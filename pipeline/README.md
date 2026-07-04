# Pipeline — "Every Ball Ever" R0 + R1a

Python 3, **stdlib only** (json, gzip, struct/array, pathlib, unittest). Flattens the
Cricsheet ball-by-ball corpus (`data/ipl_json/*.json`, `data/wpl_json/*.json`) into the
R0 data-contract artifacts plus the R1a addendum (cold open + Chapter 1) under
`web/static/data/`.

## Run everything

From the repo root:

```sh
python3 pipeline/flatten.py \
  && python3 pipeline/scenes.py \
  && python3 pipeline/payoff_harness.py \
  && python3 pipeline/ledger.py \
  && python3 -m unittest discover -s pipeline/tests -q
```

Order matters: `flatten.py` emits the point stream + per-point attributes + columnar
dataset and writes `meta.json`; `scenes.py` emits `scenes/coldopen.json` +
`scenes/ch1.json`; `payoff_harness.py` emits `payoff/ch1.json` (each records its sizes
in `meta.json`); `ledger.py` audits everything on disk against the blueprint §2
budgets. The harness and the ledger exit non-zero on failure. The whole build runs in
seconds and is **byte-for-byte deterministic** (gzip level 9, `mtime=0`; JSON compact,
new artifacts key-sorted) — verified by rebuilding and diffing checksums.

## Modules

| file | role |
|---|---|
| `canon.py` | Engine #4 canonicalization: 62 raw venue strings → 37 canonical grounds, franchise renames (DD→DC, KXIP→PBKS, RCB Bangalore→Bengaluru in both leagues, Rising Pune unified; Gujarat **Lions ≠ Titans ≠ Giants**), season normalization (`'2007/08'`→2008 … — always the year the cricket was played, verified equal to `dates[0]` year for all 1331 matches), D/L flag, super-over innings detection, **and the R1a 20-franchise id table** (`TEAMS`/`team_id`): league-scoped ids 0–19 (IPL's 15 sorted by name, then the WPL's 5 — the WPL DC/MI/RCB are distinct franchises with their own ids), approximate-brand kit colors, `active` flags (Deccan Chargers, Gujarat Lions, Kochi, Pune Warriors, Rising Pune Supergiant are `false`). Every lookup raises `KeyError` on unmapped input. |
| `flatten.py` | One chronological pass emitting all per-point contract artifacts (see below). |
| `scenes.py` | R1a scene aggregates: `scenes/coldopen.json` (You-Draw-It truth series + corpus facts) and `scenes/ch1.json` (ignition, out-rate, defiers, sixes, aerial ledger, WPL beat). |
| `payoff_harness.py` | Payoff-card snapshot harness: emits + asserts the 16 Chapter-1 variants (R1a full spec). |
| `ledger.py` | Payload ledger vs the §2 budgets; prints the table; writes `ledger.json`. |
| `tests/` | `unittest` snapshot tests (see below). |

## The point stream (contract)

Every delivery in every innings, **excluding super-over innings**, sorted by
(match date, match_id, innings index, over, delivery index) across both leagues:

- **n_points = 316,199.** (The blueprint's headline 316,388 counts the 189 super-over
  balls; the standing rule excludes them from the stream, so 316,388 − 189 = 316,199.
  On-screen count is always 316,199 — the corpus total lives in the footnote layer.)
- 23 groups, column order **IPL 2008…2026 (gi 0–18), then WPL 2023…2026 (gi 19–22)**.
- No position buffers are shipped: the free-field layout is a client-side hash of point
  index; season columns derive from `groups.json`; the Ch 1 **ignition wall** derives
  from `ballsfaced.u8` × `group_ids.u16`; picker ignition tints from `team.u8`.

## Emitted artifacts (`web/static/data/`)

| artifact | contents |
|---|---|
| `meta.json` | `{ n_points, built_at: "unknown", point_order: "chronological", files: {name: {bytes_raw, bytes_gz}}, n_players, n_matches: {ipl, wpl} }` — the v2 count fields (storyboard CO-3 traceability) are added by `scenes.py`; `test_r1a` asserts they equal `scenes/coldopen.json`'s corpus block |
| `groups.json` | ordered array, index = `gi`: `{ gi, league, season, count }` × 23 |
| `group_ids.u16` | little-endian Uint16 per delivery → `gi` |
| `attrs.u8` | one byte per delivery — bits 0–2 outcome class: 0 dot · 1 single · 2 two-or-three · 3 four · 4 six · 5 other scoring ball; bit 3 wicket fell; bit 4 WPL; bits 5–7 zero |
| `ballsfaced.u8` **(R1a)** | per delivery: the striker's **1-based ball-faced index within their innings at this delivery** — wides are 0 (the batter doesn't face them), no-balls count, capped at 255 (max observed: 73 well under the cap). Powers the ignition-wall layout. |
| `team.u8` **(R1a)** | per delivery: canonical **batting-franchise id** (league-scoped; renames collapse — every Delhi Daredevils ball carries the Delhi Capitals id). Ids defined in `teams.json`. |
| `teams.json` **(R1a)** | the 20-franchise table `[{id, name, short, league, color, active}]` (`canon.TEAMS` verbatim; colors are recognizable approximate kit hexes, not official style guides). |
| `scenes/coldopen.json` **(R1a)** | per season+league: `matches`, `deliveries`, **`totals200`**, **`avg_first_innings_full`** (+ its innings count); plus `corpus` facts `{points_rendered: 316199, corpus_total: 316388, superover_balls: 189, matches: 1331, players: 938, ipl_seasons: 19, wpl_seasons: 4}` and a `definitions` block. |
| `scenes/ch1.json` **(R1a)** | Chapter 1: `ignition` (SR per balls-faced index 1..30 per era band + first-10-ball SR per season per league), `outrate` (KM-style hazard per index 1..30 per band, sample sizes, first-10 headline), `defiers` (top-5 per ball index 5/10/15/20 per band), `sixes` (per season), `aerial` (per band, with caveat), `wpl_beat` (incl. the League Maturity Clock). |
| `columnar.json.gz` | sandbox dataset: 12 parallel arrays over the same point order + `dicts` mapping codes → names. gzip level 9 |
| `payoff/ch1.json` | 16 Chapter-1 payoff variants, R1a full spec (below) |
| `ledger.json` | the payload audit (build report, excluded from its own budget math) |

## R1a recipe pins (metric definitions that reconcile with the catalog teasers)

Every number below was reconciled **exactly** against `research/metrics-catalog.md` /
`research/data-profile.md`; the definitions that make the teasers reproduce are pinned
here and asserted by `tests/test_r1a.py` via independent recounts.

- **Era bands:** IPL 2008–2010, 2011–2015, 2016–2019, 2020–2022, 2023–2026; WPL pooled
  2023–2026.
- **Balls faced:** wides excluded, no-balls counted (Ch 1 footnote convention).
- **First-10-ball SR** (balls-faced index ≤ 10): IPL 2008-10 **108.0** → 2023-26
  **135.3**; WPL pooled **110.5**. ✅ teasers exact.
- **The out-rate, ball by ball:** the per-index curve is KM-style —
  `dismissals at index n / batter-innings reaching n` (retired hurt/out censored;
  run-outs attributed to the player given out at *their own* faced-count, non-striker
  included). The **first-10 headline** uses the catalog's definition: **every**
  dismissal of a batter at faced-count 0–10 (non-striker run-outs, dismissals on wides
  and diamond ducks included) per first-10 ball faced → **5.04% vs 4.93%**. ✅ exact.
  (A striker-only/legal-ball-only definition gives 4.74% vs 4.75% — same flat story,
  but the shipped headline matches the catalog's verified computation.)
- **Six democratization:** sixes = `runs.batter == 6`; players with ≥10 sixes
  (unrestricted): 2008 **18** → 2026 **58** ✅; **top-10 hitters' share is computed
  over the ≥30-balls-faced qualifier universe** (the same universe as the catalog's
  Gini): **35.9% → 28.1%** ✅ (over *all* league sixes it would be 34.3% → 27.4% —
  the qualifier denominator is the catalog's definition and is what ships).
- **Aerial Risk Ledger:** attempt proxy = sixes + caught dismissals (caught-and-bowled
  excluded), per 100 balls faced; execution = sixes/(sixes+caught):
  **7.3 → 11.4 attempts/100, 58.7% → 67.3% execution** ✅ exact. The catalog's caveat
  ships in the artifact: caught includes keeper/slip edges (no fielding-position
  data) — stable noise, era comparisons remain valid.
- **200+ totals (cold open):** an innings — **either innings**, super overs excluded —
  totalling ≥ 200, per season. Reproduces the data-profile table exactly
  (IPL 2008 = 11 … 2026 = **65**, the You-Draw-It reveal; WPL 4/0/5/5). ✅
- **Avg first-innings score (full):** mean first-innings total excluding no-results,
  D/L-method matches, and matches whose chase target was set for < 20 overs
  (163.3 → 195.8 IPL; 156.6 → 169.1 WPL). ✅ matches the data-profile table exactly.
- **League Maturity Clock:** league year N = N-th season; **RR = ALL runs (extras
  included) / legal balls (wides AND no-balls excluded)** — the catalog's corrected
  formula. IPL years 1–4: **8.31 / 7.48 / 8.13 / 7.73**; WPL: **8.08 / 7.86 / 8.37 /
  8.54** ✅ exact. Ignition ramp at the same league age: IPL first-10 SR years 1–4
  109.9 / 101.2 / 112.8 / 104.6 vs WPL 108.2 / 104.6 / 116.7 / **112.2**.
- **Run DNA:** % of all runs (extras included) from fours (4 × count of batter fours):
  WPL **46.8%** vs modern IPL (2023-26) **33.9%**; six-share **15.5% vs 29.0%**. ✅
- **Defiers:** per ball index n ∈ {5,10,15,20} and era band, batters with ≥ 300 balls
  faced in the band, scored by
  `(survival-to-n / band survival) + (SR through 1..n / band SR) − 2`; top 5 ship with
  their survival %, SR, innings and sample size. **players = 938** = distinct people
  who faced or bowled ≥ 1 ball (939 if non-striker-only appearances counted — the
  blueprint's 938 is the faced-or-bowled definition).

## Payoff cards (Chapter 1 — "Death of the Sighter", R1a full spec)

Exactly 16 variants: 10 current IPL franchises + 5 WPL franchises + `Neutral`
(league-wide IPL, reproducing the thesis 108.0 → 135.3). Each card now carries:

- the R0 thesis fields (first-10 SR early/recent era, delta, samples, headline;
  eras IPL 2008–2010 vs 2023–2026, WPL 2023–2024 vs 2025–2026);
- **`ignition_by_era`** — SR on balls 1–10 and 11–20 per era band (IPL: the five R1a
  bands; WPL: its two card eras). Bands where a franchise bowled no balls carry null
  SRs — designed sparsity for born-late franchises, asserted, never a blank;
- **`fastest_starter`** — the franchise's best first-10-ball SR ever, min **100**
  first-10 balls faced for that franchise (Neutral: league-wide);
- **WPL cards only: `maturity_clock`** — RR + first-10 SR by league year 1–4 for both
  leagues, the four-led engine share, and templated copy. This is the bespoke
  WPL-picker payoff the release checklist requires; the harness enforces the house
  framing rule (the copy may never contain "behind").

GT, LSG and SRH (born after 2010) keep the **designed empty state**. All cards are
template + numbers; nothing is hand-authored per team. The harness asserts all 16
exist, are non-degenerate under the extended spec, and exits non-zero otherwise.

## Budgets (ledger) — actuals

- **Cold-open critical set** (`meta.json` + `groups.json` + `group_ids.u16` +
  `attrs.u8` + **`ballsfaced.u8` + `team.u8` + `teams.json` + `scenes/coldopen.json`**
  — everything needed before the cold open plays): **≤ 3 MB gz → actual 259,467 B gz
  (~0.26 MB)**. Largest members: ballsfaced.u8 139,334 B gz, attrs.u8 112,860 B gz;
  team.u8 compresses to 4,696 B gz.
- **Chapter 1** (`scenes/ch1.json` + `payoff/ch1.json`): ≤ 2 MB gz → actual 9,552 B gz.
- Sandbox columnar ≤ 2 MB gz → actual 625,823 B gz (also under the blueprint's ~0.8 MB
  target).
- Full read-through ≤ 25 MB gz → actual 894,842 B gz (~0.89 MB).

## Tests

```sh
python3 -m unittest discover -s pipeline/tests -q     # 62 tests
```

- `test_canon.py` — canonicalization tables exhaustive over the corpus in **both**
  directions, season set + `dates[0]` agreement, 23 groups, D/L = 23, super-over
  innings = 36, Gujarat teams distinct.
- `test_flatten.py` — independent recount (own ordering, own season derivation, own
  bit-packer): n_points = 316,199, full group-id + attrs stream equality, per-bit
  round-trips, super-over exclusion on the known 2017 tie, columnar integrity.
- `test_r1a.py` — the addendum artifacts against an independent recount **plus
  hand-checked anchors**: `ballsfaced.u8` full-stream equality + the hand-checked
  match (335982: McCullum 158* off **73** balls, Ganguly 12, Kohli 5 — public
  scorecard) + wides-are-exactly-the-zeros; `team.u8` full-stream equality with an
  independent rename map + the renamed-franchise spot check (335984: Delhi Daredevils
  deliveries carry the Delhi Capitals id) + WPL ids distinct from IPL namesakes
  (1358929: MI-W); `teams.json` contract (20 teams, unique shorts, 5 inactive, hex
  colors); `scenes/coldopen.json` vs the hard-coded data-profile tables (200+ series
  incl. the 65-in-2026 reveal, full-first-innings averages, match counts, corpus
  facts) and cross-artifact delivery counts vs `groups.json`; `scenes/ch1.json` —
  every curve/section recounted independently + all catalog teasers asserted as
  constants (108.0/135.3/110.5, 5.04/4.93, 7.3→11.4 + 58.7→67.3, 18→58 + 35.9→28.1,
  46.8/33.9, RR year 1–4 lists) + a full independent re-derivation of one defiers cell
  (ipl 2023-2026 @ ball 10: top-5 membership, order and scores); `payoff/ch1.json` —
  harness assertions re-run on the on-disk file, neutral reproduces the thesis, era
  labels, starter floors, WPL maturity clocks, designed sparsity for born-late
  franchises.

Snapshot constants live at the top of each test file; a new Cricsheet drop that changes
the corpus must update them consciously.
