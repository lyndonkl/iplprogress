<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen, pickedTeam } from '$lib/state';
	import { requestTeamChange } from '$lib/scenes/picker';
	import MatchField from './MatchField.svelte';
	import ReportCardRail from './ReportCardRail.svelte';
	import { loadCh8Data, payoffVariantFor, pct0, type Ch8Data, type PayoffVariant } from './data';

	/**
	 * C8-9, the per-franchise payoff ("your captains' report card"). One of 16
	 * variants (10 IPL + 5 WPL + neutral), branched on ebe.team.v1. How often its
	 * captains chose to field at home, whether that home chase actually won, and where
	 * it ranks on review discipline. Every card is a REPORT card, never a deficit
	 * card, and the WPL card is the analytics-native beat made personal, never
	 * "behind". The on-card GUARD line keeps the two home facts from reading as cause
	 * and effect (C8-3 spent five steps separating the choice from the result). Numbers
	 * are per-variant and data-bound to ch8.json. The dimmed dots idle behind, with the
	 * reader's own matches lit.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const shown = $derived(reduced || progress >= 0.3);

	let ch8 = $state<Ch8Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh8Data().then((d) => {
			if (alive) ch8 = d;
		});
		return () => {
			alive = false;
		};
	});

	const resolved = $derived(
		ch8
			? payoffVariantFor(
					ch8,
					$pickedTeam ? { league: $pickedTeam.league, team: $pickedTeam.team } : null
				)
			: null
	);
	const v = $derived<PayoffVariant | null>(resolved?.variant ?? null);
	const isIpl = $derived(v?.league === 'ipl');
	const isWpl = $derived(v?.league === 'wpl');
	const isNeutral = $derived(v?.league === 'neutral');

	let returnAnchor = $state<HTMLElement | null>(null);
</script>

<div class="return-anchor" bind:this={returnAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	<MatchField {field} {reduced} {progress} faint={true} legend={false} footnoteId="ch8-payoff" />
	<ReportCardRail report={ch8?.report_card ?? null} stamped={5} />

	<div class="card-slot" class:shown>
		{#if v}
			<div class="scene-card interactive card">
				{#if isIpl}
					<p class="overline">your captains' report card</p>
					<h2>{v.team}</h2>
					{#if v.field_first_at_home}
						<p class="row">
							At home, your captains chose to field first
							<strong>{pct0(v.field_first_at_home.pct)} in 100</strong>
							<span class="dim">({v.field_first_at_home.n} of {v.field_first_at_home.d} home tosses).</span>
						</p>
					{/if}
					{#if v.chase_win_at_home}
						<p class="row">And chasing at home won <strong>{pct0(v.chase_win_at_home.pct)} in 100.</strong></p>
					{/if}
					{#if v.guard}
						<p class="guard">{v.guard}</p>
					{/if}
					{#if v.review_rank}
						<p class="row">
							On reviews, your captains rank <strong>{v.review_rank} of {v.review_of}.</strong>
							{v.flavor ?? ''}
						</p>
					{/if}
				{:else if isWpl}
					<p class="overline">born into the analytics age</p>
					<h2>{v.team} <span class="short">{v.short}</span></h2>
					{#if v.transmission}
						<p class="row">
							Your league fielded first <strong>{pct0(v.transmission.field_first_season_one)} in 100</strong>
							in year one, then nearly always in two seasons. The men's game took the better part of a
							decade.
						</p>
						<p class="row">
							Your reviews pay off at the men's rate, <strong>{pct0(v.transmission.review_upheld_pct)} in 100</strong>,
							and you deal overs faster, <strong>{pct0(v.transmission.one_over_share)} in 100.</strong>
						</p>
					{/if}
				{:else if isNeutral}
					<p class="overline">the whole league</p>
					<h2>Every captain, graded</h2>
					{#if v.league_field_first != null}
						<p class="row">
							Across the whole league, captains chose to field <strong>{pct0(v.league_field_first)} in 100</strong>,
							the chase wins <strong>{pct0(v.league_chase_win ?? 0)}</strong>, and reviews pay off
							<strong>{pct0(v.league_review_upheld ?? 0)}.</strong>
						</p>
					{/if}
					<p class="guard">These are separate facts about the league, not cause and effect. Pick a team to see its own report card.</p>
				{/if}

				<div class="actions">
					<button class="dagger" onclick={() => footnotesOpen.set('ch8-payoff')} aria-label="How the report cards are built">ⓘ</button>
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

	.short {
		font-size: 0.7rem;
		color: var(--ink-dim);
		font-weight: 600;
	}

	.row {
		margin-top: 0.6rem;
		font-size: clamp(0.95rem, 2.2vw, 1.08rem);
		line-height: 1.5;
	}

	.dim {
		color: var(--ink-dim);
		font-size: 0.82em;
	}

	.guard {
		margin-top: 0.7rem;
		font-size: 0.78rem;
		line-height: 1.45;
		color: var(--ink-dim);
		font-style: italic;
		border-left: 2px solid rgba(151, 161, 184, 0.3);
		padding-left: 0.6rem;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		margin-top: 1rem;
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
