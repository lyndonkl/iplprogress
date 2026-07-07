<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import type { ConstellationPhase } from '$lib/field/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import {
		loadCh6Data,
		phaseGlide,
		PHASE_BOUNDS,
		PHASE_SHORT,
		PHASE_OVERS,
		PHASE_LABEL,
		PHASE_TARGET,
		type Ch6Data
	} from './data';
	import { pickCaptionCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';
	import Starfield from './Starfield.svelte';

	/**
	 * C6-4 — THE PHASE TOGGLE (a star-table swap over the HELD map, NOT a re-sort,
	 * NOT a second morph — CONTRACT §22.3). The constellation stays; only the 23
	 * star centres glide between the four precomputed, Procrustes-aligned per-phase
	 * embeddings. The point-to-star assignment never changes, so each season's disc
	 * translates rigidly and the WPL never crosses the men's worm — the Procrustes
	 * lock is why a browser must never re-embed (§22.2). The WPL dotted threads
	 * redraw per phase (the nearest men's lookalike shifts), and every one still
	 * lands on an early IPL season: the answer depends which phase you ask, but it
	 * is always the men's early years.
	 *
	 * The phase cycle is scroll-driven (phaseGlide — a pure function of progress,
	 * shared with index.ts's dynamicState so field and chip never disagree). Reduced
	 * motion renders the four phase twins as a static table (no glide).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const glide = $derived(phaseGlide(progress));
	const step = $derived(glide.step);
	const reveal = $derived(
		captionReveal(progress, PHASE_BOUNDS[step - 1], PHASE_BOUNDS[step], { reduced })
	);

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

	const PHASES: ConstellationPhase[] = ['all', 'powerplay', 'middle', 'death'];

	/** WPL 2026's nearest IPL twin per phase (from wpl_threads) — the "depends
	    which phase you ask" table, driving both the reduced fallback and the chip */
	const twinByPhase = $derived.by(() => {
		const d = ch6;
		const out: Record<ConstellationPhase, number> = {
			all: 2008,
			powerplay: 2008,
			middle: 2008,
			death: 2008
		};
		if (!d) return out;
		for (const p of PHASES) {
			const t = d.constellation.wpl_threads[p]?.find((x) => x.wpl_season === 2026);
			if (t) out[p] = t.nearest_ipl_season;
		}
		return out;
	});

	const shownPhase = $derived(glide.shown);
	const labelGis = $derived([0, 19, 20, 21, 22]);

	/* §0.4a caption safe-corner from the live star geometry (re-picks as the phase
	   glide moves the stars and on resize) */
	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => tick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	const capStyle = $derived.by(() => {
		void tick;
		void progress;
		if (isNarrowViewport() || !field) return '';
		return cornerStyle(pickCaptionCorner(field).corner);
	});

	/* the phase buttons drive the SAME scroll channel the glide reads: pressing one
	   scrolls the reader to that phase's hold point, so the field, chip and caption
	   all move together and a stray scroll can never desync them (§12.2 caveat).
	   Scroll stays the default driver; nobody is gated on tapping. The section is
	   found from the clicked button (robust; no bind:this dependency). */
	function goToPhase(e: MouseEvent, p: ConstellationPhase): void {
		const el = (e.target as HTMLElement) ?? null;
		const section = el?.closest('section.scene') as HTMLElement | null;
		if (!section) return;
		const top = section.getBoundingClientRect().top + window.scrollY;
		const target = Math.round(top + PHASE_TARGET[p] * section.offsetHeight);
		// jump the reader to that phase's hold point via the plain 2-arg scrollTo
		// (the object form's `smooth` is a no-op while html has overflow-x:hidden).
		// The field reads scroll progress, so the star table lands on the picked phase.
		window.scrollTo(0, target);
	}
</script>

<div class="pin" class:active>
	<Starfield
		{field}
		{reduced}
		{progress}
		on={true}
		threadPhase={shownPhase}
		showWorm={true}
		showThreads={true}
		{labelGis}
		legend={true}
		footnoteId="ch6-phase"
	/>

	<!-- the phase toggle: real keyboard buttons (scroll to a phase); scroll is the
	     default driver and lights the active chip -->
	<div class="phase-chips" aria-label="jump to a phase of the innings">
		{#each PHASES as p (p)}
			<button
				class="chip"
				class:on={reduced ? p === 'all' : shownPhase === p}
				aria-pressed={reduced ? p === 'all' : shownPhase === p}
				onclick={(e) => goToPhase(e, p)}
			>
				<span class="chip-lbl">{PHASE_SHORT[p]}</span>
				<span class="chip-gloss">{PHASE_OVERS[p]}</span>
			</button>
		{/each}
	</div>

	{#if reduced}
		<!-- reduced motion: the four twins as a static table (the whole point,
		     without any glide) -->
		<div class="twin-table">
			<span class="tt-head">the WPL's twin, by phase</span>
			{#each PHASES as p (p)}
				<div class="tt-row">
					<span class="tt-p">{PHASE_LABEL[p]}</span>
					<span class="tt-v">IPL {twinByPhase[p]}</span>
				</div>
			{/each}
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style="{capStyle}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>
					You can also ask this by phase of the innings. Right now every over is pooled together.
					Tap a phase, or just keep scrolling, and watch the whole map breathe. Nothing crosses
					sides.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Ask only about the first six overs, when the field is up. The WPL still lands nearest
					<strong>IPL {twinByPhase.powerplay}.</strong>
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					Ask about the middle overs and the threads drift a touch, to about
					<strong>IPL {twinByPhase.middle}.</strong> Still the men's early years, never the recent ones.
				</p>
			</div>
		{:else if step === 4}
			<div class="scene-card">
				<p>
					Ask about the death overs, the last five. The WPL swings back to
					<strong>IPL {twinByPhase.death}.</strong>
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					Whichever overs you ask about, the twin is always an early IPL season. And the WPL never
					once crosses onto the modern path. The map is built so it cannot.
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

	.phase-chips {
		position: absolute;
		left: 50%;
		top: 9vh;
		transform: translateX(-50%);
		display: flex;
		gap: 0.4rem;
	}

	.chip {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.1rem;
		min-height: 44px;
		padding: 0.35rem 0.7rem;
		border-radius: 12px;
		color: var(--ink-dim);
		background: rgba(10, 14, 24, 0.7);
		border: 1px solid rgba(151, 161, 184, 0.25);
		cursor: pointer;
	}

	.chip-lbl {
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.04em;
	}

	.chip-gloss {
		font-size: 0.58rem;
		color: var(--ink-dim);
		white-space: nowrap;
	}

	.chip.on {
		color: #0b0e14;
		background: #62d2c3;
		border-color: #62d2c3;
	}

	.chip.on .chip-gloss {
		color: rgba(11, 14, 20, 0.75);
	}

	.chip:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.twin-table {
		position: absolute;
		right: 4vw;
		top: 20vh;
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		padding: 0.75rem 0.95rem;
		border-radius: 14px;
		background: rgba(10, 14, 24, 0.85);
		border: 1px solid rgba(151, 161, 184, 0.3);
		max-width: 17rem;
		pointer-events: none;
	}

	.tt-head {
		font-size: 0.64rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: #62d2c3;
	}

	.tt-row {
		display: flex;
		justify-content: space-between;
		gap: 0.8rem;
		font-size: 0.82rem;
	}

	.tt-p {
		color: var(--ink-dim);
	}

	.tt-v {
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	/* desktop: positioned by the inline capStyle (§0.4a safe corner) */
	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 8vh;
		max-width: min(25rem, 40vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.phase-chips {
			top: 12vh;
		}

		.twin-table {
			right: 3vw;
			top: auto;
			bottom: 27vh;
			max-width: 60vw;
			padding: 0.55rem 0.7rem;
		}

		.caption-slot {
			right: auto;
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
