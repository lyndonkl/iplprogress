<script lang="ts">
	import type { HeatCell } from './data';

	/**
	 * The grid-heat panel (storyboard §2f) — one 20 (overs left) × 10 (wickets in
	 * hand) slice of the win surface at the current ask, so "you are reading one
	 * square of a big remembered table" is literal. A brighter square means teams
	 * win more often from there: luminance only, never hue (encoding grammar). The
	 * current cell is ringed. For the WPL, a thin square is hatched, never dark, so
	 * a low-evidence spot can never read as a low-win spot. Collapsed by default so
	 * it never crowds the two headline numbers on a phone.
	 *
	 * Pure presentational: it reads the already-loaded surface slice and draws DOM.
	 * No field access, no rAF — the starfield stays frozen behind it (demand mode).
	 */
	let { rows, wpl }: { rows: HeatCell[][]; wpl: boolean } = $props();
</script>

<figure class="heat" aria-hidden="true">
	<div class="axis-top">more time left →</div>
	<div class="body">
		<div class="axis-left">more wickets →</div>
		<div class="grid" style:--cols={rows[0]?.length ?? 20}>
			{#each rows as row (row[0]?.wkts)}
				{#each row as cell (cell.oversLeft)}
					<span
						class="cell"
						class:masked={cell.masked}
						class:current={cell.current}
						style:--lum={cell.masked ? 0 : cell.value}
					></span>
				{/each}
			{/each}
		</div>
	</div>
	<figcaption>
		{#if wpl}
			Each square is one spot on the women's game. Hatched squares have too few real chases to
			read yet.
		{:else}
			Each square is one spot: how often teams win from there. Brighter means more often. Hatched
			squares are thin ground, too few real chases to count. The ring is where your dials sit.
		{/if}
	</figcaption>
</figure>

<style>
	.heat {
		margin: 0.7rem 0 0;
	}

	.axis-top {
		font-size: 0.6rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-dim);
		margin-bottom: 3px;
		padding-left: 14px;
	}

	.body {
		display: flex;
		align-items: stretch;
		gap: 4px;
	}

	.axis-left {
		font-size: 0.6rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-dim);
		writing-mode: vertical-rl;
		transform: rotate(180deg);
		white-space: nowrap;
	}

	.grid {
		flex: 1;
		display: grid;
		grid-template-columns: repeat(var(--cols), 1fr);
		gap: 1px;
	}

	.cell {
		aspect-ratio: 1 / 1;
		border-radius: 1px;
		/* luminance on the field's ink, never hue: alpha rides the win rate */
		background: rgba(232, 236, 245, calc(0.06 + var(--lum) * 0.9));
	}

	.cell.masked {
		background:
			repeating-linear-gradient(
				45deg,
				rgba(151, 161, 184, 0.32) 0,
				rgba(151, 161, 184, 0.32) 1.5px,
				transparent 1.5px,
				transparent 3.5px
			);
	}

	.cell.current {
		outline: 1.5px solid var(--teal);
		outline-offset: 0;
		z-index: 1;
	}

	figcaption {
		margin-top: 0.45rem;
		font-size: 0.72rem;
		line-height: 1.4;
		color: var(--ink-dim);
	}
</style>
