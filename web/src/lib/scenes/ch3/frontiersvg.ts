import type { FieldHandle } from '$lib/field/field';
import { frontierPoint } from '$lib/field/layout';

/**
 * Shared geometry for the annotation-plane frontier overlays (C3-2 / C3-3): the
 * axes, the "edge of the possible" (per-season Pareto hull), the ghost trail and
 * the seven-an-over reference line are the SCENE's job on the SVG annotation
 * plane — never GL geometry (CONTRACT §15.4 cardinality rule; hull vertices are a
 * build-time lookup in ch3.json). Each data point (raw economy + strike rate) is
 * mapped through the EXACT shader mapping (`frontierPoint`) then to CSS px
 * (`field.projectToCss`), so the crisp SVG and the GL density haze can never
 * drift. The overlay SVG spans the fixed viewport; points are CSS px.
 */

export interface Pt {
	x: number;
	y: number;
}

/** A single (economy, strike-rate) data point as a CSS-px point, or null. */
export function frontierPt(field: FieldHandle, economy: number, strikeRate: number): Pt | null {
	const fl = field.getFrontierLayout();
	if (!fl) return null;
	const world = frontierPoint(fl, economy, strikeRate);
	return field.projectToCss(world.x, world.y);
}

/** A hull edge / ghost trail as an SVG points string (CSS px), sorted as given. */
export function frontierPolyline(
	field: FieldHandle,
	points: { economy: number; strike_rate: number }[]
): string {
	const fl = field.getFrontierLayout();
	if (!fl || points.length === 0) return '';
	let out = '';
	for (const p of points) {
		const world = frontierPoint(fl, p.economy, p.strike_rate);
		const css = field.projectToCss(world.x, world.y);
		out += `${css.x.toFixed(1)},${css.y.toFixed(1)} `;
	}
	return out.trimEnd();
}

/** Per-point CSS coords for a hull / ghost list (for dots + tap targets). */
export function frontierDots<T extends { economy: number; strike_rate: number }>(
	field: FieldHandle,
	points: T[]
): (Pt & { source: T })[] {
	const fl = field.getFrontierLayout();
	if (!fl) return [];
	return points.map((p) => {
		const world = frontierPoint(fl, p.economy, p.strike_rate);
		const css = field.projectToCss(world.x, world.y);
		return { ...css, source: p };
	});
}

export interface FrontierFrame {
	/** the plot box in CSS px */
	left: number;
	right: number;
	bottom: number;
	top: number;
	/** the seven-an-over vertical line's CSS x */
	sevenX: number;
	/** the "cheap and deadly" home-zone box in CSS px */
	home: { left: number; right: number; top: number; bottom: number };
	/** economy (x) axis ticks: label + CSS x */
	xticks: { label: string; x: number }[];
	/** strike-rate (y) axis ticks: label + CSS y */
	yticks: { label: string; y: number }[];
}

const ECON_TICKS = [4, 7, 10, 13, 16];
const SR_TICKS = [8, 20, 30, 40, 60];

/** The frontier plot frame + axis ticks + landmarks in CSS px, or null. */
export function frontierFrame(field: FieldHandle): FrontierFrame | null {
	const fl = field.getFrontierLayout();
	if (!fl) return null;
	const bl = field.projectToCss(fl.left, fl.bottom);
	const tr = field.projectToCss(fl.left + fl.width, fl.bottom + fl.height);
	const sevenCss = field.projectToCss(fl.sevenX, fl.bottom).x;
	const h0 = field.projectToCss(fl.home.x0, fl.home.y0); // bottom-left
	const h1 = field.projectToCss(fl.home.x1, fl.home.y1); // top-right of the box
	const xat = (econ: number): number => field.projectToCss(frontierPoint(fl, econ, fl.srLo).x, fl.bottom).x;
	const yat = (sr: number): number => field.projectToCss(fl.left, frontierPoint(fl, fl.econLo, sr).y).y;
	// the top economy tick is the clamp bucket (values above it pile onto it), so
	// flag it '16+' to match the strike-rate axis's '60+' cap (honesty parity)
	const xticks = ECON_TICKS.map((e) => ({ label: e >= fl.econHi ? `${e}+` : String(e), x: xat(e) }));
	const yticks = SR_TICKS.map((s) => ({ label: s >= fl.srHi ? `${s}+` : String(s), y: yat(s) }));
	return {
		left: bl.x,
		right: tr.x,
		bottom: bl.y,
		top: tr.y,
		sevenX: sevenCss,
		home: { left: h0.x, bottom: h0.y, right: h1.x, top: h1.y },
		xticks,
		yticks
	};
}
