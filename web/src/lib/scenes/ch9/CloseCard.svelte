<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { loadCh9Data, type Ch9Data } from './data';

	/**
	 * C9-9, Chapter close: compress the chapter to one breath (institutions churn,
	 * the human fabric holds), then hand to Chapter 10. The web exhales back into the
	 * free scatter (the controlling morph's reverse leg, declared in index.ts), so
	 * the end card's field is byte-identical to entry. No numbers (closes commit, they
	 * do not count). Ch 9 showed what STAYS under the churn (the rivalries); Ch 10
	 * will judge whether the modern game is a new era at all, so neither pre-judges
	 * the other.
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

	const step = $derived(progress < 0.34 ? 1 : progress < 0.66 ? 2 : 3);
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>So here is the living league. Squads get blown up on a clock. Careers scatter across nine shirts. The auction never stops.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>But the rivalries refuse to move. The same players keep meeting, straight through every reset. Institutions churn. The human fabric holds.</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					{ch9?.mystery_handoff_out ??
						'One question is still open. Was 2023 a genuinely new era, or just a louder version of the old game? Next chapter, the Era Machine settles it.'}
				</p>
				<p class="note">Next: <strong>The Era Machine.</strong></p>
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
		max-width: min(30rem, 86vw);
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
