import {
	CASCADE_CLASS,
	FILTER_DIM,
	HL_CLASS,
	type FieldRenderState,
	type ResortColumns
} from '$lib/field/types';
import { ASSEMBLY_RAIN_WINDOW } from '$lib/field/shaders';
import type {
	RunoutCascade,
	SceneDef,
	SceneFieldState,
	SubsetHighlight,
	SubsetResort
} from './types';

/** The six filter uniform fields resolved from a scene's declarative facets. */
interface ResolvedFilter {
	active: boolean;
	filterTeam: number;
	filterSeason: number;
	filterMatchIndex: number;
	filterRangeLo: number;
	filterRangeHi: number;
	filterDim: number;
}

function resolveSceneFilter(s: SceneFieldState): ResolvedFilter {
	const team = s.filterTeam ?? null;
	const season = s.filterSeason ?? null;
	const matchIndex = s.filterMatchIndex ?? null;
	const range = s.filterMatchRange ?? null;
	const active = team != null || season != null || matchIndex != null || range != null;
	const mode = s.filterMode ?? 'dim';
	return {
		active,
		filterTeam: team ?? -1,
		filterSeason: season ?? -1,
		filterMatchIndex: matchIndex ?? -1,
		filterRangeLo: range ? range[0] : 0,
		filterRangeHi: range ? range[1] : 0,
		// filterDim is a no-op when no facet is active (nothing is filtered out)
		filterDim: active ? FILTER_DIM[mode] : 1
	};
}

/**
 * Pure scene-state math for the scroll orchestrator: resolves a (from, to, t)
 * triple into one FieldRenderState for FieldHandle.applyState(). Layouts ride
 * uLayoutA/uLayoutB + morph; every scalar lerps; highlight class is discrete
 * (whichever side declares one) while its lift/boost/othersDim lerp, so
 * subsets glide in and out.
 */

interface ResolvedSceneState {
	layout: SceneFieldState['layout'];
	reveal: number;
	dim: number;
	wplDim: number;
	labels: number;
	highlight: SubsetHighlight | null;
	resort: SubsetResort | null;
	cascade: RunoutCascade | null;
	teamIgnite: boolean;
	wallHeatMix: number;
}

export function withDefaults(s: SceneFieldState): ResolvedSceneState {
	return {
		layout: s.layout,
		reveal: s.reveal ?? 1,
		dim: s.dim ?? 1,
		wplDim: s.wplDim ?? 1,
		labels: s.labels ?? 0,
		highlight: s.highlight ?? null,
		resort: s.resort ?? null,
		cascade: s.cascade ?? null,
		teamIgnite: s.teamIgnite ?? true,
		wallHeatMix: s.wallHeatMix ?? 0
	};
}

/** Default column grouping for a re-sort: IPL-only when WPL is skipped. */
function resortColumns(r: SubsetResort): ResortColumns {
	return r.columns ?? (r.skipWpl ? 'ipl' : 'all');
}

const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

export function resolveRenderState(
	from: SceneFieldState,
	to: SceneFieldState,
	t: number,
	teamId: number
): FieldRenderState {
	const f = withDefaults(from);
	const g = withDefaults(to);
	const clampedT = Math.min(1, Math.max(0, t));

	const fromHl = f.highlight;
	const toHl = g.highlight;
	const hlClass = toHl
		? HL_CLASS[toHl.class]
		: fromHl
			? HL_CLASS[fromHl.class]
			: HL_CLASS.none;

	// Re-sort resolves like the highlight: whichever side declares it fixes the
	// discrete fields (class / skipWpl / column grouping) while engage / lift /
	// tint / othersDim lerp — so the subset glides into and out of its columns.
	const fromRs = f.resort;
	const toRs = g.resort;
	const rs = toRs ?? fromRs;
	const rsClass = rs ? HL_CLASS[rs.class] : HL_CLASS.none;

	// Run-out cascade resolves like the highlight/re-sort: the active descriptor
	// (preferring `to`) fixes the discrete class + the beat's config constants
	// (tint / fall / fade / mute), while only `sweep` LERPS — so the cascade
	// engages as the scene declaring it advances the sweep, and settles back
	// (sweep → 0) when the next scene declares none. An inactive side contributes
	// sweep 0, so the run-outs return cleanly on the reverse leg.
	const fromCas = f.cascade;
	const toCas = g.cascade;
	const cas = toCas ?? fromCas;
	const casClass = cas ? CASCADE_CLASS[cas.class] : CASCADE_CLASS.none;

	// Facet filter resolves like the highlight: the discrete facets come from
	// whichever side declares an active filter (preferring `to`), while filterDim
	// lerps — an inactive side contributes dim 1, so a filter fades in/out cleanly.
	const fFilter = resolveSceneFilter(from);
	const gFilter = resolveSceneFilter(to);
	const facets = gFilter.active ? gFilter : fFilter.active ? fFilter : gFilter;

	return {
		layoutA: f.layout,
		layoutB: g.layout,
		morph: clampedT,
		reveal: lerp(f.reveal, g.reveal, clampedT),
		dim: lerp(f.dim, g.dim, clampedT),
		wplDim: lerp(f.wplDim, g.wplDim, clampedT),
		labels: lerp(f.labels, g.labels, clampedT),
		highlightClass: hlClass,
		highlightLift: lerp(fromHl?.lift ?? 0, toHl?.lift ?? 0, clampedT),
		highlightBoost: lerp(fromHl?.boost ?? 0, toHl?.boost ?? 0, clampedT),
		othersDim: lerp(fromHl?.othersDim ?? 1, toHl?.othersDim ?? 1, clampedT),
		// discrete like the class: whichever side declares the highlight decides
		highlightSkipWpl: (toHl ?? fromHl)?.skipWpl ?? false,
		// the team stays lit through morphs; a scene may opt out explicitly
		teamId: (clampedT < 0.5 ? f.teamIgnite : g.teamIgnite) ? teamId : -1,
		// era-relative recolor blend lerps like any scalar (0 both sides = no-op),
		// so the C1-2 heat beat ramps in and settles back out with the scroll
		wallHeatMix: lerp(f.wallHeatMix, g.wallHeatMix, clampedT),
		resortClass: rsClass,
		resortSkipWpl: rs?.skipWpl ?? false,
		resortColumns: rs ? resortColumns(rs) : 'ipl',
		// engage/tint/othersDim/lift lerp — a side with no re-sort reads as
		// engage 0, tint 0, othersDim 1 (fully settled, no dimming)
		resortEngage: lerp(fromRs?.engage ?? 0, toRs?.engage ?? 0, clampedT),
		resortLift: lerp(fromRs?.lift ?? 0.5, toRs?.lift ?? 0.5, clampedT),
		resortTint: lerp(fromRs?.tint ?? 0, toRs?.tint ?? 0, clampedT),
		resortOthersDim: lerp(fromRs?.othersDim ?? 1, toRs?.othersDim ?? 1, clampedT),
		// facets discrete (from the active side); the dim fades so filters glide
		filterTeam: facets.filterTeam,
		filterSeason: facets.filterSeason,
		filterMatchIndex: facets.filterMatchIndex,
		filterRangeLo: facets.filterRangeLo,
		filterRangeHi: facets.filterRangeHi,
		filterDim: lerp(fFilter.active ? fFilter.filterDim : 1, gFilter.active ? gFilter.filterDim : 1, clampedT),
		// cascade: sweep lerps (engage/settle-back); the beat constants come from
		// the active descriptor (discrete, like the highlight class). When NO
		// cascade is declared (cas null) every field takes its INERT default so a
		// non-cascade scene is byte-identical to DEFAULT_RENDER_STATE — in
		// particular cascadeMute MUST be 0 or it would desaturate a picked team's
		// ignite glow in R1 (the team-ignite mute branch keys off uCascadeMute).
		cascadeClass: casClass,
		cascadeSweep: lerp(fromCas?.sweep ?? 0, toCas?.sweep ?? 0, clampedT),
		cascadeTint: cas ? cas.tint ?? 1 : 0,
		cascadeFall: cas ? cas.fall ?? 0.9 : 0,
		cascadeFade: cas ? cas.fade ?? 0 : 1,
		cascadeMute: cas ? cas.muteIdentity ?? 1 : 0
	};
}

/**
 * A scene's fully-settled HELD state (post-morph): its fieldState resolved
 * through dynamicState at progress 1. This is the correct morph SOURCE for the
 * NEXT scene — a re-sort that engaged and tinted to completion must settle back
 * FROM that completed state, not from the un-modulated fieldState (no pop). The
 * orchestrator uses it for the `from` side; reduced motion ignores it (t = 1).
 */
export function heldState(scene: SceneDef): SceneFieldState {
	return scene.dynamicState ? scene.dynamicState(1, scene.fieldState) : scene.fieldState;
}

/**
 * A scene's live TARGET state at a given progress: its fieldState resolved
 * through dynamicState (so a caption step can drive a one-change field update
 * during the hold). The morph interpolates toward this on every tick.
 */
export function dynamicTarget(scene: SceneDef, progress: number): SceneFieldState {
	return scene.dynamicState ? scene.dynamicState(progress, scene.fieldState) : scene.fieldState;
}

/** The scene's end state for prefers-reduced-motion jump-cuts. */
export function sceneEndState(scene: SceneDef): SceneFieldState {
	return scene.reducedMotionEndState ?? scene.fieldState;
}

/** Fraction of the scene's scroll that drives the morph (rest holds). */
export function morphFraction(scene: SceneDef): number {
	const m = scene.morphLength ?? Math.min(140, scene.scrollLength);
	return Math.min(1, Math.max(0.0001, m / scene.scrollLength));
}

/**
 * How many points have appeared at a given assembly reveal value — the DOM
 * counter's source of truth. Mirrors the shader's frontier math exactly:
 * a point is visible once `chronoIndex/n < reveal * (1 + RAIN_W)`, so the
 * count is monotonic, 0 at reveal 0, and exactly n at reveal 1 — the counter
 * can only ever end at the number the pixels show.
 */
export function assemblyVisibleCount(reveal: number, nPoints: number): number {
	const r = Math.min(1, Math.max(0, reveal));
	return Math.min(nPoints, Math.floor(r * (1 + ASSEMBLY_RAIN_WINDOW) * nPoints));
}
