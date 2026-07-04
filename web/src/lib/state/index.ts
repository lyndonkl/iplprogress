/**
 * Typed, SSR-safe, localStorage-backed reader state (storyboard §0.3 — the
 * schema names are contract: `ebe.sketch.v1`, `ebe.team.v1`, `ebe.progress.v1`).
 * Everything degrades gracefully: null means "no state yet", and no scene may
 * gate content on any of these existing (deep links must always work).
 */
import { persisted, isRecord, isFiniteNumber } from './persisted';

/* ---- ebe.sketch.v1 — the cold-open You-Draw-It ---------------------------- */

export const SKETCH_BRANCHES = ['gentle', 'right', 'early', 'over'] as const;
export type SketchBranch = (typeof SKETCH_BRANCHES)[number];

export interface SketchState {
	/** true when the reader took "Just show me" (no values drawn) */
	skipped: boolean;
	/** the reader's 200+ totals for 2013..2026 (14 values), null when skipped */
	values: number[] | null;
	/** which reveal branch fired (null when skipped) */
	branch: SketchBranch | null;
	ts: number;
}

function isSketch(v: unknown): v is SketchState | null {
	if (v === null) return true;
	if (!isRecord(v)) return false;
	if (typeof v.skipped !== 'boolean' || !isFiniteNumber(v.ts)) return false;
	if (v.values !== null && !(Array.isArray(v.values) && v.values.every(isFiniteNumber)))
		return false;
	if (v.branch !== null && !SKETCH_BRANCHES.includes(v.branch as SketchBranch)) return false;
	return true;
}

/** The reader's drawn 200+ curve (or their skip). Written by the cold-open scenes. */
export const sketch = persisted<SketchState | null>('ebe.sketch.v1', null, isSketch);

/* ---- ebe.team.v1 — the team pick ------------------------------------------ */

export interface TeamPick {
	/** null league means the neutral pick */
	league: 'ipl' | 'wpl' | null;
	/** canonical franchise name from teams.json, or "neutral" */
	team: string;
	ts: number;
}

function isTeamPick(v: unknown): v is TeamPick | null {
	if (v === null) return true;
	if (!isRecord(v)) return false;
	if (v.league !== null && v.league !== 'ipl' && v.league !== 'wpl') return false;
	return typeof v.team === 'string' && isFiniteNumber(v.ts);
}

/** The picked franchise — ignites its balls field-wide; payoff cards key off it. */
export const pickedTeam = persisted<TeamPick | null>('ebe.team.v1', null, isTeamPick);

/* ---- ebe.progress.v1 — chapter/scene progress ------------------------------ */

export interface ChapterProgress {
	/** the last scene anchor reached (powers the nav's "Continue?" affordance) */
	scene: string;
	ts: number;
}

function isProgress(v: unknown): v is ChapterProgress | null {
	if (v === null) return true;
	return isRecord(v) && typeof v.scene === 'string' && isFiniteNumber(v.ts);
}

export const chapterProgress = persisted<ChapterProgress | null>(
	'ebe.progress.v1',
	null,
	isProgress
);

/* ---- ebe.footnotes.v1 — the open footnote sheet ---------------------------- */

function isFootnoteKey(v: unknown): v is string | null {
	return v === null || typeof v === 'string';
}

/**
 * The currently-open footnote id (keys of the story footnote registry), or
 * null when the panel is closed. Persisted so a reload mid-read restores the
 * open sheet. The panel validates the key against the registry before render.
 */
export const footnotesOpen = persisted<string | null>('ebe.footnotes.v1', null, isFootnoteKey);
