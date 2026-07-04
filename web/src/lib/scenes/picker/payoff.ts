import { base } from '$app/paths';
import type { TeamPick } from '$lib/state';

/**
 * Types + loader for `data/payoff/ch1.json` (pipeline-owned, 16 variants:
 * 10 IPL + 5 WPL + Neutral, snapshot-tested). Cards render this JSON —
 * headlines verbatim, numbers untouched; copy changes are pipeline changes
 * (storyboard C1-7). Fetched through `$app/paths` base (contract §8.2) and
 * cached module-wide so any number of cards cost one request.
 */

export interface PayoffEraLabels {
	early: string;
	recent: string;
}

export interface IgnitionEraRow {
	era: string;
	sr_1_10: number | null;
	sr_11_20: number | null;
	balls_1_10: number;
	balls_11_20: number;
}

export interface FastestStarter {
	name: string;
	first10_sr: number;
	first10_balls: number;
}

export interface MaturityClock {
	league_year: number;
	rr_by_year: { ipl: number[]; wpl: number[] };
	first10_sr_by_year: { ipl: number[]; wpl: number[] };
	wpl_runs_from_fours_pct: number;
	ipl_recent_runs_from_fours_pct: number;
	copy: string;
	definition: string;
}

export interface PayoffVariant {
	team: string;
	league: 'ipl' | 'wpl';
	first10_sr_early_era: number | null;
	first10_sr_recent_era: number | null;
	delta: number | null;
	sample_balls: number;
	headline: string;
	era_labels: PayoffEraLabels;
	sample_balls_early: number;
	sample_balls_recent: number;
	empty_state: boolean;
	small_sample: boolean;
	ignition_by_era: IgnitionEraRow[];
	fastest_starter?: FastestStarter;
	maturity_clock?: MaturityClock;
}

export interface PayoffCh1 {
	chapter: number;
	card: string;
	eras: { ipl: PayoffEraLabels; wpl: PayoffEraLabels };
	variants: PayoffVariant[];
}

let cached: Promise<PayoffCh1 | null> | null = null;

/**
 * Load (once) the chapter-1 payoff variants. Resolves to null on any failure —
 * the card renders its designed empty state instead of throwing; a later call
 * retries the fetch.
 */
export function loadPayoffCh1(): Promise<PayoffCh1 | null> {
	cached ??= fetch(`${base}/data/payoff/ch1.json`)
		.then(async (res) => {
			if (!res.ok) throw new Error(`payoff/ch1.json → HTTP ${res.status}`);
			const json = (await res.json()) as PayoffCh1;
			if (!Array.isArray(json.variants) || json.variants.length === 0)
				throw new Error('payoff/ch1.json: no variants');
			return json;
		})
		.catch((err: unknown) => {
			console.warn(
				'[every-ball-ever] payoff/ch1.json unavailable — payoff cards render their designed empty state.',
				err
			);
			cached = null; // allow a retry
			return null;
		});
	return cached;
}

export interface ResolvedPayoff {
	variant: PayoffVariant;
	/** which card template applies */
	kind: 'ipl' | 'wpl' | 'neutral';
	/** true when the pick named a team with no variant and we fell back to Neutral */
	fallback: boolean;
}

/**
 * Map a reader's pick (or its absence — deep links always work) to a card
 * variant. Unknown teams degrade to the Neutral league-wide card with a flag
 * so the template can say so.
 */
export function payoffVariantFor(payoff: PayoffCh1, pick: TeamPick | null): ResolvedPayoff | null {
	const neutral = payoff.variants.find((v) => v.team === 'Neutral') ?? null;
	if (pick === null || pick.league === null || pick.team === 'neutral') {
		return neutral ? { variant: neutral, kind: 'neutral', fallback: false } : null;
	}
	const exact = payoff.variants.find((v) => v.league === pick.league && v.team === pick.team);
	if (exact) {
		return { variant: exact, kind: exact.league === 'wpl' ? 'wpl' : 'ipl', fallback: false };
	}
	return neutral ? { variant: neutral, kind: 'neutral', fallback: true } : null;
}
