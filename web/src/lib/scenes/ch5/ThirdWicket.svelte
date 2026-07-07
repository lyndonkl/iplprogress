<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { worthCell } from '$lib/field/layout';
	import { loadCh5Data, reAt, runs, eraYears, type Ch5Data } from './data';
	import WorthScaffold from './WorthScaffold.svelte';

	/**
	 * C5-6b — HERO 2, part two: the third wicket at half the old price. The grid
	 * holds under the RECENT table (the rise lens releases across this scene's
	 * entry, one uniform lerp — index.ts drives it). Two hero rings land on the
	 * over-7 cells at 2 down and 3 down, then the readout card carries the pair
	 * in both eras. ARTIFACT WINS (storyboard open call a, resolved): the locked
	 * engine surface prices the third wicket at 12.07 → 6.39, so the caption says
	 * HALF the old price, never the teaser's "~12 → ~0.4" (that probe band lives
	 * in the ch5-drift footnote, clearly labelled).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.5 ? 1 : 2);
	const BOUNDS = [0, 0.5, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

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

	const tw = $derived(ch5?.re_drift.third_wicket ?? null);
	const eraA = $derived(ch5 ? ch5.re_drift.era_a : 'ipl 2008-2010');
	const eraB = $derived(ch5 ? ch5.re_drift.era_b : 'ipl 2023-2026');
	const costEarly = $derived(tw ? tw.engine_fitted[eraA] : null);
	const costRecent = $derived(tw ? tw.engine_fitted[eraB] : null);

	const HERO_OVER = 6;
	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => {
				tick++;
			});
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	let seeded = false;
	$effect(() => {
		if (field && !seeded) {
			seeded = true;
			tick++;
		}
	});
	const rings = $derived.by(() => {
		void tick;
		const f = field;
		const wl = f?.getWorthLayout();
		if (!f || !wl) return null;
		const mk = (w: number) => {
			const c = worthCell(wl, HERO_OVER, w);
			const centre = f.projectToCss(c.x, c.y);
			const corner = f.projectToCss(c.x + wl.cellW / 2, c.y - wl.cellH / 2);
			return {
				x: centre.x,
				y: centre.y,
				rx: (corner.x - centre.x) * 1.25,
				ry: (corner.y - centre.y) * 1.25
			};
		};
		return { two: mk(2), three: mk(3) };
	});

	/* tap either ringed cell for its plain read on the DISPLAYED (recent) table
	   — the C5-5 tap-gloss grammar, adds depth, never carries the thesis */
	let tappedRing = $state<number | null>(null);
	const ringRead = $derived(
		tappedRing !== null && ch5 ? reAt(ch5.re_drift.re_b, HERO_OVER, tappedRing) : null
	);
</script>

<div class="pin" class:active>
	<WorthScaffold {field} />

	{#if rings}
		<button
			class="ring"
			style="left:{rings.two.x.toFixed(1)}px; top:{rings.two.y.toFixed(1)}px; width:{(
				rings.two.rx * 2
			).toFixed(1)}px; height:{(rings.two.ry * 2).toFixed(1)}px;"
			onclick={() => (tappedRing = tappedRing === 2 ? null : 2)}
			aria-label="Read the over-seven, two-down cell"
		>
			<span class="ring-lab">2 down</span>
		</button>
		<button
			class="ring"
			style="left:{rings.three.x.toFixed(1)}px; top:{rings.three.y.toFixed(1)}px; width:{(
				rings.three.rx * 2
			).toFixed(1)}px; height:{(rings.three.ry * 2).toFixed(1)}px;"
			onclick={() => (tappedRing = tappedRing === 3 ? null : 3)}
			aria-label="Read the over-seven, three-down cell"
		>
			<span class="ring-lab below">3 down</span>
		</button>
	{/if}

	{#if rings && tappedRing !== null && ringRead !== null && ch5}
		<div
			class="ring-read"
			style="left:{(tappedRing === 2 ? rings.two : rings.three).x.toFixed(1)}px; top:{(
				(tappedRing === 2 ? rings.two : rings.three).y +
				(tappedRing === 2 ? rings.two : rings.three).ry +
				10
			).toFixed(1)}px;"
		>
			over {HERO_OVER + 1}, {tappedRing} down: about {runs(ringRead)} runs usually still to come ({eraYears(
				ch5.re_drift.era_b
			)})
		</div>
	{/if}

	{#if (reduced || step >= 2) && costEarly !== null && costRecent !== null}
		<div class="readout">
			<span class="r-title">what the third wicket costs at over seven</span>
			<div class="r-pair">
				<div class="r-cell">
					<span class="r-era">{eraYears(eraA)}</span>
					<span class="r-val">about {runs(costEarly)} runs</span>
				</div>
				<span class="r-arrow" aria-hidden="true">→</span>
				<div class="r-cell">
					<span class="r-era">{eraYears(eraB)}</span>
					<span class="r-val now">about {runs(costRecent)} runs</span>
				</div>
			</div>
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					Now read two cells against each other. Over seven, two down, and over seven, three down.
					The gap between them is what losing your third wicket right there costs you.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Losing that third wicket used to cost about
					{costEarly !== null ? runs(costEarly) : 12} of the runs still coming. Today it costs
					about {costRecent !== null ? runs(costRecent) : 6}. The same mistake, at half the old
					price. Wickets did not stop mattering. They stopped costing what they used to.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-drift')}
						aria-label="How the two-cell subtraction works">ⓘ</button
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

	.ring {
		position: absolute;
		transform: translate(-50%, -50%);
		border: 2px solid #ffd166;
		border-radius: 10px;
		box-shadow: 0 0 12px rgba(255, 209, 102, 0.5);
		/* a tappable button (the C5-5 tap-gloss grammar): plain read on tap */
		pointer-events: auto;
		background: none;
		padding: 0;
		cursor: pointer;
	}

	.ring:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 3px;
	}

	.ring-read {
		position: absolute;
		transform: translateX(-50%);
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
		text-align: center;
	}

	.ring-lab {
		position: absolute;
		top: -1.3rem;
		left: 50%;
		transform: translateX(-50%);
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #ffd166;
		white-space: nowrap;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
	}

	.ring-lab.below {
		top: auto;
		bottom: -1.3rem;
	}

	.readout {
		position: absolute;
		top: 4.5vh;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.35rem;
		padding: 0.55rem 1rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.8);
		border: 1px solid rgba(151, 161, 184, 0.3);
	}

	.r-title {
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.r-pair {
		display: flex;
		align-items: center;
		gap: 0.9rem;
	}

	.r-cell {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.r-era {
		font-size: 0.68rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.r-val {
		font-size: 1.15rem;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
	}

	.r-val.now {
		color: #ffd166;
	}

	.r-arrow {
		color: var(--ink-dim);
		font-size: 1.1rem;
	}

	/* bottom-LEFT: the empty early-collapse corner (~150 balls), clear of the
	   ringed over-7 cells and never the death-collapse corner (see WorthOrient) */
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

		.readout {
			top: max(3vh, calc(env(safe-area-inset-top) + 52px));
		}
	}
</style>
