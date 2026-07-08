<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import DuelField from './DuelField.svelte';
	import LoyaltyChart from './LoyaltyChart.svelte';
	import { panelCaptionStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh9Data, pct0, type Ch9Data } from './data';

	/**
	 * C9-6, SUPPORTING 1: the Loyalty Spectrum (the churn in careers). One line, the
	 * one-club players (four seasons deep, only ever one shirt), falling from about
	 * 27 in 100 to about 12, on a 0-based axis so the halving reads at half height.
	 * At the other extreme, on its own off the line, the man who wore nine shirts,
	 * Aaron Finch. The shirts churn too, but the rivalries outlive them. A
	 * description, never a claim that loyalty protects anything.
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

	const step = $derived(progress < 0.24 ? 1 : progress < 0.5 ? 2 : progress < 0.78 ? 3 : 4);
	const BOUNDS = [0, 0.24, 0.5, 0.78, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const chartReveal = $derived(reduced ? 1 : Math.min(1, progress / 0.72));

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

	const loy = $derived(ch9?.loyalty ?? null);
	const finch = $derived(loy?.max_shirts ?? null);
	const showFinch = $derived(reduced || step >= 3);
</script>

<div class="pin" class:active>
	<DuelField {field} legend={true} faint={true} footnoteId="ch9-loyalty" />

	{#if loy}
		<div class="panel" bind:this={panel}>
			<LoyaltyChart
				series={loy.series}
				peak={loy.peak}
				trough={loy.trough}
				yDomain={loy.y_domain}
				reveal={chartReveal}
				{reduced}
			/>
		</div>
	{/if}

	{#if finch && showFinch}
		<div class="finch">
			<span class="finch-h">the opposite extreme</span>
			<span class="finch-n">{finch.n} shirts</span>
			<span class="finch-name">{finch.name}</span>
			<span class="finch-teams">{finch.shorts.join(' · ')}</span>
		</div>
	{/if}

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if loy}
			{#if step === 1}
				<div class="scene-card">
					<p>One last way to see the churn. A one-club player is someone four seasons deep who only ever wore one shirt.</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>
						They are vanishing. One-club players roughly halved, from about {pct0(loy.peak.pct)} in
						100 down to about {pct0(loy.trough.pct)}.
					</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						Now the opposite extreme, on its own. One man wore {finch?.n ?? 9} different shirts:
						{finch?.name ?? 'AJ Finch'}, a whole league on one CV.
					</p>
				</div>
			{:else}
				<div class="scene-card interactive">
					<p>So the shirts churn too. But the rivalries outlive them. Finch kept meeting the same bowlers, whatever badge he had on.</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch9-loyalty')}>ⓘ how a one-club player is counted</button>
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

	.finch {
		position: absolute;
		right: 4vw;
		top: 16vh;
		display: flex;
		flex-direction: column;
		gap: 0.12rem;
		padding: 0.6rem 0.85rem;
		border-radius: 12px;
		background: rgba(232, 163, 61, 0.12);
		border: 1px solid rgba(232, 163, 61, 0.4);
		max-width: 12rem;
	}

	.finch-h {
		font-size: 0.6rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--gold);
	}

	.finch-n {
		font-size: 1.3rem;
		font-weight: 800;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.finch-name {
		font-size: 0.9rem;
		font-weight: 700;
		color: var(--ink);
	}

	.finch-teams {
		font-size: 0.66rem;
		color: var(--ink-dim);
		line-height: 1.4;
	}

	.caption-slot {
		position: absolute;
		right: 5vw;
		top: 15vh;
		max-width: min(24rem, 40vw);
		opacity: var(--reveal, 1);
	}

	@media (max-width: 640px) {
		.panel {
			width: 94vw;
			top: 40%;
		}

		.finch {
			right: 2vw;
			top: 9vh;
			padding: 0.4rem 0.6rem;
			max-width: 44vw;
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
