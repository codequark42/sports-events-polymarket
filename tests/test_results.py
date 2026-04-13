from __future__ import annotations

import unittest

from sports_calendar.results import build_event_notes


class ResultTests(unittest.TestCase):
    def test_resolved_multi_outcome_market(self) -> None:
        event = {
            "title": "Australian Open Women's: Laura Siegemund vs Liudmila Samsonova",
            "markets": [
                {
                    "question": "Australian Open Women's: Laura Siegemund vs Liudmila Samsonova",
                    "outcomes": '["Siegemund", "Samsonova"]',
                    "outcomePrices": '["1", "0"]',
                }
            ],
        }
        notes = build_event_notes(event)
        self.assertIn("Result: Siegemund", notes)

    def test_resolved_soccer_three_way_market(self) -> None:
        event = {
            "title": "Portsmouth FC vs. Ipswich Town FC",
            "markets": [
                {
                    "question": "Will Portsmouth FC win on 2026-01-04?",
                    "outcomes": '["Yes", "No"]',
                    "outcomePrices": '["0", "1"]',
                },
                {
                    "question": "Will Portsmouth FC vs. Ipswich Town FC end in a draw?",
                    "outcomes": '["Yes", "No"]',
                    "outcomePrices": '["0", "1"]',
                },
                {
                    "question": "Will Ipswich Town FC win on 2026-01-04?",
                    "outcomes": '["Yes", "No"]',
                    "outcomePrices": '["1", "0"]',
                },
            ],
        }
        notes = build_event_notes(event)
        self.assertIn("Result: Ipswich Town FC win", notes)


if __name__ == "__main__":
    unittest.main()
