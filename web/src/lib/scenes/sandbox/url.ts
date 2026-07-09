import { NO_FACETS, phaseToOverRange, type Columnar, type Facets, type Phase } from './data';

/**
 * THE BOWL — shareable URL state (r6b spec §6, digest URL section).
 *
 * `encodeFacets(f, flagId?)` -> a compact hash the reader can copy and hand to a
 * mate; `decodeFacets(hash, col)` restores that exact view on mount. The scheme:
 *
 *   #bowl?lg=w&t=13&s=2016&ph=death&o=15-19&oc=36&wk=1&b=<batterIdx>&w=<bowlerIdx>&fl=<id>&v=1
 *
 * Rules (all from the spec):
 *  - Null facets are OMITTED (never `=all`).
 *  - league `lg`: `i` | `w`.
 *  - phase `ph`: `p` | `m` | `d`  OR  a raw over range `o=lo-hi` (0-based). Only one
 *    is written: a phase takes `ph`, an explicit over range takes `o`. On decode a
 *    phase mirrors its over range back in (kept symmetric with the tray).
 *  - outcomes `oc`: compact letters for the off-the-bat codes {0 dot, 1 single,
 *    2 two-or-three, 3 four, 6 six}. Six is code 4 but rides the human-friendly
 *    letter `6`; everything else uses its own code. The wicket toggle is its OWN key
 *    `wk=1` (a separate AND facet), never folded into `oc`.
 *  - batter/bowler by DICT INDEX (`b`/`w`), not name — versioned by `v` so a rebuild
 *    that reorders the dicts invalidates stale links safely.
 *  - a flag id `fl=` is written on a flag view and WINS over the individual facets on
 *    restore (self-describing, reads cleaner); the facets are still written as a
 *    fallback for a client that does not know the flag.
 *  - mode, matchRange internals, the mask, and panel state are NOT encoded.
 *
 * `decodeFacets` never throws: unknown keys are ignored, out-of-range team/season/
 * over/dict-index are clamped or dropped, and a stale `v` falls back to the whole
 * field (a null return -> the caller's never-blank open takes over).
 */

/** Bump when a rebuild reorders the batter/bowler dicts (invalidates stale `b`/`w`). */
export const URL_VERSION = 1;

/** off-the-bat outcome CODE -> url letter (six=4 rides the human-friendly `6`). */
const CODE_TO_OC: Record<number, string> = { 0: '0', 1: '1', 2: '2', 3: '3', 4: '6', 5: '5' };
/** url letter -> outcome CODE (inverse; `6` -> six code 4). */
const OC_TO_CODE: Record<string, number> = { '0': 0, '1': 1, '2': 2, '3': 3, '6': 4, '5': 5 };

const PHASE_TO_CH: Record<Phase, string> = { powerplay: 'p', middle: 'm', death: 'd' };
const CH_TO_PHASE: Record<string, Phase> = { p: 'powerplay', m: 'middle', d: 'death' };

/** The decoded intent of a shared link. */
export interface DecodedView {
	/** a flag id if `fl=` was present (WINS on restore; the caller resolves it) */
	flagId: string | null;
	/** the explicit facets the hash carried, or null if it carried none */
	facets: Facets | null;
}

/** Encode the live selection (and, on a flag view, its `flagId`) to a `#bowl?…` hash. */
export function encodeFacets(f: Facets, flagId?: string | null): string {
	const parts: string[] = [];

	if (f.league === 'ipl') parts.push('lg=i');
	else if (f.league === 'wpl') parts.push('lg=w');

	if (f.team != null) parts.push(`t=${f.team}`);
	if (f.season != null) parts.push(`s=${f.season}`);

	// phase takes ph=; an explicit over range takes o=lo-hi (0-based). Never both.
	if (f.phase) {
		parts.push(`ph=${PHASE_TO_CH[f.phase]}`);
	} else if (f.overLo != null || f.overHi != null) {
		const lo = f.overLo ?? 0;
		const hi = f.overHi ?? 19;
		parts.push(`o=${lo}-${hi}`);
	}

	const oc = f.outcomes ?? 0;
	if (oc !== 0) {
		let letters = '';
		for (let c = 0; c <= 5; c++) if ((oc >> c) & 1) letters += CODE_TO_OC[c];
		if (letters) parts.push(`oc=${letters}`);
	}

	if (f.wicket === true) parts.push('wk=1');
	if (f.batter != null) parts.push(`b=${f.batter}`);
	if (f.bowler != null) parts.push(`w=${f.bowler}`);

	if (flagId) parts.push(`fl=${encodeURIComponent(flagId)}`);

	parts.push(`v=${URL_VERSION}`);
	return `#bowl?${parts.join('&')}`;
}

/**
 * Restore a shared link. Returns null when the hash carries neither a flag nor any
 * facet param (-> the caller falls through to never-blank), or when a stale `v`
 * invalidates the link. Otherwise returns the decoded flag id (if any) and the
 * explicit facets (clamped; never throws).
 */
export function decodeFacets(hash: string, col: Columnar): DecodedView | null {
	const qi = hash.indexOf('?');
	if (qi < 0) return null;
	let params: URLSearchParams;
	try {
		params = new URLSearchParams(hash.slice(qi + 1));
	} catch {
		return null;
	}

	// stale-version guard: a link from a build whose dicts differ falls back to the
	// whole field. An absent `v` is trusted (hand-typed / current).
	const vRaw = params.get('v');
	if (vRaw != null && Number(vRaw) !== URL_VERSION) return null;

	const flagId = params.get('fl');

	const f: Facets = { ...NO_FACETS };
	let any = false;

	const lg = params.get('lg');
	if (lg === 'i') {
		f.league = 'ipl';
		any = true;
	} else if (lg === 'w') {
		f.league = 'wpl';
		any = true;
	}

	const team = intParam(params.get('t'));
	if (team != null && team >= 0) {
		f.team = team;
		any = true;
	}

	const season = intParam(params.get('s'));
	if (season != null && season >= 0) {
		f.season = season;
		any = true;
	}

	// phase takes precedence; it mirrors its over range back in (symmetric).
	const ph = params.get('ph');
	if (ph && CH_TO_PHASE[ph]) {
		const phase = CH_TO_PHASE[ph];
		f.phase = phase;
		const r = phaseToOverRange(phase);
		if (r) {
			f.overLo = r[0];
			f.overHi = r[1];
		}
		any = true;
	} else {
		const o = params.get('o');
		if (o) {
			const m = /^(\d+)-(\d+)$/.exec(o);
			if (m) {
				let lo = clampOver(Number(m[1]));
				let hi = clampOver(Number(m[2]));
				if (lo > hi) [lo, hi] = [hi, lo];
				f.overLo = lo;
				f.overHi = hi;
				f.phase = null;
				any = true;
			}
		}
	}

	const oc = params.get('oc');
	if (oc) {
		let bm = 0;
		for (const ch of oc) {
			const code = OC_TO_CODE[ch];
			if (code != null) bm |= 1 << code;
		}
		if (bm !== 0) {
			f.outcomes = bm;
			any = true;
		}
	}

	if (params.get('wk') === '1') {
		f.wicket = true;
		any = true;
	}

	const b = intParam(params.get('b'));
	if (b != null && b >= 0 && b < col.dicts.batter.length) {
		f.batter = b;
		any = true;
	}

	const w = intParam(params.get('w'));
	if (w != null && w >= 0 && w < col.dicts.bowler.length) {
		f.bowler = w;
		any = true;
	}

	if (!flagId && !any) return null;
	return { flagId: flagId ?? null, facets: any ? f : null };
}

/** Parse an integer param; null on missing / non-integer (never throws). */
function intParam(v: string | null): number | null {
	if (v == null) return null;
	const n = Number(v);
	return Number.isInteger(n) ? n : null;
}

/** Clamp an over index into the valid 0..19 range. */
function clampOver(n: number): number {
	if (!Number.isFinite(n)) return 0;
	return n < 0 ? 0 : n > 19 ? 19 : Math.floor(n);
}
