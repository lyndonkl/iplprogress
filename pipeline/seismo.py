"""League-pulse seismograph — pure-Python changepoint detection (R6a helper).

PELT (L2/SSE cost, per-changepoint penalty beta) + an offline Bayesian
product-partition changepoint posterior (Normal-mean) over the IPL/WPL
season-by-season metric series. Stdlib only, byte-deterministic (no random,
no numpy). Imported by pipeline/ch10.py; emits nothing itself.

`build_seismo()` reproduces scratchpad/ch10_seismo.json exactly: the per-season
metric ladders (six-rate / run-rate / RPO / wide-rate / dot-rate / boundary-rate
2008-2026), the penalty sweep and the six-to-two strictness stops, the fault map
(break years per metric per strictness), the Bayesian posteriors (the crack
opacity source), the ribbon crack ball-positions at the medium strictness, the
composite league-pulse strictness curve, the 2021 India-vs-UAE venue-leg split,
and the WPL under-powered micro-series.

The changepoints are run on the STANDARDIZED per-season series so the penalty
beta is comparable across metrics; the ribbon crack ball-positions come from the
per-season cumulative delivery index (flatten season-blocked order, IPL first, so
a crack's point index doubles as its position on the full ribbon).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import h2h

UAE = {"Dubai", "Sharjah", "Abu Dhabi"}
METRICS = ("six_rate", "run_rate", "wide_rate", "dot_rate", "boundary_rate")


def city_of(info):
    c = info.get("city")
    if c:
        return c
    try:
        return canon.GROUND_CITY[canon.canon_venue(info["venue"])]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 1. Single-pass metric builder — per-match records + per-season aggregates
# ---------------------------------------------------------------------------


def build(league="ipl"):
    files = h2h.date_ordered_match_files()
    per_match = []
    season_agg = {}
    leg2021 = {"india": [0, 0], "uae": [0, 0]}  # runs, legal balls
    cum_deliv = 0
    for date0, mid, lg, path in files:
        if lg != league:
            continue
        m = json.load(open(path))
        info = m["info"]
        season = canon.canon_season(info)
        city = city_of(info)
        lb = runs = sixes = fours = dots = wides = deliv = 0
        for inn in m["innings"]:
            if canon.is_super_over(inn):
                continue
            for ov in inn["overs"]:
                for d in ov["deliveries"]:
                    deliv += 1
                    ex = d.get("extras", {})
                    legal = ("wides" not in ex) and ("noballs" not in ex)
                    tot = d["runs"]["total"]
                    bat = d["runs"]["batter"]
                    runs += tot
                    if "wides" in ex:
                        wides += 1
                    if legal:
                        lb += 1
                        if tot == 0:
                            dots += 1
                        if bat == 6:
                            sixes += 1
                        elif bat == 4:
                            fours += 1
        if lb == 0:
            continue
        rec = {
            "date": date0, "match_id": mid, "season": season, "city": city,
            "legal_balls": lb, "runs": runs, "sixes": sixes, "fours": fours,
            "dots": dots, "wides": wides, "deliveries": deliv,
            "ball_start": cum_deliv,
            "six_rate": sixes / lb, "run_rate": runs / lb,
            "wide_rate": wides / lb, "dot_rate": dots / lb,
            "boundary_rate": (fours + sixes) / lb,
        }
        cum_deliv += deliv
        per_match.append(rec)
        a = season_agg.setdefault(season, {k: 0 for k in
            ("lb", "runs", "sixes", "fours", "dots", "wides", "deliv", "matches")})
        for k, kk in (("lb", "legal_balls"), ("runs", "runs"), ("sixes", "sixes"),
                      ("fours", "fours"), ("dots", "dots"), ("wides", "wides"),
                      ("deliv", "deliveries")):
            a[k] += rec[kk]
        a["matches"] += 1
        if league == "ipl" and season == 2021:
            leg = "uae" if city in UAE else "india"
            leg2021[leg][0] += runs
            leg2021[leg][1] += lb
    return per_match, season_agg, leg2021


def season_series(season_agg):
    seasons = sorted(season_agg)
    out = {"seasons": seasons}
    cum = 0
    cum_balls = []
    for s in seasons:
        cum_balls.append(cum)
        cum += season_agg[s]["deliv"]
    out["cum_deliv_start"] = cum_balls
    out["total_deliv"] = cum
    for metric, num, den in (("six_rate", "sixes", "lb"), ("run_rate", "runs", "lb"),
                             ("wide_rate", "wides", "lb"), ("dot_rate", "dots", "lb"),
                             ("boundary_rate", None, "lb")):
        vals = []
        for s in seasons:
            a = season_agg[s]
            if metric == "boundary_rate":
                vals.append((a["fours"] + a["sixes"]) / a["lb"])
            else:
                vals.append(a[num] / a[den])
        out[metric] = vals
    out["rpo"] = [v * 6 for v in out["run_rate"]]
    out["matches"] = [season_agg[s]["matches"] for s in seasons]
    return out


# ---------------------------------------------------------------------------
# 2. PELT (Pruned Exact Linear Time), L2 / SSE normal cost
# ---------------------------------------------------------------------------


def _prefix(x):
    n = len(x)
    p = [0.0] * (n + 1)
    p2 = [0.0] * (n + 1)
    for i, v in enumerate(x):
        p[i + 1] = p[i] + v
        p2[i + 1] = p2[i] + v * v
    return p, p2


def _segcost(p, p2, a, b):
    n = b - a
    if n <= 0:
        return 0.0
    s = p[b] - p[a]
    s2 = p2[b] - p2[a]
    return s2 - s * s / n


def pelt(x, beta):
    """PELT with SSE (L2) segment cost and per-changepoint penalty beta.
    Returns the sorted list of internal changepoint indices (0<cp<n)."""
    n = len(x)
    p, p2 = _prefix(x)
    F = [0.0] * (n + 1)
    F[0] = -beta
    last = [0] * (n + 1)
    R = [0]
    for t in range(1, n + 1):
        best = math.inf
        bs = 0
        for s in R:
            c = F[s] + _segcost(p, p2, s, t) + beta
            if c < best:
                best = c
                bs = s
        F[t] = best
        last[t] = bs
        newR = [s for s in R if F[s] + _segcost(p, p2, s, t) <= F[t]]  # K=0 (SSE)
        newR.append(t)
        R = newR
    cps = []
    t = n
    while t > 0:
        s = last[t]
        if s > 0:
            cps.append(s)
        t = s
    return sorted(cps)


def standardize(x):
    n = len(x)
    mu = sum(x) / n
    var = sum((v - mu) ** 2 for v in x) / n
    sd = math.sqrt(var) if var > 0 else 1.0
    return [(v - mu) / sd for v in x]


# ---------------------------------------------------------------------------
# 3. Offline Bayesian changepoint posterior (product-partition, Normal mean)
# ---------------------------------------------------------------------------


def _logsumexp(a):
    m = max(a)
    if m == -math.inf:
        return -math.inf
    return m + math.log(sum(math.exp(v - m) for v in a))


def _seg_logml(p, p2, a, b, s2=1.0, kappa0=1.0):
    """log marginal likelihood of standardized y[a:b] under Normal-known-var."""
    n = b - a
    if n <= 0:
        return 0.0
    S = p[b] - p[a]
    Q = p2[b] - p2[a]
    kn = kappa0 + n
    return (-0.5 * n * math.log(2 * math.pi * s2)
            + 0.5 * math.log(kappa0 / kn)
            - 0.5 * (Q - S * S / kn) / s2)


def bayes_posterior(x, log_rho=None):
    """P(changepoint at boundary i) for i in 1..n-1 (len n-1)."""
    xs = standardize(x)
    n = len(xs)
    p, p2 = _prefix(xs)
    if log_rho is None:
        p_cp = 0.15
        log_rho = math.log(p_cp / (1 - p_cp))
    f = [-math.inf] * (n + 1)
    f[0] = 0.0
    for t in range(1, n + 1):
        terms = []
        for s in range(0, t):
            ml = _seg_logml(p, p2, s, t)
            rho = 0.0 if s == 0 else log_rho
            terms.append(f[s] + ml + rho)
        f[t] = _logsumexp(terms)
    b = [-math.inf] * (n + 1)
    b[n] = 0.0
    for s in range(n - 1, -1, -1):
        terms = []
        for t in range(s + 1, n + 1):
            ml = _seg_logml(p, p2, s, t)
            rho = 0.0 if t == n else log_rho
            terms.append(ml + rho + b[t])
        b[s] = _logsumexp(terms)
    Z = f[n]
    post = []
    for i in range(1, n):
        lp = f[i] + log_rho + b[i] - Z
        post.append(math.exp(min(0.0, lp)))
    return post


# ---------------------------------------------------------------------------
# 4. Penalty sweep, strictness stops, fault map, composite pulse
# ---------------------------------------------------------------------------


def segments_to_breaks(cps, seasons):
    return [seasons[c] for c in cps]


# The six reader-facing strictness stops (loose -> strict), verified 6->2 eras.
STRICTNESS_STOPS = (
    ("LOOSEST", 0.3), ("LOOSE", 0.6), ("MEDIUM", 1.5),
    ("FIRM", 3.0), ("STRICT", 6.0), ("STRICTEST", 12.0),
)
# The penalty sweep the footnote reports as "six loosen to two".
BETAS = (0.3, 0.6, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 14.0, 20.0)


def run(league="ipl"):
    per_match, season_agg, leg2021 = build(league)
    ss = season_series(season_agg)
    seasons = ss["seasons"]
    result = {"league": league, "seasons": seasons, "series": {},
              "per_season_matches": ss["matches"],
              "cum_deliv_start": ss["cum_deliv_start"],
              "total_deliv": ss["total_deliv"]}
    for metric in METRICS:
        result["series"][metric] = [round(v, 6) for v in ss[metric]]
    result["series"]["rpo"] = [round(v, 4) for v in ss["rpo"]]

    std = {m: standardize(ss[m]) for m in METRICS}
    sweep = []
    for beta in BETAS:
        row = {"beta": beta, "metrics": {}}
        for m in METRICS:
            cps = pelt(std[m], beta)
            row["metrics"][m] = {
                "n_eras": len(cps) + 1,
                "break_years": segments_to_breaks(cps, seasons),
                "break_idx": cps,
            }
        allbreaks = set()
        for m in METRICS:
            allbreaks |= set(row["metrics"][m]["break_years"])
        row["union_break_years"] = sorted(allbreaks)
        row["n_stations"] = len(allbreaks)
        row["runrate_eras"] = row["metrics"]["run_rate"]["n_eras"]
        row["sixrate_eras"] = row["metrics"]["six_rate"]["n_eras"]
        sweep.append(row)
    result["penalty_sweep"] = sweep

    stops = []
    for label, beta in STRICTNESS_STOPS:
        row = {"label": label, "beta": beta, "metrics": {}}
        for m in METRICS:
            cps = pelt(std[m], beta)
            row["metrics"][m] = {"n_eras": len(cps) + 1,
                                 "break_years": segments_to_breaks(cps, seasons)}
        row["union_break_years"] = sorted(
            {y for m in METRICS for y in row["metrics"][m]["break_years"]})
        stops.append(row)
    result["strictness_stops"] = stops

    bayes = {}
    for m in METRICS:
        post = bayes_posterior(ss[m])
        boundaries = [{"break_year": seasons[i], "posterior": round(post[i - 1], 4)}
                      for i in range(1, len(seasons))]
        bayes[m] = boundaries
    result["bayes_posterior"] = bayes

    post_at = {}
    for m in METRICS:
        cps = pelt(std[m], 1.5)
        pmap = {b["break_year"]: b["posterior"] for b in bayes[m]}
        post_at[m] = [{"break_year": seasons[c], "posterior": pmap.get(seasons[c]),
                       "ball_pos": ss["cum_deliv_start"][c],
                       "ball_frac": round(ss["cum_deliv_start"][c] / ss["total_deliv"], 4)}
                      for c in cps]
    result["posterior_at_breaks"] = post_at

    fault = {}
    for m in METRICS:
        fault[m] = {stop["label"]: stop["metrics"][m]["break_years"] for stop in stops}
    result["fault_map"] = fault

    if league == "ipl":
        iu = leg2021
        result["leg_2021"] = {
            "india": {"runs": iu["india"][0], "legal_balls": iu["india"][1],
                      "rr": round(iu["india"][0] / (iu["india"][1] / 6), 3)},
            "uae": {"runs": iu["uae"][0], "legal_balls": iu["uae"][1],
                    "rr": round(iu["uae"][0] / (iu["uae"][1] / 6), 3)},
        }

    comp = []
    for i in range(len(seasons)):
        comp.append((std["six_rate"][i] + std["run_rate"][i] + std["boundary_rate"][i]
                     - std["dot_rate"][i]) / 4.0)
    comp_std = standardize(comp)
    result["league_pulse"] = {"series": [round(v, 4) for v in comp],
                              "seasons": seasons, "curve": []}
    for beta in BETAS:
        cps = pelt(comp_std, beta)
        result["league_pulse"]["curve"].append(
            {"beta": beta, "n_eras": len(cps) + 1,
             "break_years": segments_to_breaks(cps, seasons)})
    cpost = bayes_posterior(comp)
    result["league_pulse"]["posterior"] = [
        {"break_year": seasons[i], "posterior": round(cpost[i - 1], 4)}
        for i in range(1, len(seasons))]

    return result, per_match, ss


def build_seismo() -> dict:
    """Full result reproducing scratchpad/ch10_seismo.json (IPL + the WPL series)."""
    res, _pm, _ss = run("ipl")
    try:
        wres, _, wss = run("wpl")
        res["wpl"] = {"seasons": wss["seasons"],
                      "six_rate": [round(v, 6) for v in wss["six_rate"]],
                      "run_rate": [round(v, 6) for v in wss["run_rate"]],
                      "rpo": [round(v, 4) for v in wss["rpo"]],
                      "wide_rate": [round(v, 6) for v in wss["wide_rate"]]}
    except Exception as e:  # pragma: no cover
        res["wpl"] = {"error": str(e)}
    return res
