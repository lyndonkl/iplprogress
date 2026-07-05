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

/* ---------------------------------------------------------------------------
 * The frontier plane (Ch 3 controlling morph, CONTRACT §15). Every ball
 * condenses onto its BOWLER-SEASON coordinate, forming dense bowler-season
 * clouds settled as a low-alpha density haze:
 *   x = economy         (runs leaked per over; LEFT = cheap, RIGHT = expensive)
 *   y = bowling strike rate (legal balls per bowler-credited wicket;
 *                            BOTTOM = strikes fast, TOP = strikes slow)
 * so the promised land is the BOTTOM-LEFT corner (cheap AND deadly). Both axes
 * are "lower is better", so the retreating Pareto edge is the lower-left
 * staircase — drawn by the SCENE on the annotation plane (SVG), never GL
 * geometry. Positions are in-shader from the interleaved `bowlerplane.u8`
 * (byte 0 = economy, byte 1 = strike rate); no positions cross the wire.
 *
 * HONESTY LOCK (storyboard §0.1 / §5.2, mirroring worm-space): the plot's DATA
 * aspect ratio is FIXED and independent of the viewport — the frame LETTERBOXES
 * (adds margin) rather than stretching, so the bottom-left "cheap and deadly"
 * corner sits in the same place on desktop and portrait phone and the rightward
 * retreat reads identically. These constants MIRROR the emitted artifact's
 * coordinate space (`ch3.json` `frontier.axis` / `bowlerplane_buffer`): the
 * economy/strike-rate lo/hi below MUST equal the pipeline's, exactly as
 * WALLHEAT_NEUTRAL_BYTE mirrors the pipeline's wallheat pivot — if the buffer is
 * re-encoded over a different range these move with it.
 * ------------------------------------------------------------------------- */

/** Economy display range (RPO) — the x axis. Mirrors bowlerplane byte-0 decode. */
export const FRONTIER_ECON_LO = 4;
export const FRONTIER_ECON_HI = 16;
/** Bowling-strike-rate display range (balls per wicket) — the y axis. Mirrors byte-1. */
export const FRONTIER_SR_LO = 8;
export const FRONTIER_SR_HI = 60;
/** The "seven-an-over" containment reference line (economy = 7). */
export const FRONTIER_SEVEN = 7;
/** Right/top edges of the bottom-left "cheap and deadly" home zone (econ, SR). */
export const FRONTIER_HOME_ECON = 7;
export const FRONTIER_HOME_SR = 24;
/**
 * Fixed world width : world height for the data box (viewport-independent,
 * letterboxed). Owner-tunable (§5.2) — changing it keeps the letterbox invariant.
 */
export const FRONTIER_ASPECT = 1.15;
/** Fraction of the frame the fixed-aspect box fills (letterbox margin + label room). */
export const FRONTIER_FILL = 0.84;
/** Per-bowler-season cloud jitter radius, as a fraction of the box (density texture). */
export const FRONTIER_CLOUD = 0.014;

export interface FrontierLayout {
	/** world x at economy = FRONTIER_ECON_LO (the plot's left edge, "cheap") */
	left: number;
	/** world width spanning economy lo → hi */
	width: number;
	/** world y at strike-rate = FRONTIER_SR_LO (the plot's baseline, "fast") */
	bottom: number;
	/** world height spanning strike-rate lo → hi */
	height: number;
	/** economy display range (x) — mirrors the buffer decode */
	econLo: number;
	econHi: number;
	/** bowling-strike-rate display range (y) — mirrors the buffer decode */
	srLo: number;
	srHi: number;
	/** in-cloud x jitter half-width (density haze), world units */
	cellHalfW: number;
	/** in-cloud y jitter half-height (density haze), world units */
	cellHalfH: number;
	/** world x of the seven-an-over reference line (economy = FRONTIER_SEVEN) */
	sevenX: number;
	/** the bottom-left "cheap and deadly" home-zone box, world coords */
	home: { x0: number; y0: number; x1: number; y1: number };
	/** persistent axis end-anchor world positions (cheap/expensive on x; fast/slow on y) */
	cheapX: number;
	expensiveX: number;
	fastY: number;
	slowY: number;
}

/**
 * Fixed-aspect, letterboxed frontier-plane box for the current frame — the
 * largest box of the locked data aspect that fits, then centred. Scenes map the
 * per-season Pareto edge / ghost trail / reference lines from `ch3.json` (raw
 * economy + strike-rate units) into it via `frontierPoint`.
 */
export function computeFrontier(halfW: number, halfH: number): FrontierLayout {
	const frameW = 2 * halfW * FRONTIER_FILL;
	const frameH = 2 * halfH * FRONTIER_FILL;
	let width = frameH * FRONTIER_ASPECT;
	if (width > frameW) width = frameW;
	const height = width / FRONTIER_ASPECT;
	const left = -width / 2;
	const bottom = -height / 2;

	const econSpan = FRONTIER_ECON_HI - FRONTIER_ECON_LO;
	const srSpan = FRONTIER_SR_HI - FRONTIER_SR_LO;
	const xAt = (econ: number): number =>
		left + ((Math.min(Math.max(econ, FRONTIER_ECON_LO), FRONTIER_ECON_HI) - FRONTIER_ECON_LO) / econSpan) * width;
	const yAt = (sr: number): number =>
		bottom + ((Math.min(Math.max(sr, FRONTIER_SR_LO), FRONTIER_SR_HI) - FRONTIER_SR_LO) / srSpan) * height;

	return {
		left,
		width,
		bottom,
		height,
		econLo: FRONTIER_ECON_LO,
		econHi: FRONTIER_ECON_HI,
		srLo: FRONTIER_SR_LO,
		srHi: FRONTIER_SR_HI,
		cellHalfW: width * FRONTIER_CLOUD,
		cellHalfH: height * FRONTIER_CLOUD,
		sevenX: xAt(FRONTIER_SEVEN),
		home: { x0: left, y0: bottom, x1: xAt(FRONTIER_HOME_ECON), y1: yAt(FRONTIER_HOME_SR) },
		cheapX: left,
		expensiveX: left + width,
		fastY: bottom,
		slowY: bottom + height
	};
}

/**
 * World coordinate for a (economy, bowling-strike-rate) data point in the given
 * frontier box — the EXACT mapping the shader uses (both clamped to the display
 * range). Scenes call this to register the SVG Pareto edge, the ghost trail, the
 * seven-an-over line and the axis anchors to the GL haze via `field.projectToCss`,
 * so the annotation plane and the density haze can never drift. Pass raw units
 * (economy in RPO, strike rate in balls-per-wicket) straight from `ch3.json`.
 */
export function frontierPoint(
	f: FrontierLayout,
	economy: number,
	strikeRate: number
): { x: number; y: number } {
	const ex = (Math.min(Math.max(economy, f.econLo), f.econHi) - f.econLo) / (f.econHi - f.econLo);
	const sy = (Math.min(Math.max(strikeRate, f.srLo), f.srHi) - f.srLo) / (f.srHi - f.srLo);
	return { x: f.left + ex * f.width, y: f.bottom + sy * f.height };
}

/* ---------------------------------------------------------------------------
 * Dismissal-rivers layout (Ch 3 subset-highlight, CONTRACT §16). The wicket
 * subset streams OUT of the frontier clouds into a FLAT-BASELINE 100%-stacked
 * band: one vertical strip per season group (laid contiguously left→right so
 * the bands flow as continuous rivers), y = cumulative share 0 (baseline) → 1
 * (top). Each strip is partitioned bottom→top into the dismissal-kind bands
 * whose thicknesses are that season's kind shares. This is pure geometry (strip
 * x's + the band box); the per-point stacked y-fraction and the pooled band
 * label anchors are computed in field.ts from the setDismissals membership.
 * ------------------------------------------------------------------------- */

/** Fraction of the frame width the band box fills. */
export const RIVERS_FILL_W = 0.9;
/** Fraction of the frame height the band box fills (the 0→100% share axis). */
export const RIVERS_FILL_H = 0.64;

export interface RiversLayout {
	/** world x of each group's season strip centre, indexed by gi (NaN = excluded) */
	xs: number[];
	/** the gi's that received a strip, in x order (IPL seasons then WPL seasons) */
	gis: number[];
	/** in-strip x jitter half-width (fills the strip so bands read continuous) */
	stripHalfW: number;
	/** world x of the band box left edge */
	left: number;
	/** world width of the band box (all strips) */
	width: number;
	/** world y at 0% share (the flat baseline) */
	bottom: number;
	/** world y at 100% share (the top) */
	top: number;
	/** world height spanning 0 → 100% share */
	height: number;
}

/**
 * Contiguous per-season strips across the full width (IPL block then WPL block,
 * each season-sorted), filling a centred band box. No league gap — the bands
 * flow as one river; the scene draws the season axis + the WPL split in SVG.
 */
export function computeRivers(groups: GroupMeta[], halfW: number, halfH: number): RiversLayout {
	const ipl = groups.filter((g) => g.league === 'ipl').sort((a, b) => a.season - b.season);
	const wpl = groups.filter((g) => g.league === 'wpl').sort((a, b) => a.season - b.season);
	const ordered = [...ipl, ...wpl];

	const width = 2 * halfW * RIVERS_FILL_W;
	const left = -width / 2;
	const height = 2 * halfH * RIVERS_FILL_H;
	const bottom = -height / 2;
	const slotW = width / Math.max(1, ordered.length);

	const xs: number[] = new Array(groups.length).fill(NaN);
	const gis: number[] = [];
	ordered.forEach((g, i) => {
		xs[g.gi] = left + (i + 0.5) * slotW;
		gis.push(g.gi);
	});

	return {
		xs,
		gis,
		stripHalfW: slotW * 0.46,
		left,
		width,
		bottom,
		top: bottom + height,
		height
	};
}
