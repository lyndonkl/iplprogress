# Pipeline — "Every Ball Ever" R0 + R1a + R2a

Python 3, **stdlib only** (json, gzip, struct/array, pathlib, unittest). Flattens the
Cricsheet ball-by-ball corpus (`data/ipl_json/*.json`, `data/wpl_json/*.json`) into the
R0 data-contract artifacts, the R1a addendum (cold open + Chapter 1), and the R2a
engine tables (engine #1 par/SR+ + engine #5 entry states, first needed by Chapter 2)
under `web/static/data/`.

## Run everything

From the repo root:

```sh
python3 pipeline/flatten.py \
  && python3 pipeline/scenes.py \
  && python3 pipeline/par.py \
  && python3 pipeline/entry.py \
  && python3 pipeline/re288.py \
  && python3 pipeline/wp.py \
  && python3 pipeline/interlude.py \
  && python3 pipeline/bowlerplane.py \
  && python3 pipeline/payoff_harness.py \
  && python3 pipeline/ledger.py \
  && python3 -m unittest discover -s pipeline/tests -q
```

Order matters: `flatten.py` emits the point stream + per-point attributes + columnar
dataset + `matches.json` and writes `meta.json`; `scenes.py` emits `scenes/coldopen.json`
+ `scenes/ch1.json` + `scenes/sandbox.json` (the R1b preset) + `scenes/ch2.json` +
**`scenes/ch3.json`** (R2b — it imports `bowlerplane.build()` for the bowler-season
frontier, so the JSON frontier and the buffer coordinates are one computation); `par.py`
and `entry.py` emit the R2a engine tables under `engines/` (they read only the corpus +
`canon`, never an R1 artifact); `re288.py` and `wp.py` are the **parallel-track engines
#2/#3** (RE288 run-expectancy surfaces + the win-probability grids / Leverage Index) —
they also read only the corpus + `canon`, emit `engines/re288.json` + `engines/wp_grid.json`,
and are consumed by **R3b** (not by any R2a scene); `interlude.py` (R3b) reads those
two gate-validated engine JSONs and emits `scenes/interlude.json` — the Net Session
two-dial widget between Ch 4 and Ch 5 — so it must run **after** `re288.py`/`wp.py`; it
never edits an engine, only re-projects it; `bowlerplane.py` (R2b, engine #1
family) emits the **`bowlerplane.u8`** per-point buffer (the Chapter-3 economy x
strike-rate morph coordinate) and registers it in `meta.json` — it must run **after**
`flatten`/`scenes` (which write `meta.json`) so the manifest stays byte-deterministic;
`payoff_harness.py` emits `payoff/ch1.json`;
`ledger.py` audits everything on disk against the blueprint §2 budgets. The harness and
the ledger exit non-zero on failure. The whole build runs in seconds and is **byte-for-byte
deterministic** (gzip level 9, `mtime=0`; JSON compact, new artifacts key-sorted) —
verified by rebuilding and diffing checksums.

## Modules

| file | role |
|---|---|
| `canon.py` | Engine #4 canonicalization: 62 raw venue strings → 37 canonical grounds, franchise renames (DD→DC, KXIP→PBKS, RCB Bangalore→Bengaluru in both leagues, Rising Pune unified; Gujarat **Lions ≠ Titans ≠ Giants**), season normalization (`'2007/08'`→2008 … — always the year the cricket was played, verified equal to `dates[0]` year for all 1331 matches), D/L flag, super-over innings detection, **and the R1a 20-franchise id table** (`TEAMS`/`team_id`): league-scoped ids 0–19 (IPL's 15 sorted by name, then the WPL's 5 — the WPL DC/MI/RCB are distinct franchises with their own ids), approximate-brand kit colors, `active` flags (Deccan Chargers, Gujarat Lions, Kochi, Pune Warriors, Rising Pune Supergiant are `false`). Every lookup raises `KeyError` on unmapped input. |
| `flatten.py` | One chronological pass emitting all per-point contract artifacts (see below). |
| `scenes.py` | R1a/R1b/R2a/R2b scene aggregates: `scenes/coldopen.json` (You-Draw-It truth series + corpus facts), `scenes/ch1.json` (ignition, out-rate, defiers, sixes, aerial ledger, WPL beat), `scenes/sandbox.json` (R1b minimal-bowl preset + team/season facets + tap-a-ball tooltip roster), `scenes/ch2.json` (the anchor elegy), and **`scenes/ch3.json`** (R2b "The Counterrevolution": the Attack-Containment frontier + Pareto hull + Ashwin ghost trail, Dot+, the Dismissal-DNA rivers, the Death-Wide Tax, the two dot-grid finals, the middle-overs crack ratio, the WPL two-clocks beat, the 20 gravity-defier payoff cards, and the footnote layer). Imports `bowlerplane.build()` for the bowler-season data. |
| `bowlerplane.py` | **R2b, engine #1 family** — the bowler-season economy x strike-rate plane. Emits the per-point buffer `bowlerplane.u8` (2 bytes/point in field order: byte 0 = bowler-season economy, byte 1 = bowling strike rate) AND exposes `build()` (the bowler-season aggregates + the phase-economy par + the phasepar-convention batter marginal) consumed by `scenes.build_ch3`. Economy = (batter runs + wides + no-balls) per 6 legal balls, byes/legbyes excluded; strike rate = legal balls per bowler-credited wicket. |
| `par.py` | **Engine #1** (R2a) — par baselines / SR+ family. Emits `engines/phasepar.json` (season × over-phase par, the Ch 2 anchor baseline + par worm), `engines/par.json` (the shrunk + calibrated venue × innings conditional model + the anchor-extinction / sub-120-occupancy validation roll-ups), and `engines/srplus.json` (per-batter-season SR+). See the model + thresholds section below. |
| `entry.py` | **Engine #5 full** (R2a) — entry states / derived batting positions. Emits `engines/entry.json`: one row per batter-innings with entry ball-index, wickets fallen, innings#, derived batting position, chase RRR at entry, and the innings outcome. |
| `re288.py` | **Engine #2** (parallel track, consumed R3b) — RE288 run-expectancy surfaces. Emits `engines/re288.json`: expected first-innings runs-to-come on the (overs-bowled × wickets-lost) grid, per era band + evidence-masked pooled WPL, weighted-isotonic-smoothed so runs-to-come is monotone in both axes. Gate-tested by `tests/test_engines.py`. |
| `wp.py` | **Engine #3** (parallel track, consumed R3b) — win-probability lookup grids + Leverage Index. Emits `engines/wp_grid.json`: P(chase win) on the (era × overs-left × wickets-in-hand × required-rate) grid (monotone in rate & wickets), the LI byproduct on the pooled grid, and the first-innings defend curve. Gate-tested by `tests/test_engines.py` (the binding calibration check). |
| `interlude.py` | **R3b — the Net Session interlude scene.** Consumes the gate-validated `engines/wp_grid.json` (win) + `engines/re288.json` (runs) and emits `scenes/interlude.json`: both dials re-indexed to one widget coordinate `[overs_left-1][wickets_in_hand-1]` (win adds a required-rate bucket), per era band + an all-time pooled default (win from `ipl pooled`; runs **derived** here — RE288 ships no IPL-pooled surface — as the evidence-weighted mean of the five era surfaces, monotone-repaired with the engine's own isotonic step) + the WPL toggle with both evidence masks (win `n<12`, runs `n<15`). Resolves three presets from the grids (**"Dhoni, 2011 final"** read from the corpus as the real chase-of-206 state; **"needing 10 an over at halfway, 2010"** and **"the same chase, 2025"** — one scoreboard, two era surfaces), the validated era anchor, and data-bound footnotes (calibration, wicket-lever-early/rate-lever-late, mask thresholds). Every preset's quoted number is the exact grid readout at its cell, so the copy can never contradict the meter. Reads engines only; never edits them. |
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
| `engines/phasepar.json` **(R2a)** | Engine #1 season × over-phase par: per (league, season, phase ∈ pp/middle/death) the **exact** mean batter-runs per ball faced + `par_sr`. The Chapter-2 anchor baseline and the par worm; no shrinkage (kept raw so the anchor share reproduces the catalog). |
| `engines/par.json` **(R2a)** | Engine #1 full model: the venue × innings **shrunk + per-league-season-calibrated** conditional cells (`E[runs.batter | league, season, phase, venue, innings]`, parallel arrays), the anchor definition + `anchor_extinction` roll-up (per season + era band), the `sub120_occupancy` roll-up, and the `srplus_calibration` check (pooled SR+ = 100 per league-season). |
| `engines/srplus.json` **(R2a)** | Engine #1 SR+ leaderboard: per batter-season (≥ 100 balls) `{league, season, batter, balls, runs, sr, expected_runs, srplus}`. `srplus = 100 × runs / expected_runs`; 100 = an average batter of the same league/era/phases/venues. |
| `engines/entry.json` **(R2a)** | Engine #5 entry states: columnar arrays over 20,488 batter-innings — `{league (0/1), season, match_index, innings, batter (dict-coded), position, entry_ball (legal-ball index), wickets, rrr (chases only, else null), balls_faced, runs, dismissed}` + a `batter` names dict. |
| `engines/re288.json` **(engine #2, R3b)** | RE288 run-expectancy surfaces. Per surface (5 IPL era bands + pooled evidence-masked WPL) a 20×10 grid `re[o][w]` = expected first-innings runs-to-come from `o` overs bowled, `w` down (runs.total, extras included), first innings only, non-D/L. Weighted-isotonic-smoothed → monotone non-increasing in both wickets and overs; each cell carries its raw `n`; WPL cells with `n < 15` carry `masked=1`. Each surface ships a `calibration` block (pooled predicted == actual). |
| `engines/wp_grid.json` **(engine #3, R3b)** | Win-probability lookup grids + Leverage Index. `second_innings.surfaces` — per surface (5 era bands + `ipl pooled` + evidence-masked WPL) a 20×10×10 grid `wp[overs_left][wickets_in_hand][rrr_bucket]` = P(chase win), monotone non-increasing in required rate & non-decreasing in wickets; the pooled surface also carries `leverage_index`. `first_innings_defend` — P(bat-first win \| final-total bucket) per era, monotone in total. `calibration` — the binding reliability table + the raw era anchor. Built empirically (a lookup, never a live model), target.overs==20, non-D/L. |
| `scenes/interlude.json` **(R3b)** | The Net Session two-dial widget. `state_space` + `index` (the widget coordinate: `win[era][overs_left-1][wickets_in_hand-1][rrr_bucket]`, `runs[era][overs_left-1][wickets_in_hand-1]`, with the `rrr_edges`); `surfaces.win` (20×10×10 per era, engine #3 verbatim) + `surfaces.runs` (20×10 per era, engine #2 re-indexed, plus a derived `ipl pooled` default); `wpl` (both evidence masks + evidenced/masked cell counts + the "not enough WPL cricket yet" note); `presets` (Dhoni 2011 final + the same-chase-two-eras pair, each with `win_pct`/`expected_runs` equal to their grid cell and voice-guide copy); `era_anchor` (the validated ~23%→~31% headline + `delta_points`); `meters`/`sliders`/`intro` copy; `footnotes` (calibration, wickets-early/rate-late, mask thresholds). ~120 KB raw / ~23 KB gz. |
| `scenes/ch3.json` **(R2b)** | Chapter 3 "The Counterrevolution". `frontier` (the Attack-Containment plane: `under7` share per era + season, the per-league-season Pareto `hull`, the Ashwin `ghost_trail`, the refuted econ~SR `correlation`, and the `axis` encoding the buffer shares), `dot_plus` (season dot rate + Dot+ leaderboard + dot-scarcity index), `dismissal_dna` (era shares + per-season `rivers` counts), `death_wide_tax` (per-season death wides/100 + the doubling), `dot_grid` (the 2009 + 2026 Finals as 120-cell outcome grids), `crack_ratio` (middle-overs, per era), `wpl_beat` (the two clocks), `gravity_defiers` (20 franchise True-Economy cards), `footnotes` (True Economy 7.79→9.38, True Wickets/24, Phase Fingerprint, FIB, the refuted correlation, conventions), and `bowlerplane_buffer` (the `bowlerplane.u8` decode spec). |
| `bowlerplane.u8` **(R2b)** | Per-point buffer, **2 bytes/point** in the field point order (season-blocked, super overs excluded — identical to the other buffers). Byte 0 = the delivery's bowler-season economy, quantized linearly over [4.0, 16.0] RPO → 0..254 (clamped); byte 1 = its bowling strike rate over [8.0, 60.0] legal-balls-per-wicket → 0..254 (clamped), `255` = the "no strike rate" sentinel (the bowler-season took no bowler-credited wicket). Lets the field condense every ball toward its bowler-season's coordinate on the economy × strike-rate plane (Ch 3's controlling morph). Wides/no-balls carry their bowler-season coordinate like any delivery; every delivery has a bowler, so there are no non-bowler deliveries. Decode: `economy = 4 + b0/254*12`; `strike_rate = 8 + b1/254*52` (b1 < 255). |
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

## Engine #1 — par baselines / SR+ family (R2a, `par.py`)

The piece's era-honest currency and the baseline Chapter 2's anchor definition is
measured against. Every number below is asserted by `tests/test_par.py` against an
independent recount.

- **Over-phases** (0-based over index): `pp` = overs 1–6 (0–5), `middle` = overs 7–15
  (6–14), `death` = overs 16–20 (15–19).
- **Balls faced:** wides excluded, no-balls counted (the SR convention, identical to
  `ballsfaced.u8` / `scenes.py`). Runs = `runs.batter`.
- **Phase-par (the marginal, `phasepar.json`) — EXACT, no shrinkage:** per (league,
  season, phase) the raw mean batter-runs per ball faced; `par_sr = 100 × that`. Kept
  raw on purpose — it is the anchor definition's "season-phase par SR" and the Ch 2 par
  worm, and rawness is what makes the anchor share reproduce the catalog.
- **Conditional model (`par.json`) — shrunk + calibrated:** `E[runs.batter | league,
  season, phase, venue, innings]`. Each raw cell mean is empirical-Bayes shrunk toward
  its season-phase parent with **pseudo-count `SHRINK_K = 50` balls faced**
  (`E = (Σruns + K·parent) / (n + K)`), then every league-season's cells are **rescaled
  so pooled expected = pooled actual** — i.e. pooled SR+ over a whole league-season is
  **exactly 100** ("100 = league-average-of-own-time"; `srplus_calibration.max_abs_dev_from_100 = 0`).
- **SR+ (`srplus.json`):** `SR+ = 100 × Σ(actual runs.batter) / Σ(E[runs.batter])` over
  the exact balls a batter faced (each ball priced by its conditional cell). Emitted per
  batter-season, min **100 balls faced** (1,117 batter-seasons).
- **Anchor innings** (catalog Anchor Extinction Index — `ANCHOR_MIN_BALLS = 15`,
  `ANCHOR_SR_RATIO = 0.85`, `ANCHOR_MAX_BOUNDARY_SHARE = 0.12`): balls faced ≥ 15 **AND**
  innings runs < 0.85 × phase-weighted par runs (SR < 0.85 × contemporaneous
  phase-weighted par SR, using the exact `phasepar` marginal) **AND** boundary balls
  (`runs.batter ≥ 4`) < 12% of balls faced. **Anchor-ball share** = balls in anchor
  innings / all balls faced: **IPL 2008-10 14.75% → 2023-26 8.35%** (a 43% collapse, the
  catalog's 14.8 → 8.5); WPL **9.41%** (catalog ~9–10% — born post-anchor).
- **Sub-120-SR occupancy** (catalog Ball-by-Ball DNA): share of qualifying batter-seasons
  (≥ 100 balls) striking under 120. **Qualifier counts are exact** vs the catalog's
  "150 early / 249 recent / 81 WPL" — **150 / 250 / 81** — and the share runs **40.67%
  (2008-10) → 2.40% (2023-26)** (recent exact; the early band is a knife-edge — a handful
  of batter-seasons sit right at SR 120, hence ~2 pts above the catalog's 38.7%, within
  the "≈" tolerance).

## Engine #5 (full) — entry states / derived batting positions (R2a, `entry.py`)

One row per **batter-innings** (20,488 rows; 867 distinct batters), asserted by
`tests/test_entry.py` against an independent per-match recompute + a delivery-for-delivery
spot check of the 2019 IPL Final.

- **Entry event:** the batter's first delivery as striker **or** non_striker.
- **`entry_ball`:** legal-ball index of the innings at entry (legal = not a wide and not
  a no-ball, matching over structure and `target.overs × 6`); openers enter at 0.
- **`wickets`:** wickets fallen before entry (retired hurt/out are not wickets); 0 for
  openers.
- **`position`:** derived batting position = order of entry (openers are 1 and 2,
  striker-first, then 3, 4, …); contiguous 1..k per innings.
- **`rrr`:** required run rate at entry, **chases only** (innings 2 with a `target`):
  `(target.runs − score) × 6 / (target.overs × 6 − entry_ball)`; `null` for first innings
  and the one D/L chase whose recorded target predates the rain revision. 9,961 chase
  entries carry an RRR.
- **Outcome (self-sufficient for "performance conditional on entry"):** `balls_faced`
  (SR convention), `runs` (`runs.batter`), `dismissed` (a real dismissal of this batter
  fell — retired hurt/out excluded).

## Chapter 3 recipe pins (R2b — "The Counterrevolution")

Every number below is recounted independently by `tests/test_r2b.py` and, where the
catalog gives a teaser, reconciled **exactly** (the pipeline artifact is authoritative).

- **Conventions.** Economy = (batter runs + wides + no-balls) per 6 **legal** balls,
  byes/legbyes excluded (project-wide). Legal ball = not a wide and not a no-ball. Dot =
  legal ball with `runs.total == 0`. Strike rate = legal balls per **bowler-credited**
  wicket (caught, bowled, lbw, stumped, caught-and-bowled, hit-wicket; **not** run outs
  or retirements). Over-phases: powerplay 1-6, middle 7-15, death 16-20.
- **Attack-Containment frontier — economy under 7.0** (bowler-seasons ≥ 90 legal balls):
  IPL 2008-10 **49 / 169 = 29.0%** → 2023-26 **4 / 267 = 1.5%** ✅ (the catalog's "49 of
  169 (29%)" → "4 of 267 (1%)", exact on numerator, denominator and share). The 90-ball
  floor is what reproduces those exact counts.
- **The refuted econ~SR correlation:** Pearson r across qualifying bowler-seasons is weakly
  **positive**: IPL 2008-10 **+0.12** → 2023-26 **+0.03**; WPL **+0.34** ✅ exact. The
  hull's retreat carries the story, not the correlation.
- **Dot rate (Dot+ backdrop):** IPL 2008-10 **37.6%** → 2023-26 **33.0%**; WPL **38.5%**
  (≈ IPL 2009) ✅ exact. Dot+ leaderboard (≥ 200 legal balls, season × over-number
  baseline) leads with Narine-2012 (142.6), Bumrah-2024/25, Rashid-2020 — elite dot
  manufacture (Dot+ 130+).
- **Dismissal DNA** (shares over **bowler-credited** dismissals — run outs/retirements
  excluded from the denominator — with "caught" **excluding** caught-and-bowled): bowled+lbw
  **27.4% → 21.3%**, caught **65.2% → 74.0%**, stumped **4.2% → 1.9%** ✅ (catalog
  27.4/65.2/4.2 → 21.3/74.1/1.9); WPL stumped **6.8%** ✅. That exact cut (bowler-credited
  denominator, caught-minus-c&b) is what makes all three teasers reproduce at once.
- **Death-Wide Tax:** death-over (16-20) wides per 100 legal balls **doubled** — IPL 2008-10
  **3.13** → 2023-26 **6.45** (×2.06); WPL just **2.69** (the wide-yorker arms race is a
  men's-league phenomenon). These are the recount; the catalog's ≈3.3/6.7/2.8 are the same
  wide-delivery-per-100-legal metric on an earlier snapshot (the WPL 2.69≈2.8 match confirms
  the delivery-count basis over a wide-runs basis).
- **Middle-overs crack ratio** = P(wicket after 3+ straight dots) / P(wicket after a scoring
  ball): WPL **1.18** (above 1 — dots still buy wickets) vs modern IPL **0.81** (below 1 —
  the IPL defused them), IPL 2008-10 **0.84**. Story-exact (catalog WPL 1.11 / IPL 0.84);
  the level is definition-sensitive, so the tests assert WPL > 1 > IPL-recent, not a constant.
- **True Economy (the gravity-defier payoff):** par = the league-season economy for the
  bowler-season's exact legal-ball phase mix (a death specialist priced against death par);
  TrueEcon = par − actual. Best per franchise (all 20): MI **JJ Bumrah 2024 (+3.22)**, SRH
  **Rashid Khan 2020 (+2.52)**, KKR **SP Narine 2026 (+3.00)**; WPL cards carry a designed
  short-sample flag. League bowler-charged economy rose **7.79 → 9.38** RPO ✅ (catalog exact).
- **Dot-grid finals** (each a full 120-legal-ball first innings, dot rate at its season's
  average, so the erosion is honest): **2009 Final** Deccan Chargers 47 dots (39.2% ≈ season
  39.1%) vs **2026 Final** Gujarat Titans 38 dots (31.7% ≈ season 32.7%). Resolved by
  (league, season, stage == "Final"), never a hard-coded index.
- **Footnotes.** FIB drift caught **60.0% → 72.6%**, run outs **12.1% → 5.2%** ✅ (catalog
  59.9/72.3, 12.0/5.3). Phase Fingerprint is definition-sensitive: the shipped recompute
  (death share ≥ 2× league death availability, min 60 balls) gives 0% (2008) → a mid-era
  peak → **0% (2026)** — the emergence-then-slump shape the catalog reports (its 0→17.3,
  peak 20.6 lands higher under its own availability recipe; both directions ship, the
  catalog value flagged as a reference).
- **Engine #1 consumption (gate).** True Economy's par is engine #1's phase-par family
  flipped to the bowling side. `bowlerplane.build` recomputes the batting marginal (batter
  runs per ball faced — wides excluded, no-balls counted, engine #1's exact denominator) and
  `test_r2b` asserts it reconciles **byte-for-byte** with `engines/phasepar.json`
  `expected_runs_per_ball` for every (league, season, phase), so Ch 3 can never drift from
  engine #1.

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
- **Chapter 2 + parallel-track engines** (all `engines/`, lazy-loaded per chapter): the
  ledger sums the whole `engines/` prefix against the ≤ 2 MB gz per-chapter bar → actual
  **194,753 B gz**. Ch 2 (engine #1/#5): entry.json 119,583, srplus.json 24,489, par.json
  9,694, phasepar.json 1,305. Parallel track (engine #2/#3, consumed R3b): wp_grid.json
  33,050, re288.json 6,632 — the two new engines add only ~40 KB gz, leaving ~1.8 MB of
  headroom in the bucket.
- **Chapter 3** (`scenes/ch3.json` + `bowlerplane.u8`, lazy-loaded at Ch 3 entry): ≤ 2 MB gz
  → actual **77,377 B gz**. bowlerplane.u8 632,398 B raw / **67,898 B gz** (2 bytes × 316,199
  points; the bowler-season coordinate runs constant within a bowler's spell, so it gzips
  hard), ch3.json **9,479 B gz** (frontier hull + ghost trail + Dot+/DNA/death-wide series +
  the two 120-cell grids + 20 gravity-defier cards + footnotes).
- Full read-through ≤ 25 MB gz → actual ~1.58 MB gz (R2a engines + the parallel track + the
  R2b Ch 3 buffer).
- The `ledger.py` rows enumerate exactly the shipped filenames (no phantom
  `draw/truth.json` / `ch1/outrate.json` rows — those never shipped; the R1a scene
  data lives in `scenes/coldopen.json` + `scenes/ch1.json`).

## Tests

```sh
python3 -m unittest discover -s pipeline/tests -q     # 193 tests
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
- `test_par.py` **(R2a, engine #1)** — the par tables against a fully independent
  recount (own phase splitter, own anchor classifier, own batter-season tallies):
  `phasepar` marginal matches per (league, season, phase); anchor-ball share per era band
  matches and reproduces the catalog (**14.75% → 8.35%**, 43% collapse, WPL 9.41%);
  sub-120 qualifier counts **exact** (150 / 250 / 81) and recent share **exact** (2.4%);
  SR+ calibration **exactly 100** per league-season; the SR+ leaderboard is qualifier-
  gated, self-consistent (`srplus == 100 × runs / expected_runs`) and deterministically
  sorted; conditional cells well-formed (canonical venues, valid phases, positive E);
  and the on-disk files equal a fresh `build_docs()` byte-for-byte.
- `test_entry.py` **(R2a, engine #5)** — entry states against an independent per-match
  recompute: positions contiguous from 1, openers enter at ball 0 with 0 wickets,
  `entry_ball`/`wickets` monotone in position, RRR only on chases (≥ 98% of 2nd-innings
  entries), value ranges; the **full-corpus batter-innings count + opener count** match
  the independent recount; and the 2019 IPL Final's entry states match the raw file
  delivery-for-delivery (incl. both chase openers' target-rate RRR). On-disk ==
  `entry_doc(build())` byte-for-byte.
- `test_engines.py` **(engines #2/#3, the binding §5 validation gate — consumed R3b)** —
  RE288: runs-to-come monotone non-increasing in **both** wickets and overs on every
  surface, pooled prediction == actual, `RE(0,0)` == era average total, the era-drift
  anchor `RE(10 overs, 3 down)` 88 → 97 (catalog 90.6 → 98.3) cross-checked against an
  independent raw cell recount, and the WPL evidence mask. WP grid: monotone non-increasing
  in required rate & non-decreasing in wickets on every surface; the **calibration check**
  independently re-scores every second-innings state from the emitted era grids and bins by
  predicted WP — weighted mean \|pred − actual\| **0.015 < 0.03**, each ≥500-ball bin within
  0.06; the era anchor (9+ RPO, ~60 balls left: **0.23 → 0.31**, blueprint 0.243 → 0.318)
  reproduced from raw; the defend curve monotone in total and 170-189 repriced **~0.70 →
  ~0.40** (catalog 74% → 38%); the Leverage Index present, non-negative, endgame cells > 3.
  Both engine files on-disk == a fresh `build_doc()` byte-for-byte.

- `test_r2b.py` **(R2b, Chapter 3)** — `scenes/ch3.json` + `bowlerplane.u8` against a fully
  independent season-blocked recount (own economy/strike-rate/dismissal classifiers): the
  frontier's economy-under-7 counts **exact** (49/169 → 4/267) and matched to the recount per
  era; the refuted correlation (+0.12/+0.03/+0.34); the Pareto hull is a real lower-left
  staircase (economy strictly descends as strike rate rises); the Ashwin ghost trail spans
  ≥ 12 frontiers with economy rising end-to-end; dot rate 37.6/33.0/38.5 and Dot+ leaderboard;
  Dismissal DNA 27.4/65.2/4.2 → 21.3/74.0/1.9 (bowler-credited denom, caught-excl-c&b) matched
  to the recount; death wides doubling 3.13 → 6.45 (WPL 2.69); crack ratio WPL > 1 > IPL-recent,
  matched to the recount; the two dot-grid finals (120 cells each, dot% self-consistent, 2009
  darker than 2026); 20 gravity-defier cards (all franchise ids, WPL small-sample flagged,
  TrueEcon = par − actual, Bumrah/Rashid headliners); footnotes (True Economy 7.79/9.38, FIB
  60.0/72.6 + 12.1/5.2, Phase-Fingerprint emergence-then-slump); the **buffer contract**
  (length == 2 × n_points, deterministic re-encode, the SR sentinel count equals the balls in
  0-wicket bowler-seasons and the economy byte never sentinels, a coordinate round-trip for MI
  Bumrah-2024); the **engine #1 gate** (Ch 3's batter marginal == `engines/phasepar.json`
  `expected_runs_per_ball` for every (league, season, phase)); and `ch3.json` on-disk ==
  `ch3_doc(build_ch3())` byte-for-byte.

- `test_r3b.py` **(R3b, the Net Session interlude)** — `scenes/interlude.json` as a faithful
  re-projection of the gate-validated engines (the engine correctness itself is `test_engines.py`'s
  job): every embedded win surface is engine #3 **verbatim** and every runs surface is engine
  #2 re-indexed cell-for-cell; the derived `ipl pooled` runs default is monotone and bracketed
  by the era surfaces; both dials are monotone in the widget coordinate (runs rise with overs +
  wickets, win falls with rate + rises with wickets). Preset integrity: each preset's `win_pct` /
  `expected_runs` **equals** its grid cell (copy can't contradict the meter); the Dhoni preset is
  the real 2011 IPL final rebuilt from the corpus (CSK batted first, Bangalore chased the target,
  ball-one state); the same-chase pair shares one scoreboard on two era surfaces with win + runs
  both rising and both cells carrying ≥20 real observations. The era anchor equals the grid's
  (~0.23 → ~0.31); the WPL win mask flags only `n<12` cells and the runs mask only `n<15` cells,
  counts consistent, never all / never none; the wicket-lever footnote is true in the emitted grid
  (early ≫ late). On-disk == a fresh `build_doc()` byte-for-byte, within the 2 MB chapter budget.

Snapshot constants live at the top of each test file; a new Cricsheet drop that changes
the corpus must update them consciously.
