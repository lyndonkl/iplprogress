<script lang="ts">
	import { inHundred, type HeartSeason } from './data';

	/**
	 * The auction heartbeat EKG (C9-4 / C9-7, CONTRACT §26.4). A 2D telemetry panel,
	 * NOT a field morph (particles carry no meaning in an EKG). ONE bold league-mean
	 * line ("how much of the squad came back") on a labelled 0-to-1 axis, with a
	 * faint min-max envelope behind it carrying the "every team at once"
	 * synchronization, never ten traceable lines. The line rests high and crashes to
	 * a flatline in each mega-auction year. The load-bearing "steady, then it
	 * crashes" read is a POSITION-on-axis read, backed by the axis label, never a
	 * color read. The line draws in left-to-right with `reveal` (the flatlines drop
	 * in the mobile clear gap); reduced motion draws it complete.
	 */
	interface Props {
		series: HeartSeason[];
		/** the mega-auction seasons (the flatlines); empty for the WPL's single reset */
		megaYears?: number[];
		/** a faint resting reference (the non-mega mean); omit to hide */
		resting?: number | null;
		/** 0..1 progressive draw; 1 (or reduced) = complete */
		reveal?: number;
		reduced?: boolean;
		yDomain?: [number, number];
		/** styling: 'ipl' the men's pulse, 'wpl' the young league's teal pulse */
		variant?: 'ipl' | 'wpl';
	}
	let {
		series,
		megaYears = [],
		resting = null,
		reveal = 1,
		reduced = false,
		yDomain = [0, 1],
		variant = 'ipl'
	}: Props = $props();

	const W = 1000;
	const H = 460;
	const padL = 78;
	const padR = 40;
	const padT = 28;
	const padB = 46;

	const megaSet = $derived(new Set(megaYears));

	const xOf = (i: number): number =>
		series.length <= 1 ? padL : padL + (i / (series.length - 1)) * (W - padL - padR);
	const yOf = (v: number): number => {
		const [lo, hi] = yDomain;
		const t = (v - lo) / (hi - lo);
		return H - padB - t * (H - padT - padB);
	};

	const drawn = $derived(
		reduced ? series.length : Math.max(2, Math.round((reveal || 0) * series.length))
	);

	const meanPts = $derived(
		series
			.slice(0, drawn)
			.map((s, i) => `${xOf(i).toFixed(1)},${yOf(s.mean).toFixed(1)}`)
			.join(' ')
	);

	const envPts = $derived.by(() => {
		const top = series.slice(0, drawn).map((s, i) => `${xOf(i).toFixed(1)},${yOf(s.hi).toFixed(1)}`);
		const bot = series
			.slice(0, drawn)
			.map((s, i) => `${xOf(i).toFixed(1)},${yOf(s.lo).toFixed(1)}`)
			.reverse();
		return [...top, ...bot].join(' ');
	});

	/* a handful of season ticks along the x-axis */
	const xTicks = $derived.by(() => {
		if (series.length <= 6) return series.map((s, i) => ({ season: s.season, x: xOf(i) }));
		const step = Math.ceil(series.length / 6);
		const out: { season: number; x: number }[] = [];
		for (let i = 0; i < series.length; i += step) out.push({ season: series[i].season, x: xOf(i) });
		const last = series.length - 1;
		if (out[out.length - 1]?.season !== series[last].season)
			out.push({ season: series[last].season, x: xOf(last) });
		return out;
	});

	const flats = $derived(
		series
			.map((s, i) => ({ ...s, i }))
			.filter((s) => megaSet.has(s.season) && s.i < drawn)
	);

	const stroke = $derived(variant === 'wpl' ? 'var(--teal)' : '#f2e9d0');
</script>

<svg class="ekg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
	<!-- y grid + labels: none / half / all -->
	{#each [0, 0.5, 1] as g (g)}
		{@const yy = yOf(yDomain[0] + (yDomain[1] - yDomain[0]) * g)}
		<line class="grid" x1={padL} x2={W - padR} y1={yy} y2={yy} />
		<text class="ylab" x={padL - 10} y={yy + 4} text-anchor="end">
			{g === 0 ? 'none' : g === 0.5 ? 'half' : 'all'}
		</text>
	{/each}
	<text class="axis-title" x={22} y={H / 2} text-anchor="middle" transform="rotate(-90 22 {H / 2})">
		how much of the squad came back
	</text>

	<!-- the min-max envelope (the synchronization, faint) -->
	<polygon class="env" class:wpl={variant === 'wpl'} points={envPts} />

	<!-- the resting reference -->
	{#if resting != null}
		<line class="resting" x1={padL} x2={W - padR} y1={yOf(resting)} y2={yOf(resting)} />
		<text class="resting-lab" x={W - padR} y={yOf(resting) - 8} text-anchor="end">
			steady, about {inHundred(resting)} in 100
		</text>
	{/if}

	<!-- the one bold league-mean line -->
	<polyline class="mean" points={meanPts} style="stroke:{stroke};" />

	<!-- the flatline markers (a dropped guide + a dot + the season) -->
	{#each flats as f (f.season)}
		<line class="drop" x1={xOf(f.i)} x2={xOf(f.i)} y1={yOf(f.mean)} y2={H - padB} />
		<circle class="flatdot" cx={xOf(f.i)} cy={yOf(f.mean)} r="5" />
		<text class="flatlab" x={xOf(f.i)} y={yOf(f.mean) - 12} text-anchor="middle">{f.season}</text>
	{/each}

	<!-- x-axis season ticks -->
	{#each xTicks as t (t.season)}
		<text class="xlab" x={t.x} y={H - padB + 22} text-anchor="middle">{t.season}</text>
	{/each}
</svg>

<style>
	.ekg {
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

	.env {
		fill: rgba(242, 233, 208, 0.1);
		stroke: none;
	}

	.env.wpl {
		fill: rgba(46, 196, 182, 0.12);
	}

	.resting {
		stroke: rgba(151, 161, 184, 0.45);
		stroke-width: 1.4;
		stroke-dasharray: 3 7;
	}

	.resting-lab {
		fill: var(--ink-dim);
		font-size: 18px;
	}

	.mean {
		fill: none;
		stroke-width: 3.4;
		stroke-linejoin: round;
		stroke-linecap: round;
		filter: drop-shadow(0 0 4px rgba(242, 233, 208, 0.35));
	}

	.drop {
		stroke: rgba(255, 93, 58, 0.5);
		stroke-width: 1.4;
		stroke-dasharray: 2 5;
	}

	.flatdot {
		fill: var(--ember);
		stroke: #0b0e14;
		stroke-width: 1.5;
	}

	.flatlab {
		fill: var(--ink);
		font-size: 19px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}
</style>
