<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import type { TeamMeta } from '$lib/field/types';
	import { pickedTeam, footnotesOpen } from '$lib/state';
	import { crestText } from '$lib/scenes/picker/crest';
	import { requestTeamChange } from '$lib/scenes/picker';
	import {
		loadCh3Data,
		gravityVariantFor,
		fmt2,
		int,
		type Ch3Data,
		type GravityVariant,
		type ResolvedGravity
	} from './data';
	import FrontierScaffold from './FrontierScaffold.svelte';

	/**
	 * C3-8 — Team payoff card ("Your gravity-defier"). The chapter's finding re-told
	 * in the reader's colours: the bowler-season at your franchise that beat its
	 * era's tide by the most (best True Economy). Strictly template + ch3.json
	 * gravity_defiers.variants (20 franchise variants incl. the WPL short-sample
	 * state), never hand-authored. ARITHMETIC LOCK (card == artifact): {league_econ}
	 * is the going rate for the exact overs the bowler bowled, so
	 * {league_econ} − {econ} = {gap} is the True-Economy differential that ranks
	 * "biggest" — the visible subtraction IS the ranking metric.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 50 / 160 — show past the morph */
	const shown = $derived(reduced || progress >= 0.4);

	let ch3 = $state<Ch3Data | null>(null);
	let returnAnchor = $state<HTMLElement | null>(null);
	onMount(() => {
		let alive = true;
		loadCh3Data().then((d) => {
			if (alive) ch3 = d;
		});
		return () => {
			alive = false;
		};
	});

	const teams = $derived<TeamMeta[] | null>(field?.data.teams ?? null);
	const resolved = $derived<ResolvedGravity | null>(ch3 ? gravityVariantFor(ch3, $pickedTeam) : null);
	const v = $derived<GravityVariant | null>(resolved?.variant ?? null);
	const kind = $derived(resolved?.kind ?? 'neutral');
	const isFallback = $derived(resolved?.fallback ?? false);
	/* the young-league short-sample state is a WPL-only designed empty state */
	const tooSoon = $derived(v?.league === 'wpl');
	const pronoun = $derived(v?.league === 'wpl' ? 'She' : 'He');

	const crest = $derived(
		v !== null && teams !== null && kind !== 'neutral'
			? (teams.find((t) => t.league === v.league && t.name === v.franchise) ?? null)
			: null
	);

	const title = $derived.by(() => {
		if (v === null) return '';
		if (kind === 'neutral') return 'The IPL’s gravity-defier';
		if (tooSoon) return 'Too soon to crown one';
		return `${v.franchise}’s gravity-defier`;
	});

	/* ---- the economy-vs-tide number line (the shaded gap IS true_economy) ---- */
	const LO = 4;
	const HI = 11;
	const VBW = 320;
	const VBH = 66;
	const PAD = 14;
	const xAt = (econ: number): number =>
		PAD + ((Math.min(HI, Math.max(LO, econ)) - LO) / (HI - LO)) * (VBW - 2 * PAD);
	const econX = $derived(v ? xAt(v.economy) : 0);
	const parX = $derived(v ? xAt(v.par_economy) : 0);
</script>

<div class="return-anchor" bind:this={returnAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	<!-- faint persistent orientation anchors behind the payoff card (held C3-3..C3-8) -->
	<FrontierScaffold {field} faint />

	<div class="card-slot" class:shown>
		<article class="payoff" aria-label="Chapter 3 team payoff, your gravity-defier">
			{#if v === null}
				<p class="overline">Chapter 3 payoff</p>
				<p class="dealing" role="status">Dealing your card…</p>
			{:else}
				<header>
					{#if crest !== null}
						<span class="chip" style:background={crest.color} style:color={crestText(crest.color)} aria-hidden="true">{crest.short}</span>
					{/if}
					<div>
						<p class="overline">Chapter 3 payoff</p>
						<h3>{title}</h3>
					</div>
				</header>

				{#if isFallback}
					<p class="note">No card for {$pickedTeam?.team} yet. Here’s the league-wide one.</p>
				{/if}

				<!-- the economy-vs-tide line: the bowler's economy (left = cheaper) against
				     the going rate he actually bowled to; the shaded gap IS his True Economy -->
				<p class="viz-label">{v.bowler} · {v.season} · leaked vs the going rate</p>
				<figure class="tide-fig">
					<svg viewBox="0 0 {VBW} {VBH}" role="img" aria-label="{v.bowler} leaked {fmt2(v.economy)} an over against a going rate of {fmt2(v.par_economy)}, a gap of {fmt2(v.true_economy)}">
						<line x1={PAD} y1={VBH - 20} x2={VBW - PAD} y2={VBH - 20} class="axis" />
						<!-- the gap (True Economy) -->
						<rect x={econX} y={VBH - 26} width={Math.max(0, parX - econX)} height="12" class="gap" />
						<!-- the going-rate tide mark -->
						<line x1={parX} y1={VBH - 34} x2={parX} y2={VBH - 6} class="par" />
						<text x={parX} y={VBH - 38} class="par-lab" text-anchor="middle">tide {fmt2(v.par_economy)}</text>
						<!-- the bowler's economy mark -->
						<circle cx={econX} cy={VBH - 20} r="4.5" class="econ-dot" />
						<text x={econX} y={VBH - 2} class="econ-lab" text-anchor="middle">him {fmt2(v.economy)}</text>
					</svg>
				</figure>

				{#if tooSoon}
					<!-- designed short-sample state (the WPL five) — authored, not blank -->
					<p class="headline">
						<strong>Four seasons is not a long enough tide to name a gravity-defier yet.</strong>
						Here is who is closest at {v.franchise} so far: {v.bowler}, {v.season},
						{fmt2(v.economy)} an over against a going rate of {fmt2(v.par_economy)} in the overs
						{pronoun.toLowerCase()} bowled. Ask again in a few years, when the water is higher.
					</p>
				{:else if kind === 'neutral'}
					<p class="headline">
						Across all of IPL history, the biggest gap between a bowler and his era's tide belongs to
						<strong>{v.bowler}, {v.season}.</strong> He leaked {fmt2(v.economy)} an over when the going
						rate in the exact overs he bowled was {fmt2(v.par_economy)}. That is
						<strong>{fmt2(v.true_economy)} runs an over better than the tide.</strong>
						Everyone else was drowning. He swam.
					</p>
				{:else}
					<p class="headline">
						<strong>{v.bowler} · {v.season}.</strong> He leaked {fmt2(v.economy)} an over. In the exact
						overs and grounds he bowled, the going rate was {fmt2(v.par_economy)}. That is
						<strong>{fmt2(v.true_economy)} runs an over better than the tide,</strong> the biggest gap
						any {v.franchise} bowler ever managed. Everyone else was drowning. He swam.
					</p>
					{#if v.small_sample}
						<p class="caveat">A short spell, {int(v.balls)} balls, so read it as a flash of the idea, not a full season.</p>
					{/if}
				{/if}

				<button class="dagger-btn" onclick={() => footnotesOpen.set('true-economy')} aria-label="How beating the tide was counted">ⓘ how we counted beating the tide</button>
				<button class="change" type="button" onclick={() => requestTeamChange(returnAnchor)}>
					{kind === 'neutral' && !isFallback ? 'Pick a team and this card re-deals in its colours' : 'Not your team? Change it'}
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

	.tide-fig {
		margin: 0;
	}

	.tide-fig svg {
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

	.gap {
		fill: rgba(46, 196, 182, 0.32);
	}

	.par {
		stroke: #8f9ab4;
		stroke-width: 2;
	}

	.par-lab {
		fill: #b9c2d6;
		font-size: 10px;
		font-variant-numeric: tabular-nums;
	}

	.econ-dot {
		fill: var(--teal);
	}

	.econ-lab {
		fill: var(--teal);
		font-size: 10px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.headline {
		margin: 0.7rem 0 0;
		font-size: clamp(1rem, 2.4vw, 1.16rem);
		line-height: 1.5;
		color: var(--ink);
	}

	.caveat {
		margin: 0.5rem 0 0;
		font-size: 0.85rem;
		font-style: italic;
		color: var(--ink-dim);
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
