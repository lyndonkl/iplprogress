import type { Columnar, MatchInfo } from '../data';

/**
 * THE BOWL, linked-panel selection stats (r6b spec section 5).
 *
 * `computeSelectionStats(col, matches, mask)` runs ONE pass over the masked indices
 * (demand-mode, panel-open-gated) and returns three small oriented views of the
 * CURRENT selection, coordinated with the field because it consumes the SAME mask:
 *  - worm: cumulative runs over the selection in point (ball) order, so "the runs
 *                piled up"; if EXACTLY one batter is in the selection it uses that
 *                batter's cumulative runs-off-the-bat so it reads as one innings.
 *  - manhattan: runs per over + wickets per over (the red caps).
 *  - leaderboard: top run-scorers (by runs off the bat) and top wicket-takers (by
 *                bowler-credited wickets; run-outs and retirements are excluded, as a
 *                bowler is not credited with them) in the selection.
 *
 * Everything is accumulated in the single masked pass. `matches` is accepted for
 * parity with the panel's data inputs (the worm/Manhattan/leaderboard need only the
 * columnar arrays); it is reserved for match-level annotations.
 *
 * R7b credibility (additive): the same single pass also tallies per-batter balls
 * faced and league, and per-bowler balls bowled and runs conceded, so the trust
 * meter (balls vs the stat M) and the batting shrinkage slider can read a sample
 * size per row without a second pass. BatterRow/BowlerRow GAIN fields; the existing
 * .runs / .wickets readers are untouched. The batter candidate pool widens to
 * LEADER_POOL so a shrinkage leader outside the raw top-8 can surface; the UI still
 * shows eight by whichever ordering is active.
 */

export interface WormPoint {
	/** ball ordinal within the selection (0 = the origin, then 1, 2, …) */
	x: number;
	/** cumulative runs at that ordinal */
	y: number;
}

export interface OverBar {
	/** 0-based over index (the UI adds 1 for "Overs 1 to 20") */
	over: number;
	/** total runs scored in this over across the selection */
	runs: number;
	/** wickets that fell in this over across the selection (the red caps) */
	wickets: number;
}

export interface BatterRow {
	name: string;
	runs: number;
	/** R7b: balls faced in the selection (trust n + strike-rate denominator) */
	balls: number;
	/** R7b: league code (0 ipl, 1 wpl), so the shrinkage leans on the own-league mean */
	league: number;
}

export interface BowlerRow {
	name: string;
	wickets: number;
	/** R7b: balls bowled in the selection (trust n vs the economy M) */
	balls: number;
	/** R7b: runs conceded in the selection (companion field; not ranked in R7b) */
	runsConceded: number;
}

export interface Leaderboard {
	batters: BatterRow[];
	bowlers: BowlerRow[];
}

export interface SelectionStats {
	/** balls in the selection (mirrors the mask's non-zero count) */
	count: number;
	/** total runs across the selection */
	totalRuns: number;
	/** total wickets across the selection */
	totalWickets: number;
	/** true when the worm y is a single batter's runs off the bat (not the total) */
	singleBatter: boolean;
	worm: WormPoint[];
	manhattan: OverBar[];
	leaderboard: Leaderboard;
}

/** cap the worm polyline so a 316k selection is still a light SVG */
const MAX_WORM_POINTS = 240;
/** top-N shown for each leaderboard list */
const LEADER_TOP = 8;
/**
 * R7b: the batter CANDIDATE pool the shrinkage slider re-ranks. Wider than the shown
 * eight so a batter outside the raw top-8 can surface once ranked by best-guess skill
 * (the UI still shows eight by the active ordering). Never scope the re-rank to the
 * shown eight, which would hide a promoted leader (a lie by omission).
 */
const LEADER_POOL = 25;
/** always show a full 20-over Manhattan (a phase selection reads as a shape) */
const MIN_OVERS = 20;

/** wicket_kind names NOT credited to the bowler (a fielding / retirement event). */
const NON_BOWLER_KINDS = new Set(['run out', 'retired hurt', 'retired out', 'obstructing the field']);

export function computeSelectionStats(
	col: Columnar,
	matches: MatchInfo[],
	mask: Uint8Array
): SelectionStats {
	void matches; // reserved for match-level annotations; the three views need only columnar
	const n = col.n_points;
	const a = col.arrays;

	// wicket_kind dict indices that do NOT count toward a bowler's tally
	const excludedKind = new Set<number>();
	col.dicts.wicket_kind.forEach((name, i) => {
		if (NON_BOWLER_KINDS.has(name)) excludedKind.add(i);
	});

	// cheap prepass: how many balls are in the selection (drives the worm stride)
	let count = 0;
	for (let i = 0; i < n; i++) if (mask[i]) count++;
	const step = Math.max(1, Math.ceil(count / MAX_WORM_POINTS));

	const runsByOver: number[] = [];
	const wktByOver: number[] = [];
	const batterRuns = new Map<number, number>();
	const bowlerWkts = new Map<number, number>();
	// R7b additive tallies, all filled in the SAME masked pass (no new pass):
	const batterBalls = new Map<number, number>();
	const batterLeague = new Map<number, number>();
	const bowlerBalls = new Map<number, number>();
	const bowlerRuns = new Map<number, number>();

	// worm samples (both cumulative series so the single-batter choice is one pass)
	const sx: number[] = [];
	const sTotal: number[] = [];
	const sBatter: number[] = [];

	let ordinal = 0;
	let cumTotal = 0;
	let cumBatter = 0;
	let totalWickets = 0;
	let maxOver = MIN_OVERS - 1;
	let firstBatter = -1;
	let multiBatter = false;

	for (let i = 0; i < n; i++) {
		if (!mask[i]) continue;
		const rt = a.runs_total[i];
		const rb = a.runs_batter[i];
		const ov = a.over[i];
		const isWkt = a.wicket[i] === 1;
		const bi = a.batter[i];
		const bw = a.bowler[i];

		ordinal++;
		cumTotal += rt;
		cumBatter += rb;
		if (ov > maxOver) maxOver = ov;

		runsByOver[ov] = (runsByOver[ov] ?? 0) + rt;
		if (isWkt) {
			wktByOver[ov] = (wktByOver[ov] ?? 0) + 1;
			totalWickets++;
			if (!excludedKind.has(a.wicket_kind[i])) {
				bowlerWkts.set(bw, (bowlerWkts.get(bw) ?? 0) + 1);
			}
		}
		if (rb !== 0) batterRuns.set(bi, (batterRuns.get(bi) ?? 0) + rb);

		// R7b: sample-size tallies per batter and per bowler for the trust meter and
		// the batting shrinkage slider. Balls in the selection are the denominator;
		// league is captured once (a batter belongs to exactly one league).
		batterBalls.set(bi, (batterBalls.get(bi) ?? 0) + 1);
		if (!batterLeague.has(bi)) batterLeague.set(bi, a.league[i]);
		bowlerBalls.set(bw, (bowlerBalls.get(bw) ?? 0) + 1);
		bowlerRuns.set(bw, (bowlerRuns.get(bw) ?? 0) + rt);

		if (firstBatter < 0) firstBatter = bi;
		else if (!multiBatter && bi !== firstBatter) multiBatter = true;

		if ((ordinal - 1) % step === 0) {
			sx.push(ordinal);
			sTotal.push(cumTotal);
			sBatter.push(cumBatter);
		}
	}

	// always end the worm on the true final total
	if (ordinal > 0 && (sx.length === 0 || sx[sx.length - 1] !== ordinal)) {
		sx.push(ordinal);
		sTotal.push(cumTotal);
		sBatter.push(cumBatter);
	}

	const singleBatter = firstBatter >= 0 && !multiBatter;
	const series = singleBatter ? sBatter : sTotal;
	const worm: WormPoint[] = [];
	if (sx.length > 0) worm.push({ x: 0, y: 0 }); // origin, so the line starts at the baseline
	for (let k = 0; k < sx.length; k++) worm.push({ x: sx[k], y: series[k] });

	const manhattan: OverBar[] = [];
	for (let ov = 0; ov <= maxOver; ov++) {
		manhattan.push({ over: ov, runs: runsByOver[ov] ?? 0, wickets: wktByOver[ov] ?? 0 });
	}

	const leaderboard: Leaderboard = {
		batters: topBatters(batterRuns, batterBalls, batterLeague, col.dicts.batter),
		bowlers: topBowlers(bowlerWkts, bowlerBalls, bowlerRuns, col.dicts.bowler)
	};

	return { count, totalRuns: cumTotal, totalWickets, singleBatter, worm, manhattan, leaderboard };
}

/**
 * The batter candidate pool, runs-sorted (the raw order). Widened to LEADER_POOL so
 * the shrinkage slider can surface a best-guess leader from outside the raw top-8;
 * the panel slices to eight by the active ordering (raw runs, or regressed skill).
 * Each row carries its selection balls and league for the trust dot and shrinkage.
 */
function topBatters(
	runs: Map<number, number>,
	balls: Map<number, number>,
	league: Map<number, number>,
	dict: string[]
): BatterRow[] {
	return [...runs.entries()]
		.map(([idx, v]) => ({
			name: dict[idx] ?? '-',
			runs: v,
			balls: balls.get(idx) ?? 0,
			league: league.get(idx) ?? 0
		}))
		.sort((p, q) => q.runs - p.runs || p.name.localeCompare(q.name))
		.slice(0, LEADER_POOL);
}

function topBowlers(
	wkts: Map<number, number>,
	balls: Map<number, number>,
	runs: Map<number, number>,
	dict: string[]
): BowlerRow[] {
	return [...wkts.entries()]
		.map(([idx, v]) => ({
			name: dict[idx] ?? '-',
			wickets: v,
			balls: balls.get(idx) ?? 0,
			runsConceded: runs.get(idx) ?? 0
		}))
		.sort((p, q) => q.wickets - p.wickets || p.name.localeCompare(q.name))
		.slice(0, LEADER_TOP);
}
