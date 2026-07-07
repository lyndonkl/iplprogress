<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { panelCaptionStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh7Data, ensureRiverTable, fmt1, type Ch7Data } from './data';

	/**
	 * C7-4 — SUPPORTING 1: the Licence Index. Freeze the game at one hard match
	 * state (four or more down, the middle overs) and compare the same spot before
	 * and after the rule: strike rate jumped 116.8 → 129.9 while the rate batters
	 * got out barely moved (4.88 → 4.95 per 100 balls). Extra aggression at no real
	 * extra risk. And the top order took the most licence (positions 1-3 +18.0% vs
	 * the lower order's +11.0%). A 2D split-screen over the dimmed rivers (no second
	 * morph). Every number from ch7.json license_index (artifact wins).
	 *
	 * Honesty (owner-locked): the out-rate did NOT fall, it held flat — the claim
	 * is "aggression up at no material risk premium", never "risk down".
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.4 ? 1 : progress < 0.72 ? 2 : 3);
	const BOUNDS = [0, 0.4, 0.72, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch7 = $state<Ch7Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh7Data().then((d) => {
			if (alive) ch7 = d;
		});
		return () => {
			alive = false;
		};
	});

	/* keep the dim river backdrop alive on a deep link into this beat */
	$effect(() => {
		if (field && ch7) ensureRiverTable(field, ch7);
	});

	const lic = $derived(ch7?.license_index ?? null);
	const showAfter = $derived(reduced || step >= 2);
	const showPos = $derived(reduced || step >= 3);
	/* SR bar width as a fraction of a 90..135 window, for the two-panel bars */
	const barPct = (sr: number): number => Math.max(6, Math.min(100, ((sr - 90) / (135 - 90)) * 100));
	const top = $derived(lic?.by_position['1-3'] ?? null);
	const low = $derived(lic?.by_position['6-8'] ?? null);

	/* §0.4a: place the caption in the measured panel's side margin so it never covers
	   the centred grid (audit should-fix #10). Mobile → bottom read-then-watch slot. */
	let panelEl = $state<HTMLElement | null>(null);
	let capTick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => capTick++);
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	const capStyle = $derived.by(() => {
		void capTick;
		void progress;
		if (isNarrowViewport() || !panelEl) return '';
		return panelCaptionStyle(panelEl);
	});
</script>

<div class="pin" class:active>
	{#if lic}
		<div class="panel" bind:this={panelEl}>
			<p class="overline">the licence · one match state, before and after the rule</p>
			<p class="state">Four or more wickets down, the middle overs (overs {lic.state.overs[0]}–{lic.state.overs[1]}).</p>

			<div class="split">
				<div class="side before">
					<span class="s-head">Before the rule<br /><span class="yrs">{lic.state.pre_window[0]}–{lic.state.pre_window[1]}</span></span>
					<span class="sr">{fmt1(lic.headline.sr_pre)}</span>
					<span class="sr-lbl">runs per 100 balls</span>
					<div class="track"><div class="fill before" style="width:{barPct(lic.headline.sr_pre)}%;"></div></div>
					<span class="risk">got out {fmt1(lic.headline.dismissals_pre)} times per 100 balls</span>
				</div>
				<div class="side after" class:show={showAfter}>
					<span class="s-head">After the rule<br /><span class="yrs">{lic.state.post_window[0]}–{lic.state.post_window[1]}</span></span>
					<span class="sr hot">{fmt1(lic.headline.sr_post)}</span>
					<span class="sr-lbl">runs per 100 balls</span>
					<div class="track"><div class="fill after" style="width:{showAfter ? barPct(lic.headline.sr_post) : barPct(lic.headline.sr_pre)}%;"></div></div>
					<span class="risk">got out {fmt1(lic.headline.dismissals_post)} times per 100 balls</span>
				</div>
			</div>

			{#if top && low}
				<div class="positions" class:show={showPos}>
					<span class="p-head">who took the licence</span>
					<div class="p-row">
						<span class="p-name">Top three (1–3)</span>
						<div class="p-track"><div class="p-fill top" style="width:{showPos ? Math.min(100, top.pct_change * 4) : 0}%;"></div></div>
						<span class="p-val">+{fmt1(top.pct_change)}%</span>
					</div>
					<div class="p-row">
						<span class="p-name">Lower order (6–8)</span>
						<div class="p-track"><div class="p-fill low" style="width:{showPos ? Math.min(100, low.pct_change * 4) : 0}%;"></div></div>
						<span class="p-val">+{fmt1(low.pct_change)}%</span>
					</div>
				</div>
			{/if}

			<button class="dagger" onclick={() => footnotesOpen.set('ch7-license')} aria-label="How the licence index is built">
				ⓘ how we measure this
			</button>
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style="{capStyle}; --reveal: {reveal};">
		{#if step === 1}
			<div class="scene-card">
				<p>
					Freeze the game at one hard spot: four or more down, in the middle overs. The same tricky
					position, before the rule and after it.
				</p>
			</div>
		{:else if step === 2 && lic}
			<div class="scene-card">
				<p>
					From that spot batters went from {fmt1(lic.headline.sr_pre)} to
					<strong>{fmt1(lic.headline.sr_post)}</strong> runs per 100 balls. And the rate they got out
					barely moved. More swing, no more risk.
				</p>
			</div>
		{:else if lic && top}
			<div class="scene-card">
				<p>
					And it was the top order who grabbed it. The first three lifted
					<strong>+{fmt1(top.pct_change)}%</strong>, the lower order less. Free licence, and the best
					batters cashed it first.
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
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	.pin.active {
		visibility: visible;
	}

	.panel {
		pointer-events: auto;
		width: min(30rem, 90vw);
		background: rgba(11, 14, 20, 0.74);
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 14px;
		padding: 1rem 1.2rem 1.1rem;
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
	}

	.overline {
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--gold);
		margin: 0 0 0.3rem;
	}

	.state {
		margin: 0 0 0.9rem;
		font-size: 0.78rem;
		color: var(--ink-dim);
		line-height: 1.35;
	}

	.split {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.side {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.s-head {
		font-size: 0.68rem;
		font-weight: 700;
		color: var(--ink-dim);
		line-height: 1.3;
		min-height: 2.6em;
	}

	.s-head .yrs {
		font-weight: 600;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.sr {
		font-size: clamp(1.8rem, 7vw, 2.5rem);
		font-weight: 800;
		line-height: 1;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
		transition: color 0.3s ease;
	}

	.sr.hot {
		color: var(--gold);
		text-shadow: 0 0 14px rgba(232, 163, 61, 0.4);
	}

	.after:not(.show) .sr.hot {
		color: var(--ink-dim);
		text-shadow: none;
	}

	.sr-lbl {
		font-size: 0.64rem;
		color: var(--ink-dim);
	}

	.track {
		margin-top: 0.35rem;
		height: 6px;
		border-radius: 999px;
		background: rgba(232, 236, 245, 0.1);
		overflow: hidden;
	}

	.fill {
		height: 100%;
		border-radius: 999px;
		transition: width 0.55s cubic-bezier(0.22, 1, 0.36, 1);
	}

	.fill.before {
		background: rgba(151, 161, 184, 0.65);
	}

	.fill.after {
		background: var(--gold);
	}

	.risk {
		margin-top: 0.45rem;
		font-size: 0.68rem;
		line-height: 1.35;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.positions {
		margin-top: 1rem;
		border-top: 1px solid rgba(151, 161, 184, 0.2);
		padding-top: 0.7rem;
		opacity: 0;
		transition: opacity 0.4s ease;
	}

	.positions.show {
		opacity: 1;
	}

	.p-head {
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.p-row {
		display: grid;
		grid-template-columns: 8rem 1fr 3rem;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.4rem;
	}

	.p-name {
		font-size: 0.72rem;
		color: var(--ink);
	}

	.p-track {
		height: 8px;
		border-radius: 999px;
		background: rgba(232, 236, 245, 0.1);
		overflow: hidden;
	}

	.p-fill {
		height: 100%;
		border-radius: 999px;
		transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
	}

	.p-fill.top {
		background: var(--gold);
	}

	.p-fill.low {
		background: rgba(151, 161, 184, 0.7);
	}

	.p-val {
		font-size: 0.76rem;
		font-weight: 700;
		text-align: right;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.dagger {
		display: inline-block;
		margin-top: 0.8rem;
		min-height: 44px;
		padding: 0.3rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.78rem;
		cursor: pointer;
	}

	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 6vh;
		max-width: min(22rem, 30vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	@media (max-width: 640px) {
		.pin {
			place-items: start center;
			padding-top: 7vh;
		}

		.panel {
			max-height: 76vh;
			overflow-y: auto;
		}

		.p-row {
			grid-template-columns: 6.5rem 1fr 2.6rem;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(3vh, calc(env(safe-area-inset-bottom) + 10px));
		}
	}
</style>
