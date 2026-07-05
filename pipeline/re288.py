"""Engine #2 — RE288 run-expectancy surfaces (parallel Python track, R2-R3a).

The cricket RE24: expected first-innings runs STILL TO COME from every
(overs-bowled x wickets-lost) state, rebuilt per era band — the engine that
later powers Chapter 5's linear weights, wicket value and the surface-drift
exhibit, and the Net Session interlude's "expected runs from here" dial.

  * NOT consumed by any R2a scene. This module de-risks R3b: it must clear the
    §5 engine-validation gate (RE-surface monotonicity + calibration sanity
    checks, in tests/test_engines.py) BEFORE any Chapter-5 / interlude
    choreography is authored, so model rework can never invalidate finished
    scene work.

The surface
-----------
State = (o, w) where o = overs bowled (0..19, sampled at each over START) and
w = wickets fallen (0..9). For every first innings we walk the over boundaries;
at the start of over o (if the innings reached it) we record the runs already
scored and wickets already down, and the OUTCOME runs-to-come = final innings
total - runs so far (runs.total, i.e. every run the batting side banked,
extras included — this is expected TEAM runs remaining, the quantity linear
weights and wicket value difference against). All-out innings contribute states
only for the overs they actually reached (natural right-censoring); D/L matches
and super overs are excluded.

  RE[o][w] = mean runs-to-come over first innings that passed through (o, w).

Smoothing + monotonicity (stdlib, deterministic — a lookup, never a live fit).
Raw per-cell means are noisy in the corners (many wickets very early, no
wickets very late), so each surface is passed through a weighted 2-D isotonic
regression (alternating pool-adjacent-violators down the wickets axis and the
overs axis to a fixpoint). This both fills empty/thin cells by interpolation
(zero-weight points inherit their block value) and GUARANTEES the two physical
monotonicities the gate checks:

  * runs-to-come is NON-INCREASING in wickets fallen (fewer wickets in hand at
    the same over -> fewer runs left);
  * runs-to-come is NON-INCREASING in overs bowled (fewer balls remaining at
    the same wicket count -> fewer runs left).

Weighted PAV preserves each block's weighted mean, so the surface stays
calibrated (pooled predicted runs-to-come == pooled actual, per era) while
becoming smooth and monotone.

Era bands (same as par.py / scenes.py): IPL 2008-2010, 2011-2015, 2016-2019,
2020-2022, 2023-2026, plus a single POOLED WPL surface (2023-2026). The WPL
surface carries a per-cell minimum-evidence mask: cells built from fewer than
MASK_MIN_N first-innings observations are flagged masked=1 so a consumer can
render them hatched ("not enough WPL cricket yet") rather than present an
imputation as a finding.

Emitted compact to engines/re288.json. Stdlib only. Byte-deterministic
(key-sorted compact JSON). Writes only under web/static/data/engines/ — it
never touches an R1 or R2a artifact.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten

ENGINES_DIR = canon.OUT_ROOT / "engines"

N_OVERS = 20   # over-start states o = 0..19
N_WKTS = 10    # wickets fallen w = 0..9

# Era bands: label -> (lo, hi) inclusive. IPL bands match par.IPL_ERA_BANDS.
IPL_ERA_BANDS = (
    ("2008-2010", 2008, 2010),
    ("2011-2015", 2011, 2015),
    ("2016-2019", 2016, 2019),
    ("2020-2022", 2020, 2022),
    ("2023-2026", 2023, 2026),
)

# WPL: one pooled surface across all four seasons; cells thinner than this get
# the minimum-evidence mask (young-league honesty, not a smoothing artifact).
MASK_MIN_N = 15

# Isotonic fixpoint controls.
ISO_MAX_ITERS = 100
ISO_EPS = 1e-9


# ---------------------------------------------------------------------------
# Corpus pass: raw (o, w) -> [sum runs-to-come, count] per surface
# ---------------------------------------------------------------------------


def _band_of(season: int) -> str | None:
    for label, lo, hi in IPL_ERA_BANDS:
        if lo <= season <= hi:
            return label
    return None


def build(data_root: Path = canon.DATA_ROOT):
    """One chronological pass. Returns raw[surface_key][(o, w)] = [runs, n]
    where surface_key is an IPL era-band label or 'wpl'."""
    raw: dict = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        if canon.is_dl(info):
            continue  # rain-shortened first innings would mis-state runs-to-come
        season = canon.canon_season(info)
        if league == "ipl":
            surface = _band_of(season)
        else:
            surface = "wpl"
        if surface is None:
            continue

        # first non-super-over innings only
        first = None
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            first = innings
            break
        if first is None:
            continue

        # replay to get (runs, wkts) at each over start and the final total
        runs = 0
        wkts = 0
        over_start = {}  # o -> (runs_before_over, wkts_before_over)
        for over in first["overs"]:
            o = over["over"]
            if o < N_OVERS:
                over_start[o] = (runs, wkts)
            for dl in over["deliveries"]:
                runs += dl["runs"]["total"]
                if "wickets" in dl:
                    wkts += len(dl["wickets"])
        final_total = runs

        cells = raw[surface]
        for o, (rs, wk) in over_start.items():
            if wk >= N_WKTS:
                continue  # all out mid-over recorded at next over start; guard
            c = cells[(o, wk)]
            c[0] += final_total - rs
            c[1] += 1

    return raw


# ---------------------------------------------------------------------------
# Weighted isotonic (pool-adjacent-violators), monotone NON-INCREASING
# ---------------------------------------------------------------------------


def _pav_decreasing(values, weights):
    """Weighted isotonic regression enforcing a NON-INCREASING sequence.

    Standard pool-adjacent-violators: append each point as its own block, then
    merge left while the previous block's weighted mean is below the current
    one's (a violation of decreasing order). All weights are strictly positive
    (empty grid cells enter with an epsilon weight and an imputed seed value —
    see `_surface`), so every block mean sum(w*v)/sum(w) is well defined and
    the fitted value of a near-empty cell is simply its block's mean (imputation
    by monotonicity). Returns a new list of fitted values, same length.
    """
    n = len(values)
    if n == 0:
        return []
    blk_wv = []   # sum(w*v) per block
    blk_w = []    # sum(w) per block
    blk_len = []  # points per block
    blk_mean = []
    for v, w in zip(values, weights):
        blk_wv.append(v * w)
        blk_w.append(w)
        blk_len.append(1)
        blk_mean.append(v)
        # merge while previous block mean < this block mean (decreasing broken)
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


def _isotonize(mean, weight):
    """Alternate decreasing-PAV down each wicket-column (over axis) and each
    over-row (wicket axis) until a fixpoint. Returns the jointly monotone,
    weight-preserving surface as a 2-D list [o][w].

    mean/weight are 2-D lists [o][w] (N_OVERS x N_WKTS)."""
    surf = [row[:] for row in mean]
    for _ in range(ISO_MAX_ITERS):
        max_delta = 0.0
        # (1) each wicket column w: decreasing in o (0..N_OVERS-1)
        for w in range(N_WKTS):
            col = [surf[o][w] for o in range(N_OVERS)]
            wt = [weight[o][w] for o in range(N_OVERS)]
            fit = _pav_decreasing(col, wt)
            for o in range(N_OVERS):
                max_delta = max(max_delta, abs(fit[o] - surf[o][w]))
                surf[o][w] = fit[o]
        # (2) each over row o: decreasing in w (0..N_WKTS-1)
        for o in range(N_OVERS):
            row = surf[o][:]
            wt = [weight[o][w] for w in range(N_WKTS)]
            fit = _pav_decreasing(row, wt)
            for w in range(N_WKTS):
                max_delta = max(max_delta, abs(fit[w] - surf[o][w]))
                surf[o][w] = fit[w]
        if max_delta < ISO_EPS:
            break
    return surf


# ---------------------------------------------------------------------------
# Surface assembly
# ---------------------------------------------------------------------------


# Epsilon weight for an empty grid cell: large enough to keep every block mean
# well defined, small enough that a single real observation dominates it.
EMPTY_W = 1e-6


def _surface(cells: dict):
    """cells[(o, w)] = [sum, n] -> (fitted[o][w], counts[o][w], raw_mean[o][w]).

    Observed cells enter isotonic regression at their raw mean with weight = n.
    Empty cells are seeded by monotone imputation (inherit the same-over /
    one-fewer-wicket value, else the previous-over / same-wicket value, else the
    global fallback) and enter with a negligible EMPTY_W weight, so they take
    their block's fitted value without perturbing observed cells.
    """
    raw_mean = [[0.0] * N_WKTS for _ in range(N_OVERS)]
    counts = [[0] * N_WKTS for _ in range(N_OVERS)]
    for o in range(N_OVERS):
        for w in range(N_WKTS):
            s, n = cells.get((o, w), (0.0, 0))
            counts[o][w] = n
            raw_mean[o][w] = (s / n) if n else 0.0

    # global fallback = the largest observed cell mean (the (0,0) corner, i.e.
    # the era's average innings total) so a wholly-empty top row imputes high.
    fallback = 0.0
    for o in range(N_OVERS):
        for w in range(N_WKTS):
            if counts[o][w] and raw_mean[o][w] > fallback:
                fallback = raw_mean[o][w]

    seed = [[0.0] * N_WKTS for _ in range(N_OVERS)]
    weight = [[0.0] * N_WKTS for _ in range(N_OVERS)]
    for o in range(N_OVERS):          # ascending so (o-1, w) already seeded
        for w in range(N_WKTS):       # ascending so (o, w-1) already seeded
            if counts[o][w]:
                seed[o][w] = raw_mean[o][w]
                weight[o][w] = float(counts[o][w])
            else:
                if w > 0:
                    seed[o][w] = seed[o][w - 1]      # one fewer wicket >= this
                elif o > 0:
                    seed[o][w] = seed[o - 1][w]      # one fewer over >= this
                else:
                    seed[o][w] = fallback            # (0,0) with no data
                weight[o][w] = EMPTY_W

    fitted = _isotonize(seed, weight)
    return fitted, counts, raw_mean


def _calibration(fitted, counts, raw_mean) -> dict:
    """Pooled predicted vs actual runs-to-come (weighted by cell n), and the
    per-over reliability rows. Weighted PAV keeps these near-equal."""
    tot_pred = 0.0
    tot_act = 0.0
    tot_n = 0
    per_over = []
    for o in range(N_OVERS):
        opred = oact = 0.0
        on = 0
        for w in range(N_WKTS):
            n = counts[o][w]
            if not n:
                continue
            opred += fitted[o][w] * n
            oact += raw_mean[o][w] * n
            on += n
        if on:
            per_over.append({
                "over": o,
                "n": on,
                "pred_rtc": round(opred / on, 3),
                "actual_rtc": round(oact / on, 3),
            })
            tot_pred += opred
            tot_act += oact
            tot_n += on
    return {
        "pooled_n": tot_n,
        "pooled_pred_rtc": round(tot_pred / tot_n, 4) if tot_n else None,
        "pooled_actual_rtc": round(tot_act / tot_n, 4) if tot_n else None,
        "pooled_abs_dev": round(abs(tot_pred - tot_act) / tot_n, 4) if tot_n else None,
        "per_over": per_over,
    }


def build_doc(data_root: Path = canon.DATA_ROOT) -> dict:
    raw = build(data_root)
    surfaces = {}
    order = [label for label, _lo, _hi in IPL_ERA_BANDS] + ["wpl"]
    for key in order:
        cells = raw.get(key, {})
        fitted, counts, raw_mean = _surface(cells)
        surf_key = f"ipl {key}" if key != "wpl" else "wpl 2023-2026"
        entry = {
            "re": [[round(fitted[o][w], 3) for w in range(N_WKTS)]
                   for o in range(N_OVERS)],
            "n": [[counts[o][w] for w in range(N_WKTS)] for o in range(N_OVERS)],
            "calibration": _calibration(fitted, counts, raw_mean),
        }
        if key == "wpl":
            entry["masked"] = [
                [1 if counts[o][w] < MASK_MIN_N else 0 for w in range(N_WKTS)]
                for o in range(N_OVERS)
            ]
            entry["mask_min_n"] = MASK_MIN_N
        surfaces[surf_key] = entry

    return {
        "engine": "2 — RE288 run-expectancy surfaces",
        "consumed_by": "R3b (Ch 5 linear weights / wicket value / surface drift; Net Session 'expected runs from here' dial). Not consumed by any R2a scene.",
        "state": {
            "o": "overs bowled, 0..19 (state sampled at each over START)",
            "w": "wickets fallen, 0..9",
            "value": "RE[o][w] = expected first-innings runs STILL TO COME (runs.total, extras included) from state (o, w)",
        },
        "method": (
            "First innings only (non-D/L, super overs excluded). Per era band, "
            "raw cell mean runs-to-come is passed through a weighted 2-D "
            "isotonic regression (alternating decreasing pool-adjacent-violators "
            "on the wickets axis and the overs axis to a fixpoint), which fills "
            "thin/empty corner cells by interpolation and guarantees runs-to-come "
            "is non-increasing in both wickets fallen and overs bowled while "
            "preserving each block's weighted mean (calibration-preserving). A "
            "lookup, not a live fit."
        ),
        "monotonicity": (
            "RE[o][w] >= RE[o][w+1] (more wickets down -> fewer runs left) and "
            "RE[o][w] >= RE[o+1][w] (fewer balls remaining -> fewer runs left), "
            "for every surface. Asserted in tests/test_engines.py."
        ),
        "era_bands": [f"ipl {label}" for label, _l, _h in IPL_ERA_BANDS]
        + ["wpl 2023-2026 (pooled, evidence-masked)"],
        "wpl_evidence_mask": (
            f"WPL cells with fewer than {MASK_MIN_N} first-innings observations "
            "carry masked=1 so a consumer renders them hatched rather than "
            "presenting an imputation as a finding."
        ),
        "n_overs": N_OVERS,
        "n_wickets": N_WKTS,
        "surfaces": surfaces,
    }


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    doc = build_doc()
    engines_dir = out_root / "engines"
    engines_dir.mkdir(parents=True, exist_ok=True)
    raw = flatten.compact_json(doc, sort_keys=True)
    (engines_dir / "re288.json").write_bytes(raw)

    gz = len(flatten.gz_bytes(raw))
    print(f"  engines/re288.json      raw={len(raw):>9,}  gz={gz:>8,}")
    early = doc["surfaces"]["ipl 2008-2010"]["re"][10][3]
    recent = doc["surfaces"]["ipl 2023-2026"]["re"][10][3]
    print(f"RE(10 overs, 3 down): ipl 2008-2010 {early} -> ipl 2023-2026 {recent}")
    for key in ("ipl 2008-2010", "ipl 2023-2026", "wpl 2023-2026"):
        cal = doc["surfaces"][key]["calibration"]
        print(f"  {key:16s} RE(0,0)={doc['surfaces'][key]['re'][0][0]:>6}  "
              f"pooled |pred-actual|={cal['pooled_abs_dev']}")
    return doc


if __name__ == "__main__":
    main()
