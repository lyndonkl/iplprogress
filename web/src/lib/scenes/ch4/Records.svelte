<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh4Data, int, TIDE_SEASONS, type Ch4Data, type RecordStep } from './data';

	/**
	 * C4-6 — The records ticker (HERO close: Record Half-Life). The standing highest
	 * first innings, replayed 2008 → 2026 on a board that SHATTERS each time it falls.
	 * The Record Half-Life close: the highest-total record, RCB's 263 from 2013, stood
	 * 3,991 days, then fell twice in 19 days in 2024. The stationary-environment null
	 * (records get harder to break on their own, so falling FASTER is the tell) lives
	 * one click deep. Skyline dimmed one stop behind. Every number from ch4.json.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	/* the scrub pointer over the 19 IPL seasons */
	const seasonIdx = $derived.by(() => {
		if (reduced) return TIDE_SEASONS.length - 1;
		if (progress < 0.18) return 0;
		if (progress >= 0.78) return TIDE_SEASONS.length - 1;
		const t = (progress - 0.18) / (0.78 - 0.18);
		return Math.min(TIDE_SEASONS.length - 1, Math.round(t * (TIDE_SEASONS.length - 1)));
	});
	const season = $derived(TIDE_SEASONS[seasonIdx]);
	/* step tracks scroll progress even under reduced motion (the board holds its
	   settled 2026 end state; the captions stay a full stepped sequence — CONTRACT
	   §17.3 / audit reduced-motion parity), not a single final frame. */
	const step = $derived(progress < 0.2 ? 1 : progress < 0.78 ? 2 : 3);
	const BOUNDS = [0, 0.2, 0.78, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch4 = $state<Ch4Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh4Data().then((d) => {
			if (alive) ch4 = d;
		});
		return () => {
			alive = false;
		};
	});

	const record = $derived(ch4 ? ch4.record_halflife.ticker.ipl[String(season)] ?? null : null);
	const progression = $derived<RecordStep[]>(ch4 ? ch4.record_halflife.ipl_progression : []);
	/* the hero pair, straight from the progression */
	const rcb263 = $derived(progression.find((p) => p.total === 263) ?? null);
	const srh277 = $derived(progression.find((p) => p.total === 277) ?? null);
	/* freshly broken this very season → shatter + "new record" flash */
	const fresh = $derived(record !== null && record.since_season === season);
	const maxTotal = $derived(progression.reduce((m, p) => Math.max(m, p.total), 1));
</script>

<div class="pin" class:active>
	{#if record}
		<div class="board-slot">
			<p class="overline">Highest first innings ever · standing</p>
			{#key record.since_season}
				<div class="board" class:fresh class:still={!reduced}>
					<div class="total">{int(record.total)}</div>
					<div class="who">
						<strong>{record.team}</strong>
						<span class="since">standing since {record.since_season}</span>
					</div>
					{#if fresh && !reduced}<div class="flash">new record</div>{/if}
				</div>
			{/key}

			<!-- the fall-line: every record total, the standing one lit -->
			<div class="fallline" aria-hidden="true">
				{#each progression as p (p.date)}
					<div class="node" class:lit={p.total === record.total} class:standing={p.standing}>
						<div class="stalk" style="height:{(p.total / maxTotal) * 40 + 6}px"></div>
						<span class="node-total">{p.total}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card chip">
				<p>
					This board shows <strong>the biggest first innings ever made,</strong> as it stood on the
					day. Scrub forward and watch the record hold, then break.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card chip">
				<p>
					For eleven straight years the board never changed:
					<strong>{rcb263 !== null ? `${rcb263.team}'s ${rcb263.total}` : "RCB's 263"}, set back in 2013.</strong>
					A record that felt like it would never fall.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					{rcb263 !== null ? rcb263.team + "'s " + rcb263.total : "RCB's 263"} stood
					<strong>{rcb263 !== null ? int(rcb263.stood_days ?? 3991) : '3,991'} days.</strong>
					Then in 2024 it fell twice in {srh277 !== null ? int(srh277.stood_days ?? 19) : '19'} days.
					A record like that only gets harder to beat as scoring climbs. So a mark that stood a decade
					and then broke twice in three weeks is the sign of a game that jumped a level, not proof that
					records now fall faster.
					<button class="dagger" onclick={() => footnotesOpen.set('record-null')} aria-label="Why a faster-falling record is the tell">ⓘ</button>
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

	.board-slot {
		position: absolute;
		top: 12vh;
		left: 50%;
		transform: translateX(-50%);
		text-align: center;
		width: min(30rem, 92vw);
	}

	.overline {
		margin: 0 0 0.6rem;
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.22em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.board {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
		padding: 0.8rem 1.6rem;
		border-radius: 14px;
		background: rgba(11, 14, 20, 0.7);
		border: 1px solid rgba(91, 140, 255, 0.3);
		position: relative;
	}

	.board.still {
		animation: flip 520ms ease;
	}

	.board.fresh {
		border-color: var(--gold);
		box-shadow: 0 0 24px rgba(232, 163, 61, 0.35);
	}

	@keyframes flip {
		0% {
			transform: rotateX(-90deg);
			opacity: 0;
		}
		100% {
			transform: rotateX(0);
			opacity: 1;
		}
	}

	.total {
		font-size: clamp(3rem, 10vw, 5rem);
		font-weight: 850;
		line-height: 0.95;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.board.fresh .total {
		color: var(--gold);
	}

	.who {
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	.who strong {
		font-size: 0.95rem;
		color: var(--ink);
	}

	.since {
		font-size: 0.72rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.flash {
		position: absolute;
		top: -10px;
		right: -10px;
		padding: 2px 8px;
		border-radius: 999px;
		background: var(--gold);
		color: #0b0e14;
		font-size: 0.62rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.fallline {
		display: flex;
		align-items: flex-end;
		justify-content: center;
		gap: 5px;
		margin-top: 1.2rem;
	}

	.node {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
		opacity: 0.5;
	}

	.node.lit {
		opacity: 1;
	}

	.stalk {
		width: 3px;
		border-radius: 2px;
		background: #56607a;
	}

	.node.lit .stalk {
		background: #5b8cff;
		box-shadow: 0 0 6px rgba(91, 140, 255, 0.6);
	}

	.node.standing.lit .stalk {
		background: var(--gold);
		box-shadow: 0 0 6px rgba(232, 163, 61, 0.6);
	}

	.node-total {
		font-size: 8.5px;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.node.lit .node-total {
		color: var(--ink);
		font-weight: 700;
	}

	.caption-slot {
		position: absolute;
		left: 6vw;
		bottom: 9vh;
		max-width: min(30rem, 46vw);
		opacity: var(--reveal, 1); /* mobile "read, then watch" (CONTRACT §17); 1 on desktop / reduced */
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

	@media (prefers-reduced-motion: reduce) {
		.board.still {
			animation: none;
		}
	}

	@media (max-width: 640px) {
		.board-slot {
			top: 8vh;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(9vh, calc(env(safe-area-inset-bottom) + 56px));
		}
	}
</style>
