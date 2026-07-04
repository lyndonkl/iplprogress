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

export interface SandboxDescriptor {
	preset: SandboxPreset;
	scope: string;
}

export interface SandboxData {
	columnar: Columnar;
	matches: MatchInfo[];
	descriptor: SandboxDescriptor;
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
		return { columnar, matches, descriptor };
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

/** The Bowl's live facet selection (team AND season AND the preset range). */
export interface Facets {
	/** teams.json id to keep, or null = all teams */
	team: number | null;
	/** season YEAR to keep (both leagues' groups for that year), or null = all */
	season: number | null;
	/** the famous-match preset's contiguous [lo, hi) point range, or null */
	matchRange: readonly [number, number] | null;
	/** how filtered-out points render */
	mode: FilterMode;
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
	filterMode: 'dim'
};

/** Mirror the reader's live facets into the orchestrator-read held state. */
export function syncBowlHeld(f: Facets): void {
	bowlHeld.filterTeam = f.team;
	bowlHeld.filterSeason = f.season;
	bowlHeld.filterMatchRange = f.matchRange;
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
	/** "4 runs off the bat" / "OUT — bowled" / "dot ball" / "2 (extras)" */
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
	const battingTeam = d.batting_team[a.batting_team[idx]] ?? '—';
	const mi = a.match_index[idx];
	const m = matches[mi];

	const opponent =
		m && m.teams ? (m.teams.find((t) => t !== battingTeam) ?? '—') : '—';
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
		result = kind ? `OUT — ${kind}` : 'OUT';
	} else {
		const rb = a.runs_batter[idx];
		const rt = a.runs_total[idx];
		if (rb === 0 && rt === 0) result = 'dot ball';
		else if (rb === 0 && rt > 0) result = `${rt} (extras)`;
		else if (rt !== rb) result = `${rb} off the bat · ${rt} to the total`;
		else result = `${rb} run${rb === 1 ? '' : 's'} off the bat`;
	}

	return {
		batter: d.batter[a.batter[idx]] ?? '—',
		bowler: d.bowler[a.bowler[idx]] ?? '—',
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
