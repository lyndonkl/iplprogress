<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C1-3 — The pivot (storyboard §3): voice the objection every fan is
	 * already making, so the out-rate strip lands as an answer, not a chart.
	 * Wall holds dimmed one stop behind; loop stopped; single caption.
	 */
	let { active }: SceneAnnotationProps = $props();
</script>

<div class="pin" class:active>
	<div class="scene-card center">
		<p>
			Of course they score faster now. <strong>So they must be getting out way more too. Right?</strong>
		</p>
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

	.center {
		text-align: center;
	}
</style>
