import type { SceneDef } from '$lib/story/types';
import Eulogy from './Eulogy.svelte';
import Worms from './Worms.svelte';
import Thinning from './Thinning.svelte';
import RunOutCascade from './RunOutCascade.svelte';
import Gearbox from './Gearbox.svelte';
import Aftershock from './Aftershock.svelte';
import WplClocks from './WplClocks.svelte';
import AnchorCard from './AnchorCard.svelte';
import CloseCh2 from './CloseCh2.svelte';

/**
 * CHAPTER 2 — The Last of the Anchors (storyboard r2a, scenes C2-1..C2-9).
 * ELEGY register: mourn the anchor; the thesis stays celebratory (every
 * extinction beat pairs a loss clause with a gain clause, varied per beat).
 *
 * Morph budget: exactly ONE controlling morph — free field → worm-space
 * (ch2-worms), returned in ch2-close (the same morph's return leg). Everything
 * between keeps layout 'worms'; ch2-runout adds the CONTRACT §14 season-swept
 * run-out CASCADE (a cross-cutting modifier that composes with the haze — it
 * does NOT spend a second controlling morph, exactly like Ch 1's fireworks
 * re-sort), and the thinning / gearbox / aftershock / WPL beats are subset or
 * 2D annotation-plane scenes over the held haze.
 *
 * Every on-screen number comes from static/data/scenes/ch2.json (see ./data.ts)
 * — never hardcoded (OWNER-LOCKED). Where the artifact and the storyboard's
 * teaser copy disagree, the ARTIFACT wins (run-out 4.7 not 4.6, occupancy 39.3
 * not 38.7, tax 1.13→1.30 not 1.22→1.40, WPL run-out 7.1 not 7.0).
 */
export const scenes: SceneDef[] = [
	{
		id: 'ch2-title',
		chapter: 'ch2',
		anchor: 'ch2',
		navLabel: 'Chapter 2: The Last of the Anchors',
		scrollLength: 100,
		morphLength: 45,
		// free field dimmed one stop behind the eulogy; Ch 1→Ch 2 is free→free
		// (no morph — Ch 1 exhaled the wall back to free at its close)
		fieldState: { layout: 'free', dim: 0.35 },
		annotations: Eulogy
	},
	{
		id: 'ch2-worms',
		chapter: 'ch2',
		scrollLength: 340,
		morphLength: 180, // THE controlling morph: free field → worm-space haze
		// the field settles into a low-alpha density haze (x = balls faced 1→60+,
		// y = cumulative innings runs); the par + anchor exemplar worms are SVG on
		// the annotation plane (Worms.svelte), never GL polylines. Reduced motion
		// jump-cuts to the settled haze (default reducedMotionEndState = fieldState).
		fieldState: { layout: 'worms' },
		annotations: Worms,
		footnote: 'anchor-definition'
	},
	{
		id: 'ch2-thinning',
		chapter: 'ch2',
		scrollLength: 320,
		morphLength: 40,
		// worm-space HOLDS (the morph budget is spent). The season-swept thicket +
		// the conservation chart do the work on the annotation plane — no re-sort.
		fieldState: { layout: 'worms' },
		annotations: Thinning,
		footnote: 'anchor-extinction'
	},
	{
		id: 'ch2-runout',
		chapter: 'ch2',
		scrollLength: 280,
		morphLength: 40,
		// HERO #2: the run-out cascade (CONTRACT §14) — a season-swept flash+fall
		// of the run-out subset over the held haze. It composes with 'worms' and
		// spends NO second morph. sweep is a caption STEP (post-morph), so it can't
		// ride the settle-in; drive it from progress via dynamicState.
		fieldState: {
			layout: 'worms',
			cascade: { class: 'runOut', sweep: 0, tint: 1, fall: 0.9, muteIdentity: 1 }
		},
		// reduced motion jump-cuts to the final fallen layout (2026 end state), no
		// red flash (tint 0) — the extinction curve carries the finding statically.
		reducedMotionEndState: {
			layout: 'worms',
			cascade: { class: 'runOut', sweep: 1, tint: 0, fall: 0.9, muteIdentity: 1 }
		},
		// sweep the season pointer 2008→2026 across the hold as the captions scroll;
		// holds fully fallen (sweep 1) through the closing thesis step.
		dynamicState: (progress, held) => ({
			...held,
			cascade: { ...held.cascade!, sweep: Math.min(1, Math.max(0, (progress - 0.2) / (0.62 - 0.2))) }
		}),
		annotations: RunOutCascade,
		footnote: 'runout-extinction'
	},
	{
		id: 'ch2-gears',
		chapter: 'ch2',
		scrollLength: 240,
		morphLength: 45,
		// worm-space dims one stop behind the gearbox illustration; declaring NO
		// cascade lerps the run-outs back (the reverse leg is free). Annotation
		// plane only — no re-sort.
		fieldState: { layout: 'worms', dim: 0.45 },
		annotations: Gearbox,
		footnote: 'gear-shift'
	},
	{
		id: 'ch2-newbatter',
		chapter: 'ch2',
		scrollLength: 240,
		morphLength: 45,
		// the sole coda: the aftershock strip (2D). Field dims far back; loop stopped.
		fieldState: { layout: 'worms', dim: 0.3 },
		annotations: Aftershock,
		footnote: 'new-batter-tax'
	},
	{
		id: 'ch2-wpl',
		chapter: 'ch2',
		scrollLength: 200,
		morphLength: 60,
		// two clocks in one beat: WPL points brighten to full, IPL takes the
		// mirrored one-stop dim (0.55 × 1.82 ≈ 1.0 — the brighten IS the beat,
		// mirroring Ch 1's C1-6). A colour-state change, not a re-sort.
		fieldState: { layout: 'worms', dim: 0.55, wplDim: 1.82 },
		annotations: WplClocks,
		footnote: 'wpl-two-clocks-ch2'
	},
	{
		id: 'ch2-payoff',
		chapter: 'ch2',
		scrollLength: 150,
		morphLength: 50,
		// the reader's team stays ignited (default) in worm-space while the rest
		// dims behind the "your last anchor" card
		fieldState: { layout: 'worms', dim: 0.3 },
		annotations: AnchorCard,
		footnote: 'payoff-ch2'
	},
	{
		id: 'ch2-close',
		chapter: 'ch2',
		scrollLength: 100,
		morphLength: 45,
		// worm-space exhales back into the free field — the controlling morph's
		// return leg, fast (hands off to the end card / Ch 3, unchanged source)
		fieldState: { layout: 'free' },
		annotations: CloseCh2
	}
];
