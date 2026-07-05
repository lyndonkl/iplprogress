import type { SceneDef, SceneFieldState } from '$lib/story/types';
import Stakes from './Stakes.svelte';
import Draw from './Draw.svelte';
import Assembly, { ASSEMBLY_MORPH_VH, ASSEMBLY_SCROLL_VH } from './Assembly.svelte';

/**
 * COLD OPEN — storyboard §1 (implementation truth) + blueprint §3.
 *
 *   CO-1  stakes line → the You-Draw-It (200+ totals per season; 2008–2012
 *         pre-drawn; "Just show me" equal-weight skip)
 *   CO-2  the reveal — truth line draws over the sketch, divergence shaded
 *         per season and quantified in totals, scripted branch copy
 *         (both live in Draw.svelte: one sticky screen, tap-gated)
 *   CO-3  the assembly set piece — the field streams in chronologically with
 *         the live counter to 316,199, authored counter stops, the WPL's
 *         pinned arrival caption, and the title card
 *
 * CO-1/CO-2 play on an unborn field (assembly layout, reveal 0 — zero points
 * visible, render loop stopped); CO-3 scrubs reveal 0 → 1 as the one
 * whole-scene morph (GSAP set piece #1). Assembly at reveal 1 is
 * position-identical to the free field, so the hand-off into the picker's
 * dimmed free field is seamless.
 */
const UNBORN: SceneFieldState = { layout: 'assembly', reveal: 0 };

export const scenes: SceneDef[] = [
	{
		id: 'co-stakes',
		chapter: 'coldopen',
		anchor: 'coldopen',
		navLabel: 'Cold open: Draw it',
		scrollLength: 120,
		fieldState: UNBORN,
		annotations: Stakes
	},
	{
		id: 'co-draw',
		chapter: 'coldopen',
		scrollLength: 200,
		fieldState: UNBORN,
		annotations: Draw,
		footnote: 'draw-200'
	},
	{
		id: 'co-assembly',
		chapter: 'coldopen',
		scrollLength: ASSEMBLY_SCROLL_VH,
		morphLength: ASSEMBLY_MORPH_VH, // whole-scrub set piece; the tail holds for the title card
		fromState: UNBORN,
		fieldState: { layout: 'assembly', reveal: 1 },
		annotations: Assembly,
		footnote: 'ball-count'
	}
];
