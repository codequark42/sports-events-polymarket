from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .config import BuildOptions
from .f1 import fetch_f1_events
from .filtering import select_polymarket_event
from .ics import render_calendar
from .models import CalendarEntry, SelectedEvent
from .polymarket_pages import fetch_curated_page_events

SPORT_CALENDARS = {
    "football": "Football",
    "f1": "F1",
    "ufc": "UFC",
    "chess": "Chess",
    "tennis": "Tennis",
    "valorant": "Valorant",
    "cricket": "Cricket",
}


def _sport_key(categories: list[str]) -> str | None:
    if not categories:
        return None
    sport = categories[-1].strip().lower()
    if sport in SPORT_CALENDARS:
        return sport
    return None


def build_polymarket_entries(
    options: BuildOptions,
    *,
    now: datetime | None = None,
) -> list[SelectedEvent]:
    effective_now = now or datetime.now(tz=UTC)
    candidate_events = fetch_curated_page_events(
        now=effective_now,
        days_forward=options.days_forward,
        days_back=options.days_back,
    )

    selected_events: list[SelectedEvent] = []
    cutoff_back = effective_now - timedelta(days=options.days_back)
    cutoff_forward = effective_now + timedelta(days=options.days_forward)
    for event in candidate_events:
        selected = select_polymarket_event(event)
        if not selected:
            continue
        if not (cutoff_back <= selected.start <= cutoff_forward):
            continue
        selected_events.append(selected)

    selected_events.sort(key=lambda entry: (entry.start, entry.summary.lower(), entry.uid))
    return selected_events


def build_calendar_artifacts(
    options: BuildOptions,
    *,
    now: datetime | None = None,
) -> tuple[str, list[SelectedEvent], dict[str, str]]:
    effective_now = now or datetime.now(tz=UTC)
    selected_entries: list[CalendarEntry] = []
    polymarket_events = build_polymarket_entries(options, now=effective_now)
    cutoff_back = effective_now - timedelta(days=options.days_back)
    cutoff_forward = effective_now + timedelta(days=options.days_forward)

    for event in polymarket_events:
        selected_entries.append(event.to_calendar_entry(last_modified=effective_now))

    for event in fetch_f1_events(options.f1_ics_url):
        if cutoff_back <= event.start <= cutoff_forward:
            selected_entries.append(event.to_calendar_entry(last_modified=effective_now))

    selected_entries.sort(key=lambda entry: (entry.start, entry.summary.lower(), entry.uid))
    grouped_entries: dict[str, list[CalendarEntry]] = {key: [] for key in SPORT_CALENDARS}
    for entry in selected_entries:
        key = _sport_key(entry.categories)
        if key:
            grouped_entries[key].append(entry)

    sport_payloads = {
        key: render_calendar(grouped_entries[key])
        for key in SPORT_CALENDARS
    }
    return render_calendar(selected_entries), polymarket_events, sport_payloads


def build_calendar(options: BuildOptions) -> str:
    payload, _, _ = build_calendar_artifacts(options)
    return payload
