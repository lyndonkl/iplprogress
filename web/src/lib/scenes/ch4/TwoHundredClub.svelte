<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { tideRule, tideAt, type Rule } from './tidesvg';
	import { loadCh4Data, clubScrub, giFor, pct, IPL_EARLY, type Ch4Data, type GroupLite } from './data';
	import TideScaffold from './TideScaffold.svelte';

	/**
	 * C4-4 — The 200 Club (HERO: Threshold Exceedance). The skyline HOLDS; declaring
	 * no waterline drained the going-rate line so the full coastline is lit. A fixed
	 * bold rule at 200 (and a faint 250 rule) are the milestone ridgeline — the
	 * columns poking above them ARE the club. A season playhead sweeps the blocks and
	 * the chip reads that season's P(200), so the 2023 cliff lands as the right-hand
	 * skyline suddenly clearing the line. Rules + playhead are SVG registered to the
	 * GL coastline (CONTRACT §18.3).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* clubScrub thresholds: 0.22 (scrub start) / 0.82 (the cliff punchline). step
	   tracks scroll progress even under reduced motion (the chip/field hold their
	   settled 2008→2026 end state; the captions stay a full stepped sequence —
	   CONTRACT §17.3 / audit reduced-motion parity), not a single final frame. */
	const cs = $derived(clubScrub(progress));
	const step = $derived(cs.step);
	const BOUNDS = [0, 0.22, 0.82, 1] as const;
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

	const p200Early = $derived(ch4 ? ch4.exceedance.by_era[IPL_EARLY].exceedance_pct['200'] : null);
	const p2002026 = $derived(ch4 ? ch4.exceedance.by_season.ipl['2026']?.exceedance_pct['200'] ?? null : null);
	/* the scrubbed season's P(200), straight from the artifact */
	const p200Live = $derived(
		ch4 ? ch4.exceedance.by_season.ipl[String(cs.season)]?.exceedance_pct['200'] ?? null : null
	);
	const groups = $derived<GroupLite[]>((field?.data.groups as GroupLite[] | undefined) ?? []);
	const seasonMax = $derived(
		ch4 ? ch4.exceedance.by_season.ipl[String(cs.season)]?.max ?? 260 : 260
	);

	const geo = $derived.by(() => {
		void tick;
		const f = field;
		if (!f) return null;
		const r200 = tideRule(f, 200);
		// 200 is the ONLY labelled threshold; 180 / 220 / 250 are a faint unlabelled
		// ruler so the club line reads as the single bold beam (audit C4-4 discipline).
		const rulers = [180, 220, 250].map((v) => tideRule(f, v)).filter((r): r is Rule => r !== null);
		if (!r200) return null;
		// the season playhead: a vertical from the baseline to that block's tallest column
		let playTop = null as { x: number; y: number } | null;
		let playBase = null as { x: number; y: number } | null;
		if (!reduced) {
			const gi = giFor(groups, 'ipl', cs.season);
			if (gi >= 0) {
				playTop = tideAt(f, gi, seasonMax);
				playBase = tideAt(f, gi, 0);
			}
		}
		return { r200, rulers, playTop, playBase };
	});
</script>

<div class="pin" class:active>
	<TideScaffold {field} />

	{#if geo}
		{@const r = geo.r200}
		<svg class="rules" aria-hidden="true">
			{#each geo.rulers as rr (rr.total)}
				<line x1={rr.left.x} y1={rr.left.y} x2={rr.right.x} y2={rr.right.y} class="rule-tick" />
			{/each}
			<line x1={r.left.x} y1={r.left.y} x2={r.right.x} y2={r.right.y} class="rule-200" />
			{#if geo.playTop && geo.playBase}
				<line x1={geo.playBase.x} y1={geo.playBase.y} x2={geo.playTop.x} y2={geo.playTop.y} class="playhead" />
			{/if}
		</svg>
		<div class="rule-lab r200" style="left:{(r.right.x - 8).toFixed(1)}px; top:{r.right.y.toFixed(1)}px;">200</div>
	{/if}

	<!-- the season + P(200) chip (top centre, clear of the columns + the top-right nav) -->
	<div class="chips" class:reduced>
		<span class="year">{reduced ? '2008 → 2026' : String(cs.season)}</span>
		<span class="p200">
			{#if reduced}
				{p200Early !== null ? pct(p200Early) : '7.7'}% → {p2002026 !== null ? pct(p2002026) : '52'}%
			{:else}
				{p200Live !== null ? pct(p200Live) : '-'}%
			{/if}
			<span class="p200-sub">passed 200</span>
		</span>
	</div>

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card chip">
				<p>
					Draw one bold line at <strong>200.</strong> A first innings that clears it is in the club, the
					kind of total that used to end the game as a contest. The fainter lines above and below are
					just markers on the ruler.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card chip">
				<p>
					For fifteen years <strong>almost nobody got there,</strong> about one first innings in
					thirteen. Then sweep across and watch it climb, until lately it is four in ten.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					Then look at 2026. The whole right of the skyline clears the line.
					<strong>More than half of all first innings now pass 200.</strong>
					<button class="dagger" onclick={() => footnotesOpen.set('full-first-innings')} aria-label="How a 200 innings is counted">ⓘ</button>
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

	.rule-200 {
		stroke: #5b8cff;
		stroke-width: 2.4;
		stroke-linecap: round;
		filter: drop-shadow(0 0 5px rgba(91, 140, 255, 0.5));
	}

	.rule-tick {
		stroke: rgba(232, 236, 245, 0.16);
		stroke-width: 1.1;
		stroke-dasharray: 3 4;
	}

	.playhead {
		stroke: var(--gold);
		stroke-width: 2;
		opacity: 0.8;
	}

	.rule-lab {
		position: absolute;
		transform: translate(-100%, -140%);
		font-size: 11px;
		font-weight: 700;
		white-space: nowrap;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.95);
		font-variant-numeric: tabular-nums;
		pointer-events: none;
	}

	.rule-lab.r200 {
		color: #9dbcff;
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

	.p200 {
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

	.chips.reduced .p200 {
		font-size: 1.3rem;
	}

	.chips.reduced .year {
		font-size: 1.1rem;
	}

	.p200-sub {
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

		.p200 {
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
