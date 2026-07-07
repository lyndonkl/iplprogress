<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C6-10 — Chapter close: the dialect lands, then the hand-off to Chapter 7. The
	 * constellation exhales back into the free field behind these two steps (the
	 * controlling morph's return leg, declared in index.ts). No numbers — closes
	 * commit, they do not count (the nav rule). Pure text over the exhale, so per
	 * CONTRACT §17.4 the caption stays persistent (nothing to watch in a gap).
	 *
	 * The hand-off is load-bearing: Ch 7's diff-in-diff needs the WPL already met
	 * as a full character (the control arm), which is exactly what this chapter
	 * built — beside the path, its own dialect.
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.55 ? 1 : 2);
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>
					So the women's game is not the men's game running late. It scores as fast, along the
					ground instead of over the rope, on spin instead of pace, and it finishes tighter than
					anything else in the sport. A different dialect, beside the men's path.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Which sets up a gift. In 2023 the men added a rule many credit for their scoring taking
					off. The women never did. One big rule apart, though they differ in more than that. A rare
					natural experiment. Next: <strong>The Twelfth Man.</strong>
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
