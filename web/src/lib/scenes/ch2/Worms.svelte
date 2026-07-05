<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { loadCh2Data, type Ch2Data, type WormSeason } from './data';
	import { wormFrame, wormPolyline, wormEnd } from './wormsvg';

	/**
	 * C2-2 — The worm field (storyboard §3): the chapter's ONE controlling morph
	 * (free field → worm-space). Every ball flies into a low-alpha density haze —
	 * x = balls faced (1 → 60+), y = cumulative innings runs. Destination-first
	 * scaffold (axes + a faint guide where the par worm lands) fades in ahead of
	 * the points. Three caption steps: axes teach → the par worm draws (it
	 * sprints) → the anchor worm draws in its dedicated FIGURE CHANNEL (dark
	 * casing + brighter stroke, the highest-contrast mark in the frame — higher
	 * than par, §0.1). The par/anchor worms are SVG on the annotation plane,
	 * registered to field coords; the 316k field is the haze (never GL polylines).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 180 / 340 → morph ends ≈ 0.53 */
	const step = $derived.by(() => {
		if (progress < 0.64) return 1;
		if (progress < 0.82) return 2;
		return 3;
	});
	const scaffoldOn = $derived(progress >= 0.08);
	const parOn = $derived(reduced || step >= 2);
	const anchorOn = $derived(reduced || step >= 3);

	let ch2 = $state<Ch2Data | null>(null);
	let tick = $state(0);
	onMount(() => {
		let alive = true;
		loadCh2Data().then((d) => {
			if (alive) ch2 = d;
		});
		const onResize = (): void => {
			requestAnimationFrame(() => {
				tick++;
			});
		};
		window.addEventListener('resize', onResize);
		return () => {
			alive = false;
			window.removeEventListener('resize', onResize);
		};
	});
	// force one recompute the moment the field handle first arrives, so the
	// projected worm geometry lands even if no window resize fires after load
	let seeded = false;
	$effect(() => {
		if (field && !seeded) {
			seeded = true;
			tick++;
		}
	});

	/** the earliest exemplar season (2010): its par worm + the anchor that most
	 *  visibly CRAWLS against the day's going rate. The morph's whole payoff is
	 *  "par sprints, the anchor crawls along the floor", so the single protagonist
	 *  is the exemplar with the DEEPEST shortfall below the drawn par worm at its
	 *  own final ball (long-and-slow wins over merely-long, §8 audit) — not just
	 *  the longest innings, whose slowness can be incidental. */
	const seed = $derived<WormSeason | null>(ch2 ? (ch2.worms.seasons[0] ?? null) : null);
	const anchorEx = $derived.by(() => {
		if (!seed || seed.exemplars.length === 0) return null;
		const par = seed.par_worm;
		let best = seed.exemplars[0];
		let bestGap = -Infinity;
		for (const e of seed.exemplars) {
			const b = e.cum_runs.length;
			if (b === 0) continue;
			const parAt = b <= par.length ? par[b - 1] : (par.length ? par[par.length - 1] : 0);
			const gap = parAt - e.cum_runs[b - 1];
			if (gap > bestGap) {
				bestGap = gap;
				best = e;
			}
		}
		return best;
	});

	const geo = $derived.by(() => {
		void tick;
		const f = field;
		if (!f || !seed) return null;
		const frame = wormFrame(f);
		if (!frame) return null;
		const par = wormPolyline(f, seed.par_worm);
		const parEnd = wormEnd(f, seed.par_worm);
		const anchor = anchorEx ? wormPolyline(f, anchorEx.cum_runs) : '';
		const anchorEndPt = anchorEx ? wormEnd(f, anchorEx.cum_runs) : null;
		return { frame, par, parEnd, anchor, anchorEnd: anchorEndPt };
	});
</script>

<div class="pin" class:active>
	{#if geo}
		{@const fr = geo.frame}
		<!-- destination-first scaffold: the labelled empty worm frame ahead of the points -->
		<div class="scaffold" class:on={scaffoldOn} aria-hidden="true">
			<!-- x axis -->
			<div
				class="axis"
				style="left:{fr.left}px; top:{fr.bottom}px; width:{(fr.right - fr.left).toFixed(1)}px; height:1px;"
			></div>
			<!-- y axis -->
			<div
				class="axis"
				style="left:{fr.left}px; top:{fr.top}px; width:1px; height:{(fr.bottom - fr.top).toFixed(1)}px;"
			></div>
			{#each fr.xticks as t (t.ball)}
				<div class="xlab" style="left:{t.x.toFixed(1)}px; top:{(fr.bottom + 6).toFixed(1)}px;">{t.label}</div>
			{/each}
			<div class="axis-name x" style="left:{((fr.left + fr.right) / 2).toFixed(1)}px; top:{(fr.bottom + 22).toFixed(1)}px;">
				balls faced
			</div>
			{#each fr.yticks as t (t.runs)}
				{#if t.runs > 0}
					<div class="ylab" style="left:{(fr.left - 6).toFixed(1)}px; top:{t.y.toFixed(1)}px;">{t.runs}</div>
				{/if}
			{/each}
			<div class="axis-name y" style="left:{(fr.left - 6).toFixed(1)}px; top:{(fr.top - 4).toFixed(1)}px;">runs</div>
		</div>

		<!-- the worms: SVG spanning the fixed viewport, registered to field coords -->
		<svg class="worm-plane" aria-hidden="true">
			<!-- faint pre-echo guide where the par worm will land (par overwrites it) -->
			{#if geo.par}
				<polyline points={geo.par} class="par-guide" class:on={scaffoldOn && !parOn} />
			{/if}
			<!-- the par worm — crisp, subordinate in the figure hierarchy -->
			{#if geo.par}
				<polyline points={geo.par} class="par" class:on={parOn} />
			{/if}
			<!-- the anchor worm — the protagonist, dedicated figure channel:
			     a dark casing/halo behind a brighter stroke (highest contrast) -->
			{#if geo.anchor}
				<polyline points={geo.anchor} class="anchor-casing" class:on={anchorOn} />
				<polyline points={geo.anchor} class="anchor-stroke" class:on={anchorOn} />
			{/if}
		</svg>

		<!-- in-frame worm labels (high-contrast even where the line is subtle) -->
		{#if geo.parEnd && parOn}
			<div class="worm-label par-label" style="left:{(geo.parEnd.x + 8).toFixed(1)}px; top:{(geo.parEnd.y - 6).toFixed(1)}px;">
				the day's going rate
			</div>
		{/if}
		{#if geo.anchorEnd && anchorOn}
			<div class="worm-label anchor-label" style="left:{(geo.anchorEnd.x + 8).toFixed(1)}px; top:{(geo.anchorEnd.y - 2).toFixed(1)}px;">
				an anchor
			</div>
		{/if}
	{/if}

	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>
					Every dot is one ball. The further right, <strong>the more balls the batter had faced.</strong>
					The higher up, the more runs. A fast innings climbs steeply, a slow one stays flat.
					Every ball ever bowled is in this cloud.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					The grey line is the day's going rate, what a good team would be on. <strong>Look how it
					sprints.</strong> Barely a pause for breath.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					The gold line is one anchor's innings.
					<button class="dagger" onclick={() => footnotesOpen.set('anchor-definition')} aria-label="How we counted an anchor">ⓘ</button>
					Same target, but <strong>look at it crawl.</strong> Barely a big shot in sight. Just nudge a
					single, live to face the next ball, and <strong>let the big hitters swing</strong> at the other end.
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

	.scaffold {
		position: absolute;
		inset: 0;
		opacity: 0;
		transition: opacity 700ms ease;
	}

	.scaffold.on {
		opacity: 1;
	}

	.axis {
		position: absolute;
		background: rgba(232, 236, 245, 0.26);
	}

	.xlab,
	.ylab,
	.axis-name {
		position: absolute;
		font-size: 11px;
		letter-spacing: 0.05em;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}

	.xlab {
		transform: translate(-50%, 0);
	}

	.ylab {
		transform: translate(-100%, -50%);
	}

	.axis-name.x {
		transform: translate(-50%, 0);
		letter-spacing: 0.12em;
		text-transform: lowercase;
	}

	.axis-name.y {
		transform: translate(-100%, -100%);
		letter-spacing: 0.12em;
	}

	/* the worm plane: a fixed-viewport SVG whose vertices are CSS px matching
	   the canvas (like the projected wall scaffold) */
	.worm-plane {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		overflow: visible;
		pointer-events: none;
	}

	polyline {
		fill: none;
		stroke-linejoin: round;
		stroke-linecap: round;
		opacity: 0;
		transition: opacity 650ms ease;
	}

	polyline.on {
		opacity: 1;
	}

	/* pre-echo: a faint guide exactly where par lands (par overwrites it) */
	.par-guide {
		stroke: rgba(232, 236, 245, 0.22);
		stroke-width: 1.4;
		stroke-dasharray: 5 5;
		transition: opacity 400ms ease;
	}

	.par-guide.on {
		opacity: 1;
	}

	/* par: crisp but deliberately SUBORDINATE — it already pops into the sparse
	   zone; making par the brightest mark is the figure-ground failure (§0.1) */
	.par {
		stroke: #8f9ab4;
		stroke-width: 2;
	}

	/* the anchor figure channel: dark casing/halo + brighter stroke — the
	   highest-contrast mark in the frame, higher than par (§0.1). The dark casing
	   over the canvas IS the corridor haze-attenuation (CONTRACT §13.3). */
	.anchor-casing {
		stroke: rgba(6, 9, 14, 0.92);
		stroke-width: 8;
	}

	.anchor-stroke {
		stroke: #ffd477;
		stroke-width: 2.8;
	}

	.worm-label {
		position: absolute;
		font-size: 12px;
		letter-spacing: 0.02em;
		white-space: nowrap;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.95);
		pointer-events: none;
	}

	.par-label {
		color: #b9c2d6;
		font-weight: 600;
	}

	/* high-contrast label even though the anchor line is subtle (§0.1) */
	.anchor-label {
		color: #ffd477;
		font-weight: 800;
		font-size: 13px;
	}

	.pin :global(.scaffold),
	.pin :global(polyline),
	.pin :global(.worm-label) {
		transition-duration: 650ms;
	}

	@media (prefers-reduced-motion: reduce) {
		.scaffold,
		polyline,
		.par-guide {
			transition: none;
		}
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 12vh;
		max-width: min(28rem, 84vw);
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
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(10vh, calc(env(safe-area-inset-bottom) + 8vh));
		}

		.worm-label {
			font-size: 11px;
		}
	}
</style>
