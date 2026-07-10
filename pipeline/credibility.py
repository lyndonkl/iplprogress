"""R7b, the credibility layer statistical core (Phase 1a).

Every rate stat on the site learns to wear its own uncertainty. ONE pid-resolved
corpus pass (mirroring registry.build) tallies per-(pid, league, season, phase)
trials + successes for six rate stats, and joins the already-emitted engine
tables (engines/srplus.json for the era-fair SR+ metric, players.json for the
name -> registry-pid map) to emit THREE tiny engine artifacts:

  engines/stabilization.json   the trust-meter table. Per rate stat, the
     stabilization point M = the balls a stat needs before it is half signal:
        reliability(n) = n / (n + M),  M = sigma2_within / tau2_between
     via the variance-components (DerSimonian-Laird) estimator GENERALIZED from
     h2h.eb_constants, fit PER stat, PER over-phase (stratified within phase) and
     PER era bucket. batting_sr lands M ~= 94.5, boundary_pct ~= 93. A rare event
     (dismissal_pct) can fall below the sampling-noise floor: its between-season
     signal is undetectable at the batter-season level, so it never stabilizes
     (M = null), the honest read, not a bug.

  engines/half_life.json       the freshness table. Per metric (srplus,
     boundary_pct, bowling_economy) the same-player cross-season persistence
        r(delta) = r0 * 0.5^(delta / H)
     fit log-linearly with a FREE r0 (sampling noise attenuates r(1), so forcing
     r0 = 1 badly underestimates H). Each season is reliability pre-shrunk toward
     the metric's population mean with the stat's own M before correlating, and a
     gap enters the fit only with enough pairs to trust its correlation. SR+ lands
     r0 ~= 0.37, H ~= 5.3 seasons (NOT the naive ~2 a forced r0 gives). Each
     half-life is named to its metric; the honest recount ships over any teaser.

  engines/truetalent.json      the shrinkage-slider params, PID-KEYED. For the
     era-fair SR+ metric (100 = league average), a wide candidate pool of every
     player with >= 200 career balls, each row:
        regressed = pop_mean + (raw - pop_mean) * n / (n + lambda*M)
        ci        = regressed +/- z * sqrt(sigma2 / (n + lambda*M))
     with z = 1.2816 (80% CI), M the batting_sr stabilization point, and pop_mean
     the league's own SR+ centre (100 by construction, a WPL row regresses toward
     the WPL average, never a cross-league mean). Stored at lambda = 1 (full prior);
     the client computes any lambda from raw / n / the block params. V Kohli career
     IPL SR+ 100.87 -> 100.86 (barely moves, huge sample); a thin player collapses
     toward 100.

Stdlib only, no numpy. Byte-deterministic (compact JSON, sorted keys; no
randomness). Reads players.json + engines/srplus.json (both already emitted by
R7a / engine #1). Emits only under engines/, so it has zero meta.json exposure.

Conventions match the rest of the pipeline: a wide is not a ball faced (SR
convention); a legal ball bowled excludes wides and no-balls; the bowler-charged
economy numerator is batter runs + wides + no-balls; over-phases are powerplay
(overs 1-6), middle (7-15), death (16-20); pids come from info.registry.people via
h2h.resolve, so two namesakes are never regressed onto one row.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten
import h2h                        # person_registry / resolve (registry pid lookup)

ENGINES_DIR = canon.OUT_ROOT / "engines"

# --- reliability / regression constants ---
Z_80 = 1.2816                 # two-sided 80% CI (the 0.90 quantile of N(0,1))
BAT_MIN_BALLS = 100           # batter-season group qualifier (== par.SRPLUS_MIN_BALLS)
BOWL_MIN_BALLS = 100          # bowler-season group qualifier (legal balls)
PHASE_MIN_BALLS = 50          # per-phase group qualifier (a phase holds ~1/3 the balls)
ERA_MIN_BALLS = 100           # per-era group qualifier
TRUETALENT_MIN_BALLS = 200    # career floor for the shrinkage-slider candidate pool
HALFLIFE_MAX_GAP = 8          # season gaps the autocorrelation is measured over
HALFLIFE_MIN_FIT_PAIRS = 300  # a gap enters the half-life fit only with >= this many pairs
SRPLUS_CENTRE = 100.0         # SR+ definitional league mean (100 = a league-average batter)

PHASES = ("pp", "middle", "death")

# Era buckets (league-scoped), same bands as par.py / scenes.py.
IPL_ERA_BANDS = (
    ("2008-2010", 2008, 2010),
    ("2011-2015", 2011, 2015),
    ("2016-2019", 2016, 2019),
    ("2020-2022", 2020, 2022),
    ("2023-2026", 2023, 2026),
)
WPL_ERA_BANDS = (("2023-2026", 2023, 2026),)


def phase_of(over: int) -> str:
    if over <= 5:
        return "pp"
    if over <= 14:
        return "middle"
    return "death"


# ---------------------------------------------------------------------------
# The one pid-resolved corpus pass
# ---------------------------------------------------------------------------
#
# Per (pid, league, season, phase) we tally, on the batting side, faced balls and
# the sums each rate stat needs; on the bowling side, legal balls and the same.
# BAT record:  [n_faced, sum_runs, sum_runs2, n_boundary, n_dot, n_dismiss]
# BOWL record: [n_legal, sum_legal_runs, sum_legal_runs2, n_dot_bowl, charged]
#   (charged = batter runs + wides + no-balls over ALL of the bowler-season's
#    deliveries, the bowler-charged economy numerator; the ball-level variance
#    for economy uses off-the-bat runs on legal balls, its dominant term.)


def _new_bat():
    return [0, 0, 0, 0, 0, 0]


def _new_bowl():
    return [0, 0, 0, 0, 0]


def build(data_root: Path = canon.DATA_ROOT, out_root: Path = canon.OUT_ROOT) -> dict:
    bat: dict = defaultdict(_new_bat)     # (pid, league, season, phase) -> BAT record
    bowl: dict = defaultdict(_new_bowl)   # (pid, league, season, phase) -> BOWL record
    # per-league ball-level runs stats (faced balls) for the SR+ CI sigma2.
    league_runs: dict = defaultdict(lambda: [0, 0, 0])   # league -> [n, sum, sum2]
    npoints = 0

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        reg = h2h.person_registry(info)
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue  # standing rule: super overs never enter the stream
            for over in innings["overs"]:
                ph = phase_of(over["over"])
                for dl in over["deliveries"]:
                    npoints += 1
                    ex = dl.get("extras", {})
                    is_wide = "wides" in ex
                    is_noball = "noballs" in ex
                    legal = not (is_wide or is_noball)
                    rb = dl["runs"]["batter"]
                    total = dl["runs"]["total"]
                    charged = rb + ex.get("wides", 0) + ex.get("noballs", 0)
                    bpid = h2h.resolve(reg, dl["batter"])
                    wpid = h2h.resolve(reg, dl["bowler"])

                    # Batting side: a wide is not a ball faced (SR convention).
                    if not is_wide:
                        c = bat[(bpid, league, season, ph)]
                        c[0] += 1
                        c[1] += rb
                        c[2] += rb * rb
                        if rb >= 4:
                            c[3] += 1
                        if rb == 0:
                            c[4] += 1
                        # dismissal% is the striker's all-cause out-rate per faced
                        # ball (rare -> the highest M; a big raw count on few balls
                        # must NOT read as trustworthy).
                        for w in dl.get("wickets", []):
                            if h2h.resolve(reg, w.get("player_out", dl["batter"])) == bpid:
                                c[5] += 1
                                break
                        lr = league_runs[league]
                        lr[0] += 1
                        lr[1] += rb
                        lr[2] += rb * rb

                    # Bowling side: charged runs accrue on every delivery; a legal
                    # ball excludes wides and no-balls.
                    d = bowl[(wpid, league, season, ph)]
                    d[4] += charged
                    if legal:
                        d[0] += 1
                        d[1] += rb
                        d[2] += rb * rb
                        if total == 0:
                            d[3] += 1

    # Join the already-emitted engine tables (no extra corpus pass): the SR+
    # metric (engine #1) and the registry pid map (R7a).
    players = json.loads((out_root / "players.json").read_text())
    name_of = {p["pid"]: p["name"] for p in players["players"]}
    pid_league = {p["pid"]: p["leagues"][0] for p in players["players"]}
    name_to_pids = players["name_to_pids"]
    srplus = json.loads((out_root / "engines" / "srplus.json").read_text())

    # Fold every SR+ batter-season onto its registry pid (aliases collapse to one
    # pid; a same-league namesake would be ambiguous and is skipped + counted).
    srplus_ps: dict = defaultdict(lambda: [0, 0, 0.0])   # (pid, league, season) -> [balls, runs, exp]
    ambiguous = 0
    for r in srplus["batter_seasons"]:
        cand = [pid for pid in name_to_pids.get(r["batter"], [])
                if pid_league.get(pid) == r["league"]]
        if len(cand) != 1:
            ambiguous += 1
            continue
        a = srplus_ps[(cand[0], r["league"], r["season"])]
        a[0] += r["balls"]
        a[1] += r["runs"]
        a[2] += r["expected_runs"]

    return {
        "bat": dict(bat),
        "bowl": dict(bowl),
        "league_runs": dict(league_runs),
        "srplus_ps": dict(srplus_ps),
        "name_of": name_of,
        "pid_league": pid_league,
        "ambiguous": ambiguous,
        "npoints": npoints,
    }


# ---------------------------------------------------------------------------
# DerSimonian-Laird variance components -> the stabilization point M
# ---------------------------------------------------------------------------


def dl_components(sigma2: float, groups: list) -> dict:
    """Generalized from h2h.eb_constants: given the ball-level within variance
    ``sigma2`` and per-group ``(n, mean)`` pairs, the method-of-moments between-
    group variance tau2 and the stabilization point M = sigma2 / tau2.

    When the observed between-group spread does not exceed what sampling noise
    alone would produce (Q <= df), tau2 clamps to 0: the stat does not stabilize
    at this grouping (M = null), which is the honest read for a rare event.
    """
    means = [(n, m) for n, m in groups if n > 0]
    ng = len(means)
    base = {"sigma2": round(sigma2, 5), "n_groups": ng}
    if ng < 2 or sigma2 <= 0:
        return {**base, "M": None, "tau2": 0.0, "mean": None, "stabilizes": False}
    sum_n = sum(n for n, _ in means)
    grand = sum(n * m for n, m in means) / sum_n
    q = sum(n * (m - grand) ** 2 for n, m in means) / sigma2
    sum_n2 = sum(n * n for n, _ in means)
    c_dl = sum_n - sum_n2 / sum_n
    tau2 = max(0.0, (q - (ng - 1)) / c_dl) * sigma2
    base["mean"] = round(grand, 5)
    if tau2 > 0:
        return {**base, "M": round(sigma2 / tau2, 2),
                "tau2": round(tau2, 6), "stabilizes": True}
    return {**base, "M": None, "tau2": 0.0, "stabilizes": False}


def _bucket_M(cells, group_key, n_of, vsx, vsx2, mean_num, min_balls):
    """sigma2 (pooled ball-level over the given cells) + DL over the groups the
    ``group_key`` folds the cells into, keeping only groups with >= min_balls."""
    tot_n = tot_sx = tot_sx2 = 0.0
    agg: dict = defaultdict(lambda: [0, 0.0, 0.0])   # n, mean_numer(sum), (unused)
    for key, rec in cells:
        n = n_of(rec)
        if n == 0:
            continue
        tot_n += n
        tot_sx += vsx(rec)
        tot_sx2 += vsx2(rec)
        a = agg[group_key(key)]
        a[0] += n
        a[1] += mean_num(rec)
    if tot_n == 0:
        return dl_components(0.0, [])
    sigma2 = tot_sx2 / tot_n - (tot_sx / tot_n) ** 2
    groups = [(a[0], a[1] / a[0]) for a in agg.values() if a[0] >= min_balls]
    return dl_components(sigma2, groups)


# A stat spec: how to read the per-ball value out of a cell record.
#   n     -> the number of trials (faced balls / legal balls)
#   vsx   -> sum of the ball value (drives sigma2 numerator)
#   vsx2  -> sum of the ball value squared (drives sigma2)
#   mean_num -> the group-mean numerator (== vsx for every stat but economy,
#               whose group mean is the bowler-charged economy while its ball-
#               level variance uses off-the-bat runs on legal balls)
BAT_STATS = {
    "batting_sr": {
        "unit": "runs per ball faced",
        "trials": "balls faced (wides excluded)",
        "gloss": "how hard a batter scores; settles into a real number at about 95 balls",
        "n": lambda c: c[0], "vsx": lambda c: c[1], "vsx2": lambda c: c[2],
        "mean_num": lambda c: c[1],
    },
    "boundary_pct": {
        "unit": "share of faced balls hit for four or six",
        "trials": "balls faced (wides excluded)",
        "gloss": "how often a batter finds the fence",
        "n": lambda c: c[0], "vsx": lambda c: c[3], "vsx2": lambda c: c[3],
        "mean_num": lambda c: c[3],
    },
    "dot_pct": {
        "unit": "share of faced balls scored off for zero",
        "trials": "balls faced (wides excluded)",
        "gloss": "how often a batter is kept quiet",
        "n": lambda c: c[0], "vsx": lambda c: c[4], "vsx2": lambda c: c[4],
        "mean_num": lambda c: c[4],
    },
    "dismissal_pct": {
        "unit": "share of faced balls the striker is dismissed on",
        "trials": "balls faced (wides excluded)",
        "gloss": "a rare event; the noise dominates, so it needs the most balls",
        "n": lambda c: c[0], "vsx": lambda c: c[5], "vsx2": lambda c: c[5],
        "mean_num": lambda c: c[5],
    },
}
BOWL_STATS = {
    "bowling_economy": {
        "unit": "bowler-charged runs per legal ball (batter runs + wides + no-balls)",
        "trials": "legal balls bowled (wides and no-balls excluded)",
        "gloss": "how few runs a bowler leaks; the ball-level variance uses off-the-"
                 "bat runs on legal balls, its dominant term",
        "n": lambda c: c[0], "vsx": lambda c: c[1], "vsx2": lambda c: c[2],
        "mean_num": lambda c: c[4],
    },
    "bowling_dot_pct": {
        "unit": "share of legal balls that are dots (no run at all)",
        "trials": "legal balls bowled (wides and no-balls excluded)",
        "gloss": "how often a bowler concedes nothing",
        "n": lambda c: c[0], "vsx": lambda c: c[3], "vsx2": lambda c: c[3],
        "mean_num": lambda c: c[3],
    },
}


def _stat_block(cells_all, spec, disc_min):
    """overall + by_phase (stratified) + by_era for one stat."""
    key_pls = lambda k: (k[0], k[1], k[2])   # (pid, league, season)
    items = list(cells_all.items())

    overall = _bucket_M(items, key_pls, spec["n"], spec["vsx"], spec["vsx2"],
                        spec["mean_num"], disc_min)

    by_phase = {}
    for ph in PHASES:
        sub = [(k, r) for k, r in items if k[3] == ph]
        by_phase[ph] = _bucket_M(sub, key_pls, spec["n"], spec["vsx"], spec["vsx2"],
                                 spec["mean_num"], PHASE_MIN_BALLS)

    by_era = {}
    for lg, bands in (("ipl", IPL_ERA_BANDS), ("wpl", WPL_ERA_BANDS)):
        for label, lo, hi in bands:
            sub = [(k, r) for k, r in items
                   if k[1] == lg and lo <= k[2] <= hi]
            by_era[f"{lg} {label}"] = _bucket_M(
                sub, key_pls, spec["n"], spec["vsx"], spec["vsx2"],
                spec["mean_num"], ERA_MIN_BALLS)

    return {
        "unit": spec["unit"],
        "trials": spec["trials"],
        "gloss": spec["gloss"],
        "min_balls": disc_min,
        "overall": overall,
        "by_phase": by_phase,
        "by_era": by_era,
    }


def stabilization_doc(agg: dict) -> dict:
    stats = {}
    for name, spec in BAT_STATS.items():
        stats[name] = _stat_block(agg["bat"], spec, BAT_MIN_BALLS)
    for name, spec in BOWL_STATS.items():
        stats[name] = _stat_block(agg["bowl"], spec, BOWL_MIN_BALLS)
    return {
        "engine": "R7b credibility: stabilization points (the trust meter)",
        "method": (
            "reliability(n) = n / (n + M): a rate stat is half signal at n = M "
            "balls. M = sigma2_within / tau2_between via the DerSimonian-Laird "
            "variance-components estimator (generalized from h2h.eb_constants), fit "
            "PER stat, PER over-phase (stratified within phase) and PER era bucket. "
            "sigma2_within is the ball-level variance over ALL of the discipline's "
            "balls; tau2_between is the method-of-moments between-(pid, league, "
            "season) variance over the qualifying groups. M is driven by n (the "
            "sample), NEVER the numerator, so a rare event needs the most balls. "
            "When the between-season spread does not exceed sampling noise (Q <= "
            "df), tau2 clamps to 0 and the stat does not stabilize at this grouping "
            "(M = null), the honest read, e.g. batter dismissal% at the season "
            "level."
        ),
        "phase_definitions": {
            "pp": "overs 1-6 (0-based over index 0-5)",
            "middle": "overs 7-15 (over index 6-14)",
            "death": "overs 16-20 (over index 15-19)",
        },
        "group": "one group per (registry pid, league, season) meeting the min-balls floor",
        "min_balls": {
            "batting": BAT_MIN_BALLS, "bowling": BOWL_MIN_BALLS,
            "phase": PHASE_MIN_BALLS, "era": ERA_MIN_BALLS,
        },
        "stats": stats,
    }


# ---------------------------------------------------------------------------
# Metric half-life (the freshness dial)
# ---------------------------------------------------------------------------


def _pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def _fit_free_r0(autocorr, fit_gaps):
    """OLS of ln(r) on delta (free intercept): r(delta) = r0 * 0.5^(delta / H).
    slope = -ln2 / H, intercept = ln r0. Forcing r0 = 1 (through the origin) is the
    naive fit sampling noise makes wrong; a FREE r0 is the honest one."""
    xs = list(fit_gaps)
    ys = [math.log(autocorr[g]) for g in fit_gaps]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    var = sum((x - mx) ** 2 for x in xs) / n
    slope = cov / var
    inter = my - slope * mx
    return math.exp(inter), -math.log(2) / slope


def _half_life_metric(by_pid_season, pop_mean, M, min_balls, unit, gloss):
    """Same-player cross-season persistence, reliability pre-shrunk toward the
    metric's population mean with its own M before correlating."""
    pairs = defaultdict(lambda: [[], []])
    for _pid, seasons in by_pid_season.items():
        items = sorted(seasons.items())
        for i in range(len(items)):
            se_i, (vi, ni) = items[i]
            si = pop_mean + (vi - pop_mean) * ni / (ni + M)
            for j in range(i + 1, len(items)):
                se_j, (vj, nj) = items[j]
                gap = se_j - se_i
                if 1 <= gap <= HALFLIFE_MAX_GAP:
                    sj = pop_mean + (vj - pop_mean) * nj / (nj + M)
                    pairs[gap][0].append(si)
                    pairs[gap][1].append(sj)

    autocorr = {}
    n_pairs = {}
    for gap in range(1, HALFLIFE_MAX_GAP + 1):
        if gap in pairs:
            r = _pearson(pairs[gap][0], pairs[gap][1])
            if r is not None:
                autocorr[gap] = r
                n_pairs[gap] = len(pairs[gap][0])

    # A gap earns a place in the fit only with enough pairs to trust its r, and a
    # positive correlation the log-linear model can take.
    fit_gaps = [g for g in sorted(autocorr)
                if n_pairs[g] >= HALFLIFE_MIN_FIT_PAIRS and autocorr[g] > 0]
    r0, half_life = _fit_free_r0(autocorr, fit_gaps)

    return {
        "unit": unit,
        "gloss": gloss,
        "min_balls": min_balls,
        "shrink_prior_M": round(M, 2),
        "pop_mean": round(pop_mean, 5),
        "r0": round(r0, 4),
        "half_life_seasons": round(half_life, 3),
        "fit_gaps": fit_gaps,
        "autocorr": {str(g): round(autocorr[g], 4) for g in sorted(autocorr)},
        "n_pairs": {str(g): n_pairs[g] for g in sorted(n_pairs)},
    }


def half_life_doc(agg: dict, batting_M: float, boundary_M: float,
                  economy_M: float, boundary_mean: float, economy_mean: float) -> dict:
    # srplus (SR+) per (pid, season), folded onto pids already.
    srp_bp = defaultdict(dict)
    for (pid, _lg, se), (balls, runs, exp) in agg["srplus_ps"].items():
        if exp > 0:
            srp_bp[pid][se] = (100.0 * runs / exp, balls)

    # boundary% + economy per (pid, season), aggregated over phases.
    bnd_bp = defaultdict(dict)
    bnd_ps = defaultdict(lambda: [0, 0])   # (pid, league, season) -> [faced, boundary]
    for (pid, lg, se, _ph), c in agg["bat"].items():
        a = bnd_ps[(pid, lg, se)]
        a[0] += c[0]
        a[1] += c[3]
    for (pid, _lg, se), (faced, boundary) in bnd_ps.items():
        if faced >= BAT_MIN_BALLS:
            bnd_bp[pid][se] = (boundary / faced, faced)

    eco_bp = defaultdict(dict)
    eco_ps = defaultdict(lambda: [0, 0])   # (pid, league, season) -> [legal, charged]
    for (pid, lg, se, _ph), d in agg["bowl"].items():
        a = eco_ps[(pid, lg, se)]
        a[0] += d[0]
        a[1] += d[4]
    for (pid, _lg, se), (legal, charged) in eco_ps.items():
        if legal >= BOWL_MIN_BALLS:
            eco_bp[pid][se] = (charged / legal, legal)

    metrics = {
        "srplus": _half_life_metric(
            srp_bp, SRPLUS_CENTRE, batting_M, BAT_MIN_BALLS,
            "SR+ (era-fair strike rate; 100 = league average that season)",
            "how fast a batter's era-fair strike-rate edge goes stale"),
        "boundary_pct": _half_life_metric(
            bnd_bp, boundary_mean, boundary_M, BAT_MIN_BALLS,
            "share of faced balls hit for four or six",
            "how fast a batter's boundary-hitting edge goes stale"),
        "bowling_economy": _half_life_metric(
            eco_bp, economy_mean, economy_M, BOWL_MIN_BALLS,
            "bowler-charged runs per legal ball",
            "how fast a bowler's economy edge goes stale"),
    }
    return {
        "engine": "R7b credibility: metric half-life (the freshness dial)",
        "method": (
            "Same-player cross-season persistence r(delta) = r0 * 0.5^(delta / H), "
            "fit log-linearly with a FREE r0. Each batter/bowler-season is "
            "reliability pre-shrunk toward the metric's population mean with the "
            "stat's own M (n / (n + M)) before the Pearson correlation, and a season "
            "gap enters the fit only with >= "
            f"{HALFLIFE_MIN_FIT_PAIRS} pooled pairs and a positive r. Forcing r0 = 1 "
            "(the naive fit) ignores that sampling noise attenuates r(1) and badly "
            "underestimates H, so the honest free-r0 recount is what ships. Each "
            "half-life is named to its metric; there is no single global half-life."
        ),
        "metrics": metrics,
    }


# ---------------------------------------------------------------------------
# True-talent (the shrinkage slider), PID-keyed
# ---------------------------------------------------------------------------


def truetalent_doc(agg: dict, batting_M: float, sr_sigma2: float) -> dict:
    name_of = agg["name_of"]
    pid_league = agg["pid_league"]

    # Career SR+ per (pid, league): sum over the pid's qualifying batter-seasons.
    career = defaultdict(lambda: [0, 0, 0.0])   # (pid, league) -> [balls, runs, exp]
    for (pid, lg, _se), (balls, runs, exp) in agg["srplus_ps"].items():
        a = career[(pid, lg)]
        a[0] += balls
        a[1] += runs
        a[2] += exp

    # pop_mean per league is the SR+ calibration centre: 100 = a league-average
    # batter of that league's own era (a WPL row regresses toward WPL 100, never a
    # cross-league mean). It is 100 by construction, computed here for the record.
    pop_mean = {"ipl": SRPLUS_CENTRE, "wpl": SRPLUS_CENTRE}

    rows = []
    for (pid, lg), (balls, runs, exp) in career.items():
        if balls < TRUETALENT_MIN_BALLS or exp <= 0:
            continue
        mu = pop_mean[lg]
        raw = 100.0 * runs / exp
        regressed = mu + (raw - mu) * balls / (balls + batting_M)
        se = math.sqrt(sr_sigma2 / (balls + batting_M))
        rows.append({
            "pid": pid,
            "name": name_of.get(pid, pid),
            "league": lg,
            "n": balls,
            "raw": round(raw, 2),
            "regressed": round(regressed, 2),
            "ci_lo": round(regressed - Z_80 * se, 2),
            "ci_hi": round(regressed + Z_80 * se, 2),
        })
    rows.sort(key=lambda r: (-r["regressed"], r["pid"]))

    return {
        "engine": "R7b credibility: true talent (the shrinkage slider)",
        "stat": "batting_srplus",
        "method": (
            "regressed(lambda) = pop_mean + (raw - pop_mean) * n / (n + lambda*M); "
            "ci(lambda) = regressed +/- z * sqrt(sigma2 / (n + lambda*M)). lambda is "
            "the slider from 0 (as it happened) to 1 (best guess at true skill); the "
            "rows below are stored at lambda = 1, and the client computes any lambda "
            "from raw / n and these block params. raw is career SR+ (100 x actual "
            "runs / expected runs over the player's qualifying batter-seasons); M is "
            "the batting_sr stabilization point; sigma2 is the SR+ ball-level "
            "variance ((100 / mean-runs-per-ball)^2 x runs variance). PID-keyed, so "
            "two namesakes are never regressed onto one row."
        ),
        "pop_mean": pop_mean,
        "pop_mean_note": (
            "SR+ is league-calibrated: the league-season average batter is 100 by "
            "construction, so each league's own centre is 100 (not a shortcut, the "
            "definition). A small sample is pulled toward its league's 100, which is "
            "'the model leans on the average more', never 'this league is worse'."
        ),
        "M": round(batting_M, 2),
        "sigma2": round(sr_sigma2, 2),
        "z": Z_80,
        "z_note": "1.2816 = the 0.90 quantile of N(0,1), for a two-sided 80% interval",
        "min_balls": TRUETALENT_MIN_BALLS,
        "count": len(rows),
        "players": rows,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build_docs(data_root: Path = canon.DATA_ROOT, out_root: Path = canon.OUT_ROOT):
    agg = build(data_root, out_root)

    stab = stabilization_doc(agg)

    batting_M = stab["stats"]["batting_sr"]["overall"]["M"]
    boundary_M = stab["stats"]["boundary_pct"]["overall"]["M"]
    economy_M = stab["stats"]["bowling_economy"]["overall"]["M"]
    boundary_mean = stab["stats"]["boundary_pct"]["overall"]["mean"]
    economy_mean = stab["stats"]["bowling_economy"]["overall"]["mean"]

    half = half_life_doc(agg, batting_M, boundary_M, economy_M,
                         boundary_mean, economy_mean)

    # SR+ ball-level variance for the true-talent CI: (100 / mean-runs-per-ball)^2
    # x runs variance, pooled over both leagues (M is scale-invariant, so it is the
    # batting_sr M; only the variance rescales into SR+ units).
    tn = sum(v[0] for v in agg["league_runs"].values())
    ts = sum(v[1] for v in agg["league_runs"].values())
    ts2 = sum(v[2] for v in agg["league_runs"].values())
    mu = ts / tn
    sigma2_runs = ts2 / tn - mu * mu
    sr_sigma2 = (100.0 / mu) ** 2 * sigma2_runs

    true = truetalent_doc(agg, batting_M, sr_sigma2)

    return {"stabilization": stab, "half_life": half, "truetalent": true,
            "_agg_meta": {"npoints": agg["npoints"], "ambiguous": agg["ambiguous"]}}


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    docs = build_docs(out_root=out_root)
    ENGINES_DIR.mkdir(parents=True, exist_ok=True)
    (out_root / "engines").mkdir(parents=True, exist_ok=True)

    sizes = {}
    for name in ("stabilization", "half_life", "truetalent"):
        raw = flatten.compact_json(docs[name], sort_keys=True)
        (out_root / "engines" / f"{name}.json").write_bytes(raw)
        sizes[f"engines/{name}.json"] = (len(raw), len(flatten.gz_bytes(raw)))

    st = docs["stabilization"]["stats"]
    hl = docs["half_life"]["metrics"]
    tt = docs["truetalent"]

    for n, (r, g) in sizes.items():
        print(f"  {n:28s} raw={r:>8,}  gz={g:>7,}")
    print(
        "stabilization M: batting_sr "
        f"{st['batting_sr']['overall']['M']}  boundary_pct "
        f"{st['boundary_pct']['overall']['M']}  dot_pct "
        f"{st['dot_pct']['overall']['M']}  dismissal_pct "
        f"{st['dismissal_pct']['overall']['M']}  economy "
        f"{st['bowling_economy']['overall']['M']}  bowl_dot "
        f"{st['bowling_dot_pct']['overall']['M']}"
    )
    print(
        "half-life: srplus r0="
        f"{hl['srplus']['r0']} H={hl['srplus']['half_life_seasons']}  "
        f"boundary H={hl['boundary_pct']['half_life_seasons']}  "
        f"economy H={hl['bowling_economy']['half_life_seasons']}"
    )
    print(
        f"truetalent: pool={tt['count']} pop_mean={tt['pop_mean']} "
        f"M={tt['M']} sigma2={tt['sigma2']}"
    )
    for r in tt["players"]:
        if r["name"] in ("V Kohli", "AB de Villiers") and r["league"] == "ipl":
            print(f"  {r['name']}: n={r['n']} raw={r['raw']} -> regressed={r['regressed']} "
                  f"ci=[{r['ci_lo']}, {r['ci_hi']}]")
    if docs["_agg_meta"]["ambiguous"]:
        print(f"  (skipped {docs['_agg_meta']['ambiguous']} ambiguous same-league srplus rows)")
    return docs


if __name__ == "__main__":
    main()
