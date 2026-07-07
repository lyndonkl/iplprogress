<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { loadCh7Data, type Ch7Data } from './data';

	/**
	 * C7-8 — Chapter close: the MYSTERY HANDOFF OUT + the hand-off to Chapter 8.
	 * The rivers exhale back into the free field behind these two steps (the
	 * controlling morph's return leg, declared in index.ts). No numbers — closes
	 * commit, they do not count. Pure text over the exhale, so per CONTRACT §17.4
	 * the caption stays persistent (nothing to watch in a gap).
	 *
	 * Two load-bearing handoffs: (1) the mystery the chapter plants for Chapter 10
	 * — same players, or new ones? (the bridge-player index settles it); (2) the
	 * Chapter 8 hook — learning is what modern franchises do.
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

	const step = $derived(progress < 0.55 ? 1 : 2);
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>
					{ch7?.mystery_handoff_out ??
						'So the rule opened the door. But was it the same players scoring faster, or new ones? Hold that too; the last chapter settles it.'}
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					One thing is clear already. Teams cracked the twelfth man in barely two seasons. Learning
					fast is what a modern franchise does. Next we grade everything else the captains thought
					they knew. Next: <strong>The Captain's Brain.</strong>
				</p>
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
