"""Engine #3 — win-probability lookup grids + Leverage Index (parallel track).

A precomputed win-probability lookup grid built from all 1,331 matches (never a
live model — the locked decision), plus the Leverage Index byproduct and the
first-innings defend curve. Powers R3b: the Net Session interlude's win meter,
Chapter 5's WPA-per-ball and the famous-final-over scrub, and (via LI) Chapter
8's leverage framing and the sandbox decision-ball flags.

  * NOT consumed by any R2a scene. This de-risks R3b and must clear the §5
    engine-validation gate — the BINDING calibration check (predicted vs actual
    win rate in bins, asserted within tolerance) plus WP monotonicity sanity
    checks live in tests/test_engines.py — BEFORE any Chapter-5 / interlude
    choreography is authored.

What is emitted (engines/wp_grid.json)
--------------------------------------
1. second_innings — P(chasing team wins) on the grid
       (era band) x (overs_left 1..20) x (wickets_in_hand 1..10) x (rrr_bucket)
   rrr = required runs per over = runs_needed x 6 / balls_left, bucketed by
   RRR_EDGES. Built empirically from every second-innings legal-ball state
   (target.overs == 20, non-D/L, super overs excluded), each labelled with the
   eventual result (ties resolved by outcome.eliminator; no-results dropped).
   Thin cells are empirical-Bayes shrunk toward the all-IPL pooled cell and a
   coarse (overs_left, rrr) marginal, then each overs_left slice is made
   jointly monotone — WP NON-INCREASING in rrr_bucket (harder chase -> lower
   win prob) and NON-DECREASING in wickets_in_hand — by weighted
   pool-adjacent-violators. A POOLED all-IPL grid and an evidence-masked WPL
   grid (shrunk toward IPL-pooled) are emitted alongside the era grids.

2. leverage_index — LI on the pooled grid: mean |WP swing to the next state|
   in each cell divided by the corpus mean. LI ~ 1 is an average ball; the
   endgame of a tight chase runs high. The byproduct that later powers
   decision-ball flags and the match EKG.

3. first_innings_defend — P(team batting first wins | final first-innings total
   bucket), per era. The "170-189 total defended 74% (2008-10) -> 38%
   (2023-26)" WPA teaser; monotone non-decreasing in total. (Mid-first-innings
   WP interpolates this via a projected total in R3b — noted, not built here.)

4. calibration — the binding gate's reliability table (predicted-WP deciles vs
   actual chase-win rate) plus the raw-data era anchor (a 9+ RPO chase with ~60
   balls left won 24.3% in 2008-12 vs 31.8% in 2023-26 — blueprint interlude).

Stdlib only. Byte-deterministic (key-sorted compact JSON). Writes only under
web/static/data/engines/ — it never touches an R1 or R2a artifact.
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

ENGINES_DIR = canon.OUT_ROOT / "engines"

# Era bands (same as re288.py / par.py).
IPL_ERA_BANDS = (
    ("2008-2010", 2008, 2010),
    ("2011-2015", 2011, 2015),
    ("2016-2019", 2016, 2019),
    ("2020-2022", 2020, 2022),
    ("2023-2026", 2023, 2026),
)

N_OVERS_LEFT = 20    # overs_left 1..20 -> index 0..19
N_WKTS_IN_HAND = 10  # wickets_in_hand 1..10 -> index 0..9

# Required-run-rate (runs per over) bucket edges -> 10 buckets.
RRR_EDGES = (6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 15.0, 20.0)
N_RRR = len(RRR_EDGES) + 1  # 10

# Empirical-Bayes pseudo-counts. K_POOL pulls a thin pooled cell toward its
# coarse (overs_left, rrr) marginal; K_ERA pulls a thin era cell toward the
# pooled cell. Small relative to a populous cell so well-evidenced states keep
# their own empirical win rate (calibration), large relative to a single-ball
# cell so it borrows strength.
K_POOL = 15.0
K_ERA = 20.0
K_WPL = 25.0  # WPL cells shrink harder toward IPL-pooled (88 matches)

# WPL minimum-evidence mask on the WP grid.
WPL_MASK_MIN_N = 12

# Calibration gate (the BINDING §5 check). A decile is "populated" at >= CALIB_MIN_N
# states; the gate requires ECE < CALIB_ECE_MAX and every populated decile within
# CALIB_BIN_MAX of the diagonal. Asserted in tests/test_engines.py.
CALIB_MIN_N = 500
CALIB_ECE_MAX = 0.03
CALIB_BIN_MAX = 0.05

# First-innings defend curve: total buckets [lo, lo+10) with a low/high catch-all.
DEFEND_LO = 120
DEFEND_HI = 230
DEFEND_STEP = 10

# Alternating isotonic (cyclic projection onto the two monotone cones) converges
# to a jointly monotone fixpoint since the cones are convex and intersect (the
# constant surface is feasible); a 10x10 slice needs a generous cap to drive the
# residual below ISO_EPS on the slowest cases.
ISO_MAX_ITERS = 2000
ISO_EPS = 1e-10


def _band_of(season: int) -> str | None:
    for label, lo, hi in IPL_ERA_BANDS:
        if lo <= season <= hi:
            return label
    return None


def rrr_bucket(rrr: float) -> int:
    for i, edge in enumerate(RRR_EDGES):
        if rrr < edge:
            return i
    return N_RRR - 1


def _is_legal(dl: dict) -> bool:
    extras = dl.get("extras", {})
    return "wides" not in extras and "noballs" not in extras


def chaser_won(info: dict, chasing_team: str) -> int | None:
    """1 if the second-batting team won, 0 if it lost, None if no result.

    Ties are resolved by the super-over winner (outcome.eliminator). Team names
    are canonicalized so the comparison is rename-safe.
    """
    outcome = info.get("outcome", {})
    result = outcome.get("result")
    if result == "no result":
        return None
    winner = outcome.get("winner")
    if not winner and result == "tie":
        winner = outcome.get("eliminator")
    if not winner:
        return None
    return 1 if canon.canon_team(winner) == canon.canon_team(chasing_team) else 0


# ---------------------------------------------------------------------------
# Corpus pass
# ---------------------------------------------------------------------------


class SecondInnings:
    """One second innings: the ordered per-legal-ball states and the result."""

    __slots__ = ("league", "era", "outcome", "states")

    def __init__(self, league, era, outcome):
        self.league = league
        self.era = era
        self.outcome = outcome
        self.states = []  # [(ol_idx, wih_idx, rb), ...] in legal-ball order


def build(data_root: Path = canon.DATA_ROOT):
    """Collect every second innings' state sequence + first-innings defend
    observations in one chronological pass."""
    innings_list = []
    # defend[(era, total_bucket)] = [batfirst_wins, n]
    defend = defaultdict(lambda: [0, 0])

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        dl_match = canon.is_dl(info)
        season = canon.canon_season(info)
        era = _band_of(season) if league == "ipl" else "wpl"
        if era is None:
            continue

        inns = [i for i in match.get("innings", []) if not canon.is_super_over(i)]
        if not inns:
            continue

        # --- first-innings defend curve (full first innings, non-D/L, decided)
        if not dl_match:
            first = inns[0]
            total = sum(
                dl["runs"]["total"]
                for over in first["overs"]
                for dl in over["deliveries"]
            )
            # "full" first innings: 20 overs bowled or all out (10 wickets)
            balls = sum(
                1 for over in first["overs"] for dl in over["deliveries"]
                if _is_legal(dl)
            )
            wkts = sum(
                len(dl["wickets"])
                for over in first["overs"] for dl in over["deliveries"]
                if "wickets" in dl
            )
            full = balls >= 120 or wkts >= 10
            batfirst_team = first["team"]
            cw = chaser_won(info, inns[1]["team"]) if len(inns) > 1 else None
            if full and cw is not None:
                tb = _total_bucket(total)
                d = defend[(era, tb)]
                d[1] += 1
                if cw == 0:  # chaser lost -> team batting first defended/won
                    d[0] += 1

        # --- second-innings WP states
        if len(inns) < 2:
            continue
        second = inns[1]
        target = second.get("target")
        if dl_match or not target or target.get("overs") != 20:
            continue
        cw = chaser_won(info, second["team"])
        if cw is None:
            continue
        target_runs = target["runs"]

        rec = SecondInnings(league, era, cw)
        score = 0
        wkts = 0
        legal = 0
        for over in second["overs"]:
            for dl in over["deliveries"]:
                if _is_legal(dl):
                    needed = target_runs - score
                    balls_left = 120 - legal
                    if balls_left > 0 and needed > 0 and wkts < 10:
                        ol_idx = math.ceil(balls_left / 6) - 1        # 0..19
                        wih_idx = (10 - wkts) - 1                     # 0..9
                        rrr = needed * 6.0 / balls_left
                        rec.states.append((ol_idx, wih_idx, rrr_bucket(rrr)))
                    legal += 1
                score += dl["runs"]["total"]
                if "wickets" in dl:
                    wkts += len(dl["wickets"])
        if rec.states:
            innings_list.append(rec)

    return innings_list, defend


def _total_bucket(total: int) -> int:
    """Index of the first-innings total bucket. 0 = < DEFEND_LO, then DEFEND_STEP
    bands, last = >= DEFEND_HI."""
    if total < DEFEND_LO:
        return 0
    if total >= DEFEND_HI:
        return (DEFEND_HI - DEFEND_LO) // DEFEND_STEP + 1
    return (total - DEFEND_LO) // DEFEND_STEP + 1


N_TOTAL_BUCKETS = (DEFEND_HI - DEFEND_LO) // DEFEND_STEP + 2


# ---------------------------------------------------------------------------
# Weighted isotonic (pool-adjacent-violators), monotone in either direction
# ---------------------------------------------------------------------------


def _pav(values, weights, increasing: bool):
    """Weighted isotonic regression. increasing=True enforces a NON-DECREASING
    sequence, False a NON-INCREASING one. All weights are strictly positive."""
    if increasing:
        fit = _pav_nonincreasing([-v for v in values], weights)
        return [-x for x in fit]
    return _pav_nonincreasing(values, weights)


def _pav_nonincreasing(values, weights):
    blk_wv, blk_w, blk_len, blk_mean = [], [], [], []
    for v, w in zip(values, weights):
        blk_wv.append(v * w)
        blk_w.append(w)
        blk_len.append(1)
        blk_mean.append(v)
        while len(blk_mean) >= 2 and blk_mean[-2] < blk_mean[-1]:
            wv = blk_wv[-1] + blk_wv[-2]
            ww = blk_w[-1] + blk_w[-2]
            ln = blk_len[-1] + blk_len[-2]
            blk_wv.pop(); blk_w.pop(); blk_len.pop(); blk_mean.pop()
            blk_wv[-1] = wv
            blk_w[-1] = ww
            blk_len[-1] = ln
            blk_mean[-1] = wv / ww
    out = []
    for ln, m in zip(blk_len, blk_mean):
        out.extend([m] * ln)
    return out


def _monotonize_slice(wp, weight):
    """For a single overs_left slice: 2-D grid over (wih 0..9, rrr 0..9). Make
    WP non-decreasing in wih and non-increasing in rrr by alternating weighted
    PAV to a fixpoint. wp / weight are [wih][rrr]."""
    surf = [row[:] for row in wp]
    for _ in range(ISO_MAX_ITERS):
        max_delta = 0.0
        # rows: fixed wih, non-increasing across rrr
        for i in range(N_WKTS_IN_HAND):
            fit = _pav(surf[i], weight[i], increasing=False)
            for j in range(N_RRR):
                max_delta = max(max_delta, abs(fit[j] - surf[i][j]))
                surf[i][j] = fit[j]
        # columns: fixed rrr, non-decreasing across wih
        for j in range(N_RRR):
            col = [surf[i][j] for i in range(N_WKTS_IN_HAND)]
            wt = [weight[i][j] for i in range(N_WKTS_IN_HAND)]
            fit = _pav(col, wt, increasing=True)
            for i in range(N_WKTS_IN_HAND):
                max_delta = max(max_delta, abs(fit[i] - surf[i][j]))
                surf[i][j] = fit[i]
        if max_delta < ISO_EPS:
            break
    return surf


# ---------------------------------------------------------------------------
# Grid assembly
# ---------------------------------------------------------------------------

EMPTY_W = 1e-6


def _raw_counts(innings_list):
    """Per (surface_key, ol, wih, rrr) -> [wins, n]. surface_key is an era
    label, 'pooled' (all IPL) or 'wpl'."""
    cells = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for rec in innings_list:
        keys = ((rec.era,) if rec.league == "wpl" else (rec.era, "pooled"))
        for (ol, wih, rb) in rec.states:
            for key in keys:
                c = cells[key][(ol, wih, rb)]
                c[0] += rec.outcome
                c[1] += 1
    return cells


def _global_rrr_marginal(pooled_cells, glob):
    """P(win | rrr_bucket) pooled over overs_left and wickets, made
    NON-INCREASING in rrr by weighted PAV. This is the physical anchor each
    (overs_left, rrr) marginal shrinks toward, so an EMPTY high-rrr tail cell
    imputes to a sensible low win prob (grrr[-1] ~ 0.01) instead of the scalar
    global chase-win rate (~0.52).

    Why this matters (it is the fix for the bin-1 over-prediction): without a
    per-rrr anchor, an unobserved high-rrr cell inherited the ~0.52 global rate;
    the non-increasing-in-rrr isotonic step then pooled that fake-high tail back
    into real, well-populated hard-chase cells (e.g. 17 overs left, 8 in hand,
    12-15 RPO: raw 0/52, inflated to ~0.21), systematically over-pricing hopeless
    early chases."""
    marg = defaultdict(lambda: [0, 0])  # rb -> [wins, n]
    for (_ol, _wih, rb), (w, n) in pooled_cells.items():
        m = marg[rb]
        m[0] += w
        m[1] += n
    vals, wts = [], []
    for rb in range(N_RRR):
        w, n = marg[rb]
        vals.append((w + K_POOL * glob) / (n + K_POOL))
        wts.append(n + 1.0)
    return _pav(vals, wts, increasing=False)


def _coarse_marginal(pooled_cells):
    """P(win | overs_left, rrr) pooled over wickets — the shrink prior for a thin
    pooled cell, and the global chase-win rate + per-rrr anchor it builds on.

    Each (overs_left, rrr) cell shrinks toward the per-rrr global anchor grrr[rb]
    (NOT the scalar global rate), and each overs_left row is then made
    non-increasing in rrr by weighted PAV. So the prior a consumer cell inherits
    already obeys the same physics the final surface isotonic enforces — an
    unobserved high-rrr cell can no longer pull a real hard-chase cell upward.
    Returns (coarse{(ol, rrr): p}, glob, grrr)."""
    marg = defaultdict(lambda: [0, 0])  # (ol, rrr) -> [wins, n]
    tot_w = tot_n = 0
    for (ol, _wih, rb), (w, n) in pooled_cells.items():
        m = marg[(ol, rb)]
        m[0] += w
        m[1] += n
        tot_w += w
        tot_n += n
    glob = tot_w / tot_n if tot_n else 0.5
    grrr = _global_rrr_marginal(pooled_cells, glob)
    coarse = {}
    for ol in range(N_OVERS_LEFT):
        row_vals, row_wts = [], []
        for rb in range(N_RRR):
            w, n = marg.get((ol, rb), (0, 0))
            row_vals.append((w + K_POOL * grrr[rb]) / (n + K_POOL))
            row_wts.append(n + 1.0)
        mono = _pav(row_vals, row_wts, increasing=False)
        for rb in range(N_RRR):
            coarse[(ol, rb)] = mono[rb]
    return coarse, glob, grrr


def _shrunk_pooled(pooled_cells, coarse, glob):
    """Pooled cell WP, EB-shrunk toward the coarse (ol, rrr) marginal."""
    out = {}
    for ol in range(N_OVERS_LEFT):
        for wih in range(N_WKTS_IN_HAND):
            for rb in range(N_RRR):
                w, n = pooled_cells.get((ol, wih, rb), (0, 0))
                prior = coarse.get((ol, rb), glob)
                out[(ol, wih, rb)] = ((w + K_POOL * prior) / (n + K_POOL), n)
    return out


def _grid_from_cells(cells, parent, K):
    """Shrink each (ol, wih, rb) cell toward parent[cell] with pseudo-count K,
    then monotonize each overs_left slice. Returns (wp[ol][wih][rb], n[ol][wih][rb])."""
    wp = [[[0.0] * N_RRR for _ in range(N_WKTS_IN_HAND)]
          for _ in range(N_OVERS_LEFT)]
    ncount = [[[0] * N_RRR for _ in range(N_WKTS_IN_HAND)]
              for _ in range(N_OVERS_LEFT)]
    for ol in range(N_OVERS_LEFT):
        for wih in range(N_WKTS_IN_HAND):
            for rb in range(N_RRR):
                w, n = cells.get((ol, wih, rb), (0, 0))
                p = parent[(ol, wih, rb)][0] if isinstance(parent[(ol, wih, rb)], tuple) \
                    else parent[(ol, wih, rb)]
                wp[ol][wih][rb] = (w + K * p) / (n + K)
                ncount[ol][wih][rb] = n
    # Monotonize per overs_left slice. Weight each cell by its POST-SHRINK
    # effective sample size (n + K): every cell then carries >= K evidence at
    # its shrunk value, which keeps the two monotone cones well-conditioned so
    # the cyclic projection converges fast to a jointly monotone fixpoint (near-
    # equal tiny weights otherwise make the rate arbitrarily slow on the sparse
    # early-era / WPL surfaces).
    for ol in range(N_OVERS_LEFT):
        weight = [[ncount[ol][i][j] + K for j in range(N_RRR)]
                  for i in range(N_WKTS_IN_HAND)]
        wp[ol] = _monotonize_slice(wp[ol], weight)
    return wp, ncount


def _leverage(innings_list, pooled_wp):
    """LI on the pooled grid: mean |WP swing to the next state| per cell / corpus
    mean. Terminal transition uses the actual outcome (0/1)."""
    cell_sum = defaultdict(float)
    cell_n = defaultdict(int)
    tot_sum = 0.0
    tot_n = 0
    for rec in innings_list:
        st = rec.states
        m = len(st)
        for i in range(m):
            wp_i = pooled_wp[st[i][0]][st[i][1]][st[i][2]]
            if i + 1 < m:
                nxt = pooled_wp[st[i + 1][0]][st[i + 1][1]][st[i + 1][2]]
            else:
                nxt = float(rec.outcome)  # match resolved
            d = abs(nxt - wp_i)
            cell_sum[st[i][:3]] += d
            cell_n[st[i][:3]] += 1
            tot_sum += d
            tot_n += 1
    corpus_mean = tot_sum / tot_n if tot_n else 0.0
    li = [[[None] * N_RRR for _ in range(N_WKTS_IN_HAND)]
          for _ in range(N_OVERS_LEFT)]
    for (ol, wih, rb), s in cell_sum.items():
        n = cell_n[(ol, wih, rb)]
        if n and corpus_mean > 0:
            li[ol][wih][rb] = round((s / n) / corpus_mean, 3)
    return li, corpus_mean


# ---------------------------------------------------------------------------
# First-innings defend curve
# ---------------------------------------------------------------------------


def _defend_curve(defend):
    """Per era: P(bat-first wins | total bucket), monotone non-decreasing in
    total (weighted PAV), with the global bat-first rate as the shrink prior."""
    out = {}
    labels = [label for label, _l, _h in IPL_ERA_BANDS] + ["wpl"]
    bucket_labels = _defend_bucket_labels()
    for era in labels:
        vals = []
        wts = []
        ns = []
        for tb in range(N_TOTAL_BUCKETS):
            w, n = defend.get((era, tb), (0, 0))
            ns.append(n)
            # light shrink toward 0.5 keeps empty buckets neutral before PAV
            vals.append((w + 3.0 * 0.5) / (n + 3.0))
            wts.append(n + EMPTY_W)
        mono = _pav(vals, wts, increasing=True)
        surf_key = f"ipl {era}" if era != "wpl" else "wpl 2023-2026"
        out[surf_key] = {
            "bucket_labels": bucket_labels,
            "p_batfirst_win": [round(x, 3) for x in mono],
            "n": ns,
        }
    return out


def _defend_bucket_labels():
    labels = [f"<{DEFEND_LO}"]
    lo = DEFEND_LO
    while lo < DEFEND_HI:
        labels.append(f"{lo}-{lo + DEFEND_STEP - 1}")
        lo += DEFEND_STEP
    labels.append(f"{DEFEND_HI}+")
    return labels


# ---------------------------------------------------------------------------
# Calibration (the binding gate) + raw era anchor
# ---------------------------------------------------------------------------


def _calibration(innings_list, era_grids):
    """Reliability table: bin every second-innings state by its predicted WP
    (from its own era grid) into deciles; report mean predicted vs actual
    chase-win rate and n per bin, plus the evidence-weighted mean abs deviation
    (the number the gate asserts)."""
    bins = [[0.0, 0.0, 0] for _ in range(10)]  # sum_pred, sum_actual, n
    for rec in innings_list:
        grid = era_grids.get(rec.era)
        if grid is None:
            continue
        for (ol, wih, rb) in rec.states:
            p = grid[ol][wih][rb]
            b = min(9, int(p * 10))
            bins[b][0] += p
            bins[b][1] += rec.outcome
            bins[b][2] += 1
    rows = []
    wdev = 0.0
    tot = 0
    worst = 0.0
    for b in range(10):
        s_pred, s_act, n = bins[b]
        if not n:
            rows.append({"bin": b, "n": 0, "pred": None, "actual": None})
            continue
        pred = s_pred / n
        act = s_act / n
        dev = abs(pred - act)
        rows.append({
            "bin": b, "n": n,
            "pred": round(pred, 4),
            "actual": round(act, 4),
            "abs_dev": round(dev, 4),
        })
        wdev += dev * n
        tot += n
        if n >= CALIB_MIN_N:
            worst = max(worst, dev)
    ece = round(wdev / tot, 5) if tot else None
    return {
        "note": (
            "Reliability table (the interlude's calibration plot): each "
            "second-innings legal-ball state scored by its own era grid, binned "
            "into predicted-WP deciles; pred = mean predicted WP, actual = "
            "observed chase-win frequency, per bin. A lookup grid is calibrated "
            "by construction; shrinkage regularizes thin cells and the monotone "
            "constraint is mild, so the deciles track the diagonal."
        ),
        "bins": rows,
        # ECE = evidence-weighted mean |pred - actual| over deciles (the gate's
        # headline number). weighted_mean_abs_dev is kept as its long-form alias.
        "ece": ece,
        "weighted_mean_abs_dev": ece,
        "worst_populated_bin_abs_dev": round(worst, 5),
        "worst_populated_bin_min_n": CALIB_MIN_N,
        "tolerance": {"ece_max": CALIB_ECE_MAX, "bin_abs_dev_max": CALIB_BIN_MAX},
        "n": tot,
    }


def _era_anchor(data_root: Path = canon.DATA_ROOT):
    """Raw-data anchor (independent of the grid): a 9+ RPO chase with ~60 balls
    left won 24.3% in 2008-12 vs 31.8% in 2023-26 (blueprint interlude). Bands
    are the blueprint's, not the engine's era bands, on purpose."""
    early = [0, 0]   # 2008-2012
    recent = [0, 0]  # 2023-2026
    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        if league != "ipl":
            continue
        with open(path) as fh:
            m = json.load(fh)
        info = m["info"]
        if canon.is_dl(info):
            continue
        season = canon.canon_season(info)
        band = early if 2008 <= season <= 2012 else (
            recent if 2023 <= season <= 2026 else None)
        if band is None:
            continue
        inns = [i for i in m.get("innings", []) if not canon.is_super_over(i)]
        if len(inns) < 2:
            continue
        second = inns[1]
        target = second.get("target")
        if not target or target.get("overs") != 20:
            continue
        cw = chaser_won(info, second["team"])
        if cw is None:
            continue
        tr = target["runs"]
        score = 0
        wkts = 0
        legal = 0
        for over in second["overs"]:
            for dl in over["deliveries"]:
                if _is_legal(dl):
                    needed = tr - score
                    balls_left = 120 - legal
                    if 57 <= balls_left <= 63 and needed > 0 and wkts < 10:
                        if needed * 6.0 / balls_left >= 9.0:
                            band[0] += cw
                            band[1] += 1
                    legal += 1
                score += dl["runs"]["total"]
                if "wickets" in dl:
                    wkts += len(dl["wickets"])
    return {
        "definition": "chase needing >= 9 RPO with ~60 balls left (balls_left in 57..63)",
        "ipl_2008_2012": {"wins": early[0], "n": early[1],
                          "win_rate": round(early[0] / early[1], 4) if early[1] else None},
        "ipl_2023_2026": {"wins": recent[0], "n": recent[1],
                          "win_rate": round(recent[0] / recent[1], 4) if recent[1] else None},
    }


# ---------------------------------------------------------------------------
# Doc assembly + emission
# ---------------------------------------------------------------------------


def _emit_grid(wp, ncount, li=None, masked=None):
    entry = {
        "wp": [[[round(wp[ol][wih][rb], 4) for rb in range(N_RRR)]
                for wih in range(N_WKTS_IN_HAND)] for ol in range(N_OVERS_LEFT)],
        "n": [[[ncount[ol][wih][rb] for rb in range(N_RRR)]
               for wih in range(N_WKTS_IN_HAND)] for ol in range(N_OVERS_LEFT)],
    }
    if li is not None:
        entry["leverage_index"] = li
    if masked is not None:
        entry["masked"] = masked
    return entry


def build_doc(data_root: Path = canon.DATA_ROOT) -> dict:
    innings_list, defend = build(data_root)
    cells = _raw_counts(innings_list)

    pooled_raw = cells.get("pooled", {})
    coarse, glob, grrr = _coarse_marginal(pooled_raw)
    pooled_parent = _shrunk_pooled(pooled_raw, coarse, glob)
    pooled_wp, pooled_n = _grid_from_cells(pooled_raw, pooled_parent, K_POOL)

    # pooled grid is the parent for era + WPL grids
    pooled_wp_dict = {
        (ol, wih, rb): pooled_wp[ol][wih][rb]
        for ol in range(N_OVERS_LEFT)
        for wih in range(N_WKTS_IN_HAND)
        for rb in range(N_RRR)
    }

    era_grids = {}
    surfaces = {}
    for label, _lo, _hi in IPL_ERA_BANDS:
        wp, ncount = _grid_from_cells(cells.get(label, {}), pooled_wp_dict, K_ERA)
        era_grids[label] = wp
        surfaces[f"ipl {label}"] = _emit_grid(wp, ncount)

    # pooled surface carries the Leverage Index
    li, corpus_mean = _leverage(innings_list, pooled_wp)
    surfaces["ipl pooled"] = _emit_grid(pooled_wp, pooled_n, li=li)

    # WPL grid: shrunk hard toward IPL-pooled, evidence-masked
    wpl_cells = cells.get("wpl", {})
    wpl_wp, wpl_n = _grid_from_cells(wpl_cells, pooled_wp_dict, K_WPL)
    era_grids["wpl"] = wpl_wp
    wpl_masked = [[[1 if wpl_n[ol][wih][rb] < WPL_MASK_MIN_N else 0
                    for rb in range(N_RRR)] for wih in range(N_WKTS_IN_HAND)]
                  for ol in range(N_OVERS_LEFT)]
    surfaces["wpl 2023-2026"] = _emit_grid(wpl_wp, wpl_n, masked=wpl_masked)

    n_wpl_cells = N_OVERS_LEFT * N_WKTS_IN_HAND * N_RRR
    n_wpl_masked = sum(wpl_masked[ol][wih][rb]
                       for ol in range(N_OVERS_LEFT)
                       for wih in range(N_WKTS_IN_HAND)
                       for rb in range(N_RRR))

    calibration = _calibration(innings_list, era_grids)
    calibration["era_anchor"] = _era_anchor(data_root)

    return {
        "engine": "3 — win-probability lookup grids + Leverage Index",
        "consumed_by": "R3b (Net Session win meter, Ch 5 WPA / final-over scrub) + Ch 8 leverage framing + sandbox decision-ball flags. Not consumed by any R2a scene.",
        "second_innings": {
            "state": {
                "era": "era band (or 'ipl pooled' / 'wpl 2023-2026')",
                "overs_left": "1..20 -> index 0..19 = ceil(balls_left/6)",
                "wickets_in_hand": "1..10 -> index 0..9 = 10 - wickets_fallen",
                "rrr_bucket": f"required runs per over, edges {list(RRR_EDGES)} -> {N_RRR} buckets",
                "value": "wp[overs_left][wickets_in_hand][rrr_bucket] = P(chasing team wins)",
            },
            "method": (
                "Empirical chase-win rate over every second-innings legal-ball "
                "state (target.overs == 20, non-D/L, super overs excluded; ties "
                "by outcome.eliminator; no-results dropped). Cells EB-shrunk "
                f"toward the all-IPL pooled cell (K={K_ERA}); the pooled cell "
                f"shrinks toward the coarse (overs_left, rrr) marginal (K={K_POOL}); "
                f"WPL shrinks toward IPL-pooled (K={K_WPL}). Each overs_left slice "
                "is then made jointly monotone by weighted pool-adjacent-violators."
            ),
            "monotonicity": (
                "WP non-increasing in rrr_bucket (harder chase -> lower win prob) "
                "and non-decreasing in wickets_in_hand, per era per overs_left. "
                "Asserted in tests/test_engines.py."
            ),
            "rrr_edges": list(RRR_EDGES),
            "global_rrr_anchor": (
                "P(chase win | rrr_bucket) pooled over all overs_left / wickets, "
                "monotone non-increasing in rrr. The physical prior every thin or "
                "unobserved (overs_left, rrr) cell shrinks toward, so an empty "
                "high-rrr tail cell imputes low instead of inheriting the global "
                "chase-win rate."
            ),
            "global_rrr_anchor_values": [round(x, 4) for x in grrr],
            "wpl_mask_min_n": WPL_MASK_MIN_N,
            "wpl_mask": {
                "note": (
                    "Minimum-evidence mask for the WPL win grid (88 matches, not "
                    "1,331): a WPL cell built from fewer than wpl_mask_min_n "
                    "second-innings observations carries masked=1 in the "
                    "'wpl 2023-2026' surface. The interlude renders masked cells "
                    "hatched ('not enough WPL cricket yet') rather than showing a "
                    "shrinkage artifact as a finding."
                ),
                "min_n": WPL_MASK_MIN_N,
                "cells_total": n_wpl_cells,
                "cells_masked": n_wpl_masked,
                "cells_evidenced": n_wpl_cells - n_wpl_masked,
            },
            "surfaces": surfaces,
        },
        "leverage_index": {
            "note": (
                "On the 'ipl pooled' surface: mean |WP swing to the next state| "
                "in the cell / corpus mean. ~1 = an average ball; a tight endgame "
                "runs high. Null where the pooled cell was never observed."
            ),
            "corpus_mean_abs_dwp": round(corpus_mean, 5),
        },
        "first_innings_defend": {
            "note": (
                "P(team batting first wins | final first-innings total bucket), "
                "per era; full first innings (>=120 balls or all out), non-D/L, "
                "decided. Monotone non-decreasing in total. Mid-first-innings WP "
                "interpolates this via a projected total in R3b (not built here)."
            ),
            "surfaces": _defend_curve(defend),
        },
        "calibration": calibration,
    }


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    doc = build_doc()
    engines_dir = out_root / "engines"
    engines_dir.mkdir(parents=True, exist_ok=True)
    raw = flatten.compact_json(doc, sort_keys=True)
    (engines_dir / "wp_grid.json").write_bytes(raw)

    gz = len(flatten.gz_bytes(raw))
    print(f"  engines/wp_grid.json    raw={len(raw):>9,}  gz={gz:>8,}")
    cal = doc["calibration"]
    print(f"WP calibration: ECE = {cal['ece']}  worst populated decile "
          f"|pred-actual| = {cal['worst_populated_bin_abs_dev']}  (n={cal['n']:,})")
    anc = cal["era_anchor"]
    print(f"anchor 9+RPO ~60 balls left: 2008-2012 "
          f"{anc['ipl_2008_2012']['win_rate']} -> 2023-2026 "
          f"{anc['ipl_2023_2026']['win_rate']}")
    dfd = doc["first_innings_defend"]["surfaces"]
    # 170-189 bucket indices
    labels = _defend_bucket_labels()
    i170 = labels.index("170-179")
    i180 = labels.index("180-189")
    for era in ("ipl 2008-2010", "ipl 2023-2026"):
        row = dfd[era]
        n1 = row["n"][i170] + row["n"][i180]
        # bat-first win% across 170-189 (evidence-weighted over the two buckets)
        p = (row["p_batfirst_win"][i170] * row["n"][i170]
             + row["p_batfirst_win"][i180] * row["n"][i180]) / n1 if n1 else None
        print(f"  defend 170-189 {era}: {round(p, 3) if p else None} (n={n1})")
    return doc


if __name__ == "__main__":
    main()
