import * as THREE from 'three';
import {
	DEFAULT_RENDER_STATE,
	FILTER_DIM,
	LAYOUT_CODE,
	NO_FILTER,
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
	basePointPx,
	WORM_X_CAP,
	WORM_RUNS_CAP,
	type ColumnLayout,
	type WallLayout,
	type WormLayout
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
	 * Set run-out membership for the C2-4 cascade (§14). Pass the point indices
	 * whose delivery is a run-out (the scene derives them from the columnar
	 * `wicket_kind == 'run out'`); the field bakes them into the per-point
	 * `aRunOut` GL flag ONCE (no per-frame cost — demand mode preserved) and
	 * renders. Pass `null` to revert to the pipeline seed (attrs.u8 bit 6). This
	 * is the working-today path until the pipeline re-encodes the run-out bit.
	 */
	setRunouts(indices: Iterable<number> | null): void;
	readonly data: FieldData;
	readonly stats: Readonly<FieldStats>;
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
		uCascadeInvSpan: { value: 1 / seasonSpan }
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
	const runOutFlag = new Uint8Array(n);
	for (let i = 0; i < n; i++) if ((data.attrs[i] & 64) !== 0) runOutFlag[i] = 1;
	geometry.setAttribute('aRunOut', new THREE.BufferAttribute(runOutFlag, 1, false));
	const runOutAttr = geometry.getAttribute('aRunOut') as THREE.BufferAttribute;
	geometry.setAttribute('aSubOrd', new THREE.BufferAttribute(subOrd, 1, false));
	const subOrdAttr = geometry.getAttribute('aSubOrd') as THREE.BufferAttribute;
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
	let cssW = 1;
	let cssH = 1;

	/* ---- run-out cascade membership (§14) ---------------------------------- */
	// Bake a CPU-supplied index set (or the pipeline seed) into the aRunOut flag
	// ONCE; there is no per-frame cost, so demand mode is preserved.
	function setRunouts(indices: Iterable<number> | null): void {
		if (disposed) return;
		const arr = runOutAttr.array as Uint8Array;
		arr.fill(0);
		if (indices === null) {
			for (let i = 0; i < n; i++) if ((data.attrs[i] & 64) !== 0) arr[i] = 1; // pipeline seed
		} else {
			for (const i of indices) if (i >= 0 && i < n) arr[i] = 1;
		}
		runOutAttr.needsUpdate = true;
		invalidate();
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
			a.cascadeMute === b.cascadeMute
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
		uniforms.uHalfW.value = halfW;
		uniforms.uHalfH.value = halfH;
		uniforms.uWormLeft.value = wormLayout.left;
		uniforms.uWormWidth.value = wormLayout.width;
		uniforms.uWormBottom.value = wormLayout.bottom;
		uniforms.uWormHeight.value = wormLayout.height;
		uniforms.uWormCellHalfW.value = wormLayout.cellHalfW;
		uniforms.uWormCellHalfH.value = wormLayout.cellHalfH;
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
		setRunouts,
		dispose(): void {
			disposed = true;
			if (rafId !== null) cancelAnimationFrame(rafId);
			resizeObserver.disconnect();
			window.removeEventListener('resize', handleResize);
			dprQuery?.removeEventListener('change', onDprChange);
			geometry.dispose();
			material.dispose();
			pickMaterial.dispose();
			pickTarget.dispose();
			renderer.dispose();
			for (const L of labels) L.el.remove();
		}
	};

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
