import type { ConstellationPhase, GroupMeta } from './types';

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

/* ---------------------------------------------------------------------------
 * The tide skyline (Ch 4 controlling morph, CONTRACT §18). Every ball condenses
 * onto its INNINGS-TOTAL COLUMN:
 *   x = season block (2008 left → this year right; the WPL block after a gap) +
 *       a within-season packing slot (innings ranked short→tall, so each season
 *       reads as a little skyline — the within-season x carries NO meaning and
 *       its ticks are suppressed by the scene)
 *   y = a column filled from the baseline up to the innings TOTAL (from
 *       innings_total.u8), so the taller the column the bigger the score.
 * The whole field reads as a coastline rising left→right as scoring climbs. Only
 * first-innings balls build columns; the rest settle into a low-alpha reservoir
 * haze near the floor (see field.setFirstInnings — the scene supplies membership
 * so "every ball ever is here" stays literally true). Positions are in-shader
 * from innings_total.u8 + the season group id + the baked within-season packing
 * index (packed into the single aTide attribute); no positions cross the wire.
 *
 * HONESTY LOCK (storyboard §0.1 / §6, mirroring worm-space + frontier): the box
 * holds a FIXED data aspect ratio independent of the viewport and LETTERBOXES on
 * portrait, so the coastline geometry (and the low-vs-high column heights, which
 * ARE the argument) survives mobile. TIDE_ASPECT / TIDE_FILL below are the
 * owner-tunable constants flagged for build sign-off; on a tall portrait the
 * letterbox keeps aspect, so if columns read too short the fix is a taller
 * TIDE_ASPECT or a horizontal season scrub — never a shorter column.
 * ------------------------------------------------------------------------- */

/**
 * Total-axis display cap (runs) — the top of the tide frame. y = 0 at the
 * baseline, y = TIDE_TOTAL_CAP at the frame top. Set at/above the current record
 * first innings (SRH 287) so the record column tops out honestly and is never
 * clipped (the storyboard's earlier 265 predates the 287 record; artifact wins).
 * The labeled ladder marks (120 / 160 / 200 / 240) sit inside it. Owner-tunable.
 */
export const TIDE_TOTAL_CAP = 300;
/** innings_total.u8 decode scale: decoded total (runs) = byte × TIDE_BYTE_SCALE. */
export const TIDE_BYTE_SCALE = 2;
/** Fixed world width : world height for the coastline box (viewport-independent). */
export const TIDE_ASPECT = 1.5;
/** Fraction of the frame the fixed-aspect box fills (letterbox margin + label room). */
export const TIDE_FILL = 0.9;
/** Season-block gap (in slot units) between the IPL block and the WPL block. */
export const TIDE_LEAGUE_GAP_SLOTS = 1.4;
/** Fraction of a season slot a season block's columns fill (jitter/packing bound). */
export const TIDE_BLOCK_FILL = 0.44;
/** Reservoir haze band height as a fraction of the box (non-first-innings balls). */
export const TIDE_RESERVOIR_FRAC = 0.15;

export interface TideLayout {
	/** world x at the box left edge */
	left: number;
	/** world width of the coastline box */
	width: number;
	/** world y at innings total = 0 (the baseline the columns rise from) */
	bottom: number;
	/** world height spanning total 0 → TIDE_TOTAL_CAP */
	height: number;
	/** total-axis display cap (runs) — mirrors the buffer decode */
	totalCap: number;
	/** world x of each season block's centre, indexed by gi (NaN = no block) */
	xs: number[];
	/** half-width of one season block, world units (columns pack within ±this) */
	blockHalfW: number;
	/** slot pitch in world units (season-axis label density decisions) */
	slotW: number;
	/** world height of the reservoir haze band (non-first-innings balls sit here) */
	reservoirH: number;
	/** centre x of the IPL block and the WPL block (for league / axis headings) */
	iplMidX: number;
	wplMidX: number;
}

/**
 * Fixed-aspect, letterboxed tide box for the current frame — the largest box of
 * the locked data aspect that fits, then centred; season blocks are laid across
 * its width (IPL block, a deliberate gap, then the WPL block, each season-sorted
 * oldest→newest). Scenes map the waterline / 200 / 230 / ghost / ladder marks
 * into it via `tidePoint` / `tideTotalToY`.
 */
export function computeTide(groups: GroupMeta[], halfW: number, halfH: number): TideLayout {
	const frameW = 2 * halfW * TIDE_FILL;
	const frameH = 2 * halfH * TIDE_FILL;
	let width = frameH * TIDE_ASPECT;
	if (width > frameW) width = frameW;
	const height = width / TIDE_ASPECT;
	const left = -width / 2;
	const bottom = -height / 2;

	const ipl = groups.filter((g) => g.league === 'ipl').sort((a, b) => a.season - b.season);
	const wpl = groups.filter((g) => g.league === 'wpl').sort((a, b) => a.season - b.season);
	const nIpl = ipl.length;
	const nWpl = wpl.length;
	const gapSlots = nWpl > 0 ? TIDE_LEAGUE_GAP_SLOTS : 0;
	const slots = nIpl + nWpl + gapSlots;
	const slotW = width / Math.max(1, slots);

	const xs: number[] = new Array(groups.length).fill(NaN);
	let iplSum = 0;
	let wplSum = 0;
	// IPL block: 2008 (left) → this year, then the gap, then the WPL block.
	ipl.forEach((g, i) => {
		const x = left + (i + 0.5) * slotW;
		xs[g.gi] = x;
		iplSum += x;
	});
	wpl.forEach((g, j) => {
		const x = left + (nIpl + gapSlots + j + 0.5) * slotW;
		xs[g.gi] = x;
		wplSum += x;
	});

	return {
		left,
		width,
		bottom,
		height,
		totalCap: TIDE_TOTAL_CAP,
		xs,
		blockHalfW: slotW * TIDE_BLOCK_FILL,
		slotW,
		reservoirH: height * TIDE_RESERVOIR_FRAC,
		iplMidX: nIpl > 0 ? iplSum / nIpl : 0,
		wplMidX: nWpl > 0 ? wplSum / nWpl : 0
	};
}

/**
 * World y for an innings TOTAL (runs) in the given tide box — the season-
 * independent height mapping the shader uses (clamped to the display cap). The
 * scene draws the rising waterline, the fixed 165 ghost line, the 200 / 230
 * reference rules and the total-axis ladder marks as SVG at this y, spanning the
 * coastline, registered to the GL skyline via `field.projectToCss`.
 */
export function tideTotalToY(layout: TideLayout, total: number): number {
	const tn = Math.min(Math.max(total, 0), layout.totalCap) / layout.totalCap;
	return layout.bottom + tn * layout.height;
}

/**
 * World coordinate for a (season block, innings total) pair — the EXACT mapping
 * the shader uses for a first-innings column TOP. `gi` is the season's group
 * index (the season block); `total` is the innings total in runs. x is the
 * season block centre, y is the column top for that total. Scenes call this to
 * anchor the season chip / scrub pointer / season-axis labels (x) and the
 * waterline + reference lines (y) to the GL skyline. For a pure horizontal rule
 * spanning all seasons, `tideTotalToY` is the y-only convenience.
 */
export function tidePoint(
	layout: TideLayout,
	gi: number,
	total: number
): { x: number; y: number } {
	const x = Number.isNaN(layout.xs[gi]) ? 0 : layout.xs[gi];
	return { x, y: tideTotalToY(layout, total) };
}

/* ---------------------------------------------------------------------------
 * The worth grid (Ch 5 controlling morph, CONTRACT §19). Every ball condenses
 * to the CELL of the match situation it was bowled in:
 *   x = the over of the innings   (over index 0 at the left → 19 at the right)
 *   y = wickets fallen when bowled (0 at the TOP → 9 at the bottom)
 * from restate.u8 (cell = over×10 + wicketsDown, 0..199). Points pack the cell
 * with deterministic in-shader jitter; cell LUMINANCE encodes the expected runs
 * still to come (the pricelens table, §19), density-normalized so integrated
 * cell brightness tracks the price, never the cell's crowd. Positions are
 * in-shader; no positions cross the wire.
 *
 * HONESTY LOCK (storyboard §0.1, mirroring worms/frontier/tide): the plot's
 * DATA aspect ratio is FIXED and independent of the viewport — the frame
 * LETTERBOXES (adds margin) rather than stretching, so the grid geometry (and
 * the brightest-at-top-left read) is identical on desktop and portrait phone.
 * WORTH_ASPECT / WORTH_FILL / WORTH_CELL_FILL and the density-gain constants
 * below are the owner-tunable constants flagged for build sign-off; changing
 * them keeps the fixed-aspect + letterbox invariant intact.
 * ------------------------------------------------------------------------- */

/** Grid extent: 20 overs across × 10 wickets-down rows. */
export const WORTH_OVERS = 20;
export const WORTH_WKTS = 10;
/** Fixed world width : world height for the grid box (viewport-independent). */
export const WORTH_ASPECT = 1.8;
/** Fraction of the frame the fixed-aspect box fills (letterbox + label room). */
export const WORTH_FILL = 0.86;
/** Fraction of a cell's pitch the points fill (the rest is the cell gutter). */
export const WORTH_CELL_FILL = 0.8;
/**
 * Density-normalization gain (§0.1 BINDING): per-point intensity is scaled by
 * gain(cell) = clamp((WORTH_GAIN_TARGET / cellCount)^WORTH_GAIN_POW,
 * WORTH_GAIN_MIN, 1) so a cell's INTEGRATED brightness tracks the price table
 * no matter how many balls live there (cell populations run 1 → ~15k). The
 * exponent < 1 compensates alpha-compositing saturation in crowded cells; the
 * clamp floor keeps ultra-dense cells from vanishing per-point. Owner-tunable.
 */
export const WORTH_GAIN_TARGET = 260;
export const WORTH_GAIN_MIN = 0.02;
export const WORTH_GAIN_POW = 0.85;

export interface WorthLayout {
	/** world x at the grid's left edge (over index 0) */
	left: number;
	/** world width spanning overs 0 → 19 */
	width: number;
	/** world y at the grid's bottom edge (9 wickets down) */
	bottom: number;
	/** world height spanning wickets-down 9 (bottom) → 0 (top) */
	height: number;
	/** grid extent (20 × 10) — mirrors the restate.u8 encoding */
	overs: number;
	wkts: number;
	/** one cell's world pitch (x / y) */
	cellW: number;
	cellH: number;
	/** half-extent of a cell's POINT-FILLED body (pitch × WORTH_CELL_FILL / 2) */
	cellHalfW: number;
	cellHalfH: number;
}

/**
 * Fixed-aspect, letterboxed worth-grid box for the current frame — the largest
 * box of the locked data aspect that fits, then centred. Scenes register cell
 * rings / hatching / axis labels via `worthCell` + `field.projectToCss`.
 */
export function computeWorth(halfW: number, halfH: number): WorthLayout {
	const frameW = 2 * halfW * WORTH_FILL;
	const frameH = 2 * halfH * WORTH_FILL;
	let width = frameH * WORTH_ASPECT;
	if (width > frameW) width = frameW;
	const height = width / WORTH_ASPECT;
	const cellW = width / WORTH_OVERS;
	const cellH = height / WORTH_WKTS;
	return {
		left: -width / 2,
		width,
		bottom: -height / 2,
		height,
		overs: WORTH_OVERS,
		wkts: WORTH_WKTS,
		cellW,
		cellH,
		cellHalfW: (cellW * WORTH_CELL_FILL) / 2,
		cellHalfH: (cellH * WORTH_CELL_FILL) / 2
	};
}

/**
 * World coordinate of a worth-grid CELL CENTRE for (over index 0..19,
 * wicketsDown 0..9) — the EXACT mapping the shader uses (0 wickets at the TOP),
 * so annotation-plane rings, hatches, readouts and the C5-6b hero rings can
 * never drift from the GL cells. The cell's rect is centre ± (cellW/2, cellH/2)
 * (use `cellHalfW/H` for the point-filled body). Project with
 * `field.projectToCss`.
 */
export function worthCell(
	w: WorthLayout,
	over: number,
	wicketsDown: number
): { x: number; y: number } {
	const o = Math.min(Math.max(over, 0), w.overs - 1);
	const k = Math.min(Math.max(wicketsDown, 0), w.wkts - 1);
	return {
		x: w.left + ((o + 0.5) / w.overs) * w.width,
		y: w.bottom + (1 - (k + 0.5) / w.wkts) * w.height
	};
}

/* ---------------------------------------------------------------------------
 * The season constellation (Ch 6 controlling morph, CONTRACT §22). Every ball
 * condenses onto its SEASON-GROUP STAR: a per-phase table of 23 (x,y) star
 * centres (all / powerplay / middle / death), indexed in-shader by the ball's
 * group id (`group_ids.u16` = position.y). Each ball sits at its star centre +
 * a small radial jitter, so a star reads as a GLOWING DISC of its own balls,
 * not an abstract dot. No new per-point buffer (the map reuses group_ids.u16);
 * the only new data is the tiny star table fed once via field.setStarTables.
 *
 * The star coordinates arrive PRE-NORMALIZED by the pipeline into ONE common
 * [-1, 1] frame with a SINGLE global scale factor across all four phases (so
 * distances are comparable both within a phase and between phases, and the
 * Procrustes-aligned WPL never flips sides). Because that normalization is
 * aspect-PRESERVING, the frame is a true SQUARE in data space: 1 unit of x =
 * 1 unit of y. So the box aspect is fixed at 1 and this layout maps the whole
 * [-1, 1] frame (centred at the origin) into the largest square that fits,
 * LETTERBOXING on portrait (the Ch 2/3/4/5 honesty lock) — the WPL sits beside
 * the men's path identically on desktop and phone. NEVER a live re-embed: the
 * positions are a lookup (a browser re-fit could mirror-flip the WPL, §0.1).
 *
 * CONSTELLATION_ASPECT / CONSTELLATION_FILL / CONSTELLATION_STAR_RADIUS are the
 * owner-tunable constants flagged for build sign-off (storyboard §0.1); changing
 * them keeps the fixed-aspect + letterbox invariant intact.
 * ------------------------------------------------------------------------- */

/** All four phase ids, in canonical order (feed / iteration order). */
export const CONSTELLATION_PHASES: readonly ConstellationPhase[] = [
	'all',
	'powerplay',
	'middle',
	'death'
];

/**
 * Fixed world width : world height for the star box. 1 (square), because the
 * star coordinates are already aspect-preserved in a common [-1,1] frame — the
 * box must map that frame 1:1 in both axes or it would distort the distances,
 * which ARE the whole meaning of the map (storyboard §0.1). Owner-tunable.
 */
export const CONSTELLATION_ASPECT = 1;
/** Fraction of the frame the fixed-aspect box fills (letterbox + legend/label room). */
export const CONSTELLATION_FILL = 0.82;
/**
 * A star's jitter-disc radius as a fraction of the box half-extent — sets how
 * fat each season's glowing cluster reads. Small enough that neighbouring stars
 * stay distinct, large enough that a star looks like a disc of deliveries.
 * Owner-tunable; mirrored into the shader's uConstStarR each resize.
 */
export const CONSTELLATION_STAR_RADIUS = 0.055;

export interface ConstellationLayout {
	/** world x of the box's left edge (normalized x = -1) */
	left: number;
	/** world width of the box (normalized x span -1 → 1) */
	width: number;
	/** world y of the box's bottom edge (normalized y = -1) */
	bottom: number;
	/** world height of the box (== width; the data box aspect is 1) */
	height: number;
	/** world half-size of the [-1,1] normalized frame (== width/2 == height/2) */
	halfExtent: number;
	/** world radius of a star's jitter disc (mirrors the shader's uConstStarR) */
	starRadius: number;
}

/**
 * Fixed-aspect (square), letterboxed constellation box for the current frame —
 * the largest square that fits, centred at the origin. The star tables' [-1,1]
 * frame maps into it via `constellationPoint`. Rebuilt on resize.
 */
export function computeConstellation(halfW: number, halfH: number): ConstellationLayout {
	const frameW = 2 * halfW * CONSTELLATION_FILL;
	const frameH = 2 * halfH * CONSTELLATION_FILL;
	let width = frameH * CONSTELLATION_ASPECT;
	if (width > frameW) width = frameW;
	const height = width / CONSTELLATION_ASPECT;
	const halfExtent = width / 2;
	return {
		left: -width / 2,
		width,
		bottom: -height / 2,
		height,
		halfExtent,
		starRadius: halfExtent * CONSTELLATION_STAR_RADIUS
	};
}

/**
 * World coordinate for a NORMALIZED star position (nx, ny each in [-1,1], from
 * `scenes/ch6.json`) in the given constellation box — the EXACT centre mapping
 * the shader uses (the frame is centred at the origin, so world = n × halfExtent
 * with no jitter). Scenes call this to register the men's worm polyline, the WPL
 * dotted threads, the star labels, the persistent legend and the payoff
 * sister-thread to the GL star centres via `field.projectToCss`, and to place a
 * caption clear of the emitted WPL cluster hull (§0.4a). For a per-gi star that
 * tracks the LIVE phase lerp, read `field.getConstellationLayout().stars[gi]`.
 */
export function constellationPoint(
	layout: ConstellationLayout,
	nx: number,
	ny: number
): { x: number; y: number } {
	return { x: nx * layout.halfExtent, y: ny * layout.halfExtent };
}

/* ---------------------------------------------------------------------------
 * The over rail (Ch 5 set piece, CONTRACT §20): slot capacity for the six(+)
 * lifted balls. Uniform arrays and the overlay draw are sized to this.
 * ------------------------------------------------------------------------- */
export const RAIL_MAX_SLOTS = 8;

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

/* ---------------------------------------------------------------------------
 * The twin rivers (Ch 7 controlling morph, CONTRACT §23). Every ball condenses
 * to its LEAGUE-SEASON RIVER CELL, forming two flowing ribbons:
 *   x = the ball's SEASON along a shared time axis (IPL 2008 left → 2026 right;
 *       the WPL's 2023-2026 share the SAME season x's, so its ribbon sources at
 *       2023 right alongside the IPL — the honest diff-in-diff geometry: there is
 *       no faked pre-2023 stretch for the WPL, it simply begins at the rule year)
 *   y = that league-season's RUN RATE on a fixed "runs an over" axis (the per-gi
 *       river table fed via field.setRiverTable), plus a FIXED DECORATIVE band
 *       thickness (a constant jitter around the centreline, NOT a ball-count /
 *       volume encoding — height means run rate, full stop), so the ribbon reads
 *       as a flowing band of its own balls.
 * The two rivers run parallel over the shared window and DIVERGE at 2023 (the IPL
 * climbing, the WPL staying level); the causal read is the VERTICAL GAP between
 * the two centrelines, which the scene draws as clean SVG lines on the annotation
 * plane. Positions are in-shader from the season group id (group_ids.u16 = the
 * ball's gi = position.y; the league bit rides along) against the small river
 * table; no positions cross the wire, no new per-point buffer.
 *
 * This layout.ts function owns only the letterboxed BOX + the per-gi season x's
 * (derived from each group's SEASON YEAR, so IPL-2023 and WPL-2023 land on the
 * same x). The per-gi centreline HEIGHTS (run rate) + the flat baseline for the
 * lift + the band thickness + the fork season are fed by the scene into
 * field.setRiverTable; field.ts bakes them into the uFlow uniform against this box.
 *
 * HONESTY LOCK (storyboard §0.1, mirroring worms/frontier/tide/worth/constellation):
 * the plot's DATA aspect ratio is FIXED and independent of the viewport — the
 * frame LETTERBOXES (adds margin) rather than stretching, so the vertical gap
 * between the two rivers reads identically on desktop and portrait phone.
 * FLOW_ASPECT / FLOW_FILL / FLOW_RIBBON_ALPHA are the owner-tunable constants
 * flagged for build sign-off; changing them keeps the fixed-aspect + letterbox
 * invariant intact.
 * ------------------------------------------------------------------------- */

/** Fixed world width : world height for the twin-rivers box (viewport-independent). */
export const FLOW_ASPECT = 1.6;
/** Fraction of the frame the fixed-aspect box fills (letterbox margin + axis/label room). */
export const FLOW_FILL = 0.82;
/**
 * Base alpha the flow ribbons settle to: the two rivers are dense bands (~310k
 * IPL balls across 19 seasons), so a moderate alpha lets each ribbon read as a
 * bright band of texture rather than a saturated blob (brighter than the worm
 * haze 0.3 — the rivers are the hero visual, not a low haze). Team-ignited points
 * resist it (personalization survives). Owner-tunable; baked as FLOW_RIBBON_A.
 */
export const FLOW_RIBBON_ALPHA = 0.5;

export interface FlowLayout {
	/** world x at the box left edge (the earliest season) */
	left: number;
	/** world width of the twin-rivers box (season axis span) */
	width: number;
	/** world y at run rate = the axis low (the box floor) */
	bottom: number;
	/** world height spanning the "runs an over" axis low → high */
	height: number;
	/** world x of each group's SEASON centre, indexed by gi (NaN = no season) */
	xs: number[];
	/** earliest / latest season year across all groups (the shared time axis span) */
	minSeason: number;
	maxSeason: number;
	/**
	 * in-season x jitter half-width = half the year pitch, so adjacent seasons'
	 * balls meet and the ribbon reads continuous left→right (world units)
	 */
	cellHalfW: number;
}

/**
 * Fixed-aspect, letterboxed twin-rivers box for the current frame — the largest
 * box of the locked data aspect that fits, then centred. Season x's are laid by
 * SEASON YEAR across a shared time axis (minSeason → maxSeason), so an IPL season
 * and the WPL season of the same year share one x (the two rivers run over the
 * same window). The per-gi run-rate heights are fed separately via
 * field.setRiverTable; this box only carries the season-x mapping + the frame.
 */
export function computeFlow(groups: GroupMeta[], halfW: number, halfH: number): FlowLayout {
	const frameW = 2 * halfW * FLOW_FILL;
	const frameH = 2 * halfH * FLOW_FILL;
	let width = frameW;
	if (width > frameH * FLOW_ASPECT) width = frameH * FLOW_ASPECT;
	const height = width / FLOW_ASPECT;
	const left = -width / 2;
	const bottom = -height / 2;

	let minSeason = Infinity;
	let maxSeason = -Infinity;
	for (const g of groups) {
		if (g.season < minSeason) minSeason = g.season;
		if (g.season > maxSeason) maxSeason = g.season;
	}
	if (!Number.isFinite(minSeason)) {
		minSeason = 0;
		maxSeason = 1;
	}
	const span = Math.max(1, maxSeason - minSeason);

	const xs: number[] = new Array(groups.length).fill(NaN);
	for (const g of groups) xs[g.gi] = left + ((g.season - minSeason) / span) * width;

	return {
		left,
		width,
		bottom,
		height,
		xs,
		minSeason,
		maxSeason,
		// half the year pitch: adjacent seasons' jitter meets exactly, so the ribbon
		// reads as one continuous band rather than separated per-season columns.
		cellHalfW: (width / span) * 0.5
	};
}

/**
 * World x for a SEASON YEAR in the given flow box — the exact mapping the shader
 * uses for a season centre (before the in-season jitter). Scenes call this to
 * anchor the season-axis labels, the 2023 fork marker and any season chip to the
 * GL ribbons via `field.projectToCss`. `season` may be fractional (e.g. 2022.5
 * for a tick between years).
 */
export function flowSeasonToX(
	layout: { left: number; width: number; minSeason: number; maxSeason: number },
	season: number
): number {
	const span = Math.max(1, layout.maxSeason - layout.minSeason);
	return layout.left + ((season - layout.minSeason) / span) * layout.width;
}

/**
 * World y for a RUN RATE (runs an over) in the given flow box + rate axis — the
 * exact mapping field.ts bakes into the uFlow centreline uniform, so the scene's
 * SVG centrelines, the gap read and the "runs an over" axis marks can never drift
 * from the GL ribbons. `rateLo` / `rateHi` are the axis range the scene fed via
 * setRiverTable (returned on `getFlowLayout()`). Clamped to the axis.
 */
export function flowRateToY(
	layout: { bottom: number; height: number; rateLo: number; rateHi: number },
	rate: number
): number {
	const span = layout.rateHi - layout.rateLo;
	const norm = span > 0 ? (Math.min(Math.max(rate, layout.rateLo), layout.rateHi) - layout.rateLo) / span : 0;
	return layout.bottom + norm * layout.height;
}

/* ---------------------------------------------------------------------------
 * The match-dots (Ch 8 controlling morph, CONTRACT §24). Every ball condenses to
 * the CENTROID of the MATCH it belongs to, forming 1,331 glowing discs (one dot =
 * one whole match):
 *   x = the match's SEASON/TIME position (2008 left → 2026 right)
 *   y = the match centroid; the held `matchSplit` scalar lerps each dot into its
 *       toss lane (winner batted first → upper lane, winner chose to field → lower
 *       lane), so the field-first river swells after 2016 straight from the data.
 * The per-match normalized centroid (nx, ny each in [-1,1]), the toss class and a
 * density gain live in a `uMatchTex` data texture; the ball's match id is recovered
 * in-shader by a binary search of position.x against a `match_bounds` data texture
 * (both fed once via field.setMatchTable). NO new per-point buffer, NO new vertex
 * attribute — the field holds at 14 attributes.
 *
 * This layout.ts function owns only the letterboxed BOX (the per-axis half extents
 * that map the normalized [-1,1] centroid frame to world) + the lane geometry (the
 * world lane-centre offset and the lane band half-height) + the constant jitter-disc
 * radius. The per-match world centroids for the LIVE `matchSplit` are re-derived on
 * `getMatchDotsLayout()`, so the scene's SVG lane labels / season axis / crossover
 * lines / WPL circles can never drift from the GL dots.
 *
 * HONESTY LOCK (mirroring worms/frontier/tide/worth/constellation/flow): the box holds
 * a FIXED data aspect independent of the viewport and LETTERBOXES on portrait, so the
 * time axis and the two toss lanes read identically on desktop and phone. The consts
 * below are owner-tunable (storyboard §7); changing them keeps the letterbox invariant.
 * ------------------------------------------------------------------------- */

/** Fixed world width : world height for the match-dots box (wide — the time axis). */
export const MATCHDOTS_ASPECT = 1.7;
/** Fraction of the frame the fixed-aspect box fills (letterbox + axis/label room). */
export const MATCHDOTS_FILL = 0.84;
/** A match dot's jitter-disc radius as a fraction of the box half-height (constant — no data). */
export const MATCHDOTS_DOT_RADIUS = 0.02;
/** Lane-centre offset (bat-first up / field-first down) as a fraction of the box half-height. */
export const MATCHDOTS_LANE = 0.42;
/** Lane band half-height as a fraction of the box half-height (the dots spread inside the lane). */
export const MATCHDOTS_LANE_HALF = 0.2;
/**
 * Per-match DENSITY GAIN (mirrors the worth-grid §0.1 gain): a dot's per-ball alpha
 * is scaled by clamp((MATCHDOTS_GAIN_TARGET / ballCount)^POW, MIN, 1) so a match's
 * INTEGRATED dot brightness is (near) independent of how many balls it had — a longer
 * / run-heavier match is never brighter than a short one (the design gate that killed
 * data-varying luminance). ~230-ball full T20s land near 1; short/rain matches are
 * lifted, huge ones damped. Owner-tunable; used in field.ts setMatchTable.
 */
export const MATCHDOTS_GAIN_TARGET = 230;
export const MATCHDOTS_GAIN_MIN = 0.05;
export const MATCHDOTS_GAIN_POW = 0.85;

export interface MatchDotsLayout {
	/** world x of the box left edge (normalized x = -1) */
	left: number;
	/** world width of the box (normalized x span -1 → 1) */
	width: number;
	/** world y of the box bottom edge (normalized y = -1) */
	bottom: number;
	/** world height of the box (normalized y span -1 → 1) */
	height: number;
	/** world half-width — normalized nx ∈ [-1,1] maps to world x = nx × halfW */
	halfW: number;
	/** world half-height — normalized ny ∈ [-1,1] maps to world y = ny × halfH */
	halfH: number;
	/** world radius of a match dot's constant jitter disc (mirrors uMatchDotR) */
	dotRadius: number;
	/** world lane-centre offset (upper lane +laneY, lower lane -laneY; mirrors uMatchLaneY) */
	laneY: number;
	/** world lane band half-height the dots spread within a lane (mirrors uMatchLaneHalf) */
	laneHalf: number;
}

/**
 * Fixed-aspect, letterboxed match-dots box for the current frame — the largest box
 * of the locked data aspect that fits, then centred at the origin. The normalized
 * [-1,1] centroid frame maps into it via `matchDotsPoint`. Rebuilt on resize.
 */
export function computeMatchDots(halfW: number, halfH: number): MatchDotsLayout {
	const frameW = 2 * halfW * MATCHDOTS_FILL;
	const frameH = 2 * halfH * MATCHDOTS_FILL;
	let width = frameH * MATCHDOTS_ASPECT;
	if (width > frameW) width = frameW;
	const height = width / MATCHDOTS_ASPECT;
	const hw = width / 2;
	const hh = height / 2;
	return {
		left: -hw,
		width,
		bottom: -hh,
		height,
		halfW: hw,
		halfH: hh,
		dotRadius: hh * MATCHDOTS_DOT_RADIUS,
		laneY: hh * MATCHDOTS_LANE,
		laneHalf: hh * MATCHDOTS_LANE_HALF
	};
}

/**
 * World coordinate for a NORMALIZED match centroid (nx, ny each in [-1,1], from
 * `scenes/ch8.json` `match_dots.centroids`) in the given box — the NEUTRAL (pre-split)
 * centre the shader uses at `matchSplit` 0 (world = n × halfExtent, no jitter). Scenes
 * call this to register the season axis, lane labels and the crossover's anchors to the
 * GL dots via `field.projectToCss`. For a per-match centre that tracks the LIVE
 * `matchSplit` (the toss lane lift), read `field.getMatchDotsLayout().centres[m]`.
 */
export function matchDotsPoint(
	layout: MatchDotsLayout,
	nx: number,
	ny: number
): { x: number; y: number } {
	return { x: nx * layout.halfW, y: ny * layout.halfH };
}

/* ---------------------------------------------------------------------------
 * The review chips (Ch 8 subset, CONTRACT §25). The 988 review deliveries fly OUT
 * of the held match-dots into per-team chip stacks: one vertical column per franchise
 * LANE, laid evenly across a centred box, struck-down (red) chips at the bottom and
 * upheld (green) chips stacked on top. Each lane's height is proportional to its review
 * count (normalized against the busiest lane), so the volume is honest and "mostly
 * red = mostly the call stood" reads by area. This function owns only the box + the
 * per-lane x's; the per-point cumulative stack slot is baked in field.ts.
 * ------------------------------------------------------------------------- */

/** Fraction of the frame width the chip-stack box fills. */
export const REVIEW_FILL_W = 0.9;
/** Fraction of the frame height the chip-stack box fills. */
export const REVIEW_FILL_H = 0.7;

export interface ReviewChipsLayout {
	/** world x of the box left edge */
	left: number;
	/** world width of the box (all lanes) */
	width: number;
	/** world y at the stack baseline (0% — chips build up from here) */
	bottom: number;
	/** world y at the top of the busiest lane (100%) */
	top: number;
	/** world height spanning 0 → the busiest lane */
	height: number;
	/** world x of each lane's centre, indexed by lane index (length nLanes) */
	laneXs: number[];
	/** in-lane x jitter half-width (fills the column so chips read as a stack) */
	laneHalfW: number;
	/** slot pitch in world units (label-density decisions) */
	slotW: number;
}

/**
 * Evenly-spaced review chip lanes across a centred box for the current frame. `nLanes`
 * is the number of franchise columns the scene assigned (via the `team` lane indices in
 * `field.setReviews`). Scenes anchor lane labels / the green-red legend / the per-chip
 * tick-cross glyphs to these via `getReviewChipsLayout()` + `field.projectToCss`.
 */
export function computeReviewChips(nLanes: number, halfW: number, halfH: number): ReviewChipsLayout {
	const width = 2 * halfW * REVIEW_FILL_W;
	const left = -width / 2;
	const height = 2 * halfH * REVIEW_FILL_H;
	const bottom = -height / 2;
	const lanes = Math.max(1, nLanes);
	const slotW = width / lanes;
	const laneXs: number[] = new Array(nLanes);
	for (let i = 0; i < nLanes; i++) laneXs[i] = left + (i + 0.5) * slotW;
	return {
		left,
		width,
		bottom,
		top: bottom + height,
		height,
		laneXs,
		laneHalfW: slotW * 0.4,
		slotW
	};
}

/* ---------------------------------------------------------------------------
 * The duel web (Ch 9 controlling morph, CONTRACT §26). Every ball condenses onto
 * its DUEL's strand-midpoint cluster centre (px, py each in [-1,1], where that
 * batter-vs-bowler pairing's deliveries pile) + a small radial jitter disc, so a
 * strand reads as a glowing band of its own balls; balls in no tracked pairing
 * scatter as low-alpha DUST. The per-duel cluster centre + dominance color + ball
 * weight lives in a `uDuelTex` data texture; the ball's duel id is recovered
 * in-shader by a texelFetch of `uPairingTex` (indexed by point index; 0xFFFF =
 * dust) — both fed once via field.setDuelGraph. NO new per-point buffer, NO new
 * vertex attribute — the field holds at 14 attributes.
 *
 * This layout.ts function owns only the letterboxed SQUARE box (the half-extent
 * that maps the normalized [-1,1] node / strand-midpoint frame to world) + the
 * constant jitter-disc radius. The per-node world coordinates are re-derived on
 * `getDuelWebLayout()` so the scene's SVG strands, player dots and tap targets can
 * never drift from the GL clusters.
 *
 * HONESTY LOCK (mirroring constellation): the pipeline emits the node + strand-
 * midpoint coordinates PRE-NORMALIZED into ONE aspect-preserving [-1,1] frame, so
 * the box is a true SQUARE (1 unit of x = 1 unit of y) and maps that frame into the
 * largest square that fits, LETTERBOXING on portrait — the web reads identically on
 * desktop and phone. NEVER a live re-embed (a browser re-fit could distort the
 * force layout). The consts below are owner-tunable (storyboard §7); changing them
 * keeps the fixed-aspect + letterbox invariant intact.
 * ------------------------------------------------------------------------- */

/** Fixed world width : world height for the duel-web box. 1 (square) — the node /
 *  strand coordinates are already aspect-preserved in a common [-1,1] frame. */
export const DUELWEB_ASPECT = 1;
/** Fraction of the frame the fixed-aspect box fills (letterbox + label/legend room). */
export const DUELWEB_FILL = 0.86;
/** A strand cluster's jitter-disc radius as a fraction of the box half-extent (constant — no data). */
export const DUELWEB_DOT_RADIUS = 0.02;

export interface DuelWebLayout {
	/** world x of the box's left edge (normalized x = -1) */
	left: number;
	/** world width of the box (normalized x span -1 → 1) */
	width: number;
	/** world y of the box's bottom edge (normalized y = -1) */
	bottom: number;
	/** world height of the box (== width; the data box aspect is 1) */
	height: number;
	/** world half-size of the [-1,1] normalized frame (== width/2 == height/2) */
	halfExtent: number;
	/** world radius of a strand cluster's jitter disc (mirrors the shader's uDuelDotR) */
	dotRadius: number;
}

/**
 * Fixed-aspect (square), letterboxed duel-web box for the current frame — the largest
 * square that fits, centred at the origin. The node / strand-midpoint [-1,1] frame maps
 * into it via `duelWebPoint`. Rebuilt on resize.
 */
export function computeDuelWeb(halfW: number, halfH: number): DuelWebLayout {
	const frameW = 2 * halfW * DUELWEB_FILL;
	const frameH = 2 * halfH * DUELWEB_FILL;
	let width = frameH * DUELWEB_ASPECT;
	if (width > frameW) width = frameW;
	const height = width / DUELWEB_ASPECT;
	const halfExtent = width / 2;
	return {
		left: -width / 2,
		width,
		bottom: -height / 2,
		height,
		halfExtent,
		dotRadius: halfExtent * DUELWEB_DOT_RADIUS
	};
}

/**
 * World coordinate for a NORMALIZED duel-web position (nx, ny each in [-1,1], from
 * `scenes/ch9.json` node / strand-midpoint coords) in the given box — the EXACT
 * centre mapping the shader uses (the frame is centred at the origin, so world =
 * n × halfExtent with no jitter). Scenes call this to register the SVG strands,
 * player dots and tap targets to the GL clusters via `field.projectToCss`.
 */
export function duelWebPoint(
	layout: DuelWebLayout,
	nx: number,
	ny: number
): { x: number; y: number } {
	return { x: nx * layout.halfExtent, y: ny * layout.halfExtent };
}

/* ---------------------------------------------------------------------------
 * The ribbon (Ch 10 controlling morph, CONTRACT §27 — the finale). Every ball
 * condenses onto one long CHRONOLOGICAL band: x = the ball's own point index
 * 0..N-1 mapped left→right (essentially match order 2008→2026), y = a thin
 * centred band + a small hashed jitter so the dense stream reads as texture.
 * The whole layout is a PURE FUNCTION of the point index (position.x) — NO new
 * per-point buffer / attribute / data texture (the field holds at 14). The
 * fault-line cracks are SCENE-drawn SVG, anchored to the band via the world x
 * `getRibbonLayout().pointToX(i)` returns (which mirrors the shader's exact
 * `(i/N * 2 - 1) * halfW * RIBBON_X_FRAC`).
 *
 * This function owns only the band BOX + the band centre/half-thickness the
 * shader reads as uRibbonBandY / uRibbonBandHalf. Unlike the fixed-aspect
 * layouts the ribbon spans the FULL frame width (like the free field), so a
 * wider viewport just stretches the time axis; the band stays a thin letterbox.
 * ------------------------------------------------------------------------- */

/** Fraction of the frame half-width the ribbon spans (matches the shader's uHalfW × this). */
export const RIBBON_X_FRAC = 0.95;
/** Ribbon band half-thickness as a fraction of the frame half-height (a thin centred band). */
export const RIBBON_BAND_HALF_FRAC = 0.08;

export interface RibbonLayout {
	/** world x at the earliest ball (point index 0) */
	left: number;
	/** world width spanning point index 0 → N-1 */
	width: number;
	/** world y at the band bottom edge */
	bottom: number;
	/** world height of the band */
	height: number;
	/** world y of the band centre (mirrors uRibbonBandY) */
	bandY: number;
	/** world half-thickness of the band (mirrors uRibbonBandHalf) */
	bandHalf: number;
}

/**
 * The centred chronological band box for the current frame — full-width (± the
 * frame half-width × RIBBON_X_FRAC, matching the shader) and a thin letterboxed
 * band centred at the origin. Rebuilt on resize.
 */
export function computeRibbon(halfW: number, halfH: number): RibbonLayout {
	const left = -RIBBON_X_FRAC * halfW;
	const width = 2 * RIBBON_X_FRAC * halfW;
	const bandY = 0;
	const bandHalf = RIBBON_BAND_HALF_FRAC * halfH;
	return {
		left,
		width,
		bottom: bandY - bandHalf,
		height: 2 * bandHalf,
		bandY,
		bandHalf
	};
}
