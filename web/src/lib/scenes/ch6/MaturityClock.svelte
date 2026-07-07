<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh6Data, fmt2, type Ch6Data } from './data';

	/**
	 * C6-5 — HERO 2: the League Maturity Clock (the recurring device gets its home
	 * chapter, paired with its dialect refusal so it never runs as a single clock).
	 * Wind both leagues back to their own season one and lay them on top: run rate
	 * against seasons-since-founding. The WPL reaches 8.54 an over in its fourth
	 * year where the men's game first crossed it in its fifteenth — but BOTH leagues
	 * opened near 8 an over, so this is a threshold-crossing coincidence, not a
	 * faster climb. The honest read (§2 corollary): quicker to that rate, still a
	 * different game by the ball (the men's 2022 rate at the men's 2008 style).
	 *
	 * A 2D annotation-plane scene over the dimmed held constellation (no second
	 * morph). The dial is a league-year stepper (interaction adds depth); the point
	 * lands in the caption without a tap. Reduced motion: the stepper is plain
	 * buttons and the whole curve is static-legible. Every number from ch6.json
	 * maturity_clock (artifact wins).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.38 ? 1 : progress < 0.7 ? 2 : 3);
	const BOUNDS = [0, 0.38, 0.7, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch6 = $state<Ch6Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh6Data().then((d) => {
			if (alive) ch6 = d;
		});
		return () => {
			alive = false;
		};
	});

	const mc = $derived(ch6?.maturity_clock ?? null);
	const wplYears = $derived(mc ? mc.wpl.league_years.length : 4); // 4
	const iplYear15Rr = $derived(mc?.headline.ipl_year15_rr ?? 8.54);
	const iplYear15Season = $derived(mc?.headline.ipl_year15_season ?? 2022);
	const iplYear15 = $derived(mc ? mc.ipl.seasons.indexOf(iplYear15Season) + 1 : 15);
	const wplYear4Rr = $derived(mc?.headline.wpl_year4_rr ?? 8.54);

	/* the STYLE twin (WPL 2026's nearest men's season by ball-for-ball mix), bound
	   from the C6-4 constellation read — powers the persistent dialect reminder so
	   the clock is never a single clock (§2 corollary) */
	const styleSeason = $derived(
		ch6?.constellation.two_truths.find((t) => t.wpl_season === 2026)?.outcome_mix_twin.ipl_season ??
			2008
	);

	/* the dial (interaction adds depth; default sits on the story's year) */
	let year = $state(4);
	$effect(() => {
		// keep the dial inside the IPL range once data lands
		if (mc && year > mc.ipl.league_years.length) year = mc.ipl.league_years.length;
	});
	const maxYear = $derived(mc ? mc.ipl.league_years.length : 19);
	const iplAt = $derived(mc ? (mc.ipl.rr[year - 1] ?? null) : null);
	const wplAt = $derived(mc && year <= wplYears ? (mc.wpl.rr[year - 1] ?? null) : null);

	/* ---- chart geometry (fixed viewBox; letterboxes with the panel) --------- */
	const VB_W = 340;
	const VB_H = 210;
	const PX0 = 34;
	const PX1 = VB_W - 46;
	const PY0 = 16;
	const PY1 = VB_H - 26;
	const Y_MIN = 7.0;
	const Y_MAX = 10.0;

	const xAt = (yr: number): number => PX0 + ((yr - 1) / (maxYear - 1)) * (PX1 - PX0);
	const yAt = (rr: number): number => PY1 - ((rr - Y_MIN) / (Y_MAX - Y_MIN)) * (PY1 - PY0);

	const iplLine = $derived(
		mc ? mc.ipl.rr.map((rr, i) => `${xAt(i + 1).toFixed(1)},${yAt(rr).toFixed(1)}`).join(' ') : ''
	);
	const wplLine = $derived(
		mc ? mc.wpl.rr.map((rr, i) => `${xAt(i + 1).toFixed(1)},${yAt(rr).toFixed(1)}`).join(' ') : ''
	);
	const yTicks = [7, 8, 9, 10];
</script>

<div class="pin" class:active>
	{#if mc}
		<div class="panel">
			<p class="overline">the maturity clock · both leagues, on their own age</p>
			<svg class="chart" viewBox="0 0 {VB_W} {VB_H}" role="img"
				aria-label="Run rate against seasons since each league began. The WPL reaches 8.54 an over in four years; the IPL took fifteen.">
				<!-- y grid + labels -->
				{#each yTicks as t (t)}
					<line class="grid" x1={PX0} y1={yAt(t)} x2={PX1} y2={yAt(t)} />
					<text class="ax-y" x={PX0 - 6} y={yAt(t) + 3}>{t}</text>
				{/each}

				<!-- the 8.54 reference: WPL year-4 across to IPL year-15 -->
				<line
					class="ref"
					x1={xAt(wplYears)}
					y1={yAt(wplYear4Rr)}
					x2={xAt(iplYear15)}
					y2={yAt(iplYear15Rr)}
				/>
				<text class="ref-lbl" x={xAt(iplYear15)} y={yAt(iplYear15Rr) - 6}>
					{fmt2(iplYear15Rr)} an over
				</text>

				<!-- the two league curves -->
				<polyline class="ipl-line" points={iplLine} />
				<polyline class="wpl-line" points={wplLine} />

				<!-- the dial guide + the two reads at the selected year -->
				<line class="dial" x1={xAt(year)} y1={PY0} x2={xAt(year)} y2={PY1} />
				{#if iplAt !== null}
					<circle class="dot ipl" cx={xAt(year)} cy={yAt(iplAt)} r="4" />
				{/if}
				{#if wplAt !== null}
					<circle class="dot wpl" cx={xAt(year)} cy={yAt(wplAt)} r="4" />
				{/if}

				<!-- x endpoints -->
				<text class="ax-x" x={xAt(1)} y={PY1 + 16}>year 1</text>
				<text class="ax-x end" x={xAt(maxYear)} y={PY1 + 16}>year {maxYear}</text>

				<!-- axis-break marker: the rate axis starts at 7, not 0 (honest scale) -->
				<text class="ax-break" x={PX0 - 6} y={PY1 + 1}>⌇</text>
			</svg>

			<p class="axis-note">the rate scale starts at 7 an over, not zero</p>

			<div class="reads">
				<span class="rd ipl">IPL year {year}: {iplAt !== null ? fmt2(iplAt) : 'not played yet'}</span>
				<span class="rd wpl"
					>WPL year {year}: {wplAt !== null ? fmt2(wplAt) : 'not played yet'}</span
				>
			</div>

			<!-- the persistent dialect reminder: this clock is never read alone (§2) -->
			<p class="dialect-note">
				Same rate as the men's {iplYear15Season}, still the men's {styleSeason} by the ball.
			</p>

			<div class="dial-row">
				<button
					class="step"
					aria-label="earlier league year"
					disabled={year <= 1}
					onclick={() => (year = Math.max(1, year - 1))}>−</button
				>
				<input
					class="slider"
					type="range"
					min="1"
					max={maxYear}
					bind:value={year}
					aria-label="league year"
				/>
				<button
					class="step"
					aria-label="later league year"
					disabled={year >= maxYear}
					onclick={() => (year = Math.min(maxYear, year + 1))}>+</button
				>
			</div>

			{#if year === wplYears}
				<p class="snap">
					The WPL got to {fmt2(wplYear4Rr)} an over in four years. The IPL took until year {iplYear15}
					({iplYear15Season}).
				</p>
			{/if}

			<button
				class="dagger"
				onclick={() => footnotesOpen.set('ch6-maturity')}
				aria-label="How run rate and league year are defined">ⓘ how we count this</button
			>
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					Same picture, different question. Wind both leagues back to their own first season and
					lay them on top of each other. Run rate up the side, seasons since day one across the
					bottom. Gold is the IPL, teal the WPL.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Slide to the WPL's fourth year: {fmt2(wplYear4Rr)} runs an over. The men's game first hit
					that in its <strong>fifteenth</strong> season, the women in their fourth.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Quicker to that rate, sure, but not a faster climb. Both leagues opened near 8 an over.
					What counts is now: the WPL reaches the men's {iplYear15Season} rate while still playing
					the men's {styleSeason} game.
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
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	.pin.active {
		visibility: visible;
	}

	.panel {
		pointer-events: auto;
		width: min(38rem, 92vw);
		background: rgba(11, 14, 20, 0.72);
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 14px;
		padding: 1rem 1.2rem 1.1rem;
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
	}

	.overline {
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: var(--gold);
		margin: 0 0 0.55rem;
	}

	.chart {
		width: 100%;
		height: auto;
	}

	.grid {
		stroke: rgba(151, 161, 184, 0.16);
		stroke-width: 1;
		vector-effect: non-scaling-stroke;
	}

	.ax-y {
		fill: var(--ink-dim);
		font-size: 9px;
		text-anchor: end;
		font-variant-numeric: tabular-nums;
	}

	.ax-x {
		fill: var(--ink-dim);
		font-size: 9px;
		text-anchor: start;
	}

	.ax-x.end {
		text-anchor: end;
	}

	.ref {
		stroke: rgba(232, 236, 245, 0.55);
		stroke-width: 1.3;
		stroke-dasharray: 4 4;
		vector-effect: non-scaling-stroke;
	}

	.ref-lbl {
		fill: var(--ink);
		font-size: 9px;
		font-weight: 700;
		text-anchor: end;
	}

	.ipl-line {
		fill: none;
		stroke: #e8a33d;
		stroke-width: 2.2;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.wpl-line {
		fill: none;
		stroke: #2ec4b6;
		stroke-width: 2.6;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.dial {
		stroke: rgba(232, 236, 245, 0.35);
		stroke-width: 1;
		vector-effect: non-scaling-stroke;
	}

	.dot {
		stroke: #0b0e14;
		stroke-width: 1.5;
	}

	.dot.ipl {
		fill: #e8a33d;
	}

	.dot.wpl {
		fill: #2ec4b6;
	}

	.ax-break {
		fill: var(--ink-dim);
		font-size: 11px;
		text-anchor: end;
	}

	.axis-note {
		margin: 0.2rem 0 0;
		font-size: 0.64rem;
		color: var(--ink-dim);
		font-style: italic;
	}

	.dialect-note {
		margin: 0.45rem 0 0;
		font-size: 0.78rem;
		line-height: 1.4;
		color: #62d2c3;
		font-weight: 600;
		font-variant-numeric: tabular-nums;
	}

	.reads {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		margin-top: 0.5rem;
		font-size: 0.82rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.rd.ipl {
		color: var(--gold);
	}

	.rd.wpl {
		color: #62d2c3;
	}

	.dial-row {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		margin-top: 0.7rem;
	}

	.step {
		min-width: 44px;
		min-height: 44px;
		border-radius: 10px;
		border: 1px solid rgba(151, 161, 184, 0.45);
		background: none;
		color: var(--ink);
		font-size: 1.2rem;
		font-weight: 700;
		cursor: pointer;
	}

	.step:disabled {
		opacity: 0.35;
		cursor: default;
	}

	.slider {
		flex: 1;
		accent-color: #2ec4b6;
		min-height: 44px;
		cursor: pointer;
	}

	.step:focus-visible,
	.slider:focus-visible,
	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.snap {
		margin: 0.6rem 0 0;
		font-size: 0.86rem;
		line-height: 1.45;
		color: var(--ink);
		font-weight: 600;
		font-variant-numeric: tabular-nums;
	}

	.dagger {
		display: inline-block;
		margin-top: 0.6rem;
		min-height: 44px;
		padding: 0.3rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.78rem;
		cursor: pointer;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 6vh;
		max-width: min(23rem, 34vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.pin {
			place-items: start center;
			padding-top: 8vh;
		}

		/* keep the tall dial clear of the bottom read-beat caption (§C2): cap the
		   panel and let it scroll internally rather than run under the caption */
		.panel {
			max-height: 66vh;
			overflow-y: auto;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(3vh, calc(env(safe-area-inset-bottom) + 10px));
		}
	}
</style>
