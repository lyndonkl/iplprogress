<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import RiverPlane from './RiverPlane.svelte';
	import { pickCaptionCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh7Data, fmt1, type Ch7Data } from './data';

	/**
	 * C7-3 — THE HERO, first half: the FORK at the rule year. Four one-point beats
	 * (storyboard C7-3, decomposed per audit consider #11 so no step carries more
	 * than one on-screen change): (1) the men's river is flat for its first fifteen
	 * years; (2) at 2023 the twelfth man arrives (the sparks) and the river climbs;
	 * (3) the women's river, no such rule, barely lifts; (4) the gap that opens is
	 * close to a run an over, at the exact rule year — the shape that makes the rule
	 * the prime suspect. The ruler-gloss + the honest confound are the SECOND half
	 * (C7-4, Ruler.svelte). Numbers stay under cap and the full 8.99/9.56/9.63/9.88
	 * ladder lives in the ch7-rivers footnote, never in a caption (audit must-fix #4).
	 *
	 * flowLift 0→1 (the climb) and sparks.glow 0→1 are POST-MORPH field changes owned
	 * by the scene's dynamicState (index.ts); this component owns the captions, the
	 * gap shading gate, and feeding spark membership.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

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

	/* feed the 517 impact-sub spark indices ONCE — §23.4 (no pipeline seed). */
	let sparked = false;
	$effect(() => {
		const f = field;
		const d = ch7;
		if (!f || !d || sparked) return;
		sparked = true;
		f.setSparks(d.impact_subs.spark_indices);
	});

	const ne = $derived(ch7?.natural_experiment ?? null);

	/* four one-point steps: flat / climb+sparks / WPL level / the gap. The lift and
	   sparks (index.ts dynamicState) play during step 2; the gap read lands at step 3+ */
	const step = $derived(progress < 0.3 ? 1 : progress < 0.52 ? 2 : progress < 0.76 ? 3 : 4);
	const BOUNDS = [0, 0.3, 0.52, 0.76, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const diverged = $derived(reduced || progress >= 0.52);

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
	<RiverPlane
		{field}
		{reduced}
		{progress}
		on={true}
		showGap={diverged}
		legend={true}
		footnoteId="ch7-rivers"
	/>

	<div class="caption-slot" class:gap={reveal < 0.5} style="{capStyle}; --reveal: {reveal};">
		{#if step === 1 && ne}
			<div class="scene-card">
				<p>
					Look at the men's river for its first fifteen years. Flat. Season after season it wandered
					between {fmt1(ne.ipl_pre_band.min)} and {fmt1(ne.ipl_pre_band.max)} runs an over, and never
					broke out.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Then 2023, the rule year. The twelfth man arrives. Those bright dots are the subs walking
					in, and the river climbs. It keeps climbing, every season since, up toward 10 an over.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					Now the women's river, over the very same four years. No twelfth-man rule. It barely lifts,
					about half a run, then just holds its line.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					So a gap opens, close to a run an over, and it opens the exact year of the rule. That is the
					shape that makes the rule the prime suspect.
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
		bottom: 8vh;
		max-width: min(25rem, 42vw);
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
