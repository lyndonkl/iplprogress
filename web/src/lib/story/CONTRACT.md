# Story Shell Contract — R1a

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
hover). Plain-text paragraphs only.

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

Scenes with `navLabel` appear in the persistent chapter nav (☰, appears after
the cold open; immediately on deep entry / return visits). Anchors are section
ids; the shell calls `ScrollTrigger.update()` on hashchange and honors an
entry hash after triggers mount. Future chapters are titles + `soon` tags in
`navplan.ts` — titles are commitments, numbers aren't.

## 7. File ownership map

| Path | Owner | Notes |
|---|---|---|
| `src/lib/story/**` | **shell** | scene system, orchestrator, footnote UI, nav, this contract |
| `src/lib/field/**` | **shell** | renderer, shaders, layouts, data loading — request changes, don't fork |
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
