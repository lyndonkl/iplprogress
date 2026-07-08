<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import DuelField from './DuelField.svelte';
	import DuelStrands from './DuelStrands.svelte';
	import { isNarrowViewport } from './captionCorner.svelte';
	import { loadCh9Data, heroDuel, type Ch9Data } from './data';

	/**
	 * C9-5, the SYNTHESIS (the chapter thesis image). Scrub through the seasons and
	 * across the five flatlines: the web draws itself in year by year, and as each
	 * mega-auction reset sweeps through, the lit strands FLASH and visibly continue
	 * (survival drawn as an EVENT, not inferred from a non-break). The web positions
	 * are fixed throughout, so the scrub is a visibility-and-luminance change, never a
	 * re-sort. Institutions churn; the human fabric holds. A contrast held in one
	 * picture, never a cause.
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

	const step = $derived(progress < 0.24 ? 1 : progress < 0.52 ? 2 : progress < 0.8 ? 3 : 4);
	const BOUNDS = [0, 0.24, 0.52, 0.8, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	const MIN_SEASON = 2008;
	const MAX_SEASON = 2026;
	const megaYears = $derived(ch9?.heartbeat.ipl.mega_years ?? []);

	/* the scrub advances 2008 -> 2026, complete by ~0.82 so step 4 can name it */
	const scanPos = $derived(reduced ? 1 : Math.min(1, progress / 0.82));
	const currentSeason = $derived(
		Math.round(MIN_SEASON + scanPos * (MAX_SEASON - MIN_SEASON))
	);
	const litUpToSeason = $derived(reduced ? MAX_SEASON : currentSeason);

	/* a sharp reset flash as the scan crosses each mega-auction year */
	const flash = $derived.by(() => {
		if (reduced) return 0;
		let f = 0;
		for (const m of megaYears) {
			const posM = (m - MIN_SEASON) / (MAX_SEASON - MIN_SEASON);
			f = Math.max(f, Math.max(0, 1 - Math.abs(scanPos - posM) / 0.035));
		}
		return f;
	});
	const flashingYear = $derived.by(() => {
		if (reduced || flash < 0.25) return null;
		let best: number | null = null;
		let bestD = 1;
		for (const m of megaYears) {
			const posM = (m - MIN_SEASON) / (MAX_SEASON - MIN_SEASON);
			const d = Math.abs(scanPos - posM);
			if (d < bestD) {
				bestD = d;
				best = m;
			}
		}
		return best;
	});

	const hero = $derived(ch9 ? heroDuel(ch9) : null);
	const heroId = $derived(hero ? hero.id : null);
</script>

<div class="pin" class:active>
	<DuelField {field} legend={true} faint={true} footnoteId="ch9-heartbeat" />
	<DuelStrands
		{field}
		{reduced}
		{progress}
		{active}
		topN={isNarrowViewport() ? 50 : 90}
		{heroId}
		{litUpToSeason}
		{flash}
		showHubLabels={true}
		hubLabelCount={isNarrowViewport() ? 3 : 5}
	/>

	<!-- the season scale: the five reset years marked, a scan marker sweeping across -->
	<div class="scale" aria-hidden="true">
		<div class="track">
			<div class="scan" style="left:{(scanPos * 100).toFixed(1)}%;"></div>
			{#each megaYears as m (m)}
				{@const pos = ((m - MIN_SEASON) / (MAX_SEASON - MIN_SEASON)) * 100}
				<div class="reset" class:hot={flashingYear === m} style="left:{pos.toFixed(1)}%;">
					<span class="tick"></span><span class="year">{m}</span>
				</div>
			{/each}
		</div>
		<div class="ends"><span>{MIN_SEASON}</span><span class="now">{reduced ? MAX_SEASON : currentSeason}</span><span>{MAX_SEASON}</span></div>
	</div>

	{#if flashingYear != null}
		<div class="reset-banner" aria-hidden="true">
			<strong>{flashingYear}.</strong> Whole squads torn up. The rivalries hold.
		</div>
	{/if}

	<div class="caption-slot" style="--reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>Back to the web. Now run through the seasons. Watch the rivalries draw themselves in, year by year.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>Here come the mega-auctions, the five flatlines from a moment ago. Whole squads torn up, one reset after another.</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>And the web does not break. Kohli still meets Jadeja. The rivalries re-draw straight through every reset.</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>That is the whole chapter. Institutions churn. The human fabric holds.</p>
				{#if reduced}
					<p class="note">The rivalries cross every reset unbroken.</p>
				{/if}
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

	.scale {
		position: absolute;
		left: 8vw;
		right: 8vw;
		bottom: 4vh;
		pointer-events: none;
	}

	.track {
		position: relative;
		height: 2px;
		background: rgba(151, 161, 184, 0.3);
		margin-bottom: 1.2rem;
	}

	.scan {
		position: absolute;
		top: -7px;
		width: 2px;
		height: 16px;
		background: var(--ink);
		box-shadow: 0 0 6px rgba(232, 236, 245, 0.7);
		transform: translateX(-1px);
	}

	.reset {
		position: absolute;
		top: -4px;
		transform: translateX(-50%);
		text-align: center;
	}

	.reset .tick {
		display: block;
		width: 2px;
		height: 10px;
		margin: 0 auto;
		background: rgba(255, 93, 58, 0.6);
	}

	.reset .year {
		font-size: 0.62rem;
		font-weight: 700;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.reset.hot .tick {
		background: var(--ember);
		height: 14px;
	}

	.reset.hot .year {
		color: var(--ember);
	}

	.ends {
		display: flex;
		justify-content: space-between;
		font-size: 0.64rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.ends .now {
		color: var(--ink);
		font-weight: 700;
	}

	.reset-banner {
		position: absolute;
		top: 12vh;
		left: 50%;
		transform: translateX(-50%);
		padding: 0.4rem 0.9rem;
		border-radius: 10px;
		background: rgba(255, 93, 58, 0.14);
		border: 1px solid rgba(255, 93, 58, 0.4);
		font-size: 0.82rem;
		color: var(--ink);
		white-space: nowrap;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 16vh;
		max-width: min(26rem, 42vw);
		opacity: var(--reveal, 1);
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			right: auto;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(14vh, calc(env(safe-area-inset-bottom) + 88px));
		}

		.reset-banner {
			font-size: 0.72rem;
			white-space: normal;
			max-width: 80vw;
			text-align: center;
		}
	}
</style>
