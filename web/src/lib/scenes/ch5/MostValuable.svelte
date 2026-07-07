<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen, pickedTeam } from '$lib/state';
	import { requestTeamChange } from '$lib/scenes/picker';
	import { worthCell } from '$lib/field/layout';
	import {
		loadCh5Data,
		mvbVariantFor,
		setMvbIgnite,
		win100,
		swing100,
		type Ch5Data,
		type PayoffBall,
		type PayoffMoment
	} from './data';

	/**
	 * C5-11 — Team payoff: "your team's most valuable ball ever". The single
	 * biggest win-chance swing in franchise history, from scenes/ch5.json payoff
	 * variants (20 franchise cards, snapshot-tested in the pipeline; card ==
	 * artifact). Tappable to replay its whole over as a stepper-driven mini rail
	 * with the worm segment beneath (the C5-3 grammar, DOM, no GSAP — the scrub
	 * budget stays spent). Runner-ups one click deeper. WPL pickers get the
	 * designed short-history card (a young list said as promise, never deficit);
	 * neutral pickers get the league's biggest ball with the ONE-BALL-PER-SEASON
	 * gallery (wpa.season_gallery — storyboard payoff QA). The mini worm's axis
	 * names ITS referent per card ("{Team}'s wins in 100") because the reader's
	 * team may be defending, unlike the canonical worm.
	 *
	 * THE IGNITE (storyboard C5-11 "the one ball itself ignites"): this
	 * component resolves the card's ball, projects its worth-grid cell to a
	 * viewport-fraction slot, and feeds the data.ts cache; the SceneDef's
	 * dynamicState rides the §20 overrail with dimRest 1 so the single real
	 * point enlarges in place. Reduced motion: no ignite (static card carries
	 * the beat); the cache is cleared.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	const shown = $derived(progress >= 0.32);

	let ch5 = $state<Ch5Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh5Data().then((d) => {
			if (alive) ch5 = d;
		});
		return () => {
			alive = false;
		};
	});

	const resolved = $derived(
		ch5 ? mvbVariantFor(ch5, $pickedTeam ? { league: $pickedTeam.league, team: $pickedTeam.team } : null) : null
	);
	const v = $derived(resolved?.variant ?? null);
	const neutralTop = $derived(ch5?.wpa.top_swings[0] ?? null);

	/* ---- the single-point ignite (data.ts cache, read by dynamicState) ------ */
	let tick = $state(0);
	onMount(() => {
		const onResize = (): void => {
			requestAnimationFrame(() => {
				tick++;
			});
		};
		window.addEventListener('resize', onResize);
		return () => {
			window.removeEventListener('resize', onResize);
			setMvbIgnite(null);
		};
	});
	const igniteBall = $derived(v ? v.most_valuable : neutralTop);
	$effect(() => {
		void tick;
		void progress; // getWorthLayout() is not reactive — re-resolve as the
		// scene scrubs so the cache seeds once the layout exists (and re-seeds
		// after resizes), exactly when dynamicState needs it
		const f = field;
		const b = igniteBall;
		const wl = f?.getWorthLayout();
		if (!f || !b || !wl || reduced || typeof window === 'undefined') {
			setMvbIgnite(null);
			return;
		}
		const c = worthCell(wl, Math.floor(b.state_cell / 10), b.state_cell % 10);
		const css = f.projectToCss(c.x, c.y);
		setMvbIgnite({
			index: b.point_index,
			slot: [css.x / window.innerWidth, css.y / window.innerHeight]
		});
	});

	let replayOpen = $state(false);
	let replayStep = $state(0);
	let runnersOpen = $state(false);
	let galleryOpen = $state(false);

	function fmtDate(iso: string): string {
		const [y, m, d] = iso.split('-').map(Number);
		const dt = new Date(Date.UTC(y, (m ?? 1) - 1, d ?? 1));
		return dt.toLocaleDateString('en-GB', {
			day: 'numeric',
			month: 'long',
			year: 'numeric',
			timeZone: 'UTC'
		});
	}

	function ballLine(b: PayoffBall): string {
		if (b.wicket) return `${b.wicket.player_out} ${b.wicket.kind}`;
		return `${b.runs_total} run${b.runs_total === 1 ? '' : 's'}`;
	}

	function momentLine(m: PayoffMoment): string {
		return `${fmtDate(m.date)}. ${m.opponent}, ${m.venue}. ${m.what_happened}`;
	}

	/* mini worm geometry for the replay (wp for the READER'S team) */
	const mwX = (i: number): number => 6 + (i * 88) / 6;
	const mwY = (wp: number): number => 4 + (1 - wp) * 32;
	const miniWorm = $derived.by(() => {
		if (!v) return '';
		const balls = v.replay.balls;
		if (balls.length === 0) return '';
		const upto = reduced ? balls.length : Math.min(balls.length, replayStep + 1);
		const pts = [`${mwX(0)},${mwY(balls[0].wp_team_before)}`];
		for (let i = 0; i < upto; i++) pts.push(`${mwX(i + 1)},${mwY(balls[i].wp_team_after)}`);
		return pts.join(' ');
	});

	let returnAnchor = $state<HTMLElement | null>(null);
</script>

<!-- in-flow scroll target for the change-team round trip -->
<div class="return-anchor" bind:this={returnAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	<div class="card-slot" class:shown>
		{#if ch5}
			{#if v}
				<div class="scene-card interactive card">
					<p class="overline">
						{v.team}'s most valuable ball{v.short_history ? ', four seasons in' : ' ever'}
					</p>
					<h2>{v.most_valuable.batter} against {v.most_valuable.bowler}</h2>
					<p class="moment">{momentLine(v.most_valuable)}</p>
					<p class="price">
						One delivery moved {v.team}'s win chance by
						<strong>{win100(v.most_valuable.swing)} in a hundred.</strong>
						No other ball in your history moved it more.
					</p>
					{#if v.short_history && v.honesty}
						<p class="honesty">{v.honesty} Here is the one to beat.</p>
					{/if}

					<div class="actions">
						<button class="act" onclick={() => ((replayOpen = !replayOpen), (replayStep = 0))}>
							{replayOpen ? 'close the replay' : 'replay the over →'}
						</button>
						<button class="act" onclick={() => (runnersOpen = !runnersOpen)}>
							{runnersOpen ? 'close the list' : 'the next four →'}
						</button>
						<button
							class="dagger"
							onclick={() => footnotesOpen.set('ch5-payoff')}
							aria-label="How the biggest swing is found">ⓘ</button
						>
					</div>

					{#if replayOpen}
						<div class="replay">
							{#if reduced}
								<!-- reduced motion: the six-panel strip (the C5-3 fallback grammar) -->
								{#each v.replay.balls as b (b.label)}
									<div class="rb-row">
										<span class="rb-label">{b.label}</span>
										<span class="rb-what">{b.batter}: {ballLine(b)}</span>
										<span class="rb-swing">{swing100(b.swing_team)} in 100</span>
									</div>
								{/each}
							{:else}
								{@const b = v.replay.balls[replayStep]}
								<div class="rb-active">
									<span class="rb-label">{b.label}</span>
									<span class="rb-what">{b.batter} vs {b.bowler}: {ballLine(b)}</span>
									<span class="rb-swing">the swing: {swing100(b.swing_team)} in 100</span>
								</div>
								<div class="stepper">
									<button
										class="act"
										disabled={replayStep === 0}
										onclick={() => (replayStep = Math.max(0, replayStep - 1))}>← previous ball</button
									>
									<span class="step-count">{replayStep + 1} / {v.replay.balls.length}</span>
									<button
										class="act"
										disabled={replayStep >= v.replay.balls.length - 1}
										onclick={() => (replayStep = Math.min(v.replay.balls.length - 1, replayStep + 1))}
										>next ball →</button
									>
								</div>
							{/if}
							<svg class="mini-worm" viewBox="0 0 100 44" preserveAspectRatio="none" aria-hidden="true">
								<line class="mw-rule" x1="4" y1="4" x2="96" y2="4" />
								<line class="mw-rule mid" x1="4" y1="20" x2="96" y2="20" />
								<line class="mw-rule" x1="4" y1="36" x2="96" y2="36" />
								{#if miniWorm}
									<polyline class="mw-line" points={miniWorm} />
								{/if}
							</svg>
							<span class="mw-axis">{v.team}'s wins in 100 · 0 at the floor, 100 at the top</span>
						</div>
					{/if}

					{#if runnersOpen}
						<div class="runners">
							{#each v.runners_up as r (r.match_index + r.label)}
								<div class="ru-row">
									<span class="ru-date">{fmtDate(r.date)}</span>
									<span class="ru-what">{r.what_happened}</span>
									<span class="ru-swing">{win100(r.swing)} in 100</span>
								</div>
							{/each}
						</div>
					{/if}

					<button class="change" onclick={() => requestTeamChange(returnAnchor)}>
						Not your team? Change it
					</button>
				</div>
			{:else if neutralTop}
				<div class="scene-card interactive card">
					<p class="overline">the league's most valuable ball ever</p>
					<h2>{neutralTop.batter} against {neutralTop.bowler}</h2>
					<p class="moment">
						{neutralTop.season} · {neutralTop.stage} · {neutralTop.teams[0]} v {neutralTop.teams[1]}.
						{neutralTop.what_happened}
					</p>
					<p class="price">
						One delivery moved the batting side's win chance by
						<strong>{win100(Math.abs(neutralTop.wpa))} in a hundred.</strong>
						No ball in league history moved a match more.
					</p>
					<div class="actions">
						<button class="act" onclick={() => (galleryOpen = !galleryOpen)}>
							{galleryOpen ? 'close the gallery' : "every season's biggest ball →"}
						</button>
						<button
							class="dagger"
							onclick={() => footnotesOpen.set('ch5-payoff')}
							aria-label="How the biggest swing is found">ⓘ</button
						>
					</div>
					{#if galleryOpen && ch5}
						<!-- one ball per season (wpa.season_gallery — storyboard payoff QA);
						     swings show MAGNITUDE (a bowling side's ball carries a negative
						     batting-side read) -->
						<div class="runners">
							{#each ch5.wpa.season_gallery as s (s.league + s.season)}
								<div class="ru-row">
									<span class="ru-date">{s.league.toUpperCase()} {s.season}</span>
									<span class="ru-what">{s.what_happened}</span>
									<span class="ru-swing">{win100(Math.abs(s.wpa))} in 100</span>
								</div>
							{/each}
						</div>
					{/if}
					<button class="change" onclick={() => requestTeamChange(returnAnchor)}>
						Pick a team to make this yours
					</button>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.return-anchor {
		position: absolute;
		top: 40%;
		left: 0;
		width: 1px;
		height: 1px;
	}

	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	.pin.active {
		visibility: visible;
	}

	.card-slot {
		opacity: 0;
		max-height: 100%;
		overflow-y: auto;
	}

	.card-slot.shown {
		opacity: 1;
	}

	.card {
		max-width: min(32rem, 92vw);
	}

	.card h2 {
		font-size: clamp(1.15rem, 3vw, 1.6rem);
	}

	.moment {
		margin-top: 0.55rem;
		font-size: clamp(0.92rem, 2.1vw, 1.05rem);
		line-height: 1.5;
	}

	.price {
		margin-top: 0.7rem;
		font-size: clamp(0.95rem, 2.2vw, 1.1rem);
		line-height: 1.5;
	}

	.price strong {
		color: #ffd166;
	}

	.honesty {
		margin-top: 0.6rem;
		font-size: 0.85rem;
		color: var(--ink-dim);
		line-height: 1.5;
		font-style: italic;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		margin-top: 0.9rem;
		flex-wrap: wrap;
	}

	.act {
		min-height: 44px;
		padding: 0.4rem 0.85rem;
		border-radius: 999px;
		border: 1px solid rgba(151, 161, 184, 0.45);
		background: none;
		color: var(--ink);
		font-size: 0.82rem;
		font-weight: 600;
		cursor: pointer;
	}

	.act:disabled {
		opacity: 0.4;
		cursor: default;
	}

	.act:focus-visible,
	.change:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.replay {
		margin-top: 0.8rem;
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
		border-top: 1px solid rgba(151, 161, 184, 0.2);
		padding-top: 0.7rem;
	}

	.rb-active,
	.rb-row {
		display: flex;
		align-items: baseline;
		gap: 0.6rem;
		flex-wrap: wrap;
	}

	.rb-label {
		font-size: 0.72rem;
		font-weight: 700;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.rb-what {
		font-size: 0.9rem;
		font-weight: 600;
		flex: 1;
	}

	.rb-swing {
		font-size: 0.8rem;
		font-weight: 700;
		color: #ffd166;
		font-variant-numeric: tabular-nums;
	}

	.stepper {
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}

	.step-count {
		font-size: 0.78rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.mini-worm {
		width: 100%;
		height: 3.4rem;
	}

	.mw-rule {
		stroke: rgba(151, 161, 184, 0.25);
		vector-effect: non-scaling-stroke;
	}

	.mw-rule.mid {
		stroke-dasharray: 3 4;
	}

	.mw-line {
		fill: none;
		stroke: #ffd166;
		stroke-width: 2.2;
		stroke-linejoin: round;
		stroke-linecap: round;
		vector-effect: non-scaling-stroke;
	}

	.mw-axis {
		font-size: 0.66rem;
		color: var(--ink-dim);
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.runners {
		margin-top: 0.8rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		border-top: 1px solid rgba(151, 161, 184, 0.2);
		padding-top: 0.7rem;
		max-height: 30vh;
		overflow-y: auto;
	}

	.ru-row {
		display: flex;
		align-items: baseline;
		gap: 0.6rem;
	}

	.ru-date {
		font-size: 0.72rem;
		color: var(--ink-dim);
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}

	.ru-what {
		font-size: 0.82rem;
		flex: 1;
		line-height: 1.4;
	}

	.ru-swing {
		font-size: 0.78rem;
		font-weight: 700;
		color: #ffd166;
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}

	.change {
		display: block;
		margin-top: 1rem;
		min-height: 44px;
		padding: 0.4rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.85rem;
		font-weight: 600;
		cursor: pointer;
	}
</style>
