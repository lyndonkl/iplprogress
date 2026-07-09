<script lang="ts">
	import { onMount } from 'svelte';
	import type { FieldHandle } from '$lib/field/field';
	import { footnotesOpen } from '$lib/state';
	import { loadCh10Data, type Ch10Data, type TimeTick } from './data';
	import { isNarrowViewport } from './captionCorner.svelte';

	/**
	 * The shared held-ribbon backdrop + persistent orientation legend (§0.4a). The
	 * ribbon is a PURE FUNCTION of position.x, so unlike Ch 9's duel web there is
	 * nothing to FEED; this only draws the legend so a reader landing mid-chapter is
	 * never un-oriented (one dot one ball, left to right is 2008 to now, spaced by
	 * balls so recent seasons are wider), and optionally the time-axis tick-lane
	 * under the band (seasons anchored to the GL band via getRibbonLayout().pointToX
	 * + projectToCss, so the labels can never drift from the ribbon).
	 */
	interface Props {
		field: FieldHandle | null;
		/** draw the persistent orientation legend + methods ⓘ */
		legend?: boolean;
		/** dim the legend to a faint trace (behind a 2D panel) */
		faint?: boolean;
		/** draw the season tick-lane under the band (C10-2 the orient scene) */
		timeAxis?: boolean;
		footnoteId?: string;
		/** re-project trigger (a scene passes its progress so the axis tracks scroll) */
		progress?: number;
	}
	let {
		field,
		legend = false,
		faint = false,
		timeAxis = false,
		footnoteId = 'ch10-seismo',
		progress = 0
	}: Props = $props();

	let ch10 = $state<Ch10Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh10Data().then((d) => {
			if (alive) ch10 = d;
		});
		return () => {
			alive = false;
		};
	});

	/* re-project one frame after each progress change / resize (applyState sets the
	   scalars in a sibling effect on the same tick, so a synchronous read can race). */
	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => tick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	let raf = 0;
	$effect(() => {
		void progress;
		cancelAnimationFrame(raf);
		raf = requestAnimationFrame(() => {
			tick += 1;
		});
		return () => cancelAnimationFrame(raf);
	});

	interface DrawnTick {
		season: number;
		x: number;
		y: number;
	}

	const ticks = $derived.by<DrawnTick[] | null>(() => {
		void tick;
		void progress;
		const f = field;
		const d = ch10;
		if (!f || !d || !timeAxis) return null;
		const rib = f.getRibbonLayout();
		if (!rib) return null;
		const baseY = rib.box.bandY - rib.box.bandHalf;
		// on a phone the labels collide, so only 2008 / the midpoint / now are drawn
		const all: TimeTick[] = d.ribbon.time_axis_ticks;
		const chosen = isNarrowViewport()
			? [all[0], all[Math.floor(all.length / 2)], all[all.length - 1]]
			: all;
		return chosen
			.filter((t): t is TimeTick => !!t)
			.map((t) => {
				const p = f.projectToCss(rib.pointToX(t.ball_pos), baseY);
				return { season: t.season, x: p.x, y: p.y };
			});
	});
</script>

{#if ticks}
	<svg class="axis" aria-hidden="true">
		{#each ticks as t (t.season)}
			<line class="tick" x1={t.x.toFixed(1)} y1={(t.y + 4).toFixed(1)} x2={t.x.toFixed(1)} y2={(t.y + 12).toFixed(1)} />
			<text class="tick-label" x={t.x.toFixed(1)} y={(t.y + 26).toFixed(1)}>{t.season}</text>
		{/each}
	</svg>
{/if}

{#if legend && ch10}
	<div class="legend" class:faint>
		<span class="lg-strong">One dot, one ball. Left to right is time.</span>
		<span class="lg-row">2008 on the left, now on the right, spaced by balls.</span>
		<span class="lg-row dim">Recent seasons are wider because there are more matches now, not because anything sped up.</span>
		<span class="lg-row">A crack is where the game broke. A solid bright one we are surer of, a faint dashed one less so.</span>
		<button class="lg-info" onclick={() => footnotesOpen.set(footnoteId)} aria-label="How the ribbon is built">
			ⓘ how the ribbon is read
		</button>
	</div>
{/if}

<style>
	.axis {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: visible;
	}

	.tick {
		stroke: rgba(151, 161, 184, 0.55);
		stroke-width: 1;
		vector-effect: non-scaling-stroke;
	}

	.tick-label {
		fill: var(--ink-dim);
		font-size: 0.62rem;
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
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
		max-width: min(21rem, 66vw);
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
		font-size: 0.72rem;
		color: var(--ink-dim);
		line-height: 1.3;
	}

	.lg-row.dim {
		color: rgba(151, 161, 184, 0.7);
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
			top: 11vh;
			left: 2vw;
			padding: 0.4rem 0.55rem;
			gap: 0.16rem;
			max-width: 72vw;
		}
	}
</style>
