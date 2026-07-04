"""Snapshot tests for wallheat.u8 — the Ch 1 ignition-wall era-relative-intent
buffer (thesis-beat recolour) — and its scenes/ch1.json scale/legend config.

The recount is a deliberately different implementation from wallheat.py: own
file ordering, own accumulators, own clamping. It rebuilds every per-delivery
byte from the CONFIG'S published lo/hi/neutral (not wallheat's constants), so
the buffer, the config, and an independent cell recount must all agree. It
also verifies the desired thesis: a recent early-ball cell is clearly hotter
than the same 2008-10 cell, while 2008-10 early balls sit at neutral.
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
import scenes
import wallheat

EXPECTED_N_POINTS = 316_199
MAXN = 30

ART = None  # loaded artifacts
REF = None  # independent recount


def _clamp_n(bf: int) -> int:
    return MAXN if bf > MAXN else bf  # bf >= 1 for every non-wide delivery


def independent_recount():
    """Own season-blocked pass: per-delivery (league, season, ballsfaced) in
    point order + cell run/ball sums, all derived independently of wallheat.py
    and flatten.py (season = dates[0] year, own sort key, own clamping)."""
    entries = []
    for league, dirname in (("ipl", "ipl_json"), ("wpl", "wpl_json")):
        for path in (canon.DATA_ROOT / dirname).glob("*.json"):
            with open(path) as fh:
                date0 = str(json.load(fh)["info"]["dates"][0])
            entries.append((date0, int(path.stem), league, path))
    entries.sort(key=lambda e: (int(e[0][:4]), e[2] != "ipl", e[0], e[1]))

    league_seq: list = []
    season_seq: list = []
    ballsfaced = bytearray()
    runs_batter: list = []
    cell_runs: dict = defaultdict(int)
    cell_balls: dict = defaultdict(int)

    for date0, _mid, league, path in entries:
        with open(path) as fh:
            match = json.load(fh)
        season = int(date0[:4])  # independent of canon.canon_season
        for innings in match.get("innings", []):
            if innings.get("super_over"):
                continue
            faced: dict = {}
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    rb = dl["runs"]["batter"]
                    league_seq.append(league)
                    season_seq.append(season)
                    runs_batter.append(rb)
                    if "wides" in dl.get("extras", {}):
                        ballsfaced.append(0)
                    else:
                        c = faced.get(dl["batter"], 0) + 1
                        faced[dl["batter"]] = c
                        bf = min(c, 255)
                        ballsfaced.append(bf)
                        key = (league, season, _clamp_n(bf))
                        cell_runs[key] += rb
                        cell_balls[key] += 1

    # baselineSR[n] pooled over IPL 2008,2009,2010 (runs per ball).
    base_runs = [0] * (MAXN + 1)
    base_balls = [0] * (MAXN + 1)
    for (lg, se, nn), balls in cell_balls.items():
        if lg == "ipl" and se in (2008, 2009, 2010):
            base_runs[nn] += cell_runs[(lg, se, nn)]
            base_balls[nn] += balls
    baseline_rpb = [
        base_runs[nn] / base_balls[nn] if base_balls[nn] else None
        for nn in range(MAXN + 1)
    ]
    cell_delta = {
        k: cell_runs[k] / cell_balls[k] - baseline_rpb[k[2]] for k in cell_balls
    }
    return {
        "league_seq": league_seq,
        "season_seq": season_seq,
        "ballsfaced": ballsfaced,
        "cell_delta": cell_delta,
        "baseline_rpb": baseline_rpb,
    }


def setUpModule():
    global ART, REF
    out = canon.OUT_ROOT
    if not (out / "wallheat.u8").exists() or not (out / "meta.json").exists():
        flatten.main()
    if not (out / "scenes" / "ch1.json").exists():
        scenes.main()
    ART = {
        "meta": json.loads((out / "meta.json").read_text()),
        "wallheat": (out / "wallheat.u8").read_bytes(),
        "ballsfaced": (out / "ballsfaced.u8").read_bytes(),
        "ch1": json.loads((out / "scenes" / "ch1.json").read_text()),
    }
    REF = independent_recount()


def cfg():
    return ART["ch1"]["ignition"]["wallheat"]


def cfg_quantize(delta: float) -> int:
    """Quantize using the CONFIG'S published lo/hi (independent of wallheat)."""
    lo, hi = cfg()["lo"], cfg()["hi"]
    v = round((delta - lo) / (hi - lo) * 255)
    return 0 if v < 0 else 255 if v > 255 else v


class TestWallHeatBuffer(unittest.TestCase):
    def test_length_is_n_points(self):
        self.assertEqual(len(ART["wallheat"]), EXPECTED_N_POINTS)
        self.assertEqual(ART["meta"]["n_points"], EXPECTED_N_POINTS)
        self.assertEqual(len(ART["wallheat"]), len(ART["ballsfaced"]))

    def test_wides_are_the_neutral_byte(self):
        neutral = cfg()["neutral_byte"]
        n_wide = 0
        for i, bf in enumerate(ART["ballsfaced"]):
            if bf == 0:
                self.assertEqual(ART["wallheat"][i], neutral, f"wide at {i}")
                n_wide += 1
        self.assertGreater(n_wide, 8_000)  # ~10k wides in the corpus

    def test_full_stream_matches_independent_recount(self):
        """Every byte == quantize(cell delta) from an independent recount,
        using the config's lo/hi; wides == neutral. Buffer, config and recount
        must all agree."""
        neutral = cfg()["neutral_byte"]
        expected = bytearray(len(ART["wallheat"]))
        for i in range(len(expected)):
            bf = REF["ballsfaced"][i]
            if bf == 0:
                expected[i] = neutral
            else:
                key = (REF["league_seq"][i], REF["season_seq"][i], _clamp_n(bf))
                expected[i] = cfg_quantize(REF["cell_delta"][key])
        # ballsfaced streams must line up first (same point order).
        self.assertEqual(bytes(REF["ballsfaced"]), bytes(ART["ballsfaced"]))
        self.assertEqual(bytes(ART["wallheat"]), bytes(expected))

    def test_deterministic_second_run(self):
        b1, _ = wallheat.build()
        b2, _ = wallheat.build()
        self.assertEqual(bytes(b1), bytes(b2))
        self.assertEqual(bytes(b1), bytes(ART["wallheat"]))


class TestWallHeatThesis(unittest.TestCase):
    def _cell_byte(self, league, season, n):
        return cfg_quantize(REF["cell_delta"][(league, season, n)])

    def test_2008_10_early_balls_sit_at_neutral(self):
        """The pooled 2008-10 batter IS the baseline, so 2008-10 early-ball
        deliveries average to the neutral byte (each ball-index column is
        centred on its own 2008-10 value)."""
        neutral = cfg()["neutral_byte"]
        total = count = 0
        for i, bf in enumerate(ART["ballsfaced"]):
            if (
                REF["league_seq"][i] == "ipl"
                and REF["season_seq"][i] in (2008, 2009, 2010)
                and 1 <= bf <= 10
            ):
                total += ART["wallheat"][i]
                count += 1
        self.assertGreater(count, 10_000)
        mean_byte = total / count
        self.assertAlmostEqual(mean_byte, neutral, delta=3.0)
        # a specific early 2008-10 cell also lands near neutral.
        self.assertLessEqual(abs(self._cell_byte("ipl", 2008, 1) - neutral), 15)

    def test_recent_ball1_clearly_hotter_than_2008(self):
        old = self._cell_byte("ipl", 2008, 1)
        recent = self._cell_byte("ipl", 2026, 1)
        self.assertGreater(recent, old + 40, f"recent {recent} vs old {old}")
        # the whole recent era outguns the 2008-10 corner at ball 1.
        for season in (2023, 2024, 2025, 2026):
            self.assertGreater(self._cell_byte("ipl", season, 1), old)

    def test_hot_and_cool_both_exercised(self):
        """A genuine diverging scale: some cells below neutral (cool), the hot
        corner near the top of the range."""
        neutral = cfg()["neutral_byte"]
        self.assertLess(min(ART["wallheat"]), neutral)  # cool cells exist
        self.assertGreater(max(ART["wallheat"]), 200)  # hot cells exist
        self.assertLess(self._cell_byte("ipl", 2011, 1), neutral)  # a cool cell


class TestWallHeatConfig(unittest.TestCase):
    def test_scale_fields_present_and_consistent(self):
        c = cfg()
        self.assertEqual(c["buffer"], "wallheat.u8")
        self.assertEqual(c["bytes_per_point"], 1)
        self.assertEqual(c["clamp_ball_index"], MAXN)
        self.assertLess(c["lo"], 0)
        self.assertGreater(c["hi"], 0)
        # neutral_byte is exactly the byte at delta 0 under lo/hi.
        v = round((0 - c["lo"]) / (c["hi"] - c["lo"]) * 255)
        self.assertEqual(c["neutral_byte"], max(0, min(255, v)))
        self.assertEqual(c["lo_sr_delta"], round(c["lo"] * 100.0, 1))
        self.assertEqual(c["hi_sr_delta"], round(c["hi"] * 100.0, 1))

    def test_baseline_sr_matches_ignition_curve(self):
        """baseline_sr[n] is the 2008-10 SR at ball-index n — for n < 30 it
        equals the (unclamped) ignition curve; n = 30 is the clamped 30+
        pool and legitimately differs."""
        c = cfg()
        self.assertEqual(len(c["baseline_sr"]), MAXN)
        ign = ART["ch1"]["ignition"]["sr_by_ball_index"]["ipl 2008-2010"]
        self.assertEqual(c["baseline_sr"][:28], ign[:28])
        self.assertNotEqual(c["baseline_sr"][29], ign[29])  # clamped 30+ vs exact 30
        # every baseline present (2008-10 reaches every index 1..30).
        self.assertTrue(all(x is not None and x > 0 for x in c["baseline_sr"]))

    def test_three_legend_labels(self):
        c = cfg()
        self.assertEqual(len(c["legend_labels"]), 3)
        self.assertEqual(len(c["legend"]), 3)
        self.assertEqual([r["key"] for r in c["legend"]], ["cool", "neutral", "hot"])
        self.assertEqual(c["legend"][1]["byte"], c["neutral_byte"])
        self.assertEqual(c["legend"][0]["byte"], 0)
        self.assertEqual(c["legend"][2]["byte"], 255)
        for row in c["legend"]:
            self.assertTrue(row["label"].strip())
        self.assertTrue(c["definition"].strip())

    def test_wallheat_in_meta_files_map(self):
        entry = ART["meta"]["files"].get("wallheat.u8")
        self.assertIsInstance(entry, dict)
        self.assertEqual(entry["bytes_raw"], EXPECTED_N_POINTS)
        self.assertGreater(entry["bytes_gz"], 0)


if __name__ == "__main__":
    unittest.main()
