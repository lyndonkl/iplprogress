<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import DuelField from './DuelField.svelte';
	import HeartbeatChart from './HeartbeatChart.svelte';
	import { panelCaptionStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh9Data, inHundred, type Ch9Data } from './data';

	/**
	 * C9-4, HERO 2: the Auction Heartbeat (institutions torn up on a clock). The held
	 * web dims to a quiet backdrop; the scene is a 2D EKG (particles carry no meaning
	 * in an EKG, so this spends no morph). ONE bold league-mean line, "how much of a
	 * squad came back", on a labelled 0-to-1 axis, with a faint min-max envelope. It
	 * rests around 46 in 100 and crashes to about 19 in each of the five mega-auction
	 * years. A description of the schedule, never a claim the auction causes anything.
	 * (The ten franchise monitors are opt-in depth; the emitted series carries only
	 * the mean + min-max envelope, so the default single-line view is the data.)
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

	const step = $derived(
		progress < 0.18 ? 1 : progress < 0.4 ? 2 : progress < 0.62 ? 3 : progress < 0.82 ? 4 : 5
	);
	const BOUNDS = [0, 0.18, 0.4, 0.62, 0.82, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	/* the line draws in left-to-right, complete by step 4 (the flatlines drop in the gap) */
	const chartReveal = $derived(reduced ? 1 : Math.min(1, progress / 0.78));

	let panel = $state<HTMLElement | null>(null);
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
		if (isNarrowViewport()) return '';
		return panelCaptionStyle(panel);
	});

	const hb = $derived(ch9?.heartbeat.ipl ?? null);
	const megaYears = $derived(hb?.mega_years ?? []);
</script>

<div class="pin" class:active>
	<DuelField {field} legend={true} faint={true} footnoteId="ch9-heartbeat" />

	{#if hb}
		<div class="panel" bind:this={panel}>
			<HeartbeatChart
				series={hb.series}
				megaYears={hb.mega_years}
				resting={hb.nonmega_mean}
				reveal={chartReveal}
				{reduced}
				yDomain={hb.y_domain}
			/>
		</div>
	{/if}

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if hb}
			{#if step === 1}
				<div class="scene-card">
					<p>
						Leave the web for a moment. This one line is how much of a typical squad came back the
						next season, averaged across the league. High means the band stayed together.
					</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>Most years, about half a squad returns. A steady heartbeat, near {inHundred(hb.nonmega_mean)} in 100.</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						Then every few years the line falls off a cliff. In a mega-auction the whole league is
						torn up at once, and only about {inHundred(hb.mega_mean)} in 100 come back.
					</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>
						{megaYears.length} of these resets in the whole history. {megaYears.join(', ')}. Five
						flatlines, all at once, right across the league.
					</p>
				</div>
			{:else}
				<div class="scene-card interactive">
					<p>Institutions get rebuilt on a clock. Every few years the league blows itself up and starts again.</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch9-heartbeat')}>ⓘ how the heartbeat is counted</button>
				</div>
			{/if}
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

	.panel {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: min(62vw, 60rem);
		max-height: 70vh;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 15vh;
		max-width: min(24rem, 40vw);
		opacity: var(--reveal, 1);
	}

	.fn {
		margin-top: 0.5rem;
		min-height: 40px;
		padding: 0.2rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.78rem;
		font-weight: 600;
		text-align: left;
		cursor: pointer;
	}

	.fn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.panel {
			width: 94vw;
			top: 42%;
		}

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
