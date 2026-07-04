/**
 * The field data contract (R0, extended for R1a). Files live under
 * static/data/, emitted by the Python pipeline. The web app never writes there.
 */

export interface GroupMeta {
	/** group index — array position in groups.json */
	gi: number;
	league: 'ipl' | 'wpl';
	season: number;
	count: number;
}

export interface TeamMeta {
	/** team id — matches the per-point byte in team.u8 */
	id: number;
	league: 'ipl' | 'wpl';
	/** canonical current franchise name (pipeline canonicalization tables) */
	name: string;
	short: string;
	/** hex color, e.g. "#FDB913" */
	color: string;
	active: boolean;
}

export interface MetaJson {
	n_points: number;
	built_at: string;
	point_order: string;
	/** meta v2 (storyboard CO-3 traceability) — optional until the pipeline emits them */
	n_players?: number;
	n_matches?: Record<string, number>;
	files?: Record<string, { bytes_raw: number; bytes_gz: number }>;
}

export interface FieldData {
	nPoints: number;
	meta: MetaJson;
	groups: GroupMeta[];
	teams: TeamMeta[];
	/** per-delivery group index (gi), length nPoints */
	groupIds: Uint16Array;
	/**
	 * per-delivery packed byte, length nPoints:
	 * bits 0-2 outcome class (0 dot · 1 single · 2 two-or-three · 3 four · 4 six ·
	 * 5 other-extras-scoring-ball), bit 3 wicket fell, bit 4 WPL.
	 */
	attrs: Uint8Array;
	/** per-delivery batter balls-faced-so-far index, capped at 255 (wides excluded) */
	ballsFaced: Uint8Array;
	/** per-delivery batting-team id (matches teams.json ids) */
	team: Uint8Array;
	/** true when this is the dev-only synthetic fallback, not pipeline output */
	synthetic: boolean;
}

/** Outcome-class bit meanings, for readability at call sites. */
export const OUTCOME_DOT = 0;
export const OUTCOME_SINGLE = 1;
export const OUTCOME_TWO_THREE = 2;
export const OUTCOME_FOUR = 3;
export const OUTCOME_SIX = 4;
export const OUTCOME_OTHER = 5;

/* ---------------------------------------------------------------------------
 * Field layouts + render state — the uniform-level contract the story shell
 * drives. All layouts are computed IN-SHADER from per-point attributes; no
 * position buffers ever cross the wire (blueprint §2).
 * ------------------------------------------------------------------------- */

export type LayoutId = 'free' | 'columns' | 'wall' | 'assembly';

/** Shader-side layout codes (uLayoutA / uLayoutB). */
export const LAYOUT_CODE: Record<LayoutId, number> = {
	free: 0,
	columns: 1,
	wall: 2,
	assembly: 3
};

/**
 * Subset-highlight class codes (uHlClass). 0-5 match the outcome classes in
 * attrs.u8; 6 selects the wicket bit; -1 = no highlight active.
 */
export const HL_CLASS = {
	none: -1,
	dot: OUTCOME_DOT,
	single: OUTCOME_SINGLE,
	twoThree: OUTCOME_TWO_THREE,
	four: OUTCOME_FOUR,
	six: OUTCOME_SIX,
	other: OUTCOME_OTHER,
	wicket: 6
} as const;

export type HighlightClass = Exclude<keyof typeof HL_CLASS, 'none'>;

/**
 * One fully-resolved GPU state for the persistent field. The story
 * orchestrator interpolates between scene fieldStates and calls
 * FieldHandle.applyState() with one of these — exactly one render per change
 * (demand-mode rendering, blueprint §2).
 */
export interface FieldRenderState {
	/** morph source layout */
	layoutA: LayoutId;
	/** morph target layout */
	layoutB: LayoutId;
	/** 0 = pure layoutA · 1 = pure layoutB */
	morph: number;
	/**
	 * assembly stream-in 0..1 (chronological by point index). Only meaningful
	 * while layoutA or layoutB is 'assembly'; keep at 1 otherwise.
	 */
	reveal: number;
	/** global luminance multiplier — 1 = full brightness (dim = the loop stops, too) */
	dim: number;
	/** extra luminance multiplier on WPL points — 1 = full (C1-2 shelf staging) */
	wplDim: number;
	/** season-column DOM label plane opacity 0..1 */
	labels: number;
	/** subset-highlight class code (HL_CLASS values; -1 = none) */
	highlightClass: number;
	/** world-units vertical lift for highlighted points */
	highlightLift: number;
	/** brightness boost for highlighted points (0..1) */
	highlightBoost: number;
	/** luminance multiplier for non-matching points while a highlight is active */
	othersDim: number;
	/** WPL points never match the highlight (they take the others path — C1-5) */
	highlightSkipWpl: boolean;
	/** picked-team id (teams.json) whose balls ignite in team color; -1 = none */
	teamId: number;
}

export const DEFAULT_RENDER_STATE: FieldRenderState = {
	layoutA: 'free',
	layoutB: 'free',
	morph: 0,
	reveal: 1,
	dim: 1,
	wplDim: 1,
	labels: 0,
	highlightClass: HL_CLASS.none,
	highlightLift: 0,
	highlightBoost: 0,
	othersDim: 1,
	highlightSkipWpl: false,
	teamId: -1
};
