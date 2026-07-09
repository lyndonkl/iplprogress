<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import RibbonField from './RibbonField.svelte';
	import FaultSubway from './FaultSubway.svelte';
	import { pickRibbonCorner, cornerStyle } from './captionCorner.svelte';
	import { loadCh10Data, type Ch10Data } from './data';

	/**
	 * C10-4, Supporting 1: the Fault Map. Lay the breaks side by side and the order
	 * jumps out. Each metric is a subway line, each break a station, and the sixes
	 * line has its station about five years before the scoring line does. 2023 is the
	 * big interchange where scoring, boundaries and dots all broke at once. The reveal
	 * is tied to the scroll STEP (not a tap): the two hero lines carry the distance
	 * beat, then the boundaries/dots lines and the ringed 2023 glyph reveal for the
	 * interchange beat. A description of the record's order, never a causal claim.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	let ch10 = $state<Ch10Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh10Data().then((d) => {
			if (alive) ch10 = d;
		});
		return () => {
			alive = false;
		};
	});

	const step = $derived(progress < 0.26 ? 1 : progress < 0.5 ? 2 : progress < 0.76 ? 3 : 4);
	const BOUNDS = [0, 0.26, 0.5, 0.76, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const corner = $derived(pickRibbonCorner(field, 'tr'));
	const revealLevel = $derived(reduced || step >= 3 ? 2 : 1);
	const gap = $derived(ch10?.fault_map.order_gap ?? null);
</script>

<div class="pin" class:active>
	<RibbonField {field} {progress} faint={true} footnoteId="ch10-seismo" />

	{#if ch10}
		<div class="panel">
			<FaultSubway d={ch10} {revealLevel} />
		</div>
	{/if}

	<div class="caption-slot" style="{cornerStyle(corner)}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>Leave the ribbon for a moment. Each line here is one thing about the game: sixes, scoring, wides, dot balls. A dot on a line is a year that thing broke.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Now read left to right. The sixes line breaks first, mid-2010s. The scoring line does not break
					until {gap?.scoring_year ?? 2023}. Sixes changed about {gap?.years ?? 5} years before the score did.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>And look at 2023. Scoring, boundaries and dot balls all break in the same year. One big interchange where three lines meet at once.</p>
			</div>
		{:else}
			<div class="scene-card interactive">
				<p>So the modern game is not one change. Sixes broke first, years early. Then in 2023 the rest broke together. A slow build, then a sudden convergence.</p>
				<button class="fn" onclick={() => footnotesOpen.set('ch10-seismo')}>ⓘ the fault map</button>
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

	.panel {
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		width: min(56vw, 44rem);
		height: min(52vh, 26rem);
		padding: 0.8rem 1rem;
		border-radius: 14px;
		background: rgba(10, 14, 24, 0.72);
		border: 1px solid rgba(151, 161, 184, 0.2);
	}

	.caption-slot {
		position: absolute;
		max-width: min(24rem, 38vw);
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
		.panel {
			width: 92vw;
			height: 46vh;
			top: 44%;
		}

		.caption-slot {
			left: 50% !important;
			right: auto !important;
			top: auto !important;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px)) !important;
		}
	}
</style>
