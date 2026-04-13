from __future__ import annotations

import json
import re
import zlib
from base64 import urlsafe_b64decode
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from time import sleep
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen

from .config import (
    BIG_SOCCER_TEAMS,
    CHESS_KEYWORDS,
    CURRENT_TOP_UFC_FIGHTER_KEYWORDS,
    CRICKET_KNOCKOUT_KEYWORDS,
    CRICKET_PAGE_ROUTES,
    CRICKET_TARGET_TEAMS,
    DEFAULT_HTTP_RETRIES,
    DEFAULT_HTTP_TIMEOUT_SECONDS,
    FOOTBALL_CUP_PAGE_ROUTES,
    FOOTBALL_LEAGUE_PAGE_ROUTES,
    GRAND_SLAM_KEYWORDS,
    POLYMARKET_WEB_BASE_URL,
    TENNIS_PAGE_ROUTES,
    TENNIS_PLAYER_KEYWORDS,
    TENNIS_ROUND_KEYWORDS,
    UFC_PAGE_ROUTE,
    VALORANT_PAGE_ROUTE,
)
from .polymarket import fetch_event_by_slug


USER_AGENT = "sports-events-polymarket/1.0"
PAGE_ITEM_EXCLUSION_KEYWORDS = {
    "halftime result",
    "exact score",
    "more markets",
    "toss",
    "most sixes",
    "team top batter",
    "top batter",
}


@dataclass(frozen=True)
class PageRef:
    slug: str
    title: str
    page_route: str
    page_label: str
    category: str


@lru_cache(maxsize=None)
def _fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(DEFAULT_HTTP_RETRIES):
        try:
            with urlopen(request, timeout=DEFAULT_HTTP_TIMEOUT_SECONDS) as response:
                return response.read().decode("utf-8")
        except (TimeoutError, URLError, OSError) as exc:
            last_error = exc
            if attempt + 1 == DEFAULT_HTTP_RETRIES:
                raise
            sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"unreachable _fetch_html failure for {url}: {last_error}")


def _full_url(route: str) -> str:
    return f"{POLYMARKET_WEB_BASE_URL}{route}"


@lru_cache(maxsize=None)
def _extract_initial_state(route: str) -> dict:
    try:
        html = _fetch_html(_full_url(route))
    except Exception:
        return {}
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json" crossorigin="anonymous">(.*?)</script>',
        html,
        re.S,
    )
    if not match:
        return {}

    try:
        next_data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    initial_state = (
        next_data.get("props", {})
        .get("pageProps", {})
        .get("initialState", "")
    )
    if not initial_state:
        return {}

    payload = initial_state + ("=" * (-len(initial_state) % 4))
    try:
        decoded = zlib.decompress(urlsafe_b64decode(payload), 15)
    except (zlib.error, ValueError):
        return {}
    try:
        return json.loads(decoded)
    except json.JSONDecodeError:
        return {}


def _extract_state_refs(route: str, *, page_label: str, category: str) -> list[PageRef]:
    state = _extract_initial_state(route)
    refs: list[PageRef] = []
    for event in state.get("events", {}).values():
        title = str(event.get("title") or "").strip()
        slug = str(event.get("slug") or "").strip()
        if not title or not slug:
            continue
        refs.append(
            PageRef(
                slug=slug,
                title=title,
                page_route=route,
                page_label=page_label,
                category=category,
            )
        )
    return refs


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


def _big_soccer_team_count(title: str) -> int:
    lowered = title.lower()
    return sum(1 for team in BIG_SOCCER_TEAMS if _contains_phrase(lowered, team))


def _football_routes() -> list[tuple[str, str]]:
    routes: list[tuple[str, str]] = []
    for route, label in FOOTBALL_CUP_PAGE_ROUTES.items():
        routes.append((route, label))

    for route, label in FOOTBALL_LEAGUE_PAGE_ROUTES.items():
        routes.append((route, label))
        state = _extract_initial_state(route)
        for week in state.get("summary", {}).get("eventWeeks", []):
            routes.append((f"{route}/week/{week}", label))
    return routes


def _filter_football_refs() -> list[PageRef]:
    refs: list[PageRef] = []
    for route, label in _football_routes():
        for ref in _extract_state_refs(route, page_label=label, category="Football"):
            lowered = ref.title.lower()
            if " vs " not in lowered and " vs. " not in lowered:
                continue
            if _contains_any(lowered, PAGE_ITEM_EXCLUSION_KEYWORDS):
                continue
            if _big_soccer_team_count(ref.title) < 2 and not _contains_any(
                lowered, {"semi-final", "semifinal", "semi final", "final", "decider"}
            ):
                continue
            refs.append(ref)
    return refs


def _filter_chess_refs() -> list[PageRef]:
    refs: list[PageRef] = []
    for ref in _extract_state_refs("/sports/chess/games", page_label="Chess", category="Chess"):
        if _contains_any(ref.title.lower(), CHESS_KEYWORDS):
            refs.append(ref)
    return refs


def _filter_tennis_refs() -> list[PageRef]:
    refs: list[PageRef] = []
    for route, label in TENNIS_PAGE_ROUTES.items():
        for ref in _extract_state_refs(route, page_label=label, category="Tennis"):
            lowered = ref.title.lower()
            if _contains_any(lowered, TENNIS_PLAYER_KEYWORDS) and _contains_any(
                lowered, TENNIS_ROUND_KEYWORDS
            ) and _contains_any(lowered, GRAND_SLAM_KEYWORDS):
                refs.append(ref)
    return refs


def _filter_cricket_refs() -> list[PageRef]:
    refs: list[PageRef] = []
    for route, label in CRICKET_PAGE_ROUTES.items():
        for ref in _extract_state_refs(route, page_label=label, category="Cricket"):
            lowered = ref.title.lower()
            if _contains_any(lowered, PAGE_ITEM_EXCLUSION_KEYWORDS):
                continue
            if " vs " not in lowered and " vs. " not in lowered:
                continue
            if not _contains_any(lowered, CRICKET_TARGET_TEAMS):
                continue
            if not _contains_any(lowered, {"royal challengers bangalore", "royal challengers bengaluru", "rcb"}) and not _contains_any(
                lowered, CRICKET_KNOCKOUT_KEYWORDS
            ):
                continue
            refs.append(ref)
    return refs


def _filter_ufc_refs() -> list[PageRef]:
    return [
        ref
        for ref in _extract_state_refs(UFC_PAGE_ROUTE, page_label="UFC", category="UFC")
        if ("main card" in ref.title.lower() or "main event" in ref.title.lower())
        and _contains_any(ref.title.lower(), CURRENT_TOP_UFC_FIGHTER_KEYWORDS)
    ]


def _all_football_refs() -> list[PageRef]:
    refs: list[PageRef] = []
    for route, label in _football_routes():
        refs.extend(_extract_state_refs(route, page_label=label, category="Football"))
    return refs


def _all_chess_refs() -> list[PageRef]:
    return _extract_state_refs("/sports/chess/games", page_label="Chess", category="Chess")


def _all_tennis_refs() -> list[PageRef]:
    refs: list[PageRef] = []
    for route, label in TENNIS_PAGE_ROUTES.items():
        refs.extend(_extract_state_refs(route, page_label=label, category="Tennis"))
    return refs


def _all_cricket_refs() -> list[PageRef]:
    refs: list[PageRef] = []
    for route, label in CRICKET_PAGE_ROUTES.items():
        refs.extend(_extract_state_refs(route, page_label=label, category="Cricket"))
    return refs


def _all_ufc_refs() -> list[PageRef]:
    return _extract_state_refs(UFC_PAGE_ROUTE, page_label="UFC", category="UFC")


def _all_valorant_refs() -> list[PageRef]:
    return _extract_state_refs(VALORANT_PAGE_ROUTE, page_label="Valorant", category="Valorant")


def _filter_valorant_events(events: list[dict]) -> list[dict]:
    filtered = []
    for event in events:
        title = str(event.get("title") or "").lower()
        metadata = event.get("eventMetadata") or {}
        route = str(event.get("_page_route") or "")
        if route != VALORANT_PAGE_ROUTE:
            continue
        league = str(metadata.get("league") or "").upper()
        try:
            league_tier = int(str(metadata.get("leagueTier") or "99"))
        except ValueError:
            league_tier = 99
        if "vct china" in title or str(metadata.get("serie") or "").lower() == "china":
            continue
        if league != "VCT" and league_tier > 3 and "vct" not in title and "champions tour" not in title:
            continue
        filtered.append(event)
    return filtered


def _enrich_refs(refs: list[PageRef]) -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()
    for ref in refs:
        if ref.slug in seen:
            continue
        seen.add(ref.slug)
        event = fetch_event_by_slug(ref.slug)
        if not event:
            continue
        event["_forced_category"] = ref.category
        event["_page_route"] = ref.page_route
        event["_page_label"] = ref.page_label
        events.append(event)
    return events


def fetch_curated_page_events(*, now: datetime, days_forward: int, days_back: int) -> list[dict]:
    cutoff_back = now - timedelta(days=days_back)
    cutoff_forward = now + timedelta(days=days_forward)

    refs = [
        *_filter_football_refs(),
        *_filter_chess_refs(),
        *_filter_tennis_refs(),
        *_filter_cricket_refs(),
    ]

    ufc_events = _enrich_refs(_filter_ufc_refs())
    valorant_events = _filter_valorant_events(_enrich_refs(_all_valorant_refs()))

    events = [*_enrich_refs(refs), *ufc_events, *valorant_events]
    in_window = []
    for event in events:
        raw_end = str(event.get("endDate") or "")
        if not raw_end:
            continue
        end = datetime.fromisoformat(raw_end.replace("Z", "+00:00")).astimezone(UTC)
        if cutoff_back <= end <= cutoff_forward:
            in_window.append(event)

    return sorted(in_window, key=lambda event: (str(event.get("endDate") or ""), str(event.get("slug") or "")))


def fetch_page_source_events(*, now: datetime, days_forward: int, days_back: int) -> list[dict]:
    cutoff_back = now - timedelta(days=days_back)
    cutoff_forward = now + timedelta(days=days_forward)

    refs = [
        *_all_football_refs(),
        *_all_ufc_refs(),
        *_all_chess_refs(),
        *_all_tennis_refs(),
        *_all_cricket_refs(),
        *_all_valorant_refs(),
    ]
    events = _enrich_refs(refs)

    in_window = []
    for event in events:
        raw_end = str(event.get("endDate") or "")
        if not raw_end:
            continue
        end = datetime.fromisoformat(raw_end.replace("Z", "+00:00")).astimezone(UTC)
        if cutoff_back <= end <= cutoff_forward:
            in_window.append(event)

    return sorted(
        in_window,
        key=lambda event: (
            str(event.get("_forced_category") or ""),
            str(event.get("_page_label") or ""),
            str(event.get("endDate") or ""),
            str(event.get("slug") or ""),
        ),
    )
