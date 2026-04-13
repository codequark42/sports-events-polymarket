from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from .config import TIMEZONE_NAME
from .models import CalendarEntry


ROME_TZ = ZoneInfo(TIMEZONE_NAME)

ROME_VTIMEZONE = """BEGIN:VTIMEZONE
TZID:Europe/Rome
X-LIC-LOCATION:Europe/Rome
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE"""


def _escape_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\n", r"\n")
    )


def _fold_line(line: str) -> str:
    if len(line) <= 75:
        return line
    parts = []
    while len(line) > 75:
        parts.append(line[:75])
        line = " " + line[75:]
    parts.append(line)
    return "\r\n".join(parts)


def _format_local_dt(value: datetime) -> str:
    return value.astimezone(ROME_TZ).strftime("%Y%m%dT%H%M%S")


def _format_utc_dt(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _render_event(entry: CalendarEntry, dtstamp: datetime) -> str:
    lines = [
        "BEGIN:VEVENT",
        f"UID:{entry.uid}",
        f"DTSTAMP:{_format_utc_dt(dtstamp)}",
        f"LAST-MODIFIED:{_format_utc_dt(entry.last_modified or dtstamp)}",
        f"DTSTART;TZID={TIMEZONE_NAME}:{_format_local_dt(entry.start)}",
        f"DTEND;TZID={TIMEZONE_NAME}:{_format_local_dt(entry.end)}",
        f"SUMMARY:{_escape_text(entry.summary)}",
        f"STATUS:{entry.status}",
    ]
    if entry.categories:
        lines.append(f"CATEGORIES:{_escape_text(','.join(entry.categories))}")
    if entry.location:
        lines.append(f"LOCATION:{_escape_text(entry.location)}")
    if entry.url:
        lines.append(f"URL:{entry.url}")
    if entry.description:
        lines.append(f"DESCRIPTION:{_escape_text(entry.description)}")
    lines.append("END:VEVENT")
    return "\r\n".join(_fold_line(line) for line in lines)


def render_calendar(entries: list[CalendarEntry]) -> str:
    dtstamp = datetime.now(tz=UTC)
    rendered_events = "\r\n".join(_render_event(entry, dtstamp) for entry in entries)
    calendar_lines = [
        "BEGIN:VCALENDAR",
        "PRODID:-//sports-events-polymarket//calendar//EN",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Sports Events Polymarket",
        f"X-WR-TIMEZONE:{TIMEZONE_NAME}",
        "REFRESH-INTERVAL;VALUE=DURATION:PT30M",
        "X-PUBLISHED-TTL:PT30M",
        ROME_VTIMEZONE,
        rendered_events,
        "END:VCALENDAR",
        "",
    ]
    return "\r\n".join(calendar_lines)
