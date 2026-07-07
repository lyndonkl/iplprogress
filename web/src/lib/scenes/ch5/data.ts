import { base } from '$app/paths';
import { loadSandboxData, deriveMatchRange } from '$lib/scenes/sandbox/data';

/**
 * Typed access to Chapter 5's scene artifact:
 *   static/data/scenes/ch5.json — the 2019-final scrub (six verified balls +
 *     win-chance reads) · the 170-189 defended contrast · the two era RE
 *     surfaces + the rise (difference) table · the third-wicket hero pair ·
 *     the outcome price board (linear weights) · the wicket value counterweight ·
 *     the finisher curves · the WPL mask + observed dots + cohort · the
 *     "most valuable ball" payoff variants · the footnote blocks.
 *
 * EVERY on-screen number in C5-1..C5-12 comes through here — never hardcoded
 * (OWNER-LOCKED rule). Where the storyboard's teaser copy and the emitted
 * artifact disagree, the ARTIFACT wins (defended 73.2 → 38.9 on 41/54 matches,
 * not "74/38"; the worm opens at 71.5 in 100, not "~66"; the third wicket at
 * over 7 reads 12.07 → 6.39 on the locked engine surface, not "~12 → ~0.4";
 * the finisher cohort is 17/31 → 35/41; the WPL finisher cohort is 9 of 11).
 * Fetched once per session, cached as a module-level promise, always through
 * `$app/paths` base.
 */

/* ---- era bands (shared convention with ch1..ch4) --------------------------- */

export type BandKey =
	| 'ipl 2008-2010'
	| 'ipl 2011-2015'
	| 'ipl 2016-2019'
	| 'ipl 2020-2022'
	| 'ipl 2023-2026'
	| 'wpl 2023-2026';

export const IPL_EARLY: BandKey = 'ipl 2008-2010';
export const IPL_RECENT: BandKey = 'ipl 2023-2026';
export const WPL_BAND: BandKey = 'wpl 2023-2026';

/** "ipl 2008-2010" → "2008-2010" (era chips / axis labels). */
export const eraYears = (band: string): string => band.replace(/^[a-z]+ /, '');

/* ---- the scrub (C5-2 / C5-3) ----------------------------------------------- */

export interface ScrubWicket {
	kind: string;
	player_out: string;
}

export interface ScrubBall {
	ball: number;
	/** the ball's index in the shared field point order (pipeline-emitted) */
	point_index: number;
	label: string;
	batter: string;
	bowler: string;
	over: number;
	runs_batter: number;
	runs_total: number;
	extras: string | null;
	wicket: ScrubWicket | null;
	needed_before: number;
	balls_left_before: number;
	wickets_in_hand_before: number;
	wp_before: number;
	wp_after: number;
	wpa: number;
	/** raw all-IPL exact-state outcome frequency at the BEFORE state */
	observed: { wins: number; n: number; win_pct: number };
}

export interface ScrubMatch {
	teams: [string, string];
	season: number;
	date: string;
	stage: string;
	venue: string;
	city: string;
	league: string;
	result_text: string;
}

export interface ScrubBlock {
	match_index: number;
	match: ScrubMatch;
	target: number;
	era_surface: string;
	perspective: string;
	worm_note: string;
	entering: {
		score: number;
		wickets_down: number;
		needed: number;
		balls_left: number;
		bowler: string;
	};
	balls: ScrubBall[];
	/** the six field point indices in bowling order (CONTRACT §20: the rail
	 *  lifts THESE — emitted by the pipeline, never client-derived) */
	point_indices: number[];
}

/* ---- HERO 1 — the 170-189 repricing (C5-4) --------------------------------- */

export interface DefendedRaw {
	defended: number;
	n: number;
	pct: number;
}

export interface DefendedBand {
	band: string;
	definition: string;
	raw: Record<BandKey, DefendedRaw>;
	fitted_curve_170_189: Record<string, { n: number; p_batfirst_win: number }>;
	headline: { early_pct: number; recent_pct: number; delta_points: number };
}

/* ---- HERO 2 — the RE surfaces + the rise (C5-5 / C5-6a / C5-6b) ------------- */

export interface ThirdWicketBlock {
	state: string;
	engine_fitted: Record<string, number>;
	raw: Record<
		string,
		{
			re_2_down: number;
			re_3_down: number;
			third_wicket_cost: number;
			n_2_down: number;
			n_3_down: number;
		}
	>;
}

export interface ReDriftBlock {
	era_a: string;
	era_b: string;
	/** 20 rows (over 0..19) × 10 cols (wickets down 0..9), expected runs to come */
	re_a: number[][];
	re_b: number[][];
	diff: number[][];
	n_a: number[][];
	n_b: number[][];
	diff_by_phase: {
		powerplay_overs_1_6: number;
		middle_overs_7_15: number;
		death_overs_16_20: number;
	};
	third_wicket: ThirdWicketBlock;
}

/* ---- the price board (C5-7) ------------------------------------------------- */

export interface LwEntry {
	value: number;
	n: number;
}

export type LwOutcome =
	| 'dot'
	| 'single'
	| 'two'
	| 'three'
	| 'two_or_three'
	| 'four'
	| 'six'
	| 'wide'
	| 'wicket';

export interface LinearWeightsBlock {
	method: string;
	headline: {
		dot: { early: number; recent: number };
		single: { early: number; recent: number };
		six: { early: number; recent: number };
		wicket_event: { early: number; recent: number };
	};
	era_bands: Record<BandKey, Record<LwOutcome, LwEntry>>;
}

export interface PriceBoardSeason {
	season: number;
	league: 'ipl' | 'wpl';
	n_balls: number;
	dot: number;
	single: number;
	two_or_three: number;
	four: number;
	six: number;
	wicket: number;
}

/* ---- the wicket counterweight (C5-8) ---------------------------------------- */

export interface WicketValueBlock {
	method: string;
	headline: { early: number; recent: number; appreciation_pct: number };
	by_band: Record<BandKey, { expected_runs_removed: number; n_wickets: number }>;
	run_rate_context: {
		rr_early: number;
		rr_recent: number;
		run_inflation_pct: number;
		wicket_appreciation_pct: number;
	};
	window_2024_2026: { window: string; expected_runs_removed: number; n_wickets: number };
}

/* ---- the finisher beat (C5-9) ------------------------------------------------ */

export interface FinisherCohort {
	wins: number;
	n: number;
	win_pct: number;
}

export type FinisherBandName = '6-8' | '8-10' | '10-12' | '12+';

export interface FinisherBlock {
	state: string;
	headline: { band: string; early: FinisherCohort; recent: FinisherCohort };
	table: Record<BandKey, Record<FinisherBandName, FinisherCohort>>;
	fatal_rrr: {
		early_10_12_pct: number;
		recent_10_12_pct: number;
		early_12_plus_pct: number;
		recent_12_plus_pct: number;
		note: string;
	};
}

/* ---- the WPL beat (C5-10) ----------------------------------------------------- */

export interface WplBeatBlock {
	/** counted from the corpus by the pipeline — the C5-10 step-1 literals */
	match_counts: { ipl: number; wpl: number; total: number };
	re_surface: number[][];
	re_n: number[][];
	mask: {
		min_n: number;
		cells_masked: number;
		cells_evidenced: number;
		/** [over, wicketsDown] pairs under the evidence threshold */
		masked_cells: [number, number][];
		note: string;
	};
	observed_dots: {
		note: string;
		cells: { o: number; w: number; n: number; mean: number; observed_runs_to_come: number[] }[];
	};
	finisher_8_10: { wins: number; n: number; win_pct: number; note: string };
	defended_170_189: { defended: number; n: number; pct: number };
}

/* ---- the payoff (C5-11) -------------------------------------------------------- */

export interface PayoffBall {
	label: string;
	batter: string;
	bowler: string;
	runs_batter: number;
	runs_total: number;
	extras: string | null;
	wicket: ScrubWicket | null;
	needed_before: number | null;
	balls_left_before: number | null;
	swing_team: number;
	wp_team_before: number;
	wp_team_after: number;
}

export interface PayoffMoment {
	batter: string;
	bowler: string;
	batting: boolean;
	date: string;
	season: number;
	stage: string;
	opponent: string;
	venue: string;
	innings: number;
	label: string;
	match_index: number;
	/** field point order index — drives the C5-11 single-point ignite */
	point_index: number;
	/** restate.u8 cell (over×10 + wicketsDown) — the ignite's grid anchor */
	state_cell: number;
	what_happened: string;
	swing: number;
	result_text: string;
	wicket: ScrubWicket | null;
}

export interface PayoffVariant {
	team_id: number;
	team: string;
	league: 'ipl' | 'wpl';
	active: boolean;
	empty_state: boolean;
	short_history?: boolean;
	honesty: string;
	most_valuable: PayoffMoment;
	runners_up: PayoffMoment[];
	replay: { innings: number; over: number; balls: PayoffBall[] };
}

export interface TopSwing {
	batter: string;
	bowler: string;
	league: string;
	season: number;
	stage: string;
	teams: [string, string];
	label: string;
	match_index: number;
	point_index: number;
	state_cell: number;
	what_happened: string;
	result_text: string;
	/** signed, batting-team perspective — display the MAGNITUDE (a bowling
	 *  side's biggest ball carries a negative batting-side wpa) */
	wpa: number;
}

/* ---- footnote blocks ------------------------------------------------------------ */

export interface Ch5Footnotes {
	chase_difficulty: {
		definition: string;
		by_band: Record<BandKey, FinisherCohort>;
	};
	era_swap: {
		batter: string;
		runs: number;
		balls_faced: number;
		target: number;
		chase_start_wp_2008_2010: number;
		chase_start_wp_2023_2026: number;
		note: string;
	};
	smoothing: { note: string; wp_grid_calibration_ece: number };
	crediting: string;
	tie_rule: string;
}

/* ---- top level -------------------------------------------------------------------- */

export interface Ch5Data {
	chapter: number;
	title: string;
	register: string;
	scrub: ScrubBlock;
	defended_band: DefendedBand;
	re_drift: ReDriftBlock;
	linear_weights: LinearWeightsBlock;
	price_board: { note: string; seasons: PriceBoardSeason[] };
	wicket_value: WicketValueBlock;
	finisher: FinisherBlock;
	wpl_beat: WplBeatBlock;
	wpa: {
		perspective: string;
		swinginess_note: string;
		top_swings: TopSwing[];
		/** one ball per (league, season) — the neutral payoff gallery */
		season_gallery: TopSwing[];
		per_band: Record<BandKey, { mean_abs_wpa: number; n: number }>;
		coverage: {
			balls_scored: number;
			balls_sentinel: number;
			sentinel_matches: { dl: number; no_result_or_undecided: number; short_target: number };
		};
	};
	payoff: { note: string; min_swing_considered: number; variants: PayoffVariant[] };
	footnotes: Ch5Footnotes;
}

/* ---- loader (cached; base-path aware) ------------------------------------------- */

let ch5Promise: Promise<Ch5Data> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

export function loadCh5Data(): Promise<Ch5Data> {
	ch5Promise ??= fetchJson<Ch5Data>('/data/scenes/ch5.json');
	return ch5Promise;
}

/* ---- formatters -------------------------------------------------------------------- */

/** A win read as "N in 100" (the interlude's lock): 0.715 → 72. */
export const win100 = (p: number): number => Math.round(p * 100);
/** A signed swing chip: +18 / −25 (in 100); 0 → "0". */
export const swing100 = (wpa: number): string => {
	const v = Math.round(wpa * 100);
	return v > 0 ? `+${v}` : String(v);
};
/** One decimal ("1.1", "4.6"). */
export const fmt1 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
/** Two decimals ("0.25"). */
export const fmt2 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
/** Magnitude of a price, one decimal, no sign ("0.9" from −0.898). */
export const mag1 = (n: number): string => fmt1(Math.abs(n));
/** Whole runs ("110", "130"). */
export const runs = (n: number): string => Math.round(n).toLocaleString('en-US');
/** Integer with thousands separators. */
export const int = (n: number): string => Math.round(n).toLocaleString('en-US');
/** A rate like 73.2 shown as its "out of 100" integer (73). */
export const in100 = (pct: number): number => Math.round(pct);

/* ---- the over rail: slots + point-index cache (C5-2 / C5-3) ----------------------- */

/**
 * The six rail slots as VIEWPORT FRACTIONS (CONTRACT §20): a single row across
 * the upper-middle, left → right in bowling order. The scene's DOM chips anchor
 * at the same fractions, so chip and GL ball agree by construction.
 */
export const RAIL_Y = 0.44;
export const RAIL_SLOTS: readonly (readonly [number, number])[] = Array.from(
	{ length: 6 },
	(_, i) => [0.125 + (i * 0.75) / 5, RAIL_Y] as const
);

/** Set-piece rest-of-field dim (alpha dims saturate — stay ≤ ~0.1, CONTRACT §20). */
export const RAIL_DIM = 0.05;

/**
 * The six field point indices of the scrub over (match 755, innings 2, over 20).
 * PIPELINE-EMITTED in scenes/ch5.json (CONTRACT §20: "a tiny index set from
 * scenes/ch5.json, never client-derived") and cached module-level; the SceneDef
 * dynamicState reads this cache so a stray scroll can never desync the rail
 * (ch4's tideParLevels pattern). The old columnar derivation survives only as
 * a DEV-time cross-check — the 655KB gz sandbox corpus is no longer fetched at
 * C5-2 entry (design audit: the parse landed mid set piece on mobile, and a
 * failed fetch left the GL lift dead under a caption asserting it).
 */
let railIdx: number[] | null = null;
export function railIndices(): number[] | null {
	return railIdx;
}

let railChecked = false;
export function setRailIndices(d: Ch5Data): number[] {
	railIdx ??= [...d.scrub.point_indices];
	if (import.meta.env.DEV && !railChecked) {
		railChecked = true;
		void loadSandboxData()
			.then((sb) => {
				const a = sb.columnar.arrays;
				const range = deriveMatchRange(sb.columnar, d.scrub.match_index);
				const found: { idx: number; ball: number }[] = [];
				if (range) {
					for (let i = range[0]; i < range[1]; i++) {
						if (a.innings[i] === 2 && a.over[i] === 19) {
							found.push({ idx: i, ball: a.ball_index_in_over[i] });
						}
					}
				}
				found.sort((x, y) => x.ball - y.ball);
				const derived = found.map((f) => f.idx);
				if (JSON.stringify(derived) !== JSON.stringify(railIdx)) {
					console.warn(
						'[every-ball-ever] ch5 rail indices: emitted set diverges from the columnar derivation',
						{ emitted: railIdx, derived }
					);
				}
			})
			.catch(() => {});
	}
	return railIdx;
}

/* ---- the scrub pointer (shared by index.ts dynamicState + OverScrub) --------------- */

/**
 * How many balls have fully played at `progress`, as a float 0..6.
 *
 * `gapAligned` (mobile read-then-watch, CONTRACT §17.6): the delivery must
 * play in the caption step's CLEAR GAP, not under the caption. Each ball's
 * step spans one sixth of the scrub window; aligned, the pointer HOLDS the
 * previous ball through the read beat (the first ~60% of the step, matching
 * captionReveal's readHold) and draws the segment across the fade + gap tail.
 * Desktop / reduced motion pass false (byte-identical behaviour).
 */
export function scrubBallFloat(progress: number, gapAligned = false): number {
	const t = (progress - 0.06) / (0.82 - 0.06);
	const f = Math.min(6, Math.max(0, t * 6));
	if (!gapAligned || f >= 6) return f;
	const full = Math.floor(f);
	const u = f - full;
	const READ = 0.6; // captionReveal's default readHold
	return full + (u < READ ? 0 : (u - READ) / (1 - READ));
}

/** The C5-3 caption step: 1..6 = that ball's beat, 7 = the end beat. */
export function scrubStep(progress: number): number {
	if (progress >= 0.88) return 7;
	return Math.min(6, Math.floor(scrubBallFloat(progress)) + 1);
}

/** Caption-step BOUNDS for the read-then-watch reveal (CONTRACT §17.4). */
export const SCRUB_BOUNDS: readonly number[] = (() => {
	const b: number[] = [0];
	for (let k = 1; k <= 6; k++) b.push(0.06 + ((0.82 - 0.06) * k) / 6);
	b[6] = 0.88; // step 6 runs to the end beat's threshold
	b.push(1);
	return b;
})();

/* ---- the worth-grid price tables (C5-5 onward) -------------------------------------- */

export interface WorthTables {
	early: Float32Array;
	recent: Float32Array;
	rise: Float32Array;
	wpl: Float32Array;
	/** the shared price scale (max runs across early/recent/wpl surfaces) */
	priceMax: number;
	/** the rise lens's own scale (max positive per-cell rise) */
	riseMax: number;
}

/**
 * The masked WPL cells' flat NEUTRAL luminance: deliberately not a price and
 * not a dimness (hatched is never dim — a thin cell must never read as a
 * cheap one). Uniform across every masked cell, so no gradient under the
 * hatch can be misread as a fitted surface (storyboard C5-10: "the map
 * deliberately shows nothing rather than a fake fitted surface").
 */
export const WPL_MASK_NEUTRAL = 0.42;

/**
 * Normalize the raw engine runs into 0..1 luminance tables (cell = over×10 +
 * wicketsDown, the restate.u8 convention). Editorial scale choices (storyboard
 * §0.1): the two era maps + the WPL share ONE scale so the flip is honest; the
 * rise lens has its own, and negative cells (spots that fell) clamp to 0 — the
 * fallen cells are disclosed in the ch5-drift footnote, never silently brightened.
 * WPL HONESTY (design audit): the engine's wpl surface carries smoothed values
 * under the 155 masked cells; those cells are (a) excluded from the shared
 * price scale and (b) overwritten with the flat WPL_MASK_NEUTRAL, so the only
 * WPL prices painted are the evidenced ones — the hatch and the observed marks
 * (WplBeat's annotation plane) carry the masked cells' meaning.
 */
export function buildWorthTables(d: Ch5Data): WorthTables {
	const flat = (rows: number[][]): Float32Array => {
		const out = new Float32Array(200);
		for (let o = 0; o < 20; o++)
			for (let w = 0; w < 10; w++) out[o * 10 + w] = rows[o]?.[w] ?? 0;
		return out;
	};
	const early = flat(d.re_drift.re_a);
	const recent = flat(d.re_drift.re_b);
	const wpl = flat(d.wpl_beat.re_surface);
	const rise = flat(d.re_drift.diff);
	const masked = new Set(d.wpl_beat.mask.masked_cells.map(([o, w]) => o * 10 + w));
	let priceMax = 1;
	for (let i = 0; i < 200; i++) {
		priceMax = Math.max(priceMax, early[i], recent[i]);
		if (!masked.has(i)) priceMax = Math.max(priceMax, wpl[i]);
	}
	let riseMax = 1;
	for (let i = 0; i < 200; i++) riseMax = Math.max(riseMax, rise[i]);
	const norm = (t: Float32Array, m: number): Float32Array => {
		const out = new Float32Array(200);
		for (let i = 0; i < 200; i++) out[i] = Math.max(0, t[i]) / m;
		return out;
	};
	const wplLum = norm(wpl, priceMax);
	for (const i of masked) wplLum[i] = WPL_MASK_NEUTRAL;
	return {
		early: norm(early, priceMax),
		recent: norm(recent, priceMax),
		rise: norm(rise, riseMax),
		wpl: wplLum,
		priceMax,
		riseMax
	};
}

/** Expected runs to come at (over 0-idx, wicketsDown) for a drift surface. */
export function reAt(rows: number[][], over: number, wkts: number): number {
	return rows[over]?.[wkts] ?? 0;
}

/* ---- the era flip + the rise lens (C5-6a), shared scrub math ------------------------- */

const clamp01 = (t: number): number => Math.min(1, Math.max(0, t));

export interface FlipState {
	/** 1 = the early map (worked example) · 2 = the flip to recent · 3 = the rise lens */
	stage: 1 | 2 | 3;
	lens: { from: string; table: string; mix: number };
	/** the dip-to-dark re-light rides the scene dim (storyboard C5-6a) */
	dim: number;
}

/**
 * The C5-6a color-state scrub as a PURE function of scroll progress, shared by
 * index.ts's dynamicState and the EraFlip component so the field recolor and
 * the on-screen era chip / legend can never disagree (ch4's waterlineScrub
 * pattern). Stages: hold the early map → lerp early→recent → dip to near-black
 * and re-light under the rise table. The scene's very end swaps the pair to
 * (rise → recent, mix 0) — pixel-identical to the settled rise — so C5-6b's
 * entry can release the lens by ramping mix (CONTRACT §19.3 cross-table rule).
 *
 * `gapAligned` (mobile read-then-watch, CONTRACT §17.6): the flip and the
 * lens must advance in the caption steps' CLEAR GAPS, not under the read
 * beats. Aligned, the era lerp runs across step 2's fade + gap tail
 * (p 0.53 → 0.585), the dip rides the step-2→3 boundary gap, and the rise
 * re-lights as step 3's caption fades in — so the read beats always narrate
 * a settled map. STAGE thresholds never move (they are the caption BOUNDS).
 * Desktop / reduced motion pass false (byte-identical behaviour).
 */
export function eraFlipState(progress: number, gapAligned = false): FlipState {
	const stage: 1 | 2 | 3 = progress < 0.38 ? 1 : progress < 0.62 ? 2 : 3;
	if (progress >= 0.985) {
		// the held hand-off state: renders pure rise, pair pre-swapped for C5-6b
		return { stage: 3, lens: { from: 'rise', table: 'recent', mix: 0 }, dim: 1 };
	}
	if (!gapAligned) {
		if (progress < 0.62) {
			const mix = clamp01((progress - 0.38) / (0.54 - 0.38));
			return { stage, lens: { from: 'early', table: 'recent', mix }, dim: 1 };
		}
		// the dip-to-dark re-light: dim dives, the rise table fades in, dim recovers
		let dim = 1;
		if (progress < 0.66) dim = 1 - ((progress - 0.62) / 0.04) * 0.85;
		else if (progress < 0.74) dim = 0.15 + ((progress - 0.66) / 0.08) * 0.85;
		const mix = clamp01((progress - 0.65) / (0.76 - 0.65));
		return { stage, lens: { from: 'recent', table: 'rise', mix }, dim };
	}
	// gap-aligned (mobile): flip in step 2's tail, dip across the boundary,
	// re-light under the rise as step 3 opens
	if (progress < 0.585) {
		const mix = clamp01((progress - 0.53) / (0.585 - 0.53));
		return { stage, lens: { from: 'early', table: 'recent', mix }, dim: 1 };
	}
	let dim = 1;
	if (progress < 0.62) dim = 1 - ((progress - 0.585) / 0.035) * 0.85;
	else if (progress < 0.7) dim = 0.15 + ((progress - 0.62) / 0.08) * 0.85;
	const mix = clamp01((progress - 0.61) / (0.7 - 0.61));
	return { stage, lens: { from: 'recent', table: 'rise', mix }, dim };
}

/* ---- the finisher cliff (data-derived, C5-9) ----------------------------------------- */

export const FINISHER_BANDS: readonly FinisherBandName[] = ['6-8', '8-10', '10-12', '12+'];

/** Numeric lower edge of a band ("10-12" → 10, "12+" → 12). */
export const bandLo = (b: FinisherBandName): number => parseInt(b, 10);

/**
 * The fatal rate ("the cliff"): the lower edge of the first band where fewer
 * than half of such chases came off. Early era → 10, recent era → 12 on the
 * shipped table (data-derived, never hardcoded).
 */
export function fatalRate(table: Record<FinisherBandName, FinisherCohort>): number {
	for (const b of FINISHER_BANDS) {
		if (table[b].win_pct < 50) return bandLo(b);
	}
	return bandLo(FINISHER_BANDS[FINISHER_BANDS.length - 1]);
}

/* ---- payoff resolution (mirrors ch3/ch4's variant contract) --------------------------- */

export interface TeamPickLite {
	league: 'ipl' | 'wpl' | null;
	team: string;
}

export interface ResolvedMvb {
	variant: PayoffVariant | null;
	kind: 'ipl' | 'wpl' | 'neutral';
	fallback: boolean;
}

/**
 * Resolve a reader's pick to their "most valuable ball" card. Neutral / unknown
 * picks get the league-wide card (built from wpa.top_swings — deep links always
 * work; no variant is required to exist).
 */
export function mvbVariantFor(d: Ch5Data, pick: TeamPickLite | null): ResolvedMvb {
	if (pick === null || pick.league === null || pick.team === 'neutral') {
		return { variant: null, kind: 'neutral', fallback: false };
	}
	const exact = d.payoff.variants.find((v) => v.league === pick.league && v.team === pick.team);
	if (exact) return { variant: exact, kind: exact.league, fallback: false };
	return { variant: null, kind: 'neutral', fallback: true };
}

/* ---- the C5-11 single-point ignite (module cache, ch4's tideParLevels pattern) ------ */

export interface MvbIgnite {
	/** the most-valuable ball's field point index (pipeline-emitted) */
	index: number;
	/** its own worth-grid cell centre as viewport fractions — the §20 rail
	 *  slot, so the ignite enlarges the ball essentially in place */
	slot: readonly [number, number];
}

/**
 * Set by MostValuable (which knows the reader's resolved variant and the
 * projected worth-grid geometry), read by the ch5-payoff SceneDef's
 * dynamicState — the storyboard's "the one ball itself ignites" beat, riding
 * the existing §20 overrail capability (indices + slots + progress; dimRest 1
 * leaves the rest of the field at the scene dim). null = no ignite (data not
 * ready, or reduced motion, where the static card carries the whole beat).
 */
let mvbIgnite: MvbIgnite | null = null;
export function mvbIgniteState(): MvbIgnite | null {
	return mvbIgnite;
}
export function setMvbIgnite(v: MvbIgnite | null): void {
	mvbIgnite = v;
}
