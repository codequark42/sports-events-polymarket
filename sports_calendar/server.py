from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from time import monotonic

from .calendar_builder import build_calendar
from .config import BuildOptions, DEFAULT_CACHE_TTL_SECONDS


class CalendarCache:
    def __init__(self, options: BuildOptions, ttl_seconds: int) -> None:
        self.options = options
        self.ttl_seconds = ttl_seconds
        self._expires_at = 0.0
        self._payload: str | None = None
        self._last_refresh_status = "never"
        self._lock = Lock()

    def get(self) -> str:
        with self._lock:
            if self._payload is None or monotonic() >= self._expires_at:
                self._refresh_locked()
            return self._payload or ""

    def refresh(self) -> None:
        with self._lock:
            self._refresh_locked()

    def status(self) -> str:
        with self._lock:
            return self._last_refresh_status

    def _refresh_locked(self) -> None:
        self._payload = build_calendar(self.options)
        self._expires_at = monotonic() + self.ttl_seconds
        self._last_refresh_status = "ok"


def _control_page(cache_ttl: int, refresh_status: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sports Calendar Control</title>
  <style>
    :root {{
      --bg: #f3efe6;
      --card: #fffaf2;
      --ink: #1e1b16;
      --muted: #6d6458;
      --accent: #0c6b58;
      --accent-2: #d9efe4;
      --border: #d7cdbf;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, #fff7e5 0, transparent 32%),
        linear-gradient(135deg, #efe7d6, var(--bg));
      color: var(--ink);
    }}
    main {{
      max-width: 720px;
      margin: 48px auto;
      padding: 0 20px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 28px;
      box-shadow: 0 18px 60px rgba(48, 38, 25, 0.08);
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: 2rem;
    }}
    p {{
      line-height: 1.5;
      color: var(--muted);
    }}
    .row {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 20px;
    }}
    button, a {{
      appearance: none;
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      text-decoration: none;
      cursor: pointer;
    }}
    button {{
      background: var(--accent);
      color: white;
      font-weight: 700;
    }}
    a {{
      background: var(--accent-2);
      color: var(--ink);
    }}
    .meta {{
      margin-top: 20px;
      padding-top: 18px;
      border-top: 1px solid var(--border);
      font-size: 0.95rem;
      color: var(--muted);
    }}
    code {{
      background: #f2eadc;
      padding: 2px 6px;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <main>
    <section class="card">
      <h1>Sports Calendar</h1>
      <p>Use this page to force an immediate rebuild of the subscribed <code>/calendar.ics</code> feed.</p>
      <form method="post" action="/refresh">
        <div class="row">
          <button type="submit">Refresh Now</button>
          <a href="/calendar.ics">Open Calendar Feed</a>
          <a href="/healthz">Health Check</a>
        </div>
      </form>
      <div class="meta">
        <div>Cache TTL: {cache_ttl} seconds</div>
        <div>Last refresh status: {refresh_status}</div>
      </div>
    </section>
  </main>
</body>
</html>
"""


def serve_calendar(host: str, port: int, options: BuildOptions, cache_ttl: int) -> None:
    cache = CalendarCache(options, cache_ttl or DEFAULT_CACHE_TTL_SECONDS)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                payload = _control_page(cache.ttl_seconds, cache.status()).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return

            if self.path == "/healthz":
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"ok\n")
                return

            if self.path != "/calendar.ics":
                self.send_response(HTTPStatus.NOT_FOUND)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"not found\n")
                return

            try:
                payload = cache.get().encode("utf-8")
            except Exception as exc:  # pragma: no cover
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"calendar build failed: {exc}\n".encode("utf-8"))
                return

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/calendar; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", f"public, max-age={cache.ttl_seconds}")
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self) -> None:
            if self.path != "/refresh":
                self.send_response(HTTPStatus.NOT_FOUND)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"not found\n")
                return

            try:
                cache.refresh()
            except Exception as exc:  # pragma: no cover
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"calendar refresh failed: {exc}\n".encode("utf-8"))
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
