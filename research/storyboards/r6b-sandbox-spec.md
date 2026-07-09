# R6b UX Spec: THE BOWL (the full sandbox instrument)

**Status:** implementation truth for R6b (the sandbox only). This is a UX spec for a single interactive INSTRUMENT, not a scroll storyboard. Where this document and older blueprint copy disagree, this document wins; where it disagrees with the blueprint's standing rules (experience-blueprint §2) or the voice guide, those win, and nothing below may violate them. Modeled on the chapter storyboards' rigor (a hard-invariants header block, a §0 interaction grammar, sectioned per-surface specs, a stage-name/label table, a verified-number index, a QA checklist, and owner-call notes), but every section describes the instrument's UX, not a scene.

**What R6b is.** After the Ch10 finale exhales the chronological ribbon back into the cold-open free field (C10-9), the persistent 316,199-ball field is HANDED to the reader as a filterable instrument. The piece is over; this is the playground it leaves behind. The reader drives it: filter the whole field by any combination of facets, tap any ball to see the exact delivery, open a breakdown panel, take a one-tap guided tour, and copy a link to any view.

**What R6b extends.** The R1b minimal sandbox already ships (`web/src/lib/scenes/sandbox/Bowl.svelte` + `data.ts`): team + season facets, the tap-a-ball tooltip, the keyboard inspector, one 2019-final preset, and the open-never-blank pre-filter to the reader's picked team. R6b keeps all of that and extends it to the full facet grammar (league, phase, over-range, outcome, batter, bowler, all combinable), a ~10-flag guided-tour rail, a linked breakdown panel, and shareable URLs.

**Grounding source:** `scratchpad/r6b-digest.md` (the verified plan) and `scratchpad/r6b_tourflags.json` (the ten flags with real ball counts). Every on-screen number below is data-bound and traces to those two files. **ARTIFACT WINS:** where a count here differs from the emitted `scenes/sandbox.json` / columnar recount, the emitted value ships and QA asserts the on-screen figure equals it.

---

## Hard invariants (the header block; every surface inherits these; none may break them)

1. **The field STAYS at 14 vertex attributes.** The full grammar is delivered as a per-point PASS/FAIL `Uint8Array(316,199)` mask uploaded as ONE R8 data texture (`uFilterMaskTex`), computed in JS over the columnar typed arrays (0.26 to 4.8ms measured). No 15th attribute is bound (a 15th blacked out the whole field on one build, CONTRACT §24.2). The mask adds one data texture plus two scalars, never an attribute.

2. **SCALAR-vs-MASK routing, mutually exclusive per render.** If ONLY team/season/matchRange are set, keep the R1b scalar fast path (`field.setFilter`, mask null, zero mask cost, byte-identical to R1b). If ANY of phase/over/outcome/batter/bowler is set, build the mask (`field.setFilterMask`, scalar team/season/range set to -1/inactive). `buildFacetMask` decides which path `commit()` takes. CONTRACT §28.

3. **Demand mode: ONE commit per change, no idle loop.** Every facet change is exactly one committed field state, rendered either as one static frame or as a single bounded self-terminating transition to that frame (a one-shot crossfade/pulse of ~150 to 250ms on the balls that entered or left the bright set, §0.4). The commit is still one `setFilter` OR one `setFilterMask` (never both); the optional cue tweens to that one result and then stops. After it settles the GPU returns to idle: there is no persistent rAF loop, no scrub, no set piece, and `prefers-reduced-motion` collapses the cue to the static frame. A tap is one offscreen pick pass. The breakdown panel recompute is ONE pass over the masked indices, gated behind panel-open.

4. **NEVER-BLANK.** The field is never shown empty. The instrument opens pre-filtered (picked team, or the 2019-final flag for a neutral reader). Clear-all re-lands on a non-empty view. A facet combo that returns zero balls does NOT blank the field: the field renders as dim haze and an empty-state card explains and offers one-tap recovery (§3).

5. **AND-combining.** Every facet AND-combines with every other (team AND season AND phase AND outcome AND wicket AND batter AND bowler). Within the outcome chips only, selections OR (Four OR Six), then that set ANDs against everything else; the wicket toggle is its OWN AND facet, kept in a separate control from the OR-chips (§2) so the OR/AND boundary is visible on the surface, not learned by surprise. The reader can always read the whole selection as one plain sentence (`selectionLabel`) plus a live "N balls" count.

6. **One commit write path.** All facet changes, flags, clear-all, and URL restores flow through a single `commit()`: it updates state, syncs `bowlHeld` (so a stray scroll re-applying the scene state can never revert the reader's facets, CONTRACT §12.2), routes scalar-vs-mask, renders once, drops a now-hidden tooltip, and `history.replaceState`s the shareable URL. There is no second path.

7. **Every number is data-bound.** The live count comes from `buildFacetMask().count` (or the R1b `countVisible` on the scalar path). Every flag-card count, every panel figure, and every tooltip figure is read from the columnar arrays or the emitted artifact, never hand-typed.

8. **A shared URL is explicit intent and SUPERSEDES never-blank.** On mount, if the hash carries facet params or a flag id, the instrument decodes and commits that view instead of the picked-team open. Deep links never throw (unknown/out-of-range params are clamped or ignored).

9. **Tour flags never point at nothing.** Each of the ~10 flags is resolved against real data at build and validated to return at least one ball (loud build failure on 0). The counts shipped on the flag cards are the verified counts in the verified-number index (§13).

10. **Mobile-first, keyboard-accessible, no hover-only content.** The tray and the panel are bottom sheets on a phone; every control is a 44px tap target reachable by thumb; every control is reachable and operable by keyboard with a visible focus ring; nothing is revealed on hover alone (hover may enhance, never gate). `aria-live` announces the count and the selection.

11. **VOICE (binding).** Every reader-facing string follows the voice guide: plain, "you" with mate-on-the-couch swagger, orient before you flourish, ZERO em dashes anywhere, and no stat jargon in a label (the powerplay is "the first six overs," the death is "the last five," economy/strike-rate/par never appear as bare terms of art). The tour-flag blurbs in `r6b_tourflags.json` contain em dashes and MUST be re-authored to the zero-em-dash forms in §12 before they ship.

12. **ARTIFACT WINS.** Every {braced} literal and every on-screen number traces to `scenes/sandbox.json` (the descriptor + the `tourFlags` array) or the columnar recount; the emitted value wins over any figure typed here if a rebuild shifts it.

---

## 0. Interaction grammar (deltas on the R1b Bowl grammar)

Everything in the R1b Bowl carries forward: a dot is one ball; the field is the pick surface (`touch-action: pan-y`, `onclick` not `pointerdown` so a scroll-drag never fires a pick); the tap-a-ball tooltip names the exact delivery; the keyboard inspector steps visible balls; the intro orients; the controls sit thumb-reachable at the bottom. R6b adds:

### 0.1 The unit and the mark, unchanged
A dot is still one ball, one of 316,199. Filtering does not move a dot; it decides whether a dot is BRIGHT (a member of the selection) or DIM (filtered out but still part of the haze, so the field is never blank). The reader's mental model is "I am dimming the sky down to the balls I care about," never "I am loading a new chart." This is why `mode: 'dim'` is the default for facet building (the haze always survives) and `mode: 'hide'` is reserved for the match-preset flag (a single match reads cleaner with the rest hidden).

### 0.2 The AND-combining model, made legible
Facets AND together. The reader must always be able to answer two questions without guessing: "what is selected right now?" and "what will this control do?" Both are answered by permanent on-screen scent, never by a tooltip or a hover:
- **selectionLabel** is a single plain sentence built from the active facets, in fan language, dot-separated: e.g. `RCB batting · 2016 · the death overs · sixes only`, or `Bumrah to KL Rahul`, or `The whole field`. A team facet ALWAYS renders with its side (`RCB batting`), so the label claims exactly what the mask selects (batting-side deliveries) and never reads as a bare team name that a fan would take to mean all of a team's balls. Null facets are omitted, not shown as "All". If the sentence runs long it wraps to at most two lines (never truncated so far the scent is lost); at mobile peek it truncates with the full label on focus/tap.
- **the live count** reads `N balls` beside the label, updated on every change (`aria-live="polite"`).
- **active controls are visibly lit** (a set select shows its value; a lit chip has `aria-pressed="true"` and a filled style; a picked batter/bowler shows a removable chip). An inactive control reads "All ..." or empty.
- Within the outcome chips, multiple chips OR (Four + Six = "fours or sixes"); the wicket toggle is a SEPARATE AND control (its own labelled toggle, §2), so `sixes only` and `sixes that took a wicket` read as two different selections; across facets everything ANDs.

### 0.3 The one commit() write path (extends R1b)
`commit(patch)` is the only writer. It: (1) folds the patch into the facet state; (2) calls `buildFacetMask(col, groupSeason, teams, f)` which returns `{ mask, count, firstIndex }` AND a scalar-vs-mask decision; (3) if `count === 0`, takes the never-blank empty branch (§3) instead of applying; (4) else routes `field.setFilter` (scalar path) OR `field.setFilterMask` (mask path) exactly once; (5) `syncBowlHeld(f)` (stashes the last mask on `bowlHeld.filterMask` so a re-application re-uploads the SAME mask); (6) `history.replaceState(null, '', encodeFacets(f))`; (7) drops the tooltip and `kbIndex` if the tapped ball is no longer visible. No control, flag, clear-all, or URL restore may bypass this path.

### 0.4 Demand-mode discipline
One committed state per change (invariant 3). The mask build is a single columnar pass with cheapest-first short-circuit (matchRange, league, team, season, over-range, outcomes, batter, bowler). The panel recompute is a single pass over the masked indices and only runs while the panel is open. Typing in a typeahead does NOT commit per keystroke; a commit fires only on a resolved selection (a name that maps to a dict index) or on clearing the field.

**The change cue (make the re-mask perceptible).** A small facet delta (say bright-set 40k down to 37k) re-masks a dim 316k field with almost no visible difference, and a silent static swap between two near-identical frames is the weakest possible attention cue. So the PRIMARY feedback for every commit is the live count + `selectionLabel` (always legible, always updated, and enough on its own). On top of that, the field plays a single bounded one-shot cue, a ~150 to 250ms crossfade or a brief pulse on the balls that entered or left the bright set, so the change is perceptible on the hero surface (the field is the declared hero, and it should visibly respond). The cue is triggered by the commit, runs once, and settles to idle; it is not an rAF loop and not a scrub (invariant 3), and `prefers-reduced-motion` drops it to the static swap and leans on the count + label.

### 0.5 Keyboard & a11y grammar
The tray is native controls in DOM tab order. Segmented controls (league, phase) are radio-style button groups (arrow keys move within, Space/Enter selects). Outcome chips are toggle buttons (`aria-pressed`, Space toggles). Typeaheads are `<input list>` backed by `<datalist>` (native combobox a11y). The flag rail is a horizontal list of buttons (Tab through, or Left/Right arrow roving tabindex). The panel is a labelled region/dialog; the tooltip is a `role="dialog"` dismissed by Escape or its close button. The keyboard inspector (Inspect a ball, then arrow keys) carries over from R1b and honors the mask via the CPU `pointVisible` mirror. Every focus target has a `:focus-visible` ring; every interactive element is ≥44px.

### 0.6 Banned in labels and copy
No bare stat jargon on any control or card. Banned as labels: *economy, strike rate, RPO, par, dot-ball percentage, boundary %, dismissal, phase (as a bare term)*. Allowed only with an in-breath gloss in a footnote-depth blurb. ZERO em dashes. No "not X, not Y." Orient before you flourish.

---

## 1. THE INTRO / the handoff from the Ch10 finale

**Purpose:** name the handoff and orient the reader on what they can now do, in one breath, then get out of the way.

**Entry.** The instrument mounts after C10-9 exhales the ribbon back to the cold-open free field and holds. The Bowl morphs that free field into season columns (so the season facet maps spatially) and holds there (the existing `bowlHeld` terminal held scene, `morphLength: 90` then a long interactive hold). No new morph. The reader's picked team stays lit as members of the field, so their own history is already visible before they touch anything.

**The intro card** (top-centered, non-interactive, fades to a clear gap so it never covers the field for long; carries over the R1b markup, re-authored copy):
- **Overline:** `THE BOWL · THE FIELD IS YOURS`
- **Lede (orient):** `Every dot is one ball, from every IPL and WPL match ever played. The story's done. The field is yours now.`
- **One line of what-you-can-do:** `Filter it down below, tap any bright ball to see exactly what happened, or take a guided tour to get started.`

That third line is the load-bearing onboarding sentence: it names the three affordances (the tray, the tap, the tour) so a reader who does not know what to filter has a door in (the tour rail, §4). Reduced motion / static: the card renders as a static stepped block; nothing requires motion.

**Persistent re-entry (do not lose the sentence on a timer).** The intro card fades to a clear gap so it never covers the field for long, but the three-affordance sentence is critical guidance and must not vanish for a slow newcomer who has not acted yet. So a compact, always-present `New here?` control (in the tray's readout row, and at mobile peek, §2/§7) re-shows the affordance line and points at the tour rail on tap. A reader who missed or lost the card can always call the guidance back without recall; the whole newcomer path rests on this sentence plus the persistent tour rail (§4), so neither is left on a timer.

**Never-blank on entry (carried from R1b, extended):** the open effect fires once the Bowl is active. If the reader picked a team, `commit({ team })` (their team lit, dim mode). If neutral or unmapped, `commit` the 2019-final flag (`fl=final-2019`, hide mode). If the mount hash carries facet params or a flag id, the URL restore SUPERSEDES both (§6, §8). The full field shows meanwhile (never blank) until the open commit lands.

---

## 2. THE FACET TRAY

**Surface.** The R1b `.controls` bottom bar becomes a scrollable facet tray: a thumb-reachable panel on desktop (bottom-center, `min(640px, 96vw)`), a bottom sheet on mobile (§7). Native controls only (a11y, zero deps). A single `commit()` write path (§0.3). The tray scrolls internally if it overflows; the live readout and the primary actions are pinned so the count and Clear-all are always visible.

**Control layout: three titled groups (not one stack of seven).** The controls are chunked into three labelled sections with a divider between them (Gestalt common-region and proximity), so the reader scans three small groups instead of one undifferentiated list of seven. Within each group the coarse, most-used facets sit first and the rare/precise ones sit under a disclosure. The section titles are quiet fan-language headers, never stat jargon.

**Group A. `Where & when`**

1. **League** segmented control. Options: `All` / `IPL` / `WPL`. Selecting a league re-scopes the Team and Season option lists to that league (an IPL team can't be picked under WPL). Label: `League`.
2. **Team** `<select>` with optgroups (`IPL`, `WPL`), from `teams.json` (20 ids). Options read `short · name`. The picked value renders batting-side at a glance, e.g. `RCB batting`, so the control never claims more than the mask selects (§0.2); the footnote-depth blurb confirms the team facet is batting-side in v1. Default `All teams`. Label: `Team`.
3. **Season** `<select>`, the distinct years (2008 to 2026). Default `All seasons`. Label: `Season`.
4. **When in the innings** segmented control (the phase facet in fan language). Options: `All` / `The powerplay` / `The middle` / `The death`. Each option carries a plain gloss on the control or one line beneath it: powerplay = the first six overs, the middle = overs 7 to 15, the death = the last five overs. Sets `overLo`/`overHi` via `phaseToOverRange` (powerplay [0,5], middle [6,14], death [15,19]). Label: `When in the innings`.
5. **More filters** disclosure (collapsed by default; the label is `More filters`, never "Advanced", for one consistent name) containing:
   - **Pick your overs** dual number input, `Overs 1 to 20` (1-based on screen, 0-based `overLo`/`overHi` under the hood). The over-range and the phase control are ONE underlying facet made symmetric (the "one facet, two doors" rule): setting an explicit over-range CLEARS the phase control back to `All`, AND setting a phase MIRRORS its resulting range into these inputs (picking `The death` fills them with `Overs 16 to 20`), so whenever both are on screen they agree instead of contradicting. Label: `Pick your overs`.
   - **Active-facet badge + auto-expand.** When the disclosure holds an active facet (an over-range set by hand or mirrored from a phase), its header badges the count, `More filters · 1 active`, and the section auto-expands on a URL/flag restore, so an active facet is never stranded and invisible inside a collapsed section. The badge is in tab order and the disclosure is keyboard-expandable (§8).

**Group B. `What happened`**

6. **What came off the bat** toggle chips (the outcome facet). Chips: `Dot` · `1` · `2 or 3` · `Four` · `Six`. Multiple chips OR within the facet (Four + Six = fours or sixes); the set ANDs against everything else. Maps to the outcome bitmask. Label: `What came off the bat`.
7. **...that took a wicket** a single separate AND-toggle, set off from the outcome chips by a divider (its own labelled control, not a sixth chip). Wicket combines DIFFERENTLY from the chips: the chips OR, the wicket toggle ANDs, so `Four` + `Six` + wicket reads as "(fours or sixes) that took a wicket," never "fours or sixes or wickets." Because it combines differently it is grouped differently, so the OR/AND boundary is visible on the surface rather than learned by surprise. Maps to the independent wicket bit (it can co-occur with a run, so `Six` + wicket = sixes that were also a wicket ball, honest and rare). Label: `...that took a wicket`.

**Group C. `Who`**

8. **Batter** typeahead: `<input list>` backed by a `<datalist>` of all 860 batter names (from `col.dicts.batter`). Placeholder `Start typing a batter`. Resolves a typed name to a dict index on selection; commits then. A picked batter shows as a removable chip. Label: `Batter`.
9. **Bowler** typeahead: same pattern, 672 bowler names (`col.dicts.bowler`). Label: `Bowler`.
10. **The duel.** When BOTH a batter and a bowler are picked, the selection IS the duel (batter faced by bowler). The tray shows one merged chip, e.g. `Bumrah to KL Rahul`, and `selectionLabel` renders the duel form rather than two separate facets.

**The live readout + selectionLabel (pinned, always visible; the primary change feedback).**
- `selectionLabel`: the plain sentence (§0.2), e.g. `RCB batting · 2016 · the death overs · sixes only`. `The whole field` when nothing is active. A team facet always carries its side (`RCB batting`); a long sentence wraps to at most two lines and, at mobile peek, truncates with the full label on focus/tap so the scent survives at max facet depth.
- the count: `{N} balls`, `aria-live="polite"`, tabular numerals, from `buildFacetMask().count` (mask path) or `countVisible` (scalar path). The count + label are the GUARANTEED feedback for every commit (the field's one-shot change cue in §0.4 is additive, not the only signal).
- **Copy this view** is docked here, beside the label, because "share THIS view" is conceptually the readout made portable; it carries an icon + label and more visual weight than the niche `Inspect a ball` tool (§6).
- **New here?** a compact, always-present control here re-shows the intro's three-affordance line and points at the tour rail (§1), so the onboarding sentence is never lost on a timer.

**Primary actions (pinned row).** Visual weight tracks action value: `Copy this view` (the share loop) is elevated (docked by the readout, above); `Clear all` and `Show the breakdown` are the standard pair; `Inspect a ball` is deprioritized as a keyboard-only tool.
- **Clear all** button. Resets to `NO_FACETS`, then re-applies never-blank (the reader's team, or the 2019-final flag) so it never lands empty. Copy on the button: `Clear all` (its result is the whole field or your team, never a blank). It also clears the URL back to the base `#bowl`.
- **Show the breakdown** button. Opens the linked panel (§5). `aria-expanded` tracks panel state.
- **Copy this view** button. The share affordance (§6), elevated and docked beside the readout (above).
- **Inspect a ball** button (carried from R1b): starts the keyboard inspector at the first visible ball; arrow keys step. Kept for keyboard-only readers who cannot tap the field; deprioritized in the layout (on mobile it lives in the expanded sheet, not at peek, §7).

**Information scent (the reader always knows what a control does).** Every facet group carries a short label in the tray (the stage-name table, §11) and sits inside one of the three titled sections (above). No control's effect is hidden behind a hover. A disabled control (e.g. Team optgroups outside the chosen league) is visibly dimmed, not removed, so the reader sees why. When a control is set, it is lit; when cleared, it reads `All ...`.

---

## 3. THE NEVER-BLANK RULE + the "0 balls" empty state

**The problem.** A legal facet combo can return zero balls (a batter who never faced a bowler; a WPL team in a season it did not play; sixes in a spell that had none). Never-blank forbids showing an empty field, and every number is data-bound, so the reader will see the count go to `0`.

**The rule.** `commit()` computes `{ mask, count }` BEFORE applying. If `count === 0`:
1. **The field never goes blank.** The instrument does NOT apply an all-false HIDE. It renders the field as DIM HAZE (`mode: 'dim'` with the all-zero mask, so every point dims but the 316k-ball haze survives). The reader is looking at the whole sky, dimmed, not a black screen.
2. **An empty-state card appears** over the field, plain and specific, naming why and offering recovery. It dims the sky behind it but does NOT occlude the facet tray, so the reader can also fix the selection by hand, not only by the card's buttons. It is non-modal and non-blocking: an explorer hitting many rare zero-combos in a row keeps tweaking facets underneath without dismissing anything each time (the only ever-transient status in the instrument is the field's `Copied` toast; this card is a persistent, non-trapping panel that simply updates or clears when the count goes non-zero). Copy is data-bound to the offending facets:
   - Duel with no meeting: `No balls here. {Batter} never faced {Bowler} in this data.`
   - Team-in-season with no matches: `No balls here. {Team} didn't play in {Season}.`
   - Generic over-constrained combo: `No balls match all of that. Try loosening one filter.`
3. **Recovery, one tap, and it names what it removes.** The primary button NAMES the exact facet it will drop, so the effect is predictable before the tap, e.g. `Undo: sixes only` (removes the most-recently-changed facet, the one that dropped the count to zero, and re-commits, landing back on a non-empty view). A secondary `Clear all` goes back to the whole field / your team. The recovery is never "start over from scratch"; it always steps back to the last non-empty selection. On a zero-count commit, keyboard focus moves to this recovery button (§8).
4. **The readout shows the honest zero.** `0 balls` renders in the ember tint (`--ember`) so the reader sees the data told the truth, while the field behind it is the dim haze, not a void.

**Why dim, not hide, on zero.** Hide mode on an all-false mask is a literally blank field (the banned state). Dim mode on the same mask leaves the haze, so the never-blank invariant is satisfied structurally, and the empty card carries the information. Flags and the match preset (which use hide mode) are validated to return >0 at build (invariant 9), so they never reach this branch.

---

## 4. THE TOUR FLAGS (the guided-tour rail)

**Purpose.** Onboard the reader who does not know what to filter. A newcomer lands, sees the field, and can take one tap to a curated, spectacular, pre-filtered view with a one-line story. The flags are also the deep-link entries (a shared flag URL restores the exact view).

**The rail.** A horizontally scrollable rail of ~10 flag cards, sitting above the tray (desktop) or as a dedicated tab of the bottom sheet (mobile, §7). Each card is a button. The rail scrolls horizontally with momentum on touch and with Left/Right arrow keys (roving tabindex) for keyboard; the first and last cards are fully reachable (scroll-padding so no card is clipped under an edge). A subtle right-edge fade signals more cards off-screen (scent, not hover-gated).

**The flag card.** Each card shows:
- a short **label** (the hook), e.g. `Bumrah's longest duel`;
- the **count** as a data-bound number, e.g. `123 balls`;
- a one-line **blurb** in voice (zero em dashes, §12), e.g. `123 balls of India's deadliest yorker at its coolest head.`

Tapping a card calls `commit()` with the flag's facets (invariant 6): it sets the exact facet combo (or the match range for the 2019 final), renders once, updates `selectionLabel` and the count to match the card, and writes `fl={id}` to the URL.

**The reflection is made perceptible (this is the load-bearing grammar lesson).** The tray's controls update to reflect the flag's facets, but because the tray is a separate surface (a collapsed bottom sheet on mobile) that update is easy to miss across surfaces, so the controls the flag just set briefly pulse/highlight, and the FIRST time a reader opens any flag a one-time coach line reads `These filters made this view. Change any of them.` This turns "watch the field light up" into the actual grammar lesson (these facets built this view, now tweak them), so the reader learns the instrument by worked example rather than by osmosis. The flag is a STARTING POINT, not a locked mode: any subsequent facet change drops the `fl=` id and switches the URL to explicit facets (so the reader can take Kohli's 2016 and change the season).

**Flag categories and how each sets facets:**
- **Facet-predicate flags** (most): a pure per-column mask, e.g. `wpl-all-sixes` = league WPL AND outcome six. Sets the facets directly.
- **The match-preset flag** (`final-2019`): the contiguous match range (the existing R1b preset, hide mode). Becomes flag #0 in the rail.
- **The computed-predicate flag** (`two-hundred-club`): a precomputed 228-match "first-innings total ≥ 200" point set expanded to a mask at build (NOT a contiguous range). The pipeline emits the point ranges (or the match set) so the client applies it as a mask like any other.

**Onboarding read.** The rail is the answer to "what do I filter?" The default order leads with the most legible, human hooks (a famous duel, a record season, a famous final) before the aggregate-pattern flags (the powerplay six explosion, the death-overs dot storm). A newcomer taps one, reads the one-liner, sees the field light up, and now understands the instrument by example, then reaches for the tray.

The ten flags, their facets, verified counts, and re-authored zero-em-dash blurbs are in §12.

---

## 5. THE LINKED PANEL (worm + Manhattan + leaderboard)

**Purpose.** Answer "so what does this selection actually look like?" with three small, oriented, labelled views of the CURRENT selection, coordinated with the field (same mask, so the panel and the field can never drift).

**Surface.** `web/src/lib/scenes/sandbox/panel/LinkedPanel.svelte`, opened by the tray's **Show the breakdown** button. Fixed side panel on desktop (right edge, does not cover the tray or the intro), a bottom sheet on mobile (§7). Closable (Escape, a close button, or tapping Show-the-breakdown again). `computeSelectionStats(col, matches, mask) → SelectionStats` runs ONE pass over the masked indices and only while the panel is open (demand-mode, invariant 3). The panel is passed the SAME mask the field got, so they always agree.

**The always-on coupling strip (desktop; keeps the link visible, not just true).** The same-mask architecture guarantees the field and the panel can never DRIFT, but brushing/linking only pays off when the linked views are co-visible and move together. So on desktop a slim, always-on coupling strip sits at the field edge showing the live count + a one-line thread of the current selection (a sparkline of the worm, or the top scorer and top wicket-taker); it expands into the full breakdown panel on demand. It never steals the field; it keeps a visible thread of coordination so the reader can watch the count and the panel move WITH the field on every commit. When the mask changes, the strip/panel plays a brief COORDINATED transition alongside the field's change cue (§0.4), so the reader perceives field-and-panel-moving-together (one cause, one effect) rather than two surfaces updating independently. Mobile keeps temporal, not spatial, coupling (the field and the sheet are mutually exclusive, so the panel reflects the latest commit when reopened, §7).

**The three views, each oriented then labelled:**

- **The worm ("how the runs piled up").** Orient: `Runs adding up, ball by ball, across everything you've picked.` A single cumulative-runs polyline over the selection in point order (or, if exactly one batter is selected, that batter's cumulative `runs_batter` so it reads as one innings-shape). Self-contained local viewBox SVG (reuse the Ch2 Worms markup but DROP the GL `projectToCss` registration, since the panel is 2D DOM). Direct-labelled axes; no legend.

- **The Manhattan ("runs per over").** Orient: `Runs in each over. The red caps are wickets.` Inline SVG bars, `runsPerOver[over] += runs_total`, with a red cap segment per wicket in that over. Overs 1 to 20 on the x-axis (1-based on screen). ~40-line inline SVG modeled on the Ch3 single-bar. The load-bearing read is bar height (position on a common scale), never color.

- **The leaderboard ("who did the damage").** Orient two mini-lists: `Top run-scorers` and `Top wicket-takers` in this selection. Accumulate `runs_batter` by batter and wickets by bowler in the SAME pass, sort, take the top 5 to 8, resolve names via `col.dicts`. Reuse the Ch8 ReportCardRail ranked-list markup with a Ch3 mini value-bar. If the selection has no wickets (e.g. outcome = six only), the wicket list shows a plain `No wickets in this selection.` line, never an empty box (the panel's own never-blank).

**Coordination.** Recompute whenever the mask changes (the panel subscribes to the same committed facet state). Because it consumes the exact mask, a flag, a URL restore, and a hand-built facet combo all produce a panel that matches the field one-to-one. If profiling shows jank on the single pass, gate the recompute strictly behind panel-open (already the plan) and debounce to the committed state (never per-keystroke). Because the field re-masks instantly but the panel pass can trail on the largest selections (the 200 Club's 28,704 balls, the whole field's 316,199), the panel shows a legible updating state while it recomputes (a subtle `Updating...` line or a skeleton on the three views), so the momentary gap reads as "catching up," not as the two surfaces disagreeing; perceived coordination survives even when the computation lags, and the panel never shows stale numbers as if they were current.

**Empty selection in the panel.** The panel is only reachable when the field is non-empty (the tray's zero-count branch shows the empty card, not the panel). If a reader opens the panel and then drives the selection to zero, the panel shows its own `Nothing to break down yet. Loosen a filter.` line, matching §3.

---

## 6. SHAREABLE URL

**Purpose.** Let the reader copy any view and hand it to a mate; let a shared link restore that exact view.

**The affordance.** `Copy this view` is the product's viral loop (fans-first sharing), so its treatment matches its value: it is docked BESIDE the `selectionLabel` readout ("share THIS view" is the readout made portable), carries an icon + label, and is surfaced at mobile PEEK level, not buried in the expanded sheet (§7). It outranks `Inspect a ball` (a keyboard-only niche) in the layout. On tap: build `encodeFacets(f)`, write the full absolute URL to the clipboard, and show a brief inline confirmation `Copied` (a status line, `aria-live`, auto-clearing after ~2s; never a modal). The button is always enabled (there is always a view to share, even the whole field). On a flag view, the copied URL carries the flag id (`fl=`), which reads cleaner and is self-describing.

**The scheme** (`web/src/lib/scenes/sandbox/url.ts`, from the digest):
`#bowl?lg=w&t=13&s=2016&ph=death&o=15-19&oc=6&wk=1&b={batterIdx}&w={bowlerIdx}&fl={flagId}&v=1`
- omit null facets; league `i`/`w`; phase `p`/`m`/`d` OR a raw `o=lo-hi` over-range; the off-the-bat outcomes as compact letters `{0,1,2,3=four,6=six}` in `oc`; the wicket toggle as its OWN key `wk=1` (it is a separate AND facet from the outcome chips, §2, so it gets its own param, not a letter folded into `oc`); batter/bowler by DICT INDEX (not name); versioned `v=1` so a rebuild that reorders dicts invalidates stale links safely; a flag id `fl=` wins over individual facets on restore. Encode ONLY league/team/season/phase|overRange/outcomes/wicket/batter/bowler/flag (NOT mode, matchRange internals, the mask, or panel-open state).

**Writing the URL.** On every `commit()`, `history.replaceState(null, '', encodeFacets(f))` (replaceState, NOT pushState, so filtering does not spam the browser history / back button).

**Restoring a shared link.** On mount, once the columnar resolves, `decodeFacets(hash, col)`: if the hash carries facet params or a flag id, decode and `commit()` that view. This SUPERSEDES never-blank (invariant 8: a shared URL is explicit intent). Deep links never throw: unknown keys ignored, out-of-range team/season/over/dict-index clamped or dropped, a stale `v` falls back to the whole field (never a crash, never a blank). A `fl=` id restores the flag (facets + the flag card's lit state); an unknown `fl=` falls through to the individual facet params, then to never-blank.

---

## 7. MOBILE

Mobile is the primary target. The desktop layout is the enhancement.

- **The tray as a bottom sheet, with an explicit peek-vs-expanded action hierarchy.** The facet tray is a bottom sheet. **At peek** (always visible): `selectionLabel` + the live count + `Clear all` + `Copy this view` + `New here?`. Copy rides at peek because it is the viral loop (§6); Clear-all is the always-available escape; the count and label are the persistent scent. **On expand** (drag up or tap the handle): the full three-group facet stack (one titled group demanded at a time, see Density below), plus `Show the breakdown` and `Inspect a ball`. The sheet scrolls internally; `env(safe-area-inset-bottom)` respected; the peek readout never scrolls away.
- **The panel as a bottom sheet.** Show-the-breakdown opens the linked panel as a second bottom sheet (worm, Manhattan, leaderboard stacked vertically, one under the next, each with its orient line). It overlays the tray sheet; closing it returns to the tray. Never side-by-side on a phone.
- **The flag rail.** A horizontally scrolling rail (or a dedicated tab of the tray sheet labelled `Take a tour`), snap-scrolling one card at a time, with `scroll-padding` so the first and last cards clear the edges and a right-edge fade signaling more. Each card is a full 44px+ tap target. Arrow-key nav still works for external keyboards.
- **Tap targets.** Every control, chip, card, and the sheet handle is ≥44px. Chips wrap to multiple rows rather than shrink below 44px. The typeaheads use the native mobile combobox (the OS picker), so the datalist of 860/672 names is scrollable and searchable without custom JS.
- **The field stays tappable behind the sheets.** The sheets do not cover the whole field; a tap on the exposed field still fires a pick (the R1b `touch-action: pan-y` + `onclick` rule holds, so a vertical drag on the sheet or the field scrolls rather than picks).
- **Density and temporal coupling.** No more than the peek readout + one titled facet group (`Where & when` / `What happened` / `Who`) is demanded of the reader at once; that rule governs the expanded sheet too (the groups reveal progressively, not all at once). The tour rail is the low-effort entry, the full tray the high-effort one. On mobile the field and the sheets are mutually exclusive, so the field-panel link is TEMPORAL not spatial: the breakdown reflects the latest commit each time it is opened, and shows its updating state (§5) if it is still catching up.

---

## 8. Demand-mode + keyboard/a11y invariants (restated as an audit surface)

- **One commit per change (invariant 3).** Every facet change, flag tap, clear-all, and URL restore is exactly one `setFilter` OR one `setFilterMask` (one committed result). The optional field change cue (§0.4) is a single bounded self-terminating transition to that one result, not a second commit and not a loop. No render fires on a typeahead keystroke (only on a resolved selection). The panel recompute is one masked pass, panel-open-gated. The GPU is provably idle once the cue settles (no persistent rAF, no scrub, no set-piece budget spent).
- **Mask-vs-scalar (invariant 2)** is chosen once per commit by `buildFacetMask`; the two paths are mutually exclusive; the scalar path stays byte-identical to R1b.
- **Keyboard (invariant 10, §0.5).** Full tab order through the tray; segmented controls are arrow-navigable radio groups; chips are Space-toggle buttons with `aria-pressed`; the wicket toggle is its own Space-toggle button (a separate control from the chips, §2); typeaheads are native comboboxes; the flag rail is arrow-navigable; the panel is a labelled dialog; the tooltip is Escape-dismissable; the Inspect-a-ball keyboard inspector honors the mask via the CPU `pointVisible` mirror.
- **Keyboard focus management (small, load-bearing).** On a zero-count commit, focus moves to (or is announced and becomes the next tab stop for) the empty-card recovery button (§3), so a keyboard reader lands on the fix. Flag-rail arrow navigation scrolls the focused card into view (focus-scroll coupling), so no focused card is clipped under an edge. The `More filters` disclosure is keyboard-expandable and its active-facet badge (§2) is in tab order and reachable, so an active facet inside it can be found and changed by keyboard.
- **A11y.** `aria-live="polite"` on the count and the copied-confirmation; `aria-pressed`/`aria-expanded` on toggles and the panel button; visible `:focus-visible` rings everywhere; no hover-only content; the empty-state and copied confirmations are `role="status"`. Color is never the sole carrier of a read (the count's ember-on-zero is backed by the empty card's text; the Manhattan's wicket caps are backed by the "red caps are wickets" orient line).
- **Never-blank (invariant 4, §3)** is enforced in `commit()` before any apply, so no path (facet, flag, clear-all, URL) can blank the field.

---

## 9. Surface list (the instrument's UX surfaces)

1. **The intro / handoff card** (§1): orient + the three affordances, fades to a gap.
2. **The facet tray** (§2): the control surface; single `commit()` write path.
3. **The never-blank empty-state card** (§3): the "0 balls" guard + one-tap recovery.
4. **The tour-flag rail + flag cards** (§4): ~10 one-tap curated views; the onboarding door; deep-link entries.
5. **The linked breakdown panel + desktop coupling strip** (§5): worm + Manhattan + leaderboard of the current selection, fronted on desktop by an always-on slim strip (count + a one-line selection thread) that keeps the coordination co-visible with the field and expands into the full panel.
6. **The share affordance** (§6): Copy this view + shareable-URL restore.
7. **The tap-a-ball tooltip + keyboard inspector** (carried from R1b, honors the mask): names the exact delivery.
8. **The mobile bottom sheets** (§7): the tray and the panel as sheets, the flag rail as a scroll/tab.

---

## 10. File-by-file (the R6b extension plan, from the digest; for the build agent)

- **field/shaders.ts**: add `uFilterMaskTex` / `uFilterMaskTexW` / `uFilterMaskOn` uniforms next to `uPairingTex`; add the `passesFilter(gi)` mask branch (ANDs with the existing team/season/range/match test).
- **field/field.ts**: `setFilterMask(mask|null)` (one persistent R8 DataTexture, copy-bytes-and-flag, cheaper than dispose/recreate); the `pointVisible` CPU mirror (`if (appliedMask && appliedMask[i]===0) return false;`); `applyFilterUniforms` threading; keep `appliedMask` CPU copy.
- **field/types.ts**: `FieldFilter`/`RenderState` mask fields.
- **story/types.ts, story/fieldstate.ts**: `SceneFieldState.filterMask?`, threaded through `resolveSceneFilter` + `applyFilterUniforms` so a re-application re-uploads the SAME mask; `syncBowlHeld` stashes the last mask on `bowlHeld.filterMask`.
- **sandbox/data.ts**: extend `Facets` (league/team/season/phase/overLo/overHi/outcomes/batter/bowler/matchRange/mode); `buildFacetMask` (single pass, cheapest-first short-circuit, scalar-vs-mask decision); `phaseToOverRange`; name→dict-index maps built once on columnar load.
- **sandbox/Bowl.svelte**: the facet tray, clear-all, the flag rail + flag cards, the empty-state card, the panel toggle, the URL replaceState + restore, and the commit routing.
- **sandbox/url.ts** (ADD): `encodeFacets` / `decodeFacets`.
- **sandbox/panel/LinkedPanel.svelte** + **panel/select-stats.ts** (ADD): the worm/Manhattan/leaderboard + the one-pass `computeSelectionStats`.
- **pipeline/scenes.py**: `TOUR_FLAGS` module const + `resolve_tour_flags(matches)` (match flags resolve by identity with SystemExit guards; facet flags validate ≥1 ball, loud failure on 0); emit the `tourFlags` array in `scenes/sandbox.json`; rewrite the `scope` string (the facets are no longer "deferred to R6/R7"; R6b delivers them). **pipeline/tests/test_r1a.py**: assert the `tourFlags` shape + non-empty resolution.

---

## 11. Stage-name / label table (fan language for every control and facet)

| Concept | On-screen label / value (fan language) | Footnote-depth gloss (one click deep) |
|---|---|---|
| the whole instrument | `The Bowl` / `The field is yours` | the persistent 316,199-ball field as a filterable instrument |
| a dot | `one ball` | one delivery in the flattened corpus |
| league facet | `League`: `All` / `IPL` / `WPL` | league scope (re-scopes team + season lists) |
| team facet | `Team` (+ `All teams`); picked value reads batting-side, e.g. `RCB batting` | batting-side team via `team.u8` → `teams.json` (20 ids); the label always names the side so it claims only what the mask selects |
| season facet | `Season` (+ `All seasons`) | the calendar year, both leagues' groups for that year |
| phase facet | `When in the innings`: `The powerplay` / `The middle` / `The death` | powerplay = first six overs (over 0-5); the middle = overs 7-15 (over 6-14); the death = the last five overs (over 15-19) |
| over-range facet | `Pick your overs` (`Overs 1 to 20`), under `More filters` | explicit `overLo`/`overHi`, 0-based under the hood; one facet with the phase control, kept symmetric (setting overs clears phase; setting a phase mirrors its range in here); an active over-range badges `More filters · 1 active` |
| outcome facet | `What came off the bat`: `Dot` · `1` · `2 or 3` · `Four` · `Six` | the off-the-bat outcome class; chips OR within, AND against the rest |
| wicket facet | `...that took a wicket` (a separate toggle, divided from the chips) | the independent wicket bit; ANDs (not ORs) against everything, including the outcome chips; grouped apart so the OR/AND boundary is visible |
| batter facet | `Batter` (`Start typing a batter`) | one of 860 batters (`col.dicts.batter`) |
| bowler facet | `Bowler` (`Start typing a bowler`) | one of 672 bowlers (`col.dicts.bowler`) |
| both picked | `Bumrah to KL Rahul` (the duel chip) | batter faced by bowler |
| the live count | `{N} balls` | `buildFacetMask().count` / `countVisible` |
| the selection summary | `selectionLabel` (`RCB batting · 2016 · the death overs`) | the AND of the active facets in plain words; team reads batting-side; wraps to two lines / truncates-with-full-on-focus at max depth |
| clear | `Clear all` | reset to no facets, then re-apply never-blank |
| the panel | `Show the breakdown` | the linked worm + runs-per-over + leaderboard |
| the coupling strip | (desktop, always-on) count + one-line selection thread | the slim always-on link that keeps count + a worm sparkline / top scorer co-visible with the field; expands into the panel |
| worm view | `How the runs piled up` | cumulative runs over the selection in ball order |
| Manhattan view | `Runs in each over` (`the red caps are wickets`) | runs per over + wickets per over |
| leaderboard view | `Who did the damage` (`Top run-scorers` / `Top wicket-takers`) | top batters by runs, top bowlers by wickets in the selection |
| share | `Copy this view` (`Copied`), docked beside the readout and at mobile peek | `encodeFacets` URL to clipboard; elevated as the viral loop, outranks `Inspect a ball` |
| the tour | `Take a tour` (the flag rail) | ~10 one-tap curated pre-filtered views |
| onboarding re-entry | `New here?` | re-shows the intro's three-affordance line and points at the tour rail; the guidance is never lost on a timer |
| keyboard inspect | `Inspect a ball` | keyboard step through visible balls (mask-honoring) |
| empty state | `No balls here` / `Undo: {facet}` (names the facet it removes, e.g. `Undo: sixes only`) | the zero-count never-blank guard |

---

## 12. The tour-flag blurbs (verified counts; zero-em-dash re-authored copy)

The blurbs in `r6b_tourflags.json` carry em dashes and MUST ship in the re-authored forms below (invariant 11). Counts are data-bound to the emitted `tourFlags`; the label is the card hook.

| # | Flag id | Card label (hook) | Facets | Count (verified) | Blurb (ships, zero em dashes) |
|---|---|---|---|---|---|
| 0 | `final-2019` | The 2019 Final, ball by ball | match_index 755, range [178711,178958) (hide mode) | **247** | `Nine off Malinga's last over, and Mumbai win by one run. All 247 balls of the closest final there's been.` |
| 1 | `bumrah-rahul` | Bumrah's longest duel | bowler JJ Bumrah AND batter KL Rahul | **123** | `123 balls of India's deadliest yorker at its coolest head. Bumrah's most-bowled duel with anyone.` |
| 2 | `kohli-2016` | Kohli's record 2016 | batter V Kohli AND season 2016 | **655** | `The best single season the IPL has seen. All 655 balls Kohli faced in 2016, the summer he made 973.` |
| 3 | `wpl-all-sixes` | Every six in WPL history | league WPL AND outcome six | **705** | `Every maximum in the WPL, from the very first swing to now. 705 of them.` |
| 4 | `two-hundred-club` | The 200 Club | innings 1 AND that match's 1st-innings total ≥ 200 (computed 228-match mask) | **28,704** | `228 times a side has posted 200 batting first. Here's all 28,704 balls of it, up to the record 287.` |
| 5 | `wickets-2022` | Every wicket of IPL 2022 | league IPL AND season 2022 AND wicket | **912** | `The first season after the mega-auction reshuffle. All 912 wickets that fell across IPL 2022.` |
| 6 | `death-carnage-2023` | Death-overs carnage, 2023 to now | over ≥ 15 AND season in {2023-26} AND outcome in {four, six} | **4,470** | `Overs 16 to 20 in the Impact Player era. 4,470 fours and sixes launched at the death since 2023.` |
| 7 | `powerplay-six-explosion` | The powerplay six explosion | over ≤ 5 AND outcome six | **3,920** | `3,920 sixes in the first six overs, and the modern game nearly doubled the rate, from 1,106 back then to 1,934 now.` |
| 8 | `death-dot-storm` | The death-overs dot storm | over ≥ 15 AND outcome dot | **19,414** | `When the bowlers slam the door. 19,414 dot balls squeezed out in the last five overs.` |
| 9 | `shafali-wpl` | Shafali Verma in the WPL | batter Shafali Verma AND league WPL | **778** | `The WPL's biggest hitter, in full. All 778 balls Shafali Verma has faced, 53 of them sixes.` |

**Notes.** The spin-vs-pace flag is DROPPED (the corpus has no bowler-role field; `bowlerplane.u8` is economy/strike-rate, not spin/pace) and replaced by #8 the death-overs dot storm. The WPL flags (#3, #9) are framed as records and firsts, never as "behind." Batter/bowler in a flag are emitted BY NAME in `scenes/sandbox.json`; the client resolves name → dict index. #4 is a computed predicate mask (228 first-innings), not a contiguous range; the pipeline emits its point set. #0 reuses the existing match preset.

---

## 13. Verified-number index (single source for QA; every on-screen figure traces here)

| Figure | Value | Status |
|---|---|---|
| Total field | 316,199 balls | **verified** (corpus total; point order aligned 0/316,199 mismatches) |
| Distinct batters (typeahead source) | 860 | **verified** (`col.dicts.batter`) |
| Distinct bowlers (typeahead source) | 672 | **verified** (`col.dicts.bowler`) |
| Team ids (team facet) | 20 (15 IPL 0-14 + 5 WPL 15-19) | **verified** (`team.u8` → `teams.json`) |
| Seasons | 2008 to 2026 (19 IPL years, 23 season groups) | **verified** |
| Phase splits | powerplay 99,326 / middle 145,256 / death 71,617 | **verified** |
| Outcome counts | dot 108,887 / single 116,760 / two-three 19,990 / four 37,625 / six 16,468 / extras 16,469 | **verified** |
| Wicket flag (independent) | 15,752 | **verified** (can co-occur with a run) |
| Flag counts | 247 / 123 / 655 / 705 / 28,704 / 912 / 4,470 / 3,920 / 19,414 / 778 | **verified** (see §12; validated ≥1 ball at build) |
| Outcome codes | dot 0, single 1, two_or_three 2, four 3, six 4, extras 5 (+ wicket bit) | **verified** (six=4, four=3, the trap) |
| Phase over-ranges | powerplay [0,5], middle [6,14], death [15,19] (0-based) | **verified** |

---

## 14. QA checklist (instrument-level)

- [ ] **14-attribute gate (release-blocking).** The field's vertex-attribute count STAYS at 14; the mask is a single R8 data texture (`uFilterMaskTex`) plus two scalars, never a 15th attribute; the `passesFilter` mask branch ANDs with the existing team/season/range/match test; QA asserts the program compiles on-target and the field is not blacked out.
- [ ] **Scalar-vs-mask routing (invariant 2).** Team/season/matchRange-only selections take the R1b scalar path (byte-identical to R1b, mask null, zero mask cost); any phase/over/outcome/batter/bowler selection takes the mask path with scalars inactive; the two are mutually exclusive per commit; QA diffs an R1b-equivalent selection against the R1b build.
- [ ] **Demand-mode (invariant 3).** Exactly one committed field state per facet change / flag / clear-all / URL restore; the optional change cue is a single bounded self-terminating transition (~150 to 250ms) that settles to idle, NOT an rAF loop or scrub, and collapses to a static swap under `prefers-reduced-motion`; the count + label are the guaranteed primary feedback; no render on a typeahead keystroke; the panel recompute is one masked pass, panel-open-gated; the GPU is idle once the cue settles; `?hud=1` confirms no persistent idle renders.
- [ ] **Never-blank (invariant 4, §3).** No path (facet, flag, clear-all, URL, panel) blanks the field; a 0-count selection renders dim haze + the empty card + one-tap recovery, never a void; the empty card is non-modal and does NOT occlude the tray (the reader can also fix by hand); its recovery button NAMES the facet it removes (`Undo: sixes only`); the readout shows `0 balls` in ember; QA drives a known-zero combo (a non-meeting duel) and asserts the field still shows the haze.
- [ ] **AND-combining + scent (invariant 5, §0.2).** Facets AND (the outcome chips OR within, AND across; the wicket toggle is a SEPARATE control that ANDs, never a sixth OR-chip); `selectionLabel` reads the active facets as one plain sentence with null facets omitted and a team facet rendered batting-side (`RCB batting`); the live count matches `buildFacetMask().count`; the controls sit in the three titled groups (`Where & when` / `What happened` / `Who`); every active control is visibly lit and every control's effect is legible without hover.
- [ ] **One commit path (invariant 6).** Every writer goes through `commit()`; `syncBowlHeld` stashes the facets + last mask so a stray scroll re-applies the SAME view and never reverts the reader; a scripted scroll during an active selection is asserted not to change the field.
- [ ] **Data-bound numbers (invariant 7, §13).** Every on-screen count (readout, flag cards, panel, tooltip) traces to the columnar recount or the emitted `tourFlags`; QA asserts card count == emitted artifact for all ten flags.
- [ ] **URL supersedes never-blank (invariant 8, §6).** A facet or `fl=` hash on mount restores that exact view over the picked-team open; `replaceState` (not push) on every commit (no history spam); `decodeFacets` clamps/ignores unknown/out-of-range and never throws; a stale `v` falls back to the whole field; `Copy this view` writes the absolute URL and shows `Copied`.
- [ ] **Flags resolve non-empty (invariant 9).** All ten flags resolve to ≥1 ball at build (loud failure on 0); the spin-vs-pace flag is absent; #8 death-dot-storm is present; the two WPL flags carry no "behind" framing.
- [ ] **Voice audit (invariant 11, binding).** ZERO em dashes in every reader-facing string incl. all ten re-authored flag blurbs (§12), the intro + the `New here?` re-entry line, the flag reflection coach line (`These filters made this view. Change any of them.`), the empty-state copy + the `Undo: {facet}` recovery label, the `...that took a wicket` control label, the three group titles (`Where & when` / `What happened` / `Who`), the panel orient + `Updating...` lines, the labels, and the confirmations; no bare stat jargon on any control (the powerplay is "the first six overs," the death "the last five," no economy/strike-rate/par as labels); orient before flourish; re-run at copy freeze against the FINAL emitted `scenes/sandbox.json` strings.
- [ ] **Mobile (§7).** Tray and panel are bottom sheets; the peek shows `selectionLabel` + count + `Clear all` + `Copy this view` + `New here?`, the expanded sheet reveals one titled facet group at a time plus `Show the breakdown`/`Inspect a ball`; the flag rail scrolls with snap + edge fade and the first/last cards clear the edges; every control/chip/card/handle is ≥44px; the field stays tappable behind the sheets; a vertical drag scrolls, never picks.
- [ ] **Keyboard & a11y (invariant 10, §0.5, §8).** Full tab order; segmented controls arrow-navigable; chips Space-toggle with `aria-pressed`; the wicket toggle its own Space-toggle button; typeaheads native comboboxes; flag rail arrow-navigable; panel a labelled dialog; tooltip Escape-dismissable; the keyboard inspector honors the mask; `:focus-visible` everywhere; `aria-live` on the count and the copied confirmation; color never the sole carrier of a read; no hover-only content; on a zero-count commit focus moves to the empty-card recovery; flag-rail arrow nav scrolls the focused card into view; the `More filters` disclosure is keyboard-expandable and its active-facet badge is reachable.
- [ ] **Panel coordination (§5).** The panel consumes the SAME mask the field got; worm / Manhattan / leaderboard recompute on mask change in one pass; the desktop coupling strip keeps count + a one-line thread co-visible with the field and plays a coordinated transition with the field's change cue; the panel shows a legible `Updating...`/skeleton state while a large recompute (28,704 or 316,199 balls) trails the instant field re-mask, and never shows stale numbers as current; each view orients before it labels; the leaderboard's empty wicket list shows a plain line, never an empty box; a selection driven to zero shows the panel's own loosen-a-filter line.
- [ ] **Pixels-match-copy.** The lit balls are exactly the selection the count and label describe; a caption/label may only claim what the mask actually selects (a team facet reads `RCB batting`, never a bare `RCB` that would claim all of a team's balls); the flag card's count equals the balls that light up.

---

## 15. Owner-call notes (decisions this spec makes; for sign-off before build)

1. **The never-blank ZERO branch renders dim haze + an empty card, not a hidden field** (§3). A 0-count selection is shown as the whole field dimmed (not blank) with a specific, data-bound empty card, a non-modal card that does not occlude the tray, and a one-tap recovery that names the facet it removes (`Undo: sixes only`). This is the spec's reading of the never-blank rule applied to an empty facet combo; confirm before build (it is the one behavior the digest names but does not fully resolve).
2. **The tour rail is the onboarding door and leads with human hooks** (§4). Default order: the 2019 final, the Bumrah-Rahul duel, Kohli's 2016, then the aggregate-pattern flags. Flags are starting points the reader can then tweak (a flag tap sets facets the tray then reflects), not locked modes. Confirm the order and the "tweakable" behavior.
3. **The ten flags ship with the §12 zero-em-dash blurbs, replacing the em-dash forms in `r6b_tourflags.json`** (invariant 11). The counts are unchanged and data-bound; only the prose is re-authored. Spin-vs-pace stays dropped; #8 death-dot-storm ships in its place.
4. **The team facet is batting-side in v1** (§2, §11). A bowling-side team facet is deferred; the footnote-depth blurb says so. Confirm v1 scope.
5. **The over-range and the phase control are one facet, kept symmetric** (§2). Setting an over-range clears phase to `All`; setting a phase MIRRORS its resulting range into the over-range inputs (`The death` shows `Overs 16 to 20`). The UI never lets the two contradict when both are on screen. Confirm this two-way mirror over the alternative (phase as a coarse preset that the over-range one-way refines).
6. **The panel opens on demand and recomputes only while open, with a visible updating state and an always-on coupling strip** (§5, invariant 3). If the single masked pass ever janks on the largest selections (the 200 Club's 28,704 balls or the whole field's 316,199), it stays panel-open-gated and debounced to the committed state, and shows an `Updating...`/skeleton state so the momentary lag reads as catching up, not disagreeing. A slim desktop coupling strip keeps the count + a one-line selection thread co-visible with the field even when the full panel is closed. Confirm the gate + the strip is acceptable versus an always-live full panel.
7. **The shareable URL encodes batter/bowler by DICT INDEX with a `v=1` guard** (§6). A dict-reordering rebuild invalidates stale links safely (falls back to the whole field). Confirm the version-guard-and-fallback over encoding names (longer, but rebuild-stable). The wicket toggle, now a separate facet, encodes as its own `wk=1` key (not a letter folded into `oc`).
8. **Every commit plays a single bounded one-shot field change cue** (§0.4, invariant 3 as amended). Because a small facet delta re-masks a dim 316k field almost invisibly, the field plays a ~150 to 250ms self-terminating crossfade/pulse on the balls that entered or left the bright set, so the change is perceptible on the hero surface. It is NOT an rAF loop or a scrub, it settles to idle, and it drops to a static swap under `prefers-reduced-motion` (the count + label remain the guaranteed feedback). Confirm this narrow, self-terminating exception to "one static frame per change" is acceptable, or fall back to count+label-as-primary with the field ambient.
9. **The wicket toggle is pulled out of the outcome OR-chips into its own AND control, and the team facet renders batting-side** (§2, §0.2). Wicket combines differently (ANDs) from the outcome chips (OR), so it gets a separate, divided control rather than a sixth chip that would imply the same combine rule; the team value and `selectionLabel` always read `RCB batting`, so a label never claims all of a team's balls when the mask is batting-side only. Both are honesty fixes the cognitive-design review flagged as build-blocking; confirm the wording.

**The three that must settle before build starts** (they define the mask contract and the never-blank behavior): (1) the 14-attribute mask-texture approach and the scalar-vs-mask routing (invariants 1, 2), already verified in the digest; (2) the ZERO-count dim-haze-plus-card behavior (owner-call 1); (3) the flag set, order, and the re-authored blurbs (owner-calls 2, 3). None changes the instrument's shape; they fix its edges. The cognitive-design review adds two build-blocking honesty fixes that need no separate sign-off round but MUST land (they mislead a reader otherwise): the Wicket-out-of-the-OR-group separation and the batting-side team label (owner-call 9); plus one edge that touches the demand-mode invariant: the one-shot change cue (owner-call 8).
