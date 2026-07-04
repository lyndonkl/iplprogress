<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { sketch, footnotesOpen, type SketchBranch } from '$lib/state';
	import { loadColdOpenData, type ColdOpenData } from './data';

	/**
	 * CO-1 (the draw) + CO-2 (the reveal) — storyboard §1. The reader stakes a
	 * belief by drawing 200+ totals per season for 2013–2026 over a pre-drawn
	 * 2008–2012 anchor (11, 1, 9, 5, 5), then the truth line draws itself and
	 * the divergence is shaded per season and quantified in totals. "Just show
	 * me" is an equal-weight skip; nobody is ever gated on drawing. The field
	 * stays unborn behind this scene (2D moment; render loop stopped).
	 */
	let { progress, reduced }: SceneAnnotationProps = $props();

	/* ---- chart constants (storyboard CO-1: axes are spec) ------------------- */
	const N_SEASONS = 19; // 2008..2026
	const PRE_SEASONS = 5; // 2008..2012 pre-drawn
	const DRAW_SEASONS = 14; // 2013..2026
	const Y_MAX = 80;
	const GRID = [0, 20, 40, 60, 80];
	const GAP_SHADE_MIN = 8; // per-season |truth − sketch| ≥ 8 shades (CO-2)
	const M = { top: 34, right: 18, bottom: 30, left: 14 };

	/* ---- data (pipeline artifact; storyboard §9 constants as fallback) ------ */
	let data = $state<ColdOpenData | null>(null);

	const totals = $derived(data?.iplTotals200 ?? null);
	/** the pre-drawn 2008–2012 ink (5 seasons) */
	const preDrawn = $derived(totals ? totals.slice(0, PRE_SEASONS) : null);
	/** the truth the reader draws against: 2013–2026 (14 seasons) */
	const truth = $derived(totals ? totals.slice(PRE_SEASONS) : null);
	const truthEnd = $derived(truth ? truth[truth.length - 1] : 65);
	const truthSum1322 = $derived(
		truth ? truth.slice(0, 10).reduce((a, b) => a + b, 0) : 102
	);
	const firstSeason = $derived(data?.firstSeason ?? 2008);
	const matchesFmt = $derived((data?.corpus.matches ?? 1331).toLocaleString('en-US'));

	/* ---- draw state ---------------------------------------------------------- */
	let phase = $state<'draw' | 'revealing' | 'done'>('draw');
	let skipped = $state(false);
	let values = $state<(number | null)[]>(Array.from({ length: DRAW_SEASONS }, () => null));
	let branch = $state<SketchBranch | null>(null);
	/** seasons of truth revealed past 2012 (0..14) */
	let truthT = $state(0);
	let flashMsg = $state(false);

	let w = $state(0);
	let h = $state(0);
	let chipH = $state(0);
	let svgEl: SVGSVGElement | undefined = $state();

	const canReveal = $derived(values[DRAW_SEASONS - 1] !== null);

	/* ---- geometry ------------------------------------------------------------ */
	const plotW = $derived(Math.max(1, w - M.left - M.right));
	const plotH = $derived(Math.max(1, h - M.top - M.bottom));
	const xAt = (i: number): number => M.left + (i / (N_SEASONS - 1)) * plotW;
	const yAt = (v: number): number => M.top + (1 - v / Y_MAX) * plotH;

	/** x ticks: 2008/2013/2019/2023/2026 on mobile, all seasons on desktop */
	const tickIdxs = $derived(
		w < 640 ? [0, 5, 11, 15, 18] : Array.from({ length: N_SEASONS }, (_, i) => i)
	);

	const preDrawnPts = $derived.by(() => {
		if (!preDrawn) return '';
		return preDrawn.map((v, i) => `${xAt(i)},${yAt(v)}`).join(' ');
	});

	const readerPts = $derived.by(() => {
		if (!preDrawn) return '';
		const pts: string[] = [];
		for (let k = 0; k < DRAW_SEASONS; k++) {
			const v = values[k];
			if (v !== null) pts.push(`${xAt(PRE_SEASONS + k)},${yAt(v)}`);
		}
		if (pts.length === 0) return '';
		// the reader's line continues the pre-drawn ink from the 2012 point
		return `${xAt(PRE_SEASONS - 1)},${yAt(preDrawn[PRE_SEASONS - 1])} ${pts.join(' ')}`;
	});

	const truthPts = $derived.by(() => {
		if (!truth || !preDrawn || truthT <= 0) return '';
		const anchor = preDrawn[PRE_SEASONS - 1];
		const pts = [`${xAt(PRE_SEASONS - 1)},${yAt(anchor)}`];
		const whole = Math.min(DRAW_SEASONS, Math.floor(truthT));
		for (let k = 1; k <= whole; k++) pts.push(`${xAt(PRE_SEASONS - 1 + k)},${yAt(truth[k - 1])}`);
		const frac = truthT - whole;
		if (frac > 0 && whole < DRAW_SEASONS) {
			const v0 = whole === 0 ? anchor : truth[whole - 1];
			const v1 = truth[whole];
			const i0 = PRE_SEASONS - 1 + whole;
			const x = xAt(i0) + frac * (xAt(i0 + 1) - xAt(i0));
			pts.push(`${x},${yAt(v0 + frac * (v1 - v0))}`);
		}
		return pts.join(' ');
	});

	interface Band {
		x: number;
		y: number;
		bw: number;
		bh: number;
	}

	/** CO-2 gap shading: a per-season test, never "from the first miss onward". */
	const bands = $derived.by((): Band[] => {
		if (!truth || skipped || phase === 'draw') return [];
		const step = plotW / (N_SEASONS - 1);
		const out: Band[] = [];
		for (let k = 0; k < DRAW_SEASONS; k++) {
			if (truthT < k + 1) break;
			const v = values[k];
			if (v === null || Math.abs(truth[k] - v) < GAP_SHADE_MIN) continue;
			const yTopPx = yAt(Math.max(truth[k], v));
			const yBotPx = yAt(Math.min(truth[k], v));
			out.push({ x: xAt(PRE_SEASONS + k) - step * 0.33, y: yTopPx, bw: step * 0.66, bh: yBotPx - yTopPx });
		}
		return out;
	});

	/** pick-up-the-pen handle at the 2013 column (hidden once drawing starts) */
	const handleVisible = $derived(phase === 'draw' && values.every((v) => v === null));

	/* ---- branch math (storyboard CO-2 — first-match precedence) -------------- */
	const y26 = $derived(values[DRAW_SEASONS - 1] ?? 0);
	const sketchSum1322 = $derived.by(() => {
		let s = 0;
		for (let k = 0; k < 10; k++) s += values[k] ?? 0;
		return s;
	});
	const dBar = $derived(sketchSum1322 / 10);
	const gentleFloodEarly = $derived(branch === 'gentle' && dBar > 20);

	function computeBranch(vals: number[]): SketchBranch {
		const end = vals[DRAW_SEASONS - 1];
		const mean = vals.slice(0, 10).reduce((a, b) => a + b, 0) / 10;
		// first-match order is spec: over → early → right → gentle
		if (end > 77) return 'over';
		if (end >= 53 && mean > 20) return 'early';
		if (end >= 53 && end <= 77) return 'right';
		return 'gentle';
	}

	/* ---- pointer drawing ------------------------------------------------------ */
	let drawing = false;
	let last: { idx: number; v: number } | null = null;

	function samplePoint(e: PointerEvent): { idx: number; v: number } {
		const rect = svgEl!.getBoundingClientRect();
		const px = e.clientX - rect.left;
		const py = e.clientY - rect.top;
		const step = plotW / (N_SEASONS - 1);
		const idx = Math.min(N_SEASONS - 1, Math.max(PRE_SEASONS, Math.round((px - M.left) / step)));
		const v = Math.min(Y_MAX, Math.max(0, Math.round((1 - (py - M.top) / plotH) * Y_MAX)));
		return { idx, v };
	}

	function applySample(s: { idx: number; v: number }): void {
		// fast drags interpolate across skipped columns; values snap to integers
		if (last && Math.abs(s.idx - last.idx) > 1) {
			const dir = s.idx > last.idx ? 1 : -1;
			for (let i = last.idx + dir; i !== s.idx; i += dir) {
				const t = (i - last.idx) / (s.idx - last.idx);
				values[i - PRE_SEASONS] = Math.round(last.v + t * (s.v - last.v));
			}
		}
		values[s.idx - PRE_SEASONS] = s.v;
		last = s;
	}

	function onPointerDown(e: PointerEvent): void {
		if (phase === 'revealing') {
			finishReveal(); // tap anywhere skips the reveal animation
			return;
		}
		if (phase !== 'draw' || !svgEl) return;
		svgEl.setPointerCapture(e.pointerId);
		drawing = true;
		last = null; // re-touching continues from any column (no join-up line)
		applySample(samplePoint(e));
		e.preventDefault();
	}

	function onPointerMove(e: PointerEvent): void {
		if (!drawing || phase !== 'draw') return;
		applySample(samplePoint(e));
	}

	function onPointerUp(): void {
		drawing = false;
		last = null;
	}

	/* ---- reveal / skip -------------------------------------------------------- */
	let raf = 0;
	let revealStartProgress = 0;
	let flashTimer: ReturnType<typeof setTimeout> | undefined;

	/** unfilled columns interpolate linearly on submit; the lead anchors on 2012 */
	function finalized(): number[] {
		const out = values.slice();
		let prevIdx = -1;
		let prevVal = preDrawn ? preDrawn[PRE_SEASONS - 1] : 5;
		for (let i = 0; i < DRAW_SEASONS; i++) {
			const cur = out[i];
			if (cur === null) continue;
			if (i - prevIdx > 1) {
				for (let j = prevIdx + 1; j < i; j++) {
					const t = (j - prevIdx) / (i - prevIdx);
					out[j] = Math.round(prevVal + t * (cur - prevVal));
				}
			}
			prevIdx = i;
			prevVal = cur;
		}
		return out as number[];
	}

	function onReveal(): void {
		if (phase !== 'draw') return;
		if (!canReveal) {
			// feedback, never a dead control (storyboard CO-1)
			flashMsg = true;
			clearTimeout(flashTimer);
			flashTimer = setTimeout(() => (flashMsg = false), 2400);
			return;
		}
		const vals = finalized();
		for (let i = 0; i < DRAW_SEASONS; i++) values[i] = vals[i];
		branch = computeBranch(vals);
		skipped = false;
		sketch.set({ skipped: false, values: vals, branch, ts: Date.now() });
		startReveal();
	}

	function onJustShow(): void {
		if (phase !== 'draw') return;
		skipped = true;
		branch = null;
		sketch.set({ skipped: true, values: null, branch: null, ts: Date.now() });
		truthT = DRAW_SEASONS; // truth fully drawn, no branch copy, no gap shading
		phase = 'done';
	}

	function startReveal(): void {
		if (reduced) {
			// reduced motion: the end state, instantly (storyboard CO-2)
			truthT = DRAW_SEASONS;
			phase = 'done';
			return;
		}
		phase = 'revealing';
		revealStartProgress = progress;
		const t0 = performance.now();
		const tick = (now: number): void => {
			truthT = Math.min(DRAW_SEASONS, (now - t0) / 400); // ~400ms per season
			if (truthT >= DRAW_SEASONS) {
				phase = 'done';
				raf = 0;
				return;
			}
			raf = requestAnimationFrame(tick);
		};
		raf = requestAnimationFrame(tick);
	}

	function finishReveal(): void {
		if (raf) cancelAnimationFrame(raf);
		raf = 0;
		truthT = DRAW_SEASONS;
		if (phase === 'revealing') phase = 'done';
	}

	// scrolling past the reveal completes it instantly (storyboard CO-2)
	$effect(() => {
		if (phase === 'revealing' && Math.abs(progress - revealStartProgress) > 0.02) finishReveal();
	});

	// CO-2 auto-resolve (finding #6): a reader who scrolls past the draw without
	// tapping Reveal OR Just-show-me still gets the truth line + the universal
	// bridge — the cold open's beat is never lost behind a tap (CONTRACT §8.3:
	// interaction adds depth, never carries a beat). The buttons stay the
	// primary path; this only fires once the reader has clearly scrolled on.
	$effect(() => {
		if (phase === 'draw' && progress > 0.85) onJustShow();
	});

	onMount(() => {
		void loadColdOpenData().then((d) => (data = d));
		// returning reader with a real sketch: restore it (their reveal stands;
		// re-skipping can never clobber a drawn sketch by accident)
		const s = get(sketch);
		if (s && !s.skipped && s.values && s.values.length === DRAW_SEASONS) {
			for (let i = 0; i < DRAW_SEASONS; i++)
				values[i] = Math.min(Y_MAX, Math.max(0, Math.round(s.values[i])));
			branch = s.branch ?? computeBranch(values as number[]);
			skipped = false;
			truthT = DRAW_SEASONS;
			phase = 'done';
		}
		return () => {
			if (raf) cancelAnimationFrame(raf);
			clearTimeout(flashTimer);
		};
	});

	/* ---- chip placement (docks to the top when the sketch crowds it) --------- */
	const chipTop = $derived.by(() => {
		if (!truth) return 8;
		const yT = yAt(truthEnd);
		const yS = yAt(Math.min(Y_MAX, y26));
		return Math.max(8, Math.min(yT, yS) - chipH - 12);
	});
	const chipDocked = $derived(chipTop <= 8);
	const tetherH = $derived(Math.max(0, yAt(truthEnd) - chipH - 22));
</script>

<div class="pin">
	<div class="stars" aria-hidden="true"></div>

	<div class="draw-screen">
		<div class="prompt scene-card interactive">
			<p class="ask"><strong>How many times a season does someone put 200 on the board?</strong></p>
			<p class="sub">We’ve drawn 2008–2012 for you. You draw the rest.</p>
		</div>

		<div class="chart interactive" bind:clientWidth={w} bind:clientHeight={h}>
			<p class="sr-only">
				A chart of 200-run innings per season, 2008 to 2026. The drawing interaction is
				pointer-only — choose “Just show me” below to see the answer.
			</p>

			{#if w > 0 && totals && preDrawn && truth}
				<svg
					bind:this={svgEl}
					width={w}
					height={h}
					aria-hidden="true"
					class="plot"
					class:drawable={phase === 'draw'}
					onpointerdown={onPointerDown}
					onpointermove={onPointerMove}
					onpointerup={onPointerUp}
					onpointercancel={onPointerUp}
				>
					<!-- gridlines, labels inside the plot area (mobile-first) -->
					{#each GRID as g (g)}
						<line x1={M.left} x2={w - M.right} y1={yAt(g)} y2={yAt(g)} class="grid" />
						{#if g > 0}
							<text x={M.left + 3} y={yAt(g) - 4} class="grid-label">{g}</text>
						{/if}
					{/each}
					<text x={M.left + 3} y={16} class="axis-title">200-run innings per season</text>

					{#each tickIdxs as i (i)}
						<text x={xAt(i)} y={h - 8} class="tick">{firstSeason + i}</text>
					{/each}

					<!-- per-season divergence shading (CO-2) -->
					{#each bands as b, bi (bi)}
						<rect x={b.x} y={b.y} width={b.bw} height={b.bh} class="band" />
					{/each}

					<!-- pre-drawn 2008–2012 ink anchor -->
					<polyline points={preDrawnPts} class="ink pre" />

					<!-- the reader's line, same ink (they picked up the pen) -->
					{#if readerPts}
						<polyline points={readerPts} class="ink reader" />
					{/if}

					<!-- the truth (CO-2 reveal) -->
					{#if truthPts}
						<polyline points={truthPts} class="truth" />
					{/if}

					<!-- pick-up-the-pen handle at the 2013 column -->
					{#if handleVisible}
						<g class="handle" transform="translate({xAt(PRE_SEASONS)}, {yAt(preDrawn[PRE_SEASONS - 1])})">
							<circle r="14" class="halo" />
							<circle r="6" class="dot" />
						</g>
					{/if}
				</svg>

				<!-- anchor chip on the pre-drawn segment -->
				{#if phase === 'draw'}
					<div class="anchor-chip" style:left="{M.left + 4}px" style:top="{yAt(14) - 54}px">
						2008–2012: about six a season.<br />That much we’ll give you.
					</div>
				{/if}

				<!-- branch chip (CO-2) -->
				{#if phase === 'done' && !skipped && branch}
					{#if chipDocked && tetherH > 16}
						<div class="tether" style:left="{xAt(N_SEASONS - 1) - 1}px" style:top="{chipH + 14}px" style:height="{tetherH}px"></div>
					{/if}
					<div class="chip" role="status" bind:clientHeight={chipH} style:top="{chipTop}px">
						{#if branch === 'over'}
							<p>
								<strong>You out-dreamed it — barely.</strong> 2026 alone put up
								<strong>{truthEnd}</strong> two-hundreds, more than any season in history. Your
								line: <strong>{y26}</strong>.
							</p>
						{:else if branch === 'early'}
							<p>
								<strong>You called the flood — but rang the bell early.</strong> From 2013 to 2022
								you imagined <strong>{sketchSum1322}</strong> two-hundreds; the league managed
								<strong>{truthSum1322}</strong>. Then 2023 happened.
							</p>
						{:else if branch === 'right'}
							<p>
								<strong>You knew.</strong> But do you know <strong>when</strong> it broke? The eye
								says <strong>2018</strong> — the year the sixes exploded. The scoreboard says
								<strong>2023</strong>.
							</p>
						{:else if gentleFloodEarly}
							<p>
								<strong>You imagined the flood early — then lost your nerve.</strong> The real
								2026: <strong>{truthEnd}</strong>.
							</p>
						{:else}
							<p>
								<strong>You were {truthEnd - y26} two-hundreds too gentle about 2026.</strong> The
								real number: <strong>{truthEnd}</strong>. For fifteen years you’d have been right —
								then the ceiling broke.
							</p>
						{/if}
					</div>
				{/if}
			{/if}
		</div>

		{#if phase === 'draw'}
			<div class="controls interactive">
				<div class="buttons">
					<!-- DOM order: Just-show-me is the first focusable control (CO-1);
					     visual order (Reveal first) is restored with flex direction -->
					<button class="btn" class:emphasis={reduced} onclick={onJustShow}>Just show me</button>
					<button class="btn" class:dimmed={!canReveal} aria-disabled={!canReveal} onclick={onReveal}>
						Reveal
					</button>
				</div>
				{#if flashMsg}
					<p class="flash" role="status">Draw to 2026 first.</p>
				{/if}
			</div>
		{:else if phase === 'done'}
			<div class="bridge">
				<p><strong>Nineteen seasons. {matchesFmt} matches. Here comes every ball of it.</strong></p>
				<div class="cue" aria-hidden="true">↓</div>
			</div>
		{/if}

		<!-- footnote ⓘ on the prompt (storyboard CO-1). LAST in DOM so [Just show
		     me] is the first focusable control (finding #14); CSS pins it back to
		     the prompt's top-right corner. -->
		<button
			class="info prompt-info"
			onclick={() => footnotesOpen.set('draw-200')}
			aria-haspopup="dialog"
			aria-label="How a 200-run innings is counted"
		>
			ⓘ
		</button>
	</div>
</div>

<style>
	.pin {
		position: sticky;
		top: 0;
		height: 100vh;
		height: 100dvh;
		overflow: hidden;
	}

	.stars {
		position: absolute;
		inset: 0;
		background-image:
			radial-gradient(1.2px 1.2px at 22% 18%, rgba(232, 236, 245, 0.4), transparent 60%),
			radial-gradient(1px 1px at 70% 9%, rgba(232, 236, 245, 0.3), transparent 60%),
			radial-gradient(1.4px 1.4px at 88% 66%, rgba(232, 236, 245, 0.26), transparent 60%),
			radial-gradient(1px 1px at 34% 82%, rgba(232, 236, 245, 0.3), transparent 60%),
			radial-gradient(1px 1px at 6% 48%, rgba(232, 236, 245, 0.22), transparent 60%);
		background-size:
			280px 260px,
			340px 300px,
			420px 380px,
			360px 320px,
			300px 340px;
		background-repeat: repeat;
		opacity: 0.4;
	}

	.draw-screen {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		gap: 10px;
		max-width: 780px;
		margin: 0 auto;
		padding: max(12px, env(safe-area-inset-top)) 14px max(12px, env(safe-area-inset-bottom));
	}

	.prompt {
		max-width: none;
		padding: 0.85rem 1.1rem;
	}

	.prompt .ask {
		font-size: clamp(1.05rem, 2.8vw, 1.3rem);
		line-height: 1.35;
		/* reserve the top-right corner for the absolutely-placed ⓘ */
		padding-right: 1.9rem;
	}

	.prompt .sub {
		margin-top: 0.3rem;
		font-size: clamp(0.9rem, 2.3vw, 1rem);
		color: var(--ink-dim);
	}

	.info {
		display: inline-grid;
		place-content: center;
		min-width: 44px;
		min-height: 44px;
		margin: -12px -6px;
		padding: 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 1rem;
		cursor: pointer;
		vertical-align: middle;
	}

	.info:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
		border-radius: 8px;
	}

	/* moved LAST in DOM (finding #14: [Just show me] first-focusable); pinned
	   back to the prompt card's top-right corner. .draw-screen is the positioned
	   ancestor and its padding matches these offsets, so this lands on the card
	   edge on every viewport. */
	.prompt-info {
		position: absolute;
		top: max(12px, env(safe-area-inset-top));
		right: 14px;
		margin: 0;
		z-index: 2;
	}

	.chart {
		position: relative;
		height: min(55vh, 480px);
		flex: none;
		pointer-events: auto;
		border: 1px solid rgba(232, 236, 245, 0.08);
		border-radius: 12px;
		background: rgba(11, 14, 20, 0.45);
	}

	.plot {
		display: block;
		border-radius: 12px;
	}

	.plot.drawable {
		touch-action: none; /* the canvas is the pen surface */
		cursor: crosshair;
	}

	.grid {
		stroke: rgba(232, 236, 245, 0.1);
		stroke-width: 1;
	}

	.grid-label,
	.tick,
	.axis-title {
		fill: var(--ink-dim);
		font-size: 10px;
		font-variant-numeric: tabular-nums;
	}

	.axis-title {
		font-size: 11px;
		letter-spacing: 0.06em;
		fill: var(--ink);
		opacity: 0.85;
	}

	.tick {
		text-anchor: middle;
	}

	.band {
		fill: rgba(255, 93, 58, 0.16);
	}

	.ink {
		fill: none;
		stroke: var(--ink);
		stroke-width: 2;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	.ink.pre {
		opacity: 0.9;
	}

	.ink.reader {
		opacity: 0.95;
	}

	.truth {
		fill: none;
		stroke: var(--ember);
		stroke-width: 2.5;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	.handle .halo {
		fill: none;
		stroke: rgba(232, 236, 245, 0.55);
		stroke-width: 1.5;
		animation: pulse 1.6s ease-in-out infinite;
		transform-box: fill-box;
		transform-origin: center;
	}

	.handle .dot {
		fill: var(--ink);
	}

	@keyframes pulse {
		0%,
		100% {
			transform: scale(0.72);
			opacity: 0.9;
		}
		50% {
			transform: scale(1.15);
			opacity: 0.35;
		}
	}

	.anchor-chip {
		position: absolute;
		font-size: 0.72rem;
		line-height: 1.35;
		color: var(--ink-dim);
		background: rgba(11, 14, 20, 0.7);
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 8px;
		padding: 5px 8px;
		pointer-events: none;
		max-width: 180px;
	}

	.chip {
		position: absolute;
		right: 10px;
		max-width: min(320px, 78%);
		background: rgba(11, 14, 20, 0.82);
		border: 1px solid rgba(232, 236, 245, 0.14);
		border-radius: 10px;
		padding: 0.7rem 0.9rem;
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
		font-variant-numeric: tabular-nums;
	}

	.chip p {
		margin: 0;
		font-size: clamp(0.88rem, 2.3vw, 1rem);
		line-height: 1.45;
	}

	.tether {
		position: absolute;
		width: 1px;
		background: rgba(232, 236, 245, 0.3);
		pointer-events: none;
	}

	.controls {
		pointer-events: auto;
	}

	.buttons {
		display: flex;
		flex-direction: column-reverse; /* Reveal renders above Just-show-me */
		gap: 10px;
	}

	.btn {
		min-height: 48px;
		padding: 0.65rem 1.4rem;
		border-radius: 12px;
		border: 1px solid rgba(232, 236, 245, 0.25);
		background: rgba(232, 236, 245, 0.08);
		color: var(--ink);
		font-size: 1rem;
		font-weight: 650;
		letter-spacing: 0.02em;
		cursor: pointer;
		width: 100%;
	}

	.btn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.btn.dimmed {
		opacity: 0.55;
	}

	.btn.emphasis {
		border-color: var(--teal);
	}

	.flash {
		margin: 8px 0 0;
		font-size: 0.85rem;
		color: var(--gold);
		text-align: center;
	}

	.bridge {
		text-align: center;
		padding: 0.4rem 1rem 0;
	}

	.bridge p {
		margin: 0;
		font-size: clamp(1.05rem, 2.8vw, 1.3rem);
		font-variant-numeric: tabular-nums;
	}

	.cue {
		margin-top: 0.5rem;
		font-size: 1.2rem;
		color: var(--ink-dim);
		animation: bounce 1.8s ease-in-out infinite;
	}

	@keyframes bounce {
		0%,
		100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(7px);
		}
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		margin: -1px;
		padding: 0;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
		border: 0;
	}

	@media (min-width: 641px) {
		.buttons {
			flex-direction: row-reverse; /* Reveal left, Just-show-me right */
			justify-content: center;
		}

		.btn {
			width: auto;
			min-width: 200px;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.handle .halo,
		.cue {
			animation: none;
		}
	}
</style>
