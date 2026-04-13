from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CalendarEntry:
    uid: str
    summary: str
    start: datetime
    end: datetime
    description: str = ""
    categories: list[str] = field(default_factory=list)
    location: str | None = None
    url: str | None = None
    status: str = "CONFIRMED"
    last_modified: datetime | None = None


@dataclass
class SelectedEvent:
    source: str
    summary: str
    uid: str
    start: datetime
    end: datetime
    categories: list[str]
    description_lines: list[str]
    url: str | None = None
    location: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def to_calendar_entry(self, *, last_modified: datetime) -> CalendarEntry:
        return CalendarEntry(
            uid=self.uid,
            summary=self.summary,
            start=self.start,
            end=self.end,
            description="\n".join(line for line in self.description_lines if line),
            categories=self.categories,
            location=self.location,
            url=self.url,
            last_modified=last_modified,
        )
