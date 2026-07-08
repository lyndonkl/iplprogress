<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import MatchField from './MatchField.svelte';
	import ReportCardRail from './ReportCardRail.svelte';
	import { panelCaptionStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh8Data, type Ch8Data, type ClaimRow } from './data';

	/**
	 * C8-6, SUPPORTING, Belief 4: momentum (FAIL, with an honest small real part).
	 * REDESIGN (owner review): the permutation-null histogram was unreadable to a
	 * cricket fan, and the same-batter shuffle barely moved the band (1.078 -> 1.087),
	 * so the "hold the batter fixed and it vanishes" story was both opaque AND wrong.
	 * The real deflator is the SITUATION (boundaries bunch in good conditions), not
	 * batter quality, and about HALF the apparent effect survives as real. So the beat
	 * is now a SPLIT BAR: the apparent effect decomposed into "the situation" (what a
	 * random shuffle of the same balls still produces) and "real" (what survives the
	 * shuffle). Wickets have no real part, only a small dip (the collapse is a myth).
	 * The same-batter control is demoted to the footnote. One bar, read at a glance.
	 */
	const VB_W = 420;
	const VB_H = 128;
	const PL = 18;
	const PR = 18;
	const PT = 44;
	const PB = 34;
	const ERA = '2023-26';

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
		progress < 0.22 ? 1 : progress < 0.42 ? 2 : progress < 0.62 ? 3 : progress < 0.82 ? 4 : 5
	);
	const BOUNDS = [0, 0.22, 0.42, 0.62, 0.82, 1] as const;
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

	const mo = $derived(ch8?.momentum ?? null);

	/* step 1 audits the collapse (wicket myth); steps 2-5 audit the hot streak
	   (hitting). A menu pick overrides the scripted claim (optional exploration). */
	let pickedClaim = $state<string | null>(null);
	const scriptedClaim = $derived(step <= 1 ? mo?.scripted.wicket_myth : mo?.scripted.hitting_sliver);
	const activeClaim = $derived(pickedClaim ?? scriptedClaim ?? 'bnd|bnd');
	const row = $derived<ClaimRow | null>(
		mo?.claims_by_era[ERA]?.find((r) => r.claim === activeClaim) ?? null
	);
	/* the split (situation vs real) reveals in the scripted flow at step 3; a menu
	   pick shows the full decomposition straight away. */
	const showSplit = $derived(pickedClaim != null || step >= 3);

	const chart = $derived.by(() => {
		void tick;
		const r = row;
		if (!r) return null;
		const apparent = (r.lift - 1) * 100; // percentage points, e.g. +15.9 or -7.0
		// the strictest shuffle we have (same match + over + batter), else the plain one
		const nul = r.batter_null ?? r.plain_null;
		const bandHi = nul.band[1];
		const explained = (nul.mean_lift - 1) * 100; // what the shuffle alone produces
		const outside = r.lift > bandHi; // clears the shuffle -> a real part exists
		const negative = apparent < -0.6;
		const realRaw = apparent - explained;
		const real = outside ? Math.max(0, realRaw) : 0;
		const situation = apparent - real; // the rest: conditions + chance
		// axis: fit 0, the apparent value, and a little headroom (per-claim adaptive)
		const lo = Math.min(-8, apparent - 3);
		const hi = Math.max(apparent + 4, 13);
		const plotL = PL;
		const plotR = VB_W - PR;
		const xS = (v: number): number => plotL + ((v - lo) / (hi - lo)) * (plotR - plotL);
		const barY = PT + 6;
		const barH = 30;
		return {
			apparent,
			apparentPct: Math.round(apparent),
			saferPct: Math.round(-apparent),
			sitPct: Math.round(Math.max(0, situation)),
			realPct: Math.round(real),
			outside,
			negative,
			zeroX: xS(0),
			sitX0: xS(0),
			sitX1: xS(Math.max(0, situation)),
			realX1: xS(apparent),
			negX0: xS(apparent),
			negX1: xS(0),
			barY,
			barH,
			plotL,
			plotR
		};
	});

	const capStyle = $derived.by(() => {
		void tick;
		void step;
		if (isNarrowViewport()) return '';
		return panelCaptionStyle(panel);
	});

	const stamped = $derived(reduced || step >= 5 ? 4 : 3);

	function pick(claim: string): void {
		pickedClaim = claim;
	}
</script>

<div class="pin" class:active>
	<MatchField {field} {reduced} {progress} faint={true} legend={false} footnoteId="ch8-momentum" />
	<ReportCardRail report={ch8?.report_card ?? null} {stamped} />

	<div class="stage">
		<div class="panel" bind:this={panel}>
			{#if chart && row}
				<div class="panel-head">
					<span class="claim-name">{row.fan.split('(')[0].trim()}</span>
					<span class="claim-sub">{row.fan.includes('(') ? row.fan.split('(')[1].replace(')', '') : ''}</span>
				</div>
				<svg viewBox="0 0 {VB_W} {VB_H}" class="mchart" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
					<!-- baseline at 0 (no effect) -->
					<line class="zero" x1={chart.zeroX} x2={chart.zeroX} y1={chart.barY - 12} y2={chart.barY + chart.barH + 6} />
					<text class="zero-lbl" x={chart.zeroX} y={chart.barY + chart.barH + 20}>no change</text>

					{#if chart.negative}
						<!-- the wicket dip: after a wicket, the next ball is SAFER (a myth, no collapse) -->
						<rect class="dip" x={chart.negX0} y={chart.barY} width={Math.max(1, chart.negX1 - chart.negX0)} height={chart.barH} />
						<text class="seg-lbl dip-lbl" x={(chart.negX0 + chart.negX1) / 2} y={chart.barY - 6}>
							{chart.saferPct}% safer. no collapse.
						</text>
					{:else}
						<!-- the situation part (grey): what a random shuffle of the same balls still gives -->
						<rect class="situation" x={chart.sitX0} y={chart.barY} width={Math.max(0.5, chart.sitX1 - chart.sitX0)} height={chart.barH} />
						{#if showSplit && chart.outside && chart.realPct > 0}
							<!-- the real part (green): what survives the shuffle -->
							<rect class="real" x={chart.sitX1} y={chart.barY} width={Math.max(0.5, chart.realX1 - chart.sitX1)} height={chart.barH} />
							<text class="seg-lbl sit-lbl" x={(chart.sitX0 + chart.sitX1) / 2} y={chart.barY - 6}>the situation ~{chart.sitPct}</text>
							<text class="seg-lbl real-lbl" x={(chart.sitX1 + chart.realX1) / 2} y={chart.barY - 6}>real ~{chart.realPct}</text>
						{:else}
							<!-- pre-split (step 2) or no real part: one bar, its size = the apparent effect -->
							<rect class="apparent" x={chart.sitX0} y={chart.barY} width={Math.max(0.5, chart.realX1 - chart.sitX0)} height={chart.barH} />
							<text class="seg-lbl app-lbl" x={(chart.sitX0 + chart.realX1) / 2} y={chart.barY - 6}>
								{chart.apparentPct}% more often
							</text>
						{/if}
					{/if}
				</svg>
				<!-- the claim menu (optional depth) -->
				<div class="menu">
					{#each mo?.menu ?? [] as m (m.claim)}
						<button class="mbtn" class:on={activeClaim === m.claim} onclick={() => pick(m.claim)}>
							{m.fan.split('(')[0].trim()}
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if mo && chart}
			{#if step === 1}
				<div class="scene-card">
					<p>
						First belief: the collapse. One wicket brings the next. But the data says the opposite.
						After a wicket falls, the next ball is about {chart.saferPct}% <strong>safer</strong>, not
						more dangerous. There is no streak here at all. The famous collapse is a myth.
					</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>
						Now the other belief: the hot streak. Hitting begets hitting. And at first glance this one
						looks real. After a boundary, boundaries come about {chart.apparentPct}% more often.
					</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						But boundaries bunch in good conditions. A flat pitch, the powerplay, a bowler getting
						carted. They cluster whether or not the last ball was a four. Shuffle every ball into a
						random order and about {chart.sitPct} of those {chart.apparentPct} points are still there.
						That grey part is just the situation, not the shot.
					</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>
						What is left, the green part, is the real thing: about {chart.realPct} extra boundaries in
						every 100 that the situation cannot explain. A genuine ball-to-ball nudge, and it has held
						steady across the eras. Momentum is real for hitting. Just a nudge, not the avalanche the
						commentary sells.
					</p>
				</div>
			{:else}
				<div class="scene-card">
					<p>
						Belief four: momentum. Graded on the whole record: mostly a feeling. The collapse is a
						myth. The hot streak is real, but small.
					</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch8-momentum')}>ⓘ how we graded momentum</button>
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
		width: min(46rem, 92vw);
		display: grid;
		place-items: center;
	}

	.panel {
		width: min(34rem, 92vw);
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		padding: 0.9rem 1rem;
		border-radius: 14px;
		background: rgba(10, 14, 24, 0.78);
		border: 1px solid rgba(151, 161, 184, 0.22);
	}

	.panel-head {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
	}

	.claim-name {
		font-size: 0.9rem;
		font-weight: 700;
		color: var(--ink);
	}

	.claim-sub {
		font-size: 0.68rem;
		color: var(--ink-dim);
		font-style: italic;
	}

	.mchart {
		width: 100%;
		height: auto;
	}

	.zero {
		stroke: var(--ink-dim);
		stroke-width: 1;
		stroke-dasharray: 3 3;
	}

	.zero-lbl {
		font-size: 8px;
		fill: var(--ink-dim);
		text-anchor: middle;
	}

	.situation {
		fill: rgba(151, 161, 184, 0.45);
	}

	.apparent {
		fill: rgba(232, 163, 61, 0.55);
	}

	.real {
		fill: #6fcf97;
	}

	.dip {
		fill: rgba(91, 140, 255, 0.5);
	}

	.seg-lbl {
		font-size: 9px;
		text-anchor: middle;
		font-weight: 700;
	}

	.sit-lbl {
		fill: var(--ink-dim);
	}

	.real-lbl {
		fill: #cde7d8;
	}

	.app-lbl {
		fill: #f0cf9a;
	}

	.dip-lbl {
		fill: #b9ccff;
	}

	.menu {
		display: flex;
		flex-wrap: wrap;
		gap: 0.3rem;
		margin-top: 0.3rem;
	}

	.mbtn {
		font-size: 0.62rem;
		padding: 0.2rem 0.45rem;
		border-radius: 6px;
		border: 1px solid rgba(151, 161, 184, 0.25);
		background: rgba(151, 161, 184, 0.08);
		color: var(--ink-dim);
		cursor: pointer;
		min-height: 32px;
	}

	.mbtn.on {
		color: var(--ink);
		border-color: var(--teal);
	}

	.mbtn:focus-visible,
	.fn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
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

	@media (max-width: 640px) {
		.caption-slot {
			position: absolute;
			left: 50%;
			right: auto;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
