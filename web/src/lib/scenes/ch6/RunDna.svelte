<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh6Data, fmt1, type Ch6Data, type DnaComposition } from './data';

	/**
	 * C6-6 — SUPPORTING 1: Run DNA (the different engine). Two composition columns
	 * side by side: where every run comes from, modern IPL vs WPL. The WPL is
	 * FOUR-led — 46.8% of its runs are fours against the IPL's 33.9% — and leans on
	 * the six far less (15.5% vs 29.0%). A structurally different scoring engine, a
	 * flood along the ground, not a scaled-down copy. A 2D annotation-plane scene
	 * over the dimmed constellation (no second morph). Every number from ch6.json
	 * run_dna.helix (artifact wins).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.4 ? 1 : progress < 0.72 ? 2 : 3);
	const BOUNDS = [0, 0.4, 0.72, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch6 = $state<Ch6Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh6Data().then((d) => {
			if (alive) ch6 = d;
		});
		return () => {
			alive = false;
		};
	});

	const dna = $derived(ch6?.run_dna ?? null);
	const fourWpl = $derived(dna?.headline.four_share.wpl ?? 46.8);
	const fourIpl = $derived(dna?.headline.four_share.ipl_modern ?? 33.9);
	const sixWpl = $derived(dna?.headline.six_share.wpl ?? 15.5);
	const sixIpl = $derived(dna?.headline.six_share.ipl_modern ?? 29.0);

	interface Seg {
		key: string;
		label: string;
		pct: number;
		cls: string;
		big: boolean;
	}
	/** segments top→bottom: sixes, fours, threes, twos, singles, then extras/5s */
	function segments(c: DnaComposition): Seg[] {
		const other = Math.max(0, 100 - (c.six + c.four + c.three + c.two + c.single));
		return [
			{ key: 'six', label: 'sixes', pct: c.six, cls: 'six', big: true },
			{ key: 'four', label: 'fours', pct: c.four, cls: 'four', big: true },
			{ key: 'three', label: 'threes', pct: c.three, cls: 'three', big: false },
			{ key: 'two', label: 'twos', pct: c.two, cls: 'two', big: false },
			{ key: 'single', label: 'singles', pct: c.single, cls: 'single', big: false },
			{ key: 'other', label: 'extras', pct: other, cls: 'other', big: false }
		];
	}
	const cols = $derived(
		dna
			? [
					{ league: 'ipl', name: 'IPL, recent', segs: segments(dna.helix.ipl_modern) },
					{ league: 'wpl', name: 'WPL', segs: segments(dna.helix.wpl) }
				]
			: []
	);
	/* highlight the boundary bands from the reveal step on */
	const emph = $derived(reduced || step >= 2);
</script>

<div class="pin" class:active>
	{#if dna}
		<div class="panel">
			<p class="overline">run dna · where every run comes from</p>
			<div class="bars">
				{#each cols as col (col.league)}
					<div class="col">
						<div class="bar" class:emph>
							{#each col.segs as s (s.key)}
								<div
									class="seg {s.cls}"
									class:boundary={s.big}
									style="height:{s.pct}%;"
									title="{s.label}: {fmt1(s.pct)}% of runs"
								>
									{#if s.big && s.pct >= 8}
										<span class="seg-lbl">{s.label} {fmt1(s.pct)}%</span>
									{/if}
								</div>
							{/each}
						</div>
						<span class="col-name" class:wpl={col.league === 'wpl'}>{col.name}</span>
					</div>
				{/each}
			</div>
			<button
				class="dagger"
				onclick={() => footnotesOpen.set('ch6-dna')}
				aria-label="How the run breakdown is counted">ⓘ how we count this</button
			>
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					Break every run down by how it was scored. Each column is one league's runs, singles and
					twos near the bottom, fours and sixes stacked on top. The four and six bands carry their
					share, so read those numbers, not the heights.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					The WPL's fat gold band is fours: <strong>{fmt1(fourWpl)}%</strong> of its runs, against
					the modern IPL's {fmt1(fourIpl)}%. This is a game scored along the ground.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					The red band, sixes, flips it: {fmt1(sixWpl)}% for the WPL against
					<strong>{fmt1(sixIpl)}%</strong> for the IPL. A different engine, not a smaller one.
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
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	.pin.active {
		visibility: visible;
	}

	.panel {
		pointer-events: auto;
		width: min(26rem, 88vw);
		background: rgba(11, 14, 20, 0.72);
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 14px;
		padding: 1rem 1.2rem 1.1rem;
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
	}

	.overline {
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: var(--gold);
		margin: 0 0 0.7rem;
	}

	.bars {
		display: flex;
		justify-content: center;
		gap: 2.4rem;
		height: 46vh;
		max-height: 340px;
	}

	.col {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.bar {
		width: 4.4rem;
		height: 100%;
		display: flex;
		flex-direction: column;
		border-radius: 8px;
		overflow: hidden;
		border: 1px solid rgba(151, 161, 184, 0.25);
	}

	.seg {
		width: 100%;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: filter 0.25s ease;
	}

	.seg.six {
		background: #d1495b;
	}

	.seg.four {
		background: #e8a33d;
	}

	.seg.three {
		background: rgba(151, 161, 184, 0.55);
	}

	.seg.two {
		background: rgba(151, 161, 184, 0.42);
	}

	.seg.single {
		background: rgba(151, 161, 184, 0.28);
	}

	.seg.other {
		background: rgba(151, 161, 184, 0.14);
	}

	/* before the reveal, the boundary bands sit quiet; on emph they pop */
	.bar:not(.emph) .seg.boundary {
		filter: saturate(0.55) brightness(0.8);
	}

	.seg-lbl {
		font-size: 0.6rem;
		font-weight: 800;
		color: #0b0e14;
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
		text-shadow: 0 0 3px rgba(255, 255, 255, 0.35);
	}

	.col-name {
		font-size: 0.78rem;
		font-weight: 700;
		color: var(--gold);
	}

	.col-name.wpl {
		color: #62d2c3;
	}

	.dagger {
		display: inline-block;
		margin-top: 0.7rem;
		min-height: 44px;
		padding: 0.3rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.78rem;
		cursor: pointer;
	}

	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 6vh;
		max-width: min(23rem, 32vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.pin {
			place-items: start center;
			padding-top: 7vh;
		}

		.panel {
			max-height: 70vh;
			overflow-y: auto;
		}

		.bars {
			height: 38vh;
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
