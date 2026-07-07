<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh5Data, fmt1, fmt2, type Ch5Data } from './data';

	/**
	 * C5-8 — Supporting 2: the wicket's counterweight (Wicket Value Index). One
	 * price rose against the tide: a wicket removes more of what the batting side
	 * had coming than it ever has, and it appreciated faster than the runs around
	 * it. A single centred price-tag card flips from the early price to the
	 * recent one; beneath it the "faster than the tide" strip compares the two
	 * rises as plain multipliers. ARTIFACT WINS: 4.2 → 5.1 runs removed (+23.1%)
	 * against run inflation +19.6% on the chapter's era bands; the catalog's
	 * "+33%" (a 2024-26 window) lives in the ch5-prices footnote, labelled.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.36 ? 1 : progress < 0.66 ? 2 : 3);
	const BOUNDS = [0, 0.36, 0.66, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

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

	const wv = $derived(ch5?.wicket_value ?? null);
	const flipDone = $derived(reduced || step >= 1); // the tag shows both; recent lands with the scene
	const stripOn = $derived(reduced || step >= 2);
	/** plain multipliers for the comparison strip (×1.20 vs ×1.23), data-bound */
	const runsMult = $derived(wv ? 1 + wv.run_rate_context.run_inflation_pct / 100 : null);
	const wktMult = $derived(wv ? 1 + wv.run_rate_context.wicket_appreciation_pct / 100 : null);
</script>

<div class="pin" class:active>
	{#if wv}
		<div class="tag" class:shown={flipDone}>
			<span class="t-title">a wicket's price tag</span>
			<span class="t-sub">runs it removes from what the batting side had coming</span>
			<div class="t-pair">
				<div class="t-cell">
					<span class="t-era">2008-2010</span>
					<span class="t-val">{fmt1(wv.headline.early)}</span>
				</div>
				<span class="t-arrow" aria-hidden="true">→</span>
				<div class="t-cell">
					<span class="t-era">2023-2026</span>
					<span class="t-val now">{fmt1(wv.headline.recent)}</span>
				</div>
			</div>
			{#if stripOn && runsMult !== null && wktMult !== null}
				<div class="strip">
					<span class="s-row">
						<span class="s-lab">scoring, across these eras</span>
						<span class="s-val">×{fmt2(runsMult)}</span>
					</span>
					<span class="s-row">
						<span class="s-lab">the wicket's price</span>
						<span class="s-val hot">×{fmt2(wktMult)}</span>
					</span>
				</div>
			{/if}
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					One price went the other way, and hard. The wicket. Taking one used to remove about
					{wv ? fmt1(wv.headline.early) : '4.2'} of the runs the batting side had coming. Now it
					removes about {wv ? fmt1(wv.headline.recent) : '5.1'}.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-prices')}
						aria-label="How a wicket's price tag is computed">ⓘ</button
					>
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Set that against the tide. Scoring across these eras rose by about a fifth. The price of
					a wicket rose faster, nearly a quarter. Wickets appreciated quicker than the runs around
					them.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Put the last two boards together. Caution costs more than it ever did, and the thing
					caution protects is worth more than it ever was. The modern game stopped wasting balls
					to protect wickets. The risk got priced, and batters pay it on purpose.
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

	.tag {
		position: absolute;
		left: 50%;
		top: 46%;
		transform: translate(-50%, -50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 1rem 1.4rem;
		border-radius: 16px;
		background: rgba(10, 14, 24, 0.82);
		border: 1px solid rgba(151, 161, 184, 0.28);
		opacity: 0;
	}

	.tag.shown {
		opacity: 1;
	}

	.t-title {
		font-size: 0.78rem;
		font-weight: 800;
		letter-spacing: 0.12em;
		text-transform: uppercase;
	}

	.t-sub {
		font-size: 0.68rem;
		color: var(--ink-dim);
		text-align: center;
		max-width: 18rem;
	}

	.t-pair {
		display: flex;
		align-items: center;
		gap: 1.1rem;
		margin-top: 0.3rem;
	}

	.t-cell {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.t-era {
		font-size: 0.68rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.t-val {
		font-size: 2rem;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
	}

	.t-val.now {
		color: #ffd166;
	}

	.t-arrow {
		color: var(--ink-dim);
		font-size: 1.3rem;
	}

	.strip {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		width: 100%;
		border-top: 1px solid rgba(151, 161, 184, 0.2);
		padding-top: 0.55rem;
	}

	.s-row {
		display: flex;
		justify-content: space-between;
		gap: 1.2rem;
	}

	.s-lab {
		font-size: 0.74rem;
		color: var(--ink-dim);
	}

	.s-val {
		font-size: 0.82rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.s-val.hot {
		color: #ffd166;
	}

	/* tag captions live TOP-LEFT (the tag owns the centre) */
	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 12vh;
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
		.tag {
			top: 40%;
			width: 88vw;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
