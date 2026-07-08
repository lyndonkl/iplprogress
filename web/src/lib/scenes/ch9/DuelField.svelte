<script lang="ts">
	import { onMount } from 'svelte';
	import type { FieldHandle } from '$lib/field/field';
	import { footnotesOpen } from '$lib/state';
	import { loadCh9Data, ensureDuelGraph, BATTER_RED, BOWLER_BLUE, type Ch9Data } from './data';

	/**
	 * The shared duel-web feeder + persistent legend (CONTRACT §26.2 / §0.4a). FEEDS
	 * the duel graph ONCE (setDuelGraph, so the free -> web morph and every held-web
	 * scene share one fed graph and can never drift), and draws the persistent
	 * orientation legend so a reader landing mid-chapter is never un-oriented: one
	 * dot is a ball, one strand is a duel, red = runs (the batter came out on top),
	 * blue = the bowler, the deeper the color the more one-sided, a pale strand was
	 * an even fight, and the dim haze is everything else. The strands themselves are
	 * drawn by DuelStrands.svelte; this only feeds + orients.
	 */
	interface Props {
		field: FieldHandle | null;
		/** draw the persistent orientation legend + methods ⓘ */
		legend?: boolean;
		/** dim the legend to a faint trace (behind a 2D panel) */
		faint?: boolean;
		footnoteId?: string;
	}
	let { field, legend = false, faint = false, footnoteId = 'ch9-duel' }: Props = $props();

	let ch9 = $state<Ch9Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh9Data().then((d) => {
			if (alive) ch9 = d;
		});
		return () => {
			alive = false;
		};
	});

	/* feed the duel graph ONCE per field instance (the morph reads uPairingTex /
	   uDuelTex), so a deep link into any later beat still resolves the web. */
	$effect(() => {
		if (field && ch9) ensureDuelGraph(field, ch9);
	});
</script>

{#if legend}
	<div class="legend" class:faint>
		<span class="lg-strong">One dot, one ball. One strand, one duel.</span>
		<span class="lg-row">
			<span class="sw" style="background:{BATTER_RED};"></span>red = runs, the batter came out on top
		</span>
		<span class="lg-row">
			<span class="sw" style="background:{BOWLER_BLUE};"></span>blue = the bowler did
		</span>
		<span class="lg-row">The deeper the color, the more one-sided. A pale strand was an even fight.</span>
		<span class="lg-row dim">The dim haze is everything else.</span>
		<button
			class="lg-info"
			onclick={() => footnotesOpen.set(footnoteId)}
			aria-label="How the duel web is built"
		>
			ⓘ how we built the duel web
		</button>
	</div>
{/if}

<style>
	.legend {
		position: absolute;
		left: 2.5vw;
		bottom: 3vh;
		display: flex;
		flex-direction: column;
		gap: 0.22rem;
		padding: 0.5rem 0.7rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.82);
		border: 1px solid rgba(151, 161, 184, 0.25);
		max-width: min(19rem, 66vw);
	}

	.legend.faint {
		opacity: 0.4;
	}

	.lg-strong {
		font-size: 0.76rem;
		font-weight: 700;
		color: var(--ink);
	}

	.lg-row {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.72rem;
		color: var(--ink-dim);
		line-height: 1.3;
	}

	.lg-row.dim {
		color: rgba(151, 161, 184, 0.7);
	}

	.sw {
		display: inline-block;
		width: 0.8rem;
		height: 0.8rem;
		border-radius: 3px;
		flex: none;
	}

	.lg-info {
		margin-top: 0.15rem;
		min-height: 44px;
		padding: 0.2rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.72rem;
		text-align: left;
		cursor: pointer;
	}

	.lg-info:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.legend {
			bottom: auto;
			top: 12vh;
			left: 2vw;
			padding: 0.4rem 0.55rem;
			gap: 0.16rem;
			max-width: 70vw;
		}

		.lg-info {
			min-height: 40px;
		}
	}
</style>
