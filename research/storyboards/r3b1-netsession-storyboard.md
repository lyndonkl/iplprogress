# R3b-1 Storyboard — Interlude: The Net Session

**The implementation truth for the Net Session interlude**, the two-dial teaching widget that sits between Chapter 4 (The Rising Tide) and Chapter 5 (What a Ball Is Worth). Authoritative sources: blueprint §3 "Interlude — The Net Session", the §5 engine-validation gate note, and the §2 standing rules; voice-guide.md (binding on every word); CONTRACT.md (the story shell). Register throughout: fans first, orient-then-reveal, one idea per caption, zero em dashes.

This release ships the interlude ONLY. Chapter 5 is a separate later release (R3b-2) and is not built here. The engines it reads (`engines/wp_grid.json`, `engines/re288.json`) already exist, built on the R2 parallel track and passed through the §5 validation gate (calibration ECE 0.0114 against a 0.03 tolerance). This storyboard authors no model; it authors the figure that reads the models.

The one-sentence promise, in the reader's language: *before we tell you what a ball is worth, you feel it, by dragging a chase around under your thumb and watching two honest numbers move.*

---

## 0. Global grammar (Interlude deltas on top of r1a §0, r2a §0, r2b §0, r3a §0)

Everything in the prior storyboards' §0 carries forward unchanged: the encoding grammar (luminance/position never hue; hue is identity only), one-message-per-scene, ≤3 numbers per caption step, the footnote progressive-disclosure chain, persistence discipline, the reduced-motion jump-cut rule, and the banned-terms glossary. The interlude is different in kind from a chapter, so it adds the following.

### 0.1 Encoding grammar — two dials on one lookup grid (cognitive-design)

- **The mechanism, not a chart.** This is a Ciechanowski-style figure: three inputs you drag, two outputs that respond, and (optionally, one click into the widget) the grid the outputs are read off. The reader learns by *manipulation*, not by reading axes. The whole point of placing it here, one scroll before Chapter 5, is that Ch 5 prices deliveries in two currencies (expected runs and win probability), and the reader should have moved both by hand first. No dangling pedagogy, no untaught unit.
- **Two dials, deliberately, and they are NOT redundant.** The teaching spine of the whole widget is the difference between them:
  - **Meter A — "runs you'll probably still get"** reads run-expectancy (`re288.json`). It answers *how much batting have you got left?* and depends on **overs left and wickets in hand ONLY**. It does not care what you are chasing.
  - **Meter B — "how often teams win from here"** reads the win grid (`wp_grid.json`). It answers *can you climb the mountain?* and depends on **all three sliders**, because it needs the mountain (runs needed) as well as the batting you have.
  - This is a genuine, correct teaching moment, not a quirk: **runs needed moves only Meter B.** The affordance below (§3) makes the non-response read as *right*, never as *broken*.
- **Both outputs are plain DOM numbers**, big, with a one-line plain gloss under each. No gauge needlework required to read them; a needle/bar is decoration on top of the number, not the number.
- **The shape is memory; the thin spots are filled in by a stated rule, and shown as such.** The grids are precomputed from 1,331 matches (88 of them WPL). The client interpolates and looks up; it never fits live. But "a lookup, not a guess" is only true where matches actually happened. The win grid is an evidence-weighted rate that is pulled toward a sensible anchor where a spot is thin, and made to move the right way across the board; where a spot has almost no real chases behind it, the cell is imputed by rule, not counted. So the honest claim is scoped: the *shape* of the surface is real memory, and any *thin cell is marked as a filled-in estimate*, never dressed as an observed finding. This is the interlude's headline honesty claim, and it is stated truthfully rather than overclaimed.
- **The minimum-evidence rule applies to BOTH leagues, not just the WPL.** Every surface ships a per-cell `n` (the count of real chases behind that cell), so the cost of showing evidence is zero. One threshold governs both leagues (`evidence_min` = 12 chases for the win grid, 15 innings for the runs grid). A cell at or above threshold is **evidenced** (the meter shows a plain number, an observed read); a cell below threshold is **thin ground** (hatched on the grid, and the meter shows the number visibly demoted as a rule-filled estimate with a plain gloss, never a bare confident number). This is the fix for the trap where the IPL free-play toy would confidently print "36 in 100" on a cell built from a handful of chases while identical thinness in the WPL is honestly hatched. Same rule, same geography, both leagues. The difference is only *how much* thin ground each has and how the reason is worded (§2d, §2f, §5).
- **The grid heat is luminance, not hue.** If the widget shows the win surface as a small heat panel (§2f), a brighter square means teams win more often from there and a dimmer one means less, on the field's existing palette. Team color and the WPL family stay the only hues. Thin-ground cells are hatched in **either** league, never a colour, so a low-evidence spot never reads as a low-win spot.

### 0.2 Register — THE NET SESSION (on-screen copy rules)

The register is a **breather and a hand-off**. Chapters 1 to 4 were a rising argument. This is the coach pulling you aside in the nets: *"Right, before the next bit, have a feel of this."* Warm, plain, unhurried, a little bit of swagger once the orientation is done. Four guardrails:

1. **Orient every dial and every meter in plain words, and put that gloss with the thing before its number can mean anything.** What is "overs left"? What is "runs you'll still get"? The reader must be able to read the machine before any figure is asked to make a point. A widget that starts blank teaches nothing, so the two meters *do* show their default-spot values on load, and that is fine here: **orientation is satisfied by gloss-adjacency.** Each dial and each meter carries its plain gloss right beside it, so a default value sitting under its own gloss ("out of a hundred teams sat exactly where you are, this many went on to win") is an *oriented read*, not a surprising reveal. The rule this scene must never break is the other one: no figure is used to *make an argument* (the era jump, the WPL hole) before the reader has been told, in plain words, what that figure is. Default badges and default meter values are labels, not claims. (This is the reconciliation of the release-blocking voice gate in §2 and §8: gloss-adjacency counts as orientation; a bound number that carries a point still comes after its plain setup.)
2. **The numbers are the game's, not ours.** Every figure the reader sees is bound to `wp_grid.json` / `re288.json` / the pipeline-emitted `interlude.json`. Nothing is hand-typed. When the copy quotes "31 in 100", that literal is a data binding (`0.314`), and QA (§6) traces it to a field.
3. **The WPL is a young league, said as fact, never as a deficit.** When the reader flips to the WPL and hits a hatched cell, the copy is "not enough WPL cricket yet", which is a true statement about 88 matches, and it is on-message: we would rather show a hole than fake a finding. Never "the WPL is behind."
4. **The pause earns Chapter 5.** The close hands directly to "what a ball is worth", naming both currencies, so the return to the moving field lands harder.

### 0.3 The WIDGET exception (not a scroll-scrubbed morph)

The interlude is **slider- and button-driven**, so it deliberately breaks the piece's scroll-scrub grammar:

- It is **not** a controlling morph. There is no `worms` / `frontier` / `tide` layout, no field re-sort, no GSAP scrub of particles. The morph budget is untouched (the interlude spends zero morphs).
- The framing prose scenes around the widget (IN-1, IN-6) are pure-text caption steps over a static dimmed field, exactly like the C4-1 title scene. Per CONTRACT §17.4 they do **not** adopt the mobile read-then-watch caption fade (there is nothing to "watch" behind pure text).
- The widget scene (IN-2..IN-5) is one **pinned interactive figure**. The reader is not scrubbing a timeline; they are dragging controls. So the widget does not use `captionReveal`; it uses ordinary responsive layout and lives in the sticky viewport for as long as the reader wants it.

### 0.4 Demand-mode — the resting starfield, loop STOPPED

- Entering the interlude, the field **settles to a resting starfield and the render loop STOPS** (blueprint: "dimmed means paused, not idling"). Concretely: `fieldState = { layout: 'free', dim: ~0.18, teamIgnite: true }`, held. Per the shell's demand-mode contract (CONTRACT §1: "holding = zero renders"), once that state settles the GPU is idle. **No new layout is invented** (CONTRACT §3), the starfield is the existing `free` scatter under a heavy dim, with the reader's franchise still faintly lit for identity.
- **The widget never invalidates the field.** Dragging a slider updates DOM numbers and the widget's own small canvas/heat only; it must not touch `field.*` or request a field frame. The starfield stays frozen behind the glass while the reader plays. This is the invariant that makes the interlude thermally free on a phone during a long dwell.
- The entry is a settle, not a set piece: Ch 4's close (C4-12) already exhales `tide → free`; the interlude simply lands that `free` state dimmed. The nav's set-piece dimming does not engage (no layout change, no reveal scrub).

### 0.5 Persistence (localStorage) — reads one existing key, writes none new

- Reads **`ebe.team.v1`** only, to keep the reader's franchise faintly lit in the starfield (identity continuity). The widget's numbers are league-and-era facts, not team facts, so there is **no team-variant copy** and no payoff card here.
- Writes `ebe.progress.v1` via the shell on scene change (unchanged). **No new store, no new key.** The widget's control state (slider positions, WPL toggle, active preset) is ephemeral component state and is deliberately not persisted; a returning reader gets the clean default spot, not a stale one.
- No content gates on any store existing. Deep-linking to `#interlude` always works.

### 0.6 Caption / layout rules (binding)

- **Captions and labels never cover the widget.** The widget owns the center of the viewport. On desktop the framing caption (IN-1, IN-6) sits top-left, clear of the nav (☰, top-right). The widget's own control labels sit with their controls, never floating over the meters.
- **Mobile: the widget is thumb-usable, fits one viewport, and stacks cleanly** (full spec §2b). The two meters sit **above** the dials; presets are a full-width wrapping button group; the WPL toggle and the era toggle are each their own full-width switch. No horizontal scrolling, tap targets ≥44px, no hover-only content (voice + CONTRACT invariant). The read-then-watch caption mechanism is not used (it is for scrubbed morphs); the widget is simply responsive.
- **The changing number must never hide under the thumb (binding).** The core teaching loop is "move a dial, watch a number", so the number being changed must stay visible while the thumb is on the slider. Two guarantees, both required: (a) the widget is sized to **fit within 100dvh** on a small phone (compact meter cards, condensed preset group, grid heat collapsed) so nothing essential scrolls out of view; and (b) whenever any slider is being dragged, a slim **live readout of both meters pins to the top of the widget's sticky viewport**, so the runs-needed slider (the lowest control) can be moved with both meters still in sight above the hand. Meters-above-dials plus the pinned readout together make the loop hold on the phones the piece targets.
- **No hover-only content, anywhere.** Every meter value, every preset result, every mask state is present on load or on tap/drag, never on hover, and reachable by keyboard.

### 0.7 Banned terms + stage names (glossary rule)

No statistical term of art appears in main flow. Terms banned on screen (inheriting all prior chapters' lists, plus this interlude's): *win probability, WP, WPA, expected runs, run expectancy, RE, RE288, required run rate, RRR, base rate, lookup grid, calibration, empirical Bayes, shrinkage, isotonic, monotone, leverage index, model, posterior, sample size, n, D/L, DLS, points, percentage-points.* "Points" is banned specifically because the reader was taught the win figure in the "in 100" frame; a win gap is always said as "about eight more in a hundred", never "eight points".

| On screen (fan language) | Technical name (footnote / QA only) |
|---|---|
| "how often teams win from here" / "out of a hundred teams in this spot" | win probability, P(chase win), from `wp_grid.second_innings` |
| "runs you'll probably still get" / "runs a team usually still scores from here" | run-expectancy, runs-to-come, from `re288.json` |
| "overs left" | balls/overs remaining → grid `overs_left` index |
| "wickets in hand" | wickets remaining → grid `wickets_in_hand` index |
| "runs needed" / "how far from the target" | runs to win → drives the required-rate bucket |
| "how hard the chase is" / "the ask" | required run rate, `rrr_bucket` |
| "the same chase, two different times" | era-band split of the second-innings grid |
| "not enough WPL cricket yet" | minimum-evidence mask (`masked=1`, cell `n` below the WPL threshold) |
| "not many real chases from this exact spot yet, so this one is filled in" / "thin ground" | minimum-evidence flag on an IPL free-play cell (`n < evidence_min`, imputed by rule) |
| "read from real matches" / "the shape is memory; the thin spots say so" | precomputed grid, no live model, thin cells rule-imputed and flagged |
| "1,331 real matches" | the corpus behind the win grid |

### 0.8 Reduced motion (nothing is lost)

The widget is slider- and button-driven, so **reduced-motion loses nothing**: there is no morph to jump-cut past. Under `prefers-reduced-motion` the field renders the dimmed `free` starfield as a still (it is already still), the framing captions are persistent (never faded), the meters are plain DOM numbers, and the presets are ordinary keyboard-accessible buttons. Every teaching beat that a mouse reader gets by dragging, a keyboard reader gets by tabbing to a slider and pressing an arrow key, and a screen-reader reader gets by the live-region announcement of the meter values (§3). This is the one scene in the piece where the accessible path and the primary path are the same path.

**The one place this needs care is the runs-needed non-response.** When a sighted reader drags runs needed, Meter A visibly does not move, and the on-screen affordance note (§2d) tells them why. A screen-reader reader hears only Meter B change and would otherwise hear silence from Meter A, which reads as broken, not as correct. So on any runs-needed change the live region must announce the affordance too, e.g. *"win chance updated to 34 in 100; runs meter reads your batting, not the target, so it holds at about 89."* The non-response is then explained for the SR reader in the same breath a sighted reader gets the visual note. Without this, §0's claim that here the accessible path and the primary path are the same path would not actually hold for the widget's cleverest beat.

---

## 1. THE INTERLUDE — beat map

The interlude is one pause and one machine, in six beats. It is not a chapter and carries no beat budget, no hero metric, no controlling morph, no team payoff. Entry: Ch 4's close hands off on the `free` field (already exhaled from the tide). Exit: hand-off to Chapter 5 (in-build), then on into the existing end card / sandbox for this release.

```
IN-1  The pause              framing prose: why we stop here (pure text over the resting starfield)
IN-2  Meet the machine       orient the three dials + the two meters, in plain words, before any number
IN-3  Feel it move           three guided drags: the clock, spend a wicket, wickets early / ask late
IN-4  The presets            the message for the 85% who never drag: both currencies + the same-chase, two-eras pair
IN-5  The WPL toggle         flip to the women's game + the "not enough WPL cricket yet" mask
IN-6  Close                  two dials, one scoreboard; hand off to "what a ball is worth"
```

The widget itself (a single pinned figure) is live from IN-2 through IN-5; IN-3/IN-4/IN-5 are caption beats *about* the same figure, guiding the reader's hands. IN-1 and IN-6 are prose bookends.

---

### Scene IN-1 — The pause (framing prose: why we stop here)

**Purpose (one point):** tell the reader why the argument stops for a moment, and what they are about to get their hands on, before the machine appears.

**Particle field:** the resting starfield. `free`, dimmed to ~0.18, loop stopped. The reader's team stays faintly lit.

**Annotation plane (three caption steps, top-left, persistent, no read-then-watch):**

1. > **The Net Session**

2. > For four chapters the game kept changing under you. Batters, bowlers, and then the ground itself. In a moment we start pricing all of it, working out what a single ball is actually worth.

3. > Before that, have a feel of it yourself. Two dials, one scoreboard. How many runs a team usually still gets from a spot, and how often teams win from it. Give it a drag. *(scroll cue)*

*(Register note: step 2 hands off from Ch 4 and names what is coming, so a deep-entry arrival gets the setup self-contained. Step 3 names both dials in plain words and issues the invitation to touch, with zero numbers on the pause scene. No em dashes; "you" throughout; the coach-in-the-nets voice.)*

**Footnote:** none on the pause (the widget scene carries the "how we worked this out" sheet).

---

### Scene IN-2 — Meet the machine (orient the dials, then the meters, before any number)

**Purpose (one point):** the reader can read every control and every output in plain language before being asked to act or being shown anything surprising. This is the orient half of orient-then-reveal, and it is a whole scene because the widget has five moving parts and voice-rule 1 is non-negotiable.

**Particle field:** resting starfield behind the widget glass, loop stopped.

**The widget appears, in its resting default state** (§3 for exact state). Default spot, chosen to be legible and mid-drama, not a corner: **10 overs left, 6 wickets in hand, 90 runs needed** (a real "game in the balance" spot). The two meters read that spot from the best-evidenced all-history grids and show their numbers immediately (a machine that starts blank teaches nothing). This default spot is well-evidenced (124 real chases behind Meter B's cell), so both meters open on plain observed numbers, not a flagged estimate; per §0.2 the numbers are oriented reads because each sits under its own plain gloss.

**Annotation plane / widget labels (orient copy, plain, each control glossed once):**

The three sliders, each with its plain gloss shown beside it:

- > **Overs left.** How much batting time is left on the clock.
- > **Wickets in hand.** How many batters you have still to come.
- > **Runs needed.** How far you are from the target.

The two meters, each with its plain gloss shown beneath the big number:

- > **Runs you'll probably still get** \
  > *From this much batting left, this is how many more runs a team usually scores.*
- > **How often teams win from here** \
  > *Out of a hundred teams sat exactly where you are, this many went on to win.*

**Caption steps (one idea each, top-left, persistent):**

1. > This is a chase, frozen. Three dials set the scoreboard: time left, batting left, and how far you have to go.
2. > Two meters read it back. One tells you the runs a team usually still gets from here. The other tells you how often teams win from here, out of a hundred.
3. > Both are memory. Every number is read from real matches. Where the matches run thin, it says so instead of guessing. Drag a dial and watch them answer. *(hands off to IN-3)*

**Reduced motion / keyboard:** the sliders are native range inputs (label + value + arrow-key steppable); the meters are a polite live region so a screen reader hears "runs you'll still get, about 89; teams win about 36 in a hundred" when a value changes. When runs needed is the dial being moved, the announcement also states that the runs meter holds because it reads your batting, not the target (§2d, §0.8), so the non-response reads as correct. Nothing here needs a pointer.

**Footnote (ⓘ how we worked this out) — the interlude's single sheet, `netsession`:** see §4. Reachable from IN-2 and held for the rest of the interlude.

#### 2a. Widget layout — desktop

```
┌───────────────────────────────── the Net Session ─────────────────────────────────┐
│  caption (top-left, clear of ☰)                                          ☰ nav     │
│                                                                                    │
│   ┌──── the dials ────────────┐        ┌──── the meters ─────────────────────┐     │
│   │  Overs left        [10]   │        │   Runs you'll probably still get     │     │
│   │  ●───────────────○──       │        │            ~89                        │     │
│   │  Wickets in hand    [6]   │        │   from this much batting left        │     │
│   │  ●──────────○───────       │        │                                      │     │
│   │  Runs needed       [90]   │        │   How often teams win from here      │     │
│   │  ●────────○─────────       │        │            36 in 100                 │     │
│   └───────────────────────────┘        │   teams sat exactly here             │     │
│                                         └──────────────────────────────────────┘     │
│   [ Dhoni chase finish ]   [ Nine an over, ten overs to go ]                        │
│                                                                                    │
│   The same chase, then and now:   [ 2008 to 2012 ]   [ 2023 to 2026 ]  (own row)   │
│                                                                                    │
│   ( WPL  ◯── )  the women's game, same two dials                                   │
└────────────────────────────────────────────────────────────────────────────────────┘
```

Dials left, meters right, presets across the bottom, WPL toggle bottom-left. The (optional) grid heat panel (§2f) tucks under the meters or behind a "show the grid" disclosure so it never crowds the two headline numbers.

#### 2b. Widget layout — mobile (thumb-usable, stacked)

Single column, in this order, full-width, generous 44px+ touch targets:

1. Meter A (runs you'll still get) — big number + gloss.
2. Meter B (win from here) — big number + gloss.
3. Overs left slider.
4. Wickets in hand slider.
5. Runs needed slider.
6. Presets: full-width wrapping button group ("Dhoni chase finish", "Nine an over, ten overs to go").
7. **The era contrast is its own full-width control**, not nested in the preset row: a labelled two-state switch **[ 2008 to 2012 | 2023 to 2026 ]** under its own line "the same chase, then and now". It sits at full width and high discoverability because it drives the interlude's climax, and the ~85% who never drag must not have to hunt for it (§IN-4). The default-visible era caption (IN-4) carries the payoff even for a reader who never touches this switch.
8. WPL toggle: one full-width switch.

Meters go **above** the dials on mobile so that when a thumb is on a slider at the bottom of the screen, the numbers it is changing are still visible above the thumb (they are not hidden under the hand). Two viewport guarantees are binding (§0.6): the whole widget is sized to **fit within 100dvh** on a small phone (compact meter cards, condensed preset group, grid heat collapsed by default), *and* whenever a slider is being dragged a slim **live readout of both meters pins to the top** of the sticky viewport, so moving the lowest slider (runs needed) never scrolls the changing numbers out of sight. The widget is `position: sticky; top: 0` inside its section; no horizontal scroll.

#### 2c. The three sliders (ranges, steps, exact meaning) — see §3 for index math

- **Overs left:** integer 1..20, step 1. (20 = start of the innings, 1 = last over.)
- **Wickets in hand:** integer 1..10, step 1.
- **Runs needed:** integer 1..250, step 1. Drives the "ask" (runs needed ÷ overs left) that Meter B buckets.

#### 2d. The two meters (what they read, what they show)

- **Meter A — runs you'll probably still get.** Reads `re288`. Shows an integer ("~89"). Driven by overs-left + wickets-in-hand only.
- **Meter B — how often teams win from here.** Reads `wp_grid.second_innings`. Shows "N in 100" (never "N%" and never "points"; the reader was taught the "in 100" frame and it stays locked, §0.7). Driven by all three sliders.
- **The minimum-evidence flag (binding, both leagues, §0.1).** Before either meter prints a number it checks the current cell's `n`. If the cell is **evidenced** (`n ≥ evidence_min`: 12 chases for win, 15 innings for runs) the meter shows a plain number, an observed read. If the cell is **thin** (`n < evidence_min`) the meter must not print a bare confident number: the value renders visibly demoted (faint/italic) with a one-line plain gloss, IPL free-play wording *"not many real chases from this exact spot yet, so this is filled in by rule, not counted"*, and the grid heat square (if shown) hatches. The WPL uses the stronger, on-message form of the same rule at the same threshold (no number, "not enough WPL cricket yet", §2d/§5) because most WPL cells are thin and the hole is that beat's whole point; but in *neither* league is a thin cell ever presented as an observed finding. The default spot and mainstream chases are evidenced, so the toy's common path shows real numbers; only when the reader drags into a sparse corner do they meet the flag.
- **The runs-needed affordance (binding, cognitive-design):** when the reader drags *runs needed*, Meter A must visibly NOT change, and this must read as correct. So while runs-needed is the active control, Meter A shows a quiet inline note: *"This meter reads your batting, not the target."* No number flickers, no error state. The reader learns the true thing: how much you still score is about how much bat you have left; the ask only changes whether it is enough. (This is the widget's cleverest single teaching beat and it is free.) **Accessibility parity (binding):** the same non-response must be announced, not just shown. On any runs-needed change the live region says both that Meter B updated and that Meter A holds *because* it reads your batting, not the target (e.g. *"win chance now 34 in 100; runs meter holds at about 89, it reads your batting, not the target"*), so a keyboard or screen-reader reader hears the silence explained rather than hearing a broken meter (§0.8).

#### 2e. How each meter reads the grid (implementation truth) — see §3

Both meters are pure array lookups into JSON that already ships. Exact indices, defaults, the required-rate bucketing, and the WPL-mask branch are specified in §3 so the builder writes no arithmetic beyond an index and a bucket.

#### 2f. The grid heat panel (optional, one disclosure deep)

Behind a "show the grid" toggle (collapsed by default, especially on mobile): a small 20×10 heat of the win surface at the current required-rate bucket (overs-left across, wickets-in-hand down), a brighter square meaning teams win more often from there, with the current cell ringed. It makes "you are reading one square of a big remembered table" literal. It is optional for v1; if cut for scope it becomes a footnote figure. Thin-ground cells render **hatched in either league** (same `evidence_min` rule as the meters, §0.1), so a low-evidence spot never masquerades as a low-win (dark) cell. On the IPL surface this shows the reader that the well-travelled middle of a chase is solid ground and the extreme corners are thin; on the WPL surface most of the grid is hatched, which is itself the honest picture of a four-season league.

---

### Scene IN-3 — Feel it move (three guided drags)

**Purpose (one point per drag):** hand the reader three specific manipulations that each reveal one true thing about how a chase works, so that even a reader who only follows the prompts leaves with the mechanism, not just the meters.

**Particle field:** resting starfield, loop stopped. Widget live.

**Caption steps (each is an instruction + the reveal it produces; ≤3 numbers; the reader's own drag supplies the motion):**

1. **The clock.** > Slide overs left down. Both meters fall together. Less time means fewer runs and fewer wins. That is the clock, and it never stops.
2. **Spend a wicket.** > Now knock off a wicket early, with plenty of overs left. Watch the win meter drop a long way. Early on, wickets are the whole game.
3. **The ask takes over.** > Drag overs left down to two, then move runs needed. Now the wicket barely matters and the ask is everything. Late in a chase it is not how many are out, it is how many you need.

*(Register note: beat 2 and beat 3 together teach the single most important shape in win probability, that wickets dominate early and the ask dominates late, without ever saying "win probability" or "required rate". The full "why" is one click down, §4. The reader feels it before they can name it.)*

**Reduced motion / keyboard:** each instruction works by arrow-keying the named slider; the reveal is the announced meter change. A reader who cannot or will not drag can still be walked through all three with the keyboard, and the caption tells them which dial to move. In beat 3, when they arrow runs needed, the live region announces that the win meter moved and the runs meter held because it reads their batting, not the target (§0.8, §2d), so the SR reader learns "the ask takes over" from the same non-response a sighted reader sees.

---

### Scene IN-4 — The presets (the message for the ~85% who never drag)

**Purpose (one point):** carry the entire lesson to the reader who never touches a slider, by pre-loading two real, dramatic spots that each quote **both currencies**, and by landing the piece's designed punch as a **default-visible caption**: **the same scoreboard, two different eras, two different truths.**

**Particle field:** resting starfield, loop stopped. Widget live; pressing a preset sets the three sliders and updates both meters.

Presets are **pipeline-emitted, never hand-authored** (same discipline as payoff cards): `interlude.json` carries each preset's exact `{label, overs_left, wickets, runs_needed, era}` state and its two looked-up meter values, and the snapshot harness asserts each is present, non-degenerate, and (for the chase presets) that the bound state **actually exists in the second-innings grid**. The copy below is the **template**; the bracketed values are bindings.

**Preset 1 — a famous Dhoni chase finish (both currencies), pipeline-verified.** The label and scoreboard are bound to a real, corpus-verified Dhoni *chase* the pipeline selects (not the 2011 final, which was a defend, see §9.2). It maps to a genuine second-innings state so the widget stays two-currency and chase-shaped:

> **{label}** *(e.g. a famous Dhoni finish, bound to its real over-and-wickets spot)* \
> From this exact spot, teams usually get **{expRuns}** more runs and win **{win} in 100**.

**Preset 2 — the ordinary hard chase (both currencies):**

> **Nine an over, ten overs to go.** \
> A proper scrap. From here, teams usually get **{expRuns}** more runs and win **{win} in 100**.

**The climax is a default-visible caption, not a hidden toggle.** The same-chase, two-eras payoff is the interlude's punch and its audience is the ~85% who never drag, so it renders as **prose the passive reader sees without touching anything**, both eras' bound numbers in the caption. The era switch (§2b, its own full-width control) is kept only as optional *"feel it yourself"* reinforcement, never the sole path to the payoff. The caption is two steps so each stays within the ≤3-numbers rule and the **win jump leads** (the runs pair is quiet corroboration, not a co-headline):

1. > **The same chase, then and now.** Needing nine an over with ten overs left. Back in **2008 to 2012**, that chase came off about **23 in 100**. The very same scoreboard now, **2023 to 2026**, comes off about **31**. About **eight more** wins in a hundred, and not a thing on the board changed.
2. > Teams even score a touch more from there now, about **89** where it used to be about **78**. The chase just got easier, and the numbers remember.

*(Register note: the win jump is the headline and carries the punch; the runs pair is demoted to a quiet second line as corroboration, not a co-headline (one idea, one number each). Win is always said "in 100", never "%" or "points"; dates are spelled out. The era numbers bind to the well-sampled era anchor window, not a single noisy grid cell, see §3. The certainty is deliberately hedged to "about" because the anchor's count is legal-ball states, not independent matches, and the match-level gap is less certain than the raw count implies (§4 para 5, §9.1): the pipeline must confirm the gap survives at the match level, with a distinct-match count and a match-clustered interval, before this ships as "the point". The direction, chases got easier, is robust; the copy claims only that. Zero em dashes; the swagger lives in "the numbers remember".)*

**Reduced motion / keyboard:** presets are ordinary buttons; the era switch is a two-button segmented control at full width. Pressing any of them announces the new spot and both meter values in the live region; if the landed cell is thin, the announcement says so rather than reading a filled-in number as a fact. The default-visible era caption means no reader has to find or press the switch to get the payoff. No motion, no hover, fully keyboard-reachable.

---

### Scene IN-5 — The WPL toggle + the minimum-evidence mask

**Purpose (one point):** the same two dials read the women's game honestly, which means showing where there is not yet enough of it, in plain words, rather than smoothing a hole into a finding.

**Particle field:** resting starfield, loop stopped. Widget live; flipping the toggle switches both meters (and the grid heat, if shown) to the WPL surfaces.

**Behaviour:**

- The toggle switches Meter A to `re288` surface `wpl 2023-2026` and Meter B to `wp_grid.second_innings` surface `wpl 2023-2026`, at the same slider state.
- **The default spot is itself masked in the WPL** (`wpl` win cell at 10 overs, 6 in hand, nine-an-over has n=10, below the threshold of 12), so **the very first WPL read the reader gets is a mask, not a number.** That is why caption 1 must orient the young league *in the same breath* as the first mask (below): the reader meets the hole already knowing why it is there, never as "the widget broke for the women's game".
- **If the current cell is masked** (`re288` cell `n < 15`, or `wp_grid` WPL cell `n < 12`, both flagged `masked=1` in the artifacts), the meter does not show a number. It shows the mask state:
  > **Not enough WPL cricket yet.**
  and (if the grid heat is open) the corresponding squares render hatched, not dark. Most of the WPL grid is masked (1,725 of 2,000 win cells; 155 of 200 run cells), which is itself the honest picture.
- **If the current cell is evidenced**, the meter shows the WPL number normally.
- This is the **same minimum-evidence rule** that flags thin IPL free-play cells (§0.1, §2d), at the same thresholds; the WPL just meets it far more often, and this beat uses its strong "no number" form because the hole is the whole point.

**Caption steps:**

1. > Flip it to the WPL, the same two dials on the women's game. It has played 88 matches, not 1,331, so at a spot like this one there is not enough of it yet, and the meter tells you so instead of guessing.
2. > Wherever the real matches run thin, the number stays hidden and the grid goes hatched. We would rather show you a hole than dress a guess up as a finding. As the WPL plays more, more of it fills in.

*(Register note: "88 matches, not 1,331" is the two-clocks honesty, stated as a fact about a young league, never as "behind". Because the default read is masked, caption 1 does the orienting in the same breath as the first mask, so the honest hole lands as designed, not as a broken widget. The mask is on-message: the empty squares are the story of a four-season league, not a defect.)*

**Reduced motion / keyboard:** the toggle is a native switch; the masked state is text, announced in the live region ("not enough WPL cricket yet") so a screen-reader reader gets the same honesty a sighted reader gets from the hatch.

---

### Scene IN-6 — Close (two dials, one scoreboard) + hand-off to Chapter 5

**Purpose (one point):** name what the reader just learned and spend it immediately, by pointing at Chapter 5, so the pause pays off and the return to the moving field lands.

**Particle field:** resting starfield begins to un-dim slightly on the last step (still no morph, still demand-mode; a luminance lerp back toward full, foreshadowing the field's return in Ch 5). The widget fades out as the caption lands.

**Annotation plane (two caption steps, top-left, persistent):**

1. > That is the machine. Two dials, one scoreboard, and every number a memory of a real match.
2. > Now we spend it. Next up, what a single ball is actually worth, priced in both: the runs it is likely to cost or make, and the win it swings. *(hands off to Chapter 5, in-build)*

**Teasers (on screen, both bound):**

> `The same chase is a win about eight more times in a hundred now than in 2008 to 2012.` \
> `Every number here is read from 1,331 real matches. Where the matches run thin, it says so.`

**Footnote:** the `netsession` sheet remains reachable from the close.

---

## 2. On-screen copy — consolidated single source (for QA + voice pass)

Every string a reader sees, in order, so the copy can be voice-checked and diffed against the bound values in one place. Bracketed `{…}` are data bindings; everything else is authored literal. (Bodies live in the scenes above; this is the flat index.)

- IN-1: "The Net Session" / the two framing paragraphs / "Give it a drag."
- IN-2: dial glosses (overs left / wickets in hand / runs needed); meter glosses (runs you'll probably still get / how often teams win from here); three orient captions; the runs-needed affordance note "This meter reads your batting, not the target."; the thin-ground flag "not many real chases from this exact spot yet, so this is filled in by rule, not counted."
- IN-3: "The clock…"; "Spend a wicket…"; "The ask takes over…".
- IN-4: preset labels (`{label}` bound Dhoni chase finish, "Nine an over, ten overs to go"); both-currencies templates with `{expRuns}` / `{win} in 100`; the default-visible era caption with `{23 in 100}` / `{31 in 100}` / "about eight more" / `{78}` / `{89}` (all bound, §6); tie line "The chase just got easier, and the numbers remember."; era switch labels "2008 to 2012 | 2023 to 2026".
- IN-5: "Flip it to the WPL…"; "…88 matches, not 1,331…"; the mask state "Not enough WPL cricket yet."
- IN-6: "That is the machine…"; "Now we spend it…"; two bound teasers ("…about eight more times in a hundred…"; "…read from 1,331 real matches. Where the matches run thin, it says so.").

**Voice pass gate (blocking):** zero em dashes across all of the above; every meter and every dial glossed in plain words beside its first number (gloss-adjacency, §0.2); one idea per caption and one number per idea; win said as "in 100" everywhere with **no "%" and no "points"** in reader copy; on-screen dates spelled out ("2008 to 2012", never an en-dash); no thin or rule-imputed cell presented as an observed finding in either league; every literal number traces to §6. Run the slop/voice check on this block before build.

---

## 3. The widget spec (implementation truth)

The builder writes an index and a bucket, nothing more. All arithmetic is stated here.

**Controls (component state, not persisted):**

| Control | Range / values | Default | Feeds |
|---|---|---|---|
| Overs left `oL` | int 1..20 | 10 | Meter A, Meter B |
| Wickets in hand `w` | int 1..10 | 6 | Meter A, Meter B |
| Runs needed `R` | int 1..250 | 90 | Meter B only |
| League | IPL / WPL | IPL | which surface both meters read |
| Active preset | none / p1 (Dhoni chase) / p2 (nine an over) | none | sets the three sliders + era |
| Era switch | 2008 to 2012 / 2023 to 2026 | (drives the default-visible era caption) | its own full-width control; flips the same-chase headline between eras; does not gate the payoff (IN-4) |

**Meter A — runs you'll probably still get (reads `re288.json`):**

- `re288.state`: `o` = overs bowled 0..19, `w` = wickets fallen 0..9, `value` = `re[o][w]` = expected first-innings runs still to come.
- Index map from the sliders: `o = 20 - oL` (overs left 20 → o=0 at the innings start; overs left 1 → o=19 at the last over); `wFallen = 10 - w`.
- IPL default surface: **`ipl 2023-2026`** unless a pooled all-era surface is added (open call §9; recommended). Value = `surfaces[surface].re[20 - oL][10 - w]`, rounded to an integer.
- **Evidence gate (both leagues, §0.1):** every `re288` surface ships a per-cell `n`. Before printing, check `surfaces[surface].n[20 - oL][10 - w]`. If `n < 15` (`evidence_min` for runs) the cell is thin: IPL free-play shows the value demoted with the "filled in by rule, not counted" gloss (§2d); the WPL shows the mask state (`masked[...] === 1`, the strong form). A thin runs cell is never printed as a bare observed number in either league.

**Meter B — how often teams win from here (reads `wp_grid.json` → `second_innings`):**

- `second_innings.state`: `overs_left` 1..20 → index `oL - 1`; `wickets_in_hand` 1..10 → index `w - 1`; `rrr_bucket` 0..9 via `rrr_edges = [6,7,8,9,10,11,12,15,20]`; `value = wp[overs_left-1][wickets_in_hand-1][rrr_bucket] = P(chase win)`.
- Required rate: `rrr = R / oL`. Bucket = number of edges `rrr` meets or exceeds → `bucket = count(e in rrr_edges where rrr >= e)` (equivalently `bisect_right(rrr_edges, rrr)`; e.g. rrr 9.5 → 4, rrr 10.0 → 5, rrr 5.5 → 0).
- IPL free-play surface: **`ipl pooled`** (best-evidenced, all history). Value = `surfaces['ipl pooled'].wp[oL-1][w-1][bucket]`, shown as `round(value*100)` "in 100". At the default spot (`wp[9][5][4]`) this is **0.3568 → 36 in 100** (the storyboard's earlier "46" was stale; bind to the cell, do not hand-type).
- **Evidence gate (both leagues, binding, §0.1).** The `ipl pooled` surface ships a per-cell `n`, and it is thin over much of the grid (median cell n≈9; 730/2000 cells have n=0; 1049/2000 (≈53%) have n<12, the same thinness the WPL masks). So before printing, check `surfaces[surface].n[oL-1][w-1][bucket]`. If `n < 12` (`evidence_min` for win) the cell is thin ground: IPL free-play shows the value demoted with the "not many real chases from this exact spot yet, filled in by rule" gloss (§2d) and the grid square hatches; the WPL shows the mask state (`masked[...] === 1`, no number). The default and mainstream chases are evidenced (default `n[9][5][4] = 124`), so the toy's common path prints real numbers; only sparse corners show the flag. A thin win cell is never printed as a bare confident "N in 100" in either league. This is the fix for the honesty asymmetry where the IPL toy printed shrunk cells as fact while the WPL hatched identical thinness.
- WPL: surface `wpl 2023-2026`. If `surfaces['wpl 2023-2026'].masked[oL-1][w-1][bucket] === 1`, render the mask state. (`wpl_mask_min_n = 12`.)

**The same-chase, two-eras contrast (IN-4 preset 2 era toggle) — the ONE place the interlude splits by era, and it does NOT read a single grid cell:**

- The two headline **win** figures bind to `wp_grid.calibration.era_anchor` (the well-sampled window "chase needing ≥9 an over with ~60 balls left"): `ipl_2008_2012.win_rate = 0.2323` → on screen **about 23 in 100**; `ipl_2023_2026.win_rate = 0.314` → **about 31 in 100**. These pool a whole window rather than a lone noisy cell. **Caveat (binding):** the emitted counts (934 and 1242) are legal-ball *states* inside a ~7-ball window (balls_left 57..63), not independent matches, so up to ~7 near-identical states can come from one chase. The effective match-level sample is much smaller, and a rough clustering deflation drops the gap's significance from very strong (states-as-independent) to borderline. So the pipeline must **emit a distinct-match count for each era and a match-clustered uncertainty interval on the gap**, and the gap must clear significance **at the match level** before this ships as the climax (§9.1). The copy is hedged to "about" and the claim is only directional (chases got easier) for exactly this reason.
- The two headline **runs** figures bind to `re288` era-band cells at the anchor's representative spot (`o=10, wFallen=4` = ten overs left, six in hand): `ipl 2008-2010`.re[10][4] = **77.7 → ~78**; `ipl 2023-2026`.re[10][4] = **89.0 → ~89**. (Emitted into `interlude.json` so the copy binds to a field, not a hand read.) These are the quiet corroboration line in IN-4, not the headline.
- Pressing the switch sets the sliders to `oL=10, w=6, R=90` (rrr = 9.0, bucket 4) so the reader sees where on the dials this chase sits, and flips the two headline numbers between the eras. The live pooled meter is a secondary "feel"; the authoritative era numbers are the bound window aggregates above. **The window is fixed on interpretable, pre-registered grounds (rrr ≥ 9, ~60 balls left); it must never be reshaped to reproduce a target headline** (§9.1). The one-line honesty note (window aggregate vs single cell; ball-states vs matches) lives in §4 para 5.

**Demand-mode invariant (blocking):** no control handler may call any `field.*` method or request a frame. The field stays the held dimmed `free` state; the widget re-renders only its own DOM/canvas.

---

## 4. Footnote layer (`netsession` sheet, plain voice)

One sheet, reachable from IN-2 onward, `SceneDef.footnote = 'netsession'`, added to `lib/story/footnotes.ts`. Plain voice, names the stat terms but glosses them in the same breath. Paragraphs, in order:

1. **Where the numbers come from, and where they are filled in.** Every figure in the net session is looked up from a table built once, from the ball-by-ball record of 1,331 matches (88 of them WPL). Nothing is fitted live in your browser. But "read from real matches" is only the whole truth where real matches piled up. The "how often teams win" table starts from the observed win rate at each match state (overs left, wickets in hand, and how hard the ask is), then does two honest repairs: where a spot has few real chases behind it, its value is pulled toward the broader pattern for spots like it (so a barely-seen corner borrows from its neighbours instead of swinging wildly), and each row is nudged so the numbers move the sensible way (a harder ask never comes out easier). Where a spot has almost no real chases at all, the cell is filled in by that rule, not counted from matches, and the widget marks it as thin ground rather than printing it as a fact (§0.1). So the honest headline is: the *shape* of the table is real memory; the thin cells are filled in by a stated rule and shown as such. The "runs you'll still get" table is the average runs a first innings still scored from each over-and-wickets state, repaired the same way and masked the same way where the innings are too few. *(Technical: EB-shrinkage toward the pooled cell, then toward the coarse over-by-rate marginal; each over-slice made jointly monotone in the ask by PAVA; the same per-cell evidence threshold, 12 chases / 15 innings, that masks the WPL also flags thin IPL cells.)*

2. **How honest the win numbers are (the calibration plot).** *(FootnoteFigure, data-only.)* We checked the table against reality: group every real chase by the win chance the table gave it, then see how often those groups actually won. The dots sit on the diagonal (a table that says "30 in 100" is right about 30 times in 100). Average gap between the chance given and what actually happened: about 1 in 100. The figure plots `wp_grid.calibration.bins` (10 deciles, predicted vs actual, the diagonal reference), from `calibration.n = 144,136` chase states.

3. **Why a wicket matters most early, and the ask matters most late.** Early in a chase there are overs to spare, so the thing that decides the game is whether you keep batters to use them; lose a couple early and the win number craters. Late in a chase there is no time left to save, so the only thing that moves the number is how many you still need. That is why dragging wickets swings the meter hard at the top of a chase and barely at all at the death, and runs-needed does the opposite. The two tables encode exactly that shape.

4. **Rain-hit and tied games.** The win table is built only from chases that were played to a full 20-over target, so rain-shortened targets (which change the maths mid-game) are left out rather than fudged. The handful of matches decided by a super over count by who actually advanced. No-result games are dropped. (Technical: `target.overs == 20`, non-D/L, ties by `outcome.eliminator`, no-results excluded.)

5. **The same-chase, two-eras number, and how sure we are of it.** When we say the same chase came off about 23 in 100 in 2008 to 2012 and about 31 in 100 now, that is the win rate over *every* chase at least that hard in each era, not one square of the grid, so it does not jump around the way a single square would. Two honesty notes. First, the count behind each era (934 and 1242) is legal-*ball* states inside a roughly ten-ball window, not separate matches: a single chase can contribute up to about seven near-identical states, so the true number of distinct matches is a good deal smaller than those counts suggest. Second, because of that clustering, an eight-in-a-hundred gap on this base is less nailed-down than the raw counts imply. So we quote the era numbers as "about", we report a distinct-match count and a match-clustered range on the gap, and we only present the jump as the headline once it holds up at the match level and across nearby ways of drawing the window (a touch easier or harder ask, a few more or fewer balls left). The direction, that the same chase is easier now, is the robust part and is all the copy claims. (Technical: `wp_grid.calibration.era_anchor`, window = required rate ≥ 9 with balls_left in 57..63; distinct-match count, match-clustered interval, and an adjacent-window robustness sweep are emitted and checked before ship; the window is fixed on pre-registered grounds and is never tuned to a target headline.)

6. **The WPL mask.** The women's league has played 88 matches, so most states have too few chases to say anything honest about. Any WPL square built from fewer than a dozen chases (fewer than 15 for the runs table) is marked and shown hatched with "not enough WPL cricket yet", instead of a smoothed number that would look like a finding. As the WPL plays more cricket, more of the grid fills in. (Technical: win-grid `wpl_mask_min_n = 12`; run-grid `mask_min_n = 15`; masked cells carry `masked = 1`.)

7. **Full methods →** (persistent footer link to `${base}/methods/`, per CONTRACT §4).

---

## 5. Payload inventory (ledger delta, blueprint §2)

The interlude ships **no new layout buffer** (it reuses `free`) and **no new per-point attribute**. Its incremental payload is the two engine JSONs (which R3b introduces; the interlude is their first consumer) plus one small scene file, all lazy-loaded when the reader reaches `#interlude`:

| Artifact | Raw | Note |
|---|---|---|
| `engines/wp_grid.json` | ~154 KB | win grid + calibration + era anchor; lazy on interlude entry |
| `engines/re288.json` | ~21 KB | run-expectancy surfaces; lazy on interlude entry |
| `data/scenes/interlude.json` | ~2–4 KB (new) | the two chase presets (state + both looked-up values + era), the era-anchor pair (+ distinct-match count, clustered interval, robustness sweep), and the IPL free-play evidence flags; pipeline-emitted |

Gzipped these are well under the **≤2 MB gz per-chapter** incremental budget (order ~40–50 KB gz total). No layout buffer means the interlude does not move the "≤3 MB before assembly" or "≤25 MB full read" numbers meaningfully. The R3b full-read total is dominated by Ch 5's assets, not the interlude. **Pass criterion for this release: interlude incremental within budget; verified in the payload ledger.**

---

## 6. Verified-number index (single source for QA)

Every on-screen number and every default, with its artifact field. On-screen literals are bound at build; illustrative numbers used in this storyboard's prose are marked *illus.*

| On screen / default | Value | Bound to |
|---|---|---|
| Same chase, 2008 to 2012, win | **about 23 in 100** | `wp_grid.calibration.era_anchor.ipl_2008_2012.win_rate = 0.2323` (934 ball-states) |
| Same chase, 2023 to 2026, win | **about 31 in 100** | `wp_grid.calibration.era_anchor.ipl_2023_2026.win_rate = 0.314` (1242 ball-states) |
| Same chase, win gap | **about eight more in a hundred** | 0.314 − 0.2323 = 0.0817; on screen never "points" |
| Same chase, gap: distinct-match count + match-clustered range | **pipeline to emit** | new `era_anchor` fields (distinct matches per era, clustered interval on the gap, adjacent-window sweep); gap must clear match-level significance before shipping as the climax (§9.1) |
| Same chase, 2008 to 2012, runs (quiet corroboration) | **~78** | `re288.surfaces['ipl 2008-2010'].re[10][4]` = 77.7 |
| Same chase, 2023 to 2026, runs (quiet corroboration) | **~89** | `re288.surfaces['ipl 2023-2026'].re[10][4]` = 89.0 |
| Default-spot Meter A (10 left, 6 in hand) | **~89** *illus.* | `re288.surfaces['ipl 2023-2026'].re[10][4]` = 89.0 (or pooled if added) |
| Default-spot Meter B (10 left, 6 in hand, 90 needed → rrr 9) | **36 in 100** *illus.* | `wp_grid.second_innings.surfaces['ipl pooled'].wp[9][5][4]` = 0.3568; cell n=124 (evidenced) |
| Preset 1 (Dhoni chase finish) both currencies | **{expRuns}/{win} in 100** | `interlude.json` presets[0]: a corpus-verified Dhoni *chase*, state asserted present in the second-innings grid (§9.2) |
| Preset 2 (nine an over) both currencies | **{expRuns}/{win} in 100** | `interlude.json` presets[1] |
| IPL free-play evidence threshold (same rule as WPL) | **12** chases / **15** innings | `evidence_min`; per-cell `n` on `ipl pooled` / `re288` IPL surfaces (win: 1049/2000 cells n<12, median n≈9); thin cells flagged, not printed as fact |
| Matches behind the grid | **1,331** (88 WPL) | corpus / `wp.py` |
| Calibration gap | **~1 in 100** | `wp_grid.calibration.ece = 0.01144` (tolerance 0.03) |
| Calibration states checked | **144,136** | `wp_grid.calibration.n` |
| First innings now averages | **~189** | `re288.surfaces['ipl 2023-2026'].re[0][0] = 188.5` (footnote/QA anchor) |
| WPL win-grid mask threshold | **12** chases | `wp_grid.second_innings.wpl_mask_min_n = 12` (1,725/2,000 masked) |
| WPL run-grid mask threshold | **15** innings | `re288.wpl_evidence_mask` / `mask_min_n = 15` (155/200 masked) |
| rrr bucket edges | `[6,7,8,9,10,11,12,15,20]` | `wp_grid.second_innings.rrr_edges` |

**QA rule:** no literal number appears in a component or a caption; every one resolves through a fetch of the artifact above (payoff-card discipline extended to the interlude). If a value changes when the pipeline reruns, the copy changes with it, byte-for-byte.

---

## 7. Integration notes (shell + pipeline + composition)

New scene dir: **`web/src/lib/scenes/interlude/`** (owner: interlude builder; add to the CONTRACT §7 ownership map). Exports `scenes: SceneDef[]` from `index.ts`. Requires the following shell-owned changes (by PR to the shell, per CONTRACT §7), each small:

1. **`types.ts` — `ChapterId`.** Add `'interlude'` to the union (`'coldopen' | 'picker' | 'ch1' | 'ch2' | 'ch3' | 'ch4' | 'interlude' | 'endcard' | 'bowl'`). No new `LayoutId` (the interlude uses `free`).
2. **Composition order — `web/src/routes/+page.svelte`.** Insert `...interlude` between `...ch4` and `...endcard`: `[...coldopen, ...picker, ...ch1, ...ch2, ...ch3, ...ch4, ...interlude, ...endcard, ...sandbox]`. (Chapter 5 slots between the interlude and the end card in R3b-2; not here.)
3. **Nav flip — `navplan.ts`.** Remove `'Interlude: The Net Session'` from `FUTURE_CHAPTERS`; the first interlude scene declares `navLabel: 'Interlude: The Net Session'` and `anchor: 'interlude'`, so `buildNavItems` lists it as a live link. This is the "flip SOON to live" the brief asks for.
4. **End-card tease flip — `web/src/lib/scenes/endcard/EndCard.svelte`.** The interlude is no longer the thing being teased (it is live), so retarget the tease. Chapter 5 ships in a *separate later release* (R3b-2) and is not live here, so the tease must carry an honest **in-build / coming-soon qualifier** and must not promise shipped content: e.g. "Coming soon: Chapter 5, What a Ball Is Worth (in build)", or route the end card to the live sandbox / end for this release. No on-screen line may promise content that is not shipped.
5. **Ch 4 hand-off — `web/src/lib/scenes/ch4/index.ts`.** The C4-12 return leg comment already says it "hands off to the interlude / end card"; its `free` end-state is exactly the interlude's entry, so no field change is needed. The interlude's `fromState` defaults to Ch 4's `free`; its `fieldState = { layout: 'free', dim: ~0.18, teamIgnite: true }`.
6. **Footnote registry — `footnotes.ts`.** Add the `netsession` entry (§4) with the calibration `FootnoteFigure` (pred/actual deciles from `wp_grid.calibration.bins`).

**Pipeline (`pipeline/scenes.py`):** add an interlude emitter that writes `web/static/data/scenes/interlude.json`, byte-deterministic and snapshot-tested. The meters read the two engine JSONs directly (already shipped, gate-passed); the pipeline adds only this small scene file. It must emit:

- **The two chase presets** (`{label, overs_left, wickets, runs_needed, era, expRuns, win}` each, with `expRuns`/`win` looked up from `re288.json`/`wp_grid.json` at build time so the copy binds to a field). **Preset 1 must be a corpus-verified Dhoni *chase* finish** bound to a real second-innings state; the snapshot harness asserts that state actually exists in `wp_grid.second_innings` (not an imputed corner) and that its cell is evidenced. **Do not ship the currently-emitted `presets[0]` "Dhoni, 2011 final", which is a first-innings *defend*** (CSK batted first, 205/5) framed with a defend percentage: that is a third currency the interlude was scoped to avoid and a defend cannot supply a chase scoreboard (§9.2). Re-bind or relabel it before ship.
- **The same-chase era pair** pulled straight from `wp_grid.calibration.era_anchor` + the two `re288` era cells. Also emit, per era, a **distinct-match count** and a **match-clustered uncertainty interval on the gap**, plus an **adjacent-window robustness sweep** (rrr ≥ 8 vs ≥ 9; balls_left 50–70 vs 57–63), so the climax can be gated on match-level significance (§9.1). Reconcile the emitted single-cell era reads (currently `presets[1]/[2]` at rrr 10 give 21 / 34) with the storyboard's window-aggregate headline (23 / 31 from `era_anchor`): the headline binds to the aggregate, the live meter is the secondary single-cell "feel".
- **A per-cell evidence flag for the IPL free-play surfaces**, at the same thresholds as the WPL mask (12 win / 15 runs), so the client can flag thin IPL cells without printing them as fact. The per-cell `n` already ships on every surface, so this is a threshold read, not new modelling.

Extend the snapshot harness to assert the presets exist and are non-degenerate (numbers present, in range, not all equal), that preset 1's state exists and is evidenced in the second-innings grid, and that no preset lands on an imputed cell presented as observed.

---

## 8. QA checklist (storyboard-level, release-blocking)

- [ ] **Voice:** zero em dashes anywhere in interlude copy; every dial and meter glossed in plain words beside its first number (gloss-adjacency, §0.2); one idea per caption, one number per idea; slop/voice check passed on §2.
- [ ] **Win format + dates locked:** win said as "in 100" everywhere (meters, presets, era caption, teasers); **no "%" and no "points"** in any reader copy; on-screen dates spelled out ("2008 to 2012"), no en-dash.
- [ ] **Numbers bound:** every literal in §6 resolves through an artifact fetch; nothing hand-typed; reruns of the pipeline change the copy automatically.
- [ ] **Honesty parity, both leagues (blocking):** no thin or rule-imputed cell is presented as an observed finding in *either* league; IPL free-play thin cells (`n < 12` win / `< 15` runs) carry the same evidence flag + hatch the WPL uses; the default spot (n=124) shows a real number; a swept sparse corner shows the flag; footnote §4 para 1 describes the table as EB-shrunk / monotone-regularized with thin cells imputed by rule, not "the empirical win rate".
- [ ] **Demand-mode:** the field loop is provably STOPPED while the widget is shown (idle GPU near zero); no control handler calls `field.*` or requests a frame; verified on a mid-range Android over a multi-minute dwell.
- [ ] **Two meters correct:** Meter A responds to overs-left + wickets only; Meter B responds to all three; dragging runs-needed leaves Meter A unchanged, shows the "reads your batting, not the target" note, **and announces that non-response in the live region** (reads as correct, not broken, for SR too).
- [ ] **Presets:** both set the sliders and update both meters; each quotes both currencies ("{expRuns}" / "{win} in 100"); preset 1 is a corpus-verified Dhoni *chase* whose state exists and is evidenced in the second-innings grid (not the 2011 defend).
- [ ] **Era climax is default-visible + honest:** the same-chase, two-eras payoff renders as a default-visible caption (not gated behind the era switch); the win jump leads (23 → 31 in 100, "about eight more in a hundred") and the runs pair (~78 → ~89) is demoted, not co-headline; the switch is optional reinforcement on its own full-width control. The gap ships only after the pipeline confirms it holds **at the match level** (distinct-match count + match-clustered interval + adjacent-window robustness sweep), and the window is not tuned to a target headline.
- [ ] **WPL mask:** the first WPL flip at the default spot (a masked cell) is pre-framed by IN-5 caption 1 (young-league orientation in the same breath); masked cells show "not enough WPL cricket yet" (and hatched grid if shown), never a smoothed number; evidenced cells show a number; thresholds 12 (win) / 15 (runs) honoured.
- [ ] **Mobile:** widget thumb-usable, single column, meters above dials, presets wrap, WPL + era switches each full-width; **fits within 100dvh and/or pins a live meter readout to the top while any slider is dragged** so the changing number never hides under the thumb; no horizontal scroll; tap targets ≥44px; no hover-only content.
- [ ] **Reduced motion / keyboard / SR:** every teaching beat reachable by keyboard; meters announced in a live region; the runs-needed non-response announced as text; masked/thin state announced as text; captions persistent (never faded); nothing lost.
- [ ] **Caption placement:** no caption covers the widget; framing captions top-left clear of ☰.
- [ ] **Nav + composition:** interlude live in the nav (SOON flipped); `#interlude` deep-links; end-card tease carries an in-build/coming-soon qualifier for Ch 5 (or routes to the live sandbox/end) and promises no unshipped content; R1–R3a scenes still render byte-identically.
- [ ] **Payload:** interlude incremental within the ≤2 MB gz per-chapter budget; ledger updated.
- [ ] **Footnote:** `netsession` sheet reachable from IN-2 on; calibration figure plots only verified `bins`; "Full methods →" present.

---

## 9. Open calls to owner / pipeline (decide at the R3b milestone review)

1. **The same-chase headline is the emitted 23 / 31 in 100 on a fixed, pre-registered window (the load-bearing one).** The blueprint quoted 24.3 / 31.8; the engine emits `wp_grid.calibration.era_anchor` = **0.2323 (2008 to 2012) vs 0.314 (2023 to 2026)**, i.e. about **23 vs 31 in 100**, a gap of about eight in a hundred. Numbers are data-bound and never hand-typed, so the copy binds to the emitted values. **This closes to option (a): accept 23 / 31.** The earlier "option (b) re-derive the window to reproduce 24.3 / 31.8" is **removed**: choosing the window by the headline it produces is exactly the cherry-picking the audit guards against. The window stays fixed on interpretable, pre-registered grounds (required rate ≥ 9, balls_left 57..63), and no window may be selected by its resulting number. **Two binding pipeline asks before this ships as the climax (§3, §4 para 5, §8):** (i) the anchor counts (934 / 1242) are legal-*ball* states, not matches, so emit a distinct-match count per era and a **match-clustered uncertainty interval on the gap**, and confirm the gap clears significance at the match level (a rough clustering deflation drops it from very strong toward borderline, so this is not a formality); (ii) emit an **adjacent-window robustness sweep** (rrr ≥ 8 vs ≥ 9; balls_left 50–70 vs 57–63) showing the gap is directionally stable, so the climax is evidenced, not an artifact of one exact window. If the gap does not survive, keep the direction ("chases got easier") and soften the certainty; do not overstate.
2. **RESOLVED (blocking): preset 1 must be a Dhoni *chase* finish, not the 2011 defend.** In the 2011 final Dhoni's CSK **batted first** (205/5) and **defended**; the widget is chase-shaped and reads the second-innings grid, so no honest chase scoreboard exists for that match, and the currently-emitted `presets[0]` reaches for a defend percentage (a third currency the interlude was scoped to avoid). **Decision:** relabel and re-bind preset 1 to a **corpus-verified famous Dhoni chase finish** that maps to a real, evidenced second-innings state; the pipeline binds the scoreboard and both currencies from a field, and the snapshot harness **asserts that state exists and is evidenced in `wp_grid.second_innings`**. Do not ship a chase preset built from a defend. (If no single iconic verified Dhoni chase finish qualifies, fall back to a de-personalised but real famous last-over chase rather than a defend; still pipeline-bound.)
3. **Add a pooled all-era RE surface for Meter A's default (recommended small pipeline ask).** `wp_grid.second_innings` has an `ipl pooled` surface (best-evidenced) that Meter B uses by default. `re288.json` has only era bands, so Meter A's free-play default currently has to pick a band (this storyboard picks `ipl 2023-2026`). For a consistent, best-evidenced default across both meters, add an `ipl pooled` (all-era) surface to `re288.json`. If it is not added, Meter A defaults to `ipl 2023-2026` and this is fine, just flagged.
4. **Preset 2 label: "nine an over" vs the blueprint's "ten an over."** This storyboard uses **nine an over, ten overs to go** so the preset sits exactly inside the well-sampled `era_anchor` window (required rate ≥ 9), making the "23 vs 31 in 100" headline data-honest. The blueprint's illustrative label was "ten an over at halfway." Minor; flagged for sign-off.
5. **Optional grid heat panel (§2f).** Ship the small 20×10 win-surface heat behind a "show the grid" disclosure, or defer it to a footnote figure for v1? It makes "you are reading one square of a remembered table" literal and gives the WPL mask a place to render as visible geography, but it is the one non-essential surface here. Owner call on scope.

---

## Revision notes (audit pass, 2026-07-06)

Applied all **must-fix** and **should-fix** items from the design audit, plus all four **consider** items (each cheap and honesty- or voice-improving). Data claims were verified directly against `engines/wp_grid.json` and `engines/re288.json` before editing.

- **[must-fix] IN-6 teaser reframe.** Replaced "about eight points more often a win now than in 2008–12" (leaked the banned "points" unit and did not parse) with the taught in-100 frame: "The same chase is a win about eight more times in a hundred now than in 2008 to 2012." Added *points / percentage-points* to the §0.7 banned-on-screen list.
- **[must-fix] Honesty parity for the IPL free-play meters.** Verified the IPL `ipl pooled` win surface is thin over most of the grid (median cell n≈9; 730/2000 cells n=0; 1049/2000 ≈53% with n<12) yet printed confident "N in 100". Introduced one minimum-evidence rule for **both** leagues (per-cell `n` already ships; `evidence_min` = 12 win / 15 runs): evidenced cells print a number, thin cells flag as filled-in-by-rule and hatch. Rewrote footnote §4 para 1 from "the empirical win rate" to an honest EB-shrunk / monotone-regularized / rule-imputed description, scoped the "a lookup, not a guess" claim to "the shape is memory; thin spots say so", and added a §8 blocking check that no imputed cell is presented as observed. Updated §0.1, §2d, §2e/§3, §2f, §6, and the IN-6 teaser.
- **[should-fix] Era climax made default-visible (IN-4).** The same-chase, two-eras payoff now renders as a default-visible caption (both eras' bound numbers in prose), not gated behind a nested toggle its own target audience would never find; the switch is demoted to optional reinforcement on its own full-width control (§2b promotes it out of the preset row).
- **[should-fix] Same-chase caption number load.** Split into two steps: the **win jump leads** (23 → 31 in 100, "about eight more in a hundred"); the runs pair (~78 → ~89) is quiet corroboration, not a co-headline. Keeps each step within ≤3 numbers / one number per idea.
- **[should-fix] Orient-then-reveal contradiction reconciled.** Chose the gloss-adjacency resolution (§0.2 rule 1, aligned in §2 and §8): default meter reads are permitted because each gloss sits with its control/meter, so an oriented default value is a label, not a surprising reveal; the rule that still binds is that no figure *makes an argument* before its plain setup.
- **[should-fix] Mobile viewport guarantee.** Added a binding constraint (§0.6, §2b, §8): the widget fits within 100dvh **and** pins a slim live meter readout to the top while any slider is dragged, so the changing number never hides under the thumb on the lowest (runs-needed) slider.
- **[should-fix] Win format + date style locked.** "in 100" everywhere for win; dropped "%" and "points" from all reader copy; on-screen dates spelled out ("2008 to 2012"), no en-dash. Swept meters, presets, era caption, teasers, and stale meta references.
- **[should-fix] Accessibility parity on the runs-needed non-response.** On any runs-needed change the live region now announces that Meter B updated and Meter A holds *because* it reads your batting, not the target, so the non-response reads as correct for SR/keyboard readers too (§0.8, §2d, IN-2, IN-3, §8).
- **[should-fix] WPL default-cell first read.** Verified the default spot is masked in the WPL (n=10 < 12), so the first flip hits a mask. IN-5 caption 1 now folds the young-league orientation into the same breath as the first mask, so the honest hole never reads as a broken widget.
- **[should-fix] Era gap certainty.** Verified the anchor counts (934 / 1242) are legal-ball states, not matches; a rough clustering deflation drops the gap from very strong toward borderline. Replaced "hundreds of matches each" (§4 para 5) with the true unit, hedged the on-screen copy to directional ("chases got easier"), and made shipping the climax contingent on the pipeline emitting a distinct-match count, a match-clustered interval, and an adjacent-window robustness sweep (§3, §6, §8, §9.1).
- **[should-fix] §9.1 de-risked.** Removed the option that reshapes the window to reproduce the blueprint's 24.3 / 31.8; locked to the emitted 23 / 31 on a pre-registered window (rrr ≥ 9, ~60 balls left) with an explicit "no window selected by its resulting headline" rule.
- **[should-fix] Preset 1 Dhoni defend→chase.** The 2011 final is a first-innings defend and the emitted `presets[0]` reaches for a defend percentage (a third currency); resolved §9.2 as blocking. Preset 1 must be a corpus-verified Dhoni *chase* finish bound to a real, evidenced second-innings state, with a snapshot assertion that the state exists in the grid.
- **[consider] applied:** illustrative default win corrected 46 → 36 in 100 (`wp[9][5][4] = 0.3568`) across §2a, §0.8, IN-2, §6; "the numbers remember" kept only at the IN-4 tie line and the IN-6 teaser varied to plain, honesty-scoped fact; end-card Ch 5 tease carries an in-build / coming-soon qualifier so no on-screen line promises unshipped content (§7 item 4, §8).
