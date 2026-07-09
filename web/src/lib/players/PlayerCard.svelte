<script lang="ts">
	/**
	 * The player card (storyboard 9.0-9.8). Header signature leads with the unarguable
	 * VOLUME facts (balls, runs, dismissal rate) and only then the SR+ peak as TEMPO, so
	 * an accumulator is never made to look ordinary. Above the fold: header + SR+ river
	 * hero. Entry map / top duels / teleporter collapse behind one-line teasers that
	 * already carry the payload in words. A bowler-first card leads with the bowling
	 * panel instead. Small samples degrade to a stub; every panel suppresses rather than
	 * fakes. The footer bridges back into the Bowl.
	 */
	import type { PlayerCard } from './data';
	import SrPlusRiver from './SrPlusRiver.svelte';
	import EntryMap from './EntryMap.svelte';
	import DuelList from './DuelList.svelte';
	import Teleporter from './Teleporter.svelte';
	import { openInBowl } from './bowlLink';
	import {
		aliasLine,
		entryRoleShort,
		fmt1,
		fmtInt,
		leagueName,
		roleWord,
		seasonsLabel,
		teamsLabel
	} from './copy';

	let { card }: { card: PlayerCard } = $props();

	const h = $derived(card.header);
	const isBowlerFirst = $derived(
		!card.suppress.bowlingPanel && (card.suppress.srPlusRiver || h.role === 'bowl')
	);
	const isStub = $derived(card.smallSample && card.suppress.bowlingPanel);

	const showRiver = $derived(!isBowlerFirst && !card.suppress.srPlusRiver);
	const showEntry = $derived(
		!isBowlerFirst && !card.smallSample && !card.suppress.entryMap && card.entryMap != null
	);
	const showDuelsBat = $derived(!isBowlerFirst && card.duels.asBatter.length > 0);
	const showTeleporter = $derived(
		!isBowlerFirst && !card.smallSample && !card.suppress.teleporter && card.teleporter != null
	);
	const showBowling = $derived(!card.suppress.bowlingPanel);

	// Header signature line: volume first, tempo (SR+) last.
	const signature = $derived.by((): string => {
		const seg: string[] = [teamsLabel(h.teams), seasonsLabel(h.firstSeason, h.lastSeason)];
		if (isBowlerFirst) {
			seg.push(`${fmtInt(h.ballsBowled)} balls bowled`);
			return seg.join('  ·  ');
		}
		seg.push(`${fmtInt(h.ballsFaced)} balls`);
		if (h.runs != null) seg.push(`${fmtInt(h.runs)} runs`);
		if (h.ballsPerDismissal != null) seg.push(`out once every ${fmtInt(h.ballsPerDismissal)} balls`);
		if (h.peakSRPlus) seg.push(`peak SR+ ${fmt1(h.peakSRPlus.srplus)} in ${h.peakSRPlus.season}`);
		return seg.join('  ·  ');
	});

	const basis = $derived.by((): string => {
		const f = card.basisNote.ballsFaced;
		const b = card.basisNote.ballsBowled;
		if (f > 0 && b > 0) return `Based on ${fmtInt(f)} balls faced and ${fmtInt(b)} bowled.`;
		if (f > 0) return `Based on ${fmtInt(f)} balls faced.`;
		return `Based on ${fmtInt(b)} balls bowled.`;
	});

	const alias = $derived(aliasLine(h.name, h.aliases));
	const topPct = $derived(
		card.teleporter ? Math.max(1, Math.round(100 - card.teleporter.eraPercentile)) : 0
	);
	const topBatDuel = $derived(card.duels.asBatter[0] ?? null);
	const topBowlDuel = $derived(card.duels.asBowler[0] ?? null);

	// Desktop opens the collapsibles by default; mobile keeps them collapsed (the fold).
	let openEntry = $state(false);
	let openDuels = $state(false);
	let openTele = $state(false);
	let openBowl = $state(false);
	$effect(() => {
		if (typeof window !== 'undefined' && window.matchMedia('(min-width: 56rem)').matches) {
			openEntry = true;
			openDuels = true;
			openTele = true;
			openBowl = true;
		}
	});

	let bowlPending = $state(false);
	async function bridge(opts: { batterNames?: string[]; bowlerNames?: string[] }): Promise<void> {
		if (bowlPending) return;
		bowlPending = true;
		try {
			await openInBowl(opts);
		} finally {
			bowlPending = false;
		}
	}
	const openAsBatter = (oppName: string) =>
		bridge({ batterNames: card.nameUnion, bowlerNames: [oppName] });
	const openAsBowler = (oppName: string) =>
		bridge({ batterNames: [oppName], bowlerNames: card.nameUnion });
	const seeInBowl = () =>
		isBowlerFirst
			? bridge({ bowlerNames: card.nameUnion })
			: bridge({ batterNames: card.nameUnion });
</script>

<article class="card">
	<header>
		<div class="name-row">
			<h1>{h.name}</h1>
			<span class="role-badge">{roleWord(h.role)}</span>
		</div>
		<div class="chips">
			{#each h.leagues as lg (lg)}
				<span class="chip league">{leagueName(lg)}</span>
			{/each}
			{#each h.teams as t (t)}
				<span class="chip team">{t}</span>
			{/each}
		</div>
		<p class="signature">{signature}</p>
		<p class="basis">{basis}</p>
		{#if alias}
			<p class="alias">{alias}</p>
		{/if}
	</header>

	{#if isStub}
		<section class="stub">
			<p class="stub-note">Small sample, so read this one lightly.</p>
			<p class="stub-sub">
				Under 100 balls in their main role is too little to price their scoring against an era, so the
				SR+ river and the 2026 teleporter are held back rather than faked.
			</p>
		</section>
	{:else}
		<div class="panels">
			{#if isBowlerFirst && showBowling}
				<section class="hero panel">
					<h2 class="panel-title">As a bowler</h2>
					<p class="caveat">
						Raw matchups, not era-adjusted yet. The era-fair version, runs saved versus an average
						bowler, comes next.
					</p>
					{#if topBowlDuel}
						<DuelList
							duels={card.duels.asBowler}
							mu={card.duels.eb.mu}
							onOpen={openAsBowler}
							pending={bowlPending}
						/>
					{:else}
						<p class="empty">Top matchups arrive with the era-fair bowling metric next.</p>
					{/if}
				</section>
			{/if}

			{#if showRiver}
				<section class="hero panel">
					<h2 class="panel-title">How fast they scored, priced against their era</h2>
					<SrPlusRiver points={card.srPlusRiver} peak={h.peakSRPlus} league={card.primaryLeague} />
				</section>
			{/if}

			<div class="grid">
				{#if showTeleporter && card.teleporter}
					<details class="panel collapsible" bind:open={openTele}>
						<summary>
							<span class="teaser-label">Teleport their peak to 2026</span>
							<span class="teaser-text">How far above their own era they sat: the top {topPct}%.</span>
							<span class="hint" aria-hidden="true">Tap to re-price</span>
						</summary>
						<div class="collapsible-body">
							<Teleporter tp={card.teleporter} />
						</div>
					</details>
				{/if}

				{#if showEntry && card.entryMap}
					<details class="panel collapsible" bind:open={openEntry}>
						<summary>
							<span class="teaser-label">Where they came in</span>
							<span class="teaser-text">
								Usually around ball {fmtInt(card.entryMap.medianEntryBall)}{card.entryMap.brightest
									? `, ${entryRoleShort(card.entryMap.brightest.role)}`
									: ''}.
							</span>
							<span class="hint" aria-hidden="true">Tap to see</span>
						</summary>
						<div class="collapsible-body">
							<EntryMap map={card.entryMap} />
						</div>
					</details>
				{/if}

				{#if showDuelsBat}
					<details class="panel collapsible" bind:open={openDuels}>
						<summary>
							<span class="teaser-label">Who they battled most</span>
							<span class="teaser-text">
								{#if topBatDuel}
									Biggest matchup: {topBatDuel.balls} balls vs {topBatDuel.oppName}.
								{:else}
									Their most-faced bowlers.
								{/if}
							</span>
							<span class="hint" aria-hidden="true">Tap for the list</span>
						</summary>
						<div class="collapsible-body">
							<DuelList
								duels={card.duels.asBatter}
								mu={card.duels.eb.mu}
								onOpen={openAsBatter}
								pending={bowlPending}
							/>
						</div>
					</details>
				{/if}

				{#if !isBowlerFirst && showBowling}
					<details class="panel collapsible" bind:open={openBowl}>
						<summary>
							<span class="teaser-label">They bowled too</span>
							<span class="teaser-text">
								{fmtInt(h.ballsBowled)} balls bowled{topBowlDuel
									? `, biggest matchup vs ${topBowlDuel.oppName}`
									: ''}.
							</span>
							<span class="hint" aria-hidden="true">Tap for matchups</span>
						</summary>
						<div class="collapsible-body">
							<p class="caveat">Raw matchups, not era-adjusted yet.</p>
							{#if topBowlDuel}
								<DuelList
									duels={card.duels.asBowler}
									mu={card.duels.eb.mu}
									onOpen={openAsBowler}
									pending={bowlPending}
								/>
							{:else}
								<p class="empty">No standout bowling matchups on record.</p>
							{/if}
						</div>
					</details>
				{/if}
			</div>
		</div>
	{/if}

	<footer>
		<button class="bowl-btn" onclick={seeInBowl} disabled={bowlPending}>
			{#if bowlPending}
				Opening the field...
			{:else if isBowlerFirst}
				See every ball they bowled
			{:else}
				See every ball they faced
			{/if}
		</button>
		<p class="bowl-note">Their slice of the 316,199-ball field.</p>
	</footer>
</article>

<style>
	.card {
		display: flex;
		flex-direction: column;
		gap: 1.4rem;
	}
	header {
		border-bottom: 1px solid rgba(232, 236, 245, 0.1);
		padding-bottom: 1rem;
	}
	.name-row {
		display: flex;
		align-items: baseline;
		flex-wrap: wrap;
		gap: 0.6rem;
	}
	h1 {
		margin: 0;
		font-size: clamp(1.6rem, 5vw, 2.3rem);
		line-height: 1.15;
	}
	.role-badge {
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--gold);
		border: 1px solid rgba(232, 163, 61, 0.4);
		border-radius: 999px;
		padding: 0.15rem 0.6rem;
	}
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		margin: 0.7rem 0 0;
	}
	.chip {
		font-size: 0.75rem;
		font-weight: 600;
		border-radius: 6px;
		padding: 0.2rem 0.55rem;
		border: 1px solid rgba(232, 236, 245, 0.14);
		color: var(--ink-dim);
	}
	.chip.league {
		color: var(--ink);
		border-color: rgba(232, 236, 245, 0.28);
	}
	.signature {
		margin: 0.8rem 0 0;
		font-size: 0.95rem;
		line-height: 1.5;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	.basis {
		margin: 0.4rem 0 0;
		font-size: 0.78rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}
	.alias {
		margin: 0.25rem 0 0;
		font-size: 0.78rem;
		color: var(--ink-dim);
		font-style: italic;
	}
	.panels {
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
	}
	.panel {
		background: rgba(232, 236, 245, 0.02);
		border: 1px solid rgba(232, 236, 245, 0.07);
		border-radius: 12px;
		padding: 1rem 1.1rem;
	}
	.panel-title {
		margin: 0 0 0.6rem;
		font-size: 1.05rem;
		font-weight: 650;
	}
	.caveat {
		margin: 0 0 0.7rem;
		font-size: 0.82rem;
		line-height: 1.4;
		color: var(--gold);
	}
	.empty {
		margin: 0;
		font-size: 0.85rem;
		color: var(--ink-dim);
	}
	.grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 1.2rem;
	}
	.collapsible {
		padding: 0;
	}
	summary {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		padding: 0.85rem 1.1rem;
		min-height: 44px;
		cursor: pointer;
		list-style: none;
		border-radius: 12px;
	}
	summary::-webkit-details-marker {
		display: none;
	}
	summary:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: -2px;
	}
	.teaser-label {
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--gold);
	}
	.teaser-text {
		font-size: 0.95rem;
		line-height: 1.4;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	.hint {
		font-size: 0.75rem;
		color: var(--teal);
	}
	.collapsible-body {
		padding: 0 1.1rem 1.1rem;
	}
	.stub {
		background: rgba(232, 236, 245, 0.02);
		border: 1px solid rgba(232, 236, 245, 0.07);
		border-radius: 12px;
		padding: 1rem 1.1rem;
	}
	.stub-note {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: var(--gold);
	}
	.stub-sub {
		margin: 0.5rem 0 0;
		font-size: 0.88rem;
		line-height: 1.45;
		color: var(--ink-dim);
	}
	footer {
		border-top: 1px solid rgba(232, 236, 245, 0.1);
		padding-top: 1.2rem;
	}
	.bowl-btn {
		width: 100%;
		min-height: 48px;
		padding: 0.8rem 1rem;
		font: inherit;
		font-weight: 650;
		color: var(--bg);
		background: var(--gold);
		border: none;
		border-radius: 10px;
		cursor: pointer;
	}
	.bowl-btn:hover:not(:disabled),
	.bowl-btn:focus-visible {
		filter: brightness(1.08);
		outline: none;
	}
	.bowl-btn:focus-visible {
		outline: 2px solid var(--ink);
		outline-offset: 2px;
	}
	.bowl-btn:disabled {
		cursor: progress;
		opacity: 0.75;
	}
	.bowl-note {
		margin: 0.5rem 0 0;
		font-size: 0.78rem;
		color: var(--ink-dim);
		text-align: center;
		font-variant-numeric: tabular-nums;
	}

	@media (min-width: 56rem) {
		.grid {
			grid-template-columns: 1fr 1fr;
		}
	}
</style>
