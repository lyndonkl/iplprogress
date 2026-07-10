# R7b — The Credibility Layer (storyboard for the design gate)

The final piece. Every number on the site learns to wear its own uncertainty. Four
components, wired into the R6b sandbox and the R7a player cards:

1. **Stabilization Points → a trust meter.** Each rate stat carries how many balls it needs
   before it is half signal (batting SR ~94.5, boundary% ~93). A leaderboard row or a card
   number shows whether it has cleared that bar or is still noise.
2. **Metric Half-Life → a freshness dial.** A cross-era comparison (the teleporter's peak
   season vs 2026) spans more seasons than a metric's half-life, so a dial shows how much of
   its meaning survives.
3. **True-Talent + a shrinkage slider.** Drag from raw to regressed and watch small-sample
   flukes fall while high-volume greats hold, with confidence intervals.
4. **The bowler TrueEcon river.** The era-fair economy line deferred from R7a, completing
   bowler cards.

After R7b the epic is fully delivered.

All grounded in verified recounts (below). One standing rule reaffirmed: **the honest recount
wins over the catalog teaser.** The naive half-life fit gives ~2.9 seasons; the catalog's
free-r0 fit gives ~5.3 for SR+ (and ~4.3 for a faster metric). We ship what the proper method
computes, dated, and say so.

---

## 0. The method, in one honest sentence per component (verified)

- **Stabilization**: reliability(n) = n / (n + M), so a stat is half signal at n = M balls.
  M = sigma2_within / tau2_between (variance components, DerSimonian-Laird) computed PER stat,
  PER phase, PER era. This is the same EB algebra as `h2h.eb_constants` (sigma2=2.7973 for
  runs/ball), fit per stat instead of once. Verified: batting SR M ~= 94.5; boundary% ~= 93
  (the "first such number for T20"). The existing k=51.2 (pair) / 50 (cell) are the WRONG
  priors here; fit per stat.
- **Half-Life**: same-player cross-season persistence r(delta) = r0 * 0.5^(delta / H), fit
  log-linearly with a FREE r0 (sampling noise attenuates r(1), so forcing r0=1 is wrong).
  Verified (srplus, pooled over players): autocorr 0.33, 0.26, 0.25, 0.20, 0.20 -> r0 ~= 0.36,
  H ~= 5.27 seasons. Regime-break interaction: gaps straddling a Ch10 seismograph changepoint
  decay faster (an independent validation of the cracks).
- **True-Talent**: regressed(lambda) = mean + (raw - mean) * n / (n + lambda*M); CI = regressed
  +/- 1.96 * sqrt(sigma2 / (n + lambda*M)). The slider is lambda from 0 (raw) to 1 (full
  stabilization prior). PID-keyed (never regress two namesakes onto one row). Verified: Kohli
  career SR+ 100.87 -> 100.86 (barely moves, huge sample); a thin player collapses toward 100.
- **TrueEcon**: phase-par economy - conceded economy over the exact phase mix bowled; TrueEcon+
  = 100 * par / actual (>100 = better than era par). Already computed in `bowlerplane` for Ch3.
  Verified: L Ngidi IPL 2018 economy 6.0 / par 8.92 / TrueEcon 2.92 (a genuine outlier season).

---

## 1. Trust meter (Stabilization) — where and how

**What it says (honesty first):** a number below its stabilization point is NOT wrong, it is
STILL SETTLING. Frame as "how much of this is signal yet," never "true/false." Copy pattern:
"boundary% needs about 93 balls to mean much. This is 240 balls, so read it straight." /
"only 40 balls so far, so treat it as a hint."

**Sandbox leaderboards (LinkedPanel `.rank` rows):** each row gains a small trust cue driven by
that row's balls vs the stat's M. Not a number soup: a 3-state luminance chip (mirroring the
project's CVD rule) is the safest idiom:
- reliable (balls >= M): full-opacity value.
- firming (M/2 <= balls < M): value at reduced opacity + a small "settling" glyph.
- noisy (balls < M/2): value dimmed + a "hint only" glyph.
The exact thresholds and glyph are a design-gate call (Q1). The leaderboard already sorts by
runs/wickets; the trust cue must NOT reorder, only annotate.

**Player card SR+ river + signature:** per-season dots already carry `balls` (data.ts:143). A
season under M reads as a hollow/dim dot (consistent with the river's existing sub-100-ball gap
treatment). The peak's headline gets a one-line trust read ("peak SR+ 112.3 in 2013, off 457
balls, well past the ~95 a strike rate needs"). The card's existing "Based on N balls" note
becomes a REAL reliability read, not just a count.

**Data:** `engines/stabilization.json` (league-wide M per stat, per phase, per era). Tiny.
Trust is then computed client-side (balls vs M). No per-player trust artifact.

**Fallacy guard:** never a single "trust score" 0-100 that hides which stat or sample; always
"N balls vs ~M for this stat." Rare events (wicket%, needs the most balls) must not read as
"more trustworthy" just because the raw count is small.

---

## 2. Freshness dial (Metric Half-Life) — where and how

**What it says:** a cross-era comparison loses meaning with distance; the dial quantifies how
much survives. It reinforces the teleporter's existing "cross-era is a range, not a verdict."

**Player card Teleporter (the only home in R7b):** beside/above the band (Teleporter.svelte:65-85)
or folded into the `.note` caveat (:91-94). The comparison age = targetSeason(2026) - peak season
is already on the type (data.ts:216,230). Dial reads: "This compares a {peak} season to 2026,
{gap} seasons apart. A strike rate's meaning roughly halves every {H} seasons, so this keeps
about {retained}% of it." retained = 0.5^(gap / H).
- Design idiom (Q2): a small arc/gauge filled to `retained`, or a plain inline sentence. On a
  phone the sentence may beat a tiny gauge; the gate decides.
- Honesty: `retained` is approximate (H itself has a CI); phrase as "about", never a false
  precise %. For a very old peak (2008 vs 2026) the dial is near-empty and that is the point.

**Data:** `engines/half_life.json` (per metric r0 + H). The dial needs only the metric's H, read
once. Verified srplus H ~= 5.27 (ship the recount, not the 4.3 teaser, and note which metric each
number belongs to).

**Fallacy guard:** the dial must not imply the honest teleport band is invalidated, only that a
distant comparison is softer. It COMPOSES with the existing honest-band/naive-ghost, it does not
replace it.

---

## 3. Shrinkage slider (True-Talent) — where and how

**What it says:** a raw leaderboard rewards flukes (a hot 30-ball cameo tops the strike-rate
list); regression asks "what is their true skill, given how little we have seen." Drag raw ->
regressed and the flukes fall while the high-volume names hold. The slider IS the "regression
called it" teaching device.

**Sandbox leaderboards (the primary home):** a board-level control above the leaderboards
(LinkedPanel `.v-title` / above `.boards`). At raw (lambda=0) the list is today's runs/wickets
order. As lambda -> 1, rows re-rank by the EB-regressed rate with 80% CIs shown (a whisker or a
+/- on each row). Labels: raw = "what happened in this selection", regressed = "best guess at
true skill". 
- **Critical build constraint (from the scout):** the slider must live OUTSIDE the
  `{#key coordTick}` block so its value survives a mask commit, and must re-rank from
  already-computed per-row aggregates WITHOUT re-firing the demand-mode pass on drag. And
  `LEADER_TOP=8` must widen (emit/keep a larger candidate list) so a regressed leader who sits
  outside the raw top-8 can actually appear; else the slider lies by omission.
- The raw denominators (batter balls, bowler runs-conceded + balls) come from extending
  `computeSelectionStats`' single masked pass with a couple of Map writes (no new pass). Caveat:
  columnar `runs_total` includes byes/legbyes, so a client economy is slightly generous vs the
  pipeline's bowler-charged economy; disclose or use the batting side as the flagship slider and
  keep bowling economy honest via the emitted `trueecon.json`.

**Player card (lighter touch):** the card is a single player, so a full slider is overkill. The
SR+ river can show a faint regressed companion, or the signature can note the regressed career
number with its CI ("career SR+ 100.9, and the model is 80% sure the true figure sits between
X and Y"). The gate decides whether the card gets any slider at all (Q3); recommendation: no
slider on the card, just the CI on the career number, and reserve the interactive slider for the
sandbox where comparison across players is the point.

**Data:** `engines/truetalent.json` (per-stat: pop_mean, M, sigma2, z, and the pid-keyed
[n, raw, regressed, ci_lo, ci_hi] rows) so the client computes any lambda. PID-keyed.

**Fallacy guard:** regressed is a BEST ESTIMATE with a CI, never "the truth"; the CI must be
visible so the slider does not trade one false precision (raw fluke) for another (a point
estimate). The raw end must stay reachable and labeled honestly ("what happened", which is real,
just small). Never hide that WPL's tiny samples sit mostly below M (regression pulls them hard,
and that IS the honest lesson, not a knock on WPL).

---

## 4. Bowler TrueEcon river (the R7a completion) — where and how

**What it says:** the batting SR+ river's bowling twin. A line over a 0 baseline = par economy
minus actual economy per season (runs saved per over vs an average bowler that era). Above 0 =
better than par; the peak = "biggest edge over his era". Fills the R7a bowler-card gap (whose
copy already promises "the era-fair version, runs saved versus an average bowler, comes next").

**Player card:** build `TrueEconRiver.svelte` mirroring `SrPlusRiver.svelte` (same broken-line,
gap, peak, figcaption pattern). Render it in the bowler-first hero (PlayerCard.svelte:140-158,
replacing the placeholder caveat at :143-146) and the collapsible bowling panel (:222-247,
replacing :234). New model fields `trueEconRiver` + header `peakTrueEcon`, assembled in
`loadPlayerCard` from `engines/trueecon.json` (loaded like `srplus`, suppressible so a load
failure can never regress an existing card).

**Data:** `engines/trueecon.json` (per bowler-season, PID-keyed: par_economy, economy,
true_economy, trueecon_plus, legal_balls, wickets). Piggybacks the existing bowlerplane pass
(no new corpus pass).

**Honesty:** priced against era par (like SR+); WPL bowlers vs the WPL baseline; a season under
the min-balls floor breaks the line (never interpolated); the trust meter from #1 applies to the
economy stat here too.

---

## 5. Data + pipeline (build contract)

- NEW `pipeline/credibility.py`: ONE pid-resolved corpus pass (mirror `registry.build`) tallying
  per-(pid, league, season) trials+successes per rate stat with phase splits; emits
  `engines/stabilization.json` + `engines/half_life.json` + `engines/truetalent.json`. Reads
  `players.json` for canonical names.
- EXTEND `pipeline/bowlerplane.py main()` to also emit `engines/trueecon.json` from aggregates it
  already builds (zero extra pass), pid-resolved.
- Build order: par -> bowlerplane(+trueecon) -> registry -> player_tables -> credibility ->
  ledger -> tests.
- Ledger: the four files are under `engines/`, auto-counted by `ENGINES_PREFIXES`; add a named
  R7b release-gate block. Budget is a non-issue (all tiny).
- `test_r7b.py` (mirror test_r7a conventions): pin stabilization M (SR ~94.5, boundary% ~93),
  half-life (srplus r0 ~0.36 / H ~5.27, dated), a true-talent spot (Kohli SR+ 100.87 -> 100.86),
  and a FREE cross-artifact reconciliation (L Ngidi IPL-2018 trueecon 6.0/8.92/2.92 vs
  scenes/ch3.json gravity_defiers), plus a mutation guard.
- Byte-deterministic (sorted keys). Emitting only `engines/*.json` has zero meta.json exposure.

---

## 6. Voice (binding): zero em dashes; orient-then-reveal; one idea + one number; plain glosses
("stabilizes" = "settles into a real number"; "regressed / true-talent" = "best guess at real
skill once we account for how little we have seen"; "half-life" = "how fast a comparison goes
stale"; "TrueEcon" = "runs saved vs an average bowler that era"); "you/they" with warmth on the
point only.

---

## 7. Open questions for the design gate

- **Q1 (trust meter idiom):** 3-state luminance chip vs a fill bar (balls/M) vs a plain caption?
  On a dense leaderboard row (LinkedPanel `.rank` is a 3-col grid), which reads at a glance
  without adding number-soup? What is the exact firming/reliable threshold framing?
- **Q2 (freshness dial idiom):** a small arc gauge vs a plain inline sentence on the teleporter?
  Phone legibility.
- **Q3 (slider on the card?):** sandbox-only slider (recommended) + a static CI on the card
  career number, or a slider on the card too?
- **Q4 (LEADER_TOP widening):** widen the emitted/kept candidate list to e.g. top-25 so the
  regressed leader can surface, or scope the slider to re-rank only the shown 8 (and disclose)?
- **Q5 (bowling economy honesty in the sandbox slider):** the client economy is byes/legbyes-
  generous; make the sandbox slider batting-only (flagship) and keep bowling TrueEcon to the
  emitted card artifact, or emit a per-selection bowler-charged correction?
- **Q6 (half-life number to show):** show the per-metric H honestly (SR ~5.3, a faster metric
  ~4.3) with the metric named, not a single global "half-life".

## 8. Cognitive-design review asks

- The credibility layer adds meta-information to already-dense surfaces (a leaderboard, a card).
  Guard against cognitive overload: what is the MINIMUM cue that conveys "trust this / do not"
  without turning every row into a dashboard?
- The shrinkage slider animates a re-ranking; make the motion legible (rows rising/falling) and
  reduced-motion-safe, and make the raw<->regressed labels unmistakable so a viewer never thinks
  the regressed order is "what happened".
- The freshness dial and the teleporter's honest band both speak to cross-era uncertainty;
  ensure they compose into one clear message, not two competing gauges.
- CVD-safe throughout (luminance, not hue); zero em dashes.

---

## 9. DESIGN-GATE RESOLUTIONS (binding on the build)

The cognitive-design + fallacies-guard review is folded in here. This is the build contract;
where it conflicts with the sketch above, this wins.

### 9.0 The central move: reliable = the SILENT default (exception-only rendering)
Trust is an EXCEPTION, not a universal readout. A reliable row/number carries NO mark. Only
firming and noisy rows get a cue. A high-sample leaderboard then shows almost no marks, and the
eye is drawn to the one fluke that needs a caveat. This is the load-reduction key: four passive
cues + one control, and on a clean board the reader sees essentially none of it until it matters.
Nothing behind a hidden toggle (honesty is not opt-in); the slider is the only interaction.

### 9.1 Trust meter (MUST) — a 2-mark luminance glyph, exception-only
NOT a fill bar (reads as a continuous "% true" = false precision + chartjunk), NOT a per-row
caption (soup). An 8px trust dot prefixed to the value cell (`.rk-val`):
- reliable (balls >= M): NO glyph, value full `--ink`.
- firming (M/2 <= balls < M): FILLED dot, ink opacity ~0.72, value ~0.72.
- noisy (balls < M/2): HOLLOW dot (1px ink stroke, no fill), ink ~0.6, value floored at 0.6
  (NEVER dim to illegibility, an unreadable number reads as "wrong" not "noisy").
Filled-vs-hollow = the CVD-safe SHAPE channel (fullness maps to sample size); opacity reinforces
on the luminance ramp. **Driven by n (balls/trials) vs that stat's per-stat M, NEVER the
numerator** (so a big raw wicket tally on few balls still flags noisy; rare events like wicket%
have the highest M). Copy: one board legend under the board title ("A hollow dot means still
settling. Too few balls to trust yet."); per-row tooltip at footnote depth ("40 balls faced. A
strike rate needs about 95 to settle.") naming the metric + n vs M. States are "settled / still
settling / a hint", NEVER "reliable/unreliable" or "true/false". ANNOTATE, never reorder (glyph
in the value cell; the sort comparator never sees trust state). Same treatment on the card SR+
river dots (per-season `balls` vs M) and the peak note.

### 9.2 Freshness dial (MUST) — a SENTENCE, never an arc gauge
A plain sentence folded into the teleporter existing `.note`. NO arc/gauge, NO `retained%`
number (false precision; a third gauge competing with the band). Freshness stays OFF the band
(the band is the single visual answer; it composes, it does not invalidate). Copy (one
load-bearing number, named to the metric): "This peak is {gap} seasons before 2026. A strike
rate's edge fades by about half every {H} seasons, so read this as a soft echo, not a
like-for-like." Round to "about 5 seasons" on the card; keep the dated 5.27 in a methods/how-we-
computed panel. Say "still the best cross-era read we can make, just a softer one with age",
never that age invalidates the band.

### 9.3 Shrinkage slider (MUST) — 3 detents, keyed FLIP, widen the pool, CIs visible
- **3 DETENTS**, not a continuous lambda: "As it happened" (0) / "Halfway" (~0.5) / "Best guess"
  (1.0), a snapping segmented control. Compute any lambda under the hood; the UI snaps (a
  continuous drag thrashes the rows).
- **Object constancy:** key rows by pid/name + `animate:flip` so a fluke SLIDES down (never a
  cross-fade into a different list). Reduced-motion: snap instantly + reuse the 220ms `settle` +
  `aria-live="polite"` ("Reordered by best-guess skill. New leader: X."). Debounce the recompute.
- **Live state header** above the board: "Ranked by: what actually happened" <-> "Ranked by:
  best guess at true skill" (a viewer mid-drag must always know which end is active).
- **Labels jargon-free:** "As it happened" (gloss: small samples included, a 30-ball cameo can
  top it) / "Best guess at true skill" (gloss: our best guess once we account for how little we
  have seen). NEVER the words "regressed" / "corrected" / "the truth".
- **80% CI (MUST, always visible):** in a regressed state the `.rk-bar` track switches from a
  runs magnitude bar to a floating WHISKER (ci_lo..ci_hi) + a bright point at the estimate (point
  ink 1.0, whisker ~0.45, luminance-coded). RELABEL the channel with the state header (bars:
  runs -> bars: strike rate, with the range we are 80% sure of) so the quantity switch is
  unmistakable. Numbers only at tooltip depth ("Best guess 128. 80% sure it is between 119 and
  137."). Never a bare regressed point.
- **LEADER_TOP (MUST): WIDEN to a qualified pool** (~top-25 by raw, or a min-balls floor);
  compute regressed for all, display top-8 by the ACTIVE ordering. Promoted rows ENTER (brief
  luminance flash from the bottom); demoted flukes EXIT by translating out (that exit IS the
  lesson). NEVER scope the re-rank to the shown 8 (a lie by omission).
- **WPL (MUST):** WPL rows regress toward the WPL `pop_mean` (per-league prior), NEVER a
  cross-league mean; frame the pull as "smaller sample, so the model leans on the average more",
  NEVER "WPL is worse/behind".
- **Sandbox slider is BATTING-ONLY for R7b (MUST):** the client economy is byes/legbyes-generous
  (a systematic bias); do not ship a biased number inside the tool built to teach honesty.
  Bowler TrueEcon stays on the emitted, bowler-charged card artifact.
- **NO slider on the CARD:** a single player has nothing to re-rank. Put a static 80% CI on the
  career number instead ("career SR+ 100.9, and the model is 80% sure the true figure sits
  between X and Y"). The interactive slider is sandbox-only.

### 9.4 Bowler TrueEcon river (MUST) — plot the 100-baseline trueecon_plus
Plot `trueecon_plus` (100 = par, ABOVE = better), NOT a 0-baseline runs-saved line, so it mirrors
the SR+ river with zero relearning (economy is "lower is better", so a raw-economy line would dip
for good bowling and fight the SR+ river the card just taught). "100 is a par bowler that season.
Above the line means he leaked fewer runs than his era's peers." Peak = max `trueecon_plus`
season, framed "biggest edge over his era", with the runs-saved as the caption GLOSS not the axis
("saving about 2.9 runs an over versus par"). min-balls floor breaks the line (never
interpolated); the trust dot (9.1) applies to the economy stat with its own M.

### 9.5 Banned + honesty (MUST)
No single 0-100 trust/credibility SCORE and no card-level "confidence" badge (every cue names its
stat + n vs M). Half-life beside an SR+ number is the dated SR+ recount (~5.3), named to the
metric, never the 4.3 teaser, never a global half-life. Every threshold names its stat ("a strike
rate needs about 95 balls", "boundary-hitting needs about 93"). Zero em dashes; split any
multi-number line to one-idea-one-number (e.g. peak `.point` = "biggest edge in 2013: SR+ 112.3";
a separate `.note` = "That is off 457 balls, well past the roughly 95 a strike rate needs to
settle").

### 9.6 Confirmed Q-answers: Q1 2-mark glyph exception-only · Q2 sentence not gauge · Q3 no card
slider (static CI) · Q4 widen the pool never scope-to-8 · Q5 sandbox slider batting-only · Q6
per-metric named half-life (SR+ ~5, dated 5.27 in methods).
