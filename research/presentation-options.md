# Presentation Options — IPL/WPL Evolution Explorer

Synthesized from four research tracks (scrollytelling stacks, immersive/WebGL rendering, data-compute architecture measured on this repo's actual data, and interaction/narrative patterns). Dataset ground truth used throughout: **316,388 deliveries, 1,331 matches, 23 seasons (IPL 2008–2026 + WPL), 938 players**, flattened from ~110 MB of Cricsheet JSON; the entire flattened dataset compresses to **~0.81 MB gzipped** columnar JSON or **1.18 MB** zstd Parquet.

---

## Section 1: The Landscape

### Track 1 — Scrollytelling stacks (what the newsrooms actually use)

**The genre has a house stack, and it fits this project exactly.** SvelteKit statically prerendered + a ~30-line IntersectionObserver `Scrolly` component + D3 used only for scales/interpolators is what The Pudding, ONS, and ABC Australia ship with; NYT graphics has run on Svelte since ~2019. The reactive model ("scroll step N drives chart state X") is the cleanest mental model for a solo builder pairing with AI, and bundles stay tiny for static hosting.

- The Pudding's starter (includes `Scrolly.svelte`): https://github.com/the-pudding/svelte-starter
- Exemplar of the genre (martini glass in practice): https://pudding.cool/2024/11/love-songs/
- Newsroom templates: https://github.com/onsvisual/svelte-scrolly, https://github.com/abcnews/svelte-scrollyteller
- Minimal path (one-chapter prototype): Scrollama v3 + D3, no framework — https://github.com/russellsamora/scrollama, rationale at https://pudding.cool/process/how-to-implement-scrollytelling/

**GSAP is now 100% free** (Webflow acquisition, Apr 2025 — https://webflow.com/updates/gsap-becomes-free) and is the tool for *scrubbed* cinematic scenes (pinning, `scrub: true`, timelines): https://gsap.com/scroll/. But scrub-animating thousands of data marks through GSAP is a trap — tween a single progress value and redraw canvas yourself. Use GSAP surgically for 2–3 set pieces, not as the backbone.

**Other notes worth keeping:**
- React/Motion is only preferable if the owner is already fluent in React; bundles run 5–15× Svelte's and there are almost no newsroom scrolly templates to crib. https://motion.dev/docs/react-scroll-animations
- Native CSS scroll-driven animations (`animation-timeline: scroll()/view()`) are free compositor-thread polish for parallax/progress chrome — enhancement only, never load-bearing (Firefox still lagging). https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations
- Observable Framework's **data-loader pattern** (build-time scripts emit per-scene JSON/Arrow; the deployed site is pure static files) is the right pipeline discipline — adopt the pattern in Python/DuckDB build scripts, skip the tool. https://github.com/observablehq/framework
- Information architecture: Segel & Heer's **martini glass** (authored linear stem → free-exploration bowl) dissolves the scrollytelling-vs-data-world dilemma — it's both, sequenced. Paper: https://sunzhida.github.io/reading_note/9.pdf
- Mobile discipline from The Pudding (the IPL audience is overwhelmingly mobile): mobile-first, no CSS `vh`, stack to static charts where animation isn't load-bearing, no hover-dependent content, honor `prefers-reduced-motion`. https://pudding.cool/process/responsive-scrollytelling/

### Track 2 — Immersive rendering and the "data world"

**The single strongest technical idea across all research: one persistent WebGL particle field, one point per delivery, morphing between precomputed layouts.** 330k points × ~6 float attributes ≈ 8 MB of GPU data loadable as one binary Float32Array; a vertex shader interpolates source→target positions so the whole dataset rearranges in one draw call. Object constancy — watching the *same* balls migrate — is the most powerful device for making evolution feel physical.

- Foundational technique writeup (100k points with regl): https://peterbeshai.com/blog/2017-05-26-beautifully-animate-points-with-webgl-and-regl/
- Fly-through data worlds, and their limits: https://stars.chromeexperiments.com/ (100,000 Stars), https://cprimozic.net/blog/building-music-galaxy/ (solo-built; author had to add a guided tour because free-roamers never found the insights)
- Scroll-choreographed WebGL (the recommended fusion): https://tympanus.net/codrops/2025/11/19/how-to-build-cinematic-3d-scroll-experiences-with-gsap/, https://awards.journalists.org/entries/the-fine-line/ (NYT's The Fine Line — gold standard of guided immersive sports storytelling)
- deck.gl with OrthographicView is the low-shader-work fallback (picking/tooltips/transitions built in; ~60fps to ~1M points) but its aesthetic defaults read "dashboard": https://deck.gl/docs/developer-guide/performance

**Hard-won cautions:**
- **Literal 3D cricket is ruled out.** Cricsheet-style data has events, not tracking coordinates — no ball flight, no wagon-wheel angles. Statcast 3D works because pitch trajectories are physical (https://baseballsavant.mlb.com/visuals/pitch3d); faking stadium 3D from event data is exactly when 3D becomes a gimmick. Keep the camera 2D/2.5D (orthographic, gentle parallax), because depth should only encode real quantities.
- **A hybrid rendering contract is mandatory, not optional:** WebGL plane for the 330k marks; SVG/HTML plane for axes, labels, story cards, tooltips — sharing one projection so they stay registered. Cricket storytelling lives on names ("Dhoni, final over, 2011") and names must be DOM, not GL sprites. Pattern: https://blog.scottlogic.com/2020/05/01/rendering-one-million-points-with-d3.html; drei `<Html>` label limits: https://github.com/pmndrs/react-three-fiber/discussions/3130
- Per-point React components are a trap in r3f — data bypasses React via buffers/refs.
- WebGPU is a later one-line renderer swap in three.js (production-ready with automatic WebGL fallback since r171), not a foundation decision.

### Track 3 — Data and compute architecture (measured on this repo's data)

This track benchmarked the actual dataset (scripts at `/private/tmp/claude-501/-Users-kushaldsouza-Documents-Projects-iplprogress/d0562d52-1cde-46d6-8e36-be2f0894941b/scratchpad/flatten.py` and `bench.mjs`). The numbers end the architecture debate:

| Question | Measured answer |
|---|---|
| Full build-time parse of all 1,331 matches | 1.2 s |
| Typical per-scene payload (23 seasons × 20 overs heatmap) | ~4 KB JSON |
| Entire dataset, gzipped columnar JSON | **0.81 MB** |
| One-time browser decode to typed arrays | < 100 ms; 4.8 MB in memory |
| Season run-rate full scan (316k rows, plain JS) | 0.96 ms |
| Per-batter strike-rate filter+group | 0.26 ms |
| Brushed crossfilter pass | 0.40 ms |
| Worst case (full batter×bowler matchup map) | 4.8 ms |
| DuckDB-WASM engine payload | 8.1 MB gzipped + 1–5 s cold start |

Every conceivable interaction fits inside one 60 fps frame with ~10× headroom, in plain JavaScript. The existence proof for the explore mode is 13 years old: crossfilter's flights demo — 231k rows, five coordinated views, <30 ms interactions, built in 2012 pre-WASM (https://square.github.io/crossfilter/). Arquero (~105 KB, https://idl.uw.edu/arquero/) or hand-rolled loops both work.

**Recommended data architecture (all tracks agree):** build-time precompute (Python or native DuckDB CLI — DuckDB belongs in the build script, not the bundle) emitting small per-scene JSON for narrative scenes, plus a lazily loaded ~1 MB columnar file decoded to typed arrays for the explore mode, plus binary Float32 layout buffers for any particle scenes.

### Track 4 — Interaction patterns, narrative devices, and anti-patterns

The pattern catalog, ranked by fit:

- **Martini glass / guided-tour-then-sandbox** — the overall architecture. Exemplars: https://ncase.me/trust/, https://www.fallen.io/ww2/, https://projects.fivethirtyeight.com/complete-history-of-the-nba/
- **Unit visualization** (every ball a visible mark) — signature-moment material, 2–3 scenes max. Exemplars: https://graphics.latimes.com/kobe-every-shot/ (30,699 shots on canvas), NYT "One Race, Every Medalist Ever" (https://www.nytimes.com/interactive/2012/08/05/sports/olympics/the-100-meter-dash-one-race-every-medalist-ever.html) — the "all eras on one axis" trick maps directly to overlaying 19 seasons of worms.
- **Ladder of abstraction** (balls visibly aggregate into overs → innings → seasons; the reader watches strike rate *become* a number) — the highest-value pattern for "make metrics feel understandable." Do it for 2–3 metrics max. http://worrydream.com/LadderOfAbstraction/, http://www.r2d3.us/visual-intro-to-machine-learning-part-1/
- **Time scrubbing with annotated timeline** (538-Elo treatment) for the macro season arc: https://projects.fivethirtyeight.com/complete-history-of-the-nba/
- **You-Draw-It / predict-then-reveal** — highest engagement per unit of build cost; ideal cold open ("draw the death-over run rate since 2008"): https://www.nytimes.com/interactive/2015/05/28/upshot/you-draw-it-how-family-income-affects-childrens-college-chances.html
- **Team-picker personalization** — cheapest engagement multiplier for a fandom audience; reader's franchise drawn bold everywhere, sandbox opens pre-filtered. Never gate content behind it.
- **Inline mechanism figures** (Ciechanowski/distill idiom) for 2–4 interludes — win probability, required-rate pressure — with preset buttons and defaults that carry the message: https://ciechanow.ski/, https://distill.pub/2016/misread-tsne/
- **Small multiples + brushing** — the workhorse; 19–23 seasons is textbook small-multiples cardinality.
- **Broadcast-native idioms as the visual substrate** — worms, Manhattans, wagon wheels are zero-teaching-cost for this audience; open with the familiar form, then perform one transformation on it. **Confirmed field gap: no canonical cricket scrollytelling piece exists** — the space is dashboards (Statsguru: https://stats.espncricinfo.com/ci/engine/stats/index.html is the anti-model). This project would be first of its kind.
- Win-probability content should ship as a **precomputed (over, wickets, required-rate) → P(win) lookup grid**, used retrospectively (replay famous chases), not as a live predictor — the predictor is a scope trap.

**Anti-patterns (the guardrails):** only 10–15% of readers click anything (Aisch/NYT); Archie Tse's rules — readers just want to scroll, assume no one sees a tooltip, and if you force a click, something spectacular must happen (https://www.fastcompany.com/3069008/the-problem-with-interactive-graphics). No scrolljacking/velocity hijack (https://www.nngroup.com/articles/scrolljacking-101/). No hover-only content (mobile-majority audience). Sandbox never opens blank — always pre-populated with a famous match. Every scene must land its point with scroll alone; interaction adds depth, never carries the thesis.

---

## Section 2: The WASM Verdict

**Skip Rust/WebAssembly entirely. The measurements make this unambiguous, not a judgment call.**

1. **The engine outweighs the data 7:1.** DuckDB-WASM is 8.1 MB gzipped with a 1–5 s cold start; the *entire* dataset it would query is 0.81–1.18 MB. Shipping it would mean downloading a query engine several times larger than every ball ever bowled in the IPL and WPL combined.
2. **There is no speed to add.** Plain JS over dictionary-encoded typed arrays answers every realistic interactive query in **0.26–4.8 ms** — already 10× inside a 60 fps frame budget. A generous 5× WASM kernel speedup saves under a millisecond, and wasm-bindgen boundary copies eat most of it.
3. **The data is precomputable by definition.** The project brief eliminates the one workload class WASM accelerates: heavy in-browser recomputation. No major newsroom data story at any comparable scale uses WASM for rendering or querying.
4. **It taxes the solo+AI iteration loop** — a second toolchain, edit-compile-reload cycles, harder debugging — for zero user-visible benefit. Rendering performance lives on the GPU either way; Rust cannot talk to the GPU faster than JS can.

**The honest crossover points:** DuckDB-WASM starts earning its 8 MB around 5–10M rows, multi-table joins, or a user-authored-SQL feature (Mosaic's 10M-flights demo is the existence proof: https://idl.uw.edu/mosaic/). A custom Rust→WASM kernel earns its toolchain only for per-frame iterative numeric work — e.g., a future live Monte-Carlo win-probability simulator replaying thousands of matches under a scrubber, or an O(n²) force layout — and even then as one small kernel, never as the architecture. If Rust is *fun*, use it offline in the build pipeline emitting static Float32/Arrow files. WebGPU, similarly, is a later one-line renderer swap, not a decision to make now.

---

## Section 3: Experience Concepts

Five genuinely distinct shapes. All share the same data pipeline (build-time precompute + optional 1 MB typed-array payload), so switching between them mid-project loses little.

---

### Concept 1: "Season Ticket" — the visual essay
*Narrative-first · 2D · scroll-stepper*

**The pitch.** A Pudding-grade scrollytelling essay — the first great cricket visual essay, full stop. Chapters walk the 2008→2026 evolution (the scoring explosion, the death-over revolution, spin's arc, the WPL's arrival), each built on a broadcast-familiar chart form that gets one transformation performed on it. Every chapter ends by unlocking its graphic as a free-play widget; the piece closes with a compact explorer pre-filtered to your team.

**First three minutes.**
- *0:00–0:30* — Cold open: "Before we show you anything — draw it." A You-Draw-It canvas asks the reader to sketch how first-innings 200+ totals changed since 2008. Their line stays on screen as the real curve is revealed against it.
- *0:30–1:15* — Team picker (skippable, "neutral" offered). Scroll into Chapter 1: a sticky season run-rate chart; text steps annotate rule changes (fielding restrictions, impact player) as vertical flags; the reader's franchise is drawn bold, others ghosted.
- *1:15–2:30* — First signature canvas scene: every six ever hit appears as one dot on a seasons axis, sparse in 2008, a monsoon by 2025. Steps recolor by phase of innings to show *where* in the innings the sixes moved.
- *2:30–3:00* — The chapter's chart unlocks: "Try it — filter by phase, venue, or team." A one-line tease scrolls Chapter 2 into view.

**Stack.** SvelteKit (static prerender) + The Pudding's `Scrolly` component + D3 scales + LayerCake; one Canvas 2D layer for unit-viz scenes (sampled/aggregated where needed); Python/DuckDB build scripts emitting per-scene JSON; CSS scroll-driven animations for chrome; GSAP optionally for one pinned title sequence.

**Effort.** Medium. Every ingredient has an open newsroom template; per-chapter cost is predictable.

**Trades off.** The immersion ceiling — it reads as a great *article*, not a *place*. All-330k-points-simultaneously-morphing money shots are out of scope (Canvas 2D animates ~10–50k marks comfortably), so hero scenes sample or aggregate. Lowest wow-per-share of the narrative options.

**Presents best.** Season-over-season trend metrics (run rates, boundary %, phase splits), distribution shifts, annotated rule-change causality, team arcs via personalization.

---

### Concept 2: "Every Ball Ever" — the particle field
*Hybrid (narrative spine → sandbox) · immersive 2.5D · scroll-choreographed WebGL*

**The pitch.** All 316,388 deliveries exist as one persistent WebGL point cloud that never unmounts. Scrolling morphs the *same* points between precomputed layouts — season columns, over-by-over innings arcs, phase grids, matchup matrices — so "the death-over revolution" is something you watch happen to the very balls that constitute it. The story ends by handing you the field: the full cloud becomes a filterable sandbox. This is the concept only this dataset can support, and the one nobody has built for cricket.

**First three minutes.**
- *0:00–0:40* — Black screen. Deliveries stream in season by season with a live counter — 2008… 2012… 2026 — until all 316,388 hang as a shimmering field. Title sets over it: *Every ball ever bowled in the IPL and WPL.*
- *0:40–1:30* — First scroll: the cloud pours into 23 season columns. Scrubbing back and forth replays the morph under your thumb — the pile visibly swells and recolors as boundaries take over. A text card names the scoring explosion; a DOM annotation layer labels the seasons.
- *1:30–2:30* — Second morph: the same points rearrange into a 20-over × season grid. The death-overs corner ignites in boundary color decade by decade. Tap any point (GPU picking): a DOM tooltip names the exact ball — bowler, batter, match, result.
- *2:30–3:00* — The camera glides (gentle 2.5D parallax, orthographic) into Chapter 2: one famous final over isolated from the field, its six balls enlarged, scrub-able ball by ball with the win-probability worm drawing alongside.

**Stack.** three.js instanced Points (hosted in react-three-fiber, or three.js inside a Svelte shell) with vertex-shader source→target morphs; precomputed layout coordinates baked to binary Float32 buffers at build time (Python); GSAP ScrollTrigger (or R3F ScrollControls) driving progress uniforms; SVG/HTML annotation plane sharing one projection contract with the GL plane; typed-array explorer for the sandbox; static hosting throughout.

**Effort.** High — but it decomposes into shippable scenes, which is exactly the right shape for solo+AI iteration. The field + one morph is a weekend-scale proof.

**Trades off.** Choreography is the hidden cost (easily 50% of total effort — every transition is bespoke design work). The GL/DOM projection sync is real engineering. Mobile GPU behavior, thermal throttling, and `prefers-reduced-motion` static fallbacks must be designed in from day one, not bolted on. Each additional chapter is slower to author than in Concept 1.

**Presents best.** Anything expressible as re-layout of unit marks: volume and density shifts (sixes, dot balls, wickets by phase), era comparisons through object constancy, "the scale of the league" awe moments. Weaker for precise numeric comparison — those readings must be carried by the annotation plane.

---

### Concept 3: "The Observatory" — the explorable atlas
*Exploration-first · 2D · linked views with a guided tour overlay*

**The pitch.** The explorer cricket has never had: every worm, Manhattan, and phase heatmap for 1,331 matches, cross-filtered live from a ~1 MB in-memory dataset with sub-5ms response. It fixes Statsguru's failure mode (infinite queries, zero visual reward) by being visual-first and *never opening blank* — and a "tour" mode of authored annotation flags (the 538 Complete History pattern) walks newcomers to the good stuff.

**First three minutes.**
- *0:00–0:30* — Lands pre-populated with a famous match: its worm drawn with win-probability shading, Manhattan below, key balls flagged. No empty state, no query builder.
- *0:30–1:30* — Tour flag one: "2008 vs 2026." One tap snaps the season brush wide; every view updates in a frame; a small-multiple wall of 23 season-average worms fades in, the flattening-then-steepening arc plainly visible.
- *1:30–2:30* — The reader brushes overs 16–20 on the phase axis. The run-rate histogram re-shapes, the bowler leaderboard re-ranks, the season multiples re-scale — all live. They tap their team; it draws bold in every panel.
- *2:30–3:00* — Drill-down: clicking any season opens its authored mini-story card (champion, defining stat, one chart). A WPL toggle re-scopes everything.

**Stack.** SvelteKit or vanilla TypeScript; the full flattened dataset as one gzipped columnar JSON (~0.81 MB) decoded to dictionary-encoded typed arrays (<100 ms); hand-rolled aggregation loops or Arquero; Canvas 2D for dense marks, SVG for axes/annotations; authored tour flags as precomputed JSON; static hosting.

**Effort.** Medium. The compute layer is proven (crossfilter did this row count in 2012); the real cost is editorial — writing the tour and the per-season cards so exploring has a spine.

**Trades off.** Narrative reach: only 10–15% of visitors will interact, so the argument must live entirely in the tour defaults or most readers never receive it. Least shareable "wow." Permanent risk of drifting back into Statsguru-ness without ruthless curation. The "evolution" thesis is available but not *enforced* — readers can miss the point.

**Presents best.** Comparative and conditional metrics — any player vs any phase vs any venue, matchup matrices, team arcs — and the long tail of "but what about MY team in 2018?" questions that drive fan sharing.

---

### Concept 4: "Prime Time" — the data documentary
*Narrative-maximal · time-based, not scroll-based · broadcast register*

**The pitch.** A fallen.io-style paced film: chapters play on a directed GSAP timeline with narration captions (optionally audio), rendered in the visual language of a broadcast graphics package. The film pauses at explorable moments — "drag to compare any two seasons" — then resumes when you press play. It treats 18 years of T20 evolution the way a title-sequence director would, and it is the only concept where the author fully controls pacing, drama, and reveal order.

**First three minutes.**
- *0:00–0:45* — Auto-playing cold open: a single worm draws itself for the 2008 opener while captions set the scene — the night T20 changed cricket. The score ticks up like a broadcast scorebug.
- *0:45–1:45* — The film pulls back: that worm becomes one thread among 23 season-average worms stacking on a single axis (the "One Race, Every Medalist" device). Narration names the eras as annotation flags land. First pause point: a slider invites you to isolate any two seasons; play resumes on tap.
- *1:45–2:45* — Chapter two: the death-over revolution. A Manhattan skyline ignites era by era; the win-probability worm for a famous chase scrubs itself while captions explain what "required rate pressure" feels like.
- *2:45–3:00* — Interlude card: pick your team. The rest of the film draws your franchise bold in every scene.

**Stack.** GSAP master timelines (now fully free) driving Canvas 2D/SVG scenes; Svelte or vanilla shell; the same precomputed per-scene JSON; optional Web Audio narration track; chapter menu for random access; static hosting.

**Effort.** High. Autoplay pacing is the hardest editorial craft in this list, and every scene is bespoke motion design.

**Trades off.** Gives up reader pacing — the one interaction (scroll) with near-100% completion is replaced by the one (watch) that mobile attention punishes. Least explorable of all concepts; the pause-to-explore moments soften but don't remove that. Accessibility (captions, reduced-motion, seekability) is extra scope. Re-visiting a specific fact is clumsy without a strong chapter menu.

**Presents best.** Dramatic single-narrative metrics: win-probability swings in famous finals, record chases, era-defining discontinuities — told once, with maximum emotional force.

---

### Concept 5: "The Net Session" — the mechanism explorable
*Pedagogy-first · prose + inline reactive figures · no scroll choreography*

**The pitch.** A Ciechanowski/distill-style essay that teaches you to *read* cricket's metrics before anyone argues about them: prose with embedded figures where you drag required rate, wickets in hand, or field restrictions and watch win probability, pressure, and scoring value respond under your finger. Less about IPL history, more about making strike rate, economy-by-phase, and P(win) feel like physical mechanisms — the deepest answer to "make metrics FEEL understandable."

**First three minutes.**
- *0:00–0:40* — Opening figure: a single over as six empty slots. Tap each ball to score runs; strike rate recomputes live above your over. The number stops being a statistic and becomes something you *did*.
- *0:40–1:40* — The pressure figure: drag a chasing team's worm and watch the required-rate gap widen and the pressure gauge climb. Preset buttons — "Dhoni, 2011 final," "a 2024 powerplay" — jump to famous states, t-SNE-guide style, so no one faces a blank slate.
- *1:40–3:00* — The win-probability figure: sliders for over, wickets in hand, and required rate read from a precomputed P(win) grid built from all 1,331 matches. Prose explains why wickets dominate early and rate dominates late; each figure's default state is a publication-quality screenshot for the readers who never touch a slider (most of them).

**Stack.** Svelte (or vanilla) + D3; precomputed lookup grids (over × wickets × required-rate → P(win); phase-value tables) emitted at build time; sensible-default figures; no scroll choreography, no GL; static hosting.

**Effort.** Medium. No scroll or GL engineering, but each figure is a bespoke mini-app and the interaction design must be exact (Ciechanowski spends months per essay).

**Trades off.** Doesn't tell the 2008→2026 evolution story by itself — it's the pedagogy layer, not the history. Sliders are precisely what most readers skip, so the defaults carry everything. Low fandom-share energy (no "my team" hook unless added).

**Presents best.** Model-like and derived metrics: win probability, required-rate pressure, why strike rate beats average in T20, DLS intuition, phase-value trade-offs.

---

## Section 4: Recommendation

**Build "Every Ball Ever" (Concept 2), scoped with Concept 1's discipline, ending in a lightweight Concept 3 bowl.** Concretely: a SvelteKit (or R3F) static site whose spine is stepper-driven scroll chapters, with one persistent WebGL particle field used in three or four signature scenes rather than everywhere; GSAP scrubbing reserved for two set pieces (the opening field-assembly and one famous final over); Concept 1's You-Draw-It as the cold open and team picker early; one Net-Session-style win-probability interlude (precomputed lookup grid); and the particle field + a typed-array mini-explorer unlocked as the closing sandbox, pre-filtered to the reader's team and a famous match.

**Why this one:**

1. **All four tracks independently converged on the same architecture** — martini glass (authored stem, explorable bowl), stepper-default with sparing scrubs, precompute + typed arrays, hybrid GL/DOM rendering, no WASM. That convergence is the strongest signal in the research.
2. **Object constancy is the project's thesis made technical.** The goal is to make metrics *feel* understandable; watching the same 316,388 balls rearrange from raw deliveries into season columns into phase grids is the single strongest known device for that — and it is the one experience this dataset uniquely supports.
3. **The field is empty.** Research confirmed no canonical cricket scrollytelling or explorable essay exists — only dashboards. First-of-kind status justifies aiming above a conventional essay (Concept 1), while the fandom audience justifies the explorer bowl.
4. **The effort decomposes correctly for a solo builder + AI pair.** The particle field plus one morph is a weekend-scale proof; every chapter after that ships independently. And because all five concepts share one data pipeline, downshifting to Concept 1 (same chapters, canvas instead of GL) wastes almost nothing if the prototype disappoints.

**What to prototype first, in order, to de-risk:**

1. **The data pipeline (days, near-zero risk — Track 3 already validated it).** Commit build scripts (Python or DuckDB CLI) that flatten the Cricsheet JSON and emit: (a) per-scene aggregate JSON (KB each), (b) the full columnar dataset (~0.81 MB gz), (c) two binary Float32 layout buffers for the particle field (e.g., "raw field" and "season columns"). Track 3's `flatten.py`/`bench.mjs` in the scratchpad are the starting point.
2. **The particle-morph spike — the real risk gate (one weekend).** One three.js Points layer, 316k points, two precomputed layouts, scroll-scrubbed morph, plus a DOM label plane sharing the projection. Test on a mid-range Android phone, not just the dev laptop. Pass criteria: 60 fps through the morph, the transition *reads* (you can follow what the balls are doing), and labels stay registered. If it fails: drop to a stratified sample (~50k points) or Canvas 2D, or downshift to Concept 1 — the chapters survive intact.
3. **One complete chapter end-to-end (1–2 weeks).** Text steps, annotation plane, mobile layout, `prefers-reduced-motion` static fallback, and the end-of-chapter unlock. This prices the per-chapter cost honestly before committing to a chapter count — choreography, not compute, is where this project's budget lives.
4. **The bowl last.** The explorer reuses the field, the typed-array columns, and the chapter widgets; build it only after the stem proves out, and never let it open blank.

**Standing constraints from the research, restated as rules:** camera stays 2.5D/orthographic (no fake stadium 3D); every scene lands its point with scroll alone; no hover-only content; mobile-first with The Pudding's responsive rules; win probability ships as a lookup grid, not a live simulator; and no Rust/WASM anywhere in the browser (Section 2) — revisit only if a live Monte-Carlo feature is ever added, and then as one small kernel.
