<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen, pickedTeam } from '$lib/state';
	import { requestTeamChange } from '$lib/scenes/picker';
	import RiverPlane from './RiverPlane.svelte';
	import {
		loadCh7Data,
		payoffVariantFor,
		leagueBreakPct,
		pct0,
		type Ch7Data,
		type PayoffVariant
	} from './data';

	/**
	 * C7-7 — Team payoff: your team's playbook. IPL pickers get their franchise's
	 * impact-player habits: batting vs bowling reinforcement, most-used impact
	 * player, break-vs-mid timing, and the win rate behind each pattern. WPL pickers
	 * get the control-arm card — their league is the reason the rule is readable at
	 * all (empowering, never "behind", per the house framing). Neutral pickers get
	 * the league-wide diff-in-diff. All 16 variants come from ch7.json payoff.variants
	 * (card == artifact — never hand-authored per team). The rivers idle faintly
	 * behind the card, tying the payoff back to the hero.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const shown = $derived(reduced || progress >= 0.3);

	let ch7 = $state<Ch7Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh7Data().then((d) => {
			if (alive) ch7 = d;
		});
		return () => {
			alive = false;
		};
	});

	const resolved = $derived(
		ch7
			? payoffVariantFor(
					ch7,
					$pickedTeam ? { league: $pickedTeam.league, team: $pickedTeam.team } : null
				)
			: null
	);
	const v = $derived<PayoffVariant | null>(resolved?.variant ?? null);
	const isIpl = $derived(v?.league === 'ipl');
	const isWpl = $derived(v?.league === 'wpl');
	const isNeutral = $derived(v?.league === 'neutral');
	const leaned = $derived(v?.favorite_pattern === 'bat' ? 'batting' : 'bowling');

	/* timing vs the league (storyboard C7-8, audit consider #14): compare this team's
	   break share to the league-wide pooled break share, both artifact-derived. */
	const leagueBreak = $derived(ch7 ? leagueBreakPct(ch7.playbook) : 0);
	const teamBreak = $derived(
		v?.timing && v.total_subs ? (100 * v.timing.at_break) / v.total_subs : 0
	);
	const breakLean = $derived(teamBreak >= leagueBreak ? 'more' : 'less');

	let returnAnchor = $state<HTMLElement | null>(null);
</script>

<div class="return-anchor" bind:this={returnAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	<RiverPlane {field} {reduced} {progress} on={shown} faint={true} legend={false} footnoteId="ch7-payoff" />

	<div class="card-slot" class:shown>
		{#if v}
			<div class="scene-card interactive card">
				{#if isIpl}
					<p class="overline">your team's twelfth man</p>
					<h2>{v.team}</h2>
					<p class="body">
						{v.team} leaned <strong>{leaned}</strong>: {v.bat_subs} batting reinforcements,
						{v.bowl_subs} bowling. Their most-used impact player was
						<strong>{v.most_used_player?.name}</strong> ({v.most_used_player?.count} times).
					</p>
					{#if v.timing && v.total_subs}
						<p class="ground">
							They play the card {breakLean} at the break than the league: {pct0(teamBreak)}% of
							their subs at the innings break, against {pct0(leagueBreak)}% across the IPL.
						</p>
					{/if}
					{#if v.win_rate}
						<div class="stats">
							<div class="stat">
								<span class="s-num">{pct0(v.win_rate.bat)}%</span>
								<span class="s-lbl">won, batting sub</span>
							</div>
							<div class="stat">
								<span class="s-num">{pct0(v.win_rate.bowl)}%</span>
								<span class="s-lbl">won, bowling sub</span>
							</div>
						</div>
						<p class="caveat">Small sample, about 50 to 60 subs over four seasons. A tendency, not a law.</p>
					{/if}
				{:else if isWpl}
					<p class="overline">home advantage</p>
					<h2>{v.team} ({v.short})</h2>
					<p class="body">{v.headline}</p>
				{:else if isNeutral}
					<p class="overline">the whole league</p>
					<h2>The rule, in one number</h2>
					<p class="body">{v.headline}</p>
				{/if}

				<div class="actions">
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch7-payoff')}
						aria-label="How the playbook cards are built">ⓘ</button
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

	.stats {
		display: flex;
		gap: 1.4rem;
		margin-top: 0.9rem;
	}

	.stat {
		display: flex;
		flex-direction: column;
	}

	.s-num {
		font-size: 1.5rem;
		font-weight: 800;
		color: var(--gold);
		font-variant-numeric: tabular-nums;
		line-height: 1;
	}

	.s-lbl {
		font-size: 0.68rem;
		color: var(--ink-dim);
		margin-top: 0.15rem;
	}

	.ground {
		margin-top: 0.7rem;
		font-size: 0.9rem;
		line-height: 1.5;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.caveat {
		margin-top: 0.5rem;
		font-size: 0.7rem;
		line-height: 1.4;
		color: var(--ink-dim);
		font-style: italic;
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
