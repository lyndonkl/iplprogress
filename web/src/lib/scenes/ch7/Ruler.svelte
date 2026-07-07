<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import RiverPlane from './RiverPlane.svelte';
	import { pickCaptionCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';

	/**
	 * C7-4 — THE HERO, second half: the ruler and the honest bounds. The twin rivers
	 * hold at true heights with the gap read pinned; three one-point beats:
	 *   1. the ruler gloss — the women's river is the yardstick, glossing "the
	 *      control group" in fan language in the same breath (glossary rule);
	 *   2. the WPL-framing reframe, IN THIS BEAT (audit should-fix #6 / the house
	 *      rule): not the slow league, the ruler, and its steady rule-free path is
	 *      what lets us measure the men's jump at all;
	 *   3. the confound named in main flow (audit should-fix #7 / evidence-weight
	 *      gate): the pitches got flatter and the balls changed those same years too,
	 *      so the strongest suspect, not a confession.
	 * Zero numbers (argument beats commit, they do not count). No field morph — the
	 * rivers are held; the sparks (fed in C7-3) lerp back to 0 as this scene declares
	 * none.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.38 ? 1 : progress < 0.72 ? 2 : 3);
	const BOUNDS = [0, 0.38, 0.72, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => tick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	const capStyle = $derived.by(() => {
		void tick;
		void progress;
		if (isNarrowViewport() || !field) return '';
		return cornerStyle(pickCaptionCorner(field).corner);
	});
</script>

<div class="pin" class:active>
	<RiverPlane
		{field}
		{reduced}
		{progress}
		on={true}
		showGap={true}
		legend={true}
		footnoteId="ch7-rivers"
	/>

	<div class="caption-slot" class:gap={reveal < 0.5} style="{capStyle}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>
					Here is why the women's river matters so much. It had no twelfth-man rule, so it is our
					yardstick. It shows, roughly, what the men's game would have done if nothing had changed.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					So do not read it as the slow league. It is not lagging. Its steady, rule-free path is the
					whole reason we can measure the men's jump at all. No ruler, no measurement.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Now the honest part. The rule opened the door. But the pitches got flatter and the balls
					changed those same years too. So this is the strongest suspect, not a confession.
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

	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 8vh;
		max-width: min(25rem, 42vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.caption-slot {
			right: auto;
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
