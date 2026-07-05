<script lang="ts">
	import { onMount } from 'svelte';
	import type { FieldHandle } from '$lib/field/field';
	import { frontierFrame } from './frontiersvg';

	/**
	 * The persistent frontier-plane orientation layer (storyboard §0.1 / §8):
	 * the x/y axes + ticks + gloss names, the short end-anchors (cheap/expensive on
	 * x, fast/slow on y) and the warm "cheap and deadly" home zone. Drawn in C3-2
	 * (destination-first reveal) and HELD through C3-3..C3-8 so the inverted
	 * good=bottom-left prior stays anchored on screen wherever the plane is argued
	 * or sits as background. Factored out of Frontier.svelte so a scroll-back /
	 * deep-link reader recognises the plane without the caption. All coords come
	 * from `frontierFrame(field)` (the exact shader mapping), so the labels can
	 * never drift from the GL haze.
	 *
	 * On narrow viewports the y-axis ticks + name sit INSIDE the plot (the fixed
	 * letterbox pushes the left edge to ~8% of screen width, so an outside-left
	 * label clips) — storyboard mobile-axis lock.
	 */
	interface Props {
		field?: FieldHandle | null;
		/** outer visibility / destination-first reveal (default shown) */
		on?: boolean;
		/** the y-axis ticks + name + fast/slow anchors (C3-2 gates this on step 2) */
		showY?: boolean;
		/** the warm bottom-left home zone (C3-2 gates this on step 2) */
		showHome?: boolean;
		/** brighten the y-axis line (defaults to showY) */
		litY?: boolean;
		/** background use behind a 2D scene — hold the anchors at low salience */
		faint?: boolean;
	}
	let { field, on = true, showY = true, showHome = true, litY, faint = false }: Props = $props();
	const lit = $derived(litY ?? showY);

	let tick = $state(0);
	let narrow = $state(false);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => {
				tick++;
			});
		};
		const mq = window.matchMedia('(max-width: 640px)');
		const updMq = (): void => {
			narrow = mq.matches;
		};
		updMq();
		window.addEventListener('resize', onResize);
		mq.addEventListener('change', updMq);
		return () => {
			window.removeEventListener('resize', onResize);
			mq.removeEventListener('change', updMq);
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

	const fr = $derived.by(() => {
		void tick;
		return field ? frontierFrame(field) : null;
	});
</script>

{#if fr}
	<div class="scaffold" class:on class:faint aria-hidden="true">
		<!-- the warm "cheap and deadly" home zone (bottom-left, fixed good corner) -->
		<div
			class="home"
			class:on={showHome}
			style="left:{fr.home.left}px; top:{fr.home.top}px; width:{(fr.home.right - fr.home.left).toFixed(1)}px; height:{(fr.home.bottom - fr.home.top).toFixed(1)}px;"
		></div>
		<!-- x axis -->
		<div class="axis" style="left:{fr.left}px; top:{fr.bottom}px; width:{(fr.right - fr.left).toFixed(1)}px; height:1px;"></div>
		<!-- y axis (brightens in step 2) -->
		<div class="axis" class:lit style="left:{fr.left}px; top:{fr.top}px; width:1px; height:{(fr.bottom - fr.top).toFixed(1)}px;"></div>

		{#each fr.xticks as t (t.label)}
			<div class="xlab" style="left:{t.x.toFixed(1)}px; top:{(fr.bottom + 6).toFixed(1)}px;">{t.label}</div>
		{/each}
		<div class="axis-name x" style="left:{((fr.left + fr.right) / 2).toFixed(1)}px; top:{(fr.bottom + 22).toFixed(1)}px;">
			runs leaked an over
		</div>
		<!-- persistent x end-anchors (the x-axis runs along the bottom) -->
		<div class="end-anchor cheap" style="left:{fr.left.toFixed(1)}px; top:{(fr.bottom + 22).toFixed(1)}px;">← cheap</div>
		<div class="end-anchor expensive" style="left:{fr.right.toFixed(1)}px; top:{(fr.bottom + 22).toFixed(1)}px;">expensive →</div>

		{#if showY}
			{#each fr.yticks as t (t.label)}
				<div
					class="ylab"
					class:inside={narrow}
					style="left:{(narrow ? fr.left + 5 : fr.left - 6).toFixed(1)}px; top:{t.y.toFixed(1)}px;"
				>{t.label}</div>
			{/each}
			<div
				class="axis-name y"
				class:inside={narrow}
				style="left:{(narrow ? fr.left + 12 : fr.left - 34).toFixed(1)}px; top:{((fr.top + fr.bottom) / 2).toFixed(1)}px;"
			>
				balls to a wicket
			</div>
			<!-- persistent y end-anchors (the y-axis runs up the left edge) -->
			<div class="end-anchor fast" style="left:{(fr.left + 6).toFixed(1)}px; top:{(fr.bottom - 8).toFixed(1)}px;">fast ↓</div>
			<div class="end-anchor slow" style="left:{(fr.left + 6).toFixed(1)}px; top:{(fr.top + 8).toFixed(1)}px;">slow ↑</div>
		{/if}
	</div>
{/if}

<style>
	.scaffold {
		position: absolute;
		inset: 0;
		opacity: 0;
		transition: opacity 700ms ease;
		pointer-events: none;
	}

	.scaffold.on {
		opacity: 1;
	}

	.scaffold.faint.on {
		opacity: 0.42;
	}

	.home {
		position: absolute;
		border-radius: 6px;
		background: radial-gradient(
			ellipse at bottom left,
			rgba(232, 163, 61, 0.16),
			rgba(232, 163, 61, 0) 72%
		);
		opacity: 0;
		transition: opacity 700ms ease;
	}

	.home.on {
		opacity: 1;
	}

	.axis {
		position: absolute;
		background: rgba(232, 236, 245, 0.24);
		transition: background 500ms ease;
	}

	.axis.lit {
		background: rgba(232, 236, 245, 0.34);
	}

	.xlab,
	.ylab,
	.axis-name {
		position: absolute;
		font-size: 11px;
		letter-spacing: 0.05em;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
	}

	.xlab {
		transform: translate(-50%, 0);
	}

	.ylab {
		transform: translate(-100%, -50%);
	}

	.ylab.inside {
		transform: translate(0, -50%);
	}

	.axis-name {
		letter-spacing: 0.12em;
		text-transform: lowercase;
	}

	.axis-name.x {
		transform: translate(-50%, 0);
	}

	.axis-name.y {
		transform: translate(-50%, -50%) rotate(-90deg);
	}

	.end-anchor {
		position: absolute;
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--gold);
		white-space: nowrap;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
	}

	.end-anchor.expensive {
		transform: translate(-100%, 0);
		color: var(--ink-dim);
	}

	.end-anchor.slow {
		color: var(--ink-dim);
	}

	@media (prefers-reduced-motion: reduce) {
		.scaffold,
		.home,
		.axis {
			transition: none;
		}
	}
</style>
