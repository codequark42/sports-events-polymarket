from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import POLYMARKET_BASE_URL, SPORTS_TAG_ID


def _get_json(path: str, params: dict[str, Any]) -> Any:
    query = urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{POLYMARKET_BASE_URL}{path}?{query}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "sports-events-polymarket/1.0",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(UTC)


def fetch_candidate_events(
    *,
    now: datetime,
    days_forward: int,
    days_back: int,
    page_limit: int,
    max_pages: int,
) -> list[dict[str, Any]]:
    events_by_id: dict[str, dict[str, Any]] = {}
    forward_cutoff = now + timedelta(days=days_forward)
    back_cutoff = now - timedelta(days=days_back)

    for page in range(max_pages):
        offset = page * page_limit
        batch = _get_json(
            "/events",
            {
                "tag_id": SPORTS_TAG_ID,
                "active": "true",
                "closed": "false",
                "order": "start_date",
                "ascending": "true",
                "limit": page_limit,
                "offset": offset,
            },
        )
        if not batch:
            break

        for event in batch:
            start = _parse_dt(event.get("startDate"))
            if start and start <= forward_cutoff:
                events_by_id[str(event["id"])] = event

        last_start = _parse_dt(batch[-1].get("startDate"))
        if last_start and last_start > forward_cutoff:
            break

    for page in range(max_pages):
        offset = page * page_limit
        batch = _get_json(
            "/events",
            {
                "tag_id": SPORTS_TAG_ID,
                "closed": "true",
                "order": "end_date",
                "ascending": "false",
                "limit": page_limit,
                "offset": offset,
            },
        )
        if not batch:
            break

        for event in batch:
            end = _parse_dt(event.get("endDate")) or _parse_dt(event.get("startDate"))
            if end and end >= back_cutoff:
                events_by_id[str(event["id"])] = event

        last_end = _parse_dt(batch[-1].get("endDate")) or _parse_dt(batch[-1].get("startDate"))
        if last_end and last_end < back_cutoff:
            break

    return sorted(
        events_by_id.values(),
        key=lambda event: (_parse_dt(event.get("startDate")) or now, str(event.get("id"))),
    )


@lru_cache(maxsize=None)
def fetch_event_by_slug(slug: str) -> dict[str, Any] | None:
    batch = _get_json("/events", {"slug": slug})
    if not batch:
        return None
    return batch[0]
