<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * C10-9, the finale close: total the whole piece in one breath (the data drew its
	 * own fault lines, the modern era is a stack of them), then exhale the ribbon back
	 * into the cold-open free field (the controlling morph's reverse leg, declared in
	 * index.ts), so the piece ends where it began, byte-identical to entry. A
	 * protected recognition beat ("except now you can read it") lands before the hand
	 * to the reader. There is no next-chapter tease, because the narrative is complete;
	 * the handoff is to the sandbox that rises after (the shell's post-narrative
	 * surface). No new number (closes commit, they do not count). Register: valedictory
	 * and warm.
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.26 ? 1 : progress < 0.52 ? 2 : progress < 0.78 ? 3 : 4);
</script>

<div class="pin" class:active>
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>So there it is. The game did not change once. It broke in stages, sixes first, then everything at once in 2023, on top of a decade of climbing skill.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>And the data drew every one of those lines itself. We just handed it the whole history and asked where the game broke.</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>This is where we started. The same cloud of every ball ever bowled. Except now you can read it.</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>Your turn. Every ball is still here. Go find your own.</p>
				<p class="note">the sandbox is yours</p>
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
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		max-width: min(32rem, 88vw);
		text-align: center;
	}

	@media (max-width: 640px) {
		.caption-slot {
			width: 92vw;
			max-width: 92vw;
		}
	}
</style>
