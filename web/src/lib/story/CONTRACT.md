# Story Shell Contract — R1a (+ R1b field capabilities: §11 picking · §12 filtering)

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
  layout: 'free' | 'columns' | 'wall' | 'assembly';
  reveal?: number;    // assembly stream-in 0..1 (chronological by point index)
  dim?: number;       // global luminance ×, 1 = full (default 1)
  wplDim?: number;    // WPL-points luminance × (C1-2 shelf staging; default 1)
  labels?: number;    // season-columns DOM label plane opacity (default 0)
  highlight?: {       // uniform-driven subset: lift/tint points matching a class
    class: 'dot'|'single'|'twoThree'|'four'|'six'|'other'|'wicket';
    lift: number;     // world-units vertical lift (frustum y ∈ [-1,1])
    boost: number;    // brightness boost for matches (0..1)
    othersDim: number;// luminance × for everything else (1 = none)
    skipWpl?: boolean;// WPL points never match — they take the others path
                      //   (C1-5: the IPL's sixes lift; the WPL's stay shelved)
  } | null;
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
`reveal:1` it is position-identical to `free`, so assembly→free is seamless). All scalar fields lerp during the morph; highlight lift/boost/dim
lerp so subsets glide in and out.

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
