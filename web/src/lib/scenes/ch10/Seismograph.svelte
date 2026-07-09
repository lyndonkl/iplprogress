<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import RibbonField from './RibbonField.svelte';
	import SeismographStrip from './SeismographStrip.svelte';
	import { pickRibbonCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';
	import {
		loadCh10Data,
		defaultStopIndex,
		eraBands,
		isSureCrack,
		crackGlow,
		type Ch10Data,
		type Crack
	} from './data';

	/**
	 * C10-3, HERO: the Seismograph. The game did not break once, it broke in stages.
	 * The data cracks the ribbon at the seasons it changed, and the cracks are
	 * STAGGERED across a decade (sixes 2014 then 2018, wides 2022, scoring 2023,
	 * everything 2024). The strictness dial merges six eras down to two. Every crack
	 * sits at the exact emitted ball-position; its certainty rides two redundant
	 * honest channels (a soft glow whose intensity tracks how sure we are + a solid/
	 * dashed style), NEVER a brightened faint break; legibility is a separate always-
	 * visible neutral locator stroke with a dark halo + a direct year label in the
	 * tick-lane. The cracks + era-bands + dial are all scene-drawn SVG; the field
	 * draws no crack. The dial is a PRECOMPUTED lookup into scenes/ch10.json, never a
	 * live re-fit.
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

	const step = $derived(progress < 0.2 ? 1 : progress < 0.42 ? 2 : progress < 0.62 ? 3 : progress < 0.82 ? 4 : 5);
	const BOUNDS = [0, 0.2, 0.42, 0.62, 0.82, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const corner = $derived(pickRibbonCorner(field, 'br'));

	/* the strictness dial: a precomputed lookup. The reader may grab the slider
	   (manualIndex wins); otherwise the scripted scroll steps loose->strict through
	   the last two beats so the 6-to-2 merge lands for a one-thumb scroll. */
	let manualIndex = $state<number | null>(null);
	$effect(() => {
		if (!active) manualIndex = null;
	});

	const stops = $derived(ch10?.seismograph.strictness.stops ?? []);
	const idxDefault = $derived(ch10 ? defaultStopIndex(ch10) : 1);
	const idxLoose = $derived(0);
	const idxTwoEras = $derived(Math.max(0, stops.findIndex((s) => s.n_eras === 2)));

	const scriptIndex = $derived(step <= 3 ? idxDefault : step === 4 ? idxLoose : idxTwoEras);
	const dialIndex = $derived(reduced ? idxDefault : (manualIndex ?? scriptIndex));
	const stop = $derived(stops[dialIndex] ?? null);
	const nEras = $derived(stop?.n_eras ?? ch10?.seismograph.strictness.default_n_eras ?? 4);

	const showStrip = $derived(reduced || step >= 3);

	/* re-project the cracks + era-bands after each progress / dial / resize change */
	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => tick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	let raf = 0;
	$effect(() => {
		void progress;
		void dialIndex;
		cancelAnimationFrame(raf);
		raf = requestAnimationFrame(() => (tick += 1));
		return () => cancelAnimationFrame(raf);
	});

	interface DrawnCrack {
		year: number;
		x: number;
		topY: number;
		botY: number;
		labelY: number;
		glow: number;
		glowW: number;
		sure: boolean;
	}
	interface DrawnBand {
		x: number;
		w: number;
		topY: number;
		h: number;
		alt: boolean;
	}

	const geom = $derived.by(() => {
		void tick;
		const f = field;
		const d = ch10;
		const s = stop;
		if (!f || !d || !s) return null;
		const rib = f.getRibbonLayout();
		if (!rib) return null;
		const range = d.seismograph.posterior_range;
		const topPt = f.projectToCss(rib.box.left, rib.box.bandY + rib.box.bandHalf);
		const botPt = f.projectToCss(rib.box.left, rib.box.bandY - rib.box.bandHalf);
		const topY = Math.min(topPt.y, botPt.y);
		const botY = Math.max(topPt.y, botPt.y);
		const bh = botY - topY;

		const bands: DrawnBand[] = eraBands(s).map((b, i) => {
			const xLo = f.projectToCss(rib.pointToX(b.lo * (d.ribbon.total_points - 1)), rib.box.bandY).x;
			const xHi = f.projectToCss(rib.pointToX(b.hi * (d.ribbon.total_points - 1)), rib.box.bandY).x;
			return { x: Math.min(xLo, xHi), w: Math.abs(xHi - xLo), topY, h: bh, alt: i % 2 === 1 };
		});

		const cracks: DrawnCrack[] = (s.cracks as Crack[]).map((c) => {
			const x = f.projectToCss(rib.pointToX(c.ball_pos), rib.box.bandY).x;
			const t = range[1] > range[0] ? (c.posterior - range[0]) / (range[1] - range[0]) : 0.5;
			const sure = isSureCrack(c.posterior);
			const short = sure ? 0 : bh * 0.16;
			return {
				year: c.year,
				x,
				topY: topY + short,
				botY: botY - short,
				labelY: topY - 8,
				glow: crackGlow(c.posterior, range),
				glowW: 6 + 10 * (1 - Math.min(1, Math.max(0, t))),
				sure
			};
		});
		return { bands, cracks, topY, botY };
	});

	const seisLabels = $derived(ch10?.seismograph ?? null);
	const strongest = $derived(ch10?.seismograph.strictness.strongest_fault ?? null);
</script>

<div class="pin" class:active>
	<RibbonField {field} {progress} legend={true} faint={true} footnoteId="ch10-seismo" />

	{#if geom}
		<svg class="cracks" aria-hidden="true">
			<!-- the era-bands (the tinted regions BETWEEN cracks): an era is a visible region -->
			{#each geom.bands as b, i (i)}
				<rect
					class="band"
					class:alt={b.alt}
					x={b.x.toFixed(1)}
					y={b.topY.toFixed(1)}
					width={b.w.toFixed(1)}
					height={b.h.toFixed(1)}
				/>
			{/each}

			<!-- the cracks: glow (how sure) + halo/locator (legibility) + solid/dashed style -->
			{#each geom.cracks as c (c.year)}
				<!-- soft glow band: intensity = how sure, width = how unsure WHERE (never brightened) -->
				<line
					class="glow"
					x1={c.x.toFixed(1)}
					y1={c.topY.toFixed(1)}
					x2={c.x.toFixed(1)}
					y2={c.botY.toFixed(1)}
					stroke-width={c.glowW.toFixed(1)}
					opacity={c.glow.toFixed(3)}
				/>
				<!-- the dark halo, then the neutral locator: clears the detection floor, no certainty -->
				<line class="halo" x1={c.x.toFixed(1)} y1={c.topY.toFixed(1)} x2={c.x.toFixed(1)} y2={c.botY.toFixed(1)} />
				<line
					class="locator"
					class:dashed={!c.sure}
					x1={c.x.toFixed(1)}
					y1={c.topY.toFixed(1)}
					x2={c.x.toFixed(1)}
					y2={c.botY.toFixed(1)}
				/>
				<!-- the direct year label in the tick-lane above the band -->
				<text class="crack-year" x={c.x.toFixed(1)} y={c.labelY.toFixed(1)}>{c.year}</text>
			{/each}
		</svg>
	{/if}

	{#if seisLabels && showStrip}
		<div class="strip-wrap">
			<span class="strip-h">the pulse under the crack</span>
			<div class="strip-box">
				<SeismographStrip d={ch10!} />
			</div>
		</div>
	{/if}

	<!-- the strictness dial + the live "N eras" counter -->
	{#if ch10 && !reduced}
		<div class="dial">
			<label class="dial-label" for="strictness">how big a change counts as a new era</label>
			<input
				id="strictness"
				type="range"
				min="0"
				max={stops.length - 1}
				step="1"
				value={dialIndex}
				oninput={(e) => (manualIndex = Number((e.currentTarget as HTMLInputElement).value))}
			/>
			<span class="dial-count"><strong>{nEras}</strong> {nEras === 1 ? 'era' : 'eras'}</span>
		</div>
	{:else if ch10}
		<div class="dial reduced">
			<span class="dial-count"><strong>{nEras}</strong> eras</span>
			<span class="dial-note">{ch10.seismograph.strictness.endpoints_note}</span>
		</div>
	{/if}

	<div class="caption-slot" style="{cornerStyle(corner)}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>
					Here comes the machine's answer. Every vertical line marks a season the data thinks the game
					shifted. A solid bright crack is one it is surer of; a faint dashed one it is less sure of. And
					most are faint.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					And they do not line up. Sixes cracked way back in the mid-2010s, around 2014 and again 2018.
					Everything else is piled at the right edge. The game broke in stages, not all at once.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>You can see it in the pulse. Sixes climb, then step up hard. Runs an over sit flat for years, then jump at 2023. Each crack sits on a real step.</p>
			</div>
		{:else if step === 4}
			<div class="scene-card">
				<p>
					Now drag this. It sets how big a change has to be to count as a new era. The tinted bands are
					the eras. Loosen it and there are six. Tighten it and neighbouring bands fuse, all the way down
					to two.
				</p>
			</div>
		{:else}
			<div class="scene-card interactive">
				<p>
					That is the whole point. The modern game is not one new era. It is a stack of staggered ones,
					piled up since the mid-2010s. Squint hard and they collapse into the big one: {strongest?.year ?? 2023}.
				</p>
				<button class="fn" onclick={() => footnotesOpen.set('ch10-seismo')}>ⓘ where the game broke</button>
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

	.cracks {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: visible;
	}

	.band {
		fill: rgba(151, 161, 184, 0.04);
	}

	.band.alt {
		fill: rgba(46, 196, 182, 0.07);
	}

	.glow {
		stroke: var(--gold, #e8b84b);
		stroke-linecap: round;
	}

	.halo {
		stroke: #0b0e14;
		stroke-width: 3;
		opacity: 0.85;
		vector-effect: non-scaling-stroke;
	}

	.locator {
		stroke: rgba(232, 236, 245, 0.92);
		stroke-width: 1.2;
		vector-effect: non-scaling-stroke;
	}

	.locator.dashed {
		stroke-dasharray: 4 4;
		stroke: rgba(232, 236, 245, 0.7);
	}

	.crack-year {
		fill: var(--ink);
		font-size: 0.66rem;
		font-weight: 700;
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	.strip-wrap {
		position: absolute;
		left: 3vw;
		top: 12vh;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		width: min(28vw, 22rem);
	}

	.strip-h {
		font-size: 0.6rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.strip-box {
		height: 13rem;
		padding: 0.5rem 0.7rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.82);
		border: 1px solid rgba(151, 161, 184, 0.22);
	}

	.dial {
		position: absolute;
		left: 50%;
		transform: translateX(-50%);
		bottom: 3.5vh;
		display: flex;
		align-items: center;
		gap: 0.7rem;
		padding: 0.5rem 0.9rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.86);
		border: 1px solid rgba(151, 161, 184, 0.28);
		pointer-events: auto;
		max-width: 92vw;
	}

	.dial.reduced {
		flex-direction: column;
		align-items: flex-start;
		gap: 0.2rem;
	}

	.dial-label {
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.dial input {
		width: min(30vw, 16rem);
		accent-color: var(--teal);
		cursor: pointer;
	}

	.dial-count {
		font-size: 0.8rem;
		color: var(--ink);
		white-space: nowrap;
	}

	.dial-count strong {
		font-size: 1rem;
		color: var(--teal);
	}

	.dial-note {
		font-size: 0.68rem;
		color: var(--ink-dim);
	}

	.caption-slot {
		position: absolute;
		max-width: min(25rem, 40vw);
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
		.strip-wrap {
			left: 50%;
			transform: translateX(-50%);
			top: auto;
			bottom: 22vh;
			width: 88vw;
		}

		.strip-box {
			height: 10rem;
		}

		.dial {
			bottom: 12vh;
			flex-wrap: wrap;
			justify-content: center;
		}

		.dial input {
			width: 60vw;
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
