# R2b Storyboard — Chapter 3: The Counterrevolution

**Status:** implementation truth for R2b (Chapter 3 only). Where this document and older blueprint copy disagree, this document wins. Where this document and the blueprint's *standing rules* (§2) disagree, the standing rules win, and no scene below may violate them. Modeled on `r1a-storyboard.md` and `r2a-chapter2-storyboard.md`. **No new engine:** Chapter 3 reuses engine #1 (season × phase × venue par / SR+, built in R2a) for "the going rate" and for True Economy. It adds one new controlling layout (`frontier`, the economy × bowling-strike-rate plane) and one new subset capability (`rivers`, the dismissal-kind flat-baseline 100%-stacked band), both requested from the shell in §6. R1 and R2a scenes must still render byte-identically.

**Sources of record:** `research/experience-blueprint.md` (§2 standing rules, §3 Chapter 3, §5 engine order), `research/voice-guide.md` (BINDING on every reader-facing word: orient-then-reveal, zero em dashes, say the plain thing, one idea and one number per caption, plain glosses for stats jargon, "you" with a mate-on-the-couch swagger), `research/metrics-catalog.md` (Attack-Containment Frontier Drift, Dot+, Dismissal DNA, Extras Weather / Death-Wide Tax, True Economy + True Wickets per 24, Dot-Ball Crack Ratio, FIB, Phase Fingerprint, Squeeze Retention: verified recipes + teasers), `research/data-profile.md` (bowling + dismissal + extras ground-truth tables), `web/src/lib/story/CONTRACT.md` (SceneFieldState, layout ids, subset/resort/cascade/filter capabilities, footnote registry, nav, §11 picking / §12 filtering / §13 worm-space / §14 cascade), `web/static/data/*` (R0/R1/R2a artifacts).

**Hard invariants carried by every scene (do not re-litigate per scene):**
demand-mode rendering (the loop stops whenever no morph, scrub, or interaction is active) · payload ledger (≤2MB gz incremental for Ch 3) · reduced-motion = live-rendered end-state jump-cuts, never baked frames · no hover-only content · mobile-first · **exactly one controlling morph in Ch 3 (free field → the frontier plane)**, and everything else is a subset-highlight or a 2D annotation-plane scene · GitHub Pages base path via `$app/paths` · byte-deterministic pipeline · no WASM · glossary rule (no statistical term of art in main flow; technical names live in the footnote layer) · **WPL never "behind"; every WPL beat is two clocks in one beat** · on-screen ball count is **316,199** wherever pixels are visible · **R1 and R2a scenes render byte-identically** (every Ch 3 capability is a no-op when its scene is not active) · **register is COUNTERREVOLUTION** (grudging admiration for the men with the ball, who got a worse deal every year and rebuilt their whole game; bowlers are the resistance, never "beaten" and never "worse").

---

## 0. Global grammar (Chapter 3 deltas on top of r1a §0 and r2a §0)

Everything in `r1a-storyboard.md` §0 (encoding grammar, one-message-per-scene, annotation-guided reading order, numbers style, footnote progressive disclosure, timing/scroll notation, persistence, register rules) carries forward unchanged, as do r2a's figure-channel and one-label-per-concept disciplines. Ch 3 adds:

### 0.1 Encoding grammar — the frontier plane (cognitive-design)

- **Position IS the argument.** Ch 3's controlling layout, **`frontier`**, condenses every ball to its **bowler-season's** spot on one map: **x = how many runs that bowler leaked an over that season** (economy; left = cheap, right = expensive), **y = how many balls he needed to take a wicket that season** (bowling strike rate; low = strikes fast, high = strikes slow). Every ball a bowler-season bowled stacks on that one coordinate, so a bowler-season reads as a **dense cloud** and a busy season reads as a bright smudge. The **promised land is the bottom-left corner** (cheap AND deadly). This is the single most important encoding in the chapter and the reason the morph is worth its budget: a whole career's containment argument becomes one dot's horizontal position.
- **The plane's orientation is anchored on screen, not just in captions.** The good corner sits bottom-left, which inverts the usual good=up-right prior, and the hero migration runs up-and-right, so C3-2 plants three quiet, persistent anchors that hold through every frontier scene (C3-3 to C3-8): short end-words at the axis ends (**cheap / expensive** on x, **fast / slow** on y) and a faint warm **"cheap and deadly" home zone** in the bottom-left corner. A scroll-back or deep-link reader then recognizes the plane without the caption, and the rightward drift reads as a retreat away from a fixed good corner, not as growth.
- **The clouds never re-sort; the migration is real data.** All bowler-seasons from all time land at **fixed** coordinates in the controlling morph (a bowler-season's economy and strike rate do not change once the season is over). The Gapminder retreat (C3-3) is NOT a second morph: as the reader scrubs a season pointer, the **current season's clouds brighten** (via the existing season filter, §12) while the rest dim to a faint all-time haze, and the bright cloud genuinely **migrates up and to the right** because later seasons' bowler-seasons genuinely sit further up and to the right. The dots do not move. Different dots light up. This honors "every ball on screen" (the all-time haze) while the season filter carries the argument, exactly as Ch 2 held worm-space and scrubbed a season pointer.
- **"The edge of the possible" is a lookup, drawn on the annotation plane.** The per-season Pareto hull (the best-anyone-managed lower-left boundary), the **ghost trail** following one great across the frontiers, and the **seven-an-over reference line** are SVG on the annotation plane, registered to field coordinates via `field.projectToCss` from `scenes/ch3.json`. The hull vertices per season are **precomputed at build time in Python** (a lookup, per the standing rule); the client interpolates between precomputed hull polylines as the pointer scrubs, and never fits a hull. The word "hull" and the word "frontier" (in its technical sense) never appear on screen; the reader sees **"the edge of the possible"** and **"the best anyone managed."**
- **The frontier retreats mostly sideways, and that is the whole point.** The cheap corner (low economy, the left) empties season by season while the deadly capacity (low strike rate, the bottom) roughly holds: bowlers can still take wickets as fast as ever, they just cannot also be cheap. Copy must land this as **"attack survived, containment died,"** never as "bowlers got worse" (the True Economy footnote proves the opposite; see §0.2 and the C3-9 affirmation).
- **Luminance and density carry the read; hue stays identity, with ONE gated exception.** Within a cloud, a ball keeps its outcome luminance (a dot is dimmest, a six brightest) as everywhere else, but at frontier scale a bowler-season reads primarily by **density and position**, not by any single ball's brightness. This density is salient, so C3-2 glosses it in one plain clause (a brighter, thicker dot just means a bowler who bowled more that season) rather than leaving a prominent visual channel unexplained. Hue stays identity (team color, WPL family) everywhere except the **one gated exception in this chapter: the dismissal rivers (C3-4)**, where the wicket subset recolors by **how the batter got out** (bowled, leg before, caught, stumped) so the streams separate. That categorical palette is beat-gated, luminance-distinct, and brighter than any team-identity color, and the reader's team glow mutes one stop through the beat so a red-team reader never confuses "my team" with "a caught dismissal" (the same guardrail Ch 2 put on its red cascade). Hue leaves identity nowhere else in Ch 3.
- **Working-memory cap holds:** ≤3 numbers per caption step, one on-screen change per step. The economy retreat and the dismissal-mix flip never share a caption step (two arguments, told one at a time).

### 0.2 Register — COUNTERREVOLUTION (on-screen copy rules, Ch 3)

Grudging admiration for the men with the ball. The bowler is the resistance: he got a worse deal every year and answered by tearing up the old plan and building a stranger, braver one. Two honesty guardrails, both load-bearing, both mirrors of the WPL-never-behind rule:

1. **The bowler is never "beaten" and never "worse."** Every retreat beat pairs the **loss** (the old containment identity died) with the **adaptation** (the game that replaced it attacks more and risks more), and the chapter affirms in the close that bowlers got **more skilled** even as their raw numbers got uglier. The tide rose. The men did not sink; they learned to swim. The True Economy evidence (a 7.5 economy went from par to elite) lives one click deep and backs this affirmation, but the affirmation itself is number-free main-flow copy so a reader who never opens a footnote still leaves respecting the bowler.
2. **The frontier's story is the retreating edge, not a correlation.** The blueprint's own sub-claim (that wicket-taking now buys containment) is **refuted** in the data: the cross-bowler economy-to-strike-rate correlation is weakly positive in both eras and does not carry the story. Main flow therefore never says "taking wickets now makes you cheap." It says only what the hull shows: the whole edge marched right, and the cheap corner went extinct. The refutation lives in the footnote as an honest "we checked, and here is why we tell it through the edge."

Banned on screen (main flow + teasers), inheriting r1a §0.4 and r2a §0.2 plus Ch 3's terms of art: *hazard, Pareto, hull, frontier (technical sense), convex, economy (bare, un-glossed), strike rate (bare, un-glossed), streamgraph, correlation, entropy, Gini, quantile, percentile, z-score, regression, distribution, park factor, inflation-adjusted, FIB.* Stage names used on screen in Ch 3:

| On screen (fan language) | Technical name (footnote only) |
|---|---|
| "the edge of the possible" / "the best anyone managed" | the Pareto hull of economy vs bowling strike rate |
| "how many runs he leaks an over" / "how cheap he was" | economy |
| "how many balls he needs for a wicket" / "how fast he strikes" | bowling strike rate |
| "cheap and deadly" (the bottom-left corner) | low economy + low strike rate |
| "the stopper" / "bowling to dry the game up" | the containment-only bowler identity (economy under 7) |
| "a ball with no run" / "a dot" | dot ball |
| "the dot's worth more now" | Dot+ (era-normalized dot manufacturing) |
| "aiming at the stumps" vs "aiming at the boundary" | bowled+lbw vs caught dismissal mix (Dismissal DNA) |
| "the keeper whips the bails off" | stumped |
| "the wide-yorker tax" / "leaking wides at the death" | death-over wide rate (the Death-Wide Tax) |
| "dots still buy wickets" / "the squeeze still cracks them" | the Dot-Ball Crack Ratio |
| "beating the tide" / "your gravity-defier" | True Economy (inflation-adjusted bowling) |
| "a spinner's league" (WPL) | high stumping / spin share |

**One label for one concept (r2a discipline).** The going-rate line, when it appears, is **"the going rate"** in reader copy (bare "par" is footnote/QA-only). Economy is always glossed the first time it appears in a scene ("how many runs he leaks an over") and then carried as "how cheap he was" / "leaking runs," never as the bare noun "economy." Bowling strike rate is always "how many balls he needs for a wicket" / "how fast he strikes," never bare "strike rate."

### 0.3 Persistence (localStorage) — no new keys

Ch 3 reads `ebe.team.v1` (payoff variant) and writes `ebe.progress.v1` via the shell on scene change (unchanged from r1a §0.3 / r2a §0.3). No new keys.

### 0.4 Timing & demand-mode

Total scroll ≈ **1,050vh**. Exactly one scrubbed field morph (free → frontier, C3-2) plus its free reverse leg (C3-9). The dismissal rivers (C3-4) are a **subset 100%-stacked band** driven by scroll progress over the held frontier plane (a subset-highlight, not a second layout morph, exactly like Ch 1's fireworks re-sort and Ch 2's run-out cascade). The season retreat (C3-3) is a **season-filter brighten + annotation scrub** over the held frontier plane (not a re-sort). All else is stepper-driven captions over a sticky canvas, 2D annotation-plane scenes, or the payoff card. The loop is provably **stopped** during: C3-1 prose, C3-2's held plane between caption steps, the C3-5 dot-grids (SVG), the C3-6 leak gauge (SVG), the C3-7 panel between states, the payoff card, and the chapter-close hold.

---

## 1. CHAPTER 3 — The Counterrevolution

Beat-budget check (blueprint §3): **hero** = Attack-Containment Frontier Drift (C3-2 orient + C3-3 the retreat); **3 supporting** = Dismissal DNA (C3-4, the rivers subset), Dot+ (C3-5, the dot-grid), Death-Wide Tax (C3-6, the leak gauge); **WPL beat** two clocks (C3-7, where the Dot-Ball Crack Ratio does its real work); **payoff** (C3-8, your gravity-defier). One controlling morph (free → frontier). One subset-highlight (the dismissal rivers). True Economy, Phase Fingerprint, FIB, the refuted correlation, Squeeze Retention's bounce-back null, and the crack-ratio construction all live in the footnote layer. Entry point: the chapter opens on the **free field** (Ch 2's close, C2-9, exhaled worm-space back to free; Ch 2 → Ch 3 is free → free, no morph). Exit: C3-9 exhales frontier → free, handing off to the (updated) end card / Ch 4.

---

### Scene C3-1 — Chapter title + turning to face the other end

**Purpose (one point):** name what this chapter is about, in fan language and in the counterrevolution register, before any data, and pre-commit the affirmation (the bowler adapted, he was not beaten) so no retreat beat can read as pure defeat.

**Particle field:** free field, dimmed one stop, loop stopped. Reader's team stays lit (identity).

**Annotation plane (three caption steps):**
1. > **Chapter 3: The Counterrevolution**
2. > For two chapters the batters have run the show. They attack from ball one, they hunted the patient anchor out of the game, and here was the sting: they did it without getting out any more often. So now turn around and look at the other end of the pitch. The men with the ball had to answer all of that.
3. > Here is the part nobody tells you. The bowlers did not just get beaten. They tore up the old plan and built a stranger, braver one. This is how they fought back. *(scroll cue)*

*(Register note: step 2 names the batting revolution as the thing the bowler has to answer, so Ch 3 reads as the reply to Ch 2's "and then what?" from the very first scene, and a deep-entry arrival still gets the setup in one self-contained clause. Step 3 seeds the counterrevolution affirmation in the same breath as it names the fight, so a reader who lands on or bounces after C3-1 never gets pure "bowlers lost." The full loss-and-adaptation pairing then recurs in every retreat beat after this one, exactly as Ch 2 paired loss with gain.)*

**Interactions:** none. **Mobile:** full-bleed title, caption card bottom-anchored. **Reduced-motion:** static stepped card. **Footnote:** none.

---

### Scene C3-2 — The frontier plane (the controlling morph)

**Purpose (one point):** every bowler's whole season is one dot on one map, and there is an edge to that map, the best anyone managed.

**Particle field:** THE morph of the chapter, scrubbed over ~200vh: every ball flies from the free field to the **frontier plane**, condensing onto its bowler-season coordinate (**x = economy** from `bowlecon.u8`, **y = bowling strike rate** from `bowlsr.u8`), landing as an all-time low-alpha haze with the busy bowler-seasons reading as dense clouds. Reader's team stays lit through the flight (object constancy).

**Destination-first scaffold (mirrors C1-2 / C2-2):** early in the scrub the empty frame fades in ahead of the points, the x-axis (`how many runs he leaks an over`, left = cheap) and the y-axis (`how many balls he needs for a wicket`, low = fast), so the reader watches points fly *into* a labeled map. The frame holds a **fixed data aspect ratio and letterboxes** on portrait rather than stretching (§0.1 honesty lock), so the bottom-left "cheap and deadly" corner sits in the same place on desktop and phone.

**Flight order:** staggered by season (2008 lands first, echoing the assembly, the wall, and the worms) so neutral pickers and deep-link arrivals have a trackable rule across the chapter's biggest morph.

**Annotation-plane overlays (SVG, crisp, drawn after the morph settles):**
- **The two axes**, glossed as above.
- **Persistent orientation anchors (drawn here, held through C3-3 to C3-8):** short end-words at the axis ends, **cheap** / **expensive** on x and **fast** / **slow** on y, sitting alongside the long gloss labels so recognition survives a scroll-back or a deep-link arrival, and a faint warm **"cheap and deadly" home zone** shading the bottom-left corner so the good corner stays fixed on screen and the later rightward drift reads as a retreat away from it.
- **The edge of the possible for the opening season**, drawn as a glowing line curving through the bottom-left, from `scenes/ch3.json` hull coords, registered via `field.getFrontierLayout()` + `field.projectToCss`.

**Caption steps (one change each):**
1. *(axes teach, nothing highlighted)* > Every dot is one bowler's whole season. Left to right is how many runs he leaked an over. Miserly on the left, expensive on the right. Every ball he bowled stacks on his dot, so a busier bowler makes a brighter, thicker smudge.
2. *(the y-axis lights, the one change)* > Top to bottom is how quickly he struck: how many balls he needed to take a wicket. Down low, wickets came fast. Up high, they came slow.
3. *(the edge line draws through the bottom-left, the one change)* > So the best place to live is the bottom-left corner: cheap and deadly at once. That glowing line curving through it is the edge of the possible, the best anyone managed that year.

**Wire cost:** two new per-point attributes, **`bowlecon.u8`** and **`bowlsr.u8`** (the bowler-season's economy and bowling strike rate, quantized to the display range, same point order as `ballsfaced.u8`). Both are extremely blocky (every ball of one bowler-season shares one value), so each is ~316KB raw and tens of KB gz. Lazy-loaded at Ch 3 entry. New layout id `frontier` (shell request, §6). Frontier positions are computed **in-shader** from these two bytes; no positions cross the wire. (Ledger entry in §2.)

**Interactions / skip:** none required; scroll lands everything. **Mobile:** the plane keeps its fixed aspect ratio and letterboxes (margin left/right or top/bottom) rather than stretching to portrait, so the corner geometry is identical to desktop; axis labels sit inside the plot. **Reduced-motion:** jump-cut from free field to the settled frontier haze (live GL end state, team glow intact) with the axes and the opening-season edge drawn statically; caption steps become a stepped card sequence.

**Footnote layer (ⓘ on step 1, the economy conventions):** how "how many runs he leaks an over" is counted (the batter's runs plus wides plus no-balls, per six legal balls; byes and leg-byes excluded, the convention documented project-wide); how "how many balls he needs for a wicket" is counted (legal balls per bowler-credited wicket; run-outs are a fielding event and are not credited to the bowler); the **minimum-sample rule** (a bowler-season needs at least 90 legal balls to draw a crisp cloud and to count toward the edge; shorter stints fade into the all-time haze); and the **undefined-strike-rate handling** (a bowler-season that took no wickets has no balls-per-wicket, so it clamps to the top "60+" bucket, labeled as such). Data source: the bowler-season table built on engine #1's season × phase baselines.

---

### Scene C3-3 — The retreat (hero: Attack-Containment Frontier Drift)

**Purpose (one point):** the cheap corner went extinct, the edge marched right, and the survivors kept their bite: attack survived, containment died.

**Particle field:** the frontier plane **holds** (no re-sort, the morph budget is spent). As the reader scrubs a season pointer 2008 → 2026, the **current season's clouds brighten** and the rest dim to the all-time haze (via `filterSeason` in dim mode, driven from `dynamicState`, §12.2 orchestrator-caveat pattern), so the bright cloud genuinely migrates up and to the right. On the annotation plane, the **seven-an-over reference line** stands fixed, a **fixed 2008 edge ghost stays greyed on screen** through the whole scrub while the **live edge of the possible re-draws** for each scrubbed season (interpolating precomputed hull polylines), so the retreat reads as a widening gap between where the edge was and where it is now rather than one ambiguous moving line, and the **ghost trail** of one great draws forward season by season. Loop stopped between steps.

**Annotation plane:**
- The **fixed 2008 edge ghost** (greyed, drawn once and held) + the **live season-swept edge** + the fixed seven-an-over vertical + the ghost trail. The retreat is the widening gap between the two edges.
- A small **season chip** (2008 … 2026) tied to the scrub position, and a **count chip** reading the share of that season's bowler-seasons left of the seven-an-over line (from `scenes/ch3.json`, never hardcoded). The season chip and count chip sit **together, next to the scrub**, so proximity ties them.
- **Label z-hierarchy (spec before build):** the **count chip is the hero number and dominates**; the reference marks are secondary and visually differentiated from each other by weight and style (the 2008 ghost edge thin and grey, the live edge bright, the seven-an-over line a plain fixed rule, the ghost trail a single gold thread); the **season chip is ambient**. Nothing at similar weight competes with the count chip.

**Caption steps (one change each):**
1. *(the seven-an-over line lights, season pointer early)* > Draw a line at seven runs an over. Leak fewer than that across a whole season and you were a genuine stopper, a bowler who dried the game right up.
2. *(scrub 2008 → 2026, the bright cloud drains rightward past the fixed line, the one change and the hero number)* > In the league's first three years, nearly a third of bowlers lived left of that line. The line has not moved. Now watch the cloud slide right, season by season, until in the last three years just one bowler in a hundred still gets there.
3. *(the ghost trail draws forward, the one change)* > The gold trail is one great, season after season, always hunting the edge. Even he gets shoved to the right. He stayed brilliant. He could not stay cheap.
4. *(the deadly axis holds while the cheap corner empties, the one change, no number, the thesis)* > Now look up and down. The bite never went, wickets come as fast as ever. What died was the double act. No one manages both any more, cheap and deadly at once, so bowlers gave up cheap and hunted wickets. Attack lived. Containment died.

*(Register: step 2 is the loss, the containment corner emptying, and it carries the chapter's single quotable number, roughly a third down to one in a hundred. Step 2 also names that the seven-an-over line never moved while the cloud drifted past it, the number-free way of signalling that part of the drain is the whole game getting dearer, not lost skill (the True Economy point, proven one click deep). Step 4 says "no one manages both any more," an observed-best claim, never the impossibility claim "you cannot," so the edge is never read as a law. Step 4 is the mandated adaptation clause inside the hero beat, so the retreat can never read as pure defeat: the bowler kept his bite and changed his aim. Working memory: the whole scene carries exactly ONE main-flow number, the share left of the seven-an-over line, 29% down to 1%. The catalog's raw counts, 49 of 169 then and 4 of 267 now, are the footnote form. Step 4 is number-free by design and lands on the thesis, not a figure.)*

**Interaction (+ skip path):** tap the ghost trail's dot in any season to name that bowler-season (player · season · how cheap he was · how fast he struck), from `scenes/ch3.json`. The captions carry the entire point; the tap adds a name, never the thesis.

**Mobile:** the season pointer is a scroll-scrubbed value, not a draggable control; the seven-an-over line and the edge are the only crisp lines (the haze reads as texture); the ghost trail is a single bright thread. **Reduced-motion:** the retreat renders as a static **two-panel small-multiple**, the 2008 cloud and edge beside the 2026 cloud and edge, with the seven-an-over line drawn on both and the ghost trail complete; chips appear as instant states.

**Footnote layer (ⓘ on step 4, the counterrevolution's honest machinery):** the **raw counts** behind the share (49 of 169 bowler-seasons under seven an over in 2008-10, 4 of 267 in 2023-26); **why the story is the retreating edge and not a correlation** (we checked whether taking more wickets now buys you a cheaper economy across bowlers, and it does not: that link is weakly positive in both eras, +0.12 then and +0.03 now, +0.34 in the WPL, so the honest way to tell the counterrevolution is the edge marching right, not a link that was never there); **True Economy** (the tide, not the men: the league's bowler-charged economy rose 7.79 to 9.38 runs an over, so a 7.5 economy went from league-par in 2009 to 1.9 runs an over BETTER than par in 2025, which is why the raw numbers get uglier while the bowling gets better); **Phase Fingerprint** (the death specialist rose and is already eroding: death overs bowled by genuine death specialists went 0.0% in 2008 to 17.3% in 2023, peaking 20.6% in 2021, then slumping, maybe as the Impact Player rule let teams stay flexible); and the **honest confound on the 2023-26 endpoint** (the same Impact Player rule that lands on the batting extinction in Ch 2 lands here too: it freed batters up, so part of the frontier's most recent rightward jump is a rule change entangled with bowler skill, not bowler skill alone, and Ch 7 pulls that thread out).

---

### Scene C3-4 — The dismissal rivers (supporting: Dismissal DNA, the subset-highlight)

**Purpose (one point):** bowlers stopped aiming at the stumps and started aiming at the boundary, and the shape of a wicket changed to prove it.

**Particle field:** a **subset 100%-stacked band chart** over the held frontier plane (a subset-highlight, it composes with `frontier` and does NOT spend a second controlling morph, exactly like Ch 1's fireworks and Ch 2's cascade). Every ball that took a **bowler-credited wicket** lifts out of its cloud and streams into a horizontal band for its dismissal kind (bowled, leg before, caught, stumped), the bands **stacked flat between a fixed 0 baseline at the bottom and 100 at the top** (NOT a wiggly centered streamgraph), each band's thickness the kind's share of all wickets, flowing left-to-right across the seasons. The flat baseline keeps every share readable against a common scale and never hides that the total is always 100%. Scrubbing back returns the wickets to their clouds (the reverse leg is free). Run-outs are excluded (they are a fielding event, told in Ch 2), so every share here shares one denominator: the wickets the bowler actually earned.

**Band order and grouping (readability lock):** bottom-to-top the bands are **bowled, leg before, stumped, caught**, so the two ways of hitting the woodwork (**bowled + leg before**) sit **adjacent, anchored to the 0 baseline, and share one hue family** (the "stumps" group), reading as one contiguous region that visibly shrinks. Caught and stumped each get their own distinct hue. Every beat then reads as a single moving boundary against a flat baseline (share-against-a-common-scale, the highest-accuracy encoding), never as band-thickness guessed off a wandering midline.

**Gated hue exception (§0.1):** the wicket subset recolors by dismissal kind for this beat only, a categorical, luminance-distinct palette brighter than any team red, **bowled and leg before sharing one hue family (the "stumps" group), caught and stumped each a distinct hue**, with the reader's team glow muted one stop through the beat (the red-team collision guard from Ch 2). Hue returns to identity the moment the bands settle back. A dev assertion warns if any dismissal tint is non-zero outside C3-4.

**Annotation plane:** the band labels grouped as drawn (**stumps: bowled · leg before**, then **stumped**, then **caught**), a **0-to-100 share axis on the left** so the flat baseline is explicit, and a season axis along the bottom, all from `scenes/ch3.json`; the era ghost convention carried from Ch 1 (the 2008 mix greyed as a reference edge on each band).

**Caption steps (one change each):**
1. *(the wickets lift out and stack into the flat-baseline bands, the one change)* > Now just the wickets. Every ball that took one lifts off the map and sorts itself by how the batter went: bowled, leg before, caught, stumped. Each colored band is one way out, and its thickness is its share of all wickets.
2. *(the stumps group narrows, the one change and the number)* > Watch the stumps group at the bottom. Bowled and leg before, the balls that beat the bat and hit the woodwork, shrank from 27 wickets in every hundred to 21. Bowlers are aiming at the stumps less.
3. *(the caught band swells, the one change and the number)* > Now the caught band, the ball skied to a waiting fielder. It swelled from 65% of wickets to 74%. Two things pushed it up: bowlers dare the batter to clear the rope, and the batter, swinging bigger than ever, keeps holing out.
4. *(the stumping band all but vanishes, the one change, the number, the thesis)* > And the stumping, the keeper whipping the bails off, almost disappeared, 4.2% of wickets down to 1.9%. The wicket did not stop coming. It just changed shape, from a ball at the stumps to a ball in the deep.

*(Register: the beat is admiration for a change of plan, not a lament. Step 3 credits both drivers of the caught rise, the bowler aiming wider AND the batter going aerial more (Ch 2's revolution), so the fingerprint is not misread as pure bowler agency. Working memory: three number pairs across three separate steps (27→21, 65→74, 4.2→1.9), never stacked in one caption. The bowled+lbw, caught, and stumped shares here are the **bowler-credited** view, which is one consistent denominator; the all-dismissal caught figure that includes run-outs, 59.9% to 72.3%, is a different denominator and lives only in the FIB footnote, so the two never sit on screen together, per §3.)*

**Interactions:** none required (the subset lands by scroll). **Mobile:** the 100%-stacked band is full-width, the grouped band labels (stumps: bowled/leg before, then stumped, then caught) stack legibly at portrait; each caption below the field. **Reduced-motion:** renders the **final settled band** (the 2026 mix) with all four bands and their labels and the 0-to-100 share axis, no sweep required, and the wickets shown already sorted.

**Wire cost:** zero new bytes on the required path. Dismissal-kind membership is a per-point flag baked at runtime from the columnar `wicket_kind` array (`field.setDismissals(...)`, the working-today path with zero pipeline dependency, exactly like Ch 2's `field.setRunouts`); the `rivers` subset capability itself is a shell request (§6) and adds no positions on the wire. **Footnote layer (ⓘ):** the exact dismissal-kind recipe (share of each `wickets[].kind` per season, bowler-credited core, run-outs separate); the **batting driver on the caught rise** (the swelling caught share is not pure bowler intent: Ch 2's aerial revolution and the Aerial Risk Ledger show batters skied far more over the era, which manufactures catches independently of where the bowler aimed, so the caught band rose because bowlers aimed wider AND batters went up more); the **caught-behind proxy** caveat (the keeper is inferred from stumping credits, covering 84% of team-seasons, with the ~16% residual documented) for readers who want caught-behind split from caught-in-the-deep; **FIB, field-independent bowling** (the deep cut: caught rose 59.9% to 72.3% of ALL dismissals while run-outs collapsed 12.0% to 5.3%, so the share of a bowler's fate that sits in a fielder's hands swelled by a fifth, which makes raw bowler numbers LESS skill-reflective in 2026 than in 2008; FIB strips exactly that drift); and the note that the WPL keeps a much fatter stumping band (5.2% to 7.9% every season), teased here and paid off in Ch 6.

---

### Scene C3-5 — The dot-grid (supporting: Dot+)

**Purpose (one point):** a dot ball is worth more now than it used to be, because the dot is drying up.

**Particle field:** frontier plane holds, dimmed one stop. Loop stopped. This is a **2D annotation-plane** beat, no re-sort.

**Annotation plane:** the **dot-grid** (2D, DOM/SVG, from `scenes/ch3.json`): one real 2009 innings and one real 2026 innings drawn side by side as **120-cell grids** (20 overs by 6 balls, one cell per ball), a **dark cell for every dot** (a ball with no run) and a lit cell for every scored ball. Each grid is **illustrative texture, a single innings and not the league**, labelled "one 2009 innings" / "one 2026 innings," and carries its own **dot-tally chip** (for example "44 dots of 120") so the quantity is read from the number, never eyeballed off a speckle. The two exemplars are **chosen at or very near each era's mean dot rate** so the picture cannot overstate (or reverse) the modest league gap. The league number, 37.6 to 33.0, is the evidence; the grids are only the feel of it.

**Caption steps:**
1. *(both grids draw)* > Here are two innings, one from 2009 and one from 2026, drawn as 120 boxes, one box per ball. A dark box is a dot, a ball the batter could not score off. Each grid shows its own dot count.
2. *(the tally chips and the league number light, the one change and the number)* > One innings is noisy, so trust the league, not the two grids. Across every ball bowled, dots fell from 37.6% in 2009 to 33.0% by 2026. The dot is drying up.
3. *(number-free thesis chip)* > So a bowler who still bowls a pile of dots today is doing something harder than the same bowler in 2009. The dot did not get easier. It got rarer, which means every one is worth more.

**Interactions:** none required. **Mobile:** the two grids stack (2009 above, 2026 below) so the dark-cell contrast survives portrait width; caption last. **Reduced-motion:** both grids static by construction; steps are instant states. **Footnote layer (ⓘ):** Dot+ (the era-normalized version: dots manufactured against an average bowler with the same over-mix in the same season, so Malinga-2010 and Bumrah-2024 sit on one leaderboard, and whether elite dot-manufacture is going extinct); the exact dot definition (a legal delivery with zero total runs); and the note that the two exemplar innings are real innings chosen from the data (not the field's own points), each picked **at or very near its era's mean dot rate**, because a single innings swings roughly 25% to 50% dots and would otherwise over- or under-state the honest 4.6-point league shift the caption cites.

---

### Scene C3-6 — The wide-yorker tax (supporting: Death-Wide Tax)

**Purpose (one point):** chasing the un-hittable ball at the death, bowlers now leak far more wides, and that is a risk taken on purpose, not sloppiness.

**Particle field:** frontier plane dims behind the gauge; loop provably stopped for the whole scene.

**Annotation plane:** the **leak gauge** (2D, DOM/SVG, from `scenes/ch3.json`): a rising fluid level reading **wides given away per 100 legal balls at the death** (overs 16 to 20), with the early-seasons level and the recent-seasons level marked, and the free-hit and wide-review rule dates pinned lightly on the side.

**Caption steps:**
1. *(the gauge and its meaning draw)* > At the death, the last five overs, bowlers now aim for the edges: the yorker into the toes, the ball climbing past the shoulder. Miss by a hair and it is a wide, a free run to the batting side. This gauge fills with wides given away per 100 balls at the death.
2. *(the level doubles, the one change and the number)* > It doubled. 3.3 wides per 100 balls at the death in the early seasons, 6.7 now. Every extra wide is a run the bowler never meant to give.
3. *(number-free thesis chip)* > This is not bowlers getting worse. Three things drive it: they chase the un-hittable ball on purpose, batters shuffle across to make good balls look wide, and umpires call the wide line tighter than they once did. The arms race, made of runs.

**Interactions:** none. **Mobile:** gauge ~45vh, full-width; caption below. **Reduced-motion:** the gauge renders at its final level, static; steps are instant states. **Footnote layer (ⓘ):** the extras recipe (wides per 100 legal balls, split out for the death overs; the all-phase wide rate rose more gently, from a 2.71 trough in 2013 to 4.78 in 2026, while the death split is the star and doubles); the **multi-causal hedge** (the doubling is not solely deliberate risk: deliberate edge-hunting, a demonstrably tighter wide-line interpretation across the era, and batter movement that forces wides all contribute, and the data cannot cleanly separate them); the honest note that the wide-review sub-metric is not computable in this data (review type only ever reads 'wicket' or is absent); and that the WPL's death-wide rate is just 2.8, the seed of the C3-7 point that the arms race is a men's-league thing.

---

### Scene C3-7 — The WPL beat (two clocks, one beat, house rule)

**Purpose (one point):** the WPL still has the containment corner the IPL lost, AND it refuses the IPL's timeline: dots still buy wickets there, and the wide-yorker arms race has not arrived. A different game, not an earlier one. (This is where the Dot-Ball Crack Ratio does its real work, and it teases the spinner's-league finding that Ch 6 pays off.)

**Particle field:** on the frontier plane, **WPL clouds brighten to full** and IPL clouds dim one stop (the mirror of Ch 1's WPL beat, a color-state change, not a re-sort). Loop renders once per state. Reduced motion: instant states.

**Annotation plane:** a compact 2D panel of **one clock and two head-to-head gauges**, deliberately different chrome so the reader never reads all three as points on one IPL timeline:
- **Containment clock (the ONLY on-timeline dial), "still has the corner":** WPL dot rate **38.5%**, needle landing at **IPL 2009**, with the IPL era-scale printed beneath **it and nowhere else**. This is the one WPL number placed on the IPL's own history.
- **Squeeze gauge (off the IPL's map), "the squeeze still cracks them":** a direct WPL-vs-IPL pair, crack ratio **1.11** in the WPL against the IPL's flat **0.84**, drawn as two bars with **no IPL-year axis** and marked "not on the IPL's timeline."
- **Arms-race gauge (off the IPL's map), "not a stage every league passes through":** a direct WPL-vs-IPL pair, death wides **2.8** vs **6.7**, again two bars, **no IPL-year axis**, marked off the timeline.

**Caption steps (all in one beat, one change each):**
1. *(the containment clock lands)* > The WPL still has the corner the IPL lost. Its dot rate, 38.5%, sits right where the IPL's did back in 2009. On this one clock it looks like a young league.
2. *(the squeeze gauge lands, the crack ratio, the one change)* > But it is a different game, not a young IPL. Squeeze a WPL batter with dot after dot and the wicket still comes, 1.11 times as often. In the IPL that same squeeze has gone quiet, down to 0.84.
3. *(the arms-race clock lands, the one change)* > And that flood of death wides from two scenes back? It never reached the WPL: 2.8 per 100 balls, not 6.7. The wide-yorker arms race is a men's-league thing, not a stage every league has to pass through.

*(Register: "still has the corner" and "a different game" are the grammatical subjects, never a deficit. One on-timeline clock plus two off-timeline head-to-head gauges are the whole point: the clock says the WPL keeps the old containment, the two gauges say it refuses the IPL's path, and all three sit in the same beat, so the single-clock framing the §2 corollary bans never appears. Only the containment dial is placed on the IPL's timeline; the squeeze and arms-race pairs carry no IPL-year axis, so the beat cannot smuggle back "the WPL is just an earlier IPL." Step 2 is a plain cross-league difference (dots still buy WPL wickets, the same squeeze has gone quiet in the IPL), never the temporal claim "the IPL learned to survive them," which one cross-league snapshot cannot support. WPL numbers render in the WPL hue, color-linked to their dials, so hue stays identity.)*

**Interactions:** none. **Mobile:** the three clocks stack (containment, squeeze, arms-race), caption last. **Reduced-motion:** brighten and dim are instant states; the panel is static SVG. **Footnote layer (ⓘ):** the crack-ratio construction (the chance of a wicket right after a run of three-plus dots, divided by the chance off a fresh ball, with the permutation and phase-stratification controls that make it honest, since pressure states also coincide with the better bowlers; middle overs, 2023-26); **what the crack ratio does NOT prove** (it is a single cross-league snapshot and does not by itself explain why IPL economies inflated; we checked whether taking wickets buys a cheaper economy across bowlers and that link is weak in both leagues, +0.12 then and +0.03 now in the IPL, +0.34 in the WPL, so read the 1.11-vs-0.84 gap as a plain difference between two leagues today, not the IPL "learning to survive" over time, which we cannot show without an IPL crack-ratio time series we do not draw); the WPL sample honesty (88 matches across four seasons, early numbers will move); the **spinner's-league tease** (the WPL keeps stumpings at 5.2% to 7.9% of wickets every season against the IPL's **1.4% in 2026** and **1.9% pooled across 2023-26**, a genuinely different dismissal ecology; note plainly that stumping share is only a **proxy** for spin, because the data has no bowler-type field at all, which is why "a spinner's league" stays out of the main flow and the full treatment is named by title, *Two Dialects*, Chapter 6); and why "behind" is the wrong word (a league can keep an old strength and refuse an old path at the same time).

---

### Scene C3-8 — Team payoff card ("Your gravity-defier")

**Purpose:** the chapter's finding, re-told in the reader's colors: the bowler-season at your franchise that beat its era's tide by the most. Strictly template + `payoff/ch3.json` (16 variants, snapshot-tested, never hand-authored).

**Particle field:** reader's team clouds brighten to full on the frontier plane, everything else dims (the frontier scene re-centered on your team's dots). One render.

**Card template — IPL picker (with a qualifying gravity-defier):**
- Header: crest + **"{Team}'s gravity-defier"**
- **The re-centered frontier:** the team's bowler-seasons lit on the plane, the named season's dot ringed, the going-rate of that year drawn as the tide line so the gap is visible.
- Body (from JSON verbatim): *"{player} · {season}. He leaked {econ} an over. In the exact overs and grounds he bowled, the going rate was {league_econ}. That is {gap} runs an over better than the tide, the biggest gap any {Team} bowler ever managed. Everyone else was drowning. He swam."*
- **Arithmetic lock (card == artifact):** `{league_econ}` is the going rate for the exact overs, phases, and grounds this bowler actually bowled (the True-Economy baseline), and `{gap}` = `{league_econ}` − `{econ}` is therefore the True-Economy differential that ranks "biggest." The visible subtraction is the ranking metric, not a simple season-average gap, so what the reader can add up on the card is exactly the number that crowned the defier.

**Card template — designed short-sample / empty state (the WPL five, and any young IPL side without enough bowler-seasons, per the pipeline's emitted flag):**
- Header: crest + **"Too soon to crown one"**
- Body (verbatim, from JSON `empty_state`): *"Four seasons is not a long enough tide to name a gravity-defier yet. Here is who is closest at {Team} so far: {player}, {season}, {econ} an over against a going rate of {league_econ} in the overs he bowled. Ask again in a few years, when the water is higher."*
- *(This is the WPL point made personal, and it is authored copy, not a blank card, per the §2 payoff-QA rule. The honest short sample is itself on-message: the tide has not risen far enough in the WPL to have drowned anyone yet.)*

**Card template — Neutral:** league-wide card, rendered from JSON verbatim: the bowler-season that beat its era's tide by the most across all of IPL history, with its gap and the going rate that year.

**Interactions (+ skip):** **[ Not your team? Change it ]** → picker (state preserved, returns here); the re-centered frontier is static otherwise. **Mobile:** full-width sheet over the dimmed field; the re-centered plane sized to portrait. **Reduced-motion:** static card, team dots lit as the end state, the ringed dot drawn, no animation. **Footnote layer (ⓘ):** True Economy in plain words (beating the tide means leaking fewer runs than an average bowler would have in the exact overs, phases, and venues this bowler actually bowled, so a modest raw economy in a high-scoring year can be a huge gap, and the `{gap}` printed on the card IS that True-Economy differential, card == artifact); the minimum-sample rule; and which franchises get the designed short-sample state and why.

---

### Scene C3-9 — Chapter close (the counterrevolution lands; hand off to Ch 4)

**Purpose:** compress the chapter to one sentence, admiration not defeat, and aim it at the rising tide.

**Particle field:** the frontier plane exhales back into the free field (the reverse of the controlling morph, fast, ~40vh, the same morph's return leg, not a second morph). Reader's team stays lit.

**Annotation plane (single caption):**
> The old stopper is gone, the bowler who dried the game up and kept it under seven an over. He did not fail. The tide came in over his head. What stands in his place attacks more and risks more, and here is the part the scoreboard hides: he is a better bowler than bowlers have ever been. He just has a far harder job. Next: the tide itself, and how high it really got.

*(The close carries both halves of the register, the loss of the containment bowler and the affirmation that the bowler got better, the tide rose, not the men, which is the True Economy point in number-free main-flow words, and then the Ch 4 handoff. It names the shape of Ch 4, "The Rising Tide," without a number, per the nav rule that titles are commitments and numbers are not. The affirmation wording is fresh, not a repeat of the retreat beats' "attack lived, containment died," so the felt turn never goes boilerplate.)*

**Interactions:** none. **Mobile:** caption bottom. **Reduced-motion:** jump-cut back to free field; static caption. **Footnote:** none.

---

## 2. R2b (Chapter 3) payload inventory (ledger deltas)

| Artifact | New in R2b | Est. size (gz) | Budget bucket |
|---|---|---|---|
| `bowlecon.u8` (per-point bowler-season economy, quantized) | **yes** | ~15-35KB (blocky, one value per bowler-season) | Ch 3 (≤2MB) ✓, lazy-loaded at Ch 3 entry |
| `bowlsr.u8` (per-point bowler-season bowling strike rate, quantized) | **yes** | ~15-35KB (blocky, one value per bowler-season) | Ch 3 ✓ |
| `scenes/ch3.json` (per-season edge polylines + ghost-trail coords + seven-an-over line + season count chips + dismissal 100%-stacked band series (bowled/lbw/stumped/caught share by season) + dot-grid 2009/2026 exemplars (at/near era-mean dot rate, with tally chips) + death-wides gauge series + WPL two-clock values + crack ratio) | **yes** | ~10-18KB | Ch 3 ✓ |
| `payoff/ch3.json` (16 "your gravity-defier" variants incl. designed short-sample states + re-centered-frontier coords) | **yes** | ~5-9KB | Ch 3 ✓ |
| Dismissal-kind membership for the rivers | client-baked from columnar `wicket_kind` (`field.setDismissals`), **0 new bytes** on the required path; optional `attrs.u8` bit re-encode later | 0 | Ch 3 ✓ |
| Frontier / rivers layouts | no new position buffers, in-shader from `bowlecon.u8` + `bowlsr.u8` + group ids + baked dismissal flag | 0 | — |
| `meta.json` (add Ch 3 files to the ledger block) | field add | ~0 | pre-assembly ✓ |

**Ch 3 total delta: ≲ 90KB gz, well under 2MB.** R1 and R2a artifacts unchanged (they render byte-identically). `pipeline/ledger.py` gains rows for each new artifact; "chapter payload within budget" stays a release pass criterion.

---

## 3. Verified-number index (single source for QA)

Every number below is the blueprint/catalog target; the **emitted artifact wins** wherever the final filtered computation differs, and QA asserts card == artifact (the same discipline R1a used for 316,199 / 938 players and R2a used for the run-out 4.6 vs 4.7 reconciliation).

| On-screen claim | Value | Source |
|---|---|---|
| Bowler-seasons under seven an over (the hero share) | 29% (2008-10) → 1% (2023-26) | catalog (Attack-Containment Frontier Drift ★); raw counts 49 of 169 → 4 of 267 are the footnote form, not main flow |
| League dot rate (the dot-grid) | 37.6% (2008-10) → 33.0% (2023-26) | catalog (Dot+); data-profile pooled (37.6 from 38.0/39.1/35.8; 33.0 from 33.9/32.9/32.3/32.7); the two grid exemplars are single innings chosen at/near each era's mean dot rate and carry numeric tally chips, illustrative only (the league number is the claim, not the grids) |
| Bowled + leg before, share of bowler-credited wickets | 27.4% → 21.3% | catalog (Dismissal DNA) |
| Caught, share of bowler-credited wickets | 65.2% → 74.1% | catalog (Dismissal DNA) — **bowler-credited denominator; NOT the FIB 59.9→72.3 all-dismissal figure, which is footnote-only, per §0.1** |
| Stumped, share of bowler-credited wickets (IPL) | 4.2% → 1.9% | catalog (Dismissal DNA); data-profile 2009 4.2 → 2026 1.4, pooled ~1.9 |
| Death-over wides per 100 legal balls | 3.3 (2008-10) → 6.7 (2023-26) | catalog (Extras Weather / Death-Wide Tax) |
| WPL death-over wides per 100 legal balls | 2.8 | catalog (Death-Wide Tax, WPL kicker) |
| WPL dot rate (containment clock) | 38.5% (≈ IPL 2009's 39.1%) | catalog (Dot+, WPL); data-profile WPL pooled (39.9/40.3/37.9/36.0) |
| Dot-Ball Crack Ratio, middle overs (squeeze clock) | WPL 1.11 vs IPL 0.84 (2023-26) | catalog (Dot-Ball Pressure Cascades) |
| WPL stumping share (spinner's-league tease, footnote) | 5.2%–7.9% every season vs IPL 2026's 1.4% | catalog (Dismissal DNA, WPL); data-profile (6.9/7.9/5.2/5.3); footnote labels both IPL endpoints (1.4% in 2026, 1.9% pooled 2023-26) so it reconciles with C3-4's main-flow 1.9%; stumping share flagged as a proxy for spin (no bowler-type field in the data) |
| True Economy (footnote) | league bowler-charged economy 7.79 → 9.38; a 7.5 economy went from par (2009) to 1.9 RPO better than par (2025) | catalog (True Economy + True Wickets per 24) |
| Phase Fingerprint (footnote) | death overs by 2×-death-indexed bowlers 0.0% (2008) → 17.3% (2023), peak 20.6% (2021), recent slump | catalog (Phase Fingerprint) |
| FIB, all-dismissal drift (footnote) | caught 59.9% → 72.3%; run-outs 12.0% → 5.3% | catalog (FIB) — **all-dismissal denominator; kept apart from the main-flow bowler-credited caught figure** |
| Refuted econ~SR link (footnote) | +0.12 → +0.03; WPL +0.34 | catalog (Attack-Containment Frontier Drift, refuted sub-claim) |
| Squeeze Retention bounce-back null (footnote) | +4.0pp then, +3.9pp now | catalog (Squeeze Retention) |
| Frontier qualification (footnote) | ≥ 90 legal balls per bowler-season; 0-wicket seasons clamp to the "60+" balls-per-wicket bucket | catalog (Attack-Containment recipe) + this storyboard |
| Axis constants (honesty-locked) | x = economy (left = cheap), display cap at the expensive end labeled `14+`; y = balls per wicket, capped `60+`; seven-an-over reference line fixed; fixed data aspect ratio, letterbox never stretch; edge = precomputed hull lookup, never client-fit; season retreat = filter brighten, never a re-sort | this storyboard (C3-2/C3-3) |
| Per-team gravity-defier figures | per-variant, from `payoff/ch3.json` verbatim | pipeline JSON |
| On-screen ball count wherever pixels are visible | 316,199 | R0 artifact |

---

## 4. R2b QA checklist (storyboard-level)

- [ ] Glossary scan: no banned term (§0.2) in any main-flow or teaser string; the stage-name table's fan phrasings used wherever a term of art is meant; **bare "economy" and bare "strike rate" appear in NO reader-facing caption or card** (they are always glossed as "how many runs he leaks an over" / "how many balls he needs for a wicket"); bare "par" confined to footnote/QA (reader copy says "the going rate").
- [ ] **Voice-guide audit (BINDING):** ZERO em dashes in any reader-facing string, **including the C3-1 title card, which reads "Chapter 3: The Counterrevolution" with a colon (matching the nav label) and is explicitly IN the scan, never treated as exempt formatting** (captions, chips, cards, footnote prose all covered); every scene ORIENTS (what the dots/axes/colors mean) before it REVEALS; one idea and one number per caption step; "you" with couch-swagger in the point, dead-plain in the orientation.
- [ ] **Register (counterrevolution) audit:** every retreat beat (C3-3 step 4, and the dot/wide theses) pairs the loss with the adaptation **inside the beat**; C3-1 step 3 plants the affirmation ("they did not just get beaten") so both halves survive a deep-entry bounce; C3-9 close carries both halves; NO beat reads as "bowlers got worse" (C3-6 step 3 explicitly says "this is not bowlers getting worse"); the True Economy affirmation reaches main flow number-free in C3-9; **C3-3 step 4 says "no one manages both any more" (observed-best), never the impossibility "you cannot"; C3-3 step 2 signals the seven-an-over line never moved while the game got dearer; C3-6 step 3 gives the death-wide rise as multi-causal (deliberate risk + tighter wide-calling + batter movement), not sole intent.**
- [ ] **Refuted-correlation honesty:** no main-flow sentence claims taking wickets now buys a cheaper economy across bowlers; the story is the retreating edge only; the +0.12 → +0.03 refutation lives in the C3-3 footnote.
- [ ] **Two-caught-denominators honesty:** main flow carries only the bowler-credited caught figure (65.2 → 74.1); the FIB all-dismissal figure (59.9 → 72.3) appears ONLY in the C3-4 footnote; the two never sit on screen together.
- [ ] **Dot-grid honesty:** the two grids are labelled single innings (not the league), each chosen at/near its era's mean dot rate, each carrying a numeric dot-tally chip; NO caption claims one grid is "visibly darker"; the evidence is the league 37.6 → 33.0, and step 2 explicitly demotes the grids ("one innings is noisy, so trust the league").
- [ ] **Dismissal-band honesty:** the rivers render as a **flat-baseline 100%-stacked band (0 at bottom, 100 at top), never a wiggly streamgraph**; a 0-to-100 share axis is drawn; band order bottom-to-top is bowled, leg before, stumped, caught so the stumps group is adjacent and baseline-anchored; each of the three number beats reads as one moving boundary; step 3 credits both the bowler's wider aim AND the batter's aerial play for the caught rise.
- [ ] Pixel-number audit: every visible ball count says 316,199; every share reads whatever `scenes/ch3.json` emits (artifact wins over blueprint copy, reconciled to the artifact, not the reverse).
- [ ] Morph budget: exactly one controlling field morph (free → frontier) + its free reverse; the dismissal rivers, the season retreat, the dot-grid, the leak gauge, and the WPL brighten are subset / filter / 2D / color-state only (no second layout re-sort).
- [ ] 16/16 payoff variants non-degenerate; designed short-sample states authored for the WPL five and any young IPL side without a qualifying bowler-season; at least one bespoke WPL-picker card ships (the short-sample card qualifies); **the card's visible `{gap}` IS the True-Economy differential (`{league_econ}` is the going rate for the exact overs/phases/grounds the bowler bowled, so `{league_econ}` − `{econ}` = `{gap}` and it equals the metric that ranks "biggest," card == artifact).**
- [ ] WPL beat reads **one on-timeline containment clock + two off-timeline head-to-head gauges (squeeze + arms-race)** in one beat; the IPL era-scale sits under the containment clock ONLY, the squeeze and arms-race pairs carry no IPL-year axis and are marked off the timeline; no sentence with the WPL as object of "behind/lags/still-only"; "still has the corner"/"a different game" is the grammatical subject; the crack ratio (1.11 vs 0.84) lands here as main flow as a **plain cross-league difference** (no "learned to survive"); the C3-7 footnote states the crack ratio does not by itself explain IPL economy inflation and repeats the +0.12→+0.03 / +0.34 refutation, flags stumping share as a spin proxy, and labels stumping periods (IPL 1.4% in 2026, 1.9% pooled 2023-26) so they reconcile with C3-4's 1.9%.
- [ ] Reduced-motion pass: every scene has its jump-cut exercised — settled frontier haze (C3-2), 2008-vs-2026 small-multiple + complete ghost trail + fixed 2008 edge ghost (C3-3), settled 100%-stacked band (C3-4), static dot-grids (C3-5), gauge at final level (C3-6), instant WPL states (C3-7), static card + lit team dots (C3-8), jump-cut back to free (C3-9). No beat requires motion or a tap to land.
- [ ] No hover-only content; all ⓘ, the ghost-trail name tap, and the change-team control are tap/keyboard; targets ≥44px.
- [ ] Hue-exception audit: the categorical dismissal palette appears ONLY during the C3-4 rivers beat (dev assertion warns if any dismissal tint is non-zero elsewhere); it is luminance-distinct and brighter than any team red; **bowled+leg before share one hue family (the "stumps" group), caught and stumped each distinct**; the team-identity glow mutes one stop through the beat (the red-team collision case is exercised); hue is identity everywhere else.
- [ ] Frontier-honesty audit: the clouds never re-sort (positions fixed per bowler-season); the season retreat is a filter brighten (real data migration), not a re-layout; the edge is a precomputed hull lookup interpolated, never client-fit; the seven-an-over line is fixed; the plane holds a fixed data aspect ratio and letterboxes on portrait (never stretches); the expensive-end cap is labeled `14+` and the balls-per-wicket cap `60+`; 0-wicket bowler-seasons clamp to `60+`, not hidden or dropped; **the fixed 2008 edge ghost stays greyed on screen through the whole scrub beside the live edge (the retreat reads as the widening gap between them); the persistent axis end-anchors (cheap/expensive, fast/slow) and the bottom-left "cheap and deadly" home zone hold through C3-3 to C3-8; the salient dot-density is glossed once in C3-2.**
- [ ] Caption grammar lint: ≤45 words/step (C3-3 steps 2 and 4 sit near the cap, verified; C3-7 step 2 trimmed to a single cross-league contrast, now well below cap with the "learned to survive" interpretation moved to the footnote), ≤3 numbers/step, one on-screen change/step; C3-3 main flow carries exactly one number (29% → 1%); C3-4's three number pairs sit in three separate steps.
- [ ] Payload ledger re-run passes with `bowlecon.u8` + `bowlsr.u8` + `scenes/ch3.json` + `payoff/ch3.json`; Ch 3 delta well under 2MB; R1 and R2a artifacts byte-identical.
- [ ] Nav: Ch 3 flipped from `soon` to live (declares `navLabel: 'Chapter 3: The Counterrevolution'`, anchor `#ch3`); removed from `FUTURE_CHAPTERS`; deep entry into `#ch3` works with no sketch/team state (neutral field + neutral payoff variant); the end card flips Ch 3 to done and teases Ch 4 as in-build.
- [ ] Multi-causality honesty: C3-3's ⓘ states the 2023-26 endpoint is entangled with the Impact Player rule (Ch 7's thread), not bowler skill alone; the True Economy footnote states raw economies rose because the tide rose, not because bowlers got worse.
- [ ] Demand-mode: idle GPU ~0 in C3-1 prose, C3-2 holds, C3-5 (SVG), C3-6 (SVG), C3-7 between states, C3-8 card, C3-9 hold.
- [ ] `?hud=1` stays dev-only; zero HUD DOM on default load.

---

## 5. Copy / design decisions made here (the blueprint left these open) — for owner sign-off at the R2 milestone review

1. **The register (COUNTERREVOLUTION) and its two guardrails.** The blueprint gave the one-liner ("bowlers abandoned the old map… stranger and braver") but not a named register or its honesty rails. Authored here: grudging admiration, the bowler as resistance, with two locks, the bowler is never "beaten" or "worse" (the True Economy affirmation reaches main flow number-free at C3-9), and the frontier's story is the retreating edge, never the refuted correlation. This mirrors Ch 2's elegy loss/gain pairing, inverted.
2. **Frontier axis orientation, with persistent on-screen anchors.** x = economy (left = cheap), y = bowling strike rate (bottom = strikes fast), promised land bottom-left. Proposed because "leaks fewer runs" reads leftward and "needs fewer balls" reads downward with an honest (non-inverted) axis, and because the retreat then runs mostly sideways, which sharpens the "attack survived, containment died" thesis (the deadly axis holds, the cheap axis empties). Because this puts "good" at bottom-left (inverting the usual good=up-right prior) and runs the hero migration up-and-right, the plane carries **persistent orientation anchors** (short end-words cheap/expensive and fast/slow at the axis ends, plus a faint warm "cheap and deadly" home zone bottom-left) that hold through C3-3 to C3-8, so the drift reads as a retreat away from a fixed good corner; the salient dot-density is glossed once in C3-2 (a brighter, thicker dot just means a bowler who bowled more). **Confirm** the exact display caps (`14+` economy, `60+` balls-per-wicket) and the banking target at build.
3. **The retreat is a filter brighten, not a Gapminder re-layout.** All bowler-seasons land at fixed all-time coordinates in the one controlling morph; the season scrub brightens the current season and dims the rest, so the visible migration is real data (later seasons genuinely sit up-and-right), never a second re-sort. This keeps the chapter inside the one-morph budget while staying Gapminder-faithful. **Confirm** the dim level for the all-time haze so the abandoned cheap corner stays faintly legible.
4. **The dismissal rivers are the Dismissal DNA beat AND the chapter's one subset-highlight**, fused for efficiency (run-outs excluded, one consistent bowler-credited denominator). They are drawn as a **flat-baseline 100%-stacked band (0 at bottom, 100 at top), not a wiggly centered streamgraph**, so each share reads against a common scale and the constant total is honest; the bands are ordered bottom-to-top **bowled, leg before, stumped, caught** so the two woodwork dismissals sit adjacent and baseline-anchored as one "stumps" group. The gated dismissal-kind hue exception is authored with Ch 2's red-cascade guardrails, with **bowled+leg before sharing one hue family** and caught and stumped each distinct. **Decision confirmed here:** categorical tint per band (needed so the shrinking stumps group reads as one contiguous region) over pure position separation.
5. **The ghost-trail great comes from the pipeline JSON, never hardcoded.** The catalog proposes Ashwin (a spinner whose career spans ~15 frontiers); the storyboard names no player, and `scenes/ch3.json` emits which bowler-season sequence draws the trail (the every-name-from-an-artifact rule).
6. **Two new per-point buffers, not one.** Ch 1 reused `ballsfaced` for the wall's x and added one byte (`wallheat`); Ch 2 reused `ballsfaced` for worm x and added one byte (`cumruns`). The frontier plane has no reusable axis, so it needs two new bytes (`bowlecon`, `bowlsr`), both extremely blocky and cheap. Flagged so the ledger reviewer expects two, not one.
7. **Frontier qualification and the undefined strike rate.** Bowler-seasons under 90 legal balls fade into the all-time haze rather than drawing a crisp cloud (and do not count toward the edge); 0-wicket bowler-seasons have no balls-per-wicket and clamp to the labeled `60+` bucket rather than being dropped (honoring "every ball on screen"). **Confirm** the 90-ball threshold against the emitted bowler-season table.
8. **"Your gravity-defier" short-sample state extends to any young IPL side, not just the WPL.** GT / LSG and the WPL five likely lack a settled tide to crown a defier against; the pipeline emits the `empty_state` flag per variant and the storyboard does not hardcode which. **Confirm** the exact franchise list against the emitted `payoff/ch3.json`.
9. **Crack ratio placement and honest framing.** It lands as MAIN FLOW in the WPL beat (C3-7 step 2), not a footnote, because that is where it does its real work (dots still buy wickets in the WPL, gone quiet in the IPL), per the blueprint. Step 2 is a **plain cross-league difference** (1.11 vs 0.84), never the temporal claim "the IPL learned to survive them," which a single cross-league snapshot cannot support; the footnote states outright that the crack ratio does not by itself explain IPL economy inflation and repeats the +0.12→+0.03 / +0.34 refutation there. The WPL panel is **one on-timeline containment clock plus two off-timeline head-to-head gauges** (squeeze, arms-race) so the shared clock chrome cannot smuggle back the single-clock framing. Its construction (the permutation and stratification controls) lives one click deep.
10. **Stage names (Ch 3 roster).** Authored per the glossary rule (§0.2 table). Sign off before R2 copy freeze, alongside the Ch 2 roster.
11. **The dot-grid is illustrative texture; the league number is the evidence.** Two single innings cannot show a 4.6-point league shift (about 5 dark cells of 120) and could individually reverse it, so each grid is labelled a single innings, chosen at or near its era's mean dot rate, and carries a numeric dot-tally chip; the "visibly darker" claim is dropped, and step 2 explicitly demotes the grids ("one innings is noisy, so trust the league") and lands on the league figure (37.6 → 33.0), not the eye. **Confirm** the two exemplar innings against the emitted per-innings dot rates.
12. **The gravity-defier card's visible gap IS the True-Economy differential.** `{league_econ}` is the going rate for the exact overs, phases, and grounds the bowler bowled (the True-Economy baseline), so `{league_econ}` − `{econ}` = `{gap}` is both what the reader can add up on the card and the metric that ranks "biggest," keeping card == artifact. **Confirm** the pipeline emits the matched baseline as `{league_econ}` (not a plain season average) so the on-card subtraction is self-consistent.

---

## 6. Integration notes (shell + pipeline + composition)

**Shell requests (new field capabilities, owned by the story-shell architect, requested here, not forked):**

- **New layout id `frontier`** (`SceneFieldState.layout`): x = `bowlecon.u8`, y = `bowlsr.u8`, rendered as an all-time low-alpha haze with dense per-bowler-season clouds; in-shader, no positions on the wire. The plane uses a **fixed data aspect ratio independent of viewport and letterboxes on portrait** (so the bottom-left corner geometry survives mobile), exactly the honesty lock Ch 2 put on `worms`. This is Ch 3's single controlling morph (free → frontier), analogous to Ch 1's `wall` and Ch 2's `worms`. Add `frontier` to `LayoutId` + `LAYOUT_CODE`. Expose **`field.getFrontierLayout()`** (returning the fixed-aspect box + axis caps + the seven-an-over line's world x + the world coords for the persistent axis end-anchors (cheap/expensive, fast/slow) and the bottom-left "cheap and deadly" home-zone box, rebuilt on resize) and a **`frontierPoint(layout, economy, ballsPerWicket)`** mapping (the exact shader mapping, so the SVG edge/ghost-trail/reference-line vertices from `scenes/ch3.json` register to field coordinates and can never drift from the GL haze).
- **New subset capability `rivers`** (a cross-cutting modifier like `highlight` / `resort` / `cascade`, does NOT spend a second controlling morph): the wicket subset streams out of the frontier clouds into a **per-dismissal-kind 100%-stacked band with a fixed 0 baseline** (NOT a wiggly streamgraph) and back. Proposed shape mirroring §9's `resort` and §14's `cascade`:
  ```ts
  rivers?: {
    class: 'wicket';         // the wicket subset (bowler-credited)
    engage: number;          // 0 = points in their clouds · 1 = fully stacked into the flat-baseline bands
    kinds: ('bowled'|'lbw'|'stumped'|'caught')[]; // band order bottom→top: stumps group (bowled,lbw) anchored to the 0 baseline, then stumped, then caught filling to 100
    tint: number;            // categorical dismissal-kind recolor strength 0..1 (gated hue exception; bowled+lbw share one hue family, caught and stumped each distinct)
    othersDim?: number;      // luminance × for non-wicket points (default 0.12)
    muteIdentity?: number;   // team-glow desaturation through the beat (default 1)
  } | null;
  ```
  `engage` lerps like any scalar during the scene's morph (wickets fly out and stack into their kind's band, thickness = that kind's share by season, the four bands always summing to the full 0-to-100 height); the next scene declares no `rivers`, so `engage` lerps back to 0 and the wickets settle into their clouds (the reverse leg is free). The `kinds` order keeps **bowled and leg before adjacent and baseline-anchored** so the "stumps" group reads as one shrinking region. The `tint` categorical palette must be luminance-distinct and brighter than any team red (bowled+lbw share one hue family), and `muteIdentity` desaturates the reader's team glow one stop for the beat (red-team collision guard, §0.1). Reduced motion jump-cuts to `engage:1` (the settled 100%-stacked band). Anchor the labels and the 0-to-100 share axis with a `field.getRiversLayout()` returning per-band world y-centers and the baseline/top world y.
- **Dismissal-kind membership — `field.setDismissals(kindByIndex)` (read this).** Membership is a per-point GL flag seeded from `attrs.u8` bits, but the pipeline has not re-encoded those bits yet, so the scene supplies membership at runtime from the columnar `wicket_kind` array, the working-today path with zero pipeline dependency, exactly like Ch 2's `field.setRunouts`:
  ```ts
  // once, when the scene mounts, before the rivers engage:
  const kind = new Int8Array(arrays.wicketKind.length).fill(-1);
  for (let i = 0; i < arrays.wicketKind.length; i++) {
    const k = arrays.wicketKind[i];              // '', 'bowled', 'lbw', 'caught', 'stumped', 'run out', …
    if (k === 'bowled') kind[i] = 0;
    else if (k === 'lbw') kind[i] = 1;
    else if (k === 'caught' || k === 'caught and bowled') kind[i] = 2;
    else if (k === 'stumped') kind[i] = 3;       // run out / retired excluded (fielding events)
  }
  field.setDismissals(kind);                     // baked into aDismissal ONCE, no per-frame cost
  ```
  The point order of the columnar `wicket_kind` array IS the field's point order (same as every per-point buffer), so index `i` is the field index to flag. Call `setDismissals` once; it O(n)-bakes and renders (demand mode preserved). When the pipeline re-encodes `attrs.u8` for dismissal kind, the seed covers it and `setDismissals` becomes optional.
- **`bowlecon.u8` + `bowlsr.u8` loaders** (parallel to `ballsfaced.u8` / `cumruns.u8`, normalized 0..1 GPU-side into the fixed-aspect box). Both are no-ops for R1 and R2a scenes (byte-identical rendering preserved; `frontier` is never a layout before Ch 3).
- **The season retreat reuses the existing season filter (§12).** No new capability: C3-3 brightens the scrubbed season and dims the rest with `filterSeason` in `dim` mode, driven from `dynamicState(progress, held) => ({ ...held, filterSeason })` (the §12.2 orchestrator-caveat pattern, so a stray scroll re-application cannot revert the scrub). The team ignite still wins on top (personalization survives into the payoff).

**Pipeline requests (owned by the pipeline; `static/data/**` is never hand-edited):**
- Emit `bowlecon.u8` and `bowlsr.u8` (per-point bowler-season economy and bowling strike rate, quantized to the display ranges in §3, same point order as `ballsfaced.u8`; flag or clamp sub-90-ball bowler-seasons; clamp 0-wicket seasons to the `60+` bucket).
- Emit `scenes/ch3.json` (per-season edge polylines + ghost-trail bowler-season coords + the seven-an-over line + per-season under-seven share for the count chip + dismissal-river band series by season + the two dot-grid exemplar innings, 2009 and 2026, 120 cells each + the death-wides gauge series + the WPL two-clock values + the crack ratio) and `payoff/ch3.json` (16 gravity-defier variants incl. designed short-sample states + re-centered-frontier coords; the snapshot harness asserts 16/16 non-degenerate and card == artifact for every on-screen number).
- Optionally re-encode `attrs.u8` bits for dismissal kind (the rivers seed), a re-encode exactly like Ch 1's bit-5 top-10 flag and Ch 2's bit-6 run-out flag; a no-op for R1/R2a scenes until consumed. The client-baked path (`setDismissals`) makes this optional for R2b.
- **Engine dependency:** engine #1 (season × phase × venue par / SR+, built in R2a) powers "the going rate" tide line on the payoff card and the True Economy footnote. No new engine (per the release note); the frontier's economy/strike-rate table is a direct roll-up, not a model.

**Composition / nav:**
- `+page.svelte` composition order becomes coldopen → picker → ch1 → ch2 → **ch3** → endcard (→ sandbox as its live navLabel). Ch 3 opens from Ch 2's exhaled free field.
- `navplan.ts`: remove `'Chapter 3: The Counterrevolution'` from `FUTURE_CHAPTERS`; the Ch 3 scenes declare `navLabel: 'Chapter 3: The Counterrevolution'` (anchor `#ch3`) so it becomes a live nav item.
- **End-card update (owned by the endcard builder):** flip the R2a "Chapter 3… in build" tease to "Chapter 3 — The Counterrevolution · done" and tease Chapter 4 ("The Rising Tide — while batters and bowlers fought, the water level rose") with an `in build` tag.
- New scene directory `src/lib/scenes/ch3/` (exports `scenes: SceneDef[]` in reading order, C3-1..C3-9; scene data at `data/scenes/ch3.json`, cards at `data/payoff/ch3.json`, read through `$app/paths` `base`); footnote registry entries for the economy conventions + minimum sample, the retreat's raw counts + refuted correlation + True Economy + Phase Fingerprint + Impact-Player confound, the dismissal recipe + caught-behind proxy + FIB, Dot+, the death-wide recipe, and the crack-ratio construction + WPL sample honesty + spinner's-league tease.

---

## 7. Where this storyboard leaves a call to the owner/pipeline (summary)

Open calls, all flagged inline above and gathered here for the R2 review: (a) the frontier display caps and banking target (§5.2); (b) the all-time-haze dim level so the abandoned cheap corner stays legible (§5.3); (c) the exact categorical hues for the dismissal bands, the stumps group (bowled+lbw) vs caught vs stumped, luminance-distinct and brighter than any team red (the flat-baseline 100%-stacked band and tint-per-band choice is now decided in §5.4; only the specific hues remain to confirm); (d) the ghost-trail bowler, emitted by the pipeline, catalog proposes Ashwin (§5.5); (e) the 90-ball frontier threshold and the 0-wicket clamp, confirmed against the emitted bowler-season table (§5.7); (f) the exact franchise list that gets the designed short-sample gravity-defier state (§5.8); (g) the Ch 3 stage-name roster sign-off at copy freeze (§5.10). None of these change the chapter's shape; each is a constant or a name the pipeline owns, and the honesty rules above hold regardless of the final value.

---

## 8. Revision notes (design-audit pass)

Applied against the design-audit issue list. Must-fix and should-fix all applied; every "consider" applied too (each strengthened the beat and several folded into a should-fix).

**Must-fix**
- **Em-dash in the title (C3-1 step 1).** Changed "Chapter 3 — The Counterrevolution" to "Chapter 3: The Counterrevolution" (colon, matching the nav label). Added the title card to the §4 voice-guide scan so it is not treated as exempt formatting.

**Should-fix**
- **C3-5 dot-grid overstates the league gap.** Demoted the grids to illustrative texture: each is labelled a single innings (not the league), chosen at/near its era's mean dot rate, and carries a numeric dot-tally chip. Dropped "visibly darker/fewer dark cells." Step 2 now demotes the grids ("one innings is noisy, so trust the league") and carries the league figure (37.6 → 33.0) as the evidence. New §4 dot-grid-honesty check; §3 and §5.11 updated.
- **C3-4 wiggly streamgraph.** Switched to a flat-baseline 100%-stacked band (0 at bottom, 100 at top) with a 0-to-100 share axis. Bands ordered bottom-to-top bowled, leg before, stumped, caught, so the two woodwork dismissals sit adjacent and baseline-anchored as one "stumps" group sharing one hue family; caught and stumped each distinct. §6 `rivers` shape, §4 hue-exception + new dismissal-band check, §5.4 updated.
- **C3-3 retreating edge underpowered.** A fixed, greyed 2008 edge ghost now holds on screen through the whole scrub beside the live edge, so the retreat reads as the widening gap between the two edges. Z-hierarchy spec added (count chip dominant, edges/lines differentiated, season chip ambient), chips grouped by the scrub.
- **Unexplained density channel.** C3-2 step 1 now glosses density in one plain clause ("a busier bowler makes a brighter, thicker smudge"); §0.1 notes the gloss.
- **Axis direction cues only in captions.** Persistent end-anchors (cheap/expensive, fast/slow) added at the axis ends and held through C3-3 to C3-8; §0.1, C3-2 overlays, §5.2, §6 getFrontierLayout updated.
- **C3-7 crack-ratio temporal overclaim.** Step 2 softened to a plain cross-league difference (dots still buy WPL wickets, the same squeeze has gone quiet in the IPL), dropping "the IPL learned to survive them." The C3-7 footnote now states the crack ratio does not by itself explain IPL economy inflation and repeats the +0.12 → +0.03 / +0.34 refutation at the point of claim.
- **C3-3 hero impossibility claim.** Step 2 signals the seven-an-over line never moved while the cloud drifted past it (the game got dearer); step 4 now says "no one manages both any more" (observed-best), not "you cannot."
- **C3-4 caught-rise single-cause.** Step 3 credits both drivers (bowlers aim wider AND batters go aerial more, Ch 2's revolution); the footnote adds the batting-driver disclosure.
- **C3-6 death-wide single-cause.** Step 3 now gives three drivers (deliberate risk + tighter wide-calling + batter movement); the footnote adds a multi-causal hedge. Register kept admiring ("this is not bowlers getting worse").
- **Spinner-proxy leap.** The C3-7 tease footnote now states plainly that stumping share is only a proxy for spin (no bowler-type field in the data); "a spinner's league" stays out of main flow.

**Consider (all applied)**
- **Good-corner gestalt.** A faint warm "cheap and deadly" home zone anchors the bottom-left through the frontier scenes, so the rightward drift reads as retreat away from a fixed good corner (folds in with the axis end-anchors).
- **Shared clock chrome.** The WPL panel is now one on-timeline containment clock (IPL era-scale beneath it only) plus two off-timeline head-to-head gauges (squeeze, arms-race) with no IPL-year axis, so the single-clock framing cannot return.
- **C3-7 step 2 density.** Trimmed to one idea (the interpretation moved to the footnote), now below the word cap.
- **Two stumping figures.** The C3-7 footnote labels both IPL endpoints (1.4% in 2026, 1.9% pooled 2023-26) so they reconcile with C3-4's main-flow 1.9%.
- **Card arithmetic.** The gravity-defier card's `{league_econ}` is the going rate for the exact overs/phases/grounds bowled, so `{league_econ}` − `{econ}` = `{gap}` is the True-Economy differential that ranks "biggest" (card == artifact); §4 and §5.12 lock it.
- **C3-3 label hierarchy.** Explicit z-hierarchy specified before build (added above).

*End of storyboard.*
