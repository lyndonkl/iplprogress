<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import type { TeamMeta } from '$lib/field/types';
	import { pickedTeam, footnotesOpen } from '$lib/state';
	import { crestText } from '$lib/scenes/picker/crest';
	import { requestTeamChange } from '$lib/scenes/picker';
	import {
		loadCh4Data,
		payoffVariantFor,
		fmt1,
		runs,
		type Ch4Data,
		type PayoffVariant,
		type ResolvedPayoff
	} from './data';

	/**
	 * C4-11 — Team payoff card ("Your home ground's tide"). The chapter's finding in
	 * the reader's colours: par at your venue by era, plus a fingerprint (Chepauk
	 * holds its character; the flood plains rose most). Strictly template + ch4.json
	 * payoff.variants (10 IPL + 5 WPL designed empty states + the neutral all-India
	 * map), never hand-authored per team. Neutral / unknown picks get the full map.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const shown = $derived(reduced || progress >= 0.4);

	let ch4 = $state<Ch4Data | null>(null);
	let returnAnchor = $state<HTMLElement | null>(null);
	onMount(() => {
		let alive = true;
		loadCh4Data().then((d) => {
			if (alive) ch4 = d;
		});
		return () => {
			alive = false;
		};
	});

	const teams = $derived<TeamMeta[] | null>(field?.data.teams ?? null);
	const resolved = $derived<ResolvedPayoff | null>(ch4 ? payoffVariantFor(ch4, $pickedTeam) : null);
	const v = $derived<PayoffVariant | null>(resolved?.variant ?? null);
	const kind = $derived(resolved?.kind ?? 'neutral');
	const isFallback = $derived(resolved?.fallback ?? false);

	const crest = $derived(
		v !== null && teams !== null && kind !== 'neutral'
			? (teams.find((t) => t.league === (v.league as 'ipl' | 'wpl') && t.name === v.team) ?? null)
			: null
	);

	const title = $derived.by(() => {
		if (v === null) return '';
		if (kind === 'neutral') return 'The tide across India';
		if (kind === 'wpl') return 'The WPL is still on tour';
		return `${v.team} at home`;
	});

	/* ---- IPL era-tide bars ---- */
	const YLO = 120;
	const YHI = 210;
	const barH = (avg: number | null): number =>
		avg === null ? 0 : ((Math.min(YHI, Math.max(YLO, avg)) - YLO) / (YHI - YLO)) * 100;
	const accent = $derived(
		v?.fingerprint === 'holds_character'
			? 'var(--teal)'
			: v?.fingerprint === 'new_ground'
				? 'var(--gold)'
				: '#5b8cff'
	);
	const leagueAvg = $derived(v?.league_latest_avg_first_innings ?? null);

	/* ---- WPL season sparkline + neutral map ---- */
	const wplSeasons = $derived.by(() => {
		if (!v?.league_avg_first_innings_by_season) return [] as { season: number; avg: number }[];
		const m = v.league_avg_first_innings_by_season;
		return Object.keys(m)
			.map(Number)
			.sort((a, b) => a - b)
			.map((season) => ({ season, avg: m[String(season)] }));
	});
	const mapRanked = $derived(v?.india_map ? [...v.india_map].sort((a, b) => b.avg_first_innings - a.avg_first_innings) : []);
	const mapMax = $derived(mapRanked.length ? mapRanked[0].avg_first_innings : 200);
	const mapMin = 150;
</script>

<div class="return-anchor" bind:this={returnAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	<div class="card-slot" class:shown>
		<article class="payoff" aria-label="Chapter 4 team payoff, your home ground's tide">
			{#if v === null}
				<p class="overline">Chapter 4 payoff</p>
				<p class="dealing" role="status">Reading your ground…</p>
			{:else}
				<header>
					{#if crest !== null}
						<span class="chip" style:background={crest.color} style:color={crestText(crest.color)} aria-hidden="true">{crest.short}</span>
					{/if}
					<div>
						<p class="overline">Chapter 4 payoff</p>
						<h3>{title}</h3>
					</div>
				</header>

				{#if isFallback}
					<p class="note">No home ground for {$pickedTeam?.team} yet. Here's the whole map instead.</p>
				{/if}

				{#if kind === 'ipl' && v.par_by_era}
					<!-- the ground's tide, era by era -->
					<figure class="tide-fig">
						<div class="bars">
							{#each v.par_by_era as cell (cell.era)}
								<div class="bar-col">
									{#if cell.avg_first_innings !== null}
										<div class="bar-val">{runs(cell.avg_first_innings)}</div>
										<div
											class="bar"
											style="height:{barH(cell.avg_first_innings)}%; background:{cell.era === v.par_by_era[v.par_by_era.length - 1].era ? accent : '#56607a'}"
										></div>
									{:else}
										<div class="bar empty"></div>
									{/if}
									<span class="bar-lab">{cell.era.replace('20', "'")}</span>
								</div>
							{/each}
							{#if leagueAvg !== null}
								<div class="ref" style="bottom:{barH(leagueAvg)}%"><span>league {runs(leagueAvg)}</span></div>
							{/if}
						</div>
					</figure>
					<p class="headline">{v.headline}</p>
					{#if v.fingerprint_copy}<p class="fingerprint" style:color={accent}>{v.fingerprint_copy}</p>{/if}
				{:else if kind === 'wpl'}
					<!-- designed rotating-home empty state (authored) -->
					{#if wplSeasons.length}
						<figure class="tide-fig">
							<div class="bars">
								{#each wplSeasons as s (s.season)}
									<div class="bar-col">
										<div class="bar-val">{runs(s.avg)}</div>
										<div class="bar" style="height:{barH(s.avg)}%; background:var(--teal)"></div>
										<span class="bar-lab">’{String(s.season).slice(2)}</span>
									</div>
								{/each}
							</div>
						</figure>
					{/if}
					<p class="headline">{v.headline}</p>
					{#if v.fingerprint_copy}<p class="fingerprint" style:color="var(--teal)">{v.fingerprint_copy}</p>{/if}
				{:else}
					<!-- neutral: the whole map of India, ranked -->
					<p class="headline">{v.headline}</p>
					<ul class="map">
						{#each mapRanked as g (g.venue)}
							<li>
								<span class="g-city">{g.city}</span>
								<span class="g-bar-wrap">
									<span
										class="g-bar"
										style="width:{((g.avg_first_innings - mapMin) / (mapMax - mapMin)) * 100}%"
									></span>
								</span>
								<span class="g-val">{runs(g.avg_first_innings)}</span>
							</li>
						{/each}
					</ul>
				{/if}

				<button class="dagger-btn" onclick={() => footnotesOpen.set('venue-canon')} aria-label="How grounds are counted">ⓘ how we counted a ground's tide</button>
				<button class="change" type="button" onclick={() => requestTeamChange(returnAnchor)}>
					{kind === 'neutral' && !isFallback ? 'Pick a team and this card re-deals to your home ground' : 'Not your team? Change it'}
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

	.tide-fig {
		margin: 0.8rem 0 0.2rem;
	}

	.bars {
		position: relative;
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 0.5rem;
		height: 120px;
		padding: 0 0.2rem;
	}

	.bar-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: flex-end;
		height: 100%;
		flex: 1;
	}

	.bar {
		width: 100%;
		max-width: 42px;
		border-radius: 4px 4px 0 0;
	}

	.bar.empty {
		height: 4px;
		background: rgba(232, 236, 245, 0.08);
		border-radius: 2px;
	}

	.bar-val {
		font-size: 0.72rem;
		font-weight: 700;
		color: var(--ink);
	}

	.bar-lab {
		margin-top: 0.25rem;
		font-size: 0.6rem;
		color: var(--ink-dim);
		text-align: center;
	}

	.ref {
		position: absolute;
		left: 0.2rem;
		right: 0.2rem;
		border-top: 1.4px dashed rgba(232, 236, 245, 0.4);
		pointer-events: none;
	}

	.ref span {
		position: absolute;
		right: 0;
		top: -0.9rem;
		font-size: 0.6rem;
		color: var(--ink-dim);
	}

	.headline {
		margin: 0.8rem 0 0;
		font-size: clamp(1rem, 2.4vw, 1.14rem);
		line-height: 1.5;
		color: var(--ink);
	}

	.fingerprint {
		margin: 0.5rem 0 0;
		font-size: 0.95rem;
		font-weight: 650;
		line-height: 1.4;
	}

	.map {
		list-style: none;
		margin: 0.8rem 0 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.map li {
		display: grid;
		grid-template-columns: 5.5rem 1fr 2.4rem;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.82rem;
	}

	.g-city {
		color: var(--ink-dim);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.g-bar-wrap {
		height: 10px;
		background: rgba(232, 236, 245, 0.06);
		border-radius: 5px;
		overflow: hidden;
	}

	.g-bar {
		display: block;
		height: 100%;
		background: linear-gradient(90deg, #56607a, #5b8cff);
		border-radius: 5px;
	}

	.g-val {
		text-align: right;
		font-weight: 700;
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
