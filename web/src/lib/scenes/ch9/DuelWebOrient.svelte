<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import DuelField from './DuelField.svelte';
	import DuelStrands from './DuelStrands.svelte';
	import { pickCaptionCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh9Data, heroDuel, int, type Ch9Data } from './data';

	/**
	 * C9-2, THE CONTROLLING MORPH: the free field condenses into the duel web (free
	 * -> `duelweb`, declared in index.ts, ~240vh). Every one of the 316,199 balls
	 * flies to the strand of the rivalry it belongs to, or sinks into the dim dust.
	 * This is pure ORIENT (voice rule): the count you arrive with, the new mark
	 * (a strand is a duel) taught on ONE isolated named strand first (Kohli-Jadeja),
	 * then the dust split, then the red/blue "who came out on top" key, then a light
	 * touch that position carries era. Zero arguments, zero grades. A dot is still a
	 * ball; size and brightness encode nothing.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

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

	/* five orient steps; the balls fly through steps 1-2, the marks read after. */
	const step = $derived(
		progress < 0.16 ? 1 : progress < 0.42 ? 2 : progress < 0.62 ? 3 : progress < 0.82 ? 4 : 5
	);
	const BOUNDS = [0, 0.16, 0.42, 0.62, 0.82, 1] as const;
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

	const hero = $derived(ch9 ? heroDuel(ch9) : null);
	const heroId = $derived(hero ? hero.id : null);
	/* teach the mark on ONE isolated strand first (steps 1-2), then release the web */
	const focusIds = $derived(reduced ? null : step <= 2 && heroId != null ? [heroId] : null);
	const topN = $derived(isNarrowViewport() ? 42 : 60);

	const nBalls = $derived(ch9 ? int(ch9.duel_web.meta.balls_split.total_points) : '316,199');
	const nInDuel = $derived(ch9 ? int(ch9.duel_web.meta.balls_split.in_duel_points) : '79,378');
</script>

<div class="pin" class:active>
	<DuelField {field} legend={true} footnoteId="ch9-duel" />
	<DuelStrands
		{field}
		{reduced}
		{progress}
		{active}
		{topN}
		{focusIds}
		{heroId}
		showHubLabels={step >= 5 || reduced}
		hubLabelCount={isNarrowViewport() ? 3 : 5}
	/>

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>Every ball ever bowled. All {nBalls} of them, back in the sky.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Watch one rivalry form first. These balls pile onto a single strand between two players,
					Kohli and Jadeja. A dot is still one ball. A strand is one duel: the two who kept facing
					each other.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					About a quarter of every ball ever bowled lands in a real rivalry, {nInDuel} of them. The
					rest is dust, the games nobody remembers.
				</p>
			</div>
		{:else if step === 4}
			<div class="scene-card">
				<p>
					A strand runs red for runs, the batter's color, and blue when the bowler came out on top.
					The more one-sided it was, the deeper the color. A pale strand was an even fight.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					And the layout is a timeline. The busiest players sit dead centre, the 2008 crowd drifts
					one way and today's stars the other.
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
		top: 15vh;
		max-width: min(25rem, 42vw);
		opacity: var(--reveal, 1);
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
