<script lang="ts">
	import { base } from '$app/paths';
	import { footnotesOpen } from '$lib/state';
	import { FOOTNOTES, isFootnoteId, type FootnoteFigure, type OverClockFigure } from './footnotes';
	import { lockScroll, unlockScroll } from './scrollLock';

	/**
	 * The footnote slide-over: bottom sheet on mobile, side panel on desktop.
	 * Pure DOM, tap- and keyboard-operable (blueprint §2: no hover-only
	 * content). Opens when the footnotesOpen store holds a registry id.
	 *
	 * Every sheet carries a persistent "Full methods →" footer (finding #7 —
	 * the progressive-disclosure chain reaches the methods page from any sheet,
	 * and it gives the focus trap a link to cycle). A footnote entry may also
	 * carry an optional static 2D figure (finding #16-1 — C1-4's over-clock
	 * radial), rendered below the prose. Opening the sheet locks background
	 * scroll (finding #18) so the field can't scrub underneath.
	 */

	let panelEl = $state<HTMLElement | null>(null);
	let lastFocused: Element | null = null;

	const entry = $derived(isFootnoteId($footnotesOpen) ? FOOTNOTES[$footnotesOpen] : null);
	// registry entries are `as const`; narrow to the ones carrying a figure and
	// widen the readonly literal to the mutable figure type for rendering
	const figure: FootnoteFigure | null = $derived(
		entry && 'figure' in entry ? ((entry.figure as FootnoteFigure) ?? null) : null
	);

	$effect(() => {
		if (entry && panelEl) {
			lastFocused = document.activeElement;
			panelEl.focus();
			lockScroll();
			return unlockScroll;
		} else if (!entry && lastFocused instanceof HTMLElement) {
			lastFocused.focus();
			lastFocused = null;
		}
	});

	function close(): void {
		footnotesOpen.set(null);
	}

	function onKeydown(e: KeyboardEvent): void {
		if (e.key === 'Escape') {
			e.stopPropagation();
			close();
			return;
		}
		if (e.key !== 'Tab' || !panelEl) return;
		// minimal focus trap: cycle within the panel
		const focusables = panelEl.querySelectorAll<HTMLElement>(
			'button, a[href], [tabindex]:not([tabindex="-1"])'
		);
		if (focusables.length === 0) return;
		const first = focusables[0];
		const last = focusables[focusables.length - 1];
		if (e.shiftKey && document.activeElement === first) {
			e.preventDefault();
			last.focus();
		} else if (!e.shiftKey && document.activeElement === last) {
			e.preventDefault();
			first.focus();
		}
	}

	/* ---- over-clock radial geometry (only verified balls are plotted) -------- */
	const RC = { cx: 110, cy: 100, R: 74 };
	const angleOf = (ball: number, balls: number): number =>
		((-90 + ((ball - 1) / balls) * 360) * Math.PI) / 180;

	interface RadialDot {
		x: number;
		y: number;
		lx: number;
		ly: number;
		rr: string;
		tone: 'ghost' | 'bold';
	}
	interface RadialSpoke {
		x2: number;
		y2: number;
		bx: number;
		by: number;
		ball: number;
	}

	const radial = $derived.by(() => {
		const f: OverClockFigure | null = figure && figure.kind === 'over-clock' ? figure : null;
		if (!f) return null;
		const spokes: RadialSpoke[] = [];
		for (let b = 1; b <= f.balls; b++) {
			const a = angleOf(b, f.balls);
			spokes.push({
				x2: RC.cx + RC.R * Math.cos(a),
				y2: RC.cy + RC.R * Math.sin(a),
				bx: RC.cx + (RC.R + 12) * Math.cos(a),
				by: RC.cy + (RC.R + 12) * Math.sin(a),
				ball: b
			});
		}
		const dots: RadialDot[] = [];
		for (const s of f.series) {
			for (const p of s.points) {
				const a = angleOf(p.ball, f.balls);
				const r = (p.rr / f.max) * RC.R;
				const x = RC.cx + r * Math.cos(a);
				const y = RC.cy + r * Math.sin(a);
				dots.push({
					x,
					y,
					lx: RC.cx + (r + 13) * Math.cos(a),
					ly: RC.cy + (r + 13) * Math.sin(a),
					rr: p.rr.toFixed(2),
					tone: s.tone
				});
			}
		}
		return { f, spokes, dots };
	});
</script>

{#if entry}
	<div class="scrim" onclick={close} aria-hidden="true"></div>
	<div
		class="panel"
		role="dialog"
		aria-modal="true"
		aria-labelledby="footnote-title"
		tabindex="-1"
		bind:this={panelEl}
		onkeydown={onKeydown}
	>
		<header>
			<p class="overline">How we computed this</p>
			<h2 id="footnote-title">{entry.title}</h2>
			<button class="close" onclick={close} aria-label="Close footnote">✕</button>
		</header>
		<div class="body">
			{#each entry.paragraphs as para (para)}
				<p>{para}</p>
			{/each}

			{#if radial}
				<figure class="over-clock">
					<svg viewBox="0 0 220 210" role="img" aria-label={radial.f.caption}>
						<circle cx={RC.cx} cy={RC.cy} r={RC.R} class="dial" />
						{#each radial.spokes as s (s.ball)}
							<line x1={RC.cx} y1={RC.cy} x2={s.x2} y2={s.y2} class="spoke" />
							<text x={s.bx} y={s.by} class="ball-lab">{s.ball}</text>
						{/each}
						{#each radial.dots as d, i (i)}
							<circle cx={d.x} cy={d.y} r="4.5" class="dot {d.tone}" />
							<text x={d.lx} y={d.ly} class="rr-lab {d.tone}">{d.rr}</text>
						{/each}
					</svg>
					<div class="legend">
						{#each radial.f.series as s (s.label)}
							<span class="key {s.tone}"><i></i>{s.label}</span>
						{/each}
					</div>
					<figcaption>{radial.f.caption}</figcaption>
				</figure>
			{/if}
		</div>
		<footer>
			<a href="{base}/methods/" class="methods">Full methods →</a>
		</footer>
	</div>
{/if}

<style>
	.scrim {
		position: fixed;
		inset: 0;
		z-index: 80;
		background: rgba(4, 6, 10, 0.55);
	}

	.panel {
		position: fixed;
		z-index: 81;
		background: #10141d;
		border: 1px solid rgba(232, 236, 245, 0.12);
		color: var(--ink);
		display: flex;
		flex-direction: column;
		outline: none;

		/* mobile: bottom sheet */
		left: 0;
		right: 0;
		bottom: 0;
		max-height: 78dvh;
		border-radius: 16px 16px 0 0;
	}

	@media (min-width: 720px) {
		/* desktop: right slide-over */
		.panel {
			left: auto;
			top: 0;
			bottom: 0;
			width: min(26rem, 90vw);
			max-height: none;
			border-radius: 0;
			border-right: none;
		}
	}

	header {
		position: relative;
		padding: 1.1rem 3rem 0.6rem 1.3rem;
		border-bottom: 1px solid rgba(232, 236, 245, 0.08);
	}

	.overline {
		margin: 0 0 0.3rem;
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.24em;
		text-transform: uppercase;
		color: var(--gold);
	}

	h2 {
		margin: 0 0 0.7rem;
		font-size: 1.15rem;
		line-height: 1.3;
	}

	.close {
		position: absolute;
		top: 0.9rem;
		right: 0.9rem;
		width: 44px;
		height: 44px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		border-radius: 10px;
		background: transparent;
		color: var(--ink);
		font-size: 1rem;
		cursor: pointer;
	}

	.close:focus-visible,
	.methods:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.body {
		padding: 1rem 1.3rem 1.4rem;
		overflow-y: auto;
		flex: 1 1 auto;
	}

	.body p {
		margin: 0 0 0.9rem;
		font-size: 0.95rem;
		line-height: 1.55;
		color: var(--ink);
	}

	/* ---- over-clock radial (a demoted, static 2D exhibit) ---- */
	.over-clock {
		margin: 0.4rem 0 0;
		padding: 0.9rem 0.6rem 0.4rem;
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 12px;
		background: rgba(4, 6, 10, 0.35);
	}

	.over-clock svg {
		display: block;
		width: min(220px, 70%);
		height: auto;
		margin: 0 auto;
	}

	.over-clock .dial {
		fill: none;
		stroke: rgba(232, 236, 245, 0.14);
		stroke-width: 1;
	}

	.over-clock .spoke {
		stroke: rgba(232, 236, 245, 0.09);
		stroke-width: 1;
	}

	.over-clock .ball-lab {
		font-size: 9px;
		fill: var(--ink-dim);
		text-anchor: middle;
		dominant-baseline: middle;
		font-variant-numeric: tabular-nums;
	}

	.over-clock .dot.ghost {
		fill: var(--ink-dim);
	}

	.over-clock .dot.bold {
		fill: var(--ember);
	}

	.over-clock .rr-lab {
		font-size: 10px;
		text-anchor: middle;
		dominant-baseline: middle;
		font-variant-numeric: tabular-nums;
		font-weight: 600;
	}

	.over-clock .rr-lab.ghost {
		fill: var(--ink-dim);
	}

	.over-clock .rr-lab.bold {
		fill: var(--ember);
	}

	.over-clock .legend {
		display: flex;
		justify-content: center;
		gap: 1.1rem;
		margin-top: 0.3rem;
	}

	.over-clock .key {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.75rem;
		color: var(--ink-dim);
	}

	.over-clock .key i {
		width: 10px;
		height: 10px;
		border-radius: 50%;
	}

	.over-clock .key.ghost i {
		background: var(--ink-dim);
	}

	.over-clock .key.bold i {
		background: var(--ember);
	}

	.over-clock figcaption {
		margin-top: 0.5rem;
		font-size: 0.8rem;
		line-height: 1.45;
		color: var(--ink-dim);
	}

	footer {
		flex: none;
		padding: 0.85rem 1.3rem calc(0.85rem + env(safe-area-inset-bottom));
		border-top: 1px solid rgba(232, 236, 245, 0.08);
		background: #0d1119;
	}

	.methods {
		color: var(--teal);
		font-size: 0.9rem;
		font-weight: 600;
		text-decoration: none;
	}
</style>
