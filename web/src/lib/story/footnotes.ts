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

/**
 * An optional small static 2D figure a footnote may carry (storyboard C1-4's
 * "Over as a Clock Face" demoted exhibit). Data-only — no markup — so the
 * registry stays plain-text-friendly; FootnotePanel owns the rendering. Only
 * the 'over-clock' radial exists in R1a; the union grows as scenes need it.
 */
export interface OverClockFigure {
	kind: 'over-clock';
	/** balls per over on the dial (6) */
	balls: number;
	/** radial axis maximum, run-rate units */
	max: number;
	/**
	 * one entry per era line. `points` carries ONLY verified (ball, rr) anchors
	 * — the renderer marks and labels exactly those, never inventing the
	 * unmeasured balls between them (honesty invariant: no on-screen number
	 * without a source).
	 */
	series: { label: string; tone: 'ghost' | 'bold'; points: { ball: number; rr: number }[] }[];
	/** one-line reading of the figure */
	caption: string;
}

export type FootnoteFigure = OverClockFigure;

export interface FootnoteEntry {
	/** panel heading, fan-legible */
	title: string;
	/** paragraphs of plain text (no markup — keep the layer honest and simple) */
	paragraphs: string[];
	/** optional small static 2D figure rendered below the prose (C1-4 radial) */
	figure?: FootnoteFigure;
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
			'Wides are not balls faced; no-balls are. In the establishing shot, brightness is runs off the bat and hue is the outcome — dot, single, four, six.',
			'The thesis recolour: in the second half of the wall each ball is re-tinted by how hard it was hit versus a 2008-2010 batter at the very same point in the innings. For every balls-faced column — ball 1, ball 2, and so on — the pooled 2008-2010 strike rate at that ball-count is the neutral pivot; a cell (one season × one ball-count) reads cool when it sits at or below its 2008-2010 mark and hot when it runs well above it.',
			'Why baseline each column to its own 2008-2010 value: batters always speed up once they are set, so raw strike rate climbs across the first twenty-odd balls in every era — a left-to-right gradient that swamps the year-on-year change in colour. Subtracting the 2008-2010 batter at each ball-count cancels that shared acceleration and leaves only the era difference, so the early-ball corner ignites bottom-to-top exactly where recent seasons most exceed 2008.',
			'The scale is diverging: deep blue below the 2008-2010 batter, grey-blue at it, amber-to-red well above. The chip’s exact figures — strike rate on the first ball of the innings — 73.7 in 2008-2010 → 95.5 in 2023-2026. Pooled over the first ten balls it is 108.0 → 135.3.',
			'The era bands: IPL 2008-2010 (the league’s first three seasons, the recolour baseline) versus 2023-2026 (its last four). The middle bands — 2011-2015, 2016-2019, 2020-2022 — are computed too and drive the payoff cards. Sample sizes on the first ten balls: 20,101 across 2,733 batter-innings then; 33,882 across 4,579 now.',
			'The start of the innings outgrew the game itself: the first-ten-ball strike rate rose about +25% while the all-innings strike rate rose about +21% — the revolution concentrates at the top.',
			'The wall is computed on your device from three small per-ball attributes (balls faced, season, and the era-relative heat byte); no positions are downloaded.'
		]
	},
	sixes: {
		title: 'Counting the sixes',
		paragraphs: [
			'A six is any ball the batter hit for six (runs off the bat, not extras). Each firework column is that season’s real IPL sixes; the raw heights run 623 in 2008 to 1,426 in 2026, and behind the rounded “every 21 → every 12” sit 20.8 balls per six then and 11.7 now.',
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
		],
		figure: {
			kind: 'over-clock',
			balls: 6,
			max: 10,
			series: [
				{
					label: '2008-10',
					tone: 'ghost',
					points: [
						{ ball: 1, rr: 7.34 },
						{ ball: 3, rr: 8.02 }
					]
				},
				{
					label: '2023-26',
					tone: 'bold',
					points: [
						{ ball: 1, rr: 9.2 },
						{ ball: 6, rr: 8.89 }
					]
				}
			],
			caption:
				'Run rate by ball of the over. 2008-10 ran quiet-loud-quiet (a ball-three peak); 2023-26 starts hot off ball one and eases. Only the verified balls are marked.'
		}
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
	},

	/* ---- Chapter 2 — The Last of the Anchors (r2a) --------------------------
	 * Prose numbers below are documented constants that MATCH ch2.json exactly
	 * (the ch1 footnote convention — the "how we computed this" layer carries the
	 * verified figures as text; every MAIN-FLOW number is data-bound to ch2.json).
	 * Where the artifact and the blueprint teaser diverge, these track the
	 * ARTIFACT (occupancy 39.3 not 38.7, run-out 4.7 not 4.6, tax 1.13→1.30,
	 * incoming SR 95→119). */
	'anchor-definition': {
		title: 'What counts as an anchor',
		paragraphs: [
			'The technical name is an anchor innings: a batter innings of at least 15 balls faced whose strike rate ran below 0.85× the day’s going rate — the season-and-phase par strike rate, each league priced against its own baseline — with boundary balls (four or six off the bat) under 12% of the balls faced.',
			'Why 0.85× the day’s rate, not a fixed strike-rate cutoff: a strike rate of 120 meant something very different in 2009 than in 2026. The bar has to move with the era, or you just measure how much the whole league sped up. (The fixed-bar version is the raw sub-120 cut — see the anchor-decline sheet — and it is a different, less honest number.)',
			'The finding survives the reasonable cuts. Loosening or tightening the slowness bar (0.80× / 0.85× / 0.90× of the day’s rate) and the boundary cap (10% / 12% / 15% of balls) moves the exact percentages but not the shape: the anchor thins out across the era every way you slice it.',
			'“The worm” is the broadcast term for a cumulative-runs line — runs on the vertical, balls faced on the horizontal. A steep worm is fast scoring; a flat one is an anchor. Balls faced excludes wides; the day’s going rate is priced on legal deliveries (a scorecard strike rate).'
		]
	},
	'anchor-extinction': {
		title: 'How the anchor decline is counted',
		paragraphs: [
			'The headline is era-relative: the share of every ball bowled in a season that was consumed by an anchor innings (as defined in the anchor sheet). It fell from 14.8% across the league’s first three seasons (2008-2010) to 8.5% across its last four (2023-2026) — a decline of roughly 43%.',
			'A blunter, fixed-bar version you may have seen: the share of qualifying batter-seasons (100+ balls) whose whole-season strike rate stayed under 120 fell from 39.3% (2008-2010) to 2.4% (2023-2026). That looks like a ~94% collapse — but 120 is a FIXED bar the whole league simply outgrew, not an era-relative measure. The two numbers diverge precisely because one moves with the era and one does not; they do not corroborate each other, which is why the main flow carries only the era-relative 14.8 → 8.5.',
			'How much of the decline is intent (batters choosing to attack), how much is selection (teams no longer picking accumulators), and how much is rules is not cleanly separable, and the chapter does not claim it is. In particular the Impact Player substitute (2023+) makes losing a wicket cheaper and lands squarely on the 2023-2026 end of the curve — a structural rule change entangled with the batter-and-team-choice story at exactly the point the extinction completes.',
			'The “last surviving anchors” are real qualifying innings from the final seasons, named from the pipeline — the magnitude claim (“few enough to name”) rides that list and the population chart, never the illustrative worm thicket, which is a sample per season, not a headcount. Era bands: 2008-2010 versus 2023-2026.'
		]
	},
	'runout-extinction': {
		title: 'Counting the run-outs',
		paragraphs: [
			'Run-out share is the number of dismissals of kind “run out” as a share of all non-retired dismissals that season (retired hurt / retired out are censored, never counted as wickets). It fell from 12.3% of wickets in 2008 to 4.7% in 2026.',
			'The run-out decomposes by which end was given out: striker versus non-striker (from who was dismissed). Across 2008-2010, 142 strikers to 112 non-strikers were run out (44.1% non-striker); the mix drifts season to season on small counts.',
			'This is fewer risky singles PLUS safer running, not one alone — and it is a league-wide trend, not the anchor’s personal doing. Break-Even Running (the demoted mechanism note): run-outs per 1,000 legal balls roughly halved, 6.4 → 2.8, while the rate of twos held essentially flat, 7.8 → 7.6 per 100 non-boundary balls. Running didn’t atrophy; it got safer at constant aggression — so the “risky two” never stopped; only the frequency and value of the scampered single fell. The “gone together” line is a real co-decline of two era trends, not the anchor causing the run-out to die.',
			'Direct-hit and fielding detail would need a fielders array that is sparse or missing for stretches (gaps cluster around 2018-2021), so that cut is handled cautiously and not headlined.'
		]
	},
	'gear-shift': {
		title: 'The shape of an innings',
		paragraphs: [
			'The technical name is an innings-shape taxonomy over innings of at least 25 balls faced. The headline “two-act” share counts innings whose second-half strike rate ran at least 1.5× the first half (split by balls faced) — the classic crawl-then-launch. It fell from 33.7% of long innings in 2008-2010 to 24.1% in 2023-2026.',
			'A companion thirds lens tells the same story from the other side: “flat-max” innings — the three thirds’ strike rates all within 1.25× of each other, one gear held the whole way — are now the modal long innings, rising to 11.6% while the rising-across-thirds “three-act” shape fell.',
			'This isn’t a sampling artifact: the share of innings that even reach 25 balls is era-stable, so the change is in the shape of long innings, not in how many there are. The two exemplar worm shapes on screen are an illustration of the taxonomy, not specific field points.'
		]
	},
	'new-batter-tax': {
		title: 'What a wicket still costs',
		paragraphs: [
			'The New-Batter Tax is the team’s runs-per-over shortfall over the 10 legal balls after each dismissal, measured against the season-and-phase par for that window (full windows only — dismissals within 10 balls of the innings end are trimmed). It did not shrink: −1.13 runs per over below the day’s rate in 2008-2010, −1.30 in 2023-2026 — a slight DEEPENING, which is what makes it the one cost the revolution couldn’t kill.',
			'A note on baselines: that is the ABSOLUTE gap, and it deepened even as the day’s going rate itself rose (from 7.74 to 9.20 runs per over). As a SHARE of the going rate the tax is roughly flat — about 15% in both eras — so “deepened” is the honest word for the absolute gap and “un-killed” for the relative one; either way the revolution couldn’t erase it.',
			'The incoming batter, meanwhile, walks in swinging far harder than ever: strike rate on the first five balls faced after a wicket rose from about 95 (2008-2010) to about 119 (2023-2026), roughly a 25% jump — yet the team still stalls the moment a new man arrives. The cost is structural (a new batter set-up, a field reset), not a failure of nerve.',
			'The absolute level tracks the par baseline used: this season-and-phase stand-in yields ~1.1 → ~1.3, and the catalog’s wickets-in-hand-conditioned par yields 1.22 → 1.40; the level converges when engine #1’s conditioned table replaces the stand-in. The direction — a slight deepening — is the same either way. The WPL comparison stays open (not enough post-wicket WPL cricket yet for a clean number).',
			'A second, deliberately demoted nerd-nugget — the Milestone Braking Index: batters still ease off approaching a landmark like a fifty, and if anything more so now than in 2008. It is not a rival coda; the full index lives in the methods pages.'
		]
	},
	'wpl-two-clocks-ch2': {
		title: 'Two clocks, one beat (the anchor and the run-out)',
		paragraphs: [
			'Sample honesty: the WPL is four seasons young — about 19,988 legal balls faced in the anchor computation — so these curves will move as the league plays. The point is the SHAPE, not the decimals. The run-out share in particular swings season to season on tiny wicket counts (7.0 / 8.6 / 9.1 / 3.4% across the four seasons); the ~7.1% needle is their pooled mean, and the latest season already dipped below the IPL’s modern 4.7% — so read the running dial as a cloud, not a fixed point.',
			'Two clocks at once. Batting: the WPL’s slow-innings share (~9.2% of every ball) already sits at the modern IPL’s level (8.5%) — it was born past the anchor, a modern batting dialect. This undercuts the lazy “women’s cricket still rewards anchors” narrative directly. Running: its run-out share (~7.1%) is still partway down the IPL’s own fall from 12.3% (2008) to 4.7% (2026) — the risky single hasn’t died there yet.',
			'Why “behind” is the wrong word: a league can be modern in one dimension and still developing in another AT THE SAME TIME — that is the whole point of two clocks. Reading a four-season league’s numbers against a nineteen-season timeline collapses the two into a single misleading rank. Chapter 6 — Two Dialects — gives this the full treatment.',
			'A companion figure in the same spirit: the WPL’s fixed-bar sub-120 occupancy sits at 19.8%, roughly where the early-2010s IPL stood — young in one measure, already modern in another.'
		]
	},
	'payoff-ch2': {
		title: 'Behind “your last anchor”',
		paragraphs: [
			'Each card names a franchise’s most recent qualifying TOP-ORDER (batting position 1-4) anchor innings — the batter who held the innings together — with its balls, runs, strike rate, boundary share, and the day’s going rate that match. An anchor is defined exactly as in the anchor sheet (15+ balls, below 0.85× the day’s rate, under 12% boundary balls).',
			'Franchises born after the archetype was already gone, with no qualifying top-order anchor, get the designed empty state — authored copy, never a blank card — because the empty state is itself the finding (“born post-anchor”). The neutral card names the most recent qualifying top-order anchor in IPL history and the league-wide decline.',
			'The replayable worm is that exact innings, drawn ball by ball against the day’s going-rate line — a real trajectory from the pipeline, not a reconstruction. Numbers on the card are per-franchise values from the payoff artifact; nothing is hand-authored per team.'
		]
	}
} as const satisfies Record<string, FootnoteEntry>;

export type FootnoteId = keyof typeof FOOTNOTES;

export function isFootnoteId(id: string | null): id is FootnoteId {
	return id !== null && Object.prototype.hasOwnProperty.call(FOOTNOTES, id);
}
