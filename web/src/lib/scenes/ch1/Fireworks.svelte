<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { OUTCOME_SIX, ATTR_TOP10_BIT } from '$lib/field/types';
	import { loadCh1Data, fmt1, GHOST_BAND, BOLD_BAND, twoTone, type Ch1Data } from './data';

	/**
	 * C1-5 — The fireworks (storyboard §3, the chapter's signature subset moment).
	 * The choreography lives in the FIELD, not this DOM layer: the ch1-sixes scene
	 * def declares the CONTRACT §7 subset RE-SORT, so every IPL six lifts out of
	 * the ignition wall (two-phase — arcing up as the wall dims hard) and re-sorts
	 * into 19 per-season firework columns where each point is a real six; the
	 * settle-back is free (the next scene declares no re-sort). This component only
	 * (1) anchors the 2008 / 2023 / 2026 DOM labels over their field columns via
	 * field.getResortLayout() + projectToCss, and (2) steps the captions.
	 *
	 * Step 3's one change is a per-point two-tone recolor (attrs.u8 bit 5 = a
	 * top-10 hitter's six) driven by resort.tint. It is gated on the bit actually
	 * being populated (twoTone.available): until the pipeline ships it, raising the
	 * tint would dim every six uniformly, so we hold the field single-tone and drop
	 * the "watch the slice shrink" line — pixels == copy either way.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 70 / 170 */
	const step = $derived.by(() => {
		if (progress < 0.44) return 0;
		if (progress < 0.62) return 1;
		if (progress < 0.8) return 2;
		return 3;
	});

	// mobile "read, then watch" (CONTRACT §17): step k spans [CAP_BOUNDS[k],
	// CAP_BOUNDS[k + 1]). Step 0 is the two-phase six-lift + re-sort morph; step 1
	// starts once the columns have formed, so the first caption holds (not gapped)
	// until then. Returns 1 on desktop / reduced motion (caption unchanged).
	const CAP_BOUNDS = [0, 0.44, 0.62, 0.8, 1] as const;
	const reveal = $derived(
		captionReveal(progress, CAP_BOUNDS[step], CAP_BOUNDS[step + 1], { reduced })
	);

	let ch1 = $state<Ch1Data | null>(null);
	let tick = $state(0); // resize signal for label re-anchoring
	onMount(() => {
		let alive = true;
		loadCh1Data().then((d) => {
			if (alive) ch1 = d;
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

	/* ---- two-tone availability: scan attrs once for the top-10 bit ----------- */
	let twoToneAvailable = $state(false);
	$effect(() => {
		const f = field;
		if (!f || twoToneAvailable) return;
		const attrs = f.data.attrs;
		for (let i = 0; i < attrs.length; i++) {
			if ((attrs[i] & 7) === OUTCOME_SIX && (attrs[i] & ATTR_TOP10_BIT) !== 0) {
				twoToneAvailable = true;
				break;
			}
		}
		twoTone.available = twoToneAvailable;
	});

	/* ---- on-screen numbers (every one from the artifact) --------------------- */
	const seasons = $derived(ch1 ? ch1.sixes.seasons.ipl : null);
	const s2008 = $derived(seasons ? (seasons.find((s) => s.season === 2008) ?? null) : null);
	const s2026 = $derived(seasons ? (seasons.find((s) => s.season === 2026) ?? null) : null);

	/* balls-per-six headline pair — the pipeline's per-season field, rounded (the
	   caption's "every 21 → every 12"; 20.8 → 11.7 live in the dagger). */
	const bpsFirst = $derived(s2008 ? Math.round(s2008.balls_per_six) : null);
	const bpsLast = $derived(s2026 ? Math.round(s2026.balls_per_six) : null);

	const aerialEarly = $derived(ch1 ? ch1.aerial.bands[GHOST_BAND] : null);
	const aerialRecent = $derived(ch1 ? ch1.aerial.bands[BOLD_BAND] : null);

	/* ---- DOM column labels anchored to the FIELD columns --------------------- */
	interface ColLabel {
		season: number;
		x: number;
		y: number;
	}

	// getResortLayout() is IMPERATIVE — it turns non-null a frame or two after the
	// re-sort first applies, and a reader who deep-links / jump-cuts in parks at a
	// static progress where no tracked dep changes to re-run a $derived. So drive
	// it from an $effect that re-anchors on progress/resize AND rAF-retries while
	// the geometry is still building (self-terminates once it resolves).
	let colLabels = $state<ColLabel[]>([]);
	let retry = $state(0);
	$effect(() => {
		void progress; // re-anchor as the reader scrubs
		void tick; // and on resize
		void retry; // and on the rAF retry while geometry builds
		const f = field;
		if (!f || !seasons || !active) {
			colLabels = [];
			return;
		}
		const rl = f.getResortLayout();
		if (!rl) {
			if (retry < 240) {
				const id = requestAnimationFrame(() => retry++);
				return () => cancelAnimationFrame(id);
			}
			return;
		}
		const groups = f.data.groups;
		const giOf = (season: number): number | null => {
			const g = groups.find((gr) => gr.league === 'ipl' && gr.season === season);
			return g ? g.gi : null;
		};
		const out: ColLabel[] = [];
		for (const season of [2008, 2023, 2026]) {
			const gi = giOf(season);
			if (gi === null || Number.isNaN(rl.xs[gi])) continue;
			// anchor just above the column TOP (not the base — the base sits
			// behind the bottom-anchored caption card on mobile)
			const topWorld = rl.bottom + rl.counts[gi] * rl.invMax * rl.usableH;
			const p = f.projectToCss(rl.xs[gi], topWorld);
			out.push({ season, x: p.x, y: p.y });
		}
		colLabels = out;
	});

	/* the two-tone split is legible only once it is actually rendered */
	const showTwoTone = $derived(step >= 3 && twoToneAvailable);
	/* labels appear once the columns have formed (the morph has completed) */
	const labelsShown = $derived(step >= 1 && colLabels.length > 0);
</script>

<div class="pin" class:reduced class:active>
	<!-- season labels float just above their field columns (DOM, CSS px —
	     always legible on mobile, no SVG to shrink; MF2 for this scene) -->
	{#if labelsShown}
		<div class="fw-labels" aria-hidden="true">
			{#each colLabels as c (c.season)}
				<div class="fw-label" style="left:{c.x.toFixed(1)}px; top:{c.y.toFixed(1)}px;">
					{c.season}
				</div>
			{/each}
			{#if showTwoTone}
				<div class="fw-legend">Bright slice = a six from one of the season's ten biggest hitters</div>
			{/if}
		</div>
	{/if}

	<div class="caption-slot" style:--reveal={reveal}>
		{#if step === 1}
			<div class="scene-card">
				<p>
					<strong>Every IPL six ever hit, one dot each, stacked up by season.</strong> Back in 2008,
					a six landed every {bpsFirst ?? '-'} balls. By 2026, <strong>one every {bpsLast ?? '-'}.</strong>
				</p>
				<p class="note">
					The WPL's sixes stay parked on their own shelf for now. Its batting gets its own moment next.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>
					It is not just that batters swing big more often.
					<strong>
						More of those big swings are landing:
						{aerialEarly ? fmt1(aerialEarly.execution_pct) : '-'}% then,
						{aerialRecent ? fmt1(aerialRecent.execution_pct) : '-'}% now.
					</strong>
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('sixes')}
						aria-label="How we computed this">ⓘ</button
					>
					Braver, <em>and</em> better at it.
				</p>
			</div>
		{:else if step === 3}
			<div class="scene-card">
				<p>
					And the six stopped belonging to a handful of big hitters.
					<strong>
						Batters hitting ten or more sixes in a season:
						{s2008 ? s2008.players_10plus_sixes : '-'} in 2008,
						{s2026 ? s2026.players_10plus_sixes : '-'} in 2026.
					</strong>
					{#if showTwoTone}Watch the big hitters' slice of each column shrink.{/if}
					<button
						class="dagger"
						onclick={() => footnotesOpen.set('sixes')}
						aria-label="How we computed this">ⓘ</button
					>
				</p>
			</div>
		{/if}
	</div>
</div>

<style>
	/* viewport-fixed while active — one scene's captions on screen at a time */
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
	}

	.pin.active {
		visibility: visible;
	}

	/* ---- DOM column labels (anchored to field columns; own class to avoid the
	   shell season-label plane's .col-label) ---- */
	.fw-labels {
		position: absolute;
		inset: 0;
	}

	.fw-label {
		position: absolute;
		/* anchor point is the column TOP; float the label just above it, centered */
		transform: translate(-50%, calc(-100% - 5px));
		font-size: 13px;
		font-weight: 700;
		letter-spacing: 0.04em;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.95);
		white-space: nowrap;
	}

	.fw-legend {
		position: absolute;
		top: 3vh;
		left: 50%;
		transform: translateX(-50%);
		font-size: 12px;
		letter-spacing: 0.02em;
		color: var(--ink-dim);
		background: rgba(11, 14, 20, 0.6);
		padding: 0.2rem 0.6rem;
		border-radius: 999px;
		white-space: nowrap;
	}

	.caption-slot {
		position: absolute;
		left: 8vw;
		bottom: 10vh;
		max-width: min(32rem, 84vw);
		/* mobile read-then-watch (CONTRACT §17); resolves to 1 on desktop / SSR */
		opacity: var(--reveal, 1);
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
		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			/* clear the shell's fixed "how we computed this" affordance (bottom 14px) */
			bottom: max(72px, calc(env(safe-area-inset-bottom) + 60px));
		}
	}
</style>
