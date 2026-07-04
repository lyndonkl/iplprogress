/**
 * In-page coordination between the payoff card's "Not your team? Change it"
 * link and the picker (storyboard C1-7: "→ picker (state preserved, returns
 * here)"). The card records where the reader left from; after the re-pick the
 * picker's advance returns them there instead of moving on to the next scene.
 * Module-level state is fine: both ends live in this directory and the scenes
 * never unmount.
 */

import { scrollToElement } from './scroll';

let returnTarget: HTMLElement | null = null;

/** Called by the payoff card: remember the card, then jump to the picker. */
export function requestTeamChange(from: HTMLElement | null): void {
	returnTarget = from;
	const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	const picker = document.getElementById('picker');
	if (picker !== null) scrollToElement(picker, reduced);
}

/** Called by the picker's advance: the pending return point, if any (one-shot). */
export function consumeReturnTarget(): HTMLElement | null {
	const el = returnTarget;
	returnTarget = null;
	return el !== null && el.isConnected ? el : null;
}
