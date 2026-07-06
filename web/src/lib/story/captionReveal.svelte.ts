/**
 * "Read, then watch" — the shared MOBILE-ONLY caption reveal mechanism.
 * See CONTRACT.md §17 for the full contract + the per-scene adoption recipe.
 *
 * THE PROBLEM this fixes: on phones the caption box sits ON TOP of the
 * full-screen field/charts, so a reader can never see the visual they are
 * reading about. THE FIX the owner chose: within each caption STEP's scroll
 * range the caption fades IN (read beat), then fades fully OUT to a CLEAR GAP
 * (watch beat) before the next step — text and picture take turns.
 *
 * This module maps the reader's scroll position WITHIN the current step to an
 * opacity in [0,1] following that curve. It is gated so DESKTOP and
 * REDUCED-MOTION readers get a constant 1 (the persistent corner caption is
 * unchanged and byte-identical): only a mobile viewport (or the
 * `?mobilecaptions=1` preview flag) turns the fade on.
 *
 * Scenes apply the returned opacity to their `.caption-slot` via a CSS custom
 * property `--reveal` (default 1) so it COMPOSES with any existing appear-gate
 * and is a no-op on desktop / SSR / no-JS. Opacity only — the caption stays in
 * the DOM and the accessibility tree even at 0 (screen readers still reach it).
 */

/* -------------------------------------------------------------------------- */
/*  The gate: is the read-then-watch fade ACTIVE for this viewport?            */
/* -------------------------------------------------------------------------- */

/** The mobile breakpoint — matches every scene's `@media (max-width: 640px)`. */
const MOBILE_QUERY = '(max-width: 640px)';

/**
 * The DEBUG flag: `?mobilecaptions=1` FORCES the read-then-watch behaviour
 * regardless of viewport, purely for preview/testing in a desktop automation
 * browser that cannot emulate a 375px phone (mirrors the existing `?hud=1`).
 */
const FORCE_PARAM = 'mobilecaptions';

/**
 * Reactive singleton: true when the read-then-watch fade should apply, i.e. a
 * mobile-width viewport OR the `?mobilecaptions=1` force flag. Initialised once
 * per page on the client; stays `false` during SSR/prerender (no `window`), so
 * the prerendered HTML — and every desktop reader — gets the persistent
 * caption. The matchMedia listener keeps it live across resizes/rotation.
 */
let active = $state(false);

if (typeof window !== 'undefined') {
	if (new URLSearchParams(window.location.search).has(FORCE_PARAM)) {
		active = true;
	} else {
		const mql = window.matchMedia(MOBILE_QUERY);
		active = mql.matches;
		// module-singleton listener: lives for the page lifetime (never removed)
		mql.addEventListener('change', (e) => {
			active = e.matches;
		});
	}
}

/**
 * Reactive: true when read-then-watch is active (mobile viewport, or forced by
 * `?mobilecaptions=1`). Reading this inside a `$derived`/`$effect` tracks it, so
 * callers recompute when the viewport crosses the mobile breakpoint. Also drives
 * the optional mobile scroll-length bump in Story.svelte.
 */
export function captionRevealActive(): boolean {
	return active;
}

/* -------------------------------------------------------------------------- */
/*  The curve                                                                  */
/* -------------------------------------------------------------------------- */

export interface CaptionRevealOpts {
	/**
	 * prefers-reduced-motion. Under reduced motion scenes JUMP-CUT (there is no
	 * morph to watch), so the caption must STAY VISIBLE — pass this and the
	 * helper returns 1 (no fade). Scenes already receive `reduced` as a prop.
	 */
	reduced?: boolean;
	/** fraction of the step spent fading IN at the start (default 0.06 — fast). */
	fadeIn?: number;
	/**
	 * fraction of the step (from the step start) held FULLY visible for the READ
	 * beat (default 0.60 — the first ~60%; owner spec is 55–65%).
	 */
	readHold?: number;
	/**
	 * fraction of the step spent fading OUT after the read beat (default 0.20).
	 * The remaining tail — `1 - readHold - fadeOut` — is the CLEAR GAP at
	 * opacity 0 where the reader WATCHES the unobstructed visual (default 0.20).
	 */
	fadeOut?: number;
}

function clamp01(x: number): number {
	return x < 0 ? 0 : x > 1 ? 1 : x;
}

/**
 * PURE opacity curve for the reader position `progress` within the step
 * `[stepStart, stepEnd)`, ignoring the mobile/reduced gate. Exported for tests
 * and advanced use; scenes call {@link captionReveal} instead.
 *
 * Shape (local position u = (progress - stepStart) / (stepEnd - stepStart)):
 *   u ∈ [0, fadeIn)                 → ramp 0 → 1   (fast fade-in)
 *   u ∈ [fadeIn, readHold)          → 1            (hold — the READ beat)
 *   u ∈ [readHold, readHold+fadeOut)→ ramp 1 → 0   (fade-out)
 *   u ∈ [readHold+fadeOut, 1)       → 0            (the CLEAR GAP — watch beat)
 */
export function captionRevealCurve(
	progress: number,
	stepStart: number,
	stepEnd: number,
	opts: CaptionRevealOpts = {}
): number {
	const span = stepEnd - stepStart;
	if (span <= 0) return 1; // degenerate bounds → never hide

	const u = (progress - stepStart) / span;
	if (u <= 0 || u >= 1) return 0; // before this step, or past the gap → next step owns the screen

	const fadeIn = opts.fadeIn ?? 0.06;
	const readHold = opts.readHold ?? 0.6;
	const fadeOut = opts.fadeOut ?? 0.2;

	if (u < fadeIn) return clamp01(u / fadeIn); // 1) fast fade-in
	if (u < readHold) return 1; //                 2) hold for the read beat
	const fadeOutEnd = readHold + fadeOut;
	if (u < fadeOutEnd) return clamp01(1 - (u - readHold) / fadeOut); // 3) fade-out
	return 0; //                                   4) clear gap (watch beat)
}

/**
 * The scene-facing helper: the read-then-watch opacity for `.caption-slot`.
 *
 * Returns **1** on DESKTOP, during SSR/prerender, and under REDUCED MOTION —
 * so the persistent corner caption is unchanged. On a mobile viewport (or with
 * `?mobilecaptions=1`) and normal motion, returns the {@link captionRevealCurve}
 * value for the reader's position within the current caption step.
 *
 * @param progress  the scene's 0..1 scroll progress (the `progress` prop)
 * @param stepStart progress at which the current caption step begins (inclusive)
 * @param stepEnd   progress at which the current caption step ends (exclusive)
 * @param opts      `{ reduced }` (required for correctness) + optional curve tuning
 */
export function captionReveal(
	progress: number,
	stepStart: number,
	stepEnd: number,
	opts: CaptionRevealOpts = {}
): number {
	if (opts.reduced || !captionRevealActive()) return 1;
	return captionRevealCurve(progress, stepStart, stepEnd, opts);
}

/* -------------------------------------------------------------------------- */
/*  Optional: mobile scroll-length bump for a comfortable read + gap           */
/* -------------------------------------------------------------------------- */

/**
 * Multiplier a scene MAY apply to its `scrollLength` on mobile so the read beat
 * and the clear gap both feel unhurried (the reveal splits each step into
 * ~60% read + ~20% fade + ~20% watch, so a step that was comfortable as a
 * single desktop caption can feel rushed on a phone). ~1.3 adds a third more
 * scroll travel. Tuning value — not mandatory.
 */
export const MOBILE_READ_GAP_SCALE = 1.3;

/**
 * Recommended mobile scroll length (vh) for a scene that adopts read-then-watch
 * and whose steps feel cramped: `round(baseVh * MOBILE_READ_GAP_SCALE)`. Set it
 * on the SceneDef's optional `mobileScrollLength` — Story.svelte uses it only
 * when the mobile gate is active, so desktop is untouched.
 */
export function readGapScrollLength(baseVh: number): number {
	return Math.round(baseVh * MOBILE_READ_GAP_SCALE);
}
