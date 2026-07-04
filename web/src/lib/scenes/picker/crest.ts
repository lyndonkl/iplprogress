/**
 * Typographic-crest color helpers (storyboard §2: no logo assets — the crest
 * is the short code on a franchise-color chip). Hue stays identity-only; these
 * helpers only adjust luminance so identity colors stay legible on the dark
 * stage (standing rule: luminance is the quantity channel, hue never is —
 * lifting a dark navy to a readable tint changes no meaning).
 */

const HEX_RE = /^#([0-9a-f]{6})$/i;

export function parseHex(hex: string): [number, number, number] | null {
	const m = HEX_RE.exec(hex.trim());
	if (!m) return null;
	const v = parseInt(m[1], 16);
	return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}

function luma(rgb: [number, number, number]): number {
	return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
}

/** Text color for a chip painted in the team color: ink on dark, near-black on light. */
export function crestText(hex: string): string {
	const rgb = parseHex(hex);
	if (!rgb) return '#e8ecf5';
	return luma(rgb) > 145 ? '#0b0e14' : '#e8ecf5';
}

/**
 * The team hue lifted just enough to read as a thin line / selection ring on
 * the dark background (GT navy #1B2133 is invisible at 1.5px otherwise).
 * Colors that are already bright pass through untouched.
 */
export function lineTint(hex: string): string {
	const rgb = parseHex(hex);
	if (!rgb) return '#e8a33d';
	if (luma(rgb) >= 90) return hex;
	const t = 0.55; // mix toward the page ink, keeping the hue family
	const r = Math.round(rgb[0] + (232 - rgb[0]) * t);
	const g = Math.round(rgb[1] + (236 - rgb[1]) * t);
	const b = Math.round(rgb[2] + (245 - rgb[2]) * t);
	return `rgb(${r}, ${g}, ${b})`;
}
