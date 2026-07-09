/**
 * R7a PLAYER CARDS - the bridge back INTO the Bowl (the 316k-ball field).
 *
 * The Bowl restores a view from a `#bowl?...` hash whose batter/bowler are DICT
 * INDICES (`b`/`w`), versioned by `v` (sandbox/url.ts). Those indices live only in
 * the field's columnar dict, so we resolve a NAME to an index by lazily loading the
 * sandbox dataset. That load is heavy (the whole columnar), so it happens ONLY on an
 * explicit tap, never on card paint, and is cached module-level (the sandbox loader
 * memoizes), so a second tap is instant. Runtime-imports nothing from the field: the
 * sandbox loader's only value import is `$app/paths` (its field imports are types).
 */

import { base } from '$app/paths';
import { goto } from '$app/navigation';
import { loadSandboxData } from '$lib/scenes/sandbox/data';
import { URL_VERSION } from '$lib/scenes/sandbox/url';

/** Resolve the first of `names` present in the given side's dict, or null. */
async function resolveIndex(names: string[], side: 'bat' | 'bowl'): Promise<number | null> {
	const data = await loadSandboxData();
	const dict = side === 'bat' ? data.nameIndex.batter : data.nameIndex.bowler;
	for (const n of names) {
		const i = dict.get(n);
		if (i !== undefined) return i;
	}
	return null;
}

/**
 * Open a selection in the Bowl. `batterNames` / `bowlerNames` are each a spelling
 * list (nameUnion or a single opponent name); the first that resolves wins. A side
 * that resolves to nothing is simply omitted (the Bowl's never-blank open covers a
 * fully-unresolved link). Always navigates; never throws to the caller.
 */
export async function openInBowl(opts: {
	batterNames?: string[];
	bowlerNames?: string[];
}): Promise<void> {
	const parts: string[] = [];
	if (opts.batterNames?.length) {
		const bi = await resolveIndex(opts.batterNames, 'bat');
		if (bi !== null) parts.push(`b=${bi}`);
	}
	if (opts.bowlerNames?.length) {
		const wi = await resolveIndex(opts.bowlerNames, 'bowl');
		if (wi !== null) parts.push(`w=${wi}`);
	}
	parts.push(`v=${URL_VERSION}`);
	await goto(`${base}/#bowl?${parts.join('&')}`);
}
