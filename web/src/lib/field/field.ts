import * as THREE from 'three';
import {
	DEFAULT_RENDER_STATE,
	DISMISSAL_CODE,
	FILTER_DIM,
	LAYOUT_CODE,
	NO_FILTER,
	type ConstellationPhase,
	type DismissalKind,
	type FieldData,
	type FieldFilter,
	type FieldRenderState,
	type GroupMeta
} from './types';
import {
	computeColumns,
	computeWall,
	computeResortColumns,
	computeWorms,
	computeFrontier,
	computeRivers,
	computeTide,
	computeWorth,
	computeConstellation,
	constellationPoint,
	computeFlow,
	flowSeasonToX,
	flowRateToY,
	CONSTELLATION_PHASES,
	basePointPx,
	WORM_X_CAP,
	WORM_RUNS_CAP,
	TIDE_TOTAL_CAP,
	WORTH_GAIN_TARGET,
	WORTH_GAIN_MIN,
	WORTH_GAIN_POW,
	RAIL_MAX_SLOTS,
	type ColumnLayout,
	type WallLayout,
	type WormLayout,
	type FrontierLayout,
	type RiversLayout,
	type TideLayout,
	type WorthLayout,
	type ConstellationLayout,
	type FlowLayout
} from './layout';
import { makeVertexShader, fragmentShader, makePickVertexShader, pickFragmentShader } from './shaders';

/** Pick target edge, device px. The tap patch is rendered 1:1 into it; the
 *  readback scans outward from the centre → the effective pick radius is
 *  (PICK_PATCH-1)/2 device px (≈10 CSS px at DPR 2). Odd so there is an exact
 *  centre pixel. */
const PICK_PATCH = 41;

/**
 * The persistent field renderer (R0 spike, promoted to the story platform):
 * one THREE.Points object, ~316k points, orthographic 2.5D camera,
 * demand-mode rendering (blueprint §2: NO requestAnimationFrame loop while
 * idle — exactly one render per applyState / resize / DPR change), and a DOM
 * label plane projected through the same camera on every rendered frame.
 *
 * The renderer is state-driven: the story orchestrator resolves scene
 * fieldStates into FieldRenderState objects and calls applyState(). Identical
 * consecutive states are skipped entirely (idle scroll noise → zero renders).
 */

export interface FieldStats {
	/** total frames actually rendered — the demand-mode proof counter */
	frames: number;
	/** renders in the trailing 1s window (≈ fps while scrubbing) */
	fps: number;
	nPoints: number;
	/** current morph progress 0..1 (uProgress) */
	progress: number;
}

export interface FieldOptions {
	canvas: HTMLCanvasElement;
	/** the sized sticky-viewport element the canvas fills */
	container: HTMLElement;
	/** absolutely-positioned DOM layer for season labels */
	labelLayer: HTMLElement;
	data: FieldData;
	onRender?: (stats: Readonly<FieldStats>) => void;
}

export interface FieldHandle {
	/** apply a resolved render state; renders at most once (skips no-ops) */
	applyState(state: FieldRenderState): void;
	/** request exactly one render on the next animation frame */
	invalidate(): void;

	/* ---- GPU picking (§11) ------------------------------------------------- */
	/**
	 * Recover the field point nearest a tap/click at CSS coordinates (relative
	 * to the field container), or null if no visible point is within `radiusPx`.
	 * Filtered-out points (see setFilter) and not-yet-assembled points are NOT
	 * pickable. Demand-mode: renders a tiny offscreen patch ONCE and reads it
	 * back — no persistent loop, idle GPU stays ~0. Call it on the tap event.
	 * @param cssX horizontal CSS px inside the field container
	 * @param cssY vertical CSS px inside the field container
	 * @param radiusPx max distance in CSS px (default = the full patch radius)
	 */
	pickAt(cssX: number, cssY: number, radiusPx?: number): number | null;

	/* ---- keyboard select (§11) — no GPU, filter-aware CPU walks ------------- */
	/** first VISIBLE point index in chronological order, or null if the filter hides all */
	firstVisiblePoint(): number | null;
	/**
	 * step to the next VISIBLE point from `fromIndex` in chronological order
	 * (dir +1 forward, -1 back); null at the ends. Pass -1 as fromIndex with
	 * dir +1 to get the first visible point. For a keyboard focus cursor moving
	 * in screen space, use pickAt(x, y) with a generous radius instead.
	 */
	stepVisiblePoint(fromIndex: number, dir: 1 | -1): number | null;

	/* ---- facet filter (§12) — the Bowl instrument -------------------------- */
	/**
	 * Merge a partial facet filter into the live field and render once
	 * (demand-mode). For interactive scenes (the Bowl) where no scroll morph is
	 * competing; declarative scenes set the same facets via SceneFieldState.
	 */
	setFilter(partial: Partial<FieldFilter>): void;
	/** the currently applied facet filter */
	getFilter(): Readonly<FieldFilter>;
	/** whether the match_index buffer is loaded (i.e. the matchIndex facet works) */
	readonly hasMatchAttr: boolean;

	dispose(): void;
	/** project field/world coordinates to CSS px inside the container (annotation anchoring) */
	projectToCss(worldX: number, worldY: number): { x: number; y: number };
	/** current season-columns geometry (null before first resize) */
	getColumnLayout(): ColumnLayout | null;
	/** current ignition-wall geometry (null before first resize) */
	getWallLayout(): WallLayout | null;
	/**
	 * current subset re-sort column geometry (§7) — column centres, per-group
	 * subset counts and the height normalizer, for anchoring DOM column labels.
	 * null until a re-sort has been applied at least once.
	 */
	getResortLayout(): ResortColumnInfo | null;
	/**
	 * current worm-space geometry (§13 — Ch 2's controlling morph): the
	 * fixed-aspect, letterboxed plot box + display caps. Scenes register the par
	 * / anchor exemplar worms and the axes to the GL haze by mapping data points
	 * through `wormPoint(layout, ballsFaced, runs)` then `projectToCss`. null
	 * before the first resize. Rebuilt on resize.
	 */
	getWormLayout(): WormLayout | null;
	/**
	 * current frontier-plane geometry (§15 — Ch 3's controlling morph): the
	 * fixed-aspect, letterboxed box + economy/strike-rate display ranges + the
	 * seven-an-over line's world x + the axis end-anchor world coords + the
	 * bottom-left "cheap and deadly" home-zone box. Scenes register the SVG
	 * Pareto edge / ghost trail / reference lines by mapping data points through
	 * `frontierPoint(layout, economy, strikeRate)` then `projectToCss`. null
	 * before the first resize. Rebuilt on resize.
	 */
	getFrontierLayout(): FrontierLayout | null;
	/**
	 * current dismissal-rivers geometry (§16): the flat-baseline 100%-stacked band
	 * box, per-season strip x's, baseline/top world y, and the pooled-share band
	 * label anchors (bottom→top). Scenes draw the 0-to-100 share axis, the season
	 * axis and the band boundaries in SVG from `ch3.json`, registered to these
	 * world coords via `projectToCss`. null before the first resize. The band
	 * anchors reflect the last stack order seen by `applyState`/`setDismissals`.
	 */
	getRiversLayout(): RiversLayoutInfo | null;
	/**
	 * current tide-skyline geometry (§18 — Ch 4's controlling morph): the
	 * fixed-aspect, letterboxed box + the total-axis cap + per-season block
	 * x-centres + the reservoir band height. Scenes register the rising waterline,
	 * the 165 ghost / 200 / 230 reference rules and the season-axis labels to the
	 * GL skyline by mapping through `tidePoint(layout, gi, total)` /
	 * `tideTotalToY(layout, total)` then `projectToCss`. null before the first
	 * resize. Rebuilt on resize.
	 */
	getTideLayout(): TideLayout | null;
	/**
	 * current worth-grid geometry (§19 — Ch 5's controlling morph): the
	 * fixed-aspect, letterboxed 20-over × 10-wicket box + cell pitches. Scenes
	 * register cell rings / WPL hatching / readouts / axis labels to the GL cells
	 * by mapping through `worthCell(layout, over, wicketsDown)` (layout.ts — the
	 * exact shader mapping, 0 wickets at the TOP) then `projectToCss`. null
	 * before the first resize. Rebuilt on resize.
	 */
	getWorthLayout(): WorthLayout | null;
	/**
	 * Feed the per-phase star tables for the Ch 6 constellation (§22). `tables`
	 * maps each phase id ('all' | 'powerplay' | 'middle' | 'death') to its 23
	 * normalized (x,y) star centres (indexed by gi 0-22 — the `group_ids.u16`
	 * value), straight from `scenes/ch6.json` `constellation.stars`. Fed ONCE by
	 * the scene before the constellation engages; the field copies them into the
	 * `uStar` uniform (both phase slots) on demand and re-resolves the currently
	 * applied phase, so a scene may feed tables before OR after its fieldState
	 * first declares the layout / phase. Any subset of phases may be supplied;
	 * an unfed phase renders as the origin (a graceful collapse — R1..R5 never use
	 * the constellation). No positions cross the wire per point: the render reads
	 * `uStar[gi]` off the ball's group id. Re-calling replaces the whole set.
	 */
	setStarTables(tables: Partial<Record<ConstellationPhase, StarTable>>): void;
	/**
	 * current constellation geometry (§22 — Ch 6's controlling morph): the
	 * fixed-aspect (square) letterboxed box + the per-gi star WORLD coordinates
	 * for the live applied phase table + mix. Scenes register the men's worm
	 * polyline, the WPL dotted threads, the star labels, the persistent legend
	 * and the payoff sister-thread to the GL star centres via `stars[gi]` +
	 * `field.projectToCss`; arbitrary normalized coords (thread endpoints, the
	 * WPL cluster hull) map through `constellationPoint(layout, nx, ny)`. null
	 * before the first resize. Rebuilt on resize; star coords re-derived per read.
	 */
	getConstellationLayout(): ConstellationLayoutInfo | null;
	/**
	 * Feed the per-gi river table for the Ch 7 twin rivers (§23 — the `flow`
	 * layout). Fed ONCE by the scene (from `scenes/ch7.json`) before the flow
	 * layout engages, like `setStarTables` / `setWorthTables`. `heights[gi]` is the
	 * league-season's TRUE run rate (runs an over), indexed by gi (the
	 * `group_ids.u16` value); `baseHeights[gi]` is the flat baseline the river lifts
	 * FROM (drive `flowLift` 0→1 for the divergence reveal — the pipeline sets
	 * `baseHeights == heights` for the pre-rule seasons so only the post-fork climb
	 * moves; omit `baseHeights` for no lift). `rateLo`/`rateHi` are the "runs an
	 * over" axis range (world floor/ceiling); `bandThickness` is the decorative band
	 * height as a FRACTION of the axis (0..1, a constant, NOT a ball-count encoding);
	 * `forkSeason` is the fork year (2023) exposed as the world fork x on
	 * `getFlowLayout()`; `axisTicks` are run-rate values the scene labels. The field
	 * bakes them into the `uFlow` uniform against the letterboxed box (rebuilt on
	 * resize) — no positions cross the wire, no new per-point buffer. Re-calling
	 * replaces the table. A gi whose height is NaN has no river (collapses to the
	 * box centre — graceful; R1..R6 never use `flow`).
	 */
	setRiverTable(table: RiverTable): void;
	/**
	 * current twin-rivers geometry (§23 — Ch 7's controlling morph): the fixed-
	 * aspect, letterboxed box + the run-rate axis range + the per-gi season x's +
	 * the per-gi centreline WORLD coords for the LIVE `flowLift` (so the scene's SVG
	 * centrelines, the gap read and the axis marks track the divergence reveal) +
	 * the world fork x (the 2023 marker) + the decorative band half-thickness. Map
	 * an arbitrary (season, rate) through `flowSeasonToX` / `flowRateToY` (layout.ts)
	 * then `field.projectToCss`. null before the first resize OR before a river table
	 * is fed. Rebuilt on resize; the centres are re-derived from the live `flowLift`
	 * on every read.
	 */
	getFlowLayout(): FlowLayoutInfo | null;
	/**
	 * Feed the pricelens tables for the Ch 5 worth grid (§19). `tables` maps a
	 * table id (e.g. 'early' | 'recent' | 'rise' | 'wpl') to a 200-entry
	 * per-cell LUMINANCE array (0..1, cell index = over×10 + wicketsDown — the
	 * restate.u8 convention; the SCENE normalizes raw engine runs to luminance,
	 * because scale choices are editorial: the era flip shares one scale, the
	 * rise lens has its own). The field bakes each table into a row of the
	 * pricelens data texture alongside the §0.1 DENSITY GAIN it derives once
	 * from restate.u8 cell populations, so integrated cell brightness tracks the
	 * price, never the crowd. Up to 7 tables; re-calling replaces the whole set.
	 * O(1) per frame afterwards — demand mode preserved. Scenes then select
	 * tables declaratively via `SceneFieldState.pricelens` (table ids + mix).
	 */
	setWorthTables(tables: Record<string, ArrayLike<number>>): void;
	/** whether restate.u8 is loaded (the worth grid has real cells) */
	readonly hasStateAttr: boolean;
	/** whether wpa.u8 is loaded (the 'wpa' highlight class can match) */
	readonly hasWpaAttr: boolean;
	/**
	 * Set first-innings membership for the Ch 4 `tide` skyline (§18). Pass the
	 * point indices whose delivery is part of a FULL FIRST innings (the scene
	 * derives them from the columnar `innings` array); those balls build the
	 * innings-total columns, and every OTHER ball settles into the low-alpha
	 * reservoir haze behind the skyline (so "every ball ever is here" stays
	 * literally true). The field bakes the membership ONCE and re-derives the
	 * within-season column packing into the packed `aTide` attribute (no per-frame
	 * cost — demand mode preserved), then renders. Pass `null` to reset to "every
	 * ball builds a column" (the graceful default before the scene supplies
	 * membership; innings_total.u8 carries a total for every ball, so the layout
	 * works out of the box). See CONTRACT §18.
	 */
	setFirstInnings(indices: Iterable<number> | null): void;
	/**
	 * Set run-out membership for the C2-4 cascade (§14). Pass the point indices
	 * whose delivery is a run-out (the scene derives them from the columnar
	 * `wicket_kind == 'run out'`); the field bakes them into the per-point
	 * `aRunOut` GL flag ONCE (no per-frame cost — demand mode preserved) and
	 * renders. Pass `null` to revert to the pipeline seed (attrs.u8 bit 6). This
	 * is the working-today path until the pipeline re-encodes the run-out bit.
	 */
	setRunouts(indices: Iterable<number> | null): void;
	/**
	 * Set dismissal-kind membership for the C3-4 rivers (§16). Pass a per-point
	 * array (length nPoints) of dismissal codes — -1 = not a bowler-credited
	 * wicket (run-outs / retired excluded), 0 bowled, 1 lbw, 2 caught, 3 stumped
	 * — which the scene derives from the columnar `wicket_kind` (see CONTRACT §16).
	 * The field bakes it into the per-point `aDismissal` GL flag ONCE and
	 * recomputes the stacked band positions (no per-frame cost — demand mode
	 * preserved). Pass `null` to clear membership (all -1). The working-today path
	 * until the pipeline re-encodes dismissal-kind bits into attrs.u8.
	 */
	setDismissals(kindByIndex: ArrayLike<number> | null): void;
	/**
	 * Set impact-sub spark membership for the Ch 7 twin rivers (§23). Pass the point
	 * indices of the deliveries carrying an activated Impact Player substitution (the
	 * scene derives them from `scenes/ch7.json` `impact_subs.spark_indices` — the 517
	 * spark deliveries); the field bakes them into the per-point `aSpark` GL flag ONCE
	 * (no per-frame cost — demand mode preserved) and renders. Pass `null` to clear
	 * (all 0). The working-today path (the `setRunouts` / `setDismissals` precedent);
	 * there is no pipeline seed, so a `flow` scene MUST call this to light the sparks.
	 */
	setSparks(indices: Iterable<number> | null): void;
	readonly data: FieldData;
	readonly stats: Readonly<FieldStats>;
}

/**
 * The per-gi river table for `field.setRiverTable` (§23 — the Ch 7 twin rivers).
 * `heights` / `baseHeights` are indexed by gi (the `group_ids.u16` value), straight
 * from the scene's roll-up of `scenes/ch7.json` run rates.
 */
export interface RiverTable {
	/** per-gi TRUE run rate (runs an over), indexed by gi; NaN = the gi has no river */
	heights: ArrayLike<number>;
	/**
	 * per-gi flat BASELINE run rate the river lifts FROM at `flowLift` 0 (the
	 * divergence reveal). Omit → no lift (baseline == true, so `flowLift` is a no-op).
	 */
	baseHeights?: ArrayLike<number>;
	/** "runs an over" axis low (the box floor) */
	rateLo: number;
	/** "runs an over" axis high (the box ceiling) */
	rateHi: number;
	/** decorative band height as a FRACTION of the axis (0..1); a constant, NOT ball count */
	bandThickness: number;
	/** the fork season year (e.g. 2023) — exposed as the world fork x on getFlowLayout() */
	forkSeason: number;
	/** run-rate values the scene labels on the "runs an over" axis (scene convenience) */
	axisTicks?: number[];
}

/**
 * Twin-rivers geometry exposed to scenes (§23 — the Ch 7 flow layout). The fixed-
 * aspect, letterboxed box (from `computeFlow`) + the run-rate axis range and
 * decorative band half-thickness (from the fed river table) + the per-gi centreline
 * WORLD coords for the CURRENTLY APPLIED `flowLift` (so the scene's SVG centrelines,
 * the gap read and the axis marks track the divergence reveal) + the world fork x.
 * Map an arbitrary (season, rate) through `flowSeasonToX` / `flowRateToY` (layout.ts).
 */
export interface FlowLayoutInfo extends FlowLayout {
	/** "runs an over" axis range (world floor/ceiling map through flowRateToY) */
	rateLo: number;
	rateHi: number;
	/** decorative band half-thickness (world) — the ribbon's constant vertical spread */
	bandHalf: number;
	/** world x of the fork season (the 2023 marker the scene draws) */
	forkX: number;
	/** the fork season year (echoed from the fed river table) */
	forkSeason: number;
	/** run-rate values to label on the "runs an over" axis (echoed from the table) */
	axisTicks: number[];
	/** per-gi centreline WORLD coordinate for the live `flowLift` (length groupCount; NaN = no river) */
	centres: { x: number; y: number }[];
}

/** A pooled-share dismissal band, for anchoring the band's SVG label (§16). */
export interface RiversBand {
	kind: DismissalKind;
	/** cumulative-share lower bound 0..1 (pooled across all seasons) */
	loFrac: number;
	/** cumulative-share upper bound 0..1 (pooled) */
	hiFrac: number;
	/** world y of the band's pooled-share centre (label anchor) */
	centerY: number;
}

/** Dismissal-rivers geometry exposed to scenes (§16 — the C3-4 rivers). */
export interface RiversLayoutInfo extends RiversLayout {
	/** the four bands bottom→top, with pooled-share label anchors */
	bands: RiversBand[];
}

/**
 * One phase's star table for `field.setStarTables` (§22): 23 normalized (x,y)
 * star centres in the common [-1,1] frame, indexed by group id (gi 0-22, the
 * `group_ids.u16` value) — straight from `scenes/ch6.json` `constellation.stars`.
 */
export type StarTable = ReadonlyArray<readonly [number, number]>;

/**
 * Constellation geometry exposed to scenes (§22 — the Ch 6 season map). The
 * fixed-aspect (square), letterboxed box + the per-gi star world coordinates for
 * the CURRENTLY APPLIED phase table + mix (so the scene's SVG worm, dotted
 * threads, star labels, legend and the payoff sister-thread register exactly to
 * the live GL star centres, tracking the phase-toggle glide). For an arbitrary
 * normalized coordinate (a thread endpoint or a WPL cluster-hull vertex from
 * `ch6.json`) map it through `constellationPoint(layout, nx, ny)` then
 * `field.projectToCss`. Rebuilt on resize; the star coords are re-derived from
 * the live applied phase on every read.
 */
export interface ConstellationLayoutInfo extends ConstellationLayout {
	/** per-gi star world coordinates for the live applied phase table + mix (length groupCount) */
	stars: { x: number; y: number }[];
	/** the resolved active phase pair (null ids resolve to 'all') + lerp position */
	phaseA: ConstellationPhase;
	phaseB: ConstellationPhase;
	mix: number;
}

/** Subset re-sort column geometry exposed to scenes (§7 — the C1-5 fireworks). */
export interface ResortColumnInfo {
	/** world x of each group's column centre, indexed by gi (NaN = no column) */
	xs: number[];
	/** subset point count per group, indexed by gi (the column's raw height) */
	counts: number[];
	/** world y of the column base */
	bottom: number;
	/** world height at the tallest column */
	usableH: number;
	/** 1 / max per-group subset count — column top = bottom + counts[gi]*invMax*usableH */
	invMax: number;
	/** the gi's that received a column, in season order */
	gis: number[];
}

interface LabelEntry {
	el: HTMLElement;
	gi: number; // -1 IPL heading, -2 WPL heading
	kind: 'season' | 'league';
	worldX: number;
	worldY: number;
}

export function createField(opts: FieldOptions): FieldHandle {
	const { canvas, container, labelLayer, data, onRender } = opts;
	const n = data.nPoints;
	const groupCount = data.groups.length;

	// The match facet + exact-match tooltip need a per-point match index. It is
	// OPTIONAL: present only when the pipeline ships match_index.u16. Without it
	// the match preset filters by a contiguous point-index range instead (§12.4).
	const hasMatchAttr = data.matchIndex != null && data.matchIndex.length === n;

	// gi → season year, for the season facet (a season may span both leagues).
	const groupSeason = new Array<number>(groupCount).fill(0);
	for (const g of data.groups) groupSeason[g.gi] = g.season;

	// gi → the NEXT same-league season's gi (or -1), for the Ch 7 twin-rivers slope
	// (§23): each river segment tilts toward its next season so the band flows. Static
	// (the season groups never change), computed once.
	const nextGi = new Int32Array(groupCount).fill(-1);
	{
		const byLeague = new Map<string, GroupMeta[]>();
		for (const g of data.groups) {
			const arr = byLeague.get(g.league);
			if (arr) arr.push(g);
			else byLeague.set(g.league, [g]);
		}
		for (const arr of byLeague.values()) {
			arr.sort((a, b) => a.season - b.season);
			for (let i = 0; i < arr.length - 1; i++) nextGi[arr[i].gi] = arr[i + 1].gi;
		}
	}

	// season range → the run-out cascade's sweep normalizer (§14). The sweep maps
	// 0→1 across [minSeason, maxSeason], so each season's cohort has one phase.
	const minSeason = data.groups.reduce((m, g) => Math.min(m, g.season), Infinity);
	const maxSeason = data.groups.reduce((m, g) => Math.max(m, g.season), -Infinity);
	const seasonSpan = Math.max(1, maxSeason - minSeason);

	/* ---- per-point attributes: ordinal-in-group in one pass ------------- */
	// position vec3 = (index, gi, ordinal) — all exact integers in Float32.
	const record = new Float32Array(n * 3);
	const counters = new Uint32Array(groupCount);
	for (let i = 0; i < n; i++) {
		const g = data.groupIds[i];
		const o = counters[g]++;
		const j = i * 3;
		record[j] = i;
		record[j + 1] = g;
		record[j + 2] = o;
	}

	/* ---- three.js scene -------------------------------------------------- */
	const renderer = new THREE.WebGLRenderer({
		canvas,
		antialias: false,
		alpha: false,
		powerPreference: 'high-performance',
		preserveDrawingBuffer: false
	});
	renderer.setClearColor(0x0b0e14, 1);

	const scene = new THREE.Scene();
	const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
	camera.position.set(0, 0, 5);
	camera.lookAt(0, 0, 0);

	// per-group table: x = column centre x · y = wall row centre y
	const colVectors: THREE.Vector2[] = data.groups.map(() => new THREE.Vector2());

	// per-point re-sort ordinal (filled on demand, §7) and per-group column x
	const subOrd = new Float32Array(n);
	const resortX = new Float32Array(groupCount);
	// per-group dismissal-rivers strip centre x (filled on resize, §16)
	const riverX = new Float32Array(groupCount);
	// per-group tide season-block centre x (filled on resize, §18)
	const tideX = new Float32Array(groupCount);

	/* ---- constellation star tables (§22 — the Ch 6 season map) --------------
	 * The per-phase 23×(x,y) NORMALIZED star tables, fed once via setStarTables.
	 * uStar[gi] packs BOTH the active lerp endpoints (xy = phase A, zw = phase B);
	 * the shader lerps them by uStarMix. No per-point position ever crosses the
	 * wire — the render reads uStar off the ball's group id (position.y). */
	const starTables = new Map<ConstellationPhase, Float32Array>();
	const starVectors: THREE.Vector4[] = data.groups.map(() => new THREE.Vector4());
	// which (phaseA, phaseB) pair is currently copied into starVectors — so a
	// phase LERP (A/B fixed, mix moving) only touches uStarMix, never re-copies.
	let appliedStarKey = '';
	let appliedPhaseA: ConstellationPhase = 'all';
	let appliedPhaseB: ConstellationPhase = 'all';
	let appliedPhaseMix = 0;

	/* ---- twin-rivers river table (§23 — the Ch 7 flow layout) ----------------
	 * uFlow[gi] = (season centre x, flat-baseline y, true run-rate y, world slope
	 * toward the next same-league season), all in world units, baked from the fed
	 * river table against the letterboxed box (rebuilt on resize). No per-point
	 * position ever crosses the wire — the render reads uFlow off the ball's gi. */
	const flowVectors: THREE.Vector4[] = data.groups.map(() => new THREE.Vector4());
	let riverTable: {
		heights: Float64Array;
		base: Float64Array;
		rateLo: number;
		rateHi: number;
		bandThickness: number;
		forkSeason: number;
		axisTicks: number[];
	} | null = null;

	/* ---- worth-grid pricelens texture (§19) ---------------------------------
	 * 200 cells × 8 rows, RG float: R = the cell's price LUMINANCE (0..1, fed by
	 * the scene via setWorthTables), G = the cell's DENSITY GAIN, derived ONCE
	 * from restate.u8 cell populations (§0.1 binding: integrated cell brightness
	 * must track the price table, never the crowd — a dense cheap cell may never
	 * outshine a sparse expensive one). Row 0 is the always-present NEUTRAL ramp
	 * (lum 1 × gain); rows 1..7 are the scene's tables. ~12.8KB, created up
	 * front so the sampler uniform is always bound. */
	const WORTH_CELLS = 200;
	const WORTH_TABLE_ROWS = 8;
	const worthGain = new Float32Array(WORTH_CELLS).fill(1);
	// stateCellBuf is defined below with the geometry, but the counts only need
	// the raw data buffer — read it directly (identical source).
	if (data.stateCell && data.stateCell.length === n) {
		const counts = new Uint32Array(WORTH_CELLS);
		for (let i = 0; i < n; i++) counts[Math.min(data.stateCell[i], 199)]++;
		for (let c = 0; c < WORTH_CELLS; c++)
			if (counts[c] > 0)
				worthGain[c] = Math.min(
					1,
					Math.max(WORTH_GAIN_MIN, Math.pow(WORTH_GAIN_TARGET / counts[c], WORTH_GAIN_POW))
				);
	}
	const worthTexData = new Float32Array(WORTH_CELLS * WORTH_TABLE_ROWS * 2);
	for (let c = 0; c < WORTH_CELLS; c++) {
		worthTexData[c * 2] = 1; // row 0: the neutral ramp (full luminance ×
		worthTexData[c * 2 + 1] = worthGain[c]; //          the density gain)
	}
	const worthTex = new THREE.DataTexture(
		worthTexData,
		WORTH_CELLS,
		WORTH_TABLE_ROWS,
		THREE.RGFormat,
		THREE.FloatType
	);
	worthTex.minFilter = THREE.NearestFilter;
	worthTex.magFilter = THREE.NearestFilter;
	worthTex.needsUpdate = true;
	/** table id → texture row (1..7); row 0 = neutral, never in the map */
	const worthRows = new Map<string, number>();
	const worthWarned = new Set<string>();

	/** Resolve a pricelens table id to its texture row (null/unknown → neutral). */
	function worthRow(id: string | null): number {
		if (id === null) return 0;
		const r = worthRows.get(id);
		if (r != null) return r;
		if (import.meta.env.DEV && !worthWarned.has(id)) {
			worthWarned.add(id);
			console.warn(
				`[every-ball-ever] pricelens table '${id}' has not been fed via`,
				'field.setWorthTables — rendering the neutral ramp until it arrives.'
			);
		}
		return 0;
	}

	/**
	 * Feed / replace the pricelens tables (§19). Each table is a 200-entry
	 * per-cell LUMINANCE array (0..1; cell = over×10 + wicketsDown). Baked into
	 * texture rows 1..7 in insertion order alongside the density gain — one
	 * upload, O(1) per frame afterwards (demand mode preserved). Re-resolves the
	 * currently applied state's rows, so a scene may feed tables before OR after
	 * its fieldState first declares them.
	 */
	function setWorthTables(tables: Record<string, ArrayLike<number>>): void {
		if (disposed) return;
		worthRows.clear();
		worthWarned.clear();
		let row = 1; // row 0 stays the neutral ramp
		for (const [id, table] of Object.entries(tables)) {
			if (row >= WORTH_TABLE_ROWS) {
				if (import.meta.env.DEV)
					console.warn(
						`[every-ball-ever] setWorthTables: more than ${WORTH_TABLE_ROWS - 1} tables —`,
						`'${id}' and later ids ignored.`
					);
				break;
			}
			if (table.length !== WORTH_CELLS) {
				if (import.meta.env.DEV)
					console.warn(
						`[every-ball-ever] setWorthTables: table '${id}' has ${table.length} entries,`,
						`expected ${WORTH_CELLS} — ignoring it.`
					);
				continue;
			}
			const base = row * WORTH_CELLS * 2;
			for (let c = 0; c < WORTH_CELLS; c++) {
				const v = Number(table[c]);
				worthTexData[base + c * 2] = Number.isFinite(v) ? Math.min(1, Math.max(0, v)) : 0;
				worthTexData[base + c * 2 + 1] = worthGain[c];
			}
			worthRows.set(id, row);
			row++;
		}
		worthTex.needsUpdate = true;
		// the applied state may already name these tables — resolve rows now
		uniforms.uWorthRowA.value = worthRow(applied.worthTableA);
		uniforms.uWorthRowB.value = worthRow(applied.worthTableB);
		invalidate();
	}

	/* ---- constellation star tables (§22 — the Ch 6 season map) -------------- */
	/**
	 * Store / replace the per-phase star tables (§22). Each table is 23 normalized
	 * (x,y) pairs indexed by gi. Any subset of phases may be fed; an unfed phase
	 * stays absent → its stars collapse to the origin (graceful). Re-copies the
	 * live phase into uStar and re-renders, so a scene may feed tables before OR
	 * after its fieldState first declares the layout/phase (like setWorthTables).
	 */
	function setStarTables(tables: Partial<Record<ConstellationPhase, StarTable>>): void {
		if (disposed) return;
		starTables.clear();
		for (const phase of CONSTELLATION_PHASES) {
			const table = tables[phase];
			if (!table) continue;
			if (table.length !== groupCount) {
				if (import.meta.env.DEV)
					console.warn(
						`[every-ball-ever] setStarTables: phase '${phase}' has ${table.length} stars,`,
						`expected ${groupCount} — ignoring it.`
					);
				continue;
			}
			const buf = new Float32Array(groupCount * 2);
			for (let gi = 0; gi < groupCount; gi++) {
				buf[gi * 2] = Number(table[gi][0]) || 0;
				buf[gi * 2 + 1] = Number(table[gi][1]) || 0;
			}
			starTables.set(phase, buf);
		}
		// force a re-copy on the next apply, and refresh now if a phase is applied
		appliedStarKey = '';
		applyStarArrays(appliedPhaseA, appliedPhaseB, appliedPhaseMix);
		invalidate();
	}

	// Copy the (phaseA, phaseB) tables into the packed uStar vec4 array (xy = A,
	// zw = B) and set the lerp. The copy runs only when the phase PAIR changes;
	// a pure phase glide (A/B fixed, mix moving) only updates uStarMix, so the
	// toggle is a minimal per-frame touch (demand mode preserved).
	function applyStarArrays(a: ConstellationPhase, b: ConstellationPhase, mix: number): void {
		const key = `${a}>${b}`;
		if (key !== appliedStarKey) {
			appliedStarKey = key;
			const ta = starTables.get(a);
			const tb = starTables.get(b);
			for (let gi = 0; gi < groupCount; gi++) {
				starVectors[gi].set(
					ta ? ta[gi * 2] : 0,
					ta ? ta[gi * 2 + 1] : 0,
					tb ? tb[gi * 2] : 0,
					tb ? tb[gi * 2 + 1] : 0
				);
			}
			uniforms.uStar.value = starVectors;
		}
		uniforms.uStarMix.value = mix;
		appliedPhaseA = a;
		appliedPhaseB = b;
		appliedPhaseMix = mix;
	}

	function getConstellationLayout(): ConstellationLayoutInfo | null {
		if (!constellationLayout) return null;
		const ta = starTables.get(appliedPhaseA);
		const tb = starTables.get(appliedPhaseB);
		const mix = appliedPhaseMix;
		const stars: { x: number; y: number }[] = new Array(groupCount);
		for (let gi = 0; gi < groupCount; gi++) {
			const ax = ta ? ta[gi * 2] : 0;
			const ay = ta ? ta[gi * 2 + 1] : 0;
			const bx = tb ? tb[gi * 2] : 0;
			const by = tb ? tb[gi * 2 + 1] : 0;
			stars[gi] = constellationPoint(constellationLayout, ax + (bx - ax) * mix, ay + (by - ay) * mix);
		}
		return { ...constellationLayout, stars, phaseA: appliedPhaseA, phaseB: appliedPhaseB, mix };
	}

	/* ---- twin-rivers river table (§23 — the Ch 7 flow layout) --------------- */
	/**
	 * Store / replace the per-gi river table (§23) and bake it into the uFlow
	 * uniform against the current box. Fed once by the scene from scenes/ch7.json
	 * (like setStarTables / setWorthTables); a gi with a NaN height has no river and
	 * collapses to the box centre. Re-renders so the change shows immediately.
	 */
	function setRiverTable(table: RiverTable): void {
		if (disposed) return;
		if (table.heights.length !== groupCount) {
			if (import.meta.env.DEV)
				console.warn(
					`[every-ball-ever] setRiverTable: heights has ${table.heights.length} entries,`,
					`expected ${groupCount} (one per gi) — ignoring.`
				);
			return;
		}
		const heights = new Float64Array(groupCount);
		const base = new Float64Array(groupCount);
		for (let gi = 0; gi < groupCount; gi++) {
			const h = Number(table.heights[gi]);
			heights[gi] = h;
			const b = table.baseHeights ? Number(table.baseHeights[gi]) : h;
			base[gi] = Number.isFinite(b) ? b : h;
		}
		riverTable = {
			heights,
			base,
			rateLo: table.rateLo,
			rateHi: table.rateHi,
			bandThickness: Math.max(0, table.bandThickness),
			forkSeason: table.forkSeason,
			axisTicks: table.axisTicks ? table.axisTicks.slice() : []
		};
		applyFlowGeometry();
		invalidate();
	}

	// Bake the river table into the uFlow uniform (season x, baseline y, true y,
	// slope-to-next) against the current letterboxed box. Called on setRiverTable and
	// on resize. Cheap (groupCount groups) — no per-frame cost, demand mode holds.
	function applyFlowGeometry(): void {
		if (!riverTable || !flowLayout) return;
		const box = {
			bottom: flowLayout.bottom,
			height: flowLayout.height,
			rateLo: riverTable.rateLo,
			rateHi: riverTable.rateHi
		};
		for (let gi = 0; gi < groupCount; gi++) {
			const x = flowLayout.xs[gi];
			const h = riverTable.heights[gi];
			if (Number.isNaN(x) || !Number.isFinite(h)) {
				flowVectors[gi].set(0, 0, 0, 0); // no river → box centre (graceful)
				continue;
			}
			const trueY = flowRateToY(box, h);
			const b = riverTable.base[gi];
			const baseY = Number.isFinite(b) ? flowRateToY(box, b) : trueY;
			flowVectors[gi].set(x, baseY, trueY, 0); // slope filled in the next pass
		}
		// world slope of each river segment toward its next same-league season (on the
		// TRUE heights), so the band tilts and reads as a continuous flowing ribbon.
		for (let gi = 0; gi < groupCount; gi++) {
			const ng = nextGi[gi];
			if (ng < 0) {
				flowVectors[gi].w = 0;
				continue;
			}
			const dx = flowVectors[ng].x - flowVectors[gi].x;
			flowVectors[gi].w = Math.abs(dx) > 1e-6 ? (flowVectors[ng].z - flowVectors[gi].z) / dx : 0;
		}
		uniforms.uFlow.value = flowVectors;
		uniforms.uFlowHalfPitch.value = flowLayout.cellHalfW;
		uniforms.uFlowBandHalf.value = riverTable.bandThickness * 0.5 * flowLayout.height;
	}

	function getFlowLayout(): FlowLayoutInfo | null {
		if (!flowLayout || !riverTable) return null;
		const lift = Math.min(1, Math.max(0, applied.flowLift));
		const centres: { x: number; y: number }[] = new Array(groupCount);
		for (let gi = 0; gi < groupCount; gi++) {
			const v = flowVectors[gi];
			if (Number.isNaN(flowLayout.xs[gi]) || !Number.isFinite(riverTable.heights[gi])) {
				centres[gi] = { x: NaN, y: NaN };
			} else {
				centres[gi] = { x: v.x, y: v.y + (v.z - v.y) * lift };
			}
		}
		return {
			...flowLayout,
			rateLo: riverTable.rateLo,
			rateHi: riverTable.rateHi,
			bandHalf: riverTable.bandThickness * 0.5 * flowLayout.height,
			forkX: flowSeasonToX(flowLayout, riverTable.forkSeason),
			forkSeason: riverTable.forkSeason,
			axisTicks: riverTable.axisTicks.slice(),
			centres
		};
	}

	/* ---- over-rail uniform arrays (§20) — sized to RAIL_MAX_SLOTS ----------- */
	const railIdxArr = new Float32Array(RAIL_MAX_SLOTS).fill(-9999);
	const railSlotVecs: THREE.Vector2[] = Array.from(
		{ length: RAIL_MAX_SLOTS },
		() => new THREE.Vector2(0.5, 0.5)
	);

	const uniforms: Record<string, THREE.IUniform> = {
		uProgress: { value: 0 },
		uLayoutA: { value: LAYOUT_CODE.free },
		uLayoutB: { value: LAYOUT_CODE.free },
		uReveal: { value: 1 },
		uInvN: { value: 1 / Math.max(1, n) },
		uHalfW: { value: 1 },
		uHalfH: { value: 1 },
		uPointScale: { value: 2 },
		uColHalfWidth: { value: 0.02 },
		uColBottom: { value: -0.68 },
		uColUsableH: { value: 1.38 },
		uInvMaxCount: { value: 1 },
		uCols: { value: colVectors },
		uWallLeft: { value: -0.84 },
		uWallWidth: { value: 1.68 },
		uWallCellHalfW: { value: 0.02 },
		uWallRowHalfH: { value: 0.02 },
		uDim: { value: 1 },
		uWplDim: { value: 1 },
		uHlClass: { value: -1 },
		uHlLift: { value: 0 },
		uHlBoost: { value: 0 },
		uOthersDim: { value: 1 },
		uHlSkipWpl: { value: 0 },
		uResortClass: { value: -1 },
		uResortSkipWpl: { value: 0 },
		uResortEngage: { value: 0 },
		uResortLift: { value: 0 },
		uResortTint: { value: 0 },
		uResortOthersDim: { value: 1 },
		uResortInvMax: { value: 1 },
		uResortX: { value: resortX },
		uPickedTeam: { value: -1 },
		uTeamColor: { value: new THREE.Color('#ffffff') },
		uWallHeatMix: { value: 0 },
		// facet filter (§12) — all inactive by default (R1a scenes unaffected)
		uFilterTeam: { value: -1 },
		uFilterSeason: { value: -1 },
		uGroupSeason: { value: groupSeason },
		uFilterRangeLo: { value: 0 },
		uFilterRangeHi: { value: 0 },
		uFilterMatch: { value: -1 },
		uFilterDim: { value: 1 },
		// worm-space layout (§13) — geometry set on every resize (letterboxed box)
		uWormLeft: { value: 0 },
		uWormWidth: { value: 1 },
		uWormBottom: { value: 0 },
		uWormHeight: { value: 1 },
		uWormXCap: { value: WORM_X_CAP },
		uWormRunsCapNorm: { value: WORM_RUNS_CAP / 255 },
		uWormCellHalfW: { value: 0.01 },
		uWormCellHalfH: { value: 0.01 },
		// run-out cascade (§14) — all inactive by default (R1 scenes unaffected)
		uCascadeClass: { value: -1 },
		uCascadeSweep: { value: 0 },
		uCascadeTint: { value: 0 },
		uCascadeFall: { value: 0 },
		uCascadeFade: { value: 1 },
		uCascadeMute: { value: 0 },
		uCascadeMinSeason: { value: Number.isFinite(minSeason) ? minSeason : 0 },
		uCascadeInvSpan: { value: 1 / seasonSpan },
		// frontier plane (§15) — geometry set on every resize (letterboxed box)
		uFrontierLeft: { value: 0 },
		uFrontierWidth: { value: 1 },
		uFrontierBottom: { value: 0 },
		uFrontierHeight: { value: 1 },
		uFrontierCellHalfW: { value: 0.01 },
		uFrontierCellHalfH: { value: 0.01 },
		// dismissal rivers (§16) — all inactive by default (R1/R2a scenes unaffected)
		uRiversClass: { value: -1 },
		uRiversEngage: { value: 0 },
		uRiversTint: { value: 0 },
		uRiversOthersDim: { value: 1 },
		uRiversMute: { value: 0 },
		uRiverBottom: { value: 0 },
		uRiverHeight: { value: 1 },
		uRiverHalfW: { value: 0.01 },
		uRiverX: { value: riverX },
		// tide skyline (§18) — geometry set on every resize (letterboxed box); the
		// packed per-point record (aTide) is baked on demand when tide first engages
		uTideBottom: { value: -0.5 },
		uTideHeight: { value: 1 },
		uTideInvCap: { value: 1 / TIDE_TOTAL_CAP },
		uTideBlockHalfW: { value: 0.02 },
		uTideCellHalfW: { value: 0.002 },
		uTideReservoirH: { value: 0.15 },
		uTideX: { value: tideX },
		// waterline (§18) — inactive by default (uWaterLevel < 0), so R1/R2 render
		// byte-identically (the drown branch is a shader no-op)
		uWaterLevel: { value: -1 },
		uWaterDrownDim: { value: 1 },
		uWaterTeamKeep: { value: 0 },
		// worth grid + pricelens (§19) — geometry set on every resize; the recolor
		// is gated on the worth layout being in the mix, so prior scenes are
		// byte-identical regardless of these values
		uWorthLeft: { value: 0 },
		uWorthWidth: { value: 1 },
		uWorthBottom: { value: -0.5 },
		uWorthHeight: { value: 1 },
		uWorthTex: { value: worthTex },
		uWorthRowA: { value: 0 },
		uWorthRowB: { value: 0 },
		uWorthMix: { value: 0 },
		// WPA subset-highlight threshold (§21) — only read while uHlClass == 7
		uHlWpaMin: { value: 0 },
		// over rail (§20) — inactive by default (uRailN 0), so every prior scene
		// renders byte-identically (the rail branches are shader no-ops)
		uRailN: { value: 0 },
		uRailIdx: { value: railIdxArr },
		uRailSlot: { value: railSlotVecs },
		uRailProgress: { value: 0 },
		uRailDim: { value: 1 },
		uRailScale: { value: 7 },
		uRailLift: { value: 0.35 },
		// constellation (§22) — the per-gi star table (xy = phase A, zw = phase B)
		// + the phase-toggle lerp + the letterboxed box geometry (set on resize).
		// Zero until setStarTables is fed, so the map collapses to the origin
		// (graceful; R1..R5 never use the constellation layout — byte-identical).
		uStar: { value: starVectors },
		uStarMix: { value: 0 },
		uConstHalfExtent: { value: 0.82 },
		uConstStarR: { value: 0.045 },
		// twin rivers (§23) — the per-gi river cell (season x, baseline y, true y,
		// slope) + the decorative band + the lift. Zero until setRiverTable is fed
		// (the rivers collapse to the origin — graceful; R1..R6 never use flow), and
		// the lift defaults to 1 (true heights). Read only while the flow layout is
		// in the mix, so every prior scene renders byte-identically.
		uFlow: { value: flowVectors },
		uFlowHalfPitch: { value: 0.02 },
		uFlowBandHalf: { value: 0.05 },
		uFlowLift: { value: 1 },
		// impact-sub sparks (§23) — inactive by default (uSparkGlow 0), so the spark
		// branch is a shader no-op and every prior scene renders byte-identically.
		uSparkGlow: { value: 0 },
		uSparkLift: { value: 0 },
		uSparkOthersDim: { value: 1 }
	};

	const geometry = new THREE.BufferGeometry();
	geometry.setAttribute('position', new THREE.BufferAttribute(record, 3));
	geometry.setAttribute('aAttrs', new THREE.BufferAttribute(data.attrs, 1, false));
	geometry.setAttribute('aBallsFaced', new THREE.BufferAttribute(data.ballsFaced, 1, false));
	geometry.setAttribute('aTeam', new THREE.BufferAttribute(data.team, 1, false));
	// wallheat is uploaded NORMALIZED (u8 → 0..1) so the shader reads aWallHeat
	// directly against WALLHEAT_NEUTRAL (73/255); every other attr is raw bytes.
	geometry.setAttribute('aWallHeat', new THREE.BufferAttribute(data.wallHeat, 1, true));
	// worm-space y (§13): cumulative innings runs, NORMALIZED (u8 → 0..1) like
	// wallheat. OPTIONAL buffer — until the pipeline ships cumruns.u8 it binds
	// zeros, so worm-space y collapses to the floor (graceful; R1 never uses worms).
	const cumRunsBuf =
		data.cumRuns && data.cumRuns.length === n ? data.cumRuns : new Uint8Array(n);
	geometry.setAttribute('aCumRuns', new THREE.BufferAttribute(cumRunsBuf, 1, true));
	// run-out cascade membership (§14): a 0/1 flag, seeded from attrs.u8 bit 6
	// (0x40). Client-baked, zero wire cost. Overridable at runtime via
	// setRunouts(indices) with a CPU set (columnar wicket_kind == 'run out'), so
	// the cascade works BEFORE the pipeline re-encodes the bit.
	// aRunOut is a packed runtime FLAG byte (no wire cost): bit0 = run-out (Ch 2
	// cascade, seeded from attrs bit 6 / setRunouts), bit1 = impact-sub spark (Ch 7,
	// setSparks). ONE attribute carries both — Ch 2 and Ch 7 never render together,
	// and adding a 15th vertex attribute overflows the ANGLE/Metal ceiling (verified:
	// "Too many attributes"), so the two single-bit flags share this byte (§23).
	const runOutFlag = new Uint8Array(n);
	for (let i = 0; i < n; i++) if ((data.attrs[i] & 64) !== 0) runOutFlag[i] = 1; // bit0
	geometry.setAttribute('aRunOut', new THREE.BufferAttribute(runOutFlag, 1, false));
	const runOutAttr = geometry.getAttribute('aRunOut') as THREE.BufferAttribute;
	geometry.setAttribute('aSubOrd', new THREE.BufferAttribute(subOrd, 1, false));
	const subOrdAttr = geometry.getAttribute('aSubOrd') as THREE.BufferAttribute;
	// frontier plane (§15): the interleaved bowler-season coordinate. Two
	// non-normalized u8 attributes off ONE interleaved buffer (byte 0 economy,
	// byte 1 strike rate) — zero copy, raw byte values 0..255 in-shader. OPTIONAL
	// buffer: until the pipeline ships bowlerplane.u8 it binds zeros, so the
	// frontier plane collapses to the bottom-left corner (graceful; R1/R2a never
	// use `frontier`).
	const bowlerPlaneBuf =
		data.bowlerPlane && data.bowlerPlane.length === n * 2 ? data.bowlerPlane : new Uint8Array(n * 2);
	const planeIB = new THREE.InterleavedBuffer(bowlerPlaneBuf, 2);
	geometry.setAttribute('aBowlEcon', new THREE.InterleavedBufferAttribute(planeIB, 1, 0, false));
	geometry.setAttribute('aBowlSr', new THREE.InterleavedBufferAttribute(planeIB, 1, 1, false));
	// dismissal-rivers membership (§16): a per-point kind flag (-1 none / 0 bowled
	// / 1 lbw / 2 caught / 3 stumped), client-baked via setDismissals from the
	// columnar wicket_kind. Default -1 (no membership) until the scene supplies it.
	const dismissalFlag = new Int8Array(n).fill(-1);
	geometry.setAttribute('aDismissal', new THREE.BufferAttribute(dismissalFlag, 1, false));
	const dismissalAttr = geometry.getAttribute('aDismissal') as THREE.BufferAttribute;
	// dismissal-rivers stacked y (§16): the baked 0..1 share-position within a
	// season strip; recomputed on-device whenever setDismissals or the stack order
	// changes (cached — no per-frame cost). Zero until the rivers first engage.
	const riverPos = new Float32Array(n);
	geometry.setAttribute('aRiverPos', new THREE.BufferAttribute(riverPos, 1, false));
	const riverPosAttr = geometry.getAttribute('aRiverPos') as THREE.BufferAttribute;
	// tide skyline (§18): ONE packed per-point attribute (to stay within the GPU's
	// vertex-attribute budget — MAX_VERTEX_ATTRIBS). It packs the innings-total byte
	// (tide y; runs = byte×2), the within-season packing slot quantized to 0..1023
	// (tide x), and the first-innings flag (0 = reservoir haze), baked on demand in
	// ensureTideData. innings_total.u8 is OPTIONAL — its bytes stay CPU-side here and
	// are baked into aTide; until it ships they are zero, so the skyline collapses to
	// the floor (graceful; R1/R2 never use tide). firstInnFlag is CPU-only membership
	// (default 1 = every ball builds a column), set via setFirstInnings.
	const inningsTotalBuf =
		data.inningsTotal && data.inningsTotal.length === n ? data.inningsTotal : new Uint8Array(n);
	const firstInnFlag = new Uint8Array(n).fill(1);
	const tidePack = new Float32Array(n);
	geometry.setAttribute('aTide', new THREE.BufferAttribute(tidePack, 1, false));
	const tideAttr = geometry.getAttribute('aTide') as THREE.BufferAttribute;
	// Ch 5 (§19/§21): ONE packed per-point attribute for the worth grid + the WPA
	// highlight (vertex-attribute budget, like aTide): restate.u8 state-cell byte
	// (bits 0-7; cell = over×10 + wicketsDown) + wpa.u8 byte × 256 (bits 8-15).
	// Both buffers are OPTIONAL: without restate.u8 every ball reads cell 0 (the
	// worth grid collapses to one cell — graceful, R1..R3b-1 never use `worth`);
	// without wpa.u8 the WPA byte bakes to the 255 sentinel, so the 'wpa'
	// highlight class matches nothing. Exact integers < 2^16 — safe in Float32.
	const hasStateAttr = data.stateCell != null && data.stateCell.length === n;
	const hasWpaAttr = data.wpa != null && data.wpa.length === n;
	const stateCellBuf = hasStateAttr ? data.stateCell! : new Uint8Array(n);
	const wpaBuf = hasWpaAttr ? data.wpa! : null;
	const pricePack = new Float32Array(n);
	for (let i = 0; i < n; i++)
		pricePack[i] = Math.min(stateCellBuf[i], 199) + 256 * (wpaBuf ? wpaBuf[i] : 255);
	geometry.setAttribute('aPrice', new THREE.BufferAttribute(pricePack, 1, false));
	// OPTIONAL match index (u16 → non-normalized float attr); gates the match facet
	if (hasMatchAttr)
		geometry.setAttribute('aMatchIndex', new THREE.BufferAttribute(data.matchIndex!, 1, false));
	// positions are procedural in-shader; give THREE an all-covering bound
	geometry.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 0, 0), 100);

	const material = new THREE.ShaderMaterial({
		glslVersion: THREE.GLSL3,
		vertexShader: makeVertexShader(groupCount, hasMatchAttr),
		fragmentShader,
		uniforms,
		transparent: true,
		depthTest: false,
		depthWrite: false,
		blending: THREE.NormalBlending
	});

	const points = new THREE.Points(geometry, material);
	points.frustumCulled = false;
	scene.add(points);

	/* ---- over-rail overlay draw (§20) — the hero balls render ON TOP ---------
	 * A second draw of the SAME geometry with the SAME uniforms object, compiled
	 * with RAIL_OVERLAY: its vertex pass culls everything except the ≤8 rail
	 * members (offscreen + pointSize 0 → zero fragment cost), and it draws AFTER
	 * the main pass (renderOrder 1), so a lifted hero ball is never fogged by
	 * later-indexed points in the 316k draw (draw order = point order there). The
	 * main pass culls the members while the rail is engaged (computeCore §20), so
	 * no ball is ever drawn twice. Visible ONLY while uRailN > 0 — the overlay
	 * costs nothing (not even a vertex pass) for every prior scene, preserving
	 * byte-identical rendering. */
	const railMaterial = new THREE.ShaderMaterial({
		glslVersion: THREE.GLSL3,
		vertexShader: makeVertexShader(groupCount, hasMatchAttr, true),
		fragmentShader,
		uniforms, // SAME object → layout/morph/dim state always matches the field
		transparent: true,
		depthTest: false,
		depthWrite: false,
		blending: THREE.NormalBlending
	});
	const railPoints = new THREE.Points(geometry, railMaterial);
	railPoints.frustumCulled = false;
	railPoints.renderOrder = 1;
	railPoints.visible = false;
	scene.add(railPoints);

	/* ---- GPU picking pass (§11) — shares geometry + uniforms with the visual
	   material, so points sit at the same place and honour the same filter; the
	   pick material only differs in the fragment (index-as-color) and blending.
	   Rendered on demand to a tiny offscreen target — never in the render loop. */
	const pickMaterial = new THREE.ShaderMaterial({
		glslVersion: THREE.GLSL3,
		vertexShader: makePickVertexShader(groupCount, hasMatchAttr),
		fragmentShader: pickFragmentShader,
		uniforms, // SAME object → morph/layout/filter always match the visual field
		transparent: false,
		depthTest: false,
		depthWrite: false,
		blending: THREE.NoBlending
	});
	const pickPoints = new THREE.Points(geometry, pickMaterial);
	pickPoints.frustumCulled = false;
	const pickScene = new THREE.Scene();
	pickScene.add(pickPoints);
	const pickTarget = new THREE.WebGLRenderTarget(PICK_PATCH, PICK_PATCH, {
		format: THREE.RGBAFormat,
		type: THREE.UnsignedByteType,
		depthBuffer: false,
		stencilBuffer: false,
		minFilter: THREE.NearestFilter,
		magFilter: THREE.NearestFilter
	});
	const pickPixels = new Uint8Array(PICK_PATCH * PICK_PATCH * 4);

	/* ---- DOM label plane -------------------------------------------------- */
	const labels: LabelEntry[] = buildLabels(labelLayer, data.groups);
	let columnLayout: ColumnLayout | null = null;
	let wallLayout: WallLayout | null = null;
	let wormLayout: WormLayout | null = null;
	let frontierLayout: FrontierLayout | null = null;
	let riversLayout: RiversLayout | null = null;
	let tideLayout: TideLayout | null = null;
	let worthLayout: WorthLayout | null = null;
	let constellationLayout: ConstellationLayout | null = null;
	let flowLayout: FlowLayout | null = null;
	let cssW = 1;
	let cssH = 1;

	/* ---- tide skyline state (§18 — the Ch 4 waterline morph) ---------------- */
	// The packed per-point tide record (aTide) is derived on-device the first time
	// the tide layout engages (or after setFirstInnings changes membership), then
	// cached — keyed by a first-innings version, so a scroll scrub never recomputes.
	// tideMaxCols (the busiest season's first-innings count) sizes the per-column x
	// jitter so the densest comb never overlaps.
	let tideVersion = 0; // bumped by setFirstInnings — invalidates the packing cache
	let tideKey = ''; // the version currently baked into aTide
	let tideMaxCols = 1; // max first-innings innings in any one season
	let tideActive = false; // whether the last applied state engaged the tide layout

	// Rebuild the tide geometry uniforms from the current box + packing density.
	function applyTideGeometry(): void {
		if (!tideLayout) return;
		uniforms.uTideBottom.value = tideLayout.bottom;
		uniforms.uTideHeight.value = tideLayout.height;
		uniforms.uTideInvCap.value = 1 / tideLayout.totalCap;
		uniforms.uTideBlockHalfW.value = tideLayout.blockHalfW;
		uniforms.uTideReservoirH.value = tideLayout.reservoirH;
		// per-column x jitter < the column pitch (2·blockHalfW / nCols) so the
		// densest season's thin columns stay separated, sparser seasons a touch more.
		uniforms.uTideCellHalfW.value = (tideLayout.blockHalfW / Math.max(1, tideMaxCols)) * 0.7;
		for (let gi = 0; gi < groupCount; gi++) {
			const x = tideLayout.xs[gi];
			tideX[gi] = Number.isNaN(x) ? 0 : x;
		}
		uniforms.uTideX.value = tideX;
	}

	// Identify first-innings innings as maximal contiguous runs of equal
	// (season, innings-total byte) among the first-innings points (deliveries of a
	// match are contiguous in point order, and first→second innings alternate, so
	// runs separate cleanly), rank each season's innings SHORT→TALL, and bake the
	// packed per-point record (aTide = innings byte + 256·packing-slot + first flag).
	// Reservoir points get the first flag cleared. Cached by the first-innings
	// version — O(n) + a per-season sort of ~70 innings, no per-frame cost.
	function ensureTideData(): void {
		const key = `${tideVersion}`;
		if (tideKey === key) return;
		tideKey = key;

		const inningsId = new Int32Array(n).fill(-1);
		const innTotal: number[] = [];
		const innGi: number[] = [];
		const innStart: number[] = [];
		let prevFirst = false;
		let prevGid = -1;
		let prevByte = -1;
		for (let i = 0; i < n; i++) {
			if (firstInnFlag[i] === 0) {
				prevFirst = false;
				continue;
			}
			const gid = data.groupIds[i];
			const byte = inningsTotalBuf[i];
			if (!prevFirst || gid !== prevGid || byte !== prevByte) {
				innTotal.push(byte * 2); // decode: byte → runs (innings_total.u8 scale 2)
				innGi.push(gid);
				innStart.push(i);
			}
			inningsId[i] = innTotal.length - 1;
			prevFirst = true;
			prevGid = gid;
			prevByte = byte;
		}

		const byGroup: number[][] = Array.from({ length: groupCount }, () => []);
		for (let k = 0; k < innTotal.length; k++) byGroup[innGi[k]].push(k);
		const innFrac = new Float32Array(innTotal.length);
		let maxCols = 1;
		for (let g = 0; g < groupCount; g++) {
			const arr = byGroup[g];
			// short→tall; tie-break on first point index so the packing is deterministic
			arr.sort((a, b) => innTotal[a] - innTotal[b] || innStart[a] - innStart[b]);
			const k = arr.length;
			if (k > maxCols) maxCols = k;
			for (let r = 0; r < k; r++) innFrac[arr[r]] = ((r + 0.5) / k) * 2 - 1;
		}

		// bake the packed record: byte + 256·colQuant(0..1023) + 262144·firstFlag
		const pack = tideAttr.array as Float32Array;
		for (let i = 0; i < n; i++) {
			const id = inningsId[i];
			const colFrac = id >= 0 ? innFrac[id] : 0;
			const colQuant = Math.round(((colFrac + 1) / 2) * 1023);
			pack[i] = inningsTotalBuf[i] + 256 * colQuant + (id >= 0 ? 262144 : 0);
		}
		tideAttr.needsUpdate = true;
		tideMaxCols = maxCols;
		applyTideGeometry();
	}

	// Bake first-innings membership (CPU-only) and re-derive the packed within-season
	// tide record if the tide layout is live. No per-frame cost — demand mode holds.
	function setFirstInnings(indices: Iterable<number> | null): void {
		if (disposed) return;
		if (indices === null) {
			firstInnFlag.fill(1); // graceful default: every ball builds a column
		} else {
			firstInnFlag.fill(0);
			for (const i of indices) if (i >= 0 && i < n) firstInnFlag[i] = 1;
		}
		tideVersion++;
		tideKey = ''; // invalidate the packing cache
		if (tideActive) ensureTideData();
		invalidate();
	}

	/* ---- run-out cascade membership (§14) ---------------------------------- */
	// Bake a CPU-supplied index set (or the pipeline seed) into the aRunOut flag
	// ONCE; there is no per-frame cost, so demand mode is preserved.
	function setRunouts(indices: Iterable<number> | null): void {
		if (disposed) return;
		const arr = runOutAttr.array as Uint8Array;
		for (let i = 0; i < n; i++) arr[i] &= 0xfe; // clear bit0, PRESERVE the spark bit1
		if (indices === null) {
			for (let i = 0; i < n; i++) if ((data.attrs[i] & 64) !== 0) arr[i] |= 1; // pipeline seed
		} else {
			for (const i of indices) if (i >= 0 && i < n) arr[i] |= 1;
		}
		runOutAttr.needsUpdate = true;
		invalidate();
	}

	/* ---- impact-sub spark membership (§23 — the Ch 7 sparks) ---------------- */
	// Bake a CPU-supplied index set (the 517 impact-sub deliveries) into aRunOut's
	// bit1 ONCE (bit0 = run-out is preserved), no per-frame cost — demand mode holds.
	// No pipeline seed (unlike the run-out bit) — a flow scene must call this to light
	// the sparks. Packed into aRunOut to stay inside the vertex-attribute budget.
	function setSparks(indices: Iterable<number> | null): void {
		if (disposed) return;
		const arr = runOutAttr.array as Uint8Array;
		for (let i = 0; i < n; i++) arr[i] &= 0xfd; // clear bit1, PRESERVE the run-out bit0
		if (indices !== null) for (const i of indices) if (i >= 0 && i < n) arr[i] |= 2;
		runOutAttr.needsUpdate = true;
		invalidate();
	}

	/* ---- dismissal rivers state (§16 — the C3-4 rivers) --------------------- */
	// setDismissals bakes per-point kind membership; ensureRiversData derives the
	// stacked band y-positions on-device the first time a given (order, membership)
	// engages, then caches — keyed by the stack order + a membership version, so a
	// scroll scrub never recomputes. Pooled kind totals feed the band label anchors.
	let dismissalVersion = 0;
	let riversKey = ''; // `${order.join(',')}@${dismissalVersion}` currently in aRiverPos
	let riversPooled: number[] = [0, 0, 0, 0]; // pooled counts by dismissal CODE
	let riversOrder: readonly DismissalKind[] = ['bowled', 'lbw', 'stumped', 'caught'];
	let riversActive = false; // whether the last applied state engaged the rivers

	function setDismissals(kindByIndex: ArrayLike<number> | null): void {
		if (disposed) return;
		const arr = dismissalAttr.array as Int8Array;
		if (kindByIndex === null) {
			arr.fill(-1);
		} else {
			for (let i = 0; i < n; i++) {
				const k = kindByIndex[i];
				arr[i] = k >= 0 && k <= 3 ? k : -1;
			}
		}
		dismissalAttr.needsUpdate = true;
		dismissalVersion++; // invalidate the rivers ordinal cache
		riversKey = '';
		// if the rivers are already engaged, recompute the stacked positions now so
		// the change is visible without waiting for the next applyState.
		if (riversActive) ensureRiversData(riversOrder);
		invalidate();
	}

	// Derive the per-point stacked band position (aRiverPos, 0 baseline → 1 top)
	// for the given stack order. One O(n) pass to count per (season × kind), then
	// one to bake each member's cumulative-share slot. Cached by (order, version).
	function ensureRiversData(order: readonly DismissalKind[]): void {
		const key = `${order.join(',')}@${dismissalVersion}`;
		if (riversKey === key) return;
		riversKey = key;
		riversOrder = order;

		// stack index (0 = bottom) by dismissal code
		const stackIdx = [0, 0, 0, 0];
		order.forEach((name, j) => (stackIdx[DISMISSAL_CODE[name]] = j));

		const dis = dismissalAttr.array as Int8Array;
		const counts = new Float64Array(groupCount * 4); // per (gi, code)
		const pooled = [0, 0, 0, 0];
		for (let i = 0; i < n; i++) {
			const k = dis[i];
			if (k < 0) continue;
			counts[data.groupIds[i] * 4 + k]++;
			pooled[k]++;
		}

		const share = new Float64Array(groupCount * 4);
		const cumBelow = new Float64Array(groupCount * 4);
		for (let g = 0; g < groupCount; g++) {
			let total = 0;
			for (let k = 0; k < 4; k++) total += counts[g * 4 + k];
			if (total <= 0) continue;
			for (let k = 0; k < 4; k++) share[g * 4 + k] = counts[g * 4 + k] / total;
			for (let k = 0; k < 4; k++) {
				let below = 0;
				for (let k2 = 0; k2 < 4; k2++)
					if (stackIdx[k2] < stackIdx[k]) below += share[g * 4 + k2];
				cumBelow[g * 4 + k] = below;
			}
		}

		const pos = riverPosAttr.array as Float32Array;
		pos.fill(0);
		const running = new Float64Array(groupCount * 4);
		for (let i = 0; i < n; i++) {
			const k = dis[i];
			if (k < 0) continue;
			const base = data.groupIds[i] * 4 + k;
			const cnt = counts[base];
			const ord = running[base]++;
			pos[i] = cumBelow[base] + ((ord + 0.5) / cnt) * share[base];
		}
		riverPosAttr.needsUpdate = true;
		riversPooled = pooled;
	}

	function getRiversLayout(): RiversLayoutInfo | null {
		if (!riversLayout) return null;
		const totals = riversPooled;
		const grand = totals[0] + totals[1] + totals[2] + totals[3];
		const bands: RiversBand[] = [];
		let cum = 0;
		for (const kind of riversOrder) {
			const code = DISMISSAL_CODE[kind];
			const s = grand > 0 ? totals[code] / grand : 1 / Math.max(1, riversOrder.length);
			const lo = cum;
			const hi = cum + s;
			bands.push({
				kind,
				loFrac: lo,
				hiFrac: hi,
				centerY: riversLayout.bottom + ((lo + hi) / 2) * riversLayout.height
			});
			cum = hi;
		}
		return { ...riversLayout, bands };
	}

	/* ---- subset re-sort state (§7 — the C1-5 fireworks) --------------------- */
	// per-point ordinals are derived on-device the first time a given
	// (class, skipWpl) re-sort is applied, then cached — no wire cost, no
	// recompute on scrub. Column geometry rebuilds on resize.
	const resortCache = new Map<
		string,
		{ ord: Float32Array; counts: number[]; invMax: number }
	>();
	let resortKey = ''; // the (class,skipWpl) pair currently uploaded to aSubOrd
	let resortColumnsMode: 'ipl' | 'all' | null = null;
	let resortInfo: ResortColumnInfo | null = null;
	let halfWCache = 1;
	let halfHCache = 1;

	function ensureResortData(classCode: number, skipWpl: boolean, columns: 'ipl' | 'all'): void {
		const key = `${classCode}:${skipWpl ? 1 : 0}`;
		let entry = resortCache.get(key);
		if (!entry) {
			const ord = new Float32Array(n);
			const counts = new Array<number>(groupCount).fill(0);
			for (let i = 0; i < n; i++) {
				const at = data.attrs[i];
				const match = classCode === 6 ? (at & 8) !== 0 : (at & 7) === classCode;
				if (!match) continue;
				if (skipWpl && (at & 16) !== 0) continue;
				const g = data.groupIds[i];
				ord[i] = counts[g];
				counts[g]++;
			}
			let maxc = 1;
			for (let g = 0; g < groupCount; g++) if (counts[g] > maxc) maxc = counts[g];
			entry = { ord, counts, invMax: 1 / maxc };
			resortCache.set(key, entry);
		}
		if (resortKey !== key) {
			(subOrdAttr.array as Float32Array).set(entry.ord);
			subOrdAttr.needsUpdate = true;
			uniforms.uResortInvMax.value = entry.invMax;
			resortKey = key;
		}
		if (resortColumnsMode !== columns || !resortInfo) {
			resortColumnsMode = columns;
			rebuildResortColumns();
		}
	}

	function rebuildResortColumns(): void {
		if (resortColumnsMode === null) return;
		const rl = computeResortColumns(data.groups, halfWCache, halfHCache, resortColumnsMode);
		for (let gi = 0; gi < groupCount; gi++) {
			const x = rl.xs[gi];
			resortX[gi] = Number.isNaN(x) ? 0 : x;
		}
		uniforms.uResortX.value = resortX;
		const entry = resortCache.get(resortKey);
		resortInfo = {
			xs: rl.xs,
			counts: entry ? entry.counts.slice() : new Array<number>(groupCount).fill(0),
			bottom: rl.bottom,
			usableH: rl.usableH,
			invMax: entry ? entry.invMax : 1,
			gis: rl.gis
		};
	}

	const proj = new THREE.Vector3();
	function toCss(worldX: number, worldY: number): { x: number; y: number } {
		proj.set(worldX, worldY, 0).project(camera);
		return { x: (proj.x * 0.5 + 0.5) * cssW, y: (-proj.y * 0.5 + 0.5) * cssH };
	}

	function updateLabels(): void {
		for (const L of labels) {
			const p = toCss(L.worldX, L.worldY);
			L.el.style.transform = `translate3d(${p.x.toFixed(1)}px, ${p.y.toFixed(1)}px, 0)`;
		}
	}

	function anchorLabels(): void {
		if (!columnLayout) return;
		for (const L of labels) {
			if (L.kind === 'season') {
				L.worldX = columnLayout.xs[L.gi];
				L.worldY = columnLayout.bottom;
			} else {
				L.worldX = L.gi === -1 ? columnLayout.iplMidX : columnLayout.wplMidX;
				L.worldY = columnLayout.bottom;
			}
		}
	}

	/* ---- demand-mode rendering (invalidate pattern) ----------------------- */
	const stats: FieldStats = { frames: 0, fps: 0, nPoints: n, progress: 0 };
	const renderTimes: number[] = [];
	let rafId: number | null = null;
	let disposed = false;

	function invalidate(): void {
		if (rafId !== null || disposed) return;
		rafId = requestAnimationFrame(() => {
			rafId = null; // no re-queue: the loop provably stops when nothing moves
			renderFrame();
		});
	}

	function renderFrame(): void {
		if (disposed) return;
		renderer.render(scene, camera);
		updateLabels();
		stats.frames++;
		const now = performance.now();
		renderTimes.push(now);
		while (renderTimes.length > 0 && renderTimes[0] < now - 1000) renderTimes.shift();
		stats.fps = renderTimes.length;
		onRender?.(stats);
	}

	/* ---- state application -------------------------------------------------- */
	let applied: FieldRenderState = { ...DEFAULT_RENDER_STATE };
	const teamColorById = new Map<number, THREE.Color>(
		data.teams.map((t) => [t.id, new THREE.Color(t.color)])
	);

	// compare band stack orders by value (scenes may pass a fresh array each tick,
	// so reference equality would defeat the idle-noise no-op guard — demand mode).
	function sameKinds(a: readonly DismissalKind[], b: readonly DismissalKind[]): boolean {
		if (a === b) return true;
		if (a.length !== b.length) return false;
		for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
		return true;
	}

	// compare rail index/slot arrays by value for the same reason (the resolver
	// builds fresh arrays each tick; identical content must stay a no-op).
	function sameNums(a: readonly number[], b: readonly number[]): boolean {
		if (a === b) return true;
		if (a.length !== b.length) return false;
		for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
		return true;
	}

	function sameState(a: FieldRenderState, b: FieldRenderState): boolean {
		return (
			a.layoutA === b.layoutA &&
			a.layoutB === b.layoutB &&
			a.morph === b.morph &&
			a.reveal === b.reveal &&
			a.dim === b.dim &&
			a.wplDim === b.wplDim &&
			a.labels === b.labels &&
			a.highlightClass === b.highlightClass &&
			a.highlightLift === b.highlightLift &&
			a.highlightBoost === b.highlightBoost &&
			a.othersDim === b.othersDim &&
			a.highlightSkipWpl === b.highlightSkipWpl &&
			a.teamId === b.teamId &&
			a.wallHeatMix === b.wallHeatMix &&
			a.resortClass === b.resortClass &&
			a.resortSkipWpl === b.resortSkipWpl &&
			a.resortColumns === b.resortColumns &&
			a.resortEngage === b.resortEngage &&
			a.resortLift === b.resortLift &&
			a.resortTint === b.resortTint &&
			a.resortOthersDim === b.resortOthersDim &&
			a.filterTeam === b.filterTeam &&
			a.filterSeason === b.filterSeason &&
			a.filterMatchIndex === b.filterMatchIndex &&
			a.filterRangeLo === b.filterRangeLo &&
			a.filterRangeHi === b.filterRangeHi &&
			a.filterDim === b.filterDim &&
			a.cascadeClass === b.cascadeClass &&
			a.cascadeSweep === b.cascadeSweep &&
			a.cascadeTint === b.cascadeTint &&
			a.cascadeFall === b.cascadeFall &&
			a.cascadeFade === b.cascadeFade &&
			a.cascadeMute === b.cascadeMute &&
			a.riversClass === b.riversClass &&
			a.riversEngage === b.riversEngage &&
			a.riversTint === b.riversTint &&
			a.riversOthersDim === b.riversOthersDim &&
			a.riversMute === b.riversMute &&
			sameKinds(a.riversKinds, b.riversKinds) &&
			a.waterLevel === b.waterLevel &&
			a.waterDrownDim === b.waterDrownDim &&
			a.waterTeamKeep === b.waterTeamKeep &&
			a.highlightWpaMin === b.highlightWpaMin &&
			a.worthTableA === b.worthTableA &&
			a.worthTableB === b.worthTableB &&
			a.worthMix === b.worthMix &&
			sameNums(a.railIndices, b.railIndices) &&
			sameNums(a.railSlots, b.railSlots) &&
			a.railProgress === b.railProgress &&
			a.railDim === b.railDim &&
			a.railScale === b.railScale &&
			a.railLift === b.railLift &&
			a.phaseTableA === b.phaseTableA &&
			a.phaseTableB === b.phaseTableB &&
			a.phaseMix === b.phaseMix &&
			a.flowLift === b.flowLift &&
			a.sparkGlow === b.sparkGlow &&
			a.sparkLift === b.sparkLift &&
			a.sparkOthersDim === b.sparkOthersDim
		);
	}

	function applyState(s: FieldRenderState): void {
		if (disposed || sameState(applied, s)) return; // idle noise → no render
		applied = { ...s };

		uniforms.uLayoutA.value = LAYOUT_CODE[s.layoutA];
		uniforms.uLayoutB.value = LAYOUT_CODE[s.layoutB];
		uniforms.uProgress.value = s.morph;
		uniforms.uReveal.value = s.reveal;
		uniforms.uDim.value = s.dim;
		uniforms.uWplDim.value = s.wplDim;
		uniforms.uHlClass.value = s.highlightClass;
		uniforms.uHlLift.value = s.highlightLift;
		uniforms.uHlBoost.value = s.highlightBoost;
		uniforms.uOthersDim.value = s.othersDim;
		uniforms.uHlSkipWpl.value = s.highlightSkipWpl ? 1 : 0;

		// era-relative recolor blend (C1-2 thesis beat). Staged alone: the beat
		// runs before the fireworks, so heat and the re-sort/tint never overlap.
		uniforms.uWallHeatMix.value = s.wallHeatMix;
		if (import.meta.env.DEV && s.wallHeatMix > 0 && s.resortClass >= 0)
			console.warn(
				'[every-ball-ever] invariant: uWallHeatMix > 0 while a re-sort is engaged —',
				'the heat beat (C1-2) and the fireworks re-sort (C1-5) must be staged apart.'
			);

		// subset re-sort (§7): lazily derive the per-point ordinals + column
		// geometry the first time a given class engages; every scalar is set
		// each apply so engage/tint/lift lerp exactly like the highlight.
		uniforms.uResortEngage.value = s.resortEngage;
		uniforms.uResortLift.value = s.resortLift;
		uniforms.uResortTint.value = s.resortTint;
		uniforms.uResortOthersDim.value = s.resortOthersDim;
		uniforms.uResortSkipWpl.value = s.resortSkipWpl ? 1 : 0;
		if (s.resortClass >= 0) {
			ensureResortData(s.resortClass, s.resortSkipWpl, s.resortColumns);
			uniforms.uResortClass.value = s.resortClass;
		} else {
			uniforms.uResortClass.value = -1;
		}

		uniforms.uPickedTeam.value = s.teamId;
		const tc = teamColorById.get(s.teamId);
		if (tc) (uniforms.uTeamColor.value as THREE.Color).copy(tc);

		// facet filter (§12): the match facet is inert unless the buffer is loaded
		uniforms.uFilterTeam.value = s.filterTeam;
		uniforms.uFilterSeason.value = s.filterSeason;
		uniforms.uFilterRangeLo.value = s.filterRangeLo;
		uniforms.uFilterRangeHi.value = s.filterRangeHi;
		uniforms.uFilterMatch.value = hasMatchAttr ? s.filterMatchIndex : -1;
		uniforms.uFilterDim.value = s.filterDim;

		// run-out cascade (§14): season-swept flash+fall of the aRunOut subset.
		// A cross-cutting position modifier like the re-sort — the two must be
		// staged apart (both move points), so warn if they engage together.
		uniforms.uCascadeClass.value = s.cascadeClass;
		uniforms.uCascadeSweep.value = s.cascadeSweep;
		uniforms.uCascadeTint.value = s.cascadeTint;
		uniforms.uCascadeFall.value = s.cascadeFall;
		uniforms.uCascadeFade.value = s.cascadeFade;
		uniforms.uCascadeMute.value = s.cascadeMute;
		if (import.meta.env.DEV && s.cascadeClass >= 0 && s.resortClass >= 0)
			console.warn(
				'[every-ball-ever] invariant: the run-out cascade (C2-4) and a re-sort are',
				'both engaged — cross-cutting position modifiers must be staged apart.'
			);

		// dismissal rivers (§16): the wicket subset streams into the flat-baseline
		// 100%-stacked band. A cross-cutting position modifier like the re-sort and
		// cascade — the per-point stacked y is derived on-device the first time a
		// given stack order engages (cached), and every scalar is set each apply so
		// engage/tint/othersDim lerp exactly like the re-sort. Warn if it engages
		// with another position modifier (all move points; stage them apart).
		uniforms.uRiversEngage.value = s.riversEngage;
		uniforms.uRiversTint.value = s.riversTint;
		uniforms.uRiversOthersDim.value = s.riversOthersDim;
		uniforms.uRiversMute.value = s.riversMute;
		if (s.riversClass >= 0) {
			ensureRiversData(s.riversKinds);
			uniforms.uRiversClass.value = s.riversClass;
			riversActive = true;
		} else {
			uniforms.uRiversClass.value = -1;
			riversActive = false;
		}
		if (import.meta.env.DEV && s.riversClass >= 0 && (s.resortClass >= 0 || s.cascadeClass >= 0))
			console.warn(
				'[every-ball-ever] invariant: the dismissal rivers (C3-4) and a re-sort/cascade',
				'are both engaged — cross-cutting position modifiers must be staged apart.'
			);

		// tide skyline (§18): bake the within-season packing the first time the tide
		// layout engages (cached by the first-innings version). The waterline is a
		// LUMINANCE-only level over the held skyline — no position change, no second
		// controlling morph — so it just sets its uniforms; inactive at level < 0, so
		// R1/R2 render byte-identically.
		if (s.layoutA === 'tide' || s.layoutB === 'tide') {
			ensureTideData();
			tideActive = true;
		} else {
			tideActive = false;
		}
		uniforms.uWaterLevel.value = s.waterLevel;
		uniforms.uWaterDrownDim.value = s.waterDrownDim;
		uniforms.uWaterTeamKeep.value = s.waterTeamKeep ? 1 : 0;

		// worth-grid pricelens (§19): table ids resolve to texture rows (a not-yet
		// -fed id renders the neutral ramp, dev-warned; setWorthTables re-resolves
		// when the tables arrive). The recolor is gated in-shader on the worth
		// layout's share of the A/B mix, so these are no-ops for every prior scene.
		uniforms.uWorthRowA.value = worthRow(s.worthTableA);
		uniforms.uWorthRowB.value = worthRow(s.worthTableB);
		uniforms.uWorthMix.value = s.worthMix;

		// WPA subset-highlight threshold (§21) — only read while uHlClass == 7.
		uniforms.uHlWpaMin.value = s.highlightWpaMin;

		// over rail (§20): bake the tiny index set + slot anchors into the uniform
		// arrays; the overlay draw wakes only while at least one slot is active, so
		// every prior scene pays nothing (not even a vertex pass). A cross-cutting
		// POSITION modifier like the re-sort/cascade/rivers — stage them apart.
		const railN = Math.min(s.railIndices.length, RAIL_MAX_SLOTS);
		if (import.meta.env.DEV && s.railIndices.length > RAIL_MAX_SLOTS)
			console.warn(
				`[every-ball-ever] over rail: ${s.railIndices.length} indices exceed the`,
				`${RAIL_MAX_SLOTS}-slot capacity — extra balls stay in the field.`
			);
		for (let i = 0; i < RAIL_MAX_SLOTS; i++) {
			railIdxArr[i] = i < railN ? s.railIndices[i] : -9999;
			railSlotVecs[i].set(
				i < railN ? s.railSlots[i * 2] ?? 0.5 : 0.5,
				i < railN ? s.railSlots[i * 2 + 1] ?? 0.5 : 0.5
			);
		}
		uniforms.uRailN.value = railN;
		uniforms.uRailProgress.value = s.railProgress;
		uniforms.uRailDim.value = s.railDim;
		uniforms.uRailScale.value = s.railScale;
		uniforms.uRailLift.value = s.railLift;
		railPoints.visible = railN > 0;
		if (
			import.meta.env.DEV &&
			railN > 0 &&
			(s.resortClass >= 0 || s.cascadeClass >= 0 || s.riversClass >= 0)
		)
			console.warn(
				'[every-ball-ever] invariant: the over rail (C5-2/3) and a re-sort/cascade/rivers',
				'are both engaged — cross-cutting position modifiers must be staged apart.'
			);

		// constellation phase (§22): resolve the (A, B, mix) star-table lerp for
		// the held constellation. A null id resolves to 'all' (so a phase-less
		// constellation scene shows the all-innings map, and every non-constellation
		// scene keeps uStar on 'all' — harmless, since the shader only reads uStar
		// while the constellation layout is in the mix, so R1..R5 are byte-identical).
		// The copy runs only when the phase PAIR changes (applyStarArrays), so a
		// phase glide is a minimal per-frame touch. NEVER a live re-embed.
		applyStarArrays(s.phaseTableA ?? 'all', s.phaseTableB ?? 'all', s.phaseMix);

		// twin rivers (§23): the divergence-reveal lift over the held flow layout —
		// a scalar drive only (the per-gi river cells are baked into uFlow by
		// setRiverTable / resize). Read in-shader only while the flow layout is in the
		// mix, so this is a no-op for every prior scene. impact-sub sparks: the
		// luminance-lift glow over the aSpark subset — inert at sparkGlow 0.
		uniforms.uFlowLift.value = s.flowLift;
		uniforms.uSparkGlow.value = s.sparkGlow;
		uniforms.uSparkLift.value = s.sparkLift;
		uniforms.uSparkOthersDim.value = s.sparkOthersDim;

		// label plane opacity is scene-state-driven, never animated on its own
		const o = Math.min(1, Math.max(0, s.labels));
		labelLayer.style.opacity = o.toFixed(3);
		labelLayer.style.visibility = o <= 0 ? 'hidden' : 'visible';

		stats.progress = s.morph;
		invalidate();
	}

	/* ---- GPU picking (§11) -------------------------------------------------- */
	const pickCenter = (PICK_PATCH - 1) / 2;

	function pickAt(cssX: number, cssY: number, radiusPx?: number): number | null {
		if (disposed) return null;
		const dpr = renderer.getPixelRatio();
		const fullW = Math.max(1, Math.round(cssW * dpr));
		const fullH = Math.max(1, Math.round(cssH * dpr));
		const devX = cssX * dpr;
		const devY = cssY * dpr;

		// Render only the PICK_PATCH×PICK_PATCH device-px window under the tap into
		// the offscreen target (1:1), then read it back — ONE render, ONE readback,
		// no loop. The visible canvas is untouched (we never target the default
		// framebuffer), so demand-mode idle GPU stays ~0.
		const prevTarget = renderer.getRenderTarget();
		camera.setViewOffset(fullW, fullH, devX - pickCenter, devY - pickCenter, PICK_PATCH, PICK_PATCH);
		camera.updateProjectionMatrix();
		renderer.setRenderTarget(pickTarget);
		renderer.setClearColor(0x000000, 1); // background 0 → decodes to "no point"
		renderer.render(pickScene, camera);
		renderer.readRenderTargetPixels(pickTarget, 0, 0, PICK_PATCH, PICK_PATCH, pickPixels);
		// restore renderer + camera exactly (no side effects on the next visible frame)
		renderer.setRenderTarget(prevTarget);
		renderer.setClearColor(0x0b0e14, 1);
		camera.clearViewOffset();
		camera.updateProjectionMatrix();

		// nearest painted pixel to the patch centre = the pick radius (readback is
		// bottom-up, but the centre is the fixed point of that flip, so distances
		// to centre are unchanged).
		const maxR = radiusPx != null ? radiusPx * dpr : Infinity;
		const maxR2 = maxR * maxR;
		let best = -1;
		let bestD2 = Infinity;
		for (let py = 0; py < PICK_PATCH; py++) {
			for (let px = 0; px < PICK_PATCH; px++) {
				const o = (py * PICK_PATCH + px) * 4;
				const id1 = pickPixels[o] + pickPixels[o + 1] * 256 + pickPixels[o + 2] * 65536;
				if (id1 === 0) continue; // background
				const dx = px - pickCenter;
				const dy = py - pickCenter;
				const d2 = dx * dx + dy * dy;
				if (d2 < bestD2 && d2 <= maxR2) {
					bestD2 = d2;
					best = id1 - 1;
				}
			}
		}
		return best >= 0 ? best : null;
	}

	/* ---- facet filter (§12) + keyboard select ------------------------------ */
	// `mode` memory for the "no facet active" case (filterDim carries no mode then).
	let filterMode: FieldFilter['mode'] = NO_FILTER.mode;

	function filterToRenderState(f: FieldFilter): Pick<
		FieldRenderState,
		'filterTeam' | 'filterSeason' | 'filterMatchIndex' | 'filterRangeLo' | 'filterRangeHi' | 'filterDim'
	> {
		const anyFacet =
			f.team != null || f.season != null || f.matchIndex != null || f.matchRange != null;
		return {
			filterTeam: f.team ?? -1,
			filterSeason: f.season ?? -1,
			filterMatchIndex: f.matchIndex ?? -1,
			filterRangeLo: f.matchRange ? f.matchRange[0] : 0,
			filterRangeHi: f.matchRange ? f.matchRange[1] : 0,
			// filterDim is a no-op whenever no facet is active (nothing is filtered out)
			filterDim: anyFacet ? FILTER_DIM[f.mode] : 1
		};
	}

	function getFilter(): Readonly<FieldFilter> {
		const rangeActive = applied.filterRangeHi > applied.filterRangeLo;
		const matchActive = hasMatchAttr && applied.filterMatchIndex >= 0;
		const anyFacet =
			applied.filterTeam >= 0 || applied.filterSeason >= 0 || matchActive || rangeActive;
		return {
			team: applied.filterTeam >= 0 ? applied.filterTeam : null,
			season: applied.filterSeason >= 0 ? applied.filterSeason : null,
			matchIndex: matchActive ? applied.filterMatchIndex : null,
			matchRange: rangeActive ? [applied.filterRangeLo, applied.filterRangeHi] : null,
			mode: !anyFacet ? filterMode : applied.filterDim === 0 ? 'hide' : 'dim'
		};
	}

	function setFilter(partial: Partial<FieldFilter>): void {
		const merged: FieldFilter = { ...getFilter(), ...partial };
		filterMode = merged.mode; // remember the mode across "clear all facets"
		applyState({ ...applied, ...filterToRenderState(merged) });
	}

	// CPU mirror of the shader's `passesFilter`, read from the LIVE applied
	// uniforms so it is correct no matter which path (setFilter or a scene's
	// declarative fieldState) set the filter.
	function pointVisible(i: number): boolean {
		if (applied.filterTeam >= 0 && data.team[i] !== applied.filterTeam) return false;
		if (applied.filterSeason >= 0 && groupSeason[data.groupIds[i]] !== applied.filterSeason)
			return false;
		if (
			applied.filterRangeHi > applied.filterRangeLo &&
			(i < applied.filterRangeLo || i >= applied.filterRangeHi)
		)
			return false;
		if (hasMatchAttr && applied.filterMatchIndex >= 0 && data.matchIndex![i] !== applied.filterMatchIndex)
			return false;
		return true;
	}

	function firstVisiblePoint(): number | null {
		for (let i = 0; i < n; i++) if (pointVisible(i)) return i;
		return null;
	}

	function stepVisiblePoint(fromIndex: number, dir: 1 | -1): number | null {
		for (let i = fromIndex + dir; i >= 0 && i < n; i += dir) if (pointVisible(i)) return i;
		return null;
	}

	/* ---- resize / DPR ------------------------------------------------------ */
	function handleResize(): void {
		const w = container.clientWidth || 1;
		const h = container.clientHeight || 1;
		cssW = w;
		cssH = h;
		const dpr = Math.min(window.devicePixelRatio || 1, 2); // mobile DPR cap
		renderer.setPixelRatio(dpr);
		renderer.setSize(w, h, false);

		const halfH = 1;
		const halfW = w / h;
		halfWCache = halfW;
		halfHCache = halfH;
		camera.left = -halfW;
		camera.right = halfW;
		camera.top = halfH;
		camera.bottom = -halfH;
		camera.updateProjectionMatrix();

		columnLayout = computeColumns(data.groups, halfW, halfH);
		wallLayout = computeWall(data.groups, halfW, halfH);
		wormLayout = computeWorms(halfW, halfH);
		frontierLayout = computeFrontier(halfW, halfH);
		riversLayout = computeRivers(data.groups, halfW, halfH);
		tideLayout = computeTide(data.groups, halfW, halfH);
		worthLayout = computeWorth(halfW, halfH);
		constellationLayout = computeConstellation(halfW, halfH);
		flowLayout = computeFlow(data.groups, halfW, halfH);
		uniforms.uHalfW.value = halfW;
		uniforms.uHalfH.value = halfH;
		uniforms.uWormLeft.value = wormLayout.left;
		uniforms.uWormWidth.value = wormLayout.width;
		uniforms.uWormBottom.value = wormLayout.bottom;
		uniforms.uWormHeight.value = wormLayout.height;
		uniforms.uWormCellHalfW.value = wormLayout.cellHalfW;
		uniforms.uWormCellHalfH.value = wormLayout.cellHalfH;
		// frontier plane (§15): the fixed-aspect letterboxed box
		uniforms.uFrontierLeft.value = frontierLayout.left;
		uniforms.uFrontierWidth.value = frontierLayout.width;
		uniforms.uFrontierBottom.value = frontierLayout.bottom;
		uniforms.uFrontierHeight.value = frontierLayout.height;
		uniforms.uFrontierCellHalfW.value = frontierLayout.cellHalfW;
		uniforms.uFrontierCellHalfH.value = frontierLayout.cellHalfH;
		// dismissal rivers (§16): the flat-baseline band box + per-season strip x's
		uniforms.uRiverBottom.value = riversLayout.bottom;
		uniforms.uRiverHeight.value = riversLayout.height;
		uniforms.uRiverHalfW.value = riversLayout.stripHalfW;
		for (let gi = 0; gi < groupCount; gi++) {
			const rx = riversLayout.xs[gi];
			riverX[gi] = Number.isNaN(rx) ? 0 : rx;
		}
		uniforms.uRiverX.value = riverX;
		// tide skyline (§18): the fixed-aspect letterboxed box + season-block x's
		applyTideGeometry();
		// worth grid (§19): the fixed-aspect letterboxed 20×10 box
		uniforms.uWorthLeft.value = worthLayout.left;
		uniforms.uWorthWidth.value = worthLayout.width;
		uniforms.uWorthBottom.value = worthLayout.bottom;
		uniforms.uWorthHeight.value = worthLayout.height;
		// constellation (§22): the fixed-aspect (square) letterboxed star box. The
		// star tables are resolution-independent normalized coords, so only the box
		// world-scale (halfExtent) + the jitter-disc radius change on resize.
		uniforms.uConstHalfExtent.value = constellationLayout.halfExtent;
		uniforms.uConstStarR.value = constellationLayout.starRadius;
		// twin rivers (§23): the letterboxed box changed, so re-bake the per-gi river
		// cells (season x, centreline heights, band) if a table has been fed.
		applyFlowGeometry();
		uniforms.uPointScale.value = basePointPx(w, h, n) * dpr;
		uniforms.uColHalfWidth.value = columnLayout.colHalfWidth;
		uniforms.uColBottom.value = columnLayout.bottom;
		uniforms.uColUsableH.value = columnLayout.usableH;
		uniforms.uInvMaxCount.value = columnLayout.invMaxCount;
		uniforms.uWallLeft.value = wallLayout.left;
		uniforms.uWallWidth.value = wallLayout.width;
		uniforms.uWallCellHalfW.value = wallLayout.cellHalfW;
		uniforms.uWallRowHalfH.value = wallLayout.rowHalfH;
		for (let gi = 0; gi < groupCount; gi++)
			colVectors[gi].set(columnLayout.xs[gi], wallLayout.rowYs[gi]);

		// re-sort column x's follow the width; rebuild if a re-sort is live
		if (resortColumnsMode !== null) rebuildResortColumns();

		// label density: rotate to vertical when column pitch gets tight (mobile)
		const slotPx = (columnLayout.slotW / (2 * halfW)) * w;
		labelLayer.classList.toggle('vertical', slotPx < 52);

		anchorLabels();
		invalidate();
	}

	const resizeObserver = new ResizeObserver(handleResize);
	resizeObserver.observe(container);
	window.addEventListener('resize', handleResize); // also fires on DPR/zoom change

	// dedicated DPR-change watcher (e.g. dragging between monitors)
	let dprQuery: MediaQueryList | null = null;
	const onDprChange = (): void => {
		handleResize();
		watchDpr();
	};
	function watchDpr(): void {
		dprQuery?.removeEventListener('change', onDprChange);
		dprQuery = window.matchMedia(`(resolution: ${window.devicePixelRatio}dppx)`);
		dprQuery.addEventListener('change', onDprChange, { once: true });
	}
	watchDpr();

	// Pre-compile every program in the visible scene — including the (invisible
	// until Ch 5) rail overlay — so engaging the rail never hitches the set-piece
	// scrub's first frame with a mid-scroll shader compile, and any GLSL error
	// surfaces at load, not mid-chapter. No draw happens here (demand mode holds).
	renderer.compile(scene, camera);

	handleResize(); // initial size + first render

	const handle: FieldHandle = {
		applyState,
		invalidate,
		pickAt,
		firstVisiblePoint,
		stepVisiblePoint,
		setFilter,
		getFilter,
		hasMatchAttr,
		stats,
		data,
		projectToCss: toCss,
		getColumnLayout: () => columnLayout,
		getWallLayout: () => wallLayout,
		getResortLayout: () => resortInfo,
		getWormLayout: () => wormLayout,
		getFrontierLayout: () => frontierLayout,
		getRiversLayout,
		getTideLayout: () => tideLayout,
		getWorthLayout: () => worthLayout,
		getConstellationLayout,
		setStarTables,
		setRiverTable,
		getFlowLayout,
		setWorthTables,
		hasStateAttr,
		hasWpaAttr,
		setFirstInnings,
		setRunouts,
		setDismissals,
		setSparks,
		dispose(): void {
			disposed = true;
			if (rafId !== null) cancelAnimationFrame(rafId);
			resizeObserver.disconnect();
			window.removeEventListener('resize', handleResize);
			dprQuery?.removeEventListener('change', onDprChange);
			geometry.dispose();
			material.dispose();
			railMaterial.dispose();
			pickMaterial.dispose();
			pickTarget.dispose();
			worthTex.dispose();
			renderer.dispose();
			for (const L of labels) L.el.remove();
		}
	};

	// Dev-only debug hook (statically dead in production, like the synthetic
	// fallback and ?hud=1): exposes the live handle so field capabilities can be
	// exercised from the console / automation without authoring a scene.
	if (import.meta.env.DEV) {
		(window as unknown as Record<string, unknown>).__ebeField = handle;
	}

	return handle;
}

/* ---- label construction ---------------------------------------------------- */

function buildLabels(layer: HTMLElement, groups: GroupMeta[]): LabelEntry[] {
	const entries: LabelEntry[] = [];
	layer.style.opacity = '0';
	layer.style.visibility = 'hidden';

	for (const g of groups) {
		const anchor = document.createElement('div');
		anchor.className = 'col-anchor';
		const label = document.createElement('div');
		label.className = `col-label ${g.league}`;
		const season = document.createElement('span');
		season.className = 'season';
		season.textContent = String(g.season);
		const count = document.createElement('span');
		count.className = 'count';
		count.textContent = compact(g.count);
		label.append(season, count);
		anchor.appendChild(label);
		layer.appendChild(anchor);
		entries.push({ el: anchor, gi: g.gi, kind: 'season', worldX: 0, worldY: 0 });
	}

	for (const [league, giFlag] of [
		['ipl', -1],
		['wpl', -2]
	] as const) {
		if (!groups.some((g) => g.league === league)) continue;
		const anchor = document.createElement('div');
		anchor.className = 'col-anchor';
		const heading = document.createElement('div');
		heading.className = `league-heading ${league}`;
		heading.textContent = league.toUpperCase();
		anchor.appendChild(heading);
		layer.appendChild(anchor);
		entries.push({ el: anchor, gi: giFlag, kind: 'league', worldX: 0, worldY: 0 });
	}

	return entries;
}

function compact(count: number): string {
	return count >= 1000 ? `${(count / 1000).toFixed(1)}k` : String(count);
}
