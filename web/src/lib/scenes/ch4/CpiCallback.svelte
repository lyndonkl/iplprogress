<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { sketch, footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh4Data, fmt1, int, TIDE_SEASONS, type Ch4Data } from './data';

	/**
	 * C4-7 — The T20 CPI callback (SUPPORTING). The reader's own cold-open sketch
	 * returns: they drew how often teams pass 200 each season, and now the truth draws
	 * over it. No-sketch variant (skipped / shared-link / returning session): the
	 * authored "here's what most readers drew" line stands in — the beat never depends
	 * on a sketch existing (storyboard). Then the same story as a run rate: the going
	 * rate for runs rose 8.03 → 9.55 an over, index 119. Over the dimmed skyline.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.34) return 1;
		if (progress < 0.66) return 2;
		return 3;
	});
	const BOUNDS = [0, 0.34, 0.66, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch4 = $state<Ch4Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh4Data().then((d) => {
			if (alive) ch4 = d;
		});
		return () => {
			alive = false;
		};
	});

	/* did the reader draw a real curve? (14 values for 2013..2026) */
	const usedSketch = $derived(
		$sketch != null && !$sketch.skipped && Array.isArray($sketch.values) && $sketch.values.length === 14
	);

	const truth = $derived.by(() => {
		const d = ch4;
		if (!d) return [];
		return TIDE_SEASONS.map((y) => d.cpi.callback_sketch.truth_200s_by_season[String(y)] ?? 0);
	});
	/* the reader line: their sketch spliced onto the pre-drawn 2008-2012 anchors
	   (which equal the truth for those years); or the authored "most readers" line. */
	const yours = $derived.by(() => {
		const d = ch4;
		if (!d) return [];
		if (usedSketch && $sketch?.values) {
			const anchors = TIDE_SEASONS.slice(0, 5).map(
				(y) => d.cpi.callback_sketch.truth_200s_by_season[String(y)] ?? 0
			);
			return [...anchors, ...$sketch.values];
		}
		return TIDE_SEASONS.map((y) => d.cpi.callback_sketch.authored_typical_200s_by_season[String(y)] ?? 0);
	});

	const rpoEarly = $derived(ch4 ? ch4.cpi.by_era['ipl 2008-2010'].first_innings_rpo : null);
	const rpoModern = $derived(ch4 ? ch4.cpi.by_era['ipl 2023-2026'].first_innings_rpo : null);
	const truth2026 = $derived(truth.length ? truth[truth.length - 1] : 65);

	/* ---- chart geometry ---- */
	const W = 360;
	const H = 170;
	const PAD = 22;
	const VMAX = 70;
	const n = TIDE_SEASONS.length;
	const xAt = (i: number): number => PAD + (i / (n - 1)) * (W - 2 * PAD);
	const yAt = (v: number): number => H - PAD - (Math.min(VMAX, v) / VMAX) * (H - 2 * PAD);
	const poly = (vals: number[]): string =>
		vals.map((v, i) => `${xAt(i).toFixed(1)},${yAt(v).toFixed(1)}`).join(' ');
</script>

<div class="pin" class:active>
	{#if truth.length}
		<figure class="chart-slot">
			<svg viewBox="0 0 {W} {H}" role="img" aria-label="Every 200-plus total, batting first or chasing, per season: {usedSketch ? 'your line' : 'a typical drawn line'} against the truth, which reaches {truth2026} in 2026">
				<!-- baseline -->
				<line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} class="axis" />
				<!-- the reader's / authored line -->
				{#if step >= 1}
					<polyline points={poly(yours)} class="yours" />
				{/if}
				<!-- the truth draws over it -->
				{#if reduced || step >= 2}
					<polyline points={poly(truth)} class="truth" />
					<circle cx={xAt(n - 1)} cy={yAt(truth2026)} r="4" class="truth-dot" />
					<text x={xAt(n - 1)} y={yAt(truth2026) - 8} class="truth-val" text-anchor="end">{truth2026}</text>
				{/if}
				<text x={PAD} y={H - 6} class="ax-lab" text-anchor="start">2008</text>
				<text x={W - PAD} y={H - 6} class="ax-lab" text-anchor="end">2026</text>
			</svg>
			<figcaption>every 200-plus total, batting first or chasing, per season</figcaption>
		</figure>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card chip">
				{#if usedSketch}
					<p>
						Right at the start, we asked you to draw how often teams pass 200 each season.
						<strong>Here is your line again.</strong> Hold that shape in your head.
					</p>
				{:else}
					<p>
						Right at the start, we asked readers to draw how often teams pass 200 each season.
						<strong>Here is roughly what most people drew:</strong> a gentle, steady climb.
					</p>
				{/if}
			</div>
		{:else if step === 2}
			<div class="scene-card chip">
				<p>
					Now here is the truth over the top. Flat for a decade and a half, then it takes off.
					<strong>65 times in 2026 alone.</strong> {usedSketch ? 'Almost nobody drew that.' : 'Almost nobody saw that coming.'}
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					Same story told in runs an over. The going rate for a first innings went from
					<strong>{rpoEarly !== null ? fmt1(rpoEarly) : '8.0'} an over to {rpoModern !== null ? fmt1(rpoModern) : '9.6'}.</strong>
					Every score you remember has quietly been repriced.
					<button class="dagger" onclick={() => footnotesOpen.set('cpi-callback')} aria-label="Your sketch, and the two ways to count 200">ⓘ</button>
				</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
	}

	.pin.active {
		visibility: visible;
	}

	.chart-slot {
		position: absolute;
		top: 14vh;
		left: 50%;
		transform: translateX(-50%);
		margin: 0;
		width: min(30rem, 88vw);
		text-align: center;
	}

	.chart-slot svg {
		display: block;
		width: 100%;
		height: auto;
		background: rgba(6, 9, 14, 0.4);
		border-radius: 10px;
	}

	.axis {
		stroke: rgba(232, 236, 245, 0.2);
		stroke-width: 1;
	}

	.yours {
		fill: none;
		stroke: var(--gold);
		stroke-width: 2;
		stroke-dasharray: 4 3;
		stroke-linejoin: round;
	}

	.truth {
		fill: none;
		stroke: #5b8cff;
		stroke-width: 2.6;
		stroke-linejoin: round;
		stroke-linecap: round;
		filter: drop-shadow(0 0 5px rgba(91, 140, 255, 0.4));
	}

	.truth-dot {
		fill: #5b8cff;
	}

	.truth-val {
		fill: #9dbcff;
		font-size: 12px;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
	}

	.ax-lab {
		fill: var(--ink-dim);
		font-size: 9px;
		font-variant-numeric: tabular-nums;
	}

	figcaption {
		margin-top: 0.4rem;
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.caption-slot {
		position: absolute;
		left: 6vw;
		bottom: 9vh;
		max-width: min(30rem, 46vw);
		opacity: var(--reveal, 1); /* mobile "read, then watch" (CONTRACT §17); 1 on desktop / reduced */
	}

	.dagger {
		pointer-events: auto;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 44px;
		min-height: 44px;
		margin: -10px 0;
		padding: 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 1rem;
		cursor: pointer;
	}

	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.chart-slot {
			top: 9vh;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(9vh, calc(env(safe-area-inset-bottom) + 56px));
		}
	}
</style>
