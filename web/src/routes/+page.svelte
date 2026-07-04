<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import type { FieldHandle, FieldStats } from '$lib/field/field';

	let canvas: HTMLCanvasElement;
	let stickyViewport: HTMLDivElement;
	let labelLayer: HTMLDivElement;
	let scrollRoot: HTMLElement;

	let hud = $state(false);
	let dataMode = $state<'loading' | 'real' | 'synthetic' | 'error'>('loading');
	let errorMsg = $state('');
	let reduced = $state(false);
	let hudStats = $state<FieldStats>({ frames: 0, fps: 0, nPoints: 0, progress: 0 });

	// Scroll → morph mapping across the tall container:
	// step (i) hold the free field, (ii) morph to season columns, (iii) hold columns.
	const HOLD_END = 0.3;
	const MORPH_END = 0.72;
	function morphT(p: number): number {
		return Math.min(1, Math.max(0, (p - HOLD_END) / (MORPH_END - HOLD_END)));
	}

	onMount(() => {
		let field: FieldHandle | null = null;
		let trigger: { kill: () => void } | null = null;
		let hudTimer: ReturnType<typeof setInterval> | null = null;
		let disposed = false;
		let lastRaw = 0;

		const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
		reduced = mq.matches;

		const applyProgress = (raw: number): void => {
			lastRaw = raw;
			let t = morphT(raw);
			// Reduced motion: no interpolation — each scroll step renders its
			// end-state layout as a live jump-cut through the same renderer.
			if (reduced) t = t < 0.5 ? 0 : 1;
			field?.setProgress(t);
		};

		const onMotionPrefChange = (e: MediaQueryListEvent): void => {
			reduced = e.matches;
			applyProgress(lastRaw);
		};
		mq.addEventListener('change', onMotionPrefChange);

		(async () => {
			hud = new URLSearchParams(window.location.search).has('hud');

			try {
				// Heavy modules are loaded client-side only (page is prerendered).
				const [{ loadFieldData }, fieldMod, gsapMod, stMod] = await Promise.all([
					import('$lib/field/data'),
					import('$lib/field/field'),
					import('gsap'),
					import('gsap/ScrollTrigger')
				]);
				const data = await loadFieldData(base);
				if (disposed) return;

				field = fieldMod.createField({
					canvas,
					container: stickyViewport,
					labelLayer,
					data,
					onRender: (s) => {
						if (hud) hudStats = { ...s };
					}
				});
				dataMode = data.synthetic ? 'synthetic' : 'real';

				const gsap = gsapMod.gsap;
				const ScrollTrigger = stMod.ScrollTrigger;
				gsap.registerPlugin(ScrollTrigger);
				const st = ScrollTrigger.create({
					trigger: scrollRoot,
					start: 'top top',
					end: 'bottom bottom',
					scrub: true, // uProgress is driven by scroll only
					onUpdate: (self) => applyProgress(self.progress)
				});
				trigger = st;
				// Seed from the trigger's own progress, not 0: browsers restore the
				// scroll position on reload/back-navigation before this runs, and
				// onUpdate only fires on *changes* — seeding 0 would leave a reader
				// mid-page staring at the wrong layout until their first scroll.
				applyProgress(st.progress);

				if (hud) {
					// DOM-only ticker so the FPS readout decays to 0 when idle.
					// It never touches the GL renderer — the frames counter is the
					// demand-mode proof and only moves when a real render happens.
					let framesAtLastTick = -1;
					hudTimer = setInterval(() => {
						if (!field) return;
						const s = field.stats;
						hudStats = { ...s, fps: s.frames === framesAtLastTick ? 0 : s.fps };
						framesAtLastTick = s.frames;
					}, 500);
				}
			} catch (err) {
				dataMode = 'error';
				errorMsg = err instanceof Error ? err.message : String(err);
			}
		})();

		return () => {
			disposed = true;
			mq.removeEventListener('change', onMotionPrefChange);
			if (hudTimer !== null) clearInterval(hudTimer);
			trigger?.kill();
			field?.dispose();
		};
	});
</script>

<svelte:head>
	<title>Every Ball Ever — the field</title>
	<meta
		name="description"
		content="Every ball ever bowled in the IPL and WPL, as one living field of light. R0 particle-morph spike."
	/>
</svelte:head>

<section class="scroll-stage" bind:this={scrollRoot}>
	<div class="sticky-viewport" bind:this={stickyViewport}>
		<canvas bind:this={canvas} aria-hidden="true"></canvas>
		<div class="labels" bind:this={labelLayer} aria-hidden="true"></div>

		{#if dataMode === 'loading'}
			<div class="overlay boot" role="status">assembling the field…</div>
		{:else if dataMode === 'error'}
			<div class="overlay error" role="alert">
				<p><strong>The field can’t assemble.</strong></p>
				<p class="detail">
					Data files are missing from <code>/data/</code> — the pipeline emits
					<code>meta.json · groups.json · group_ids.u16 · attrs.u8</code> into
					<code>web/static/data/</code> at integration.
				</p>
				<p class="detail mono">{errorMsg}</p>
			</div>
		{/if}
	</div>

	<div class="caption step-1">
		<p class="overline">Every Ball Ever</p>
		<h1>Every ball ever bowled in the IPL and WPL.</h1>
	</div>
	<div class="caption step-2">
		<p>Nineteen seasons of one league, four of another.</p>
	</div>
	<div class="caption step-3">
		<p>This is the field the whole story plays on.</p>
	</div>
</section>

{#if hud}
	<aside class="hud" aria-label="render debug HUD">
		<div class="row"><span>frames rendered</span><b>{hudStats.frames}</b></div>
		<div class="row"><span>fps (scrub)</span><b>{hudStats.fps}</b></div>
		<div class="row"><span>points</span><b>{hudStats.nPoints.toLocaleString('en-IN')}</b></div>
		<div class="row"><span>morph</span><b>{hudStats.progress.toFixed(3)}</b></div>
		<div class="row"><span>data</span><b class:warn={dataMode === 'synthetic'}>{dataMode}</b></div>
		<div class="row"><span>reduced motion</span><b>{reduced ? 'on' : 'off'}</b></div>
	</aside>
{/if}

<style>
	.scroll-stage {
		position: relative;
		height: 420vh;
	}

	.sticky-viewport {
		position: sticky;
		top: 0;
		height: 100vh;
		height: 100dvh;
		overflow: hidden;
	}

	canvas {
		display: block;
		width: 100%;
		height: 100%;
	}

	/* ---- DOM label plane (shares the GL projection) ---- */
	.labels {
		position: absolute;
		inset: 0;
		pointer-events: none;
		transition: none; /* opacity is scrub-driven, never animated on its own */
	}

	.labels :global(.col-anchor) {
		position: absolute;
		top: 0;
		left: 0;
		will-change: transform;
	}

	.labels :global(.col-label) {
		position: absolute;
		transform: translate(-50%, 10px);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
		font-size: 11px;
		letter-spacing: 0.04em;
		color: var(--ink-dim);
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}

	.labels :global(.col-label .season) {
		color: var(--ink);
		font-weight: 600;
	}

	.labels :global(.col-label .count) {
		font-size: 10px;
		opacity: 0.75;
	}

	.labels :global(.col-label.wpl .season) {
		color: var(--teal);
	}

	/* tight column pitch (mobile): rotate labels to a vertical run */
	.labels:global(.vertical) :global(.col-label) {
		display: block;
		writing-mode: vertical-rl;
		transform: translate(-50%, 8px);
	}

	.labels:global(.vertical) :global(.col-label .count) {
		margin-inline-start: 5px;
	}

	.labels :global(.league-heading) {
		position: absolute;
		transform: translate(-50%, 52px);
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.3em;
		color: var(--ink-dim);
	}

	.labels:global(.vertical) :global(.league-heading) {
		transform: translate(-50%, 72px);
	}

	.labels :global(.league-heading.wpl) {
		color: var(--teal);
	}

	/* ---- caption column ---- */
	.caption {
		position: absolute;
		left: 8vw;
		max-width: min(30rem, 84vw);
		pointer-events: none;
		background: rgba(11, 14, 20, 0.55);
		border: 1px solid rgba(232, 236, 245, 0.08);
		border-radius: 12px;
		padding: 1.1rem 1.4rem;
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
	}

	.step-1 {
		top: 16vh;
	}
	.step-2 {
		top: 176vh;
	}
	.step-3 {
		top: 338vh;
	}

	.caption h1 {
		margin: 0;
		font-size: clamp(1.4rem, 3.4vw, 2.1rem);
		line-height: 1.25;
		font-weight: 650;
	}

	.caption p {
		margin: 0;
		font-size: clamp(1.05rem, 2.4vw, 1.35rem);
		line-height: 1.45;
		color: var(--ink);
	}

	.caption .overline {
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.28em;
		text-transform: uppercase;
		color: var(--gold);
		margin-bottom: 0.55rem;
	}

	@media (max-width: 640px) {
		.caption {
			left: 50%;
			transform: translateX(-50%);
			text-align: center;
		}
	}

	/* ---- overlays ---- */
	.overlay {
		position: absolute;
		inset: 0;
		display: grid;
		place-content: center;
		text-align: center;
		padding: 2rem;
		gap: 0.6rem;
	}

	.boot {
		color: var(--ink-dim);
		font-size: 0.95rem;
		letter-spacing: 0.12em;
	}

	.error p {
		margin: 0;
		max-width: 34rem;
	}

	.error .detail {
		color: var(--ink-dim);
		font-size: 0.88rem;
	}

	.error .mono,
	.error code {
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.8rem;
	}

	/* ---- dev HUD (?hud=1) ---- */
	.hud {
		position: fixed;
		top: 12px;
		right: 12px;
		z-index: 50;
		min-width: 200px;
		padding: 10px 12px;
		border-radius: 10px;
		background: rgba(11, 14, 20, 0.82);
		border: 1px solid rgba(46, 196, 182, 0.35);
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 11px;
		color: var(--ink);
	}

	.hud .row {
		display: flex;
		justify-content: space-between;
		gap: 16px;
		padding: 1px 0;
	}

	.hud .row span {
		color: var(--ink-dim);
	}

	.hud .row b.warn {
		color: var(--ember);
	}
</style>
