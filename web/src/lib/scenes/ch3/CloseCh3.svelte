<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C3-9 — Chapter close (storyboard §3): the frontier plane exhales back into
	 * the free field (the controlling morph's return leg, fast). One caption
	 * carries both halves of the counterrevolution register — the loss of the
	 * containment bowler and the affirmation that the bowler got better (the True
	 * Economy point in number-free main-flow words) — then aims at Chapter 4
	 * without a number (titles are commitments, numbers aren't).
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const shown = $derived(progress >= 0.45);
</script>

<div class="pin" class:active>
	<div class="caption-slot" class:shown>
		<div class="scene-card">
			<p>
				The old stopper is gone, the bowler who dried the game up and kept it under seven an over.
				<strong>He did not fail. The tide came in over his head.</strong> What stands in his place
				attacks more and risks more, and here is the part the scoreboard hides: he is a
				<strong>better bowler than bowlers have ever been.</strong> He just has a far harder job.
				<strong>Next: the tide itself, and how high it really got.</strong>
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
