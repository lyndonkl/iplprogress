<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen, pickedTeam } from '$lib/state';
	import { requestTeamChange } from '$lib/scenes/picker';
	import { loadCh6Data, payoffVariantFor, type Ch6Data, type PayoffVariant } from './data';
	import Starfield from './Starfield.svelte';

	/**
	 * C6-9 — Team payoff: your two dialects. IPL pickers meet their shared-city WPL
	 * SISTER (MI→MI-W, RCB→RCB-W, DC→DC-W, GT→Gujarat Giants); WPL pickers get the
	 * inverted card — home turf here — plus the IPL season-star nearest their team's
	 * style. Sisterless sides (six IPL franchises, UP Warriorz) get the designed
	 * no-sister state (authored copy, never a blank card — the empty state is itself
	 * the point). Neutral pickers get the five shared grounds + the league-wide
	 * style twin. All 16 variants come from ch6.json payoff.variants (snapshot-
	 * tested in the pipeline; card == artifact — never hand-authored per team).
	 *
	 * The constellation holds dimmed behind the card; for a WPL picker the nearest
	 * IPL style-star is ringed on the map (the payoff's tie back to the hero).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const shown = $derived(reduced || progress >= 0.3);

	let ch6 = $state<Ch6Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh6Data().then((d) => {
			if (alive) ch6 = d;
		});
		return () => {
			alive = false;
		};
	});

	const resolved = $derived(
		ch6
			? payoffVariantFor(
					ch6,
					$pickedTeam ? { league: $pickedTeam.league, team: $pickedTeam.team } : null
				)
			: null
	);
	const v = $derived<PayoffVariant | null>(resolved?.variant ?? null);
	const isWpl = $derived(v?.league === 'wpl');
	const isIpl = $derived(v?.league === 'ipl');
	const isNeutral = $derived(v?.league === 'neutral');
	const nearestSeason = $derived(v?.nearest_ipl_star_by_style?.ipl_season ?? null);
	const nearestGi = $derived(v?.nearest_ipl_star_by_style?.gi ?? null);

	/* shared-ground city list (both variants carry the five) */
	const grounds = $derived(v?.shared_grounds ?? ch6?.payoff.shared_grounds.map((g) => ({ city: g.city, venue: g.venue })) ?? []);

	/* the league-wide WPL style twin (all WPL seasons play nearest the men's 2008),
	   bound from the constellation read — powers the sisterless-IPL "the season your
	   rivals play like" line without a fabricated per-team read */
	const wplStyleSeason = $derived(
		ch6?.constellation.two_truths.find((t) => t.wpl_season === 2026)?.outcome_mix_twin.ipl_season ??
			2008
	);

	/* an IPL picker WITH a sister: find that sister's WPL variant to light its
	   nearest men's season-star, mirroring the WPL-picker map treatment */
	const sisterVariant = $derived(
		isIpl && v?.sister
			? (ch6?.payoff.variants.find((x) => x.league === 'wpl' && x.team === v!.sister!.team) ?? null)
			: null
	);
	const sisterNearestGi = $derived(sisterVariant?.nearest_ipl_star_by_style?.gi ?? null);
	const sisterNearestSeason = $derived(sisterVariant?.nearest_ipl_star_by_style?.ipl_season ?? null);

	/* light the map for BOTH a WPL picker (home) and an IPL picker with a sister:
	   ring the WPL cluster + the nearest men's season-star, and draw the threads */
	const highlightGis = $derived.by<number[]>(() => {
		if (!shown) return [];
		if (isWpl && nearestGi !== null) return [19, 20, 21, 22, nearestGi];
		if (isIpl && v?.sister)
			return sisterNearestGi !== null ? [19, 20, 21, 22, sisterNearestGi] : [19, 20, 21, 22];
		return [];
	});
	const labelGis = $derived(highlightGis);
	const showThreads = $derived(isWpl || (isIpl && !!v?.sister));

	let returnAnchor = $state<HTMLElement | null>(null);
</script>

<div class="return-anchor" bind:this={returnAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	<Starfield
		{field}
		{reduced}
		{progress}
		on={shown}
		threadPhase="all"
		showWorm={true}
		{showThreads}
		{labelGis}
		{highlightGis}
		faint={true}
		legend={true}
		footnoteId="ch6-payoff"
	/>

	<div class="card-slot" class:shown>
		{#if v}
			<div class="scene-card interactive card">
				{#if isIpl && v.sister}
					<p class="overline">your club, in two leagues</p>
					<h2>{v.team} has a sister</h2>
					<p class="body">
						The men play here in the IPL. In the WPL, <strong>{v.sister.team}</strong> ({v.sister.short})
						carry the same city and the same colours. Two teams, two dialects, one badge.
					</p>
					{#if v.shared_city}
						<p class="ground">Your city, {v.shared_city}, sends a side to both.</p>
					{/if}
					{#if sisterNearestSeason !== null}
						<p class="ground">
							By the way it plays, {v.sister.short}'s cricket sits closest to the men's season of
							<strong>IPL {sisterNearestSeason}.</strong> Its stars are ringed on the map here.
						</p>
					{/if}
				{:else if isIpl && !v.sister}
					<p class="overline">your club, in two leagues</p>
					<h2>{v.team}</h2>
					<p class="body">{v.empty_copy}</p>
					<p class="ground">
						Wherever a WPL side plays, its cricket sits closest to the men's game of
						<strong>IPL {wplStyleSeason}.</strong> A city with no women's team yet would be walking
						into the tightest league in the game.
					</p>
				{:else if isWpl}
					<p class="overline">home turf</p>
					<h2>{v.team} ({v.short})</h2>
					<p class="body">
						In this chapter your league is the home side and the IPL is the visitor.
						{#if v.sister}
							Across town, <strong>{v.sister.team}</strong> ({v.sister.short}) fly the same flag in
							the men's game.
						{:else if v.empty_copy}
							{v.empty_copy}
						{/if}
					</p>
					{#if nearestSeason !== null}
						<p class="ground">
							By style, your league's nearest men's season-star is <strong>IPL {nearestSeason}.</strong>
							It is ringed on the map here.
						</p>
					{/if}
				{:else if isNeutral}
					<p class="overline">the whole map is yours</p>
					<h2>Two dialects, side by side</h2>
					<p class="body">
						No team picked, so here is the common ground. Every WPL season's style twin is the
						early IPL, and five stadiums host both leagues.
					</p>
				{/if}

				{#if grounds.length && !(isIpl && !v.sister)}
					<div class="grounds">
						<span class="g-head">grounds that host both</span>
						<span class="g-list">{grounds.map((g) => g.city).join(' · ')}</span>
					</div>
				{/if}

				<div class="actions">
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch6-payoff')}
						aria-label="How the sister pairing is built">ⓘ</button
					>
					<button class="change" onclick={() => requestTeamChange(returnAnchor)}>
						{isNeutral ? 'Pick a team to make this yours' : 'Not your team? Change it'}
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.return-anchor {
		position: absolute;
		top: 40%;
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
		overflow-y: auto;
		transition: opacity 0.25s ease;
	}

	.card-slot.shown {
		opacity: 1;
	}

	.card {
		max-width: min(30rem, 92vw);
	}

	.card h2 {
		font-size: clamp(1.15rem, 3vw, 1.6rem);
	}

	.body {
		margin-top: 0.55rem;
		font-size: clamp(0.95rem, 2.2vw, 1.1rem);
		line-height: 1.5;
	}

	.ground {
		margin-top: 0.6rem;
		font-size: 0.9rem;
		line-height: 1.5;
		color: var(--ink);
	}

	.grounds {
		margin-top: 0.8rem;
		border-top: 1px solid rgba(151, 161, 184, 0.2);
		padding-top: 0.6rem;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.g-head {
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.g-list {
		font-size: 0.85rem;
		color: var(--ink);
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		margin-top: 0.9rem;
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

	.change {
		min-height: 44px;
		padding: 0.4rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.85rem;
		font-weight: 600;
		cursor: pointer;
	}

	.dagger:focus-visible,
	.change:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.pin {
			place-items: start center;
			padding-top: 9vh;
		}
	}
</style>
