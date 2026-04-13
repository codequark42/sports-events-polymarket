from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .calendar_builder import build_calendar, build_calendar_artifacts
from .config import (
    BuildOptions,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_DAYS_BACK,
    DEFAULT_DAYS_FORWARD,
    DEFAULT_F1_ICS_URL,
    DEFAULT_MAX_POLYMARKET_PAGES,
    DEFAULT_PAGE_LIMIT,
    TIMEZONE_NAME,
)
from .models import SelectedEvent
from .polymarket_pages import fetch_page_source_events
from .server import serve_calendar


ROME_TZ = ZoneInfo(TIMEZONE_NAME)


def _build_options(args: argparse.Namespace) -> BuildOptions:
    return BuildOptions(
        days_forward=args.days_forward,
        days_back=args.days_back,
        max_polymarket_pages=args.max_polymarket_pages,
        page_limit=args.page_limit,
        f1_ics_url=args.f1_ics_url,
    )


def _write_prefilter_dump(output_dir: Path, options: BuildOptions) -> None:
    now = datetime.now(tz=UTC)
    events = fetch_page_source_events(
        now=now,
        days_forward=options.days_forward,
        days_back=options.days_back,
    )

    json_path = output_dir / "polymarket_pre_filter.json"
    tsv_path = output_dir / "polymarket_pre_filter.tsv"

    json_path.write_text(json.dumps(events, indent=2, ensure_ascii=True), encoding="utf-8")
    with tsv_path.open("w", encoding="utf-8") as handle:
        handle.write(
            "id\tcategory\tpage_label\ttitle\tstartDate\tendDate\tclosed\ttags\tslug\tpage_route\n"
        )
        for event in events:
            tags = "|".join(tag.get("label", "") for tag in event.get("tags", []))
            row = [
                str(event.get("id", "")),
                str(event.get("_forced_category", "")),
                str(event.get("_page_label", "")),
                str(event.get("title", "")).replace("\t", " ").replace("\n", " "),
                str(event.get("startDate", "")),
                str(event.get("endDate", "")),
                str(event.get("closed", "")),
                tags.replace("\t", " ").replace("\n", " "),
                str(event.get("slug", "")),
                str(event.get("_page_route", "")),
            ]
            handle.write("\t".join(row) + "\n")


def _write_postfilter_dump(output_dir: Path, events: list[SelectedEvent]) -> None:
    tsv_path = output_dir / "polymarket_post_filter.tsv"

    with tsv_path.open("w", encoding="utf-8") as handle:
        handle.write(
            "event_id\tcategory\ttitle\tstart_local\tend_local\ttags\tslug\tpage_label\tpage_route\turl\n"
        )
        for event in events:
            row = [
                event.metadata.get("event_id", ""),
                event.metadata.get("category", ""),
                event.summary.replace("\t", " ").replace("\n", " "),
                event.start.astimezone(ROME_TZ).isoformat(),
                event.end.astimezone(ROME_TZ).isoformat(),
                event.metadata.get("tags", "").replace("\t", " ").replace("\n", " "),
                event.metadata.get("slug", ""),
                event.metadata.get("page_label", ""),
                event.metadata.get("page_route", ""),
                event.url or "",
            ]
            handle.write("\t".join(row) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or serve a sports events ICS calendar.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--days-forward", type=int, default=DEFAULT_DAYS_FORWARD)
    common.add_argument("--days-back", type=int, default=DEFAULT_DAYS_BACK)
    common.add_argument("--max-polymarket-pages", type=int, default=DEFAULT_MAX_POLYMARKET_PAGES)
    common.add_argument("--page-limit", type=int, default=DEFAULT_PAGE_LIMIT)
    common.add_argument("--f1-ics-url", default=DEFAULT_F1_ICS_URL)

    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser(
        "serve",
        help="Serve a subscribable ICS endpoint.",
        parents=[common],
    )
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--cache-ttl", type=int, default=DEFAULT_CACHE_TTL_SECONDS)

    generate_parser = subparsers.add_parser(
        "generate",
        help="Write the calendar to a file.",
        parents=[common],
    )
    generate_parser.add_argument("--output", required=True)

    argv = sys.argv[1:]
    if not argv or argv[0].startswith("-"):
        argv = ["serve", *argv]
    args = parser.parse_args(argv)
    options = _build_options(args)

    if args.command == "generate":
        payload, polymarket_events = build_calendar_artifacts(options)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
        _write_prefilter_dump(output.parent, options)
        _write_postfilter_dump(output.parent, polymarket_events)
        return

    serve_calendar(args.host, args.port, options, args.cache_ttl)


if __name__ == "__main__":
    main()
