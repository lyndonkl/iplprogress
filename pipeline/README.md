# Pipeline — "Every Ball Ever" R0

Python 3, **stdlib only** (json, gzip, struct/array, pathlib, unittest). Flattens the
Cricsheet ball-by-ball corpus (`data/ipl_json/*.json`, `data/wpl_json/*.json`) into the
R0 data-contract artifacts under `web/static/data/`.

## Run everything

From the repo root:

```sh
python3 pipeline/flatten.py \
  && python3 pipeline/payoff_harness.py \
  && python3 pipeline/ledger.py \
  && python3 -m unittest discover -s pipeline/tests -q
```

Order matters: `flatten.py` emits the point stream + columnar dataset and writes
`meta.json`; `payoff_harness.py` emits `payoff/ch1.json` (and records its sizes in
`meta.json`); `ledger.py` audits everything on disk against the blueprint §2 budgets.
Both the harness and the ledger exit non-zero on failure. The whole build runs in a few
seconds and is byte-for-byte deterministic (gzip level 9, `mtime=0`).

## Modules

| file | role |
|---|---|
| `canon.py` | Engine #4 canonicalization: 62 raw venue strings → 37 canonical grounds, franchise renames (DD→DC, KXIP→PBKS, RCB Bangalore→Bengaluru in both leagues, Rising Pune unified; Gujarat **Lions ≠ Titans ≠ Giants**), season normalization (`'2007/08'`→2008, `'2009/10'`→2010, `'2020/21'`→2020, WPL `'2022/23'`→2023 … — always the year the cricket was played, verified equal to `dates[0]` year for all 1331 matches), D/L flag, super-over innings detection. Every lookup raises `KeyError` on unmapped input. |
| `flatten.py` | One chronological pass emitting all contract artifacts (see below). |
| `payoff_harness.py` | Payoff-card snapshot harness: emits + asserts the 16 Chapter-1 variants. |
| `ledger.py` | Payload ledger vs the §2 budgets; prints the table; writes `ledger.json`. |
| `tests/` | `unittest` snapshot tests (see below). |

## The point stream (contract)

Every delivery in every innings, **excluding super-over innings**, sorted by
(match date, match_id, innings index, over, delivery index) across both leagues:

- **n_points = 316,199.** (The blueprint's headline 316,388 counts the 189 super-over
  balls; the standing rule excludes them from the stream, so 316,388 − 189 = 316,199.)
- 23 groups, column order **IPL 2008…2026 (gi 0–18), then WPL 2023…2026 (gi 19–22)**.
- No position buffers are shipped: the free-field layout is a client-side hash of point
  index; season columns derive from `groups.json` + a client-side group_id counting pass.

## Emitted artifacts (`web/static/data/`)

| artifact | contents |
|---|---|
| `meta.json` | `{ n_points, built_at: "unknown", point_order: "chronological", files: {name: {bytes_raw, bytes_gz}} }` |
| `groups.json` | ordered array, index = `gi`: `{ gi, league, season, count }` × 23 |
| `group_ids.u16` | little-endian Uint16 per delivery → `gi` |
| `attrs.u8` | one byte per delivery — bits 0–2 outcome class: 0 dot · 1 single · 2 two-or-three · 3 four · 4 six · 5 other scoring ball (extras-only scorers plus the 78 all-run 5s); bit 3 wicket fell (any `wickets` entry, incl. retirements); bit 4 WPL; bits 5–7 zero |
| `columnar.json.gz` | sandbox dataset: 12 parallel arrays over the same point order — `season, league (0/1), innings (1/2), over (0–19), ball_index_in_over, batter, bowler, batting_team` (dict-encoded ints), `runs_batter, runs_total, outcome, wicket` — plus `dicts` mapping codes → names. gzip level 9 |
| `payoff/ch1.json` | 16 Chapter-1 payoff variants (below) |
| `ledger.json` | the payload audit (build report, excluded from its own budget math) |

Outcome classing: off-the-bat runs win (1 → single, 2/3 → two-or-three, 4 → four,
6 → six); zero total runs → dot; anything else that scored → class 5.

## Payoff cards (Chapter 1 — "Death of the Sighter")

Exactly 16 variants: 10 current IPL franchises + 5 WPL franchises + `Neutral`
(league-wide IPL, reproducing the thesis: first-10-ball SR **108.0 → 135.3**). Metric:
strike rate off each batter's first ten balls faced of an innings (wides are not balls
faced). Eras: IPL 2008–2010 vs 2023–2026; WPL 2023–2024 vs 2025–2026 with a
small-sample honesty flag + copy. GT, LSG and SRH (born after 2010) get the **designed
empty state** — authored copy, `first10_sr_early_era: null`, never a blank card. All
cards are template + numbers; nothing is hand-authored per team. The harness asserts
all 16 exist and are non-degenerate and exits non-zero otherwise.

## Budgets (ledger)

- R0 spike set (`meta.json` + `groups.json` + `group_ids.u16` + `attrs.u8` — everything
  needed before the cold-open field assembles): **≤ 3 MB gz** → actual ~0.11 MB gz.
- Per-chapter payloads ≤ 2 MB gz (ch1 payoff ~1.3 KB gz; columnar ~0.63 MB gz, also
  under the blueprint's ~0.8 MB sandbox target).
- Full read-through ≤ 25 MB gz → actual ~0.74 MB gz.

## Tests

```sh
python3 -m unittest discover -s pipeline/tests -q
```

- `test_canon.py` — canonicalization tables exhaustive over the corpus in **both**
  directions (unmapped input fails; stale keys fail), season set exactly
  {ipl: 2008–2026, wpl: 2023–2026}, season == `dates[0]` year for all matches, 23
  groups, D/L count = 23, super-over innings = 36, Gujarat teams distinct.
- `test_flatten.py` — rebuilds the whole stream from the raw corpus with an
  **independent implementation** (own ordering, `dates[0]`-derived seasons, its own
  bit-packer) and compares: n_points = 316,199, full group-id stream equality, full
  attrs equality plus per-bit round-trip on sampled IPL/WPL matches, super-over
  exclusion on the known 2017 tie (`1082625.json`), columnar arrays all length
  n_points with range/dict/bit-consistency checks. Builds the artifacts first if
  they're missing.

Snapshot constants live at the top of each test file; a new Cricsheet drop that changes
the corpus must update them consciously.
