<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { loadCh1Data, fmt1, GHOST_BAND, BOLD_BAND, type Ch1Data } from './data';

	/**
	 * C1-5 — The fireworks (storyboard §3): every IPL six lifts out of the
	 * wall (the chapter's one subset-highlight — uniform-driven, no re-sort;
	 * CONTRACT §3 keeps every Ch 1 layout on the wall), while the per-season
	 * stacking claim is carried by this 2D annotation-plane chart: 19 columns,
	 * height = that season's six count. Step 3's one change is the two-tone
	 * split — the top-10 hitters' slice vs everyone else's — on columns
	 * already on screen. WPL sixes are deliberately absent from the columns
	 * (framing rule); the caption names the omission.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 70 / 170 */
	const step = $derived.by(() => {
		if (progress < 0.44) return 0;
		if (progress < 0.62) return 1;
		if (progress < 0.8) return 2;
		return 3;
	});

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

	/**
	 * Balls-per-six headline pair ("a six every 21 balls → every 12").
	 * scenes/ch1.json carries no per-season legal-ball counts, so these two
	 * rounded figures trace to the storyboard §9 verified-number index
	 * (balls per six 20.8 → 11.7) — see the integration note in the report.
	 */
	const BALLS_PER_SIX_2008 = 21;
	const BALLS_PER_SIX_2026 = 12;

	const seasons = $derived(ch1 ? ch1.sixes.seasons.ipl : null);
	const aerialEarly = $derived(ch1 ? ch1.aerial.bands[GHOST_BAND] : null);
	const aerialRecent = $derived(ch1 ? ch1.aerial.bands[BOLD_BAND] : null);
	const p10First = $derived(seasons ? seasons[0] : null);
	const p10Last = $derived(seasons ? seasons[seasons.length - 1] : null);

	/* ---- columns chart geometry ---------------------------------------------- */
	const W = 640;
	const H = 250;
	const ML = 14;
	const MR = 14;
	const MT = 30;
	const MB = 28;
	const plotW = W - ML - MR;
	const plotH = H - MT - MB;

	const maxSixes = $derived(seasons ? Math.max(...seasons.map((s) => s.sixes)) : 1);

	interface Column {
		season: number;
		x: number;
		w: number;
		yTop: number;
		h: number;
		hTop10: number;
		labeled: boolean;
		sixes: number;
	}

	const columns = $derived.by((): Column[] => {
		if (!seasons) return [];
		const slot = plotW / seasons.length;
		const w = slot * 0.62;
		return seasons.map((s, i) => {
			const h = (s.sixes / maxSixes) * plotH;
			return {
				season: s.season,
				x: ML + i * slot + (slot - w) / 2,
				w,
				yTop: MT + plotH - h,
				h,
				hTop10: h * (s.top10_share_pct / 100),
				labeled: s.season === 2008 || s.season === 2023 || s.season === 2026,
				sixes: s.sixes
			};
		});
	});
</script>

<div class="pin" class:reduced class:active>
	{#if seasons}
		<div class="chart-slot" class:shown={step >= 1}>
			<figure class="chart" aria-label="IPL sixes per season, 2008 to 2026">
				<figcaption class="chart-title">
					IPL sixes per season
					{#if step >= 3}
						<span class="legend">bright slice = that season's top-10 hitters</span>
					{/if}
				</figcaption>
				<svg viewBox="0 0 {W} {H}" role="img" aria-hidden="true">
					{#each columns as c (c.season)}
						{#if step >= 3}
							<!-- two-tone: everyone else below, the specialists' slice on top -->
							<rect
								x={c.x}
								y={c.yTop + c.hTop10}
								width={c.w}
								height={c.h - c.hTop10}
								class="bar rest"
							/>
							<rect x={c.x} y={c.yTop} width={c.w} height={c.hTop10} class="bar top10" />
						{:else}
							<rect x={c.x} y={c.yTop} width={c.w} height={c.h} class="bar" />
						{/if}
						{#if c.labeled}
							<text x={c.x + c.w / 2} y={MT + plotH + 16} class="xlab">{c.season}</text>
							<text x={c.x + c.w / 2} y={c.yTop - 5} class="countlab">{c.sixes}</text>
						{/if}
					{/each}
					<line x1={ML} x2={ML + plotW} y1={MT + plotH} y2={MT + plotH} class="axis" />
				</svg>
			</figure>
		</div>
	{/if}

	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>
					<strong>Every IPL six ever hit, stacked by season.</strong> 2008: a six every
					{BALLS_PER_SIX_2008} balls. 2026: <strong>every {BALLS_PER_SIX_2026}.</strong>
				</p>
				<p class="note">
					The WPL's sixes stay on its shelf — its scoring engine gets its own beat, next.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Batters aren't just swinging more —
					<strong>
						more big swings land:
						{aerialEarly ? fmt1(aerialEarly.execution_pct) : '—'}% →
						{aerialRecent ? fmt1(aerialRecent.execution_pct) : '—'}%.
					</strong>
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('sixes')}
						aria-label="How we computed this">ⓘ</button
					>
					Braver <em>and</em> better.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					And the six stopped being a specialist's weapon.
					<strong>
						Players with ten-plus sixes in a season:
						{p10First ? p10First.players_10plus_sixes : '—'} in 2008 →
						{p10Last ? p10Last.players_10plus_sixes : '—'} in 2026.
					</strong>
					Watch the specialists' slice of every column shrink.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('sixes')}
						aria-label="How we computed this">ⓘ</button
					>
				</p>
			</div>
		{/if}
	</div>
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

	.chart-title .legend {
		font-weight: 500;
		font-size: 0.72rem;
		letter-spacing: 0.03em;
		color: var(--ink-dim);
		margin-left: 0.6rem;
	}

	svg {
		display: block;
		width: 100%;
		height: auto;
	}

	.axis {
		stroke: rgba(232, 236, 245, 0.25);
		stroke-width: 1;
	}

	/* six-ember hue is the sixes' identity color; the two-tone split is a
	   luminance difference within it, never a second hue */
	.bar {
		fill: #ff5d3a;
	}

	.bar.top10 {
		fill: #ffd0c4;
	}

	.bar.rest {
		fill: #99361f;
	}

	.xlab {
		font-size: 11px;
		fill: var(--ink-dim);
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	.countlab {
		font-size: 10px;
		fill: var(--ink-dim);
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

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

	@media (prefers-reduced-motion: reduce) {
		.chart-slot {
			transition: none;
		}
	}

	.pin.reduced .chart-slot {
		transition: none;
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
			bottom: max(9vh, calc(env(safe-area-inset-bottom) + 7vh));
		}
	}
</style>
