import type { Component } from 'svelte';
import type { FieldHandle } from '$lib/field/field';
import type { HighlightClass, LayoutId } from '$lib/field/types';
import type { FootnoteId } from './footnotes';

/**
 * The scene system: the story is an ordered list of SceneDefs composed into
 * one scroll timeline over ONE persistent field renderer (it never unmounts).
 * See CONTRACT.md in this directory for the full contract and ownership map.
 */

export type ChapterId = 'coldopen' | 'picker' | 'ch1' | 'endcard';

/** Uniform-driven subset highlight: lift/tint points matching a class mask. */
export interface SubsetHighlight {
	/** which points match: an outcome class ('six', 'four', …) or 'wicket' */
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
	/** whether the picked team's balls stay ignited (default true — §2 standing rule) */
	teamIgnite?: boolean;
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
	/** DOM/SVG annotation layer, rendered inside the scene's scroll section */
	annotations: Component<SceneAnnotationProps>;
	/** per-scene "how we computed this" sheet (typed registry key) */
	footnote?: FootnoteId;
}
