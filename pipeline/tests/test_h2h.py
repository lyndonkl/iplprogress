"""Lookahead-bias snapshot tests for Engine #6 (pipeline/h2h.py) on the real corpus.

The engine's whole job is to serve each ball ONLY the head-to-head history that
existed strictly before it in real calendar time. These tests recount that
property three independent ways and prove the date-ordering is load-bearing by
mutating it into a season-label sort and watching the guarantee break.

  INV1  the first-ever meeting of a pair exposes prior state (0, 0, 0)
  INV2  the snapshot served at ball k equals an INDEPENDENT rollup of balls 0..k-1
  INV3  every pair's ball dates are non-decreasing (no ball is fed its future)
  guard a season-label sort (season, match_id — dropping the within-season date)
        FAILS INV3, while the engine's strict-date order passes it with 0 violations

Plus the empirical-Bayes constants fit on the corpus and the published Kohli-vs-
Jadeja worked example. All invariants must hold with ZERO violations.
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import h2h

# Corpus-wide snapshot constants (recounted 2026-07-07; see r5a-scout-digest.md).
N_PAIRS = 33772
N_BALLS = 305738


# ---------------------------------------------------------------------------
# Shared single-pass fixtures (the corpus is parsed as few times as possible)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def corpus():
    """One strict-date pass: every BallEvent, the per-pair sequence, final table."""
    table = h2h.H2HTable()
    events = []
    per_pair = defaultdict(list)
    for ev in h2h.iter_deliveries(table=table):
        events.append(ev)
        per_pair[(ev.batter, ev.bowler)].append(ev)
    return events, dict(per_pair), table


@pytest.fixture(scope="module")
def eb():
    return h2h.eb_constants()


def _per_pair_dates(files):
    """Per (batter_id, bowler_id) the ordered list of ball dates, for a given file
    ordering — the minimal recompute INV3 needs, independent of the engine."""
    per_pair = defaultdict(list)
    for date0, _mid, _league, path in files:
        match = h2h._load(path)
        reg = h2h.person_registry(match["info"])
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            for over in innings.get("overs", []):
                for dl in over["deliveries"]:
                    if "wides" in dl.get("extras", {}):
                        continue
                    key = (h2h.resolve(reg, dl["batter"]),
                           h2h.resolve(reg, dl["bowler"]))
                    per_pair[key].append(date0)
    return per_pair


def _count_date_violations(per_pair_dates):
    return sum(1 for dates in per_pair_dates.values() if dates != sorted(dates))


# ---------------------------------------------------------------------------
# INV1 — first-ever meeting exposes zero prior state
# ---------------------------------------------------------------------------


def test_inv1_first_meeting_exposes_zero_prior(corpus):
    _events, per_pair, _table = corpus
    violations = 0
    for seq in per_pair.values():
        first = seq[0]
        if (first.prior_balls, first.prior_runs, first.prior_dismissals) != (0, 0, 0):
            violations += 1
    assert violations == 0
    assert len(per_pair) == N_PAIRS


# ---------------------------------------------------------------------------
# INV2 — snapshot at ball k == independent rollup of balls 0..k-1
# ---------------------------------------------------------------------------


def test_inv2_snapshot_equals_independent_rollup(corpus):
    _events, per_pair, _table = corpus
    violations = 0
    checked = 0
    for seq in per_pair.values():
        balls = runs = dismissals = 0  # independent replay, engine never consulted
        for ev in seq:
            checked += 1
            if (ev.prior_balls, ev.prior_runs, ev.prior_dismissals) != (
                balls, runs, dismissals
            ):
                violations += 1
            balls += 1
            runs += ev.runs
            dismissals += 1 if ev.dismissed else 0
    assert violations == 0
    assert checked == N_BALLS


# ---------------------------------------------------------------------------
# INV3 — each pair's ball dates are non-decreasing
# ---------------------------------------------------------------------------


def test_inv3_pair_dates_non_decreasing(corpus):
    _events, per_pair, _table = corpus
    violations = 0
    for seq in per_pair.values():
        dates = [ev.date for ev in seq]
        if dates != sorted(dates):
            violations += 1
    assert violations == 0


# ---------------------------------------------------------------------------
# Mutation guard — a season-label sort FAILS INV3 (the dates are load-bearing)
# ---------------------------------------------------------------------------


def test_mutation_season_label_sort_fails_inv3():
    correct = list(h2h.date_ordered_match_files())  # sorted by (full date, match_id)
    # The load-bearing mutation: order matches by SEASON LABEL + match_id, dropping
    # the within-season DATE tiebreak (the naive "just group by season" ordering the
    # engine deliberately refuses). match ids are not chronological within a season,
    # so this serves some pairs deliveries out of real-time order.
    mutated = sorted(correct, key=lambda e: (e[0][:4], e[1]))

    # the mutation is non-trivial (else the guard would be vacuous)
    assert [e[1] for e in mutated] != [e[1] for e in correct]

    # the engine's strict-date order is clean; the season-label order is not
    assert _count_date_violations(_per_pair_dates(correct)) == 0
    assert _count_date_violations(_per_pair_dates(mutated)) > 0


def test_strict_date_order_differs_from_season_blocked():
    """The engine's chronology is genuinely NOT flatten's season-blocked point
    order: 381 match positions move (IPL-before-WPL within a shared year)."""
    date_order = [e[1] for e in h2h.date_ordered_match_files()]
    season_blocked = [e[1] for e in flatten.sorted_match_files()]
    n_diff = sum(1 for a, b in zip(date_order, season_blocked) if a != b)
    assert n_diff == 381


# ---------------------------------------------------------------------------
# Empirical-Bayes shrinkage constants
# ---------------------------------------------------------------------------


def test_eb_constants_on_corpus(eb):
    assert eb.n_pairs == N_PAIRS
    assert eb.n_balls == N_BALLS
    assert eb.mu == pytest.approx(1.3322, abs=5e-4)
    assert eb.sigma2 == pytest.approx(2.7973, abs=1e-3)
    assert eb.tau2 == pytest.approx(0.05463, abs=1e-4)
    assert eb.k == pytest.approx(51.20, abs=0.1)


def test_eb_shrinkage_behaviour(eb):
    # a zero-ball pair sits exactly at league par
    assert eb.shrunk(0, 0) == pytest.approx(eb.mu, abs=1e-12)
    # a one-ball six barely moves; a huge sample of sixes dominates par
    assert eb.shrunk(1, 6) < eb.shrunk(10_000, 60_000)
    # a pair that only ever scored below par stays below par, and vice-versa
    assert eb.shrunk(500, 0) < eb.mu < eb.shrunk(500, 500 * 4)
    # closed-form identity: shrunk == mu + (x-mu)*n/(n+k)
    n, runs = 175, 200
    x = runs / n
    assert eb.shrunk(n, runs) == pytest.approx(eb.mu + (x - eb.mu) * n / (n + eb.k))


# ---------------------------------------------------------------------------
# Kohli vs Jadeja — the published worked example
# ---------------------------------------------------------------------------


def test_kohli_jadeja_worked_example(corpus):
    _events, per_pair, table = corpus
    # ids are stable; name strings are not — resolve both via the registry
    kohli = jadeja = None
    for _d, _m, _lg, path in h2h.date_ordered_match_files():
        reg = h2h.person_registry(h2h._load(path)["info"])
        kohli = kohli or reg.get("V Kohli")
        jadeja = jadeja or reg.get("RA Jadeja")
        if kohli and jadeja:
            break
    assert kohli and jadeja

    seq = per_pair[(kohli, jadeja)]
    assert len(seq) == 160

    # first meeting exposes zero prior
    first = seq[0]
    assert (first.prior_balls, first.prior_runs, first.prior_dismissals) == (0, 0, 0)

    # before the 160th ball the strictly no-lookahead prior is 159 / 175 / 3
    last = seq[159]
    assert (last.prior_balls, last.prior_runs, last.prior_dismissals) == (159, 175, 3)

    # the final rollup over all 160 balls is 160 / 179 / 3
    balls = len(seq)
    runs = sum(ev.runs for ev in seq)
    dismissals = sum(1 for ev in seq if ev.dismissed)
    assert (balls, runs, dismissals) == (160, 179, 3)

    # the fully-rolled table agrees with the per-ball replay
    assert table.get(kohli, jadeja) == (160, 179, 3)


# ---------------------------------------------------------------------------
# Final-state helpers — Ch9 dominance + the over-decision (Ch8) stream
# ---------------------------------------------------------------------------


def test_over_decisions_cover_the_same_balls(corpus):
    """iter_over_decisions and iter_deliveries fold in the identical ball set, so
    the Matchup-Engineering input stream shares the delivery iterator's guarantees."""
    _events, _per_pair, delivery_table = corpus
    over_table = h2h.H2HTable()
    for _od in h2h.iter_over_decisions(table=over_table):
        pass
    assert len(over_table) == N_PAIRS
    assert dict(over_table.items()) == dict(delivery_table.items())


def test_dominance_is_shrunk_final_rate(corpus, eb):
    _events, _per_pair, table = corpus
    dom = h2h.dominance(eb=eb, table=table)
    assert len(dom) == N_PAIRS
    # every dominance value is a shrunk expected runs/ball, bounded by the data
    assert all(0.0 <= v <= 6.0 for v in dom.values())
    # spot check the closed form on one pair
    (bat, bowl), (balls, runs, _dis) = next(iter(table.items()))
    assert dom[(bat, bowl)] == pytest.approx(eb.shrunk(balls, runs))


def test_usable_history_growth():
    """Ch8 footnote lead: usable h2h history (>=12 prior faced balls, denom = faced
    balls) grew from ~12% (2009) to ~42% (2019)."""
    hist = h2h.usable_history()
    y2009 = hist[("ipl", 2009)]
    y2019 = hist[("ipl", 2019)]
    pct2009 = 100.0 * y2009["ge"][12] / y2009["balls"]
    pct2019 = 100.0 * y2019["ge"][12] / y2019["balls"]
    assert pct2009 == pytest.approx(12.4, abs=0.5)
    assert pct2019 == pytest.approx(42.1, abs=0.5)
    assert pct2019 > pct2009
