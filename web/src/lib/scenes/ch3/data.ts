import { base } from '$app/paths';

/**
 * Typed access to Chapter 3's scene artifact:
 *   static/data/scenes/ch3.json — the frontier plane (per-season Pareto edges +
 *     ghost trail + under-seven share) · dismissal DNA rivers (per-season kind
 *     counts) · Dot+ dot-grid exemplars · the death-wide tax gauge · the WPL
 *     two-clock beat · per-franchise "gravity-defier" payoff variants · the
 *     footnote figures (True Economy, refuted correlation, FIB, Phase Fingerprint).
 *
 * EVERY on-screen number in C3-1..C3-9 comes through here — never hardcoded
 * (OWNER-LOCKED rule). Where the storyboard's teaser copy and the emitted
 * artifact disagree (death wides 3.3→6.7 vs the emitted 3.13→6.45; crack ratio
 * 1.11/0.84 vs the emitted 1.18/0.81; the hero share 1% vs the emitted 1.5%),
 * the ARTIFACT wins — the pipeline JSON is the source of truth (storyboard §3).
 * Fetched once per session, cached as a module-level promise, always through
 * `$app/paths` base.
 */

/* ---- band keys + era bands (shared with ch1/ch2 convention) --------------- */

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

export interface EraBand {
	key: BandKey;
	label: string;
	league: 'ipl' | 'wpl';
	seasons: number[];
}

/* ---- the frontier plane (hero: Attack-Containment Frontier Drift) ---------- */

export interface HullPoint {
	bowler: string;
	economy: number;
	strike_rate: number;
	wickets: number;
	balls: number;
}

export interface HullSeason {
	league: 'ipl' | 'wpl';
	season: number;
	points: HullPoint[];
}

export interface GhostPoint {
	season: number;
	economy: number;
	strike_rate: number;
	wickets: number;
	balls: number;
}

export interface Under7Band {
	pct: number;
	qualifiers: number;
	under7: number;
}

export interface Under7Season {
	league: 'ipl' | 'wpl';
	season: number;
	pct: number;
	qualifiers: number;
	under7: number;
}

export interface FrontierAxis {
	economy: { lo: number; hi: number; unit: string; better: string };
	strike_rate: { lo: number; hi: number; unit: string; better: string; sentinel: number };
}

export interface FrontierBlock {
	definition: string;
	axis: FrontierAxis;
	hull: { note: string; seasons: HullSeason[] };
	ghost_trail: { bowler: string; league: 'ipl' | 'wpl'; note: string; points: GhostPoint[] };
	under7: { definition: string; era_bands: Record<BandKey, Under7Band>; per_season: Under7Season[] };
	correlation: { definition: string; era_bands: Record<string, { n: number; r: number }> };
}

/* ---- dismissal DNA (supporting: the rivers subset) ------------------------- */

export interface DismissalBand {
	bowled_lbw_pct: number;
	caught_pct: number;
	caught_and_bowled_pct: number;
	stumped_pct: number;
	run_outs: number;
	bowler_credited: number;
	kinds: Record<string, number>;
}

export interface RiverSeason {
	league: 'ipl' | 'wpl';
	season: number;
	kinds: Record<string, number>;
}

export interface DismissalBlock {
	definition: string;
	era_bands: Record<BandKey, DismissalBand>;
	rivers: { note: string; per_season: RiverSeason[] };
}

/* ---- Dot+ (the dot-grid) -------------------------------------------------- */

export interface DotInnings {
	label: string;
	league: 'ipl' | 'wpl';
	season: number;
	batting_team: string;
	opponent: string;
	venue: string;
	city: string;
	date: string;
	stage: string;
	legal_balls: number;
	dots: number;
	dot_pct: number;
	match_index: number;
	/** 120 cells: 0 dot · 1 single · 2 two/three · 3 four · 4 six · 5 other */
	outcomes: number[];
	/** 120 cells: 1 where a wicket fell */
	wickets: number[];
}

export interface DotGridBlock {
	definition: string;
	innings: DotInnings[];
	outcome_legend: Record<string, string>;
}

export interface DotPlusBlock {
	definition: string;
	era_headline: { ipl_2008_2010: number; ipl_2023_2026: number; wpl_2023_2026: number };
	leaderboard: { bowler: string; season: number; league: string; dot_plus: number }[];
	per_season: { league: 'ipl' | 'wpl'; season: number; dot_pct: number; legal_balls: number }[];
}

/* ---- Death-Wide Tax (the leak gauge) -------------------------------------- */

export interface WideSeason {
	league: 'ipl' | 'wpl';
	season: number;
	death_legal_balls: number;
	wide_deliveries: number;
	wides_per_100_legal: number;
}

export interface DeathWideBlock {
	definition: string;
	era_headline: {
		doubling_factor: number;
		ipl_2008_2010: number;
		ipl_2023_2026: number;
		wpl_2023_2026: number;
	};
	per_season: WideSeason[];
}

/* ---- WPL two-clock beat --------------------------------------------------- */

export interface WplStumped {
	ipl_2023_2026_pct: number;
	pooled_pct: number;
	per_season: { season: number; stumped: number; bowler_credited: number; pct: number }[];
}

export interface WplBeatBlock {
	dot_rate_pct: number;
	dot_rate_matches: string;
	crack_ratio_wpl: number;
	crack_ratio_ipl_2023_2026: number;
	death_wides_per_100_legal: number;
	note: string;
	stumped: WplStumped;
}

/* ---- "your gravity-defier" payoff ----------------------------------------- */

export interface GravityVariant {
	franchise_id: number;
	franchise: string;
	league: 'ipl' | 'wpl';
	bowler: string;
	season: number;
	economy: number;
	par_economy: number;
	true_economy: number;
	wickets: number;
	balls: number;
	small_sample: boolean;
}

export interface GravityBlock {
	definition: string;
	variants: GravityVariant[];
	wpl_note: string;
}

/* ---- top level ------------------------------------------------------------ */

export interface Ch3Data {
	chapter: number;
	title: string;
	register: string;
	era_bands: EraBand[];
	frontier: FrontierBlock;
	dismissal_dna: DismissalBlock;
	dot_grid: DotGridBlock;
	dot_plus: DotPlusBlock;
	death_wide_tax: DeathWideBlock;
	wpl_beat: WplBeatBlock;
	gravity_defiers: GravityBlock;
}

/* ---- loader (cached; base-path aware) ------------------------------------- */

let ch3Promise: Promise<Ch3Data> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

export function loadCh3Data(): Promise<Ch3Data> {
	ch3Promise ??= fetchJson<Ch3Data>('/data/scenes/ch3.json');
	return ch3Promise;
}

/* ---- formatters ----------------------------------------------------------- */

/** One decimal, tabular (6.1, 27.4). */
export const fmt1 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
/** Two decimals (0.84). */
export const fmt2 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export const int = (n: number): string => n.toLocaleString('en-US');
/** A percent number, trailing ".0" dropped ("29", "1.5", "74"). */
export const pctText = (n: number): string =>
	Number.isInteger(n) ? n.toFixed(0) : n.toFixed(1);

/* ---- derived helpers ------------------------------------------------------ */

/** The bowler-credited wicket kinds the GL bands + SVG areas share (§16 codes). */
export const RIVER_STACK: ('bowled' | 'lbw' | 'stumped' | 'caught')[] = [
	'bowled',
	'lbw',
	'stumped',
	'caught'
];

/**
 * The five-kind bowler-credited share for one season strip, bottom→top:
 * bowled, lbw, stumped, caught-and-bowled, caught, summing to 1. Caught-and-bowled
 * is split into its OWN thin sliver just beneath caught so the visible caught band
 * equals the caption's bowler-credited `caught_pct` (65.2 → 74.0), which EXCLUDES
 * caught-and-bowled per ch3.json's definition — folding c&b into caught made the
 * band ~3pp thicker than the number the caption states. The denominator still
 * counts every bowler-credited wicket (incl. c&b), so the bowled/lbw/stumped
 * boundaries are unchanged and the (c&b + caught) union registers exactly to the
 * GL caught band (setDismissals folds c&b into code 2). Empty season → zeros.
 */
export function riverShares(k: Record<string, number>): number[] {
	const bowled = k['bowled'] ?? 0;
	const lbw = k['lbw'] ?? 0;
	const stumped = k['stumped'] ?? 0;
	const caughtAndBowled = k['caught and bowled'] ?? 0;
	const caught = k['caught'] ?? 0;
	const total = bowled + lbw + stumped + caughtAndBowled + caught;
	if (total <= 0) return [0, 0, 0, 0, 0];
	return [bowled / total, lbw / total, stumped / total, caughtAndBowled / total, caught / total];
}

/** Cumulative-share boundaries 0..1 for a season strip (length 5: 0 → 1). */
export function riverBoundaries(k: Record<string, number>): number[] {
	const s = riverShares(k);
	const out = [0];
	let acc = 0;
	for (const v of s) {
		acc += v;
		out.push(acc);
	}
	out[out.length - 1] = 1; // clamp rounding
	return out;
}

/* ---- the C3-3 retreat scrub (shared by index.ts dynamicState + Retreat.svelte)
 * so the scroll-driven season filter and the on-screen chip can never disagree. */

export const RETREAT_YEARS: number[] = Array.from({ length: 19 }, (_, i) => 2008 + i);

export interface RetreatState {
	/** 1 seven-line · 2 the scrub (hero number) · 3 ghost trail · 4 thesis */
	step: 1 | 2 | 3 | 4;
	/** filterSeason value driving the field brighten (null = whole all-time haze) */
	year: number | null;
	/** the year the count chip reads (never null — 2008 baseline before the scrub) */
	chipYear: number;
}

export function retreatState(progress: number): RetreatState {
	if (progress < 0.28) return { step: 1, year: null, chipYear: 2008 };
	if (progress < 0.6) {
		const t = (progress - 0.28) / (0.6 - 0.28);
		const idx = Math.min(RETREAT_YEARS.length - 1, Math.round(t * (RETREAT_YEARS.length - 1)));
		const y = RETREAT_YEARS[idx];
		return { step: 2, year: y, chipYear: y };
	}
	if (progress < 0.8) return { step: 3, year: 2026, chipYear: 2026 };
	return { step: 4, year: null, chipYear: 2026 };
}

/**
 * IPL under-seven share as a trailing 3-season POOLED rate for the count chip,
 * forward-clamped so the window always spans 3 available seasons (the earliest
 * three at the start). Pooling the raw under7/qualifier COUNTS (not averaging the
 * noisy per-season percentages) yields a monotone-reading retreat that holds
 * 29.0% across 2008-2010 — matching the caption's "nearly a third (29%)" — instead
 * of the raw whiplash (2008 20.8% → 2009 42.6%). Returns null before the data loads.
 */
export function under7PooledPct(d: Ch3Data, season: number): number | null {
	const rows = d.frontier.under7.per_season
		.filter((s) => s.league === 'ipl')
		.sort((a, b) => a.season - b.season);
	if (rows.length === 0) return null;
	let i = rows.findIndex((s) => s.season === season);
	if (i < 0) i = season < rows[0].season ? 0 : rows.length - 1;
	// trailing 3-season window, clamped forward at the start so it is always 3 wide
	const start = Math.max(0, Math.min(i - 2, rows.length - 3));
	const win = rows.slice(start, start + 3);
	let under = 0;
	let qual = 0;
	for (const r of win) {
		under += r.under7;
		qual += r.qualifiers;
	}
	return qual > 0 ? Math.round((1000 * under) / qual) / 10 : null;
}

/** The IPL hull ("edge of the possible") for a season year, or null. */
export function iplHull(d: Ch3Data, season: number): HullPoint[] | null {
	const row = d.frontier.hull.seasons.find((s) => s.league === 'ipl' && s.season === season);
	return row ? row.points : null;
}

/* ---- gravity-defier resolution (mirrors ch2's anchorVariantFor contract) --- */

export interface TeamPickLite {
	league: 'ipl' | 'wpl' | null;
	team: string;
}

export interface ResolvedGravity {
	variant: GravityVariant;
	kind: 'ipl' | 'wpl' | 'neutral';
	fallback: boolean;
}

/**
 * Resolve a reader's pick to their gravity-defier. Neutral / unknown picks fall
 * back to the league-wide best True Economy across all IPL history (deep links
 * always work). Sister franchises are disambiguated by matching league AND name.
 */
export function gravityVariantFor(d: Ch3Data, pick: TeamPickLite | null): ResolvedGravity | null {
	const variants = d.gravity_defiers.variants;
	if (variants.length === 0) return null;

	// the neutral / fallback card: the biggest True-Economy gap in IPL history
	const iplBest = variants
		.filter((v) => v.league === 'ipl')
		.reduce<GravityVariant | null>((best, v) => (!best || v.true_economy > best.true_economy ? v : best), null);
	const neutralPick = iplBest ?? variants[0];

	if (pick === null || pick.league === null || pick.team === 'neutral') {
		return { variant: neutralPick, kind: 'neutral', fallback: false };
	}
	const exact = variants.find((v) => v.league === pick.league && v.franchise === pick.team);
	if (exact) return { variant: exact, kind: exact.league === 'wpl' ? 'wpl' : 'ipl', fallback: false };
	return { variant: neutralPick, kind: 'neutral', fallback: true };
}
