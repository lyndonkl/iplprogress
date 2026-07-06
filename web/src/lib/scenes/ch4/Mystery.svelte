<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { loadCh4Data, pct, type Ch4Data } from './data';

	/**
	 * C4-5 — The planted 2023 mystery (an AUTHORED beat, on screen). The chapter shows
	 * the 2023 cliff in full drama and then VISIBLY REFUSES to explain it. The hold
	 * line is rendered verbatim from ch4.json (`mystery.hold`) — "Something snapped in
	 * 2023. Hold that thought. The answer is three chapters away." No em dash; no
	 * cause given here (Ch 7 the suspect, Ch 10 the verdict). Skyline dimmed one stop
	 * behind; loop stopped. A small P(200)-by-season cliff sits above the hold so the
	 * refusal lands on a picture the reader can already read.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	const shown = $derived(reduced || progress >= 0.12);
	const step = $derived(reduced ? 2 : progress < 0.5 ? 1 : 2);

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

	const cliff = $derived(ch4 ? ch4.exceedance.cliff : null);
	/* the little cliff sparkline: P(200) per season 2018 → 2026 (the flat run + the jump) */
	const CLIFF_SEASONS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];
	const bars = $derived.by(() => {
		const d = ch4;
		if (!d) return [];
		return CLIFF_SEASONS.map((y) => ({
			season: y,
			p: d.exceedance.by_season.ipl[String(y)]?.exceedance_pct['200'] ?? 0
		}));
	});
	const maxP = $derived(bars.reduce((m, b) => Math.max(m, b.p), 1));
</script>

<div class="pin" class:active>
	<div class="card-slot" class:shown>
		<div class="mystery">
			{#if cliff}
				<!-- the cliff, in full: P(200) per season, the flat run then the 2023 jump -->
				<figure class="cliff">
					<div class="bars">
						{#each bars as b (b.season)}
							<div class="col" class:cliffed={b.season >= 2023}>
								<div class="bar" style="height:{(b.p / maxP) * 100}%"></div>
								<span class="yr">{String(b.season).slice(2)}</span>
							</div>
						{/each}
					</div>
					<figcaption>
						First innings passing 200, by season. {pct(cliff.before.p200)}% in {cliff.before.season},
						then <strong>{pct(cliff.after.p200)}% in {cliff.after.season}.</strong>
					</figcaption>
				</figure>
			{/if}

			{#if step === 1}
				<p class="lead">
					Fifteen years almost flat. Then, in one off-season, <strong>a cliff.</strong> The number
					doubled and stayed doubled.
				</p>
			{:else}
				<p class="hold">{ch4 ? ch4.mystery.hold : 'Something snapped in 2023. Hold that thought. The answer is three chapters away.'}</p>
				<p class="sub">
					We could hand you a neat reason right now. Three of them, actually. We are not going to. Not
					yet.
					<button class="dagger" onclick={() => footnotesOpen.set('measured-jump')} aria-label="How we know 2023 really bent">ⓘ</button>
				</p>
			{/if}
		</div>
	</div>
</div>

<style>
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
		width: min(40rem, 92vw);
	}

	.card-slot.shown {
		opacity: 1;
	}

	.mystery {
		text-align: center;
	}

	.cliff {
		margin: 0 0 1.4rem;
	}

	.bars {
		display: flex;
		align-items: flex-end;
		justify-content: center;
		gap: 4px;
		height: 96px;
	}

	.col {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: flex-end;
		height: 100%;
		width: 22px;
	}

	.bar {
		width: 16px;
		border-radius: 3px 3px 0 0;
		background: #56607a;
	}

	.col.cliffed .bar {
		background: #5b8cff;
		box-shadow: 0 0 8px rgba(91, 140, 255, 0.5);
	}

	.yr {
		margin-top: 4px;
		font-size: 9px;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.col.cliffed .yr {
		color: #9dbcff;
	}

	figcaption {
		margin-top: 0.6rem;
		font-size: 0.82rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.lead {
		margin: 0;
		font-size: clamp(1.1rem, 2.6vw, 1.4rem);
		line-height: 1.45;
		color: var(--ink);
	}

	.hold {
		margin: 0;
		font-size: clamp(1.4rem, 3.6vw, 2.1rem);
		line-height: 1.3;
		font-weight: 700;
		color: var(--ink);
	}

	.sub {
		margin: 0.8rem 0 0;
		font-size: 0.95rem;
		color: var(--ink-dim);
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
</style>
