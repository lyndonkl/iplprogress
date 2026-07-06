<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { tideRule } from './tidesvg';
	import {
		loadCh4Data,
		waterlineScrub,
		waterlineLevelAt,
		runs,
		type Ch4Data
	} from './data';
	import TideScaffold from './TideScaffold.svelte';

	/**
	 * C4-3 — The rising waterline (HERO: Par-Score Drift). The skyline HOLDS (the
	 * morph budget is spent). The waterline is the GOING RATE: the first-innings total
	 * that wins exactly half the time. It floods in at the 2008 level, then RISES
	 * season by season as the reader scrubs — the field drowns every column below it
	 * (declared on the scene's fieldState, level driven by dynamicState). This
	 * component draws the blue waterline, the faint 2008 ghost line and the year/level
	 * chip in SVG registered to the GL coastline, so the crisp line and the drowned
	 * columns can never drift. The level here mirrors the field's exactly (same
	 * waterlineScrub / waterlineLevelAt), so SVG and GL share one source of truth.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* waterlineScrub thresholds: 0.24 (rise start) / 0.72 (settled). Four caption
	   steps: orient (1) · the rise (2) · the par-drift punchline (3) · the 230
	   ceiling (4). step tracks scroll progress even under reduced motion — the field
	   jump-cuts to the settled 2026 water, the captions stay a full stepped sequence
	   (CONTRACT §17.3 / audit reduced-motion parity), not a single final frame. */
	const scrub = $derived(waterlineScrub(progress));
	const step = $derived<1 | 2 | 3 | 4>(scrub.step < 3 ? scrub.step : progress < 0.87 ? 3 : 4);
	const BOUNDS = [0, 0.24, 0.72, 0.87, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch4 = $state<Ch4Data | null>(null);
	let tick = $state(0);
	onMount(() => {
		let alive = true;
		loadCh4Data().then((d) => {
			if (alive) {
				ch4 = d;
				tick++;
			}
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
	let seeded = false;
	$effect(() => {
		if (field && !seeded) {
			seeded = true;
			tick++;
		}
	});

	const par2008 = $derived(ch4 ? ch4.columns.par_waterline['2008'] : null);
	const par2026 = $derived(ch4 ? ch4.columns.par_waterline['2026'] : null);
	/* the honest ceiling: 230 is now postable, yet still almost always defended */
	const t230 = $derived(ch4 ? ch4.par_drift.totals_230plus : null);
	/* the live level, EXACTLY the field's drown level (reduced → settled 2026) */
	const level = $derived(
		reduced ? (par2026 ?? 0) : waterlineLevelAt(scrub.seasonIdx)
	);
	const chipYear = $derived(reduced ? '2008 → 2026' : String(scrub.season));

	const geo = $derived.by(() => {
		void tick;
		const f = field;
		if (!f || level <= 0) return null;
		const water = tideRule(f, level);
		const ghost = par2008 !== null ? tideRule(f, par2008) : null;
		const ceiling = tideRule(f, 230);
		if (!water) return null;
		return { water, ghost, ceiling };
	});
</script>

<div class="pin" class:active>
	<!-- persistent orientation anchors (shared, held from C4-2 through the tide) -->
	<TideScaffold {field} />

	{#if geo}
		{@const w = geo.water}
		<svg class="rules" aria-hidden="true">
			<!-- the faint fixed 2008 going-rate ghost line -->
			{#if geo.ghost}
				<line
					x1={geo.ghost.left.x}
					y1={geo.ghost.left.y}
					x2={geo.ghost.right.x}
					y2={geo.ghost.right.y}
					class="ghost"
				/>
			{/if}
			<!-- the rising waterline (the going rate) -->
			<line x1={w.left.x} y1={w.left.y} x2={w.right.x} y2={w.right.y} class="water" />
			<!-- the honest 230 ceiling, drawn quietly once the punchline lands -->
			{#if geo.ceiling && step >= 4}
				<line x1={geo.ceiling.left.x} y1={geo.ceiling.left.y} x2={geo.ceiling.right.x} y2={geo.ceiling.right.y} class="ceiling" />
			{/if}
		</svg>

		{#if geo.ghost && par2008 !== null && step >= 2}
			<div class="ghost-lab" style="left:{(geo.ghost.right.x - 8).toFixed(1)}px; top:{(geo.ghost.right.y).toFixed(1)}px;">
				2008: {runs(par2008)}
			</div>
		{/if}
		{#if geo.ceiling && step >= 4}
			<div class="ceiling-lab" style="left:{(geo.ceiling.right.x - 8).toFixed(1)}px; top:{geo.ceiling.right.y.toFixed(1)}px;">230</div>
		{/if}
		<div class="water-lab" style="left:{(w.right.x - 8).toFixed(1)}px; top:{w.right.y.toFixed(1)}px;">
			the going rate
		</div>
	{/if}

	<!-- the year + level chip (top centre, clear of the columns + the top-right nav) -->
	{#if level > 0}
		<div class="chips" class:reduced>
			<span class="year">{chipYear}</span>
			<span class="level">
				{runs(level)}
				<span class="level-sub">the going rate</span>
			</span>
		</div>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card chip">
				<p>
					The blue line is <strong>the going rate:</strong> the first-innings score that wins exactly
					half the time. Back in 2008 it sat at {par2008 !== null ? runs(par2008) : '165'}. Post that,
					and it was a coin toss.
					<button class="dagger" onclick={() => footnotesOpen.set('par-drift')} aria-label="How the going rate is worked out">ⓘ</button>
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card chip">
				<p>
					Now watch the line <strong>climb, season by season.</strong> Every column it rises past has
					just drowned: a score that used to be safe, sunk under the new water level.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card chip">
				<p>
					By {reduced ? 'now' : String(scrub.season)} the going rate is
					<strong>{par2026 !== null ? runs(par2026) : '206'}.</strong>
					That 2008-winning {par2008 !== null ? runs(par2008) : '165'} would lose today, and lose
					comfortably. The whole waterline came up by around 40 runs.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					And a line most sides never used to touch, up at <strong>230.</strong> In just these last
					four seasons teams have posted it {t230 ? t230.posted : 33} times, and only
					{t230 ? t230.chased_down : 4} of those got chased down. The water rose, but a big enough
					total still wins.
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

	.rules {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		overflow: visible;
		pointer-events: none;
	}

	.water {
		stroke: #5b8cff;
		stroke-width: 2.6;
		stroke-linecap: round;
		filter: drop-shadow(0 0 6px rgba(91, 140, 255, 0.5));
	}

	.ghost {
		stroke: #6b7284;
		stroke-width: 1.4;
		stroke-dasharray: 4 4;
	}

	.ceiling {
		stroke: rgba(232, 236, 245, 0.32);
		stroke-width: 1.4;
		stroke-dasharray: 5 4;
	}

	.ceiling-lab {
		position: absolute;
		transform: translate(-100%, -140%);
		font-size: 10px;
		font-weight: 700;
		color: var(--ink-dim);
		white-space: nowrap;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.95);
		font-variant-numeric: tabular-nums;
		pointer-events: none;
	}

	.water-lab {
		position: absolute;
		transform: translate(-100%, -140%);
		font-size: 11px;
		font-weight: 700;
		color: #9dbcff;
		white-space: nowrap;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.95);
		pointer-events: none;
	}

	.ghost-lab {
		position: absolute;
		transform: translate(-100%, -140%);
		font-size: 10px;
		color: var(--ink-dim);
		white-space: nowrap;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.95);
		font-variant-numeric: tabular-nums;
		pointer-events: none;
	}

	.chips {
		position: absolute;
		top: 5vh;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}

	.year {
		font-size: 1.4rem;
		font-weight: 700;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.level {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		padding: 0.3rem 0.7rem;
		border-radius: 10px;
		background: rgba(91, 140, 255, 0.14);
		border: 1px solid rgba(91, 140, 255, 0.4);
		font-size: 1.9rem;
		font-weight: 800;
		line-height: 1;
		color: #9dbcff;
		font-variant-numeric: tabular-nums;
	}

	.chips.reduced .level {
		font-size: 1.4rem;
	}

	.chips.reduced .year {
		font-size: 1.1rem;
	}

	.level-sub {
		margin-top: 2px;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 12vh;
		max-width: min(25rem, 40vw);
		opacity: var(--reveal, 1); /* mobile "read, then watch" (CONTRACT §17); 1 on desktop / reduced */
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
		.chips {
			top: 3vh;
		}

		.level {
			font-size: 1.5rem;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: max(15vh, calc(env(safe-area-inset-top) + 56px));
		}
	}
</style>
