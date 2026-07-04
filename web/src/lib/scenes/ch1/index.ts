import type { SceneDef } from '$lib/story/types';
import TitleRitual from './TitleRitual.svelte';
import Wall from './Wall.svelte';
import Pivot from './Pivot.svelte';
import OutRate from './OutRate.svelte';
import Fireworks from './Fireworks.svelte';
import WplBeat from './WplBeat.svelte';
import PayoffCard from './PayoffCard.svelte';
import Close from './Close.svelte';

/**
 * CHAPTER 1 — The Death of the Sighter (storyboard §3, scenes C1-1..C1-8).
 *
 * Morph budget: exactly ONE controlling morph — free field → ignition wall
 * (ch1-wall), returned in ch1-close (the same morph's return leg). Everything
 * between is a subset-highlight (ch1-sixes) or a 2D annotation-plane scene;
 * every intermediate scene keeps layout 'wall' so no second re-sort exists.
 *
 * WPL shelf staging (storyboard C1-2/C1-6): wplDim 0.55 from the wall's
 * completion through the fireworks — the shelf's dark left edge must not
 * contradict the upward luminance sweep in the channel that carries it —
 * then restored at ch1-wpl, where the brighten IS the beat. ch1-wpl pairs
 * dim 0.55 with wplDim 1.82 (0.55 × 1.82 ≈ 1.0): the IPL takes the identical
 * one-stop dim the shelf carried, and the WPL returns to full — the shader
 * multiplies the two, so this is luminance-exact.
 *
 * Scene data: static/data/scenes/ch1.json + payoff/ch1.json (see ./data.ts);
 * no on-screen number is hardcoded except the two storyboard-§9 constants
 * flagged in Fireworks.svelte.
 */
export const scenes: SceneDef[] = [
	{
		id: 'ch1-title',
		chapter: 'ch1',
		anchor: 'ch1',
		navLabel: 'Chapter 1 — The Death of the Sighter',
		scrollLength: 80,
		morphLength: 40,
		// free field dimmed behind the title; loop stopped while holding
		fieldState: { layout: 'free', dim: 0.35 },
		annotations: TitleRitual
	},
	{
		id: 'ch1-wall',
		chapter: 'ch1',
		scrollLength: 300,
		morphLength: 150, // THE controlling morph: free field → ignition wall
		fieldState: { layout: 'wall', wplDim: 0.55 },
		annotations: Wall,
		footnote: 'ignition-wall'
	},
	{
		id: 'ch1-pivot',
		chapter: 'ch1',
		scrollLength: 60,
		morphLength: 35,
		// the wall holds, dimmed one stop, while the objection is voiced
		fieldState: { layout: 'wall', dim: 0.55, wplDim: 0.55 },
		annotations: Pivot
	},
	{
		id: 'ch1-outrate',
		chapter: 'ch1',
		scrollLength: 200,
		morphLength: 50,
		// pure 2D scene: the field dims far back; loop provably stopped
		fieldState: { layout: 'wall', dim: 0.16, wplDim: 0.55 },
		annotations: OutRate,
		footnote: 'out-rate'
	},
	{
		id: 'ch1-sixes',
		chapter: 'ch1',
		scrollLength: 170,
		morphLength: 70,
		// the chapter's one subset-highlight: the IPL's sixes lift out of the
		// wall and brighten while everything else dims hard (no re-sort —
		// CONTRACT §3). skipWpl: the WPL's sixes stay on its shelf — the
		// caption names the omission as deliberate (storyboard C1-5).
		fieldState: {
			layout: 'wall',
			wplDim: 0.55,
			highlight: { class: 'six', lift: 0.14, boost: 0.6, othersDim: 0.12, skipWpl: true }
		},
		annotations: Fireworks,
		footnote: 'sixes'
	},
	{
		id: 'ch1-wpl',
		chapter: 'ch1',
		scrollLength: 150,
		morphLength: 60,
		// the shelf brightens to full (the beat), the IPL takes the mirrored
		// one-stop dim; the sixes settle back as the highlight lerps out
		fieldState: { layout: 'wall', dim: 0.55, wplDim: 1.82 },
		annotations: WplBeat,
		footnote: 'wpl-two-clocks'
	},
	{
		id: 'ch1-payoff',
		chapter: 'ch1',
		scrollLength: 140,
		morphLength: 50,
		// reader's team stays ignited (default) while the field dims behind the card
		fieldState: { layout: 'wall', dim: 0.3 },
		annotations: PayoffCard,
		footnote: 'payoff-ch1'
	},
	{
		id: 'ch1-close',
		chapter: 'ch1',
		scrollLength: 90,
		morphLength: 40,
		// the wall exhales back into the free field — the return leg, fast
		fieldState: { layout: 'free' },
		annotations: Close
	}
];
