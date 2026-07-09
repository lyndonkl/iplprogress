<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import RibbonField from './RibbonField.svelte';
	import { pickRibbonCorner, cornerStyle } from './captionCorner.svelte';
	import { loadCh10Data, int, type Ch10Data } from './data';

	/**
	 * C10-2, THE controlling morph (free field -> the chronological ribbon) and
	 * orient. The 316,199 balls sort into one horizontal band ordered left to right
	 * by when they were bowled, so from here x is time and the whole history is one
	 * ribbon. Teaches the ONE mark the chapter rests on before any argument. Owns
	 * the ball-spacing honesty in the legend: recent seasons are wider only because
	 * there are more matches now, brightness held uniform, never a false trend.
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

	const step = $derived(progress < 0.3 ? 1 : progress < 0.55 ? 2 : progress < 0.8 ? 3 : 4);
	const BOUNDS = [0, 0.3, 0.55, 0.8, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const corner = $derived(pickRibbonCorner(field, 'tl'));
	const total = $derived(ch10 ? int(ch10.ribbon.total_points) : '316,199');
</script>

<div class="pin" class:active>
	<RibbonField {field} {progress} legend={true} timeAxis={true} footnoteId="ch10-seismo" />

	<div class="caption-slot" style="{cornerStyle(corner)}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>Every ball ever bowled. All {total} of them, back in the sky.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Now watch them line up. A dot is still one ball. Left to right is time: the very first ball
					of 2008 on the left, the last ball of 2026 on the right.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>That is the whole story you have been reading, in one ribbon. Nineteen seasons, in the order they happened.</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>Now we ask the machine one question. Somewhere in here, the game changed. Where?</p>
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

	.caption-slot {
		position: absolute;
		max-width: min(26rem, 42vw);
		opacity: var(--reveal, 1);
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50% !important;
			right: auto !important;
			top: auto !important;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(6vh, calc(env(safe-area-inset-bottom) + 16px)) !important;
		}
	}
</style>
