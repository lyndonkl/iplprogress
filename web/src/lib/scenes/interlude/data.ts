import { base } from '$app/paths';

/**
 * Typed access to the Net Session interlude's scene artifact:
 *   static/data/scenes/interlude.json — two dials on one precomputed lookup.
 *   surfaces.win[era]  : 20 × 10 × 10, indexed [oversLeft-1][wktsInHand-1][rrrBucket]
 *                        (engine #3's chase-win grid, wp_grid.json).
 *   surfaces.runs[era] : 20 × 10, indexed [oversLeft-1][wktsInHand-1]
 *                        (engine #2's run-expectancy surface, re288.json, re-indexed
 *                        to the same widget coordinate — runs depend only on resources,
 *                        never on the target).
 *   wpl.win_mask / runs_mask : the minimum-evidence mask (1 = too few chases to read).
 *   presets, era_anchor, footnotes.
 *
 * EVERY on-screen figure in IN-1..IN-6 resolves through here — never hand-typed
 * (OWNER-LOCK, storyboard §6). The widget does client-side derivation (required
 * rate → bucket → array lookup); it NEVER fits a model live. The two meters are
 * pure array reads. Fetched once per session, cached as a module-level promise,
 * always through `$app/paths` base.
 *
 * Honesty parity, both leagues (storyboard §0.1/§8): every surface ships a
 * per-cell n (surfaces.win_n / surfaces.runs_n), so ONE minimum-evidence rule
 * (evidence.win_min_n = 12 chases, runs_min_n = 15 innings) gates both leagues.
 * A cell at or above threshold is evidenced (a plain observed number); a thin
 * cell is demoted — the WPL renders it as a hole ("not enough WPL cricket yet"),
 * IPL free-play shows the number but marks it filled-in-by-rule and hatches its
 * grid square. The default spot (win n=124) is well evidenced, so the toy's
 * common path shows real numbers; only a drag into a sparse corner meets the flag.
 *
 * Presets (§9.2): preset 1 is a REAL Dhoni CHASE finish (Chennai chased 206 vs
 * Bangalore, 2018, read at the start of the final five overs) on an evidenced
 * second-innings cell — two currencies only, never a defend. The same-chase pair
 * is one exact grid square on two eras (21 → 34 in 100), framed as corroboration;
 * the robust window aggregate (23 → 31 in 100) is the default-visible era headline.
 */

/* ---- era keys -------------------------------------------------------------- */

/** The IPL free-play default (best-evidenced, all history). */
export const IPL_DEFAULT_ERA = 'ipl pooled';
/** The WPL surface both meters read when the league toggle is flipped. */
export const WPL_ERA = 'wpl 2023-2026';
/** The two era-anchor RUNS cells for the same-chase corroboration line. */
export const ERA_THEN = 'ipl 2008-2010';
export const ERA_NOW = 'ipl 2023-2026';

export type League = 'ipl' | 'wpl';

/* ---- artifact shape ------------------------------------------------------- */

export interface EraDef {
	key: string;
	label: string;
	short: string;
}

export interface MeterDef {
	format: string;
	gloss: string;
	label: string;
}

export interface SlidersDef {
	overs_left: string;
	runs_needed: string;
	wickets_in_hand: string;
}

export interface Bound {
	min: number;
	max: number;
}

export interface StateSpace {
	overs_left: Bound;
	wickets_in_hand: Bound;
	runs_needed: Bound;
	rrr_edges: number[];
	index: Record<string, string>;
}

export interface PresetMatch {
	batting_first: string;
	chasing: string;
	result: { by: Record<string, number>; winner: string };
	season: number;
	target: number;
	venue: string;
}

export interface PresetState {
	overs_left: number;
	wickets_in_hand: number;
	runs_needed: number;
}

export interface Preset {
	id: string;
	label: string;
	era: string;
	state: PresetState;
	win_pct: number;
	win_display: number;
	expected_runs: number;
	expected_runs_display: number;
	required_rate: number;
	copy: { orient: string; reveal: string };
	/** e.g. "2010" / "2025" for the same-chase pair */
	season_word?: string;
	/** the two ids that make the same-chase, two-eras pair */
	pair?: [string, string];
	match?: PresetMatch;
}

export interface EraAnchorCell {
	n: number;
	win_rate: number;
	wins: number;
}

export interface EraAnchor {
	definition: string;
	delta_points: number;
	ipl_2008_2012: EraAnchorCell;
	ipl_2023_2026: EraAnchorCell;
}

export interface Surfaces {
	/** [era][oversLeft-1][wktsInHand-1][rrrBucket] = P(chase win) */
	win: Record<string, number[][][]>;
	/** [era][oversLeft-1][wktsInHand-1] = expected runs still to come */
	runs: Record<string, number[][]>;
	/** [era][oversLeft-1][wktsInHand-1][rrrBucket] = real chases behind the win cell */
	win_n: Record<string, number[][][]>;
	/** [era][oversLeft-1][wktsInHand-1] = real innings behind the runs cell */
	runs_n: Record<string, number[][]>;
}

/** One minimum-evidence rule for both leagues (storyboard §0.1). */
export interface Evidence {
	win_min_n: number;
	runs_min_n: number;
	note: string;
}

/** Match counts behind the grids, so "1,331 / 88" binds to a field (§0.2). */
export interface Corpus {
	matches: number;
	ipl_matches: number;
	wpl_matches: number;
}

export interface CellCount {
	evidenced: number;
	masked: number;
	total: number;
}

export interface WplBlock {
	note: string;
	/** [oversLeft-1][wktsInHand-1][rrrBucket] — 1 = too few chases to read */
	win_mask: number[][][];
	win_mask_min_n: number;
	win_cells: CellCount;
	/** [oversLeft-1][wktsInHand-1] — 1 = too few innings to read */
	runs_mask: number[][];
	runs_mask_min_n: number;
	runs_cells: CellCount;
}

export interface FootnotesBlock {
	calibration: {
		text: string;
		win_calibration_n: number;
		win_ece: number;
		win_worst_populated_bin_abs_dev: number;
		runs_pooled_abs_dev_by_surface: Record<string, number>;
	};
	evidence_mask: { text: string; win_mask_min_n: number; runs_mask_min_n: number };
	wickets_early_rate_late: {
		text: string;
		early_overs_left: number;
		early_wicket_lever: number;
		early_win_10_wkts: number;
		early_win_5_wkts: number;
		hard_ask_rpo: string;
		late_overs_left: number;
		late_wicket_lever: number;
		late_win_10_wkts: number;
		late_win_5_wkts: number;
	};
}

export interface InterludeData {
	title: string;
	scene: string;
	release: string;
	default_era: string;
	note: string;
	intro: { orient: string; reveal: string };
	eras: EraDef[];
	sliders: SlidersDef;
	meters: { runs: MeterDef; win: MeterDef };
	state_space: StateSpace;
	surfaces: Surfaces;
	evidence: Evidence;
	corpus: Corpus;
	wpl: WplBlock;
	presets: Preset[];
	era_anchor: EraAnchor;
	engine_sources: { runs: string; win: string };
	footnotes: FootnotesBlock;
}

/* ---- the default spot (storyboard §3): a "game in the balance" state ------- */

export const DEFAULT_STATE: PresetState = {
	overs_left: 10,
	wickets_in_hand: 6,
	runs_needed: 90
};

/* ---- the lookup engine (client-side derivation, never a live model) -------- */

/**
 * The required-rate bucket, exactly as the pipeline indexed it
 * (state_space.index): the first edge the ask does not clear, else the last
 * bucket. rrr_edges = [6,7,8,9,10,11,12,15,20] → buckets 0..9. This is the ONLY
 * arithmetic the widget does beyond an array read; it reproduces every preset's
 * cell to the digit, so a meter can never contradict its own preset copy.
 */
export function rrrBucket(oversLeft: number, runsNeeded: number, edges: number[]): number {
	const rrr = runsNeeded / oversLeft;
	for (let i = 0; i < edges.length; i++) if (rrr < edges[i]) return i;
	return edges.length; // 9 — the "20 an over or worse" bucket
}

/** Win look-up for an era at a chase state (all three dials feed it). */
export function winAt(d: InterludeData, era: string, oL: number, w: number, R: number): number {
	const b = rrrBucket(oL, R, d.state_space.rrr_edges);
	return d.surfaces.win[era][oL - 1][w - 1][b];
}

/** Runs look-up for an era (overs left + wickets in hand only — never the ask). */
export function runsAt(d: InterludeData, era: string, oL: number, w: number): number {
	return d.surfaces.runs[era][oL - 1][w - 1];
}

/** WPL minimum-evidence: is this win cell built on too few chases to read? */
export function wplWinMasked(d: InterludeData, oL: number, w: number, R: number): boolean {
	const b = rrrBucket(oL, R, d.state_space.rrr_edges);
	return d.wpl.win_mask[oL - 1][w - 1][b] === 1;
}

/** WPL minimum-evidence: is this runs cell built on too few innings to read? */
export function wplRunsMasked(d: InterludeData, oL: number, w: number): boolean {
	return d.wpl.runs_mask[oL - 1][w - 1] === 1;
}

/** Real chases behind a win cell (the evidence count the gate reads). */
export function winN(d: InterludeData, era: string, oL: number, w: number, R: number): number {
	const b = rrrBucket(oL, R, d.state_space.rrr_edges);
	return d.surfaces.win_n[era][oL - 1][w - 1][b];
}

/** Real innings behind a runs cell. */
export function runsN(d: InterludeData, era: string, oL: number, w: number): number {
	return d.surfaces.runs_n[era][oL - 1][w - 1];
}

/**
 * A meter's resolved reading. Three states, one rule for both leagues (§0.1):
 *   - masked : a WPL hole — too few real matches, so NO number is shown.
 *   - thin   : an IPL free-play cell below the same threshold — the number IS
 *              shown, but demoted and flagged as filled in by rule, not counted.
 *   - neither: an evidenced, observed read.
 */
export interface MeterReading {
	masked: boolean;
	thin: boolean;
	value: number;
	display: number;
}

/** True for any WPL surface key (drives the minimum-evidence mask branch). */
export const isWplEra = (era: string): boolean => era.startsWith('wpl');

/**
 * The win meter's reading. Same minimum-evidence threshold for both leagues: a
 * thin WPL cell is a hole (masked, no number); a thin IPL cell is demoted (thin,
 * a filled-in-by-rule number). The default and mainstream chases are evidenced.
 */
export function readWin(d: InterludeData, era: string, oL: number, w: number, R: number): MeterReading {
	if (isWplEra(era) && wplWinMasked(d, oL, w, R)) return { masked: true, thin: false, value: 0, display: 0 };
	const v = winAt(d, era, oL, w, R);
	const thin = winN(d, era, oL, w, R) < d.evidence.win_min_n;
	return { masked: false, thin, value: v, display: Math.round(v * 100) };
}

/** The runs meter's reading (overs + wickets only), same evidence rule. */
export function readRuns(d: InterludeData, era: string, oL: number, w: number): MeterReading {
	if (isWplEra(era) && wplRunsMasked(d, oL, w)) return { masked: true, thin: false, value: 0, display: 0 };
	const v = runsAt(d, era, oL, w);
	const thin = runsN(d, era, oL, w) < d.evidence.runs_min_n;
	return { masked: false, thin, value: v, display: Math.round(v) };
}

/**
 * The same-chase, two-eras contrast — the interlude's default-visible climax.
 * The WIN pair binds to the well-sampled era anchor window (a whole window, not
 * one noisy cell) so it is the robust headline; the RUNS pair is the quiet
 * corroboration line, read from the era-band runs surfaces at the anchor's
 * representative spot (ten overs left, six in hand). Every value is a field read.
 */
export interface EraContrast {
	winThen: number;
	winNow: number;
	winGap: number;
	runsThen: number;
	runsNow: number;
}

export function eraContrast(d: InterludeData): EraContrast {
	const ea = d.era_anchor;
	const winThen = Math.round(ea.ipl_2008_2012.win_rate * 100);
	const winNow = Math.round(ea.ipl_2023_2026.win_rate * 100);
	return {
		winThen,
		winNow,
		winGap: winNow - winThen,
		runsThen: Math.round(runsAt(d, ERA_THEN, 10, 6)),
		runsNow: Math.round(runsAt(d, ERA_NOW, 10, 6))
	};
}

/** Preset by id (for wiring the same-chase pair). */
export function presetById(d: InterludeData, id: string): Preset | undefined {
	return d.presets.find((p) => p.id === id);
}

/* ---- the win-surface heat slice (the optional "show the grid" panel) -------
   One 20 (overs left) × 10 (wickets in hand) slice at the current ask bucket. A
   brighter square = teams win more often from there (luminance, never hue). A
   thin-ground square is hatched in EITHER league (same evidence_min rule, §2f),
   so a low-evidence spot never reads as a low-win spot. On the IPL surface this
   shows the solid middle and thin extreme corners; on the WPL most is hatched. */
export interface HeatCell {
	oversLeft: number;
	wkts: number;
	value: number;
	masked: boolean;
	current: boolean;
}

export function winHeatSlice(
	d: InterludeData,
	era: string,
	oL: number,
	w: number,
	R: number
): { rows: HeatCell[][]; bucket: number } {
	const bucket = rrrBucket(oL, R, d.state_space.rrr_edges);
	const surface = d.surfaces.win[era];
	const surfaceN = d.surfaces.win_n[era];
	const rows: HeatCell[][] = [];
	// rows = wickets in hand 10 (top) → 1 (bottom); columns = overs left 20 → 1
	for (let wi = 10; wi >= 1; wi--) {
		const row: HeatCell[] = [];
		for (let oi = 20; oi >= 1; oi--) {
			// thin ground = below the shared evidence threshold, hatched in either league
			const masked = surfaceN[oi - 1][wi - 1][bucket] < d.evidence.win_min_n;
			row.push({
				oversLeft: oi,
				wkts: wi,
				value: surface[oi - 1][wi - 1][bucket],
				masked,
				current: oi === oL && wi === w
			});
		}
		rows.push(row);
	}
	return { rows, bucket };
}

/* ---- loader (cached; base-path aware) ------------------------------------- */

let promise: Promise<InterludeData> | null = null;

export function loadInterludeData(): Promise<InterludeData> {
	promise ??= fetch(`${base}/data/scenes/interlude.json`).then((res) => {
		if (!res.ok) throw new Error(`interlude.json: HTTP ${res.status}`);
		return res.json() as Promise<InterludeData>;
	});
	return promise;
}

/* ---- formatters ----------------------------------------------------------- */

/** Integer with thousands separators (1,331 · 144,136). */
export const int = (n: number): string => n.toLocaleString('en-US');
