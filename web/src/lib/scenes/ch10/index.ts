import type { SceneDef, SceneFieldState } from '$lib/story/types';
import { readGapScrollLength } from '$lib/story/captionReveal.svelte';
import Title from './Title.svelte';
import Ribbon from './Ribbon.svelte';
import Seismograph from './Seismograph.svelte';
import FaultMap from './FaultMap.svelte';
import VerdictCard from './VerdictCard.svelte';
import Teleporter from './Teleporter.svelte';
import ConvergenceClock from './ConvergenceClock.svelte';
import PayoffCard from './PayoffCard.svelte';
import CloseCard from './CloseCard.svelte';

/**
 * CHAPTER 10, The Era Machine (storyboard r6a, scenes C10-1..C10-9). THE FINALE.
 * REGISTER: the synthesis, case closed honestly. It stops narrating eras and hands
 * the pen to the data: the segmentation draws its own fault lines, the modern era
 * is a STACK of staggered revolutions, the 2023 mystery (posed in Ch 4, partially
 * answered in Ch 7) is closed as three suspects each guilty on a different count,
 * the Player Teleporter re-quotes any innings into any era, the convergence clock
 * points the machine forward, and then the ribbon exhales back into the cold-open
 * free field, so the piece ends where it began, and the sandbox rises. There is no
 * Chapter 11.
 *
 * BUDGETS (storyboard §0.5 / hard invariants):
 * - Exactly ONE controlling morph: the free field -> the chronological ribbon
 *   (ch10-ribbon, free -> `ribbon`), returned in ch10-close (`ribbon` -> free, the
 *   cold-open scatter, byte-identical to entry). The ribbon is a PURE FUNCTION of
 *   position.x (the chronological point index) + the existing uInvN, so it adds NO
 *   new per-point buffer and NO 15th attribute; the field STAYS at 14. `ribbonReveal`
 *   rides the morph; three teleport scalars default inert (§27) so every prior
 *   release renders byte-identically.
 * - The fault-line CRACKS + era-bands + strictness dial (C10-3), the seismograph
 *   strip (C10-3), the fault-map subway (C10-4), the verdict card (C10-5), the two-
 *   machine Teleporter (C10-6), the convergence fans (C10-7) and the payoff (C10-8)
 *   are all scene-authored SVG/DOM over the held (dimmed) ribbon; the field draws no
 *   crack, and the strictness dial is a PRECOMPUTED lookup into scenes/ch10.json,
 *   never a live re-fit.
 * - Beat budget: 1 hero (the seismograph) + 3 supporting (the fault map, the bridge
 *   verdict, the Teleporter). Title / ribbon-orient / convergence / payoff / close
 *   are framing, not counted beats.
 *
 * Every on-screen number comes from static/data/scenes/ch10.json (see ./data.ts) -
 * never hardcoded (OWNER-LOCKED; the ARTIFACT wins over teaser copy). Six honest
 * deltas ship straight: sixes broke 2014 then 2018 (not one clean 2018), about two-
 * thirds of the 2023-24 jump was new personnel (not three-quarters), the naive
 * teleport ceiling is about 224 (not 228), "how far above his own era" is a percent-
 * above-par gap and NEVER a z-score, and the WPL six-hitting is off the clock (never
 * "behind"). GLOSSARY: fan language on screen, the technical name one click deep.
 */

const clamp01 = (t: number): number => Math.min(1, Math.max(0, t));

/* the held ribbon, bright (C10-2 end): the whole history drawn, full luminance. */
const RIBBON_HELD: SceneFieldState = { layout: 'ribbon', ribbonReveal: 1, dim: 1 };

/* the held ribbon dimmed a stop so the cracks + the seismograph strip pop (C10-3). */
const RIBBON_SEISMO: SceneFieldState = { layout: 'ribbon', ribbonReveal: 1, dim: 0.6 };

/* the held ribbon dimmed to a quiet backdrop behind a 2D exhibit (C10-4..C10-8). */
const RIBBON_DIM: SceneFieldState = { layout: 'ribbon', ribbonReveal: 1, dim: 0.2 };

/* the held ribbon held mid-dim for the Teleporter (the picked player would read
   against a legible band; the field subset lift is not engaged, see Teleporter.svelte). */
const RIBBON_TELE: SceneFieldState = { layout: 'ribbon', ribbonReveal: 1, dim: 0.6 };

export const scenes: SceneDef[] = [
	{
		id: 'ch10-title',
		chapter: 'ch10',
		anchor: 'ch10',
		navLabel: 'Chapter 10: The Era Machine',
		scrollLength: 110,
		morphLength: 0,
		// C10-1: inherits `free` from Ch 9's C9-9 close (no morph at entry); a gentle
		// luminance hold, no numbers on a title.
		fromState: { layout: 'free' },
		fieldState: { layout: 'free', dim: 1 },
		reducedMotionEndState: { layout: 'free' },
		annotations: Title
	},
	{
		id: 'ch10-ribbon',
		chapter: 'ch10',
		scrollLength: 240,
		mobileScrollLength: readGapScrollLength(240),
		morphLength: 240,
		// C10-2, THE CONTROLLING MORPH: free field -> the chronological ribbon. The
		// 316,199 balls sort into one horizontal band ordered left to right by when they
		// were bowled. `ribbonReveal` rides the whole-scene scrub; the tail holds.
		fromState: { layout: 'free', ribbonReveal: 0 },
		fieldState: RIBBON_HELD,
		reducedMotionEndState: { layout: 'ribbon', ribbonReveal: 1 },
		dynamicState: (progress, held): SceneFieldState => ({
			...held,
			ribbonReveal: clamp01(progress / 0.85)
		}),
		annotations: Ribbon,
		footnote: 'ch10-seismo'
	},
	{
		id: 'ch10-seismo',
		chapter: 'ch10',
		scrollLength: 220,
		mobileScrollLength: readGapScrollLength(220),
		morphLength: 45,
		// C10-3, HERO: the Seismograph. Holds `ribbon` from C10-2 and dims a stop; the
		// movement is the cracks falling and the strictness dial merging, both scene-
		// authored SVG (the field draws no crack).
		fromState: RIBBON_HELD,
		fieldState: RIBBON_SEISMO,
		reducedMotionEndState: RIBBON_SEISMO,
		annotations: Seismograph,
		footnote: 'ch10-seismo'
	},
	{
		id: 'ch10-faultmap',
		chapter: 'ch10',
		scrollLength: 170,
		mobileScrollLength: readGapScrollLength(170),
		morphLength: 45,
		// C10-4, SUPPORTING 1: the Fault Map. The ribbon dims to a quiet backdrop; the
		// subway map is DOM/SVG, the reveal tied to the scroll step.
		fromState: RIBBON_SEISMO,
		fieldState: RIBBON_DIM,
		reducedMotionEndState: RIBBON_DIM,
		annotations: FaultMap,
		footnote: 'ch10-seismo'
	},
	{
		id: 'ch10-bridge',
		chapter: 'ch10',
		scrollLength: 190,
		mobileScrollLength: readGapScrollLength(190),
		morphLength: 45,
		// C10-5, SUPPORTING 2: the Bridge-Player Verdict (the 2023 mystery, closed). The
		// shift-share two-way bar and the three-suspect verdict card are DOM/SVG.
		fieldState: RIBBON_DIM,
		reducedMotionEndState: RIBBON_DIM,
		annotations: VerdictCard,
		footnote: 'ch10-bridge'
	},
	{
		id: 'ch10-teleporter',
		chapter: 'ch10',
		scrollLength: 210,
		mobileScrollLength: readGapScrollLength(210),
		morphLength: 45,
		// C10-6, SUPPORTING 3: the Player Teleporter. TWO hard-separated machines, never
		// co-displayed (Machine A on one strike-rate axis, Machine B the rank-vs-era bar-
		// swap). The field subset lift is NOT engaged (scenes/ch10.json carries no per-
		// delivery indices; the 2D machines are the load-bearing exhibit).
		fromState: RIBBON_DIM,
		fieldState: RIBBON_TELE,
		reducedMotionEndState: RIBBON_TELE,
		annotations: Teleporter,
		footnote: 'ch10-teleporter'
	},
	{
		id: 'ch10-convergence',
		chapter: 'ch10',
		scrollLength: 150,
		mobileScrollLength: readGapScrollLength(150),
		morphLength: 45,
		// C10-7, the WPL thread + the Convergence Clock. The ribbon dims; the WPL keeps
		// its teal identity glow; the three convergence small multiples are DOM/SVG.
		fromState: RIBBON_TELE,
		fieldState: RIBBON_DIM,
		reducedMotionEndState: RIBBON_DIM,
		annotations: ConvergenceClock,
		footnote: 'ch10-convergence'
	},
	{
		id: 'ch10-payoff',
		chapter: 'ch10',
		scrollLength: 90,
		morphLength: 45,
		// C10-8, the per-franchise payoff ("your adapters"). The dimmed ribbon idles
		// behind the DOM card with the reader's team lit. All 16 variants come from
		// ch10.json payoff.variants (card == artifact).
		fieldState: RIBBON_DIM,
		reducedMotionEndState: RIBBON_DIM,
		annotations: PayoffCard,
		footnote: 'ch10-payoff'
	},
	{
		id: 'ch10-close',
		chapter: 'ch10',
		scrollLength: 130,
		morphLength: 110,
		// C10-9, the finale close: the ribbon exhales back into the free field (the
		// controlling morph's reverse leg), totalling the piece and handing to the
		// sandbox. The free scatter is byte-identical to entry (the piece ends where it
		// began). NO next-chapter tease.
		fromState: RIBBON_DIM,
		fieldState: { layout: 'free', dim: 1 },
		reducedMotionEndState: { layout: 'free' },
		dynamicState: (progress, held): SceneFieldState => ({
			...held,
			ribbonReveal: 1 - clamp01(progress / 0.7)
		}),
		annotations: CloseCard
	}
];
