import type { FieldHandle } from '$lib/field/field';
import type { DuelWebLayout } from './data';

/**
 * §0.4a caption-overlap safe corner (the BINDING desktop rule), retuned from the
 * Ch 8 match-dots version to Chapter 9's duel-web geometry: a dense central hub
 * cluster (the IPL giant component) plus a small separate WPL sub-web up in the
 * top-right, drawn over the dust.
 *
 * Rather than emit a hull, we read the LIVE field geometry (the projected player-
 * node positions) and pick the corner whose caption footprint overlaps the on-
 * screen web the least. This tracks the strand recede, the season scrub and any
 * resize for free. Top-right is reserved for the nav AND for the WPL sub-web;
 * bottom-left is reserved for the persistent duel-web legend, so the corner pick
 * chooses between top-left and bottom-right. The hub cluster fills the middle
 * band, so top-left usually wins.
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

let warnedWeb = false;

/**
 * Pick the caption corner clear of the duel-web hub cluster (and its WPL sub-web)
 * for the LIVE layout. Samples the projected player-node positions from
 * `getDuelWebLayout()` (every Nth, so ~60 obstacle points, cheap) and projects
 * them to CSS. Returns 'tl' as a safe default before the first resize / graph
 * feed. Excludes top-right (nav + WPL sub-web) and bottom-left (the persistent
 * legend), so it chooses top-left vs bottom-right, the hub cluster fills the
 * middle, so top-left usually wins.
 */
export function pickCaptionCorner(field: FieldHandle | null): CornerPick {
	const fallback: CornerPick = { corner: 'tl', overlap: 0 };
	if (typeof window === 'undefined' || !field) return fallback;
	const dw = field.getDuelWebLayout() as DuelWebLayout | null;
	if (!dw) return fallback;

	const vw = window.innerWidth;
	const vh = window.innerHeight;
	const r = Math.max(16, Math.min(vw, vh) * 0.02);

	const obstacles: Rect[] = [];
	const nodes = dw.nodes;
	const stride = Math.max(1, Math.floor(nodes.length / 60));
	for (let i = 0; i < nodes.length; i += stride) {
		const nd = nodes[i];
		if (!nd || Number.isNaN(nd.x) || Number.isNaN(nd.y)) continue;
		const p = field.projectToCss(nd.x, nd.y);
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
	if (import.meta.env.DEV && pick.overlap > 1 && !warnedWeb) {
		warnedWeb = true;
		// eslint-disable-next-line no-console
		console.warn(
			`[ch9] caption safe-corner '${pick.corner}' still overlaps the duel web by` +
				` ~${Math.round(pick.overlap)}px², tighten the caption size.`
		);
	}
	return pick;
}

/**
 * §0.4a for the CENTRED-PANEL exhibits (the auction heartbeat, the loyalty
 * spectrum): those beats are a centred SVG panel, not the web, so the caption
 * safe-corner is derived from the ACTUAL panel rect, placed in the margin BESIDE
 * it (left preferred, the nav owns the top-right). Returns '' when neither margin
 * is wide enough for a legible caption so the scene falls back to its CSS default;
 * mobile uses the bottom read-then-watch slot and never calls this.
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
