import type { FieldHandle } from '$lib/field/field';

/**
 * §0.4a caption-overlap safe corner (the BINDING desktop rule), retuned from the
 * Ch 7 twin-rivers version to Chapter 8's geometry: the match-dots box (a wide,
 * letterboxed cloud), the two toss lanes, and the per-franchise review chip lanes.
 *
 * Rather than emit a hull, we read the LIVE field geometry and pick the corner
 * whose caption footprint overlaps the on-screen content the least. This tracks
 * the `matchSplit` lane lift, the review chip fly-out and any resize for free.
 * Top-right is reserved for the nav; bottom-left is reserved for the persistent
 * match-dots legend, so the dot-cloud corner pick chooses between top-left and
 * bottom-right. On the toss lanes the field-first river swells along the bottom
 * toward the right, so top-left wins (the corner opposite the swelling river).
 */

export type Corner = 'tl' | 'tr' | 'bl' | 'br';

interface Rect {
	x: number;
	y: number;
	w: number;
	h: number;
}

let narrow = $state(false);
if (typeof window !== 'undefined') {
	const mql = window.matchMedia('(max-width: 640px)');
	narrow = mql.matches;
	mql.addEventListener('change', (e) => {
		narrow = e.matches;
	});
}

/** True on a real phone-width viewport (mobile uses the bottom read-then-watch slot). */
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
	const w = Math.min(400, vw * 0.42);
	const h = Math.min(230, vh * 0.36);
	const mx = vw * 0.05;
	const mb = vh * 0.08;
	const mt = vh * 0.15;
	const x = corner === 'tl' || corner === 'bl' ? mx : vw - mx - w;
	const y = corner === 'tl' || corner === 'tr' ? mt : vh - mb - h;
	return { x, y, w, h };
}

export interface CornerPick {
	corner: Corner;
	overlap: number;
}

let warnedDots = false;

/**
 * Pick the caption corner clear of the match-dot cloud (and its lane lift) for the
 * LIVE `matchSplit`. Samples the per-match world centroids from `getMatchDotsLayout()`
 * (every Nth, so ~50 obstacle points, cheap) and projects them to CSS. Returns 'tl'
 * as a safe default before the first resize / match table. Excludes top-right (nav)
 * and bottom-left (the persistent legend), so it chooses top-left vs bottom-right -
 * the dot cloud fills the middle band, so top-left usually wins, and on the split
 * lanes the caption takes the upper-left corner opposite the swelling river.
 */
export function pickCaptionCorner(field: FieldHandle | null): CornerPick {
	const fallback: CornerPick = { corner: 'tl', overlap: 0 };
	if (typeof window === 'undefined' || !field) return fallback;
	const md = field.getMatchDotsLayout();
	if (!md) return fallback;

	const vw = window.innerWidth;
	const vh = window.innerHeight;
	const r = Math.max(16, Math.min(vw, vh) * 0.02);

	const obstacles: Rect[] = [];
	const centres = md.centres;
	const stride = Math.max(1, Math.floor(centres.length / 60));
	for (let m = 0; m < centres.length; m += stride) {
		const c = centres[m];
		if (!c || Number.isNaN(c.x) || Number.isNaN(c.y)) continue;
		const p = field.projectToCss(c.x, c.y);
		obstacles.push({ x: p.x - r, y: p.y - r, w: 2 * r, h: 2 * r });
	}

	const order: Corner[] = ['tl', 'br'];
	let best: CornerPick | null = null;
	for (const corner of order) {
		const cap = captionRect(corner, vw, vh);
		let overlap = 0;
		for (const o of obstacles) overlap += intersectArea(cap, o);
		if (best === null || overlap < best.overlap - 1) best = { corner, overlap };
	}
	const pick = best ?? fallback;
	if (import.meta.env.DEV && pick.overlap > 1 && !warnedDots) {
		warnedDots = true;
		// eslint-disable-next-line no-console
		console.warn(
			`[ch8] caption safe-corner '${pick.corner}' still overlaps the match-dots by` +
				` ~${Math.round(pick.overlap)}px², tighten the fill or caption size.`
		);
	}
	return pick;
}

/**
 * §0.4a corner for the REVIEW-CHIP scene (C8-4): "upper-right if the tallest chip
 * lane is on the left, else upper-left" (storyboard), recomputed from the emitted
 * chip-lane centres so the caption never covers a lane or the legend. The chips
 * build up from the bottom, so the caption always takes a TOP corner; we only
 * decide left vs right by where the tallest lane sits.
 */
export function pickReviewCorner(field: FieldHandle | null): CornerPick {
	const fallback: CornerPick = { corner: 'tl', overlap: 0 };
	if (typeof window === 'undefined' || !field) return fallback;
	const rc = field.getReviewChipsLayout();
	if (!rc || rc.lanes.length === 0) return fallback;

	// find the tallest lane's screen x (topY is the world top of the stack)
	let tallest = rc.lanes[0];
	for (const ln of rc.lanes) if (ln.total > tallest.total) tallest = ln;
	const vw = typeof window !== 'undefined' ? window.innerWidth : 1024;
	const tallestX = field.projectToCss(tallest.x, tallest.topY).x;
	// tallest lane on the left → caption on the right, and vice versa
	const corner: Corner = tallestX < vw / 2 ? 'tr' : 'tl';
	return { corner, overlap: 0 };
}

/**
 * §0.4a for the CENTRED-PANEL exhibits (the spell mosaics, the momentum panel, the
 * required-rate curve): those beats are a centred panel, not the dot cloud, so the
 * caption safe-corner is derived from the ACTUAL panel rect, placed in the margin
 * BESIDE it (left preferred, the nav owns the top-right). Returns '' when neither
 * margin is wide enough for a legible caption so the scene falls back to its CSS
 * default; mobile uses the bottom read-then-watch slot and never calls this.
 */
export function panelCaptionStyle(panel: HTMLElement | null): string {
	if (typeof window === 'undefined' || !panel) return '';
	const r = panel.getBoundingClientRect();
	if (r.width === 0) return '';
	const vw = window.innerWidth;
	const gutter = Math.max(16, vw * 0.025);
	const MIN = 190; // a caption narrower than this is unreadable, fall back
	const leftMargin = r.left;
	const rightMargin = vw - r.right;
	if (leftMargin >= MIN + gutter) {
		const w = Math.round(Math.min(360, leftMargin - gutter));
		return `left:${Math.round(gutter)}px;right:auto;top:50%;bottom:auto;transform:translateY(-50%);width:${w}px;max-width:${w}px;`;
	}
	if (rightMargin >= MIN + gutter) {
		const w = Math.round(Math.min(360, rightMargin - gutter));
		return `right:${Math.round(gutter)}px;left:auto;top:auto;bottom:8vh;transform:none;width:${w}px;max-width:${w}px;`;
	}
	return '';
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
