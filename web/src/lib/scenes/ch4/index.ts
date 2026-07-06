import type { SceneDef } from '$lib/story/types';
import { readGapScrollLength } from '$lib/story/captionReveal.svelte';
import {
	WATER_DROWN,
	tideParLevels,
	waterlineScrub,
	waterlineLevelAt,
	waterlineReducedEnd
} from './data';
import Title from './Title.svelte';
import TideOrient from './TideOrient.svelte';
import Waterline from './Waterline.svelte';
import TwoHundredClub from './TwoHundredClub.svelte';
import Mystery from './Mystery.svelte';
import Records from './Records.svelte';
import CpiCallback from './CpiCallback.svelte';
import Powerplay from './Powerplay.svelte';
import Venues from './Venues.svelte';
import WplBeat from './WplBeat.svelte';
import HomeGroundTide from './HomeGroundTide.svelte';
import CloseCh4 from './CloseCh4.svelte';

/**
 * CHAPTER 4 — The Rising Tide (storyboard §3, scenes C4-1..C4-12).
 * REGISTER: "the ground itself moves." The scoring environment is the character —
 * every ball is one first innings stacked into a column, and the water level (the
 * going rate) rises up the wall, drowning totals that used to be safe.
 *
 * Morph budget: exactly ONE controlling morph — free field → the tide skyline
 * (ch4-tide), returned in ch4-close (the same morph's return leg). Everything
 * between HOLDS layout 'tide': ch4-waterline adds the CONTRACT §18 waterline (a
 * rising luminance LEVEL that drowns old-safe columns — it composes with the
 * skyline and spends NO second morph, exactly like Ch 1's fireworks, Ch 2's
 * cascade and Ch 3's rivers); the 200 Club / mystery / records / CPI / powerplay /
 * venue / WPL beats are SVG + colour-state beats over the held skyline.
 *
 * ENGINE-LIGHT: no new engine. The waterline level is a per-season lookup from
 * ch4.json columns.par_waterline (engine #1, from R2a), cached by data.ts so the
 * pure dynamicState below raises the water without hardcoding a number.
 *
 * Every on-screen number comes from static/data/scenes/ch4.json (see ./data.ts)
 * — never hardcoded (OWNER-LOCKED). Where the artifact and the storyboard's teaser
 * copy disagree, the ARTIFACT wins (P(200) 42.0 not 41.9; par 195.3; 230-plus
 * posted 33 / defended 29, NOT the stale "11/11"; between-venue share 10.1 → 23.7).
 */
export const scenes: SceneDef[] = [
	{
		id: 'ch4-title',
		chapter: 'ch4',
		anchor: 'ch4',
		navLabel: 'Chapter 4: The Rising Tide',
		scrollLength: 100,
		morphLength: 45,
		// free field dimmed one stop behind the title; Ch 3 exhaled to free at close
		fieldState: { layout: 'free', dim: 0.32 },
		annotations: Title
	},
	{
		id: 'ch4-tide',
		chapter: 'ch4',
		scrollLength: 360,
		// MOBILE read-then-watch (CONTRACT §17.5): three post-morph orientation steps;
		// the extra travel keeps each read beat + clear gap unhurried on a phone.
		mobileScrollLength: readGapScrollLength(360),
		morphLength: 190, // THE controlling morph: free field → the tide skyline
		// every first innings condenses into its innings-total column; the rest settle
		// into the low-alpha reservoir haze (setFirstInnings in TideOrient). The
		// baseline / total ladder / season axis are SVG (TideScaffold). Reduced motion
		// jump-cuts free→tide (default reducedMotionEndState = fieldState).
		fieldState: { layout: 'tide' },
		annotations: TideOrient,
		footnote: 'tide-reservoir'
	},
	{
		id: 'ch4-waterline',
		chapter: 'ch4',
		// four caption steps (orient · rise · par-drift punchline · the 230 ceiling);
		// the extra travel keeps each read beat unhurried under read-then-watch.
		scrollLength: 480,
		mobileScrollLength: readGapScrollLength(480),
		morphLength: 40,
		// HERO (Par-Score Drift): the skyline HOLDS (the morph budget is spent). The
		// waterline (the going rate) floods in and then RISES season by season as the
		// reader scrubs, drowning columns that fall below it — real data (the per-season
		// par from ch4.json), never a re-layout. level is a post-morph field change, so
		// drive it from progress via dynamicState (kept in sync with the year chip by
		// the shared waterlineScrub). OWNER-LOCK: the level comes from tideParLevels()
		// (cached from ch4.json by data.ts), never a hardcoded number here.
		fieldState: { layout: 'tide', waterline: { level: 0, drownDim: WATER_DROWN } },
		// reduced motion jump-cuts to the water at its 2026 height (level filled in from
		// the artifact by loadCh4Data — no hardcoded number).
		reducedMotionEndState: waterlineReducedEnd,
		dynamicState: (progress, held) => {
			void tideParLevels(); // (touch the cache; level resolved below)
			const s = waterlineScrub(progress);
			return {
				...held,
				waterline: { ...held.waterline!, level: waterlineLevelAt(s.seasonIdx) }
			};
		},
		annotations: Waterline,
		footnote: 'par-drift'
	},
	{
		id: 'ch4-club',
		chapter: 'ch4',
		scrollLength: 400,
		mobileScrollLength: readGapScrollLength(400),
		morphLength: 45,
		// HERO (Threshold Exceedance — the 200 Club): the skyline HOLDS. Declaring no
		// waterline drains the going-rate line (the reverse leg is free) so the full
		// coastline is lit again; the fixed 200 / 180 / 220 / 250 rules + the scrubbing
		// P(200) chip are the SCENE's SVG over the held skyline (TwoHundredClub).
		fieldState: { layout: 'tide' },
		annotations: TwoHundredClub,
		footnote: 'full-first-innings'
	},
	{
		id: 'ch4-mystery',
		chapter: 'ch4',
		scrollLength: 200,
		morphLength: 45,
		// the planted 2023 mystery (authored beat): the 2023 cliff frozen on screen,
		// the chapter visibly refusing to explain it. Skyline dims one stop behind the
		// card; loop stopped. layout held (no morph).
		fieldState: { layout: 'tide', dim: 0.42 },
		annotations: Mystery,
		footnote: 'measured-jump'
	},
	{
		id: 'ch4-records',
		chapter: 'ch4',
		scrollLength: 320,
		mobileScrollLength: readGapScrollLength(320),
		morphLength: 45,
		// HERO close (Record Half-Life): the records ticker over the dimmed skyline —
		// the standing highest total, scrubbed 2008 → 2026, shattering on a board.
		fieldState: { layout: 'tide', dim: 0.4 },
		annotations: Records,
		footnote: 'record-null'
	},
	{
		id: 'ch4-cpi',
		chapter: 'ch4',
		scrollLength: 280,
		mobileScrollLength: readGapScrollLength(280),
		morphLength: 45,
		// SUPPORTING (T20 CPI callback): the reader's cold-open sketch returns over the
		// dimmed skyline (no-sketch variant when they skipped / arrived by link).
		fieldState: { layout: 'tide', dim: 0.38 },
		annotations: CpiCallback,
		footnote: 'cpi-callback'
	},
	{
		id: 'ch4-powerplay',
		chapter: 'ch4',
		scrollLength: 300,
		mobileScrollLength: readGapScrollLength(300),
		morphLength: 45,
		// SUPPORTING (Powerplay Exploitation Premium): the 20-over × season phase
		// heatmap (2D) over the dimmed skyline — the powerplay corner igniting.
		fieldState: { layout: 'tide', dim: 0.35 },
		annotations: Powerplay,
		footnote: 'phase-economy'
	},
	{
		id: 'ch4-venues',
		chapter: 'ch4',
		scrollLength: 300,
		mobileScrollLength: readGapScrollLength(300),
		morphLength: 45,
		// SUPPORTING (Venue Fingerprints — the contrarian twist): the venue divergence
		// cone (2D) over the dimmed skyline.
		fieldState: { layout: 'tide', dim: 0.35 },
		annotations: Venues,
		footnote: 'venue-canon'
	},
	{
		id: 'ch4-wpl',
		chapter: 'ch4',
		// four one-idea steps (calendar clock · faster rise · four-led shape · the
		// event); the longer travel gives each read beat room under read-then-watch.
		scrollLength: 360,
		mobileScrollLength: readGapScrollLength(360),
		morphLength: 60,
		// two clocks in one beat: the WPL block brightens to full, the IPL takes the
		// mirrored one-stop dim (0.55 × 1.82 ≈ 1.0), the same colour-state change as Ch
		// 1/2/3's WPL beat — no re-sort.
		fieldState: { layout: 'tide', dim: 0.55, wplDim: 1.82 },
		annotations: WplBeat,
		footnote: 'wpl-two-clocks-ch4'
	},
	{
		id: 'ch4-payoff',
		chapter: 'ch4',
		scrollLength: 200,
		morphLength: 50,
		// the reader's team stays ignited (default) on the skyline while the rest dims
		// behind the "your home ground's tide" card.
		fieldState: { layout: 'tide', dim: 0.3 },
		annotations: HomeGroundTide,
		footnote: 'venue-canon'
	},
	{
		id: 'ch4-close',
		chapter: 'ch4',
		scrollLength: 100,
		morphLength: 45,
		// the tide skyline exhales back into the free field — the controlling morph's
		// return leg, fast (hands off to the interlude / end card).
		fieldState: { layout: 'free' },
		annotations: CloseCh4
	}
];
