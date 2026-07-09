<script lang="ts">
	import { base } from '$app/paths';

	/**
	 * Methods page (storyboard §5): the honest core behind every on-screen
	 * number — data sources + ODbL attribution, what counts as a ball, season
	 * normalization, era bands, and the repo. Fans-first register; this is the
	 * one place technical names are introduced as "the technical name for
	 * this." Prerendered, linked from the end card and from footnote sheets.
	 * Grows every release.
	 */
	const REPO = 'https://github.com/lyndonkl/iplprogress';
</script>

<svelte:head>
	<title>Every Ball Ever — How we computed this</title>
	<meta
		name="description"
		content="Data sources, definitions, and methods behind Every Ball Ever: Cricsheet ball-by-ball data under ODbL, what counts as a ball, season normalization, era bands, and how every on-screen number is computed."
	/>
</svelte:head>

<main>
	<p class="overline">Every Ball Ever</p>
	<h1>How we computed this</h1>
	<p class="lede">
		Every number in the story traces to an artifact built by a deterministic pipeline from
		public ball-by-ball data — same input, same bytes out, every time. This page is the honest
		core: what we counted, what we excluded, and why. It grows with each release.
	</p>

	<section id="corpus">
		<h2>The corpus</h2>
		<p>
			Everything starts from <a href="https://cricsheet.org/">Cricsheet</a>’s ball-by-ball
			JSON: 1,243 IPL matches (2008–2026) and 88 WPL matches (2023–2026) — 1,331 matches
			across 19 IPL seasons and 4 WPL seasons, with 937 players counted by registry ID rather
			than by name, so one player written two ways stays one player and two players who share a
			name stay two. Every count the story shows is read from
			the pipeline’s emitted artifacts (<code>meta.json</code> and friends) — the artifact,
			not the prose, is the source of truth; if the two ever disagree, the artifact wins and
			the copy changes.
		</p>
	</section>

	<section id="what-counts-as-a-ball">
		<h2>What counts as a ball</h2>
		<p>
			Every legal and illegal delivery recorded by Cricsheet — except super overs. The corpus
			holds <strong>316,388</strong> deliveries; 189 of them belong to the 17 tie-match super
			overs (36 super-over innings), and those 189 are excluded from the field and from every
			ball-level stat. So the number the screen shows — <strong>316,199</strong> — is exactly
			the number that’s there. House rule: never show a number the pixels contradict.
		</p>
		<p>
			Conventions used throughout: wides don’t count toward a batter’s balls faced (the
			batter never faced them); no-balls do. A dot ball is a legal delivery with zero total
			runs. Strike rate is runs off the bat per 100 balls faced.
		</p>
	</section>

	<section id="season-normalization">
		<h2>One season, one label</h2>
		<p>
			Cricsheet labels a few editions with split years; the pipeline collapses each to its
			edition year — 2007/08→2008, 2009/10→2010, 2020/21→2020 — so “2008” means the same
			season in every chart, caption, and buffer. That normalization is why the piece counts
			19 IPL seasons, 2008 through 2026, with no gaps and no doubles.
		</p>
	</section>

	<section id="era-bands">
		<h2>Era bands</h2>
		<p>
			When the story says “then vs now,” <em>then</em> is IPL 2008–2010 and <em>now</em> is
			IPL 2023–2026: the league’s first three seasons against its latest four. Curves that
			need finer resolution use five IPL bands — 2008–10, 2011–15, 2016–19, 2020–22, 2023–26.
			Bands exist because single seasons are noisy; pooled, the first-ten-ball samples run
			from about 20,100 balls (2008–10) to about 33,900 (2023–26), enough that a curve’s
			shape is signal rather than luck.
		</p>
		<p>
			The WPL is pooled as one band — four seasons, 88 matches, 20,642 deliveries, about
			10,200 first-ten balls. It is a young league and its numbers will move; the story says
			so wherever they appear. Each scene’s ⓘ footnote repeats the band definitions and
			sample sizes it relies on.
		</p>
	</section>

	<section id="out-rate">
		<h2>The out-rate, ball by ball</h2>
		<p>
			In the story we call it “how often a batter gets out on exactly that ball.” The
			technical name is a discrete-time hazard curve, estimated Kaplan-Meier-style:
			dismissals at ball <em>n</em> divided by batter-innings that reached ball <em>n</em>.
			Not-out innings are censored — they count while observed, then stop counting — as are
			the corpus’s 10 retired-hurt and 5 tactical retired-out innings. Run-outs count against
			the batter given out, non-strikers included, at their own ball count. The out-rate is
			risk per ball; strike rate is runs per ball. They move independently — which is exactly
			Chapter 1’s point.
		</p>
	</section>

	<section id="aerial-proxy">
		<h2>Aerial attempts (a proxy)</h2>
		<p>
			The public record doesn’t say whether a batter swung hard, so we use a proxy: aerial
			attempts = sixes + caught dismissals (caught-and-bowled excluded), and execution =
			sixes as a share of attempts. Caught includes keeper and slip edges — noise, but
			<em>stable</em> noise, so era-to-era comparisons hold even though any single number
			carries this caveat. True shot-level intent would need ball-tracking data that isn’t
			public.
		</p>
	</section>

	<section id="the-draw">
		<h2>The draw</h2>
		<p>
			The cold-open truth series counts 200-run innings per season — any innings, either
			batting side, super overs excluded. The 2008–2012 segment comes pre-drawn from the real
			values to anchor the sketch. The reveal’s copy branches are decided by documented
			constants applied to your drawn values, evaluated in a fixed order; your sketch is
			stored only in your browser. Aggregated sketch statistics may be published in a later
			release.
		</p>
	</section>

	<section id="payoff-cards">
		<h2>Payoff cards</h2>
		<p>
			Team payoff cards are strictly template + per-team JSON emitted by the pipeline — never
			hand-authored. A snapshot harness asserts all 16 variants (10 IPL + 5 WPL + neutral)
			exist and are non-degenerate, including the designed empty states for franchises born
			after 2010. Franchise renames merge histories: Delhi Daredevils→Delhi Capitals,
			Kings XI Punjab→Punjab Kings, Royal Challengers Bangalore→Bengaluru. Defunct franchises
			(Deccan Chargers, Kochi Tuskers Kerala, Pune Warriors, Rising Pune Supergiant, Gujarat
			Lions) keep their own
			identities — their balls are on the field; they just aren’t pickable.
		</p>
	</section>

	<section id="rendering">
		<h2>Rendering honesty</h2>
		<p>
			The render loop stops whenever nothing moves (demand-mode rendering): “the field dims”
			means the GPU rests. Readers with reduced-motion preferences get live-rendered
			end-state jump-cuts — the same renderer, no interpolation, no pre-baked frames — so
			team colors and personalization survive. Layout positions are computed on your device
			from small per-ball attributes; nothing heavier crosses the wire, and a payload ledger
			in the build enforces byte budgets on every artifact the page fetches.
		</p>
	</section>

	<section id="credits">
		<h2>Licenses &amp; credits</h2>
		<p>
			Ball-by-ball data from <a href="https://cricsheet.org/">Cricsheet</a>, used under the
			<a href="https://opendatacommons.org/licenses/odbl/1-0/"
				>Open Data Commons Open Database License (ODbL) 1.0</a
			>. This project’s derived datasets — every JSON and binary buffer the page fetches —
			are shared under the same license, as ODbL’s share-alike terms require. Built with
			SvelteKit, three.js, and GSAP.
		</p>
		<p>
			The code is open: <a href={REPO}>github.com/lyndonkl/iplprogress</a> — the deterministic
			pipeline, the payload ledger, and the snapshot tests behind every number on this page
			live there.
		</p>
	</section>

	<p class="back"><a href="{base}/">← Back to the field</a></p>
</main>

<style>
	main {
		max-width: 42rem;
		margin: 0 auto;
		padding: 4rem 1.4rem 5rem;
	}

	.overline {
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.28em;
		text-transform: uppercase;
		color: var(--gold);
		margin: 0 0 0.6rem;
	}

	h1 {
		margin: 0 0 0.8rem;
		font-size: clamp(1.7rem, 4.5vw, 2.4rem);
		line-height: 1.2;
	}

	.lede {
		color: var(--ink-dim);
		font-size: 1.05rem;
		line-height: 1.55;
		margin: 0 0 2.2rem;
	}

	section {
		margin-bottom: 2rem;
	}

	h2 {
		font-size: 1.15rem;
		margin: 0 0 0.5rem;
	}

	p {
		margin: 0;
		line-height: 1.6;
		font-size: 0.97rem;
		font-variant-numeric: tabular-nums;
	}

	section p + p {
		margin-top: 0.7rem;
	}

	code {
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.85em;
	}

	a {
		color: var(--teal);
	}

	a:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.back {
		margin-top: 3rem;
	}

	.back a {
		/* comfortable tap target on mobile */
		display: inline-block;
		padding: 0.6rem 0;
	}
</style>
