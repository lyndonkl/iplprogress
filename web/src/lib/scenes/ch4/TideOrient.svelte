<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadSandboxData } from '$lib/scenes/sandbox/data';
	import TideScaffold from './TideScaffold.svelte';

	/**
	 * C4-2 — The tide skyline (the chapter's ONE controlling morph, free → tide).
	 * Every full first innings condenses into its innings-total column; the taller the
	 * column, the bigger the score. Seasons run left to right, 2008 to now, then the
	 * WPL on its own block; every OTHER ball settles into the low-alpha reservoir haze
	 * so "every ball ever is here" stays literally true. The baseline / total ladder /
	 * season axis are SVG (TideScaffold), registered to the GL coastline.
	 *
	 * Orient-then-reveal: step 1 says what a column IS, step 2 the season axis, step 3
	 * the coastline reveal. First-innings membership is client-baked ONCE from the
	 * columnar `innings` array (zero pipeline dependency — CONTRACT §18.5).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 190 / 360 → morph ends ≈ 0.53 */
	const step = $derived.by(() => {
		if (progress < 0.62) return 1;
		if (progress < 0.82) return 2;
		return 3;
	});
	const BOUNDS = [0, 0.62, 0.82, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const scaffoldOn = $derived(reduced || progress >= 0.42);
	const seasonsOn = $derived(reduced || step >= 2);

	/* seed first-innings membership ONCE from the columnar innings array (§18.5) —
	   the working-today path with zero pipeline dependency. Cached with the sandbox
	   dataset, so ch2/ch3's setRunouts/setDismissals reuse the same fetch. */
	let baked = false;
	$effect(() => {
		const f = field;
		if (!f || baked) return;
		baked = true;
		loadSandboxData()
			.then((sb) => {
				const inn = sb.columnar.arrays.innings;
				const firstInn: number[] = [];
				for (let i = 0; i < inn.length; i++) if (inn[i] === 1) firstInn.push(i);
				f.setFirstInnings(firstInn);
			})
			.catch(() => {
				/* graceful: with no membership every ball builds a column (still honest) */
			});
	});
</script>

<div class="pin" class:active>
	<!-- destination-first orientation scaffold (shared, held through C4-3..C4-11) -->
	<TideScaffold {field} on={scaffoldOn} showSeasons={seasonsOn} />

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card chip">
				<p>
					Every column is <strong>one first innings ever batted.</strong> The taller it stands, the
					bigger the score. A little 90 all out is a stub. A 250 is a tower.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card chip">
				<p>
					Columns line up by <strong>season, 2008 on the left to this year on the right,</strong> with
					the WPL on its own block. Each season's innings are sorted short to tall, so the block reads
					as a little skyline.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					Now stand back. <strong>The whole coastline rises as you go right.</strong> Every other ball
					ever bowled is still here too, the faint haze along the floor. Watch the water come in.
					<button class="dagger" onclick={() => footnotesOpen.set('tide-reservoir')} aria-label="How the tide skyline is built">ⓘ</button>
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
		top: 11vh;
		max-width: min(26rem, 42vw);
		opacity: var(--reveal, 1); /* mobile "read, then watch" (CONTRACT §17); 1 on desktop / reduced */
	}

	.dagger {
		pointer-events: auto;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 44px;
		min-height: 44px;
		margin: -10px 0;
		padding: 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 1rem;
		cursor: pointer;
	}

	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: max(10vh, calc(env(safe-area-inset-top) + 56px));
		}
	}
</style>
