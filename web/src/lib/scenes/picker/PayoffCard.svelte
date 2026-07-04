<script lang="ts">
	import { onMount } from 'svelte';
	import type { TeamMeta } from '$lib/field/types';
	import { pickedTeam, type TeamPick } from '$lib/state';
	import {
		loadPayoffCh1,
		payoffVariantFor,
		type IgnitionEraRow,
		type PayoffCh1
	} from './payoff';
	import { crestText, lineTint } from './crest';
	import { requestTeamChange } from './changeteam';
	import IgnitionStrip from './IgnitionStrip.svelte';
	import MaturityLines from './MaturityLines.svelte';

	/**
	 * The reusable end-of-chapter payoff card (storyboard C1-7): strictly
	 * template + per-team JSON from data/payoff/ch1.json — headlines verbatim,
	 * never hand-authored. Three templates: IPL (mini ignition strip), WPL (the
	 * bespoke maturity-clock card with the sparkline pair and the clock plant),
	 * Neutral (league-wide). Designed empty states: born-into-the-attack-era
	 * franchises (authored in JSON), unknown pick → Neutral with a note, data
	 * unavailable → an honest card, still no dead ends.
	 *
	 * Drop-in: with no props it reads the picked team from the store and
	 * fetches the JSON itself (cached module-wide, inside the Ch 1 payload
	 * budget). Scene builders may inject `payoff`/`pick` for tests/snapshots.
	 */
	interface Props {
		/** injected payoff data; undefined → self-load, null → unavailable state */
		payoff?: PayoffCh1 | null;
		/** injected pick; undefined → the pickedTeam store */
		pick?: TeamPick | null;
		/** teams.json rows (field.data.teams) for the typographic crest colors */
		teams?: TeamMeta[] | null;
		/** override the "change it" behavior (default: jump to #picker, return here) */
		onChangeTeam?: (() => void) | null;
	}
	let { payoff = undefined, pick = undefined, teams = null, onChangeTeam = null }: Props =
		$props();

	let rootEl = $state<HTMLElement | null>(null);
	let selfLoaded = $state<PayoffCh1 | null>(null);
	let selfStatus = $state<'loading' | 'ready' | 'unavailable'>('loading');

	onMount(() => {
		if (payoff === undefined) void refresh();
	});

	async function refresh(): Promise<void> {
		selfStatus = 'loading';
		const p = await loadPayoffCh1();
		selfLoaded = p;
		selfStatus = p !== null ? 'ready' : 'unavailable';
	}

	const data = $derived(payoff === undefined ? selfLoaded : payoff);
	const status = $derived(
		payoff === undefined ? selfStatus : payoff === null ? 'unavailable' : 'ready'
	);

	const effPick = $derived(pick === undefined ? $pickedTeam : pick);
	const resolved = $derived(data !== null ? payoffVariantFor(data, effPick) : null);
	const v = $derived(resolved?.variant ?? null);
	const kind = $derived(resolved?.kind ?? 'neutral');
	const isFallback = $derived(resolved?.fallback ?? false);

	const crest = $derived(
		v !== null && teams !== null && kind !== 'neutral'
			? (teams.find((t) => t.league === v.league && t.name === v.team) ?? null)
			: null
	);
	const accent = $derived(crest !== null ? lineTint(crest.color) : '#e8a33d');

	const title = $derived.by(() => {
		if (v === null) return '';
		if (kind === 'neutral') return 'The league’s first ten balls';
		if (kind === 'wpl') return `${v.team}, four seasons in`;
		return `${v.team}’s first ten balls`;
	});

	function rowFor(era: string): IgnitionEraRow | null {
		return v?.ignition_by_era.find((r) => r.era === era && r.sr_1_10 !== null) ?? null;
	}
	const earlyRow = $derived(v !== null ? rowFor(v.era_labels.early) : null);
	const recentRow = $derived(v !== null ? rowFor(v.era_labels.recent) : null);

	/* ---- WPL maturity-clock template pieces ------------------------------- */
	const clock = $derived(v?.maturity_clock ?? null);
	const wplBody = $derived(kind === 'wpl' && clock !== null);
	const iplRR = $derived(clock?.rr_by_year.ipl ?? []);
	const wplRR = $derived(clock?.rr_by_year.wpl ?? []);

	/**
	 * The JSON's discrete small-sample honesty sentence (v2 field: non-empty ⟺
	 * small_sample), rendered verbatim between the league clause and the team
	 * pair (storyboard C1-7 snapshot-review note). No prose parsing — the
	 * template renders the field as shipped (finding #8).
	 */
	const honesty = $derived(v !== null && v.honesty !== '' ? v.honesty : null);

	/** the team pair as its two discrete strike-rate numbers — the compact
	 *  ≤3-number form the WPL headline wants; the verbose team_pair sentence is
	 *  the fallback below, never the regex-spliced full headline */
	const teamPair = $derived.by(() => {
		if (v === null) return null;
		if (v.first10_sr_early_era === null || v.first10_sr_recent_era === null) return null;
		return { early: v.first10_sr_early_era, recent: v.first10_sr_recent_era };
	});

	const pronoun = $derived(v?.league === 'wpl' ? 'her' : 'his');
	const starterTeam = $derived(v === null ? '' : v.team === 'Neutral' ? 'IPL' : v.team);

	const f1 = (x: number): string => x.toFixed(1);
	const f2 = (x: number): string => x.toFixed(2);
	const num = (x: number): string => x.toLocaleString('en-US');

	/* ---- the card dagger (tap/keyboard disclosure, never hover) ----------- */
	const daggerLines = $derived.by(() => {
		if (v === null) return [] as string[];
		const lines: string[] = [];
		if (wplBody && clock !== null) {
			lines.push(
				`At the same league age the IPL’s run rate fell: ${f2(iplRR[0])} → ${f2(iplRR[iplRR.length - 1])} over league years 1–4 (IPL year 1 = 2008, WPL year 1 = 2023).`
			);
			lines.push(
				`Year by year — IPL ${iplRR.map(f2).join(' / ')} · WPL ${wplRR.map(f2).join(' / ')}. Neither path is a straight line; endpoints alone flatter both.`
			);
			lines.push(
				`Eras on this card: ${v.era_labels.early} vs ${v.era_labels.recent}. First-ten-ball samples: ${num(v.sample_balls_early)} and ${num(v.sample_balls_recent)} balls.`
			);
			lines.push(clock.definition);
		} else {
			lines.push(
				v.empty_state
					? `No ${v.era_labels.early} innings to compare — the ${v.era_labels.recent} sample is ${num(v.sample_balls_recent)} balls.`
					: `Era bands: ${v.era_labels.early} vs ${v.era_labels.recent}. First-ten-ball samples: ${num(v.sample_balls_early)} and ${num(v.sample_balls_recent)} balls.`
			);
			lines.push(
				'Franchise renames merge histories — Delhi Daredevils → Delhi Capitals, Kings XI Punjab → Punjab Kings, Royal Challengers Bangalore → Bengaluru.'
			);
		}
		if (v.fastest_starter !== undefined) {
			lines.push(
				`Fastest-starter rule: minimum 100 first-ten balls faced (${v.fastest_starter.name}: ${num(v.fastest_starter.first10_balls)}).`
			);
		}
		lines.push('Wides don’t count toward balls faced; no-balls do.');
		return lines;
	});

	const changeLabel = $derived(
		kind === 'neutral' && !isFallback
			? 'Pick a team — this card re-deals in its colors'
			: 'Not your team? Change it'
	);

	function changeTeam(): void {
		if (onChangeTeam !== null) onChangeTeam();
		else requestTeamChange(rootEl);
	}
</script>

<article class="payoff" bind:this={rootEl} aria-label="Chapter 1 team payoff">
	{#if status === 'loading'}
		<p class="overline">Chapter 1 payoff</p>
		<p class="dealing" role="status">Dealing your card…</p>
	{:else if v === null}
		<!-- designed empty state: data unavailable — honest, no dead end -->
		<p class="overline">Chapter 1 payoff</p>
		<h3>The card didn’t arrive.</h3>
		<p class="note">
			This card renders from the pipeline’s payoff data, which didn’t load. The chapter above
			stands on its own — nothing in it depended on the card.
		</p>
		{#if payoff === undefined}
			<button class="change" type="button" onclick={() => void refresh()}>Try again</button>
		{/if}
	{:else}
		<header>
			{#if crest !== null}
				<span
					class="chip"
					style:background={crest.color}
					style:color={crestText(crest.color)}
					aria-hidden="true"
				>
					{crest.short}
				</span>
			{/if}
			<div>
				<p class="overline">Chapter 1 payoff</p>
				<h3>{title}</h3>
			</div>
		</header>

		{#if isFallback}
			<p class="note">No card for {effPick?.team} yet — here’s the league-wide one.</p>
		{/if}

		{#if wplBody && clock !== null}
			<!-- the bespoke WPL card: maturity clock, two clocks framing, no deficit language -->
			<p class="viz-label">Run rate, league years 1–4 — one scale</p>
			<MaturityLines ipl={iplRR} wpl={wplRR} />
			<p class="headline">
				Four seasons in, your league is <strong>already climbing</strong>: run rate
				<strong class="wpl-num">{f2(wplRR[0])} → {f2(wplRR[wplRR.length - 1])}</strong> — while
				the IPL at the same age was still falling.
			</p>
			{#if honesty !== null}
				<p class="honesty">{honesty}</p>
			{/if}
			{#if teamPair !== null}
				<p class="headline pair">
					{v.team}’s first ten balls:
					<strong class="wpl-num">{f1(teamPair.early)} → {f1(teamPair.recent)}</strong>.
				</p>
			{:else}
				<!-- discrete team-pair field (no honesty tail) — never the full
				     headline, which would duplicate the honesty sentence above -->
				<p class="headline pair">{v.team_pair}</p>
			{/if}
			<p class="plant">Remember that clock. We’ll come back to it.</p>
		{:else}
			<p class="viz-label">Strike rate: first ten balls, then the next ten — 0–180 scale</p>
			<IgnitionStrip early={earlyRow} recent={recentRow} {accent} />
			{#if v.empty_state}
				<p class="note">No {v.era_labels.early} innings — the club didn’t exist yet.</p>
			{/if}
			<p class="headline">{v.headline}</p>
		{/if}

		{#if v.fastest_starter !== undefined}
			<p class="starter">
				Fastest starter in {starterTeam} history: <strong>{v.fastest_starter.name}</strong> — SR
				<strong>{f1(v.fastest_starter.first10_sr)}</strong> on {pronoun} first ten balls (min 100
				balls).
			</p>
		{/if}

		<details class="dagger">
			<summary><span aria-hidden="true">ⓘ</span> the fine print</summary>
			<div class="fine">
				{#each daggerLines as line (line)}
					<p>{line}</p>
				{/each}
			</div>
		</details>

		<button class="change" type="button" onclick={changeTeam}>{changeLabel}</button>
	{/if}
</article>

<style>
	.payoff {
		pointer-events: auto;
		width: min(560px, 94vw);
		max-height: min(86dvh, 100%);
		overflow-y: auto;
		background: rgba(11, 14, 20, 0.78);
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
		margin: 0.9rem 0 0.25rem;
		font-size: 0.7rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.headline {
		margin: 0.7rem 0 0;
		font-size: clamp(1rem, 2.4vw, 1.18rem);
		line-height: 1.5;
		color: var(--ink);
	}

	.headline.pair {
		margin-top: 0.55rem;
	}

	.wpl-num {
		color: var(--teal);
	}

	.honesty {
		margin: 0.55rem 0 0;
		font-size: 0.86rem;
		line-height: 1.45;
		color: var(--ink-dim);
	}

	.plant {
		margin: 0.8rem 0 0;
		font-size: 0.92rem;
		font-style: italic;
		color: var(--gold);
	}

	.starter {
		margin: 0.85rem 0 0;
		padding-top: 0.75rem;
		border-top: 1px solid rgba(232, 236, 245, 0.1);
		font-size: 0.92rem;
		line-height: 1.5;
		color: var(--ink);
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

	.dagger {
		margin-top: 0.8rem;
	}

	.dagger summary {
		display: flex;
		align-items: center;
		gap: 6px;
		min-height: 44px;
		cursor: pointer;
		font-size: 0.82rem;
		color: var(--ink-dim);
		list-style: none;
	}

	.dagger summary::-webkit-details-marker {
		display: none;
	}

	.dagger summary:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
		border-radius: 6px;
	}

	.dagger[open] summary {
		color: var(--ink);
	}

	.fine p {
		margin: 0 0 0.55rem;
		font-size: 0.8rem;
		line-height: 1.5;
		color: var(--ink-dim);
	}

	.change {
		margin-top: 0.9rem;
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

	h3:only-of-type {
		margin-top: 0;
	}
</style>
