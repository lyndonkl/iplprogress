<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * IN-1 — The pause (storyboard §1). Pure framing prose over the resting
	 * starfield: why the argument stops for a moment, and what the reader is
	 * about to get their hands on. No numbers on this scene. Per §0.3/§0.4 it does
	 * NOT use the mobile read-then-watch fade (there is nothing to watch behind
	 * pure text); the lines simply reveal as the reader scrolls and stay put
	 * (persistent), and under reduced motion all three are shown at once.
	 *
	 * Field: the shell holds `free` dimmed to a resting starfield, loop stopped —
	 * this component never touches `field`, so the GPU stays idle (demand mode).
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	// three lines, revealed in turn; once shown they never hide (persistent)
	const shown = $derived.by(() => {
		if (reduced) return 3;
		if (progress >= 0.5) return 3;
		if (progress >= 0.22) return 2;
		return 1;
	});
</script>

<div class="pin" class:active>
	<div class="col">
		<p class="overline">The Interlude</p>
		<h2>The Net Session</h2>

		<p class="line" class:on={shown >= 2}>
			For four chapters the game kept changing under you. Batters, then bowlers, then the
			ground itself. In a moment we start pricing all of it, working out what a single ball is
			actually worth.
		</p>

		<p class="line" class:on={shown >= 3}>
			Before that, have a feel of it yourself. Two dials, one scoreboard. How many runs a team
			usually still gets from a spot, and how often teams win from it. Give it a drag.
			<span class="cue" aria-hidden="true">↓</span>
		</p>
	</div>
</div>

<style>
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
		pointer-events: none;
	}

	.pin.active {
		visibility: visible;
	}

	/* top-left on desktop, clear of the ☰ nav (top-right); bottom-anchored on
	   mobile so the starfield reads above the words */
	.col {
		position: absolute;
		top: 14vh;
		left: 6vw;
		max-width: min(32rem, 78vw);
	}

	.overline {
		margin: 0 0 0.5rem;
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.28em;
		text-transform: uppercase;
		color: var(--gold);
	}

	h2 {
		margin: 0 0 1rem;
		font-size: clamp(1.9rem, 6vw, 3rem);
		line-height: 1.05;
		font-weight: 700;
		color: var(--ink);
	}

	.line {
		margin: 0 0 0.9rem;
		font-size: clamp(1.02rem, 2.4vw, 1.25rem);
		line-height: 1.5;
		color: var(--ink);
		opacity: 0;
		transform: translateY(6px);
		transition:
			opacity 420ms ease,
			transform 420ms ease;
	}

	.line.on {
		opacity: 1;
		transform: none;
	}

	.cue {
		display: inline-block;
		margin-left: 0.2rem;
		color: var(--teal);
		font-weight: 700;
	}

	@media (prefers-reduced-motion: reduce) {
		.line {
			transition: none;
		}
	}

	@media (max-width: 640px) {
		.col {
			top: auto;
			bottom: 12vh;
			left: 50%;
			transform: translateX(-50%);
			width: 88vw;
			max-width: 88vw;
		}
	}
</style>
