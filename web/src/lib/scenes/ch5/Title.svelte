<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C5-1 — Chapter title + the handoff from the nets. Zero numbers (titles are
	 * commitments, numbers are not). The free field idles dimmed behind the card,
	 * loop stopped; the reader's team stays lit. Pure text over a static field, so
	 * per CONTRACT §17.4 it does NOT adopt read-then-watch (nothing to watch).
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.4 ? 1 : progress < 0.72 ? 2 : 3);
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card title-card">
				<p class="overline">Chapter 5</p>
				<h2>What a Ball Is Worth</h2>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					In the nets you just moved two dials with your own hands. How many runs a team usually
					still gets from a spot, and how often teams win from it. Now watch one real over move
					both of them for keeps.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					This is the chapter where every ball gets a price tag. It starts in a final, with one
					over left and a title on the line.
				</p>
				<p class="note">keep scrolling</p>
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
		top: 14vh;
		max-width: min(26rem, 86vw);
	}

	.title-card h2 {
		font-size: clamp(1.6rem, 4.4vw, 2.4rem);
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(10vh, calc(env(safe-area-inset-bottom) + 64px));
		}
	}
</style>
