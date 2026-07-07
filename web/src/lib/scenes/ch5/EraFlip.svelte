<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal, captionRevealActive } from '$lib/story/captionReveal.svelte';
	import { worthCell } from '$lib/field/layout';
	import { loadCh5Data, eraFlipState, reAt, runs, eraYears, type Ch5Data } from './data';
	import WorthScaffold from './WorthScaffold.svelte';

	/**
	 * C5-6a — HERO 2, part one: the era flip + the difference lens (Run-Expectancy
	 * Surface Drift). The grid HOLDS (the morph budget is spent); the flip and the
	 * rise are COLOR states over the held cells (the §19 pricelens, driven by
	 * index.ts's dynamicState through the SAME eraFlipState this component reads,
	 * so the era chip / legend / field can never disagree). The lens lands as a
	 * dip-to-dark re-light, and the on-grid state label + legend swap in step so
	 * the channel's change of meaning is re-glossed the moment it lands. The
	 * worked-example ring sits on the over-7, 2-down cell; both its numbers bind
	 * to the emitted engine surfaces (110.3 → 130.4, shown rounded).
	 *
	 * STEP 3'S LOCATION CLAUSE IS ARTIFACT-VERIFIED (release-blocking, storyboard
	 * §3/§4): the emitted rise table burns brightest at the LEFT EDGE (over 1's
	 * pooled column, ~29 runs — the whole innings still ahead) and fades toward
	 * the death; the storyboard's original middle-overs clause did NOT survive
	 * the emitted table and was rewritten (test_ch5.test_rise_lens_caption_claims
	 * pins the copy to the diff maxima).
	 *
	 * REDUCED MOTION: the field jump-cuts straight to the settled RISE state
	 * (index.ts reducedMotionEndState) while the caption steps still advance on
	 * scroll — so steps 1-2 get reduced VARIANTS that state the two era prices
	 * as facts about the ringed spot, never as "the map you are looking at".
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* gap-aligned on mobile (§17.6) — the SAME flag index.ts's dynamicState
	   passes, so chip/legend and field recolor stay in lock-step */
	const flip = $derived(eraFlipState(progress, captionRevealActive() && !reduced));
	const step = $derived(flip.stage);
	const BOUNDS = [0, 0.38, 0.62, 1] as const;
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

	/* the worked-example cell: over 7 (index 6), 2 down */
	const HERO_OVER = 6;
	const HERO_WKTS = 2;
	const earlyRead = $derived(ch5 ? reAt(ch5.re_drift.re_a, HERO_OVER, HERO_WKTS) : null);
	const recentRead = $derived(ch5 ? reAt(ch5.re_drift.re_b, HERO_OVER, HERO_WKTS) : null);
	const eraA = $derived(ch5 ? eraYears(ch5.re_drift.era_a) : '2008-2010');
	const eraB = $derived(ch5 ? eraYears(ch5.re_drift.era_b) : '2023-2026');

	/* the era chip mirrors the FIELD's displayed state exactly (reduced → the rise) */
	const chipLabel = $derived(reduced ? 'the rise' : step === 1 ? eraA : step === 2 ? eraB : 'the rise');
	const stateLabel = $derived(reduced || step === 3 ? 'the rise' : 'the price');
	const legend = $derived(
		reduced || step === 3 ? 'brighter = the bigger rise' : 'brighter = more runs still to come'
	);

	/* ring geometry, registered to the GL cell */
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
	const ring = $derived.by(() => {
		void tick;
		const f = field;
		const wl = f?.getWorthLayout();
		if (!f || !wl) return null;
		const c = worthCell(wl, HERO_OVER, HERO_WKTS);
		const centre = f.projectToCss(c.x, c.y);
		const corner = f.projectToCss(c.x + wl.cellW / 2, c.y - wl.cellH / 2);
		return { x: centre.x, y: centre.y, rx: (corner.x - centre.x) * 1.25, ry: (corner.y - centre.y) * 1.25 };
	});
</script>

<div class="pin" class:active>
	<WorthScaffold {field} />

	<!-- the era chip (tied to the field's displayed state) -->
	<div class="era-chip">
		<span class="chip-label">{chipLabel}</span>
		<span class="chip-sub">{stateLabel} · {legend}</span>
	</div>

	{#if ring && step <= 2}
		<div
			class="ring"
			style="left:{ring.x.toFixed(1)}px; top:{ring.y.toFixed(1)}px; width:{(ring.rx * 2).toFixed(
				1
			)}px; height:{(ring.ry * 2).toFixed(1)}px;"
			aria-hidden="true"
		></div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					{#if reduced}
						Read one spot first. Over seven, two wickets down, ringed on the map. In the league's
						first three seasons a team there usually still had about
						{earlyRead !== null ? runs(earlyRead) : 110} runs coming.
					{:else}
						Read one spot first. Over seven, two wickets down. In the league's first three seasons
						a team there usually still had about {earlyRead !== null ? runs(earlyRead) : 110} runs
						coming.
					{/if}
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					{#if reduced}
						In the last four seasons that same spot promises about
						{recentRead !== null ? runs(recentRead) : 130}. The prices moved. The grid did not.
					{:else}
						Now flip the map to the last four seasons. The same spot promises about
						{recentRead !== null ? runs(recentRead) : 130}. The prices moved. The grid did not.
					{/if}
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					This view keeps only the rise. Brightness now means how much a spot's price went up. It
					burns brightest at the left edge and fades toward the death: the earlier you stand, the
					more of the new game's flood still lies ahead of you.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-drift')}
						aria-label="How the rise is computed">ⓘ</button
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

	.era-chip {
		position: absolute;
		top: 4.5vh;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.1rem;
		padding: 0.4rem 0.9rem;
		border-radius: 10px;
		background: rgba(10, 14, 24, 0.72);
		border: 1px solid rgba(151, 161, 184, 0.25);
	}

	.chip-label {
		font-size: 1.1rem;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
	}

	.chip-sub {
		font-size: 0.62rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.ring {
		position: absolute;
		transform: translate(-50%, -50%);
		border: 2px solid #ffd166;
		border-radius: 10px;
		box-shadow: 0 0 12px rgba(255, 209, 102, 0.5);
		pointer-events: none;
	}

	/* grid captions live in the BOTTOM-LEFT corner: overs 1-8 × wickets 6-9
	   hold ~150 of 316k balls, so almost nothing renders under the panel in
	   ANY lens (an empty cell is dark regardless of its table value — light
	   comes from points). The rise lens's LIT hot band is the LEFT EDGE and
	   the top-left rows (over 1's pooled column ~29 runs, the emitted diff's
	   maxima — see test_rise_lens_caption_claims), which sit well above this
	   corner; the bottom-right corner is the death-collapse corner and holds
	   ~21k balls — never park a caption there. 12vw clears the wickets ticks. */
	.caption-slot {
		position: absolute;
		left: 12vw;
		bottom: 9vh;
		max-width: min(24rem, 38vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	/* the ⓘ target must not stay tappable while the caption sits invisible in
	   the mobile clear gap (an invisible 44px trap over the field) */
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

		.era-chip {
			top: max(3vh, calc(env(safe-area-inset-top) + 52px));
		}
	}
</style>
