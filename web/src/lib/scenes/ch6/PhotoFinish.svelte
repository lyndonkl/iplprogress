<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh6Data, fmt1, type Ch6Data } from './data';

	/**
	 * C6-8 — SUPPORTING 3: the Photo-Finish rate (the payoff stat). A photo-finish
	 * is a defence won by five runs or fewer, or a chase completed with three balls
	 * or fewer to spare — the nail-biters. The WPL is the TIGHTEST league in the
	 * whole dataset: 24.1% of its decided matches, above every IPL era (16-23%). A
	 * 2D annotation-plane scene over the dimmed constellation. Every number from
	 * ch6.json photo_finish (artifact wins).
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

	const pf = $derived(ch6?.photo_finish ?? null);
	const wplPct = $derived(pf?.headline.wpl ?? 24.1);

	interface Bar {
		key: string;
		name: string;
		pct: number;
		league: 'ipl' | 'wpl';
	}
	const bars = $derived.by<Bar[]>(() => {
		if (!pf) return [];
		const ipl: Bar[] = Object.entries(pf.ipl_eras)
			.map(([k, v]) => ({
				key: k,
				name: 'IPL ' + k.replace(/^[a-z]+ /, ''),
				pct: v.pct,
				league: 'ipl' as const
			}))
			.sort((a, b) => a.key.localeCompare(b.key));
		return [{ key: 'wpl', name: 'WPL', pct: pf.wpl_all.pct, league: 'wpl' as const }, ...ipl];
	});
	const maxPct = $derived(Math.max(1, ...bars.map((b) => b.pct)));
	const grown = $derived(reduced || step >= 2);
</script>

<div class="pin" class:active>
	{#if pf}
		<div class="panel">
			<p class="overline">photo finish · how often it goes to the wire</p>
			<div class="bars">
				{#each bars as b (b.key)}
					<div class="row">
						<span class="r-name" class:wpl={b.league === 'wpl'}>{b.name}</span>
						<div class="track">
							<div
								class="fill {b.league}"
								style="width:{grown ? (b.pct / maxPct) * 100 : 0}%;"
							></div>
						</div>
						<span class="r-val" class:wpl={b.league === 'wpl'}>{fmt1(b.pct)}%</span>
					</div>
				{/each}
			</div>
			<button
				class="dagger"
				onclick={() => footnotesOpen.set('ch6-photofinish')}
				aria-label="What counts as a photo finish">ⓘ what counts as one</button
			>
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					One last dialect word. A photo-finish is a game won by five runs or fewer, or a chase
					home with three balls or fewer to spare. The ones that go to the very last over. Here is
					how often each league serves one up.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					The WPL: <strong>{fmt1(wplPct)}%</strong> of its finished games. No IPL era has ever been
					that tight. Not one.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					The tightest league in this whole story. Its own way of playing ends in the closest
					finishes too. Beside the path, and worth watching to the last ball.
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
		width: min(34rem, 92vw);
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
		flex-direction: column;
		gap: 0.55rem;
	}

	.row {
		display: grid;
		grid-template-columns: 6.5rem 1fr 2.6rem;
		align-items: center;
		gap: 0.6rem;
	}

	.r-name {
		font-size: 0.72rem;
		color: var(--ink-dim);
		text-align: right;
		font-variant-numeric: tabular-nums;
	}

	.r-name.wpl {
		color: #62d2c3;
		font-weight: 700;
	}

	.track {
		height: 0.85rem;
		background: rgba(151, 161, 184, 0.14);
		border-radius: 999px;
		overflow: hidden;
	}

	.fill {
		height: 100%;
		border-radius: 999px;
		transition: width 0.5s ease;
	}

	.fill.ipl {
		background: #e8a33d;
	}

	.fill.wpl {
		background: #2ec4b6;
		box-shadow: 0 0 10px rgba(46, 196, 182, 0.5);
	}

	.r-val {
		font-size: 0.78rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		color: var(--ink-dim);
	}

	.r-val.wpl {
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
		max-width: min(23rem, 34vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.pin {
			place-items: start center;
			padding-top: 8vh;
		}

		.panel {
			max-height: 70vh;
			overflow-y: auto;
		}

		.row {
			grid-template-columns: 5rem 1fr 2.4rem;
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
