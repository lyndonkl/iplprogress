<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import RiverPlane from './RiverPlane.svelte';
	import { pickCaptionCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';

	/**
	 * C7-2 — THE CONTROLLING MORPH: the free field pours into TWO flowing rivers
	 * (free → `flow`, declared in index.ts). Every ball settles to its league-
	 * season cell: left→right is the seasons, up is runs an over. The men's IPL
	 * ribbon runs the full width; the women's WPL ribbon is a short teal band on
	 * the right, sourcing at 2023. This is pure ORIENT (voice rule): what the
	 * rivers are, what up/across mean, and that the band's thickness is decoration.
	 * The rivers land at TRUE heights here (flowLift 1) — the honest full picture.
	 * The divergence gets NAMED next (C7-3).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength 150 / scrollLength 340 → morph ends ≈ 0.44 */
	const step = $derived(progress < 0.44 ? 1 : progress < 0.72 ? 2 : 3);
	const BOUNDS = [0, 0.44, 0.72, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const landed = $derived(reduced || progress >= 0.46);

	/* §0.4a caption safe-corner from the live river geometry; re-picks on resize +
	   as the morph settles. Mobile uses the bottom read-then-watch slot. */
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
	<RiverPlane {field} {reduced} {progress} on={landed} legend={landed} footnoteId="ch7-rivers" />

	<div class="caption-slot" class:gap={reveal < 0.5} style="{capStyle}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>
					Every ball just flowed into its league and its season, and the field became two rivers. The
					gold one is the men's game, the IPL. The teal one is the women's, the WPL.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Left to right is the seasons, 2008 over to 2026. How high a river runs is how many runs an
					over teams were scoring. The thickness is just for looks. Only the height carries a number.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					The women's river is short because the WPL only started in 2023. So both rivers run
					together from 2023 on, marked here. Keep your eye on that line.
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
		max-width: min(24rem, 42vw);
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
