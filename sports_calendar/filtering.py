from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from .config import (
    BIG_SOCCER_TEAMS,
    BIG_VALORANT_TEAMS,
    CHESS_KEYWORDS,
    CURRENT_TOP_UFC_FIGHTER_KEYWORDS,
    CRICKET_KNOCKOUT_KEYWORDS,
    CRICKET_TAGS,
    CRICKET_TARGET_TEAMS,
    GRAND_SLAM_KEYWORDS,
    MAJOR_SOCCER_COMPETITIONS,
    SOCCER_KNOCKOUT_KEYWORDS,
    SOCCER_TAGS,
    SOCCER_TITLE_DECIDER_KEYWORDS,
    TENNIS_PLAYER_KEYWORDS,
    TENNIS_ROUND_KEYWORDS,
    TENNIS_TAGS,
    UFC_EXCLUDED_KEYWORDS,
    UFC_TAGS,
    VALORANT_TAGS,
)
from .models import SelectedEvent
from .results import build_event_notes

GENERIC_EXCLUDED_TITLE_KEYWORDS = {
    "more markets",
    "who will advance",
    "winner",
    "champion",
    "top scorer",
    "top 4",
    "relegated",
    "promoted",
    "manager",
    "trophy",
    "reach final",
    "to reach final",
    "which clubs",
    "most assists",
    "most clean sheets",
}
DEFAULT_EVENT_DURATIONS = {
    "Football": timedelta(hours=2),
    "UFC": timedelta(hours=4),
    "Chess": timedelta(hours=3),
    "Tennis": timedelta(hours=3),
    "Valorant": timedelta(hours=3),
    "Cricket": timedelta(hours=8),
}


def _lower_set(items: list[str]) -> set[str]:
    return {item.lower() for item in items}


def _text_blob(event: dict[str, Any]) -> str:
    parts = [
        event.get("title", ""),
        *(tag.get("label", "") for tag in event.get("tags", [])),
    ]
    return " ".join(parts).lower()


def _tag_labels(event: dict[str, Any]) -> set[str]:
    return _lower_set([tag.get("label", "") for tag in event.get("tags", [])])


def _contains_any(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


def _matching_teams(text: str, candidates: set[str]) -> list[str]:
    return sorted({team for team in candidates if _contains_phrase(text, team)})


def _is_matchup_title(title: str) -> bool:
    lowered = title.lower()
    return " vs " in lowered or " vs. " in lowered


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(UTC)


def _should_exclude_title(title: str) -> bool:
    lowered = title.lower()
    return any(keyword in lowered for keyword in GENERIC_EXCLUDED_TITLE_KEYWORDS)


def _infer_schedule(
    *,
    raw_start: datetime | None,
    raw_end: datetime | None,
    sport: str,
) -> tuple[datetime, datetime] | None:
    if raw_start is None and raw_end is None:
        return None

    duration = DEFAULT_EVENT_DURATIONS[sport]
    if raw_end and raw_start:
        # Polymarket sports event startDate is often market creation time.
        if raw_end - raw_start > timedelta(hours=12):
            return raw_end, raw_end + duration
        if raw_end > raw_start:
            return raw_start, raw_end
        return raw_start, raw_start + duration

    if raw_end:
        return raw_end, raw_end + duration

    return raw_start, raw_start + duration


def _football_match_interest(event: dict[str, Any]) -> bool:
    title = event.get("title", "")
    lowered = _text_blob(event)
    tags = _tag_labels(event)
    if _should_exclude_title(title):
        return False
    if "soccer" not in tags and "soccer" not in lowered:
        return False
    if not _is_matchup_title(title):
        return False

    big_teams = _matching_teams(lowered, BIG_SOCCER_TEAMS)
    has_major_competition = bool(tags.intersection(MAJOR_SOCCER_COMPETITIONS))
    is_knockout = _contains_any(lowered, SOCCER_KNOCKOUT_KEYWORDS)
    is_decider = _contains_any(lowered, SOCCER_TITLE_DECIDER_KEYWORDS)
    return (len(big_teams) >= 2 and has_major_competition) or is_knockout or is_decider


def _ufc_interest(event: dict[str, Any]) -> bool:
    title = event.get("title", "")
    lowered = _text_blob(event)
    tags = _tag_labels(event)
    if _should_exclude_title(title):
        return False
    if "ufc" not in lowered and "ufc" not in tags:
        return False
    if _contains_any(lowered, UFC_EXCLUDED_KEYWORDS):
        return False
    if not _contains_any(lowered, CURRENT_TOP_UFC_FIGHTER_KEYWORDS):
        return False
    return _is_matchup_title(title) or "main event" in lowered or re.search(r"\bufc\s+\d+", lowered)


def _chess_interest(event: dict[str, Any]) -> bool:
    if _should_exclude_title(event.get("title", "")):
        return False
    lowered = _text_blob(event)
    return "chess" in lowered and _contains_any(lowered, CHESS_KEYWORDS)


def _tennis_interest(event: dict[str, Any]) -> bool:
    title = event.get("title", "")
    lowered = _text_blob(event)
    tags = _tag_labels(event)
    if _should_exclude_title(title):
        return False
    if not tags.intersection(TENNIS_TAGS):
        return False
    if not _contains_any(lowered, GRAND_SLAM_KEYWORDS):
        return False
    return _contains_any(lowered, TENNIS_PLAYER_KEYWORDS) and _contains_any(
        lowered, TENNIS_ROUND_KEYWORDS
    )


def _valorant_interest(event: dict[str, Any]) -> bool:
    title = event.get("title", "")
    lowered = _text_blob(event)
    tags = _tag_labels(event)
    metadata = event.get("eventMetadata") or {}
    if _should_exclude_title(title):
        return False
    if not tags.intersection(VALORANT_TAGS) and "valorant" not in lowered:
        return False
    if not _is_matchup_title(title):
        return False
    league = str(metadata.get("league") or "").upper()
    try:
        league_tier = int(str(metadata.get("leagueTier") or "99"))
    except ValueError:
        league_tier = 99
    if "vct china" in lowered or " china " in f" {lowered} ":
        return False
    return (
        league == "VCT"
        or league_tier <= 3
        or "vct" in lowered
        or "champions tour" in lowered
        or len(_matching_teams(lowered, BIG_VALORANT_TEAMS)) >= 2
    )


def _cricket_interest(event: dict[str, Any]) -> bool:
    title = event.get("title", "")
    lowered = _text_blob(event)
    tags = _tag_labels(event)
    if _should_exclude_title(title):
        return False
    if not tags.intersection(CRICKET_TAGS):
        return False
    if not _is_matchup_title(title):
        return False
    if _contains_any(lowered, {"royal challengers bangalore", "royal challengers bengaluru", "rcb"}):
        return True
    return (
        _contains_any(lowered, CRICKET_KNOCKOUT_KEYWORDS)
        and _contains_any(lowered, CRICKET_TARGET_TEAMS)
    )


def select_polymarket_event(event: dict[str, Any]) -> SelectedEvent | None:
    title = event.get("title", "").strip()
    if not title:
        return None

    forced_category = event.get("_forced_category")
    categories: list[str] | None = ["Polymarket", forced_category] if forced_category else None
    if not categories:
        if _football_match_interest(event):
            categories = ["Polymarket", "Football"]
        elif _ufc_interest(event):
            categories = ["Polymarket", "UFC"]
        elif _chess_interest(event):
            categories = ["Polymarket", "Chess"]
        elif _tennis_interest(event):
            categories = ["Polymarket", "Tennis"]
        elif _valorant_interest(event):
            categories = ["Polymarket", "Valorant"]
        elif _cricket_interest(event):
            categories = ["Polymarket", "Cricket"]

    if not categories:
        return None

    raw_start = _parse_dt(event.get("startDate"))
    raw_end = _parse_dt(event.get("endDate"))
    sport = categories[-1]
    schedule = _infer_schedule(raw_start=raw_start, raw_end=raw_end, sport=sport)
    if not schedule:
        return None
    start, end = schedule

    event_slug = event.get("slug") or f"event-{event.get('id')}"
    notes = build_event_notes(event)
    tag_labels = ", ".join(sorted(_tag_labels(event)))
    source_page_label = event.get("_page_label")
    description_lines = [
        f"Source: Polymarket",
        f"Event: {title}",
        f"Tags: {tag_labels}",
        *( [f"Source page: {source_page_label}"] if source_page_label else [] ),
        "Calendar time is inferred from Polymarket's effective event date fields.",
        *notes,
    ]
    return SelectedEvent(
        source="polymarket",
        summary=title,
        uid=f"polymarket-event-{event.get('id')}@sports-calendar",
        start=start,
        end=end,
        categories=categories,
        description_lines=description_lines,
        url=f"https://polymarket.com/event/{event_slug}",
        metadata={
            "event_id": str(event.get("id", "")),
            "slug": str(event_slug),
            "page_label": str(event.get("_page_label", "")),
            "page_route": str(event.get("_page_route", "")),
            "category": str(sport),
            "tags": tag_labels,
        },
    )
