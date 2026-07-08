import { base } from '$app/paths';
import type { FieldHandle, MatchTable, ReviewInput } from '$lib/field/field';

/**
 * Typed access to Chapter 8's scene artifact:
 *   static/data/scenes/ch8.json, THE BELIEF AUDIT. The 1,331 match-dots table
 *     (the controlling morph), the toss revolution + belief-reality crossover, the
 *     988 review chips, the spell mosaics + cold-return tax, the momentum audit
 *     (needle vs shuffled cricket), the required-rate flip, the WPL doctrine
 *     transmission, and the 16-variant "your captains' report card" payoff.
 *
 * EVERY on-screen number in C8-1..C8-10 comes through here, never hardcoded
 * (OWNER-LOCKED rule; the ARTIFACT wins over the storyboard's teaser copy, and
 * three honest deltas ship straight: the review success rate DEGRADED, the
 * cold-return tax GREW, and momentum is a FAIL with an honest ~1.07 residual).
 *
 * The match-dots table is fed VERBATIM to the field (field.setMatchTable) after a
 * [0,1] → [-1,1] remap (the pipeline emits normalized [0,1] centroids; the field's
 * shader convention is [-1,1]). The 988 review deliveries feed field.setReviews.
 * Fetched once per session, cached as a module-level promise, always through
 * `$app/paths` base.
 */

/* ---- report card (the chapter's spine: four fails, one pass) -------------- */

export type Grade = 'fail' | 'pass';

export interface Belief {
	slot: number;
	name: string;
	grade: Grade;
	note?: string;
}

export interface ReportCard {
	shape: string;
	beliefs: Belief[];
}

/* ---- the controlling morph (1,331 match-dots) ----------------------------- */

export interface ControllingMorph {
	name: string;
	note: string;
	reuses_buffer: string;
}

export interface MatchDots {
	count: number;
	n_points: number;
	ipl_matches: number;
	wpl_matches: number;
	/** [x, y, toss_class, result] × count, x,y normalized [0,1]; toss 0=bat-first/1=field-first; result 1=chase won/0=bat-first won/-1=undecided */
	centroids: number[][];
	/** per-match block-start point index (monotone), length count */
	bounds: number[];
	season: number[];
	league: number[];
	/** [season, x_norm] label ticks along the time axis */
	axis_ticks: [number, number][];
	date_range: [string, string];
	encoding: string;
}

/* ---- belief 1: the toss revolution (FAIL) --------------------------------- */

export interface TossEra {
	era: string;
	n: number;
	decided: number;
	field_first: number;
	chase_win: number;
	tosswin_matchwin: number;
}

export interface Crossover {
	/** [x_norm, pct] × 5, how often captains chose to field */
	field_first_line: [number, number][];
	/** [x_norm, pct] × 5, how often the chase actually won */
	chase_win_line: [number, number][];
	crossing_point: { x: number; pct: number; between: [string, string] };
	y_domain: [number, number];
	y_observed: [number, number];
	x_is_normalized_date: boolean;
	note: string;
}

export interface CaptainSimRow {
	season: number;
	actual_field_first: number;
	/** what a captain following the trailing chase-win trend would have chosen; null in year one */
	trailing_chase_win: number | null;
}

export interface Toss {
	grade: Grade;
	eras: TossEra[];
	per_season_field_first: Record<string, number>;
	crossover: Crossover;
	captain_sim: CaptainSimRow[];
	headline: {
		field_first_start: number;
		field_first_end: number;
		field_first_2026: number;
		chase_win_start: number;
		chase_win_hump: number;
		chase_win_end: number;
		text: string;
	};
	wrinkle: string;
	definition: string;
}

/* ---- belief 2: the review economics (FAIL) -------------------------------- */

export interface ReviewTeam {
	team: string;
	team_id: number;
	short: string;
	reviews: number;
	upheld: number;
	struck: number;
	upheld_pct: number;
	rank?: number;
}

export interface ReviewWindow {
	seasons: [number, number];
	reviews: number;
	upheld: number;
	per_match: number;
	upheld_pct: number;
}

export interface Review {
	grade: Grade;
	total: number;
	upheld: number;
	upheld_pct: number;
	windows: { pre: ReviewWindow; post: ReviewWindow; volume_ratio_per_match: number };
	per_season: Record<
		string,
		{ reviews: number; upheld: number; upheld_pct: number; per_match: number; matches: number }
	>;
	per_team: ReviewTeam[];
	leaderboard: ReviewTeam[];
	schema: { decisions: string[]; umpires_call_present?: number; type_present?: number; note: string };
	headline: { per_match_pre: number; per_match_post: number; text: string };
	honesty: string;
}

export interface ReviewSubsetData {
	count: number;
	/** the 988 review-delivery point indices (ascending) */
	indices: number[];
	/** each review's IPL franchise team_id (or -1 unknown) */
	team: number[];
	/** each review's outcome: 0 struck down (the call stood) / 1 upheld (paid off) */
	outcome: number[];
	unknown_team: number;
	encoding: string;
}

/* ---- belief 3: spell fragmentation + the cold-return tax (FAIL) ----------- */

export interface SpellExemplar {
	match_index: number;
	innings: number;
	season: number;
	batting_team: string;
	bowling_team: string;
	n_overs: number;
	one_over_share: number;
	n_spells: number;
	n_one_over: number;
	/** per over, the bowler slot that bowled it (index into bowler_names) */
	over_bowler: number[];
	bowler_names: string[];
	/** the fused bars: each a bowler's unbroken same-end run */
	spells: { slot: number; end: number; start_over: number; len: number }[];
}

export interface Spell {
	grade: Grade;
	per_era: Record<string, { one_over_share: number; spells: number }>;
	wpl: { one_over_share: number; spells: number };
	per_season: Record<string, number>;
	ipl_span: { start: number; end: number };
	cold_return_tax: Record<string, { matched: number; strict: number }>;
	exemplars: Record<string, SpellExemplar[]>;
	exemplar_medians: Record<string, number>;
	headline: {
		one_over_start: number;
		one_over_end: number;
		tax_start: number;
		tax_end: number;
		text: string;
	};
	definition: string;
}

/* ---- belief 4: momentum (FAIL with an honest residual) -------------------- */

export interface ShuffleNull {
	mean_lift: number;
	sd: number;
	/** [lo, hi], the shaded band of shuffled cricket */
	band: [number, number];
	z: number;
	clears: boolean;
	/** binned counts over [hist.lo, hist.hi], length nbins */
	counts: number[];
	/** present on the fuller (same-batter) null: the surviving real part */
	residual?: number;
}

export interface ClaimRow {
	claim: string;
	fan: string;
	obs_pct: number;
	base_pct: number;
	/** the observed value, the needle (1.0 = no effect) */
	lift: number;
	hist: { lo: number; hi: number; nbins: number };
	plain_null: ShuffleNull;
	/** the same-batter null, present only on bnd|bnd, six|six, dot|dot, wkt|wkt in the 3 IPL eras */
	batter_null?: ShuffleNull;
}

export interface Momentum {
	grade: Grade;
	menu: { claim: string; fan: string }[];
	scripted: { wicket_myth: string; hitting_sliver: string };
	no_effect_line: number;
	claims_by_era: Record<string, ClaimRow[]>;
	summary: {
		wicket_plain_lifts: Record<string, number>;
		boundary_raw_lifts: Record<string, number>;
		boundary_residuals: Record<string, number>;
		six_residuals: Record<string, number>;
		hero_reconcile: Record<string, { obs: number; base: number }>;
		text: string;
	};
	definition: string;
}

/* ---- belief 5: required-rate responsiveness (PASS) ------------------------ */

export interface RequiredRate {
	grade: Grade;
	phases: string[];
	by_era: Record<string, { pp: number; mid: number; death: number }>;
	pinned: string[];
	/** per era: [phase_idx, run_rate] × 3 */
	curve: Record<string, [number, number][]>;
	ahead_halfway: Record<string, number>;
	rrr_drift: Record<string, number>;
	pp_jump: number;
	headline: {
		pp_2008: number;
		pp_2026: number;
		mid_2026: number;
		pp_jump: number;
		ahead_2008: number;
		ahead_2026: number;
		text: string;
	};
	caveat: string;
	definition: string;
}

/* ---- the WPL doctrine transmission ---------------------------------------- */

export interface Wpl {
	field_first_by_season: Record<string, { field_first: number; matches: number }>;
	field_first_pooled: number;
	/** [x_norm, pct] × 4, the fast two-season adoption curve */
	adoption_curve: [number, number][];
	chase_win_pooled: number;
	review: { reviews: number; upheld_pct: number };
	one_over_share: number;
	ipl_compare: { field_first_settled: string; one_over_share: number; review_upheld_pct: number };
	headline: {
		season_one_field_first: number;
		field_first_pooled: number;
		review_upheld_pct: number;
		one_over_share: number;
		text: string;
	};
	framing: string;
}

/* ---- the payoff (your captains' report card, 16 variants) ----------------- */

export interface HomeStat {
	pct: number;
	n: number;
	d: number;
}

export interface PayoffVariant {
	team: string;
	team_id: number | null;
	short: string;
	league: 'ipl' | 'wpl' | 'neutral';
	empty_state: boolean;
	headline: string;
	/* IPL */
	home_ground?: string;
	field_first_at_home?: HomeStat;
	chase_win_at_home?: HomeStat;
	review_rank?: number;
	review_upheld_pct?: number;
	review_of?: number;
	flavor?: string;
	guard?: string;
	/* WPL bespoke */
	bespoke?: boolean;
	wpl_transmission?: boolean;
	transmission?: {
		field_first_season_one: number;
		field_first_pooled: number;
		review_upheld_pct: number;
		one_over_share: number;
	};
	/* neutral */
	league_field_first?: number;
	league_chase_win?: number;
	league_review_upheld?: number;
}

export interface PayoffBlock {
	card: string;
	definition: string;
	leaderboard: ReviewTeam[];
	variants: PayoffVariant[];
}

/* ---- footnotes ------------------------------------------------------------ */

export interface Ch8Footnote {
	text: string;
	usable_by_season?: Record<string, number>;
}

/* ---- top level ------------------------------------------------------------ */

export interface Ch8Data {
	chapter: number;
	title: string;
	register: string;
	report_card: ReportCard;
	controlling_morph: ControllingMorph;
	mystery_handoff_in: string;
	mystery_handoff_out: string;
	match_dots: MatchDots;
	toss: Toss;
	review: Review;
	review_subset: ReviewSubsetData;
	spell: Spell;
	momentum: Momentum;
	required_rate: RequiredRate;
	wpl: Wpl;
	payoff: PayoffBlock;
	footnotes: Record<string, Ch8Footnote>;
}

/* ---- loader (cached; base-path aware) ------------------------------------- */

let ch8Promise: Promise<Ch8Data> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

export function loadCh8Data(): Promise<Ch8Data> {
	ch8Promise ??= fetchJson<Ch8Data>('/data/scenes/ch8.json');
	return ch8Promise;
}

/* ---- the match-dots table (fed to the field, CONTRACT §24) ---------------- */

/**
 * Build the 1,331-row match table for `field.setMatchTable`. The pipeline emits
 * normalized [0,1] centroids (x = start-date, y = low-discrepancy spread); the
 * field's shader maps a [-1,1] frame to world (nx × halfW), so we remap here so
 * the earliest match lands at the left edge and the latest at the right. Size and
 * brightness encode NOTHING (the density gain is derived in the field from the
 * bounds block, so a run-heavy match is no brighter than a short one).
 */
export function buildMatchTable(d: Ch8Data): MatchTable {
	const md = d.match_dots;
	const cnt = md.count;
	const centroids = new Float32Array(cnt * 2);
	const toss = new Float32Array(cnt);
	const result = new Float32Array(cnt);
	for (let m = 0; m < cnt; m++) {
		const row = md.centroids[m];
		centroids[m * 2] = row[0] * 2 - 1; // [0,1] → [-1,1]
		centroids[m * 2 + 1] = row[1] * 2 - 1;
		toss[m] = row[2];
		result[m] = row[3];
	}
	return { count: cnt, centroids, toss, bounds: md.bounds, result };
}

/**
 * Feed the match table to the field ONCE per field instance (idempotent, a
 * re-feed just re-bakes the two data textures). Called by every match-dots scene
 * so a deep link into a belief still condenses the dots, not the free scatter.
 */
let matchFedFor: FieldHandle | null = null;
export function ensureMatchTable(field: FieldHandle | null, d: Ch8Data | null): void {
	if (!field || !d || matchFedFor === field) return;
	matchFedFor = field;
	field.setMatchTable(buildMatchTable(d));
}

/** Map a normalized-date x in [0,1] to the field's [-1,1] frame (for the season axis). */
export const dateNormToField = (xn: number): number => xn * 2 - 1;
/** Map a normalized y in [0,1] to the field's [-1,1] frame. */
export const spreadNormToField = (yn: number): number => yn * 2 - 1;

/* ---- the review chips (the 988, fed to the field, CONTRACT §25) ----------- */

export interface ReviewLaneMeta {
	lane: number;
	team_id: number;
	short: string;
	team: string;
	reviews: number;
	upheld: number;
	struck: number;
	upheld_pct: number;
}

/**
 * The franchise lanes, in a stable contiguous order (by team_id) so the review
 * subset's sparse team_ids (0,2,4,6,7,8,10,11,13,14) collapse to 0..9 with no
 * empty columns. Drives both the setReviews lane index and the scene's SVG labels.
 */
export function reviewLanes(d: Ch8Data): ReviewLaneMeta[] {
	const teams = d.review.per_team.slice().sort((a, b) => a.team_id - b.team_id);
	return teams.map((t, i) => ({
		lane: i,
		team_id: t.team_id,
		short: t.short,
		team: t.team,
		reviews: t.reviews,
		upheld: t.upheld,
		struck: t.struck,
		upheld_pct: t.upheld_pct
	}));
}

/** team_id → contiguous lane index. */
function laneIndexByTeamId(d: Ch8Data): Map<number, number> {
	const m = new Map<number, number>();
	reviewLanes(d).forEach((l) => m.set(l.team_id, l.lane));
	return m;
}

/**
 * Build the 988-chip membership for `field.setReviews`, remapping the raw team_ids
 * to contiguous lane indices so the chip stacks have no gaps. Unknown-team reviews
 * (-1) fall to lane 0 (there are none in the emitted subset: unknown_team = 0).
 */
export function buildReviewInput(d: Ch8Data): ReviewInput {
	const map = laneIndexByTeamId(d);
	const rs = d.review_subset;
	const team = new Int32Array(rs.count);
	for (let j = 0; j < rs.count; j++) team[j] = map.get(rs.team[j]) ?? 0;
	return { indices: rs.indices, team, outcome: rs.outcome };
}

/** Feed the review membership ONCE per field instance (the chips fly on `reviews.engage`). */
let reviewsFedFor: FieldHandle | null = null;
export function ensureReviews(field: FieldHandle | null, d: Ch8Data | null): void {
	if (!field || !d || reviewsFedFor === field) return;
	reviewsFedFor = field;
	field.setReviews(buildReviewInput(d));
}

/** The reader's own chip lane (-1 when they picked no IPL franchise with reviews). */
export function ownReviewLane(d: Ch8Data, pick: TeamPickLite | null): number {
	if (!pick || pick.league !== 'ipl') return -1;
	const l = reviewLanes(d).find((x) => x.team === pick.team);
	return l ? l.lane : -1;
}

/* ---- payoff resolution (mirrors the ch7 variant contract) ----------------- */

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
 * Resolve a reader's pick to their report card. Neutral / unknown picks get the
 * neutral variant (deep links always work). Matching is by (league, team name) -
 * the WPL and IPL share franchise names, so the league is load-bearing.
 */
export function payoffVariantFor(d: Ch8Data, pick: TeamPickLite | null): ResolvedPayoff {
	const neutral = d.payoff.variants.find((v) => v.league === 'neutral') ?? null;
	if (pick === null || pick.league === null || pick.team === 'neutral') {
		return { variant: neutral, kind: 'neutral', fallback: false };
	}
	const exact = d.payoff.variants.find((v) => v.league === pick.league && v.team === pick.team);
	if (exact)
		return {
			variant: exact,
			kind: exact.league === 'neutral' ? 'neutral' : exact.league,
			fallback: false
		};
	return { variant: neutral, kind: 'neutral', fallback: true };
}

/* ---- formatters ----------------------------------------------------------- */

/** One decimal ("8.5"). */
export const fmt1 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
/** Two decimals ("8.99"). */
export const fmt2 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
/** A percentage rounded to a whole number ("52"), for the "N in 100" reads. */
export const pct0 = (n: number): number => Math.round(n);
/** Integer with thousands separators ("1,331"). */
export const int = (n: number): string => Math.round(n).toLocaleString('en-US');
/** A signed two-decimal delta ("+0.16", "-0.04"), the cold-return tax reads. */
export const signed2 = (n: number): string => (n >= 0 ? '+' : '') + fmt2(n);
