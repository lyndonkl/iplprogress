import type { FieldHandle } from '$lib/field/field';
import { tideTotalToY, tidePoint } from '$lib/field/layout';
import type { GroupLite } from './data';

/**
 * Shared geometry for the annotation-plane tide overlays (the rising waterline,
 * the fixed 165 ghost line, the 200 / 230 reference rules, the total-axis ladder
 * and the season-axis labels). These are the SCENE's job on the SVG annotation
 * plane — never GL geometry (CONTRACT §18.3 cardinality rule). Every rule / label
 * is mapped through the EXACT shader mapping (`tideTotalToY` / `tidePoint`) then to
 * CSS px (`field.projectToCss`), so the crisp SVG and the GL skyline can never
 * drift. The overlay SVG spans the fixed viewport; coords are CSS px.
 */

export interface Pt {
	x: number;
	y: number;
}

/** The endpoints of a horizontal rule at a run total, spanning the skyline. */
export interface Rule {
	total: number;
	left: Pt;
	right: Pt;
}

export interface SeasonTick {
	gi: number;
	season: number;
	league: 'ipl' | 'wpl';
	/** the block-centre point at the baseline (total 0) */
	base: Pt;
}

export interface TideFrame {
	/** the letterboxed skyline box in CSS px */
	left: number;
	right: number;
	/** baseline (total 0) and cap (total 300) in CSS px */
	bottom: number;
	top: number;
	/** IPL / WPL block-centre x in CSS px (league headings) */
	iplMidX: number;
	wplMidX: number;
	/** the total-axis display cap (runs) */
	totalCap: number;
}

/** The skyline plot frame in CSS px, or null before the first field resize. */
export function tideFrame(field: FieldHandle): TideFrame | null {
	const t = field.getTideLayout();
	if (!t) return null;
	const bl = field.projectToCss(t.left, t.bottom);
	const tr = field.projectToCss(t.left + t.width, t.bottom + t.height);
	const iplMid = field.projectToCss(t.iplMidX, t.bottom).x;
	const wplMid = field.projectToCss(t.wplMidX, t.bottom).x;
	return {
		left: bl.x,
		right: tr.x,
		bottom: bl.y,
		top: tr.y,
		iplMidX: iplMid,
		wplMidX: wplMid,
		totalCap: t.totalCap
	};
}

/** A horizontal rule at `total` runs, spanning the skyline, in CSS px, or null. */
export function tideRule(field: FieldHandle, total: number): Rule | null {
	const t = field.getTideLayout();
	if (!t) return null;
	const y = tideTotalToY(t, total);
	return {
		total,
		left: field.projectToCss(t.left, y),
		right: field.projectToCss(t.left + t.width, y)
	};
}

/** The CSS-px point for a (season block, total) pair on the skyline, or null. */
export function tideAt(field: FieldHandle, gi: number, total: number): Pt | null {
	const t = field.getTideLayout();
	if (!t || Number.isNaN(t.xs[gi])) return null;
	const world = tidePoint(t, gi, total);
	return field.projectToCss(world.x, world.y);
}

/**
 * The season-axis ticks (block centres at the baseline), in CSS px. Pass the
 * field's `data.groups`; only blocks with a live x are returned.
 */
export function tideSeasonTicks(field: FieldHandle, groups: GroupLite[]): SeasonTick[] {
	const t = field.getTideLayout();
	if (!t) return [];
	const out: SeasonTick[] = [];
	for (const g of groups) {
		const x = t.xs[g.gi];
		if (Number.isNaN(x)) continue;
		out.push({
			gi: g.gi,
			season: g.season,
			league: g.league,
			base: field.projectToCss(x, t.bottom)
		});
	}
	return out;
}
