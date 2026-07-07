import { base } from '$app/paths';
import type { GroupMeta } from '$lib/field/types';
import type { FieldHandle, RiverTable } from '$lib/field/field';

/**
 * Typed access to Chapter 7's scene artifact:
 *   static/data/scenes/ch7.json — the natural experiment (the twin-rivers run
 *     rates, the diff-in-diff, the impact-sub spark indices), the License Index,
 *     the Rule-Change Event Study (the placebo-cursor grid), the Playbook Decoder,
 *     the honest null + demoted exhibits, and the your-team-playbook payoff.
 *
 * EVERY on-screen number in C7-1..C7-8 comes through here — never hardcoded
 * (OWNER-LOCKED rule; the ARTIFACT wins over the storyboard's teaser copy). The
 * run rates roll up into the per-gi river table fed VERBATIM to the field
 * (field.setRiverTable); the 517 spark point indices feed field.setSparks. The
 * placebo cursor is a LOOKUP over the precomputed event-study grid — never a
 * live fit (blueprint standing rule: anything that looks like a computation is a
 * lookup). Fetched once per session, cached as a module-level promise, always
 * through `$app/paths` base.
 */

/* ---- natural experiment (hero — "the control group") --------------------- */

export interface DiffInDiff {
	estimate: number;
	estimate_immediate: number;
	ipl_delta_vs_band: number;
	ipl_delta_vs_immediate: number;
	ipl_post_mean: number;
	ipl_pre_band_mean: number;
	ipl_pre_immediate_mean: number;
	level_gap_at_treatment: number;
	wpl_delta: number;
	wpl_end: number;
	wpl_start: number;
}

export interface NaturalExperiment {
	confounds: string;
	definition: string;
	diff_in_diff: DiffInDiff;
	headline: {
		did: number;
		ipl_post_sequence: number[];
		text: string;
		wpl_change: number;
	};
	hero_name: string;
	ipl_post: { mean: number; seasons: [number, number]; values: number[] };
	ipl_pre_band: { max: number; mean: number; min: number; seasons: [number, number] };
	/** IPL league run rate keyed by season year (string keys in JSON) */
	ipl_rr: Record<string, number>;
	/** WPL league run rate keyed by season year (2023+) */
	wpl_rr: Record<string, number>;
}

/* ---- controlling morph (the twin rivers) --------------------------------- */

export interface ControllingMorph {
	name: string;
	note: string;
	reuses_buffer: string;
}

/* ---- impact subs (the sparks) -------------------------------------------- */

export interface ImpactSubs {
	activation_note: string;
	by_season: Record<string, number>;
	definition: string;
	n_events: number;
	n_spark_deliveries: number;
	n_sub_usages: number;
	reinforcement: { bat: number; bowl: number };
	spark_encoding: string;
	/** 517 field POINT indices (group_ids.u16 point order) — fed to field.setSparks */
	spark_indices: number[];
	wpl_events: number;
}

/* ---- license index (supporting 1) ---------------------------------------- */

export interface LicensePosition {
	pct_change: number;
	sr_post: number;
	sr_pre: number;
}

export interface LicenseState {
	balls: number;
	bowler_dismissals_per_100: number;
	dismissals: number;
	dismissals_per_100: number;
	runs: number;
	sr: number;
}

export interface LicenseIndex {
	by_position: Record<string, LicensePosition>;
	definition: string;
	headline: {
		dismissals_post: number;
		dismissals_pre: number;
		lower_order_pct_change: number;
		sr_post: number;
		sr_pre: number;
		text: string;
		top_order_pct_change: number;
	};
	honesty: string;
	post: LicenseState;
	pre: LicenseState;
	state: {
		overs: [number, number];
		post_window: [number, number];
		pre_window: [number, number];
		wickets_down_min: number;
	};
}

/* ---- event study (supporting 2 — the placebo cursor) --------------------- */

export interface EventStudyCandidate {
	level_shift: number;
	se: number;
	season: number;
	t: number;
}

export interface EventStudy {
	candidates: EventStudyCandidate[];
	definition: string;
	global_max_shift: number;
	global_max_shift_date: number;
	headline: { placebo_max_shift: number; text: string; true_shift: number };
	note: string;
	placebo_cloud_max_shift: number;
	placebo_cloud_max_t: number;
	placebo_window: [number, number];
	treatment_window: [number, number];
	true_date: number;
	true_date_shift: number;
	true_date_stands_out: boolean;
	true_date_t: number;
}

/* ---- playbook decoder (supporting 3) ------------------------------------- */

export interface PlaybookSeason {
	at_break: number;
	break_pct: number;
	mid_innings: number;
	total: number;
}

export interface Playbook {
	definition: string;
	headline: { break_pct_2023: number; break_pct_2025: number; text: string };
	per_season: Record<string, PlaybookSeason>;
}

/* ---- honest null + demoted exhibits (footnote layer) --------------------- */

export interface EntryEntropy {
	definition: string;
	delta: number;
	flat: boolean;
	per_season: Record<string, number>;
	headline: { entry_post: number; entry_pre: number; text: string };
	post_pooled: number;
	pre_pooled: number;
}

export interface HonestNull {
	entry_entropy: EntryEntropy;
	headline: { entry_post: number; entry_pre: number; text: string };
	part_timer: {
		definition: string;
		per_season: Record<string, number>;
		post_2023: number;
		pre_2022: number;
	};
	tail_exposure: { definition: string; post: number; pre: number };
	top3_sr: { definition: string; post: number; pre: number };
}

/* ---- payoff (your team's playbook) --------------------------------------- */

export interface PayoffVariant {
	team_id: number | null;
	team: string;
	league: 'ipl' | 'wpl' | 'neutral';
	short: string;
	empty_state: boolean;
	headline: string;
	/* IPL fields */
	bat_subs?: number;
	bowl_subs?: number;
	favorite_pattern?: 'bat' | 'bowl';
	most_used_player?: { count: number; name: string };
	timing?: { at_break: number; mid_innings: number };
	total_subs?: number;
	win_rate?: { bat: number; bowl: number };
	/* WPL control-arm flag */
	control_arm?: boolean;
	/* neutral */
	did?: number;
}

export interface PayoffBlock {
	card: string;
	definition: string;
	variants: PayoffVariant[];
}

/* ---- footnote strings ----------------------------------------------------- */

export interface Ch7FootnoteStrings {
	batting_order_fluidity: string;
	diff_in_diff: string;
	part_timer: string;
	replacements_schema: string;
	tail_exposure: string;
}

/* ---- top level ------------------------------------------------------------ */

export interface Ch7Data {
	chapter: number;
	title: string;
	register: string;
	controlling_morph: ControllingMorph;
	event_study: EventStudy;
	footnotes: Ch7FootnoteStrings;
	honest_null: HonestNull;
	impact_subs: ImpactSubs;
	license_index: LicenseIndex;
	mystery_handoff_in: string;
	mystery_handoff_out: string;
	natural_experiment: NaturalExperiment;
	payoff: PayoffBlock;
	playbook: Playbook;
}

/* ---- loader (cached; base-path aware) ------------------------------------- */

let ch7Promise: Promise<Ch7Data> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

export function loadCh7Data(): Promise<Ch7Data> {
	ch7Promise ??= fetchJson<Ch7Data>('/data/scenes/ch7.json');
	return ch7Promise;
}

/* ---- the twin-rivers table (fed to the field, CONTRACT §23.2) ------------- */

/** The "runs an over" axis for the twin-rivers box (world floor / ceiling). */
export const FLOW_RATE_LO = 7;
export const FLOW_RATE_HI = 10;
/** run-rate values the scene labels on the axis */
export const FLOW_AXIS_TICKS = [7, 8, 9, 10];
/** decorative band height as a fraction of the axis (a constant, NOT ball count) */
export const FLOW_BAND_THICKNESS = 0.06;

/**
 * Build the per-gi river table straight from the field's own group metadata
 * (gi → league + season) and ch7.json's league-season run rates. NO transform,
 * no fitted model — each height is a direct corpus run-rate roll-up.
 *
 * `heights[gi]` = the league-season TRUE run rate; `baseHeights[gi]` = the flat
 * counterfactual the river lifts FROM when `flowLift` scrubs 0→1 (C7-3's
 * "line them up flat, then let go"). Only the IPL's TREATMENT years (>= the fork)
 * carry a lower baseline — they lift; every pre-rule IPL season and every WPL
 * season keeps baseHeight == trueHeight, so they never move. The IPL baseline is
 * its immediate pre-rule level (2022), so at flowLift 0 the men's river simply
 * carries its plateau flat into the treatment years.
 */
export function buildRiverTable(groups: GroupMeta[], d: Ch7Data): RiverTable {
	const forkSeason = d.event_study.true_date; // 2023
	const iplRr = d.natural_experiment.ipl_rr;
	const wplRr = d.natural_experiment.wpl_rr;
	// the flat continuation baseline: the IPL's immediate pre-rule (2022) level
	const preForkKey = String(forkSeason - 1);
	const iplBaseline = iplRr[preForkKey] ?? d.natural_experiment.ipl_pre_band.mean;

	let maxGi = 0;
	for (const g of groups) if (g.gi > maxGi) maxGi = g.gi;
	const heights = new Array<number>(maxGi + 1).fill(NaN);
	const baseHeights = new Array<number>(maxGi + 1).fill(NaN);

	for (const g of groups) {
		const table = g.league === 'ipl' ? iplRr : wplRr;
		const rr = table[String(g.season)];
		if (rr == null) continue; // gi has no river (graceful — collapses to centre)
		heights[g.gi] = rr;
		// IPL treatment years lift from the flat plateau; everything else is fixed
		baseHeights[g.gi] = g.league === 'ipl' && g.season >= forkSeason ? iplBaseline : rr;
	}

	return {
		heights,
		baseHeights,
		rateLo: FLOW_RATE_LO,
		rateHi: FLOW_RATE_HI,
		bandThickness: FLOW_BAND_THICKNESS,
		forkSeason,
		axisTicks: FLOW_AXIS_TICKS
	};
}

/**
 * Feed the twin-rivers table to the field ONCE per field instance (idempotent —
 * setRiverTable is self-rendering, so a re-feed is a cheap re-bake). Called by
 * every `flow` scene so a deep link into a supporting beat still shows the dim
 * river backdrop, not the graceful "no table → collapse to centre" blob.
 */
let riverFedFor: FieldHandle | null = null;
export function ensureRiverTable(field: FieldHandle | null, d: Ch7Data | null): void {
	if (!field || !d || riverFedFor === field) return;
	riverFedFor = field;
	field.setRiverTable(buildRiverTable(field.data.groups, d));
}

/** IPL gis in season order, and WPL gis in season order (for the two centrelines). */
export function riverGis(groups: GroupMeta[]): { ipl: number[]; wpl: number[] } {
	const ipl = groups
		.filter((g) => g.league === 'ipl')
		.sort((a, b) => a.season - b.season)
		.map((g) => g.gi);
	const wpl = groups
		.filter((g) => g.league === 'wpl')
		.sort((a, b) => a.season - b.season)
		.map((g) => g.gi);
	return { ipl, wpl };
}

/** League-wide pooled share of impact subs used at the innings break (%), from the
 *  playbook per-season table — the yardstick a team's own break% is read against
 *  (payoff timing-vs-league framing, storyboard C7-8). Artifact-derived, not typed. */
export function leagueBreakPct(pb: Playbook): number {
	let atBreak = 0;
	let total = 0;
	for (const s of Object.values(pb.per_season)) {
		atBreak += s.at_break;
		total += s.total;
	}
	return total > 0 ? (100 * atBreak) / total : 0;
}

/* ---- placebo cursor helpers ---------------------------------------------- */

/** The candidate for a given season year, or null if out of the grid. */
export function candidateFor(es: EventStudy, season: number): EventStudyCandidate | null {
	return es.candidates.find((c) => c.season === season) ?? null;
}

/** True while a season sits inside the grey placebo window (before the rule). */
export function isPlacebo(es: EventStudy, season: number): boolean {
	return season >= es.placebo_window[0] && season <= es.placebo_window[1];
}

/* ---- payoff resolution (mirrors the ch6 variant contract) ----------------- */

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
 * Resolve a reader's pick to their playbook card. Neutral / unknown picks get
 * the neutral variant (deep links always work). Matching is by (league, team
 * name) — the WPL and IPL share franchise names, so the league is load-bearing.
 */
export function payoffVariantFor(d: Ch7Data, pick: TeamPickLite | null): ResolvedPayoff {
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

/** One decimal ("8.5", "129.9"). */
export const fmt1 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
/** Two decimals ("8.99"). */
export const fmt2 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
/** A percentage rounded to a whole number ("52"). */
export const pct0 = (n: number): number => Math.round(n);
/** Integer with thousands separators. */
export const int = (n: number): string => Math.round(n).toLocaleString('en-US');
/** A signed one-decimal delta ("+0.5", "-0.3"). */
export const signed1 = (n: number): string => (n >= 0 ? '+' : '') + fmt1(n);
