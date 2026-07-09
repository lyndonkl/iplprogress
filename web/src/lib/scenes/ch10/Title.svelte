<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C10-1, Chapter title + the handoff from Chapter 9 ("was 2023 a genuinely new
	 * era, or just a louder version of the old game"). Names the frame: for nine
	 * chapters we told you where the eras were, now we stop narrating and hand the
	 * pen to the data. Zero numbers on a title (titles are commitments, numbers are
	 * not). The free field idles behind the card, loop stopped; the reader's team
	 * stays lit. Pure text over a static field, so per CONTRACT §17.4 it does NOT
	 * adopt read-then-watch (nothing to watch in a gap). Register: valedictory.
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.4 ? 1 : progress < 0.72 ? 2 : 3);
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card title-card">
				<p class="overline">Chapter 10</p>
				<h2>The Era Machine</h2>
				<p class="sub">For nine chapters we told you where the eras were. Now we let the data draw its own.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Last chapter left one question open. Was 2023 a genuinely new era, or just a louder version
					of the old game? Time to settle it.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>So we stop narrating. We hand the whole history to the machine, and we let it show us exactly where the game broke.</p>
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
		bottom: 12vh;
		max-width: min(32rem, 86vw);
	}

	.title-card h2 {
		font-size: clamp(1.7rem, 4.6vw, 2.6rem);
	}

	.sub {
		margin-top: 0.55rem;
		font-size: clamp(1rem, 2.4vw, 1.2rem);
		color: var(--ink-dim);
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(10vh, calc(env(safe-area-inset-bottom) + 64px));
		}
	}
</style>
