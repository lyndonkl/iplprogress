<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh6Data, fmt2, type Ch6Data, type TwoTruth } from './data';
	import { pickCaptionCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';
	import Starfield from './Starfield.svelte';

	/**
	 * C6-3 — THE TWO-TRUTHS MONEY SHOT (the house framing made literal). The
	 * constellation HOLDS the 'all' map (no re-sort, no second morph). Two honest
	 * ways to compare a season usually agree; here they split. By outcome mix (where
	 * the runs come from, ball by ball) WPL 2026's twin is IPL 2008. By run rate it
	 * is IPL 2022. BOTH TRUE AT ONCE — so the WPL sits beside the men's path, a
	 * different dialect, not an earlier IPL. The WPL cluster dims while the IPL path
	 * is oriented, then BRIGHTENS on the reveal (wplDim, driven by index.ts).
	 *
	 * Every number is from ch6.json constellation.two_truths (artifact wins).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.3 ? 1 : progress < 0.55 ? 2 : progress < 0.8 ? 3 : 4);
	const BOUNDS = [0, 0.3, 0.55, 0.8, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

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

	/** the money-shot season: WPL 2026 (the last two-truths pairing) */
	const tt2026 = $derived<TwoTruth | null>(
		ch6?.constellation.two_truths.find((t) => t.wpl_season === 2026) ?? null
	);
	const styleTwin = $derived(tt2026?.outcome_mix_twin.ipl_season ?? 2008);
	const rrTwin = $derived(tt2026?.run_rate_twin.ipl_season ?? 2022);
	const wplRr = $derived(tt2026?.wpl_rr ?? 8.54);

	/* the WPL-2026 gi (22) and its STYLE-twin gi (0 = IPL 2008): looked up from the
	   groups, never hardcoded. The rate twin is NOT drawn on the map — the map
	   encodes STYLE only (§0.2 guardrail 6), so the run rate lives ONLY on the card. */
	const wpl26Gi = $derived(
		ch6?.constellation.groups.find((g) => g.league === 'wpl' && g.season === 2026)?.gi ?? 22
	);
	const styleGi = $derived(
		ch6?.constellation.groups.find((g) => g.league === 'ipl' && g.season === styleTwin)?.gi ?? 0
	);

	const highlightGis = $derived(step >= 2 ? [wpl26Gi, styleGi] : []);
	const labelGis = $derived(step >= 2 ? [wpl26Gi, styleGi] : []);

	/* §0.4a caption safe-corner from the live star geometry (opposite the WPL
	   cluster); re-picks on resize + as the WPL brighten settles */
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
</script>

<div class="pin" class:active>
	<Starfield
		{field}
		{reduced}
		{progress}
		on={true}
		threadPhase="all"
		showWorm={true}
		showThreads={true}
		{labelGis}
		{highlightGis}
		legend={true}
		footnoteId="ch6-constellation"
	/>

	{#if tt2026 && (reduced || step >= 3)}
		<div class="truths">
			<span class="t-head">WPL 2026, two true readings</span>
			<div class="t-row">
				<span class="t-key style">its style</span>
				<span class="t-val">plays most like IPL {styleTwin}</span>
			</div>
			<div class="t-row">
				<span class="t-key rate">its scoring</span>
				<span class="t-val">{fmt2(wplRr)} an over, the IPL's {rrTwin} rate</span>
			</div>
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style="{capStyle}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>
					There are two fair ways to ask how alike two seasons are. How fast they scored, and where
					the runs came from, ball by ball. Usually the two answers roughly agree. For the WPL, they
					come apart.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					By where the runs come from, WPL 2026's nearest twin is <strong>IPL {styleTwin}.</strong> All
					four teal threads run back to the men's earliest years. That is the style match.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					But it scores {fmt2(wplRr)} runs an over, and the IPL did not reach that until
					<strong>{rrTwin}.</strong> Same run rate as {rrTwin}, same shot mix as {styleTwin}. Both true
					at once.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					So it is not a younger IPL running the same road. Style of {styleTwin}, scoring of {rrTwin},
					in one season. A different dialect of the same game, standing beside the path.
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

	/* upper-right region is clear of the IPL worm's very top (2026) but not the
	   nav — keep this panel top-RIGHT-of-centre, below the nav band */
	.truths {
		position: absolute;
		right: 4vw;
		top: 20vh;
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
		padding: 0.75rem 0.95rem;
		border-radius: 14px;
		background: rgba(10, 14, 24, 0.85);
		border: 1px solid rgba(46, 196, 182, 0.4);
		max-width: 17rem;
		pointer-events: none;
	}

	.t-head {
		font-size: 0.64rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: #62d2c3;
	}

	.t-row {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
	}

	.t-key {
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.t-key.style {
		color: #62d2c3;
	}

	.t-key.rate {
		color: var(--gold);
	}

	.t-val {
		font-size: 0.92rem;
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
		.truths {
			right: 3vw;
			top: auto;
			bottom: 27vh;
			max-width: 66vw;
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
