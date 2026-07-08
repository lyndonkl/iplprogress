import { base } from '$app/paths';
import type { FieldHandle } from '$lib/field/field';

/**
 * Typed access to Chapter 9's scene artifact:
 *   static/data/scenes/ch9.json, THE LIVING LEAGUE. The 277-player / 1,691-duel
 *     rivalry web (the controlling morph, free -> duelweb), the per-duel ball-by-
 *     ball replay lists, the auction heartbeat (five synchronized mega-auction
 *     flatlines), the one-club loyalty spectrum, the WPL forming-fast thread, and
 *     the 16-variant "your team through the churn" payoff.
 *   static/data/pairing.u16, the per-point duel id (0xFFFF = dust), fed to the
 *     field as a data texture so the field holds at 14 vertex attributes (§26.2).
 *
 * EVERY on-screen number in C9-1..C9-9 comes through here, never hardcoded
 * (OWNER-LOCKED rule; the ARTIFACT wins over the storyboard's teaser copy). Three
 * honest deltas ship straight, never fudged toward a teaser: 232 duels ran eight
 * seasons or longer (not 235), one-club players roughly halved from about 27 in
 * 100 to about 12 (not 28 to 15), and the mega-auction trough averages 0.186.
 *
 * The web is fed VERBATIM to the field (field.setDuelGraph) with NO [0,1] remap:
 * the pipeline already emits normalized [-1,1] node and strand-midpoint
 * coordinates (the field's shader convention), unlike Ch 8's [0,1] centroids.
 * Fetched once per session, cached as module-level promises, always through
 * `$app/paths` base.
 */

/* ---- the duel web (the controlling morph) --------------------------------- */

export interface DuelNode {
	/** person-id (stable) */
	id: string;
	name: string;
	/** normalized world x in [-1,1] (the field's shader frame, no remap) */
	x: number;
	/** normalized world y in [-1,1] */
	y: number;
	/** how many duels this player is in (the "hub" size, never drawn as a stat) */
	deg: number;
	/** activity-weighted mean season (era; carried by POSITION, never a hue) */
	era: number;
	league: 'ipl' | 'wpl';
}

export interface Duel {
	/** stable duel id 0..1690 (index into replays[]); sorted by balls DESC, duel 0 = Kohli-Jadeja */
	id: number;
	/** node index of the batter */
	a: number;
	/** node index of the bowler */
	b: number;
	bat: string;
	bowl: string;
	balls: number;
	runs: number;
	/** bowler-credited dismissals of the batter in this pairing */
	dis: number;
	/** distinct seasons the pair actually faced a ball */
	seasons: number;
	/** [first, last] season the pair met */
	span: [number, number];
	/** empirical-Bayes-shrunk runs a ball for the pair */
	dom: number;
	/** dominance color in [-1,1]; +1 batter-red, -1 bowler-blue */
	color: number;
	/** strand-midpoint cluster centre x in [-1,1] (where this duel's balls pile) */
	px: number;
	/** strand-midpoint cluster centre y in [-1,1] */
	py: number;
}

export interface DuelWebMeta {
	n_duels: number;
	n_nodes: number;
	n_men: number;
	n_women: number;
	duel_min_balls: number;
	components: number[];
	balls_split: {
		total_points: number;
		in_duel_points: number;
		dust_points: number;
		faced_balls_total: number;
		faced_balls_in_duels: number;
	};
	dominance_color: { center_mu: number; half_range: number; note: string };
	eb: { mu: number; sigma2: number; tau2: number; k: number; n_pairs: number; n_balls: number };
	force: Record<string, unknown>;
	legibility: Record<string, unknown>;
}

export interface DuelWeb {
	meta: DuelWebMeta;
	nodes: DuelNode[];
	duels: Duel[];
}

/* ---- the tap-a-duel replay lists (index == duel id) ----------------------- */

export interface Replay {
	/** one code per faced ball, in bowling order: 0..6 runs off the bat, 7 = wicket */
	c: number[];
	/** [season, count] run-length blocks for the strip's season separators */
	sb: [number, number][];
}

/* ---- the auction heartbeat (2D telemetry) --------------------------------- */

export interface HeartSeason {
	season: number;
	mean: number;
	/** min-max envelope (lowest / highest single team that season) */
	lo: number;
	hi: number;
	n: number;
}

export interface HeartbeatIpl {
	series: HeartSeason[];
	mega_years: number[];
	mega_mean: number;
	nonmega_mean: number;
	resting: number;
	trough: number;
	sixth_lowest: { season: number; mean: number };
	y_domain: [number, number];
}

export interface HeartbeatWpl {
	series: HeartSeason[];
	first_reset: { season: number; mean: number };
}

export interface Heartbeat {
	ipl: HeartbeatIpl;
	wpl: HeartbeatWpl;
	definition: string;
}

/* ---- the loyalty spectrum (2D) -------------------------------------------- */

export interface LoyaltyPoint {
	season: number;
	pct: number;
	one_club: number;
	veterans: number;
}

export interface MaxShirts {
	id: string;
	name: string;
	n: number;
	teams: string[];
	shorts: string[];
}

export interface Loyalty {
	series: LoyaltyPoint[];
	start: LoyaltyPoint;
	end: LoyaltyPoint;
	peak: LoyaltyPoint;
	trough: LoyaltyPoint;
	span: { start: LoyaltyPoint; end: LoyaltyPoint };
	y_domain: [number, number];
	max_shirts: MaxShirts;
	definition: string;
}

/* ---- the WPL forming-fast thread ------------------------------------------ */

export interface WplThreadData {
	n_players: number;
	n_duels: number;
	age_matched: { at_seasons: number; wpl_duels_by_season3: number; ipl_duels_by_season3: number };
	heartbeat: HeartbeatWpl;
	framing: string;
}

/* ---- Collapse Contagion (demoted to the footnote) ------------------------- */

export interface Collapse {
	aftershock: number;
	cond_rate: number;
	base_rate: number;
	n_after_wicket: number;
	note: string;
}

/* ---- the payoff (your team through the churn, 16 variants) ----------------- */

export interface PayoffRivalry {
	duel_id: number;
	bat: string;
	bowl: string;
	balls: number;
	seasons?: number;
	span: [number, number];
	runs?: number;
	dis?: number;
	color: number;
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
	rivalry: PayoffRivalry;
	/* IPL */
	reset?: { year: number; out: number; in: number; kept: number };
	loyalist?: { name: string; seasons: number };
	/* WPL bespoke */
	bespoke?: boolean;
	forming_fast?: boolean;
	duel_count?: number;
	/* neutral */
	mega_years?: number[];
	loyalty_start?: number;
	loyalty_end?: number;
}

export interface PayoffBlock {
	card: string;
	definition: string;
	variants: PayoffVariant[];
}

/* ---- footnotes + controlling morph + top level ---------------------------- */

export interface Ch9Footnote {
	text: string;
}

export interface ControllingMorph {
	name: string;
	layout_code: number;
	new_buffer: string;
	note: string;
}

export interface Ch9Data {
	chapter: number;
	title: string;
	register: string;
	mystery_handoff_in: string;
	mystery_handoff_out: string;
	controlling_morph: ControllingMorph;
	duel_web: DuelWeb;
	replays: Replay[];
	heartbeat: Heartbeat;
	loyalty: Loyalty;
	wpl: WplThreadData;
	collapse: Collapse;
	payoff: PayoffBlock;
	footnotes: Record<string, Ch9Footnote>;
}

/* ---- loader (cached; base-path aware) ------------------------------------- */

let ch9Promise: Promise<Ch9Data> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

export function loadCh9Data(): Promise<Ch9Data> {
	ch9Promise ??= fetchJson<Ch9Data>('/data/scenes/ch9.json');
	return ch9Promise;
}

/* ---- the duel graph (fed to the field, CONTRACT §26.2) -------------------- */

/** One duel strand for readback / SVG drawing (a subset of Duel, the §26.4 edge). */
export interface DuelEdge {
	id: number;
	a: number;
	b: number;
	bat: string;
	bowl: string;
	balls: number;
	dom: number;
	color: number;
	span: [number, number];
}

/** The argument to `field.setDuelGraph` (§26.2, fed ONCE before the morph engages). */
export interface DuelGraphInput {
	/** pairing.u16: per-point duel id (0xFFFF = dust), aligned with group_ids.u16 */
	pairing: Uint16Array;
	/** the 1,691 duels (px/py strand-midpoint + color), baked into uDuelTex */
	duels: Duel[];
	/** the 277 player nodes (x/y world position), stored for getDuelWebLayout readback */
	nodes: DuelNode[];
	/** the duel edge list (a,b node indices + balls + dom), stored for readback */
	edges: DuelEdge[];
}

/**
 * The world-space duel-web geometry `field.getDuelWebLayout()` returns (§26.4),
 * rebuilt on resize and re-read after each applyState. `null` before the first
 * resize OR before `setDuelGraph`. Scenes project the node world coordinates
 * through `field.projectToCss` to draw the SVG strands, player dots, tap targets
 * and the tap-a-duel replay strip; the field itself draws no lines.
 */
export interface DuelWebLayoutNode {
	x: number;
	y: number;
	name: string;
	deg: number;
	era: number;
	league: 'ipl' | 'wpl';
}

export interface DuelWebLayout {
	nodes: DuelWebLayoutNode[];
	edges: DuelEdge[];
	left: number;
	width: number;
	bottom: number;
	height: number;
	halfExtent: number;
}

/** Derive the §26.4 edge list from the emitted duels (each duel IS one strand). */
export function duelEdges(d: Ch9Data): DuelEdge[] {
	return d.duel_web.duels.map((x) => ({
		id: x.id,
		a: x.a,
		b: x.b,
		bat: x.bat,
		bowl: x.bowl,
		balls: x.balls,
		dom: x.dom,
		color: x.color,
		span: x.span
	}));
}

/* the per-point pairing buffer (pairing.u16), fetched once and cached */
let pairingPromise: Promise<Uint16Array> | null = null;
function loadPairing(): Promise<Uint16Array> {
	pairingPromise ??= (async () => {
		const res = await fetch(`${base}/data/pairing.u16`);
		if (!res.ok) throw new Error(`pairing.u16: HTTP ${res.status}`);
		const buf = await res.arrayBuffer();
		return new Uint16Array(buf);
	})();
	return pairingPromise;
}

/**
 * Feed the duel graph to the field ONCE per field instance (idempotent; a re-feed
 * just re-bakes the pairing / duel data textures). Called by every duel-web scene
 * so a deep link into a later beat still resolves the web, not the free scatter.
 * Fetches pairing.u16, then hands the field the pairing + duels + nodes + edges.
 */
let duelGraphFedFor: FieldHandle | null = null;
export function ensureDuelGraph(field: FieldHandle | null, d: Ch9Data | null): void {
	if (!field || !d || duelGraphFedFor === field) return;
	duelGraphFedFor = field;
	loadPairing()
		.then((pairing) => {
			field.setDuelGraph({
				pairing,
				duels: d.duel_web.duels,
				nodes: d.duel_web.nodes,
				edges: duelEdges(d)
			});
		})
		.catch((err) => {
			// a failed pairing fetch leaves the web un-fed (graceful, the field renders
			// the free scatter); log in dev so the miss is visible.
			duelGraphFedFor = null;
			if (import.meta.env.DEV) console.warn('[ch9] pairing.u16 feed failed:', err);
		});
}

/* ---- duel selection helpers ---------------------------------------------- */

/** The hero rivalry, duel 0 (Kohli vs Jadeja), sorted first by ball count. */
export function heroDuel(d: Ch9Data): Duel {
	return d.duel_web.duels[0];
}

/**
 * The top-N strands by ball count. The duels are emitted sorted by balls DESC, so
 * the top tier is a prefix; the render mock proved ~60 is legible and all-1,691 is
 * a hairball, so scenes cap the bright tier here (mobile passes a smaller n).
 */
export function topDuels(d: Ch9Data, n: number): Duel[] {
	return d.duel_web.duels.slice(0, Math.max(0, n));
}

/** The long duels: those that ran 8+ seasons. Count is the honest delta, 232. */
export function longDuels(d: Ch9Data): Duel[] {
	return d.duel_web.duels.filter((x) => x.seasons >= 8);
}

/** The four busiest hubs, most duels first (V Kohli 76, S Dhawan 65, ...). */
export function topHubs(d: Ch9Data, n: number): DuelNode[] {
	return d.duel_web.nodes
		.slice()
		.sort((p, q) => q.deg - p.deg)
		.slice(0, n);
}

/* ---- payoff resolution (mirrors the ch7 / ch8 variant contract) ----------- */

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
 * Resolve a reader's pick to their "through the churn" card. Neutral / unknown
 * picks get the neutral variant (deep links always work). Matching is by (league,
 * team name), the WPL and IPL share franchise names, so the league is load-bearing.
 */
export function payoffVariantFor(d: Ch9Data, pick: TeamPickLite | null): ResolvedPayoff {
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

/* ---- the dominance hue (batter-red <-> bowler-blue), red = runs ----------- */

/* Deliberately red-vs-blue (not red-vs-green) so "who came out on top" survives
   red-green colorblindness (invariant 9); the poles carry a clear LIGHTNESS delta
   and the neutral gray sits between them. The value is EB-shrunk, so most strands
   land pale near the gray: saturation reads as how one-sided a duel was, and a
   pale strand was an even fight (the copy teaches this, never a red-or-blue binary). */
const DOM_RED: [number, number, number] = [255, 106, 77]; // batter came out on top
const DOM_BLUE: [number, number, number] = [74, 163, 255]; // bowler came out on top
const DOM_NEUTRAL: [number, number, number] = [151, 161, 184]; // an even fight (pale)

/**
 * Map a duel's dominance color in [-1,1] to a CSS rgb() string on the batter-red
 * (+1) <-> bowler-blue (-1) diverging ramp. Interpolates from the neutral gray
 * toward a pole by |color|, so a near-even duel stays pale and a one-sided duel
 * runs deep. `mute` fades it toward the neutral gray for receded / non-focus strands.
 */
export function dominanceColor(color: number, mute = 0): string {
	const t = Math.min(1, Math.abs(color)) * (1 - Math.min(1, Math.max(0, mute)));
	const pole = color >= 0 ? DOM_RED : DOM_BLUE;
	const r = Math.round(DOM_NEUTRAL[0] + (pole[0] - DOM_NEUTRAL[0]) * t);
	const g = Math.round(DOM_NEUTRAL[1] + (pole[1] - DOM_NEUTRAL[1]) * t);
	const b = Math.round(DOM_NEUTRAL[2] + (pole[2] - DOM_NEUTRAL[2]) * t);
	return `rgb(${r}, ${g}, ${b})`;
}

/** The batter-red pole (for the legend swatch). */
export const BATTER_RED = `rgb(${DOM_RED.join(', ')})`;
/** The bowler-blue pole (for the legend swatch). */
export const BOWLER_BLUE = `rgb(${DOM_BLUE.join(', ')})`;

/**
 * A strand's base opacity, weighted by ball count (the layout's own edge weight
 * log1p(balls)/log1p(30), normalized against a 160-ball hero) so light duels fade
 * first and the heavy rivalries carry the frame. Clamped to a legible floor/ceiling.
 */
export function strandOpacity(balls: number): number {
	const w = Math.log1p(balls) / Math.log1p(160);
	return Math.min(0.95, Math.max(0.25, 0.25 + 0.7 * w));
}

/* ---- replay helpers ------------------------------------------------------- */

/** True for a wicket code (7); the strip draws a redundant SHAPE, never color alone. */
export const isWicket = (code: number): boolean => code === 7;
/** Runs off the bat for a code (0..6); a wicket (7) scores 0 off the bat. */
export const runsOff = (code: number): number => (code <= 6 ? code : 0);

/* ---- formatters ----------------------------------------------------------- */

/** Integer with thousands separators ("316,199"). */
export const int = (n: number): string => Math.round(n).toLocaleString('en-US');
/** A percentage rounded to a whole number ("27"), for the "N in 100" reads. */
export const pct0 = (n: number): number => Math.round(n);
/** A 0..1 share rendered as a whole "N in 100" number ("46" from 0.461). */
export const inHundred = (frac: number): number => Math.round(frac * 100);
/** Three decimals ("0.186"), the overlap reads in the footnote-adjacent copy. */
export const fmt3 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 3, maximumFractionDigits: 3 });
/** Two decimals ("1.17"). */
export const fmt2 = (n: number): string =>
	n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
