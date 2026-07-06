<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh4Data, fmt1, pct, runs, type BandKey, type Ch4Data, type VenueStrand } from './data';

	/**
	 * C4-9 — Venue Fingerprints (SUPPORTING, the contrarian twist) + the venue
	 * divergence cone (2D). Each strand is one ground's typical first innings, era by
	 * era; they converge early and FAN APART recently. The flat-pitch era did not
	 * flatten the country: between-venue spread more than doubled (10.1% → 23.7%,
	 * season-controlled), and Chinnaswamy (195) sits 22 runs above Chepauk (173) in
	 * the same era. Over the dimmed skyline; every number from ch4.json.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.34) return 1;
		if (progress < 0.66) return 2;
		return 3;
	});
	const BOUNDS = [0, 0.34, 0.66, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const fanOn = $derived(reduced || step >= 2);

	let ch4 = $state<Ch4Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh4Data().then((d) => {
			if (alive) ch4 = d;
		});
		return () => {
			alive = false;
		};
	});

	const ERAS: BandKey[] = [
		'ipl 2008-2010',
		'ipl 2011-2015',
		'ipl 2016-2019',
		'ipl 2020-2022',
		'ipl 2023-2026'
	];
	const ERA_LAB = ['08–10', '11–15', '16–19', '20–22', '23–26'];

	const varEarly = $derived(
		ch4 ? ch4.venues.between_venue_variance['ipl 2008-2010'].between_venue_share_pct : null
	);
	const varLate = $derived(
		ch4 ? ch4.venues.between_venue_variance['ipl 2023-2026'].between_venue_share_pct : null
	);
	const fp = $derived(ch4 ? ch4.venues.fingerprint_2023_2026 : null);

	function isNamed(v: VenueStrand, needle: string): boolean {
		return v.venue.toLowerCase().includes(needle);
	}

	/* ---- cone geometry ---- */
	const W = 360;
	const H = 190;
	const PAD = 26;
	const YMIN = 135;
	const YMAX = 215;
	const xAt = (i: number): number => PAD + (i / (ERAS.length - 1)) * (W - 2 * PAD);
	const yAt = (v: number): number =>
		H - PAD - ((Math.min(YMAX, Math.max(YMIN, v)) - YMIN) / (YMAX - YMIN)) * (H - 2 * PAD);

	interface Strand {
		key: string;
		pts: { x: number; y: number }[];
		named: 'chinnaswamy' | 'chepauk' | null;
	}
	const strands = $derived.by(() => {
		const d = ch4;
		if (!d) return [] as Strand[];
		const out: Strand[] = [];
		for (const v of d.venues.strands) {
			if (v.league !== 'ipl') continue;
			const pts: { x: number; y: number }[] = [];
			ERAS.forEach((e, i) => {
				const cell = v.by_era[e];
				if (cell && typeof cell.avg_first_innings === 'number')
					pts.push({ x: xAt(i), y: yAt(cell.avg_first_innings) });
			});
			if (pts.length < 2) continue;
			const named = isNamed(v, 'chinnaswamy') ? 'chinnaswamy' : isNamed(v, 'chidambaram') ? 'chepauk' : null;
			out.push({ key: v.venue, pts, named });
		}
		return out;
	});
	const polyOf = (pts: { x: number; y: number }[]): string =>
		pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
</script>

<div class="pin" class:active>
	{#if strands.length}
		<figure class="cone-slot">
			<svg viewBox="0 0 {W} {H}" role="img" aria-label="Per-ground typical first innings by era; the strands fan apart, Chinnaswamy high and Chepauk low in the latest era">
				<line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} class="axis" />
				<!-- faint strands (every ground) -->
				{#if fanOn}
					{#each strands.filter((s) => s.named === null) as s (s.key)}
						<polyline points={polyOf(s.pts)} class="strand" />
					{/each}
				{/if}
				<!-- the two named fingerprints, bold -->
				{#each strands.filter((s) => s.named !== null) as s (s.key)}
					<polyline points={polyOf(s.pts)} class="strand named {s.named}" />
					{#if (reduced || step >= 3) && fp}
						<text
							x={s.pts[s.pts.length - 1].x - 4}
							y={s.pts[s.pts.length - 1].y - 6}
							class="named-lab {s.named}"
							text-anchor="end"
						>{s.named === 'chinnaswamy' ? `Chinnaswamy ${runs(fp.chinnaswamy)}` : `Chepauk ${runs(fp.chepauk)}`}</text>
					{/if}
				{/each}
				{#each ERA_LAB as lab, i (lab)}
					<text x={xAt(i)} y={H - 8} class="ax-lab" text-anchor="middle">{lab}</text>
				{/each}
			</svg>
			<figcaption>typical first innings, ground by ground, era by era</figcaption>
		</figure>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card chip">
				<p>
					Each thin line is <strong>one ground's typical first innings,</strong> era by era. The far
					left is the league's first years, the far right is now.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card chip">
				<p>
					You would expect flat, batter-friendly pitches to make every ground the same.
					<strong>The opposite happened. The lines fan apart.</strong> The share of scoring you can pin
					on which ground it was
					{varEarly !== null && varLate !== null ? `more than doubled, ${pct(varEarly)}% to ${pct(varLate)}%` : 'more than doubled'}.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					Chinnaswamy plays at {fp !== null ? runs(fp.chinnaswamy) : '195'}, Chepauk at
					{fp !== null ? runs(fp.chepauk) : '173'}, <strong>22 runs apart in the same era.</strong>
					Grounds got more different, not less.
					<button class="dagger" onclick={() => footnotesOpen.set('venue-canon')} aria-label="How venues are counted">ⓘ</button>
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

	.cone-slot {
		position: absolute;
		top: 13vh;
		left: 50%;
		transform: translateX(-50%);
		margin: 0;
		width: min(31rem, 90vw);
		text-align: center;
	}

	.cone-slot svg {
		display: block;
		width: 100%;
		height: auto;
		background: rgba(6, 9, 14, 0.4);
		border-radius: 10px;
	}

	.axis {
		stroke: rgba(232, 236, 245, 0.2);
		stroke-width: 1;
	}

	.strand {
		fill: none;
		stroke: rgba(151, 161, 184, 0.4);
		stroke-width: 1.2;
		stroke-linejoin: round;
	}

	.strand.named.chinnaswamy {
		stroke: var(--ember);
		stroke-width: 2.6;
		filter: drop-shadow(0 0 4px rgba(255, 93, 58, 0.4));
	}

	.strand.named.chepauk {
		stroke: var(--teal);
		stroke-width: 2.6;
		filter: drop-shadow(0 0 4px rgba(46, 196, 182, 0.4));
	}

	.named-lab {
		font-size: 10px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.named-lab.chinnaswamy {
		fill: #ff8a6a;
	}

	.named-lab.chepauk {
		fill: var(--teal);
	}

	.ax-lab {
		fill: var(--ink-dim);
		font-size: 8.5px;
		font-variant-numeric: tabular-nums;
	}

	figcaption {
		margin-top: 0.4rem;
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.caption-slot {
		position: absolute;
		left: 6vw;
		bottom: 9vh;
		max-width: min(30rem, 46vw);
		opacity: var(--reveal, 1); /* mobile "read, then watch" (CONTRACT §17); 1 on desktop / reduced */
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
		.cone-slot {
			top: 9vh;
			width: 94vw;
		}

		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(9vh, calc(env(safe-area-inset-bottom) + 56px));
		}
	}
</style>
