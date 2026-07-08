"""R5a — Chapter 8 "The Captain's Brain" (the belief audit: report card FFFFP).

The one authoritative corpus pass for Chapter 8 (separate from scenes.py's Ch1-4
build and ch5/ch6/ch7.py so the R1-R4b scene bytes stay byte-identical). Stdlib
only, byte-deterministic (compact JSON, sorted keys, fixed-decimal rounding, the
momentum permutation nulls are drawn from fixed-seed local RNGs so two runs emit
identical bytes).

Emits web/static/data/scenes/ch8.json. The ONE controlling morph is the MATCH-DOTS
(free field -> 1,331 match centroids): every ball condenses to the centroid of its
match. It ships NO new per-point buffer — the field binary-searches a `match_bounds`
data texture (1,331 monotone block-start point indices in flatten point order,
emitted inline here) to resolve each ball's match id in-shader, holding the field at
14 vertex attributes. The 988 review deliveries fly out as a subset (reusing
aDismissal/aTeam/aRiverPos), so `review_subset` carries their point indices, team,
and outcome. Everything else (the toss crossover, spell strips, momentum needle-and-
band, required-rate curve, WPL adoption curves) is scene-authored 2D over the held
dots and just needs the numbers, tables, and geometry this JSON emits.

The register (glossary rule): on screen this is THE BELIEF AUDIT. Every belief is
GRADED, never caused. Stat terms of art (field-first share, batting-second win rate,
review success rate, permutation null, autocorrelation, shrinkage, expected value)
live one click deep in the footnotes; the main flow speaks fan language.

Report card (the shape): FAIL (toss), FAIL (reviews), FAIL (spells), FAIL-with-an-
honest-residual (momentum), PASS (required rate). Three honest deltas ship straight,
never fudged toward the teaser: the review success rate DEGRADED (32.8 -> 28.1, free
fall to 16.9 by 2026), the cold-return tax GREW (+0.16 -> +0.30, not "stable ~0.2"),
and momentum is a FAIL with a thin real residual that HOLDS steady (1.07 flat, only
the confounded raw edge 1.21 -> 1.16 fades). Plus the WPL is a two-season adoption
curve (54.5 -> ~100), analytics-native, never "behind".

What Ch8 puts on screen, all recounted (super overs excluded, flatten point order):

  match_dots     THE controlling morph: 1,331 match centroids (normalized x/y + toss
                 class + result) + match_bounds (block-start point indices) + the
                 season axis. 316,199 balls resolve to 1,331 matches (1,244 IPL + 89
                 WPL minus super-over exclusions).
  toss           HERO / FAIL: field-first 42.9 -> 77.1 while the chase never paid any
                 better (54.3, humped 59.6, back to 52.8); the crossover's two lines
                 that CROSS; toss-to-win ~50% every era.
  review         HERO / FAIL: 988 reviews, 292 upheld (29.6%); volume 1.26 -> 1.87 a
                 match at the 2022 doubling while the success rate FELL 32.8 -> 28.1,
                 a free fall to 16.9 by 2026. Plus review_subset (the 988 point
                 indices / team / outcome for the field chips).
  spell          SUPPORTING / FAIL: one-over-spell share 54.7 -> 64.1 (WPL 75.3), the
                 cold-return tax GREW +0.16 -> +0.30, and near-median example innings
                 as over-by-bowler strips.
  momentum       SUPPORTING / FAIL with an honest residual: the wicket myth collapses
                 (0.93, anti), and the hitting edge is mostly good batters batting
                 with a flat ~1.07 real sliver. All shuffle nulls precomputed here.
  required_rate  SUPPORTING / PASS: chase pacing genuinely flipped — powerplay 7.62
                 -> 9.19 (now above the middle overs), ahead-at-halfway 31.7 -> 37.5.
  wpl            the transmission beat: field-first 54.5 -> ~100 across two seasons,
                 reviews calibrated at 30.5 vs 29.6, out-fragments at 75.3.
  payoff         16 team cards (10 IPL "your captains' report card" + 5 WPL "born
                 into the analytics age" + neutral).
  footnotes      ch8-matchdots / toss / review / spell / momentum / required / wpl /
                 payoff / matchup (LED by the h2h-history growth 12.4 -> 42.1, Engine
                 #6) / dew. h2h is imported for the matchup footnote lead ONLY.
"""

from __future__ import annotations

import datetime
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten
import h2h  # imported for the demoted Matchup Engineering footnote lead ONLY

SCENES_DIR = canon.OUT_ROOT / "scenes"

# fixed seed for the momentum permutation nulls — byte-determinism (two runs of
# this pipeline must emit identical ch8.json). The plain and batter-stratified
# nulls each draw from their own fixed-seed RNG, mirroring the validated recount.
MOM_SEED = 20260707
N_PERM_PLAIN = 300
N_PERM_BATTER = 200

# ---------------------------------------------------------------------------
# Eras (the belief-audit bands; IPL five-band, WPL is the modern band only)
# ---------------------------------------------------------------------------

IPL_ERAS = ("2008-10", "2011-15", "2016-19", "2020-22", "2023-26")
# momentum is measured on three contrasting IPL eras + the WPL pooled
MOM_ERAS = ("2008-10", "2016-19", "2023-26")
# the required-rate curve is pinned to two contrasting eras; the rest footnote-only
REQ_PINNED = ("2008-10", "2023-26")


def era_of(season: int) -> str | None:
    if 2008 <= season <= 2010:
        return "2008-10"
    if 2011 <= season <= 2015:
        return "2011-15"
    if 2016 <= season <= 2019:
        return "2016-19"
    if 2020 <= season <= 2022:
        return "2020-22"
    if 2023 <= season <= 2026:
        return "2023-26"
    return None


def phase_of(over_no: int) -> str:
    return "pp" if over_no <= 5 else ("mid" if over_no <= 14 else "death")


def flags_for(dl: dict) -> tuple:
    """(is_boundary, is_six, is_dot, is_wicket) for one delivery."""
    rb = dl["runs"]["batter"]
    tot = dl["runs"]["total"]
    return (rb in (4, 6), rb == 6, tot == 0, bool(dl.get("wickets")))


# ---------------------------------------------------------------------------
# The one corpus pass
# ---------------------------------------------------------------------------


def build_ch8(data_root: Path = canon.DATA_ROOT) -> dict:
    """Single pass over the corpus in flatten's exact season-blocked point order.

    Maintains a global `point_index` incremented delivery-for-delivery exactly as
    flatten.build_stream does (super-over innings skipped identically), so every
    review `point_index` and every `match_bounds` block-start recorded here is the
    SAME field index the render's per-point buffers use.
    """
    # BELIEF 1 toss: per (league, season)
    toss = defaultdict(lambda: {
        "n": 0, "field": 0, "decided": 0, "chase_win": 0,
        "tosswin_matchwin": 0, "tosswin_decided": 0,
    })
    # BELIEF 2 reviews: per (league, season) + per team + the 988-delivery subset
    drs = defaultdict(lambda: {"rev": 0, "upheld": 0, "uc": 0, "type": 0})
    matches_per = defaultdict(int)
    drs_by_team = defaultdict(lambda: [0, 0])  # (league, canon team) -> [rev, upheld]
    review_indices = []  # IPL review-delivery point indices (ascending)
    review_team = []      # IPL franchise id of the reviewing team (-1 unknown)
    review_outcome = []   # 0 struck-down / 1 upheld
    # BELIEF 3 spells: per (league, season) -> [n_spells, n_one_over]
    spell = defaultdict(lambda: [0, 0])
    # cold-return tax: etag(league:era) -> over_no -> buckets. "p1" = every first-
    # of-spell over (the on-screen matched tax); "re" = strict cold re-entry only
    # (a bowler returning to an end they bowled earlier — the footnote's stricter
    # read); "cont" = continuation overs (spell position 2+).
    reentry = defaultdict(lambda: defaultdict(
        lambda: {"p1": [0, 0], "re": [0, 0], "cont": [0, 0]}))
    # spell exemplars: (era) -> list of qualifying near-full IPL innings
    spell_innings = defaultdict(list)
    # BELIEF 4 momentum: group -> list of (phases, batters, flags)
    mom = defaultdict(list)
    # BELIEF 5 required-rate: era -> phase -> [runs, legal_balls]
    chasepace = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    rrr_traj = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))
    ahead10 = defaultdict(lambda: [0, 0])
    # payoff: franchise home venues + per-match rows
    fr_venue = defaultdict(Counter)   # (league, team) -> Counter(raw venue)
    match_rows = []
    # match-dots: per match_index
    match_data = []   # {ord, toss, result, season, league, teams}
    match_bounds = []  # block-start point index per match_index

    point_index = -1
    for match_index, (_date, _mid, league, path) in enumerate(
        flatten.sorted_match_files(data_root)
    ):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        era = era_of(season)
        key = (league, season)
        matches_per[key] += 1
        match_bounds.append(point_index + 1)  # this match's first point index

        venue_raw = info["venue"]
        canon.canon_venue(venue_raw)  # exhaustiveness enforced at build time
        tinfo = info["toss"]
        decision = tinfo["decision"]
        toss_winner = canon.canon_team(tinfo["winner"])
        teams = [canon.canon_team(t) for t in info["teams"]]
        other = next((t for t in teams if t != toss_winner), toss_winner)
        outcome = info.get("outcome", {})
        winner = outcome.get("winner")
        winner = canon.canon_team(winner) if winner else None
        bat_first = toss_winner if decision == "bat" else other
        chase_team = other if decision == "bat" else toss_winner

        T = toss[key]
        T["n"] += 1
        if decision == "field":
            T["field"] += 1
        if winner is not None:
            T["decided"] += 1
            if winner == chase_team:
                T["chase_win"] += 1
            T["tosswin_decided"] += 1
            if winner == toss_winner:
                T["tosswin_matchwin"] += 1

        for t in teams:
            fr_venue[(league, t)][venue_raw] += 1
        match_rows.append({
            "league": league, "season": season, "venue": venue_raw,
            "teams": teams, "chase_team": chase_team, "bat_first": bat_first,
            "toss_winner": toss_winner, "decision": decision, "winner": winner,
        })

        # per-match-dot: toss class (0 bat-first upper / 1 field-first lower),
        # result (1 chase won / 0 bat-first won / -1 undecided)
        toss_class = 1 if decision == "field" else 0
        if winner is None:
            result_code = -1
        elif winner == chase_team:
            result_code = 1
        else:
            result_code = 0
        match_data.append({
            "ord": datetime.date.fromisoformat(str(info["dates"][0])).toordinal(),
            "toss": toss_class, "result": result_code,
            "season": season, "league": league,
        })

        innings_list = [
            inn for inn in match.get("innings", []) if not canon.is_super_over(inn)
        ]
        first_total = None
        for inn_idx, inn in enumerate(innings_list):
            batting_team = canon.canon_team(inn["team"])
            bowling_team = next((t for t in teams if t != batting_team), batting_team)
            collect_mom = (league == "ipl" and era in MOM_ERAS) or (league == "wpl")
            mom_group = "WPL" if league == "wpl" else era
            mom_phases, mom_batters, mom_flags = [], [], []
            over_seq = []       # [(over_no, bowler_name)] in bowling order
            over_runs = {}      # over_no -> total runs

            for over in inn["overs"]:
                over_no = over["over"]
                bowler0 = over["deliveries"][0]["bowler"]
                over_seq.append((over_no, bowler0))
                over_runs[over_no] = 0
                for ball_i, dl in enumerate(over["deliveries"]):
                    point_index += 1
                    over_runs[over_no] += dl["runs"]["total"]

                    # reviews (all leagues counted; IPL-only subset for the chips)
                    rv = dl.get("review")
                    if rv:
                        d = drs[key]
                        d["rev"] += 1
                        upheld = rv.get("decision") == "upheld"
                        if upheld:
                            d["upheld"] += 1
                        if "umpires_call" in rv:
                            d["uc"] += 1
                        if "type" in rv:
                            d["type"] += 1
                        by = rv.get("by")
                        bt = None
                        if by:
                            try:
                                bt = canon.canon_team(by)
                            except KeyError:
                                bt = None
                        if bt:
                            drs_by_team[(league, bt)][0] += 1
                            if upheld:
                                drs_by_team[(league, bt)][1] += 1
                        if league == "ipl":
                            review_indices.append(point_index)
                            review_team.append(
                                canon.team_id("ipl", bt) if bt else -1)
                            review_outcome.append(1 if upheld else 0)

                    if collect_mom:
                        mom_phases.append(phase_of(over_no))
                        mom_batters.append(dl["batter"])
                        mom_flags.append(flags_for(dl))

            # ----- spells (maximal same-end consecutive-over runs) -----
            ends = {0: [], 1: []}
            for ov, bw in over_seq:
                ends[ov % 2].append((ov, bw))
            spell_pos = {}          # over_no -> position within its spell (1-based)
            is_cold_reentry = {}    # over_no -> True if a strict cold re-entry
            n_spells = n_one = 0
            spell_list = []         # [(bowler_name, end, start_over, length)]
            for parity in (0, 1):
                seq = ends[parity]
                seen = set()
                i = 0
                while i < len(seq):
                    ov, bw = seq[i]
                    j = i
                    while j + 1 < len(seq) and seq[j + 1][1] == bw:
                        j += 1
                    length = j - i + 1
                    n_spells += 1
                    spell[key][0] += 1
                    if length == 1:
                        n_one += 1
                        spell[key][1] += 1
                    reent = bw in seen
                    for pos, (o2, _b2) in enumerate(seq[i:j + 1]):
                        spell_pos[o2] = pos + 1
                        is_cold_reentry[o2] = (pos == 0 and reent)
                    spell_list.append((bw, parity, ov, length))
                    seen.add(bw)
                    i = j + 1

            etag = ("wpl" if league == "wpl" else "ipl") + ":" + (era or "na")
            for ov, runs in over_runs.items():
                pos = spell_pos.get(ov, 1)
                bucket = reentry[etag][ov]
                if pos == 1:
                    bucket["p1"][0] += runs
                    bucket["p1"][1] += 1
                    if is_cold_reentry.get(ov):
                        bucket["re"][0] += runs
                        bucket["re"][1] += 1
                else:
                    bucket["cont"][0] += runs
                    bucket["cont"][1] += 1

            # near-median exemplar candidates (IPL momentum eras, near-full innings)
            n_overs = len(over_seq)
            if (league == "ipl" and era in MOM_ERAS and n_overs >= 18
                    and n_spells >= 6):
                spell_innings[era].append({
                    "match_index": match_index, "innings": inn_idx + 1,
                    "season": season, "batting_team": batting_team,
                    "bowling_team": bowling_team, "over_seq": over_seq,
                    "spells": spell_list, "n_spells": n_spells,
                    "n_one_over": n_one, "n_overs": n_overs,
                    "one_over_share": n_one / n_spells,
                })

            if collect_mom:
                mom[mom_group].append((mom_phases, mom_batters, mom_flags))

            # ----- required-rate (2nd innings, non-D/L, full 20-over target) -----
            if inn_idx == 0:
                first_total = sum(
                    dl["runs"]["total"] for over in inn["overs"]
                    for dl in over["deliveries"])
            if inn_idx == 1 and era is not None and not canon.is_dl(info):
                tgt = inn.get("target", {})
                tovers = tgt.get("overs")
                target_runs = tgt.get(
                    "runs", (first_total + 1) if first_total is not None else None)
                if tovers == 20 and target_runs:
                    over_cum = {}
                    cum = 0
                    for over in inn["overs"]:
                        ov = over["over"]
                        ph = phase_of(ov)
                        cp = chasepace[era][ph]
                        for dl in over["deliveries"]:
                            ex = dl.get("extras", {})
                            legal = not ("wides" in ex or "noballs" in ex)
                            cum += dl["runs"]["total"]
                            cp[0] += dl["runs"]["total"]
                            if legal:
                                cp[1] += 1
                        over_cum[ov] = cum
                    runs_before = {}
                    run_acc = 0
                    for over in inn["overs"]:
                        ov = over["over"]
                        runs_before[ov] = run_acc
                        run_acc += sum(
                            dl["runs"]["total"] for dl in over["deliveries"])
                    for k in range(20):
                        rb = runs_before.get(k)
                        if rb is None:
                            break
                        need = target_runs - rb
                        if need <= 0:
                            break
                        rrr_traj[era][k][0] += need / (20 - k)
                        rrr_traj[era][k][1] += 1
                    r10 = over_cum.get(9)
                    if r10 is not None:
                        ahead10[era][1] += 1
                        if r10 > target_runs / 2.0:
                            ahead10[era][0] += 1

    return {
        "n_points": point_index + 1,
        "n_matches": len(match_data),
        "toss": toss,
        "drs": drs,
        "matches_per": matches_per,
        "drs_by_team": drs_by_team,
        "review_indices": review_indices,
        "review_team": review_team,
        "review_outcome": review_outcome,
        "spell": spell,
        "reentry": reentry,
        "spell_innings": spell_innings,
        "mom": mom,
        "chasepace": chasepace,
        "rrr_traj": rrr_traj,
        "ahead10": ahead10,
        "fr_venue": fr_venue,
        "match_rows": match_rows,
        "match_data": match_data,
        "match_bounds": match_bounds,
    }


# ---------------------------------------------------------------------------
# Rounding + small helpers (mirror ch7)
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


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _era_pool(acc, league, band, field):
    """Pool a per-(league, season) toss/spell counter to an era band."""
    seasons = canon.IPL_SEASONS if league == "ipl" else canon.WPL_SEASONS
    out = 0
    for s in seasons:
        if era_of(s) == band:
            out += field((league, s))
    return out


# ---------------------------------------------------------------------------
# BELIEF 1 — the toss revolution (HERO, FAIL)
# ---------------------------------------------------------------------------


def toss_section(acc, match_dots) -> dict:
    toss = acc["toss"]

    def era_row(band):
        n = _era_pool(acc, "ipl", band, lambda k: toss[k]["n"])
        field = _era_pool(acc, "ipl", band, lambda k: toss[k]["field"])
        dec = _era_pool(acc, "ipl", band, lambda k: toss[k]["decided"])
        cw = _era_pool(acc, "ipl", band, lambda k: toss[k]["chase_win"])
        twm = _era_pool(acc, "ipl", band, lambda k: toss[k]["tosswin_matchwin"])
        twd = _era_pool(acc, "ipl", band, lambda k: toss[k]["tosswin_decided"])
        return {
            "era": band, "n": n, "decided": dec,
            "field_first": r1(pct(field, n)),
            "chase_win": r1(pct(cw, dec)),
            "tosswin_matchwin": r1(pct(twm, twd)),
        }

    eras = [era_row(b) for b in IPL_ERAS]
    per_season_ff = {
        str(s): r1(pct(toss[("ipl", s)]["field"], toss[("ipl", s)]["n"]))
        for s in canon.IPL_SEASONS if toss[("ipl", s)]["n"]
    }

    # captain-simulator lookup: per IPL season, the actual field-first share and the
    # trailing (through the prior season) batting-second win rate a chase-following
    # captain would have read off. A LOOKUP, not a live fit.
    captain_sim = []
    cum_cw = cum_dec = 0
    for s in canon.IPL_SEASONS:
        t = toss[("ipl", s)]
        if not t["n"]:
            continue
        trailing = r1(pct(cum_cw, cum_dec)) if cum_dec else None
        captain_sim.append({
            "season": s,
            "actual_field_first": r1(pct(t["field"], t["n"])),
            "trailing_chase_win": trailing,
        })
        cum_cw += t["chase_win"]
        cum_dec += t["decided"]

    # the belief-reality crossover: two era-level lines that CROSS, plotted over the
    # match-dots time axis (era x = the mean normalized-date of the era's IPL dots).
    era_x = match_dots["_era_x"]
    ff_line = [[era_x[b], era_row(b)["field_first"]] for b in IPL_ERAS]
    cw_line = [[era_x[b], era_row(b)["chase_win"]] for b in IPL_ERAS]
    crossing = None
    for i in range(len(IPL_ERAS) - 1):
        d0 = ff_line[i][1] - cw_line[i][1]
        d1 = ff_line[i + 1][1] - cw_line[i + 1][1]
        if d0 <= 0 <= d1 or d0 >= 0 >= d1:
            span = (d0 - d1)
            t = d0 / span if span else 0.0
            xc = ff_line[i][0] + t * (ff_line[i + 1][0] - ff_line[i][0])
            yc = ff_line[i][1] + t * (ff_line[i + 1][1] - ff_line[i][1])
            crossing = {
                "x": r4(xc), "pct": r1(yc),
                "between": [IPL_ERAS[i], IPL_ERAS[i + 1]],
            }
            break

    ys = [p[1] for p in ff_line + cw_line]

    return {
        "grade": "fail",
        "eras": eras,
        "per_season_field_first": per_season_ff,
        "crossover": {
            "field_first_line": ff_line,
            "chase_win_line": cw_line,
            "crossing_point": crossing,
            "y_domain": [40.0, 85.0],
            "y_observed": [r1(min(ys)), r1(max(ys))],
            "x_is_normalized_date": True,
            "note": (
                "Two lines that cross, drawn as the real data draws them: a CHOICE "
                "(how often captains chose to field) and a RESULT (how often the "
                "chase won). They are different kinds, not a subtractable gap; no "
                "shaded area between them."
            ),
        },
        "captain_sim": captain_sim,
        "headline": {
            "field_first_start": eras[0]["field_first"],
            "field_first_end": eras[-1]["field_first"],
            "chase_win_start": eras[0]["chase_win"],
            "chase_win_hump": eras[2]["chase_win"],
            "chase_win_end": eras[-1]["chase_win"],
            "field_first_2026": per_season_ff["2026"],
            "text": (
                "Captains went from choosing to field 43 in 100 to 77, while the "
                "chase won no more than it ever did: 54, up to a 60 in 100 hump in "
                "the late 2010s, then back to 53. The line that moved was the "
                "choice, not the result. Winning the toss itself: about 50/50, "
                "every era."
            ),
        },
        "wrinkle": (
            "The field-first surge landed in the one window the chase genuinely "
            "paid (2016-19, 59.6 in 100), then chasing decayed back to about 53 "
            "while the doctrine stayed locked at 77 to 82. The belief outlived its "
            "evidence."
        ),
        "definition": (
            "Field-first share = the share of tosses where the winner chose to bowl "
            "first. Batting-second win rate = the chase's win rate among decided "
            "matches. Toss-to-win = how often the toss winner won the match. This is "
            "a belief-versus-outcome mismatch, graded on the whole record; it is NOT "
            "a claim that the toss decides matches (it does not)."
        ),
    }


# ---------------------------------------------------------------------------
# BELIEF 2 — the review economics (HERO, FAIL) + the 988-chip subset
# ---------------------------------------------------------------------------

REVIEW_PRE = (2018, 2021)   # the pre-doubling window
REVIEW_POST = (2022, 2026)  # from the 2022 doubling of the allowance


def review_section(acc) -> dict:
    drs = acc["drs"]
    mp = acc["matches_per"]

    tot_rev = sum(drs[("ipl", s)]["rev"] for s in canon.IPL_SEASONS)
    tot_up = sum(drs[("ipl", s)]["upheld"] for s in canon.IPL_SEASONS)
    tot_uc = sum(drs[("ipl", s)]["uc"] for s in canon.IPL_SEASONS)
    tot_type = sum(drs[("ipl", s)]["type"] for s in canon.IPL_SEASONS)

    def window(lo, hi):
        rev = up = m = 0
        for s in canon.IPL_SEASONS:
            if lo <= s <= hi:
                rev += drs[("ipl", s)]["rev"]
                up += drs[("ipl", s)]["upheld"]
                m += mp[("ipl", s)]
        return rev, up, m

    pre_rev, pre_up, pre_m = window(*REVIEW_PRE)
    post_rev, post_up, post_m = window(*REVIEW_POST)

    per_season = {}
    for s in canon.IPL_SEASONS:
        d = drs[("ipl", s)]
        if d["rev"] == 0:
            continue
        m = mp[("ipl", s)]
        per_season[str(s)] = {
            "reviews": d["rev"], "upheld": d["upheld"],
            "upheld_pct": r1(pct(d["upheld"], d["rev"])),
            "per_match": r2(d["rev"] / m), "matches": m,
        }

    # per-team chip lanes (IPL): reviews / upheld / struck, ordered by lane
    per_team = []
    for tid, meta in enumerate(canon.TEAMS):
        if meta["league"] != "ipl":
            continue
        rev, up = acc["drs_by_team"][("ipl", meta["name"])]
        if rev == 0:
            continue
        per_team.append({
            "team": meta["name"], "team_id": tid, "short": meta["short"],
            "reviews": rev, "upheld": up, "struck": rev - up,
            "upheld_pct": r1(pct(up, rev)),
        })
    per_team.sort(key=lambda x: x["team_id"])

    leaderboard = sorted(
        [t for t in per_team if t["reviews"] >= 20],
        key=lambda x: (-x["upheld_pct"], x["team_id"]),
    )

    return {
        "grade": "fail",
        "total": tot_rev,
        "upheld": tot_up,
        "upheld_pct": r1(pct(tot_up, tot_rev)),
        "windows": {
            "pre": {
                "seasons": list(REVIEW_PRE), "reviews": pre_rev, "upheld": pre_up,
                "per_match": r2(pre_rev / pre_m), "upheld_pct": r1(pct(pre_up, pre_rev)),
            },
            "post": {
                "seasons": list(REVIEW_POST), "reviews": post_rev, "upheld": post_up,
                "per_match": r2(post_rev / post_m),
                "upheld_pct": r1(pct(post_up, post_rev)),
            },
            "volume_ratio_per_match": r2((post_rev / post_m) / (pre_rev / pre_m)),
        },
        "per_season": per_season,
        "per_team": per_team,
        "leaderboard": [
            {**t, "rank": i + 1} for i, t in enumerate(leaderboard)
        ],
        "schema": {
            "decisions": ["struck down", "upheld"],
            "umpires_call_present": tot_uc,
            "type_present": tot_type,
            "note": (
                "The record carries only two outcomes, 'struck down' (the on-field "
                "call stood) and 'upheld' (the call was overturned). A review-type "
                f"field is present on {tot_type} of {tot_rev} and is unreliable, so "
                f"it is kept out; the umpire's-call field is on only {tot_uc} of "
                f"{tot_rev} and is not used. Reviews exist from 2018 on only, so "
                "pre-2018 is no reviews, not missing data."
            ),
        },
        "headline": {
            "total": tot_rev, "upheld_pct": r1(pct(tot_up, tot_rev)),
            "per_match_pre": r2(pre_rev / pre_m), "per_match_post": r2(post_rev / post_m),
            "upheld_pct_pre": r1(pct(pre_up, pre_rev)),
            "upheld_pct_post": r1(pct(post_up, post_rev)),
            "upheld_pct_2026": per_season["2026"]["upheld_pct"],
            "text": (
                "988 reviews, only 30 in 100 overturned the call. Then in 2022 the "
                "league doubled the allowance: reviews jumped 1.3 to 1.9 a match, "
                "and the share that overturned the call FELL, 33 in 100 down to 28, "
                "and kept sliding to just 17 in 100 by 2026."
            ),
        },
        "honesty": (
            "The honest delta ships straight: the success rate got WORSE, not merely "
            "flat. But a falling share overturned is graded as the measured rate "
            "only; it is equally consistent with better on-field umpiring or more "
            "marginal reviews under the bigger allowance, so the copy never claims "
            "the reviewing judgment got dumber, and a struck-down review is never "
            "called 'wasted' (it still confirmed the on-field call)."
        ),
    }


def review_subset_section(acc) -> dict:
    idx = acc["review_indices"]
    unknown = sum(1 for t in acc["review_team"] if t < 0)
    return {
        "count": len(idx),
        "indices": idx,
        "team": acc["review_team"],
        "outcome": acc["review_outcome"],
        "unknown_team": unknown,
        "encoding": (
            "The 988 IPL review deliveries, in field POINT order (season-blocked, "
            "identical to group_ids.u16 / attrs.u8). Each carries the reviewing "
            "team's IPL franchise id (or -1 when the raw record omits who reviewed) "
            "and its outcome (0 = struck down / the call stood, 1 = upheld / paid "
            "off). field.setReviews bakes these into aDismissal (review code), aTeam "
            "(the chip-stack lane) and aRiverPos (the stack slot); no new per-point "
            "buffer. Green (upheld) is held apart from the WPL teal, the review-red "
            "(struck) apart from every team red, and the struck band is drawn darker "
            "so 'mostly dark = mostly the call stood' survives with no color."
        ),
    }


# ---------------------------------------------------------------------------
# BELIEF 3 — spell fragmentation + the cold-return tax (SUPPORTING, FAIL)
# ---------------------------------------------------------------------------


def _matched_tax(over_buckets, kind):
    """Over-number-matched run-rate tax (RPO): standardise the continuation-over
    run rate onto the first-of-spell over-number distribution, ≥5 overs a bin."""
    num = 0.0
    wsum = 0
    for ov in sorted(over_buckets):
        a = over_buckets[ov][kind]
        c = over_buckets[ov]["cont"]
        if a[1] >= 5 and c[1] >= 5:
            num += a[1] * (a[0] / a[1] - c[0] / c[1])
            wsum += a[1]
    return (num / wsum) if wsum else None


def _pick_near_median(cands, k=3):
    """The k innings whose one-over-spell share is nearest the era median (never
    the maximally-fragmented extreme). Deterministic tie-break on (match, innings)."""
    if not cands:
        return []
    shares = sorted(c["one_over_share"] for c in cands)
    n = len(shares)
    median = shares[n // 2] if n % 2 else 0.5 * (shares[n // 2 - 1] + shares[n // 2])
    ranked = sorted(
        cands,
        key=lambda c: (abs(c["one_over_share"] - median), c["match_index"], c["innings"]),
    )
    return ranked[:k], median


def _exemplar(inn):
    """One over-by-bowler strip: over_bowler[i] = bowler slot; fused per end."""
    slot = {}
    names = []
    over_bowler = []
    for _ov, bw in inn["over_seq"]:
        if bw not in slot:
            slot[bw] = len(names)
            names.append(bw)
        over_bowler.append(slot[bw])
    spells = [
        {"slot": slot[bw], "end": end, "start_over": start, "len": length}
        for (bw, end, start, length) in inn["spells"]
    ]
    return {
        "match_index": inn["match_index"], "innings": inn["innings"],
        "season": inn["season"], "batting_team": inn["batting_team"],
        "bowling_team": inn["bowling_team"], "n_overs": inn["n_overs"],
        "one_over_share": r3(inn["one_over_share"]),
        "n_spells": inn["n_spells"], "n_one_over": inn["n_one_over"],
        "over_bowler": over_bowler, "bowler_names": names, "spells": spells,
    }


def spell_section(acc) -> dict:
    spell = acc["spell"]

    def era_share(league, band):
        one = _era_pool(acc, league, band, lambda k: spell[k][1])
        tot = _era_pool(acc, league, band, lambda k: spell[k][0])
        return r1(pct(one, tot)), tot

    per_era = {}
    for band in IPL_ERAS:
        share, tot = era_share("ipl", band)
        per_era[band] = {"one_over_share": share, "spells": tot}
    wpl_share, wpl_tot = era_share("wpl", "2023-26")

    per_season = {}
    for s in canon.IPL_SEASONS:
        sp = spell[("ipl", s)]
        if sp[0]:
            per_season[str(s)] = r1(pct(sp[1], sp[0]))

    # cold-return tax (matched): on-screen = every first-of-spell over ("p1");
    # footnote strict = only true cold re-entries ("re"). WPL dropped (too thin).
    tax = {}
    for etag in ("ipl:2008-10", "ipl:2016-19", "ipl:2023-26"):
        buckets = acc["reentry"][etag]
        band = etag.split(":")[1]
        matched = _matched_tax(buckets, "p1")
        strict = _matched_tax(buckets, "re")
        tax[band] = {
            "matched": r2(matched) if matched is not None else None,
            "strict": r2(strict) if strict is not None else None,
        }

    # near-median exemplar strips (2-3 per era, "one example innings")
    exemplars = {}
    medians = {}
    for band in MOM_ERAS:
        picks, med = _pick_near_median(acc["spell_innings"][band], k=3)
        exemplars[band] = [_exemplar(inn) for inn in picks]
        medians[band] = r3(med)

    return {
        "grade": "fail",
        "per_era": per_era,
        "wpl": {"one_over_share": wpl_share, "spells": wpl_tot},
        "per_season": per_season,
        "ipl_span": {
            "start": per_season[str(canon.IPL_SEASONS[0])],
            "end": per_season[str(canon.IPL_SEASONS[-1])],
        },
        "cold_return_tax": tax,
        "exemplars": exemplars,
        "exemplar_medians": medians,
        "headline": {
            "one_over_start": per_era["2008-10"]["one_over_share"],
            "one_over_end": per_era["2023-26"]["one_over_share"],
            "wpl_one_over": wpl_share,
            "tax_start": tax["2008-10"]["matched"],
            "tax_end": tax["2023-26"]["matched"],
            "text": (
                "One-and-done overs, a bowler used for a single over then pulled, "
                "went from 55 in 100 to 64. And bringing a bowler back cold used to "
                "cost a sixth of a run an over; now it costs nearly a third. Rhythm "
                "captaincy dissolved into matchup chess."
            ),
        },
        "definition": (
            "A spell = a bowler's unbroken run of overs from one end (the laws "
            "forbid two in a row, so this is the consecutive-over run at one end). "
            "One-and-done = a one-over spell. The cold-return tax = the extra runs "
            "an over a bowler leaks on the first over of a spell, measured only "
            "against other bowlers bowling the same over number (≥5 overs a bin) so "
            "cheap early overs do not flatter the first spell. The on-screen tax is "
            "every first-of-spell over; the stricter read counts only true cold "
            "re-entries. Each strip is a NEAR-MEDIAN example innings, never a "
            "cherry-picked extreme. The WPL tax is dropped on screen (about zero, "
            "the over-matched bins are too thin for a stable read)."
        ),
    }


# ---------------------------------------------------------------------------
# BELIEF 4 — momentum (SUPPORTING, FAIL with an honest residual)
# ---------------------------------------------------------------------------

CLAIMS7 = ("bnd|bnd", "dot|dot", "six|six", "wkt|wkt", "wkt|bnd", "dot|wkt", "bnd|2dot")
CLAIMS4 = ("bnd|bnd", "six|six", "dot|dot", "wkt|wkt")
CLAIM_FAN = {
    "bnd|bnd": "a boundary after a boundary (hitting begets hitting)",
    "dot|dot": "a dot after a dot (pressure builds)",
    "six|six": "a six after a six (he is seeing it big)",
    "wkt|wkt": "a wicket after a wicket (a wicket brings a wicket)",
    "wkt|bnd": "a wicket after a boundary (the big shot brings the downfall)",
    "dot|wkt": "a dot after a wicket (the new batter is tentative)",
    "bnd|2dot": "a boundary after two dots (he breaks the shackles)",
}


def _mom_count(innings, claims):
    """Observed numerator/denominator per claim + the four marginal rates.

    innings = list of (phases, flags). Matches the validated recount exactly."""
    num = Counter()
    den = Counter()
    mb = ms = md = mw = 0
    N = 0
    two_dot = "bnd|2dot" in claims
    for phases, flags in innings:
        n = len(flags)
        for i in range(n):
            b, s, d, w = flags[i]
            mb += b
            ms += s
            md += d
            mw += w
            N += 1
        for i in range(1, n):
            pb, ps, pd, pw = flags[i - 1]
            b, s, d, w = flags[i]
            if pb:
                den["bnd|bnd"] += 1
                num["bnd|bnd"] += b
                den["wkt|bnd"] += 1
                num["wkt|bnd"] += w
            if pd:
                den["dot|dot"] += 1
                num["dot|dot"] += d
            if ps:
                den["six|six"] += 1
                num["six|six"] += s
            if pw:
                den["wkt|wkt"] += 1
                num["wkt|wkt"] += w
                den["dot|wkt"] += 1
                num["dot|wkt"] += d
        if two_dot:
            for i in range(2, n):
                if flags[i - 2][2] and flags[i - 1][2]:
                    den["bnd|2dot"] += 1
                    num["bnd|2dot"] += flags[i][0]
    marg = {"bnd": mb / N, "six": ms / N, "dot": md / N, "wkt": mw / N}
    return num, den, marg


def _base_for(claim, marg):
    return {
        "bnd|bnd": marg["bnd"], "dot|dot": marg["dot"], "six|six": marg["six"],
        "wkt|wkt": marg["wkt"], "wkt|bnd": marg["wkt"], "dot|wkt": marg["dot"],
        "bnd|2dot": marg["bnd"],
    }[claim]


def _histogram(values, lo, hi, nbins):
    counts = [0] * nbins
    w = (hi - lo) / nbins if hi > lo else 1.0
    for v in values:
        j = int((v - lo) / w) if w else 0
        if j < 0:
            j = 0
        elif j >= nbins:
            j = nbins - 1
        counts[j] += 1
    return counts


def _percentile(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    idx = p * (len(sorted_vals) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def _null_lifts(innings, claims, base, group_key, rng, n_perm):
    """Draw n_perm permutation-null conditional lifts per claim. group_key(i, phase,
    batter) selects the exchangeable block: phase (plain) or (phase, batter)."""
    prepped = []
    for phases, batters, flags in innings:
        groups = defaultdict(list)
        for i in range(len(flags)):
            groups[group_key(phases[i], batters[i])].append(i)
        prepped.append((phases, list(groups.values()), flags))
    out = {c: [] for c in claims}
    for _ in range(n_perm):
        shuffled = []
        for phases, blocks, flags in prepped:
            nf = list(flags)
            for idxs in blocks:
                vals = [flags[i] for i in idxs]
                rng.shuffle(vals)
                for i, v in zip(idxs, vals):
                    nf[i] = v
            shuffled.append((phases, nf))
        num, den, _ = _mom_count(shuffled, claims)
        for c in claims:
            out[c].append((num[c] / den[c]) / base[c] if den[c] and base[c] else 0.0)
    return out


def momentum_section(acc) -> dict:
    mom = acc["mom"]
    rng_plain = random.Random(MOM_SEED)
    rng_batter = random.Random(MOM_SEED)
    groups = ("2008-10", "2016-19", "2023-26", "WPL")

    claims_by_era = {}
    # summaries the copy leans on
    wkt_plain = {}
    bnd_raw = {}
    bnd_resid = {}
    six_resid = {}

    for g in groups:
        innings_pf = [(ph, fl) for (ph, _bt, fl) in mom[g]]
        num, den, marg = _mom_count(innings_pf, CLAIMS7)
        base = {c: _base_for(c, marg) for c in CLAIMS7}
        obs = {c: (num[c] / den[c] if den[c] else 0.0) for c in CLAIMS7}

        plain = _null_lifts(
            mom[g], CLAIMS7, base, lambda ph, bt: ph, rng_plain, N_PERM_PLAIN)
        batter = None
        if g in MOM_ERAS:
            batter = _null_lifts(
                mom[g], CLAIMS4, base, lambda ph, bt: (ph, bt),
                rng_batter, N_PERM_BATTER)

        rows = []
        for c in CLAIMS7:
            lift = obs[c] / base[c] if base[c] else 0.0
            pv = sorted(plain[c])
            pm = mean(pv)
            psd = (sum((x - pm) ** 2 for x in pv) / len(pv)) ** 0.5 if pv else 0.0
            pband = [_percentile(pv, 0.025), _percentile(pv, 0.975)]
            pclears = lift < pband[0] or lift > pband[1]

            bn = None
            if batter is not None and c in CLAIMS4:
                bv = sorted(batter[c])
                bm = mean(bv)
                bsd = (sum((x - bm) ** 2 for x in bv) / len(bv)) ** 0.5 if bv else 0.0
                bband = [_percentile(bv, 0.025), _percentile(bv, 0.975)]
                residual = lift / bm if bm else 0.0
                bclears = lift < bband[0] or lift > bband[1]
                bn = {"mean_lift": bm, "sd": bsd, "band": bband,
                      "residual": residual, "z": (lift - bm) / bsd if bsd else 0.0,
                      "clears": bclears, "vals": bv}

            # shared histogram range covering plain, batter, obs
            span = pv + (bn["vals"] if bn else []) + [lift]
            lo = min(span) - 0.02
            hi = max(span) + 0.02
            nbins = 28
            row = {
                "claim": c, "fan": CLAIM_FAN[c],
                "obs_pct": r2(100.0 * obs[c]), "base_pct": r2(100.0 * base[c]),
                "lift": r3(lift),
                "hist": {"lo": r4(lo), "hi": r4(hi), "nbins": nbins},
                "plain_null": {
                    "mean_lift": r3(pm), "sd": r3(psd),
                    "band": [r3(pband[0]), r3(pband[1])],
                    "z": r2((lift - pm) / psd) if psd else 0.0,
                    "clears": pclears,
                    "counts": _histogram(pv, lo, hi, nbins),
                },
            }
            if bn is not None:
                row["batter_null"] = {
                    "mean_lift": r3(bn["mean_lift"]), "sd": r3(bn["sd"]),
                    "band": [r3(bn["band"][0]), r3(bn["band"][1])],
                    "residual": r3(bn["residual"]), "z": r2(bn["z"]),
                    "clears": bn["clears"],
                    "counts": _histogram(bn["vals"], lo, hi, nbins),
                }
            rows.append(row)
            if c == "wkt|wkt":
                wkt_plain[g] = r3(lift)
            if c == "bnd|bnd":
                bnd_raw[g] = r3(lift)
                if bn is not None:
                    bnd_resid[g] = r3(bn["residual"])
            if c == "six|six" and bn is not None:
                six_resid[g] = r3(bn["residual"])
        claims_by_era[g] = rows

    # hero reconcile: boundary conditional vs base, 2008-10 -> 2023-26
    def find(g, c):
        return next(r for r in claims_by_era[g] if r["claim"] == c)

    hero = {
        "2008-10": {"obs": find("2008-10", "bnd|bnd")["obs_pct"],
                    "base": find("2008-10", "bnd|bnd")["base_pct"]},
        "2023-26": {"obs": find("2023-26", "bnd|bnd")["obs_pct"],
                    "base": find("2023-26", "bnd|bnd")["base_pct"]},
    }

    return {
        "grade": "fail",
        "claims_by_era": claims_by_era,
        "menu": [{"claim": c, "fan": CLAIM_FAN[c]} for c in CLAIMS7],
        "scripted": {"wicket_myth": "wkt|wkt", "hitting_sliver": "bnd|bnd"},
        "no_effect_line": 1.0,
        "summary": {
            "wicket_plain_lifts": wkt_plain,
            "boundary_raw_lifts": bnd_raw,
            "boundary_residuals": bnd_resid,
            "six_residuals": six_resid,
            "hero_reconcile": hero,
            "text": (
                "A wicket brings a wicket lands dead inside shuffled cricket, even "
                "on the wrong side of no-effect lately (0.93). Hitting begets "
                "hitting clears at first (1.16), but hold the same batter fixed and "
                "most of it was good batters batting: the real part is about 7 in "
                "100, and it has HELD steady season after season (1.07 flat). What "
                "shrank is the bigger raw number, and that was mostly good batters "
                "batting all along."
            ),
        },
        "definition": (
            "Each claim = how much likelier an outcome is right after another versus "
            "its baseline (1.0 = no effect). The band is that same measurement on "
            "the deliveries reshuffled thousands of times, first within an innings "
            "and its phase (plain), then also holding the batter fixed (the fuller "
            "shuffle that removes the good-batters-batting effect). The needle is "
            "green outside the band, grey inside. The residual = the observed edge "
            "over the batter-held band centre, drawn as a labeled bracket. All nulls "
            "are precomputed here (a lookup, not a client permutation)."
        ),
    }


# ---------------------------------------------------------------------------
# BELIEF 5 — required-rate responsiveness (SUPPORTING, PASS, saved for last)
# ---------------------------------------------------------------------------


def required_rate_section(acc) -> dict:
    cp = acc["chasepace"]
    phases = ("pp", "mid", "death")

    def rr(era, ph):
        runs, balls = cp[era][ph]
        return r2(6.0 * runs / balls) if balls else None

    by_era = {era: {ph: rr(era, ph) for ph in phases} for era in IPL_ERAS}

    def drift(era):
        r0 = acc["rrr_traj"][era][0]
        r10 = acc["rrr_traj"][era][10]
        d0 = r0[0] / r0[1] if r0[1] else 0.0
        d10 = r10[0] / r10[1] if r10[1] else 0.0
        return r2(d10 - d0)

    ahead = {
        era: r1(pct(acc["ahead10"][era][0], acc["ahead10"][era][1]))
        for era in REQ_PINNED
    }
    rrr_drift = {era: drift(era) for era in REQ_PINNED}

    curve = {era: [[i, by_era[era][ph]] for i, ph in enumerate(phases)]
             for era in REQ_PINNED}
    pp_jump = r2(by_era["2023-26"]["pp"] - by_era["2008-10"]["pp"])

    return {
        "grade": "pass",
        "phases": list(phases),
        "by_era": by_era,
        "pinned": list(REQ_PINNED),
        "curve": curve,
        "ahead_halfway": ahead,
        "rrr_drift": rrr_drift,
        "pp_jump": pp_jump,
        "headline": {
            "pp_2008": by_era["2008-10"]["pp"], "pp_2026": by_era["2023-26"]["pp"],
            "mid_2026": by_era["2023-26"]["mid"], "pp_jump": pp_jump,
            "ahead_2008": ahead["2008-10"], "ahead_2026": ahead["2023-26"],
            "text": (
                "Back in 2008 chases idled early and slammed the door at the death, "
                "an up-slope. Now they front-load: the powerplay jumped to over 9 an "
                "over, above the middle overs, and teams get ahead of the rate "
                "earlier, 32 in 100 at halfway up to 38. The one belief the record "
                "actually backs."
            ),
        },
        "caveat": (
            "The pass is on the pacing SHAPE, not on winning. The chase changed "
            "shape exactly as captains say, but chasing still wins about half the "
            "time (~53, flat, per Belief 1). 'Works' means the pacing changed, never "
            "that chasing wins more."
        ),
        "definition": (
            "Chase run rate by phase = all runs per 6 legal balls in the second "
            "innings, real chases only (non-rain-shortened, a full 20-over target). "
            "The death-over rates are conditioned on the chases that lasted that "
            "long, so the shape-flip leans on the powerplay jump (every chase faces "
            "it), not the death figure. Ahead-at-halfway = the share of chases past "
            "the going rate at the 10-over mark."
        ),
    }


# ---------------------------------------------------------------------------
# The WPL doctrine transmission (structural — analytics-native, never behind)
# ---------------------------------------------------------------------------


def wpl_section(acc, match_dots) -> dict:
    toss = acc["toss"]
    drs = acc["drs"]
    spell = acc["spell"]

    ff_by_season = {}
    curve = []
    season_x = match_dots["_wpl_season_x"]
    n_field = n_toss = n_cw = n_dec = 0
    for s in canon.WPL_SEASONS:
        t = toss[("wpl", s)]
        if not t["n"]:
            continue
        ff = r1(pct(t["field"], t["n"]))
        ff_by_season[str(s)] = {"field_first": ff, "matches": t["n"]}
        curve.append([season_x.get(s, 0.0), ff])
        n_field += t["field"]
        n_toss += t["n"]
        n_cw += t["chase_win"]
        n_dec += t["decided"]

    wrev = sum(drs[("wpl", s)]["rev"] for s in canon.WPL_SEASONS)
    wup = sum(drs[("wpl", s)]["upheld"] for s in canon.WPL_SEASONS)
    one = _era_pool(acc, "wpl", "2023-26", lambda k: spell[k][1])
    tot = _era_pool(acc, "wpl", "2023-26", lambda k: spell[k][0])

    season_one = ff_by_season[str(canon.WPL_SEASONS[0])]["field_first"]

    return {
        "field_first_by_season": ff_by_season,
        "field_first_pooled": r1(pct(n_field, n_toss)),
        "adoption_curve": curve,
        "chase_win_pooled": r1(pct(n_cw, n_dec)),
        "review": {"reviews": wrev, "upheld_pct": r1(pct(wup, wrev))},
        "one_over_share": r1(pct(one, tot)),
        "ipl_compare": {
            "field_first_settled": "77 to 82",
            "one_over_share": 64.1, "review_upheld_pct": 29.6,
        },
        "headline": {
            "season_one_field_first": season_one,
            "field_first_pooled": r1(pct(n_field, n_toss)),
            "review_upheld_pct": r1(pct(wup, wrev)),
            "one_over_share": r1(pct(one, tot)),
            "text": (
                "Season one, the women's league split the toss like the men's game "
                "did back in 2008, 55 in 100. Two seasons later nearly every captain "
                "fields first. Its reviews pay off at almost exactly the men's rate, "
                "31 in 100 to 30, and it deals overs even faster, 75 in 100. A "
                "league born into the analytics age, behaving like one from the "
                "start."
            ),
        },
        "framing": (
            "The WPL is analytics-native: it adopted the field-first doctrine on a "
            "fast two-season curve (54.5 to about 100), calibrates its reviews like "
            "the men's game, and out-fragments the modern men's game. It is a young "
            "league that already behaves like an analytics-native. The chase-win "
            "figure (59.8) is stated bare and un-caused; it is NOT "
            "'the doctrine works in the WPL'. Per-season match counts are carried so "
            "'100%' reads as a small single-season sample, not certainty."
        ),
    }


# ---------------------------------------------------------------------------
# Per-franchise payoff (16 cards) — "your captains' report card"
# ---------------------------------------------------------------------------


def _home_stats(acc, league, team):
    """Home ground + own field-first@home + chase-win@home (raw-venue home, the
    validated recount method)."""
    counter = acc["fr_venue"][(league, team)]
    if not counter:
        return None
    home_raw, apps = counter.most_common(1)[0]
    rows = [r for r in acc["match_rows"]
            if r["league"] == league and r["venue"] == home_raw and team in r["teams"]]
    tw_home = [r for r in rows if r["toss_winner"] == team]
    ff = sum(1 for r in tw_home if r["decision"] == "field")
    chased = [r for r in rows
              if r["chase_team"] == team and r["winner"] is not None]
    cw = sum(1 for r in chased if r["winner"] == team)
    return {
        "home_ground": canon.canon_venue(home_raw),
        "home_apps": apps,
        "field_first_at_home": {
            "pct": r1(pct(ff, len(tw_home))), "n": ff, "d": len(tw_home)},
        "chase_win_at_home": {
            "pct": r1(pct(cw, len(chased))), "n": cw, "d": len(chased)},
    }


def payoff_section(acc, review, wpl) -> dict:
    leaderboard = review["leaderboard"]
    rank_of = {t["team"]: t["rank"] for t in leaderboard}
    up_of = {t["team"]: t["upheld_pct"] for t in leaderboard}
    n_ranked = len(leaderboard)
    variants = []

    for team in canon.CURRENT_IPL_FRANCHISES:
        tid = canon.team_id("ipl", team)
        short = canon.TEAMS[tid]["short"]
        hs = _home_stats(acc, "ipl", team)
        rank = rank_of.get(team)
        up = up_of.get(team)
        ff = hs["field_first_at_home"]["pct"]
        cw = hs["chase_win_at_home"]["pct"]

        if short == "RCB":
            flavor = "The doctrine, embodied. And the best review eye in the league."
        elif short == "CSK":
            flavor = ("They bat first at Chepauk and let the spin bite. The "
                      "exception that ignores the doctrine.")
        elif short == "DC":
            flavor = f"Dead last on reviews. Just {round(up)} in 100 paid off."
        elif rank == 1:
            flavor = "The best review eye in the league."
        elif rank == n_ranked:
            flavor = "The worst review discipline in the league."
        else:
            lean = "field first" if ff >= 50 else "bat first"
            flavor = f"At home they lean {lean}."

        variants.append({
            "team": team, "team_id": tid, "short": short, "league": "ipl",
            "empty_state": False,
            "home_ground": hs["home_ground"],
            "field_first_at_home": hs["field_first_at_home"],
            "chase_win_at_home": hs["chase_win_at_home"],
            "review_rank": rank, "review_upheld_pct": up, "review_of": n_ranked,
            "flavor": flavor,
            "guard": (
                "These are two separate facts about your team, not cause and "
                "effect. And on about twenty home games, read them lightly."
            ),
            "headline": (
                f"{team}. Your captains' report card. At home your captains chose to "
                f"field first {round(ff)} in 100, and chasing at home won "
                f"{round(cw)} in 100. On reviews they rank {rank} of {n_ranked}."
            ),
        })

    # WPL cards: the analytics-native transmission beat made personal, never a
    # deficit card. All bespoke (they carry the shared transmission numbers).
    tr = wpl["headline"]
    for team in canon.WPL_FRANCHISES:
        tid = canon.team_id("wpl", team)
        short = canon.TEAMS[tid]["short"]
        hs = _home_stats(acc, "wpl", team)
        variants.append({
            "team": team, "team_id": tid, "short": short, "league": "wpl",
            "empty_state": False, "bespoke": True, "wpl_transmission": True,
            "home_ground": hs["home_ground"] if hs else None,
            "field_first_at_home": hs["field_first_at_home"] if hs else None,
            "chase_win_at_home": hs["chase_win_at_home"] if hs else None,
            "transmission": {
                "field_first_season_one": tr["season_one_field_first"],
                "field_first_pooled": wpl["field_first_pooled"],
                "review_upheld_pct": tr["review_upheld_pct"],
                "one_over_share": tr["one_over_share"],
            },
            "headline": (
                f"{team}. Born into the analytics age. Your league fielded first "
                f"{round(tr['season_one_field_first'])} in 100 in year one, then "
                f"nearly always in two seasons. The men's game took the better part "
                f"of a decade. Your reviews pay off at the men's rate, "
                f"{round(tr['review_upheld_pct'])} in 100, and you deal overs faster "
                f"than the men's game, {round(tr['one_over_share'])} in 100."
            ),
        })

    # neutral: the live league-wide report card
    ff_now = acc["_toss_eras"][-1]["field_first"]
    cw_now = acc["_toss_eras"][-1]["chase_win"]
    variants.append({
        "team": "Neutral", "team_id": None, "short": "NEU", "league": "neutral",
        "empty_state": False,
        "league_field_first": ff_now, "league_chase_win": cw_now,
        "league_review_upheld": review["upheld_pct"],
        "headline": (
            "The league's captains, graded. Across the whole league, captains chose "
            f"to field {round(ff_now)} in 100, the chase wins {round(cw_now)}, and "
            f"reviews pay off {round(review['upheld_pct'])}. Pick a team to see its "
            "own report card."
        ),
    })

    return {
        "card": "your-captains-report-card",
        "variants": variants,
        "leaderboard": leaderboard,
        "definition": (
            "Per franchise (10 IPL + 5 WPL + neutral). IPL cards: the home ground is "
            "the franchise's most-frequent participation venue; the home toss share "
            "is how often its own captains chose to field there; the home chase-win "
            "is its win rate batting second at home; the review rank is league-wide "
            "review success by franchise. WPL cards are the analytics-native "
            "transmission beat made personal, never a deficit card. Two separate "
            "facts, not cause and effect, on about twenty home games each."
        ),
    }


# ---------------------------------------------------------------------------
# Match-dots (THE controlling morph table) + season axis
# ---------------------------------------------------------------------------

GOLDEN = 0.6180339887498949


def match_dots_section(acc) -> dict:
    md = acc["match_data"]
    ords = [m["ord"] for m in md]
    lo, hi = min(ords), max(ords)
    span = (hi - lo) or 1

    centroids = []
    seasons = []
    leagues = []
    for i, m in enumerate(md):
        x = (m["ord"] - lo) / span
        # low-discrepancy vertical spread so the 1,331 dots form an even cloud;
        # dot size and brightness encode nothing (cognitive-design must-fix).
        y = ((i + 1) * GOLDEN) % 1.0
        centroids.append([r4(x), r4(y), m["toss"], m["result"]])
        seasons.append(m["season"])
        leagues.append(0 if m["league"] == "ipl" else 1)

    # season axis ticks (IPL) + per-era x + per-WPL-season x, from the same axis
    def norm(o):
        return (o - lo) / span

    season_ords = defaultdict(list)
    era_ords = defaultdict(list)
    wpl_season_ords = defaultdict(list)
    for m in md:
        if m["league"] == "ipl":
            season_ords[m["season"]].append(m["ord"])
            e = era_of(m["season"])
            if e:
                era_ords[e].append(m["ord"])
        else:
            wpl_season_ords[m["season"]].append(m["ord"])
    axis_ticks = [
        [s, r4(norm(mean(season_ords[s])))]
        for s in canon.IPL_SEASONS if season_ords[s]
    ]
    era_x = {e: r4(norm(mean(era_ords[e]))) for e in IPL_ERAS if era_ords[e]}
    wpl_season_x = {s: r4(norm(mean(wpl_season_ords[s])))
                    for s in canon.WPL_SEASONS if wpl_season_ords[s]}

    return {
        "count": len(md),
        "n_points": acc["n_points"],
        "centroids": centroids,
        "bounds": acc["match_bounds"],
        "season": seasons,
        "league": leagues,
        "axis_ticks": axis_ticks,
        "date_range": [
            datetime.date.fromordinal(lo).isoformat(),
            datetime.date.fromordinal(hi).isoformat(),
        ],
        "ipl_matches": sum(1 for m in md if m["league"] == "ipl"),
        "wpl_matches": sum(1 for m in md if m["league"] == "wpl"),
        "encoding": (
            "One dot, one whole match; 1,331 of them, the 316,199 balls resolved to "
            "their match centroid. centroids[i] = [x, y, toss_class, result]: x is "
            "the match's normalized start date (2008 left, 2026 right), y a fixed "
            "low-discrepancy spread (size and brightness encode NOTHING), toss_class "
            "0 = the toss winner batted first (upper lane) / 1 = chose to field "
            "(lower lane), result 1 = the chase won / 0 = the side batting first won "
            "/ -1 = undecided. bounds[i] = the block-start point index of match i in "
            "flatten point order (monotone non-decreasing) — the field binary-"
            "searches these in-shader to map each ball to its match, adding NO per-"
            "point attribute. Tap labels (teams, season, result) come from "
            "matches.json, which is in this same match order."
        ),
        # private helpers for the toss/wpl sections (stripped before emit)
        "_era_x": era_x,
        "_wpl_season_x": wpl_season_x,
    }


# ---------------------------------------------------------------------------
# Footnotes (ch8-* strings; numbers f-bound so they always match the artifact)
# ---------------------------------------------------------------------------


def footnotes_section(acc, sections, hist) -> dict:
    toss = sections["toss"]
    review = sections["review"]
    spell = sections["spell"]
    mom = sections["momentum"]
    req = sections["required_rate"]
    wpl = sections["wpl"]
    md = sections["match_dots"]

    e = {row["era"]: row for row in toss["eras"]}
    tax = spell["cold_return_tax"]

    def ff_seq():
        return ", ".join(f"{e[b]['field_first']}" for b in IPL_ERAS)

    def cw_seq():
        return ", ".join(f"{e[b]['chase_win']}" for b in IPL_ERAS)

    # usable head-to-head history (Engine #6): share of faced balls with >=12 prior
    # faced balls, per IPL season — the matchup footnote LEAD (the raw material grew).
    usable = {}
    for s in canon.IPL_SEASONS:
        rec = hist.get(("ipl", s))
        if rec and rec["balls"]:
            usable[str(s)] = r1(100.0 * rec["ge"][12] / rec["balls"])

    return {
        "ch8-matchdots": {
            "usable_by_season": None,
            "text": (
                f"Each match-dot is every ball of one match placed at its centroid, "
                f"with a small jitter disc so a match reads as one soft dot. Every "
                f"dot is drawn at the same radius and the same brightness, so a "
                f"run-heavy match is no bigger or brighter than a low-scoring one, "
                f"because nothing about a dot's size or glow is a stat. The "
                f"{md['n_points']:,} field balls resolve into {md['count']:,} "
                f"matches ({md['ipl_matches']:,} IPL plus {md['wpl_matches']} WPL, "
                f"minus the super-over exclusions), the same universe as every prior "
                f"chapter. Each match sits at its start date, so seasons read left "
                f"to right, and from here every belief re-poses this same cloud."
            ),
        },
        "ch8-toss": {
            "text": (
                f"Captains chose to field {ff_seq()} in 100 across the eras, while "
                f"the chase won {cw_seq()} in 100 over the same eras, and winning "
                f"the toss led to winning the match about half the time every era. "
                f"Per season the field-first share ran 55, 39, 35 in the first three "
                f"years, then broke at 2016 to the low 80s and never came back down "
                f"({toss['per_season_field_first']['2026']} in 2026). The honest "
                f"wrinkle: the field-first surge landed in the same window the chase "
                f"genuinely paid ({e['2016-19']['chase_win']} in 100, 2016-19), then "
                f"chasing decayed back to about 53 while the doctrine stayed locked "
                f"at 77 to 82, so the belief outlived its evidence. Sample sizes "
                f"{', '.join(str(e[b]['n']) for b in IPL_ERAS)} matches by era. This "
                f"is a belief-versus-outcome mismatch, not a claim the toss decides "
                f"matches. 'Field-first share' and 'batting-second win rate' are the "
                f"technical names. See also the Double-Header Dew Ledger (ch8-dew)."
            ),
        },
        "ch8-review": {
            "text": (
                f"{review['total']} reviews in all, {review['upheld']} of them "
                f"right, so {review['upheld_pct']} in 100 paid off. Before the 2022 "
                f"doubling, {review['windows']['pre']['reviews']} reviews at "
                f"{review['windows']['pre']['per_match']} a match and "
                f"{review['windows']['pre']['upheld_pct']} right; from 2022 on, "
                f"{review['windows']['post']['reviews']} at "
                f"{review['windows']['post']['per_match']} a match and "
                f"{review['windows']['post']['upheld_pct']} right. Per season the "
                f"hit rate fell "
                f"{', '.join(str(review['per_season'][str(s)]['upheld_pct']) for s in range(2022, 2027))} "
                f"across 2022 to 2026 (the 2026 count was "
                f"{review['per_season']['2026']['reviews']} reviews, so read the "
                f"last point as one noisy season, not certainty). The record holds "
                f"only two outcomes, 'struck down' (the call stood) and 'upheld' "
                f"(the call overturned); a review-type field is on barely half and "
                f"unreliable, the umpire's-call field on only {review['schema']['umpires_call_present']} "
                f"of {review['total']}. The honest delta: the success rate actively "
                f"fell, not merely stayed flat. A falling share is equally "
                f"consistent with better on-field umpiring or more marginal reviews "
                f"under the doubled allowance, so the grade is scoped to the "
                f"measured rate, never 'the reviewing got dumber'; a struck-down "
                f"review still confirmed the call and is not 'wasted'. 'Review "
                f"success rate' and 'upheld share' are the technical names."
            ),
        },
        "ch8-spell": {
            "text": (
                f"A spell is a bowler's unbroken run of overs from one end; because "
                f"the laws forbid two overs in a row, this is the consecutive-over "
                f"run at one end. One-and-done overs ran "
                f"{spell['per_era']['2008-10']['one_over_share']} in 2008-10, "
                f"{spell['per_era']['2016-19']['one_over_share']} in 2016-19, "
                f"{spell['per_era']['2023-26']['one_over_share']} in 2023-26, and "
                f"{spell['ipl_span']['start']} to {spell['ipl_span']['end']} season "
                f"to season; the WPL runs highest at {spell['wpl']['one_over_share']}. "
                f"The cold-return tax, measured only against other bowlers bowling "
                f"the same over number (at least five overs a bin), ran "
                f"{tax['2008-10']['matched']:+}, {tax['2016-19']['matched']:+}, "
                f"{tax['2023-26']['matched']:+} an over, or "
                f"{tax['2008-10']['strict']:+}, {tax['2016-19']['strict']:+}, "
                f"{tax['2023-26']['strict']:+} on the stricter cold-re-entry read. "
                f"The honest delta: the tax roughly doubled, from about a sixth of a "
                f"run to nearly a third, not the teaser's stable fifth. Each strip "
                f"is a near-median example innings, labeled 'one example innings', "
                f"chosen so the picture does not overstate the modest 9-point shift; "
                f"adjacent same-end same-bowler overs merge into one fused bar so a "
                f"spell reads by connectedness, not by telling bowler hues apart. "
                f"The WPL tax is dropped on screen (about zero, the over-matched "
                f"bins are too thin). See also the Matchup Engineering footnote "
                f"(ch8-matchup)."
            ),
        },
        "ch8-momentum": {
            "text": (
                f"Each claim is how much likelier an outcome is right after another "
                f"versus its baseline; the cloud is that same measurement on the "
                f"deliveries reshuffled thousands of times, first within an innings "
                f"and its phase, then also holding the batter fixed. A boundary "
                f"after a boundary runs "
                f"{mom['summary']['boundary_raw_lifts']['2008-10']}, "
                f"{mom['summary']['boundary_raw_lifts']['2016-19']}, "
                f"{mom['summary']['boundary_raw_lifts']['2023-26']} across the eras "
                f"and clears the plain shuffle; a six after a six runs far higher, "
                f"near 2 early; a dot after a wicket clears strongly, the one wicket "
                f"pattern that survives. But a wicket after a wicket runs "
                f"{mom['summary']['wicket_plain_lifts']['2008-10']}, "
                f"{mom['summary']['wicket_plain_lifts']['2016-19']}, then "
                f"{mom['summary']['wicket_plain_lifts']['2023-26']}, never clearing "
                f"and turning the wrong way. Hold the batter fixed and a boundary "
                f"after a boundary drops to a residual of about "
                f"{mom['summary']['boundary_residuals']['2008-10']}, "
                f"{mom['summary']['boundary_residuals']['2016-19']}, "
                f"{mom['summary']['boundary_residuals']['2023-26']}, holding FLAT "
                f"across the eras so the real part does not fade even as the raw "
                f"edge does; a six after a six sits about "
                f"{mom['summary']['six_residuals']['2023-26']} to "
                f"{mom['summary']['six_residuals']['2008-10']}, a thin but robust "
                f"sliver. A wicket after a wicket clears the fuller test only in the "
                f"2016-19 window and is null or reversed before and since, so the "
                f"myth grade is scoped to today's game. The belief as sold on "
                f"television is mostly a feeling: the wicket half is false, and most "
                f"of the hitting half is good batters batting, with a small real "
                f"sliver left. This is consistent with Collapse Contagion, the "
                f"aftershock read in Chapter 9. 'Permutation null', "
                f"'autocorrelation' and 'the batter-stratified null' are the "
                f"technical names."
            ),
        },
        "ch8-required": {
            "text": (
                f"Chase run rate by phase, powerplay then middle then death: "
                f"{req['by_era']['2008-10']['pp']}, {req['by_era']['2008-10']['mid']}, "
                f"{req['by_era']['2008-10']['death']} in 2008-10; "
                f"{req['by_era']['2016-19']['pp']}, {req['by_era']['2016-19']['mid']}, "
                f"{req['by_era']['2016-19']['death']} in 2016-19; "
                f"{req['by_era']['2023-26']['pp']}, {req['by_era']['2023-26']['mid']}, "
                f"{req['by_era']['2023-26']['death']} in 2023-26. The powerplay "
                f"jumped {req['pp_jump']:+} to sit above the middle overs, the shape "
                f"flipping from up-sloping to front-loaded. Read on real chases only "
                f"(second innings, non-rain-shortened, a full 20-over target); the "
                f"death rates are conditioned on the chases that lasted that long, "
                f"so the shape-flip leans on the powerplay jump. Teams ahead of the "
                f"going rate at the 10-over mark rose from {req['ahead_halfway']['2008-10']} "
                f"to {req['ahead_halfway']['2023-26']}. The pacing genuinely "
                f"changed, but it does not mean chasing wins more, which stayed flat "
                f"at about 53 per Belief 1, so the pass is on the pacing shape, not "
                f"the result. 'Required run rate' is the technical name."
            ),
        },
        "ch8-wpl": {
            "text": (
                f"The women's league chose to field "
                f"{', '.join(str(wpl['field_first_by_season'][str(s)]['field_first']) for s in canon.WPL_SEASONS if str(s) in wpl['field_first_by_season'])} "
                f"of the time across 2023 to 2026, pooling to {wpl['field_first_pooled']}, "
                f"almost exactly the men's pooled rate; the per-season match counts "
                f"were "
                f"{', '.join(str(wpl['field_first_by_season'][str(s)]['matches']) for s in canon.WPL_SEASONS if str(s) in wpl['field_first_by_season'])}, "
                f"so 100 in a season is a small sample, not certainty. Its reviews "
                f"paid off {wpl['review']['upheld_pct']} of the time across "
                f"{wpl['review']['reviews']} reviews, next to the men's "
                f"{wpl['ipl_compare']['review_upheld_pct']}; its one-and-done over "
                f"share was {wpl['one_over_share']}, above the modern men's "
                f"{wpl['ipl_compare']['one_over_share']}. The chase-win figure of "
                f"{wpl['chase_win_pooled']} is a bare fact and never caused, so it "
                f"must not read as the doctrine working in the WPL. The teaser said "
                f"the women's league inherited chase-first fully formed from season "
                f"one; the recount shows season one at "
                f"{wpl['headline']['season_one_field_first']}, about the men's 2008 "
                f"rate, then a hard two-season ramp to near 100, so the culture "
                f"arrived fast but it did arrive. The men's game took the better "
                f"part of a decade and settled around three-quarters, never reaching "
                f"the WPL's near-100, so no 'fifteen years to get there' claim is "
                f"made. The WPL is framed only as a league born into the analytics "
                f"age, arriving with the culture before the history. See also the "
                f"Double-Header Dew Ledger (ch8-dew)."
            ),
        },
        "ch8-payoff": {
            "text": (
                "The home ground is the franchise's most-frequent venue; the home "
                "toss share is how often its own captains chose to field there; the "
                "home chase-win is its win rate batting second at home; the review-"
                "discipline rank is league-wide review success by franchise. On "
                "about twenty home games each, the home toss share and the home "
                "chase-win are two separate facts, not cause and effect, so read "
                "them lightly. The review-discipline leaderboard runs best to worst "
                + ", ".join(
                    f"{t['short']} {t['upheld_pct']}"
                    for t in review["leaderboard"]
                )
                + ". The WPL card is the analytics-native beat made personal, never "
                "a deficit card. See also the Matchup Engineering footnote "
                "(ch8-matchup)."
            ),
        },
        "ch8-matchup": {
            "usable_by_season": usable,
            "text": (
                f"Lead with the raw material growing, not the score. How much head-"
                f"to-head history a captain has to work with exploded: the share of "
                f"balls where the batter and bowler had already faced each other at "
                f"least a dozen deliveries was {usable.get('2009')} in 2009, "
                f"{usable.get('2019')} by 2019, and about 32 after the 2022 "
                f"expansion diluted the pool with new teams "
                f"({usable.get('2023')}, {usable.get('2024')}, {usable.get('2025')} "
                f"across the recent seasons), more than tripling in a decade. The "
                f"score itself is weak: judged only on what was known before each "
                f"ball, captains landed on a best-third matchup about 30 in 100 "
                f"against 25 by luck, roughly 1.2 times, with no adoption ramp and "
                f"confounded by simpler pace-versus-spin and left-right logic, so we "
                f"do not put it on screen. Each pair's record is built with no "
                f"peeking (matches ordered by real date, a ball sees only "
                f"deliveries strictly before it; three snapshot tests confirm zero "
                f"lookahead on all 33,772 pairs), and a thin sample is pulled toward "
                f"the league average of 1.3322 runs a ball until a pair has earned "
                f"about 51 balls of weight. Empirical-Bayes shrinkage and the no-"
                f"lookahead ordering are the technical names."
            ),
        },
        "ch8-dew": {
            "text": (
                "Part of why captains choose to field is not belief at all, it is "
                "the weather. In day-night matches the evening dew makes the ball "
                "skid wet and hard to grip, so bowling second is genuinely harder, "
                "which is exactly why a captain who wins the toss puts the other "
                "side in and takes the chase. The Double-Header Dew Ledger tracks "
                "how much of the field-first surge sits in dew-prone evening slots "
                "and double-headers, and it grows with the schedule. We keep this "
                "off the main grade because it does not change the verdict (the "
                "chase-win rate stayed flat whether or not dew was in play), but it "
                "is the honest caveat on Belief 1: not every captain choosing to "
                "field is chasing a myth, some are just reading the sky. The WPL "
                "plays many day-night double-headers, so it is especially exposed to "
                "dew, part of why its field-first curve ramped so fast."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Document assembly + main
# ---------------------------------------------------------------------------


def build_doc(data_root: Path = canon.DATA_ROOT) -> dict:
    acc = build_ch8(data_root)

    match_dots = match_dots_section(acc)
    toss = toss_section(acc, match_dots)
    acc["_toss_eras"] = toss["eras"]  # neutral payoff reads the current-era row
    review = review_section(acc)
    review_subset = review_subset_section(acc)
    spell = spell_section(acc)
    momentum = momentum_section(acc)
    required = required_rate_section(acc)
    wpl = wpl_section(acc, match_dots)
    payoff = payoff_section(acc, review, wpl)

    hist = h2h.usable_history(data_root, thresholds=(12,))

    sections = {
        "match_dots": match_dots, "toss": toss, "review": review,
        "spell": spell, "momentum": momentum, "required_rate": required,
        "wpl": wpl,
    }
    footnotes = footnotes_section(acc, sections, hist)

    # strip the private layout helpers before emit
    match_dots = {k: v for k, v in match_dots.items() if not k.startswith("_")}

    return {
        "chapter": 8,
        "title": "The Captain's Brain",
        "register": "the belief audit",
        "report_card": {
            "shape": "four fails, one pass",
            "beliefs": [
                {"slot": 1, "name": "the toss revolution", "grade": "fail"},
                {"slot": 2, "name": "the review economics", "grade": "fail"},
                {"slot": 3, "name": "spell fragmentation", "grade": "fail"},
                {"slot": 4, "name": "momentum", "grade": "fail",
                 "note": "fail with an honest residual"},
                {"slot": 5, "name": "required-rate responsiveness", "grade": "pass"},
            ],
        },
        "mystery_handoff_in": (
            "Last chapter, one rule rewired the game. Learning is what modern "
            "franchises do. So let's audit everything else captains learned."
        ),
        "mystery_handoff_out": (
            "Beliefs churn, and a whole doctrine can arrive and die inside a "
            "broadcast cycle. But underneath the churn some things refuse to move. "
            "Next chapter, we find what stays."
        ),
        "controlling_morph": {
            "name": "match-dots",
            "reuses_buffer": "match_bounds data texture (no new per-point attribute)",
            "note": (
                "Free field to the 1,331 match-dots: every ball condenses to its "
                "match centroid. The field binary-searches match_dots.bounds "
                "in-shader to resolve each ball's match id, holding at 14 vertex "
                "attributes. matchSplit lifts each dot into its toss lane; the 988 "
                "review chips fly out reusing aDismissal/aTeam/aRiverPos. No new "
                "per-point buffer."
            ),
        },
        "match_dots": match_dots,
        "toss": toss,
        "review": review,
        "review_subset": review_subset,
        "spell": spell,
        "momentum": momentum,
        "required_rate": required,
        "wpl": wpl,
        "payoff": payoff,
        "footnotes": footnotes,
    }


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    doc = build_doc()
    out_root.mkdir(parents=True, exist_ok=True)
    scenes_dir = out_root / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    raw = flatten.compact_json(doc, sort_keys=True)
    (scenes_dir / "ch8.json").write_bytes(raw)
    sizes = {
        "scenes/ch8.json": {
            "bytes_raw": len(raw),
            "bytes_gz": len(flatten.gz_bytes(raw)),
        }
    }

    meta_path = out_root / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta.setdefault("files", {}).update(sizes)
        meta_path.write_bytes(flatten.compact_json(meta))

    for name, s in sizes.items():
        print(f"  {name:18s} raw={s['bytes_raw']:>9,}  gz={s['bytes_gz']:>8,}")
    md = doc["match_dots"]
    print(f"ch8 match-dots: {md['count']:,} matches from {md['n_points']:,} balls "
          f"(IPL {md['ipl_matches']:,} + WPL {md['wpl_matches']})")
    t = doc["toss"]["headline"]
    print(f"ch8 toss FAIL: field-first {t['field_first_start']} -> "
          f"{t['field_first_end']}; chase-win {t['chase_win_start']} -> "
          f"{t['chase_win_hump']} -> {t['chase_win_end']}")
    rv = doc["review"]["headline"]
    print(f"ch8 review FAIL: {rv['total']} reviews {rv['upheld_pct']}% upheld; "
          f"{rv['per_match_pre']} -> {rv['per_match_post']}/match, "
          f"{rv['upheld_pct_pre']}% -> {rv['upheld_pct_post']}% -> "
          f"{rv['upheld_pct_2026']}% (2026); subset {doc['review_subset']['count']}")
    sp = doc["spell"]["headline"]
    print(f"ch8 spell FAIL: one-over {sp['one_over_start']} -> {sp['one_over_end']} "
          f"(WPL {sp['wpl_one_over']}); cold-return tax {sp['tax_start']:+} -> "
          f"{sp['tax_end']:+}")
    ms = doc["momentum"]["summary"]
    print(f"ch8 momentum FAIL+residual: wicket {ms['wicket_plain_lifts']['2023-26']} "
          f"(anti); boundary raw {ms['boundary_raw_lifts']['2008-10']} -> "
          f"{ms['boundary_raw_lifts']['2023-26']}; residual FLAT "
          f"{ms['boundary_residuals']['2008-10']}/{ms['boundary_residuals']['2016-19']}"
          f"/{ms['boundary_residuals']['2023-26']}")
    rq = doc["required_rate"]["headline"]
    print(f"ch8 required PASS: PP {rq['pp_2008']} -> {rq['pp_2026']} (above mid "
          f"{rq['mid_2026']}); ahead-at-half {rq['ahead_2008']} -> {rq['ahead_2026']}")
    w = doc["wpl"]["headline"]
    print(f"ch8 WPL: field-first season-one {w['season_one_field_first']} -> pooled "
          f"{w['field_first_pooled']}; reviews {w['review_upheld_pct']}%; one-over "
          f"{w['one_over_share']}%")
    n_pay = len(doc["payoff"]["variants"])
    n_wpl = sum(1 for v in doc["payoff"]["variants"] if v["league"] == "wpl")
    n_ipl = sum(1 for v in doc["payoff"]["variants"] if v["league"] == "ipl")
    print(f"ch8 payoff: {n_pay} variants ({n_ipl} IPL + {n_wpl} WPL + 1 neutral)")
    return doc


if __name__ == "__main__":
    main()
