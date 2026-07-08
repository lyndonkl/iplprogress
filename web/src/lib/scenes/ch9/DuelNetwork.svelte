<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import DuelField from './DuelField.svelte';
	import DuelStrands from './DuelStrands.svelte';
	import ReplayStrip from './ReplayStrip.svelte';
	import { pickCaptionCorner, cornerStyle, isNarrowViewport } from './captionCorner.svelte';
	import { loadCh9Data, heroDuel, longDuels, int, type Ch9Data, type Duel } from './data';

	/**
	 * C9-3, HERO 1: the Duel Network (the rivalries that lasted). The held web plus
	 * the focus scalars: the dust nearly vanishes, the ~1,459 shorter duels recede to
	 * a faint neutral gray, and the 232 rivalries that ran eight seasons or longer
	 * hold full red/blue. The headline pair, Kohli vs Jadeja, is found by three
	 * channels (extra width + a pulsing knot + a pinned leader-line callout), 160
	 * balls across 14 seasons, and Jadeja edged it (blue). Tap any strand to play it
	 * back ball by ball. Everything is a description, never a cause.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	let ch9 = $state<Ch9Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh9Data().then((d) => {
			if (alive) ch9 = d;
		});
		return () => {
			alive = false;
		};
	});

	/* five steps: orient the long ones / the headline pair / who won / how common / tap */
	const step = $derived(
		progress < 0.18 ? 1 : progress < 0.4 ? 2 : progress < 0.62 ? 3 : progress < 0.82 ? 4 : 5
	);
	const BOUNDS = [0, 0.18, 0.4, 0.62, 0.82, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

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

	const hero = $derived(ch9 ? heroDuel(ch9) : null);
	const heroId = $derived(hero ? hero.id : null);
	const longs = $derived(ch9 ? longDuels(ch9) : []);
	const longCount = $derived(longs.length);
	/* mobile caps the bright tier to the strongest ~60 (a sub-fingertip tangle otherwise) */
	const longIds = $derived(
		(isNarrowViewport() ? longs.slice(0, 60) : longs).map((x) => x.id)
	);

	/* the two-step mobile drill (tap a hub -> isolate that player's strands) + tap replay */
	let selectedDuel = $state<number | null>(null);
	let nodeFocus = $state<number | null>(null);

	const focusIds = $derived.by<number[] | null>(() => {
		if (selectedDuel != null) return [selectedDuel];
		if (nodeFocus != null && ch9) {
			return ch9.duel_web.duels
				.filter((x) => x.a === nodeFocus || x.b === nodeFocus)
				.map((x) => x.id);
		}
		if (step === 2 || step === 3) return heroId != null ? [heroId] : null;
		return longIds;
	});

	/* the scripted default: step 5 opens the Kohli-Jadeja strip without a tap */
	const replayId = $derived(selectedDuel ?? (step >= 5 || reduced ? heroId : null));
	const replayDuel = $derived<Duel | null>(
		ch9 && replayId != null ? (ch9.duel_web.duels[replayId] ?? null) : null
	);

	function onTapDuel(id: number): void {
		selectedDuel = id;
		nodeFocus = null;
	}
	function onTapNode(i: number): void {
		nodeFocus = i;
		selectedDuel = null;
	}
</script>

<div class="pin" class:active>
	<DuelField {field} legend={true} footnoteId="ch9-duel" />
	<DuelStrands
		{field}
		{reduced}
		{progress}
		{active}
		topN={isNarrowViewport() ? 42 : 60}
		{focusIds}
		{heroId}
		showHubLabels={true}
		hubLabelCount={isNarrowViewport() ? 3 : 5}
		onTapDuel={step >= 5 || reduced ? onTapDuel : undefined}
		onTapNode={isNarrowViewport() && (step >= 5 || reduced) ? onTapNode : undefined}
	/>

	{#if replayDuel}
		<div class="replay-slot">
			<ReplayStrip
				replay={ch9?.replays[replayDuel.id] ?? null}
				summary={{
					bat: replayDuel.bat,
					bowl: replayDuel.bowl,
					balls: replayDuel.balls,
					runs: replayDuel.runs,
					dis: replayDuel.dis,
					span: replayDuel.span
				}}
				onClose={selectedDuel != null ? () => (selectedDuel = null) : undefined}
			/>
		</div>
	{/if}

	<div class="caption-slot" style="{capStyle}; --reveal: {reveal};">
		{#if hero}
			{#if step === 1}
				<div class="scene-card">
					<p>
						Now the rivalries that lasted. The longest strands light up: the same two players, meeting
						season after season, for years.
					</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>
						Take Kohli and Jadeja. {hero.balls} balls at each other, spread across {hero.seasons} seasons.
						A rivalry older than most teams.
					</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>
						And Jadeja edged it. He got Kohli out {hero.dis} times and kept him quiet, so the strand
						runs blue. The bowler came out on top.
					</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>And it is not a one-off. {int(longCount)} of these rivalries have run eight seasons or longer.</p>
				</div>
			{:else}
				<div class="scene-card interactive">
					<p>
						Tap any strand to play it back, ball by ball. Every meeting these two ever had, in order.
					</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch9-duel')}>ⓘ how we read a rivalry</button>
				</div>
			{/if}
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

	.replay-slot {
		position: absolute;
		left: 50%;
		bottom: 4vh;
		transform: translateX(-50%);
		width: max-content;
		max-width: 94vw;
		z-index: 3;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		bottom: 8vh;
		max-width: min(25rem, 42vw);
		opacity: var(--reveal, 1);
	}

	.fn {
		margin-top: 0.5rem;
		min-height: 40px;
		padding: 0.2rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.78rem;
		font-weight: 600;
		text-align: left;
		cursor: pointer;
	}

	.fn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			right: auto;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}

		.replay-slot {
			bottom: auto;
			top: 16vh;
		}
	}
</style>
