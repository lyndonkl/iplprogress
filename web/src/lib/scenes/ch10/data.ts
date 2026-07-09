import { base } from '$app/paths';

/**
 * Typed access to Chapter 10's scene artifact:
 *   static/data/scenes/ch10.json, THE ERA MACHINE (the FINALE). The chronological
 *     ribbon (the controlling morph, free -> ribbon, a pure function of position.x
 *     so the field stays at 14 attributes), the league-pulse seismograph and its
 *     scene-drawn fault-line cracks + strictness dial (a precomputed lookup, never
 *     a live re-fit), the fault-map subway, the bridge-player verdict that closes
 *     the 2023 mystery, the two-machine Player Teleporter, the convergence clock,
 *     the 2021 venue-leg micro-era, and the 16-variant "your adapters" payoff.
 *
 * EVERY on-screen number in C10-1..C10-9 comes through here, never hardcoded
 * (OWNER-LOCKED; the ARTIFACT wins over the storyboard's teaser copy). Six honest
 * deltas ship straight, never fudged toward a teaser: sixes broke 2014 THEN 2018
 * (not one clean 2018), about two-thirds of the 2023-24 jump was new personnel
 * (not three-quarters), the naive teleport ceiling is about 224 (not 228), "how
 * far above his own era" ships as a percent-above-par gap and NEVER a z-score, and
 * the WPL six-hitting is owned as off the clock (never "behind").
 *
 * Fetched once per session, cached as a module-level promise, always through
 * `$app/paths` base.
 */

/* ---- the ribbon (the controlling morph) ---------------------------------- */

export interface TimeTick {
	season: number;
	/** point index on the full 316,199-ball ribbon (feed to getRibbonLayout().pointToX) */
	ball_pos: number;
	/** fraction along the ribbon 0..1 */
	ribbon_frac: number;
}

export interface RibbonBlock {
	total_points: number;
	n_matches_ipl: number;
	legal_deliveries_ipl: number;
	seasons: number[];
	per_season_matches: number[];
	cum_deliv_start: number[];
	time_axis_ticks: TimeTick[];
	legend: string;
	note: string;
}

/* ---- the seismograph (the hero: cracks + strictness dial) ----------------- */

export type MetricKey =
	| 'six_rate'
	| 'run_rate'
	| 'rpo'
	| 'wide_rate'
	| 'dot_rate'
	| 'boundary_rate';

export interface Crack {
	/** point index on the ribbon (feed to getRibbonLayout().pointToX) */
	ball_pos: number;
	ribbon_frac: number;
	posterior: number;
	year: number;
	metric?: MetricKey;
	season_frac?: number;
}

export interface Fault {
	metric: MetricKey;
	year: number;
	posterior: number;
}

export interface StrictnessStop {
	/** the segmentation penalty (fan name: "how big a change counts as a new era") */
	beta: number;
	/** the number of eras (tinted regions) at this stop */
	n_eras: number;
	/** the break years standing at this stop */
	break_years: number[];
	/** the cracks to draw at this stop (one per break year) */
	cracks: Crack[];
}

export interface Strictness {
	label: string;
	composite_series: number[];
	stops: StrictnessStop[];
	default_beta: number;
	default_n_eras: number;
	endpoints_note: string;
	strongest_fault: Fault;
}

export interface Seismograph {
	seasons: number[];
	series: Record<MetricKey, number[]>;
	labels: Record<MetricKey, string>;
	record: { matches: number; legal_deliveries: number };
	posterior_range: [number, number];
	strongest_faults: Fault[];
	cracks: Crack[];
	strictness: Strictness;
	bayes_posterior: Record<string, { break_year: number; posterior: number }[]>;
	penalty_sweep_note: string;
}

/* ---- the fault map (the subway of change) --------------------------------- */

export interface Station {
	year: number;
	ball_pos: number;
	ribbon_frac: number;
	posterior: number;
}

export interface FaultLine {
	key: MetricKey;
	label: string;
	primary: number;
	stations: Station[];
	per_match_extra?: number[];
}

export interface Interchange {
	year: number;
	metrics: MetricKey[];
	label: string;
}

export interface OrderGap {
	six_year: number;
	scoring_year: number;
	years: number;
	alt_six_year: number;
	alt_years: number;
	note: string;
}

export interface FaultMap {
	seasons: number[];
	metrics: FaultLine[];
	hero_lines: MetricKey[];
	interchanges: Interchange[];
	order_gap: OrderGap;
}

/* ---- the bridge-player verdict (the 2023 mystery, closed) ----------------- */

export interface VerdictPanel {
	type: string;
	chapter: number;
	text: string;
	number?: string;
}

export interface ShiftShare {
	total: number;
	within: number;
	within_pct: number;
	turnover: number;
	turnover_pct: number;
	components: { usage: number; entrants: number; leavers: number };
	stayers: number;
	entrants_n: number;
	leavers_n: number;
}

export interface Bridge {
	league_sr_2023: number;
	league_sr_2024: number;
	jump: number;
	n_bridge: number;
	bridge_min_balls: number;
	within_mean: number;
	within_pooled: number;
	shift_share: ShiftShare;
	turnover_range: string;
	verdict: { headline: string; panels: VerdictPanel[]; note: string };
}

/* ---- the Player Teleporter (two hard-separated machines) ------------------ */

export interface Translation {
	year: number;
	naive: number;
	honest: number;
	band_lo: number;
	band_hi: number;
	band_halfwidth: number;
	gap: number;
	band_lt_gap: boolean;
}

export interface TeleportPlayer {
	name: string;
	season: number;
	balls: number;
	runs: number;
	sr: number;
	league_sr_season: number;
	percentile: number;
	srplus: number;
	naive_ceiling: number;
	translations: Translation[];
}

export interface MachineA {
	/** the strike-rate axis anchor (the player's real number, e.g. 185) */
	anchor_sr: number;
	default: TeleportPlayer;
	integrity: { check_year: number; band_halfwidth: number; gap: number; band_lt_gap: boolean };
	note: string;
}

export interface EraPlayer {
	name: string;
	season: number;
	sr: number;
	srplus: number;
	/** "how far above the going rate of his own year" (percent, NEVER a z-score) */
	pct_above_par: number;
}

export interface MachineB {
	players: EraPlayer[];
	raw_sr_gap: number;
	verdict: string;
	unit: string;
}

export interface Teleporter {
	machine_a: MachineA;
	machine_b: MachineB;
}

/* ---- the convergence clock (point the machine forward) -------------------- */

export interface MensConvergence {
	series: { seasons: number[]; rpo: number[] };
	recent: { seasons: number[]; rpo: number[] };
	fit_window: [number, number];
	slope: number;
	slope_se: number;
	crosses_ten: { central: number; band_lo: number; band_hi: number; band_years: [number, number] };
	today: { season: number; rpo: number };
	target: number;
}

export interface WplRunRate {
	seasons: number[];
	rpo: number[];
	slope: number;
	slope_se: number;
	reaches_mens_2026_level: number;
	mens_2026_level: number;
}

export interface WplSixRate {
	seasons: number[];
	six_per_over: number[];
	slope: number;
	slope_se: number;
	off_the_clock: boolean;
	reaches_mens_2026_level: number;
	mens_2026_level: number;
}

export interface Convergence {
	mens: MensConvergence;
	wpl: { run_rate: WplRunRate; six_rate: WplSixRate };
	framing: string;
	wpl_framing: string;
}

/* ---- the 2021 venue-leg micro-era (a footnote exhibit) -------------------- */

export interface MicroEra {
	year: number;
	india: { rr: number; runs: number; legal_balls: number };
	uae: { rr: number; runs: number; legal_balls: number };
	note: string;
}

/* ---- the payoff (your adapters, 16 variants) ------------------------------ */

export interface PayoffRiser {
	name: string;
	rise: number;
	season_from: number;
	season_to: number;
	sr_from: number;
	sr_to: number;
}

export interface PayoffLegend {
	name: string;
	season: number;
	sr: number;
	honest_2026: number;
	naive_2026: number;
	translations: Translation[];
}

export interface PayoffClimb {
	team_rate: number;
	league_rate: number;
	position: string;
}

export interface PayoffVariant {
	team: string;
	team_id: number | null;
	short: string;
	league: 'ipl' | 'wpl' | 'neutral';
	empty_state: boolean;
	headline: string;
	row1: string;
	row2: string;
	row3: string;
	/* IPL */
	riser?: PayoffRiser;
	legend?: PayoffLegend;
	climb?: PayoffClimb;
	/* WPL bespoke */
	bespoke?: boolean;
	forming_fast?: boolean;
	/* neutral */
	sehwag_honest_2026?: number;
}

export interface PayoffBlock {
	card: string;
	definition: string;
	variants: PayoffVariant[];
}

/* ---- footnotes + controlling morph + top level ---------------------------- */

export interface Ch10Footnote {
	text: string;
}

export interface ControllingMorph {
	name: string;
	layout_code: number;
	new_buffer: string | null;
	reverse: string;
	teleport_bit: number;
	note: string;
}

export interface Ch10Data {
	chapter: number;
	title: string;
	register: string;
	finale: boolean;
	mystery_handoff_in: string;
	controlling_morph: ControllingMorph;
	ribbon: RibbonBlock;
	seismograph: Seismograph;
	fault_map: FaultMap;
	bridge: Bridge;
	teleporter: Teleporter;
	convergence: Convergence;
	micro_era_2021: MicroEra;
	payoff: PayoffBlock;
	footnotes: Record<string, Ch10Footnote>;
}

/* ---- loader (cached; base-path aware) ------------------------------------- */

let ch10Promise: Promise<Ch10Data> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

export function loadCh10Data(): Promise<Ch10Data> {
	ch10Promise ??= fetchJson<Ch10Data>('/data/scenes/ch10.json');
	return ch10Promise;
}

/* ---- strictness-dial helpers (the precomputed lookup, never a re-fit) ------ */

/** The default dial stop (beta 0.6 = 4 eras = the middle still, storyboard C10-3). */
export function defaultStopIndex(d: Ch10Data): number {
	const stops = d.seismograph.strictness.stops;
	const target = d.seismograph.strictness.default_n_eras;
	const i = stops.findIndex((s) => s.n_eras === target);
	return i >= 0 ? i : Math.min(1, stops.length - 1);
}

/**
 * The era-bands (the tinted regions BETWEEN cracks) for a strictness stop, as
 * fraction pairs [lo, hi] along the ribbon (0..1). N cracks -> N+1 bands, so the
 * merge is a literal region fuse as the count drops (cognitive-design #3).
 */
export function eraBands(stop: StrictnessStop): { lo: number; hi: number }[] {
	const cuts = stop.cracks.map((c) => c.ribbon_frac).slice().sort((a, b) => a - b);
	const edges = [0, ...cuts, 1];
	const bands: { lo: number; hi: number }[] = [];
	for (let i = 0; i < edges.length - 1; i++) bands.push({ lo: edges[i], hi: edges[i + 1] });
	return bands;
}

/** A crack is drawn SOLID+full when we are surer of it, DASHED+short when less. */
export const SURE_POSTERIOR = 0.3;
export function isSureCrack(posterior: number): boolean {
	return posterior >= SURE_POSTERIOR;
}

/**
 * Map a crack's posterior (how sure we are, 0.15..0.44) to a glow opacity. Kept
 * honestly faint: a modest posterior stays modest on the certainty channel, and
 * legibility is carried on a SEPARATE always-visible locator stroke, never by
 * brightening a faint break (fallacies-guard honest-encoding gate).
 */
export function crackGlow(posterior: number, range: [number, number]): number {
	const [lo, hi] = range;
	const t = hi > lo ? (posterior - lo) / (hi - lo) : 0.5;
	return 0.14 + 0.34 * Math.min(1, Math.max(0, t));
}

/* ---- sparkline / polyline path builders (2D exhibits) --------------------- */

/**
 * A polyline path over an array of values mapped into a [x0,x1] x [y0,y1] box,
 * with y inverted (SVG y grows downward) against an explicit value domain.
 */
export function linePath(
	values: number[],
	x0: number,
	x1: number,
	y0: number,
	y1: number,
	vlo: number,
	vhi: number
): string {
	const n = values.length;
	if (n === 0) return '';
	const span = vhi - vlo || 1;
	return values
		.map((v, i) => {
			const x = n === 1 ? x0 : x0 + ((x1 - x0) * i) / (n - 1);
			const y = y1 - ((y1 - y0) * (v - vlo)) / span;
			return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
		})
		.join(' ');
}

/** The x for a season on an EQUAL-SPACED year axis (the fault map / convergence). */
export function yearX(year: number, years: number[], x0: number, x1: number): number {
	const first = years[0];
	const last = years[years.length - 1];
	const span = last - first || 1;
	return x0 + ((x1 - x0) * (year - first)) / span;
}

/* ---- payoff resolution (mirrors the ch7 / ch8 / ch9 variant contract) ----- */

export interface TeamPickLite {
	league: 'ipl' | 'wpl' | null;
	team: string;
}

export interface ResolvedPayoff {
	variant: PayoffVariant | null;
	kind: 'ipl' | 'wpl' | 'neutral';
	/** true when the pick had no exact variant and we fell back to neutral */
	fallback: boolean;
}

/**
 * Resolve a reader's pick to their "your adapters" card. Neutral / unknown picks
 * get the neutral variant (deep links always work). Matching is by (league, team
 * name); the WPL and IPL share franchise names, so the league is load-bearing.
 */
export function payoffVariantFor(d: Ch10Data, pick: TeamPickLite | null): ResolvedPayoff {
	const neutral = d.payoff.variants.find((v) => v.league === 'neutral') ?? null;
	if (pick === null || pick.league === null || pick.team === 'neutral') {
		return { variant: neutral, kind: 'neutral', fallback: false };
	}
	const exact = d.payoff.variants.find((v) => v.league === pick.league && v.team === pick.team);
	if (exact) return { variant: exact, kind: exact.league, fallback: false };
	return { variant: neutral, kind: 'neutral', fallback: true };
}

/* ---- formatters ----------------------------------------------------------- */

/** Integer with thousands separators ("316,199"). */
export const int = (n: number): string => Math.round(n).toLocaleString('en-US');
/** One decimal ("213.6"), the strike-rate / run-rate reads. */
export const fmt1 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
/** Two decimals ("184.55"). */
export const fmt2 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
/** A whole percent ("57"). */
export const pct0 = (n: number): string => `${Math.round(n)}`;
/** A signed one-decimal delta ("+8.9"). */
export const signed1 = (n: number): string => `${n >= 0 ? '+' : ''}${fmt1(n)}`;
