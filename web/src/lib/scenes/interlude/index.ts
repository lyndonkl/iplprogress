import type { SceneDef } from '$lib/story/types';
import Pause from './Pause.svelte';
import NetSession from './NetSession.svelte';
import Close from './Close.svelte';

/**
 * THE INTERLUDE — The Net Session (storyboard r3b1-netsession-storyboard.md).
 * The two-dial teaching widget between Chapter 4 (The Rising Tide) and Chapter 5
 * (What a Ball Is Worth, in build). It is NOT a chapter: no beat budget, no hero
 * metric, no controlling morph, no team payoff. It is one pause and one machine.
 *
 * MORPH BUDGET: the interlude spends ZERO morphs. There is no new layout — every
 * scene HOLDS the existing `free` scatter under a heavy dim (the resting
 * starfield), with the reader's franchise still faintly lit for identity. Per the
 * shell's demand-mode contract (CONTRACT §1: "holding = zero renders"), once that
 * dim settles the render loop STOPS and the GPU is idle. Ch 4's close (C4-12)
 * already exhaled `tide → free`, so entering the interlude is a settle (a dim-down
 * lerp), not a set piece; the nav's set-piece dimming does not engage (no layout
 * change, no reveal scrub).
 *
 * DEMAND-MODE INVARIANT: none of these components touch `field` — the starfield
 * stays frozen behind the glass while the reader drags the widget.
 *
 * Every on-screen figure binds to static/data/scenes/interlude.json (see
 * ./data.ts) — never hardcoded. The nav flip (SOON → live) is automatic: the
 * first scene declares `navLabel`, and 'Interlude: The Net Session' is removed
 * from FUTURE_CHAPTERS in navplan.ts.
 */

/** The resting starfield dim — heavy, so the field reads as paused (storyboard §0.4). */
const STARFIELD_DIM = 0.18;

export const scenes: SceneDef[] = [
	{
		id: 'interlude',
		chapter: 'interlude',
		anchor: 'interlude',
		navLabel: 'Interlude: The Net Session',
		scrollLength: 200,
		// the field DIMS in: free (dim 1 from Ch 4's close) → the resting starfield,
		// then holds (loop stops). A luminance lerp, not a layout morph.
		morphLength: 90,
		fieldState: { layout: 'free', dim: STARFIELD_DIM, teamIgnite: true },
		annotations: Pause
	},
	{
		id: 'interlude-widget',
		chapter: 'interlude',
		// long dwell: the widget is pinned and the reader drags it; the scroll only
		// advances the coaching prompts (IN-2 orient → IN-3 feel → the ask → IN-5 WPL).
		scrollLength: 560,
		morphLength: 40, // same dim as IN-1 → effectively no morph; loop stays stopped
		fieldState: { layout: 'free', dim: STARFIELD_DIM, teamIgnite: true },
		annotations: NetSession,
		footnote: 'netsession'
	},
	{
		id: 'interlude-close',
		chapter: 'interlude',
		scrollLength: 220,
		// the starfield un-dims a touch on the way out (foreshadows the field's
		// return in Ch 5); still demand-mode, still no morph — a luminance lerp only.
		morphLength: 120,
		fieldState: { layout: 'free', dim: 0.5, teamIgnite: true },
		annotations: Close,
		footnote: 'netsession'
	}
];
