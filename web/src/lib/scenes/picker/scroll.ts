/**
 * Guaranteed-arrival scroll for the picker's auto-advance and the payoff
 * card's change-team round trip. Native `scrollIntoView({behavior:'smooth'})`
 * is silently cancelled in some Chromium configurations — a reader stuck on
 * the picker after tapping their team is a broken story, so we drive a short
 * eased tween ourselves. It is transient (≤ ~0.9s) and self-terminating: the
 * field renders during it exactly as during a manual scrub, and the loop
 * stops at arrival (demand-mode invariant intact). Any reader input cancels
 * it — the reader always outranks the tween. Reduced motion jumps instantly.
 */
export function scrollToElement(el: HTMLElement, reduced: boolean): void {
	// Land a hair INSIDE the target (mirrors the shell's 2px scene anchors):
	// arriving at exactly a section's top leaves its ScrollTrigger at
	// progress 0, so the PREVIOUS scene still owns the field and the target
	// scene's captions stay hidden until the reader scrolls one more pixel.
	const targetY = window.scrollY + el.getBoundingClientRect().top + 3;
	if (reduced) {
		window.scrollTo(0, targetY);
		return;
	}

	const startY = window.scrollY;
	const dist = targetY - startY;
	if (Math.abs(dist) < 1) return;
	const duration = Math.min(900, Math.max(350, Math.abs(dist) * 0.45));
	const t0 = performance.now();
	let cancelled = false;

	const cancel = (): void => {
		cancelled = true;
		window.removeEventListener('wheel', cancel);
		window.removeEventListener('touchstart', cancel);
		window.removeEventListener('keydown', cancel);
	};
	window.addEventListener('wheel', cancel, { passive: true });
	window.addEventListener('touchstart', cancel, { passive: true });
	window.addEventListener('keydown', cancel);

	const ease = (t: number): number => 1 - Math.pow(1 - t, 3); // easeOutCubic

	const step = (now: number): void => {
		if (cancelled) return;
		const t = Math.min(1, (now - t0) / duration);
		window.scrollTo(0, startY + dist * ease(t));
		if (t < 1) requestAnimationFrame(step);
		else cancel(); // arrival: detach listeners, loop ends
	};
	requestAnimationFrame(step);
}
