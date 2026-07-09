<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen, pickedTeam } from '$lib/state';
	import { requestTeamChange } from '$lib/scenes/picker';
	import RibbonField from './RibbonField.svelte';
	import { loadCh10Data, payoffVariantFor, fmt1, type Ch10Data, type PayoffVariant } from './data';

	/**
	 * C10-8, the per-franchise payoff ("your adapters"). One of 16 variants (10 IPL +
	 * 5 WPL + neutral), branched on ebe.team.v1. Which of its icons crossed the 2023
	 * fault RISING (the adaptation badge), its legend teleported through the eras (the
	 * honest re-quote, never the naive ghost, as the headline number), and where it
	 * sits on the modern climb (as a position, never a ranking claim). Every card is
	 * an "adapters" card, never a deficit card; the WPL card is the forward-clock beat
	 * made personal, never "behind". Every number is per-variant and data-bound to
	 * ch10.json (the rows are authored in the pipeline, so card == artifact).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const shown = $derived(reduced || progress >= 0.3);

	let ch10 = $state<Ch10Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh10Data().then((d) => {
			if (alive) ch10 = d;
		});
		return () => {
			alive = false;
		};
	});

	const resolved = $derived(
		ch10
			? payoffVariantFor(ch10, $pickedTeam ? { league: $pickedTeam.league, team: $pickedTeam.team } : null)
			: null
	);
	const v = $derived<PayoffVariant | null>(resolved?.variant ?? null);

	let teleOpen = $state(false);
	const legend = $derived(v?.legend ?? null);

	let returnAnchor = $state<HTMLElement | null>(null);
</script>

<div class="return-anchor" bind:this={returnAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	<RibbonField {field} {progress} faint={true} footnoteId="ch10-payoff" />

	<div class="card-slot" class:shown>
		{#if v}
			<div class="scene-card interactive card">
				<p class="overline">
					{v.league === 'wpl' ? 'a young league' : v.league === 'neutral' ? 'the whole league' : 'your adapters'}
				</p>
				<h2>{v.headline}</h2>

				<p class="row">{v.row1}</p>
				<p class="row">
					{v.row2}
					{#if legend}
						<button class="tele-btn" onclick={() => (teleOpen = !teleOpen)}>
							{teleOpen ? 'hide the Teleporter' : 'tap to open the Teleporter on them'}
						</button>
					{/if}
				</p>

				{#if legend && (teleOpen || reduced)}
					<div class="tele-mini">
						<span class="tm-name">{legend.name}, {legend.season}, into 2026</span>
						<div class="tm-row">
							<span class="tm-honest">honest re-quote <strong>{fmt1(legend.honest_2026)}</strong></span>
							<span class="tm-ghost">naive ghost {fmt1(legend.naive_2026)}</span>
						</div>
					</div>
				{/if}

				<p class="row">{v.row3}</p>

				<div class="actions">
					<button class="dagger" onclick={() => footnotesOpen.set('ch10-payoff')} aria-label="How the card is built">ⓘ</button>
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

	.tele-btn {
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

	.tele-mini {
		margin-top: 0.6rem;
		padding: 0.6rem 0.8rem;
		border-radius: 10px;
		background: rgba(10, 14, 24, 0.8);
		border: 1px solid rgba(46, 196, 182, 0.3);
	}

	.tm-name {
		font-size: 0.7rem;
		color: var(--ink-dim);
	}

	.tm-row {
		display: flex;
		gap: 1rem;
		margin-top: 0.3rem;
		flex-wrap: wrap;
	}

	.tm-honest {
		font-size: 0.85rem;
		color: var(--teal);
	}

	.tm-honest strong {
		font-size: 1rem;
	}

	.tm-ghost {
		font-size: 0.85rem;
		color: var(--gold, #e8b84b);
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
	.tele-btn:focus-visible {
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
