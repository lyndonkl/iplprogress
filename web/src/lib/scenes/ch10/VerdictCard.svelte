<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import RibbonField from './RibbonField.svelte';
	import { pickRibbonCorner, cornerStyle } from './captionCorner.svelte';
	import { loadCh10Data, signed1, fmt1, type Ch10Data } from './data';

	/**
	 * C10-5, Supporting 2: the Bridge-Player Verdict (the 2023 mystery, closed). The
	 * 56 batters who played both 2023 and 2024 got only about +3 within themselves
	 * while the league jumped +8.9, so about two-thirds of the explosion was new faces
	 * and new roles, not the same players hitting harder. Two grammars: the legitimate
	 * within-vs-turnover TWO-WAY bar (which does sum to +8.87), and the three-suspect
	 * VERDICT CARD as three CO-EQUAL panels (deliberately NOT a partition, so the
	 * reader is never invited to sum the three suspects to 100%). A weight of evidence
	 * across three chapters, never one cause.
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

	const step = $derived(progress < 0.2 ? 1 : progress < 0.4 ? 2 : progress < 0.6 ? 3 : progress < 0.8 ? 4 : 5);
	const BOUNDS = [0, 0.2, 0.4, 0.6, 0.8, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const corner = $derived(pickRibbonCorner(field, 'bl'));

	const b = $derived(ch10?.bridge ?? null);
	const ss = $derived(b?.shift_share ?? null);
	const showBar = $derived(reduced || step >= 2);
	const showPanels = $derived(reduced || step >= 4);
</script>

<div class="pin" class:active>
	<RibbonField {field} {progress} faint={true} footnoteId="ch10-bridge" />

	{#if b && ss}
		<div class="exhibit">
			{#if showBar}
				<div class="bar-block">
					<div class="bar-head">
						the 2023 to 2024 jump: <strong>{signed1(b.jump)}</strong> runs per 100 balls
					</div>
					<div class="bar">
						<div class="seg within" style="width: {ss.within_pct}%">
							<span class="seg-t">same players<br /><strong>{signed1(ss.within)}</strong> ({ss.within_pct}%)</span>
						</div>
						<div class="seg turnover" style="width: {ss.turnover_pct}%">
							<span class="seg-t">new faces and roles<br /><strong>{signed1(ss.turnover)}</strong> ({ss.turnover_pct}%)</span>
						</div>
					</div>
				</div>
			{/if}

			{#if showPanels}
				<div class="verdict">
					<p class="v-head">{b.verdict.headline}</p>
					<div class="panels">
						{#each b.verdict.panels as p (p.chapter)}
							<div class="panel">
								<span class="p-type">{p.type}</span>
								<p class="p-text">{p.text}</p>
								{#if p.number}<span class="p-num">{p.number}</span>{/if}
								<span class="p-badge">Chapter {p.chapter}</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{/if}

	<div class="caption-slot" style="{cornerStyle(corner)}; --reveal: {reveal};">
		{#if b}
			{#if step === 1}
				<div class="scene-card">
					<p>Back to the mystery Chapter 4 could not solve. Scoring jumped {signed1(b.jump)} runs per 100 balls between 2023 and 2024. Who did it?</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>Start with the {b.n_bridge} batters who played both seasons. Held against themselves, they got about {fmt1(b.shift_share.within)} runs per 100 faster. Real, but small.</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>So the same players are only a third of the story. The other two-thirds is new faces and old faces in new roles. The same players hit only a little harder. Most of the change was who was batting.</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>Case closed. Three suspects, all guilty on a different count. The rule opened the door (Chapter 7). New faces walked through it (about two-thirds, here). And the skill had been climbing for a decade (Chapter 1).</p>
				</div>
			{:else}
				<div class="scene-card interactive">
					<p>So, a genuinely new era, or a louder old game? Both. The rule opened the door, new faces walked through it, and it all sat on a decade of climbing skill. Three things, each doing some of the work, not one that made it happen.</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch10-bridge')}>ⓘ how the case is built</button>
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

	.exhibit {
		position: absolute;
		left: 50%;
		top: 46%;
		transform: translate(-50%, -50%);
		width: min(52rem, 88vw);
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
	}

	.bar-head {
		font-size: 0.82rem;
		color: var(--ink-dim);
		margin-bottom: 0.4rem;
	}

	.bar-head strong {
		color: var(--ink);
		font-size: 1rem;
	}

	.bar {
		display: flex;
		width: 100%;
		height: 3.4rem;
		border-radius: 8px;
		overflow: hidden;
		border: 1px solid rgba(151, 161, 184, 0.28);
	}

	.seg {
		display: flex;
		align-items: center;
		justify-content: center;
		text-align: center;
		font-size: 0.72rem;
		line-height: 1.25;
		color: var(--ink);
	}

	.seg.within {
		background: rgba(151, 161, 184, 0.32);
	}

	.seg.turnover {
		background: rgba(46, 196, 182, 0.34);
	}

	.seg-t strong {
		font-size: 0.95rem;
	}

	.v-head {
		font-size: 0.92rem;
		font-weight: 700;
		color: var(--ink);
		margin-bottom: 0.6rem;
	}

	.panels {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.7rem;
	}

	.panel {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		padding: 0.7rem 0.8rem;
		border-radius: 10px;
		background: rgba(10, 14, 24, 0.8);
		border: 1px solid rgba(151, 161, 184, 0.25);
	}

	.p-type {
		font-size: 0.6rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--teal);
	}

	.p-text {
		font-size: 0.85rem;
		line-height: 1.35;
		color: var(--ink);
	}

	.p-num {
		font-size: 0.9rem;
		font-weight: 700;
		color: var(--ink);
	}

	.p-badge {
		margin-top: auto;
		font-size: 0.66rem;
		color: var(--ink-dim);
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
		.exhibit {
			width: 92vw;
			top: 38%;
			gap: 0.9rem;
		}

		.panels {
			grid-template-columns: 1fr;
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
