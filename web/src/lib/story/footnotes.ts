/**
 * The typed footnote registry — the "how we computed this" layer (blueprint
 * §2: progressive disclosure; the technical names live here, one click deep,
 * never in main flow). Scenes reference entries by id via SceneDef.footnote;
 * the shell renders the per-scene affordance and FootnotePanel.
 *
 * Scene builders: add entries here (typed — a bad id is a compile error) and
 * keep every on-screen banned term (§0.4) out of main flow. Inside a sheet,
 * technical names are introduced as "the technical name for this".
 */

export interface FootnoteEntry {
	/** panel heading, fan-legible */
	title: string;
	/** paragraphs of plain text (no markup — keep the layer honest and simple) */
	paragraphs: string[];
}

export const FOOTNOTES = {
	'draw-200': {
		title: 'What counts as a 200-run innings',
		paragraphs: [
			'A 200-run innings is any innings total of 200 or more, by either batting side — first innings or chase. Super-over innings are excluded. The chart counts how many such innings each season produced.',
			'Why counts, not averages: an average smooths the ceiling out of the picture. What changed is how often somebody blows straight past 200 — a count shows that directly. 2008–2012 produced 31 of them; 2026 alone produced 65.',
			'Prefer the classical framing? The share of first innings reaching 200 rose from 7.7% in 2008-10 to 41.9% in 2023-26 — and hit 52% in 2026.'
		]
	},
	'ball-count': {
		title: 'What counts as a ball',
		paragraphs: [
			'Every legal and illegal delivery recorded by Cricsheet, except super-over deliveries. The corpus holds 316,388 deliveries; 189 of them belong to the 17 tie-match super overs (36 super-over innings) and are excluded from the field — what you see is exactly 316,199. (House rule: never show a number the pixels contradict.)',
			'Wides don’t count toward a batter’s balls faced; no-balls do. That convention is used throughout the piece.',
			'Data source: Cricsheet ball-by-ball JSON. Season labels are normalized (2007/08→2008, 2009/10→2010, 2020/21→2020).'
		]
	},
	'ignition-wall': {
		title: 'How the wall is built',
		paragraphs: [
			'Every ball is placed by how long its batter had been in when it was bowled: the x-axis is the batter’s balls-faced count (1 at the left, a capped 30+ bucket at the right edge), and each row is a season — 2008 at the bottom, 2026 at the top, with the WPL’s four seasons on their own shelf above.',
			'Wides are not balls faced; no-balls are. Brightness is runs off the bat — hue never encodes a quantity.',
			'The era bands behind the chip: IPL 2008-2010 (the league’s first three seasons) versus 2023-2026 (its last four). The middle bands — 2011-2015, 2016-2019, 2020-2022 — are computed too and drive the payoff cards.',
			'Exact figures: strike rate on the first ten balls of an innings, 108.0 in 2008-2010 → 135.3 in 2023-2026. Sample sizes: 20,101 first-ten balls across 2,733 batter-innings then; 33,882 across 4,579 now.',
			'The start of the innings outgrew the game itself: the first-ten-ball strike rate rose about +25% while the all-innings strike rate rose about +21% — the revolution concentrates at the top.',
			'The wall is computed on your device from two small per-ball attributes; no positions are downloaded.'
		]
	},
	sixes: {
		title: 'Counting the sixes',
		paragraphs: [
			'A six is any ball the batter hit for six (runs off the bat, not extras). The columns chart counts every IPL six by season; behind the rounded “every 21 → every 12” sit 20.8 balls per six in 2008 and 11.7 in 2026.',
			'Seasons grew too — more matches, more balls (13,489 deliveries in 2008 versus far more now) — so raw six counts flatter the modern game; the per-ball rate is the honest comparison, and it is the one the caption quotes.',
			'The “big swings” pair uses an aerial-attempt proxy: attempts = sixes + caught dismissals (caught-and-bowled excluded) per 100 balls; execution = sixes ÷ (sixes + caught). Caught includes keeper and slip edges — the data carries no fielding positions — a fixed noise floor that leaves era-over-era comparisons valid so long as edge rates are stable. True shot-level intent would need non-public ball-tracking.',
			'Attempts rose as well as landings: 7.3 per 100 balls (2008-2010) → 11.4 (2023-2026), about +56%, while execution rose 58.7% → 67.3%.',
			'The shrinking specialists’ slice, quantified: the top-10 hitters’ share of league sixes fell 35.9% (2008) → 28.1% (2026); players with ten-plus sixes in a season rose 18 → 58.',
			'The technical name for the spread: the season-by-season concentration of six-hitting (a Gini coefficient over batters with at least 30 balls faced) fell from 0.49-0.54 in the early years to 0.40-0.46 in 2024-26.'
		]
	},
	'out-rate': {
		title: 'The out-rate, ball by ball',
		paragraphs: [
			'The technical name for this is a discrete-time hazard curve, estimated Kaplan-Meier-style: for each ball of a batter’s innings, the share of innings that reached that ball and ended on it.',
			'Innings that ended not-out are censored — they stop counting once they stop being observed. Retired-hurt innings (10 in the corpus) and tactical retired-out innings (5) are censored too, never counted as dismissals.',
			'The out-rate is risk per ball; strike rate is runs per ball. They move independently — which is exactly the point of Chapter 1.',
			'Conventions: wides don’t count toward balls faced (a batter can still be out on one, and that dismissal counts); no-balls do. The first-ten-balls headline — 5.04% then, 4.93% now — counts every dismissal at a faced-count of ten or fewer. Per-era samples: 2,733 batter-innings and 20,101 first-ten balls (2008-2010); 4,579 and 33,882 (2023-2026).',
			'A demoted exhibit — the over as a clock face: even inside the over the sighter died. 2008-10 overs ran quiet-loud-quiet: the over’s first ball scored at a 7.34 run rate with a ball-three peak of 8.02. 2023-26 overs start hot and fade: ball one at 9.20, ball six at 8.89.',
			'The environment moved too — pitches, rules (the 2023 Impact Player among them). Chapters 4, 7 and 10 apportion the credit; the early-innings out-rate stayed flat across all of it.'
		]
	},
	'wpl-two-clocks': {
		title: 'Two clocks, one beat',
		paragraphs: [
			'Sample honesty: the WPL is 88 matches and 20,642 deliveries across four seasons — young curves that will move as the league plays.',
			'The six-share companion to the fours pair: 15.5% of WPL runs come in sixes versus 29.0% in the modern IPL. A different engine, not a smaller one — a four-led attack the men’s league never played at any age.',
			'Why “behind” is the wrong word: the leagues differ in outcome mix (where the runs come from), not just outcome rate (how many). Reading a four-season league’s numbers against a nineteen-season league’s timeline confuses those two clocks. Chapter 6 — Two Dialects — gives this the full treatment.',
			'Aerial execution sits here too: WPL execution on big swings is 54.5%, at intent-era IPL levels (same proxy and caveats as the sixes sheet).'
		]
	},
	'payoff-ch1': {
		title: 'Behind the payoff card',
		paragraphs: [
			'Team pools show their per-era ball counts on the card (the Sample line). Fastest-starter lines require at least 100 first-ten balls faced for that franchise. Teams born after 2010 (Gujarat Titans, Lucknow Super Giants, Sunrisers Hyderabad) get a designed empty state instead of a fabricated early era.',
			'Franchise renames merge histories: Delhi Daredevils → Delhi Capitals, Kings XI Punjab → Punjab Kings, Royal Challengers Bangalore → Bengaluru. Defunct franchises (Deccan Chargers, Kochi Tuskers Kerala, the Pune entities, Gujarat Lions) stay distinct — they are not folded into current teams.',
			'Behind the WPL card’s league clock: at the same league age (years 1-4), the IPL’s run rate went 8.31 → 7.73; year by year, IPL 8.31 / 7.48 / 8.13 / 7.73 and WPL 8.08 / 7.86 / 8.37 / 8.54. Both paths are non-monotonic — endpoints alone flatter both. WPL era bands on the card are 2023-2024 versus 2025-2026. Early days for a young league — small sample, honest numbers.'
		]
	}
} as const satisfies Record<string, FootnoteEntry>;

export type FootnoteId = keyof typeof FOOTNOTES;

export function isFootnoteId(id: string | null): id is FootnoteId {
	return id !== null && Object.prototype.hasOwnProperty.call(FOOTNOTES, id);
}
