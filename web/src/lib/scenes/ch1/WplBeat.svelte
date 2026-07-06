<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
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
	// the panel + the single caption appear once the field morph has settled
	const CAPTION_SHOWN = 0.42;
	const shown = $derived(progress >= CAPTION_SHOWN);

	// mobile "read, then watch" (CONTRACT §17): this scene has ONE caption step,
	// spanning [CAPTION_SHOWN, 1). It fades in for the read beat, then clears to a
	// gap so the reader watches the strike-rate panel + engine bars unobstructed.
	// Returns 1 on desktop / reduced motion (the persistent caption is unchanged).
	const reveal = $derived(captionReveal(progress, CAPTION_SHOWN, 1, { reduced }));

	let ch1 = $state<Ch1Data | null>(null);
	/* mobile legibility (MF2): narrower viewBox + bigger user-unit type so the
	   three end labels, ticks and axis names clear 11px effective at 320/375px. */
	let narrow = $state(false);
	onMount(() => {
		let alive = true;
		loadCh1Data().then((d) => {
			if (alive) ch1 = d;
		});
		const mql = window.matchMedia('(max-width: 640px)');
		const sync = (): void => {
			narrow = mql.matches;
		};
		sync();
		mql.addEventListener('change', sync);
		return () => {
			alive = false;
			mql.removeEventListener('change', sync);
		};
	});

	/* ---- strike-rate peer curves (y zero-based, fixed max — axis honesty) ---- */
	const W = $derived(narrow ? 430 : 640);
	const H = $derived(narrow ? 320 : 300);
	const ML = $derived(narrow ? 44 : 48);
	const MR = $derived(narrow ? 96 : 110); // room for the "2023-26" end label at FONT 18
	const MT = 18;
	const MB = $derived(narrow ? 52 : 36);
	const FONT = $derived(narrow ? 18 : 11);
	const plotW = $derived(W - ML - MR);
	const plotH = $derived(H - MT - MB);
	const Y_MAX = 200; // fixed; data max ≈ 180

	const xAt = (ball: number): number => ML + ((ball - 1) / 29) * plotW;
	const yAt = (sr: number): number => MT + (1 - Math.min(sr, Y_MAX) / Y_MAX) * plotH;

	function line(vals: number[]): string {
		return vals.map((v, i) => `${xAt(i + 1).toFixed(1)},${yAt(v).toFixed(1)}`).join(' ');
	}

	/* text metrics that scale with FONT */
	const vc = $derived(FONT * 0.34);
	const tickLabY = $derived(narrow ? 26 : 18);

	/* right-edge label from the pipeline's axis convention (per-ball curves end
	   at exactly ball 30 → "30"; only the wall caps at "30+"). Not hardcoded. */
	const axis = $derived(ch1 ? ch1.ball_index_axis : null);
	const maxLabel = $derived(axis ? axis.max_label : '30');

	/* end labels: drop the "IPL " prefix on the narrow frame to fit (hue already
	   carries league — grey/ink are IPL, teal is WPL) */
	const iplGhostLab = $derived(narrow ? '2008-10' : 'IPL 2008-10');
	const iplBoldLab = $derived(narrow ? '2023-26' : 'IPL 2023-26');

	const ticks = [1, 5, 10, 15, 20, 25];

	const ghost = $derived(ch1 ? ch1.ignition.sr_by_ball_index[GHOST_BAND] : null);
	const bold = $derived(ch1 ? ch1.ignition.sr_by_ball_index[BOLD_BAND] : null);
	const wpl = $derived(ch1 ? ch1.ignition.sr_by_ball_index[WPL_BAND] : null);

	/* direct end-of-line labels with collision nudging (gap scales with FONT so
	   the three labels never overlap on the larger mobile type) */
	const endLabels = $derived.by(() => {
		if (!ghost || !bold || !wpl) return null;
		const gap = FONT + 2;
		const raw = [
			{ id: 'ghost', y: yAt(ghost[29]) },
			{ id: 'bold', y: yAt(bold[29]) },
			{ id: 'wpl', y: yAt(wpl[29]) }
		].sort((a, b) => a.y - b.y);
		for (let i = 1; i < raw.length; i++) {
			if (raw[i].y - raw[i - 1].y < gap) raw[i].y = raw[i - 1].y + gap;
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
				<p class="panel-title">Scoring rate, ball by ball</p>
				<svg
					viewBox="0 0 {W} {H}"
					style="font-size:{FONT}px"
					role="img"
					aria-label="Scoring rate in runs per 100 balls, ball by ball, over balls 1 to {maxLabel} of the innings, on a zero-based fixed scale. IPL 2008-10, IPL 2023-26, and the WPL side by side"
				>
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
							<text x={ML - 6} y={yAt(g) + vc} class="ylab">{g}</text>
						{/if}
					{/each}
					<text x={12} y={MT + plotH / 2} class="yname" transform="rotate(-90 12 {MT + plotH / 2})">
						runs per 100 balls
					</text>

					{#each ticks as t (t)}
						<line x1={xAt(t)} x2={xAt(t)} y1={yAt(0)} y2={yAt(0) + 5} class="tickmark" />
						<text x={xAt(t)} y={yAt(0) + tickLabY} class="xlab">{t}</text>
					{/each}
					<!-- right edge: exactly ball 30 (not the wall's capped 30+) — artifact label -->
					<line x1={xAt(30)} x2={xAt(30)} y1={yAt(0)} y2={yAt(0) + 5} class="tickmark" />
					<text x={xAt(30)} y={yAt(0) + tickLabY} class="xlab">{maxLabel}</text>
					<text x={ML + plotW / 2} y={H - 5} class="axis-name">ball of the innings</text>

					<polyline points={line(ghost)} class="curve ghost" />
					<polyline points={line(bold)} class="curve bold" />
					<polyline points={line(wpl)} class="curve wplline" />

					{#if endLabels}
						<text x={xAt(30) + 8} y={endLabels.ghost + vc} class="endlab ghost-lab">{iplGhostLab}</text>
						<text x={xAt(30) + 8} y={endLabels.bold + vc} class="endlab bold-lab">{iplBoldLab}</text>
						<text x={xAt(30) + 8} y={endLabels.wpl + vc} class="endlab wpl-lab">WPL</text>
					{/if}
				</svg>

				<!-- the engine pair: share of runs scored in fours (zero-based bars) -->
				{#if foursWpl !== null && foursIpl !== null}
					<div class="engine" role="img" aria-label="Share of runs that come from fours, bars on a fixed 0 to 50 percent scale. WPL {fmt1(foursWpl)} percent, IPL 2023-26 {fmt1(foursIpl)} percent">
						<p class="engine-title">
							Share of runs that come from fours <span class="scale-note">(0 to 50% scale)</span>
						</p>
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
		<div class="caption-slot" class:shown style:--reveal={reveal}>
			<div class="scene-card">
				<p>
					<strong>The WPL is going its own way.</strong>
					Just four seasons old, over its first ten balls it scores at
					<strong class="wpl-ink">{fmt1(beat.first10_sr.wpl_2023_2026)}</strong> runs per 100 balls. That is right where
					the IPL sat back in 2008. But it gets its runs differently.
					<strong class="wpl-ink">{fmt1(beat.runs_from_fours_pct.wpl_2023_2026)}% of them come from fours.</strong>
					In today's IPL it is {fmt1(beat.runs_from_fours_pct.ipl_2023_2026)}%.
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
		/* mobile read-then-watch (CONTRACT §17); resolves to 1 on desktop / SSR */
		opacity: var(--reveal, 1);
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

	/* font-size is inherited from the <svg> inline style (reactive user units —
	   MF2 scales type up on the narrow viewBox); never hardcode it here */
	.ylab,
	.xlab,
	.endlab,
	.axis-name,
	.yname {
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

	/* names the bars' track so the WPL's 46.8% can't read as "nearly all" (#13) */
	.scale-note {
		font-weight: 500;
		letter-spacing: 0.02em;
		opacity: 0.85;
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
			/* clear the shell's fixed "how we computed this" affordance (finding #10) */
			bottom: max(72px, calc(env(safe-area-inset-bottom) + 60px));
		}
	}
</style>
