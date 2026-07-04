import { HL_CLASS, type FieldRenderState } from '$lib/field/types';
import { ASSEMBLY_RAIN_WINDOW } from '$lib/field/shaders';
import type { SceneDef, SceneFieldState, SubsetHighlight } from './types';

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
		teamIgnite: s.teamIgnite ?? true
	};
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
		teamId: (clampedT < 0.5 ? f.teamIgnite : g.teamIgnite) ? teamId : -1
	};
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
