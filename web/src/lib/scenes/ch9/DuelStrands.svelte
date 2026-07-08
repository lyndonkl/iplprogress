<script lang="ts">
	import { onMount } from 'svelte';
	import type { FieldHandle } from '$lib/field/field';
	import { dominanceColor, strandOpacity, type DuelWebLayout, type DuelEdge } from './data';

	/**
	 * The shared duel-web SVG overlay (CONTRACT §26.4): the player-to-player
	 * strands, the player-node dots, the hero isolation (extra width + a pulsing
	 * knot + a pinned leader-line callout) and the tap targets, all scene-authored
	 * SVG registered to the GL box via `getDuelWebLayout()` + `field.projectToCss`.
	 * The field draws no lines; it owns only the dust and the in-strand knots.
	 *
	 * Reused by C9-2 (orient), C9-3 (the three tiers + tap-a-duel), C9-5 (the season
	 * scrub), C9-7 (the WPL sub-web foregrounded) and C9-8 (the payoff highlight).
	 * strandRecede is a FIELD scalar (the knots); this SVG mirrors it on the lines:
	 * a `focusIds` set carries full red/blue chroma while every other strand falls
	 * to a faint neutral gray, so only the argued rivalries pop out of the tangle.
	 */
	interface Props {
		field: FieldHandle | null;
		reduced: boolean;
		progress: number;
		/** true while this scene owns the field (gates the shared setDuelFocus write) */
		active?: boolean;
		/** the bright tier cap (the render mock proved ~60 legible; mobile passes fewer) */
		topN?: number;
		/** the in-focus duel ids: these keep chroma, the rest recede to gray (null = all) */
		focusIds?: number[] | null;
		/** the hero duel: extra width + a pulsing knot + a pinned leader-line callout */
		heroId?: number | null;
		/** a persistent highlighted strand (the payoff rivalry), extra width, no pulse */
		highlightId?: number | null;
		/** season scrub: draw a strand only once its first season has arrived (null = all) */
		litUpToSeason?: number | null;
		/** a transient reset flash 0..1 (C9-5): lit strands brighten as a reset sweeps */
		flash?: number;
		/** foreground the WPL sub-web (its strands bright, the men's web faint) */
		wplForeground?: boolean;
		/** draw the hub labels for the busiest players */
		showHubLabels?: boolean;
		/** how many hubs to label (desktop ~5, mobile ~3) */
		hubLabelCount?: number;
		/** tap a strand for its replay (desktop primary) */
		onTapDuel?: (id: number) => void;
		/** tap a player node to isolate their strands (the mobile two-step drill) */
		onTapNode?: (nodeIndex: number) => void;
	}
	let {
		field,
		reduced,
		progress,
		active = true,
		topN = 60,
		focusIds = null,
		heroId = null,
		highlightId = null,
		litUpToSeason = null,
		flash = 0,
		wplForeground = false,
		showHubLabels = false,
		hubLabelCount = 5,
		onTapDuel,
		onTapNode
	}: Props = $props();

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

	/* drive the field's hero-isolation focus set (§26.2). The knots recede in-shader
	   via strandRecede + uDuelFocusTex; this SVG mirrors the recede on the lines. Gated
	   on `active` so an off-screen scene's overlay never clobbers the live focus set. */
	$effect(() => {
		if (!field || !active) return;
		field.setDuelFocus(focusIds && focusIds.length > 0 ? focusIds : null);
	});

	const focusSet = $derived(focusIds ? new Set(focusIds) : null);

	interface DrawnStrand {
		id: number;
		x1: number;
		y1: number;
		x2: number;
		y2: number;
		mx: number;
		my: number;
		color: string;
		opacity: number;
		width: number;
		bat: string;
		bowl: string;
		balls: number;
	}

	const geom = $derived.by(() => {
		void tick;
		void progress;
		void reduced;
		void flash;
		const f = field;
		if (!f) return null;
		const dw = f.getDuelWebLayout() as DuelWebLayout | null;
		if (!dw || dw.nodes.length === 0) return null;

		const npos = dw.nodes.map((n) => f.projectToCss(n.x, n.y));

		// which strands to draw: the top tier prefix (edges are sorted by balls DESC),
		// plus any focus / hero / highlight ids so an isolated set is never dropped.
		const drawIds = new Set<number>();
		for (let i = 0; i < Math.min(topN, dw.edges.length); i++) drawIds.add(dw.edges[i].id);
		if (focusIds) for (const id of focusIds) drawIds.add(id);
		if (heroId != null) drawIds.add(heroId);
		if (highlightId != null) drawIds.add(highlightId);

		const byId = new Map<number, DuelEdge>();
		for (const e of dw.edges) byId.set(e.id, e);

		const strands: DrawnStrand[] = [];
		for (const id of drawIds) {
			const e = byId.get(id);
			if (!e) continue;
			const na = dw.nodes[e.a];
			const nb = dw.nodes[e.b];
			if (!na || !nb) continue;
			const isWpl = na.league === 'wpl' && nb.league === 'wpl';
			// season scrub: a strand is drawn only once its first season has arrived
			if (litUpToSeason != null && e.span[0] > litUpToSeason) continue;

			const isFocus = focusSet ? focusSet.has(id) : true;
			const isHero = heroId === id;
			const isHi = highlightId === id;

			// WPL foreground: the men's web recedes to gray, the WPL web keeps chroma
			const receded = (focusSet && !isFocus) || (wplForeground && !isWpl && !isHero && !isHi);
			const color = dominanceColor(e.color, receded ? 1 : 0);
			let opacity = strandOpacity(e.balls);
			if (receded) opacity *= 0.28;
			if (flash > 0 && !receded) opacity = Math.min(1, opacity + 0.4 * flash);
			const width = isHero ? 3.4 : isHi ? 2.6 : receded ? 1 : 1.5;

			const a = npos[e.a];
			const b = npos[e.b];
			strands.push({
				id,
				x1: a.x,
				y1: a.y,
				x2: b.x,
				y2: b.y,
				mx: (a.x + b.x) / 2,
				my: (a.y + b.y) / 2,
				color,
				opacity,
				width,
				bat: e.bat,
				bowl: e.bowl,
				balls: e.balls
			});
		}
		// draw receded first, chroma on top, hero/highlight last
		strands.sort((p, q) => p.width - q.width);

		// the hero knot + leader-line label (found by width + a pulsing knot + a label)
		let hero: { mx: number; my: number; bat: string; bowl: string } | null = null;
		if (heroId != null) {
			const s = strands.find((x) => x.id === heroId);
			if (s) hero = { mx: s.mx, my: s.my, bat: s.bat, bowl: s.bowl };
		}

		// the hub labels for the busiest players (deg is the hub weight, never drawn as a stat)
		const hubs = showHubLabels
			? dw.nodes
					.map((n, i) => ({ n, i, css: npos[i] }))
					.filter((h) => (wplForeground ? h.n.league === 'wpl' : true))
					.sort((p, q) => q.n.deg - p.n.deg)
					.slice(0, hubLabelCount)
			: [];

		return { npos, nodes: dw.nodes, strands, hero, hubs };
	});

	// the leader-line label sits up-and-right of the knot, clamped into the viewport
	function labelPos(mx: number, my: number): { lx: number; ly: number } {
		const vw = typeof window !== 'undefined' ? window.innerWidth : 1024;
		const right = mx < vw * 0.6;
		return { lx: right ? mx + 54 : mx - 54, ly: my - 46 };
	}
</script>

{#if geom}
	<svg class="web" aria-hidden="true">
		<!-- the strands: a strand is a duel; color = who came out on top, opacity = ball-weight -->
		{#each geom.strands as s (s.id)}
			<line
				class="strand"
				class:hero={heroId === s.id}
				x1={s.x1.toFixed(1)}
				y1={s.y1.toFixed(1)}
				x2={s.x2.toFixed(1)}
				y2={s.y2.toFixed(1)}
				stroke={s.color}
				stroke-width={s.width}
				opacity={s.opacity.toFixed(3)}
			/>
		{/each}

		<!-- the player-node dots: constant radius, never a stat; WPL nodes teal -->
		{#each geom.nodes as n, i (i)}
			<circle
				class="node"
				class:wpl={n.league === 'wpl'}
				cx={geom.npos[i].x.toFixed(1)}
				cy={geom.npos[i].y.toFixed(1)}
				r={n.league === 'wpl' ? 2.2 : 1.8}
			/>
		{/each}

		<!-- the hero's pulsing knot (motion is the one preattentive channel that survives the tangle) -->
		{#if geom.hero && !reduced}
			<circle class="knot-pulse" cx={geom.hero.mx.toFixed(1)} cy={geom.hero.my.toFixed(1)} r="7" />
		{/if}
		{#if geom.hero}
			{@const lp = labelPos(geom.hero.mx, geom.hero.my)}
			<circle class="knot" cx={geom.hero.mx.toFixed(1)} cy={geom.hero.my.toFixed(1)} r="4.5" />
			<line
				class="leader"
				x1={geom.hero.mx.toFixed(1)}
				y1={geom.hero.my.toFixed(1)}
				x2={lp.lx.toFixed(1)}
				y2={(lp.ly + 6).toFixed(1)}
			/>
		{/if}

		<!-- the tap targets (invisible fat lines): strand tap opens the replay -->
		{#if onTapDuel}
			{#each geom.strands as s (s.id)}
				<line
					class="hit"
					x1={s.x1.toFixed(1)}
					y1={s.y1.toFixed(1)}
					x2={s.x2.toFixed(1)}
					y2={s.y2.toFixed(1)}
					onclick={() => onTapDuel?.(s.id)}
					onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), onTapDuel?.(s.id))}
					role="button"
					tabindex="-1"
					aria-label={`Replay ${s.bat} versus ${s.bowl}`}
				/>
			{/each}
		{/if}

		<!-- node tap targets (the mobile two-step drill: isolate a player's strands) -->
		{#if onTapNode}
			{#each geom.nodes as n, i (i)}
				<circle
					class="node-hit"
					cx={geom.npos[i].x.toFixed(1)}
					cy={geom.npos[i].y.toFixed(1)}
					r="22"
					onclick={() => onTapNode?.(i)}
					onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), onTapNode?.(i))}
					role="button"
					tabindex="-1"
					aria-label={`Isolate ${n.name}'s rivalries`}
				/>
			{/each}
		{/if}
	</svg>

	<!-- the hero leader-line label (DOM, so the type is crisp) -->
	{#if geom.hero}
		{@const lp = labelPos(geom.hero.mx, geom.hero.my)}
		<div
			class="hero-label"
			class:flip={lp.lx < geom.hero.mx}
			style="left:{lp.lx.toFixed(1)}px; top:{lp.ly.toFixed(1)}px;"
			aria-hidden="true"
		>
			<strong>{geom.hero.bat}</strong> v {geom.hero.bowl}
		</div>
	{/if}

	<!-- the hub labels (only the central hubs; the full set is a hairball) -->
	{#if showHubLabels}
		<div class="hubs" aria-hidden="true">
			{#each geom.hubs as h (h.i)}
				<span
					class="hub"
					class:wpl={h.n.league === 'wpl'}
					style="left:{h.css.x.toFixed(1)}px; top:{h.css.y.toFixed(1)}px;"
				>
					{h.n.name}
				</span>
			{/each}
		</div>
	{/if}
{/if}

<style>
	.web {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: visible;
	}

	.strand {
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.strand.hero {
		filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.35));
	}

	.node {
		fill: rgba(232, 236, 245, 0.55);
	}

	.node.wpl {
		fill: var(--teal);
	}

	.knot {
		fill: #fff;
		stroke: #0b0e14;
		stroke-width: 1.5;
	}

	.knot-pulse {
		fill: none;
		stroke: #fff;
		stroke-width: 2;
		transform-box: fill-box;
		transform-origin: center;
		animation: knotpulse 1.8s ease-out infinite;
	}

	@keyframes knotpulse {
		0% {
			r: 5;
			opacity: 0.7;
		}
		100% {
			r: 16;
			opacity: 0;
		}
	}

	.leader {
		stroke: rgba(232, 236, 245, 0.6);
		stroke-width: 1;
		vector-effect: non-scaling-stroke;
	}

	.hit {
		stroke: transparent;
		stroke-width: 14;
		pointer-events: stroke;
		cursor: pointer;
	}

	.node-hit {
		fill: transparent;
		pointer-events: fill;
		cursor: pointer;
	}

	.hero-label {
		position: absolute;
		transform: translateY(-50%);
		white-space: nowrap;
		font-size: 0.74rem;
		font-weight: 600;
		color: var(--ink);
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
		pointer-events: none;
	}

	.hero-label.flip {
		transform: translate(-100%, -50%);
	}

	.hero-label strong {
		font-weight: 800;
	}

	.hubs {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.hub {
		position: absolute;
		transform: translate(-50%, -140%);
		white-space: nowrap;
		font-size: 0.66rem;
		font-weight: 700;
		color: var(--ink);
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
	}

	.hub.wpl {
		color: var(--teal);
	}

	@media (prefers-reduced-motion: reduce) {
		.knot-pulse {
			animation: none;
			display: none;
		}
	}
</style>
