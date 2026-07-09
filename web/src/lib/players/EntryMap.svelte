<script lang="ts">
	/**
	 * Panel B - Entry Map (storyboard 9.2). A 10x6 heatmap: x = the 2-over window he
	 * walked in (overs 1-2 ... 19-20), y = wickets already down (0 ... 5+). A SINGLE-HUE
	 * luminance ramp on sqrt(count) (dark #3a2a1a -> light #ffcf8f, L* verified monotonic);
	 * empty cells are outline-only so absence never reads as a cold zero. The brightest
	 * cell is called out and translated to a role. Framing is "where his team sent him,"
	 * never "chose"; "brighter = more often, not better."
	 */
	import type { EntryMap } from './data';
	import { entryRolePhrase, fmtInt, overRangePhrase, wicketsPhrase } from './copy';

	let { map }: { map: EntryMap } = $props();

	const RAMP_LO = [58, 42, 26];
	const RAMP_HI = [255, 207, 143];
	function rampColor(count: number, maxCount: number): string {
		const t = maxCount > 0 ? Math.sqrt(count) / Math.sqrt(maxCount) : 0;
		const r = Math.round(RAMP_LO[0] + (RAMP_HI[0] - RAMP_LO[0]) * t);
		const g = Math.round(RAMP_LO[1] + (RAMP_HI[1] - RAMP_LO[1]) * t);
		const b = Math.round(RAMP_LO[2] + (RAMP_HI[2] - RAMP_LO[2]) * t);
		return `rgb(${r} ${g} ${b})`;
	}

	const CELL = 26;
	const GX = 22;
	const GY = 6;
	const GW = 10 * CELL;
	const GH = 6 * CELL;
	const W = GX + GW + 6;
	const H = GY + GH + 22;

	const cells = $derived(
		map.cells.map((c) => ({
			x: GX + c.xBin * CELL + 0.9,
			y: GY + c.yBin * CELL + 0.9,
			size: CELL - 1.8,
			count: c.count,
			xBin: c.xBin,
			yBin: c.yBin,
			fill: c.count > 0 ? rampColor(c.count, map.maxCount) : null,
			label: `${overRangePhrase(c.xBin * 2, c.xBin * 2 + 1)}, ${wicketsPhrase(c.yBin, c.yBin === 5)}`
		}))
	);
	const bright = $derived(map.brightest);
</script>

<figure class="entry">
	<figcaption>
		<p class="orient">
			Each square is one innings they began. Brighter means they walked in there more often, not that
			they did better.
		</p>
		{#if bright}
			<p class="point">
				Where they came in most: {overRangePhrase(bright.overLo, bright.overHi)}, {wicketsPhrase(
					bright.wickets,
					bright.wicketsPlus
				)}. {entryRolePhrase(bright.role)}
			</p>
			<p class="note">
				That cell is {fmtInt(bright.count)} of {fmtInt(map.totalInnings)} innings. Median entry: ball
				{fmtInt(map.medianEntryBall)}.
			</p>
		{/if}
	</figcaption>

	<svg
		viewBox="0 0 {W} {H}"
		role="img"
		aria-label="Heat map of the over and wickets-down they walked in at across their innings"
	>
		{#each cells as c (c.yBin * 10 + c.xBin)}
			<rect
				class="cell"
				class:filled={c.fill != null}
				x={c.x}
				y={c.y}
				width={c.size}
				height={c.size}
				rx="2"
				style={c.fill != null ? `fill:${c.fill}` : ''}
			>
				<title>{c.label}: {fmtInt(c.count)} innings</title>
			</rect>
		{/each}

		{#if bright}
			<rect
				class="bright-ring"
				x={GX + bright.xBin * CELL + 0.2}
				y={GY + bright.yBin * CELL + 0.2}
				width={CELL - 0.4}
				height={CELL - 0.4}
				rx="3"
			/>
		{/if}

		<!-- y anchors: 0 wickets at top, 5+ at bottom -->
		<text class="axis" x={GX - 3} y={GY + CELL * 0.62} text-anchor="end">0</text>
		<text class="axis" x={GX - 3} y={GY + GH - CELL * 0.4} text-anchor="end">5+</text>

		<!-- x anchors: powerplay end (left), death (right) -->
		<text class="axis" x={GX} y={GY + GH + 13} text-anchor="start">Powerplay</text>
		<text class="axis" x={GX + GW} y={GY + GH + 13} text-anchor="end">Death</text>
	</svg>
</figure>

<style>
	.entry {
		margin: 0;
	}
	figcaption {
		margin-bottom: 0.5rem;
	}
	.orient {
		margin: 0;
		font-size: 0.9rem;
		line-height: 1.45;
		color: var(--ink-dim);
	}
	.point {
		margin: 0.35rem 0 0;
		font-size: 0.95rem;
		line-height: 1.4;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	.note {
		margin: 0.3rem 0 0;
		font-size: 0.8rem;
		line-height: 1.4;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}
	svg {
		display: block;
		width: 100%;
		height: auto;
		max-width: 420px;
	}
	.cell {
		fill: transparent;
		stroke: rgba(232, 236, 245, 0.1);
		stroke-width: 0.6;
	}
	.cell.filled {
		stroke: rgba(11, 14, 20, 0.5);
	}
	.bright-ring {
		fill: none;
		stroke: var(--ink);
		stroke-width: 1.4;
	}
	.axis {
		fill: var(--ink-dim);
		font-size: 8px;
		font-variant-numeric: tabular-nums;
	}
</style>
