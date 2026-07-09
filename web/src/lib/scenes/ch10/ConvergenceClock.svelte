<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import RibbonField from './RibbonField.svelte';
	import ConvergenceFans from './ConvergenceFans.svelte';
	import { pickRibbonCorner, cornerStyle } from './captionCorner.svelte';
	import { loadCh10Data, fmt2, type Ch10Data } from './data';

	/**
	 * C10-7, the WPL thread + the Convergence Clock. Point the machine forward. If the
	 * run-rate trend holds, the men's game crosses ten an over around 2028-29 (already
	 * 9.88), with the band running past 2030. The women's league run rate is rising on
	 * a slope you can read, toward where the men's game sits TODAY (a fixed level,
	 * never a moving target); its six-hitting is so far out on four seasons that it is
	 * honestly off the clock. Uncertainty owned loudly, fans not prophets. NEVER
	 * "behind / catching up / closing on the men's game".
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	let ch10 = $state<Ch10Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh10Data().then((d) => {
			if (alive) ch10 = d;
		});
		return () => {
			alive = false;
		};
	});

	const step = $derived(progress < 0.26 ? 1 : progress < 0.5 ? 2 : progress < 0.76 ? 3 : 4);
	const BOUNDS = [0, 0.26, 0.5, 0.76, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const corner = $derived(pickRibbonCorner(field, 'bl'));
	const today = $derived(ch10?.convergence.mens.today ?? null);
</script>

<div class="pin" class:active>
	<RibbonField {field} {progress} faint={true} footnoteId="ch10-convergence" />

	{#if ch10}
		<div class="panel">
			<ConvergenceFans d={ch10} />
		</div>
	{/if}

	<div class="caption-slot" style="{cornerStyle(corner)}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>Now point the machine forward. The solid line is what actually happened, up to today. Past today it goes dashed, and the shaded band around it fans out, because the further out we look the less sure we are.</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>Runs an over already sit at {fmt2(today?.rpo ?? 9.88)}. If the climb holds, the men's game crosses ten an over around 2028 or 2029, and the band runs out past 2030.</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>The women's league is four seasons old, and its run rate is rising on a slope you can already read, toward where the men's game sits today.</p>
			</div>
		{:else}
			<div class="scene-card interactive">
				<p>But its six-hitting is a different story. On four seasons it is so far out that it is honestly off the clock. We are fans clocking a young league, not prophets.</p>
				<button class="fn" onclick={() => footnotesOpen.set('ch10-convergence')}>ⓘ how the clock is read</button>
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

	.panel {
		position: absolute;
		left: 50%;
		top: 46%;
		transform: translate(-50%, -50%);
		width: min(64vw, 52rem);
		padding: 0.9rem 1.1rem;
		border-radius: 14px;
		background: rgba(10, 14, 24, 0.72);
		border: 1px solid rgba(151, 161, 184, 0.2);
	}

	.caption-slot {
		position: absolute;
		max-width: min(24rem, 38vw);
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
			width: 92vw;
			top: 40%;
		}

		.caption-slot {
			left: 50% !important;
			right: auto !important;
			top: auto !important;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px)) !important;
		}
	}
</style>
