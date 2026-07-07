<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import {
		loadCh5Data,
		IPL_EARLY,
		IPL_RECENT,
		FINISHER_BANDS,
		fatalRate,
		in100,
		type Ch5Data,
		type FinisherBandName
	} from './data';

	/**
	 * C5-9 — Supporting 3: the finisher's office (the moving cliff). The chart
	 * reads chases with five overs left: along the bottom, how many an over you
	 * still need; the height, how many of a hundred such chases got home. One
	 * curve per era (early grey ghost, recent bright). The highlighted 8-10 band
	 * carries per-era "{w} of {t} such chases" sub-labels ON SCREEN (guardrail 4),
	 * and the fatal rate (the cliff, the first band losing more than it wins) is
	 * DATA-DERIVED from the emitted table, never hardcoded: 10 then, 12 now.
	 * Tapping any band reads its raw cohort. ARTIFACT WINS: 55 → 85 (17/31 → 35/41).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.34 ? 1 : progress < 0.68 ? 2 : 3);
	const BOUNDS = [0, 0.34, 0.68, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch5 = $state<Ch5Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh5Data().then((d) => {
			if (alive) ch5 = d;
		});
		return () => {
			alive = false;
		};
	});

	const early = $derived(ch5?.finisher.table[IPL_EARLY] ?? null);
	const recent = $derived(ch5?.finisher.table[IPL_RECENT] ?? null);
	const head = $derived(ch5?.finisher.headline ?? null);
	const cliffEarly = $derived(early ? fatalRate(early) : null);
	const cliffRecent = $derived(recent ? fatalRate(recent) : null);

	/* chart geometry: x = band index (0..3), y = wins in 100 (0 bottom .. 100 top) */
	const CW = 100;
	const CH = 62;
	const PAD_L = 8;
	const PAD_R = 4;
	const PAD_T = 6;
	const PAD_B = 10;
	const bx = (i: number): number => PAD_L + (i * (CW - PAD_L - PAD_R)) / (FINISHER_BANDS.length - 1);
	const by = (pct: number): number => PAD_T + (1 - pct / 100) * (CH - PAD_T - PAD_B);
	const curve = (t: Record<FinisherBandName, { win_pct: number }>): string =>
		FINISHER_BANDS.map((b, i) => `${bx(i)},${by(t[b].win_pct)}`).join(' ');

	/** x of a fatal-rate boundary (10 → between band 1 and 2; 12 → band 3's left edge) */
	function cliffX(rate: number): number {
		// band lower edges: 6, 8, 10, 12 → boundary sits at the band whose lo == rate
		const i = FINISHER_BANDS.findIndex((b) => parseInt(b, 10) === rate);
		return i >= 0 ? bx(i) : bx(FINISHER_BANDS.length - 1);
	}

	const bandHot = $derived(reduced || step >= 2);
	const cliffOn = $derived(reduced || step >= 3);

	/* tap a band → its raw cohort read */
	let tappedBand = $state<FinisherBandName | null>(null);
</script>

<div class="pin" class:active>
	{#if early && recent && head}
		<div class="chart-wrap" class:shown={reduced || progress >= 0.06}>
			<span class="c-title">chases with five overs left · runs an over still needed</span>
			<svg viewBox="0 0 {CW} {CH}" aria-hidden="true">
				<!-- the 50-in-100 waterline (where a chase becomes a loser) -->
				<line class="half" x1={PAD_L} y1={by(50)} x2={CW - PAD_R} y2={by(50)} />
				<text class="half-lab" x={PAD_L + 0.5} y={by(50) - 1.2}>50 in 100</text>

				<!-- the 8-10 band highlight -->
				{#if bandHot}
					<rect
						class="band"
						x={bx(1) - 4}
						y={PAD_T - 2}
						width="8"
						height={CH - PAD_T - PAD_B + 4}
						rx="1.5"
					/>
				{/if}

				<!-- the cliffs (data-derived fatal rates), old then new -->
				{#if cliffOn && cliffEarly !== null && cliffRecent !== null}
					<line class="cliff old" x1={cliffX(cliffEarly)} y1={PAD_T} x2={cliffX(cliffEarly)} y2={CH - PAD_B} />
					<line class="cliff new" x1={cliffX(cliffRecent)} y1={PAD_T} x2={cliffX(cliffRecent)} y2={CH - PAD_B} />
				{/if}

				<polyline class="era ghost" points={curve(early)} />
				<polyline class="era bright" points={curve(recent)} />

				{#each FINISHER_BANDS as b, i (b)}
					<circle class="pt ghost" cx={bx(i)} cy={by(early[b].win_pct)} r="1" />
					<circle class="pt bright" cx={bx(i)} cy={by(recent[b].win_pct)} r="1" />
					<text class="x-lab" x={bx(i)} y={CH - 3}>{b}</text>
				{/each}
			</svg>

			<!-- tap targets per band (adds depth; the captions carry the point) -->
			<div class="band-taps">
				{#each FINISHER_BANDS as b (b)}
					<button
						class="band-tap"
						onclick={() => (tappedBand = tappedBand === b ? null : b)}
						aria-label="Read the {b} an over cohort"
					>{b}</button>
				{/each}
			</div>

			{#if bandHot}
				<div class="sub-labels">
					<span class="sl ghost">2008-2010: {early['8-10'].wins} of {early['8-10'].n} such chases</span>
					<span class="sl bright">2023-2026: {recent['8-10'].wins} of {recent['8-10'].n} such chases</span>
				</div>
			{/if}

			{#if tappedBand}
				<div class="tap-read">
					needing {tappedBand} an over: {early[tappedBand].wins} of {early[tappedBand].n} came off
					then · {recent[tappedBand].wins} of {recent[tappedBand].n} now
				</div>
			{/if}
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					One more repricing, the one that invented a job. This chart reads chases with five overs
					left. Along the bottom, how many an over you still need. The height, how many of a
					hundred such chases got home.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-finisher')}
						aria-label="How the chase cohorts are counted">ⓘ</button
					>
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Needing eight to ten an over with five overs left used to be a scrap: about
					{head ? in100(head.early.win_pct) : 55} in a hundred got home. Now it is
					{head ? in100(head.recent.win_pct) : 85}. What used to be a collapse waiting to happen
					is the finisher's office.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					The rate that kills a chase moved too. The old cliff sat around
					{cliffEarly ?? 10} an over. The new one sits around {cliffRecent ?? 12}. Past twelve,
					chases still die like they always did. The cliff did not crumble. It moved.
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

	.chart-wrap {
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.45rem;
		width: min(36rem, 92vw);
		padding: 0.9rem 1rem;
		border-radius: 16px;
		background: rgba(10, 14, 24, 0.78);
		border: 1px solid rgba(151, 161, 184, 0.26);
		opacity: 0;
	}

	.chart-wrap.shown {
		opacity: 1;
	}

	.c-title {
		font-size: 0.64rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--ink-dim);
		text-align: center;
	}

	svg {
		width: 100%;
		height: auto;
	}

	.half {
		stroke: rgba(151, 161, 184, 0.4);
		stroke-dasharray: 2 2.5;
		stroke-width: 0.35;
	}

	.half-lab {
		font-size: 2.6px;
		fill: var(--ink-dim);
		letter-spacing: 0.05em;
	}

	.band {
		fill: rgba(255, 209, 102, 0.12);
		stroke: rgba(255, 209, 102, 0.5);
		stroke-width: 0.3;
	}

	.cliff {
		stroke-width: 0.45;
		stroke-dasharray: 1.6 1.6;
	}

	.cliff.old {
		stroke: rgba(151, 161, 184, 0.7);
	}

	.cliff.new {
		stroke: rgba(255, 209, 102, 0.85);
	}

	.era {
		fill: none;
		stroke-width: 0.8;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	.era.ghost {
		stroke: rgba(151, 161, 184, 0.75);
	}

	.era.bright {
		stroke: #ffd166;
		filter: drop-shadow(0 0 3px rgba(255, 209, 102, 0.45));
	}

	.pt.ghost {
		fill: rgba(151, 161, 184, 0.9);
	}

	.pt.bright {
		fill: #ffd166;
	}

	.x-lab {
		font-size: 3px;
		fill: var(--ink-dim);
		text-anchor: middle;
		font-variant-numeric: tabular-nums;
	}

	.band-taps {
		pointer-events: auto;
		display: flex;
		gap: 0.4rem;
	}

	.band-tap {
		min-height: 44px;
		min-width: 44px;
		padding: 0.2rem 0.6rem;
		border-radius: 999px;
		border: 1px solid rgba(151, 161, 184, 0.35);
		background: none;
		color: var(--ink-dim);
		font-size: 0.72rem;
		font-weight: 700;
		cursor: pointer;
		font-variant-numeric: tabular-nums;
	}

	.band-tap:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.sub-labels {
		display: flex;
		gap: 1.1rem;
		flex-wrap: wrap;
		justify-content: center;
	}

	.sl {
		font-size: 0.7rem;
		font-variant-numeric: tabular-nums;
	}

	.sl.ghost {
		color: var(--ink-dim);
	}

	.sl.bright {
		color: #ffd166;
	}

	.tap-read {
		font-size: 0.74rem;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
		text-align: center;
	}

	/* curve captions live TOP-LEFT (the curves fan up-and-right) */
	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 8vh;
		max-width: min(24rem, 36vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
	}

	/* no invisible ⓘ tap target during the mobile clear gap */
	.caption-slot.gap .dagger {
		pointer-events: none;
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

	/* small desktops (641-1200px): the centred chart card grazes the top-left
	   caption at ~1024×768, so it narrows and drops — provable no-overlap
	   (QA §4 smallest-desktop assertion) */
	@media (max-width: 1200px) and (min-width: 641px) {
		.chart-wrap {
			width: min(30rem, 88vw);
			top: 56%;
		}
	}

	@media (max-width: 640px) {
		.chart-wrap {
			top: 42%;
			width: 94vw;
			padding: 0.6rem 0.5rem;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}
	}
</style>
