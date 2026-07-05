<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C3-1 — Chapter title + turning to face the other end (storyboard §3). Free
	 * field dimmed one stop behind; loop stopped. Three caption steps, one change
	 * each, COUNTERREVOLUTION register: name the chapter in fan language, name the
	 * batting revolution as the thing the bowler has to answer (the reply to Ch 2's
	 * "and then what?"), then seed the affirmation in the same breath (step 3, "they
	 * did not just get beaten") so a deep-entry bounce never lands on pure defeat.
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
				<p class="overline">Chapter 3</p>
				<h2>The Counterrevolution</h2>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					For two chapters the batters have run the show. They attack from ball one, they hunted the
					patient anchor out of the game, and here was the sting: <strong>they did it without
						getting out any more often.</strong> So turn around now and look at the other end of the
					pitch. The men with the ball had to answer all of that.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Here is the part nobody tells you. <strong>The bowlers did not just get beaten.</strong>
					They tore up the old plan and built a stranger, braver one. This is how they fought back.
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
