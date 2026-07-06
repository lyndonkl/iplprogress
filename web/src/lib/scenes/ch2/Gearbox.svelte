<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh2Data, fmt1, IPL_EARLY, IPL_MODERN, type Ch2Data } from './data';

	/**
	 * C2-5 — The deleted gearbox (supporting: Gear-Shift Detector). Worm-space
	 * holds, dimmed one stop; an annotation-plane beat (no re-sort). Two crisp
	 * exemplar worm SHAPES drawn in the figure channel (dark casing + brighter
	 * stroke): a 2008 two-act innings that crawls then kinks steeper (build →
	 * launch), and a 2026 flat-max innings — one straight steep gear from ball
	 * one. The shapes are an ILLUSTRATION of the taxonomy (labelled as such,
	 * storyboard §5.5); every NUMBER comes from ch2.json gearshift.bands.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.34) return 1;
		if (progress < 0.66) return 2;
		return 3;
	});
	const twoActOn = $derived(reduced || step >= 1);
	const flatOn = $derived(reduced || step >= 2);

	// mobile "read, then watch" (CONTRACT §17): caption fades in for the read beat,
	// then to a clear gap so the two gearbox illustration shapes are unobstructed.
	// Desktop + reduced motion → 1 (persistent caption, byte-identical).
	const BOUNDS = [0, 0.34, 0.66, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));

	let ch2 = $state<Ch2Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh2Data().then((d) => {
			if (alive) ch2 = d;
		});
		return () => {
			alive = false;
		};
	});

	/* the headline pair — two-act share of long innings (from the artifact) */
	const twoActEarly = $derived(ch2 ? ch2.gearshift.bands[IPL_EARLY].two_act_share_pct : null);
	const twoActModern = $derived(ch2 ? ch2.gearshift.bands[IPL_MODERN].two_act_share_pct : null);

	/* illustrative shapes (schematic — NOT field points; see §5.5). A two-act
	   worm crawls then kinks steeper; a flat-max worm is one straight steep gear. */
	const VB = 200;
	const twoAct = '14,186 40,168 66,150 92,132 118,96 152,52 186,14';
	const twoActKinkX = 92;
	const flatMax = '14,186 186,14';
</script>

<div class="pin" class:reduced class:active>
	{#if ch2}
		<div class="panel-slot">
			<div class="panel">
				<p class="panel-title">The shape of an innings <span class="illus">(illustration)</span></p>
				<div class="shapes">
					<figure class="shape">
						<svg viewBox="0 0 {VB} {VB}" role="img" aria-label="A 2008 innings that crawls, then kinks upward into a steeper climb">
							<line x1="8" y1="192" x2="192" y2="192" class="axis" />
							<line x1="8" y1="192" x2="8" y2="8" class="axis" />
							<!-- build / launch split marker -->
							<line x1={twoActKinkX} y1="8" x2={twoActKinkX} y2="192" class="split" class:on={twoActOn} />
							<polyline points={twoAct} class="casing" class:on={twoActOn} />
							<polyline points={twoAct} class="stroke build" class:on={twoActOn} />
						</svg>
						<figcaption><span class="tag build-tag">build</span> then <span class="tag launch-tag">launch</span>, 2008</figcaption>
					</figure>
					<figure class="shape">
						<svg viewBox="0 0 {VB} {VB}" role="img" aria-label="A 2026 innings: one straight steep line from the first ball">
							<line x1="8" y1="192" x2="192" y2="192" class="axis" />
							<line x1="8" y1="192" x2="8" y2="8" class="axis" />
							<polyline points={flatMax} class="casing" class:on={flatOn} />
							<polyline points={flatMax} class="stroke launch" class:on={flatOn} />
						</svg>
						<figcaption><span class="tag launch-tag">one gear: flat out</span>, 2026</figcaption>
					</figure>
				</div>
			</div>
		</div>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					The old T20 innings had <strong>gears</strong>. See off the bowling, build, then launch.
					You can watch it on the left: the line crawls, then bends steeply up.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					The modern innings has <strong>one gear: flat out.</strong> From ball one, straight into
					the launch.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					Innings that shifted up a gear late were <strong>a third</strong> of the long ones once
					(<strong>{twoActEarly !== null ? fmt1(twoActEarly) : '-'}%</strong>). Now
					<strong>a quarter</strong> (<strong>{twoActModern !== null ? fmt1(twoActModern) : '-'}%</strong>).
					<button class="dagger" onclick={() => footnotesOpen.set('gear-shift')} aria-label="How we counted the gears">ⓘ</button>
					The build-up went with the man who used to play it.
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

	.panel-slot {
		position: absolute;
		top: 7vh;
		left: 50%;
		transform: translateX(-50%);
		width: min(560px, 94vw);
	}

	.panel {
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 12px;
		background: rgba(11, 14, 20, 0.74);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
		padding: 0 0.7rem 0.7rem;
		overflow: hidden;
	}

	.panel-title {
		margin: 0 -0.7rem 0.4rem;
		padding: 0.5rem 1rem;
		background: rgba(232, 236, 245, 0.05);
		font-size: 0.82rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		color: var(--ink);
	}

	.illus {
		font-weight: 500;
		letter-spacing: 0.02em;
		color: var(--ink-dim);
	}

	.shapes {
		display: flex;
		gap: 0.8rem;
	}

	.shape {
		margin: 0;
		flex: 1;
		text-align: center;
	}

	.shape svg {
		width: 100%;
		height: auto;
	}

	.shape figcaption {
		margin-top: 0.2rem;
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.axis {
		stroke: rgba(232, 236, 245, 0.24);
		stroke-width: 1.5;
	}

	.split {
		stroke: rgba(232, 236, 245, 0.18);
		stroke-width: 1;
		stroke-dasharray: 3 4;
		opacity: 0;
		transition: opacity 500ms ease;
	}

	.split.on {
		opacity: 1;
	}

	polyline {
		fill: none;
		stroke-linejoin: round;
		stroke-linecap: round;
		opacity: 0;
		transition: opacity 600ms ease;
	}

	polyline.on {
		opacity: 1;
	}

	.casing {
		stroke: rgba(6, 9, 14, 0.92);
		stroke-width: 9;
	}

	.stroke {
		stroke-width: 3;
	}

	.build {
		stroke: #ffd477;
	}

	.launch {
		stroke: #ff8a4c;
	}

	.tag {
		font-weight: 700;
	}

	.build-tag {
		color: #ffd477;
	}

	.launch-tag {
		color: #ff8a4c;
	}

	.pin.reduced polyline,
	.pin.reduced .split {
		transition: none;
	}

	@media (prefers-reduced-motion: reduce) {
		polyline,
		.split {
			transition: none;
		}
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 10vh;
		max-width: min(30rem, 84vw);
		opacity: var(--reveal, 1); /* read-then-watch (CONTRACT §17); 1 on desktop */
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
			top: 5vh;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(72px, calc(env(safe-area-inset-bottom) + 60px));
		}
	}
</style>
