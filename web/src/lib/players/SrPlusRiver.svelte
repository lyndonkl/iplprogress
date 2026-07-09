<script lang="ts">
	/**
	 * Panel A - SR+ River (hero; storyboard 9.3). SR+ by season as a LINE over a flat
	 * 100 baseline: 100 = an average batter that season, above = he scored faster than
	 * his era's peers. The line BREAKS at any season under 100 balls (never interpolated,
	 * never dropped to zero); those seasons get a neutral gap tick in the top margin.
	 * No zero baseline; y-domain kept roughly symmetric so 100 is always on screen. The
	 * peak is marked as "biggest edge over his era" (era-relative, never "improvement").
	 */
	import type { League, PeakSRPlus, SRPlusPoint } from './data';
	import { fmt1, leagueName } from './copy';

	let { points, peak, league }: { points: SRPlusPoint[]; peak: PeakSRPlus | null; league: League } =
		$props();

	interface Dot {
		x: number;
		y: number;
		season: number;
		srplus: number;
		sr: number | null;
	}
	interface Gap {
		x: number;
		season: number;
	}

	const V = $derived.by(() => {
		const W = 340;
		const H = 190;
		const mL = 12;
		const mR = 14;
		const mT = 30;
		const mB = 26;
		const x0 = mL;
		const x1 = W - mR;
		const y0 = mT;
		const y1 = H - mB;
		const plotW = x1 - x0;
		const plotH = y1 - y0;
		const n = points.length;
		const xFor = (i: number): number => (n > 1 ? x0 + (i / (n - 1)) * plotW : (x0 + x1) / 2);

		const data: number[] = [];
		for (const p of points) if (p.hasData && p.srplus != null) data.push(p.srplus);
		let dmin = Math.min(100, ...data);
		let dmax = Math.max(100, ...data);
		if (!isFinite(dmin) || !isFinite(dmax)) {
			dmin = 90;
			dmax = 110;
		}
		const pad = Math.max(8, (dmax - dmin) * 0.18);
		let yMin = dmin - pad;
		let yMax = dmax + pad;
		yMin = Math.max(40, Math.min(yMin, 92));
		yMax = Math.min(220, Math.max(yMax, 108));
		const yFor = (v: number): number => y1 - ((v - yMin) / (yMax - yMin)) * plotH;

		// Broken segments: a fresh subpath after every gap season.
		const paths: string[] = [];
		let cur: string[] = [];
		points.forEach((p, i) => {
			if (p.hasData && p.srplus != null) {
				cur.push(`${xFor(i).toFixed(2)} ${yFor(p.srplus).toFixed(2)}`);
			} else if (cur.length) {
				paths.push('M' + cur.join(' L'));
				cur = [];
			}
		});
		if (cur.length) paths.push('M' + cur.join(' L'));

		const dots: Dot[] = [];
		const gaps: Gap[] = [];
		points.forEach((p, i) => {
			if (p.hasData && p.srplus != null) {
				dots.push({ x: xFor(i), y: yFor(p.srplus), season: p.season, srplus: p.srplus, sr: p.sr });
			} else {
				gaps.push({ x: xFor(i), season: p.season });
			}
		});

		let peakPt: Dot | null = null;
		if (peak) {
			const i = points.findIndex((p) => p.season === peak.season && p.hasData);
			if (i >= 0)
				peakPt = { x: xFor(i), y: yFor(peak.srplus), season: peak.season, srplus: peak.srplus, sr: peak.sr };
		}

		const first = points[0]?.season ?? 0;
		const last = points[points.length - 1]?.season ?? 0;
		return {
			W,
			H,
			x0,
			x1,
			y0,
			y1,
			y100: yFor(100),
			gapTop: mT - 12,
			gapBot: mT - 4,
			paths,
			dots,
			gaps,
			peakPt,
			first,
			last,
			xFirst: xFor(0),
			xLast: xFor(n - 1),
			labelY: H - mB + 13
		};
	});
</script>

<figure class="river">
	<figcaption>
		<p class="orient">
			100 is an average {leagueName(league)} batter that season. Above the line means they scored
			faster than their peers, priced against their own era, not today's.
		</p>
		{#if peak}
			<p class="point">
				Their biggest edge over their era came in {peak.season}: SR+ {fmt1(peak.srplus)}.
			</p>
		{/if}
	</figcaption>

	<svg
		viewBox="0 0 {V.W} {V.H}"
		role="img"
		aria-label="Strike-rate-plus by season for this batter, era-adjusted, over a baseline of 100"
	>
		<!-- 100 reference line (era baseline) -->
		<line class="ref" x1={V.x0} y1={V.y100} x2={V.x1} y2={V.y100} />
		<text class="ref-label" x={V.x0 + 1} y={V.y100 - 3}>
			100 = an average {leagueName(league)} batter
		</text>

		<!-- gap ticks (neutral top-margin position; never near the value axis) -->
		{#each V.gaps as g (g.season)}
			<line class="gap" x1={g.x} y1={V.gapTop} x2={g.x} y2={V.gapBot}>
				<title>{g.season}: too few balls this season (under 100 faced)</title>
			</line>
		{/each}

		<!-- broken SR+ line -->
		{#each V.paths as d, i (i)}
			<path class="line" d={d} />
		{/each}

		<!-- season dots -->
		{#each V.dots as dot (dot.season)}
			<circle class="dot" cx={dot.x} cy={dot.y} r="2.4">
				<title>{dot.season}: SR+ {fmt1(dot.srplus)}{dot.sr != null ? `, raw SR ${fmt1(dot.sr)}` : ''}</title>
			</circle>
		{/each}

		<!-- peak marker -->
		{#if V.peakPt}
			<circle class="peak-ring" cx={V.peakPt.x} cy={V.peakPt.y} r="4.6" />
			<circle class="peak-dot" cx={V.peakPt.x} cy={V.peakPt.y} r="2.6" />
			<text
				class="peak-label"
				x={V.peakPt.x}
				y={V.peakPt.y - 8}
				text-anchor={V.peakPt.x > V.W / 2 ? 'end' : 'start'}
			>
				biggest edge, {V.peakPt.season}
			</text>
		{/if}

		<!-- anchor-only x labels -->
		<text class="axis" x={V.xFirst} y={V.labelY} text-anchor="start">{V.first}</text>
		{#if V.last !== V.first}
			<text class="axis" x={V.xLast} y={V.labelY} text-anchor="end">{V.last}</text>
		{/if}
	</svg>
</figure>

<style>
	.river {
		margin: 0;
	}
	figcaption {
		margin-bottom: 0.5rem;
	}
	.orient {
		margin: 0;
		font-size: 0.9rem;
		line-height: 1.45;
		color: var(--ink-dim);
	}
	.point {
		margin: 0.35rem 0 0;
		font-size: 0.95rem;
		line-height: 1.4;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	svg {
		display: block;
		width: 100%;
		height: auto;
		max-width: 560px;
	}
	.ref {
		stroke: var(--ink-dim);
		stroke-width: 0.8;
		opacity: 0.55;
	}
	.ref-label {
		fill: var(--ink-dim);
		font-size: 7px;
		opacity: 0.85;
	}
	.gap {
		stroke: var(--ink-dim);
		stroke-width: 1.4;
		opacity: 0.4;
	}
	.line {
		fill: none;
		stroke: var(--gold);
		stroke-width: 2;
		stroke-linejoin: round;
		stroke-linecap: round;
	}
	.dot {
		fill: var(--gold);
	}
	.peak-ring {
		fill: none;
		stroke: var(--ink);
		stroke-width: 1.2;
		opacity: 0.9;
	}
	.peak-dot {
		fill: var(--ink);
	}
	.peak-label {
		fill: var(--ink);
		font-size: 8px;
		font-weight: 600;
	}
	.axis {
		fill: var(--ink-dim);
		font-size: 8px;
		font-variant-numeric: tabular-nums;
	}
</style>
