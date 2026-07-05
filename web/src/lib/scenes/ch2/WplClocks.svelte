<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { loadCh2Data, fmt1, type Ch2Data } from './data';

	/**
	 * C2-7 — The WPL beat (two clocks, one beat — house rule). In worm-space, WPL
	 * points brighten to full and IPL dims one stop (the brighten IS the beat, a
	 * colour-state change — no re-sort). Two zero-based gauges side by side, each
	 * with the IPL era-scale printed so the reader reads WHERE on the IPL's own
	 * history each WPL number sits: a BATTING clock (slow-innings share, already
	 * at modern-IPL levels — born past the anchor) and a RUNNING clock (run-out
	 * share, still mid-revolution). One league, two clocks at once. Never
	 * "behind" — "already modern" / "born past the anchor" is the subject.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	const shown = $derived(reduced || progress >= 0.4);

	let ch2 = $state<Ch2Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh2Data().then((d) => {
			if (alive) ch2 = d;
		});
		return () => {
			alive = false;
		};
	});

	const b = $derived(ch2 ? ch2.wpl_beat : null);

	/* ---- semicircular gauge geometry ---------------------------------------- */
	const CX = 110;
	const CY = 104;
	const R = 88;
	function polar(value: number, max: number): { x: number; y: number } {
		const t = Math.min(1, Math.max(0, value / max));
		const theta = Math.PI * (1 - t); // value 0 → 180° (left), max → 0° (right)
		return { x: CX + R * Math.cos(theta), y: CY - R * Math.sin(theta) };
	}
	function arcPath(fromV: number, toV: number, max: number): string {
		const a = polar(fromV, max);
		const c = polar(toV, max);
		const large = 0;
		const sweep = 1; // clockwise from left toward right
		return `M ${a.x.toFixed(1)} ${a.y.toFixed(1)} A ${R} ${R} 0 ${large} ${sweep} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`;
	}

	interface Gauge {
		id: string;
		title: string;
		sub: string;
		max: number;
		wpl: number;
		iplStart: number;
		iplModern: number;
		iplStartYear: number;
		iplModernYear: number;
	}

	// the batting clock's IPL-start is the 2008-2010 anchor band (14.8%) — the same
	// era-band figure the C2-3 hero cites; sourced from the artifact, never hardcoded.
	const battingIplStart = $derived(ch2 ? ch2.anchor.bands['ipl 2008-2010'].anchor_ball_share_pct : 14.8);

	const gauges = $derived<Gauge[]>(
		b
			? [
					{
						id: 'batting',
						title: 'Batting clock',
						sub: 'already modern',
						max: 16,
						wpl: b.anchor_ball_share_pct,
						iplStart: battingIplStart,
						iplModern: b.ipl_modern_anchor_ball_share_pct,
						iplStartYear: 2008,
						iplModernYear: 2026
					},
					{
						id: 'running',
						title: 'Running clock',
						sub: 'mid-revolution',
						max: 14,
						wpl: b.runout_share_pct,
						iplStart: b.ipl_start_runout_share_pct,
						iplModern: b.ipl_modern_runout_share_pct,
						iplStartYear: 2008,
						iplModernYear: 2026
					}
				]
			: []
	);
</script>

<div class="pin" class:active>
	{#if b && gauges.length}
		<div class="panel-slot" class:shown>
			<div class="panel">
				<p class="panel-title">One league, two clocks</p>
				<div class="dials">
					{#each gauges as g (g.id)}
						{@const start = g.iplStart}
						{@const needle = polar(g.wpl, g.max)}
						{@const sTick = polar(start, g.max)}
						{@const mTick = polar(g.iplModern, g.max)}
						<figure class="dial">
							<figcaption>
								<span class="dial-title">{g.title}</span>
								<span class="dial-sub">{g.sub}</span>
							</figcaption>
							<svg viewBox="0 0 220 132" role="img" aria-label="{g.title}: the WPL at {fmt1(g.wpl)} percent, against the IPL's own decline from {fmt1(start)} percent in {g.iplStartYear} to {fmt1(g.iplModern)} percent in {g.iplModernYear}">
								<!-- the IPL's own span, drawn as the dial's era-scale track -->
								<path d={arcPath(0, g.max, g.max)} class="track" />
								<path d={arcPath(g.iplModern, start, g.max)} class="ipl-span" />
								<!-- IPL era markers (where the IPL's history sits on the same scale) -->
								<line x1={CX} y1={CY} x2={sTick.x} y2={sTick.y} class="ipl-tick" />
								<line x1={CX} y1={CY} x2={mTick.x} y2={mTick.y} class="ipl-tick" />
								<text x={mTick.x - 4} y={mTick.y - 6} class="ipl-yr" text-anchor="end">{g.iplModernYear}</text>
								<text x={sTick.x + 4} y={sTick.y - 6} class="ipl-yr" text-anchor="start">{g.iplStartYear}</text>
								<!-- the WPL needle (its hue — teal — names whose number it is) -->
								<line x1={CX} y1={CY} x2={needle.x} y2={needle.y} class="needle" />
								<circle cx={CX} cy={CY} r="5" class="hub" />
								<text x={CX} y={CY + 22} class="wpl-val">WPL {fmt1(g.wpl)}%</text>
							</svg>
							<!-- the IPL era-scale, printed beneath (no on-arc clipping) -->
							<p class="dial-scale">
								IPL: {g.iplStartYear} <b>{fmt1(start)}%</b> → {g.iplModernYear} <b>{fmt1(g.iplModern)}%</b>
							</p>
						</figure>
					{/each}
				</div>
			</div>
		</div>
	{/if}

	{#if b}
		<div class="caption-slot" class:shown>
			<div class="scene-card">
				<p>
					<strong>The WPL never had an anchor era to lose.</strong> Four seasons in, its
					slow-innings share already sits at the modern IPL's — born past the anchor. Yet its
					run-outs run at <strong class="wpl-ink">{fmt1(b.runout_share_pct)}%</strong> —
					mid-revolution, partway down the IPL's long fall.
					<strong>Two clocks: batting modern, running mid-clock.</strong>
					<button class="dagger" onclick={() => footnotesOpen.set('wpl-two-clocks-ch2')} aria-label="How the WPL numbers were counted">ⓘ</button>
				</p>
			</div>
		</div>
	{/if}
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

	.panel-slot {
		position: absolute;
		top: 6vh;
		left: 50%;
		transform: translateX(-50%);
		width: min(640px, 94vw);
		opacity: 0;
	}

	.panel-slot.shown {
		opacity: 1;
	}

	.panel {
		border: 1px solid rgba(46, 196, 182, 0.32);
		border-radius: 12px;
		background: rgba(13, 20, 24, 0.82);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
		padding: 0 0.7rem 0.7rem;
		overflow: hidden;
	}

	.panel-title {
		margin: 0 -0.7rem 0.5rem;
		padding: 0.5rem 1rem;
		background: rgba(46, 196, 182, 0.1);
		font-size: 0.84rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		color: var(--ink);
	}

	.dials {
		display: flex;
		gap: 0.6rem;
	}

	.dial {
		margin: 0;
		flex: 1;
		min-width: 0;
	}

	.dial figcaption {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.1rem;
		margin-bottom: 0.2rem;
	}

	.dial-title {
		font-size: 0.82rem;
		font-weight: 700;
		color: var(--ink);
	}

	.dial-sub {
		font-size: 0.72rem;
		letter-spacing: 0.04em;
		color: var(--teal);
	}

	.dial svg {
		display: block;
		width: 100%;
		height: auto;
	}

	.track {
		fill: none;
		stroke: rgba(232, 236, 245, 0.12);
		stroke-width: 8;
		stroke-linecap: round;
	}

	.ipl-span {
		fill: none;
		stroke: #7a8298;
		stroke-width: 8;
		stroke-linecap: round;
	}

	.ipl-tick {
		stroke: rgba(232, 236, 245, 0.35);
		stroke-width: 1.2;
		stroke-dasharray: 2 3;
	}

	.ipl-yr {
		fill: var(--ink-dim);
		font-size: 9.5px;
		font-variant-numeric: tabular-nums;
	}

	.dial-scale {
		margin: 0.1rem 0 0;
		text-align: center;
		font-size: 0.72rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.dial-scale b {
		color: #b9c2d6;
		font-weight: 700;
	}

	.needle {
		stroke: var(--teal);
		stroke-width: 3;
		stroke-linecap: round;
	}

	.hub {
		fill: var(--teal);
	}

	.wpl-val {
		fill: var(--teal);
		font-size: 12px;
		font-weight: 700;
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 8vh;
		max-width: min(36rem, 84vw);
		opacity: 0;
	}

	.caption-slot.shown {
		opacity: 1;
	}

	.wpl-ink {
		color: var(--teal);
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
		.panel-slot {
			top: 4vh;
		}

		.ipl-yr {
			font-size: 8.5px;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(72px, calc(env(safe-area-inset-bottom) + 60px));
		}
	}
</style>
