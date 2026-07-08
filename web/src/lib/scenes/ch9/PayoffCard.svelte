<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen, pickedTeam } from '$lib/state';
	import { requestTeamChange } from '$lib/scenes/picker';
	import DuelField from './DuelField.svelte';
	import DuelStrands from './DuelStrands.svelte';
	import ReplayStrip from './ReplayStrip.svelte';
	import { loadCh9Data, payoffVariantFor, type Ch9Data, type PayoffVariant } from './data';

	/**
	 * C9-8, the per-franchise payoff ("your team through the churn"). One of 16
	 * variants (10 IPL + 5 WPL + neutral), branched on ebe.team.v1. Its longest-
	 * running rivalry (with a ball-by-ball replay), how its squad got torn up at the
	 * last reset, and its most loyal one-club player. Every card is a "through the
	 * churn" card, never a deficit card, and the WPL card is the forming-fast beat
	 * made personal, never "behind". Every number is per-variant and data-bound to
	 * ch9.json (the rows are authored in the pipeline, so card == artifact). The
	 * dimmed web idles behind with the reader's own rivalry strand highlighted.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const shown = $derived(reduced || progress >= 0.3);

	let ch9 = $state<Ch9Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh9Data().then((d) => {
			if (alive) ch9 = d;
		});
		return () => {
			alive = false;
		};
	});

	const resolved = $derived(
		ch9
			? payoffVariantFor(
					ch9,
					$pickedTeam ? { league: $pickedTeam.league, team: $pickedTeam.team } : null
				)
			: null
	);
	const v = $derived<PayoffVariant | null>(resolved?.variant ?? null);
	const duelId = $derived(v ? v.rivalry.duel_id : null);

	let replayOpen = $state(false);
	const showReplay = $derived((replayOpen || reduced) && v != null && ch9 != null);
	const replayDuel = $derived(
		ch9 && duelId != null ? (ch9.duel_web.duels[duelId] ?? null) : null
	);

	let returnAnchor = $state<HTMLElement | null>(null);
</script>

<div class="return-anchor" bind:this={returnAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	<DuelField {field} faint={true} footnoteId="ch9-payoff" />
	{#if duelId != null}
		<DuelStrands
			{field}
			{reduced}
			{progress}
			{active}
			topN={40}
			focusIds={[duelId]}
			highlightId={duelId}
			showHubLabels={false}
		/>
	{/if}

	<div class="card-slot" class:shown>
		{#if v}
			<div class="scene-card interactive card">
				<p class="overline">{v.league === 'wpl' ? 'a young league' : v.league === 'neutral' ? 'the whole league' : 'your team through the churn'}</p>
				<h2>{v.headline}</h2>

				<p class="row">
					{v.row1}
					{#if replayDuel}
						<button class="replay-btn" onclick={() => (replayOpen = !replayOpen)}>
							{replayOpen ? 'hide the replay' : 'tap to replay it ball by ball'}
						</button>
					{/if}
				</p>
				<p class="row">{v.row2}</p>
				<p class="row">{v.row3}</p>

				{#if showReplay && replayDuel}
					<div class="replay-inline">
						<ReplayStrip
							replay={ch9?.replays[replayDuel.id] ?? null}
							summary={{
								bat: replayDuel.bat,
								bowl: replayDuel.bowl,
								balls: replayDuel.balls,
								runs: replayDuel.runs,
								dis: replayDuel.dis,
								span: replayDuel.span
							}}
							onClose={reduced ? undefined : () => (replayOpen = false)}
						/>
					</div>
				{/if}

				<div class="actions">
					<button class="dagger" onclick={() => footnotesOpen.set('ch9-payoff')} aria-label="How the card is built">ⓘ</button>
					<button class="change" onclick={() => requestTeamChange(returnAnchor)}>
						{v.league === 'neutral' ? 'Pick a team to make this yours' : 'Not your team? Change it'}
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
		max-width: min(34rem, 92vw);
	}

	.card h2 {
		font-size: clamp(1.15rem, 3vw, 1.6rem);
	}

	.row {
		margin-top: 0.6rem;
		font-size: clamp(0.95rem, 2.2vw, 1.08rem);
		line-height: 1.5;
	}

	.replay-btn {
		display: block;
		margin-top: 0.3rem;
		min-height: 40px;
		padding: 0.2rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.82rem;
		font-weight: 600;
		text-align: left;
		cursor: pointer;
	}

	.replay-inline {
		margin-top: 0.7rem;
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
	.change:focus-visible,
	.replay-btn:focus-visible {
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
