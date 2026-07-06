<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh2Data, fmt2, IPL_EARLY, IPL_MODERN, type Ch2Data, type TaxBand } from './data';

	/**
	 * C2-6 — The one survivor (the SOLE coda: New-Batter Tax). Worm-space dims
	 * behind; loop provably stopped. The aftershock strip (2D): per era, the team
	 * run rate over the 10 balls after a wicket sits as a DIP below the day's
	 * going rate. The 2008 dip and the 2026 dip sit close together — the later one
	 * a touch DEEPER (it never healed). Main flow carries only the tax pair
	 * (−1.13 → −1.30, from the artifact); the incoming-batter SR jump is footnote-
	 * only by default (§7 should-fix). Honest reframe: the tax DEEPENED — which
	 * strengthens the thesis that the revolution couldn't kill this cost.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.34) return 1;
		if (progress < 0.68) return 2;
		return 3;
	});
	const bothOn = $derived(reduced || step >= 2);

	// mobile "read, then watch" (CONTRACT §17): caption fades in for the read beat,
	// then to a clear gap so the aftershock (post-wicket dip) strip is unobstructed.
	// Desktop + reduced motion → 1 (persistent caption, byte-identical).
	const BOUNDS = [0, 0.34, 0.68, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch2 = $state<Ch2Data | null>(null);
	let narrow = $state(false);
	onMount(() => {
		let alive = true;
		loadCh2Data().then((d) => {
			if (alive) ch2 = d;
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

	const early = $derived<TaxBand | null>(ch2 ? ch2.newbatter.tax[IPL_EARLY] : null);
	const modern = $derived<TaxBand | null>(ch2 ? ch2.newbatter.tax[IPL_MODERN] : null);
	const taxEarly = $derived(early ? early.tax_rpo_below_par : null);
	const taxModern = $derived(modern ? modern.tax_rpo_below_par : null);

	/* ---- the aftershock strip (2D, zero-based RPO) --------------------------- */
	const W = $derived(narrow ? 420 : 560);
	const H = $derived(narrow ? 300 : 300);
	const ML = $derived(narrow ? 44 : 48);
	const MR = 18;
	const MT = 18;
	const MB = $derived(narrow ? 50 : 40);
	const FONT = $derived(narrow ? 17 : 11);
	const plotW = $derived(W - ML - MR);
	const plotH = $derived(H - MT - MB);
	const Y_MAX = 10; // zero-based RPO; modern par ≈ 9.2

	const yAt = (rpo: number): number => MT + (1 - Math.min(rpo, Y_MAX) / Y_MAX) * plotH;
	const vc = $derived(FONT * 0.34);
	const colX = (i: number): number => ML + plotW * (i === 0 ? 0.28 : 0.72);
	const barW = $derived(plotW * 0.17);

	interface Col {
		label: string;
		par: number;
		actual: number;
		tax: number;
		x: number;
	}
	const cols = $derived<Col[]>(
		early && modern
			? [
					{ label: 'early seasons', par: early.par_rpo, actual: early.actual_rpo, tax: early.tax_rpo_below_par, x: colX(0) },
					{ label: 'now', par: modern.par_rpo, actual: modern.actual_rpo, tax: modern.tax_rpo_below_par, x: colX(1) }
				]
			: []
	);

	let tapped = $state(false);
</script>

<div class="pin" class:reduced class:active>
	{#if ch2 && cols.length}
		<div class="chart-slot">
			<figure class="chart" aria-label="Team run rate in the 10 balls after a wicket, versus the day's going rate, early seasons and now, on a zero-based runs-per-over scale">
				<figcaption class="chart-title">The 10 balls after a wicket, vs the day's going rate</figcaption>
				<svg viewBox="0 0 {W} {H}" style="font-size:{FONT}px" role="img" aria-hidden="true">
					{#each [0, 2, 4, 6, 8, 10] as g (g)}
						<line x1={ML} x2={ML + plotW} y1={yAt(g)} y2={yAt(g)} class="grid" class:major={g === 0} />
						{#if g % 2 === 0}
							<text x={ML - 6} y={yAt(g) + vc} class="ylab">{g}</text>
						{/if}
					{/each}
					<text x={14} y={MT + plotH / 2} class="yname" transform="rotate(-90 14 {MT + plotH / 2})">runs per over</text>

					{#each cols as c, i (c.label)}
						<!-- the day's going rate: a light cap line the dip falls from -->
						<line x1={c.x - barW} x2={c.x + barW} y1={yAt(c.par)} y2={yAt(c.par)} class="par-cap" class:on={i === 0 ? true : bothOn} />
						<text x={c.x} y={yAt(c.par) - 6} class="cap-lab" class:on={i === 0 ? true : bothOn}>going rate {fmt2(c.par)}</text>
						<!-- the dip: post-wicket rate falls below the going rate (the tax) -->
						<rect
							x={c.x - barW}
							y={yAt(c.par)}
							width={barW * 2}
							height={Math.max(0, yAt(c.actual) - yAt(c.par))}
							class="dip"
							class:on={i === 0 ? true : bothOn}
						/>
						<line x1={c.x - barW} x2={c.x + barW} y1={yAt(c.actual)} y2={yAt(c.actual)} class="actual-cap" class:on={i === 0 ? true : bothOn} />
						<text x={c.x} y={yAt(0) + (narrow ? 26 : 18)} class="xlab">{c.label}</text>
						<text x={c.x} y={(yAt(c.par) + yAt(c.actual)) / 2 + vc} class="tax-lab" class:on={i === 0 ? true : bothOn}>−{fmt2(c.tax)}</text>
					{/each}
				</svg>
				<button class="strip-tap" onclick={() => (tapped = !tapped)} aria-label="Read the exact rates per era">
					{tapped ? 'hide the exact rates' : 'the exact rates →'}
				</button>
				{#if tapped}
					<div class="tap-read">
						{#each cols as c (c.label)}
							<p><strong>{c.label}:</strong> the day's rate {fmt2(c.par)}, and {fmt2(c.actual)} right after a wicket. A stall of {fmt2(c.tax)} runs an over.</p>
						{/each}
					</div>
				{/if}
			</figure>
		</div>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					Everything in this chapter is something the revolution <strong>killed.</strong> Here is the
					one thing it couldn't. When a wicket falls, <strong>the scoring stalls</strong>. The next
					ten balls dip below the day's rate.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					And the dip <strong>didn't shrink. If anything it got deeper.</strong> It was
					<strong>−{taxEarly !== null ? fmt2(taxEarly) : '-'}</strong> runs an over below the going
					rate in the early seasons, and <strong>−{taxModern !== null ? fmt2(taxModern) : '-'}</strong>
					now. The new man walks in swinging harder than ever, and the scoring still stalls the
					moment he arrives.
					<button class="dagger" onclick={() => footnotesOpen.set('new-batter-tax')} aria-label="How we measured the tax">ⓘ</button>
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					The batter changed, but the cost didn't budge. <strong>Some costs are baked into the game,
					not the player.</strong> A new man at the crease, a field reset. Built into the game, not a
					failure of nerve.
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
	}

	.pin.active {
		visibility: visible;
	}

	.chart-slot {
		position: absolute;
		top: 7vh;
		left: 50%;
		transform: translateX(-50%);
		width: min(580px, 94vw);
	}

	.chart {
		position: relative;
		margin: 0;
		padding: 0.5rem 0.6rem 0.2rem;
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 12px;
		background: rgba(11, 14, 20, 0.74);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
	}

	.chart-title {
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		color: var(--ink);
		padding: 0.1rem 0.3rem 0.35rem;
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

	.ylab,
	.xlab,
	.yname,
	.cap-lab,
	.tax-lab {
		fill: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.ylab {
		text-anchor: end;
	}

	.xlab,
	.yname,
	.cap-lab,
	.tax-lab {
		text-anchor: middle;
	}

	.yname {
		letter-spacing: 0.08em;
	}

	.par-cap {
		stroke: #8f9ab4;
		stroke-width: 2;
		opacity: 0;
		transition: opacity 500ms ease;
	}

	.actual-cap {
		stroke: var(--ink);
		stroke-width: 2.4;
		opacity: 0;
		transition: opacity 500ms ease;
	}

	.dip {
		fill: rgba(255, 138, 76, 0.28);
		stroke: none;
		opacity: 0;
		transition: opacity 500ms ease;
	}

	.par-cap.on,
	.actual-cap.on,
	.dip.on,
	.cap-lab.on,
	.tax-lab.on {
		opacity: 1;
	}

	.cap-lab {
		opacity: 0;
		transition: opacity 500ms ease;
	}

	.tax-lab {
		opacity: 0;
		fill: #ff8a4c;
		font-weight: 700;
		transition: opacity 500ms ease;
	}

	.pin.reduced .par-cap,
	.pin.reduced .actual-cap,
	.pin.reduced .dip,
	.pin.reduced .cap-lab,
	.pin.reduced .tax-lab {
		transition: none;
	}

	@media (prefers-reduced-motion: reduce) {
		.par-cap,
		.actual-cap,
		.dip,
		.cap-lab,
		.tax-lab {
			transition: none;
		}
	}

	.strip-tap {
		pointer-events: auto;
		display: inline-flex;
		align-items: center;
		min-height: 44px;
		margin: 0.1rem 0 0.1rem 0.3rem;
		padding: 0 0.2rem;
		border: none;
		background: none;
		color: var(--teal);
		font: inherit;
		font-size: 0.8rem;
		cursor: pointer;
	}

	.strip-tap:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.tap-read {
		padding: 0 0.3rem 0.3rem;
	}

	.tap-read p {
		margin: 0.2rem 0;
		font-size: 0.8rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 10vh;
		max-width: min(30rem, 84vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
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

	@media (max-width: 640px) {
		.chart-slot {
			top: 5vh;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(72px, calc(env(safe-area-inset-bottom) + 60px));
		}
	}
</style>
