"""R4b — Chapter 7 "The Twelfth Man" (the Impact Player rule as a natural experiment).

The one authoritative corpus pass for Chapter 7 (separate from scenes.py's Ch1-4
build, ch5.py and ch6.py so the R1-R4a scene bytes stay byte-identical). Stdlib
only, byte-deterministic (compact JSON, sorted keys, fixed-decimal rounding).

Emits web/static/data/scenes/ch7.json. The controlling morph is the TWIN RIVERS
(IPL vs WPL run-rate flows built from the balls themselves, reusing the existing
per-point group_ids.u16 / attrs.u8 — no new per-point buffer). The hero
subset-highlight — the deliveries carrying Impact-sub events — ships as a COMPACT
INDEX LIST inside this JSON (`impact_subs.spark_indices`, in field point order),
because the Impact Player substitution lives in the raw match JSON `replacements`
field, which the shipped columnar dataset does NOT carry (unlike Ch 2/3/4's
run-out / dismissal-kind / first-innings membership, which the client derives from
columnar arrays via setRunouts / setDismissals / setFirstInnings). So Ch 7's
membership MUST come from the pipeline; the index list is the Ch 5 over-rail /
Ch 6 star-table precedent (a small lookup in the scene JSON, not a new buffer).

The hero framing (glossary rule): on screen this leads as "the control group";
"diff-in-diff" lives one click deep in the footnote. The WPL is the control arm —
a league with no Impact Player rule whose slower, rule-free trend is what makes
the IPL's discontinuity readable at all.

What Ch7 puts on screen, all recounted by tests/test_r4b.py against an
independent recompute:

  natural_experiment  the hero: IPL run rate per season (range-bound 7.5-8.7 for
                      2008-2022, then 8.99 -> 9.56 -> 9.63 -> 9.88 from the exact
                      season of the rule) vs the WPL's rule-free 8.08 -> 8.54 over
                      the same window (+0.46). The diff-in-diff estimate (~+0.9
                      RPO) with its honest caveats. RR = all runs / legal balls
                      (extras included; wides + no-balls excluded from the
                      denominator) — identical to ch6's maturity clock, so the two
                      chapters' WPL run rates agree by construction.
  license_index       at identical match states (>=4 wickets down, overs 7-16) SR
                      pre-rule (2020-2022) vs post-rule (2023-2026): 116.8 -> 129.9
                      while the dismissal rate held ~flat (4.88 -> 4.95 per 100
                      balls) — extra aggression at no material rise in risk. Plus
                      the by-position split: the top order took the license MOST
                      (positions 1-3 SR +18.0% vs +11.0% for 6-8).
  event_study         the placebo grid: for every candidate intervention season
                      2012-2025, a before/after level shift in IPL run rate (+ SE +
                      t), emitted whole so the placebo cursor is a LOOKUP. The true
                      2023 rule date stands out clean from the entire pre-rule
                      placebo cloud (2012-2022); the break then DEEPENS into 2024
                      as teams learn the rule (disclosed honestly — 2024's raw
                      magnitude edges 2023's).
  playbook            share of impact subs used at the innings break vs mid-innings,
                      per season: 51.8% (2023) -> 35.7% (2025) as teams held the
                      card for mid-innings strikes.
  impact_subs         the extraction: 556 Impact Player substitution events across
                      517 distinct deliveries (2023+), WPL 0 (no such rule); the
                      spark index list (the 517 deliveries carrying an event), the
                      bat-vs-bowl reinforcement split (256 bat / 300 bowl), per
                      season, and the per-franchise patterns.
  honest_null         the rule added a 12th name WITHOUT rewiring batting-order
                      thinking: entry entropy flat across the rule; the footnote
                      numbers (Tail Exposure ~flat, top-3 SR 131.5 -> 155.3,
                      Part-Timer bowlers per innings 5.79 -> 6.12).
  payoff              the 16 team cards (10 IPL "your team's playbook" + 5 WPL
                      "you are the control group" + neutral).
  footnotes           the replacements schema, the diff-in-diff confounds, and the
                      demoted Tail Exposure / Part-Timer beats.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten

SCENES_DIR = canon.OUT_ROOT / "scenes"

# --- eras (shared with the rest of the piece) ---------------------------------
RULE_SEASON = 2023  # the Impact Player rule's first IPL season
PRE_WINDOW = (2020, 2022)  # immediate pre-rule window (license + by-position)
POST_WINDOW = (2023, 2026)  # post-rule window
IPL_PRE_BAND = (2008, 2022)  # the 15-season range-bound band

# license-state definition: >= this many wickets down, over index in [lo, hi]
LICENSE_WKTS_MIN = 4
LICENSE_OVER_LO = 6  # over index 6 == the 7th over
LICENSE_OVER_HI = 15  # over index 15 == the 16th over ("overs 7-16")

# placebo event-study candidate intervention seasons (inclusive)
PLACEBO_LO = 2012
PLACEBO_HI = 2025
# the "placebo cloud" = every candidate date strictly before the rule; the true
# 2023 date must beat every one of them on the SIZE of the jump to "stand out".
PLACEBO_CLOUD_HI = RULE_SEASON - 1  # 2022
# local symmetric event-study window: K seasons each side of a candidate date
# (R4b audit must-fix #1 — replaces the confounded cumulative split).
WINDOW_K = 3

RETIRED_KINDS = frozenset({"retired hurt", "retired out", "retired not out"})
# dismissals NOT credited to the bowler (fielding / other) — excluded from the
# "bowler dismissal" view of the license risk footnote.
NON_BOWLER_KINDS = frozenset(
    {"run out", "obstructing the field", "retired hurt", "retired out",
     "retired not out", "hit the ball twice", "timed out"}
)


def in_window(season, window):
    return window[0] <= season <= window[1]


def period_of(season):
    if in_window(season, PRE_WINDOW):
        return "pre"
    if in_window(season, POST_WINDOW):
        return "post"
    return None


# ---------------------------------------------------------------------------
# The one corpus pass
# ---------------------------------------------------------------------------


def build_ch7(data_root: Path = canon.DATA_ROOT) -> dict:
    """Single pass over the corpus in flatten's exact season-blocked point order.

    Maintains a global `point_index` that increments delivery-for-delivery exactly
    as flatten.build_stream does (super-over innings skipped identically), so every
    impact-sub `point_index` recorded here is the SAME field index the render's
    per-point buffers use. Everything Chapter 7 needs is tallied in this one pass.
    """
    # run rate per (league, season)
    runs_total = defaultdict(int)
    legal = defaultdict(int)

    # impact-sub events (IPL only; the WPL has no such rule)
    impact_events = []  # dict per event, in point order
    spark_points = set()  # distinct point indices carrying >=1 impact event
    wpl_impact_events = 0

    # license index: period -> [batter_runs, legal_balls_faced, dismissals_all,
    #                           dismissals_bowler]
    lic = defaultdict(lambda: [0, 0, 0, 0])
    # by-position SR: (period, position) -> [batter_runs, legal_balls_faced]
    pos_sr = defaultdict(lambda: [0, 0])

    # playbook: season -> [at_break_events, mid_events]
    playbook = defaultdict(lambda: [0, 0])

    # honest null: entry-wickets-down entropy source: (league, season) ->
    # Counter(wickets_down_at_entry); per-player batting-position source too.
    entry_wkts = defaultdict(Counter)
    # tail exposure: period -> [innings_reaching_pos8, n_innings]
    tail = defaultdict(lambda: [0, 0])
    # top-3 SR: period -> [batter_runs, legal_balls_faced]
    top3 = defaultdict(lambda: [0, 0])
    # bowlers per innings: season -> [sum_distinct_bowlers, n_innings]
    bowlers_inn = defaultdict(lambda: [0, 0])

    # per-match outcome (for the per-franchise win correlation)
    match_winner = {}  # match_index -> canonical winner team name (or None)

    point_index = -1
    for match_index, (_date, _mid, league, path) in enumerate(
        flatten.sorted_match_files(data_root)
    ):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        outcome = info.get("outcome", {})
        winner = outcome.get("winner")
        match_winner[match_index] = canon.canon_team(winner) if winner else None
        per = period_of(season)

        innings_no = 0
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue  # standing rule: super overs never enter the stream
            innings_no += 1
            batting_team = canon.canon_team(innings["team"])
            key = (league, season)
            position = {}
            next_pos = 1
            wkts_down = 0
            distinct_bowlers = set()
            reached_pos8 = False
            for over in innings["overs"]:
                over_no = over["over"]
                for ball_i, dl in enumerate(over["deliveries"]):
                    point_index += 1
                    ex = dl.get("extras", {})
                    wide = "wides" in ex
                    noball = "noballs" in ex
                    rb = dl["runs"]["batter"]
                    tot = dl["runs"]["total"]
                    striker = dl["batter"]
                    nonst = dl["non_striker"]
                    distinct_bowlers.add(dl["bowler"])

                    # first-appearance batting position (super overs excluded);
                    # entry wickets-down recorded the first time a batter appears
                    for who in (striker, nonst):
                        if who not in position:
                            position[who] = next_pos
                            next_pos += 1
                            entry_wkts[key][wkts_down] += 1
                            if position[who] >= 8:
                                reached_pos8 = True
                    st_pos = position[striker]

                    runs_total[key] += tot
                    if not wide and not noball:
                        legal[key] += 1

                    # bowler-credited-or-not wickets on this ball (retired excluded)
                    wkts = [
                        w for w in dl.get("wickets", [])
                        if w.get("kind") not in RETIRED_KINDS
                    ]
                    n_all = len(wkts)
                    n_bowler = len(
                        [w for w in wkts if w.get("kind") not in NON_BOWLER_KINDS]
                    )

                    if league == "ipl" and per is not None:
                        # license state: >=4 down, overs 7-16
                        if (
                            LICENSE_OVER_LO <= over_no <= LICENSE_OVER_HI
                            and wkts_down >= LICENSE_WKTS_MIN
                        ):
                            lic[per][0] += rb
                            if not wide:
                                lic[per][1] += 1
                            lic[per][2] += n_all
                            lic[per][3] += n_bowler
                        # by-position SR + top-3 SR (all IPL states, balls faced)
                        if not wide:
                            pos_sr[(per, st_pos)][0] += rb
                            pos_sr[(per, st_pos)][1] += 1
                            if st_pos <= 3:
                                top3[per][0] += rb
                                top3[per][1] += 1

                    # wickets fall AFTER the ball -> wkts_down reflects the state
                    # the ball was bowled in (wickets already lost)
                    wkts_down += n_all

                    # impact-player substitutions (2023+; the raw replacements
                    # field). reason == "impact_player" only — concussion / role
                    # subs excluded.
                    for item in dl.get("replacements", {}).get("match", []):
                        if item.get("reason") != "impact_player":
                            continue
                        if league != "ipl":
                            wpl_impact_events += 1
                            continue
                        # bat reinforcement iff the sub's team is the batting side
                        # at activation (they walked in to bat); else bowl
                        # reinforcement (they came on / were added to bowl).
                        sub_team = canon.canon_team(item["team"])
                        reinforce = "bat" if sub_team == batting_team else "bowl"
                        at_break = over_no == 0 and ball_i == 0
                        impact_events.append(
                            {
                                "point_index": point_index,
                                "match_index": match_index,
                                "season": season,
                                "team": sub_team,
                                "in": item["in"],
                                "out": item["out"],
                                "innings_no": innings_no,
                                "over": over_no,
                                "ball": ball_i,
                                "reinforce": reinforce,
                                "at_break": at_break,
                            }
                        )
                        spark_points.add(point_index)
                        playbook[season][0 if at_break else 1] += 1

            # per-innings tallies
            distinct = len(distinct_bowlers)
            bowlers_inn[season][0] += distinct
            bowlers_inn[season][1] += 1
            if league == "ipl" and per is not None:
                tail[per][0] += 1 if reached_pos8 else 0
                tail[per][1] += 1

    return {
        "n_points": point_index + 1,
        "runs_total": runs_total,
        "legal": legal,
        "impact_events": impact_events,
        "spark_points": spark_points,
        "wpl_impact_events": wpl_impact_events,
        "lic": lic,
        "pos_sr": pos_sr,
        "playbook": playbook,
        "entry_wkts": entry_wkts,
        "tail": tail,
        "top3": top3,
        "bowlers_inn": bowlers_inn,
        "match_winner": match_winner,
    }


# ---------------------------------------------------------------------------
# Rounding helpers (mirror ch6)
# ---------------------------------------------------------------------------


def r1(x):
    return round(x, 1)


def r2(x):
    return round(x, 2)


def r3(x):
    return round(x, 3)


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def season_rr(acc, league, season):
    return 6.0 * acc["runs_total"][(league, season)] / acc["legal"][(league, season)]


# ---------------------------------------------------------------------------
# Natural experiment (the hero — "the control group")
# ---------------------------------------------------------------------------


def natural_experiment_section(acc) -> dict:
    ipl_rr = {s: r2(season_rr(acc, "ipl", s)) for s in canon.IPL_SEASONS}
    wpl_rr = {s: r2(season_rr(acc, "wpl", s)) for s in canon.WPL_SEASONS}

    band_vals = [ipl_rr[s] for s in range(IPL_PRE_BAND[0], IPL_PRE_BAND[1] + 1)]
    post_vals = [ipl_rr[s] for s in range(POST_WINDOW[0], POST_WINDOW[1] + 1)]
    imm_vals = [ipl_rr[s] for s in range(PRE_WINDOW[0], PRE_WINDOW[1] + 1)]

    ipl_pre_band_mean = mean(band_vals)
    ipl_pre_imm_mean = mean(imm_vals)
    ipl_post_mean = mean(post_vals)
    # the WPL has no pre-rule seasons (born 2023) — its own first-to-last drift
    # over the SAME window stands in for the contemporaneous secular trend.
    wpl_start = wpl_rr[POST_WINDOW[0]]
    wpl_end = wpl_rr[POST_WINDOW[1]]
    wpl_delta = wpl_end - wpl_start

    d_ipl_band = ipl_post_mean - ipl_pre_band_mean
    d_ipl_imm = ipl_post_mean - ipl_pre_imm_mean
    did_band = d_ipl_band - wpl_delta
    did_imm = d_ipl_imm - wpl_delta

    return {
        "hero_name": "the control group",
        "ipl_rr": {str(s): ipl_rr[s] for s in canon.IPL_SEASONS},
        "wpl_rr": {str(s): wpl_rr[s] for s in canon.WPL_SEASONS},
        "ipl_pre_band": {
            "seasons": list(IPL_PRE_BAND),
            "min": min(band_vals),
            "max": max(band_vals),
            "mean": r2(ipl_pre_band_mean),
        },
        "ipl_post": {
            "seasons": list(POST_WINDOW),
            "values": post_vals,
            "mean": r2(ipl_post_mean),
        },
        "diff_in_diff": {
            "ipl_pre_band_mean": r2(ipl_pre_band_mean),
            "ipl_pre_immediate_mean": r2(ipl_pre_imm_mean),
            "ipl_post_mean": r2(ipl_post_mean),
            "ipl_delta_vs_band": r2(d_ipl_band),
            "ipl_delta_vs_immediate": r2(d_ipl_imm),
            "wpl_start": wpl_start,
            "wpl_end": wpl_end,
            "wpl_delta": r2(wpl_delta),
            "estimate": r2(did_band),
            "estimate_immediate": r2(did_imm),
            "level_gap_at_treatment": r2(ipl_post_mean - ipl_pre_band_mean),
        },
        "headline": {
            "ipl_post_sequence": post_vals,
            "wpl_change": r2(wpl_delta),
            "did": r2(did_band),
            "text": (
                "Fifteen seasons range-bound between 7.5 and 8.7. Then, from the "
                "exact year of the rule, IPL run rate went 8.99, 9.56, 9.63, "
                "9.88. The WPL, with no such rule, moved only 8.08 to 8.54 over "
                "the same window. About a run an over opened up at the treatment "
                "date, roughly +0.9 once you take out the WPL's own drift."
            ),
        },
        "definition": (
            "Run rate = all runs (extras included) per 6 legal balls (wides and "
            "no-balls excluded from the denominator) — identical to Chapter 6's "
            "maturity clock, so the two chapters' WPL numbers agree. The diff-in-"
            "diff estimate = the IPL's post-minus-pre change minus the WPL's "
            "contemporaneous change; the WPL has no pre-rule season, so its own "
            "2023->2026 drift stands in for the secular trend."
        ),
        "confounds": (
            "Evidence weight, not proof. Pitches and balls changed over the same "
            "window, batting intent had been drifting up since the 2018 six-rate "
            "break, and the WPL is an imperfect control (four seasons, no true "
            "pre-rule period). The rule opened the door; it is not the only thing "
            "that walked through it."
        ),
    }


# ---------------------------------------------------------------------------
# License index
# ---------------------------------------------------------------------------


def license_section(acc) -> dict:
    lic = acc["lic"]

    def state(per):
        r, b, w_all, w_bowl = lic[per]
        return {
            "sr": r1(100.0 * r / b) if b else None,
            "dismissals_per_100": r2(100.0 * w_all / b) if b else None,
            "bowler_dismissals_per_100": r2(100.0 * w_bowl / b) if b else None,
            "balls": b,
            "runs": r,
            "dismissals": w_all,
        }

    pre = state("pre")
    post = state("post")

    def bucket_sr(per, lo, hi):
        r = sum(acc["pos_sr"][(per, p)][0] for p in range(lo, hi + 1))
        b = sum(acc["pos_sr"][(per, p)][1] for p in range(lo, hi + 1))
        return (100.0 * r / b) if b else None

    by_position = {}
    for label, (lo, hi) in (("1-3", (1, 3)), ("6-8", (6, 8))):
        p = bucket_sr("pre", lo, hi)
        q = bucket_sr("post", lo, hi)
        by_position[label] = {
            "sr_pre": r1(p),
            "sr_post": r1(q),
            "pct_change": r1(100.0 * (q - p) / p),
        }

    return {
        "state": {
            "wickets_down_min": LICENSE_WKTS_MIN,
            "overs": [LICENSE_OVER_LO + 1, LICENSE_OVER_HI + 1],
            "pre_window": list(PRE_WINDOW),
            "post_window": list(POST_WINDOW),
        },
        "pre": pre,
        "post": post,
        "by_position": by_position,
        "headline": {
            "sr_pre": pre["sr"],
            "sr_post": post["sr"],
            "dismissals_pre": pre["dismissals_per_100"],
            "dismissals_post": post["dismissals_per_100"],
            "top_order_pct_change": by_position["1-3"]["pct_change"],
            "lower_order_pct_change": by_position["6-8"]["pct_change"],
            "text": (
                "At the same match state, four or more down in the middle overs, "
                "batters went from 116.8 to 129.9 runs per 100 balls after the "
                "rule while the rate they got out barely moved (4.88 to 4.95 per "
                "100 balls). Extra aggression at no real extra risk. The top "
                "order took the licence most: positions 1-3 lifted +18.0%, the "
                "lower order +11.0%."
            ),
        },
        "definition": (
            "Match state held identical: at least four wickets down, overs 7-16. "
            "Strike rate = batter runs per 100 legal balls faced. Dismissal rate "
            "= all non-retired dismissals per 100 legal balls at those states "
            "(the bowler-credited-only view is alongside). Pre-rule = 2020-2022, "
            "post-rule = 2023-2026. The by-position split is over all IPL states, "
            "batting position by first-appearance order."
        ),
        "honesty": (
            "The dismissal rate held essentially flat rather than falling — the "
            "honest read is aggression up at no material risk premium, not risk "
            "down."
        ),
    }


# ---------------------------------------------------------------------------
# Event study / placebo grid
# ---------------------------------------------------------------------------


def event_study_section(acc) -> dict:
    seasons = list(canon.IPL_SEASONS)
    first, last = seasons[0], seasons[-1]
    rr = {s: season_rr(acc, "ipl", s) for s in seasons}

    def var(vals, m):
        return sum((x - m) ** 2 for x in vals) / len(vals) if vals else 0.0

    def local_shift(c):
        # LOCAL symmetric window (fixes the confounded cumulative split, R4b audit
        # must-fix #1): the jump at candidate date c is the mean run rate over the
        # WINDOW_K seasons FROM c, minus the mean over the WINDOW_K seasons BEFORE c.
        # For a PLACEBO date (before the rule) the later window is capped at the
        # last pre-rule season (2022), so no made-up date can borrow the real
        # post-2023 surge (the standard placebo-in-time restriction). The true and
        # post-rule dates use the natural window that spans the rule. Result: every
        # pre-rule candidate genuinely sits low and flat, and the rule year's jump
        # clears the whole cloud (unlike the old cumulative metric, which rose
        # monotonically to meet the rule year).
        after_hi = last if c >= RULE_SEASON else PLACEBO_CLOUD_HI
        pre = [rr[s] for s in seasons if c - WINDOW_K <= s <= c - 1]
        post = [rr[s] for s in seasons if c <= s <= min(c + WINDOW_K - 1, after_hi)]
        mp, mq = mean(pre), mean(post)
        shift = mq - mp
        se = (
            math.sqrt(var(pre, mp) / len(pre) + var(post, mq) / len(post))
            if pre and post
            else 0.0
        )
        t = shift / se if se > 0 else 0.0
        return shift, se, t

    candidates = []
    for c in range(PLACEBO_LO, PLACEBO_HI + 1):
        shift, se, t = local_shift(c)
        candidates.append(
            {
                "season": c,
                "level_shift": r3(shift),
                "se": r3(se),
                "t": r2(t),
            }
        )

    by_season = {c["season"]: c for c in candidates}
    true = by_season[RULE_SEASON]
    cloud = [c for c in candidates if c["season"] <= PLACEBO_CLOUD_HI]
    cloud_max_shift = max(c["level_shift"] for c in cloud)
    cloud_max_t = max(c["t"] for c in cloud)
    # The on-screen quantity is the SIZE of the jump (runs an over): the rule year
    # stands out because its jump clears the whole pre-rule cloud. (t is emitted for
    # the footnote layer, but is not the discriminator — a flat-era candidate can
    # have a tiny window variance and so a large t on a small jump.)
    stands_out = true["level_shift"] > cloud_max_shift
    global_max = max(candidates, key=lambda c: c["level_shift"])
    gmax_date = global_max["season"]
    gmax_shift = global_max["level_shift"]
    true_shift = true["level_shift"]

    return {
        "candidates": candidates,
        "true_date": RULE_SEASON,
        "placebo_window": [PLACEBO_LO, PLACEBO_CLOUD_HI],
        "treatment_window": [RULE_SEASON, POST_WINDOW[1]],
        "true_date_shift": true_shift,
        "true_date_t": true["t"],
        "placebo_cloud_max_shift": cloud_max_shift,
        "placebo_cloud_max_t": cloud_max_t,
        "true_date_stands_out": stands_out,
        "global_max_shift_date": gmax_date,
        "global_max_shift": gmax_shift,
        "headline": {
            "true_shift": true_shift,
            "placebo_max_shift": cloud_max_shift,
            "text": (
                "Drag the date anywhere. Every year before the rule shows a jump of "
                f"at most about {cloud_max_shift:.2f} runs an over. The rule year, "
                f"2023, jumps {true_shift:.2f} and stands clear of the whole grey "
                f"cloud. The break then deepens into {gmax_date} as teams learn the "
                "card."
            ),
        },
        "definition": (
            "For each candidate year the jump is the mean IPL run rate over the "
            f"{WINDOW_K} seasons from that year, minus the mean over the "
            f"{WINDOW_K} before it (RR = all runs / legal balls). For a made-up "
            "date before the rule the later window stops at 2022, so no fake date "
            "can borrow the real post-2023 climb. The whole grid is precomputed so "
            "the placebo cursor is a lookup, never a live fit."
        ),
        "note": (
            "Honest read: the true rule date stands out clean from every pre-rule "
            "placebo (2012-2022). It is not the single largest jump — "
            f"{gmax_shift:.2f} in {gmax_date} edges 2023's {true_shift:.2f} because "
            "the run rate kept climbing as teams learned the rule, exactly the "
            "learning curve the playbook decoder shows. The break brackets "
            "2023-2024; the rule date is its leading edge."
        ),
    }


# ---------------------------------------------------------------------------
# Playbook decoder
# ---------------------------------------------------------------------------


def playbook_section(acc) -> dict:
    pb = acc["playbook"]
    per_season = {}
    for s in range(POST_WINDOW[0], POST_WINDOW[1] + 1):
        at_break, mid = pb[s]
        tot = at_break + mid
        per_season[str(s)] = {
            "at_break": at_break,
            "mid_innings": mid,
            "total": tot,
            "break_pct": r1(100.0 * at_break / tot) if tot else None,
        }
    return {
        "per_season": per_season,
        "headline": {
            "break_pct_2023": per_season["2023"]["break_pct"],
            "break_pct_2025": per_season["2025"]["break_pct"],
            "text": (
                "In 2023 teams used just over half their impact subs at the "
                "innings break. By 2025 that was down to a third — they learned "
                "to hold the card for a mid-innings strike."
            ),
        },
        "definition": (
            "At the innings break = the substitution is recorded on the first "
            "ball of an innings (over 0, ball 0); everything else is mid-innings. "
            "Counted per substitution event."
        ),
    }


# ---------------------------------------------------------------------------
# Honest null (batting-order fluidity + demoted footnotes)
# ---------------------------------------------------------------------------


def _entropy_bits(counter):
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counter.values() if c > 0)


def honest_null_section(acc) -> dict:
    # entry entropy: the spread of the point at which batters enter (wickets
    # already down) — a batting-order-fluidity measure. Dead flat across the rule.
    entry_by_season = {
        str(s): r3(_entropy_bits(acc["entry_wkts"][("ipl", s)]))
        for s in canon.IPL_SEASONS
    }
    pre_pool = Counter()
    for s in range(PRE_WINDOW[0], PRE_WINDOW[1] + 1):
        pre_pool.update(acc["entry_wkts"][("ipl", s)])
    post_pool = Counter()
    for s in range(POST_WINDOW[0], POST_WINDOW[1] + 1):
        post_pool.update(acc["entry_wkts"][("ipl", s)])
    entry_pre = _entropy_bits(pre_pool)
    entry_post = _entropy_bits(post_pool)

    # tail exposure (pos-8 reached), pre vs post
    def tail_rate(per):
        reached, n = acc["tail"][per]
        return r1(100.0 * reached / n) if n else None

    # top-3 SR
    def top3_sr(per):
        r, b = acc["top3"][per]
        return r1(100.0 * r / b) if b else None

    # part-timer: distinct bowlers per innings per season
    bowlers = {
        str(s): r2(acc["bowlers_inn"][s][0] / acc["bowlers_inn"][s][1])
        for s in canon.IPL_SEASONS
    }

    return {
        "entry_entropy": {
            "per_season": entry_by_season,
            "pre_pooled": r3(entry_pre),
            "post_pooled": r3(entry_post),
            "delta": r3(entry_post - entry_pre),
            "flat": abs(entry_post - entry_pre) < 0.1,
            "definition": (
                "Shannon entropy (bits) of the distribution of wickets-already-"
                "down at each batter's entry, per league-season — how spread out "
                "the batting order's entry points are. A rewired order would move "
                "it; the rule did not."
            ),
        },
        "tail_exposure": {
            "pre": tail_rate("pre"),
            "post": tail_rate("post"),
            "definition": (
                "Share of IPL innings in which the No. 8 batter came to the "
                "crease (batting position reached 8+), pre-rule (2020-2022) vs "
                "post-rule (2023-2026). The tail bats about as often as before."
            ),
        },
        "top3_sr": {
            "pre": top3_sr("pre"),
            "post": top3_sr("post"),
            "definition": (
                "Strike rate of batting positions 1-3, pre vs post. The change is "
                "in HOW the top order bats, not how often the tail is exposed."
            ),
        },
        "part_timer": {
            "per_season": bowlers,
            "pre_2022": bowlers["2022"],
            "post_2023": bowlers["2023"],
            "definition": (
                "Distinct bowlers used per innings, per season. The rule's other "
                "face: with a spare name to spend, teams reached for one more "
                "bowler the year it arrived (5.79 -> 6.12)."
            ),
        },
        "headline": {
            "entry_pre": r3(entry_pre),
            "entry_post": r3(entry_post),
            "text": (
                "The rule added a twelfth name without rewiring how teams think "
                "about the batting order. The entry order is as spread out as it "
                "always was. The top three jumped from 131.5 to 155.3, but the "
                "tail bats no more often. What changed is intent, not the running "
                "order."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Impact-sub extraction summary + the spark index list (the render's membership)
# ---------------------------------------------------------------------------


def impact_subs_section(acc) -> dict:
    events = acc["impact_events"]
    spark = sorted(acc["spark_points"])
    by_season = Counter(e["season"] for e in events)
    reinforce = Counter(e["reinforce"] for e in events)
    # distinct (match, team) substitution usages (rule = one sub per team/match)
    usages = {(e["match_index"], e["team"]) for e in events}

    return {
        "n_events": len(events),
        "n_spark_deliveries": len(spark),
        "n_sub_usages": len(usages),
        "wpl_events": acc["wpl_impact_events"],
        "by_season": {str(s): by_season[s] for s in sorted(by_season)},
        "reinforcement": {"bat": reinforce["bat"], "bowl": reinforce["bowl"]},
        "spark_indices": spark,
        "spark_encoding": (
            "spark_indices are field POINT indices (season-blocked point order, "
            "identical to group_ids.u16 / attrs.u8) of the 517 deliveries carrying "
            "at least one Impact Player substitution event. The render bakes them "
            "into a per-point spark flag once (the Ch 2 setRunouts / Ch 3 "
            "setDismissals precedent) to glow them as sparks entering the IPL "
            "river; no new per-point buffer is shipped. Two teams substituting on "
            "the same first-ball-of-innings-2 delivery is why 556 events map to "
            "517 distinct deliveries."
        ),
        "activation_note": (
            "An event is a raw-JSON match/impact_player replacement (2023+): the "
            "delivery where the substitution takes effect. Batting reinforcements "
            "are recorded on the ball the sub walks in for; bowling reinforcements "
            "at the start of the innings their team fields. Concussion and role "
            "substitutions are excluded. Reinforcement type = batting side at "
            "activation -> bat, fielding side -> bowl."
        ),
        "definition": (
            "556 Impact Player substitution events across 517 distinct deliveries "
            "(IPL 2023-2026); the WPL has no such rule, so 0 there — which is "
            "exactly what makes it the control arm."
        ),
    }


# ---------------------------------------------------------------------------
# Per-franchise playbook + the 16-card payoff
# ---------------------------------------------------------------------------


def _franchise_patterns(acc):
    """Per current-IPL-franchise impact-sub patterns for the payoff cards."""
    events = acc["impact_events"]
    winner = acc["match_winner"]
    # dedupe to one sub per (match, team): the earliest event by point index
    usage = {}
    for e in events:
        k = (e["match_index"], e["team"])
        if k not in usage or e["point_index"] < usage[k]["point_index"]:
            usage[k] = e

    per = {t: {
        "bat": 0, "bowl": 0, "break": 0, "mid": 0,
        "players": Counter(),
        "wins": {"bat": [0, 0], "bowl": [0, 0]},  # [wins, matches]
    } for t in canon.CURRENT_IPL_FRANCHISES}

    for (mi, team), e in usage.items():
        if team not in per:
            continue  # a defunct franchise never appears (all subs are 2023+)
        f = per[team]
        f[e["reinforce"]] += 1
        f["break" if e["at_break"] else "mid"] += 1
        f["players"][e["in"]] += 1
        won = 1 if winner.get(mi) == team else 0
        f["wins"][e["reinforce"]][0] += won
        f["wins"][e["reinforce"]][1] += 1
    return per


def payoff_section(acc) -> dict:
    patterns = _franchise_patterns(acc)
    variants = []

    for team in canon.CURRENT_IPL_FRANCHISES:
        tid = canon.team_id("ipl", team)
        f = patterns[team]
        total = f["bat"] + f["bowl"]
        top_player, top_count = f["players"].most_common(1)[0]
        favorite = "bat" if f["bat"] >= f["bowl"] else "bowl"
        fav_word = "batting" if favorite == "bat" else "bowling"

        def win_rate(kind):
            w, m = f["wins"][kind]
            return r1(100.0 * w / m) if m else None

        variants.append(
            {
                "team": team,
                "team_id": tid,
                "short": canon.TEAMS[tid]["short"],
                "league": "ipl",
                "empty_state": False,
                "total_subs": total,
                "bat_subs": f["bat"],
                "bowl_subs": f["bowl"],
                "favorite_pattern": favorite,
                "most_used_player": {"name": top_player, "count": top_count},
                "timing": {"at_break": f["break"], "mid_innings": f["mid"]},
                "win_rate": {"bat": win_rate("bat"), "bowl": win_rate("bowl")},
                "headline": (
                    f"{team} leaned {fav_word}: {f['bat']} batting reinforcements, "
                    f"{f['bowl']} bowling. Their most-used impact player was "
                    f"{top_player} ({top_count} times)."
                ),
            }
        )

    # WPL pickers: the control-arm card (the reason anyone can read the rule).
    for team in canon.WPL_FRANCHISES:
        tid = canon.team_id("wpl", team)
        variants.append(
            {
                "team": team,
                "team_id": tid,
                "short": canon.TEAMS[tid]["short"],
                "league": "wpl",
                "empty_state": True,
                "control_arm": True,
                "headline": (
                    f"{team} plays in the WPL, which never had an Impact Player "
                    f"rule. That is the point: your league is the control group. "
                    f"Without it, no one could say how much of the IPL's jump was "
                    f"the rule."
                ),
            }
        )

    # Neutral: the league-wide control-group summary.
    ne = natural_experiment_section(acc)
    variants.append(
        {
            "team": "Neutral",
            "team_id": None,
            "short": "NEU",
            "league": "neutral",
            "empty_state": False,
            "did": ne["diff_in_diff"]["estimate"],
            "headline": (
                "Across the whole league, IPL run rate broke a fifteen-year "
                "ceiling the year the rule arrived. Set against the WPL's rule-"
                "free drift, about +0.9 runs an over of it lines up with the "
                "twelfth man."
            ),
        }
    )

    return {
        "card": "your-team-playbook",
        "variants": variants,
        "definition": (
            "Per franchise (10 IPL + 5 WPL + neutral). IPL pickers get their "
            "team's playbook: batting vs bowling reinforcement split, most-used "
            "impact player, break-vs-mid timing, and the win rate behind each "
            "pattern. WPL pickers get the control-arm card (their league is the "
            "reason the rule is readable). Every current IPL franchise used the "
            "rule, so there is no designed empty state on the IPL side."
        ),
    }


# ---------------------------------------------------------------------------
# Footnotes
# ---------------------------------------------------------------------------


def footnotes_section(acc) -> dict:
    return {
        "replacements_schema": (
            "Impact subs come from the raw Cricsheet match JSON: an innings "
            "delivery's replacements.match entry with reason == 'impact_player' "
            "(2023 onward). Activation is inferred from the entry itself (the "
            "delivery it is recorded on is where the sub takes effect); role and "
            "concussion substitutions (reason 'injury' / 'concussion_substitute' "
            "/ role changes) are excluded. 556 activations across 517 deliveries; "
            "the WPL records none."
        ),
        "diff_in_diff": (
            "The control-group estimate is a difference-in-differences: the IPL's "
            "post-minus-pre run-rate change minus the WPL's contemporaneous "
            "change. Confounds are real and disclosed: pitch and ball changes, a "
            "secular rise in batting intent visible since the 2018 six-rate break, "
            "and a young control league with no true pre-rule period. Evidence "
            "weight, not proof."
        ),
        "batting_order_fluidity": (
            "The honest null: entry entropy (the spread of wickets-down at batter "
            "entry) is flat across the rule, so the twelfth name did not rewire "
            "batting-order thinking."
        ),
        "tail_exposure": (
            "Tail Exposure Rate (demoted): the safety net is about tail quality, "
            "not exposure. The No. 8 batter came in about as often after the rule "
            "as before, while the top-3 strike rate jumped 131.5 -> 155.3."
        ),
        "part_timer": (
            "Part-Timer Extinction / the bowling dividend (demoted): distinct "
            "bowlers per innings jumped 5.79 -> 6.12 the year the rule arrived — "
            "the spare name bought one more bowling option."
        ),
    }


# ---------------------------------------------------------------------------
# Document + main
# ---------------------------------------------------------------------------


def ch7_doc(acc) -> dict:
    return {
        "chapter": 7,
        "title": "The Twelfth Man",
        "register": "the control group",
        "mystery_handoff_in": (
            "Chapter 4 showed you the cliff. Here is the suspect."
        ),
        "mystery_handoff_out": (
            "So the rule opened the door. But was it the same players scoring "
            "faster, or new ones? Hold that too; the last chapter settles it."
        ),
        "controlling_morph": {
            "name": "twin rivers",
            "reuses_buffer": "group_ids.u16 + attrs.u8",
            "note": (
                "The field splits into two run-rate rivers, IPL and WPL, built "
                "from the balls themselves (each ball already carries its "
                "league via attrs.u8 bit 4 and its season-group via "
                "group_ids.u16). They run parallel for the shared window and "
                "diverge at 2023. The impact-sub sparks (impact_subs."
                "spark_indices) glow as they enter the IPL river. No new "
                "per-point buffer."
            ),
        },
        "natural_experiment": natural_experiment_section(acc),
        "license_index": license_section(acc),
        "event_study": event_study_section(acc),
        "playbook": playbook_section(acc),
        "impact_subs": impact_subs_section(acc),
        "honest_null": honest_null_section(acc),
        "payoff": payoff_section(acc),
        "footnotes": footnotes_section(acc),
    }


def build_doc(data_root: Path = canon.DATA_ROOT) -> dict:
    return ch7_doc(build_ch7(data_root))


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    doc = build_doc()
    out_root.mkdir(parents=True, exist_ok=True)
    scenes_dir = out_root / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    raw = flatten.compact_json(doc, sort_keys=True)
    (scenes_dir / "ch7.json").write_bytes(raw)
    sizes = {
        "scenes/ch7.json": {
            "bytes_raw": len(raw),
            "bytes_gz": len(flatten.gz_bytes(raw)),
        }
    }

    # Register in meta.json's manifest (merge, run AFTER flatten + scenes + the
    # other chapter builds so the insertion order, and therefore meta.json, stays
    # byte-deterministic).
    meta_path = out_root / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta.setdefault("files", {}).update(sizes)
        meta_path.write_bytes(flatten.compact_json(meta))

    for name, s in sizes.items():
        print(f"  {name:18s} raw={s['bytes_raw']:>9,}  gz={s['bytes_gz']:>8,}")
    ne = doc["natural_experiment"]
    print(
        "ch7 natural experiment: IPL post",
        ne["headline"]["ipl_post_sequence"],
        "| WPL change",
        ne["headline"]["wpl_change"],
        "| DiD",
        ne["headline"]["did"],
    )
    li = doc["license_index"]["headline"]
    print(
        f"ch7 license: SR {li['sr_pre']} -> {li['sr_post']} | dismissals "
        f"{li['dismissals_pre']} -> {li['dismissals_post']} | top-3 "
        f"{li['top_order_pct_change']}% vs 6-8 {li['lower_order_pct_change']}%"
    )
    es = doc["event_study"]
    print(
        f"ch7 placebo: true 2023 shift {es['true_date_shift']} (t {es['true_date_t']}) "
        f"vs cloud max {es['placebo_cloud_max_shift']} (t {es['placebo_cloud_max_t']}) "
        f"-> stands_out {es['true_date_stands_out']}; global max at "
        f"{es['global_max_shift_date']} ({es['global_max_shift']})"
    )
    pb = doc["playbook"]["headline"]
    print(f"ch7 playbook: break {pb['break_pct_2023']}% (2023) -> {pb['break_pct_2025']}% (2025)")
    isub = doc["impact_subs"]
    print(
        f"ch7 impact subs: {isub['n_events']} events / {isub['n_spark_deliveries']} "
        f"deliveries, WPL {isub['wpl_events']} | bat {isub['reinforcement']['bat']} "
        f"bowl {isub['reinforcement']['bowl']}"
    )
    hn = doc["honest_null"]
    print(
        f"ch7 honest null: entry entropy {hn['entry_entropy']['pre_pooled']} -> "
        f"{hn['entry_entropy']['post_pooled']} (flat {hn['entry_entropy']['flat']}) | "
        f"top-3 SR {hn['top3_sr']['pre']} -> {hn['top3_sr']['post']} | bowlers/inn "
        f"{hn['part_timer']['pre_2022']} -> {hn['part_timer']['post_2023']}"
    )
    n_pay = len(doc["payoff"]["variants"])
    n_empty = sum(1 for v in doc["payoff"]["variants"] if v.get("empty_state"))
    print(f"ch7 payoff: {n_pay} variants, {n_empty} control-arm/empty-state card(s)")
    return doc


if __name__ == "__main__":
    main()
