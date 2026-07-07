import type { FieldHandle } from '$lib/field/field';

/**
 * §0.4a caption-overlap safe corner (the BINDING desktop rule): on the
 * constellation scenes the caption must sit in a corner that does NOT cover any
 * star, the worm, a thread, or the WPL cluster, in ANY phase. The star box is
 * centred + letterboxed and the WPL cluster is far-left in every phase table, so
 * a hard-coded bottom-left caption would sit ON the WPL cluster (the exact
 * failure the audit flagged).
 *
 * Rather than emit a per-phase hull in the pipeline, we read the LIVE star
 * geometry straight off the field (`getConstellationLayout()` → `projectToCss`,
 * the exact centres the shader draws, which already track the phase-toggle
 * glide) and pick the corner whose caption footprint overlaps the star content
 * the least. This tracks the glide and any resize for free, and gives the QA
 * overlap check for nothing (a dev-time warn fires if even the best corner would
 * cover content). Top-right is reserved for the nav ☰.
 */

export type Corner = 'tl' | 'tr' | 'bl' | 'br';

interface Rect {
	x: number;
	y: number;
	w: number;
	h: number;
}

/** Reactive-ish singleton: is the viewport at/under the 640px mobile breakpoint? */
let narrow = $state(false);
if (typeof window !== 'undefined') {
	const mql = window.matchMedia('(max-width: 640px)');
	narrow = mql.matches;
	mql.addEventListener('change', (e) => {
		narrow = e.matches;
	});
}

/**
 * True on a real phone-width viewport. Read inside a `$derived` to track it. On
 * mobile the caption uses the bottom read-then-watch slot (§17), so scenes skip
 * the desktop corner placement and let their `@media (max-width: 640px)` rule win.
 */
export function isNarrowViewport(): boolean {
	return narrow;
}

function intersectArea(a: Rect, b: Rect): number {
	const ox = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
	const oy = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
	return ox * oy;
}

/** Nominal caption footprint (CSS px) for a corner, mirroring the .caption-slot CSS. */
function captionRect(corner: Corner, vw: number, vh: number): Rect {
	const w = Math.min(400, vw * 0.4);
	const h = Math.min(220, vh * 0.34);
	const mx = vw * 0.05; // 5vw horizontal inset
	const mb = vh * 0.08; // 8vh from the bottom
	const mt = vh * 0.15; // 15vh from the top (below the nav band)
	const x = corner === 'tl' || corner === 'bl' ? mx : vw - mx - w;
	const y = corner === 'tl' || corner === 'tr' ? mt : vh - mb - h;
	return { x, y, w, h };
}

export interface CornerPick {
	corner: Corner;
	/** overlap area (CSS px²) of the chosen caption footprint with star content */
	overlap: number;
}

let warned = false;

/**
 * Pick the caption corner clear of the star content for the LIVE phase. Returns
 * 'br' as a safe default before the first resize (the layout is null). Excludes
 * top-right (the nav lives there). Dev-warns once if even the best corner would
 * cover a star (the §0.4a QA assertion, surfaced instead of silently failing).
 */
export function pickCaptionCorner(field: FieldHandle | null): CornerPick {
	const fallback: CornerPick = { corner: 'br', overlap: 0 };
	if (typeof window === 'undefined' || !field) return fallback;
	const cl = field.getConstellationLayout();
	if (!cl) return fallback;

	const vw = window.innerWidth;
	const vh = window.innerHeight;
	// each star → a disc allowance (radius + a taller top margin for its label)
	const r = Math.max(22, Math.min(vw, vh) * 0.03);
	const obstacles: Rect[] = [];
	for (const s of cl.stars) {
		const p = field.projectToCss(s.x, s.y);
		obstacles.push({ x: p.x - r, y: p.y - r * 1.7, w: 2 * r, h: r * 2.7 });
	}

	// preference order: bottom corners first, then top-left; top-right reserved
	const order: Corner[] = ['br', 'bl', 'tl'];
	let best: CornerPick | null = null;
	for (const corner of order) {
		const cap = captionRect(corner, vw, vh);
		let overlap = 0;
		for (const o of obstacles) overlap += intersectArea(cap, o);
		if (best === null || overlap < best.overlap - 1) best = { corner, overlap };
	}
	const pick = best ?? fallback;
	if (import.meta.env.DEV && pick.overlap > 1 && !warned) {
		warned = true;
		// eslint-disable-next-line no-console
		console.warn(
			`[ch6] caption safe-corner '${pick.corner}' still overlaps stars by` +
				` ~${Math.round(pick.overlap)}px² — tighten the constellation fill or caption size.`
		);
	}
	return pick;
}

/** Inline CSS positioning the .caption-slot at the chosen corner (desktop only). */
export function cornerStyle(corner: Corner): string {
	const left = corner === 'tl' || corner === 'bl';
	const top = corner === 'tl' || corner === 'tr';
	return [
		left ? 'left:5vw' : 'left:auto',
		left ? 'right:auto' : 'right:5vw',
		top ? 'top:15vh' : 'top:auto',
		top ? 'bottom:auto' : 'bottom:8vh'
	].join(';');
}
