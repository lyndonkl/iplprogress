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

/* ==========================================================================
 * R7b CREDIBILITY LAYER voice strings (additive; §9.1 / 9.2 / 9.3 / 9.4 / 9.5)
 *
 * Each cue names its stat + n vs its own stabilization M (never a global
 * "trust score"). Half-life is named to its metric (the dated SR+ recount, not
 * the catalog teaser). Curly apostrophes use the ’ escape so they read as
 * typographic apostrophes, never a stray dash. Zero em / en dashes anywhere.
 * ========================================================================== */

/**
 * §9.5 - the SR+ peak's SEPARATE trust line (one idea, one number). The peak
 * `.point` carries the SR+ value; this note carries the sample read: how the
 * peak season's balls sit against the ~95 a strike rate needs to settle.
 */
export function peakTrustNote(balls: number, m: number): string {
	const need = Math.round(m);
	const stance = balls >= m ? 'well past' : 'still short of';
	return `That is off ${fmtInt(balls)} balls, ${stance} the roughly ${need} a strike rate needs to settle.`;
}

/**
 * §9.2 - the freshness SENTENCE folded into the teleporter note (never an arc
 * gauge, no retained% number). One load-bearing number, named to the metric,
 * rounded to "about {H} seasons" on the card face.
 */
export function freshnessNote(gap: number, halfLife: number, targetSeason: number): string {
	const h = Math.round(halfLife);
	const gs = gap === 1 ? 'season' : 'seasons';
	const hs = h === 1 ? 'season' : 'seasons';
	return `This peak is ${gap} ${gs} before ${targetSeason}. A strike rate’s edge fades by about half every ${h} ${hs}, so read this as a soft echo, not a like-for-like.`;
}

/**
 * §9.3 - the static 80% CI on the batter's CAREER SR+ (no slider on the card).
 * `raw` is the career SR+ as it happened; `lo`/`hi` bracket the true-skill guess.
 */
export function careerCILine(raw: number, lo: number, hi: number): string {
	return `Career SR+ ${fmt1(raw)}, and the model is 80% sure the true figure sits between ${fmt1(lo)} and ${fmt1(hi)}.`;
}

/**
 * §9.4 - TrueEcon river orient line: the 100 baseline reads UP = better, so it
 * mirrors the SR+ river with no relearning.
 */
export function trueEconOrient(league: League): string {
	return `100 is a par ${leagueName(league)} bowler that season. Above the line means they leaked fewer runs than their era’s peers, priced against their own era, not today’s.`;
}

/** §9.4 - the runs-saved reading as the peak's caption GLOSS (not an axis). */
export function trueEconPeakGloss(runsSaved: number): string {
	return `Saving about ${fmt1(runsSaved)} runs an over versus par.`;
}

/** §9.4 - honest gloss for a bowler whose best season still sat under era par. */
export function trueEconPeakBelowPar(runsOver: number): string {
	return `Even that sat under par, about ${fmt1(runsOver)} runs an over above era peers.`;
}

/**
 * §9.1 - the river trust legend, shown only when a non-settled dot is present.
 * Describes the SHAPE channel (hollow vs filled) so the cue is CVD-safe.
 */
export function trustLegend(hasNoisy: boolean): string {
	return hasNoisy
		? 'A hollow dot is a season still settling, too few balls to trust yet.'
		: 'A dimmer dot is a season still settling, just short of the balls it needs.';
}
