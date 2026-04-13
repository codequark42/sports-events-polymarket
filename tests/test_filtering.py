from __future__ import annotations

import unittest

from sports_calendar.filtering import select_polymarket_event


class FilteringTests(unittest.TestCase):
    def test_includes_big_soccer_match(self) -> None:
        event = {
            "id": "1",
            "title": "Arsenal vs. Manchester City",
            "startDate": "2026-04-20T18:00:00Z",
            "endDate": "2026-04-20T20:00:00Z",
            "tags": [{"label": "Sports"}, {"label": "Soccer"}, {"label": "EPL"}, {"label": "Games"}],
            "markets": [],
        }
        self.assertIsNotNone(select_polymarket_event(event))

    def test_excludes_small_soccer_match(self) -> None:
        event = {
            "id": "2",
            "title": "Llaneros FC vs. CA Bucaramanga",
            "startDate": "2026-04-20T18:00:00Z",
            "endDate": "2026-04-20T20:00:00Z",
            "tags": [{"label": "Sports"}, {"label": "Soccer"}, {"label": "Games"}],
            "markets": [],
        }
        self.assertIsNone(select_polymarket_event(event))

    def test_excludes_ufc_next_fight_prop(self) -> None:
        event = {
            "id": "3",
            "title": "Who will Alexander Volkanovski fight next?",
            "startDate": "2026-04-20T18:00:00Z",
            "endDate": "2026-04-20T20:00:00Z",
            "tags": [{"label": "Sports"}, {"label": "UFC"}],
            "markets": [],
        }
        self.assertIsNone(select_polymarket_event(event))

    def test_includes_ufc_main_event(self) -> None:
        event = {
            "id": "4",
            "title": "UFC 320 Main Event: Islam Makhachev vs. Ilia Topuria",
            "startDate": "2026-04-20T18:00:00Z",
            "endDate": "2026-04-20T20:00:00Z",
            "tags": [{"label": "Sports"}, {"label": "UFC"}, {"label": "mma"}],
            "markets": [],
        }
        self.assertIsNotNone(select_polymarket_event(event))

    def test_includes_tennis_semifinal(self) -> None:
        event = {
            "id": "5",
            "title": "Australian Open Semi-final: Jannik Sinner vs Novak Djokovic",
            "startDate": "2026-04-20T18:00:00Z",
            "endDate": "2026-04-20T20:00:00Z",
            "tags": [{"label": "Sports"}, {"label": "Tennis"}, {"label": "ATP"}],
            "markets": [],
        }
        self.assertIsNotNone(select_polymarket_event(event))

    def test_excludes_non_grand_slam_tennis_match(self) -> None:
        event = {
            "id": "5b",
            "title": "Barcelona Open Semi-final: Jannik Sinner vs Carlos Alcaraz",
            "startDate": "2026-04-20T18:00:00Z",
            "endDate": "2026-04-20T20:00:00Z",
            "tags": [{"label": "Sports"}, {"label": "Tennis"}, {"label": "ATP"}],
            "markets": [],
        }
        self.assertIsNone(select_polymarket_event(event))

    def test_includes_cricket_match_for_target_team(self) -> None:
        event = {
            "id": "6",
            "title": "Indian Premier League: Royal Challengers Bangalore vs Lucknow Super Giants",
            "startDate": "2026-04-20T18:00:00Z",
            "endDate": "2026-04-20T20:00:00Z",
            "tags": [{"label": "Sports"}, {"label": "Cricket"}, {"label": "Indian Premier League"}],
            "markets": [],
        }
        self.assertIsNotNone(select_polymarket_event(event))

    def test_excludes_regular_cricket_match(self) -> None:
        event = {
            "id": "7",
            "title": "Afghanistan vs. Sri Lanka",
            "startDate": "2026-04-20T18:00:00Z",
            "endDate": "2026-04-20T20:00:00Z",
            "tags": [{"label": "Sports"}, {"label": "Cricket"}, {"label": "Games"}],
            "markets": [],
        }
        self.assertIsNone(select_polymarket_event(event))

    def test_forced_category_bypasses_generic_heuristics(self) -> None:
        event = {
            "id": "8",
            "title": "Hikaru Nakamura vs. Matthias Bluebaum - FIDE Candidates 2026 Open (Round 13)",
            "slug": "chess-hnakam-mblueb-2026-04-14-r13",
            "startDate": "2026-04-13T10:00:00Z",
            "endDate": "2026-04-21T12:45:00Z",
            "tags": [{"label": "Sports"}, {"label": "Chess"}],
            "_forced_category": "Chess",
            "_page_label": "Chess",
            "markets": [],
        }
        selected = select_polymarket_event(event)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.categories, ["Polymarket", "Chess"])

    def test_excludes_one_big_team_soccer_match(self) -> None:
        event = {
            "id": "9",
            "title": "Manchester City FC vs. Crystal Palace FC",
            "startDate": "2026-04-20T18:00:00Z",
            "endDate": "2026-04-20T20:00:00Z",
            "tags": [{"label": "Sports"}, {"label": "Soccer"}, {"label": "EPL"}, {"label": "Games"}],
            "markets": [],
        }
        self.assertIsNone(select_polymarket_event(event))

    def test_includes_vct_valorant_match(self) -> None:
        event = {
            "id": "10",
            "title": "Valorant: TYLOO vs JD Gaming (BO3) - VCT China Group Alpha",
            "startDate": "2026-04-20T18:00:00Z",
            "endDate": "2026-04-20T20:00:00Z",
            "tags": [{"label": "Esports"}, {"label": "Valorant"}, {"label": "Games"}],
            "eventMetadata": {"league": "VCT", "leagueTier": "3"},
            "markets": [],
        }
        self.assertIsNotNone(select_polymarket_event(event))


if __name__ == "__main__":
    unittest.main()
