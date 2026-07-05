"""Engine #5 snapshot tests — entry states / derived batting positions (R2a).

The emitted engines/entry.json is checked against an independent per-match
recompute of the entry event (first ball as striker or non_striker), plus the
structural invariants the entry map depends on, plus a delivery-for-delivery
spot check of the 2019 IPL Final (the same match test_r1b hand-verifies).
"""

from __future__ import annotations

import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import entry

PRESET_FILE = "1181768.json"          # 2019 IPL Final, MI beat CSK by 1
PRESET_TEAMS = {"Mumbai Indians", "Chennai Super Kings"}

ART = None


def setUpModule():
    global ART
    out = canon.OUT_ROOT
    if not (out / "engines" / "entry.json").exists():
        entry.main()
    doc = json.loads((out / "engines" / "entry.json").read_text())
    ART = {"doc": doc, "a": doc["arrays"], "batter": doc["dicts"]["batter"]}


def recompute_match(path: Path):
    """Independent entry-state recompute for one raw match, keyed by innings."""
    with open(path) as fh:
        match = json.load(fh)
    out = {}  # innings_no -> [rows in entry order]
    ino = 0
    for inn in match.get("innings", []):
        if inn.get("super_over"):
            continue
        ino += 1
        target = inn.get("target") or {}
        t_runs, t_overs = target.get("runs"), target.get("overs")
        rows, seen = [], {}
        legal = wkts = score = 0
        for over in inn["overs"]:
            for dl in over["deliveries"]:
                for who in (dl["batter"], dl["non_striker"]):
                    if who in seen:
                        continue
                    rrr = None
                    if ino == 2 and t_runs is not None and t_overs is not None:
                        rem = int(round(float(t_overs) * 6)) - legal
                        if rem > 0:
                            rrr = round((t_runs - score) * 6.0 / rem, 3)
                    rec = {"batter": who, "position": len(rows) + 1,
                           "entry_ball": legal, "wickets": wkts, "rrr": rrr,
                           "balls_faced": 0, "runs": 0, "dismissed": 0}
                    seen[who] = rec
                    rows.append(rec)
                if "wides" not in dl.get("extras", {}):
                    r = seen[dl["batter"]]
                    r["balls_faced"] += 1
                    r["runs"] += dl["runs"]["batter"]
                score += dl["runs"]["total"]
                if "wides" not in dl.get("extras", {}) and "noballs" not in dl.get("extras", {}):
                    legal += 1
                for w in dl.get("wickets", []):
                    if w["kind"] in ("retired hurt", "retired out"):
                        continue
                    wkts += 1
                    if w.get("player_out") in seen:
                        seen[w["player_out"]]["dismissed"] = 1
        out[ino] = rows
    return match["info"], out


def rows_for(match_index):
    """Emitted rows for a match_index, grouped by innings, in table order."""
    a = ART["a"]
    by_inn = defaultdict(list)
    for i in range(ART["doc"]["count"]):
        if a["match_index"][i] == match_index:
            by_inn[a["innings"][i]].append({
                "batter": ART["batter"][a["batter"][i]],
                "position": a["position"][i], "entry_ball": a["entry_ball"][i],
                "wickets": a["wickets"][i], "rrr": a["rrr"][i],
                "balls_faced": a["balls_faced"][i], "runs": a["runs"][i],
                "dismissed": a["dismissed"][i],
            })
    return by_inn


class TestInvariants(unittest.TestCase):
    def setUp(self):
        self.a = ART["a"]
        self.n = ART["doc"]["count"]
        self.groups = defaultdict(list)
        for i in range(self.n):
            self.groups[(self.a["match_index"][i], self.a["innings"][i])].append(i)

    def test_positions_contiguous_from_one(self):
        for idxs in self.groups.values():
            positions = sorted(self.a["position"][i] for i in idxs)
            self.assertEqual(positions, list(range(1, len(positions) + 1)))

    def test_openers_enter_at_zero(self):
        for i in range(self.n):
            if self.a["position"][i] in (1, 2):
                self.assertEqual(self.a["entry_ball"][i], 0, i)
                self.assertEqual(self.a["wickets"][i], 0, i)

    def test_entry_ball_and_wickets_monotone_in_position(self):
        for idxs in self.groups.values():
            idxs.sort(key=lambda i: self.a["position"][i])
            ebs = [self.a["entry_ball"][i] for i in idxs]
            wks = [self.a["wickets"][i] for i in idxs]
            self.assertEqual(ebs, sorted(ebs))
            self.assertEqual(wks, sorted(wks))

    def test_rrr_only_on_chases(self):
        a = self.a
        for i in range(self.n):
            if a["innings"][i] == 1:
                self.assertIsNone(a["rrr"][i], i)
        # ~99% of second-innings entries carry a target-derived RRR.
        i2 = [i for i in range(self.n) if a["innings"][i] == 2]
        with_rrr = sum(1 for i in i2 if a["rrr"][i] is not None)
        self.assertGreater(with_rrr / len(i2), 0.98)

    def test_ranges(self):
        a = self.a
        self.assertTrue(all(0 <= w <= 9 for w in a["wickets"]))
        self.assertTrue(all(v in (0, 1) for v in a["dismissed"]))
        self.assertTrue(all(v in (0, 1) for v in a["league"]))
        self.assertTrue(all(b >= 0 for b in a["entry_ball"]))
        self.assertTrue(all(b >= 0 for b in a["balls_faced"]))


class TestAgainstIndependentRecount(unittest.TestCase):
    def test_full_corpus_count_and_openers(self):
        # Every innings contributes exactly its distinct batters; openers are
        # two per (completed) innings.
        total = openers = 0
        for _d, _m, _lg, path in flatten.sorted_match_files():
            _info, out = recompute_match(path)
            for rows in out.values():
                total += len(rows)
                openers += sum(1 for r in rows if r["position"] in (1, 2))
        self.assertEqual(ART["doc"]["count"], total)
        a = ART["a"]
        emitted_openers = sum(1 for i in range(ART["doc"]["count"])
                              if a["position"][i] in (1, 2))
        self.assertEqual(emitted_openers, openers)


class TestPresetSpotCheck(unittest.TestCase):
    def _preset_index(self):
        matches = flatten.build_matches()
        hits = [i for i, m in enumerate(matches)
                if m["league"] == "ipl" and m["season"] == 2019
                and m["stage"] == "Final" and set(m["teams"]) == PRESET_TEAMS]
        self.assertEqual(len(hits), 1)
        return hits[0]

    def test_2019_final_entry_states_match_raw(self):
        idx = self._preset_index()
        _info, expected = recompute_match(canon.DATA_ROOT / "ipl_json" / PRESET_FILE)
        emitted = rows_for(idx)
        self.assertEqual(set(emitted), set(expected))
        for ino in expected:
            got = sorted(emitted[ino], key=lambda r: r["position"])
            want = sorted(expected[ino], key=lambda r: r["position"])
            self.assertEqual(got, want, ino)

    def test_chase_openers_rrr_equals_target_rate(self):
        # CSK chased 150 to win off 20 overs; both openers enter at 0 needing
        # 150 x 6 / 120 run rate.
        idx = self._preset_index()
        emitted = rows_for(idx)
        openers = [r for r in emitted[2] if r["position"] in (1, 2)]
        self.assertEqual(len(openers), 2)
        for r in openers:
            self.assertEqual(r["entry_ball"], 0)
            self.assertIsNotNone(r["rrr"])
            self.assertAlmostEqual(r["rrr"], openers[0]["rrr"], places=3)


class TestDeterminism(unittest.TestCase):
    def test_on_disk_equals_fresh_build(self):
        fresh = flatten.compact_json(entry.entry_doc(entry.build()), sort_keys=True)
        self.assertEqual(
            (canon.OUT_ROOT / "engines" / "entry.json").read_bytes(), fresh
        )


if __name__ == "__main__":
    unittest.main()
