<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { loadCh1Data, fmt2, GHOST_BAND, BOLD_BAND, type Ch1Data } from './data';

	/**
	 * C1-4 — The out-rate, ball by ball (storyboard §3): the chapter's shock,
	 * a pure 2D scene (field dims behind; loop provably stopped). The y-axis
	 * is honesty-locked: zero-based, fixed 0-10%, never auto-scaled — the
	 * "lines sit on top of each other" claim may not be manufactured by scale.
	 * Tap a labeled ball tick (5/10/15/20) for who most defied the out-rate.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 50 / 200 */
	const step = $derived.by(() => {
		if (progress < 0.28) return 0;
		if (progress < 0.5) return 1;
		if (progress < 0.72) return 2;
		return 3;
	});

	let ch1 = $state<Ch1Data | null>(null);
	/* mobile legibility (MF2): a narrower viewBox + bigger user-unit type so
	   every axis/tick/end label renders >=11px EFFECTIVE at 320px and 375px. */
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

	/* ---- chart geometry (SVG user units; y fixed 0-10%) ---------------------- */
	// narrow: W=430 displayed at ~300px (320px viewport, 94vw) → scale ~0.70, so
	// FONT=17 user units → ~11.9px effective; at 375px → ~13.9px. Desktop keeps
	// the wider frame and 11px type (it renders at ~1:1).
	const W = $derived(narrow ? 430 : 640);
	const H = $derived(narrow ? 330 : 300);
	const ML = $derived(narrow ? 40 : 42);
	const MR = $derived(narrow ? 84 : 92);
	const MT = 16;
	const MB = $derived(narrow ? 50 : 38);
	const FONT = $derived(narrow ? 18 : 11);
	const plotW = $derived(W - ML - MR);
	const plotH = $derived(H - MT - MB);
	const Y_MAX = 10; // spec, not a choice (storyboard C1-4)

	const xAt = (ball: number): number => ML + ((ball - 1) / 29) * plotW;
	const yAt = (pct: number): number => MT + (1 - Math.min(pct, Y_MAX) / Y_MAX) * plotH;

	function line(vals: number[]): string {
		return vals.map((v, i) => `${xAt(i + 1).toFixed(1)},${yAt(v).toFixed(1)}`).join(' ');
	}

	/* right-edge label from the pipeline's axis convention (NOT hardcoded): the
	   per-ball curves end at exactly ball 30 (max_is_capped:false → "30"); only
	   the ignition wall caps and reads "30+". Every axis label traces here. */
	const axis = $derived(ch1 ? ch1.ball_index_axis : null);
	const maxLabel = $derived(axis ? axis.max_label : '30');

	/* text metrics that scale with FONT so labels stay centred at either size */
	const vc = $derived(FONT * 0.34); // vertical-centering nudge for baseline text
	const tickLabY = $derived(narrow ? 26 : 18); // tick-label drop below the axis

	const ghost = $derived(ch1 ? ch1.outrate.hazard_pct_by_ball_index[GHOST_BAND] : null);
	const bold = $derived(ch1 ? ch1.outrate.hazard_pct_by_ball_index[BOLD_BAND] : null);

	/* direct end-of-line labels, nudged apart when the ends nearly touch (the two
	   era lines end close together — that's the thesis — so the gap scales with
	   FONT to keep both readable on the larger mobile type) */
	const endLabels = $derived.by(() => {
		if (!ghost || !bold) return null;
		const half = (FONT + 2) / 2;
		let gy = yAt(ghost[29]);
		let by = yAt(bold[29]);
		if (Math.abs(gy - by) < half * 2) {
			const mid = (gy + by) / 2;
			gy = mid + (gy >= by ? half : -half);
			by = mid + (gy >= by ? -half : half);
		}
		return { gy, by };
	});

	const first10Early = $derived(ch1 ? ch1.outrate.first10[GHOST_BAND].hazard_pct : null);
	const first10Recent = $derived(ch1 ? ch1.outrate.first10[BOLD_BAND].hazard_pct : null);

	/* ---- defier interaction (adds names, never thesis) ------------------------ */
	// storyboard C1-4's labelled/tappable set; the pipeline ships defier lists
	// for all six (balls 1 and 3 — the sighter's heart — included).
	const TAP_BALLS = [1, 3, 5, 10, 15, 20];
	let selectedBall = $state<number | null>(null);

	const defierCard = $derived.by(() => {
		if (!ch1 || selectedBall === null) return null;
		const band = ch1.defiers.bands[BOLD_BAND];
		const list = band.by_ball_index[String(selectedBall)];
		const baseline = band.baselines[String(selectedBall)];
		if (!list || !baseline) return null;
		return { ball: selectedBall, top3: list.slice(0, 3), baseline };
	});

	/* labelled ticks match the tappable set (the right edge is drawn separately
	   with the artifact's max label). */
	const ticks = TAP_BALLS;
</script>

<div class="pin" class:reduced class:active>
	{#if ch1 && ghost && bold}
		<div class="chart-slot" class:shown={step >= 1}>
			<figure
				class="chart"
				aria-label="The out-rate, ball by ball, over balls 1 to {maxLabel} of the innings — IPL 2008-10 and 2023-26 on a fixed 0 to 10 percent scale"
			>
				<figcaption class="chart-title">The out-rate, ball by ball</figcaption>
				<svg viewBox="0 0 {W} {H}" style="font-size:{FONT}px" role="img" aria-hidden="true">
					<!-- fixed-scale gridlines: 0 / 2.5 / 5 / 7.5 / 10% (y honesty-locked) -->
					{#each [0, 2.5, 5, 7.5, 10] as g (g)}
						<line
							x1={ML}
							x2={ML + plotW}
							y1={yAt(g)}
							y2={yAt(g)}
							class="grid"
							class:major={g % 5 === 0}
						/>
						{#if g % 5 === 0}
							<text x={ML - 6} y={yAt(g) + vc} class="ylab">{g}%</text>
						{/if}
					{/each}

					<!-- x ticks (labelled = tappable) -->
					{#each ticks as t (t)}
						<line x1={xAt(t)} x2={xAt(t)} y1={yAt(0)} y2={yAt(0) + 5} class="tickmark" />
						<text x={xAt(t)} y={yAt(0) + tickLabY} class="xlab tappable">{t}</text>
					{/each}
					<!-- right edge: exactly ball 30 (not the wall's capped 30+) — artifact label -->
					<line x1={xAt(30)} x2={xAt(30)} y1={yAt(0)} y2={yAt(0) + 5} class="tickmark" />
					<text x={xAt(30)} y={yAt(0) + tickLabY} class="xlab">{maxLabel}</text>
					<text x={ML + plotW / 2} y={H - 5} class="axis-name">ball of the innings</text>

					<!-- 2008-10: the era ghost, always visible -->
					<polyline points={line(ghost)} class="curve ghost" />
					<text x={xAt(30) + 8} y={(endLabels?.gy ?? 0) + vc} class="endlab ghost-lab">
						2008-10
					</text>

					<!-- 2023-26: the bold line draws in at step 2 (the one change) -->
					<polyline
						points={line(bold)}
						class="curve bold"
						class:drawn={step >= 2}
						pathLength="1"
					/>
					{#if step >= 2}
						<text x={xAt(30) + 8} y={(endLabels?.by ?? 0) + vc} class="endlab bold-lab">
							2023-26
						</text>
					{/if}
				</svg>

				<!-- ≥44px tap targets on the labeled ticks (tap adds names, never thesis) -->
				{#each TAP_BALLS as t (t)}
					<button
						class="tick-tap"
						style="left:{(xAt(t) / W) * 100}%; top:{(yAt(0) / H) * 100}%;"
						onclick={() => (selectedBall = selectedBall === t ? null : t)}
						aria-label="Ball {t}: who most defied the out-rate"
					></button>
				{/each}
			</figure>
			<p class="hint">Tap ball 1 · 3 · 5 · 10 · 15 · 20 — who most defied the out-rate.</p>
		</div>
	{/if}

	<!-- caption steps -->
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>
					This is <strong>how often a batter gets out, ball by ball</strong>
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('out-rate')}
						aria-label="How we computed this">ⓘ</button
					>
					— the grey line is 2008-10. Out-rate on any early ball: about one in twenty.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Now 2023-26. <strong>The lines sit on top of each other.</strong> Across the first
					ten balls:
					<strong>
						{first10Early !== null ? fmt2(first10Early) : '—'}% then.
						{first10Recent !== null ? fmt2(first10Recent) : '—'}% now.
					</strong>
					All that extra attack — at no extra risk.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					That's the story of modern batting in one picture:
					<strong>not recklessness — skill.</strong> One honest note: this is a
					first-ten-balls fact. Later in the innings risk <em>did</em> rise —
					<strong>priced and paid on purpose. Chapter 5 publishes the price list.</strong>
				</p>
			</div>
		{/if}
	</div>

	<!-- defier mini card: bottom sheet, tap/keyboard, never hover -->
	{#if defierCard}
		<div class="defier-sheet" role="dialog" aria-label="Ball {defierCard.ball}: who most defied the out-rate">
			<div class="sheet-head">
				<p class="sheet-title">
					Ball {defierCard.ball}: who most defied the out-rate <span class="era">IPL 2023-26</span>
				</p>
				<button class="close" onclick={() => (selectedBall = null)} aria-label="Close">×</button>
			</div>
			<ol>
				{#each defierCard.top3 as d (d.name)}
					<li>
						<strong>{d.name}</strong> — made it past ball {defierCard.ball} in {d.survival_pct}%
						of innings · strike rate through balls 1–{defierCard.ball}: {d.sr_through_ball}
					</li>
				{/each}
			</ol>
			<p class="baseline">
				The league: {defierCard.baseline.survival_pct}% make it past ball {defierCard.ball} ·
				strike rate {defierCard.baseline.sr_through_ball}. Min 300 balls in the era.
			</p>
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

	/* ---- chart ---- */
	/* instant show/hide — appear-states never ride a transition */
	.chart-slot {
		position: absolute;
		top: 8vh;
		left: 50%;
		transform: translateX(-50%);
		width: min(680px, 94vw);
		opacity: 0;
	}

	.chart-slot.shown {
		opacity: 1;
	}

	.chart {
		position: relative;
		margin: 0;
		padding: 0.6rem 0.6rem 0.2rem;
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 12px;
		background: rgba(11, 14, 20, 0.72);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
	}

	.chart-title {
		font-size: 0.85rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		color: var(--ink);
		padding: 0.1rem 0.4rem 0.4rem;
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
	.axis-name {
		fill: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.ylab {
		text-anchor: end;
	}

	.xlab {
		text-anchor: middle;
	}

	.xlab.tappable {
		fill: var(--ink);
		text-decoration: underline;
		text-underline-offset: 3px;
	}

	.axis-name {
		text-anchor: middle;
		letter-spacing: 0.06em;
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
		stroke-dasharray: 1;
		stroke-dashoffset: 1;
		transition: stroke-dashoffset 1400ms ease;
	}

	.curve.bold.drawn {
		stroke-dashoffset: 0;
	}

	.pin.reduced .curve.bold,
	.pin.reduced .chart-slot {
		transition: none;
	}

	@media (prefers-reduced-motion: reduce) {
		.curve.bold,
		.chart-slot {
			transition: none;
		}
	}

	.endlab.ghost-lab {
		fill: #7a8298;
	}

	.endlab.bold-lab {
		fill: var(--ink);
		font-weight: 700;
	}

	.tick-tap {
		pointer-events: auto;
		position: absolute;
		width: 44px;
		height: 44px;
		transform: translate(-50%, -30%);
		border: none;
		border-radius: 50%;
		background: transparent;
		cursor: pointer;
	}

	.tick-tap:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: -4px;
	}

	.hint {
		margin: 0.45rem 0.2rem 0;
		font-size: 0.78rem;
		color: var(--ink-dim);
		text-align: center;
	}

	/* ---- captions ---- */
	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 10vh;
		max-width: min(32rem, 84vw);
	}

	.dagger {
		pointer-events: auto;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 44px;
		min-height: 44px;
		margin: -10px 0;
		padding: 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 1rem;
		cursor: pointer;
	}

	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* ---- defier bottom sheet ---- */
	.defier-sheet {
		pointer-events: auto;
		position: absolute;
		left: 50%;
		/* clears the shell's fixed "how we computed this" affordance (bottom 14px) */
		bottom: max(72px, calc(env(safe-area-inset-bottom) + 60px));
		transform: translateX(-50%);
		width: min(560px, 94vw);
		padding: 0.9rem 1.1rem 1rem;
		border-radius: 14px;
		border: 1px solid rgba(232, 236, 245, 0.16);
		background: rgba(11, 14, 20, 0.94);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		font-variant-numeric: tabular-nums;
		z-index: 5;
	}

	.sheet-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.5rem;
	}

	.sheet-title {
		margin: 0;
		font-size: 0.95rem;
		font-weight: 700;
	}

	.sheet-title .era {
		font-weight: 500;
		font-size: 0.75rem;
		color: var(--ink-dim);
		margin-left: 0.4rem;
		letter-spacing: 0.06em;
	}

	.close {
		flex: none;
		min-width: 44px;
		min-height: 44px;
		border: none;
		border-radius: 10px;
		background: rgba(232, 236, 245, 0.06);
		color: var(--ink);
		font-size: 1.3rem;
		cursor: pointer;
	}

	.close:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	ol {
		margin: 0.5rem 0 0;
		padding-left: 1.2rem;
	}

	li {
		margin: 0.3rem 0;
		font-size: 0.88rem;
		line-height: 1.45;
		color: var(--ink);
	}

	.baseline {
		margin: 0.55rem 0 0;
		font-size: 0.78rem;
		color: var(--ink-dim);
	}

	@media (max-width: 640px) {
		.chart-slot {
			top: 6vh;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			/* clear the shell's fixed "how we computed this" affordance (bottom 14px,
			   ~44px tall) — same formula the assembly scene uses (finding #10) */
			bottom: max(72px, calc(env(safe-area-inset-bottom) + 60px));
		}
	}
</style>
