import type { SceneDef } from '$lib/story/types';
import TeamPicker from './TeamPicker.svelte';

/**
 * TEAM PICKER — owned by the picker scene builders (storyboard §2).
 * One tap-screen after the title card: neutral tile first and full-width (the
 * skip IS a tile), 10 IPL + 5 WPL typographic crests from teams.json. A pick
 * writes `ebe.team.v1`; the shell maps it to the ignite uniform — the team's
 * balls light in its colors and stay lit through the whole story.
 *
 * This directory also owns the REUSABLE end-of-chapter payoff card
 * (storyboard C1-7): chapter builders import { PayoffCard } here and drop it
 * into their close scene — template + data/payoff/ch1.json, never hand-authored.
 */
export const scenes: SceneDef[] = [
	{
		id: 'picker',
		chapter: 'picker',
		anchor: 'picker',
		navLabel: 'Pick your team',
		scrollLength: 160,
		morphLength: 90,
		// the assembled free field idles dimmed behind the picker; a pick
		// re-ignites in one render (color state, not a morph — demand mode)
		fieldState: { layout: 'free', dim: 0.8 },
		annotations: TeamPicker
	}
];

/* reusable payoff-card surface for chapter builders */
export { default as PayoffCard } from './PayoffCard.svelte';
export { loadPayoffCh1, payoffVariantFor } from './payoff';
export type { PayoffCh1, PayoffVariant, ResolvedPayoff } from './payoff';
export { requestTeamChange } from './changeteam';
