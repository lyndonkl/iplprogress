import type { SceneDef } from '$lib/story/types';
import { readGapScrollLength } from '$lib/story/captionReveal.svelte';
import { phaseGlide } from './data';
import Title from './Title.svelte';
import Constellation from './Constellation.svelte';
import TwoTruths from './TwoTruths.svelte';
import PhaseToggle from './PhaseToggle.svelte';
import MaturityClock from './MaturityClock.svelte';
import RunDna from './RunDna.svelte';
import Stumping from './Stumping.svelte';
import PhotoFinish from './PhotoFinish.svelte';
import Payoff from './Payoff.svelte';
import CloseCh6 from './CloseCh6.svelte';

/**
 * CHAPTER 6 — Two Dialects (storyboard r4a, scenes C6-1..C6-10). REGISTER: THE
 * WIDENING — the lens opens to a second league, and the reader's frame turns from
 * "how far behind" to "a different dialect of the same game, beside the path".
 *
 * BUDGETS (blueprint §2 / §3):
 * - Exactly ONE controlling morph: free field → the season constellation
 *   (ch6-constellation), returned in ch6-close. The two-truths beat, the phase
 *   toggle (a §22 star-table swap over the HELD map — NOT a re-sort, NOT a second
 *   morph), the maturity clock, the run-DNA helix, the stumping signature, the
 *   photo-finish bars and the payoff all COMPOSE with the held constellation.
 * - Beat budget: HERO(S) + max 3 supporting. Heroes: the constellation (orient +
 *   two-truths + phase toggle — one device across three beats) and the Maturity
 *   Clock. Supporting: Run DNA, Stumping Signature, Photo-Finish. Title / payoff /
 *   close are structural, not beats.
 * - NEVER a live re-embed: the star tables ship precomputed + Procrustes-aligned
 *   (Constellation.svelte feeds them VERBATIM via setStarTables — CONTRACT §22.2).
 *
 * Every on-screen number comes from static/data/scenes/ch6.json (see ./data.ts)
 * — never hardcoded (OWNER-LOCKED; the ARTIFACT wins over teaser copy). HOUSE
 * FRAMING (locked): the WPL is never "behind" — it sits BESIDE the IPL path.
 */

const clamp01 = (t: number): number => Math.min(1, Math.max(0, t));

export const scenes: SceneDef[] = [
	{
		id: 'ch6-title',
		chapter: 'ch6',
		anchor: 'ch6',
		navLabel: 'Chapter 6: Two Dialects',
		scrollLength: 110,
		morphLength: 50,
		// ch5-close left the field at free; the title dims it a touch (a luminance
		// lerp, not a morph). Zero numbers on a title.
		fieldState: { layout: 'free', dim: 0.3 },
		annotations: Title
	},
	{
		id: 'ch6-constellation',
		chapter: 'ch6',
		scrollLength: 340,
		mobileScrollLength: readGapScrollLength(340),
		morphLength: 150,
		// C6-2: THE CONTROLLING MORPH — free field → the 23 season-stars (every ball
		// flies to its group's star + jitter, in-shader off group_ids.u16; no new
		// buffer). Constellation.svelte feeds the four Procrustes-aligned star tables
		// ONCE (setStarTables — VERBATIM, never re-embedded) and draws the worm +
		// threads. Phase omitted → the 'all' master map.
		fieldState: { layout: 'constellation' },
		reducedMotionEndState: { layout: 'constellation' },
		annotations: Constellation,
		footnote: 'ch6-constellation'
	},
	{
		id: 'ch6-twotruths',
		chapter: 'ch6',
		scrollLength: 360,
		mobileScrollLength: readGapScrollLength(360),
		morphLength: 40,
		// C6-3: the two-truths money shot. The 'all' map HOLDS (no re-sort). The WPL
		// cluster dims while the IPL path is oriented, then BRIGHTENS on the run-rate
		// reveal (wplDim driven up across the hold via dynamicState — a post-morph
		// luminance change, like the C1-2 heat beat). The rate-twin gold connector +
		// the two-truths panel are TwoTruths.svelte's annotation plane.
		fieldState: { layout: 'constellation', wplDim: 0.55 },
		reducedMotionEndState: { layout: 'constellation', wplDim: 1.6 },
		dynamicState: (progress, held) => {
			// brighten the WPL as step 3 (the run-rate reveal, progress ≥ 0.5) lands
			const t = clamp01((progress - 0.5) / 0.12);
			return { ...held, wplDim: 0.55 + (1.6 - 0.55) * t };
		},
		annotations: TwoTruths,
		footnote: 'ch6-constellation'
	},
	{
		id: 'ch6-phase',
		chapter: 'ch6',
		scrollLength: 440,
		mobileScrollLength: readGapScrollLength(440),
		morphLength: 30,
		// C6-4: the phase toggle (§22.3 — a star-table swap over the HELD map, NOT a
		// re-sort, NOT a second morph). phaseGlide cycles all → the first six → the
		// middle → the death overs → back to all; the 23 star centres lerp between
		// the precomputed, Procrustes-aligned per-phase tables, so the WPL glides
		// coherently and never crosses the men's worm. The glide is a pure function
		// of progress (shared with PhaseToggle.svelte's chip), so a stray scroll
		// re-application can never revert the toggle (the §12.2 orchestrator caveat).
		fieldState: { layout: 'constellation', phase: { table: 'all' } },
		reducedMotionEndState: { layout: 'constellation', phase: { table: 'all' } },
		dynamicState: (progress, held) => {
			const g = phaseGlide(progress);
			return { ...held, phase: { from: g.from, table: g.table, mix: g.mix } };
		},
		annotations: PhaseToggle,
		footnote: 'ch6-phase'
	},
	{
		id: 'ch6-maturity',
		chapter: 'ch6',
		scrollLength: 380,
		mobileScrollLength: readGapScrollLength(380),
		morphLength: 45,
		// C6-5 HERO 2: the League Maturity Clock. A 2D dual-dial over the dimmed held
		// constellation (no second morph). The dial is a league-year stepper
		// (interaction adds depth); the year-4 = year-15 point lands in the caption.
		fieldState: { layout: 'constellation', dim: 0.26, phase: { table: 'all' } },
		annotations: MaturityClock,
		footnote: 'ch6-maturity'
	},
	{
		id: 'ch6-dna',
		chapter: 'ch6',
		scrollLength: 320,
		mobileScrollLength: readGapScrollLength(320),
		morphLength: 45,
		// C6-6 Supporting 1: the Run DNA composition (four-led vs six-led). 2D bars
		// over the dimmed constellation.
		fieldState: { layout: 'constellation', dim: 0.22, phase: { table: 'all' } },
		annotations: RunDna,
		footnote: 'ch6-dna'
	},
	{
		id: 'ch6-stumping',
		chapter: 'ch6',
		scrollLength: 320,
		mobileScrollLength: readGapScrollLength(320),
		morphLength: 45,
		// C6-7 Supporting 2: the Stumping Signature (the Ch 3 tease, paid off). 2D
		// per-season chart over the dimmed constellation.
		fieldState: { layout: 'constellation', dim: 0.22, phase: { table: 'all' } },
		annotations: Stumping,
		footnote: 'ch6-stumping'
	},
	{
		id: 'ch6-photofinish',
		chapter: 'ch6',
		scrollLength: 300,
		mobileScrollLength: readGapScrollLength(300),
		morphLength: 45,
		// C6-8 Supporting 3: the Photo-Finish rate (tightest league). 2D bars over
		// the dimmed constellation.
		fieldState: { layout: 'constellation', dim: 0.22, phase: { table: 'all' } },
		annotations: PhotoFinish,
		footnote: 'ch6-photofinish'
	},
	{
		id: 'ch6-payoff',
		chapter: 'ch6',
		scrollLength: 240,
		morphLength: 55,
		// C6-9 payoff: your two dialects (the sister-franchise card). The
		// constellation holds dimmed behind the card; for a WPL picker the nearest
		// IPL style-star is ringed on the map (Payoff.svelte, Starfield faint). All
		// 16 variants come from ch6.json payoff.variants (card == artifact).
		fieldState: { layout: 'constellation', dim: 0.32, phase: { table: 'all' } },
		annotations: Payoff,
		footnote: 'ch6-payoff'
	},
	{
		id: 'ch6-close',
		chapter: 'ch6',
		scrollLength: 130,
		morphLength: 60,
		// C6-10: the constellation exhales back into the free field — the controlling
		// morph's return leg. Hands off to Chapter 7 (the WPL as the control arm).
		fieldState: { layout: 'free' },
		annotations: CloseCh6
	}
];
