import type { FieldHandle } from '$lib/field/field';

/**
 * §0.4a caption-overlap safe corner (the BINDING desktop rule), retuned from the
 * Ch 9 duel-web version to Chapter 10's RIBBON geometry.
 *
 * The ribbon is a thin horizontal band centred vertically (computeRibbon puts its
 * centre at the world origin), with a time-axis tick-lane just under it, the
 * seismograph strip / verdict panels / fault-map subway drawn in the vertical
 * space above or below it, and the strictness dial along the bottom. So the four
 * screen corners are all clear of the band's centre line; the storyboard assigns
 * each scene a named corner (C10-2 upper-left, C10-3 lower-right, C10-4 upper-
 * right, C10-5 lower-left, C10-6 upper-left/right, C10-7 lower-left) already
 * chosen clear of that scene's exhibit and of the top-right nav.
 *
 * Rather than emit a hull, we read the LIVE ribbon band rect (from getRibbonLayout
 * projected to CSS) and, given a scene's PREFERRED corner, keep it unless its
 * caption footprint would cover the band; then we fall to the diagonal corner.
 * This tracks resize and the letterbox for free. Top-right is always reserved for
 * the nav, so a preferred 'tr' only survives when nothing better is asked for.
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

function intersects(a: Rect, b: Rect): boolean {
	return !(a.x + a.w < b.x || b.x + b.w < a.x || a.y + a.h < b.y || b.y + b.h < a.y);
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

/** The diagonal fallback for a preferred corner (never lands back on the nav). */
function diagonal(corner: Corner): Corner {
	return corner === 'tl' ? 'br' : corner === 'tr' ? 'bl' : corner === 'bl' ? 'tr' : 'tl';
}

/**
 * Pick the caption corner for a scene: keep the storyboard's PREFERRED corner
 * unless its caption footprint would cover the live ribbon band, in which case
 * fall to the diagonal. Returns the preferred corner unchanged before the first
 * resize (getRibbonLayout null), so SSR / first paint are stable.
 */
export function pickRibbonCorner(field: FieldHandle | null, preferred: Corner): Corner {
	if (typeof window === 'undefined' || !field) return preferred;
	const rib = field.getRibbonLayout();
	if (!rib) return preferred;
	const top = field.projectToCss(rib.box.left, rib.box.bandY + rib.box.bandHalf);
	const bot = field.projectToCss(rib.box.left, rib.box.bandY - rib.box.bandHalf);
	const right = field.projectToCss(rib.box.left + rib.box.width, rib.box.bandY);
	const bandRect: Rect = {
		x: Math.min(top.x, right.x),
		y: Math.min(top.y, bot.y),
		w: Math.abs(right.x - top.x),
		h: Math.abs(bot.y - top.y)
	};
	const vw = window.innerWidth;
	const vh = window.innerHeight;
	if (!intersects(captionRect(preferred, vw, vh), bandRect)) return preferred;
	const alt = diagonal(preferred);
	return intersects(captionRect(alt, vw, vh), bandRect) ? preferred : alt;
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
