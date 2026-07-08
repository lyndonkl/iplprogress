<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen, pickedTeam } from '$lib/state';
	import MatchField from './MatchField.svelte';
	import ReportCardRail from './ReportCardRail.svelte';
	import { pickReviewCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh8Data, ensureReviews, ownReviewLane, reviewLanes, fmt1, pct0, type Ch8Data } from './data';

	/**
	 * C8-4, HERO, Belief 2: the review economics (FAIL). The 988 review deliveries
	 * fly out of the held match-dots into per-franchise chip stacks: struck-down (the
	 * call stood) RED at the bottom, upheld (paid off) GREEN on top. The "mostly red"
	 * read carries THREE colourblind-safe channels beyond hue: a luminance split (the
	 * struck band darker, the paid-off lighter), a per-band tick/cross glyph, and the
	 * legend. The review-red is held distinct from every team red and the team-glow is
	 * muted while engaged, so a red-franchise reader never confuses "my team" with
	 * "the call stood"; the reader's own lane is found by a NON-RED head marker. On a
	 * phone the 10 lanes are not all labelled, one aggregate split plus the own lane.
	 * The honest delta ships straight: the success rate got WORSE, not merely flat.
	 * The CVD-safe chip colours (green #a8ecc0 lighter, red #ef5a44 darker) match the
	 * field shader palette and live in the legend/aggregate CSS below.
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

	let tick = $state(0);

	/* feed the 988-chip membership ONCE (the chips fly on reviews.engage from index.ts). */
	let fed = false;
	$effect(() => {
		if (!field || !ch8 || fed) return;
		fed = true;
		ensureReviews(field, ch8);
		tick++;
	});

	const step = $derived(
		progress < 0.16
			? 1
			: progress < 0.34
				? 2
				: progress < 0.52
					? 3
					: progress < 0.7
						? 4
						: progress < 0.86
							? 5
							: 6
	);
	const BOUNDS = [0, 0.16, 0.34, 0.52, 0.7, 0.86, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

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

	const narrow = $derived(isNarrowViewport());
	const capStyle = $derived.by(() => {
		void tick;
		void progress;
		if (narrow || !field) return '';
		return cornerStyle(pickReviewCorner(field).corner);
	});

	const ownLane = $derived(
		ch8 && $pickedTeam ? ownReviewLane(ch8, { league: $pickedTeam.league, team: $pickedTeam.team }) : -1
	);
	const lanesMeta = $derived(ch8 ? reviewLanes(ch8) : []);

	/* project the chip-lane geometry to CSS for labels / glyphs / the own-team marker */
	const geom = $derived.by(() => {
		void tick;
		void progress;
		const f = field;
		if (!f) return null;
		const rc = f.getReviewChipsLayout();
		if (!rc) return null;
		const lanes = rc.lanes.map((ln) => ({
			lane: ln.lane,
			base: f.projectToCss(ln.x, rc.box.bottom),
			cross: f.projectToCss(ln.crossAnchor.x, ln.crossAnchor.y),
			tick: f.projectToCss(ln.tickAnchor.x, ln.tickAnchor.y),
			head: f.projectToCss(ln.headMarker.x, ln.headMarker.y),
			struck: ln.struck,
			upheld: ln.upheld
		}));
		const agg = rc.aggregate;
		return {
			lanes,
			aggStruck: agg.struck,
			aggUpheld: agg.upheld,
			aggFracUpheld: agg.upheldFrac
		};
	});

	const r = $derived(ch8?.review ?? null);
	const showChips = $derived(reduced || step >= 2);
	const stamped = $derived(reduced || step >= 6 ? 2 : 1);
</script>

<div class="pin" class:active>
	<MatchField {field} {reduced} {progress} legend={false} footnoteId="ch8-review" />
	<ReportCardRail report={ch8?.report_card ?? null} {stamped} />

	<!-- persistent legend (CVD-safe: icon first, luminance second, colour third) -->
	<div class="legend">
		<span class="lg-row"><span class="glyph up">✓</span> paid off, the call got overturned</span>
		<span class="lg-row"><span class="glyph struck">✕</span> the call stood, nothing overturned</span>
		<span class="lg-note">darker means the call just stood</span>
	</div>

	{#if geom && showChips && !narrow}
		<!-- desktop: label every lane + a representative tick/cross glyph -->
		<div class="lanes" aria-hidden="true">
			{#each geom.lanes as ln (ln.lane)}
				<span class="tick-g" style="left:{ln.tick.x.toFixed(1)}px; top:{ln.tick.y.toFixed(1)}px;">✓</span>
				<span class="cross-g" style="left:{ln.cross.x.toFixed(1)}px; top:{ln.cross.y.toFixed(1)}px;">✕</span>
				<span
					class="lane-lbl"
					class:own={ln.lane === ownLane}
					style="left:{ln.base.x.toFixed(1)}px; top:{ln.base.y.toFixed(1)}px;"
				>
					{lanesMeta[ln.lane]?.short ?? ''}
				</span>
				{#if ln.lane === ownLane}
					<span class="own-marker" style="left:{ln.head.x.toFixed(1)}px; top:{ln.head.y.toFixed(1)}px;">
						▾ your team
					</span>
				{/if}
			{/each}
		</div>
	{/if}

	{#if narrow && r && geom}
		<!-- mobile: ONE aggregate split (the thesis) + the reader's own lane, not 10 lanes -->
		<div class="agg" aria-hidden="true">
			<div class="agg-bar">
				<div class="agg-up" style="height:{(geom.aggFracUpheld * 100).toFixed(1)}%">
					<span class="agg-g">✓ {geom.aggUpheld} paid off</span>
				</div>
				<div class="agg-struck">
					<span class="agg-g">✕ {geom.aggStruck} the call stood</span>
				</div>
			</div>
			<span class="agg-cap">{pct0(r.upheld_pct)} in 100 overturned</span>
			{#if ownLane >= 0 && lanesMeta[ownLane]}
				<span class="agg-own">
					{lanesMeta[ownLane].short}: {lanesMeta[ownLane].upheld} paid off,
					{lanesMeta[ownLane].struck} stood
				</span>
			{/if}
		</div>
	{/if}

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if r}
			{#if step === 1}
				<div class="scene-card">
					<p>
						Every review captains have ever called: {r.total} of them. Green, with a tick, means you
						were right and the call got overturned. Red, with a cross, means the call just stood.
					</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>Now look at the wall. Mostly red. Only {pct0(r.upheld_pct)} reviews in 100 overturned the call.</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						In 2022 the league doubled the allowance. Reviews per match jumped,
						{fmt1(r.headline.per_match_pre)} to {fmt1(r.headline.per_match_post)}.
					</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>
						More allowance, a better hit rate? The opposite. A smaller share overturned the call,
						{pct0(r.windows.pre.upheld_pct)} in 100 down to {pct0(r.windows.post.upheld_pct)}.
					</p>
				</div>
			{:else if step === 5}
				<div class="scene-card">
					<p>And it kept sliding. By 2026 just {pct0(r.per_season['2026'].upheld_pct)} reviews in 100 overturned the call.</p>
				</div>
			{:else}
				<div class="scene-card">
					<p>
						Belief two: reviews are a smart bet. Graded on the whole record: fail. Most never overturn
						the call, and the success rate keeps falling.
					</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch8-review')}>ⓘ how we graded the reviews</button>
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

	.legend {
		position: absolute;
		left: 2.5vw;
		bottom: 3vh;
		display: flex;
		flex-direction: column;
		gap: 0.26rem;
		padding: 0.5rem 0.7rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.82);
		border: 1px solid rgba(151, 161, 184, 0.25);
		max-width: min(17rem, 62vw);
	}

	.lg-row {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.lg-note {
		font-size: 0.66rem;
		color: var(--ink);
		font-weight: 600;
	}

	.glyph {
		flex: none;
		width: 1.1rem;
		height: 1.1rem;
		display: grid;
		place-items: center;
		border-radius: 4px;
		font-size: 0.7rem;
		font-weight: 800;
		color: #0b0e14;
	}

	.glyph.up {
		background: #a8ecc0;
	}

	.glyph.struck {
		background: #ef5a44;
		color: #fff;
	}

	.lanes {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.lane-lbl {
		position: absolute;
		transform: translate(-50%, 8px);
		font-size: 0.6rem;
		font-weight: 700;
		color: var(--ink-dim);
		text-shadow: 0 1px 5px rgba(0, 0, 0, 0.9);
	}

	.lane-lbl.own {
		color: var(--ink);
	}

	.tick-g,
	.cross-g {
		position: absolute;
		transform: translate(-50%, -50%);
		font-size: 0.62rem;
		font-weight: 800;
		text-shadow: 0 1px 4px rgba(0, 0, 0, 0.95);
	}

	.tick-g {
		color: #0b1f13;
	}

	.cross-g {
		color: #2a0906;
	}

	.own-marker {
		position: absolute;
		transform: translate(-50%, -100%);
		white-space: nowrap;
		font-size: 0.64rem;
		font-weight: 800;
		color: var(--teal);
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
	}

	.agg {
		position: absolute;
		left: 50%;
		top: 22vh;
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.4rem;
		width: 62vw;
		max-width: 18rem;
	}

	.agg-bar {
		width: 100%;
		height: 44vh;
		display: flex;
		flex-direction: column;
		border-radius: 10px;
		overflow: hidden;
		border: 1px solid rgba(151, 161, 184, 0.3);
	}

	.agg-up {
		background: #a8ecc0;
		color: #0b1f13;
		display: grid;
		place-items: center;
	}

	.agg-struck {
		flex: 1;
		background: #ef5a44;
		color: #fff;
		display: grid;
		place-items: center;
	}

	.agg-g {
		font-size: 0.72rem;
		font-weight: 800;
	}

	.agg-cap {
		font-size: 0.9rem;
		font-weight: 800;
		color: var(--ink);
	}

	.agg-own {
		font-size: 0.72rem;
		color: var(--teal);
		font-weight: 700;
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
		.legend {
			bottom: auto;
			top: 12vh;
			left: 2vw;
			padding: 0.4rem 0.55rem;
		}

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
