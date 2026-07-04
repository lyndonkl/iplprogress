<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import type { FieldHandle, FieldStats } from '$lib/field/field';
	import { chapterProgress, footnotesOpen, pickedTeam } from '$lib/state';
	import {
		dynamicTarget,
		heldState,
		morphFraction,
		resolveRenderState,
		sceneEndState
	} from './fieldstate';
	import type { SceneDef } from './types';
	import FootnotePanel from './FootnotePanel.svelte';

	/**
	 * The story shell: ONE persistent field renderer (it never unmounts) under
	 * an ordered list of scenes, composed into a single scroll timeline by GSAP
	 * ScrollTrigger. Each scene owns a scroll section; its leading morphLength
	 * scrubs the field from the previous scene's fieldState to its own, the
	 * rest holds (zero renders while holding — demand mode).
	 *
	 * prefers-reduced-motion: every scene renders its live end state as a
	 * jump-cut through the same renderer — personalization and theming survive,
	 * zero image payload (blueprint §2).
	 */

	interface Props {
		scenes: SceneDef[];
		/** notified whenever the active scene changes (nav visibility, progress) */
		onSceneChange?: (index: number, scene: SceneDef) => void;
		/**
		 * notified when a set-piece field morph (the assembly scrub or the
		 * ignition-wall morph) enters/leaves flight — the nav dims to 40% while
		 * true so the ☰ never fights a set piece (storyboard §6).
		 */
		onSetPieceChange?: (inFlight: boolean) => void;
	}

	let { scenes, onSceneChange, onSetPieceChange }: Props = $props();

	let canvas: HTMLCanvasElement;
	let stickyViewport: HTMLDivElement;
	let labelLayer: HTMLDivElement;
	let scenesEl: HTMLDivElement;

	let hud = $state(false);
	let dataMode = $state<'loading' | 'real' | 'synthetic' | 'error'>('loading');
	let errorMsg = $state('');
	let reduced = $state(false);
	let fieldHandle = $state<FieldHandle | null>(null);
	let hudStats = $state<FieldStats>({ frames: 0, fps: 0, nPoints: 0, progress: 0 });
	// the scene list is static for the life of the story; sizing the progress
	// array from its initial value is intentional
	// svelte-ignore state_referenced_locally
	let progresses = $state<number[]>(scenes.map(() => 0));

	/* ---- active scene: the last section whose top has crossed the viewport top */
	const currentIdx = $derived.by(() => {
		let cur = 0;
		for (let i = 0; i < progresses.length; i++) if (progresses[i] > 0) cur = i;
		return cur;
	});

	const activeScene = $derived(scenes[currentIdx]);
	const activeFootnote = $derived(activeScene.footnote ?? null);

	/* ---- picked team → team id (teams.json), -1 when neutral/unset ---------- */
	const teamId = $derived.by(() => {
		const pick = $pickedTeam;
		const f = fieldHandle;
		if (!pick || !f || pick.league === null || pick.team === 'neutral') return -1;
		const t = f.data.teams.find((tm) => tm.league === pick.league && tm.name === pick.team);
		return t ? t.id : -1;
	});

	/* ---- the one field-application path (scroll, team, motion-pref, scene) ---
	   `to` is the scene's live target (fieldState resolved through its optional
	   dynamicState at the current progress — so a caption step can drive a
	   one-change held-state update, e.g. C1-5's two-tone re-sort recolor).
	   `from` is the previous scene's fully-SETTLED held state, so a re-sort that
	   engaged and tinted to completion settles back from that state (no pop). */
	$effect(() => {
		const f = fieldHandle;
		if (!f) return;
		const cur = currentIdx;
		const scene = scenes[cur];
		const p = progresses[cur];
		const to = reduced ? sceneEndState(scene) : dynamicTarget(scene, p);
		const from =
			scene.fromState ??
			(cur > 0 ? (reduced ? sceneEndState(scenes[cur - 1]) : heldState(scenes[cur - 1])) : to);
		const t = reduced
			? 1 // live end-state jump-cut, no interpolation
			: Math.min(1, Math.max(0, p / morphFraction(scene)));
		f.applyState(resolveRenderState(from, to, t, teamId));
	});

	/* ---- set-piece morph in flight → nav dims (storyboard §6). A set piece is
	   a big field move: a layout change (ignition wall, close return) OR a
	   reveal scrub (the assembly). Detected structurally so no scene id is
	   hard-coded here. Never in flight under reduced motion (jump-cut). */
	const setPieceInFlight = $derived.by(() => {
		if (reduced) return false;
		const cur = currentIdx;
		const scene = scenes[cur];
		const to = scene.fieldState;
		const from = scene.fromState ?? (cur > 0 ? scenes[cur - 1].fieldState : to);
		const bigMove = from.layout !== to.layout || (from.reveal ?? 1) !== (to.reveal ?? 1);
		if (!bigMove) return false;
		const t = progresses[cur] / morphFraction(scene);
		return t > 0.001 && t < 0.999;
	});

	/* ---- scene-change notifications + progress persistence ------------------- */
	$effect(() => {
		const scene = scenes[currentIdx];
		onSceneChange?.(currentIdx, scene);
		chapterProgress.set({ scene: scene.anchor ?? scene.id, ts: Date.now() });
	});

	$effect(() => {
		onSetPieceChange?.(setPieceInFlight);
	});

	onMount(() => {
		let disposed = false;
		let field: FieldHandle | null = null;
		let triggers: { kill: () => void; progress: number }[] = [];
		let hudTimer: ReturnType<typeof setInterval> | null = null;
		let scrollTriggerApi: { update: () => void; refresh: () => void } | null = null;

		const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
		reduced = mq.matches;
		const onMotionPrefChange = (e: MediaQueryListEvent): void => {
			reduced = e.matches;
		};
		mq.addEventListener('change', onMotionPrefChange);

		const onHashChange = (): void => {
			// deep-link contract: force triggers to re-read scroll after a jump
			// (the anchor element sits 2px inside its section, so the native jump
			// itself already lands past the trigger boundary)
			scrollTriggerApi?.update();
		};
		window.addEventListener('hashchange', onHashChange);

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
				fieldHandle = field;
				dataMode = data.synthetic ? 'synthetic' : 'real';

				const gsap = gsapMod.gsap;
				const ScrollTrigger = stMod.ScrollTrigger;
				gsap.registerPlugin(ScrollTrigger);
				scrollTriggerApi = ScrollTrigger;

				const sectionEls = Array.from(
					scenesEl.querySelectorAll<HTMLElement>(':scope > section.scene')
				);
				triggers = sectionEls.map((el, i) =>
					ScrollTrigger.create({
						trigger: el,
						start: 'top top',
						end: 'bottom top',
						// scrub semantics: progress drives the field directly; the
						// $effect above resolves it into exactly one render per change
						onUpdate: (self) => {
							progresses[i] = self.progress;
						}
					})
				);
				ScrollTrigger.refresh();
				// Seed from the triggers' own progress, not 0: browsers restore the
				// scroll position on reload/back-navigation before this runs, and
				// onUpdate only fires on *changes* — seeding 0 would leave a reader
				// mid-page staring at the wrong layout until their first scroll.
				triggers.forEach((t, i) => {
					progresses[i] = t.progress;
				});

				// Deep entry: honor the hash once triggers exist, then update()
				if (window.location.hash.length > 1) {
					const el = document.getElementById(window.location.hash.slice(1));
					if (el) {
						el.scrollIntoView({ block: 'start' });
						ScrollTrigger.update();
						triggers.forEach((t, i) => {
							progresses[i] = t.progress;
						});
					}
				}

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
			window.removeEventListener('hashchange', onHashChange);
			if (hudTimer !== null) clearInterval(hudTimer);
			for (const t of triggers) t.kill();
			field?.dispose();
			fieldHandle = null;
		};
	});
</script>

<div class="story">
	<!-- the persistent field: one renderer for the whole piece -->
	<div class="stage" bind:this={stickyViewport}>
		<canvas bind:this={canvas} aria-hidden="true"></canvas>
		<div class="labels" bind:this={labelLayer} aria-hidden="true"></div>

		{#if dataMode === 'loading'}
			<div class="overlay boot" role="status">assembling the field…</div>
		{:else if dataMode === 'error'}
			<div class="overlay error" role="alert">
				<p><strong>The field can’t assemble.</strong></p>
				<p class="detail">
					Data files are missing from <code>/data/</code> — the pipeline emits
					<code>meta.json · groups.json · teams.json · group_ids.u16 · attrs.u8 ·
					ballsfaced.u8 · team.u8</code> into <code>web/static/data/</code> at integration.
				</p>
				<p class="detail mono">{errorMsg}</p>
			</div>
		{/if}
	</div>

	<!-- scene sections overlay the sticky stage; each owns its scroll span -->
	<div class="scenes" bind:this={scenesEl}>
		{#each scenes as scene, i (scene.id)}
			{@const Annotations = scene.annotations}
			<section class="scene" style:height="{scene.scrollLength}vh">
				<!-- the anchor sits 2px INSIDE the section so a native fragment jump
				     (and Chrome's on-load fragment re-snap) always lands past the
				     trigger boundary and the anchored scene owns the field -->
				<div class="scene-anchor" id={scene.anchor ?? scene.id} aria-hidden="true"></div>
				<Annotations
					progress={progresses[i]}
					active={i === currentIdx}
					field={fieldHandle}
					{reduced}
				/>
			</section>
		{/each}
	</div>
</div>

<!-- per-scene footnote affordance (tap/keyboard, never hover-only) -->
{#if activeFootnote}
	<button
		class="footnote-affordance"
		onclick={() => footnotesOpen.set(activeFootnote)}
		aria-haspopup="dialog"
	>
		<span aria-hidden="true">ⓘ</span> how we computed this
	</button>
{/if}

<FootnotePanel />

{#if hud}
	<aside class="hud" aria-label="render debug HUD" aria-hidden="true">
		<div class="row"><span>frames rendered</span><b>{hudStats.frames}</b></div>
		<div class="row"><span>fps (scrub)</span><b>{hudStats.fps}</b></div>
		<div class="row"><span>points</span><b>{hudStats.nPoints.toLocaleString('en-US')}</b></div>
		<div class="row"><span>morph</span><b>{hudStats.progress.toFixed(3)}</b></div>
		<div class="row"><span>scene</span><b>{activeScene.id}</b></div>
		<div class="row"><span>data</span><b class:warn={dataMode === 'synthetic'}>{dataMode}</b></div>
		<div class="row"><span>reduced motion</span><b>{reduced ? 'on' : 'off'}</b></div>
	</aside>
{/if}

<style>
	.story {
		position: relative;
	}

	.stage {
		position: sticky;
		top: 0;
		height: 100vh;
		height: 100dvh;
		overflow: hidden;
		z-index: 0;
	}

	canvas {
		display: block;
		width: 100%;
		height: 100%;
	}

	.scenes {
		position: relative;
		z-index: 1;
		margin-top: -100vh;
		margin-top: -100dvh;
	}

	/* sections never intercept the field; scene components opt interactive
	   elements back in with pointer-events: auto (see CONTRACT.md) */
	section.scene {
		position: relative;
		pointer-events: none;
	}

	.scene-anchor {
		position: absolute;
		top: 2px;
		left: 0;
		width: 1px;
		height: 1px;
	}

	/* ---- DOM label plane (shares the GL projection) ---- */
	.labels {
		position: absolute;
		inset: 0;
		pointer-events: none;
		transition: none; /* opacity is scene-state-driven, never animated on its own */
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

	/* ---- footnote affordance ---- */
	.footnote-affordance {
		position: fixed;
		bottom: 14px;
		right: 14px;
		z-index: 60;
		min-height: 44px;
		padding: 0.5rem 0.9rem;
		border-radius: 999px;
		border: 1px solid rgba(232, 236, 245, 0.16);
		background: rgba(11, 14, 20, 0.62);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
		color: var(--ink-dim);
		font-size: 0.78rem;
		letter-spacing: 0.04em;
		cursor: pointer;
	}

	.footnote-affordance:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* ---- dev HUD (?hud=1) ---- */
	.hud {
		position: fixed;
		top: 66px;
		right: 12px;
		z-index: 90;
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
