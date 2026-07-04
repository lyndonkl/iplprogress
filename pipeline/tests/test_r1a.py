"""Snapshot tests for the R1a data-contract addendum artifacts.

Covers ballsfaced.u8 (hand-checked-match round-trip + full-stream recount),
team.u8 + teams.json (full recount with an independent rename map + renamed-
franchise and WPL-id spot checks), scenes/coldopen.json (the data-profile
season tables, hard-coded), scenes/ch1.json (independent recount of every
section + the metrics-catalog teaser reconciliations), and payoff/ch1.json
(the enriched 16-variant spec).

The recount is a deliberately different implementation from flatten.py /
scenes.py: own file ordering, own accumulators, own banding. Hard-coded
constants come from research/data-profile.md and research/metrics-catalog.md
(verified teasers) plus public scorecards for the hand-checked match.
"""

from __future__ import annotations

import json
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import payoff_harness
import scenes

# ---------------------------------------------------------------------------
# Snapshot constants
# ---------------------------------------------------------------------------

# Hand-checked match: IPL 2008 opener (335982), KKR 222/3 v RCB.
# Public scorecard: BB McCullum 158* off 73 balls; SC Ganguly 10 off 12;
# V Kohli (debut) 1 off 5. Ball counts re-verified by hand against the raw
# JSON on 2026-07-04.
HAND_MATCH = "335982.json"
HAND_BALLS = {"BB McCullum": 73, "SC Ganguly": 12, "V Kohli": 5}

DD_MATCH = "335984.json"  # 2008: Rajasthan Royals bat 1st, DELHI DAREDEVILS 2nd
WPL_OPENER = "1358929.json"  # WPL 2023 opener: Mumbai Indians (W) bat 1st

# data-profile.md season tables (IPL 2008..2026, WPL 2023..2026).
IPL_MATCHES = [58, 57, 60, 73, 74, 76, 60, 59, 60, 59, 60, 60, 60, 60, 74, 74, 71, 74, 74]
IPL_TOTALS200 = [11, 1, 9, 5, 5, 4, 9, 7, 6, 10, 15, 11, 13, 9, 18, 37, 41, 52, 65]
IPL_AVG_FIRST_FULL = [163.3, 150.3, 164.8, 155.6, 158.4, 156.6, 163.7, 167.8, 164.3,
                      166.4, 172.1, 168.5, 169.5, 159.3, 171.1, 183.0, 190.1, 192.3, 195.8]
WPL_MATCHES = [22, 22, 22, 22]
WPL_TOTALS200 = [4, 0, 5, 5]
WPL_AVG_FIRST_FULL = [156.6, 153.1, 163.7, 169.1]

# metrics-catalog.md verified teasers (Ch 1).
TEASER_F10_SR_IPL_EARLY = 108.0
TEASER_F10_SR_IPL_RECENT = 135.3
TEASER_F10_SR_WPL = 110.5
TEASER_F10_HAZARD_EARLY = 5.04
TEASER_F10_HAZARD_RECENT = 4.93
TEASER_AERIAL_EARLY = (7.3, 58.7)  # attempts/100, execution%
TEASER_AERIAL_RECENT = (11.4, 67.3)
TEASER_SIXES_2008 = {"sixes": 623, "players_10plus_sixes": 18, "top10_share_pct": 35.9}
TEASER_SIXES_2026 = {"sixes": 1426, "players_10plus_sixes": 58, "top10_share_pct": 28.1}
TEASER_FOURS_PCT = {"wpl": 46.8, "ipl_recent": 33.9}
TEASER_SIXSHARE_PCT = {"wpl": 15.5, "ipl_recent": 29.0}
TEASER_RR_Y1_4 = {"ipl": [8.31, 7.48, 8.13, 7.73], "wpl": [8.08, 7.86, 8.37, 8.54]}

EXPECTED_PLAYERS = 938  # faced or bowled at least one ball
EXPECTED_N_POINTS = 316_199

BANDS = {  # own banding, independent of scenes.py
    ("ipl", 2008): "ipl 2008-2010", ("ipl", 2009): "ipl 2008-2010", ("ipl", 2010): "ipl 2008-2010",
    ("ipl", 2011): "ipl 2011-2015", ("ipl", 2012): "ipl 2011-2015", ("ipl", 2013): "ipl 2011-2015",
    ("ipl", 2014): "ipl 2011-2015", ("ipl", 2015): "ipl 2011-2015",
    ("ipl", 2016): "ipl 2016-2019", ("ipl", 2017): "ipl 2016-2019", ("ipl", 2018): "ipl 2016-2019",
    ("ipl", 2019): "ipl 2016-2019",
    ("ipl", 2020): "ipl 2020-2022", ("ipl", 2021): "ipl 2020-2022", ("ipl", 2022): "ipl 2020-2022",
    ("ipl", 2023): "ipl 2023-2026", ("ipl", 2024): "ipl 2023-2026", ("ipl", 2025): "ipl 2023-2026",
    ("ipl", 2026): "ipl 2023-2026",
    ("wpl", 2023): "wpl 2023-2026", ("wpl", 2024): "wpl 2023-2026", ("wpl", 2025): "wpl 2023-2026",
    ("wpl", 2026): "wpl 2023-2026",
}
RENAMES = {  # own copy, independent of canon.TEAM_RENAMES
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
}

ART = None
REF = None


class Band:
    def __init__(self):
        self.runs = [0] * 31  # batter runs at faced-index n (1..30)
        self.balls = [0] * 31
        self.reaching = [0] * 31  # batter-innings that faced >= n
        self.out_at = [0] * 31  # dismissed at faced-count n
        self.innings = 0
        self.f10_balls = 0
        self.f10_events = 0  # every dismissal at faced-count 0..10
        self.aerial = [0, 0, 0]  # balls faced, sixes, caught (excl c&b)


class Season:
    def __init__(self):
        self.matches = 0
        self.deliveries = 0
        self.totals200 = 0
        self.first_full = []
        self.f10 = [0, 0]  # balls, runs
        self.runs = [0, 0, 0, 0]  # total, four-runs, six-runs, legal balls
        self.sixes = Counter()
        self.balls_faced = Counter()


def independent_recount():
    entries = []
    for league, dirname in (("ipl", "ipl_json"), ("wpl", "wpl_json")):
        for path in (canon.DATA_ROOT / dirname).glob("*.json"):
            with open(path) as fh:
                date0 = str(json.load(fh)["info"]["dates"][0])
            entries.append((date0, int(path.stem), league, path))
    entries.sort(key=lambda e: (e[0], e[1]))

    teams_doc = json.loads((canon.OUT_ROOT / "teams.json").read_text())
    tid = {(t["league"], t["name"]): t["id"] for t in teams_doc}

    bands = defaultdict(Band)
    seasons = defaultdict(Season)
    players = set()
    ballsfaced = bytearray()
    team_ids = bytearray()
    match_slices = {}
    n_wides = 0
    n_matches = 0

    for date0, _mid, league, path in entries:
        with open(path) as fh:
            match = json.load(fh)
        n_matches += 1
        season = int(date0[:4])  # independent of canon.canon_season
        ss = seasons[(league, season)]
        ss.matches += 1
        bd = bands[BANDS[(league, season)]]
        start = len(ballsfaced)

        info = match["info"]
        method = info.get("outcome", {}).get("method", "")
        full_first = "D/L" not in str(method) and info["outcome"].get("result") != "no result"
        first_total = None

        inn_no = 0
        for innings in match.get("innings", []):
            if innings.get("super_over"):
                continue
            inn_no += 1
            if inn_no == 2:
                overs = (innings.get("target") or {}).get("overs")
                if overs is not None and float(overs) < 20:
                    full_first = False
            franchise = tid[(league, RENAMES.get(innings["team"], innings["team"]))]
            faced = Counter()
            at_crease = set()
            dismissed = {}  # name -> faced-count when out
            total = 0
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    team_ids.append(franchise)
                    ss.deliveries += 1
                    extras = dl.get("extras", {})
                    wide = "wides" in extras
                    rb, rt = dl["runs"]["batter"], dl["runs"]["total"]
                    total += rt
                    ss.runs[0] += rt
                    ss.runs[1] += 4 if rb == 4 else 0
                    ss.runs[2] += 6 if rb == 6 else 0
                    if not wide and "noballs" not in extras:
                        ss.runs[3] += 1
                    players.add(dl["batter"])
                    players.add(dl["bowler"])
                    at_crease.add(dl["batter"])
                    at_crease.add(dl["non_striker"])
                    if wide:
                        n_wides += 1
                        ballsfaced.append(0)
                    else:
                        faced[dl["batter"]] += 1
                        n = faced[dl["batter"]]
                        ballsfaced.append(min(n, 255))
                        ss.balls_faced[dl["batter"]] += 1
                        bd.aerial[0] += 1
                        if rb == 6:
                            ss.sixes[dl["batter"]] += 1
                            bd.aerial[1] += 1
                        if n <= 10:
                            ss.f10[0] += 1
                            ss.f10[1] += rb
                            bd.f10_balls += 1
                        if n <= 30:
                            bd.balls[n] += 1
                            bd.runs[n] += rb
                    for w in dl.get("wickets", []):
                        if w["kind"] == "caught":
                            bd.aerial[2] += 1
                        if w["kind"] not in ("retired hurt", "retired out"):
                            c = faced[w["player_out"]]
                            dismissed[w["player_out"]] = c
                            if c <= 10:
                                bd.f10_events += 1
            for batter in at_crease:
                bd.innings += 1
                n = faced[batter]
                for i in range(1, min(n, 30) + 1):
                    bd.reaching[i] += 1
                c = dismissed.get(batter)
                if c is not None and 1 <= c <= 30:
                    bd.out_at[c] += 1
            if inn_no == 1:
                first_total = total
            if total >= 200:
                ss.totals200 += 1
        match_slices[path.name] = (start, len(ballsfaced))
        if full_first and first_total is not None:
            ss.first_full.append(first_total)

    return {
        "bands": bands,
        "seasons": seasons,
        "players": players,
        "ballsfaced": ballsfaced,
        "team_ids": team_ids,
        "match_slices": match_slices,
        "n_wides": n_wides,
        "n_matches": n_matches,
        "teams_doc": teams_doc,
        "tid": tid,
    }


def defier_recount_ipl_recent():
    """Per-batter survival-to-10 + SR-through-10 for the ipl 2023-2026 band
    (independent verification of one defiers cell)."""
    stats = {}  # name -> [innings, balls_total, reach10, runs<=10, balls<=10]
    for league, dirname in (("ipl", "ipl_json"),):
        for path in (canon.DATA_ROOT / dirname).glob("*.json"):
            with open(path) as fh:
                match = json.load(fh)
            if int(str(match["info"]["dates"][0])[:4]) < 2023:
                continue
            for innings in match.get("innings", []):
                if innings.get("super_over"):
                    continue
                faced = Counter()
                runs10 = Counter()
                balls10 = Counter()
                at_crease = set()
                for over in innings["overs"]:
                    for dl in over["deliveries"]:
                        at_crease.add(dl["batter"])
                        at_crease.add(dl["non_striker"])
                        if "wides" in dl.get("extras", {}):
                            continue
                        b = dl["batter"]
                        faced[b] += 1
                        if faced[b] <= 10:
                            runs10[b] += dl["runs"]["batter"]
                            balls10[b] += 1
                for b in at_crease:
                    rec = stats.setdefault(b, [0, 0, 0, 0, 0])
                    rec[0] += 1
                    rec[1] += faced[b]
                    if faced[b] >= 10:
                        rec[2] += 1
                    rec[3] += runs10[b]
                    rec[4] += balls10[b]
    return stats


def setUpModule():
    global ART, REF
    out = canon.OUT_ROOT
    if not (out / "meta.json").exists():
        flatten.main()
    if not (out / "scenes" / "ch1.json").exists():
        scenes.main()
    if not (out / "payoff" / "ch1.json").exists():
        payoff_harness.main()
    ART = {
        "meta": json.loads((out / "meta.json").read_text()),
        "ballsfaced": (out / "ballsfaced.u8").read_bytes(),
        "team": (out / "team.u8").read_bytes(),
        "teams": json.loads((out / "teams.json").read_text()),
        "groups": json.loads((out / "groups.json").read_text()),
        "coldopen": json.loads((out / "scenes" / "coldopen.json").read_text()),
        "ch1": json.loads((out / "scenes" / "ch1.json").read_text()),
        "payoff": json.loads((out / "payoff" / "ch1.json").read_text()),
    }
    REF = independent_recount()


def band_art(section, key):
    return ART["ch1"][section][key]


class TestBallsFaced(unittest.TestCase):
    def test_full_stream_matches_independent_recount(self):
        self.assertEqual(len(ART["ballsfaced"]), EXPECTED_N_POINTS)
        self.assertEqual(bytes(ART["ballsfaced"]), bytes(REF["ballsfaced"]))

    def test_hand_checked_match(self):
        """McCullum 158* off 73, Ganguly off 12, Kohli off 5 (public scorecard)."""
        start, end = REF["match_slices"][HAND_MATCH]
        emitted = ART["ballsfaced"][start:end]
        with open(canon.DATA_ROOT / "ipl_json" / HAND_MATCH) as fh:
            match = json.load(fh)
        # Walk the match's deliveries alongside the emitted bytes.
        i = 0
        max_seen = Counter()
        for innings in match["innings"]:
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    v = emitted[i]
                    if "wides" in dl.get("extras", {}):
                        self.assertEqual(v, 0, f"wide at offset {i} must be 0")
                    else:
                        self.assertEqual(
                            v, max_seen[dl["batter"]] + 1,
                            f"ball index must increment per batter (offset {i})",
                        )
                        max_seen[dl["batter"]] = v
                    i += 1
        self.assertEqual(i, end - start)
        for name, balls in HAND_BALLS.items():
            self.assertEqual(max_seen[name], balls, name)

    def test_wides_are_exactly_the_zeros(self):
        zeros = sum(1 for b in ART["ballsfaced"] if b == 0)
        self.assertEqual(zeros, REF["n_wides"])
        self.assertGreater(zeros, 8_000)  # ~10k wides in the corpus
        # Nobody has ever faced 160 balls in a T20 innings; the 255 cap is slack.
        self.assertLess(max(ART["ballsfaced"]), 160)
        self.assertGreaterEqual(max(ART["ballsfaced"]), 73)


class TestTeamStream(unittest.TestCase):
    def test_full_stream_matches_independent_recount(self):
        self.assertEqual(len(ART["team"]), EXPECTED_N_POINTS)
        self.assertEqual(bytes(ART["team"]), bytes(REF["team_ids"]))

    def test_teams_json_contract(self):
        teams = ART["teams"]
        self.assertEqual(len(teams), 20)
        self.assertEqual([t["id"] for t in teams], list(range(20)))
        self.assertEqual(len({t["short"] for t in teams}), 20, "shorts must be unique")
        inactive = {t["name"] for t in teams if not t["active"]}
        self.assertEqual(
            inactive,
            {"Deccan Chargers", "Gujarat Lions", "Kochi Tuskers Kerala",
             "Pune Warriors", "Rising Pune Supergiant"},
        )
        for t in teams:
            self.assertIn(t["league"], ("ipl", "wpl"))
            self.assertRegex(t["color"], r"^#[0-9A-F]{6}$")
        by_league = Counter(t["league"] for t in teams)
        self.assertEqual(by_league, Counter({"ipl": 15, "wpl": 5}))
        # Every picker franchise exists and is active.
        active = {(t["league"], t["name"]) for t in teams if t["active"]}
        for name in canon.CURRENT_IPL_FRANCHISES:
            self.assertIn(("ipl", name), active)
        for name in canon.WPL_FRANCHISES:
            self.assertIn(("wpl", name), active)

    def test_renamed_franchise_delhi_daredevils(self):
        """2008 Delhi Daredevils deliveries carry the Delhi Capitals id."""
        with open(canon.DATA_ROOT / "ipl_json" / DD_MATCH) as fh:
            match = json.load(fh)
        self.assertIn("Delhi Daredevils", match["info"]["teams"])
        inn1_balls = sum(len(o["deliveries"]) for o in match["innings"][0]["overs"])
        start, end = REF["match_slices"][DD_MATCH]
        rr_id = REF["tid"][("ipl", "Rajasthan Royals")]
        dc_id = REF["tid"][("ipl", "Delhi Capitals")]
        self.assertEqual(set(ART["team"][start : start + inn1_balls]), {rr_id})
        self.assertEqual(set(ART["team"][start + inn1_balls : end]), {dc_id})

    def test_wpl_franchises_have_their_own_ids(self):
        tid = REF["tid"]
        for name in ("Delhi Capitals", "Mumbai Indians", "Royal Challengers Bengaluru"):
            self.assertNotEqual(tid[("ipl", name)], tid[("wpl", name)], name)
        with open(canon.DATA_ROOT / "wpl_json" / WPL_OPENER) as fh:
            match = json.load(fh)
        self.assertEqual(match["innings"][0]["team"], "Mumbai Indians")
        start, _end = REF["match_slices"][WPL_OPENER]
        inn1_balls = sum(len(o["deliveries"]) for o in match["innings"][0]["overs"])
        self.assertEqual(
            set(ART["team"][start : start + inn1_balls]),
            {tid[("wpl", "Mumbai Indians")]},
        )


class TestColdOpenScene(unittest.TestCase):
    def test_corpus_facts(self):
        c = ART["coldopen"]["corpus"]
        self.assertEqual(c["points_rendered"], EXPECTED_N_POINTS)
        self.assertEqual(c["corpus_total"], 316_388)
        self.assertEqual(c["superover_balls"], 189)
        self.assertEqual(c["matches"], 1331)
        self.assertEqual(c["players"], EXPECTED_PLAYERS)
        self.assertEqual(c["ipl_seasons"], 19)
        self.assertEqual(c["wpl_seasons"], 4)
        self.assertEqual(len(REF["players"]), EXPECTED_PLAYERS)
        self.assertEqual(REF["n_matches"], 1331)

    def test_meta_v2_counts_match_artifacts(self):
        """meta.json v2 (storyboard CO-3): title-card counts trace to the
        artifact — n_players and per-league n_matches must equal the coldopen
        corpus block and the independent recount (card == artifact)."""
        meta = ART["meta"]
        c = ART["coldopen"]["corpus"]
        self.assertEqual(meta["n_points"], c["points_rendered"])
        self.assertEqual(meta["n_players"], c["players"])
        self.assertEqual(meta["n_players"], EXPECTED_PLAYERS)
        self.assertEqual(
            meta["n_matches"]["ipl"] + meta["n_matches"]["wpl"], c["matches"]
        )
        rows = ART["coldopen"]["seasons"]
        for league in ("ipl", "wpl"):
            self.assertEqual(
                meta["n_matches"][league],
                sum(r["matches"] for r in rows if r["league"] == league),
            )

    def rows(self, league):
        return [r for r in ART["coldopen"]["seasons"] if r["league"] == league]

    def test_ipl_series_match_data_profile(self):
        rows = self.rows("ipl")
        self.assertEqual([r["season"] for r in rows], list(range(2008, 2027)))
        self.assertEqual([r["matches"] for r in rows], IPL_MATCHES)
        self.assertEqual([r["totals200"] for r in rows], IPL_TOTALS200)
        self.assertEqual([r["avg_first_innings_full"] for r in rows], IPL_AVG_FIRST_FULL)
        self.assertEqual(rows[-1]["totals200"], 65)  # the You-Draw-It reveal

    def test_wpl_series_match_data_profile(self):
        rows = self.rows("wpl")
        self.assertEqual([r["season"] for r in rows], list(range(2023, 2027)))
        self.assertEqual([r["matches"] for r in rows], WPL_MATCHES)
        self.assertEqual([r["totals200"] for r in rows], WPL_TOTALS200)
        self.assertEqual([r["avg_first_innings_full"] for r in rows], WPL_AVG_FIRST_FULL)

    def test_deliveries_agree_with_groups_and_recount(self):
        rows = ART["coldopen"]["seasons"]
        self.assertEqual(sum(r["deliveries"] for r in rows), EXPECTED_N_POINTS)
        by_key = {(g["league"], g["season"]): g["count"] for g in ART["groups"]}
        for r in rows:
            key = (r["league"], r["season"])
            self.assertEqual(r["deliveries"], by_key[key], key)
            self.assertEqual(r["deliveries"], REF["seasons"][key].deliveries, key)
            self.assertEqual(r["matches"], REF["seasons"][key].matches, key)
            self.assertEqual(r["totals200"], REF["seasons"][key].totals200, key)


class TestCh1Ignition(unittest.TestCase):
    def test_per_index_curves_match_recount(self):
        for key, bd in REF["bands"].items():
            art_sr = band_art("ignition", "sr_by_ball_index")[key]
            art_balls = band_art("ignition", "balls_by_ball_index")[key]
            self.assertEqual(len(art_sr), 30, key)
            self.assertEqual(art_balls, bd.balls[1:], key)
            expected = [
                round(100.0 * bd.runs[n] / bd.balls[n], 1) if bd.balls[n] else None
                for n in range(1, 31)
            ]
            self.assertEqual(art_sr, expected, key)

    def test_first10_sr_by_season_matches_recount(self):
        art = band_art("ignition", "first10_sr_by_season")
        for (league, season), ss in REF["seasons"].items():
            self.assertEqual(
                art[league][str(season)],
                round(100.0 * ss.f10[1] / ss.f10[0], 1),
                (league, season),
            )

    def test_teaser_reconciliation(self):
        def band_f10_sr(key):
            bd = REF["bands"][key]
            runs = sum(bd.runs[1:11])
            balls = sum(bd.balls[1:11])
            return round(100.0 * runs / balls, 1)

        self.assertEqual(band_f10_sr("ipl 2008-2010"), TEASER_F10_SR_IPL_EARLY)
        self.assertEqual(band_f10_sr("ipl 2023-2026"), TEASER_F10_SR_IPL_RECENT)
        self.assertEqual(band_f10_sr("wpl 2023-2026"), TEASER_F10_SR_WPL)
        beat = ART["ch1"]["wpl_beat"]["first10_sr"]
        self.assertEqual(beat["ipl_2008_2010"], TEASER_F10_SR_IPL_EARLY)
        self.assertEqual(beat["wpl_2023_2026"], TEASER_F10_SR_WPL)


class TestCh1OutRate(unittest.TestCase):
    def test_curves_match_recount(self):
        for key, bd in REF["bands"].items():
            self.assertEqual(
                band_art("outrate", "reaching_by_ball_index")[key], bd.reaching[1:], key
            )
            self.assertEqual(
                band_art("outrate", "dismissed_at_ball_index")[key], bd.out_at[1:], key
            )
            expected = [
                round(100.0 * bd.out_at[n] / bd.reaching[n], 2) if bd.reaching[n] else None
                for n in range(1, 31)
            ]
            self.assertEqual(
                band_art("outrate", "hazard_pct_by_ball_index")[key], expected, key
            )
            samples = band_art("outrate", "sample_sizes")[key]
            self.assertEqual(samples["batter_innings"], bd.innings, key)
            self.assertEqual(samples["balls_1_10"], bd.f10_balls, key)

    def test_first10_hazard_teasers(self):
        f10 = ART["ch1"]["outrate"]["first10"]
        self.assertEqual(f10["ipl 2008-2010"]["hazard_pct"], TEASER_F10_HAZARD_EARLY)
        self.assertEqual(f10["ipl 2023-2026"]["hazard_pct"], TEASER_F10_HAZARD_RECENT)
        for key, bd in REF["bands"].items():
            self.assertEqual(
                f10[key]["hazard_pct"],
                round(100.0 * bd.f10_events / bd.f10_balls, 2),
                key,
            )
            self.assertEqual(f10[key]["events"], bd.f10_events, key)

    def test_survival_shape(self):
        for key, bd in REF["bands"].items():
            reaching = band_art("outrate", "reaching_by_ball_index")[key]
            self.assertTrue(
                all(a >= b for a, b in zip(reaching, reaching[1:])),
                f"{key}: reaching must be non-increasing",
            )
            self.assertLessEqual(reaching[0], bd.innings, key)


class TestCh1Defiers(unittest.TestCase):
    def test_structure(self):
        defiers = ART["ch1"]["defiers"]["bands"]
        self.assertEqual(set(defiers), set(REF["bands"]))
        for key, block in defiers.items():
            self.assertEqual(set(block["by_ball_index"]), {"5", "10", "15", "20"}, key)
            for idx, rows in block["by_ball_index"].items():
                self.assertEqual(len(rows), 5, (key, idx))
                scores = [r["score"] for r in rows]
                self.assertEqual(scores, sorted(scores, reverse=True), (key, idx))
                for r in rows:
                    self.assertGreaterEqual(r["balls_in_band"], 300, (key, idx))
                    self.assertTrue(r["name"].strip(), (key, idx))

    def test_ipl_recent_ball10_cell_against_independent_recount(self):
        stats = defier_recount_ipl_recent()
        base_innings = sum(v[0] for v in stats.values())
        base_reach = sum(v[2] for v in stats.values())
        base_runs = sum(v[3] for v in stats.values())
        base_balls = sum(v[4] for v in stats.values())
        base_surv = base_reach / base_innings
        base_sr = 100.0 * base_runs / base_balls

        def score(rec):
            surv = rec[2] / rec[0]
            sr = 100.0 * rec[3] / rec[4]
            return surv / base_surv + sr / base_sr - 2.0

        qualified = {n: rec for n, rec in stats.items() if rec[1] >= 300 and rec[4]}
        expected_top5 = sorted(
            qualified, key=lambda n: (-score(qualified[n]), n)
        )[:5]
        art_rows = ART["ch1"]["defiers"]["bands"]["ipl 2023-2026"]["by_ball_index"]["10"]
        self.assertEqual([r["name"] for r in art_rows], expected_top5)
        for r in art_rows:
            rec = qualified[r["name"]]
            self.assertEqual(r["score"], round(score(rec), 3), r["name"])
            self.assertEqual(r["survival_pct"], round(100.0 * rec[2] / rec[0], 1))
            self.assertEqual(r["sr_through_ball"], round(100.0 * rec[3] / rec[4], 1))


class TestCh1SixesAerialWpl(unittest.TestCase):
    def test_six_rows_match_recount_and_teasers(self):
        art = ART["ch1"]["sixes"]["seasons"]
        for league in ("ipl", "wpl"):
            for row in art[league]:
                ss = REF["seasons"][(league, row["season"])]
                self.assertEqual(row["sixes"], sum(ss.sixes.values()), row)
                self.assertEqual(
                    row["players_10plus_sixes"],
                    sum(1 for v in ss.sixes.values() if v >= 10),
                    row,
                )
                qual = {b for b, n in ss.balls_faced.items() if n >= 30}
                qual_sixes = sum(v for b, v in ss.sixes.items() if b in qual)
                top10 = sum(
                    v for _b, v in Counter(
                        {b: v for b, v in ss.sixes.items() if b in qual}
                    ).most_common(10)
                )
                expected = round(100.0 * top10 / qual_sixes, 1) if qual_sixes else None
                self.assertEqual(row["top10_share_pct"], expected, row)
        by_season = {r["season"]: r for r in art["ipl"]}
        for season, teaser in ((2008, TEASER_SIXES_2008), (2026, TEASER_SIXES_2026)):
            for field, value in teaser.items():
                self.assertEqual(by_season[season][field], value, (season, field))

    def test_aerial_matches_recount_and_teasers(self):
        art = ART["ch1"]["aerial"]["bands"]
        for key, bd in REF["bands"].items():
            balls, sixes, caught = bd.aerial
            attempts = sixes + caught
            self.assertEqual(art[key]["attempts_per_100_balls"],
                             round(100.0 * attempts / balls, 1), key)
            self.assertEqual(art[key]["execution_pct"],
                             round(100.0 * sixes / attempts, 1), key)
        self.assertEqual(
            (art["ipl 2008-2010"]["attempts_per_100_balls"],
             art["ipl 2008-2010"]["execution_pct"]),
            TEASER_AERIAL_EARLY,
        )
        self.assertEqual(
            (art["ipl 2023-2026"]["attempts_per_100_balls"],
             art["ipl 2023-2026"]["execution_pct"]),
            TEASER_AERIAL_RECENT,
        )
        self.assertTrue(ART["ch1"]["aerial"]["caveat"].strip())

    def test_wpl_beat_run_dna_and_maturity_clock(self):
        beat = ART["ch1"]["wpl_beat"]
        self.assertEqual(beat["runs_from_fours_pct"]["wpl_2023_2026"], TEASER_FOURS_PCT["wpl"])
        self.assertEqual(beat["runs_from_fours_pct"]["ipl_2023_2026"], TEASER_FOURS_PCT["ipl_recent"])
        self.assertEqual(beat["runs_from_sixes_pct"]["wpl_2023_2026"], TEASER_SIXSHARE_PCT["wpl"])
        self.assertEqual(beat["runs_from_sixes_pct"]["ipl_2023_2026"], TEASER_SIXSHARE_PCT["ipl_recent"])
        clock = beat["maturity_clock"]
        self.assertEqual(clock["rr"]["ipl"], TEASER_RR_Y1_4["ipl"])
        self.assertEqual(clock["rr"]["wpl"], TEASER_RR_Y1_4["wpl"])
        # Independent recount of the RR series (all runs / legal balls).
        for league, first in (("ipl", 2008), ("wpl", 2023)):
            for i in range(4):
                ss = REF["seasons"][(league, first + i)]
                self.assertEqual(
                    clock["rr"][league][i], round(6.0 * ss.runs[0] / ss.runs[3], 2)
                )
                self.assertEqual(
                    clock["first10_sr"][league][i],
                    round(100.0 * ss.f10[1] / ss.f10[0], 1),
                )
        # The Ch 1 WPL card claim: year-4 ignition above the IPL's year-4.
        self.assertGreater(clock["first10_sr"]["wpl"][3], clock["first10_sr"]["ipl"][3])


class TestPayoffCh1FullSpec(unittest.TestCase):
    def test_harness_assertions_hold_on_disk(self):
        self.assertEqual(payoff_harness.assert_non_degenerate(ART["payoff"]), [])

    def test_neutral_reproduces_the_thesis(self):
        neutral = [v for v in ART["payoff"]["variants"] if v["team"] == "Neutral"][0]
        self.assertEqual(neutral["first10_sr_early_era"], TEASER_F10_SR_IPL_EARLY)
        self.assertEqual(neutral["first10_sr_recent_era"], TEASER_F10_SR_IPL_RECENT)

    def test_ignition_by_era_band_labels(self):
        ipl_labels = ["2008-2010", "2011-2015", "2016-2019", "2020-2022", "2023-2026"]
        wpl_labels = ["2023-2024", "2025-2026"]
        for v in ART["payoff"]["variants"]:
            labels = [r["era"] for r in v["ignition_by_era"]]
            self.assertEqual(labels, ipl_labels if v["league"] == "ipl" else wpl_labels, v["team"])

    def test_fastest_starter_floor(self):
        for v in ART["payoff"]["variants"]:
            fs = v["fastest_starter"]
            self.assertGreaterEqual(fs["first10_balls"], 100, v["team"])
            self.assertGreater(fs["first10_sr"], 0, v["team"])

    def test_wpl_cards_carry_the_maturity_clock(self):
        wpl = [v for v in ART["payoff"]["variants"] if v["league"] == "wpl"]
        self.assertEqual(len(wpl), 5)
        for v in wpl:
            clock = v["maturity_clock"]
            self.assertEqual(clock["rr_by_year"]["ipl"], TEASER_RR_Y1_4["ipl"])
            self.assertEqual(clock["rr_by_year"]["wpl"], TEASER_RR_Y1_4["wpl"])
            self.assertNotIn("behind", clock["copy"].lower())

    def test_born_late_franchises_have_designed_sparsity(self):
        for team in ("Gujarat Titans", "Lucknow Super Giants", "Sunrisers Hyderabad"):
            v = [x for x in ART["payoff"]["variants"]
                 if x["team"] == team and x["league"] == "ipl"][0]
            self.assertTrue(v["empty_state"], team)
            first_band = v["ignition_by_era"][0]
            self.assertEqual(first_band["era"], "2008-2010")
            self.assertEqual(first_band["balls_1_10"], 0, team)
            self.assertIsNone(first_band["sr_1_10"], team)


if __name__ == "__main__":
    unittest.main()
