<script lang="ts">
	import { pct0, type LoyaltyPoint } from './data';

	/**
	 * The loyalty spectrum (C9-6). A 2D line: the share of players four seasons deep
	 * who only ever wore one franchise's shirt, "one-club players", falling from
	 * about 27 in 100 to about 12. Drawn on a 0-BASED y-axis (honest-axis gate) so
	 * the roughly-halving drop falls to visibly half height and the verbal claim is
	 * reinforced, never exaggerated. The peak and the trough are marked as the
	 * before/after pair. The record-holder (Aaron Finch, 9 shirts) is NOT on this
	 * line: he is a separate callout card off the axis (the scene draws it), so two
	 * different measures are never read on one scale. Draws in with `reveal`.
	 */
	interface Props {
		series: LoyaltyPoint[];
		peak: LoyaltyPoint;
		trough: LoyaltyPoint;
		/** y-axis domain, 0-based [0, peakish] */
		yDomain?: [number, number];
		reveal?: number;
		reduced?: boolean;
	}
	let { series, peak, trough, yDomain = [0, 27], reveal = 1, reduced = false }: Props = $props();

	const W = 1000;
	const H = 460;
	const padL = 88;
	const padR = 48;
	const padT = 30;
	const padB = 46;

	const xOf = (i: number): number =>
		series.length <= 1 ? padL : padL + (i / (series.length - 1)) * (W - padL - padR);
	const yOf = (v: number): number => {
		const [lo, hi] = yDomain;
		const t = (v - lo) / (hi - lo);
		return H - padB - t * (H - padT - padB);
	};

	const idxOfSeason = (season: number): number => series.findIndex((s) => s.season === season);

	const drawn = $derived(
		reduced ? series.length : Math.max(2, Math.round((reveal || 0) * series.length))
	);

	const linePts = $derived(
		series
			.slice(0, drawn)
			.map((s, i) => `${xOf(i).toFixed(1)},${yOf(s.pct).toFixed(1)}`)
			.join(' ')
	);

	const areaPts = $derived.by(() => {
		const top = series.slice(0, drawn).map((s, i) => `${xOf(i).toFixed(1)},${yOf(s.pct).toFixed(1)}`);
		if (top.length === 0) return '';
		const x0 = xOf(0).toFixed(1);
		const xN = xOf(drawn - 1).toFixed(1);
		const y0 = yOf(yDomain[0]).toFixed(1);
		return `${x0},${y0} ${top.join(' ')} ${xN},${y0}`;
	});

	const gridVals = $derived([yDomain[0], yDomain[1] / 2, yDomain[1]]);

	const xTicks = $derived.by(() => {
		const step = Math.max(1, Math.ceil(series.length / 6));
		const out: { season: number; x: number }[] = [];
		for (let i = 0; i < series.length; i += step) out.push({ season: series[i].season, x: xOf(i) });
		const last = series.length - 1;
		if (out[out.length - 1]?.season !== series[last].season)
			out.push({ season: series[last].season, x: xOf(last) });
		return out;
	});

	const peakI = $derived(idxOfSeason(peak.season));
	const troughI = $derived(idxOfSeason(trough.season));
	const showPeak = $derived(reduced || peakI < drawn);
	const showTrough = $derived(reduced || troughI < drawn);
</script>

<svg class="loyalty" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
	<!-- 0-based grid so the halving reads at half height -->
	{#each gridVals as g (g)}
		<line class="grid" x1={padL} x2={W - padR} y1={yOf(g)} y2={yOf(g)} />
		<text class="ylab" x={padL - 10} y={yOf(g) + 4} text-anchor="end">{pct0(g)} in 100</text>
	{/each}
	<text class="axis-title" x={24} y={H / 2} text-anchor="middle" transform="rotate(-90 24 {H / 2})">
		one-club players
	</text>

	<polygon class="area" points={areaPts} />
	<polyline class="line" points={linePts} />

	{#if showPeak}
		<circle class="mk peak" cx={xOf(peakI)} cy={yOf(peak.pct)} r="6" />
		<text class="mklab" x={xOf(peakI)} y={yOf(peak.pct) - 14} text-anchor="middle">
			about {pct0(peak.pct)} in 100
		</text>
	{/if}
	{#if showTrough}
		<circle class="mk trough" cx={xOf(troughI)} cy={yOf(trough.pct)} r="6" />
		<text class="mklab" x={xOf(troughI)} y={yOf(trough.pct) + 26} text-anchor="middle">
			about {pct0(trough.pct)} in 100
		</text>
	{/if}

	{#each xTicks as t (t.season)}
		<text class="xlab" x={t.x} y={H - padB + 22} text-anchor="middle">{t.season}</text>
	{/each}
</svg>

<style>
	.loyalty {
		width: 100%;
		height: 100%;
		display: block;
	}

	.grid {
		stroke: rgba(151, 161, 184, 0.16);
		stroke-width: 1;
	}

	.ylab,
	.xlab {
		fill: var(--ink-dim);
		font-size: 20px;
		font-variant-numeric: tabular-nums;
	}

	.axis-title {
		fill: var(--ink-dim);
		font-size: 19px;
	}

	.area {
		fill: rgba(46, 196, 182, 0.1);
		stroke: none;
	}

	.line {
		fill: none;
		stroke: var(--teal);
		stroke-width: 3.4;
		stroke-linejoin: round;
		stroke-linecap: round;
		filter: drop-shadow(0 0 4px rgba(46, 196, 182, 0.35));
	}

	.mk {
		stroke: #0b0e14;
		stroke-width: 1.5;
	}

	.mk.peak {
		fill: #f2e9d0;
	}

	.mk.trough {
		fill: var(--gold);
	}

	.mklab {
		fill: var(--ink);
		font-size: 19px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}
</style>
