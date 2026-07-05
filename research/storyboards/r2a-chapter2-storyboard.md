# R2a Storyboard — Chapter 2: The Last of the Anchors

**Status:** implementation truth for R2a (Chapter 2 only). Where this document and older blueprint copy disagree, this document wins (it encodes the §7 RESOLVED owner decisions — Ch 2 register = **elegy**, WPL = variable placement / two-clocks). Where this document and the blueprint's *standing rules* (§2) disagree, the standing rules win — no scene below may violate them. Modeled on `r1a-storyboard.md`; R2a also builds engine #1 (season × phase × venue par / SR+) and engine #5-full (entry states), and Chapter 3 ships alongside in R2 but is a **separate storyboard** — nothing here builds Ch 3.

**Sources of record:** `research/experience-blueprint.md` (§2 standing rules, §3 Chapter 2, §5 engine build order, §7 RESOLVED #3 register decision), `research/metrics-catalog.md` (Anchor Extinction Index, Run-Out Extinction Curve, Ball-by-Ball DNA, Gear-Shift Detector, New-Batter Tax, Break-Even Running, Milestone Braking Index — verified recipes + teasers), `research/data-profile.md` (dismissal-mix + scoring ground-truth tables), `web/src/lib/story/CONTRACT.md` (SceneFieldState, layout ids, subset/resort/filter capabilities, footnote registry, nav), `web/static/data/*` (R0/R1 artifacts).

**Hard invariants carried by every scene (do not re-litigate per scene):**
demand-mode rendering (loop stops whenever no morph/scrub/interaction is active) · payload ledger (≤2MB gz incremental for Ch 2) · reduced-motion = live-rendered end-state jump-cuts, never baked frames · no hover-only content · mobile-first · **exactly one controlling morph in Ch 2 (free field → innings worm-space)**; everything else is a subset-highlight or a 2D annotation-plane scene · GitHub Pages base path via `$app/paths` · byte-deterministic pipeline · no WASM · glossary rule (no statistical term of art in main flow; technical names live in the footnote layer) · **WPL never "behind"; every WPL beat is two clocks in one beat** · on-screen ball count is **316,199** wherever pixels are visible · **R1 scenes must still render byte-identically** — every Ch 2 capability is a no-op when its scene isn't active · **register is ELEGY** — affectionate farewell to the anchor; the thesis stays celebratory (the game's gain is real).

---

## 0. Global grammar (Chapter 2 deltas on top of r1a §0)

Everything in `r1a-storyboard.md` §0 (encoding grammar, one-message-per-scene, annotation-guided reading order, numbers style, footnote progressive disclosure, timing/scroll notation, persistence, register rules) carries forward unchanged. Ch 2 adds:

### 0.1 Encoding grammar — worm-space (cognitive-design)

- **Position IS the argument (same as Ch 1).** Ch 2's controlling layout, **`worms`**, positions every ball by **x = the batter's ball-index in the innings** (balls-faced-so-far — the *same* channel the ignition wall used, reused for cross-chapter continuity; here the display extent runs longer, ~1 → 60+, so long anchor innings actually crawl across the frame) and **y = the batter's cumulative runs in that innings so far**. Consecutive balls of one batter-innings form a rising staircase — a **worm**. **Slope = strike rate**: the league's par innings sprints up-and-right; an anchor's worm crawls along the floor. This is the single most important encoding in the chapter and the reason the morph is worth its budget — "slow" becomes *literally* a shallow line. **The plot's *data* aspect ratio is fixed — banked toward ~45° — independent of the viewport**, so the steep-par-vs-shallow-anchor *angular* difference reads identically on a desktop landscape frame and a portrait phone: the frame **letterboxes** (adds margin), the worm-space itself never stretches x or banks the worms toward vertical (the "sprints vs crawls" pop must not weaken on the primary — mobile — target).
- **Luminance and figure-ground carry the population story; hue never does.** The full 316k field morphs into worm-space as a **uniform low-alpha density haze** ("every ball on screen exactly once", honoring the device without a hairball). The haze is a **wedge** — densest at the bottom-left (every innings starts near 0 runs / low ball-index) and sparse toward the top-right — so the two exemplar lines sit in very different clutter, and the reader has to be able to track **the anchor** (the chapter's protagonist) *against* par *and* the haze. Therefore: **the anchor worm gets the dedicated figure channel and is the highest-contrast mark in the frame — higher than par.** It is drawn as a **dark casing/halo behind a brighter stroke** (Tufte layering), with the haze alpha **locally attenuated in a corridor beneath it** so figure separates cleanly from ground in exactly the dense low region it crawls through. The **par worm** is crisp but deliberately **subordinate in the figure hierarchy** — it already pops on its own, because it climbs up-and-right into the *sparse* zone; making par the brightest thing was the inverted, figure-ground-failing default and is explicitly rejected. Both, plus the season's **K exemplar anchor worms**, live on the **annotation plane** (SVG, registered to field coordinates), never as thousands of GL polylines. As seasons scrub, the drawn anchor-worm count thins — species decline as a preattentive quantity change. *(The "an anchor" direct label is drawn high-contrast even though its line is subtle — the label must never be the weak link.)*
- **One gated hue exception (documented, like Ch 1's era-recolor).** The run-out cascade (C2-4) **flashes matched points red** before they fall — red as *danger/loss*, a beat-gated dramatic highlight, not a persistent quantity encoding. The cascade red is specified **brighter and more saturated than any team-identity red** (RCB / PBKS / SRH glow) **and luminance-distinct from the dark low-alpha haze** — the signal reads on luminance, not hue alone. Because several franchises glow red, the **team-identity glow is muted/desaturated one stop through the cascade** so a red-team reader never confuses "my team" with "a run-out" (the *fall* — common fate — still disambiguates on motion). It is the one place in Ch 2 hue leaves identity, bounded entirely to the cascade beat (0 elsewhere); a dev assertion + QA line (including the red-team collision case) guard it. Everywhere else hue is identity only (team color, WPL family).
- **Working-memory cap holds:** ≤3 numbers per caption step; one on-screen change per step. The run-out curve and the anchor-population curve never share a caption step (two extinctions, told one at a time).

### 0.2 Register — ELEGY (on-screen copy rules, Ch 2)

Affectionate farewell. The anchor is *mourned*, the game's gain is *affirmed in the same breath* — no beat is allowed to read as nostalgia-for-anchors (the §7 RESOLVED #3 risk note). Every extinction beat pairs a loss clause with a celebratory clause ("hunted out — and the game is faster for it"). Banned on-screen (main flow + teasers), inherited from r1a §0.4 plus Ch 2's terms of art: *hazard, survival curve, changepoint, PELT, Poisson, cluster, occupancy, Gini, percentile, z-score, par model, phase-par, linear weight, run-expectancy.* Stage names used on screen in Ch 2:

| On screen (fan language) | Technical name (footnote only) |
|---|---|
| "the anchor" / "the careful accumulator" | a batter-season below 0.85× the day's going rate, 15+ balls, boundaries < 12% of balls faced |
| "an innings drawn as a rising line" / "the worm" | cumulative-runs trajectory on the balls-faced axis (broadcast term, fan-safe) |
| "the day's going rate" / "what par was doing" | season × phase par strike rate (engine #1) |
| "the risky single" / "turning for the sharp two" | run-out dismissals as a share of all dismissals |
| "the innings had gears" / "one gear: flat out" | Gear-Shift Detector innings-shape taxonomy (two-act share) |
| "what a wicket still costs" | New-Batter Tax (post-wicket 10-ball run-rate dip vs par) |
| "the brake at fifty" (footnote beat) | Milestone Braking Index |
| "running got safer" (footnote beat) | Break-Even Running |

**Bare "par" is footnote/QA-only.** Reader-facing captions and the payoff card always say **"the day's going rate" / "the day's rate"** for the season × phase par line — one label for one concept, everywhere (the scene's own glossary discipline: two labels for one thing forces a recognition cost). "Par" survives only in the footnote layer, the verified-number index, and QA copy. (§4 glossary scan enforces.)

### 0.3 Persistence (localStorage) — no new keys

Ch 2 reads `ebe.team.v1` (payoff variant) and writes `ebe.progress.v1` via the shell on scene change (unchanged from r1a §0.3). No new keys.

### 0.4 Timing & demand-mode

Total scroll ≈ **1,000vh**. Exactly one scrubbed field morph (free→worms, C2-2) plus its free reverse leg (C2-9). The run-out cascade (C2-4) is a **season-swept subset flash+fall** driven by scroll progress (not a second layout morph). All else is stepper-driven captions over a sticky canvas, 2D annotation-plane scenes, or the payoff card. The loop is provably **stopped** during: C2-1 prose, C2-3's held worm-space between caption steps, the C2-5 gearbox contrast (SVG), the C2-6 aftershock strip (2D), the C2-7 panel, the payoff card, the chapter close hold.

---

## 1. CHAPTER 2 — The Last of the Anchors

Beat-budget check (blueprint §3): **hero(s)** = Anchor Extinction Index (C2-2/C2-3) + Run-Out Extinction Curve (C2-4); **3 supporting** = Ball-by-Ball DNA occupancy (fused into C2-3's chip), Gear-Shift (C2-5), New-Batter Tax (C2-6, the sole coda); **WPL beat** (C2-7); **payoff** (C2-8). One controlling morph (free→worms). One subset-highlight (run-out cascade). Break-Even Running + Milestone Braking Index → footnote layer. Entry point: the chapter opens on the **free field** (Ch 1's close, C1-8, exhaled the ignition wall back to free; Ch 1→Ch 2 is free→free, no morph). Exit: C2-9 exhales worms→free, handing off to the (updated) end card / Ch 3.

---

### Scene C2-1 — Chapter title + the eulogy

**Purpose (one point):** name the thing that is dying, in fan language and in the elegy register, before any data — and pre-commit the celebratory thesis so the extinction never reads as mourning-for-its-own-sake.

**Particle field:** free field, dimmed one stop, loop stopped. Reader's team stays lit (identity).

**Annotation plane (three caption steps):**
1. > **Chapter 2 — The Last of the Anchors**
2. > Every team once had one. When a wicket fell, he walked in and did the unglamorous work — saw off the good balls, kept the score ticking, **held the innings together** while the others swung. The game had a name for him: **the anchor**. Then a revolution in how the game bats — flat out, from the first ball — came looking for him.
3. > We came to say goodbye — **to the man, not the runs.** The game he built is faster now. *(scroll cue)*

*(Register note: step 2 is the praise, and its last clause **names the hunter** — the batting revolution — so Ch 2 reads as the answer to Ch 1's "and then what?" from the very first scene (returning readers recognize it; a deep-entry arrival gets a self-contained clause). Step 3 is the farewell but **seeds the celebratory thesis in the same breath** ("to the man, not the runs — the game he built is faster now"), so both halves of the elegy are present even on a bounce — a reader who lands on or leaves after C2-1 never gets pure anchor-nostalgia (the §7 RESOLVED #3 risk). The full loss/gain pairing then recurs in every extinction beat after this one.)*

**Interactions:** none. **Mobile:** full-bleed title, caption card bottom-anchored. **Reduced-motion:** static stepped card. **Footnote:** none.

---

### Scene C2-2 — The worm field (the controlling morph)

**Purpose (one point):** an innings is a rising line; the league's line sprints and the anchor's line crawls — and here is every innings ever, drawn at once.

**Particle field:** THE morph of the chapter, scrubbed over ~180vh: every ball flies from the free field to **worm-space** — **x = balls faced so far** (1 → 60+, capped bucket at the right edge, **labeled `60+` everywhere it renders**, desktop and mobile — an open bucket never masquerades as a plain value), **y = cumulative runs in the innings so far** (0 at the bottom → capped top). The field lands as a **low-alpha density haze** — 316k balls present, no point rendered twice. Reader's team stays lit through the flight (object constancy).

**Destination-first scaffold (mirrors C1-2):** early in the scrub the empty worm frame fades in ahead of the points — the x-axis line (`balls faced 1 … 60+`), the y-axis (`runs`), and a faint diagonal guide laid **exactly where the par worm will land** (a pre-echo the par worm *overwrites* when it draws in step 2, so there are never two competing diagonals asking "which line is par?") — so the reader watches points fly *into* a labeled frame. The frame holds the fixed ~45° data aspect ratio and **letterboxes** rather than stretching (§0.1).

**Flight order:** staggered by season (2008 lands first, echoing the assembly and the ignition wall's "oldest lands first") so neutral pickers and deep-link arrivals have a trackable rule across the chapter's biggest morph.

**Annotation-plane overlays (SVG, crisp, drawn after the morph settles):**
- **The anchor worm (the protagonist — highest-contrast mark in the frame).** A single shallow-rising line rendered in the **dedicated figure channel**: a dark casing/halo behind a brighter stroke, with the haze locally attenuated in a corridor beneath it (§0.1) so it separates from the dense low haze it crawls through. A real qualifying anchor innings from an early season, its balls registered to their field coordinates via `field.projectToCss`. Titled **"an anchor"** in a **high-contrast** label (the line is subtle by design — the label is not).
- **The par worm** — one crisp, frenetic line climbing steeply: the season's average batter innings. Present and legible but deliberately **subordinate to the anchor in the figure hierarchy** — it already pops, because it travels up into the sparse zone. Titled in-frame: **"the day's going rate."**

**Caption steps (one change each):**
1. *(axes teach — nothing highlighted)* > Draw an innings as a rising line: **runs climbing with every ball faced.** Steep line, fast scoring. Flat line, slow.
2. *(the par worm draws — the one change)* > This is what a normal innings looks like now — **it sprints.** The day's going rate barely pauses for breath.
3. *(the single exemplar anchor worm draws beneath it, in its figure channel — the highest-contrast mark, and the one change)* > And this is **an anchor.** Same runs to chase, a different animal entirely — patient, boundary-light, **holding on.** Every innings ever bowled is in the haze behind them.

**Wire cost:** one new per-point attribute — **`cumruns.u8`** (batter's cumulative innings runs, cap 255; an innings rarely exceeds 175, so almost never clamped), ~316KB raw / tens of KB gz, lazy-loaded at Ch 2 entry. **x reuses the existing `ballsfaced.u8`** (already capped at 255 on the wire; the wall display-clamped it at 30, worm-space display-clamps at 60 — no new x buffer). Worm-space positions are computed **in-shader** from `ballsfaced` + `cumruns`; no positions cross the wire. New layout id `worms` (shell request — see §6). (Ledger entry in §2.)

**Interactions / skip:** none required; scroll lands everything. **Mobile:** the worm frame keeps its **fixed ~45° data aspect ratio and letterboxes** (margin top/bottom) rather than stretching to portrait — the steep-vs-shallow *angular* contrast is identical to desktop; y-axis labels inside the plot (left-anchored); the anchor worm (in its figure channel) and the par worm are the only crisp lines (the haze reads as texture). **Reduced-motion:** jump-cut from free field to the settled worm-space haze (live GL end state, team glow intact) with the anchor worm drawn statically in its figure channel (casing + brighter stroke, corridor attenuation) and the par worm subordinate; caption steps become a stepped card sequence.

**Footnote layer (ⓘ on step 3 — the anchor definition, engine #1 dependency):** the technical anchor definition (15+ balls faced; strike rate below 0.85× the season × phase **par** strike rate; boundary balls — `runs.batter ≥ 4` — under 12% of balls faced), **why 0.85× phase-par rather than a raw SR cutoff** (a 120 SR meant something different in 2009 than 2026 — the bar has to move with the era), and the **threshold sensitivity sweeps** the catalog mandates (how the extinction curve shifts under 0.80×/0.85×/0.90× par and 10%/12%/15% boundary caps — the finding survives every reasonable cut). Data source note: par from engine #1 (season × phase). ⓘ also names "the worm" as the broadcast term for a cumulative-runs line.

---

### Scene C2-3 — The thinning (hero: Anchor Extinction + the occupancy number)

**Purpose (one point):** season by season the crawlers thin out — a whole way of batting has been hunted out of the league (and the game is faster for it).

**Particle field:** worm-space **holds** (no re-sort — the morph budget is spent). Loop stopped between steps. The haze stays; the **annotation plane** does the work: as the reader scrubs a season pointer 2008 → 2026, the par worm re-draws steeper each season and the season's **K exemplar anchor worms** (each in the anchor **figure channel**, §0.1) fade in/out — the drawn count visibly drops from a small thicket (early band) to one or two (late band). **The thicket is explicitly illustrative — labeled on the plane "a sample of that season's anchors," never presented as a headcount** — and K is **pinned to the emitted per-season anchor ball-share** (the headline 14.8→8.5 quantity the caption actually cites) so the *drawn* thinning tracks a ratio the reader is being told, floored at 1 until true extinction, capped for legibility. The stronger magnitude claim ("few enough to name") rides the **conservation chart + emitted `last_survivors`**, not the drawn thicket — so a capped/floored draw can never silently over- or under-state the true decline. Exact K cap + scaling curve: owner/pipeline sign-off, §5.3. "The crawlers thin out" is a preattentive count change on the annotation plane, not a second field morph.

**Annotation plane:**
- The season-swept anchor worms (figure channel) + steepening par worm (above).
- **The conservation chart (2D, DOM/SVG):** a population-decline line — anchor share of all league balls by season, **14.8% → 8.5%** — with the "last surviving anchors" of the final seasons marked as fading dots (named from the pipeline's emitted `last_survivors`, never hardcoded here). **Drawn static and complete *before* the season scrub begins (progressive disclosure)**, so that when the reader scrubs, only the worms move — never two synchronized representations at once.

**Progressive disclosure (desktop density):** the standing field is busy (haze + par worm + K worms + conservation chart + tappable survivor dots + chips + season pointer). Per step, **aggressively dim every locus except the one changing** — one change per step is enforced by attenuation, not just by claim.

**Caption steps (one change each):**
1. *(season pointer early; the thicket is full)* > **Every team once carried two or three.** The anchor was doctrine — see off the new ball, bat till the end, let the others tee off.
2. *(scrub toward 2026; the anchor worms thin to a survivor or two — the one change)* > Watch them thin out. Slow innings ate **14.8% of every ball bowled** in the league's earliest seasons; in the last three, just **8.5%** — a whole way of batting hunted toward the margins. By the final seasons its survivors are few enough to name.
3. *(celebratory-thesis chip lands, nothing else moves — no number)* > A whole archetype, all but gone from the game — **and the game is quicker and braver for its passing.** ⓘ

*(Register: step 3 carries the mandated celebratory turn — the extinction (step 2) is stated and immediately affirmed, so C2-3 can never read as lament, and it lands on the thesis, not a number. Working memory: **the whole scene carries exactly ONE extinction number in the main flow — 14.8% → 8.5% of every ball bowled** (denominator spelled out in-caption). The older occupancy pair (38.7→2.4) and the derived "43% collapse" are gone from the flow — the pair is demoted to the ⓘ and honestly relabeled as a raw cut (see footnote); this resolves both the two-denominators risk and the one-point-per-beat cap.)*

**Interaction (+ skip path):** tap a marked "last surviving anchor" dot on the conservation chart → a mini card naming that innings (player · season · balls · SR · what par was doing), data from `ch2.json last_survivors`. The captions carry the entire point; the tap adds names, never thesis.

**Mobile:** conservation chart ~40vh below the field; season pointer is a scroll-scrubbed value, not a draggable control. **Reduced-motion:** the thinning renders as a static **two-panel small-multiple** — the 2008 worm thicket beside the 2026 survivor-or-two — with the conservation chart static-legible by construction; chips appear as instant states. **Footnote layer (ⓘ on step 3):** era-band definitions (2008-10 vs 2023-26); **the occupancy pair, demoted here and labeled honestly** — batter-seasons that kept a **whole-season raw strike rate under 120** fell **38.7% → 2.4%**, but this is a **fixed bar the league has simply outgrown**, *not* an era-relative measure: because league-wide scoring lifted everyone past a static 120, this raw cut **overstates** the decline (~94%) next to the honest era-relative anchor share (14.8→8.5, a ~43% fall). **The two numbers diverge precisely because one is era-adjusted and one isn't — they do not corroborate each other** (this is why the main flow carries only the era-relative number, and why C2-2's footnote is right to disavow raw-SR cutoffs). Sample sizes. The honest **multi-causality note** — how much of the decline is *intent* (batters choosing to attack), *fitness/selection* (teams no longer picking accumulators), **or rules** — is not cleanly separable, and the chapter does not claim it is; in particular the **Impact Player substitute (2023+)** makes losing a wicket cheaper and lands squarely on the 2023-26 endpoint of the curve, so a structural rule change is entangled with the batter/team-choice story at exactly the point the extinction completes.

---

### Scene C2-4 — The run-out cascade (hero #2; the subset-highlight)

**Purpose (one point):** the anchor took the risky single with him — the run-out, the most direct fossil of strike rotation, is draining out of the game.

**Particle field:** a **season-swept subset flash+fall** over the held worm-space haze (a subset-highlight — it composes with the base layout and does **not** spend a second controlling morph). As the reader scrubs 2008 → 2026, each season's **run-out-flagged balls** (identified from a spare `attrs.u8` bit — see §2) **flash red and fall** out of the field (eject downward + fade). Critically, each season's run-out cohort **flashes-and-falls as a single synchronized wave (Gestalt common fate)** — one discrete pulse per season, *not* asynchronous rain — so per-season magnitude reads as a **countable pulse**, not continuous drizzle (run-outs scatter across all of worm-space, so without common fate the reds would read as noise, not a shrinking flood). Early seasons dump a visible flood; late seasons a trickle — the shrinking flood **is** the extinction curve. The cascade **red is luminance-distinct from the dark low-alpha haze** (not just hue-distinct) and brighter/more saturated than any team red; the **team-identity glow mutes one stop through the cascade** so a red-team reader (RCB/PBKS/SRH) never confuses identity with a run-out — the fall disambiguates on motion (§0.1). (Red is the one gated hue exception; the primary channels are motion + luminance, red is the dramatic flash.)

**Annotation plane:**
- **The run-out extinction curve (2D, DOM/SVG):** run-outs as a share of all dismissals by season, **12.3% (2008) → 4.6% (2026)**, the falling red cascade cross-fading into this precise line (the catalog's exact viz handoff). Era ghost convention carried from Ch 1 (2008 line greyed as reference).

**Caption steps (one change each):**
1. *(the 2008 flood of red flashes and falls — the one change)* > When the anchor rotated strike, he took risks between the wickets. **In 2008, run-outs were one dismissal in eight** — the sharp single, the desperate second.
2. *(scrub forward; the red dwindles to a trickle by 2026 — the one change)* > Watch them drain away. **12.3% of all wickets then, 4.6% now.** Boundary-or-block replaced the scampered single — the sharpest, riskiest run in the game is quietly disappearing.
3. *(curve settles; thesis chip)* > It's the clearest fossil in the data: **the death of the risky single** — and the game is quicker and **no more reckless** for its passing. The anchor's whole game, and its whole way of getting out, went together.

*(Register: step 3 now pairs the loss ("the death of the risky single") with the gain ("no more reckless for its passing") **inside the beat** — the elegy rule holds here too, not deferred to C2-9 — so the one hero extinction beat with the red=loss cascade is no longer the unguarded nostalgia risk. The "risky two" claim is deleted: the emitted Break-Even data shows the twos rate held **flat** (7.8→7.6 / 100 non-boundary balls) — run-outs halved because running got safer, not because two-attempts stopped; only the "risky single" survives, and it is what the emitted linear-weight flip supports. Footnote carries the honest mechanism split — fewer *attempts* plus safer running, not one alone — so the main flow claims no more than the share-of-dismissals number supports.)*

**Interactions:** none required (subset scene lands by scroll). **Mobile:** the falling red reads at portrait width; the extinction curve labels 2008 / 2014 / 2026. **Reduced-motion:** renders the **final fallen layout** — run-out balls already ejected/faded to the 2026 end state — with the extinction curve static and complete; no sweep required.

**Wire cost:** zero new bytes — run-out identity packs into a spare **`attrs.u8` bit 6** (`0x40`), a pipeline re-encode exactly like Ch 1's top-10-six-hitter bit (ledger delta 0). The cascade capability (`cascade`, season-swept flash+fall) is a shell request (§6), mirroring the §9 resort. **Footnote layer (ⓘ):** run-out decomposition (striker vs non-striker out via `player_out`; failed-single vs turning-for-two via runs completed; phase; direct-hit proxy from `fielders` array length) — **the catalog's full recipe**; the **sparse/missing `fielders` caveat** (gaps cluster 2018-21, handled gracefully); **why this is fewer *attempts*, not just better running** — paired with singles-per-ball; **Break-Even Running** (the demoted mechanism note behind the curve): *running didn't atrophy, it got safer — run-outs per 1,000 balls halved 6.4 → 2.8 while the twos rate held flat, 7.8 → 7.6 per 100 non-boundary balls* (data from the catalog); and the **league-wide caveat behind step 3's poetic weld** — run-outs fell across *all* batters (fewer / less-valuable singles league-wide plus safer running), **not specifically because anchors left.** The "gone together" line is a real co-decline of two era trends, but the run-out's extinction is not the anchor's personal doing — the correlation should not be read as the anchor *causing* the run-out to die.

---

### Scene C2-5 — The deleted gearbox (supporting: Gear-Shift Detector)

**Purpose (one point):** the old innings had gears — see off, settle, launch; the modern one has one gear, flat out — and the patient middle went with the man who used to play it.

**Particle field:** worm-space holds, dimmed one stop. Loop stopped. This is an **annotation-plane** beat — no re-sort.

**Annotation plane:** two crisp exemplar worms drawn over the dimmed haze (SVG, from `ch2.json`) — **each in the figure channel (casing behind a brighter stroke, §0.1)** so both separate cleanly from the dimmed haze rather than reading grey-on-grey:
- **A 2008 two-act innings** — a worm that crawls, then visibly **kinks steeper** partway (the gear change), its two segments color-noted (build / launch).
- **A 2026 flat-max innings** — a single straight steep line, one gear from ball one.

**Caption steps:**
1. *(2008 worm draws with its kink)* > The classic T20 innings had **gears**: see off the bowling, consolidate, then launch. You can see the change of pace — the line bends upward.
2. *(2026 worm draws straight beside it — the one change)* > The modern innings has **one gear: flat out.** No see-off, no consolidation — just the launch.
3. *(number chip)* > Innings that shifted up a gear late were **a third** of the long ones once (**33.5%**). Now **a quarter** (**24.5%**). ⓘ The build-up went with the man who used to play it.

**Interactions:** none. **Mobile:** the two worms stack (2008 above, 2026 below) so the kink-vs-straight contrast survives portrait width; caption last. **Reduced-motion:** both worms render together immediately (static-legible); step 2's "draws beside it" is an instant state. **Footnote layer (ⓘ):** the technical name (innings-shape taxonomy via changepoint detection over the per-ball runs sequence, 25+ ball innings); the **verified non-issue** that 25+ ball innings share is era-stable (20.9% vs 20.3%), so the shape change isn't a sampling artifact; the archetype set (flat-max / ramp / two-act / stall); note that the exemplar worms are illustrative real innings, chosen from `ch2.json`, not the field's own points.

---

### Scene C2-6 — The one survivor (the sole coda: New-Batter Tax)

**Purpose (one point):** one honest counter-beat — the revolution killed the anchor but it never killed the *cost of losing a wicket*; that dip is structural, not behavioral.

**Particle field:** worm-space dims behind the strip; loop provably stopped for the whole scene.

**Annotation plane:** **the aftershock strip (2D, DOM/SVG)** — per-ball team run rate in the 10 balls after a wicket, one line per era, each drawn as a **dip below the day's going rate that recovers but never fills in.** The 2008 dip and the 2026 dip sit close together — the later one, if anything, a touch **deeper** (the point: it never healed) — with the incoming batter's opening pace annotated separately.

**Caption steps:**
1. > Everything in this chapter is something the revolution **killed.** Here's the one thing it couldn't. When a wicket falls, **the scoring stalls** — the next ten balls dip below the day's rate.
2. *(both era lines drawn together — the dips overlap)* > And the dip **didn't shrink — if anything it deepened:** **−1.22** runs an over below the day's going rate in the early seasons, **−1.40** now. Even though the new man walks in swinging harder than ever, the scoring still stalls the moment he arrives. ⓘ
3. *(thesis chip)* > The batter changed; the cost didn't budge. **Some costs are built into the game, not the player** — a new man at the crease, a field reset. Structural, not a failure of nerve.

*(Working memory: step 2 now carries only the two-era tax pair (−1.22 → −1.40) in the main flow — **the incoming-batter SR pair (101 → 127) is demoted to the ⓘ by default**, resolving the >3-number load structurally rather than conditionally. The "even though" pivot survives as one **number-free** clause ("the new man walks in swinging harder than ever"); the SR figures back it up one click deep. Note the honest reframe: −1.22 → −1.40 is a ~15% *deepening* of the absolute tax (stable only as a share of par), so "deepened" — not "barely moved" — is the accurate word, and it *strengthens* the thesis that the revolution couldn't kill this cost. Era labels track the artifact's bands ("early seasons" / "now"), not single years.)*

**Interactions (+ skip):** tap the strip → a mini "drop a wicket anywhere" read (which over, which era, the modeled dip) — depth only; the caption carries the point. **Mobile:** strip ~40vh, full-width; caption below. **Reduced-motion:** both era lines render together immediately (static by construction). **Footnote layer (ⓘ):** the **incoming batter's first-five-ball strike rate, up 101 → 127** across the eras (the "walks in swinging harder than ever" figure, demoted from step 2 so the main flow holds one number pair); the technical construction (10-ball post-wicket team run rate vs season × phase par with wickets-in-hand conditioning; trim wickets near innings end); the corrected finding (the probe *contradicted* the original "tax halved" hypothesis — the tax is ~15% of par in both eras, a slight absolute deepening −1.22 → −1.40); the honest note that the **WPL comparison is still open** (not enough post-wicket WPL cricket to state a clean number); and **Milestone Braking Index** (the second demoted nerd-nugget, deliberately *not* a rival coda): *nerves survive too — batters ease off more approaching a fifty now than in 2008, the "brake at fifty" strengthening 0.989 → 0.930, with the 45-49 dismissal rate (4.81%) sitting below the 38-44 rate (5.76%).*

---

### Scene C2-7 — The WPL beat (two clocks, one beat — house rule)

**Purpose (one point):** the WPL never had an anchor era to lose — its batting is already modern — **and** its running risk is mid-revolution. One league, two clocks at once. (This is the chapter that teaches the reader the WPL can't be placed at a single point on the IPL timeline — pre-work for Ch 6.)

**Particle field:** in worm-space, **WPL points brighten to full** and IPL points dim one stop (the mirror of Ch 1's C1-6 treatment — a color-state change, not a re-sort; the brighten IS the beat). Loop renders once per state. Reduced motion: instant states.

**Annotation plane:** a compact 2D panel — **two clock dials side by side**, both zero-based, each a small gauge with the IPL era-scale printed beneath so the reader reads *where on the IPL's own history* each WPL number sits:
- **Batting clock — "already modern":** WPL slow-innings share **~9-10%**, needle landing at **modern IPL** (2023-26 levels).
- **Running clock — "mid-revolution":** WPL run-out share **7.0%**, needle landing at **IPL circa 2014-17.**

**Caption (single card — the two clocks must share one beat; ≤45 words):**
> **The WPL never had an anchor era to lose.** Four seasons in, its slow-innings share already sits at the modern IPL's — it was **born past the anchor.** Yet its run-outs run at **7.0%** — right where the IPL stood a decade ago. **Two clocks: batting modern, running mid-revolution.**

*(~44 words. WPL numbers render in the WPL hue, color-linked to their dials — hue stays identity. "Already modern" and "born past the anchor" are the grammatical subject; no deficit language. The two clocks are the whole point: the single-clock framing is banned by the §2 corollary.)*

**Interactions:** none. **Mobile:** the two dials stack (batting above, running below), caption last. **Reduced-motion:** brighten/dim are instant states; the panel is static SVG. **Footnote layer (ⓘ):** WPL sample honesty (88 matches / 20,642 deliveries, four seasons young — early numbers will move); the anchor-share source (born post-anchor undercuts the lazy "women's cricket still rewards anchors" narrative — the catalog's verified kicker); why "behind" is the wrong word (a league can be modern in one dimension and developing in another at the same time — full treatment named by title, *Two Dialects*, Chapter 6); the WPL run-out mechanism note (its four-led scoring engine means fewer sharp singles by geometry, teased for Ch 6).

---

### Scene C2-8 — Team payoff card ("Your last anchor")

**Purpose:** the chapter's finding, re-told in the reader's colors — the last time your franchise fielded the archetype that just went extinct. Strictly template + `payoff/ch2.json` (16 variants, snapshot-tested; never hand-authored).

**Particle field:** reader's team balls at full brightness in worm-space; everything else dims. One render.

**Card template — IPL picker (with a qualifying anchor):**
- Header: crest + **"{Team}'s last anchor"**
- **The replayable worm:** the final qualifying anchor innings in the franchise's history, drawn as a **slow worm in the anchor figure channel (§0.1) against that day's going-rate line** (coordinates from `ch2.json`/`payoff/ch2.json` — a real innings, replayable as the worm animating ball by ball).
- Body (from JSON verbatim): *"{player} · {venue}, {date}. {balls} balls, {runs} runs, strike rate {sr}. Boundaries: {boundary_pct}% of what he faced. The day's going rate: {par_sr}. The last of his kind at {Team}."*
- Elegy line (template): *"No {Team} batter has played an innings like it since."*

**Card template — designed empty state (WPL sides + any attack-era IPL side with no qualifying anchor — GT / LSG and the WPL five, per the pipeline's emitted flag):**
- Header: crest + **"{Team} never had one"**
- Body (verbatim, from JSON `empty_state`): *"**Born post-anchor — your franchise never had one.** {Team} came into the game after the careful accumulator was already gone. Its slowest qualifying innings still ran at a strike rate of {x} — an attacker's floor."*
- *(This is the chapter's WPL point made personal, and it is authored copy, not a blank card — the §2 payoff-QA rule. The empty state is itself the finding.)*

**Card template — Neutral:** league-wide card, rendered from JSON verbatim: *"The league's last anchors: slow innings fell from **14.8%** of every ball to **8.5%**, and the risky single — the run-out — from **12.3%** of wickets to **4.6%**. A whole way of batting, gone in a generation."* + the most recent qualifying anchor innings in IPL history (from JSON).

**Interactions (+ skip):** **[ Not your team? Change it ]** → picker (state preserved, returns here); the worm replay is a tap-to-replay, static otherwise. **Mobile:** full-width sheet over the dimmed field; worm replay sized to portrait. **Reduced-motion:** static card, the worm drawn in its end state (no ball-by-ball animation), instant ignite. **Footnote layer (ⓘ):** the anchor-qualification rule (same as C2-2's), min-sample note, and which franchises get the designed empty state and why (born after the archetype).

---

### Scene C2-9 — Chapter close (the elegy lands; hand off to Ch 3)

**Purpose:** compress the chapter to one sentence — mourned but celebratory — and aim it at the resistance.

**Particle field:** worm-space exhales back into the free field (reverse of the controlling morph, fast, ~40vh — the same morph's return leg, not a second morph). Reader's team stays lit.

**Annotation plane (single caption):**
> The anchor is gone — and the game is **faster and braver** for losing him. But he was the **first** casualty, not the last: when batting changes this much, the men with the ball have to answer. That's next.

*(The close carries both halves of the elegy — the farewell and the affirmed gain ("faster and braver") — then the Ch 3 handoff, and stops there. "No more reckless" now lands earlier, inside the C2-4 run-out beat (and still quietly reconnects to Ch 1's flat-out-rate thesis there), so the close stays two clean halves plus the aim rather than three adjectives competing for the quotable line. The handoff names the shape of Ch 3 — The Counterrevolution — without a number, per the nav rule that titles are commitments and numbers aren't. Gain-clause wording is varied across beats — "the game he built is faster now" (C2-1), "quicker and braver for its passing" (C2-3), "no more reckless for its passing" (C2-4), "faster and braver" (here) — so the affirmation stays felt, never boilerplate a reader tunes out.)*

**Interactions:** none. **Mobile:** caption bottom. **Reduced-motion:** jump-cut back to free field; static caption. **Footnote:** none.

---

## 2. R2a (Chapter 2) payload inventory (ledger deltas)

| Artifact | New in R2a | Est. size (gz) | Budget bucket |
|---|---|---|---|
| `cumruns.u8` (per-point cumulative innings runs, cap 255) | **yes** | ~40–70KB (blocky, monotone within innings) | Ch 2 (≤2MB) ✓ — lazy-loaded at Ch 2 entry, not before assembly |
| `attrs.u8` bit 6 (`0x40`) re-encoded as the run-out flag (C2-4 cascade) | re-encode, **0 new bytes** | 0 | Ch 2 ✓ |
| `scenes/ch2.json` (anchor/occupancy curves + par-worm + K exemplar-worm coords per season + run-out extinction curve + gearbox exemplar worms + aftershock strip + WPL two-clock + `last_survivors`) | **yes** | ~8–14KB | Ch 2 ✓ |
| `payoff/ch2.json` (16 "your last anchor" variants incl. designed empty states + replayable last-anchor worm coords) | **yes** | ~4–8KB | Ch 2 ✓ |
| Worm-space / cascade layouts | no new position buffers — in-shader from `ballsfaced` + `cumruns` + group ids + `attrs` bit 6 | 0 | — |
| `meta.json` (add Ch 2 files to the ledger block) | field add | ~0 | pre-assembly ✓ |

**Ch 2 total delta: ≲ 90KB gz ≪ 2MB.** R1 assembly artifacts unchanged (R1 scenes render byte-identically). `pipeline/ledger.py` gains rows for each new artifact; "chapter payload within budget" stays a release pass criterion.

---

## 3. Verified-number index (single source for QA)

| On-screen claim | Value | Source |
|---|---|---|
| Anchor share of all league balls | 14.8% (2008-10) → 8.5% (2023-26) | catalog (Anchor Extinction Index ★) — **the single main-flow extinction number; "43% collapse" is a de-emphasized restatement (off-screen), not a third figure** |
| Occupancy — raw whole-season SR < 120 (**footnote only**) | 38.7% (2008-10) → 2.4% (2023-26) | catalog (Ball-by-Ball DNA) — **a FIXED bar the league outgrew, NOT era-relative; demoted to C2-3 ⓘ and labeled a raw cut that OVERSTATES (~94%) vs the era-relative 14.8→8.5 (~43%); the two diverge, they do not agree; never in main flow** |
| Run-outs, share of all dismissals | 12.3% (2008) → **4.6%** (2026) | catalog (Run-Out Extinction Curve ★) teaser · **reconcile:** data-profile 2026 table reads 4.7% — the emitted `ch2.json` is the source of truth; QA asserts card == artifact (r1a's 316,199 / 938-players discipline); if the final filter computes 4.7, the copy updates to match the artifact |
| Total IPL run-outs (footnote/scale) | 1,194 | catalog |
| Gear-shift: two-act long innings | 33.5% (2008-10) → 24.5% (2023-26) | catalog (Gear-Shift Detector) |
| New-Batter Tax: post-wicket 10-ball dip vs par | −1.22 (2008-10) → −1.40 RPO (2023-26) | catalog (New-Batter Tax, corrected) |
| Incoming batter first-5-ball SR | 101 → 127 | catalog (New-Batter Tax) — **demoted to C2-6 ⓘ by default; not in main flow** |
| Break-Even Running (footnote) | run-outs per 1,000 balls 6.4 → 2.8; twos rate 7.8 → 7.6 / 100 non-boundary | catalog (Break-Even Running) |
| Milestone Braking (footnote) | Braking Index 0.989 → 0.930; 45-49 dismissal 4.81% vs 38-44 5.76% | catalog (Milestone Braking Index) |
| WPL anchor-ball share (batting clock) | ~9-10% (at modern-IPL levels) | catalog (Anchor Extinction Index — WPL kicker) |
| WPL run-out share (running clock) | 7.0% (≈ IPL circa 2014-17) | catalog (Run-Out Extinction Curve — WPL) |
| WPL sub-120-SR occupancy (footnote) | 19.8% (≈ IPL 2012) | catalog (Ball-by-Ball DNA — WPL) |
| Anchor definition (footnote) | 15+ balls; SR < 0.85× season×phase par; boundary balls < 12% of balls faced | catalog (Anchor Extinction Index recipe) + engine #1 |
| Axis constants (honesty-locked) | worm x capped at `60+` (labeled) · **worm-space data aspect ratio fixed / banked ~45° independent of viewport (letterbox, never stretch)** · aftershock strip & extinction curve zero-referenced to par/0 · WPL clock dials zero-based with IPL era-scale printed · conservation chart y zero-based | this storyboard (C2-2/4/6/7) |
| Per-team "last anchor" figures | per-variant, from `payoff/ch2.json` verbatim | pipeline JSON |

---

## 4. R2a QA checklist (storyboard-level)

- [ ] Glossary scan: no banned term (§0.2) in any main-flow or teaser string; the stage-name table's fan phrasings used wherever a term of art is meant; **bare "par" appears in NO reader-facing caption or payoff card — reader-facing copy says "the day's going rate" / "the day's rate" everywhere (C2-6 step 2, C2-8 body audited); "par" is confined to the footnote/QA layer.**
- [ ] **Register (elegy) audit:** every extinction beat (C2-3, C2-4) pairs a loss clause with a celebratory clause **inside the beat** (C2-4 step 3 now carries "no more reckless for its passing" — not deferred to C2-9); **C2-1 plants a celebratory seed ("to the man, not the runs — the game he built is faster now")** so both halves are present even on a deep-entry bounce; the gain clause is **varied per beat** (no verbatim repeat); C2-9's close carries both halves; no beat reads as nostalgia-for-anchors (the §7 RESOLVED #3 risk).
- [ ] Pixel-number audit: every visible ball count says 316,199; run-out headline reads whatever `ch2.json` emits (4.6% vs 4.7% reconciled to the artifact, not to blueprint copy).
- [ ] Morph budget: exactly one controlling field morph (free→worms) + its free reverse; the run-out cascade, the thinning, the gearbox contrast, and the WPL brighten are subset/2D/color-state only (no second layout re-sort).
- [ ] 16/16 payoff variants non-degenerate; designed empty states authored for WPL sides **and** attack-era IPL sides (GT/LSG) with no qualifying anchor; at least one bespoke WPL-picker card ships (the empty-state card qualifies).
- [ ] WPL beat reads two clocks in one caption card; no sentence with WPL as object of "behind/lags/still/only"; "already modern"/"born past the anchor" is the grammatical subject.
- [ ] Reduced-motion pass: every scene has its jump-cut exercised — worm-space haze end state (C2-2), 2008-vs-2026 small-multiple (C2-3), final fallen run-out layout (C2-4), both-worms/both-lines static (C2-5/C2-6), instant WPL states (C2-7), static card + end-state worm (C2-8). No beat requires motion or a tap to land.
- [ ] No hover-only content; all ⓘ, defier/last-survivor cards, and the worm replay are tap/keyboard; targets ≥44px.
- [ ] Hue-exception audit: red appears ONLY during the C2-4 cascade flash (dev assertion warns if any run-out tint is non-zero outside C2-4); hue is identity everywhere else; **the cascade red is luminance-distinct from the haze and brighter/more saturated than any team red, and the team-identity glow mutes one stop through the cascade — the red-team collision case (RCB/PBKS/SRH: "my team" vs "a run-out") is explicitly exercised.**
- [ ] **Figure-channel / preattentive audit:** the anchor worm is the **highest-contrast mark in the frame** (dark casing/halo + brighter stroke, corridor haze-attenuation beneath it) — higher-contrast than the par worm, which is subordinate; the "an anchor" direct label is high-contrast even though the line is subtle (C2-2, C2-3, C2-5). Grey-on-grey-haze on the protagonist line is a fail.
- [ ] **Cascade common-fate:** each season's run-out cohort flashes-and-falls as ONE synchronized wave (a discrete per-season pulse), never asynchronous rain that reads as drizzle/noise.
- [ ] **Exemplar-worm honesty:** the K anchor-worm thicket is labeled illustrative ("a sample of that season's anchors," not a count); K scaling is pinned to the emitted per-season anchor ball-share; the "few enough to name" magnitude claim is sourced from emitted `last_survivors` / the conservation chart, never from the drawn thicket.
- [ ] **Occupancy honesty:** the 38.7 → 2.4 raw-SR-<120 figure appears ONLY in C2-3's ⓘ, labeled a fixed bar the league outgrew (overstates ~94% vs the era-relative 14.8→8.5 ~43%); the footnote says the two *diverge* (era-adjusted vs not), never "agree"; C2-3 main flow carries exactly one extinction number.
- [ ] Caption grammar lint: ≤45 words/step, ≤3 numbers/step, one on-screen change/step — **C2-6 step 2 carries only −1.22 → −1.40 (SR pair 101→127 demoted to ⓘ by default); C2-3 main flow carries exactly one extinction number (14.8→8.5), occupancy pair footnote-only.**
- [ ] Axis honesty: worm x capped bucket labeled `60+`; **worm-space keeps a fixed ~45° data aspect ratio independent of viewport — letterboxes on portrait, never stretches x or banks worms toward vertical (steep-vs-shallow contrast survives mobile, the primary target);** aftershock strip and extinction curve zero-referenced; WPL clock dials zero-based with the IPL era-scale printed; conservation chart zero-based.
- [ ] Payload ledger re-run passes with `cumruns.u8` + `scenes/ch2.json` + `payoff/ch2.json`; Ch 2 delta ≪ 2MB; R1 artifacts byte-identical.
- [ ] Nav: Ch 2 flipped from `soon` to live (declares `navLabel`); removed from `FUTURE_CHAPTERS`; deep entry into `#ch2` works with no sketch/team state (neutral field + neutral payoff variant).
- [ ] Multi-causality honesty: C2-3's ⓘ states intent-vs-fitness-**vs-rules (Impact Player 2023+, entangled with the 2023-26 endpoint)** is not cleanly separable; C2-4's ⓘ states the run-out decline is fewer *attempts* paired with safer running (and is **league-wide, not anchor-specific** — the "gone together" weld is co-decline, not the anchor causing the run-out's death), not one alone; **the "risky two" claim is deleted (twos rate held flat) — only "risky single" survives.**
- [ ] Demand-mode: idle GPU ~0 in C2-1, C2-3 holds, C2-5, C2-6, C2-7, C2-8, C2-9 hold.
- [ ] `?hud=1` stays dev-only; zero HUD DOM on default load.

---

## 5. Copy / design decisions made here (blueprint didn't fully determine) — for owner sign-off at the R2 milestone review

1. **The eulogy voice (C2-1).** The blueprint locked the *register* (elegy) but not the words; authored here: "held the innings together… the game had a name for him: the anchor… we came to say goodbye." Praise-then-farewell structure, with the celebratory turn deferred to C2-3/C2-9 so affection lands but nostalgia never does.
2. **Worm-space encoding (C2-2).** x = balls faced (reusing `ballsfaced.u8`, display extent to `60+`), y = cumulative innings runs (new `cumruns.u8`); slope = strike rate. Proposed because it makes "slow" *literally* a shallow line and honors "every ball on screen" as the haze. Alternative considered and rejected: y = strike-rate (bounded but less evocative than a rising worm; SR-vs-par stays the anchor *definition*, not the axis).
3. **Exemplar-worm cardinality + figure channel (C2-2/C2-3).** The par worm + K exemplar worms are **SVG on the annotation plane** (crisp, labeled, a few KB from `ch2.json`), NOT thousands of GL polylines; the 316k field is the haze. **The anchor worm now carries the dedicated figure channel** (dark casing/halo + brighter stroke + local haze-corridor attenuation) and is the highest-contrast mark — higher than par (see §0.1; this fixes the inverted-legibility audit finding). Proposed K rule: draw a small thicket per season, **K pinned to the emitted anchor ball-share** (so the drawn worm-count ratio ≈ the 14.8→8.5 ratio the caption cites — not the 6× a naive cap-6→floor-1 would imply), floored at 1 until true extinction, capped for legibility, and **labeled illustrative** ("a sample of that season's anchors," not a count) so a capped/floored draw can never over/under-state the true decline (the real magnitude rides the conservation chart + `last_survivors`). **Exact K cap + scaling curve needs owner/pipeline sign-off** (starting proposal: cap ~6, floor 1, curve pinned to ball-share).
4. **Run-out cascade encodes SHARE, cross-fading to the curve.** The falling red is season-swept; the 2D companion is run-out **share of dismissals** (not raw count — counts confound with more matches/wickets per season). The "flash red" is honored as a documented, beat-gated hue exception (§0.1). **Decision to confirm:** red flash vs a white-hot flash (blueprint says red; recommended to keep red for the danger/loss semantics).
5. **Stage names (C2 roster).** Authored per the glossary rule: "the day's going rate" (phase-par SR), "an innings drawn as a rising line / the worm," "the risky single" (run-out), "the innings had gears / one gear: flat out" (Gear-Shift), "what a wicket still costs" (New-Batter Tax), "the brake at fifty" (Milestone Braking), "running got safer" (Break-Even). Sign off before R2 copy freeze (§7 open-question #5 process).
6. **New-Batter Tax as the *sole* coda (C2-6), framed as "the one survivor."** One honest counter-beat, not two — Milestone Braking is deliberately demoted to the C2-6 footnote so the chapter has one coda, not a rival.
7. **"Your last anchor" empty state extends to attack-era IPL sides.** GT and LSG (born 2022/2023) likely have no qualifying anchor and get the same designed empty state as the WPL five — the pipeline emits the `empty_state` flag per variant; the storyboard does not hardcode which. **Confirm** the exact franchise list against the emitted `payoff/ch2.json`.
8. **Named "last surviving anchors" and per-team last anchors come only from the pipeline** (`ch2.json last_survivors`, `payoff/ch2.json`), never authored here — no player name is invented in this storyboard (the every-number-from-an-artifact rule applies to names too).
9. **Run-out headline number reconciliation.** The blueprint teaser is 12.3% → 4.6%; the data-profile 2026 table reads 4.7%. Decision: the emitted `ch2.json` wins and the copy renders the artifact value; QA asserts card == artifact (identical discipline to r1a's 316,199 / 938 handling).
10. **Occupancy pair demoted to a footnote raw-cut (C2-3).** The 38.7% → 2.4% figure is batter-seasons with *raw* SR < 120 — a fixed bar, not the era-relative "day's going rate" the anchor definition and C2-2's footnote are built on. Decision: it is **removed from main flow** and lives only in C2-3's ⓘ, relabeled honestly as a bar the league outgrew (it overstates the decline vs the era-relative 14.8→8.5), with the footnote stating the two *diverge* rather than "agree." Main flow now carries one era-relative extinction number. (Fixes the methodology contradiction where the chapter headlined the exact raw cutoff its own footnote disavows.)
11. **Worm-space fixed data aspect ratio (C2-2).** The plot banks toward ~45° independent of viewport and letterboxes on portrait rather than stretching, so the slope encoding (steep par vs shallow anchor) survives mobile, the primary target. Confirm the exact banking target at build.
12. **"The day's going rate" is the single reader-facing label; "par" is footnote/QA-only** (C2-6, C2-8 corrected). One label for one concept per the scene's glossary discipline.

---

## 6. Integration notes (shell + pipeline + composition)

**Shell requests (new field capabilities — owned by the story-shell architect, requested here, not forked):**
- **New layout id `worms`** (`SceneFieldState.layout`): x = `ballsfaced.u8` (display extent ~60+), y = `cumruns.u8`, rendered as a uniform low-alpha haze; in-shader, no positions on the wire. **The worm-space uses a fixed data aspect ratio (banked ~45°) independent of viewport — the frame letterboxes on portrait rather than stretching x** (so the slope encoding survives mobile). This is Ch 2's single controlling morph (free→worms), analogous to how Ch 1 added `wall`. Add `worms` to `LayoutId` + `LAYOUT_CODE`. *(The anchor-worm figure channel — casing/halo + brighter stroke + a locally attenuated haze corridor beneath the drawn anchor line — is an annotation-plane / compositing concern registered to field coordinates, not a per-point GL attribute; the shell exposes the corridor-attenuation hook so the SVG worm and the GL haze compose.)*
- **New subset capability `cascade`** (a cross-cutting modifier like `highlight`/`resort`, does NOT spend a second controlling morph): season-swept flash+eject of a flagged class. Proposed shape mirroring §9's `resort`: `cascade?: { class: 'runOut'; sweep: number /* 0→1 season pointer */; tint: number /* red flash strength, beat-gated */; fall: number /* eject depth */; fade: number; muteIdentity: number /* desat team glow during cascade */ } | null`. The active season's matched points flash → fall → fade **as one synchronized cohort (Gestalt common fate — a discrete pulse per season, not per-point asynchronous rain)** as `sweep` advances; the flash `tint` red must be **luminance-distinct from the haze and brighter/more saturated than any team red**, and `muteIdentity` desaturates the team glow one stop for the beat (red-team collision guard, §0.1). Reduced motion jump-cuts to `sweep:1` (final fallen layout). Needs a new `HighlightClass`-adjacent flag `runOut` sourced from `attrs.u8` bit 6.
- **`cumruns.u8` loader** (parallel to `ballsfaced.u8`, normalized 0..1 GPU-side) and **`attrs.u8` bit 6** decode for the run-out flag. Both are no-ops for R1 scenes (byte-identical rendering preserved).

**Pipeline requests (owned by the pipeline; `static/data/**` is never hand-edited):**
- Emit `cumruns.u8` (per-point batter cumulative innings runs, cap 255, same point order as `ballsfaced.u8`).
- Re-encode `attrs.u8` bit 6 = run-out dismissal flag.
- Emit `scenes/ch2.json` and `payoff/ch2.json` (schemas implied by §1/§2/§3; snapshot harness asserts 16/16 non-degenerate payoff variants incl. designed empty states, and card==artifact for every on-screen number).
- **Engine dependencies (both built in R2, per blueprint §5):** engine #1 (season × phase × venue par / SR+) powers the anchor definition and "the day's going rate"; engine #5-full (entry states / derived batting positions) powers the New-Batter Tax incoming-batter series and the gear-shift innings framing. Ch 2 copy cannot be frozen until engine #1's par table is emitted (the anchor curve and the threshold sweeps depend on it).

**Composition / nav:**
- `+page.svelte` composition order becomes coldopen → picker → ch1 → **ch2** → endcard (→ sandbox as its live navLabel). Ch 2 opens from Ch 1's exhaled free field.
- `navplan.ts`: remove `'Chapter 2 — The Last of the Anchors'` from `FUTURE_CHAPTERS`; the Ch 2 scenes declare `navLabel: 'Chapter 2 — The Last of the Anchors'` (anchor `#ch2`) so it becomes a live nav item.
- **End-card update (owned by the endcard builder):** flip the R1 "Chapter 2… in build" tease to "Chapter 2 — The Last of the Anchors · done" and tease Chapter 3 ("The Counterrevolution — the men with the ball answer") with an `in build` tag. Ch 3 ships in the same R2 release but is a separate storyboard.
- New scene directory `src/lib/scenes/ch2/` (exports `scenes: SceneDef[]` in reading order); footnote registry entries for the anchor definition, run-out decomposition + Break-Even, gear-shift, New-Batter Tax + Milestone Braking, and the WPL sample honesty.

---

## 7. Revision notes — design/honesty audit fixes applied (2026-07-04)

Applied in place; elegy register preserved. Where a fix touched a foundational rule (figure channel, hue exception, one label per concept), §0 was amended so every downstream scene inherits it rather than re-stating it.

**Must-fix (all applied):**
1. **Inverted protagonist legibility (C2-2/C2-3/C2-5).** The anchor worm — the chapter's protagonist, previously drawn grey-on-grey in the densest haze while par popped — now owns a **dedicated figure channel** (dark casing/halo + brighter stroke, a locally attenuated haze corridor beneath it) and is the **highest-contrast mark in the frame, higher than par**; par is demoted to subordinate (it already pops into the sparse zone). Rewrote §0.1, C2-2 overlays + caption step 3 stage direction, C2-3 particle field, C2-5 annotation plane; added a preattentive/figure-channel QA line. The "an anchor" label is specified high-contrast even though the line is subtle.
2. **Raw-SR-<120 cutoff contradicted the era-relative methodology (C2-3 step 3).** The 38.7% → 2.4% occupancy pair is a *fixed* bar the league outgrew — the exact raw cutoff C2-2's footnote disavows — so it is **removed from main flow**, demoted to C2-3's ⓘ, and relabeled honestly (a bar the league outgrew; it *overstates* ~94% vs the era-relative 14.8→8.5 ~43%). Footnote corrected: dropped "why the two agree," now states they **diverge** because one is era-adjusted and one isn't. Main flow now carries **one** extinction number. §3 index row and a new occupancy-honesty QA line added.
3. **C2-4 was pure loss-framing (violated the elegy rule).** Added the affirmative clause **inside the beat** — step 3 now reads "the death of the risky single — and the game is quicker and no more reckless for its passing." The run-out's death is mourned and its safety gain affirmed in the same beat, matching the §4 checklist guarantee; no longer dependent on C2-9.

**Should-fix (all applied):**
- **Two denominators in adjacent C2-3 steps** → resolved by the must-fix #2 demotion: one main-flow extinction number, denominator spelled out ("of every ball bowled"); "43% collapse" dropped from flow.
- **Untethered drawn thinning magnitude (C2-3)** → K pinned to the emitted anchor ball-share (drawn ratio ≈ the cited 14.8→8.5), thicket labeled illustrative ("a sample of that season's anchors, not a count"); the "few enough to name" magnitude sourced from `last_survivors`/the chart, not the thicket. §5.3 + exemplar-honesty QA updated.
- **C2-6 step 2 four-number overload** → SR pair (101→127) demoted to ⓘ **by default** (structural, not conditional); main flow keeps only −1.22 → −1.40; the "even though" pivot survives as a number-free clause.
- **"par" vs "the day's going rate" inconsistency** → "the day's going rate" used in all reader-facing copy (C2-6 step 2, C2-8 body/worm label); bare "par" reserved to footnote/QA. New §0.2 rule + glossary-scan QA line.
- **C2-1 had no celebratory seed** → step 3 now seeds it ("to the man, not the runs — the game he built is faster now") so both elegy halves survive a deep-entry bounce.
- **Run-out cascade read as drizzle** → each season's cohort flashes-and-falls as **one synchronized wave (common fate)** — a discrete per-season pulse; encoded in the §6 `cascade` shape + a QA line; red specified luminance-distinct from the haze.
- **Red cascade / red-team collision (RCB/PBKS/SRH)** → team-identity glow mutes one stop through the cascade; cascade red specified brighter/more saturated than any team red; `muteIdentity` added to `cascade`; red-team case added to the hue-exception QA.
- **Slope encoding lost on portrait** → worm-space uses a **fixed ~45° data aspect ratio independent of viewport** (letterbox, never stretch); §0.1, C2-2, §6 `worms`, axis-honesty QA, §3 index all updated.
- **"Risky two" contradicted Break-Even (twos rate flat)** → clause deleted; only "the risky single" survives (the emitted linear-weight flip supports it).
- **C2-3 multi-causality omitted rules** → Impact Player (2023+) added as a third, entangled channel on the 2023-26 endpoint.

**Consider — dispositions:**
- *Applied:* C2-3 progressive disclosure (conservation chart drawn static before the scrub; non-active loci dimmed per step); gain-clause wording **varied per beat** (C2-1/C2-3/C2-4/C2-9 no longer verbatim) with C2-1 and C2-3-step-3 landing on image/thesis without a number chip; C2-2 destination-first guide made **coincident with where par lands** (a pre-echo par overwrites — no duplicate diagonals); C2-9 close **trimmed** to two elegy halves + handoff ("no more reckless" moved earlier to C2-4); Ch1→Ch2 **bridge line** added at C2-1 step 2 (names the revolution as the hunter); C2-4 ⓘ **league-wide caveat** (run-out decline is not the anchor's personal doing); C2-6 "barely moved" → "didn't shrink — if anything it deepened" (honest ~15% absolute rise, strengthens the thesis); band-figure/single-year **label consistency** (−1.22/−1.40 and 14.8/8.5 carry band framing, not single years; run-out 12.3% stays a genuine 2008 value).
- *Note:* the exact K cap + scaling curve and the ~45° banking target remain flagged for owner/build sign-off (§5.3, §5.11) — the honesty rule (pinned + illustrative-labeled) holds regardless of the final constant.

*End of revision notes.*
