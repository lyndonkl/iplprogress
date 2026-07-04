import { HL_CLASS, type FieldRenderState, type ResortColumns } from '$lib/field/types';
import { ASSEMBLY_RAIN_WINDOW } from '$lib/field/shaders';
import type { SceneDef, SceneFieldState, SubsetHighlight, SubsetResort } from './types';

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
	teamIgnite: boolean;
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
		teamIgnite: s.teamIgnite ?? true
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
		resortClass: rsClass,
		resortSkipWpl: rs?.skipWpl ?? false,
		resortColumns: rs ? resortColumns(rs) : 'ipl',
		// engage/tint/othersDim/lift lerp — a side with no re-sort reads as
		// engage 0, tint 0, othersDim 1 (fully settled, no dimming)
		resortEngage: lerp(fromRs?.engage ?? 0, toRs?.engage ?? 0, clampedT),
		resortLift: lerp(fromRs?.lift ?? 0.5, toRs?.lift ?? 0.5, clampedT),
		resortTint: lerp(fromRs?.tint ?? 0, toRs?.tint ?? 0, clampedT),
		resortOthersDim: lerp(fromRs?.othersDim ?? 1, toRs?.othersDim ?? 1, clampedT)
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
