<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import {
		loadCh3Data,
		iplHull,
		under7PooledPct,
		retreatState,
		pctText,
		fmt1,
		IPL_EARLY,
		IPL_MODERN,
		type Ch3Data,
		type GhostPoint
	} from './data';
	import { frontierFrame, frontierPolyline, frontierDots } from './frontiersvg';
	import FrontierScaffold from './FrontierScaffold.svelte';

	/**
	 * C3-3 — The retreat (HERO: Attack-Containment Frontier Drift). The frontier
	 * plane HOLDS (no re-sort — the morph budget is spent). As the reader scrubs, a
	 * season pointer brightens the current season's clouds (driven by the scene
	 * def's dynamicState `filterSeason`, kept in sync with the on-screen chip via the
	 * shared `retreatState`), so the bright cloud migrates up and to the right — real
	 * data, never a re-layout. A fixed greyed 2008 edge stays on screen beside the
	 * live season-swept edge, so the retreat reads as the widening gap between them.
	 * The count chip (share left of the seven-an-over line) is the hero number.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const rs = $derived(retreatState(progress));
	const step = $derived(reduced ? 4 : rs.step);
	/* mobile "read, then watch" (CONTRACT §17): ascending step bounds (mirroring
	   retreatState's 0.28/0.6/0.8 thresholds) so the caption fades to a clear gap
	   before the next step. 1 on desktop / reduced. */
	const BOUNDS = [0, 0.28, 0.6, 0.8, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const sevenOn = $derived(reduced || rs.step >= 1);
	const liveOn = $derived(reduced || rs.step >= 2);
	const trailOn = $derived(reduced || rs.step >= 3);

	let ch3 = $state<Ch3Data | null>(null);
	let tick = $state(0);
	let named = $state<GhostPoint | null>(null);
	onMount(() => {
		let alive = true;
		loadCh3Data().then((d) => {
			if (alive) ch3 = d;
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

	/* hero pair + live count chip, all from the artifact. The dominant chip reads a
	   trailing 3-season POOLED under-seven share (forward-clamped at the start), not
	   the raw per-season value: the raw series whiplashes (2008 20.8% → 2009 42.6%),
	   reading below the caption's 29% at the very moment it is asserted and jumping
	   above 2008. The pooled series holds 29.0% across 2008-2010 (matching the
	   caption) and slides down to ~2% as one steady retreat. */
	const share2008 = $derived(ch3 ? ch3.frontier.under7.era_bands[IPL_EARLY].pct : null);
	const share2026 = $derived(ch3 ? ch3.frontier.under7.era_bands[IPL_MODERN].pct : null);
	const liveShare = $derived(ch3 ? under7PooledPct(ch3, rs.chipYear) : null);

	const ghost = $derived<GhostPoint[]>(ch3 ? ch3.frontier.ghost_trail.points : []);
	const ghostName = $derived(ch3 ? ch3.frontier.ghost_trail.bowler : '');
	/* the ghost trail grows with the scrub; complete under reduced motion */
	const trailUpTo = $derived(reduced ? ghost : ghost.filter((p) => p.season <= rs.chipYear));

	const edge2008 = $derived(ch3 ? iplHull(ch3, 2008) : null);
	const edgeLive = $derived(ch3 && rs.year !== null ? iplHull(ch3, rs.chipYear) : ch3 ? iplHull(ch3, 2026) : null);

	const geo = $derived.by(() => {
		void tick;
		const f = field;
		if (!f) return null;
		const frame = frontierFrame(f);
		if (!frame) return null;
		const ghostLine = frontierPolyline(f, trailUpTo);
		const ghostDots = frontierDots(f, trailUpTo);
		const e08 = edge2008 ? frontierPolyline(f, edge2008) : '';
		const eLive = edgeLive ? frontierPolyline(f, edgeLive) : '';
		return { frame, ghostLine, ghostDots, e08, eLive };
	});

	function nameGhost(p: GhostPoint): void {
		named = named && named.season === p.season ? null : p;
	}
</script>

<div class="pin" class:active>
	<!-- persistent orientation anchors (shared, held from C3-2 through the retreat):
	     axes + cheap/expensive + fast/slow + the "cheap and deadly" home zone -->
	<FrontierScaffold {field} />

	{#if geo}
		{@const fr = geo.frame}
		<svg class="edge-plane" aria-hidden="true">
			<!-- the seven-an-over reference line (fixed) -->
			{#if sevenOn}
				<line x1={fr.sevenX} x2={fr.sevenX} y1={fr.top} y2={fr.bottom} class="seven" />
			{/if}
			<!-- fixed 2008 edge ghost (greyed, held through the scrub) -->
			{#if liveOn && geo.e08}
				<polyline points={geo.e08} class="edge-ghost" />
			{/if}
			<!-- the live season-swept edge -->
			{#if liveOn && geo.eLive}
				<polyline points={geo.eLive} class="edge-live" />
			{/if}
			<!-- the ghost trail (one great across the frontiers) -->
			{#if trailOn && geo.ghostLine}
				<polyline points={geo.ghostLine} class="trail" />
			{/if}
		</svg>

		{#if sevenOn}
			<div class="seven-label" style="left:{fr.sevenX - 6}px; top:{fr.top + 6}px;">seven an over</div>
		{/if}

		<!-- tappable ghost-trail dots (name the season; captions carry the point) -->
		{#if trailOn}
			{#each geo.ghostDots as d (d.source.season)}
				<button
					class="trail-dot"
					style="left:{d.x.toFixed(1)}px; top:{d.y.toFixed(1)}px;"
					onclick={() => nameGhost(d.source as GhostPoint)}
					aria-label="Name {ghostName}'s {d.source.season} season"
				></button>
			{/each}
			{#if named}
				{@const nd = geo.ghostDots.find((g) => g.source.season === named?.season)}
				{#if nd}
					<div class="named" style="left:{nd.x.toFixed(1)}px; top:{(nd.y - 10).toFixed(1)}px;">
						{ghostName}, {named.season}: {fmt1(named.economy)} an over, {fmt1(named.strike_rate)} balls a wicket
					</div>
				{/if}
			{/if}
		{/if}
	{/if}

	<!-- the season chip + the hero count chip, grouped together -->
	{#if liveOn && liveShare !== null}
		<div class="chips" class:reduced>
			<span class="season-chip">{reduced ? '2008 → 2026' : rs.chipYear}</span>
			<span class="count-chip">
				{#if reduced}
					{share2008 !== null ? pctText(share2008) : '-'}% → {share2026 !== null ? pctText(share2026) : '-'}%
				{:else}
					{pctText(liveShare)}%
				{/if}
				<span class="count-sub">under seven an over</span>
			</span>
		</div>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					Draw a line at <strong>seven runs an over.</strong> Leak fewer than that across a whole
					season and you were a genuine stopper, a bowler who dried the game right up.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					In the league's first three years, <strong>nearly a third of bowlers lived left of that
						line</strong> ({share2008 !== null ? pctText(share2008) : '-'}%). The line has not moved.
					Watch the cloud slide right, season by season, until in the last four years
					<strong>just {share2026 !== null ? pctText(share2026) : '-'}% still get there.</strong>
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					The gold trail is <strong>one great, season after season,</strong> always hunting the edge.
					Even he gets shoved to the right. He stayed brilliant. <strong>He could not stay cheap.</strong>
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					Now look up and down. <strong>The bite never went, wickets come as fast as ever.</strong>
					What died was the double act. No one manages both any more, cheap and deadly at once.
					<strong>Attack lived. Containment died.</strong>
					<button class="dagger" onclick={() => footnotesOpen.set('frontier-retreat')} aria-label="How the retreat was counted">ⓘ</button>
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

	.edge-plane {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		overflow: visible;
		pointer-events: none;
	}

	.seven {
		stroke: rgba(232, 236, 245, 0.32);
		stroke-width: 1.4;
		stroke-dasharray: 4 4;
	}

	.seven-label {
		position: absolute;
		transform: translate(-100%, 0);
		font-size: 10px;
		letter-spacing: 0.04em;
		color: var(--ink-dim);
		white-space: nowrap;
	}

	.edge-ghost {
		fill: none;
		stroke: #6b7284;
		stroke-width: 1.6;
		stroke-dasharray: 3 3;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	.edge-live {
		fill: none;
		stroke: #ffd477;
		stroke-width: 2.4;
		stroke-linejoin: round;
		stroke-linecap: round;
		filter: drop-shadow(0 0 5px rgba(255, 212, 119, 0.45));
	}

	.trail {
		fill: none;
		stroke: #e8a33d;
		stroke-width: 1.6;
		stroke-linejoin: round;
		stroke-linecap: round;
		opacity: 0.9;
	}

	.trail-dot {
		position: absolute;
		width: 44px;
		height: 44px;
		transform: translate(-50%, -50%);
		border: none;
		background: none;
		cursor: pointer;
		pointer-events: auto;
	}

	.trail-dot::after {
		content: '';
		position: absolute;
		left: 50%;
		top: 50%;
		width: 7px;
		height: 7px;
		transform: translate(-50%, -50%);
		border-radius: 50%;
		background: #ffd477;
		box-shadow: 0 0 6px rgba(255, 212, 119, 0.7);
	}

	.trail-dot:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
		border-radius: 50%;
	}

	.named {
		position: absolute;
		transform: translate(-50%, -100%);
		padding: 0.3rem 0.5rem;
		border-radius: 6px;
		background: rgba(11, 14, 20, 0.92);
		border: 1px solid rgba(255, 212, 119, 0.4);
		font-size: 11px;
		color: var(--ink);
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
		pointer-events: none;
	}

	.chips {
		position: absolute;
		top: 6vh;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}

	.season-chip {
		font-size: 1.4rem;
		font-weight: 700;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.count-chip {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		padding: 0.3rem 0.7rem;
		border-radius: 10px;
		background: rgba(255, 212, 119, 0.12);
		border: 1px solid rgba(255, 212, 119, 0.34);
		font-size: 1.9rem;
		font-weight: 800;
		line-height: 1;
		color: #ffd477;
		font-variant-numeric: tabular-nums;
	}

	.chips.reduced .count-chip {
		font-size: 1.4rem;
	}

	.count-sub {
		margin-top: 2px;
		font-size: 0.62rem;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.caption-slot {
		position: absolute;
		left: 6vw;
		top: 10vh;
		max-width: min(28rem, 42vw);
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
			top: 4vh;
		}

		.count-chip {
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
