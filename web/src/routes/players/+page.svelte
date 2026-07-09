<script lang="ts">
	/**
	 * /players (storyboard 9.1, 9.9) - the search surface + card host. A DOM/SVG route
	 * modelled on /methods: prerendered, imports only $app helpers and the pure players
	 * data layer, and never touches the WebGL field. The card is deep-linked by a query
	 * param (?p=<pid>) so the prerendered shell stays a single static page and a card
	 * link a mate opens resolves client-side. Search is diacritic-insensitive, prefix
	 * before fuzzy, disambiguates namesakes on a secondary line, and tie-breaks by career
	 * balls (all in $lib/players/data). Empty state lands on suggested cards plus a
	 * Surprise-me, never blank.
	 */
	import { base } from '$app/paths';
	import { browser } from '$app/environment';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import {
		loadPlayerCard,
		loadPlayersIndex,
		searchPlayers,
		type PlayerCard as PlayerCardT,
		type PlayersIndex
	} from '$lib/players/data';
	import PlayerCard from '$lib/players/PlayerCard.svelte';
	import { leagueName, roleWord, seasonsLabel } from '$lib/players/copy';

	const SUGGESTED = ['V Kohli', 'JJ Bumrah', 'Shafali Verma', 'SP Narine'];

	let index = $state<PlayersIndex | null>(null);
	let indexError = $state(false);
	let query = $state('');
	let selectedPid = $state<string | null>(null);
	let card = $state<PlayerCardT | null>(null);
	let cardError = $state(false);
	let cardLoading = $state(false);
	let searchInput = $state<HTMLInputElement | null>(null);

	// Load the registry / search index once (module promise is cached anyway).
	$effect(() => {
		loadPlayersIndex()
			.then((i) => (index = i))
			.catch(() => (indexError = true));
	});

	// The selected pid is the URL's ?p= (reactive to client navigation; null on the
	// prerendered shell, so the server always renders the search surface).
	$effect(() => {
		selectedPid = browser ? page.url.searchParams.get('p') : null;
	});

	// Assemble the card whenever the pid changes; cancel a stale load on re-navigation.
	$effect(() => {
		const pid = selectedPid;
		if (!pid) {
			card = null;
			cardError = false;
			cardLoading = false;
			return;
		}
		cardLoading = true;
		cardError = false;
		let cancelled = false;
		loadPlayerCard(pid)
			.then((c) => {
				if (!cancelled) {
					card = c;
					cardLoading = false;
				}
			})
			.catch(() => {
				if (!cancelled) {
					cardError = true;
					cardLoading = false;
				}
			});
		return () => {
			cancelled = true;
		};
	});

	// Focus the search field when the search surface is the thing on screen.
	$effect(() => {
		if (browser && !selectedPid && searchInput) searchInput.focus();
	});

	const results = $derived(index && query.trim() ? searchPlayers(index, query, 20) : []);

	const suggested = $derived.by((): { pid: string; name: string }[] => {
		if (!index) return [];
		const out: { pid: string; name: string }[] = [];
		for (const name of SUGGESTED) {
			const pids = index.name_to_pids[name];
			if (pids && pids.length) out.push({ pid: pids[0], name });
		}
		return out;
	});

	function select(pid: string): void {
		query = '';
		void goto(`${base}/players/?p=${pid}`);
	}

	function newSearch(): void {
		void goto(`${base}/players/`);
	}

	function surprise(): void {
		if (!index) return;
		const pool = index.players.filter((p) => p.balls_faced >= 100 || p.balls_bowled >= 100);
		if (!pool.length) return;
		const pick = pool[Math.floor(Math.random() * pool.length)];
		select(pick.pid);
	}

	function onSubmit(e: SubmitEvent): void {
		e.preventDefault();
		if (results.length) select(results[0].pid);
	}
</script>

<svelte:head>
	<title>Every Ball Ever - Player cards</title>
	<meta
		name="description"
		content="Search any of the players who ever batted or bowled in the IPL or WPL and get their card: how fast they scored versus their era, where they walked in, their biggest duels, and an honest 2026 teleport."
	/>
</svelte:head>

<main>
	<p class="overline">Every Ball Ever</p>

	{#if selectedPid}
		<nav class="card-nav">
			<button class="link-btn" onclick={newSearch}>Search another player</button>
			<a class="field-link" href="{base}/">Back to the field</a>
		</nav>

		{#if cardLoading}
			<p class="status">Loading their card...</p>
		{:else if cardError || !card}
			<div class="status-block">
				<h1>No card for that link</h1>
				<p>That player id is not in the registry. Try a search instead.</p>
				<button class="link-btn" onclick={newSearch}>Search players</button>
			</div>
		{:else}
			{#key card.pid}
				<PlayerCard {card} />
			{/key}
		{/if}
	{:else}
		<h1>Type a name</h1>
		<p class="lede">
			Every player who ever batted or bowled in the IPL or WPL has a card. See how fast they scored
			against their era, where they walked in, and their biggest duels.
		</p>

		<form class="search" onsubmit={onSubmit} role="search">
			<label class="field-label" for="player-search">Search players</label>
			<input
				id="player-search"
				bind:this={searchInput}
				bind:value={query}
				type="search"
				inputmode="search"
				autocomplete="off"
				placeholder="Kohli, Bumrah, Shafali..."
			/>
		</form>

		{#if indexError}
			<p class="status">Could not load the player list. Please refresh.</p>
		{:else if !index}
			<p class="status">Loading players...</p>
		{:else if query.trim()}
			{#if results.length}
				<ul class="results">
					{#each results as hit (hit.pid)}
						<li>
							<button class="result" onclick={() => select(hit.pid)}>
								<span class="result-name">{hit.name}</span>
								<span class="result-meta">
									{roleWord(hit.role)} · {hit.leagues.map(leagueName).join(', ')} · {seasonsLabel(
										hit.seasons[0],
										hit.seasons[hit.seasons.length - 1]
									)}{hit.matchedAlias ? ` · matched: ${hit.matchedAlias}` : ''}
								</span>
							</button>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="status">No player matches that. Try fewer letters.</p>
			{/if}
		{:else}
			<div class="empty">
				<p class="empty-label">Start with one of these</p>
				<div class="chips">
					{#each suggested as s (s.pid)}
						<button class="chip-btn" onclick={() => select(s.pid)}>{s.name}</button>
					{/each}
					<button class="chip-btn surprise" onclick={surprise} disabled={!index}>
						Surprise me
					</button>
				</div>
			</div>
		{/if}

		<p class="back"><a href="{base}/">Back to the field</a></p>
	{/if}
</main>

<style>
	main {
		max-width: 46rem;
		margin: 0 auto;
		padding: calc(2.5rem + env(safe-area-inset-top)) calc(1.3rem + env(safe-area-inset-right))
			calc(4rem + env(safe-area-inset-bottom)) calc(1.3rem + env(safe-area-inset-left));
	}
	.overline {
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.28em;
		text-transform: uppercase;
		color: var(--gold);
		margin: 0 0 0.6rem;
	}
	h1 {
		margin: 0 0 0.7rem;
		font-size: clamp(1.7rem, 4.5vw, 2.4rem);
		line-height: 1.2;
	}
	.lede {
		color: var(--ink-dim);
		font-size: 1.02rem;
		line-height: 1.55;
		margin: 0 0 1.6rem;
	}
	.card-nav {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1.4rem;
	}
	.link-btn {
		font: inherit;
		font-weight: 600;
		min-height: 44px;
		padding: 0.4rem 0;
		background: none;
		border: none;
		color: var(--teal);
		cursor: pointer;
	}
	.link-btn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
	.field-link {
		color: var(--ink-dim);
		font-size: 0.9rem;
	}
	.field-link:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
	.search {
		margin: 0 0 1.2rem;
	}
	.field-label {
		display: block;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--ink-dim);
		margin-bottom: 0.4rem;
	}
	input[type='search'] {
		width: 100%;
		min-height: 52px;
		padding: 0.7rem 1rem;
		font: inherit;
		font-size: 1.1rem;
		color: var(--ink);
		background: rgba(232, 236, 245, 0.04);
		border: 1px solid rgba(232, 236, 245, 0.18);
		border-radius: 12px;
	}
	input[type='search']:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 1px;
		border-color: var(--teal);
	}
	.results {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	.result {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		width: 100%;
		min-height: 44px;
		padding: 0.55rem 0.8rem;
		text-align: left;
		background: rgba(232, 236, 245, 0.03);
		border: 1px solid rgba(232, 236, 245, 0.07);
		border-radius: 10px;
		color: var(--ink);
		font: inherit;
		cursor: pointer;
	}
	.result:hover,
	.result:focus-visible {
		background: rgba(232, 236, 245, 0.08);
		outline: none;
	}
	.result:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 1px;
	}
	.result-name {
		font-size: 1rem;
		font-weight: 650;
	}
	.result-meta {
		font-size: 0.8rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}
	.empty {
		margin-top: 0.4rem;
	}
	.empty-label {
		font-size: 0.75rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-dim);
		margin: 0 0 0.6rem;
	}
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
	.chip-btn {
		font: inherit;
		font-weight: 600;
		min-height: 44px;
		padding: 0.5rem 1rem;
		background: rgba(232, 236, 245, 0.05);
		border: 1px solid rgba(232, 236, 245, 0.16);
		border-radius: 999px;
		color: var(--ink);
		cursor: pointer;
	}
	.chip-btn:hover,
	.chip-btn:focus-visible {
		background: rgba(232, 236, 245, 0.1);
		outline: none;
	}
	.chip-btn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
	.chip-btn.surprise {
		color: var(--gold);
		border-color: rgba(232, 163, 61, 0.4);
	}
	.chip-btn:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.status {
		color: var(--ink-dim);
		font-size: 0.95rem;
	}
	.status-block h1 {
		margin-bottom: 0.5rem;
	}
	.status-block p {
		color: var(--ink-dim);
		margin: 0 0 1rem;
	}
	.back {
		margin-top: 2.5rem;
	}
	.back a {
		display: inline-block;
		padding: 0.6rem 0;
		min-height: 44px;
		color: var(--teal);
	}
	.back a:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
</style>
