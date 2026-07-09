# Pipeline — "Every Ball Ever" R0 + R1 + R2 + R3

Python 3, **stdlib only** (json, gzip, struct/array, pathlib, unittest). Flattens the
Cricsheet ball-by-ball corpus (`data/ipl_json/*.json`, `data/wpl_json/*.json`) into the
R0 data-contract artifacts, the R1a addendum (cold open + Chapter 1), the R2a
engine tables (engine #1 par/SR+ + engine #5 entry states, first needed by Chapter 2),
the R2b/R3a chapter artifacts, and the R3b consumables (the Net Session interlude +
Chapter 5's WPA/restate buffers and scene doc) under `web/static/data/`.

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
  && python3 pipeline/ch5.py \
  && python3 pipeline/ch6.py \
  && python3 pipeline/ch7.py \
  && python3 pipeline/ch8.py \
  && python3 pipeline/ch9.py \
  && python3 pipeline/ch10.py \
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
`ch5.py` (R3b-2) consumes the two gate-validated engine JSONs (never rebuilding them)
and emits Chapter 5's `wpa.u8` + `restate.u8` per-point buffers and `scenes/ch5.json`,
registering all three in `meta.json` — it runs **after** `re288.py`/`wp.py` (it reads
their output) and after `flatten`/`scenes`/`bowlerplane` (manifest order);
`ch6.py` (R4a) is engine- and buffer-free: it does its own corpus pass (never reading an
R1–R3 artifact), computes the Season Constellation Map in pure Python (Jensen-Shannon
distances → classical MDS via a Jacobi eigensolver → per-phase Procrustes alignment) and
emits only `scenes/ch6.json`, whose controlling morph reuses the existing `group_ids.u16`;
it runs **after** `flatten`/`scenes` for manifest order (it registers `scenes/ch6.json` in
`meta.json`);
`ch7.py` (R4b) is likewise engine- and buffer-free: its own corpus pass (never reading an
R1–R4a artifact) computes the Impact Player natural experiment (IPL vs the rule-free WPL
diff-in-diff), the License Index at identical match states, the rule-change event-study
placebo grid, the Playbook Decoder, the honest null, the 16 team-playbook payoff variants,
and — critically — the **impact-sub spark index list** (the ~517 field point indices of the
deliveries carrying an Impact Player substitution, in `group_ids.u16` point order), emitted
inline in `scenes/ch7.json` because the raw-JSON `replacements` field is not in the shipped
columnar dataset (so unlike Ch 2/3/4 the render cannot derive membership client-side; the
index list is the Ch 5 over-rail precedent). The twin-rivers controlling morph reuses the
existing `group_ids.u16` + `attrs.u8`, so Ch 7 adds no per-point buffer; it runs **after**
`flatten`/`scenes` for manifest order (it registers `scenes/ch7.json` in `meta.json`);
`ch8.py` (R5a) is also engine- and buffer-free: its own corpus pass in flatten's exact
season-blocked point order (never reading an R1–R4b artifact) computes the belief-audit
report card (FAIL toss / FAIL reviews / FAIL spells / FAIL-with-a-residual momentum / PASS
required rate) and emits `scenes/ch8.json`: the **match-dots** controlling-morph table (1,331
match centroids + the `match_bounds` block-start point indices the field binary-searches
in-shader, adding NO per-point attribute so the field holds at 14), the **988 review-chip
subset** (point indices / team / outcome, reusing `aDismissal`/`aTeam`/`aRiverPos`), the toss
crossover, the spell strips + cold-return tax, the precomputed momentum shuffle nulls (a
fixed-seed permutation, so two runs emit identical bytes), the required-rate curve, the WPL
adoption curve, the 16 payoff variants, and the footnote layer. It imports `h2h` (Engine #6)
for the demoted Matchup Engineering footnote lead ONLY (the usable head-to-head history grew
12.4%→42.1%). No new per-point buffer (`pairing.u16` belongs to Ch 9); it runs **after**
`flatten`/`scenes` for manifest order (it registers `scenes/ch8.json` in `meta.json`);
`ch9.py` (R5b) does its own single corpus pass in flatten's exact season-blocked point
order (never reading an R1–R5a artifact) and imports `h2h` (Engine #6) for the person
registry, striker-dismissal resolution, and the empirical-Bayes dominance shrinkage
(mu 1.3322, k 51.2). It reproduces the validated **duel-web force layout** (players as
nodes, duels as edges, ForceAtlas2-style with degree-scaled repulsion kr=0.02, linear
attraction weight=log1p(balls)/log1p(30), gravity kg=0.30, 550 iters, **seed 42**, laid
out per connected component then packed — the IPL giant centred, the disjoint WPL web in
a corner) and emits `scenes/ch9.json`: the `nodes[277]` (244 men + 33 women) and
`duels[1,691]` (≥30-ball pairings, id stable by balls-desc, each with dominance color =
clamp((EB-shrunk runs/ball − mu)/half, ±1); +1 batter-red, −1 bowler-blue) tables and
their per-duel ball-by-ball `replays`, the **auction heartbeat** (per-season league-mean
squad overlap with a min-max envelope: IPL resting 0.461, the five mega-auction troughs
2011/2014/2018/2022/2025 averaging **0.186**, plus the WPL series 2024 .476/2025 .536/2026
.257), the **loyalty spectrum** (one-club share among 4th-plus-season players, ~27 in 100
at its 2012 peak → ~12 at the 2022 trough, then an honest expansion-driven uptick; max
shirts AJ Finch 9), the **WPL age-matched comparison**, the **16 payoff variants** (10 IPL
"through the churn" + 5 WPL forming-fast + neutral), the **Collapse Contagion** footnote
figure (aftershock ~0.95, a wicket makes the next less likely), and the `ch9-*` footnote
strings. It ALSO emits the one new per-point buffer **`pairing.u16`** (per delivery the
duel id 0..1690 or the `0xFFFF` dust sentinel, in flatten season-blocked point order,
aligned with `group_ids.u16`), delivered to the field as a DATA TEXTURE (`uPairingTex`
indexed by point-index in-shader), **NOT a 15th vertex attribute — the field holds at
14**. Three honest deltas ship straight (232 duels ran 8+ seasons not 235; loyalty ~27→~12
not 28→15; mega trough 0.186 not 0.185). It must run **after** `flatten`/`scenes` for
byte-determinism (it registers `scenes/ch9.json` + `pairing.u16` in `meta.json`);
`ch10.py` (R6a, **the FINALE**) does its own single corpus pass (registry-resolved pids for
the per-player tables, batting-team for the franchise payoff) and imports `seismo` (the
pure-Python PELT + Bayesian changepoint machinery, byte-identical to
`scratchpad/ch10_seismo.json`) and `par` (Engine #1, SR+ / own-era par for the Teleporter).
It emits **`scenes/ch10.json`** and **no new buffer** (Ch 10 is buffer-free like Ch 6/Ch 7:
the `ribbon` controlling morph is a pure `position.x` function, so the field holds at 14
attributes, and the Teleporter subset rides the spare bit2 of the existing `aRunOut` byte):
the league-pulse **seismograph** (per-season metric ladders + the strictness dial's precomputed
break-index sets β0.3→6 eras … β14→1, verified 6→2, with each crack's ball-position and Bayesian
posterior 0.15–0.44), the **fault-map** subway (metric lines, break stations, the 2023/2024/2014
interchanges, the sixes-before-scoring gap), the **bridge-player** verdict (league SR 141.72→150.59
= +8.87, 56 bridge batters, the within/turnover shift-share ≈1/3 vs ≈2/3, the three-suspect card),
the **Teleporter** (Machine A Sehwag 2008 translated through time — naive ghost vs honest re-quote
with band < gap; Machine B Gayle 2011 +56.7% vs Fraser-McGurk 2024 +35.4% percent-above-par bar-swap,
never a z-score), the **convergence clock** (men's run rate crossing ten ≈2028.8, the WPL forward
clock), the 2021 venue-leg micro-era, the 16 payoff variants, and the `ch10-*` footnotes. Six honest
deltas ship straight (sixes broke 2014 then 2018 not a clean 2018; ≈two-thirds turnover not three-
quarters; naive ceiling ≈224 not 228; "how far above his own era" a percent gap never a z; WPL six-
hitting off the clock). It must run **after** `flatten`/`scenes` for byte-determinism (it registers
`scenes/ch10.json` in `meta.json`);
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
| `ch5.py` | **R3b-2 — Chapter 5 "What a Ball Is Worth".** Consumes the gate-validated `engines/wp_grid.json` + `engines/re288.json` (never rebuilds them; adds two documented derived views: mid-first-innings WP = the era defend curve at a projected total of runs-so-far + RE runs-to-come, interpolated between bucket midpoints — exactly the view `wp.py` designates for R3b — and per-ball RE by interpolating the era surface across the over axis). Emits the **`wpa.u8`** per-point buffer (signed-quantized WPA, batting-team perspective, sentinel 255 for D/L / undecided / short-target matches — the matches the grids exclude), the **`restate.u8`** per-point buffer (the ball's RE-grid cell, `over*10 + wickets_down`, the controlling-morph coordinate), and `scenes/ch5.json` (defended band, RE drift + third-wicket validation, linear weights + per-season price board, Wicket Value Index, finisher cliff, the 2019-final scrub over + WP worm, league WPA headlines, 20 franchise payoff cards with tappable over replays, WPL beats, footnotes incl. the demoted chase-difficulty + era-swap exhibits, and both buffer decode specs). The scrub match and the era-swap innings resolve **by identity**, never a hard-coded index. |
| `ch6.py` | **R4a — Chapter 6 "Two Dialects" (IPL × WPL, beside the path not on it).** Its own corpus pass (no engine, no per-point buffer — the controlling morph reuses `group_ids.u16`) plus a pure-Python linear-algebra core (Jacobi eigensolver, classical MDS, 2×2 orthogonal-Procrustes/polar factor, Jensen-Shannon divergence). Emits `scenes/ch6.json`: the **Season Constellation Map** — each of the 23 season-groups placed by the JS distance between its 7-way per-ball outcome distribution (dot/single/two-or-three/four/six/wicket/extras), classical MDS to the all-phase MASTER star layout, each per-phase layout (PP 1-6 / middle 7-15 / death 16-20) Procrustes-aligned to it so the WPL never flips sides; emits star (x,y) per phase (stable box), the IPL chronological worm, each WPL star's nearest-IPL neighbour per phase (dotted threads) and the two-truths pairing (outcome-mix twin IPL 2008 vs run-rate twin IPL 2022); the **League Maturity Clock** (WPL yr4 8.54 == IPL yr15), **Run DNA** helix (four 46.8 vs 33.9, six 15.5 vs 29.0), **Stumping Signature** (WPL 5.2-7.9% vs IPL 2026 1.4%), **Photo-Finish** rate (WPL 24.1% the tightest league), the batting ladder + depth (WPL 2025 pos-7+ 15.3%), the 16 sister-franchise payoff variants, and the footnote layer (Star Gravity/Gini, Competitive Balance win-HHI, Powerplay Fear, Twos Culture). Registers `scenes/ch6.json` in `meta.json`. |
| `ch7.py` | **R4b — Chapter 7 "The Twelfth Man" (the Impact Player rule as a natural experiment).** Its own corpus pass (no engine, no per-point buffer — the twin-rivers controlling morph reuses `group_ids.u16` + `attrs.u8`) in flatten's exact season-blocked point order. Emits `scenes/ch7.json`: the **natural experiment** (IPL run rate range-bound 7.5-8.7 for 2008-2022 then 8.99/9.56/9.63/9.88, vs the rule-free WPL 8.08→8.54; diff-in-diff ≈ +0.9 RPO with disclosed confounds — on screen "the control group", "diff-in-diff" one click deep), the **License Index** (at ≥4 down / overs 7-16: SR 116.8→129.9 while the dismissal rate held ~flat 4.88→4.95; top order took the licence most, +18.0% vs +11.0% for 6-8), the **event-study placebo grid** (every candidate season 2012-2025's before/after level shift + SE + t, emitted whole so the placebo cursor is a lookup; the true 2023 date clears the entire pre-rule placebo cloud, with the honest disclosure that 2024's raw magnitude edges it as the break deepens), the **Playbook Decoder** (subs at the innings break 51.8%→35.7%), the **honest null** (entry entropy flat; top-3 SR 131.5→155.3; bowlers/innings 5.79→6.12), and the **impact-sub extraction**: 556 Impact Player events across 517 distinct deliveries (WPL 0 — the control arm), the bat-vs-bowl reinforcement split (256/300), and the **spark index list** (the 517 field point indices carrying an event, the render's subset-highlight membership). 16 team-playbook payoff variants (10 IPL playbook cards + 5 WPL control-arm cards + neutral). Registers `scenes/ch7.json` in `meta.json`. |
| `ch8.py` | **R5a — Chapter 8 "The Captain's Brain" (the belief audit, report card FFFFP).** Its own corpus pass in flatten's exact season-blocked point order (no engine, no per-point buffer). Imports `h2h` (Engine #6) for the demoted Matchup Engineering footnote lead ONLY. Emits `scenes/ch8.json`: the **match-dots** controlling-morph table (1,331 match centroids `[x, y, toss_class, result]` + `match_bounds`, the 1,331 monotone block-start point indices the field binary-searches in-shader — NO per-point attribute, the field holds at 14), the **988-chip review subset** (`indices`/`team`/`outcome`, reusing `aDismissal`/`aTeam`/`aRiverPos`), **Belief 1 toss** FAIL (field-first 42.9→77.1 while the chase never paid better 54.3/59.6/52.8; the two crossing lines + crossing point; toss-to-win ~50% every era), **Belief 2 reviews** FAIL (988 reviews 29.6% upheld; the honest delta — the success rate DEGRADED 32.8→28.1, a free fall to 16.9 by 2026, at 1.26→1.87/match), **Belief 3 spells** FAIL (one-over share 54.7→64.1, WPL 75.3; the honest delta — the cold-return tax GREW +0.16→+0.30, strict +0.18→+0.41; near-median example strips), **Belief 4 momentum** FAIL-with-a-residual (the wicket myth collapses 0.93 anti; hitting is mostly good batters batting with a FLAT ~1.07 real sliver; the raw edge 1.21→1.16 that fades is kept off the sliver claim; all shuffle nulls precomputed, fixed seed), **Belief 5 required-rate** PASS (chase powerplay 7.62→9.19 now above the middle overs, ahead-at-halfway 31.7→37.5, with the honest caveat that chasing still wins ~53%), the **WPL transmission** (a two-season adoption curve 54.5→~100, reviews 30.5 vs 29.6, out-fragments at 75.3; analytics-native, never "behind"), the **16 payoff variants** (10 IPL "your captains' report card" incl. RCB 96%/38.7% and CSK 13%/Chepauk and DC last 19.4% + 5 WPL bespoke transmission cards + neutral), and the footnote layer (`ch8-matchdots`/`toss`/`review`/`spell`/`momentum`/`required`/`wpl`/`payoff`/`matchup`/`dew`). Byte-deterministic. Registers `scenes/ch8.json` in `meta.json`. |
| `ch9.py` | **R5b — Chapter 9 "The Living League" (institutions churn, the human fabric persists).** Its own single corpus pass in flatten's exact season-blocked point order; imports `h2h` (Engine #6) for person resolution + striker-dismissal + empirical-Bayes dominance (mu 1.3322, k 51.2). Reproduces the validated **duel-web force layout** (277 players as nodes, 1,691 ≥30-ball duels as edges; ForceAtlas2-style, degree-scaled repulsion kr=0.02, linear attraction log1p(balls)/log1p(30), gravity kg=0.30, 550 iters, **seed 42**, per connected component then packed — IPL giant centred, disjoint WPL web in a corner; the two leagues share no players so they are never normalized together — byte-identical to `scratchpad/ch9_layout.json`). Emits `scenes/ch9.json`: `duel_web` (`nodes[277]` {id,name,x,y,deg,era,league} + `duels[1691]` {id,a,b,bat,bowl,balls,runs,dis,seasons,span,dom,color,px,py} sorted by balls-desc so duel_id is stable + a `meta` block with the balls split 79,378 in-duel / 236,821 dust and the dominance-color constants), the `replays` (per-duel faced-ball code list + season run-length for the tap-a-duel strip), the `heartbeat` (per-season league-mean squad overlap + min-max envelope, IPL + WPL, the five mega-auction troughs), the `loyalty` spectrum (one-club share among 4th-plus-season players + the Finch 9-shirt record), the `wpl` age-matched comparison, the `collapse` figure (Collapse Contagion aftershock), the 16 `payoff` variants, and the `footnotes` (`ch9-duel`/`heartbeat`/`loyalty`/`payoff`/`collapse`). ALSO emits the one new per-point buffer **`pairing.u16`** (duel id or 0xFFFF dust per delivery, delivered as a data texture `uPairingTex`, holding the field at 14 vertex attributes). Byte-deterministic (seed 42, gzip mtime=0, sorted keys). Registers both artifacts in `meta.json`. |
| `seismo.py` | **R6a helper** (imported by `ch10.py`, emits nothing) — the pure-Python changepoint machinery: PELT (L2/SSE cost, per-changepoint penalty β) + an offline Bayesian product-partition changepoint posterior (Normal-mean) over the IPL/WPL season-by-season metric series. `build_seismo()` reproduces `scratchpad/ch10_seismo.json` exactly: the per-season metric ladders, the penalty sweep + six-to-two strictness stops, the fault map, the Bayesian posteriors (the crack-opacity source), the ribbon crack ball-positions, the composite league-pulse strictness curve, the 2021 India-vs-UAE venue-leg split, and the under-powered WPL micro-series. Stdlib only, no random, byte-deterministic. |
| `ch10.py` | **R6a — Chapter 10 "The Era Machine" (the FINALE: the data draws its own fault lines).** Its own single corpus pass (registry-resolved pids for the per-player tables, batting-team for the franchise payoff); imports `seismo` (the changepoint machinery) and `par` (Engine #1, SR+ / own-era par). Emits **`scenes/ch10.json`** and **no new buffer** (buffer-free like Ch 6/Ch 7: the `ribbon` morph is a pure `position.x` function so the field holds at 14 attributes, and the Teleporter subset rides the spare bit2 of the existing `aRunOut` byte): the ribbon geometry hints (316,199 balls, per-season ball starts, time-axis ticks), the **seismograph** (per-season six/run/wide/dot/boundary ladders + the strictness dial's precomputed break-index sets β0.3→6 eras / β0.6→4 / β1.0→3 / β4.0→2 / β14→1, verified 6→2, each crack carrying its ball-position and Bayesian posterior 0.15–0.44, plus the per-metric medium-strictness cracks), the **fault-map** subway (sixes 2014/2018/2022/2024, scoring 2023/2024, wides 2022/2024, dots 2015-16/2023, boundaries 2023/2024; the 2023/2024/2014 interchanges; the sixes-broke-five-years-before-scoring gap), the **bridge-player** verdict (league SR 141.72→150.59 = +8.87, 56 bridge batters ≥60 balls both seasons, within-player +2.9 vs turnover +5.9 ≈ 1/3 vs 2/3, the three-suspect card Ch7/here/Ch1), the **Teleporter** (Machine A: Sehwag 2008 SR 184.55 translated through time, naive ghost 223.7 vs honest re-quote 213.6 in 2026 with band ±5.5 < gap 10.1 asserted at build; Machine B: Gayle 2011 +56.7% vs Fraser-McGurk 2024 +35.4% percent-above-par bar-swap, raw SR gap 50.9, **never a z-score**), the **convergence clock** (men's run rate 8.99/9.56/9.63/9.88 crossing ten ≈2028.8 band 2027–2031; the WPL forward clock, run rate 8.08/7.86/8.37/8.54 slope +0.19 reaching the men's-2026 level ≈2033, six-hitting .196/.201/.229/.219 off the clock), the 2021 venue-leg micro-era (India 8.41, UAE 7.71), the 16 payoff "Your adapters" variants (10 IPL + 5 WPL forward-clock + neutral), and the footnote layer (`ch10-seismo`/`bridge`/`teleporter`/`convergence`/`microera`/`payoff`). Six honest deltas ship straight; no z-score on screen; zero em dashes. Byte-deterministic (no random, gzip mtime=0, sorted keys). Registers `scenes/ch10.json` in `meta.json`. |
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
| `wpa.u8` **(R3b-2)** | Per-point buffer, 1 byte/point in field point order: the ball's **Win Probability Added** from the **batting team's** perspective. `byte = 127 + round(wpa*127)` clamped to 0..254 (decode `wpa = (byte-127)/127`, so 127 = 0, resolution ~0.008); **255 = sentinel** "no WPA" — the ball's match is D/L, had no decided result, or set a chase target other than a full 20 overs (6,579 balls, exactly the matches the win grids exclude). Second innings reads the era grid at (overs_left, wickets in hand, required-rate bucket); first innings uses the documented projected-total defend view; terminal balls resolve to the actual result (ties to the super-over winner), so per-chase WPA telescopes exactly to (result − first-state WP). Powers the biggest-swing subset-highlights. |
| `restate.u8` **(R3b-2)** | Per-point buffer, 1 byte/point in field point order: the ball's RE-grid state cell packed `over*10 + wickets_down` (0..199). `over` = the delivery's over index 0..19 (wides/no-balls carry the over they were bowled in); `wickets_down` = dismissals before this delivery (0..9). Both innings packed; filter with the columnar `innings` array if a scene wants first innings only. Drives the Chapter 5 controlling morph (balls arrayed on the 20-over × 10-wicket grid, colored by the era RE surfaces in `scenes/ch5.json` / `engines/re288.json`). |
| `scenes/ch5.json` **(R3b-2)** | Chapter 5 "What a Ball Is Worth": `defended_band` (170-189, raw + fitted, per era), `re_drift` (both engine surfaces + diff + the third-wicket validation), `linear_weights` (per era) + `price_board` (per season), `wicket_value` (+ the 2024-26 window + run-inflation context), `finisher` (the moving cliff), `scrub` (the 2019 final last over, ball-by-ball, WP worm + observed endgame dots + `point_indices`, the six field point indices the over-rail lifts — never client-derived), `wpa` (league headlines, top-10 swings, `season_gallery` — one ball per league-season for the neutral payoff gallery — closure + coverage; swing rows carry `point_index` + `state_cell`), `payoff` (20 franchise cards: most valuable ball ever + tappable over replay + 4 runners-up, WPL short-history state; every ball row carries `point_index` + `state_cell` for the C5-11 single-point ignite), `wpl_beat` (RE evidence mask + observed-outcome dots + finisher cohort + `match_counts`, the corpus-counted 88/1,331 the C5-10 captions bind to), `footnotes` (crediting, tie rule, first-innings WP view, smoothing, chase-difficulty + era-swap demoted exhibits), and both buffer decode specs. |
| `scenes/ch8.json` **(R5a)** | Chapter 8 "The Captain's Brain" (the belief audit). `match_dots` (the controlling-morph table: `centroids` = 1,331 × `[x, y, toss_class, result]` — x normalized start date, y a fixed low-discrepancy spread, toss_class 0 bat-first / 1 field-first, result 1 chase-won / 0 bat-first-won / −1 undecided; `bounds` = 1,331 monotone block-start point indices in flatten point order the field binary-searches in-shader; `season`/`league` per match; `axis_ticks`), `review_subset` (the 988 IPL review deliveries: `indices`/`team`/`outcome` for `field.setReviews`, reusing `aDismissal`/`aTeam`/`aRiverPos`), `toss` (FAIL: per-era field-first 42.9→77.1 + chase-win 54.3/59.6/52.8, the two crossing lines + crossing point, the captain-sim lookup), `review` (FAIL: 988/29.6% + the DEGRADED delta 32.8→28.1 free-falling to 16.9, per-team chip lanes + leaderboard), `spell` (FAIL: one-over 54.7→64.1 WPL 75.3, the GROWN cold-return tax +0.16→+0.30 / strict +0.18→+0.41, near-median example strips), `momentum` (FAIL-with-residual: 7 claims × 4 groups with precomputed shuffle-null histograms + the batter-stratified residuals, wicket 0.93 anti + boundary residual FLAT ~1.07), `required_rate` (PASS: chase PP 7.62→9.19, ahead-at-halfway 31.7→37.5), `wpl` (the two-season adoption curve 54.5→~100, reviews 30.5, one-over 75.3), `payoff` (16 variants), `footnotes` (10 `ch8-*` strings). Engine- and buffer-free; no per-point buffer (`match_bounds` is inline, holding the field at 14 attributes). |
| `scenes/ch9.json` **(R5b)** | Chapter 9 "The Living League". `controlling_morph` (free→duelweb: layout code 11, the pairing delivered as `uPairingTex`, four inert-default scalars duelReveal/duelDominance/duelDustDim/strandRecede), `duel_web` (`meta` {n_duels 1691, n_nodes 277, n_men 244, n_women 33, balls_split {total 316,199 · in-duel 79,378 · dust 236,821 · faced_total · faced_in_duel 77,125}, dominance_color {center_mu 1.3322, half_range}, eb {mu,sigma2,tau2,k 51.2}, force {seed 42, kr 0.02, kg 0.30}, legibility}; `nodes[277]` {id, name, x, y ∈[-1,1], deg, era, league}; `duels[1691]` sorted by balls-desc {id, a, b (node indices), bat, bowl (names), balls, runs, dis, seasons, span:[first,last], dom, color ∈[-1,1] (+1 batter-red/−1 bowler-blue), px, py (strand-midpoint cluster centre)}), `replays[1691]` (per duel {c:[ball codes 0..6 runs / 7 wicket], sb:[[season,count]] run-length} for the tap-a-duel strip; codes sum to 77,125), `heartbeat` (`ipl` {series [{season,mean,lo,hi,n}] 2009-2026 with a min-max envelope, mega_years {2011,2014,2018,2022,2025}, mega_mean **0.186**, nonmega_mean 0.461, sixth_lowest 2024=.419}, `wpl` {series 2024 .476/2025 .536/2026 .257, first_reset}), `loyalty` (series [{season,pct,one_club,veterans}], peak 2012≈26.9, trough 2022≈12.5, start/end, max_shirts {name "AJ Finch", n 9, teams, shorts}), `wpl` (n_players 33, n_duels, age_matched {wpl_duels_by_season3, ipl_duels_by_season3}, heartbeat), `collapse` (aftershock ≈0.95 — a wicket makes the next less likely), `payoff` (16 variants: 10 IPL "through the churn" {rivalry, reset, loyalist} + 5 WPL forming-fast {rivalry, duel_count} + neutral), `footnotes` (`ch9-duel`/`heartbeat`/`loyalty`/`payoff`/`collapse`). Every on-screen number reads from here; three honest deltas ship straight (232 duels 8+ seasons, loyalty ~27→~12, mega trough 0.186). |
| `pairing.u16` **(R5b)** | The one new per-point buffer, **little-endian Uint16 per delivery** in flatten season-blocked point order (aligned with `group_ids.u16` / `attrs.u8`): value = the duel id `0..1690` the ball belongs to, or `0xFFFF` (65,535) the DUST sentinel for a ball not in any ≥30-ball duel. 316,199 entries, 632,398 B raw, ~95 KB gz; 79,378 non-dust. Delivered to the field as a DATA TEXTURE (`uPairingTex` texelFetch'd by point-index in-shader, since `position.x` already holds the point index), NOT a 15th vertex attribute, so the field holds at 14. Reproduces `scratchpad/ch9_pairing.u16` byte-for-byte. |
| `scenes/ch10.json` **(R6a, the FINALE)** | Chapter 10 "The Era Machine". `controlling_morph` (free→ribbon: layout code 12, a pure `position.x` function, `new_buffer: null`, the Teleporter subset on the spare `aRunOut` bit2, three inert-default scalars teleportProgress/teleportLift/teleportOthersDim + two float uniforms uRibbonBandY/uRibbonBandHalf), `ribbon` (total_points 316,199, per-season `cum_deliv_start`, `time_axis_ticks`, the ball-spacing legend), `seismograph` (per-season `series` {six_rate, run_rate, rpo, wide_rate, dot_rate, boundary_rate}, `record` {1,243 matches, 295,557 legal deliveries}, `strongest_faults` {wide-2022 .44, run-2023 .37, boundary-2023 .35}, per-metric medium-strictness `cracks` {metric, year, ball_pos, ribbon_frac, posterior}, `strictness` {composite dial `stops` β0.3/0.6/1.0/4.0/14 → 6/4/3/2/1 eras, each with per-crack ball_pos + posterior, default_beta 0.6/4-era}, full `bayes_posterior`), `fault_map` (`metrics`[5] {key, label, primary, stations:[{year, ball_pos, posterior}]}, `hero_lines` [six_rate, run_rate], `interchanges` 2023/2024/2014, `order_gap` {six 2018 vs scoring 2023 = 5 yr}), `bridge` (league_sr_2023 141.72, league_sr_2024 150.59, jump +8.87, n_bridge 56, within_mean/within_pooled ≈+2.9, `shift_share` {total 8.87, within 2.93/33%, turnover 5.94/67%, components}, `verdict` three co-equal panels), `teleporter` (`machine_a` {anchor_sr 185, default Sehwag {balls 220, runs 406, sr 184.55, percentile 98.0, naive_ceiling 224, `translations`[2023-26] {naive, honest, band_lo/hi, band_halfwidth, gap, band_lt_gap}}, `integrity` band<gap at 2026}, `machine_b` {Gayle +56.7%, Fraser-McGurk +35.4%, raw_sr_gap 50.9}), `convergence` (`mens` {series, recent, fit_window 2016-26, crosses_ten {central 2028.8, band_years [2027,2031]}, today 9.88}, `wpl` {run_rate slope +0.19 reaches ≈2033, six_rate off_the_clock}), `micro_era_2021` (India 8.41, UAE 7.71), `payoff` (16 variants: 10 IPL "Your adapters" {riser, legend honest-2026, climb} + 5 WPL forward-clock + neutral), `footnotes` (`ch10-seismo`/`bridge`/`teleporter`/`convergence`/`microera`/`payoff`). Every on-screen number reads from here; no new per-point buffer (the field holds at 14). |
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

## Chapter 5 recipe pins (R3b-2 — "What a Ball Is Worth")

Every number is recounted independently by `tests/test_ch5.py`; the artifact is
authoritative over the catalog teasers (which were read on an earlier corpus
snapshot). Era bands are the engines' (2008-10 vs 2023-26 unless stated).

- **Defended band (the repriced scoreboard):** first-innings totals **170-189**,
  full first innings (120 legal balls or all out), decided (ties to the
  super-over winner), non-D/L: **30/41 = 73.2% (2008-10) → 21/54 = 38.9%
  (2023-26)**; WPL 9/14. (Catalog 74% → 38%.) The fitted defend-curve readout
  over the same buckets ships alongside (~0.70 → ~0.40).
- **Third-wicket collapse (RE Surface Drift):** raw observed runs-to-come at the
  **start of the 7th over** (6 overs bowled), 2 down vs 3 down, IPL first
  innings, non-D/L: cost **11.81 (2008-10) → 3.48 (2023-26)**, and **1.04** on
  the catalog's sharper **2024-26** window (its ~0.4 was an earlier snapshot;
  RE(7th over, 2 down) = 110.3 matches the catalog exactly). The smoothed
  engine surfaces read 12.07 → 6.39 at the same cell (isotonic smoothing spreads
  thin-cell evidence); both ship, labelled.
- **Linear weights (the price board):** `weight = RE(after) − RE(before) + runs
  on the ball`, era RE surface interpolated across the over axis, **first
  innings, non-D/L**; wicket balls priced as one wicket event and excluded from
  run classes. **Dot −0.898 → −1.115; single −0.013 → −0.248 (the flip:
  value-neutral to value-losing); six +4.76 → +4.59; wicket event −6.96 →
  −7.62.** (Catalog: dot −0.85 → −1.12, single −0.01 → −0.27.) The per-season
  price board prices each season's balls on its era band's surface.
- **Wicket Value Index:** each **bowler-credited** wicket priced `R(state, w) −
  R(state, w+1)` at its exact (legal balls bowled, wickets) state from **raw
  observed runs-to-come cells over both innings**, non-D/L (chase truncation is
  real evidence): **4.155 → 5.113 (+23.1%)** across the chapter's era bands vs
  run inflation **+18.8%** — wickets appreciated faster than runs. On the
  catalog's 2024-26 window: **5.51 (+32.6%)**, reproducing its "+33%" (its
  3.99 → 5.30 was the same recipe on an earlier snapshot).
- **Finisher / the moving cliff:** chases read at **exactly 30 balls left**,
  20-over targets, non-D/L, decided; bands of required rate. **8-10 RPO: 17/31 =
  54.8% → 35/41 = 85.4%** (catalog 54.8 → 85.0); 10-12: 34.6% → 50.0% (catalog
  34.6 → 51.4); 12+: ~12% both eras. The **fatal RRR** (chase becomes a loser
  more often than not) moved **~10 → ~12**. WPL 8-10: **9/11 = 81.8%** (catalog
  ~75% on the earlier snapshot) — between the IPL eras on a tiny sample.
- **The scrub over (set piece #2):** resolved **by identity** (2019 IPL Final,
  MI beat CSK by 1 run) to `match_index` **755**; innings 2, over 19 (the 20th),
  Malinga bowling all six: Watson 1, Jadeja 1, Watson 2, Watson 1 + **run out**,
  Thakur 2, **Thakur lbw** — needed-before 9/8/7/5/4/2, CSK from WP 0.715 to 0.
  The worm is the era-correct grid readout (`ipl 2016-2019`); because the grid
  buckets required rate, three balls hold flat, so each ball also carries the
  raw all-IPL `observed` (needed, balls-left) win count as honest dot texture.
- **WPA buffer conventions:** batting-team perspective; sentinel = the 6,579
  balls of D/L (23) / undecided / short-target matches; per-chase closure is
  exact (max telescoping gap ~3e-16, asserted). Mean |WPA| per ball is ~flat
  across eras (0.013-0.016): modern cricket repriced outcomes, it did not get
  swingier ball-for-ball.
- **Payoff:** per franchise (all 20, league-scoped ids, renames collapse), the
  biggest positive swing toward the team batting **or bowling**; runners-up from
  distinct matches; the top ball ships its full over as a tappable replay with a
  team-perspective worm. MI's card is DR Smith's last-ball four off Hilfenhaus
  (2012, +0.988); WPL cards carry the designed short-history state.
- **Demoted footnote exhibits:** chase difficulty (30-42 off the last 24, 5+
  wickets in hand): **67.6% → 88.1%** (catalog 69 → 88); era swap: Gilchrist's
  2008 chase hundred — the same target's failure chance at ball one, 29 in 100
  on the 2008-10 grid vs 16 in 100 on the 2023-26 grid.

## Chapter 8 recipe pins (R5a — "The Captain's Brain", the belief audit)

Every number reconciles **exactly** with `research/storyboards/r5a-chapter8-storyboard.md`
§3 (the verified-number index) and the R5a scout recount. ARTIFACT WINS: the emitted JSON is
the on-screen source, and where the recount differs from a blueprint teaser the recount ships
(three honest deltas are shipped straight, never fudged).

- **Match-dots:** one dot per match, all 1,331 (1,243 IPL + 88 WPL, the actual corpus file
  count; the storyboard's "1,244 + 89" was off by one each, the artifact carries the real
  count) resolved from 316,199 field balls. x = normalized start date; y = a fixed
  low-discrepancy spread (`frac((i+1)·φ)`), so **dot size and brightness encode nothing**.
  `match_bounds[i]` = the block-start point index of match i in flatten's exact season-blocked
  point order (monotone non-decreasing) — the field binary-searches these in-shader, adding
  **no per-point attribute** (holds at 14).
- **Belief 1 toss (FAIL):** field-first share = the winner's toss decision to field; per era
  **42.9 / 55.8 / 82.4 / 70.1 / 77.1** (2026 = 82.4). Batting-second win rate among decided
  matches: **54.3 / 53.1 / 59.6 / 54.5 / 52.8** (the true humped shape, never "flat"). The two
  lines CROSS between 2008-10 and 2011-15. Toss-to-win ~50% every era (53.2/48.4/57.0/50.3/50.7).
- **Belief 2 reviews (FAIL):** only "struck down"/"upheld" exist (type unreliable, kept out).
  **988 reviews, 292 upheld = 29.6%.** Pre-2022 (2018-21) 302 at 1.26/match, 32.8%; from 2022
  686 at 1.87/match, 28.1%. **Honest delta: accuracy DEGRADED** — per-season 34.7/33.1/29.1/24.8/
  **16.9** (2026). The 988-delivery subset is emitted in field point order for the chips.
- **Belief 3 spells (FAIL):** a spell = a bowler's consecutive-over run from one end (even/odd
  over-index runs). One-over-spell share **54.7 → 64.1** (WPL 75.3; IPL 52.2→67.8 season to
  season). **Honest delta: the cold-return tax GREW** — over-number-matched (≥5 overs a bin),
  every first-of-spell over vs continuation: **+0.16 / +0.28 / +0.30**; the stricter cold-
  re-entry read **+0.18 / +0.34 / +0.41**. WPL tax ~0, dropped on screen. Example strips are
  NEAR-MEDIAN innings, never cherry-picked extremes.
- **Belief 4 momentum (FAIL with an honest residual):** each claim = P(outcome | prior) / base
  (1.0 = no effect), against a permutation null shuffled within (innings × phase) then within
  (innings × phase × batter). All nulls precomputed at build time with a **fixed seed** (a
  lookup, not a client permutation) → byte-deterministic. The wicket myth does NOT clear:
  wicket|wicket **1.00 / 1.09 / 0.93** (anti in the modern era, WPL 0.77). Hitting clears raw
  (boundary|boundary **1.21 / 1.19 / 1.16**) but the batter-held residual is a thin **~1.07**
  that holds FLAT (1.072 / 1.084 / 1.066) — only the confounded raw edge fades, so the sliver
  claim never says it is disappearing.
- **Belief 5 required-rate (PASS):** chase run rate by phase (all runs / 6 legal balls, 2nd
  innings, non-D/L, full 20-over target): PP/mid/death **7.62/7.61/8.99** (2008-10) → **9.19/
  8.75/10.38** (2023-26); PP jumped +1.57 above the middle overs. Ahead-at-halfway **31.7 →
  37.5**. The honest caveat: the pacing shape flipped, but chasing still wins ~53% (Belief 1).
- **WPL transmission:** a two-season adoption curve **54.5 → 59.1 → 100 → 95.5** (22 matches a
  season), pooled 77.3; chase-win 59.8 (stated bare, un-caused); reviews 30.5% over 203 (vs
  29.6); one-over-spell 75.3 (vs 64.1). Analytics-native, never "behind".
- **Payoff (16):** home ground = the franchise's most-frequent participation venue; own
  field-first@home + chase-win@home + the league-wide review-discipline rank. RCB 96%/38.7%
  (rank 1), CSK 13%/Chepauk, DC 19.4% (rank 10 of 10). 5 WPL bespoke transmission cards
  ("born into the analytics age") + neutral. Two separate facts, not cause and effect, ~20-odd
  home games each.
- **Matchup footnote (`ch8-matchup`, demoted):** LED with the raw material growing — usable
  head-to-head history (≥12 prior faced balls, via Engine #6 `h2h.usable_history`) **12.4%
  (2009) → 42.1% (2019) → ~32% post-2022**; the score itself is weak (~1.2×, no adoption ramp),
  kept off screen.

## Chapter 9 recipe pins (R5b — "The Living League")

Every number reads from the emitted `scenes/ch9.json` (ARTIFACT WINS). The force layout is
byte-identical to the scout's validated `scratchpad/ch9_layout.json`; the dominance is Engine
#6's (`h2h.py`) empirical-Bayes shrinkage. Three honest deltas ship straight, never fudged
toward a teaser.

- **The duel web.** A duel = a batter-bowler pairing that faced ≥ **30** legal balls (wides
  excluded, the `h2h` convention). **1,691 duels** between **277 players (244 men + 33 women)**.
  Players are nodes, duels are edges (weight = balls). Layout: **ForceAtlas2-style**, repulsion
  `kr·(deg_i+1)(deg_j+1)/d` (degree-scaled — the de-hairballer), attraction linear
  `log1p(balls)/log1p(30)`, gravity `kg·(deg+1)·pos`, **kr=0.02, kg=0.30, 550 iters, seed 42**,
  laid out **per connected component then packed** (the IPL giant centred at (−0.18, 0) scale
  0.78; the disjoint 33-player WPL web at (0.66, 0.62) scale 0.30 — the two leagues share no
  players so they are never normalized together). Duel ids are stable (balls desc, then the pair
  key). Node/duel arrays reproduce `ch9_layout.json` field-for-field.
- **The balls split.** Of the **316,199** balls, **79,378 (25.1%)** land in one of the 1,691
  duels and **236,821 (74.9%)** stay as dust (77,125 of the faced-ball total sit in a duel).
- **Dominance color.** Per duel, `color = clamp((shrunk_runs_per_ball − mu) / half, ±1)`, +1
  batter-red / −1 bowler-blue, `mu = 1.3322`, `half = 2·sd` of the shrunk per-duel values. EB
  constants match `h2h.eb_constants` (`k = 51.2`). Because the value is shrunk, most strands land
  pale (near-even). **Kohli vs Jadeja = duel 0: 160 balls, 179 runs, 3 dismissals, 14 seasons
  (2009-2025); shrunk 1.17 → bowler-blue color −0.539** (Jadeja edged it).
- **Honest delta 1 — long duels.** **232** duels ran eight seasons or longer, by a strict recount
  counting only seasons the pair actually faced a ball (not the teaser's 235).
- **Auction heartbeat.** Per-season league-mean squad overlap (intersection/union of each
  franchise's roster vs the prior season, canonical identity so renames collapse), with a min-max
  envelope across franchises. IPL resting mean **0.461**; the five mega-auction years
  **{2011, 2014, 2018, 2022, 2025}** are the five lowest, mean **0.186** (honest delta 2 — not
  the teaser's 0.185), a clean gap to the sixth-lowest (2024 = .419). WPL series 2024 .476 /
  2025 .536 / 2026 .257 (its first big reset).
- **Honest delta 3 — loyalty.** One-club share among players in their 4th+ IPL season (only ever
  one franchise, measured season by season): peaks at **~27 in 100 (2012, 26.9)** and falls to a
  trough of **~12 (2022, 12.5)**, roughly a halving (not the teaser's 28→15); it then ticks back
  up honestly as the two newest franchises' four-season players are one-club by definition. Most
  shirts: **AJ Finch, 9** (DC/GL/KKR/MI/PWI/PBKS/RR/RCB/SRH).
- **WPL age-matched.** By its third season the WPL had formed **51** ≥30-ball duels vs the IPL's
  **62** in its own first three seasons — forming fast at the same age, never "behind".
- **Collapse Contagion (demoted footnote).** Pooled wicket-after-wicket lift **≈ 0.95**, below
  one — a wicket makes the next ball slightly *less* likely to be another, consistent with
  Chapter 8's wicket-after-wicket 0.93.
- **Payoff (16).** 10 IPL "through the churn" cards (longest-spanning own duel + squad churn at
  the last mega-auction + longest-serving one-club player), 5 WPL forming-fast cards (longest
  rivalry so far + duel count), 1 neutral. No "behind" in any WPL copy; every read data-bound.
- **`pairing.u16`.** Per delivery the duel id 0..1690 or the `0xFFFF` dust sentinel, flatten
  season-blocked point order (aligned with `group_ids.u16`); delivered as a data texture
  `uPairingTex`, NOT a 15th vertex attribute (the field holds at 14). Reproduces
  `scratchpad/ch9_pairing.u16` byte-for-byte.

## Chapter 10 recipe pins (R6a — "The Era Machine", the FINALE)

Every number reads from the emitted `scenes/ch10.json` (ARTIFACT WINS). The changepoint
segmentations are byte-identical to the scout's validated `scratchpad/ch10_seismo.json` (via
`seismo.build_seismo()`); the Teleporter's own-era par is Engine #1 (`par.py`) SR+. **Buffer-free
like Ch 6 / Ch 7** — the `ribbon` controlling morph is a pure `position.x` function (no 15th
attribute, the field holds at 14) and the Teleporter subset rides the spare bit2 of the existing
`aRunOut` byte, so R6a adds NO new per-point buffer. Six honest deltas ship straight; **no z-score
appears on screen** (footnotes only); zero em dashes.

- **The seismograph.** The date-ordered record of **1,243 men's matches, 295,557 legal
  deliveries**. PELT (SSE cost, per-changepoint penalty β) on the standardized per-season series
  finds the breaks; an offline Bayesian product-partition posterior (**0.15 to 0.44**, so most
  cracks are drawn faint) is the crack-opacity source. Staggered break years: **sixes 2014** then
  2018/2022/2024, **runs an over 2023** (the single strongest fault, posterior .37) then 2024,
  **wides 2022** then 2024, **dots 2015-16** then 2023, **boundaries 2023** then 2024. The
  strictness dial is the composite league-pulse penalty sweep, verified **β0.3 = 6 eras (2009,
  2010, 2014, 2023, 2024) → β0.6 = 4 → β1.0 = 3 → β4.0 = 2 (2023) → β14 = 1**, six loosen to two
  exactly. Each crack's `ball_pos` is the per-season cumulative delivery index (flatten point
  order, IPL first), so it doubles as its position on the full 316,199-ball ribbon. **Honest delta:**
  the dominant six break is 2014 (dead-ball plateau ending), with 2018 a real second station, so
  the copy ships "2014, then 2018," never a clean 2018.
- **The bridge-player verdict.** League batting SR **141.72 (2023) → 150.59 (2024) = +8.87**.
  **56** bridge batters faced ≥ 60 balls in both seasons; held against themselves they gained
  about **+2.9** (mean +2.7 / pooled +2.9). A within/between shift-share over all batters (ball-share
  weighted): within-player **+2.93 (33%)**, turnover **+5.94 (67%)** — so about two-thirds was new
  faces and new roles, not the same players hitting harder. **Honest delta:** ~2/3 turnover, not
  3/4 (the footnote ships "two-thirds to three-quarters" for the stricter qualified set). The
  three-suspect card (the rule Ch7 / new faces here / the skill climb Ch1) is three co-equal panels,
  never a partition.
- **The Teleporter.** Machine A translates **Sehwag 2008 (220 balls, 406 runs, SR 184.55; league
  SR 128.98)** through time: the naive league-ratio ghost reaches **~215.5 (2024) / ~223.7 (2026)**,
  a ceiling near **224** (**honest delta:** not 228 — the league SRs never rise high enough); the
  honest rank-preserving (98th-percentile) re-quote reaches **~200.1 / ~213.6**, its ±1-percentile
  band half-width **strictly less than the naive-vs-honest gap at every dial stop** (asserted at
  build: band ±5.5 < gap 10.1 at 2026, so the ghost sits clear above the band). Machine B ranks
  each player against his own year's par as a bar-swap: **Gayle 2011 SR 183.13, +56.7% above par**;
  **Fraser-McGurk 2024 SR 234.04, +35.4%**; raw SR gap **50.9**, so Gayle still edges him.
  **Honest delta / z-drop:** the blueprint z-scores (~+5.5 / +5.2) were not reproducible (recount
  ~+3.5 / +3.3, even flip on some populations), so "how far above his own era" ships as a **percent
  gap (SR+)**, never a z-score.
- **The convergence clock.** Men's run rate **8.99 / 9.56 / 9.63 / 9.88** (2023-26); the 2016-2026
  fit crosses **ten an over ≈ 2028.8** (band **2027–2031**, drawn as a time-axis bracket), already
  9.88 at 2026. WPL run rate **8.08 / 7.86 / 8.37 / 8.54**, slope **+0.19/yr**, reaching the
  men's-2026 level ≈ **2033** against a fixed target (never "closing on" the moving men's line).
  WPL six per over **.196 / .201 / .229 / .219**, slope ≈ 0 — **off the clock** (honest delta: run
  rate closes first, six-hitting barely foreseeable on four seasons). Extrapolations with owned
  bands, never a prophecy; the WPL is never "behind."
- **The 2021 micro-era (footnote).** A strict per-match wide break at 2021 is partly venue-leg
  composition: the India leg scored **8.41** an over (9,499 / 6,777), the UAE leg **7.71** (9,123
  / 7,099).
- **The 16 payoff variants.** `payoff_section` computes, per franchise, its 2023-fault riser (the
  batter whose own SR rose most 2023→2024), its signature player-season re-quoted the honest way to
  2026, and its 2026 run rate against the league's (stated as a position). **10 IPL** "Your adapters"
  cards + **5 WPL** forward-clock cards (never a deficit card, no "behind") + **1 neutral**. Every
  read data-bound; all 16 non-degenerate.

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
- **Chapter 5** (`scenes/ch5.json` + `wpa.u8` + `restate.u8`, lazy-loaded at Ch 5 entry):
  ≤ 2 MB gz → actual **170,191 B gz**. wpa.u8 316,199 B raw / **104,365 B gz** (the
  swing bytes vary ball to ball, so it compresses least of the buffers), restate.u8
  316,199 B raw / **42,462 B gz** (the state cell steps slowly within an innings),
  ch5.json **23,364 B gz** (two 20×10 RE grids + diff, the price board, 20 payoff cards
  with replays, the scrub over, footnotes).
- **Chapter 8** (`scenes/ch8.json`, lazy-loaded at Ch 8 entry): ≤ 2 MB gz → actual **33,864 B
  gz** (115,712 B raw). Engine- and buffer-free — the 1,331 match centroids + `match_bounds`
  block-start indices + the 988-delivery review subset + the precomputed momentum shuffle-null
  histograms (small binned counts, not raw shuffles, so they compress hard) + the 16 payoff
  variants + the 10 footnote strings, all in one scene doc. `pairing.u16` belongs to Ch 9.
- **Chapter 9** (`scenes/ch9.json` + `pairing.u16`, lazy-loaded at Ch 9 entry): ≤ 2 MB gz →
  actual **213,147 B gz**. pairing.u16 632,398 B raw / **95,109 B gz** (the duel id per point,
  0xFFFF dust — long dust runs and repeated ids compress well), ch9.json 612,442 B raw /
  **118,038 B gz** (the 277-node + 1,691-duel tables, the per-duel ball-by-ball replays, the
  heartbeat + envelope, the loyalty spectrum, the WPL comparison, the 16 payoff variants, and
  the footnotes — the replays dominate the raw size and gzip hard, small integer codes).
- **Chapter 10** (`scenes/ch10.json`, lazy-loaded at Ch 10 entry): ≤ 2 MB gz → actual **10,901 B
  gz** (40,820 B raw). **Buffer-free** (like Ch 6 / Ch 7) — the `ribbon` morph is a pure
  `position.x` function so the field holds at 14 attributes and the Teleporter subset rides the
  spare `aRunOut` bit2, so R6a adds NO new per-point buffer. The whole chapter (the seismograph
  ladders + strictness break sets + posteriors + per-metric cracks, the fault-map subway, the
  bridge-player shift-share + three-suspect card, the Teleporter Machine A/B tables, the
  convergence fans, the 2021 micro-era, the 16 payoff variants, and the six `ch10-*` footnotes)
  fits in one small scene doc.
- Full read-through ≤ 25 MB gz → actual ~2.08 MB gz (R2a engines + the parallel track + the
  R2b/R3a/R3b/R5a/R5b/R6a chapter buffers and scene docs).
- The `ledger.py` rows enumerate exactly the shipped filenames (no phantom
  `draw/truth.json` / `ch1/outrate.json` rows — those never shipped; the R1a scene
  data lives in `scenes/coldopen.json` + `scenes/ch1.json`).

## Tests

```sh
python3 -m unittest discover -s pipeline/tests -q     # 336 tests
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

- `test_ch5.py` **(R3b-2, Chapter 5)** — `scenes/ch5.json` + `wpa.u8` + `restate.u8`:
  buffer contracts (both n_points long; restate round-trips against an independent
  per-delivery recount of the 2019 final and packs only possible states; the wpa
  sentinel set equals an independent per-match classification of D/L / undecided /
  short-target matches; fresh re-encode == bytes on disk); the **famous-ball spot
  check** (Malinga to Thakur, the final ball of the 2019 final: the buffer byte
  decodes to −(era-grid readout at needed 2, 1 ball, 4 in hand), the exact number
  the scrub quotes — and MI's payoff ball is Smith's 2012 last-ball four, +0.988);
  **WPA consistency** (per-chase telescoping to the result, sampled corpus-wide from
  the decoded buffer, plus the exact closure gap in the doc); the **scrub over
  matching the raw 2019 final delivery-for-delivery** (batters/bowler/runs/wickets,
  needed 9/8/7/5/4/2, identity-resolved match_index 755, worm == grid readout, final
  ball resolves to 0); the **validations** (defended band 30/41 → 21/54, single flip
  −0.013 → −0.248 + dot deepening, third-wicket 11.81 → 3.48/1.04, Wicket Value
  appreciation above run inflation + the 2024-26 window, finisher 17/31 → 35/41 with
  the fatal band moving 10 → 12, chase-difficulty 25/37 → 37/42, RE-drift grids ==
  engine verbatim, the price board covering all 23 seasons); the **payoff** (20
  cards, no empty states, real corpus-verifiable balls, replays containing their top
  ball, distinct-match runners-up, the WPL designed short-history state); the **WPL
  beat** (mask == engine verbatim; observed dots only on masked cells with evidence,
  values matching the engine's n; finisher cohort 9/11 between the eras); and
  determinism + the 2 MB chapter budget + meta.json registration.

Snapshot constants live at the top of each test file; a new Cricsheet drop that changes
the corpus must update them consciously.
