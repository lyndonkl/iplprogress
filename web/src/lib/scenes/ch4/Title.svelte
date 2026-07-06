<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C4-1 — Chapter title (storyboard §3). Free field dimmed one stop behind; loop
	 * stopped. Three caption steps, one idea each, "the ground itself moves" register:
	 * name the chapter in fan language, then set the stakes (batters and bowlers
	 * fought while the water rose under both), then point at what a rising tide does
	 * to a score. Pure text over a static field, so this scene does NOT adopt the
	 * read-then-watch fade (nothing to watch in the gap — CONTRACT §17.4).
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
				<p class="overline">Chapter 4</p>
				<h2>The Rising Tide</h2>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					For three chapters the batters and the bowlers fought each other. While they did,
					<strong>the water rose under both of them.</strong> The whole scoring world drifted up, quietly,
					season after season.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Here is what that does to a scoreboard. <strong>The score that used to win now loses.</strong>
					Let me show you the water level itself.
				</p>
				<p class="follow">Scroll on.</p>
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
