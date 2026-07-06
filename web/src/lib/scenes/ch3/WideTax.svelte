<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh3Data, fmt1, fmt2, type Ch3Data } from './data';
	import FrontierScaffold from './FrontierScaffold.svelte';

	/**
	 * C3-6 — The wide-yorker tax (supporting: Death-Wide Tax). A 2D leak gauge over
	 * the held (dimmed) frontier plane; loop provably stopped. A rising fluid level
	 * reads wides given away per 100 legal balls at the death (overs 16-20). It
	 * doubled (3.13 → 6.45). Register: this is not bowlers getting worse — the rise
	 * is multi-causal (deliberate risk + tighter wide-calling + batter movement).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.36) return 1;
		if (progress < 0.66) return 2;
		return 3;
	});
	/* mobile "read, then watch" (CONTRACT §17): ascending step bounds so the caption
	   fades to a clear gap (the leak gauge stays up to watch) before the next step.
	   1 on desktop / reduced. */
	const BOUNDS = [0, 0.36, 0.66, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const risen = $derived(reduced || step >= 2);

	let ch3 = $state<Ch3Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh3Data().then((d) => {
			if (alive) ch3 = d;
		});
		return () => {
			alive = false;
		};
	});

	const head = $derived(ch3 ? ch3.death_wide_tax.era_headline : null);
	const MAX = 8;
	const early = $derived(head ? head.ipl_2008_2010 : 0);
	const recent = $derived(head ? head.ipl_2023_2026 : 0);
	const level = $derived(risen ? recent : early);
	const fillPct = $derived(Math.min(100, (level / MAX) * 100));
	const earlyPct = $derived(Math.min(100, (early / MAX) * 100));
</script>

<div class="pin" class:active>
	<!-- faint persistent orientation anchors behind the leak gauge (held C3-3..C3-8) -->
	<FrontierScaffold {field} faint />

	{#if head}
		<div class="gauge-slot">
			<figure class="gauge">
				<div class="beaker" role="img" aria-label="Death-over wides per 100 balls: {fmt1(early)} in the early seasons, {fmt1(recent)} now">
					<div class="fill" style="height:{fillPct}%"></div>
					<!-- early-era reference mark -->
					<div class="mark early" style="bottom:{earlyPct}%">
						<span>early {fmt1(early)}</span>
					</div>
					{#if risen}
						<div class="mark now" style="bottom:{fillPct}%">
							<span>now {fmt1(recent)}</span>
						</div>
					{/if}
				</div>
				<figcaption>wides per 100 balls, last five overs</figcaption>
			</figure>
			{#if risen}
				<p class="double">× {fmt2(head.doubling_factor)}</p>
			{/if}
		</div>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					At the death, the last five overs, bowlers now aim for the edges: the yorker into the toes,
					the ball climbing past the shoulder. <strong>Miss by a hair and it is a wide, a free run to
						the batting side.</strong> This gauge fills with wides given away per 100 balls.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					<strong>It doubled.</strong> {fmt1(early)} wides per 100 balls at the death in the early
					seasons, {fmt1(recent)} now. Every extra wide is a run the bowler never meant to give.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					<strong>This is not bowlers getting worse.</strong> Three things drive it: they chase the
					un-hittable ball on purpose, batters shuffle across to make good balls look wide, and umpires
					call the wide line tighter than they once did. The arms race, made of runs.
					<button class="dagger" onclick={() => footnotesOpen.set('death-wides')} aria-label="How wides were counted">ⓘ</button>
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

	.gauge-slot {
		position: absolute;
		top: 12vh;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		align-items: flex-end;
		gap: 0.8rem;
	}

	.gauge {
		margin: 0;
		text-align: center;
	}

	.beaker {
		position: relative;
		width: 96px;
		height: 46vh;
		max-height: 320px;
		border: 2px solid rgba(232, 236, 245, 0.28);
		border-top: none;
		border-radius: 0 0 14px 14px;
		background: rgba(11, 14, 20, 0.5);
		overflow: hidden;
	}

	.fill {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		background: linear-gradient(to top, rgba(255, 93, 58, 0.85), rgba(255, 93, 58, 0.35));
		transition: height 900ms cubic-bezier(0.22, 1, 0.36, 1);
	}

	.mark {
		position: absolute;
		left: 0;
		right: 0;
		border-top: 1.5px dashed rgba(232, 236, 245, 0.5);
	}

	.mark.now {
		border-top-color: #ffd0c4;
	}

	.mark span {
		position: absolute;
		right: -6px;
		transform: translate(100%, -50%);
		font-size: 10px;
		white-space: nowrap;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.mark.now span {
		color: #ffd0c4;
		font-weight: 700;
	}

	.gauge figcaption {
		margin-top: 0.4rem;
		font-size: 0.7rem;
		color: var(--ink-dim);
		max-width: 96px;
	}

	.double {
		margin: 0 0 1.5rem;
		font-size: 2rem;
		font-weight: 800;
		color: var(--ember);
		font-variant-numeric: tabular-nums;
	}

	@media (prefers-reduced-motion: reduce) {
		.fill {
			transition: none;
		}
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 9vh;
		max-width: min(32rem, 84vw);
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
		.gauge-slot {
			top: 8vh;
		}

		.beaker {
			height: 38vh;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(72px, calc(env(safe-area-inset-bottom) + 56px));
		}
	}
</style>
