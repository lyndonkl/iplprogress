"""Snapshot + honesty + cross-artifact reconciliation tests for R7b, the
credibility layer.

This file is shared across the R7b build agents; each stat lands in its own class
so the classes never collide. TestTrueEcon (this contribution) pins the bowling
TrueEcon river emitted into engines/trueecon.json by pipeline/bowlerplane.py.

TrueEcon is the era-fair bowling economy the R7a bowler card plots: par economy
(the league-season economy for the exact phase mix a bowler bowled) minus the
bowler's actual economy, with trueecon_plus = 100 x par / actual on the SR+ river's
100 baseline (above 100 = leaked fewer runs than era par). It is engine #1's par
family flipped from batting to bowling, so it must never drift from the numbers the
Chapter 3 gravity-defier cards already ship: the reconciliation below re-derives the
river independently and asserts it reproduces scenes/ch3.json's gravity_defiers
exactly (L Ngidi's IPL 2018 6.0 / 8.92 / 2.92 among them).

Recounted on the real corpus 2026-07-09; constants are dated so a corpus drop that
moves them fails loudly rather than drifting.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bowlerplane
import canon
import credibility
import flatten
import h2h

# Corpus-wide snapshot constants (recounted 2026-07-09).
TRUEECON_ROW_COUNT = 1255          # bowler_seasons rows, all >= 90 legal balls
MIN_LEGAL_BALLS = 90               # the qualifier floor (== bowlerplane.MIN_LEGAL_BALLS)

# L Ngidi IPL 2018 — the free cross-artifact reconciliation against Chapter 3's
# Chennai gravity-defier card (scenes/ch3.json). A genuine outlier season.
NGIDI_PID = "f834dcfc"
NGIDI_2018 = {
    "league": "ipl", "season": 2018, "pid": NGIDI_PID, "bowler": "L Ngidi",
    "legal_balls": 156, "economy": 6.0, "par_economy": 8.92, "true_economy": 2.92,
    "trueecon_plus": 148.68, "wickets": 11, "strike_rate": 14.18,
}

# JJ Bumrah IPL 2024 — the famous-bowler sample: his best trueecon_plus season and
# the Mumbai gravity-defier card. Biggest edge over his era.
BUMRAH_PID = "462411b3"
BUMRAH_2024 = {
    "league": "ipl", "season": 2024, "pid": BUMRAH_PID, "bowler": "JJ Bumrah",
    "legal_balls": 311, "economy": 6.48, "par_economy": 9.7, "true_economy": 3.22,
    "trueecon_plus": 149.64, "wickets": 20, "strike_rate": 15.55,
}

ROW_KEYS = {
    "league", "season", "pid", "bowler", "legal_balls", "economy",
    "par_economy", "true_economy", "trueecon_plus", "wickets", "strike_rate",
}


# ---------------------------------------------------------------------------
# Shared single-build fixtures (parse the corpus as few times as possible)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bp_data():
    """One bowlerplane corpus pass, shared by every TrueEcon test."""
    return bowlerplane.build()


@pytest.fixture(scope="module")
def registry():
    """(name_to_pids, by_pid) off the shipped players.json the emitter joins on."""
    return bowlerplane._load_registry(canon.OUT_ROOT)


@pytest.fixture(scope="module")
def doc(bp_data, registry):
    """The TrueEcon river rebuilt from the aggregates (independent of the shipped
    file), so the reconciliation is a genuine recount, not a re-read."""
    name_to_pids, by_pid = registry
    return bowlerplane.build_trueecon(
        bp_data["bowler_seasons"], bp_data["phase_eco"], name_to_pids, by_pid
    )


@pytest.fixture(scope="module")
def by_key(doc):
    return {(r["league"], r["season"], r["pid"]): r for r in doc["bowler_seasons"]}


@pytest.fixture(scope="module")
def shipped_players():
    return json.loads((canon.OUT_ROOT / "players.json").read_text())


class TestTrueEcon:
    # -----------------------------------------------------------------------
    # Shape, count, sort order
    # -----------------------------------------------------------------------

    def test_doc_shape_and_count(self, doc):
        assert set(doc) == {"engine", "definition", "min_legal_balls", "count",
                            "bowler_seasons"}
        assert doc["min_legal_balls"] == MIN_LEGAL_BALLS == bowlerplane.MIN_LEGAL_BALLS
        assert doc["count"] == TRUEECON_ROW_COUNT
        assert len(doc["bowler_seasons"]) == TRUEECON_ROW_COUNT

    def test_no_em_dash_in_prose(self, doc):
        # binding voice rule: zero em dashes anywhere in the shipped artifact
        assert "—" not in doc["engine"]
        assert "—" not in doc["definition"]

    def test_rows_sorted_deterministically(self, doc):
        rows = doc["bowler_seasons"]
        keys = [(r["league"], r["season"], r["pid"]) for r in rows]
        assert keys == sorted(keys)
        assert len(keys) == len(set(keys))          # (league, season, pid) is unique

    def test_every_row_well_formed(self, doc):
        for r in doc["bowler_seasons"]:
            assert set(r) == ROW_KEYS
            assert r["league"] in ("ipl", "wpl")
            assert isinstance(r["season"], int)
            assert isinstance(r["pid"], str) and r["pid"]
            assert isinstance(r["bowler"], str) and r["bowler"]
            assert r["legal_balls"] >= MIN_LEGAL_BALLS      # the qualifier floor holds
            assert r["economy"] > 0 and r["par_economy"] > 0
            assert isinstance(r["trueecon_plus"], float)
            assert r["wickets"] >= 0
            # strike rate is null exactly when the bowler-season took no wicket
            assert (r["strike_rate"] is None) == (r["wickets"] == 0)
            if r["strike_rate"] is not None:
                assert r["strike_rate"] > 0

    # -----------------------------------------------------------------------
    # PID-keying: one real person per row, canonical name, no namesake merge
    # -----------------------------------------------------------------------

    def test_rows_are_pid_keyed_to_real_players(self, doc, shipped_players):
        by_pid = {p["pid"]: p for p in shipped_players["players"]}
        for r in doc["bowler_seasons"]:
            p = by_pid.get(r["pid"])
            assert p is not None                            # a real registry pid
            assert r["bowler"] == p["name"]                 # the canonical spelling
            assert r["league"] in p["leagues"]              # league family agrees
            assert r["season"] in p["seasons"]              # played that season
            assert p["balls_bowled"] > 0                    # actually a bowler

    def test_wpl_rows_priced_against_wpl(self, doc):
        # WPL bowler-seasons exist and are priced within their own league (par is a
        # league-season quantity), so the river is honest across both leagues.
        wpl = [r for r in doc["bowler_seasons"] if r["league"] == "wpl"]
        assert wpl, "expected WPL bowler-seasons in the river"
        assert all(r["par_economy"] > 0 for r in wpl)

    # -----------------------------------------------------------------------
    # trueecon_plus is the 100-baseline field the card plots (9.4)
    # -----------------------------------------------------------------------

    def test_trueecon_plus_baseline_semantics(self, doc):
        """Above 100 == better than era par == positive runs saved. Checked with a
        small guard band so the exact-par boundary (where rounding can split the two
        fields) is excluded rather than mis-asserted."""
        for r in doc["bowler_seasons"]:
            if r["true_economy"] >= 0.05:
                assert r["trueecon_plus"] > 100.0
            elif r["true_economy"] <= -0.05:
                assert r["trueecon_plus"] < 100.0

    def test_true_economy_is_par_minus_actual(self, doc):
        # true_economy == par - actual. Each of the three fields is independently
        # rounded to 2 dp, so the identity can drift by up to ~0.01 (two half-cent
        # roundings) plus float noise; 0.02 catches a real sign/formula error while
        # tolerating the published-precision slack.
        for r in doc["bowler_seasons"]:
            assert abs(r["true_economy"] - (r["par_economy"] - r["economy"])) < 0.02

    # -----------------------------------------------------------------------
    # The named spot-checks
    # -----------------------------------------------------------------------

    def test_ngidi_2018_row(self, by_key):
        assert by_key[(NGIDI_2018["league"], NGIDI_2018["season"], NGIDI_PID)] == NGIDI_2018

    def test_bumrah_best_season(self, doc, by_key):
        assert by_key[(BUMRAH_2024["league"], BUMRAH_2024["season"], BUMRAH_PID)] == BUMRAH_2024
        # it is his single best edge over par in the river
        bum = [r for r in doc["bowler_seasons"] if r["pid"] == BUMRAH_PID]
        assert len(bum) >= 1
        best = max(bum, key=lambda r: r["trueecon_plus"])
        assert (best["season"], best["trueecon_plus"]) == (2024, 149.64)

    # -----------------------------------------------------------------------
    # FREE cross-artifact reconciliation vs scenes/ch3.json gravity_defiers
    # -----------------------------------------------------------------------

    def test_reconciles_ch3_gravity_defiers(self, by_key, registry):
        """Every Chapter 3 gravity-defier card (the franchise-best TrueEcon season,
        computed independently in scenes.py off the SAME bowlerplane aggregates) must
        reappear in the river with byte-for-byte identical economy / par / true
        economy / wickets / legal balls. This is the deferred R7a bowling number
        proving it never drifted from what the site already shows."""
        name_to_pids, by_pid = registry
        ch3 = json.loads((canon.OUT_ROOT / "scenes" / "ch3.json").read_text())
        variants = ch3["gravity_defiers"]["variants"]
        assert variants, "expected gravity-defier variants in scenes/ch3.json"
        for v in variants:
            pid = bowlerplane._resolve_pid(
                v["bowler"], v["league"], v["season"], name_to_pids, by_pid
            )
            r = by_key.get((v["league"], v["season"], pid))
            assert r is not None, f"no river row for defier {v['bowler']} {v['season']}"
            assert r["economy"] == v["economy"]
            assert r["par_economy"] == v["par_economy"]
            assert r["true_economy"] == v["true_economy"]
            assert r["wickets"] == v["wickets"]
            assert r["legal_balls"] == v["balls"]

    def test_ngidi_reconciles_exactly(self, by_key, registry):
        """The pinned free test: L Ngidi's IPL 2018 card reads 6.0 / 8.92 / 2.92 in
        Chapter 3, and the river must match that exact triple."""
        name_to_pids, by_pid = registry
        ch3 = json.loads((canon.OUT_ROOT / "scenes" / "ch3.json").read_text())
        ngidi = next(
            v for v in ch3["gravity_defiers"]["variants"]
            if v["bowler"] == "L Ngidi" and v["season"] == 2018 and v["league"] == "ipl"
        )
        assert (ngidi["economy"], ngidi["par_economy"], ngidi["true_economy"]) == (6.0, 8.92, 2.92)
        r = by_key[("ipl", 2018, NGIDI_PID)]
        assert (r["economy"], r["par_economy"], r["true_economy"]) == (6.0, 8.92, 2.92)

    # -----------------------------------------------------------------------
    # Byte determinism + matches the shipped artifact
    # -----------------------------------------------------------------------

    def test_byte_deterministic_and_matches_shipped(self, bp_data, registry):
        name_to_pids, by_pid = registry
        a = flatten.compact_json(
            bowlerplane.build_trueecon(
                bp_data["bowler_seasons"], bp_data["phase_eco"], name_to_pids, by_pid),
            sort_keys=True)
        b = flatten.compact_json(
            bowlerplane.build_trueecon(
                bp_data["bowler_seasons"], bp_data["phase_eco"], name_to_pids, by_pid),
            sort_keys=True)
        assert a == b                                       # two builds, identical bytes
        shipped = (canon.OUT_ROOT / "engines" / "trueecon.json").read_bytes()
        assert hashlib.sha256(a).hexdigest() == hashlib.sha256(shipped).hexdigest()

    # -----------------------------------------------------------------------
    # Mutation guard — the 90-legal-ball floor is load-bearing
    # -----------------------------------------------------------------------

    def test_mutation_dropping_the_ball_floor_admits_noise(self, bp_data, registry, monkeypatch):
        """With the qualifier lowered to 1 legal ball, the river admits thin
        bowler-seasons the real 90-ball floor keeps out. The shipped floor has ZERO
        rows under 90; the mutation has some, proving the floor is not vacuous."""
        name_to_pids, by_pid = registry
        honest = bowlerplane.build_trueecon(
            bp_data["bowler_seasons"], bp_data["phase_eco"], name_to_pids, by_pid)
        assert min(r["legal_balls"] for r in honest["bowler_seasons"]) >= MIN_LEGAL_BALLS

        monkeypatch.setattr(bowlerplane, "MIN_LEGAL_BALLS", 1)
        mutated = bowlerplane.build_trueecon(
            bp_data["bowler_seasons"], bp_data["phase_eco"], name_to_pids, by_pid)
        assert min(r["legal_balls"] for r in mutated["bowler_seasons"]) < MIN_LEGAL_BALLS
        assert mutated["count"] > honest["count"]           # the guard is not vacuous


# ===========================================================================
# Phase 1a — the credibility statistical core (pipeline/credibility.py)
#
#   stabilization   engines/stabilization.json: per-stat stabilization point M =
#                   sigma2_within / tau2_between (DerSimonian-Laird), per phase / era
#   half_life       engines/half_life.json: per-metric free-r0 persistence half-life
#   truetalent      engines/truetalent.json: the pid-keyed EB-regressed SR+ pool
#
# Recounted on the real corpus 2026-07-09; every constant is dated so a corpus drop
# that moves it fails loudly rather than drifting. Where a recount differs from a
# catalog teaser the ARTIFACT wins and the number below is the artifact's.
# ===========================================================================

# --- stabilization snapshots (recounted 2026-07-09) ---
STAB_BATTING_SR = {"M": 94.5, "sigma2": 2.79731, "tau2": 0.0296,
                   "n_groups": 1117, "mean": 1.37053, "stabilizes": True}
STAB_BOUNDARY = {"M": 93.51, "sigma2": 0.14579, "tau2": 0.001559,
                 "n_groups": 1117, "mean": 0.18502, "stabilizes": True}
STAB_DOT_M = 86.58
STAB_ECON = {"M": 104.33, "sigma2": 2.79484, "tau2": 0.026787,
             "n_groups": 1169, "mean": 1.35153, "stabilizes": True}
STAB_BOWLDOT_M = 75.11
# The two BINDING targets (verified independently); the recount must land here.
BATTING_SR_M_TARGET = 94.5          # tol +/- 2
BOUNDARY_M_TARGET = 93.0            # tol +/- 8

# --- half-life snapshots (recounted 2026-07-09; FREE-r0 fit, pre-shrunk) ---
HL_SRPLUS = {
    "r0": 0.3701, "half_life_seasons": 5.294, "fit_gaps": [1, 2, 3, 4, 5],
    "autocorr": {"1": 0.3378, "2": 0.2617, "3": 0.2614, "4": 0.2202, "5": 0.1913,
                 "6": 0.153, "7": 0.1321, "8": 0.1301},
    "n_pairs": {"1": 726, "2": 601, "3": 503, "4": 411, "5": 333,
                "6": 275, "7": 228, "8": 186},
}
HL_BOUNDARY_H = 3.322
HL_ECON_H = 5.679
SRPLUS_H_TARGET = 5.3               # the free-r0 fit (a naive r0=1 fit gives ~2, WRONG)

# --- true-talent snapshots (recounted 2026-07-09) ---
TT_POOL_COUNT = 196
TT_SIGMA2 = 15761.48
TT_M = 94.5
TT_Z = 1.2816
KOHLI_TT = {"pid": "ba607b88", "name": "V Kohli", "league": "ipl", "n": 6926,
            "raw": 100.87, "regressed": 100.86, "ci_lo": 98.94, "ci_hi": 102.78}
ABD_TT = {"pid": "c4487b84", "name": "AB de Villiers", "league": "ipl", "n": 3305,
          "raw": 115.27, "regressed": 114.85, "ci_lo": 112.09, "ci_hi": 117.61}


@pytest.fixture(scope="module")
def cred_docs():
    """All three credibility docs from one corpus pass, shared by every test."""
    return credibility.build_docs()


@pytest.fixture(scope="module")
def stab(cred_docs):
    return cred_docs["stabilization"]


@pytest.fixture(scope="module")
def half(cred_docs):
    return cred_docs["half_life"]


@pytest.fixture(scope="module")
def true(cred_docs):
    return cred_docs["truetalent"]


class TestStabilization:
    def test_batting_sr_matches_verified_and_snapshot(self, stab):
        o = stab["stats"]["batting_sr"]["overall"]
        # BINDING: the recount reproduces the independently verified 94.5.
        assert o["M"] == pytest.approx(BATTING_SR_M_TARGET, abs=2.0)
        assert {k: o[k] for k in STAB_BATTING_SR} == STAB_BATTING_SR

    def test_boundary_matches_verified_and_snapshot(self, stab):
        o = stab["stats"]["boundary_pct"]["overall"]
        # BINDING: boundary-hitting settles at about 93 balls.
        assert o["M"] == pytest.approx(BOUNDARY_M_TARGET, abs=8.0)
        assert {k: o[k] for k in STAB_BOUNDARY} == STAB_BOUNDARY

    def test_other_stat_M_snapshots(self, stab):
        s = stab["stats"]
        assert s["dot_pct"]["overall"]["M"] == STAB_DOT_M
        assert {k: s["bowling_economy"]["overall"][k] for k in STAB_ECON} == STAB_ECON
        assert s["bowling_dot_pct"]["overall"]["M"] == STAB_BOWLDOT_M

    def test_dismissal_pct_does_not_stabilize(self, stab):
        """Fallacy guard made honest: batter dismissal% is so rare that the between-
        season spread never clears the sampling-noise floor, so tau2 clamps to 0 and
        M is null. A rare event must NOT read as 'more trustworthy' for its small
        raw count; here it reads 'never settled', which is the truth."""
        o = stab["stats"]["dismissal_pct"]["overall"]
        assert o["stabilizes"] is False
        assert o["M"] is None
        assert o["tau2"] == 0.0

    def test_sigma2_reuses_the_h2h_eb_constant(self, stab):
        """The generalization is faithful: the batting_sr within-variance is exactly
        the engine #6 empirical-Bayes sigma2 (ball-level runs variance), the anchor
        the DerSimonian-Laird estimator was generalized from."""
        eb = h2h.eb_constants()
        assert stab["stats"]["batting_sr"]["overall"]["sigma2"] == pytest.approx(
            eb.sigma2, abs=1e-4)

    def test_stratified_by_phase_and_era_present(self, stab):
        for name in ("batting_sr", "boundary_pct", "bowling_economy"):
            block = stab["stats"][name]
            assert set(block["by_phase"]) == {"pp", "middle", "death"}
            assert set(block["by_era"]) == {
                "ipl 2008-2010", "ipl 2011-2015", "ipl 2016-2019",
                "ipl 2020-2022", "ipl 2023-2026", "wpl 2023-2026"}
            for sub in list(block["by_phase"].values()) + list(block["by_era"].values()):
                assert set(sub) >= {"M", "sigma2", "tau2", "n_groups", "stabilizes"}

    def test_M_is_never_driven_by_the_numerator(self, stab):
        """The stabilization point is a function of sample size vs true spread, not
        of how big the raw tally is: it must be POSITIVE (or null), never negative,
        for every stat / phase / era that stabilizes."""
        for block in stab["stats"].values():
            cells = [block["overall"]] + list(block["by_phase"].values()) \
                + list(block["by_era"].values())
            for c in cells:
                if c["stabilizes"]:
                    assert c["M"] is not None and c["M"] > 0
                else:
                    assert c["M"] is None

    def test_no_em_dash(self, stab):
        assert "—" not in stab["method"]
        for block in stab["stats"].values():
            assert "—" not in block["gloss"]

    def test_byte_deterministic_and_matches_shipped(self, stab):
        again = credibility.build_docs()["stabilization"]
        a = flatten.compact_json(stab, sort_keys=True)
        b = flatten.compact_json(again, sort_keys=True)
        assert a == b
        shipped = (canon.OUT_ROOT / "engines" / "stabilization.json").read_bytes()
        assert hashlib.sha256(a).hexdigest() == hashlib.sha256(shipped).hexdigest()


class TestHalfLife:
    def test_srplus_free_r0_fit_snapshot(self, half):
        m = half["metrics"]["srplus"]
        # BINDING: the FREE-r0 fit lands ~5.3 seasons, far from the naive ~2.
        assert m["half_life_seasons"] == pytest.approx(SRPLUS_H_TARGET, abs=0.7)
        assert m["half_life_seasons"] > 4.0            # decisively NOT the naive fit
        for k in ("r0", "half_life_seasons", "fit_gaps", "autocorr", "n_pairs"):
            assert m[k] == HL_SRPLUS[k]

    def test_fit_window_is_the_well_sampled_gaps(self, half):
        """A season gap enters the fit only with enough pairs to trust its r
        (>= 300); that rule, not a cherry-pick, selects the window."""
        for name, m in half["metrics"].items():
            for g in m["fit_gaps"]:
                assert m["n_pairs"][str(g)] >= credibility.HALFLIFE_MIN_FIT_PAIRS
                assert m["autocorr"][str(g)] > 0

    def test_boundary_and_economy_half_lives(self, half):
        assert half["metrics"]["boundary_pct"]["half_life_seasons"] == HL_BOUNDARY_H
        assert half["metrics"]["bowling_economy"]["half_life_seasons"] == HL_ECON_H

    def test_free_r0_beats_the_naive_forced_fit(self, half):
        """The teaching point made a test: forcing r0 = 1 (a fit through the origin,
        blind to sampling attenuation) gives a much SHORTER half-life than the honest
        free-r0 fit on the same autocorrelations. The recount ships the free one."""
        m = half["metrics"]["srplus"]
        gaps = m["fit_gaps"]
        ac = {int(g): m["autocorr"][g] for g in m["autocorr"]}
        import math
        slope = sum(g * math.log(ac[g]) for g in gaps) / sum(g * g for g in gaps)
        naive_H = -math.log(2) / slope
        assert naive_H < 3.0                            # naive collapses the half-life
        assert m["half_life_seasons"] > naive_H + 2.0   # free-r0 is materially longer

    def test_no_em_dash(self, half):
        assert "—" not in half["method"]
        for m in half["metrics"].values():
            assert "—" not in m["gloss"]

    def test_byte_deterministic_and_matches_shipped(self, half):
        again = credibility.build_docs()["half_life"]
        a = flatten.compact_json(half, sort_keys=True)
        b = flatten.compact_json(again, sort_keys=True)
        assert a == b
        shipped = (canon.OUT_ROOT / "engines" / "half_life.json").read_bytes()
        assert hashlib.sha256(a).hexdigest() == hashlib.sha256(shipped).hexdigest()


class TestTrueTalent:
    def test_block_params(self, true):
        assert true["stat"] == "batting_srplus"
        assert true["pop_mean"] == {"ipl": 100.0, "wpl": 100.0}
        assert true["M"] == TT_M
        assert true["sigma2"] == TT_SIGMA2
        assert true["z"] == TT_Z
        assert true["min_balls"] == 200
        assert true["count"] == TT_POOL_COUNT
        assert len(true["players"]) == TT_POOL_COUNT

    def test_kohli_and_abd_rows(self, true):
        """BINDING: the two verified spot-checks. Kohli barely moves off a huge
        sample; ABD moves a touch more off a smaller one; both keep their CI."""
        by_pid = {r["pid"]: r for r in true["players"]}
        assert by_pid[KOHLI_TT["pid"]] == KOHLI_TT
        assert by_pid[ABD_TT["pid"]] == ABD_TT

    def test_regression_and_ci_formula(self, true):
        import math
        M, s2, z = true["M"], true["sigma2"], true["z"]
        for r in true["players"]:
            mu = true["pop_mean"][r["league"]]
            reg = mu + (r["raw"] - mu) * r["n"] / (r["n"] + M)
            se = math.sqrt(s2 / (r["n"] + M))
            assert r["regressed"] == pytest.approx(reg, abs=0.01)
            assert r["ci_lo"] == pytest.approx(reg - z * se, abs=0.01)
            assert r["ci_hi"] == pytest.approx(reg + z * se, abs=0.01)
            assert r["ci_lo"] < r["regressed"] < r["ci_hi"]

    def test_shrinkage_pulls_small_samples_toward_100(self, true):
        """A thin sample collapses toward its league's 100 (the model leans on the
        average), while a huge sample holds: the regressed value sits strictly
        between the raw and 100, and the pull is fractional in n / (n + M)."""
        for r in true["players"]:
            pull = 1 - r["n"] / (r["n"] + true["M"])       # weight given to 100
            assert 0 < pull < 1
            # regressed is raw shrunk toward 100 by exactly that pull
            assert abs(r["regressed"] - 100.0) <= abs(r["raw"] - 100.0) + 1e-6
        # the leader off a thin sample must still out-rank a league-average grinder
        assert true["players"][0]["regressed"] > 100.0

    def test_pid_keyed_no_namesake_merge(self, true, shipped_players):
        by_pid = {p["pid"]: p for p in shipped_players["players"]}
        seen = set()
        for r in true["players"]:
            assert r["pid"] not in seen                     # one row per person
            seen.add(r["pid"])
            p = by_pid[r["pid"]]
            assert r["name"] == p["name"]                   # canonical spelling
            assert r["league"] == p["leagues"][0]           # single league family
            assert p["balls_faced"] >= credibility.TRUETALENT_MIN_BALLS

    def test_wpl_regresses_to_wpl_not_cross_league(self, true):
        wpl = [r for r in true["players"] if r["league"] == "wpl"]
        assert wpl, "expected WPL rows in the pool"
        # every WPL row regresses toward the WPL centre (100), never a blended mean
        assert true["pop_mean"]["wpl"] == 100.0

    def test_rows_sorted_by_regressed_desc(self, true):
        regs = [r["regressed"] for r in true["players"]]
        assert regs == sorted(regs, reverse=True)

    def test_shares_the_stabilization_point(self, true, stab):
        # the true-talent M IS the batting_sr stabilization point (one source)
        assert true["M"] == stab["stats"]["batting_sr"]["overall"]["M"]

    def test_no_em_dash(self, true):
        assert "—" not in true["method"]
        assert "—" not in true["pop_mean_note"]

    def test_byte_deterministic_and_matches_shipped(self, true):
        again = credibility.build_docs()["truetalent"]
        a = flatten.compact_json(true, sort_keys=True)
        b = flatten.compact_json(again, sort_keys=True)
        assert a == b
        shipped = (canon.OUT_ROOT / "engines" / "truetalent.json").read_bytes()
        assert hashlib.sha256(a).hexdigest() == hashlib.sha256(shipped).hexdigest()
