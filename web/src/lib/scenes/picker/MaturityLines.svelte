<script lang="ts">
	/**
	 * The WPL card's mandatory mini league-age sparkline pair (storyboard C1-7):
	 * run rate across league years 1–4, IPL falling vs WPL rising, on ONE fixed
	 * shared y-domain (axis honesty: the truncation is named by the on-screen
	 * 7 / 9 ticks). WPL line in the WPL hue — hue stays identity.
	 */
	interface Props {
		ipl: number[];
		wpl: number[];
	}
	let { ipl, wpl }: Props = $props();

	const W = 320;
	const H = 126;
	const LEFT = 58;
	const RIGHT = 258;
	const TOP = 16;
	const BOTTOM = 92;
	const D_MIN = 7;
	const D_MAX = 9;

	const n = $derived(Math.max(ipl.length, wpl.length, 2));
	const x = (i: number): number => LEFT + (i / (n - 1)) * (RIGHT - LEFT);
	const y = (v: number): number => {
		const c = Math.min(Math.max(v, D_MIN), D_MAX);
		return BOTTOM - ((c - D_MIN) / (D_MAX - D_MIN)) * (BOTTOM - TOP);
	};
	const path = (vals: number[]): string => vals.map((v, i) => `${x(i)},${y(v)}`).join(' ');

	function spread(a: number, b: number, min: number): [number, number] {
		if (Math.abs(a - b) >= min) return [a, b];
		const mid = (a + b) / 2;
		const half = min / 2;
		return a <= b ? [mid - half, mid + half] : [mid + half, mid - half];
	}

	const endYs = $derived.by(() => {
		const yi = ipl.length > 0 ? y(ipl[ipl.length - 1]) + 3 : BOTTOM;
		const yw = wpl.length > 0 ? y(wpl[wpl.length - 1]) + 3 : TOP;
		return spread(yi, yw, 12);
	});

	const ariaLabel = $derived.by(() => {
		const dir = (vals: number[]): string =>
			vals.length > 1 && vals[vals.length - 1] < vals[0] ? 'falling' : 'climbing';
		const f = (vals: number[]): string => vals.map((v) => v.toFixed(2)).join(', ');
		return (
			`Runs an over across league years one to four, both lines on one 7-to-9 scale. ` +
			`The IPL line is ${dir(ipl)}: ${f(ipl)}. The WPL line is ${dir(wpl)}: ${f(wpl)}.`
		);
	});
</script>

{#if ipl.length > 1 && wpl.length > 1}
	<svg viewBox="0 0 {W} {H}" role="img" aria-label={ariaLabel}>
		<!-- one shared scale; both domain ticks named on screen -->
		<line class="gridline" x1={LEFT - 4} y1={y(D_MIN)} x2={RIGHT + 8} y2={y(D_MIN)} />
		<line class="gridline" x1={LEFT - 4} y1={y(D_MAX)} x2={RIGHT + 8} y2={y(D_MAX)} />
		<text class="tick" x={LEFT - 10} y={y(D_MIN) + 3} text-anchor="end">{D_MIN}</text>
		<text class="tick" x={LEFT - 10} y={y(D_MAX) + 3} text-anchor="end">{D_MAX}</text>
		<text class="axis-name" x={LEFT - 4} y={TOP - 6}>runs an over</text>

		<polyline class="ipl" points={path(ipl)} />
		<polyline class="wpl" points={path(wpl)} />

		<text class="end ipl-text" x={RIGHT + 12} y={endYs[0]}>IPL</text>
		<text class="end wpl-text" x={RIGHT + 12} y={endYs[1]}>WPL</text>

		<text class="tick" x={x(0)} y={BOTTOM + 16} text-anchor="middle">year 1</text>
		<text class="tick" x={x(n - 1)} y={BOTTOM + 16} text-anchor="middle">year {n}</text>
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

	polyline {
		fill: none;
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.ipl {
		stroke: var(--ink-dim);
		stroke-width: 1.5;
	}

	.wpl {
		stroke: var(--teal);
		stroke-width: 2.25;
	}

	text {
		font-size: 10px;
		font-variant-numeric: tabular-nums;
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

	.end {
		font-weight: 700;
	}

	.ipl-text {
		fill: var(--ink-dim);
	}

	.wpl-text {
		fill: var(--teal);
	}
</style>
