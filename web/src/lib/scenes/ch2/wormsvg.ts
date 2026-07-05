import type { FieldHandle } from '$lib/field/field';
import { wormPoint } from '$lib/field/layout';

/**
 * Shared geometry for the annotation-plane worms (C2-2 / C2-3 / C2-8). The par
 * worm, the K anchor exemplar worms and the axes are the SCENE's job on the SVG
 * annotation plane — never thousands of GL polylines (CONTRACT §13.3 cardinality
 * rule). Each worm vertex is mapped through the EXACT shader mapping
 * (`wormPoint`) then to CSS px (`field.projectToCss`), so the crisp SVG worms
 * and the GL density haze can never drift. The overlay SVG spans the fixed
 * viewport (like Wall.svelte's projected scaffold); points are CSS px.
 */

export interface Pt {
	x: number;
	y: number;
}

/** A worm as an SVG points string (CSS px), from a cumulative-runs array
 *  (index i = cumulative batter runs after ball i+1). Empty until worm layout. */
export function wormPolyline(field: FieldHandle, cumRuns: number[]): string {
	const w = field.getWormLayout();
	if (!w || cumRuns.length === 0) return '';
	let out = '';
	for (let i = 0; i < cumRuns.length; i++) {
		const world = wormPoint(w, i + 1, cumRuns[i]);
		const css = field.projectToCss(world.x, world.y);
		out += `${css.x.toFixed(1)},${css.y.toFixed(1)} `;
	}
	return out.trimEnd();
}

/** The last vertex of a worm (for the direct end-label), or null. */
export function wormEnd(field: FieldHandle, cumRuns: number[]): Pt | null {
	const w = field.getWormLayout();
	if (!w || cumRuns.length === 0) return null;
	const world = wormPoint(w, cumRuns.length, cumRuns[cumRuns.length - 1]);
	return field.projectToCss(world.x, world.y);
}

export interface WormFrame {
	/** the plot box in CSS px */
	left: number;
	right: number;
	bottom: number;
	top: number;
	/** x-axis ball ticks: { ball, x } */
	xticks: { ball: number; label: string; x: number }[];
	/** y-axis run ticks: { runs, y } */
	yticks: { runs: number; y: number }[];
	xCap: number;
	runsCap: number;
}

/** The worm-space plot frame + axis ticks in CSS px, or null before layout. */
export function wormFrame(field: FieldHandle): WormFrame | null {
	const w = field.getWormLayout();
	if (!w) return null;
	const bl = field.projectToCss(w.left, w.bottom);
	const tr = field.projectToCss(w.left + w.width, w.bottom + w.height);
	const xat = (ball: number): number =>
		field.projectToCss(wormPoint(w, ball, 0).x, w.bottom).x;
	const yat = (runs: number): number =>
		field.projectToCss(w.left, wormPoint(w, 1, runs).y).y;
	const xBalls = [1, 15, 30, 45, w.xCap];
	const xticks = xBalls.map((ball) => ({
		ball,
		label: ball >= w.xCap ? `${w.xCap}+` : String(ball),
		x: xat(ball)
	}));
	const yRuns = [0, 25, 50, 75, 100];
	const yticks = yRuns.map((runs) => ({ runs, y: yat(runs) }));
	return {
		left: bl.x,
		right: tr.x,
		bottom: bl.y,
		top: tr.y,
		xticks,
		yticks,
		xCap: w.xCap,
		runsCap: w.runsCap
	};
}
