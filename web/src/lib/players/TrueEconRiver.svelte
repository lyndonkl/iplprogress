<script lang="ts">
	/**
	 * Bowler TrueEcon river (storyboard 9.4). The SR+ river's bowling twin: TrueEcon+
	 * by season as a LINE over a flat 100 baseline, where 100 = a par bowler that
	 * season and ABOVE the line = they leaked fewer runs than their era's peers. Plotted
	 * on the 100 baseline (never a 0-baseline runs-saved line) so it mirrors the SR+
	 * river with no relearning: for both, up is better. The line BREAKS at any season
	 * under the min-legal-balls floor (never interpolated); those seasons get a neutral
	 * gap tick. The peak is "biggest edge over their era", with the runs saved as the
	 * caption GLOSS, not the axis. The §9.1 trust dot applies with the economy stat's
	 * own M (a season short of it reads dim/hollow).
	 */
	import type { League, PeakTrueEcon, TrueEconPoint, TrustState } from './data';
	import { trustState } from './data';
	import {
		fmt1,
		trueEconOrient,
		trueEconPeakBelowPar,
		trueEconPeakGloss,
		trustLegend
	} from './copy';

	let {
		points,
		peak,
		league,
		m = null
	}: { points: TrueEconPoint[]; peak: PeakTrueEcon | null; league: League; m?: number | null } =
		$props();

	interface Dot {
		x: number;
		y: number;
		season: number;
		trueeconPlus: number;
		trueEconomy: number | null;
		balls: number | null;
		trust: TrustState;
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
		for (const p of points) if (p.hasData && p.trueeconPlus != null) data.push(p.trueeconPlus);
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
			if (p.hasData && p.trueeconPlus != null) {
				cur.push(`${xFor(i).toFixed(2)} ${yFor(p.trueeconPlus).toFixed(2)}`);
			} else if (cur.length) {
				paths.push('M' + cur.join(' L'));
				cur = [];
			}
		});
		if (cur.length) paths.push('M' + cur.join(' L'));

		const dots: Dot[] = [];
		const gaps: Gap[] = [];
		let hasNoisy = false;
		let hasNonSettled = false;
		points.forEach((p, i) => {
			if (p.hasData && p.trueeconPlus != null) {
				const trust = trustState(p.balls, m);
				if (trust === 'noisy') hasNoisy = true;
				if (trust === 'firming' || trust === 'noisy') hasNonSettled = true;
				dots.push({
					x: xFor(i),
					y: yFor(p.trueeconPlus),
					season: p.season,
					trueeconPlus: p.trueeconPlus,
					trueEconomy: p.trueEconomy,
					balls: p.balls,
					trust
				});
			} else {
				gaps.push({ x: xFor(i), season: p.season });
			}
		});

		let peakPt: Dot | null = null;
		if (peak) {
			const i = points.findIndex((p) => p.season === peak.season && p.hasData);
			if (i >= 0)
				peakPt = {
					x: xFor(i),
					y: yFor(peak.trueeconPlus),
					season: peak.season,
					trueeconPlus: peak.trueeconPlus,
					trueEconomy: peak.trueEconomy,
					balls: peak.balls,
					trust: trustState(peak.balls, m)
				};
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
			labelY: H - mB + 13,
			hasNoisy,
			hasNonSettled
		};
	});

	// §9.4 peak framing: "biggest edge" only when above par; the runs-saved reading is
	// the GLOSS. A rare best-season-under-par bowler gets an honest below-par line.
	const abovePar = $derived(peak != null && peak.trueeconPlus >= 100);
	const peakGloss = $derived(
		peak == null
			? null
			: abovePar
				? trueEconPeakGloss(peak.trueEconomy)
				: trueEconPeakBelowPar(-peak.trueEconomy)
	);
	// §9.1 legend, shown ONLY when a non-settled dot is actually present (exception-only).
	const legend = $derived(V.hasNonSettled ? trustLegend(V.hasNoisy) : null);
</script>

<figure class="river">
	<figcaption>
		<p class="orient">{trueEconOrient(league)}</p>
		{#if peak}
			<p class="point">
				{#if abovePar}
					Their biggest edge over their era came in {peak.season}: TrueEcon+ {fmt1(peak.trueeconPlus)}.
				{:else}
					Their best economy season was {peak.season}: TrueEcon+ {fmt1(peak.trueeconPlus)}.
				{/if}
			</p>
			{#if peakGloss}
				<p class="note">{peakGloss}</p>
			{/if}
		{/if}
		{#if legend}
			<p class="legend">{legend}</p>
		{/if}
	</figcaption>

	<svg
		viewBox="0 0 {V.W} {V.H}"
		role="img"
		aria-label="TrueEcon-plus by season for this bowler, era-adjusted, over a baseline of 100"
	>
		<!-- 100 reference line (era par) -->
		<line class="ref" x1={V.x0} y1={V.y100} x2={V.x1} y2={V.y100} />
		<text class="ref-label" x={V.x0 + 1} y={V.y100 - 3}>100 = a par {league === 'wpl' ? 'WPL' : 'IPL'} bowler</text>

		<!-- gap ticks (neutral top-margin position; never near the value axis) -->
		{#each V.gaps as g (g.season)}
			<line class="gap" x1={g.x} y1={V.gapTop} x2={g.x} y2={V.gapBot}>
				<title>{g.season}: too few overs this season to price against the era</title>
			</line>
		{/each}

		<!-- broken TrueEcon+ line -->
		{#each V.paths as d, i (i)}
			<path class="line" d={d} />
		{/each}

		<!-- season dots: exception-only trust treatment (settled = full; firming = dim
		     filled; noisy = hollow). Fullness is the CVD-safe SHAPE channel. -->
		{#each V.dots as dot (dot.season)}
			<circle class="dot" class:firming={dot.trust === 'firming'} class:noisy={dot.trust === 'noisy'} cx={dot.x} cy={dot.y} r="2.4">
				<title>{dot.season}: TrueEcon+ {fmt1(dot.trueeconPlus)}{(dot.trust === 'firming' || dot.trust === 'noisy') && dot.balls != null && m != null
						? `. ${dot.balls} legal balls, an economy needs about ${Math.round(m)} to settle`
						: ''}</title>
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
				{abovePar ? 'biggest edge' : 'best season'}, {V.peakPt.season}
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
	.note {
		margin: 0.25rem 0 0;
		font-size: 0.8rem;
		line-height: 1.45;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}
	.legend {
		margin: 0.25rem 0 0;
		font-size: 0.75rem;
		line-height: 1.4;
		color: var(--ink-dim);
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
		stroke: var(--teal);
		stroke-width: 2;
		stroke-linejoin: round;
		stroke-linecap: round;
	}
	.dot {
		fill: var(--teal);
	}
	/* firming: filled but dimmed (past the noisy floor, still short of M). */
	.dot.firming {
		fill: var(--teal);
		opacity: 0.72;
	}
	/* noisy: HOLLOW ring (shape channel), never dimmed to illegibility. */
	.dot.noisy {
		fill: none;
		stroke: var(--teal);
		stroke-width: 1;
		opacity: 0.6;
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
