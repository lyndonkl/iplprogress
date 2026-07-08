<script lang="ts">
	import { onMount } from 'svelte';
	import type { FieldHandle } from '$lib/field/field';
	import { matchDotsPoint } from '$lib/field/layout';
	import { footnotesOpen } from '$lib/state';
	import { loadCh8Data, ensureMatchTable, dateNormToField, type Ch8Data } from './data';

	/**
	 * The shared match-dots annotation plane (CONTRACT §24). FEEDS the 1,331-row
	 * match table ONCE (setMatchTable, so the free → match-dots morph and every
	 * held-dots scene share one fed table and can never drift), and draws the season
	 * time-axis + the persistent orientation legend registered to the GL box via
	 * `getMatchDotsLayout()` + `field.projectToCss`. The legend ("one dot, one whole
	 * match, 1,331 of them; left to right is 2008 to 2026") survives deep entry so a
	 * reader landing mid-chapter is never un-oriented.
	 */
	interface Props {
		field: FieldHandle | null;
		reduced: boolean;
		progress: number;
		/** draw the season time-axis (orientation scenes) */
		axis?: boolean;
		/** draw the persistent orientation legend + methods ⓘ */
		legend?: boolean;
		/** dim the axis/legend to a faint trace (behind a 2D panel) */
		faint?: boolean;
		footnoteId?: string;
	}
	let {
		field,
		reduced,
		progress,
		axis = false,
		legend = false,
		faint = false,
		footnoteId = 'ch8-matchdots'
	}: Props = $props();

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

	/* feed the match table ONCE per field instance, the morph reads uMatchTex, so a
	   deep link into any belief still condenses the dots. `tick++` is load-bearing:
	   getMatchDotsLayout() is non-null only after a table is fed. */
	let tick = $state(0);
	let seeded = false;
	$effect(() => {
		if (!field || !ch8 || seeded) return;
		seeded = true;
		ensureMatchTable(field, ch8);
		tick++;
	});

	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => tick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});

	/* re-project one frame after each progress change (applyState sets matchSplit in a
	   sibling effect on the same tick, so reading getMatchDotsLayout synchronously can
	   race, the rAF bump guarantees it ran first). */
	let raf = 0;
	$effect(() => {
		void progress;
		cancelAnimationFrame(raf);
		raf = requestAnimationFrame(() => {
			tick += 1;
		});
		return () => cancelAnimationFrame(raf);
	});

	/** a handful of season ticks along the bottom edge of the box */
	const axisMarks = $derived.by(() => {
		void tick;
		void progress;
		void reduced; // re-project when the motion preference flips (jump-cut vs settle)
		const f = field;
		const d = ch8;
		if (!f || !d) return null;
		const md = f.getMatchDotsLayout();
		if (!md) return null;
		const wanted = new Set([2008, 2011, 2014, 2017, 2020, 2023, 2026]);
		return d.match_dots.axis_ticks
			.filter(([season]) => wanted.has(season))
			.map(([season, xn]) => {
				const p = matchDotsPoint(md, dateNormToField(xn), -1);
				return { season, css: f.projectToCss(p.x, p.y) };
			});
	});
</script>

{#if axis && axisMarks}
	<div class="axis" class:faint aria-hidden="true">
		{#each axisMarks as m (m.season)}
			<span class="season" style="left:{m.css.x.toFixed(1)}px; top:{m.css.y.toFixed(1)}px;">
				{m.season}
			</span>
		{/each}
	</div>
{/if}

{#if legend}
	<div class="legend" class:faint>
		<span class="lg-strong">One dot, one whole match.</span>
		<span class="lg-row">1,331 of them, both leagues.</span>
		<span class="lg-row">Left to right is 2008 to 2026.</span>
		<button
			class="lg-info"
			onclick={() => footnotesOpen.set(footnoteId)}
			aria-label="How the match-dots are built"
		>
			ⓘ how we built the match-dots
		</button>
	</div>
{/if}

<style>
	.axis {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.axis.faint,
	.legend.faint {
		opacity: 0.4;
	}

	.season {
		position: absolute;
		transform: translate(-50%, 10px);
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
		font-size: 0.66rem;
		font-weight: 600;
		color: var(--ink-dim);
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
	}

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
		max-width: min(17rem, 62vw);
	}

	.lg-strong {
		font-size: 0.76rem;
		font-weight: 700;
		color: var(--ink);
	}

	.lg-row {
		font-size: 0.72rem;
		color: var(--ink-dim);
		line-height: 1.3;
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
		/* on mobile the caption uses the bottom slot, so the legend rides the top-left
		   under the report-card strip, clear of the bottom caption and top-right nav */
		.legend {
			bottom: auto;
			top: 12vh;
			left: 2vw;
			padding: 0.4rem 0.55rem;
			gap: 0.16rem;
		}

		.lg-info {
			min-height: 40px;
		}
	}
</style>
