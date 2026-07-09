/**
 * R7a PLAYER CARDS - shared voice + formatting helpers (pure, no DOM).
 *
 * Every string the card shows in-voice funnels through here so the register stays
 * consistent and the honesty rules (plain glosses, era-relative framing, no
 * greatness-score language) live in one place. ZERO em dashes / en dashes: ranges
 * use a plain hyphen, separators use the middle dot.
 */

import type { EntryRole, League, PlayerRole } from './data';

/** Thousands-separated integer, e.g. 6926 -> "6,926". */
export function fmtInt(n: number): string {
	return Math.round(n).toLocaleString('en-US');
}

/** Strike-rate / SR+ style number to one decimal, e.g. 112.264 -> "112.3". */
export function fmt1(n: number): string {
	return n.toFixed(1);
}

/** League display name. */
export function leagueName(l: League): string {
	return l === 'wpl' ? 'WPL' : 'IPL';
}

/** Role badge word. */
export function roleWord(role: PlayerRole): string {
	if (role === 'bat') return 'Batter';
	if (role === 'bowl') return 'Bowler';
	return 'All-rounder';
}

/** "RCB", "RCB and RR", "MI, RR, GT" (no serial dashes). */
export function teamsLabel(teams: string[]): string {
	if (teams.length === 0) return '';
	if (teams.length === 1) return teams[0];
	if (teams.length === 2) return `${teams[0]} and ${teams[1]}`;
	return teams.join(', ');
}

/** "2008-2024", or a single year when the span is one season. */
export function seasonsLabel(first: number, last: number): string {
	return first === last ? String(first) : `${first}-${last}`;
}

/** The brightest-entry-cell role, as a full callout sentence. */
export function entryRolePhrase(role: EntryRole): string {
	switch (role) {
		case 'opener':
			return 'An opener.';
		case 'top-order':
			return 'A top-order bat.';
		case 'finisher':
			return 'A finisher.';
		case 'middle-order':
			return 'A middle-order bat.';
		default:
			return 'A floater, up and down the order.';
	}
}

/** The same role as a short phrase for the collapsed teaser line. */
export function entryRoleShort(role: EntryRole): string {
	switch (role) {
		case 'opener':
			return 'opening';
		case 'top-order':
			return 'near the top';
		case 'finisher':
			return 'at the death';
		case 'middle-order':
			return 'in the middle';
		default:
			return 'all over the order';
	}
}

/** Wickets-already-down of an entry cell, in fan language. */
export function wicketsPhrase(wickets: number, plus: boolean): string {
	if (wickets === 0) return 'none down';
	if (plus) return `${wickets} or more down`;
	return wickets === 1 ? '1 down' : `${wickets} down`;
}

/** A 2-over entry bin as 1-indexed fan overs, e.g. bin [0,1] -> "overs 1-2". */
export function overRangePhrase(lo: number, hi: number): string {
	return `overs ${lo + 1}-${hi + 1}`;
}

/** The others a pid was also recorded under (canonical excluded); "" if none. */
export function aliasLine(name: string, aliases: string[]): string {
	const others = aliases.filter((a) => a !== name);
	return others.length ? `also recorded as ${others.join(', ')}` : '';
}
