<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import {
		loadCh2Data,
		exemplarSeasons,
		fmt1,
		IPL_EARLY,
		IPL_MODERN,
		type Ch2Data,
		type ExemplarSeason,
		type WormExemplar
	} from './data';
	import { wormPolyline } from './wormsvg';

	/**
	 * C2-3 — The thinning (HERO #1: Anchor Extinction + the population decline).
	 * Worm-space HOLDS (the morph budget is spent). As the reader scrubs a season
	 * pointer 2008 → 2026, the par worm re-draws steeper and the season's K anchor
	 * exemplar worms thin from a small thicket to a survivor or two — a
	 * preattentive count change on the annotation plane, NOT a second morph. K is
	 * pinned to the emitted per-season anchor ball-share; the thicket is labelled
	 * illustrative ("a sample," never a headcount). The conservation chart (2D)
	 * carries the true magnitude — anchor share of every ball, 14.8% → 8.5% — and
	 * is drawn static + complete BEFORE the scrub (progressive disclosure). Main
	 * flow carries exactly ONE extinction number; the raw sub-120 cut is footnote-
	 * only (§7 must-fix #2).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.28) return 1;
		if (progress < 0.66) return 2;
		return 3;
	});

	let ch2 = $state<Ch2Data | null>(null);
	let narrow = $state(false);
	let tick = $state(0);
	onMount(() => {
		let alive = true;
		loadCh2Data().then((d) => {
			if (alive) ch2 = d;
		});
		const mql = window.matchMedia('(max-width: 640px)');
		const sync = (): void => {
			narrow = mql.matches;
		};
		sync();
		const onResize = (): void => {
			requestAnimationFrame(() => {
				tick++;
			});
		};
		mql.addEventListener('change', sync);
		window.addEventListener('resize', onResize);
		return () => {
			alive = false;
			mql.removeEventListener('change', sync);
			window.removeEventListener('resize', onResize);
		};
	});
	// force one recompute the moment the field handle first arrives
	let seeded = false;
	$effect(() => {
		if (field && !seeded) {
			seeded = true;
			tick++;
		}
	});

	/* the exemplar seasons + their pinned K thicket sizes */
	const es = $derived<ExemplarSeason[]>(ch2 ? exemplarSeasons(ch2) : []);

	/* season pointer: holds at the earliest through step 1, scrubs to the latest
	   across step 2, holds at the survivor-or-two through step 3 */
	const sweptIdx = $derived.by(() => {
		if (es.length === 0) return 0;
		const t = Math.min(1, Math.max(0, (progress - 0.26) / (0.62 - 0.26)));
		return Math.round(t * (es.length - 1));
	});
	const pointed = $derived<ExemplarSeason | null>(es.length ? es[sweptIdx] : null);

	/* field-registered thicket (motion): par worm + K anchor figure-channel worms */
	const thicket = $derived.by(() => {
		void tick;
		const f = field;
		if (!f || !pointed) return null;
		const par = wormPolyline(f, pointed.parWorm);
		const anchors = pointed.exemplars
			.slice(0, pointed.k)
			.map((e) => wormPolyline(f, e.cum_runs))
			.filter((s) => s.length > 0);
		return { par, anchors };
	});

	/* ---- the extinction numbers (single main-flow pair, from the artifact) --- */
	const shareEarly = $derived(ch2 ? ch2.anchor.bands[IPL_EARLY].anchor_ball_share_pct : null);
	const shareModern = $derived(ch2 ? ch2.anchor.bands[IPL_MODERN].anchor_ball_share_pct : null);

	/* ---- the conservation chart (2D, DOM/SVG, y zero-based, drawn static) ---- */
	const W = $derived(narrow ? 430 : 640);
	// narrower chart on mobile so the worm thicket keeps clear vertical space
	// above the card (§C2-3 mobile audit) — the thinning must not be buried
	const H = $derived(narrow ? 196 : 230);
	const ML = $derived(narrow ? 40 : 44);
	const MR = 18;
	const MT = 14;
	const MB = $derived(narrow ? 46 : 34);
	const FONT = $derived(narrow ? 17 : 11);
	const plotW = $derived(W - ML - MR);
	const plotH = $derived(H - MT - MB);
	const Y_MAX = 18; // zero-based, fixed; data max ≈ 15.4

	const seasonsIpl = $derived(ch2 ? ch2.anchor.seasons.ipl : []);
	const minYear = $derived(seasonsIpl.length ? seasonsIpl[0].season : 2008);
	const maxYear = $derived(seasonsIpl.length ? seasonsIpl[seasonsIpl.length - 1].season : 2026);
	const xAt = (year: number): number => ML + ((year - minYear) / Math.max(1, maxYear - minYear)) * plotW;
	const yAt = (pct: number): number => MT + (1 - Math.min(pct, Y_MAX) / Y_MAX) * plotH;
	const vc = $derived(FONT * 0.34);
	const tickLabY = $derived(narrow ? 26 : 18);

	const consLine = $derived(
		seasonsIpl.map((s) => `${xAt(s.season).toFixed(1)},${yAt(s.anchor_ball_share_pct).toFixed(1)}`).join(' ')
	);
	const yearTicks = [2008, 2014, 2020, 2026];

	/* the "last surviving anchors" of the final seasons — named from the emitted
	   worm exemplars, never hardcoded here (the magnitude claim rides THIS list) */
	const survivors = $derived<WormExemplar[]>(es.length ? es[es.length - 1].exemplars : []);
	const survivorYear = $derived(es.length ? es[es.length - 1].season : maxYear);
	let picked = $state<WormExemplar | null>(null);

	/* reduced-motion small-multiple: mini self-contained worm panels (2010 vs 2026) */
	const MINI = 150;
	const MAX_B = 60;
	const MAX_R = 90;
	function miniPoints(cum: number[]): string {
		return cum
			.map((r, i) => `${(6 + (Math.min(i + 1, MAX_B) / MAX_B) * (MINI - 12)).toFixed(1)},${(MINI - 6 - (Math.min(r, MAX_R) / MAX_R) * (MINI - 12)).toFixed(1)}`)
			.join(' ');
	}
	const firstSeason = $derived<ExemplarSeason | null>(es.length ? es[0] : null);
	const lastSeason = $derived<ExemplarSeason | null>(es.length ? es[es.length - 1] : null);
</script>

<div class="pin" class:reduced class:active>
	{#if !reduced && thicket}
		<!-- the season-swept thicket, registered to field coords over the haze.
		     Progressive disclosure (§C2-3 / §0.1): the thicket holds full through
		     the sweep (steps 1-2) and DIMS when the thesis chip lands (step 3), so
		     one locus changes per step by attenuation, not just by claim. -->
		<svg class="worm-plane" class:dimmed={step === 3} aria-hidden="true">
			{#if thicket.par}
				<polyline points={thicket.par} class="par" />
			{/if}
			{#each thicket.anchors as pts, i (i)}
				<polyline points={pts} class="anchor-casing" />
				<polyline points={pts} class="anchor-stroke" />
			{/each}
		</svg>
		{#if pointed}
			<div class="thicket-badge" class:dimmed={step === 3}>
				<span class="yr">{pointed.season}</span>
				<span class="note">a sample of that season's anchors</span>
			</div>
		{/if}
	{/if}

	<!-- reduced-motion small-multiple: 2008-era thicket beside the 2026 survivors -->
	{#if reduced && firstSeason && lastSeason}
		<div class="small-multiple">
			<figure class="mini">
				<figcaption>{firstSeason.season} — a sample of anchors</figcaption>
				<svg viewBox="0 0 {MINI} {MINI}" role="img" aria-label="{firstSeason.season} anchor innings, several slow rising lines">
					{#each firstSeason.exemplars.slice(0, firstSeason.k) as e (e.batter)}
						<polyline points={miniPoints(e.cum_runs)} class="mini-anchor" />
					{/each}
				</svg>
			</figure>
			<figure class="mini">
				<figcaption>{lastSeason.season} — a survivor or two</figcaption>
				<svg viewBox="0 0 {MINI} {MINI}" role="img" aria-label="{lastSeason.season} anchor innings, one or two slow rising lines">
					{#each lastSeason.exemplars.slice(0, lastSeason.k) as e (e.batter)}
						<polyline points={miniPoints(e.cum_runs)} class="mini-anchor" />
					{/each}
				</svg>
			</figure>
		</div>
	{/if}

	<!-- the conservation chart: population decline, static + complete. Drawn full
	     before the scrub (step 1) so only the worms move; DIMS while the thicket
	     sweeps (step 2) so the sweep is the one change; restored when the thesis
	     lands (step 3). Reduced motion keeps it static-legible (never dimmed). -->
	{#if ch2 && seasonsIpl.length}
		<div class="chart-slot" class:dimmed={!reduced && step === 2}>
			<figure class="chart" aria-label="Anchor share of every ball bowled, by season, {minYear} to {maxYear}, on a zero-based scale — {shareEarly !== null ? fmt1(shareEarly) : ''}% falling to {shareModern !== null ? fmt1(shareModern) : ''}%">
				<figcaption class="chart-title">Slow innings, share of every ball bowled</figcaption>
				<svg viewBox="0 0 {W} {H}" style="font-size:{FONT}px" role="img" aria-hidden="true">
					{#each [0, 6, 12, 18] as g (g)}
						<line x1={ML} x2={ML + plotW} y1={yAt(g)} y2={yAt(g)} class="grid" class:major={g === 0} />
						<text x={ML - 6} y={yAt(g) + vc} class="ylab">{g}%</text>
					{/each}
					{#each yearTicks as yr (yr)}
						<line x1={xAt(yr)} x2={xAt(yr)} y1={yAt(0)} y2={yAt(0) + 5} class="tickmark" />
						<text x={xAt(yr)} y={yAt(0) + tickLabY} class="xlab">{yr}</text>
					{/each}
					<polyline points={consLine} class="cons-line" />
					<!-- the last surviving anchors: fading dots on the final season -->
					<circle cx={xAt(survivorYear)} cy={yAt(shareModern ?? 0)} r="4.5" class="survivor-dot" />
				</svg>
				{#if survivors.length}
					<button class="survivors-tap" onclick={() => (picked = picked ? null : survivors[0])} aria-label="Name the last surviving anchors">
						the last surviving anchors →
					</button>
				{/if}
			</figure>
		</div>
	{/if}

	<!-- captions: one change per step; exactly ONE extinction number in flow -->
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>
					<strong>Every team once carried two or three.</strong> The anchor was doctrine — see off
					the new ball, bat till the end, let the others tee off.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Watch them thin out. Slow innings ate <strong>{shareEarly !== null ? fmt1(shareEarly) : '—'}% of every
						ball bowled</strong> in the league's earliest seasons; in the last four, just
					<strong>{shareModern !== null ? fmt1(shareModern) : '—'}%</strong> — a whole way of batting hunted
					toward the margins. By the final seasons its survivors are <strong>few enough to name.</strong>
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					A whole archetype, all but gone from the game — <strong>and the game is quicker and
						braver for its passing.</strong>
					<button class="dagger" onclick={() => footnotesOpen.set('anchor-extinction')} aria-label="How we counted the decline">ⓘ</button>
				</p>
			</div>
		{/if}
	</div>

	<!-- the last survivors: names on tap (adds names, never thesis) -->
	{#if picked && survivors.length}
		<div class="survivor-sheet" role="dialog" aria-label="The last surviving anchors, {survivorYear}">
			<div class="sheet-head">
				<p class="sheet-title">The last surviving anchors <span class="era">{survivorYear}</span></p>
				<button class="close" onclick={() => (picked = null)} aria-label="Close">×</button>
			</div>
			<ol>
				{#each survivors as s (s.batter)}
					<li>
						<strong>{s.batter}</strong> — {s.runs} off {s.balls}: strike rate {fmt1(s.sr)},
						well under the day's going rate of {fmt1(s.par_sr)}
					</li>
				{/each}
			</ol>
			<p class="baseline">Slow for their day — each one well below the going rate, few enough to name.</p>
		</div>
	{/if}
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

	.worm-plane {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		overflow: visible;
		pointer-events: none;
		transition: opacity 550ms ease;
	}

	/* progressive disclosure: dim the non-active locus per caption step */
	.worm-plane.dimmed,
	.thicket-badge.dimmed {
		opacity: 0.22;
	}

	.chart-slot {
		transition: opacity 550ms ease;
	}

	.chart-slot.dimmed {
		opacity: 0.34;
	}

	@media (prefers-reduced-motion: reduce) {
		.worm-plane,
		.chart-slot {
			transition: none;
		}
	}

	polyline {
		fill: none;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	.par {
		stroke: #8f9ab4;
		stroke-width: 2;
	}

	.anchor-casing {
		stroke: rgba(6, 9, 14, 0.92);
		stroke-width: 7;
	}

	.anchor-stroke {
		stroke: #ffd477;
		stroke-width: 2.4;
	}

	.thicket-badge {
		position: absolute;
		top: 5rem;
		left: 6vw;
		display: flex;
		align-items: baseline;
		gap: 0.5rem;
		font-variant-numeric: tabular-nums;
		transition: opacity 550ms ease;
	}

	.thicket-badge .yr {
		font-size: 1.5rem;
		font-weight: 800;
		color: var(--ink);
	}

	.thicket-badge .note {
		font-size: 0.72rem;
		color: var(--ink-dim);
		max-width: 10rem;
	}

	/* ---- reduced-motion small-multiple ---- */
	.small-multiple {
		position: absolute;
		top: 6vh;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		gap: 1rem;
	}

	.mini {
		margin: 0;
		text-align: center;
	}

	.mini figcaption {
		font-size: 0.72rem;
		color: var(--ink-dim);
		margin-bottom: 0.2rem;
	}

	.mini svg {
		width: min(38vw, 160px);
		height: auto;
		background: rgba(11, 14, 20, 0.6);
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 8px;
	}

	.mini-anchor {
		stroke: #ffd477;
		stroke-width: 2.4;
	}

	/* ---- conservation chart ---- */
	.chart-slot {
		position: absolute;
		right: 4vw;
		bottom: 8vh;
		width: min(660px, 92vw);
	}

	.chart {
		position: relative;
		margin: 0;
		padding: 0.5rem 0.6rem 0.2rem;
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 12px;
		background: rgba(11, 14, 20, 0.74);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
	}

	.chart-title {
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		color: var(--ink);
		padding: 0.1rem 0.3rem 0.35rem;
	}

	svg {
		display: block;
		width: 100%;
		height: auto;
	}

	.grid {
		stroke: rgba(232, 236, 245, 0.07);
		stroke-width: 1;
	}

	.grid.major {
		stroke: rgba(232, 236, 245, 0.16);
	}

	.tickmark {
		stroke: rgba(232, 236, 245, 0.3);
		stroke-width: 1;
	}

	.ylab,
	.xlab {
		fill: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.ylab {
		text-anchor: end;
	}

	.xlab {
		text-anchor: middle;
	}

	.cons-line {
		stroke: #ffd477;
		stroke-width: 2.6;
	}

	.survivor-dot {
		fill: #ffd477;
		stroke: rgba(6, 9, 14, 0.9);
		stroke-width: 1.5;
	}

	.survivors-tap {
		pointer-events: auto;
		display: inline-flex;
		align-items: center;
		min-height: 44px;
		margin: 0.1rem 0 0.2rem 0.3rem;
		padding: 0 0.2rem;
		border: none;
		background: none;
		color: var(--gold);
		font: inherit;
		font-size: 0.8rem;
		cursor: pointer;
	}

	.survivors-tap:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* ---- captions ---- */
	.caption-slot {
		position: absolute;
		left: 6vw;
		bottom: 12vh;
		max-width: min(28rem, 84vw);
	}

	.dagger {
		pointer-events: auto;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 44px;
		min-height: 44px;
		margin: -10px 0;
		padding: 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 1rem;
		cursor: pointer;
	}

	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* ---- survivors sheet ---- */
	.survivor-sheet {
		pointer-events: auto;
		position: absolute;
		left: 50%;
		bottom: max(72px, calc(env(safe-area-inset-bottom) + 60px));
		transform: translateX(-50%);
		width: min(560px, 94vw);
		padding: 0.9rem 1.1rem 1rem;
		border-radius: 14px;
		border: 1px solid rgba(232, 236, 245, 0.16);
		background: rgba(11, 14, 20, 0.95);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		font-variant-numeric: tabular-nums;
		z-index: 5;
	}

	.sheet-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.5rem;
	}

	.sheet-title {
		margin: 0;
		font-size: 0.95rem;
		font-weight: 700;
	}

	.sheet-title .era {
		font-weight: 500;
		font-size: 0.75rem;
		color: var(--ink-dim);
		margin-left: 0.4rem;
		letter-spacing: 0.06em;
	}

	.close {
		flex: none;
		min-width: 44px;
		min-height: 44px;
		border: none;
		border-radius: 10px;
		background: rgba(232, 236, 245, 0.06);
		color: var(--ink);
		font-size: 1.3rem;
		cursor: pointer;
	}

	.close:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	ol {
		margin: 0.5rem 0 0;
		padding-left: 1.2rem;
	}

	li {
		margin: 0.3rem 0;
		font-size: 0.86rem;
		line-height: 1.45;
		color: var(--ink);
	}

	.baseline {
		margin: 0.55rem 0 0;
		font-size: 0.78rem;
		color: var(--ink-dim);
	}

	@media (max-width: 640px) {
		.chart-slot {
			right: 50%;
			transform: translateX(50%);
			bottom: 4vh;
			width: 94vw;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(38vh, calc(env(safe-area-inset-bottom) + 34vh));
		}

		.thicket-badge {
			top: 4rem;
			left: 4vw;
		}
	}
</style>
