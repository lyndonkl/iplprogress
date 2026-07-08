<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import MatchField from './MatchField.svelte';
	import ReportCardRail from './ReportCardRail.svelte';
	import { panelCaptionStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh8Data, pct0, type Ch8Data, type ClaimRow, type ShuffleNull } from './data';

	/**
	 * C8-6, SUPPORTING, Belief 4: momentum (FAIL with an honest residual). The dots
	 * dim to a backdrop; the scene is the momentum audit panel: a claim's observed
	 * value drawn as a NEEDLE over the HISTOGRAM of the same claim measured on
	 * shuffled cricket. The cloud's mass is an explicit shaded BAND, a "no effect"
	 * line sits at 1.0 with "more likely" / "less likely" direction labels, and the
	 * needle is GREEN outside the band, GREY inside (so "outside" is a categorical
	 * read, never a fine eyeball). The two shuffles are never overlaid: the panel
	 * SWAPS the plain band for the same-batter band. The honest residual is drawn as
	 * a labelled band-edge-to-needle bracket ("the real part, about 7 in 100") and
	 * it HELD STEADY season after season (the raw edge fades, the real part does not).
	 * Rendered once per state (no rAF loop). ONE distribution on screen at a time.
	 */
	const VB_W = 400;
	const VB_H = 200;
	const PL = 34;
	const PR = 18;
	const PT = 30;
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
		progress < 0.2
			? 1
			: progress < 0.38
				? 2
				: progress < 0.56
					? 3
					: progress < 0.72
						? 4
						: progress < 0.87
							? 5
							: 6
	);
	const BOUNDS = [0, 0.2, 0.38, 0.56, 0.72, 0.87, 1] as const;
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

	/* the scripted claim + null mode by step (menu picks override the claim). Steps 1-2
	   hold the wicket myth (plain), step 3 the hitting raw (plain), steps 4-6 the same-
	   batter residual. Only ONE null (band) is ever on screen, never overlaid. */
	let pickedClaim = $state<string | null>(null);
	let userBatter = $state(false);
	const scriptedClaim = $derived(step <= 2 ? mo?.scripted.wicket_myth : mo?.scripted.hitting_sliver);
	const scriptedBatter = $derived(step >= 4);

	const activeClaim = $derived(pickedClaim ?? scriptedClaim ?? 'bnd|bnd');
	const row = $derived<ClaimRow | null>(
		mo?.claims_by_era[ERA]?.find((r) => r.claim === activeClaim) ?? null
	);
	const wantBatter = $derived(pickedClaim ? userBatter : scriptedBatter);
	const useBatter = $derived(wantBatter && !!row?.batter_null);
	const nul = $derived<ShuffleNull | null>((useBatter ? row?.batter_null : row?.plain_null) ?? null);

	const chart = $derived.by(() => {
		void tick;
		const r = row;
		const nl = nul;
		if (!r || !nl) return null;
		const lift = r.lift;
		const bandLo = nl.band[0];
		const bandHi = nl.band[1];
		const xLo = Math.min(r.hist.lo, bandLo, lift, 1.0) - 0.01;
		const xHi = Math.max(r.hist.hi, bandHi, lift, 1.0) + 0.01;
		const plotL = PL;
		const plotR = VB_W - PR;
		const plotT = PT;
		const plotB = VB_H - PB;
		const xS = (v: number): number => plotL + ((v - xLo) / (xHi - xLo)) * (plotR - plotL);
		const binW = (r.hist.hi - r.hist.lo) / r.hist.nbins;
		let maxC = 1;
		for (const c of nl.counts) if (c > maxC) maxC = c;
		const bars = nl.counts.map((c, i) => {
			const x0 = xS(r.hist.lo + i * binW);
			const x1 = xS(r.hist.lo + (i + 1) * binW);
			const h = (c / maxC) * (plotB - plotT);
			return { x: x0, w: Math.max(0.5, x1 - x0 - 0.5), y: plotB - h, h };
		});
		const outside = lift < bandLo || lift > bandHi;
		const resid = r.batter_null?.residual ?? null;
		return {
			plotL,
			plotR,
			plotT,
			plotB,
			bandX: xS(bandLo),
			bandW: xS(bandHi) - xS(bandLo),
			bandHiX: xS(bandHi),
			bandLoX: xS(bandLo),
			zeroX: xS(1.0),
			needleX: xS(lift),
			bars,
			outside,
			lift,
			resid,
			residPct: resid != null ? pct0((resid - 1) * 100) : null
		};
	});

	const capStyle = $derived.by(() => {
		void tick;
		void step;
		if (isNarrowViewport()) return '';
		return panelCaptionStyle(panel);
	});

	const stamped = $derived(reduced || step >= 6 ? 4 : 3);

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
					<span class="claim-name">{row.fan}</span>
					<span class="null-name">{useBatter ? 'the same batter, reshuffled' : 'shuffled cricket'}</span>
				</div>
				<svg viewBox="0 0 {VB_W} {VB_H}" class="mchart" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
					<!-- the shaded band: the mass of shuffled cricket -->
					<rect class="band" x={chart.bandX} y={chart.plotT} width={chart.bandW} height={chart.plotB - chart.plotT} />
					<!-- the histogram of the shuffle -->
					{#each chart.bars as b, i (i)}
						<rect class="hbar" x={b.x} y={b.y} width={b.w} height={b.h} />
					{/each}
					<!-- the no-effect line at 1.0 -->
					<line class="zero" x1={chart.zeroX} x2={chart.zeroX} y1={chart.plotT - 6} y2={chart.plotB} />
					<text class="dir left" x={chart.zeroX - 6} y={chart.plotT - 12}>&lt; less likely</text>
					<text class="dir right" x={chart.zeroX + 6} y={chart.plotT - 12}>more likely &gt;</text>
					<!-- the residual bracket (same-batter mode): band edge to needle -->
					{#if useBatter && chart.residPct != null}
						<line class="brk" x1={chart.bandHiX} x2={chart.needleX} y1={chart.plotT + 10} y2={chart.plotT + 10} />
						<line class="brk" x1={chart.bandHiX} x2={chart.bandHiX} y1={chart.plotT + 6} y2={chart.plotT + 14} />
						<line class="brk" x1={chart.needleX} x2={chart.needleX} y1={chart.plotT + 6} y2={chart.plotT + 14} />
						<text class="brk-lbl" x={(chart.bandHiX + chart.needleX) / 2} y={chart.plotT + 4}>
							the real part, about {chart.residPct} in 100
						</text>
					{/if}
					<!-- the needle: green outside the band, grey inside -->
					<line
						class="needle"
						class:green={chart.outside}
						x1={chart.needleX}
						x2={chart.needleX}
						y1={chart.plotT - 4}
						y2={chart.plotB}
					/>
					<polygon
						class="needle-head"
						class:green={chart.outside}
						points="{chart.needleX - 5},{chart.plotT - 10} {chart.needleX + 5},{chart.plotT - 10} {chart.needleX},{chart.plotT - 2}"
					/>
				</svg>
				<!-- the claim menu (optional depth) -->
				<div class="menu">
					{#each mo?.menu ?? [] as m (m.claim)}
						<button class="mbtn" class:on={activeClaim === m.claim} onclick={() => pick(m.claim)}>
							{m.fan.split('(')[0].trim()}
						</button>
					{/each}
				</div>
				{#if pickedClaim && row.batter_null}
					<button class="swap" onclick={() => (userBatter = !userBatter)}>
						{useBatter ? 'Show plain shuffled cricket' : 'Hold the same batter fixed'}
					</button>
				{/if}
			{/if}
		</div>
	</div>

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if mo}
			{#if step === 1}
				<div class="scene-card">
					<p>
						Every commentator swears by momentum. So let us test it. The tall needle is what really
						happens on the field. The grey band behind it is those same balls shuffled into a random
						order, hundreds of times over, so it shows what pure luck would look like. If a belief is
						real, the needle breaks clear of the band. If it is just a feeling, it sits inside.
					</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>
						First belief: one wicket brings another. The dreaded collapse. But the needle sits dead
						inside the grey. After a wicket falls, the next ball is no likelier to take one than any
						other ball. The collapse is a story we tell, not a thing the data does.
					</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						Second belief: hitting begets hitting. Middle a boundary and the next comes easier. And
						here the needle does break clear of the grey. At first glance, this one looks real.
					</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>
						But watch. Freeze it to one batter and shuffle only his own balls. Nearly all of the edge
						vanishes. The boundaries came in a bunch because a good batter was in and set, not because
						one shot fed the next. Kohli middles three fours in an over because he is Kohli, not
						because the over had momentum.
					</p>
				</div>
			{:else if step === 5}
				<div class="scene-card">
					<p>
						A thin sliver is left, and it is real: about {chart?.residPct ?? 7} more boundaries in
						every 100 than pure luck alone. And it has held steady, era after era. That sliver is the
						only true momentum in the game. The rest was a good batter batting.
					</p>
				</div>
			{:else}
				<div class="scene-card">
					<p>
						Belief four: momentum. Graded on the whole record: mostly a feeling. The collapse is a
						myth. The hot streak is nearly all just a good batter in form, with a sliver of something
						real underneath.
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
		justify-content: space-between;
		align-items: baseline;
		gap: 0.6rem;
	}

	.claim-name {
		font-size: 0.86rem;
		font-weight: 700;
		color: var(--ink);
	}

	.null-name {
		font-size: 0.66rem;
		color: var(--ink-dim);
		font-style: italic;
	}

	.mchart {
		width: 100%;
		height: auto;
	}

	.band {
		fill: rgba(151, 161, 184, 0.2);
	}

	.hbar {
		fill: rgba(151, 161, 184, 0.5);
	}

	.zero {
		stroke: var(--ink-dim);
		stroke-width: 1;
		stroke-dasharray: 3 3;
	}

	.dir {
		font-size: 8px;
		fill: var(--ink-dim);
	}

	.dir.left {
		text-anchor: end;
	}

	.dir.right {
		text-anchor: start;
	}

	.needle {
		stroke: #97a1b8;
		stroke-width: 2.4;
	}

	.needle.green {
		stroke: #6fcf97;
	}

	.needle-head {
		fill: #97a1b8;
	}

	.needle-head.green {
		fill: #6fcf97;
	}

	.brk {
		stroke: #6fcf97;
		stroke-width: 1.2;
	}

	.brk-lbl {
		font-size: 8px;
		fill: #cde7d8;
		text-anchor: middle;
		font-weight: 700;
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

	.swap {
		align-self: flex-start;
		min-height: 36px;
		padding: 0.2rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.72rem;
		font-weight: 600;
		cursor: pointer;
	}

	.mbtn:focus-visible,
	.swap:focus-visible,
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
