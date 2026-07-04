import { base } from '$app/paths';

/**
 * Typed access to Chapter 1's scene artifact:
 *   static/data/scenes/ch1.json  — ignition / out-rate / defiers / sixes /
 *                                  aerial / WPL-beat numbers
 *
 * (The payoff-card artifact, payoff/ch1.json, is owned by the picker
 * directory's reusable card — $lib/scenes/picker/payoff.ts — which C1-7
 * renders through; see CONTRACT §7.)
 *
 * Every on-screen number in C1-1..C1-8 comes through here (or, where the
 * artifact lacks a value, from the storyboard §9 verified-number index —
 * those constants are flagged at their use sites). Fetched once per session,
 * cached as module-level promises, always through `$app/paths` base.
 */

/* ---- scenes/ch1.json ------------------------------------------------------ */

export type BandKey =
	| 'ipl 2008-2010'
	| 'ipl 2011-2015'
	| 'ipl 2016-2019'
	| 'ipl 2020-2022'
	| 'ipl 2023-2026'
	| 'wpl 2023-2026';

/** the era-ghost convention: 2008-10 grey, 2023-26 bold, WPL its own hue */
export const GHOST_BAND: BandKey = 'ipl 2008-2010';
export const BOLD_BAND: BandKey = 'ipl 2023-2026';
export const WPL_BAND: BandKey = 'wpl 2023-2026';

export interface EraBand {
	key: BandKey;
	label: string;
	league: 'ipl' | 'wpl';
	seasons: number[];
}

export interface DefierEntry {
	name: string;
	survival_pct: number;
	sr_through_ball: number;
	innings: number;
	balls_in_band: number;
	score: number;
}

export interface SeasonSixes {
	season: number;
	sixes: number;
	/** legal balls bowled that season (wides AND no-balls excluded) — the six denominator */
	legal_balls: number;
	/** legal balls per six (the honest per-ball rate; caption quotes round(): 21 → 12) */
	balls_per_six: number;
	players_10plus_sixes: number;
	top10_share_pct: number;
}

/**
 * The ball-index x-axis convention (pipeline `ball_index_axis`), shared by the
 * out-rate strip and the WPL strike-rate panel. The per-ball curves run over the
 * batter's exact n-th ball, n = min..max; `max_is_capped` is FALSE for these
 * strips (index 30 is exactly ball 30, not a 30+ aggregate — capping the
 * discrete hazard there would spike it), so their right edge is labelled
 * `max_label` ("30"). Only the ignition wall caps (`wall_capped_label` = "30+").
 * Every axis label traces here instead of a hardcoded literal.
 */
export interface BallIndexAxis {
	min: number;
	max: number;
	max_is_capped: boolean;
	max_label: string;
	wall_capped_index: number;
	wall_capped_label: string;
	note: string;
}

export interface Ch1Data {
	era_bands: EraBand[];
	ball_index_axis: BallIndexAxis;
	ignition: {
		definition: string;
		sr_by_ball_index: Record<BandKey, number[]>;
		balls_by_ball_index: Record<BandKey, number[]>;
		first10_sr_by_season: {
			ipl: Record<string, number>;
			wpl: Record<string, number>;
		};
	};
	outrate: {
		definition: string;
		hazard_pct_by_ball_index: Record<BandKey, number[]>;
		dismissed_at_ball_index: Record<BandKey, number[]>;
		reaching_by_ball_index: Record<BandKey, number[]>;
		first10: Record<BandKey, { balls: number; events: number; hazard_pct: number }>;
		sample_sizes: Record<BandKey, { balls_1_10: number; batter_innings: number }>;
	};
	defiers: {
		definition: string;
		bands: Record<
			BandKey,
			{
				baselines: Record<string, { sr_through_ball: number; survival_pct: number }>;
				by_ball_index: Record<string, DefierEntry[]>;
			}
		>;
	};
	sixes: {
		definition: string;
		seasons: { ipl: SeasonSixes[]; wpl: SeasonSixes[] };
	};
	aerial: {
		caveat: string;
		bands: Record<
			BandKey,
			{
				attempts_per_100_balls: number;
				execution_pct: number;
				balls: number;
				sixes: number;
				caught_excl_cb: number;
			}
		>;
	};
	wpl_beat: {
		first10_sr: { ipl_2008_2010: number; wpl_2023_2026: number };
		runs_from_fours_pct: { ipl_2023_2026: number; wpl_2023_2026: number };
		runs_from_sixes_pct: { ipl_2023_2026: number; wpl_2023_2026: number };
		maturity_clock: {
			definition: string;
			league_years: number[];
			rr: { ipl: number[]; wpl: number[] };
			first10_sr: { ipl: number[]; wpl: number[] };
		};
	};
}

/* ---- loaders (cached; base-path aware) -------------------------------------- */

let ch1Promise: Promise<Ch1Data> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

export function loadCh1Data(): Promise<Ch1Data> {
	ch1Promise ??= fetchJson<Ch1Data>('/data/scenes/ch1.json');
	return ch1Promise;
}

/* ---- derived numbers --------------------------------------------------------- */

/**
 * Pooled strike rate across a balls-faced range (runs recovered from the
 * per-index SR × balls, so the pooled figure is ball-weighted — this
 * reconciles exactly with the catalog teasers: 108.0 → 135.3, WPL 110.5).
 */
export function pooledSr(d: Ch1Data, band: BandKey, fromBall = 1, toBall = 10): number {
	const sr = d.ignition.sr_by_ball_index[band];
	const balls = d.ignition.balls_by_ball_index[band];
	let runs = 0;
	let n = 0;
	for (let i = fromBall - 1; i < toBall && i < sr.length; i++) {
		runs += (sr[i] * balls[i]) / 100;
		n += balls[i];
	}
	return n > 0 ? (100 * runs) / n : 0;
}

/** Format helpers — tabular figures, en-US separators (storyboard §0.1). */
export const fmt1 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
export const fmt2 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/**
 * C1-5 two-tone gate (shared between Fireworks.svelte and the ch1-sixes scene
 * def's `dynamicState`). The step-3 recolor reads `attrs.u8` bit 5 (= hit by
 * that season's top-10 six-hitter). Until the pipeline re-encodes that bit it
 * reads 0 everywhere, and the shader's `mix(1.0, top10 ? 1.4 : 0.5, tint)` would
 * dim EVERY six uniformly (reads as "zero specialists") — a pixels-vs-copy
 * miss. Fireworks scans the buffer once, sets `available`, and the scene def
 * only raises `resort.tint` (and the caption only shows the "watch the slice
 * shrink" line) when it is true. When the pipeline ships the bit, the two-tone
 * lights up with no code change on the animated path (see integration notes).
 */
export const twoTone = { available: false };
