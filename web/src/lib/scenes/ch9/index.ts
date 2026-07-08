import type { SceneDef, SceneFieldState } from '$lib/story/types';
import { readGapScrollLength } from '$lib/story/captionReveal.svelte';
import Title from './Title.svelte';
import DuelWebOrient from './DuelWebOrient.svelte';
import DuelNetwork from './DuelNetwork.svelte';
import AuctionHeartbeat from './AuctionHeartbeat.svelte';
import Synthesis from './Synthesis.svelte';
import LoyaltySpectrum from './LoyaltySpectrum.svelte';
import WplThread from './WplThread.svelte';
import PayoffCard from './PayoffCard.svelte';
import CloseCard from './CloseCard.svelte';

/**
 * CHAPTER 9, The Living League (storyboard r5b, scenes C9-1..C9-9). REGISTER:
 * PERSISTENCE THROUGH CHURN, the celebratory companion to Chapter 2's elegy. It
 * holds two facts side by side, never a cause: institutions (squads, careers) churn
 * on a clock, and the human rivalries persist through it. Picks up the Ch 8 handoff
 * ("beliefs churn, but some things refuse to move") and plants Ch 10 ("was 2023 a
 * genuinely new era, or a louder version of the old game").
 *
 * BUDGETS (storyboard §0.5 / hard invariants):
 * - Exactly ONE controlling morph: the free field -> the duel web (ch9-web, free
 *   -> `duelweb`), returned in ch9-close. Four HELD SCALARS ride over it, all
 *   default inert so every prior release renders byte-identically (CONTRACT §26):
 *   `duelReveal` (the web draw), `duelDominance` (the red/blue "who came out on
 *   top" hue), `duelDustDim` (sink the 236,821 dust balls so the strands pop), and
 *   `strandRecede` (recede every non-focus strand's knot to neutral so only the
 *   argued rivalries carry chroma). None re-sorts the field.
 * - The auction heartbeat, the loyalty spectrum, the player-to-player strands, the
 *   tap-a-duel replay strip, the season scrub and the WPL sub-web are all 2D/DOM
 *   annotation-plane scenes over the held (dimmed) web; the field draws no lines
 *   and adds no per-point buffer beyond the pairing DATA TEXTURE, so it holds at
 *   14 vertex attributes.
 * - Beat budget: 2 heroes (the duel network, the auction heartbeat) + 1 supporting
 *   (the loyalty spectrum). Title / web-orient / synthesis / WPL / payoff / close
 *   are framing, not counted beats.
 *
 * Every on-screen number comes from static/data/scenes/ch9.json (see ./data.ts) -
 * never hardcoded (OWNER-LOCKED; the ARTIFACT wins over teaser copy). Three honest
 * deltas ship straight: 232 duels ran 8+ seasons (not 235), one-club players
 * roughly halved to about 12 in 100 (not 28 to 15), and the mega-auction trough
 * averages 0.186. GLOSSARY (locked): fan language on screen, the technical name one
 * click deep. HOUSE FRAMING: the WPL is never "behind", it is a young league whose
 * fabric is forming fast.
 */

const clamp01 = (t: number): number => Math.min(1, Math.max(0, t));
const mix = (a: number, b: number, t: number): number => a + (b - a) * clamp01(t);

/* the web AS TAUGHT (C9-2 end): drawn, coloured, dust dimmed to a haze, strands
   only lightly receded so the whole web reads while it is being oriented. */
const WEB_TAUGHT: SceneFieldState = {
	layout: 'duelweb',
	duelReveal: 1,
	duelDominance: 1,
	duelDustDim: 0.35,
	strandRecede: 0.4
};

/* the web AS ARGUED (C9-3 end): the dust nearly gone, the short duels receded to
   gray so the long strands own the frame. */
const WEB_ARGUED: SceneFieldState = {
	layout: 'duelweb',
	duelReveal: 1,
	duelDominance: 1,
	duelDustDim: 0.12,
	strandRecede: 1
};

/* the web dimmed to a quiet backdrop behind a 2D exhibit (heartbeat / loyalty /
   WPL / payoff). */
const WEB_DIM: SceneFieldState = { ...WEB_ARGUED, dim: 0.2 };

/* the web brightened back for the synthesis scrub, strands relaxed so the whole
   web reads as it re-draws year by year. */
const WEB_SYNTH: SceneFieldState = {
	layout: 'duelweb',
	duelReveal: 1,
	duelDominance: 1,
	duelDustDim: 0.12,
	strandRecede: 0.4,
	dim: 1
};

/* C9-3: the dust sinks further and the short duels recede over the first ~third */
const ARGUE_LO = 0.06;
const ARGUE_HI = 0.36;

export const scenes: SceneDef[] = [
	{
		id: 'ch9-title',
		chapter: 'ch9',
		anchor: 'ch9',
		navLabel: 'Chapter 9: The Living League',
		scrollLength: 110,
		morphLength: 50,
		// C9-1: inherits `free` from Ch 8's close (no morph at entry); a gentle
		// luminance settle, no numbers on a title.
		fieldState: { layout: 'free', dim: 1 },
		annotations: Title
	},
	{
		id: 'ch9-web',
		chapter: 'ch9',
		scrollLength: 240,
		mobileScrollLength: readGapScrollLength(240),
		morphLength: 240,
		// C9-2, THE CONTROLLING MORPH: free field -> the duel web. Every ball flies to
		// its rivalry's strand or sinks into the dust; the dust dims, the strands take
		// their red/blue hue, and the web relaxes into place across the whole scrub.
		// The reveal / dominance / dust-dim / strand-recede all ride the from->to morph.
		fromState: { layout: 'free', duelReveal: 0, duelDominance: 0, duelDustDim: 1, strandRecede: 1 },
		fieldState: WEB_TAUGHT,
		reducedMotionEndState: WEB_TAUGHT,
		annotations: DuelWebOrient,
		footnote: 'ch9-duel'
	},
	{
		id: 'ch9-duels',
		chapter: 'ch9',
		scrollLength: 200,
		mobileScrollLength: readGapScrollLength(200),
		morphLength: 40,
		// C9-3, HERO 1: the Duel Network. The dust sinks the rest of the way and the
		// ~1,459 short duels recede to gray (dynamicState drives duelDustDim/strandRecede
		// across the first third), leaving the 232 long strands and the Kohli-Jadeja hero.
		fieldState: WEB_TAUGHT,
		reducedMotionEndState: WEB_ARGUED,
		dynamicState: (progress, held): SceneFieldState => ({
			...held,
			duelDustDim: mix(0.35, 0.12, clamp01((progress - ARGUE_LO) / (ARGUE_HI - ARGUE_LO))),
			strandRecede: mix(0.4, 1, clamp01((progress - ARGUE_LO) / (ARGUE_HI - ARGUE_LO)))
		}),
		annotations: DuelNetwork,
		footnote: 'ch9-duel'
	},
	{
		id: 'ch9-heartbeat',
		chapter: 'ch9',
		scrollLength: 190,
		mobileScrollLength: readGapScrollLength(190),
		morphLength: 45,
		// C9-4, HERO 2: the Auction Heartbeat. The web dims to a backdrop; the EKG is a
		// 2D SVG scene (particles carry no meaning in an EKG), so no morph beyond `dim`.
		fieldState: WEB_DIM,
		reducedMotionEndState: WEB_DIM,
		annotations: AuctionHeartbeat,
		footnote: 'ch9-heartbeat'
	},
	{
		id: 'ch9-synthesis',
		chapter: 'ch9',
		scrollLength: 180,
		mobileScrollLength: readGapScrollLength(180),
		morphLength: 45,
		// C9-5, the SYNTHESIS: the web brightens back and the season scrub (scene-authored
		// SVG) re-draws it year by year across the five resets. The web positions are
		// fixed, so this is a luminance restore, not a re-sort.
		fieldState: WEB_SYNTH,
		reducedMotionEndState: WEB_SYNTH,
		annotations: Synthesis,
		footnote: 'ch9-heartbeat'
	},
	{
		id: 'ch9-loyalty',
		chapter: 'ch9',
		scrollLength: 150,
		mobileScrollLength: readGapScrollLength(150),
		morphLength: 45,
		// C9-6, SUPPORTING 1: the Loyalty Spectrum. The web dims; the one-club line is a
		// 2D SVG scene on a 0-based axis, with Finch a separate callout off the line.
		fieldState: WEB_DIM,
		reducedMotionEndState: WEB_DIM,
		annotations: LoyaltySpectrum,
		footnote: 'ch9-loyalty'
	},
	{
		id: 'ch9-wpl',
		chapter: 'ch9',
		scrollLength: 140,
		morphLength: 45,
		// C9-7, the WPL thread. The web dims; the WPL sub-web foregrounds via SVG and its
		// own heartbeat draws. A young league whose fabric is forming fast, never "behind".
		fieldState: WEB_DIM,
		reducedMotionEndState: WEB_DIM,
		annotations: WplThread,
		footnote: 'ch9-duel'
	},
	{
		id: 'ch9-payoff',
		chapter: 'ch9',
		scrollLength: 90,
		morphLength: 45,
		// C9-8, the per-franchise payoff ("your team through the churn"). The dimmed web
		// idles behind the DOM card with the reader's own rivalry strand highlighted. All
		// 16 variants come from ch9.json payoff.variants (card == artifact).
		fieldState: WEB_DIM,
		reducedMotionEndState: WEB_DIM,
		annotations: PayoffCard,
		footnote: 'ch9-payoff'
	},
	{
		id: 'ch9-close',
		chapter: 'ch9',
		scrollLength: 110,
		morphLength: 110,
		// C9-9, chapter close: the web exhales back into the free field (the controlling
		// morph's reverse leg), totalling the chapter and handing to Chapter 10 (The Era
		// Machine). The end card's scatter is byte-identical to entry.
		fromState: WEB_DIM,
		fieldState: { layout: 'free', dim: 1 },
		reducedMotionEndState: { layout: 'free' },
		dynamicState: (progress, held): SceneFieldState => ({
			...held,
			duelReveal: 1 - clamp01(progress)
		}),
		annotations: CloseCard
	}
];
