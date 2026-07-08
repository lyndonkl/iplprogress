import type { SceneDef } from '$lib/story/types';
import { readGapScrollLength } from '$lib/story/captionReveal.svelte';
import Title from './Title.svelte';
import MatchDots from './MatchDots.svelte';
import TossLanes from './TossLanes.svelte';
import ReviewChips from './ReviewChips.svelte';
import SpellStrips from './SpellStrips.svelte';
import Momentum from './Momentum.svelte';
import RequiredRate from './RequiredRate.svelte';
import Wpl from './Wpl.svelte';
import Payoff from './Payoff.svelte';
import CloseCh8 from './CloseCh8.svelte';

/**
 * CHAPTER 8, The Captain's Brain (storyboard r5a, scenes C8-1..C8-10). REGISTER:
 * THE BELIEF AUDIT, it takes the things captains and pundits believe in the
 * analytics era, holds each up to the whole record, and stamps a grade. The shape
 * is the point: four fails and one pass, the pass saved for last so the four fails
 * sting. Picks up the Ch 7 handoff ("learning is what modern franchises do; audit
 * everything else captains learned") and plants Ch 9 ("beliefs churn, but some
 * things refuse to move").
 *
 * BUDGETS (storyboard §0.5 / hard invariants):
 * - Exactly ONE controlling morph: the free field → the 1,331 match-dots
 *   (ch8-matchdots), returned in ch8-close. The `matchSplit` toss-lane lift
 *   (ch8-toss) is a HELD SCALAR over the match-dots (the flowLift analog), and the
 *   988 review chips (ch8-review) are the single subset fly-out, neither spends a
 *   morph. The crossover, the spell mosaics, the momentum panel, the required-rate
 *   curve and the WPL adoption curves are 2D/DOM annotation-plane scenes over the
 *   held (dimmed) dots. No new per-point buffer (the dots binary-search a data
 *   texture in-shader), so the field holds at 14 vertex attributes.
 * - Beat budget: 2 heroes (the toss revolution, the review economics) + 3 supporting
 *   (spell fragmentation, momentum, required rate). Title / match-dots / WPL / payoff
 *   / close are framing, not graded beats.
 *
 * Every on-screen number comes from static/data/scenes/ch8.json (see ./data.ts) -
 * never hardcoded (OWNER-LOCKED; the ARTIFACT wins over teaser copy). Three honest
 * deltas ship straight: the review success rate DEGRADED, the cold-return tax GREW,
 * and momentum is a FAIL with an honest ~1.07 residual. GLOSSARY (locked): fan
 * language on screen, the technical name one click deep in the footnotes. HOUSE
 * FRAMING: the WPL is never "behind", it is a league born into the analytics age.
 */

const clamp01 = (t: number): number => Math.min(1, Math.max(0, t));

/* C8-3: the toss lanes lift (matchSplit 0→1) across steps 1-2; the crossover reads
   land after. C8-4: the review chips fly out (reviews.engage 0→1) across steps 1-2. */
const SPLIT_LO = 0.06;
const SPLIT_HI = 0.3;
const ENGAGE_LO = 0.06;
const ENGAGE_HI = 0.3;

export const scenes: SceneDef[] = [
	{
		id: 'ch8-title',
		chapter: 'ch8',
		anchor: 'ch8',
		navLabel: "Chapter 8: The Captain's Brain",
		scrollLength: 120,
		morphLength: 50,
		// ch7-close left the field at free; the title dims it a touch (a luminance
		// lerp, not a morph). Zero numbers on a title.
		fieldState: { layout: 'free', dim: 0.3 },
		annotations: Title
	},
	{
		id: 'ch8-matchdots',
		chapter: 'ch8',
		scrollLength: 320,
		mobileScrollLength: readGapScrollLength(320),
		morphLength: 240,
		// C8-2: THE CONTROLLING MORPH, free field → the 1,331 match-dots. Every ball
		// condenses to its match centroid (in-shader binary search of the match_bounds
		// data texture, no new buffer). Lands on the neutral centroids (matchSplit 0).
		fieldState: { layout: 'matchdots', matchSplit: 0 },
		reducedMotionEndState: { layout: 'matchdots', matchSplit: 0 },
		annotations: MatchDots
	},
	{
		id: 'ch8-toss',
		chapter: 'ch8',
		scrollLength: 460,
		mobileScrollLength: readGapScrollLength(460),
		morphLength: 60,
		// C8-3 HERO, Belief 1: the toss revolution (FAIL). The held match-dots lift into
		// their two toss lanes, matchSplit 0→1, a HELD SCALAR (the flowLift analog), NOT
		// a second morph, so the field-first river swells straight from the data's toss
		// shift. The belief-reality crossover is the scene's SVG (TossLanes). The split
		// lifts across steps 1-2; the crossover reads land after (dynamicState drives it).
		fromState: { layout: 'matchdots', matchSplit: 0 },
		fieldState: { layout: 'matchdots', matchSplit: 0 },
		reducedMotionEndState: { layout: 'matchdots', matchSplit: 1 },
		dynamicState: (progress, held) => ({
			...held,
			matchSplit: clamp01((progress - SPLIT_LO) / (SPLIT_HI - SPLIT_LO))
		}),
		annotations: TossLanes
	},
	{
		id: 'ch8-review',
		chapter: 'ch8',
		scrollLength: 480,
		mobileScrollLength: readGapScrollLength(480),
		morphLength: 60,
		// C8-4 HERO, Belief 2: the review economics (FAIL). matchSplit returns to 0 (the
		// dots settle back onto their neutral centroids) and the 988 review deliveries fly
		// OUT into per-franchise green/red chip stacks, reviews.engage 0→1, the single
		// subset fly-out (setDismissals/setSparks precedent), spends no morph. The chips
		// fly across steps 1-2 (dynamicState); the reads land after. Membership is fed once
		// by ReviewChips.svelte (field.setReviews).
		fieldState: {
			layout: 'matchdots',
			matchSplit: 0,
			reviews: { engage: 1, tint: 1, othersDim: 0.12 }
		},
		reducedMotionEndState: {
			layout: 'matchdots',
			matchSplit: 0,
			reviews: { engage: 1, tint: 1, othersDim: 0.12 }
		},
		dynamicState: (progress, held) => ({
			...held,
			reviews: {
				...(held.reviews ?? { tint: 1, othersDim: 0.12 }),
				engage: clamp01((progress - ENGAGE_LO) / (ENGAGE_HI - ENGAGE_LO))
			}
		}),
		annotations: ReviewChips
	},
	{
		id: 'ch8-spell',
		chapter: 'ch8',
		scrollLength: 400,
		mobileScrollLength: readGapScrollLength(400),
		morphLength: 45,
		// C8-5 Supporting, Belief 3: spell fragmentation + the cold-return tax (FAIL).
		// The dots dim to a backdrop; the scene is authored SVG/DOM (fused-bar mosaics).
		// Declaring no `reviews` lets the C8-4 chips settle back (engage → 0, reversible).
		fieldState: { layout: 'matchdots', dim: 0.28 },
		reducedMotionEndState: { layout: 'matchdots', dim: 0.28 },
		annotations: SpellStrips
	},
	{
		id: 'ch8-momentum',
		chapter: 'ch8',
		scrollLength: 460,
		mobileScrollLength: readGapScrollLength(460),
		morphLength: 45,
		// C8-6 Supporting, Belief 4: momentum (FAIL with an honest residual). The dots
		// dim; the scene is the needle-vs-shuffled-cricket panel (on-demand render, no
		// rAF loop). The wicket half collapses, the hitting half is nearly all good
		// batters batting, with a thin real sliver that HELD steady.
		fieldState: { layout: 'matchdots', dim: 0.3 },
		reducedMotionEndState: { layout: 'matchdots', dim: 0.3 },
		annotations: Momentum
	},
	{
		id: 'ch8-required',
		chapter: 'ch8',
		scrollLength: 400,
		mobileScrollLength: readGapScrollLength(400),
		morphLength: 45,
		// C8-7 Supporting, Belief 5: required-rate responsiveness (PASS, saved for last).
		// The dots dim; the scene is the chase run-rate curve, pinned to two contrasting
		// eras (2008-10 vs 2023-26). The up-slope-to-front-load flip is the one belief
		// the record actually backs, with an honest caveat that it is not "wins more".
		fieldState: { layout: 'matchdots', dim: 0.3 },
		reducedMotionEndState: { layout: 'matchdots', dim: 0.3 },
		annotations: RequiredRate
	},
	{
		id: 'ch8-wpl',
		chapter: 'ch8',
		scrollLength: 400,
		mobileScrollLength: readGapScrollLength(400),
		morphLength: 45,
		// C8-8 the WPL doctrine transmission (structural). The dots dim; the WPL's 88
		// match-dots are circled in teal inside the same cloud and its toss adoption
		// curve draws over them. A league born into the analytics age, never "behind".
		fieldState: { layout: 'matchdots', dim: 0.3 },
		reducedMotionEndState: { layout: 'matchdots', dim: 0.3 },
		annotations: Wpl
	},
	{
		id: 'ch8-payoff',
		chapter: 'ch8',
		scrollLength: 240,
		morphLength: 45,
		// C8-9 the per-franchise payoff ("your captains' report card"). The dimmed dots
		// idle behind the DOM card with the reader's matches lit. All 16 variants come
		// from ch8.json payoff.variants (card == artifact), with the on-card guard note.
		fieldState: { layout: 'matchdots', dim: 0.3 },
		reducedMotionEndState: { layout: 'matchdots', dim: 0.3 },
		annotations: Payoff
	},
	{
		id: 'ch8-close',
		chapter: 'ch8',
		scrollLength: 140,
		morphLength: 60,
		// C8-10 chapter close: the match-dots exhale back into the free field (the
		// controlling morph's reverse leg), totalling the report card and handing to
		// Chapter 9 ("some things refuse to move").
		fieldState: { layout: 'free' },
		annotations: CloseCh8
	}
];
