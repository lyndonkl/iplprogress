<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal, captionRevealActive } from '$lib/story/captionReveal.svelte';
	import {
		loadCh5Data,
		setRailIndices,
		scrubBallFloat,
		scrubStep,
		SCRUB_BOUNDS,
		RAIL_SLOTS,
		RAIL_Y,
		swing100,
		win100,
		type Ch5Data,
		type ScrubBall
	} from './data';
	import Worm from './Worm.svelte';

	/**
	 * C5-3 — THE SCRUB (set piece #2 of 2, the chapter's whole scrub budget).
	 * Six balls, ball by ball: the active chip enlarges, its outcome plays, and
	 * the worm draws its next segment beneath. Scrubbing back replays in reverse
	 * (state, not video — everything is a pure function of scroll progress). The
	 * rest of the field holds hard-dimmed behind the rail (the §20 overrail,
	 * engaged at progress 1 through the whole scene). Every chip fact and every
	 * worm value binds to scenes/ch5.json — the swing sizes live on the CHIPS,
	 * the captions carry only the state numbers (one idea per step).
	 *
	 * MOBILE (read-then-watch, §17.6): the ball pointer is GAP-ALIGNED — the
	 * delivery and its worm segment play in each step's clear gap, after the
	 * caption has been read and cleared, never under it. The caption STEP
	 * thresholds never move (scrubStep stays un-aligned), so captions and
	 * SCRUB_BOUNDS agree on both variants.
	 *
	 * REDUCED MOTION (mandated fallback): the six-panel sequential strip — one
	 * DOM panel per ball with its worm segment beneath, plus the completed-worm
	 * end beat (which carries the thesis line and the ⓘ). The stepped captions
	 * are SUPPRESSED under reduced motion (design audit: they rendered on top
	 * of the strip's first panels; every beat they carried is on the panels).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const gapAligned = $derived(captionRevealActive() && !reduced);
	const ballFloat = $derived(scrubBallFloat(progress, gapAligned));
	const step = $derived(scrubStep(progress));
	const reveal = $derived(
		captionReveal(progress, SCRUB_BOUNDS[step - 1], SCRUB_BOUNDS[step], { reduced })
	);

	let ch5 = $state<Ch5Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh5Data().then((d) => {
			if (!alive) return;
			ch5 = d;
			setRailIndices(d); // pipeline-emitted indices (dev cross-checks columnar)
		});
		return () => {
			alive = false;
		};
	});

	const balls = $derived(ch5?.scrub.balls ?? []);
	/** how many balls have fully played (0..6) */
	const played = $derived(Math.min(6, Math.floor(ballFloat)));
	/** the ball whose beat we are in (1..6), or null at the end beat */
	const activeBall = $derived(step <= 6 ? step : null);

	/** a tapped chip re-opens that ball's detail (only balls that have played) */
	let tapped = $state<number | null>(null);
	$effect(() => {
		void step; // moving to a new beat clears the re-opened detail
		tapped = null;
	});
	const detailBall = $derived.by((): ScrubBall | null => {
		if (balls.length === 0) return null;
		if (tapped !== null) return balls[tapped - 1] ?? null;
		if (activeBall !== null && ballFloat > 0.05) return balls[activeBall - 1] ?? null;
		return null;
	});

	/** the state AFTER ball i (1-based): the next ball's before-state, else the result */
	function afterState(i: number): { needed: number; ballsLeft: number } | null {
		if (i >= 6 || balls.length < 6) return null;
		const nxt = balls[i];
		return { needed: nxt.needed_before, ballsLeft: nxt.balls_left_before };
	}

	function outcomeText(b: ScrubBall): string {
		if (b.wicket && b.wicket.kind === 'run out')
			return `${b.runs_total} run, ${b.wicket.player_out} run out`;
		if (b.wicket) return `${b.wicket.player_out} ${b.wicket.kind}`;
		return `${b.runs_total} run${b.runs_total === 1 ? '' : 's'}`;
	}

	function chipBadge(b: ScrubBall): string {
		if (b.wicket) return 'W';
		return String(b.runs_total);
	}

	/* skip control: jumps the scroll to the end beat (nobody is gated on the scrub) */
	let endAnchor = $state<HTMLElement | null>(null);
	function skipOver(): void {
		endAnchor?.scrollIntoView({ behavior: 'auto', block: 'start' });
	}
</script>

<!-- in-flow scroll target for "skip the over" (≈ progress 0.9, the end beat) -->
<div class="end-anchor" bind:this={endAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	{#if !reduced && balls.length === 6}
		<!-- the six ball chips at the rail slots (GL balls sit beneath the same fractions) -->
		<div class="chips">
			{#each balls as b, i (b.ball)}
				{@const isActive = activeBall === i + 1 || tapped === i + 1}
				{@const isPlayed = i < played || (activeBall === i + 1 && ballFloat - i > 0.6)}
				<button
					class="chip"
					class:active={isActive}
					class:played={isPlayed}
					class:dim={step === 7}
					style="left: {RAIL_SLOTS[i][0] * 100}%; top: {RAIL_Y * 100}%;"
					disabled={!isPlayed && activeBall !== i + 1}
					onclick={() => (tapped = i + 1)}
					aria-label="Ball {b.label}: {outcomeText(b)}"
				>
					<span class="ball-label">{b.label}</span>
					{#if isPlayed}
						<span class="badge" class:wicket={b.wicket !== null}>{chipBadge(b)}</span>
						<span class="swing" class:down={b.wpa < -0.005}>{swing100(b.wpa)} in 100</span>
					{:else}
						<span class="badge pending">·</span>
					{/if}
				</button>
			{/each}
		</div>

		<Worm {balls} reveal={ballFloat} bright={step === 7} />

		<!-- the active ball's detail card (names + numbers are DOM; the chip is the label) -->
		{#if detailBall && step <= 6}
			<div class="detail">
				<span class="who">{detailBall.batter} vs {detailBall.bowler}</span>
				<span class="what">{outcomeText(detailBall)}</span>
				<span class="state">
					needed {detailBall.needed_before} off {detailBall.balls_left_before} before this ball
				</span>
				<span class="d-swing" class:down={detailBall.wpa < -0.005}
					>the swing: {swing100(detailBall.wpa)} in 100</span
				>
			</div>
		{/if}

		{#if step < 7}
			<button class="skip" onclick={skipOver}>Skip the over →</button>
		{/if}
	{/if}

	{#if reduced && balls.length === 6 && ch5}
		<!-- REDUCED MOTION: the six-panel sequential strip (the mandated fallback) -->
		<div class="strip" tabindex="-1">
			{#each balls as b, i (b.ball)}
				<div class="panel">
					<span class="p-label">{b.label} · {b.batter} vs {b.bowler}</span>
					<span class="p-what">{outcomeText(b)}</span>
					<span class="p-state">
						{#if afterState(i + 1)}
							{afterState(i + 1)?.needed} needed off {afterState(i + 1)?.ballsLeft} after it
						{:else}
							{ch5.scrub.match.result_text}
						{/if}
					</span>
					<svg class="p-worm" viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">
						<line x1="0" y1="20" x2="100" y2="20" class="p-mid" />
						<line
							x1="8"
							y1={40 - b.wp_before * 40}
							x2="92"
							y2={40 - b.wp_after * 40}
							class="p-seg"
						/>
					</svg>
					<span class="p-swing">{win100(b.wp_before)} → {win100(b.wp_after)} in 100</span>
				</div>
			{/each}
			<div class="panel end-panel">
				<span class="p-what">
					The whole over, drawn as one line: {win100(balls[0].wp_before)} in 100 down to zero in
					six balls. Every one of those lurches has a size. That size is what a ball is worth.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-over')}
						aria-label="How the per-ball swings are read">ⓘ</button
					>
				</span>
			</div>
		</div>
	{/if}

	<!-- the stepped captions belong to the scrubbed rail; under reduced motion
	     the six-panel strip IS the scene and the captions stay out of its way -->
	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if !reduced && balls.length === 6 && ch5}
			{#if step === 1}
				<div class="scene-card"><p>
					Malinga to Watson. A single. {afterState(1)?.needed ?? 8} needed off
					{afterState(1)?.ballsLeft ?? 5}. The worm barely moves. A quiet single does not scare a
					chase like this.
				</p></div>
			{:else if step === 2}
				<div class="scene-card"><p>
					Jadeja knocks another single. {afterState(2)?.needed ?? 7} off
					{afterState(2)?.ballsLeft ?? 4}. The worm slips a touch. Still Chennai's game.
				</p></div>
			{:else if step === 3}
				<div class="scene-card"><p>
					Watson cuts hard and they run two. {afterState(3)?.needed ?? 5} off
					{afterState(3)?.ballsLeft ?? 3}. The worm holds its ground. This chase is still on
					course.
				</p></div>
			{:else if step === 4}
				<div class="scene-card"><p>
					One run, and Watson dives for a second that is not there. Run out.
					{afterState(4)?.needed ?? 4} off {afterState(4)?.ballsLeft ?? 2}, and the set batter is
					gone. Watch the worm lurch.
				</p></div>
			{:else if step === 5}
				<div class="scene-card"><p>
					Thakur squeezes two more. {afterState(5)?.needed ?? 2} off
					{afterState(5)?.ballsLeft ?? 1}. The worm stays put. A whole final now fits inside
					one delivery.
				</p></div>
			{:else if step === 6}
				<div class="scene-card"><p>
					Malinga drops the slower ball in full. Thakur is hit on the pad. Out. Chennai finish
					one run short, and the worm plunges to nothing. Mumbai are champions by the width of a
					single delivery.
				</p></div>
			{:else}
				<div class="scene-card"><p>
					Now look at the whole worm. Look how far it travelled in six balls. Every one of those
					lurches has a size. That size is what a ball is worth.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-over')}
						aria-label="How the per-ball swings are read">ⓘ</button
					>
				</p></div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.end-anchor {
		position: absolute;
		top: 89%;
		left: 0;
		width: 1px;
		height: 1px;
	}

	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
	}

	.pin.active {
		visibility: visible;
	}

	.chips {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.chip {
		pointer-events: auto;
		position: absolute;
		transform: translate(-50%, -50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
		min-width: 44px;
		min-height: 44px;
		padding: 2.6rem 0.3rem 0.3rem;
		border: none;
		background: none;
		color: var(--ink);
		cursor: pointer;
		transition: transform 180ms ease;
	}

	.chip.active {
		transform: translate(-50%, -50%) scale(1.22);
	}

	.chip.dim {
		opacity: 0.55;
	}

	.chip:disabled {
		cursor: default;
	}

	.chip:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
		border-radius: 8px;
	}

	.ball-label {
		font-size: 0.68rem;
		font-weight: 700;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
	}

	.badge {
		display: grid;
		place-items: center;
		width: 1.5rem;
		height: 1.5rem;
		border-radius: 50%;
		font-size: 0.85rem;
		font-weight: 800;
		background: rgba(232, 236, 245, 0.14);
		border: 1px solid rgba(232, 236, 245, 0.35);
		font-variant-numeric: tabular-nums;
	}

	.badge.wicket {
		background: rgba(255, 92, 92, 0.22);
		border-color: rgba(255, 92, 92, 0.7);
		color: #ff9c9c;
	}

	.badge.pending {
		opacity: 0.4;
	}

	.swing {
		font-size: 0.62rem;
		font-weight: 700;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
		white-space: nowrap;
	}

	.swing.down {
		color: #ff9c9c;
	}

	.detail {
		position: absolute;
		left: 50%;
		top: 5vh;
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.18rem;
		padding: 0.55rem 1rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.82);
		border: 1px solid rgba(151, 161, 184, 0.3);
		text-align: center;
		max-width: 92vw;
	}

	.who {
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.what {
		font-size: 1.05rem;
		font-weight: 800;
	}

	.state {
		font-size: 0.78rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.d-swing {
		font-size: 0.85rem;
		font-weight: 700;
		color: #ffd166;
		font-variant-numeric: tabular-nums;
	}

	.d-swing.down {
		color: #ff9c9c;
	}

	.skip {
		pointer-events: auto;
		position: absolute;
		top: 12vh;
		right: 4vw;
		min-height: 44px;
		padding: 0.5rem 0.95rem;
		border-radius: 999px;
		border: 1px solid rgba(151, 161, 184, 0.45);
		background: rgba(10, 14, 24, 0.7);
		color: var(--ink);
		font-size: 0.85rem;
		font-weight: 600;
		cursor: pointer;
	}

	.skip:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.strip {
		pointer-events: auto;
		position: absolute;
		inset: 8vh 4vw;
		overflow-y: auto;
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
		gap: 0.7rem;
		align-content: start;
	}

	.panel {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		padding: 0.7rem 0.85rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.82);
		border: 1px solid rgba(151, 161, 184, 0.28);
	}

	.p-label {
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.p-what {
		font-size: 0.95rem;
		font-weight: 700;
	}

	.p-state {
		font-size: 0.78rem;
		color: var(--ink-dim);
	}

	.p-worm {
		width: 100%;
		height: 2.2rem;
	}

	.p-mid {
		stroke: rgba(151, 161, 184, 0.25);
		stroke-dasharray: 3 4;
		vector-effect: non-scaling-stroke;
	}

	.p-seg {
		stroke: #ffd166;
		stroke-width: 2.2;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.p-swing {
		font-size: 0.75rem;
		font-weight: 700;
		color: #ffd166;
		font-variant-numeric: tabular-nums;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 12vh;
		max-width: min(24rem, 38vw);
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

	/* small desktops (641-1200px): the centred detail card collides with the
	   top-left caption box, so it right-anchors (still above the rail) and the
	   skip control drops below it — provable no-overlap at 1024×768 (QA §4) */
	@media (max-width: 1200px) and (min-width: 641px) {
		.detail {
			left: auto;
			right: 3vw;
			transform: none;
			align-items: flex-end;
			text-align: right;
		}

		.skip {
			top: 26vh;
		}
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px));
		}

		.skip {
			top: auto;
			bottom: max(24vh, calc(env(safe-area-inset-bottom) + 168px));
			right: 3vw;
			font-size: 0.78rem;
		}

		.detail {
			top: max(3vh, calc(env(safe-area-inset-top) + 52px));
			padding: 0.4rem 0.7rem;
			width: 88vw;
		}

		.what {
			font-size: 0.9rem;
		}

		.chip {
			padding-top: 2rem;
		}

		.swing {
			font-size: 0.55rem;
		}

		.strip {
			inset: 7vh 3vw;
			grid-template-columns: 1fr;
		}
	}

	/* the narrowest phones: chip swing labels ("−5 in 100", nowrap) graze their
	   neighbours at a ~45px slot pitch — the detail card still carries the swing */
	@media (max-width: 360px) {
		.swing {
			display: none;
		}
	}
</style>
