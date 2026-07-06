<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { loadInterludeData, eraContrast, int, type InterludeData } from './data';

	/**
	 * IN-6 — Close (storyboard §1). Name what the reader just learned, then spend
	 * it by pointing at Chapter 5, so the pause pays off and the return to the
	 * moving field lands. Two caption steps, top-left, persistent. The teasers are
	 * bound to interlude.json (the win gap, the corpus size), never hand-typed.
	 *
	 * Chapter 5 ships in a separate later release (R3b-2), so the hand-off carries
	 * an explicit in-build qualifier and promises no shipped content. The field
	 * begins to un-dim on the last step (a luminance lerp back toward full, still
	 * demand-mode, no morph) — declared on the SceneDef, not driven here.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	let d = $state<InterludeData | null>(null);
	let started = false;
	$effect(() => {
		if (!(active || progress > 0) || started) return;
		started = true;
		loadInterludeData()
			.then((x) => (d = x))
			.catch(() => {});
	});

	const contrast = $derived(d ? eraContrast(d) : null);
	// spelt-out gap word for the teaser, so no digit sits alone in the sentence
	const GAP_WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
	const gapWord = $derived(
		contrast ? (GAP_WORDS[contrast.winGap] ?? String(contrast.winGap)) : 'eight'
	);

	const shown = $derived.by(() => {
		if (reduced) return 2;
		return progress >= 0.4 ? 2 : 1;
	});
</script>

<div class="pin" class:active>
	<div class="col">
		<p class="line on">That is the machine. Two dials, one scoreboard, and every number a memory of a real match.</p>

		<p class="line" class:on={shown >= 2}>
			Now we spend it. Next up, what a single ball is actually worth, priced in both: the runs it
			is likely to make, and the win it swings.
			<span class="soon">Chapter 5 is in build.</span>
		</p>

		{#if d && contrast}
			<div class="teasers" class:on={shown >= 2}>
				<p class="teaser">
					The same chase is a win about {gapWord} more times in a hundred now than in 2008 to 2012.
				</p>
				<p class="teaser">
					Every number here is read from {int(d.corpus.matches)} real matches. Where the matches run thin, it
					says so.
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
		pointer-events: none;
	}

	.pin.active {
		visibility: visible;
	}

	.col {
		position: absolute;
		top: 16vh;
		left: 6vw;
		max-width: min(34rem, 80vw);
	}

	.line {
		margin: 0 0 1rem;
		font-size: clamp(1.1rem, 2.8vw, 1.5rem);
		line-height: 1.4;
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

	.soon {
		display: inline-block;
		margin-left: 0.35rem;
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		padding: 0.15rem 0.5rem;
		border: 1px solid rgba(151, 161, 184, 0.35);
		border-radius: 999px;
		color: var(--ink-dim);
		vertical-align: middle;
	}

	.teasers {
		margin-top: 0.6rem;
		opacity: 0;
		transition: opacity 500ms ease;
	}

	.teasers.on {
		opacity: 1;
	}

	.teaser {
		margin: 0 0 0.5rem;
		padding-left: 0.7rem;
		border-left: 2px solid rgba(46, 196, 182, 0.5);
		font-size: clamp(0.85rem, 1.9vw, 0.98rem);
		line-height: 1.4;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	@media (prefers-reduced-motion: reduce) {
		.line,
		.teasers {
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
