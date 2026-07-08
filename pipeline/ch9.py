"""R5b — Chapter 9 "The Living League" (institutions churn, the human fabric persists).

The one authoritative corpus pass for Chapter 9 (separate from scenes.py's Ch1-4
build and ch5/ch6/ch7/ch8.py so the R1-R5a scene bytes stay byte-identical). Stdlib
only, no numpy, byte-deterministic (compact JSON, sorted keys, fixed-decimal
rounding; the force layout is seeded random.Random(42) per connected component, so
two runs emit identical bytes).

Emits two artifacts:

  scenes/ch9.json  the duel web (nodes[277] + duels[1691] + per-duel ball-by-ball
                   replays), the auction heartbeat (per-season league-mean squad
                   overlap with a min-max envelope + the five mega-auction troughs +
                   the WPL series), the loyalty spectrum (the vanishing one-club
                   player + the most-shirts record), the WPL age-matched comparison,
                   the 16 payoff variants, the Collapse Contagion footnote figure,
                   and the ch9-* footnote strings.
  pairing.u16      THE one new per-point buffer: per delivery (flatten season-blocked
                   point order, aligned with group_ids.u16) the duel id 0..1690 or the
                   0xFFFF dust sentinel. Delivered to the field as a DATA TEXTURE
                   (uPairingTex indexed by point-index in-shader), NOT a 15th vertex
                   attribute, so the field holds at 14 attributes.

THE controlling morph is free -> duelweb: every ball flies to its duel's strand or
sinks into the dust. Players are nodes (277 = 244 men + 33 women), duels are edges
(1,691 pairings that met >=30 legal balls), laid out ForceAtlas2-style (degree-scaled
repulsion kr=0.02, linear attraction weight=log1p(balls)/log1p(30), gravity kg=0.30,
550 iters, seed 42) PER connected component then packed (the IPL giant centred, the
disjoint WPL web in a corner; the two leagues share no players, so they are never
normalized together). This reproduces scratchpad/ch9_layout.json exactly.

Duel dominance is Engine #6's (h2h.py) empirical-Bayes-shrunk runs-per-ball vs the
league mean (mu=1.3322, k=51.2), clamped to +-1: +1 batter-red, -1 bowler-blue. The
strand color is who came out on top; because the value is shrunk, most strands land
pale (near-even duels), so saturation reads as how lopsided a duel was.

The register (glossary rule): on screen this is PERSISTENCE THROUGH CHURN. A dot is a
ball, a strand is a duel, red is the batter came out on top, blue the bowler; the EKG
line is how much of the squad came back; a one-club player wore one shirt. Stat terms
of art (graph, node, edge, Jaccard, empirical-Bayes, shrinkage, Hawkes, aftershock)
live one click deep in the footnotes.

Three honest deltas ship straight, never fudged toward the teaser: 232 duels ran eight
seasons or longer (not 235), one-club players fell from about 27 in 100 to about 12
(not 28 to 15), and the mega-auction squad-overlap trough averages 0.186 (not 0.185).
ARTIFACT WINS: every on-screen number reads from this emitted JSON.
"""

from __future__ import annotations

import json
import math
import random
import sys
from array import array
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten
import h2h  # Engine #6: person registry / resolve / striker-dismissal + EB reference

SCENES_DIR = canon.OUT_ROOT / "scenes"

DUEL_MIN = 30            # a duel = a batter-bowler pairing that met >=30 legal balls
DUST = 0xFFFF           # the pairing.u16 sentinel for a ball not in any duel
SEED = 42               # the force-layout seed (byte-determinism)
FA2_ITERS = 550
KR = 0.02               # ForceAtlas2 degree-scaled repulsion
KG = 0.30               # ForceAtlas2 gravity
MEGA_YEARS = (2011, 2014, 2018, 2022, 2025)  # the five full re-auction years (IPL)

# The replay ball code (one byte per faced ball in a duel): 0..6 = runs off the bat,
# 7 = a bowler-credited dismissal of the striker (the cell that carries the skittle
# shape). runs.batter is 0 on every such dismissal, so 7 is unambiguous.
WKT_CODE = 7


def ball_code(runs_batter: int, dismissed: bool) -> int:
    if dismissed:
        return WKT_CODE
    return runs_batter if 0 <= runs_batter <= 6 else 6


# ---------------------------------------------------------------------------
# Rounding helpers (mirror ch8)
# ---------------------------------------------------------------------------


def r1(x):
    return round(x, 1)


def r2(x):
    return round(x, 2)


def r3(x):
    return round(x, 3)


def r4(x):
    return round(x, 4)


def pct(a, b):
    return 100.0 * a / b if b else None


# ---------------------------------------------------------------------------
# The one corpus pass (flatten season-blocked point order == pairing.u16 order)
# ---------------------------------------------------------------------------


def build_ch9(data_root: Path = canon.DATA_ROOT) -> dict:
    """Single pass over the corpus in flatten's exact season-blocked point order.

    Collects, delivery-for-delivery (super-over innings skipped identically to
    flatten.build_stream, so every code recorded here shares the field point index the
    render's per-point buffers use):

      * per (batter_id, bowler_id) pairing final totals (balls faced excl. wides,
        runs.batter, bowler-credited striker dismissals, the set of seasons met) plus
        the ordered per-ball replay code and its season run-length;
      * a runs.batter histogram (mu / ball-level variance for EB shrinkage);
      * the interned pairing code of every delivery (all 316,199 points -> pairing.u16);
      * id -> display name; per-person activity balls + season-weighted-sum (node era);
      * per (league, season, franchise) squad set (the auction-heartbeat Jaccard) and
        per-person distinct-franchise set (the loyalty spectrum + the most-shirts record);
      * the Collapse Contagion aftershock counts (a wicket after a wicket, pooled).
    """
    pair_code: dict = {}         # (bat_id, bowl_id) -> int code
    pair_keys: list = []         # code -> (bat_id, bowl_id)
    pair_balls: list = []        # code -> faced balls (excl. wides)
    pair_runs: list = []         # code -> runs.batter on faced balls
    pair_dis: list = []          # code -> bowler-credited striker dismissals
    pair_seasons: list = []      # code -> set of seasons the pair met
    pair_seq: list = []          # code -> bytearray of per-ball replay codes
    pair_sb: list = []           # code -> [[season, count], ...] run-length
    pair_ipl3: list = []         # code -> faced balls in the IPL's first 3 seasons
    pair_wpl3: list = []         # code -> faced balls in the WPL's first 3 seasons

    runhist: Counter = Counter()
    per_delivery = array("I")    # pairing code per delivery (wides included)

    id_name: dict = {}
    person_balls: dict = defaultdict(int)
    person_seasonsum: dict = defaultdict(int)
    person_franchises: dict = defaultdict(set)         # pid -> {canon team} (both leagues)
    squads: dict = defaultdict(set)                    # (league, season, team) -> {pid}

    # Collapse Contagion: pooled wicket-after-wicket vs the marginal wicket rate over
    # every delivery that has a same-innings predecessor.
    coll_pred = 0        # deliveries with a predecessor
    coll_wkt = 0         # of those, how many were wickets (the marginal denominator)
    coll_ww_den = 0      # deliveries whose predecessor was a wicket
    coll_ww_num = 0      # of those, how many were themselves wickets

    IPL3 = (2008, 2009, 2010)
    WPL3 = (2023, 2024, 2025)

    def code_of(bat, bowl):
        key = (bat, bowl)
        c = pair_code.get(key)
        if c is None:
            c = len(pair_keys)
            pair_code[key] = c
            pair_keys.append(key)
            pair_balls.append(0)
            pair_runs.append(0)
            pair_dis.append(0)
            pair_seasons.append(set())
            pair_seq.append(bytearray())
            pair_sb.append([])
            pair_ipl3.append(0)
            pair_wpl3.append(0)
        return c

    npoints = 0
    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        reg = h2h.person_registry(info)
        # squads from the matchday XIs (union across the season == season roster)
        for raw_team, names in info.get("players", {}).items():
            ct = canon.canon_team(raw_team)
            for nm in names:
                pid = h2h.resolve(reg, nm)
                squads[(league, season, ct)].add(pid)
                person_franchises[pid].add(ct)
        for nm, pid in reg.items():
            id_name.setdefault(pid, nm)

        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            prev_wkt = None  # reset the collapse chain each innings
            for over in innings.get("overs", []):
                for dl in over["deliveries"]:
                    bat = h2h.resolve(reg, dl["batter"])
                    bowl = h2h.resolve(reg, dl["bowler"])
                    c = code_of(bat, bowl)
                    per_delivery.append(c)
                    npoints += 1

                    is_wkt = bool(dl.get("wickets"))
                    if prev_wkt is not None:
                        coll_pred += 1
                        if is_wkt:
                            coll_wkt += 1
                        if prev_wkt:
                            coll_ww_den += 1
                            if is_wkt:
                                coll_ww_num += 1
                    prev_wkt = is_wkt

                    if "wides" in dl.get("extras", {}):
                        continue  # a wide is not a ball faced (matches h2h)
                    rb = dl["runs"]["batter"]
                    dismissed = h2h.striker_dismissed(dl, reg, bat)
                    pair_balls[c] += 1
                    pair_runs[c] += rb
                    pair_seasons[c].add(season)
                    if dismissed:
                        pair_dis[c] += 1
                    pair_seq[c].append(ball_code(rb, dismissed))
                    sb = pair_sb[c]
                    if sb and sb[-1][0] == season:
                        sb[-1][1] += 1
                    else:
                        sb.append([season, 1])
                    if league == "ipl" and season in IPL3:
                        pair_ipl3[c] += 1
                    elif league == "wpl" and season in WPL3:
                        pair_wpl3[c] += 1
                    runhist[rb] += 1
                    person_balls[bat] += 1
                    person_seasonsum[bat] += season
                    person_balls[bowl] += 1
                    person_seasonsum[bowl] += season

    return {
        "npoints": npoints,
        "pair_keys": pair_keys,
        "pair_balls": pair_balls,
        "pair_runs": pair_runs,
        "pair_dis": pair_dis,
        "pair_seasons": pair_seasons,
        "pair_seq": pair_seq,
        "pair_sb": pair_sb,
        "pair_ipl3": pair_ipl3,
        "pair_wpl3": pair_wpl3,
        "runhist": runhist,
        "per_delivery": per_delivery,
        "id_name": id_name,
        "person_balls": dict(person_balls),
        "person_seasonsum": dict(person_seasonsum),
        "person_franchises": {k: set(v) for k, v in person_franchises.items()},
        "squads": {k: set(v) for k, v in squads.items()},
        "collapse": {
            "pred": coll_pred, "wkt": coll_wkt,
            "ww_den": coll_ww_den, "ww_num": coll_ww_num,
        },
    }


# ---------------------------------------------------------------------------
# Empirical-Bayes shrinkage (replicate h2h.eb_constants exactly; DerSimonian-Laird)
# ---------------------------------------------------------------------------


def compute_eb(acc: dict) -> dict:
    runhist = acc["runhist"]
    pair_balls = acc["pair_balls"]
    pair_runs = acc["pair_runs"]

    n_balls = sum(runhist.values())
    mu = sum(r * c for r, c in runhist.items()) / n_balls
    e_r2 = sum(r * r * c for r, c in runhist.items()) / n_balls
    sigma2 = e_r2 - mu * mu

    means = [(pair_balls[c], pair_runs[c] / pair_balls[c])
             for c in range(len(pair_balls)) if pair_balls[c] > 0]
    n_pairs = len(means)
    sum_n = sum(n for n, _ in means)
    grand = sum(n * x for n, x in means) / sum_n
    q = sum(n * (x - grand) ** 2 for n, x in means) / sigma2
    sum_n2 = sum(n * n for n, _ in means)
    c_dl = sum_n - sum_n2 / sum_n
    tau2 = max(0.0, (q - (n_pairs - 1)) / c_dl) * sigma2
    k = sigma2 / tau2 if tau2 > 0 else math.inf
    return {"mu": mu, "sigma2": sigma2, "tau2": tau2, "k": k,
            "n_balls": n_balls, "n_pairs": n_pairs}


# ---------------------------------------------------------------------------
# ForceAtlas2 on one connected component (verbatim from the validated layout2)
# ---------------------------------------------------------------------------


def _fa2(members, edges, kr=KR, kg=KG, iters=FA2_ITERS, seed=SEED):
    m = len(members)
    loc = {g: i for i, g in enumerate(members)}
    memset = set(members)
    ledges = [(loc[a], loc[b], balls) for (a, b, balls, _c) in edges
              if a in memset and b in memset]
    deg = [0] * m
    for a, b, _ in ledges:
        deg[a] += 1
        deg[b] += 1
    rnd = random.Random(seed)
    px = [0.0] * m
    py = [0.0] * m
    for i in range(m):
        ang = 2 * math.pi * i / m
        r = 0.3 + 0.2 * rnd.random()
        px[i] = r * math.cos(ang) + rnd.uniform(-1e-3, 1e-3)
        py[i] = r * math.sin(ang) + rnd.uniform(-1e-3, 1e-3)
    WREF = math.log1p(DUEL_MIN)
    T0 = 0.10
    MIND = 1e-4
    dp1 = [deg[i] + 1 for i in range(m)]
    for it in range(iters):
        temp = T0 * (1 - it / iters) + 0.002
        dx = [0.0] * m
        dy = [0.0] * m
        for i in range(m):
            xi, yi, ci = px[i], py[i], dp1[i]
            axi = ayi = 0.0
            for j in range(i + 1, m):
                ddx = xi - px[j]
                ddy = yi - py[j]
                d2 = ddx * ddx + ddy * ddy
                if d2 < MIND:
                    d2 = MIND
                d = math.sqrt(d2)
                f = kr * ci * dp1[j] / d          # FA2 degree-scaled repulsion
                fx = ddx / d * f
                fy = ddy / d * f
                axi += fx
                ayi += fy
                dx[j] -= fx
                dy[j] -= fy
            dx[i] += axi
            dy[i] += ayi
        for a, b, balls in ledges:
            ddx = px[a] - px[b]
            ddy = py[a] - py[b]
            w = math.log1p(balls) / WREF
            fx = ddx * w
            fy = ddy * w                          # linear attraction (force = w*d)
            dx[a] -= fx
            dy[a] -= fy
            dx[b] += fx
            dy[b] += fy
        for i in range(m):
            gx = dx[i] - kg * dp1[i] * px[i]
            gy = dy[i] - kg * dp1[i] * py[i]
            d = math.hypot(gx, gy) or MIND
            step = min(d, temp)
            px[i] += gx / d * step
            py[i] += gy / d * step
    cx = sum(px) / m
    cy = sum(py) / m
    px = [x - cx for x in px]
    py = [y - cy for y in py]
    rmax = max(math.hypot(px[i], py[i]) for i in range(m)) or 1.0
    return {members[i]: (px[i] / rmax, py[i] / rmax) for i in range(m)}


def _metrics(xs, ys):
    n = len(xs)
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    cx = sum(xs) / n
    cy = sum(ys) / n
    rms = math.sqrt(sum((xs[i] - cx) ** 2 + (ys[i] - cy) ** 2 for i in range(n)) / n)
    minpd = 1e9
    close = 0
    tot = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = math.hypot(xs[i] - xs[j], ys[i] - ys[j])
            if d < minpd:
                minpd = d
            if d < 0.02:
                close += 1
            tot += 1
    return {"n": n, "bbox": [r3(minx), r3(miny), r3(maxx), r3(maxy)],
            "rms": r3(rms), "min_pair_dist": r4(minpd),
            "pct_pairs_within_0.02": r3(100 * close / tot)}


# ---------------------------------------------------------------------------
# The duel-web layout (reproduces scratchpad/ch9_layout.json)
# ---------------------------------------------------------------------------


def compute_layout(acc: dict, eb: dict) -> dict:
    pair_keys = acc["pair_keys"]
    pair_balls = acc["pair_balls"]
    pair_runs = acc["pair_runs"]
    pair_dis = acc["pair_dis"]
    pair_seasons = acc["pair_seasons"]
    id_name = acc["id_name"]
    person_balls = acc["person_balls"]
    person_seasonsum = acc["person_seasonsum"]
    mu = eb["mu"]
    k = eb["k"]

    def shrunk(b, r):
        return mu if not math.isfinite(k) else (r + k * mu) / (b + k)

    # duels: >=30 faced balls, ids stable by (balls desc, then the pair key)
    duel_codes = [c for c in range(len(pair_keys)) if pair_balls[c] >= DUEL_MIN]
    duel_codes.sort(key=lambda c: (-pair_balls[c], pair_keys[c]))
    duel_id_of_code = {c: i for i, c in enumerate(duel_codes)}

    node_ids = sorted({p for c in duel_codes for p in pair_keys[c]})
    node_idx = {n: i for i, n in enumerate(node_ids)}
    N = len(node_ids)

    degree = [0] * N
    edges = []  # (ai, bi, balls, code)
    for c in duel_codes:
        b, w = pair_keys[c]
        ai, bi = node_idx[b], node_idx[w]
        if ai == bi:
            continue
        degree[ai] += 1
        degree[bi] += 1
        edges.append((ai, bi, pair_balls[c], c))

    node_era = [person_seasonsum[n] / person_balls[n] if person_balls.get(n) else 2017.0
                for n in node_ids]

    # league of a node from the EXPLICIT league key in squads (pools are disjoint, so
    # a person appears under exactly one league; franchise names collide across leagues
    # so league is never inferred from a name)
    person_leagues = defaultdict(set)
    for (lg, _se, _tm), ids in acc["squads"].items():
        for pid in ids:
            person_leagues[pid].add(lg)

    def node_league(n):
        lgs = person_leagues.get(n, set())
        return "wpl" if lgs == {"wpl"} else "ipl"

    # connected components (union-find), laid out per component then packed
    parent = list(range(N))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, _, _ in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comp_map = defaultdict(list)
    for i in range(N):
        comp_map[find(i)].append(i)
    comps = sorted(comp_map.values(), key=len, reverse=True)

    pos = [(0.0, 0.0)] * N

    def place(layout, cx, cy, scale):
        for g, (x, y) in layout.items():
            pos[g] = (cx + x * scale, cy + y * scale)

    giant = comps[0]
    place(_fa2(giant, edges), -0.18, 0.0, 0.78)      # main IPL web, left-of-centre
    if len(comps) > 1:
        place(_fa2(comps[1], edges), 0.66, 0.62, 0.30)  # the disjoint WPL web, corner
    sy = -0.55
    for comp in comps[2:]:
        if len(comp) == 1:
            pos[comp[0]] = (0.9, sy)
            sy += 0.12
            continue
        place(_fa2(comp, edges, iters=300), 0.85, sy, 0.08)
        sy += 0.22

    px = [pos[i][0] for i in range(N)]
    py = [pos[i][1] for i in range(N)]

    # dominance color: half-range = 2 * sd of the shrunk per-duel values
    dom_vals = [shrunk(pair_balls[c], pair_runs[c]) for c in duel_codes]
    dmean = sum(dom_vals) / len(dom_vals)
    dstd = math.sqrt(sum((d - dmean) ** 2 for d in dom_vals) / len(dom_vals))
    dom_half = 2 * dstd

    def color(d):
        return max(-1.0, min(1.0, (d - mu) / dom_half))

    nodes_out = [{
        "id": node_ids[i], "name": id_name.get(node_ids[i], node_ids[i]),
        "x": r4(px[i]), "y": r4(py[i]), "deg": degree[i],
        "era": r1(node_era[i]), "league": node_league(node_ids[i]),
    } for i in range(N)]

    duels_out = []
    for did, c in enumerate(duel_codes):
        b, w = pair_keys[c]
        ai, bi = node_idx[b], node_idx[w]
        d = shrunk(pair_balls[c], pair_runs[c])
        ss = sorted(pair_seasons[c])
        duels_out.append({
            "id": did, "a": ai, "b": bi,
            "bat": id_name.get(b, b), "bowl": id_name.get(w, w),
            "balls": pair_balls[c], "runs": pair_runs[c], "dis": pair_dis[c],
            "seasons": len(ss), "span": [ss[0], ss[-1]] if ss else None,
            "dom": r4(d), "color": r3(color(d)),
            "px": r4((px[ai] + px[bi]) / 2), "py": r4((py[ai] + py[bi]) / 2),
        })

    # balls split (dust vs in-a-duel), the field's own honest quarter/three-quarters
    in_duel_pts = sum(pair_balls[c] for c in duel_codes)  # placeholder, recomputed below
    faced_in_duel = sum(pair_balls[c] for c in duel_codes)
    faced_total = sum(pair_balls)

    giant_metrics = _metrics([px[i] for i in giant], [py[i] for i in giant])
    all_metrics = _metrics(px, py)

    n_wpl_nodes = sum(1 for i in range(N) if node_league(node_ids[i]) == "wpl")

    return {
        "node_ids": node_ids,
        "node_idx": node_idx,
        "node_league": {node_ids[i]: node_league(node_ids[i]) for i in range(N)},
        "degree": degree,
        "duel_codes": duel_codes,
        "duel_id_of_code": duel_id_of_code,
        "dom_half": dom_half,
        "nodes": nodes_out,
        "duels": duels_out,
        "N": N,
        "n_men": N - n_wpl_nodes,
        "n_women": n_wpl_nodes,
        "components": [len(c) for c in comps],
        "faced_total": faced_total,
        "faced_in_duel": faced_in_duel,
        "giant_metrics": giant_metrics,
        "all_metrics": all_metrics,
        "era_knn": _era_cluster(giant, px, py, node_era),
    }


def _era_cluster(giant, px, py, node_era):
    """knn6 vs global mean era-difference within the giant (the timeline read)."""
    knn = []
    for a in giant:
        ds = sorted((math.hypot(px[a] - px[b], py[a] - py[b]), b)
                    for b in giant if b != a)[:6]
        knn.append(sum(abs(node_era[a] - node_era[b]) for _d, b in ds) / len(ds))
    mean_knn = sum(knn) / len(giant)
    tot = 0.0
    cnt = 0
    for ii in range(len(giant)):
        for jj in range(ii + 1, len(giant)):
            tot += abs(node_era[giant[ii]] - node_era[giant[jj]])
            cnt += 1
    return {"knn6": r3(mean_knn), "global": r3(tot / cnt)}


# ---------------------------------------------------------------------------
# The per-duel ball-by-ball replay strips (scene-authored SVG reads these)
# ---------------------------------------------------------------------------


def replays_section(acc: dict, layout: dict) -> list:
    """One entry per duel (index == duel id): the ordered faced-ball codes and the
    per-season run-length so the strip can place season separators."""
    pair_seq = acc["pair_seq"]
    pair_sb = acc["pair_sb"]
    out = []
    for c in layout["duel_codes"]:
        out.append({"c": list(pair_seq[c]), "sb": [list(x) for x in pair_sb[c]]})
    return out


# ---------------------------------------------------------------------------
# The auction heartbeat (per-season league-mean squad overlap + min-max envelope)
# ---------------------------------------------------------------------------


def _jaccard_series(squads, league, seasons):
    """Per season transition: the per-franchise squad overlap vs the prior season
    (intersection/union of the two rosters), the league mean and the min-max envelope
    across the franchises present in both seasons."""
    series = []
    for si in range(1, len(seasons)):
        s, sp = seasons[si], seasons[si - 1]
        teams_now = {t for (lg, se, t) in squads if lg == league and se == s}
        vals = []
        for t in teams_now:
            cur = squads.get((league, s, t))
            prev = squads.get((league, sp, t))
            if cur and prev:
                vals.append(len(cur & prev) / len(cur | prev))
        if vals:
            series.append({
                "season": s, "mean": r3(sum(vals) / len(vals)),
                "lo": r3(min(vals)), "hi": r3(max(vals)), "n": len(vals),
            })
    return series


def heartbeat_section(acc: dict) -> dict:
    squads = acc["squads"]
    ipl = _jaccard_series(squads, "ipl", list(canon.IPL_SEASONS))
    wpl = _jaccard_series(squads, "wpl", list(canon.WPL_SEASONS))

    mega_set = set(MEGA_YEARS)
    mega_vals = [row["mean"] for row in ipl if row["season"] in mega_set]
    nonmega_vals = [row["mean"] for row in ipl if row["season"] not in mega_set]
    mega_mean = r3(sum(mega_vals) / len(mega_vals))
    nonmega_mean = r3(sum(nonmega_vals) / len(nonmega_vals))

    by_mean = sorted(ipl, key=lambda r: (r["mean"], r["season"]))
    sixth_lowest = by_mean[5]  # the clean gap: 6th-lowest year sits with the resting pulse

    wpl_reset = next((r for r in wpl if r["season"] == 2026), None)

    return {
        "ipl": {
            "series": ipl,
            "mega_years": list(MEGA_YEARS),
            "mega_mean": mega_mean,
            "nonmega_mean": nonmega_mean,
            "resting": nonmega_mean,
            "trough": mega_mean,
            "sixth_lowest": {"season": sixth_lowest["season"],
                             "mean": sixth_lowest["mean"]},
            "y_domain": [0.0, 1.0],
        },
        "wpl": {
            "series": wpl,
            "first_reset": ({"season": wpl_reset["season"], "mean": wpl_reset["mean"]}
                            if wpl_reset else None),
        },
        "definition": (
            "For each team we ask what share of last season's squad is back this "
            "season, the count they kept over the count they used across both years, "
            "then average across the league. A full re-auction resets almost everyone, "
            "so the line drops. The faint band around the line is the lowest and "
            "highest single team each season. Franchises are tracked by their canonical "
            "identity, so a team that changed its name is not counted as a new squad."
        ),
    }


# ---------------------------------------------------------------------------
# The loyalty spectrum (the vanishing one-club player + the most-shirts record)
# ---------------------------------------------------------------------------


def loyalty_section(acc: dict) -> dict:
    squads = acc["squads"]
    person_franchises = acc["person_franchises"]
    id_name = acc["id_name"]

    # per (person, season) the IPL franchises they appeared for (matchday XIs)
    ipl_person_season_teams = defaultdict(set)
    for (lg, se, t), ids in squads.items():
        if lg != "ipl":
            continue
        for pid in ids:
            ipl_person_season_teams[(pid, se)].add(t)

    # walk the seasons in order; a one-club player is a 4th-plus-season player whose
    # cumulative franchise set (through this season) is a single shirt
    cum_seasons: dict = defaultdict(set)
    cum_teams: dict = defaultdict(set)
    series = []
    for s in canon.IPL_SEASONS:
        active = [pid for (pid, se) in ipl_person_season_teams if se == s]
        for pid in active:
            cum_seasons[pid].add(s)
            cum_teams[pid] |= ipl_person_season_teams[(pid, s)]
        den = num = 0
        for pid in active:
            if len(cum_seasons[pid]) >= 4:
                den += 1
                if len(cum_teams[pid]) == 1:
                    num += 1
        if den:
            series.append({"season": s, "pct": r1(pct(num, den)),
                           "one_club": num, "veterans": den})

    # the most shirts a player ever wore (deterministic: count desc, then name)
    ranked = sorted(
        person_franchises.items(),
        key=lambda kv: (-len(kv[1]), id_name.get(kv[0], kv[0])),
    )
    top_pid, top_teams = ranked[0]
    teams_full = sorted(top_teams)
    shorts = []
    for name in teams_full:
        for lg in ("ipl", "wpl"):
            try:
                shorts.append(canon.TEAMS[canon.team_id(lg, name)]["short"])
                break
            except KeyError:
                continue

    # the honest-delta anchors: the peak (about 27, 2012) and the post-peak trough
    # (about 12, 2022), the "roughly halved" pair the copy binds to. The series then
    # ticks up genuinely as the GT/LSG expansion veterans reach their fourth season,
    # which ships straight (never fudged flat).
    peak = max(series, key=lambda r: (r["pct"], -r["season"])) if series else None
    trough = None
    if peak:
        after = [r for r in series if r["season"] >= peak["season"]]
        trough = min(after, key=lambda r: (r["pct"], r["season"]))

    return {
        "series": series,
        "start": series[0] if series else None,
        "end": series[-1] if series else None,
        "peak": peak,
        "trough": trough,
        "span": {"start": peak, "end": trough} if peak else None,
        "y_domain": [0.0, r1(max(row["pct"] for row in series)) if series else 100.0],
        "max_shirts": {
            "id": top_pid, "name": id_name.get(top_pid, top_pid),
            "n": len(top_teams), "teams": teams_full, "shorts": shorts,
        },
        "definition": (
            "A one-club player is someone in their fourth season or later who has only "
            "ever appeared for one franchise, measured season by season. Requiring a "
            "fourth season keeps out one-season cameos, so the measure is about players "
            "with real careers. A franchise that changed its name is treated as one "
            "club, so a player who stayed through a rename is still a one-club player."
        ),
    }


# ---------------------------------------------------------------------------
# The WPL age-matched comparison (a young league whose fabric forms fast)
# ---------------------------------------------------------------------------


def wpl_section(acc: dict, layout: dict, heartbeat: dict) -> dict:
    pair_ipl3 = acc["pair_ipl3"]
    pair_wpl3 = acc["pair_wpl3"]
    ipl_age3 = sum(1 for v in pair_ipl3 if v >= DUEL_MIN)
    wpl_age3 = sum(1 for v in pair_wpl3 if v >= DUEL_MIN)

    node_league = layout["node_league"]
    node_ids = layout["node_ids"]
    wpl_duels = sum(1 for d in layout["duels"]
                    if node_league[node_ids[d["a"]]] == "wpl")

    return {
        "n_players": layout["n_women"],
        "n_duels": wpl_duels,
        "age_matched": {
            "at_seasons": 3,
            "wpl_duels_by_season3": wpl_age3,
            "ipl_duels_by_season3": ipl_age3,
        },
        "heartbeat": heartbeat["wpl"],
        "framing": (
            "The women's league has its own web, laid out separately because the "
            "men's and women's leagues share no players. At three seasons old its "
            "rivalries are taking shape as fast as the men's game did at the same age, "
            "and it has its own auction pulse. It is a young league whose fabric is "
            "forming fast, already knotting together rivalries that will run for a "
            "decade."
        ),
    }


# ---------------------------------------------------------------------------
# Collapse Contagion (the demoted footnote figure, companion to Ch 8 momentum)
# ---------------------------------------------------------------------------


def collapse_section(acc: dict) -> dict:
    c = acc["collapse"]
    base = c["wkt"] / c["pred"] if c["pred"] else 0.0
    cond = c["ww_num"] / c["ww_den"] if c["ww_den"] else 0.0
    ratio = cond / base if base else 0.0
    return {
        "aftershock": r2(ratio),
        "cond_rate": r4(cond),
        "base_rate": r4(base),
        "n_after_wicket": c["ww_den"],
        "note": (
            "A wicket after a wicket, pooled over every delivery with a same-innings "
            "predecessor: how likely the next ball is a wicket right after one, over "
            "the same balls' marginal rate. Below one means a wicket makes the next "
            "ball slightly less likely to be another, not more."
        ),
    }


# ---------------------------------------------------------------------------
# The 16 payoff variants ("your team through the churn")
# ---------------------------------------------------------------------------


def _franchise_person_sets(acc: dict, league: str):
    """pid -> {franchise} and pid -> {season} for one league (matchday XIs)."""
    franchises = defaultdict(set)
    seasons = defaultdict(set)
    for (lg, se, t), ids in acc["squads"].items():
        if lg != league:
            continue
        for pid in ids:
            franchises[pid].add(t)
            seasons[pid].add(se)
    return franchises, seasons


def _longest_duel_for(layout, node_ids, person_franchises, team, by="seasons"):
    """The duel where either player ever wore this team's shirt, richest by `by`
    (seasons then balls, or balls then seasons), else None."""
    best = None
    for d in layout["duels"]:
        a_pid = node_ids[d["a"]]
        b_pid = node_ids[d["b"]]
        if team in person_franchises.get(a_pid, ()) or team in person_franchises.get(b_pid, ()):
            if by == "seasons":
                key = (d["seasons"], d["balls"])
            else:
                key = (d["balls"], d["seasons"])
            if best is None or key > best[0]:
                best = (key, d)
    return best[1] if best else None


def _reset_churn(acc, league, team, reset_year):
    """Players lost / brought in at the team's last mega-auction (reset_year vs the
    prior season roster)."""
    cur = acc["squads"].get((league, reset_year, team), set())
    prev = acc["squads"].get((league, reset_year - 1, team), set())
    return {"year": reset_year, "out": len(prev - cur), "in": len(cur - prev),
            "kept": len(cur & prev)}


def payoff_section(acc, layout, heartbeat, loyalty) -> list:
    node_ids = layout["node_ids"]
    duel_id = {(d["a"], d["b"]): d["id"] for d in layout["duels"]}
    ipl_fr, ipl_seasons = _franchise_person_sets(acc, "ipl")
    wpl_fr, wpl_seasons = _franchise_person_sets(acc, "wpl")
    id_name = acc["id_name"]
    variants = []

    ipl_reset = MEGA_YEARS[-1]  # the most recent IPL mega-auction (2025)

    for team in canon.CURRENT_IPL_FRANCHISES:
        tid = canon.team_id("ipl", team)
        short = canon.TEAMS[tid]["short"]
        d = _longest_duel_for(layout, node_ids, ipl_fr, team, by="seasons")
        # most loyal one-club player: only ever this franchise, most seasons for it
        loyalists = [(len(ipl_seasons[pid]), id_name.get(pid, pid), pid)
                     for pid, frs in ipl_fr.items()
                     if frs == {team}]
        loyalists.sort(key=lambda x: (-x[0], x[1]))
        loyal = loyalists[0] if loyalists else None
        churn = _reset_churn(acc, "ipl", team, ipl_reset)

        rivalry = None
        if d is not None:
            rivalry = {
                "duel_id": d["id"], "bat": d["bat"], "bowl": d["bowl"],
                "balls": d["balls"], "seasons": d["seasons"], "span": d["span"],
                "runs": d["runs"], "dis": d["dis"], "color": d["color"],
            }
        loyalist = ({"name": loyal[1], "seasons": loyal[0]} if loyal else None)

        variants.append({
            "team": team, "team_id": tid, "short": short, "league": "ipl",
            "empty_state": False,
            "rivalry": rivalry, "reset": churn, "loyalist": loyalist,
            "headline": f"{team}. Your team through the churn.",
            "row1": (
                f"Your longest-running rivalry: {rivalry['bat']} versus "
                f"{rivalry['bowl']}, {rivalry['balls']} balls across "
                f"{rivalry['seasons']} seasons." if rivalry else None),
            "row2": (
                f"Every mega-auction tore your squad up. In {churn['year']} you lost "
                f"{churn['out']} players and brought in {churn['in']}."),
            "row3": (
                f"Your most loyal one-club player: {loyalist['name']}, "
                f"{loyalist['seasons']} seasons in one shirt." if loyalist else None),
        })

    for team in canon.WPL_FRANCHISES:
        tid = canon.team_id("wpl", team)
        short = canon.TEAMS[tid]["short"]
        d = _longest_duel_for(layout, node_ids, wpl_fr, team, by="balls")
        team_duels = sum(
            1 for dl in layout["duels"]
            if team in wpl_fr.get(node_ids[dl["a"]], ())
            or team in wpl_fr.get(node_ids[dl["b"]], ()))
        rivalry = None
        if d is not None:
            rivalry = {
                "duel_id": d["id"], "bat": d["bat"], "bowl": d["bowl"],
                "balls": d["balls"], "seasons": d["seasons"], "span": d["span"],
                "runs": d["runs"], "dis": d["dis"], "color": d["color"],
            }
        variants.append({
            "team": team, "team_id": tid, "short": short, "league": "wpl",
            "empty_state": False, "bespoke": True, "forming_fast": True,
            "rivalry": rivalry, "duel_count": team_duels,
            "headline": f"{team}. A young league, already building rivalries.",
            "row1": (
                f"Your longest rivalry so far: {rivalry['bat']} versus "
                f"{rivalry['bowl']}, {rivalry['balls']} balls." if rivalry else None),
            "row2": (
                f"Your web is forming fast. In three seasons you have already knotted "
                f"{team_duels} real rivalries together."),
            "row3": "Your fabric is forming fast.",
        })

    # neutral: the league-wide living-league card
    top = layout["duels"][0]  # Kohli-Jadeja, the single longest rivalry of all
    loy = loyalty["span"]
    variants.append({
        "team": "Neutral", "team_id": None, "short": "NEU", "league": "neutral",
        "empty_state": False,
        "rivalry": {
            "duel_id": top["id"], "bat": top["bat"], "bowl": top["bowl"],
            "balls": top["balls"], "seasons": top["seasons"], "span": top["span"],
            "runs": top["runs"], "dis": top["dis"], "color": top["color"],
        },
        "mega_years": list(MEGA_YEARS),
        "loyalty_start": loy["start"]["pct"] if loy else None,
        "loyalty_end": loy["end"]["pct"] if loy else None,
        "headline": "The living league.",
        "row1": (
            f"The longest rivalry of all: {top['bat']} versus {top['bowl']}, "
            f"{top['balls']} balls across {top['seasons']} seasons."),
        "row2": (
            f"Every few years the whole league is torn up: "
            f"{', '.join(str(y) for y in MEGA_YEARS)}."),
        "row3": (
            f"The one-club player is vanishing, from about "
            f"{round(loy['start']['pct']) if loy else 0} in 100 down to about "
            f"{round(loy['end']['pct']) if loy else 0}. Pick a team to see its own."),
    })
    return variants


# ---------------------------------------------------------------------------
# Footnotes (numbers f-bound so the prose always matches the artifact)
# ---------------------------------------------------------------------------


def _seq(nums):
    return ", ".join(str(n) for n in nums)


def footnotes_section(acc, eb, layout, duel_web, heartbeat, loyalty, wpl,
                      collapse) -> dict:
    nodes = layout["nodes"]
    duels = layout["duels"]
    bs = duel_web["meta"]["balls_split"]
    hubs = sorted(nodes, key=lambda n: (-n["deg"], n["id"]))[:4]
    kj = duels[0]
    ge8 = sum(1 for d in duels if d["seasons"] >= 8)

    ipl = heartbeat["ipl"]
    ladder = ", ".join(f"{row['season']} {row['mean']:.3f}" for row in ipl["series"])
    mega_str = ", ".join(
        f"{row['season']} ({row['mean']:.3f})"
        for row in ipl["series"] if row["season"] in set(MEGA_YEARS))
    wpl_hb = heartbeat["wpl"]["series"]
    wpl_str = ", ".join(f"{row['season']} {row['mean']:.3f}" for row in wpl_hb)

    ms = loyalty["max_shirts"]
    lstart = loyalty["span"]["start"]
    lend = loyalty["span"]["end"]
    lend_season = loyalty["end"]

    return {
        "ch9-duel": {
            "text": (
                f"A duel is a batter and a bowler who faced each other at least "
                f"{DUEL_MIN} legal balls across the whole history, and there are "
                f"{duel_web['meta']['n_duels']:,} of them between "
                f"{duel_web['meta']['n_nodes']} players ({duel_web['meta']['n_men']} "
                f"men and {duel_web['meta']['n_women']} women). Of the "
                f"{bs['total_points']:,} balls ever bowled, {bs['in_duel_points']:,} "
                f"live in one of those duels, about a quarter, and the other "
                f"{bs['dust_points']:,} stay as dust. The busiest players sit dead "
                f"centre because everyone has a rivalry with them: "
                f"{hubs[0]['name']} with {hubs[0]['deg']} duels, then "
                f"{hubs[1]['name']} {hubs[1]['deg']}, {hubs[2]['name']} "
                f"{hubs[2]['deg']}, {hubs[3]['name']} {hubs[3]['deg']}; players "
                f"spread by era so the layout reads left to right as a timeline. "
                f"{kj['bat']} and {kj['bowl']} met {kj['balls']} balls for "
                f"{kj['runs']} runs and {kj['dis']} dismissals across "
                f"{kj['seasons']} seasons ({kj['span'][0]} to {kj['span'][1]}); the "
                f"shrunk read comes out to about {kj['dom']:.2f} runs a ball, below "
                f"the league average, so the strand runs bowler-blue at about "
                f"{kj['color']:.2f}. {ge8} duels have run eight seasons or longer "
                f"by a strict recount that counts only seasons the pair actually "
                f"faced a ball, so it ships {ge8} rather than the blueprint teaser's "
                f"235. The color is each pair's runs a ball against the league "
                f"average of {eb['mu']:.4f}, pulled toward the average until the pair "
                f"has faced about {round(eb['k'])} balls of weight, then clamped to "
                f"plus or minus one, so a thirty-ball duel does not out-shout a "
                f"hundred-and-sixty-ball one and most strands land pale. Dropping the "
                f"thirty-ball threshold adds shorter, noisier duels without changing "
                f"the web's shape; raising it thins the tail but keeps every hub. The "
                f"men's and women's leagues share no players, so they are laid out as "
                f"two separate webs and never mixed; the women's web has "
                f"{wpl['n_players']} players. The empirical-Bayes shrinkage and the "
                f"at-least-thirty-ball threshold are the technical names."
            ),
        },
        "ch9-heartbeat": {
            "text": (
                f"For each team we take the share of last season's squad that is back "
                f"this season, then average across the league, so a full re-auction "
                f"drops the line. Across the seasons the overlap ran {ladder}. The "
                f"five mega-auction years are the five lowest, {mega_str}, averaging "
                f"{ipl['mega_mean']:.3f} against {ipl['nonmega_mean']:.3f} in every "
                f"other year, a clean gap with the sixth-lowest year "
                f"({ipl['sixth_lowest']['season']}) up at "
                f"{ipl['sixth_lowest']['mean']:.3f}. Franchises are tracked by their "
                f"canonical identity, so a team that changed its name is not counted "
                f"as a new squad. The women's league has its own pulse, {wpl_str}, "
                f"with its first big reset in 2026. The season scrub lights each "
                f"strand only in the years its two players actually faced a ball; the "
                f"web positions never move during the scrub, so the rivalries "
                f"genuinely span the reset years rather than being redrawn to look "
                f"continuous. Squad overlap is the technical name."
            ),
        },
        "ch9-loyalty": {
            "text": (
                f"A one-club player is a player in their fourth season or later who "
                f"has only ever appeared for one franchise, measured season by "
                f"season; requiring a fourth season keeps out one-season cameos. The "
                f"one-club share fell from about {round(lstart['pct'])} in 100 in "
                f"{lstart['season']} to about {round(lend['pct'])} in "
                f"{lend['season']}, roughly a halving, which ships straight rather "
                f"than the blueprint teaser's 28 to 15. It has ticked back up lately "
                f"to about {round(lend_season['pct'])} in {lend_season['season']} as "
                f"the two newest franchises' four-season players are one-club by "
                f"definition, an honest wrinkle rather than a reversal of the fall. "
                f"{ms['name']} appeared for "
                f"{ms['n']} franchises ({', '.join(ms['shorts'])}), the most of any "
                f"player. A franchise that changed its name is treated as one club, "
                f"so a player who stayed through a rename is still a one-club player. "
                f"Distinct franchises across a career is the technical name."
            ),
        },
        "ch9-payoff": {
            "text": (
                "Your longest rivalry is your franchise's own duel that spans the "
                "most seasons, a duel where the batter or the bowler ever wore your "
                "shirt. The reset row counts who left and who arrived at your most "
                "recent mega-auction. The loyal player is your longest-serving "
                "one-club player. A young franchise has fewer decade-scale rivalries, "
                "so its longest may be shorter, which is a fact about its age and "
                "never a deficit. The women's league card is the forming-fast beat "
                "made personal, never a deficit card."
            ),
        },
        "ch9-collapse": {
            "text": (
                f"Commentary loves a collapse: one wicket brings the next. We tested "
                f"it the way Chapter 8 tested a wicket bringing a wicket, by asking "
                f"whether a wicket really makes the next delivery more dangerous. It "
                f"does not. The aftershock read comes out at about "
                f"{collapse['aftershock']:.2f}, below one, which means a wicket makes "
                f"the very next ball slightly less likely to be another, not more, "
                f"across the {collapse['n_after_wicket']:,} balls that followed a "
                f"wicket. That lines up with Chapter 8's finding that a wicket after "
                f"a wicket runs about 0.93 and never clears shuffled cricket in the "
                f"modern game, so the collapse is mostly a story we tell after the "
                f"fact. The self-exciting aftershock read and the shuffle test are "
                f"the technical names."
            ),
        },
    }


# ---------------------------------------------------------------------------
# pairing.u16 (per point: duel id 0..1690 or the 0xFFFF dust sentinel)
# ---------------------------------------------------------------------------


def build_pairing(acc: dict, duel_id_of_code: dict) -> bytes:
    per_delivery = acc["per_delivery"]
    n = acc["npoints"]
    pairing = array("H", bytes(2 * n))
    for idx in range(n):
        did = duel_id_of_code.get(per_delivery[idx])
        pairing[idx] = did if did is not None else DUST
    if sys.byteorder == "big":
        pairing.byteswap()
    return pairing.tobytes()


# ---------------------------------------------------------------------------
# Document assembly + main
# ---------------------------------------------------------------------------


def build_doc(data_root: Path = canon.DATA_ROOT) -> tuple:
    acc = build_ch9(data_root)
    eb = compute_eb(acc)
    layout = compute_layout(acc, eb)

    pairing = build_pairing(acc, layout["duel_id_of_code"])
    # in-duel point count == deliveries (wides included) whose pairing is a duel,
    # counted from the per-delivery codes (matches the buffer's non-sentinel count)
    duel_id_of_code = layout["duel_id_of_code"]
    in_duel_points = sum(1 for c in acc["per_delivery"] if c in duel_id_of_code)
    dust_points = acc["npoints"] - in_duel_points

    balls_split = {
        "total_points": acc["npoints"],
        "in_duel_points": in_duel_points,
        "dust_points": dust_points,
        "faced_balls_total": layout["faced_total"],
        "faced_balls_in_duels": layout["faced_in_duel"],
    }

    duel_web = {
        "meta": {
            "n_duels": len(layout["duels"]),
            "n_nodes": layout["N"],
            "n_men": layout["n_men"],
            "n_women": layout["n_women"],
            "duel_min_balls": DUEL_MIN,
            "components": layout["components"],
            "balls_split": balls_split,
            "dominance_color": {
                "center_mu": r4(eb["mu"]),
                "half_range": r4(layout["dom_half"]),
                "note": ("color = clamp((dom - center_mu) / half_range, -1, 1); "
                         "+1 batter-red, -1 bowler-blue; the value is empirical-Bayes "
                         "shrunk runs a ball, so most strands land pale"),
            },
            "eb": {"mu": r4(eb["mu"]), "sigma2": r4(eb["sigma2"]),
                   "tau2": r4(eb["tau2"]), "k": r2(eb["k"]),
                   "n_pairs": eb["n_pairs"], "n_balls": eb["n_balls"]},
            "force": {"algo": "forceatlas2", "iters": FA2_ITERS, "kr": KR, "kg": KG,
                      "attraction": "linear, weight=log1p(balls)/log1p(30)",
                      "repulsion": "kr*(deg_i+1)*(deg_j+1)/d",
                      "gravity": "kg*(deg+1)*pos", "per_component": True, "seed": SEED},
            "legibility": {"giant": layout["giant_metrics"],
                           "all": layout["all_metrics"],
                           "era_knn6": layout["era_knn"]["knn6"],
                           "era_global": layout["era_knn"]["global"]},
        },
        "nodes": layout["nodes"],
        "duels": layout["duels"],
    }

    replays = replays_section(acc, layout)
    heartbeat = heartbeat_section(acc)
    loyalty = loyalty_section(acc)
    wpl = wpl_section(acc, layout, heartbeat)
    collapse = collapse_section(acc)
    payoff = payoff_section(acc, layout, heartbeat, loyalty)
    footnotes = footnotes_section(acc, eb, layout, duel_web, heartbeat, loyalty, wpl,
                                  collapse)

    doc = {
        "chapter": 9,
        "title": "The Living League",
        "register": "persistence through churn",
        "mystery_handoff_in": (
            "Last chapter, beliefs churned and a whole doctrine could arrive and die "
            "inside a broadcast cycle. But underneath the churn some things refuse to "
            "move. Rivalries. Who a team keeps. This chapter finds what stays."
        ),
        "mystery_handoff_out": (
            "Institutions churn and the human fabric holds. One question is still "
            "open: was 2023 a genuinely new era, or just a louder version of the old "
            "game? Next chapter, the Era Machine settles it."
        ),
        "controlling_morph": {
            "name": "duelweb",
            "layout_code": 11,
            "new_buffer": "pairing.u16 (duel id per point, delivered as uPairingTex)",
            "note": (
                "Free field to the duel web: every ball flies to its duel's strand "
                "midpoint (plus a jitter that grows with the duel's ball count) or "
                "sinks into the dim dust. The field reads the pairing from a data "
                "texture uPairingTex indexed by point-index in-shader (position.x "
                "already holds the point index), so no 15th vertex attribute is added "
                "and the field holds at 14. The per-duel strand centre and color come "
                "from uDuelTex, texelFetch'd by duel id. Four held scalars over the "
                "morph: duelReveal, duelDominance, duelDustDim, strandRecede; all "
                "default inert so every prior release renders byte-identically."
            ),
        },
        "duel_web": duel_web,
        "replays": replays,
        "heartbeat": heartbeat,
        "loyalty": loyalty,
        "wpl": wpl,
        "collapse": collapse,
        "payoff": {
            "card": "your-team-through-the-churn",
            "variants": payoff,
            "definition": footnotes["ch9-payoff"]["text"],
        },
        "footnotes": footnotes,
    }
    return doc, pairing


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    doc, pairing = build_doc()
    out_root.mkdir(parents=True, exist_ok=True)
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    scenes_dir = out_root / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    raw = flatten.compact_json(doc, sort_keys=True)
    (scenes_dir / "ch9.json").write_bytes(raw)
    (out_root / "pairing.u16").write_bytes(pairing)

    sizes = {
        "scenes/ch9.json": {"bytes_raw": len(raw), "bytes_gz": len(flatten.gz_bytes(raw))},
        "pairing.u16": {"bytes_raw": len(pairing),
                        "bytes_gz": len(flatten.gz_bytes(pairing))},
    }
    meta_path = out_root / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta.setdefault("files", {}).update(sizes)
        meta_path.write_bytes(flatten.compact_json(meta))

    for name, s in sizes.items():
        print(f"  {name:18s} raw={s['bytes_raw']:>9,}  gz={s['bytes_gz']:>8,}")

    dw = doc["duel_web"]["meta"]
    print(f"ch9 duel web: {dw['n_duels']:,} duels between {dw['n_nodes']} players "
          f"({dw['n_men']} men + {dw['n_women']} women)")
    bs = dw["balls_split"]
    print(f"  balls split: {bs['in_duel_points']:,} in duels / {bs['dust_points']:,} "
          f"dust of {bs['total_points']:,}")
    kj = doc["duel_web"]["duels"][0]
    print(f"  hero {kj['bat']} v {kj['bowl']}: {kj['balls']}/{kj['runs']}/{kj['dis']}"
          f"/{kj['seasons']} span {kj['span']} dom {kj['dom']} color {kj['color']}")
    ge8 = sum(1 for d in doc["duel_web"]["duels"] if d["seasons"] >= 8)
    print(f"  duels 8+ seasons: {ge8}")
    hb = doc["heartbeat"]["ipl"]
    print(f"ch9 heartbeat: resting {hb['resting']} trough {hb['trough']} "
          f"(mega {hb['mega_years']}); 6th-lowest {hb['sixth_lowest']}")
    print(f"  WPL heartbeat: {[[r['season'], r['mean']] for r in doc['heartbeat']['wpl']['series']]}")
    ly = doc["loyalty"]
    print(f"ch9 loyalty: {ly['span']['start']['pct']} ({ly['span']['start']['season']}) "
          f"-> {ly['span']['end']['pct']} ({ly['span']['end']['season']}); "
          f"max shirts {ly['max_shirts']['name']} {ly['max_shirts']['n']}")
    print(f"ch9 collapse: aftershock {doc['collapse']['aftershock']} "
          f"(cond {doc['collapse']['cond_rate']} / base {doc['collapse']['base_rate']})")
    am = doc["wpl"]["age_matched"]
    print(f"ch9 WPL: {doc['wpl']['n_duels']} duels; age-3 WPL {am['wpl_duels_by_season3']}"
          f" vs IPL first-3 {am['ipl_duels_by_season3']}")
    n_pay = len(doc["payoff"]["variants"])
    n_ipl = sum(1 for v in doc["payoff"]["variants"] if v["league"] == "ipl")
    n_wpl = sum(1 for v in doc["payoff"]["variants"] if v["league"] == "wpl")
    print(f"ch9 payoff: {n_pay} variants ({n_ipl} IPL + {n_wpl} WPL + 1 neutral)")
    return doc


if __name__ == "__main__":
    main()
