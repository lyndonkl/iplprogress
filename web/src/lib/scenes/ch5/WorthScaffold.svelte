<script lang="ts">
	import { onMount } from 'svelte';
	import type { FieldHandle } from '$lib/field/field';
	import { worthCell } from '$lib/field/layout';

	/**
	 * Shared destination-first scaffold for the worth grid (C5-5 .. C5-10): the
	 * over axis along the bottom, the wickets-down axis up the left (0 at the
	 * TOP), the two axis titles, and the small persistent axis tag so orientation
	 * survives deep entry (storyboard §0.4a). Registered to the GL cells via
	 * `worthCell` + `projectToCss` (the exact shader mapping — CONTRACT §19.5);
	 * rebuilt on resize.
	 */
	let { field, on = true }: { field: FieldHandle | null; on?: boolean } = $props();

	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => {
				tick++;
			});
		};
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});
	let seeded = false;
	$effect(() => {
		if (field && !seeded) {
			seeded = true;
			tick++;
		}
	});

	/** display overs (1-based) that get a bottom tick */
	const OVER_TICKS = [1, 5, 10, 15, 20] as const;
	/** wickets-down rows that get a left tick */
	const WKT_TICKS = [0, 3, 6, 9] as const;

	const geo = $derived.by(() => {
		void tick;
		const f = field;
		const wl = f?.getWorthLayout();
		if (!f || !wl) return null;
		const overs = OVER_TICKS.map((o) => {
			const c = worthCell(wl, o - 1, 9);
			return { label: String(o), ...f.projectToCss(c.x, wl.bottom - wl.cellH * 0.35) };
		});
		const wkts = WKT_TICKS.map((w) => {
			const c = worthCell(wl, 0, w);
			return { label: String(w), ...f.projectToCss(wl.left - wl.cellW * 0.45, c.y) };
		});
		const overTitle = f.projectToCss(wl.left + wl.width / 2, wl.bottom - wl.cellH * 1.3);
		const wktTitle = f.projectToCss(wl.left - wl.cellW * 1.5, wl.bottom + wl.height / 2);
		return { overs, wkts, overTitle, wktTitle };
	});
</script>

{#if geo && on}
	<div class="scaffold" aria-hidden="true">
		{#each geo.overs as t (t.label)}
			<span class="tick" style="left:{t.x.toFixed(1)}px; top:{t.y.toFixed(1)}px;">{t.label}</span>
		{/each}
		{#each geo.wkts as t (t.label)}
			<span class="tick wkt" style="left:{t.x.toFixed(1)}px; top:{t.y.toFixed(1)}px;">{t.label}</span>
		{/each}
		<span class="title" style="left:{geo.overTitle.x.toFixed(1)}px; top:{geo.overTitle.y.toFixed(1)}px;">
			over of the innings →
		</span>
		<span class="title rot" style="left:{geo.wktTitle.x.toFixed(1)}px; top:{geo.wktTitle.y.toFixed(1)}px;">
			wickets down ↓
		</span>
		<!-- the persistent axis tag (orientation survives deep entry) -->
		<span class="axis-tag">over 1 → 20 across · 0 → 9 wickets down, none at the top</span>
	</div>
{/if}

<style>
	.scaffold {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.tick {
		position: absolute;
		transform: translate(-50%, -50%);
		font-size: 10px;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
	}

	.title {
		position: absolute;
		transform: translate(-50%, -50%);
		font-size: 10.5px;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--ink-dim);
		white-space: nowrap;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
	}

	.title.rot {
		transform: translate(-50%, -50%) rotate(-90deg);
	}

	.axis-tag {
		position: absolute;
		left: 4vw;
		bottom: max(2.2vh, env(safe-area-inset-bottom));
		font-size: 10px;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--ink-dim);
		white-space: nowrap;
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
	}

	@media (max-width: 640px) {
		.axis-tag {
			font-size: 8.5px;
		}
	}
</style>
