# Experience Blueprint — "Every Ball Ever"

**The definitive build plan.** Synthesizes the locked product decisions with `metrics-catalog.md` (143 verified ideas, 15 ★ heroes), `presentation-options.md` (the chosen "Every Ball Ever" hybrid concept + engineering constraints), and `data-profile.md` (ground truth). Register throughout: **fans first** — every scene lands visually with zero stats background; formulas and caveats live one click deeper in "how we computed this" footnote layers.

---

## 1. The piece in one paragraph

All 316,388 balls ever bowled in the IPL and WPL exist on screen as one living field of light — and they never leave. You start by sketching what you *think* happened to scoring since 2008; the truth diverges from your finger, and then the field assembles: every delivery in the history of both leagues, raining in season by season. You pick your team, and thirty-odd thousand of those points ignite in your colors. From there, ten scroll-driven chapters rearrange the *same* points — into ignition walls, extinction curves, retreating bowling frontiers, rising tides of runs, win-probability worms, constellation maps of two leagues speaking two dialects, rivalry webs, and finally a seismograph that cracks the timeline where the eras really broke. Nothing is a chart *of* the data; everything *is* the data, morphing. The story's thesis — T20 batting attacked earlier, harder, and (this is the shock) at no extra risk, until the game's own physics had to be repriced — builds chapter by chapter, and when it's done the piece hands you the field itself: a filterable sandbox, pre-tuned to your team, where every claim you just read can be re-derived under your own thumb.

### Working-title candidates

1. **Every Ball Ever** — literal, confident, and names the device itself; the URL and the promise are the same thing. (Default.)
2. **Attack From Ball One** — the thesis as a title; the strongest single finding in the data (intent exploded, risk didn't) doubles as an imperative to the reader.
3. **A Natural History of the T20 Run** — the wildlife-documentary register (anchor extinction, dismissal ecologies, era strata) as brand; positions the piece as study, not hot take.

---

## 2. The experience spine

```
COLD OPEN   You-Draw-It (sketch scoring since 2008) → truth diverges → the 316k field assembles
TEAM PICKER 10 IPL + 5 WPL franchises + "neutral" — your balls glow from here on
ACT I  SETUP        Ch 1  The Death of the Sighter          (Batting Revolution I — the thesis)
ACT II ESCALATION   Ch 2  The Last of the Anchors            (Batting Revolution II — an archetype dies)
                    Ch 3  The Counterrevolution              (Bowling — the resistance mutates)
                    Ch 4  The Rising Tide                    (Scoring Environment — the ground moves)
ACT III REPRICING   —     Interlude: The Net Session         (win-probability + expected-runs mechanism widget)
                    Ch 5  What a Ball Is Worth               (Impact & Win Probability + famous-final-over scrub)
ACT IV WIDENING     Ch 6  Two Dialects                       (IPL × WPL — the constellation)
                    Ch 7  The Twelfth Man                    (Rules — the Impact Player natural experiment)
                    Ch 8  The Captain's Brain                (Tactics/Meta — the belief audit: fail, fail, fail, fail, pass)
                    Ch 9  The Living League                  (Duels & Living Structure — persistence through churn)
ACT V  FINALE       Ch 10 The Era Machine                    (regime detection + Player Teleporter)
THE BOWL            The Field Is Yours — full sandbox, pre-filtered to your team, never blank
```

### Why this order (the narrative arc)

- **Setup (Cold open → Ch 1).** The You-Draw-It makes the reader stake a belief before we show anything — the single highest-engagement-per-effort device in the research. Ch 1 then lands the piece's thesis in one chapter: modern batters attack from ball one *at no extra dismissal risk* — skill revolution, not recklessness. Everything after is consequence.
- **Escalation (Ch 2–4).** A widening blast radius, one scale per chapter: the revolution kills a *player archetype* (the anchor, Ch 2), forces a whole *discipline* to mutate (bowling, Ch 3), and finally moves the *ground itself* (par scores, venues, the 200 club, Ch 4). Each chapter answers "and then what?" for the previous one.
- **Repricing (Interlude → Ch 5).** By now the reader has seen that the environment moved; the natural question is "so what do the numbers even *mean*?" The Net Session interlude teaches **both of Ch 5's currencies** as a physical mechanism — the win meter *and* the expected-runs-from-here meter, two dials on the same lookup grid (sliders, presets, no scroll choreography) — and Ch 5 spends that literacy immediately: linear weights, the collapsing price of a wicket, one famous final over scrubbed ball by ball. This is the deliberate placement of the interlude — *just before* first use, never earlier (no dangling pedagogy), never later (Ch 5 would be unreadable without it — and the second dial exists because Ch 5's run-expectancy scenes would otherwise trade in an untaught unit one scene after the interlude solved exactly that problem).
- **Widening (Ch 6–9).** The lens opens outward: a second league that speaks a different dialect (Ch 6), the rule that broke the timeline (Ch 7), the minds making the decisions (Ch 8), and the human fabric underneath the numbers (Ch 9). **Two Dialects deliberately precedes The Twelfth Man**: Ch 7's central evidence is a diff-in-diff with the WPL as the no-rule control, and the control is only legible if the reader has already met the WPL as a full character — not as a footnote summoned to serve an IPL argument.
- **Finale (Ch 10 → Bowl).** The Era Machine is the synthesis chapter: the changepoint seismograph proves the "eras" the whole piece has been narrating are real, staggered, datable objects — then the Player Teleporter turns the whole read into a toy, and the field dissolves into the sandbox. Martini glass complete: authored stem, free bowl.
- **The planted mystery (the 2023 throughline).** The piece's most dramatic number — the 2023 scoring discontinuity — has three true causes, and the piece scripts their reconciliation as a detective spine rather than letting three chapters give three competing accounts. **Ch 4 poses the question and visibly defers it** ("hold that thought — the answer is three chapters away"). **Ch 7 delivers the partial answer** (the rule, with its honest confound note) **and plants the follow-up** ("but was it the same players?"). **Ch 10 closes the case** with the staggered-breaks seismograph plus a one-beat verdict card: *three suspects, all guilty, on different counts — the rule opened the door, new personnel walked through it, and the skill curve had been climbing for a decade.* Three sentences of connective tissue; zero self-contradiction at the climax.

All eight locked arcs appear: Batting Revolution (Ch 1–2), Bowling Counterrevolution (Ch 3), Scoring Environment (Ch 4, seeded in the cold open), Impact & Win Probability (Interlude + Ch 5), IPL×WPL Two Dialects (Ch 6, woven through every chapter), Tactics/Rules/Meta (Ch 7–8), Duels & Living Structure (Ch 9), The Era Machine (Ch 10, seeded in the cold open). All 15 ★ hero metrics from the catalog are placed (map in §5).

### Standing rules (the locked decisions plus the piece-wide rules every scene must obey)

- One persistent WebGL particle field; it never unmounts. Chapters lazy-load their layout buffers. 2.5D orthographic camera only.
- Hybrid rendering contract: GL points + DOM/SVG annotation plane sharing one projection. All names, numbers, and story cards are DOM.
- Every scene lands its point with scroll alone; interaction adds depth, never carries the thesis. No hover-only content. Mobile-first.
- **Reduced-motion rule:** `prefers-reduced-motion` gets **live-rendered end-state jump-cuts** — the GL field renders each scene's final layout with no interpolation. Personalization (the reader's franchise glow) and theming survive for free, and there is zero image payload — pre-baked frames are banned for exactly those two reasons. Every chapter spec below carries a mandatory **fallback** line covering its interaction-carried moments.
- GSAP scrubbing for exactly two set pieces: the opening field assembly and the Ch 5 famous final over. Everything else is stepper-driven.
- Win probability is a precomputed lookup grid, always. No WASM. Corollary, piece-wide: **anything that looks like a computation is a lookup** — null histograms, embeddings, force layouts, and layout buffers are all Python build-time artifacts; the client interpolates and looks up, never fits.
- **Morph budget:** one **controlling morph** per chapter. Every other particle moment is a *subset-highlight* (all sixes lift out, run-out balls fall away — cheap and constancy-preserving) or a 2D scene on the annotation plane. Full-field re-sorts are rationed to the controlling morph so the reader never loses track of what a point means.
- **Demand-mode rendering:** the render loop pauses whenever no morph, scrub, or field interaction is active (invalidate-based frameloop). "The field dims" means *the loop stops*. Idle GPU between scenes is ~zero — this is a 20-45 minute read on mid-range phones, not a 3-minute demo, and the thermal budget is sized for the read, not the demo.
- **Payload ledger:** a standing per-release budget, inventoried per chapter (layouts + new per-point attributes + scene JSON): **≤3MB gz before the cold-open field can assemble · ≤2MB gz incremental per chapter · ≤25MB gz for a full read-through.** Layout positions ship Uint16-quantized on the wire and decode to Float32 GPU-side (no visible cost on a 2.5D ortho field; halves every buffer); group ids pack as Uint16 where cardinality allows. "Chapter payload within budget" is a pass criterion for **every** release, not just R0.
- **WPL framing rule:** the WPL is never "behind." The Season Constellation Map finding is the house framing — *beside the path, not on it*. Any sentence that reads as a deficit gets rewritten as a dialect difference or an open question about a young league. **Corollary — no single-clock WPL beat:** any stat that places the WPL on the IPL timeline must be paired, *in the same on-screen beat*, with a dialect stat that refuses the timeline. Ch 2 is the template — batting archetypes modern, running risk mid-revolution, two clocks at once. This matters doubly because Ch 1's WPL beat stands alone in public from R1 until R4.
- **Glossary rule (hard):** no statistical term of art appears on-screen in main flow or teasers. Every device ships with a stage name *before its chapter's copy is written*; the technical name lives one click deep in the footnote layer. Seeded now: Pareto hull → *"the edge of the possible"* · hazard curve → *"the out-rate, ball by ball"* · diff-in-diff → *"the control group"* · z-score → *"how far above his own era,"* always expressed as a rank or a gap, never as a z.
- **Payoff-card QA:** team-picker payoff cards are strictly template + per-team JSON emitted by the pipeline — never hand-authored per team. The snapshot harness asserts all 16 picker variants (10 IPL + 5 WPL + neutral) exist and are non-degenerate for every chapter, including designed empty-state copy (a young WPL side with no "last anchor" gets authored empty-state language, not a blank card). "16/16 payoff variants pass" is on every release checklist, and every release from R1 onward ships at least one bespoke WPL-picker payoff card.
- **Chapter nav:** a persistent chapter navigation ships from R1. Chapters stand alone by design (the release structure already requires it), so readers can legitimately enter — and leave — at any chapter. Total length is a menu, not a gauntlet; the beat budget (§3) keeps each course short.

---

## 3. The chapters

Format per chapter: one-liner → hero + supporting metrics (★ = catalog hero candidate; **beat budget: hero(s) + max 3 supporting beats in main flow** — everything beyond the budget demotes to the footnote layer or a sandbox tour flag, never silently cut) → controlling morph + subset-highlights (one full-field morph per chapter, per the standing rule) → 2D scenes & widgets → WPL thread → team-picker payoff → **fallback** (the mandatory reduced-motion / no-interaction path) → footnote layer → on-screen teaser numbers (all verified, from the catalog/profile).

---

### Cold Open — "Draw what you think happened"

**One-liner:** Before we show you anything, you commit: sketch the path of IPL scoring since 2008 — then the truth peels away from your line, and every ball ever bowled assembles in front of you.

- **Beats:** (1) Black screen, one axis — and one line of stakes *before* any ask: *"Something happened to cricket scoring. Draw what you think it was."* Then the prompt proper (per RESOLVED #2 — the 200+ totals draw): *"How many times a season does someone put 200 on the board?"* The 2008–2012 segment comes **pre-drawn** (11, 1, 9, 5, 5 — "about six a season") to anchor weak fan intuitions; the reader picks up the pen at 2013 and draws to 2026. Finger or mouse — with an explicit, equally prominent **"just show me"** skip on the sketch screen that jumps straight to the reveal-and-assembly. Nobody is ever gated on drawing. (2) Reveal: the real line (single digits for a decade and a half… then 37, 41, 52, **65**) draws over the reader's sketch; the per-season divergence gap is shaded and quantified **in totals** ("you were {N} two-hundreds too gentle about 2026 — the real number: 65"). **Correct-guess branch (scripted):** a reader whose sketch is roughly right gets celebration-and-escalation, not a flat beat — *"You knew. But do you know WHEN it broke? The eye says 2018 — the year the sixes exploded. The scoreboard says 2023."* Being right feeds momentum into the piece instead of deflating the device. (3) The truth curve detonates: deliveries stream in season by season with a live counter — 2008… 2015… 2023… — until all **316,199** hang as a shimmering field (GSAP scrub set piece #1; the corpus's 189 super-over deliveries live in the footnote layer — never show a number the pixels contradict). Title card over the field. (4) Team picker: 15 crests + "neutral," one tap-screen, its skip exactly as prominent as the sketch's. Your franchise's balls ignite in team color and stay lit for the whole piece; sandbox will open pre-filtered to this choice. Skippable, never gates content. The sketch **and** the team pick persist to localStorage from R1 day one — Ch 4's callback, shared-link arrivals, and returning sessions all depend on it.
- **Metrics used:** T20 Consumer Price Index (the truth curve; also the site-wide deflator from here on).
- **WPL thread:** the WPL's 88 matches arrive **as their own constellation** — deliberately apart, never merely last in a queue — with one line of copy that names the deliberateness (*"…and then a second league assembles: its own body of light"*), so *separate-not-late* is authored, not inferred. The first image of the Ch 6 framing.
- **Fallback:** reduced-motion / keyboard / screen-reader readers get the "just show me" path by default — the truth curve and the assembled field render as live end-state jump-cuts with the counter narrated as text; the draw canvas is never required for entry.
- **Footnote layer:** what counts as a ball (super overs excluded, wides/no-balls conventions), where the data comes from (Cricsheet), season-label normalization.
- **Teasers on screen:** `316,199 deliveries · 1,331 matches · 19 IPL seasons + 4 WPL seasons · 938 players` · "200-run innings per season: about six a year (2008–12) → 65 (2026)".

---

### Chapter 1 — The Death of the Sighter *(Batting Revolution I — the thesis)* — ships in R1

**One-liner:** Batters used to spend ten balls "having a look." Now they attack ball one — and here's the shock: they don't get out any more often doing it.

- **Hero metric:** ★ **Death of the Sighter** (Kaplan-Meier survival / hazard-of-dismissal by balls faced — on screen it is *"the out-rate, ball by ball,"* per the glossary rule) — the strongest single verified finding in the corpus: first-10-ball SR exploded 108.0 → 135.3 while per-ball dismissal hazard on those balls stayed flat (5.04% vs 4.93%). Skill revolution, cleanly separated from risk appetite. **Thesis scope, stated here once for the whole piece:** the flat out-rate is a *first-ten-balls* finding — batters attack from ball one at no extra risk, **and where risk *did* rise, later in the innings, it was priced and paid on purpose** (Ch 5 publishes the price list). One clause; the whole piece is inoculated, and the skill-revolution claim gets sharper, not weaker.
- **Supporting metrics (curated — beat budget: 3):**
  - **Ignition Curve & Early Intent** — SR as a function of balls-faced; the drag-racer visual; the early ramp grew faster than overall SR (+25% vs +21%).
  - **Aerial Risk Ledger** — braver AND better: aerial attempts per 100 balls 7.3 → 11.4 *and* execution 58.7% → 67.3%.
  - **Six-Hitting Democratization** — the six stopped being a specialist weapon: players with ≥10 sixes 18 (2008) → 58 (2026); top-10 hitters' share of league sixes 35.9% → 28.1%.
- **Controlling morph:** the free field pours into the **ignition wall** — every ball positioned by (batter's balls-faced-so-far → x, season → y), colored by runs scored; the reader literally watches the "slow start" region brighten across two decades. **Subset-highlight:** all sixes lift out of the field and stack into per-season **firework columns** (2008: three tall rockets; 2026: a skyline firing), then settle back. The field re-sorts exactly once this chapter; the over-clock re-sort is cut per the morph budget (its finding survives below).
- **2D scenes / widgets:** **the out-rate strip** — layered era curves of *how often batters get out, ball by ball*, with 2008's ghost always visible (DOM/SVG; the words "hazard curve" live one click deeper) — the one chart in the chapter, because the flat-out-rate punchline needs a precise axis. Tapping a ball count shows which real batters most defied that out-rate.
- **WPL thread (two clocks, one beat — house rule):** **the WPL is already moving, and not along the IPL's track.** Its first-10-ball SR (110.5) sits where the IPL's 2008 curve did — *but the engine driving it is nothing 2008 ever had:* 46.8% of its runs come in fours (modern IPL: 33.9%), a four-led attack the men's league never played at any age. The single-clock "live broadcast of IPL 2008" framing is banned; "already moving" is the subject of the sentence, not the afterthought. WPL curve drawn as a peer line, never a laggard annotation. (This beat matters disproportionately: it is the only published WPL narrative from R1 until R4.)
- **Team-picker payoff:** your team's balls stay lit through every morph; end-of-chapter card: *your franchise's ignition curve by era* + its fastest starter ever (first-10-balls SR, min 100 balls). **WPL pickers get a bespoke card from R1 day one:** *your league's ignition curve, four seasons in — already climbing faster than the IPL did at the same league age* (the Maturity Clock, planted three chapters early).
- **Fallback:** reduced-motion renders the ignition wall and firework columns as end-state jump-cuts; the out-rate strip is static-legible by construction; no beat in the chapter requires a tap.
- **Footnote layer:** KM estimator and censoring rules (retired hurt/out), wides excluded from balls faced, why hazard ≠ strike rate, sample sizes per era band; aerial-attempt proxy caveat (caught includes edges; stable-noise argument); **The Over as a Clock Face** (demoted from main flow by the beat budget — a small 2D radial, not a field morph: 2008 overs ran quiet-loud-quiet, ball-1 RR 7.34 → 9.20; the sighter died even *inside* the over).
- **Teasers:** `First 10 balls: SR 108 → 135, dismissal risk unchanged` · `Aerial attempts +56%, execution +9pts` · `≥10-six players: 18 → 58` · `WPL, four seasons in: climbing faster than the IPL did at the same age`.

---

### Chapter 2 — The Last of the Anchors *(Batting Revolution II — an archetype goes extinct)* — ships in R2

**One-liner:** A whole species of batter — the careful accumulator who "held the innings together" — has been hunted out of the league, and the risky single died with him.

- **Hero metrics:** ★ **Anchor Extinction Index** (share of a season's balls consumed by long, slow, low-boundary innings — a population-decline chart: 14.8% → 8.5%, a 43% collapse) and ★ **Run-Out Extinction Curve** (run-outs 12.3% of dismissals in 2008 → 4.6% in 2026 — the death of the risky single, the most direct behavioral fossil in the data).
- **Supporting metrics (curated — beat budget: 3):**
  - **Ball-by-Ball DNA (archetype occupancy)** — the extinction stated in one number: batter-seasons striking under 120 were 38.7% of the league in 2008-10, **2.4%** now.
  - **Gear-Shift Detector** — the three-act innings (see off → consolidate → launch) deleted; two-act innings 33.5% → 24.5%; modal long innings now one-gear flat-max.
  - **New-Batter Tax** *(the chapter's sole coda — one honest counter-beat, not two)* — what T20 *couldn't* kill: the post-wicket scoring dip never went away (−1.22 → −1.40 RPO vs par) even as incoming batters' first-5-ball SR jumped 101 → 127. The tax is structural, not behavioral.
- **Controlling morph (with its curation rule written into the pipeline contract):** balls regroup into **innings worm-threads** — but never thousands of overlapping polylines. The scene is the **par worm + K exemplar anchor worms per season** (slow grey worms crawling against the frenetic par line), with every remaining ball present as a **low-alpha density haze** behind them — still "every ball on screen," honoring the device, without the hairball. Season by season the grey worms thin out (species-decline framing). **Subset-highlight:** run-out dismissal balls flash red and fall out of the field along the extinction curve. Closing beat (annotation plane, no re-sort): the surviving anchors of the final seasons individually named as they blink out.
- **2D scenes / widgets:** the conservation-chart (population count with "last surviving anchors" profiled); the aftershock strip for the New-Batter Tax (per-ball RPO after a wicket, one line per era — the dip rises in level but never fills in).
- **WPL thread:** the anti-lazy-narrative beat, stated on screen: **the WPL was born post-anchor** (anchor-ball share ~9-10%, already at modern-IPL levels) — but its run-out share (7.0%) sits where the IPL was circa 2014-17. One league, two clocks running at once: batting archetypes are modern, running risk is mid-revolution. This is the chapter that teaches the reader the WPL can't be placed at a single point on the IPL timeline — pre-work for Ch 6.
- **Team-picker payoff:** *"Your last anchor"* — the final qualifying anchor innings in your franchise's history, named, dated, and replayable as a worm (e.g. the innings card shows balls, SR, boundary %, and what par was doing that day). Young WPL sides with no qualifying anchor get the designed empty state (*"born post-anchor — your franchise never had one"*), which is itself the chapter's WPL point.
- **Fallback:** the worm scene jump-cuts between its per-season end states; the red run-out cascade renders as its final fallen layout; the replayable worm card degrades to a static innings chart.
- **Footnote layer:** anchor definition and threshold sensitivity sweeps (the catalog mandates them); why SR < 0.85 × phase-par rather than a raw cutoff; run-out decomposition (striker vs non-striker, phase); which of these effects is intent vs fitness (honestly multi-causal); **Break-Even Running** (demoted by the beat budget — running got *safer at constant aggression*: run outs per 1,000 balls halved 6.4 → 2.8 while the twos rate held flat; the mechanism note behind the hero's extinction curve); **Milestone Braking Index** (nerves survive too: batters ease off *more* approaching fifty, Braking Index 0.989 → 0.930 — a lovely nerd-layer nugget, deliberately not a second coda).
- **Teasers:** `Anchor balls: 14.8% → 8.5% of the league` · `Sub-120-SR batter-seasons: 38.7% → 2.4%` · `Run-outs: 12.3% → 4.6% of dismissals` · `The one survivor: the post-wicket dip never healed`.

---

### Chapter 3 — The Counterrevolution *(Bowling — the resistance mutates)* — ships in R2

**One-liner:** Bowlers didn't lose the war — they abandoned the old map. Containment as an identity is extinct; what replaced it is stranger and braver.

- **Hero metric:** ★ **Attack-Containment Frontier Drift** — the Pareto frontier of bowling strike rate vs economy retreating season by season; the bowlers'-eye view of the scoring explosion. Bowler-seasons with economy under 7.0: **49 of 169 (29%) in 2008-10 → 4 of 267 (1%) in 2023-26**.
- **Supporting metrics (curated — beat budget: 3):**
  - **Dot+ (era-normalized dot manufacturing)** — dots are a deflating currency: league dot rate 37.6% → 33.0%; a 40% dot rate in 2026 is a different achievement than in 2009.
  - **Dismissal DNA** — fingerprint evidence bowlers stopped attacking stumps and started attacking the long boundary: bowled+lbw 27.4% → 21.3%, caught 65.2% → 74.1%, stumped collapsed 4.2% → 1.9%.
  - **Extras Weather / the Death-Wide Tax** — the arms race made flesh: death-over wides **doubled** (3.3 → 6.7 per 100 balls) as bowlers chased wide-yorker extremes.
- **Controlling morph:** every ball condenses toward its bowler-season's coordinate on the **economy × strike-rate plane** — bowler-seasons as dense clouds, and on the annotation plane **"the edge of the possible"** (the Pareto hull, named one click deeper per the glossary rule) visibly retreating as seasons scrub (Gapminder treatment; ghost trail follows one great across 15 frontiers). **Subset-highlight:** all 13k+ wicket balls stream out into **dismissal-kind rivers** (streamgraph made of the actual wicket balls), then return.
- **2D scenes / widgets:** the **dot-grid scene** (2D, annotation plane): a 2009 innings and a 2026 innings as side-by-side 120-cell grids, dark dot-cells eroding; the death-wides leak gauge.
- **WPL thread (two clocks in the same breath — house rule):** the WPL's frontier still *has* the containment corner — its dot rate (38.5%) sits where the IPL's did in 2009 — **and, in the same on-screen beat, the stats that refuse the timeline:** it is structurally **a spinner's league** (stumped 5.2-7.9% of dismissals every season vs IPL's 1.4% — teased here, full treatment in Ch 6); its death-wide rate (2.8) shows the wide-yorker arms race is a *men's-league phenomenon*, not a maturity stage; and **dots still buy wickets there** — the **Dot-Ball Crack Ratio** lands here, where it does its real work: middle-overs crack ratio 1.11 in the WPL vs the IPL's defused 0.84, which is precisely *why* IPL bowling economies inflated even as bowler skill grew. A different ecosystem, not an earlier one.
- **Team-picker payoff:** *your franchise's gravity-defier* — the bowler-season that beat its era's tide by the most (best True Economy, computed even though the headwind exhibit lives one click deep), with the frontier scene re-centered on your team's dots.
- **Fallback:** the frontier scene jump-cuts between per-season end states with the hull redrawn per step; the dismissal rivers render as their final streamgraph; the dot-grids are static by nature.
- **Footnote layer:** economy conventions (byes/legbyes excluded, documented project-wide); **True Economy + True Wickets per 24** (demoted by the beat budget — the headwind chart: raw economy drifts up with the league tide; a 7.5 death economy went from par to 1.9 RPO *better* than par); **Phase Fingerprint** (death-specialist emergence: 0% → 17.3%, peak 20.6%, then a recent slump — the specialist rose and is already being eroded); FIB (field-independent bowling) as the deep layer — caught rose 59.9% → 72.3% and run-outs collapsed, so raw bowler stats are *less* skill-reflective in 2026 than 2008, and FIB strips exactly that drift; the refuted econ~SR correlation sub-claim (+0.12 → +0.03 — the hull, not the correlation, carries the story); Squeeze Retention's bounce-back null (+4.0pp then, +3.9pp now — modern "B-options" don't stop the bleed any better); crack-ratio construction notes.
- **Teasers:** `Economy under 7: 29% of bowlers → 1%` · `Death wides doubled` · `Stumpings: 4.2% → 1.9% (WPL: 6.8%)` · `Dots still kill in the WPL; the IPL defused them`.

---

### Chapter 4 — The Rising Tide *(Scoring Environment — the ground itself moves)* — ships in R3a

**One-liner:** While batters and bowlers fought, the water level rose: the score that used to win now loses, the powerplay caught fire, and records that stood for a decade fell twice in nineteen days.

- **Hero metrics:** **Threshold Exceedance Curves (the 200 Club)** — P(first innings ≥ 200): **7.7% → 41.9%**, and 52% in 2026 alone; the 2023 discontinuity is the most dramatic single number in the dataset — paired with **Par-Score Drift** — the total that wins exactly half the time climbed 165 → 195; 230+ totals went 11/11 defended in 2023-26. The hero beat closes on **Record Half-Life** (fused in — the era told through falling records: the highest-total record, RCB's 263 from 2013, stood 3,991 days, then fell twice in 19 days in 2024).
- **The planted mystery (an authored beat, on screen):** the chapter shows the 2023 cliff in full drama and then *visibly refuses to explain it*: **"Something snapped in 2023. Hold that thought — the answer is three chapters away."** Ch 7 delivers the partial answer (a rule); Ch 10 delivers the verdict (three causes, reconciled). The piece's biggest number becomes its detective spine instead of three competing explanations.
- **Supporting metrics (curated — beat budget: 3):**
  - **T20 CPI** *(callback)* — the reader's own cold-open sketch returns, now annotated with everything learned since; first-innings RPO 8.03 → 9.55, index 119. **No-sketch variant (specced now):** readers who skipped drawing, arrived by shared link, or return in a later session get the authored line — *"here's what most readers drew"* — from aggregated or authored data; the beat never depends on a sketch existing.
  - **Powerplay Exploitation Premium** — the extra powerplay runs came *free*: PP run rate 7.60 → 9.48 at identical wicket cost (1.54 vs 1.52 per 36 balls).
  - **Pitch Homogenization Index + Venue Fingerprints** *(fused beat, the contrarian twist)* — the flat-pitch era did NOT flatten the country: between-venue variance share nearly tripled (~11% → ~27%); Chinnaswamy 197 vs Chepauk 174 persists. Venue identity is *growing*.
- **Controlling morph:** balls stack into **innings-total columns per season** and a rising **par waterline** climbs the wall, visibly drowning totals that used to be safe — "the water level" is the chapter's controlling image, and its only full-field re-sort.
- **2D scenes / widgets:** the **20-over × season phase heatmap** (2D, annotation plane — the powerplay corner igniting decade by decade); the **venue divergence cone** (2D — per-ground par strands fanning apart); the milestone light-beam ridgeline (season total distributions crossing 180/200/220/250 thresholds); the records ticker (scrub 2008 → 2026, standing records shatter on a board — cheap, delightful, extremely shareable).
- **WPL thread (two clocks, one beat — house rule):** on the calendar clock the WPL's exceedance curve sits between IPL 2008 and 2015 — **and in the same beat, the clock that refuses the comparison: at the same league age its tide is rising faster than the IPL's did** (avg first innings 157 → 169 in four seasons), and it is rising *four-led* — a flood built along the ground, not over the rope. A 200 in the WPL is still an event; the chapter shows one (2026 has five).
- **Team-picker payoff:** *your home ground's tide* — par at your venue by era, plus its fingerprint radial ("Chepauk keeps its character; Chinnaswamy is the flood plain"). Neutral pickers get the full venue map of India.
- **Fallback:** the waterline morph jump-cuts to per-era end states; the records ticker degrades to a static "records that fell" board; every heatmap and ridgeline is 2D and static-legible.
- **Footnote layer:** the par logistic model spec and the full-first-innings filter (200+ counts shift ±1 with it); D/L exclusions; the ~60-string venue canonicalization table; why record lifespans need a stationary-environment null (records get monotonically harder); **Phase Economy Map** (demoted by the beat budget — the innings became phase-agnostic: death-minus-PP RPO spread compressed 1.98 → 1.18; by 2026 the powerplay, 10.10, nearly matches the death overs, 10.79).
- **Teasers:** `P(200+): 7.7% → 41.9% — 52% in 2026` · `Par: 165 → 195` · `PP runs became free: +1.9 RPO at zero extra wicket cost` · `RCB's 263 stood 3,991 days, then fell twice in 19 days`.

---

### Interlude — The Net Session *(win probability AND expected runs, taught by hand)* — ships in R3b

**One-liner:** Before we tell you what a ball is *worth*, feel it: drag the required rate, spend a wicket, and watch two meters move under your finger — how many runs are usually left here, and how often teams win from here.

- **What it is:** a Ciechanowski-style mechanism figure, deliberately placed *between* Ch 4 and Ch 5 — the exact moment the reader needs it and not a scroll earlier. Sliders for overs left, wickets in hand, and runs needed read from the **precomputed (over × wickets × required-rate) → P(win) lookup grid** built from all 1,331 matches (never a live model — locked decision). **Two dials, deliberately (the no-dangling-pedagogy rule applied to itself):** beside the win meter sits the **"expected runs from here" meter** — same lookup-grid machinery, arguably more intuitive than win probability — so that when Ch 5 prices things in expected runs one scene later, both of its currencies have already been felt by hand. Preset buttons carry the message for the 85% who never touch a slider, quoting both currencies: *"from this exact spot, teams usually get 62 more runs — and win 31% of the time."* Presets: *"Dhoni, 2011 final" · "needing 10 an over at halfway, 2010" · "the same chase, 2025."* That last pair is the point: **the same scoreboard, two different truths** — chases needing 9+ RPO with 60 balls left won 24.3% of the time in 2008-12 and 31.8% in 2023-26.
- **No particle morphs here** — the field dims to a resting starfield behind the widget, **and per the demand-mode rule the render loop stops** (dimmed means paused, not idling). The interlude is intentionally a change of texture (prose + one figure) so Ch 5's return to the field lands harder.
- **WPL thread:** a league toggle on the grid — WPL chases carry more late drama (its photo-finish rate is the highest in the dataset; the full stat lands in Ch 6). **Minimum-evidence mask (88 matches is not 1,331):** WPL cells below an n threshold render hatched/blurred with an explicit *"not enough WPL cricket yet"* state — the young-league honesty is itself on-message, and no smoothing artifact ever presents as a finding.
- **Fallback:** the widget is slider- and button-driven, not motion-driven — reduced-motion loses nothing; presets are keyboard-accessible buttons and the meters are plain DOM numbers.
- **Footnote layer:** grid construction (era-windowed models, D/L handling via target.overs, tie rules for 26 no-winner matches), calibration plots, why wickets dominate early and rate dominates late, the WPL evidence-mask thresholds.
- **Teasers:** `Same chase, +7.5 points of win probability across eras` · `Every number here: a lookup, not a guess — 1,331 matches remember`.

---

### Chapter 5 — What a Ball Is Worth *(Impact & Win Probability — everything gets repriced)* — ships in R3b

**One-liner:** A dot ball costs more than it ever has, a single now *loses* expected runs, wickets appreciated faster than inflation — and one famous final over, scrubbed ball by ball, shows you why.

- **Hero metrics:** ★ **Win Probability Added (WPA) per ball** — every delivery in history tagged with how much it swung the match; a 170-190 total was defended 74% of the time in 2008-10 and **38%** in 2023-26 — the same scoreboard lost 36 points of win probability across eras — and ★ **Run-Expectancy Surface Drift** — where the revolution actually lives: the value of wickets in hand has collapsed (the 3rd wicket's marginal cost at over 7 fell from ~12 expected runs to **~0.4**). Both currencies were taught one scene ago — the Net Session's two dials exist precisely so this chapter never trades in an untaught unit.
- **Supporting metrics (curated — beat budget: 3):**
  - **Cricket Linear Weights** — the price board, framed plainly first (*"what a team usually still gets from here"*): the dot deepened (−0.85 → −1.12), and the single **flipped from value-neutral to value-losing** (−0.01 → −0.27) — in the modern IPL, rotating strike literally loses expected runs. (This is where Ch 2's dead anchor gets its economic autopsy.)
  - **Wicket Value Index** — the counterweight: a wicket removes MORE expected runs now (3.99 → 5.30, +33%), outpacing run inflation. Wickets appreciated; caution didn't.
  - **Finisher Rating / the moving cliff** — the invention of a job: a chase needing 8-10 RPO with 5 overs left was won 54.8% of the time in 2008-10, **85.0%** now; the "fatal RRR" moved from ~10 to ~12.
- **Set piece (locked, #2 of 2) + controlling morph:** the **famous final over scrub** — proposed default: **the 2019 final, Malinga defending 9 off the last over, MI by 1 run** — its six balls enlarge out of the dimmed field and scrub ball-by-ball while the WP worm draws alongside on the annotation plane (fans feel the worm before any formula appears). Then the chapter's controlling morph: the field re-forms as the **RE surface** — balls arrayed in a 20-over × 10-wicket grid, colored by expected runs-to-come, morphing 2008 → 2026 with a difference lens (the middle overs inflate first). The era-swap morph is cut per the morph budget; its exhibit survives one click deep.
- **2D scenes / widgets:** the outcome price-board (each outcome a ticker floating up/down with the season slider).
- **WPL thread:** the WPL gets honest surfaces, not fake ones — **gated by the same minimum-evidence mask as the interlude** (cells under the n threshold render hatched with *"not enough WPL cricket yet"*; where the mask bites hardest, WPL shows as observed-outcome dots overlaid on the IPL grid rather than a fitted surface of its own). The WPL finisher cohort is forming live (RRR 8-10 chases won 75% — between the IPL's two eras, on its own trajectory).
- **Team-picker payoff:** *your team's most valuable ball ever* — the single biggest WPA swing in franchise history, tappable to replay its over; runner-up list one click deeper. The scrub itself is **one canonical over for everyone** — the shared-culture moment (resolved in open question #1; per-team alternate scrubs multiplied the piece's most expensive asset type, and this data-driven card already carries the personalization).
- **Fallback:** the final-over scrub degrades to a **six-panel sequential strip** — one panel per ball with its WP-worm segment beneath; the RE-surface morph jump-cuts between its 2008 / 2026 / difference end states; the price board is DOM.
- **Footnote layer:** the WP model spec (era features are mandatory — identical totals carry wildly different WP by era; monotonicity constraints; D/L and super-over handling), WPA crediting rules (striker/bowler), RE288 smoothing (GAM pooling; single-season cells are n=26-77), linear-weights derivation from RE state changes, Leverage Index as the byproduct that powers "decision ball" flags in the sandbox; **Era-Indexed Chase Difficulty Surface** (demoted by the beat budget — needing 30-42 off the last 24 with 5+ wickets went from 69% to 88%; the heatmap with iconic chases crawling across it lives here and as a sandbox view); **Era-Swap Counterfactual Replay** (demoted — the same innings re-priced under another era's physics: Gilchrist's 2008 hundred as a massive WP swing then, "a good day" now; a natural sandbox tour flag).
- **Teasers:** `A 170-189 total: 74% safe then, 38% now` · `The single: −0.01 → −0.27 expected runs` · `A wicket: +33% more expensive, faster than inflation` · `The 3rd wicket at over 7: ~12 runs → ~0.4`.

---

### Chapter 6 — Two Dialects *(IPL × WPL — beside the path, not on it)* — ships in R4

**One-liner:** The WPL scores at IPL-2022 rates with an IPL-2008 outcome mix — it isn't N years behind the men's league; it's speaking a different dialect of the same language.

- **Hero metrics:** ★ **Season Constellation Map** — the piece's framing device made literal geometry: each season placed by the actual distance between its per-ball outcome distributions; the WPL's stars sit **beside** the IPL's chronological path, not on it (same run rate as IPL 2022, outcome mix nearest IPL 2008) — and ★ **League Maturity Clock** — the recurring device gets its home chapter: align both leagues on seasons-since-founding and the WPL's year-4 run rate (8.54) equals what took the IPL **fifteen years** to reach.
- **Supporting metrics (curated — beat budget: 3):**
  - **Run DNA + SR Inflation Decomposition** *(fused beat: the different engine)* — the WPL is not "fewer boundaries," it is **four-led**: 46.8% of its runs come from fours (vs modern IPL's 33.9%), six-share 15.5% vs 29.0%, with weaker rotation — a structurally different scoring engine, not a scaled-down copy.
  - **Stumping Signature** — the WPL is structurally a spinner's league: stumpings 5.2-7.9% of dismissals every season vs IPL 2026's 1.4% — a genuinely different dismissal ecology (paid off from its Ch 3 tease).
  - **Photo-Finish / Thriller Rate** — the payoff stat: the WPL is **the tightest league in the dataset** (photo-finish rate 24.1% vs IPL ~16-17%).
- **Controlling morph:** the **ladder of abstraction in reverse**: the full field condenses, season by season, into 23 glowing **season-stars** — the reader watches 316k balls *become* the constellation — IPL stars strung on a chronological worm, WPL stars beside it with dotted nearest-neighbor threads. **The phase toggle swaps between per-phase embeddings precomputed in the Python pipeline and Procrustes-aligned to the all-phase master layout** — never a live re-embed (MDS is invariant under rotation/reflection, so a client-side re-fit could legitimately flip the WPL's stars to the other side of the IPL path and destroy the piece's single most important image). Stars move minimally and coherently between toggles; the client only interpolates tiny per-phase JSON.
- **2D scenes / widgets:** the **DNA double-helix** as a 2D scene on the annotation plane (two bar-columns of run-type composition, four-led vs six-led engines side by side — the particles stay in the constellation behind it); the maturity-clock dual dial (rotate to snap both leagues to the same league-year; every panel in the chapter re-aligns); the batting-ladder (rungs 1-11 sized by run share, league × era).
- **WPL thread:** *is* the chapter — but note what it is not: it is not the WPL's only home. Every other chapter carries its thread; this one changes the reader's frame from "comparison" to "two dialects."
- **Team-picker payoff:** IPL pickers meet their **sister franchise** (MI→MI-W, RCB→RCB-W, DC→DC-W, GT→Gujarat Giants) with a shared-city card; WPL pickers get the inverted experience — their team is home turf here, and their card names the IPL season-star nearest their team's style. The five shared venues (Chinnaswamy, Brabourne…) power a same-ground comparison card.
- **Fallback:** the constellation renders as its aligned end states per phase preset; the dual dial degrades to preset league-year buttons; helix and ladder are static 2D.
- **Footnote layer:** Jensen-Shannon divergence + MDS method (23×23 matrix, phase-weighted) and the Procrustes alignment of per-phase variants; the RR formula correction (all runs / legal balls); **Star Gravity + Competitive Balance Barometer** (demoted by the beat budget — the two-truths-at-once pairing is nerd-register nuance: apparent WPL star-dependence is a pool-size illusion at matched percentiles, *yet* its title race is real duopoly, normalized win-HHI ~2.4× the chaotic early IPL); **Batting Depth Ledger** (demoted — WPL positions 7+ scored 15.3% of all runs in 2025, the highest single season in either league, with the honest opportunity-vs-skill decomposition); Gini threshold sensitivity (0.61 unfiltered vs 0.39 at ≥30 balls — why matched percentiles are the honest cut); Powerplay Fear Index (the WPL sits at the *old IPL equilibrium* of 0.92 — the question is whether it needs a structural shock of its own); Twos Culture (smaller ropes convert twos into fours — the running game is thinner for geometric reasons, a live rope-length policy debate).
- **Teasers:** `WPL year 4 = IPL year 15, by run rate` · `Outcome mix nearest: IPL 2008. Run rate equal to: IPL 2022. Both true.` · `46.8% of WPL runs come in fours` · `Tightest league in the dataset: 24.1% photo-finishes`.

---

### Chapter 7 — The Twelfth Man *(Rules — the natural experiment)* — ships in R4

**One-liner:** In 2023 the IPL let teams field a twelfth player — and scoring broke a fifteen-year ceiling overnight. The WPL, with no such rule, is the control group that lets us say how much was the rule.

- **Mystery handoff (in):** this chapter opens by picking up what Ch 4 planted — *"Chapter 4 showed you the cliff. Here is the suspect."*
- **Hero metric:** ★ **Impact Player Natural Experiment** — on screen it leads as **"the control group"** (the one-liner already does this correctly; "diff-in-diff" lives one click deeper, per the glossary rule): IPL run rate was range-bound 7.5-8.7 for fifteen seasons, then 8.99 → 9.56 → 9.63 → 9.88 from the exact season of the rule; the WPL moved only 8.08 → 8.54 over the same window — **a ~1 RPO gap opening at the treatment date**, presented honestly as evidence weight, not proof (pitches and balls changed too).
- **Supporting metrics (curated — beat budget: 3):**
  - **License Index** — the psychological subsidy measured: at identical match states (≥4 down, overs 7-16), SR jumped 117.7 → 127.5 while dismissal rate *fell* — extra aggression at zero risk premium.
  - **Rule-Change Event Study with Placebo Cursor** — the reader drags the "intervention date" anywhere on the timeline and watches the discontinuity estimate re-fit live; the true rule date pops out of the grey placebo cloud. The verified twist on the mechanism: the **top order took the license** (positions 1-3 SR +13.0% vs +11.0% for 6-8).
  - **Impact Player Playbook Decoder** — the league visibly learning the rule: 53% of 2023 subs at the innings break → 35% by 2025 as teams held the card for mid-innings strikes.
- **Mystery handoff (out):** before it closes, the chapter plants the follow-up on screen: *"So the rule opened the door. But was it the same players scoring faster — or new ones? Hold that too; the last chapter settles it."* (Ch 10's bridge-player index is the answer.)
- **Controlling morph:** the field splits into **twin rivers** — IPL and WPL run-rate flows built from the balls themselves, running parallel for the shared window and visibly diverging at 2023. **Subset-highlight:** the 584 deliveries carrying Impact-sub events glow as sparks entering the IPL river.
- **2D scenes / widgets:** the **license surface** split-screen as a 2D scene (aggression over wickets-down × overs-left, 2022 left, 2024 right, the diff glowing where the license was granted); the placebo cursor (the chapter's signature interactive — spectacular on tap, per the Tse rule); the sub-timing Sankey (toss → innings → timing → role → outcome, animating season by season).
- **WPL thread:** structural, not decorative — the WPL *is the control arm*. Stated framing: the WPL's slower, rule-free trend is what makes the IPL's discontinuity readable at all; without it this chapter would be an anecdote.
- **Team-picker payoff:** *your team's playbook* — favorite sub pattern (bat vs bowl reinforcement), most-used impact player, timing histogram vs league meta, and whether the pattern won matches. WPL pickers get the control-arm card: *your league is the reason anyone can say what the rule did.*
- **Fallback:** the placebo cursor degrades to the true-date fit drawn with the placebo cloud rendered statically around it; the twin rivers jump-cut to their diverged end state; the Sankey steps by season buttons.
- **Handoff to Ch 8:** the closing beat — *teams learned the rule in two seasons. Learning is what modern franchises do. Next: an audit of everything else captains learned.*
- **Footnote layer:** diff-in-diff assumptions and confounds (pitch curation, ball changes, secular intent drift visible from the 2018 six-rate break); the replacements schema (557 impact subs; activation-vs-naming inference; concussion/role subs excluded); the honest null from Batting-Order Fluidity — the rule added a 12th name **without rewiring batting-order thinking** (entry entropy flat 1.12 → 1.10); **Tail Exposure Rate** (demoted by the beat budget — the safety net is about tail *quality*, not exposure, flat at ~58%: top-3 SR jumped 131 → 155 while the tail batted no more often); **Part-Timer Extinction / the bowling dividend** (demoted — the rule's other face: bowlers per innings jumped 5.78 → 6.09 the year it arrived).
- **Teasers:** `15 seasons range-bound. Then: 8.99, 9.56, 9.63, 9.88` · `WPL (no rule): +0.46 over the same span` · `Aggression up, risk down — at identical states` · `2023: 53% of subs at the break. 2025: 35%. Teams learned.`

---

### Chapter 8 — The Captain's Brain *(Tactics/Meta — the belief audit)* — ships in R5

**One-liner:** The analytics era rewired what captains — and commentators — believe, and the data can now grade every belief. The verdict, read out like a report card: doctrine moved faster than evidence… except once.

**Structure: a report card with mixed verdicts — fail, fail, fail, fail, pass.** Each beat is a belief, an audit, and a grade; the one vindicated doctrine is saved for last so the chapter has a shape, not a list. (Opening handoff from Ch 7: *learning is what modern franchises do — so let's audit everything else captains learned.*)

- **Hero metrics:** ★ **Toss Revolution** *(belief #1 — FAIL)* — the single clearest behavioral revolution in the data: field-first went 43% → 77% while the chase win rate went 54% → **53%** — the doctrine hardened; the evidence never did — and ★ **DRS Review Economics** *(belief #2 — FAIL)* — reviews as bets: 988 IPL reviews, 29.6% upheld; doubling the allowance in 2022 nearly doubled the volume **without improving accuracy**.
- **Supporting metrics (curated — beat budget: 3):**
  - **Spell Fragmentation & the Re-entry Tax** *(belief #3, fused with its price tag — FAIL)* — rhythm captaincy dissolved into matchup chess: same-end one-over spells 54.7% → 64.1% (the **WPL more fragmented still, 75.3%**) — and fragmentation is not free: a stable ~0.2 RPO leak every time a bowler is brought back cold, a constant, unexamined tax.
  - **Momentum Myth-Buster** *(belief #4 — the pundits' beliefs, audited — FAIL; moved here from Ch 9, where it had no rivalry to belong to)* — the falsifiable panel: pick a conditional claim ("a boundary makes the next boundary likelier") from a **curated menu of 5-10 claims × era bands**, and watch the observed needle against its shuffled-null histogram. **All null histograms are precomputed at build time in Python** (a few KB of JSON — a lookup, not a computation, per the standing rule; no free-form claim-builder, no client-side permutation test). Momentum's raw edge is already fading era over era (lift 1.19 → 1.17).
  - **Required-Rate Responsiveness** *(belief #5 — the PASS, the deliberate contrast beat)* — the one doctrine the data vindicates: the chase pacing curve flipped from up-sloping to down-sloping; modern chases kill the game inside the powerplay so the required rate never rises. Modern chase theory genuinely works — which is what makes the other four grades sting.
- **Controlling morph:** the **ladder-of-abstraction condensation**: 316k balls collapse into their 1,331 **match-dots** (the reader watches matches *become* the unit) — then the match-dots split into two streams at every toss (bat/field), the field-first river swelling after 2016 while the belief-reality wedge shades open on the annotation plane. **Subset-highlight:** the 988 review balls stack into per-team **chip stacks** on a casino table, resolving green/red as time scrubs.
- **2D scenes / widgets:** the **spell mosaics as an authored SVG scene, not a field morph** (the unit here is overs, not balls — pretending it's the field would silently break object constancy): **3-4 exemplar innings per era** as 20-square bowler mosaics, long same-color runs in 2008 dissolving into confetti by 2026, with the **fragmentation ticker** carrying the aggregate claim; the toss dual-line with the wedge + a "captain simulator" toggle (what pure trailing evidence would have decided); the momentum audit panel (above).
- **WPL thread:** doctrine transmission: WPL captains inherited chase-first fully formed (77% field-first from season one, ~100% by 2025-26 — though their 60% chase win rate partially justifies it), review like identically calibrated gamblers (30.5% vs 29.6% upheld), and out-fragment the modern IPL. A league born into the analytics age behaves like one — the culture arrived before the history did.
- **Team-picker payoff:** *your captains' report card* — your franchise's field-first rate against its actual chase win rate at home, plus your team's review-discipline rank (upheld % leaderboard position).
- **Fallback:** the match-dot morph jump-cuts to its split-river end state; chip stacks render resolved; the momentum panel degrades to static observed-vs-null small multiples; the mosaics are SVG and static by nature.
- **Handoff to Ch 9:** the closing beat — *beliefs churn every season; whole doctrines arrive and die inside a broadcast cycle. But underneath the churn, some things refuse to move.*
- **Footnote layer:** review-schema honesty (review.type present on only 540/990; umpires_call truncation); spells defined per bowling end (the naive definition is degenerate — the laws forbid consecutive overs); **Matchup Engineering Score** (demoted by the beat budget, and a genuine engine — see §5 engine #6: how often the bowling change matches the best available no-lookahead head-to-head, with the honest note that the raw material itself grew — 12% of balls had usable h2h history in 2009, 42% by 2019); **Double-Header Dew Ledger** (demoted — the audit that stings: captains fielded first in 77.9% of night double-headers 2014-19, yet night chases won *less*, 51.0% vs 57.3% afternoon; joins Dew Dividend, the conditioned mechanism study, already here); the momentum permutation-null construction (stratified within innings × phase × batter — stratification is the whole game; computed at build time); Chase Pacing Portraits as the fuller phase-space treatment of the pacing beat.
- **Teasers:** `Field-first: 43% → 77%. Chase wins: 54% → 53%.` · `Reviews doubled; accuracy didn't budge` · `Momentum, tested: mostly indistinguishable from shuffled cricket` · `The one pass: modern chase pacing genuinely works`.

---

### Chapter 9 — The Living League *(Duels & Living Structure — persistence through churn)* — ships in R5

**One-liner:** Institutions churn — five synchronized mega-auction flatlines in nineteen seasons — but the human fabric refuses to: decade-long duels and one-club loyalists persist straight through every reset.

*(Single-pointed by design: the belief-testing beats that used to share this chapter moved to their true homes — Momentum Myth-Buster to Ch 8's audit, the crack ratio to Ch 3, where it explains bowling economies. What remains is one point, made three ways — welcome pacing relief before the finale. Opening handoff from Ch 8: **but underneath the churn, some things refuse to move.**)*

- **Hero metrics:** ★ **Duel Network** — the temporal rivalry graph; 235 duels span 8+ seasons; the longest-running: **Kohli vs Jadeja, 160 balls across 14 seasons** — and ★ **Roster Continuity Index (the Auction Heartbeat)** — franchise squads as an EKG: league-mean squad overlap 0.46 in retention years, crashing to **0.19** in mega-auction years — five synchronized flatlines in 19 seasons, and rivalries persist straight through them.
- **Supporting metrics (curated — beat budget: 1, deliberately under budget):**
  - **Journeyman Network & Loyalty Spectrum** — the transfer-market chord diagram: among players in ≥ their 4th season, one-franchise loyalists fell 28% → 14-15%; one player has worn nine shirts.
- **Controlling morph (with its curation rule written into the pipeline contract):** the **duel web** — a precomputed force layout over **pairings with ≥30 balls only** (a few thousand nodes; the full 31,355-pairing graph is a fur-ball, and the story lives in the long duels anyway), with the long tail rendered as **background dust that condenses into nodes on filter**. Edges glow batter-red or bowler-blue by dominance; the graph densifies and churns as seasons scrub; tapping an edge opens a ball-by-ball duel replay strip (every ball of Kohli-Jadeja, in order, on the annotation plane). The chapter's thesis image is the closing beat: **the duel web re-draws across the flatline years** — institutions churn, rivalries persist.
- **2D scenes / widgets:** the **auction heartbeat as a straight 2D telemetry chart** (per the morph budget — roster overlap is a squad-level stat; the 316k balls carry no meaning in an EKG trace, so the particles are saved for the duel web): ten franchise monitors, mega-auction years hitting all of them at once; the loyalty chord diagram with a season scrubber.
- **WPL thread:** overlay the WPL's rivalry graph at league-age 3 on the IPL's at the same age — how fast does a league's rivalry structure crystallize? Plus the WPL's compressed mini-auction cycles as a fast-forward replica of the heartbeat.
- **Team-picker payoff:** *your team's longest-running duel* (with replay), your franchise's heartbeat trace (who left and arrived at each flatline), and your most loyal one-club player.
- **Fallback:** the duel web renders its end-state layout per season preset; the replay strip is a DOM strip, static-friendly; heartbeat and chord diagram are 2D charts.
- **Footnote layer:** empirical-Bayes shrinkage of duel dominance (small-sample duels pulled toward par); the ≥30-ball curation threshold and its sensitivity; Collapse Contagion as the deep cut — Hawkes-process analysis shows a wicket makes the *next* wicket less likely (aftershock ratio 0.94; "collapses" fire at an eerily era-stable rate), the contrarian companion to Ch 8's momentum audit.
- **Teasers:** `Kohli vs Jadeja: 160 balls, 14 seasons, 3 dismissals` · `Mega-auction years: squad overlap 0.46 → 0.19, all ten monitors at once` · `Loyalists (4+ seasons in): 28% → 14%` · `One player has worn nine shirts`.

---

### Chapter 10 — The Era Machine *(regime detection + the Teleporter — the synthesis)* — ships in R6

**One-liner:** We stop narrating eras and let the data draw its own fault lines — the "modern era" turns out to be a stack of staggered revolutions — and then you get the machine itself: teleport any player to any year.

- **Hero metric:** ★ **League Pulse Seismograph** — PELT + Bayesian changepoint detection over every per-match series; the breaks are **staggered** (six-rate ~2018, run-rate 2023-24, wide-rate ~2022/2024): the modern era is not one event but a stack of revolutions. A "statistical strictness" dial lets the reader watch eras merge and split live — 6 eras at loose settings, 2 at strict.
- **Supporting metrics (curated — beat budget: 3):**
  - **Per-Metric Fault Map** — the anatomy of change as a subway map: each metric a line, break years as stations, co-breaking metrics sharing interchanges; the six revolution preceded the run-rate revolution by five years.
  - **Bridge-Player Chained Environment Index** — the answer Ch 7 planted: the 56 batters who played both 2023 and 2024 gained only **+2.3 SR within-player while the league jumped +8.9** — roughly three-quarters of the explosion was personnel and usage turnover, not the same players hitting harder. **Verdict card (one beat, closing the mystery Ch 4 opened):** *three suspects, all guilty, on different counts — the rule opened the door (Ch 7), new personnel walked through it (this chapter), and the skill curve had been climbing for a decade (Ch 1).* Case closed.
  - **Era Translation Factors (the Player Teleporter — with the Z-Ledger folded in as its argument-settling face)** — the payoff toy: pick any player-season, drag the era dial across 2008-2026, watch the stat line re-quote with uncertainty bands — percentile method as the honest default, the naive league-ratio multiplier shown as the ghost (the gap between them is itself the exhibit: Sehwag 2008's SR 184.5 naively "translates" to ~228). Cross-era rankings appear on screen as **"how far above his own era"** — always a rank or a gap, never a z (glossary rule): *2011 Gayle still edges 2024 Fraser-McGurk once each is measured against his own league's physics, despite a raw SR 51 points lower.* Adaptation badges for the players whose games survived the 2023 fault.
- **Controlling morph (the finale):** the entire field arranges into **one chronological ribbon** — all 316,388 balls in match order, 2008 to now — and the detected fault lines **crack the ribbon** with posterior-probability opacity while the strictness dial re-fractures it live (every dial stop is a precomputed segmentation — a lookup, per the standing rule). **Subset-highlight:** the Teleporter lifts one player-season's balls bodily out of the ribbon onto a stage where they re-price. Final beat: the ribbon exhales back into the free-floating field of the cold open — the piece ends where it began, except now the reader can read it — and the sandbox UI rises around it.
- **2D scenes / widgets:** the seismograph strip-stack; the Teleporter card (with "find their modern twin" one-tap); the convergence fan chart.
- **WPL thread:** the Maturity Clock's last appearance — the WPL's own micro-seismograph (4 seasons, honestly under-powered, labeled as such), the constellation callback, and the **Convergence Clock** as the thread's closing look forward: if the current slope holds, league RR crosses 10 around 2027-28 — and the WPL's run-rate convergence arrives roughly a decade before its six-rate convergence, per metric, rendered as honest posterior fans, not prophecy. Uncertainty owned loudly.
- **Team-picker payoff:** *your adapters* — which of your franchise's icons crossed the 2023 fault line rising (adaptation badge), and the Teleporter defaults to your team's legend.
- **Fallback:** the ribbon renders as strictness-preset end states (the 2-era, 4-era, and 6-era stills); the Teleporter is a card widget, not a motion beat; the strictness dial degrades to preset buttons.
- **Footnote layer:** PELT/BOCPD spec (per-match series sorted by actual dates, not season labels); the penalty-sweep era-count curve; the chaining method and its survivorship shrinkage; why the two translation variants disagree (chained environment factors ≪ raw league ratios); the **Z-Ledger arithmetic** (the z-scores behind "how far above his own era": Gayle +5.54, Fraser-McGurk +5.22 — kept off-screen per the glossary rule); Micro-Era Tapes as the within-season check (2021 was two leagues in one season: India leg RR 8.41, UAE leg 7.71 — some "era breaks" are venue-leg composition).
- **Teasers:** `The modern era is a stack: sixes broke in 2018, run rate in 2023, wides in 2024` · `¾ of the 2024 explosion was personnel, not improvement` · `2011 Gayle still outranks everyone, measured against his own era` · `RR 10 by ~2027-28 — if the slope holds`.

---

### The Bowl — "The Field Is Yours" — minimal in R1, full grammar in R6, credibility layer + player cards in R7

**One-liner:** The story ends by handing over its own material: the full 316k-ball field plus a linked mini-explorer, opening pre-filtered to your team on a famous match — never blank.

- **What it is (at full build):** the persistent field becomes a filterable instrument — league / season / team / player / phase / over / outcome / bowler-batter facets over the ~0.8MB-gz columnar dataset decoded to typed arrays (all realistic queries answered in 0.26-4.8ms — measured). Tap any point: the DOM tooltip names the exact ball — bowler, batter, match, result. A linked panel shows the selection as worm / Manhattan / leaderboard, reusing chapter widgets.
- **"Minimal" defined tightly (R1 scope honesty — the minimal bowl is secretly platform work: GPU picking on 316k points, facet-driven per-point filtering of the GL field, tooltip metadata plumbing):** R1 ships **team + season facets only, one famous-match preset, and the tap-a-ball tooltip. Nothing else.** League/phase/player facets, the linked worm/Manhattan panel, tour flags, and shareable URLs are all explicitly deferred to R6.
- **Never blank (locked):** opens on the reader's team (from the picker) at a famous match preset; from R6, **tour flags** (538-style authored annotations) walk newcomers to ten spectacular filters ("all 316 balls Bumrah bowled to Buttler," "every ball of the 2016 Kohli season," "the WPL's entire six-hitting history on one screen").
- **Credibility layer (ships in R7 — the §7 methodology ideas live here, site-wide):** every leaderboard carries a **trust meter** from Stabilization Points (~93 balls before boundary% is half-signal — the first such number computed for T20); a **shrinkage slider** morphs raw → regressed leaderboards (True-Talent, with CIs); cross-era comparison cards carry a **freshness dial** from Metric Half-Life ("this 2013-vs-2025 economy comparison retains 22% of its meaning"). SR+ / True SR is the sandbox's era-honest currency for all player comparisons.
- **Growth path:** R1 ships field + team/season facets + tap-a-ball + one preset (as R1's own internal milestone R1b, reviewed separately from the cold open + Ch 1); R6 adds the full filter grammar, tour flags, and shareable URL states; **R7** adds the credibility layer and **player search-a-name cards** (the locked later-release personalization feature, now with the release it implies: type any of 938 names, get their card — entry map, SR+ river, duel list, teleporter link).
- **Fallback:** the sandbox is interaction-first by nature, but every facet change resolves to a static field state (demand-rendered); tour flags are DOM annotations readable without motion; tooltips work by tap and by keyboard focus.

---

## 4. Release plan (risk-gated, always publishable)

Working mode is milestone reviews: each release is a coherent chunk of working software the owner reviews before the next begins. Chapters append in narrative order, so the live piece is complete-as-published at every stage. Efforts are rough solo+AI-pair calendar estimates — **with two binding mechanics:**

- **Re-baselining is mandatory, not a gesture:** R1's milestone review produces a *measured* per-morph-scene and per-widget cost, and every R2+ estimate below is **recomputed from those actuals before any date is committed**. The research's own finding stands: choreography is easily 50% of total effort, and every transition is bespoke design work.
- **Inter-release buffer:** owner review + rework latency between releases is real work; the plan carries **~20% buffer between releases**. Headline totals below are quoted as best-case *and* planning-case.
- **Every release checklist includes:** chapter payload within the §2 ledger budget · 16/16 payoff-card variants pass the snapshot harness · at least one bespoke WPL-picker payoff card ships.

### R0 — Pipeline + particle-morph spike *(the risk gate; ~1-2 weeks)*

**Scope:** Python build pipeline (flatten Cricsheet → per-scene aggregate JSON + ~0.8MB gz columnar sandbox dataset + binary layout buffers — **Uint16-quantized positions on the wire, decoded to Float32 GPU-side**); canonicalization tables (engine #4: ~60 venue strings, franchise renames, season normalization, super-over/D-L flags) with snapshot tests; **the payload ledger as a named deliverable** (per-chapter inventory of layouts + new per-point attributes + JSON against the §2 budgets, including the "what must arrive before the cold-open assembly can start" number); **the payoff-card snapshot harness** (asserts 16 non-degenerate variants per chapter); the morph spike — one three.js instanced-Points layer, 316k points, two precomputed layouts (free field ↔ season columns), scroll-scrubbed, plus a DOM label plane sharing the projection.

**Pass criteria (all must hold, tested on a mid-range Android phone, not the dev laptop):**
1. 60fps through the morph; **no thermal collapse over a 10-minute dwell with battery-drain measured** (the experience is a 20-45 minute read, not a 3-minute demo), and **idle GPU near zero between scenes** (demand-mode rendering verified — the loop provably stops when nothing moves).
2. The transition *reads* — a viewer can follow what the balls are doing (object constancy survives).
3. DOM labels stay registered to GL positions through the whole scrub.
4. `prefers-reduced-motion` renders **live end-state jump-cuts** (the field renders each scene's final layout with no interpolation) that stay legible and keep personalization.
5. **Layout-encoding + payload budget validated:** per-point bespoke layouts ≤ ~1.5MB gz each and lazy-loaded per chapter; group-indexed layouts (season columns, match-dots, duel web) encoded as small centroid tables + per-point Uint16 group ids + in-shader jitter — NOT 2.5MB per layout × 20 layouts; **the summed ledger fits the §2 budgets (≤3MB before assembly · ≤2MB/chapter · ≤25MB full read)**. If the budget fails, this is where we find out.

**Fallback if the spike fails (pre-agreed):** stratified ~50k-point sample or Canvas 2D, or downshift to the Concept-1 essay — every chapter below survives intact because layouts are data, not code.

### R1 — A complete publishable piece *(~6-9 weeks — re-baselined; see scope honesty below)*

**Scope honesty (why this is not 3-5 weeks):** R1's contents are locked, but R1 builds the *entire platform* plus four distinct product surfaces — the You-Draw-It widget (touch+mouse drawing, divergence quantification, correct-guess branch), the biggest GSAP scrub in the piece (316k-point staggered field assembly with live counter), the full chapter system (scroll orchestration, GL/DOM shared-projection annotation plane, footnote-layer UI, per-team personalization state, mobile + reduced-motion variants, persistent chapter nav), and the minimal sandbox — which is secretly hard (GPU picking on 316k points, facet-driven per-point GL filtering, tooltip plumbing, preset system). **R1 pays the one-time platform cost that every later release amortizes; R2+ per-chapter estimates must never be judged against R1's duration.**

**Sequenced internally as two milestones, each with its own owner review:**
- **R1a — publishable on its own:** cold open (stakes line → You-Draw-It with "just show me" skip → truth reveal with correct-guess branch → field assembly scrub set piece #1) · team picker (one tap-screen, skip equally prominent) · **Chapter 1** end-to-end (controlling morph + six-subset highlight, out-rate strip, payoff cards incl. the WPL-picker card, footnote layer, fallback path) · sketch + team pick persisted to localStorage from day one · methods page stub · **a simple end-card teasing the sandbox.**
- **R1b — the minimal bowl:** field + **team/season facets only**, tap-a-ball tooltip, one famous-match preset (per the tightened §3 definition; everything else deferred to R6).

**Why it's publishable:** the martini glass in miniature — a hook, a complete thesis chapter, and (after R1b) a bowl. R1 is deliberately engine-light: Ch 1's metrics are all direct computations (no par model, no RE, no WP), so narrative ships before modeling.
**Milestone review:** prices the true per-morph and per-widget cost — and those actuals **re-baseline every estimate below before its dates are committed**.

### R2 — The revolution and the resistance *(~3-4 weeks, pending R1 re-baseline)*

**Scope:** **Chapters 2 + 3.** Builds engine #1 (season/phase/venue par baselines + SR+ family — needed for the anchor definition and Dot+/True Economy) and engine #5 (entry states / derived batting positions — needed for archetypes; the light balls-faced index already shipped inside Ch 1). **Parallel Python track starts now:** engines #2 (RE288) and #3 (WP model) have zero frontend dependency, so their pipeline work begins during R2 and runs behind the chapter work — they must clear the §5 validation gate before any R3b choreography is authored.
**Piece state when live:** cold open + thesis + consequence chain through bowling — a coherent three-act mini-story.

### R3a — The rising tide *(~2-3 weeks)*

**Scope:** **Chapter 4** — deliberately engine-light (par logistic + direct counts), carrying the planted-mystery beat and the sketch-callback (with its no-sketch variant).
**Why it's a release, not a phase:** "always publishable" must not silently degrade into "publishable only at the end of an 8-10 week block." The piece reads cleanly ending on The Rising Tide; the deferred mystery is an authored cliffhanger, not a hole.

### R3b — The repricing *(~4-6 weeks; the heavy-engine release)*

**Scope:** **Net Session interlude (both dials) + Chapter 5**, plus scrub set piece #2 (the famous final over). Consumes engines #2 (RE288 surfaces, per era + pooled WPL with the evidence mask) and #3 (WP lookup grids; WPA per ball; LI byproduct) — both already built on the R2-R3a parallel track and **passed through the §5 validation gate (calibration plots + RE-surface sanity checks) before any scene choreography was authored**, so model rework can never invalidate finished scene work.
**Piece state when live:** the emotional arc is complete (belief → thesis → consequences → meaning). Soft-promote to friendly audiences for feedback.

### R4 — The wider world *(~3-4 weeks)* ← **"complete enough to promote"**

**Scope:** **Chapters 6 + 7** (Two Dialects, then the Twelfth Man that depends on it). Constellation map (per-phase embeddings Procrustes-aligned in the pipeline), maturity clock, the control-group natural experiment, placebo cursor.
**Why the promote line sits here:** after R4 every locked commitment is visibly delivered — the thesis chapters, the win-probability spine, a *dedicated* WPL chapter honoring the two-dialects framing (promoting earlier would front a piece whose WPL promise is still IOU), the signature rule-change story, and a working sandbox. R5-R7 deepen; they no longer complete.

### R5 — Minds and fabric *(~3-4 weeks)*

**Scope:** **Chapters 8 + 9** (Captain's Brain, Living League). **Engine #6 (no-lookahead h2h history table with empirical-Bayes shrinkage) is built at the start of R5 with lookahead-bias snapshot tests** — same discipline as the other engines. Duel-web force layout precomputation (≥30-ball pairings + background dust), momentum audit panel (**all nulls precomputed at build time** — no client-side permutation), auction heartbeat as a 2D telemetry chart, spell-mosaic SVG scene.

### R6 — The Era Machine + the full grammar *(~4-6 weeks)*

**Scope:** **Chapter 10** (seismograph with precomputed strictness stops, fault map, bridge-player index + the verdict card that closes the 2023 mystery, Teleporter with the folded-in era-rank face, convergence fans) · full sandbox filter grammar (league/phase/player/over/outcome/bowler-batter facets), the linked worm/Manhattan panel, tour flags, shareable URL states.
**Piece state when live:** **the narrative is definitively complete** — every chapter, every arc, the full bowl.

### R7 — The credibility layer + player cards *(~3-4 weeks)*

**Scope:** **Player search-a-name cards** for 938 players (entry map, SR+ river, duel list, teleporter link — a standalone product surface, given the release the locked "later-release feature" language always implied) · the sandbox **credibility layer** (trust meters from Stabilization Points, shrinkage slider, freshness dials).
**Piece state when live:** the definitive version. **Total elapsed: best-case ~7 months; planning-case ~9-12 months** once the ~20% inter-release review/rework buffer and R1's re-baselined actuals are applied. The old "~5-7 months" headline priced R1, R3, and R6 as single releases; the split releases price the same work honestly.

**Post-R7 stretch (explicitly out of scope until then):** the ESPNcricinfo enrichment join (one scrape of ~950 player pages unlocks bowling styles, platoon matchups, nationality pipeline, birthdates — the catalog's highest-leverage external add), the Lineup Simulator, and any parked idea graduating into sandbox tour flags.

---

## 5. Engine build order (engineering follows narrative need)

The six shared engine layers from the catalog, mapped to the first chapter that needs them — so no engine is built before a shipping chapter demands it:

| # | Engine layer | First narrative need | Built in | Also powers later |
|---|---|---|---|---|
| **#4** | Canonicalization tables (venues ×60, franchise renames, season normalization, super-over/D-L/legal-ball bookkeeping) | Everything — the cold open's counts are wrong without it | **R0** | Every chapter, sandbox facets |
| **#5** | Entry states / derived batting positions (light: per-batter balls-faced index; full: entry over × wickets × RRR) | Light version: Ch 1 ignition wall (R1). Full version: Ch 2 archetypes | **R1 (light) / R2 (full)** | Ch 5 finisher supply, Ch 7 tail/position footnotes, sandbox entry map |
| **#1** | Par baselines / SR+ family (season × phase × venue expected rates; RVAE state-baseline table) | Ch 2 anchor definition (SR vs phase par); Ch 3 Dot+/True Economy | **R2** | Ch 4 PP premium, Ch 10 era-rank + Teleporter, sandbox SR+ currency |
| **#2** | RE288 run-expectancy / resource surfaces (per era band; pooled WPL behind the evidence mask) | Net Session second dial + Ch 5 linear weights, wicket value, surface-drift exhibit | **Parallel Python track from R2; validation-gated; consumed in R3b** | Ch 10 translation factors, sandbox pricing |
| **#3** | Win-probability model → precomputed lookup grids; WPA per ball; Leverage Index byproduct | Net Session interlude + Ch 5 (WPA, final-over scrub) | **Parallel Python track from R2; validation-gated; consumed in R3b** | Ch 8 leverage framing, sandbox decision-ball flags, search-a-name cards |
| **#6** | No-lookahead per-ball head-to-head history table with empirical-Bayes shrinkage | Ch 8 Matchup Engineering Score (footnote layer) + duel dominance shrinkage | **Start of R5, with lookahead-bias snapshot tests** | Ch 9 duel web dominance, sandbox bowler-batter facet, search-a-name duel lists |

**Engine-validation gate (binding):** engines #2 and #3 must pass calibration plots and RE-surface sanity checks **before any Chapter 5 / interlude choreography is authored**. Model rework must never invalidate finished scene work — the gate is what makes the R2-era parallel track safe. Engine #6 carries the same discipline via its lookahead-bias snapshot tests: no h2h number ships without proof the table never peeks forward.

Hero-metric placement check (all 15 ★ land in a chapter): SR+ (engine #1 → Ch 10 Teleporter + sandbox currency) · Anchor Extinction (Ch 2) · Run-Out Extinction (Ch 2) · Attack-Containment Frontier (Ch 3) · Toss Revolution (Ch 8) · RE Surface Drift (Ch 5) · WPA (Ch 5) · Impact Player Natural Experiment (Ch 7) · DRS Economics (Ch 8) · Death of the Sighter (Ch 1) · Duel Network (Ch 9) · League Maturity Clock (Ch 6) · Season Constellation Map (Ch 6 + Ch 10 callback) · Roster Continuity Index (Ch 9) · League Pulse Seismograph (Ch 10).

---

## 6. Parking lot (nothing silently dropped)

**Standing infrastructure, not chapter-bound (in the piece, listed here so they aren't mistaken for cuts):** SR+/True SR (engine + sandbox currency); RVAE (engine #1b); RE288 (engine #2, exhibited in Ch 5); Win Probability Engine (engine #3, the interlude); Leverage Index (WP byproduct; decision-ball flags + match-EKG in sandbox); Entry-Point Fingerprint (engine #5; the entry *map* is a sandbox view); T20 CPI (cold-open truth curve + site-wide deflator); Stabilization Points, True-Talent Leaderboards, Metric Half-Life (the sandbox credibility layer: trust meters, shrinkage slider, freshness dials).

**Absorbed into footnote layers (in the piece, one click deep — the beat budget of hero + max 3 supporting pushed several of these down; none are cut):** The Over as a Clock Face (Ch 1, as a small 2D radial); Break-Even Running + Milestone Braking (Ch 2); FIB + True Economy/headwind + Phase Fingerprint + Squeeze Retention's bounce-back null (Ch 3); Phase Economy Map (Ch 4); Era-Indexed Chase Difficulty Surface + Era-Swap Counterfactual Replay (Ch 5); Star Gravity/Competitive Balance paired myth-bust + Batting Depth Ledger + Twos Culture + Powerplay Fear Index (Ch 6); Tail Exposure Rate + Part-Timer Extinction + Batting-Order Fluidity null (Ch 7); Matchup Engineering Score + Double-Header Dew Ledger + Chase Pacing Portraits + Dew Dividend (Ch 8); Collapse Contagion (Ch 9); Micro-Era Tapes + the Z-Ledger arithmetic (Ch 10).

**Parked — duplicate lens (the beat is told by a stronger sibling):**
- Partnership Tempo & Rebuild Persistence — same finding as New-Batter Tax (Ch 2 coda), one lens is enough.
- Runs per Resource — the anchor's obituary already told by Anchor Extinction + linear weights; needs the resource engine for a redundant beat.
- Entry-Point Adjusted Innings Value — subsumed by RVAE + the sandbox entry map.
- Shape of an Innings (worm taxonomy) — the innings-shape beat is carried by Gear-Shift Detector at player level; team-curve gallery is a natural sandbox add later.
- Ignition Curve is IN (Ch 1) but its scalar cousins (SR-crossing points) stay footnotes — one ramp visual suffices.

**Parked — strong idea, wrong piece length (first candidates to graduate into sandbox tour flags or seasonal follow-up posts):**
- Rare Dismissals Museum — delightful cabinet of curiosities; ideal sandbox easter-egg tour, not a chapter beat.
- Record Half-Life is IN (Ch 4); Streak Atlas with Luck Nulls — parked: the luck-band device needs room the chapters don't have.
- Pythagorean Wins — the "lucky champions" ledger; fan-shareable sandbox tour flag.
- Award Bias Audit + Player-of-Match Archetype Drift — fun awards content; standalone follow-up post material.
- Home Fortress Erosion — fan-friendly map; sandbox tour flag.
- Season Phase-Space (standings race) — gorgeous but off-thesis; sandbox race view later.
- Photo-Finish is IN (Ch 6); Entropy Engine — "faster AND more varied" is a lovely nuance without a chapter-sized point.
- Strike Machine (strike-farming) — the sacrificial single lives; needs its own essay-length treatment.
- Era-Swap Counterfactual is a Ch 5 footnote exhibit (demoted from main flow by the beat budget); the Lineup Simulator — the heaviest build in the catalog; post-R7 stretch goal, explicitly.

**Parked — needs the external ESPNcricinfo/auction join (post-R7 enrichment, the catalog's decision list):**
- Bowling-Style Phase Shares (the single highest-leverage join — spin-invasion narrative).
- Platoon Polarity (handedness × style matchups).
- Auction Value-for-Money (price per impact run).
- Homegrown Pipeline Tracker (uncapped-Indian share; the join path is already proven).
- Team Travel Odometer's kilometers layer (hops are in-data; km needs a gazetteer).

**Parked — verified null / subtle result (honest, but not fan-first chapter material):**
- Matchup Targeting Score — near-null in both eras; mythology-puncturing footnote candidate at best.
- Quota Fatigue / 4th-Over Premium — inverted premise, fixed-effects-heavy story.
- Death-Over Specialization Gini — real but modest; superseded by Phase Fingerprint (Ch 3).
- Wickets Above Expectation (WAE) — leaderboard machinery, not a story beat; sandbox candidate post-engines.
- Franchise Convergence Index — probe found only mild convergence; validate the full vector before promising the "meta galaxy."
- Batting-Order Fluidity — kept only as Ch 7's honest-null footnote.
- Milestone Braking is a Ch 2 footnote beat (one honest coda per chapter; New-Batter Tax carries it); Sequencing Luck — the estimator fix (resample-extended permutations) is heavy for a subtle payoff.

**Parked — off the eight arcs (the schedule/fatigue and fielding/officiating families):**
- Season Compression Index, Rest-Delta Win Edge, XI Churn Under Congestion, Road-Trip Fatigue Gradient, Rain & DLS Exposure Audit, Playoff Gauntlet vs Fresh-Legs Final, Venue Familiarity Decay, Calendar Climate Curve, Playoff Pressure, Must-Win Meter, Dead-Rubber Laboratory, Post-Defeat Panic Index — a coherent "The Grind" chapter exists in this material if the piece ever wants an eleventh chapter; parked as a set.
- No-Ball Technology Shock, Umpire Fingerprint Cards, Keeper Inference + Byes Ledger, Catch Networks & the Substitute Underworld, Fielding Impact — the officiating/fielding family; strong follow-up-post material (the no-ball instrumentation story is a gem) but off the locked arcs.

**Parked — careers/cohorts beyond Ch 9's cut:**
- League-Age Curves, Debut Cohort Survival, Career Shape Clustering, Career Gap & Comeback Map, Debut-to-Signature Lag, One-Season Wonder Rate, XI Stability Meter — Ch 9 takes the heartbeat + loyalty thread; the full careers corpus becomes the search-a-name card content (R7) and follow-up material.
- Volatility Premium, Clutch Score, T20 RAR/WAR, Composite Impact Score, Impact Index (Varma), Captain's Trust/Fireman Index — the deep impact-family stack; all post-engine sandbox/leaderboard candidates rather than scroll beats.
- Vanishing Deflection (legbyes) — a quiet gem with no chapter home; tour flag ("the stat hiding in a column nobody reads").
- Unspent Resources Index — U-shaped and needs the exchange-rate regression to say anything; Ch 5 tells the wicket-price story better.
- Pressure Index (academic) — the Net Session interlude covers pressure intuition; the formal index is sandbox-layer.
- Scoring-Rate Convergence Gap — folded into Ch 6's maturity beat rather than standing alone.

---

## 7. Open editorial questions for the owner (max 5)

1. **Which final over is THE final over?** Ch 5's scrub set piece proposes the 2019 final (Malinga defending 9, MI by 1). Alternatives: 2017 final (Mumbai defend 129), or a dual-scrub with a WPL final to honor the two-dialects commitment inside the set piece. *(The per-team-swap half of this question is resolved in this revision: one canonical over for everyone — each alternate over is bespoke scrub choreography + authored annotation timing + a WP-worm sync, the single most expensive asset type in the project, and Ch 5's personalization is already fully served by the data-driven "your team's most valuable ball ever" card. Only* which *over remains open.)*
2. **What exactly does the reader draw in the cold open?** Proposed: average first-innings score (most legible for fans). Alternatives: season run rate, or 200+ totals per season (more dramatic hockey stick, harder to have intuitions about). Only drafting + a few hallway tests will settle which produces the best "I was wrong" gasp on a phone screen.
3. **Ch 2's emotional register:** the wildlife-documentary framing (extinction, last survivors, obituary) is the catalog's pitch and it's strong — but does elegy risk reading as nostalgia-for-anchors, cutting against the piece's celebratory thesis? Decide in drafting whether the register is elegy, autopsy, or dark comedy.
4. **How loud is the WPL in IPL-centric chapters?** The thread is designed into every chapter, but the dose matters: a fixed "WPL beat" slot per chapter (predictable rhythm) vs variable placement where the comparison genuinely illuminates (locked decision language). Drafting Ch 1-3 will reveal whether the fixed slot feels like quota.
5. **Stage names — sign-off, not policy:** the policy is now a standing rule (§2, glossary rule: no term of art on-screen in main flow or teasers; every device gets a stage name before its chapter's copy is written), and the first seeds are planted there (edge of the possible / out-rate / control group / how-far-above-his-own-era). What remains for the owner: sign off on the seeded names before R2 copy, name the rest of the device roster ("League Maturity Clock," "SR+," "RE288"), and decide which technical-ish names are themselves the brand ("the Teleporter" arguably already is one).

### RESOLVED — owner decisions, 2026-07-03 (all five closed)

1. **Final over: 2019 final, Malinga defends 9** (MI beat CSK by 1). One canonical over for everyone, per the revision.
2. **Cold-open draw: 200+ totals per season** (the hockey stick). Mitigation for weak fan baselines is mandatory: the 2008–2012 segment comes pre-drawn (~6/season); the reader completes 2013–2026. The reveal is 65 in 2026.
3. **Ch 2 register: elegy** — affectionate farewell to the anchor; watch the nostalgia risk in drafting (the piece's thesis stays celebratory).
4. **WPL dose: variable placement** — the WPL appears where the comparison genuinely illuminates; no fixed quota slot. The §2 no-single-clock corollary still binds every beat.
5. **Stage names: seeds approved as-is**; remaining devices named during each chapter's drafting with owner sign-off at milestone reviews.

**Kickoff decision:** R0 approved to start (git init + pipeline + payload ledger + morph spike, GitHub Pages base path from day one). Owner also added §8 (GitHub Pages deployment + design-review cadence) on the same date.

---

## 8. Deployment & design process (owner additions, 2026-07-03)

### Deployment: GitHub Pages
- **Target:** GitHub Pages via a GitHub Actions workflow on push; SvelteKit `adapter-static`, full prerender, no server routes anywhere.
- **Base path from day one:** the site must work at `https://<user>.github.io/<repo>/` — `paths.base` configured in R0, and every asset/fetch/buffer URL goes through it. CI asserts a subpath build (retrofitting base paths is the classic Pages failure mode).
- **No server-header control:** Pages cannot set custom compression/cache headers, which is why the payload ledger's Uint16 wire quantization is mandatory rather than nice-to-have; immutable-asset caching comes from hashed filenames, not headers.
- **Repo:** project is not yet a git repository — `git init` + Pages action are R0 deliverables; the owner creates the GitHub repo and enables Pages at first deploy.

### Design-review cadence (uses the owner's design agent + skills)
- **Storyboard gate (before building any chapter):** the chapter's storyboard (morph choreography, annotation plan, on-screen numbers) gets a **cognitive-design-architect** review — visual hierarchy, cognitive load, preattentive legibility of the one-point-per-scene rule.
- **Scene construction:** the **d3-visualization** skill drives 2D chart scenes; **visual-storytelling-design** shapes the annotation/caption layer; **cognitive-design** grounds encoding choices.
- **Built-scene audit (before owner milestone review):** a **design-evaluation-audit** pass on the running scene, so milestone reviews spend the owner's attention on direction, not findable defects.
- **Honesty gate:** **cognitive-fallacies-guard** audits every causal-flavored chapter (Ch 7's diff-in-diff, Ch 8's belief audit, Ch 1's "aggression was free") so visuals never imply more causality than the data supports. Fans-first must not mean rigor-last.

---

*End of blueprint. Companions: `metrics-catalog.md` (all 143 ideas + verification verdicts), `presentation-options.md` (concept research + measured constraints), `data-profile.md` (ground truth tables).*

---

## Revision notes

**What changed in this revision (all locked decisions intact; chapter count, order, and titles unchanged):**

- **The 2023 mystery is now authored, not accidental:** Ch 4 poses "what broke in 2023?" and visibly defers it; Ch 7 opens and closes with explicit mystery handoffs (the rule as partial answer, "was it the same players?" planted); Ch 10's bridge-player beat carries a one-beat verdict card reconciling all three causes. A "planted mystery" bullet was added to §2's narrative-arc rationale.
- **WPL single-clock beats eliminated:** new standing-rule corollary — any stat placing the WPL on the IPL timeline must be paired *in the same beat* with a dialect stat that refuses the timeline. Ch 1's WPL beat was rewritten ("already moving" is now the subject; paired with the four-led engine; the "live broadcast of 2008" framing removed), Ch 3 and Ch 4's WPL beats were re-paired, and the cold open now stages the WPL "as its own constellation" with authored separate-not-late copy.
- **Cold open de-risked:** stakes line before the draw ask, an explicit "just show me" skip on the sketch screen, and a scripted correct-guess branch; sketch + team pick persist to localStorage from R1 (Ch 4's no-sketch variant is specced).
- **Release plan restructured, same contents:** R1 re-baselined to ~6-9 weeks with internal R1a/R1b milestones and an explicit one-time-platform-cost statement; "minimal sandbox" tightened to team+season facets, one preset, tap-a-ball only; R3 split into R3a (Ch 4, publishable) and R3b (interlude + Ch 5), with engines #2/#3 moved to a parallel Python track from R2 behind a binding validation gate; R6 split into R6 (Ch 10 + full filter grammar + shareable URLs) and a new R7 (search-a-name cards + credibility layer). Totals re-quoted as best-case ~7 months / planning-case ~9-12 months with a ~20% inter-release buffer, and R1-actuals re-baselining is now binding.
- **Payload ledger added** as a standing §2 rule (≤3MB before assembly / ≤2MB per chapter / ≤25MB full read), an R0 deliverable, and a per-release pass criterion. Layout buffers ship Uint16-quantized on the wire and decode to Float32 GPU-side — this *preserves* the locked "Float32 layout buffers" GPU contract while halving wire size.
- **Beat budget enforced piece-wide** (hero + max 3 supporting in main flow): demotions to footnote layers are listed per chapter and mirrored in §6 (nothing cut). Ch 10's Z-Ledger folded into the Teleporter; Ch 6's Star Gravity pair and Batting Depth Ledger, Ch 2's Milestone Braking and Break-Even Running, Ch 3's True Economy and Phase Fingerprint, Ch 4's Phase Economy Map, Ch 5's chase surface and era-swap, Ch 7's tail/part-timer beats, Ch 8's matchup score and dew ledger all moved one click down. A persistent chapter nav ships from R1.
- **Morph budget enforced** (one controlling morph + subset-highlights per chapter): Ch 1's over-clock morph cut (small 2D radial in footnotes), Ch 9's auction heartbeat is now a 2D telemetry chart, Ch 8's spell mosaics are an authored SVG scene (the balls→overs unit switch is no longer disguised as the field), and Ch 3/4/6/7's secondary full-field re-sorts became 2D scenes or subsets. Cardinality curation rules are now written into the pipeline contracts: Ch 2 (par worm + exemplar worms + density haze), Ch 9 (duel web over ≥30-ball pairings + background dust), Ch 8 (3-4 exemplar mosaics per era + aggregate ticker).
- **Ch 8 refocused** as the belief audit (report card: fail, fail, fail, fail, pass — Required-Rate Responsiveness as the deliberate pass) and **Ch 9 refocused** on persistence-through-churn; Momentum Myth-Buster moved to Ch 8 (with build-time precomputed nulls from a curated claim menu — no client-side permutation test), the crack ratio moved to Ch 3's WPL beat where it explains economy inflation. Act IV chained with two handoff beats (Ch 7→8, Ch 8→9).
- **Net Session gained a second dial** (expected-runs-from-here) so Ch 5 never trades in an untaught currency; presets quote both. WPL WP/RE surfaces gated by a minimum-evidence mask ("not enough WPL cricket yet") in the interlude and Ch 5.
- **Reduced-motion redefined** as live-rendered end-state jump-cuts (personalization survives, zero image payload); a mandatory per-chapter **fallback** line was added to the §3 format and every chapter/interlude/bowl spec (six-panel strip for the final-over scrub, static placebo cloud for Ch 7, etc.). Demand-mode rendering is a standing rule; R0's device test extended to a 10-minute dwell with battery-drain and idle-GPU criteria.
- **Ch 6 constellation correctness:** per-phase embeddings are precomputed and Procrustes-aligned to the master layout (a live re-embed could flip the WPL's stars across the path).
- **Glossary hardened** from open question #5 into a standing rule with seeded stage names (edge of the possible / out-rate, ball by ball / the control group / how far above his own era); all main-flow terms of art in Ch 1, 3, 7, 10 rewritten to stage names.
- **Engine table:** engine #6 (no-lookahead h2h table) added, built at R5 start with lookahead-bias snapshot tests; engines #2/#3 rows updated for the parallel track + validation gate.
- **Payoff-card QA:** cards are strictly template + per-team JSON; the R0 harness asserts 16/16 non-degenerate variants per chapter (with designed empty states); every release ships at least one bespoke WPL-picker card.

**Considered items — disposition:** all "consider" items were applied (Ch 2 single coda; thesis risk-scoping clause in Ch 1; Act IV handoffs; WPL-picker per-release cards + constellation staging; sketch persistence + no-sketch variant; engine #6; WPL evidence mask; payoff-card QA harness). One was applied **partially**: open question #1 (the famous final over) — the per-team-swap half is resolved to one canonical over (it multiplied the piece's most expensive asset type for marginal payoff), but *which* over remains a genuine editorial call and stays with the owner rather than being decided here. No considered item was rejected outright; none conflicted with the locked decisions.
