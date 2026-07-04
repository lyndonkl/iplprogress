/**
 * Background scroll lock for open dialogs (storyboard §6 nav + the footnote
 * sheet; audit finding #18). While a sheet is open, a stray swipe on the scrim
 * must not scroll the story underneath — otherwise the field scrubs and the
 * active scene changes beneath the reader mid-read.
 *
 * Uses the iOS-safe position-fixed technique (plain `overflow: hidden` on body
 * does not stop touch scrolling in mobile Safari): pin the body at its current
 * scroll offset, then restore it on release. Reference-counted so the nav and
 * the footnote panel can hold the lock independently without clobbering each
 * other — the body is only pinned on the first lock and released on the last.
 */

let count = 0;
let savedScrollY = 0;
let savedStyles: {
	position: string;
	top: string;
	left: string;
	right: string;
	width: string;
	overflow: string;
} | null = null;

export function lockScroll(): void {
	if (typeof document === 'undefined') return;
	if (count++ > 0) return; // already locked by another dialog

	savedScrollY = window.scrollY;
	const body = document.body;
	savedStyles = {
		position: body.style.position,
		top: body.style.top,
		left: body.style.left,
		right: body.style.right,
		width: body.style.width,
		overflow: body.style.overflow
	};

	body.style.position = 'fixed';
	body.style.top = `-${savedScrollY}px`;
	body.style.left = '0';
	body.style.right = '0';
	body.style.width = '100%';
	body.style.overflow = 'hidden';
}

export function unlockScroll(): void {
	if (typeof document === 'undefined') return;
	if (count === 0) return;
	if (--count > 0) return; // another dialog still holds the lock

	const body = document.body;
	if (savedStyles) {
		body.style.position = savedStyles.position;
		body.style.top = savedStyles.top;
		body.style.left = savedStyles.left;
		body.style.right = savedStyles.right;
		body.style.width = savedStyles.width;
		body.style.overflow = savedStyles.overflow;
		savedStyles = null;
	}
	// restoring position removes the pin; put the reader back where they were
	// (this scroll fires ScrollTrigger.update → the field re-renders in place)
	window.scrollTo(0, savedScrollY);
}
