<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal, captionRevealActive } from '$lib/story/captionReveal.svelte';
	import { worthCell } from '$lib/field/layout';
	import { loadCh5Data, IPL_EARLY, IPL_RECENT, in100, int, type Ch5Data } from './data';
	import WorthScaffold from './WorthScaffold.svelte';

	/**
	 * C5-10 — The WPL beat (two clocks, one beat — house rule). The grid recolors
	 * to the WPL surface (pricelens 'wpl', driven by index.ts): evidenced cells
	 * carry real WPL prices, and the 155 masked cells render the flat NEUTRAL
	 * luminance (buildWorthTables strips the engine's smoothed values there — no
	 * fake fitted surface glows beneath the hatch) with the hatching drawn on
	 * this annotation plane (hatching is never a dimness — a thin cell must
	 * never read as a cheap one). Where the mask bites and cricket HAS been
	 * played, the OBSERVED marks are drawn cell by cell: one small mark per real
	 * WPL innings through that spot ("real outcomes as real marks", ch5-wpl ¶2 —
	 * the only WPL evidence drawn on masked ground). Then the forming finisher
	 * cohort as literal match dots (9 of 11, the honest small count as the star)
	 * with the IPL's two era readings as quiet reference ticks, and the
	 * number-free dialect chip (Ch 6's tease). The on-timeline read (step 3) and
	 * the timeline-refusing read (step 4) land in adjacent steps of ONE scene;
	 * "behind" never appears. Match counts (88 / 1,331) are pipeline-emitted
	 * fields counted from the corpus (wpl_beat.match_counts), never typed.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.3 ? 1 : progress < 0.55 ? 2 : progress < 0.78 ? 3 : 4);
	const BOUNDS = [0, 0.3, 0.55, 0.78, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch5 = $state<Ch5Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh5Data().then((d) => {
			if (alive) ch5 = d;
		});
		return () => {
			alive = false;
		};
	});

	const mask = $derived(ch5?.wpl_beat.mask ?? null);
	const matchCounts = $derived(ch5?.wpl_beat.match_counts ?? null);
	const cohort = $derived(ch5?.wpl_beat.finisher_8_10 ?? null);
	const iplEarly = $derived(ch5?.finisher.table[IPL_EARLY]['8-10'] ?? null);
	const iplRecent = $derived(ch5?.finisher.table[IPL_RECENT]['8-10'] ?? null);

	/* hatch rects registered to the GL cells (rebuilt on resize) */
	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => {
				tick++;
			});
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	let seeded = false;
	$effect(() => {
		if (field && !seeded) {
			seeded = true;
			tick++;
		}
	});
	const hatch = $derived.by(() => {
		void tick;
		const f = field;
		const wl = f?.getWorthLayout();
		const m = mask;
		if (!f || !wl || !m) return null;
		return m.masked_cells.map(([o, w]) => {
			const c = worthCell(wl, o, w);
			const centre = f.projectToCss(c.x, c.y);
			const corner = f.projectToCss(c.x + wl.cellW / 2, c.y - wl.cellH / 2);
			const hw = corner.x - centre.x;
			const hh = corner.y - centre.y;
			return { o, w, x: centre.x - hw, y: centre.y - hh, w2: hw * 2, h2: hh * 2 };
		});
	});
	const hatchOn = $derived(reduced || progress >= 0.12);

	/* the OBSERVED marks: one small mark per real WPL innings through each
	   masked-but-played cell (wpl_beat.observed_dots — the only WPL evidence
	   drawn where the mask bites; a mini row-major grid inside the cell) */
	const marks = $derived.by(() => {
		void tick;
		const f = field;
		const wl = f?.getWorthLayout();
		const od = ch5?.wpl_beat.observed_dots ?? null;
		if (!f || !wl || !od) return null;
		const pts: { x: number; y: number }[] = [];
		for (const cell of od.cells) {
			const c = worthCell(wl, cell.o, cell.w);
			const centre = f.projectToCss(c.x, c.y);
			const corner = f.projectToCss(c.x + wl.cellW / 2, c.y - wl.cellH / 2);
			const hw = (corner.x - centre.x) * 0.72;
			const hh = (corner.y - centre.y) * 0.72;
			const cols = Math.min(cell.n, 5);
			const rows = Math.ceil(cell.n / 5);
			for (let k = 0; k < cell.n; k++) {
				pts.push({
					x: centre.x - hw + (((k % cols) + 0.5) * (2 * hw)) / cols,
					y: centre.y - hh + ((Math.floor(k / cols) + 0.5) * (2 * hh)) / rows
				});
			}
		}
		return pts;
	});

	/* tapping the cohort panel shows the rate conversion (the dots stay the star) */
	let cohortTapped = $state(false);

	/* tap any hatched cell for the mask gloss (the C5-5 tap-read grammar) */
	let hatchTapped = $state<{ o: number; w: number; x: number; y: number } | null>(null);
	const hatchTapN = $derived(
		hatchTapped && ch5 ? (ch5.wpl_beat.re_n[hatchTapped.o]?.[hatchTapped.w] ?? 0) : 0
	);

	/* mobile step 4: the dialect chip is the star — the cohort card compresses
	   (dots + ticks fold away) so the stack never buries the hatched grid */
	const cohortCompact = $derived(captionRevealActive() && !reduced && step >= 4);
</script>

<div class="pin" class:active>
	<WorthScaffold {field} />

	{#if hatch && hatchOn}
		<svg class="hatch-layer" aria-hidden="true">
			<defs>
				<pattern id="ch5-hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
					<line x1="0" y1="0" x2="0" y2="7" stroke="rgba(151, 161, 184, 0.5)" stroke-width="1.4" />
				</pattern>
			</defs>
			{#each hatch as r (r.o * 10 + r.w)}
				<rect x={r.x} y={r.y} width={r.w2} height={r.h2} fill="url(#ch5-hatch)" />
			{/each}
			{#if marks}
				{#each marks as p, i (i)}
					<circle class="obs-mark" cx={p.x} cy={p.y} r="1.7" />
				{/each}
			{/if}
		</svg>
		<!-- tap targets over the hatched cells (mask gloss on tap, ≥ cell-size) -->
		<div class="hatch-taps">
			{#each hatch as r (r.o * 10 + r.w)}
				<button
					class="hatch-tap"
					style="left:{r.x.toFixed(1)}px; top:{r.y.toFixed(1)}px; width:{r.w2.toFixed(
						1
					)}px; height:{r.h2.toFixed(1)}px;"
					tabindex="-1"
					onclick={() =>
						(hatchTapped =
							hatchTapped && hatchTapped.o === r.o && hatchTapped.w === r.w
								? null
								: { o: r.o, w: r.w, x: r.x + r.w2 / 2, y: r.y })}
					aria-label="Over {r.o + 1}, {r.w} down: not enough WPL cricket yet"
				></button>
			{/each}
		</div>
		{#if hatchTapped}
			<div
				class="hatch-read"
				style="left:{hatchTapped.x.toFixed(1)}px; top:{hatchTapped.y.toFixed(1)}px;"
			>
				over {hatchTapped.o + 1}, {hatchTapped.w} down: not enough WPL cricket yet ({int(
					hatchTapN
				)}
				{hatchTapN === 1 ? 'innings has' : 'innings have'} passed through)
			</div>
		{/if}
		<span class="hatch-key">
			<span>hatched = not enough WPL cricket yet</span>
			<span class="hk-sub">small marks = the real WPL innings through those spots</span>
		</span>
	{/if}

	{#if cohort && iplEarly && iplRecent && (reduced || step >= 2)}
		<div class="cohort" class:compact={cohortCompact}>
			<span class="co-title">WPL chases needing 8-10 an over, five overs left</span>
			<button
				class="dots"
				onclick={() => (cohortTapped = !cohortTapped)}
				aria-label="The WPL finisher cohort: {cohort.wins} of {cohort.n} such chases won"
			>
				{#each Array.from({ length: cohort.n }) as _, i (i)}
					<span class="dot" class:lit={i < cohort.wins}></span>
				{/each}
			</button>
			<span class="co-read">{cohort.wins} of {cohort.n} came off</span>
			{#if cohortTapped}
				<span class="co-rate">as a rate: about {in100(cohort.win_pct)} in 100, from {cohort.n} real chases</span>
			{/if}
			{#if reduced || step >= 3}
				<div class="ticks">
					<span class="tick-row">
						<span class="t-mark"></span> IPL {'2008-2010'}: {in100(iplEarly.win_pct)} in 100
					</span>
					<span class="tick-row">
						<span class="t-mark new"></span> IPL {'2023-2026'}: {in100(iplRecent.win_pct)} in 100
					</span>
				</div>
			{/if}
		</div>
	{/if}

	{#if reduced || step >= 4}
		<div class="dialect-chip">
			<span class="d-big">no league in this story finishes tighter</span>
			<span class="d-sub">the WPL's own dialect · Chapter 6 is built on it</span>
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					Same map, the women's game. The WPL has played {matchCounts ? int(matchCounts.wpl) : 88}
					matches, not {matchCounts ? int(matchCounts.total) : '1,331'}, so most cells do not hold
					enough cricket to price honestly yet. Those are hatched out. We would rather show you
					the gap than dress up a guess.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-wpl')}
						aria-label="How the evidence mask works">ⓘ</button
					>
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Where there is enough cricket, the reads are real. Chases needing eight to ten an over
					with five overs left: {cohort?.n ?? 11} of them so far, and {cohort?.wins ?? 9} came
					off. Every dot here is a real match, not a curve.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					The two quiet ticks are the IPL's own eras. {cohort?.wins ?? 9} of {cohort?.n ?? 11}
					lands above the old one and below the new one, on the WPL's own clock, not along the
					IPL's.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					And in the same breath, a thing no timeline explains: no league in this whole story
					finishes tighter than the WPL. Its own dialect. Chapter 6 is built on it.
				</p>
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

	.hatch-layer {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	/* the observed marks: real WPL innings drawn as real marks on masked
	   ground (never a curve; never a price) */
	.obs-mark {
		fill: rgba(232, 236, 245, 0.78);
	}

	.hatch-taps {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.hatch-tap {
		pointer-events: auto;
		position: absolute;
		margin: 0;
		padding: 0;
		border: none;
		background: transparent;
		cursor: pointer;
		/* taps register, vertical scroll still belongs to the page */
		touch-action: pan-y pinch-zoom;
	}

	.hatch-read {
		position: absolute;
		transform: translate(-50%, -130%);
		max-width: 17rem;
		padding: 0.4rem 0.65rem;
		border-radius: 10px;
		background: rgba(10, 14, 24, 0.9);
		border: 1px solid rgba(151, 161, 184, 0.35);
		font-size: 0.78rem;
		line-height: 1.35;
		color: var(--ink);
		pointer-events: none;
		font-variant-numeric: tabular-nums;
		text-align: center;
	}

	.hatch-key {
		position: absolute;
		top: 4.5vh;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.1rem;
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-dim);
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
		white-space: nowrap;
	}

	.hk-sub {
		font-size: 0.56rem;
		font-weight: 600;
		letter-spacing: 0.08em;
	}

	.cohort {
		position: absolute;
		left: 4vw;
		/* 42%, not 50%: guarantees clearance above the bottom-left caption slot
		   even on short desktop viewports (~800px CSS) */
		top: 42%;
		transform: translateY(-50%);
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		padding: 0.75rem 0.95rem;
		border-radius: 14px;
		background: rgba(10, 14, 24, 0.85);
		border: 1px solid rgba(151, 161, 184, 0.3);
		max-width: 17rem;
	}

	.co-title {
		font-size: 0.64rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.dots {
		pointer-events: auto;
		display: flex;
		gap: 0.35rem;
		flex-wrap: wrap;
		background: none;
		border: none;
		padding: 0.4rem 0;
		min-height: 44px;
		cursor: pointer;
		align-items: center;
	}

	.dots:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.dot {
		width: 0.85rem;
		height: 0.85rem;
		border-radius: 50%;
		background: rgba(151, 161, 184, 0.25);
		border: 1px solid rgba(151, 161, 184, 0.4);
	}

	.dot.lit {
		background: #62d2c3;
		border-color: #62d2c3;
		box-shadow: 0 0 8px rgba(98, 210, 195, 0.5);
	}

	.co-read {
		font-size: 0.92rem;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
	}

	.co-rate {
		font-size: 0.72rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.ticks {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		border-top: 1px solid rgba(151, 161, 184, 0.2);
		padding-top: 0.45rem;
	}

	.tick-row {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.72rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.t-mark {
		width: 0.7rem;
		height: 2px;
		background: rgba(151, 161, 184, 0.8);
	}

	.t-mark.new {
		background: #ffd166;
	}

	.dialect-chip {
		position: absolute;
		right: 4vw;
		top: 20vh;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		padding: 0.7rem 0.95rem;
		border-radius: 14px;
		background: rgba(10, 14, 24, 0.85);
		border: 1px solid rgba(98, 210, 195, 0.45);
		max-width: 16rem;
	}

	.d-big {
		font-size: 0.95rem;
		font-weight: 800;
		color: #62d2c3;
	}

	.d-sub {
		font-size: 0.7rem;
		color: var(--ink-dim);
	}

	/* grid captions live in the BOTTOM-LEFT corner — the empty early-collapse
	   cells (~150 balls; hatched under the WPL mask), never the death-collapse
	   corner where the observed-outcome dots live. 12vw clears the wickets
	   ticks; the cohort card rides higher (top 42%) so the two never meet. */
	.caption-slot {
		position: absolute;
		left: 12vw;
		bottom: 9vh;
		max-width: min(24rem, 38vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	/* no invisible ⓘ tap target during the mobile clear gap */
	.caption-slot.gap .dagger {
		pointer-events: none;
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

	/* mobile step 4: the dialect chip is the star — the cohort folds to its
	   one-line read so the stack never buries the hatched grid */
	.cohort.compact .dots,
	.cohort.compact .ticks,
	.cohort.compact .co-rate {
		display: none;
	}

	@media (max-width: 640px) {
		.cohort {
			left: 3vw;
			top: auto;
			bottom: 26vh;
			max-width: 60vw;
			padding: 0.5rem 0.65rem;
		}

		.dialect-chip {
			right: 3vw;
			top: auto;
			bottom: 26vh;
			max-width: 34vw;
			padding: 0.5rem 0.6rem;
		}

		.d-big {
			font-size: 0.78rem;
		}

		.caption-slot {
			right: auto;
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(3vh, calc(env(safe-area-inset-bottom) + 10px));
		}
	}
</style>
