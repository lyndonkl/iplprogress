<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C1-1 — Chapter title + the ritual (storyboard §3). Free field dimmed
	 * behind; loop stopped. Two caption steps, one change each: the title,
	 * then the sighter named in fan language before any data.
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.55 ? 1 : 2);
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card title-card">
				<p class="overline">Chapter 1</p>
				<h2>The Death of the Sighter</h2>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					For T20's first ten years, every innings opened the same way, with a little ritual: <strong>the sighter</strong>.
					Ten balls of just having a look. Getting your eye in. Giving the bowler some respect.
				</p>
				<p class="follow">Watch what happened to it.</p>
			</div>
		{/if}
	</div>
</div>

<style>
	/* viewport-fixed while this scene owns the field (the sticky-pin pattern
	   unpins for the last 100vh of a section — annotations must stay glued to
	   the canvas for the WHOLE scene, and exactly one scene shows at a time) */
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
		left: 8vw;
		bottom: 14vh;
		max-width: min(34rem, 84vw);
	}

	.title-card h2 {
		font-size: clamp(1.8rem, 5vw, 2.8rem);
	}

	.scene-card .follow {
		margin-top: 0.7rem;
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(12vh, calc(env(safe-area-inset-bottom) + 10vh));
		}
	}
</style>
