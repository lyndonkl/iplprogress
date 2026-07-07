<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh5Data, setRailIndices, RAIL_SLOTS, RAIL_Y, win100, type Ch5Data } from './data';
	import Worm from './Worm.svelte';

	/**
	 * C5-2 — The last over lifts out (orient the rail + the worm BEFORE anything
	 * moves). The six deliveries of the 2019 final's last over fly from the dimmed
	 * field to the rail slots (the §20 overrail — the lift rides this scene's
	 * entry morph, so the nav's set-piece dimming tracks it), six DOM ball chips
	 * fade in dormant at the same viewport fractions, and the worm's empty axis
	 * draws underneath with its start anchor glossed. Everything on this card is
	 * bound to scenes/ch5.json (the match card, the entering state, the start
	 * anchor) — never hand-typed. One orientation unit with C5-3 (§0.2 rule 2).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.34 ? 1 : progress < 0.64 ? 2 : 3);
	const BOUNDS = [0, 0.34, 0.64, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch5 = $state<Ch5Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh5Data().then((d) => {
			if (!alive) return;
			ch5 = d;
			// cache the six PIPELINE-EMITTED field point indices (the SceneDef
			// dynamicState reads the cache; ch4's tideParLevels pattern). They
			// arrive with the same fetch every caption here binds to, so the
			// step-2 "just lifted out" line and the GL lift resolve together.
			setRailIndices(d);
		});
		return () => {
			alive = false;
		};
	});

	const m = $derived(ch5?.scrub.match ?? null);
	const entering = $derived(ch5?.scrub.entering ?? null);
	const defendingTotal = $derived(ch5 ? ch5.scrub.target - 1 : null);
	const startWp = $derived(ch5 ? ch5.scrub.balls[0].wp_before : null);

	/** chips fade in once the lift is mostly home (or instantly under reduced motion) */
	const chipsOn = $derived(reduced || progress >= 0.3);
	const wormOn = $derived(reduced || step >= 3);
</script>

<div class="pin" class:active>
	{#if m && entering && defendingTotal !== null}
		<!-- the match card, top-center (bound to the artifact) -->
		<div class="match-card" class:shown={reduced || progress >= 0.06}>
			<span class="stage">{m.league.toUpperCase()} {m.stage}, {m.season}</span>
			<span class="line"
				>{m.teams[0]} {defendingTotal} · {m.teams[1]} {entering.score} for {entering.wickets_down} ·
				one over left</span
			>
		</div>

		<!-- the six dormant ball chips at the rail slots -->
		{#if chipsOn && ch5}
			<div class="chips">
				{#each ch5.scrub.balls as b, i (b.ball)}
					<div
						class="chip dormant"
						style="left: {RAIL_SLOTS[i][0] * 100}%; top: {RAIL_Y * 100}%;"
					>
						<span class="ball-no">{b.label}</span>
					</div>
				{/each}
			</div>
		{/if}

		{#if wormOn && ch5}
			<!-- the worm's empty axis + the pulsing start-anchor stub -->
			<Worm balls={ch5.scrub.balls} reveal={0} />
		{/if}
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					Hyderabad, May 2019. The final. Mumbai have put up {defendingTotal ?? 149}, and Chennai
					have clawed to within {entering?.needed ?? 9} of it. One over left, Malinga bowling. Six
					balls to decide a title.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Those six balls have just lifted out of the field. Every other ball ever bowled dims
					behind them. We are going to walk them one at a time.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					The line underneath is <strong>the worm.</strong> It draws as each ball plays, and its
					height shows how often the chasing side wins from that exact spot, out of a hundred.
					Chennai start the over at about {startWp !== null ? win100(startWp) : 72} in 100.
					Clear favourites.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-over')}
						aria-label="How the worm is read">ⓘ</button
					>
				</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
	}

	.pin.active {
		visibility: visible;
	}

	.match-card {
		position: absolute;
		top: 4.5vh;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.15rem;
		padding: 0.45rem 0.9rem;
		border-radius: 10px;
		background: rgba(10, 14, 24, 0.72);
		border: 1px solid rgba(151, 161, 184, 0.25);
		opacity: 0;
		text-align: center;
		max-width: 92vw;
	}

	.match-card.shown {
		opacity: 1;
	}

	.stage {
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.line {
		font-size: clamp(0.78rem, 1.9vw, 0.95rem);
		font-weight: 600;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.chips {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.chip {
		position: absolute;
		transform: translate(-50%, -50%);
		display: grid;
		place-items: center;
	}

	.chip.dormant .ball-no {
		display: inline-block;
		margin-top: 3.2rem;
		font-size: 0.72rem;
		font-weight: 700;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 12vh;
		max-width: min(24rem, 38vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	/* no invisible ⓘ tap target during the mobile clear gap */
	.caption-slot.gap .dagger {
		pointer-events: none;
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

	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}

		.match-card {
			top: max(3vh, calc(env(safe-area-inset-top) + 52px));
		}

		.chip.dormant .ball-no {
			margin-top: 2.2rem;
			font-size: 0.62rem;
		}
	}
</style>
