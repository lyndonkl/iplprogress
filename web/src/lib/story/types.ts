import type { Component } from 'svelte';
import type { FieldHandle } from '$lib/field/field';
import type {
	CascadeClass,
	ConstellationPhase,
	DismissalKind,
	FilterMode,
	HighlightClass,
	LayoutId,
	ResortableClass,
	ResortColumns,
	RiversClass
} from '$lib/field/types';
import type { FootnoteId } from './footnotes';

/**
 * The scene system: the story is an ordered list of SceneDefs composed into
 * one scroll timeline over ONE persistent field renderer (it never unmounts).
 * See CONTRACT.md in this directory for the full contract and ownership map.
 */

export type ChapterId =
	| 'coldopen'
	| 'picker'
	| 'ch1'
	| 'ch2'
	| 'ch3'
	| 'ch4'
	| 'interlude'
	| 'ch5'
	| 'ch6'
	| 'ch7'
	| 'ch8'
	| 'ch9'
	| 'endcard'
	| 'bowl';

/** Uniform-driven subset highlight: lift/tint points matching a class mask. */
export interface SubsetHighlight {
	/**
	 * which points match: an outcome class ('six', 'four', …), 'wicket', or
	 * 'wpa' (Ch 5 §21 — the biggest win-chance swings, gated by `wpaThreshold`)
	 */
	class: HighlightClass;
	/** world-units vertical lift for matching points (frustum is y ∈ [-1, 1]) */
	lift: number;
	/** brightness boost for matching points, 0..1 */
	boost: number;
	/** luminance multiplier for everything else, 0..1 (1 = no dimming) */
	othersDim: number;
	/**
	 * WPL points never match — they take the others path instead (C1-5: the
	 * IPL's sixes lift while the WPL's stay on its shelf). Default false.
	 */
	skipWpl?: boolean;
	/**
	 * ONLY read when `class` is 'wpa' (Ch 5 §21): the minimum ABSOLUTE
	 * win-chance swing (|ΔWP|, 0..1 — e.g. 0.3 = "moved the win chance by 30 in
	 * 100 or more") a ball must carry to match. Resolved against the wpa.u8
	 * byte encoding (|byte − 127| ≥ round(t × 127), floored at 1 so 0 never
	 * matches the whole field); sentinel-255 balls (no honest tag: D/L,
	 * undecided, short-target matches) never match. Default 0 → floor 1.
	 */
	wpaThreshold?: number;
}

/**
 * The subset re-sort (§7 capability — the C1-5 fireworks signature moment).
 * Declared on a scene's `fieldState`: the points matching `class` fly from the
 * base layout into per-season firework columns as the scene's morph scrubs
 * `engage` 0→1 (staggered per point, arcing up out of the wall → object
 * constancy), and settle back when the NEXT scene declares no re-sort (engage
 * lerps 1→0). A per-point two-tone recolor fades in with `tint` (drive it from
 * a caption step via SceneDef.dynamicState — it is a post-morph field change).
 * No new position buffers: the per-season stacking ordinal is derived
 * on-device from attrs + group ids. See CONTRACT §7.
 */
export interface SubsetResort {
	/** which points re-sort: an outcome class ('six', …) or 'wicket' ('wpa' is highlight-only) */
	class: ResortableClass;
	/** WPL points never re-sort — they stay on the wall (default false) */
	skipWpl?: boolean;
	/** which season groups become columns (default 'ipl' when skipWpl, else 'all') */
	columns?: ResortColumns;
	/** 0 = base layout · 1 = matching points fully stacked in columns (default 0) */
	engage: number;
	/** world-units peak of the lift arc during the flight (default 0.5) */
	lift?: number;
	/** two-tone recolor strength 0..1: top-10 specialists vs everyone else (default 0) */
	tint?: number;
	/** luminance × for everything else while engaged (default 0.12 — wall dims hard) */
	othersDim?: number;
}

/**
 * The run-out cascade (§14 capability — the C2-4 hero subset-highlight). A
 * cross-cutting SEASON-SWEPT flash+fall of the run-out subset, declared on a
 * scene's `fieldState` over the held `worms` layout. It composes with the base
 * layout and does NOT spend a second controlling morph (like `highlight` and
 * `resort`). As `sweep` advances 0→1 each season's run-out cohort flashes red
 * and ejects downward TOGETHER (Gestalt common fate — one discrete pulse per
 * season), then fades. Drive `sweep` across the hold from a caption step via
 * `SceneDef.dynamicState` (it is a post-morph field change, like the C1-5 tint
 * and the C1-2 heat beat). The NEXT scene declaring no cascade lerps `sweep`
 * back to 0 — the run-outs return (reversible, the reverse leg is free).
 *
 * MEMBERSHIP: the shell reads a per-point `aRunOut` GL flag, seeded from
 * attrs.u8 bit 6. Until the pipeline re-encodes that bit, the scene supplies
 * membership at runtime with `field.setRunouts(indices)` (a CPU index set
 * derived from the columnar `wicket_kind == 'run out'`). See CONTRACT §14.
 */
export interface RunoutCascade {
	/** which subset cascades — only 'runOut' today (aRunOut flag) */
	class: CascadeClass;
	/** 0→1 season pointer: cohorts up to this season have flashed red + fallen (default 0) */
	sweep: number;
	/** red flash strength 0..1 — the beat-gated hue exception (default 1) */
	tint?: number;
	/** world-units downward eject depth for a fully fallen point (default 0.9) */
	fall?: number;
	/** residual alpha × for a fully fallen point (default 0 — fully gone) */
	fade?: number;
	/** team-glow desaturation 0..1 through the cascade (red-team guard; default 1) */
	muteIdentity?: number;
}

/**
 * The dismissal rivers (§16 capability — the Ch 3 hero subset-highlight). A
 * cross-cutting subset that streams the bowler-credited wicket points OUT of the
 * `frontier` clouds into a FLAT-BASELINE 100%-stacked band (one strip per season,
 * bands = dismissal kinds, thickness = that season's kind share), and back. It
 * composes with the `frontier` layout and does NOT spend a second controlling
 * morph (like `highlight`, `resort` and `cascade`). As `engage` scrubs 0→1 the
 * wickets fly out and stack; the NEXT scene declaring no rivers lerps `engage`
 * back to 0 and they settle into their clouds (reversible, the reverse leg is
 * free). Drive `engage` across the hold from a caption step via
 * `SceneDef.dynamicState` (a post-morph field change, like the C1-5 tint). The
 * wicket points recolour categorically by dismissal kind (the ONE gated hue
 * exception in Ch 3), weighted by `tint`.
 *
 * MEMBERSHIP: the shell reads a per-point `aDismissal` GL flag (-1 none / 0
 * bowled / 1 lbw / 2 caught / 3 stumped). The scene supplies it at runtime with
 * `field.setDismissals(kindByIndex)` (a per-point array derived from the columnar
 * `wicket_kind`, run-outs / retired excluded). See CONTRACT §16.
 */
export interface SubsetRivers {
	/** which subset streams — only 'wicket' today (the bowler-credited wickets) */
	class: RiversClass;
	/** 0 = points in their clouds · 1 = fully stacked into the bands (default 0) */
	engage: number;
	/**
	 * band stack order bottom→top; default ['bowled','lbw','stumped','caught'] so
	 * the two woodwork dismissals sit adjacent + baseline-anchored as one "stumps"
	 * group. List all four kinds.
	 */
	kinds?: DismissalKind[];
	/** categorical dismissal-kind recolor strength 0..1 — the hue exception (default 1) */
	tint?: number;
	/** luminance × for non-wicket points while engaged (default 0.12) */
	othersDim?: number;
	/** team-glow desaturation 0..1 through the beat (red-team guard; default 1) */
	muteIdentity?: number;
}

/**
 * The waterline (§18 capability — the Ch 4 rising going rate). A cross-cutting
 * LEVEL over the held `tide` layout, declared on a scene's `fieldState`. It
 * composes with the layout and does NOT spend a second controlling morph (like
 * `highlight`, `resort`, `cascade` and `rivers`). A first-innings column whose
 * innings TOTAL sits below `level` (the going rate for the scrubbed season, in
 * runs) is DROWNED — dimmed toward the reservoir on LUMINANCE only, never a hue
 * change, so hue stays identity. Drive `level` across the hold from a caption
 * step via `SceneDef.dynamicState` (a post-morph field change, like the C1-5
 * tint): as the reader scrubs the season pointer the water RISES. The NEXT scene
 * declaring no waterline lets `level` fall away (reversible — the reverse leg is
 * free). The waterline LINE, the fixed 165 ghost line and the 200 / 230 rules are
 * pure annotation-plane SVG the scene draws itself via `tidePoint` /
 * `tideTotalToY` + `field.projectToCss`; this capability only drives the column
 * dim. Reservoir vs first-innings membership is supplied once via
 * `field.setFirstInnings`. See CONTRACT §18.
 */
export interface Waterline {
	/**
	 * the going rate for the scrubbed season, in RUNS (e.g. 165 → 206). A
	 * first-innings column whose innings total is below this drowns. Lerps as the
	 * scene scrubs (the water rises), and drains to the floor on the reverse leg.
	 */
	level: number;
	/** luminance × for a drowned column, 0..1 (default 0.18 — dims one-plus stop) */
	drownDim?: number;
	/** the picked team's columns keep their identity glow even when drowned (default true) */
	teamKeepLit?: boolean;
	/**
	 * OPTIONAL world-y for the fixed 165 ghost line — carried for the scene's
	 * convenience only; the FIELD does not read it (the ghost line, like the 200 /
	 * 230 rules, is annotation-plane SVG the scene draws via `tideTotalToY`).
	 */
	ghostLevel?: number;
}

/**
 * The pricelens (§19 capability — the Ch 5 worth-grid color state). A
 * cross-cutting COLOR state over the held `worth` layout, declared on a scene's
 * `fieldState`. It composes with the layout and does NOT spend a second
 * controlling morph (the Ch 4 fixed-columns/moving-water discipline: the grid
 * holds, the prices move). Each table id names a 200-entry per-cell LUMINANCE
 * table the scene fed ONCE via `field.setWorthTables()` (cell = over×10 +
 * wicketsDown, the restate.u8 convention); the shader renders
 * `mix(from, table, mix)` and then applies the §0.1 density-normalization gain
 * (derived on-device from restate.u8 cell populations) so a cell's INTEGRATED
 * brightness tracks its price, never its point count. LUMINANCE only — hue
 * stays identity. The C5-6a era flip is `{ from: 'early', table: 'recent' }`
 * with `mix` driven 0→1 from `SceneDef.dynamicState` (a post-morph field
 * change, like the C1-5 tint / cascade sweep / waterline level); the dip-to-
 * dark re-light staging is the scene driving `dim` down and back in the same
 * dynamicState. A scene declaring no pricelens renders `worth` with the
 * neutral ramp (density gain only); a no-op for every prior layout. An unknown
 * / not-yet-fed table id renders the neutral ramp (dev-warned). See CONTRACT §19.
 */
export interface PriceLens {
	/** the active table id ('early' | 'recent' | 'rise' | 'wpl' — scene-defined names) */
	table: string;
	/**
	 * optional mix SOURCE table: when set, the lens renders mix(from, table, mix)
	 * — the era flip / lens landing. Omitted → the lens is pure `table`.
	 */
	from?: string | null;
	/**
	 * 0 = pure `from` · 1 = pure `table` (default 1). Drive it across the hold
	 * via `dynamicState` for the C5-6a flip; it lerps like any scalar between
	 * scenes that declare the same pair.
	 */
	mix?: number;
}

/**
 * The over rail (§20 capability — the Ch 5 set-piece six-ball lift). A
 * cross-cutting subset modifier (like `resort` / `cascade` / `rivers`: it
 * composes with any base layout and spends NO controlling morph): the named
 * field points — a tiny index set, the six(+) deliveries of ONE over, from
 * `scenes/ch5.json` — lift out of the field and fly to viewport-anchored rail
 * slots as `progress` scrubs 0→1, enlarging to hero size; the REST of the
 * field dims hard behind them (set-piece dimming). The flying balls render in
 * a dedicated GL OVERLAY draw on top of the 316k field so a hero ball is never
 * fogged by later-indexed points; the DOM ball chips (names and numbers) are
 * the SCENE's job, anchored to the slots via `field.projectToCss`, and the WP
 * worm is the SCENE's SVG on the annotation plane. Fully reversible: drive
 * `progress` from `SceneDef.dynamicState` (the C5-3 GSAP scrub maps its scroll
 * progress straight onto it, so a stray scroll can never desync the rail from
 * the captions), and the NEXT scene declaring no overrail lerps `progress`
 * back to 0 — the balls return to their exact field positions (the reverse leg
 * is free). Reduced motion: the resolved end state renders the balls AT their
 * slots instantly (the scene's six-panel DOM strip carries the fallback
 * content). Inactive (empty `indices`) = byte-identical for every prior scene.
 * See CONTRACT §20.
 */
export interface OverRail {
	/** field point indices of the over's balls, bowling order (≤ 8, from scenes/ch5.json) */
	indices: readonly number[];
	/**
	 * per-ball slot anchors as VIEWPORT FRACTIONS [x, y] (x 0 left → 1 right,
	 * y 0 top → 1 bottom — CSS-like, so a slot projects to the same spot the
	 * scene's DOM chip occupies). One per index; missing slots default to an
	 * evenly-spaced row across the middle of the viewport.
	 */
	slots?: readonly (readonly [number, number])[];
	/** 0 = balls in the field · 1 = balls at their slots (drive via dynamicState) */
	progress: number;
	/**
	 * luminance×alpha for the REST of the field at progress 1 (default 0.06 —
	 * dims hard; note alpha dims SATURATE on dense layouts because overlapping
	 * points re-accumulate coverage, so values above ~0.1 read barely dimmed)
	 */
	dimRest?: number;
	/** hero point-size multiplier at the slots (default 7) */
	scale?: number;
	/** world-units peak of the flight arc (default 0.35) */
	lift?: number;
}

/**
 * The constellation phase toggle (§22 capability — the Ch 6 hero map). A
 * cross-cutting POSITION state over the held `constellation` layout, declared on
 * a scene's `fieldState`. It is the exact analog of the Ch 5 `pricelens` (a
 * table swap over a held grid), except the table is star POSITIONS: the 23 star
 * centres lerp from phase table `from` to phase table `table` by `mix`. The
 * point-to-star assignment never changes — only the centres move, minimally and
 * Procrustes-locked (the whole season-cohort glides together), so the WPL never
 * crosses the men's worm. It is NOT a re-sort and NOT a second controlling
 * morph. The four tables are fed ONCE via `field.setStarTables`. Drive the C6-5
 * glide by setting `{ from, table, mix }` and lerping `mix` 0→1 from
 * `SceneDef.dynamicState` (a post-morph field change, like the pricelens `mix`);
 * per the orchestrator caveat also surface the active table through
 * `dynamicState` so a stray scroll re-application cannot revert the toggle. A
 * phase-less constellation scene (C6-2..C6-4) omits this → the 'all' map. NEVER a
 * live re-embed (a browser re-fit could mirror-flip the WPL, §0.1). See CONTRACT §22.
 */
/**
 * The impact-sub sparks (§23 capability — the Ch 7 subset lift). A cross-cutting
 * LUMINANCE + small-lift glow over the per-point `aSpark` flag (the 517 impact-sub
 * deliveries, baked once via `field.setSparks(indices)` — the `setRunouts` /
 * `setDismissals` precedent). It composes with any layout (the sparks glow as they
 * enter the IPL river over the held `flow` layout) and spends NO controlling morph
 * (like `highlight` / `cascade`). LUMINANCE/position only — hue stays identity.
 * Reversible: the NEXT scene declaring no `sparks` lerps `glow` back to 0. Drive
 * `glow` across the hold from a caption step via `SceneDef.dynamicState` (a
 * post-morph field change, like the cascade `sweep` / rivers `engage`). Inactive at
 * `glow` 0 (every prior scene byte-identical). See CONTRACT §23.
 */
export interface SparkSubset {
	/** spark brightness/glow strength 0..1 (0 = inactive — no spark effect) */
	glow: number;
	/** world-units vertical lift for spark points while glowing (default 0) */
	lift?: number;
	/** luminance × for non-spark points while the sparks glow (default 1 — no dimming) */
	othersDim?: number;
}

/**
 * The review chips (§25 capability — the Ch 8 subset-highlight). A cross-cutting
 * subset over the held `matchdots` layout, declared on a scene's `fieldState`. The
 * 988 review deliveries fly OUT of the held match-dots into per-team green/red chip
 * stacks (one column per franchise, struck-down red at the bottom, upheld green on
 * top) as `engage` scrubs 0→1 (the setDismissals/setSparks precedent — it composes
 * with the matchdots layout and spends NO controlling morph). The NEXT scene
 * declaring no reviews lerps `engage` back to 0 and the chips settle back onto their
 * match-dots (reversible, the reverse leg is free). Drive `engage` across the hold
 * from a caption step via `SceneDef.dynamicState` (a post-morph field change, like
 * the rivers `engage`).
 *
 * MEMBERSHIP: the scene supplies it once via `field.setReviews({ indices, team,
 * outcome })` — `indices` the 988 review-delivery point indices, `team` each chip's
 * franchise LANE index, `outcome` 0 (struck down / the call stood) or 1 (upheld /
 * paid off). The field bakes the review code into `aDismissal` and the packed
 * lane+slot into `aRiverPos` (NO new attribute; `aTeam` is left untouched so
 * team-ignite stays correct in every chapter). The outcome recolor separates by
 * LUMINANCE not hue alone (green LIGHTER, red DARKER), so the "mostly red / mostly
 * the call stood" read survives red-green colorblindness. See CONTRACT §25.
 */
export interface ReviewSubset {
	/** 0 = review balls held on their match-dots · 1 = fully flown into the chip stacks (default 0) */
	engage: number;
	/** green/red outcome recolor strength 0..1 — the luminance-separated CVD-safe recolor (default 1) */
	tint?: number;
	/** luminance × for non-review points while the chips are engaged (default 0.12) */
	othersDim?: number;
}

export interface ConstellationPhaseState {
	/** the active/target phase map: 'all' | 'powerplay' | 'middle' | 'death' */
	table: ConstellationPhase;
	/**
	 * optional lerp SOURCE map: when set, the stars glide mix(from, table, mix) —
	 * the C6-5 phase glide. Omitted → the stars sit at `table` (no movement).
	 */
	from?: ConstellationPhase | null;
	/**
	 * 0 = pure `from` · 1 = pure `table` (default 1). Drive it across the hold via
	 * `dynamicState` for the C6-5 glide; it lerps like any scalar between scenes
	 * that declare the same pair.
	 */
	mix?: number;
}

/**
 * A scene's declarative field state — the layout the field ARRIVES at while
 * the scene scrubs in, plus the cross-cutting uniform states. Omitted fields
 * take the defaults in fieldstate.ts (reveal 1 · dim 1 · wplDim 1 · labels 0 ·
 * no highlight · teamIgnite true).
 */
export interface SceneFieldState {
	layout: LayoutId;
	/** assembly stream-in end value (only meaningful with layout 'assembly') */
	reveal?: number;
	/** global luminance multiplier — 1 full, lower = dimmed (loop stops when idle regardless) */
	dim?: number;
	/** WPL-points luminance multiplier (C1-2 shelf staging) — 1 full */
	wplDim?: number;
	/** season-columns DOM label plane opacity 0..1 */
	labels?: number;
	/** subset highlight, or null/omitted for none */
	highlight?: SubsetHighlight | null;
	/** subset re-sort into firework columns, or null/omitted for none (§7) */
	resort?: SubsetResort | null;
	/** season-swept run-out flash+fall over worm-space, or null/omitted for none (§14) */
	cascade?: RunoutCascade | null;
	/** dismissal wicket-subset stream into the flat-baseline band over the frontier plane, or null/omitted for none (§16) */
	rivers?: SubsetRivers | null;
	/** rising going-rate level that drowns first-innings columns below it over the tide skyline, or null/omitted for none (§18) */
	waterline?: Waterline | null;
	/** per-cell price recolor over the worth grid, or null/omitted for the neutral ramp (§19) */
	pricelens?: PriceLens | null;
	/** the set-piece six-ball lift to viewport-anchored rail slots, or null/omitted for none (§20) */
	overrail?: OverRail | null;
	/** the constellation phase toggle over the held season map, or null/omitted → the 'all' map (§22) */
	phase?: ConstellationPhaseState | null;
	/**
	 * twin-rivers divergence reveal over the held `flow` layout (§23): 0 = the rivers
	 * sit at the table's flat BASELINE heights, 1 = at their TRUE run-rate heights (so
	 * the post-2023 IPL stretch climbs away from the WPL). Only meaningful with the
	 * `flow` layout + a `baseHeights`-carrying river table; default 1 (true heights).
	 * Drive 0→1 across the hold via `dynamicState` for C7-3's "flat, then lift". At 1
	 * (the settled + reduced-motion end state) the rivers show the honest picture.
	 */
	flowLift?: number;
	/** the impact-sub spark glow over the `aSpark` subset, or null/omitted for none (§23) */
	sparks?: SparkSubset | null;
	/**
	 * the toss-split lift over the held `matchdots` layout (§24 — the Ch 8 controlling
	 * morph's one held scalar, the flowLift analog): 0 = every dot on its neutral match
	 * centroid, 1 = each dot lifted into its toss lane (winner batted first → upper lane,
	 * winner chose to field → lower lane). Only meaningful with the `matchdots` layout +
	 * a fed match table; default 0. Drive 0→1 across the hold via `dynamicState` for the
	 * C8-3 lane split (the field-first river swells straight from the data's toss shift).
	 */
	matchSplit?: number;
	/** the review-chip subset fly-out over the held match-dots, or null/omitted for none (§25) */
	reviews?: ReviewSubset | null;
	/** whether the picked team's balls stay ignited (default true — §2 standing rule) */
	teamIgnite?: boolean;
	/**
	 * era-relative recolor blend for the C1-2 thesis beat (default 0). 0 = the
	 * establishing outcome colour; 1 = every ball recoloured by its wallheat cell
	 * (how far it beats the pooled 2008-2010 batter at the SAME ball-index), which
	 * cancels the wall's horizontal acceleration gradient so the early-ball corner
	 * ignites bottom→top. Drive it 0→1 during the hold via `dynamicState` (it is a
	 * post-morph field change, like the C1-5 tint). Must be 0 wherever a re-sort
	 * is engaged (the beat is staged before the fireworks). Team-ignite wins on top.
	 */
	wallHeatMix?: number;

	/* ---- facet filter (§12 capability — the Bowl instrument) ----------------
	 * A point is VISIBLE iff it passes EVERY active facet (team AND season AND
	 * match); failing points are hidden/ghosted per `filterMode` and are removed
	 * from the GPU pick pass (only visible balls are tappable). Each facet is
	 * independent; `null`/omitted means it imposes no constraint. Omit them all
	 * (the R1a default) and the field is unfiltered. The Bowl opens with
	 * `filterTeam` set so it is never blank. Interactive facet changes call
	 * `field.setFilter` imperatively; these declarative fields set the entry
	 * state. See CONTRACT §12. */
	/** teams.json id to keep, or null/omitted = all teams */
	filterTeam?: number | null;
	/** season YEAR to keep (any league's group for that year), or null = all */
	filterSeason?: number | null;
	/**
	 * match index to keep, or null = all. Needs the pipeline's OPTIONAL
	 * match_index.u16 buffer; a no-op without it — use `filterMatchRange` for the
	 * R1b famous-match preset instead. See CONTRACT §12.4.
	 */
	filterMatchIndex?: number | null;
	/**
	 * contiguous point-index range [lo, hi) to keep, or null = no range. Matches
	 * one game with zero new buffers (a match's deliveries are contiguous in
	 * point order) — the working path for R1b's famous-match preset.
	 */
	filterMatchRange?: readonly [number, number] | null;
	/** how filtered-out points render: 'hide' (α→0) or 'dim' ghost (default 'dim') */
	filterMode?: FilterMode;
}

/** Props every scene annotations component receives from the orchestrator. */
export interface SceneAnnotationProps {
	/** 0..1 scroll progress across this scene's section */
	progress: number;
	/** true while this scene owns the field */
	active: boolean;
	/** the persistent field renderer (null until data loads) */
	field: FieldHandle | null;
	/** prefers-reduced-motion: render end states, no interpolation */
	reduced: boolean;
}

export interface SceneDef {
	/** unique, stable id (also the default hash anchor) */
	id: string;
	/** which chapter directory owns this scene (nav grouping + progress) */
	chapter: ChapterId;
	/** hash anchor for deep links; defaults to id */
	anchor?: string;
	/** presence puts the scene in the persistent chapter nav */
	navLabel?: string;
	/** scroll length of the scene's section, in vh */
	scrollLength: number;
	/**
	 * OPTIONAL mobile-only scroll length (vh), used in place of `scrollLength`
	 * when the read-then-watch gate is active (mobile viewport or
	 * `?mobilecaptions=1`). Lengthen a scene here so the mobile caption's
	 * read beat + clear gap feel unhurried without touching desktop (which
	 * always uses `scrollLength`). Compute it with `readGapScrollLength()` from
	 * captionReveal.svelte.ts. Omit → mobile uses `scrollLength`. See CONTRACT §17.
	 */
	mobileScrollLength?: number;
	/**
	 * how much of the leading scroll (vh) drives the morph from the previous
	 * scene's fieldState to this one; the rest holds. Default min(140, scrollLength).
	 * Set equal to scrollLength for a whole-scene scrub (the assembly set piece).
	 */
	morphLength?: number;
	/**
	 * override the morph SOURCE state (defaults to the previous scene's
	 * fieldState). The cold-open assembly uses this to scrub reveal 0 → 1.
	 */
	fromState?: SceneFieldState;
	/** the field state this scene lands and holds */
	fieldState: SceneFieldState;
	/**
	 * the live-rendered end state for prefers-reduced-motion jump-cuts
	 * (blueprint §2: never baked frames). Defaults to fieldState.
	 */
	reducedMotionEndState?: SceneFieldState;
	/**
	 * OPTIONAL held-state modulator: when present, the orchestrator resolves the
	 * scene's HELD (post-morph) field state through this on every progress tick,
	 * so a caption STEP can drive a single one-change field update during the
	 * hold (e.g. C1-5 step 3's two-tone re-sort recolor: raise `resort.tint`
	 * once progress crosses the step threshold). Constraints (do not break the
	 * morph budget): return `held` with only SCALAR aspects changed
	 * (dims / labels / highlight+resort boost/tint/othersDim) — never a new
	 * layout or a second position morph. Ignored under reduced motion (the
	 * reducedMotionEndState already carries the final state). See CONTRACT §7.
	 */
	dynamicState?: (progress: number, held: SceneFieldState) => SceneFieldState;
	/** DOM/SVG annotation layer, rendered inside the scene's scroll section */
	annotations: Component<SceneAnnotationProps>;
	/** per-scene "how we computed this" sheet (typed registry key) */
	footnote?: FootnoteId;
}
