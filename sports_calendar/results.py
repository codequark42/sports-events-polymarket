from __future__ import annotations

import json
import re
from typing import Any


PRIMARY_MARKET_EXCLUSION_KEYWORDS = {
    "total",
    "totals",
    "handicap",
    "set 1",
    "set 2",
    "first set",
    "games o/u",
    "match o/u",
    "fight next",
    "top scorer",
    "top 4",
    "relegated",
    "promoted",
    "most assists",
    "most clean sheets",
}


def _parse_json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _normalized_question(market: dict[str, Any]) -> str:
    return str(market.get("question") or "").lower()


def _parse_price(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_percent(value: float) -> str:
    return f"{round(value * 100):d}%"


def _pick_primary_market(event: dict[str, Any]) -> dict[str, Any] | None:
    title = str(event.get("title") or "")
    markets = list(event.get("markets") or [])

    def score(market: dict[str, Any]) -> tuple[int, int]:
        question = _normalized_question(market)
        outcomes = _parse_json_list(market.get("outcomes"))
        title_match = int(str(market.get("question") or "").strip() == title.strip())
        excluded = any(keyword in question for keyword in PRIMARY_MARKET_EXCLUSION_KEYWORDS)
        multi_outcome = int(len(outcomes) >= 2 and "yes" not in {str(o).lower() for o in outcomes})
        matchup_hint = int(" vs " in question or " vs. " in question)
        return (
            int(not excluded) + title_match + multi_outcome + matchup_hint,
            len(outcomes),
        )

    if not markets:
        return None

    chosen = max(markets, key=score)
    question = _normalized_question(chosen)
    if any(keyword in question for keyword in PRIMARY_MARKET_EXCLUSION_KEYWORDS):
        return None
    return chosen


def _resolved_outcome_from_market(market: dict[str, Any]) -> str | None:
    outcomes = _parse_json_list(market.get("outcomes"))
    prices = [_parse_price(price) for price in _parse_json_list(market.get("outcomePrices"))]
    if not outcomes or len(outcomes) != len(prices):
        return None
    for outcome, price in zip(outcomes, prices):
        if price is not None and abs(price - 1.0) < 1e-9:
            return str(outcome)
    return None


def _upcoming_outlook_from_market(market: dict[str, Any]) -> str | None:
    outcomes = _parse_json_list(market.get("outcomes"))
    prices = [_parse_price(price) for price in _parse_json_list(market.get("outcomePrices"))]
    if not outcomes or len(outcomes) != len(prices):
        return None
    ranked = sorted(
        [
            (str(outcome), price)
            for outcome, price in zip(outcomes, prices)
            if price is not None and price > 0
        ],
        key=lambda item: item[1],
        reverse=True,
    )
    if not ranked:
        return None
    preview = ", ".join(f"{outcome} {_format_percent(price)}" for outcome, price in ranked[:3])
    return f"Market outlook: {preview}"


def _soccer_three_way_result(event: dict[str, Any]) -> str | None:
    title = str(event.get("title") or "")
    markets = list(event.get("markets") or [])
    if " vs" not in title.lower():
        return None
    participants = re.split(r"\s+vs\.?\s+", title, maxsplit=1, flags=re.IGNORECASE)
    if len(participants) != 2:
        return None
    home, away = participants[0].strip(), participants[1].strip()

    for market in markets:
        outcome = _resolved_outcome_from_market(market)
        if outcome != "Yes":
            continue
        question = _normalized_question(market)
        if "draw" in question:
            return "Result: Draw"
        if home.lower() in question:
            return f"Result: {home} win"
        if away.lower() in question:
            return f"Result: {away} win"
    return None


def _soccer_three_way_outlook(event: dict[str, Any]) -> str | None:
    title = str(event.get("title") or "")
    markets = list(event.get("markets") or [])
    if " vs" not in title.lower():
        return None
    participants = re.split(r"\s+vs\.?\s+", title, maxsplit=1, flags=re.IGNORECASE)
    if len(participants) != 2:
        return None
    home, away = participants[0].strip(), participants[1].strip()

    buckets: dict[str, float] = {}
    for market in markets:
        question = _normalized_question(market)
        prices = [_parse_price(price) for price in _parse_json_list(market.get("outcomePrices"))]
        outcomes = [str(outcome).lower() for outcome in _parse_json_list(market.get("outcomes"))]
        if outcomes != ["yes", "no"] or not prices:
            continue
        yes_price = prices[0]
        if yes_price is None:
            continue
        if "draw" in question:
            buckets["Draw"] = yes_price
        elif home.lower() in question:
            buckets[home] = yes_price
        elif away.lower() in question:
            buckets[away] = yes_price

    if len(buckets) < 3:
        return None
    return "Match outlook: " + ", ".join(
        f"{name} {_format_percent(price)}"
        for name, price in ((home, buckets[home]), ("Draw", buckets["Draw"]), (away, buckets[away]))
    )


def build_event_notes(event: dict[str, Any]) -> list[str]:
    soccer_result = _soccer_three_way_result(event)
    if soccer_result:
        return [soccer_result]

    soccer_outlook = _soccer_three_way_outlook(event)
    if soccer_outlook:
        return [soccer_outlook]

    primary_market = _pick_primary_market(event)
    if not primary_market:
        return []

    resolved = _resolved_outcome_from_market(primary_market)
    if resolved is not None:
        return [
            f"Result: {resolved}",
            f"Resolved market: {primary_market.get('question', '')}",
        ]

    outlook = _upcoming_outlook_from_market(primary_market)
    if outlook:
        return [f"Primary market: {primary_market.get('question', '')}", outlook]
    return []
