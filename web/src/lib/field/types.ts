/**
 * The R0 data contract (see repo task brief). Files live under static/data/,
 * emitted by the Python pipeline. The web app never writes there.
 */

export interface GroupMeta {
	/** group index — array position in groups.json */
	gi: number;
	league: 'ipl' | 'wpl';
	season: number;
	count: number;
}

export interface MetaJson {
	n_points: number;
	built_at: string;
	point_order: string;
	files?: Record<string, { bytes_raw: number; bytes_gz: number }>;
}

export interface FieldData {
	nPoints: number;
	groups: GroupMeta[];
	/** per-delivery group index (gi), length nPoints */
	groupIds: Uint16Array;
	/**
	 * per-delivery packed byte, length nPoints:
	 * bits 0-2 outcome class (0 dot · 1 single · 2 two-or-three · 3 four · 4 six ·
	 * 5 other-extras-scoring-ball), bit 3 wicket fell, bit 4 WPL.
	 */
	attrs: Uint8Array;
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
