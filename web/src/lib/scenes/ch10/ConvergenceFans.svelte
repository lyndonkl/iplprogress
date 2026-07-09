<script lang="ts">
	import { fmt1, type Ch10Data } from './data';

	/**
	 * The convergence clock (C10-7, shared SVG): three small multiples (men's run
	 * rate / WPL run rate / WPL six-hitting), each a SOLID measured line up to 2026,
	 * a salient vertical TODAY marker, and only THEN a gradient-faded fan, so it
	 * reads as "history, then forecast", not a broken chart. The men's crossing of
	 * ten an over is read as a bracketed WINDOW on the time axis (2027-2031, centred
	 * ~2028-29). The WPL run-rate fan is pinned to a FIXED present-day level (never a
	 * moving target). The WPL six-hitting fan is a DELIBERATE off-the-clock
	 * annotation, its target pushed off-screen, never a chart that failed and never
	 * "behind". A fan, not a confident line, is the honest encoding for a forecast.
	 */
	interface Props {
		d: Ch10Data;
	}
	let { d }: Props = $props();

	const VW = 190;
	const VH = 150;
	const PADL = 20;
	const PADR = 14;
	const PADT = 16;
	const PADB = 26;

	interface PanelGeom {
		key: string;
		title: string;
		xDom: [number, number];
		yDom: [number, number];
		measPath: string;
		todayX: number;
		todayLabel: number;
		// fan
		fanCentral?: string;
		fanBand?: string;
		fanTip?: { x: number; y: number };
		// men's gridline + bracket
		gridY?: number;
		gridLabel?: string;
		bracket?: { loX: number; hiX: number; cx: number; label: string };
		// wpl run-rate fixed target
		targetY?: number;
		targetLabel?: string;
		// wpl six off-the-clock
		offClockLabel?: string;
	}

	function xOf(year: number, xDom: [number, number]): number {
		return PADL + ((year - xDom[0]) / (xDom[1] - xDom[0])) * (VW - PADL - PADR);
	}
	function yOf(v: number, yDom: [number, number]): number {
		return VH - PADB - ((v - yDom[0]) / (yDom[1] - yDom[0])) * (VH - PADT - PADB);
	}
	function poly(seasons: number[], values: number[], xDom: [number, number], yDom: [number, number]): string {
		return seasons
			.map((s, i) => `${i === 0 ? 'M' : 'L'}${xOf(s, xDom).toFixed(1)},${yOf(values[i], yDom).toFixed(1)}`)
			.join(' ');
	}

	const panels = $derived.by<PanelGeom[]>(() => {
		const mens = d.convergence.mens;
		const wrr = d.convergence.wpl.run_rate;
		const wsix = d.convergence.wpl.six_rate;

		// --- men's run rate: cross ten, bracketed window ---
		const mXDom: [number, number] = [2008, 2032];
		const mYDom: [number, number] = [7, 10.6];
		const mLastX = xOf(2026, mXDom);
		const mLastY = yOf(mens.today.rpo, mYDom);
		const cx = xOf(mens.crosses_ten.central, mXDom);
		const cy = yOf(mens.target, mYDom);
		const loX = xOf(mens.crosses_ten.band_years[0], mXDom);
		const hiX = xOf(mens.crosses_ten.band_years[1], mXDom);
		const gy = yOf(mens.target, mYDom);
		const mens_panel: PanelGeom = {
			key: 'mens',
			title: "men's, runs an over",
			xDom: mXDom,
			yDom: mYDom,
			measPath: poly(mens.series.seasons, mens.series.rpo, mXDom, mYDom),
			todayX: mLastX,
			todayLabel: mens.today.season,
			fanCentral: `M${mLastX.toFixed(1)},${mLastY.toFixed(1)} L${cx.toFixed(1)},${cy.toFixed(1)}`,
			fanBand: `M${mLastX.toFixed(1)},${mLastY.toFixed(1)} L${loX.toFixed(1)},${gy.toFixed(1)} L${hiX.toFixed(1)},${gy.toFixed(1)} Z`,
			gridY: gy,
			gridLabel: 'ten an over',
			bracket: {
				loX,
				hiX,
				cx,
				label: `${mens.crosses_ten.band_years[0]} to ${mens.crosses_ten.band_years[1]}`
			}
		};

		// --- WPL run rate: rising toward the men's fixed present-day level ---
		const wXDom: [number, number] = [2023, 2035];
		const wYDom: [number, number] = [7.4, 10.2];
		const wLastX = xOf(2026, wXDom);
		const wLastY = yOf(wrr.rpo[wrr.rpo.length - 1], wYDom);
		const reachX = xOf(wrr.reaches_mens_2026_level, wXDom);
		const reachY = yOf(wrr.mens_2026_level, wYDom);
		const wgy = yOf(wrr.mens_2026_level, wYDom);
		// a widening band around the central rising line
		const bandTopY = yOf(wrr.mens_2026_level + 0.5, wYDom);
		const bandBotY = yOf(wrr.mens_2026_level - 0.5, wYDom);
		const wpl_rr_panel: PanelGeom = {
			key: 'wplrr',
			title: "women's, runs an over",
			xDom: wXDom,
			yDom: wYDom,
			measPath: poly(wrr.seasons, wrr.rpo, wXDom, wYDom),
			todayX: wLastX,
			todayLabel: 2026,
			fanCentral: `M${wLastX.toFixed(1)},${wLastY.toFixed(1)} L${reachX.toFixed(1)},${reachY.toFixed(1)}`,
			fanBand: `M${wLastX.toFixed(1)},${wLastY.toFixed(1)} L${xOf(2035, wXDom).toFixed(1)},${bandTopY.toFixed(1)} L${xOf(2035, wXDom).toFixed(1)},${bandBotY.toFixed(1)} Z`,
			targetY: wgy,
			targetLabel: `where the men's game sits today, ${fmt1(wrr.mens_2026_level)}`
		};

		// --- WPL six-hitting: off the clock, target off-screen ---
		const sXDom: [number, number] = [2023, 2031];
		const sYDom: [number, number] = [0.14, 0.32];
		const sLastX = xOf(2026, sXDom);
		const sLastY = yOf(wsix.six_per_over[wsix.six_per_over.length - 1], sYDom);
		const sEndX = xOf(2031, sXDom);
		const wpl_six_panel: PanelGeom = {
			key: 'wplsix',
			title: "women's, sixes an over",
			xDom: sXDom,
			yDom: sYDom,
			measPath: poly(wsix.seasons, wsix.six_per_over, sXDom, sYDom),
			todayX: sLastX,
			todayLabel: 2026,
			fanCentral: `M${sLastX.toFixed(1)},${sLastY.toFixed(1)} L${sEndX.toFixed(1)},${sLastY.toFixed(1)}`,
			fanBand: `M${sLastX.toFixed(1)},${(sLastY - 6).toFixed(1)} L${sEndX.toFixed(1)},${(sLastY - 12).toFixed(1)} L${sEndX.toFixed(1)},${(sLastY + 12).toFixed(1)} L${sLastX.toFixed(1)},${(sLastY + 6).toFixed(1)} Z`,
			fanTip: { x: sEndX, y: sLastY },
			offClockLabel: 'not foreseeable on four seasons'
		};

		return [mens_panel, wpl_rr_panel, wpl_six_panel];
	});

	function axisYears(p: PanelGeom): number[] {
		return [p.xDom[0], p.todayLabel];
	}
</script>

<div class="fans">
	{#each panels as p (p.key)}
		<figure class="fan">
			<figcaption>{p.title}</figcaption>
			<svg viewBox={`0 0 ${VW} ${VH}`} preserveAspectRatio="xMidYMid meet" aria-hidden="true">
				<defs>
					<linearGradient id={`fade-${p.key}`} x1="0" x2="1" y1="0" y2="0">
						<stop offset="0%" stop-color="var(--teal)" stop-opacity="0.28" />
						<stop offset="100%" stop-color="var(--teal)" stop-opacity="0.02" />
					</linearGradient>
				</defs>

				<!-- the men's "ten an over" gridline / the WPL fixed present-day level -->
				{#if p.gridY != null}
					<line class="grid" x1={PADL} y1={p.gridY.toFixed(1)} x2={VW - PADR} y2={p.gridY.toFixed(1)} />
					<text class="grid-l" x={PADL + 2} y={(p.gridY - 3).toFixed(1)}>{p.gridLabel}</text>
				{/if}
				{#if p.targetY != null}
					<line class="grid" x1={PADL} y1={p.targetY.toFixed(1)} x2={VW - PADR} y2={p.targetY.toFixed(1)} />
					<text class="grid-l" x={PADL + 2} y={(p.targetY - 3).toFixed(1)}>{p.targetLabel}</text>
				{/if}

				<!-- the fan (widening gradient-faded band), then the central dashed line -->
				{#if p.fanBand}
					<path class="fan-band" d={p.fanBand} fill={`url(#fade-${p.key})`} />
				{/if}
				{#if p.fanCentral}
					<path class="fan-central" d={p.fanCentral} />
				{/if}

				<!-- the solid measured history -->
				<path class="meas" d={p.measPath} />

				<!-- the TODAY marker -->
				<line class="today" x1={p.todayX.toFixed(1)} y1={PADT} x2={p.todayX.toFixed(1)} y2={VH - PADB} />
				<text class="today-l" x={(p.todayX - 2).toFixed(1)} y={PADT + 2}>today</text>

				<!-- the men's crossing window, drawn as a bracket on the time axis -->
				{#if p.bracket}
					<line class="brk" x1={p.bracket.loX.toFixed(1)} y1={VH - PADB} x2={p.bracket.hiX.toFixed(1)} y2={VH - PADB} />
					<line class="brk" x1={p.bracket.loX.toFixed(1)} y1={(VH - PADB - 3).toFixed(1)} x2={p.bracket.loX.toFixed(1)} y2={(VH - PADB + 3).toFixed(1)} />
					<line class="brk" x1={p.bracket.hiX.toFixed(1)} y1={(VH - PADB - 3).toFixed(1)} x2={p.bracket.hiX.toFixed(1)} y2={(VH - PADB + 3).toFixed(1)} />
					<circle class="brk-c" cx={p.bracket.cx.toFixed(1)} cy={(VH - PADB).toFixed(1)} r="2.4" />
					<text class="brk-l" x={p.bracket.cx.toFixed(1)} y={(VH - 4).toFixed(1)}>{p.bracket.label}</text>
				{/if}

				<!-- the WPL six-hitting off-the-clock arrow + label -->
				{#if p.offClockLabel && p.fanTip}
					<line class="off-arrow" x1={p.fanTip.x.toFixed(1)} y1={p.fanTip.y.toFixed(1)} x2={(VW - 2).toFixed(1)} y2={p.fanTip.y.toFixed(1)} />
					<path class="off-head" d={`M${(VW - 2).toFixed(1)},${p.fanTip.y.toFixed(1)} l-5,-3 l0,6 z`} />
					<text class="off-l" x={((PADL + VW) / 2).toFixed(1)} y={(VH - 4).toFixed(1)}>{p.offClockLabel}</text>
				{/if}

				<!-- the year axis: start / today -->
				{#each axisYears(p) as yr (yr)}
					<text class="axis-y" x={xOf(yr, p.xDom).toFixed(1)} y={(VH - PADB + 10).toFixed(1)}>{yr}</text>
				{/each}
			</svg>
		</figure>
	{/each}
</div>

<style>
	.fans {
		display: flex;
		gap: 0.7rem;
		width: 100%;
	}

	.fan {
		flex: 1;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		min-width: 0;
	}

	figcaption {
		font-size: 0.62rem;
		font-weight: 700;
		color: var(--ink);
	}

	svg {
		width: 100%;
		overflow: visible;
	}

	.meas {
		fill: none;
		stroke: var(--ink);
		stroke-width: 1.8;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.fan-central {
		fill: none;
		stroke: var(--teal);
		stroke-width: 1.4;
		stroke-dasharray: 3 2;
		vector-effect: non-scaling-stroke;
	}

	.fan-band {
		stroke: none;
	}

	.grid {
		stroke: rgba(232, 184, 75, 0.7);
		stroke-width: 1;
		stroke-dasharray: 4 3;
		vector-effect: non-scaling-stroke;
	}

	.grid-l {
		fill: var(--gold, #e8b84b);
		font-size: 6.5px;
		font-weight: 600;
	}

	.today {
		stroke: rgba(232, 236, 245, 0.55);
		stroke-width: 1;
		vector-effect: non-scaling-stroke;
	}

	.today-l {
		fill: var(--ink-dim);
		font-size: 6px;
		text-anchor: end;
	}

	.brk {
		stroke: var(--teal);
		stroke-width: 1.4;
		vector-effect: non-scaling-stroke;
	}

	.brk-c {
		fill: var(--teal);
	}

	.brk-l {
		fill: var(--teal);
		font-size: 7px;
		font-weight: 700;
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	.off-arrow {
		stroke: var(--ink-dim);
		stroke-width: 1.2;
		stroke-dasharray: 3 2;
		vector-effect: non-scaling-stroke;
	}

	.off-head {
		fill: var(--ink-dim);
	}

	.off-l {
		fill: var(--ink-dim);
		font-size: 6.5px;
		font-style: italic;
		text-anchor: middle;
	}

	.axis-y {
		fill: var(--ink-dim);
		font-size: 6.5px;
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	@media (max-width: 640px) {
		.fans {
			flex-direction: column;
		}
	}
</style>
