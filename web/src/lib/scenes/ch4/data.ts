import { base } from '$app/paths';
import type { SceneFieldState } from '$lib/story/types';

/**
 * Typed access to Chapter 4's scene artifact:
 *   static/data/scenes/ch4.json — the rising-tide skyline (per-season innings
 *     totals + the climbing par waterline) · the 200 Club threshold exceedance ·
 *     the T20 CPI cold-open callback · the powerplay premium + phase heatmap ·
 *     the venue divergence cone · the record half-life ticker · the WPL two-clock
 *     beat · the per-franchise "your home ground's tide" payoff · the footnotes.
 *
 * EVERY on-screen number in C4-1..C4-12 comes through here — never hardcoded
 * (OWNER-LOCKED rule). Where the storyboard's teaser copy and the emitted
 * artifact disagree, the ARTIFACT wins (P(200) 42.0 not 41.9; par 195.3;
 * 230-plus posted 33 / defended 29, NOT "11/11"; between-venue share
 * 10.1% → 23.7% season-controlled, not 11 → 27). Fetched once per session,
 * cached as a module-level promise, always through `$app/paths` base.
 */

/* ---- era bands (shared convention with ch1/ch2/ch3) ----------------------- */

export type BandKey =
	| 'ipl 2008-2010'
	| 'ipl 2011-2015'
	| 'ipl 2016-2019'
	| 'ipl 2020-2022'
	| 'ipl 2023-2026'
	| 'wpl 2023-2026';

export const IPL_EARLY: BandKey = 'ipl 2008-2010';
export const IPL_MODERN: BandKey = 'ipl 2023-2026';
export const WPL_BAND: BandKey = 'wpl 2023-2026';

/** Runs shorthand: a per-season map keyed by the season year as a string. */
export type SeasonMap = Record<string, number>;

/* ---- columns / waterline (the controlling morph) -------------------------- */

export interface ColumnsBlock {
	definition: string;
	/** per-season, 3-season-window logistic par — the rising waterline level (runs) */
	par_waterline: SeasonMap;
	distribution: {
		ipl: Record<string, { max: number; mean: number; median: number; min: number; n: number }>;
		wpl: Record<string, { max: number; mean: number; median: number; min: number; n: number }>;
	};
}

/* ---- 200 Club threshold exceedance (hero) --------------------------------- */

export interface ExceedanceRow {
	exceedance_count: Record<string, number>;
	exceedance_pct: Record<string, number>;
	max: number;
	n: number;
}

export interface ExceedanceBlock {
	definition: string;
	thresholds: number[];
	by_era: Record<BandKey, ExceedanceRow>;
	by_season: { ipl: Record<string, ExceedanceRow>; wpl: Record<string, ExceedanceRow> };
	cliff: {
		before: { season: number; p200: number };
		after: { season: number; p200: number };
		era_before: { era: string; p200: number };
		era_after: { era: string; p200: number };
		note: string;
	};
}

/* ---- par drift (hero) ----------------------------------------------------- */

export interface ParDriftBlock {
	definition: string;
	by_era: Record<BandKey, { par: number; safe: number; dead: number; n: number }>;
	by_season_windowed: { ipl: SeasonMap; wpl: SeasonMap };
	totals_230plus: {
		floor: number;
		era: string;
		posted: number;
		defended: number;
		defended_pct: number;
		chased_down: number;
		chased_list: { season: number; total: number }[];
		note: string;
	};
}

/* ---- T20 CPI cold-open callback (supporting) ------------------------------ */

export interface CpiBlock {
	definition: string;
	index_base: string;
	first_innings_rpo_by_season: { ipl: SeasonMap; wpl: SeasonMap };
	by_era: Record<string, { first_innings_rpo: number; index: number }>;
	callback_sketch: {
		definition: string;
		truth_200s_by_season: SeasonMap;
		authored_typical_200s_by_season: SeasonMap;
	};
}

/* ---- powerplay premium (supporting) --------------------------------------- */

export interface PowerplayBlock {
	definition: string;
	by_era: Record<BandKey, { run_rate: number; wickets_per_36: number; legal_balls: number }>;
	by_season: {
		ipl: Record<string, { run_rate: number; wickets_per_36: number; legal_balls: number }>;
		wpl: Record<string, { run_rate: number; wickets_per_36: number; legal_balls: number }>;
	};
	equal_wicket_cost: {
		early_rr: number;
		early_wickets_per_36: number;
		late_rr: number;
		late_wickets_per_36: number;
		note: string;
	};
}

/* ---- phase heatmap (2D scene, powers the powerplay beat) ------------------- */

export interface PhaseHeatmapBlock {
	definition: string;
	by_over: { ipl: Record<string, number[]>; wpl: Record<string, number[]> };
	phase_rpo_by_era: Record<
		BandKey,
		{ pp: number; middle: number; death: number; death_minus_pp: number }
	>;
}

/* ---- venues (supporting, contrarian twist) -------------------------------- */

export interface VenueStrand {
	venue: string;
	city: string;
	league: 'ipl' | 'wpl';
	by_era: Partial<Record<BandKey, { avg_first_innings: number; n: number }>>;
}

export interface VenuesBlock {
	definition: string;
	between_venue_variance: Record<string, { between_venue_share_pct: number; seasons: number }>;
	fingerprint_2023_2026: { chinnaswamy: number; chepauk: number; note: string };
	strands: VenueStrand[];
}

/* ---- record half-life (hero close) ---------------------------------------- */

export interface RecordStep {
	total: number;
	team: string;
	opponent: string;
	season: number;
	date: string;
	venue: string;
	city: string;
	stood_days: number | null;
	standing: boolean;
}

export interface RecordBlock {
	definition: string;
	ipl_progression: RecordStep[];
	wpl_progression: RecordStep[];
	ticker: {
		ipl: Record<string, { total: number; team: string; since_season: number }>;
		wpl: Record<string, { total: number; team: string; since_season: number }>;
	};
	stationary_environment_null: string;
}

/* ---- the planted 2023 mystery --------------------------------------------- */

export interface MysteryBlock {
	hold: string;
	note: string;
}

/* ---- WPL two-clock beat --------------------------------------------------- */

export interface WplBeatBlock {
	framing: string;
	avg_first_innings_by_season: SeasonMap;
	exceedance_p200: number;
	totals_200_by_season: SeasonMap;
	sits_between_ipl_seasons: {
		seasons: number[];
		wpl_p200: number;
		ipl_p200: Record<string, number>;
	};
	maturity_clock: {
		definition: string;
		ipl_by_league_year: Record<string, number>;
		wpl_by_league_year: Record<string, number>;
	};
}

/* ---- "your home ground's tide" payoff ------------------------------------- */

export interface PayoffEraCell {
	era: string;
	avg_first_innings: number | null;
	n: number;
}

export interface PayoffVariant {
	team: string;
	league: 'ipl' | 'wpl' | 'neutral';
	empty_state: boolean;
	headline: string;
	fingerprint?: string;
	fingerprint_copy?: string;
	home_ground?: string | null;
	home_city?: string;
	latest_avg_first_innings?: number;
	league_latest_avg_first_innings?: number;
	rise_first_to_latest?: number | null;
	par_by_era?: PayoffEraCell[];
	rotating_home?: boolean;
	league_avg_first_innings_by_season?: SeasonMap;
	india_map?: {
		venue: string;
		city: string;
		team: string;
		avg_first_innings: number;
		n: number;
	}[];
}

export interface PayoffBlock {
	card: string;
	eras: { ipl: string[] };
	variants: PayoffVariant[];
}

/* ---- footnotes ------------------------------------------------------------ */

export interface Ch4Footnotes {
	par_model: string;
	full_first_innings_filter: string;
	venue_canonicalization: string;
	record_null: string;
	phase_economy_map: string;
}

/* ---- top level ------------------------------------------------------------ */

export interface Ch4Data {
	chapter: number;
	title: string;
	register: string;
	columns: ColumnsBlock;
	exceedance: ExceedanceBlock;
	par_drift: ParDriftBlock;
	cpi: CpiBlock;
	powerplay: PowerplayBlock;
	phase_heatmap: PhaseHeatmapBlock;
	venues: VenuesBlock;
	record_halflife: RecordBlock;
	mystery: MysteryBlock;
	wpl_beat: WplBeatBlock;
	payoff: PayoffBlock;
	footnotes: Ch4Footnotes;
}

/* ---- loader (cached; base-path aware) ------------------------------------- */

let ch4Promise: Promise<Ch4Data> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

export function loadCh4Data(): Promise<Ch4Data> {
	ch4Promise ??= fetchJson<Ch4Data>('/data/scenes/ch4.json').then((d) => {
		// OWNER-LOCK: cache the waterline levels + the reduced-motion settled level
		// straight from the artifact, so index.ts's pure dynamicState and the
		// reduced-motion end state never carry a hardcoded number.
		parLevelsBySeasonIdx = TIDE_SEASONS.map((y) => d.columns.par_waterline[String(y)] ?? 0);
		const last = parLevelsBySeasonIdx[parLevelsBySeasonIdx.length - 1] ?? 0;
		waterlineReducedEnd.waterline = { level: last, drownDim: WATER_DROWN };
		return d;
	});
	return ch4Promise;
}

/* ---- formatters ----------------------------------------------------------- */

/** Integer with thousands separators (263, 3,991). */
export const int = (n: number): string => n.toLocaleString('en-US');
/** One decimal, tabular (9.5, 172.7). */
export const fmt1 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
/** Two decimals (1.54). */
export const fmt2 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
/** Round to whole runs (165, 206) — par reads as a scoreboard number, not a decimal. */
export const runs = (n: number): string => Math.round(n).toLocaleString('en-US');
/** A percent number, trailing ".0" dropped ("52", "7.7", "42"). */
export const pct = (n: number): string => (Number.isInteger(n) ? n.toFixed(0) : n.toFixed(1));

/* ---- the tide skyline: shared morph state (OWNER-LOCK aware) --------------- */

/** Default drowned-column luminance (CONTRACT §18.4 default). */
export const WATER_DROWN = 0.18;

/** The 19 IPL seasons the waterline scrub walks (2008 → 2026). */
export const TIDE_SEASONS: number[] = Array.from({ length: 19 }, (_, i) => 2008 + i);

/**
 * The per-season windowed par (waterline level in runs), cached from ch4.json by
 * the loader so the SceneDef's pure `dynamicState` can raise the water without
 * hardcoding a number. null until the artifact loads (level 0 = nothing drowns).
 */
let parLevelsBySeasonIdx: number[] | null = null;
export function tideParLevels(): number[] | null {
	return parLevelsBySeasonIdx;
}

/**
 * The reduced-motion settled waterline end state: the field jump-cuts to the
 * water at its 2026 height (drowning every old-safe total). Its level is filled
 * in by `loadCh4Data` from the artifact, so no number is hardcoded here.
 */
export const waterlineReducedEnd: SceneFieldState = {
	layout: 'tide',
	waterline: { level: 0, drownDim: WATER_DROWN }
};

export interface WaterScrub {
	/** 1 orient the line · 2 the water rises (hero) · 3 the drowned-total punchline */
	step: 1 | 2 | 3;
	/** index into TIDE_SEASONS (0 = 2008) the water has climbed to */
	seasonIdx: number;
	season: number;
}

/**
 * The waterline scrub pointer as a PURE function of scroll progress (shared by
 * index.ts's dynamicState and the Waterline component so the field level and the
 * on-screen year chip can never disagree — mirrors ch3's retreatState).
 */
export function waterlineScrub(progress: number): WaterScrub {
	if (progress < 0.24) return { step: 1, seasonIdx: 0, season: TIDE_SEASONS[0] };
	if (progress < 0.72) {
		const t = (progress - 0.24) / (0.72 - 0.24);
		const idx = Math.min(TIDE_SEASONS.length - 1, Math.round(t * (TIDE_SEASONS.length - 1)));
		return { step: 2, seasonIdx: idx, season: TIDE_SEASONS[idx] };
	}
	const last = TIDE_SEASONS.length - 1;
	return { step: 3, seasonIdx: last, season: TIDE_SEASONS[last] };
}

/**
 * The waterline level (runs) for a scrub pointer, straight from the cached
 * per-season par. Returns 0 (nothing drowns) until the artifact loads.
 */
export function waterlineLevelAt(seasonIdx: number): number {
	const levels = parLevelsBySeasonIdx;
	if (!levels) return 0;
	return levels[Math.min(levels.length - 1, Math.max(0, seasonIdx))];
}

/* ---- the 200 Club scrub (shared by index.ts filterSeason + the component) -- */

export interface ClubScrub {
	step: 1 | 2 | 3;
	seasonIdx: number;
	season: number;
	/** true once the reader has scrubbed past the 2023 cliff (2023..2026) */
	pastCliff: boolean;
}

/** The exceedance scrub pointer as a pure function of progress. */
export function clubScrub(progress: number): ClubScrub {
	if (progress < 0.22) return mkClub(1, 0);
	if (progress < 0.82) {
		const t = (progress - 0.22) / (0.82 - 0.22);
		const idx = Math.min(TIDE_SEASONS.length - 1, Math.round(t * (TIDE_SEASONS.length - 1)));
		return mkClub(2, idx);
	}
	return mkClub(3, TIDE_SEASONS.length - 1);
}
function mkClub(step: 1 | 2 | 3, seasonIdx: number): ClubScrub {
	const season = TIDE_SEASONS[seasonIdx];
	return { step, seasonIdx, season, pastCliff: season >= 2023 };
}

/* ---- gi ↔ season, for anchoring SVG rules / chips to the GL skyline -------- */

export interface GroupLite {
	gi: number;
	league: 'ipl' | 'wpl';
	season: number;
}

/** The group index for a (league, season) block, or -1. */
export function giFor(groups: GroupLite[], league: 'ipl' | 'wpl', season: number): number {
	const g = groups.find((x) => x.league === league && x.season === season);
	return g ? g.gi : -1;
}

/* ---- payoff resolution (mirrors ch3's gravityVariantFor contract) --------- */

export interface TeamPickLite {
	league: 'ipl' | 'wpl' | null;
	team: string;
}

export interface ResolvedPayoff {
	variant: PayoffVariant;
	kind: 'ipl' | 'wpl' | 'neutral';
	fallback: boolean;
}

/**
 * Resolve a reader's pick to their home-ground tide card. Neutral / unknown
 * picks fall back to the all-India map variant (deep links always work).
 */
export function payoffVariantFor(d: Ch4Data, pick: TeamPickLite | null): ResolvedPayoff | null {
	const variants = d.payoff.variants;
	if (variants.length === 0) return null;
	const neutral = variants.find((v) => v.league === 'neutral') ?? variants[variants.length - 1];

	if (pick === null || pick.league === null || pick.team === 'neutral') {
		return { variant: neutral, kind: 'neutral', fallback: false };
	}
	const exact = variants.find((v) => v.league === pick.league && v.team === pick.team);
	if (exact) return { variant: exact, kind: exact.league === 'wpl' ? 'wpl' : 'ipl', fallback: false };
	return { variant: neutral, kind: 'neutral', fallback: true };
}
