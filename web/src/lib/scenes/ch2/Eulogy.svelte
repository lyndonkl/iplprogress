<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C2-1 — Chapter title + the eulogy (storyboard §3). Free field dimmed one
	 * stop behind; loop stopped. Three caption steps, one change each, ELEGY
	 * register: name the thing that is dying in fan language, praise it (step 2's
	 * last clause names the batting revolution as the hunter — the answer to
	 * Ch 1's "and then what?"), then say goodbye — and seed the celebratory
	 * thesis in the same breath (step 3), so a deep-entry bounce never gets pure
	 * anchor-nostalgia (§7 RESOLVED #3).
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.34) return 1;
		if (progress < 0.68) return 2;
		return 3;
	});
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card title-card">
				<p class="overline">Chapter 2</p>
				<h2>The Last of the Anchors</h2>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Every team used to have one. When a wicket fell, he walked in and did the quiet
					work. He saw off the good balls, kept the score ticking, <strong>held the innings
						together</strong> while the big hitters swung. Cricket had a name for him.
					<strong>The anchor</strong>. Then the game learned to bat flat out from ball one,
					and it came looking for him.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					We came to say goodbye. <strong>To the man, not the runs.</strong> The game he built
					is faster now.
				</p>
				<p class="follow">Scroll on.</p>
			</div>
		{/if}
	</div>
</div>

<style>
	/* viewport-fixed while this scene owns the field — exactly one scene's
	   captions on screen at a time (the sticky-pin pattern unpins over the last
	   100vh of a section, so annotations use a fixed pin instead) */
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
		color: var(--ink-dim);
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
