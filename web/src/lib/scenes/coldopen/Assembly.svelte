<script module lang="ts">
	/**
	 * Scroll geometry, exported so index.ts declares the SceneDef from the same
	 * numbers this component uses to map progress → reveal. The morph is the
	 * storyboard's ~300vh scrub; the extra scroll keeps the sticky annotation
	 * pin on screen through the whole scrub plus a settled hold for the title
	 * card (a 100dvh sticky child unpins scrollLength−100vh into its section).
	 */
	export const ASSEMBLY_SCROLL_VH = 420;
	export const ASSEMBLY_MORPH_VH = 300;

	const MORPH_FRACTION = ASSEMBLY_MORPH_VH / ASSEMBLY_SCROLL_VH;
	/** title card fades in once the field has settled (after the scrub ends) */
	const TITLE_AT = 0.74;
</script>

<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { assemblyVisibleCount } from '$lib/story/fieldstate';
	import { footnotesOpen } from '$lib/state';
	import { loadColdOpenData, type ColdOpenData } from './data';

	/**
	 * CO-3 — the assembly (GSAP scrub set piece #1) + title card (storyboard
	 * §1). Every ball streams in chronologically under scroll scrub; the live
	 * counter is driven by assemblyVisibleCount, which mirrors the shader
	 * frontier exactly — it can only ever end at the number the pixels show.
	 * Authored counter stops fire off the same count; their thresholds are
	 * measured from the actual point buffer (first occurrence per season), so
	 * every caption names exactly what is raining in when it fires.
	 */
	let { progress, field, reduced }: SceneAnnotationProps = $props();

	let data = $state<ColdOpenData | null>(null);
	onMount(() => {
		void loadColdOpenData().then((d) => (data = d));
	});

	const n = $derived(field?.data.nPoints ?? 0);
	const reveal = $derived(Math.min(1, Math.max(0, progress / MORPH_FRACTION)));
	const count = $derived(reduced ? n : assemblyVisibleCount(reveal, n));
	const locked = $derived(n > 0 && count >= n);
	const showTitle = $derived(reduced || progress >= TITLE_AT);

	const fmt = (v: number): string => v.toLocaleString('en-US');

	/* ---- title-card counts — every figure reads from an artifact ------------- */
	const deliveries = $derived(n > 0 ? n : (data?.corpus.points_rendered ?? 316199));
	const matches = $derived(data?.corpus.matches ?? 1331);
	const players = $derived(data?.corpus.players ?? 938);
	const iplSeasons = $derived(data?.corpus.ipl_seasons ?? 19);
	const wplSeasons = $derived(data?.corpus.wpl_seasons ?? 4);
	const wplTotal = $derived(
		field
			? field.data.groups.filter((g) => g.league === 'wpl').reduce((s, g) => s + g.count, 0)
			: 20642
	);

	/* ---- authored counter stops (storyboard CO-3, §9) ------------------------- */
	interface Stop {
		id: string;
		/** trigger: fires once `count` reaches this many landed points */
		at: number;
		/** pinned stops hold until the title card; the rest are ephemeral */
		pinned: boolean;
		text: string;
	}

	const stops = $derived.by((): Stop[] => {
		const f = field;
		if (!f || wplTotal <= 0) return [];
		const groups = f.data.groups;
		const gids = f.data.groupIds;
		const giOf = (league: 'ipl' | 'wpl', season: number): number =>
			groups.find((g) => g.league === league && g.season === season)?.gi ?? -1;
		const marks = [giOf('ipl', 2009), giOf('ipl', 2016), giOf('ipl', 2023), giOf('wpl', 2023)];
		const want = new Set(marks.filter((gi) => gi >= 0));
		const first = new Map<number, number>();
		for (let i = 0; i < gids.length && first.size < want.size; i++) {
			const g = gids[i];
			if (want.has(g) && !first.has(g)) first.set(g, i);
		}

		const out: Stop[] = [];
		const t2008 = first.get(marks[0]); // 2008 fully in = first 2009 point
		if (t2008 !== undefined)
			out.push({ id: 's2008', at: t2008, pinned: false, text: `2008: the first ${fmt(t2008)}.` });
		const t2015 = first.get(marks[1]); // 2015 passes = first 2016 point
		if (t2015 !== undefined)
			out.push({ id: 's2015', at: t2015, pinned: false, text: `${fmt(t2015)} and climbing.` });
		const tCeiling = first.get(marks[2]); // the IPL 2023 stream begins
		if (tCeiling !== undefined)
			out.push({
				id: 'ceiling',
				at: tCeiling,
				pinned: false,
				text: '2023: the year the ceiling broke.'
			});
		const tWpl = first.get(marks[3]); // the WPL's first delivery rains in
		if (tWpl !== undefined)
			out.push({
				id: 'wpl',
				at: tWpl,
				pinned: true,
				text: `And a second league assembles — deliberately apart, its own body of light. The WPL: ${fmt(wplTotal)} deliveries.`
			});
		// captions fire in buffer order — each names what is actually raining in.
		// Chronology puts the WPL's March-2023 arrival BEFORE IPL 2023 (the
		// pixels rule outranks the storyboard's assumed order), so the pinned
		// WPL caption fires first and the ceiling stop follows ~5k points later
		// — still one change per beat, in the true order.
		out.sort((a, b) => a.at - b.at);
		return out;
	});

	const micro = $derived.by((): Stop | null => {
		if (reduced || showTitle || reveal >= 1) return null;
		let cur: Stop | null = null;
		for (const s of stops) if (!s.pinned && count >= s.at) cur = s;
		return cur;
	});

	const pinnedStop = $derived.by((): Stop | null => {
		if (reduced || showTitle) return null;
		for (const s of stops) if (s.pinned && count >= s.at) return s;
		return null;
	});
</script>

<div class="pin">
	{#if n > 0 && !reduced}
		<div class="counter" class:locked aria-hidden="true">{fmt(count)}</div>
	{/if}

	<div class="caption-col">
		{#if micro}
			{#key micro.id}
				<div class="scene-card micro">
					<p>{micro.text}</p>
				</div>
			{/key}
		{/if}
		{#if pinnedStop}
			<div class="scene-card wpl-pin">
				<p>{pinnedStop.text}</p>
			</div>
		{/if}
	</div>

	{#if showTitle}
		<div class="title-slot">
			<div class="scene-card title interactive">
				<h1 class="masthead">Every Ball Ever</h1>
				<p class="stats">
					<strong>
						{fmt(deliveries)} deliveries · {fmt(matches)} matches · {iplSeasons} IPL seasons +
						{wplSeasons} WPL seasons · {fmt(players)} players
					</strong>
				</p>
				<p class="note never-leave">
					Every one of them is on this screen right now. They never leave.
					<button
						class="info"
						onclick={() => footnotesOpen.set('ball-count')}
						aria-haspopup="dialog"
						aria-label="What counts as a ball"
					>
						ⓘ
					</button>
				</p>
				{#if reduced}
					<p class="note narration">
						Between 2008 and 2026, {fmt(deliveries)} deliveries were bowled across the IPL and WPL
						— {fmt(matches)} matches, {fmt(players)} players. The WPL’s {fmt(wplTotal)} arrive as
						their own constellation, apart from the IPL’s cloud.
					</p>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.pin {
		position: sticky;
		top: 0;
		height: 100vh;
		height: 100dvh;
	}

	.counter {
		position: absolute;
		top: max(14px, env(safe-area-inset-top));
		left: 50%;
		transform: translateX(-50%);
		font-variant-numeric: tabular-nums;
		font-size: clamp(1rem, 3vw, 1.4rem);
		font-weight: 650;
		letter-spacing: 0.06em;
		color: var(--ink);
		text-shadow: 0 1px 8px rgba(0, 0, 0, 0.6);
	}

	.counter.locked {
		color: var(--gold);
	}

	.caption-col {
		position: absolute;
		left: 50%;
		/* clears the shell's fixed "how we computed this" affordance (bottom
		   14px, ~44px tall) — the pinned WPL caption is the cold open's one
		   authored "deliberately apart" signal and must never sit under it */
		bottom: max(72px, calc(env(safe-area-inset-bottom) + 60px));
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 10px;
		width: max-content;
		max-width: 92vw;
	}

	.caption-col .scene-card {
		text-align: center;
		padding: 0.8rem 1.1rem;
	}

	.caption-col p {
		font-size: clamp(0.95rem, 2.4vw, 1.15rem);
	}

	.micro {
		animation: fadeup 320ms ease-out both;
	}

	.wpl-pin {
		border-color: rgba(46, 196, 182, 0.45);
	}

	@keyframes fadeup {
		from {
			opacity: 0;
			transform: translateY(8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.title-slot {
		position: absolute;
		inset: 0;
		display: grid;
		place-content: center;
		padding: 1.5rem;
	}

	.title {
		text-align: center;
		max-width: min(36rem, 90vw);
		animation: fadeup 500ms ease-out both;
	}

	.masthead {
		font-size: clamp(2rem, 7vw, 3.4rem);
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.stats {
		margin-top: 0.7rem;
		font-size: clamp(0.92rem, 2.4vw, 1.1rem);
		color: var(--ink);
	}

	.never-leave {
		font-size: 0.9rem;
	}

	.narration {
		border-top: 1px solid rgba(232, 236, 245, 0.12);
		padding-top: 0.6rem;
	}

	.info {
		display: inline-grid;
		place-content: center;
		min-width: 44px;
		min-height: 44px;
		margin: -12px -6px;
		padding: 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 1rem;
		cursor: pointer;
		vertical-align: middle;
	}

	.info:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
		border-radius: 8px;
	}

	@media (prefers-reduced-motion: reduce) {
		.micro,
		.title {
			animation: none;
		}
	}
</style>
