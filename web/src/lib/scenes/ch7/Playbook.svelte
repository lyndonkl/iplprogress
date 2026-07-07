<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { panelCaptionStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh7Data, ensureRiverTable, fmt1, pct0, type Ch7Data, type PlaybookSeason } from './data';

	/**
	 * C7-6 — SUPPORTING 3: the Impact Player Playbook Decoder. The league visibly
	 * learning the rule. In 2023 teams spent just over half their impact subs at the
	 * innings break (the safe, obvious slot); by 2025 that was a third — they learned
	 * to hold the card for a mid-innings strike. A 2D per-season stacked bar over the
	 * dimmed rivers (no second morph): gold = used at the break, grey = held for
	 * mid-innings. The shrinking gold band IS the learning curve. Every number from
	 * ch7.json playbook (artifact wins).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.4 ? 1 : progress < 0.72 ? 2 : 3);
	const BOUNDS = [0, 0.4, 0.72, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

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

	/* keep the dim river backdrop alive on a deep link into this beat */
	$effect(() => {
		if (field && ch7) ensureRiverTable(field, ch7);
	});

	const pb = $derived(ch7?.playbook ?? null);
	/* the honest null (audit must-fix #5): the entry order held flat across the rule.
	   Bound to the artifact — rendered only when the emitted data confirms it. */
	const nullFlat = $derived(ch7?.honest_null?.entry_entropy?.flat ?? false);
	interface Bar {
		season: string;
		s: PlaybookSeason;
	}
	const bars = $derived.by<Bar[]>(() => {
		if (!pb) return [];
		return Object.keys(pb.per_season)
			.sort()
			.map((season) => ({ season, s: pb.per_season[season] }));
	});
	/* animate the fill in once the reveal step lands */
	const grown = $derived(reduced || step >= 2);
	const showNull = $derived(nullFlat && (reduced || step >= 3));

	/* §0.4a: place the caption in the measured panel's side margin so it never covers
	   the centred bars (audit should-fix #10). Mobile → bottom read-then-watch slot. */
	let panelEl = $state<HTMLElement | null>(null);
	let capTick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => capTick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	const capStyle = $derived.by(() => {
		void capTick;
		void progress;
		if (isNarrowViewport() || !panelEl) return '';
		return panelCaptionStyle(panelEl);
	});
</script>

<div class="pin" class:active>
	{#if pb}
		<div class="panel" bind:this={panelEl}>
			<p class="overline">the playbook · when teams play their twelfth man</p>
			<div class="bars">
				{#each bars as b (b.season)}
					<div class="col">
						<div class="bar">
							<!-- gold "break" band anchored at the BASELINE so its shrinking height left→
							     right is a clean length read (the single salient change, audit consider #12) -->
							<div class="seg mid" style="height:{grown ? 100 - b.s.break_pct : 100}%;"></div>
							<div
								class="seg break"
								style="height:{grown ? b.s.break_pct : 0}%;"
								title="{fmt1(b.s.break_pct)}% used at the innings break"
							>
								{#if b.s.break_pct >= 14}<span class="seg-lbl">{pct0(b.s.break_pct)}%</span>{/if}
							</div>
						</div>
						<span class="col-name">{b.season}</span>
					</div>
				{/each}
			</div>
			<div class="key">
				<span class="k-row"><span class="sw break"></span> played at the innings break</span>
				<span class="k-row"><span class="sw mid"></span> held for a mid-innings strike</span>
			</div>
			<p class="null-strip" class:show={showNull}>
				But where batters walk in: about the same before and after. A twelfth name, not a new order.
			</p>
			<button class="dagger" onclick={() => footnotesOpen.set('ch7-playbook')} aria-label="How impact-sub timing is counted">
				ⓘ how we read the timing
			</button>
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style="{capStyle}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>
					Each bar is one season's impact subs, split by when teams played them. Gold is the safe,
					obvious slot: at the innings break. Grey is a sub held back for a strike mid-innings.
				</p>
			</div>
		{:else if step === 2 && pb}
			<div class="scene-card">
				<p>
					In 2023, over half went in at the break: <strong>{fmt1(pb.headline.break_pct_2023)}%</strong>.
					By 2025 it was down to {fmt1(pb.headline.break_pct_2025)}%. Watch the gold shrink.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					That is a league learning its own rule fast. But here is what it did not do: it did not
					rewire the batting order. Where batters walk in looks the same as before. A twelfth name,
					not a new way of thinking.
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
		width: min(27rem, 90vw);
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
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--gold);
		margin: 0 0 0.8rem;
	}

	.bars {
		display: flex;
		justify-content: center;
		gap: 1.4rem;
		height: 40vh;
		max-height: 300px;
	}

	.col {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.45rem;
	}

	.bar {
		width: 3rem;
		height: 100%;
		display: flex;
		flex-direction: column;
		border-radius: 8px;
		overflow: hidden;
		border: 1px solid rgba(151, 161, 184, 0.25);
	}

	.seg {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: height 0.6s cubic-bezier(0.22, 1, 0.36, 1);
	}

	.seg.break {
		background: var(--gold);
	}

	.seg.mid {
		background: rgba(151, 161, 184, 0.28);
	}

	.seg-lbl {
		font-size: 0.62rem;
		font-weight: 800;
		color: #0b0e14;
		font-variant-numeric: tabular-nums;
	}

	.col-name {
		font-size: 0.76rem;
		font-weight: 700;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.key {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		margin-top: 0.8rem;
	}

	.k-row {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		font-size: 0.7rem;
		color: var(--ink-dim);
	}

	.sw {
		width: 0.8rem;
		height: 0.8rem;
		border-radius: 3px;
		flex: none;
	}

	.sw.break {
		background: var(--gold);
	}

	.sw.mid {
		background: rgba(151, 161, 184, 0.5);
	}

	.null-strip {
		margin: 0.7rem 0 0;
		padding-top: 0.6rem;
		border-top: 1px solid rgba(151, 161, 184, 0.2);
		font-size: 0.72rem;
		line-height: 1.35;
		color: var(--ink);
		opacity: 0;
		transition: opacity 0.4s ease;
	}

	.null-strip.show {
		opacity: 1;
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
		max-width: min(22rem, 30vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.pin {
			place-items: start center;
			padding-top: 7vh;
		}

		.panel {
			max-height: 74vh;
			overflow-y: auto;
		}

		.bars {
			height: 34vh;
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
