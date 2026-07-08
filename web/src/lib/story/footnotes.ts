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
			'A 200-run innings is any innings where a batting side scores 200 or more, batting first or chasing. Super-over innings don’t count. The chart counts how many such innings each season produced.',
			'Why counts, not averages? An average hides the ceiling. What changed is how often a team blasts past 200, and a count shows that straight up. 2008–2012 produced 31 of them. 2026 alone produced 65.',
			'Prefer the classic framing? The share of first innings reaching 200 rose from 7.7% in 2008-10 to 41.9% in 2023-26. In 2026 alone it hit 52%.'
		]
	},
	'ball-count': {
		title: 'What counts as a ball',
		paragraphs: [
			'Every legal and illegal delivery Cricsheet recorded, except super-over deliveries. The full data holds 316,388 deliveries. 189 of them come from the 17 tie-match super overs (36 super-over innings) and are left out of the field, so what you see is exactly 316,199. House rule: never show a number the pixels contradict.',
			'Wides don’t count toward a batter’s balls faced. No-balls do. That rule holds throughout the piece.',
			'Data source: Cricsheet ball-by-ball JSON. Season labels are normalized (2007/08→2008, 2009/10→2010, 2020/21→2020).'
		]
	},
	'ignition-wall': {
		title: 'How the wall is built',
		paragraphs: [
			'Every ball is placed by how long its batter had been in when it was bowled. The x-axis is the batter’s balls-faced count: 1 at the left, a capped 30+ bucket at the right edge. Each row is a season, 2008 at the bottom and 2026 at the top, with the WPL’s four seasons on their own shelf above.',
			'Wides are not balls faced; no-balls are. In the establishing shot, brightness is runs off the bat and hue is the outcome: dot, single, four, six.',
			'The thesis recolour: in the second half of the wall each ball is re-tinted by how hard it was hit versus a 2008-2010 batter at the very same point in the innings. For every balls-faced column (ball 1, ball 2, and so on), the pooled 2008-2010 strike rate at that ball-count is the neutral pivot. A cell (one season by one ball-count) reads cool when it sits at or below its 2008-2010 mark and hot when it runs well above it.',
			'Why baseline each column to its own 2008-2010 value: batters always speed up once they are set, so raw strike rate climbs across the first twenty-odd balls in every era. That left-to-right gradient swamps the year-on-year change in colour. Subtracting the 2008-2010 batter at each ball-count cancels that shared acceleration and leaves only the era difference, so the early-ball corner ignites bottom-to-top exactly where recent seasons most exceed 2008.',
			'The scale is diverging: deep blue below the 2008-2010 batter, grey-blue at it, amber-to-red well above. The chip’s exact figures are strike rate on the first ball of the innings: 73.7 in 2008-2010, up to 95.5 in 2023-2026. Pooled over the first ten balls it is 108.0, up to 135.3.',
			'The era bands: IPL 2008-2010 (the league’s first three seasons, the recolour baseline) versus 2023-2026 (its last four). The middle bands (2011-2015, 2016-2019, 2020-2022) are computed too and drive the payoff cards. Sample sizes on the first ten balls: 20,101 across 2,733 batter-innings then; 33,882 across 4,579 now.',
			'The start of the innings outgrew the game itself: the first-ten-ball strike rate rose about +25% while the all-innings strike rate rose about +21%. The revolution concentrates at the top.',
			'The wall is computed on your device from three small per-ball attributes (balls faced, season, and the era-relative heat byte); no positions are downloaded.'
		]
	},
	sixes: {
		title: 'Counting the sixes',
		paragraphs: [
			'A six is any ball the batter hit for six (runs off the bat, not extras). Each firework column is that season’s real IPL sixes; the raw heights run 623 in 2008 to 1,426 in 2026, and behind the rounded “every 21 → every 12” sit 20.8 balls per six then and 11.7 now.',
			'Seasons grew too, with more matches and more balls (13,489 deliveries in 2008 versus far more now), so raw six counts flatter the modern game. The per-ball rate is the honest comparison, and it is the one the caption quotes.',
			'The “big swings” pair uses an aerial-attempt proxy: attempts = sixes + caught dismissals (caught-and-bowled excluded) per 100 balls; execution = sixes ÷ (sixes + caught). Caught includes keeper and slip edges, because the data carries no fielding positions. That is a fixed noise floor that leaves era-over-era comparisons valid so long as edge rates are stable. True shot-level intent would need non-public ball-tracking.',
			'Attempts rose as well as landings: 7.3 per 100 balls (2008-2010) → 11.4 (2023-2026), about +56%, while execution rose 58.7% → 67.3%.',
			'The shrinking specialists’ slice, quantified: the top-10 hitters’ share of league sixes fell 35.9% (2008) → 28.1% (2026); players with ten-plus sixes in a season rose 18 → 58.',
			'The technical name for the spread: the season-by-season concentration of six-hitting (a Gini coefficient over batters with at least 30 balls faced) fell from 0.49-0.54 in the early years to 0.40-0.46 in 2024-26.'
		]
	},
	'out-rate': {
		title: 'The out-rate, ball by ball',
		paragraphs: [
			'The technical name for this is a discrete-time hazard curve, estimated Kaplan-Meier-style: for each ball of a batter’s innings, the share of innings that reached that ball and ended on it.',
			'Innings that ended not-out are censored: they stop counting once they stop being observed. Retired-hurt innings (10 in the corpus) and tactical retired-out innings (5) are censored too, never counted as dismissals.',
			'The out-rate is risk per ball; strike rate is runs per ball. They move independently, which is exactly the point of Chapter 1.',
			'Conventions: wides don’t count toward balls faced (a batter can still be out on one, and that dismissal counts); no-balls do. The first-ten-balls headline (5.04% then, 4.93% now) counts every dismissal at a faced-count of ten or fewer. Per-era samples: 2,733 batter-innings and 20,101 first-ten balls (2008-2010); 4,579 and 33,882 (2023-2026).',
			'A demoted exhibit, the over as a clock face: even inside the over the sighter died. 2008-10 overs ran quiet-loud-quiet: the over’s first ball scored at a 7.34 run rate with a ball-three peak of 8.02. 2023-26 overs start hot and fade: ball one at 9.20, ball six at 8.89.',
			'The environment moved too: pitches, and rules like the 2023 Impact Player. Chapters 4, 7 and 10 apportion the credit. The early-innings out-rate stayed flat across all of it.'
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
			'Sample honesty: the WPL is 88 matches and 20,642 deliveries across four seasons. These are young curves that will move as the league plays.',
			'The six-share companion to the fours pair: 15.5% of WPL runs come in sixes versus 29.0% in the modern IPL. It is a different engine, not a smaller one. The WPL leans on fours in a way the men’s league never did at any age.',
			'Why “behind” is the wrong word: the leagues differ in outcome mix (where the runs come from), not just outcome rate (how many). Reading a four-season league’s numbers against a nineteen-season league’s timeline confuses those two clocks. Chapter 6, Two Dialects, gives this the full treatment.',
			'Aerial execution sits here too: WPL execution on big swings is 54.5%, at intent-era IPL levels (same proxy and caveats as the sixes sheet).'
		]
	},
	'payoff-ch1': {
		title: 'Behind the payoff card',
		paragraphs: [
			'Team pools show their per-era ball counts on the card (the Sample line). Fastest-starter lines require at least 100 first-ten balls faced for that franchise. Teams born after 2010 (Gujarat Titans, Lucknow Super Giants, Sunrisers Hyderabad) get a designed empty state instead of a fabricated early era.',
			'Franchise renames merge histories: Delhi Daredevils → Delhi Capitals, Kings XI Punjab → Punjab Kings, Royal Challengers Bangalore → Bengaluru. Defunct franchises (Deccan Chargers, Kochi Tuskers Kerala, the Pune entities, Gujarat Lions) stay distinct. They are not folded into current teams.',
			'Behind the WPL card’s league clock: at the same league age (years 1-4), the IPL’s run rate went 8.31 → 7.73; year by year, IPL 8.31 / 7.48 / 8.13 / 7.73 and WPL 8.08 / 7.86 / 8.37 / 8.54. Both paths are non-monotonic, so endpoints alone flatter both. WPL era bands on the card are 2023-2024 versus 2025-2026. Early days for a young league: small sample, honest numbers.'
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
			'The technical name is an anchor innings: a batter innings of at least 15 balls faced whose strike rate ran below 0.85× the day’s going rate (the season-and-phase par strike rate, each league priced against its own baseline), with boundary balls (four or six off the bat) under 12% of the balls faced.',
			'Why 0.85× the day’s rate, not a fixed strike-rate cutoff: a strike rate of 120 meant something very different in 2009 than in 2026. The bar has to move with the era, or you just measure how much the whole league sped up. (The fixed-bar version is the raw sub-120 cut, in the anchor-decline sheet, and it is a different, less honest number.)',
			'The finding survives the reasonable cuts. Loosening or tightening the slowness bar (0.80× / 0.85× / 0.90× of the day’s rate) and the boundary cap (10% / 12% / 15% of balls) moves the exact percentages but not the shape: the anchor thins out across the era every way you slice it.',
			'“The worm” is the broadcast term for a cumulative-runs line: runs on the vertical, balls faced on the horizontal. A steep worm is fast scoring, a flat one is an anchor. Balls faced excludes wides. The day’s going rate is priced on legal deliveries (a scorecard strike rate).'
		]
	},
	'anchor-extinction': {
		title: 'How the anchor decline is counted',
		paragraphs: [
			'The headline is era-relative: the share of every ball bowled in a season that was consumed by an anchor innings (as defined in the anchor sheet). It fell from 14.8% across the league’s first three seasons (2008-2010) to 8.5% across its last four (2023-2026), a decline of roughly 43%.',
			'A blunter, fixed-bar version you may have seen: the share of qualifying batter-seasons (100+ balls) whose whole-season strike rate stayed under 120 fell from 39.3% (2008-2010) to 2.4% (2023-2026). That looks like a ~94% collapse, but 120 is a FIXED bar the whole league simply outgrew, not an era-relative measure. The two numbers diverge precisely because one moves with the era and one does not; they do not corroborate each other, which is why the main flow carries only the era-relative 14.8 → 8.5.',
			'How much of the decline is intent (batters choosing to attack), how much is selection (teams no longer picking accumulators), and how much is rules is not cleanly separable, and the chapter does not claim it is. In particular the Impact Player substitute (2023+) makes losing a wicket cheaper and lands squarely on the 2023-2026 end of the curve. It is a structural rule change entangled with the batter-and-team-choice story at exactly the point the extinction completes.',
			'The “last surviving anchors” are real qualifying innings from the final seasons, named from the pipeline. The magnitude claim (“few enough to name”) rides that list and the population chart, never the illustrative worm thicket, which is a sample per season, not a headcount. Era bands: 2008-2010 versus 2023-2026.'
		]
	},
	'runout-extinction': {
		title: 'Counting the run-outs',
		paragraphs: [
			'Run-out share is the number of dismissals of kind “run out” as a share of all non-retired dismissals that season (retired hurt / retired out are censored, never counted as wickets). It fell from 12.3% of wickets in 2008 to 4.7% in 2026.',
			'The run-out decomposes by which end was given out: striker versus non-striker (from who was dismissed). Across 2008-2010, 142 strikers to 112 non-strikers were run out (44.1% non-striker); the mix drifts season to season on small counts.',
			'This is fewer risky singles PLUS safer running, not one alone, and it is a league-wide trend, not the anchor’s personal doing. Break-Even Running (the demoted mechanism note): run-outs per 1,000 legal balls roughly halved, 6.4 → 2.8, while the rate of twos held essentially flat, 7.8 → 7.6 per 100 non-boundary balls. Running didn’t atrophy, it got safer at constant aggression. So the “risky two” never stopped; only the frequency and value of the scampered single fell. The “gone together” line is a real co-decline of two era trends, not the anchor causing the run-out to die.',
			'Direct-hit and fielding detail would need a fielders array that is sparse or missing for stretches (gaps cluster around 2018-2021), so that cut is handled cautiously and not headlined.'
		]
	},
	'gear-shift': {
		title: 'The shape of an innings',
		paragraphs: [
			'The technical name is an innings-shape taxonomy over innings of at least 25 balls faced. The headline “two-act” share counts innings whose second-half strike rate ran at least 1.5× the first half (split by balls faced), the classic crawl-then-launch. It fell from 33.7% of long innings in 2008-2010 to 24.1% in 2023-2026.',
			'A companion thirds lens tells the same story from the other side. “Flat-max” innings (the three thirds’ strike rates all within 1.25× of each other, one gear held the whole way) are now the modal long innings, rising to 11.6% while the rising-across-thirds “three-act” shape fell.',
			'This isn’t a sampling artifact: the share of innings that even reach 25 balls is era-stable, so the change is in the shape of long innings, not in how many there are. The two exemplar worm shapes on screen are an illustration of the taxonomy, not specific field points.'
		]
	},
	'new-batter-tax': {
		title: 'What a wicket still costs',
		paragraphs: [
			'The New-Batter Tax is the team’s runs-per-over shortfall over the 10 legal balls after each dismissal, measured against the season-and-phase par for that window (full windows only; dismissals within 10 balls of the innings end are trimmed). It did not shrink: −1.13 runs per over below the day’s rate in 2008-2010, −1.30 in 2023-2026. That is a slight DEEPENING, which is what makes it the one cost the revolution couldn’t kill.',
			'A note on baselines: that is the ABSOLUTE gap, and it deepened even as the day’s going rate itself rose (from 7.74 to 9.20 runs per over). As a SHARE of the going rate the tax is roughly flat, about 15% in both eras. So “deepened” is the honest word for the absolute gap and “un-killed” for the relative one. Either way the revolution couldn’t erase it.',
			'The incoming batter, meanwhile, walks in swinging far harder than ever: strike rate on the first five balls faced after a wicket rose from about 95 (2008-2010) to about 119 (2023-2026), roughly a 25% jump. Yet the team still stalls the moment a new man arrives. The cost is structural (a new batter set-up, a field reset), not a failure of nerve.',
			'The absolute level tracks the par baseline used: this season-and-phase stand-in yields ~1.1 → ~1.3, and the catalog’s wickets-in-hand-conditioned par yields 1.22 → 1.40; the level converges when engine #1’s conditioned table replaces the stand-in. The direction, a slight deepening, is the same either way. The WPL comparison stays open (not enough post-wicket WPL cricket yet for a clean number).',
			'A second, deliberately demoted nerd-nugget, the Milestone Braking Index: batters still ease off approaching a landmark like a fifty, and if anything more so now than in 2008. It is not a rival coda; the full index lives in the methods pages.'
		]
	},
	'wpl-two-clocks-ch2': {
		title: 'Two clocks, one beat (the anchor and the run-out)',
		paragraphs: [
			'Sample honesty: the WPL is four seasons young, about 19,988 legal balls faced in the anchor computation, so these curves will move as the league plays. The point is the SHAPE, not the decimals. The run-out share in particular swings season to season on tiny wicket counts (7.0 / 8.6 / 9.1 / 3.4% across the four seasons). The ~7.1% needle is their pooled mean, and the latest season already dipped below the IPL’s modern 4.7%. Read the running dial as a cloud, not a fixed point.',
			'Two clocks at once. Batting: the WPL’s slow-innings share (~9.2% of every ball) already sits at the modern IPL’s level (8.5%). It was born past the anchor, a modern batting dialect. This undercuts the lazy “women’s cricket still rewards anchors” narrative directly. Running: its run-out share (~7.1%) is still partway down the IPL’s own fall from 12.3% (2008) to 4.7% (2026). The risky single hasn’t died there yet.',
			'Why “behind” is the wrong word: a league can be modern in one dimension and still developing in another AT THE SAME TIME. That is the whole point of two clocks. Reading a four-season league’s numbers against a nineteen-season timeline collapses the two into a single misleading rank. Chapter 6, Two Dialects, gives this the full treatment.',
			'A companion figure in the same spirit: the WPL’s fixed-bar sub-120 occupancy sits at 19.8%, roughly where the early-2010s IPL stood. Young in one measure, already modern in another.'
		]
	},
	'payoff-ch2': {
		title: 'Behind “your last anchor”',
		paragraphs: [
			'Each card names a franchise’s most recent qualifying TOP-ORDER (batting position 1-4) anchor innings, the batter who held the innings together, with its balls, runs, strike rate, boundary share, and the day’s going rate that match. An anchor is defined exactly as in the anchor sheet (15+ balls, below 0.85× the day’s rate, under 12% boundary balls).',
			'Franchises born after the archetype was already gone, with no qualifying top-order anchor, get the designed empty state (authored copy, never a blank card) because the empty state is itself the finding (“born post-anchor”). The neutral card names the most recent qualifying top-order anchor in IPL history and the league-wide decline.',
			'The replayable worm is that exact innings, drawn ball by ball against the day’s going-rate line. It is a real trajectory from the pipeline, not a reconstruction. Numbers on the card are per-franchise values from the payoff artifact; nothing is hand-authored per team.'
		]
	},

	/* ---- Chapter 3: The Counterrevolution ---------------------------------- */
	'economy-convention': {
		title: 'How the plane is counted',
		paragraphs: [
			'Left to right is economy, the runs a bowler leaks per over. It is bowler-charged: the batter’s runs plus wides plus no-balls, per six legal balls. Byes and leg-byes are left out everywhere in this piece, because they are not the bowler’s fault (this shifts league runs-per-over about 0.15 versus an all-extras economy).',
			'Top to bottom is bowling strike rate, the number of legal balls a bowler needs to take a wicket. Only wickets credited to the bowler count. A run-out is a fielding event, so it is not on this axis (Chapter 2 told that story).',
			'A bowler-season needs at least 90 legal balls to draw a crisp cloud and to count toward the edge of the possible. Shorter spells fade into the all-time haze. A bowler-season that took no wicket has no balls-per-wicket at all, so it clamps to the top “60+” bucket, labelled as such.',
			'The economy and strike-rate numbers are a direct roll-up of every delivery, built on the same season baselines the piece uses for the going rate. Both axes are better when lower, so the good corner is the bottom-left: cheap and deadly at once.'
		]
	},
	'frontier-retreat': {
		title: 'The edge, and why it retreats',
		paragraphs: [
			'The hero share in fan form: bowler-seasons that kept their economy under seven an over. In the league’s first three years that was 49 of 169 qualifying bowler-seasons (29.0%). In the last four it was 4 of 267 (1.5%). The edge of the possible is the lower-left staircase of the best-anyone-managed bowler-seasons each year, a precomputed lookup, never fitted on your device.',
			'Why we tell it through the edge and not a correlation: you might think taking more wickets now buys you a cheaper economy across bowlers. We checked, and it does not. That link is weakly POSITIVE in both eras, +0.12 in the early years and +0.03 now (and +0.34 in the WPL), so the honest way to tell the counterrevolution is the edge marching right, not a link that was never there.',
			'The tide, not the men. The league’s bowler-charged economy rose from 7.79 to 9.38 runs an over. So a 7.5 economy went from roughly league-par in 2009 to nearly two runs an over BETTER than par by 2025. The raw numbers got uglier while the bowling got better. That is True Economy, and it is why the close says the bowler improved even as the scoreboard turned against him.',
			'A demoted exhibit, the death specialist: the share of death overs bowled by genuine death specialists rose from nothing in 2008 to a mid-era peak and is already eroding, maybe as the Impact Player rule lets teams stay flexible. This recompute is definition-sensitive and lands lower than the catalog’s headline figure, but the shape (a rise, then a 2026 slump) is the same.',
			'One honest confound on the most recent seasons: the 2023 Impact Player rule freed batters up, so part of the frontier’s latest rightward jump is a rule change tangled up with bowler skill, not bowler skill alone. Chapter 7 pulls that thread out.'
		]
	},
	'dismissal-dna': {
		title: 'How wickets changed shape',
		paragraphs: [
			'The bands are shares of the wickets the bowler actually earned. Run-outs and retirements are left out of the count (they are a fielding event, told in Chapter 2), so every share sits on one honest denominator. “Caught” here is a catch in the field or to the keeper; caught-and-bowled is kept separate. Bowled and leg before share one colour because they are the same idea: the ball beat the bat and hit the woodwork.',
			'The caught band did not swell on bowler intent alone. Chapter 2’s aerial revolution matters here too: batters skied the ball far more over the era, which manufactures catches no matter where the bowler aimed. So caught rose because bowlers aimed wider AND batters went up more.',
			'A caveat on the keeper: we infer keeper credit from stumping records, which covers about 84% of team-seasons, so a clean split of caught-behind from caught-in-the-deep is not fully available. The residual is documented.',
			'The deep cut, field-independent bowling: across ALL dismissals (run-outs included) caught rose from 60.0% to 72.6% while run-outs collapsed from 12.1% to 5.2%. So more of a bowler’s fate now sits in a fielder’s hands, which makes raw bowler numbers LESS skill-reflective in 2026 than in 2008. This all-dismissal figure is a different denominator from the bowler-credited shares in the main flow, which is why the two never sit on screen together.',
			'The WPL keeps a much fatter stumping band, 5.2% to 7.9% of its wickets every season, a genuinely different way of getting batters out. That is teased here and paid off in Chapter 6.'
		]
	},
	'dot-plus': {
		title: 'The dot, and what it is worth',
		paragraphs: [
			'A dot is a legal ball the batter scores nothing off. The league dot rate fell from 37.6% in the early years to 33.0% now. Because a dot got rarer, the same dot rate is a harder achievement today than it was in 2009.',
			'The technical version is Dot+: a bowler’s dots measured against the dots an average bowler would make with the same season and over-number mix, so 100 is the league average of its own time. On that scale Narine in 2012 tops the board at 142.6, with Bumrah’s recent seasons and Rashid Khan close behind. It lets a 2010 dot artist and a 2024 one share one leaderboard.',
			'The two grids are real single innings, not the field’s own points, each chosen at or very near its era’s mean dot rate. A single innings swings anywhere from a quarter to half its balls as dots, so one innings on its own could easily over- or under-state the honest 4.6-point league shift. That is why the caption trusts the league number, not the eye.'
		]
	},
	'death-wides': {
		title: 'The wide-yorker tax',
		paragraphs: [
			'This counts wides given away per 100 legal balls in the death overs, the last five (overs 16 to 20). It doubled, from 3.13 in the early seasons to 6.45 now (a factor of 2.06). Across all phases the wide rate rose more gently, from a low of 2.71 in 2013 to 4.78 in 2026, so the death overs are the real story.',
			'The doubling is not one clean cause. Three things push it up together and the data cannot cleanly separate them: bowlers chase the un-hittable ball on purpose, batters shuffle across their stumps to make good balls look wide, and umpires call the wide line tighter than they once did. It is an arms race made of runs, not bowlers getting worse.',
			'We cannot measure the wide-review sub-metric in this data: the review-type field only ever reads “wicket” or is missing. And the WPL’s death-wide rate is just 2.69, the seed of the next scene’s point that the arms race is a men’s-league thing, not a stage every league passes through.'
		]
	},
	'crack-ratio': {
		title: 'Does the squeeze still crack them?',
		paragraphs: [
			'The squeeze number is the chance of a wicket on the ball right after a run of three or more dots, divided by the chance off a fresh scoring ball, in the middle overs. Above 1, dot pressure still buys wickets. Below 1, batters have defused it. The raw release ratios are always below 1 because pressure moments coincide with the better bowlers, so this ratio is the honest read of whether the squeeze itself still bites.',
			'What it does NOT prove. This is a single cross-league snapshot, so read the 1.18-versus-0.81 gap as a plain difference between two leagues today, not the IPL “learning to survive” dots over time (we do not draw an IPL crack-ratio time series). And it does not by itself explain why IPL economies inflated. As above, taking wickets does not buy a cheaper economy across bowlers: that link is weak in both leagues, +0.12 then and +0.03 now in the IPL, +0.34 in the WPL.',
			'The spinner’s-league tease is a proxy, said plainly: the WPL keeps stumpings at 5.2% to 7.9% of its wickets every season, against the IPL’s 1.4% in 2026 (1.9% pooled across 2023-26). A stumping usually means spin, but the data carries no bowler-type field at all, so stumping share is only a proxy for spin. That is why “a spinner’s league” stays out of the main flow, and the full treatment is Chapter 6, Two Dialects.',
			'Sample honesty: the WPL is 88 matches across four seasons, so these numbers will move as it plays. A league can keep an old strength and refuse an old path at the same time, which is why “behind” is the wrong word for it.'
		]
	},
	'true-economy': {
		title: 'Beating the tide',
		paragraphs: [
			'Beating the tide means leaking fewer runs than an average bowler would have in the exact overs, phases, and grounds this bowler actually bowled. A death specialist is priced against death par, not against the whole game, so a modest raw economy in a high-scoring year can be a huge gap. This is the going-rate family from the rest of the piece, flipped from batting to bowling.',
			'The gap printed on the card is that True-Economy differential, and the card shows its own arithmetic: the going rate for the overs he bowled, minus the runs he actually leaked, equals the gap. That gap is exactly the number that ranks his season the biggest at the franchise, so what you can add up on the card is the metric itself.',
			'A bowler-season needs at least 90 legal balls to qualify. The WPL five carry a designed short-sample state by choice: four seasons is not a long enough tide to crown a gravity-defier against yet, so the card names who is closest so far and says to ask again in a few years. That honest short sample is itself the point. A couple of IPL cards rest on a thin spell too and say so.',
			'The wicket-taking mirror of this idea is True Wickets per 24: actual minus expected wickets per 24 balls, expected from the same league-season baseline. It answers who really took more wickets than their era should have, and it lives here in the deep layer.'
		]
	},
	'par-drift': {
		title: 'The going rate, and how we find it',
		paragraphs: [
			'The going rate we call par is the first-innings total that wins exactly half the time. We fit it with a logistic model: the chance the team batting first wins, read against the total it posted, on decided matches with a full first innings (no rain-shortened chases, no no-results). Par is the total at 50%, a safe score is the total at 75%, and a dead one is the total at 25%.',
			'Pooled by era, par climbed from about 165 runs in 2008-2010 to about 195 in 2023-2026, and a safe score from 191 to 230. The rising blue waterline uses a per-season version, fit on a three-season window so a single small season borrows strength from its neighbours; that per-season line reaches about 206 by 2026.',
			'Par is a batting-first idea on purpose: it answers "was that enough?". It is the same going-rate family the bowling chapter used, just read from the batting end.'
		]
	},
	'full-first-innings': {
		title: 'What counts as a 200 innings',
		paragraphs: [
			'The 200 Club counts first innings that reached 200 or more, using full innings only: no Duckworth-Lewis rain jobs, no no-results, and no innings cut short below twenty overs. Chases are left out because a team chasing 170 stops at 170, so its total is not a free swing at a big score.',
			'Where you draw that full-innings line moves the 200-plus count by about one either way, which is why the artifact wins over any single quoted figure. Pooled by era, the share of first innings passing 200 went from 7.7% in 2008-2010 to 42.0% in 2023-2026, and to 52.1% in 2026 alone.',
			'The 180, 220 and 250 lines are counted the same way; they are the other beams of the same ridgeline.'
		]
	},
	'record-null': {
		title: 'Why a faster-falling record is the tell',
		paragraphs: [
			'Records get harder to break as they climb, purely by arithmetic: each new high is a taller bar to clear. So in a still, unchanging scoring world, each record should stand LONGER than the last one did, not shorter.',
			'The opposite happened. The highest first-innings total, RCB’s 263 from 2013, stood 3,991 days. Then it fell twice in 19 days in 2024, to SRH’s 277 and then 287. A record speeding up instead of slowing down is direct evidence the water level itself moved, not that one team got lucky on one night.',
			'We track first-innings totals only, and a lifespan is the number of calendar days between the day a record was set and the day it was beaten.'
		]
	},
	'phase-economy': {
		title: 'The innings went phase-agnostic',
		paragraphs: [
			'Demoted from the main flow, but a lovely nugget: the innings flattened out across its phases. The gap between the death-overs run rate and the powerplay run rate compressed from about 1.9 runs an over in 2008-2010 to about 1.4 in 2023-2026.',
			'By 2023-2026 the powerplay ran at about 9.5 an over and the death overs at about 10.9. The start of the innings now nearly keeps up with the end. Teams stopped saving themselves for later, because there is less "later" premium left to save for.',
			'Powerplay wicket cost is wickets lost per 36 legal balls; the run rates here are legal-ball run rates by over, pooled within each era.'
		]
	},
	'venue-canon': {
		title: 'Counting a ground’s tide',
		paragraphs: [
			'A ground’s tide is its typical first innings: the mean full first-innings total at that venue in an era. Before any of it, about sixty raw ground spellings collapse to their real venue. Chinnaswamy shows up under three spellings, Chepauk under three, and a rebuilt stadium keeps one identity.',
			'The share of scoring you can pin on which ground it was is a one-way analysis of variance, run within each season and then averaged across the era, so a season played mostly at neutral away grounds (South Africa in 2009, the UAE in 2020-21) cannot fake a spread. Measured that way it went from about 10% in 2008-2010 to about 24% in 2023-2026: grounds pulling apart, not together.',
			'A team’s home-ground card uses the same venue means, split by era, for the ground that team plays most of its home games at now. Punjab, for instance, is priced against Mullanpur, its current home, not the largely abandoned Mohali.'
		]
	},
	'tide-reservoir': {
		title: 'How the tide skyline is built',
		paragraphs: [
			'Every column is one full first innings, and the taller it stands the bigger the score. Full means the same clean cut used all through the chapter: no rain-shortened games, no no-results, and no innings cut short below twenty overs. Chasing innings aren’t columns, because a team chasing 170 stops at 170.',
			'Each season’s innings are sorted short to tall, so a block reads as a little skyline. Seasons run left to right, 2008 to now, with the WPL on its own block. The rising waterline, the going rate, is drawn on the very same scale, so a column that drops below it has literally been overtaken.',
			'Every OTHER ball ever bowled is still here too, settled into the low-alpha haze along the floor, so “every ball ever is here” stays literally true. The whole skyline is built on your device from one per-ball flag (was this a first innings), never downloaded as positions.'
		]
	},
	'cpi-callback': {
		title: 'Your sketch, and the two ways to count 200',
		paragraphs: [
			'At the cold open we asked you to draw how often teams pass 200 each season. We keep that sketch on your own device, in the browser’s local storage, and here we draw it back over the truth. If you skipped it or arrived by a shared link, we show the line a typical reader drew instead.',
			'Two honest counts of 2026 sit in this chapter and they are not the same number. The blue truth line here counts EVERY innings that passed 200 in a season, batting first or chasing: that is 65 in 2026. The 200 Club scene earlier counted the SHARE of FIRST innings that reached 200, which was 52.1% in 2026. So in 2026 teams cleared 200 sixty-five times either way, and more than half of all first innings got there. One is a count of innings, the other is a share of first innings. Neither is the other.',
			'Told as a run rate, it is the same story: the first-innings going rate rose from 8.03 an over in 2008-2010 to 9.55 in 2023-2026. The technical name is the T20 Consumer Price Index, a scoring price level. Set 2008-2010 to 100 and 2023-2026 reads 119, about 19% more runs for the same over. Every score you remember has quietly been repriced.'
		]
	},
	'measured-jump': {
		title: 'How we know 2023 really bent',
		paragraphs: [
			'The cliff is not one number acting up. The share of first innings passing 200 jumped from 17.6% in 2022 to 32.4% in 2023, and it is not alone: the going rate, the powerplay run rate and the highest-total record all step up at the same seam, not on a gentle slope.',
			'That simultaneity is what makes it a measured jump and not noise. When one number spikes you suspect a fluke. When several unrelated ones all hinge on the same off-season, something in the environment moved.',
			'What moved it is deliberately not named here. That is the whole point of the beat: the chapter shows the jump and refuses the reason. Chapter 7 names a suspect, and Chapter 10 gives the verdict.'
		]
	},
	'wpl-two-clocks-ch4': {
		title: 'The WPL, on two clocks',
		paragraphs: [
			'Reading a four-season league against a nineteen-season timeline needs two clocks at once. On the calendar clock the WPL’s 200 Club (11.4% of first innings) sits between the young IPL’s 2008 (13.0%) and 2015 (11.3%). On the league-age clock, wind both leagues back to season one, and its typical first innings rose 156.6 to 169.1 across its first four years, faster than the IPL climbed at the same age.',
			'It is not a smaller version of the men’s game, it is a different engine. About 46.8% of WPL runs come in fours against 33.9% in the modern IPL, and only 15.5% come in sixes against 29.0%. The flood is built along the ground, four-led, not over the rope.',
			'Sample honesty: four seasons is young. The WPL’s 200-plus totals by season run 4, then 0, then 5, then 5 across 2023 to 2026, small counts that will move as the league plays. A 200 there is still a real event, where in the modern IPL more than half of first innings clear it.'
		]
	},
	netsession: {
		title: 'How we worked out the net session',
		paragraphs: [
			'Every figure in the net session is looked up from a table built once, from the ball-by-ball record of 1,331 matches, 88 of them from the WPL. Nothing is fitted live in your browser: dragging a dial reads a square out of a table, it does not run a model. But “read from real matches” is only the whole truth where real matches piled up. The “how often teams win” table starts from how often teams actually won at each spot on the board (overs left, wickets in hand, and how hard the ask is), then makes two honest repairs. Where a spot had only a handful of real chases, its number is pulled toward the broader pattern for spots like it, so a barely-seen corner borrows from its neighbours instead of swinging wildly. And each row is nudged so the numbers move the sensible way: a harder ask never comes out easier than a softer one. So the honest headline is that the shape of the table is real memory, and the thin corners are filled in by that rule. The “runs a team usually still gets” table is the average a first innings went on to add from each over-and-wickets spot, built the same way. (The technical names for the two repairs: shrinkage toward the pooled cell, then a monotone repair across the ask.)',
			'We checked the win table against reality. Group every real chase by the chance the table gave it, then see how often those groups actually won. A table that says thirty in a hundred turns out to be right about thirty times in a hundred: across 144,136 real chase moments the average gap between the chance given and what actually happened was about one in a hundred, and never worse than about three in a hundred in any well-stocked band. (The technical name for that check is calibration.)',
			'Why a wicket matters most early and the ask matters most late: early in a chase there are overs to spare, so what decides the game is whether you keep batters to use them. With sixteen overs left and eleven or twelve an over to get, going from five wickets in hand to ten lifts your chances from about eleven in a hundred to about forty-six. Late, there is no time left to save, so only the ask moves the number. With two overs left those same wickets buy you nothing, about sixty-one in a hundred either way. That is why dragging wickets swings the meter hard at the top of a chase and barely at all at the death, and runs needed does the opposite.',
			'The win table is built only from chases that were played to a full twenty-over target, so rain-shortened targets, which change the maths mid-game, are left out rather than fudged. The handful of matches settled by a super over count by who actually went through. Games with no result are dropped.',
			'When we say the same chase came off about twenty-three in a hundred in 2008 to 2012 and about thirty-one in a hundred now, that is the win rate over every chase at least that hard in each era, not one square of the table, so it does not jump around the way a single square would. One honesty note: the counts behind each era are ball-by-ball states inside a short window near the same point of the chase, not separate matches, so the number of distinct games behind them is smaller than the raw counts suggest, and an eight-in-a-hundred gap on that base is less nailed down than it looks. So we say “about”, and the part we stand behind is the direction: the same chase is easier now than it was.',
			'The women’s league has played 88 matches, so most spots have too few real chases to say anything honest about. Any WPL square built on fewer than a dozen chases, or fewer than fifteen innings for the runs table, is marked and shown hatched with “not enough WPL cricket yet”, instead of a smoothed number that would look like a finding. As the WPL plays more cricket, more of the table fills in.'
		]
	},
	'ch5-over': {
		title: 'How the worm is read',
		paragraphs: [
			'The worm is a lookup, not a guess. For each spot in the over (runs needed, balls left, wickets in hand) its height is how often chasing sides win from that kind of spot, out of a hundred, read from the same win table the Net Session put under your fingers. The final anchor is pinned to what actually happened: Chennai finished one run short, so the worm ends at zero.',
			'The table buckets the ask (how many an over you still need), so two neighbouring balls can land in the same square and the worm holds flat between them. That is the table being honest, not the drama being flattened. And the raw history behind each spot lives here, one click deep on purpose: out of every time that exact endgame has ever come up in the league, how many chasing sides actually won. Needing 9 off 6 has come up 26 times; 17 of those chases got home.',
			'Inside a final over no single era holds enough of these exact endgames to read honestly, so those raw reads lean on the league’s whole last-over history there. Everywhere else in the chapter, prices are stamped with their own era. We treat “inside the last over, the ask matters far more than the era” as a working assumption and say so plainly here rather than as a fact.',
			'The swing on each chip is simply the worm after the ball minus the worm before it. Ball four carries one price for one delivery: the completed single and the run out are the same ball. And a single ball can cross both a wicket boundary and an ask boundary at once, which is how a late delivery can post a huge swing out of a thinly-stocked square; every readout is the locked table verbatim.',
			'The over is the same for every reader, on purpose. It is the chapter’s shared-culture moment, and the worm prices the spot, not the players standing on it. Naming whose moment it was is the payoff card’s job, and your own team’s biggest ball is waiting at the end of the chapter.',
			'One more thing this table quietly gives us: for every delivery ever bowled, how hard the match COULD swing at that moment. The sandbox will use it to flag “decision balls”, the deliveries bowled when everything was on the line. The technical name is Leverage Index.'
		]
	},
	'ch5-wpa': {
		title: 'How every ball gets its tag',
		paragraphs: [
			'Every delivery’s tag is its before-and-after read on the win table: the chance the batting side wins from the spot after the ball, minus the chance from the spot before it. The tables are built per era from the ball-by-ball record of 1,331 matches, because identical totals carry wildly different win chances in different eras; the era stamp is not optional, it is the finding. Each row is also nudged so a harder ask never prints as easier than a softer one.',
			'6,579 deliveries carry no honest tag and are left out rather than fudged: the 23 rain-rule matches, games with no decided winner, and chases set less than a full 20-over target. The tie matches count for the side that won the super over. When the chapter says “every ball here carries that tag”, this is the fine print that keeps it honest.',
			'Who gets the credit is a choice, and we say so. Each ball’s swing is credited to the striker and debited to the bowler; run outs go to the fielding side. The swing itself is the measured fact, but the split is our accounting convention: the non-striker and most fielders are invisible to it, and other honest splits exist. The payoff cards use exactly these credits.',
			'The 170-to-189 pair, reconciled: the on-screen 73 and 39 are the raw defended shares of real 170-to-189 first innings, from 41 matches then and 54 now. The engine’s smoothed curve reads the same band at about 70 and about 40; it exists so every total, even rare ones, has a stable read. Raw carries the scene, smoothed lives here.',
			'And the check that makes the whole system trustworthy: group every real chase by the chance the table gave it and see how often those groups actually won. Across the full history the table’s stated chances match reality to about one in a hundred. The technical name is calibration.'
		]
	},
	'ch5-worth': {
		title: 'How the runs-left map is built',
		paragraphs: [
			'A cell is a match situation: the over of the innings across, wickets already down going down the side. Its price is the average runs a first innings still scored from that spot, smoothed so thin cells borrow from their neighbours; a single season’s cells run as thin as 26 to 77 innings, which is why era bands and pooling are mandatory and the map never quotes one season alone.',
			'Chase balls sit on the map too, placed by their real over-and-wickets state. The price painted on their cell is the first-innings “what a batting side usually still gets from here”, exactly the number the Net Session’s runs meter used. Chases get their own currency everywhere it matters: the worm, the finisher chart, and the payoff card all read the win table instead.',
			'Brightness honesty: a cell’s brightness tracks its price, never its crowd. The first over with nobody out holds thousands of times more balls than the deep late rows, so per-ball brightness is rebalanced cell by cell before the price is painted. A crowded cheap cell can never outshine a sparse expensive one.',
			'One demoted exhibit lives here: the same innings priced under another era’s physics. Gilchrist’s 109 off 47 in the 2008 final chased a target of 155. That chase opens at 71 in 100 on the 2008-2010 table and at 84 in 100 on the 2023-2026 table: a knock that was a massive swing in its own time reads as merely a very good day at today’s prices. It is a re-pricing of the record, never a simulation of play.'
		]
	},
	'ch5-drift': {
		title: 'The rise, cell by cell',
		paragraphs: [
			'The rise lens is a subtraction: each cell’s new price minus its old one, 2023-2026 minus 2008-2010. Where it burns brightest, the price rose most, which is why the map glows hardest along its left edge: the very first over’s column rose most of anywhere on the map (about 29 runs), because from there the whole richer innings still lay ahead. Averaged cell by cell, the middle overs (7 to 15) rose by about 3.7 runs, the only stretch of the innings that rose at all.',
			'Not every cell rose, and none are hidden. The first six overs read about 1.2 runs LOWER per cell on average across the eras, and the last five about 0.2 lower; under the rise lens those fallen cells simply render dark. Nothing is clipped to make the map look more uniformly brighter than it is.',
			'The third-wicket readout is a two-cell subtraction: the price of losing your third wicket at over seven is the gap between the 2-down and 3-down cells at that over. On the locked, calibration-checked era tables the gap reads about 12 runs then and about 6 now.',
			'How big that collapse looks depends on the window and the smoothing, so here is the full spread. The raw, unsmoothed reads at that exact spot: 11.8 runs then (53 and 33 innings behind the two cells) and 3.5 across 2023-2026 (68 and 39 innings). A probe on the newest three seasons alone puts it near 1 run, which is where an earlier draft’s “nearly free” teaser came from. The number on screen is the gate-checked table’s answer, the more conservative one, on purpose.'
		]
	},
	'ch5-prices': {
		title: 'The price board, and both wicket numbers',
		paragraphs: [
			'How a price is computed: take the runs-left table before the ball and after it, subtract, add the runs the ball itself scored, and average over every ball of that kind in the era. That is the whole recipe. The board’s prices are derived from the locked era tables in the pipeline and shipped as data; nothing is fitted in your browser.',
			'Why a single can cost runs at all: it moves the total by one but spends one of a limited 120 balls. In a league scoring quicker than a run a ball, that trade now loses ground, about a quarter of a run on average. It used to be almost exactly a fair swap.',
			'A price is an average, not a ruling. The single’s price is averaged over the situations singles actually happen in; a single that keeps a set batter on strike can still be the right ball. The board prices habits, not decisions.',
			'The chapter shows two wicket numbers and both are true. The board’s wicket price (about 7.0 runs then, 7.6 now) includes the scoring chance the ball itself wasted. The price-tag scene’s number (4.2 to 5.1) is the state change alone, priced at the moment each real bowler-credited wicket fell, with run outs set aside for the fielding side. Two honest accountings of one event.',
			'And the pair that looks like a contradiction: the third wicket at a calm over-seven spot got dramatically cheaper, while the average wicket’s removed-runs value ROSE. Both hold, because modern wickets fall in bigger, hotter moments at higher scoring rates. The spot got cheap; the moments got expensive. That reconciliation is the chapter’s sharpest nugget.',
			'The catalog’s “+33%” wicket appreciation is the same table on a newer window: measured on 2024-2026 alone the wicket removes about 5.5 runs, roughly a third up on the early era. The chapter’s own era bands (2023-2026) give the more conservative +23% against scoring’s +20%. Same recipe, different window, both shown.',
			'A death-over dot is not a powerplay dot; prices split by phase are a sandbox view to come.'
		]
	},
	'ch5-finisher': {
		title: 'The finisher cohort, pinned',
		paragraphs: [
			'The cohort definition, exactly: chases read at the moment exactly 30 balls remain (the start of the final five overs), full 20-over targets only, rain-hit chases excluded, the tie matches counted for the side that won the super over, and one read per match so a stalling team cannot vote twice. The bands are the required rate at that moment.',
			'The raw counts behind the headline: needing 8 to 10 an over from there, 17 of 31 such chases came off in 2008-2010 and 35 of 41 in 2023-2026. Small cohorts, printed on the chart rather than hidden behind a rate.',
			'The rest of the curve: at 10 to 12 an over the win rate roughly jumped from 35 in 100 to 50, and past twelve both eras still sit near 12 in 100. That last part is why the chapter says the cliff MOVED rather than crumbled: beyond the new fatal rate, chases die exactly like they always did.',
			'One demoted exhibit lives here: the wider chase-difficulty map. Needing 30 to 42 runs off the last 24 balls with five or more wickets in hand went from 68 in 100 (25 of 37 chases) in 2008-2010 to 88 in 100 (37 of 42) in 2023-2026. The full state-by-state map, with famous chases crawling across it, is a sandbox view to come.'
		]
	},
	'ch5-wpl': {
		title: 'The mask, and a cohort of eleven',
		paragraphs: [
			'The evidence mask is the same rule the Net Session taught, at the same thresholds: any WPL runs-left cell built on fewer than 15 innings renders hatched, “not enough WPL cricket yet”, never a smoothed number dressed as a finding. That is 155 of the 200 cells today. The hatch is a texture laid over the map, never a dimming, so a thin cell can never be misread as a cheap one.',
			'Where the mask bites and any cricket HAS been played, the honest alternative to a fitted surface is the observed record itself: the actual runs-to-come from the real innings that passed through that spot. Real outcomes as real marks, never a curve pretending to be one.',
			'The finisher cohort is forming live: 9 of 11 is about 82 in 100, but eleven chases is a young list. The direction is the finding; the digit will move as the league plays. It lands above the IPL’s early-era rate and below its modern one, on the WPL’s own clock.',
			'A league can sit between two IPL eras on one dial and off the IPL’s map entirely on another. That is not a contradiction, it is the whole thesis of the next chapter, and the tightest-finishes line is its opening argument.'
		]
	},
	'ch5-payoff': {
		title: 'How your most valuable ball is found',
		paragraphs: [
			'Every delivery in your franchise’s history gets its before-and-after win read on its own era’s table, credited by the chapter’s accounting: the striker credited, the bowler debited, run outs to the fielding side. The card shows the single biggest swing the pipeline found, and the release checks assert the card’s number equals the emitted maximum, so what you read is what the data says.',
			'Why a defended last ball or a run out can out-swing a six: late in a tight chase, one delivery carries the whole match. The swing measures the match, not the shot’s beauty. Some of the biggest balls in history are scrambled twos and lbw shouts.',
			'WPL cards are priced on the evidenced WPL and pooled tables, and four seasons is a short list. The card says so on its face: a young history is a promise, not a deficit.',
			'The replay’s worm reads YOUR team’s win chance, which may be the defending side. The canonical over earlier in the chapter reads the chasing side. Same method, different referent, which is why the two worms can quote different numbers for similar spots.'
		]
	},

	/* ---- Chapter 6 — Two Dialects (r4a) ------------------------------------
	 * Prose numbers below are documented constants that trace to ch6.json exactly
	 * (the house convention: the "how we computed this" layer carries verified
	 * figures as text; every MAIN-FLOW number is data-bound to ch6.json). Where a
	 * blueprint teaser and the artifact diverge, these track the ARTIFACT. */
	'ch6-constellation': {
		title: 'How the season map is built',
		paragraphs: [
			'Every one of the 23 stars is one season of one league, placed by how differently it played, ball by ball. For each season we take the mix of what happened on a delivery, split into seven shares that add up to one: dot, single, two or three, four, six, wicket, or extra. A wicket ball counts as a wicket whatever else happened on it.',
			'The distance between two seasons is how different those two mixes are. The technical name is the Jensen-Shannon distance, a standard, symmetric way to measure the gap between two distributions. We build the full 23-by-23 table of those distances, then find the flat map of 23 points whose straight-line gaps best reproduce it. The technical name is classical (Torgerson) multidimensional scaling. It is computed once, in the pipeline, and never re-fitted in your browser.',
			'Read only the CLOSENESS. This map has no up, down, left or right that means anything: you can spin it or flip it like a photograph and every distance between stars stays the same, so the directions carry no information at all. How faithfully the flat map reproduces the true distances (the technical name is stress) is 0.13 for the all-overs map, low enough to trust how close two stars sit.',
			'And the headline the geometry earns: every WPL season’s nearest men’s neighbour by shot mix is IPL 2008, while at the same time it scores at IPL 2022’s run rate. Two honest comparisons that usually agree, here disagreeing. That is why the WPL sits beside the men’s path, not on it. A different dialect, not an earlier version.'
		]
	},
	'ch6-phase': {
		title: 'Why the phase maps line up',
		paragraphs: [
			'The same map is built four times over: once with every over pooled, and once each for the first six overs, the middle overs (7 to 15) and the death overs (16 to 20). Each is a fresh Jensen-Shannon distance table and a fresh flat map.',
			'Because the map has no meaningful directions, each phase’s map could come out spun or mirrored from the others by pure chance, and a mirror would throw the WPL to the wrong side of the men’s path. So each phase map is rotated, scaled and if needed flipped to sit as closely as possible on top of the all-overs master. The technical name is Procrustes alignment. That lock is exactly why the browser looks the positions up and never re-fits them: a fresh fit could legally mirror the WPL across the path and wreck the chapter’s whole picture.',
			'The alignment does real work. It cuts the mismatch between a phase map and the master by more than twenty times over. After it, the WPL’s nearest men’s twin is an early IPL season in every phase: 2008 in the first six overs and at the death, about 2011 through the middle. It never once lands among the recent years, whichever overs you ask about.'
		]
	},
	'ch6-maturity': {
		title: 'The maturity clock, and two demoted exhibits',
		paragraphs: [
			'League year N is simply a league’s Nth season: IPL year 1 is 2008, WPL year 1 is 2023. Run rate is all the runs, extras included, per six legal balls. Wides and no-balls are left out of the deliveries counted, the same convention as the rest of the piece.',
			'The match is exact: the WPL’s fourth-year run rate is 8.54, and the IPL’s fifteenth season, 2022, also ran at 8.54. But both leagues opened near 8 an over: the IPL’s first four years went 8.31, 7.48, 8.13, 7.73, the WPL’s 8.08, 7.86, 8.37, 8.54. So the men’s fifteen seasons to 8.5 is a long flat plateau that finally edged over the line, not a long climb from a low base. And the WPL launched in 2023 into a mature T20 world, inheriting fifteen years of the men’s know-how and importing established stars rather than climbing from scratch. Four seasons against fifteen is a threshold-crossing coincidence, not a steeper development curve: reaching the same rate sooner is not the same as developing faster.',
			'A demoted exhibit, the powerplay’s share of scoring: the WPL’s first six overs score at 0.92 times its overall rate in 2026, exactly where the IPL sat for years before it crossed 1.0 (reaching 1.02 by 2026). The open question a young league raises is whether it needs a shock of its own to break that equilibrium.',
			'A second demoted exhibit, batting depth: in 2025 the WPL’s number sevens and lower scored 15.3% of all runs, the highest single season in either league. Read it as opportunity, not a skill claim. More collapses force the lower order to bat. The WPL’s pooled figure (12.1%) sits close to the modern IPL’s (11.6%).'
		]
	},
	'ch6-dna': {
		title: 'How the runs are split, and the twos question',
		paragraphs: [
			'Each column splits a league’s runs by how they were scored: a four is four runs times the balls hit for four, a six is six times the sixes, and singles, twos and threes likewise. The shares are of all runs off the bat; the small remainder on top of each bar is extras and the rare five. Modern IPL here means 2023-2026, matched to the WPL’s four seasons.',
			'The gap is real and large: 46.8% of WPL runs come in fours against the modern IPL’s 33.9%, and only 15.5% in sixes against 29.0%. A flood built along the ground, not over the rope. A different engine, not a smaller one.',
			'A demoted exhibit that cuts the other way. You might expect a ground-based game to run harder for twos, but the WPL’s twos rate (9.8% of its one-two-three balls) sits below the modern IPL’s (13.5%). Smaller boundaries turn would-be twos into fours, so the running game is thinner for a geometric reason, not a fitness one. Meanwhile the IPL’s three is quietly dying, 0.85 to 0.46 per match, as boundary hitting replaces hard running.'
		]
	},
	'ch6-stumping': {
		title: 'Counting stumpings, and the spin proxy',
		paragraphs: [
			'The share is stumpings as a fraction of all of a season’s dismissals, run-outs included; only retirements are set aside. The data also carries the bowled-plus-lbw and caught shares beside it.',
			'A stumping nearly always means a spinner was bowling, so its share is a proxy for how spin-heavy a league is. We say proxy on purpose, because the data carries no bowler-type field. We never state "a spinner’s league" as a measured fact, only as what a stumping share three-to-five times the men’s strongly implies.',
			'Every WPL season runs 5.2 to 7.9% (7.0, 7.9, 5.2, 5.3 across 2023 to 2026). The IPL last topped 5% back in 2010 and reached just 1.4% in 2026.',
			'Sample honesty: the WPL is four seasons and a few hundred dismissals a year, so the season-to-season figures will move. The size of the gap, not the decimals, is the point.'
		]
	},
	'ch6-photofinish': {
		title: 'What counts as a photo finish, and the balance exhibits',
		paragraphs: [
			'A photo-finish is a first-innings defence won by five runs or fewer, or a chase completed with three balls or fewer to spare. The denominator is decided matches only: ties (which go to a super over), rain-rule results and no-results are left out. Balls to spare is 120 minus the legal balls bowled when the target was passed.',
			'The WPL’s 24.1% (21 of 87 decided games) is the highest of any league-era in the data; the IPL’s five eras run from 16 to 23%.',
			'A demoted exhibit on the title race. The WPL launched more top-heavy than even the chaotic early IPL. Its win concentration reads about 0.043 against the early IPL’s 0.016 on a normalised win-share measure. Yet the trophy is a genuine duopoly: two different champions in four years, Mumbai and Bengaluru twice each, against the early IPL’s three in four.',
			'And the star-dependence scare, defused. Batter-run concentration (a Gini coefficient) reads star-heavy for the WPL unfiltered, around 0.54 to 0.59, but that is a small-pool illusion. Among batters with at least 30 balls faced the WPL’s concentration is 0.34 to 0.38, at or below the IPL’s. Matched fairly, the WPL is not a one-woman league.'
		]
	},
	'ch6-payoff': {
		title: 'How your two dialects are paired',
		paragraphs: [
			'IPL sides are matched to their shared-city WPL sister where one exists: Mumbai, Bengaluru and Delhi each field a team in both leagues, and Gujarat’s IPL Titans pair with the WPL’s Gujarat Giants. Six IPL sides and the WPL’s UP Warriorz have no sister yet, and get an authored empty state rather than a blank card or a fabricated match. The missing side is itself the point about a young second league.',
			'A WPL side’s "nearest men’s season-star by style" is the IPL season whose ball-by-ball shot mix sits closest to that team’s, measured by the same Jensen-Shannon distance the map uses. For all four WPL sisters and UP Warriorz it comes out as IPL 2008, the same early-IPL dialect the whole chapter has been tracing.',
			'Five grounds have hosted both leagues: Arun Jaitley in Delhi, Brabourne and DY Patil across Mumbai and Navi Mumbai, Ekana in Lucknow, and Chinnaswamy in Bengaluru. Every card is built by the pipeline from one 16-variant table, snapshot-tested, never typed by hand.'
		]
	},

	/* ---- Chapter 7 · The Twelfth Man (r4b) -----------------------------------
	 * The hero leads on screen as "the control group"; the technical names —
	 * difference-in-differences, the event study, the t-statistic, entry entropy —
	 * live here, one click deep (the glossary rule). Numbers track ch7.json. */
	'ch7-rivers': {
		title: 'How the two rivers, and the control group, are built',
		paragraphs: [
			'Run rate is all the runs, extras included, per six legal balls; wides and no-balls are left out of the deliveries counted. It is the same formula as Chapter 6’s maturity clock, so the two chapters’ WPL numbers agree. Each river’s height at a season is that league-season’s run rate. The band’s thickness is decoration, a constant, not a count of balls.',
			'The control-group estimate has a technical name: a difference-in-differences. It is the IPL’s change after the rule minus the WPL’s change over the very same window. The men sat inside a fifteen-year band that ran 7.48 to 8.65, then climbed season by season from the rule year on: 8.99 in 2023, 9.56, 9.63, 9.88, about 1.36 an over off the band. The women, with no such rule, drifted only 8.08 to 8.54, about +0.46. Take out that drift and roughly +0.9 of the men’s jump lines up with the rule.',
			'Evidence weight, not proof. Pitches and balls changed over the same window, batting intent had been climbing since the 2018 six-rate break, and the WPL is an imperfect control: four seasons, no true pre-rule period. The rule opened the door. It was not the only thing that walked through. Chapter 10 apportions the credit.',
			'The honest null (its technical name is Batting-Order Fluidity). The twelfth name did not rewire how teams think about the order. The spread of wickets-already-down when each batter walks in (the technical name is entry entropy, measured in bits) held flat across the rule, about 3.04 before and 3.06 after. What changed is intent, not the running order: the top three’s strike rate jumped 131.5 to 155.3 while the tail batted about as often as before.',
			'Two demoted exhibits. Tail Exposure: the safety net is about tail quality, not exposure. The number eight came to the crease about as often after the rule as before (53.4% of innings to 56.2%). Part-Timer Extinction, the bowling dividend: with a spare name to spend, teams reached for one more bowler the year the rule arrived, 5.79 distinct bowlers an innings to 6.12.'
		]
	},
	'ch7-license': {
		title: 'How the licence is measured',
		paragraphs: [
			'The match state is held identical on both sides: at least four wickets down, in overs 7 to 16. Pre-rule is 2020 to 2022, post-rule 2023 to 2026. Strike rate is batter runs per 100 legal balls faced. From that spot it jumped 116.8 to 129.9.',
			'The out-rate is every non-retired dismissal per 100 legal balls at those states. Read it honestly: it did NOT fall. It held essentially flat, 4.88 to 4.95 (the bowler-credited-only view, 4.62 to 4.75, tells the same story). So the claim is aggression up at no material risk premium, never risk down.',
			'The by-position split is over all IPL states, with batting position taken by order of first appearance. Positions 1 to 3 lifted 18.0%, positions 6 to 8 lifted 11.0%. The top order took the licence most. The best batters cashed the free aggression first.',
			'Sample sizes: 6,000 balls and 293 dismissals before the rule; 10,525 balls and 521 dismissals after.'
		]
	},
	'ch7-placebo': {
		title: 'How the placebo test works, and where the subs come from',
		paragraphs: [
			'For every candidate year the "jump" is the mean IPL run rate over the three seasons from that year, minus the mean over the three before it (the same run-rate formula). For a made-up date before the rule, the later window stops at 2022, so no fake date can borrow the real post-2023 climb. Every candidate is worked out once in the pipeline, so dragging the cursor is a lookup, never a live fit in your browser.',
			'The technical name for the whole exercise is a rule-change event study with a placebo test; the jump is measured the same before-and-after way as the control-group estimate. The real 2023 rule date jumps about 1.10 runs an over and stands clear of the whole grey cloud. The biggest a made-up date before the rule ever manages is about 0.55. That size of jump, in runs an over, is exactly what the cursor reads out.',
			'One honest wrinkle, shown on screen. The rule year is not the single largest jump: 2024’s raw size (about 1.16) edges 2023’s (about 1.10), because scoring kept climbing as teams learned the card, exactly the learning curve the playbook shows. The break brackets 2023 and 2024, and 2023 is where it starts.',
			'Where the impact subs come from: the raw Cricsheet match JSON records an Impact Player substitution in a delivery’s "replacements" field, from 2023 on. We infer activation from the entry itself. The ball it is recorded on is where the sub takes effect. Role and concussion substitutions are excluded. That leaves 556 activations across 517 distinct deliveries; the WPL records none, which is exactly what makes it the control arm. Two teams subbing on the same first ball of the second innings is why 556 events land on 517 deliveries.'
		]
	},
	'ch7-playbook': {
		title: 'How impact-sub timing is read',
		paragraphs: [
			'"At the innings break" means the substitution is recorded on the first ball of an innings (over 0, ball 0). Everything else counts as mid-innings. Counting is per substitution event.',
			'The share used at the break fell season by season: 51.8% in 2023, 42.3% in 2024, 35.7% in 2025, ticking back to 39.3% in 2026. Teams stopped burning the card at the obvious moment and started holding it for a mid-innings strike. A league learning its own rule in real time.',
			'A fuller view exists: the sub-timing flow from toss to innings to timing to role to result. It lives here rather than as its own on-screen exhibit, to keep the chapter to one hero and three supporting beats.'
		]
	},
	'ch7-payoff': {
		title: 'How your playbook card is built',
		paragraphs: [
			'One card per franchise: 10 IPL, 5 WPL, and a neutral league-wide card. An IPL card carries that team’s habits: the split of batting versus bowling reinforcements, the most-used impact player, the break-versus-mid timing, and the win rate behind each pattern. Every current IPL side used the rule, so there is no empty state on the men’s side.',
			'Reinforcement type is read from the match state when the sub is activated: if that team is batting it is a batting reinforcement, if fielding a bowling one. Batting reinforcements are recorded on the ball the sub walks in for; bowling ones at the start of the innings their team fields.',
			'A WPL card is the control-arm card. The women’s league never had the rule, which is precisely why anyone can say what the rule did to the men’s. An advantage, never a deficit. Every card is built by the pipeline from one 16-variant table, snapshot-tested, never typed by hand.'
		]
	},

	/* ---- Chapter 8 · The Captain's Brain (r5a) -------------------------------
	 * The belief audit: five beliefs held up to the whole record, four fails and
	 * one pass. On screen every device wears a fan name; the technical names
	 * (field-first share, upheld share, the permutation null, empirical-Bayes
	 * shrinkage, the no-lookahead ordering) live here, one click deep (the
	 * glossary rule). Prose numbers track scenes/ch8.json EXACTLY (the artifact
	 * wins: where a recount differs from an older teaser the recount ships, so
	 * DRS accuracy fell, the cold-return tax grew, momentum is a fail with an
	 * honest residual, and the WPL adopted chase-first on a two-season curve). */
	'ch8-matchdots': {
		title: 'What a match-dot is',
		paragraphs: [
			'Each match-dot is every ball of one match placed at its centroid, with a small jitter disc so a match reads as one soft dot. Every dot is drawn at the same radius and the same brightness, so a run-heavy match is no bigger or brighter than a low-scoring one, because nothing about a dot’s size or glow is a stat.',
			'The 316,199 field balls resolve into 1,331 matches (1,243 IPL plus 88 WPL, minus the super-over exclusions), the same universe as every prior chapter. Each match sits at its start date, so seasons read left to right, and from here every belief re-poses this same cloud.'
		]
	},
	'ch8-toss': {
		title: 'How the two rivers of the toss are counted',
		paragraphs: [
			'Captains chose to field 42.9, 55.8, 82.4, 70.1, 77.1 in 100 across the eras, while the chase won 54.3, 53.1, 59.6, 54.5, 52.8 in 100 over the same eras, and winning the toss led to winning the match about half the time every era. Per season the field-first share ran 55, 39, 35 in the first three years, then broke at 2016 to the low 80s and never came back down (82.4 in 2026).',
			'The honest wrinkle: the field-first surge landed in the same window the chase genuinely paid (59.6 in 100, 2016-19), then chasing decayed back to about 53 while the doctrine stayed locked at 77 to 82, so the belief outlived its evidence. Sample sizes 175, 342, 239, 194, 293 matches by era.',
			'This is a belief-versus-outcome mismatch, not a claim the toss decides matches. “Field-first share” and “batting-second win rate” are the technical names. See also the Double-Header Dew Ledger (ch8-dew).'
		]
	},
	'ch8-review': {
		title: 'How the review chips are counted, and the two outcomes',
		paragraphs: [
			'988 reviews in all, 292 of them right, so 29.6 in 100 paid off. Before the 2022 doubling, 302 reviews at 1.26 a match and 32.8 right; from 2022 on, 686 at 1.87 a match and 28.1 right. Per season the hit rate fell 34.7, 33.1, 29.1, 24.8, 16.9 across 2022 to 2026 (the 2026 count was 118 reviews, so read the last point as one noisy season, not certainty).',
			'The record holds only two outcomes, “struck down” (the call stood) and “upheld” (the call overturned); a review-type field is on barely half and unreliable, the umpire’s-call field on only 140 of 988.',
			'The honest delta: the success rate actively fell, not merely stayed flat. A falling share is equally consistent with better on-field umpiring or more marginal reviews under the doubled allowance, so the grade is scoped to the measured rate, never “the reviewing got dumber”; a struck-down review still confirmed the call and is not “wasted.”',
			'“Review success rate” and “upheld share” are the technical names.'
		]
	},
	'ch8-spell': {
		title: 'What a spell is, and the cold-return tax',
		paragraphs: [
			'A spell is a bowler’s unbroken run of overs from one end; because the laws forbid two overs in a row, this is the consecutive-over run at one end. One-and-done overs ran 54.7 in 2008-10, 62.3 in 2016-19, 64.1 in 2023-26, and 52.2 to 67.8 season to season; the WPL runs highest at 75.3.',
			'The cold-return tax, measured only against other bowlers bowling the same over number (at least five overs a bin), ran +0.16, +0.28, +0.3 an over, or +0.18, +0.34, +0.41 on the stricter cold-re-entry read. The honest delta: the tax roughly doubled, from about a sixth of a run to nearly a third, not the teaser’s stable fifth.',
			'Each strip is a near-median example innings, labeled “one example innings,” chosen so the picture does not overstate the modest 9-point shift; adjacent same-end same-bowler overs merge into one fused bar so a spell reads by connectedness, not by telling bowler hues apart. The WPL tax is dropped on screen (about zero, the over-matched bins are too thin). See also the Matchup Engineering footnote (ch8-matchup).'
		]
	},
	'ch8-momentum': {
		title: 'How momentum is split into the situation and the real part',
		paragraphs: [
			'Each claim asks how much likelier an outcome is right after another. The trap is that outcomes bunch in the same conditions: boundaries come in a rush on a flat pitch or in the powerplay whether or not the last ball went for four. So we deal the deliveries back in a random order hundreds of times, keeping each match and over intact. Whatever the shuffle still produces is just that bunching. Whatever the real order beats it by is the genuine ball-to-ball part.',
			'A boundary after a boundary runs about 16% more often (1.159 in 2023-26). But the shuffle alone already produces about half of that, near 1.08, so roughly half the apparent streak is just the situation. What clears the shuffle, about 7 in every 100, is real, and that real part holds flat across the eras (a residual near 1.072, 1.084, 1.066) even as the bigger raw number fades. A six after a six carries a larger real part, a residual around 1.14 to 1.30: a set batter really does keep clearing the rope.',
			'Also holding the batter fixed barely moves the shuffle (from about 1.078 to 1.087), so the deflator is the situation, not who is batting. A wicket after a wicket runs 0.926: after a wicket the next ball is a touch safer, not more dangerous, and it never clears the shuffle, so the collapse is a myth. It clears the fuller test only in the 2016-19 window, so the myth grade is scoped to today’s game. This is consistent with Collapse Contagion, the aftershock read in Chapter 9.',
			'So the belief as sold on television is overstated, not empty: the collapse half is a myth, and the hot-streak half is about half real. The technical names are the permutation null (the shuffle), autocorrelation (the claim), and the batter-stratified null (holding the batter fixed).'
		]
	},
	'ch8-required': {
		title: 'How the chase-pacing curve is read',
		paragraphs: [
			'Chase run rate by phase, powerplay then middle then death: 7.62, 7.61, 8.99 in 2008-10; 8.42, 7.84, 9.81 in 2016-19; 9.19, 8.75, 10.38 in 2023-26. The powerplay jumped +1.57 to sit above the middle overs, the shape flipping from up-sloping to front-loaded.',
			'Read on real chases only (second innings, non-rain-shortened, a full 20-over target); the death rates are conditioned on the chases that lasted that long, so the shape-flip leans on the powerplay jump. Teams ahead of the going rate at the 10-over mark rose from 31.7 to 37.5.',
			'The pacing genuinely changed, but it does not mean chasing wins more, which stayed flat at about 53 per Belief 1, so the pass is on the pacing shape, not the result. “Required run rate” is the technical name.'
		]
	},
	'ch8-wpl': {
		title: 'The WPL, born into the analytics age',
		paragraphs: [
			'The women’s league chose to field 54.5, 59.1, 100.0, 95.5 of the time across 2023 to 2026, pooling to 77.3, almost exactly the men’s pooled rate; the per-season match counts were 22, 22, 22, 22, so 100 in a season is a small sample, not certainty. Its reviews paid off 30.5 of the time across 203 reviews, next to the men’s 29.6; its one-and-done over share was 75.3, above the modern men’s 64.1.',
			'The chase-win figure of 59.8 is a bare fact and never caused, so it must not read as the doctrine working in the WPL. The teaser said the women’s league inherited chase-first fully formed from season one; the recount shows season one at 54.5, about the men’s 2008 rate, then a hard two-season ramp to near 100, so the culture arrived fast but it did arrive.',
			'The men’s game took the better part of a decade and settled around three-quarters, never reaching the WPL’s near-100, so no “fifteen years to get there” claim is made. The WPL is framed only as a league born into the analytics age, arriving with the culture before the history. See also the Double-Header Dew Ledger (ch8-dew).'
		]
	},
	'ch8-payoff': {
		title: 'How your captains’ report card is built',
		paragraphs: [
			'The home ground is the franchise’s most-frequent venue; the home toss share is how often its own captains chose to field there; the home chase-win is its win rate batting second at home; the review-discipline rank is league-wide review success by franchise. On about twenty home games each, the home toss share and the home chase-win are two separate facts, not cause and effect, so read them lightly.',
			'The review-discipline leaderboard runs best to worst RCB 38.7, RR 33.6, SRH 32.7, MI 32.4, CSK 29.7, KKR 27.7, PBKS 27.7, LSG 25.8, GT 25.3, DC 19.4.',
			'The WPL card is the analytics-native beat made personal, never a deficit card. See also the Matchup Engineering footnote (ch8-matchup).'
		]
	},
	'ch8-matchup': {
		title: 'The matchup era, and how a head-to-head record is read',
		paragraphs: [
			'Lead with the raw material growing, not the score. How much head-to-head history a captain has to work with exploded: the share of balls where the batter and bowler had already faced each other at least a dozen deliveries was 12.4 in 2009, 42.1 by 2019, and about 32 after the 2022 expansion diluted the pool with new teams (29.8, 33.0, 34.2 across the recent seasons), more than tripling in a decade.',
			'The score itself is weak: judged only on what was known before each ball, captains landed on a best-third matchup about 30 in 100 against 25 by luck, roughly 1.2 times, with no adoption ramp and confounded by simpler pace-versus-spin and left-right logic, so we do not put it on screen.',
			'Each pair’s record is built with no peeking (matches ordered by real date, a ball sees only deliveries strictly before it; three snapshot tests confirm zero lookahead on all 33,772 pairs), and a thin sample is pulled toward the league average of 1.3322 runs a ball until a pair has earned about 51 balls of weight. Empirical-Bayes shrinkage and the no-lookahead ordering are the technical names.'
		]
	},
	'ch8-dew': {
		title: 'The Double-Header Dew Ledger',
		paragraphs: [
			'Part of why captains choose to field is not belief at all, it is the weather. In day-night matches the evening dew makes the ball skid wet and hard to grip, so bowling second is genuinely harder, which is exactly why a captain who wins the toss puts the other side in and takes the chase. The Double-Header Dew Ledger tracks how much of the field-first surge sits in dew-prone evening slots and double-headers, and it grows with the schedule.',
			'We keep this off the main grade because it does not change the verdict (the chase-win rate stayed flat whether or not dew was in play), but it is the honest caveat on Belief 1: not every captain choosing to field is chasing a myth, some are just reading the sky. The WPL plays many day-night double-headers, so it is especially exposed to dew, part of why its field-first curve ramped so fast.'
		]
	},

	/* ---- Chapter 9 · The Living League (r5b) ---------------------------------
	 * The chapter's single point: institutions churn, the human fabric persists.
	 * On screen every device wears a fan name; the technical names (the
	 * force-directed player-duel graph, empirical-Bayes shrinkage, Jaccard squad
	 * overlap, distinct franchises across a career, the Hawkes aftershock) live
	 * here, one click deep (the glossary rule). Prose numbers track
	 * scenes/ch9.json EXACTLY (the artifact wins: the three honest deltas ship
	 * straight, 232 duels over eight seasons not 235, one-club players ~27 in 100
	 * to ~12 not 28 to 15, and the mega-auction trough mean 0.186 not 0.185). */
	'ch9-duel': {
		title: 'What a duel is, and who came out on top',
		paragraphs: [
			'A duel is a batter and a bowler who faced each other at least thirty legal balls across the whole history. There are 1,691 of them, between 277 players, 244 in the men’s league and 33 in the women’s. Wides do not count toward those thirty balls; no-balls do, the same rule the rest of the piece uses. The technical name for the whole picture is a force-directed player-duel graph: the 277 players are its points and each duel is a link between two of them.',
			'Of the 316,199 balls, 79,378 land in one of those duels, about a quarter of every ball ever bowled. The other 236,821 stay as dust, the deliveries that never became a lasting rivalry.',
			'The busiest players sit dead centre, because everyone has a rivalry with them: Kohli has 76 duels, then Dhawan 65, Jadeja 59, and Rohit 57. Players also spread out by era, the 2008 crowd drifting to one edge and today’s stars to the other, so the layout itself reads as a timeline. It is computed once in the pipeline from a fixed seed, so it is the same web for every reader, and never re-fitted in your browser.',
			'A strand’s color is how many runs a ball the batter scored against that bowler, measured against the league average of 1.3322 runs a ball. The value is pulled toward that average until the pair has faced enough balls to earn its own read, about fifty, so a thirty-ball duel never out-shouts a hundred-and-sixty-ball one. It is then clamped to a scale from plus one (all batter, deep red) to minus one (all bowler, deep blue), where a pale strand was an even fight. The technical name for that pull toward the average is empirical-Bayes shrinkage.',
			'The headline rivalry, Kohli and Jadeja: 160 balls, 179 runs, 3 dismissals, across 14 seasons from 2009 to 2025. The shrunk read comes out to about 1.17 runs a ball, below the league average, so the strand runs bowler-blue, about minus a half on that scale. Jadeja edged it.',
			'232 duels have run eight seasons or longer, counting only the seasons a pair actually faced a ball. That strict recount ships 232 rather than an earlier teaser’s 235, a difference of about one in a hundred. The thirty-ball cutoff is not load-bearing: dropping it adds shorter, noisier duels without changing the web’s shape, and raising it thins the tail but keeps every central player. See Collapse Contagion (ch9-collapse) for the wicket-brings-a-wicket read that Chapter 8 tested.',
			'The men’s and women’s leagues share no players, so they are laid out as two separate webs and never mixed. The women’s web has its own 33 players, and its rivalry structure is compared to the men’s only at a matched age: how many decade-scale rivalries each league had formed by its third season, the WPL against the IPL’s first three years, so the comparison is fair by age and not by calendar.'
		]
	},
	'ch9-heartbeat': {
		title: 'How the auction heartbeat is counted',
		paragraphs: [
			'For each team we ask what share of last season’s squad is back this season, then average that across the league. A full re-auction resets almost everyone at once, so the line falls off a cliff. The technical name for one team’s share is the Jaccard overlap of its two squads; the line drawn on screen is the league mean of it, season over season.',
			'The full per-season series: 2009 .421, 2010 .523, 2011 .175, 2012 .474, 2013 .471, 2014 .191, 2015 .484, 2016 .430, 2017 .479, 2018 .179, 2019 .468, 2020 .426, 2021 .504, 2022 .196, 2023 .430, 2024 .419, 2025 .190, 2026 .458. The five mega-auction years, 2011, 2014, 2018, 2022, and 2025, are the five lowest, averaging 0.186 against 0.461 in every other year. The gap is clean: the sixth-lowest season, 2024, sits all the way up at .419.',
			'Franchises are tracked by their canonical identity, so a team that only changed its name keeps one identity and is never counted as a fresh squad.',
			'The season scrub in the synthesis scene is built the same way: each strand knows the seasons its two players actually faced a ball, so scrubbing lights a strand only in those years, and the five reset markers are the mega-auction years from this heartbeat. The web positions never move during the scrub, only which strands are lit, so the survival is honest: the rivalries genuinely span the reset years, they are not redrawn to look continuous.',
			'The women’s league has its own pulse: a steady squad through its early seasons, 2024 at .476 and 2025 at .536, then its first big reset in 2026 at .257. That is a young league’s compressed auction cycle, never a league behind.'
		]
	},
	'ch9-loyalty': {
		title: 'How a one-club player is counted',
		paragraphs: [
			'A one-club player is a player in their fourth season or later who has only ever appeared for one franchise, counted season by season. Requiring a fourth season keeps out one-season cameos, so the measure is about players with real careers, not passers-through.',
			'That share fell from about 27 in 100 to about 12 across the seasons, roughly a halving. It ships straight, rather than an earlier teaser’s roughly 28 in 100 down to 15, a couple of points off.',
			'At the other extreme, Aaron Finch appeared for nine different franchises, the most of any player: Delhi Capitals, Gujarat Lions, Kolkata Knight Riders, Mumbai Indians, Pune Warriors India, Punjab Kings, Rajasthan Royals, Royal Challengers Bengaluru, and Sunrisers Hyderabad.',
			'A franchise that only changed its name counts as one club, so a player who stayed through a rename is still a one-club player. The technical name for what this counts is distinct franchises across a career.'
		]
	},
	'ch9-payoff': {
		title: 'How your team’s card is built',
		paragraphs: [
			'Each card carries your franchise’s own three reads. The longest rivalry is the team’s duel that spans the most seasons; the reset row counts who left and who arrived in the team’s mega-auction years; the loyal player is its longest-serving one-club player. All three come straight from the per-franchise tables the pipeline emits, and every number on the card equals those tables exactly.',
			'A young franchise has had fewer years to grow decade-scale rivalries, so its longest may be shorter than an older club’s. That is a fact about its age, never a deficit.',
			'The women’s-league card is the forming-fast beat made personal, never a deficit card. If you have not picked a team, the neutral card carries the league-wide reads instead: the single longest rivalry of all, Kohli and Jadeja; the five mega-auction resets; and the vanishing one-club player.'
		]
	},
	'ch9-collapse': {
		title: 'Collapse Contagion, the aftershock that isn’t',
		paragraphs: [
			'The dressing-room belief is that one wicket brings another, a collapse. The record says the opposite. Right after a wicket falls, the next ball is a touch safer, not more dangerous: a second wicket comes at about 0.94 times its usual rate, below one.',
			'That lines up with the belief audit in Chapter 8, where a wicket after a wicket ran about 0.93 (ch8-momentum). So the collapse is a story, not a mechanism: wickets do not summon more wickets. The technical name for a does-an-event-trigger-more-of-itself read is a Hawkes aftershock model, and here the ratio sits below one, meaning a wicket dampens the next rather than exciting it.',
			'It is the contrarian companion to Chapter 8’s momentum beat, demoted to this footnote on purpose: the chapter’s on-screen budget is two heroes and one supporting beat, so Collapse Contagion earns a mention here, not a scene of its own.'
		]
	}
} as const satisfies Record<string, FootnoteEntry>;

export type FootnoteId = keyof typeof FOOTNOTES;

export function isFootnoteId(id: string | null): id is FootnoteId {
	return id !== null && Object.prototype.hasOwnProperty.call(FOOTNOTES, id);
}
