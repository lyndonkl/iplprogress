<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { loadCh4Data, fmt1, fmt2, type Ch4Data } from './data';

	/**
	 * C4-8 — Powerplay Exploitation Premium (SUPPORTING) + the 20-over × season phase
	 * heatmap (2D scene). Every cell is a season's run rate in one over; the powerplay
	 * corner (overs 1-6) catches fire decade by decade. The premium: powerplay run
	 * rate 7.60 → 9.48 at essentially the SAME wicket cost (1.54 vs 1.52 per 36).
	 * The extra runs came free. Over the dimmed skyline; every number from ch4.json.
	 */
	let { progress, active, reduced }: SceneAnnotationProps = $props();

	const step = $derived.by(() => {
		if (progress < 0.34) return 1;
		if (progress < 0.66) return 2;
		return 3;
	});
	const BOUNDS = [0, 0.34, 0.66, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const ppLit = $derived(reduced || step >= 2);

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

	/* newest season on top (like the wall); each row is 20 over-run-rates, plus the
	   season's powerplay wicket cost for the paired strip (audit C4-8 "banked runs,
	   paid no wickets" made VISIBLE beside the igniting corner). */
	const rows = $derived.by(() => {
		const d = ch4;
		if (!d) return [];
		const by = d.phase_heatmap.by_over.ipl;
		const pw = d.powerplay.by_season.ipl;
		return Object.keys(by)
			.map((s) => Number(s))
			.sort((a, b) => b - a)
			.map((season) => ({
				season,
				overs: by[String(season)],
				wkt: pw[String(season)]?.wickets_per_36 ?? null
			}));
	});

	const eq = $derived(ch4 ? ch4.powerplay.equal_wicket_cost : null);

	/* the wicket strip: a SINGLE cool hue whose lightness barely moves, so the strip
	   reads visibly FLAT against the blazing top-left run corner (the whole point:
	   runs soared, wickets did not). Fixed domain keeps the flatness honest. */
	const WK_MIN = 1.2;
	const WK_MAX = 2.0;
	function wktShade(w: number | null): string {
		if (w === null) return 'hsl(212 20% 20%)';
		const t = Math.min(1, Math.max(0, (w - WK_MIN) / (WK_MAX - WK_MIN)));
		return `hsl(212 34% ${(26 + t * 24).toFixed(1)}%)`;
	}

	/* sequential heat ramp: cool low → ember high (2D annotation, not the field) */
	const MIN = 6;
	const MAX = 12.5;
	function heat(rr: number): string {
		const t = Math.min(1, Math.max(0, (rr - MIN) / (MAX - MIN)));
		// three-stop: deep blue-grey → warm ochre → ember
		const stops: [number, [number, number, number]][] = [
			[0, [28, 39, 64]],
			[0.55, [122, 90, 42]],
			[1, [255, 110, 58]]
		];
		let a = stops[0];
		let b = stops[stops.length - 1];
		for (let i = 0; i < stops.length - 1; i++) {
			if (t >= stops[i][0] && t <= stops[i + 1][0]) {
				a = stops[i];
				b = stops[i + 1];
				break;
			}
		}
		const lt = (b[0] - a[0]) === 0 ? 0 : (t - a[0]) / (b[0] - a[0]);
		const c = a[1].map((v, i) => Math.round(v + (b[1][i] - v) * lt));
		return `rgb(${c[0]},${c[1]},${c[2]})`;
	}
</script>

<div class="pin" class:active>
	{#if rows.length}
		<figure class="heat-slot">
			<div class="heat-body">
				<div class="heat" class:pp-lit={ppLit} style="--cols:{rows[0].overs.length}">
					{#each rows as row (row.season)}
						{#each row.overs as rr, o (o)}
							<div
								class="cell"
								class:pp={o < 6}
								style="background:{heat(rr)}"
								title="{row.season}, over {o + 1}: {fmt1(rr)}"
							></div>
						{/each}
					{/each}
				</div>
				<!-- paired per-season wicket strip (same season axis, 2026 on top) -->
				<div class="wkt-strip" class:lit={ppLit} style="--rows:{rows.length}" aria-hidden="true">
					{#each rows as row (row.season)}
						<div
							class="wkt-cell"
							style="background:{wktShade(row.wkt)}"
							title="{row.season}: {row.wkt !== null ? fmt2(row.wkt) : 'no'} wickets per 36 in the powerplay"
						></div>
					{/each}
				</div>
			</div>
			<div class="heat-axes">
				<span class="pp-bracket">powerplay: overs 1–6</span>
				<span class="ov-lab">over 20 →</span>
				<span class="wkt-tag">wickets</span>
			</div>
			<figcaption>run rate, every over × every season (2026 on top); the right strip is powerplay wickets lost</figcaption>
		</figure>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card chip">
				<p>
					Every little square is <strong>one season's run rate in one over.</strong> Overs run left to
					right, seasons stacked with this year on top. The brighter and hotter the square, the more
					runs came off it.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card chip">
				<p>
					Look at the left block, <strong>the first six overs, the powerplay.</strong> It used to be a
					careful look at the bowling. Now the corner is on fire, jumping from
					{eq !== null ? fmt1(eq.early_rr) : '7.6'} an over to {eq !== null ? fmt1(eq.late_rr) : '9.5'}.
				</p>
			</div>
		{:else}
			<div class="scene-card chip">
				<p>
					And teams paid nothing for it. Look at the flat strip on the right:
					<strong>the same wickets fell, {eq !== null ? fmt2(eq.early_wickets_per_36) : '1.54'} an innings then,
					{eq !== null ? fmt2(eq.late_wickets_per_36) : '1.52'} now.</strong> The extra runs came free.
					<button class="dagger" onclick={() => footnotesOpen.set('phase-economy')} aria-label="How the phases moved">ⓘ</button>
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

	.heat-slot {
		position: absolute;
		top: 12vh;
		left: 50%;
		transform: translateX(-50%);
		margin: 0;
		width: min(34rem, 90vw);
		text-align: center;
	}

	.heat-body {
		display: flex;
		align-items: stretch;
		gap: 6px;
	}

	.heat {
		flex: 1;
		min-width: 0;
		display: grid;
		grid-template-columns: repeat(var(--cols), 1fr);
		gap: 1px;
		border-radius: 6px;
		overflow: hidden;
	}

	.cell {
		aspect-ratio: 1;
		border-radius: 1px;
	}

	/* the powerplay block gets a subtle inset ring once it is the subject */
	.heat.pp-lit .cell.pp {
		box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.14);
	}

	/* the paired wicket strip — same season rows, one cool hue, barely moving */
	.wkt-strip {
		flex: 0 0 12px;
		display: grid;
		grid-template-rows: repeat(var(--rows, 19), 1fr);
		gap: 1px;
		border-radius: 4px;
		overflow: hidden;
		opacity: 0.9;
	}

	.wkt-cell {
		border-radius: 1px;
	}

	.wkt-strip.lit {
		box-shadow: 0 0 0 1px rgba(157, 188, 255, 0.22);
	}

	.heat-axes {
		display: flex;
		justify-content: space-between;
		margin-top: 4px;
		font-size: 0.66rem;
		color: var(--ink-dim);
	}

	.pp-bracket {
		color: #ffb676;
		font-weight: 700;
	}

	.wkt-tag {
		color: hsl(212 34% 64%);
		font-weight: 700;
	}

	figcaption {
		margin-top: 0.4rem;
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.caption-slot {
		/* §0.4(a): the heatmap caption sits bottom-RIGHT, clear of the top-left
		   igniting powerplay band, the right-edge wicket strip and the top-right nav */
		position: absolute;
		right: 6vw;
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
		.heat-slot {
			top: 9vh;
			width: 94vw;
		}

		.caption-slot {
			left: 50%;
			right: auto;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(9vh, calc(env(safe-area-inset-bottom) + 56px));
		}
	}
</style>
