# IPL/WPL Era-Evolution Metrics Catalog

**The definitive research catalog for the interactive explorer.** 143 verified metric ideas covering IPL 2008-2026 (1,243 matches) and WPL 2023-2026 (88 matches), all Cricsheet ball-by-ball. Every idea below survived a verification pass against the actual data; killed ideas have already been removed.

## How to read this

- **Sections** consolidate the raw idea categories into 12 thematic groups; each idea keeps its raw `category` tag in parentheses after its name where it differs from the section theme.
- **★ = HERO CANDIDATE** (15 total): the best combination of (novel or underused) + feasible + strong era story + strong viz hook, spread across sections. Heroes lead each section.
- **Ordering within sections:** heroes first, then novel + feasible, then known-but-underused, with needs-external-data near the end and table-stakes last.
- **Feasibility:** `direct` = computable straight off the delivery stream; `derivable` = needs a model/inference layer built from the same data; `needs-external-data` = requires a named public join (all such ideas are also collected in the final section).
- **Verdicts:** every idea was probed against the corpus. `confirmed` = recipe and story hold as pitched (99 ideas); `adjusted` = feasible but the recipe or headline needed correction (44 ideas) — corrections are folded into the entries below, so **trust these entries over any earlier pitch documents**.
- **Teasers** are real numbers computed from the corpus during verification, not estimates. Era buckets are typically IPL 2008-10 vs 2023-26 unless stated.
- **Shared infrastructure:** many ideas reuse five engine layers — (1) season/phase/venue par baselines (SR+ family), (2) RE288 run-expectancy surfaces, (3) the win-probability model (WPA/LI family), (4) venue + franchise + season-label canonicalization tables, (5) derived batting position / entry states. Build order matters: engines are flagged inline.
- **Recurring bookkeeping (applies everywhere):** normalize season strings (`2007/08`→2008, `2009/10`→2010, `2020/21`→2020, WPL `2022/23`→2023 — or derive season from `dates[0]`); exclude super-over innings (36 innings across 17 tie matches); flag D/L via `outcome.method` (23 matches); count legal balls by absence of wides/no-balls keys; canonicalize ~60 venue strings and franchise renames (Daredevils→Capitals, Kings XI→Punjab Kings, Bangalore→Bengaluru, Rising Pune variants).

## Summary counts

| Section | Ideas | ★ | Novel | Underused | Table-stakes | Needs-external |
|---|---|---|---|---|---|---|
| 1. Batting Evolution | 23 | 3 | 11 | 11 | 1 | 0 |
| 2. Bowling Evolution | 13 | 1 | 6 | 7 | 0 | 1 |
| 3. Scoring Environments & Venues | 18 | 2 | 6 | 9 | 3 | 0 |
| 4. Impact & Player Value | 16 | 2 | 7 | 8 | 1 | 1 |
| 5. Tactics, Rules & Team Strategy | 19 | 1 | 11 | 8 | 0 | 1 |
| 6. Match Dynamics & Structural Analytics | 12 | 2 | 6 | 6 | 0 | 0 |
| 7. Luck, Skill & Measurement Methodology | 5 | 0 | 3 | 2 | 0 | 0 |
| 8. Cross-League: IPL × WPL | 10 | 2 | 6 | 4 | 0 | 1 |
| 9. Fielding & Officiating | 5 | 0 | 4 | 1 | 0 | 0 |
| 10. Schedule, Calendar & Fatigue | 7 | 0 | 4 | 3 | 0 | 1 |
| 11. Careers, Cohorts & Roster Churn | 10 | 1 | 9 | 1 | 0 | 0 |
| 12. The Era Machine: Detection & Translation | 5 | 1 | 4 | 1 | 0 | 0 |
| **Total** | **143** | **15** | **77** | **61** | **5** | **5** |

Feasibility overall: **88 direct · 50 derivable · 5 needs-external-data.** Verification verdicts: **99 confirmed · 44 adjusted.**

---

## 1. Batting Evolution

### ★ SR+ / True Strike Rate (era-, phase-, venue- and pressure-adjusted batting index)
An OPS+-style index: a batter's scoring rate versus the expected rate for the exact balls they faced (season × over-phase × venue × innings), where 100 = league average of their own time.
- **Recipe:** Fit E[runs/ball | season, over, venue, innings#, wickets down] from all ~1.5M deliveries (cell means with shrinkage, or GBM). SR+ = 100 × Σ(actual runs.batter) / Σ(E[r]). Same machinery yields Average+ from dismissal probability. **This is engine layer #1** — the par model reused by a dozen ideas below.
- **Feasibility:** derivable — all conditioning fields verified present (powerplays[] everywhere, target in ~99% of chases). Venue canonicalization is mandatory: 60 raw strings for ~45 grounds (Chinnaswamy under 3 spellings).
- **Novelty:** known-but-underused · confirmed
- **Era story:** The project's currency converter: lets 2008 Sehwag argue with 2024 Head on equal footing; surfaces "time travelers" (SR+ 130 in a 120-SR world) vs stat-padders riding 2024 inflation. Also the honest bridge for IPL-vs-WPL, each priced against its own baseline.
- **Viz:** A "time machine" matchup tool: pick any two player-seasons across eras/leagues; raw stats get re-priced through an exchange-rate animation into SR+ before the face-off verdict renders.
- **Teaser:** League scoring rose 7.63 → 9.14 RPO (2008-10 vs 2023-26): a batter striking at 150 was +21% above his league in 2008 and dead average in 2024.
- **Lenses:** batting-evolution, impact-value, sabermetric-translation, landscape-scan

### ★ Anchor Extinction Index
The disappearing anchor: what share of a season's balls are consumed by long, slow, low-boundary innings, tracked like an endangered-species population count.
- **Recipe:** Anchor innings = balls faced ≥ 15, SR < 0.85 × season-phase par SR, boundary balls < 12% of balls faced (boundary ball = runs.batter ≥ 4). Per season: % of team balls consumed by anchors, players with ≥5 anchor innings, and the "anchor penalty" (win rate with/without a top-4 anchor innings). Run threshold sensitivity sweeps.
- **Feasibility:** derivable — one pass over deliveries plus the shared par model; pipeline verified end-to-end.
- **Novelty:** novel · confirmed
- **Era story:** 2008-2015 was full of 120-SR accumulators; by 2024-26 the archetype is nearly extinct. Verified kicker: WPL anchor-ball share (~9-10%) is already at modern-IPL levels — the women's league was *born post-anchor*, undercutting the lazy "women's cricket still rewards anchors" narrative.
- **Viz:** Wildlife-documentary framing: a species-decline conservation chart, with "last surviving anchors" profiled as they blink out; hovering a season draws the actual anchor innings as slow worm lines against the frenetic par worm.
- **Teaser:** Anchor innings consumed 14.8% of all balls in IPL 2008-10 but 8.5% in 2023-26 — a 43% population decline; WPL is already at ~9%.
- **Lenses:** batting-evolution

### ★ Run-Out Extinction Curve
Charts the collapse of the run-out — from 12% of all dismissals in 2008 to under 5% in 2026 — as the most direct evidence of the death of the risky single.
- **Recipe:** run_out share = wickets.kind=='run out' / all wickets, per season. Decompose: striker vs non-striker out (player_out vs batter/non_striker), runs completed on the ball (failed single vs turning-for-two), phase, direct-hit proxy (fielders array length 1 vs 2+). Pair with singles-per-ball to separate fewer attempts from better running. Handle sparse/missing fielders arrays gracefully (gaps cluster in 2018-21).
- **Feasibility:** direct — verified as the strongest ready-to-ship idea in the batch; 1,194 IPL run-outs.
- **Novelty:** novel · confirmed
- **Era story:** Boundary-or-block replaced strike rotation, so batters simply stopped taking the runs that produce run-outs. WPL at 7.0% sits where the IPL was circa 2014-17 — its batting revolution still in progress.
- **Viz:** Animated top-down pitch with two runners; the "danger zone" between creases visibly shrinks per season; scrubber cross-fades to the extinction curve with each season's most famous run-out as a hover story.
- **Teaser:** Run-outs: 12.3% of all IPL dismissals in 2008 → 4.6% in 2026; WPL 7.0% — right where the IPL was a decade ago.
- **Lenses:** hidden-fields

### New-Batter Tax (post-wicket scoring dip and its era persistence)
The hidden cost of a wicket: how far team scoring dips in the 10 balls after a dismissal — and the verified surprise that the dip never went away.
- **Recipe:** For each dismissal, compare team runs/ball over the next 10 legal deliveries vs the phase-season par for those exact overs (shared par model, with wickets-in-hand conditioning); trim wickets near innings end. Companion: incoming batter's first-5-ball SR by season. Cut by wickets-down, phase, pre/post-2023 (Impact Player via replacements field, 128-142 events/season from 2023 vs 1-6 strays before).
- **Feasibility:** derivable · **adjusted** — the probe *contradicts* the original "tax halved" hypothesis: the 10-ball tax was 1.22 runs/over below par in 2008-10 and 1.40 in 2023-26 (~15% of par in both eras).
- **Novelty:** novel
- **Era story (corrected):** Incoming batters' intent exploded (first-5-ball SR 101 → 127) yet the team-level tax stubbornly persists — the tax is structural (new batter + field reset), not behavioral. Arguably a better story than the one pitched. WPL comparison still open.
- **Viz:** Seismograph strip per era: each wicket a tremor, the run-rate trace showing recovery; interactive — drop a wicket anywhere in an innings and watch each era's modeled recovery.
- **Teaser:** Post-wicket 10-ball tax barely moved (1.22 → 1.40 runs/over below par) even as the incoming batter's first-5-ball SR jumped 101 → 127.
- **Lenses:** batting-evolution, scoring-environment

### Aerial Risk Ledger (intent vs execution via caught% and six ratios)
Splits the six-hitting boom into intent inflation vs skill inflation using sixes-per-caught-dismissal as an execution proxy for big-shot attempts.
- **Recipe:** Attempt proxy = sixes + caught dismissals (exclude 'caught and bowled' — verified tiny: 36-87/era). Attempt rate per ball and execution rate = sixes/(sixes+caught) per season, phase, player. Secondary: fours-to-sixes conversion.
- **Feasibility:** derivable — proxy computes cleanly; honest caveat: caught includes keeper/slip edges (no fielding-position data), fixed noise that leaves era comparisons valid if edge rates are stable. True shot-level intent would need non-public ball-tracking.
- **Novelty:** novel · confirmed
- **Era story:** Braver AND better — verified that attempt rate and execution rate both rose, i.e. genuine skill evolution (range hitting, bat speed), not recklessness forgiven by flat decks. WPL execution (54.5%) sits at intent-era IPL levels.
- **Viz:** Risk-reward frontier scatter: x = attempt rate, y = execution rate, one dot per team-season, animated 2008→2026 as the cloud migrates up-and-right; sluggers (Gayle, Russell, Head, Shafali) leave comet trails.
- **Teaser:** Aerial attempts per 100 balls rose 7.3 → 11.4 while execution rose 58.7% → 67.3% (IPL 2008-10 vs 2023-26).
- **Lenses:** batting-evolution, wpl-comparative

### Gear-Shift Detector (innings shape taxonomy)
Changepoint detection on every substantial innings' scoring trajectory to count and time a batter's "gear changes", then classify innings into shape archetypes per season.
- **Recipe:** For innings ≥ 25 balls, run changepoint detection (PELT/binary segmentation on Poisson rate) over the per-ball runs sequence (exclude wides from balls faced). Extract segment count, segment SRs, shift timing; cluster into archetypes: flat-max, ramp, two-act, stall. Report archetype shares per season/role.
- **Feasibility:** derivable — ~1,500 qualifying innings per era; full PELT runs in seconds-to-minutes. Verified non-issue: 25+ ball innings share is stable across eras (20.9% vs 20.3%), so no sample-framing distortion.
- **Novelty:** novel · confirmed
- **Era story:** The classical T20 innings was three acts (see off, consolidate, launch). By 2024-26 the modal long innings is one-gear flat-max — the gearbox deleted. WPL innings may still show two-act structure, dating it on the IPL timeline.
- **Viz:** Innings as subway-line paths with color-coded gear segments; a "transmission" dial shows the era's modal gear count dropping 3 → 1; click famous innings (Gayle 175, Head's final) to see their detected gears.
- **Teaser:** Two-act innings (2nd-half SR ≥ 1.5× 1st-half, among 25+ ball innings) fell 33.5% → 24.5% (2008-10 vs 2023-26).
- **Lenses:** batting-evolution

### License Index (depth-conditional aggression)
Measures the "license to swing": how much extra risk batters take when more batting remains behind them — isolating the Impact Player rule's psychological subsidy.
- **Recipe:** Per delivery, resources-behind = XI members (players{}) not yet dismissed/batting, plus Impact-Player availability flag (2023+, via replacements). Model aggression (boundary + caught-out rate; raw SR) over (wickets down × overs left) cells; compare identical states 2022 vs 2023-26, and within 2023+ matches with vs without a batting sub deployed.
- **Feasibility:** derivable — replacements verified (584 tagged deliveries 2023-24 for the deployed-vs-not split); matched-cell comparison already yields clean signal (4,380/5,310 balls per era in the probed cell); fine cells need smoothing.
- **Novelty:** novel · confirmed
- **Era story:** The sharpest structural-rule story in the dataset: did Impact Player cause the 2023-26 explosion by making the 7th wicket painless? WPL (no rule) doubles as control.
- **Viz:** Split-screen "parallel universe" aggression surfaces over (wickets down × overs remaining), 2022 left, 2024 right, diff surface glowing where the license was granted; a toggle shows the no-Impact-Player counterfactual.
- **Teaser:** At identical states (≥4 down, overs 7-16): SR jumped 117.7 (2021-22) → 127.5 (2023-24) while dismissal rate FELL 4.98% → 4.76% — extra aggression at zero risk premium.
- **Lenses:** batting-evolution

### Six-Hitting Democratization (concentration Gini)
Whether the six boom belongs to everyone or a few freaks: concentration of season six-hitting across batters as a Gini/Lorenz story.
- **Recipe:** Per season: sixes per batter (runs.batter==6), Gini/HHI over batters with ≥30 balls faced (85-101 qualifiers/season — stable); companions: players with ≥10 sixes, top-10 hitters' share of league sixes, sixes by batting-position bucket (positions from appearance order, shared with Entry-Point Fingerprint).
- **Feasibility:** direct — verified end-to-end on all 19 seasons; every companion lands in the hypothesized direction.
- **Novelty:** novel · confirmed
- **Era story:** 2008-2013 sixes were a specialist weapon; by 2024-26 the Gini has fallen (0.49-0.54 → 0.40-0.46) — No. 8s clear the rope, every squad carries five 20-six players. WPL overlay tests whether women's six-hitting is still in its specialist era.
- **Viz:** Animated Lorenz curve bending toward equality year by year, paired with a "firework wall": each batter a launcher whose height is their six count — 2008 shows three towering rockets, 2026 a whole skyline firing.
- **Teaser:** Players with ≥10 sixes: 18 (2008) → 58 (2026); the top-10 hitters' share of all league sixes fell 35.9% → 28.1%.
- **Lenses:** batting-evolution

### League-Age Curves (the T20 experience arc)
Aging-curve methodology using seasons-since-IPL-debut (derivable from the registry, no birthdates needed): rise, peak, fade in league-experience terms via the survivorship-safe delta method.
- **Recipe:** League-age = season − first registry season. Delta method: for players with ≥N balls in consecutive seasons, average Δ(wRC+/FIB) per age step, chained into a curve, harmonic-mean weighted. Separate batter/bowler curves and era cohorts. **Mandatory correction:** 2008 (and WPL 2023) cohorts are left-censored — everyone "debuts" in season 1 — exclude or flag them.
- **Feasibility:** direct (adjusted for the censoring fix) — registry person-IDs verified stable 2008-2025. True biological aging needs external birthdates (ESPNcricinfo via Cricsheet people register) — flagged, optional upgrade.
- **Novelty:** novel
- **Era story:** Has the development arc compressed? 2008-era players needed seasons to acclimatize; the 2023+ cohort arrives pre-trained by academies. Twilight question: does modern T20 discard players faster after decline onset? WPL gives a live view of a league's first-ever experience curves forming.
- **Viz:** Ghost-grey spaghetti of individual trajectories with the cohort delta-method curve bold on top; cohort selector animates the curve steepening; player pages get a "you are here" marker.
- **Teaser:** Debut-season (league-age-0) batters faced 18.4% of all balls in 2009-10 but only 9.5% in 2023-26 — the league became twice as hard to break into.
- **Lenses:** sabermetric-translation

### Break-Even Running (the stolen-base calculus for twos and singles)
Baseball's break-even stolen-base rate applied to running between wickets — runs added by aggressive running vs run-out risk, priced by the run-expectancy matrix.
- **Recipe:** Running value = linear-weight value of 1s/2s/3s on balls in play − run-out cost (run outs × wicket linear weight). Break-even threshold from RE288: minimum success rate justifying the extra run, by phase and wickets in hand. Team aggression index: 2s per non-boundary ball; run-out rate as caught-stealing analogue. Attribute running value at *team* level (who called the run is unknowable).
- **Feasibility:** direct · **adjusted** — the WPL hypothesis was empirically backwards: WPL's twos rate is LOWER than IPL's (4.95 vs 7.62 per 100 non-boundary balls); frame the WPL angle as "why does WPL run less?" (it scores via fours instead).
- **Novelty:** novel
- **Era story:** As sixes doubled, running didn't atrophy — it got dramatically *safer* at constant aggression. The break-even rate itself shifts as wickets cheapen post-2023; test whether teams noticed.
- **Viz:** Risk-reward frontier: team-seasons plotted by twos-per-non-boundary-ball vs run-out rate with the era-specific break-even curve drawn; 19 seasons of drift animated; real-time run-out "cost meter" on match pages.
- **Teaser:** Run outs per 1,000 legal balls halved 6.4 → 2.8 while the twos rate held flat (7.8 → 7.6 per 100 non-boundary balls).
- **Lenses:** sabermetric-translation

### The Vanishing Deflection (legbye decline)
Tracks legbyes — runs off the batter's body — as a proxy for how often the ball beats the bat, halving across the eras.
- **Recipe:** Legbye runs/events per 100 legal balls per season (extras.legbyes); split by phase. Companions: byes (keeper misses) and lbw rate — if legbyes fall while lbw share holds, batters are making *contact* more, not just getting hit less. Cross-check WPL. Pace-vs-spin slice needs external style data (don't lean on keeper-inference for it).
- **Feasibility:** direct — verified: 2.24 → 1.15 legbye events per 100 legal balls (2008 → 2026). Present as a downward drift, not a monotone (2014 bounced to 6.18/match).
- **Novelty:** novel · confirmed
- **Era story:** A quiet, near-monotonic signal that modern batters make contact with far more deliveries than 2008 batters did — a skill-improvement story told entirely from an extras column nobody reads. Interpretation is honestly multi-causal (bats, 360° technique, umpiring norms) — present candidate explanations.
- **Viz:** Batter-silhouette "body map" where per-season legbye density fades from bruised-red (2008) to clean (2026); scrub the timeline and watch the bruises heal, with the companion lbw line confirming contact, not line.
- **Teaser:** Balls that hit the body and ran away for legbyes halved: 2.24 per 100 legal balls (2008) → 1.15 (2026); WPL already at modern-IPL contact levels (3.19/match).
- **Lenses:** hidden-fields

### Matchup Targeting Score
Detects deliberate bowler-hunting: how much a batter's within-match SR varies across bowlers faced, beyond what random ball assignment would produce.
- **Recipe (corrected):** Within-match per-bowler SR (raise minimum to ≥6 balls), compare observed variance to a permutation null (shuffle bowler labels, ~500-1000 reps) — but score via the **permutation percentile/exceedance rate, not raw variance difference** (raw is outlier-dominated with sign flips). Aggregate at season level. Companion: boundary "attack asymmetry" toward the most-attacked bowler.
- **Feasibility:** derivable · **adjusted** — cheap (full-era permutation test ~7s). With the corrected statistic the signal is near-NULL in both eras.
- **Novelty:** novel
- **Era story:** Sell it as the mythology-puncturing branch: within-match bowler-hunting is nearly indistinguishable from random ball assignment in BOTH eras — franchise analytics did not visibly change ball-level targeting. The spin-vs-pace split (needs external style data) is the rescue path if a positive story is wanted.
- **Viz:** Predator-prey web per match: bowlers as nodes sized by overs, edges colored by batter aggression, "hunted" bowlers glowing red; a season dial of league targeting intensity — which stays flat, and that's the point.
- **Teaser:** Batter-innings beating the 90th-percentile permutation null: 11.1% (2008-10) vs 10.3% (2023-26), against a 10% chance baseline.
- **Lenses:** batting-evolution

### Ignition Curve & Early Intent (SR by balls faced)
How fast batters get up to speed: strike rate as a function of balls-faced-so-far, and the balls needed to cross SR 100/130/150. (Companion of the ★ Death of the Sighter hazard analysis in Section 6.)
- **Recipe:** Index each legal delivery by the batter's cumulative balls faced (exclude wides, count no-balls); aggregate season SR(n) curves; scalars: SR on balls 1-10, "ignition point" where cumulative SR crosses 100/130. Slice by batting position (appearance order) and league.
- **Feasibility:** direct — trivial and stable across the schema; verified over all 1,331 matches.
- **Novelty:** known-but-underused · confirmed
- **Era story:** The death of the sighter: in 2008 batters played themselves in for 10-15 balls; by 2024-26 ball one is attacked at near-full intent. The early ramp grew faster than overall SR (+25% vs +21%) — the early innings is where the revolution actually happened.
- **Viz:** Animated "drag racer": each season a car whose speedometer (running SR) climbs as balls tick by; scrub 2008→2026 and watch the curve morph from slow ramp to a flat line pinned at 140+; small multiples per batting position.
- **Teaser:** First-10-ball SR: 108.0 (IPL 2008-10) vs 135.3 (2023-26); WPL 110.5 — almost exactly 2008-era IPL.
- **Lenses:** batting-evolution, landscape-scan

### Entry-Point Fingerprint & Role Cartography
Maps when a batter arrives (over × wickets down × required-rate context) against how they perform from that entry state — data-driven role archetypes. (**Engine layer #5:** entry-state extraction shared by many ideas.)
- **Recipe:** Entry event = first delivery as batter or non_striker; record legal-ball index, wickets fallen, innings, RRR at entry (target present in ~99% of chases). Build per-batter entry distributions (2D histogram) and performance surfaces conditional on entry cell; k-means season role archetypes (opener, one-drop, finisher, floater).
- **Feasibility:** derivable — entry reconstruction verified across eras.
- **Novelty:** known-but-underused · confirmed
- **Era story:** Entry-point analysis is CricViz's secret weapon, almost never shown across eras: the rise of the floater (position-4 entries got later AND more dispersed — median ball 35→41, IQR widening), finishers entering earlier as teams bat deeper, and whether Impact Player compressed entry points. WPL: has role specialization emerged yet?
- **Viz:** Interactive "entry map": innings timeline × wickets down, each batter's career entries as a heat blob morphing season by season; click a cell to see everyone who entered there; role clusters migrate across the map over eras.
- **Teaser:** Position-4 entry: median ball 35 (IQR 22-55) in 2008-10 vs 41 (IQR 22-60) in 2023-26.
- **Lenses:** batting-evolution, landscape-scan

### SR Inflation Decomposition: Boundary Engine vs Rotation Engine
Kaya-style decomposition of every season's strike-rate gain into three levers: more boundary balls, bigger boundaries (6s replacing 4s), better rotation on non-boundary balls.
- **Recipe:** SR = boundary_ball% × avg_boundary_value + (1−boundary_ball%) × non_boundary_runs_per_ball; standard index decomposition of ΔSR year over year (identity verified to reproduce SR exactly). Pin era windows and legal-ball denominators in the spec. Per-player version tags boundary-dependent vs rotation-dependent scorers.
- **Feasibility:** direct · confirmed
- **Era story:** Answers HOW scoring exploded: the boundary engine dominates. Verified second story: WPL runs a structurally different engine — four-led (15.8% fours, 3.6% sixes, boundary value 4.37 vs IPL 4.73) with WEAKER rotation (0.567 vs 0.645 non-boundary runs/ball) — not a delayed copy.
- **Viz:** Three-cylinder engine diagram where each cylinder's firing rate is a lever's contribution; per-season waterfall bars; an IPL/WPL toggle showing the two leagues running on different fuel.
- **Teaser:** Of the +26 SR points the IPL gained (124→150), ~74% came from more boundary balls, ~14% from sixes replacing fours, ~10% from rotation.
- **Lenses:** batting-evolution

### Powerplay Exploitation Premium
Runs banked above par during fielding restrictions, traded against wickets spent — and how violently that repriced in 2023.
- **Recipe:** Tag exact PP deliveries via powerplays[] (verified present in effectively every innings, DLS-shortened PPs handled automatically). Per team-innings: PP runs above season par, PP wickets lost, downstream cost (post-PP RR conditional on PP wickets, league-wide). Premium = runs above par − wicket cost in run-equivalents.
- **Feasibility:** direct — reuses the SR+ par machinery; full-corpus aggregation ~4s.
- **Novelty:** known-but-underused · confirmed
- **Era story:** PP intent was strikingly flat for ~15 years, then detonated in 2023-26 — and the verified punchline is that the extra runs came *free* (wicket cost unchanged). WPL sits exactly on the 2008-IPL baseline, giving the evolutionary overlay for free.
- **Viz:** Field graphic with the 30-yard circle glowing during PP; per-season risk-budget meter (runs bought vs wickets spent) and a "price of a PP wicket" ticker that visibly crashes in 2023.
- **Teaser:** PP run rate 7.60 → 9.48 (IPL 2008-10 vs 2023-26) at identical wicket cost (1.54 vs 1.52 per 36 PP balls); WPL: 7.55.
- **Lenses:** batting-evolution

### Required-Rate Responsiveness (chase calibration)
In chases, how batter intent tracks the required rate: the slope of SR against RRR separates proactive pacers from firefighters.
- **Recipe:** Second innings: per-delivery RRR from target; bin batter SR by RRR band and RRR-minus-current-RR gap; responsiveness = ball-level regression slope of scoring on RRR controlling for phase and wickets in hand. Season "chase pacing curves" (mean RRR trajectory). **Correction:** fixed-ball RRR snapshots drop already-finished chases (biasing against the modern-frontloading story) — use survival-conditioned curves or per-over resampling; clip remaining-runs at 0.
- **Feasibility:** direct · confirmed (with the snapshot-bias fix)
- **Era story:** Old-school chases back-loaded risk; the modern chase kills the game inside the powerplay so RRR never rises. The pacing curve flipping from up-sloping to down-sloping is a one-chart summary of two decades of chase theory — with WPL curves showing which era of chase logic women's teams run.
- **Viz:** "Chase cockpit": a required-rate ribbon batters surf, era-average trajectories ghosted behind live replays; player dials from "thermostat" (pre-emptive) to "firefighter" (reactive).
- **Teaser:** Mean RRR drift by over 10: +0.61 (2008-10) vs +0.47 (2023-26); chases ahead of the rate at halfway rose 31.7% → 37.8% — despite the snapshot bias understating the shift.
- **Lenses:** batting-evolution

### Milestone Braking Index
Whether batters still slow down approaching fifties and hundreds: SR by personal-score band, isolating the 45-49 and 90-99 brake zones.
- **Recipe:** Running personal score per batter-innings; bucket every ball by score band; Braking Index = SR(45-49)/SR(38-44) with dismissal-rate deltas in the same bands. Pool multi-season windows (45-49 band has only 823/1,893 balls per era; 90s era-pooled only).
- **Feasibility:** direct · confirmed
- **Era story (inverted by the data, better than pitched):** braking has NOT vanished — it is mildly *stronger* now, and in both eras the 45-49 dismissal rate sits below 38-44 (nerves expressed as risk-aversion). Personal milestones still bend team-first cricket. Does the young WPL brake like old IPL?
- **Viz:** Speedometer strip along the personal-score axis with brake lights flaring at 45-49; era slider dims (or doesn't) the lights. Hall of fame: "honest finishers" vs "milestone decelerators".
- **Teaser:** Braking Index 0.989 (2008-10) vs 0.930 (2023-26) — modern batters ease off MORE approaching fifty; their 45-49 dismissal rate (4.81%) is well below their 38-44 rate (5.76%).
- **Lenses:** batting-evolution

### Finisher Rating
A shrunken composite of chase-death-overs performance: WPA/ball, boundary and dot rates vs state baselines, and chases converted vs model expectation.
- **Recipe:** Qualifying balls: overs 16-20, 2nd innings, RRR ≥ 8 (verified supply: 2,765 early / 4,979 recent). Composite z of (a) WPA/ball, (b) boundary% above baseline, (c) dot% below baseline, (d) conversion above entering-over-16 WP. Empirical-Bayes shrink; filter target.overs==20 and skip super overs. Ships after the WP model.
- **Feasibility:** derivable · confirmed
- **Novelty:** known-but-underused
- **Era story (recalibrated):** The invention of a job — count players with 100+ qualifying balls to watch the finisher role emerge (~2013+); the "fatal RRR" cliff moved from ~10 to ~12 (not 9→12 monotonic: RRR ≥ 12 is still ~12% in both eras). WPL's finisher cohort is forming live (RRR 8-10 chases won 75% — between IPL's two eras).
- **Viz:** "The Last Five Overs" hall: replay a finisher's best chase as an animated WP worm; era slider on the survival curve of chases by required rate — watch the cliff move right.
- **Teaser:** A chase needing 8-10 RPO with 5 overs left was won 54.8% of the time in 2008-10 but 85.0% in 2023-26; at RRR 10-12 win rate jumped 34.6% → 51.4%.
- **Lenses:** impact-value

### Entry-Point Adjusted Innings Value
Values each innings against what an average batter contributes from the identical entry state — a 30(15) entering at 17 overs can outrank a 70(55) as an opener.
- **Recipe:** Entry state (over.ball, wickets, innings, RRR if chasing) from first appearance; expected contribution = state-bucketed empirical mean with shrinkage (or RVAE baselines over expected survival); innings value = actual − expectation; career aggregate = position-neutral batting value. Filter replacements on reason=='impact_player' (exactly 557; plus 6 concussion + 20 role subs to exclude).
- **Feasibility:** derivable · **adjusted** — era story corrected: "positions 4-6 drift later" only holds for 4-5 (pos-4 median entry over 5.8 → 6.8); positions 6-7 enter slightly EARLIER now (15.5 → 15.0) — modern aggression burns wickets faster even as teams bat deeper. That two-way tension is the better exhibit.
- **Novelty:** known-but-underused
- **Viz:** Entry-state map: every innings of a career plotted at (entry over, wickets down), colored by value above expectation — drag-select a region ("entering at 15+, 4 down") to filter any player or era.
- **Teaser:** The No. 4's median entry drifted a full over later (5.8 → 6.8) while the No. 7's moved half an over earlier (15.5 → 15.0).
- **Lenses:** impact-value

### Cricket Linear Weights (the wOBA translation)
Empirical run values for every ball outcome — dot, single, two, four, six, wide, each dismissal kind — derived from run-expectancy state changes, exactly how baseball derives wOBA.
- **Recipe:** weight(outcome) = RE(after) − RE(before) + runs on the ball, using the season's RE288 matrix (derive from first-innings RE; second innings needs chase-aware truncation handling). Average by outcome type per season; batter wBRV = Σ weights per 100 balls above average; bowler version sign-flipped. Publish context-free AND phase-conditional weights.
- **Feasibility:** direct · **adjusted** — two corrections: the dot's run value is ~−0.85 → −1.12 (not −0.16); the wicket's absolute cost GREW (−7.07 → −7.43) and only shrank as a share of innings total (4.5% → 4.0%) — state the wicket claim in relative terms.
- **Novelty:** known-but-underused
- **Era story:** Track each event's price across 19 seasons. Verified headline the pitch missed: **the single flipped from value-neutral (−0.01) to value-LOSING (−0.27)** — in the modern IPL, rotating strike literally loses expected runs. Sixes stable at ~+4.5. IPL vs WPL weights show the leagues price risk differently.
- **Viz:** Animated "price board": each outcome as a stock ticker floating up/down with the season slider; click W to explode into dismissal kinds; batter pages show a wBRV waterfall.
- **Teaser:** Dot cost deepened −0.85 → −1.12; a single flipped from −0.01 to −0.27 expected runs.
- **Lenses:** sabermetric-translation

### Runs per Resource (DLS-denominated batting efficiency)
Runs scored per percentage of team resources (balls × wickets) a batter consumed — academic lineage via Beaudoin & Swartz.
- **Recipe:** Resource at any state = E[R|balls, wickets] from the era resource surface, normalized to 100% at innings start; consumption = entry resources − exit resources (apportion shared-wicket cost; not-outs exit at end-of-innings state). Efficiency = runs / resource%. Corrections: treat 'retired hurt' as state transfer/censoring (9 cases probed), use target.overs-adjusted surfaces for D/L, build separate era-band and WPL surfaces.
- **Feasibility:** derivable (needs the resource-surface engine) · confirmed
- **Novelty:** known-but-underused
- **Era story:** The anchor's obituary in resource units: batters who consumed 30% of resources for 40 runs were tolerated in 2010, extinct by 2024. Openers vs finishers efficiency convergence.
- **Viz:** Innings "resource pie" — each batter's slice sized by resources consumed, colored by runs per resource; season slider shows anchor slices dying out.
- **Teaser:** Anchor innings (20+ balls at SR<100) fell from 19.8% of all 20-ball innings (2008-10) to 5.7% (2023-26); WPL 14.2% — IPL-2009 vintage.
- **Lenses:** landscape-scan

### Partnership Tempo & Rebuild Persistence *(table-stakes)*
Partnership-level run rate and duration by wicket number — testing whether the post-wicket "rebuild" still exists.
- **Recipe:** Segment innings into partnerships from wicket events; per partnership: runs, balls, RPO, and RPO in the first 12 balls post-wicket vs innings baseline ("rebuild depth") per era. Non-striker tracking (present) gives exact pair attribution.
- **Feasibility:** direct · **adjusted** — the pilot INVERTS the pitched story: the post-wicket lull has not gone extinct. Relative dip slightly *deepened* (−7.9% → −9.4% vs baseline) even as absolute tempo rose.
- **Novelty:** table-stakes
- **Era story (corrected):** A myth-buster — "the one behavior T20 never killed." Slice by phase/wicket number for local extinctions. Pairs with New-Batter Tax (same finding, two lenses).
- **Viz:** "Aftershock" chart: average RPO in the 12 balls after a wicket, ball by ball, one line per era — watch the dip rise in level but never fill in.
- **Teaser:** Post-wicket 12-ball RPO: 7.03 vs 7.63 baseline (2008-10); 8.28 vs 9.14 (2023-26) — the rebuild lull rose in tempo but never disappeared.
- **Lenses:** landscape-scan

---

## 2. Bowling Evolution

### ★ Attack-Containment Frontier Drift
The Pareto frontier of bowling strike rate vs economy per season — does wicket-taking now buy containment, and how far has the whole frontier retreated?
- **Recipe:** Per bowler-season (≥90 legal balls): economy (batter runs + wides + no-balls per 6 legal balls; byes/legbyes excluded — document the convention project-wide) and strike rate (legal balls per bowler-credited wicket). Compute each season's Pareto-efficient hull; track hull drift.
- **Feasibility:** direct · confirmed. **One sub-claim refuted:** the cross-bowler econ~SR correlation is weakly POSITIVE in both eras (+0.12 → +0.03; WPL +0.34) — pitch the idea on the hull's retreat, not the correlation panel.
- **Novelty:** novel
- **Era story:** Early IPL had a viable containment-only identity (economy under 7, SR near 30). That corner of the frontier is now extinct — the frontier's rightward drift is the bowlers'-eye view of the scoring explosion.
- **Viz:** Gapminder-style animated scatter: every bowler-season a dot, the Pareto hull a glowing frontier line visibly retreating as years scrub past; ghost trails follow one bowler (Ashwin) across 15 frontiers.
- **Teaser:** Bowler-seasons with economy under 7.0: 49 of 169 (29%) in 2008-10 vs 4 of 267 (1%) in 2023-26.
- **Lenses:** bowling-evolution

### The Re-entry Tax
The runs cost of bringing a bowler back cold: economy in the first over of a new spell vs continuation overs, controlling for over-number.
- **Recipe:** Tag overs as spell-position 1 vs 2+ (spells defined per bowling end — see Spell Fragmentation); compare RPO and wicket rate within matched over-number bins (min 5 overs/group, weighted). Add within-bowler matching or bowler fixed effects (continuation overs skew toward frontline bowlers). Pool 2-3 season windows.
- **Feasibility:** derivable · confirmed
- **Novelty:** novel
- **Era story:** The counterweight to spell fragmentation: the tax never shrank — a stable ~0.2 runs/over leak per re-entry, meaning matchup-chasing captains pay a real, constant toll for shattering quotas.
- **Viz:** Per-season dumbbell (first-over-of-spell vs continuation economy); hover any death over in a replay strip to see "cold re-entry, expected tax +0.8".
- **Teaser:** Over-number-matched cold-re-entry tax: +0.15 runs/over (2008-10) vs +0.19 (2023-26); WPL +0.19.
- **Lenses:** bowling-evolution

### Squeeze Retention & Bleed-Stopping
Bowler performance conditional on pressure: economy when the required rate favors the bowling side, and P(boundary next ball | just conceded a boundary).
- **Recipe:** Per 2nd-innings ball, RRR band (<8, 8-10, 10-12, 12+) from target{}; per bowler-season and league: economy, dot%, wicket rate by band (exclude reduced-target and D/L innings). Bleed-stopping: among consecutive legal balls by the same bowler, P(boundary | previous ball was boundary) vs unconditional — a bounce-back index (extend across spell as a second pass).
- **Feasibility:** derivable · confirmed — RRR band samples healthy (2.5k-8.8k balls per band per era).
- **Novelty:** novel
- **Era story:** Verified bonus: the bounce-back lift is a stable null (+4.0pp then, +3.9pp now) — modern bowlers armed with pre-planned B-options do NOT stop the bleed any better. Meanwhile the "defendable RRR" threshold crept up.
- **Viz:** Two-node Markov diagram (boundary / no boundary) with animated transition arrows morphing across eras; a pressure dial on each bowler card (economy at RRR 10+ vs cruise).
- **Teaser:** At RRR 12+, bowlers conceded 8.44 RPO in 2008-10 vs 9.91 in 2023-26; P(boundary | boundary) lift unchanged at ~+4pp.
- **Lenses:** bowling-evolution

### Quota Fatigue Curve → The 4th-Over Premium
Outcomes by a bowler's 1st-4th over of the match — reframed by verification as "who earns the 4th over and what it's worth."
- **Recipe:** Index each bowler's overs within an innings 1-4; per season: RPO, wicket rate, wide+no-ball rate by quota position, controlled for over-number (two-way fixed effects). **Bowler fixed effects are mandatory, not optional** — selection (only frontline bowlers earn a 4th over) inverts the raw premise. Second output: over-number distribution of 4th quota overs.
- **Feasibility:** derivable · **adjusted** — raw premise inverted: the 4th over runs BELOW par (−0.27 early, −0.10 recent; WPL −0.23).
- **Novelty:** novel
- **Era story (corrected):** The 4th over is a bargain, not a tax — and its elite-bowler premium has more than halved (−0.27 → −0.10), while Q4 scheduling into overs 17-20 is static (67% → 66%; WPL 74%). Fresh WPL question: is the women's 4th-over premium bigger (thinner attacks)?
- **Viz:** Four-cell "quota strip" on every bowler card tinted by relative economy; the league-level curve flattening across the era scrubber.
- **Teaser:** The 4th quota over ran 0.27 RPO below its over-slot par in 2008-10, shrinking to 0.10 below in 2023-26.
- **Lenses:** bowling-evolution

### FIB: Field-Independent Bowling (the FIP/BABIP translation)
Splits bowling results into what the bowler controls (bowled/lbw, boundaries, dots, extras) and what fielders/luck control (caught, run out) — cricket's FIP, validated by prediction.
- **Recipe:** FIB = linear-weight value per ball using only fielder-independent events (bowled + lbw + hit-wicket, **and caught-and-bowled — classify as fielder-INdependent**, stumped tested both ways); replace caught outcomes with league-average ball-in-play value. Validation: year-N FIB vs year-N results predicting year-N+1 (restrict to bowlers with 120+ balls both seasons). Report caught and run-out luck components separately (their mix shifts across eras).
- **Feasibility:** direct · confirmed
- **Novelty:** novel
- **Era story:** Caught rose 59.9% → 72.3% of dismissals while run outs fell 12.0% → 5.3% — the fielder-dependent share of bowling outcomes swelled by a fifth, making raw bowler stats *less* skill-reflective in 2026 than 2008; FIB strips exactly that drift. Also names which legendary seasons were catch-conversion mirages.
- **Viz:** Dual leaderboard with a "strip the luck" morph toggle — bars re-sort from actual results to FIB with movement trails; dismissal-mix stacked area 2008→2026.
- **Teaser:** Caught 59.9% → 72.3%, run outs 12.0% → 5.3% — exactly the era drift FIB is built to remove.
- **Lenses:** sabermetric-translation

### Death-Over Specialization Gini *(bowling-tactics)*
How concentrated the overs-17-20 workload is in designated closers, per team-season — the rise of the bowling closer role.
- **Recipe:** Per team-season: distribution of death overs across the squad; Gini/HHI (define the population explicitly — results differ); companions: cross-phase mobility matrix, top death bowler's share trend, death economy premium for specialists vs non-specialists.
- **Feasibility:** direct · confirmed — but the effect is real-yet-modest: temper the closer narrative or sharpen it with the companions.
- **Novelty:** novel
- **Era story:** Did 2008 teams spread death overs democratically while 2020s teams funnel them into one or two closers — and did specialization buy economy?
- **Viz:** Phase-allocation subway map per franchise — bowlers as lines traveling through PP/middle/death stations, consolidating onto dedicated death tracks as the era slider advances.
- **Teaser:** Top death bowler's share of team overs 17-20: 26.6% (2008-10) → 30.2% (2023-26); death-over Gini 0.412 → 0.443.
- **Lenses:** team-tactics-meta

### Phase Fingerprint & Specialization Entropy
How narrowly each bowler's overs concentrate into specific over-numbers/phases — with a verified reframe away from "entropy fell league-wide."
- **Recipe:** Per bowler-season, legal deliveries per over-number 1-20 (skip super overs); specialization = 1 − normalized Shannon entropy (min 60 balls). **Corrections:** (1) classify archetypes by over-indexing vs phase availability (share/availability ≥ 2×) — the naive ">55% of overs in one phase" rule yields ZERO death specialists ever; (2) balls-weighted entropy is FLAT across all 19 seasons (0.178-0.212), so drop the "hyper-specialization grew" headline.
- **Feasibility:** direct · **adjusted**
- **Novelty:** known-but-underused
- **Era story (corrected):** The live signal is phase-specific: death-phase over-indexing rose from ~0-2% (2008-10) to 9-21% (2013-2023) then slumps by 2026 — death-specialist emergence and its recent erosion (Impact Player flexibility?), not monotonic entropy decline.
- **Viz:** Each bowler as a 20-cell "barcode" (opacity = share of balls per over-slot); the league's stacked barcodes sharpen from smeared to striped — for the death slots specifically.
- **Teaser:** Death balls delivered by 2×-death-over-indexed bowlers: 0.0% (2008) → 17.3% (2023), peak 20.6% (2021) — yet overall over-slot entropy is flat for 19 seasons.
- **Lenses:** bowling-evolution

### Dot+ : Era-Normalized Dot Manufacturing
A park/era-adjusted dot-ball rate (like ERA+): dots manufactured relative to an average bowler with the same phase mix in the same season.
- **Recipe:** Dot = legal delivery with runs.total==0; baseline dot% per season × over-number (optionally venue, after canonicalization); Dot+ = 100 × actual/expected dots (min 120 legal balls). League raw dot% by phase as backdrop.
- **Feasibility:** direct · confirmed — extras schema identical 2008-2026; baselines compute in seconds.
- **Novelty:** known-but-underused
- **Era story:** Dots are a deflating currency: a 40% dot rate in 2026 is a different achievement than in 2009. Dot+ puts Malinga-2010 and Bumrah-2024 on one leaderboard and asks whether elite dot-manufacture (Dot+ 130+) is going extinct.
- **Viz:** An innings as a 120-pixel grid with dots as dark cells — 2009 vs 2026 side by side makes the erosion visceral; bowler cards get a Dot+ gauge with a moving era zero-line.
- **Teaser:** League dot rate fell 37.6% → 33.0% of legal balls; WPL sits at 38.5% — almost exactly IPL 2009.
- **Lenses:** bowling-evolution

### Dismissal DNA
The evolving mix of HOW wickets fall — bowled/lbw vs caught-in-the-deep vs caught-behind (keeper-inferred) vs stumped — by phase and era.
- **Recipe:** Per season × phase, share of each wickets[].kind (bowler-credited core view; run outs separate). Caught-behind proxy: infer each team's keeper from stumping credits (per-match → team-season most-frequent-stumper → career fallback; 84% of team-seasons covered, document the ~16% residual); 'caught' with fielders[0]==keeper = caught behind.
- **Feasibility:** derivable · confirmed — core streamgraph needs no inference at all.
- **Novelty:** known-but-underused
- **Era story:** Bowled+lbw share fell 27.4% → 21.3% while caught rose 65.2% → 74.1% — fingerprint evidence bowlers stopped attacking stumps and started attacking the long boundary. Stumped collapsed 4.2% → 1.9% in IPL but is 6.8% in WPL — a genuinely different dismissal ecology.
- **Viz:** Streamgraph of dismissal kinds across 19 seasons with animated icons (castled stumps, deep catch, edge); click a stream to isolate "the last era when LBW mattered."
- **Teaser:** IPL stumped share 4.2% → 1.9%; WPL 6.8%.
- **Lenses:** bowling-evolution

### Wicket Value Index (not all wickets are equal)
Each dismissal priced in expected runs prevented given its state — separating the set-opener scalp in over 14 from tail-end mop-up.
- **Recipe:** From the RE layer, R(over, wickets) per era window; wicket value = R(s, w) − R(s, w+1) at the ball's state (also expressible as ΔWP). Bowler credit = Σ values excluding run outs (1,185 verified → fielding credit); Weighted Wickets = Σ values / era-average wicket value. Add min-sample shrinkage for rare states.
- **Feasibility:** derivable · **adjusted** — pitched era story contradicted: a wicket costs MORE expected runs now (3.99 → 5.30), appreciating even deflated by CPI (~0.50 → ~0.55 overs-equivalent). Headline must be "wickets appreciated with inflation," or slice by batting position/over for any compression story.
- **Novelty:** known-but-underused
- **Viz:** A bowler's career as a bubble timeline — every wicket a bubble sized by run value, so Malinga's death scalps visually dwarf equal wicket counts; league ribbon of wicket worth by over, era-animated.
- **Teaser:** The average bowler-credited wicket removed 3.99 expected runs in 2008-10 vs 5.30 in 2023-26 — +33%, outpacing run-rate inflation.
- **Lenses:** impact-value

### Wickets Above Expectation (WAE)
Bowler strike ability vs a per-ball dismissal-probability model — actual wickets minus expected over the balls actually bowled.
- **Recipe:** Fit P(bowler-credited wicket | over, wickets, innings, RRR gap, batter balls-faced-so-far) — logistic/GBM on 295k balls, ~4.5% positive rate (~13,440 bowler-credited wickets; exclude run out, retired hurt/out, obstructing). WAE = actual − Σ P̂. Batter mirror: Dismissals Below Expectation. Guard against leakage in the set-batter feature.
- **Feasibility:** derivable · confirmed
- **Novelty:** known-but-underused
- **Era story:** The league expected-wicket rate per phase charts the attack-vs-contain revolution: death dismissal rates rising as batters accept risk — batters buying runs with wickets. IPL-vs-WPL gap places the women's league on that curve.
- **Viz:** Quadrant plot per era (x: runs saved above expectation, y: WAE) — the bowler population migrating from "containers" toward "strikers" as you scrub 2008→2026.
- **Teaser:** Death-overs bowler-credited dismissal rate rose 7.07% → 7.42% per legal ball even as death RPO exploded.
- **Lenses:** impact-value

### True Economy + True Wickets per 24 (inflation-adjusted bowling)
The bowling mirror of SR+: runs conceded and wickets taken vs expectation for the exact overs bowled (phase, venue, era).
- **Recipe:** Same conditional baselines as SR+, flipped: TrueEcon = Σ(expected − conceded)/overs; TrueW24 = (actual − expected wickets) per 24 balls. Bowler-charged runs = runs.batter + wides + no-balls (verified exactly computable; byes/legbyes exclusion shifts league RPO ~0.15).
- **Feasibility:** derivable · confirmed
- **Novelty:** known-but-underused
- **Era story:** Who actually got better as batting exploded? A 7.5 death economy in 2024 is elite; the same figure in 2012 was mediocre. Is the death specialist a dying or thriving species?
- **Viz:** Bowler "headwind" chart: raw economy drifting up with the league tide, true economy plotted as deviation from the tide — Bumrah/Rashid defying gravity.
- **Teaser:** League bowler-charged economy rose 7.79 → 9.38 RPO — a 7.5 economy went from league-par (2009) to 1.9 RPO better than par (2025).
- **Lenses:** landscape-scan

### Bowling-Style Phase Shares Across Eras (spin invasion of the powerplay) *(needs-external-data)*
Share of overs by bowling type and phase across eras — requires an external player-style join but unlocks the spin-era narrative and style-aware matchups everywhere else.
- **Recipe:** Join bowler registry IDs → Cricsheet people register → ESPNcricinfo profile keys → bowling style (verified two-hop join, no fuzzy matching). Then: spin share of overs by phase/season, wrist vs finger spin eras, left-arm pace premium, handedness-aware matchup matrices. Label by career-balls-bowled descending — top ~300 of 577 IPL + 96 WPL bowlers covers most deliveries.
- **Feasibility:** needs-external-data (source: ESPNcricinfo profiles via Cricsheet people.csv / cricketdata package; Kaggle IPL metadata as secondary) · **adjusted** — labeling burden smaller than pitched (577+96, not ~700). **The single highest-leverage external join for the project.**
- **Novelty:** known-but-underused
- **Era story:** The middle-overs wrist-spin boom (2016-19), spinners invading the powerplay, pace holding the death; whether WPL leans more on spin than the IPL did at the same league age.
- **Viz:** A 20-over "strata" chart: each over-slot colored by dominant bowling type, morphing across seasons — the spin belt visibly migrating.
- **Teaser:** (none computable without the join — see Stumping Signature for the in-data proxy)
- **Lenses:** landscape-scan, bowling-evolution

---

## 3. Scoring Environments & Venues

### ★ Toss Revolution: Decision Evolution, Toss Value, and the Chase-Bias Reality Gap
Tracks the collapse of "bat first" — the share of toss winners choosing to field — against the actual realized chase advantage, exposing when captains' herd belief outran the evidence.
- **Recipe:** Per season: (a) field-first% from toss.decision; (b) chase win% among decided matches; (c) toss-winner match-win conversion; (d) belief-reality gap = (a) − (b). Split by venue and league. Counterfactual series: the decision a Bayesian captain would make from trailing 3-season venue chase win rates.
- **Feasibility:** direct · confirmed — fully verified on all 1,331 matches, no recipe corrections.
- **Novelty:** known-but-underused
- **Era story:** The single clearest behavioral revolution in the data: a near-universal chase-first doctrine emerged (~2016) that outcomes only partially support. WPL captains inherited the doctrine fully formed from season one (77% field-first, though their 60% chase win rate partially justifies it) — a culture-transmission story.
- **Viz:** Dual-line chart with the belief-reality gap shaded as a widening wedge; a "captain simulator" toggle overlays what pure evidence would have decided; per-venue small-multiple grid shows where fielding first is genuinely justified.
- **Teaser:** Field-first went 43% (2008-10) → 77% (2023-26) — while the chase win rate went 54% → 53%. The doctrine hardened; the evidence never did.
- **Lenses:** scoring-environment, landscape-scan, team-tactics-meta, wpl-comparative

### ★ Run-Expectancy Surface Drift
The full run-expectancy surface (expected runs-to-come by ball number × wickets lost) per season, measuring where the surface deformed most — a standalone exhibit AND the engine behind era translation and counterfactuals. (**Engine layer #2**, with RE288 below.)
- **Recipe:** Walk first-innings deliveries accumulating (ball 1-120, wickets, runs-to-come); average per cell per season; smoothing/GAM pooling is **mandatory, not optional** (single-season wicket-state cells run n=26-77); WPL needs hierarchical pooling across its 4 seasons. Drift = state-visit-weighted RMSE between season surfaces; per-cell deltas localize deformation. Matching 2nd-innings WP surfaces from target.runs (present in all 1,325 second innings).
- **Feasibility:** direct · confirmed
- **Novelty:** known-but-underused
- **Era story:** Localizes the revolution — and the probe already found the headline: **the value of wickets in hand has collapsed.** In 2008-10, being 3 down (vs 2) at over 7 cost ~12 expected runs; in 2024-26 it costs ~0.4. Depth (Impact Player) made the scoreboard state nearly wicket-indifferent.
- **Viz:** Morphing heatmap (ball × wickets → expected runs-to-come) with a season scrubber; "difference lens" pins a reference season and paints red/blue deltas — drag 2016→2026 and watch the surface inflate from the middle overs outward.
- **Teaser:** Expected runs-to-come at over 7, 2 down: 110.3 (2008-10) vs 130.8 (2024-26); the 3rd wicket's marginal cost collapsed ~12 → ~0.4 runs.
- **Lenses:** era-machine-regime-detection

### Photo-Finish / Thriller Rate (match closeness and the decision ball)
How close matches really are: victory margins normalized onto one scale, plus the "decision ball" — the earliest moment a WP model says the match was effectively over.
- **Recipe:** (a) Unified margin: defenses as margin/first-innings total; chases mapped through a resource table into equivalent-runs margin. (b) Binned WP lookup on all chases (era-split to avoid anachronistic baselines); decision ball = last ball the eventual loser's WP > 10%. Season aggregates: median normalized margin, % alive entering over 19, last-ball/super-over rate (all 16-17 tie matches carry super-over innings), margin Gini. Exclude D/L.
- **Feasibility:** direct · confirmed — no recipe corrections.
- **Novelty:** novel
- **Era story:** Tests the Impact-Player-as-comeback-mechanism sales pitch — the proxy already shows a genuinely interesting null (closeness flat), while the young WPL is the tightest league in the dataset.
- **Viz:** Season beeswarm on a closeness axis with photo-finishes glowing; click any match to open its WP timeline with the decision ball flagged; a "still alive at over 19" gauge per season.
- **Teaser:** Photo-finish rate (≤5 runs or ≤3 balls to spare): IPL 17.3% (2008-10) vs 16.0% (2023-26); WPL 24.1%.
- **Lenses:** scoring-environment, wpl-comparative

### Dew Dividend (evening second-innings ease index)
A dew proxy: how much easier batting gets in the second innings of evening games — isolated from chase tactics — per venue and season.
- **Recipe:** Within-match paired design: Δ = (inn2 RPO in overs 7-15, ≥6 wickets in hand, RRR within ±1.5 of initial ask) − (inn1 RPO, same overs) — **the conditioning is load-bearing** (the crude delta collapses +0.35 → +0.08 across eras purely from chase truncation). Also Δboundary%, Δdismissal, Δwide rate (wet-ball tell). Afternoon games identified via double-header date + match_number inference; full start times would need ESPNcricinfo.
- **Feasibility:** derivable · confirmed
- **Novelty:** novel
- **Era story:** Quantifies the mechanism behind the toss revolution: which grounds' dividend grew, whether it justified the 2016+ field-first herd, and whether WPL's Feb-Mar window shows a smaller dividend — evidence the chase-first doctrine was cargo-culted into the women's league.
- **Viz:** Venue heatmap of dew dividend with evening/afternoon toggle; per-match dumbbell (inn1 → inn2) leaning right in dew-heavy games; scatter linking each venue's dividend to its field-first%.
- **Teaser:** Second-innings mid-overs ran +0.35 RPO hotter than first innings within the same match in 2008-10 — the raw signal the conditioning will decompose into dew vs tactics.
- **Lenses:** scoring-environment

### Pitch Homogenization Index (scoring dispersion)
The within-season spread of first-innings totals and the between-venue variance share — testing whether India's grounds are converging into one flat scoring environment.
- **Recipe:** Per season: SD/IQR/CV of full first-innings totals; ANOVA variance share explained by venue means; dispersion of ground factors. Needs the venue canonicalization table for cross-season strands; interpret UAE seasons (2014, 2020-21) carefully.
- **Feasibility:** direct · **adjusted** — the probe answers in the OPPOSITE direction: venues are *diverging*, not homogenizing. Lead with divergence.
- **Novelty:** novel
- **Era story (corrected):** Curated 200-par surfaces did NOT flatten the country — Chepauk and Eden keep their character while others inflate, so venue identity is *growing*. Either direction was a story; the data picked the contrarian one.
- **Viz:** "Convergence cone": each ground a strand plotting its mean total over seasons — the strands visibly fan apart; violin-per-season strip below as distributional backdrop.
- **Teaser:** Between-venue share of first-innings-total variance nearly tripled: ~11% (2008-10) → ~27% (2023-26).
- **Lenses:** scoring-environment

### Venue Familiarity Decay Curve
Team performance at a venue as a function of matches played there recently — testing whether data-era teams neutralized the unfamiliarity penalty.
- **Recipe:** Per (team, match): familiarity = team's matches at that venue in prior 3 seasons; outcome = net run margin standardized against the venue's rolling par, plus first-innings SR delta vs venue par. Fit familiarity-response curves by era. Requires the ~35-entry venue-alias map. Relocation seasons (2009, 2014 leg, 2020-21) supply hundreds of zero-familiarity observations.
- **Feasibility:** direct · confirmed — the exile-season contrast already validates the hypothesis at league level.
- **Novelty:** novel
- **Era story:** In 2009 (South Africa) every team was a stranger and scoring cratered; in 2020 (UAE) every team was a stranger and scoring barely dipped — direct evidence that video/data staffs neutralized venue unfamiliarity.
- **Viz:** Decay curves as era-colored strands that flatten over time, with the 2009 and 2020 exiles highlighted as constellation points at familiarity zero.
- **Teaser:** The 2009 relocation cost 0.82 RPO league-wide (8.31 → 7.49); the 2020 relocation cost just 0.13 (8.42 → 8.29).
- **Lenses:** schedule-calendar-fatigue

### Calendar Climate Curve
Day-of-year as a scoring covariate — separating seasonal climate from within-season pitch wear using the calendar window's 19-year drift plus the autumn 2020 season.
- **Recipe:** Per innings: day-of-year and within-season match index; jointly model 1st-innings totals, chase success, middle-overs RR on both. Identification: the window moved (Apr 18 starts in 2008 → Mar 22 by 2024; 2020 ran Sept-Nov), decorrelating the two covariates across eras. Spin/pace decomposition needs external style data; all else local.
- **Feasibility:** direct · confirmed
- **Novelty:** novel
- **Era story:** "Tired late-season pitches" is folklore that the data can finally test — and the probe shows the within-season effect has *inverted* across eras.
- **Viz:** Polar annulus calendar (Jan-Dec ring): each season an arc at its true dates, colored by scoring intensity — arcs rotating counter-clockwise over the years, the 2020 arc stranded alone in autumn.
- **Teaser:** Second-half-of-season totals were 4.2 runs LOWER than first-half in 2008-10, but 4.2 runs HIGHER in 2023-26.
- **Lenses:** schedule-calendar-fatigue

### Convergence Clock (2030 forecast + WPL intersection posterior)
A regime-aware Bayesian forecast of the 2030 scoring environment with honest uncertainty fans, plus the posterior for when WPL's environment reaches chosen IPL historical levels.
- **Recipe:** Bayesian structural time series (local linear trend, changepoints from the Seismograph as level-shift priors) on seasonal RR/six rate/dot rate; sample paths to 2030. WPL: hierarchical model with the IPL's early-seasons trajectory as growth-curve prior; per-metric crossing-time posteriors. Normalize seasons by dates[0], not the season string.
- **Feasibility:** derivable · confirmed — 19 clean annual points; render uncertainty prominently or it becomes astrology.
- **Novelty:** novel
- **Era story:** If the 2023-26 slope (~+0.30 RR/season) holds, league RR crosses 10 around 2027-28 — or does the model see saturation? And WPL's run-rate convergence arrives roughly a decade before its six-rate convergence — pre-verified that the per-metric split gives different answers.
- **Viz:** Clock/horizon hybrid: history flows into a fan of sampled futures; drag a "target level" line to IPL 2020's RR and a posterior histogram of the WPL crossing season materializes.
- **Teaser:** WPL 2026 RR (8.54) = IPL 2022 exactly, but WPL's six rate (3.65%) is still at IPL 2011-13 levels.
- **Lenses:** era-machine-regime-detection

### Phase Economy Map (powerplay/middle/death escalation compression)
Powerplay / middle / death shares of runs, wickets, boundaries and dots per season — locating exactly where in the innings the run environment moved.
- **Recipe:** Bound the mandatory PP exactly via powerplays[] (robust to shortened innings; type 'mandatory' verified in effectively every innings); middle = post-PP to over 15, death = 16-20. Per season/league/venue: phase RPO, wicket rate, run share, boundary%, dot%; report the death-minus-PP RPO spread. Decide the rain-shortened rule (scale vs exclude) up front.
- **Feasibility:** direct · confirmed — compression story confirmed almost exactly as pitched.
- **Novelty:** known-but-underused
- **Era story:** Early IPL: spin-strangled middle and a huge death premium. Modern IPL: PP RPO surging toward death RPO — the innings becoming phase-agnostic. WPL still shows the old-shape premium, dating its evolutionary stage.
- **Viz:** Streamgraph of phase run shares 2008-2026, plus an "innings clock" — a 20-segment radial dial heat-colored by per-over RPO that repaints as the era slider moves.
- **Teaser:** Death-minus-PP RPO spread compressed 1.98 → 1.18 (IPL); WPL sits at 2.25 — wider than 2008 IPL.
- **Lenses:** scoring-environment, bowling-evolution, landscape-scan, team-tactics-meta

### Extras Weather: Wide Inflation, Discipline, and the Death-Wide Tax
Extras as a scoring-environment component: wide/no-ball rates, the free runs they inject, and what a >50% rise in wides says about umpiring strictness and death-bowling risk appetite.
- **Recipe:** Per season/phase/league: wides per 100 legal balls, no-ball rate, byes/legbyes/penalty; extras as % of match runs; free-hit tax (runs on the delivery after a no-ball — pair by sequence, not delivery number); death-over wide rate separately. **Correction:** the wide/no-ball DRS-review sub-metric is NOT computable (review.type only ever says 'wicket' or is absent) — replace with umpires_call burn (140 tagged reviews).
- **Feasibility:** direct · **adjusted**
- **Novelty:** known-but-underused
- **Era story:** Wide rate troughed 2.71/100 (2013) and rose to 4.78 (2026) — bowlers pushing wide-line margins in a 200-par world plus stricter calling. The death split is the star: it doubles while the all-phase rate rises modestly. Wide-yorker arms race = a men's-league phenomenon (WPL death wides: 2.8).
- **Viz:** "Leak gauge": extras runs per match as a rising fluid level, phase-split small multiples, rule-change annotations (free hit 2015, wide reviews 2023) pinned on the timeline.
- **Teaser:** Death-over wides DOUBLED: 3.3 per 100 legal balls (2008-10) → 6.7 (2023-26); WPL just 2.8.
- **Lenses:** scoring-environment, bowling-evolution, team-tactics-meta, hidden-fields, wpl-comparative

### Venue Fingerprints & Park Factors
Per-venue scoring DNA — par score, phase RPO shape, chase bias, six rate — as venue fixed effects, with real boundary dimensions as an optional external garnish.
- **Recipe:** Venue fixed effects from a mixed model on innings totals (season + venue + toss); per-venue phase RPO profiles and six rates; pool venue effects across rolling 3-season windows (per-venue-season samples are thin). The ~60-row venue canonicalization table is required preprocessing (**engine layer #4**). Boundary dimensions: annotation-only, low-reliability external (scattered media/stadium guides — no authoritative dataset).
- **Feasibility:** derivable · confirmed
- **Novelty:** known-but-underused
- **Era story:** Venue identity persistence in the flat-pitch era — direct evidence venues have NOT homogenized (pairs with the Homogenization Index). WPL venue rotation effects on its scoring numbers.
- **Viz:** Venue "vinyl records": each ground a circular phase-RPO radial fingerprint; a map of India where stadiums pulse by par score per season.
- **Teaser:** 2023-26 average first innings: Chinnaswamy 197 vs Chepauk 174 — a 23-run venue gap persisting in the flat-pitch era.
- **Lenses:** landscape-scan, scoring-environment, sabermetric-translation

### RE288: Era-Specific Run-Expectancy / Resource Surfaces
The cricket RE24: expected runs remaining from every (balls-remaining × wickets-lost) state, rebuilt per season — the engine powering linear weights, WPA, leverage, and sequencing ideas. (**Engine layer #2**, tabular form of Surface Drift above.)
- **Recipe:** Per first-innings delivery: state (legal balls bowled 0-119, wickets 0-9) and runs-to-come; season averages with GAM smoothing over the 120×10 grid (single exact cells yield only ~46-62 innings per era-band — raw per-season cell means are too noisy). Count legal balls correctly; treat rain-shortened innings as censored. WPL gets its own heavily-pooled matrix.
- **Feasibility:** direct · confirmed — verified end-to-end.
- **Novelty:** known-but-underused
- **Era story:** The matrix IS the era: watching 2008's surface morph into 2026's shows exactly where teams stopped conserving wickets (the middle-overs plateau), and quantifies how much less a wicket "costs" in the Impact Player era.
- **Viz:** 3D/heatmap surface with a season scrubber; "diff mode" colors cells by change vs 2008, lighting up the middle overs; overlay the WPL surface on the IPL one.
- **Teaser:** Expected runs remaining from "10 overs bowled, 3 down": 90.6 (2008-10) vs 98.3 (2023-26).
- **Lenses:** sabermetric-translation, landscape-scan

### Par-Score Drift
The first-innings total that wins exactly 50% of the time — per season and per ground — and how fast that number is climbing.
- **Recipe:** On decided, non-D/L matches with **full first innings** (20 overs or all out — the filter the pitch missed): logistic P(bat-first wins) ~ total + season spline + venue random effect; Par = fitted P=0.5; also safe (0.75) and dead (0.25) scores. Validate against empirical 10-run bins; fallback = rolling median of defended totals.
- **Feasibility:** direct · confirmed (n=166 early / 279 recent decided matches — regression holds)
- **Novelty:** known-but-underused
- **Era story:** Par jumped ~30 runs in the Impact Player era; at some grounds today's par exceeds what was a winning score anywhere in 2012. WPL par vs IPL par quantifies the league gap.
- **Viz:** "Rising tide": the par line climbs while every match sits as a dot (defended/chased); the water level drowns totals that used to be safe; ground selector re-draws the tide per venue.
- **Teaser:** Logistic par: 165 (2008-10) → 195 (2023-26); 230+ totals were 11/11 defended in 2023-26.
- **Lenses:** scoring-environment

### Double-Header Dew Ledger
Uses the 296 same-date match pairs — lower match_number = afternoon — to cleanly isolate the dew effect on chasing and audit whether toss decisions rationally track the slot.
- **Recipe:** Group by (season, date); tag min(match_number) afternoon (all 296 pairs verified to carry both numbers; zero 3-match days; playoffs never share dates). Within double-header days: afternoon vs night chase win rate, inn2-vs-inn1 mid-overs RR, wides (wet-ball tell), toss field-first rate by slot and season.
- **Feasibility:** direct · confirmed
- **Novelty:** known-but-underused
- **Era story:** Verified twist that upgrades this from dew tracker to decision audit: **night chases in double-headers win LESS (51.0%) than afternoon chases (57.3%)** — captains' dew-driven field-first conviction is not supported by outcomes. Field-first-at-night went 49.2% (2008-13) → 77.9% (2014-19).
- **Viz:** Split-violin pairs per season (afternoon vs night totals) with a "dew meter" needle; a toss-audit strip tinting each season by how slavishly captains fielded at night.
- **Teaser:** Captains fielded first in 77.9% of night double-header games in 2014-19 — yet night chases won only 51.0% vs 57.3% for afternoon.
- **Lenses:** schedule-calendar-fatigue

### Playoff Pressure: Knockout vs League-Stage Shifts
Uses event.stage to measure how scoring, boundaries, dots, and extras change in knockout cricket vs the group stage.
- **Recipe:** Unified knockout flag over stage labels (Final 19, Qualifier 1/2 32, Eliminator 13, Semi Final 6, Elimination Final 3, 3rd-Place 1 — verified exact; group matches have stage absent). Per pooled multi-season window: knockout-minus-group deltas in RR, boundary%, dot%, wides, reviews, run-out rate; venue-adjust (finals concentrate at few grounds). Uncertainty bands mandatory (early-era KO ≈ 2,275 legal balls).
- **Feasibility:** direct · confirmed
- **Novelty:** known-but-underused
- **Era story:** Pressure cricket used to resist the batting revolution — knockouts played measurably slower — but the drag has vanished: conservatism became too costly.
- **Viz:** Per-season dumbbell (group dot vs knockout dot) with a "pressure gap" band; click a final to overlay its worm on the season's median group-stage worm.
- **Teaser:** Knockouts scored 0.65 RPO BELOW group stage in 2008-10 (7.02 vs 7.67); by 2023-26 they score 0.09 ABOVE (9.23 vs 9.13).
- **Lenses:** hidden-fields, team-tactics-meta

### T20 Consumer Price Index (run-rate inflation index) *(table-stakes)*
A CPI of league scoring — RPO indexed to a 2008 base — so every stat in the project can be quoted in "real" era-adjusted runs.
- **Recipe:** Per season: RPO overall, first-innings-only, and per phase (exact PP via powerplays[]); Index = RPO_s / RPO_2008 × 100; publish a deflator function. Exclude super overs; optionally exclude the 23 D/L matches from the headline.
- **Feasibility:** direct · confirmed. **Novelty:** table-stakes — but it is the backbone every other metric quotes.
- **Era story:** Turns "is 180 good?" into a real-vs-nominal question; visible 2023 discontinuity. Bonus verified hook: WPL all-time first-innings RPO (8.07) ≈ IPL 2008-10 (8.03), so the deflator can place WPL seasons on the IPL timeline.
- **Viz:** CPI line with shaded era bands (UAE 2014, COVID 2020, Impact Player 2023) plus a currency-converter widget: type "180 in 2010" → the equivalent 2026 total, animated along the curve.
- **Teaser:** First-innings RPO: 8.03 (2008-10) → 9.55 (2023-26), index 119 on a 2008-10 base; 2026 alone = 9.87.
- **Lenses:** scoring-environment

### Threshold Exceedance Curves (the 200 Club and the 250 Frontier) *(table-stakes)*
The full survival curve of first-innings totals per season — P(total ≥ X) for every X.
- **Recipe:** For full-length first innings (state the filter explicitly — 200+ counts shift ±1 with it), empirical survival function per season; extract P(≥180/200/220/250) and season max; repeat per ground, for WPL, and for second innings (chased-down 200s). **Correction:** "the 250 frontier exists only in the Impact Player era" is false — RCB 263 in 2013 (Gayle 175*); 250+ counts: 2013:1, then 2023:1, 2024:6, 2025:2, 2026:5.
- **Feasibility:** direct · **adjusted**. **Novelty:** table-stakes
- **Era story:** The 2023 discontinuity is the most dramatic single number in the dataset — 200+ tripled in one season and kept climbing. WPL 2026's exceedance curve sits between IPL 2008 and 2015.
- **Viz:** Ridgeline of total distributions stacked by season with milestone thresholds as vertical light beams that glow brighter as distributions cross them; a record ticker animates each new all-time high.
- **Teaser:** P(first innings ≥ 200): 7.7% (2008-10) → 41.9% (2023-26); 2026 alone: 52%.
- **Lenses:** scoring-environment

### Run DNA (boundary/rotation composition of scoring) *(table-stakes)*
Every season's runs decomposed into sixes, fours, running (1s/2s/3s) and extras — the changing genetic makeup of a T20 run.
- **Recipe:** Per season/league/venue: run shares by component from runs{} and extras{}; six:four ratio, dot%, balls-per-boundary; cross with the CPI to separate structural from volume change. Convention: no-ball batter runs → batter component.
- **Feasibility:** direct · confirmed. **Novelty:** table-stakes
- **Era story:** Six-share rises steadily while dots erode — and the verified WPL nuance: WPL is NOT "fewer boundaries," it is *four-led* (46.8% of runs from fours vs recent IPL's 33.9%, six-share 15.5% vs 29.0%) — genuinely different DNA, not scaled-down DNA.
- **Viz:** Animated stacked "DNA bar" morphing with the season slider, IPL and WPL as a side-by-side double helix; hover isolates one component's timeline.
- **Teaser:** Six-share of all runs 19.4% → 29.0% (IPL); WPL takes 46.8% of its runs from fours.
- **Lenses:** scoring-environment, landscape-scan, wpl-comparative

---

## 4. Impact & Player Value

### ★ Win Probability Added (WPA) per ball, per player
A ball-by-ball win-probability model (score, wickets, balls, target) whose per-delivery swings are credited to batter and bowler — baseball's WPA with a cleaner two-innings structure. (**Engine layer #3**, with the WP Engine below.)
- **Recipe:** Train WP on all matches: 2nd innings from (runs needed, balls left, wickets left) with monotonicity constraints; 1st innings via P(defend t) × P(reach t | state). **Era adjustment is not optional:** include the season run environment as a feature — identical totals carry wildly different WP by era. WPA(ball) = ΔWP, credited to striker and bowler. Housekeeping verified: 23 D/L to flag, 26 no-winner matches need a tie rule, super overs as separate mini-states.
- **Feasibility:** direct · confirmed
- **Novelty:** known-but-underused
- **Era story:** Aggregate WPA measures whether 2024-26 matches are objectively swingier; plus the definitive Player-of-the-Match audit (how often the award went to the WPA leader, and whether alignment improved).
- **Viz:** The signature interactive: a scrubbable WP worm for any of 1,331 matches with biggest swings flagged; "most valuable ball of each season" gallery; career WPA rivers; a season volatility-index strip.
- **Teaser:** A 170-190 first-innings total was defended 74% of the time in 2008-10 but only 38% in 2023-26 — the same scoreboard lost 36 points of win probability across eras.
- **Lenses:** sabermetric-translation, impact-value, landscape-scan

### ★ Impact Player Natural Experiment (sub-level WPA + IPL×WPL diff-in-diff)
Uses the replacements field (556 impact subs, IPL 2023+ only) plus WPL as a no-treatment control to estimate how much of the post-2023 scoring explosion the rule caused.
- **Recipe:** Parse delivery.replacements.match[]{in, out, team, reason=='impact_player'}: entry over/innings, batting-sub vs bowling-sub (classified by subsequent appearances); runs added by "in" players; share of teams effectively playing 12. Diff-in-diff: IPL pre/post 2023 vs WPL 2023-26 (zero impact subs — clean control, verified). 7 concussion subs as a separate strand. Present as evidence weight, not causal proof (pitches/ball changes coincide).
- **Feasibility:** direct · confirmed (counts verified: 139/137/140/140 by season)
- **Novelty:** novel
- **Era story:** THE rule-change story of the modern IPL: the IPL's run rate was range-bound 7.5-8.7 for 15 seasons, then broke out exactly at the 2023 rule while WPL stayed on a gentle trend; entry-over histograms show teams converging on the optimal sub moment within two seasons — visible strategic learning.
- **Viz:** A match strip where the 12th player literally slides onto the field at the sub moment; aggregate entry-over histogram morphing 2023→2026; IPL-vs-WPL diverging run-rate lines beside it.
- **Teaser:** IPL RR: 8.54 (2022) → 8.99, 9.56, 9.63, 9.88 (2023-26); WPL went only 8.08 → 8.54 — a ~1 RPO diff-in-diff gap.
- **Lenses:** hidden-fields, scoring-environment, impact-value, landscape-scan, wpl-comparative

### Clutch Score / Timing Gap (context-heavy vs context-neutral value)
WPA/LI minus context-neutral linear-weight value — baseball's clutch metric applied to cricket's most romanticized role, with a repeatability test to ask whether finishing is skill or narrative.
- **Recipe:** Per batter-season: Clutch = Σ(WPA/LI) − context-neutral wins (wBRV ÷ runs-per-win); then year-to-year correlation of Clutch across batter-season pairs (baseball's answer: r≈0). Same test on chase-only SR, death-overs splits, RRR-pressure splits (the pressure splits probe cleanly today, before the WP model exists). Ships after WPA/RE — build dependency, not parallel.
- **Feasibility:** direct (post-engines) · confirmed
- **Novelty:** novel
- **Era story:** Cricket batters *choose* aggression ball-by-ball (unlike hitters), so clutch could genuinely be a skill — a more interesting test than baseball's. Era angle: if 2023+ teams hit from ball one, clutch variance should collapse — chase pacing as a dying art. Probe already hints at it: the pressure premium narrowed +16 → +12 SR points.
- **Viz:** "Heart vs hands" quadrant (context-neutral value × clutch), era-animated with famous finishers' career trails; a repeatability panel showing the year-N vs year-N+1 scatter with the correlation displayed like a verdict.
- **Teaser:** Chase SR under pressure (RRR 10+): 132 (2008-10) → 155 (2023-26), while the pressure premium over cruise chases narrowed from +16 to +12.
- **Lenses:** sabermetric-translation, impact-value

### T20 Runs Above Replacement (RAR/WAR)
Player value over a freely-available replacement at the same role, converted to wins via the WP model's own runs-per-win slope — one career-value currency for 19 seasons.
- **Recipe:** Role buckets from observed usage (batters by median entry over; bowlers by phase share). Replacement level per role = 20th percentile RVAE/ball among 100+-ball players — pool rolling 2-3 season windows (per-season death-bowler samples are ~14-23, too thin). WAR = RAR / runs-per-win(era). Expose the contestable choices (percentile, ball floor) as explorer toggles.
- **Feasibility:** derivable · confirmed
- **Novelty:** novel
- **Era story:** Two stories in one: positional scarcity (verified: the death-bowling replacement gap *widened* 0.76 → 1.39 raw RPO — opposite the pitch's hint, pending RVAE normalization) and the runs-per-win exchange rate inflating with scoring — a 2008 run literally bought more win than a 2026 run.
- **Viz:** Career WAR as a stacked-area stock chart overlayable across players and eras; a scarcity dashboard showing replacement level per role drifting season by season.
- **Teaser:** Median-vs-replacement death bowler gap widened 0.76 → 1.39 runs/over (raw economy) between eras.
- **Lenses:** impact-value

### Volatility Premium: boom-bust as option value
Treats innings-to-innings variance as a priced asset — simulating whether an explosive-but-erratic batter wins more matches than a consistent one of equal average impact, per chase context.
- **Recipe:** Per player-season: μ, σ, Gini of per-match RVAE. Monte-Carlo synthetic batter pairs (equal μ, different σ, innings resampled from real state-conditional sequences) through the WP model across chase scenarios; premium(σ, context) = win% difference. **Must be computed on environment-adjusted impact:** raw within-player SD rose 20.5 → 22.4 but CV *fell* 0.826 → 0.805 — batters got bigger, not streakier, in raw terms; frame that divergence as part of the exhibit.
- **Feasibility:** derivable · **adjusted** — most involved build in the impact family (~1 week), reuses all prior layers.
- **Novelty:** novel
- **Era story:** Is franchise selection for boom-bust hitters rational? Theory says volatility is positive-value chasing big totals, negative defending small ones — the simulation prices it. Where does WPL 2026 sit on the volatility curve?
- **Viz:** "Would you rather" simulator: pit a real consistent batter against a real volatile one in a chosen chase, watch 1,000 simulated outcomes rain down as a win/loss dot cascade; era-morphing violins of match impact.
- **Teaser:** Within-player SD of innings runs rose 20.5 → 22.4 while relative volatility (CV) fell 0.826 → 0.805.
- **Lenses:** impact-value

### Player-of-Match Archetype Drift
Joins the ignored player_of_match field with in-match ball-by-ball to classify every award and track what kind of performance wins matches across eras.
- **Recipe:** Per match: PoM's batting line, bowling line, fielding involvements from deliveries; classify batting/bowling/all-round/other. Per season: archetype shares, median runs for a batting PoM, winner-team and chasing-team shares, cheapest awards and priciest snubs. Join verified airtight: 0 of 1,322 PoM names failed to match; every award is single-recipient.
- **Feasibility:** direct · confirmed
- **Novelty:** novel
- **Era story:** Run inflation raised the bar for a batting PoM by 13 runs; is the bowler's share of awards shrinking as the league becomes batter-first? Do Impact Players win awards despite playing half a match?
- **Viz:** Archetype-share streamgraph 2008-2026 with pluckable award "medallions"; a slider game: "would this 2009 performance win PoM in 2026?" scored against era medians.
- **Teaser:** Median runs for a batting Player-of-the-Match: 62 (2008-10) → 75 (2023-26).
- **Lenses:** hidden-fields

### Era-Swap Counterfactual Replay
Replays a classic innings state-by-state under another era's RE and WP surfaces — the identical ball sequence changing meaning as "par" moves.
- **Recipe:** Extract an innings' state sequence; compute ΔRE/ΔWP under the source season's surfaces and a user-chosen target season's; sum for era-conditional innings value and WPA. Chase WP states must use balls-remaining from target.overs (34 D/L-shortened second innings); exclude super overs from surface fitting. Frame honestly as a *valuation* counterfactual, not a simulation of play.
- **Feasibility:** derivable (pure function of the RE/WP engines) · confirmed
- **Novelty:** novel
- **Era story:** Makes inflation visceral: Gilchrist's 2008 hundred was a massive WP swing when par was 160; the same sequence in 2026 is merely a good day — and a 2009 match-winning 45(40) translates to a match-losing anchor job.
- **Viz:** Cinema replay: the innings' WP worm drawn twice on the same axes — own era vs teleported era — diverging in real time as the scrub advances, biggest single-ball meaning-gaps annotated.
- **Teaser:** The same state (over 7, 2 down) was worth 110.3 expected runs-to-come in 2008-10 and 130.8 in 2024-26 — a +20-run par shift repricing every ball.
- **Lenses:** era-machine-regime-detection

### Run Value Above Expectation (RVAE)
Per-ball run value vs the historical expectation for that exact game state, credited plus to the batter and minus to the bowler — the foundation layer most impact metrics build on. (**Engine layer #1b**, the state-baseline table.)
- **Recipe:** State s = (innings, over 0-19, wickets 0-9); baseline E[runs|s] per **rolling 3-season window** (mandatory: per-era-band the grid is thin — 2023-26 populates 165/200 cells with min count 1); empirical-Bayes shrink sparse cells toward *phase means within the window*, not the global surface. Ball value = actual − E; batter RVAE = Σ over balls faced; bowler Runs Saved = −Σ (wides/no-balls at full value). WPL: pool with IPL baselines + league fixed effect.
- **Feasibility:** derivable · **adjusted** (coverage claim corrected as above)
- **Novelty:** known-but-underused
- **Era story:** The baseline surface IS the era — the 20×10 expected-runs grid morphing 2008→2026 shows exactly where scoring inflated; player RVAE then answers who beat their own environment, putting 2008 Sehwag and 2026 hitters on one leaderboard.
- **Viz:** Animated 20×10 heatmap (over × wickets, color = expected runs/ball) with a season scrubber; player overlay showing which cells of the surface they harvest value from.
- **Teaser:** First-innings death-over expected runs per legal ball: 1.72 (2008-10) → 1.91 (2023-26) — the baseline itself inflated 11%.
- **Lenses:** impact-value, landscape-scan

### Leverage Index (LI) for T20
How much a given ball can swing the match — expected |ΔWP| at that state, normalized to league mean 1.0 — tagging every delivery in history with how much it mattered.
- **Recipe:** LI(s) = E[|ΔWP|] over the empirical outcome distribution at s, ÷ league mean; precompute on the state grid, join to all 295,557 balls (count verified). Byproducts: per-match LI traces, per-player LI faced/bowled, league share of balls above LI 2.0. Pure post-processing of the WP + RVAE layers — a day of work once WPA exists.
- **Feasibility:** derivable · confirmed
- **Novelty:** known-but-underused
- **Era story:** Has the drama moved? Early-IPL leverage concentrated in death overs of tight chases; the proxy suggests leverage is decompressing away from the endgame in the high-scoring era. WPL's leverage profile (front-loaded via early collapses?) is untested territory.
- **Viz:** The match as an EKG: LI as a heartbeat strip under the WP worm — flatlines and spikes at a glance; season small-multiples of the league's collective heartbeat changing shape over 19 years.
- **Teaser:** Decided chases still alive in the 20th over: 59.5% (2008-10) vs 55.3% (2023-26).
- **Lenses:** impact-value

### Captain's Trust / Fireman Index (leverage-weighted ace deployment)
Who gets handed the ball when the match hangs: each bowler's mean leverage faced and share of the team's highest-stakes balls, paired with whether the trust paid off.
- **Recipe:** Per bowler-season: mean LI over balls bowled + share of team's top-decile-LI deliveries (deployment), paired with WPA per high-LI ball (payoff); team-level leverage-share matrix reveals hierarchy. Caveat: first-innings LI needs the par/projection model — budget for it or restrict v1 to second innings, where leverage is best defined.
- **Feasibility:** derivable · confirmed — cleanest new-information-per-effort ratio in the tactics family: deployment is a revealed-preference signal no scorecard stat captures.
- **Novelty:** novel
- **Era story:** Tactical evolution as revealed preference: when did captains start trusting spinners with high-leverage powerplay overs, when did the death specialist crystallize, and do WPL captains distribute leverage differently?
- **Viz:** Per-team "trust network": bowlers as nodes sized by mean leverage faced, hierarchies forming and collapsing after failures across a season; era scrubber shows specialist roles crystallizing league-wide.
- **Teaser:** Proxy: the most-trusted bowler's share of his team's death-over balls rose 44.5% → 46.8%; WPL captains spread it thinner at 43.1%.
- **Lenses:** impact-value, bowling-evolution, sabermetric-translation

### Composite Impact Score (bat + bowl + field in one WPA ledger)
One number per player-match denominated in win probability: batting + bowling WPA plus fielding credit carved from each dismissal's WP swing.
- **Recipe:** Fielding credit from wickets[].fielders (inventory verified exactly: 9,310 caught, 1,185 run out, 388 stumped, 410 c&b): split ΔWP 70/30 bowler/fielder for catches and stumpings, 100% to run-out fielders, 100% bowler for c&b. Zero unnamed fielders in the current dump; substitutes explicitly flagged (optionally exclude). Season score = Σ WPA rescaled 0-100. Validation: regress player_of_match on component WPAs to expose voter bias. State the blind spot honestly: no drops or saves — converted chances only.
- **Feasibility:** derivable · confirmed
- **Novelty:** known-but-underused
- **Era story:** A 19-season MVP timeline on one scale, plus the bias audit; fielding-involved dismissals rose 73.0% → 76.9% of wickets — fielding's raw share of impact is growing. WPL MVP arcs render on the identical scale.
- **Viz:** Season MVP race as an animated bump chart; each player-match a "DNA strip" of colored ticks (bat/bowl/field events sized by WPA) — a match-winning spell reads visually different from a quiet fifty.
- **Teaser:** Fielding-involved dismissals: 73.0% → 76.9% of all wickets (8.79 → 9.32 per match).
- **Lenses:** impact-value

### Impact Index (Jaideep Varma school): share-of-match relative rating
Rates each performance relative to the other 21 players in the same match, weighting tournament-deciding games higher — self-normalizing across eras by construction.
- **Recipe:** Player context-valued output as a share of the match's total output, normalized so the match average = 1; career = mean with a knockout multiplier (event.stage verified on knockouts in every season — normalize 'Semi Final' vs 'Qualifier' labels). Weight the thin fielding component lightly or omit.
- **Feasibility:** derivable · confirmed
- **Novelty:** known-but-underused
- **Era story:** Big-match temperament across eras — and a verified structural finding: the top performer's share of match output fell 16.3% → 14.4%, i.e. IPL matches are measurably less of a one-man show than they used to be.
- **Viz:** Tournament bracket view where each knockout glows by its highest individual impact; the all-time list visibly reshuffles when the knockout multiplier toggles.
- **Teaser:** The match's top performer captured 16.3% of total output in 2008-12 vs 14.4% in 2023-26.
- **Lenses:** landscape-scan

### Award Bias Audit (Smart MVP vs actual awards)
Ranks every season by the project's impact metrics and diffs against actual PoM awards and Orange/Purple Caps to expose systematic award bias.
- **Recipe:** Per-match impact leader vs info.player_of_match (present everywhere; exclude 5-9 no-result misses); per-season WPA leaders vs raw run/wicket leaders; quantify bias directions (toward batters, first-innings centuries, winning teams; against death bowlers). Needs the impact engine — the PoM-vs-top-scorer pilot runs today.
- **Feasibility:** derivable · confirmed
- **Novelty:** known-but-underused
- **Era story:** Has award judgment improved as analytics went mainstream? The bias magnitude per season is itself an era curve; do WPL awards (born in the analytics age) show less bias than early IPL's?
- **Viz:** "Robbed" hall of fame: per season, the actual award photo-frame beside the metric's pick with the gap quantified; a bias-direction compass per era.
- **Teaser:** The PoM was simply the match's top run-scorer in 50.9% of 2008-10 games but only 41.7% of 2023-26 games.
- **Lenses:** landscape-scan

### Era-Relative Z-Ledger (regime-normalized leaderboards)
Every player-season stat re-expressed as a z-score within its detected regime — cross-era dominance leaderboards plus adaptation scores for careers straddling regime breaks.
- **Recipe:** Pool player-seasons within each Seismograph regime; robust z (median/MAD, min ~125 balls) for SR, boundary%, economy, dot% per phase. Dominance = career-best/average z; adaptation score for break-straddlers = post-break z − pre-break z, net of a career-year aging prior (no birthdates needed).
- **Feasibility:** direct · **adjusted** — marquee example corrected: 2013 Gayle (z +1.90) is third-tier in his own season; the poster child is **2011 Gayle (SR 183 vs season median 122, z +5.54)**, which does outrank the modern outliers (2024 Fraser-McGurk z +5.22, 2026 Suryavanshi z +4.43, 2015 Russell z +5.39).
- **Novelty:** known-but-underused
- **Era story:** Settles cross-era arguments in regime-aware units, and names the great adapters — whose games survived the 2023 break vs stars the new regime stranded.
- **Viz:** Leaderboard with an era-normalization toggle — flip it and ranks reshuffle with animated transitions; career-river charts shade regime backgrounds; an "adaptation" badge marks players whose river rises across a fault line.
- **Teaser:** Era-normalized, 2011 Gayle (z +5.54) edges 2024 Fraser-McGurk (z +5.22) despite a raw SR 51 points lower.
- **Lenses:** era-machine-regime-detection

### Auction Value-for-Money (price per impact run) *(needs-external-data)*
Joins auction prices to derived impact value: rupees per WPA point, tracking market efficiency across auctions.
- **Recipe:** Join Kaggle "IPL Player Auction Dataset" (2013+), OpenDataBay lists, or iplt20.com results to registry IDs. Verified complication: Cricsheet uses initial-style names ('V Kohli') vs auction datasets' full names — fuzzy match on name + season-team (duplicate-surname collisions exist). Metric: price / delivered impact; residuals = over/underpays; model what the market actually buys (raw SR vs true SR).
- **Feasibility:** needs-external-data (sources named above; retention prices and pre-2013 patchy) · confirmed
- **Novelty:** known-but-underused
- **Era story:** Did the market get smarter? If price correlates increasingly with context-adjusted metrics, franchises learned analytics; the death-specialist premium and post-2023 all-rounder discount should be visible in prices.
- **Viz:** Value frontier scatter (price vs delivered impact) per auction year with over/underpay zones; "moneyball moments" annotated.
- **Teaser:** (none without the join)
- **Lenses:** landscape-scan

### Win Probability Engine (WinViz / Forecaster class) *(table-stakes)*
Ball-by-ball P(batting team wins), recomputed after every delivery — the foundational engine most other impact metrics sit on. (**Engine layer #3.**)
- **Recipe:** Per delivery: innings, balls remaining, wickets in hand, runs/needed + RRR, venue mean, season; label with eventual winner; GBM/logistic on ~290k IPL balls; season-windowed models (rolling ~4 years) rather than one pooled model; WPL via IPL model + calibration offset (88 matches too few standalone). Flag D/L; use target.overs for shortened chases.
- **Feasibility:** derivable · confirmed. **Novelty:** table-stakes — but the era-specific twist (same state, different era) is the differentiator.
- **Era story:** 60 off 36 with 5 down was a coin-flip in 2010 and comfortable in 2025 — era-specific models make that drift measurable.
- **Viz:** Scrubbable WP worm for any match with an "era ghost" overlay: what the 2010-trained model would have said at each ball of a 2025 match.
- **Teaser:** Chases needing 9+ RPO with 60 balls left: won 24.3% (2008-12) vs 31.8% (2023-26) — +7.5 WP points for the same state.
- **Lenses:** landscape-scan

---

## 5. Tactics, Rules & Team Strategy

*(Note: Captain's Trust / Fireman Index, a tactics idea, is filed in Section 4 with its LI dependencies.)*

### ★ DRS Review Economics
Treats each team's DRS reviews as bets and scores their gambling discipline: success rate, umpires-call burn, batting vs bowling splits, and what doubling the allowance did.
- **Recipe:** Per review{by, decision, umpires_call, batter}: reviewing side = review.by (infer batting/bowling vs the innings team — review.type is unreliable, present on only 540/990); per team-season: reviews taken, upheld%, umpires_call% (140 tagged — verify season coverage, likely truncated), phase taken, "desperation index" (share in last 4 overs); track the allowance-doubling jump (avg 76/season 2018-21 → 137 from 2022). review.batter enables a "review magnet" sub-metric.
- **Feasibility:** direct · confirmed (988 IPL reviews, 29.6% upheld; WPL 203, 30.5%)
- **Novelty:** novel
- **Era story:** Eight seasons of review strategy: did teams get better at reviewing, did doubling the allowance make them looser gamblers (verified: volume nearly doubled, accuracy didn't budge), and are WPL captains already as calibrated as IPL captains? (Strikingly: yes — 30.5% vs 29.6%.)
- **Viz:** Casino-table interface: each team-season a chip stack; bets resolve green (upheld) or red (struck down) as you scrub time; a "house edge" line tracks the league struck-down rate.
- **Teaser:** Teams review like identical gamblers across leagues: IPL 29.6% upheld vs WPL 30.5% — and doubling the allowance in 2022 nearly doubled volume without improving accuracy.
- **Lenses:** hidden-fields, bowling-evolution, landscape-scan, team-tactics-meta

### Spell Fragmentation & Bowling-Change Entropy (captaincy fingerprint)
Each innings' bowler sequence as a string: spell fragmentation, bowling-change entropy, and matchup micro-management as an evolving captaincy style.
- **Recipe (corrected):** Spells must be defined **per bowling end** (alternating even/odd over-index subsequences) — the naive "consecutive overs" definition returns 100% one-over spells because the laws forbid consecutive overs. Then: spell-length distribution, 1-over-spell share, distinct bowlers, Shannon entropy of over-to-over transitions, death-over allocation Gini; cluster team-season profiles. Mid-over changes negligible (0.12%).
- **Feasibility:** direct · **adjusted**. Captain attribution needs external data; team-season level doesn't.
- **Novelty:** novel
- **Era story:** The analytics arms race from the bowling side: rhythm-based captaincy (bowl your four straight) dissolving into matchup chess — with the verified surprise that **WPL is MORE fragmented than the modern IPL**, flipping the pitched question into a headline.
- **Viz:** Innings as a 20-square mosaic strip colored by bowler, stacked by season — long same-color runs in 2008 dissolving into confetti by 2026; a fragmentation ticker per season.
- **Teaser:** Same-end 1-over spell share: 54.7% (IPL 2008-10) → 64.1% (2023-26) — and 75.3% in WPL.
- **Lenses:** creative-structures, bowling-evolution, team-tactics-meta

### Rule-Change Event Study with Placebo Cursor
Interrupted time-series (RD-in-time) around documented rule changes — Impact Player foremost — estimating the causal jump against a distribution of placebo dates.
- **Recipe:** Local linear trends either side of a candidate date on the per-match series; placebo distribution from re-running at every fake date. Mechanism metrics from replacements ('match'-type only: 133/128/140/142 for 2023-26; exclude 'role'-type injury subs back to 2008) and review (2018+) for the DRS/lbw study. Batting position from first appearance on strike.
- **Feasibility:** direct · **adjusted** — headline mechanism reversed in the naive cut: positions 6-8 SR rose +11.0% (2021-22 → 2023-24) but the top 3 rose MORE (+13.0%). The finding becomes "aggression licensed at the top, not the tail"; the placebo machinery works regardless of sign.
- **Novelty:** novel
- **Era story:** Decomposes the 2023-26 explosion: how much is the rule vs secular intent drift already visible in the 2018 six-rate break.
- **Viz:** A draggable placebo cursor: drag the "intervention date" anywhere and the discontinuity estimate re-fits live; the true rule date pops out of the gray placebo cloud; a mechanism panel lights up at the cursor.
- **Teaser:** Positions 6-8 SR: 131.5 → 145.9 after the rule; positions 1-3: 131.0 → 148.0 — the top order took the license.
- **Lenses:** era-machine-regime-detection

### Batting-Order Fluidity & Entry-Position Entropy
Each player's entry-position entropy and each team's lineup fluidity per season, with 2023's Impact Player rule as a natural experiment in structural flexibility.
- **Recipe:** Batting position from order of first appearance; per player-season: entropy of position distribution, entry-ball variance; per team-season: mean lineup edit-distance between consecutive orders; replacements usage (filter by era/type — the field is NOT 2023-only: 2-5 injury 'role' subs/season exist back to 2008). Interrupted time-series 2019-22 vs 2023-26 with WPL as control.
- **Feasibility:** direct · **adjusted** — probe caution: entry-position entropy is FLAT across the rule change (1.122 → 1.095; WPL 0.944).
- **Novelty:** novel
- **Era story (corrected):** Pitch as a natural experiment whose headline may be the surprising null: the rule added a 12th name **without rewiring batting-order thinking**. Substitution timing/usage analysis stays rich (see Playbook Decoder).
- **Viz:** Alluvial ribbons per team: players weaving between batting positions across a season — taut parallel lines vs braided chaos — plus an Impact-Player substitution timeline.
- **Teaser:** Impact Player subs in ~100% of IPL matches since 2023 (289/292) vs 1 WPL match ever — yet entry entropy barely moved (1.12 → 1.10).
- **Lenses:** creative-structures, team-tactics-meta

### Part-Timer Extinction & the Impact-Player Bowling Dividend
The share of overs bowled by non-frontline bowlers per season, and whether the 2023 rule killed the part-time over for good.
- **Recipe:** Per team-season, frontline = top 5 by overs; filler share = everyone else's %; distinct bowlers per innings; % of innings needing a 6th/7th bowler. **Correction:** replacements is delivery-level with schema {match:[{in,out,team,reason}]} — no role[] key; identify bowling subs by whether the "in" player bowls after the sub delivery.
- **Feasibility:** derivable · **adjusted**
- **Novelty:** novel
- **Era story:** Two regime changes in one metric: professionalization squeezed the Yuvraj/Raina filler over through the 2010s (30.6% → 26.3%), then 2023 *added* a bowling option — bowlers/innings jumped 5.78 → 6.09 the year the rule arrived. WPL (no rule) uses even more (6.27): a depth-structure contrast.
- **Viz:** Stacked area of overs share by bowler-rank (1st-8th choice) with a bold 2023 annotation band; an "endangered species" panel listing each season's last true part-time overs.
- **Teaser:** Filler share 30.6% → 26.3%, yet bowlers-per-innings jumped 5.78 → 6.09 in 2023; WPL: 6.27.
- **Lenses:** bowling-evolution

### Matchup Engineering Score
How often captains bring on the bowler with the best historical head-to-head against the striker — an analytics-adoption index computed entirely from the data itself.
- **Recipe:** Rolling no-lookahead h2h table (only deliveries before the match date); at each bowling change, score the chosen bowler's matchup vs the best available alternative (define "available" explicitly: XI members who bowl that match or ≥10% of team-season overs; quota + previous-over constraints derivable). Team-season score = share of changes in the top matchup tercile; also reactive "matchup pulls" after a new batter arrives. **Empirical-Bayes shrinkage is core, not optional:** only 12% of balls in 2009 had a 12-ball h2h history, peaking 42% (2019), diluted to ~32% post-expansion.
- **Feasibility:** derivable · **adjusted** — heaviest self-contained build in the tactics family; pre-2012 curve will be mostly prior-driven (say so honestly).
- **Novelty:** novel
- **Era story:** The rise of the team analyst made flesh: if the score is flat 2008-2015 then climbs after ~2016-18, the data itself dates the analytics revolution; team curves name early adopters; WPL tests whether new franchises were born analytical.
- **Viz:** Live "captain's decision" replay: at each bowling change, the option board (available bowlers ranked by matchup) with the actual pick highlighted — right calls glow, misses flash; the adoption S-curve is the marquee chart.
- **Teaser:** The raw material itself evolved: 12% of balls had 12-ball h2h history in 2009, 42% by 2019, ~32% in 2024-26.
- **Lenses:** bowling-evolution

### Tail Exposure Rate *(lineup-tactics)*
How often positions 8-11 actually bat, and whether the Impact Player era let top orders swing without fear of exposing the tail.
- **Recipe:** From derived positions: share of full first innings where position 8+ faced a ball; mean tail balls; top-3 SR conditioned on exposure. **Mechanism correction:** exposure is FLAT across eras (59.9% → 58.2% → 58.3%) — drop "exposure fell" as mediator; the Impact Player safety net is about tail *quality* (the sub makes No. 8 a real batter). Mediate the diff-in-diff on tail run-scoring ability instead.
- **Feasibility:** derivable · **adjusted**
- **Novelty:** novel
- **Era story (corrected):** Exposure held constant while top-3 aggression spiked (SR 131 → 155 from 2021-22 to 2023-26) — batters swing harder without the tail batting any more often. WPL as partial control.
- **Viz:** "Safety net" visual: an innings depth chart where positions 8-11 glow when exposed; the net's *quality* rises while a top-order strike-rate flame grows.
- **Teaser:** Top-3 SR jumped 131 (2021-22) → 155 (2023-26) while tail exposure stayed flat at ~58%.
- **Lenses:** team-tactics-meta

### Franchise Convergence Index (tactical fingerprints) *(franchise-identity)*
A per-franchise-season tactical DNA vector — does CSK really play differently, and is the league's meta converging into one strategy?
- **Recipe:** 10-12 dimensions per franchise-season assembled from other metrics (PP intent, death Gini, order entropy, bowling-change reactivity, field-first rate, review overturn, sub timing, wickets risked...), z-scored within season (kills era inflation). Convergence = mean pairwise distance per season; identity persistence = autocorrelation of a franchise's vector across seasons; hierarchical clustering + PCA projection; WPL teams enter the same space. Franchise alias table required.
- **Feasibility:** derivable · confirmed — but a 4-dim probe found only mild convergence (2.93 → 2.83), so validate the "galaxy collapsing" visual on the full vector before promising it; the identity-persistence angle may carry the piece.
- **Novelty:** novel
- **Era story:** Early IPL had distinct schools (CSK stability, RCB star-batting, RR moneyball); does analytics kill tactical diversity — and do WPL teams land inside modern IPL's cluster (meta imported wholesale) or not?
- **Viz:** Animated 2D "meta galaxy": each franchise a glowing node with a radar tooltip, drifting season by season; CSK's orbit trail highlighted to answer the fan question directly.
- **Teaser:** 4-dim probe: mean pairwise tactical distance 2.93 (2008-10) → 2.83 (2023-26) — mild convergence, pending the full vector.
- **Lenses:** team-tactics-meta

### Post-Defeat Panic Index
How many more XI changes a franchise makes after a loss than after a win — a measurable knee-jerk coefficient across eras.
- **Recipe:** For consecutive same-season fixtures: changes = players dropped from previous personnel, conditioned on prior result; panic = mean(changes|loss) − mean(changes|win); control for stage and rest days. Corrections: recover true XIs from 12-13-name Impact-era lists (or use the dropped-players measure — the differential survives either way); derive season from dates, not the '2020/21' label. Injury vs choice can't be split, but injuries are outcome-independent and cancel in the differential.
- **Feasibility:** derivable · confirmed
- **Novelty:** novel
- **Era story (verified surprise):** absolute churn declined ~20% but the knee-jerk differential did NOT budge — teams got calmer overall yet still panic exactly as much after losses. Professionalization of management, half-achieved.
- **Viz:** Butterfly chart per franchise: left wing = changes after wins, right = after losses, animated by season; league leaderboard of "coolest head" vs "itchiest trigger finger."
- **Teaser:** 2.32 changes after a loss vs 1.39 after a win in 2008-10 (panic +0.92); 2.03 vs 1.10 in 2023-26 (panic +0.94).
- **Lenses:** career-arcs-cohorts-roster-churn

### Dead-Rubber Laboratory
Flags matches where playoff fates are sealed and measures whether teams learned to use them as auditions — debutants, XI shuffles, fringe-bowler overs.
- **Recipe:** From the Must-Win standings replay, tag dead rubbers (leverage < 0.02 both teams — strict both-dead rubbers number only ~9, so use soft leverage or one-team-dead matches, ~86 available). Experimentation index: never-before-seen players, XI diffs, non-top-5 bowler overs, batting-order displacement. **Confound control:** compare dead vs live within the same final-fortnight window (late matches mechanically have fewer possible new faces).
- **Feasibility:** derivable · **adjusted**
- **Novelty:** novel
- **Era story:** 2008-era teams fielded full-strength XIs in meaningless games; modern franchises convert them into talent labs — and the 10-team format produces more dead rubbers, earlier.
- **Viz:** "Graveyard shift" panel: the season timeline with dead rubbers as dimmed tombstone ticks, each expanding into a before/after XI diff showing who got their audition.
- **Teaser:** Matches with an already-eliminated team produced 0.97 fresh season-debuts per game in 2020-26 vs 0.35 in 2014-19 — near-3× more end-of-season auditioning.
- **Lenses:** schedule-calendar-fatigue

### Rare Dismissals Museum
A curated timeline of the schema's exotic events — retired out, obstructing the field, hit wicket, penalty runs, the double super over — as era-marking artifacts.
- **Recipe:** Scan for retired out (IPL 6, all 2022+; WPL 2, both 2026), obstructing (4), hit wicket (20), retired hurt (19), penalty runs (2 ever), super overs (**17 matches / 36 innings** — corrected from 16/34; the arithmetic confirms 2020's double super over), D/L (23). Pull full ball context per exhibit.
- **Feasibility:** direct · confirmed — every count verified against the corpus.
- **Novelty:** novel
- **Era story:** Retired-out went from unthinkable to a repeated tactical tool within four seasons — the sharpest example of T20 optimization eroding cricket taboos; the WPL adopted it *faster* than the IPL did.
- **Viz:** Scrolling "cabinet of curiosities": each rare event an exhibit card on a 2008-2026 shelf timeline with ball-by-ball context on hover; the empty shelves before 2022 make the retired-out cluster visually loud.
- **Teaser:** Retired out: zero in the IPL's first 14 seasons, then 6 in the five seasons since 2022 — and the WPL logged 2 by its fourth season.
- **Lenses:** hidden-fields

### Impact Player Playbook Decoder *(rule-change)*
When, why, and with what effect teams deploy the Impact Player sub (2023+): timing, role swapped, and the win-rate payoff of each pattern.
- **Recipe:** Parse impact_player replacements (557 records; ~1.9/match — both teams nearly every match): team, in/out, innings, over of the carrying delivery. Classify batting- vs bowling-reinforcement by subsequent appearances (verified split: 288 bat / 208 bowl / 34 both / 27 unused). **Timing correction:** Cricsheet attaches the record at *activation*, so "named at toss" vs tactical is inferred from the activation point (zero at innings-1 ball 1; 42.7% at the innings break; rest mid-innings). Cross-tab pattern × toss × result; depth effect on positions 6-8.
- **Feasibility:** direct · confirmed
- **Novelty:** known-but-underused
- **Era story:** The biggest structural rule change in IPL history, with every use recorded: the meta moved off the innings break as teams learned to hold the sub for mid-innings strikes.
- **Viz:** Decision-tree Sankey: toss → innings → sub timing → sub role → outcome, flows animating season by season as the league learns the rule.
- **Teaser:** 53% of 2023 subs happened at the innings changeover, falling to 35% by 2025 — teams learned to hold the card.
- **Lenses:** team-tactics-meta

### Must-Win Meter
Recomputes live standings (points + NRR from ball-by-ball) before every match to tag its playoff leverage, then measures how behavior warps under elimination pressure.
- **Recipe:** Chronological standings replay (2-point wins incl. super-over results via outcome.eliminator, 1 for NR; NRR with all-out-counts-as-full-quota, target.overs for reduced games; stage labels disambiguate 2008-10 semifinal rules vs 2011+). Leverage = P(playoffs|win) − P(playoffs|loss) by Monte Carlo over remaining fixtures — **the MC soft-leverage tagging is what makes the sample usable** (strict mathematical elimination gives only ~76 matches in 19 seasons). Condition dot rates, PP aggression, bowling-change entropy, review usage on leverage tercile.
- **Feasibility:** derivable · confirmed (simplified replay engine already proven in ~40 lines)
- **Novelty:** known-but-underused
- **Era story:** Did data-era franchises learn to play elimination games exactly like dead ones? Plus a found gem: dead teams punch harder in the squad-depth era.
- **Viz:** Stakes-tinted fixture timeline: each season a ribbon of match ticks from grey (nothing at stake) to red-hot (elimination); hover reveals the live table that morning; a toggle overlays chase aggression where the ribbon burns.
- **Teaser:** Eliminated teams beat still-alive opponents 35.3% of the time in 2014-19 but 41.9% in 2020-26.
- **Lenses:** schedule-calendar-fatigue

### Chase Pacing Portraits (front-loaded vs back-loaded chase control)
Trajectories of chases in (required rate × wickets in hand) space, separating won vs lost paths — the arXiv higher-order-Markov chase line of work.
- **Recipe:** Per second innings: (RRR, wickets) at each over boundary; overlay trajectories by outcome; era-specific "safe frontier" = max RRR from which >50% of chases succeed, by wickets and overs left. Filter target.overs==20 (DLS handled separately), exclude super overs, RRR uses total runs incl. extras.
- **Feasibility:** derivable · confirmed — era-binned frontier samples healthy.
- **Novelty:** known-but-underused
- **Era story:** The chaseable frontier's outward march: 10-an-over at halfway was a lost cause in 2010 and is live in 2025 — the behavioral echo is the toss revolution.
- **Viz:** Phase-space "wind map": flow arrows showing where chases in each state tend to go next, the win frontier as a moving coastline across eras.
- **Teaser:** Chases needing 10+ RPO at halfway: won 15.7% (2008-10, n=51) vs 24.4% (2023-26, n=172).
- **Lenses:** landscape-scan, team-tactics-meta

### Pressure Index (chase pressure per ball)
Per-ball pressure on the chasing side from required-rate gap and resources remaining — the Mallawa Arachchi / Bhattacharjee academic lineage, implementable directly.
- **Recipe:** Pressure(ball) = f(RRR/initial RR, wicket resources, balls remaining), recursively smoothed per the published papers; aggregate "pressure faced" and SR conditional on pressure quartile per batter. **Normalization by initial required rate is essential** — raw RRR thresholds are era-confounded by scoring inflation.
- **Feasibility:** derivable · confirmed — target present in 100% of second innings checked, D/L included.
- **Novelty:** known-but-underused
- **Era story:** What fraction of chase balls are faced under high pressure, 2008 vs 2026? Do WPL chases carry more pressure per ball (closer games)?
- **Viz:** Chase replays with a pressure gauge glowing behind the worm; an "ice-vein index" leaderboard of batters whose true SR rises with pressure quartile.
- **Teaser:** Share of chase deliveries at RRR ≥ 10: 30.5% (2008-10) vs 53.3% (2023-26); WPL 36.3% — more than half of every modern chase happens above ten-an-over.
- **Lenses:** landscape-scan

### Unspent Resources Index *(resource-strategy)*
How many runs first-innings teams leave in the shed by finishing with wickets in hand — quantifying the death of wicket-preservation.
- **Recipe:** (a) Mean first-innings wickets lost per season; (b) regression of total on wickets lost with season/venue fixed effects — the era-specific price of risk; (c) rolling-window R(balls, wickets) resource table; unspent = R at the endpoint; (d) correlate unspent resources with loss probability. Exclude rain-shortened innings.
- **Feasibility:** derivable · **adjusted** — the expected trend was factually wrong: wickets lost is **U-shaped** (6.81 in 2008 — the series max — falling to 5.77 in 2012, back to 6.2-6.4 in 2023-26). That strengthens the case for the full resource table: 2008's spend was involuntary (skill), 2024's is voluntary (intent) — only the exchange-rate regression disambiguates.
- **Novelty:** known-but-underused
- **Era story:** "Intent" ideology as a price chart: same wicket spend, opposite reasons.
- **Viz:** "Fuel gauge" innings replay: balls drain the tank while wicket-fuel burns; end-of-innings unspent fuel pools into a season reservoir that shrinks 2008 → 2026.
- **Teaser:** First-innings wickets lost: 6.81 (2008) → 5.77 (2012) → 6.4 (2024) — U-shaped, not monotonic.
- **Lenses:** team-tactics-meta

### Home Fortress Erosion Index *(home-advantage)*
Home-team win rates by season and venue — testing whether scouting, data, and player churn dissolved home advantage.
- **Recipe:** Hardcoded ~19-row franchise → home city table (add secondary homes: Dharamsala/Indore, Guwahati, Visakhapatnam); "home" if city matches and season isn't neutral-hosted (exclude 2009, 2020, 2021 legs — the exactly-one-home-team filter gracefully handles 2014/2022 too). Per season: home win% with CIs; per franchise: home-minus-away differential; fortress decay at Chepauk/Eden over rolling windows; interaction with toss.
- **Feasibility:** derivable · confirmed (45-68 qualifying matches most seasons)
- **Novelty:** known-but-underused
- **Era story:** Fortress tactics defined early IPL; mega-auction churn and universal data scouting flattened the edge — to below coin-flip. Did WPL, with shared grounds, ever have home advantage at all?
- **Viz:** An India map of fortresses whose castle icons crumble or fortify per season; clicking Chepauk shows its home win% timeline with CSK-era annotations.
- **Teaser:** Home teams won 55.0% of matches in 2008+2010 but 47.6% in 2023-26 (n=248) — the fortress is now statistically a road game.
- **Lenses:** team-tactics-meta

### Lineup Simulator (batting-order & bowling-plan optimization)
A Monte-Carlo match simulator on phase-based player profiles with James-Stein shrinkage (arXiv 2604.13861 approach), turned into an interactive what-if toy.
- **Recipe:** Per player per phase: outcome distribution over {0,1,2,3,4,6,W} shrunk toward role means (**shrinkage is load-bearing:** 54% of 2025 batter-phase cells have <30 balls); simulate ball-by-ball with matchup-adjusted draws; evaluate lineup permutations or cross-era fantasy fixtures; era-condition the environment (wides rate, boundary payoff) from season baselines; model 2023+ depth via replacements.
- **Feasibility:** derivable · confirmed — heaviest build in the catalog, but nothing blocks it.
- **Novelty:** known-but-underused
- **Era story:** Cross-era exhibition matches — 2008 Rajasthan Royals vs 2024 KKR under 2024 physics — makes era evolution *playable* rather than just chartable.
- **Viz:** Drag-and-drop lineup builder; hit simulate and watch 1,000 worms bloom into an outcome distribution; an era dial changes the physics of the whole match.
- **Teaser:** The "era physics" the dial changes: six rate 4.27% → 7.64% of legal balls, dot rate 37.4% → 32.8%.
- **Lenses:** landscape-scan

### Platoon Polarity: Handedness × Bowling-Style Matchups *(needs-external-data)*
Baseball's L/R platoon analysis for batter-vs-bowler-type matchups, and how ruthlessly teams exploit them in bowling changes and batting-order design.
- **Recipe:** Join batting hand + bowling style onto registry IDs (verified gap: nothing in the match files; verified path: Cricsheet people.csv → ESPNcricinfo profile pages, ~700 IPL + ~150 WPL players, one-time). Then: linear-weight run value per matchup cell per era with shrinkage; team exploitation index (post-wicket bowling flips to the batter's weak matchup vs random-rotation baseline); batting-order L/R alternation rate.
- **Feasibility:** needs-external-data (source: ESPNcricinfo via Cricsheet people register / cricketdata) · confirmed — everything downstream is direct after the join; the degraded no-join proxy is not recommended.
- **Novelty:** known-but-underused
- **Era story:** The rise of matchup cricket: when did the exploitation index inflect (hypothesis: post-2018 analytics departments), does left-arm pace's edge survive shrinkage, and do WPL teams exploit matchups at 2026-IPL levels from day one?
- **Viz:** A matchup chessboard (batter types × bowler types, colored by run value) with a season scrubber; team "matchup discipline" gauges; lineups as L/R beads showing alternation strategy evolve.
- **Teaser:** (none without the join)
- **Lenses:** sabermetric-translation, creative-structures

---

## 6. Match Dynamics & Structural Analytics

### ★ Death of the Sighter: Survival Analysis of the Individual Innings *(survival-analysis)*
Kaplan-Meier survival and hazard-of-dismissal curves indexed by the batter's own ball count, stratified by era — the rigorous version of "getting your eye in."
- **Recipe:** Per batter-innings: legal deliveries faced (wides excluded, no-balls counted), event = dismissal, censored if not out; KM per era band and league; discrete hazard h(b); Cox/logistic extension with entry over, wickets down, RRR, position. Censor 'retired hurt' (10 cases) AND 'retired out' (5, tactical — censor too); run-outs attribute via player_out.
- **Feasibility:** direct · confirmed — **the strongest single finding of the whole verification batch.**
- **Novelty:** known-but-underused
- **Era story:** The scoring ramp exploded while early-innings hazard stayed flat — modern batters attack from ball one at NO extra dismissal risk. That is skill evolution, cleanly separated from risk appetite. WPL's curves test whether the women's league entered at the 2023 hazard shape or is recapitulating IPL history at fast-forward.
- **Viz:** Layered hazard curves morphing under an era slider with 2008's ghost always visible; hover any ball number to see which real batters most defied that hazard.
- **Teaser:** First-10-ball SR jumped 108.0 → 135.3 while per-ball dismissal hazard on those balls stayed flat (5.04% vs 4.93%); WPL's 110.5 sits at IPL-2008 intent.
- **Lenses:** creative-structures

### ★ Duel Network (shrunken batter-bowler matchup matrix and rivalry graph) *(network-structure)*
A temporal bipartite graph where every batter-bowler pairing is an edge weighted by balls, runs, dismissals, and dominance — who owns whom, and how rivalry structure evolved.
- **Recipe:** Accumulate edges on registry IDs (verified stable across seasons): legal balls, runs.batter, bowler-credited dismissals only (bowled/caught/lbw/stumped/c&b/hit wicket); dominance = empirical-Bayes-shrunk SR-vs-expected + dismissal rate vs baseline; rivalry intensity = balls × closeness × distinct seasons recurring. One graph per season + cumulative; Louvain communities, degree/density trends. Exclude super overs (34).
- **Feasibility:** direct · confirmed — full 31,355-edge list built from all 1,243 matches in ~30s; 235 duels span 8+ seasons.
- **Novelty:** known-but-underused
- **Era story:** Watch the graph densify and churn: imported-star vs domestic-bowler edges of 2008-12, spin-vs-top-order edges post-2018, decade-long duels persisting through franchise churn. Overlay WPL's 3-season graph on IPL-2010's at the same age: how fast does a league's rivalry structure crystallize?
- **Viz:** Force-directed graph with a season scrubber: edges glow by dominance direction (batter-red vs bowler-blue); click an edge for a ball-by-ball duel replay strip; a "longest-running duels" hall-of-fame filter.
- **Teaser:** The longest-running duel is Kohli vs Jadeja: 160 balls across 14 seasons (179 runs, 3 dismissals); Kohli vs Ashwin ran 149 balls across 13 seasons with 1 dismissal.
- **Lenses:** creative-structures, landscape-scan

### Entropy Engine: The Predictability of Scoring Sequences *(information-theory)*
Shannon entropy of per-ball outcome distributions and Markov next-ball conditional entropy — has T20 collapsed into predictable boundary-or-dot cricket?
- **Recipe:** Encode deliveries as symbols {0,1,2,3,4,6,W,extra} (W-precedence, legal balls); per season/team/player (≥100-120 balls): H, first-order Markov H(next|current), predictability gain; entropy-vs-run-rate scatter; phase-normalize so era shifts aren't phase-mix shifts.
- **Feasibility:** direct · confirmed — with one steer: the Markov gain is tiny (~0.008 bits), so lean on marginal and phase-conditioned entropy, not sequence structure.
- **Novelty:** novel
- **Era story (the stated alternative won):** entropy ROSE with run rate — modern batting is faster AND more varied (sixes tripled in share even as 2s/3s declined). WPL is the most predictable dialect (2.157 bits) — more running variety but far fewer sixes.
- **Viz:** A "predictability meter" ticking in real time during ball-by-ball replay; a season-level scatter of entropy vs run rate with eras drifting visibly across the plane.
- **Teaser:** RR jumped 7.64 → 9.14 and outcome entropy rose with it, 2.251 → 2.294 bits; WPL: 2.157.
- **Lenses:** creative-structures

### Momentum Myth-Buster *(dynamics)*
A permutation-test framework asking whether momentum statistically exists: does a boundary (or wicket) change the next-ball outcome distribution beyond baseline?
- **Recipe:** Conditional probabilities (boundary|boundary, wicket within 6|wicket, boundary|3+ dots...) vs nulls from shuffling outcomes within innings × phase × batter strata, 1000×; z-scores per era; lag-k autocorrelation of runs-per-ball. **Stratification is the whole game** — the raw lift is mostly batter-quality clustering.
- **Feasibility:** direct · confirmed — minutes in NumPy; the honest risk (near-zero effect after stratification) is itself the headline, and the raw lift is already fading across eras.
- **Novelty:** novel
- **Era story:** If modern batting is premeditated (hit regardless of previous ball), autocorrelation should decay toward the shuffled null by 2026 — and the raw trend already points that way (lift 1.19 → 1.17 → 1.12 WPL).
- **Viz:** An interactive "did momentum happen?" panel: pick any conditional claim, see the observed needle against the shuffled-null histogram, with an era toggle. Punchy, falsifiable, shareable.
- **Teaser:** P(boundary | boundary): 19.2% vs 16.1% baseline in 2008-10 (lift 1.19); 24.5% vs 21.0% in 2023-26 (1.17) — momentum's raw edge is fading before the permutation test even runs.
- **Lenses:** creative-structures

### Collapse Contagion: Wickets as a Self-Exciting Point Process *(dynamics)*
Fit a Hawkes process to wicket timings within innings to measure whether wickets trigger wickets, and how collapse-proneness changed.
- **Recipe:** Wicket times on the 0-120 legal-ball axis; Hawkes MLE with phase-varying baseline μ(t) + exponential excitation, truncation handled as censoring — **both are load-bearing, not refinements** (the raw pooled conditional shows ANTI-excitation because post-wicket caution dominates). Fallback: inter-wicket gaps vs independence null. **Tighten the collapse definition to 3-in-12 or 4-in-18** (the pitched 3-in-18 fires in ~51% of ALL innings).
- **Feasibility:** direct · **adjusted**
- **Novelty:** novel
- **Era story (contrarian headline):** wickets calm the game down — the aftershock ratio is below 1 in every era — and the collapse rate is eerily era-stable across 15 years of scoring inflation. Post-2023, does Impact-Player depth raise excitation as post-wicket caution disappears?
- **Viz:** Seismograph view of every innings with wicket shocks and decaying aftershock-probability glow; famous collapses (RCB 49 all out) as earthquake swarms; a per-era aftershock-multiplier dial.
- **Teaser:** A wicket makes another wicket in the next 12 balls LESS likely than baseline (ratio 0.94 in 2023-26); the 3-in-18 "collapse" rate is 50.8 vs 51.2 per 100 innings across 15 years.
- **Lenses:** creative-structures

### Dot-Ball Pressure Cascades (debt, release, and the crack ratio) *(dynamics)*
Accumulating dot-ball pressure as a debt variable: how it resolves — boundary release, risky-shot wicket, or defused single — and how that economy shifted by era.
- **Recipe (reframed):** Pressure = consecutive-dot count (+ RRR delta in chases); next-ball outcome distribution at each level k. **Corrections:** the "next-ball boundary spike" is wrong — raw release ratios are always <1 (pressure states coincide with good bowlers), so the permutation/stratification controls are load-bearing; include run outs (pressure singles); stratify by phase from the start. Build on the same conditional-probability engine as the Momentum tester. Lead with the **crack ratio** = P(wicket|k≥3)/P(wicket|k=0).
- **Feasibility:** direct · **adjusted**
- **Novelty:** known-but-underused
- **Era story:** "Dots buy wickets" gets an era test — and the verified answer: pressure still kills in the WPL but IPL batters have defused it, explaining why bowling economies inflated even as bowler skill grew.
- **Viz:** A pressure-gauge overlay on innings replays: a needle climbing with each dot, then shattering green (boundary release) or blowing a red fuse (wicket) — with era dials for how often each ending occurs.
- **Teaser:** Middle-overs crack ratio: 1.11 in WPL vs 0.84 in IPL 2023-26 — dots still buy wickets in the WPL, no longer in the IPL.
- **Lenses:** creative-structures, batting-evolution, landscape-scan

### Strike Machine: Partnerships as Directed Flow Systems *(network-structure)*
Each partnership as a two-node dynamic system tracking who takes/gives strike — strike-farming, junior-partner shielding, and how strike management evolved.
- **Recipe:** Strike is explicit on every ball (no inference); per partnership: strike share vs 50/50, last-legal-ball-of-over behavior (keep vs surrender strike), farming index = correlation of strike share with partner SR gap, especially overs 16-20. Handle odd-run/over-boundary/wide-with-run swaps via extras fields. **Condition on death overs and partner gap** — the raw last-ball single rate is contaminated by ordinary rotation and actually rose.
- **Feasibility:** direct · confirmed
- **Novelty:** novel
- **Era story:** Either direction publishes: the sacrificial single is *not* dying (37.6% → 39.7% last-ball singles, gap over balls 1-5 widening) — and WPL shows the widest strike-management gap of any era, consistent with steeper batting-depth cliffs.
- **Viz:** Two batter avatars with a pulsing "strike token" passing between them over an innings replay; flow-ribbon summaries for legendary partnerships; a league trend line for the strike-keeping single.
- **Teaser:** Last-ball-of-over single rate rose 37.6% → 39.7%; WPL's last-ball singles run +2.2pp above its balls-1-5 rate — the widest gap in the dataset.
- **Lenses:** creative-structures

### Ball-by-Ball DNA: Player Fingerprints and Data-Driven Archetypes *(clustering)*
Embed every player-season as a feature vector from raw ball-by-ball signatures, cluster into archetypes with no labels, and watch archetypes appear and go extinct.
- **Recipe:** Per batter-season (≥100 balls; 150 early / 249 recent / 81 WPL qualify): SR/dot%/boundary% by phase, median entry ball, acceleration slope, dismissal mix, entropy, rotation rate, team-ball share. Standardize → PCA/UMAP → GMM/HDBSCAN; **fit pooled over all player-seasons, then plot per-season cluster occupancy.** Bowler mirror: economy/wicket% by phase, over-slot distribution, spell structure. Bootstrap cluster stability.
- **Feasibility:** derivable · confirmed — a one-feature proxy already shows the extinction signal is enormous.
- **Novelty:** novel
- **Era story:** Quantify the anchor's extinction as cluster-occupancy collapse; project WPL player-seasons into the same space — they land where IPL ~2012 lived, straight out of the era-migration hypothesis.
- **Viz:** Animated UMAP star-field: each dot a player-season colored by archetype, drifting season by season; trace a career path through archetype space (watch Kohli walk from anchor-land toward hitter-land).
- **Teaser:** Batter-seasons with SR < 120: 38.7% (2008-10) → 2.4% (2023-26); WPL 19.8% — almost exactly IPL 2012.
- **Lenses:** creative-structures

### The Shape of an Innings: Worm-Curve Taxonomy and Era Signatures *(clustering)*
Cluster all ~2,600 team innings as normalized cumulative-run curves into canonical silhouettes (front-loaded blitz, slow burn, mid-collapse, death surge) and chart the shape mix across seasons.
- **Recipe:** Cumulative run curves on the legal-ball axis, resampled to 120 points, total-normalized (plus an un-normalized variant); k-shape/DTW k-medoids (k≈5-8 by silhouette); wicket-fall marks as a secondary channel; per-season shape frequencies, shape-vs-win rate, innings-1 vs innings-2 asymmetry. Flag/exclude D/L innings.
- **Feasibility:** direct · confirmed — with a tempering note that *strengthens* the case: powerplay share of first-innings runs moved only 28.3% → 29.5%, so the shape revolution lives mid-innings, exactly what curve clustering (vs phase shares) reveals.
- **Novelty:** known-but-underused
- **Era story:** The moment the modal innings shape flips from convex ("preserve then explode") to linear IS the strategic revolution — datable to a specific season.
- **Viz:** Morphing gallery: each archetype an animated centroid curve with real innings ghosted behind; a stacked-area "shape market share" river 2008-2026; click a shape for its most extreme real example.
- **Teaser:** PP share of first-innings runs: 28.3% → 29.5% (WPL 26.7%) — totals exploded but the silhouette barely front-loaded; the real shape change is hiding mid-innings.
- **Lenses:** creative-structures, scoring-environment

### The Over as a Clock Face: Intra-Over Ball-Position Economics *(micro-structure)*
Decompose the six-ball over into positional structure — outcome distributions by ball-in-over — revealing how the internal script of an over evolved.
- **Recipe:** Re-index legal positions 1-6 around extras (actual_delivery cross-checks; decide a convention for attaching wide/no-ball runs — probe excluded illegal deliveries); per era/phase: RR, boundary%, dot%, wicket%, wide rate by position. Test scripts: ball-1 quiet spot, ball-6 strike-keeping single, balls-4-6 "lined up" premium.
- **Feasibility:** direct · confirmed — flattening confirmed AND the script inverted.
- **Novelty:** novel
- **Era story:** Early overs built to a ball-3 peak then faded; modern overs start hot and decay — the ball-1 "sighter" is extinct even *within* the over. WPL comparison: is the intra-over script sharper where bowling depth is thinner?
- **Viz:** Radial clock-face: six sectors per over, height = run rate, color = wicket risk, animated across eras so you watch the clock face flatten; flip between PP/middle/death faces.
- **Teaser:** 2008-10 ran quiet-loud-quiet (ball 1 = 7.34 RR, ball 3 = 8.02 peak, spread 0.68); 2023-26 starts hot and fades (ball 1 = 9.20, ball 6 = 8.89, spread 0.40).
- **Lenses:** creative-structures

### Era-Indexed Chase Difficulty Surface *(state-space)*
An empirical win-probability surface over chase states (balls left × runs needed × wickets in hand) per era — positions that were dead in 2010 becoming par by 2025.
- **Recipe:** Per 2nd-innings delivery: state + final outcome; fit WP per era band (GBM or kNN-smoothed lookup). **Correction: dedupe to one observation per match per state cell** (or cluster SEs by match) — raw ball-weighted sampling is biased by stalling teams and produced a misleading flat trend in the probe. Deliverables: the surface, the era-DELTA surface, and re-scored historical chases. Exclude 23 D/L; define an outcome rule for 26 no-winner matches.
- **Feasibility:** derivable · **adjusted**
- **Novelty:** known-but-underused
- **Era story:** The cleanest visualization of scoring inflation as changed geometry of possibility: "60 off 24 with 5 wickets" moving from lost to coin-flip across 19 seasons; IPL-vs-WPL surfaces at matched required rates.
- **Viz:** A heatmap (balls remaining × runs needed) colored by WP that MORPHS as you scrub eras, with iconic chases drawn as paths crawling across it; a time-machine mode re-prices any historic chase.
- **Teaser:** Needing 30-42 off the last 24 with 5+ wickets: 69% win rate in 2008-10 vs 88% in 2023-26.
- **Lenses:** creative-structures, scoring-environment, hidden-fields

### Season Phase-Space: Team Trajectories Through the Standings Manifold *(state-space)*
Every team-season as a trajectory through (cumulative points, NRR, Elo) space, clustered into narrative archetypes: wire-to-wire, late surge, mid-season collapse.
- **Recipe:** Chronological per-team: points (super-over ties resolved via outcome.eliminator — note ties carry no margin, so Elo needs a tie convention), running NRR (all-out = full quota; DLS via target.overs), match-level Elo (K≈20, margin multiplier); resample trajectories to 14 checkpoints, DTW k-medoids; league parity = end-season Elo variance + "race entropy" (how late qualification stayed undecided). Document Elo init for GT/LSG 2022.
- **Feasibility:** direct · confirmed — all outcome variants enumerated and handleable.
- **Novelty:** known-but-underused
- **Era story:** Did the auction system deliver its equalizing promise? Verified: yes, measurably — plus mega-auction resets (2022, 2025) should appear as Elo variance collapse.
- **Viz:** An animated "race in phase space": team dots leaving glowing trails through the points-NRR plane as the season clock runs; scrub any of 19 seasons or watch all ten franchises' historical trail-bundles at once.
- **Teaser:** Within-season SD of team win% fell 0.150 (2008-10) → 0.126 (2023-26) — real parity gain across 15 years of auctions.
- **Lenses:** creative-structures

---

## 7. Luck, Skill & Measurement Methodology

*The credibility layer: these ideas police every leaderboard in the product.*

### Stabilization Points: when is a cricket stat real? *(methodology)*
For each core rate stat, the number of balls at which half the observed variance is signal — baseball's famous stabilization table, which doesn't yet exist for T20.
- **Recipe:** Split-half / Cronbach-alpha resampling per stat (SR, boundary%, six%, dot%; economy, wicket%...), finding n where r = 0.5 (or beta-binomial prior strength); **stratify splits within phase** (verified necessity — role differences inflate naive reliability); compute per era bucket and phase. Wicket% (rare event) needs the most balls.
- **Feasibility:** direct · confirmed (live probe on 227 batters with 200+ balls)
- **Novelty:** novel
- **Era story:** (1) Meta-honesty: every leaderboard's minimum-sample threshold comes from here instead of arbitrary cutoffs; (2) if role specialization made performance more consistent, stabilization points should have shrunk — the league becoming more "legible." WPL's tiny sample is itself the lesson: most WPL player stats are still mostly noise, provably.
- **Viz:** Interactive reliability curve: pick a stat, drag the sample-size slider, watch signal% fill with a marker at the r=0.5 ball count; every leaderboard elsewhere shows a "trust meter" badge powered by this.
- **Teaser:** Split-half reliability of boundary% is r=0.518 at 100 balls — Spearman-Brown puts stabilization at ~93 balls, the first such number computed for T20.
- **Lenses:** sabermetric-translation

### Metric Half-Life (Staleness Meter) *(meta-measurement)*
How fast each headline stat's meaning decays across seasons — cross-season correlation at gap k fit to an exponential — telling the site how gray to render any cross-era comparison.
- **Recipe:** Per entity-stat pair (player SR/boundary%/economy, venue mean score, team chase win%): corr(season t, t+k) pooled over t for k=1..10 with reliability gating and pre-shrinkage; fit corr(k) = r0·e^(−k·ln2/h). Keep the free r0 (sampling noise attenuates r(1) to ~0.5); add a survivorship check (k-apart pairs are selected). Regime-break interaction: excess decay when a changepoint sits inside the gap validates the Seismograph independently.
- **Feasibility:** direct · confirmed (ran on all 19 seasons: clean, near-monotonic curves)
- **Novelty:** novel
- **Era story:** Different truths age differently — venue identities vs player boundary% vs economy across the 2023 break — and every comparison card inherits a freshness gauge from it.
- **Viz:** A freshness dial on every comparison card ("this 2013-vs-2025 economy comparison retains 22% of its meaning"); a dedicated page of decay small-multiples with changepoint-straddling gaps highlighted.
- **Teaser:** Batter SR half-life ≈ 4.3 seasons (r 0.46 at k=1 → 0.19 at k=5); bowler economy ages slower at ≈ 5.3 seasons.
- **Lenses:** era-machine-regime-detection

### Sequencing Luck: the innings reshuffle test *(luck-vs-skill)*
Cluster-luck for cricket — compare an innings' total to the distribution from re-ordering its own deliveries, isolating runs from fortunate sequencing.
- **Recipe (fixed):** The specced version is degenerate — completed not-all-out innings are shuffle-INVARIANT and won chases reach target under every permutation (~90% of innings give SeqLuck = 0), and on all-out innings the naive estimator is biased +11-13 runs (the real 10th wicket always falls on the multiset's last ball). **Fix:** extend truncated permutations by resampling deliveries from a phase-conditional corpus to 120 balls / 10 wickets, or price ball-order directly through the RE288 matrix. Phase-blocked shuffles still separate intent structure (skill) from within-phase luck.
- **Feasibility:** derivable (downgraded from direct) · **adjusted**
- **Novelty:** novel
- **Era story:** Re-based on an RE-priced trajectory statistic: how much innings *shape* matters should collapse from the back-loaded 2008-15 era to 2024-26 flat-line aggression — a rigorous fingerprint of the anchor era's death. WPL shapes placed on that scale.
- **Viz:** "Innings blender": pick a real innings, hit shuffle, watch the Manhattan re-deal and the total histogram build with the real total pinned — works verbatim on all-out innings.
- **Teaser:** Only 7.8% of modern first innings (10.2% in 2008-10; 14.8% WPL) are even shuffle-sensitive under the naive rules — the fix is what makes the metric real.
- **Lenses:** sabermetric-translation

### Pythagorean Wins for T20 (resource-adjusted) *(luck-vs-skill)*
Expected season win% from run differential with a T20-fitted exponent — which champions were lucky — with the truncated-chase problem solved via run expectancy.
- **Recipe:** Replace raw runs with resource-adjusted runs (project every innings to a full 20-over/10-wicket equivalent via RE288); fit the Pythagenpat exponent; luck = actual − Pythag wins; test year-to-year luck persistence. Exclude/repair D/L; skip super-over innings in run tallies but count their results as wins. 14-game seasons make luck enormous — show binomial CIs and sell the randomness as the story.
- **Feasibility:** direct · confirmed — champion identification validated 2008-2026; the cheap run-rate-differential precursor already produces the story.
- **Novelty:** known-but-underused
- **Era story:** A 19-season audit of earned vs lucky titles; a formal test of the "CSK wins close games" myth; and the fitted exponent itself should drift upward with the scoring environment, as in baseball.
- **Viz:** Every team-season a dot (Pythag wins × actual wins, diagonal = fair), champions crowned — see instantly which trophies sit far above the line; a per-franchise 19-season "luck ledger."
- **Teaser:** 2022 champions GT won 12 of 16 with only the 5th-best run-rate differential (+0.20); 2024 KKR won with the best in history (+1.55).
- **Lenses:** sabermetric-translation

### True-Talent Leaderboards (empirical-Bayes shrinkage) *(methodology)*
Every rate stat regressed to the mean with a principled prior — small-sample sensations pulled toward league average with credible intervals.
- **Recipe:** Beta-binomial / normal-normal empirical Bayes with prior strength k from the Stabilization analysis (~93 balls for boundary%); decaying-weight priors (recent balls count more, since talent drifts); posterior means with 80% CIs; a "regression called it" backtest on every breakout half-season 2008-2025.
- **Feasibility:** direct · confirmed — registry IDs make career pooling exact.
- **Novelty:** known-but-underused
- **Era story:** 19 seasons of April sensations meeting their forecasts — and the WPL as a league still living almost entirely inside the heavy-shrinkage zone, visible proof its stat record is young.
- **Viz:** The shrinkage slider: leaderboard bars morph raw→regressed, each sliding toward the mean proportional to sample size, CI whiskers attached; "fluke detector" cards for one-season wonders.
- **Teaser:** 69% of the 736 batters in IPL history have faced fewer than 200 career balls (WPL: 73% of 123) — most of both leagues lives in the shrinkage zone.
- **Lenses:** sabermetric-translation

---

## 8. Cross-League: IPL × WPL

### ★ League Maturity Clock (WPL year-N vs IPL year-N)
Aligns both leagues on seasons-since-founding (IPL S1=2008, WPL S1=2023) so any metric can be compared at the same league age — is the WPL maturing faster than the young IPL did?
- **Recipe:** Map info.season to league-year (WPL year 1 = the '2022/23' string); aggregate any season metric and index against league-year. **RR formula correction:** numerator = ALL runs (including wide/no-ball runs), denominator = legal balls — summing runs over legal deliveries only understates RR by ~0.3. Ship the alignment as a reusable dimension every other metric pivots on.
- **Feasibility:** direct · confirmed (proposer's numbers reproduced exactly after the fix: IPL Y1-4 RR 8.31/7.48/8.13/7.73; WPL 8.08/7.86/8.37/8.54)
- **Novelty:** novel
- **Era story:** The core comparative question: is a league founded into a mature T20 ecosystem on a steeper development curve than one that invented franchise T20 from scratch? Early evidence: yes for scoring, no for depth.
- **Viz:** Dual-clock interface: two concentric season dials the user rotates to snap onto the same league-year; every downstream chart re-aligns instantly; a fast-forward toggle projects where WPL year 8 might land.
- **Teaser:** WPL year-4 run rate (8.54) exactly equals the IPL's *year-15* run rate (2022) — 4 seasons to reach what took the men's league 15.
- **Lenses:** wpl-comparative, landscape-scan

### ★ Season Constellation Map (distribution-distance embedding with WPL projection)
A 2D "map of seasons" where each IPL and WPL season is placed by the actual distance between their per-ball outcome distributions — "WPL 2026 plays like IPL 20XX" becomes literal geometry.
- **Recipe:** Per season: a 4-phase × 10-outcome probability tensor over {0,1,2,3,4,6,wicket,wide,no-ball,bye/legbye}; pairwise phase-weighted Jensen-Shannon divergence; classical MDS on the 23×23 matrix (small numpy eigendecomposition — scipy not required); draw the IPL chronological path, project WPL points, report nearest IPL neighbors per phase. (Season-label fix: the pitched "WPL 2026 RR 8.24" was a label mixup; actual 8.54.)
- **Feasibility:** direct · **adjusted** — fully computed during verification; the punchline survives and is STRONGER.
- **Novelty:** novel
- **Era story:** Refutes "WPL is N years behind": WPL sits *beside* the IPL path, not on it — same run rate as IPL 2022, but a ball-by-ball outcome mix nearest IPL 2008 (four-led, six-light). Also shows whether 2020's UAE season is an off-path detour that snaps back.
- **Viz:** Night-sky constellation: IPL seasons as stars connected by a glowing chronological worm; WPL stars in another color with dotted lines to nearest IPL neighbors; a phase toggle re-embeds the map live — the answer depends on which phase you ask.
- **Teaser:** WPL 2026 scores at exactly IPL 2022's rate (8.54) yet its outcome mix is closest to IPL 2008 — 3.65 sixes per 100 balls vs IPL 2026's 8.56.
- **Lenses:** era-machine-regime-detection

### Scoring-Rate Convergence Gap
The calendar-year run-rate gap between IPL and WPL in the shared 2023-2026 window — converging, or is the men's explosion outrunning the women's growth?
- **Recipe:** Per season 2023-26: overall/PP/death RR per league; plot IPL-minus-WPL per phase; a per-100-balls boundary-count variant separates rate from mix. **Honesty note:** the widening is NOT monotonic — the gap peaked at 1.70 (2024) then narrowed before rising again.
- **Feasibility:** direct · confirmed
- **Novelty:** novel
- **Era story:** Both leagues are improving; the IPL's post-2023 (Impact Player) slope is simply steeper — a structural story about rule changes and hitting ceilings, not ability. The phase split sharpens it: the 2026 powerplay gap (2.24 RR) dwarfs the overall gap.
- **Viz:** Two-river chart: two flowing bands whose vertical separation is the gap, shaded and annotated; hovering a season splits the gap into PP/middle/death contributions.
- **Teaser:** The gap grew 0.91 (2023) → 1.35 (2026), spiking to 1.70 in 2024; the 2026 powerplay gap is 2.24 RPO (10.10 vs 7.86).
- **Lenses:** wpl-comparative

### Batting Depth Ledger (positions 7+)
Share of a league-season's runs scored by batters entering at 7 or lower — a direct read on the most-cited structural gap between the leagues, which the data overturns.
- **Recipe:** Positions from first-appearance order (exclude super overs; exclude wides from balls-consumed; footnote that an Impact sub can perturb naive ordering in a handful of innings; filter replacements to impact_player type for the 2023+ flag). Report pos-7+ run share, tail balls and SR per league-season; decompose share into opportunity (balls) vs productivity (SR).
- **Feasibility:** direct · confirmed
- **Novelty:** novel
- **Era story:** Conventional wisdom says WPL tails contribute nothing. The data says WPL lower orders contribute at or above IPL norms — opportunity-driven (more collapses force them to bat: 13.5% of balls at SR 117), not skill parity. Tell the honest decomposed version.
- **Viz:** Stacked "batting ladder" (rungs 1-11 sized by run share) side by side per league; maturity slider animates rung thickness; a toggle re-colors by SR to separate opportunity from skill.
- **Teaser:** WPL 2025 positions 7+ scored 15.3% of all runs — the highest single season in EITHER league (early IPL 10.3%, Impact-era IPL 11.6%).
- **Lenses:** wpl-comparative

### Star Gravity (normalized top-player concentration)
How much of each league's output its biggest stars produce — Lorenz/Gini over player run and wicket shares, normalized so the WPL's 5-team size doesn't fake the answer.
- **Recipe:** Per league-season: runs per batter, bowler-credited wickets per bowler; Lorenz over qualifiers (fix and report the threshold — Gini is highly threshold-sensitive: 0.61 unfiltered vs 0.39 at ≥30 balls); report Gini AND top-5%-of-players share (percentile-based, not raw top-5).
- **Feasibility:** direct · **adjusted** — the headline REVERSES under the idea's own normalization (which the proposer never ran): raw top-5 shares are ~2× IPL's, but at matched percentiles WPL's share and Gini are *lower* than IPL's.
- **Novelty:** novel
- **Era story (corrected):** Apparent WPL star-dependence is a pool-size illusion — reframe as myth-busting, then track whether that parity survives league expansion. Keep the raw-vs-normalized pair as the interactive reveal.
- **Viz:** Animated Lorenz curves breathing between seasons, one color per league; a "gravity well" view with players orbiting the league center at distance inverse to output share.
- **Teaser:** Raw top-5 batters hold 24.5-27% of WPL runs vs 12-19.5% in IPL — but at matched percentiles the gap vanishes (WPL top-5% share 10.9-14.0% vs IPL 12.2-17.5%; Gini 0.36 vs 0.40).
- **Lenses:** wpl-comparative

### Twos Culture / Ground-Geometry Proxy
Twos (and near-extinct threes) as a share of running shots — how boundary dimensions and outfield athleticism shape a different running economy in each league.
- **Recipe:** twos_rate = P(runs.batter==2 | runs.batter ∈ {1,2,3}) per league-season; threes via runs.batter==3 (**not runs.total==3** — the pitched "81 threes in 2021" counted extras; actual 34, corpus max 71 in 2013); WPL threes are lumpy (25 total, 13 in 2024 alone) — avoid per-season WPL claims. Shared-venue slice verified: 5 exact venue matches host both leagues (Chinnaswamy 24/19, Brabourne 17/15) for the controlled comparison. Rope-length attribution needs external boundary data (annotation only).
- **Feasibility:** direct · **adjusted**
- **Novelty:** novel
- **Era story:** Counterintuitive and verified: smaller WPL ropes convert would-be twos into fours, so the women's running game is *thinner*, not richer; meanwhile the IPL's three is dying (0.85 → 0.46/match) as boundary hitting replaced hard running. Track whether WPL twos rise as boards push ropes back (a live 2024-26 policy debate).
- **Viz:** A "running odometer": animated pitch diagram with stick figures completing 1s/2s/3s at each league's observed frequencies; a venue dropdown filters to grounds hosting both leagues.
- **Teaser:** Only 9.8% of WPL running shots are twos vs 13.5% in the modern IPL; IPL threes fell 0.85 → 0.46 per match.
- **Lenses:** wpl-comparative

### Powerplay Fear Index
Powerplay run rate as a ratio of overall run rate — how much of the fielding-restriction advantage each league actually cashes, at the same league age.
- **Recipe:** PP_RR / overall RR per league-season with **consistent legal-ball denominators** (verified bug in the pitched numbers: PP rate used all balls, overall used legal balls, inflating the "fear" gap); PP wicket cost alongside; exact restriction windows from powerplays[] (present in 100% of innings).
- **Feasibility:** direct · **adjusted**
- **Novelty:** known-but-underused
- **Era story (corrected):** The IPL did NOT learn gradually — the ratio was FLAT at ~0.92-0.93 for 15 seasons and jumped only in the Impact Player era, crossing 1.0 by 2026 (the powerplay now outscores the rest of the innings). WPL 2026 (0.92) sits exactly at the old IPL equilibrium — so the question becomes whether it needs a structural shock of its own to break out.
- **Viz:** Overlaid intra-innings RR curves (overs 1-20) per league morphing under the maturity slider; the PP window glows; a "fear gauge" needle with IPL-2008's position ghosted behind WPL's current one.
- **Teaser:** IPL PP/overall ratio: stuck at ~0.93 from 2008-2020, then 1.02 in 2026; WPL 2026: 0.92.
- **Lenses:** wpl-comparative

### Stumping Signature (data-native spin-share and feet-usage proxy)
Stumped% of dismissals — plus bowled+lbw share and keeper-up frequency — as a data-native proxy for how spin-dominated each league's bowling ecosystem is.
- **Recipe:** Per league-season: stumped / bowled+lbw / caught shares from wickets[].kind. Optional upgrade to true spin over-share needs the external bowler-style table (doesn't gate the core). **Narrative fix:** IPL stumped share was not monotonically high early — 1.9% (2008), peak 5.0% (2010), decay to 1.4-2.2%; frame as "peaked circa 2009-13, then collapsed."
- **Feasibility:** direct · confirmed
- **Novelty:** known-but-underused
- **Era story:** The IPL drifted toward pace-at-the-death orthodoxy (stumpings collapsing); the WPL is structurally a spinner's league (5.2-7.9% every season). Watching whether WPL stumpings fall as batters learn to play spin deeper is a legitimate skill-evolution signal.
- **Viz:** Dismissal-type streamgraph per league aligned on the maturity clock, stumpings as a glowing thread; clicking the thread opens keeper-standing-up moments per season.
- **Teaser:** Stumpings are 5.2-7.9% of WPL dismissals every season vs 1.4% in IPL 2026 — a 4-5× gap.
- **Lenses:** wpl-comparative, hidden-fields

### Competitive Balance Barometer
Within-season win concentration (HHI normalized for league size) plus title concentration — is the WPL more of a duopoly than the young IPL was?
- **Recipe:** Win share per team from outcome.winner **including super-over ties via outcome.eliminator** (27 tied matches otherwise silently drop); normalized HHI = (HHI − 1/N)/(1 − 1/N); cumulative distinct champions by league-year after canonicalizing renames. (Factual fix: early IPL had 3 distinct champions in its first 4 seasons, not 4; WPL has 2 in 4 — MI ×2, RCB ×2 — strengthening the duopoly story.)
- **Feasibility:** direct · confirmed
- **Novelty:** known-but-underused
- **Era story:** The early IPL was famously chaotic; the WPL launched stratified. Track normalized HHI on the maturity clock — a bending-down curve would show the WPL auction mechanism starting to work.
- **Viz:** A balance-beam per season: teams sit at positions weighted by win share and the beam tilts by imbalance; both leagues' beams animate side by side on the maturity clock.
- **Teaser:** Mean normalized win-HHI: WPL 0.046 vs 0.019 for the chaotic early IPL and 0.011 for the modern IPL — the WPL is ~2.4× more top-heavy than even the early IPL.
- **Lenses:** wpl-comparative

### Homegrown Pipeline Tracker (uncapped-Indian share) *(needs-external-data)*
The share of each season's debutants and appearances that are uncapped Indians vs capped Indians vs overseas players — the league's talent-factory dividend.
- **Recipe:** Join registry IDs → Cricsheet people.csv (live-verified: 811/811 IPL players matched, all carrying ESPNcricinfo keys) → scrape nationality + international-debut date (~811 IPL + 136 WPL pages; Kaggle auction data as secondary for capped status). Then: debutant mix, share of deliveries by class, graduation rate (uncapped debutants later capped by India) per cohort. The same join unlocks birthdates for biological-age curves.
- **Feasibility:** needs-external-data (ESPNcricinfo via Cricsheet register — **the strongest external-data candidate in the catalog; the join path is already proven**) · confirmed
- **Novelty:** known-but-underused
- **Era story:** The IPL's founding promise was an Indian talent factory — measure it: does the uncapped share of deliveries rise, does graduation-to-Team-India improve by cohort (Bumrah 2013, Hardik 2015 vs class of 2023)? For WPL: is a 4-year-old league already shifting from imported stars to homegrown players?
- **Viz:** A stacked "pipeline river" per season (overseas / capped / uncapped bands) with graduation moments as sparks jumping upward; IPL and WPL panels aligned on league age.
- **Teaser:** (none without the join)
- **Lenses:** career-arcs-cohorts-roster-churn

---

## 9. Fielding & Officiating

### No-Ball Technology Shock *(officiating)*
An interrupted time-series of front-foot no-balls around the 2020 introduction of automated third-umpire no-ball monitoring.
- **Recipe:** No-balls per match per season; level-shift fit at 2020 (on-field-only vs TV-monitored eras); secondary splits by phase and free-hit tax (pair the no-ball with subsequent deliveries **by sequence within the over, not delivery number** — re-bowled balls repeat numbers).
- **Feasibility:** direct · confirmed — claimed numbers reproduce exactly.
- **Novelty:** novel
- **Era story:** The post-2020 rebound is a measurement-regime change masquerading as a skill change — a perfect teaching exhibit about instrumentation effects, and a real estimate that umpires historically missed ~40% of oversteps.
- **Viz:** Classic interrupted-time-series chart with a bold "machines start watching" marker at 2020; hover any season for its most expensive free-hit sequences as ball strips.
- **Teaser:** No-balls/match fell 1.41 (2008) → 0.65 (2018), then jumped back to 1.35 (2023) once the TV umpire watched every ball.
- **Lenses:** hidden-fields

### Umpire Fingerprint Cards *(officiating)*
Per-umpire profiles: wide/no-ball call rates (pair-level), lbw-given rates, and DRS overturn rates from the review.umpire field that names exactly whose decision was challenged.
- **Recipe:** Attribute match wides/no-balls/lbw to the on-field pair (individual attribution impossible — ends alternate; decompose via regression on umpire indicators); for 2018+ reviews (all 990 carry the umpire name): per-umpire overturn rate and umpires_call share (140 flags). Absence of review pre-2018 = no DRS, not missing data; review.type present on only 540/990.
- **Feasibility:** direct · confirmed — 85 distinct umpires, top ones 131 matches.
- **Novelty:** novel
- **Era story:** Umpiring accuracy under DRS scrutiny: do veterans' decisions survive review more often; has the struck-down rate shifted as teams got savvier; who officiated across all 19 seasons — the professionalization of the panel.
- **Viz:** Baseball-card gallery: each umpire a card with a "decision survival" gauge, wide-strictness percentile, seasons-active timeline; a beeswarm of all 85 umpires by overturn rate.
- **Teaser:** DRS overturn rates among high-volume umpires range 22% (Nitin Menon, 73 reviews) to 39% (VK Sharma, 64); league-wide, 70% of challenged decisions survive.
- **Lenses:** hidden-fields

### Keeper Inference Engine + Byes Ledger *(fielding)*
Infers who kept wicket in every match from stumping credits, then measures keeper quality via byes conceded and keeper-catch share.
- **Recipe:** Keeper = stumping-credited fielder (13.6% of team-matches directly) → season most-frequent-stumper in XI (+64.7%) → career-stumper fallback (+18.2%) — only 3.5% of 2,486 team-matches left for external designation, far below the pitched 15-20%. Byes per 100 balls fielded (normalize by team wide rate) and keeper-catch share. **Byes are sparse (~1/match): report career/era aggregates, not single-season leaderboards.**
- **Feasibility:** derivable · **adjusted**
- **Novelty:** novel
- **Era story (twist, verified):** the "keepers became batters and gloves slipped" hypothesis is refuted — byes *fell* across eras. Keepers became batters AND got tidier: a stronger story.
- **Viz:** Career-arc small multiples (byes rate per keeper, dot size = matches kept); a "leaky gloves vs safe hands" quadrant (byes rate × keeper-catch share) animated per era.
- **Teaser:** IPL byes per 100 legal balls fell 0.58 (2008-10) → 0.46 (2023-26) — the batter-keeper era leaks fewer byes, not more.
- **Lenses:** hidden-fields

### Catch Networks & the Substitute Underworld *(fielding)*
Bowler-to-fielder catch graphs from the fielders arrays, plus the 231 wickets involving substitute fielders that official stats ignore.
- **Recipe:** Per 'caught' wicket: directed edge (bowler → fielders[0]) per franchise-era; Fielding Involvement Index = appearances in fielders arrays per match; substitute strand via fielders[].substitute==true (231 records: 226 IPL + 5 WPL; 2023 spike to 30 confirmed). **Correction:** missing run-out fielder names are NOT an early-files issue — 167 of 177 gaps cluster in 2018-2021; flag that window.
- **Feasibility:** direct · confirmed
- **Novelty:** novel
- **Era story:** Catching now carries 72.4% of dismissals (59.9% in 2008-10), so fielding workload concentration matters more each year; the network shows which bowler-fielder duos define each tactical era.
- **Viz:** Force-directed catch web per franchise in team colors; era slider grows the hubs (gun fielders); an "underworld" toggle reveals ghost nodes — substitutes who took catches while officially not in the XI.
- **Teaser:** Caught share 59.9% → 72.4%; substitute-fielder involvements spiked from ~10/season to 30 in 2023, the Impact Player year.
- **Lenses:** hidden-fields

### Fielding Impact (dismissal-linked) *(fielding)*
Catches, run-outs and stumpings per fielder, weighted by the win-probability value of the dismissal — the only fielding signal Cricsheet carries.
- **Recipe:** Involvements per fielder from wickets[].fielders (present in every era; 1.6-2.7% substitute/name-only entries handled by name string); weight by the dismissal ball's WPA; keeper-specific splits. State honestly: drops, saves and boundary catches are invisible — converted chances only.
- **Feasibility:** direct · confirmed
- **Novelty:** known-but-underused
- **Era story:** Dismissal-mix evolution as a fielding-workload story (caught up, run-outs collapsed, stumpings tracking spin eras); WPL's stumping share (6.3%) as a league-development marker in the keeper-centrality view.
- **Viz:** A fielding "web" per team-season — fielder nodes sized by weighted dismissal impact, edges to the bowlers they converted for; keeper centrality shifting across spin eras.
- **Teaser:** Caught share rose 57.2% → 69.9% of all dismissals while run-out share collapsed 12.0% → 5.2%.
- **Lenses:** landscape-scan

---

## 10. Schedule, Calendar & Fatigue

### Season Compression Index *(schedule-structure)*
A league-health series of calendar density: matches per day league-wide and games per team per week, IPL vs the hyper-compressed WPL.
- **Recipe:** League compression = matches / span days (split 2021's two legs — raw span 190 days); team compression = matches per rolling 7-day window; rest-gap Gini as an equity measure. **Correction: the cross-league story must be told at TEAM level** — WPL league-level compression is *lower* (5 teams), but WPL team schedules are the densest ever recorded.
- **Feasibility:** direct · **adjusted**
- **Novelty:** novel
- **Era story:** The IPL calendar got measurably kinder (peak 1.54 matches/day in 2009 → 1.00-1.14 now) while the WPL launched at maximum team-level compression and is itself decompressing (3.13 → 2.47 games/week) — the "WPL replays IPL history" arc live within four seasons.
- **Viz:** A wall of season calendar strips (one row per season, one cell per day, intensity = matches) — 2009 glows dense, 2025 breathes, 2021 snaps in half, WPL rows sit below as short hot bars.
- **Teaser:** A 2023 WPL team played 3.13 games/week — denser than any IPL team schedule ever (IPL peak 2.91 in 2009; IPL 2025: 1.57).
- **Lenses:** schedule-calendar-fatigue

### Rest-Delta Win Edge *(schedule-fatigue)*
How much win probability and late-game execution shift with a team's rest advantage over its opponent — and the verified reversal: the effect *emerged* rather than shrank.
- **Recipe:** Rest = days since the team's previous match (split 2021 legs via >30-day rule; franchise-name map; exclude ties/NRs); rest_delta buckets; outcomes per bucket: win rate, death-overs economy, fielding-dismissal share, wides as fatigue tells. Back-to-backs are extinct post-2011 (6 ever) — use 2d/3d/4d+ buckets.
- **Feasibility:** direct · **adjusted** — hypothesis ran backwards: 2008-13 non-monotonic, 2014-19 dead flat (49.6/50.4), 2020-26 a real edge.
- **Novelty:** known-but-underused
- **Era story (corrected):** "Why does rest matter more NOW?" — candidates: heavier travel, the 10-team format. An NBA-staple analysis never computed for the IPL, with WPL congestion as the stress case.
- **Viz:** Dumbbell chart per era: rest-delta buckets as rungs with win-rate dots, animating the fatigue penalty *appearing* over time.
- **Teaser:** Teams with a 2+ day rest advantage won 57.0% in 2020-26 (vs 43.0% short); in 2014-19 the identical split was exactly 50.0/50.0.
- **Lenses:** schedule-calendar-fatigue

### XI Churn Under Congestion *(schedule-fatigue)*
Lineup changes between consecutive fixtures as a function of rest, prior result, and leverage — rotation as panic vs load management.
- **Recipe:** Churn from consecutive info.players lists on registry IDs (subtract the Impact "in" player for true XIs — 2023+ lists carry 12 names in 551 matches); model on rest gap, prior result, leverage, double-header participation. Forced-vs-elective churn is unsplittable without injury data — flag the limit.
- **Feasibility:** direct · confirmed
- **Novelty:** novel
- **Era story (verified sign flip):** 2008-10 teams churned MORE on short rest (+0.24); 2023-26 teams churn LESS (−0.17) — from squeezed-into-changes to planned load management. WPL rotates like the modern IPL on results (loss 1.25 vs win 0.67).
- **Viz:** Rotation rhythm wall: one row per team-season, one cell per match colored by players changed, cell spacing encoding rest gaps — congested wide-churn clusters pop out.
- **Teaser:** Short-rest churn flipped from +0.24 extra changes (2008-10) to −0.17 (2023-26).
- **Lenses:** schedule-calendar-fatigue

### Road-Trip Fatigue Gradient *(schedule-fatigue)*
Performance on the Nth consecutive away fixture — do long road trips erode teams, and what do the caravan eras do to "away" at all?
- **Recipe (corrected):** Home = the *set* of cities with ≥3 fixtures that season (single-modal-city logic breaks on multi-home teams — median modal share is only 0.46); tag 2009/2020 fully neutral, 2014 UAE leg neutral; league phase only; backfill 51 null cities from the two UAE venue strings. Outcomes by away-streak position vs the home-streak control gradient.
- **Feasibility:** derivable · **adjusted**
- **Novelty:** novel
- **Era story:** The road-trip sag of the early IPL has nearly vanished in the charter-flight era; and in no-home seasons (2009/2020/WPL) the residual "home" edge isolates venue knowledge from scheduling comfort.
- **Viz:** Each team-season as a band of houses and suitcases with a performance sparkline underneath — long suitcase runs sagging the sparkline in early eras, holding flat in modern ones.
- **Teaser:** Win rate on the 3rd+ consecutive away match: 41.0% in 2008-13 vs 49.6% in 2021-26.
- **Lenses:** schedule-calendar-fatigue

### Rain & DLS Exposure Audit *(schedule-structure)*
How often weather decides matches, whether the calendar window's drift changed rain exposure, and whether D/L chases are won at fair rates.
- **Recipe:** Rain-touched flags: outcome.method=='D/L' (23), multi-date matches (2), target.overs<20, no-results (**filter on outcome.result=='no result', not absence of winner — 16 ties also lack winners**), short non-all-out first innings. Rate per season and calendar half-month; D/L fairness: chase win rate in adjusted vs unaffected matches, era-pooled (n=23 demands it).
- **Feasibility:** direct · confirmed
- **Novelty:** known-but-underused
- **Era story:** The IPL quietly migrated three weeks earlier (Apr 18 → Mar 22 starts) and once fled to autumn — and the counterintuitive verified headline: the modern early-start era is the DRIEST (2.5% rain-touched vs 5.0% in 2014-19). Meanwhile D/L par math looks systematically kind to chasers.
- **Viz:** Ribbon chart of each season's calendar window on a shared Jan-Dec axis, rain-affected matches falling as animated droplets — ribbons sliding left over the years while droplet density shifts.
- **Teaser:** D/L-adjusted chases were won by the chaser 69.6% of the time (16/23) vs a 54.7% baseline.
- **Lenses:** schedule-calendar-fatigue

### Playoff Gauntlet vs Fresh-Legs Final *(schedule-structure)*
Finalists arriving via the Eliminator+Qualifier-2 gauntlet (~3 knockouts in ~6 days) vs rested Qualifier-1 winners — the rest-vs-rhythm tradeoff in deciders.
- **Recipe:** Classify each finalist's path from event.stage (**accept both 'Eliminator' and 'Elimination Final' labels**; 16 Qualifier-era finals 2011-26; Q2→Final gap is 1-3 days); rest days, matches in the last 8 days, cumulative overs by the top-4 bowlers; outcomes: final win rate by path, final scoring vs own league-phase baseline, death economy of heavily-worked bowlers. Present as an evidence ledger, not p-values (n=19 finals). WPL = Eliminator+Final only — frame accordingly.
- **Feasibility:** direct · **adjusted** (label + framing fixes)
- **Novelty:** known-but-underused
- **Era story:** The 2011 Qualifier system deliberately gave the top-2 a safety net — never audited across 15+ finals. Verified drama: gauntlet teams won 3/8 finals 2011-18, then 0/8 since 2019; WPL Eliminator-path teams have won 3/4.
- **Viz:** An interactive bracket where each finalist's path is a physical road — length = days, tollbooths = matches — converging on the trophy; gauntlet-path winners light up in defiance of the rest advantage.
- **Teaser:** Qualifier-2-path teams have won 3 of 16 IPL finals since 2011 — and 0 of the last 8 — while WPL Eliminator-path teams are 3 of 4.
- **Lenses:** schedule-calendar-fatigue

### Team Travel Odometer *(schedule-fatigue, needs-external-data for km only)*
Each team's city-to-city hop sequence per season as a travel-burden series — caravan eras vs home-and-away eras, and whether kilometers cost runs.
- **Recipe:** Hop counts and unique-cities are 100% in-data now (fix the 51 null-city UAE matches with a 2-row venue map; consider venue-level hops as a secondary series — Mumbai used 3 stadiums in 2022). Kilometers need a one-time ~45-row city lat/long gazetteer (GeoNames/OpenFlights, public domain) for great-circle sums. Regress next-match performance on hopped-yesterday and cumulative km, controlling rest.
- **Feasibility:** needs-external-data (km layer only; hops ship today) · confirmed
- **Novelty:** novel
- **Era story:** Three natural experiments where the whole league was airlifted (2009 SA, 2014 UAE leg, 2020-21 bubble), plus the structural arc: early IPL and the WPL are caravan leagues; the mature 10-team IPL restored true mileage — trading rest for airports?
- **Viz:** Animated map with each team a colored comet tracing its season route; the season slider morphs India 2008 into South Africa 2009 into the UAE bubble, comet tails thickening with accumulated fatigue-km.
- **Teaser:** Mean unique cities per team: 8.1 (2010) → 3.0 (2020 bubble); mean city-hops jumped 7.1 (2022) → 12.6 (2023) when home-and-away returned.
- **Lenses:** schedule-calendar-fatigue

---

## 11. Careers, Cohorts & Roster Churn

### ★ Roster Continuity Index (Auction Heartbeat) *(roster-churn)*
Season-over-season Jaccard similarity of each franchise's used squad — the auction cycle as a measurable EKG, and a test of whether continuity buys wins.
- **Recipe:** Squad = union of registry IDs across a franchise's players lists per season (canonicalized names); RCI = Jaccard with the prior season; decompose core retention (≥50% of matches) vs fringe churn; regress next-season win% on RCI with mega-auction dummies. Define a gap rule for the CSK/RR 2016-17 suspensions; Deccan→SRH is a new franchise, not a rename.
- **Feasibility:** direct · confirmed — proposer's CSK numbers replicated exactly; league-wide the EKG is even cleaner. One hypothesis pre-killed: baseline (non-mega) continuity is FLAT 2009-2026, not rising — itself publishable.
- **Novelty:** novel
- **Era story:** Every mega-auction (2011, 2014, 2018, 2022, 2025) is a synchronized league-wide continuity crash; then the continuity-wins question — CSK's dynasty vs GT winning immediately from a from-scratch 2022 squad. WPL's mini-auction cycles give a compressed replica.
- **Viz:** Hospital telemetry: one pulse trace per franchise stacked like monitors, mega-auction years producing synchronized flatline dips; next-season win% as a dot on each beat; click a dip to see exactly who left and arrived.
- **Teaser:** League-mean used-squad Jaccard: 0.19 in mega-auction years vs 0.46 in retention years — five synchronized flatlines in 19 seasons.
- **Lenses:** career-arcs-cohorts-roster-churn

### Debut Cohort Survival Curves *(cohorts)*
Kaplan-Meier survival for every debut class: what fraction of the class of X still appears at league-age 1, 2, 3... N.
- **Recipe:** Debut = first season in any players list (809 IPL / 136 WPL players verified); survival at age k = share appearing in season debut+k *or later* (robust to gap years); right-censor young cohorts. **Corrections:** (1) survival is U-shaped, not monotonically declining — 62% (2008 class) → 35% (2011) → 82% peak (2015) → 39% (2023); the honest story is a mid-2010s retention golden age. (2) WPL-vs-IPL year-2 comparisons need symmetric censoring (WPL classes have no future seasons for gap-year returns).
- **Feasibility:** direct · **adjusted**
- **Novelty:** novel
- **Era story:** Does the league chew players up faster now? Recent decline is real but recent — and the WPL's class-of-2024 vs IPL's class-of-2009 (both "year two of a new league") is the cleanest cross-league cohort test.
- **Viz:** 19 cohort ribbons flowing across the timeline, thickness = survivors; hover isolates a survival curve with the WPL cohort overlaid at the same league age; a toggle re-bases the axis to league-age so 2008-IPL and 2023-WPL share an origin.
- **Teaser:** 62% of the class of 2008 was still appearing three seasons later; only 39% of the class of 2023 — but 2015 peaked at 82%, so the decline is recent, not monotonic.
- **Lenses:** career-arcs-cohorts-roster-churn

### XI Stability Meter *(roster-churn)*
Within-season, match-to-match churn of each franchise's starting XI, and whether the Impact Player era changed rotation habits.
- **Recipe:** Stability = Jaccard of consecutive XIs ordered by date; 2023+ recover the true XI by subtracting the replacements "in" player (12-name lists in 138/148 matches; edge cases: 29 eleven-name, 6 thirteen-name; replacement names need registry lookup). League-wide stability index per season.
- **Feasibility:** derivable · confirmed — drift verified conservative (12-name lists mechanically depress Jaccard, and it still rises).
- **Novelty:** novel
- **Era story:** Two forces compete — analytics-driven settled-XI thinking vs Impact-Player horses-for-courses — and the settled-XI force is winning: a genuinely non-obvious finding. WPL sits higher still (0.84-0.87), churn-under-scarcity.
- **Viz:** Barcode wall: each franchise-season a row, each match a thin bar colored by names changed (calm green → alarm red); 19 seasons stack into a heat-tapestry; an Impact-era toggle splits XI churn from 12th-name churn.
- **Teaser:** Consecutive-XI Jaccard drifted up 0.733 (2008) → 0.794 (2025) despite 12-name lists dragging it down; WPL 0.84-0.87.
- **Lenses:** career-arcs-cohorts-roster-churn

### Record Half-Life *(records-streaks)*
How long each league record survives before falling — record decay as a direct measurement of the scoring environment, without any rate stats.
- **Recipe:** Chronological replay maintaining running records (highest total, highest score, fastest 50/100, best figures, biggest chase excluding D/L wins, most sixes); half-life = days/matches until broken. **Statistical correction:** naive mean lifespan is misleading (records get monotonically harder — lifespans of broken records rose even as scoring exploded); use record-falls-per-season clustering or a stationary-environment null replay.
- **Feasibility:** direct · confirmed — the replay engine reproduces reality exactly (Gayle 175 2013, SRH 287 2024, 265 chase 2026).
- **Novelty:** novel
- **Era story:** 2024 as a mass-extinction event for batting records; the WPL's ticker visibly runs at a different clock speed (25 post-establishment record falls in 88 matches vs the IPL's 13 in ~1,185 since 2009).
- **Viz:** A records-falling ticker: scrub April 2008 → 2026 while standing records shatter on a board (match, venue, holder); below, step-function record frontiers with era-shaded lifespan bands compressing like a spring.
- **Teaser:** The highest-total record (RCB 263, Apr 2013) stood 3,991 days — then fell twice in 19 days in 2024.
- **Lenses:** career-arcs-cohorts-roster-churn

### Streak Atlas with Luck Nulls *(records-streaks)*
Every notable streak — team wins, consecutive 30+ scores, economical death overs — tested against permutation nulls to separate form from coin-flip luck.
- **Recipe:** Per-entity ordered sequences; max run-lengths vs 1,000-shuffle nulls preserving marginal rates — **permute within season** (or condition on season win rates), else 2012 luck leaks into 2024 streaks; fix 5-6 canonical streak definitions; minimum-overs filters for bowling streaks. Fast enough to run the permutation live client-side (<5s verified).
- **Feasibility:** direct · confirmed
- **Novelty:** novel
- **Era story:** Are streaks dying as opponents adapt faster? And the headline probe IS the pitch: famous streaks mostly live inside the luck band.
- **Viz:** Soccer-style form-guide strips for every team and star on the season timeline, with a translucent grey "luck band" (5th-95th percentile null range) — streaks that pierce it glow gold; a "was it luck?" button runs the permutation animation live.
- **Teaser:** KKR's celebrated 10-match win streak (2014) sits at the 85th percentile of their own shuffled-history null — indistinguishable from a 52%-win coin.
- **Lenses:** career-arcs-cohorts-roster-churn

### One-Season Wonder Rate *(cohorts)*
The share of each season's top-20 impact players who never crack a top-50 again — a market-efficiency signal per era.
- **Recipe:** Season impact rank (project impact layer, or the model-free PoM variant that runs today); "wonder" = top-20 in season t, never top-50 later — **at fixed horizons** (never-within-3-years) to handle censoring. PoM cross-check: winners who never win again.
- **Feasibility:** derivable (PoM variant direct, already run end-to-end) · confirmed
- **Novelty:** novel
- **Era story:** Early IPL was full of flash-in-the-pan stars (Valthaty, Asnodkar); scouting networks and feeder leagues make breakouts more durable — the verified direction supports market efficiency. WPL gives a high-variance comparison.
- **Viz:** Comet chart: each season's top-20 enter the sky; persisters keep burning, wonders flare once and fade to grey ash accumulating along the timeline; hover a burnt-out comet for their one glorious season.
- **Teaser:** 44% of 2008-10 PoM winners never won another within 3 seasons; for 2020-22 winners, 36%.
- **Lenses:** career-arcs-cohorts-roster-churn

### Career Shape Clustering (arc archetypes) *(career-arcs)*
Cluster per-player league-age trajectories of era-adjusted impact into archetypes — early peak, late bloomer, plateau, yo-yo — and track the mix by debut cohort.
- **Recipe:** Players with ≥4 seasons (**corrected count: 339 IPL careers qualify, not ~411** — the larger figure counted 2+ seasons); within-season z-scored impact series indexed by league-age; interpolate/DTW + k-medoids (k≈4-6). WPL "first light" is tinier than pitched: exactly 33 players span all 4 seasons — a single-archetype comparison, not standalone clustering. Derive season from dates.
- **Feasibility:** derivable · **adjusted**
- **Novelty:** novel
- **Era story:** Has the shape of an IPL career changed? Early cohorts skew slow-build (learned T20 on the job); 2018+ cohorts arrive ready (instant-peak arcs) — the mix per cohort measures the player-development pipeline industrializing.
- **Viz:** Archetype gallery: 4-6 panels of spaghetti with the named medoid bold ("The Meteor", "The Slow Burn", "The Metronome"); a sankey from debut-cohort ribbons into archetype panels; click a strand for the player's actual career chart.
- **Teaser:** 339 IPL careers span 4+ seasons (of 811 players ever) vs exactly 33 qualifying WPL careers in 2026 — the first year WPL arcs are analyzable at all.
- **Lenses:** career-arcs-cohorts-roster-churn

### Career Gap & Comeback Map *(career-arcs)*
Every hole in every career — seasons missed to unsold/dropped/injured — and the probability of coming back, by gap length and era.
- **Recipe (bug fixed):** the pitched "maximal gaps strictly inside [debut, last]" end in a return *by construction* (P=1 always). Correct: condition on absence-START events (played s, absent s+1), measure whether the player EVER returns; right-censor absences within ~3 seasons of 2026. Exile-and-return flavor: same or different franchise (joins the Journeyman Network). Gap *cause* needs external annotation for famous cases only.
- **Feasibility:** direct · **adjusted** — corrected version run on all 811 players.
- **Novelty:** novel
- **Era story (contrarian, verified):** the league got MORE forgiving — comeback probability rose, plausibly a mega-auction recycling effect. Missing an auction is less career-ending now, not more.
- **Viz:** A piano-roll of 809 careers: one thin strip per player sorted by debut, filled where they played, black voids where they vanished, comeback returns as bright re-entry flashes; filters isolate "the exiled who returned."
- **Teaser:** P(ever returning after missing a season): 33% for absences starting 2009-14 → 45% for 2018-23.
- **Lenses:** career-arcs-cohorts-roster-churn

### Debut-to-Signature Lag *(cohorts)*
How many matches a debutant needs before their first signature moment — first fifty, first 3-wicket haul, first PoM — and whether new players arrive "pre-built."
- **Recipe:** Kaplan-Meier on matches-to-first-signature (never-achieved = censored); signature events verified computable across eras; bowler credit via standard wicket-kind filtering.
- **Feasibility:** direct · confirmed — with an honest warning: the headline cohort hypothesis FAILED first contact (flat at the 5-match horizon for 15 years). **Lead with the IPL-vs-WPL contrast instead**, or test finer horizons/harder thresholds before committing to cohort drift.
- **Novelty:** novel
- **Era story:** WPL debutants are the fastest cohort to a signature moment — consistent with many arriving as capped internationals — while IPL debutants' ramp is unchanged since 2008.
- **Viz:** Beeswarm runway: each debutant a dot at their matches-to-first-signature, one swarm per cohort year, the median a takeoff line; clicking a dot replays the actual signature moment as a card.
- **Teaser:** 41% of 2008-10 IPL debutants landed a signature within 5 matches — and 41% of 2021-23 debutants, identical; WPL median = 4 matches vs IPL's 5.
- **Lenses:** career-arcs-cohorts-roster-churn

### Journeyman Network & Loyalty Spectrum *(roster-churn)*
A player-movement graph between franchises — who moves, where, when — with every player on a one-club-loyalist → nomad spectrum.
- **Recipe:** Ordered franchise sequence per player ID (411/809 one-franchise, 183 two, tail to one 9-franchise nomad — verified); edges tagged by mega-auction years; loyalty = 1/distinct franchises or entropy weighted by matches. **Design note:** condition the loyalty share on career length (rookies are mechanically one-franchise) — e.g. players in ≥ their 4th season.
- **Feasibility:** direct · confirmed
- **Novelty:** known-but-underused
- **Era story:** Did the league professionalize into a transfer market? Icon-player one-club identities shredded by mega-auctions; the 2022 expansion forcibly created two franchises made entirely of movers. Is the 5-team WPL already more nomadic per-capita than the IPL at the same age?
- **Viz:** Chord diagram with a season scrubber: franchises as arcs in team colors, player-fibers flowing between; mega-auctions visibly explode the chords; click a fiber to light up one player's full journey (the 9-franchise record-holder as a featured story).
- **Teaser:** Among players in at least their 4th IPL season, one-franchise loyalists fell from 28% (2012) to 14-15% (2019-2025).
- **Lenses:** career-arcs-cohorts-roster-churn

---

## 12. The Era Machine: Detection & Translation

### ★ League Pulse Seismograph (multi-metric changepoint detector) *(era-detection)*
PELT and Bayesian Online Changepoint Detection on chronologically-ordered per-match league series — where the data says the eras actually break, with posteriors instead of hand-drawn era lines.
- **Recipe:** Per-match series (RR, six rate, dot rate, wide rate, chase-won, first-innings total) sorted by dates[0] (**not the season label** — '2020/21' otherwise merges IPL 2020 into 2021); ruptures.Pelt + a ~50-line BOCPD (hazard 1/200); break locations as dates with credible intervals; a penalty sweep gives the era-count-vs-strictness curve. (ruptures/scipy not installed here — pip install or pure-python.)
- **Feasibility:** direct · confirmed — signal verified large relative to noise; 57-76 matches/season supports within-season breaks.
- **Novelty:** novel
- **Era story:** Answers "when did modern T20 begin?" empirically — and the probe already shows the breaks are STAGGERED (six-rate ~2018, wide-rate ~2022/2024, RR 2023-24): the modern era is not one event but a stack of revolutions. This is the spine the whole explorer's era framing hangs on.
- **Viz:** A seismograph: stacked per-metric strips sharing a time axis, detected breaks as vertical fault lines with posterior-probability opacity; a "statistical strictness" dial (the PELT penalty) lets users watch eras merge and split live — 6 eras at loose settings, 2 at strict.
- **Teaser:** League RR 7.98 (2008-10) vs 9.69 (2024-26); six rate nearly doubled, 4.29 → 8.06 per 100 balls — with the breaks landing in different years per metric.
- **Lenses:** era-machine-regime-detection

### Per-Metric Fault Map (break-signature clustering) *(era-detection)*
Formalizes the staggered-revolutions finding: a metric-by-season fault matrix, with metrics clustered by their break signatures to reveal which revolutions travelled together.
- **Recipe:** Extend the Seismograph to ~15 metrics (phase RRs, boundary share, wicket rate, bowler-change frequency, extras, review rate, sub timing, no-balls, chase success at par); binary/probability break vectors per metric; Jaccard/cosine hierarchical clustering. **Corrections:** mask the review series pre-2018; filter replacements to 'match'-type; the wide-rate story is non-monotonic (2022 spike partially reverted before the durable 2024 break) — don't oversimplify the narrative.
- **Feasibility:** direct · **adjusted**
- **Novelty:** novel
- **Era story:** The anatomy of change as a geological record with datable strata: the six revolution preceded the run-rate revolution by five years; the powerplay is where the revolution hit hardest.
- **Viz:** A subway map: each metric a colored line across 2008-2026, break years as stations, co-breaking metrics sharing interchanges; hover a station for before/after values.
- **Teaser:** Powerplay RR rose +2.12 (7.61 → 9.73) from 2008-10 to 2024-26 while death RR rose only +1.44 (9.55 → 10.99).
- **Lenses:** era-machine-regime-detection

### Bridge-Player Chained Environment Index *(era-translation)*
How much of each season-to-season scoring change is environment vs personnel — chaining within-player year-over-year deltas holds talent roughly constant.
- **Recipe:** For every player in seasons t and t+1 (registry-matched; ≥60 legal balls both — sensitivity-test the filter): balls-weighted mean within-player Δ(SR, boundary%, economy) at shared phase mix; chain into an index (2008=100); the gap vs the raw league series = the personnel effect. Shrink deltas by reliability against survivorship (dropped decliners bias returnees).
- **Feasibility:** direct · confirmed — and the 2023→24 probe REVERSES the leading hypothesis: same-player SR moved only +2.3 while the league moved +8.9. **Roughly three-quarters of the 2024 explosion was personnel/usage turnover, not the same players hitting harder.**
- **Novelty:** novel
- **Era story:** The sharpest question about 2024-26 — did batting get better or conditions easier? — answered with the Davenport/chess-inflation chaining method. Also runs on WPL 2023-26 (strong player continuity).
- **Viz:** Dual-line chart: raw league SR vs the same-player chained index with the divergence shaded "personnel effect"; click any season gap for a beeswarm of every bridge player's delta — Kohli's dot among hundreds.
- **Teaser:** The 56 batters with 60+ balls in both 2023 and 2024 gained only +2.3 SR within-player while the league jumped +8.9 (141.7 → 150.6).
- **Lenses:** era-machine-regime-detection

### Micro-Era Tapes (within-season regime detection) *(era-detection)*
Changepoint detection inside each season's match-order series — venue legs, playoff transitions, pitch wear — rendering every season as a color-coded tape.
- **Recipe:** BOCPD on per-match RR/dot rate/totals within each season (hazard tuned for 58-76 points); annotate causes from venue clusters, stage transitions (**the playoff flag is 'stage key present' — only 74/1243 files carry it, exclusively knockouts**), double-header slots. Positive control passes: the 2021 tape must (and does) snap at the India→UAE pandemic seam.
- **Feasibility:** direct · **adjusted** — the "playoffs play 0.5 RR slower" prior is overstated (pooled gap −0.12); venue legs are the dominant fault lines.
- **Novelty:** novel
- **Era story:** "A season" is itself a fiction: 2014 and 2021 were each two different leagues; some apparent season-level breaks may really be venue-leg composition effects — a check on the macro Seismograph.
- **Viz:** Nineteen horizontal tapes stacked chronologically, each strip colored by detected regime with cause glyphs (plane = venue leg, trophy = playoffs); the 2021 tape visibly snapping in two at the pandemic gap is the money shot.
- **Teaser:** 2021 was two leagues in one season: India leg RR 8.41 vs UAE leg 7.71; 2014 repeats the pattern (UAE 7.57 vs India 8.52).
- **Lenses:** era-machine-regime-detection

### Era Translation Factors (Player Teleporter) *(era-translation)*
Davenport-style conversion rates that re-quote any player-season in any other season's environment — what is 2008 Sehwag worth in 2025?
- **Recipe:** From the chained index + phase baselines: per-season multipliers for SR, boundary%, dot%, dismissal rate, economy, applied through the player's own phase mix; bootstrap uncertainty over matches. **Make the z-score/percentile translation the default** — the bridge-player probe shows chained environment factors are far smaller than raw league ratios, so the two variants disagree materially; show the raw multiplier as the naive alternative. WPL↔IPL translation labeled experimental (no shared players; rides on constellation distances). Data fix: Sehwag 2008 = 406 runs at SR 184.5 (validated against official totals), not the pitched 174.
- **Feasibility:** direct · **adjusted**
- **Novelty:** known-but-underused
- **Era story:** The core cross-era product: icons re-quoted in the 2026 environment and 2026 stars deflated to 2008 — which iconic numbers were era artifacts, and which were genuinely ahead of their time.
- **Viz:** The Player Teleporter card: pick a player-season, drag an era dial across 2008-2026 (and into WPL), watch the stat line morph with uncertainty bands and a raw-number ghost; one-click "find their modern twin."
- **Teaser:** Sehwag 2008 (SR 184.5): the naive league-ratio translation re-quotes him at SR ~228 in the 2024-26 environment — the percentile method will say something saner, and that gap is the exhibit.
- **Lenses:** era-machine-regime-detection

---

## Needs external data — enrichment decision list

Five ideas are gated on external joins; four more get optional upgrades. All joins key off Cricsheet registry IDs → Cricsheet's public people.csv (live-verified: 811/811 IPL players carry ESPNcricinfo keys), so **one scrape of ~950 ESPNcricinfo player pages unlocks items 1, 2, and 4 simultaneously, plus birthdates and keeper designations.**

| # | Idea (section) | External need | Named source |
|---|---|---|---|
| 1 | Bowling-Style Phase Shares (§2) | Bowling style per bowler (577 IPL + 96 WPL; top ~300 covers most balls) | ESPNcricinfo profiles via Cricsheet people.csv; cricketdata R package; Kaggle IPL player metadata |
| 2 | Platoon Polarity (§5) | Batting hand + bowling style (~700 IPL + ~150 WPL players) | Same join as #1 |
| 3 | Auction Value-for-Money (§4) | Auction prices 2013+ | Kaggle "IPL Player Auction Dataset — From Start to Now"; OpenDataBay; iplt20.com official results (fuzzy name match on name + season-team) |
| 4 | Homegrown Pipeline Tracker (§8) | Nationality + international debut date | ESPNcricinfo pages via the proven people.csv join — strongest candidate in the catalog |
| 5 | Team Travel Odometer (§10) | City lat/long for km weighting only (hops ship today) | GeoNames / OpenFlights static ~45-row gazetteer (public domain) |

**Optional upgrades (do not gate the core idea):** League-Age Curves & Career Shape Clustering — birthdates for true biological aging (same ESPNcricinfo join); Venue Fingerprints & Twos Culture — boundary dimensions (scattered media/stadium guides; annotation-only, low reliability); Dew Dividend — exact start times for single-match days (ESPNcricinfo match pages); Keeper Inference — external keeper designation for the residual 3.5% of team-matches; Matchup Targeting & Calendar Climate & Dismissal DNA — spin/pace splits via join #1; Spell Fragmentation & Matchup Engineering — captain identity for attribution (Wikipedia/ESPNcricinfo season pages).

*End of catalog — 143 ideas, 15 hero candidates. Companion file: `research/data-profile.md` (per-season ground truth tables).*
