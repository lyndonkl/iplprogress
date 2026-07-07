<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh6Data, fmt1, type Ch6Data } from './data';

	/**
	 * C6-7 — SUPPORTING 2: the Stumping Signature (the Ch 3 tease, paid off). A
	 * stumping almost always means a spinner beat the bat, so the share of a
	 * season's wickets that are stumpings is a fingerprint for how spin-heavy a
	 * league is. Every WPL season runs 5.2-7.9%; the IPL in 2026 is 1.4%. The WPL
	 * is structurally a spinner's league — a genuinely different dismissal ecology,
	 * not a worse one. A 2D annotation-plane scene over the dimmed constellation.
	 * Every number from ch6.json stumping (artifact wins).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.4 ? 1 : progress < 0.72 ? 2 : 3);
	const BOUNDS = [0, 0.4, 0.72, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch6 = $state<Ch6Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh6Data().then((d) => {
			if (alive) ch6 = d;
		});
		return () => {
			alive = false;
		};
	});

	const st = $derived(ch6?.stumping ?? null);
	const ipl2026 = $derived(st?.headline.ipl_2026 ?? 1.4);
	const wplLo = $derived(st?.headline.wpl_range[0] ?? 5.2);
	const wplHi = $derived(st?.headline.wpl_range[1] ?? 7.9);

	/* ---- chart geometry ----------------------------------------------------- */
	const VB_W = 340;
	const VB_H = 200;
	const PX0 = 30;
	const PX1 = VB_W - 14;
	const PY0 = 14;
	const PY1 = VB_H - 24;
	const Y_MAX = 9;
	const S_MIN = 2008;
	const S_MAX = 2026;

	const xAt = (s: number): number => PX0 + ((s - S_MIN) / (S_MAX - S_MIN)) * (PX1 - PX0);
	const yAt = (pct: number): number => PY1 - (pct / Y_MAX) * (PY1 - PY0);

	const iplLine = $derived(
		st ? st.ipl.map((r) => `${xAt(r.season).toFixed(1)},${yAt(r.stumped_pct).toFixed(1)}`).join(' ') : ''
	);
	const wplDots = $derived(st ? st.wpl.map((r) => ({ x: xAt(r.season), y: yAt(r.stumped_pct), v: r.stumped_pct, s: r.season })) : []);
	const yTicks = [0, 3, 6, 9];
	/* the WPL band (5.2 → 7.9) as a shaded strip */
	const bandTop = $derived(yAt(wplHi));
	const bandBot = $derived(yAt(wplLo));
	const showChart = $derived(reduced || step >= 1);
</script>

<div class="pin" class:active>
	{#if st}
		<div class="panel">
			<p class="overline">stumping signature · spin's fingerprint</p>
			<svg class="chart" viewBox="0 0 {VB_W} {VB_H}" role="img"
				aria-label="Share of each season's wickets that were stumpings. Every WPL season runs 5 to 8%; the IPL in 2026 is 1.4%.">
				{#if showChart && step >= 2}
					<rect class="band" x={PX0} y={bandTop} width={PX1 - PX0} height={bandBot - bandTop} />
				{/if}
				{#each yTicks as t (t)}
					<line class="grid" x1={PX0} y1={yAt(t)} x2={PX1} y2={yAt(t)} />
					<text class="ax-y" x={PX0 - 5} y={yAt(t) + 3}>{t}%</text>
				{/each}
				<polyline class="ipl-line" points={iplLine} />
				{#each wplDots as d (d.s)}
					<circle class="wpl-dot" cx={d.x} cy={d.y} r="4.5" />
				{/each}
				<text class="ax-x" x={xAt(2008)} y={PY1 + 15}>2008</text>
				<text class="ax-x end" x={xAt(2026)} y={PY1 + 15}>2026</text>
			</svg>
			<div class="key">
				<span class="k-row"><span class="k-dot ipl"></span> IPL, season by season</span>
				<span class="k-row"><span class="k-dot wpl"></span> WPL</span>
			</div>
			<button
				class="dagger"
				onclick={() => footnotesOpen.set('ch6-stumping')}
				aria-label="How stumping share is counted">ⓘ how we count this</button
			>
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					Back to a promise from Chapter 3. A stumping, where the keeper whips off the bails the
					moment a batter is beaten, almost always means a spinner bowled it. So its share of a
					season's wickets tells you how spin-heavy a league is.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Every WPL season sits in that teal band, <strong>{fmt1(wplLo)} to {fmt1(wplHi)}%</strong>
					of its wickets. The IPL in 2026 managed {fmt1(ipl2026)}%.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					The WPL leans on spin the way the men's game no longer does. The men used to as well, back
					in the early years; now it is pace. A different way to take a wicket, a different game to
					bat in.
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
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	.pin.active {
		visibility: visible;
	}

	.panel {
		pointer-events: auto;
		width: min(36rem, 92vw);
		background: rgba(11, 14, 20, 0.72);
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 14px;
		padding: 1rem 1.2rem 1.1rem;
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
	}

	.overline {
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: var(--gold);
		margin: 0 0 0.55rem;
	}

	.chart {
		width: 100%;
		height: auto;
	}

	.band {
		fill: rgba(46, 196, 182, 0.16);
	}

	.grid {
		stroke: rgba(151, 161, 184, 0.16);
		stroke-width: 1;
		vector-effect: non-scaling-stroke;
	}

	.ax-y {
		fill: var(--ink-dim);
		font-size: 9px;
		text-anchor: end;
		font-variant-numeric: tabular-nums;
	}

	.ax-x {
		fill: var(--ink-dim);
		font-size: 9px;
		text-anchor: start;
	}

	.ax-x.end {
		text-anchor: end;
	}

	.ipl-line {
		fill: none;
		stroke: #e8a33d;
		stroke-width: 2.2;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.wpl-dot {
		fill: #2ec4b6;
		stroke: #0b0e14;
		stroke-width: 1.5;
	}

	.key {
		display: flex;
		gap: 1.2rem;
		margin-top: 0.5rem;
	}

	.k-row {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.k-dot {
		width: 0.7rem;
		height: 0.7rem;
		border-radius: 50%;
	}

	.k-dot.ipl {
		background: #e8a33d;
	}

	.k-dot.wpl {
		background: #2ec4b6;
	}

	.dagger {
		display: inline-block;
		margin-top: 0.5rem;
		min-height: 44px;
		padding: 0.3rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.78rem;
		cursor: pointer;
	}

	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 6vh;
		max-width: min(23rem, 34vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.pin {
			place-items: start center;
			padding-top: 8vh;
		}

		.panel {
			max-height: 68vh;
			overflow-y: auto;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(3vh, calc(env(safe-area-inset-bottom) + 10px));
		}
	}
</style>
