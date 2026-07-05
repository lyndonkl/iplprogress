<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import type { GroupMeta } from '$lib/field/types';
	import { footnotesOpen } from '$lib/state';
	import { loadSandboxData } from '$lib/scenes/sandbox/data';
	import {
		loadCh3Data,
		riverBoundaries,
		pctText,
		IPL_EARLY,
		IPL_MODERN,
		type Ch3Data,
		type RiverSeason
	} from './data';

	/**
	 * C3-4 — The dismissal rivers (supporting: Dismissal DNA; the chapter's ONE
	 * subset-highlight). Over the held frontier plane, every bowler-credited wicket
	 * lifts out of its cloud and stacks into a FLAT-BASELINE 100%-stacked band, one
	 * strip per season, bands = dismissal kinds bottom→top (bowled, leg before,
	 * stumped, caught — the two woodwork dismissals adjacent + baseline-anchored as
	 * one "stumps" group). The GL fly-out (declared on the scene's fieldState,
	 * engage driven by dynamicState) supplies the living texture; this component
	 * draws the SVG axis, the season axis, the stacked areas from ch3.json and the
	 * band labels, so the finding lands even before the GL membership bakes.
	 *
	 * Membership is client-baked ONCE from the columnar `wicket_kind` (zero pipeline
	 * dependency, exactly like Ch 2's setRunouts) — CONTRACT §16.3.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.34) return 1;
		if (progress < 0.56) return 2;
		if (progress < 0.78) return 3;
		return 4;
	});
	const engaged = $derived(reduced ? 1 : Math.min(1, progress / 0.3));

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

	/* seed wicket-kind membership ONCE from the columnar wicket_kind (§16.3) —
	   the working-today path with zero pipeline dependency. Cached with the
	   sandbox dataset, so the Bowl reuses the same fetch. */
	let baked = false;
	$effect(() => {
		const f = field;
		if (!f || baked) return;
		baked = true;
		tick++; // force one geo recompute the moment the field arrives
		loadSandboxData()
			.then((sb) => {
				const a = sb.columnar.arrays.wicket_kind;
				const dict = sb.columnar.dicts.wicket_kind;
				const kind = new Int8Array(a.length).fill(-1);
				for (let i = 0; i < a.length; i++) {
					const k = dict[a[i]] ?? '';
					if (k === 'bowled') kind[i] = 0;
					else if (k === 'lbw') kind[i] = 1;
					else if (k === 'caught' || k === 'caught and bowled') kind[i] = 2;
					else if (k === 'stumped') kind[i] = 3; // run out / retired excluded
				}
				f.setDismissals(kind);
				tick++;
			})
			.catch(() => {
				/* the SVG stacked band carries the finding even if membership fails */
			});
	});

	/* the DNA number pairs (bowler-credited shares), all from the artifact */
	const bowledLbwEarly = $derived(ch3 ? ch3.dismissal_dna.era_bands[IPL_EARLY].bowled_lbw_pct : null);
	const bowledLbwModern = $derived(ch3 ? ch3.dismissal_dna.era_bands[IPL_MODERN].bowled_lbw_pct : null);
	const caughtEarly = $derived(ch3 ? ch3.dismissal_dna.era_bands[IPL_EARLY].caught_pct : null);
	const caughtModern = $derived(ch3 ? ch3.dismissal_dna.era_bands[IPL_MODERN].caught_pct : null);
	const stumpedEarly = $derived(ch3 ? ch3.dismissal_dna.era_bands[IPL_EARLY].stumped_pct : null);
	const stumpedModern = $derived(ch3 ? ch3.dismissal_dna.era_bands[IPL_MODERN].stumped_pct : null);

	/* band hues — bowled/lbw share the woodwork hue, stumped + caught distinct, and
	   caught-and-bowled a pale caught-family sliver (split out so the caught band
	   equals the caption's caught_pct); matches the GL categorical palette (§16) */
	const BAND_FILL = ['#ffb02e', '#ffb02e', '#e05fd8', '#9fb4d8', '#5b8cff']; // bowled, lbw, stumped, c&b, caught

	interface Strip {
		x: number;
		b: number[]; // 5 cumulative boundaries 0..1
		league: 'ipl' | 'wpl';
		season: number;
	}

	const geo = $derived.by(() => {
		void tick;
		const f = field;
		const d = ch3;
		if (!f || !d) return null;
		const ly = f.getRiversLayout();
		if (!ly) return null;
		const groups: GroupMeta[] = f.data.groups;
		const byGi = new Map<number, GroupMeta>();
		for (const g of groups) byGi.set(g.gi, g);
		const riverBy = new Map<string, RiverSeason>();
		for (const r of d.dismissal_dna.rivers.per_season) riverBy.set(`${r.league}-${r.season}`, r);

		const worldY = (frac: number): number => ly.bottom + frac * ly.height;
		const strips: Strip[] = [];
		for (const gi of ly.gis) {
			const g = byGi.get(gi);
			if (!g) continue;
			const r = riverBy.get(`${g.league}-${g.season}`);
			if (!r) continue;
			strips.push({ x: ly.xs[gi], b: riverBoundaries(r.kinds), league: g.league, season: g.season });
		}
		if (strips.length === 0) return null;

		// edge-extend so the areas fill the full band box
		const xLeft = ly.left;
		const xRight = ly.left + ly.width;
		const xs = [xLeft, ...strips.map((s) => s.x), xRight];
		const bs = [strips[0].b, ...strips.map((s) => s.b), strips[strips.length - 1].b];

		// five stacked-area polygons (bottom→top: bowled, lbw, stumped, c&b, caught)
		const bands = [0, 1, 2, 3, 4].map((k) => {
			const tops: string[] = [];
			const bots: string[] = [];
			for (let i = 0; i < xs.length; i++) {
				const top = f.projectToCss(xs[i], worldY(bs[i][k + 1]));
				const bot = f.projectToCss(xs[i], worldY(bs[i][k]));
				tops.push(`${top.x.toFixed(1)},${top.y.toFixed(1)}`);
				bots.unshift(`${bot.x.toFixed(1)},${bot.y.toFixed(1)}`);
			}
			return `${tops.join(' ')} ${bots.join(' ')}`;
		});

		// 2008 reference boundaries (era ghost) — greyed horizontal marks (all four
		// internal boundaries of the five-band stack, incl. the caught boundary)
		const g2008 = strips.find((s) => s.league === 'ipl' && s.season === 2008);
		const ghostYs = g2008
			? [1, 2, 3, 4].map((k) => f.projectToCss(xLeft, worldY(g2008.b[k])).y)
			: [];

		// box corners + axis anchors
		const bl = f.projectToCss(ly.left, ly.bottom);
		const tr = f.projectToCss(ly.left + ly.width, ly.top);
		const axis = [0, 0.5, 1].map((frac) => ({
			label: `${Math.round(frac * 100)}%`,
			y: f.projectToCss(ly.left, worldY(frac)).y
		}));

		// band label anchors from the pooled-share bands
		const labelY = (kind: string): number => {
			const band = ly.bands.find((b) => b.kind === kind);
			return band ? f.projectToCss(ly.left, band.centerY).y : bl.y;
		};
		const stumpsLabelY = (labelY('bowled') + labelY('lbw')) / 2;

		// season axis ticks + the WPL split
		let splitX: number | null = null;
		for (let i = 1; i < strips.length; i++) {
			if (strips[i - 1].league === 'ipl' && strips[i].league === 'wpl') {
				splitX = f.projectToCss((strips[i - 1].x + strips[i].x) / 2, ly.bottom).x;
			}
		}
		const tickSeasons = [2008, 2014, 2020, 2026];
		const seasonTicks = tickSeasons
			.map((yr) => {
				const s = strips.find((st) => st.league === 'ipl' && st.season === yr);
				return s ? { yr, x: f.projectToCss(s.x, ly.bottom).x } : null;
			})
			.filter((t): t is { yr: number; x: number } => t !== null);

		return {
			left: bl.x,
			right: tr.x,
			bottom: bl.y,
			top: tr.y,
			bands,
			ghostYs,
			axis,
			stumpsLabelY,
			stumpedLabelY: labelY('stumped'),
			caughtLabelY: labelY('caught'),
			splitX,
			seasonTicks
		};
	});
</script>

<div class="pin" class:active>
	{#if geo}
		<svg class="river-plane" aria-hidden="true">
			<!-- the 0-to-100 share axis (left) -->
			{#each geo.axis as a (a.label)}
				<line x1={geo.left} x2={geo.right} y1={a.y} y2={a.y} class="axis-grid" class:base={a.label === '0%'} />
			{/each}
			<!-- the stacked bands (opacity ramps with engage as the wickets fly in) -->
			{#each geo.bands as pts, k (k)}
				<polygon points={pts} fill={BAND_FILL[k]} style="opacity:{(0.24 + 0.34 * engaged).toFixed(3)}" />
			{/each}
			<!-- desaturate the WPL strips: this scene argues the IPL's dismissal DNA
			     (the stumping vanishing, etc.), so the fat WPL stumped band on the far
			     right is held back so it never visually rebuts the IPL claim (its full
			     two-clock treatment is C3-7) -->
			{#if geo.splitX !== null}
				<rect x={geo.splitX} y={geo.top} width={Math.max(0, geo.right - geo.splitX)} height={Math.max(0, geo.bottom - geo.top)} class="wpl-dim" />
			{/if}
			<!-- 2008 reference boundaries (era ghost) -->
			{#each geo.ghostYs as y (y)}
				<line x1={geo.left} x2={geo.right} y1={y} y2={y} class="ghost-edge" />
			{/each}
			<!-- the WPL split -->
			{#if geo.splitX !== null}
				<line x1={geo.splitX} x2={geo.splitX} y1={geo.top} y2={geo.bottom} class="split" />
			{/if}
		</svg>

		<!-- share axis labels -->
		{#each geo.axis as a (a.label)}
			<div class="ylab" style="left:{(geo.left - 6).toFixed(1)}px; top:{a.y.toFixed(1)}px;">{a.label}</div>
		{/each}
		<!-- season axis + league labels -->
		{#each geo.seasonTicks as t (t.yr)}
			<div class="xlab" style="left:{t.x.toFixed(1)}px; top:{(geo.bottom + 6).toFixed(1)}px;">{t.yr}</div>
		{/each}
		{#if geo.splitX !== null}
			<div class="league-lab" style="left:{(geo.splitX - 8).toFixed(1)}px; top:{(geo.bottom + 6).toFixed(1)}px;">IPL</div>
			<div class="league-lab wpl" style="left:{(geo.splitX + 8).toFixed(1)}px; top:{(geo.bottom + 6).toFixed(1)}px;">WPL</div>
		{/if}
		<!-- band labels -->
		<div class="band-lab stumps" style="left:{(geo.right - 4).toFixed(1)}px; top:{geo.stumpsLabelY.toFixed(1)}px;">woodwork: bowled + leg before</div>
		<div class="band-lab stumped" style="left:{(geo.right - 4).toFixed(1)}px; top:{geo.stumpedLabelY.toFixed(1)}px;">stumped</div>
		<div class="band-lab caught" style="left:{(geo.right - 4).toFixed(1)}px; top:{geo.caughtLabelY.toFixed(1)}px;">caught</div>
	{/if}

	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>
					Now just the wickets. Every ball that took one <strong>lifts off the map and sorts itself by
						how the batter went:</strong> bowled, leg before, caught, stumped. Each colored band is one
					way out, and its thickness is its share of all wickets.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					Watch the <strong>woodwork group</strong> at the bottom. Bowled and leg before, the balls that
					beat the bat and hit the woodwork, shrank from
					<strong>{bowledLbwEarly !== null ? pctText(bowledLbwEarly) : '-'} wickets in every hundred to
						{bowledLbwModern !== null ? pctText(bowledLbwModern) : '-'}.</strong>
					Bowlers are aiming at the stumps less.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					Now the <strong>caught band</strong>, the ball skied to a waiting fielder. It swelled from
					<strong>{caughtEarly !== null ? pctText(caughtEarly) : '-'}% of wickets to
						{caughtModern !== null ? pctText(caughtModern) : '-'}%.</strong>
					Bowlers dare the batter to clear the rope, and the batter, swinging bigger than ever, keeps
					holing out.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					And the <strong>stumping</strong>, the keeper whipping the bails off, almost disappeared,
					<strong>{stumpedEarly !== null ? pctText(stumpedEarly) : '-'}% of wickets down to
						{stumpedModern !== null ? pctText(stumpedModern) : '-'}%.</strong>
					The wicket did not stop coming. It just changed shape, from a ball at the stumps to a ball in
					the deep.
					<button class="dagger" onclick={() => footnotesOpen.set('dismissal-dna')} aria-label="How wickets were counted">ⓘ</button>
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

	.river-plane {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		overflow: visible;
		pointer-events: none;
	}

	.axis-grid {
		stroke: rgba(232, 236, 245, 0.08);
		stroke-width: 1;
	}

	.axis-grid.base {
		stroke: rgba(232, 236, 245, 0.22);
	}

	.ghost-edge {
		stroke: rgba(232, 236, 245, 0.28);
		stroke-width: 1;
		stroke-dasharray: 3 4;
	}

	.split {
		stroke: rgba(232, 236, 245, 0.3);
		stroke-width: 1.2;
		stroke-dasharray: 2 3;
	}

	.wpl-dim {
		fill: rgba(11, 14, 20, 0.62);
	}

	.ylab,
	.xlab,
	.league-lab,
	.band-lab {
		position: absolute;
		font-size: 11px;
		letter-spacing: 0.04em;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}

	.ylab {
		transform: translate(-100%, -50%);
	}

	.xlab {
		transform: translate(-50%, 0);
	}

	.league-lab {
		font-weight: 700;
		transform: translate(-100%, 0);
		color: var(--ink);
	}

	.league-lab.wpl {
		transform: translate(0, 0);
		color: var(--teal);
	}

	.band-lab {
		transform: translate(-100%, -50%);
		font-weight: 700;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
	}

	.band-lab.stumps {
		color: #ffb02e;
	}

	.band-lab.stumped {
		color: #e05fd8;
	}

	.band-lab.caught {
		color: #5b8cff;
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 10vh;
		max-width: min(32rem, 84vw);
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
		.band-lab {
			font-size: 10px;
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
