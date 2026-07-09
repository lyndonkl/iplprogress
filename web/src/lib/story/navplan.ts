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
	// Every chapter is now LIVE. Chapters 2 through 9 declare navLabels on their
	// title scenes (see src/lib/scenes/ch2..ch9, interlude), and 'Chapter 10: The
	// Era Machine' shipped in R6a as the LAST chapter (its title scene declares
	// the navLabel; see src/lib/scenes/ch10), so it too is a live nav item, not a
	// `soon`. 'The Field Is Yours' (the sandbox) is live via its Bowl scene's
	// navLabel. With Chapter 10 the narrative is complete: there is no Chapter 11
	// and no next-chapter tease, so FUTURE_CHAPTERS is empty and the nav is
	// all-live.
];

/** Compose nav items: scenes that declare navLabel, then the soon list. */
export function buildNavItems(scenes: SceneDef[]): NavItem[] {
	const live: NavItem[] = scenes
		.filter((s) => s.navLabel)
		.map((s) => ({ label: s.navLabel as string, anchor: s.anchor ?? s.id, status: 'live' }));
	const soon: NavItem[] = FUTURE_CHAPTERS.map((label) => ({ label, status: 'soon' }));
	return [...live, ...soon];
}
