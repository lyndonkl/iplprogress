<script lang="ts">
	import { linePath, yearX, type Ch10Data, type MetricKey } from './data';

	/**
	 * The seismograph strip (C10-3, shared SVG): a compact stack of two direct-
	 * labelled sparklines, the six-rate and runs-an-over, drawn 2008->2026 with the
	 * season each genuinely STEPS marked. It is the evidence panel under the crack:
	 * the reader sees the six-rate step at 2014 and the run rate step at 2023, so a
	 * crack on the ribbon is never an assertion taken on faith. The load-bearing
	 * "the break is real" read is position-on-a-common-scale (the line visibly
	 * steps), never a color read; each mini-line is direct-labelled so no legend.
	 */
	interface Props {
		d: Ch10Data;
	}
	let { d }: Props = $props();

	const seasons = $derived(d.seismograph.seasons);

	interface Panel {
		key: MetricKey;
		label: string;
		values: number[];
		breakYear: number;
		fmt: (v: number) => string;
	}

	const panels = $derived.by<Panel[]>(() => {
		const seis = d.seismograph;
		const fm = d.fault_map;
		const six = fm.metrics.find((m) => m.key === 'six_rate');
		const run = fm.metrics.find((m) => m.key === 'run_rate');
		return [
			{
				key: 'six_rate',
				label: seis.labels.six_rate,
				values: seis.series.six_rate,
				breakYear: six?.primary ?? 2014,
				fmt: (v: number) => v.toFixed(3)
			},
			{
				key: 'rpo',
				label: seis.labels.rpo,
				values: seis.series.rpo,
				breakYear: run?.primary ?? 2023,
				fmt: (v: number) => v.toFixed(2)
			}
		];
	});

	// internal viewBox coords (scene-authored, not field-anchored)
	const VW = 320;
	const PH = 92; // per-panel height
	const GAP = 14;
	const PADL = 8;
	const PADR = 8;
	const PADT = 20;
	const PADB = 16;

	function panelGeom(p: Panel, i: number) {
		const y0 = i * (PH + GAP);
		const x0 = PADL;
		const x1 = VW - PADR;
		const py0 = y0 + PADT;
		const py1 = y0 + PH - PADB;
		const vlo = Math.min(...p.values);
		const vhi = Math.max(...p.values);
		const pad = (vhi - vlo) * 0.12 || 1;
		const path = linePath(p.values, x0, x1, py0, py1, vlo - pad, vhi + pad);
		const bx = yearX(p.breakYear, seasons, x0, x1);
		const bi = seasons.indexOf(p.breakYear);
		const bv = bi >= 0 ? p.values[bi] : p.values[p.values.length - 1];
		const by = py1 - ((py1 - py0) * (bv - (vlo - pad))) / (vhi + pad - (vlo - pad));
		return { y0, x0, x1, py0, py1, path, bx, by, label: p.label, breakYear: p.breakYear };
	}

	const totalH = $derived(panels.length * (PH + GAP) - GAP);
</script>

<svg class="strip" viewBox={`0 0 ${VW} ${totalH}`} preserveAspectRatio="xMidYMid meet" aria-hidden="true">
	{#each panels as p, i (p.key)}
		{@const g = panelGeom(p, i)}
		<text class="p-label" x={g.x0} y={g.y0 + 12}>{g.label}</text>
		<!-- the step guide: where the game broke on this line -->
		<line class="brk" x1={g.bx.toFixed(1)} y1={g.py0 - 4} x2={g.bx.toFixed(1)} y2={g.py1 + 4} />
		<text class="brk-year" x={g.bx.toFixed(1)} y={g.py1 + 12}>{g.breakYear}</text>
		<path class="p-line" d={g.path} />
		<circle class="brk-dot" cx={g.bx.toFixed(1)} cy={g.by.toFixed(1)} r="3.2" />
	{/each}
</svg>

<style>
	.strip {
		width: 100%;
		height: 100%;
		overflow: visible;
	}

	.p-label {
		fill: var(--ink);
		font-size: 8.5px;
		font-weight: 700;
	}

	.p-line {
		fill: none;
		stroke: var(--ink);
		stroke-width: 1.6;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.brk {
		stroke: var(--gold, #e8b84b);
		stroke-width: 1;
		stroke-dasharray: 2 2;
		vector-effect: non-scaling-stroke;
		opacity: 0.8;
	}

	.brk-year {
		fill: var(--gold, #e8b84b);
		font-size: 7.5px;
		font-weight: 700;
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	.brk-dot {
		fill: var(--gold, #e8b84b);
		stroke: #0b0e14;
		stroke-width: 1;
	}
</style>
