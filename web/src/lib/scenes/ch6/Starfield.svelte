<script lang="ts">
	import { onMount } from 'svelte';
	import type { FieldHandle } from '$lib/field/field';
	import type { ConstellationPhase } from '$lib/field/types';
	import { footnotesOpen } from '$lib/state';
	import { loadCh6Data, groupBy, type Ch6Data, type ConstGroup } from './data';

	/**
	 * The constellation annotation plane (CONTRACT §22.4). Draws the men's
	 * chronological WORM (IPL stars joined in season order), the WPL dotted
	 * THREADS (each WPL star → its nearest men's lookalike for the live phase),
	 * the star LABELS and the two-truths HIGHLIGHT rings — all SVG registered to
	 * the GL star centres via `field.getConstellationLayout().stars[gi]` +
	 * `field.projectToCss`, so the overlay tracks the phase-toggle glide exactly
	 * and never becomes GL geometry (the cardinality rule). NEVER re-embeds — the
	 * star world coords come straight from the field's applied phase table.
	 *
	 * Shared by every constellation scene (orient / two-truths / phase / payoff):
	 * each passes which threads-phase to read, which stars to label, and which to
	 * ring. Coordinates re-derive on resize (`tick`) and as the morph / glide
	 * settles (`progress`).
	 */
	interface Props {
		field: FieldHandle | null;
		reduced: boolean;
		progress: number;
		/** reveal gate — the worm/threads/labels fade in once the morph has landed */
		on?: boolean;
		/** which wpl_threads set to draw (the live phase) */
		threadPhase?: ConstellationPhase;
		showWorm?: boolean;
		showThreads?: boolean;
		/** gis to label (with their group label) */
		labelGis?: number[];
		/** gis to ring + keep bright (the two-truths emphasis) */
		highlightGis?: number[];
		/** dim the worm to a faint trace (behind a 2D panel) */
		faint?: boolean;
		/** render the persistent orientation legend (+ the always-on methods ⓘ) */
		legend?: boolean;
		/** which methods sheet the legend's persistent ⓘ opens */
		footnoteId?: string;
	}
	let {
		field,
		reduced,
		progress,
		on = true,
		threadPhase = 'all',
		showWorm = true,
		showThreads = true,
		labelGis = [],
		highlightGis = [],
		faint = false,
		legend = false,
		footnoteId = 'ch6-constellation'
	}: Props = $props();

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

	let tick = $state(0);
	let seeded = false;
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => tick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	$effect(() => {
		if (field && ch6 && !seeded) {
			seeded = true;
			tick++;
		}
	});

	interface StarCss {
		gi: number;
		x: number;
		y: number;
		g: ConstGroup;
	}

	/** every star projected to CSS px for the LIVE applied phase (tracks the glide) */
	const stars = $derived.by<StarCss[] | null>(() => {
		void tick;
		void progress; // re-project as the morph / phase glide settles
		const f = field;
		const d = ch6;
		if (!f || !d) return null;
		const cl = f.getConstellationLayout();
		if (!cl) return null;
		const gmap = groupBy(d);
		const out: StarCss[] = [];
		for (let gi = 0; gi < cl.stars.length; gi++) {
			const g = gmap.get(gi);
			if (!g) continue;
			const css = f.projectToCss(cl.stars[gi].x, cl.stars[gi].y);
			out.push({ gi, x: css.x, y: css.y, g });
		}
		return out;
	});

	const starAt = $derived.by(() => {
		const m = new Map<number, StarCss>();
		for (const s of stars ?? []) m.set(s.gi, s);
		return m;
	});

	/** the IPL worm polyline points, in chronological order */
	const wormPts = $derived.by(() => {
		const d = ch6;
		if (!d || !stars) return '';
		const pts: string[] = [];
		for (const gi of d.constellation.ipl_worm) {
			const s = starAt.get(gi);
			if (s) pts.push(`${s.x.toFixed(1)},${s.y.toFixed(1)}`);
		}
		return pts.join(' ');
	});

	/** the WPL threads for the live phase: wpl star → nearest men's star */
	const threads = $derived.by(() => {
		const d = ch6;
		if (!d || !stars) return [];
		const set = d.constellation.wpl_threads[threadPhase] ?? d.constellation.wpl_threads.all;
		const out: { x1: number; y1: number; x2: number; y2: number; wplGi: number }[] = [];
		for (const t of set) {
			const a = starAt.get(t.wpl_gi);
			const b = starAt.get(t.nearest_ipl_gi);
			if (a && b) out.push({ x1: a.x, y1: a.y, x2: b.x, y2: b.y, wplGi: t.wpl_gi });
		}
		return out;
	});

	const labels = $derived.by(() => (stars ?? []).filter((s) => labelGis.includes(s.gi)));
	const rings = $derived.by(() => (stars ?? []).filter((s) => highlightGis.includes(s.gi)));
	const shown = $derived(reduced || on);
</script>

{#if stars && shown}
	<svg class="starlines" class:faint aria-hidden="true">
		{#if showWorm && wormPts}
			<polyline class="worm" points={wormPts} />
		{/if}
		{#if showThreads}
			{#each threads as t (t.wplGi)}
				<line class="thread" x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2} />
			{/each}
		{/if}
		{#each rings as r (r.gi)}
			<circle class="ring" class:wpl={r.g.league === 'wpl'} cx={r.x} cy={r.y} r="22" />
		{/each}
	</svg>

	{#each labels as s (s.gi)}
		<span
			class="star-label"
			class:wpl={s.g.league === 'wpl'}
			class:hi={highlightGis.includes(s.gi)}
			style="left:{s.x.toFixed(1)}px; top:{s.y.toFixed(1)}px;"
		>
			{s.g.label}
		</span>
	{/each}
{/if}

<!-- persistent orientation legend + always-on methods ⓘ (§0.4a): survives deep
     entry into any constellation scene, and the ⓘ is never gated by the mobile
     read-gap because it sits outside the caption slot -->
{#if legend}
	<div class="legend">
		<span class="lg-row"><span class="lg-swatch wpl"></span> the women's game</span>
		<span class="lg-row"><span class="lg-worm"></span> the men's seasons, joined in order</span>
		<span class="lg-row lg-note">closer together, plays more alike ball for ball</span>
		<button class="lg-info" onclick={() => footnotesOpen.set(footnoteId)} aria-label="How the map is built">
			ⓘ how we built this map
		</button>
	</div>
{/if}

<style>
	.starlines {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: visible;
	}

	.starlines.faint {
		opacity: 0.32;
	}

	.worm {
		fill: none;
		stroke: rgba(232, 163, 61, 0.55);
		stroke-width: 1.6;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.thread {
		stroke: rgba(46, 196, 182, 0.75);
		stroke-width: 1.4;
		stroke-dasharray: 3 4;
		vector-effect: non-scaling-stroke;
	}

	.ring {
		fill: none;
		stroke: #e8a33d;
		stroke-width: 2;
		vector-effect: non-scaling-stroke;
		opacity: 0.9;
	}

	.ring.wpl {
		stroke: #2ec4b6;
	}

	.star-label {
		position: absolute;
		transform: translate(-50%, calc(-100% - 14px));
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.02em;
		color: var(--ink-dim);
		white-space: nowrap;
		pointer-events: none;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
	}

	.star-label.wpl {
		color: #62d2c3;
	}

	.star-label.hi {
		color: var(--ink);
		font-size: 0.74rem;
	}

	.star-label.wpl.hi {
		color: #7fe0d3;
	}

	/* persistent legend — top-left, clear of the top-right nav; the WPL cluster
	   sits on the LEFT but LOWER than this band, so the legend stays off it */
	.legend {
		position: absolute;
		left: 4vw;
		top: 11vh;
		display: flex;
		flex-direction: column;
		gap: 0.32rem;
		padding: 0.6rem 0.8rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.72);
		border: 1px solid rgba(151, 161, 184, 0.25);
		max-width: min(17rem, 60vw);
	}

	.lg-row {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.lg-note {
		color: var(--ink);
		font-weight: 600;
		line-height: 1.3;
	}

	.lg-swatch {
		width: 0.85rem;
		height: 0.85rem;
		border-radius: 50%;
		flex: none;
		background: #2ec4b6;
		box-shadow: 0 0 8px rgba(46, 196, 182, 0.6);
	}

	.lg-worm {
		width: 0.95rem;
		height: 0;
		flex: none;
		border-top: 2px solid #e8a33d;
		box-shadow: 0 0 6px rgba(232, 163, 61, 0.55);
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
		.star-label {
			font-size: 0.58rem;
			transform: translate(-50%, calc(-100% - 10px));
		}

		.legend {
			top: 8vh;
			left: 3vw;
			padding: 0.45rem 0.6rem;
			gap: 0.25rem;
		}

		.lg-info {
			min-height: 40px;
		}
	}
</style>
