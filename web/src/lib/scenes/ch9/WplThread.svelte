<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import DuelField from './DuelField.svelte';
	import DuelStrands from './DuelStrands.svelte';
	import HeartbeatChart from './HeartbeatChart.svelte';
	import { isNarrowViewport } from './captionCorner.svelte';
	import { loadCh9Data, inHundred, int, type Ch9Data } from './data';

	/**
	 * C9-7, the WPL thread (a young league whose fabric is forming fast). The held web
	 * dims; the WPL sub-web (33 players, off to one side, sharing no players with the
	 * men's web) foregrounds in teal, and its own auction pulse draws as a small EKG.
	 * At three seasons old its rivalries are taking shape as fast as the men's game
	 * did at the same age, and it has its first big reset in 2026. NEVER "behind":
	 * a young league building its fabric fast (the house framing rule made literal).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	let ch9 = $state<Ch9Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh9Data().then((d) => {
			if (alive) ch9 = d;
		});
		return () => {
			alive = false;
		};
	});

	const step = $derived(progress < 0.24 ? 1 : progress < 0.5 ? 2 : progress < 0.78 ? 3 : 4);
	const BOUNDS = [0, 0.24, 0.5, 0.78, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	const w = $derived(ch9?.wpl ?? null);
	const wbeat = $derived(ch9?.heartbeat.wpl ?? null);
	const am = $derived(w?.age_matched ?? null);
	const showBeat = $derived(reduced || step >= 3);
</script>

<div class="pin" class:active>
	<DuelField {field} legend={true} faint={true} footnoteId="ch9-duel" />
	<DuelStrands
		{field}
		{reduced}
		{progress}
		{active}
		topN={isNarrowViewport() ? 42 : 60}
		wplForeground={true}
		showHubLabels={true}
		hubLabelCount={isNarrowViewport() ? 3 : 4}
	/>

	{#if wbeat && showBeat}
		<div class="beat">
			<span class="beat-h">its own pulse</span>
			<div class="beat-chart">
				<HeartbeatChart
					series={wbeat.series}
					megaYears={[wbeat.first_reset.season]}
					reveal={1}
					{reduced}
					variant="wpl"
				/>
			</div>
		</div>
	{/if}

	<div class="caption-slot" style="--reveal: {reveal};">
		{#if w}
			{#if step === 1}
				<div class="scene-card">
					<p>
						The women's league has its own web, off to one side. Just a few seasons old, {int(w.n_players)}
						players, and already knotting together.
					</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>
						At {am?.at_seasons ?? 3} seasons old it has already knotted {am?.wpl_duels_by_season3 ?? 51}
						real rivalries, right alongside the {am?.ipl_duels_by_season3 ?? 62} the men's game had at
						the same age.
					</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						It has its own pulse too. A steady squad, then its first big reset in {wbeat?.first_reset
							.season ?? 2026}, with only about {inHundred(wbeat?.first_reset.mean ?? 0.257)} in 100 coming back.
					</p>
				</div>
			{:else}
				<div class="scene-card interactive">
					<p>A young league whose fabric is forming fast. You can already see the rivalries that will run for a decade.</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch9-duel')}>ⓘ how the young league is read</button>
				</div>
			{/if}
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

	.beat {
		position: absolute;
		right: 3vw;
		bottom: 4vh;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		padding: 0.55rem 0.7rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.82);
		border: 1px solid rgba(46, 196, 182, 0.3);
		width: min(26vw, 22rem);
	}

	.beat-h {
		font-size: 0.6rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--teal);
	}

	.beat-chart {
		height: 9rem;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 8vh;
		max-width: min(25rem, 42vw);
		opacity: var(--reveal, 1);
	}

	.fn {
		margin-top: 0.5rem;
		min-height: 40px;
		padding: 0.2rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.78rem;
		font-weight: 600;
		text-align: left;
		cursor: pointer;
	}

	.fn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.beat {
			right: auto;
			left: 50%;
			transform: translateX(-50%);
			bottom: auto;
			top: 16vh;
			width: 84vw;
		}

		.beat-chart {
			height: 7rem;
		}

		.caption-slot {
			left: 50%;
			right: auto;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
