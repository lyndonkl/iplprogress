<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { loadCh8Data, type Ch8Data } from './data';

	/**
	 * C8-1, Chapter title + the MYSTERY HANDOFF IN from Chapter 7 ("learning is
	 * what modern franchises do; so let's audit everything else captains learned").
	 * Names the frame: five beliefs, graded on the whole record, four fail and one
	 * passes, and we saved it for last. Zero numbers on a title (titles are
	 * commitments, numbers are not). The free field idles behind the card, loop
	 * stopped; the reader's team stays lit. Pure text over a static field, so per
	 * CONTRACT §17.4 it does NOT adopt read-then-watch (nothing to watch in a gap).
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	let ch8 = $state<Ch8Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh8Data().then((d) => {
			if (alive) ch8 = d;
		});
		return () => {
			alive = false;
		};
	});

	const step = $derived(progress < 0.4 ? 1 : progress < 0.72 ? 2 : 3);
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card title-card">
				<p class="overline">Chapter 8</p>
				<h2>The Captain's Brain</h2>
				<p class="sub">The analytics era rewired what captains believe. Let's grade it.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					{ch8?.mystery_handoff_in ??
						"Last chapter, one rule rewired the game. Learning is what modern franchises do. So let's audit everything else captains learned."}
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Five beliefs. We put each one to the whole record. Four of them fail. One passes, and we
					saved it for last.
				</p>
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
		max-width: min(30rem, 86vw);
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
