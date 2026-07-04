import type { SceneDef } from '$lib/story/types';
import TitleRitual from './TitleRitual.svelte';
import Wall from './Wall.svelte';
import Pivot from './Pivot.svelte';
import OutRate from './OutRate.svelte';
import Fireworks from './Fireworks.svelte';
import WplBeat from './WplBeat.svelte';
import PayoffCard from './PayoffCard.svelte';
import Close from './Close.svelte';
import { twoTone, wallHeatMixAt } from './data';

/**
 * CHAPTER 1 — The Death of the Sighter (storyboard §3, scenes C1-1..C1-8).
 *
 * Morph budget: exactly ONE controlling morph — free field → ignition wall
 * (ch1-wall), returned in ch1-close (the same morph's return leg). Everything
 * between keeps layout 'wall'; ch1-sixes adds the CONTRACT §7 subset RE-SORT
 * (a cross-cutting modifier that composes with the wall — it does NOT spend a
 * second controlling morph), and the others are 2D annotation-plane scenes.
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
		// Establishing shot (outcome colour) as the points fly in and through
		// caption steps 1-2 (heat 0). Steps 3-4 are the THESIS beat: dynamicState
		// ramps wallHeatMix 0→1 during the hold, recolouring every ball by how
		// far it beats the 2008-2010 batter at the same ball-index — the wall's
		// horizontal acceleration gradient cancels and the early-ball corner
		// ignites bottom→top. No re-sort here → the heat beat is staged ALONE.
		fieldState: { layout: 'wall', wplDim: 0.55 },
		// step 3's recolor ramp + step 4's hold live in the HOLD (post-morph), so
		// they can't ride the free→wall morph; drive them from progress. The
		// settle-back is free — ch1-pivot declares wallHeatMix 0 (default), so the
		// heat lerps 1→0 as the pivot morphs in, well before the fireworks lift.
		dynamicState: (progress, held) => ({ ...held, wallHeatMix: wallHeatMixAt(progress) }),
		// reduced motion jump-cuts to the beat's rest position: the heated wall
		// (wallHeatMix 1) rendered statically, team glow intact.
		reducedMotionEndState: { layout: 'wall', wplDim: 0.55, wallHeatMix: 1 },
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
		// The chapter's signature subset moment (storyboard C1-5, CONTRACT §7/§9):
		// every IPL six lifts vertically out of the ignition wall (two-phase — it
		// arcs up as the wall dims hard via othersDim) and RE-SORTS into 19
		// per-season firework columns, height = that season's six count, each
		// point a real six. Reversible: the next scene (ch1-wpl) declares no
		// resort, so `engage` lerps 1→0 and the sixes settle back onto the wall.
		// skipWpl keeps the WPL's sixes on its shelf — the caption names the
		// omission as deliberate. columns:'ipl' → 19 IPL season columns only.
		fieldState: {
			layout: 'wall',
			wplDim: 0.55,
			resort: {
				class: 'six',
				skipWpl: true,
				columns: 'ipl',
				engage: 1,
				lift: 0.5,
				othersDim: 0.12,
				tint: 0
			}
		},
		// reduced motion jump-cuts straight to the stacked columns (the two-phase
		// lift collapses). tint stays 0 until the pipeline ships attrs.u8 bit 5
		// (the season-top-10-hitter flag) — with the bit absent the shader would
		// dim every six uniformly. When it ships, set tint: 1 here so the
		// reduced-motion jump-cut lands on the two-toned columns (the animated
		// path already auto-enables via the twoTone gate below).
		reducedMotionEndState: {
			layout: 'wall',
			wplDim: 0.55,
			resort: {
				class: 'six',
				skipWpl: true,
				columns: 'ipl',
				engage: 1,
				lift: 0.5,
				othersDim: 0.12,
				tint: 0
			}
		},
		// step 3's one change: raise the two-tone recolor tint once the caption
		// crosses its threshold — but ONLY when the top-10 bit is actually
		// populated (twoTone.available, set by Fireworks after scanning attrs).
		// With the bit absent the shader dims every six uniformly (misleading),
		// so we hold tint at 0 and Fireworks drops the "watch the slice shrink"
		// line to match (pixels == copy in both states).
		dynamicState: (progress, held) => ({
			...held,
			resort: { ...held.resort!, tint: progress >= 0.8 && twoTone.available ? 1 : 0 }
		}),
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
