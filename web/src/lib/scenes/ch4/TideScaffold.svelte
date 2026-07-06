<script lang="ts">
	import { onMount } from 'svelte';
	import type { FieldHandle } from '$lib/field/field';
	import type { GroupLite } from './data';
	import { tideFrame, tideRule, tideSeasonTicks } from './tidesvg';

	/**
	 * The persistent tide-skyline orientation layer (CONTRACT §18.3): the baseline,
	 * the total-axis ladder (120 / 160 / 200 / 240 runs), the season-axis labels
	 * along the bottom and the IPL / WPL league headings. Drawn once the skyline
	 * lands and HELD behind the tide scenes so a scroll-back / deep-link reader
	 * recognises what a column is without the caption. All coords come from
	 * `tideFrame` / `tideRule` / `tideSeasonTicks` (the exact shader mapping), so the
	 * ticks can never drift from the GL coastline.
	 *
	 * Faint mode holds the anchors at low salience behind a 2D scene.
	 */
	interface Props {
		field?: FieldHandle | null;
		/** outer visibility (default shown once the skyline is up) */
		on?: boolean;
		/** the total-axis ladder marks (default shown) */
		showLadder?: boolean;
		/** the per-season labels along the baseline (default shown) */
		showSeasons?: boolean;
		/** low-salience background use behind a 2D scene */
		faint?: boolean;
	}
	let { field, on = true, showLadder = true, showSeasons = true, faint = false }: Props =
		$props();

	/** the labelled total-axis marks (runs) — the honesty ladder */
	const LADDER = [120, 160, 200, 240] as const;

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
	let seeded = false;
	$effect(() => {
		if (field && !seeded) {
			seeded = true;
			tick++;
		}
	});

	const groups = $derived<GroupLite[]>((field?.data.groups as GroupLite[] | undefined) ?? []);

	const geo = $derived.by(() => {
		void tick;
		const f = field;
		if (!f) return null;
		const frame = tideFrame(f);
		if (!frame) return null;
		const ladder = LADDER.map((total) => tideRule(f, total)).filter((r) => r !== null);
		const ticks = tideSeasonTicks(f, groups);
		// on a phone the season blocks are tight; label every other IPL season +
		// the first/last, and always both WPL ends, so the axis never crowds
		const ipl = ticks.filter((t) => t.league === 'ipl');
		const wpl = ticks.filter((t) => t.league === 'wpl');
		const seasons = narrow
			? [
					...ipl.filter((t, i) => i === 0 || i === ipl.length - 1 || i % 3 === 0),
					...wpl.filter((t, i) => i === 0 || i === wpl.length - 1)
				]
			: ipl.filter((t, i) => i % 2 === 0 || i === ipl.length - 1).concat(wpl);
		return { frame, ladder, seasons, ipl, wpl };
	});
</script>

{#if geo}
	{@const fr = geo.frame}
	<div class="scaffold" class:on class:faint aria-hidden="true">
		<!-- baseline -->
		<div
			class="axis base"
			style="left:{fr.left}px; top:{fr.bottom}px; width:{(fr.right - fr.left).toFixed(1)}px; height:1px;"
		></div>

		{#if showLadder}
			{#each geo.ladder as r (r.total)}
				<div
					class="rule"
					style="left:{r.left.x.toFixed(1)}px; top:{r.left.y.toFixed(1)}px; width:{(r.right.x - r.left.x).toFixed(1)}px;"
				></div>
				<div class="rule-lab" style="left:{(r.left.x - 6).toFixed(1)}px; top:{r.left.y.toFixed(1)}px;">
					{r.total}
				</div>
			{/each}
			<div class="axis-name" style="left:{(fr.left - 6).toFixed(1)}px; top:{fr.top.toFixed(1)}px;">
				first-innings total →
			</div>
		{/if}

		{#if showSeasons}
			{#each geo.seasons as s (s.league + s.season)}
				<div
					class="ylab"
					class:wpl={s.league === 'wpl'}
					style="left:{s.base.x.toFixed(1)}px; top:{(s.base.y + 6).toFixed(1)}px;"
				>
					{s.league === 'wpl' ? `’${String(s.season).slice(2)}` : s.season}
				</div>
			{/each}
			<div class="head" style="left:{fr.iplMidX.toFixed(1)}px; top:{(fr.bottom + 22).toFixed(1)}px;">
				IPL
			</div>
			{#if geo.wpl.length > 0}
				<div
					class="head wpl"
					style="left:{fr.wplMidX.toFixed(1)}px; top:{(fr.bottom + 22).toFixed(1)}px;"
				>
					WPL
				</div>
			{/if}
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
		opacity: 0.4;
	}

	.axis.base {
		position: absolute;
		background: rgba(232, 236, 245, 0.28);
	}

	.rule {
		position: absolute;
		height: 1px;
		background: rgba(232, 236, 245, 0.08);
	}

	.rule-lab {
		position: absolute;
		transform: translate(-100%, -50%);
		font-size: 10px;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
	}

	.ylab {
		position: absolute;
		transform: translate(-50%, 0);
		font-size: 10px;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
	}

	.ylab.wpl {
		color: var(--teal);
	}

	.axis-name {
		position: absolute;
		transform: translate(-50%, -50%) rotate(-90deg);
		font-size: 10px;
		letter-spacing: 0.1em;
		text-transform: lowercase;
		color: var(--ink-dim);
		white-space: nowrap;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
	}

	.head {
		position: absolute;
		transform: translate(-50%, 0);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.3em;
		color: var(--ink-dim);
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
	}

	.head.wpl {
		color: var(--teal);
	}

	@media (prefers-reduced-motion: reduce) {
		.scaffold {
			transition: none;
		}
	}
</style>
