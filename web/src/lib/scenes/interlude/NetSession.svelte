<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { footnotesOpen } from '$lib/state';
	import GridHeat from './GridHeat.svelte';
	import {
		loadInterludeData,
		readWin,
		readRuns,
		eraContrast,
		winHeatSlice,
		presetById,
		isWplEra,
		int,
		IPL_DEFAULT_ERA,
		WPL_ERA,
		DEFAULT_STATE,
		type InterludeData,
		type Preset,
		type League
	} from './data';

	/**
	 * IN-2..IN-5 — the Net Session widget (storyboard §2, §3). ONE pinned
	 * interactive figure: three sliders (overs left, wickets in hand, runs needed)
	 * driving TWO live meters read from the precomputed grid, the three presets
	 * (both currencies), the default-visible same-chase era climax, and the WPL
	 * toggle with its minimum-evidence mask.
	 *
	 * DEMAND-MODE INVARIANT (blocking, storyboard §0.4/§3): this component NEVER
	 * touches `field` and never requests a frame. The shell holds the resting
	 * `free` starfield dimmed; once it settles the render loop STOPS and the GPU is
	 * idle. Dragging a slider updates DOM numbers only. That is what makes the
	 * interlude thermally free during a long dwell on a phone.
	 *
	 * NO LIVE MODEL: both meters are pure array look-ups (client-side required-rate
	 * → bucket → cell). Every on-screen number binds to interlude.json; the copy is
	 * an authored template, the figures are field reads (storyboard §6).
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	/* ---- lazy-load the scene artifact on entry (not in the cold-open payload) - */
	let d = $state<InterludeData | null>(null);
	let loadErr = $state<string | null>(null);
	let started = false;
	$effect(() => {
		if (!(active || progress > 0) || started) return;
		started = true;
		loadInterludeData()
			.then((x) => (d = x))
			.catch((e) => (loadErr = e instanceof Error ? e.message : String(e)));
	});

	/* ---- the reader's controls (ephemeral component state, never persisted) --- */
	let oL = $state(DEFAULT_STATE.overs_left);
	let w = $state(DEFAULT_STATE.wickets_in_hand);
	let R = $state(DEFAULT_STATE.runs_needed);
	let league = $state<League>('ipl');
	let activePresetId = $state<string | null>(null);
	let lastTouched = $state<'overs' | 'wkts' | 'runs' | null>(null);
	let showGrid = $state(false);

	/* ---- the era surface both meters read ------------------------------------
	   Free play reads the best-evidenced all-history IPL surface; a preset reads
	   its own named era (so the preset's number always equals its own copy); the
	   WPL toggle reads the women's surface. `iplEra` is PERSISTENT, not derived
	   from the preset, so that dragging runs-needed can never move Meter A even
	   right after a preset: a runs-drag leaves the era untouched (the whole point
	   of the runs-needed non-response), while an overs/wickets drag returns to
	   free-play all-history (Meter A changes there anyway, so no lesson breaks). */
	let iplEra = $state<string>(IPL_DEFAULT_ERA);
	const activePreset = $derived<Preset | null>(
		d && activePresetId ? presetById(d, activePresetId) ?? null : null
	);
	const era = $derived(league === 'wpl' ? WPL_ERA : iplEra);

	const winRead = $derived(d ? readWin(d, era, oL, w, R) : null);
	const runsRead = $derived(d ? readRuns(d, era, oL, w) : null);
	const contrast = $derived(d ? eraContrast(d) : null);
	const heat = $derived(d && showGrid ? winHeatSlice(d, era, oL, w, R) : null);

	/* the runs-needed non-response: while runs-needed is the live control, Meter A
	   visibly does NOT move — say why, so it reads as correct, not broken. */
	const runsHeld = $derived(lastTouched === 'runs' && !!runsRead && !runsRead.masked);

	/* ---- polite live region: the accessible path IS the primary path here ----- */
	const announce = $derived.by(() => {
		if (!d || !winRead || !runsRead) return '';
		const onWpl = league === 'wpl' ? 'On the women’s game. ' : '';
		if (winRead.masked && runsRead.masked)
			return `${onWpl}Not enough WPL cricket from this exact spot yet. Both meters are waiting for more matches.`;
		// same evidence rule spoken for both leagues: a WPL hole waits for matches,
		// a thin IPL cell reads a filled-in-by-rule number, never a bare fact.
		const winPart = winRead.masked
			? 'the win meter is waiting for more WPL matches'
			: winRead.thin
				? `teams win about ${winRead.display} in 100, but that is filled in by rule, not counted, too few real chases from this exact spot yet`
				: `teams win about ${winRead.display} in 100`;
		const runsPart = runsRead.masked
			? 'the runs meter is waiting for more WPL matches'
			: runsRead.thin
				? `a team usually still gets about ${runsRead.display}, filled in by rule, not counted`
				: `a team usually still gets about ${runsRead.display}`;
		if (runsHeld)
			return `${winPart}. The runs meter reads your batting, not the target, so it holds at about ${runsRead.display}.`;
		return `${onWpl}${winPart}, and ${runsPart}.`;
	});

	/* ---- coaching caption step (guidance only; the widget works regardless) ---- */
	const coach = $derived.by(() => {
		if (progress < 0.28) return 1;
		if (progress < 0.52) return 2;
		if (progress < 0.76) return 3;
		return 4;
	});

	/* ---- handlers ------------------------------------------------------------- */
	function touch(which: 'overs' | 'wkts' | 'runs'): void {
		lastTouched = which;
		activePresetId = null; // any drag = free play
		// an overs/wickets drag returns to all-history; a runs drag leaves the era
		// alone so Meter A genuinely HOLDS (the runs-needed non-response, §2d)
		if (which !== 'runs') iplEra = IPL_DEFAULT_ERA;
	}

	function applyPreset(p: Preset): void {
		oL = p.state.overs_left;
		w = p.state.wickets_in_hand;
		R = p.state.runs_needed;
		league = 'ipl';
		iplEra = p.era; // the preset's own named era → its meter equals its own copy
		activePresetId = p.id;
		lastTouched = null;
	}

	function setLeague(next: League): void {
		league = next;
		activePresetId = null;
		lastTouched = null;
		if (next === 'ipl') iplEra = IPL_DEFAULT_ERA; // back to men's free-play, all history
	}

	function openMethods(): void {
		footnotesOpen.set('netsession');
	}
</script>

<div class="pin" class:active>
	<!-- coaching: the coach in the nets, one prompt at a time. Announced politely
	     (role=note + aria-live) so the guided-drag instructions reach keyboard and
	     screen-reader readers too — the accessible path is the primary path (§0.8). -->
	<div class="coach" role="note" aria-live="polite">
		{#if coach === 1}
			<p>This is a chase, frozen. Three dials set the scoreboard. Two meters read it back.</p>
		{:else if coach === 2}
			<p>Have a drag. Slide the overs down and both meters fall. Knock a wicket off early and the win meter drops a long way. Early on, wickets are the whole game.</p>
		{:else if coach === 3}
			<p>Drop the overs to two, then move runs needed. Late on, the wicket barely matters and the ask is everything. Or tap a famous spot below.</p>
		{:else}
			<p>Flip it to the WPL, the same two dials on the women’s game. Where the real matches run thin, it says so instead of guessing.</p>
		{/if}
	</div>

	<div class="widget" role="group" aria-label="The Net Session, a chase you can drag around">
		{#if !d}
			<div class="inner loading">
				{#if loadErr}
					<p class="err">Couldn’t load the net session ({loadErr}).</p>
				{:else}
					<p class="loading-note">Setting up the net session…</p>
				{/if}
			</div>
		{:else}
			<div class="inner">
				<!-- METERS: pinned to the top so the changing number is never hidden
				     under the thumb on the lowest slider (§0.6). Meter A (runs) leads,
				     then Meter B (win), per §2b; single full-width column on a phone. -->
				<div class="meters">
					<!-- METER A — runs you'll probably still get -->
					<div
						class="meter"
						class:wpl={league === 'wpl'}
						class:held={runsHeld}
						class:thin={runsRead?.thin}
					>
						<p class="m-label">{d.meters.runs.label}</p>
						{#if runsRead?.masked}
							<p class="m-hole">Not enough<br />WPL cricket yet</p>
						{:else}
							<p class="m-value" class:est={runsRead?.thin}>
								<span class="big">{runsRead?.display}</span>
							</p>
						{/if}
						{#if runsHeld}
							<p class="m-note">This reads your batting, not the target.</p>
						{:else if runsRead?.thin}
							<p class="m-flag">Filled in by rule, not counted. Too few real innings from this exact spot yet.</p>
						{:else}
							<p class="m-gloss">From the batting you have left, not the target.</p>
						{/if}
					</div>

					<!-- METER B — how often teams win from here -->
					<div class="meter" class:wpl={league === 'wpl'} class:thin={winRead?.thin}>
						<p class="m-label">{d.meters.win.label}</p>
						{#if winRead?.masked}
							<p class="m-hole">Not enough<br />WPL cricket yet</p>
						{:else}
							<p class="m-value" class:est={winRead?.thin}>
								<span class="big">{winRead?.display}</span><span class="unit">in 100</span>
							</p>
						{/if}
						{#if winRead?.thin}
							<p class="m-flag">Filled in by rule, not counted. Too few real chases from this exact spot yet.</p>
						{:else}
							<p class="m-gloss">{d.meters.win.gloss}</p>
						{/if}
					</div>
				</div>

				<!-- THE READING moved directly under the sticky meters so the default-
				     visible era climax is in the first viewport on a small phone (the
				     ~85% who never drag, §IN-4); the dials and presets sit below it. -->
				<div class="reading" aria-live="off">
					{#if activePreset}
						{@const p = activePreset}
						{#if p.id === 'dhoni_2018_chase'}
							<p class="r-lead">
								Chennai chasing {p.match?.target}, 2018, Dhoni set at the crease. {p.state.overs_left}
								overs left, {p.state.wickets_in_hand} wickets in hand, still {p.state.runs_needed} to
								get.
							</p>
							<p class="r-quiet">
								From a spot this steep teams usually make about {p.expected_runs_display} more runs and
								win about {p.win_display} in 100. Dhoni got them there anyway.
							</p>
						{:else if p.id === 'same_chase_2025'}
							<p class="r-lead">
								The same one square, now in 2025. Nothing on the sliders moved. Ten overs left, three
								down, needing 100.
							</p>
							<p class="r-quiet">
								From this exact spot teams now win about {p.win_display} in 100 and make about {p.expected_runs_display}
								more. Same square, later era, and the chase got kinder.
							</p>
						{:else}
							<p class="r-lead">
								One exact square, back in 2010. Ten overs left, three down, needing 100. That is ten an
								over.
							</p>
							<p class="r-quiet">
								From this one spot teams won about {p.win_display} in 100 and usually made about {p.expected_runs_display}
								more. Now press “the same chase, 2025” and watch only the year change.
							</p>
						{/if}
					{:else if league === 'wpl'}
						<p class="r-lead">
							The same two dials, now on the women’s game. It has played {d.corpus.wpl_matches} matches,
							not {int(d.corpus.matches)}, so at a spot like this there is not enough of it yet, and the
							meter tells you so instead of guessing.
						</p>
						<p class="r-quiet">We would rather show you a hole than dress a guess up as a finding.</p>
					{:else if contrast}
						<p class="r-head">The same chase, then and now</p>
						<p class="r-lead">
							Needing nine an over with ten overs left came off about {contrast.winThen} in 100 back in
							2008 to 2012. The same scoreboard now, in 2023 to 2026, comes off about {contrast.winNow}.
							About {contrast.winGap} more wins in a hundred, and nothing on the board changed.
						</p>
						<p class="r-quiet">
							Teams even score a touch more from there now, about {contrast.runsNow} where it used to be
							about {contrast.runsThen}.
						</p>
					{/if}
				</div>

				<p class="methods-link">
					<button type="button" onclick={openMethods}>ⓘ how we worked this out</button>
				</p>

				<!-- DIALS -->
				<div class="dials">
					<label class="dial">
						<span class="d-top">
							<span class="d-name">{d.sliders.overs_left}</span>
							<span class="d-val">{oL}</span>
						</span>
						<input
							type="range"
							min={d.state_space.overs_left.min}
							max={d.state_space.overs_left.max}
							step="1"
							bind:value={oL}
							oninput={() => touch('overs')}
							aria-label="{d.sliders.overs_left}, how much batting time is left"
						/>
						<span class="d-ends" aria-hidden="true"><span>{d.state_space.overs_left.min}</span><span>{d.state_space.overs_left.max}</span></span>
						<span class="d-gloss">How much batting time is left.</span>
					</label>

					<label class="dial">
						<span class="d-top">
							<span class="d-name">{d.sliders.wickets_in_hand}</span>
							<span class="d-val">{w}</span>
						</span>
						<input
							type="range"
							min={d.state_space.wickets_in_hand.min}
							max={d.state_space.wickets_in_hand.max}
							step="1"
							bind:value={w}
							oninput={() => touch('wkts')}
							aria-label="{d.sliders.wickets_in_hand}, how many batters you have to come"
						/>
						<span class="d-ends" aria-hidden="true"><span>{d.state_space.wickets_in_hand.min}</span><span>{d.state_space.wickets_in_hand.max}</span></span>
						<span class="d-gloss">How many batters you have still to come.</span>
					</label>

					<label class="dial">
						<span class="d-top">
							<span class="d-name">{d.sliders.runs_needed}</span>
							<span class="d-val">{R}</span>
						</span>
						<input
							type="range"
							min={d.state_space.runs_needed.min}
							max={d.state_space.runs_needed.max}
							step="1"
							bind:value={R}
							oninput={() => touch('runs')}
							aria-label="{d.sliders.runs_needed}, how far from the target"
						/>
						<span class="d-ends" aria-hidden="true"><span>{d.state_space.runs_needed.min}</span><span>{d.state_space.runs_needed.max}</span></span>
						<span class="d-gloss">How far you are from the target.</span>
					</label>
				</div>

				<!-- PRESETS: both currencies, bound to the grid -->
				<div class="presets">
					<p class="p-head">Or drop into a real spot</p>
					<div class="p-row">
						{#each d.presets as p (p.id)}
							<button
								type="button"
								class="preset"
								class:on={activePresetId === p.id}
								aria-pressed={activePresetId === p.id}
								onclick={() => applyPreset(p)}
							>
								<span class="pk">{p.label}</span>
								<span class="pv">{p.expected_runs_display} runs · {p.win_display} in 100</span>
							</button>
						{/each}
					</div>
				</div>

				<!-- SWITCHES: WPL league toggle + the optional grid disclosure -->
				<div class="switches">
					<div class="switch" role="group" aria-label="Which league">
						<button
							type="button"
							class="seg"
							class:on={league === 'ipl'}
							aria-pressed={league === 'ipl'}
							onclick={() => setLeague('ipl')}>IPL</button
						>
						<button
							type="button"
							class="seg"
							class:on={league === 'wpl'}
							aria-pressed={league === 'wpl'}
							onclick={() => setLeague('wpl')}>WPL</button
						>
					</div>
					<button
						type="button"
						class="disclosure"
						aria-expanded={showGrid}
						onclick={() => (showGrid = !showGrid)}
					>
						{showGrid ? 'Hide the table' : 'Show the table'}
					</button>
				</div>

				{#if heat}
					<GridHeat rows={heat.rows} wpl={isWplEra(era)} />
				{/if}
			</div>
		{/if}
	</div>

	<!-- the accessible path is the primary path: announce every change, and
	     explain the runs-needed non-response so it reads as correct, not broken -->
	<div class="sr-only" aria-live="polite" role="status">{announce}</div>
</div>

<style>
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
		pointer-events: none;
	}

	.pin.active {
		visibility: visible;
	}

	/* ---- coaching caption: top-left on desktop (clear of ☰), slim top strip on
	   mobile so it never covers the widget (§0.6) ---- */
	.coach {
		position: absolute;
		top: 12px;
		left: 6vw;
		max-width: min(22rem, 40vw);
		font-size: clamp(0.9rem, 1.6vw, 1.05rem);
		line-height: 1.45;
		color: var(--ink-dim);
	}

	.coach p {
		margin: 0;
	}

	/* ---- the widget itself ---- */
	.widget {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: min(30rem, 94vw);
		max-height: 92dvh;
		pointer-events: auto;
	}

	.inner {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		max-height: 92dvh;
		overflow-y: auto;
		padding: 0.9rem;
		border-radius: 16px;
		border: 1px solid rgba(232, 236, 245, 0.12);
		background: rgba(11, 14, 20, 0.86);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
	}

	.loading {
		align-items: center;
		justify-content: center;
		min-height: 8rem;
	}

	.loading-note {
		color: var(--ink-dim);
		font-size: 0.9rem;
	}

	.err {
		color: var(--ember);
		font-size: 0.85rem;
	}

	/* ---- meters: pinned to the top of the scrollable widget ---- */
	.meters {
		position: sticky;
		top: 0;
		z-index: 2;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
		padding-bottom: 2px;
		background: rgba(11, 14, 20, 0.86);
	}

	.meter {
		padding: 0.6rem 0.7rem 0.65rem;
		border-radius: 12px;
		border: 1px solid rgba(232, 236, 245, 0.12);
		background: rgba(232, 236, 245, 0.04);
	}

	.meter.wpl {
		border-color: rgba(46, 196, 182, 0.4);
	}

	.m-label {
		margin: 0;
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.02em;
		line-height: 1.2;
		color: var(--ink-dim);
		min-height: 1.6em;
	}

	.m-value {
		margin: 0.25rem 0 0;
		display: flex;
		align-items: baseline;
		gap: 0.28rem;
	}

	.m-value .big {
		font-size: clamp(1.9rem, 8vw, 2.7rem);
		font-weight: 800;
		line-height: 0.95;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.m-value .unit {
		font-size: 0.78rem;
		color: var(--ink-dim);
	}

	.m-hole {
		margin: 0.35rem 0 0.1rem;
		font-size: 0.92rem;
		font-weight: 700;
		line-height: 1.15;
		color: var(--teal);
	}

	.m-gloss,
	.m-note {
		margin: 0.3rem 0 0;
		font-size: 0.7rem;
		line-height: 1.35;
		color: var(--ink-dim);
	}

	.m-note {
		color: var(--gold);
	}

	/* thin ground (§0.1/§2d): an IPL free-play cell below the evidence threshold.
	   The number still shows, but demoted — faint + italic — and flagged as
	   filled in by rule, so it never reads as an observed finding. Same rule the
	   WPL toggle applies (there it shows the hole instead). */
	.meter.thin {
		border-style: dashed;
		border-color: rgba(232, 236, 245, 0.28);
	}

	.m-value.est .big {
		color: var(--ink-dim);
		font-style: italic;
	}

	.m-flag {
		margin: 0.3rem 0 0;
		font-size: 0.7rem;
		line-height: 1.35;
		font-style: italic;
		color: var(--ink-dim);
	}

	.methods-link {
		margin: 0;
		text-align: right;
	}

	.methods-link button {
		padding: 0.2rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font: inherit;
		font-size: 0.72rem;
		cursor: pointer;
	}

	.methods-link button:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* ---- dials ---- */
	.dials {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.dial {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.d-top {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
	}

	.d-name {
		font-size: 0.8rem;
		font-weight: 650;
		color: var(--ink);
	}

	.d-val {
		font-size: 1rem;
		font-weight: 800;
		color: var(--teal);
		font-variant-numeric: tabular-nums;
	}

	.d-gloss {
		font-size: 0.68rem;
		color: var(--ink-dim);
	}

	/* faint range-extent labels under each track, so the slider's direction reads
	   before the reader drags (min on the left, full innings on the right). */
	.d-ends {
		display: flex;
		justify-content: space-between;
		margin-top: -2px;
		font-size: 0.6rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	input[type='range'] {
		width: 100%;
		height: 44px; /* thumb-safe 44px hit target */
		margin: 0;
		background: transparent;
		cursor: pointer;
		-webkit-appearance: none;
		appearance: none;
	}

	input[type='range']:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 4px;
		border-radius: 4px;
	}

	input[type='range']::-webkit-slider-runnable-track {
		height: 4px;
		border-radius: 999px;
		background: rgba(232, 236, 245, 0.18);
	}

	input[type='range']::-moz-range-track {
		height: 4px;
		border-radius: 999px;
		background: rgba(232, 236, 245, 0.18);
	}

	input[type='range']::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 22px;
		height: 22px;
		margin-top: -9px;
		border-radius: 50%;
		background: var(--teal);
		border: 3px solid #0b0e14;
		box-shadow: 0 0 0 1px var(--teal);
	}

	input[type='range']::-moz-range-thumb {
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: var(--teal);
		border: 3px solid #0b0e14;
		box-shadow: 0 0 0 1px var(--teal);
	}

	/* ---- presets ---- */
	.p-head {
		margin: 0.2rem 0 0.1rem;
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.p-row {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}

	.preset {
		flex: 1 1 auto;
		min-width: 9rem;
		min-height: 44px;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 1px;
		padding: 0.4rem 0.6rem;
		border-radius: 10px;
		border: 1px solid rgba(232, 236, 245, 0.16);
		background: rgba(232, 236, 245, 0.04);
		color: var(--ink);
		font: inherit;
		text-align: left;
		cursor: pointer;
	}

	.preset.on {
		border-color: var(--teal);
		background: rgba(46, 196, 182, 0.16);
	}

	.preset:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.pk {
		font-size: 0.78rem;
		font-weight: 650;
		line-height: 1.2;
	}

	.pv {
		font-size: 0.7rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	/* ---- the reading (adaptive prose: era climax / preset reveal / WPL note) --- */
	.reading {
		padding: 0.55rem 0.65rem;
		border-radius: 10px;
		background: rgba(232, 236, 245, 0.03);
		border-left: 2px solid rgba(46, 196, 182, 0.5);
	}

	.r-head {
		margin: 0 0 0.25rem;
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--gold);
	}

	.r-lead {
		margin: 0;
		font-size: 0.86rem;
		line-height: 1.45;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.r-quiet {
		margin: 0.35rem 0 0;
		font-size: 0.78rem;
		line-height: 1.4;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	/* ---- switches ---- */
	.switches {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
	}

	.switch {
		display: inline-flex;
		border-radius: 10px;
		border: 1px solid rgba(232, 236, 245, 0.16);
		overflow: hidden;
	}

	.seg {
		min-height: 44px;
		padding: 0 1rem;
		border: none;
		background: transparent;
		color: var(--ink-dim);
		font: inherit;
		font-size: 0.82rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		cursor: pointer;
	}

	.seg.on {
		background: rgba(46, 196, 182, 0.18);
		color: var(--ink);
		box-shadow: inset 0 0 0 1px var(--teal);
	}

	.seg:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: -3px;
	}

	.disclosure {
		min-height: 44px;
		padding: 0 0.7rem;
		border: none;
		background: none;
		color: var(--teal);
		font: inherit;
		font-size: 0.78rem;
		cursor: pointer;
	}

	.disclosure:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* ---- screen-reader-only live region ---- */
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	/* ---- mobile: coach becomes a slim top strip; widget fills the rest ---- */
	@media (max-width: 720px) {
		.coach {
			left: 50%;
			transform: translateX(-50%);
			top: 8px;
			max-width: 92vw;
			width: 92vw;
			text-align: center;
			font-size: 0.85rem;
		}

		.widget {
			top: auto;
			bottom: max(10px, env(safe-area-inset-bottom));
			transform: translateX(-50%);
			width: 96vw;
			max-height: 84dvh;
		}

		.inner {
			max-height: 84dvh;
		}

		/* meters stack full-width in the storyboard order (Meter A runs first),
		   so on a ~360px phone the big number is never squeezed into a ~150px
		   half-column with a 3-line label (§2b, should-fix). */
		.meters {
			grid-template-columns: 1fr;
		}

		.m-label {
			min-height: 0;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		input[type='range'] {
			scroll-behavior: auto;
		}
	}
</style>
