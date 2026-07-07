<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh6Data, starTables, type Ch6Data } from './data';
	import { pickCaptionCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';
	import Starfield from './Starfield.svelte';

	/**
	 * C6-2 — THE CONTROLLING MORPH: the free field condenses into 23 season-stars
	 * (free → `constellation`, declared in index.ts). Every ball flies to its
	 * season-group's star, so a star reads as a glowing disc of that season's own
	 * deliveries. This component FEEDS the four Procrustes-aligned star tables ONCE
	 * (setStarTables — VERBATIM from the artifact, CONTRACT §22.2: never re-embed),
	 * then reveals the men's chronological WORM and the WPL dotted THREADS on the
	 * annotation plane (Starfield). The morph itself is declared in index.ts; the
	 * captions carry the point without any tap.
	 *
	 * ORIENT FIRST (voice rule): each star is one season of one league; near = plays
	 * alike ball-for-ball. And the honest caveat, up front: the DIRECTIONS on this
	 * map mean nothing — only how close two stars sit (the axes are not interpretable).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength 150 / scrollLength 340 → morph ends ≈ 0.44 */
	const step = $derived(progress < 0.44 ? 1 : progress < 0.72 ? 2 : 3);
	const BOUNDS = [0, 0.44, 0.72, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	/* the worm/threads/labels appear once the discs have landed (after the morph) */
	const landed = $derived(reduced || progress >= 0.46);
	const showWorm = $derived(reduced || step >= 2);
	const showThreads = $derived(reduced || step >= 3);
	const labelGis = $derived(landed ? [0, 18, 19, 20, 21, 22] : []);

	let ch6 = $state<Ch6Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh6Data().then((d) => {
			if (alive) ch6 = d;
		});
		return () => {
			alive = false;
		};
	});

	/* feed the star tables ONCE per (field, data) pair — §22.2 (VERBATIM) */
	let fed = false;
	$effect(() => {
		const f = field;
		const d = ch6;
		if (!f || !d || fed) return;
		fed = true;
		f.setStarTables(starTables(d));
	});

	/* §0.4a caption safe-corner from the LIVE star geometry (opposite the WPL
	   cluster); re-picks on resize + as the morph settles. Mobile uses the bottom
	   read-then-watch slot, so skip the inline corner there. */
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
</script>

<div class="pin" class:active>
	<Starfield
		{field}
		{reduced}
		{progress}
		on={landed}
		threadPhase="all"
		{showWorm}
		{showThreads}
		{labelGis}
		legend={landed}
		footnoteId="ch6-constellation"
	/>

	<div class="caption-slot" class:gap={reveal < 0.5} style="{capStyle}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>
					Every ball just flew home to its season. Twenty-three stars, one for each season of each
					league, and each star is a glowing ball of that season's own deliveries. Two stars sit
					close when those seasons played alike, ball for ball. Only the closeness means anything.
					Up, down, left, right point nowhere.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Join the men's seasons up in the order they were played and a path appears. Call it the
					worm. It is not a calendar. It is a path across a map of who plays like who, and it does
					not double back: season after season the men drift further from how they played in 2008.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					The recent seasons sit furthest of all from 2008, right out at one end. Now the teal
					stars, the WPL, light up nowhere near that end, in their own little cluster off to one
					side. Beside the path, not on it.
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

	/* desktop: the caption sits in the safe corner (§0.4a), positioned by the
	   inline capStyle picked from the live star geometry, opposite the WPL cluster */
	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 8vh;
		max-width: min(25rem, 40vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.caption-slot {
			right: auto;
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
