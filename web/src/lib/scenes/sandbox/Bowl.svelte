<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import type { FilterMode } from '$lib/field/types';
	import { pickedTeam } from '$lib/state';
	import {
		loadSandboxData,
		deriveMatchRange,
		buildTooltip,
		buildGroupSeason,
		countVisible,
		teamIdFor,
		syncBowlHeld,
		type Facets,
		type BallTooltip,
		type SandboxData
	} from './data';

	/**
	 * THE BOWL — "The Field Is Yours" (blueprint §3, R1b minimal scope). The
	 * persistent 316k-ball field becomes a filterable instrument: TEAM + SEASON
	 * facets, ONE famous-match preset, and a tap-a-ball tooltip that names the
	 * exact delivery. Opens PRE-FILTERED to the reader's picked team (never
	 * blank); a neutral reader opens on the preset instead.
	 *
	 * Demand-mode preserved: every facet change is ONE static `field.setFilter`
	 * render; a tap is ONE offscreen pick pass (no visible-frame render, no rAF
	 * loop). All facets are also mirrored into the orchestrator-read held state
	 * (`syncBowlHeld`) so a stray scroll can never revert them (CONTRACT §12.2).
	 */
	let { progress, active, field }: SceneAnnotationProps = $props();

	/* ---- facet UI state (string-backed for the native selects) --------------- */
	let teamSel = $state('');   // '' = all teams, else String(teams.json id)
	let seasonSel = $state(''); // '' = all seasons, else String(year)
	let matchRange = $state<readonly [number, number] | null>(null);
	let mode = $state<FilterMode>('dim');

	const selTeam = $derived(teamSel === '' ? null : Number(teamSel));
	const selSeason = $derived(seasonSel === '' ? null : Number(seasonSel));
	const presetActive = $derived(matchRange != null);
	const facets = $derived<Facets>({ team: selTeam, season: selSeason, matchRange, mode });

	/* ---- lazily-loaded sandbox dataset (columnar + matches + descriptor) ------ */
	let sandbox = $state<SandboxData | null>(null);
	let presetRange = $state<readonly [number, number] | null>(null);
	let loadError = $state<string | null>(null);
	let loadStarted = false;

	/* ---- field-derived option lists + the live count ------------------------- */
	const groupSeason = $derived(field ? buildGroupSeason(field.data) : null);
	const teams = $derived(field?.data.teams ?? []);
	const iplTeams = $derived(teams.filter((t) => t.league === 'ipl'));
	const wplTeams = $derived(teams.filter((t) => t.league === 'wpl'));
	const seasons = $derived.by(() => {
		const set = new Set<number>();
		for (const g of field?.data.groups ?? []) set.add(g.season);
		return [...set].sort((a, b) => a - b);
	});
	const count = $derived.by(() => {
		if (!field || !groupSeason) return null;
		return countVisible(field.data, groupSeason, facets);
	});

	const selectionLabel = $derived.by(() => {
		if (presetActive) return sandbox?.descriptor.preset.label ?? 'Famous match';
		const t = teams.find((tm) => tm.id === selTeam);
		const teamLabel = t ? `${t.name}${t.league === 'wpl' ? ' (WPL)' : ''}` : 'All teams';
		return `${teamLabel} · ${selSeason != null ? selSeason : 'All seasons'}`;
	});

	/* ---- the one write path: mirror held state + render once ------------------ */
	function commit(o: {
		team?: string;
		season?: string;
		matchRange?: readonly [number, number] | null;
		mode?: FilterMode;
	}): void {
		if (o.team !== undefined) teamSel = o.team;
		if (o.season !== undefined) seasonSel = o.season;
		if (o.matchRange !== undefined) matchRange = o.matchRange;
		if (o.mode !== undefined) mode = o.mode;
		const f: Facets = {
			team: teamSel === '' ? null : Number(teamSel),
			season: seasonSel === '' ? null : Number(seasonSel),
			matchRange,
			mode
		};
		syncBowlHeld(f); // guard against a stray scroll re-applying the scene state
		field?.setFilter({ team: f.team, season: f.season, matchRange: f.matchRange, mode: f.mode });
		// a facet change can hide the tooltip's ball → drop it
		tooltip = null;
		kbIndex = null;
	}

	function onTeamChange(): void {
		commit({ team: teamSel, matchRange: null, mode: 'dim' });
	}
	function onSeasonChange(): void {
		commit({ season: seasonSel, matchRange: null, mode: 'dim' });
	}
	function applyPreset(): void {
		if (!presetRange) return;
		commit({ team: '', season: '', matchRange: presetRange, mode: 'hide' });
	}
	function exitPreset(): void {
		commit({ team: '', season: '', matchRange: null, mode: 'dim' });
	}

	/* ---- lazy load on entering the Bowl (not in the cold-open payload) -------- */
	$effect(() => {
		if (!(active || progress > 0) || !field || loadStarted) return;
		loadStarted = true;
		loadSandboxData()
			.then((d) => {
				sandbox = d;
				presetRange = deriveMatchRange(d.columnar, d.descriptor.preset.match_index);
			})
			.catch((e) => (loadError = e instanceof Error ? e.message : String(e)));
	});
	$effect(() => {
		if (sandbox) loadingPickHint = false;
	});

	/* ---- open pre-filtered — never blank (only once the Bowl is active) ------- */
	let opened = false;
	$effect(() => {
		if (!active || !field || opened) return;
		const pick = $pickedTeam;
		if (pick && pick.league !== null && pick.team !== 'neutral') {
			const id = teamIdFor(field.data.teams, pick.league, pick.team);
			if (id != null) {
				commit({ team: String(id), season: '', matchRange: null, mode: 'dim' });
				opened = true;
				return;
			}
		}
		// neutral / unmapped → open on the famous-match preset (waits for columnar;
		// the effect re-runs when presetRange resolves). Full field shows meanwhile.
		if (presetRange) {
			commit({ team: '', season: '', matchRange: presetRange, mode: 'hide' });
			opened = true;
		}
	});

	/* ---- tap-a-ball tooltip + keyboard inspector ----------------------------- */
	let tooltip = $state<{ t: BallTooltip; x: number; y: number; anchored: boolean } | null>(null);
	let kbIndex = $state<number | null>(null);
	let loadingPickHint = $state(false);
	let surfaceEl = $state<HTMLDivElement | null>(null);

	function tooltipFor(idx: number, x: number, y: number, anchored: boolean): void {
		if (!sandbox) {
			loadingPickHint = true;
			return;
		}
		kbIndex = idx;
		tooltip = { t: buildTooltip(sandbox.columnar, sandbox.matches, idx), x, y, anchored };
	}

	function onSurfaceClick(e: MouseEvent): void {
		const f = field;
		const el = surfaceEl;
		if (!f || !el) return;
		const r = el.getBoundingClientRect();
		const x = e.clientX - r.left;
		const y = e.clientY - r.top;
		const idx = f.pickAt(x, y, 24); // finger-friendly radius
		if (idx == null) {
			tooltip = null;
			kbIndex = null;
			return;
		}
		tooltipFor(idx, x, y, true);
	}

	/** dir 0 = first visible ball; ±1 = step from the current one. */
	function inspectStep(dir: 0 | 1 | -1): void {
		const f = field;
		if (!f) return;
		if (!sandbox) {
			loadingPickHint = true;
			return;
		}
		const idx = dir === 0 || kbIndex == null ? f.firstVisiblePoint() : f.stepVisiblePoint(kbIndex, dir);
		if (idx == null) return; // at an end (or the filter hides everything)
		tooltipFor(idx, 0, 0, false);
	}

	function onInspectKeydown(e: KeyboardEvent): void {
		if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
			e.preventDefault();
			inspectStep(1);
		} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
			e.preventDefault();
			inspectStep(-1);
		} else if (e.key === 'Home') {
			e.preventDefault();
			inspectStep(0);
		}
	}

	function dismiss(): void {
		tooltip = null;
		kbIndex = null;
	}

	/** Anchored (tap) tooltip position, clamped into the viewport. */
	function tipStyle(t: { x: number; y: number; anchored: boolean }): string {
		if (!t.anchored || typeof window === 'undefined') return '';
		const vw = window.innerWidth;
		const vh = window.innerHeight;
		const w = Math.min(320, vw * 0.9);
		let left = t.x + 14;
		if (left + w > vw - 8) left = t.x - w - 14;
		if (left < 8) left = 8;
		let top = t.y + 14;
		const approxH = 230;
		if (top + approxH > vh - 8) top = Math.max(8, t.y - approxH - 14);
		return `left:${left}px; top:${top}px; width:${w}px;`;
	}

	onMount(() => {
		const onKey = (e: KeyboardEvent): void => {
			if (e.key === 'Escape' && tooltip) dismiss();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

<div class="bowl" class:active>
	<!-- the field itself is the surface: a tap resolves to the nearest visible
	     ball. touch-action pan-y keeps native vertical scroll; onclick (not
	     pointerdown) means a scroll-drag never fires a pick. -->
	<div
		class="pick-surface"
		bind:this={surfaceEl}
		onclick={onSurfaceClick}
		role="presentation"
	></div>

	<!-- intro (non-interactive) -->
	<div class="intro">
		<p class="overline">The Bowl · The Field Is Yours</p>
		<p class="lede">The field is yours. Every ball ever — filter it, tap it.</p>
		<p class="hint">Tap any lit ball to name the exact delivery.</p>
	</div>

	<!-- the famous-match preset card (shown while the preset is engaged) -->
	{#if presetActive && sandbox}
		{@const p = sandbox.descriptor.preset}
		{@const m = sandbox.matches[p.match_index]}
		<div class="preset-card" role="region" aria-label="Famous match preset">
			<p class="preset-label">{p.label}</p>
			{#if m}<p class="preset-result">{m.result_text} · {m.venue}</p>{/if}
			<p class="preset-blurb">{p.blurb}</p>
			<button class="link" type="button" onclick={exitPreset}>← Back to the whole field</button>
		</div>
	{/if}

	<!-- the tap-a-ball / keyboard tooltip -->
	{#if tooltip}
		{@const t = tooltip.t}
		<div
			class="tooltip"
			class:kb={!tooltip.anchored}
			style={tipStyle(tooltip)}
			role="dialog"
			aria-label="Ball detail"
		>
			<button class="close" type="button" onclick={dismiss} aria-label="Dismiss">×</button>
			<p class="tt-headline"><strong>{t.batter}</strong> <span class="v">vs</span> {t.bowler}</p>
			<p class="tt-teams">{t.battingTeam} <span class="v">vs</span> {t.opponent}</p>
			<p class="tt-match">{t.matchLabel}{#if t.date} · {t.date}{/if}</p>
			{#if t.venue}<p class="tt-venue">{t.venue}</p>{/if}
			<p class="tt-line">
				<span class="over">Over {t.overBall}</span>
				<span class="sep">·</span>
				<span class="inn">{t.inningsLabel}</span>
			</p>
			<p class="tt-result">{t.result}</p>
			{#if t.resultText}<p class="tt-final">{t.resultText}</p>{/if}
		</div>
	{/if}

	<!-- controls: bottom bar, thumb-reachable, keyboard-navigable -->
	<div class="controls" role="group" aria-label="Filter the field">
		<div class="facets">
			<label class="facet-l">
				<span class="lbl">Team</span>
				<select bind:value={teamSel} onchange={onTeamChange} aria-label="Filter by team">
					<option value="">All teams</option>
					<optgroup label="IPL">
						{#each iplTeams as t (t.id)}
							<option value={String(t.id)}>{t.short} — {t.name}</option>
						{/each}
					</optgroup>
					<optgroup label="WPL">
						{#each wplTeams as t (t.id)}
							<option value={String(t.id)}>{t.short} — {t.name}</option>
						{/each}
					</optgroup>
				</select>
			</label>

			<label class="facet-l">
				<span class="lbl">Season</span>
				<select bind:value={seasonSel} onchange={onSeasonChange} aria-label="Filter by season">
					<option value="">All seasons</option>
					{#each seasons as y (y)}
						<option value={String(y)}>{y}</option>
					{/each}
				</select>
			</label>
		</div>

		<div class="actions">
			<button
				class="preset-btn"
				type="button"
				onclick={applyPreset}
				disabled={!presetRange}
				aria-pressed={presetActive}
			>
				{#if sandbox}
					<span class="pb-kicker">Famous match</span>
					<span class="pb-label">{sandbox.descriptor.preset.label}</span>
				{:else}
					<span class="pb-kicker">Loading the sandbox…</span>
				{/if}
			</button>

			<button
				class="inspect-btn"
				type="button"
				onclick={() => inspectStep(0)}
				onkeydown={onInspectKeydown}
				aria-label="Inspect a ball with the keyboard; use arrow keys to step"
			>
				⌨ Inspect a ball
			</button>
		</div>

		<div class="readout" aria-live="polite">
			<span class="rd-sel">{selectionLabel}</span>
			<span class="rd-count"
				>{count != null ? count.toLocaleString('en-US') : '—'}<span class="rd-unit"> balls</span></span
			>
		</div>

		{#if loadingPickHint}
			<p class="mini-note" role="status">Reading the ball data… tap again in a moment.</p>
		{:else if loadError}
			<p class="mini-note err" role="status">Couldn’t load the sandbox data ({loadError}).</p>
		{/if}
	</div>
</div>

<style>
	/* the whole overlay matches the persistent field container (100dvh) so a tap's
	   coordinates map 1:1 to the field's pick pass. Hidden (and inert) unless the
	   Bowl owns the field. */
	.bowl {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100dvh;
		pointer-events: none;
		visibility: hidden;
		z-index: 0;
	}

	.bowl.active {
		visibility: visible;
	}

	.pick-surface {
		position: absolute;
		inset: 0;
		z-index: 1;
		pointer-events: auto;
		touch-action: pan-y; /* keep native vertical scroll; taps still pick */
		cursor: crosshair;
	}

	/* ---- intro ---- */
	.intro {
		position: absolute;
		top: max(14px, env(safe-area-inset-top));
		left: 50%;
		transform: translateX(-50%);
		width: min(560px, 92vw);
		z-index: 2;
		pointer-events: none;
		text-align: center;
	}

	.overline {
		margin: 0;
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.26em;
		text-transform: uppercase;
		color: var(--gold);
	}

	.lede {
		margin: 0.35rem 0 0;
		font-size: clamp(1.05rem, 2.8vw, 1.35rem);
		line-height: 1.35;
		color: var(--ink);
		text-shadow: 0 1px 12px rgba(11, 14, 20, 0.8);
	}

	.hint {
		margin: 0.3rem 0 0;
		font-size: 0.8rem;
		color: var(--ink-dim);
		text-shadow: 0 1px 10px rgba(11, 14, 20, 0.9);
	}

	/* ---- preset card ---- */
	.preset-card {
		position: absolute;
		top: max(96px, calc(env(safe-area-inset-top) + 84px));
		left: 50%;
		transform: translateX(-50%);
		width: min(520px, 92vw);
		z-index: 3;
		pointer-events: auto;
		padding: 0.85rem 1rem;
		border-radius: 14px;
		border: 1px solid rgba(46, 196, 182, 0.4);
		background: rgba(11, 14, 20, 0.9);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
	}

	.preset-label {
		margin: 0;
		font-size: 0.98rem;
		font-weight: 700;
		line-height: 1.3;
		color: var(--ink);
	}

	.preset-result {
		margin: 0.3rem 0 0;
		font-size: 0.82rem;
		color: var(--teal);
	}

	.preset-blurb {
		margin: 0.35rem 0 0;
		font-size: 0.86rem;
		line-height: 1.45;
		color: var(--ink-dim);
	}

	.link {
		margin-top: 0.5rem;
		padding: 0.5rem 0;
		min-height: 44px;
		border: none;
		background: none;
		color: var(--teal);
		font: inherit;
		font-size: 0.85rem;
		cursor: pointer;
	}

	.link:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* ---- tooltip ---- */
	.tooltip {
		position: absolute;
		z-index: 5;
		pointer-events: auto;
		max-width: 92vw;
		padding: 0.7rem 0.85rem 0.8rem;
		border-radius: 12px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		background: rgba(11, 14, 20, 0.95);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
		font-variant-numeric: tabular-nums;
	}

	/* keyboard-selected balls have no tap location → fixed above the controls */
	.tooltip.kb {
		left: 50%;
		transform: translateX(-50%);
		bottom: calc(env(safe-area-inset-bottom) + 168px);
		width: min(320px, 92vw);
	}

	.close {
		position: absolute;
		top: 4px;
		right: 4px;
		width: 40px;
		height: 40px;
		border: none;
		border-radius: 10px;
		background: transparent;
		color: var(--ink-dim);
		font-size: 1.3rem;
		line-height: 1;
		cursor: pointer;
	}

	.close:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: -3px;
	}

	.tooltip p {
		margin: 0;
	}

	.tt-headline {
		font-size: 0.98rem;
		line-height: 1.3;
		color: var(--ink);
		padding-right: 26px;
	}

	.tt-teams {
		margin-top: 0.15rem !important;
		font-size: 0.86rem;
		color: var(--ink);
	}

	.v {
		color: var(--ink-dim);
		font-weight: 400;
	}

	.tt-match {
		margin-top: 0.4rem !important;
		font-size: 0.82rem;
		color: var(--gold);
	}

	.tt-venue {
		font-size: 0.78rem;
		color: var(--ink-dim);
	}

	.tt-line {
		margin-top: 0.4rem !important;
		font-size: 0.82rem;
		color: var(--ink-dim);
	}

	.tt-line .sep {
		margin: 0 0.35rem;
	}

	.tt-result {
		margin-top: 0.35rem !important;
		font-size: 0.95rem;
		font-weight: 700;
		color: var(--teal);
	}

	.tt-final {
		margin-top: 0.2rem !important;
		font-size: 0.78rem;
		color: var(--ink-dim);
	}

	/* ---- controls ---- */
	.controls {
		position: absolute;
		left: 50%;
		transform: translateX(-50%);
		bottom: max(12px, env(safe-area-inset-bottom));
		width: min(640px, 96vw);
		z-index: 4;
		pointer-events: auto;
		padding: 0.7rem 0.8rem 0.75rem;
		border-radius: 16px;
		border: 1px solid rgba(232, 236, 245, 0.12);
		background: rgba(11, 14, 20, 0.82);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
	}

	.facets {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
	}

	.facet-l {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.lbl {
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	select {
		width: 100%;
		min-height: 44px;
		padding: 0 0.6rem;
		border-radius: 10px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		background: rgba(232, 236, 245, 0.06);
		color: var(--ink);
		font: inherit;
		font-size: 0.9rem;
		cursor: pointer;
		-webkit-appearance: none;
		appearance: none;
	}

	select:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 1px;
	}

	.actions {
		display: flex;
		gap: 8px;
		margin-top: 8px;
	}

	.preset-btn {
		flex: 1 1 auto;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 1px;
		min-height: 44px;
		padding: 0.4rem 0.7rem;
		border-radius: 10px;
		border: 1px solid rgba(46, 196, 182, 0.45);
		background: rgba(46, 196, 182, 0.1);
		color: var(--ink);
		font: inherit;
		text-align: left;
		cursor: pointer;
	}

	.preset-btn[aria-pressed='true'] {
		background: rgba(46, 196, 182, 0.22);
		box-shadow: 0 0 0 1px var(--teal);
	}

	.preset-btn:disabled {
		opacity: 0.55;
		cursor: default;
	}

	.preset-btn:focus-visible,
	.inspect-btn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.pb-kicker {
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--teal);
	}

	.pb-label {
		font-size: 0.78rem;
		line-height: 1.25;
		color: var(--ink);
	}

	.inspect-btn {
		flex: 0 0 auto;
		min-height: 44px;
		padding: 0 0.8rem;
		border-radius: 10px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		background: rgba(232, 236, 245, 0.05);
		color: var(--ink);
		font: inherit;
		font-size: 0.82rem;
		cursor: pointer;
	}

	.readout {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 10px;
		margin-top: 9px;
		padding-top: 8px;
		border-top: 1px solid rgba(232, 236, 245, 0.1);
	}

	.rd-sel {
		font-size: 0.82rem;
		color: var(--ink-dim);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.rd-count {
		flex: none;
		font-size: 1.05rem;
		font-weight: 700;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.rd-unit {
		font-size: 0.78rem;
		font-weight: 400;
		color: var(--ink-dim);
	}

	.mini-note {
		margin: 8px 0 0;
		font-size: 0.76rem;
		color: var(--ink-dim);
	}

	.mini-note.err {
		color: var(--ember);
	}

	@media (min-width: 560px) {
		.actions {
			align-items: stretch;
		}
	}
</style>
