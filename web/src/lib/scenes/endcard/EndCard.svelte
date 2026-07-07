<script lang="ts">
	import { base } from '$app/paths';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { pickedTeam } from '$lib/state';

	/**
	 * END CARD (storyboard §4) — closes the R1a read with the piece's shape
	 * visible: what's done, what's next, where the methods live. Restates the
	 * piece's promise (the field behind the card never left), teases the
	 * sandbox, and points at the chapter nav. No dead links, no promised
	 * features that don't exist yet. Static DOM — the field idles dim behind
	 * it, loop stopped (demand mode).
	 */
	let { field }: SceneAnnotationProps = $props();

	// Pixel truth: the count the tease quotes is the count the field renders.
	const n = $derived(field?.data.nPoints ?? 316199);
	const teamClause = $derived(
		$pickedTeam !== null && $pickedTeam.league !== null && $pickedTeam.team !== 'neutral'
			? `, opening on ${$pickedTeam.team}`
			: '. It opens on the 2019 final, or on whichever team you pick'
	);
</script>

<div class="pin">
	<div class="scene-card interactive card">
		<p class="overline">Chapter 6: Two Dialects · done</p>

		<h2>Every ball is still here.</h2>
		<p class="promise">
			The field behind this card is the one you watched build. Every ball the IPL and WPL
			have ever bowled is in it. That was the promise: they never leave. The rest of the
			story is told on top of them.
		</p>

		<p class="next">
			<strong>Up next: Chapter 7, The Twelfth Man.</strong>
			<em>In 2023 the men added a rule many credit for their scoring taking off. The women never did. A rare natural experiment.</em>
			<span class="tag">in build · the story grows chapter by chapter</span>
		</p>

		<p class="tease">
			<strong>The field is yours.</strong>
			All {n.toLocaleString('en-US')} balls on this screen, filterable under your thumb, season
			by season and team by team{teamClause}. Tap any ball to name it.
			<a class="tease-link" href="{base}/#bowl">Keep scrolling into the sandbox →</a>
		</p>

		<p class="navhint">
			The whole shape of the story lives in the <span class="glyph" aria-hidden="true">☰</span>
			menu, top right. Every chapter by name, lighting up as it lands. Your team pick rides
			along, and you can change it there anytime.
		</p>

		<p class="methods"><a href="{base}/methods/">How we computed all of this →</a></p>
		<p class="note">Data: Cricsheet, ball-by-ball, through IPL 2026 / WPL 2026.</p>
	</div>
</div>

<style>
	.pin {
		position: sticky;
		top: 0;
		height: 100vh;
		height: 100dvh;
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	.card {
		max-width: min(34rem, 92vw);
	}

	.card h2 {
		font-size: clamp(1.35rem, 3.2vw, 1.9rem);
	}

	.promise,
	.next,
	.tease,
	.navhint {
		margin-top: 0.9rem;
		font-size: clamp(0.98rem, 2.2vw, 1.12rem);
		line-height: 1.5;
	}

	.promise {
		margin-top: 0.55rem;
	}

	.next em {
		display: block;
		color: var(--ink-dim);
		font-style: italic;
	}

	.tease-link {
		display: inline-block;
		margin-top: 0.5rem;
		padding: 0.4rem 0;
		color: var(--teal);
		font-weight: 600;
	}

	.tease-link:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.navhint {
		color: var(--ink-dim);
		font-size: clamp(0.88rem, 2vw, 0.98rem);
	}

	.glyph {
		display: inline-block;
		padding: 0 0.15em;
		border: 1px solid rgba(151, 161, 184, 0.45);
		border-radius: 4px;
		font-size: 0.85em;
		line-height: 1.3;
		color: var(--ink);
	}

	.tag {
		display: inline-block;
		margin-top: 0.35rem;
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		padding: 0.15rem 0.5rem;
		border: 1px solid rgba(151, 161, 184, 0.35);
		border-radius: 999px;
		color: var(--ink-dim);
	}

	.methods {
		margin-top: 1rem;
	}

	.methods a {
		/* comfortable tap target (≥44px effective) without breaking the text flow */
		display: inline-block;
		padding: 0.6rem 0;
		color: var(--teal);
	}

	.methods a:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
</style>
