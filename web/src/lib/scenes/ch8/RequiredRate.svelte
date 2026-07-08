<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import MatchField from './MatchField.svelte';
	import ReportCardRail from './ReportCardRail.svelte';
	import { panelCaptionStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh8Data, fmt1, fmt2, pct0, type Ch8Data } from './data';

	/**
	 * C8-7, SUPPORTING, Belief 5: required-rate responsiveness (PASS, saved for
	 * last so the four fails sting). The dots dim; the scene is the chase run-rate
	 * curve by phase (powerplay, middle, death), pinned to TWO contrasting eras only
	 * (2008-10 vs 2023-26, never a 5-era spaghetti). The up-slope-to-front-load flip
	 * is a clean two-line read: back then chases idled early and slammed the door at
	 * the death; now they front-load, the powerplay above the middle overs. The
	 * honest caveat keeps the PASS from overclaiming: the chase changed shape as
	 * captains say, but it does NOT mean chasing wins more (it still wins about half).
	 */
	const VB_W = 400;
	const VB_H = 220;
	const PL = 40;
	const PR = 60;
	const PT = 24;
	const PB = 40;
	const RR_LO = 7;
	const RR_HI = 10.8;

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

	const step = $derived(
		progress < 0.18
			? 1
			: progress < 0.36
				? 2
				: progress < 0.54
					? 3
					: progress < 0.72
						? 4
						: progress < 0.87
							? 5
							: 6
	);
	const BOUNDS = [0, 0.18, 0.36, 0.54, 0.72, 0.87, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

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
		void step;
		if (isNarrowViewport()) return '';
		return panelCaptionStyle(panel);
	});

	const rr = $derived(ch8?.required_rate ?? null);
	const showNew = $derived(reduced || step >= 3);

	const plotL = PL;
	const plotR = VB_W - PR;
	const plotT = PT;
	const plotB = VB_H - PB;
	const xOfPhase = (i: number): number => plotL + (i / 2) * (plotR - plotL);
	const yOfRate = (v: number): number => plotB - ((v - RR_LO) / (RR_HI - RR_LO)) * (plotB - plotT);
	function poly(era: string): string {
		const c = rr?.curve[era];
		if (!c) return '';
		return c.map(([i, v]) => `${xOfPhase(i).toFixed(1)},${yOfRate(v).toFixed(1)}`).join(' ');
	}
	const endOld = $derived(rr ? { x: xOfPhase(2), y: yOfRate(rr.curve['2008-10'][2][1]) } : null);
	const endNew = $derived(rr ? { x: xOfPhase(2), y: yOfRate(rr.curve['2023-26'][2][1]) } : null);
	const stamped = $derived(reduced || step >= 5 ? 5 : 4);
</script>

<div class="pin" class:active>
	<MatchField {field} {reduced} {progress} faint={true} legend={false} footnoteId="ch8-required" />
	<ReportCardRail report={ch8?.report_card ?? null} {stamped} />

	<div class="stage">
		<div class="panel" bind:this={panel}>
			{#if rr}
				<svg viewBox="0 0 {VB_W} {VB_H}" class="rchart" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
					<!-- gridlines for each phase -->
					{#each [0, 1, 2] as i (i)}
						<line class="grid" x1={xOfPhase(i)} x2={xOfPhase(i)} y1={plotT} y2={plotB} />
						<text class="phase" x={xOfPhase(i)} y={plotB + 16}>
							{i === 0 ? 'powerplay' : i === 1 ? 'middle' : 'death'}
						</text>
					{/each}
					<!-- the 2008 up-slope -->
					<polyline class="curve old" points={poly('2008-10')} />
					{#each rr.curve['2008-10'] as p, i (i)}
						<circle class="dot old" cx={xOfPhase(p[0])} cy={yOfRate(p[1])} r="3" />
					{/each}
					{#if endOld}
						<text class="era-tag old" x={endOld.x + 8} y={endOld.y}>2008</text>
					{/if}
					<!-- the 2026 front-load -->
					{#if showNew}
						<polyline class="curve new" points={poly('2023-26')} />
						{#each rr.curve['2023-26'] as p, i (i)}
							<circle class="dot new" cx={xOfPhase(p[0])} cy={yOfRate(p[1])} r="3" />
						{/each}
						{#if endNew}
							<text class="era-tag new" x={endNew.x + 8} y={endNew.y}>2026</text>
						{/if}
					{/if}
				</svg>
			{/if}
		</div>
	</div>

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if rr}
			{#if step === 1}
				<div class="scene-card">
					<p>
						One more belief, and this one is different. Here is how fast teams score when they chase,
						across the innings: the powerplay, the middle, the death.
					</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>
						Back in 2008, chases idled early and slammed the door at the death. An up-slope. The
						powerplay ran {fmt2(rr.by_era['2008-10'].pp)} an over, the death {fmt2(rr.by_era['2008-10'].death)}.
						Leave the work late.
					</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						Now they front-load. The powerplay jumped to {fmt2(rr.headline.pp_2026)} an over, above the
						middle overs ({fmt2(rr.headline.mid_2026)}). Get ahead early, so the ask never spikes.
					</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>
						And teams get ahead of the rate earlier. Ahead at halfway: {pct0(rr.headline.ahead_2008)} in
						100, now {pct0(rr.headline.ahead_2026)}.
					</p>
				</div>
			{:else if step === 5}
				<div class="scene-card">
					<p>Belief five: pace the chase, get ahead early. Graded on the whole record: pass. The one belief the record actually backs.</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch8-required')}>ⓘ how we graded the chase</button>
				</div>
			{:else}
				<div class="scene-card">
					<p>
						One catch. This means the chase changed shape exactly as captains say. It does not mean
						chasing wins more. It still wins about half the time.
					</p>
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
		display: grid;
		place-items: center;
	}

	.pin.active {
		visibility: visible;
	}

	.stage {
		width: min(44rem, 92vw);
		display: grid;
		place-items: center;
	}

	.panel {
		width: min(34rem, 92vw);
		padding: 0.9rem 1rem;
		border-radius: 14px;
		background: rgba(10, 14, 24, 0.78);
		border: 1px solid rgba(151, 161, 184, 0.22);
	}

	.rchart {
		width: 100%;
		height: auto;
	}

	.grid {
		stroke: rgba(151, 161, 184, 0.16);
		stroke-width: 1;
	}

	.phase {
		font-size: 9px;
		fill: var(--ink-dim);
		text-anchor: middle;
	}

	.curve {
		fill: none;
		stroke-width: 2.6;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	.curve.old {
		stroke: #8fa2c4;
	}

	.curve.new {
		stroke: #e8a33d;
		filter: drop-shadow(0 0 4px rgba(232, 163, 61, 0.5));
	}

	.dot.old {
		fill: #8fa2c4;
	}

	.dot.new {
		fill: #e8a33d;
	}

	.era-tag {
		font-size: 10px;
		font-weight: 800;
	}

	.era-tag.old {
		fill: #a9b8d6;
	}

	.era-tag.new {
		fill: #f0b85c;
	}

	.caption-slot {
		position: absolute;
		right: 5vw;
		bottom: 8vh;
		max-width: min(22rem, 32vw);
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
		.caption-slot {
			position: absolute;
			right: auto;
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
