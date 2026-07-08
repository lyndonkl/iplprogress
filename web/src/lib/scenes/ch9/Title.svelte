<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { loadCh9Data, type Ch9Data } from './data';

	/**
	 * C9-1, Chapter title + the MYSTERY HANDOFF IN from Chapter 8 ("beliefs churn,
	 * but underneath, some things refuse to move"). Names the frame: everything
	 * captains believe gets torn up and rebuilt on a clock, and this chapter finds
	 * what stays. Zero numbers on a title (titles are commitments, numbers are not).
	 * The free field idles behind the card, loop stopped; the reader's team stays
	 * lit. Pure text over a static field, so per CONTRACT §17.4 it does NOT adopt
	 * read-then-watch (nothing to watch in a gap). Register: elegiac but warm.
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	let ch9 = $state<Ch9Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh9Data().then((d) => {
			if (alive) ch9 = d;
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
				<p class="overline">Chapter 9</p>
				<h2>The Living League</h2>
				<p class="sub">Everything gets torn up and rebuilt. Some things never move.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					{ch9?.mystery_handoff_in ??
						'Last chapter, beliefs churned. A whole doctrine could arrive and die inside a broadcast cycle. But underneath all that churn, some things refuse to move.'}
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>Squads get blown up on a clock. The rivalries do not. Let's find what stays.</p>
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
		max-width: min(32rem, 86vw);
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
