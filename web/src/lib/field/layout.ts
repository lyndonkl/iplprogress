import type { GroupMeta } from './types';

/**
 * Season-columns layout geometry, derived client-side from groups.json
 * (blueprint §2: group-indexed layouts are centroid tables + per-point group
 * ids + in-shader jitter — zero position buffers on the wire).
 *
 * World space: the orthographic camera frustum is y ∈ [-1, 1],
 * x ∈ [-aspect, aspect]. Columns are laid across the width, IPL block first,
 * a deliberate gap, then the WPL block — two populations, not one queue.
 */
export interface ColumnLayout {
	/** world x of each group's column centre, indexed by gi */
	xs: number[];
	/** half-width of a column body, world units */
	colHalfWidth: number;
	/** world y of the column base */
	bottom: number;
	/** world height of the tallest possible column (count == maxCount) */
	usableH: number;
	/** 1 / max group count — ordinal * invMaxCount * usableH = stack height */
	invMaxCount: number;
	/** centre x of the IPL block and the WPL block (for league headings) */
	iplMidX: number;
	wplMidX: number;
	/** slot pitch in world units (label-density decisions) */
	slotW: number;
}

export function computeColumns(groups: GroupMeta[], halfW: number, halfH: number): ColumnLayout {
	const nIpl = groups.filter((g) => g.league === 'ipl').length;
	const nWpl = groups.length - nIpl;

	const leagueGapSlots = 1.6;
	const slots = nIpl + nWpl + (nWpl > 0 ? leagueGapSlots : 0);
	const sideMargin = 0.055 * (2 * halfW);
	const usableW = 2 * halfW - 2 * sideMargin;
	const slotW = usableW / slots;

	const xs: number[] = [];
	let cursor = -halfW + sideMargin + slotW / 2;
	let prevLeague: GroupMeta['league'] | null = null;
	let iplSum = 0;
	let wplSum = 0;
	for (const g of groups) {
		if (prevLeague !== null && g.league !== prevLeague) cursor += leagueGapSlots * slotW;
		xs.push(cursor);
		if (g.league === 'ipl') iplSum += cursor;
		else wplSum += cursor;
		cursor += slotW;
		prevLeague = g.league;
	}

	const maxCount = groups.reduce((m, g) => Math.max(m, g.count), 1);

	return {
		xs,
		colHalfWidth: slotW * 0.36,
		bottom: -0.68 * halfH,
		usableH: 1.38 * halfH,
		invMaxCount: 1 / maxCount,
		iplMidX: nIpl > 0 ? iplSum / nIpl : 0,
		wplMidX: nWpl > 0 ? wplSum / nWpl : 0,
		slotW
	};
}

/**
 * Ignition-wall layout geometry (Ch 1 controlling morph):
 * x = the batter's balls-faced index (1..30+, capped bucket at the right edge),
 * y = season row — IPL rows 2008 (bottom) → 2026 (top), then a deliberate gap,
 * then the WPL's four rows as a visibly separate shelf above (storyboard C1-2).
 * Positions are in-shader: this table only carries per-group row centres.
 */
export interface WallLayout {
	/** world y of each group's row centre, indexed by gi */
	rowYs: number[];
	/** half-height of a row body, world units */
	rowHalfH: number;
	/** world x of the wall's left edge (ball 1) */
	left: number;
	/** world width of the wall (ball 1 → 30+) */
	width: number;
	/** half-width of one balls-faced cell body, world units (jitter bound) */
	cellHalfW: number;
	/** world y of the WPL shelf centre (label anchoring); NaN when no WPL groups */
	shelfMidY: number;
}

/** number of balls-faced cells on the wall: 1..29 plus the capped `30+` bucket */
export const WALL_CELLS = 30;

export function computeWall(groups: GroupMeta[], halfW: number, halfH: number): WallLayout {
	const ipl = groups.filter((g) => g.league === 'ipl').sort((a, b) => a.season - b.season);
	const wpl = groups.filter((g) => g.league === 'wpl').sort((a, b) => a.season - b.season);

	const shelfGapRows = wpl.length > 0 ? 1.4 : 0;
	const totalRows = ipl.length + wpl.length + shelfGapRows;

	const yBottom = -0.74 * halfH;
	const yTop = 0.84 * halfH;
	const pitch = (yTop - yBottom) / Math.max(1, totalRows);

	const rowYs: number[] = new Array(groups.length).fill(0);
	ipl.forEach((g, i) => {
		rowYs[g.gi] = yBottom + (i + 0.5) * pitch;
	});
	let shelfSum = 0;
	wpl.forEach((g, j) => {
		const y = yBottom + (ipl.length + shelfGapRows + j + 0.5) * pitch;
		rowYs[g.gi] = y;
		shelfSum += y;
	});

	const left = -0.84 * halfW;
	const width = 1.68 * halfW;

	return {
		rowYs,
		rowHalfH: pitch * 0.38,
		left,
		width,
		cellHalfW: (width / WALL_CELLS) * 0.42,
		shelfMidY: wpl.length > 0 ? shelfSum / wpl.length : NaN
	};
}

/** DPR-aware base point size in CSS px — scaled so ~316k points fill the view. */
export function basePointPx(cssW: number, cssH: number, nPoints: number): number {
	const perPoint = (cssW * cssH) / Math.max(1, nPoints);
	return Math.min(3.2, Math.max(1.3, Math.sqrt(perPoint) * 1.15));
}

/**
 * Subset re-sort column geometry (Ch 1 fireworks, §7 capability): one column
 * per season group in the subset, laid evenly across the width so the columns
 * fill the stage (C1-5: "19 thin columns fit portrait width"). Only the
 * grouping (which gi's get a column) is geometry; the column HEIGHTS come from
 * the per-group subset counts computed on-device in field.ts. Positions never
 * cross the wire.
 */
export interface ResortLayout {
	/** world x of each subset group's column centre, indexed by gi (NaN = excluded) */
	xs: number[];
	/** half-width of a column body, world units (jitter bound) */
	colHalfWidth: number;
	/** world y of the column base (shared with the season-columns layout) */
	bottom: number;
	/** world height at the tallest column (subset max count) */
	usableH: number;
	/** the gi's that received a column, in season order */
	gis: number[];
}

export function computeResortColumns(
	groups: GroupMeta[],
	halfW: number,
	halfH: number,
	columns: 'ipl' | 'all'
): ResortLayout {
	const subset = groups
		.filter((g) => columns === 'all' || g.league === 'ipl')
		.sort((a, b) => a.season - b.season);

	const sideMargin = 0.06 * (2 * halfW);
	const usableW = 2 * halfW - 2 * sideMargin;
	const slotW = usableW / Math.max(1, subset.length);

	const xs: number[] = new Array(groups.length).fill(NaN);
	const gis: number[] = [];
	subset.forEach((g, i) => {
		xs[g.gi] = -halfW + sideMargin + (i + 0.5) * slotW;
		gis.push(g.gi);
	});

	return {
		xs,
		colHalfWidth: slotW * 0.34,
		bottom: -0.68 * halfH,
		usableH: 1.38 * halfH,
		gis
	};
}

/* ---------------------------------------------------------------------------
 * Worm-space layout (Ch 2 controlling morph, CONTRACT §13). Every ball settles
 * into a low-alpha density haze:  x = the batter's balls-faced index (1..60+,
 * capped bucket at the right edge),  y = cumulative innings runs (0..cap). A
 * rising staircase of one batter-innings is a "worm"; slope = strike rate. The
 * par / anchor exemplar worms are drawn by the SCENE on the annotation plane
 * (SVG, registered via projectToCss + this geometry), NEVER as GL polylines.
 *
 * HONESTY LOCK (storyboard §0.1 / §5.11): the plot's DATA aspect ratio is FIXED
 * (banked ~45° for a modern-par slope) and independent of the viewport — the
 * frame LETTERBOXES (adds margin) rather than stretching x or banking the worms
 * toward vertical, so the "sprints vs crawls" angular contrast reads identically
 * on desktop landscape and portrait phone (the primary target). The exact
 * banking + caps below are the owner-tunable constants flagged for build
 * sign-off; changing them keeps the fixed-aspect + letterbox invariant intact.
 * ------------------------------------------------------------------------- */

/** Balls-faced display clamp — the `60+` capped bucket at the right edge. */
export const WORM_X_CAP = 60;
/** Cumulative-runs display clamp — the top of the worm frame. */
export const WORM_RUNS_CAP = 130;
/**
 * Runs-per-ball that banks to ~45° in-frame (modern par ≈ 1.5 rpb → SR 150).
 * Sets the fixed data-box aspect so par sprints up-and-right while an anchor
 * crawls along the floor. Owner-tunable (§5.11).
 */
export const WORM_REF_RPB = 1.5;
/** Fraction of the frame the fixed-aspect plot box fills (the letterbox margin). */
export const WORM_FILL = 0.86;

export interface WormLayout {
	/** world x at balls-faced = 1 (the plot's left edge) */
	left: number;
	/** world width spanning balls-faced 1 → WORM_X_CAP */
	width: number;
	/** world y at cumulative runs = 0 (the plot's baseline) */
	bottom: number;
	/** world height spanning runs 0 → WORM_RUNS_CAP */
	height: number;
	/** balls-faced display clamp (60) — x beyond this stacks in the `60+` bucket */
	xCap: number;
	/** cumulative-runs display clamp (130) — the top of the frame */
	runsCap: number;
	/** in-cell horizontal jitter half-width (haze texture), world units */
	cellHalfW: number;
	/** in-cell vertical jitter half-height (haze texture), world units */
	cellHalfH: number;
}

/**
 * Fixed-aspect, letterboxed worm-space box for the current frame. The box's
 * world width/height ratio is locked to the data banking (independent of the
 * viewport); it is scaled to the largest size that fits the frame, then centred.
 */
export function computeWorms(halfW: number, halfH: number): WormLayout {
	// world width per world height for the FULL data box (fixed, viewport-independent)
	const boxAspect = ((WORM_X_CAP - 1) * WORM_REF_RPB) / WORM_RUNS_CAP;
	const frameW = 2 * halfW * WORM_FILL;
	const frameH = 2 * halfH * WORM_FILL;

	// letterbox: the largest fixed-aspect box that fits inside the frame
	let width = frameH * boxAspect;
	if (width > frameW) width = frameW;
	const height = width / boxAspect;

	const cellW = width / (WORM_X_CAP - 1);
	const cellH = height / WORM_RUNS_CAP;

	return {
		left: -width / 2,
		width,
		bottom: -height / 2,
		height,
		xCap: WORM_X_CAP,
		runsCap: WORM_RUNS_CAP,
		// sub-cell jitter so coincident balls spread into density texture, not z-fight
		cellHalfW: cellW * 0.5,
		cellHalfH: cellH * 0.85
	};
}

/**
 * World coordinate for a (balls-faced, cumulative-runs) data point in the given
 * worm-space box — the exact mapping the shader uses (balls clamped to the 60+
 * bucket, runs clamped to the cap). Scenes call this to register the par /
 * anchor exemplar worms and the axes to the GL haze via `field.projectToCss`.
 */
export function wormPoint(
	w: WormLayout,
	ballsFaced: number,
	cumRuns: number
): { x: number; y: number } {
	const bf = Math.min(Math.max(ballsFaced, 1), w.xCap);
	const wx = (bf - 1) / (w.xCap - 1);
	const wy = Math.min(Math.max(cumRuns, 0), w.runsCap) / w.runsCap;
	return { x: w.left + wx * w.width, y: w.bottom + wy * w.height };
}
