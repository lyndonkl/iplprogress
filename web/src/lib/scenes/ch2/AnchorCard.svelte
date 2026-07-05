<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import type { TeamMeta } from '$lib/field/types';
	import { pickedTeam, footnotesOpen } from '$lib/state';
	import { crestText } from '$lib/scenes/picker/crest';
	import { requestTeamChange } from '$lib/scenes/picker';
	import {
		loadCh2Data,
		anchorVariantFor,
		fmt1,
		fmt2,
		IPL_EARLY,
		IPL_MODERN,
		runoutSeasonPct,
		type Ch2Data,
		type AnchorVariant,
		type ResolvedAnchor
	} from './data';

	/**
	 * C2-8 — Team payoff card ("Your last anchor"). The chapter's finding re-told
	 * in the reader's colours: the last time the franchise fielded the archetype
	 * that just went extinct. Strictly template + ch2.json payoff.variants (16 —
	 * 10 IPL + 5 WPL + Neutral, incl. the designed empty state). The BODY is
	 * composed from the variant's structured fields using the storyboard C2-8
	 * template — the glossary-clean "the day's going rate" phrasing (NOT the
	 * emitted headline string, which carries the footnote-only word "par").
	 * A replayable worm draws the innings ball by ball against that day's rate.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 50 / 150 — show past the morph */
	const shown = $derived(progress >= 0.4);

	let ch2 = $state<Ch2Data | null>(null);
	let rootEl = $state<HTMLElement | null>(null);
	let returnAnchor = $state<HTMLElement | null>(null);
	let replaying = $state(false);

	onMount(() => {
		let alive = true;
		loadCh2Data().then((d) => {
			if (alive) ch2 = d;
		});
		return () => {
			alive = false;
		};
	});

	const teams = $derived<TeamMeta[] | null>(field?.data.teams ?? null);
	const resolved = $derived<ResolvedAnchor | null>(ch2 ? anchorVariantFor(ch2, $pickedTeam) : null);
	const v = $derived<AnchorVariant | null>(resolved?.variant ?? null);
	const kind = $derived(resolved?.kind ?? 'neutral');
	const isFallback = $derived(resolved?.fallback ?? false);
	const pronounObj = $derived(v?.league === 'wpl' ? 'her' : 'his');
	const leagueLabel = $derived(v?.league === 'wpl' ? 'WPL' : 'IPL');
	/** the rarity signal: how few anchor innings this innings' season produced */
	const rarity = $derived<number | null>(v && !v.empty_state ? v.season_anchor_innings : null);

	const crest = $derived(
		v !== null && teams !== null && kind !== 'neutral'
			? (teams.find((t) => t.league === v.league && t.name === v.team) ?? null)
			: null
	);

	const title = $derived.by(() => {
		if (v === null) return '';
		if (kind === 'neutral') return 'The league’s last anchors';
		if (v.empty_state) return `${v.team} never had one`;
		return `${v.team}’s last anchor`;
	});

	/* league-wide numbers for the neutral card (from the artifact) */
	const anchorEarly = $derived(ch2 ? ch2.anchor.bands[IPL_EARLY].anchor_ball_share_pct : null);
	const anchorModern = $derived(ch2 ? ch2.anchor.bands[IPL_MODERN].anchor_ball_share_pct : null);
	const runoutEarly = $derived(ch2 ? runoutSeasonPct(ch2, 2008) : null);
	const runoutModern = $derived(ch2 ? runoutSeasonPct(ch2, 2026) : null);

	/* ---- the replayable worm (self-contained mini SVG) ---------------------- */
	const cum = $derived<number[]>(v && !v.empty_state ? v.cum_runs : []);
	const maxBalls = $derived(cum.length);
	const parEnd = $derived(v ? (v.par_sr / 100) * Math.max(1, maxBalls) : 0);
	const maxRuns = $derived(Math.max(cum.length ? cum[cum.length - 1] : 0, parEnd, 1));
	const PAD = 10;
	const VBW = 320;
	const VBH = 150;
	const wx = (ball: number): number => PAD + (Math.max(0, ball - 1) / Math.max(1, maxBalls - 1)) * (VBW - 2 * PAD);
	const wy = (runs: number): number => VBH - PAD - (runs / maxRuns) * (VBH - 2 * PAD);
	const wormPts = $derived(cum.map((r, i) => `${wx(i + 1).toFixed(1)},${wy(r).toFixed(1)}`).join(' '));
	const parPts = $derived(`${wx(1).toFixed(1)},${wy(0).toFixed(1)} ${wx(maxBalls).toFixed(1)},${wy(parEnd).toFixed(1)}`);

	function replay(): void {
		if (reduced) return;
		replaying = false;
		// restart the CSS draw on the next frame
		requestAnimationFrame(() => {
			requestAnimationFrame(() => {
				replaying = true;
			});
		});
	}
</script>

<div class="return-anchor" bind:this={returnAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	<div class="card-slot" class:shown>
	<article class="payoff" bind:this={rootEl} aria-label="Chapter 2 team payoff — your last anchor">
		{#if v === null}
			<p class="overline">Chapter 2 payoff</p>
			<p class="dealing" role="status">Dealing your card…</p>
		{:else}
			<header>
				{#if crest !== null}
					<span class="chip" style:background={crest.color} style:color={crestText(crest.color)} aria-hidden="true">{crest.short}</span>
				{/if}
				<div>
					<p class="overline">Chapter 2 payoff</p>
					<h3>{title}</h3>
				</div>
			</header>

			{#if isFallback}
				<p class="note">No card for {$pickedTeam?.team} yet — here’s the league-wide one.</p>
			{/if}

			{#if v.empty_state}
				<!-- designed empty state: born post-anchor (authored, never a blank card).
				     Dead-defence today — the era-relative anchor definition gives every
				     current franchise a qualifying slowest innings, so no live variant
				     sets empty_state; kept authored + unit-tested against future data. -->
				<p class="headline">
					<strong>Born post-anchor — your franchise never had one.</strong>
					{v.team} came into the game after the careful accumulator was already gone. The archetype
					this chapter mourns was never part of its story.
				</p>
			{:else if kind === 'neutral'}
				<p class="viz-label">The most recent anchor the IPL has seen — {v.batter}, {v.season}</p>
				<figure class="worm-fig">
					<svg viewBox="0 0 {VBW} {VBH}" role="img" aria-label="{v.batter}'s {v.runs} off {v.balls}, a slow worm against the day's going rate">
						<line x1={PAD} y1={VBH - PAD} x2={VBW - PAD} y2={VBH - PAD} class="axis" />
						<line x1={PAD} y1={VBH - PAD} x2={PAD} y2={PAD} class="axis" />
						<polyline points={parPts} class="par" />
						<polyline points={wormPts} class="worm-casing" />
						<polyline points={wormPts} class="worm-stroke" class:replaying pathLength="1" />
					</svg>
					{#if !reduced}
						<button class="replay" onclick={replay} aria-label="Replay the innings ball by ball">↻ replay the innings</button>
					{/if}
				</figure>
				<p class="headline">
					The league’s last anchors: slow innings fell from
					<strong>{anchorEarly !== null ? fmt1(anchorEarly) : '—'}%</strong> of every ball to
					<strong>{anchorModern !== null ? fmt1(anchorModern) : '—'}%</strong>, and the risky single
					— the run-out — from <strong>{runoutEarly !== null ? fmt1(runoutEarly) : '—'}%</strong> of
					wickets to <strong>{runoutModern !== null ? fmt1(runoutModern) : '—'}%</strong>. A whole way
					of batting, gone in a generation.
				</p>
				<p class="elegy">The most recent to play it: {v.batter} — {v.runs} off {v.balls}, strike rate {fmt1(v.sr)} against a going rate of {fmt1(v.par_sr)}{#if rarity !== null}; one of just {rarity} the league produced all {v.season}{/if}.</p>
			{:else}
				<p class="viz-label">{v.batter} · {v.venue}, {v.date}</p>
				<figure class="worm-fig">
					<svg viewBox="0 0 {VBW} {VBH}" role="img" aria-label="{v.batter}'s {v.runs} off {v.balls}, a slow worm against the day's going rate">
						<line x1={PAD} y1={VBH - PAD} x2={VBW - PAD} y2={VBH - PAD} class="axis" />
						<line x1={PAD} y1={VBH - PAD} x2={PAD} y2={PAD} class="axis" />
						<polyline points={parPts} class="par" />
						<polyline points={wormPts} class="worm-casing" />
						<polyline points={wormPts} class="worm-stroke" class:replaying pathLength="1" />
					</svg>
					{#if !reduced}
						<button class="replay" onclick={replay} aria-label="Replay the innings ball by ball">↻ replay the innings</button>
					{/if}
				</figure>
				<p class="headline">
					<strong>{v.balls} balls, {v.runs} runs, strike rate {fmt1(v.sr)}.</strong>
					Boundaries: {fmt1(v.boundary_pct)}% of what {pronounObj === 'her' ? 'she' : 'he'} faced. The
					day’s going rate: {fmt1(v.par_sr)}.
				</p>
				<p class="elegy">
					{v.team}’s most recent anchor{#if rarity !== null} — one of just {rarity} the {leagueLabel} produced all {v.season}{/if}. The careful accumulator is all but gone, and the game is quicker for its going.
				</p>
			{/if}

			<button class="dagger-btn" onclick={() => footnotesOpen.set('payoff-ch2')} aria-label="How the anchor was counted">ⓘ how we counted an anchor</button>
			<button class="change" type="button" onclick={() => requestTeamChange(returnAnchor)}>
				{kind === 'neutral' && !isFallback ? 'Pick a team — this card re-deals in its colours' : 'Not your team? Change it'}
			</button>
		{/if}
	</article>
	</div>
</div>

<style>
	.return-anchor {
		position: absolute;
		top: 45%;
		left: 0;
		width: 1px;
		height: 1px;
	}

	/* viewport-fixed while active — exactly one scene's card on screen at a time */
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	.pin.active {
		visibility: visible;
	}

	/* instant show/hide — appear-states never ride a transition (a stalled fade
	   after a nav jump would hide the card; the beat must not need it) */
	.card-slot {
		opacity: 0;
		max-height: 100%;
		display: grid;
		place-items: center;
	}

	.card-slot.shown {
		opacity: 1;
	}

	.payoff {
		pointer-events: auto;
		width: min(560px, 94vw);
		max-height: min(86dvh, 100%);
		overflow-y: auto;
		background: rgba(11, 14, 20, 0.82);
		border: 1px solid rgba(232, 236, 245, 0.12);
		border-radius: 16px;
		padding: 1.2rem 1.3rem 1.3rem;
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		font-variant-numeric: tabular-nums;
	}

	.overline {
		margin: 0 0 0.3rem;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.28em;
		text-transform: uppercase;
		color: var(--gold);
	}

	header {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 0.6rem;
	}

	.chip {
		flex: none;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 52px;
		height: 34px;
		padding: 0 10px;
		border-radius: 8px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		font-weight: 750;
		font-size: 0.9rem;
		letter-spacing: 0.06em;
	}

	h3 {
		margin: 0;
		font-size: clamp(1.15rem, 3vw, 1.5rem);
		line-height: 1.25;
		font-weight: 650;
	}

	.viz-label {
		margin: 0.7rem 0 0.25rem;
		font-size: 0.72rem;
		letter-spacing: 0.04em;
		color: var(--ink-dim);
	}

	.worm-fig {
		margin: 0;
	}

	.worm-fig svg {
		display: block;
		width: 100%;
		height: auto;
		background: rgba(6, 9, 14, 0.4);
		border-radius: 8px;
	}

	.axis {
		stroke: rgba(232, 236, 245, 0.2);
		stroke-width: 1;
	}

	.par {
		fill: none;
		stroke: #8f9ab4;
		stroke-width: 1.8;
	}

	.worm-casing {
		fill: none;
		stroke: rgba(6, 9, 14, 0.92);
		stroke-width: 7;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	.worm-stroke {
		fill: none;
		stroke: #ffd477;
		stroke-width: 2.6;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	.worm-stroke.replaying {
		stroke-dasharray: 1;
		stroke-dashoffset: 1;
		animation: draw 2200ms ease forwards;
	}

	@keyframes draw {
		to {
			stroke-dashoffset: 0;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.worm-stroke.replaying {
			animation: none;
			stroke-dashoffset: 0;
		}
	}

	.replay {
		margin-top: 0.3rem;
		min-height: 44px;
		padding: 0 0.4rem;
		border: none;
		background: none;
		color: var(--teal);
		font: inherit;
		font-size: 0.8rem;
		cursor: pointer;
	}

	.replay:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.headline {
		margin: 0.7rem 0 0;
		font-size: clamp(1rem, 2.4vw, 1.16rem);
		line-height: 1.5;
		color: var(--ink);
	}

	.elegy {
		margin: 0.7rem 0 0;
		font-size: 0.95rem;
		font-style: italic;
		color: var(--gold);
	}

	.note {
		margin: 0.5rem 0 0;
		font-size: 0.8rem;
		line-height: 1.4;
		color: var(--ink-dim);
	}

	.dealing {
		margin: 0;
		color: var(--ink-dim);
		letter-spacing: 0.08em;
	}

	.dagger-btn {
		display: inline-flex;
		align-items: center;
		min-height: 44px;
		margin: 0.8rem 0 0;
		padding: 0 0.2rem;
		border: none;
		background: none;
		color: var(--ink-dim);
		font: inherit;
		font-size: 0.82rem;
		cursor: pointer;
	}

	.dagger-btn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
		border-radius: 6px;
	}

	.change {
		display: block;
		margin-top: 0.6rem;
		min-height: 44px;
		padding: 0.5rem 1.1rem;
		border-radius: 999px;
		border: 1px solid rgba(232, 236, 245, 0.2);
		background: rgba(232, 236, 245, 0.06);
		color: var(--ink);
		font: inherit;
		font-size: 0.88rem;
		cursor: pointer;
	}

	.change:hover {
		background: rgba(232, 236, 245, 0.1);
	}

	.change:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
</style>
