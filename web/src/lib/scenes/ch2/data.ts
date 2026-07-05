import { base } from '$app/paths';

/**
 * Typed access to Chapter 2's scene artifact:
 *   static/data/scenes/ch2.json — anchor extinction · archetype occupancy ·
 *     gear-shift · new-batter tax · run-out extinction + break-even · worm
 *     exemplars (par + K anchor worms per exemplar season) · WPL two-clock ·
 *     per-franchise "last anchor" payoff variants (incl. designed empty states).
 *
 * EVERY on-screen number in C2-1..C2-9 comes through here — never hardcoded
 * (OWNER-LOCKED rule). Where the storyboard's teaser copy and the emitted
 * artifact disagree (e.g. run-out 4.6 vs 4.7, occupancy 38.7 vs 39.3, tax
 * 1.22 vs 1.13), the ARTIFACT wins — the pipeline JSON is the source of truth
 * (storyboard §3 / §5.9 reconciliation rule). Fetched once per session, cached
 * as a module-level promise, always through `$app/paths` base.
 */

/* ---- band keys + era bands (shared with ch1's convention) ----------------- */

export type BandKey =
	| 'ipl 2008-2010'
	| 'ipl 2011-2015'
	| 'ipl 2016-2019'
	| 'ipl 2020-2022'
	| 'ipl 2023-2026'
	| 'wpl 2023-2026';

/** the era-band shorthand the chapter cites in the main flow */
export const IPL_EARLY: BandKey = 'ipl 2008-2010';
export const IPL_MODERN: BandKey = 'ipl 2023-2026';
export const WPL_BAND: BandKey = 'wpl 2023-2026';

export interface EraBand {
	key: BandKey;
	label: string;
	league: 'ipl' | 'wpl';
	seasons: number[];
}

/* ---- anchor extinction (hero #1) ------------------------------------------ */

export interface AnchorBand {
	anchor_ball_share_pct: number;
	anchor_balls: number;
	total_balls: number;
}

export interface AnchorSeason {
	season: number;
	anchor_ball_share_pct: number;
	anchor_balls: number;
	prolific_players: number;
	total_balls: number;
}

export interface AnchorBlock {
	definition: string;
	bands: Record<BandKey, AnchorBand>;
	penalty: Record<BandKey, { with_anchor: { n: number; win_pct: number }; without_anchor: { n: number; win_pct: number } }>;
	seasons: { ipl: AnchorSeason[]; wpl: AnchorSeason[] };
}

/* ---- archetype occupancy (sub-120 raw cut — footnote only) ---------------- */

export interface ArchetypeBand {
	qualifiers: number;
	sub120: number;
	sub120_share_pct: number;
}

export interface ArchetypeBlock {
	definition: string;
	bands: Record<BandKey, ArchetypeBand>;
	seasons: { ipl: { season: number; qualifiers: number; sub120: number; sub120_share_pct: number }[]; wpl: unknown[] };
}

/* ---- gear-shift ----------------------------------------------------------- */

export interface GearBand {
	flat_max_share_pct: number;
	three_act_share_pct: number;
	two_act_share_pct: number;
	innings: number;
}

export interface GearBlock {
	definition: string;
	bands: Record<BandKey, GearBand>;
	seasons: { ipl: unknown[]; wpl: unknown[] };
}

/* ---- new-batter tax (the sole coda) --------------------------------------- */

export interface TaxBand {
	actual_rpo: number;
	par_rpo: number;
	tax_rpo_below_par: number;
	window_balls: number;
}

export interface NewBatterBlock {
	definition: string;
	incoming_first5_sr: Record<BandKey, { balls: number; first5_sr: number }>;
	tax: Record<BandKey, TaxBand>;
}

/* ---- run-out extinction (hero #2) ----------------------------------------- */

export interface RunoutSeason {
	season: number;
	dismissals: number;
	run_outs: number;
	runout_share_pct: number;
}

export interface RunoutBlock {
	definition: string;
	break_even_running: Record<BandKey, { runouts_per_1000_legal: number; twos_per_100_nonboundary: number }>;
	striker_split: Record<BandKey, { striker: number; non_striker: number; non_striker_pct: number }>;
	seasons: { ipl: RunoutSeason[]; wpl: RunoutSeason[] };
}

/* ---- worm exemplars (the controlling morph's SVG overlays) ---------------- */

export interface WormExemplar {
	batter: string;
	team: string;
	opponent: string;
	season: number;
	date: string;
	balls: number;
	runs: number;
	sr: number;
	boundary_pct: number;
	par_sr: number;
	/** cumulative batter runs after each ball faced (length = balls) */
	cum_runs: number[];
}

export interface WormSeason {
	season: number;
	/** mean cumulative runs of the season's average batter, by ball faced */
	par_worm: number[];
	exemplars: WormExemplar[];
}

export interface WormBlock {
	definition: string;
	seasons: WormSeason[];
}

/* ---- WPL two-clock beat --------------------------------------------------- */

export interface WplBeat {
	anchor_ball_share_pct: number;
	ipl_modern_anchor_ball_share_pct: number;
	runout_share_pct: number;
	ipl_start_runout_share_pct: number;
	ipl_modern_runout_share_pct: number;
	anchor_ball_share_by_season: Record<string, number>;
	runout_share_by_season: Record<string, number>;
	two_clocks_note: string;
}

/* ---- payoff ("your last anchor") ------------------------------------------ */

export interface AnchorVariant {
	team: string;
	league: 'ipl' | 'wpl';
	batter: string;
	opponent: string;
	venue: string;
	date: string;
	season: number;
	balls: number;
	runs: number;
	sr: number;
	boundary_pct: number;
	par_sr: number;
	/** cumulative batter runs after each ball (the replayable worm) */
	cum_runs: number[];
	empty_state: boolean;
	/**
	 * how many top-order qualifying anchor innings the SAME league produced in
	 * this innings' season — the rarity signal that reframes "last anchor" as
	 * "one of only N that whole season" (null on the designed empty state).
	 */
	season_anchor_innings: number | null;
	/** the pipeline's verbatim headline sentence — rendered, never parsed */
	headline: string;
}

export interface PayoffBlock {
	card: string;
	definition: string;
	variants: AnchorVariant[];
}

/* ---- top level ------------------------------------------------------------ */

export interface Ch2Data {
	chapter: number;
	title: string;
	register: string;
	era_bands: EraBand[];
	anchor: AnchorBlock;
	archetype: ArchetypeBlock;
	gearshift: GearBlock;
	newbatter: NewBatterBlock;
	runout: RunoutBlock;
	worms: WormBlock;
	wpl_beat: WplBeat;
	payoff: PayoffBlock;
	par_model: { definition: string; integration_note: string; phases: string[] };
}

/* ---- loader (cached; base-path aware) ------------------------------------- */

let ch2Promise: Promise<Ch2Data> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

export function loadCh2Data(): Promise<Ch2Data> {
	ch2Promise ??= fetchJson<Ch2Data>('/data/scenes/ch2.json');
	return ch2Promise;
}

/* ---- derived helpers ------------------------------------------------------ */

/** Tabular figures, one decimal (12.3, 8.5). */
export const fmt1 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
export const fmt2 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export const int = (n: number): string => n.toLocaleString('en-US');

/** IPL run-out share for a season year (the extinction curve's points). */
export function runoutSeasonPct(d: Ch2Data, season: number): number | null {
	const row = d.runout.seasons.ipl.find((s) => s.season === season);
	return row ? row.runout_share_pct : null;
}

/** IPL anchor ball-share for a season year (the conservation curve's points). */
export function anchorSeasonPct(d: Ch2Data, season: number): number | null {
	const row = d.anchor.seasons.ipl.find((s) => s.season === season);
	return row ? row.anchor_ball_share_pct : null;
}

/**
 * The IPL era-band anchor ball-share containing a season year — the 14.8→8.5
 * magnitude the C2-3 caption actually cites. The drawn thicket is pinned to
 * THIS (not the noisier single-season share), so the illustrative worm-count
 * ratio tracks the cited band ratio rather than a low outlier season (§7 audit).
 */
export function anchorBandShareForSeason(d: Ch2Data, season: number): number | null {
	const band = d.era_bands.find(
		(b) => b.league === 'ipl' && season >= b.seasons[0] && season <= b.seasons[b.seasons.length - 1]
	);
	return band ? (d.anchor.bands[band.key]?.anchor_ball_share_pct ?? null) : null;
}

/**
 * The exemplar seasons the C2-2 morph and C2-3 thinning draw over the haze —
 * one par worm + K anchor worms each, K PINNED to the season's emitted anchor
 * ball-share (the drawn thinning tracks the 14.8→8.5 ratio the caption cites),
 * floored at 1, capped for legibility. The thicket is illustrative — labeled
 * "a sample of that season's anchors," never a headcount (storyboard §5.3).
 */
export interface ExemplarSeason {
	season: number;
	share: number | null;
	/** how many anchor worms to draw this season (K, pinned to share) */
	k: number;
	parWorm: number[];
	exemplars: WormExemplar[];
}

/** Legibility cap on the drawn anchor-worm thicket (owner-tunable, §5.3). */
export const WORM_THICKET_CAP = 4;

export function exemplarSeasons(d: Ch2Data): ExemplarSeason[] {
	const seasons = d.worms.seasons;
	// pin to the ERA-BAND share the caption cites (14.8→8.5), not the noisier
	// single-season share — so a low outlier season (2026 = 6.7%) can't make the
	// final thicket read thinner than the cited 8.5% band (§7 audit).
	const shares = seasons.map((s) => anchorBandShareForSeason(d, s.season) ?? 0);
	const maxShare = Math.max(...shares, 1);
	return seasons.map((s, i) => {
		const share = shares[i];
		// K pinned to the cited band-share ratio, floor 1, cap for legibility
		const k = Math.max(1, Math.min(WORM_THICKET_CAP, Math.round((WORM_THICKET_CAP * shares[i]) / maxShare)));
		return { season: s.season, share, k, parWorm: s.par_worm, exemplars: s.exemplars };
	});
}

/**
 * Resolve a reader's pick to their "last anchor" variant. Unknown/neutral picks
 * fall back to the Neutral league-wide card (deep links always work). Mirrors
 * the ch1 payoffVariantFor contract.
 */
export interface TeamPickLite {
	league: 'ipl' | 'wpl' | null;
	team: string;
}

export interface ResolvedAnchor {
	variant: AnchorVariant;
	kind: 'ipl' | 'wpl' | 'neutral';
	fallback: boolean;
}

export function anchorVariantFor(d: Ch2Data, pick: TeamPickLite | null): ResolvedAnchor | null {
	const neutral = d.payoff.variants.find((v) => v.team === 'Neutral') ?? null;
	if (pick === null || pick.league === null || pick.team === 'neutral') {
		return neutral ? { variant: neutral, kind: 'neutral', fallback: false } : null;
	}
	const exact = d.payoff.variants.find((v) => v.league === pick.league && v.team === pick.team);
	if (exact) return { variant: exact, kind: exact.league === 'wpl' ? 'wpl' : 'ipl', fallback: false };
	return neutral ? { variant: neutral, kind: 'neutral', fallback: true } : null;
}
