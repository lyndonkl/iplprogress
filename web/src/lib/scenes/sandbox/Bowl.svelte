<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import type { FilterMode } from '$lib/field/types';
	import { pickedTeam } from '$lib/state';
	import {
		loadSandboxData,
		buildTooltip,
		buildGroupSeason,
		countVisible,
		teamIdFor,
		syncBowlHeld,
		buildFacetMask,
		facetsNeedMask,
		buildTourFlagMask,
		tourFlagToFacets,
		tourFlags,
		phaseToOverRange,
		overRangeToPhase,
		NO_FACETS,
		type Facets,
		type Phase,
		type BallTooltip,
		type SandboxData,
		type TourFlag
	} from './data';
	import { encodeFacets, decodeFacets, type DecodedView } from './url';
	import LinkedPanel from './panel/LinkedPanel.svelte';

	/**
	 * THE BOWL: "The Field Is Yours", the FULL R6b sandbox (r6b spec). The persistent
	 * 316,199-ball field becomes a filterable INSTRUMENT: the full facet grammar (league,
	 * team, season, phase / over-range, outcome, the separate wicket AND-toggle, batter,
	 * bowler, all combinable), a ten-flag guided-tour rail, a linked breakdown panel, and
	 * shareable URLs. It EXTENDS the R1b minimal sandbox (team + season + one preset + the
	 * tap-a-ball tooltip + the keyboard inspector), all of which carry forward.
	 *
	 * Hard invariants (spec §Hard-invariants): the field STAYS at 14 vertex attributes (the
	 * mask is a data texture, never an attribute); scalar-vs-mask routing is mutually
	 * exclusive per commit and the R1b scalar path renders byte-identically; ONE commit()
	 * write path; every on-screen number is data-bound; demand-mode (one render per change,
	 * the change cue is a single self-terminating one-shot, reduced-motion falls to a static
	 * swap); NEVER-BLANK (a zero-count combo dims the whole sky and shows a recovery card,
	 * never a void); mobile-first + keyboard-accessible; ZERO em dashes.
	 */
	let { progress, active, field, reduced }: SceneAnnotationProps = $props();

	/* ---- the ONE live facet state (the whole grammar) ------------------------ */
	let facets = $state<Facets>({ ...NO_FACETS });
	let activeFlagId = $state<string | null>(null);
	let liveCount = $state<number | null>(null);
	/** the true selection mask, handed to the panel so field + panel never drift */
	let currentMask = $state<Uint8Array | null>(null);

	/* ---- lazily-loaded sandbox dataset --------------------------------------- */
	let sandbox = $state<SandboxData | null>(null);
	let loadError = $state<string | null>(null);
	let loadStarted = false;

	const col = $derived(sandbox?.columnar ?? null);
	const matches = $derived(sandbox?.matches ?? []);
	const nameIndex = $derived(sandbox?.nameIndex ?? null);
	const flags = $derived<TourFlag[]>(sandbox ? tourFlags(sandbox) : []);
	const groupSeason = $derived(field ? buildGroupSeason(field.data) : null);

	/* ---- field-derived option lists (re-scoped by the league facet) ---------- */
	const teams = $derived(field?.data.teams ?? []);
	const iplTeams = $derived(teams.filter((t) => t.league === 'ipl'));
	const wplTeams = $derived(teams.filter((t) => t.league === 'wpl'));
	const seasons = $derived.by(() => {
		const lg = facets.league;
		const set = new Set<number>();
		for (const g of field?.data.groups ?? []) {
			if (lg && g.league !== lg) continue;
			set.add(g.season);
		}
		return [...set].sort((a, b) => a - b);
	});

	/* ---- outcome chip vocabulary (fan language; the six=4/four=3 trap lives in the codes) */
	const OUTCOME_CHIPS: { code: number; label: string; plural: string }[] = [
		{ code: 0, label: 'Dot', plural: 'dots' },
		{ code: 1, label: '1', plural: 'singles' },
		{ code: 2, label: '2 or 3', plural: 'twos and threes' },
		{ code: 3, label: 'Four', plural: 'fours' },
		{ code: 4, label: 'Six', plural: 'sixes' }
	];

	/* ---- the plain selection sentence (batting-side team; null facets omitted) */
	function phaseWord(p: Phase): string {
		return p === 'powerplay' ? 'the powerplay' : p === 'middle' ? 'the middle overs' : 'the death overs';
	}
	function joinOr(names: string[]): string {
		if (names.length <= 1) return names[0] ?? '';
		return names.slice(0, -1).join(', ') + ' or ' + names[names.length - 1];
	}
	function labelForOutcomes(bm: number): string {
		const names = OUTCOME_CHIPS.filter((o) => (bm >> o.code) & 1).map((o) => o.plural);
		if (names.length === 0) return 'that outcome';
		if (names.length === 1) return `${names[0]} only`;
		return joinOr(names);
	}
	function buildSelectionLabel(f: Facets): string {
		const parts: string[] = [];
		const t = f.team != null ? teams.find((tm) => tm.id === f.team) : null;
		if (t) parts.push(`${t.short} batting`);
		else if (f.league) parts.push(f.league === 'ipl' ? 'IPL' : 'WPL');
		if (f.season != null) parts.push(String(f.season));
		if (f.phase) parts.push(phaseWord(f.phase));
		else if (f.overLo != null || f.overHi != null)
			parts.push(`overs ${(f.overLo ?? 0) + 1} to ${(f.overHi ?? 19) + 1}`);
		if (f.outcomes) parts.push(labelForOutcomes(f.outcomes));
		if (f.wicket) parts.push('that took a wicket');
		const bName = f.batter != null ? col?.dicts.batter[f.batter] ?? null : null;
		const wName = f.bowler != null ? col?.dicts.bowler[f.bowler] ?? null : null;
		if (bName && wName) parts.push(`${wName} to ${bName}`);
		else if (bName) parts.push(`${bName} batting`);
		else if (wName) parts.push(`${wName} bowling`);
		return parts.length === 0 ? 'The whole field' : parts.join(' · ');
	}
	const selectionLabel = $derived.by(() => {
		const base = buildSelectionLabel(facets);
		if (base === 'The whole field' && activeFlagId) {
			const fl = flags.find((f) => f.id === activeFlagId);
			if (fl) return fl.label;
		}
		return base;
	});
	const activeFlag = $derived(activeFlagId ? flags.find((f) => f.id === activeFlagId) ?? null : null);

	/* the "More filters" disclosure badges an active over-range (hand-set or phase-mirrored) */
	const overActive = $derived(facets.overLo != null || facets.overHi != null);

	/* ---- the ONE commit write path ------------------------------------------- */
	interface ChangeMeta {
		label: string;
		undo: Partial<Facets>;
	}
	let emptyCard = $state<{ message: string; undoLabel: string; undo: Partial<Facets> | null } | null>(
		null
	);
	let cueTick = $state(0); // bumped per commit → the one-shot field-change cue remounts

	/** viewport width (the desktop coupling strip is always live and needs the mask) */
	let isWide = $state(false);
	let panelOpen = $state(false);
	const panelWatching = $derived(panelOpen || isWide);

	function buildEmptyCard(
		f: Facets,
		change: ChangeMeta | null
	): { message: string; undoLabel: string; undo: Partial<Facets> | null } {
		const bName = f.batter != null ? col?.dicts.batter[f.batter] ?? null : null;
		const wName = f.bowler != null ? col?.dicts.bowler[f.bowler] ?? null : null;
		const t = f.team != null ? teams.find((tm) => tm.id === f.team) ?? null : null;
		let message: string;
		if (bName && wName) message = `No balls here. ${bName} never faced ${wName} in this data.`;
		else if (t && f.season != null) message = `No balls here. ${t.name} didn't play in ${f.season}.`;
		else message = 'No balls match all of that. Try loosening one filter.';
		return {
			message,
			undoLabel: change ? `Undo: ${change.label}` : 'Back to the whole field',
			undo: change ? change.undo : null
		};
	}

	/** Apply a fully-formed Facets state to the field (routing + held-sync + URL + cue). */
	function applyFacets(
		f: Facets,
		opts: { flagId?: string | null; change?: ChangeMeta | null; flagMask?: Uint8Array | null }
	): void {
		const fld = field;
		if (!fld) return;
		const c = col;
		const watching = panelWatching;

		let mask: Uint8Array | null = null;
		let cnt: number;

		if (opts.flagMask) {
			// flag path: the prebuilt mask is authoritative (it can encode matchSet / innings
			// the live Facets cannot hold). Count the mask; keep DIM if somehow zero.
			mask = opts.flagMask;
			cnt = 0;
			for (let i = 0; i < mask.length; i++) if (mask[i]) cnt++;
			const renderMode: FilterMode = cnt === 0 ? 'dim' : f.mode;
			fld.setFilter({ team: null, season: null, matchRange: null, mode: renderMode });
			fld.setFilterMask(mask);
			syncBowlHeld({ ...f, mode: renderMode }, mask);
		} else if (facetsNeedMask(f) && c) {
			const r = buildFacetMask(c, fld.data.team, f);
			mask = r.mask;
			cnt = r.count;
			// never-blank: a 0-count mask stays DIM so the 316k haze survives (never hide → void)
			const renderMode: FilterMode = cnt === 0 ? 'dim' : f.mode;
			fld.setFilter({ team: null, season: null, matchRange: null, mode: renderMode });
			fld.setFilterMask(mask);
			syncBowlHeld({ ...f, mode: renderMode }, mask);
		} else {
			// R1b scalar fast path (byte-identical): team / season / matchRange on the scalars,
			// the mask cleared. The panel still needs a mask, so build one only while watching.
			cnt = groupSeason ? countVisible(fld.data, groupSeason, f) : fld.data.nPoints;
			const renderMode: FilterMode = cnt === 0 ? 'dim' : f.mode;
			fld.setFilterMask(null);
			fld.setFilter({ team: f.team, season: f.season, matchRange: f.matchRange, mode: renderMode });
			syncBowlHeld({ ...f, mode: renderMode }, null);
			if (watching && c) mask = buildFacetMask(c, fld.data.team, f).mask;
		}

		facets = f;
		activeFlagId = opts.flagId ?? null;
		liveCount = cnt;
		currentMask = mask;
		emptyCard = cnt === 0 ? buildEmptyCard(f, opts.change ?? null) : null;

		try {
			history.replaceState(null, '', encodeFacets(f, activeFlagId));
		} catch {
			/* replaceState can throw in a sandboxed frame; the view still stands */
		}

		// a facet change can hide the tapped ball → drop the tooltip + inspector
		tooltip = null;
		kbIndex = null;
		cueTick++; // fire the single self-terminating change cue
	}

	/** Fold a partial patch into the live facets and commit once. */
	function commit(
		patch: Partial<Facets>,
		opts: { flagId?: string | null; change?: ChangeMeta | null; markUser?: boolean } = {}
	): void {
		// Tweaking any facet leaves an active flag ("these filters made this view, change
		// any of them"). Drop the flag's NON-editable extras first: a match-preset's
		// matchRange and the hide mode are invisible in the tray, so keeping them would
		// silently scope the tweak to the flag's match while the label reads whole-field.
		const leavingFlag = activeFlagId != null && opts.flagId == null;
		const base: Facets = leavingFlag ? { ...facets, matchRange: null, mode: 'dim' } : facets;
		const f: Facets = { ...base, ...patch };
		applyFacets(f, { flagId: opts.flagId ?? null, change: opts.change ?? null });
		if (opts.markUser !== false) introDismissed = true; // the first real action fades the intro
	}

	/* ---- facet control handlers ---------------------------------------------- */
	function setLeague(lg: 'ipl' | 'wpl' | null): void {
		const patch: Partial<Facets> = { league: lg };
		if (lg && facets.team != null) {
			const t = teams.find((tm) => tm.id === facets.team);
			if (t && t.league !== lg) patch.team = null;
		}
		if (lg && facets.season != null) {
			const inLeague = (field?.data.groups ?? []).some((g) => g.league === lg && g.season === facets.season);
			if (!inLeague) patch.season = null;
		}
		commit(patch, {
			change: { label: lg ? (lg === 'ipl' ? 'IPL' : 'WPL') : 'both leagues', undo: { league: null } }
		});
	}
	function onTeamChange(e: Event): void {
		const v = (e.currentTarget as HTMLSelectElement).value;
		const id = v === '' ? null : Number(v);
		const t = id != null ? teams.find((tm) => tm.id === id) : null;
		commit(
			{ team: id, matchRange: null, mode: 'dim' },
			{ change: { label: t ? `${t.short} batting` : 'that team', undo: { team: null } } }
		);
	}
	function onSeasonChange(e: Event): void {
		const v = (e.currentTarget as HTMLSelectElement).value;
		const s = v === '' ? null : Number(v);
		commit(
			{ season: s, matchRange: null, mode: 'dim' },
			{ change: { label: s != null ? String(s) : 'that season', undo: { season: null } } }
		);
	}
	function setPhase(p: Phase | null): void {
		if (p) {
			const r = phaseToOverRange(p)!;
			commit(
				{ phase: p, overLo: r[0], overHi: r[1] },
				{ change: { label: phaseWord(p), undo: { phase: null, overLo: null, overHi: null } } }
			);
		} else {
			commit(
				{ phase: null, overLo: null, overHi: null },
				{ change: { label: 'the innings phase', undo: { phase: null, overLo: null, overHi: null } } }
			);
		}
	}
	function clampOver0(n: number): number {
		if (!Number.isFinite(n)) return 0;
		return n < 0 ? 0 : n > 19 ? 19 : Math.floor(n);
	}
	function onOverChange(which: 'lo' | 'hi', e: Event): void {
		const raw = Number((e.currentTarget as HTMLInputElement).value);
		let lo = which === 'lo' ? clampOver0(raw - 1) : facets.overLo ?? 0;
		let hi = which === 'hi' ? clampOver0(raw - 1) : facets.overHi ?? 19;
		if (lo > hi) [lo, hi] = [hi, lo];
		commit(
			{ overLo: lo, overHi: hi, phase: overRangeToPhase(lo, hi) },
			{ change: { label: `overs ${lo + 1} to ${hi + 1}`, undo: { overLo: null, overHi: null, phase: null } } }
		);
	}
	function toggleOutcome(code: number): void {
		const cur = facets.outcomes ?? 0;
		const next = cur ^ (1 << code);
		const undoOutcomes = cur === 0 ? null : cur;
		commit(
			{ outcomes: next === 0 ? null : next },
			{ change: { label: labelForOutcomes(next), undo: { outcomes: undoOutcomes } } }
		);
	}
	function isOutcomeOn(code: number): boolean {
		return ((facets.outcomes ?? 0) >> code) & 1 ? true : false;
	}
	function toggleWicket(): void {
		commit({ wicket: !facets.wicket }, { change: { label: 'that took a wicket', undo: { wicket: false } } });
	}

	/* batter / bowler typeaheads: commit only on a RESOLVED name (never per keystroke) */
	let batterText = $state('');
	let bowlerText = $state('');
	function onBatterInput(e: Event): void {
		const text = (e.currentTarget as HTMLInputElement).value;
		batterText = text;
		if (text.trim() === '') {
			if (facets.batter != null) commit({ batter: null }, { change: { label: 'that batter', undo: { batter: null } } });
			return;
		}
		const idx = nameIndex?.batter.get(text.trim());
		if (idx != null && idx !== facets.batter) {
			const name = col?.dicts.batter[idx] ?? text;
			commit({ batter: idx }, { change: { label: `${name} batting`, undo: { batter: null } } });
		}
	}
	function onBowlerInput(e: Event): void {
		const text = (e.currentTarget as HTMLInputElement).value;
		bowlerText = text;
		if (text.trim() === '') {
			if (facets.bowler != null) commit({ bowler: null }, { change: { label: 'that bowler', undo: { bowler: null } } });
			return;
		}
		const idx = nameIndex?.bowler.get(text.trim());
		if (idx != null && idx !== facets.bowler) {
			const name = col?.dicts.bowler[idx] ?? text;
			commit({ bowler: idx }, { change: { label: `${name} bowling`, undo: { bowler: null } } });
		}
	}
	function clearBatter(): void {
		batterText = '';
		commit({ batter: null }, { change: { label: 'that batter', undo: { batter: null } } });
	}
	function clearBowler(): void {
		bowlerText = '';
		commit({ bowler: null }, { change: { label: 'that bowler', undo: { bowler: null } } });
	}
	const duelName = $derived.by(() => {
		if (facets.batter == null || facets.bowler == null || !col) return null;
		return `${col.dicts.bowler[facets.bowler]} to ${col.dicts.batter[facets.batter]}`;
	});

	/* ---- the tour-flag rail -------------------------------------------------- */
	let coachLine = $state(false);
	let pulsedKeys = $state<Set<string>>(new Set());
	let pulseTimer: ReturnType<typeof setTimeout> | null = null;

	function coachSeen(): boolean {
		try {
			return localStorage.getItem('ebe.bowl.coach') === '1';
		} catch {
			return false;
		}
	}
	function markCoachSeen(): void {
		try {
			localStorage.setItem('ebe.bowl.coach', '1');
		} catch {
			/* private mode: the line still showed this session */
		}
	}
	function pulseControls(rf: Facets): void {
		if (reduced) return; // reduced-motion: the reflection is static, no pulse
		const keys = new Set<string>();
		if (rf.league) keys.add('league');
		if (rf.season != null) keys.add('season');
		if (rf.phase || rf.overLo != null || rf.overHi != null) keys.add('phase');
		if (rf.outcomes) keys.add('outcomes');
		if (rf.wicket) keys.add('wicket');
		if (rf.batter != null) keys.add('batter');
		if (rf.bowler != null) keys.add('bowler');
		pulsedKeys = keys;
		if (pulseTimer) clearTimeout(pulseTimer);
		pulseTimer = setTimeout(() => (pulsedKeys = new Set()), 1200); // one-shot, self-terminating
	}
	function openFlag(flag: TourFlag, opts: { markUser?: boolean } = {}): void {
		const c = col;
		const ni = nameIndex;
		if (!c || !ni || !field) return;
		const { mask } = buildTourFlagMask(c, flag, ni);
		const rf = tourFlagToFacets(flag, c, ni);
		applyFacets(rf, {
			flagId: flag.id,
			change: { label: flag.label, undo: {} },
			flagMask: mask
		});
		batterText = rf.batter != null ? c.dicts.batter[rf.batter] ?? '' : '';
		bowlerText = rf.bowler != null ? c.dicts.bowler[rf.bowler] ?? '' : '';
		if (rf.overLo != null || rf.overHi != null) moreOpen = true; // auto-expand for a stranded facet
		pulseControls(rf);
		if (!coachSeen()) {
			coachLine = true;
			markCoachSeen();
		}
		if (opts.markUser !== false) introDismissed = true;
	}

	/* flag-rail roving tabindex + focus-scroll coupling */
	let railFocus = $state(0);
	let cardEls: HTMLButtonElement[] = [];
	function onRailKeydown(e: KeyboardEvent, i: number): void {
		let next = i;
		if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = Math.min(flags.length - 1, i + 1);
		else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = Math.max(0, i - 1);
		else if (e.key === 'Home') next = 0;
		else if (e.key === 'End') next = flags.length - 1;
		else return;
		e.preventDefault();
		railFocus = next;
		const el = cardEls[next];
		if (el) {
			el.focus();
			el.scrollIntoView({ block: 'nearest', inline: 'nearest' });
		}
	}

	/* ---- explicit "show me everything" escape hatch -------------------------
	   The whole 316,199-ball field (every ball bright, nothing filtered) is the
	   hero view, not a blank one, so a control that says "the whole field" lands
	   there literally rather than re-curating a starting flag the way clearAll does. */
	function showWholeField(): void {
		batterText = '';
		bowlerText = '';
		moreOpen = false;
		emptyCard = null;
		commit({ ...NO_FACETS }, { flagId: null, change: null });
	}

	/* ---- clear-all + recovery (both re-land NON-EMPTY) ----------------------- */
	function clearAll(): void {
		batterText = '';
		bowlerText = '';
		moreOpen = false;
		emptyCard = null;
		const pick = $pickedTeam;
		if (pick && pick.league && pick.team !== 'neutral' && field) {
			const id = teamIdFor(field.data.teams, pick.league, pick.team);
			if (id != null) {
				commit({ ...NO_FACETS, team: id }, { flagId: null, change: null });
				return;
			}
		}
		const fl = flags.find((f) => f.id === 'final-2019');
		if (fl && col) {
			openFlag(fl);
			return;
		}
		commit({ ...NO_FACETS }, { flagId: null, change: null });
	}
	function recover(): void {
		const card = emptyCard;
		if (!card) return;
		if (card.undo && Object.keys(card.undo).length > 0) {
			if (card.undo.batter === null) batterText = '';
			if (card.undo.bowler === null) bowlerText = '';
			commit(card.undo, { change: null });
		} else {
			clearAll();
		}
	}

	/* ---- the breakdown panel ------------------------------------------------- */
	function ensureMask(): void {
		if (currentMask || !col || !field) return;
		if (activeFlagId && nameIndex) {
			const fl = flags.find((f) => f.id === activeFlagId);
			if (fl) {
				currentMask = buildTourFlagMask(col, fl, nameIndex).mask;
				return;
			}
		}
		currentMask = buildFacetMask(col, field.data.team, facets).mask;
	}
	function openPanel(): void {
		panelOpen = true;
		ensureMask();
	}
	function closePanel(): void {
		panelOpen = false;
	}

	/* ---- copy this view (the viral loop) ------------------------------------- */
	let copied = $state<'ok' | 'fail' | null>(null);
	let copyTimer: ReturnType<typeof setTimeout> | null = null;
	function copyView(): void {
		const url =
			typeof location !== 'undefined'
				? `${location.origin}${location.pathname}${location.search}${encodeFacets(facets, activeFlagId)}`
				: encodeFacets(facets, activeFlagId);
		const done = (state: 'ok' | 'fail'): void => {
			copied = state;
			if (copyTimer) clearTimeout(copyTimer);
			copyTimer = setTimeout(() => (copied = null), 2200);
		};
		try {
			navigator.clipboard.writeText(url).then(() => done('ok')).catch(() => done('fail'));
		} catch {
			done('fail');
		}
	}

	/* ---- intro handoff + "New here?" re-entry -------------------------------- */
	let introDismissed = $state(false);
	let railNudge = $state(false);
	function newHere(): void {
		introDismissed = false;
		if (reduced) return;
		railNudge = false; // restart the one-shot nudge that points at the tour rail
		requestAnimationFrame(() => {
			railNudge = true;
			setTimeout(() => (railNudge = false), 700);
		});
	}

	/* ---- "More filters" disclosure + mobile sheet ---------------------------- */
	let moreOpen = $state(false);
	let trayExpanded = $state(false);

	/* ---- lazy load on entering the Bowl -------------------------------------- */
	$effect(() => {
		if (!(active || progress > 0) || !field || loadStarted) return;
		loadStarted = true;
		loadSandboxData()
			.then((d) => (sandbox = d))
			.catch((e) => (loadError = e instanceof Error ? e.message : String(e)));
	});
	$effect(() => {
		if (sandbox) loadingPickHint = false;
	});

	/* ---- open: a shared URL SUPERSEDES the never-blank pre-filter ------------- */
	let opened = false;
	function restoreDecoded(v: DecodedView): void {
		if (v.flagId) {
			const fl = flags.find((f) => f.id === v.flagId);
			if (fl) {
				openFlag(fl, { markUser: false });
				return;
			}
		}
		if (v.facets) {
			const f = v.facets;
			batterText = f.batter != null ? col?.dicts.batter[f.batter] ?? '' : '';
			bowlerText = f.bowler != null ? col?.dicts.bowler[f.bowler] ?? '' : '';
			if (f.overLo != null || f.overHi != null) moreOpen = true;
			commit({ ...NO_FACETS, ...f }, { flagId: null, change: null, markUser: false });
			return;
		}
		neverBlankOpen();
	}
	function neverBlankOpen(): void {
		const pick = $pickedTeam;
		if (pick && pick.league && pick.team !== 'neutral' && field) {
			const id = teamIdFor(field.data.teams, pick.league, pick.team);
			if (id != null) {
				commit({ ...NO_FACETS, team: id }, { flagId: null, change: null, markUser: false });
				return;
			}
		}
		const fl = flags.find((f) => f.id === 'final-2019');
		if (fl && col) openFlag(fl, { markUser: false });
	}
	$effect(() => {
		if (!active || !field || opened) return;
		const hasHashIntent = typeof location !== 'undefined' && location.hash.includes('?');
		if (hasHashIntent) {
			if (!col) return; // wait for the columnar so a shared link decodes losslessly
			const decoded = decodeFacets(location.hash, col);
			if (decoded) {
				opened = true;
				restoreDecoded(decoded);
				return;
			}
			// stale / empty hash → fall through to never-blank
		}
		// picked team needs no columnar; the neutral 2019-final flag does
		const pick = $pickedTeam;
		if (pick && pick.league && pick.team !== 'neutral') {
			const id = teamIdFor(field.data.teams, pick.league, pick.team);
			if (id != null) {
				commit({ ...NO_FACETS, team: id }, { flagId: null, change: null, markUser: false });
				opened = true;
				return;
			}
		}
		if (col && sandbox) {
			neverBlankOpen();
			opened = true;
		}
	});

	/* ---- tap-a-ball tooltip + keyboard inspector (carried from R1b) ----------- */
	let tooltip = $state<{ t: BallTooltip; x: number; y: number; anchored: boolean } | null>(null);
	let kbIndex = $state<number | null>(null);
	let loadingPickHint = $state(false);
	let surfaceEl = $state<HTMLDivElement | null>(null);

	function tooltipFor(idx: number, x: number, y: number, anchored: boolean): void {
		if (!sandbox) {
			loadingPickHint = true;
			return;
		}
		kbIndex = idx;
		tooltip = { t: buildTooltip(sandbox.columnar, sandbox.matches, idx), x, y, anchored };
	}
	function onSurfaceClick(e: MouseEvent): void {
		const f = field;
		const el = surfaceEl;
		if (!f || !el) return;
		const r = el.getBoundingClientRect();
		const x = e.clientX - r.left;
		const y = e.clientY - r.top;
		const idx = f.pickAt(x, y, 24);
		if (idx == null) {
			tooltip = null;
			kbIndex = null;
			return;
		}
		tooltipFor(idx, x, y, true);
	}
	function inspectStep(dir: 0 | 1 | -1): void {
		const f = field;
		if (!f) return;
		if (!sandbox) {
			loadingPickHint = true;
			return;
		}
		const idx = dir === 0 || kbIndex == null ? f.firstVisiblePoint() : f.stepVisiblePoint(kbIndex, dir);
		if (idx == null) return;
		tooltipFor(idx, 0, 0, false);
	}
	function onInspectKeydown(e: KeyboardEvent): void {
		if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
			e.preventDefault();
			inspectStep(1);
		} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
			e.preventDefault();
			inspectStep(-1);
		} else if (e.key === 'Home') {
			e.preventDefault();
			inspectStep(0);
		}
	}
	function dismiss(): void {
		tooltip = null;
		kbIndex = null;
	}
	function tipStyle(t: { x: number; y: number; anchored: boolean }): string {
		if (!t.anchored || typeof window === 'undefined') return '';
		const vw = window.innerWidth;
		const vh = window.innerHeight;
		const w = Math.min(320, vw * 0.9);
		let left = t.x + 14;
		if (left + w > vw - 8) left = t.x - w - 14;
		if (left < 8) left = 8;
		let top = t.y + 14;
		const approxH = 230;
		if (top + approxH > vh - 8) top = Math.max(8, t.y - approxH - 14);
		return `left:${left}px; top:${top}px; width:${w}px;`;
	}

	onMount(() => {
		const mq = window.matchMedia('(min-width: 900px)');
		isWide = mq.matches;
		const onMq = (): void => {
			isWide = mq.matches;
		};
		mq.addEventListener('change', onMq);
		const onKey = (e: KeyboardEvent): void => {
			if (e.key === 'Escape') {
				if (tooltip) dismiss();
				else if (panelOpen) closePanel();
			}
		};
		window.addEventListener('keydown', onKey);
		return () => {
			mq.removeEventListener('change', onMq);
			window.removeEventListener('keydown', onKey);
			if (pulseTimer) clearTimeout(pulseTimer);
			if (copyTimer) clearTimeout(copyTimer);
		};
	});

	const teamSelValue = $derived(facets.team != null ? String(facets.team) : '');
	const seasonSelValue = $derived(facets.season != null ? String(facets.season) : '');
	const overLoDisplay = $derived(facets.overLo != null ? String(facets.overLo + 1) : '1');
	const overHiDisplay = $derived(facets.overHi != null ? String(facets.overHi + 1) : '20');
</script>

<div class="bowl" class:active>
	<!-- the field itself is the pick surface: touch-action pan-y keeps native scroll,
	     onclick (not pointerdown) means a scroll-drag never fires a pick. -->
	<div class="pick-surface" bind:this={surfaceEl} onclick={onSurfaceClick} role="presentation"></div>

	<!-- the single self-terminating field-change cue (a keyed one-shot; reduced-motion static) -->
	{#key cueTick}
		<div class="change-cue" class:reduced aria-hidden="true"></div>
	{/key}

	<!-- intro / handoff (fades once the reader acts; "New here?" recalls it) -->
	<div class="intro" class:dismissed={introDismissed}>
		<p class="overline">The Bowl · The field is yours</p>
		<p class="lede">Every dot is one ball, from every IPL and WPL match ever played. The story's done. The field is yours now.</p>
		<p class="hint">Filter it down below, tap any bright ball to see exactly what happened, or take a guided tour to get started.</p>
	</div>

	<!-- the tap-a-ball / keyboard tooltip -->
	{#if tooltip}
		{@const t = tooltip.t}
		<div class="tooltip" class:kb={!tooltip.anchored} style={tipStyle(tooltip)} role="dialog" aria-label="Ball detail">
			<button class="close" type="button" onclick={dismiss} aria-label="Dismiss">×</button>
			<p class="tt-headline"><strong>{t.batter}</strong> <span class="v">vs</span> {t.bowler}</p>
			<p class="tt-teams">{t.battingTeam} <span class="v">vs</span> {t.opponent}</p>
			<p class="tt-match">{t.matchLabel}{#if t.date} · {t.date}{/if}</p>
			{#if t.venue}<p class="tt-venue">{t.venue}</p>{/if}
			<p class="tt-line">
				<span class="over">Over {t.overBall}</span>
				<span class="sep">·</span>
				<span class="inn">{t.inningsLabel}</span>
			</p>
			<p class="tt-result">{t.result}</p>
			{#if t.resultText}<p class="tt-final">{t.resultText}</p>{/if}
		</div>
	{/if}

	<!-- the "0 balls" empty-state card: non-modal, does NOT occlude the tray, recovery names the facet -->
	{#if emptyCard}
		<div class="empty-card" role="status">
			<p class="ec-title">No balls here</p>
			<p class="ec-msg">{emptyCard.message}</p>
			<div class="ec-actions">
				<button class="ec-undo" type="button" onclick={recover}>{emptyCard.undoLabel}</button>
				<button class="ec-clear" type="button" onclick={clearAll}>Clear all</button>
			</div>
		</div>
	{/if}

	<!-- the linked breakdown panel + always-on desktop coupling strip -->
	<LinkedPanel
		{col}
		{matches}
		mask={currentMask}
		count={liveCount}
		{selectionLabel}
		open={panelOpen}
		{reduced}
		onClose={closePanel}
		onExpand={openPanel}
	/>

	<!-- the bottom dock: [coach line] → [tour rail] → [active flag] → [facet tray] -->
	<div class="dock">
		{#if coachLine}
			<div class="coach" role="status">
				<span>These filters made this view. Change any of them.</span>
				<button class="coach-x" type="button" onclick={() => (coachLine = false)} aria-label="Dismiss">×</button>
			</div>
		{/if}

		<!-- the tour-flag rail (the onboarding door; deep-link entries) -->
		{#if flags.length > 0}
			<div class="rail-wrap">
				<p class="rail-title">Take a tour</p>
				<div class="rail" class:nudge={railNudge} role="toolbar" aria-label="Guided tour of the field">
					{#each flags as flag, i (flag.id)}
						<button
							class="flag-card"
							class:on={activeFlagId === flag.id}
							type="button"
							tabindex={railFocus === i ? 0 : -1}
							bind:this={cardEls[i]}
							onclick={() => openFlag(flag)}
							onkeydown={(e) => onRailKeydown(e, i)}
							onfocus={() => (railFocus = i)}
						>
							<span class="fc-label">{flag.label}</span>
							<span class="fc-count">{flag.count.toLocaleString('en-US')} balls</span>
							<span class="fc-blurb">{flag.blurb}</span>
						</button>
					{/each}
				</div>
			</div>
		{/if}

		<!-- the active-flag banner (blurb + a way back) -->
		{#if activeFlag}
			<div class="flag-banner" role="region" aria-label="The tour view you're on">
				<p class="fb-label">{activeFlag.label}</p>
				<p class="fb-blurb">{activeFlag.blurb}</p>
				<button class="fb-back" type="button" onclick={showWholeField}>Back to the whole field</button>
			</div>
		{/if}

		<!-- the facet tray -->
		<div class="tray" class:expanded={trayExpanded} role="group" aria-label="Filter the field">
			<!-- mobile sheet handle -->
			<button
				class="handle"
				type="button"
				aria-expanded={trayExpanded}
				aria-label={trayExpanded ? 'Collapse the filters' : 'Expand the filters'}
				onclick={() => (trayExpanded = !trayExpanded)}
			>
				<span class="handle-bar"></span>
			</button>

			<!-- the pinned readout (peek): label + count + copy + clear + new here -->
			<div class="readout" aria-live="polite">
				<div class="rd-line">
					<span class="rd-sel">{selectionLabel}</span>
					<span class="rd-count"
						>{liveCount != null ? liveCount.toLocaleString('en-US') : '-'}<span class="rd-unit"> balls</span></span
					>
				</div>
				<div class="rd-actions">
					<button class="copy-btn" type="button" onclick={copyView}>
						<span aria-hidden="true">⧉</span> Copy this view
					</button>
					{#if copied}
						<span class="copied" role="status">{copied === 'ok' ? 'Copied' : 'Copy failed'}</span>
					{/if}
					<button class="clear-btn" type="button" onclick={clearAll}>Clear all</button>
					<button class="newhere-btn" type="button" onclick={newHere}>New here?</button>
				</div>
			</div>

			<!-- the three titled groups (revealed on expand on mobile; always shown on desktop) -->
			<div class="tray-body">
				<!-- GROUP A: Where & when -->
				<fieldset class="group">
					<legend>Where &amp; when</legend>

					<div class="facet" class:pulse={pulsedKeys.has('league')}>
						<span class="lbl" id="lbl-league">League</span>
						<div class="seg" role="group" aria-labelledby="lbl-league">
							<button class="seg-b" aria-pressed={facets.league == null} type="button" onclick={() => setLeague(null)}>All</button>
							<button class="seg-b" aria-pressed={facets.league === 'ipl'} type="button" onclick={() => setLeague('ipl')}>IPL</button>
							<button class="seg-b" aria-pressed={facets.league === 'wpl'} type="button" onclick={() => setLeague('wpl')}>WPL</button>
						</div>
					</div>

					<div class="facet two-up">
						<label class="facet-l">
							<span class="lbl">Team</span>
							<select value={teamSelValue} onchange={onTeamChange} aria-label="Filter by team, batting side">
								<option value="">All teams</option>
								<optgroup label="IPL" disabled={facets.league === 'wpl'}>
									{#each iplTeams as t (t.id)}
										<option value={String(t.id)}>{t.short} · {t.name}</option>
									{/each}
								</optgroup>
								<optgroup label="WPL" disabled={facets.league === 'ipl'}>
									{#each wplTeams as t (t.id)}
										<option value={String(t.id)}>{t.short} · {t.name}</option>
									{/each}
								</optgroup>
							</select>
						</label>

						<label class="facet-l">
							<span class="lbl">Season</span>
							<select value={seasonSelValue} onchange={onSeasonChange} aria-label="Filter by season">
								<option value="">All seasons</option>
								{#each seasons as y (y)}
									<option value={String(y)}>{y}</option>
								{/each}
							</select>
						</label>
					</div>

					<div class="facet" class:pulse={pulsedKeys.has('phase')}>
						<span class="lbl" id="lbl-phase">When in the innings</span>
						<div class="seg wrap" role="group" aria-labelledby="lbl-phase">
							<button class="seg-b" aria-pressed={facets.phase == null && !overActive} type="button" onclick={() => setPhase(null)}>All</button>
							<button class="seg-b" aria-pressed={facets.phase === 'powerplay'} type="button" onclick={() => setPhase('powerplay')}>The powerplay</button>
							<button class="seg-b" aria-pressed={facets.phase === 'middle'} type="button" onclick={() => setPhase('middle')}>The middle</button>
							<button class="seg-b" aria-pressed={facets.phase === 'death'} type="button" onclick={() => setPhase('death')}>The death</button>
						</div>
						{#if facets.phase === 'powerplay'}<span class="gloss">The first six overs.</span>
						{:else if facets.phase === 'middle'}<span class="gloss">Overs 7 to 15.</span>
						{:else if facets.phase === 'death'}<span class="gloss">The last five overs.</span>{/if}
					</div>

					<!-- More filters disclosure: badges an active over-range, auto-expands on restore -->
					<div class="more" class:pulse={pulsedKeys.has('phase')}>
						<button
							class="more-head"
							type="button"
							aria-expanded={moreOpen}
							onclick={() => (moreOpen = !moreOpen)}
						>
							<span class="more-caret" aria-hidden="true">{moreOpen ? '▾' : '▸'}</span>
							More filters{#if overActive}<span class="more-badge">1 active</span>{/if}
						</button>
						{#if moreOpen}
							<div class="more-body">
								<span class="lbl">Pick your overs</span>
								<div class="over-range">
									<label class="over-in">
										<span class="over-cap">From over</span>
										<input type="number" min="1" max="20" value={overLoDisplay} onchange={(e) => onOverChange('lo', e)} aria-label="From over" />
									</label>
									<span class="over-to">to</span>
									<label class="over-in">
										<span class="over-cap">to over</span>
										<input type="number" min="1" max="20" value={overHiDisplay} onchange={(e) => onOverChange('hi', e)} aria-label="To over" />
									</label>
								</div>
							</div>
						{/if}
					</div>
				</fieldset>

				<!-- GROUP B: What happened -->
				<fieldset class="group">
					<legend>What happened</legend>

					<div class="facet" class:pulse={pulsedKeys.has('outcomes')}>
						<span class="lbl" id="lbl-outcome">What came off the bat</span>
						<div class="chips" role="group" aria-labelledby="lbl-outcome">
							{#each OUTCOME_CHIPS as o (o.code)}
								<button class="chip" aria-pressed={isOutcomeOn(o.code)} type="button" onclick={() => toggleOutcome(o.code)}>{o.label}</button>
							{/each}
						</div>
					</div>

					<div class="facet wicket-facet" class:pulse={pulsedKeys.has('wicket')}>
						<button class="wicket-toggle" aria-pressed={facets.wicket === true} type="button" onclick={toggleWicket}>
							<span class="wt-box" aria-hidden="true">{facets.wicket ? '✓' : ''}</span>
							<span class="wt-text">...that took a wicket</span>
						</button>
					</div>
				</fieldset>

				<!-- GROUP C: Who -->
				<fieldset class="group">
					<legend>Who</legend>

					{#if duelName}
						<div class="duel-chip">
							<span class="dc-text">{duelName}</span>
							<button class="dc-x" type="button" onclick={() => { clearBatter(); clearBowler(); }} aria-label="Clear the duel">×</button>
						</div>
					{/if}

					<div class="facet" class:pulse={pulsedKeys.has('batter')}>
						<label class="facet-l">
							<span class="lbl">Batter</span>
							<div class="type-wrap">
								<input list="batter-list" placeholder="Start typing a batter" value={batterText} oninput={onBatterInput} aria-label="Filter by batter" />
								{#if facets.batter != null}<button class="type-x" type="button" onclick={clearBatter} aria-label="Clear batter">×</button>{/if}
							</div>
						</label>
						<datalist id="batter-list">
							{#each col?.dicts.batter ?? [] as name (name)}
								<option value={name}></option>
							{/each}
						</datalist>
					</div>

					<div class="facet" class:pulse={pulsedKeys.has('bowler')}>
						<label class="facet-l">
							<span class="lbl">Bowler</span>
							<div class="type-wrap">
								<input list="bowler-list" placeholder="Start typing a bowler" value={bowlerText} oninput={onBowlerInput} aria-label="Filter by bowler" />
								{#if facets.bowler != null}<button class="type-x" type="button" onclick={clearBowler} aria-label="Clear bowler">×</button>{/if}
							</div>
						</label>
						<datalist id="bowler-list">
							{#each col?.dicts.bowler ?? [] as name (name)}
								<option value={name}></option>
							{/each}
						</datalist>
					</div>
				</fieldset>

				<!-- secondary actions -->
				<div class="secondary">
					<button class="sec-btn" type="button" onclick={openPanel} aria-expanded={panelOpen}>Show the breakdown</button>
					<button
						class="sec-btn"
						type="button"
						onclick={() => inspectStep(0)}
						onkeydown={onInspectKeydown}
						aria-label="Inspect a ball with the keyboard; use arrow keys to step"
					>
						⌨ Inspect a ball
					</button>
				</div>

				{#if loadingPickHint}
					<p class="mini-note" role="status">Reading the ball data. Tap again in a moment.</p>
				{:else if loadError}
					<p class="mini-note err" role="status">Couldn't load the sandbox data ({loadError}).</p>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.bowl {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100dvh;
		pointer-events: none;
		visibility: hidden;
		z-index: 0;
	}
	.bowl.active {
		visibility: visible;
	}

	.pick-surface {
		position: absolute;
		inset: 0;
		z-index: 1;
		pointer-events: auto;
		touch-action: pan-y;
		cursor: crosshair;
	}

	/* ---- the one-shot change cue (perceptible re-mask on the hero surface) ---- */
	.change-cue {
		position: absolute;
		inset: 0;
		z-index: 2;
		pointer-events: none;
		box-shadow: inset 0 0 90px rgba(46, 196, 182, 0);
		animation: cue-flash 220ms ease-out;
	}
	@keyframes cue-flash {
		0% {
			box-shadow: inset 0 0 90px rgba(46, 196, 182, 0.28);
		}
		100% {
			box-shadow: inset 0 0 90px rgba(46, 196, 182, 0);
		}
	}
	.change-cue.reduced {
		animation: none;
	}
	@media (prefers-reduced-motion: reduce) {
		.change-cue {
			animation: none;
		}
	}

	/* ---- intro ---- */
	.intro {
		position: absolute;
		top: max(14px, env(safe-area-inset-top));
		left: 50%;
		transform: translateX(-50%);
		width: min(560px, 92vw);
		z-index: 2;
		pointer-events: none;
		text-align: center;
		transition: opacity 500ms ease;
	}
	.intro.dismissed {
		opacity: 0;
	}
	.overline {
		margin: 0;
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.26em;
		text-transform: uppercase;
		color: var(--gold);
	}
	.lede {
		margin: 0.35rem 0 0;
		font-size: clamp(1.05rem, 2.8vw, 1.35rem);
		line-height: 1.35;
		color: var(--ink);
		text-shadow: 0 1px 12px rgba(11, 14, 20, 0.8);
	}
	.hint {
		margin: 0.3rem 0 0;
		font-size: 0.8rem;
		color: var(--ink-dim);
		text-shadow: 0 1px 10px rgba(11, 14, 20, 0.9);
	}
	@media (prefers-reduced-motion: reduce) {
		.intro {
			transition: none;
		}
	}

	/* ---- empty-state card (non-modal, non-occluding the tray) ---- */
	.empty-card {
		position: absolute;
		top: max(90px, calc(env(safe-area-inset-top) + 78px));
		left: 50%;
		transform: translateX(-50%);
		width: min(420px, 92vw);
		z-index: 3;
		pointer-events: auto;
		padding: 0.85rem 1rem 0.95rem;
		border-radius: 14px;
		border: 1px solid rgba(255, 93, 58, 0.5);
		background: rgba(11, 14, 20, 0.92);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
	}
	.ec-title {
		margin: 0;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: var(--ember);
	}
	.ec-msg {
		margin: 0.35rem 0 0;
		font-size: 0.92rem;
		line-height: 1.4;
		color: var(--ink);
	}
	.ec-actions {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-top: 0.7rem;
	}
	.ec-undo,
	.ec-clear {
		min-height: 44px;
		padding: 0 0.9rem;
		border-radius: 10px;
		font: inherit;
		font-size: 0.84rem;
		cursor: pointer;
	}
	.ec-undo {
		border: 1px solid var(--teal);
		background: rgba(46, 196, 182, 0.16);
		color: var(--ink);
	}
	.ec-clear {
		border: 1px solid rgba(232, 236, 245, 0.2);
		background: rgba(232, 236, 245, 0.05);
		color: var(--ink-dim);
	}
	.ec-undo:focus-visible,
	.ec-clear:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* ---- tooltip (carried from R1b) ---- */
	.tooltip {
		position: absolute;
		z-index: 5;
		pointer-events: auto;
		max-width: 92vw;
		padding: 0.7rem 0.85rem 0.8rem;
		border-radius: 12px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		background: rgba(11, 14, 20, 0.95);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
		font-variant-numeric: tabular-nums;
	}
	.tooltip.kb {
		left: 50%;
		transform: translateX(-50%);
		bottom: calc(env(safe-area-inset-bottom) + 320px);
		width: min(320px, 92vw);
	}
	.close {
		position: absolute;
		top: 4px;
		right: 4px;
		width: 40px;
		height: 40px;
		border: none;
		border-radius: 10px;
		background: transparent;
		color: var(--ink-dim);
		font-size: 1.3rem;
		line-height: 1;
		cursor: pointer;
	}
	.close:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: -3px;
	}
	.tooltip p {
		margin: 0;
	}
	.tt-headline {
		font-size: 0.98rem;
		line-height: 1.3;
		color: var(--ink);
		padding-right: 26px;
	}
	.tt-teams {
		margin-top: 0.15rem !important;
		font-size: 0.86rem;
		color: var(--ink);
	}
	.v {
		color: var(--ink-dim);
		font-weight: 400;
	}
	.tt-match {
		margin-top: 0.4rem !important;
		font-size: 0.82rem;
		color: var(--gold);
	}
	.tt-venue {
		font-size: 0.78rem;
		color: var(--ink-dim);
	}
	.tt-line {
		margin-top: 0.4rem !important;
		font-size: 0.82rem;
		color: var(--ink-dim);
	}
	.tt-line .sep {
		margin: 0 0.35rem;
	}
	.tt-result {
		margin-top: 0.35rem !important;
		font-size: 0.95rem;
		font-weight: 700;
		color: var(--teal);
	}
	.tt-final {
		margin-top: 0.2rem !important;
		font-size: 0.78rem;
		color: var(--ink-dim);
	}

	/* ---- the bottom dock ---- */
	.dock {
		position: absolute;
		left: 50%;
		transform: translateX(-50%);
		bottom: max(10px, env(safe-area-inset-bottom));
		width: min(680px, 96vw);
		z-index: 4;
		pointer-events: auto;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	/* coach line */
	.coach {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 0.5rem 0.5rem 0.5rem 0.85rem;
		border-radius: 12px;
		border: 1px solid rgba(232, 168, 61, 0.5);
		background: rgba(11, 14, 20, 0.9);
		font-size: 0.82rem;
		color: var(--ink);
	}
	.coach-x {
		flex: none;
		width: 34px;
		height: 34px;
		border: none;
		border-radius: 8px;
		background: transparent;
		color: var(--ink-dim);
		font-size: 1.2rem;
		line-height: 1;
		cursor: pointer;
	}
	.coach-x:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: -2px;
	}

	/* the tour rail */
	.rail-wrap {
		position: relative;
	}
	.rail-title {
		margin: 0 0 4px 2px;
		font-size: 0.64rem;
		font-weight: 700;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}
	.rail {
		display: flex;
		gap: 8px;
		overflow-x: auto;
		scroll-snap-type: x mandatory;
		scroll-padding: 0 8px;
		-webkit-overflow-scrolling: touch;
		padding-bottom: 4px;
		/* the right-edge fade signals more cards off-screen */
		-webkit-mask-image: linear-gradient(90deg, #000 88%, transparent 100%);
		mask-image: linear-gradient(90deg, #000 88%, transparent 100%);
	}
	.rail.nudge {
		animation: rail-nudge 620ms ease;
	}
	@keyframes rail-nudge {
		0%,
		100% {
			transform: translateX(0);
		}
		40% {
			transform: translateX(14px);
		}
	}
	.flag-card {
		scroll-snap-align: start;
		flex: 0 0 auto;
		width: 200px;
		min-height: 44px;
		display: flex;
		flex-direction: column;
		gap: 2px;
		padding: 0.6rem 0.7rem;
		border-radius: 12px;
		border: 1px solid rgba(232, 236, 245, 0.14);
		background: rgba(11, 14, 20, 0.86);
		color: var(--ink);
		font: inherit;
		text-align: left;
		cursor: pointer;
	}
	.flag-card.on {
		border-color: var(--teal);
		background: rgba(46, 196, 182, 0.14);
	}
	.flag-card:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
	.fc-label {
		font-size: 0.86rem;
		font-weight: 700;
		line-height: 1.2;
	}
	.fc-count {
		font-size: 0.74rem;
		font-weight: 700;
		color: var(--teal);
		font-variant-numeric: tabular-nums;
	}
	.fc-blurb {
		font-size: 0.72rem;
		line-height: 1.3;
		color: var(--ink-dim);
	}

	/* active-flag banner */
	.flag-banner {
		padding: 0.6rem 0.85rem 0.7rem;
		border-radius: 12px;
		border: 1px solid rgba(46, 196, 182, 0.4);
		background: rgba(11, 14, 20, 0.9);
	}
	.fb-label {
		margin: 0;
		font-size: 0.92rem;
		font-weight: 700;
		color: var(--ink);
	}
	.fb-blurb {
		margin: 0.25rem 0 0;
		font-size: 0.8rem;
		line-height: 1.4;
		color: var(--ink-dim);
	}
	.fb-back {
		margin-top: 0.45rem;
		min-height: 40px;
		padding: 0.4rem 0;
		border: none;
		background: none;
		color: var(--teal);
		font: inherit;
		font-size: 0.82rem;
		cursor: pointer;
	}
	.fb-back:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* the facet tray */
	.tray {
		border-radius: 16px;
		border: 1px solid rgba(232, 236, 245, 0.12);
		background: rgba(11, 14, 20, 0.86);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		padding: 0.55rem 0.8rem 0.75rem;
	}

	.handle {
		display: none;
	}

	.readout {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.rd-line {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 10px;
	}
	.rd-sel {
		font-size: 0.84rem;
		color: var(--ink-dim);
		overflow: hidden;
		text-overflow: ellipsis;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		line-height: 1.3;
	}
	.rd-count {
		flex: none;
		font-size: 1.1rem;
		font-weight: 700;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	.rd-unit {
		font-size: 0.78rem;
		font-weight: 400;
		color: var(--ink-dim);
	}
	.rd-actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 6px;
	}
	.copy-btn {
		min-height: 40px;
		padding: 0 0.8rem;
		border-radius: 10px;
		border: 1px solid var(--teal);
		background: rgba(46, 196, 182, 0.16);
		color: var(--ink);
		font: inherit;
		font-size: 0.82rem;
		font-weight: 600;
		cursor: pointer;
	}
	.clear-btn,
	.newhere-btn {
		min-height: 40px;
		padding: 0 0.75rem;
		border-radius: 10px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		background: rgba(232, 236, 245, 0.05);
		color: var(--ink-dim);
		font: inherit;
		font-size: 0.8rem;
		cursor: pointer;
	}
	.copy-btn:focus-visible,
	.clear-btn:focus-visible,
	.newhere-btn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
	.copied {
		font-size: 0.78rem;
		color: var(--teal);
	}

	.tray-body {
		margin-top: 0.6rem;
		padding-top: 0.6rem;
		border-top: 1px solid rgba(232, 236, 245, 0.1);
		display: flex;
		flex-direction: column;
		gap: 0.7rem;
	}

	.group {
		margin: 0;
		padding: 0.55rem 0.6rem 0.65rem;
		border: 1px solid rgba(232, 236, 245, 0.1);
		border-radius: 12px;
	}
	.group legend {
		padding: 0 0.4rem;
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--gold);
	}

	.facet {
		margin-top: 0.5rem;
		border-radius: 10px;
	}
	.facet:first-of-type {
		margin-top: 0.2rem;
	}
	.facet.two-up {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
	}
	.facet-l {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.lbl {
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}
	.gloss {
		display: block;
		margin-top: 4px;
		font-size: 0.74rem;
		color: var(--ink-dim);
	}

	/* pulse when a flag reflects into a control */
	.facet.pulse,
	.more.pulse {
		animation: facet-pulse 1200ms ease;
	}
	@keyframes facet-pulse {
		0%,
		100% {
			box-shadow: 0 0 0 0 rgba(46, 196, 182, 0);
		}
		25% {
			box-shadow: 0 0 0 3px rgba(46, 196, 182, 0.5);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.facet.pulse,
		.more.pulse,
		.rail.nudge {
			animation: none;
		}
	}

	select,
	input[type='number'],
	.type-wrap input {
		width: 100%;
		min-height: 44px;
		padding: 0 0.6rem;
		border-radius: 10px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		background: rgba(232, 236, 245, 0.06);
		color: var(--ink);
		font: inherit;
		font-size: 0.9rem;
		cursor: pointer;
		-webkit-appearance: none;
		appearance: none;
	}
	select:focus-visible,
	input:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 1px;
	}

	/* segmented controls */
	.seg {
		display: flex;
		gap: 4px;
		margin-top: 4px;
	}
	.seg.wrap {
		flex-wrap: wrap;
	}
	.seg-b {
		flex: 1 1 auto;
		min-height: 44px;
		padding: 0 0.5rem;
		border-radius: 10px;
		border: 1px solid rgba(232, 236, 245, 0.16);
		background: rgba(232, 236, 245, 0.05);
		color: var(--ink-dim);
		font: inherit;
		font-size: 0.8rem;
		cursor: pointer;
		white-space: nowrap;
	}
	.seg-b[aria-pressed='true'] {
		border-color: var(--teal);
		background: rgba(46, 196, 182, 0.18);
		color: var(--ink);
		font-weight: 600;
	}
	.seg-b:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* More filters disclosure */
	.more {
		margin-top: 0.5rem;
	}
	.more-head {
		display: flex;
		align-items: center;
		gap: 6px;
		width: 100%;
		min-height: 44px;
		padding: 0 0.2rem;
		border: none;
		background: none;
		color: var(--ink-dim);
		font: inherit;
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		cursor: pointer;
	}
	.more-head:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
	.more-badge {
		margin-left: 6px;
		padding: 2px 7px;
		border-radius: 999px;
		background: rgba(46, 196, 182, 0.2);
		color: var(--teal);
		font-size: 0.68rem;
		letter-spacing: 0.02em;
		text-transform: none;
	}
	.more-body {
		margin-top: 0.35rem;
	}
	.over-range {
		display: flex;
		align-items: flex-end;
		gap: 8px;
		margin-top: 4px;
	}
	.over-in {
		flex: 1 1 auto;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.over-cap {
		font-size: 0.68rem;
		color: var(--ink-dim);
	}
	.over-to {
		padding-bottom: 12px;
		font-size: 0.8rem;
		color: var(--ink-dim);
	}

	/* outcome chips */
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 4px;
	}
	.chip {
		min-height: 44px;
		min-width: 44px;
		padding: 0 0.85rem;
		border-radius: 999px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		background: rgba(232, 236, 245, 0.05);
		color: var(--ink-dim);
		font: inherit;
		font-size: 0.84rem;
		cursor: pointer;
	}
	.chip[aria-pressed='true'] {
		border-color: var(--teal);
		background: rgba(46, 196, 182, 0.2);
		color: var(--ink);
		font-weight: 600;
	}
	.chip:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	/* the separate wicket AND-toggle (divided from the OR-chips) */
	.wicket-facet {
		padding-top: 0.5rem;
		border-top: 1px dashed rgba(232, 236, 245, 0.14);
	}
	.wicket-toggle {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		min-height: 44px;
		padding: 0 0.6rem;
		border-radius: 10px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		background: rgba(232, 236, 245, 0.05);
		color: var(--ink);
		font: inherit;
		font-size: 0.9rem;
		cursor: pointer;
		text-align: left;
	}
	.wicket-toggle[aria-pressed='true'] {
		border-color: var(--ember);
		background: rgba(255, 93, 58, 0.16);
	}
	.wicket-toggle:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}
	.wt-box {
		flex: none;
		width: 22px;
		height: 22px;
		border-radius: 6px;
		border: 1px solid rgba(232, 236, 245, 0.4);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.9rem;
		color: var(--ember);
	}
	.wicket-toggle[aria-pressed='true'] .wt-box {
		border-color: var(--ember);
	}

	/* typeaheads */
	.type-wrap {
		position: relative;
		display: flex;
	}
	.type-x {
		position: absolute;
		right: 4px;
		top: 50%;
		transform: translateY(-50%);
		width: 36px;
		height: 36px;
		border: none;
		border-radius: 8px;
		background: transparent;
		color: var(--ink-dim);
		font-size: 1.1rem;
		line-height: 1;
		cursor: pointer;
	}
	.type-x:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: -2px;
	}
	.duel-chip {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 0.5rem;
		padding: 0.25rem 0.35rem 0.25rem 0.7rem;
		border-radius: 999px;
		border: 1px solid var(--teal);
		background: rgba(46, 196, 182, 0.16);
	}
	.dc-text {
		font-size: 0.84rem;
		font-weight: 600;
		color: var(--ink);
	}
	.dc-x {
		width: 30px;
		height: 30px;
		border: none;
		border-radius: 999px;
		background: transparent;
		color: var(--ink-dim);
		font-size: 1.1rem;
		line-height: 1;
		cursor: pointer;
	}
	.dc-x:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: -2px;
	}

	/* secondary actions */
	.secondary {
		display: flex;
		gap: 8px;
	}
	.sec-btn {
		flex: 1 1 auto;
		min-height: 44px;
		padding: 0 0.7rem;
		border-radius: 10px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		background: rgba(232, 236, 245, 0.05);
		color: var(--ink);
		font: inherit;
		font-size: 0.82rem;
		cursor: pointer;
	}
	.sec-btn:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.mini-note {
		margin: 0;
		font-size: 0.76rem;
		color: var(--ink-dim);
	}
	.mini-note.err {
		color: var(--ember);
	}

	/* ---- mobile: the tray is a bottom sheet with a peek / expand hierarchy ---- */
	@media (max-width: 899px) {
		.handle {
			display: flex;
			align-items: center;
			justify-content: center;
			width: 100%;
			min-height: 28px;
			margin: -0.35rem 0 0.15rem;
			border: none;
			background: none;
			cursor: pointer;
		}
		.handle-bar {
			width: 40px;
			height: 4px;
			border-radius: 999px;
			background: rgba(232, 236, 245, 0.3);
		}
		.handle:focus-visible {
			outline: 2px solid var(--teal);
			outline-offset: 2px;
		}
		/* peek: readout only; expand reveals the groups */
		.tray-body {
			display: none;
		}
		.tray.expanded .tray-body {
			display: flex;
			max-height: 56dvh;
			overflow-y: auto;
			overscroll-behavior: contain;
		}
	}

	@media (min-width: 900px) {
		.rd-actions {
			justify-content: flex-start;
		}
	}
</style>
