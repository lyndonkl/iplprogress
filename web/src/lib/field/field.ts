import * as THREE from 'three';
import {
	DEFAULT_RENDER_STATE,
	LAYOUT_CODE,
	type FieldData,
	type FieldRenderState,
	type GroupMeta
} from './types';
import {
	computeColumns,
	computeWall,
	computeResortColumns,
	basePointPx,
	type ColumnLayout,
	type WallLayout
} from './layout';
import { makeVertexShader, fragmentShader } from './shaders';

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
		uWallHeatMix: { value: 0 }
	};

	const geometry = new THREE.BufferGeometry();
	geometry.setAttribute('position', new THREE.BufferAttribute(record, 3));
	geometry.setAttribute('aAttrs', new THREE.BufferAttribute(data.attrs, 1, false));
	geometry.setAttribute('aBallsFaced', new THREE.BufferAttribute(data.ballsFaced, 1, false));
	geometry.setAttribute('aTeam', new THREE.BufferAttribute(data.team, 1, false));
	// wallheat is uploaded NORMALIZED (u8 → 0..1) so the shader reads aWallHeat
	// directly against WALLHEAT_NEUTRAL (73/255); every other attr is raw bytes.
	geometry.setAttribute('aWallHeat', new THREE.BufferAttribute(data.wallHeat, 1, true));
	geometry.setAttribute('aSubOrd', new THREE.BufferAttribute(subOrd, 1, false));
	const subOrdAttr = geometry.getAttribute('aSubOrd') as THREE.BufferAttribute;
	// positions are procedural in-shader; give THREE an all-covering bound
	geometry.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 0, 0), 100);

	const material = new THREE.ShaderMaterial({
		glslVersion: THREE.GLSL3,
		vertexShader: makeVertexShader(groupCount),
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

	/* ---- DOM label plane -------------------------------------------------- */
	const labels: LabelEntry[] = buildLabels(labelLayer, data.groups);
	let columnLayout: ColumnLayout | null = null;
	let wallLayout: WallLayout | null = null;
	let cssW = 1;
	let cssH = 1;

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
			a.resortOthersDim === b.resortOthersDim
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

		// label plane opacity is scene-state-driven, never animated on its own
		const o = Math.min(1, Math.max(0, s.labels));
		labelLayer.style.opacity = o.toFixed(3);
		labelLayer.style.visibility = o <= 0 ? 'hidden' : 'visible';

		stats.progress = s.morph;
		invalidate();
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
		uniforms.uHalfW.value = halfW;
		uniforms.uHalfH.value = halfH;
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

	return {
		applyState,
		invalidate,
		stats,
		data,
		projectToCss: toCss,
		getColumnLayout: () => columnLayout,
		getWallLayout: () => wallLayout,
		getResortLayout: () => resortInfo,
		dispose(): void {
			disposed = true;
			if (rafId !== null) cancelAnimationFrame(rafId);
			resizeObserver.disconnect();
			window.removeEventListener('resize', handleResize);
			dprQuery?.removeEventListener('change', onDprChange);
			geometry.dispose();
			material.dispose();
			renderer.dispose();
			for (const L of labels) L.el.remove();
		}
	};
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
