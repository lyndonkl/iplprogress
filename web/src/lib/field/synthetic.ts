import type { FieldData, GroupMeta, TeamMeta } from './types';

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
	const ballsFaced = new Uint8Array(SYNTH_N);
	const team = new Uint8Array(SYNTH_N);
	const wallHeat = new Uint8Array(SYNTH_N);
	// Ch 2 worm-space y (§13): batter cumulative innings runs, reset each innings.
	const cumRuns = new Uint8Array(SYNTH_N);
	// neutral byte = the pooled 2008-2010 batter (matches the pipeline encoding);
	// synthetic heat rises for recent seasons at low ball-index so the dev wall
	// visibly ignites bottom→top when the C1-2 heat beat is exercised.
	const NEUTRAL01 = 73 / 255;
	let p = 0;
	for (const g of groups) {
		const isWpl = g.league === 'wpl';
		// aggression drifts up with season, so even fake data "reads"
		const eraLift = g.league === 'ipl' ? (g.season - 2008) / 18 : 0.55;
		let bf = 1;
		let runsSoFar = 0;
		let battingTeam = pickTeam(rng, isWpl);
		for (let i = 0; i < g.count; i++) {
			groupIds[p] = g.gi;
			attrs[p] = syntheticAttrByte(rng, eraLift, isWpl);
			// rough balls-faced ramp: most balls are early-innings balls
			ballsFaced[p] = Math.min(255, bf);
			// cumulative innings runs from the outcome class (worm-space y)
			const cls = attrs[p] & 0b111;
			const ballRuns = cls === 0 ? 0 : cls === 1 ? 1 : cls === 2 ? 2 : cls === 3 ? 4 : cls === 4 ? 6 : 1;
			runsSoFar = Math.min(255, runsSoFar + ballRuns);
			cumRuns[p] = runsSoFar;
			// synthetic run-out flag (attrs bit 6, §14): a share of wickets, higher
			// in the early eras so the dev cascade visibly shrinks 2008 → 2026.
			if ((attrs[p] & 0b1000) !== 0) {
				const roShare = isWpl ? 0.07 : 0.12 - 0.07 * eraLift;
				if (rng() < roShare) attrs[p] |= 0b0100_0000;
			}
			// era-relative intent: early balls (low bf) in recent seasons run hot
			// above the neutral 2008-2010 pivot; 2008 rows sit near neutral.
			const earlyWeight = 1 - Math.min(1, (bf - 1) / 29);
			const heat01 = NEUTRAL01 + eraLift * earlyWeight * 0.62 + (rng() - 0.5) * 0.08;
			wallHeat[p] = Math.max(0, Math.min(255, Math.round(heat01 * 255)));
			if (rng() < 0.12) {
				bf = 1; // "new batter" — the innings worm restarts at (1, 0)
				runsSoFar = 0;
			} else {
				bf = Math.min(255, bf + 1);
			}
			if (rng() < 0.008) battingTeam = pickTeam(rng, isWpl); // "new innings"
			team[p] = battingTeam;
			p++;
		}
	}

	return {
		nPoints: SYNTH_N,
		meta: { n_points: SYNTH_N, built_at: 'synthetic', point_order: 'chronological' },
		groups,
		teams: syntheticTeams(),
		groupIds,
		attrs,
		ballsFaced,
		team,
		wallHeat,
		cumRuns,
		synthetic: true
	};
}

const SYNTH_PALETTE = [
	'#FDB913',
	'#004BA0',
	'#EC1C24',
	'#3A225D',
	'#EA1A8E',
	'#F26522',
	'#DD1F2D',
	'#282968',
	'#00A3E0',
	'#1B2133'
];

function syntheticTeams(): TeamMeta[] {
	const teams: TeamMeta[] = [];
	for (let i = 0; i < 15; i++)
		teams.push({
			id: i,
			league: 'ipl',
			name: `Synthetic IPL ${i + 1}`,
			short: `S${i + 1}`,
			color: SYNTH_PALETTE[i % SYNTH_PALETTE.length],
			active: i < 10
		});
	for (let i = 0; i < 5; i++)
		teams.push({
			id: 15 + i,
			league: 'wpl',
			name: `Synthetic WPL ${i + 1}`,
			short: `W${i + 1}`,
			color: SYNTH_PALETTE[(i + 3) % SYNTH_PALETTE.length],
			active: true
		});
	return teams;
}

function pickTeam(rng: () => number, isWpl: boolean): number {
	return isWpl ? 15 + Math.floor(rng() * 5) : Math.floor(rng() * 15);
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
