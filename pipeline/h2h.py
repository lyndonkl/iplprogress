"""Engine #6 — the no-lookahead per-ball head-to-head history table.

Built at the START of R5 (the "blueprint engine table"), reused by two chapters:
  * Chapter 8's Matchup Engineering Score footnote (R5a) — how often a captain's
    bowling change lands the best no-lookahead h2h matchup against the striker;
  * Chapter 9's duel dominance (R5b) — the batter-red <-> bowler-blue edge colour
    of the duel web, from each pair's empirical-Bayes-shrunk runs-per-ball.

Pure stdlib, no numpy. The module reads the raw Cricsheet match JSON (canon /
flatten conventions) and exposes a small public API; it emits no artifacts, so it
imposes no byte-determinism obligations of its own (its consumers ch8.py / ch9.py
do the emission). The one thing it guarantees is the property its snapshot tests
assert: STRICT NO-LOOKAHEAD.

STRICT NO-LOOKAHEAD ORDERING
  Matches are sorted by ``(info.dates[0], match_id)`` — real calendar time, then a
  stable id tiebreak. This is deliberately NOT flatten's season-blocked point
  order: flatten places every IPL-2023 delivery before every WPL-2023 delivery
  regardless of date (so its cold-open captions fire in narrative order), which
  moves 381 match positions relative to true chronology. The men's / women's
  player pools are disjoint so no cross-league pair exists, but the engine keys on
  DATES, not season labels, because a naive "sort by season label + match id"
  (dropping the within-season date) feeds some pairs deliveries from their own
  future — the mutation the snapshot tests catch.

  Within a match, deliveries are visited in ``(innings index, over, ball index)``
  order — the natural JSON order. Per faced ball the engine READS the pair's
  running state, yields it, THEN updates it, so a ball only ever sees deliveries
  strictly before it in real time.

  A "faced ball" excludes wides (the striker does not face a wide); no-balls are
  counted and ``runs.batter`` is credited. A dismissal is charged to the pair only
  when the STRIKER is the one out and the kind is bowler-credited (bowled / caught
  / lbw / stumped / caught and bowled / hit wicket). This convention reproduces the
  published Kohli teasers exactly (Kohli vs Jadeja: 160 balls, 179 runs, 3
  dismissals; before the 160th ball the no-lookahead prior is 159 / 175 / 3).

EMPIRICAL-BAYES SHRINKAGE (normal-normal / DerSimonian-Laird)
  A raw runs-per-ball off a 6-ball sample is noise. Each pair's rate is shrunk
  toward the league par:
      shrunk(n, runs) = (runs + k * mu) / (n + k) = mu + (x - mu) * n / (n + k)
  where mu is the pooled runs / faced-ball (~1.3322), and k = sigma^2 / tau^2
  (~51.2 pseudo-balls) with sigma^2 the ball-level variance of runs.batter and
  tau^2 the between-pair variance estimated by the DerSimonian-Laird method of
  moments over the full pair distribution. A pair needs ~51 balls to earn half its
  weight off par; sub-30-ball pairs sit near league par. k is a global
  hyperparameter fit on the full-corpus pair distribution (standard EB practice, a
  hyperparameter-level peek); the per-ball n that drives every individual shrink is
  strictly no-lookahead.

PUBLIC API (what ch8.py / ch9.py import)
  Keying / parsing helpers:
    BOWLER_CREDIT, person_registry(info), resolve(reg, name),
    striker_dismissed(delivery, reg, striker_id),
    date_ordered_match_files(data_root)
  The running table:
    class H2HTable  (.prior / .get / .update / .items / __len__ / __contains__)
  Per-ball no-lookahead stream (the primary iterator):
    BallEvent, iter_deliveries(data_root, table=None)
  Per-over no-lookahead stream (the Matchup Engineering Score inputs for Ch8):
    OverDecision, iter_over_decisions(data_root, table=None)
  Empirical-Bayes shrinkage:
    EBConstants (with .shrunk(n, runs)), eb_constants(data_root)
  Final-state helpers (Ch9 duel dominance + Ch8 usable-history):
    build_table(data_root), dominance(data_root, eb, table),
    usable_history(data_root, thresholds)

Every pair is keyed on the registry PERSON-ID (info.registry.people), never on a
name string — name strings are not unique across the corpus.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten

# Dismissal kinds credited to the bowler AND to the striker's h2h ledger. Run
# outs, obstruction, retirements, timed-out etc. are excluded — they are not the
# bowler beating the bat, so they never count against the batter in this duel.
BOWLER_CREDIT = frozenset(
    {"bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"}
)


# ---------------------------------------------------------------------------
# Keying / parsing helpers
# ---------------------------------------------------------------------------


def person_registry(info: dict) -> dict:
    """The match's ``registry.people`` name -> stable person-id table."""
    return info.get("registry", {}).get("people", {})


def resolve(reg: dict, name: str) -> str:
    """Person-id for a name (falls back to the raw name if unregistered)."""
    return reg.get(name, name)


def striker_dismissed(delivery: dict, reg: dict, striker_id: str) -> bool:
    """True iff this delivery dismisses the STRIKER in a bowler-credited way."""
    for wicket in delivery.get("wickets", []):
        if wicket.get("kind") in BOWLER_CREDIT:
            out_id = resolve(reg, wicket.get("player_out", delivery["batter"]))
            if out_id == striker_id:
                return True
    return False


@lru_cache(maxsize=None)
def date_ordered_match_files(data_root: Path = canon.DATA_ROOT) -> tuple:
    """``[(date0, match_id, league, path)]`` in STRICT chronological order.

    flatten.sorted_match_files gives season-blocked order (IPL before WPL within a
    shared year); this re-sorts it purely by ``(date0, match_id)`` so no ball is
    ever visited before a delivery that happened earlier in real time. Cached: the
    corpus does not change within a run and several entry points share the list.
    """
    files = flatten.sorted_match_files(data_root)
    return tuple(sorted(files, key=lambda e: (e[0], e[1])))


def _load(path: Path) -> dict:
    with open(path) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# The running head-to-head table
# ---------------------------------------------------------------------------


class H2HTable:
    """Running (batter_id, bowler_id) -> [balls, runs, dismissals] accumulator.

    ``prior`` READS the state reflecting only deliveries processed so far; ``update``
    folds one more faced ball in. Keeping the two calls separate is what makes the
    no-lookahead discipline auditable: a consumer reads, acts, then updates.
    """

    __slots__ = ("_state",)

    def __init__(self) -> None:
        self._state: dict = defaultdict(lambda: [0, 0, 0])

    def prior(self, batter_id: str, bowler_id: str) -> tuple:
        """(balls, runs, dismissals) for the pair BEFORE any pending update."""
        st = self._state.get((batter_id, bowler_id))
        return (0, 0, 0) if st is None else (st[0], st[1], st[2])

    def get(self, batter_id: str, bowler_id: str) -> tuple:
        """Alias for :meth:`prior` (reads current cumulative state)."""
        return self.prior(batter_id, bowler_id)

    def update(self, batter_id: str, bowler_id: str, runs: int, dismissed: bool) -> None:
        """Fold one faced ball into the pair's cumulative state."""
        st = self._state[(batter_id, bowler_id)]
        st[0] += 1
        st[1] += runs
        st[2] += 1 if dismissed else 0

    def __contains__(self, key: tuple) -> bool:
        return key in self._state

    def __len__(self) -> int:
        return len(self._state)

    def items(self):
        """Yield ``(key, (balls, runs, dismissals))`` for every pair seen."""
        for key, st in self._state.items():
            yield key, (st[0], st[1], st[2])

    # Ch9 reads dominance off the final table; alias reads well at the call site.
    pairs = items


# ---------------------------------------------------------------------------
# Per-ball no-lookahead stream (the primary iterator)
# ---------------------------------------------------------------------------


class BallEvent(NamedTuple):
    date: str
    match_id: int
    league: str
    season: int
    innings: int  # 0-based index into match["innings"]
    over_no: int  # over["over"]
    ball_no: int  # 0-based delivery index within the over (wides included)
    batter: str  # registry person-id
    bowler: str  # registry person-id
    runs: int  # runs.batter off this ball
    dismissed: bool  # striker out to the bowler on this ball
    prior_balls: int  # pair state BEFORE this ball — strictly no-lookahead
    prior_runs: int
    prior_dismissals: int


def iter_deliveries(data_root: Path = canon.DATA_ROOT, table: H2HTable = None):
    """Yield a :class:`BallEvent` per faced ball, strict no-lookahead.

    For each ball the pair's PRIOR running state (before this ball) is read and
    attached to the event, then the table is updated — so ``prior_*`` never reflects
    this ball or any later one. Pass ``table`` to keep the final cumulative state
    (otherwise an internal table is used and discarded).
    """
    table = H2HTable() if table is None else table
    for date0, match_id, league, path in date_ordered_match_files(data_root):
        match = _load(path)
        info = match["info"]
        season = canon.canon_season(info)
        reg = person_registry(info)
        for inn_i, innings in enumerate(match.get("innings", [])):
            if canon.is_super_over(innings):
                continue  # standing rule: super overs never enter the stream
            for over in innings.get("overs", []):
                over_no = over["over"]
                for ball_i, dl in enumerate(over["deliveries"]):
                    if "wides" in dl.get("extras", {}):
                        continue  # a wide is not a ball faced
                    batter = resolve(reg, dl["batter"])
                    bowler = resolve(reg, dl["bowler"])
                    runs = dl["runs"]["batter"]
                    dismissed = striker_dismissed(dl, reg, batter)
                    pb, pr, pd = table.prior(batter, bowler)
                    yield BallEvent(
                        date0, match_id, league, season, inn_i, over_no, ball_i,
                        batter, bowler, runs, dismissed, pb, pr, pd,
                    )
                    table.update(batter, bowler, runs, dismissed)


# ---------------------------------------------------------------------------
# Per-over no-lookahead stream — the Matchup Engineering Score inputs (Ch8)
# ---------------------------------------------------------------------------


class OverDecision(NamedTuple):
    date: str
    match_id: int
    league: str
    season: int
    innings: int  # 0-based index into match["innings"]
    over_no: int  # over["over"]
    over_index: int  # 0-based position among the innings' non-empty overs
    bowler_id: str  # this over's bowler (deliveries[0])
    striker_id: str  # batter on strike at the over's first delivery
    innings_bowler_ids: frozenset  # every bowler used in this innings (a roster fact)
    faced: tuple  # ((batter_id, bowler_id, runs, dismissed), ...) for non-wide balls


def iter_over_decisions(data_root: Path = canon.DATA_ROOT, table: H2HTable = None):
    """Yield an :class:`OverDecision` per over, strict no-lookahead.

    At the instant an ``OverDecision`` is yielded, ``table`` reflects every delivery
    strictly BEFORE this over, so the caller can score the bowling decision — read
    ``table.prior(striker_id, candidate)`` for each candidate and shrink it — without
    peeking at the over about to be bowled. After the caller resumes iteration the
    over's faced balls are folded in. Pass your own ``table`` so you can read it.

    ``innings_bowler_ids`` is the set of bowlers who bowled in the innings (a
    full-innings roster scan, the natural candidate pool). It is a roster fact, NOT
    an h2h-state lookahead: the h2h TABLE stays strictly no-lookahead. Deciding what
    counts as a bowling change, the over quota, and the candidate filter is the
    consumer's job (Ch8's modelling choice), not this engine's.
    """
    table = H2HTable() if table is None else table
    for date0, match_id, league, path in date_ordered_match_files(data_root):
        match = _load(path)
        info = match["info"]
        season = canon.canon_season(info)
        reg = person_registry(info)
        for inn_i, innings in enumerate(match.get("innings", [])):
            if canon.is_super_over(innings):
                continue
            overs = innings.get("overs", [])
            pool = frozenset(
                resolve(reg, dl["bowler"])
                for over in overs
                for dl in over["deliveries"]
            )
            over_index = 0
            for over in overs:
                dls = over["deliveries"]
                if not dls:
                    continue
                bowler_id = resolve(reg, dls[0]["bowler"])
                striker_id = resolve(reg, dls[0]["batter"])
                faced = []
                for dl in dls:
                    if "wides" in dl.get("extras", {}):
                        continue
                    batter = resolve(reg, dl["batter"])
                    bowler = resolve(reg, dl["bowler"])
                    faced.append(
                        (batter, bowler, dl["runs"]["batter"],
                         striker_dismissed(dl, reg, batter))
                    )
                yield OverDecision(
                    date0, match_id, league, season, inn_i, over["over"],
                    over_index, bowler_id, striker_id, pool, tuple(faced),
                )
                for batter, bowler, runs, dismissed in faced:
                    table.update(batter, bowler, runs, dismissed)
                over_index += 1


# ---------------------------------------------------------------------------
# Empirical-Bayes shrinkage
# ---------------------------------------------------------------------------


class EBConstants(NamedTuple):
    mu: float  # pooled runs / faced-ball (league par)
    sigma2: float  # ball-level variance of runs.batter
    tau2: float  # between-pair variance (DerSimonian-Laird MoM)
    k: float  # shrinkage strength sigma^2 / tau^2, in pseudo-balls
    n_balls: int  # faced balls the constants were fit on
    n_pairs: int  # distinct (batter, bowler) pairs

    def shrunk(self, balls: int, runs: float) -> float:
        """EB-shrunk expected runs/ball for a pair with ``balls`` faced, ``runs`` off.

        (runs + k*mu) / (balls + k). Zero-ball pairs return par exactly; the value
        moves off par only as ``balls`` approaches and exceeds k.
        """
        if not math.isfinite(self.k):
            return self.mu
        return (runs + self.k * self.mu) / (balls + self.k)


def eb_constants(data_root: Path = canon.DATA_ROOT) -> EBConstants:
    """Fit the EB shrinkage constants on the full corpus pair distribution.

    One pass over :func:`iter_deliveries`: a runs.batter histogram gives mu and the
    ball-level variance sigma^2; the per-pair final (balls, runs) gives the
    DerSimonian-Laird between-pair variance tau^2; k = sigma^2 / tau^2.
    """
    runhist: Counter = Counter()
    pair_final: dict = defaultdict(lambda: [0, 0])  # balls, runs
    for ev in iter_deliveries(data_root):
        runhist[ev.runs] += 1
        pf = pair_final[(ev.batter, ev.bowler)]
        pf[0] += 1
        pf[1] += ev.runs

    n_balls = sum(runhist.values())
    e_r = sum(r * c for r, c in runhist.items()) / n_balls
    e_r2 = sum(r * r * c for r, c in runhist.items()) / n_balls
    sigma2 = e_r2 - e_r * e_r
    mu = e_r

    means = [(n, runs / n) for n, runs in pair_final.values() if n > 0]
    n_pairs = len(means)
    sum_n = sum(n for n, _ in means)
    grand = sum(n * x for n, x in means) / sum_n
    q = sum(n * (x - grand) ** 2 for n, x in means) / sigma2
    sum_n2 = sum(n * n for n, _ in means)
    c_dl = sum_n - sum_n2 / sum_n
    tau2 = max(0.0, (q - (n_pairs - 1)) / c_dl) * sigma2
    k = sigma2 / tau2 if tau2 > 0 else math.inf
    return EBConstants(mu, sigma2, tau2, k, n_balls, n_pairs)


# ---------------------------------------------------------------------------
# Final-state helpers (Ch9 duel dominance + Ch8 usable-history)
# ---------------------------------------------------------------------------


def build_table(data_root: Path = canon.DATA_ROOT) -> H2HTable:
    """Roll :func:`iter_deliveries` to the end; return the final H2HTable."""
    table = H2HTable()
    for _ in iter_deliveries(data_root, table=table):
        pass
    return table


def dominance(
    data_root: Path = canon.DATA_ROOT,
    eb: EBConstants = None,
    table: H2HTable = None,
) -> dict:
    """Final EB-shrunk expected runs/ball per pair — Ch9's duel-edge colour.

    ``{(batter_id, bowler_id): shrunk_runs_per_ball}``. Higher = batter-favoured
    (edge reads red), lower = bowler-favoured (edge reads blue), par ~= mu. Pass a
    prebuilt ``table`` / ``eb`` to avoid re-parsing the corpus.
    """
    if table is None:
        table = build_table(data_root)
    if eb is None:
        eb = eb_constants(data_root)
    return {key: eb.shrunk(balls, runs) for key, (balls, runs, _dis) in table.items()}


def usable_history(
    data_root: Path = canon.DATA_ROOT,
    thresholds: tuple = (1, 12),
) -> dict:
    """Per (league, season): faced balls, and how many were bowled with enough
    prior h2h history to be "usable".

    ``{(league, season): {"balls": int, "ge": {threshold: count}}}``. The share with
    >= 12 prior faced balls is Chapter 8's Matchup Engineering footnote lead (the raw
    material grew 12.4% in 2009 to 42.1% in 2019). Purely a function of the strictly
    no-lookahead ``prior_balls`` each ball is served.
    """
    out: dict = {}
    for ev in iter_deliveries(data_root):
        rec = out.get((ev.league, ev.season))
        if rec is None:
            rec = {"balls": 0, "ge": {t: 0 for t in thresholds}}
            out[(ev.league, ev.season)] = rec
        rec["balls"] += 1
        for t in thresholds:
            if ev.prior_balls >= t:
                rec["ge"][t] += 1
    return out


# ---------------------------------------------------------------------------
# CLI (a human-readable dump; the module ships no artifacts)
# ---------------------------------------------------------------------------


def main() -> None:
    eb = eb_constants()
    print("Engine #6 — no-lookahead h2h + empirical-Bayes shrinkage")
    print(
        f"  mu={eb.mu:.4f}  sigma^2={eb.sigma2:.4f}  tau^2={eb.tau2:.5f}  "
        f"k={eb.k:.1f}  pairs={eb.n_pairs}  balls={eb.n_balls}"
    )
    table = build_table()
    print(f"  final table pairs: {len(table)}")
    hist = usable_history()
    print("  usable h2h history (IPL, >=12 prior faced balls, % of faced balls):")
    for s in canon.IPL_SEASONS:
        rec = hist.get(("ipl", s))
        if rec:
            pct = 100.0 * rec["ge"][12] / rec["balls"]
            print(f"    {s}: {pct:5.1f}%  ({rec['balls']} balls)")


if __name__ == "__main__":
    main()
