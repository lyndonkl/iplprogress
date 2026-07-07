<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C6-1 — Chapter title + the handoff from Chapter 5's close (which already
	 * named "Two Dialects"). Zero numbers (titles are commitments, numbers are
	 * not). The free field idles dimmed behind the card, loop stopped; the
	 * reader's team stays lit. Pure text over a static field, so per CONTRACT
	 * §17.4 it does NOT adopt read-then-watch (nothing to watch in a gap).
	 *
	 * HOUSE FRAMING (locked): the WPL is never "behind". This whole chapter turns
	 * "comparison" into "two dialects of one language" — beside the path, not on it.
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.4 ? 1 : progress < 0.72 ? 2 : 3);
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card title-card">
				<p class="overline">Chapter 6</p>
				<h2>Two Dialects</h2>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					For five chapters the men's league changed under your eyes. Next door, a second league
					has been playing the whole time. Same sport, same shots, but a different accent.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Forget "how far behind". That is the wrong question. Watch where the WPL actually sits
					next to the IPL, and you find it standing beside the men's path, not somewhere back
					along it.
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
