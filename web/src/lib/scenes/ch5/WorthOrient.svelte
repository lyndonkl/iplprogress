<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { worthCell } from '$lib/field/layout';
	import { loadCh5Data, buildWorthTables, reAt, runs, eraYears, type Ch5Data } from './data';
	import WorthScaffold from './WorthScaffold.svelte';

	/**
	 * C5-5 — THE CONTROLLING MORPH: the runs-left map (free field → `worth`).
	 * Every ball flies to the (over × wickets-down) cell its match was in when it
	 * was bowled; brightness is the price (expected runs still to come, the early
	 * era's surface first). This component FEEDS the four price tables ONCE
	 * (setWorthTables — the scene normalizes engine runs to luminance, CONTRACT
	 * §19.2: the era pair + WPL share one scale, the rise has its own), draws the
	 * destination-first scaffold, and offers the tap-a-cell plain read. The morph
	 * itself is declared in index.ts; the captions carry the point without any tap.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 170 / 300 → morph ends ≈ 0.57 */
	const step = $derived(progress < 0.6 ? 1 : 2);
	const BOUNDS = [0, 0.6, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	/* destination-first (storyboard C5-5): the empty 20×10 frame fades in AHEAD
	   of the points — as the flight starts, not at 0.4 — so step 1's axis gloss
	   always reads over a drawn frame and the balls land INTO it */
	const scaffoldOn = $derived(reduced || progress >= 0.08);

	let ch5 = $state<Ch5Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh5Data().then((d) => {
			if (alive) ch5 = d;
		});
		return () => {
			alive = false;
		};
	});

	/* feed the pricelens tables ONCE per (field, data) pair — §19.2 */
	let fed = $state(false);
	$effect(() => {
		const f = field;
		const d = ch5;
		if (!f || !d || fed) return;
		fed = true;
		const t = buildWorthTables(d);
		f.setWorthTables({ early: t.early, recent: t.recent, rise: t.rise, wpl: t.wpl });
	});

	/* ---- tap-a-cell plain read (adds depth, never carries the thesis) -------- */
	let tapRead = $state<{ over: number; wkts: number; x: number; y: number } | null>(null);
	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => {
				tick++;
				tapRead = null;
			});
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});

	/** the grid box in CSS px (projected corners), for the tap layer */
	const box = $derived.by(() => {
		void tick;
		void progress; // re-project as the morph settles
		const f = field;
		const wl = f?.getWorthLayout();
		if (!f || !wl) return null;
		const tl = f.projectToCss(wl.left, wl.bottom + wl.height);
		const br = f.projectToCss(wl.left + wl.width, wl.bottom);
		return { left: tl.x, top: tl.y, w: br.x - tl.x, h: br.y - tl.y };
	});

	function onTap(ev: MouseEvent): void {
		const f = field;
		const wl = f?.getWorthLayout();
		const b = box;
		if (!f || !wl || !b || !ch5) return;
		const el = ev.currentTarget as HTMLElement;
		const rect = el.getBoundingClientRect();
		const px = ev.clientX - rect.left;
		const py = ev.clientY - rect.top;
		const over = Math.min(19, Math.max(0, Math.floor((px / b.w) * 20)));
		const wkts = Math.min(9, Math.max(0, Math.floor((py / b.h) * 10)));
		const c = worthCell(wl, over, wkts);
		const css = f.projectToCss(c.x, c.y);
		tapRead = { over, wkts, x: css.x, y: css.y };
	}

	const tapValue = $derived(
		tapRead && ch5 ? reAt(ch5.re_drift.re_a, tapRead.over, tapRead.wkts) : null
	);
	const eraLabel = $derived(ch5 ? eraYears(ch5.re_drift.era_a) : '2008-2010');
</script>

<div class="pin" class:active>
	<WorthScaffold {field} on={scaffoldOn} />

	<!-- tap layer over the grid body only (touch-action pan-y keeps scroll alive) -->
	{#if box && (reduced || progress >= 0.55)}
		<button
			class="tap-layer"
			style="left:{box.left.toFixed(1)}px; top:{box.top.toFixed(1)}px; width:{box.w.toFixed(
				1
			)}px; height:{box.h.toFixed(1)}px;"
			onclick={onTap}
			aria-label="Read a cell of the runs-left map"
		></button>
	{/if}

	{#if tapRead && tapValue !== null}
		<div class="cell-read" style="left:{tapRead.x.toFixed(1)}px; top:{tapRead.y.toFixed(1)}px;">
			over {tapRead.over + 1}, {tapRead.wkts} down: about {runs(tapValue)} runs usually still to
			come ({eraLabel})
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					One more re-sort, the last big one for a while. Every ball flies to the spot its match
					was in when it was bowled. Across: the over of the innings, first to twentieth. Down:
					how many wickets had fallen, none at the top, nine at the bottom.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Brightness is the price. The brighter a cell, the more runs a batting side usually
					still gets from there. Top left glows brightest: the whole innings ahead, every wicket
					standing. This is <strong>the runs-left map,</strong> and right now it shows the
					league's first three seasons.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-worth')}
						aria-label="How a cell's price is computed">ⓘ</button
					>
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

	.tap-layer {
		pointer-events: auto;
		position: absolute;
		margin: 0;
		padding: 0;
		border: none;
		background: transparent;
		cursor: pointer;
		/* taps register, vertical scroll still belongs to the page */
		touch-action: pan-y pinch-zoom;
	}

	.tap-layer:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.cell-read {
		position: absolute;
		transform: translate(-50%, -130%);
		max-width: 16rem;
		padding: 0.4rem 0.65rem;
		border-radius: 10px;
		background: rgba(10, 14, 24, 0.88);
		border: 1px solid rgba(151, 161, 184, 0.35);
		font-size: 0.78rem;
		line-height: 1.35;
		color: var(--ink);
		pointer-events: none;
		font-variant-numeric: tabular-nums;
	}

	/* grid captions live in the BOTTOM-LEFT corner — the truly spent one:
	   overs 1-8 × wickets 6-9 hold ~150 of 316k balls (early collapses barely
	   exist), so the panel covers the emptiest cells in every lens. The
	   bottom-RIGHT corner is the death-collapse corner (~21k balls, and bright
	   in the rise lens) — never park a caption there. 12vw clears the
	   wickets-axis tick labels at every desktop width. */
	.caption-slot {
		position: absolute;
		left: 12vw;
		bottom: 9vh;
		max-width: min(24rem, 38vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	/* no invisible ⓘ tap target during the mobile clear gap */
	.caption-slot.gap .dagger {
		pointer-events: none;
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
		.caption-slot {
			right: auto;
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
