<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal, captionRevealActive } from '$lib/story/captionReveal.svelte';
	import {
		loadCh5Data,
		IPL_EARLY,
		IPL_RECENT,
		mag1,
		fmt2,
		type Ch5Data,
		type PriceBoardSeason
	} from './data';

	/**
	 * C5-7 — Supporting 1: the price board (the everyday outcomes, priced). Three
	 * tickers in main flow (the dot, the single, the six), one caption step each
	 * so no board element goes unspoken; the four, the two, the three, the wide
	 * and the wicket live one click deep (the full price list), and a small
	 * season slider under the board replays any ticker's season-by-season path.
	 * Prices are the pipeline's per-era linear weights derived from the locked
	 * runs-left tables (scenes/ch5.json) — the captions carry the whole point
	 * without the slider or the list. DOM only; the grid dims behind; loop stopped.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(
		progress < 0.28 ? 1 : progress < 0.46 ? 2 : progress < 0.64 ? 3 : progress < 0.82 ? 4 : 5
	);
	const BOUNDS = [0, 0.28, 0.46, 0.64, 0.82, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	/* gap-aligned on mobile (§17.6): the hot ticker ADVANCES in the previous
	   step's clear gap (the only movement this DOM board has), so the next
	   caption always fades in over its already-settled ticker; desktop and
	   reduced motion keep the step-boundary swap (byte-identical). */
	const hotStep = $derived.by(() => {
		if (reduced || !captionRevealActive()) return step;
		const u = (progress - BOUNDS[step - 1]) / (BOUNDS[step] - BOUNDS[step - 1]);
		return u >= 0.8 && step < 5 ? step + 1 : step;
	});

	let ch5 = $state<Ch5Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh5Data().then((d) => {
			if (alive) ch5 = d;
		});
		return () => {
			alive = false;
		};
	});

	const hl = $derived(ch5?.linear_weights.headline ?? null);

	/* the season slider (interactive depth): IPL seasons in board order */
	const iplSeasons = $derived.by((): PriceBoardSeason[] =>
		ch5 ? ch5.price_board.seasons.filter((s) => s.league === 'ipl') : []
	);
	let seasonIdx = $state<number | null>(null);
	const seasonRow = $derived(
		seasonIdx !== null && iplSeasons.length > 0
			? iplSeasons[Math.min(iplSeasons.length - 1, seasonIdx)]
			: null
	);

	let listOpen = $state(false);
	const FULL_ROWS = [
		{ key: 'dot', label: 'the dot' },
		{ key: 'single', label: 'the single' },
		{ key: 'two_or_three', label: 'the two or three' },
		{ key: 'four', label: 'the four' },
		{ key: 'six', label: 'the six' },
		{ key: 'wide', label: 'the wide' },
		{ key: 'wicket', label: 'the wicket' }
	] as const;

	/* under two-hundredths of a run reads as an even trade (the single's early
	   price, −0.01, must read as the caption says: dead even) */
	function dir(v: number): string {
		return v < -0.02 ? 'takes away' : v > 0.02 ? 'adds' : 'about even';
	}
	function price(v: number): string {
		return Math.abs(v) < 0.02 ? '' : fmt2(Math.abs(v));
	}

	interface Ticker {
		key: 'dot' | 'single' | 'six';
		label: string;
		early: number;
		recent: number;
		activeStep: number;
	}
	const tickers = $derived.by((): Ticker[] => {
		if (!hl) return [];
		return [
			{ key: 'dot', label: 'the dot', early: hl.dot.early, recent: hl.dot.recent, activeStep: 2 },
			{
				key: 'single',
				label: 'the single',
				early: hl.single.early,
				recent: hl.single.recent,
				activeStep: 3
			},
			// the six's caption is STEP 5 (step 4 is the single's autopsy beat,
			// which keeps the single hot via the class expression's special case)
			{ key: 'six', label: 'the six', early: hl.six.early, recent: hl.six.recent, activeStep: 5 }
		];
	});
</script>

<div class="pin" class:active>
	{#if ch5 && hl}
		<div class="board" class:shown={reduced || progress >= 0.08}>
			<span class="b-title">what one ball does to the runs a team usually still gets</span>
			<div class="tickers">
				{#each tickers as t (t.key)}
					{@const seasonVal = seasonRow ? seasonRow[t.key] : null}
					<div
						class="ticker"
						class:hot={hotStep === t.activeStep || (hotStep === 4 && t.key === 'single')}
					>
						<span class="t-name">{t.label}</span>
						{#if seasonVal !== null && seasonRow}
							<span class="t-now" class:neg={seasonVal < -0.005} class:pos={seasonVal > 0.005}>
								{dir(seasonVal)} {price(seasonVal)}
							</span>
							<span class="t-then">in {seasonRow.season}</span>
						{:else}
							<span class="t-now" class:neg={t.recent < -0.005} class:pos={t.recent > 0.005}>
								{dir(t.recent)} {price(t.recent)}
							</span>
							<span class="t-then">was: {dir(t.early)} {price(t.early)}</span>
						{/if}
					</div>
				{/each}
			</div>

			<div class="controls">
				<label class="slider">
					<span class="s-lab">
						{seasonRow ? `season ${seasonRow.season}` : 'replay season by season'}
					</span>
					<input
						type="range"
						min="0"
						max={Math.max(0, iplSeasons.length - 1)}
						value={seasonIdx ?? 0}
						oninput={(e) => (seasonIdx = Number((e.currentTarget as HTMLInputElement).value))}
					/>
				</label>
				{#if seasonRow}
					<button class="mini" onclick={() => (seasonIdx = null)}>back to the two eras</button>
				{/if}
				<button class="mini" onclick={() => (listOpen = !listOpen)}>
					{listOpen ? 'close the full price list' : 'the full price list →'}
				</button>
			</div>

			{#if listOpen}
				<div class="full-list">
					<div class="fl-head">
						<span></span><span>2008-2010</span><span>2023-2026</span>
					</div>
					{#each FULL_ROWS as row (row.key)}
						{@const e = ch5.linear_weights.era_bands[IPL_EARLY][row.key]}
						{@const r = ch5.linear_weights.era_bands[IPL_RECENT][row.key]}
						<div class="fl-row">
							<span class="fl-name">{row.label}</span>
							<span class="fl-val" class:neg={e.value < -0.005}>{dir(e.value)} {price(e.value)}</span>
							<span class="fl-val" class:neg={r.value < -0.005}>{dir(r.value)} {price(r.value)}</span>
						</div>
					{/each}
					<p class="fl-note">
						Runs a team usually still gets, moved by one ball of each kind, priced on each era's
						own runs-left table.
					</p>
				</div>
			{/if}
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					This board prices the everyday outcomes. Each price is what one ball of that kind does
					to the runs a team usually still gets. A six adds. A dot takes away. The question is how
					much, and when.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-prices')}
						aria-label="How a price is computed">ⓘ</button
					>
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					The dot got dearer. A dot ball used to take about {hl ? mag1(hl.dot.early) : '0.9'} of a
					run off what was coming. Now it takes about {hl ? mag1(hl.dot.recent) : '1.1'}. Doing
					nothing has never cost more.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					Now the single. It moves the score by one but spends one of just 120 balls. Today that
					trade loses about a quarter of a run. Rotating the strike literally loses ground in this
					league.
				</p>
			</div>
		{:else if step === 4}
			<div class="scene-card">
				<p>
					It used to be dead even. No gain, no loss, a fair trade. The flip is new. The anchor you
					mourned in Chapter 2? This is the autopsy.
				</p>
			</div>
		{:else}
			<!-- MF audit: BOTH era readings bind to the artifact (the ticker above
			     prints 4.76 / 4.59 — the caption must never contradict its board) -->
			<div class="scene-card">
				<p>
					And the six barely moved. About {hl ? mag1(hl.six.early) : '4.8'} runs of value then,
					about {hl ? mag1(hl.six.recent) : '4.6'} now. The reward held its ground while the price
					of caution climbed. That is the whole revolution, printed on one board.
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

	.board {
		pointer-events: auto;
		position: absolute;
		left: 50%;
		top: 42%;
		transform: translate(-50%, -50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.8rem;
		padding: 1rem 1.2rem;
		border-radius: 16px;
		background: rgba(10, 14, 24, 0.82);
		border: 1px solid rgba(151, 161, 184, 0.28);
		max-width: min(40rem, 94vw);
		/* centre-anchored at 42%: capping total height at 56vh keeps the board's
		   bottom edge above ~70vh, provably clear of the bottom-left caption even
		   with the full price list open on short desktops (the list scrolls) */
		max-height: 56vh;
		opacity: 0;
	}

	.board.shown {
		opacity: 1;
	}

	.b-title {
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--ink-dim);
		text-align: center;
	}

	.tickers {
		display: flex;
		gap: clamp(0.6rem, 2.5vw, 1.4rem);
	}

	.ticker {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
		padding: 0.6rem 0.9rem;
		border-radius: 12px;
		border: 1px solid rgba(151, 161, 184, 0.22);
		background: rgba(232, 236, 245, 0.03);
		min-width: 8.5rem;
		transition: border-color 200ms ease, box-shadow 200ms ease;
	}

	.ticker.hot {
		border-color: rgba(255, 209, 102, 0.7);
		box-shadow: 0 0 14px rgba(255, 209, 102, 0.22);
	}

	.t-name {
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.t-now {
		font-size: 1.05rem;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}

	.t-now.neg {
		color: #ff9c9c;
	}

	.t-now.pos {
		color: #7fd8a6;
	}

	.t-then {
		font-size: 0.7rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}

	.controls {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		flex-wrap: wrap;
		justify-content: center;
	}

	.slider {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.15rem;
	}

	.s-lab {
		font-size: 0.62rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.slider input {
		width: clamp(8rem, 24vw, 14rem);
		min-height: 24px;
		accent-color: #ffd166;
		cursor: pointer;
	}

	.mini {
		min-height: 44px;
		padding: 0.35rem 0.7rem;
		border-radius: 999px;
		border: 1px solid rgba(151, 161, 184, 0.4);
		background: none;
		color: var(--ink);
		font-size: 0.75rem;
		font-weight: 600;
		cursor: pointer;
	}

	.mini:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.full-list {
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		border-top: 1px solid rgba(151, 161, 184, 0.2);
		padding-top: 0.6rem;
		/* flexes into whatever the board's 56vh cap leaves and scrolls inside it,
		   so opening the list can never push the board over the caption */
		flex: 1 1 auto;
		min-height: 0;
		max-height: 32vh;
		overflow-y: auto;
	}

	.fl-head,
	.fl-row {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr;
		gap: 0.5rem;
		align-items: baseline;
	}

	.fl-head span {
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.fl-name {
		font-size: 0.8rem;
		font-weight: 600;
	}

	.fl-val {
		font-size: 0.8rem;
		font-variant-numeric: tabular-nums;
	}

	.fl-val.neg {
		color: #ff9c9c;
	}

	.fl-note {
		margin-top: 0.4rem;
		font-size: 0.7rem;
		color: var(--ink-dim);
		line-height: 1.4;
	}

	/* board captions live BOTTOM-LEFT (the board owns the centre) */
	.caption-slot {
		position: absolute;
		left: 4vw;
		bottom: 8vh;
		max-width: min(24rem, 36vw);
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
		.board {
			top: 38%;
			width: 94vw;
			padding: 0.7rem 0.6rem;
		}

		.tickers {
			flex-direction: column;
			width: 100%;
		}

		.ticker {
			flex-direction: row;
			justify-content: space-between;
			width: 100%;
			min-width: 0;
			padding: 0.45rem 0.7rem;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(3vh, calc(env(safe-area-inset-bottom) + 10px));
		}
	}
</style>
