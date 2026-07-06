<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C4-12 — Chapter close (storyboard §3): the tide skyline exhales back into the
	 * free field (the controlling morph's return leg, fast). One caption carries the
	 * chapter's register ("the ground itself moved") number-free, keeps the planted
	 * 2023 mystery OPEN (it is deliberately not resolved here), and aims forward at
	 * what a score is now worth without a number (titles are commitments, numbers
	 * aren't). Pure text over the settling field, so it does not adopt the
	 * read-then-watch fade (nothing to watch in the gap — CONTRACT §17.4).
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const shown = $derived(progress >= 0.45);
</script>

<div class="pin" class:active>
	<div class="caption-slot" class:shown>
		<div class="scene-card">
			<p>
				The water moved under everyone. <strong>The score that used to win now loses,</strong> the
				powerplay caught fire, and records that stood for a decade fell twice in a fortnight. And that
				2023 cliff is still sitting there, unexplained. We meant it: hold that thought.
				<strong>Next: what a single ball is even worth, once the water is this high.</strong>
			</p>
		</div>
	</div>
</div>

<style>
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	.pin.active {
		visibility: visible;
	}

	.caption-slot {
		opacity: 0;
		max-width: min(36rem, 88vw);
	}

	.caption-slot.shown {
		opacity: 1;
	}
</style>
