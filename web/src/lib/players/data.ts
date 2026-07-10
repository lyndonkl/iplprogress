import { base } from '$app/paths';

/**
 * R7a PLAYER CARDS  -  the /players data layer (pure logic, no DOM, no colours, no copy).
 *
 * This module is the client-side join engine the card UI consumes. It NEVER touches
 * three.js or the WebGL field. It lazily loads and caches (module-level promises) the
 * five shipped artifacts and assembles a typed, honest PlayerCard by the verified
 * join recipe:
 *
 *   players.json                    -> the PID registry (join key + search index)
 *   engines/srplus.json             -> SR+ river (name-indexed, filtered by name-union)
 *   engines/entry.json              -> entry map (name-indexed, aggregated client-side)
 *   players/duels_by_player.json    -> Top Duels (already pid-keyed, EB-shrunk)
 *   players/teleporter_lookup.json  -> per-league-season SR curves (cross-era re-price)
 *
 * INVARIANTS honoured (verified against the shipped data):
 *  - `pid` is the join key: the 2 namesakes ("Harmeet Singh", "S Rana") stay two cards;
 *    the 3 alias-split players stay one card.
 *  - name-union = the set of a player's spellings (registry `aliases`, which always
 *    includes the canonical `name`) is the single key into the two NAME-indexed engines.
 *  - Cards/search enumerate registry pids only, so the one 0-ball entry-only name
 *    ("Mayank Rawat") correctly resolves to no card.
 *  - Nothing is fabricated: a season absent from srplus is a GAP (hasData:false), never
 *    interpolated; a panel with no data is suppressed, never faked.
 */

/* ==========================================================================
 * Raw artifact shapes (snake_case, exactly as emitted by the pipeline)
 * ========================================================================== */

export type League = 'ipl' | 'wpl';
export type PlayerRole = 'bat' | 'bowl' | 'all';

/** One registry row from players.json `players[]`. */
export interface PlayerRecord {
	pid: string;
	/** canonical (last-seen) display spelling */
	name: string;
	/** every recorded spelling for this pid; ALWAYS contains `name` */
	aliases: string[];
	/** exactly one league per pid (verified: aliases never bridge IPL and WPL) */
	leagues: League[];
	seasons: number[];
	teams: string[];
	role: PlayerRole;
	balls_faced: number;
	balls_bowled: number;
}

/** players.json top level. */
export interface PlayersIndex {
	count: number;
	/** every spelling -> [pid,...]; a LIST because 2 names are genuinely shared */
	name_to_pids: Record<string, string[]>;
	/** the 2 shared spellings -> their 2 distinct pids (disambiguation chooser) */
	namesakes: Record<string, string[]>;
	players: PlayerRecord[];
}

interface SrPlusRow {
	league: League;
	season: number;
	batter: string;
	balls: number;
	runs: number;
	sr: number;
	expected_runs: number;
	srplus: number;
}
interface SrPlusFile {
	batter_seasons: SrPlusRow[];
	min_balls: number;
	count: number;
}

interface EntryFile {
	arrays: {
		batter: number[];
		league: number[];
		season: number[];
		position: number[];
		entry_ball: number[];
		balls_faced: number[];
		runs: number[];
		dismissed: number[];
		wickets: number[];
		innings: number[];
		match_index: number[];
		rrr: (number | null)[];
	};
	dicts: { batter: string[] };
	count: number;
}

interface DuelRaw {
	opp_pid: string;
	opp_name: string;
	balls: number;
	runs: number;
	dismissals: number;
	dom: number;
}
interface DuelsFile {
	by_pid: Record<string, { as_batter: DuelRaw[]; as_bowler: DuelRaw[] }>;
	count_pairs: number;
	eb: { mu: number; k: number };
}

interface TeleporterFile {
	/** by_league_season[league][String(year)] = SR values of that season's
	 *  qualified (>=100-ball) batters, sorted ASCENDING. */
	by_league_season: Record<League, Record<string, number[]>>;
	target_season: number;
}

/* -- R7b credibility engines (all four loaded SUPPRESSIBLY; see loaders) ---- */

/** engines/half_life.json - per-metric persistence fit; the freshness dial reads H. */
interface HalfLifeMetric {
	half_life_seasons: number;
	r0: number;
	pop_mean: number;
	unit: string;
}
interface HalfLifeFile {
	metrics: Record<string, HalfLifeMetric>;
}

/** engines/trueecon.json - per bowler-season era-fair economy (100 = par, up = better). */
interface TrueEconRow {
	pid: string;
	bowler: string;
	league: League;
	season: number;
	economy: number;
	par_economy: number;
	true_economy: number;
	trueecon_plus: number;
	legal_balls: number;
	wickets: number;
	strike_rate: number;
}
interface TrueEconFile {
	bowler_seasons: TrueEconRow[];
	min_legal_balls: number;
	count: number;
}

/** engines/stabilization.json - per-stat M (balls to half-signal); M can be null. */
interface StabOverall {
	M: number | null;
	mean: number;
	sigma2: number;
	tau2: number;
	n_groups: number;
	stabilizes: boolean;
}
interface StabStat {
	overall: StabOverall;
	min_balls: number;
}
interface StabilizationFile {
	stats: Record<string, StabStat>;
}

/** engines/truetalent.json - per-pid career SR+ with an 80% CI (the static card CI). */
interface TrueTalentRow {
	pid: string;
	league: League;
	name: string;
	n: number;
	raw: number;
	regressed: number;
	ci_lo: number;
	ci_hi: number;
}
interface TrueTalentFile {
	players: TrueTalentRow[];
	pop_mean: Record<League, number>;
	M: number;
	sigma2: number;
	z: number;
}

/* ==========================================================================
 * Public model  -  the card the UI renders (camelCase, everything precomputed)
 * ========================================================================== */

/** A search result row for the disambiguation / typeahead list. */
export interface PlayerHit {
	pid: string;
	/** canonical name (always shown); `matchedAlias` names the spelling that hit */
	name: string;
	/** set only when the match landed on a NON-canonical spelling */
	matchedAlias?: string;
	role: PlayerRole;
	leagues: League[];
	seasons: number[];
	teams: string[];
	/** balls_faced + balls_bowled, the career-volume tie-break */
	careerBalls: number;
}

/** One point on the SR+ river; a gap season carries hasData:false (never interpolated). */
export interface SRPlusPoint {
	season: number;
	/** null on a gap season (played but under 100 balls faced, or absent) */
	srplus: number | null;
	/** raw strike rate that season (null on a gap) */
	sr: number | null;
	/** balls faced that season: srplus.balls when hasData, else the entry-derived count */
	balls: number | null;
	league: League;
	hasData: boolean;
}

export interface PeakSRPlus {
	srplus: number;
	season: number;
	/** raw SR that peak season  -  the number the teleporter re-prices */
	sr: number;
	/** balls faced that peak season  -  the §9.5 trust read (balls vs the SR M) */
	balls: number;
	league: League;
}

/** One point on the TrueEcon river; a gap season carries hasData:false (never interpolated). */
export interface TrueEconPoint {
	season: number;
	league: League;
	/** null on a gap season (bowled under the min-legal-balls floor, or absent) */
	trueeconPlus: number | null;
	/** runs saved per over vs era par that season (null on a gap) */
	trueEconomy: number | null;
	/** legal balls bowled that season (null on a gap) */
	balls: number | null;
	hasData: boolean;
}

export interface PeakTrueEcon {
	trueeconPlus: number;
	season: number;
	/** runs saved per over vs par that peak season  -  the caption gloss */
	trueEconomy: number;
	/** legal balls that peak season  -  the trust read */
	balls: number;
	league: League;
}

/**
 * §9.1 trust state of a rate stat: a player's balls vs that stat's stabilization M.
 * The EXCEPTION-ONLY default  -  'settled' (and 'unknown', when M is unavailable)
 * render with NO mark; only 'firming' and 'noisy' get a cue. Driven by n (balls),
 * NEVER the numerator, so a big raw tally on few balls still flags as still-settling.
 */
export type TrustState = 'settled' | 'firming' | 'noisy' | 'unknown';

/** balls >= M settled; M/2 <= balls < M firming; balls < M/2 noisy; M/balls null unknown. */
export function trustState(balls: number | null, m: number | null): TrustState {
	if (m == null || balls == null) return 'unknown';
	if (balls >= m) return 'settled';
	if (balls >= m / 2) return 'firming';
	return 'noisy';
}

/** The role token a brightest entry-cell classifies into (no prose; the UI writes copy). */
export type EntryRole = 'opener' | 'top-order' | 'middle-order' | 'finisher' | 'floater';

export interface EntryCell {
	/** 0..9 : the 2-over bin the batter walked in (over 0-1, 2-3, ... 18-19) */
	xBin: number;
	/** 0..5 : wickets already down when they walked in (5 = five or more) */
	yBin: number;
	count: number;
}

export interface EntryBrightest {
	xBin: number;
	yBin: number;
	count: number;
	/** inclusive over range of the bin, 0-based (e.g. 0..1) */
	overLo: number;
	overHi: number;
	/** wickets-down of the bin; wicketsPlus === true means the "5+" bin */
	wickets: number;
	wicketsPlus: boolean;
	role: EntryRole;
}

export interface EntryMap {
	cols: 10;
	rows: 6;
	/** length 60, index = yBin*10 + xBin; UI outlines all 60, fills count>=1 */
	cells: EntryCell[];
	totalInnings: number;
	maxCount: number;
	/** median of entry_ball over all their innings */
	medianEntryBall: number;
	/** most frequent batting position (mode) */
	typicalPosition: number;
	brightest: EntryBrightest | null;
}

export interface Duel {
	oppPid: string;
	oppName: string;
	balls: number;
	runs: number;
	dismissals: number;
	/** EB-shrunk runs/ball (>1 batter-leaning, <1 bowler-leaning; par ~= eb.mu) */
	dom: number;
	/** true below the 30-ball floor: render hollow, "too few balls to call" */
	tooFew: boolean;
}

export interface Duels {
	asBatter: Duel[];
	asBowler: Duel[];
	/** the empirical-Bayes constants the dom shrinkage used (method disclosure) */
	eb: { mu: number; k: number };
}

export interface Teleporter {
	league: League;
	/** the peak SR+ season being re-priced */
	season: number;
	/** raw SR that season */
	sr: number;
	/** their percentile among that season's qualified peers (0..100) */
	eraPercentile: number;
	/** naive league-median-ratio carry-over (the fantasy; may sit ABOVE or BELOW honest) */
	naive2026SR: number;
	/** rank-preserving honest re-quote (read this first) */
	honestMid: number;
	/** [lo, hi]; width guaranteed <= |naive2026SR - honestMid| (the anti-overclaim guardrail) */
	honestBand: [number, number];
	/** true if the natural +-1-percentile band was clamped to satisfy the guardrail */
	bandClamped: boolean;
	targetSeason: number;
}

export interface PlayerHeader {
	name: string;
	aliases: string[];
	role: PlayerRole;
	leagues: League[];
	teams: string[];
	seasons: number[];
	firstSeason: number;
	lastSeason: number;
	ballsFaced: number;
	ballsBowled: number;
	/** career runs (entry-summed over their primary league); null if they never batted */
	runs: number | null;
	/** career dismissals (entry-summed); null if they have no batting innings */
	dismissals: number | null;
	/** balls_faced / dismissals  -  the accumulator's due; null if dismissals unknown/0 */
	ballsPerDismissal: number | null;
	peakSRPlus: PeakSRPlus | null;
	/** the bowler's best era-fair economy season (max TrueEcon+); null if no bowling data */
	peakTrueEcon: PeakTrueEcon | null;
	/** §9.3 static 80% CI on the CAREER SR+ (raw + interval); null if the pool omits them */
	careerSRPlus: { raw: number; ciLo: number; ciHi: number } | null;
}

/** Per-panel suppression: true = omit the panel (never fake it). */
export interface PanelSuppress {
	/** balls_bowled < 100 */
	bowlingPanel: boolean;
	/** no qualifying peak season / target arrays absent */
	teleporter: boolean;
	/** no srplus rows at all */
	srPlusRiver: boolean;
	/** no entry rows at all */
	entryMap: boolean;
}

export interface PlayerCard {
	pid: string;
	header: PlayerHeader;
	/** {canonical name} U aliases  -  the name-key into the two NAME-indexed engines */
	nameUnion: string[];
	primaryLeague: League;
	/** balls in the primary role (balls_faced for bat/all, balls_bowled for bowl) */
	primaryBalls: number;
	/** primaryBalls < 100 -> the UI shows a stub (header + raw line + Bowl link only) */
	smallSample: boolean;
	srPlusRiver: SRPlusPoint[];
	/** §9.4 per-season era-fair economy line (100 = par, above = better); [] if no bowling */
	trueEconRiver: TrueEconPoint[];
	entryMap: EntryMap | null;
	duels: Duels;
	teleporter: Teleporter | null;
	suppress: PanelSuppress;
	/** §9.1 the flagged stats' stabilization M (balls to half-signal); null if unavailable */
	stabilizationM: { battingSr: number | null; bowlingEconomy: number | null };
	/** §9.2 the SR+ (srplus) half-life in seasons for the freshness dial; null if unavailable */
	srHalfLife: number | null;
	/** the always-visible "based on N balls" honesty basis */
	basisNote: { ballsFaced: number; ballsBowled: number };
}

/* ==========================================================================
 * Lazy, cached loaders (base-path aware; each artifact decoded once)
 * ========================================================================== */

let indexPromise: Promise<PlayersIndex> | null = null;
let srplusPromise: Promise<SrPlusFile> | null = null;
let entryPromise: Promise<EntryFile> | null = null;
let duelsPromise: Promise<DuelsFile> | null = null;
let teleporterPromise: Promise<TeleporterFile> | null = null;
// R7b credibility engines: cached separately, each resolves null on any failure.
let halfLifePromise: Promise<HalfLifeFile | null> | null = null;
let trueEconPromise: Promise<TrueEconFile | null> | null = null;
let stabilizationPromise: Promise<StabilizationFile | null> | null = null;
let trueTalentPromise: Promise<TrueTalentFile | null> | null = null;

async function fetchJson<T>(url: string): Promise<T> {
	const res = await fetch(url);
	if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
	return (await res.json()) as T;
}

/**
 * SUPPRESSIBLE loader: a fetch/parse failure resolves `null` instead of throwing,
 * so a missing or malformed R7b credibility layer can NEVER regress an already
 * shippable R7a card (the card just renders without that cue). Cached per file.
 */
function fetchJsonOrNull<T>(url: string): Promise<T | null> {
	return fetchJson<T>(url).catch(() => null);
}

/** Load (once) and cache the player registry / search index. */
export function loadPlayersIndex(): Promise<PlayersIndex> {
	indexPromise ??= fetchJson<PlayersIndex>(`${base}/data/players.json`);
	return indexPromise;
}

function loadSrPlus(): Promise<SrPlusFile> {
	srplusPromise ??= fetchJson<SrPlusFile>(`${base}/data/engines/srplus.json`);
	return srplusPromise;
}
function loadEntry(): Promise<EntryFile> {
	entryPromise ??= fetchJson<EntryFile>(`${base}/data/engines/entry.json`);
	return entryPromise;
}
function loadDuels(): Promise<DuelsFile> {
	duelsPromise ??= fetchJson<DuelsFile>(`${base}/data/players/duels_by_player.json`);
	return duelsPromise;
}
function loadTeleporter(): Promise<TeleporterFile> {
	teleporterPromise ??= fetchJson<TeleporterFile>(`${base}/data/players/teleporter_lookup.json`);
	return teleporterPromise;
}
function loadHalfLife(): Promise<HalfLifeFile | null> {
	halfLifePromise ??= fetchJsonOrNull<HalfLifeFile>(`${base}/data/engines/half_life.json`);
	return halfLifePromise;
}
function loadTrueEcon(): Promise<TrueEconFile | null> {
	trueEconPromise ??= fetchJsonOrNull<TrueEconFile>(`${base}/data/engines/trueecon.json`);
	return trueEconPromise;
}
function loadStabilization(): Promise<StabilizationFile | null> {
	stabilizationPromise ??= fetchJsonOrNull<StabilizationFile>(
		`${base}/data/engines/stabilization.json`
	);
	return stabilizationPromise;
}
function loadTrueTalent(): Promise<TrueTalentFile | null> {
	trueTalentPromise ??= fetchJsonOrNull<TrueTalentFile>(`${base}/data/engines/truetalent.json`);
	return trueTalentPromise;
}

/* ==========================================================================
 * Registry helpers (pid <-> record; name resolution)
 * ========================================================================== */

const recordMapCache = new WeakMap<PlayersIndex, Map<string, PlayerRecord>>();

/** pid -> record, built once per loaded index. */
function recordMap(index: PlayersIndex): Map<string, PlayerRecord> {
	let m = recordMapCache.get(index);
	if (!m) {
		m = new Map();
		for (const p of index.players) m.set(p.pid, p);
		recordMapCache.set(index, m);
	}
	return m;
}

export function getRecord(index: PlayersIndex, pid: string): PlayerRecord | null {
	return recordMap(index).get(pid) ?? null;
}

/**
 * Resolve an EXACT typed spelling to its record(s). Returns [] if unknown, one record
 * for 934 pids, and TWO records for the shared spellings ("Harmeet Singh", "S Rana") so
 * the UI shows a chooser. Never silently folds two people into one.
 */
export function resolveName(index: PlayersIndex, spelling: string): PlayerRecord[] {
	const pids = index.name_to_pids[spelling];
	if (!pids) return [];
	const rm = recordMap(index);
	const out: PlayerRecord[] = [];
	for (const pid of pids) {
		const r = rm.get(pid);
		if (r) out.push(r);
	}
	return out;
}

/* ==========================================================================
 * Search (§9.9): prefix over fuzzy, diacritic-insensitive, tie-break by balls
 * ========================================================================== */

/** Lowercase + strip combining diacritics; the search is accent- and case-blind. */
function fold(s: string): string {
	return s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().trim();
}

/** Does `q` appear as an in-order subsequence of `t`? (the last-resort fuzzy tier) */
function isSubsequence(q: string, t: string): boolean {
	if (!q) return true;
	let i = 0;
	for (let j = 0; j < t.length && i < q.length; j++) {
		if (t[j] === q[i]) i++;
	}
	return i === q.length;
}

/**
 * Match tier of a single (folded) candidate spelling against a folded query.
 * Lower is better: 0 exact, 1 full-string prefix, 2 word-prefix ("kohli" -> "v kohli"),
 * 3 substring, 4 in-order subsequence fuzzy, 5 no match.
 */
function matchTier(q: string, cand: string): number {
	if (cand === q) return 0;
	if (cand.startsWith(q)) return 1;
	for (const tok of cand.split(/\s+/)) if (tok.startsWith(q)) return 2;
	if (cand.includes(q)) return 3;
	if (isSubsequence(q, cand)) return 4;
	return 5;
}

interface Scored {
	rec: PlayerRecord;
	tier: number;
	matchedAlias?: string;
	careerBalls: number;
}

/**
 * Rank players by a name/alias match to `query`. Prefix beats mid-string beats fuzzy;
 * diacritic-insensitive; a per-player best tier across all its spellings; tie-break by
 * career balls (balls_faced + balls_bowled) DESC so the prominent namesake ranks first.
 * `matchedAlias` is set only when the winning spelling is not the canonical name.
 */
export function searchPlayers(index: PlayersIndex, query: string, limit = 20): PlayerHit[] {
	const q = fold(query);
	if (!q) return [];

	const scored: Scored[] = [];
	for (const rec of index.players) {
		let bestTier = 5;
		let bestAlias: string | undefined;
		// Canonical name first so an equal-tier canonical hit wins over an alias hit.
		const cName = fold(rec.name);
		const nameTier = matchTier(q, cName);
		if (nameTier < bestTier) {
			bestTier = nameTier;
			bestAlias = undefined;
		}
		for (const alias of rec.aliases) {
			if (alias === rec.name) continue;
			const t = matchTier(q, fold(alias));
			if (t < bestTier) {
				bestTier = t;
				bestAlias = alias;
			}
		}
		if (bestTier < 5) {
			scored.push({
				rec,
				tier: bestTier,
				matchedAlias: bestAlias,
				careerBalls: rec.balls_faced + rec.balls_bowled
			});
		}
	}

	scored.sort(
		(a, b) =>
			a.tier - b.tier ||
			b.careerBalls - a.careerBalls ||
			a.rec.name.localeCompare(b.rec.name) ||
			a.rec.pid.localeCompare(b.rec.pid)
	);

	return scored.slice(0, limit).map((s) => ({
		pid: s.rec.pid,
		name: s.rec.name,
		matchedAlias: s.matchedAlias,
		role: s.rec.role,
		leagues: s.rec.leagues,
		seasons: s.rec.seasons,
		teams: s.rec.teams,
		careerBalls: s.careerBalls
	}));
}

/* ==========================================================================
 * Percentile machinery (mirrors ch10.py sr_at_pct / percentile_of exactly)
 * ========================================================================== */

/** SR at percentile `p` (0..100) within a sorted-ascending array; linear-interpolated. */
function srAtPct(sorted: number[], p: number): number | null {
	if (!sorted.length) return null;
	const idx = (p / 100) * (sorted.length - 1);
	const lo = Math.floor(idx);
	const hi = Math.min(lo + 1, sorted.length - 1);
	const frac = idx - lo;
	return sorted[lo] + frac * (sorted[hi] - sorted[lo]);
}

/** Percentile (0..100) of `sr` within a sorted-ascending array: share strictly below. */
function percentileOf(sorted: number[], sr: number): number | null {
	if (!sorted.length) return null;
	let below = 0;
	for (const x of sorted) if (x < sr) below++;
	return (100 * below) / sorted.length;
}

/** +-1 percentile point defines the honest re-quote's band (ch10 PERCENTILE_WINDOW). */
const PERCENTILE_WINDOW = 1.0;

/* ==========================================================================
 * loadPlayerCard  -  assemble the card by the verified join recipe
 * ========================================================================== */

const LEAGUE_CODE: Record<League, number> = { ipl: 0, wpl: 1 };

/** Median of a numeric array (average of the two middles for even length). */
function median(values: number[]): number {
	if (!values.length) return 0;
	const s = [...values].sort((a, b) => a - b);
	const mid = s.length >> 1;
	return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

/** Classify a brightest entry cell into a role token (heuristic; UI supplies the words). */
function classifyEntryRole(xBin: number, yBin: number, concentration: number): EntryRole {
	let role: EntryRole;
	if (xBin === 0 && yBin <= 1) role = 'opener';
	else if (xBin <= 2 && yBin <= 2) role = 'top-order';
	else if (xBin >= 8 || yBin >= 4) role = 'finisher';
	else role = 'middle-order';
	// A batter with no dominant entry point reads as a floater (unless a clear opener).
	if (role !== 'opener' && concentration < 0.22) role = 'floater';
	return role;
}

/**
 * Assemble the full PlayerCard for `pid`. Lazily loads (and caches) srplus + entry +
 * duels + teleporter, then joins them by the verified recipe. All honesty computed here:
 * gaps in the river, EB-shrunk duels, the guardrailed teleporter band, per-panel
 * suppression, small-sample flag. Nothing is fabricated when data is absent.
 */
export async function loadPlayerCard(pid: string): Promise<PlayerCard> {
	const [index, srplus, entry, duelsFile, teleporterFile, halfLife, trueEcon, stabilization, trueTalent] =
		await Promise.all([
			loadPlayersIndex(),
			loadSrPlus(),
			loadEntry(),
			loadDuels(),
			loadTeleporter(),
			loadHalfLife(),
			loadTrueEcon(),
			loadStabilization(),
			loadTrueTalent()
		]);

	const record = getRecord(index, pid);
	if (!record) throw new Error(`loadPlayerCard: unknown pid ${pid}`);

	const primaryLeague = record.leagues[0];
	const leagueCode = LEAGUE_CODE[primaryLeague];
	const nameUnion = Array.from(new Set(record.aliases)); // always contains record.name
	const unionSet = new Set(nameUnion);

	/* ---- SR+ river + peak (srplus, name-indexed, primary league) ---------- */
	const srMap = new Map<number, SrPlusRow>();
	for (const row of srplus.batter_seasons) {
		if (row.league === primaryLeague && unionSet.has(row.batter)) srMap.set(row.season, row);
	}

	let peakSRPlus: PeakSRPlus | null = null;
	for (const row of srMap.values()) {
		if (!peakSRPlus || row.srplus > peakSRPlus.srplus) {
			peakSRPlus = {
				srplus: row.srplus,
				season: row.season,
				sr: row.sr,
				balls: row.balls,
				league: primaryLeague
			};
		}
	}

	/* ---- entry pass (name-indexed, primary league): map + career aggregates */
	const unionIdx = new Set<number>();
	entry.dicts.batter.forEach((n, i) => {
		if (unionSet.has(n)) unionIdx.add(i);
	});

	const a = entry.arrays;
	const cells: EntryCell[] = Array.from({ length: 60 }, (_, k) => ({
		xBin: k % 10,
		yBin: Math.floor(k / 10),
		count: 0
	}));
	const entryBalls: number[] = [];
	const positionCount = new Map<number, number>();
	const perSeasonBalls = new Map<number, number>();
	let careerRuns = 0;
	let careerDismissals = 0;
	let totalInnings = 0;

	for (let i = 0; i < entry.count; i++) {
		if (a.league[i] !== leagueCode || !unionIdx.has(a.batter[i])) continue;
		totalInnings++;
		const over = Math.floor(a.entry_ball[i] / 6);
		const xBin = Math.min(Math.max(Math.floor(over / 2), 0), 9);
		const yBin = Math.min(Math.max(a.wickets[i], 0), 5);
		cells[yBin * 10 + xBin].count++;
		entryBalls.push(a.entry_ball[i]);
		positionCount.set(a.position[i], (positionCount.get(a.position[i]) ?? 0) + 1);
		perSeasonBalls.set(a.season[i], (perSeasonBalls.get(a.season[i]) ?? 0) + a.balls_faced[i]);
		careerRuns += a.runs[i];
		careerDismissals += a.dismissed[i];
	}

	let entryMap: EntryMap | null = null;
	if (totalInnings > 0) {
		let maxCount = 0;
		let bestIdx = -1;
		for (let k = 0; k < cells.length; k++) {
			if (cells[k].count > maxCount) {
				maxCount = cells[k].count;
				bestIdx = k;
			}
		}
		let typicalPosition = 0;
		let bestPosCount = -1;
		for (const [pos, c] of positionCount) {
			if (c > bestPosCount || (c === bestPosCount && pos < typicalPosition)) {
				bestPosCount = c;
				typicalPosition = pos;
			}
		}
		let brightest: EntryBrightest | null = null;
		if (bestIdx >= 0) {
			const bx = cells[bestIdx].xBin;
			const by = cells[bestIdx].yBin;
			brightest = {
				xBin: bx,
				yBin: by,
				count: maxCount,
				overLo: bx * 2,
				overHi: bx * 2 + 1,
				wickets: by,
				wicketsPlus: by === 5,
				role: classifyEntryRole(bx, by, maxCount / totalInnings)
			};
		}
		entryMap = {
			cols: 10,
			rows: 6,
			cells,
			totalInnings,
			maxCount,
			medianEntryBall: median(entryBalls),
			typicalPosition,
			brightest
		};
	}

	/* ---- SR+ river over the contiguous active span (gaps where <100 balls) - */
	const srPlusRiver: SRPlusPoint[] = [];
	if (record.seasons.length) {
		const first = record.seasons[0];
		const last = record.seasons[record.seasons.length - 1];
		for (let s = first; s <= last; s++) {
			const row = srMap.get(s);
			if (row) {
				srPlusRiver.push({
					season: s,
					srplus: row.srplus,
					sr: row.sr,
					balls: row.balls,
					league: primaryLeague,
					hasData: true
				});
			} else {
				srPlusRiver.push({
					season: s,
					srplus: null,
					sr: null,
					balls: perSeasonBalls.get(s) ?? null,
					league: primaryLeague,
					hasData: false
				});
			}
		}
	}

	/* ---- TrueEcon river + peak (trueecon, PID-keyed, primary league) ------
	 * §9.4: plot trueecon_plus over a 100 baseline (up = better). A season under
	 * the min-legal-balls floor is absent from the artifact -> it breaks the line
	 * as a gap (never interpolated), exactly like the SR+ river's <100-ball gap. */
	const teMap = new Map<number, TrueEconRow>();
	if (trueEcon) {
		for (const row of trueEcon.bowler_seasons) {
			if (row.pid === pid && row.league === primaryLeague) teMap.set(row.season, row);
		}
	}

	let peakTrueEcon: PeakTrueEcon | null = null;
	for (const row of teMap.values()) {
		if (!peakTrueEcon || row.trueecon_plus > peakTrueEcon.trueeconPlus) {
			peakTrueEcon = {
				trueeconPlus: row.trueecon_plus,
				season: row.season,
				trueEconomy: row.true_economy,
				balls: row.legal_balls,
				league: primaryLeague
			};
		}
	}

	const trueEconRiver: TrueEconPoint[] = [];
	if (teMap.size && record.seasons.length) {
		const first = record.seasons[0];
		const last = record.seasons[record.seasons.length - 1];
		for (let s = first; s <= last; s++) {
			const row = teMap.get(s);
			if (row) {
				trueEconRiver.push({
					season: s,
					league: primaryLeague,
					trueeconPlus: row.trueecon_plus,
					trueEconomy: row.true_economy,
					balls: row.legal_balls,
					hasData: true
				});
			} else {
				trueEconRiver.push({
					season: s,
					league: primaryLeague,
					trueeconPlus: null,
					trueEconomy: null,
					balls: null,
					hasData: false
				});
			}
		}
	}

	/* ---- credibility constants: M (§9.1), SR+ half-life (§9.2), CI (§9.3) --
	 * All suppressible: a null flows through to "no cue" and the card is unharmed.
	 * dismissal_pct.M is null by design (never stabilizes); the ?? null keeps that
	 * honest for any stat, so a null M is treated as "unknown trust", never divided. */
	const battingSrM = stabilization?.stats?.batting_sr?.overall?.M ?? null;
	const bowlingEconomyM = stabilization?.stats?.bowling_economy?.overall?.M ?? null;
	const srHalfLife = halfLife?.metrics?.srplus?.half_life_seasons ?? null;

	let careerSRPlus: { raw: number; ciLo: number; ciHi: number } | null = null;
	if (trueTalent) {
		const ttRow = trueTalent.players.find((r) => r.pid === pid);
		if (ttRow) careerSRPlus = { raw: ttRow.raw, ciLo: ttRow.ci_lo, ciHi: ttRow.ci_hi };
	}

	/* ---- Top Duels (pid-keyed, EB-shrunk, pre-ranked balls-desc) ---------- */
	const rawDuels = duelsFile.by_pid[pid];
	const toDuel = (d: DuelRaw): Duel => ({
		oppPid: d.opp_pid,
		oppName: d.opp_name,
		balls: d.balls,
		runs: d.runs,
		dismissals: d.dismissals,
		dom: d.dom,
		tooFew: d.balls < 30
	});
	const duels: Duels = {
		asBatter: rawDuels ? rawDuels.as_batter.map(toDuel) : [],
		asBowler: rawDuels ? rawDuels.as_bowler.map(toDuel) : [],
		eb: duelsFile.eb
	};

	/* ---- Teleporter (peak season re-priced; guardrailed band) ------------- */
	let teleporter: Teleporter | null = null;
	if (peakSRPlus) {
		const bySeason = teleporterFile.by_league_season[primaryLeague];
		const peakArr = bySeason?.[String(peakSRPlus.season)];
		const tgtArr = bySeason?.[String(teleporterFile.target_season)];
		if (peakArr?.length && tgtArr?.length) {
			const sr = peakSRPlus.sr;
			const pct = percentileOf(peakArr, sr);
			const honest = srAtPct(tgtArr, pct ?? 0);
			const peakMed = srAtPct(peakArr, 50);
			const tgtMed = srAtPct(tgtArr, 50);
			if (pct != null && honest != null && peakMed != null && tgtMed != null && peakMed > 0) {
				const blo = srAtPct(tgtArr, Math.max(0, pct - PERCENTILE_WINDOW)) ?? honest;
				const bhi = srAtPct(tgtArr, Math.min(100, pct + PERCENTILE_WINDOW)) ?? honest;
				const half = (bhi - blo) / 2;
				const naive = (sr * tgtMed) / peakMed;
				const gap = Math.abs(naive - honest);
				// Anti-overclaim guardrail: the honest band's full width must be <= the
				// naive-vs-honest gap. Clamp (and flag) if the natural +-1pct band is wider.
				let lo = honest - half;
				let hi = honest + half;
				let bandClamped = false;
				if (hi - lo > gap) {
					lo = honest - gap / 2;
					hi = honest + gap / 2;
					bandClamped = true;
				}
				teleporter = {
					league: primaryLeague,
					season: peakSRPlus.season,
					sr,
					eraPercentile: pct,
					naive2026SR: naive,
					honestMid: honest,
					honestBand: [lo, hi],
					bandClamped,
					targetSeason: teleporterFile.target_season
				};
			}
		}
	}

	/* ---- header + suppression + basis ------------------------------------- */
	const primaryBalls = record.role === 'bowl' ? record.balls_bowled : record.balls_faced;
	const hasBatting = totalInnings > 0;
	const ballsPerDismissal =
		careerDismissals > 0 ? record.balls_faced / careerDismissals : null;

	const header: PlayerHeader = {
		name: record.name,
		aliases: record.aliases,
		role: record.role,
		leagues: record.leagues,
		teams: record.teams,
		seasons: record.seasons,
		firstSeason: record.seasons[0],
		lastSeason: record.seasons[record.seasons.length - 1],
		ballsFaced: record.balls_faced,
		ballsBowled: record.balls_bowled,
		runs: hasBatting ? careerRuns : null,
		dismissals: hasBatting ? careerDismissals : null,
		ballsPerDismissal,
		peakSRPlus,
		peakTrueEcon,
		careerSRPlus
	};

	const suppress: PanelSuppress = {
		bowlingPanel: record.balls_bowled < 100,
		teleporter: teleporter === null,
		srPlusRiver: srMap.size === 0,
		entryMap: entryMap === null
	};

	return {
		pid,
		header,
		nameUnion,
		primaryLeague,
		primaryBalls,
		smallSample: primaryBalls < 100,
		srPlusRiver,
		trueEconRiver,
		entryMap,
		duels,
		teleporter,
		suppress,
		stabilizationM: { battingSr: battingSrM, bowlingEconomy: bowlingEconomyM },
		srHalfLife,
		basisNote: { ballsFaced: record.balls_faced, ballsBowled: record.balls_bowled }
	};
}
