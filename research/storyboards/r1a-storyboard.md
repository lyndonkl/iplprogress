# R1a Storyboard — Cold Open · Team Picker · Chapter 1 · End Card · Nav

**Status:** implementation truth for R1a. Where this document and older blueprint copy disagree, this document wins (it encodes the §7 RESOLVED owner decisions). Where this document and the blueprint's *standing rules* (§2) disagree, the standing rules win — no scene below is allowed to violate them.

**Sources of record:** `research/experience-blueprint.md` (§2 standing rules, §3 Cold Open + Ch 1, §7 RESOLVED), `research/metrics-catalog.md` (verified recipes + teasers), `research/data-profile.md` (ground-truth tables), `web/static/data/*` (R0 artifacts: 316,199 points, group table, ledger, `payoff/ch1.json` 16 variants).

**Hard invariants carried by every scene (do not re-litigate per scene):**
demand-mode rendering (loop stops whenever no morph/scrub/interaction is active) · payload ledger budgets (≤3MB gz before assembly, ≤2MB gz/chapter) · reduced-motion = live-rendered end-state jump-cuts, never baked frames · no hover-only content · mobile-first · exactly one controlling morph in Ch 1 (free field → ignition wall) · GitHub Pages base path via `$app/paths` for every asset/fetch · byte-deterministic pipeline · no WASM · glossary rule (no statistical term of art in main flow; technical names live in the footnote layer) · WPL never "behind"; every WPL beat is two clocks in one beat · on-screen ball count is **316,199** everywhere pixels are visible (316,388 and the 189 super-over balls live in the footnote layer only).

---

## 0. Global grammar (applies to every scene)

### 0.1 Encoding grammar (cognitive-design commitments)

- **Position** carries the scene's semantics (the layout IS the argument). **Luminance/brightness** = runs per ball (dot ≈ dimmest, 4 bright, 6 brightest) — luminance is the preattentive channel that makes "the dark corner catches fire" legible at a glance. **Hue** is reserved for *identity only*: the reader's franchise color, and the WPL constellation's distinct hue family. Never encode a quantity in hue.
- **One message per scene; one change per caption step.** Each caption step changes exactly one thing on screen (a highlight OR an annotation OR a layout move — never two at once). Working-memory cap: no scene asks the reader to hold more than 3 numbers at a time.
- **Annotation-guided reading order:** every scene reads (1) caption card → (2) the one highlighted region the caption names → (3) number chip → (4) optional interaction affordance → (5) footnote dagger (ⓘ). Captions are DOM, bottom-anchored on mobile, left-column on desktop. Max ~45 words per caption step.
- **Numbers style:** tabular figures, thousands separators (`316,199`). Decimals only when the decimal *is* the point (`5.04% vs 4.93%`); otherwise round (`108 → 135`). Era-band *definitions* (which seasons, and why) live in the footnote dagger; the band labels themselves (`2008-10`, `2023-26`) may appear as chart labels and in captions that reference a labeled line — a curve on screen needs a name.
- **Footnote layer = progressive disclosure.** Every ⓘ opens a bottom sheet (mobile) / side panel (desktop), tap- and keyboard-operable, containing the technical names, era-band definitions, caveats, and demoted exhibits. Nothing in a footnote is required to understand the main flow.

### 0.2 Timing & scroll notation

- Scroll budgets in `vh` (1vh = 1% viewport height of sticky-scene scroll length). GSAP scrub set piece #1 (field assembly) is scroll-scrubbed; everything else in R1a is stepper-driven captions over a sticky canvas. The one autonomous animation is the You-Draw-It truth reveal (triggered by a tap, ~6s, skippable by tap or scroll; reduced-motion jump-cuts it).
- Demand-mode: the frameloop is `invalidate`-driven. It runs during: assembly scrub, ignition-wall morph, firework lift/settle, team-ignite color swap, WPL-glow swap. It is provably stopped during: prose captions, the 2D out-rate strip, cards, picker idle, end card, methods page.

### 0.3 Persistence (localStorage, from day one)

| Key | Contents |
|---|---|
| `ebe.sketch.v1` | `{skipped: bool, values: number[14] /* 2013..2026 */, branch: "gentle"\|"right"\|"early"\|"over", ts}` — written on reveal OR on skip (`skipped:true`, no values). Ch 4's callback and the no-sketch variant read this. |
| `ebe.team.v1` | `{league: "ipl"\|"wpl"\|null, team: string /* canonical name or "neutral" */, ts}` |
| `ebe.progress.v1` | `{scene: string /* last anchor reached */, ts}` — powers the return-visit "Continue?" affordance in the nav. |

### 0.4 On-screen copy rules (register)

Fans-first. Banned on-screen anywhere in main flow or teasers: *hazard, Kaplan-Meier, survival curve, censoring, Gini, percentile, z-score, regression, distribution, statistically significant.* Stage names used in R1a: **"the out-rate, ball by ball"** (hazard curve). All banned words may appear inside footnote sheets and the methods page, where they are introduced as "the technical name for this."

---

## 1. COLD OPEN

Four beats. Total scroll ≈ 650vh plus two tap-gated moments (Reveal, team pick). The reader can reach Chapter 1 having drawn nothing and picked nothing.

---

### Scene CO-1 — The stakes + the draw

**Purpose (one point):** make the reader stake a belief about the scoring explosion before seeing anything.

**Particle field:** not yet born. Black screen. Render loop stopped (nothing to render). A faint static starfield texture (CSS, not GL) so black ≠ broken.

**Annotation plane / layout:**
1. Stakes line, alone on black, centered (fade in on scroll):
   > **Something happened to cricket scoring. Draw what you think it was.**
2. Scroll → the draw screen (sticky). Prompt block:
   > **How many times a season does someone put 200 on the board?**
   > We've drawn 2008–2012 for you. You draw the rest.
   *("someone," not "a team" — the per-team-frequency misreading dies in the prompt itself, not in the axis label.)*
3. Draw canvas: x-axis `2008 → 2026` (19 season ticks, labeled 2008 / 2013 / 2019 / 2023 / 2026 on mobile, all on desktop); y-axis `200-run innings per season`, range **0–80**, gridlines at 0 / 20 / 40 / 60 / 80.
4. **Pre-drawn anchor segment (RESOLVED #2):** 2008–2012 drawn in "ink" style with the true values **11, 1, 9, 5, 5**, with a small chip pinned to it:
   > *2008–2012: about six a season. That much we'll give you.*
5. **The handle:** the pre-drawn ink ends at the 2013 column in a **pulsing handle** — pick-up-the-pen as a direct-manipulation affordance. Grabbing it (or touching any 2013+ column) starts the reader's line. No hint text under the canvas — the handle replaces the old "Drag from 2013 to 2026" line (three text loci stating one contract was two too many).
6. Two buttons, visually equal weight, side by side (stacked full-width on mobile):
   - **[ Reveal ]** — disabled until the reader's line reaches 2026. Tapping it while disabled flashes microcopy beneath it: *Draw to 2026 first.* (Feedback, never a dead control.)
   - **[ Just show me ]** — always enabled, same size, same visual weight. Never a text-link afterthought.

**Interaction:** continuous drag; values snap to integer per season column; lifting the finger and re-touching continues from any column; unfilled columns between touched points linearly interpolated on submit. No eraser needed — redrawing overwrites. Keyboard/screen-reader users: the draw canvas is skipped from the tab order; **[ Just show me ]** is the first focusable control (blueprint: nobody is ever gated on drawing).

**Skip path:** **[ Just show me ]** → jumps directly to CO-2's truth curve fully drawn (no branch copy, no gap shading), writes `ebe.sketch.v1 = {skipped:true}`, then flows into CO-3 normally.

**Mobile:** canvas height ~55vh, y-axis labels inside the plot area (left-anchored) to save width; drag target is the full canvas height per column; the two buttons full-width, Reveal above Just-show-me (equal styling).

**Reduced-motion (and SR) default:** the just-show-me path is the *default* — the draw screen still renders (drawing is interaction, not motion) but the page's initial CTA emphasis flips to **[ Just show me ]** and the reveal animation is replaced by the end state.

**Footnote layer (ⓘ on the prompt):** what a "200-run innings" is (any innings, either batting side, reaching 200+; super overs excluded); why the y-axis is counts, not averages; the first-innings-only version of the stat (P(first innings ≥ 200): 7.7% in 2008-10 → 41.9% in 2023-26; 52% in 2026) for readers who want the classical framing.

**Exact numbers used:** pre-drawn 11, 1, 9, 5, 5 (data-profile scoring table, "200+ inn" column). Truth polyline for CO-2: 2013–2026 = **4, 9, 7, 6, 10, 15, 11, 13, 9, 18, 37, 41, 52, 65**.

---

### Scene CO-2 — The reveal (with scripted branches)

**Purpose:** the truth peels away from the reader's line; the divergence is quantified **in totals** (not runs — the old "34 runs too gentle" copy is dead).

**Particle field:** still none. This is a 2D moment on the annotation plane.

**Choreography:** on **[ Reveal ]**, the true line draws itself 2013 → 2026 over the sketch (~400ms/season, ~5.6s total; tap or scroll skips to end). The reader's line remains in their ink color. The **gap region is shaded per season, wherever |truth − sketch| ≥ 8** — a per-season test, never "from the first such season onward," so seasons where the reader was right are never shaded as misses. A chip lands on 2026 with the branch copy.

**Branch logic + EXACT copy** (evaluated from the sketch; `y26` = reader's 2026 value, `d̄` = mean of reader's 2013–2022 values; truth: 2026 = 65, 2013–2022 sum = 102). **Evaluation is first-match, in this exact order: over → early → right → gentle.** The predicates overlap by design; the declared precedence resolves every sketch to exactly one branch:

| Order | Branch | Predicate (first match wins) | On-screen copy |
|---|---|---|---|
| 1 | **over** | `y26 > 77` | **You out-dreamed it — barely.** 2026 alone put up **65** two-hundreds, more than any season in history. Your line: **{y26}**. |
| 2 | **early** | `y26 ≥ 53` AND `d̄ > 20` | **You called the flood — but rang the bell early.** From 2013 to 2022 you imagined **{Σ sketch 2013-22}** two-hundreds; the league managed **102**. Then 2023 happened. |
| 3 | **right** (RESOLVED-scripted celebration-and-escalation) | `53 ≤ y26 ≤ 77` (high-decade sketches already caught by "early") | **You knew.** But do you know **when** it broke? The eye says **2018** — the year the sixes exploded. The scoreboard says **2023**. |
| 4 | **gentle** (default) — copy gated on `d̄`: | `y26 < 53` AND `d̄ ≤ 20` | **You were {65 − y26} two-hundreds too gentle about 2026.** The real number: **65**. For fifteen years you'd have been right — then the ceiling broke. |
| 4′ | **gentle** (flood-early-then-collapse variant) | `y26 < 53` AND `d̄ > 20` | **You imagined the flood early — then lost your nerve.** The real 2026: **65**. |

Branch is stored in `ebe.sketch.v1.branch` (`gentle` covers 4 and 4′; the copy variant recomputes from the stored values). *(Copy decisions: the blueprint scripts only "gentle" and "right"; "early" and "over" are authored here so no drawer gets a mismatched chip. "Gentle" gates its "fifteen years you'd have been right" clause on `d̄ ≤ 20` — a reader who drew a wild decade collapsing to a low 2026 is never told copy their own sketch contradicts. The old "most people put the jump five years too early" line is dead: no reader-sketch aggregate exists yet (methods §5), so the "right" branch is re-anchored to the verified staggered-breaks finding — six-rate break ~2018 vs run-rate break 2023, Ch 10's seismograph. "Early" doubles as a quiet plant for Ch 4/Ch 7's 2023 mystery.)*

**Universal bridge line** (all branches, and the just-show-me path, below the chart, with a scroll cue):
> **Nineteen seasons. 1,331 matches. Here comes every ball of it.**

**Interactions / skip:** tap anywhere skips the line-drawing animation to its end state. Scrolling past also completes it instantly.

**Mobile:** chip anchors above the 2026 endpoint; if the sketch crowds it, the chip docks to the top of the canvas with a pointer line.

**Reduced-motion:** truth line and gap shading render instantly as the end state; the branch chip appears with no animation; the bridge line is static text.

**Footnote layer:** none new (CO-1's sheet covers definitions).

---

### Scene CO-3 — The assembly (GSAP scrub set piece #1) + title card

**Purpose:** every ball ever bowled materializes; the dataset becomes a *place*. One point: **all of it is here, and it stays.**

**Particle field:** the field is born. Scroll-scrubbed over **~300vh** (sticky). Deliveries stream in **season by season, chronologically** (point order in the buffers is already chronological; in-shader assembly from group ids — zero new layout bytes). Each season pours into the free-field cloud; a **live counter** (DOM, top center, tabular figures) counts points actually landed — it can only ever end at **316,199**.

**WPL staging (RESOLVED #4 / §2 rule — separate-not-late, authored):** when the scrub reaches 2023, the IPL stream visibly thickens first — its own micro-stop — and **a beat later (~10vh of scrub)** the WPL begins assembling **apart**: its 20,642 points rain into a visually distinct constellation region (upper-right sky on desktop, upper third on mobile), in the WPL hue family. Staggering the two starts keeps one change per beat — the reader never has to parse "the ceiling broke" and "a second league appears" in the same instant, and the WPL's rain can never be misattributed to the IPL's thickening. It completes alongside IPL 2026. It is never the last item in a queue.

**Authored counter stops (annotation micro-captions, one at a time, tied to scrub position):**
1. 2008 lands → *2008: the first **13,489**.*
2. 2015 passes → ***122,434** and climbing.*
3. 2023 begins → *2023: the year the ceiling broke —* (one change only: the IPL stream visibly thickens; the WPL has not started yet)
4. A beat later, the WPL constellation starts → **And a second league assembles — deliberately apart, its own body of light. The WPL: 20,642 deliveries.** Unlike micro-captions 1–3 (ephemeral), this caption **pins once triggered** and holds until the title card fades in — a fast scrub can never skip the piece's only authored "deliberately apart" signal. One number only; 88 matches / four seasons live in C1-6's beat and dagger and in the title card's stat line.
5. Scrub end → counter locks at **316,199**; the field settles; the pinned WPL caption hands off; **title card** fades over it:

> # EVERY BALL EVER
> **316,199 deliveries · 1,331 matches · 19 IPL seasons + 4 WPL seasons · 938 players**
> Every one of them is on this screen right now. They never leave. ⓘ

**Count traceability (pipeline addition):** `meta.json` v2 must emit `n_players` (registry-ID count) and per-league `n_matches` alongside `n_points` — today's meta.json holds `n_points` only, and "938 players" otherwise traces to nothing but blueprint copy citing copy. The title card reads **every** count from the artifact, and the QA harness asserts card == artifact. If the registry count differs from 938, the artifact wins and the copy updates.

**Interactions / skip:** the scrub *is* the interaction; fast scrolling is allowed and safe (morph is position-interpolated, no physics). No tap required anywhere.

**Mobile:** counter pinned top-center at ~15vw max width; captions bottom sheet style; WPL constellation placed upper third so the thumb never covers it.

**Reduced-motion:** the field renders **fully assembled** (live GL end state — team/theming shaders still apply); the counter renders as static text `316,199`; captions 1–4 collapse into one static narration block under the title card:
> *Between 2008 and 2026, 316,199 deliveries were bowled across the IPL and WPL — 1,331 matches, 938 players. The WPL's 20,642 arrive as their own constellation, apart from the IPL's cloud.*

**Footnote layer (ⓘ on the title card — the ball-count footnote, verbatim spec):**
- **What counts as a ball:** every legal and illegal delivery recorded by Cricsheet, **except super-over deliveries**. The corpus holds **316,388** deliveries; **189** of them belong to the 17 tie-match super overs (36 super-over innings) and are excluded from the field — what you see is exactly **316,199**. (Owner rule: never show a number the pixels contradict.)
- Wides don't count toward a batter's balls faced; no-balls do (convention used throughout).
- Data source: Cricsheet ball-by-ball JSON; season labels normalized (2007/08→2008, 2009/10→2010, 2020/21→2020).
- Link: *Full methods →* (methods page).

---

### Scene CO-4 → handled by the Team Picker (Section 2).

---

## 2. TEAM PICKER (Scene TP)

**Purpose (one point):** claim your thirty-odd thousand points of light — or don't; both are first-class.

**Particle field:** the assembled free field idles dimmed behind the picker (loop stopped). On tile tap: one render pass ignites that franchise's balls in team color (subset color swap, not a morph). Demand-mode: render only on selection change.

**Annotation plane / layout:**
> *Thirty-odd thousand of these points belong to one team. Yours?*
> **Pick your team.**
> Its deliveries ignite in its colors — and stay lit through the whole story.

*(The bridge line converts the ask into a payoff of the field the reader just watched assemble — never a cold imperative straight after "they never leave.")*

**16 tiles, equal size and identical styling** — the **neutral tile first and full-width**, then 15 crest tiles (grid: 2 columns portrait mobile, 4 per row desktop), grouped with two small headers:

- **Neutral — a full-width tile directly under the heading, before the IPL group, visible in the first viewport on every phone:** **“No team — show me everything.”** Tile styling identical to the crests, never link styling. (A 2×8 crest grid puts a 16th tile below the fold on most phones; the locked rule — "its skip exactly as prominent as the sketch's" — means the skip must be *seen* without scrolling, not merely exist.)
- **IPL** (10): Chennai Super Kings · Delhi Capitals · Gujarat Titans · Kolkata Knight Riders · Lucknow Super Giants · Mumbai Indians · Punjab Kings · Rajasthan Royals · Royal Challengers Bengaluru · Sunrisers Hyderabad
- **WPL** (5): Delhi Capitals · Gujarat Giants · Mumbai Indians · Royal Challengers Bengaluru · UP Warriorz

*(Names are the canonical current franchise names from the pipeline's canonicalization tables; they match `payoff/ch1.json` exactly. WPL sister franchises show a "WPL" corner tag so the two Mumbai/Delhi/Bengaluru tiles are never ambiguous.)*

**Skip prominence (locked):** the neutral tile *is* the skip — full-width, first, above the fold, same tile treatment — plus a persistent line under the grid: *You can change this anytime from the menu.* No modal, no confirm step.

**Interaction:** single tap = select: the field ignites (one render), a toast confirms — *"{Team} it is. Change anytime in ☰."* — and the page auto-advances to Chapter 1 after ~1.2s. **The toast persists across the transition and dismisses itself early in C1-1** (~2s total life): the change-anytime reassurance — the line that justifies the no-confirm design — travels with the reader instead of racing the auto-advance while the ignite render pulls attention to the field. Tapping a different tile within the advance window re-selects. Keyboard: tiles are buttons in a roving-tabindex grid; selection announces via `aria-live`.

**Persistence:** `ebe.team.v1` written immediately. The sandbox (R1b) and every payoff card read it. Returning visitors skip this screen (nav offers "Change team").

**Mobile:** tiles ≥ 88px tall; crest + short name; the field's ignite preview is visible above the fold behind a translucent grid.

**Reduced-motion:** ignite is an instant color state (it already is — no interpolated pulse); auto-advance replaced by an explicit **[ Continue ]** button (motion-free page transitions).

**Footnote layer:** none. (Franchise rename lineage — Daredevils→Capitals, Kings XI→Punjab Kings, Bangalore→Bengaluru — lives on the methods page.)

---

## 3. CHAPTER 1 — The Death of the Sighter

Beat budget check: hero (Death of the Sighter, carried by the wall + out-rate strip) + 3 supporting (Ignition Curve — fused into the hero wall; Aerial Risk Ledger; Six-Hitting Democratization) + WPL beat + payoff card. One controlling morph (free field → ignition wall). One subset-highlight (sixes fireworks) plus the WPL shelf glow (color state, not a re-sort). Total scroll ≈ 900vh.

---

### Scene C1-1 — Chapter title + the ritual

**Purpose:** name the thing that died, in fan language, before any data.

**Particle field:** free field dimmed, loop stopped.

**Annotation plane (two caption steps):**
1. > **Chapter 1 — The Death of the Sighter**
2. > For T20's first decade, an innings began with a ritual: **the sighter**. Ten balls of having a look. Getting your eye in. Respecting the bowler.
   > Watch what happened to it.

**Interactions:** none. **Mobile:** full-bleed title, caption card bottom. **Reduced-motion:** static. **Footnotes:** none.

---

### Scene C1-2 — The ignition wall (controlling morph)

**Purpose (one point):** the slow start is gone — the "warm-up" region of the innings caught fire, season by season.

**Particle field:** THE morph of the chapter, scrubbed over ~150vh: every ball flies from the free field to the **ignition wall** — x = the batter's balls-faced-so-far at that delivery (1 → 30+, capped bucket at right edge, **labeled `30+` everywhere it renders, desktop and mobile** — an open bucket never masquerades as a plain value), y = season rows (2008 bottom → 2026 top; WPL's four rows sit as a visibly separate block above 2026 with a gap — same axes, its own shelf), brightness = runs off the bat.

**Destination-first scaffold:** early in the scrub (~first 20vh) the empty wall frame fades in ahead of the points — the x-axis line (`ball 1 … 30+`), sparse season row labels (2008 / 2015 / 2023 / 2026), and the "WPL" shelf label — so the reader watches points fly *into* a labeled frame instead of retro-interpreting the wall after 150vh of unlabeled re-sort. (Caption step 1 still does the full axes-teach after the morph; the scaffold buys mid-flight legibility, it doesn't replace the teach.)

**Flight order:** the flight staggers by season — 2008's rows land first and the wall builds upward, echoing the assembly's chronological pour — so every reader has a trackable rule ("oldest lands first") even without a team hue: neutral pickers and deep-link arrivals cross the chapter's biggest morph with an anchor. The WPL constellation flies to its shelf **as one coherent block** — upper-right sky → upper shelf, upper→upper spatial continuity preserved deliberately, so the constellation→shelf tracking the reader built in CO-3 survives the morph. Reader's team stays lit in hue throughout the flight (object constancy). After the morph completes, the wall holds still for the caption steps (loop stopped between steps).

**WPL shelf staging (preattentive honesty):** from the moment the wall completes, through caption steps 2–4, the WPL shelf renders **dimmed one stop** — label visible, every point present (the never-leaves rule holds). Reason: the shelf's left edge is genuinely dark (WPL first-10 SR 110.5 ≈ IPL 2008 levels), and steps 2–4's operative image — an upward luminance sweep ending in "by 2026 there is no warm-up left" — must not be contradicted in the exact channel that carries it by the four rows above 2026 going dark again. The shelf returns to full luminance at C1-6, **where its brighten IS the beat.** This is staging, not deficit language: C1-6 is the WPL's authored spotlight, and the IPL field takes the identical one-stop dim there.

**Wire cost:** one new per-point attribute — `ballsfaced.u8` (batter's balls-faced index, capped at 255), ~316KB raw before gz; wall positions computed in-shader from `ballsfaced` + existing season group id. No Float32 layout buffer needed. (Ledger entry in §7.)

**Caption steps (one change each):**
1. *(axes teach — nothing highlighted yet)* > Every ball, arranged by how long its batter had been in. **Left edge: a batter's first balls.** Rows climb from 2008 at the bottom to 2026 at the top. Brightness = runs.
2. *(highlight: bottom-left region)* > **2008: the left edge is dark.** New batters blocked, nudged, had a look. The sighter, visible from space.
3. *(highlight sweeps up the left columns)* > Climb the seasons. **The dark corner catches fire.** By 2026 there is no warm-up left — ball one is attacked at full intent.
4. *(number chip lands, nothing else moves)* > **First ten balls: strike rate 108 → 135.** ⓘ The revolution lives at the start of the innings. *(The ramp-vs-overall comparison — +25% vs +21% — lives entirely in the dagger: comparing two growth rates is a second claim and two extra numbers, and this step is the chip landing, nothing more.)*

**Interactions / skip:** none required; scroll alone lands everything.

**Mobile:** wall fills the viewport; x-axis labeled `ball 1 … 30+` (the capped bucket is always `30+`); season labels only at 2008 / 2015 / 2023 / 2026 rows + "WPL" shelf label; caption card bottom-anchored.

**Reduced-motion:** jump-cut from free field directly to the completed wall (live GL end state, team glow intact); caption steps 1–4 become a static stepped card sequence (tap/scroll through, no interpolation, highlights appear as instant states).

**Footnote layer (ⓘ on step 4):** era bands defined (IPL 2008-10 vs 2023-26); exact figures 108.0 → 135.3; wides excluded from balls faced, no-balls counted; the +25% vs +21% ramp-vs-overall comparison (Ignition Curve recipe); sample sizes per era band.

---

### Scene C1-3 — The pivot (setup for the shock)

**Purpose:** voice the objection every fan is already making, so the next scene can destroy it.

**Particle field:** wall holds, dimmed one stop. Loop stopped.

**Annotation plane (single caption, centered):**
> Of course they score faster. **They must be getting out more — right?**

**Everything else:** none/static. This beat exists so the out-rate strip lands as an answer, not a chart.

---

### Scene C1-4 — The out-rate strip (the 2D scene; the chapter's shock)

**Purpose (one point):** all that extra attack came at **no extra dismissal risk** in the first ten balls. The thesis of the whole piece.

**Particle field:** dims behind the strip; **loop provably stopped** for the whole scene.

**Annotation plane:** a DOM/SVG chart — **"The out-rate, ball by ball."** x = ball of the batter's innings (1–30; if the right edge is the capped bucket it is labeled `30+`, matching the wall); **y = how often batters get out on exactly that ball (%), axis zero-based with a fixed max of 10% (~2× peak hazard) — never auto-scaled, never cropped.** The chapter's shock ("the lines sit on top of each other") is honest only if the scale cannot manufacture separation between 5.04% and 4.93%; the axis range is spec, not an implementer choice. Two curves: **2008-10 as the ghost** (grey, always visible — the era ghost convention starts here) and **2023-26 bold**. Direct end-of-line labels, no legend, no hover.

**Caption steps:**
1. > This is **how often a batter gets out, ball by ball** ⓘ — the grey line is 2008-10. Out-rate on any early ball: about one in twenty.
2. *(bold line draws — the one change)* > Now 2023-26. **The lines sit on top of each other.** Across the first ten balls: **5.04% then. 4.93% now.** All that extra attack — at no extra risk.
3. *(thesis card + scope clause — stated here once for the whole piece)* > That's the story of modern batting in one picture: **not recklessness — skill.** One honest note: this is a first-ten-balls fact. Later in the innings risk *did* rise — **priced and paid on purpose. Chapter 5 publishes the price list.**

**Interaction (+ skip path):** tap any labeled ball tick (1, 3, 5, 10, 15, 20 — targets ≥44px) → a mini card: *"Ball {n}: who most defied the out-rate"* — top 3 batters (min-sample rule from the pipeline), e.g. name · innings survived past ball n · SR on balls 1–n. Data: `data/ch1/outrate.json`. **Skip path:** the captions carry the entire point; the tap adds names, never thesis.

**Mobile:** chart ~40vh, full-width; caption steps below; the defier card is a bottom sheet.

**Reduced-motion:** both curves render together immediately (static-legible by construction); step 2's "draws in" becomes an instant state; taps still work.

**Footnote layer (ⓘ on step 1):** the technical name (*this is a discrete-time hazard curve, estimated Kaplan-Meier-style*); censoring rules (not-out innings censored; retired hurt — 10 cases — and tactical retired out — 5 — censored too); why the out-rate ≠ strike rate (risk per ball vs runs per ball); wides/no-balls conventions; per-era sample sizes; **The Over as a Clock Face** (the demoted exhibit, a small static 2D radial inside the sheet): *even inside the over the sighter died — 2008-10 overs ran quiet-loud-quiet (ball 1 = 7.34 RR, ball-3 peak 8.02); 2023-26 overs start hot and fade (ball 1 = 9.20, ball 6 = 8.89)*; **the environment note (causal inoculation, one line):** *the environment moved too — pitches, rules (the 2023 Impact Player among them). Chapters 4, 7 and 10 apportion the credit; the early-innings out-rate stayed flat across all of it.*

---

### Scene C1-5 — The fireworks (subset-highlight: every IPL six ever)

**Purpose (one point):** the six went from a specialist's weapon to everyone's — and the swing got *better*, not just braver.

**Particle field (two-phase choreography — the axis-role swap is staged, not sprung):** all IPL six-balls first **lift vertically in place** out of the wall — the reader sees exactly which points are leaving and that they came from the wall — while the wall behind them **dims hard**; only then do the lifted sixes re-sort into **19 per-season firework columns** on what now reads as a fresh stage (x = season, column height = that season's six count; each point is a real six). The wall's "up = later season" briefly becomes the columns' "right = later season"; the two-phase stage-clear is what keeps that swap legible, and the settle reverses it. 2008: three tall rockets' worth; 2026: a skyline. WPL sixes stay in the constellation — deliberately not staged as short columns beside IPL skyscrapers (WPL framing rule; the WPL's scoring engine gets its own beat next, on its own terms). **Step 3's one change is a per-point recolor:** every column splits two-tone — sixes by that season's top-10 six-hitters vs everyone else's — so the shrinking specialist share is a preattentive proportion change on columns already on screen, not an assertion floating over counts. After the caption steps, the sixes **settle back into the wall** (reverse two-phase: columns dissolve back over the dimmed wall, then the wall re-brightens; constancy restored before the next scene).

**Wire cost:** zero new bytes — six-balls are identifiable from the existing per-point runs attribute (`attrs.u8`); columns are group-indexed (season) + in-shader stacking jitter; the step-3 two-tone flag ("hit by that season's top-10 six-hitter") packs into a spare bit of the existing `attrs.u8` (pipeline re-encode, no new artifact, ledger delta 0).

**Caption steps:**
1. > **Every IPL six ever hit, stacked by season.** 2008: a six every 21 balls. 2026: **every 12.** (The WPL's sixes stay in its constellation — its scoring engine gets its own beat, next.)
2. > Batters aren't just swinging more — **more big swings land: 58.7% → 67.3%.** ⓘ Braver *and* better.
3. *(the one change: every column splits two-tone — the top-10 hitters' sixes vs everyone else's)* > And the six stopped being a specialist's weapon. **Players with ten-plus sixes in a season: 18 in 2008 → 58 in 2026.** Watch the specialists' slice of every column shrink. ⓘ

*(Caption discipline: step 1 is scoped to the league actually on screen — "every six ever" over IPL-only pixels violated the pixels-match-copy rule — and names the WPL omission as deliberate, pre-answering the observant reader in the house framing. Step 2 leads with the fan gloss and carries exactly one pair; "aerial attempts +56%" is demoted to the dagger, where the proxy is defined and the exact rates already live. Step 3 carries one pair; 35.9% → 28.1% moves to the dagger — the recolor shows the share shrinking, so the caption doesn't have to quote it.)*

**Interactions:** none (subset scene lands by scroll alone).

**Mobile:** 19 thin columns fit portrait width; the 2008, 2023 and 2026 columns are labeled (2023 too — the skyline's step lands there); caption card bottom.

**Reduced-motion:** jump-cut straight to the fully stacked columns (the two-phase lift collapses); the step-3 recolor is an instant state; settle-back becomes a jump-cut back to the wall.

**Footnote layer (ⓘ on steps 2 and 3):** the aerial-attempt proxy, named and defined here (sixes + caught dismissals; caught includes keeper/slip edges — stable noise, so era *comparisons* hold; true intent would need ball-tracking); **attempts up +56%** — exact rates 7.3 → 11.4 per 100 balls; **the top-10 hitters' share of league sixes fell 35.9% → 28.1%** (step 3's shrinking slice, quantified); six-concentration technical note (season six Gini 0.49-0.54 → 0.40-0.46, batters ≥30 balls); balls-per-six 20.8 → 11.7 behind the rounded 21 → 12; **denominator honesty:** seasons grew too (more matches, more balls: 13,489 in 2008 vs far more now) — column heights are raw six counts, so the per-ball rate (every 21 → every 12) is the honest comparison, and it is the one the caption quotes.

---

### Scene C1-6 — The WPL beat (two clocks, one beat — the only public WPL narrative until R4)

**Purpose (one point):** the WPL is **already moving — and not along the IPL's track.** (Timeline stat and dialect stat in the same breath; "already moving" is the grammatical subject; no deficit language anywhere.)

**Particle field:** the WPL's **shelf on the wall brightens to full** — restoring the one stop it lost in C1-2, so the brighten IS the beat; IPL points dim one stop (the mirror of the treatment the shelf carried through C1-2/4/5). **Shelf only:** during wall layout every WPL ball lives on the shelf — there is no separate cloud, and no WPL point may render twice ("every ball on screen exactly once"; the constellation→shelf identity was preserved as one coherent block in the C1-2 morph). A color-state change, not a re-sort. Loop renders once per state.

**Annotation plane:** a compact 2D panel beside/below the field:
- **Strike-rate ignition curves as peers** — panel titled in-frame: **"Strike rate, ball by ball."** Same *x*-axis convention as the wall and the out-rate strip (balls faced 1–30+), but a **new y-axis: strike rate — labeled on the axis, zero-based with a fixed max** — NOT the out-rate. The era-ghost *line* convention carries over (IPL 2008-10 ghost grey, IPL 2023-26 bold, WPL solid in WPL hue — three labeled lines), so the panel must carry a **visibly different frame/accent treatment from C1-4's strip**: a reader who just internalized "ghost-grey/bold curves on balls 1–30 = how often batters get out" must never read the WPL's high line as "gets out more." The WPL line is a peer line, never an annotation on an IPL chart.
- **The engine pair:** two bars, zero-based — *share of runs scored in fours*: **WPL 46.8%** vs **IPL (2023-26) 33.9%**.

**Caption (single step — the two clocks must share one beat, so this is one card; ≤45 words):**
> **The WPL is already moving — and not on the IPL's track.** Four seasons in, its first-ten-balls strike rate — **110.5** — sits where IPL 2008 stood. But the engine is new: **46.8% of its runs come in fours.** The modern IPL: 33.9%.

*(~40 words. The WPL's numbers — 110.5, 46.8% — render in the WPL hue, color-linked to its line and bar to cut visual search; hue stays identity, not quantity — the tint names whose number it is, nothing more. The cut flourish moves to the dagger.)*

**Interactions:** none. **Mobile:** panel stacks — curves above, bars below, caption last.

**Reduced-motion:** brighten/dim are instant states; the panel is static SVG.

**Footnote layer (ⓘ):** WPL sample honesty (88 matches, 20,642 deliveries — four seasons young; early curves will move); six-share companion (WPL 15.5% vs IPL 29.0%); why "behind" is the wrong word (outcome *mix* vs outcome *rate* — full treatment in Chapter 6, teased by name: *Two Dialects*); aerial-execution comparison lives here too (WPL execution 54.5%, at intent-era IPL levels) rather than in main flow; the caption's cut flourish — *a four-led attack the men's league never played at any age* — lands here beside the six-share pair.

---

### Scene C1-7 — Team payoff card

**Purpose:** the chapter's finding, re-told in the reader's colors. Strictly template + `payoff/ch1.json` (16 variants, snapshot-tested; never hand-authored).

**Particle field:** reader's team balls at full ignite on the wall; everything else dims. One render.

**Card template — IPL picker:**
- Header: crest + **"{Team}'s first ten balls"**
- Mini ignition strip: two small curves (early era vs recent era, team-only balls).
- Headline: **from JSON verbatim** (e.g. CSK: *"Chennai Super Kings's first ten balls: strike rate 110.0 in 2008-2010, 134.4 in 2023-2026 — +24.4 points of intent."*).
- **Fastest starter line:** *"Fastest starter in {Team} history: {player} — SR {x} on his first ten balls (min 100 balls)."* → **pipeline addition:** `payoff/ch1.json` v2 must add `fastest_starter {name, first10_sr, sample_balls}` per variant; the snapshot harness gains a non-degeneracy assertion for it.
- Designed empty state (already authored in JSON for GT / LSG / SRH): *"{Team} was born into the attack era — it has no 2008-2010 innings to compare. Its batters' first ten balls already run at a strike rate of {x}."*

**Card template — WPL picker (the bespoke R1 WPL card, mandatory per release checklist):**
- Header: crest + **"{Team}, four seasons in"**
- **Mini league-age sparkline pair:** two tiny slope lines, league years 1–4 — IPL falling, WPL rising, the WPL line in WPL hue — **sharing one fixed y-domain** (axis honesty), so the opposite directions are preattentive before any number is read. (The IPL cards get a mini visual; the mandatory bespoke WPL card gets one too.)
- Headline (template, numbers from JSON + data-profile constants — the team pair plus one league pair, nothing more): *"Four seasons in, your league is **already climbing**: run rate **8.08 → 8.54** — while the IPL at the same age was still falling. {Team}'s first ten balls: **{early} → {recent}**."* ("Climbing **while** the IPL was still falling" replaces "climbing faster than the IPL did" — out-climbing a decline is a slippery brag; the honest phrasing is also the stronger one. The IPL pair leaves the headline entirely.)
- Clock plant (one line, verbatim): *"Remember that clock. We'll come back to it."* (League Maturity Clock, planted three chapters early per blueprint.)
- Card dagger: the IPL comparison pair (league years 1–4: **8.31 → 7.73**) with the era-band note; the **full year-by-year series** (IPL 8.31 / 7.48 / 8.13 / 7.73 · WPL 8.08 / 7.86 / 8.37 / 8.54 — both paths non-monotonic; endpoints alone flatter both); WPL era bands 2023-24 vs 2025-26 (from JSON `eras.wpl`); and the JSON's small-sample honesty sentence — **the template must render it**.
- **Snapshot-review note:** the DC-W variant carries a negative team delta (115.2 → 113.6) under the "already climbing" league header — the review must confirm it reads as candor, not contradiction (the league claim and the team pair are separate clauses by design; the honesty sentence sits between them).

**Card template — Neutral:** league-wide card, rendered **from JSON verbatim like every other variant** — the desired copy is a pipeline change, never a hand-authored overlay: `payoff/ch1.json` v2 rewrites the Neutral headline to *"The league's first ten balls: strike rate **108.0 → 135.3** — and the out-rate on those balls never moved."* (scope clause included — the flat out-rate is a first-ten-balls fact) and the snapshot re-baselines. + fastest starter in IPL history line (same v2 field on the Neutral variant).

**Interactions (+ skip):** **[ Not your team? Change it ]** link → picker (state preserved, returns here). Card is otherwise static.

**Mobile:** card is a full-width sheet over the dimmed field.
**Reduced-motion:** static card, instant ignite state.
**Footnote layer (ⓘ):** min-sample rules (team first-10 pools; per-era ball counts shown, e.g. `sample_balls_early/recent` from JSON); why franchise renames merge histories (Daredevils→Capitals etc.).

---

### Scene C1-8 — Chapter close

**Purpose:** compress the chapter to one sentence and aim it at the rest of the piece.

**Particle field:** the wall exhales back into the free field (reverse of the controlling morph, fast — ~40vh scrub; this is the same morph's return leg, not a second morph).

**Annotation plane (single caption):**
> Batters attacked from ball one — and those balls cost them nothing extra. Where risk rose later, they paid it on purpose. That freedom rewired everything: what a good score is, what bowlers do, **what a wicket is worth.** That's the rest of the story.

*(Scope survives the summary: the chapter's most quotable line may never restate the no-extra-risk claim unscoped — "paid nothing for it" would reverse the piece's one mandated inoculation (C1-4 step 3) four scenes after it was stated. "Those balls cost them nothing extra / where risk rose later, they paid it on purpose" keeps the punch and the scope.)*

**Reduced-motion:** jump-cut back to free field.

---

## 4. END CARD (Scene EC)

**Purpose:** close the R1a read with the piece's shape visible: what's done, what's next, where the methods live. No dead links, no promised features that don't exist yet.

**Particle field:** free field idles dim behind the card; loop stopped.

**Card content (DOM, in order):**
1. Progress marker: **Chapter 1 of 10 — The Death of the Sighter · done.**
2. Next-chapter tease: **Next — Chapter 2: The Last of the Anchors.** *A whole species of batter is about to go extinct.* Tag: `in build — the story grows chapter by chapter`.
3. **Sandbox tease** (R1b is not live yet — tease, don't link): **The field will be yours.** *Every one of the 316,199 balls on this screen, filterable under your thumb — season by season, team by team{, pre-tuned to {Team}| — pre-tuned to whichever team you pick}. Next release.* *(Conditional clause resolves from `ebe.team.v1`; neutral pickers get the second form.)*
4. Methods link: **How we computed all of this →** (methods page).
5. Footer microcopy: *Data: Cricsheet, ball-by-ball, through IPL 2026 / WPL 2026.*

**Interactions:** links only. **Mobile:** single column. **Reduced-motion:** static.

---

## 5. METHODS PAGE STUB (`/methods`, prerendered, linked from EC + footnote sheets)

R1a ships the stub: section headers + one honest paragraph each (grows every release). Sections:

1. **The corpus.** Cricsheet ball-by-ball JSON: 1,243 IPL matches (2008–2026) + 88 WPL matches (2023–2026) = 1,331. 938 players by registry ID (the count `meta.json` v2 emits — the artifact, not this page, is the source of truth). Season normalization (2007/08→2008, 2009/10→2010, 2020/21→2020).
2. **What counts as a ball.** Corpus total 316,388 deliveries; the field renders **316,199** — the 189 super-over deliveries (17 tie matches, 36 super-over innings) are excluded from all ball-level stats and from the pixels. Wides excluded from balls faced; no-balls counted; dot ball = legal delivery, zero total runs.
3. **The out-rate, ball by ball** *(technical name: discrete hazard, Kaplan-Meier-style)*: estimator, censoring of not-outs / retired hurt (10) / retired out (5); why hazard ≠ strike rate; era bands 2008-10 vs 2023-26 and per-band sample sizes.
4. **Aerial attempts proxy.** Attempts = sixes + caught dismissals (c&b excluded); the edge-rate stability argument; what ball-tracking would add.
5. **The draw.** Truth series definition (200-run innings per season, any innings, super overs excluded), the pre-drawn 2008–2012 anchor values, and how branch thresholds are computed. Aggregated sketch statistics may be published in a later release *(supports Ch 4's "here's what most readers drew" no-sketch variant)*.
6. **Payoff cards.** Template + per-team JSON from the pipeline; 16/16 snapshot harness; min-sample and designed-empty-state rules; franchise rename lineage table.
7. **Rendering honesty.** Demand-mode rendering; reduced-motion = live end-state jump-cuts (why there are no pre-baked frames); payload budgets and the ledger.
8. **Licenses & credits.** Cricsheet (ODbL attribution), three.js/GSAP/SvelteKit, and the project's own license note.

---

## 6. PERSISTENT CHAPTER NAV (ships with R1a)

- **Affordance:** a fixed ☰ button, top-right, 44×44px, translucent over the field; visible in every scene (dims to 40% opacity during the assembly scrub and the ignition morph so it never fights a set piece; never hidden).
- **Opens:** full-screen sheet (mobile) / right rail (desktop). Contents, in reading order: **Cold open — Draw it** · **Team: {crest/name} — change** · **Chapter 1 — The Death of the Sighter** (live) · Chapters 2–10 + *The Net Session* interlude + *The Field Is Yours* (the bowl), each listed by title with a `soon` tag — the full menu is the promise of shape; total length is a menu, not a gauntlet. No teaser copy on unbuilt chapters beyond titles (titles are commitments; numbers aren't, yet).
- **Jump behavior:** entries anchor to scene starts (`#coldopen`, `#picker`, `#ch1`, `#end`). Chapters stand alone: jumping into Ch 1 without a sketch or team pick must work — the chapter renders with neutral field + neutral payoff variant until a pick exists.
- **Resume:** on return visits with `ebe.progress.v1`, the nav button shows a dot and the sheet's top row offers **Continue where you left off →**. Shared-link arrivals mid-piece get the same nav without any gating.
- **Team change:** selecting "change" opens the picker in an overlay; on pick, the field re-ignites and any visible payoff card re-renders from the new JSON variant.
- **Keyboard/SR:** the sheet is a focus-trapped dialog; ESC closes; entries are real links.
- **Reduced-motion:** navigation jumps are instant (no smooth scroll); each target scene renders its end state on arrival.

---

## 7. HUD — dev-only (standing)

The R0 HUD (fps, draw calls, scrub progress, layout index) remains gated behind `?hud=1` **only**: no UI link, no keyboard shortcut, excluded from tab order, `aria-hidden`, and never mentioned in shipped copy. It ships in the production bundle (it's how field issues get diagnosed on real phones) but is unreachable without the query param. A release-checklist assertion: default page load renders zero HUD DOM.

---

## 8. R1a payload inventory (ledger deltas)

| Artifact | New in R1a | Est. size (gz) | Budget bucket |
|---|---|---|---|
| `meta/groups/group_ids/attrs` (R0) | field adds only: `meta.json` v2 (+`n_players`, per-league `n_matches` — title-card traceability) · one spare `attrs.u8` bit re-encoded as the season-top-10-hitter flag (C1-5 step 3) | 114KB (measured; deltas ≈ 0) | pre-assembly (≤3MB) ✓ |
| `ballsfaced.u8` (per-point balls-faced index, cap 255) | **yes** | ~80–150KB | Ch 1 (≤2MB) ✓ — lazy-loaded at Ch 1 entry, not before assembly |
| `draw/truth.json` (19 IPL season counts + branch constants) | **yes** | <1KB | pre-assembly ✓ |
| `ch1/outrate.json` (per-ball out-rates ×2 eras + WPL curve + defier lists) | **yes** | ~3–6KB | Ch 1 ✓ |
| `ch1/wpl.json` (fours-share pair, six-share, league-age RR series) | **yes** (may fold into `outrate.json`) | <1KB | Ch 1 ✓ |
| `payoff/ch1.json` v2 (+`fastest_starter` per variant; Neutral headline rewritten with the scoped out-rate clause) | field add + copy rev | ~1.5KB | Ch 1 ✓ (v1 measured 1.3KB) |
| Ignition wall / firework columns / assembly layouts | no new buffers — in-shader from `ballsfaced` + group ids + runs attr | 0 | — |

Cold-open assembly needs only the R0 spike set (+`draw/truth.json`): **~115KB ≪ 3MB.** Chapter 1 total delta: **≲160KB ≪ 2MB.** The ledger (`pipeline/ledger.py`) gains rows for each new artifact; "chapter payload within budget" stays a release pass criterion.

---

## 9. Verified-number index (single source for QA)

| On-screen claim | Value | Source |
|---|---|---|
| Pre-drawn 2008–2012 200-run innings | 11, 1, 9, 5, 5 (≈6/season) | data-profile IPL scoring table |
| Truth 2013–2026 | 4, 9, 7, 6, 10, 15, 11, 13, 9, 18, 37, 41, 52, **65** | data-profile |
| Actual 2013–2022 sum ("the league managed 102") | 102 | data-profile (sum) |
| Counter stops | 13,489 (2008) · 122,434 (thru 2015) · 316,199 (final) | `groups.json` cumulative |
| WPL constellation | 88 matches · 20,642 deliveries · 4 seasons | data-profile + `groups.json` |
| Title card | 316,199 · 1,331 · 19+4 seasons · 938 players | `meta.json` v2 (pipeline must emit `n_players` + per-league `n_matches`; QA asserts card == artifact; if the registry count ≠ 938, the artifact wins) |
| "Right" branch break years ("the eye says 2018, the scoreboard says 2023") | six-rate break ~2018 · run-rate break 2023 | catalog (League Pulse Seismograph, staggered breaks — Ch 10) |
| Footnote-only counts | 316,388 corpus · 189 super-over balls · 17 tie matches / 36 SO innings | blueprint §7 + catalog bookkeeping |
| First-10-ball SR | 108.0 → 135.3 (headline "108 → 135") | catalog (Death of the Sighter ★) |
| Out-rate first 10 balls | 5.04% → 4.93% | catalog ★ |
| Ramp vs overall SR growth (dagger only) | +25% vs +21% | catalog (Ignition Curve) |
| Balls per six | 20.8 → 11.7 (headline "every 21 → every 12") | data-profile |
| Aerial attempts / execution | 7.3 → 11.4 per 100 balls (+56%) / 58.7% → 67.3% | catalog (Aerial Risk Ledger) |
| ≥10-six players / top-10 share (share quantified in dagger; on screen as the two-tone recolor) | 18 → 58 / 35.9% → 28.1% | catalog (Six-Hitting Democratization) |
| WPL first-10 SR | 110.5 | catalog |
| Fours-share of runs | WPL 46.8% vs IPL (2023-26) 33.9%; six-share 15.5% vs 29.0% (footnote) | catalog (Run DNA) |
| League-age RR (WPL card; IPL pair + year-by-year in the card dagger) | IPL yrs 1–4: 8.31 → 7.73 (8.31 / 7.48 / 8.13 / 7.73) · WPL yrs 1–4: 8.08 → 8.54 (8.08 / 7.86 / 8.37 / 8.54) | data-profile |
| Axis constants (honesty-locked) | out-rate strip y: fixed 0–10% · C1-6 strike-rate panel y: zero-based, fixed max · C1-7 sparklines: one shared y-domain · engine bars zero-based · capped buckets labeled `30+` | this storyboard (C1-2/4/6/7) |
| Over-clock footnote radial | ball-1 RR 7.34 → 9.20; 2008-10 ball-3 peak 8.02; 2023-26 ball-6 8.89 | catalog (Clock Face) |
| P(first innings ≥200) footnote | 7.7% → 41.9%; 2026: 52% | catalog (Threshold Exceedance) |
| Team payoff figures | per-variant, from `payoff/ch1.json` verbatim (e.g. CSK 110.0 → 134.4; Neutral 108.0 → 135.3) | pipeline JSON |

---

## 10. R1a QA checklist (storyboard-level)

- [ ] Glossary scan: no banned term (§0.4 list) in any main-flow or teaser string; "out-rate, ball by ball" used wherever hazard is meant.
- [ ] Pixel-number audit: every visible ball count says 316,199; 316,388/189 appear only inside footnote sheets and `/methods`.
- [ ] 16/16 payoff variants non-degenerate (incl. new `fastest_starter`), WPL bespoke card present, empty states authored.
- [ ] Reduced-motion pass: every scene above has its jump-cut state exercised; no beat requires motion or a tap to land its point.
- [ ] No hover-only content anywhere (all ⓘ and defier cards are tap/keyboard).
- [ ] WPL beat reads two clocks in one caption card; no sentence with WPL as object of "behind/lags/still/only."
- [ ] Demand-mode: idle GPU ~0 in scenes CO-1/2, C1-1/3/4/6/7, TP idle, EC, methods.
- [ ] Payload ledger re-run passes all four checks with the new artifacts.
- [ ] Nav reachable and functional from every scene; deep entry into `#ch1` works with no sketch/team state.
- [ ] Default page load renders zero HUD DOM; `?hud=1` still works.
- [ ] Caption grammar lint (§0.1): no caption step exceeds ~45 words; no step carries more than 3 numbers; exactly one on-screen change per step.
- [ ] Luminance-sweep audit: no highlighted-sweep scene contains an un-dimmed region whose luminance contradicts the sweep's claim (C1-2: WPL shelf dimmed one stop through steps 2–4, restored to full at C1-6).
- [ ] Axis honesty: all rate/count axes zero-based, or the truncation named on screen; compared series always share one scale; out-rate strip y fixed at 0–10%; C1-6 panel titled "Strike rate, ball by ball" with its own y-label and a frame treatment visibly distinct from the out-rate strip; every capped bucket labeled `30+`.
- [ ] CO-2 branch unit tests: sweep the (y26, d̄) sketch space — every sketch maps to exactly one branch under the first-match order (over → early → right → gentle), and gentle's copy variant matches its d̄ gate; no reader can receive copy their own sketch contradicts.
- [ ] Scope audit: no unscoped restatement of the no-extra-risk claim anywhere outside C1-4's scope clause (C1-8's close and the v2 Neutral headline both carry the first-ten-balls scope).
- [ ] Title-card counts (316,199 / 1,331 / 19+4 / 938) equal `meta.json` v2 values — asserted in the snapshot harness.
- [ ] Pixels-match-copy: WPL sixes absent from the firework columns AND the caption reads "Every IPL six ever" — never "every six ever" over IPL-only pixels.

---

## 11. Copy decisions made here (blueprint didn't fully determine) — for owner sign-off at the R1a milestone review

1. **Draw prompt rewritten for the 200+ decision:** "How many times a season does **someone** put 200 on the board? We've drawn 2008–2012 for you. You draw the rest." ("someone," not "a team," kills the per-team-frequency misreading; replaces the obsolete "Average first-innings score" ask). Axis label: "200-run innings per season." Pick-up-the-pen is a pulsing handle at the 2013 column (no hint line); a tapped-while-disabled Reveal answers *"Draw to 2026 first."*
2. **"200-run innings" counts any innings, either side** (matches the 65-in-2026 reveal); the first-innings-only percentages live in the footnote.
3. Pre-drawn anchor chip: "2008–2012: about six a season. That much we'll give you."
4. **Divergence quantified in totals:** "You were {N} two-hundreds too gentle about 2026. The real number: 65."
5. **Two extra reveal branches** beyond the blueprint's two — "early" (high flat decade — "you rang the bell early… the league managed 102") and "over" (overshoot) — plus deterministic first-match precedence (over → early → right → gentle), a d̄-gated "gentle" copy variant for flood-early-then-collapse sketches, and the "right" branch re-anchored from the unverifiable "most people" claim to the verified staggered-breaks pair (sixes ~2018 vs scoreboard 2023). Predicates in CO-2's table.
6. Universal bridge line: "Nineteen seasons. 1,331 matches. Here comes every ball of it."
7. Assembly counter micro-captions (2008 / 2015 / 2023 stops — the 2023 IPL-thickens stop staged a beat before the WPL start so each is one change) and the WPL constellation line, pinned once triggered until the title card: "And a second league assembles — deliberately apart, its own body of light. The WPL: 20,642 deliveries." (one number; 88 matches / four seasons live in C1-6 and the title card's stat line).
8. Title card sub-line: "Every one of them is on this screen right now. They never leave." — and the teaser stat line quotes **316,199** (blueprint §3's 316,388 teaser is overridden by RESOLVED #2).
9. Picker bridge line ("Thirty-odd thousand of these points belong to one team. Yours?") + heading/sub: "Pick your team." / "Its deliveries ignite in its colors — and stay lit through the whole story."; **the equal-styled neutral tile is the skip and sits first, full-width, above the fold**: "No team — show me everything."; single-tap select with ~1.2s auto-advance + a change-anytime toast that persists into C1-1.
10. Ch 1 opening ritual copy (C1-1) naming the sighter in fan language.
11. Ignition-wall caption sequence (axes-teach → dark corner → catches fire → number chip), incl. "The dark corner catches fire" as the scene's operative image; WPL rows sit as a separate shelf above 2026 rather than interleaved.
12. The pivot beat (C1-3): "Of course they score faster. They must be getting out more — right?" — authored to make the flat out-rate land as an answer.
13. Out-rate strip copy: "The lines sit on top of each other. 5.04% then. 4.93% now. All that extra attack — at no extra risk."
14. **Thesis-scope clause final wording:** "…this is a first-ten-balls fact. Later in the innings risk did rise — priced and paid on purpose. Chapter 5 publishes the price list."
15. Fireworks captions, incl. "a six every 21 balls → every 12" and "the six stopped being a specialist's weapon"; **WPL sixes deliberately excluded from the firework columns** (short-columns-next-to-skyscrapers would read as "behind" — the framing rule outranks completeness here) — **and the caption is scoped to match the pixels: "Every IPL six ever hit," with the omission named on screen as deliberate**; step 3's specialist-share claim is carried by the two-tone recolor, not a fourth number.
16. WPL beat single-card copy (two clocks, one breath): "The WPL is already moving — and not along the IPL's track…" with 110.5 + 46.8%-vs-33.9% in the same card.
17. WPL payoff card body + the Maturity Clock plant line: "Remember that clock. We'll come back to it."; headline framing is "climbing **while** the IPL at the same age was still falling" (never "climbing faster than" a decline); the card's verified engine is the league-age RR pair (WPL 8.08→8.54 in the headline; IPL 8.31→7.73 + both year-by-year paths in the dagger), made preattentive by the mini sparkline pair.
18. **Pipeline additions required:** `payoff/ch1.json` v2 adds `fastest_starter` per variant (the blueprint promises the stat on the card; the shipped JSON lacks it) **and rewrites the Neutral headline with the scoped out-rate clause** (cards stay JSON-verbatim — copy changes are pipeline changes); `meta.json` v2 emits `n_players` + per-league `n_matches` so every title-card count traces to an artifact; one spare `attrs.u8` bit re-encodes as the season-top-10-hitter flag for C1-5's recolor.
19. Chapter close line, scoped: "Batters attacked from ball one — and those balls cost them nothing extra. Where risk rose later, they paid it on purpose. That freedom rewired everything: what a good score is, what bowlers do, what a wicket is worth."
20. End-card sandbox tease worded as a promise, not a link ("The field will be yours… Next release."), personalized from the team pick; Ch 2 teased with one line ("A whole species of batter is about to go extinct.") and an explicit `in build` tag.
21. Nav lists all future chapters by title with `soon` tags (titles as commitments, no numbers); resume affordance and change-team entry as specced in §6.
22. localStorage schema names (`ebe.sketch.v1`, `ebe.team.v1`, `ebe.progress.v1`) incl. storing `skipped:true` so Ch 4's no-sketch variant has a signal.

*End of R1a storyboard.*

---

## 12. Revision notes — design-review fixes applied (2026-07-04)

Applied in place from the cognitive-design / honesty audit. Companion patch: blueprint §3 Cold Open beats 1–2, beat 3's counter total, and the teaser line were updated to the RESOLVED decisions (200+ totals draw; 316,199 on-screen), so the blueprint no longer contradicts this document there.

**Must-fix (all applied):**
1. **C1-2 preattentive contradiction** — WPL shelf now renders dimmed one stop through caption steps 2–4 (points present, label visible) and restores at C1-6 where the brighten is the beat; luminance-sweep QA line added.
2. **C1-6 axis collision** — peer-curve panel respecced: same x only (balls 1–30+), new y = strike rate, titled in-frame ("Strike rate, ball by ball"), zero-based fixed-max axis, visibly distinct frame from the out-rate strip; QA + §9 rows added.
3. **CO-2 branch determinism** — first-match order declared (over → early → right → gentle); "gentle" gates its "fifteen years you'd have been right" clause on d̄ ≤ 20 with an authored flood-early-then-collapse variant; gap shading is per-season (|truth − sketch| ≥ 8), never "from the first such season onward"; branch unit tests added to QA.
4. **C1-5 working-memory overload** — step 2 carries one pair (58.7% → 67.3%, fan gloss leads); +56% attempts demoted to the dagger; step 3 gets its own one-change visual (two-tone top-10-vs-everyone recolor via a spare `attrs.u8` bit) and quotes only 18 → 58; 35.9% → 28.1% demoted to the dagger.
5. **C1-8 un-inoculated close** — rewritten to carry the first-ten-balls scope ("those balls cost them nothing extra; where risk rose later, they paid it on purpose"); scope-audit QA line added.
6. **C1-5 pixels-vs-copy** — scene retitled and captioned "Every IPL six ever hit," with the WPL omission named on screen as deliberate; pixels-match-copy QA line added.

**Should-fix (all applied):** C1-2 step 4 is chip-only (ramp comparison dagger-only) · C1-6 caption tightened to ~40 words with WPL-hue color-linked numbers + caption-length lint in QA · C1-6 "its cloud" deleted (shelf-only; constellation flies as one coherent upper→upper block, stated in C1-2) · neutral picker tile is first, full-width, above the fold, identical tile styling · C1-2 destination-first scaffold fades in early in the scrub · CO-3 2023 stop split from the WPL start (one change per beat), WPL caption cut to one number and pinned until the title card · CO-1 prompt says "someone," pulsing pick-up-the-pen handle at 2013 replaces the hint line, disabled Reveal answers "Draw to 2026 first." · C1-4 y-axis pinned (zero-based, fixed 0–10%) with axis-honesty QA covering C1-6 bars and C1-7 sparklines · capped bucket labeled `30+` everywhere · C1-7 WPL card gains the league-age sparkline pair, headline cut to the WPL pair + team pair, IPL pair + year-by-year series in the dagger · "right" branch re-anchored to the verified staggered-breaks pair (2018 sixes vs 2023 scoreboard) · 938-players traceability: `meta.json` v2 emits `n_players`/`n_matches`, title card reads the artifact, harness asserts equality.

**Consider items — dispositions:**
- *Applied:* C1-5 denominator-honesty clause in the dagger; C1-5 two-phase lift/settle choreography + 2023 column label; season-staggered morph flight ("oldest lands first") for neutral-anchor constancy; §0.1 era-band rule reworded (definitions in dagger, labels allowed on charts/captions); picker toast persists into C1-1; C1-5 step 2 leads with the fan gloss ("aerial attempts" stays in the dagger); caption-grammar lints (≤45 words, ≤3 numbers, one change) added to §10; WPL payoff reframed "climbing while the IPL was still falling" + full year-by-year series in dagger + DC-W candor check in snapshot review; C1-4 environment/causal-inoculation line in the footnote sheet; picker bridge line; Neutral card copy resolved as a pipeline change (v2 headline with scope clause, rendered verbatim — §9 row reconciled).
- *Applied partially:* C1-5 balls-bowled baseline strip **not** added — the dagger's denominator clause plus the caption quoting only the per-ball rate covers the honesty without a second encoding fighting the one-message rule.

*End of revision notes.*
