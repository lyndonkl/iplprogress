<script lang="ts">
	import { onDestroy } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import type { TeamMeta } from '$lib/field/types';
	import { pickedTeam } from '$lib/state';
	import { crestText, lineTint } from './crest';
	import { consumeReturnTarget } from './changeteam';
	import { scrollToElement } from './scroll';

	/**
	 * Scene TP — the team picker (storyboard §2). One tap-screen after the
	 * title card: the neutral tile first and FULL-WIDTH (the skip IS a tile,
	 * identical styling, above the fold), then 10 IPL + 5 WPL typographic
	 * crests. Single tap selects: the store write ignites the franchise's
	 * balls field-wide (shell plumbing — one render, demand mode), a toast
	 * confirms and persists into C1-1, and the page auto-advances after ~1.2s.
	 * Reduced motion: no auto-advance — an explicit Continue button instead.
	 */
	let { field, reduced }: SceneAnnotationProps = $props();

	const AUTO_ADVANCE_MS = 1200;
	// ~1.2s here + ~1.2s into C1-1 (finding #19 / storyboard §2): the
	// change-anytime reassurance travels with the reader instead of racing the
	// auto-advance, and persists long enough for the now-wrapping two-line toast
	// (finding #9) to be read before it dismisses itself early in C1-1.
	const TOAST_LIFE_MS = 2400;

	const teams = $derived(field?.data.teams.filter((t) => t.active) ?? []);
	const ipl = $derived(teams.filter((t) => t.league === 'ipl'));
	const wpl = $derived(teams.filter((t) => t.league === 'wpl'));
	/** flat roving order: neutral · IPL · WPL — must match DOM order below */
	const flat = $derived<(TeamMeta | null)[]>([null, ...ipl, ...wpl]);

	const selectedKey = $derived(
		$pickedTeam === null
			? null
			: $pickedTeam.league === null || $pickedTeam.team === 'neutral'
				? 'neutral'
				: `${$pickedTeam.league}|${$pickedTeam.team}`
	);

	let rootEl = $state<HTMLElement | null>(null);
	let tilesEl = $state<HTMLElement | null>(null);
	let toast = $state<string | null>(null);
	let rovingIdx = $state(0);
	let rovingSeeded = false;

	let advanceTimer: ReturnType<typeof setTimeout> | null = null;
	let toastTimer: ReturnType<typeof setTimeout> | null = null;

	// seed the roving-tabindex position on the already-picked tile (returning
	// visitors land with their team focus-ready), once the tiles exist
	$effect(() => {
		if (rovingSeeded || flat.length <= 1) return;
		const key = selectedKey ?? 'neutral';
		const idx = flat.findIndex((t) => (t === null ? 'neutral' : `${t.league}|${t.name}`) === key);
		if (idx >= 0) rovingIdx = idx;
		rovingSeeded = true;
	});

	function keyOf(t: TeamMeta | null): string {
		return t === null ? 'neutral' : `${t.league}|${t.name}`;
	}

	function select(t: TeamMeta | null): void {
		if (t === null) pickedTeam.set({ league: null, team: 'neutral', ts: Date.now() });
		else pickedTeam.set({ league: t.league, team: t.name, ts: Date.now() });

		toast =
			t === null
				? 'The whole field it is. Change anytime in ☰.'
				: `${t.name} it is. Change anytime in ☰.`;
		if (toastTimer !== null) clearTimeout(toastTimer);
		toastTimer = setTimeout(() => (toast = null), TOAST_LIFE_MS);

		// tapping a different tile inside the window re-selects (timer resets);
		// reduced motion replaces the auto-advance with the Continue button
		if (advanceTimer !== null) clearTimeout(advanceTimer);
		advanceTimer = null;
		if (!reduced) advanceTimer = setTimeout(advance, AUTO_ADVANCE_MS);
	}

	function advance(): void {
		advanceTimer = null;
		// a change-team round trip from the payoff card returns to the card
		const target = consumeReturnTarget() ?? nextSection();
		if (target !== null) scrollToElement(target, reduced);
	}

	function nextSection(): HTMLElement | null {
		const next = rootEl?.closest('section.scene')?.nextElementSibling;
		return next instanceof HTMLElement ? next : document.getElementById('ch1');
	}

	/* ---- roving-tabindex grid (storyboard §2: tiles are buttons) ---------- */
	function onTileKeydown(e: KeyboardEvent): void {
		let next = rovingIdx;
		switch (e.key) {
			case 'ArrowRight':
			case 'ArrowDown':
				next = Math.min(flat.length - 1, rovingIdx + 1);
				break;
			case 'ArrowLeft':
			case 'ArrowUp':
				next = Math.max(0, rovingIdx - 1);
				break;
			case 'Home':
				next = 0;
				break;
			case 'End':
				next = flat.length - 1;
				break;
			default:
				return;
		}
		e.preventDefault();
		rovingIdx = next;
		const tiles = tilesEl?.querySelectorAll<HTMLButtonElement>('button.tile');
		tiles?.[next]?.focus();
	}

	onDestroy(() => {
		if (advanceTimer !== null) clearTimeout(advanceTimer);
		if (toastTimer !== null) clearTimeout(toastTimer);
	});
</script>

{#snippet crestTile(t: TeamMeta, idx: number)}
	<button
		class="tile"
		type="button"
		style:--ring={lineTint(t.color)}
		aria-pressed={selectedKey === keyOf(t)}
		tabindex={rovingIdx === idx ? 0 : -1}
		onfocus={() => (rovingIdx = idx)}
		onkeydown={onTileKeydown}
		onclick={() => select(t)}
	>
		<span class="chip" style:background={t.color} style:color={crestText(t.color)}>
			{t.short}
		</span>
		<!-- sr-only " (WPL)" gives the sister franchises unique accessible names
		     regardless of whether the SR announces the group label (finding #15) -->
		<span class="name">{t.name}{#if t.league === 'wpl'}<span class="sr-only"> (WPL)</span>{/if}</span>
		{#if t.league === 'wpl'}<span class="tag" aria-hidden="true">WPL</span>{/if}
	</button>
{/snippet}

<div class="pin" bind:this={rootEl}>
	<div class="panel">
		<p class="bridge">Thirty-odd thousand of these dots belong to one team. Yours?</p>
		<h2>Pick your team.</h2>
		<p class="sub">Its balls light up in its colors, and stay lit through the whole story.</p>

		<div class="tiles" bind:this={tilesEl} role="group" aria-label="Pick your team">
			<!-- the skip IS a tile: first, full-width, identical styling (locked rule) -->
			<button
				class="tile neutral"
				type="button"
				style:--ring="var(--ink-dim)"
				aria-pressed={selectedKey === 'neutral'}
				tabindex={rovingIdx === 0 ? 0 : -1}
				onfocus={() => (rovingIdx = 0)}
				onkeydown={onTileKeydown}
				onclick={() => select(null)}
			>
				<span class="chip all">ALL</span>
				<span class="name">No team. Show me everything.</span>
			</button>

			{#if teams.length > 0}
				<h3 class="group-h" id="picker-grp-ipl">IPL</h3>
				<div class="grid" role="group" aria-labelledby="picker-grp-ipl">
					{#each ipl as t, j (t.id)}
						{@render crestTile(t, 1 + j)}
					{/each}
				</div>

				<h3 class="group-h" id="picker-grp-wpl">WPL</h3>
				<div class="grid" role="group" aria-labelledby="picker-grp-wpl">
					{#each wpl as t, j (t.id)}
						{@render crestTile(t, 1 + ipl.length + j)}
					{/each}
				</div>
			{:else}
				<p class="note" role="status">The teams are still loading in with the field…</p>
			{/if}
		</div>

		<div class="under">
			<p class="note">You can change this anytime from the menu.</p>
			{#if $pickedTeam !== null}
				<button class="continue" type="button" onclick={advance}>Continue →</button>
			{/if}
		</div>
	</div>

	{#if toast !== null}
		<div class="toast" class:animate={!reduced} role="status">{toast}</div>
	{/if}
</div>

<style>
	.pin {
		position: sticky;
		top: 0;
		height: 100vh;
		height: 100dvh;
		display: grid;
		place-items: center;
		padding: 12px;
	}

	/* translucent over the dimmed field: the ignite preview stays visible
	   behind the grid (storyboard §2, mobile note) */
	.panel {
		pointer-events: auto;
		width: min(720px, 94vw);
		max-height: calc(100dvh - 24px);
		overflow-y: auto;
		background: rgba(11, 14, 20, 0.62);
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 16px;
		padding: 1.2rem 1.2rem 1.35rem;
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
	}

	.bridge {
		margin: 0 0 0.65rem;
		font-size: clamp(1rem, 2.4vw, 1.2rem);
		line-height: 1.45;
		color: var(--ink);
	}

	h2 {
		margin: 0;
		font-size: clamp(1.5rem, 4vw, 2.1rem);
		line-height: 1.2;
		font-weight: 650;
	}

	.sub {
		margin: 0.4rem 0 1rem;
		font-size: 0.95rem;
		line-height: 1.45;
		color: var(--ink-dim);
	}

	.group-h {
		margin: 1rem 0 0.5rem;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.28em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 10px;
	}

	@media (min-width: 720px) {
		.grid {
			grid-template-columns: repeat(4, 1fr);
		}
	}

	.tile {
		position: relative;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		justify-content: center;
		gap: 8px;
		min-height: 88px;
		padding: 12px;
		border-radius: 12px;
		border: 1px solid rgba(232, 236, 245, 0.14);
		background: rgba(232, 236, 245, 0.04);
		color: var(--ink);
		font: inherit;
		text-align: left;
		cursor: pointer;
	}

	.tile:hover {
		background: rgba(232, 236, 245, 0.08);
	}

	.tile[aria-pressed='true'] {
		border-color: transparent;
		box-shadow: 0 0 0 2px var(--ring);
	}

	.tile:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* the neutral tile: full-width, first, above the fold — same tile styling */
	.tile.neutral {
		width: 100%;
		flex-direction: row;
		align-items: center;
	}

	.chip {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 46px;
		height: 28px;
		padding: 0 8px;
		border-radius: 7px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		font-weight: 750;
		font-size: 0.82rem;
		letter-spacing: 0.06em;
	}

	.chip.all {
		background: rgba(232, 236, 245, 0.12);
		color: var(--ink);
	}

	.name {
		font-size: 0.86rem;
		line-height: 1.3;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		margin: -1px;
		padding: 0;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
		border: 0;
	}

	.tag {
		position: absolute;
		top: 8px;
		right: 10px;
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.18em;
		color: var(--teal);
	}

	.under {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		margin-top: 1rem;
		flex-wrap: wrap;
	}

	.note {
		margin: 0;
		font-size: 0.8rem;
		line-height: 1.4;
		color: var(--ink-dim);
	}

	.continue {
		min-height: 44px;
		padding: 0.5rem 1.1rem;
		border-radius: 999px;
		border: 1px solid rgba(46, 196, 182, 0.5);
		background: rgba(46, 196, 182, 0.12);
		color: var(--ink);
		font: inherit;
		font-size: 0.9rem;
		cursor: pointer;
	}

	.continue:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* fixed so it survives the auto-advance into C1-1 (storyboard §2) */
	.toast {
		position: fixed;
		left: 50%;
		bottom: max(20px, env(safe-area-inset-bottom));
		transform: translateX(-50%);
		z-index: 70;
		/* wrap rather than ellipsize — the "Change anytime in ☰" reassurance is
		   the line that justifies the no-confirm design and must never be cut
		   (finding #9). Bottom-anchored, so a two-line toast still clears the
		   safe area and never covers the neutral tile at the top of the panel. */
		max-width: min(92vw, 30rem);
		padding: 0.65rem 1.15rem;
		border-radius: 14px;
		border: 1px solid rgba(46, 196, 182, 0.4);
		background: rgba(11, 14, 20, 0.88);
		color: var(--ink);
		font-size: 0.9rem;
		white-space: normal;
		text-align: center;
		pointer-events: none;
	}

	.toast.animate {
		animation: toast-in 200ms ease-out;
	}

	@keyframes toast-in {
		from {
			opacity: 0;
			transform: translateX(-50%) translateY(6px);
		}
		to {
			opacity: 1;
			transform: translateX(-50%) translateY(0);
		}
	}
</style>
