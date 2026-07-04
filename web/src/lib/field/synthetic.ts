import type { FieldData, GroupMeta } from './types';

/**
 * Dev-only synthetic fallback field.
 *
 * This module is only ever reached through the `import.meta.env.DEV` branch in
 * `data.ts`. In production builds that branch is statically dead, the dynamic
 * import is eliminated, and this file never becomes a chunk — the synthetic
 * path cannot ship.
 */

const SYNTH_N = 316_388;

/** Deterministic PRNG so the dev field is stable across reloads. */
function mulberry32(seed: number): () => number {
	let a = seed >>> 0;
	return () => {
		a = (a + 0x6d2b79f5) | 0;
		let t = Math.imul(a ^ (a >>> 15), 1 | a);
		t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}

export function syntheticFieldData(): FieldData {
	const rng = mulberry32(20080418);

	// WPL: 88-ish matches over 4 seasons.
	const wplCounts = [4830, 5170, 5390, 5730]; // 21,120
	const wplTotal = wplCounts.reduce((s, c) => s + c, 0);

	// IPL: remaining points ramped across 19 seasons (leagues grew over time).
	const iplTotal = SYNTH_N - wplTotal;
	const weights: number[] = [];
	for (let i = 0; i < 19; i++) weights.push(0.78 + (0.44 * i) / 18);
	const wSum = weights.reduce((s, w) => s + w, 0);
	const iplCounts = weights.map((w) => Math.floor((iplTotal * w) / wSum));
	const allocated = iplCounts.reduce((s, c) => s + c, 0);
	iplCounts[iplCounts.length - 1] += iplTotal - allocated;

	const groups: GroupMeta[] = [];
	iplCounts.forEach((count, i) =>
		groups.push({ gi: groups.length, league: 'ipl', season: 2008 + i, count })
	);
	wplCounts.forEach((count, i) =>
		groups.push({ gi: groups.length, league: 'wpl', season: 2023 + i, count })
	);

	const groupIds = new Uint16Array(SYNTH_N);
	const attrs = new Uint8Array(SYNTH_N);
	let p = 0;
	for (const g of groups) {
		const isWpl = g.league === 'wpl';
		// aggression drifts up with season, so even fake data "reads"
		const eraLift = g.league === 'ipl' ? (g.season - 2008) / 18 : 0.55;
		for (let i = 0; i < g.count; i++) {
			groupIds[p] = g.gi;
			attrs[p] = syntheticAttrByte(rng, eraLift, isWpl);
			p++;
		}
	}

	return { nPoints: SYNTH_N, groups, groupIds, attrs, synthetic: true };
}

function syntheticAttrByte(rng: () => number, eraLift: number, isWpl: boolean): number {
	const r = rng();
	// rough T20 outcome mix, boundary share drifting up with eraLift
	const four = 0.1 + 0.035 * eraLift + (isWpl ? 0.02 : 0);
	const six = 0.04 + 0.03 * eraLift - (isWpl ? 0.015 : 0);
	const dot = 0.38 - 0.05 * eraLift;
	const single = 0.36;
	const twoThree = 0.09;
	let cls: number;
	if (r < dot) cls = 0;
	else if (r < dot + single) cls = 1;
	else if (r < dot + single + twoThree) cls = 2;
	else if (r < dot + single + twoThree + four) cls = 3;
	else if (r < dot + single + twoThree + four + six) cls = 4;
	else cls = 5;
	const wicket = rng() < 0.049 ? 1 : 0;
	return (cls & 0b111) | (wicket << 3) | ((isWpl ? 1 : 0) << 4);
}
