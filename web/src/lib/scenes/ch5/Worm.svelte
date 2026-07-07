<script lang="ts">
	import { RAIL_SLOTS, win100, type ScrubBall } from './data';

	/**
	 * The WORM — the chapter's teaching image (C5-2 / C5-3). One line whose
	 * height is how often the chasing side wins from that exact spot, out of a
	 * hundred. Anchors: the state BEFORE ball 1, then AFTER each ball, x-aligned
	 * under the rail slots so the line and the chips agree by construction.
	 * ONE series only (design audit): the storyboard's worm spec carries no
	 * second mark in main flow, so the raw observed-outcome counts live one
	 * click deep in the ch5-over footnote instead of as hover-glossed hollow
	 * dots (hover-only content is a hard invariant violation). All values come
	 * from scenes/ch5.json — the grid can hold FLAT between balls (the table
	 * buckets the ask) and the flat steps are kept, never smoothed for drama.
	 *
	 * At reveal 0 (the C5-2 ghost stub) the start anchor PULSES and carries its
	 * live "wins in 100" label, so the orientation caption's number has a
	 * visual anchor before the scrub begins (CSS honours reduced motion).
	 *
	 * SVG viewBox 0 0 100 100, preserveAspectRatio="none": x = viewport fraction
	 * × 100 (matching the chips' percentage anchors), y = 100 − wins-in-100.
	 */
	let {
		balls,
		reveal = 6,
		bright = false
	}: { balls: ScrubBall[]; reveal?: number; bright?: boolean } = $props();

	/** x (0..100) of the worm anchor AFTER ball i (1-based); 0 = the start. */
	const ax = (i: number): number =>
		i === 0 ? (RAIL_SLOTS[0][0] - 0.09) * 100 : RAIL_SLOTS[i - 1][0] * 100;
	const ay = (wp: number): number => (1 - wp) * 100;

	/** the 7 anchors: wp before ball 1, then wp after balls 1..6 */
	const anchors = $derived.by(() => {
		if (balls.length === 0) return [] as { x: number; y: number; wp: number }[];
		const out = [{ x: ax(0), y: ay(balls[0].wp_before), wp: balls[0].wp_before }];
		balls.forEach((b, i) => out.push({ x: ax(i + 1), y: ay(b.wp_after), wp: b.wp_after }));
		return out;
	});

	/** polyline points up to the fractional reveal (0..6 balls drawn) */
	const points = $derived.by(() => {
		const a = anchors;
		if (a.length === 0) return '';
		const full = Math.min(6, Math.floor(reveal));
		const pts: string[] = [];
		for (let i = 0; i <= full; i++) pts.push(`${a[i].x},${a[i].y}`);
		const frac = reveal - full;
		if (full < 6 && frac > 0) {
			const p = a[full];
			const q = a[full + 1];
			pts.push(`${p.x + (q.x - p.x) * frac},${p.y + (q.y - p.y) * frac}`);
		}
		return pts.join(' ');
	});

	const playedCount = $derived(Math.min(6, Math.floor(reveal)));
	const liveWp = $derived.by(() => {
		const a = anchors;
		if (a.length === 0) return null;
		return a[Math.min(6, Math.max(0, Math.round(reveal)))].wp;
	});
</script>

<div class="worm-box" aria-hidden="true">
	<svg viewBox="0 0 100 100" preserveAspectRatio="none">
		<!-- the 0 / 50 / 100 grid rules -->
		<line class="rule" x1="2" y1="0" x2="98" y2="0" />
		<line class="rule mid" x1="2" y1="50" x2="98" y2="50" />
		<line class="rule" x1="2" y1="100" x2="98" y2="100" />
		{#if points}
			<polyline class="worm" class:bright points={points} />
		{/if}
		<!-- the anchors (one series only — the observed counts are footnote depth) -->
		{#each anchors as a, i (i)}
			{#if i <= reveal + 1e-6 && (i === 0 || i <= playedCount)}
				<circle class="anchor" class:pulse={i === 0 && reveal === 0} cx={a.x} cy={a.y} r="0.9" />
			{/if}
		{/each}
	</svg>

	<!-- axis labels (0 / 50 / 100 only) + the axis title -->
	<span class="tick t100">100</span>
	<span class="tick t50">50</span>
	<span class="tick t0">0</span>
	<span class="axis-title">wins in 100 from here, for the chasing side</span>

	{#if liveWp !== null}
		<span
			class="live"
			style="left: {anchors[Math.min(6, Math.max(0, Math.round(reveal)))].x}%; top: {anchors[
				Math.min(6, Math.max(0, Math.round(reveal)))
			].y}%;"
		>
			{win100(liveWp)}
		</span>
	{/if}
</div>

<style>
	.worm-box {
		position: absolute;
		left: 0;
		right: 0;
		top: 56vh;
		height: 24vh;
		pointer-events: none;
	}

	svg {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		overflow: visible;
	}

	.rule {
		stroke: rgba(151, 161, 184, 0.22);
		stroke-width: 0.5;
		vector-effect: non-scaling-stroke;
	}

	.rule.mid {
		stroke-dasharray: 3 4;
	}

	.worm {
		fill: none;
		stroke: #ffd166;
		stroke-width: 2.4;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
		filter: drop-shadow(0 0 6px rgba(255, 209, 102, 0.45));
	}

	.worm.bright {
		stroke-width: 3.2;
		filter: drop-shadow(0 0 10px rgba(255, 209, 102, 0.7));
	}

	.anchor {
		fill: #ffd166;
	}

	/* the C5-2 ghost-stub start anchor breathes so the caption's start value
	   has a visual anchor; stilled for reduced-motion readers */
	.anchor.pulse {
		transform-box: fill-box;
		transform-origin: center;
		animation: worm-pulse 1.6s ease-in-out infinite;
	}

	@keyframes worm-pulse {
		0%,
		100% {
			transform: scale(1);
			opacity: 1;
		}
		50% {
			transform: scale(1.9);
			opacity: 0.55;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.anchor.pulse {
			animation: none;
		}
	}

	.tick {
		position: absolute;
		left: 0.6%;
		font-size: 10px;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		transform: translateY(-50%);
	}

	.t100 {
		top: 0;
	}

	.t50 {
		top: 50%;
	}

	.t0 {
		top: 100%;
	}

	.axis-title {
		position: absolute;
		left: 2%;
		top: calc(100% + 12px);
		font-size: 10.5px;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--ink-dim);
		white-space: nowrap;
	}

	.live {
		position: absolute;
		transform: translate(10px, -50%);
		font-size: 15px;
		font-weight: 800;
		color: #ffd166;
		font-variant-numeric: tabular-nums;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
	}

	@media (max-width: 640px) {
		.worm-box {
			top: 54vh;
			height: 16vh;
		}

		.axis-title {
			font-size: 9px;
		}
	}

	/* short phones: shrink the worm band so the axis title clears the
	   bottom-anchored caption card (the rail above pins the worm's top) */
	@media (max-width: 640px) and (max-height: 568px) {
		.worm-box {
			height: 10vh;
		}
	}
</style>
