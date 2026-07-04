import type { SceneDef } from '$lib/story/types';
import Bowl from './Bowl.svelte';
import { bowlHeld } from './data';

/**
 * THE BOWL — "The Field Is Yours" (blueprint §3 minimal-Bowl, R1b). The FINAL
 * scene: the persistent 316k-ball field becomes a filterable instrument. The
 * end card exhaled to the free field; the Bowl morphs it into season columns
 * (so the season facet maps spatially) and HOLDS there while the reader filters
 * and taps.
 *
 * Terminal held scene (CONTRACT §12.2): `fieldState` AND `reducedMotionEndState`
 * both point at the SAME live `bowlHeld` object, which Bowl.svelte keeps in sync
 * with the reader's facets on every change (via `syncBowlHeld`). So whichever
 * path the orchestrator resolves the held state through — `dynamicTarget` /
 * `heldState` under normal motion, `sceneEndState` under reduced motion — it
 * reads the reader's CURRENT facets, and a stray scroll can never revert them.
 * The instant render on each facet change comes from `field.setFilter`.
 */
export const scenes: SceneDef[] = [
	{
		id: 'bowl',
		chapter: 'bowl',
		anchor: 'bowl',
		navLabel: 'The Field Is Yours',
		scrollLength: 220,
		morphLength: 90, // free field → season columns, then a long interactive hold
		fieldState: bowlHeld,
		reducedMotionEndState: bowlHeld,
		annotations: Bowl
	}
];
