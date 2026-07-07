"""R4a — Chapter 6 "Two Dialects" (IPL x WPL, beside the path not on it).

The one authoritative corpus pass for Chapter 6 (separate from scenes.py's
Ch1-4 build and ch5.py so the R1-R3 scene bytes stay byte-identical) plus the
pure-Python linear algebra the Season Constellation Map needs. Stdlib only, no
numpy; byte-deterministic (compact JSON, sorted keys, fixed-decimal rounding).

Emits web/static/data/scenes/ch6.json. The controlling morph reuses the
existing per-point group_ids.u16 (each ball already carries its season-group
0-22); Ch 6 ships no new per-point buffer — only a tiny star table per phase.

The house framing rule made literal: the WPL is NEVER "behind". Every WPL
season-star sits nearest IPL 2008 by ball-by-ball OUTCOME MIX while scoring at
IPL-2022's run rate — both true at once — so it lands BESIDE the IPL path, not
on it. A different dialect of the same language.

What Ch6 puts on screen, all recounted by tests/test_r4a.py against an
independent recompute:

  constellation   the hero: each of the 23 season-groups placed by the actual
                  distance between its per-ball outcome distribution and every
                  other's. Categories (attrs.u8 convention, wicket takes
                  precedence): dot / single / two-or-three / four / six /
                  wicket / extras. Per group AND per phase (powerplay 1-6 /
                  middle 7-15 / death 16-20). 23x23 pairwise Jensen-Shannon
                  distance -> classical MDS (double-centre + Jacobi
                  eigensolver) -> the all-phase MASTER star layout; each
                  per-phase layout Procrustes-aligned (2x2 SVD via the
                  orthogonal/polar factor, reflection allowed, uniform scale)
                  to the master so the WPL never flips sides on a phase toggle.
                  Emits star (x,y) per phase (normalised to a stable box), the
                  IPL chronological worm order, each WPL star's nearest-IPL
                  neighbour per phase (dotted threads), and the two-truths pair
                  (outcome-mix twin vs run-rate twin) per WPL season.
  maturity_clock  RR by league-year, both leagues (RR = ALL runs / legal
                  balls); the validated headline WPL yr4 8.54 == IPL yr15 2022.
  run_dna         run-source composition per league x era (four 46.8 vs 33.9,
                  six 15.5 vs 29.0, plus singles/twos/threes) — the helix.
  stumping        stumped % of dismissals per league-season (WPL 5.2-7.9 vs
                  IPL 2026 1.4) + bowled/lbw + caught shares.
  photo_finish    thriller rate per league (WPL 24.1 the tightest in the
                  dataset; IPL ~16-17). Defended by <=5 runs OR chased with
                  <=3 balls to spare; ties, D/L and no-results excluded.
  batting_ladder  run share by batting position 1-11, league x era, plus the
                  Batting Depth Ledger footnote (WPL 2025 pos-7+ 15.3%).
  payoff          the sister-franchise cards (MI/RCB/DC/GT <-> their WPL
                  sisters), each WPL team's nearest IPL season-star by style,
                  the five shared grounds, and the designed no-sister state.
  footnotes       Star Gravity / Gini threshold sensitivity, Competitive
                  Balance normalised win-HHI + distinct champions, Powerplay
                  Fear Index, Twos Culture.
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

SCENES_DIR = canon.OUT_ROOT / "scenes"

# --- outcome categories (attrs.u8 convention; wicket takes precedence) --------
CATEGORIES = ("dot", "single", "two_or_three", "four", "six", "wicket", "extras")
DOT, SINGLE, TWO_OR_THREE, FOUR, SIX, WICKET, EXTRAS = range(7)
NCAT = 7

# --- phase views: 0 all, 1 powerplay (overs 1-6), 2 middle (7-15), 3 death ----
PHASE_VIEWS = ("all", "powerplay", "middle", "death")

# --- era bands (shared with the rest of the piece) ----------------------------
IPL_ERA_BANDS = (
    ("ipl", "2008-2010", 2008, 2010),
    ("ipl", "2011-2015", 2011, 2015),
    ("ipl", "2016-2019", 2016, 2019),
    ("ipl", "2020-2022", 2020, 2022),
    ("ipl", "2023-2026", 2023, 2026),
)
WPL_BAND = ("wpl", "2023-2026", 2023, 2026)
ERA_BANDS = IPL_ERA_BANDS + (WPL_BAND,)
BAND_KEYS = tuple(f"{lg} {label}" for lg, label, _lo, _hi in ERA_BANDS)

RETIRED_KINDS = frozenset({"retired hurt", "retired out"})

# The 23 season-groups in group_ids.u16 order (gi 0-18 IPL 2008-2026, 19-22 WPL
# 2023-2026). This IS groups.json's order — the render maps a ball's group id
# straight into the emitted star table.
GROUPS = [("ipl", s) for s in canon.IPL_SEASONS] + [
    ("wpl", s) for s in canon.WPL_SEASONS
]
GI_OF = {k: i for i, k in enumerate(GROUPS)}
N_GROUPS = len(GROUPS)  # 23
IPL_GIS = [i for i, (lg, _s) in enumerate(GROUPS) if lg == "ipl"]
WPL_GIS = [i for i, (lg, _s) in enumerate(GROUPS) if lg == "wpl"]

# Sister franchises (blueprint Ch6): shared-city pairs, IPL id -> WPL id.
# Only these four are designated sisters; UP Warriorz and the six sisterless
# IPL franchises get the designed no-sister state.
SISTER_PAIRS = {
    ("ipl", "Mumbai Indians"): ("wpl", "Mumbai Indians", "Mumbai"),
    ("ipl", "Royal Challengers Bengaluru"): (
        "wpl",
        "Royal Challengers Bengaluru",
        "Bengaluru",
    ),
    ("ipl", "Delhi Capitals"): ("wpl", "Delhi Capitals", "Delhi"),
    ("ipl", "Gujarat Titans"): ("wpl", "Gujarat Giants", "Gujarat"),
}


def band_key(league: str, season: int) -> str:
    if league == "wpl":
        return "wpl " + WPL_BAND[1]
    for _lg, label, lo, hi in IPL_ERA_BANDS:
        if lo <= season <= hi:
            return "ipl " + label
    raise KeyError(f"season {season} outside every IPL era band")


def phase_of(over_index: int) -> int:
    """0 powerplay (overs 1-6) / 1 middle (7-15) / 2 death (16-20)."""
    if over_index < 6:
        return 0
    if over_index < 15:
        return 1
    return 2


def outcome_category(dl: dict) -> int:
    """The 7-way partition. A wicket ball is 'wicket' regardless of runs (so
    the buckets are mutually exclusive); otherwise the attrs.u8 outcome class
    (dot / single / two-or-three / four / six / other-scoring==extras)."""
    if dl.get("wickets"):
        return WICKET
    rb = dl["runs"]["batter"]
    if rb == 0 and dl["runs"]["total"] == 0:
        return DOT
    if rb == 1:
        return SINGLE
    if rb in (2, 3):
        return TWO_OR_THREE
    if rb == 4:
        return FOUR
    if rb == 6:
        return SIX
    return EXTRAS  # extras-only scoring balls + the freak batter-5s


# ---------------------------------------------------------------------------
# Pure-Python linear algebra (no numpy) — Jacobi eig, classical MDS, Procrustes
# ---------------------------------------------------------------------------


def jacobi_eigen(matrix, max_sweeps: int = 200, tol: float = 1e-18):
    """Cyclic Jacobi eigendecomposition of a symmetric n x n matrix.

    Returns (eigenvalues, eigenvectors) with eigenvectors as COLUMNS
    (eigenvectors[i][k] = i-th component of the k-th eigenvector). Deterministic
    (fixed sweep order, IEEE doubles), which is what makes the whole scene
    byte-reproducible."""
    n = len(matrix)
    a = [list(map(float, row)) for row in matrix]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _sweep in range(max_sweeps):
        off = 0.0
        for p in range(n):
            for q in range(p + 1, n):
                off += a[p][q] * a[p][q]
        if off <= tol:
            break
        for p in range(n):
            for q in range(p + 1, n):
                apq = a[p][q]
                if apq == 0.0:
                    continue
                app, aqq = a[p][p], a[q][q]
                tau = (aqq - app) / (2.0 * apq)
                if tau >= 0.0:
                    t = 1.0 / (tau + math.sqrt(1.0 + tau * tau))
                else:
                    t = -1.0 / (-tau + math.sqrt(1.0 + tau * tau))
                c = 1.0 / math.sqrt(1.0 + t * t)
                s = t * c
                for i in range(n):
                    aip, aiq = a[i][p], a[i][q]
                    a[i][p] = c * aip - s * aiq
                    a[i][q] = s * aip + c * aiq
                for i in range(n):
                    api, aqi = a[p][i], a[q][i]
                    a[p][i] = c * api - s * aqi
                    a[q][i] = s * api + c * aqi
                for i in range(n):
                    vip, viq = v[i][p], v[i][q]
                    v[i][p] = c * vip - s * viq
                    v[i][q] = s * vip + c * viq
    eigenvalues = [a[i][i] for i in range(n)]
    return eigenvalues, v


def eig_sorted_desc(matrix):
    """Eigenpairs [(eigenvalue, eigenvector_list), ...] sorted by eigenvalue
    descending, then by a deterministic tie-break on the vector."""
    vals, vecs = jacobi_eigen(matrix)
    n = len(matrix)
    pairs = []
    for k in range(n):
        vec = [vecs[i][k] for i in range(n)]
        pairs.append((vals[k], vec))
    pairs.sort(key=lambda pv: (-pv[0], pv[1]))
    return pairs


def classical_mds_2d(dist):
    """Classical (Torgerson) MDS to 2D. dist is an n x n distance matrix.

    Returns (coords, eigenvalues) where coords[i] = [x, y]. Double-centre the
    squared-distance matrix B = -0.5 J D2 J, eigendecompose, take the top two
    eigenvectors scaled by sqrt(eigenvalue)."""
    n = len(dist)
    d2 = [[dist[i][j] ** 2 for j in range(n)] for i in range(n)]
    row_mean = [sum(d2[i]) / n for i in range(n)]
    grand = sum(row_mean) / n
    b = [
        [-0.5 * (d2[i][j] - row_mean[i] - row_mean[j] + grand) for j in range(n)]
        for i in range(n)
    ]
    pairs = eig_sorted_desc(b)
    coords = [[0.0, 0.0] for _ in range(n)]
    for k in range(2):
        val, vec = pairs[k]
        scale = math.sqrt(val) if val > 0 else 0.0
        for i in range(n):
            coords[i][k] = scale * vec[i]
    return coords, [pairs[k][0] for k in range(n)]


def _centroid(points):
    n = len(points)
    return [sum(p[0] for p in points) / n, sum(p[1] for p in points) / n]


def _mat2_mul(a, b):
    return [
        [a[0][0] * b[0][0] + a[0][1] * b[1][0], a[0][0] * b[0][1] + a[0][1] * b[1][1]],
        [a[1][0] * b[0][0] + a[1][1] * b[1][0], a[1][0] * b[0][1] + a[1][1] * b[1][1]],
    ]


def procrustes_align(source, target):
    """Orthogonal Procrustes (rotation + reflection + uniform scale) mapping
    `source` onto `target`; both are n x 2 point lists.

    The optimal orthogonal factor Q of the 2x2 cross-covariance M = Xc^T Yc is
    its polar factor Q = M (M^T M)^-1/2 (== U V^T from M = U S V^T, reflection
    allowed because we never force det Q = +1). Uniform scale s = tr(S) /
    ||Xc||_F^2. Returns (aligned_points, disparity, disparity_raw)."""
    n = len(source)
    cx, cy = _centroid(source), _centroid(target)
    xc = [[p[0] - cx[0], p[1] - cx[1]] for p in source]
    yc = [[p[0] - cy[0], p[1] - cy[1]] for p in target]
    # M = Xc^T Yc  (2x2)
    m = [[0.0, 0.0], [0.0, 0.0]]
    for i in range(n):
        for r in range(2):
            for c in range(2):
                m[r][c] += xc[i][r] * yc[i][c]
    # M^T M (2x2 symmetric)
    mtm = [
        [m[0][0] * m[0][0] + m[1][0] * m[1][0], m[0][0] * m[0][1] + m[1][0] * m[1][1]],
        [m[0][1] * m[0][0] + m[1][1] * m[1][0], m[0][1] * m[0][1] + m[1][1] * m[1][1]],
    ]
    pairs = eig_sorted_desc(mtm)
    sigmas = [math.sqrt(max(pairs[k][0], 0.0)) for k in range(2)]
    # inv_sqrt(M^T M) = V diag(1/sigma) V^T (pseudo-inverse guard on sigma==0)
    v = [[pairs[0][1][r], pairs[1][1][r]] for r in range(2)]  # columns = eigvecs
    inv_sig = [[0.0, 0.0], [0.0, 0.0]]
    for k in range(2):
        if sigmas[k] > 1e-12:
            inv_sig[k][k] = 1.0 / sigmas[k]
    vt = [[v[0][0], v[1][0]], [v[0][1], v[1][1]]]
    inv_sqrt = _mat2_mul(_mat2_mul(v, inv_sig), vt)
    q = _mat2_mul(m, inv_sqrt)  # orthogonal factor (reflection allowed)
    denom = sum(xc[i][0] ** 2 + xc[i][1] ** 2 for i in range(n))
    s = (sigmas[0] + sigmas[1]) / denom if denom > 0 else 1.0
    aligned = []
    for i in range(n):
        x0, x1 = xc[i]
        ax = s * (x0 * q[0][0] + x1 * q[1][0]) + cy[0]
        ay = s * (x0 * q[0][1] + x1 * q[1][1]) + cy[1]
        aligned.append([ax, ay])
    disparity = sum(
        (aligned[i][0] - target[i][0]) ** 2 + (aligned[i][1] - target[i][1]) ** 2
        for i in range(n)
    )
    disparity_raw = sum(
        (source[i][0] - target[i][0]) ** 2 + (source[i][1] - target[i][1]) ** 2
        for i in range(n)
    )
    return aligned, disparity, disparity_raw


# --- Jensen-Shannon (base-2, bounded in [0,1]); distance = sqrt(JSD) ----------


def _kl(p, m):
    total = 0.0
    for pi, mi in zip(p, m):
        if pi > 0.0 and mi > 0.0:
            total += pi * math.log2(pi / mi)
    return total


def js_divergence(p, q):
    m = [(a + b) / 2.0 for a, b in zip(p, q)]
    return 0.5 * _kl(p, m) + 0.5 * _kl(q, m)


def js_distance(p, q):
    return math.sqrt(max(js_divergence(p, q), 0.0))


def normalize(counts):
    s = sum(counts)
    return [c / s for c in counts] if s else [0.0] * NCAT


def dist_matrix(distributions):
    """Full symmetric n x n Jensen-Shannon distance matrix."""
    n = len(distributions)
    d = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            v = js_distance(distributions[i], distributions[j])
            d[i][j] = v
            d[j][i] = v
    return d


def mds_stress(dist, coords):
    """Kruskal-style relative stress of a 2D embedding vs its distance matrix."""
    n = len(dist)
    num = 0.0
    den = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            dhat = math.hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1])
            num += (dhat - dist[i][j]) ** 2
            den += dist[i][j] ** 2
    return math.sqrt(num / den) if den > 0 else 0.0


# ---------------------------------------------------------------------------
# The one corpus pass
# ---------------------------------------------------------------------------


def build_ch6(data_root: Path = canon.DATA_ROOT) -> dict:
    # constellation: dist[gi][view] -> [7] counts
    dist = [[[0] * NCAT for _ in range(4)] for _ in range(N_GROUPS)]
    runs_total = defaultdict(int)  # (lg, ss) -> all runs
    legal = defaultdict(int)  # (lg, ss) -> legal balls
    four_runs = defaultdict(int)
    six_runs = defaultdict(int)
    one_runs = defaultdict(int)
    two_runs = defaultdict(int)
    three_runs = defaultdict(int)
    c1 = defaultdict(int)  # count of singles
    c2 = defaultdict(int)  # count of twos
    c3 = defaultdict(int)  # count of threes
    dismissals = defaultdict(int)
    stumped = defaultdict(int)
    bowled_lbw = defaultdict(int)
    caught = defaultdict(int)
    runout = defaultdict(int)
    pp_runs = defaultdict(int)
    pp_legal = defaultdict(int)
    pos_runs = defaultdict(int)  # (lg, ss, pos) -> batter runs
    batter_runs = defaultdict(lambda: defaultdict(int))  # (lg, ss) -> {batter: runs}
    batter_balls = defaultdict(lambda: defaultdict(int))
    team_dist = defaultdict(lambda: [0] * NCAT)  # team_id -> [7] all-phase counts
    team_venue = defaultdict(lambda: defaultdict(int))  # team_id -> {venue: matches}
    win_share = defaultdict(lambda: defaultdict(int))  # (lg, ss) -> {team: wins}
    champions = {"ipl": [], "wpl": []}  # [(season, team), ...]
    photo_matches = []  # per-match closeness records
    n_matches = defaultdict(int)

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        gi = GI_OF[(league, season)]
        n_matches[(league, season)] += 1
        venue = canon.canon_venue(info["venue"])
        outcome = info.get("outcome", {})
        result = outcome.get("result")
        by = outcome.get("by", {})
        winner = outcome.get("winner")
        elim = outcome.get("eliminator")
        won_team = (
            canon.canon_team(winner)
            if winner
            else (canon.canon_team(elim) if elim else None)
        )
        if won_team:
            win_share[(league, season)][won_team] += 1
        if flatten.match_stage(info) == "Final" and won_team:
            champions[league].append((season, won_team))
        for tname in info["teams"]:
            tid = canon.team_id(league, canon.canon_team(tname))
            team_venue[tid][venue] += 1

        innings_no = 0
        chase_win_balls = None
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            innings_no += 1
            team_id = canon.team_id(league, canon.canon_team(innings["team"]))
            key = (league, season)
            position = {}
            next_pos = 1
            crun = 0
            cum_legal = 0
            won_ball = None
            target = (
                (innings.get("target") or {}).get("runs") if innings_no == 2 else None
            )
            for over in innings["overs"]:
                ph = phase_of(over["over"])
                for dl in over["deliveries"]:
                    ex = dl.get("extras", {})
                    wide = "wides" in ex
                    noball = "noballs" in ex
                    tot = dl["runs"]["total"]
                    rb = dl["runs"]["batter"]
                    striker = dl["batter"]
                    nonst = dl["non_striker"]
                    if striker not in position:
                        position[striker] = next_pos
                        next_pos += 1
                    if nonst not in position:
                        position[nonst] = next_pos
                        next_pos += 1
                    cat = outcome_category(dl)
                    dist[gi][0][cat] += 1
                    dist[gi][1 + ph][cat] += 1
                    team_dist[team_id][cat] += 1
                    runs_total[key] += tot
                    pos_runs[(league, season, position[striker])] += rb
                    if not wide and not noball:
                        legal[key] += 1
                        cum_legal += 1
                        batter_balls[key][striker] += 1
                        if ph == 0:
                            pp_legal[key] += 1
                    batter_runs[key][striker] += rb
                    if ph == 0:
                        pp_runs[key] += tot
                    if rb == 4:
                        four_runs[key] += 4
                    elif rb == 6:
                        six_runs[key] += 6
                    elif rb == 1:
                        one_runs[key] += 1
                        c1[key] += 1
                    elif rb == 2:
                        two_runs[key] += 2
                        c2[key] += 1
                    elif rb == 3:
                        three_runs[key] += 3
                        c3[key] += 1
                    crun += tot
                    if target is not None and crun >= target and won_ball is None:
                        won_ball = cum_legal
                    for w in dl.get("wickets", []):
                        kind = w["kind"]
                        if kind in RETIRED_KINDS:
                            continue
                        dismissals[key] += 1
                        if kind == "stumped":
                            stumped[key] += 1
                        elif kind in ("bowled", "lbw"):
                            bowled_lbw[key] += 1
                        elif kind == "caught":
                            caught[key] += 1
                        elif kind == "run out":
                            runout[key] += 1
            if innings_no == 2:
                chase_win_balls = won_ball
        photo_matches.append(
            {
                "league": league,
                "season": season,
                "dl": canon.is_dl(info),
                "result": result,
                "by": dict(by),
                "chase_win_balls": chase_win_balls,
            }
        )

    return {
        "dist": dist,
        "runs_total": runs_total,
        "legal": legal,
        "four_runs": four_runs,
        "six_runs": six_runs,
        "one_runs": one_runs,
        "two_runs": two_runs,
        "three_runs": three_runs,
        "c1": c1,
        "c2": c2,
        "c3": c3,
        "dismissals": dismissals,
        "stumped": stumped,
        "bowled_lbw": bowled_lbw,
        "caught": caught,
        "runout": runout,
        "pp_runs": pp_runs,
        "pp_legal": pp_legal,
        "pos_runs": pos_runs,
        "batter_runs": batter_runs,
        "batter_balls": batter_balls,
        "team_dist": {k: v for k, v in team_dist.items()},
        "team_venue": {k: dict(v) for k, v in team_venue.items()},
        "win_share": {k: dict(v) for k, v in win_share.items()},
        "champions": champions,
        "photo_matches": photo_matches,
        "n_matches": n_matches,
    }


# ---------------------------------------------------------------------------
# Rounding helpers
# ---------------------------------------------------------------------------


def r1(x):
    return round(x, 1)


def r2(x):
    return round(x, 2)


def r4(x):
    return round(x, 4)


def r6(x):
    return round(x, 6)


# ---------------------------------------------------------------------------
# Constellation embedding
# ---------------------------------------------------------------------------


def group_distributions(acc):
    """distributions[view][gi] = probability vector; view in PHASE_VIEWS."""
    dist = acc["dist"]
    out = {}
    for vi, view in enumerate(PHASE_VIEWS):
        out[view] = [normalize(dist[g][vi]) for g in range(N_GROUPS)]
    return out


def build_embedding(acc):
    """Master (all-phase) MDS layout + Procrustes-aligned per-phase layouts,
    sign-canonicalised and normalised into a stable [-1, 1] box."""
    dists = group_distributions(acc)
    dmats = {view: dist_matrix(dists[view]) for view in PHASE_VIEWS}
    raw = {}
    stress = {}
    for view in PHASE_VIEWS:
        coords, _ev = classical_mds_2d(dmats[view])
        raw[view] = coords
        stress[view] = mds_stress(dmats[view], coords)

    master = [row[:] for row in raw["all"]]
    # Deterministic sign canonicalisation of the master: axis 0 flows early ->
    # late IPL (2026 to the right of 2008), axis 1 puts the WPL cluster on the
    # positive-y side. Both are reflections, to which MDS is invariant.
    gi_08, gi_26 = GI_OF[("ipl", 2008)], GI_OF[("ipl", 2026)]
    if master[gi_26][0] < master[gi_08][0]:
        for row in master:
            row[0] = -row[0]
    wpl_y = sum(master[g][1] for g in WPL_GIS) / len(WPL_GIS)
    if wpl_y < 0:
        for row in master:
            row[1] = -row[1]

    aligned = {"all": master}
    disparity = {}
    disparity_raw = {}
    for view in ("powerplay", "middle", "death"):
        al, disp, disp_raw = procrustes_align(raw[view], master)
        aligned[view] = al
        disparity[view] = disp
        disparity_raw[view] = disp_raw

    # One global scale over every layout so stars sit in a stable box and move
    # minimally & coherently between phase toggles.
    scale = 0.0
    for view in PHASE_VIEWS:
        for x, y in aligned[view]:
            scale = max(scale, abs(x), abs(y))
    if scale == 0.0:
        scale = 1.0
    stars = {
        view: [[r4(x / scale), r4(y / scale)] for x, y in aligned[view]]
        for view in PHASE_VIEWS
    }
    return dists, dmats, stars, stress, disparity, disparity_raw


def nearest_ipl(dists, view, wpl_gi):
    """(nearest IPL gi, distance) for a WPL group in a given phase view."""
    best_gi, best_d = None, None
    p = dists[view][wpl_gi]
    for ig in IPL_GIS:
        d = js_distance(p, dists[view][ig])
        if best_d is None or d < best_d:
            best_gi, best_d = ig, d
    return best_gi, best_d


def season_rr(acc, league, season):
    key = (league, season)
    return 6.0 * acc["runs_total"][key] / acc["legal"][key]


def constellation_section(acc):
    dists, dmats, stars, stress, disparity, disparity_raw = build_embedding(acc)

    groups = []
    for gi, (lg, ss) in enumerate(GROUPS):
        six_ct = acc["dist"][gi][0][SIX]
        groups.append(
            {
                "gi": gi,
                "league": lg,
                "season": ss,
                "label": f"{lg.upper()} {ss}",
                "rr": r2(season_rr(acc, lg, ss)),
                "sixes_per_100_legal": r2(100.0 * six_ct / acc["legal"][(lg, ss)]),
            }
        )

    # WPL threads: nearest IPL neighbour per phase (dotted threads) + the two
    # truths at once (outcome-mix twin vs run-rate twin) on the all-phase view.
    threads = {}
    for view in PHASE_VIEWS:
        rows = []
        for wg in WPL_GIS:
            ig, d = nearest_ipl(dists, view, wg)
            rows.append(
                {
                    "wpl_gi": wg,
                    "wpl_season": GROUPS[wg][1],
                    "nearest_ipl_gi": ig,
                    "nearest_ipl_season": GROUPS[ig][1],
                    "distance": r4(d),
                }
            )
        threads[view] = rows

    two_truths = []
    for wg in WPL_GIS:
        wpl_season = GROUPS[wg][1]
        mix_gi, mix_d = nearest_ipl(dists, "all", wg)
        wpl_rr = season_rr(acc, "wpl", wpl_season)
        rate_gi, rate_gap = None, None
        for ig in IPL_GIS:
            gap = abs(season_rr(acc, "ipl", GROUPS[ig][1]) - wpl_rr)
            if rate_gap is None or gap < rate_gap:
                rate_gi, rate_gap = ig, gap
        two_truths.append(
            {
                "wpl_season": wpl_season,
                "wpl_rr": r2(wpl_rr),
                "outcome_mix_twin": {
                    "ipl_season": GROUPS[mix_gi][1],
                    "distance": r4(mix_d),
                },
                "run_rate_twin": {
                    "ipl_season": GROUPS[rate_gi][1],
                    "ipl_rr": r2(season_rr(acc, "ipl", GROUPS[rate_gi][1])),
                    "rr_gap": r2(rate_gap),
                },
            }
        )

    distributions = {
        view: [[r6(x) for x in dists[view][g]] for g in range(N_GROUPS)]
        for view in PHASE_VIEWS
    }
    validation = {
        "mds_stress": {v: r4(stress[v]) for v in PHASE_VIEWS},
        "procrustes_disparity": {v: r6(disparity[v]) for v in disparity},
        "procrustes_disparity_raw": {v: r6(disparity_raw[v]) for v in disparity_raw},
        "all_wpl_nearest_is_2008": all(
            GROUPS[nearest_ipl(dists, "all", wg)[0]][1] == 2008 for wg in WPL_GIS
        ),
    }
    return {
        "categories": list(CATEGORIES),
        "phase_views": list(PHASE_VIEWS),
        "phase_overs": {
            "powerplay": [1, 6],
            "middle": [7, 15],
            "death": [16, 20],
        },
        "groups": groups,
        "stars": stars,
        "ipl_worm": IPL_GIS,
        "wpl_gis": WPL_GIS,
        "wpl_threads": threads,
        "two_truths": two_truths,
        "distributions": distributions,
        "validation": validation,
        "method": (
            "Each of the 23 season-groups is placed by the Jensen-Shannon "
            "distance (sqrt of the base-2 JS divergence) between its per-ball "
            "outcome distribution over {dot, single, two-or-three, four, six, "
            "wicket, extras} and every other's; a wicket ball counts as "
            "'wicket' regardless of runs. Classical (Torgerson) MDS on the "
            "23x23 distance matrix (double-centred squared distances, Jacobi "
            "eigendecomposition, top-2 eigenvectors scaled by sqrt-eigenvalue) "
            "gives the all-phase MASTER layout. Each per-phase layout "
            "(powerplay 1-6 / middle 7-15 / death 16-20) is embedded the same "
            "way then Procrustes-aligned to the master (2x2 orthogonal/polar "
            "factor, reflection allowed, uniform scale) so the WPL never flips "
            "sides on a phase toggle. Positions are normalised by one global "
            "scale into a stable box and rounded to 4 decimals; the client "
            "interpolates and looks up, never re-embeds."
        ),
        "framing": (
            "Every WPL season-star sits nearest IPL 2008 by ball-by-ball "
            "outcome mix while scoring at IPL 2022's run rate — both true at "
            "once — so the WPL lands beside the IPL path, not on it. A "
            "different dialect of the same language, not an earlier version."
        ),
    }


# ---------------------------------------------------------------------------
# Maturity clock
# ---------------------------------------------------------------------------


def maturity_section(acc):
    ipl_years = list(range(1, len(canon.IPL_SEASONS) + 1))
    wpl_years = list(range(1, len(canon.WPL_SEASONS) + 1))
    ipl_rr = [r2(season_rr(acc, "ipl", 2007 + y)) for y in ipl_years]
    wpl_rr = [r2(season_rr(acc, "wpl", 2022 + y)) for y in wpl_years]
    wpl_y4 = wpl_rr[3]
    ipl_y15 = ipl_rr[14]
    return {
        "ipl": {"league_years": ipl_years, "seasons": list(canon.IPL_SEASONS), "rr": ipl_rr},
        "wpl": {"league_years": wpl_years, "seasons": list(canon.WPL_SEASONS), "rr": wpl_rr},
        "headline": {
            "wpl_year4_rr": wpl_y4,
            "ipl_year15_rr": ipl_y15,
            "ipl_year15_season": 2022,
            "equal": wpl_y4 == ipl_y15,
            "text": (
                "The WPL's year-4 run rate (8.54) is exactly the IPL's "
                "year-15 rate — four seasons to reach what took the men's "
                "league fifteen."
            ),
        },
        "definition": (
            "League year N = the league's N-th season (IPL year 1 = 2008, WPL "
            "year 1 = 2023). RR = all runs (extras included) per 6 legal balls "
            "(wides and no-balls excluded from the denominator)."
        ),
    }


# ---------------------------------------------------------------------------
# Run DNA (the helix)
# ---------------------------------------------------------------------------


def _run_shares(acc, keys):
    total = sum(acc["runs_total"][k] for k in keys)
    if total == 0:
        return None
    return {
        "four": r1(100.0 * sum(acc["four_runs"][k] for k in keys) / total),
        "six": r1(100.0 * sum(acc["six_runs"][k] for k in keys) / total),
        "single": r1(100.0 * sum(acc["one_runs"][k] for k in keys) / total),
        "two": r1(100.0 * sum(acc["two_runs"][k] for k in keys) / total),
        "three": r1(100.0 * sum(acc["three_runs"][k] for k in keys) / total),
    }


def run_dna_section(acc):
    era_keys = {}
    for lg, label, lo, hi in ERA_BANDS:
        era_keys[f"{lg} {label}"] = [(lg, s) for s in range(lo, hi + 1)]
    eras = {bk: _run_shares(acc, keys) for bk, keys in era_keys.items()}
    ipl_modern = _run_shares(acc, [("ipl", s) for s in range(2023, 2027)])
    wpl = _run_shares(acc, [("wpl", s) for s in canon.WPL_SEASONS])
    return {
        "eras": eras,
        "helix": {
            "ipl_modern": ipl_modern,
            "wpl": wpl,
        },
        "headline": {
            "four_share": {"wpl": wpl["four"], "ipl_modern": ipl_modern["four"]},
            "six_share": {"wpl": wpl["six"], "ipl_modern": ipl_modern["six"]},
            "text": (
                "The WPL is four-led: 46.8% of its runs come from fours vs the "
                "modern IPL's 33.9%; its six-share is 15.5% vs 29.0%. A "
                "structurally different scoring engine, not a scaled-down copy."
            ),
        },
        "definition": (
            "Share of ALL runs from each source: four = 4 x (runs.batter==4), "
            "six = 6 x (==6), single/two/three from runs.batter 1/2/3. Modern "
            "IPL = 2023-2026, WPL = 2023-2026."
        ),
    }


# ---------------------------------------------------------------------------
# Stumping signature
# ---------------------------------------------------------------------------


def stumping_section(acc):
    def rows(league, seasons):
        out = []
        for s in seasons:
            key = (league, s)
            tot = acc["dismissals"][key]
            out.append(
                {
                    "season": s,
                    "stumped_pct": r1(100.0 * acc["stumped"][key] / tot) if tot else None,
                    "bowled_lbw_pct": r1(100.0 * acc["bowled_lbw"][key] / tot)
                    if tot
                    else None,
                    "caught_pct": r1(100.0 * acc["caught"][key] / tot) if tot else None,
                    "dismissals": tot,
                }
            )
        return out

    wpl_rows = rows("wpl", canon.WPL_SEASONS)
    wpl_vals = [r["stumped_pct"] for r in wpl_rows]
    ipl_rows = rows("ipl", canon.IPL_SEASONS)
    return {
        "ipl": ipl_rows,
        "wpl": wpl_rows,
        "headline": {
            "wpl_range": [min(wpl_vals), max(wpl_vals)],
            "ipl_2026": next(r["stumped_pct"] for r in ipl_rows if r["season"] == 2026),
            "text": (
                "Stumpings are 5.2-7.9% of WPL dismissals every season vs 1.4% "
                "in IPL 2026 — a genuinely different dismissal ecology, "
                "structurally a spinner's league."
            ),
        },
        "definition": (
            "stumped_pct = wickets of kind 'stumped' / all non-retired "
            "dismissals that season (any kind, run-outs included); "
            "bowled_lbw and caught shares alongside."
        ),
    }


# ---------------------------------------------------------------------------
# Photo-finish / thriller rate
# ---------------------------------------------------------------------------


def _photo_verdict(m):
    """None if the match is excluded (D/L, no-result, or a tie — ties go to a
    super over and are their own category); else True/False."""
    if m["dl"] or m["result"] == "no result" or m["result"] == "tie":
        return None
    by = m["by"]
    if "runs" in by:  # defended
        return by["runs"] <= 5
    if "wickets" in by:  # chased
        wb = m["chase_win_balls"]
        return None if wb is None else (120 - wb) <= 3
    return None


def photo_finish_section(acc):
    def rate(keys):
        ks = set(keys)
        decided = [
            m
            for m in acc["photo_matches"]
            if (m["league"], m["season"]) in ks and _photo_verdict(m) is not None
        ]
        pf = [m for m in decided if _photo_verdict(m)]
        return {
            "photo_finishes": len(pf),
            "decided": len(decided),
            "pct": r1(100.0 * len(pf) / len(decided)) if decided else None,
        }

    ipl_eras = {}
    for _lg, label, lo, hi in IPL_ERA_BANDS:
        ipl_eras[f"ipl {label}"] = rate([("ipl", s) for s in range(lo, hi + 1)])
    per_season = {
        "ipl": {str(s): rate([("ipl", s)]) for s in canon.IPL_SEASONS},
        "wpl": {str(s): rate([("wpl", s)]) for s in canon.WPL_SEASONS},
    }
    wpl_all = rate([("wpl", s) for s in canon.WPL_SEASONS])
    ipl_early = ipl_eras["ipl 2008-2010"]
    ipl_modern = ipl_eras["ipl 2023-2026"]
    return {
        "ipl_eras": ipl_eras,
        "per_season": per_season,
        "wpl_all": wpl_all,
        "headline": {
            "wpl": wpl_all["pct"],
            "ipl_early": ipl_early["pct"],
            "ipl_modern": ipl_modern["pct"],
            "text": (
                "The WPL is the tightest league in the dataset: 24.1% of its "
                "decided matches are photo-finishes vs the IPL's 16-17%."
            ),
        },
        "definition": (
            "A photo-finish = a first-innings defence won by <=5 runs OR a "
            "chase completed with <=3 balls to spare. Denominator = decided "
            "matches; D/L, no-results and ties (which go to a super over) are "
            "excluded. Balls to spare = 120 - legal balls bowled when the "
            "target was reached."
        ),
    }


# ---------------------------------------------------------------------------
# Batting ladder + depth
# ---------------------------------------------------------------------------

LADDER_MAX_POS = 11


def batting_ladder_section(acc):
    pos_runs = acc["pos_runs"]

    def ladder(keys):
        rungs = [0] * (LADDER_MAX_POS + 1)  # index 1..11 (11 = 11+)
        for (lg, ss, pos), r in pos_runs.items():
            if (lg, ss) in keys:
                p = min(pos, LADDER_MAX_POS)
                rungs[p] += r
        total = sum(rungs)
        return [r1(100.0 * rungs[p] / total) if total else 0.0 for p in range(1, LADDER_MAX_POS + 1)]

    bands = {}
    for lg, label, lo, hi in ERA_BANDS:
        keys = {(lg, s) for s in range(lo, hi + 1)}
        bands[f"{lg} {label}"] = ladder(keys)

    def depth(keys):
        total = sum(r for (lg, ss, _p), r in pos_runs.items() if (lg, ss) in keys)
        tail = sum(
            r for (lg, ss, p), r in pos_runs.items() if (lg, ss) in keys and p >= 7
        )
        return r1(100.0 * tail / total) if total else None

    depth_seasons = {
        "ipl": {str(s): depth({("ipl", s)}) for s in canon.IPL_SEASONS},
        "wpl": {str(s): depth({("wpl", s)}) for s in canon.WPL_SEASONS},
    }
    return {
        "positions": list(range(1, LADDER_MAX_POS + 1)),
        "position_labels": [str(p) if p < LADDER_MAX_POS else "11+" for p in range(1, LADDER_MAX_POS + 1)],
        "bands": bands,
        "depth": {
            "per_season": depth_seasons,
            "ipl_early_pooled": depth({("ipl", s) for s in (2008, 2009, 2010)}),
            "ipl_modern_pooled": depth({("ipl", s) for s in range(2023, 2027)}),
            "wpl_pooled": depth({("wpl", s) for s in canon.WPL_SEASONS}),
            "headline": {
                "wpl_2025_pos7plus": depth({("wpl", 2025)}),
                "text": (
                    "WPL 2025 positions 7+ scored 15.3% of all runs, the "
                    "highest single season in either league — opportunity-"
                    "driven (more collapses force them to bat), not a claim of "
                    "skill parity."
                ),
            },
        },
        "definition": (
            "Batting position from first-appearance order per innings "
            "(super overs excluded); run share = batter runs at that position "
            "/ all batter runs. Positions 11+ fold into rung 11. Depth = "
            "position-7+ run share."
        ),
    }


# ---------------------------------------------------------------------------
# Footnote layer
# ---------------------------------------------------------------------------


def _gini(values):
    vals = sorted(values)
    n = len(vals)
    s = sum(vals)
    if n == 0 or s == 0:
        return 0.0
    cum = sum(i * v for i, v in enumerate(vals, 1))
    return (2.0 * cum) / (n * s) - (n + 1.0) / n


def _norm_hhi(shares):
    n = len(shares)
    total = sum(shares)
    if total == 0 or n <= 1:
        return 0.0
    hhi = sum((v / total) ** 2 for v in shares)
    return (hhi - 1.0 / n) / (1.0 - 1.0 / n)


def footnotes_section(acc):
    # Star Gravity / Gini threshold sensitivity (WPL). Per-season is the honest
    # cut; pooling across seasons inflates it (a one-season player looks poorer
    # against the multi-season stars).
    star_gravity = {"ipl": {}, "wpl": {}}
    for lg, seasons in (("ipl", canon.IPL_SEASONS), ("wpl", canon.WPL_SEASONS)):
        for s in seasons:
            key = (lg, s)
            runs = acc["batter_runs"][key]
            balls = acc["batter_balls"][key]
            unfiltered = list(runs.values())
            qualified = [runs[b] for b in runs if balls[b] >= 30]
            star_gravity[lg][str(s)] = {
                "gini_unfiltered": r2(_gini(unfiltered)),
                "gini_min30": r2(_gini(qualified)),
                "qualifiers": len(qualified),
            }
    wpl_min30 = [star_gravity["wpl"][str(s)]["gini_min30"] for s in canon.WPL_SEASONS]
    wpl_unf = [star_gravity["wpl"][str(s)]["gini_unfiltered"] for s in canon.WPL_SEASONS]

    # Competitive Balance: normalised win-HHI + distinct champions.
    def mean_nhhi(keys):
        vs = [
            _norm_hhi(list(acc["win_share"][k].values()))
            for k in keys
            if acc["win_share"].get(k)
        ]
        return r4(sum(vs) / len(vs)) if vs else None

    early_ipl = [("ipl", s) for s in (2008, 2009, 2010, 2011)]
    modern_ipl = [("ipl", s) for s in range(2023, 2027)]
    wpl_keys = [("wpl", s) for s in canon.WPL_SEASONS]
    champ = {}
    for lg in ("ipl", "wpl"):
        seen = []
        cum = []
        for season, team in sorted(acc["champions"][lg]):
            if team not in seen:
                seen.append(team)
            cum.append({"season": season, "champion": team, "distinct_so_far": len(seen)})
        champ[lg] = cum

    # Powerplay Fear Index: PP RR / overall RR (consistent legal-ball denoms).
    def pp_fear(league, season):
        key = (league, season)
        if not acc["pp_legal"][key] or not acc["legal"][key]:
            return None
        pp = 6.0 * acc["pp_runs"][key] / acc["pp_legal"][key]
        ov = 6.0 * acc["runs_total"][key] / acc["legal"][key]
        return r2(pp / ov)

    pp_fear_series = {
        "ipl": {str(s): pp_fear("ipl", s) for s in canon.IPL_SEASONS},
        "wpl": {str(s): pp_fear("wpl", s) for s in canon.WPL_SEASONS},
    }

    # Twos Culture: P(2 | runs.batter in {1,2,3}), threes per match.
    def twos_rate(keys):
        a = sum(acc["c1"][k] for k in keys)
        b = sum(acc["c2"][k] for k in keys)
        c = sum(acc["c3"][k] for k in keys)
        return r1(100.0 * b / (a + b + c)) if (a + b + c) else None

    def threes_per_match(keys):
        c = sum(acc["c3"][k] for k in keys)
        m = sum(acc["n_matches"][k] for k in keys)
        return r2(c / m) if m else None

    return {
        "star_gravity": {
            "per_season": star_gravity,
            "wpl_gini_min30_range": [min(wpl_min30), max(wpl_min30)],
            "wpl_gini_unfiltered_range": [min(wpl_unf), max(wpl_unf)],
            "note": (
                "Gini of batter runs is highly threshold-sensitive: unfiltered "
                "it reads star-heavy, but at >=30 balls the WPL's per-season "
                "Gini (~0.35-0.38) sits at or below the IPL's — apparent WPL "
                "star-dependence is a pool-size illusion at matched percentiles."
            ),
        },
        "competitive_balance": {
            "mean_norm_win_hhi": {
                "wpl": mean_nhhi(wpl_keys),
                "ipl_early": mean_nhhi(early_ipl),
                "ipl_modern": mean_nhhi(modern_ipl),
            },
            "distinct_champions": champ,
            "note": (
                "Normalised win-HHI = (HHI - 1/N)/(1 - 1/N), win share via "
                "outcome.winner (super-over ties resolved by eliminator). The "
                "WPL launched more top-heavy than even the chaotic early IPL, "
                "yet the title race is a real duopoly: 2 distinct champions in "
                "4 seasons (MI x2, RCB x2) vs the early IPL's 3 in 4."
            ),
        },
        "powerplay_fear": {
            "series": pp_fear_series,
            "note": (
                "PP run rate / overall run rate, consistent legal-ball "
                "denominators. The IPL sat at ~0.92-0.93 for 15 seasons then "
                "crossed 1.0 by 2026; the WPL 2026 (0.92) sits exactly at the "
                "old IPL equilibrium — the question is whether it needs a "
                "structural shock of its own to break out."
            ),
        },
        "twos_culture": {
            "twos_rate_pct": {
                "ipl_modern": twos_rate(modern_ipl),
                "wpl": twos_rate(wpl_keys),
            },
            "ipl_threes_per_match": {
                "early": threes_per_match([("ipl", s) for s in (2008, 2009, 2010)]),
                "modern": threes_per_match(modern_ipl),
            },
            "note": (
                "twos_rate = P(runs.batter==2 | runs.batter in {1,2,3}). "
                "Smaller WPL ropes convert would-be twos into fours, so the "
                "women's running game is thinner, not richer; meanwhile the "
                "IPL's three is dying as boundary hitting replaced hard "
                "running."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Sister-franchise payoff
# ---------------------------------------------------------------------------


def _shared_grounds(acc):
    """Canonical grounds hosting BOTH leagues, with per-league match counts."""
    ipl_grounds = defaultdict(int)
    wpl_grounds = defaultdict(int)
    for tid, venues in acc["team_venue"].items():
        league = canon.TEAMS[tid]["league"]
        target = ipl_grounds if league == "ipl" else wpl_grounds
        for v, n in venues.items():
            target[v] += n
    shared = sorted(set(ipl_grounds) & set(wpl_grounds))
    return [
        {"venue": v, "city": canon.GROUND_CITY[v], "ipl_matches": ipl_grounds[v], "wpl_matches": wpl_grounds[v]}
        for v in shared
    ]


def _team_grounds(acc, tid):
    return set(acc["team_venue"].get(tid, {}))


def nearest_ipl_star_by_style(acc, team_dist_vec):
    """Nearest IPL SEASON-star to a franchise's pooled outcome distribution."""
    p = normalize(team_dist_vec)
    best_gi, best_d = None, None
    for ig in IPL_GIS:
        d = js_distance(p, normalize(acc["dist"][ig][0]))
        if best_d is None or d < best_d:
            best_gi, best_d = ig, d
    return best_gi, best_d


def payoff_section(acc):
    shared = _shared_grounds(acc)
    shared_set = {g["venue"] for g in shared}
    variants = []

    # Reverse sister lookup (WPL name -> IPL name) for the shared-city label.
    wpl_to_ipl_city = {}
    for (ipl_lg, ipl_name), (wpl_lg, wpl_name, city) in SISTER_PAIRS.items():
        wpl_to_ipl_city[wpl_name] = (ipl_name, city)

    for ipl_name in canon.CURRENT_IPL_FRANCHISES:
        tid = canon.team_id("ipl", ipl_name)
        short = canon.TEAMS[tid]["short"]
        sister = SISTER_PAIRS.get(("ipl", ipl_name))
        if sister:
            _wlg, wpl_name, city = sister
            wtid = canon.team_id("wpl", wpl_name)
            grounds = sorted(
                (_team_grounds(acc, tid) & _team_grounds(acc, wtid)) & shared_set
            )
            variants.append(
                {
                    "team": ipl_name,
                    "team_id": tid,
                    "short": short,
                    "league": "ipl",
                    "empty_state": False,
                    "sister": {
                        "team": wpl_name,
                        "team_id": wtid,
                        "short": canon.TEAMS[wtid]["short"],
                        "league": "wpl",
                    },
                    "shared_city": city,
                    "shared_grounds": [
                        {"venue": v, "city": canon.GROUND_CITY[v]} for v in grounds
                    ],
                }
            )
        else:
            variants.append(
                {
                    "team": ipl_name,
                    "team_id": tid,
                    "short": short,
                    "league": "ipl",
                    "empty_state": True,
                    "sister": None,
                    "empty_copy": (
                        "No sister side in the WPL yet. Your city is still "
                        "waiting for its second franchise of light."
                    ),
                }
            )

    for wpl_name in canon.WPL_FRANCHISES:
        wtid = canon.team_id("wpl", wpl_name)
        short = canon.TEAMS[wtid]["short"]
        star_gi, star_d = nearest_ipl_star_by_style(acc, acc["team_dist"][wtid])
        nearest_style = {
            "ipl_season": GROUPS[star_gi][1],
            "gi": star_gi,
            "distance": r4(star_d),
        }
        pair = wpl_to_ipl_city.get(wpl_name)
        if pair:
            ipl_name, city = pair
            itid = canon.team_id("ipl", ipl_name)
            grounds = sorted(
                (_team_grounds(acc, wtid) & _team_grounds(acc, itid)) & shared_set
            )
            variants.append(
                {
                    "team": wpl_name,
                    "team_id": wtid,
                    "short": short,
                    "league": "wpl",
                    "empty_state": False,
                    "sister": {
                        "team": ipl_name,
                        "team_id": itid,
                        "short": canon.TEAMS[itid]["short"],
                        "league": "ipl",
                    },
                    "shared_city": city,
                    "shared_grounds": [
                        {"venue": v, "city": canon.GROUND_CITY[v]} for v in grounds
                    ],
                    "nearest_ipl_star_by_style": nearest_style,
                }
            )
        else:
            variants.append(
                {
                    "team": wpl_name,
                    "team_id": wtid,
                    "short": short,
                    "league": "wpl",
                    "empty_state": True,
                    "sister": None,
                    "nearest_ipl_star_by_style": nearest_style,
                    "empty_copy": (
                        "No IPL sister franchise, so you are home turf here. "
                        "Your dialect sits nearest IPL "
                        f"{GROUPS[star_gi][1]} in style."
                    ),
                }
            )

    # Neutral: the whole shared-city map is the payoff.
    variants.append(
        {
            "team": "Neutral",
            "team_id": None,
            "short": "NEU",
            "league": "neutral",
            "empty_state": False,
            "sister": None,
            "shared_grounds": [
                {"venue": g["venue"], "city": g["city"]} for g in shared
            ],
        }
    )

    return {
        "card": "your-sister-franchise",
        "variants": variants,
        "sister_pairs": [
            {
                "ipl": ipl_name,
                "ipl_id": canon.team_id("ipl", ipl_name),
                "wpl": wpl_name,
                "wpl_id": canon.team_id("wpl", wpl_name),
                "shared_city": city,
            }
            for (ipl_lg, ipl_name), (wpl_lg, wpl_name, city) in SISTER_PAIRS.items()
        ],
        "shared_grounds": shared,
        "definition": (
            "Per franchise (10 IPL + 5 WPL + neutral): IPL pickers meet their "
            "shared-city WPL sister (MI, RCB, DC and GT<->Gujarat Giants); WPL "
            "pickers get the inverted card — home turf here — plus the IPL "
            "season-star nearest their team's style by outcome-mix distance. "
            "The five grounds hosting both leagues power the same-ground "
            "comparison. Sisterless sides (six IPL franchises, UP Warriorz) "
            "get the designed no-sister state."
        ),
    }


# ---------------------------------------------------------------------------
# Document + main
# ---------------------------------------------------------------------------


def ch6_doc(acc) -> dict:
    return {
        "chapter": 6,
        "title": "Two Dialects",
        "register": "beside the path, not on it",
        "era_bands": [
            {"key": f"{lg} {label}", "league": lg, "label": label, "seasons": [lo, hi]}
            for lg, label, lo, hi in ERA_BANDS
        ],
        "controlling_morph": {
            "reuses_buffer": "group_ids.u16",
            "note": (
                "The field condenses into 23 season-stars; each ball renders at "
                "its group's star position (group_ids.u16 already maps every "
                "ball to its group 0-22) plus jitter. The phase toggle swaps "
                "between the precomputed, Procrustes-aligned per-phase star "
                "tables below — never a live re-embed, so the WPL can never "
                "flip to the wrong side of the IPL path."
            ),
        },
        "constellation": constellation_section(acc),
        "maturity_clock": maturity_section(acc),
        "run_dna": run_dna_section(acc),
        "stumping": stumping_section(acc),
        "photo_finish": photo_finish_section(acc),
        "batting_ladder": batting_ladder_section(acc),
        "payoff": payoff_section(acc),
        "footnotes": footnotes_section(acc),
    }


def build_doc(data_root: Path = canon.DATA_ROOT) -> dict:
    return ch6_doc(build_ch6(data_root))


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    doc = build_doc()
    out_root.mkdir(parents=True, exist_ok=True)
    scenes_dir = out_root / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    raw = flatten.compact_json(doc, sort_keys=True)
    (scenes_dir / "ch6.json").write_bytes(raw)
    sizes = {
        "scenes/ch6.json": {
            "bytes_raw": len(raw),
            "bytes_gz": len(flatten.gz_bytes(raw)),
        }
    }

    # Register in meta.json's manifest (merge, run AFTER flatten + scenes so the
    # insertion order, and therefore meta.json, stays byte-deterministic).
    meta_path = out_root / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta.setdefault("files", {}).update(sizes)
        meta_path.write_bytes(flatten.compact_json(meta))

    for name, s in sizes.items():
        print(f"  {name:18s} raw={s['bytes_raw']:>9,}  gz={s['bytes_gz']:>8,}")
    con = doc["constellation"]["validation"]
    print(
        "ch6 constellation stress:",
        {k: v for k, v in con["mds_stress"].items()},
        "| all WPL nearest 2008:",
        con["all_wpl_nearest_is_2008"],
    )
    for t in doc["constellation"]["two_truths"]:
        print(
            f"  WPL {t['wpl_season']}: mix-twin IPL {t['outcome_mix_twin']['ipl_season']}, "
            f"rate-twin IPL {t['run_rate_twin']['ipl_season']} "
            f"(RR {t['wpl_rr']} vs {t['run_rate_twin']['ipl_rr']})"
        )
    m = doc["maturity_clock"]["headline"]
    print(f"ch6 maturity: WPL yr4 {m['wpl_year4_rr']} == IPL yr15 {m['ipl_year15_rr']} -> {m['equal']}")
    h = doc["run_dna"]["headline"]
    print(f"ch6 run DNA fours: WPL {h['four_share']['wpl']} vs IPL {h['four_share']['ipl_modern']}; "
          f"sixes WPL {h['six_share']['wpl']} vs IPL {h['six_share']['ipl_modern']}")
    st = doc["stumping"]["headline"]
    print(f"ch6 stumping: WPL {st['wpl_range']} vs IPL 2026 {st['ipl_2026']}")
    pf = doc["photo_finish"]["headline"]
    print(f"ch6 photo-finish: WPL {pf['wpl']}% vs IPL {pf['ipl_early']}%/{pf['ipl_modern']}%")
    dp = doc["batting_ladder"]["depth"]["headline"]
    print(f"ch6 batting depth: WPL 2025 pos7+ {dp['wpl_2025_pos7plus']}%")
    n_pay = len(doc["payoff"]["variants"])
    n_empty = sum(1 for v in doc["payoff"]["variants"] if v["empty_state"])
    print(f"ch6 payoff: {n_pay} variants, {n_empty} designed empty state(s), "
          f"{len(doc['payoff']['shared_grounds'])} shared grounds")
    return doc


if __name__ == "__main__":
    main()
