<script lang="ts">
	/**
	 * Panel D - Teleporter (storyboard 9.5; highest overclaim risk on the card). One
	 * 2026-strike-rate axis. The HONEST re-quote is a solid, bright, FILLED band (an
	 * interval) and is read first; the NAIVE carry-over is a dim, dashed, hollow ghost
	 * labelled "raw carry-over, ignores the era." The band's full width is guaranteed by
	 * the data layer to be <= the naive-vs-honest gap, so the band renders as the compact,
	 * truer quantity and the ghost sits distinctly apart. Copy is RANK-TRANSLATION only:
	 * how far above his own era he sat, put at the same rank among 2026 batters. It never
	 * restates that as a single present-day scoring figure or a named present-day
	 * equivalent. Cross-era is a range, not a verdict.
	 */
	import { base } from '$app/paths';
	import type { Teleporter } from './data';
	import { fmt1, freshnessNote, leagueName } from './copy';

	let { tp, halfLife = null }: { tp: Teleporter; halfLife?: number | null } = $props();

	const topPct = $derived(Math.max(1, Math.round(100 - tp.eraPercentile)));

	// §9.2 freshness: a plain SENTENCE folded into the note (never an arc gauge, no
	// retained% number, OFF the band). Named to the SR+ half-life; suppressed if the
	// half-life failed to load or the peak is not before the target season.
	const gap = $derived(tp.targetSeason - tp.season);
	const freshness = $derived(
		halfLife != null && gap > 0 ? freshnessNote(gap, halfLife, tp.targetSeason) : null
	);

	const V = $derived.by(() => {
		const W = 340;
		const H = 118;
		const padL = 16;
		const padR = 16;
		const axisY = 66;
		const lo = tp.honestBand[0];
		const hi = tp.honestBand[1];
		const mid = tp.honestMid;
		const naive = tp.naive2026SR;
		const vals = [lo, hi, mid, naive];
		const dmin = Math.min(...vals);
		const dmax = Math.max(...vals);
		const span = Math.max(4, dmax - dmin);
		const pad = span * 0.35 + 2;
		const domMin = dmin - pad;
		const domMax = dmax + pad;
		const x = (v: number): number => padL + ((v - domMin) / (domMax - domMin)) * (W - padL - padR);
		const clampLabel = (v: number): number => Math.max(padL + 12, Math.min(W - padR - 12, x(v)));
		return {
			W,
			H,
			axisY,
			xMin: x(domMin),
			xMax: x(domMax),
			bandX: x(lo),
			bandW: Math.max(2, x(hi) - x(lo)),
			midX: x(mid),
			naiveX: x(naive),
			midLabelX: clampLabel(mid),
			naiveLabelX: clampLabel(naive),
			midVal: fmt1(mid),
			naiveVal: fmt1(naive)
		};
	});
</script>

<div class="teleporter">
	<p class="orient">
		This axis is 2026 strike rate. The bright band is where their era-rank lands among today's {leagueName(
			tp.league
		)} batters. Read it first.
	</p>

	<svg
		viewBox="0 0 {V.W} {V.H}"
		role="img"
		aria-label="Their peak season re-priced to 2026: a bright honest band beside a dim naive carry-over"
	>
		<line class="axis" x1={V.xMin} y1={V.axisY} x2={V.xMax} y2={V.axisY} />

		<!-- naive ghost (dim, dashed, hollow): read second -->
		<line class="ghost-line" x1={V.naiveX} y1={V.axisY - 14} x2={V.naiveX} y2={V.axisY + 14} />
		<circle class="ghost-dot" cx={V.naiveX} cy={V.axisY} r="3" />
		<text class="ghost-label" x={V.naiveLabelX} y={V.axisY - 19} text-anchor="middle">
			naive {V.naiveVal}
		</text>

		<!-- honest band (bright, filled): read first -->
		<rect class="band" x={V.bandX} y={V.axisY - 9} width={V.bandW} height="18" rx="3" />
		<line class="band-mid" x1={V.midX} y1={V.axisY - 11} x2={V.midX} y2={V.axisY + 11} />
		<text class="band-label" x={V.midLabelX} y={V.axisY + 24} text-anchor="middle">
			honest {V.midVal}
		</text>
	</svg>

	<p class="point">
		Measured against their own era they sat in the top {topPct}% of batters. Put that same rank among
		2026 {leagueName(tp.league)} batters and it lands in this band.
	</p>
	<p class="note">
		The naive number pretends 2026 is their era. It isn't. Cross-era is a range, not a verdict, so the
		band, not a single figure, is the answer.{freshness ? ` ${freshness}` : ''}
	</p>
	<p class="link">
		<a href="{base}/#ch10">See how their era compares</a>
	</p>
</div>

<style>
	.teleporter {
		margin: 0;
	}
	.orient {
		margin: 0 0 0.5rem;
		font-size: 0.9rem;
		line-height: 1.45;
		color: var(--ink-dim);
	}
	svg {
		display: block;
		width: 100%;
		height: auto;
		max-width: 560px;
	}
	.axis {
		stroke: var(--ink-dim);
		stroke-width: 0.8;
		opacity: 0.5;
	}
	.ghost-line {
		stroke: var(--ink-dim);
		stroke-width: 1.2;
		stroke-dasharray: 3 2.5;
		opacity: 0.7;
	}
	.ghost-dot {
		fill: none;
		stroke: var(--ink-dim);
		stroke-width: 1;
		opacity: 0.7;
	}
	.ghost-label {
		fill: var(--ink-dim);
		font-size: 8px;
		font-variant-numeric: tabular-nums;
	}
	.band {
		fill: var(--gold);
		opacity: 0.9;
	}
	.band-mid {
		stroke: var(--bg);
		stroke-width: 1.4;
	}
	.band-label {
		fill: var(--ink);
		font-size: 8.5px;
		font-weight: 600;
		font-variant-numeric: tabular-nums;
	}
	.point {
		margin: 0.5rem 0 0;
		font-size: 0.95rem;
		line-height: 1.4;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	.note {
		margin: 0.35rem 0 0;
		font-size: 0.8rem;
		line-height: 1.45;
		color: var(--ink-dim);
	}
	.link {
		margin: 0.5rem 0 0;
		font-size: 0.85rem;
	}
	.link a {
		color: var(--teal);
	}
	.link a:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
</style>
