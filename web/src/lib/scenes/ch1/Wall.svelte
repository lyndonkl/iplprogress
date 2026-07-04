<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import {
		loadCh1Data,
		srAtBall,
		WALL_HEAT_RAMP_START,
		WALL_HEAT_RAMP_END,
		GHOST_BAND,
		BOLD_BAND,
		type Ch1Data
	} from './data';

	/**
	 * C1-2 — The ignition wall (storyboard §3): annotations for the chapter's
	 * ONE controlling morph (free field → wall). Destination-first scaffold
	 * fades in ahead of the points; four caption steps (one change each). Steps
	 * 1-2 are the ESTABLISHING outcome-coloured shot; steps 3-4 are the THESIS
	 * beat — the field recolours by era-relative intent (uWallHeatMix, driven by
	 * the scene def's dynamicState) so the early-ball corner ignites bottom→top,
	 * and an always-visible diverging legend names the scale. The WPL shelf
	 * renders dimmed one stop throughout (fieldState wplDim), restored at C1-6.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 150 / 300 */
	const MORPH_END = 0.5;

	const scaffoldOn = $derived(progress >= 0.05);
	// step thresholds align with the heat ramp in data.ts (shared source): step 3
	// (the recolor ramp) spans [RAMP_START, RAMP_END); step 4 (the chip) holds.
	const step = $derived.by(() => {
		if (progress < MORPH_END + 0.02) return 0;
		if (progress < 0.64) return 1;
		if (progress < WALL_HEAT_RAMP_START) return 2;
		if (progress < WALL_HEAT_RAMP_END) return 3;
		return 4;
	});

	// the heat beat is live for steps 3-4; under reduced motion the field jump-cuts
	// straight to the heated end-state, so the legend rides along the whole scene.
	const heatOn = $derived(reduced || step >= 3);

	/* ---- chapter data (chip numbers + legend labels — never hardcoded) ------- */
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

	// the ball-1 chip: strike rate on the first ball of the innings, the cleanest
	// single column of the era-relative recolor (73.7 → 95.5, rounds to 74 → 96)
	const srBall1Early = $derived(ch1 ? Math.round(srAtBall(ch1, GHOST_BAND, 1)) : null);
	const srBall1Recent = $derived(ch1 ? Math.round(srAtBall(ch1, BOLD_BAND, 1)) : null);

	/* ---- diverging legend (labels from ch1.json; swatch matches the shader) ----
	   the neutral tick sits at the pipeline's neutral byte (73/255 ≈ 28.6%), so
	   "like 2008" reads at exactly the pivot the shader recolours around. */
	const heat = $derived(ch1 ? ch1.ignition.wallheat : null);
	const neutralPct = $derived(heat ? (heat.neutral_byte / 255) * 100 : (73 / 255) * 100);
	const legendLabels = $derived(
		heat?.legend_labels ?? [
			'Below the 2008-10 batter',
			'Like the 2008-10 batter',
			'Hotter than the 2008-10 batter'
		]
	);

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
					Now colour each ball by how hard it's hit — versus a 2008 batter at the very same
					point. <strong>The corner catches fire:</strong> the opening balls, once played quietly,
					now blaze.
				</p>
			</div>
		{:else if step === 4}
			<div class="scene-card chip">
				<p>
					<strong>
						First ball of the innings: struck at {srBall1Early ?? '—'} in 2008, {srBall1Recent ??
							'—'} now.
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

	<!-- diverging legend — names the recolor scale on screen (cognitive-design):
	     visible through the heat beat (steps 3-4, or the whole scene under reduced
	     motion). The swatch stops match the shader; labels come from ch1.json. -->
	<div class="legend" class:on={heatOn} aria-hidden={!heatOn}>
		<p class="legend-title">Each ball vs a 2008 batter at the same point</p>
		<div class="legend-bar">
			<span class="neutral-tick" style="left:{neutralPct.toFixed(1)}%"></span>
		</div>
		<ul class="legend-key">
			<li><span class="chip-swatch cool"></span>{legendLabels[0]}</li>
			<li><span class="chip-swatch neutral"></span>{legendLabels[1]}</li>
			<li><span class="chip-swatch hot"></span>{legendLabels[2]}</li>
		</ul>
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
	.pin.reduced .scaffold,
	.pin.reduced .legend {
		transition: none;
	}

	@media (prefers-reduced-motion: reduce) {
		.sweep,
		.scaffold,
		.legend {
			transition: none;
		}
	}

	/* ---- diverging legend: top-right, below the nav, so it never covers the
	   wall's igniting LEFT corner (early balls climbing bottom→top) ---- */
	.legend {
		position: absolute;
		top: 4.5rem;
		right: 5vw;
		width: min(18rem, 66vw);
		padding: 0.6rem 0.75rem;
		border-radius: 10px;
		background: rgba(13, 20, 24, 0.82);
		border: 1px solid rgba(232, 236, 245, 0.12);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
		opacity: 0;
		transition: opacity 500ms ease;
		pointer-events: none;
	}

	.legend.on {
		opacity: 1;
	}

	.legend-title {
		margin: 0 0 0.5rem;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.03em;
		color: var(--ink);
	}

	/* the diverging swatch — stops match the shader (deep-blue → grey-blue at the
	   neutral pivot 73/255 ≈ 28.6% → amber at 64.3% → six-red) */
	.legend-bar {
		position: relative;
		height: 10px;
		border-radius: 5px;
		background: linear-gradient(
			to right,
			#3a4358 0%,
			#7d8fb0 28.6%,
			#e8a33d 64.3%,
			#ff5d3a 100%
		);
	}

	.neutral-tick {
		position: absolute;
		top: -3px;
		bottom: -3px;
		width: 2px;
		transform: translateX(-1px);
		background: var(--ink);
		border-radius: 1px;
		box-shadow: 0 0 0 1px rgba(11, 14, 20, 0.65);
	}

	.legend-key {
		list-style: none;
		margin: 0.5rem 0 0;
		padding: 0;
		display: grid;
		gap: 0.25rem;
	}

	.legend-key li {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.7rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.chip-swatch {
		flex: none;
		width: 12px;
		height: 12px;
		border-radius: 3px;
	}

	.chip-swatch.cool {
		background: #3a4358;
	}

	.chip-swatch.neutral {
		background: #7d8fb0;
	}

	.chip-swatch.hot {
		background: #ff5d3a;
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

		/* legend stays top-right, narrower, clear of the nav and the left corner */
		.legend {
			top: 4rem;
			right: 4vw;
			width: min(15rem, 62vw);
			padding: 0.5rem 0.6rem;
		}
	}
</style>
