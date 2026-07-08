<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import MatchField from './MatchField.svelte';
	import ReportCardRail from './ReportCardRail.svelte';
	import { panelCaptionStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh8Data, pct0, signed2, fmt2, type Ch8Data, type SpellExemplar } from './data';

	/**
	 * C8-5, SUPPORTING, Belief 3: spell fragmentation + the cold-return tax (FAIL).
	 * The held match-dots dim to a backdrop; the scene is authored SVG/DOM. Each
	 * example innings is a strip of the same 20 overs, drawn as FUSED BARS: a
	 * bowler's unbroken same-end run is ONE bar whose length is its over count, with
	 * a gap before the next bowler, so a settled spell is literally one long bar and
	 * fragmentation is many separate tiles (connectedness, the strongest Gestalt
	 * grouping cue, colourblind-robust). The two eras sit side by side (near-median,
	 * labelled "one example innings", never "typical"), with the ~9-point aggregate
	 * shift pinned adjacent so the vivid picture never outruns the number. The honest
	 * delta ships straight: the cold-return tax GREW, a sixth of a run to nearly a third.
	 */
	const SLOT_COLORS = [
		'#e8a33d',
		'#2ec4b6',
		'#c58fd8',
		'#7ab0f0',
		'#e77e7e',
		'#9bd07a',
		'#f0c95c',
		'#8fa2c4'
	];

	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

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

	const step = $derived(
		progress < 0.2 ? 1 : progress < 0.42 ? 2 : progress < 0.62 ? 3 : progress < 0.82 ? 4 : 5
	);
	const BOUNDS = [0, 0.2, 0.42, 0.62, 0.82, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let midOn = $state(false);
	let panel = $state<HTMLElement | null>(null);
	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => tick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	const capStyle = $derived.by(() => {
		void tick;
		void midOn;
		if (isNarrowViewport()) return '';
		return panelCaptionStyle(panel);
	});

	const sp = $derived(ch8?.spell ?? null);
	const ex2008 = $derived(sp?.exemplars['2008-10']?.[0] ?? null);
	const ex2016 = $derived(sp?.exemplars['2016-19']?.[0] ?? null);
	const ex2026 = $derived(sp?.exemplars['2023-26']?.[0] ?? null);
	const showSecond = $derived(reduced || step >= 2);

	/** the fused bars for an exemplar, sorted in bowling order, width ∝ over count */
	function bars(ex: SpellExemplar): { slot: number; len: number; name: string }[] {
		return ex.spells
			.slice()
			.sort((a, b) => a.start_over - b.start_over)
			.map((s) => ({ slot: s.slot, len: s.len, name: ex.bowler_names[s.slot] ?? '' }));
	}

	const stamped = $derived(reduced || step >= 5 ? 3 : 2);
</script>

<div class="pin" class:active>
	<MatchField {field} {reduced} {progress} faint={true} legend={false} footnoteId="ch8-spell" />
	<ReportCardRail report={ch8?.report_card ?? null} {stamped} />

	<div class="stage">
		<div class="strips" bind:this={panel}>
			{#if ex2008}
				<div class="strip-card">
					<div class="strip-head">
						<span class="era">2008</span>
						<span class="one-example">one example innings</span>
					</div>
					<div class="strip" aria-hidden="true">
						{#each bars(ex2008) as b, i (i)}
							<div
								class="bar"
								style="flex-grow:{b.len}; background:{SLOT_COLORS[b.slot % SLOT_COLORS.length]}"
								title={b.name}
							></div>
						{/each}
					</div>
					<div class="strip-foot">{ex2008.bowling_team} bowling, {ex2008.n_spells} spells over {ex2008.n_overs} overs</div>
				</div>
			{/if}

			{#if midOn && ex2016}
				<div class="strip-card">
					<div class="strip-head">
						<span class="era">2016</span>
						<span class="one-example">one example innings</span>
					</div>
					<div class="strip" aria-hidden="true">
						{#each bars(ex2016) as b, i (i)}
							<div class="bar" style="flex-grow:{b.len}; background:{SLOT_COLORS[b.slot % SLOT_COLORS.length]}" title={b.name}></div>
						{/each}
					</div>
					<div class="strip-foot">{ex2016.bowling_team} bowling, {ex2016.n_spells} spells over {ex2016.n_overs} overs</div>
				</div>
			{/if}

			{#if ex2026 && showSecond}
				<div class="strip-card">
					<div class="strip-head">
						<span class="era">2026</span>
						<span class="one-example">one example innings</span>
					</div>
					<div class="strip" aria-hidden="true">
						{#each bars(ex2026) as b, i (i)}
							<div class="bar" style="flex-grow:{b.len}; background:{SLOT_COLORS[b.slot % SLOT_COLORS.length]}" title={b.name}></div>
						{/each}
					</div>
					<div class="strip-foot">{ex2026.bowling_team} bowling, {ex2026.n_spells} spells over {ex2026.n_overs} overs</div>
				</div>
			{/if}
		</div>

		{#if sp && (reduced || step >= 3)}
			<div class="reads">
				<div class="read">
					<span class="read-num">{pct0(sp.headline.one_over_start)} to {pct0(sp.headline.one_over_end)}</span>
					<span class="read-lbl">one-and-done overs, in 100</span>
				</div>
				{#if reduced || step >= 4}
					<div class="read">
						<span class="read-num">{signed2(sp.headline.tax_start)} to {signed2(sp.headline.tax_end)}</span>
						<span class="read-lbl">the cold-return tax, runs an over</span>
					</div>
				{/if}
			</div>
		{/if}

		{#if ex2016 && (reduced || step >= 2)}
			<button class="mid-toggle" onclick={() => (midOn = !midOn)}>
				{midOn ? 'Hide the 2016 innings' : 'Add a 2016 innings between them'}
			</button>
		{/if}
	</div>

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if sp}
			{#if step === 1}
				<div class="scene-card">
					<p>
						Here is one innings as a strip. One cell per over, in bowling order, coloured by who bowled
						it. When the same bowler bowls on, the cells fuse into one long bar. That bar is a spell.
					</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>Now a 2026 innings beside it. The long bars are mostly gone. More overs, more fresh bowlers, shorter bars.</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						Across the whole league, one-and-done overs, a bowler used for a single over then pulled,
						went from {pct0(sp.headline.one_over_start)} in 100 to {pct0(sp.headline.one_over_end)}.
					</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>
						Bringing a bowler back cold used to cost a sixth of a run an over ({fmt2(sp.headline.tax_start)}).
						Now it costs nearly a third ({fmt2(sp.headline.tax_end)}). The price of matchup chess.
					</p>
				</div>
			{:else}
				<div class="scene-card">
					<p>Belief three: captains build spells. Graded on the whole record: fail. They deal overs like cards now, and it costs them.</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch8-spell')}>ⓘ how we graded the spells</button>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
		display: grid;
		place-items: center;
	}

	.pin.active {
		visibility: visible;
	}

	.stage {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		width: min(60rem, 88vw);
	}

	.strips {
		display: flex;
		gap: 1.2rem;
		width: 100%;
		justify-content: center;
	}

	.strip-card {
		flex: 1;
		max-width: 22rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.strip-head {
		display: flex;
		align-items: baseline;
		gap: 0.6rem;
	}

	.era {
		font-size: 1.1rem;
		font-weight: 800;
		color: var(--ink);
	}

	.one-example {
		font-size: 0.66rem;
		color: var(--ink-dim);
		font-style: italic;
	}

	.strip {
		display: flex;
		gap: 3px;
		height: 2.2rem;
		border-radius: 6px;
		overflow: hidden;
	}

	.bar {
		flex-basis: 0;
		min-width: 4px;
		border-radius: 3px;
	}

	.strip-foot {
		font-size: 0.66rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.reads {
		display: flex;
		gap: 2rem;
	}

	.read {
		display: flex;
		flex-direction: column;
	}

	.read-num {
		font-size: 1.35rem;
		font-weight: 800;
		color: var(--gold);
		font-variant-numeric: tabular-nums;
		line-height: 1;
	}

	.read-lbl {
		font-size: 0.66rem;
		color: var(--ink-dim);
		margin-top: 0.15rem;
	}

	.mid-toggle,
	.fn {
		min-height: 40px;
		padding: 0.2rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.78rem;
		font-weight: 600;
		text-align: left;
		cursor: pointer;
	}

	.mid-toggle:focus-visible,
	.fn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 8vh;
		max-width: min(22rem, 32vw);
		opacity: var(--reveal, 1);
	}

	.fn {
		margin-top: 0.5rem;
	}

	@media (max-width: 640px) {
		.strips {
			flex-direction: column;
			align-items: stretch;
		}

		.strip-card {
			max-width: none;
		}

		.reads {
			gap: 1.2rem;
		}

		.caption-slot {
			position: absolute;
			left: 50%;
			right: auto;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
