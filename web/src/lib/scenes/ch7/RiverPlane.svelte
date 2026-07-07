<script lang="ts">
	import { onMount } from 'svelte';
	import type { FieldHandle } from '$lib/field/field';
	import { flowSeasonToX, flowRateToY } from '$lib/field/layout';
	import { footnotesOpen } from '$lib/state';
	import { loadCh7Data, ensureRiverTable, riverGis, type Ch7Data } from './data';

	/**
	 * The twin-rivers annotation plane (CONTRACT §23.5). Draws the two run-rate
	 * CENTRELINES (the crisp two-line read of the divergence), the "runs an over"
	 * axis, the season axis, the 2023 FORK marker, the shaded GAP between the
	 * rivers over the treatment years, and the persistent legend — all SVG
	 * registered to the GL ribbons via `field.getFlowLayout()` + `field.projectToCss`,
	 * so the overlay tracks the `flowLift` divergence reveal exactly and never
	 * becomes GL geometry (the cardinality rule).
	 *
	 * This component also FEEDS the per-gi river table ONCE (setRiverTable — the
	 * run rates rolled up from ch7.json), so the GL ribbons and this SVG can never
	 * drift. Shared by the orient (C7-2) and control-group (C7-3) scenes.
	 *
	 * Hue is identity: the men's river reads warm/gold, the women's reads teal —
	 * the same family colours the field uses, so the two rivers are legible even
	 * where they run vertically close.
	 */
	interface Props {
		field: FieldHandle | null;
		reduced: boolean;
		progress: number;
		/** reveal gate — the lines/labels fade in once the ribbons have landed */
		on?: boolean;
		/** shade the gap between the two rivers over the treatment years */
		showGap?: boolean;
		/** dim the whole plane to a faint trace (behind a 2D panel) */
		faint?: boolean;
		/** render the persistent orientation legend (+ the always-on methods ⓘ) */
		legend?: boolean;
		footnoteId?: string;
	}
	let {
		field,
		reduced,
		progress,
		on = true,
		showGap = false,
		faint = false,
		legend = false,
		footnoteId = 'ch7-rivers'
	}: Props = $props();

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

	/* feed the river table ONCE per field instance — §23.2 (shared feeder so a deep
	   link into any flow scene has the rivers; setRiverTable is self-rendering). The
	   `seeded` guard is load-bearing: `tick++` reads tick, so without it the effect
	   would self-loop (the ch6 Constellation pattern). */
	let tick = $state(0);
	let seeded = false;
	$effect(() => {
		if (!field || !ch7 || seeded) return;
		seeded = true;
		ensureRiverTable(field, ch7);
		tick++; // getFlowLayout() is non-null only after a table is fed
	});

	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => tick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});

	/* Re-derive the centrelines ONE frame after each progress change. getFlowLayout()
	   reads the field's applied `flowLift`, which the shell's applyState sets in a
	   sibling effect on the same progress tick — so reading it synchronously races
	   and can leave the SVG centreline stale at the baseline while the GL ribbon has
	   already lifted. Bumping `tick` on the next rAF guarantees applyState ran first,
	   so the two SVG centrelines track the divergence reveal exactly. (tick += 1
	   inside rAF is untracked — no self-loop.) */
	let raf = 0;
	$effect(() => {
		void progress;
		cancelAnimationFrame(raf);
		raf = requestAnimationFrame(() => {
			tick += 1;
		});
		return () => cancelAnimationFrame(raf);
	});

	/** the two centrelines, projected to CSS px for the LIVE flowLift + season labels */
	const geom = $derived.by(() => {
		void tick;
		void progress; // re-project as the morph / flowLift reveal settles
		const f = field;
		const d = ch7;
		if (!f || !d) return null;
		const fl = f.getFlowLayout();
		if (!fl) return null;
		const gis = riverGis(f.data.groups);
		const toCss = (gi: number): { x: number; y: number } | null => {
			const c = fl.centres[gi];
			if (!c || Number.isNaN(c.x) || Number.isNaN(c.y)) return null;
			return f.projectToCss(c.x, c.y);
		};
		const line = (order: number[]): { x: number; y: number }[] =>
			order.map(toCss).filter((p): p is { x: number; y: number } => p !== null);
		const iplPts = line(gis.ipl);
		const wplPts = line(gis.wpl);

		// axis ticks (run-rate labels on the left edge)
		const ticks = fl.axisTicks.map((rate) => ({
			rate,
			css: f.projectToCss(fl.left, flowRateToY(fl, rate))
		}));
		// season labels along the bottom (a handful, evenly telling the timeline)
		const seasonMarks = [fl.minSeason, 2015, fl.forkSeason, fl.maxSeason].map((s) => ({
			season: s,
			css: f.projectToCss(flowSeasonToX(fl, s), fl.bottom)
		}));
		// the 2023 fork marker (a vertical rule)
		const forkTop = f.projectToCss(fl.forkX, fl.bottom + fl.height);
		const forkBot = f.projectToCss(fl.forkX, fl.bottom);

		// the gap polygon over the treatment years (IPL forward, WPL back)
		let gapPts = '';
		if (showGap) {
			const forkX = fl.forkX;
			const treat = (order: number[]): number[] =>
				order.filter((gi) => {
					const c = fl.centres[gi];
					return c && !Number.isNaN(c.x) && c.x >= forkX - 1e-6;
				});
			const iplT = line(treat(gis.ipl));
			const wplT = line(treat(gis.wpl));
			if (iplT.length && wplT.length) {
				const ring = [...iplT, ...wplT.slice().reverse()];
				gapPts = ring.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
			}
		}

		const toPoly = (pts: { x: number; y: number }[]): string =>
			pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');

		return {
			ipl: toPoly(iplPts),
			wpl: toPoly(wplPts),
			iplEnd: iplPts.at(-1) ?? null,
			wplEnd: wplPts.at(-1) ?? null,
			ticks,
			seasonMarks,
			forkTop,
			forkBot,
			gapPts,
			left: f.projectToCss(fl.left, fl.bottom).x
		};
	});

	const shown = $derived(reduced || on);
</script>

{#if geom && shown}
	<svg class="riverlines" class:faint aria-hidden="true">
		{#if showGap && geom.gapPts}
			<polygon class="gap" points={geom.gapPts} />
		{/if}
		<!-- the 2023 fork marker -->
		<line
			class="fork"
			x1={geom.forkTop.x}
			y1={geom.forkTop.y}
			x2={geom.forkBot.x}
			y2={geom.forkBot.y}
		/>
		{#if geom.wpl}
			<polyline class="river wpl" points={geom.wpl} />
		{/if}
		{#if geom.ipl}
			<polyline class="river ipl" points={geom.ipl} />
		{/if}
	</svg>

	<!-- axis + season + river labels (DOM, so they read crisply over the GL band) -->
	<div class="marks" aria-hidden="true">
		{#each geom.ticks as t (t.rate)}
			<span class="tick" style="left:{t.css.x.toFixed(1)}px; top:{t.css.y.toFixed(1)}px;">
				{t.rate}
			</span>
		{/each}
		{#each geom.seasonMarks as s (s.season)}
			<span class="season" style="left:{s.css.x.toFixed(1)}px; top:{s.css.y.toFixed(1)}px;">
				{s.season}
			</span>
		{/each}
		<span class="fork-tag" style="left:{geom.forkTop.x.toFixed(1)}px; top:{geom.forkTop.y.toFixed(1)}px;">
			2023 · the rule
		</span>
		{#if geom.iplEnd}
			<span class="river-tag ipl" style="left:{geom.iplEnd.x.toFixed(1)}px; top:{geom.iplEnd.y.toFixed(1)}px;">
				IPL
			</span>
		{/if}
		{#if geom.wplEnd}
			<span class="river-tag wpl" style="left:{geom.wplEnd.x.toFixed(1)}px; top:{geom.wplEnd.y.toFixed(1)}px;">
				WPL
			</span>
		{/if}
	</div>
{/if}

<!-- persistent orientation legend + always-on methods ⓘ (§0.4a). Top-left, clear
     of the top-right nav; the rivers sit centred + lower, so the legend stays off. -->
{#if legend}
	<div class="legend">
		<span class="lg-row"><span class="lg-swatch ipl"></span> the men's game (IPL)</span>
		<span class="lg-row"><span class="lg-swatch wpl"></span> the women's game (WPL)</span>
		<span class="lg-row lg-note">higher up means more runs an over</span>
		<span class="lg-row lg-note">the band's thickness is just for looks</span>
		<button class="lg-info" onclick={() => footnotesOpen.set(footnoteId)} aria-label="How the rivers are built">
			ⓘ how we built the rivers
		</button>
	</div>
{/if}

<style>
	.riverlines {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: visible;
	}

	.riverlines.faint {
		opacity: 0.34;
	}

	.river {
		fill: none;
		stroke-width: 2.4;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.river.ipl {
		stroke: #e8a33d;
		filter: drop-shadow(0 0 4px rgba(232, 163, 61, 0.55));
	}

	.river.wpl {
		stroke: #2ec4b6;
		filter: drop-shadow(0 0 4px rgba(46, 196, 182, 0.5));
	}

	.gap {
		fill: rgba(232, 163, 61, 0.14);
		stroke: none;
	}

	.fork {
		stroke: rgba(232, 236, 245, 0.4);
		stroke-width: 1.4;
		stroke-dasharray: 4 5;
		vector-effect: non-scaling-stroke;
	}

	.marks {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.tick,
	.season,
	.fork-tag,
	.river-tag {
		position: absolute;
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
	}

	.tick {
		transform: translate(-140%, -50%);
		font-size: 0.66rem;
		color: var(--ink-dim);
	}

	.season {
		transform: translate(-50%, 8px);
		font-size: 0.66rem;
		font-weight: 600;
		color: var(--ink-dim);
	}

	.fork-tag {
		transform: translate(-50%, -18px);
		font-size: 0.66rem;
		font-weight: 700;
		color: var(--ink);
	}

	.river-tag {
		transform: translate(10px, -50%);
		font-size: 0.72rem;
		font-weight: 800;
		letter-spacing: 0.04em;
	}

	.river-tag.ipl {
		color: #f0b85c;
	}

	.river-tag.wpl {
		color: #62d2c3;
	}

	/* bottom-left: the persistent orientation legend lives in the bottom letterbox
	   strip, clear of the top-left caption zone and the top-right nav */
	.legend {
		position: absolute;
		left: 2.5vw;
		bottom: 3vh;
		display: flex;
		flex-direction: column;
		gap: 0.28rem;
		padding: 0.5rem 0.7rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.82);
		border: 1px solid rgba(151, 161, 184, 0.25);
		max-width: min(16rem, 60vw);
	}

	.lg-row {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.lg-note {
		color: var(--ink);
		font-weight: 600;
		line-height: 1.3;
	}

	.lg-swatch {
		width: 0.85rem;
		height: 0.85rem;
		border-radius: 50%;
		flex: none;
	}

	.lg-swatch.ipl {
		background: #e8a33d;
		box-shadow: 0 0 8px rgba(232, 163, 61, 0.6);
	}

	.lg-swatch.wpl {
		background: #2ec4b6;
		box-shadow: 0 0 8px rgba(46, 196, 182, 0.6);
	}

	.lg-info {
		margin-top: 0.15rem;
		min-height: 44px;
		padding: 0.2rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.72rem;
		text-align: left;
		cursor: pointer;
	}

	.lg-info:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		/* on mobile the caption uses the bottom read-then-watch slot, so the legend
		   moves to the top-left (clear of the bottom caption and the top-right nav) */
		.legend {
			bottom: auto;
			top: 8vh;
			left: 2vw;
			padding: 0.4rem 0.55rem;
			gap: 0.2rem;
		}

		.lg-info {
			min-height: 40px;
		}

		.river-tag {
			font-size: 0.64rem;
		}
	}
</style>
