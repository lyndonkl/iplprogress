<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C2-9 — Chapter close (storyboard §3): worm-space exhales back into the free
	 * field (the controlling morph's return leg, fast). One caption carries both
	 * halves of the elegy — the farewell and the affirmed gain ("faster and
	 * braver") — then aims at Chapter 3 without a number (titles are commitments,
	 * numbers aren't). Gain-clause wording is varied across the chapter's beats so
	 * the affirmation stays felt, never boilerplate.
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const shown = $derived(progress >= 0.45);
</script>

<div class="pin" class:active>
	<div class="caption-slot" class:shown>
		<div class="scene-card">
			<p>
				The anchor is gone — and the game is <strong>faster and braver</strong> for losing him. But
				he was the <strong>first</strong> casualty, not the last: when batting changes this much, the
				men with the ball have to answer. <strong>That's next.</strong>
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
