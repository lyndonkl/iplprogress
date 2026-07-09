<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import type { Columnar, MatchInfo } from '../data';
	import { computeSelectionStats, type SelectionStats } from './select-stats';

	/**
	 * THE BOWL: the linked breakdown panel (r6b spec §5). Three small oriented views
	 * of the CURRENT selection (the worm, the runs-per-over Manhattan, the leaderboard),
	 * coordinated with the field because it consumes the SAME `mask` the field got, so
	 * the panel and the field can never drift.
	 *
	 * Two surfaces in one component:
	 *  - the always-on desktop COUPLING STRIP (slim, at the field edge; count + a one-line
	 *    worm sparkline + the top scorer) that keeps the coordination co-visible with the
	 *    field and expands into the full panel;
	 *  - the full PANEL (a right-edge side panel on desktop, a bottom sheet on mobile).
	 *
	 * Demand-mode: `computeSelectionStats` runs ONE pass over the masked indices and only
	 * while the panel is open OR the desktop strip is live (`panelActive`). A large recompute
	 * (the 200 Club's 28,704 balls, the whole field's 316,199) shows an `Updating…` state so
	 * the momentary lag reads as catching up, never as the two surfaces disagreeing.
	 */
	interface Props {
		col: Columnar | null;
		matches: MatchInfo[];
		/** the SAME mask the field got (mask/flag path) or a panel-built mask (scalar path) */
		mask: Uint8Array | null;
		/** the live data-bound count (from the tray readout) */
		count: number | null;
		/** the plain selection sentence (batting-side team etc.) */
		selectionLabel: string;
		/** true when the full panel is open (side panel / bottom sheet) */
		open: boolean;
		/** prefers-reduced-motion: no coordinated transition, static swap */
		reduced: boolean;
		onClose: () => void;
		onExpand: () => void;
	}
	let { col, matches, mask, count, selectionLabel, open, reduced, onClose, onExpand }: Props =
		$props();

	/* the desktop coupling strip is always live; on mobile stats compute only when open */
	let isWide = $state(false);
	onMount(() => {
		const mq = window.matchMedia('(min-width: 900px)');
		isWide = mq.matches;
		const on = (): void => {
			isWide = mq.matches;
		};
		mq.addEventListener('change', on);
		return () => mq.removeEventListener('change', on);
	});

	const panelActive = $derived(open || isWide);
	/** a recompute above this many balls defers a frame + shows the Updating… state */
	const BIG_RECOMPUTE = 20000;

	let stats = $state<SelectionStats | null>(null);
	let updating = $state(false);
	/** bumped on every commit so a coordinated transition replays with the field's cue */
	let coordTick = $state(0);

	// recompute whenever the committed mask changes (and the panel/strip is watching).
	// A big selection defers one frame so the Updating… state paints before the pass.
	$effect(() => {
		const m = mask;
		const c = col;
		void panelActive;
		if (!panelActive || !c || !m) {
			stats = null;
			updating = false;
			return;
		}
		const heavy = (count ?? 0) > BIG_RECOMPUTE;
		if (heavy) {
			updating = true;
			let cancelled = false;
			const id = requestAnimationFrame(() => {
				if (cancelled) return;
				stats = computeSelectionStats(c, matches, m);
				updating = false;
				coordTick = untrack(() => coordTick) + 1;
			});
			return () => {
				cancelled = true;
				cancelAnimationFrame(id);
			};
		}
		stats = computeSelectionStats(c, matches, m);
		updating = false;
		coordTick = untrack(() => coordTick) + 1;
	});

	const empty = $derived((count ?? 0) === 0);
	const fmt = (n: number): string => n.toLocaleString('en-US');

	/* ---- worm geometry (self-contained local viewBox; the Ch2 markup, no GL) ---- */
	const WORM_W = 340;
	const WORM_H = 128;
	const wormGeo = $derived.by(() => {
		const w = stats?.worm ?? [];
		if (w.length < 2) return null;
		const padL = 8;
		const padR = 46;
		const padT = 12;
		const padB = 22;
		let xmax = 1;
		let ymax = 1;
		for (const p of w) {
			if (p.x > xmax) xmax = p.x;
			if (p.y > ymax) ymax = p.y;
		}
		const px = (x: number): number => padL + (x / xmax) * (WORM_W - padL - padR);
		const py = (y: number): number => WORM_H - padB - (y / ymax) * (WORM_H - padT - padB);
		const points = w.map((p) => `${px(p.x).toFixed(1)},${py(p.y).toFixed(1)}`).join(' ');
		const last = w[w.length - 1];
		return {
			points,
			baseY: py(0),
			endX: px(last.x),
			endY: py(last.y),
			total: last.y,
			balls: last.x
		};
	});

	/* ---- Manhattan geometry (inline SVG bars; the Ch3 single-bar model) ---- */
	const MAN_H = 120;
	const manGeo = $derived.by(() => {
		const bars = stats?.manhattan ?? [];
		if (bars.length === 0) return null;
		const barW = 12;
		const gap = 4;
		const padT = 10;
		const padB = 20;
		const width = bars.length * (barW + gap) + gap;
		let rmax = 1;
		for (const b of bars) if (b.runs > rmax) rmax = b.runs;
		const h = (v: number): number => (v / rmax) * (MAN_H - padT - padB);
		const rects = bars.map((b, i) => {
			const x = gap + i * (barW + gap);
			const bh = h(b.runs);
			const capH = b.wickets > 0 ? Math.min(bh, 3 + (b.wickets - 1) * 2.5) : 0;
			return {
				over: b.over,
				x,
				w: barW,
				runsY: MAN_H - padB - bh,
				runsH: bh,
				capY: MAN_H - padB - bh,
				capH,
				runs: b.runs,
				wickets: b.wickets,
				label: b.over + 1
			};
		});
		return { rects, width, baseY: MAN_H - padB, rmax };
	});

	const battersMax = $derived(stats?.leaderboard.batters[0]?.runs ?? 1);
	const bowlersMax = $derived(stats?.leaderboard.bowlers[0]?.wickets ?? 1);

	function onKeydown(e: KeyboardEvent): void {
		if (e.key === 'Escape') onClose();
	}
</script>

<!-- the always-on desktop coupling strip: keeps count + a one-line thread co-visible
     with the field, and expands into the full panel. Hidden on mobile (temporal coupling). -->
<div class="strip" class:hidden={open} class:reduced aria-hidden={open}>
	<button
		class="strip-btn"
		type="button"
		onclick={onExpand}
		aria-label="Show the breakdown of this selection"
	>
		<span class="strip-count">
			<span class="sc-n">{count != null ? fmt(count) : '-'}</span>
			<span class="sc-u">balls</span>
		</span>
		{#if empty}
			<span class="strip-thread">Nothing to break down yet</span>
		{:else if updating}
			<span class="strip-thread">Updating...</span>
		{:else if stats}
			{#if wormGeo}
				<svg class="spark" viewBox="0 0 100 26" preserveAspectRatio="none" aria-hidden="true">
					<polyline
						points={stats.worm
							.map((p, i) => {
								const xm = wormGeo.balls || 1;
								const ym = wormGeo.total || 1;
								void i;
								return `${((p.x / xm) * 100).toFixed(1)},${(24 - (p.y / ym) * 22).toFixed(1)}`;
							})
							.join(' ')}
					/>
				</svg>
			{/if}
			<span class="strip-thread">
				{#if stats.leaderboard.batters[0]}
					{stats.leaderboard.batters[0].name} · {fmt(stats.leaderboard.batters[0].runs)} runs
				{:else}
					{fmt(stats.totalRuns)} runs
				{/if}
			</span>
		{/if}
		<span class="strip-open">Show the breakdown</span>
	</button>
</div>

{#if open}
	<!-- the full panel: right-edge side panel (desktop) / bottom sheet (mobile) -->
	<div
		class="panel"
		class:reduced
		role="dialog"
		aria-label="Breakdown of this selection"
		tabindex="-1"
		onkeydown={onKeydown}
	>
		<div class="panel-head">
			<div class="ph-text">
				<p class="ph-title">The breakdown</p>
				<p class="ph-sel">{selectionLabel}</p>
			</div>
			<div class="ph-count">
				<span class="phc-n">{count != null ? fmt(count) : '-'}</span>
				<span class="phc-u">balls</span>
			</div>
			<button class="panel-close" type="button" onclick={onClose} aria-label="Close the breakdown"
				>×</button
			>
		</div>

		{#if updating}
			<p class="updating" role="status">Updating...</p>
		{/if}

		{#if empty}
			<p class="panel-empty">Nothing to break down yet. Loosen a filter.</p>
		{:else if stats}
			{#key coordTick}
				<div class="views" class:settling={!reduced}>
					<!-- the worm -->
					<section class="view" aria-label="How the runs piled up">
						<p class="v-title">How the runs piled up</p>
						<p class="v-orient">
							{#if stats.singleBatter}
								Runs adding up, ball by ball, through this one batter's innings.
							{:else}
								Runs adding up, ball by ball, across everything you've picked.
							{/if}
						</p>
						{#if wormGeo}
							<svg
								class="worm"
								viewBox="0 0 {WORM_W} {WORM_H}"
								role="img"
								aria-label={`Cumulative runs reaching ${fmt(wormGeo.total)} across ${fmt(
									wormGeo.balls
								)} balls`}
							>
								<line
									class="axis"
									x1="8"
									y1={wormGeo.baseY}
									x2={WORM_W - 46}
									y2={wormGeo.baseY}
								/>
								<polyline class="worm-line" points={wormGeo.points} />
								<circle class="worm-end" cx={wormGeo.endX} cy={wormGeo.endY} r="3" />
								<text class="worm-total" x={wormGeo.endX + 6} y={wormGeo.endY + 4}
									>{fmt(wormGeo.total)}</text
								>
							</svg>
							<p class="v-foot">{fmt(wormGeo.total)} runs off {fmt(wormGeo.balls)} balls</p>
						{:else}
							<p class="v-foot">Not enough balls to draw the run climb.</p>
						{/if}
					</section>

					<!-- the Manhattan -->
					<section class="view" aria-label="Runs in each over">
						<p class="v-title">Runs in each over</p>
						<p class="v-orient">The red caps are wickets.</p>
						{#if manGeo}
							<div class="man-scroll">
								<svg
									class="man"
									viewBox="0 0 {manGeo.width} {MAN_H}"
									role="img"
									aria-label={`Runs per over across ${fmt(stats.count)} balls, ${fmt(
										stats.totalWickets
									)} wickets`}
									style="width:{Math.max(manGeo.width, 260)}px"
								>
									<line
										class="axis"
										x1="0"
										y1={manGeo.baseY}
										x2={manGeo.width}
										y2={manGeo.baseY}
									/>
									{#each manGeo.rects as r (r.over)}
										<rect
											class="man-bar"
											x={r.x}
											y={r.runsY}
											width={r.w}
											height={r.runsH}
										/>
										{#if r.capH > 0}
											<rect
												class="man-cap"
												x={r.x}
												y={r.capY}
												width={r.w}
												height={r.capH}
											/>
										{/if}
										{#if r.label % 5 === 0 || r.label === 1}
											<text class="man-lab" x={r.x + r.w / 2} y={MAN_H - 6}>{r.label}</text>
										{/if}
									{/each}
								</svg>
							</div>
							<p class="v-foot">Overs 1 to {manGeo.rects.length} · {fmt(stats.totalWickets)} wickets</p>
						{/if}
					</section>

					<!-- the leaderboard -->
					<section class="view" aria-label="Who did the damage">
						<p class="v-title">Who did the damage</p>
						<div class="boards">
							<div class="board">
								<p class="board-title">Top run-scorers</p>
								{#if stats.leaderboard.batters.length > 0}
									<ol class="ranks">
										{#each stats.leaderboard.batters as b (b.name)}
											<li class="rank">
												<span class="rk-name">{b.name}</span>
												<span class="rk-bar" aria-hidden="true">
													<span
														class="rk-fill runs"
														style="width:{Math.max(4, (b.runs / battersMax) * 100)}%"
													></span>
												</span>
												<span class="rk-val">{fmt(b.runs)}</span>
											</li>
										{/each}
									</ol>
								{:else}
									<p class="board-empty">No runs off the bat in this selection.</p>
								{/if}
							</div>
							<div class="board">
								<p class="board-title">Top wicket-takers</p>
								{#if stats.leaderboard.bowlers.length > 0}
									<ol class="ranks">
										{#each stats.leaderboard.bowlers as b (b.name)}
											<li class="rank">
												<span class="rk-name">{b.name}</span>
												<span class="rk-bar" aria-hidden="true">
													<span
														class="rk-fill wkts"
														style="width:{Math.max(4, (b.wickets / bowlersMax) * 100)}%"
													></span>
												</span>
												<span class="rk-val">{fmt(b.wickets)}</span>
											</li>
										{/each}
									</ol>
								{:else}
									<p class="board-empty">No wickets in this selection.</p>
								{/if}
							</div>
						</div>
					</section>
				</div>
			{/key}
		{/if}
	</div>
{/if}

<style>
	/* ---- the desktop coupling strip ---- */
	.strip {
		position: fixed;
		right: max(12px, env(safe-area-inset-right));
		bottom: 50%;
		transform: translateY(50%);
		z-index: 4;
		pointer-events: auto;
	}

	.strip.hidden {
		display: none;
	}

	.strip-btn {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 4px;
		width: 168px;
		padding: 0.6rem 0.7rem;
		border-radius: 12px;
		border: 1px solid rgba(46, 196, 182, 0.35);
		background: rgba(11, 14, 20, 0.86);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		color: var(--ink);
		font: inherit;
		text-align: left;
		cursor: pointer;
	}

	.strip-btn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.strip-count {
		display: flex;
		align-items: baseline;
		gap: 5px;
	}

	.sc-n {
		font-size: 1.2rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.sc-u {
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.spark {
		width: 100%;
		height: 20px;
	}

	.spark polyline {
		fill: none;
		stroke: var(--teal);
		stroke-width: 1.6;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.strip-thread {
		font-size: 0.74rem;
		color: var(--ink-dim);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		max-width: 100%;
	}

	.strip-open {
		margin-top: 2px;
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--teal);
	}

	/* hide the strip entirely on phones (temporal, not spatial, coupling) */
	@media (max-width: 899px) {
		.strip {
			display: none;
		}
	}

	/* ---- the full panel ---- */
	.panel {
		position: fixed;
		z-index: 7;
		pointer-events: auto;
		background: rgba(11, 14, 20, 0.94);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border: 1px solid rgba(232, 236, 245, 0.14);
		color: var(--ink);
		font-variant-numeric: tabular-nums;
		overflow-y: auto;
		overscroll-behavior: contain;
	}

	/* desktop: a right-edge side panel that never covers the tray or the intro */
	@media (min-width: 900px) {
		.panel {
			top: 12px;
			right: 12px;
			bottom: 12px;
			width: min(380px, 34vw);
			border-radius: 16px;
			padding: 0.9rem 1rem 1.2rem;
		}
	}

	/* mobile: a bottom sheet, above the tray sheet */
	@media (max-width: 899px) {
		.panel {
			left: 0;
			right: 0;
			bottom: 0;
			max-height: 82dvh;
			border-radius: 18px 18px 0 0;
			padding: 0.9rem 1rem calc(1.2rem + env(safe-area-inset-bottom));
		}
	}

	.panel-head {
		display: flex;
		align-items: flex-start;
		gap: 10px;
		padding-bottom: 0.7rem;
		border-bottom: 1px solid rgba(232, 236, 245, 0.1);
	}

	.ph-text {
		flex: 1 1 auto;
		min-width: 0;
	}

	.ph-title {
		margin: 0;
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: var(--gold);
	}

	.ph-sel {
		margin: 0.2rem 0 0;
		font-size: 0.86rem;
		color: var(--ink-dim);
		line-height: 1.35;
	}

	.ph-count {
		flex: none;
		display: flex;
		align-items: baseline;
		gap: 5px;
	}

	.phc-n {
		font-size: 1.15rem;
		font-weight: 700;
	}

	.phc-u {
		font-size: 0.72rem;
		color: var(--ink-dim);
	}

	.panel-close {
		flex: none;
		width: 40px;
		height: 40px;
		margin: -6px -6px 0 0;
		border: none;
		border-radius: 10px;
		background: transparent;
		color: var(--ink-dim);
		font-size: 1.4rem;
		line-height: 1;
		cursor: pointer;
	}

	.panel-close:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: -3px;
	}

	.updating {
		margin: 0.6rem 0 0;
		font-size: 0.76rem;
		color: var(--teal);
	}

	.panel-empty {
		margin: 1.2rem 0;
		font-size: 0.9rem;
		color: var(--ink-dim);
	}

	.views {
		display: flex;
		flex-direction: column;
		gap: 1.1rem;
		margin-top: 0.8rem;
	}

	/* a brief coordinated settle alongside the field's change cue (one cause, one effect) */
	.views.settling {
		animation: settle 220ms ease;
	}

	@keyframes settle {
		from {
			opacity: 0.35;
		}
		to {
			opacity: 1;
		}
	}

	.view {
		display: flex;
		flex-direction: column;
	}

	.v-title {
		margin: 0;
		font-size: 0.92rem;
		font-weight: 700;
		color: var(--ink);
	}

	.v-orient {
		margin: 0.15rem 0 0.5rem;
		font-size: 0.78rem;
		color: var(--ink-dim);
		line-height: 1.35;
	}

	.v-foot {
		margin: 0.35rem 0 0;
		font-size: 0.74rem;
		color: var(--ink-dim);
	}

	.worm {
		width: 100%;
		height: auto;
		overflow: visible;
	}

	.axis {
		stroke: rgba(232, 236, 245, 0.24);
		stroke-width: 1;
	}

	.worm-line {
		fill: none;
		stroke: var(--teal);
		stroke-width: 2;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	.worm-end {
		fill: var(--teal);
	}

	.worm-total {
		fill: var(--ink);
		font-size: 11px;
		font-weight: 700;
	}

	.man-scroll {
		overflow-x: auto;
		overscroll-behavior-x: contain;
	}

	.man {
		height: 120px;
		display: block;
	}

	.man-bar {
		fill: rgba(46, 196, 182, 0.7);
	}

	.man-cap {
		fill: var(--ember);
	}

	.man-lab {
		fill: var(--ink-dim);
		font-size: 9px;
		text-anchor: middle;
	}

	.boards {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.9rem;
	}

	@media (max-width: 480px) {
		.boards {
			grid-template-columns: 1fr;
		}
	}

	.board-title {
		margin: 0 0 0.35rem;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		color: var(--ink-dim);
	}

	.board-empty {
		margin: 0;
		font-size: 0.78rem;
		color: var(--ink-dim);
	}

	.ranks {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 5px;
	}

	.rank {
		display: grid;
		grid-template-columns: 1fr 46px auto;
		align-items: center;
		gap: 6px;
	}

	.rk-name {
		font-size: 0.78rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.rk-bar {
		height: 6px;
		border-radius: 3px;
		background: rgba(232, 236, 245, 0.1);
		overflow: hidden;
	}

	.rk-fill {
		display: block;
		height: 100%;
		border-radius: 3px;
	}

	.rk-fill.runs {
		background: var(--teal);
	}

	.rk-fill.wkts {
		background: var(--ember);
	}

	.rk-val {
		font-size: 0.78rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	@media (prefers-reduced-motion: reduce) {
		.views.settling {
			animation: none;
		}
	}

	.panel.reduced .views.settling {
		animation: none;
	}
</style>
