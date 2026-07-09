"""R6a — Chapter 10 "The Era Machine" (the FINALE: the data draws its own fault lines).

The one authoritative corpus pass for Chapter 10 (separate from scenes.py's Ch1-4
build and ch5..ch9.py so the R1-R5b scene bytes stay byte-identical). Stdlib only,
no numpy, byte-deterministic (compact JSON, sorted keys, fixed-decimal rounding; no
random is used, so two runs emit identical bytes).

Emits ONE artifact and no new buffer (Ch 10 is buffer-free, like Ch 6 and Ch 7):

  scenes/ch10.json  the ribbon geometry hints (total points, per-season ball
                    starts, time-axis ticks); the SEISMOGRAPH (per-season metric
                    ladders + the strictness dial's precomputed break-index sets
                    beta0.3..beta14 with each crack's ball-position and Bayesian
                    posterior + the per-metric ribbon cracks at medium strictness);
                    the FAULT MAP subway (metric lines, break stations, the 2023 /
                    2024 / 2014 interchanges, the sixes-before-scoring gap); the
                    BRIDGE-PLAYER verdict (league SR 141.72 -> 150.59 = +8.87, 56
                    bridge batters, the within/turnover shift-share ~1/3 vs ~2/3,
                    the three-suspect card); the TELEPORTER (Machine A: Sehwag 2008
                    translated through time, the naive ghost vs the honest re-quote
                    with band < gap; Machine B: Gayle 2011 vs Fraser-McGurk 2024 as
                    a percent-above-par bar-swap, never a z-score); the CONVERGENCE
                    clock (men's run rate crossing ten ~2028.8, the WPL forward
                    clock); the 2021 venue-leg micro-era; the 16 payoff variants;
                    and the ch10-* footnote strings.

THE controlling morph is free -> ribbon (LAYOUT_CODE 12): the 316,199 balls sort
into one horizontal band ordered left-to-right by when they were bowled. The ribbon
is a PURE FUNCTION of position.x (the chronological point index) so it adds NO new
buffer and NO 15th attribute; the field STAYS at 14. The fault-line cracks are
scene-drawn SVG at getRibbonLayout().pointToX(ballPos); the strictness dial swaps a
precomputed break-index set out of this JSON (never a live re-fit); the Teleporter
lift rides the spare bit2 of the existing aRunOut byte.

The register (glossary rule): on screen this is THE SYNTHESIS, case closed honestly.
A crack is "where the game broke," its brightness "how sure we are," the dial "the
strictness dial," "how far above his own era" a PERCENT gap and NEVER a z-score. Stat
terms of art (changepoint, PELT, penalty, posterior, shift-share, SR+, percentile,
extrapolation) live one click deep in the footnotes.

Six honest deltas ship straight, never fudged toward the teaser: sixes broke 2014
then 2018 (not one clean 2018), about two-thirds of the 2023-24 jump was new personnel
and usage (not three-quarters), the naive era-translation ceiling is about 224 (not
228), "how far above his own era" ships as a percent-above-par gap (the blueprint
z-scores were not reproducible), and the WPL convergence is owned as barely
foreseeable on four seasons. ARTIFACT WINS: every on-screen number reads from here.
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
import par                      # Engine #1: SR+ / own-era par (the Teleporter)
import seismo                   # the changepoint seismograph (reproduces ch10_seismo.json)

SCENES_DIR = canon.OUT_ROOT / "scenes"

# The whole field in time order (the ribbon), incl. wides/no-balls, super-overs
# skipped, both leagues (IPL 2008-2026 then WPL 2023-2026 in flatten point order).
# Computed in build_ch10 and asserted == this well-known corpus total.
TOTAL_POINTS_EXPECT = 316199

BRIDGE_MIN_BALLS = 60           # a bridge batter faced >= 60 balls in BOTH 2023 & 2024
SRPLUS_QUAL = par.SRPLUS_MIN_BALLS  # 100 balls, the percentile-map + SR+ qualifier
PERCENTILE_WINDOW = 1.0         # +-1 percentile point -> the honest re-quote's band
TELEPORT_ANCHOR_SR = 185        # Sehwag's real 2008 SR, drawn as the display anchor
CONVERGENCE_WINDOW = (2016, 2026)  # the men's run-rate fit window (the digest's clock)
CONVERGENCE_TARGET = 10.0       # "ten an over"
MENS_2026_RPO_LEVEL = None      # filled from the data (the WPL's fixed target)

# The reader-facing strictness dial: the composite league-pulse penalty sweep, verified
# 6 -> 2 eras (digest). Betas pulled from seismo's league_pulse curve.
DIAL_BETAS = (0.3, 0.6, 1.0, 4.0, 14.0)
DIAL_DEFAULT_BETA = 0.6         # the middle (4-era) still (reduced-motion default)

# The Teleporter marquee player-seasons (curated; verified numbers).
SEHWAG = ("V Sehwag", 2008)
GAYLE = ("CH Gayle", 2011)
FRASER_MCGURK = ("J Fraser-McGurk", 2024)
# The era-dial stops for Machine A (the modern band the exhibit re-quotes into).
TELEPORT_TARGET_YEARS = (2023, 2024, 2025, 2026)


# ---------------------------------------------------------------------------
# Rounding helpers (mirror ch9)
# ---------------------------------------------------------------------------


def r1(x):
    return round(x, 1) if x is not None else None


def r2(x):
    return round(x, 2) if x is not None else None


def r3(x):
    return round(x, 3) if x is not None else None


def r4(x):
    return round(x, 4) if x is not None else None


# ---------------------------------------------------------------------------
# The one corpus pass (registry-resolved pids for per-player tables; raw batting
# team for the franchise payoff; league aggregates for SR / run rate / six rate)
# ---------------------------------------------------------------------------


def build_ch10(data_root: Path = canon.DATA_ROOT) -> dict:
    bat: dict = defaultdict(lambda: [0, 0])         # (league, season, pid) -> [balls, runs]
    name_of: dict = {}                              # pid -> display name (last seen)
    league_bat: dict = defaultdict(lambda: [0, 0])  # (league, season) -> [faced_balls, batter_runs]
    league_rr: dict = defaultdict(lambda: [0, 0])   # (league, season) -> [total_runs, legal_balls]
    league_six: dict = defaultdict(lambda: [0, 0])  # (league, season) -> [sixes, legal_balls]
    bat_team: dict = defaultdict(lambda: defaultdict(int))  # (league, season, pid) -> {team: balls}
    team_rr: dict = defaultdict(lambda: [0, 0])     # (league, season, team) -> [total_runs, legal_balls]
    npoints = 0

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        reg = info.get("registry", {}).get("people", {})
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            try:
                bteam = canon.canon_team(innings["team"])
            except (KeyError, TypeError):
                bteam = None
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    npoints += 1
                    ex = dl.get("extras", {})
                    is_wide = "wides" in ex
                    is_noball = "noballs" in ex
                    rb = dl["runs"]["batter"]
                    rt = dl["runs"]["total"]
                    lr = league_rr[(league, season)]
                    lr[0] += rt
                    if not is_wide and not is_noball:
                        lr[1] += 1
                    if bteam is not None:
                        tr = team_rr[(league, season, bteam)]
                        tr[0] += rt
                        if not is_wide and not is_noball:
                            tr[1] += 1
                    if is_wide:
                        continue  # a wide is not a ball faced (SR convention)
                    pid = reg.get(dl["batter"], dl["batter"])
                    name_of[pid] = dl["batter"]
                    b = bat[(league, season, pid)]
                    b[0] += 1
                    b[1] += rb
                    lb = league_bat[(league, season)]
                    lb[0] += 1
                    lb[1] += rb
                    s6 = league_six[(league, season)]
                    s6[1] += 1
                    if rb == 6:
                        s6[0] += 1
                    if bteam is not None:
                        bat_team[(league, season, pid)][bteam] += 1

    assert npoints == TOTAL_POINTS_EXPECT, (npoints, TOTAL_POINTS_EXPECT)
    return {
        "bat": dict(bat),
        "name_of": name_of,
        "league_bat": dict(league_bat),
        "league_rr": dict(league_rr),
        "league_six": dict(league_six),
        "bat_team": {k: dict(v) for k, v in bat_team.items()},
        "team_rr": dict(team_rr),
        "npoints": npoints,
    }


# ---------------------------------------------------------------------------
# League-level accessors + the season SR distribution / quantile map
# ---------------------------------------------------------------------------


def _mk_accessors(acc):
    bat = acc["bat"]
    league_bat = acc["league_bat"]
    league_rr = acc["league_rr"]
    league_six = acc["league_six"]

    def league_sr(lg, s):
        fb, r = league_bat.get((lg, s), (0, 0))
        return 100.0 * r / fb if fb else None

    def run_rate(lg, s):
        tr, lb = league_rr.get((lg, s), (0, 0))
        return 6.0 * tr / lb if lb else None

    def six_per_over(lg, s):
        s6, lb = league_six.get((lg, s), (0, 0))
        tr, lbr = league_rr.get((lg, s), (0, 0))
        return 6.0 * s6 / lbr if lbr else None

    _dist_cache: dict = {}

    def season_srs(lg, s, minb):
        key = (lg, s, minb)
        v = _dist_cache.get(key)
        if v is None:
            v = sorted(100.0 * val[1] / val[0]
                       for (L, S, _pid), val in bat.items()
                       if L == lg and S == s and val[0] >= minb)
            _dist_cache[key] = v
        return v

    def sr_at_pct(lg, s, p, minb):
        v = season_srs(lg, s, minb)
        if not v:
            return None
        idx = (p / 100.0) * (len(v) - 1)
        lo = int(math.floor(idx))
        hi = min(lo + 1, len(v) - 1)
        frac = idx - lo
        return v[lo] + frac * (v[hi] - v[lo])

    def percentile_of(lg, s, sr, minb):
        v = season_srs(lg, s, minb)
        if not v:
            return None
        below = sum(1 for x in v if x < sr)
        return 100.0 * below / len(v)

    return league_sr, run_rate, six_per_over, season_srs, sr_at_pct, percentile_of


# ---------------------------------------------------------------------------
# The ribbon geometry hints (crack ball-positions map onto the full ribbon)
# ---------------------------------------------------------------------------


def ribbon_section(acc, seis) -> dict:
    seasons = seis["seasons"]
    cum = seis["cum_deliv_start"]
    total = acc["npoints"]
    ticks = []
    for i, s in enumerate(seasons):
        ticks.append({"season": s, "ball_pos": cum[i], "ribbon_frac": r4(cum[i] / total)})
    return {
        "total_points": total,
        "n_matches_ipl": sum(seis["per_season_matches"]),
        "legal_deliveries_ipl": seis["total_deliv"],
        "seasons": list(seasons),
        "per_season_matches": list(seis["per_season_matches"]),
        "cum_deliv_start": list(cum),
        "time_axis_ticks": ticks,
        "legend": (
            "One dot, one ball. Left to right is 2008 to now, spaced by balls, so "
            "recent seasons are wider because there are more matches now, not because "
            "anything sped up. A crack is where the game broke, and a solid bright "
            "crack is one we are surer of, a faint dashed one less so."
        ),
        "note": (
            "The ribbon holds all 316,199 balls in flatten point order (IPL 2008 to "
            "2026, then the WPL), so a crack's point index doubles as its position on "
            "the ribbon. x is the ball index, so brightness is uniform along the band."
        ),
    }


# ---------------------------------------------------------------------------
# The Seismograph (metric ladders + the strictness dial + the per-metric cracks)
# ---------------------------------------------------------------------------

METRIC_LABELS = {
    "six_rate": "how often a ball is a six",
    "run_rate": "runs a ball",
    "rpo": "runs an over",
    "wide_rate": "how often a ball is a wide",
    "dot_rate": "how often a ball is a dot",
    "boundary_rate": "how often a ball is a four or six",
}


def _year_ball_pos(seis, year):
    seasons = seis["seasons"]
    if year not in seasons:
        return None
    return seis["cum_deliv_start"][seasons.index(year)]


def _pulse_posterior_map(seis):
    return {row["break_year"]: row["posterior"] for row in seis["league_pulse"]["posterior"]}


def _bayes_map(seis, metric):
    return {row["break_year"]: row["posterior"] for row in seis["bayes_posterior"][metric]}


def seismograph_section(acc, seis) -> dict:
    seasons = seis["seasons"]
    total = acc["npoints"]
    series = {m: list(seis["series"][m]) for m in
              ("six_rate", "run_rate", "rpo", "wide_rate", "dot_rate", "boundary_rate")}

    # per-metric ribbon cracks at the medium strictness (the scene's default draw)
    cracks = []
    for metric, rows in seis["posterior_at_breaks"].items():
        for row in rows:
            bp = row["ball_pos"]
            cracks.append({
                "metric": metric, "year": row["break_year"],
                "ball_pos": bp, "ribbon_frac": r4(bp / total),
                "season_frac": row["ball_frac"], "posterior": row["posterior"],
            })
    cracks.sort(key=lambda c: (c["ball_pos"], c["metric"]))

    # the reader-facing strictness dial: the composite league-pulse penalty sweep
    curve = {row["beta"]: row for row in seis["league_pulse"]["curve"]}
    pulse_post = _pulse_posterior_map(seis)
    stops = []
    for beta in DIAL_BETAS:
        row = curve[beta]
        stop_cracks = []
        for year in row["break_years"]:
            bp = _year_ball_pos(seis, year)
            stop_cracks.append({
                "year": year, "ball_pos": bp, "ribbon_frac": r4(bp / total),
                "posterior": pulse_post.get(year),
            })
        stops.append({
            "beta": beta, "n_eras": row["n_eras"],
            "break_years": list(row["break_years"]), "cracks": stop_cracks,
        })

    # strongest faults across all metrics (for the "how sure" honest framing)
    strongest = []
    for metric, rows in seis["bayes_posterior"].items():
        best = max(rows, key=lambda r: r["posterior"])
        strongest.append({"metric": metric, "year": best["break_year"],
                          "posterior": best["posterior"]})
    strongest.sort(key=lambda r: -r["posterior"])

    return {
        "seasons": list(seasons),
        "series": series,
        "labels": {k: METRIC_LABELS[k] for k in series},
        "record": {"matches": sum(seis["per_season_matches"]),
                   "legal_deliveries": seis["total_deliv"]},
        "posterior_range": [0.15, 0.44],
        "strongest_faults": strongest[:3],
        "cracks": cracks,
        "strictness": {
            "label": "how big a change counts as a new era",
            "composite_series": list(seis["league_pulse"]["series"]),
            "stops": stops,
            "default_beta": DIAL_DEFAULT_BETA,
            "default_n_eras": curve[DIAL_DEFAULT_BETA]["n_eras"],
            "endpoints_note": "loosen and it is six eras, tighten and it is two",
            "strongest_fault": {"metric": "run_rate", "year": 2023,
                                "posterior": _bayes_map(seis, "run_rate")[2023]},
        },
        "bayes_posterior": {m: seis["bayes_posterior"][m] for m in seis["bayes_posterior"]},
        "penalty_sweep_note": (
            "beta0.3 gives six eras (2009, 2010, 2014, 2023, 2024); beta0.6 four; "
            "beta1.0 three; beta4.0 two (2023); beta14 and up one. Six loosen to two."
        ),
    }


# ---------------------------------------------------------------------------
# The Fault Map subway (curated verified station lists + interchanges + the gap)
# ---------------------------------------------------------------------------

FAULT_STATIONS = (
    ("six_rate", "sixes", [2014, 2018, 2022, 2024], 2014),
    ("run_rate", "scoring", [2023, 2024], 2023),
    ("wide_rate", "wides", [2022, 2024], 2022),
    ("dot_rate", "dot balls", [2015, 2016, 2023], 2016),
    ("boundary_rate", "boundaries", [2023, 2024], 2023),
)
FAULT_INTERCHANGES = (
    (2023, ["run_rate", "boundary_rate", "dot_rate"], "scoring, boundaries and dot balls"),
    (2024, ["six_rate", "run_rate", "wide_rate", "boundary_rate"],
     "sixes, scoring, wides and boundaries"),
    (2014, ["six_rate", "dot_rate"], "sixes and dot balls"),
)


def faultmap_section(acc, seis) -> dict:
    total = acc["npoints"]
    metrics = []
    for key, label, stations, primary in FAULT_STATIONS:
        bm = _bayes_map(seis, key)
        st = []
        for year in stations:
            bp = _year_ball_pos(seis, year)
            st.append({"year": year,
                       "ball_pos": bp,
                       "ribbon_frac": r4(bp / total) if bp is not None else None,
                       "posterior": bm.get(year)})
        entry = {"key": key, "label": label, "primary": primary, "stations": st}
        if key == "wide_rate":
            entry["per_match_extra"] = [2021]  # a strict per-match wide break at 2021
        metrics.append(entry)
    interchanges = [{"year": y, "metrics": ms, "label": lbl}
                    for (y, ms, lbl) in FAULT_INTERCHANGES]
    return {
        "seasons": list(seis["seasons"]),
        "metrics": metrics,
        "hero_lines": ["six_rate", "run_rate"],
        "interchanges": interchanges,
        "order_gap": {
            "six_year": 2018, "scoring_year": 2023, "years": 5,
            "alt_six_year": 2014, "alt_years": 9,
            "note": "sixes broke about five years before scoring",
        },
    }


# ---------------------------------------------------------------------------
# The Bridge-Player Verdict (the 2023 mystery, closed)
# ---------------------------------------------------------------------------


def bridge_section(acc) -> dict:
    league_sr, _rr, _spo, _srs, _atp, _pct = _mk_accessors(acc)
    bat = acc["bat"]
    name_of = acc["name_of"]

    sr23 = league_sr("ipl", 2023)
    sr24 = league_sr("ipl", 2024)
    jump = sr24 - sr23

    # bridge batters: >= BRIDGE_MIN_BALLS faced in BOTH 2023 and 2024
    b23 = {pid: v for (lg, s, pid), v in bat.items()
           if lg == "ipl" and s == 2023 and v[0] >= BRIDGE_MIN_BALLS}
    b24 = {pid: v for (lg, s, pid), v in bat.items()
           if lg == "ipl" and s == 2024 and v[0] >= BRIDGE_MIN_BALLS}
    bridge = sorted(set(b23) & set(b24))
    n_bridge = len(bridge)
    deltas = [100.0 * (b24[p][1] / b24[p][0] - b23[p][1] / b23[p][0]) for p in bridge]
    within_mean = sum(deltas) / n_bridge if n_bridge else 0.0
    pr23 = sum(b23[p][1] for p in bridge)
    pb23 = sum(b23[p][0] for p in bridge)
    pr24 = sum(b24[p][1] for p in bridge)
    pb24 = sum(b24[p][0] for p in bridge)
    within_pooled = 100.0 * pr24 / pb24 - 100.0 * pr23 / pb23 if pb23 and pb24 else 0.0

    # formal within / between (turnover) shift-share over ALL batters (ball-share)
    all23 = {pid: v for (lg, s, pid), v in bat.items() if lg == "ipl" and s == 2023}
    all24 = {pid: v for (lg, s, pid), v in bat.items() if lg == "ipl" and s == 2024}
    B23 = sum(v[0] for v in all23.values())
    B24 = sum(v[0] for v in all24.values())
    stayers = set(all23) & set(all24)
    entr = set(all24) - set(all23)
    leav = set(all23) - set(all24)
    within = usage = 0.0
    for pid in stayers:
        s23 = all23[pid][1] / all23[pid][0]
        s24 = all24[pid][1] / all24[pid][0]
        w23 = all23[pid][0] / B23
        w24 = all24[pid][0] / B24
        wbar = 0.5 * (w23 + w24)
        srbar = 0.5 * (s23 + s24)
        within += wbar * (s24 - s23) * 100.0
        usage += srbar * (w24 - w23) * 100.0
    entrants = sum((all24[p][0] / B24) * (all24[p][1] / all24[p][0]) for p in entr) * 100.0
    leavers = -sum((all23[p][0] / B23) * (all23[p][1] / all23[p][0]) for p in leav) * 100.0
    turnover = usage + entrants + leavers
    total_delta = sr24 - sr23

    within_pct = round(100.0 * within / total_delta)
    turnover_pct = round(100.0 * turnover / total_delta)

    return {
        "league_sr_2023": r2(sr23),
        "league_sr_2024": r2(sr24),
        "jump": r2(jump),
        "n_bridge": n_bridge,
        "bridge_min_balls": BRIDGE_MIN_BALLS,
        "within_mean": r2(within_mean),
        "within_pooled": r2(within_pooled),
        "shift_share": {
            "total": r2(total_delta),
            "within": r2(within),
            "within_pct": within_pct,
            "turnover": r2(turnover),
            "turnover_pct": turnover_pct,
            "components": {"usage": r2(usage), "entrants": r2(entrants),
                           "leavers": r2(leavers)},
            "stayers": len(stayers), "entrants_n": len(entr), "leavers_n": len(leav),
        },
        "turnover_range": "two-thirds to three-quarters",
        "verdict": {
            "headline": "Case closed. Three suspects, all guilty on a different count.",
            "panels": [
                {"type": "enabling condition", "chapter": 7,
                 "text": "The rule opened the door."},
                {"type": "measured share", "chapter": 10, "number": "about two-thirds",
                 "text": "New faces walked through it."},
                {"type": "long-run trend", "chapter": 1,
                 "text": "The skill had been climbing for a decade."},
            ],
            "note": (
                "A weight of evidence across three chapters, three things each doing "
                "some of the work, not one that made it happen."
            ),
        },
    }


# ---------------------------------------------------------------------------
# The Player Teleporter (Machine A: translate through time; Machine B: rank vs era)
# ---------------------------------------------------------------------------


def _find_pid(acc, name, season):
    for (lg, s, pid), _v in acc["bat"].items():
        if s == season and acc["name_of"].get(pid) == name:
            return lg, pid
    return None, None


def _player_season(acc, name, season):
    lg, pid = _find_pid(acc, name, season)
    if pid is None:
        return None
    balls, runs = acc["bat"][(lg, season, pid)]
    return {"lg": lg, "pid": pid, "name": name, "season": season,
            "balls": balls, "runs": runs, "sr": 100.0 * runs / balls}


def _translate(acc, sr, season, target_years):
    """Naive (league-ratio) and honest (rank-preserving) re-quotes per target year,
    with the honest re-quote's +-1-percentile band. band half-width < gap holds."""
    league_sr, _rr, _spo, _srs, sr_at_pct, percentile_of = _mk_accessors(acc)
    pct = percentile_of("ipl", season, sr, SRPLUS_QUAL)
    src_sr = league_sr("ipl", season)
    out = []
    for tgt in target_years:
        tgt_lsr = league_sr("ipl", tgt)
        naive = sr * tgt_lsr / src_sr
        honest = sr_at_pct("ipl", tgt, pct, SRPLUS_QUAL)
        blo = sr_at_pct("ipl", tgt, max(0.0, pct - PERCENTILE_WINDOW), SRPLUS_QUAL)
        bhi = sr_at_pct("ipl", tgt, min(100.0, pct + PERCENTILE_WINDOW), SRPLUS_QUAL)
        half = (bhi - blo) / 2.0
        gap = naive - honest
        out.append({
            "year": tgt, "naive": r1(naive), "honest": r1(honest),
            "band_lo": r1(honest - half), "band_hi": r1(honest + half),
            "band_halfwidth": r2(half), "gap": r2(gap),
            "band_lt_gap": half < gap,
        })
    return pct, out


def _srplus_of(srplus_rows, name, season):
    for row in srplus_rows:
        if row["league"] == "ipl" and row["season"] == season and row["batter"] == name:
            return row["srplus"]
    return None


def teleporter_section(acc, srplus_rows) -> dict:
    league_sr, _rr, _spo, _srs, _atp, _pct = _mk_accessors(acc)

    # --- Machine A: translate Sehwag 2008 through time ---
    seh = _player_season(acc, *SEHWAG)
    pct, trans = _translate(acc, seh["sr"], seh["season"], TELEPORT_TARGET_YEARS)
    naive_ceiling = max(t["naive"] for t in trans)
    check = next(t for t in trans if t["year"] == 2026)
    sehwag = {
        "name": seh["name"], "season": seh["season"],
        "balls": seh["balls"], "runs": seh["runs"], "sr": r2(seh["sr"]),
        "league_sr_season": r2(league_sr("ipl", seh["season"])),
        "percentile": r1(pct), "srplus": _srplus_of(srplus_rows, *SEHWAG),
        "naive_ceiling": round(naive_ceiling), "translations": trans,
    }

    # --- Machine B: rank Gayle 2011 vs Fraser-McGurk 2024 against their own eras ---
    gayle = _player_season(acc, *GAYLE)
    fm = _player_season(acc, *FRASER_MCGURK)
    gayle_srp = _srplus_of(srplus_rows, *GAYLE)
    fm_srp = _srplus_of(srplus_rows, *FRASER_MCGURK)
    machine_b = {
        "players": [
            {"name": gayle["name"], "season": gayle["season"], "sr": r2(gayle["sr"]),
             "srplus": gayle_srp, "pct_above_par": r1(gayle_srp - 100.0)},
            {"name": fm["name"], "season": fm["season"], "sr": r2(fm["sr"]),
             "srplus": fm_srp, "pct_above_par": r1(fm_srp - 100.0)},
        ],
        "raw_sr_gap": r1(fm["sr"] - gayle["sr"]),
        "verdict": (
            "Measured against the physics of his own time, 2011 Gayle still edges "
            "2024 Fraser-McGurk, despite a raw strike rate about 51 points lower."
        ),
        "unit": "percent above the going rate of his own year",
    }

    return {
        "machine_a": {
            "anchor_sr": TELEPORT_ANCHOR_SR,
            "default": sehwag,
            "integrity": {
                "check_year": 2026,
                "band_halfwidth": check["band_halfwidth"],
                "gap": check["gap"],
                "band_lt_gap": check["band_lt_gap"],
            },
            "note": (
                "The naive ghost scales the old number up by how much faster the "
                "league scores now; the honest re-quote holds the player at the rank "
                "he actually reached. The ghost overshoots because you cannot scale "
                "an outlier up. Every re-quote is a lookup, never a live model."
            ),
        },
        "machine_b": machine_b,
    }


# ---------------------------------------------------------------------------
# The Convergence Clock (men's run rate crossing ten; the WPL forward clock)
# ---------------------------------------------------------------------------


def _ols(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    m = sxy / sxx
    b = my - m * mx
    resid = [y - (m * x + b) for x, y in zip(xs, ys)]
    se = math.sqrt((sum(r * r for r in resid) / (n - 2)) / sxx) if n > 2 else float("nan")
    return m, b, se, mx, my


def convergence_section(acc, seis) -> dict:
    global MENS_2026_RPO_LEVEL
    league_rr = acc["league_rr"]
    ipl_seasons = list(seis["seasons"])
    ipl_rpo = list(seis["series"]["rpo"])

    lo, hi = CONVERGENCE_WINDOW
    xs = [y for y in ipl_seasons if lo <= y <= hi]
    ys = [ipl_rpo[ipl_seasons.index(y)] for y in xs]
    m, b, se, mx, my = _ols(xs, ys)

    def cross(mm, bb, target=CONVERGENCE_TARGET):
        return (target - bb) / mm

    central = cross(m, b)
    # band: pivot the slope +-se about the centroid, cross ten at each
    lo_cross = cross(m + se, my - (m + se) * mx)   # steeper slope -> earlier
    hi_cross = cross(m - se, my - (m - se) * mx)    # shallower slope -> later
    today_rpo = ipl_rpo[ipl_seasons.index(2026)]
    MENS_2026_RPO_LEVEL = today_rpo

    mens = {
        "series": {"seasons": ipl_seasons, "rpo": ipl_rpo},
        "recent": {"seasons": [2023, 2024, 2025, 2026],
                   "rpo": [ipl_rpo[ipl_seasons.index(y)] for y in (2023, 2024, 2025, 2026)]},
        "fit_window": [lo, hi],
        "slope": r4(m),
        "slope_se": r4(se),
        "crosses_ten": {
            "central": r1(central),
            "band_lo": r1(lo_cross),
            "band_hi": r1(hi_cross),
            "band_years": [round(lo_cross), round(hi_cross)],
        },
        "today": {"season": 2026, "rpo": r2(today_rpo)},
        "target": CONVERGENCE_TARGET,
    }

    # WPL forward clock (4 seasons, under-powered)
    wpl_seasons = list(seis["wpl"]["seasons"])
    wpl_rpo = list(seis["wpl"]["rpo"])
    wpl_six_po = [round(v * 6.0, 3) for v in seis["wpl"]["six_rate"]]
    mR, bR, seR, _, _ = _ols(wpl_seasons, wpl_rpo)
    mS, bS, seS, _, _ = _ols(wpl_seasons, wpl_six_po)
    mens_six_2026 = seis["series"]["six_rate"][ipl_seasons.index(2026)] * 6.0
    wpl_rr_reaches = (today_rpo - bR) / mR if mR else None
    wpl_six_reaches = (mens_six_2026 - bS) / mS if mS else None

    wpl = {
        "run_rate": {
            "seasons": wpl_seasons, "rpo": wpl_rpo, "slope": r2(mR), "slope_se": r4(seR),
            "reaches_mens_2026_level": r1(wpl_rr_reaches) if wpl_rr_reaches else None,
            "mens_2026_level": r2(today_rpo),
        },
        "six_rate": {
            "seasons": wpl_seasons, "six_per_over": wpl_six_po,
            "slope": r3(mS), "slope_se": r4(seS),
            "off_the_clock": True,
            "reaches_mens_2026_level": r1(wpl_six_reaches) if wpl_six_reaches else None,
            "mens_2026_level": r3(mens_six_2026),
        },
    }

    return {
        "mens": mens,
        "wpl": wpl,
        "framing": (
            "Run rate closes first; six-hitting is so far out it is barely "
            "foreseeable on four seasons."
        ),
        "wpl_framing": (
            "A young league whose future you can already clock, its run rate rising "
            "toward where the men's game sits today."
        ),
    }


# ---------------------------------------------------------------------------
# The 2021 venue-leg micro-era (footnote figure)
# ---------------------------------------------------------------------------


def microera_section(seis) -> dict:
    leg = seis["leg_2021"]
    return {
        "year": 2021,
        "india": {"rr": leg["india"]["rr"], "runs": leg["india"]["runs"],
                  "legal_balls": leg["india"]["legal_balls"]},
        "uae": {"rr": leg["uae"]["rr"], "runs": leg["uae"]["runs"],
                "legal_balls": leg["uae"]["legal_balls"]},
        "note": (
            "A strict per-match wide-rate break at 2021 partly reflects the "
            "India-leg-versus-UAE-leg split, not only a rule change."
        ),
    }


# ---------------------------------------------------------------------------
# The 16 payoff variants ("Your adapters")
# ---------------------------------------------------------------------------


def _majority_team(bat_team, lg, season, pid):
    tc = bat_team.get((lg, season, pid))
    if not tc:
        return None, 0
    team = max(tc, key=lambda t: (tc[t], t))
    return team, sum(tc.values())


def _franchise_riser(acc, league, team, s_from, s_to, minb=40):
    """The batter (majority-team `team` in s_to) whose SR rose most from s_from to
    s_to, faced >= minb balls in both. Returns dict or None."""
    bat = acc["bat"]
    bat_team = acc["bat_team"]
    name_of = acc["name_of"]
    best = None
    for (lg, s, pid), v in bat.items():
        if lg != league or s != s_to or v[0] < minb:
            continue
        mt, _n = _majority_team(bat_team, lg, s_to, pid)
        if mt != team:
            continue
        prev = bat.get((lg, s_from, pid))
        if not prev or prev[0] < minb:
            continue
        sr_from = 100.0 * prev[1] / prev[0]
        sr_to = 100.0 * v[1] / v[0]
        rise = sr_to - sr_from
        key = (rise, name_of.get(pid, pid))
        if best is None or key > best[0]:
            best = (key, {"name": name_of.get(pid, pid), "rise": r1(rise),
                          "sr_from": r1(sr_from), "sr_to": r1(sr_to),
                          "season_from": s_from, "season_to": s_to})
    return best[1] if best else None


def _franchise_legend(acc, league, team, minb=150):
    """The highest-SR substantial player-season (>= minb balls) for the franchise."""
    bat = acc["bat"]
    bat_team = acc["bat_team"]
    name_of = acc["name_of"]
    best = None
    for thresh in (200, minb, 100):
        for (lg, s, pid), v in bat.items():
            if lg != league or v[0] < thresh:
                continue
            mt, _n = _majority_team(bat_team, lg, s, pid)
            if mt != team:
                continue
            sr = 100.0 * v[1] / v[0]
            key = (sr, name_of.get(pid, pid), s)
            if best is None or key > best[0]:
                best = (key, {"name": name_of.get(pid, pid), "season": s,
                              "sr": r2(sr), "balls": v[0], "runs": v[1]})
        if best is not None:
            break
    return best[1] if best else None


def _team_run_rate(acc, league, season, team):
    tr, lb = acc["team_rr"].get((league, season, team), (0, 0))
    return 6.0 * tr / lb if lb else None


def payoff_section(acc, srplus_rows) -> dict:
    league_sr, run_rate, _spo, _srs, _atp, _pct = _mk_accessors(acc)
    variants = []
    league_rr_2026 = run_rate("ipl", 2026)

    for team in canon.CURRENT_IPL_FRANCHISES:
        tid = canon.team_id("ipl", team)
        short = canon.TEAMS[tid]["short"]
        riser = _franchise_riser(acc, "ipl", team, 2023, 2024)
        legend = _franchise_legend(acc, "ipl", team)
        legend_out = None
        if legend is not None:
            _p, trans = _translate(acc, 100.0 * legend["runs"] / legend["balls"],
                                   legend["season"], TELEPORT_TARGET_YEARS)
            t2026 = next(t for t in trans if t["year"] == 2026)
            legend_out = {
                "name": legend["name"], "season": legend["season"],
                "sr": legend["sr"], "honest_2026": t2026["honest"],
                "naive_2026": t2026["naive"], "translations": trans,
            }
        team_rr = _team_run_rate(acc, "ipl", 2026, team)
        position = None
        if team_rr is not None and league_rr_2026 is not None:
            if team_rr > league_rr_2026 + 0.05:
                position = "above"
            elif team_rr < league_rr_2026 - 0.05:
                position = "short of"
            else:
                position = "level with"

        variants.append({
            "team": team, "team_id": tid, "short": short, "league": "ipl",
            "empty_state": False,
            "headline": f"{team}. Your adapters.",
            "riser": riser,
            "legend": legend_out,
            "climb": ({"team_rate": r2(team_rr), "league_rate": r2(league_rr_2026),
                       "position": position} if team_rr is not None else None),
            "row1": (
                f"When the game broke in 2023, {riser['name']} rose with it. Their "
                f"scoring jumped {riser['rise']} runs per 100 balls as the fault "
                f"opened." if riser else None),
            "row2": (
                f"Drop your legend into today. {legend_out['name']}'s "
                f"{legend_out['season']} would re-quote to about "
                f"{legend_out['honest_2026']} runs per 100 in 2026."
                if legend_out else None),
            "row3": (
                f"Your team's scoring now sits at {r2(team_rr)} an over, {position} "
                f"the league's {r2(league_rr_2026)}." if team_rr is not None else None),
        })

    for team in canon.WPL_FRANCHISES:
        tid = canon.team_id("wpl", team)
        short = canon.TEAMS[tid]["short"]
        # the WPL seasons this franchise batted in
        yrs = sorted({s for (lg, s, _pid) in acc["bat_team"] if lg == "wpl"
                      and _majority_team(acc["bat_team"], lg, s, _pid)[0] == team})
        first = yrs[0] if yrs else 2023
        riser = _franchise_riser(acc, "wpl", team, first, 2026, minb=30)
        if riser is None:  # fall back to the franchise's top 2026 SR (never a deficit)
            legend26 = _franchise_legend(acc, "wpl", team, minb=60)
            riser = ({"name": legend26["name"], "rise": None,
                      "sr_to": legend26["sr"], "season_from": first, "season_to": 2026}
                     if legend26 else None)
        variants.append({
            "team": team, "team_id": tid, "short": short, "league": "wpl",
            "empty_state": False, "bespoke": True, "forming_fast": True,
            "headline": f"{team}. A young league whose future you can already clock.",
            "riser": riser,
            "row1": ("Your scoring is rising toward where the men's game sits today, "
                     "on a slope you can already read."),
            "row2": (
                f"Your longest riser so far: {riser['name']}, {riser['rise']} runs per "
                f"100 faster since your first season."
                if riser and riser.get("rise") is not None
                else (f"Your top striker so far: {riser['name']}, at "
                      f"{riser['sr_to']} runs per 100." if riser else None)),
            "row3": "Your fabric is young, and you can already see where it is headed.",
        })

    # neutral card (no team picked): the league-wide reads
    seh = _player_season(acc, *SEHWAG)
    _p, seh_trans = _translate(acc, seh["sr"], seh["season"], (2026,))
    variants.append({
        "team": "Neutral", "team_id": None, "short": "NEU", "league": "neutral",
        "empty_state": False,
        "headline": "The Era Machine.",
        "row1": ("The game broke in stages. Sixes cracked first in the mid-2010s, "
                 "then everything broke together in 2023."),
        "row2": ("The 2023 jump was about two-thirds new faces, not the same players "
                 "hitting harder."),
        "row3": (f"Drop Sehwag's 2008 into today and it re-quotes from 185 to about "
                 f"{seh_trans[0]['honest']} in 2026. The men's game crosses ten an "
                 f"over around 2028 or 2029. Pick a team to see its own."),
        "sehwag_honest_2026": seh_trans[0]["honest"],
    })
    return {
        "card": "your-adapters",
        "variants": variants,
        "definition": (
            "Each card's riser is the franchise batter whose own scoring rose most "
            "across the 2023 fault; the teleported legend is the franchise's signature "
            "player-season re-quoted the honest way to 2026; the climb position is the "
            "team's current run rate against the league's, stated as a position, never "
            "a ranking. The WPL card is the forward-clock beat made personal, never a "
            "deficit card."
        ),
    }


# ---------------------------------------------------------------------------
# Footnotes (numbers f-bound so the prose always matches the artifact)
# ---------------------------------------------------------------------------


def _seq(nums, fmt="{}"):
    return ", ".join(fmt.format(n) for n in nums)


def footnotes_section(ribbon, seismo_b, faultmap, bridge, teleporter, convergence,
                      microera) -> dict:
    six_ladder = _seq(seismo_b["series"]["six_rate"], "{:.3f}")
    rpo_ladder = _seq(seismo_b["series"]["rpo"], "{:.2f}")
    sf = seismo_b["strongest_faults"]
    seh = teleporter["machine_a"]["default"]
    t24 = next(t for t in seh["translations"] if t["year"] == 2024)
    t26 = next(t for t in seh["translations"] if t["year"] == 2026)
    mb = teleporter["machine_b"]["players"]
    ss = bridge["shift_share"]
    mens = convergence["mens"]
    wrr = convergence["wpl"]["run_rate"]
    wsr = convergence["wpl"]["six_rate"]
    sf0 = sf[0] if sf else {"metric": "wide_rate", "year": 2022, "posterior": 0.44}
    sf0_noun = {
        "six_rate": "six-hitting", "run_rate": "scoring", "rpo": "scoring",
        "wide_rate": "wides", "dot_rate": "dot-ball", "boundary_rate": "boundary",
    }.get(sf0["metric"], sf0["metric"])
    _rr_post = {r["break_year"]: r["posterior"] for r in seismo_b["bayes_posterior"]["run_rate"]}
    run2023_post = _rr_post.get(2023, 0.37)

    return {
        "ch10-seismo": {
            "text": (
                f"The ribbon holds all {ribbon['total_points']:,} balls in the order "
                f"they were bowled, so left to right is time. The machine scans each "
                f"season-by-season series for the years the level genuinely steps, on "
                f"the date-ordered record of {seismo_b['record']['matches']:,} men's "
                f"matches and {seismo_b['record']['legal_deliveries']:,} legal "
                f"deliveries, and marks a crack where a step is real. How sure it is "
                f"runs from about {seismo_b['posterior_range'][0]} to "
                f"{seismo_b['posterior_range'][1]}, so most cracks are drawn faint "
                f"because the record is only nineteen seasons long. The breaks are "
                f"staggered: sixes at 2014, then again 2018, 2022 and 2024; runs an "
                f"over at 2023, then 2024; wides at 2022, then 2024; dots at 2015 to "
                f"2016, then 2023; boundaries at 2023, then 2024. So the six-rate "
                f"broke about five years before scoring did, and 2018 to 2023 is "
                f"exactly five. The strictness dial is a penalty sweep: beta0.3 gives "
                f"six eras split at 2009, 2010, 2014, 2023 and 2024; beta0.6 gives "
                f"four; beta1.0 gives three; beta4.0 gives two split at 2023; beta14 "
                f"and up give one, so six loosen to two exactly. The single strongest "
                f"fault in the whole system is the {sf0['year']} {sf0_noun} break at "
                f"about {sf0['posterior']}, and the mystery year, 2023, shows up as the "
                f"strongest break in scoring at about {run2023_post}. The six-rate "
                f"ladder ran "
                f"{six_ladder} across 2008 to 2026, and runs an over ran {rpo_ladder}. "
                f"The teaser called the six-hitting break a clean 2018; the record "
                f"shows the dominant six break is 2014 with 2018 a real second "
                f"station, so the copy ships 2014, then 2018. These are the years the "
                f"data itself marks, drawn at their real strength, never dressed up as "
                f"certainties. The changepoint, the penalty and the posterior are the "
                f"technical names."
            ),
        },
        "ch10-bridge": {
            "text": (
                f"The league's batting strike rate rose from {bridge['league_sr_2023']} "
                f"in 2023 to {bridge['league_sr_2024']} in 2024, a jump of "
                f"{bridge['jump']} runs per 100 balls. Of the batters who faced at "
                f"least {bridge['bridge_min_balls']} balls in both seasons, "
                f"{bridge['n_bridge']} of them, held against themselves the average "
                f"change was about {bridge['within_mean']:+.1f} and the pooled change "
                f"about {bridge['within_pooled']:+.1f}, so the same players got a "
                f"little faster but not much. Of the {ss['total']:+.2f}, about "
                f"{ss['within']:+.2f} came from the same players improving and about "
                f"{ss['turnover']:+.2f} from turnover, new faces plus old faces in new "
                f"roles minus who left, so within-player is about a third "
                f"({ss['within_pct']}%) and turnover about two-thirds "
                f"({ss['turnover_pct']}%). On a stricter qualified set the turnover "
                f"share rises toward three-quarters, so the copy ships about "
                f"two-thirds to three-quarters. The within-player figure is a "
                f"survivors-only statistic, the batters present in both seasons, a "
                f"favourably-selected cohort, so a gain of only "
                f"{bridge['within_pooled']:+.1f} is if anything an upper bound, which "
                f"if corrected only strengthens the two-thirds-turnover conclusion. "
                f"The teaser said about +2.3 within and roughly three-quarters "
                f"turnover; the recount gives about {bridge['within_pooled']:+.1f} "
                f"within and about two-thirds turnover, so the copy ships two-thirds. "
                f"The rule that opened the door was graded in Chapter 7, the new faces "
                f"are the turnover measured here, and the decade of climbing skill is "
                f"the ignition curve of Chapter 1; all three did some of the work, "
                f"none of them caused it alone. The within-player and between-player "
                f"shift-share is the technical name."
            ),
        },
        "ch10-teleporter": {
            "text": (
                f"{seh['name']} in {seh['season']} faced {seh['balls']} balls for "
                f"{seh['runs']} runs, a strike rate of {seh['sr']}, when the league "
                f"scored {seh['league_sr_season']} per 100 balls. The naive way scales "
                f"that up by the ratio of league strike rates, giving about "
                f"{t24['naive']} in 2024 and about {t26['naive']} in 2026, a modern "
                f"ceiling near {seh['naive_ceiling']}. The honest way keeps him at the "
                f"rank he actually reached, about the {round(seh['percentile'])}th "
                f"place in 100 of 2008, giving about {t24['honest']} in 2024 and about "
                f"{t26['honest']} in 2026, so the naive figure overshoots the honest "
                f"one by about {round(t24['gap'])} in 2024 and about "
                f"{round(t26['gap'])} in 2026, because you cannot scale an outlier up. "
                f"The honest re-quote's uncertainty band is narrower than that gap, "
                f"its half-width {t26['band_halfwidth']} strictly less than the "
                f"{t26['gap']}-point 2026 gap, so the ghost sits clear above the band "
                f"and the overshoot is real. The teaser said the naive figure was "
                f"about 228; the record's league strike rates never rise high enough "
                f"for 228, so the naive ceiling ships as about "
                f"{seh['naive_ceiling']}. Measured against the going rate of its own "
                f"season, {mb[0]['name']} in {mb[0]['season']} scored {mb[0]['sr']} "
                f"and comes out {mb[0]['pct_above_par']}% above his year's par, while "
                f"{mb[1]['name']} in {mb[1]['season']} scored {mb[1]['sr']} and comes "
                f"out {mb[1]['pct_above_par']}% above his, so Gayle edges him despite a "
                f"raw strike rate about {teleporter['machine_b']['raw_sr_gap']} points "
                f"lower. The blueprint quoted era-relative z-scores of about +5.5 and "
                f"+5.2; those numbers were not reproducible on the record, they "
                f"recount to about +3.5 and +3.3 and even flip on some populations, so "
                f"the chapter drops the z entirely and ships a plain percent-above-par "
                f"gap. The league-ratio and percentile era translations and SR+ are "
                f"the technical names."
            ),
        },
        "ch10-convergence": {
            "text": (
                f"Runs an over ran {_seq(mens['recent']['rpo'], '{:.2f}')} across 2023 "
                f"to 2026; carrying the {mens['fit_window'][0]}-to-"
                f"{mens['fit_window'][1]} climb forward, the line crosses ten an over "
                f"around {mens['crosses_ten']['central']}, with a band of roughly "
                f"{mens['crosses_ten']['band_years'][0]} to "
                f"{mens['crosses_ten']['band_years'][1]} drawn as a bracket on the "
                f"time axis, and 2026 is already at {mens['today']['rpo']}, just below "
                f"ten in level. The women's league has four seasons of run rate, "
                f"{_seq(wrr['rpo'], '{:.2f}')}, a climb of about {wrr['slope']:+.2f} a "
                f"season, so its run rate is rising but the date carries a wide band; "
                f"measured against a fixed target it reaches the men's-2026 level of "
                f"about {wrr['mens_2026_level']} around "
                f"{round(wrr['reaches_mens_2026_level'])} on the central line. Its six "
                f"rate ran {_seq(wsr['six_per_over'], '{:.3f}')}, a slope "
                f"indistinguishable from flat, so on four seasons the six-hitting is "
                f"off the clock and reaching the men's 2026 level is not honestly "
                f"foreseeable, drawn with its target off-screen on purpose. The teaser "
                f"said the run rate converges about a decade before the six-hitting; "
                f"the recount holds the direction, run rate first, but the magnitudes "
                f"are far larger and far less certain, so the copy ships run rate "
                f"closes first and six-hitting is barely foreseeable on four seasons. "
                f"These are the trend carried forward, not a prophecy, and the bands "
                f"are drawn wide on purpose. The WPL is never behind; it is a young "
                f"league whose future you can already clock. Linear extrapolation and "
                f"slope are the technical names."
            ),
        },
        "ch10-microera": {
            "text": (
                f"When the machine scans the per-match series strictly it lands a "
                f"break at 2021, which looks like a mid-pandemic rule shift. It is "
                f"mostly geography. The 2021 men's season was split across two venues: "
                f"the India leg scored at {microera['india']['rr']} an over "
                f"({microera['india']['runs']:,} runs off "
                f"{microera['india']['legal_balls']:,} balls) and the UAE leg, on "
                f"slower pitches in a bio-bubble, at {microera['uae']['rr']} "
                f"({microera['uae']['runs']:,} off "
                f"{microera['uae']['legal_balls']:,}). So a chunk of the 2021 break in "
                f"the wide rate and the run rate is not a change in how the game was "
                f"played but a change in where it was played that season. We keep this "
                f"off the main flow because the hero story is the genuine staggered "
                f"breaks, not a venue artefact. A strict per-match changepoint at 2021 "
                f"attributable to leg composition is the technical detail."
            ),
        },
        "ch10-payoff": {
            "text": (
                "Your riser is the franchise batter whose own strike rate rose most "
                "across the 2023 fault, with an adaptation badge. The teleported "
                "legend is the franchise's signature player-season re-quoted the "
                "honest way to 2026, the rank-preserving figure and never the naive "
                "ghost. The climb position is the team's current run rate against the "
                "league's, stated as a position, not a ranking. A young franchise or a "
                "thin season carries a wide re-quote, which is a fact about its record, "
                "never a deficit. The WPL card is the forward-clock beat made "
                "personal, never a deficit card and never behind."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Document assembly + main
# ---------------------------------------------------------------------------


def build_doc(data_root: Path = canon.DATA_ROOT) -> dict:
    acc = build_ch10(data_root)
    seis = seismo.build_seismo()
    srplus_rows = par.build_docs(data_root)["srplus"]["batter_seasons"]

    ribbon = ribbon_section(acc, seis)
    seismograph = seismograph_section(acc, seis)
    faultmap = faultmap_section(acc, seis)
    bridge = bridge_section(acc)
    teleporter = teleporter_section(acc, srplus_rows)
    convergence = convergence_section(acc, seis)
    microera = microera_section(seis)
    payoff = payoff_section(acc, srplus_rows)
    footnotes = footnotes_section(ribbon, seismograph, faultmap, bridge, teleporter,
                                  convergence, microera)

    # release-blocking integrity check: the honest band never reaches the ghost
    for t in teleporter["machine_a"]["default"]["translations"]:
        assert t["band_lt_gap"], ("teleporter band>=gap", t)
    assert teleporter["machine_a"]["integrity"]["band_lt_gap"]

    doc = {
        "chapter": 10,
        "title": "The Era Machine",
        "register": "the synthesis, case closed honestly",
        "finale": True,
        "mystery_handoff_in": (
            "Last chapter left one question open. Was 2023 a genuinely new era, or "
            "just a louder version of the old game? For nine chapters we told you "
            "where the eras were. Now we let the data draw its own."
        ),
        "controlling_morph": {
            "name": "ribbon",
            "layout_code": 12,
            "new_buffer": None,
            "reverse": "ribbon -> free (C10-9, back to the cold-open free field)",
            "teleport_bit": 4,
            "note": (
                "Free field to the chronological ribbon: the 316,199 balls sort into "
                "one horizontal band ordered by when they were bowled. The ribbon is a "
                "pure function of position.x (the chronological point index) and the "
                "existing uInvN, so it adds no new per-point buffer and no 15th "
                "attribute; the field stays at 14. The fault-line cracks are "
                "scene-drawn SVG at getRibbonLayout().pointToX(ballPos); the strictness "
                "dial swaps a precomputed break-index set out of this JSON, never a "
                "live re-fit; the Teleporter lift rides the spare bit2 of the existing "
                "aRunOut byte. Three held scalars over the morph (teleportProgress, "
                "teleportLift, teleportOthersDim) plus two float uniforms "
                "(uRibbonBandY, uRibbonBandHalf), all inert by default so every prior "
                "release renders byte-identically."
            ),
        },
        "ribbon": ribbon,
        "seismograph": seismograph,
        "fault_map": faultmap,
        "bridge": bridge,
        "teleporter": teleporter,
        "convergence": convergence,
        "micro_era_2021": microera,
        "payoff": payoff,
        "footnotes": footnotes,
    }
    return doc


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    doc = build_doc()
    scenes_dir = out_root / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    raw = flatten.compact_json(doc, sort_keys=True)
    (scenes_dir / "ch10.json").write_bytes(raw)

    sizes = {
        "scenes/ch10.json": {"bytes_raw": len(raw),
                             "bytes_gz": len(flatten.gz_bytes(raw))},
    }
    meta_path = out_root / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta.setdefault("files", {}).update(sizes)
        meta_path.write_bytes(flatten.compact_json(meta))

    for name, s in sizes.items():
        print(f"  {name:18s} raw={s['bytes_raw']:>9,}  gz={s['bytes_gz']:>8,}")

    rb = doc["ribbon"]
    print(f"ch10 ribbon: {rb['total_points']:,} balls, {rb['n_matches_ipl']:,} IPL "
          f"matches, {rb['legal_deliveries_ipl']:,} legal deliveries")
    st = doc["seismograph"]["strictness"]
    print("ch10 strictness (composite dial):",
          " ".join(f"b{s['beta']}={s['n_eras']}era" for s in st["stops"]))
    br = doc["bridge"]
    print(f"ch10 bridge: SR {br['league_sr_2023']} -> {br['league_sr_2024']} "
          f"(+{br['jump']}); {br['n_bridge']} bridge; within {br['shift_share']['within']} "
          f"({br['shift_share']['within_pct']}%) turnover {br['shift_share']['turnover']} "
          f"({br['shift_share']['turnover_pct']}%)")
    tp = doc["teleporter"]
    seh = tp["machine_a"]["default"]
    t26 = next(t for t in seh["translations"] if t["year"] == 2026)
    print(f"ch10 teleporter: Sehwag {seh['sr']} -> naive {t26['naive']} / honest "
          f"{t26['honest']} (band+-{t26['band_halfwidth']} < gap {t26['gap']}); "
          f"Gayle +{tp['machine_b']['players'][0]['pct_above_par']}% vs FM "
          f"+{tp['machine_b']['players'][1]['pct_above_par']}% (raw gap "
          f"{tp['machine_b']['raw_sr_gap']})")
    cv = doc["convergence"]["mens"]["crosses_ten"]
    print(f"ch10 convergence: men cross ten ~{cv['central']} (band "
          f"{cv['band_years']}); WPL RR reaches men-2026 "
          f"~{doc['convergence']['wpl']['run_rate']['reaches_mens_2026_level']}")
    pv = doc["payoff"]["variants"]
    n_ipl = sum(1 for v in pv if v["league"] == "ipl")
    n_wpl = sum(1 for v in pv if v["league"] == "wpl")
    n_neu = sum(1 for v in pv if v["league"] == "neutral")
    print(f"ch10 payoff: {len(pv)} variants ({n_ipl} IPL + {n_wpl} WPL + {n_neu} neutral)")
    return doc


if __name__ == "__main__":
    main()
