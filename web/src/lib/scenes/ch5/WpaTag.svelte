<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh5Data, IPL_EARLY, IPL_RECENT, in100, int, type Ch5Data } from './data';

	/**
	 * C5-4 — HERO 1: every ball gets the tag (WPA per ball + the 170-189
	 * repricing). Step 1 is the bridge from the scrub: the biggest-swing balls in
	 * history lift out of the field (the §21 'wpa' subset highlight, declared on
	 * this scene's fieldState — the threshold is a scene parameter, the matching
	 * is the shipped wpa.u8 byte). Steps 2-3 are the era-stamp argument: the
	 * 170-189 waffle pair, RATE-framed (lit dots = the share out of 100 that went
	 * on to win, real match counts printed on-panel — guardrail 4). All values
	 * bind to scenes/ch5.json defended_band.raw; the artifact wins (73/39 on
	 * 41/54 matches, not the teaser's 74/38). The highlight RELEASES as step 2
	 * arrives (index.ts dynamicState) so the lift never competes with the
	 * centred waffles for attention.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived(progress < 0.38 ? 1 : progress < 0.68 ? 2 : 3);
	const BOUNDS = [0, 0.38, 0.68, 1] as const;
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

	const early = $derived(ch5?.defended_band.raw[IPL_EARLY] ?? null);
	const recent = $derived(ch5?.defended_band.raw[IPL_RECENT] ?? null);
	const band = $derived(ch5?.defended_band.band ?? '170-189');

	const leftOn = $derived(reduced || step >= 2);
	const rightOn = $derived(reduced || step >= 3);
</script>

{#snippet waffle(label: string, lit: number, n: number, on: boolean)}
	<div class="panel" class:on>
		<span class="p-era">{label}</span>
		<svg viewBox="0 0 100 100" aria-hidden="true">
			{#each Array.from({ length: 100 }) as _, i (i)}
				{@const col = i % 10}
				{@const row = Math.floor(i / 10)}
				<circle
					cx={5 + col * 10}
					cy={95 - row * 10}
					r="3.1"
					class="dot"
					class:lit={on && i < lit}
				/>
			{/each}
		</svg>
		<span class="p-num">{on ? `${lit} in 100 won` : '· · ·'}</span>
		<span class="p-n">from {int(n)} matches</span>
	</div>
{/snippet}

<div class="pin" class:active>
	{#if early && recent}
		<div class="waffles" class:shown={reduced || step >= 2}>
			<span class="w-title">batting first with {band} on the board</span>
			<div class="pair">
				{@render waffle('2008-2010', in100(early.pct), early.n, leftOn)}
				{@render waffle('2023-2026', in100(recent.pct), recent.n, rightOn)}
			</div>
		</div>
	{/if}

	<div class="caption-slot" class:gap={reveal < 0.5} style:--reveal={reveal}>
		{#if step === 1}
			<!-- the storyboard's in-line era-stamp qualification is restored (the
			     endgame worm pools every last over ever bowled — ch5-wpa carries
			     the fine print); the lift sentence is trimmed to keep 45 words -->
			<div class="scene-card">
				<p>
					We priced six balls by how far each moved the win chance. Now price them all. Every
					delivery here carries that tag, worked out from its own era's matches, and in the
					tightest endgames, from every last over ever bowled. The biggest swings lifted out.
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ch5-wpa')}
						aria-label="How every ball's tag is computed">ⓘ</button
					>
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Here is why the era stamp matters. Of every hundred teams batting first with 170 to 189
					on the board in the league's first three seasons, {early ? in100(early.pct) : 73} went
					on to win.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					The same scoreboard in the last four seasons wins {recent ? in100(recent.pct) : 39} times
					in a hundred. The total did not change. The water around it did. That is why every price
					in this chapter comes stamped with its era.
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

	.waffles {
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.8rem;
		opacity: 0;
	}

	.waffles.shown {
		opacity: 1;
	}

	.w-title {
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--ink-dim);
		text-align: center;
	}

	.pair {
		display: flex;
		gap: clamp(1rem, 4vw, 2.6rem);
	}

	.panel {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.4rem;
		padding: 0.8rem;
		border-radius: 14px;
		background: rgba(10, 14, 24, 0.72);
		border: 1px solid rgba(151, 161, 184, 0.25);
		opacity: 0.35;
	}

	.panel.on {
		opacity: 1;
	}

	.panel svg {
		width: clamp(8.5rem, 22vw, 13rem);
		height: clamp(8.5rem, 22vw, 13rem);
	}

	.dot {
		fill: rgba(151, 161, 184, 0.22);
	}

	.dot.lit {
		fill: #ffd166;
	}

	.p-era {
		font-size: 0.8rem;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
	}

	.p-num {
		font-size: 1rem;
		font-weight: 800;
		color: #ffd166;
		font-variant-numeric: tabular-nums;
	}

	.p-n {
		font-size: 0.72rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 12vh;
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

	@media (max-width: 640px) {
		.waffles {
			top: 42%;
			width: 94vw;
		}

		.pair {
			width: 100%;
			justify-content: center;
		}

		.panel svg {
			width: clamp(7rem, 38vw, 9rem);
			height: clamp(7rem, 38vw, 9rem);
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
