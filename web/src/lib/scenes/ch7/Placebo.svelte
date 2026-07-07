<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { panelCaptionStyle, isNarrowViewport } from './captionCorner.svelte';
	import {
		loadCh7Data,
		ensureRiverTable,
		fmt2,
		candidateFor,
		isPlacebo,
		type Ch7Data
	} from './data';

	/**
	 * C7-5 — SUPPORTING 2 + the CHAPTER SIGNATURE INTERACTIVE: the Rule-Change
	 * Event Study with the Placebo Cursor. Drag the "if the rule had come in…" date
	 * anywhere along the timeline and the jump estimate re-reads from the
	 * precomputed grid (a LOOKUP, never a live fit — blueprint standing rule). Every
	 * date before the rule (the grey placebo cloud, 2012–2022) produces a jump of at
	 * most 1.19 runs an over; the real 2023 rule date jumps 1.36 and clears the whole
	 * cloud. Honest disclosure on screen: 2024's raw size edges it, because teams
	 * kept learning the card — the break brackets 2023–24, and 2023 is its leading
	 * edge. On screen it leads plainly ("the jump", "a fake date"); "difference-in-
	 * differences" and the t-statistic live one click deep (glossary rule).
	 *
	 * FALLBACK (reduced motion / no interaction): the cursor rests on the true 2023
	 * date with the placebo cloud drawn statically around it — the point lands with
	 * zero dragging. Interaction adds depth, never carries the thesis.
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

	/* keep the dim river backdrop alive on a deep link into this beat */
	$effect(() => {
		if (field && ch7) ensureRiverTable(field, ch7);
	});

	const es = $derived(ch7?.event_study ?? null);

	/* three caption steps carry the point for the thumb that only scrolls (guardrail
	   4 / audit should-fix #9): orient the drag, sweep the flat pre-rule cloud, snap
	   to the rule year. */
	const step = $derived(progress < 0.33 ? 1 : progress < 0.62 ? 2 : 3);
	const BOUNDS = [0, 0.33, 0.62, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	/* the reader's chosen "what if the rule came in this year" date. A SCRIPTED scroll
	   path drives the marker for the ~85% who never drag (and reduced motion rests it
	   on the true date): early years → a sweep across the pre-rule cloud → a snap to
	   2023 in the clear gap. The moment the reader drags or keys, they take over
	   (userControlled) and the script lets go. candidates span 2012..2025. */
	let selected = $state(2023);
	let userControlled = $state(false);
	const scriptedSeason = $derived.by(() => {
		if (!es) return 2023;
		if (reduced) return es.true_date; // reduced motion: park on 2023, no sweep
		const p = progress;
		if (p < 0.33) return 2014; // step 1: an early made-up date
		if (p < 0.62) return Math.round(2014 + ((p - 0.33) / (0.62 - 0.33)) * (2022 - 2014));
		return es.true_date; // step 3: snap to the rule year in the clear gap
	});
	$effect(() => {
		if (userControlled || !es) return;
		selected = scriptedSeason; // the scripted path drives the marker until a drag
	});

	const cand = $derived(es ? candidateFor(es, selected) : null);
	const placebo = $derived(es ? isPlacebo(es, selected) : false);
	const isTrue = $derived(es ? selected === es.true_date : false);

	/* ---- SVG scales (a pure 2D exhibit; not registered to the field) --------- */
	const VB = { w: 360, h: 240, l: 44, r: 20, t: 24, b: 40 };
	const X0 = 2012;
	const X1 = 2025;
	const YMAX = 1.6;
	const xTo = (s: number): number => VB.l + ((s - X0) / (X1 - X0)) * (VB.w - VB.l - VB.r);
	const yTo = (v: number): number => VB.h - VB.b - (v / YMAX) * (VB.h - VB.t - VB.b);

	interface Dot {
		season: number;
		x: number;
		y: number;
		shift: number;
		placebo: boolean;
		treat: boolean;
		isTrue: boolean;
	}
	const dots = $derived.by<Dot[]>(() => {
		if (!es) return [];
		return es.candidates.map((c) => ({
			season: c.season,
			x: xTo(c.season),
			y: yTo(c.level_shift),
			shift: c.level_shift,
			placebo: isPlacebo(es, c.season),
			treat: c.season >= es.treatment_window[0],
			isTrue: c.season === es.true_date
		}));
	});

	const cloudMaxY = $derived(es ? yTo(es.placebo_cloud_max_shift) : 0);
	const cursorX = $derived(xTo(selected));

	/* ---- interaction: pointer drag on the plot + a keyboard slider ----------- */
	let svgEl = $state<SVGSVGElement | null>(null);
	let dragging = false;

	function seasonFromClientX(clientX: number): number {
		if (!svgEl || !es) return selected;
		const rect = svgEl.getBoundingClientRect();
		const frac = (clientX - rect.left) / rect.width; // 0..1 across the SVG width
		const sx = X0 + frac * (X1 - X0);
		// snap to the nearest candidate season we actually have a lookup for
		let best = es.candidates[0].season;
		let bestD = Infinity;
		for (const c of es.candidates) {
			const dd = Math.abs(c.season - sx);
			if (dd < bestD) {
				bestD = dd;
				best = c.season;
			}
		}
		return best;
	}

	function onPointerDown(ev: PointerEvent): void {
		dragging = true;
		userControlled = true; // the reader takes over; the scripted sweep lets go
		(ev.currentTarget as SVGSVGElement).setPointerCapture(ev.pointerId);
		selected = seasonFromClientX(ev.clientX);
	}
	function onPointerMove(ev: PointerEvent): void {
		if (!dragging) return;
		selected = seasonFromClientX(ev.clientX);
	}
	function onPointerUp(ev: PointerEvent): void {
		dragging = false;
		try {
			(ev.currentTarget as SVGSVGElement).releasePointerCapture(ev.pointerId);
		} catch {
			/* capture may already be released */
		}
	}

	const announce = $derived.by(() => {
		if (!es || !cand) return '';
		if (isTrue)
			return `The real rule date, ${selected}. Scoring jumped ${fmt2(cand.level_shift)} runs an over, clearing every date before the rule.`;
		if (placebo)
			return `A made-up date, ${selected}. The jump here is only ${fmt2(cand.level_shift)} runs an over.`;
		return `${selected}, after the rule. The jump is ${fmt2(cand.level_shift)} runs an over.`;
	});

	/* §0.4a caption placement for a CENTRED panel: derive the safe slot from the live
	   panel rect so the caption never covers the exhibit (audit should-fix #10).
	   Mobile uses the bottom read-then-watch slot (isNarrowViewport → CSS default). */
	let panelEl = $state<HTMLElement | null>(null);
	let capTick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => capTick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	const capStyle = $derived.by(() => {
		void capTick;
		void progress;
		if (isNarrowViewport() || !panelEl) return '';
		return panelCaptionStyle(panelEl);
	});
</script>

<div class="pin" class:active>
	{#if es}
		<div class="panel" bind:this={panelEl}>
			<p class="overline">the fake-date test · drag the rule date</p>

			<!-- the live readout: the jump for the selected date -->
			<div class="readout" class:true={isTrue} class:placebo aria-hidden="true">
				<div class="ro-year">{selected}</div>
				<div class="ro-jump">
					<span class="ro-big">{cand ? fmt2(cand.level_shift) : '–'}</span>
					<span class="ro-unit">runs an over jump</span>
				</div>
			</div>
			<p class="ro-tag" class:true={isTrue} class:placebo>
				{#if isTrue}
					The real rule date. It clears every date in grey.
				{:else if placebo}
					A made-up date. The jump stays small.
				{:else}
					After the rule. The break kept deepening as teams learned the card.
				{/if}
			</p>
			<p class="lookup">a lookup, not a guess · every year worked out ahead of time</p>

			<!-- the event-study chart -->
			<svg
				bind:this={svgEl}
				class="chart"
				class:reduced
				viewBox="0 0 {VB.w} {VB.h}"
				role="img"
				aria-label="Jump in runs an over for each possible rule date, 2012 to 2025"
				onpointerdown={reduced ? undefined : onPointerDown}
				onpointermove={reduced ? undefined : onPointerMove}
				onpointerup={reduced ? undefined : onPointerUp}
			>
				<!-- placebo region (grey) + treatment region (gold), behind the dots -->
				<rect
					class="zone placebo"
					x={xTo(es.placebo_window[0]) - 8}
					y={VB.t}
					width={xTo(es.placebo_window[1]) - xTo(es.placebo_window[0]) + 16}
					height={VB.h - VB.b - VB.t}
				/>
				<rect
					class="zone treat"
					x={xTo(es.treatment_window[0]) - 8}
					y={VB.t}
					width={xTo(2025) - xTo(es.treatment_window[0]) + 16}
					height={VB.h - VB.b - VB.t}
				/>

				<!-- "the most a fake date jumps" reference line across the placebo years -->
				<line
					class="cloudline"
					x1={xTo(es.placebo_window[0]) - 8}
					y1={cloudMaxY}
					x2={xTo(es.placebo_window[1]) + 8}
					y2={cloudMaxY}
				/>
				<text class="cloudlbl" x={xTo(es.placebo_window[0]) - 6} y={cloudMaxY - 5}>
					most a fake date jumps: {fmt2(es.placebo_cloud_max_shift)}
				</text>

				<!-- axis baseline + a couple of season ticks -->
				<line class="axis" x1={VB.l - 8} y1={VB.h - VB.b} x2={VB.w - VB.r} y2={VB.h - VB.b} />
				{#each [2012, 2016, 2020, 2023, 2025] as s (s)}
					<text class="xtick" x={xTo(s)} y={VB.h - VB.b + 16}>{s}</text>
				{/each}

				<!-- the cursor -->
				<line class="cursor" x1={cursorX} y1={VB.t} x2={cursorX} y2={VB.h - VB.b} />

				<!-- the candidate dots -->
				{#each dots as d (d.season)}
					<circle
						class="dot"
						class:placebo={d.placebo}
						class:treat={d.treat}
						class:istrue={d.isTrue}
						class:sel={d.season === selected}
						cx={d.x}
						cy={d.y}
						r={d.season === selected ? 6.5 : d.isTrue ? 5 : 4}
					/>
				{/each}
			</svg>

			<!-- keyboard / touch control (the accessible path is the primary path) -->
			<label class="slider">
				<span class="s-lbl">Drag the date the rule "arrived"</span>
				<input
					type="range"
					min={X0}
					max={X1}
					step="1"
					bind:value={selected}
					oninput={() => (userControlled = true)}
					aria-label="The year the rule arrived, from 2012 to 2025"
					aria-valuetext="{selected}, jump {cand ? fmt2(cand.level_shift) : ''} runs an over"
				/>
			</label>

			<p class="disclose">
				2024 edges 2023 for raw size, because teams kept learning the rule. The break brackets
				2023–24, and 2023 is where it starts.
			</p>

			<button class="dagger" onclick={() => footnotesOpen.set('ch7-placebo')} aria-label="How this test works">
				ⓘ how this test works
			</button>
		</div>

		<div class="caption-slot" class:gap={reveal < 0.5} style="{capStyle}; --reveal: {reveal};">
			{#if step === 1}
				<div class="scene-card">
					<p>
						Maybe we just cherry-picked 2023. So let us test it. This marker asks a simple question:
						if the rule had come in that year instead, how big would the scoring jump be?
					</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>
						Try every year before the rule. Barely a bump, any of them. The grey line is the most a
						made-up date ever manages.
					</p>
				</div>
			{:else}
				<div class="scene-card">
					<p>
						Now land on the rule year. The jump leaps clear of the grey cloud, and stays clear the two
						seasons after. That is the only place a real jump shows up.
					</p>
				</div>
			{/if}
		</div>
	{/if}

	<div class="sr-only" aria-live="polite" role="status">{announce}</div>
</div>

<style>
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	.pin.active {
		visibility: visible;
	}

	.panel {
		pointer-events: auto;
		width: min(30rem, 92vw);
		background: rgba(11, 14, 20, 0.78);
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 14px;
		padding: 1rem 1.2rem 1.1rem;
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		max-height: 92dvh;
		overflow-y: auto;
	}

	.overline {
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--gold);
		margin: 0 0 0.7rem;
	}

	.readout {
		display: flex;
		align-items: baseline;
		gap: 0.9rem;
	}

	.ro-year {
		font-size: clamp(2rem, 9vw, 2.8rem);
		font-weight: 800;
		line-height: 1;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.readout.true .ro-year {
		color: var(--gold);
	}

	.ro-jump {
		display: flex;
		flex-direction: column;
	}

	.ro-big {
		font-size: 1.5rem;
		font-weight: 800;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.ro-unit {
		font-size: 0.64rem;
		color: var(--ink-dim);
	}

	.ro-tag {
		margin: 0.3rem 0 0.6rem;
		font-size: 0.78rem;
		line-height: 1.35;
		color: var(--ink-dim);
		min-height: 2.4em;
	}

	.ro-tag.true {
		color: var(--gold);
		font-weight: 600;
	}

	.lookup {
		margin: 0 0 0.5rem;
		font-size: 0.66rem;
		font-weight: 600;
		letter-spacing: 0.02em;
		color: var(--teal);
	}

	.chart {
		width: 100%;
		height: auto;
		display: block;
		touch-action: none; /* let the drag own horizontal gestures on the plot */
		cursor: ew-resize;
	}

	.chart.reduced {
		cursor: default;
	}

	.zone {
		stroke: none;
	}

	.zone.placebo {
		fill: rgba(151, 161, 184, 0.09);
	}

	.zone.treat {
		fill: rgba(232, 163, 61, 0.1);
	}

	.cloudline {
		stroke: rgba(151, 161, 184, 0.7);
		stroke-width: 1;
		stroke-dasharray: 3 3;
	}

	.cloudlbl {
		fill: var(--ink-dim);
		font-size: 8px;
	}

	.axis {
		stroke: rgba(232, 236, 245, 0.2);
		stroke-width: 1;
	}

	.xtick {
		fill: var(--ink-dim);
		font-size: 9px;
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	.cursor {
		stroke: rgba(232, 236, 245, 0.55);
		stroke-width: 1.4;
	}

	.dot {
		fill: rgba(151, 161, 184, 0.75);
		stroke: #0b0e14;
		stroke-width: 1;
	}

	.dot.treat {
		fill: var(--gold);
	}

	.dot.istrue {
		fill: var(--gold);
		stroke: #fff;
		stroke-width: 1.4;
	}

	.dot.sel {
		stroke: #fff;
		stroke-width: 1.6;
	}

	.slider {
		display: block;
		margin-top: 0.7rem;
	}

	.s-lbl {
		display: block;
		font-size: 0.72rem;
		color: var(--ink);
		margin-bottom: 0.1rem;
	}

	input[type='range'] {
		width: 100%;
		height: 44px;
		margin: 0;
		background: transparent;
		cursor: pointer;
		-webkit-appearance: none;
		appearance: none;
	}

	input[type='range']:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 4px;
		border-radius: 4px;
	}

	input[type='range']::-webkit-slider-runnable-track {
		height: 4px;
		border-radius: 999px;
		background: rgba(232, 236, 245, 0.18);
	}

	input[type='range']::-moz-range-track {
		height: 4px;
		border-radius: 999px;
		background: rgba(232, 236, 245, 0.18);
	}

	input[type='range']::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 22px;
		height: 22px;
		margin-top: -9px;
		border-radius: 50%;
		background: var(--gold);
		border: 3px solid #0b0e14;
		box-shadow: 0 0 0 1px var(--gold);
	}

	input[type='range']::-moz-range-thumb {
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: var(--gold);
		border: 3px solid #0b0e14;
		box-shadow: 0 0 0 1px var(--gold);
	}

	.disclose {
		margin: 0.6rem 0 0;
		font-size: 0.68rem;
		line-height: 1.4;
		color: var(--ink-dim);
		font-style: italic;
	}

	.dagger {
		display: inline-block;
		margin-top: 0.6rem;
		min-height: 44px;
		padding: 0.3rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.78rem;
		cursor: pointer;
	}

	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	/* the caption slot: desktop is placed in the panel's side margin via capStyle
	   (panelCaptionStyle); this base is the pre-measure fallback. */
	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 8vh;
		max-width: min(22rem, 26vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.pin {
			place-items: start center;
			padding-top: 6vh;
		}

		.panel {
			max-height: 62dvh;
		}

		/* mobile: the caption uses the bottom read-then-watch slot (capStyle is '' on
		   narrow), so the full-screen panel is unobstructed in the clear gap */
		.caption-slot {
			left: 50%;
			right: auto;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(3vh, calc(env(safe-area-inset-bottom) + 10px));
		}
	}
</style>
