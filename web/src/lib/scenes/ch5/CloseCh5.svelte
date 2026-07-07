<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C5-12 — Chapter close: the audit lands, then the hand-off to Two Dialects.
	 * The worth grid exhales back into the free field behind these two steps (the
	 * controlling morph's return leg, declared in index.ts). No numbers — closes
	 * commit, they do not count (the nav rule). Pure text over the exhale, so per
	 * CONTRACT §17.4 the caption stays persistent (nothing to watch in a gap).
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.55 ? 1 : 2);
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>
					So now every ball has a price. The dot costs more than it ever did. The single stopped
					paying its way. Wickets appreciated faster than the runs around them, and whole jobs
					were invented in the space the new prices opened.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					One league, repriced end to end. Next door, a second league speaks a different dialect:
					runs along the ground where this one clears the rope, spin where this one leans on
					pace, finishes tighter than anything you just watched. Next: <strong>Two Dialects.</strong>
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
