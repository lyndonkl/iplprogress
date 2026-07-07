import { base } from '$app/paths';
import type { ConstellationPhase } from '$lib/field/types';
import type { StarTable } from '$lib/field/field';

/**
 * Typed access to Chapter 6's scene artifact:
 *   static/data/scenes/ch6.json — the season constellation (23 season-stars +
 *     four Procrustes-aligned per-phase star tables + the IPL worm order + the
 *     WPL nearest-neighbour threads + the two-truths pairings) · the League
 *     Maturity Clock (both leagues on league-year) · the Run DNA composition ·
 *     the Stumping Signature · the Photo-Finish rate · the sister-franchise
 *     payoff variants · the demoted footnote exhibits.
 *
 * EVERY on-screen number in C6-1..C6-10 comes through here — never hardcoded
 * (OWNER-LOCKED rule; the ARTIFACT wins over teaser copy). The star tables are
 * fed to the field VERBATIM (field.setStarTables) — never re-embedded in the
 * browser (CONTRACT §22.2: a client re-fit could mirror-flip the WPL cluster to
 * the wrong side of the IPL path and destroy the chapter's whole image).
 * Fetched once per session, cached as a module-level promise, always through
 * `$app/paths` base.
 */

/* ---- the constellation (hero 1) ------------------------------------------- */

export interface ConstGroup {
	gi: number;
	label: string;
	league: 'ipl' | 'wpl';
	rr: number;
	season: number;
	sixes_per_100_legal: number;
}

export interface WplThread {
	distance: number;
	nearest_ipl_gi: number;
	nearest_ipl_season: number;
	wpl_gi: number;
	wpl_season: number;
}

export interface TwoTruth {
	outcome_mix_twin: { distance: number; ipl_season: number };
	run_rate_twin: { ipl_rr: number; ipl_season: number; rr_gap: number };
	wpl_rr: number;
	wpl_season: number;
}

export interface ConstellationBlock {
	categories: string[];
	distributions: Record<ConstellationPhase, number[][]>;
	framing: string;
	groups: ConstGroup[];
	ipl_worm: number[];
	method: string;
	phase_overs: Record<Exclude<ConstellationPhase, 'all'>, [number, number]>;
	phase_views: string[];
	/** the four Procrustes-aligned per-phase tables, 23 × (x,y) each — fed VERBATIM */
	stars: Record<ConstellationPhase, [number, number][]>;
	two_truths: TwoTruth[];
	validation: {
		all_wpl_nearest_is_2008: boolean;
		mds_stress: Record<ConstellationPhase, number>;
		procrustes_disparity: Record<Exclude<ConstellationPhase, 'all'>, number>;
		procrustes_disparity_raw: Record<Exclude<ConstellationPhase, 'all'>, number>;
	};
	wpl_gis: number[];
	wpl_threads: Record<ConstellationPhase, WplThread[]>;
}

/* ---- the maturity clock (hero 2) ------------------------------------------ */

export interface MaturitySeries {
	league_years: number[];
	rr: number[];
	seasons: number[];
}

export interface MaturityBlock {
	definition: string;
	headline: {
		equal: boolean;
		ipl_year15_rr: number;
		ipl_year15_season: number;
		text: string;
		wpl_year4_rr: number;
	};
	ipl: MaturitySeries;
	wpl: MaturitySeries;
}

/* ---- run DNA (supporting 1) ----------------------------------------------- */

export interface DnaComposition {
	four: number;
	single: number;
	six: number;
	three: number;
	two: number;
}

export interface RunDnaBlock {
	definition: string;
	eras: Record<string, DnaComposition>;
	headline: {
		four_share: { ipl_modern: number; wpl: number };
		six_share: { ipl_modern: number; wpl: number };
		text: string;
	};
	helix: { ipl_modern: DnaComposition; wpl: DnaComposition };
}

/* ---- stumping signature (supporting 2) ------------------------------------ */

export interface StumpSeason {
	bowled_lbw_pct: number;
	caught_pct: number;
	dismissals: number;
	season: number;
	stumped_pct: number;
}

export interface StumpingBlock {
	definition: string;
	headline: { ipl_2026: number; text: string; wpl_range: [number, number] };
	ipl: StumpSeason[];
	wpl: StumpSeason[];
}

/* ---- photo-finish (supporting 3) ------------------------------------------ */

export interface PhotoEra {
	decided: number;
	pct: number;
	photo_finishes: number;
}

export interface PhotoFinishBlock {
	definition: string;
	headline: { ipl_early: number; ipl_modern: number; text: string; wpl: number };
	ipl_eras: Record<string, PhotoEra>;
	per_season: { ipl: Record<string, PhotoEra>; wpl: Record<string, PhotoEra> };
	wpl_all: PhotoEra;
}

/* ---- the payoff (sister franchise) ---------------------------------------- */

export interface SisterRef {
	league: 'ipl' | 'wpl';
	short: string;
	team: string;
	team_id: number;
}

export interface SharedGround {
	city: string;
	venue: string;
}

export interface PayoffVariant {
	team_id: number | null;
	team: string;
	league: 'ipl' | 'wpl' | 'neutral';
	short: string;
	empty_state: boolean;
	empty_copy?: string;
	sister: SisterRef | null;
	shared_city?: string;
	shared_grounds?: SharedGround[];
	nearest_ipl_star_by_style?: { distance: number; gi: number; ipl_season: number };
}

export interface PayoffBlock {
	card: string;
	definition: string;
	shared_grounds: { city: string; ipl_matches: number; venue: string; wpl_matches: number }[];
	sister_pairs: { ipl: string; ipl_id: number; shared_city: string; wpl: string; wpl_id: number }[];
	variants: PayoffVariant[];
}

/* ---- footnote blocks (the demoted exhibits) ------------------------------- */

export interface Ch6Footnotes {
	competitive_balance: {
		distinct_champions: {
			ipl: { champion: string; distinct_so_far: number; season: number }[];
			wpl: { champion: string; distinct_so_far: number; season: number }[];
		};
		mean_norm_win_hhi: { ipl_early: number; ipl_modern: number; wpl: number };
		note: string;
	};
	powerplay_fear: {
		note: string;
		series: { ipl: Record<string, number>; wpl: Record<string, number> };
	};
	star_gravity: {
		note: string;
		wpl_gini_min30_range: [number, number];
		wpl_gini_unfiltered_range: [number, number];
	};
	twos_culture: {
		ipl_threes_per_match: { early: number; modern: number };
		note: string;
		twos_rate_pct: { ipl_modern: number; wpl: number };
	};
}

export interface BattingLadderBlock {
	bands: Record<string, number[]>;
	definition: string;
	depth: {
		headline: { text: string; wpl_2025_pos7plus: number };
		ipl_early_pooled: number;
		ipl_modern_pooled: number;
		wpl_pooled: number;
	};
	position_labels: string[];
	positions: number[];
}

/* ---- top level ------------------------------------------------------------ */

export interface Ch6Data {
	chapter: number;
	title: string;
	register: string;
	constellation: ConstellationBlock;
	controlling_morph: { note: string; reuses_buffer: string };
	era_bands: { key: string; label: string; league: string; seasons: [number, number] }[];
	maturity_clock: MaturityBlock;
	run_dna: RunDnaBlock;
	stumping: StumpingBlock;
	photo_finish: PhotoFinishBlock;
	payoff: PayoffBlock;
	batting_ladder: BattingLadderBlock;
	footnotes: Ch6Footnotes;
}

/* ---- loader (cached; base-path aware) ------------------------------------- */

let ch6Promise: Promise<Ch6Data> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

export function loadCh6Data(): Promise<Ch6Data> {
	ch6Promise ??= fetchJson<Ch6Data>('/data/scenes/ch6.json');
	return ch6Promise;
}

/* ---- star tables (fed VERBATIM to the field, CONTRACT §22.2) --------------- */

/**
 * The four per-phase star tables straight from the artifact, typed for
 * `field.setStarTables`. NO transform, NO client re-embed — the positions are a
 * Procrustes-aligned lookup; a browser re-fit could mirror-flip the WPL cluster.
 */
export function starTables(d: Ch6Data): Partial<Record<ConstellationPhase, StarTable>> {
	return d.constellation.stars;
}

/* ---- formatters ----------------------------------------------------------- */

/** One decimal ("8.5", "46.8"). */
export const fmt1 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
/** Two decimals ("8.54"). */
export const fmt2 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
/** A percentage rounded to a whole number ("24"). */
export const pct0 = (n: number): number => Math.round(n);
/** Integer with thousands separators. */
export const int = (n: number): string => Math.round(n).toLocaleString('en-US');

/* ---- constellation helpers ------------------------------------------------ */

/** gi → group meta (label / league / rr / season). */
export function groupBy(d: Ch6Data): Map<number, ConstGroup> {
	const m = new Map<number, ConstGroup>();
	for (const g of d.constellation.groups) m.set(g.gi, g);
	return m;
}

/** Plain-word label for a phase ('all' → "every over"; the glossary rule). */
export const PHASE_LABEL: Record<ConstellationPhase, string> = {
	all: 'every over',
	powerplay: 'the first six overs',
	middle: 'the middle overs',
	death: 'the death overs'
};

/** Short chip label per phase (for the toggle indicator). */
export const PHASE_SHORT: Record<ConstellationPhase, string> = {
	all: 'all',
	powerplay: 'first six',
	middle: 'middle',
	death: 'death'
};

/** Same-breath over-range gloss under each phase button (the glossary rule). */
export const PHASE_OVERS: Record<ConstellationPhase, string> = {
	all: 'whole innings',
	powerplay: 'first six overs',
	middle: 'middle overs',
	death: 'last overs'
};

/**
 * Scroll-progress HOLD point for each phase inside the C6-5 phase-cycle, so the
 * phase buttons can drive the SAME scroll channel the glide reads (a keyboard/tap
 * button scrolls the reader to its phase; scroll stays the default driver — no
 * competing field state, no orchestrator revert). Each value sits after its leg's
 * glide (the glide occupies the first ~55% of a leg; see PHASE_LEGS).
 */
export const PHASE_TARGET: Record<ConstellationPhase, number> = {
	all: 0.12,
	powerplay: 0.33,
	middle: 0.53,
	death: 0.73
};

/**
 * The C6-4 phase glide as a PURE function of scroll progress, shared by the
 * scene's dynamicState and the PhaseToggle component so the field star-swap and
 * the on-screen phase chip can never disagree (the ch5 eraFlipState pattern).
 * Cycles all → the first six → the middle → the death overs → back to all, each
 * leg a `from`→`table` mix ramp; the point-to-star assignment never changes, so
 * the WPL cluster glides coherently and never crosses the men's worm (§22.3).
 */
export interface PhaseGlide {
	from: ConstellationPhase;
	table: ConstellationPhase;
	mix: number;
	/**
	 * the phase this step is ABOUT — the leg's target `table` (what the caption
	 * names and the threads point at). The stars glide toward it; the chip labels
	 * the destination so chip, caption and thread-target always agree.
	 */
	shown: ConstellationPhase;
	/** 1..5 caption step */
	step: number;
}

const clamp01 = (t: number): number => Math.min(1, Math.max(0, t));

/** The five phase-cycle legs and their progress windows. */
const PHASE_LEGS: readonly {
	from: ConstellationPhase;
	table: ConstellationPhase;
	lo: number;
	hi: number;
}[] = [
	{ from: 'all', table: 'all', lo: 0, hi: 0.18 },
	{ from: 'all', table: 'powerplay', lo: 0.18, hi: 0.4 },
	{ from: 'powerplay', table: 'middle', lo: 0.4, hi: 0.6 },
	{ from: 'middle', table: 'death', lo: 0.6, hi: 0.8 },
	{ from: 'death', table: 'all', lo: 0.8, hi: 1 }
];

export function phaseGlide(progress: number): PhaseGlide {
	for (let i = 0; i < PHASE_LEGS.length; i++) {
		const leg = PHASE_LEGS[i];
		if (progress < leg.hi || i === PHASE_LEGS.length - 1) {
			// glide occupies the first ~55% of the leg; the rest HOLDS the phase
			const span = leg.hi - leg.lo;
			const mix = clamp01((progress - leg.lo) / (span * 0.55));
			// the chip / caption / thread-target all name the leg's DESTINATION
			return { from: leg.from, table: leg.table, mix, shown: leg.table, step: i + 1 };
		}
	}
	const last = PHASE_LEGS[PHASE_LEGS.length - 1];
	return { from: last.from, table: last.table, mix: 1, shown: last.table, step: PHASE_LEGS.length };
}

/** Caption-step BOUNDS for the phase scene's read-then-watch reveal (§17.4). */
export const PHASE_BOUNDS: readonly number[] = [0, 0.18, 0.4, 0.6, 0.8, 1];

/* ---- payoff resolution (mirrors ch5's variant contract) ------------------- */

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
 * Resolve a reader's pick to their sister-franchise card. Neutral / unknown
 * picks get the neutral variant (deep links always work). Matching is by
 * (league, team name) — the WPL and IPL share franchise names (Mumbai Indians
 * exists in both), so the league is load-bearing.
 */
export function payoffVariantFor(d: Ch6Data, pick: TeamPickLite | null): ResolvedPayoff {
	const neutral = d.payoff.variants.find((v) => v.league === 'neutral') ?? null;
	if (pick === null || pick.league === null || pick.team === 'neutral') {
		return { variant: neutral, kind: 'neutral', fallback: false };
	}
	const exact = d.payoff.variants.find((v) => v.league === pick.league && v.team === pick.team);
	if (exact) return { variant: exact, kind: exact.league === 'neutral' ? 'neutral' : exact.league, fallback: false };
	return { variant: neutral, kind: 'neutral', fallback: true };
}
