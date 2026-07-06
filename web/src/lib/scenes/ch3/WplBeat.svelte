<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh3Data, fmt1, fmt2, type Ch3Data } from './data';
	import FrontierScaffold from './FrontierScaffold.svelte';

	/**
	 * C3-7 — The WPL beat (two clocks, one beat — house rule). On the frontier plane,
	 * WPL clouds brighten and IPL dims (set on the scene's fieldState). ONE
	 * on-timeline containment clock (dot rate 38.5, needle landing at IPL 2009, the
	 * IPL era-scale printed beneath IT AND NOWHERE ELSE) plus TWO off-timeline
	 * head-to-head gauges (the squeeze, the arms race), each a direct WPL-vs-IPL
	 * pair with no IPL-year axis. "Still has the corner" / "a different game" is the
	 * subject — never a deficit. Crack ratio lands here as a plain cross-league
	 * difference (no "the IPL learned to survive them"; that lives in the footnote).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.4) return 1;
		if (progress < 0.7) return 2;
		return 3;
	});
	const shown = $derived(reduced || progress >= 0.25);
	/* mobile "read, then watch" (CONTRACT §17): ascending step bounds. Step 1 starts
	   at 0.25 to match the `shown` gate (the caption + panel appear together there),
	   so the reveal fades in when the caption actually shows, not before. It composes
	   with `.caption-slot.shown` via --reveal; 1 on desktop / reduced. */
	const BOUNDS = [0.25, 0.4, 0.7, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	/* land ONE gauge per caption step (storyboard working-memory cap): the
	   containment clock with step 1, the squeeze with step 2, the arms race with
	   step 3, so their numbers are never disclosed before their beat. */
	const showContainment = $derived(reduced || (shown && step >= 1));
	const showSqueeze = $derived(reduced || (shown && step >= 2));
	const showArms = $derived(reduced || (shown && step >= 3));

	let ch3 = $state<Ch3Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh3Data().then((d) => {
			if (alive) ch3 = d;
		});
		return () => {
			alive = false;
		};
	});

	const b = $derived(ch3 ? ch3.wpl_beat : null);
	/* the IPL death-wide comparator for the arms-race gauge (from the tax block) */
	const iplDeathWides = $derived(ch3 ? ch3.death_wide_tax.era_headline.ipl_2023_2026 : null);
	/* the IPL dot-rate era-scale endpoints for the containment clock */
	const iplDot = (season: number): number | null => {
		const row = ch3?.dot_plus.per_season.find((s) => s.league === 'ipl' && s.season === season);
		return row ? row.dot_pct : null;
	};
	const dot2009 = $derived(iplDot(2009));
	const dot2026 = $derived(iplDot(2026));

	/* ---- semicircular dial (containment clock) ------------------------------ */
	const CX = 110;
	const CY = 104;
	const R = 86;
	const DOT_MAX = 45;
	const S_MAX = 1.4; // squeeze (crack-ratio) bar scale
	const A_MAX = 8; // arms-race (death-wide) bar scale
	function polar(value: number, max: number): { x: number; y: number } {
		const t = Math.min(1, Math.max(0, value / max));
		const theta = Math.PI * (1 - t);
		return { x: CX + R * Math.cos(theta), y: CY - R * Math.sin(theta) };
	}
	function arcPath(fromV: number, toV: number, max: number): string {
		const a = polar(fromV, max);
		const c = polar(toV, max);
		return `M ${a.x.toFixed(1)} ${a.y.toFixed(1)} A ${R} ${R} 0 0 1 ${c.x.toFixed(1)} ${c.y.toFixed(1)}`;
	}
</script>

<div class="pin" class:active>
	<!-- faint persistent orientation anchors behind the WPL panel (held C3-3..C3-8) -->
	<FrontierScaffold {field} faint />

	{#if b}
		<div class="panel-slot" class:shown>
			<div class="panel">
				<p class="panel-title">Two clocks in the same breath</p>
				<div class="clocks">
					<!-- 1) the ONE on-timeline clock: containment (step 1) -->
					<figure class="clock on-timeline" class:lit={showContainment}>
						<figcaption>
							<span class="c-title">Containment clock</span>
							<span class="c-sub">still has the corner</span>
						</figcaption>
						{#if dot2009 !== null && dot2026 !== null}
							{@const needle = polar(b.dot_rate_pct, DOT_MAX)}
							{@const t09 = polar(dot2009, DOT_MAX)}
							{@const t26 = polar(dot2026, DOT_MAX)}
							<svg viewBox="0 0 220 128" role="img" aria-label="WPL dot rate {fmt1(b.dot_rate_pct)} percent, landing where the IPL's own dot rate was in 2009">
								<path d={arcPath(0, DOT_MAX, DOT_MAX)} class="track" />
								<path d={arcPath(dot2026, dot2009, DOT_MAX)} class="ipl-span" />
								<line x1={CX} y1={CY} x2={t09.x} y2={t09.y} class="ipl-tick" />
								<line x1={CX} y1={CY} x2={t26.x} y2={t26.y} class="ipl-tick" />
								<text x={t09.x + 4} y={t09.y - 6} class="ipl-yr" text-anchor="start">2009</text>
								<text x={t26.x - 4} y={t26.y - 6} class="ipl-yr" text-anchor="end">2026</text>
								<line x1={CX} y1={CY} x2={needle.x} y2={needle.y} class="needle" />
								<circle cx={CX} cy={CY} r="5" class="hub" />
								<text x={CX} y={CY + 20} class="wpl-val">WPL {fmt1(b.dot_rate_pct)}%</text>
							</svg>
							<p class="c-scale">IPL dot rate: 2009 <b>{fmt1(dot2009)}%</b> → 2026 <b>{fmt1(dot2026)}%</b></p>
						{/if}
					</figure>

					<!-- 2) off-timeline: the squeeze (crack ratio) (step 2) -->
					<figure class="clock off-timeline" class:lit={showSqueeze}>
						<figcaption>
							<span class="c-title">The squeeze</span>
							<span class="c-sub">not on the IPL's timeline</span>
						</figcaption>
						<div class="bars">
							<div class="bar-col">
								<div class="bar wpl" style="height:{(b.crack_ratio_wpl / S_MAX) * 100}%"><span>{fmt2(b.crack_ratio_wpl)}</span></div>
								<span class="bar-lab">WPL</span>
							</div>
							<div class="bar-col">
								<div class="bar ipl" style="height:{(b.crack_ratio_ipl_2023_2026 / S_MAX) * 100}%"><span>{fmt2(b.crack_ratio_ipl_2023_2026)}</span></div>
								<span class="bar-lab">IPL</span>
							</div>
							<div class="ref-one" style="bottom:{(1 / S_MAX) * 100}%"><span>1.0</span></div>
						</div>
						<p class="c-scale">dots still buy wickets above 1.0</p>
					</figure>

					<!-- 3) off-timeline: the arms race (death wides) (step 3) -->
					<figure class="clock off-timeline" class:lit={showArms}>
						<figcaption>
							<span class="c-title">The arms race</span>
							<span class="c-sub">not on the IPL's timeline</span>
						</figcaption>
						{#if iplDeathWides !== null}
							<div class="bars">
								<div class="bar-col">
									<div class="bar wpl" style="height:{(b.death_wides_per_100_legal / A_MAX) * 100}%"><span>{fmt1(b.death_wides_per_100_legal)}</span></div>
									<span class="bar-lab">WPL</span>
								</div>
								<div class="bar-col">
									<div class="bar ipl" style="height:{(iplDeathWides / A_MAX) * 100}%"><span>{fmt1(iplDeathWides)}</span></div>
									<span class="bar-lab">IPL</span>
								</div>
							</div>
							<p class="c-scale">death wides per 100 balls</p>
						{/if}
					</figure>
				</div>
			</div>
		</div>

		<div class="caption-slot" class:shown style:--reveal={reveal}>
			<div class="scene-card chip">
				{#if step === 1}
					<p>
						The WPL <strong>still has the corner the IPL lost.</strong> Its dot rate,
						{fmt1(b.dot_rate_pct)}%, sits right where the IPL's did back in 2009. On this one clock it
						looks like a young league.
					</p>
				{:else if step === 2}
					<p>
						But it is a <strong>different game, not a young IPL.</strong> Squeeze a WPL batter with dot
						after dot and the wicket still comes, <strong>{fmt2(b.crack_ratio_wpl)} times as often.</strong>
						In the IPL that same squeeze has gone quiet, down to {fmt2(b.crack_ratio_ipl_2023_2026)}.
						<button class="dagger" onclick={() => footnotesOpen.set('crack-ratio')} aria-label="How the squeeze was counted">ⓘ</button>
					</p>
				{:else}
					<p>
						And that flood of death wides? <strong>It never reached the WPL:</strong>
						{fmt1(b.death_wides_per_100_legal)} per 100 balls, not {iplDeathWides !== null ? fmt1(iplDeathWides) : '-'}.
						The wide-yorker arms race is a men's-league thing, not a stage every league has to pass
						through.
					</p>
				{/if}
			</div>
		</div>
	{/if}
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

	.panel-slot {
		position: absolute;
		top: 5vh;
		left: 50%;
		transform: translateX(-50%);
		width: min(720px, 95vw);
		opacity: 0;
	}

	.panel-slot.shown {
		opacity: 1;
	}

	.panel {
		border: 1px solid rgba(46, 196, 182, 0.32);
		border-radius: 12px;
		background: rgba(13, 20, 24, 0.82);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
		padding: 0 0.7rem 0.7rem;
		overflow: hidden;
	}

	.panel-title {
		margin: 0 -0.7rem 0.6rem;
		padding: 0.5rem 1rem;
		background: rgba(46, 196, 182, 0.1);
		font-size: 0.84rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		color: var(--ink);
	}

	.clocks {
		display: flex;
		gap: 0.6rem;
		align-items: flex-end;
	}

	.clock {
		margin: 0;
		flex: 1;
		min-width: 0;
		/* reserve the slot always (no layout shift) but reveal per caption step;
		   instant, not a transition — the demand-mode loop can idle mid-scroll and
		   freeze a CSS opacity transition partway (leaving a gauge near-invisible),
		   so match the panel's own instant show/hide */
		opacity: 0;
	}

	.clock.lit {
		opacity: 1;
	}

	.off-timeline {
		border-left: 1px dashed rgba(232, 236, 245, 0.14);
		padding-left: 0.5rem;
	}

	.clock figcaption {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.1rem;
		margin-bottom: 0.3rem;
	}

	.c-title {
		font-size: 0.8rem;
		font-weight: 700;
		color: var(--ink);
		text-align: center;
	}

	.c-sub {
		font-size: 0.66rem;
		letter-spacing: 0.03em;
		color: var(--teal);
		text-align: center;
	}

	.clock svg {
		display: block;
		width: 100%;
		height: auto;
	}

	.track {
		fill: none;
		stroke: rgba(232, 236, 245, 0.12);
		stroke-width: 8;
		stroke-linecap: round;
	}

	.ipl-span {
		fill: none;
		stroke: #7a8298;
		stroke-width: 8;
		stroke-linecap: round;
	}

	.ipl-tick {
		stroke: rgba(232, 236, 245, 0.35);
		stroke-width: 1.2;
		stroke-dasharray: 2 3;
	}

	.ipl-yr {
		fill: var(--ink-dim);
		font-size: 9.5px;
		font-variant-numeric: tabular-nums;
	}

	.needle {
		stroke: var(--teal);
		stroke-width: 3;
		stroke-linecap: round;
	}

	.hub {
		fill: var(--teal);
	}

	.wpl-val {
		fill: var(--teal);
		font-size: 12px;
		font-weight: 700;
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	.c-scale {
		margin: 0.2rem 0 0;
		text-align: center;
		font-size: 0.68rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.c-scale b {
		color: #b9c2d6;
		font-weight: 700;
	}

	/* off-timeline bar pairs */
	.bars {
		position: relative;
		display: flex;
		justify-content: center;
		align-items: flex-end;
		gap: 0.7rem;
		height: 108px;
		margin-top: 1.1rem;
		padding: 0 0.4rem;
	}

	.bar-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: flex-end;
		height: 100%;
	}

	.bar {
		width: 26px;
		border-radius: 4px 4px 0 0;
		display: flex;
		justify-content: center;
		align-items: flex-start;
		transition: height 700ms ease;
	}

	.bar span {
		transform: translateY(-1.1rem);
		font-size: 0.72rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		color: var(--ink);
	}

	.bar.wpl {
		background: var(--teal);
	}

	.bar.ipl {
		background: #7a8298;
	}

	.bar-lab {
		margin-top: 0.2rem;
		font-size: 0.66rem;
		color: var(--ink-dim);
	}

	.ref-one {
		position: absolute;
		left: 0.4rem;
		right: 0.4rem;
		border-top: 1.4px dashed rgba(232, 236, 245, 0.45);
	}

	.ref-one span {
		position: absolute;
		left: -4px;
		transform: translate(-100%, -50%);
		font-size: 9px;
		color: var(--ink-dim);
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 8vh;
		max-width: min(36rem, 84vw);
		opacity: 0;
	}

	.caption-slot.shown {
		opacity: var(--reveal, 1); /* mobile "read, then watch" (CONTRACT §17); 1 on desktop / reduced */
	}

	.dagger {
		pointer-events: auto;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 44px;
		min-height: 44px;
		margin: -10px 0;
		padding: 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 1rem;
		cursor: pointer;
	}

	.dagger:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.panel-slot {
			top: 3vh;
			/* the three gauges stack vertically on phones; cap the panel and let it
			   scroll so it never collides with the bottom caption slot */
			max-height: 66dvh;
			overflow-y: auto;
			overscroll-behavior: contain;
		}

		.clocks {
			flex-direction: column;
			align-items: stretch;
			gap: 0.4rem;
		}

		.off-timeline {
			border-left: none;
			border-top: 1px dashed rgba(232, 236, 245, 0.14);
			padding-left: 0;
			padding-top: 0.4rem;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(72px, calc(env(safe-area-inset-bottom) + 56px));
		}
	}
</style>
