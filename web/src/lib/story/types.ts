import type { Component } from 'svelte';
import type { FieldHandle } from '$lib/field/field';
import type {
	CascadeClass,
	DismissalKind,
	FilterMode,
	HighlightClass,
	LayoutId,
	ResortColumns,
	RiversClass
} from '$lib/field/types';
import type { FootnoteId } from './footnotes';

/**
 * The scene system: the story is an ordered list of SceneDefs composed into
 * one scroll timeline over ONE persistent field renderer (it never unmounts).
 * See CONTRACT.md in this directory for the full contract and ownership map.
 */

export type ChapterId = 'coldopen' | 'picker' | 'ch1' | 'ch2' | 'ch3' | 'endcard' | 'bowl';

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
	/** which points re-sort: an outcome class ('six', …) or 'wicket' */
	class: HighlightClass;
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
