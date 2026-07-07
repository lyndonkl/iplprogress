# Story Shell Contract — R1a (+ R1b field capabilities: §11 picking · §12 filtering; + R2a Ch 2: §13 worm-space · §14 run-out cascade; + R2b Ch 3: §15 frontier plane · §16 dismissal rivers; + MF §17 mobile "read, then watch" captions; + R3a Ch 4: §18 tide skyline + waterline; + R3b-2 Ch 5: §19 worth grid + pricelens · §20 over rail · §21 WPA highlight)

The scene system every scene builder codes against. The shell (this directory +
`lib/field/` + `lib/state/`) is owned by the story-shell architect; **scene
builders own only their directory under `src/lib/scenes/`** and the footnote
registry entries their scenes declare. If a scene needs something the shell
doesn't provide, the request goes to the shell — don't fork the field.

Sources of truth: `research/storyboards/r1a-storyboard.md` (scene-by-scene
implementation truth), `research/experience-blueprint.md` §2 (standing rules).

---

## 1. The model

The story is an **ordered list of scenes** composed into one scroll timeline
over **ONE persistent field renderer** (a 316,199-point `THREE.Points`; it
never unmounts). Each scene owns a scroll section; GSAP ScrollTrigger drives a
per-scene progress `p ∈ [0,1]`; the leading `morphLength` vh of the section
scrubs the field from the previous scene's `fieldState` to this scene's
`fieldState`, and the remainder holds (holding = zero renders — demand mode).

```
+page.svelte
  scenes = [...coldopen, ...picker, ...ch1, ...endcard]   // reading order
  <Story {scenes} onSceneChange /> + <ChapterNav />
```

## 2. SceneDef (lib/story/types.ts)

```ts
{
  id: string;                    // unique, stable; default hash anchor
  chapter: 'coldopen' | 'picker' | 'ch1' | 'endcard';
  anchor?: string;               // hash deep-link target (#coldopen, #picker, #ch1, #end)
  navLabel?: string;             // presence → listed in the chapter nav
  scrollLength: number;          // section height in vh
  morphLength?: number;          // leading vh that scrub the field morph
                                 //   default min(140, scrollLength);
                                 //   set = scrollLength for a whole-scene scrub
  fromState?: SceneFieldState;   // morph SOURCE override (default: previous
                                 //   scene's fieldState) — the assembly scene
                                 //   uses { layout:'assembly', reveal:0 }
  fieldState: SceneFieldState;   // the state this scene lands and HOLDS
  reducedMotionEndState?: SceneFieldState; // live jump-cut target (default fieldState)
  annotations: Component<SceneAnnotationProps>; // your DOM/SVG layer
  footnote?: FootnoteId;         // per-scene "how we computed this" sheet
}
```

### SceneFieldState — layout id + uniforms + subset filters

```ts
{
  layout: 'free' | 'columns' | 'wall' | 'assembly' | 'worms' | 'frontier'
        | 'tide' | 'worth';
  reveal?: number;    // assembly stream-in 0..1 (chronological by point index)
  dim?: number;       // global luminance ×, 1 = full (default 1)
  wplDim?: number;    // WPL-points luminance × (C1-2 shelf staging; default 1)
  labels?: number;    // season-columns DOM label plane opacity (default 0)
  highlight?: {       // uniform-driven subset: lift/tint points matching a class
    class: 'dot'|'single'|'twoThree'|'four'|'six'|'other'|'wicket'|'wpa';
    lift: number;     // world-units vertical lift (frustum y ∈ [-1,1])
    boost: number;    // brightness boost for matches (0..1)
    othersDim: number;// luminance × for everything else (1 = none)
    skipWpl?: boolean;// WPL points never match — they take the others path
                      //   (C1-5: the IPL's sixes lift; the WPL's stay shelved)
    wpaThreshold?: number; // ONLY with class 'wpa': min |ΔWP| 0..1 to match (§21)
  } | null;
  pricelens?: PriceLens | null; // per-cell price recolor over the worth grid (§19)
  overrail?: OverRail | null;   // the set-piece six-ball lift to rail slots (§20)
  teamIgnite?: boolean; // default true — the picked team STAYS lit (§2 rule)
  wallHeatMix?: number; // C1-2 thesis beat: 0 = outcome colour · 1 = era-relative
                        //   heat recolor (§10). Default 0. Drive 0→1 in the HOLD
                        //   via dynamicState; must be 0 wherever a re-sort engages.
}
```

Layouts are **in-shader** from per-point attributes; no positions cross the
wire. `free` = hash scatter — the IPL cloud fills the sky below a clear gap;
the WPL scatters into **its own constellation, upper-right sky, deliberately
apart** (storyboard CO-3; its upper→upper continuity into the wall shelf is
authored) · `columns` = season columns (centroid table + ordinal) · `wall` =
ignition wall (x = balls-faced 1..30+ from `ballsfaced.u8`, y = season row,
WPL rows on a separate shelf above 2026) · `assembly` = the free scatter
revealed chronologically as `reveal` scrubs 0→1 (the counter set piece; at
`reveal:1` it is position-identical to `free`, so assembly→free is seamless) ·
`worms` = Ch 2 worm-space (x = balls-faced 1..60+ from `ballsfaced.u8`, y =
cumulative innings runs from `cumruns.u8`, settled as a low-alpha density haze;
fixed data aspect ratio + letterbox — §13) · `frontier` = Ch 3 economy ×
bowling-strike-rate plane (x = bowler-season economy, y = bowler-season strike
rate, both from the interleaved `bowlerplane.u8`, settled as a low-alpha density
haze of dense bowler-season clouds; fixed data aspect ratio + letterbox — §15) ·
`tide` = Ch 4 innings-total skyline (x = season block + within-season packing,
y = a column filled to the innings total from `innings_total.u8`; reservoir haze
for non-first-innings balls — §18) · `worth` = Ch 5 state grid (every ball
condenses to the (over × wickets-down) cell it was bowled in, from `restate.u8`;
20 × 10, 0 wickets at the TOP; cell luminance = the pricelens price — §19).
All scalar fields lerp during the morph; highlight lift/boost/dim lerp so subsets
glide in and out.

**Every scalar here is luminance/position, never hue.** Hue is identity only
(team color, WPL family) — standing rule.

### Annotations component

Rendered inside your scene's `<section>` (height = `scrollLength` vh,
`position: relative`). Receives live props:

```ts
{ progress: number;          // 0..1 across your section, scrub-rate updates
  active: boolean;           // you own the field right now
  field: FieldHandle | null; // null until data loads — always guard
  reduced: boolean }         // prefers-reduced-motion: render end states only
```

Patterns:
- Pin content with `position: sticky; top: 0; height: 100dvh` inside your section.
- Caption-step by thresholding `progress` (one change per step, ≤45 words, ≤3 numbers).
- Sections are `pointer-events: none`; opt interactive elements back in
  (`.scene-card.interactive` or your own `pointer-events: auto`). **No
  hover-only content; tap targets ≥44px.**
- Shared card styles: `.scene-card`, `.overline`, `.note` (app.css).
- `field.projectToCss(x, y)` anchors DOM to field coordinates;
  `field.getWallLayout()` / `field.getColumnLayout()` expose geometry
  (row/column centres, wall extents) for axis labels and highlights.
- `assemblyVisibleCount(reveal, n)` (lib/story/fieldstate.ts) is the counter's
  source of truth — it mirrors the shader frontier exactly and can only end at
  the number the pixels show.

### Reduced motion (hard invariant)

The shell forces morph `t = 1` whenever `reduced` is true: the field
live-renders each scene's end state as a jump-cut (never baked frames —
personalization survives). Your annotations must also carry every point
without motion or taps: check `reduced` and render final states. If your
scene's held `fieldState` isn't the right jump-cut target, declare
`reducedMotionEndState`.

## 3. Field states you may NOT invent

- One controlling morph per chapter (morph budget). Ch 1's is free→wall.
  Everything else is a subset-highlight or a 2D annotation-plane scene.
- The on-screen ball count is **316,199** wherever pixels are visible; 316,388
  and the 189 super-over balls live in footnote sheets and /methods only.
- No statistical term of art in main flow (glossary rule) — technical names go
  in the footnote registry entry.
- WPL beats: two clocks in one beat; never "behind". WPL points may dim one
  stop (`wplDim`) only as authored staging (C1-2), restored where the brighten
  IS the beat (C1-6).

## 4. Footnote layer

`lib/story/footnotes.ts` is a typed registry (`FOOTNOTES`); add your entry and
reference it via `SceneDef.footnote`. The shell renders the per-scene
"ⓘ how we computed this" affordance and the accessible slide-over
(`FootnotePanel.svelte`: dialog, focus-trapped, ESC, tap/keyboard — never
hover; opening it **locks background scroll** so the field can't scrub under a
stray swipe). Every sheet carries a persistent **"Full methods →"** footer link
to `${base}/methods/` — the progressive-disclosure chain reaches the methods
page from any sheet.

Entries are plain-text `paragraphs` plus an OPTIONAL data-only `figure` slot
(`FootnoteFigure`) for a small static 2D exhibit (R1a: the `over-clock` radial,
C1-4). The figure is numbers + labels only — no markup — and the panel owns the
rendering; only plot values that trace to an artifact/§9 (the over-clock figure
marks only verified balls, never invented intermediates).

## 5. Reader state (lib/state/)

SSR-safe, localStorage-backed, typed; import from `$lib/state`:

| Store | Key | Holds |
|---|---|---|
| `sketch` | `ebe.sketch.v1` | `{skipped, values: number[14] \| null, branch, ts} \| null` — written by CO-1/CO-2 on reveal or skip |
| `pickedTeam` | `ebe.team.v1` | `{league: 'ipl'\|'wpl'\|null, team: name \| 'neutral', ts} \| null` — the shell maps it to the ignite uniform automatically |
| `chapterProgress` | `ebe.progress.v1` | `{scene: anchor, ts}` — written by the shell on scene change; powers the nav's Continue |
| `footnotesOpen` | `ebe.footnotes.v1` | open footnote id \| null — set it to open the panel |

No scene may gate content on any of these existing (deep links always work).

## 6. Nav & deep links

Scenes with `navLabel` appear in the persistent chapter nav (☰). The ☰ is
**visible in every scene — including the cold open — and never hidden**
(storyboard §6); it **dims to 40% opacity while a set-piece field morph is in
flight** (the assembly scrub and the ignition-wall morph) so it never fights a
set piece. The shell detects a set piece structurally (a layout change or a
reveal scrub) and passes `dimmed` to `<ChapterNav>` — no scene id is hard-coded.
Opening the sheet **locks background scroll**. Anchors are section ids; the
shell calls `ScrollTrigger.update()` on hashchange and honors an entry hash
after triggers mount. Future chapters are titles + `soon` tags in `navplan.ts`
— titles are commitments, numbers aren't.

## 7. File ownership map

| Path | Owner | Notes |
|---|---|---|
| `src/lib/story/**` | **shell** | scene system, orchestrator, footnote UI, nav, this contract |
| `src/lib/field/**` | **shell** | renderer, shaders, layouts, data loading — request changes, don't fork; subset re-sort capability in §9 |
| `src/lib/state/**` | **shell** | store schemas are contract; additions by PR to the shell |
| `src/lib/scenes/coldopen/` | cold-open builder | CO-1 draw · CO-2 reveal branches · CO-3 assembly + title card (replace `Assembly.svelte`/`Columns.svelte`) |
| `src/lib/scenes/picker/` | picker builder | TP tile screen (replace `PickerStub.svelte`; keep writing `pickedTeam`) |
| `src/lib/scenes/ch1/` | ch1 builder | C1-1..C1-8 (replace `WallStub.svelte`/`SixesStub.svelte`); scene data at `data/scenes/ch1.json`, cards at `data/payoff/ch1.json` |
| `src/lib/scenes/endcard/` | end-card builder | EC card copy/polish |
| `src/routes/+page.svelte` | **shell** | composition order only — builders export `scenes: SceneDef[]` from their `index.ts` |
| `src/routes/methods/` | shell (stub) | grows every release |
| `static/data/**` | **pipeline** | never hand-edited; fetch via `` `${base}/data/...` `` only |

Each scene directory's `index.ts` exports `scenes: SceneDef[]` in reading
order; `+page.svelte` concatenates the four exports. Replacing a stub =
replacing components/defs inside your directory. Never renumber another
directory's anchors.

## 8. Invariants your scene must not break (release checklist)

1. Demand-mode: no rAF loops of your own; the field renders only via
   `applyState`/`invalidate`. DOM animation is fine, but scrub-driven state
   belongs in `fieldState` or `progress`.
2. Payloads: new per-scene JSON must be in the pipeline ledger and inside the
   ≤2MB/chapter budget; fetch through `$app/paths` `base`. No new per-point
   buffers without a shell + pipeline change.
3. Reduced motion carries every beat; no beat requires a tap (interaction adds
   depth, never carries the thesis).
4. Mobile-first: bottom-anchored captions, thumb-safe zones, 44px targets.
5. `?hud=1` stays dev-only; zero HUD DOM on default load.
6. Byte-determinism and the numbers: every on-screen figure traces to a
   pipeline artifact or the storyboard's verified-number index (§9).

---

## 9. The subset re-sort capability (C1-5 fireworks — the signature moment)

A **reversible, in-shader re-sort** of one class of points into per-season
firework columns and back. It is a cross-cutting modifier (like the highlight)
— it composes with the base layout and does **not** spend a second controlling
morph; the free→wall morph remains Ch 1's only layout morph. No positions cross
the wire: the per-season stacking ordinal is derived on-device from `attrs` +
group ids the first time a class engages (cached; zero recompute on scrub).

### 9.1 Declaring it — `SceneFieldState.resort`

```ts
resort?: {
  class: HighlightClass;   // which points re-sort ('six' for C1-5)
  skipWpl?: boolean;       // WPL points stay on the wall (default false)
  columns?: 'ipl' | 'all'; // which season groups become columns
                           //   (default 'ipl' when skipWpl, else 'all')
  engage: number;          // 0 = base layout · 1 = fully stacked in columns
  lift?: number;           // world-units peak of the flight arc (default 0.5)
  tint?: number;           // two-tone recolor strength 0..1 (default 0)
  othersDim?: number;      // luminance × for everything else (default 0.12)
} | null;
```

**How it animates.** `engage` lerps like any scalar during the scene's morph:
the scene that DECLARES the re-sort pulls `engage` 0→1 (matching points fly out
of the wall, arc up — staggered per point so each traces one continuous path,
object constancy — and stack into their season's column, height = that season's
count). The **next scene declares no `resort`**, so `engage` lerps 1→0 and the
points settle back onto the wall — the reverse leg is free. The two-tone recolor
is a per-point **luminance** split within the class hue (never a second hue),
driven by `attrs.u8` **bit 5** (= hit by that season's top-10 six-hitter):
top-10 bright, everyone else dim, weighted by `tint`.

### 9.2 The two-tone recolor is a caption STEP → use `dynamicState`

The recolor lands during the HOLD (after the morph), as a one-change caption
step — so it can't ride the morph. Drive it with the optional
`SceneDef.dynamicState(progress, held)`, which the orchestrator resolves the
held state through on every tick (and which the settle-back reads at progress 1
so there is no pop). It may only touch scalar aspects — never a new layout:

```ts
{
  id: 'ch1-sixes',
  scrollLength: 170, morphLength: 70,
  fieldState: {
    layout: 'wall', wplDim: 0.55,
    resort: { class: 'six', skipWpl: true, engage: 1, lift: 0.5, othersDim: 0.12, tint: 0 }
  },
  // reduced motion jump-cuts straight to the stacked, two-toned columns:
  reducedMotionEndState: {
    layout: 'wall', wplDim: 0.55,
    resort: { class: 'six', skipWpl: true, engage: 1, lift: 0.5, othersDim: 0.12, tint: 1 }
  },
  // step 3's one change: raise the two-tone tint once the caption crosses its
  // threshold (the field re-renders once — demand mode holds):
  dynamicState: (progress, held) => ({
    ...held,
    resort: { ...held.resort!, tint: progress >= 0.8 ? 1 : 0 }
  }),
  annotations: Fireworks,
  footnote: 'sixes'
}
```

The following scene (`ch1-wpl`) declares **no** `resort` → the columns dissolve
back to the wall as its morph runs. (It keeps `layout: 'wall'`.)

### 9.3 Anchoring DOM column labels — `field.getResortLayout()`

Returns `null` until a re-sort has engaged, then:

```ts
{
  xs: number[];      // world x of each group's column centre, indexed by gi (NaN = no column)
  counts: number[];  // subset point count per gi (the column's raw height)
  bottom: number;    // world y of the column base
  usableH: number;   // world height at the tallest column
  invMax: number;    // 1 / max subset count
  gis: number[];     // gi's with a column, in season order
}
```

Column top for group `gi` (world) = `bottom + counts[gi] * invMax * usableH`;
project it with `field.projectToCss(xs[gi], top)` to place a `2008 / 2023 / 2026`
label exactly over its column of points. Rebuilt on resize.

### 9.4 Pipeline dependency (integration)

The two-tone tint reads `attrs.u8` **bit 5** (mask `0x20`). Until the pipeline
re-encodes that bit (season-top-10-six-hitter flag), it reads 0 everywhere and
the re-sort degrades gracefully to a single-tone column. The re-sort itself
(positions, columns, arc) needs no new bytes.

---

## 10. The era-relative recolor (C1-2 thesis beat)

The ignition wall positions every ball by (balls-faced → x, season → y) and by
default colours it by **outcome** (dot → blue … six → red). That produces a
strong left→right strike-rate gradient — batters accelerate once set in every
era — which visually **drowns out** the chapter's actual thesis: the *early*
balls got more aggressive over the YEARS. The recolor is the fix (owner-approved
"colour by era, not outcome").

**What it is.** A per-point attribute `aWallHeat` (from `wallheat.u8`, one byte
per point, same order as `ballsfaced.u8`, uploaded NORMALIZED to 0..1) encodes
how hot a ball's **(season × clamped balls-faced) cell** strike rate runs versus
the pooled **IPL 2008-2010** batter at the **same ball-index**. Baselining each
ball-index column to its own 2008-2010 value **removes the horizontal
acceleration gradient**, leaving only the era difference — so the early-ball
corner ignites bottom→top exactly where recent seasons most exceed 2008.

**How a scene drives it.** `SceneFieldState.wallHeatMix` (0 = outcome colour, 1 =
era-relative) → uniform `uWallHeatMix`. In the shader the final base colour is
`mix(outcomeColour, heatColour(aWallHeat), uWallHeatMix)`, where `heatColour` is
a DIVERGING ramp about `WALLHEAT_NEUTRAL` (= the pipeline's neutral byte 73/255,
the 2008-2010 batter): cool deep-blue below → neutral grey-blue at it → amber →
six-red well above, reusing the outcome palette constants. **Team-ignite still
wins on top** (personalization survives). At `wallHeatMix: 0` the mix is a no-op,
so the establishing outcome shot AND the C1-5 fireworks two-tone are
pixel-identical — this is the ONE authored place hue encodes a quantity, gated
entirely to the beat.

**Staging (invariants).** The beat runs in the wall scene's HOLD (post-morph),
so drive `wallHeatMix` 0→1 from `dynamicState(progress, held)` — it can't ride
the free→wall morph. The next scene declares `wallHeatMix` 0 (default), so it
lerps back to 0 as that scene morphs in — the settle-back is free, and the heat
is 0 well before the fireworks lift. It must be **0 wherever a re-sort is
engaged**, and the fireworks scene keeps it 0 (a dev-only `field.ts` assertion
warns if both are non-zero). Reduced motion jump-cuts to the beat's rest
position (`reducedMotionEndState.wallHeatMix: 1`), rendered live. Scenes name the
diverging scale on screen (a legend built from `ch1.json`
`ignition.wallheat.legend_labels`).

**No new position buffers.** The recolor is a per-point colour blend only; the
one new byte (`wallheat.u8`, ≈316KB raw / tens of KB gz) is in the pipeline
ledger and inside the Ch 1 budget.

---

## 11. GPU picking on the 316k-point field (R1b — the Bowl's tap-a-ball)

Tap/click/keyboard-select recovers the exact field point the reader aimed at,
so the sandbox can name the delivery (bowler · batter · match · result). The
platform returns only the **point index**; the scene reads the delivery's
metadata from the columnar sandbox dataset at that index (§12.4).

### 11.1 `field.pickAt(cssX, cssY, radiusPx?) → number | null`

```ts
const idx = field.pickAt(ev.offsetX, ev.offsetY);      // tap → point index
if (idx != null) showTooltip(idx);                     // null = empty space
```

- `cssX` / `cssY` are CSS px **inside the field container** (a pointer event's
  `offsetX/offsetY`, or `clientX/Y` minus the container rect).
- Returns the **nearest VISIBLE point** to the tap within the pick radius, or
  `null`. Radius defaults to the full patch (≈10 CSS px at DPR 2); pass a
  smaller `radiusPx` to tighten it (finger vs. mouse).
- **Filtered-out points are never pickable** — the pick pass honours the exact
  same facet filter as the visible field (§12), and not-yet-assembled points
  (assembly reveal) are excluded too.
- **How (demand-mode, hard invariant):** one render of a tiny `PICK_PATCH`×
  `PICK_PATCH` offscreen target under the tap **plus one 1-shot pixel readback,
  fired only on the event** — never a persistent loop. It renders to an
  offscreen target, so the visible canvas and the demand-mode frame counter are
  untouched; idle GPU stays ~0. Each point is drawn as a solid square encoding
  `index+1` as 24-bit RGB; the readback returns the nearest painted pixel to the
  tap centre.

### 11.2 Keyboard select — filter-aware, no GPU

For "no hover-only content; works by keyboard" (blueprint §2). Two helpers walk
the **visible** set (they mirror the shader filter on the CPU, so they never
return a hidden ball):

```ts
field.firstVisiblePoint(): number | null           // first visible ball, chrono order
field.stepVisiblePoint(fromIndex, dir): number | null // next/prev visible ball (dir ±1)
```

- Tab into the field → `firstVisiblePoint()`; arrow keys → `stepVisiblePoint`
  (returns `null` at the ends; wrap by calling `firstVisiblePoint()` yourself).
- For a keyboard focus **cursor moving in screen space**, call `pickAt(x, y)`
  with a generous `radiusPx` at the cursor's logical position instead.

---

## 12. Per-point facet filtering (R1b — the filterable instrument)

The field becomes an instrument: a point is **visible iff it passes EVERY active
facet** (team AND season AND match). R1b ships **team + season facets and one
famous-match preset only** (blueprint §3 minimal-Bowl definition); league /
phase / player / over / outcome facets are deferred to R6. Failing points render
hidden or ghosted, and drop out of the pick pass (§11). Every facet change
resolves to **one static demand-rendered field state** (set uniforms → one
render), so the fallback path is satisfied for free.

### 12.1 Declarative — `SceneFieldState` (the entry state)

Omit them all (the R1a default) and the field is unfiltered. The Bowl opens with
`filterTeam` set to the reader's pick so it is **never blank**:

```ts
fieldState: {
  layout: 'free',
  filterTeam: pickedTeamId,     // teams.json id, or null = all teams
  filterSeason: null,           // season YEAR, or null = all
  filterMatchIndex: null,       // match index (needs match_index.u16; else null)
  filterMatchRange: null,       // [lo, hi) point-index range — the preset path
  filterMode: 'dim'             // filtered-out points: 'dim' ghost (default) | 'hide'
}
```

Each facet is independent; `null`/omitted imposes no constraint. Facets resolve
discretely (whichever side of a morph declares an active filter, preferring the
target) while the dim **lerps**, so a filter fades in/out cleanly with a morph.

### 12.2 Imperative — `field.setFilter` (interactive facet buttons)

The Bowl's facet controls change the filter *without* a scroll morph:

```ts
field.setFilter({ team: teamId });        // merge one facet, render once
field.setFilter({ season: 2016 });        // compose (team AND season)
field.setFilter({ matchRange: [lo, hi], mode: 'hide' }); // the famous-match preset
field.setFilter({ team: null, season: null, matchRange: null }); // clear → full field
field.getFilter();  // → Readonly<FieldFilter> (the live applied filter)
field.hasMatchAttr; // true once match_index.u16 is loaded (else the matchIndex facet is inert)
```

`FieldFilter = { team, season, matchIndex, matchRange, mode }` (all facets
`number | null`; `matchRange` is `readonly [lo, hi) | null`; `mode` is
`'hide' | 'dim'`). `setFilter` merges a partial onto the current filter and
demand-renders once.

**Orchestrator caveat (integration — read this).** The scroll orchestrator
re-applies a scene's declarative `fieldState` on every progress tick. So a scene
that changes facets interactively must keep its own reactive facet state and
**both** (a) call `field.setFilter(...)` on a control change for the instant
render, **and** (b) surface the same facets through `dynamicState(progress,
held) => ({ ...held, filterTeam, filterSeason, filterMatchRange })` so a stray
scroll re-application can't revert them. The Bowl is the terminal held scene, so
in practice this only bites if the reader scrolls while a facet is non-default —
but wire both paths to the same state and it is a non-issue.

### 12.3 Season facet semantics

`filterSeason` matches a **year** against the point's group season, so a season
spans **both leagues' groups** for that year (e.g. `2023` keeps IPL-2023 and
WPL-2023). Composed with a team facet (which already implies a league) it
resolves to that team's balls in that year.

### 12.4 Pipeline dependency — `match_index.u16` + `matches.json` (integration note)

The **exact-match tooltip** ("…in the 2019 final…") and **arbitrary match
selection** (tap any ball → filter to its match; R6) need a per-point match
identity that the shipped data does **not** yet carry. Two working facts shape
the ask:

- **Today, with zero new buffers:** a match's deliveries are **contiguous in
  point order** (verified: exactly 1,331 contiguous blocks, no interleaving), so
  the R1b famous-match preset filters by a **`matchRange` = [lo, hi)** point-index
  range. The scene derives `[lo, hi)` for the chosen match from the columnar
  dataset (first/last index whose row matches the preset's season+teams+innings),
  or the pipeline emits it in a tiny preset JSON. **No pipeline buffer required
  for R1b.**
- **Preferred / R6:** ship **`match_index.u16`** — one Uint16 per delivery, same
  point order as the other per-point buffers (max index 1330 < 65535; blocky and
  monotone → gz to ~a KB, like `group_ids.u16`). The loader auto-detects it
  (`FieldData.matchIndex`), `field.hasMatchAttr` flips true, and the
  `uFilterMatch` uniform / `filterMatchIndex` facet light up for selecting **any**
  match by id. Also ship **`matches.json`** (`match_index → { label, date, venue,
  teams, result }`) so a tap on any ball can NAME its match, not just the preset's.

The **tooltip metadata itself** (bowler · batter · runs · wicket) already lives
in `columnar.json.gz` (parallel arrays + dicts, same point order): the scene
reads `arrays.batter[idx]` etc. at the `pickAt` index. The platform's job ends at
returning the index; only the *match name* is blocked on the pipeline note above.

### 12.5 What the platform added (for the pipeline/other agents)

- **No new GL attribute is required for R1b.** `aMatchIndex` is wired but
  **optional** — it binds only when `match_index.u16` ships. Team (`aTeam`) and
  season (`gi` → `uGroupSeason[]`) facets reuse buffers already on the wire.
- New `FieldRenderState` uniform fields (set by `resolveRenderState` /
  `setFilter`): `filterTeam`, `filterSeason`, `filterMatchIndex`, `filterRangeLo`,
  `filterRangeHi`, `filterDim`. All default inactive, so **R1a scenes render
  byte-identically** (the filter block is a shader no-op when no facet is active).
- The visual and pick vertex shaders share one `computeCore()` (position +
  visibility), so the pick pass can never drift from what the reader sees.

---

## 13. Worm-space — Ch 2's controlling morph (R2a `worms` layout)

Chapter 2's single controlling morph (free→worms, analogous to Ch 1's free→wall).
Every ball settles into a **low-alpha density haze**: **x = the batter's
balls-faced index** (1..60+, reusing `ballsfaced.u8` — the wall display-clamped
it at 30, worm-space clamps at **60**, the capped `60+` bucket at the right edge)
and **y = cumulative innings runs** (new `cumruns.u8`). A rising staircase of one
batter-innings is a **worm**; slope = strike rate — par sprints up-and-right, an
anchor crawls along the floor. Positions are **in-shader**; no positions cross the
wire. Add nothing yourself — the shell owns the layout.

### 13.1 Declaring it

```ts
fieldState: { layout: 'worms' }   // that's it — free→worms is the morph
```

The field lands as the haze automatically (base alpha drops to a haze level as
the field morphs into worm-space, restored on the way out — no-op for every R1
layout). The reader's **team stays ignited at full brightness** through the haze
(personalization survives — C2-8 payoff). The morph is the chapter's ONE layout
morph; the run-out cascade (§14), the thinning, the gearbox and the WPL brighten
are all subset / 2D / colour-state beats that **compose** with `worms` and spend
no second morph.

### 13.2 Honesty lock (do not fight it)

The plot's **data aspect ratio is FIXED (banked ~45° for a modern-par slope) and
independent of the viewport** — the frame **letterboxes** (adds margin) rather
than stretching x or banking worms toward vertical, so the "sprints vs crawls"
angular contrast reads identically on desktop and portrait phone (the primary
target). The banking + display caps (`WORM_X_CAP` 60, `WORM_RUNS_CAP` 130,
`WORM_REF_RPB` 1.5) live in `lib/field/layout.ts` and are the **owner-tunable**
constants flagged for build sign-off (storyboard §5.11); changing them keeps the
fixed-aspect + letterbox invariant.

### 13.3 Drawing the par / anchor exemplar worms — `field.getWormLayout()`

The par worm, the K anchor exemplar worms and the axes are the **scene's job on
the annotation plane** (SVG registered to field coordinates) — **never** thousands
of GL polylines (the cardinality rule). The GL field is the haze; the worms are
crisp SVG on top. Register them with:

```ts
import { wormPoint } from '$lib/field/layout';
const w = field.getWormLayout();            // null before first resize — guard
if (w) {
  // map a data point (balls-faced, runs) → world, then → CSS px
  const world = wormPoint(w, ballsFaced, cumulativeRuns);
  const css = field.projectToCss(world.x, world.y);   // place the SVG vertex here
}
```

`getWormLayout()` returns `{ left, width, bottom, height, xCap, runsCap,
cellHalfW, cellHalfH }` (the fixed-aspect box + display caps), rebuilt on resize.
`wormPoint(layout, ballsFaced, runs)` is the **exact** mapping the shader uses
(balls clamped to the 60+ bucket, runs clamped to the cap), so the SVG worms and
the GL haze can never drift. The **anchor-worm figure channel** (dark casing/halo
+ brighter stroke + a locally-attenuated haze corridor beneath the line, storyboard
§0.1) is a compositing concern the scene owns on the annotation plane: the dark
SVG casing drawn over the canvas IS the corridor attenuation — no GL geometry
needed. The haze is deliberately dim so the SVG figure separates cleanly.

### 13.4 Reduced motion & pipeline dependency

Reduced motion jump-cuts free→worms live (the settled haze end state, team glow
intact) — declare `reducedMotionEndState: { layout: 'worms' }` (or let it default
to `fieldState`). **Pipeline dependency:** the y axis needs `cumruns.u8`
(per-point cumulative innings runs, cap 255, same point order as `ballsfaced.u8`,
uploaded normalized). The loader auto-detects it (`FieldData.cumRuns`); **until it
ships, worm-space y collapses to the floor** (graceful — R1 never uses `worms`).
No new x buffer (reuses `ballsfaced.u8`).

---

## 14. The run-out cascade — Ch 2's hero subset-highlight (R2a `cascade`)

A **reversible, season-swept flash+fall** of the run-out subset over the held
worm-space haze (C2-4). It is a cross-cutting modifier (like the highlight and the
§9 re-sort) — it composes with `worms` and does **NOT** spend a second controlling
morph. As a season pointer sweeps 2008→2026, each season's run-out cohort **flashes
red and ejects downward** out of the field, then fades; scrubbing back returns them.

### 14.1 Declaring it — `SceneFieldState.cascade`

```ts
cascade?: {
  class: 'runOut';       // the only cascade class today (the aRunOut flag)
  sweep: number;         // 0→1 season pointer — cohorts up to here have fallen
  tint?: number;         // red flash strength 0..1 (default 1) — the hue exception
  fall?: number;         // world-units downward eject depth (default 0.9)
  fade?: number;         // residual alpha × for a fully fallen point (default 0 = gone)
  muteIdentity?: number; // team-glow desaturation 0..1 through the cascade (default 1)
} | null;
```

**How it animates.** `sweep` lerps like any scalar. Each season's run-out cohort
shares ONE phase (a per-season pointer derived from the group's season year), so
the whole cohort flashes-and-falls **together as one synchronized wave (Gestalt
common fate — a discrete pulse per season, not asynchronous rain)**. Early seasons
dump a visible flood of red, late seasons a trickle — the shrinking flood **is** the
extinction curve. The flash **red** (`C_CASCADE_RED`, brighter + more saturated than
any team red, luminance-distinct from the haze) is the ONE gated hue exception in
Ch 2. `muteIdentity` desaturates the reader's team glow one stop **through the
cascade** so a red-team reader (RCB/PBKS/SRH) never confuses "my team" with "a
run-out" (the fall disambiguates on motion). Carry `sweep` at 1 to hold everything
fallen; declare **no** `cascade` in the next scene to lerp `sweep` back to 0 (the
run-outs return — the reverse leg is free).

### 14.2 The sweep is a caption STEP → drive it from `dynamicState`

`sweep` advances across the scene's HOLD (after the free→worms bit settles), so it
can't ride the morph — drive it from `SceneDef.dynamicState(progress, held)`,
exactly like the C1-5 re-sort tint and the C1-2 heat beat:

```ts
{
  id: 'ch2-runout',
  scrollLength: 200, morphLength: 40,
  fieldState: {
    layout: 'worms',
    cascade: { class: 'runOut', sweep: 0, tint: 1, fall: 0.9, muteIdentity: 1 }
  },
  // reduced motion jump-cuts straight to the final fallen layout:
  reducedMotionEndState: {
    layout: 'worms',
    cascade: { class: 'runOut', sweep: 1, tint: 0, fall: 0.9, muteIdentity: 1 }
  },
  // sweep the season pointer 2008→2026 as the caption scrolls:
  dynamicState: (progress, held) => ({
    ...held,
    cascade: { ...held.cascade!, sweep: Math.min(1, progress / 0.9) }
  }),
  annotations: RunOutCascade,
  footnote: 'runout'
}
```

The cascade is a POSITION modifier — the shell warns (dev) if it engages while a
`resort` is also engaged (both move points; stage them apart).

### 14.3 Feeding run-out membership — `field.setRunouts(indices)` (READ THIS)

Membership is a per-point GL flag (`aRunOut`), **seeded from `attrs.u8` bit 6**
(mask `0x40`). Because the pipeline has **not yet re-encoded that bit** (it reads 0
everywhere today), the scene supplies membership at runtime with a CPU index set —
the working-today path with **zero pipeline dependency**:

```ts
// once, when the scene mounts (before the cascade engages):
const runouts: number[] = [];
for (let i = 0; i < arrays.wicketKind.length; i++)
  if (arrays.wicketKind[i] === 'run out') runouts.push(i);   // from the columnar dataset
field.setRunouts(runouts);          // baked into aRunOut ONCE — no per-frame cost
// field.setRunouts(null) reverts to the pipeline seed (attrs.u8 bit 6)
```

The point order of the columnar `wicket_kind` array **is** the field's point order
(same as every per-point buffer), so `arrays.wicketKind[i] === 'run out'` gives
exactly the field index `i` to flag. Call `setRunouts` once; it O(n)-bakes the flag
and renders (demand mode preserved — no per-frame work). When the pipeline
re-encodes `attrs.u8` bit 6, the seed covers it and `setRunouts` becomes optional.

### 14.4 What the platform added (for the pipeline/other agents)

- **New `LayoutId` `worms`** (code 4) + **new `FieldRenderState` fields**:
  `cascadeClass`, `cascadeSweep`, `cascadeTint`, `cascadeFall`, `cascadeFade`,
  `cascadeMute` (set by `resolveRenderState`). All default inactive
  (`cascadeClass` -1), and `worms` is never a layout in R1 — so **R1a/R1b scenes
  render byte-identically** (verified: ignition wall + Bowl unchanged).
- **New optional buffers, zero wire cost until they ship:** `cumruns.u8`
  (`FieldData.cumRuns`, worm-space y — binds zeros until present) and the
  client-baked `aRunOut` flag (seeded from `attrs.u8` bit 6, overridable via
  `setRunouts`). No new **required** buffer; `worms` positions are in-shader from
  `ballsfaced.u8` + `cumruns.u8`.
- **Pipeline asks (integration):** emit `cumruns.u8` (per-point cumulative innings
  runs, cap 255, `ballsfaced.u8` point order); re-encode `attrs.u8` **bit 6** =
  run-out dismissal flag (a re-encode exactly like Ch 1's bit-5 top-10 flag,
  ledger delta 0). Both are no-ops for R1 until consumed by a Ch 2 scene.
- The worm haze + cascade fall live in the shared `computeCore()`, so the pick
  pass tracks fallen points and never drifts from the visual field.

---

## 15. The frontier plane — Ch 3's controlling morph (R2b `frontier` layout)

Chapter 3's single controlling morph (free→frontier, analogous to Ch 1's
free→wall and Ch 2's free→worms). Every ball condenses onto its **bowler-season**
coordinate, settling into a **low-alpha density haze** of dense bowler-season
clouds: **x = economy** (runs leaked per over; left = cheap, right = expensive)
and **y = bowling strike rate** (legal balls per bowler-credited wicket; bottom =
strikes fast, top = strikes slow). Both axes are "lower is better", so the
promised land is the **bottom-left corner** (cheap AND deadly) and the retreating
Pareto edge is the lower-left staircase. Positions are **in-shader**; no positions
cross the wire. Add nothing yourself — the shell owns the layout.

### 15.1 Declaring it

```ts
fieldState: { layout: 'frontier' }   // that's it — free→frontier is the morph
```

The field lands as the haze automatically (base alpha drops to a haze level as
the field morphs into the plane, restored on the way out — no-op for every R1/R2a
layout). The reader's **team stays ignited at full brightness** through the haze
(personalization survives — the payoff card re-centres on your dots). The morph
is the chapter's ONE layout morph; the dismissal rivers (§16), the season retreat
(a §12 `filterSeason` brighten), the dot-grid, the leak gauge and the WPL
brighten are all subset / filter / 2D / colour-state beats that **compose** with
`frontier` and spend no second morph.

### 15.2 The buffer — ONE interleaved `bowlerplane.u8` (read this)

The pipeline ships **one** buffer, `bowlerplane.u8` — **2 bytes per point**,
field point order, `byteLength == 2 × nPoints`, loaded like `wallheat.u8` /
`cumruns.u8` into `FieldData.bowlerPlane`. (This supersedes the older storyboard's
imagined two separate `bowlecon.u8` + `bowlsr.u8`; **the emitted artifact wins**.)
The shell binds it as two non-normalized u8 attributes off ONE
`THREE.InterleavedBuffer` (no copy):

- **byte 0 = economy**, linear over **[4.0, 16.0] RPO** → 0..254. Decode:
  `economy = 4 + b0/254 × 12`. `b0/254` IS the normalized x position.
- **byte 1 = bowling strike rate**, linear over **[8.0, 60.0]** balls/wicket →
  0..254, with **255 = sentinel** = "no bowler-credited wicket" → clamps to the
  top `60+` bucket. Decode: `strike_rate = 8 + b1/254 × 52` for `b1 < 255`.

Both display ranges are baked into `lib/field/layout.ts` as `FRONTIER_ECON_LO/HI`
(4/16) and `FRONTIER_SR_LO/HI` (8/60). **These mirror the emitted artifact** —
`scenes/ch3.json` `frontier.axis` and `bowlerplane_buffer` carry the same lo/hi,
exactly as `WALLHEAT_NEUTRAL_BYTE` mirrors the pipeline's wallheat pivot. If the
buffer is ever re-encoded over a different range, both move together (a build
sign-off constant, §5.2 of the storyboard). Because the buffer is encoded over
the same lo/hi the box spans, `b0/254` is the exact normalized axis position, so
the GL haze and the SVG `frontierPoint` mapping (§15.4) can never drift.

### 15.3 Honesty lock (do not fight it)

The plot's **data aspect ratio is FIXED** (`FRONTIER_ASPECT`, world width : height)
and independent of the viewport — the frame **letterboxes** (adds margin) rather
than stretching, so the bottom-left "cheap and deadly" corner sits in the same
place on desktop and portrait phone and the rightward retreat reads identically.
The aspect + fill + cloud-jitter constants live in `lib/field/layout.ts`
(`FRONTIER_ASPECT`, `FRONTIER_FILL`, `FRONTIER_CLOUD`) and are the owner-tunable
constants flagged for build sign-off; changing them keeps the fixed-aspect +
letterbox invariant. **The clouds never re-sort:** a bowler-season's economy and
strike rate are fixed once the season is over, so the C3-3 season retreat is a
`filterSeason` brighten (§12) over the held plane — real data migration, never a
second layout morph.

### 15.4 Drawing the edge / ghost trail / axes — `field.getFrontierLayout()`

The per-season Pareto edge ("the edge of the possible"), the ghost trail, the
seven-an-over reference line, the axes and the persistent orientation anchors are
the **scene's job on the annotation plane** (SVG registered to field coordinates)
— **never** GL geometry (the cardinality rule; hull vertices are a build-time
lookup in `ch3.json`, never client-fit). Register them with:

```ts
import { frontierPoint } from '$lib/field/layout';
const fl = field.getFrontierLayout();            // null before first resize — guard
if (fl) {
  // map raw (economy, strikeRate) from ch3.json → world, then → CSS px
  const world = frontierPoint(fl, economy, strikeRate);  // e.g. a hull vertex
  const css = field.projectToCss(world.x, world.y);      // place the SVG vertex here
}
```

`getFrontierLayout()` returns the fixed-aspect box + display ranges + registered
landmarks (rebuilt on resize):

```ts
{
  left, width, bottom, height;      // the letterboxed data box (world)
  econLo, econHi, srLo, srHi;       // display ranges (mirror ch3.json frontier.axis)
  cellHalfW, cellHalfH;             // per-bowler-season cloud jitter (density haze)
  sevenX;                           // world x of the seven-an-over reference line
  home: { x0, y0, x1, y1 };         // the bottom-left "cheap and deadly" home-zone box
  cheapX, expensiveX, fastY, slowY; // axis end-anchor world coords (cheap/expensive · fast/slow)
}
```

`frontierPoint(layout, economy, strikeRate)` is the **exact** mapping the shader
uses (both clamped to the display range), so the SVG edge/ghost/reference lines
and the GL haze can never drift. Pass raw units straight from `ch3.json`. (A
bowler-season with no wicket has no strike rate; those points clamp to the `60+`
top in the shader and are simply not drawn as SVG vertices by the scene.)

### 15.5 Reduced motion & pipeline dependency

Reduced motion jump-cuts free→frontier live (the settled haze end state, team glow
intact) — declare `reducedMotionEndState: { layout: 'frontier' }` (or let it
default to `fieldState`). **Pipeline dependency:** the plane needs
`bowlerplane.u8` (`FieldData.bowlerPlane`, 2×n bytes). The loader auto-detects it;
**until it ships, the plane collapses to the bottom-left corner** (graceful — R1
and R2a never use `frontier`). No other new buffer; positions are in-shader.

---

## 16. The dismissal rivers — Ch 3's hero subset-highlight (R2b `rivers`)

A **reversible** stream of the **bowler-credited wicket** subset out of the
frontier clouds into a **flat-baseline 100%-stacked band** and back (C3-4). It is
a cross-cutting modifier (like the highlight, the §9 re-sort and the §14 cascade)
— it composes with `frontier` and does **NOT** spend a second controlling morph.
As the reader scrubs, every wicket ball **lifts out of its cloud** and stacks into
a horizontal band for its dismissal kind (bowled · leg before · stumped · caught),
the bands **stacked flat between a fixed 0 baseline (bottom) and 100 (top)**, each
band's thickness the kind's share of that season's wickets, flowing left→right
across per-season strips. Scrubbing back returns the wickets to their clouds (the
reverse leg is free). Run-outs / retired are excluded (a fielding event, told in
Ch 2), so every share here shares one denominator: the wickets the bowler earned.

### 16.1 Declaring it — `SceneFieldState.rivers`

```ts
rivers?: {
  class: 'wicket';       // the bowler-credited wicket subset (aDismissal >= 0)
  engage: number;        // 0 = points in their clouds · 1 = fully stacked in the bands
  kinds?: ('bowled'|'lbw'|'stumped'|'caught')[]; // band order bottom→top
                         //   (default ['bowled','lbw','stumped','caught'] so the two
                         //    woodwork dismissals sit adjacent + baseline-anchored)
  tint?: number;         // categorical dismissal recolor strength 0..1 (gated hue
                         //   exception; bowled+lbw share one hue, caught + stumped
                         //   each distinct). Default 1
  othersDim?: number;    // luminance × for non-wicket points (default 0.12)
  muteIdentity?: number; // team-glow desaturation through the beat (default 1)
} | null;
```

**How it animates.** `engage` lerps like any scalar during the scene's morph: the
scene that DECLARES the rivers pulls `engage` 0→1 (wickets fly out — staggered per
point so each traces one path, object constancy — and stack into their kind's band,
thickness = that kind's share by season, the bands always summing to the full
0-to-100 height). The **next scene declares no `rivers`**, so `engage` lerps 1→0
and the wickets settle back into their clouds — the reverse leg is free. The
`kinds` order keeps **bowled and leg before adjacent + baseline-anchored** so the
"stumps" group reads as one shrinking region. The `tint` categorical palette
(`C_RIVER_STUMPS` for bowled+lbw · `C_RIVER_CAUGHT` · `C_RIVER_STUMPED` in
`shaders.ts`) is luminance-distinct, **brighter than any team red**, and avoids the
WPL teal; the exact hues are the remaining owner sign-off (storyboard §7c).
`muteIdentity` desaturates the reader's team glow one stop for the beat (the
red-team collision guard, §0.1 — the same guardrail Ch 2 put on its cascade).
Reduced motion jump-cuts to `engage:1` (the settled 100%-stacked band).

### 16.2 The engage is a caption STEP → drive it from `dynamicState`

`engage` advances across the scene's HOLD (after the free→frontier bit settles),
so it can't ride the morph — drive it from `SceneDef.dynamicState(progress, held)`,
exactly like the C1-5 re-sort tint and the C2-4 cascade sweep:

```ts
{
  id: 'ch3-rivers',
  scrollLength: 220, morphLength: 40,
  fieldState: {
    layout: 'frontier',
    rivers: { class: 'wicket', engage: 0, tint: 1, othersDim: 0.1, muteIdentity: 1 }
  },
  // reduced motion jump-cuts straight to the settled 100%-stacked band:
  reducedMotionEndState: {
    layout: 'frontier',
    rivers: { class: 'wicket', engage: 1, tint: 1, othersDim: 0.1, muteIdentity: 1 }
  },
  // stack the wickets into the bands as the caption scrolls:
  dynamicState: (progress, held) => ({
    ...held,
    rivers: { ...held.rivers!, engage: Math.min(1, progress / 0.6) }
  }),
  annotations: DismissalRivers,
  footnote: 'dismissal'
}
```

The rivers are a POSITION modifier — the shell warns (dev) if they engage while a
`resort` or `cascade` is also engaged (all move points; stage them apart).

### 16.3 Feeding wicket-kind membership — `field.setDismissals(kindByIndex)` (READ THIS)

Membership is a per-point GL flag (`aDismissal`): **-1 = not a bowler-credited
wicket**, **0 bowled · 1 lbw · 2 caught · 3 stumped**. The pipeline has **not**
re-encoded `attrs.u8` bits for dismissal kind yet, so the scene supplies membership
at runtime from the columnar `wicket_kind` array — the working-today path with
**zero pipeline dependency**, exactly like Ch 2's `field.setRunouts`:

```ts
// once, when the scene mounts (before the rivers engage):
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

The point order of the columnar `wicket_kind` array **is** the field's point order
(same as every per-point buffer), so index `i` is the field index to flag. Call
`setDismissals` once; it O(n)-bakes the flag **and recomputes the stacked band
positions** (the per-point cumulative-share slot, cached — no per-frame cost on
scrub), then renders (demand mode preserved). Pass `null` to clear membership. When
the pipeline re-encodes `attrs.u8` for dismissal kind, this seed can read it and
`setDismissals` becomes optional.

### 16.4 Anchoring band labels + the 0-to-100 axis — `field.getRiversLayout()`

The band labels, the **0-to-100 share axis** on the left, the season axis along the
bottom, and the era-ghost band boundaries are the scene's SVG, drawn from
`ch3.json`'s per-season shares and registered to these world coords:

```ts
{
  xs: number[];       // per-season strip centre world x, indexed by gi (NaN = none)
  gis: number[];      // strips in x order (IPL seasons then WPL seasons)
  stripHalfW: number; // in-strip jitter half-width
  left, width;        // the band box (world)
  bottom, top, height;// world y at 0% share (baseline) · 100% · the span
  bands: {            // the bands bottom→top, with POOLED-share label anchors
    kind: 'bowled'|'lbw'|'stumped'|'caught';
    loFrac, hiFrac;   // cumulative-share bounds 0..1 (pooled across all seasons)
    centerY;          // world y of the band's pooled-share centre (label anchor)
  }[];
}
```

Draw a band boundary at cumulative share `c` for season strip `gi` at world
`(xs[gi], bottom + c × height)`; the `bands` array gives a stable per-band label
anchor from the pooled shares (it reflects the last stack order seen by
`applyState`/`setDismissals`). All strips are contiguous (no league gap) so the
bands flow as one river; the scene draws the WPL split + season axis in SVG.

### 16.5 What the platform added (for the pipeline/other agents)

- **New `LayoutId` `frontier`** (code 5) + **new `FieldRenderState` fields**:
  `riversClass`, `riversEngage`, `riversTint`, `riversOthersDim`, `riversMute`,
  `riversKinds` (set by `resolveRenderState`). All default inactive (`riversClass`
  -1; `frontier` is never a layout in R1/R2a) — so **R1a/R1b/R2a scenes render
  byte-identically** (verified: the density-haze weight, the team-ignite mute and
  every new branch are no-ops when `frontier` isn't in the A/B mix and no rivers
  are declared).
- **New optional buffer, zero wire cost until it ships:** `bowlerplane.u8`
  (`FieldData.bowlerPlane`, 2×n interleaved — binds zeros until present, so the
  plane collapses to the corner) and the client-baked `aDismissal` flag (default
  -1, supplied via `setDismissals`; `aRiverPos` is derived on-device). No new
  **required** buffer; `frontier` positions are in-shader from `bowlerplane.u8`.
- **Pipeline asks (integration):** emit `bowlerplane.u8` (2 bytes/point, byte 0
  economy over [4,16], byte 1 strike rate over [8,60] with 255 = no-wicket
  sentinel, `ballsfaced.u8` point order) — **shipped**; optionally re-encode
  `attrs.u8` bits for dismissal kind later (a re-encode like Ch 1's bit-5 / Ch 2's
  bit-6; the client-baked `setDismissals` path makes it optional). Keep the
  `FRONTIER_*` display-range constants in `layout.ts` in lock-step with
  `ch3.json` `frontier.axis` / `bowlerplane_buffer`.
- The frontier haze + the rivers fly-out live in the shared `computeCore()`, so the
  pick pass tracks the flown points and never drifts from the visual field.

---

## 17. Mobile "read, then watch" captions (MF — the mobile caption fix)

**The problem (owner feedback):** on phones the `.caption-slot` sits ON TOP of
the full-screen field/charts on almost every scene, so a reader can never see
the visual they are reading about. This piece is mobile-first — most fans open
it on a phone — so this is a core-experience bug.

**The fix (mobile only):** the visual stays full-screen. Within each caption
STEP's scroll range the caption fades IN (the reader reads), then fades fully
OUT to a CLEAR GAP (opacity 0) so the field is unobstructed and the reader
WATCHES it before the next step's caption fades in. Text and picture take turns;
the text never sits on the data for more than its read beat.

**Desktop is untouched and byte-identical** — it keeps the persistent corner
caption. The mechanism is a single shared helper; scenes opt in with two lines.

### 17.1 The helper — `lib/story/captionReveal.svelte.ts`

```ts
// the scene-facing helper — the opacity for `.caption-slot`
captionReveal(progress, stepStart, stepEnd, opts?): number
```

- `progress` — the scene's 0..1 `progress` prop.
- `stepStart`, `stepEnd` — the `[start, end)` progress boundaries of the CURRENT
  caption step (the scene already knows these from its step thresholds; see 17.4).
- `opts: CaptionRevealOpts` — `{ reduced?, fadeIn?, readHold?, fadeOut? }`.
  **Pass `reduced`** (the scene's `reduced` prop) — it is required for correctness.
  The curve knobs are fractions of the step and default to the owner spec:
  `fadeIn 0.06` · `readHold 0.60` · `fadeOut 0.20` (⇒ clear gap = last 0.20).

**Return value:**

- **`1`** on DESKTOP, during SSR/prerender, and under REDUCED MOTION — the
  caption never fades (persistent, byte-identical, accessible).
- On a MOBILE viewport (`max-width: 640px`) or with `?mobilecaptions=1`, and
  normal motion, the read-then-watch curve for the reader's position in the step:

  | local `u = (progress-stepStart)/(stepEnd-stepStart)` | opacity |
  | --- | --- |
  | `[0, 0.06)`   | ramp 0 → 1 (fast fade-in) |
  | `[0.06, 0.60)`| **1** — the READ beat |
  | `[0.60, 0.80)`| ramp 1 → 0 (fade-out) |
  | `[0.80, 1.0)` | **0** — the CLEAR GAP (watch beat) |

Opacity follows SCROLL position, so a reader who pauses mid-read keeps the
caption; it only fades as they scroll into the gap (reader-paced). Apply **no
CSS transition** to the reveal — it is scrubbed frame-by-frame; a transition
would lag the scroll (a short ≤200 ms appear-transition on a `.shown` gate is OK).

Also exported:

- `captionRevealActive(): boolean` — reactive; true when the fade is on (mobile
  or forced). Drives the optional scroll-length bump; scenes rarely need it.
- `captionRevealCurve(progress, start, end, opts?)` — the PURE curve (ungated),
  for tests.
- `MOBILE_READ_GAP_SCALE` (`1.3`) + `readGapScrollLength(baseVh)` — see 17.5.

### 17.2 The debug flag — `?mobilecaptions=1`

Append `?mobilecaptions=1` to the URL (like the existing `?hud=1`) to FORCE the
read-then-watch behaviour regardless of viewport width — for previewing/testing
in a desktop automation browser that cannot emulate a 375 px phone. It flips
`captionRevealActive()` true for the whole page (fades **and** the mobile
scroll-length bump). Read once at load; add it to the query string, not a toggle.

### 17.3 Accessibility, reduced motion, composition (hard invariants)

- **Opacity only.** Drive the fade with a CSS custom property `--reveal` and
  `opacity`. Do **not** use `display:none`, `visibility:hidden`, or `aria-hidden`
  in the gap — the caption must stay in the DOM and the accessibility tree so
  screen readers still reach it while it is visually faded.
- **Reduced motion stays visible.** Under `prefers-reduced-motion` scenes
  jump-cut (no morph to watch), so `captionReveal` returns 1 — the caption never
  fades. Always pass `reduced`.
- **Composes with an existing appear-gate.** Scenes that already gate the whole
  slot (`.caption-slot.shown { opacity: 1 }`, e.g. the Close/WplBeat scenes) must
  multiply, not clobber: change that rule to `opacity: var(--reveal, 1)`. The
  `--reveal` fallback of `1` means desktop/SSR/no-JS render exactly as before.

### 17.4 ADOPTION RECIPE (per-scene agents — copy/paste)

**Step A — import + derive the current step's `[start, end)`.** Hoist your step
thresholds into one ascending array so you can read the current step's bounds.
Example for a 3-step scene whose thresholds are `< 0.64` → step 1, `< 0.82` →
step 2, else step 3 (Worms/Frontier shape):

```svelte
<script lang="ts">
  import { captionReveal } from '$lib/story/captionReveal.svelte';
  // …existing props…
  let { progress, active, field, reduced }: SceneAnnotationProps = $props();

  // ascending step boundaries: step k (1-based) spans [BOUNDS[k-1], BOUNDS[k])
  const BOUNDS = [0, 0.64, 0.82, 1] as const;
  const step = $derived(progress < 0.64 ? 1 : progress < 0.82 ? 2 : 3);

  // read-then-watch opacity for the CURRENT step (1 on desktop / reduced motion)
  const reveal = $derived(
    captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced })
  );
</script>
```

**Step B — apply `--reveal` to `.caption-slot`** (nothing else about the slot
changes):

```svelte
<div class="caption-slot" style:--reveal={reveal}>
  {#if step === 1}
    …
  {/if}
</div>
```

**Step C — one CSS line so the slot honours `--reveal`.**

- Slot with NO existing opacity gate (most scenes — Wall, Worms, Frontier, …):

  ```css
  .caption-slot {
    /* …existing position rules… */
    opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
  }
  ```

- Slot that ALREADY gates with `.shown` (Close, WplBeat, CloseCh2/3): keep the
  hidden default, and make the shown state follow `--reveal`:

  ```css
  .caption-slot { opacity: 0; }
  .caption-slot.shown { opacity: var(--reveal, 1); } /* was: opacity: 1 */
  ```

That is the whole change: two lines in markup/script + one CSS line. Desktop
(`--reveal` resolves to 1) and reduced motion (`captionReveal` returns 1) are
untouched; do not add any `@media (max-width: 640px)` branch for this — the gate
lives in the helper.

**Notes for irregular step maps.** If your steps do not start at 0 or you have a
`step 0` pre-morph beat (e.g. Wall), just build `BOUNDS` from your actual
thresholds so `BOUNDS[i]`/`BOUNDS[i+1]` bracket the step you are rendering. If a
scene has a leading morph where you want the first caption held (not gapped)
until the morph lands, set that step's `start` to the morph-end progress. Scenes
with NO visual behind the caption (pure-text titles/closes over a static field)
should NOT adopt — there is nothing to watch in the gap; leave them as-is.

### 17.5 Optional — lengthen the mobile scroll for a comfortable read + gap

The reveal splits each step into ~60% read + ~20% fade + ~20% watch, so a step
that reads fine as one desktop caption can feel rushed on a phone. If so, give
the scene a longer **mobile-only** scroll span via the new optional
`SceneDef.mobileScrollLength` (vh) in your `index.ts`:

```ts
import { readGapScrollLength } from '$lib/story/captionReveal.svelte';

{
  id: 'ch2-worms',
  scrollLength: 340,                                // desktop, unchanged
  mobileScrollLength: readGapScrollLength(340),     // ≈ 442vh on mobile only
  // …
}
```

Story.svelte uses `mobileScrollLength` **only** when the gate is active (mobile
or `?mobilecaptions=1`) and calls `ScrollTrigger.refresh()` when the gate flips;
desktop always uses `scrollLength` (byte-identical). Omit it and mobile keeps
`scrollLength`. Use it sparingly — only where a step genuinely feels cramped.

### 17.6 Ideal (tuning, not required for v1): align the morph with the gap

Where a scene's timing allows, hold the morph relatively STILL during the read
beat (`u ∈ [0.06, 0.60]`) and let the interesting movement PLAY during the clear
gap (`u ∈ [0.80, 1.0]`) so nothing important is missed while the caption is up.
For `dynamicState`-driven beats (the C1-5 tint, the cascade `sweep`, the rivers
`engage`), schedule the change to advance across the gap window rather than
during the read. Align where you can; flag in your report where a scene's fixed
timing cannot.

---

## 18. The tide skyline + the waterline — Ch 4's controlling morph (R3a `tide` layout + `waterline`)

Chapter 4's single controlling morph (free→tide, analogous to Ch 1's free→wall,
Ch 2's free→worms, Ch 3's free→frontier). Every ball condenses onto its
**innings-total column**: **x = season block** (2008 on the left → this year on
the right, then a deliberate gap, then the WPL block) plus a **within-season
packing slot** (each season's innings ranked SHORT→TALL so the block reads as a
little skyline; the within-season x carries no meaning and the scene suppresses
its ticks), and **y = a column filled from the floor up to the innings TOTAL**
(from `innings_total.u8`), so the taller the column the bigger the score and the
whole field reads as a coastline rising left→right. Positions are **in-shader**;
no positions cross the wire. Add nothing yourself — the shell owns the layout.

**No new engine.** The waterline (the going rate) is a per-season lookup from
`scenes/ch4.json` `columns.par_waterline` (engine #1), interpolated by the scene,
never client-fit. The field only draws the skyline and dims drowned columns; the
scene draws the waterline LINE + the reference rules on the annotation plane.

### 18.1 Declaring it

```ts
fieldState: { layout: 'tide' }   // that's it — free→tide is the morph
```

The field lands as the dense first-innings skyline automatically (full alpha —
the skyline is the hero visual, NOT a low-alpha haze like `worms`/`frontier`).
The reader's **team stays ignited** through the flight (personalization survives
— C4-11). The morph is the chapter's ONE layout morph; the waterline (§18.4), the
200-club crest (a §2 `highlight`), the 2023 jump (a `waterline.level` freeze) and
the WPL brighten (a `wplDim`/luminance state) all **compose** with `tide` and
spend no second morph. Reduced motion jump-cuts free→tide live (declare
`reducedMotionEndState: { layout: 'tide' }` or let it default to `fieldState`).

### 18.2 Honesty lock (do not fight it)

The plot's **data aspect ratio is FIXED** (`TIDE_ASPECT`, world width : height)
and independent of the viewport — the frame **letterboxes** (adds margin) rather
than stretching, so the coastline geometry and, crucially, the **low-vs-high
column heights (which ARE the argument)** read consistently on desktop and
portrait. The total-axis cap is `TIDE_TOTAL_CAP` (**300 runs**), set at/above the
current record first innings (SRH 287) so the record column tops out honestly and
is never clipped. The decode scale is fixed (`TIDE_BYTE_SCALE` = 2: runs = byte ×
2). `TIDE_ASPECT` / `TIDE_FILL` / `TIDE_TOTAL_CAP` live in `lib/field/layout.ts`
and are the owner-tunable constants flagged for build sign-off; on a very tall
portrait, if columns read too short the fix is a taller `TIDE_ASPECT` or a
horizontal season scrub — **never a shorter column** (column height is the
argument). **The columns never re-sort:** an innings' total and season slot are
fixed, so the waterline rise (§18.4) is a luminance state over the held skyline —
real data, never a second layout morph.

### 18.3 Drawing the waterline / 200 / 230 / ghost / axis — `field.getTideLayout()`

The rising waterline, the fixed 165 ghost line, the 200 / 230 reference rules, the
total-axis ladder (120 / 160 / 200 / 240) and the season-axis labels are the
**scene's job on the annotation plane** (SVG registered to field coordinates) —
**never** GL geometry (the cardinality rule). Register them with:

```ts
import { tidePoint, tideTotalToY } from '$lib/field/layout';
const t = field.getTideLayout();                 // null before first resize — guard
if (t) {
  // a horizontal rule at a total (waterline, 165 ghost, 200, 230, ladder marks):
  const y = tideTotalToY(t, 195);                // world y for 195 runs (season-independent)
  const left = field.projectToCss(t.left, y);
  const right = field.projectToCss(t.left + t.width, y);   // draw the SVG line left→right

  // a season anchor (season chip, scrub pointer, season-axis label) at a gi:
  const p = tidePoint(t, gi, 195);               // { x: season block centre, y: total→y }
  const css = field.projectToCss(p.x, p.y);
}
```

`getTideLayout()` returns the fixed-aspect letterboxed box + the total cap + the
per-season block x-centres (rebuilt on resize):

```ts
{
  left, width, bottom, height;   // the letterboxed data box (world)
  totalCap;                      // total-axis display cap in RUNS (300) — mirrors the shader
  xs: number[];                  // per-season block centre world x, indexed by gi (NaN = none)
  blockHalfW;                    // half-width of a season block (columns pack within ±)
  slotW;                         // season slot pitch (season-axis label density)
  reservoirH;                    // world height of the reservoir haze band
  iplMidX, wplMidX;              // IPL/WPL block centres (league / axis headings)
}
```

`tidePoint(layout, gi, total)` and `tideTotalToY(layout, total)` are the **exact**
mappings the shader uses (total clamped to the cap), so the SVG waterline / rules
/ axes and the GL skyline can never drift. `gi` is the season's group index (the
season block); x is season-block-only, y is total-only.

### 18.4 The waterline — `SceneFieldState.waterline` (the rising going rate)

A cross-cutting LEVEL over the held `tide` layout (like `highlight` / `resort` /
`cascade` / `rivers` — it composes with the layout and does **NOT** spend a second
controlling morph). A first-innings column whose innings TOTAL sits below the
level DROWNS — dimmed toward the reservoir on **LUMINANCE only, never a hue
change** (hue stays identity; the waterline LINE and the 200/230 rules are the
only blue on screen and they are annotation-plane SVG, not this uniform).

```ts
waterline?: {
  level: number;         // the going rate for the scrubbed season, in RUNS (e.g. 165 → 206).
                         //   A first-innings column with total < level drowns. Lerps as the
                         //   scene scrubs (the water RISES); drains to the floor on the
                         //   reverse leg. Omit / null → inert (nothing drowns).
  drownDim?: number;     // luminance × for a drowned column, 0..1 (default 0.18 — one-plus stop)
  teamKeepLit?: boolean; // the picked team's columns keep their glow even when drowned (default true)
  ghostLevel?: number;   // OPTIONAL, scene-convenience only — the FIELD ignores it; the 165 ghost
                         //   line (like the 200/230 rules) is annotation-plane SVG via tideTotalToY
} | null;
```

**How it animates.** `level` lerps like any scalar. As the reader scrubs the
season pointer 2008→2026 the going rate genuinely climbs (feed the per-season par
from `scenes/ch4.json` `columns.par_waterline`), so more columns drop below the
line and drown. Drive `level` across the HOLD from a caption step via
`SceneDef.dynamicState(progress, held)` (a post-morph field change, exactly like
the C1-5 tint / cascade `sweep` / rivers `engage`; use the §12.2 orchestrator-
caveat pattern so a stray scroll can't revert the scrub). The **next scene
declaring no waterline** lets `level` drain to the floor (the water recedes; the
reverse leg is free). Reduced motion resolves to the season's settled `level`
(render the 2008-vs-2026 small-multiple per the storyboard). Anchor the waterline
label + the total-axis marks with `getTideLayout()` / `tideTotalToY`.

Example (waterline rising across the hold):

```ts
{
  id: 'ch4-waterline',
  scrollLength: 320, morphLength: 40,
  fieldState: { layout: 'tide', waterline: { level: 165, drownDim: 0.18 } },
  reducedMotionEndState: { layout: 'tide', waterline: { level: 206, drownDim: 0.18 } },
  dynamicState: (progress, held) => ({
    ...held,
    waterline: { ...held.waterline!, level: 165 + (206 - 165) * Math.min(1, progress / 0.9) }
  }),
  annotations: Waterline,
  footnote: 'pardrift'
}
```

### 18.5 First-innings vs reservoir — `field.setFirstInnings(indices)` (READ THIS)

Only **full first innings** build columns; every other ball (second innings,
super-over, rain-hit) settles into a **low-alpha reservoir haze** near the floor,
so "every ball ever is here" (316,199) stays literally true while the lit columns
carry the argument. `innings_total.u8` carries a total for **every** ball and does
NOT flag first innings, so the scene supplies membership at runtime — the
working-today path with **zero pipeline dependency**, exactly like Ch 2's
`setRunouts` / Ch 3's `setDismissals`:

```ts
// once, when the scene mounts (before the tide morph engages):
const firstInn: number[] = [];
for (let i = 0; i < arrays.innings.length; i++)
  if (arrays.innings[i] === 1) firstInn.push(i);   // from the columnar `innings` array
field.setFirstInnings(firstInn);                   // the rest route to the reservoir haze
// field.setFirstInnings(null) → every ball builds a column (the graceful default)
```

The field bakes membership ONCE and re-derives the within-season packing (only
first-innings innings are ranked, so the comb has no gaps), cached — **no
per-frame cost**, demand mode preserved. Called with `null` (or never called) it
degrades gracefully to "every ball builds a column", so the layout works out of
the box for dev / deep-link before the columnar data is read. The waterline drown
only applies to first-innings columns; reservoir balls are already dim.

### 18.6 What the platform added (for the pipeline / other agents)

- **New `LayoutId` `tide`** (code 6) + **new `FieldRenderState` fields**:
  `waterLevel` (-1 inert), `waterDrownDim` (1), `waterTeamKeep` (false), set by
  `resolveRenderState`. All default inert (`waterLevel` -1; `tide` is never a
  layout in R1/R2) — so **R1a/R1b/R2a/R2b scenes render byte-identically**
  (verified: free / columns / wall / worms / frontier all render unchanged; the
  waterline drown is a shader no-op at `waterLevel < 0`).
- **New OPTIONAL buffer, zero wire cost until it ships:** `innings_total.u8`
  (`FieldData.inningsTotal`, one byte/point, runs = byte × 2 — binds zeros until
  present, so the skyline collapses to the floor). Its bytes stay CPU-side and are
  packed, together with the on-device within-season packing slot and the
  first-innings flag, into **ONE** GL attribute `aTide` (byte | slot·256 |
  flag·262144) to stay within `MAX_VERTEX_ATTRIBS` (adding three separate
  attributes overflowed the ANGLE/Metal budget; one packed attribute keeps the
  field at 13 of 16). Decoded in the shared `computeCore()` the same way the pick
  shader decodes its index, so the pick pass tracks tide points and never drifts.
- **Pipeline asks (integration):** emit `innings_total.u8` (per-point full-innings
  total, `ballsfaced.u8` point order, runs = byte × 2) — **shipped**; and the
  per-season going rate + milestone shares in `scenes/ch4.json` (the waterline
  reads `columns.par_waterline`). No engine and no first-innings buffer required:
  first-innings membership comes from the columnar `innings` array via
  `setFirstInnings`. Keep `TIDE_TOTAL_CAP` / `TIDE_BYTE_SCALE` in `layout.ts` in
  lock-step with the `innings_total.u8` encoding.
- The tide position + the waterline drown live in the shared `computeCore()` /
  visual shader, so the pick pass is registered to the visible skyline.

---

## 19. The worth grid + the pricelens — Ch 5's controlling morph (R3b-2 `worth` layout + `pricelens` color state)

Chapter 5's single controlling morph (free→worth, analogous to free→wall /
free→worms / free→frontier / free→tide). Every ball condenses to the **cell of
the match situation it was bowled in**: **x = the over of the innings** (over
index 0 at the left → 19 at the right) and **y = wickets fallen when the ball
was bowled** (0 at the **TOP** → 9 at the bottom), from `restate.u8` (one byte
per point, cell = over×10 + wicketsDown, 0..199; both innings packed — filter
via the columnar `innings` array if a scene needs one innings only). Points
pack the cell body with deterministic in-shader jitter (`WORTH_CELL_FILL` of
the pitch; the gutter keeps cells readable). Positions are **in-shader**; no
positions cross the wire. Add nothing yourself — the shell owns the layout.

**Cell COLOR is the price.** Cell luminance encodes the expected runs still to
come for the displayed era — a **200-entry lookup table the scene feeds** (the
`pricelens`), never a hue (hue stays identity: team color, WPL family). The
era flip and the difference lens are COLOR states over the held grid — the
grid never moves after the morph lands (the Ch 4 fixed-columns/moving-water
discipline).

### 19.1 Declaring it

```ts
fieldState: { layout: 'worth', pricelens: { table: 'early' } }
```

`free→worth` is the morph. A scene declaring **no** `pricelens` renders the
grid under the NEUTRAL ramp (density gain only — §19.4). The reader's **team
stays ignited** through the flight and resists the density gain one stop
(personalization survives). The morph is the chapter's ONE layout morph; the
era flip / difference lens / WPL recolor are `pricelens` color states, the
six-ball lift is the §20 over rail, and the WPA lift is a §21 highlight — all
compose with `worth` and spend no second morph.

### 19.2 Feeding the tables — `field.setWorthTables()` (READ THIS)

The scene feeds the per-era tables ONCE (from `scenes/ch5.json`), then selects
them declaratively:

```ts
// once, when the scene mounts (tables from scenes/ch5.json — the SCENE
// normalizes raw engine runs to 0..1 luminance, because the scale choice is
// editorial: the two era maps share one scale, the rise lens has its own):
field.setWorthTables({
  early:  earlyLum,   // 200 entries, cell = over×10 + wicketsDown, 0..1
  recent: recentLum,  // (same scale as early — the flip must be honest)
  rise:   riseLum,    // the difference lens, its own scale
  wpl:    wplLum      // evidenced WPL cells (mask hatching is the scene's SVG)
});
```

Up to **7 tables** per call; re-calling replaces the whole set; a table id the
field hasn't been fed renders the neutral ramp (dev-warned). Feeding order is
insertion order (deterministic). O(1) per frame afterwards — demand mode holds.

### 19.3 Selecting + flipping — `SceneFieldState.pricelens`

```ts
pricelens?: {
  table: string;         // the active table id ('early' | 'recent' | 'rise' | 'wpl')
  from?: string | null;  // optional mix SOURCE: render mix(from, table, mix)
  mix?: number;          // 0 = pure `from` · 1 = pure `table` (default 1)
} | null;
```

- **The C5-6a era flip** is `{ from: 'early', table: 'recent', mix }` with
  `mix` driven 0→1 across the HOLD from `SceneDef.dynamicState` (a post-morph
  field change, exactly like the C1-5 tint / cascade sweep / waterline level).
- **The lens landing (dip-to-dark re-light)** is the same `dynamicState`
  swapping the pair to `{ from: 'recent', table: 'rise' }` while driving the
  scene's `dim` down to near-black and back — no extra capability.
- **Cross-scene transitions:** the active descriptor (preferring the `to`
  side) fixes the table pair; `mix` lerps between the sides' declared mixes.
  A cross-TABLE release (C5-6b: rise → recent on entry) is the entering
  scene's job: declare `{ from: 'rise', table: 'recent', mix: 0 }` and drive
  `mix` up across the entry morph via `dynamicState` (declare
  `reducedMotionEndState` with `mix: 1`).
- The recolor is **gated on the worth layout's share of the A/B morph mix**,
  so it rides free→worth in and worth→free out automatically, and is a shader
  no-op for every prior layout (byte-identical R1–R3b-1).

### 19.4 Density normalization (§0.1 BINDING — do not fight it)

Perceived cell brightness = point density × per-point luminance, and cell
populations run 1 → ~15k, so uncorrected luminance would encode CROWD, not
price. The field derives a per-cell **density gain** ONCE from the restate.u8
cell populations — `clamp((WORTH_GAIN_TARGET / cellCount)^WORTH_GAIN_POW,
WORTH_GAIN_MIN, 1)` in `layout.ts`, owner-tunable — and bakes it beside every
table row (a 200×8 RG float data texture), so a cell's INTEGRATED brightness
tracks the active price table and **a dense cheap cell never outshines a
sparse expensive one**. The scene ships only prices; the gain is the shell's.

### 19.5 Honesty lock + anchoring — `field.getWorthLayout()` / `worthCell()`

The plot's **data aspect ratio is FIXED** (`WORTH_ASPECT`) and viewport-
independent — the frame **letterboxes**, never stretches (the Ch 2/3/4 lock),
so "brightest at the top-left" reads identically on desktop and portrait.
Axis labels, the persistent axis tag, cell tap-reads, the C5-6b hero rings,
and the **WPL mask hatching are the scene's SVG on the annotation plane**
(hatched is never a dimness — a thin cell must never read as a cheap one),
registered to GL cells via:

```ts
import { worthCell } from '$lib/field/layout';
const wl = field.getWorthLayout();          // null before first resize — guard
if (wl) {
  const c = worthCell(wl, 6, 2);            // over 7, two down (0-indexed over)
  const css = field.projectToCss(c.x, c.y); // ring/hatch/readout anchor
}
```

`getWorthLayout()` returns `{ left, width, bottom, height, overs, wkts, cellW,
cellH, cellHalfW, cellHalfH }` (the letterboxed box + cell pitches, rebuilt on
resize); `worthCell(layout, over, wicketsDown)` is the **exact** shader mapping
(0 wickets at the TOP), so annotation-plane geometry can never drift from the
GL cells. A cell's rect is centre ± (cellW/2, cellH/2).

### 19.6 Reduced motion & pipeline dependency

Reduced motion jump-cuts free→worth live (settled grid, active table, team glow
intact) — `reducedMotionEndState` defaults to `fieldState`; color states swap
instantly (declare the end-state `pricelens`). **Pipeline dependency:**
`restate.u8` (`FieldData.stateCell`, one byte/point; any byte > 199 clamps to
cell 199 defensively). The loader auto-detects it; until it ships, every ball
reads cell 0 (graceful — prior releases never use `worth`). `hasStateAttr`
flips true when loaded. The state-cell byte is packed with the WPA byte into
ONE GL attribute `aPrice` (cell + wpaByte×256 — the vertex-attribute budget,
exactly like `aTide`).

---

## 20. The over rail — Ch 5's set-piece six-ball lift (R3b-2 `overrail`)

A **reversible** subset modifier for the C5-2/C5-3 set piece (like `resort` /
`cascade` / `rivers`: it composes with any base layout and spends **NO**
controlling morph): the **six(+) deliveries of ONE over** — a tiny index set
from `scenes/ch5.json`, never client-derived — lift out of the field and fly
to **viewport-anchored rail slots** as `progress` scrubs 0→1, enlarging to
hero size, while the REST of the field dims hard behind them (set-piece
dimming rides the lift). Scrubbing back returns every ball to its exact field
position (the reverse leg is free — the next scene declares no `overrail`).

### 20.1 Declaring it — `SceneFieldState.overrail`

```ts
overrail?: {
  indices: readonly number[];  // field point indices, bowling order (≤ 8)
  slots?: readonly [number, number][]; // per-ball anchors as VIEWPORT FRACTIONS
                               //   (x 0 left→1 right, y 0 top→1 bottom; default =
                               //    an evenly-spaced row across the middle)
  progress: number;            // 0 = in the field · 1 = at the slots
  dimRest?: number;            // rest-of-field luminance×alpha at progress 1 (default 0.06;
                               //   alpha dims saturate on dense layouts — stay ≤ ~0.1 to dim hard)
  scale?: number;              // hero point-size multiplier (default 7)
  lift?: number;               // world-units flight-arc peak (default 0.35)
} | null;
```

Drive `progress` from `SceneDef.dynamicState` — C5-3's GSAP scrub maps its
scroll progress straight onto it, so a stray scroll re-application can never
desync the rail from the chips/worm (the §12.2 orchestrator-caveat pattern).
The flight is staggered per slot (ball 1 leads — a readable left-to-right
wave, object constancy). Indices/slots/config are discrete from the active
descriptor; only `progress` lerps.

### 20.2 The implementation choice (documented — why GL fly-out, not DOM heroes)

The rail is **GL points flying to slots, with a dedicated OVERLAY draw**, not
DOM hero balls over dimmed GL originals:

- **The lift must be literal.** "Six balls lift OUT of the field" is the beat;
  only the real points give one continuous path from each ball's true field
  position (object constancy, same grammar as the C1-5 fireworks arc), and the
  reverse scrub returns them exactly. A DOM double would teleport identity.
- **No registration drift.** Slots are viewport fractions; the same fractions
  position the scene's DOM chips (via `projectToCss` on the slot), so chip and
  ball agree by construction on every viewport.
- **Draw-order honesty.** The main 316k draw renders in point order, so a
  lifted 2019 ball would be fogged by ~40k later-indexed points. The shell
  therefore CULLS rail members from the main pass while the rail is engaged
  and draws them in a second `THREE.Points` pass (same geometry, same uniforms
  object, `RAIL_OVERLAY` shader define, renderOrder 1) that culls everything
  BUT the members — ≤8 vertices survive, zero fragment cost, on top of the
  whole field. The overlay is `visible` only while the rail is engaged and is
  pre-compiled at load, so prior scenes pay nothing and the first scrub frame
  never hitches.
- **The hero ball reads as THE OBJECT.** As `railT → 1` an overlay ball
  resists the scene dim and the §19 pricelens luminance/density gain (a
  lifted ball is the drama's object, not its cell's price — a death-over
  cell would otherwise render its hero near-black). Compiled only under
  `RAIL_OVERLAY` (`railKeep` is constant 0 in the main pass), so every
  non-rail scene renders byte-identically. This is what lets the C5-11
  payoff ignite a single ball IN PLACE on the worth grid: one index, the
  slot set to the ball's own cell centre, `dimRest: 1` so the rest of the
  field keeps the scene dim.
- **Hybrid contract holds.** Names and numbers are DOM: the scene's ball chips
  anchor at the slots; the WP worm is the scene's SVG on the annotation plane.
  The GL ball is the object; the chip is the label.

Membership is a **uniform index set** (≤ `RAIL_MAX_SLOTS` = 8) — no per-point
attribute, no wire cost, nothing baked.

### 20.3 Staging, reduced motion, picking, nav

- A cross-cutting POSITION modifier: the shell dev-warns if the rail engages
  while a `resort` / `cascade` / `rivers` is also engaged (stage them apart).
- **Reduced motion:** the resolved end state renders the balls AT their slots
  instantly (live-rendered, never baked); the C5-3 six-panel DOM strip is the
  scene's mandated fallback content.
- **Picking:** rail members are not pickable while lifted (they leave the main
  + pick passes; the chips are the tap surface — ≥44px, richer content).
- **Nav dimming (integration note):** the shell's structural set-piece
  detection (§6) keys on layout/reveal changes and does NOT see the rail; if
  the ☰ should dim through C5-2/C5-3, extend that detection to "either side
  declares an `overrail`" in Story.svelte (shell change, one clause) — the
  field-side dimming (`dimRest`) is already carried by this capability.

---

## 21. The WPA subset-highlight — Ch 5's biggest-swing lift (R3b-2 `'wpa'` class)

The existing §2 subset highlight, extended with one class: `'wpa'` matches the
balls whose **win-chance swing** (WPA, batting-team perspective, from
`wpa.u8`) is at least `wpaThreshold` in ABSOLUTE size. Reuses the whole
highlight pipeline — lift, boost, othersDim, skipWpl, lerped engagement — so
it composes with any layout (dim the worth grid, lift the decisive balls) and
spends nothing.

```ts
fieldState: {
  layout: 'worth',
  pricelens: { table: 'recent' },
  highlight: { class: 'wpa', wpaThreshold: 0.3,   // |ΔWP| ≥ 30 in 100
               lift: 0.12, boost: 0.8, othersDim: 0.25 }
}
```

- **Encoding (mirrors the pipeline's `wpa_buffer` decode spec):** byte = 127 +
  round(wpa×127) clamped 0..254 (127 = zero swing; decode (byte−127)/127,
  resolution ≈ 0.008); **byte 255 = sentinel** "no honest tag" (D/L,
  undecided, short-target matches — exactly what the win grids exclude).
  Constants `WPA_ZERO_BYTE` / `WPA_SENTINEL_BYTE` in `field/types.ts`.
- `wpaThreshold` (0..1) resolves to byte units as max(1, round(t×127)) — a
  threshold of 0 can never match the whole field, and **sentinel balls never
  match** (they take the others path silently; never surface them as swings).
- **Pipeline dependency:** `wpa.u8` (`FieldData.wpa`); auto-detected,
  `hasWpaAttr` flips true. Absent → every ball bakes the sentinel and the
  class matches nothing (graceful). Packed into `aPrice` with the state cell
  (§19.6).
- The highlight class is position-affecting only via its lift (shared
  `computeCore()`), so the pick pass tracks lifted swings exactly.
