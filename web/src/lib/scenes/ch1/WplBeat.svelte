<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { loadCh1Data, fmt1, GHOST_BAND, BOLD_BAND, WPL_BAND, type Ch1Data } from './data';

	/**
	 * C1-6 — The WPL beat (storyboard §3): two clocks in one beat — the only
	 * public WPL narrative until R4. The shelf brightens to full (the brighten
	 * IS the beat; fieldState restores the stop it carried since C1-2) while
	 * the IPL dims one stop. The panel is a PEER-curve chart: same x as the
	 * wall and the strip, but a NEW y — strike rate, titled in-frame, with a
	 * visibly distinct frame treatment from the out-rate strip so the WPL's
	 * high line can never be read as "gets out more". Never "behind".
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 60 / 150 */
	const shown = $derived(progress >= 0.42);

	let ch1 = $state<Ch1Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh1Data().then((d) => {
			if (alive) ch1 = d;
		});
		return () => {
			alive = false;
		};
	});

	/* ---- strike-rate peer curves (y zero-based, fixed max — axis honesty) ---- */
	const W = 640;
	const H = 300;
	const ML = 48;
	const MR = 110;
	const MT = 18;
	const MB = 36;
	const plotW = W - ML - MR;
	const plotH = H - MT - MB;
	const Y_MAX = 200; // fixed; data max ≈ 180

	const xAt = (ball: number): number => ML + ((ball - 1) / 29) * plotW;
	const yAt = (sr: number): number => MT + (1 - Math.min(sr, Y_MAX) / Y_MAX) * plotH;

	function line(vals: number[]): string {
		return vals.map((v, i) => `${xAt(i + 1).toFixed(1)},${yAt(v).toFixed(1)}`).join(' ');
	}

	const ghost = $derived(ch1 ? ch1.ignition.sr_by_ball_index[GHOST_BAND] : null);
	const bold = $derived(ch1 ? ch1.ignition.sr_by_ball_index[BOLD_BAND] : null);
	const wpl = $derived(ch1 ? ch1.ignition.sr_by_ball_index[WPL_BAND] : null);

	/* direct end-of-line labels with collision nudging */
	const endLabels = $derived.by(() => {
		if (!ghost || !bold || !wpl) return null;
		const raw = [
			{ id: 'ghost', y: yAt(ghost[29]) },
			{ id: 'bold', y: yAt(bold[29]) },
			{ id: 'wpl', y: yAt(wpl[29]) }
		].sort((a, b) => a.y - b.y);
		for (let i = 1; i < raw.length; i++) {
			if (raw[i].y - raw[i - 1].y < 15) raw[i].y = raw[i - 1].y + 15;
		}
		const out: Record<string, number> = {};
		for (const r of raw) out[r.id] = r.y;
		return out;
	});

	const beat = $derived(ch1 ? ch1.wpl_beat : null);
	const foursWpl = $derived(beat ? beat.runs_from_fours_pct.wpl_2023_2026 : null);
	const foursIpl = $derived(beat ? beat.runs_from_fours_pct.ipl_2023_2026 : null);
	const BAR_MAX = 50; // shared zero-based scale for the engine pair
</script>

<div class="pin" class:reduced class:active>
	{#if ghost && bold && wpl}
		<div class="panel-slot" class:shown>
			<!-- deliberately distinct frame: teal edge + header band (≠ out-rate strip) -->
			<div class="panel">
				<p class="panel-title">Strike rate, ball by ball</p>
				<svg viewBox="0 0 {W} {H}" role="img" aria-label="Strike rate by ball of the innings: IPL 2008-10, IPL 2023-26, and the WPL as peers">
					{#each [0, 50, 100, 150, 200] as g (g)}
						<line
							x1={ML}
							x2={ML + plotW}
							y1={yAt(g)}
							y2={yAt(g)}
							class="grid"
							class:major={g % 100 === 0}
						/>
						{#if g % 100 === 0}
							<text x={ML - 6} y={yAt(g) + 3.5} class="ylab">{g}</text>
						{/if}
					{/each}
					<text x={12} y={MT + plotH / 2} class="yname" transform="rotate(-90 12 {MT + plotH / 2})">
						strike rate
					</text>

					{#each [1, 5, 10, 15, 20, 25, 30] as t (t)}
						<line x1={xAt(t)} x2={xAt(t)} y1={yAt(0)} y2={yAt(0) + 5} class="tickmark" />
						<text x={xAt(t)} y={yAt(0) + 18} class="xlab">{t}</text>
					{/each}
					<text x={ML + plotW / 2} y={H - 2} class="axis-name">ball of the innings</text>

					<polyline points={line(ghost)} class="curve ghost" />
					<polyline points={line(bold)} class="curve bold" />
					<polyline points={line(wpl)} class="curve wplline" />

					{#if endLabels}
						<text x={xAt(30) + 8} y={endLabels.ghost + 3.5} class="endlab ghost-lab">IPL 2008-10</text>
						<text x={xAt(30) + 8} y={endLabels.bold + 3.5} class="endlab bold-lab">IPL 2023-26</text>
						<text x={xAt(30) + 8} y={endLabels.wpl + 3.5} class="endlab wpl-lab">WPL</text>
					{/if}
				</svg>

				<!-- the engine pair: share of runs scored in fours (zero-based bars) -->
				{#if foursWpl !== null && foursIpl !== null}
					<div class="engine" role="img" aria-label="Share of runs scored in fours: WPL {fmt1(foursWpl)} percent, IPL 2023-26 {fmt1(foursIpl)} percent">
						<p class="engine-title">Share of runs scored in fours</p>
						<div class="bar-row">
							<span class="bar-name wpl-ink">WPL</span>
							<div class="bar-track">
								<div class="bar-fill wpl-fill" style="width:{(foursWpl / BAR_MAX) * 100}%"></div>
							</div>
							<span class="bar-val wpl-ink">{fmt1(foursWpl)}%</span>
						</div>
						<div class="bar-row">
							<span class="bar-name">IPL 2023-26</span>
							<div class="bar-track">
								<div class="bar-fill ipl-fill" style="width:{(foursIpl / BAR_MAX) * 100}%"></div>
							</div>
							<span class="bar-val">{fmt1(foursIpl)}%</span>
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}

	<!-- the two clocks share one caption card (single step, ~40 words) -->
	{#if beat}
		<div class="caption-slot" class:shown>
			<div class="scene-card">
				<p>
					<strong>The WPL is already moving — and not on the IPL's track.</strong>
					Four seasons in, its first-ten-balls strike rate —
					<strong class="wpl-ink">{fmt1(beat.first10_sr.wpl_2023_2026)}</strong> — sits where
					IPL 2008 stood. But the engine is new:
					<strong class="wpl-ink">{fmt1(beat.runs_from_fours_pct.wpl_2023_2026)}% of its runs come in fours.</strong>
					The modern IPL: {fmt1(beat.runs_from_fours_pct.ipl_2023_2026)}%.
				</p>
			</div>
		</div>
	{/if}
</div>

<style>
	/* viewport-fixed while active — one scene's captions on screen at a time */
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
	}

	.pin.active {
		visibility: visible;
	}

	/* instant show/hide — appear-states never ride a transition */
	.panel-slot {
		position: absolute;
		top: 6vh;
		left: 50%;
		transform: translateX(-50%);
		width: min(680px, 94vw);
		opacity: 0;
	}

	.panel-slot.shown {
		opacity: 1;
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 8vh;
		max-width: min(34rem, 84vw);
		opacity: 0;
	}

	.caption-slot.shown {
		opacity: 1;
	}

	/* frame treatment deliberately distinct from the out-rate strip:
	   teal left edge + tinted header band — this is a strike-rate panel */
	.panel {
		border: 1px solid rgba(46, 196, 182, 0.35);
		border-left: 4px solid var(--teal);
		border-radius: 12px;
		background: rgba(13, 20, 24, 0.82);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
		padding: 0 0.6rem 0.6rem;
		overflow: hidden;
	}

	.panel-title {
		margin: 0 -0.6rem 0.5rem;
		padding: 0.5rem 1rem;
		background: rgba(46, 196, 182, 0.1);
		font-size: 0.85rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		color: var(--ink);
	}

	svg {
		display: block;
		width: 100%;
		height: auto;
	}

	.grid {
		stroke: rgba(232, 236, 245, 0.07);
		stroke-width: 1;
	}

	.grid.major {
		stroke: rgba(232, 236, 245, 0.16);
	}

	.tickmark {
		stroke: rgba(232, 236, 245, 0.3);
		stroke-width: 1;
	}

	.ylab,
	.xlab,
	.endlab,
	.axis-name,
	.yname {
		font-size: 11px;
		fill: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.ylab {
		text-anchor: end;
	}

	.xlab,
	.axis-name {
		text-anchor: middle;
	}

	.yname {
		text-anchor: middle;
		letter-spacing: 0.08em;
	}

	.curve {
		fill: none;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	.curve.ghost {
		stroke: #7a8298;
		stroke-width: 1.8;
	}

	.curve.bold {
		stroke: var(--ink);
		stroke-width: 2.6;
	}

	.curve.wplline {
		stroke: var(--teal);
		stroke-width: 2.6;
	}

	.endlab.ghost-lab {
		fill: #7a8298;
	}

	.endlab.bold-lab {
		fill: var(--ink);
		font-weight: 700;
	}

	.endlab.wpl-lab {
		fill: var(--teal);
		font-weight: 700;
	}

	/* ---- engine pair bars ---- */
	.engine {
		padding: 0.4rem 0.4rem 0.1rem;
		font-variant-numeric: tabular-nums;
	}

	.engine-title {
		margin: 0 0 0.4rem;
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		color: var(--ink-dim);
	}

	.bar-row {
		display: grid;
		grid-template-columns: 6.2rem 1fr 3.4rem;
		align-items: center;
		gap: 0.6rem;
		margin: 0.3rem 0;
	}

	.bar-name {
		font-size: 0.8rem;
		color: var(--ink-dim);
	}

	.bar-track {
		height: 12px;
		border-radius: 6px;
		background: rgba(232, 236, 245, 0.07);
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		border-radius: 6px;
	}

	.wpl-fill {
		background: var(--teal);
	}

	.ipl-fill {
		background: #7a8298;
	}

	.bar-val {
		font-size: 0.82rem;
		color: var(--ink);
		text-align: right;
	}

	/* the WPL's numbers render in its hue — hue names whose number it is,
	   never a quantity */
	.wpl-ink {
		color: var(--teal);
	}

	@media (prefers-reduced-motion: reduce) {
		.panel-slot,
		.caption-slot {
			transition: none;
		}
	}

	.pin.reduced .panel-slot,
	.pin.reduced .caption-slot {
		transition: none;
	}

	@media (max-width: 640px) {
		.panel-slot {
			top: 4vh;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(7vh, calc(env(safe-area-inset-bottom) + 5vh));
		}
	}
</style>
