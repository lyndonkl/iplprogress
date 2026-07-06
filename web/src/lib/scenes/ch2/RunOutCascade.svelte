<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh2Data, fmt1, runoutSeasonPct, type Ch2Data } from './data';

	/**
	 * C2-4 — The run-out cascade (HERO #2; the subset-highlight). Over the held
	 * worm-space haze, each season's run-out cohort flashes RED and falls TOGETHER
	 * (Gestalt common fate — one discrete pulse per season) as the season pointer
	 * (`cascade.sweep`, driven from the scene def's dynamicState) sweeps 2008→2026:
	 * early seasons dump a flood, late seasons a trickle — the shrinking flood IS
	 * the extinction curve. Run-out membership (the `aRunOut` GL flag) is seeded
	 * by the field from `attrs.u8` bit 6 (the pipeline re-encode, CONTRACT §14.3 /
	 * §14.4) — ZERO new bytes, no runtime dataset fetch. This component owns only
	 * the 2D run-out extinction curve the red cross-fades into. Register: step 3
	 * pairs the loss with the gain INSIDE the beat (elegy rule).
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.32) return 1;
		if (progress < 0.66) return 2;
		return 3;
	});

	// mobile "read, then watch" (CONTRACT §17): caption fades in for the read beat,
	// then to a clear gap so the season-swept run-out cascade is unobstructed.
	// Desktop + reduced motion → 1 (persistent caption, byte-identical).
	const BOUNDS = [0, 0.32, 0.66, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch2 = $state<Ch2Data | null>(null);
	let narrow = $state(false);
	onMount(() => {
		let alive = true;
		loadCh2Data().then((d) => {
			if (alive) ch2 = d;
		});
		const mql = window.matchMedia('(max-width: 640px)');
		const sync = (): void => {
			narrow = mql.matches;
		};
		sync();
		mql.addEventListener('change', sync);
		return () => {
			alive = false;
			mql.removeEventListener('change', sync);
		};
	});

	/* Run-out membership needs no setup here: the field seeds the per-point
	   `aRunOut` flag from attrs.u8 bit 6 at load (CONTRACT §14.4), so the cascade
	   flashes the run-out cohort with zero new bytes and no dataset fetch. The 2D
	   extinction curve below carries the finding even if the field never flashes. */

	/* ---- the run-out extinction curve (2D, zero-based; 2008 ghost ref) ------- */
	const seasons = $derived(ch2 ? ch2.runout.seasons.ipl : []);
	const share2008 = $derived(ch2 ? runoutSeasonPct(ch2, 2008) : null);
	const share2026 = $derived(ch2 ? runoutSeasonPct(ch2, 2026) : null);

	const W = $derived(narrow ? 430 : 640);
	const H = $derived(narrow ? 300 : 280);
	const ML = $derived(narrow ? 40 : 44);
	const MR = 18;
	const MT = 16;
	const MB = $derived(narrow ? 48 : 36);
	const FONT = $derived(narrow ? 17 : 11);
	const plotW = $derived(W - ML - MR);
	const plotH = $derived(H - MT - MB);
	const Y_MAX = 14; // zero-based, fixed; data max ≈ 12.9

	const minYear = $derived(seasons.length ? seasons[0].season : 2008);
	const maxYear = $derived(seasons.length ? seasons[seasons.length - 1].season : 2026);
	const xAt = (year: number): number => ML + ((year - minYear) / Math.max(1, maxYear - minYear)) * plotW;
	const yAt = (pct: number): number => MT + (1 - Math.min(pct, Y_MAX) / Y_MAX) * plotH;
	const vc = $derived(FONT * 0.34);
	const tickLabY = $derived(narrow ? 26 : 18);

	const curve = $derived(seasons.map((s) => `${xAt(s.season).toFixed(1)},${yAt(s.runout_share_pct).toFixed(1)}`).join(' '));
	const drawn = $derived(reduced || step >= 2);
	const yearTicks = [2008, 2014, 2020, 2026];
</script>

<div class="pin" class:reduced class:active>
	{#if ch2 && seasons.length}
		<div class="chart-slot">
			<figure class="chart" aria-label="Run-outs as a share of all wickets, by season, {minYear} to {maxYear}, on a zero-based scale. {share2008 !== null ? fmt1(share2008) : ''}% in 2008 falling to {share2026 !== null ? fmt1(share2026) : ''}% now">
				<figcaption class="chart-title">Run-outs, share of all wickets</figcaption>
				<svg viewBox="0 0 {W} {H}" style="font-size:{FONT}px" role="img" aria-hidden="true">
					{#each [0, 4, 8, 12] as g (g)}
						<line x1={ML} x2={ML + plotW} y1={yAt(g)} y2={yAt(g)} class="grid" class:major={g === 0} />
						<text x={ML - 6} y={yAt(g) + vc} class="ylab">{g}%</text>
					{/each}
					{#each yearTicks as yr (yr)}
						<line x1={xAt(yr)} x2={xAt(yr)} y1={yAt(0)} y2={yAt(0) + 5} class="tickmark" />
						<text x={xAt(yr)} y={yAt(0) + tickLabY} class="xlab">{yr}</text>
					{/each}
					<!-- 2008 ghost reference marker (era-ghost convention from Ch 1) -->
					{#if share2008 !== null}
						<circle cx={xAt(2008)} cy={yAt(share2008)} r="3.5" class="ghost-dot" />
					{/if}
					<polyline points={curve} class="curve" class:drawn pathLength="1" />
				</svg>
			</figure>
		</div>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					The anchor lived on quick singles, and quick singles mean risk between the wickets.
					<strong>Back in 2008, one wicket in eight was a run-out</strong>
					{#if share2008 !== null}({fmt1(share2008)}%){/if}. The sharp single, the desperate second.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Watch them drain away.
					<strong>
						{share2008 !== null ? fmt1(share2008) : '-'}% of all wickets then,
						{share2026 !== null ? fmt1(share2026) : '-'}% now.
					</strong>
					Batters stopped scampering singles and started swinging for four. The riskiest run in
					the game is quietly vanishing.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					The clearest fossil in the data is <strong>the death of the risky single</strong>. The game
					got <strong>quicker without getting reckless</strong>.
					<button class="dagger" onclick={() => footnotesOpen.set('runout-extinction')} aria-label="How we counted run-outs">ⓘ</button>
					The anchor's whole game, and his whole way of getting out, went together.
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
		top: 7vh;
		left: 50%;
		transform: translateX(-50%);
		width: min(660px, 94vw);
	}

	.chart {
		margin: 0;
		padding: 0.5rem 0.6rem 0.2rem;
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 12px;
		background: rgba(11, 14, 20, 0.74);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
	}

	.chart-title {
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		color: var(--ink);
		padding: 0.1rem 0.3rem 0.35rem;
	}

	svg {
		display: block;
		width: 100%;
		height: auto;
	}

	.grid {
		stroke: rgba(232, 236, 245, 0.07);
		stroke-width: 1;
	}

	.grid.major {
		stroke: rgba(232, 236, 245, 0.16);
	}

	.tickmark {
		stroke: rgba(232, 236, 245, 0.3);
		stroke-width: 1;
	}

	.ylab,
	.xlab {
		fill: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.ylab {
		text-anchor: end;
	}

	.xlab {
		text-anchor: middle;
	}

	.ghost-dot {
		fill: #7a8298;
	}

	/* the curve is the falling-red cascade's 2D handoff — drawn in the cascade
	   red (#ff251d) so the flash and the line read as one signal */
	.curve {
		fill: none;
		stroke: #ff251d;
		stroke-width: 2.8;
		stroke-linejoin: round;
		stroke-linecap: round;
		stroke-dasharray: 1;
		stroke-dashoffset: 1;
		transition: stroke-dashoffset 1400ms ease;
	}

	.curve.drawn {
		stroke-dashoffset: 0;
	}

	.pin.reduced .curve {
		transition: none;
	}

	@media (prefers-reduced-motion: reduce) {
		.curve {
			transition: none;
		}
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 10vh;
		max-width: min(30rem, 84vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
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
			top: 5vh;
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
