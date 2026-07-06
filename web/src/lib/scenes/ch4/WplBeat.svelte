<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh4Data, pct, runs, int, type Ch4Data } from './data';
	import TideScaffold from './TideScaffold.svelte';

	/**
	 * C4-10 — The WPL beat (two clocks, one beat — house rule). The WPL block
	 * brightens and the IPL dims (set on the scene's fieldState). ONE on-calendar
	 * clock (the WPL's 200-club rate sitting back with the early IPL) plus the
	 * league-age clock that REFUSES the timeline (at the same age its tide rises
	 * faster, 157 → 169 in four years, and four-led — along the ground, not over the
	 * rope). "Beside the path, not behind it" is the subject, never a deficit. Five
	 * 200s in WPL 2026: a 200 is still an event there. Every number from ch4.json.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* four one-idea steps: 1 calendar clock · 2 the faster rise · 3 the four-led
	   shape · 4 the event (still-an-event, five 200s). */
	const step = $derived.by(() => {
		if (progress < 0.36) return 1;
		if (progress < 0.56) return 2;
		if (progress < 0.76) return 3;
		return 4;
	});
	const shown = $derived(reduced || progress >= 0.22);
	const BOUNDS = [0.22, 0.36, 0.56, 0.76, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const showCalendar = $derived(reduced || (shown && step >= 1));
	const showAge = $derived(reduced || (shown && step >= 2));

	let ch4 = $state<Ch4Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh4Data().then((d) => {
			if (alive) ch4 = d;
		});
		return () => {
			alive = false;
		};
	});

	const b = $derived(ch4 ? ch4.wpl_beat : null);
	const wplP200 = $derived(b ? b.exceedance_p200 : null);
	const ipl2008 = $derived(b ? b.sits_between_ipl_seasons.ipl_p200['2008'] : null);
	const ipl2015 = $derived(b ? b.sits_between_ipl_seasons.ipl_p200['2015'] : null);
	const wplAvg = $derived.by(() => {
		if (!b) return [] as number[];
		return Object.keys(b.avg_first_innings_by_season)
			.map(Number)
			.sort((a, c) => a - c)
			.map((y) => b.avg_first_innings_by_season[String(y)]);
	});
	const iplAge = $derived.by(() => {
		if (!b) return [] as number[];
		const m = b.maturity_clock.ipl_by_league_year;
		return [1, 2, 3, 4].map((y) => m[String(y)]);
	});
	const totals2026 = $derived(b ? b.totals_200_by_season['2026'] : null);

	/* ---- calendar clock: a mini scale with the WPL marked between two IPL years -- */
	const SC_LO = 10;
	const SC_HI = 14;
	const scAt = (p: number): number =>
		4 + ((Math.min(SC_HI, Math.max(SC_LO, p)) - SC_LO) / (SC_HI - SC_LO)) * 92;

	/* ---- age clock: WPL vs IPL first-four-league-years sparkline ---- */
	const AW = 150;
	const AH = 74;
	const AP = 12;
	const AYMIN = 145;
	const AYMAX = 175;
	const axAt = (i: number): number => AP + (i / 3) * (AW - 2 * AP);
	const ayAt = (v: number): number =>
		AH - AP - ((Math.min(AYMAX, Math.max(AYMIN, v)) - AYMIN) / (AYMAX - AYMIN)) * (AH - 2 * AP);
	const spark = (vals: number[]): string =>
		vals.map((v, i) => `${axAt(i).toFixed(1)},${ayAt(v).toFixed(1)}`).join(' ');
</script>

<div class="pin" class:active>
	<TideScaffold {field} faint />

	{#if b}
		<div class="panel-slot" class:shown>
			<div class="panel">
				<p class="panel-title">Two clocks in the same breath</p>
				<div class="clocks">
					<!-- 1) on the calendar clock -->
					<figure class="clock" class:lit={showCalendar}>
						<figcaption>
							<span class="c-title">On the calendar</span>
							<span class="c-sub">sits back with the early IPL</span>
						</figcaption>
						{#if wplP200 !== null && ipl2008 !== null && ipl2015 !== null}
							<svg viewBox="0 0 100 44" role="img" aria-label="WPL 200-club rate {pct(wplP200)} percent, between the IPL's 2015 and 2008">
								<line x1="4" y1="30" x2="96" y2="30" class="scale" />
								<line x1={scAt(ipl2015)} y1="24" x2={scAt(ipl2015)} y2="36" class="ipl-tick" />
								<line x1={scAt(ipl2008)} y1="24" x2={scAt(ipl2008)} y2="36" class="ipl-tick" />
								<text x={scAt(ipl2015)} y="20" class="ipl-yr" text-anchor="middle">IPL ’15</text>
								<text x={scAt(ipl2008)} y="20" class="ipl-yr" text-anchor="middle">IPL ’08</text>
								<circle cx={scAt(wplP200)} cy="30" r="4" class="wpl-mark" />
								<text x={scAt(wplP200)} y="43" class="wpl-lab" text-anchor="middle">WPL {pct(wplP200)}%</text>
							</svg>
						{/if}
					</figure>

					<!-- 2) at the same league age (refuses the timeline) -->
					<figure class="clock off" class:lit={showAge}>
						<figcaption>
							<span class="c-title">At the same age</span>
							<span class="c-sub">rising faster</span>
						</figcaption>
						{#if wplAvg.length === 4 && iplAge.length === 4}
							<svg viewBox="0 0 {AW} {AH}" role="img" aria-label="Over its first four seasons the WPL's typical first innings rose to {runs(wplAvg[3])}, faster than the IPL at the same age">
								<polyline points={spark(iplAge)} class="ipl-line" />
								<polyline points={spark(wplAvg)} class="wpl-line" />
								<circle cx={axAt(3)} cy={ayAt(wplAvg[3])} r="3" class="wpl-dot" />
							</svg>
							<p class="c-scale">WPL {runs(wplAvg[0])} → <b>{runs(wplAvg[3])}</b> in four years</p>
						{/if}
					</figure>
				</div>
			</div>
		</div>

		<div class="caption-slot" class:shown style:--reveal={reveal}>
			<div class="scene-card chip">
				{#if step === 1}
					<p>
						On the calendar, the WPL's 200 club sits back with the young IPL:
						<strong>{wplP200 !== null ? pct(wplP200) : '11.4'}% of first innings,</strong> about where the
						men were around 2008 and 2015.
					</p>
				{:else if step === 2}
					<p>
						But wind both leagues back to season one. <strong>At the same age the WPL's tide is rising
							faster,</strong> {wplAvg.length ? runs(wplAvg[0]) : '157'} to {wplAvg.length ? runs(wplAvg[3]) : '169'}
						in four years, while the young IPL was still flat.
					</p>
				{:else if step === 3}
					<p>
						And it floods differently, <strong>along the ground, four-led, not over the rope.</strong>
						Nearly half its runs come in fours, an engine the men's game never played at any age.
						<button class="dagger" onclick={() => footnotesOpen.set('wpl-two-clocks-ch4')} aria-label="The WPL, on two clocks">ⓘ</button>
					</p>
				{:else}
					<p>
						And a 200 there is <strong>still a real event,</strong> where in the IPL more than half of
						first innings now clear it. In 2026 the WPL had {totals2026 !== null ? int(totals2026) : 'five'} of them.
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
		width: min(560px, 94vw);
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
		opacity: 0;
	}

	.clock.lit {
		opacity: 1;
	}

	.clock.off {
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

	.scale {
		stroke: rgba(232, 236, 245, 0.2);
		stroke-width: 1.4;
	}

	.ipl-tick {
		stroke: #7a8298;
		stroke-width: 1.4;
	}

	.ipl-yr {
		fill: var(--ink-dim);
		font-size: 7px;
		font-variant-numeric: tabular-nums;
	}

	.wpl-mark {
		fill: var(--teal);
	}

	.wpl-lab {
		fill: var(--teal);
		font-size: 8px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.ipl-line {
		fill: none;
		stroke: #7a8298;
		stroke-width: 1.6;
		stroke-linejoin: round;
	}

	.wpl-line {
		fill: none;
		stroke: var(--teal);
		stroke-width: 2.2;
		stroke-linejoin: round;
		filter: drop-shadow(0 0 3px rgba(46, 196, 182, 0.4));
	}

	.wpl-dot {
		fill: var(--teal);
	}

	.c-scale {
		margin: 0.2rem 0 0;
		text-align: center;
		font-size: 0.68rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.c-scale b {
		color: var(--teal);
		font-weight: 700;
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 8vh;
		max-width: min(34rem, 84vw);
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
			/* size to content — no internal scroll region, so page scroll always drives
			   the scene (audit: avoid the mobile scroll-trap on the stacked clocks) */
			top: 3vh;
		}

		.clocks {
			flex-direction: column;
			align-items: stretch;
			gap: 0.4rem;
		}

		.clock.off {
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
