<script lang="ts">
	import type { IgnitionEraRow } from './payoff';

	/**
	 * The IPL/Neutral card's mini ignition strip (storyboard C1-7): strike rate
	 * on balls 1–10 → 11–20, early era as the ghost line, recent era in the
	 * team accent. Axis honesty: zero-based, FIXED 0–180 scale, ticks named on
	 * screen; direct end-of-line labels, no legend, nothing on hover.
	 */
	interface Props {
		early: IgnitionEraRow | null;
		recent: IgnitionEraRow | null;
		/** identity accent for the recent-era line (team hue, luminance-lifted) */
		accent: string;
	}
	let { early, recent, accent }: Props = $props();

	const W = 320;
	const H = 138;
	const X1 = 92;
	const X2 = 232;
	const TOP = 16;
	const BOTTOM = 104;
	const AXIS_X = 42;
	const MAX_SR = 180;

	const y = (sr: number): number =>
		BOTTOM - (Math.min(Math.max(sr, 0), MAX_SR) / MAX_SR) * (BOTTOM - TOP);

	interface StripLine {
		era: string;
		sr10: number;
		sr20: number;
		ghost: boolean;
	}

	const lines = $derived.by(() => {
		const out: StripLine[] = [];
		if (early !== null && early.sr_1_10 !== null && early.sr_11_20 !== null)
			out.push({ era: early.era, sr10: early.sr_1_10, sr20: early.sr_11_20, ghost: true });
		if (recent !== null && recent.sr_1_10 !== null && recent.sr_11_20 !== null)
			out.push({ era: recent.era, sr10: recent.sr_1_10, sr20: recent.sr_11_20, ghost: false });
		return out;
	});

	/** nudge a label pair apart when the values nearly coincide */
	function spread(a: number, b: number, min: number): [number, number] {
		if (Math.abs(a - b) >= min) return [a, b];
		const mid = (a + b) / 2;
		const half = min / 2;
		return a <= b ? [mid - half, mid + half] : [mid + half, mid - half];
	}

	const leftYs = $derived.by(() => {
		const ys = lines.map((l) => y(l.sr10) + 3);
		return ys.length === 2 ? spread(ys[0], ys[1], 12) : ys;
	});

	const rightYs = $derived.by(() => {
		const ys = lines.map((l) => y(l.sr20) + 3);
		return ys.length === 2 ? spread(ys[0], ys[1], 12) : ys;
	});

	const ariaLabel = $derived.by(() => {
		if (lines.length === 0) return 'Scoring strip: no data yet.';
		const parts = lines.map(
			(l) =>
				`${l.era}: ${l.sr10.toFixed(1)} runs per 100 on the first ten balls, ${l.sr20.toFixed(1)} on the next ten`
		);
		return `Runs per 100 balls, on a zero-to-180 scale. ${parts.join('; ')}.`;
	});
</script>

{#if lines.length > 0}
	<svg viewBox="0 0 {W} {H}" role="img" aria-label={ariaLabel}>
		<!-- zero-based fixed scale, both ticks named on screen -->
		<line class="gridline" x1={AXIS_X + 6} y1={y(0)} x2={X2 + 8} y2={y(0)} />
		<line class="gridline" x1={AXIS_X + 6} y1={y(MAX_SR)} x2={X2 + 8} y2={y(MAX_SR)} />
		<text class="tick" x={AXIS_X} y={y(0) + 3} text-anchor="end">0</text>
		<text class="tick" x={AXIS_X} y={y(MAX_SR) + 3} text-anchor="end">{MAX_SR}</text>
		<text class="axis-name" x={AXIS_X + 6} y={TOP - 6}>runs per 100 balls</text>

		{#each lines as l, i (l.era)}
			<line
				class="series"
				class:ghost={l.ghost}
				x1={X1}
				y1={y(l.sr10)}
				x2={X2}
				y2={y(l.sr20)}
				style:stroke={l.ghost ? undefined : accent}
			/>
			<circle
				class:ghost={l.ghost}
				cx={X1}
				cy={y(l.sr10)}
				r="3"
				style:fill={l.ghost ? undefined : accent}
			/>
			<circle
				class:ghost={l.ghost}
				cx={X2}
				cy={y(l.sr20)}
				r="3"
				style:fill={l.ghost ? undefined : accent}
			/>
			<text
				class="value"
				class:ghost-text={l.ghost}
				x={X1 - 8}
				y={leftYs[i]}
				text-anchor="end"
				style:fill={l.ghost ? undefined : accent}
			>
				{l.sr10.toFixed(1)}
			</text>
			<text
				class="era"
				class:ghost-text={l.ghost}
				x={X2 + 8}
				y={rightYs[i]}
				style:fill={l.ghost ? undefined : accent}
			>
				{l.era}
			</text>
		{/each}

		<text class="tick" x={X1} y={BOTTOM + 16} text-anchor="middle">balls 1–10</text>
		<text class="tick" x={X2} y={BOTTOM + 16} text-anchor="middle">11–20</text>
	</svg>
{/if}

<style>
	svg {
		display: block;
		width: 100%;
		height: auto;
	}

	.gridline {
		stroke: rgba(232, 236, 245, 0.14);
		stroke-width: 1;
	}

	.series {
		stroke-width: 2.25;
		stroke-linecap: round;
	}

	.series.ghost {
		stroke: var(--ink-dim);
		stroke-width: 1.5;
	}

	circle.ghost {
		fill: var(--ink-dim);
	}

	text {
		font-size: 10px;
		font-variant-numeric: tabular-nums;
		fill: var(--ink);
	}

	.tick,
	.axis-name {
		fill: var(--ink-dim);
	}

	.axis-name {
		font-size: 9px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.value {
		font-weight: 650;
	}

	.ghost-text {
		fill: var(--ink-dim);
	}
</style>
