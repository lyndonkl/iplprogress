import { base } from '$app/paths';
import type { FieldData, FilterMode, TeamMeta } from '$lib/field/types';
import type { SceneFieldState } from '$lib/story/types';

/**
 * THE BOWL — sandbox data layer (blueprint §3 "The Bowl", R1b minimal scope;
 * CONTRACT §11 picking · §12 filtering).
 *
 * Loads the sandbox dataset LAZILY on entering the Bowl (never in the cold-open
 * critical payload — see static/data/ledger.json: the columnar/matches/descriptor
 * are their own "sandbox dataset" ledger check, excluded from the pre-assembly
 * set). Decoded ONCE and cached as module-level promises.
 *
 *  - columnar.json.gz → parallel arrays + dicts, SAME point order as the field's
 *    per-point buffers (verified: arrays.<x>[idx] at a `field.pickAt` index names
 *    that exact delivery). Gzip on the wire; decoded client-side.
 *  - matches.json → indexed by match_index; resolves opponent + match label.
 *  - scenes/sandbox.json → facet descriptor + the one famous-match preset.
 */

/* ---- columnar dataset (columnar.json.gz) ---------------------------------- */

export interface ColumnarArrays {
	season: number[];
	league: number[];
	innings: number[];
	over: number[];
	ball_index_in_over: number[];
	batter: number[];
	bowler: number[];
	batting_team: number[];
	runs_batter: number[];
	runs_total: number[];
	outcome: number[];
	wicket: number[];
	wicket_kind: number[];
	match_index: number[];
}

export interface ColumnarDicts {
	batter: string[];
	bowler: string[];
	batting_team: string[];
	wicket_kind: string[];
}

export interface Columnar {
	n_points: number;
	point_order: string;
	arrays: ColumnarArrays;
	dicts: ColumnarDicts;
}

/* ---- matches.json --------------------------------------------------------- */

export interface MatchInfo {
	teams: [string, string];
	season: number;
	date: string;
	stage: string;
	venue: string;
	city: string;
	result_text: string;
	league: string;
}

/* ---- scenes/sandbox.json (the parts the Bowl reads) ----------------------- */

export interface SandboxPreset {
	match_index: number;
	label: string;
	blurb: string;
}

/**
 * A tour-flag's facet dict as emitted by the pipeline (scenes.py `TOUR_FLAGS`).
 * Its vocabulary is a SUPERSET of the live `Facets` grammar: it can carry a
 * season-in-set (`seasons`), an innings, and a computed match-membership set
 * (`matchSet`) — facets the tray has no control for. batter/bowler arrive BY
 * NAME (the client resolves each to a `col.dicts` index). Only the CONSTRAINING
 * keys are present on a given flag; every key AND-combines. Outcome codes: dot 0,
 * single 1, two-or-three 2, four 3, six 4, extras 5 (the six=4/four=3 trap).
 */
export interface TourFlagFacets {
	league?: 'ipl' | 'wpl';
	/** exact season year */
	season?: number;
	/** season-in-set (e.g. the 2023-26 death-carnage window) */
	seasons?: number[];
	/** 0-based inclusive over lower bound (over >= overLo) */
	overLo?: number;
	/** 0-based inclusive over upper bound (over <= overHi) */
	overHi?: number;
	/** OR-list of off-the-bat outcome CODES (0..5), OR-ed within the list */
	outcomes?: number[];
	/** 1 = AND a wicket fell (independent of the outcome) */
	wicket?: 1;
	/** 1 = first innings, 2 = second */
	innings?: 1 | 2;
	/** batter NAME (resolve via col.dicts.batter) */
	batter?: string;
	/** bowler NAME (resolve via col.dicts.bowler) */
	bowler?: string;
	/** the computed match-membership set (match_index in set) — the 200-club predicate */
	matchSet?: number[];
	/** render-mode override — 'hide' only on the match-preset flag; the rest dim */
	mode?: 'hide';
}

/**
 * One guided-tour flag from `scenes/sandbox.json`. `count` is the build-VALIDATED
 * recount (artifact wins — the live `buildTourFlagMask(col, flag, ni).count` MUST
 * reproduce it). `match_index` is present only on the match-preset flag
 * (`final-2019`); every other flag resolves purely from its `facets`.
 */
export interface TourFlag {
	id: string;
	label: string;
	blurb: string;
	count: number;
	facets: TourFlagFacets;
	match_index?: number;
}

export interface SandboxDescriptor {
	preset: SandboxPreset;
	scope: string;
	/** the ten-flag guided-tour rail (each resolved + validated >= 1 ball at build) */
	tourFlags: TourFlag[];
}

export interface SandboxData {
	columnar: Columnar;
	matches: MatchInfo[];
	descriptor: SandboxDescriptor;
	/** batter/bowler name -> dict index, built ONCE on columnar load (typeaheads + flags) */
	nameIndex: NameIndex;
}

/* ---- lazy, cached loaders ------------------------------------------------- */

let sandboxPromise: Promise<SandboxData> | null = null;

/** Load (once) and cache the whole sandbox dataset. Base-path aware. */
export function loadSandboxData(): Promise<SandboxData> {
	sandboxPromise ??= (async () => {
		const [columnar, matches, descriptor] = await Promise.all([
			fetchColumnar(`${base}/data/columnar.json.gz`),
			fetchJson<MatchInfo[]>(`${base}/data/matches.json`),
			fetchJson<SandboxDescriptor>(`${base}/data/scenes/sandbox.json`)
		]);
		return { columnar, matches, descriptor, nameIndex: nameIndexFor(columnar) };
	})();
	return sandboxPromise;
}

async function fetchJson<T>(url: string): Promise<T> {
	const res = await fetch(url);
	if (!res.ok) throw new Error(`${url} → HTTP ${res.status}`);
	return (await res.json()) as T;
}

/**
 * Fetch the gzipped columnar JSON. Robust to either serving convention:
 *  - the host set `Content-Encoding: gzip` and `fetch` already inflated it
 *    (the bytes are plain JSON text) → parse directly;
 *  - the host served the raw `.gz` opaquely (bytes start with the gzip magic
 *    1f 8b) → inflate with `DecompressionStream('gzip')` client-side.
 * GitHub Pages serves the raw bytes, so the magic-byte path is the live one.
 */
async function fetchColumnar(url: string): Promise<Columnar> {
	const res = await fetch(url);
	if (!res.ok) throw new Error(`${url} → HTTP ${res.status}`);
	const bytes = new Uint8Array(await res.arrayBuffer());
	let text: string;
	if (bytes.length >= 2 && bytes[0] === 0x1f && bytes[1] === 0x8b) {
		if (typeof DecompressionStream === 'undefined')
			throw new Error(`${url}: gzip payload but DecompressionStream is unavailable`);
		const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
		text = await new Response(stream).text();
	} else {
		text = new TextDecoder().decode(bytes);
	}
	return JSON.parse(text) as Columnar;
}

/* ---- facets --------------------------------------------------------------- */

/** The innings phase, in fan language, mapped to a 0-based over range. */
export type Phase = 'powerplay' | 'middle' | 'death';

/**
 * The Bowl's live facet selection — the FULL R6b grammar. Every field AND-combines
 * with every other; a `null` (or `false`/omitted) field imposes no constraint.
 *
 * The first four fields (team, season, matchRange, mode) are the R1b scalar facets
 * and stay REQUIRED so an R1b `{ team, season, matchRange, mode }` literal is still
 * a valid `Facets`. The rest are the R6b extension and are optional, so the R1b
 * scalar fast path keeps compiling and rendering byte-identically.
 *
 * OUTCOME CODE TRAP: `outcomes` is a BITMASK over off-the-bat outcome codes
 * (bit c = 1 << c): dot 0, single 1, two-or-three 2, four 3, six 4, extras 5.
 * `wicket` is a SEPARATE boolean AND-field (NOT an outcome bit) — a wicket can
 * co-occur with a run, so "sixes that took a wicket" is `outcomes:(1<<4)` AND
 * `wicket:true`.
 */
export interface Facets {
	/** teams.json id (team.u8, 20 ids) to keep BATTING, or null = all teams */
	team: number | null;
	/** season YEAR to keep (both leagues' groups for that year), or null = all */
	season: number | null;
	/** the famous-match preset's contiguous [lo, hi) point range, or null */
	matchRange: readonly [number, number] | null;
	/** how filtered-out points render */
	mode: FilterMode;

	/* ---- R6b extension (optional; presence of ANY of these routes the mask path) */
	/** 'ipl' | 'wpl' to keep, or null = both leagues */
	league?: 'ipl' | 'wpl' | null;
	/** innings phase; mirrors its over range into overLo/overHi (kept symmetric) */
	phase?: Phase | null;
	/** 0-based inclusive over lower bound (over >= overLo), or null */
	overLo?: number | null;
	/** 0-based inclusive over upper bound (over <= overHi), or null */
	overHi?: number | null;
	/** outcome BITMASK (bit c = 1 << outcome-code); null or 0 = no outcome constraint */
	outcomes?: number | null;
	/** the SEPARATE wicket AND-toggle: true = a wicket fell (independent of outcome) */
	wicket?: boolean;
	/** batter dict index (col.dicts.batter), or null = any batter */
	batter?: number | null;
	/** bowler dict index (col.dicts.bowler), or null = any bowler */
	bowler?: number | null;
}

/** The neutral selection — every facet inactive (the whole field). */
export const NO_FACETS: Facets = {
	team: null,
	season: null,
	matchRange: null,
	mode: 'dim',
	league: null,
	phase: null,
	overLo: null,
	overHi: null,
	outcomes: null,
	wicket: false,
	batter: null,
	bowler: null
};

/** The result of a single mask pass over the corpus. `firstIndex` is -1 when empty. */
export interface FacetMaskResult {
	/** length-nPoints byte mask (1 = keep, 0 = drop) — hand straight to field.setFilterMask */
	mask: Uint8Array;
	/** number of balls in the selection (must reproduce the flag/artifact counts) */
	count: number;
	/** first point index with mask===1, or -1 if the selection is empty */
	firstIndex: number;
}

/** batter/bowler name -> dict index (built once on columnar load — typeaheads + flags). */
export interface NameIndex {
	batter: Map<string, number>;
	bowler: Map<string, number>;
}

/**
 * The 0-based inclusive over range for a phase (§13: powerplay [0,5], middle
 * [6,14], death [15,19]). Null phase -> null (no over constraint).
 */
export function phaseToOverRange(phase: Phase | null | undefined): readonly [number, number] | null {
	switch (phase) {
		case 'powerplay':
			return [0, 5];
		case 'middle':
			return [6, 14];
		case 'death':
			return [15, 19];
		default:
			return null;
	}
}

/** Inverse of phaseToOverRange: the phase an exact [lo,hi] over range names, or null. */
export function overRangeToPhase(lo: number, hi: number): Phase | null {
	if (lo === 0 && hi === 5) return 'powerplay';
	if (lo === 6 && hi === 14) return 'middle';
	if (lo === 15 && hi === 19) return 'death';
	return null;
}

/**
 * SCALAR-vs-MASK routing (CONTRACT §28, invariant 2). Returns true when the
 * selection needs the arbitrary-facet MASK path (`field.setFilterMask`). It only
 * needs the R1b scalar fast path (`field.setFilter`) when NOTHING beyond
 * team/season/matchRange is set — those three map onto scalar uniforms. League,
 * phase, over-range, outcomes, wicket, batter, and bowler each force the mask.
 */
export function facetsNeedMask(f: Facets): boolean {
	return (
		f.league != null ||
		f.phase != null ||
		f.overLo != null ||
		f.overHi != null ||
		(f.outcomes != null && f.outcomes !== 0) ||
		f.wicket === true ||
		f.batter != null ||
		f.bowler != null
	);
}

/**
 * Build the per-point membership mask for the FULL facet grammar in ONE pass over
 * the columnar arrays, cheapest-first short-circuit (matchRange -> league -> team
 * -> season -> over -> outcomes -> wicket -> batter -> bowler). The columnar arrays
 * are in the SAME point order as the field's per-point buffers, so `mask` indexes
 * the field 1:1.
 *
 * `teamById` is the per-point teams.json id (team.u8 = `field.data.team`), NOT the
 * columnar `batting_team` name dict (17 names, WPL collapses onto IPL namesakes) —
 * the team facet is BATTING-side via the 20-id team.u8. Season reads
 * `col.arrays.season[i]` directly (no group lookup). Outcomes is the bitmask; wicket
 * is the independent AND bit. The result reproduces the emitted flag counts exactly.
 */
export function buildFacetMask(col: Columnar, teamById: Uint8Array, f: Facets): FacetMaskResult {
	const n = col.n_points;
	const a = col.arrays;
	const mask = new Uint8Array(n);

	const hasRange = f.matchRange != null;
	const rangeLo = hasRange ? f.matchRange![0] : 0;
	const rangeHi = hasRange ? f.matchRange![1] : 0;
	const leagueCode = f.league === 'ipl' ? 0 : f.league === 'wpl' ? 1 : -1;
	const team = f.team;
	const season = f.season;

	// phase mirrors its over range; an explicit over range is used only when no phase.
	let oLo = -1;
	let oHi = -1;
	const phaseRange = f.phase ? phaseToOverRange(f.phase) : null;
	if (phaseRange) {
		oLo = phaseRange[0];
		oHi = phaseRange[1];
	} else {
		if (f.overLo != null) oLo = f.overLo;
		if (f.overHi != null) oHi = f.overHi;
	}

	const oc = f.outcomes ?? 0; // 0 = no outcome constraint
	const needWicket = f.wicket === true;
	const batter = f.batter;
	const bowler = f.bowler;

	let count = 0;
	let first = -1;
	for (let i = 0; i < n; i++) {
		if (hasRange && (i < rangeLo || i >= rangeHi)) continue;
		if (leagueCode >= 0 && a.league[i] !== leagueCode) continue;
		if (team != null && teamById[i] !== team) continue;
		if (season != null && a.season[i] !== season) continue;
		if (oLo >= 0 && a.over[i] < oLo) continue;
		if (oHi >= 0 && a.over[i] > oHi) continue;
		if (oc !== 0 && ((oc >> a.outcome[i]) & 1) === 0) continue;
		if (needWicket && a.wicket[i] !== 1) continue;
		if (batter != null && a.batter[i] !== batter) continue;
		if (bowler != null && a.bowler[i] !== bowler) continue;
		mask[i] = 1;
		count++;
		if (first < 0) first = i;
	}
	return { mask, count, firstIndex: first };
}

/** Build the batter/bowler name -> dict-index maps (call once per columnar). */
export function buildNameIndex(col: Columnar): NameIndex {
	const batter = new Map<string, number>();
	const bowler = new Map<string, number>();
	col.dicts.batter.forEach((name, i) => batter.set(name, i));
	col.dicts.bowler.forEach((name, i) => bowler.set(name, i));
	return { batter, bowler };
}

const nameIndexCache = new WeakMap<Columnar, NameIndex>();

/** Memoized `buildNameIndex` keyed by the columnar object (built once on load). */
export function nameIndexFor(col: Columnar): NameIndex {
	let ni = nameIndexCache.get(col);
	if (!ni) {
		ni = buildNameIndex(col);
		nameIndexCache.set(col, ni);
	}
	return ni;
}

/* ---- tour flags ----------------------------------------------------------- */

/** The guided-tour rail from `scenes/sandbox.json` (empty if the artifact lacks it). */
export function tourFlags(data: SandboxData): TourFlag[] {
	return data.descriptor.tourFlags ?? [];
}

/**
 * Build a tour flag's mask directly from its (richer-than-`Facets`) facet dict, in
 * ONE columnar pass. Handles the keys the live tray cannot represent — `seasons`
 * (season-in-set), `innings`, `matchSet` (the 200-club computed predicate), and the
 * `match_index` match-preset flag — and resolves batter/bowler NAMES via `nameIndex`.
 * The returned `count` reproduces the flag's build-validated artifact count exactly.
 */
export function buildTourFlagMask(col: Columnar, flag: TourFlag, nameIndex: NameIndex): FacetMaskResult {
	const n = col.n_points;
	const a = col.arrays;
	const mask = new Uint8Array(n);
	const ff = flag.facets;

	const matchIndex = flag.match_index; // number | undefined
	const matchSet = ff.matchSet ? new Set(ff.matchSet) : null;
	const leagueCode = ff.league === 'ipl' ? 0 : ff.league === 'wpl' ? 1 : -1;
	const season = ff.season; // number | undefined
	const seasonsSet = ff.seasons ? new Set(ff.seasons) : null;
	const oLo = ff.overLo ?? -1;
	const oHi = ff.overHi ?? -1;
	const oc = ff.outcomes && ff.outcomes.length ? ff.outcomes.reduce((m, c) => m | (1 << c), 0) : 0;
	const needWicket = ff.wicket === 1;
	const innings = ff.innings; // 1 | 2 | undefined
	const batterIdx = ff.batter != null ? nameIndex.batter.get(ff.batter) ?? -1 : -1;
	const bowlerIdx = ff.bowler != null ? nameIndex.bowler.get(ff.bowler) ?? -1 : -1;

	let count = 0;
	let first = -1;
	for (let i = 0; i < n; i++) {
		if (matchIndex != null && a.match_index[i] !== matchIndex) continue;
		if (matchSet && !matchSet.has(a.match_index[i])) continue;
		if (batterIdx >= 0 && a.batter[i] !== batterIdx) continue;
		if (bowlerIdx >= 0 && a.bowler[i] !== bowlerIdx) continue;
		if (leagueCode >= 0 && a.league[i] !== leagueCode) continue;
		if (innings != null && a.innings[i] !== innings) continue;
		if (season != null && a.season[i] !== season) continue;
		if (seasonsSet && !seasonsSet.has(a.season[i])) continue;
		if (oLo >= 0 && a.over[i] < oLo) continue;
		if (oHi >= 0 && a.over[i] > oHi) continue;
		if (oc !== 0 && ((oc >> a.outcome[i]) & 1) === 0) continue;
		if (needWicket && a.wicket[i] !== 1) continue;
		mask[i] = 1;
		count++;
		if (first < 0) first = i;
	}
	return { mask, count, firstIndex: first };
}

/**
 * The best-effort `Facets` a flag maps onto, so the tray can REFLECT what the flag
 * set (invariant 6: the flag is a starting point the reader can then tweak). Keys the
 * grammar cannot hold (`seasons` set, `innings`, `matchSet`) are NOT reflected — they
 * are only applied via `buildTourFlagMask`; the mappable controls (league, single
 * season, phase/over, outcomes, wicket, batter, bowler, and the match preset's range)
 * are set so the reader sees the filters that built the view. Names resolve via
 * `nameIndex`; the match-preset flag resolves its contiguous range via `deriveMatchRange`.
 */
export function tourFlagToFacets(flag: TourFlag, col: Columnar, nameIndex: NameIndex): Facets {
	const ff = flag.facets;
	const f: Facets = { ...NO_FACETS };
	f.mode = ff.mode === 'hide' ? 'hide' : 'dim';
	if (ff.league) f.league = ff.league;
	if (ff.season != null) f.season = ff.season;
	if (ff.overLo != null || ff.overHi != null) {
		const lo = ff.overLo ?? 0;
		const hi = ff.overHi ?? 19;
		f.overLo = lo;
		f.overHi = hi;
		f.phase = overRangeToPhase(lo, hi);
	}
	if (ff.outcomes && ff.outcomes.length) f.outcomes = ff.outcomes.reduce((m, c) => m | (1 << c), 0);
	if (ff.wicket === 1) f.wicket = true;
	if (ff.batter != null) f.batter = nameIndex.batter.get(ff.batter) ?? null;
	if (ff.bowler != null) f.bowler = nameIndex.bowler.get(ff.bowler) ?? null;
	if (flag.match_index != null) f.matchRange = deriveMatchRange(col, flag.match_index);
	return f;
}

/**
 * The ONE live held field state the scroll orchestrator reads every tick — the
 * Bowl's `SceneDef.fieldState` AND `reducedMotionEndState` both point AT this
 * object (see index.ts). The scene component keeps it in sync via `syncBowlHeld`
 * on every facet change, so a stray scroll re-application can never revert the
 * reader's facets (CONTRACT §12.2 orchestrator caveat) — under normal motion via
 * `dynamicTarget`/`heldState`, and under reduced motion via `sceneEndState`,
 * which both resolve through this same reference. Default layout is season
 * columns so the season facet maps spatially; labels on; no facet active yet
 * (full field — never blank) until the component opens it.
 */
export const bowlHeld: SceneFieldState = {
	layout: 'columns',
	labels: 1,
	filterTeam: null,
	filterSeason: null,
	filterMatchRange: null,
	filterMode: 'dim',
	filterMask: null
};

/**
 * Mirror the reader's live selection into the orchestrator-read held state so a
 * stray scroll re-applying the scene re-asserts the SAME view (CONTRACT §12.2), not
 * a reverted one. Pass the last-committed mask (or null) so the two field paths stay
 * mutually exclusive:
 *  - MASK path (`mask` non-null): the mask carries the whole selection, so the scalar
 *    uniforms are cleared (team/season/range null) and the mask is stashed on
 *    `filterMask` — a re-application re-uploads exactly this mask.
 *  - SCALAR fast path (`mask` null, the R1b path): team/season/range ride the scalar
 *    uniforms and `filterMask` is cleared, so the field never touches the mask texture
 *    and prior releases render byte-identically.
 */
export function syncBowlHeld(f: Facets, mask: Uint8Array | null = null): void {
	if (mask) {
		bowlHeld.filterTeam = null;
		bowlHeld.filterSeason = null;
		bowlHeld.filterMatchRange = null;
		bowlHeld.filterMask = mask;
	} else {
		bowlHeld.filterTeam = f.team;
		bowlHeld.filterSeason = f.season;
		bowlHeld.filterMatchRange = f.matchRange;
		bowlHeld.filterMask = null;
	}
	bowlHeld.filterMode = f.mode;
}

/* ---- derived helpers ------------------------------------------------------ */

/** gi → season year, for the season facet + the live count (built once). */
export function buildGroupSeason(data: FieldData): Int16Array {
	const gs = new Int16Array(data.groups.length);
	for (const g of data.groups) gs[g.gi] = g.season;
	return gs;
}

/**
 * Live "N balls" count of the current selection, straight from the field's
 * typed per-point buffers (no columnar needed) — mirrors the shader's
 * visibility test exactly (team AND season AND range).
 */
export function countVisible(data: FieldData, groupSeason: Int16Array, f: Facets): number {
	const lo = f.matchRange ? f.matchRange[0] : 0;
	const hi = f.matchRange ? f.matchRange[1] : 0;
	const hasRange = hi > lo;
	const { team, season } = f;
	const n = data.nPoints;
	let c = 0;
	for (let i = 0; i < n; i++) {
		if (hasRange && (i < lo || i >= hi)) continue;
		if (team != null && data.team[i] !== team) continue;
		if (season != null && groupSeason[data.groupIds[i]] !== season) continue;
		c++;
	}
	return c;
}

/** Map a picked-team (league + canonical name) to its teams.json id, or null. */
export function teamIdFor(teams: TeamMeta[], league: 'ipl' | 'wpl', name: string): number | null {
	const t = teams.find((tm) => tm.league === league && tm.name === name);
	return t ? t.id : null;
}

/**
 * Derive the preset's contiguous [lo, hi) point-index range by scanning
 * columnar `match_index` (a match's deliveries ARE contiguous in point order —
 * CONTRACT §12.4). Returns null if the match isn't present.
 */
export function deriveMatchRange(col: Columnar, matchIndex: number): readonly [number, number] | null {
	const mi = col.arrays.match_index;
	let lo = -1;
	let hi = -1;
	for (let i = 0; i < mi.length; i++) {
		if (mi[i] === matchIndex) {
			if (lo < 0) lo = i;
			hi = i;
		}
	}
	return lo < 0 ? null : ([lo, hi + 1] as const);
}

/* ---- the tap-a-ball tooltip ----------------------------------------------- */

export interface BallTooltip {
	batter: string;
	bowler: string;
	battingTeam: string;
	opponent: string;
	/** e.g. "2019 · Final" */
	matchLabel: string;
	date: string;
	venue: string;
	/** e.g. "1st innings" / "2nd innings" / "innings 3" */
	inningsLabel: string;
	/** over.ball, 1-based for humans (over/ball are 0-based in the data) */
	overBall: string;
	/** "4 runs off the bat" / "Out, bowled" / "dot ball" / "2 (extras)" */
	result: string;
	/** the match's result line, e.g. "Mumbai Indians won by 1 run" */
	resultText: string;
}

/**
 * Build the tooltip for the field point at `idx` (a `field.pickAt` result).
 * Reads the columnar parallel arrays + dicts at `idx` (same point order as the
 * field) and resolves the match via matches.json. This is the exact field set
 * scenes/sandbox.json enumerates.
 */
export function buildTooltip(col: Columnar, matches: MatchInfo[], idx: number): BallTooltip {
	const a = col.arrays;
	const d = col.dicts;
	const battingTeam = d.batting_team[a.batting_team[idx]] ?? '-';
	const mi = a.match_index[idx];
	const m = matches[mi];

	const opponent =
		m && m.teams ? (m.teams.find((t) => t !== battingTeam) ?? '-') : '-';
	const matchLabel = m ? `${m.season} · ${m.stage}` : `season ${a.season[idx]}`;
	const date = m ? m.date : '';
	const venue = m ? m.venue : '';
	const resultText = m ? m.result_text : '';

	const inn = a.innings[idx];
	const inningsLabel = inn === 1 ? '1st innings' : inn === 2 ? '2nd innings' : `innings ${inn}`;
	const overBall = `${a.over[idx] + 1}.${a.ball_index_in_over[idx] + 1}`;

	let result: string;
	if (a.wicket[idx] === 1) {
		const kind = d.wicket_kind[a.wicket_kind[idx]] ?? '';
		result = kind ? `Out, ${kind}` : 'Out';
	} else {
		const rb = a.runs_batter[idx];
		const rt = a.runs_total[idx];
		if (rb === 0 && rt === 0) result = 'dot ball';
		else if (rb === 0 && rt > 0) result = `${rt} (extras)`;
		else if (rt !== rb) result = `${rb} off the bat · ${rt} to the total`;
		else result = `${rb} run${rb === 1 ? '' : 's'} off the bat`;
	}

	return {
		batter: d.batter[a.batter[idx]] ?? '-',
		bowler: d.bowler[a.bowler[idx]] ?? '-',
		battingTeam,
		opponent,
		matchLabel,
		date,
		venue,
		inningsLabel,
		overBall,
		result,
		resultText
	};
}
