import type { SceneDef } from './types';

/**
 * The persistent chapter nav's item model (blueprint §2 / storyboard §6):
 * built scenes are live links; every future chapter is listed by title with a
 * `soon` tag — the full menu is the promise of shape. Titles are commitments;
 * numbers aren't, yet (no teaser copy on unbuilt chapters).
 */

export interface NavItem {
	label: string;
	/** hash anchor for live items; undefined for `soon` items */
	anchor?: string;
	status: 'live' | 'soon';
}

/** Unbuilt chapters, in reading order, titles only (storyboard §6). */
export const FUTURE_CHAPTERS: string[] = [
	// 'Chapter 2: The Last of the Anchors', 'Chapter 3: The Counterrevolution' and
	// 'Chapter 4: The Rising Tide' are now LIVE (their scenes declare a navLabel;
	// see src/lib/scenes/ch2, ch3, ch4), so they appear as live nav items.
	'Interlude: The Net Session',
	'Chapter 5: What a Ball Is Worth',
	'Chapter 6: Two Dialects',
	'Chapter 7: The Twelfth Man',
	'Chapter 8: The Captain’s Brain',
	'Chapter 9: The Living League',
	'Chapter 10: The Era Machine'
	// 'The Field Is Yours' is now LIVE (the Bowl scene declares it as a navLabel;
	// see src/lib/scenes/sandbox), so it appears as a live nav item, not a `soon`.
];

/** Compose nav items: scenes that declare navLabel, then the soon list. */
export function buildNavItems(scenes: SceneDef[]): NavItem[] {
	const live: NavItem[] = scenes
		.filter((s) => s.navLabel)
		.map((s) => ({ label: s.navLabel as string, anchor: s.anchor ?? s.id, status: 'live' }));
	const soon: NavItem[] = FUTURE_CHAPTERS.map((label) => ({ label, status: 'soon' }));
	return [...live, ...soon];
}
