<script lang="ts">
	import { yearX, type Ch10Data, type FaultLine, type MetricKey } from './data';

	/**
	 * The fault map (C10-4, shared SVG): a subway map of change. Each metric is one
	 * horizontal line on an EQUAL-SPACED year axis (so the fine modern order the
	 * ribbon cannot resolve is read HERE), each break a station dot, and co-breaking
	 * years a single ringed "big-station" interchange glyph. The two load-bearing
	 * lines (sixes and scoring) are drawn ADJACENT, so the "sixes broke about five
	 * years before scoring" read is a horizontal-distance read (colorblind-robust),
	 * never a hue read. revealLevel 1 = the two hero lines + the distance beat; 2 =
	 * all five lines + the 2023 interchange glyph.
	 */
	interface Props {
		d: Ch10Data;
		/** 1 = hero lines (distance beat) · 2 = all lines + interchanges */
		revealLevel: number;
	}
	let { d, revealLevel }: Props = $props();

	// hero lines (six, run) FIRST + adjacent, then the rest
	const LANE_ORDER: MetricKey[] = ['six_rate', 'run_rate', 'wide_rate', 'boundary_rate', 'dot_rate'];

	const VW = 360;
	const VH = 210;
	const PADL = 58;
	const PADR = 22;
	const PADT = 20;
	const LANE_GAP = 34;

	const seasons = $derived(d.fault_map.seasons);
	const x0 = PADL;
	const x1 = VW - PADR;

	interface Lane {
		key: MetricKey;
		label: string;
		y: number;
		hero: boolean;
		primary: number;
		stations: { year: number; x: number; primary: boolean }[];
	}

	const lanes = $derived.by<Lane[]>(() => {
		const heroSet = new Set(d.fault_map.hero_lines);
		return LANE_ORDER.map((key, i) => {
			const m = d.fault_map.metrics.find((x) => x.key === key) as FaultLine;
			return {
				key,
				label: m.label,
				y: PADT + i * LANE_GAP,
				hero: heroSet.has(key),
				primary: m.primary,
				stations: m.stations.map((s) => ({
					year: s.year,
					x: yearX(s.year, seasons, x0, x1),
					primary: s.year === m.primary
				}))
			};
		});
	});

	const visibleLanes = $derived(revealLevel >= 2 ? lanes : lanes.filter((l) => l.hero));

	// the distance beat: sixes primary vs scoring primary on adjacent lanes
	const gap = $derived(d.fault_map.order_gap);
	const sixLane = $derived(lanes.find((l) => l.key === 'six_rate') ?? null);
	const runLane = $derived(lanes.find((l) => l.key === 'run_rate') ?? null);
	const gapGeom = $derived.by(() => {
		if (!sixLane || !runLane) return null;
		const sx = yearX(gap.six_year, seasons, x0, x1);
		const rx = yearX(gap.scoring_year, seasons, x0, x1);
		const midY = (sixLane.y + runLane.y) / 2;
		return { sx, rx, midY };
	});

	interface Glyph {
		year: number;
		x: number;
		yTop: number;
		yBot: number;
		label: string;
	}
	const interchanges = $derived.by<Glyph[]>(() => {
		if (revealLevel < 2) return [];
		return d.fault_map.interchanges.map((ic) => {
			const ys = ic.metrics
				.map((mk) => lanes.find((l) => l.key === mk)?.y)
				.filter((y): y is number => y != null);
			return {
				year: ic.year,
				x: yearX(ic.year, seasons, x0, x1),
				yTop: Math.min(...ys),
				yBot: Math.max(...ys),
				label: ic.label
			};
		});
	});
</script>

<svg class="subway" viewBox={`0 0 ${VW} ${VH}`} preserveAspectRatio="xMidYMid meet" aria-hidden="true">
	<!-- the equal-spaced year axis: 2008 / mid / now -->
	{#each [seasons[0], seasons[Math.floor(seasons.length / 2)], seasons[seasons.length - 1]] as yr (yr)}
		<text class="axis-year" x={yearX(yr, seasons, x0, x1).toFixed(1)} y={VH - 6}>{yr}</text>
	{/each}

	<!-- the interchange connectors (behind the lines) -->
	{#each interchanges as g (g.year)}
		<line class="ic-conn" x1={g.x.toFixed(1)} y1={g.yTop.toFixed(1)} x2={g.x.toFixed(1)} y2={g.yBot.toFixed(1)} />
	{/each}

	<!-- the subway lines + station dots -->
	{#each visibleLanes as l (l.key)}
		<text class="lane-label" x={x0 - 8} y={(l.y + 3).toFixed(1)}>{l.label}</text>
		<line class="lane" class:hero={l.hero} x1={x0} y1={l.y.toFixed(1)} x2={x1} y2={l.y.toFixed(1)} />
		{#each l.stations as st (st.year)}
			<circle class="station" class:primary={st.primary} cx={st.x.toFixed(1)} cy={l.y.toFixed(1)} r={st.primary ? 4 : 2.8} />
		{/each}
	{/each}

	<!-- the ringed interchange glyph (real transit convention: many lines meet here) -->
	{#each interchanges as g (g.year)}
		<circle class="ic-ring" cx={g.x.toFixed(1)} cy={((g.yTop + g.yBot) / 2).toFixed(1)} r="8" />
		<text class="ic-year" x={g.x.toFixed(1)} y={(g.yBot + 14).toFixed(1)}>{g.year}</text>
	{/each}

	<!-- the distance beat: sixes broke about five years before scoring -->
	{#if gapGeom}
		<line
			class="gap-line"
			x1={gapGeom.sx.toFixed(1)}
			y1={gapGeom.midY.toFixed(1)}
			x2={gapGeom.rx.toFixed(1)}
			y2={gapGeom.midY.toFixed(1)}
		/>
		<circle class="gap-end" cx={gapGeom.sx.toFixed(1)} cy={gapGeom.midY.toFixed(1)} r="2" />
		<circle class="gap-end" cx={gapGeom.rx.toFixed(1)} cy={gapGeom.midY.toFixed(1)} r="2" />
		<text class="gap-label" x={((gapGeom.sx + gapGeom.rx) / 2).toFixed(1)} y={(gapGeom.midY - 5).toFixed(1)}>
			about {gap.years} years
		</text>
	{/if}
</svg>

<style>
	.subway {
		width: 100%;
		height: 100%;
		overflow: visible;
	}

	.axis-year {
		fill: var(--ink-dim);
		font-size: 8px;
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	.lane-label {
		fill: var(--ink);
		font-size: 8px;
		font-weight: 600;
		text-anchor: end;
	}

	.lane {
		stroke: rgba(151, 161, 184, 0.55);
		stroke-width: 2;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.lane.hero {
		stroke: var(--teal);
		stroke-width: 3;
	}

	.station {
		fill: rgba(232, 236, 245, 0.85);
		stroke: #0b0e14;
		stroke-width: 1;
	}

	.station.primary {
		fill: var(--gold, #e8b84b);
	}

	.ic-conn {
		stroke: rgba(232, 236, 245, 0.5);
		stroke-width: 1.5;
		vector-effect: non-scaling-stroke;
	}

	.ic-ring {
		fill: none;
		stroke: #fff;
		stroke-width: 2;
	}

	.ic-year {
		fill: var(--ink);
		font-size: 8px;
		font-weight: 700;
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	.gap-line {
		stroke: var(--gold, #e8b84b);
		stroke-width: 1.4;
		stroke-dasharray: 3 2;
		vector-effect: non-scaling-stroke;
	}

	.gap-end {
		fill: var(--gold, #e8b84b);
	}

	.gap-label {
		fill: var(--gold, #e8b84b);
		font-size: 8px;
		font-weight: 700;
		text-anchor: middle;
	}
</style>
