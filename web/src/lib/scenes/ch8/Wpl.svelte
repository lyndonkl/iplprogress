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
	 * C8-8, the WPL doctrine transmission (structural, not decorative). The dots dim;
	 * the WPL's 88 match-dots are circled in teal (the young league sitting inside the
	 * same cloud), and its toss adoption curve draws over them. The house framing rule
	 * made literal: it did NOT inherit the field-first doctrine instantly, it adopted
	 * it on a fast two-season curve (54.5 to about 100); it calibrates its reviews like
	 * the men's game; and it out-fragments the modern men's game. A league born into
	 * the analytics age, never "behind".
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

	const step = $derived(
		progress < 0.17
			? 1
			: progress < 0.35
				? 2
				: progress < 0.53
					? 3
					: progress < 0.7
						? 4
						: progress < 0.86
							? 5
							: 6
	);
	const BOUNDS = [0, 0.17, 0.35, 0.53, 0.7, 0.86, 1] as const;
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

	const geom = $derived.by(() => {
		void tick;
		void progress;
		const f = field;
		const d = ch8;
		if (!f || !d) return null;
		const md = f.getMatchDotsLayout();
		if (!md) return null;
		const topY = f.projectToCss(0, matchDotsPoint(md, 0, 0.9).y).y;
		const botY = f.projectToCss(0, matchDotsPoint(md, 0, -0.4).y).y;
		const xOf = (xn: number): number =>
			f.projectToCss(matchDotsPoint(md, dateNormToField(xn), 0).x, 0).x;
		const yOf = (pct: number): number => botY + (topY - botY) * ((pct - 40) / (100 - 40));
		const curve = d.wpl.adoption_curve
			.map(([xn, pct]) => `${xOf(xn).toFixed(1)},${yOf(pct).toFixed(1)}`)
			.join(' ');
		const seasonPts = Object.entries(d.wpl.field_first_by_season).map(([season], i) => {
			const [xn, pct] = d.wpl.adoption_curve[i];
			return { season, x: xOf(xn), y: yOf(pct) };
		});
		// circle the WPL dots (league == 1) inside the same cloud
		const rings: { x: number; y: number }[] = [];
		const centres = md.centres;
		for (let m = 0; m < centres.length; m++) {
			if (d.match_dots.league[m] !== 1) continue;
			const c = centres[m];
			if (!c || Number.isNaN(c.x)) continue;
			rings.push(f.projectToCss(c.x, c.y));
		}
		return { curve, seasonPts, rings };
	});

	const w = $derived(ch8?.wpl ?? null);
	const showCurve = $derived(reduced || step >= 2);
</script>

<div class="pin" class:active>
	<MatchField {field} {reduced} {progress} faint={true} legend={false} footnoteId="ch8-wpl" />
	<ReportCardRail report={ch8?.report_card ?? null} stamped={5} />

	{#if geom}
		<svg class="wpl-plane" aria-hidden="true">
			{#each geom.rings as p, i (i)}
				<circle class="wring" cx={p.x} cy={p.y} r="4" />
			{/each}
			{#if showCurve}
				<polyline class="acurve" points={geom.curve} />
				{#each geom.seasonPts as s (s.season)}
					<circle class="apt" cx={s.x} cy={s.y} r="4" />
				{/each}
			{/if}
		</svg>
		{#if showCurve}
			<div class="alabels" aria-hidden="true">
				{#each geom.seasonPts as s (s.season)}
					<span class="alabel" style="left:{s.x.toFixed(1)}px; top:{s.y.toFixed(1)}px;">{s.season}</span>
				{/each}
			</div>
		{/if}
	{/if}

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if w}
			{#if step === 1}
				<div class="scene-card">
					<p>The women's league is just four seasons old. Watch what it did with the toss.</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>
						Season one, it split the toss like the men's game did back in 2008,
						{pct0(w.headline.season_one_field_first)} in 100. Two seasons later, nearly every captain
						fields first.
					</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						The men's game took the better part of a decade to lean this way, and settled around
						{w.ipl_compare.field_first_settled} in 100. The women's game went nearly all the way in two
						seasons. The culture arrived before the history did.
					</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>
						Its reviews pay off at almost exactly the men's rate, {pct0(w.headline.review_upheld_pct)}
						in 100 to {pct0(w.ipl_compare.review_upheld_pct)}. Same gamblers, same odds.
					</p>
				</div>
			{:else if step === 5}
				<div class="scene-card">
					<p>
						And it deals overs even faster. One-and-done overs: {pct0(w.headline.one_over_share)} in
						100, more than the modern men's game ({pct0(w.ipl_compare.one_over_share)}).
					</p>
				</div>
			{:else}
				<div class="scene-card">
					<p>A league born into the analytics age, behaving like one from the start.</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch8-wpl')}>ⓘ how the young league reads</button>
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

	.wpl-plane {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: visible;
	}

	.wring {
		fill: none;
		stroke: #2ec4b6;
		stroke-width: 1.1;
		opacity: 0.55;
	}

	.acurve {
		fill: none;
		stroke: #2ec4b6;
		stroke-width: 2.8;
		stroke-linejoin: round;
		stroke-linecap: round;
		filter: drop-shadow(0 0 5px rgba(46, 196, 182, 0.55));
	}

	.apt {
		fill: #2ec4b6;
		stroke: #0b0e14;
		stroke-width: 1.2;
	}

	.alabels {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.alabel {
		position: absolute;
		transform: translate(-50%, -150%);
		font-size: 0.62rem;
		font-weight: 700;
		color: #62d2c3;
		font-variant-numeric: tabular-nums;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 15vh;
		max-width: min(24rem, 40vw);
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
