from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.request import Request, urlopen

from .config import F1_RACE_SUFFIXES
from .models import SelectedEvent


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "sports-events-polymarket/1.0"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def _unfold_ics_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for line in raw_text.splitlines():
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def _parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    return datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=UTC)


def _extract_prop(line: str) -> tuple[str, str]:
    name, value = line.split(":", 1)
    return name.split(";", 1)[0], value


def _is_race_or_sprint(summary: str) -> bool:
    lowered = summary.lower()
    return any(lowered.endswith(suffix) for suffix in F1_RACE_SUFFIXES)


def fetch_f1_events(url: str) -> list[SelectedEvent]:
    text = _fetch_text(url)
    lines = _unfold_ics_lines(text)
    entries: list[SelectedEvent] = []

    in_event = False
    props: dict[str, str] = {}
    for line in lines:
        if line == "BEGIN:VEVENT":
            in_event = True
            props = {}
            continue
        if line == "END:VEVENT":
            summary = props.get("SUMMARY", "")
            if summary and _is_race_or_sprint(summary):
                start = _parse_dt(props["DTSTART"])
                end = _parse_dt(props.get("DTEND", props["DTSTART"])) if "DTEND" in props else start + timedelta(hours=2)
                description = props.get("DESCRIPTION", "")
                entries.append(
                    SelectedEvent(
                        source="f1",
                        summary=summary,
                        uid=f"f1-{props.get('UID', summary)}@sports-calendar",
                        start=start,
                        end=end,
                        categories=["F1"],
                        description_lines=[
                            "Source: Formula 1 ECAL feed",
                            description,
                        ],
                        location=props.get("LOCATION"),
                    )
                )
            in_event = False
            props = {}
            continue
        if in_event and ":" in line:
            name, value = _extract_prop(line)
            props[name] = value

    return entries
