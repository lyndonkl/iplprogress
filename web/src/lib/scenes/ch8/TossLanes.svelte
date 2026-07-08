<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { matchDotsPoint } from '$lib/field/layout';
	import { footnotesOpen } from '$lib/state';
	import MatchField from './MatchField.svelte';
	import ReportCardRail from './ReportCardRail.svelte';
	import { pickCaptionCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh8Data, dateNormToField, pct0, type Ch8Data } from './data';

	/**
	 * C8-3, HERO, Belief 1: the toss revolution (FAIL). The held match-dots lift
	 * into their two toss lanes (matchSplit 0→1, driven in index.ts): the winner
	 * batted first up top, the winner chose to field down below. The lower river
	 * SWELLS after 2016 while the top thins, straight from the data's toss shift.
	 * Over the split, the belief-reality crossover draws its two directly-labelled
	 * lines that CROSS, how often captains chose to field (a CHOICE) and how often
	 * the chase actually won (a RESULT), with NO shaded gap between them (they are
	 * different kinds, not a subtractable quantity), the humped chase-win line drawn
	 * honestly, the crossing point annotated, and the toss-is-worth-nothing fact in
	 * an inset. It grades a belief-versus-outcome mismatch, never a cause.
	 */
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

	/* five one-point steps: orient the lanes / the belief hardening / the chase line /
	   the crossover / the grade. The split lifts across steps 1-2 (index.ts dynamicState). */
	const step = $derived(
		progress < 0.16 ? 1 : progress < 0.36 ? 2 : progress < 0.58 ? 3 : progress < 0.8 ? 4 : 5
	);
	const BOUNDS = [0, 0.16, 0.36, 0.58, 0.8, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

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
		cancelAnimationFrame(raf);
		raf = requestAnimationFrame(() => {
			tick += 1;
		});
		return () => cancelAnimationFrame(raf);
	});

	const capStyle = $derived.by(() => {
		void tick;
		void progress;
		if (isNarrowViewport() || !field) return '';
		return cornerStyle(pickCaptionCorner(field).corner);
	});

	/* the crossover geometry, anchored in TIME to the season axis (so the crossing
	   lands over the same seasons as the dots below) and in a percent band across the
	   upper area of the box. Re-projected each frame as the lanes lift + on resize. */
	const geom = $derived.by(() => {
		void tick;
		void progress;
		const f = field;
		const d = ch8;
		if (!f || !d) return null;
		const md = f.getMatchDotsLayout();
		if (!md) return null;
		const cx = d.toss.crossover;
		const [dLo, dHi] = cx.y_domain;
		// the percent band: high pct near the top of the box, low near the middle
		const topY = f.projectToCss(matchDotsPoint(md, 0, 0.95).x, matchDotsPoint(md, 0, 0.95).y).y;
		const botY = f.projectToCss(matchDotsPoint(md, 0, 0.1).x, matchDotsPoint(md, 0, 0.1).y).y;
		const xOf = (xn: number): number =>
			f.projectToCss(matchDotsPoint(md, dateNormToField(xn), 0).x, 0).x;
		const yOf = (pct: number): number => {
			const t = (pct - dLo) / (dHi - dLo);
			return botY + (topY - botY) * t;
		};
		const poly = (pts: [number, number][]): string =>
			pts.map(([xn, pct]) => `${xOf(xn).toFixed(1)},${yOf(pct).toFixed(1)}`).join(' ');
		const fieldFirst = poly(cx.field_first_line);
		const chase = poly(cx.chase_win_line);
		const ffEnd = cx.field_first_line.at(-1);
		const cwEnd = cx.chase_win_line.at(-1);
		const cross = { x: xOf(cx.crossing_point.x), y: yOf(cx.crossing_point.pct) };
		// lane tags at the right edge, at each lane centre (for the live split)
		const upper = f.projectToCss(md.left + md.width * 0.98, md.laneY * md.split);
		const lower = f.projectToCss(md.left + md.width * 0.98, -md.laneY * md.split);
		// the captain-simulator "chase-watcher" line (a lookup): trailing chase-win by season
		const seasonX = new Map<number, number>();
		for (const [s, xn] of d.match_dots.axis_ticks) seasonX.set(s, xn);
		const simPts = d.toss.captain_sim
			.filter((r) => r.trailing_chase_win != null && seasonX.has(r.season))
			.map((r) => `${xOf(seasonX.get(r.season) as number).toFixed(1)},${yOf(r.trailing_chase_win as number).toFixed(1)}`)
			.join(' ');
		return {
			fieldFirst,
			chase,
			ffEnd: ffEnd ? { x: xOf(ffEnd[0]), y: yOf(ffEnd[1]) } : null,
			cwEnd: cwEnd ? { x: xOf(cwEnd[0]), y: yOf(cwEnd[1]) } : null,
			cross,
			upper,
			lower,
			simPts,
			line50: yOf(50)
		};
	});

	const t = $derived(ch8?.toss ?? null);
	const showLanes = $derived(reduced || step >= 2);
	const showFF = $derived(reduced || step >= 2);
	const showChase = $derived(reduced || step >= 3);
	const showCross = $derived(reduced || step >= 4);
	const stamped = $derived(reduced || step >= 5 ? 1 : 0);

	let simOn = $state(false);
</script>

<div class="pin" class:active>
	<MatchField {field} {reduced} {progress} axis={true} legend={true} footnoteId="ch8-toss" />
	<ReportCardRail report={ch8?.report_card ?? null} {stamped} />

	{#if geom && showLanes}
		<!-- lane tags at the right edge; the field-first river swells along the bottom -->
		<div class="lane-tags" aria-hidden="true">
			<span class="lane-tag up" style="left:{geom.upper.x.toFixed(1)}px; top:{geom.upper.y.toFixed(1)}px;">
				won it, batted first
			</span>
			<span class="lane-tag down" style="left:{geom.lower.x.toFixed(1)}px; top:{geom.lower.y.toFixed(1)}px;">
				won it, put them in
			</span>
		</div>

		<!-- the belief-reality crossover: two crossing lines, NO shaded fill -->
		<svg class="crossover" aria-hidden="true">
			<line class="ref" x1="6%" x2="94%" y1={geom.line50} y2={geom.line50} />
			{#if showFF}
				<polyline class="line choice" points={geom.fieldFirst} />
			{/if}
			{#if showChase}
				<polyline class="line result" points={geom.chase} />
			{/if}
			{#if simOn && geom.simPts}
				<polyline class="line sim" points={geom.simPts} />
			{/if}
			{#if showCross}
				<circle class="cross-dot" cx={geom.cross.x} cy={geom.cross.y} r="5" />
			{/if}
		</svg>

		<div class="lbls" aria-hidden="true">
			{#if showFF && geom.ffEnd && t}
				<span class="end choice" style="left:{geom.ffEnd.x.toFixed(1)}px; top:{geom.ffEnd.y.toFixed(1)}px;">
					chose to field<br /><em>a choice, {pct0(t.headline.field_first_end)} in 100</em>
				</span>
			{/if}
			{#if showChase && geom.cwEnd && t}
				<span class="end result" style="left:{geom.cwEnd.x.toFixed(1)}px; top:{geom.cwEnd.y.toFixed(1)}px;">
					the chase won<br /><em>a result, {pct0(t.headline.chase_win_end)} in 100</em>
				</span>
			{/if}
			{#if showCross && t}
				<span class="cross-note" style="left:{geom.cross.x.toFixed(1)}px; top:{geom.cross.y.toFixed(1)}px;">
					here the choice overtook the result
				</span>
			{/if}
		</div>
	{/if}

	<!-- the toss-is-worth-nothing inset (step 4+) -->
	{#if t && (reduced || step >= 4)}
		<div class="inset">
			<span class="inset-h">Winning the toss itself</span>
			<span class="inset-b">about 50 in 100, every era</span>
			<span class="inset-row">
				{#each t.eras as e (e.era)}<span class="chip">{pct0(e.tosswin_matchwin)}</span>{/each}
			</span>
		</div>
	{/if}

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if t}
			{#if step === 1}
				<div class="scene-card">
					<p>Split every match by the toss. Won it and batted first, up top. Won it and put them in, down below.</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>
						Watch the bottom river swell as the top thins. Captains choosing to field:
						{pct0(t.headline.field_first_start)} in 100 back then, {pct0(t.headline.field_first_end)} now.
					</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						Now the line for what the chase actually did. It rose to {pct0(t.headline.chase_win_hump)} in
						100 in the late 2010s, then sank right back to where it began, {pct0(t.headline.chase_win_end)}.
					</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>
						Watch the two lines cross. Captains went from choosing to field less often than the chase
						won, to far more, while the chase wins no more than it ever did. The line that moved was
						the choice, not the result.
					</p>
					<button class="sim-toggle" onclick={() => (simOn = !simOn)}>
						{simOn ? 'Hide' : 'What would a captain who only watched the chase decide?'}
					</button>
					{#if simOn}
						<p class="guard">
							Following the chase would not have won more matches. Winning the toss barely moves the
							result. This only shows how far the choice drifted from the evidence.
						</p>
					{/if}
				</div>
			{:else}
				<div class="scene-card">
					<p>Belief one: bowling first is the edge. Graded on the whole record: not backed.</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch8-toss')}>ⓘ how we graded the toss</button>
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

	.crossover {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: visible;
	}

	.line {
		fill: none;
		stroke-width: 2.6;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	/* the two kinds are separated by STYLE + LUMINANCE, never green/red (reserved for
	   the review chips): the choice is a bright solid line, the result a dashed dimmer one */
	.line.choice {
		stroke: #f2e9d0;
		filter: drop-shadow(0 0 4px rgba(242, 233, 208, 0.5));
	}

	.line.result {
		stroke: #8fa2c4;
		stroke-dasharray: 7 5;
	}

	.line.sim {
		stroke: #c58fd8;
		stroke-dasharray: 2 5;
		stroke-width: 2;
	}

	.ref {
		stroke: rgba(151, 161, 184, 0.3);
		stroke-width: 1;
		stroke-dasharray: 2 6;
		vector-effect: non-scaling-stroke;
	}

	.cross-dot {
		fill: #fff;
		stroke: #0b0e14;
		stroke-width: 1.5;
	}

	.lbls,
	.lane-tags {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.end {
		position: absolute;
		transform: translate(10px, -50%);
		white-space: nowrap;
		font-size: 0.72rem;
		font-weight: 700;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
	}

	.end em {
		font-style: normal;
		font-weight: 500;
		font-size: 0.62rem;
		color: var(--ink-dim);
	}

	.end.choice {
		color: #f2e9d0;
	}

	.end.result {
		color: #a9b8d6;
	}

	.cross-note {
		position: absolute;
		transform: translate(-50%, -170%);
		width: 9rem;
		text-align: center;
		font-size: 0.62rem;
		font-weight: 600;
		color: var(--ink);
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
	}

	.lane-tag {
		position: absolute;
		transform: translate(-100%, -50%);
		white-space: nowrap;
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.02em;
		color: var(--ink);
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
	}

	.inset {
		position: absolute;
		right: 2.5vw;
		bottom: 4vh;
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		padding: 0.5rem 0.7rem;
		border-radius: 10px;
		background: rgba(10, 14, 24, 0.8);
		border: 1px solid rgba(151, 161, 184, 0.22);
	}

	.inset-h {
		font-size: 0.6rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.inset-b {
		font-size: 0.82rem;
		font-weight: 700;
		color: var(--ink);
	}

	.inset-row {
		display: flex;
		gap: 0.28rem;
		margin-top: 0.15rem;
	}

	.chip {
		font-size: 0.64rem;
		font-variant-numeric: tabular-nums;
		color: var(--ink-dim);
		padding: 0.05rem 0.28rem;
		border-radius: 5px;
		background: rgba(151, 161, 184, 0.12);
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 15vh;
		max-width: min(25rem, 42vw);
		opacity: var(--reveal, 1);
	}

	.sim-toggle,
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

	.sim-toggle:focus-visible,
	.fn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.guard {
		margin-top: 0.4rem;
		font-size: 0.72rem;
		line-height: 1.4;
		color: var(--ink-dim);
		font-style: italic;
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			right: auto;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}

		.inset {
			right: auto;
			left: 2vw;
			bottom: auto;
			top: 20vh;
		}
	}
</style>
