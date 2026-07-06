<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { loadCh3Data, iplHull, type Ch3Data } from './data';
	import { frontierFrame, frontierPolyline } from './frontiersvg';
	import FrontierScaffold from './FrontierScaffold.svelte';

	/**
	 * C3-2 — The frontier plane (storyboard §3): the chapter's ONE controlling
	 * morph (free field → the economy x strike-rate plane). Every ball condenses
	 * onto its bowler-season's coordinate, settling into a low-alpha density haze.
	 * Destination-first scaffold (axes + the persistent orientation anchors +
	 * the "cheap and deadly" home zone) fades in ahead of the points. Three caption
	 * steps: x teaches (cheap↔expensive) → the y-axis lights (fast↔slow) → the
	 * opening-season "edge of the possible" draws through the bottom-left. The edge
	 * is SVG on the annotation plane, registered to field coords (never GL geometry).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 180 / 340 → morph ends ≈ 0.53 */
	const step = $derived.by(() => {
		if (progress < 0.64) return 1;
		if (progress < 0.82) return 2;
		return 3;
	});
	const scaffoldOn = $derived(progress >= 0.08);
	const yOn = $derived(reduced || step >= 2);
	const edgeOn = $derived(reduced || step >= 3);

	let ch3 = $state<Ch3Data | null>(null);
	let tick = $state(0);
	onMount(() => {
		let alive = true;
		loadCh3Data().then((d) => {
			if (alive) ch3 = d;
		});
		const onResize = (): void => {
			requestAnimationFrame(() => {
				tick++;
			});
		};
		window.addEventListener('resize', onResize);
		return () => {
			alive = false;
			window.removeEventListener('resize', onResize);
		};
	});
	// recompute the moment the field handle first arrives (no resize needed)
	let seeded = false;
	$effect(() => {
		if (field && !seeded) {
			seeded = true;
			tick++;
		}
	});

	/** the opening season's edge (IPL 2008) — the best-anyone-managed lower-left line */
	const edge2008 = $derived<{ economy: number; strike_rate: number }[] | null>(
		ch3 ? iplHull(ch3, 2008) : null
	);

	const geo = $derived.by(() => {
		void tick;
		const f = field;
		if (!f) return null;
		const frame = frontierFrame(f);
		if (!frame) return null;
		const edge = edge2008 ? frontierPolyline(f, edge2008) : '';
		return { frame, edge };
	});
</script>

<div class="pin" class:active>
	<!-- destination-first orientation scaffold (shared, held through C3-3..C3-8) -->
	<FrontierScaffold {field} on={scaffoldOn} showY={yOn} showHome={yOn} litY={yOn} />

	{#if geo}
		{@const fr = geo.frame}
		<!-- the opening-season edge — SVG registered to field coords -->
		<svg class="edge-plane" aria-hidden="true">
			{#if geo.edge}
				<polyline points={geo.edge} class="edge" class:on={edgeOn} />
			{/if}
		</svg>
		{#if edgeOn && geo.edge}
			<div class="edge-label" style="left:{fr.home.right + 8}px; top:{fr.top + 30}px;">the edge of the possible, 2008</div>
		{/if}
	{/if}

	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card chip">
				<p>
					Every dot is one bowler's whole season. Left to right is <strong>how many runs he leaked
						an over.</strong> Miserly on the left, expensive on the right.
					<button class="dagger" onclick={() => footnotesOpen.set('economy-convention')} aria-label="How economy is counted">ⓘ</button>
					Every ball he bowled stacks on his dot, so a busier bowler makes a brighter, thicker smudge.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Top to bottom is <strong>how quickly he struck</strong>: how many balls he needed to take a
					wicket. Down low, wickets came fast. Up high, they came slow.
				</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					So the best place to live is the <strong>bottom-left corner: cheap and deadly at once.</strong>
					That glowing line curving through it is the edge of the possible, the best anyone managed
					that year.
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

	.edge-plane {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		overflow: visible;
		pointer-events: none;
	}

	.edge {
		fill: none;
		stroke: #ffd477;
		stroke-width: 2.4;
		stroke-linejoin: round;
		stroke-linecap: round;
		filter: drop-shadow(0 0 5px rgba(255, 212, 119, 0.5));
		opacity: 0;
		transition: opacity 650ms ease;
	}

	.edge.on {
		opacity: 1;
	}

	.edge-label {
		position: absolute;
		font-size: 12px;
		font-weight: 700;
		color: #ffd477;
		white-space: nowrap;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.95);
		pointer-events: none;
	}

	@media (prefers-reduced-motion: reduce) {
		.edge {
			transition: none;
		}
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 10vh;
		max-width: min(26rem, 44vw);
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
		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: max(10vh, calc(env(safe-area-inset-top) + 56px));
		}
	}
</style>
