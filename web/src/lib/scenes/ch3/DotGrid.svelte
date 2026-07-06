<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh3Data, fmt1, type Ch3Data, type DotInnings } from './data';
	import FrontierScaffold from './FrontierScaffold.svelte';

	/**
	 * C3-5 — The dot-grid (supporting: Dot+). A 2D annotation-plane beat over the
	 * held (dimmed) frontier plane — no re-sort. Two real innings (2009 and 2026),
	 * each 120 cells, one per ball; a dark cell is a dot (a ball with no run). The
	 * grids are illustrative texture, each labelled a single innings and carrying its
	 * own dot tally, each chosen at or near its era's mean dot rate; the LEAGUE
	 * number (37.6 → 33.0) is the evidence, not the eye (storyboard §5.11).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.36) return 1;
		if (progress < 0.66) return 2;
		return 3;
	});
	/* mobile "read, then watch" (CONTRACT §17): ascending step bounds so the caption
	   fades to a clear gap (the two dot-grids stay up to watch) before the next step.
	   1 on desktop / reduced. */
	const BOUNDS = [0, 0.36, 0.66, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch3 = $state<Ch3Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh3Data().then((d) => {
			if (alive) ch3 = d;
		});
		return () => {
			alive = false;
		};
	});

	const innings = $derived<DotInnings[]>(ch3 ? ch3.dot_grid.innings : []);
	/* the exemplar seasons come from the artifact (each chosen near its era's mean
	   dot rate), so the caption can never drift from which innings are shown */
	const earlySeason = $derived(innings[0]?.season ?? null);
	const modernSeason = $derived(innings[1]?.season ?? null);
	const dotEarly = $derived(ch3 ? ch3.dot_plus.era_headline.ipl_2008_2010 : null);
	const dotModern = $derived(ch3 ? ch3.dot_plus.era_headline.ipl_2023_2026 : null);

	/* outcome → colour (dot darkest; brighter = more runs) */
	const CELL = ['#10141d', '#3a4765', '#5b7098', '#2ec4b6', '#e8a33d', '#242a38'];
	const legend = [
		{ c: '#10141d', label: 'dot' },
		{ c: '#3a4765', label: 'single' },
		{ c: '#5b7098', label: 'two/three' },
		{ c: '#2ec4b6', label: 'four' },
		{ c: '#e8a33d', label: 'six' }
	];
</script>

<div class="pin" class:active>
	<!-- faint persistent orientation anchors behind the dot-grids (held C3-3..C3-8) -->
	<FrontierScaffold {field} faint />

	{#if innings.length === 2}
		<div class="grids" class:shown={step >= 1}>
			{#each innings as inn (inn.label)}
				<figure class="grid-fig">
					<figcaption>
						<span class="g-title">{inn.label}</span>
						<span class="g-sub">{inn.batting_team} v {inn.opponent}</span>
					</figcaption>
					<div class="grid" role="img" aria-label="{inn.label}: {inn.dots} dots of {inn.legal_balls} balls">
						{#each inn.outcomes as o, i (i)}
							<span class="cell" class:wkt={inn.wickets[i] === 1} style="background:{CELL[o] ?? CELL[5]}"></span>
						{/each}
					</div>
					<p class="tally"><strong>{inn.dots}</strong> dots of {inn.legal_balls} · {fmt1(inn.dot_pct)}%</p>
				</figure>
			{/each}
		</div>

		<div class="legend" class:shown={step >= 1}>
			{#each legend as l (l.label)}
				<span class="key"><span class="swatch" style="background:{l.c}"></span>{l.label}</span>
			{/each}
		</div>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					Here are two innings, one from {earlySeason ?? '2010'} and one from {modernSeason ?? '2026'},
					drawn as <strong>120 boxes, one box per ball.</strong> A dark box is a dot, a ball the batter
					could not score off. Each grid shows its own dot count.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card chip">
				<p>
					One innings is noisy, so trust the league, not the two grids. Across every ball bowled,
					<strong>dots fell from {dotEarly !== null ? fmt1(dotEarly) : '-'}% in the early years to
						{dotModern !== null ? fmt1(dotModern) : '-'}% now.</strong> The dot is drying up.
					<button class="dagger" onclick={() => footnotesOpen.set('dot-plus')} aria-label="How dots were counted">ⓘ</button>
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					So a bowler who still bowls a pile of dots today is doing something
					<strong>harder than the same bowler in 2009.</strong> The dot did not get easier. It got
					rarer, which means <strong>every one is worth more.</strong>
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

	.grids {
		position: absolute;
		top: 6vh;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		gap: 1.6rem;
		opacity: 0;
		transition: opacity 500ms ease;
	}

	.grids.shown {
		opacity: 1;
	}

	.grid-fig {
		margin: 0;
		text-align: center;
	}

	.grid-fig figcaption {
		display: flex;
		flex-direction: column;
		gap: 0.05rem;
		margin-bottom: 0.35rem;
	}

	.g-title {
		font-size: 0.8rem;
		font-weight: 700;
		color: var(--ink);
	}

	.g-sub {
		font-size: 0.66rem;
		color: var(--ink-dim);
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		gap: 2px;
		width: min(150px, 34vw);
	}

	.cell {
		aspect-ratio: 1;
		border-radius: 2px;
		border: 1px solid rgba(232, 236, 245, 0.06);
	}

	.cell.wkt {
		outline: 1.5px solid #ff5d3a;
		outline-offset: -1px;
	}

	.tally {
		margin: 0.4rem 0 0;
		font-size: 0.74rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.tally strong {
		color: var(--ink);
	}

	.legend {
		position: absolute;
		top: 6vh;
		left: 50%;
		transform: translate(-50%, -140%);
		display: flex;
		gap: 0.8rem;
		flex-wrap: wrap;
		justify-content: center;
		opacity: 0;
		transition: opacity 500ms ease;
	}

	.legend.shown {
		opacity: 1;
	}

	.key {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.68rem;
		color: var(--ink-dim);
	}

	.swatch {
		width: 11px;
		height: 11px;
		border-radius: 2px;
		border: 1px solid rgba(232, 236, 245, 0.12);
	}

	@media (prefers-reduced-motion: reduce) {
		.grids,
		.legend {
			transition: none;
		}
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 10vh;
		max-width: min(32rem, 84vw);
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

	@media (max-width: 640px) {
		.grids {
			top: 4vh;
			/* stack the two grids (2010 above 2026) so the dark-cell contrast survives
			   at legible cell sizes instead of shrinking to ~24px side by side */
			flex-direction: column;
			align-items: center;
			gap: 0.9rem;
		}

		.grid {
			width: min(60vw, 220px);
		}

		.legend {
			top: 3vh;
			transform: translate(-50%, -120%);
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(72px, calc(env(safe-area-inset-bottom) + 56px));
		}
	}
</style>
