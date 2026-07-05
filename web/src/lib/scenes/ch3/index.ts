import type { SceneDef } from '$lib/story/types';
import { retreatState } from './data';
import Title from './Title.svelte';
import Frontier from './Frontier.svelte';
import Retreat from './Retreat.svelte';
import DismissalRivers from './DismissalRivers.svelte';
import DotGrid from './DotGrid.svelte';
import WideTax from './WideTax.svelte';
import WplBeat from './WplBeat.svelte';
import GravityDefier from './GravityDefier.svelte';
import CloseCh3 from './CloseCh3.svelte';

/**
 * CHAPTER 3 — The Counterrevolution (storyboard r2b, scenes C3-1..C3-9).
 * COUNTERREVOLUTION register: grudging admiration for the men with the ball —
 * every retreat beat pairs the loss (containment died) with the adaptation (the
 * game that replaced it attacks and risks more); the affirmation (bowlers got
 * better, the tide rose) reaches main flow number-free in the close.
 *
 * Morph budget: exactly ONE controlling morph — free field → the frontier plane
 * (ch3-frontier), returned in ch3-close (the same morph's return leg). Everything
 * between keeps layout 'frontier'; ch3-rivers adds the CONTRACT §16 dismissal
 * RIVERS (a cross-cutting subset that composes with the plane — it does NOT spend
 * a second controlling morph, exactly like Ch 1's fireworks and Ch 2's cascade);
 * ch3-retreat brightens the scrubbed season via the §12 filterSeason (real data
 * migration, never a re-sort); the dot-grid / leak-gauge / WPL beats are 2D /
 * colour-state beats over the held plane.
 *
 * Every on-screen number comes from static/data/scenes/ch3.json (see ./data.ts)
 * — never hardcoded (OWNER-LOCKED). Where the artifact and the storyboard's teaser
 * copy disagree, the ARTIFACT wins (death wides 3.13→6.45 not 3.3→6.7; crack ratio
 * 1.18/0.81 not 1.11/0.84; the hero share 29.0%→1.5% not 29%→1%).
 */
export const scenes: SceneDef[] = [
	{
		id: 'ch3-title',
		chapter: 'ch3',
		anchor: 'ch3',
		navLabel: 'Chapter 3: The Counterrevolution',
		scrollLength: 100,
		morphLength: 45,
		// free field dimmed one stop behind the title; Ch 2→Ch 3 is free→free
		// (Ch 2 exhaled worm-space back to free at its close)
		fieldState: { layout: 'free', dim: 0.35 },
		annotations: Title
	},
	{
		id: 'ch3-frontier',
		chapter: 'ch3',
		scrollLength: 340,
		morphLength: 180, // THE controlling morph: free field → the frontier plane
		// every ball condenses onto its bowler-season's economy × strike-rate spot,
		// settling into a low-alpha density haze; the axes + the opening-season edge
		// are SVG on the annotation plane (Frontier.svelte). Reduced motion jump-cuts
		// to the settled haze (default reducedMotionEndState = fieldState).
		fieldState: { layout: 'frontier' },
		annotations: Frontier,
		footnote: 'economy-convention'
	},
	{
		id: 'ch3-retreat',
		chapter: 'ch3',
		scrollLength: 380,
		morphLength: 40,
		// HERO: the plane HOLDS (the morph budget is spent). A season pointer
		// brightens the current season and dims the rest via filterSeason (§12
		// orchestrator-caveat pattern), so the bright cloud migrates up and right —
		// real data, never a re-layout. filterSeason is a caption STEP (post-morph),
		// so drive it from progress via dynamicState (kept in sync with the chip by
		// the shared retreatState).
		fieldState: { layout: 'frontier', filterMode: 'dim' },
		// reduced motion shows the whole haze; the SVG carries the 2008/2026 edges,
		// the full ghost trail and the hero pair statically.
		reducedMotionEndState: { layout: 'frontier', filterMode: 'dim' },
		dynamicState: (progress, held) => ({ ...held, filterSeason: retreatState(progress).year }),
		annotations: Retreat,
		footnote: 'frontier-retreat'
	},
	{
		id: 'ch3-rivers',
		chapter: 'ch3',
		scrollLength: 300,
		morphLength: 40,
		// the ONE subset-highlight (CONTRACT §16): bowler-credited wickets stream out
		// of their clouds into a flat-baseline 100%-stacked band. It composes with
		// 'frontier' and spends NO second morph. engage is a caption STEP (post-morph),
		// so drive it from progress via dynamicState.
		fieldState: {
			layout: 'frontier',
			// declare the band stack order explicitly so the GL fly-out and the
			// DismissalRivers SVG overlay share one source of truth (never rely on
			// field.ts's default riversOrder happening to match the SVG's order)
			rivers: {
				class: 'wicket',
				kinds: ['bowled', 'lbw', 'stumped', 'caught'],
				engage: 0,
				tint: 1,
				othersDim: 0.12,
				muteIdentity: 1
			}
		},
		// reduced motion jump-cuts to the settled 100%-stacked band (engage 1)
		reducedMotionEndState: {
			layout: 'frontier',
			rivers: {
				class: 'wicket',
				kinds: ['bowled', 'lbw', 'stumped', 'caught'],
				engage: 1,
				tint: 1,
				othersDim: 0.12,
				muteIdentity: 1
			}
		},
		dynamicState: (progress, held) => ({
			...held,
			rivers: { ...held.rivers!, engage: Math.min(1, progress / 0.3) }
		}),
		annotations: DismissalRivers,
		footnote: 'dismissal-dna'
	},
	{
		id: 'ch3-dotgrid',
		chapter: 'ch3',
		scrollLength: 240,
		morphLength: 45,
		// 2D beat over the held (dimmed) plane; declaring NO rivers lerps the wickets
		// back into their clouds (the reverse leg is free). No re-sort.
		fieldState: { layout: 'frontier', dim: 0.4 },
		annotations: DotGrid,
		footnote: 'dot-plus'
	},
	{
		id: 'ch3-wides',
		chapter: 'ch3',
		scrollLength: 220,
		morphLength: 45,
		// the leak gauge (2D); the plane dims far back, loop stopped
		fieldState: { layout: 'frontier', dim: 0.35 },
		annotations: WideTax,
		footnote: 'death-wides'
	},
	{
		id: 'ch3-wpl',
		chapter: 'ch3',
		scrollLength: 220,
		morphLength: 60,
		// two clocks in one beat: WPL clouds brighten to full, IPL takes the mirrored
		// one-stop dim (0.55 × 1.82 ≈ 1.0), the same colour-state change as Ch 1/Ch 2's
		// WPL beat — no re-sort.
		fieldState: { layout: 'frontier', dim: 0.55, wplDim: 1.82 },
		annotations: WplBeat,
		footnote: 'crack-ratio'
	},
	{
		id: 'ch3-payoff',
		chapter: 'ch3',
		scrollLength: 160,
		morphLength: 50,
		// the reader's team stays ignited (default) on the plane while the rest dims
		// behind the "your gravity-defier" card
		fieldState: { layout: 'frontier', dim: 0.3 },
		annotations: GravityDefier,
		footnote: 'true-economy'
	},
	{
		id: 'ch3-close',
		chapter: 'ch3',
		scrollLength: 100,
		morphLength: 45,
		// the frontier plane exhales back into the free field — the controlling
		// morph's return leg, fast (hands off to the end card / Ch 4)
		fieldState: { layout: 'free' },
		annotations: CloseCh3
	}
];
