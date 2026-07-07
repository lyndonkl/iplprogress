import type { SceneDef } from '$lib/story/types';
import { readGapScrollLength, captionRevealActive } from '$lib/story/captionReveal.svelte';
import { RAIL_SLOTS, RAIL_DIM, railIndices, eraFlipState, mvbIgniteState } from './data';
import Title from './Title.svelte';
import RailOrient from './RailOrient.svelte';
import OverScrub from './OverScrub.svelte';
import WpaTag from './WpaTag.svelte';
import WorthOrient from './WorthOrient.svelte';
import EraFlip from './EraFlip.svelte';
import ThirdWicket from './ThirdWicket.svelte';
import PriceBoard from './PriceBoard.svelte';
import WicketTag from './WicketTag.svelte';
import Finisher from './Finisher.svelte';
import WplBeat from './WplBeat.svelte';
import MostValuable from './MostValuable.svelte';
import CloseCh5 from './CloseCh5.svelte';

/**
 * CHAPTER 5 — What a Ball Is Worth (storyboard r3b2, scenes C5-1..C5-12 with
 * the hero split C5-6a/C5-6b). REGISTER: THE REPRICING — everything the reader
 * has watched for four chapters had a price the whole time; now the tags go on.
 * Feel before formula: the worm is felt on one real over (the scrub) before any
 * price appears — a release-blocking sequence constraint.
 *
 * BUDGETS (blueprint §2, storyboard §0.5):
 * - Exactly ONE controlling morph: free field → the worth grid (ch5-worth),
 *   returned in ch5-close. The six-ball lift is the §20 overrail (a subset
 *   modifier); the era flip / difference lens / WPL recolor are §19 pricelens
 *   COLOR states over the held grid; the biggest-swings lift is the §21 'wpa'
 *   subset highlight; waffles / board / tag / curves / dots / cards are DOM+SVG.
 * - GSAP scrub budget: this chapter spends set piece #2 of 2 on ch5-scrub (the
 *   famous final over) — the shell's ScrollTrigger scrubs the scene's progress,
 *   and the rail / worm / chips are pure functions of it. No other Ch 5 scene
 *   scrubs anything, and no scene registers a trigger of its own (demand mode).
 *
 * Every on-screen number comes from static/data/scenes/ch5.json (see ./data.ts)
 * — never hardcoded (OWNER-LOCKED). ARTIFACT WINS over teaser copy: defended
 * 73/39 (41/54 matches) · worm opens at 72 in 100 · third wicket 12 → 6 (the
 * "~0.4" probe band is footnote-only) · finisher 55 → 85 (17/31 → 35/41) ·
 * wicket 4.2 → 5.1 (+23%) vs run inflation (+20%) · WPL cohort 9 of 11.
 */

/** stable empty index set (rail inert until scenes/ch5.json lands) */
const NO_RAIL: readonly number[] = [];

/** the shared over-rail descriptor (C5-2 lifts, C5-3 holds, C5-4 releases) */
const RAIL = {
	indices: NO_RAIL,
	slots: RAIL_SLOTS,
	progress: 1,
	dimRest: RAIL_DIM,
	scale: 7,
	lift: 0.35
} as const;

/* per-scene morph fractions used by dynamicState mix ramps (kept in lock-step
   with the SceneDef morphLength/scrollLength pairs below) */
const TW_MORPH = 60 / 220;
const WPL_MORPH = 60 / 340;
const PAYOFF_MORPH = 50 / 200;

const clamp01 = (t: number): number => Math.min(1, Math.max(0, t));

export const scenes: SceneDef[] = [
	{
		id: 'ch5-title',
		chapter: 'ch5',
		anchor: 'ch5',
		navLabel: 'Chapter 5: What a Ball Is Worth',
		scrollLength: 110,
		morphLength: 50,
		// the interlude's close left the free field at dim 0.5; the title dims it a
		// touch more (a luminance lerp, not a morph). Zero numbers on a title.
		fieldState: { layout: 'free', dim: 0.32 },
		annotations: Title
	},
	{
		id: 'ch5-rail',
		chapter: 'ch5',
		scrollLength: 240,
		mobileScrollLength: readGapScrollLength(240),
		morphLength: 130,
		// C5-2: the six deliveries of the 2019 final's last over LIFT out of the
		// field to the rail slots (§20 overrail — the lift rides this scene's
		// entry morph: the previous scene declares no rail, so railProgress lerps
		// 0 → 1 across the morph and the nav's set-piece dimming tracks it). The
		// index set is pipeline-emitted in scenes/ch5.json (data.ts cache — the
		// same fetch the captions bind to, so chips and lift resolve together);
		// the dynamicState injection keeps a stray scroll from ever desyncing it.
		fieldState: { layout: 'free', overrail: { ...RAIL } },
		// reduced motion: the DOM (match card + dormant chips + worm axis) carries
		// the whole beat; the field rests dimmed with no rail flight.
		reducedMotionEndState: { layout: 'free', dim: 0.28 },
		dynamicState: (_progress, held) => ({
			...held,
			overrail: { ...held.overrail!, indices: railIndices() ?? NO_RAIL }
		}),
		annotations: RailOrient,
		footnote: 'ch5-over'
	},
	{
		id: 'ch5-scrub',
		chapter: 'ch5',
		// C5-3: THE SCRUB (set piece #2 of 2 — the chapter's entire scrub budget).
		// The rail holds engaged; the ball-by-ball drama (active chip, outcome,
		// worm segment) is a pure function of scroll progress, scrub-backable.
		scrollLength: 360,
		mobileScrollLength: readGapScrollLength(360),
		morphLength: 30,
		fieldState: { layout: 'free', overrail: { ...RAIL } },
		// reduced motion (mandated fallback): the six-panel sequential strip is
		// the scene's DOM; the field rests dimmed behind it.
		reducedMotionEndState: { layout: 'free', dim: 0.22 },
		dynamicState: (_progress, held) => ({
			...held,
			overrail: { ...held.overrail!, indices: railIndices() ?? NO_RAIL }
		}),
		annotations: OverScrub,
		footnote: 'ch5-over'
	},
	{
		id: 'ch5-wpa',
		chapter: 'ch5',
		scrollLength: 300,
		mobileScrollLength: readGapScrollLength(300),
		morphLength: 110,
		// C5-4 HERO 1: declaring NO overrail returns the six balls to their exact
		// field positions (the reverse leg is free) while the §21 'wpa' highlight
		// lifts the biggest-swing balls in history out of the re-lit field. The
		// 170-189 waffle pair is DOM/SVG. Threshold 0.5 = "swung a match by half
		// or more" (a scene parameter; membership is the shipped wpa.u8). The
		// highlight RELEASES as step 2 arrives (design audit: the lift is step
		// 1's bridge beat and must not compete with the centred waffles) —
		// boost/lift ramp to zero and othersDim to 1, which is pixel-identical
		// to no highlight at all.
		fieldState: {
			layout: 'free',
			dim: 0.55,
			highlight: { class: 'wpa', wpaThreshold: 0.5, lift: 0.14, boost: 0.85, othersDim: 0.3 }
		},
		dynamicState: (progress, held) => {
			const r = 1 - clamp01((progress - 0.34) / 0.1); // gone by step 2 (0.38+)
			return {
				...held,
				highlight: {
					class: 'wpa',
					wpaThreshold: 0.5,
					lift: 0.14 * r,
					boost: 0.85 * r,
					othersDim: 0.3 + 0.7 * (1 - r)
				}
			};
		},
		annotations: WpaTag,
		footnote: 'ch5-wpa'
	},
	{
		id: 'ch5-worth',
		chapter: 'ch5',
		scrollLength: 300,
		mobileScrollLength: readGapScrollLength(300),
		morphLength: 170,
		// C5-5: THE CONTROLLING MORPH — free field → the worth grid (every ball
		// flies to its over × wickets-down cell; brightness = the early era's
		// price, density-normalized by the shell §19.4). The scene feeds the four
		// price tables once (WorthOrient); the highlight releases with the morph.
		fieldState: { layout: 'worth', pricelens: { table: 'early' } },
		annotations: WorthOrient,
		footnote: 'ch5-worth'
	},
	{
		id: 'ch5-flip',
		chapter: 'ch5',
		scrollLength: 360,
		mobileScrollLength: readGapScrollLength(360),
		morphLength: 45,
		// C5-6a HERO 2 (part one): the grid HOLDS; the era flip and the rise lens
		// are pricelens COLOR states driven across the hold by eraFlipState (the
		// same pure scrub math the EraFlip chip/legend read, so field and DOM can
		// never disagree). The dip-to-dark re-light rides the scene dim. The very
		// end pre-swaps the pair to (rise → recent, mix 0) — pixel-identical —
		// so C5-6b's entry releases the lens with one clean mix ramp (§19.3).
		fieldState: { layout: 'worth', pricelens: { from: 'early', table: 'recent', mix: 0 } },
		reducedMotionEndState: {
			layout: 'worth',
			pricelens: { from: 'rise', table: 'recent', mix: 0 }
		},
		dynamicState: (progress, held) => {
			// gap-aligned on mobile (§17.6): the flip / lens advance in the
			// caption steps' clear gaps — the SAME flag EraFlip's chip reads
			const f = eraFlipState(progress, captionRevealActive());
			return { ...held, dim: f.dim, pricelens: f.lens };
		},
		annotations: EraFlip,
		footnote: 'ch5-drift'
	},
	{
		id: 'ch5-thirdwicket',
		chapter: 'ch5',
		scrollLength: 220,
		morphLength: 60,
		// C5-6b HERO 2 (part two): the lens releases (rise → recent, mix ramped up
		// across the entry morph — one uniform lerp, no re-sort); the hero rings +
		// readout card are the scene's DOM, registered to the GL cells.
		fieldState: { layout: 'worth', pricelens: { from: 'rise', table: 'recent', mix: 0 } },
		reducedMotionEndState: { layout: 'worth', pricelens: { table: 'recent' } },
		dynamicState: (progress, held) => ({
			...held,
			pricelens: { ...held.pricelens!, mix: clamp01(progress / TW_MORPH) }
		}),
		annotations: ThirdWicket,
		footnote: 'ch5-drift'
	},
	{
		id: 'ch5-prices',
		chapter: 'ch5',
		scrollLength: 400,
		mobileScrollLength: readGapScrollLength(400),
		morphLength: 45,
		// C5-7 Supporting 1: the price board (DOM tickers + season slider + the
		// one-click full list). The grid dims one stop behind the board; loop
		// stopped between steps.
		fieldState: { layout: 'worth', dim: 0.35, pricelens: { table: 'recent' } },
		annotations: PriceBoard,
		footnote: 'ch5-prices'
	},
	{
		id: 'ch5-wicket',
		chapter: 'ch5',
		scrollLength: 260,
		morphLength: 45,
		// C5-8 Supporting 2: the wicket's counterweight (a single centred price
		// tag + the faster-than-the-tide strip). DOM only.
		fieldState: { layout: 'worth', dim: 0.3, pricelens: { table: 'recent' } },
		annotations: WicketTag,
		footnote: 'ch5-prices'
	},
	{
		id: 'ch5-finisher',
		chapter: 'ch5',
		scrollLength: 320,
		mobileScrollLength: readGapScrollLength(320),
		morphLength: 45,
		// C5-9 Supporting 3: the finisher's office / the moving cliff (2D SVG
		// curves with on-screen cohort counts; the cliff is data-derived).
		fieldState: { layout: 'worth', dim: 0.3, pricelens: { table: 'recent' } },
		annotations: Finisher,
		footnote: 'ch5-finisher'
	},
	{
		id: 'ch5-wpl',
		chapter: 'ch5',
		scrollLength: 340,
		morphLength: 60,
		// C5-10 the WPL beat: the grid recolors to the WPL surface (mix ramped
		// across the entry morph); the mask hatching is the scene's SVG (never a
		// dimness); WPL-family balls brighten a stop while the IPL dims one (a
		// color state, no re-sort).
		fieldState: {
			layout: 'worth',
			dim: 0.85,
			wplDim: 1.5,
			pricelens: { from: 'recent', table: 'wpl', mix: 0 }
		},
		reducedMotionEndState: {
			layout: 'worth',
			dim: 0.85,
			wplDim: 1.5,
			pricelens: { from: 'recent', table: 'wpl', mix: 1 }
		},
		dynamicState: (progress, held) => ({
			...held,
			pricelens: { ...held.pricelens!, mix: clamp01(progress / WPL_MORPH) }
		}),
		annotations: WplBeat,
		footnote: 'ch5-wpl'
	},
	{
		id: 'ch5-payoff',
		chapter: 'ch5',
		scrollLength: 200,
		morphLength: 50,
		// C5-11 payoff: "your team's most valuable ball ever". The reader's team
		// stays ignited (default) on the held grid while the rest dims behind the
		// card; the WPL surface releases back to the recent table on entry. THE
		// ONE BALL ITSELF IGNITES (storyboard C5-11): a single-point §20 overrail
		// whose slot is the ball's own worth-grid cell (set by MostValuable via
		// the data.ts cache), so the real point enlarges essentially in place —
		// dimRest 1 leaves the rest of the field at the scene dim. Reduced
		// motion: no ignite (the static card carries the whole beat).
		fieldState: {
			layout: 'worth',
			dim: 0.3,
			pricelens: { from: 'wpl', table: 'recent', mix: 0 }
		},
		reducedMotionEndState: { layout: 'worth', dim: 0.3, pricelens: { table: 'recent' } },
		dynamicState: (progress, held) => {
			const ig = mvbIgniteState();
			return {
				...held,
				pricelens: { ...held.pricelens!, mix: clamp01(progress / PAYOFF_MORPH) },
				overrail: ig
					? {
							indices: [ig.index],
							slots: [ig.slot],
							progress: clamp01((progress - 0.3) / 0.2),
							dimRest: 1,
							scale: 5,
							lift: 0.05
						}
					: null
			};
		},
		annotations: MostValuable,
		footnote: 'ch5-payoff'
	},
	{
		id: 'ch5-close',
		chapter: 'ch5',
		scrollLength: 120,
		morphLength: 55,
		// C5-12: the worth grid exhales back into the free field — the controlling
		// morph's return leg (the pricelens recolor rides out with the layout
		// share automatically, §19.3). Hands off to the end card.
		fieldState: { layout: 'free' },
		annotations: CloseCh5
	}
];
