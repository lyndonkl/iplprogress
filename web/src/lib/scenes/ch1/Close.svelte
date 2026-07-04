<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C1-8 — Chapter close (storyboard §3): the wall exhales back into the
	 * free field (the controlling morph's return leg); one caption compresses
	 * the chapter WITH its scope intact — the no-extra-risk claim is never
	 * restated unscoped (blueprint's one mandated inoculation).
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const shown = $derived(progress >= 0.45);
</script>

<div class="pin" class:active>
	<div class="caption-slot" class:shown>
		<div class="scene-card">
			<p>
				Batters attacked from ball one — and those balls cost them nothing extra. Where risk
				rose later, they paid it on purpose. That freedom rewired everything: what a good
				score is, what bowlers do, <strong>what a wicket is worth.</strong> That's the rest
				of the story.
			</p>
		</div>
	</div>
</div>

<style>
	/* viewport-fixed while active — one scene's captions on screen at a time */
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

	/* instant show/hide — appear-states never ride a transition */
	.caption-slot {
		opacity: 0;
	}

	.caption-slot.shown {
		opacity: 1;
	}
</style>
