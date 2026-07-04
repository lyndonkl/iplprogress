<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { loadCh1Data, pooledSr, GHOST_BAND, BOLD_BAND, type Ch1Data } from './data';

	/**
	 * C1-2 — The ignition wall (storyboard §3): annotations for the chapter's
	 * ONE controlling morph (free field → wall). Destination-first scaffold
	 * fades in ahead of the points; four caption steps (one change each) walk
	 * the brightening early-ball region; the number chip lands last. The WPL
	 * shelf renders dimmed one stop through steps 2-4 (fieldState wplDim) and
	 * is restored at C1-6, where the brighten IS the beat.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 150 / 300 */
	const MORPH_END = 0.5;

	const scaffoldOn = $derived(progress >= 0.05);
	const step = $derived.by(() => {
		if (progress < MORPH_END + 0.02) return 0;
		if (progress < 0.64) return 1;
		if (progress < 0.76) return 2;
		if (progress < 0.88) return 3;
		return 4;
	});

	/* ---- chapter data (chip numbers — never hardcoded) ---------------------- */
	let ch1 = $state<Ch1Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh1Data().then((d) => {
			if (alive) ch1 = d;
		});
		const onResize = (): void => {
			// defer one frame so the shell's camera resize lands first
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

	const srEarly = $derived(ch1 ? Math.round(pooledSr(ch1, GHOST_BAND)) : null);
	const srRecent = $derived(ch1 ? Math.round(pooledSr(ch1, BOLD_BAND)) : null);

	/* ---- wall geometry → CSS (scaffold + sweep anchoring) -------------------- */
	let tick = $state(0);

	interface Rect {
		left: number;
		top: number;
		width: number;
		height: number;
	}

	const geo = $derived.by(() => {
		void tick; // resize signal
		const f = field;
		if (!f) return null;
		const wall = f.getWallLayout();
		if (!wall) return null;
		const groups = f.data.groups;
		const giOf = (season: number): number | null => {
			const g = groups.find((gr) => gr.league === 'ipl' && gr.season === season);
			return g ? g.gi : null;
		};
		const gi2008 = giOf(2008);
		const gi2009 = giOf(2009);
		const gi2026 = giOf(2026);
		if (gi2008 === null || gi2026 === null) return null;

		const rowY = (gi: number): number => f.projectToCss(0, wall.rowYs[gi]).y;
		const xAt = (ball: number): number =>
			f.projectToCss(wall.left + ((ball - 1) / 29) * wall.width, 0).x;

		const y2008 = rowY(gi2008);
		const y2026 = rowY(gi2026);
		const pitch = gi2009 !== null ? Math.abs(rowY(gi2009) - y2008) : 14;

		const leftPx = xAt(1);
		const rightPx = xAt(30);
		const baselineY = y2008 + pitch * 1.1;

		const seasonLabels = [2008, 2015, 2023, 2026]
			.map((s) => {
				const gi = giOf(s);
				return gi === null ? null : { text: String(s), y: rowY(gi) };
			})
			.filter((v): v is { text: string; y: number } => v !== null);

		const shelfY = Number.isNaN(wall.shelfMidY) ? null : f.projectToCss(0, wall.shelfMidY).y;

		const sweepRight = xAt(10.5);
		const sweep2: Rect = {
			left: leftPx - 6,
			top: y2008 - pitch * 0.75,
			width: sweepRight - leftPx + 12,
			height: pitch * 1.5
		};
		const sweep3: Rect = {
			left: leftPx - 6,
			top: y2026 - pitch * 0.75,
			width: sweepRight - leftPx + 12,
			height: y2008 - y2026 + pitch * 1.5
		};

		return { leftPx, rightPx, baselineY, seasonLabels, shelfY, sweep2, sweep3 };
	});

	const sweep = $derived.by(() => {
		if (!geo) return null;
		if (step === 2) return geo.sweep2;
		if (step >= 3) return geo.sweep3;
		return null;
	});

	function px(r: Rect): string {
		return `left:${r.left.toFixed(1)}px;top:${r.top.toFixed(1)}px;width:${r.width.toFixed(1)}px;height:${r.height.toFixed(1)}px;`;
	}
</script>

<div class="pin" class:reduced class:active>
	<!-- destination-first scaffold: the empty wall frame ahead of the points -->
	{#if geo}
		<div class="scaffold" class:on={scaffoldOn} aria-hidden="true">
			<div
				class="axis"
				style="left:{geo.leftPx.toFixed(1)}px; top:{geo.baselineY.toFixed(1)}px; width:{(
					geo.rightPx - geo.leftPx
				).toFixed(1)}px;"
			></div>
			<div class="axis-label" style="left:{geo.leftPx.toFixed(1)}px; top:{(geo.baselineY + 6).toFixed(1)}px;">
				ball 1
			</div>
			<div
				class="axis-label end"
				style="left:{geo.rightPx.toFixed(1)}px; top:{(geo.baselineY + 6).toFixed(1)}px;"
			>
				30+
			</div>
			{#each geo.seasonLabels as s (s.text)}
				<div class="row-label" style="left:{(geo.leftPx - 10).toFixed(1)}px; top:{s.y.toFixed(1)}px;">
					{s.text}
				</div>
			{/each}
			{#if geo.shelfY !== null}
				<div
					class="row-label wpl"
					style="left:{(geo.leftPx - 10).toFixed(1)}px; top:{geo.shelfY.toFixed(1)}px;"
				>
					WPL
				</div>
			{/if}
		</div>
	{/if}

	<!-- the one highlighted region each caption step names -->
	{#if sweep}
		<div class="sweep" style={px(sweep)} aria-hidden="true"></div>
	{/if}

	<!-- caption steps: one change per step, ≤3 numbers on screen -->
	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>
					Every ball, arranged by how long its batter had been in.
					<strong>Left edge: a batter's first balls.</strong> Rows climb from 2008 at the
					bottom to 2026 at the top. Brightness = runs.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					<strong>2008: the left edge is dark.</strong> New batters blocked, nudged, had a
					look. The sighter, visible from space.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					Climb the seasons. <strong>The dark corner catches fire.</strong> By 2026 there is
					no warm-up left — ball one is attacked at full intent.
				</p>
			</div>
		{:else if step === 4}
			<div class="scene-card chip">
				<p>
					<strong>
						First ten balls: strike rate {srEarly ?? '—'} → {srRecent ?? '—'}.
					</strong>
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('ignition-wall')}
						aria-label="How we computed this"
					>
						ⓘ
					</button>
					The revolution lives at the start of the innings.
				</p>
			</div>
		{/if}
	</div>
</div>

<style>
	/* viewport-fixed while this scene owns the field: the scaffold and sweep
	   are projected onto the canvas and must never drift from it (a sticky
	   pin unpins over the last 100vh of the section); visibility gating keeps
	   exactly one scene's captions on screen at a time */
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
	}

	.pin.active {
		visibility: visible;
	}

	/* ---- scaffold ---- */
	.scaffold {
		position: absolute;
		inset: 0;
		opacity: 0;
		transition: opacity 700ms ease;
	}

	.scaffold.on {
		opacity: 1;
	}

	.axis {
		position: absolute;
		height: 1px;
		background: rgba(232, 236, 245, 0.28);
	}

	.axis-label {
		position: absolute;
		transform: translateX(-2px);
		font-size: 11px;
		letter-spacing: 0.06em;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.axis-label.end {
		transform: translateX(-100%);
	}

	.row-label {
		position: absolute;
		transform: translate(-100%, -50%);
		font-size: 11px;
		letter-spacing: 0.05em;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.row-label.wpl {
		color: var(--teal);
		font-weight: 700;
		letter-spacing: 0.18em;
	}

	/* ---- the sweep highlight (luminance framing only, hue-free) ---- */
	.sweep {
		position: absolute;
		border: 1px solid rgba(232, 236, 245, 0.5);
		border-radius: 6px;
		background: rgba(232, 236, 245, 0.05);
		box-shadow: 0 0 22px rgba(232, 236, 245, 0.12);
		transition:
			top 900ms ease,
			height 900ms ease,
			width 900ms ease;
	}

	.pin.reduced .sweep,
	.pin.reduced .scaffold {
		transition: none;
	}

	@media (prefers-reduced-motion: reduce) {
		.sweep,
		.scaffold {
			transition: none;
		}
	}

	/* ---- captions: right column on desktop — the region every step names is
	   the wall's LEFT edge, and the card must never cover it ---- */
	.caption-slot {
		position: absolute;
		right: 5vw;
		bottom: 12vh;
		max-width: min(26rem, 84vw);
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
			bottom: max(10vh, calc(env(safe-area-inset-bottom) + 8vh));
		}

		/* narrow screens: the wall spans nearly full width, so the row labels
		   sit just INSIDE the left edge instead of clipping off the viewport */
		.row-label {
			transform: translate(4px, -50%) scale(0.9);
			text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
		}
	}
</style>
