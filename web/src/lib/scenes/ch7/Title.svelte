<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { loadCh7Data, type Ch7Data } from './data';

	/**
	 * C7-1 — Chapter title + the MYSTERY HANDOFF IN. Chapter 4 planted the 2023
	 * cliff and visibly deferred it; this chapter picks it up ("here is the
	 * suspect"). Zero numbers on a title (titles are commitments, numbers are
	 * not). The free field idles dimmed behind the card, loop stopped; the
	 * reader's team stays lit. Pure text over a static field, so per CONTRACT
	 * §17.4 it does NOT adopt read-then-watch (nothing to watch in a gap).
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	let ch7 = $state<Ch7Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh7Data().then((d) => {
			if (alive) ch7 = d;
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
				<p class="overline">Chapter 7</p>
				<h2>The Twelfth Man</h2>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Remember the cliff. Back in Chapter 4 the scoreboard jumped in 2023 and would not say why.
					We told you to hold that thought.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					{ch7?.mystery_handoff_in ?? 'Chapter 4 showed you the cliff. Here is the suspect.'}
					In 2023 the IPL let a team field a twelfth player mid-match. The scoreboard has not been the
					same since. Let us see how much of that was the rule.
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
		top: 14vh;
		max-width: min(26rem, 86vw);
	}

	.title-card h2 {
		font-size: clamp(1.6rem, 4.4vw, 2.4rem);
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(10vh, calc(env(safe-area-inset-bottom) + 64px));
		}
	}
</style>
