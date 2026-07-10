<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { flip } from 'svelte/animate';
	import type { Columnar, MatchInfo } from '../data';
	import {
		computeSelectionStats,
		type SelectionStats,
		type BatterRow,
		type BowlerRow
	} from './select-stats';
	import {
		loadCredibility,
		trustState,
		regressSR,
		type Credibility,
		type TrustState,
		type RegressResult
	} from './credibility';

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
		return () => {
			mq.removeEventListener('change', on);
			if (rankTimer) clearTimeout(rankTimer);
		};
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

	/* ================= R7b credibility: trust meter + shrinkage slider =================
	 * The trust meter (storyboard 9.1) is an EXCEPTION-ONLY cue: a reliable row carries
	 * no mark, only firming and noisy rows get a dot, driven by n (balls) vs the stat M.
	 * The shrinkage slider (storyboard 9.3) is BATTING-ONLY, a 3-detent control that
	 * re-ranks the batter pool by the best-guess strike rate with an 80% CI whisker. Both
	 * are suppressed until the tiny league-wide artifacts load; a load failure leaves the
	 * plain R6b leaderboards untouched. */
	let credibility = $state<Credibility | null>(null);
	let credLoadStarted = false;
	// load lazily once the panel or the desktop strip is watching (never blocks R6b)
	$effect(() => {
		if (!panelActive || credLoadStarted) return;
		credLoadStarted = true;
		loadCredibility()
			.then((c) => (credibility = c))
			.catch(() => (credibility = null));
	});

	/** how many leaderboard rows are shown (the pool is wider; see select-stats) */
	const LEADER_SHOWN = 8;

	/** the 3 detents; lambda 0 (as it happened) / ~0.5 (halfway) / 1 (best guess) */
	const DETENTS = [
		{ label: 'As it happened', gloss: 'Small samples included: a short, hot spell can top it.' },
		{ label: 'Halfway', gloss: 'Part way to the best guess, weighing how little we have seen.' },
		{ label: 'Best guess', gloss: 'Our best guess at true skill, weighing how little we have seen.' }
	];
	let detent = $state(0);
	const lambda = $derived(detent === 1 ? 0.5 : detent === 2 ? 1 : 0);
	/** true only when a shrinkage detent is active AND the artifacts have loaded */
	const regressedMode = $derived(detent !== 0 && credibility != null);

	// re-rank motion gating: enter/exit + flip animate ONLY on a detent change, never on
	// a mask commit (so a new selection does not flash the whole board).
	let rankShift = $state(false);
	let rankTimer: ReturnType<typeof setTimeout> | null = null;
	let prevDetent = 0;
	let announce = $state('');

	function setDetent(d: number): void {
		if (d === detent) return;
		detent = d;
		if (!reduced) {
			rankShift = true;
			if (rankTimer) clearTimeout(rankTimer);
			rankTimer = setTimeout(() => (rankShift = false), 400);
		}
	}

	interface RankedBatter extends BatterRow {
		reg: RegressResult | null;
		trust: TrustState;
	}
	interface RankedBowler extends BowlerRow {
		trust: TrustState;
	}

	const battingPool = $derived<BatterRow[]>(stats?.leaderboard.batters ?? []);

	/** the shown eight batters by the ACTIVE ordering (raw runs at detent 0, else skill) */
	const battingRows = $derived.by<RankedBatter[]>(() => {
		const cred = credibility;
		const pool = battingPool;
		const bt = (n: number): TrustState => (cred ? trustState(n, cred.batting.M) : 'reliable');
		// detent 0 is R6b exactly: the raw runs board, every batter, no floor.
		if (!cred || detent === 0) {
			return pool.slice(0, LEADER_SHOWN).map((b) => ({ ...b, reg: null, trust: bt(b.balls) }));
		}
		// A best-guess ranking needs a real sample: below about a quarter of M the batter's
		// own numbers carry under a fifth of the estimate, so the row is essentially the
		// league average and would rank a tail-ender's non-sample above a proven batter.
		// Qualify the pool by that floor (fall back to the whole pool for a tiny selection).
		const floor = Math.ceil(cred.batting.M / 4);
		const qualified = pool.filter((b) => b.balls >= floor);
		const source = qualified.length > 0 ? qualified : pool;
		const mu = (b: BatterRow): number =>
			b.league === 1 ? cred.batting.popMeanSR.wpl : cred.batting.popMeanSR.ipl;
		const ranked = source.map((b) => {
			const rawSR = b.balls > 0 ? (100 * b.runs) / b.balls : 0;
			const reg = regressSR(rawSR, b.balls, mu(b), cred.batting.M, cred.batting.sigma2, cred.batting.z, lambda);
			return { ...b, reg, trust: bt(b.balls) };
		});
		ranked.sort((p, q) => q.reg.point - p.reg.point || q.runs - p.runs || p.name.localeCompare(q.name));
		return ranked.slice(0, LEADER_SHOWN);
	});

	/** shared x-domain for the CI whiskers, so the eight rows compare on one scale */
	const whiskerDomain = $derived.by(() => {
		if (!regressedMode) return null;
		let lo = Infinity;
		let hi = -Infinity;
		for (const b of battingRows) {
			if (!b.reg) continue;
			if (b.reg.lo < lo) lo = b.reg.lo;
			if (b.reg.hi > hi) hi = b.reg.hi;
		}
		if (!Number.isFinite(lo) || !Number.isFinite(hi) || hi <= lo) return null;
		const pad = (hi - lo) * 0.06;
		return { lo: lo - pad, hi: hi + pad };
	});

	function whiskerGeo(reg: RegressResult, dom: { lo: number; hi: number }) {
		const span = Math.max(1e-6, dom.hi - dom.lo);
		const clamp = (v: number): number => Math.max(0, Math.min(100, ((v - dom.lo) / span) * 100));
		return { lo: clamp(reg.lo), hi: clamp(reg.hi), pt: clamp(reg.point) };
	}

	const bowlingRows = $derived.by<RankedBowler[]>(() => {
		const cred = credibility;
		const rows = stats?.leaderboard.bowlers ?? [];
		const bt = (n: number): TrustState => (cred ? trustState(n, cred.bowling.M) : 'reliable');
		return rows.slice(0, LEADER_SHOWN).map((b) => ({ ...b, trust: bt(b.balls) }));
	});

	// legends are exception-only: shown only when a shown row is actually still settling
	const battingHasUnsettled = $derived(
		credibility != null && !regressedMode && battingRows.some((b) => b.trust !== 'reliable')
	);
	const bowlingHasUnsettled = $derived(
		credibility != null && bowlingRows.some((b) => b.trust !== 'reliable')
	);

	const rankLabel = $derived(
		regressedMode ? 'Ranked by: best guess at true skill' : 'Ranked by: what actually happened'
	);

	// live-region announcement, fired ONLY when the detent changes (reads the rows untracked
	// so a new selection or a slow recompute never re-announces the ranking).
	$effect(() => {
		const d = detent;
		if (d === prevDetent) return;
		const lead = untrack(() => battingRows[0]?.name ?? 'unavailable');
		prevDetent = d;
		announce =
			d === 0
				? 'Ranked by what actually happened.'
				: `Reordered by best guess at true skill. New leader: ${lead}.`;
	});

	function battingRawTip(b: RankedBatter): string {
		const M = credibility ? Math.round(credibility.batting.M) : 0;
		if (!credibility || b.trust === 'reliable') return `${b.name}: ${b.runs} runs off ${b.balls} balls.`;
		return `${b.balls} balls faced. A strike rate needs about ${M} to settle.`;
	}
	function battingRegTip(b: RankedBatter): string {
		if (!b.reg) return b.name;
		return `${b.name}. Best guess ${Math.round(b.reg.point)}. 80% sure it is between ${Math.round(
			b.reg.lo
		)} and ${Math.round(b.reg.hi)}.`;
	}
	function bowlingTip(b: RankedBowler): string {
		const M = credibility && credibility.bowling.M != null ? Math.round(credibility.bowling.M) : 0;
		if (!credibility || b.trust === 'reliable' || !M) return `${b.name}: ${b.wickets} wickets off ${b.balls} balls.`;
		return `${b.balls} balls bowled. An economy rate needs about ${M} to settle.`;
	}

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

				</div>
			{/key}

			<!-- the leaderboard lives OUTSIDE the {#key coordTick} block so the shrinkage
			     control and its active detent survive a mask commit (the keyed views above
			     remount and settle; this section persists and re-ranks reactively on the
			     detent, without re-firing the demand-mode pass). -->
			<section class="view lead" aria-label="Who did the damage">
				<p class="v-title">Who did the damage</p>

				{#if credibility && battingPool.length > 0}
					<!-- the shrinkage control: batting-only, 3 snapping detents (9.3) -->
					<div class="shrink">
						<p class="shrink-state">{rankLabel}</p>
						<div class="detents" role="radiogroup" aria-label="Rank the batters by">
							{#each DETENTS as d, i (i)}
								<button
									class="detent"
									class:on={detent === i}
									role="radio"
									aria-checked={detent === i}
									type="button"
									onclick={() => setDetent(i)}>{d.label}</button
								>
							{/each}
						</div>
						<p class="shrink-gloss">{DETENTS[detent].gloss}</p>
					</div>
				{/if}
				<p class="sr-only" aria-live="polite">{announce}</p>

				<div class="boards" class:stack={regressedMode}>
					<div class="board">
						<p class="board-title">Top run-scorers</p>
						{#if battingHasUnsettled}
							<p class="trust-legend">A hollow dot means still settling. Too few balls to trust yet.</p>
						{/if}
						{#if battingRows.length > 0}
							<ol class="ranks">
								{#each battingRows as b (b.name)}
									<li
										class="rank"
										class:regressed={regressedMode}
										class:promoted={rankShift && !reduced}
										animate:flip={{ duration: rankShift && !reduced ? 260 : 0 }}
									>
										{#if regressedMode && b.reg && whiskerDomain}
											{@const g = whiskerGeo(b.reg, whiskerDomain)}
											<span class="rk-name">{b.name}</span>
											<span class="rk-bar whisker" title={battingRegTip(b)} aria-label={battingRegTip(b)}>
												<span class="wk-track">
													<span class="wk-range" style="left:{g.lo}%; right:{100 - g.hi}%"></span>
													<span class="wk-dot" style="left:{g.pt}%"></span>
												</span>
											</span>
										{:else}
											<span class="rk-name">{b.name}</span>
											<span class="rk-bar" aria-hidden="true">
												<span class="rk-fill runs" style="width:{Math.max(4, (b.runs / battersMax) * 100)}%"></span>
											</span>
											<span class="rk-val" title={battingRawTip(b)}>
												{#if b.trust === 'firming'}<span class="trust-dot filled" aria-hidden="true"></span
													>{:else if b.trust === 'noisy'}<span class="trust-dot hollow" aria-hidden="true"></span>{/if}
												<span class="v-num" data-trust={b.trust}>{fmt(b.runs)}</span>
											</span>
										{/if}
									</li>
								{/each}
							</ol>
						{:else}
							<p class="board-empty">No runs off the bat in this selection.</p>
						{/if}
					</div>
					<div class="board">
						<p class="board-title">Top wicket-takers</p>
						{#if bowlingHasUnsettled}
							<p class="trust-legend">A hollow dot means still settling. Too few balls to trust yet.</p>
						{/if}
						{#if bowlingRows.length > 0}
							<ol class="ranks">
								{#each bowlingRows as b (b.name)}
									<li class="rank">
										<span class="rk-name">{b.name}</span>
										<span class="rk-bar" aria-hidden="true">
											<span class="rk-fill wkts" style="width:{Math.max(4, (b.wickets / bowlersMax) * 100)}%"></span>
										</span>
										<span class="rk-val" title={bowlingTip(b)}>
											{#if b.trust === 'firming'}<span class="trust-dot filled" aria-hidden="true"></span
												>{:else if b.trust === 'noisy'}<span class="trust-dot hollow" aria-hidden="true"></span>{/if}
											<span class="v-num" data-trust={b.trust}>{fmt(b.wickets)}</span>
										</span>
									</li>
								{/each}
							</ol>
						{:else}
							<p class="board-empty">No wickets in this selection.</p>
						{/if}
					</div>
				</div>
			</section>
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

	/* in a shrinkage state the batting board goes full width so the CI whisker is legible */
	.boards.stack {
		grid-template-columns: 1fr;
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
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-size: 0.78rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	/* ================= R7b credibility: trust meter + shrinkage slider ================= */

	/* the leaderboard now sits outside the keyed views; restore the inter-view spacing */
	.lead {
		margin-top: 1.1rem;
	}

	/* the shrinkage control (batting-only) */
	.shrink {
		margin: 0.35rem 0 0.6rem;
	}
	.shrink-state {
		margin: 0 0 0.35rem;
		font-size: 0.76rem;
		font-weight: 700;
		color: var(--ink);
	}
	.detents {
		display: inline-flex;
		border: 1px solid rgba(232, 236, 245, 0.16);
		border-radius: 9px;
		overflow: hidden;
	}
	.detent {
		min-height: 34px;
		padding: 0 0.6rem;
		border: none;
		border-right: 1px solid rgba(232, 236, 245, 0.12);
		background: transparent;
		color: var(--ink-dim);
		font: inherit;
		font-size: 0.74rem;
		cursor: pointer;
	}
	.detent:last-child {
		border-right: none;
	}
	.detent.on {
		background: rgba(46, 196, 182, 0.18);
		color: var(--ink);
		font-weight: 700;
	}
	.detent:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: -2px;
	}
	.shrink-gloss {
		margin: 0.3rem 0 0;
		font-size: 0.72rem;
		color: var(--ink-dim);
		line-height: 1.35;
	}

	/* the one-line, exception-only board legend */
	.trust-legend {
		margin: 0 0 0.35rem;
		font-size: 0.68rem;
		color: var(--ink-dim);
		line-height: 1.3;
	}

	/* the 8px trust glyph: filled = firming, hollow = noisy, none = settled */
	.trust-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		box-sizing: border-box;
		flex: none;
	}
	.trust-dot.filled {
		background: rgba(232, 236, 245, 0.72);
	}
	.trust-dot.hollow {
		background: transparent;
		border: 1px solid rgba(232, 236, 245, 0.6);
	}
	/* the value luminance mirrors the sample size, floored so it never reads as wrong */
	.v-num[data-trust='firming'] {
		opacity: 0.72;
	}
	.v-num[data-trust='noisy'] {
		opacity: 0.6;
	}

	/* a brief luminance pulse on a re-rank (pure CSS, no DOM lifecycle, so no ghost rows);
	   the animate:flip slide carries object constancy, this just says "it reordered" */
	.rank.promoted {
		animation: rankflash 360ms ease;
	}
	@keyframes rankflash {
		0% {
			filter: brightness(1.5);
		}
		100% {
			filter: brightness(1);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.rank.promoted {
			animation: none;
		}
	}

	/* in a shrinkage state the magnitude bar becomes a floating 80% CI whisker */
	.rank.regressed {
		grid-template-columns: minmax(60px, 1fr) minmax(120px, 1.9fr);
	}
	.rk-bar.whisker {
		height: 16px;
		background: none;
		border-radius: 0;
		overflow: visible;
	}
	.wk-track {
		display: block;
		position: relative;
		width: 100%;
		height: 16px;
	}
	.wk-range {
		position: absolute;
		top: 50%;
		height: 2px;
		transform: translateY(-50%);
		background: rgba(232, 236, 245, 0.4);
		border-radius: 1px;
	}
	.wk-range::before,
	.wk-range::after {
		content: '';
		position: absolute;
		top: -3px;
		width: 1px;
		height: 8px;
		background: rgba(232, 236, 245, 0.5);
	}
	.wk-range::before {
		left: 0;
	}
	.wk-range::after {
		right: 0;
	}
	.wk-dot {
		position: absolute;
		top: 50%;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--ink);
		transform: translate(-50%, -50%);
		box-shadow: 0 0 4px rgba(232, 236, 245, 0.5);
	}

	/* visually hidden, spoken by a screen reader (the visible state header is enough) */
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
		border: 0;
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
