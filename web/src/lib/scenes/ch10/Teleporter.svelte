<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { captionReveal } from '$lib/story/captionReveal.svelte';
	import { footnotesOpen } from '$lib/state';
	import RibbonField from './RibbonField.svelte';
	import { pickRibbonCorner, cornerStyle } from './captionCorner.svelte';
	import { loadCh10Data, fmt1, pct0, type Ch10Data, type Translation } from './data';

	/**
	 * C10-6, Supporting 3: the Player Teleporter. Run the machine on a player. TWO
	 * hard-separated machines, never co-displayed, Machine A's figures cleared before
	 * Machine B's world appears (colliding units: strike rate vs percent above par).
	 * Machine A translates ONE player through time (Sehwag 185 -> honest 214, the
	 * naive ghost overshoots to 224) as two markers on ONE aligned strike-rate axis
	 * anchored at 185, the shaded gap the exhibit, the honest band strictly narrower
	 * than the gap (band < gap). Machine B ranks against each player's OWN era as a
	 * bar-SWAP: raw says Fraser-McGurk, era-adjusted says Gayle, a plain percent gap
	 * and NEVER a z-score.
	 *
	 * NOTE: the field subset lift (setTeleport) is intentionally not engaged because
	 * scenes/ch10.json carries no per-delivery point indices for the picked player-
	 * season; the two 2D machines ARE the load-bearing exhibit (and match the reduced-
	 * motion contract, invariant 8, which never plays the lift either).
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	let ch10 = $state<Ch10Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh10Data().then((d) => {
			if (alive) ch10 = d;
		});
		return () => {
			alive = false;
		};
	});

	const step = $derived(progress < 0.2 ? 1 : progress < 0.4 ? 2 : progress < 0.6 ? 3 : progress < 0.8 ? 4 : 5);
	const BOUNDS = [0, 0.2, 0.4, 0.6, 0.8, 1] as const;
	const reveal = $derived(captionReveal(progress, BOUNDS[step - 1], BOUNDS[step], { reduced }));
	const corner = $derived(pickRibbonCorner(field, 'tl'));

	const a = $derived(ch10?.teleporter.machine_a ?? null);
	const bmac = $derived(ch10?.teleporter.machine_b ?? null);

	// Machine A owns steps 1-3; Machine B owns steps 4-5 (a HARD RESET between them,
	// so the two number-worlds never share the screen). Under reduced motion both
	// render as static sub-cards stacked (invariant 8), and Machine B shows the raw
	// AND the era-adjusted bars side by side so the swap is a visible still.
	const showA = $derived(reduced || step <= 3);
	const showB = $derived(reduced || step >= 4);
	const swapped = $derived(step >= 5);

	// the era dial: pick which translation year to quote (default the last = 2026)
	let yearIdx = $state<number | null>(null);
	$effect(() => {
		if (!active) yearIdx = null;
	});
	const translations = $derived<Translation[]>(a?.default.translations ?? []);
	const effIdx = $derived(yearIdx ?? Math.max(0, translations.length - 1));
	const tr = $derived<Translation | null>(translations[effIdx] ?? null);

	// the aligned strike-rate axis domain (anchor at bottom, ghost ceiling at top)
	const axis = $derived.by(() => {
		if (!a) return { lo: 180, hi: 230 };
		const naives = translations.map((t) => t.naive);
		const los = translations.map((t) => t.band_lo);
		const lo = Math.min(a.anchor_sr, ...los) - 6;
		const hi = Math.max(...naives) + 8;
		return { lo, hi };
	});
	function frac(sr: number): number {
		return Math.min(1, Math.max(0, (sr - axis.lo) / (axis.hi - axis.lo)));
	}
	// percent-from-bottom for the marker
	function bottomPct(sr: number): number {
		return frac(sr) * 100;
	}

	const bPlayers = $derived(bmac?.players ?? []);
	const maxRaw = $derived(bPlayers.length ? Math.max(...bPlayers.map((p) => p.sr)) : 1);
	const maxPar = $derived(bPlayers.length ? Math.max(...bPlayers.map((p) => p.pct_above_par)) : 1);
</script>

{#snippet bars(useSwap: boolean)}
	<div class="bar-panel">
		<span class="m-tag">{useSwap ? 'measured against the going rate of his own year' : 'raw strike rate'}</span>
		<div class="bars">
			{#each bPlayers as p (p.name)}
				<div class="bcol">
					<div
						class="bfill"
						class:lead={useSwap ? p.pct_above_par === maxPar : p.sr === maxRaw}
						style="height: {((useSwap ? p.pct_above_par / maxPar : p.sr / maxRaw) * 100).toFixed(1)}%"
					>
						<span class="bval">{useSwap ? `${pct0(p.pct_above_par)}%` : fmt1(p.sr)}</span>
					</div>
					<span class="bname">{p.name}<br /><span class="byr">{p.season}</span></span>
				</div>
			{/each}
		</div>
	</div>
{/snippet}

<div class="pin" class:active>
	<RibbonField {field} {progress} faint={true} footnoteId="ch10-teleporter" />

	<div class="stage" class:reduced>
		{#if a && showA && tr}
			<!-- Machine A: one aligned strike-rate axis anchored at his real number -->
			<div class="machine machine-a">
				<span class="m-tag">translate one player through time</span>
				<div class="axis">
					<!-- the shaded gap between the honest re-quote and the naive ghost IS the exhibit -->
					<div
						class="gap"
						style="bottom: {bottomPct(tr.honest)}%; height: {(bottomPct(tr.naive) - bottomPct(tr.honest)).toFixed(1)}%"
					></div>
					<!-- the honest re-quote: solid marker + uncertainty band (band < gap) -->
					<div
						class="band"
						style="bottom: {bottomPct(tr.band_lo)}%; height: {(bottomPct(tr.band_hi) - bottomPct(tr.band_lo)).toFixed(1)}%"
					></div>
					<div class="mark honest" style="bottom: {bottomPct(tr.honest)}%">
						<span class="mark-t">honest re-quote {fmt1(tr.honest)}</span>
					</div>
					<!-- the naive ghost: a pale dotted marker that overshoots -->
					<div class="mark ghost" style="bottom: {bottomPct(tr.naive)}%">
						<span class="mark-t">naive ghost {fmt1(tr.naive)}</span>
					</div>
					<!-- the anchor: his real number -->
					<div class="mark anchor" style="bottom: {bottomPct(a.anchor_sr)}%">
						<span class="mark-t">{a.default.name} {a.default.season}: {a.anchor_sr}</span>
					</div>
				</div>
				{#if !reduced}
					<div class="dial">
						<label class="dial-label" for="eradial">drag the year</label>
						<input
							id="eradial"
							type="range"
							min="0"
							max={translations.length - 1}
							step="1"
							value={effIdx}
							oninput={(e) => (yearIdx = Number((e.currentTarget as HTMLInputElement).value))}
						/>
						<span class="dial-year">{tr.year}</span>
					</div>
				{/if}
			</div>
		{/if}

		{#if bmac && showB}
			<!-- Machine B: rank each player against his OWN era, drawn as a bar-SWAP -->
			<div class="machine machine-b">
				{#if reduced}
					<!-- the swap as a visible still: raw AND era-adjusted side by side -->
					<div class="both">
						{@render bars(false)}
						{@render bars(true)}
					</div>
				{:else}
					{@render bars(swapped)}
				{/if}
			</div>
		{/if}
	</div>

	<div class="caption-slot" style="{cornerStyle(corner)}; --reveal: {reveal};">
		{#if a && bmac}
			{#if step === 1}
				<div class="scene-card">
					<p>One more thing the machine can do. Pick a player and a year, and it re-quotes their real innings into it. Here is {a.default.name} in {a.default.season}: {a.anchor_sr} runs per 100 balls.</p>
				</div>
			{:else if step === 2}
				<div class="scene-card">
					<p>Now drag him into {tr?.year ?? 2026}. The naive machine just scales him up by how much faster the league scores now, and says {fmt1(tr?.naive ?? a.default.translations[a.default.translations.length - 1].naive)}. A ghost of a number.</p>
				</div>
			{:else if step === 3}
				<div class="scene-card">
					<p>But that forgets something. {a.default.name} was already near the very top of {a.default.season}. Keep him at the same rank, and the honest answer is {fmt1(tr?.honest ?? 213.6)}, not {fmt1(tr?.naive ?? 223.7)}. You cannot just scale an outlier up.</p>
				</div>
			{:else if step === 4}
				<div class="scene-card">
					<p>That translated one player through time. Different question: who was furthest ahead of his own era? Raw, {bmac.players[1].name}'s {bmac.players[1].season} towers over {bmac.players[0].name}'s {bmac.players[0].season}.</p>
				</div>
			{:else}
				<div class="scene-card interactive">
					<p>Now measure each against the going rate of his own year. The bars swap. {bmac.players[0].name} was {pct0(bmac.players[0].pct_above_par)}% faster than his era, {bmac.players[1].name} {pct0(bmac.players[1].pct_above_par)}% faster than his. Measured against the physics of his own time, {bmac.players[0].season} {bmac.players[0].name.split(' ').slice(-1)} still edges {bmac.players[1].season}'s {bmac.players[1].name.split(' ').slice(-1)}.</p>
					<button class="fn" onclick={() => footnotesOpen.set('ch10-teleporter')}>ⓘ how the machine re-quotes</button>
				</div>
			{/if}
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

	/* non-reduced: the stage is transparent so each machine centres itself and only
	   ONE is on screen at a time (the hard reset). reduced: both machines stack. */
	.stage {
		display: contents;
	}

	.stage.reduced {
		display: flex;
		position: fixed;
		inset: 0;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1.4rem;
		padding: 9vh 1rem 4vh;
		overflow-y: auto;
	}

	.stage.reduced .machine {
		position: static;
		transform: none;
	}

	.bar-panel {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.7rem;
	}

	.both {
		display: flex;
		gap: 2rem;
		align-items: flex-end;
	}

	.machine {
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.7rem;
		padding: 1rem 1.2rem;
		border-radius: 14px;
		background: rgba(10, 14, 24, 0.78);
		border: 1px solid rgba(151, 161, 184, 0.22);
	}

	.machine-a {
		border-color: rgba(232, 184, 75, 0.3);
	}

	.machine-b {
		border-color: rgba(46, 196, 182, 0.32);
	}

	.m-tag {
		font-size: 0.62rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.axis {
		position: relative;
		width: min(20rem, 74vw);
		height: min(42vh, 21rem);
		border-left: 2px solid rgba(151, 161, 184, 0.4);
		margin-left: 3rem;
	}

	.gap {
		position: absolute;
		left: 0;
		width: 100%;
		background: repeating-linear-gradient(
			45deg,
			rgba(232, 184, 75, 0.16),
			rgba(232, 184, 75, 0.16) 4px,
			transparent 4px,
			transparent 8px
		);
	}

	.band {
		position: absolute;
		left: 0;
		width: 100%;
		background: rgba(46, 196, 182, 0.22);
		border-top: 1px solid rgba(46, 196, 182, 0.4);
		border-bottom: 1px solid rgba(46, 196, 182, 0.4);
	}

	.mark {
		position: absolute;
		left: 0;
		width: 100%;
		display: flex;
		align-items: center;
	}

	.mark::before {
		content: '';
		width: 100%;
		height: 0;
	}

	.mark-t {
		position: absolute;
		left: 0.4rem;
		transform: translateY(-50%);
		white-space: nowrap;
		font-size: 0.72rem;
		font-weight: 600;
		color: var(--ink);
		text-shadow: 0 1px 4px rgba(0, 0, 0, 0.9);
	}

	.mark.honest {
		border-top: 2.5px solid var(--teal);
	}

	.mark.honest .mark-t {
		color: var(--teal);
	}

	.mark.ghost {
		border-top: 2px dotted rgba(232, 184, 75, 0.9);
	}

	.mark.ghost .mark-t {
		color: var(--gold, #e8b84b);
	}

	.mark.anchor {
		border-top: 1.5px solid rgba(232, 236, 245, 0.5);
	}

	.mark.anchor .mark-t {
		color: var(--ink-dim);
	}

	.dial {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		pointer-events: auto;
	}

	.dial-label {
		font-size: 0.7rem;
		color: var(--ink-dim);
	}

	.dial input {
		width: min(14rem, 50vw);
		accent-color: var(--teal);
		cursor: pointer;
	}

	.dial-year {
		font-size: 0.85rem;
		font-weight: 700;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.bars {
		display: flex;
		align-items: flex-end;
		gap: 2.4rem;
		height: min(40vh, 20rem);
	}

	.bcol {
		display: flex;
		flex-direction: column;
		align-items: center;
		height: 100%;
		justify-content: flex-end;
		gap: 0.4rem;
	}

	.bfill {
		width: 3.6rem;
		background: rgba(151, 161, 184, 0.35);
		border-radius: 6px 6px 0 0;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		transition: height 0.5s ease;
		min-height: 1.6rem;
	}

	.bfill.lead {
		background: rgba(46, 196, 182, 0.5);
	}

	.bval {
		margin-top: -1.3rem;
		font-size: 0.82rem;
		font-weight: 700;
		color: var(--ink);
	}

	.bname {
		font-size: 0.72rem;
		font-weight: 600;
		text-align: center;
		color: var(--ink);
	}

	.byr {
		color: var(--ink-dim);
		font-weight: 400;
		font-variant-numeric: tabular-nums;
	}

	.caption-slot {
		position: absolute;
		max-width: min(24rem, 36vw);
		opacity: var(--reveal, 1);
	}

	.fn {
		margin-top: 0.5rem;
		min-height: 40px;
		padding: 0.2rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font-size: 0.78rem;
		font-weight: 600;
		text-align: left;
		cursor: pointer;
	}

	.fn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.machine {
			top: 40%;
			padding: 0.8rem 0.9rem;
		}

		.axis {
			width: 80vw;
			height: 40vh;
		}

		.bars {
			gap: 1.6rem;
		}

		.caption-slot {
			left: 50% !important;
			right: auto !important;
			top: auto !important;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			bottom: max(4vh, calc(env(safe-area-inset-bottom) + 12px)) !important;
		}
	}
</style>
