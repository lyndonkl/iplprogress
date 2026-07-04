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
dataset + `matches.json` and writes `meta.json`; `scenes.py` emits `scenes/coldopen.json`
+ `scenes/ch1.json` + `scenes/sandbox.json` (the R1b preset); `payoff_harness.py` emits
`payoff/ch1.json` (each records its sizes
in `meta.json`); `ledger.py` audits everything on disk against the blueprint §2
budgets. The harness and the ledger exit non-zero on failure. The whole build runs in
seconds and is **byte-for-byte deterministic** (gzip level 9, `mtime=0`; JSON compact,
new artifacts key-sorted) — verified by rebuilding and diffing checksums.

## Modules

| file | role |
|---|---|
| `canon.py` | Engine #4 canonicalization: 62 raw venue strings → 37 canonical grounds, franchise renames (DD→DC, KXIP→PBKS, RCB Bangalore→Bengaluru in both leagues, Rising Pune unified; Gujarat **Lions ≠ Titans ≠ Giants**), season normalization (`'2007/08'`→2008 … — always the year the cricket was played, verified equal to `dates[0]` year for all 1331 matches), D/L flag, super-over innings detection, **and the R1a 20-franchise id table** (`TEAMS`/`team_id`): league-scoped ids 0–19 (IPL's 15 sorted by name, then the WPL's 5 — the WPL DC/MI/RCB are distinct franchises with their own ids), approximate-brand kit colors, `active` flags (Deccan Chargers, Gujarat Lions, Kochi, Pune Warriors, Rising Pune Supergiant are `false`). Every lookup raises `KeyError` on unmapped input. |
| `flatten.py` | One chronological pass emitting all per-point contract artifacts (see below). |
| `scenes.py` | R1a/R1b scene aggregates: `scenes/coldopen.json` (You-Draw-It truth series + corpus facts), `scenes/ch1.json` (ignition, out-rate, defiers, sixes, aerial ledger, WPL beat), and `scenes/sandbox.json` (R1b minimal-bowl preset + team/season facets + tap-a-ball tooltip roster). |
| `payoff_harness.py` | Payoff-card snapshot harness: emits + asserts the 16 Chapter-1 variants (R1a full spec). |
| `ledger.py` | Payload ledger vs the §2 budgets; prints the table; writes `ledger.json`. |
| `tests/` | `unittest` snapshot tests (see below). |

## The point stream (contract)

Every delivery in every innings, **excluding super-over innings**, in
**season-blocked order** — the calendar year of play, then **IPL before WPL
within a shared year**, then chronological (match date, match_id, innings
index, over, delivery index):

- **Season-blocked, not raw-chronological (R1a MF3).** Across seasons the
  stream stays strictly chronological, but within 2023 every IPL-2023 delivery
  precedes every WPL-2023 delivery (the WPL's March-2023 matches would
  otherwise interleave *ahead* of IPL 2023). This assembles "season by season"
  and restores the cold-open caption order — CO-3's "2023: the year the ceiling
  broke" fires a beat **before** the WPL constellation starts — with no scene
  change (the assembly scene measures its counter stops from the actual point
  buffer, so the buffer order *is* the assembly order). `meta.json` /
  `columnar.json.gz` carry `point_order: "season-blocked"`.
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
| `meta.json` | `{ n_points, built_at: "unknown", point_order: "season-blocked", files: {name: {bytes_raw, bytes_gz}}, n_players, n_matches: {ipl, wpl, total} }` — the v2 count fields (storyboard CO-3 title-card traceability: `n_players`, per-league + **total** `n_matches`) are added by `scenes.py`; `test_r1a` asserts they equal `scenes/coldopen.json`'s corpus block |
| `groups.json` | ordered array, index = `gi`: `{ gi, league, season, count }` × 23 |
| `group_ids.u16` | little-endian Uint16 per delivery → `gi` |
| `attrs.u8` | one byte per delivery — bits 0–2 outcome class: 0 dot · 1 single · 2 two-or-three · 3 four · 4 six · 5 other scoring ball; bit 3 wicket fell; bit 4 WPL; bits 5–7 zero |
| `ballsfaced.u8` **(R1a)** | per delivery: the striker's **1-based ball-faced index within their innings at this delivery** — wides are 0 (the batter doesn't face them), no-balls count, capped at 255 (max observed: 73 well under the cap). Powers the ignition-wall layout. |
| `team.u8` **(R1a)** | per delivery: canonical **batting-franchise id** (league-scoped; renames collapse — every Delhi Daredevils ball carries the Delhi Capitals id). Ids defined in `teams.json`. |
| `teams.json` **(R1a)** | the 20-franchise table `[{id, name, short, league, color, active}]` (`canon.TEAMS` verbatim; colors are recognizable approximate kit hexes, not official style guides). |
| `scenes/coldopen.json` **(R1a)** | per season+league: `matches`, `deliveries`, **`totals200`**, **`avg_first_innings_full`** (+ its innings count); plus `corpus` facts `{points_rendered: 316199, corpus_total: 316388, superover_balls: 189, matches: 1331, players: 938, ipl_seasons: 19, wpl_seasons: 4}` and a `definitions` block. |
| `scenes/ch1.json` **(R1a)** | Chapter 1: `ball_index_axis` (the shared balls-faced x-axis convention — per-ball curves end at exactly ball 30, NOT a capped `30+` bucket; only the wall caps — so scenes label the strips' right edge `30` and the wall's `30+`), `ignition` (SR per balls-faced index 1..30 per era band + first-10-ball SR per season per league), `outrate` (KM-style hazard per index 1..30 per band, sample sizes, first-10 headline), `defiers` (top-5 per ball index **1/3/5/10/15/20** per band — balls 1 & 3 added so the strip's tap set is fully data-backed), `sixes` (per season, incl. **`legal_balls` + `balls_per_six`** so "a six every 21 → every 12" traces to an artifact), `aerial` (per band, with caveat), `wpl_beat` (incl. the League Maturity Clock). |
| `columnar.json.gz` | sandbox dataset: **14** parallel arrays over the same point order + `dicts` mapping codes → names. R1b adds `match_index` (→ `matches.json`, so a tapped ball resolves to its match) and `wicket_kind` (dict-encoded; code 0 = `""` for non-wicket balls, so `wicket_kind != 0` ⟺ `wicket == 1`). gzip level 9 |
| `matches.json` **(R1b)** | array indexed by `match_index` (== point-stream order), each `{teams:[a,b] (canonical), season, date, stage ("Final"/"Qualifier 1"/"Eliminator"/"Match N"), venue, city, result_text ("Mumbai Indians won by 1 run"), league}`. 1,331 rows. The tooltip's **opponent** is the team in `teams` that is not the tapped ball's `batting_team`. |
| `scenes/sandbox.json` **(R1b)** | the minimal-bowl descriptor: `preset` `{match_index, label, blurb}` (the 2019 IPL Final — MI beat CSK by 1 run — resolved by league+season+stage+teams+margin, never a hard-coded index), `facets` (**team + season only**, pointing at `teams.json`/`groups.json`), and `tooltip.fields` (the tap-a-ball field roster). Everything beyond team/season facets + one preset + tooltip is deferred to R6/R7. |
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
  **`balls_per_six` = legal balls (wides AND no-balls excluded) / sixes:** 2008
  **20.8** → 2026 **11.7** ✅ (the caption's rounded "every 21 → every 12";
  `legal_balls` ships per season alongside it — column heights are raw six
  counts, so the per-ball rate is the denominator-honest comparison).
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
- **Defiers:** per ball index n ∈ {1,3,5,10,15,20} and era band, batters with ≥ 300
  balls faced in the band, scored by
  `(survival-to-n / band survival) + (SR through 1..n / band SR) − 2`; top 5 ship with
  their survival %, SR, innings and sample size (a band+index with fewer than five
  qualifiers ships a shorter list, empty if none clear the floor; every band clears
  ≥ 5 at every index in this corpus). **players = 938** = distinct people
  who faced or bowled ≥ 1 ball (939 if non-striker-only appearances counted — the
  blueprint's 938 is the faced-or-bowled definition).

## Payoff cards (Chapter 1 — "Death of the Sighter", R1a full spec)

Exactly 16 variants: 10 current IPL franchises + 5 WPL franchises + `Neutral`
(league-wide IPL, reproducing the thesis 108.0 → 135.3). Each card now carries:

- the R0 thesis fields (first-10 SR early/recent era, delta, samples, headline;
  eras IPL 2008–2010 vs 2023–2026, WPL 2023–2024 vs 2025–2026);
- **`team_pair` + `honesty`** — the team-pair sentence and the small-sample honesty
  line as **discrete fields** so the scene renders fields instead of regex-parsing
  the headline (finding #6/#8). `honesty` is non-empty for every `small_sample`
  variant (all five WPL cards) and `""` otherwise; the headline is *composed* from
  these pieces, so it stays byte-identical to v1. The harness asserts the
  invariant (non-empty honesty ⟺ small_sample);
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
  `wallheat.u8` +
  — everything needed before the cold open plays): **≤ 3 MB gz → actual 405,200 B gz
  (~0.41 MB)**. Largest members: wallheat.u8 146,050 B gz, ballsfaced.u8 139,311 B gz,
  attrs.u8 112,505 B gz; team.u8 compresses to 4,680 B gz.
- **Chapter 1** (`scenes/ch1.json` + `payoff/ch1.json`): ≤ 2 MB gz → actual 12,113 B gz
  (the balls-1/3 defiers, per-season `legal_balls`/`balls_per_six`, `ball_index_axis`,
  and the payoff `team_pair`/`honesty` fields).
- **R1b sandbox dataset** (`columnar.json.gz` + `matches.json` + `scenes/sandbox.json`,
  lazy-loaded, never in the cold-open set): ≤ 2 MB gz → actual 677,157 B gz. columnar
  655,235 B gz (grew ~30 KB gz for the `match_index`/`wicket_kind` columns — both
  compress well: match_index runs constant within a match, wicket_kind is ~98 % zeros),
  matches.json 20,686 B gz, sandbox.json 1,236 B gz. Still under the blueprint's
  ~0.8 MB target.
- Full read-through ≤ 25 MB gz → actual 1,094,470 B gz (~1.09 MB).
- The `ledger.py` rows enumerate exactly the shipped filenames (no phantom
  `draw/truth.json` / `ch1/outrate.json` rows — those never shipped; the R1a scene
  data lives in `scenes/coldopen.json` + `scenes/ch1.json`).

## Tests

```sh
python3 -m unittest discover -s pipeline/tests -q     # 93 tests
```

- `test_canon.py` — canonicalization tables exhaustive over the corpus in **both**
  directions, season set + `dates[0]` agreement, 23 groups, D/L = 23, super-over
  innings = 36, Gujarat teams distinct.
- `test_flatten.py` — independent recount (own **season-blocked** ordering, own season
  derivation, own bit-packer): n_points = 316,199, full group-id + attrs stream
  equality, per-bit round-trips, super-over exclusion on the known 2017 tie, columnar
  integrity, `point_order == "season-blocked"`; and the **order invariant asserted
  directly** — every IPL-2023 delivery precedes every WPL-2023 delivery, the year of
  play is non-decreasing across the stream, and the CO-3 counter stops still land at
  13,489 (2008) / 122,434 (thru 2015).
- `test_r1a.py` — the addendum artifacts against an independent recount **plus
  hand-checked anchors**: `ballsfaced.u8` full-stream equality + the hand-checked
  match (335982: McCullum 158* off **73** balls, Ganguly 12, Kohli 5 — public
  scorecard) + wides-are-exactly-the-zeros; `team.u8` full-stream equality with an
  independent rename map + the renamed-franchise spot check (335984: Delhi Daredevils
  deliveries carry the Delhi Capitals id) + WPL ids distinct from IPL namesakes
  (1358929: MI-W); `teams.json` contract (20 teams, unique shorts, 5 inactive, hex
  colors); `scenes/coldopen.json` vs the hard-coded data-profile tables (200+ series
  incl. the 65-in-2026 reveal, full-first-innings averages, match counts, corpus
  facts) and cross-artifact delivery counts vs `groups.json` + `meta.json` v2 counts
  (`n_players` 938, per-league + **total** `n_matches` == 1331); `scenes/ch1.json` —
  every curve/section recounted independently + all catalog teasers asserted as
  constants (108.0/135.3/110.5, 5.04/4.93, 7.3→11.4 + 58.7→67.3, 18→58 + 35.9→28.1,
  **balls-per-six 20.8→11.7** with an independent legal-ball recount, 46.8/33.9, RR
  year 1–4 lists) + `ball_index_axis` convention (per-ball curves end at exactly ball
  30, not a capped 30+ bucket) + defiers keyed **{1,3,5,10,15,20}** with 5 per index
  and a full independent re-derivation of one cell (ipl 2023-2026 @ ball 10: top-5
  membership, order and scores); `payoff/ch1.json` — harness assertions re-run on the
  on-disk file, neutral reproduces the thesis, era labels, starter floors, WPL
  maturity clocks, designed sparsity for born-late franchises, and the **discrete
  `team_pair`/`honesty` fields** (non-empty honesty ⟺ small_sample; the WPL headline is
  `team_pair + " " + honesty`, no regex).
- `test_r1b.py` — the sandbox data contract: `matches.json` length == **1,331** distinct
  matches with well-formed rows (canonical `teams`, `date` year == `season`, gazetteer
  `city`, 23 Finals / 1,249 "Match N" / 17 ties / 9 no-results) and the **inline table
  == `build_matches()`** equivalence; the `match_index` column (length n_points, every
  value a valid match, monotone non-decreasing, Uint16-range, agreeing delivery-for-
  delivery with the columnar league/season and the opponent-derivation); the
  `wicket_kind` column (code 0 == `""`, `wicket_kind != 0` ⟺ `wicket == 1` corpus-wide);
  a **spot-checked known ball** — the 2019 IPL Final (1181768) flattened by hand and
  matched delivery-for-delivery against its `match_index` slice, incl. the last ball
  (Malinga to SN Thakur, lbw, opponent MI, "Mumbai Indians won by 1 run"); and the
  `scenes/sandbox.json` preset resolving **by identity** (league+season+stage+teams+
  margin) to that same match, with team+season-only facets and the tooltip field roster.

Snapshot constants live at the top of each test file; a new Cricsheet drop that changes
the corpus must update them consciously.
