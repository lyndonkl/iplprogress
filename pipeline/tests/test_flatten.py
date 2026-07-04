"""Snapshot tests for the flattened contract artifacts in web/static/data/.

An independent recount (own ordering, own season derivation via dates[0],
own bit-packing implementation) is rebuilt from the raw corpus and compared
against what flatten.py emitted — n_points, group order/counts, the full
group-id stream, attrs round-trips on sampled matches, super-over exclusion
on a known tie match, and columnar array integrity.

If the artifacts are missing, the pipeline is built once in setUpModule.
"""

from __future__ import annotations

import gzip
import json
import sys
import unittest
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten

# Snapshot constants (hand-verified against the raw corpus, 2026-07-03).
EXPECTED_N_POINTS = 316_199  # all deliveries minus the 189 super-over balls
EXPECTED_SUPER_OVER_DELIVERIES = 189
EXPECTED_GROUPS = 23
SAMPLED_IPL_MATCH = "1082591.json"  # IPL 2017 opener, SRH v RCB
SAMPLED_WPL_MATCH = "1358929.json"  # WPL 2023 opener
TIE_MATCH = "1082625.json"  # IPL 2017 tie -> super over (excluded balls)

ART = None  # emitted artifacts, loaded once
REF = None  # independent recount, built once


def independent_outcome_class(dl):
    """Deliberately different implementation from flatten.outcome_class."""
    table = {0: None, 1: 1, 2: 2, 3: 2, 4: 3, 5: 5, 6: 4}
    cls = table[dl["runs"]["batter"]]
    if cls is None:
        cls = 0 if dl["runs"]["total"] == 0 else 5
    return cls


def independent_recount():
    """Rebuild the expected point stream straight from the raw corpus."""
    entries = []
    for league, dirname in canon.LEAGUE_DIRS:
        for path in (canon.DATA_ROOT / dirname).glob("*.json"):
            with open(path) as fh:
                date0 = str(json.load(fh)["info"]["dates"][0])
            entries.append((date0, int(path.stem), league, path))
    entries.sort(key=lambda e: (e[0], e[1]))

    order = [("ipl", y) for y in range(2008, 2027)] + [
        ("wpl", y) for y in range(2023, 2027)
    ]
    gi_of = {key: gi for gi, key in enumerate(order)}

    gis = array("H")
    attrs = bytearray()
    counts = [0] * len(order)
    match_slices = {}  # filename -> (start, end) in the point stream
    match_attrs = {}  # sampled filename -> expected attr bytes
    super_over_deliveries = 0
    tie_regular_innings = None

    for date0, _mid, league, path in entries:
        with open(path) as fh:
            match = json.load(fh)
        season = int(date0[:4])  # independent of canon.canon_season
        gi = gi_of[(league, season)]
        start = len(attrs)
        sampled = path.name in (SAMPLED_IPL_MATCH, SAMPLED_WPL_MATCH)
        regular_innings = 0
        for innings in match.get("innings", []):
            if innings.get("super_over"):
                super_over_deliveries += sum(
                    len(o["deliveries"]) for o in innings["overs"]
                )
                continue
            regular_innings += 1
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    byte = independent_outcome_class(dl)
                    if dl.get("wickets"):
                        byte |= 1 << 3
                    if league == "wpl":
                        byte |= 1 << 4
                    gis.append(gi)
                    attrs.append(byte)
                    counts[gi] += 1
                    if sampled:
                        match_attrs.setdefault(path.name, bytearray()).append(byte)
        match_slices[path.name] = (start, len(attrs))
        if path.name == TIE_MATCH:
            tie_regular_innings = regular_innings

    return {
        "gis": gis,
        "attrs": attrs,
        "counts": counts,
        "order": order,
        "match_slices": match_slices,
        "match_attrs": match_attrs,
        "super_over_deliveries": super_over_deliveries,
        "tie_regular_innings": tie_regular_innings,
    }


def setUpModule():
    global ART, REF
    out = canon.OUT_ROOT
    if not (out / "meta.json").exists():
        flatten.main()
    ART = {
        "meta": json.loads((out / "meta.json").read_text()),
        "groups": json.loads((out / "groups.json").read_text()),
        "group_ids": (out / "group_ids.u16").read_bytes(),
        "attrs": (out / "attrs.u8").read_bytes(),
        "columnar": json.loads(gzip.decompress((out / "columnar.json.gz").read_bytes())),
    }
    REF = independent_recount()


class TestMetaAndCounts(unittest.TestCase):
    def test_n_points_matches_hand_verified_recount(self):
        self.assertEqual(len(REF["attrs"]), EXPECTED_N_POINTS)
        self.assertEqual(ART["meta"]["n_points"], EXPECTED_N_POINTS)
        self.assertEqual(len(ART["attrs"]), EXPECTED_N_POINTS)
        self.assertEqual(len(ART["group_ids"]), 2 * EXPECTED_N_POINTS)

    def test_meta_contract_fields(self):
        self.assertEqual(ART["meta"]["built_at"], "unknown")
        self.assertEqual(ART["meta"]["point_order"], "chronological")
        for name in ("groups.json", "group_ids.u16", "attrs.u8", "columnar.json.gz"):
            sizes = ART["meta"]["files"][name]
            self.assertGreater(sizes["bytes_raw"], 0)
            self.assertGreater(sizes["bytes_gz"], 0)


class TestGroups(unittest.TestCase):
    def test_group_count_and_order(self):
        groups = ART["groups"]
        self.assertEqual(len(groups), EXPECTED_GROUPS)
        for gi, g in enumerate(groups):
            self.assertEqual(g["gi"], gi)
            self.assertEqual((g["league"], g["season"]), REF["order"][gi])

    def test_group_counts_match_recount(self):
        self.assertEqual([g["count"] for g in ART["groups"]], REF["counts"])
        self.assertEqual(sum(g["count"] for g in ART["groups"]), EXPECTED_N_POINTS)

    def test_group_ids_stream_is_exactly_the_recount(self):
        expected = array("H", REF["gis"])
        if sys.byteorder == "big":
            expected.byteswap()
        self.assertEqual(ART["group_ids"], expected.tobytes())


class TestAttrs(unittest.TestCase):
    def test_full_attrs_stream_matches_independent_packing(self):
        self.assertEqual(bytes(ART["attrs"]), bytes(REF["attrs"]))

    def test_bitpacking_roundtrip_on_sampled_matches(self):
        for name, expect_wpl in ((SAMPLED_IPL_MATCH, False), (SAMPLED_WPL_MATCH, True)):
            start, end = REF["match_slices"][name]
            emitted = ART["attrs"][start:end]
            expected = bytes(REF["match_attrs"][name])
            self.assertGreater(len(emitted), 100, name)
            self.assertEqual(emitted, expected, name)
            for byte in emitted:
                self.assertLessEqual(byte & 0b111, 5, "outcome class range")
                self.assertEqual(bool(byte & (1 << 4)), expect_wpl, name)
                self.assertEqual(byte >> 5, 0, "bits 5-7 must stay zero")

    def test_wicket_bit_plausible(self):
        wickets = sum(1 for b in ART["attrs"] if b & (1 << 3))
        # 15,752 wicket-carrying deliveries in the corpus (incl. retirements).
        self.assertEqual(wickets, sum(1 for b in REF["attrs"] if b & (1 << 3)))
        self.assertGreater(wickets, 10_000)
        self.assertLess(wickets, 20_000)


class TestSuperOverExclusion(unittest.TestCase):
    def test_known_tie_match_contributes_only_regular_innings(self):
        with open(canon.DATA_ROOT / "ipl_json" / TIE_MATCH) as fh:
            match = json.load(fh)
        so_innings = [i for i in match["innings"] if i.get("super_over")]
        regular = [i for i in match["innings"] if not i.get("super_over")]
        self.assertGreater(len(so_innings), 0, "tie match must have a super over")
        so_balls = sum(len(o["deliveries"]) for i in so_innings for o in i["overs"])
        regular_balls = sum(len(o["deliveries"]) for i in regular for o in i["overs"])
        start, end = REF["match_slices"][TIE_MATCH]
        self.assertEqual(end - start, regular_balls)
        self.assertNotEqual(end - start, regular_balls + so_balls)
        self.assertEqual(REF["tie_regular_innings"], 2)

    def test_corpus_wide_exclusion_totals(self):
        self.assertEqual(REF["super_over_deliveries"], EXPECTED_SUPER_OVER_DELIVERIES)
        self.assertEqual(
            EXPECTED_N_POINTS + EXPECTED_SUPER_OVER_DELIVERIES, 316_388
        )  # the blueprint's headline count includes super-over balls


class TestColumnar(unittest.TestCase):
    def test_all_arrays_have_length_n_points(self):
        arrays = ART["columnar"]["arrays"]
        self.assertEqual(
            set(arrays),
            {
                "season", "league", "innings", "over", "ball_index_in_over",
                "batter", "bowler", "batting_team", "runs_batter", "runs_total",
                "outcome", "wicket",
            },
        )
        for name, values in arrays.items():
            self.assertEqual(len(values), EXPECTED_N_POINTS, name)
        self.assertEqual(ART["columnar"]["n_points"], EXPECTED_N_POINTS)

    def test_value_ranges(self):
        a = ART["columnar"]["arrays"]
        self.assertLessEqual(set(a["league"]), {0, 1})
        self.assertLessEqual(set(a["innings"]), {1, 2})
        self.assertLessEqual(set(a["outcome"]), set(range(6)))
        self.assertLessEqual(set(a["wicket"]), {0, 1})
        self.assertEqual(min(a["over"]), 0)
        self.assertLessEqual(max(a["over"]), 19)
        self.assertGreaterEqual(min(a["ball_index_in_over"]), 0)
        self.assertLessEqual(set(a["runs_batter"]), {0, 1, 2, 3, 4, 5, 6})
        self.assertTrue(
            all(rt >= rb for rt, rb in zip(a["runs_total"], a["runs_batter"]))
        )
        seasons = set(a["season"])
        self.assertLessEqual(seasons, set(range(2008, 2027)))

    def test_dict_encoding_is_consistent(self):
        c = ART["columnar"]
        for field in ("batter", "bowler", "batting_team"):
            names = c["dicts"][field]
            self.assertEqual(len(set(names)), len(names), f"{field} dict has dupes")
            self.assertLess(max(c["arrays"][field]), len(names), field)
            self.assertGreaterEqual(min(c["arrays"][field]), 0, field)
        team_names = set(c["dicts"]["batting_team"])
        self.assertLessEqual(team_names, canon.KNOWN_TEAMS)

    def test_columnar_agrees_with_attrs_bits(self):
        a = ART["columnar"]["arrays"]
        attrs = ART["attrs"]
        for i in range(0, EXPECTED_N_POINTS, 997):  # dense stride sample
            byte = attrs[i]
            self.assertEqual(a["outcome"][i], byte & 0b111, i)
            self.assertEqual(a["wicket"][i], (byte >> 3) & 1, i)
            self.assertEqual(a["league"][i], (byte >> 4) & 1, i)

    def test_columnar_league_season_agrees_with_group_ids(self):
        a = ART["columnar"]["arrays"]
        gis = array("H")
        gis.frombytes(ART["group_ids"])
        if sys.byteorder == "big":
            gis.byteswap()
        order = REF["order"]
        for i in range(0, EXPECTED_N_POINTS, 997):
            league, season = order[gis[i]]
            self.assertEqual(a["league"][i], 1 if league == "wpl" else 0, i)
            self.assertEqual(a["season"][i], season, i)


if __name__ == "__main__":
    unittest.main()
