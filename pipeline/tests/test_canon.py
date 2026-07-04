"""Snapshot tests for pipeline/canon.py — engine #4 canonicalization.

The tables must be exhaustive over the corpus (no unmapped venue/team/
season), and the snapshot constants pin the corpus so a new data drop that
adds strings fails loudly here, never silently downstream.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon

# Corpus snapshot constants (hand-verified 2026-07-03).
EXPECTED_MATCH_COUNT = 1331  # 1243 IPL + 88 WPL
EXPECTED_RAW_VENUE_COUNT = 62
EXPECTED_CANONICAL_GROUND_COUNT = 37
EXPECTED_DL_MATCHES = 23
EXPECTED_SUPER_OVER_INNINGS = 36
KNOWN_TIE_MATCH = "1082625.json"  # IPL 2017: tie, decided by super over

_scan_cache = None


def corpus_scan():
    """One cached pass over every match file."""
    global _scan_cache
    if _scan_cache is not None:
        return _scan_cache
    venues, team_names, seasons = set(), set(), set()
    dl_count = 0
    super_over_innings = 0
    season_vs_dates_mismatches = []
    tie_match_has_super_over = False
    match_count = 0
    for league, dirname in canon.LEAGUE_DIRS:
        for path in sorted((canon.DATA_ROOT / dirname).glob("*.json")):
            match_count += 1
            with open(path) as fh:
                match = json.load(fh)
            info = match["info"]
            venues.add(info["venue"])
            team_names.update(info["teams"])
            season = canon.canon_season(info)
            seasons.add((league, season))
            if season != canon.season_from_dates(info):
                season_vs_dates_mismatches.append(path.name)
            if canon.is_dl(info):
                dl_count += 1
            for innings in match.get("innings", []):
                team_names.add(innings["team"])
                if canon.is_super_over(innings):
                    super_over_innings += 1
                    if path.name == KNOWN_TIE_MATCH:
                        tie_match_has_super_over = True
    _scan_cache = {
        "match_count": match_count,
        "venues": venues,
        "team_names": team_names,
        "seasons": seasons,
        "dl_count": dl_count,
        "super_over_innings": super_over_innings,
        "season_vs_dates_mismatches": season_vs_dates_mismatches,
        "tie_match_has_super_over": tie_match_has_super_over,
    }
    return _scan_cache


class TestVenueCanonicalization(unittest.TestCase):
    def test_table_is_exhaustive_over_corpus(self):
        scan = corpus_scan()
        unmapped = {v for v in scan["venues"] if v not in canon.VENUE_CANON}
        self.assertEqual(unmapped, set(), f"unmapped venues: {sorted(unmapped)}")

    def test_table_matches_corpus_exactly(self):
        # Both directions: no stale keys, no missing keys (drift detector).
        scan = corpus_scan()
        self.assertEqual(set(canon.VENUE_CANON), scan["venues"])
        self.assertEqual(len(scan["venues"]), EXPECTED_RAW_VENUE_COUNT)

    def test_canonical_ground_snapshot(self):
        grounds = set(canon.VENUE_CANON.values())
        self.assertEqual(len(grounds), EXPECTED_CANONICAL_GROUND_COUNT)
        self.assertEqual(grounds, set(canon.GROUND_CITY), "every ground has a city")

    def test_known_renames_unify(self):
        self.assertEqual(canon.canon_venue("Feroz Shah Kotla"), "Arun Jaitley Stadium, Delhi")
        self.assertEqual(canon.canon_venue("Subrata Roy Sahara Stadium"), "MCA Stadium, Pune")
        self.assertEqual(
            canon.canon_venue("Punjab Cricket Association Stadium, Mohali"),
            canon.canon_venue("Punjab Cricket Association IS Bindra Stadium"),
        )
        self.assertEqual(
            canon.canon_venue("Sheikh Zayed Stadium"),
            canon.canon_venue("Zayed Cricket Stadium, Abu Dhabi"),
        )

    def test_unmapped_venue_raises(self):
        with self.assertRaises(KeyError):
            canon.canon_venue("Lord's")


class TestTeamCanonicalization(unittest.TestCase):
    def test_table_is_exhaustive_over_corpus(self):
        scan = corpus_scan()
        for name in scan["team_names"]:
            canon.canon_team(name)  # must not raise

    def test_canonical_universe_snapshot(self):
        scan = corpus_scan()
        observed = {canon.canon_team(n) for n in scan["team_names"]}
        self.assertEqual(observed, canon.KNOWN_TEAMS)

    def test_franchise_renames(self):
        self.assertEqual(canon.canon_team("Delhi Daredevils"), "Delhi Capitals")
        self.assertEqual(canon.canon_team("Kings XI Punjab"), "Punjab Kings")
        self.assertEqual(
            canon.canon_team("Royal Challengers Bangalore"), "Royal Challengers Bengaluru"
        )
        self.assertEqual(
            canon.canon_team("Rising Pune Supergiants"),
            canon.canon_team("Rising Pune Supergiant"),
        )

    def test_gujarat_teams_are_distinct(self):
        gujarat = {
            canon.canon_team("Gujarat Lions"),
            canon.canon_team("Gujarat Titans"),
            canon.canon_team("Gujarat Giants"),
        }
        self.assertEqual(len(gujarat), 3, "Lions / Titans / Giants must never unify")

    def test_deccan_chargers_is_not_sunrisers(self):
        self.assertNotEqual(
            canon.canon_team("Deccan Chargers"), canon.canon_team("Sunrisers Hyderabad")
        )

    def test_payoff_franchise_lists(self):
        self.assertEqual(len(canon.CURRENT_IPL_FRANCHISES), 10)
        self.assertEqual(len(canon.WPL_FRANCHISES), 5)
        for team in canon.CURRENT_IPL_FRANCHISES + canon.WPL_FRANCHISES:
            self.assertIn(team, canon.KNOWN_TEAMS)

    def test_unmapped_team_raises(self):
        with self.assertRaises(KeyError):
            canon.canon_team("Ahmedabad Rockets")


class TestSeasonNormalization(unittest.TestCase):
    def test_season_set_is_exactly_the_contract(self):
        scan = corpus_scan()
        expected = {("ipl", y) for y in canon.IPL_SEASONS} | {
            ("wpl", y) for y in canon.WPL_SEASONS
        }
        self.assertEqual(scan["seasons"], expected)
        self.assertEqual(len(expected), 23)  # 19 IPL + 4 WPL = 23 groups

    def test_slash_labels(self):
        self.assertEqual(canon.canon_season({"season": "2007/08"}), 2008)
        self.assertEqual(canon.canon_season({"season": "2009/10"}), 2010)
        self.assertEqual(canon.canon_season({"season": "2020/21"}), 2020)
        self.assertEqual(canon.canon_season({"season": "2022/23"}), 2023)
        self.assertEqual(canon.canon_season({"season": "2025/26"}), 2026)
        self.assertEqual(canon.canon_season({"season": 2017}), 2017)
        self.assertEqual(canon.canon_season({"season": "2009"}), 2009)

    def test_labels_agree_with_dates_for_every_match(self):
        scan = corpus_scan()
        self.assertEqual(scan["season_vs_dates_mismatches"], [])

    def test_unknown_label_raises(self):
        with self.assertRaises(Exception):
            canon.canon_season({"season": "1998/99"})


class TestFlags(unittest.TestCase):
    def test_match_count_snapshot(self):
        self.assertEqual(corpus_scan()["match_count"], EXPECTED_MATCH_COUNT)

    def test_dl_flag_snapshot(self):
        self.assertEqual(corpus_scan()["dl_count"], EXPECTED_DL_MATCHES)
        self.assertTrue(canon.is_dl({"outcome": {"method": "D/L", "winner": "x"}}))
        self.assertFalse(canon.is_dl({"outcome": {"winner": "x"}}))

    def test_super_over_detection_snapshot(self):
        scan = corpus_scan()
        self.assertEqual(scan["super_over_innings"], EXPECTED_SUPER_OVER_INNINGS)
        self.assertTrue(
            scan["tie_match_has_super_over"],
            f"{KNOWN_TIE_MATCH} (2017 tie) must contain super-over innings",
        )
        self.assertTrue(canon.is_super_over({"team": "x", "super_over": True}))
        self.assertFalse(canon.is_super_over({"team": "x"}))


if __name__ == "__main__":
    unittest.main()
