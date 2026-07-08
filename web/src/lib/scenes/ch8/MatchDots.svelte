<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import MatchField from './MatchField.svelte';
	import { pickCaptionCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh8Data, int, type Ch8Data } from './data';

	/**
	 * C8-2, THE CONTROLLING MORPH: the free field condenses into the 1,331 match-
	 * dots (free → `matchdots`, declared in index.ts, ~240vh). Every one of the
	 * 316,199 balls flies to the centroid of the match it belongs to, so from here
	 * ONE dot is ONE whole match. This is pure ORIENT (voice rule): the count you
	 * arrive with, the unit swap as it happens, the new count across both leagues,
	 * and the time axis. Zero belief claims, zero grades. Size and brightness encode
	 * nothing (a run-heavy match is no bigger or brighter than a short one).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

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

	/* morphLength 240 / scrollLength 360 → morph ends ≈ 0.67. Four orient steps; the
	   fall plays through step 2, the new count + axis read after it lands. */
	const step = $derived(progress < 0.18 ? 1 : progress < 0.5 ? 2 : progress < 0.78 ? 3 : 4);
	const BOUNDS = [0, 0.18, 0.5, 0.78, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => tick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	const capStyle = $derived.by(() => {
		void tick;
		void progress;
		if (isNarrowViewport() || !field) return '';
		return cornerStyle(pickCaptionCorner(field).corner);
	});

	const nBalls = $derived(ch8 ? int(ch8.match_dots.n_points) : '316,199');
	const nMatches = $derived(ch8 ? int(ch8.match_dots.count) : '1,331');
</script>

<div class="pin" class:active>
	<MatchField {field} {reduced} {progress} axis={true} legend={true} footnoteId="ch8-matchdots" />

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>Every ball you have watched. All {nBalls} of them.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>Now watch them fall together. One dot, one whole match.</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>{nMatches} matches. Every one the men's and women's leagues have ever played.</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>Left to right is every season, 2008 to 2026. This is the field we grade every belief on.</p>
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
		top: 15vh;
		max-width: min(24rem, 42vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			right: auto;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
