import type { FieldHandle } from '$lib/field/field';

/**
 * §0.4a caption-overlap safe corner (the BINDING desktop rule): on the twin-
 * rivers scenes the caption must sit in a corner that does NOT cover either
 * river, in any flowLift state. The rivers are a horizontal-ish band through the
 * vertical middle (IPL rising left→right, WPL low on the right), so a fixed
 * bottom caption would sit ON the ribbon. Rather than emit a hull, we read the
 * LIVE river geometry off the field (`getFlowLayout()` → centreline vertices,
 * sampled along each segment → `projectToCss`) and pick the corner whose caption
 * footprint overlaps the river content the least. This tracks the flowLift reveal
 * and any resize for free. Top-right is reserved for the nav ☰.
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

let warned = false;

/**
 * Pick the caption corner clear of both rivers for the LIVE flowLift. Returns
 * 'bl' as a safe default before the first resize / river table. Excludes
 * top-right (the nav lives there).
 */
export function pickCaptionCorner(field: FieldHandle | null): CornerPick {
	const fallback: CornerPick = { corner: 'tl', overlap: 0 };
	if (typeof window === 'undefined' || !field) return fallback;
	const fl = field.getFlowLayout();
	if (!fl) return fallback;

	const vw = window.innerWidth;
	const vh = window.innerHeight;
	const r = Math.max(20, Math.min(vw, vh) * 0.028);

	// obstacles: the two centrelines, sampled along each segment (so a caption
	// never lands on a long segment between two far-apart season vertices)
	const obstacles: Rect[] = [];
	const centres = fl.centres;
	const orderXs = fl.xs;
	// vertices in x order across all gis that have a river
	const gis = centres
		.map((c, gi) => ({ gi, c }))
		.filter((e) => e.c && !Number.isNaN(e.c.x) && !Number.isNaN(e.c.y))
		.sort((a, b) => orderXs[a.gi] - orderXs[b.gi]);
	const pts = gis.map((e) => field.projectToCss(e.c.x, e.c.y));
	for (let i = 0; i < pts.length; i++) {
		const p = pts[i];
		obstacles.push({ x: p.x - r, y: p.y - r, w: 2 * r, h: 2 * r });
		if (i + 1 < pts.length) {
			const q = pts[i + 1];
			for (let s = 1; s <= 3; s++) {
				const t = s / 4;
				const mx = p.x + (q.x - p.x) * t;
				const my = p.y + (q.y - p.y) * t;
				obstacles.push({ x: mx - r, y: my - r, w: 2 * r, h: 2 * r });
			}
		}
	}

	// tl and br only: the persistent legend owns bottom-left; the nav owns top-right.
	// The rising rivers leave the top-left clearest, so tl usually wins.
	const order: Corner[] = ['tl', 'br'];
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
			`[ch7] caption safe-corner '${pick.corner}' still overlaps a river by` +
				` ~${Math.round(pick.overlap)}px² — tighten the flow fill or caption size.`
		);
	}
	return pick;
}

/**
 * §0.4a for the CENTRED-PANEL exhibits (Licence, Placebo, Playbook): those beats
 * are a vertically+horizontally centred panel, not the twin-river band, so their
 * caption safe-corner is derived from the ACTUAL panel rect, not the river
 * geometry. We measure the panel and place the caption in the horizontal margin
 * BESIDE it (left preferred — the nav ☰ owns the top-right), so the caption box is
 * disjoint from the panel in x at every step and viewport, regardless of panel
 * height (the release-blocking no-overlap assert at ~1024×768). Returns '' when
 * neither margin is wide enough for a legible caption (very narrow desktop) so the
 * scene falls back to its CSS default slot; mobile uses the bottom read-then-watch
 * slot and never calls this (guarded by isNarrowViewport in the scene).
 */
export function panelCaptionStyle(panel: HTMLElement | null): string {
	if (typeof window === 'undefined' || !panel) return '';
	const r = panel.getBoundingClientRect();
	if (r.width === 0) return '';
	const vw = window.innerWidth;
	const gutter = Math.max(16, vw * 0.025);
	const MIN = 190; // a caption narrower than this is unreadable — fall back
	const leftMargin = r.left;
	const rightMargin = vw - r.right;
	if (leftMargin >= MIN + gutter) {
		const w = Math.round(Math.min(360, leftMargin - gutter));
		return `left:${Math.round(gutter)}px;right:auto;top:50%;bottom:auto;transform:translateY(-50%);width:${w}px;max-width:${w}px;`;
	}
	if (rightMargin >= MIN + gutter) {
		const w = Math.round(Math.min(360, rightMargin - gutter));
		// bottom-anchored on the right so it never rides under the top-right nav
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
