import {
	CASCADE_CLASS,
	DEFAULT_RIVERS_KINDS,
	FILTER_DIM,
	HL_CLASS,
	RIVERS_CLASS,
	type FieldRenderState,
	type ResortColumns
} from '$lib/field/types';
import { ASSEMBLY_RAIN_WINDOW } from '$lib/field/shaders';
import type { FieldHandle } from '$lib/field/field';
import type {
	ConstellationPhaseState,
	OverRail,
	PriceLens,
	ReviewSubset,
	RunoutCascade,
	SceneDef,
	SceneFieldState,
	SparkSubset,
	SubsetHighlight,
	SubsetResort,
	SubsetRivers,
	Waterline
} from './types';

/** Default drowned-column luminance × (storyboard §6: dims one-plus stop). */
const WATERLINE_DEFAULT_DROWN = 0.18;

/** Over-rail defaults (§20): rest-of-field dim / hero scale / flight-arc peak.
 *  The dim default is LOW (0.06): alpha dims saturate on dense layouts (many
 *  overlapping points re-accumulate coverage), so a set-piece "dims hard" needs
 *  a near-floor multiplier — verified against the free field at 316k points. */
const RAIL_DEFAULT_DIM = 0.06;
const RAIL_DEFAULT_SCALE = 7;
const RAIL_DEFAULT_LIFT = 0.35;

/**
 * The WPA highlight threshold in wpa.u8 BYTE units (§21): |ΔWP| 0..1 →
 * round(t × 127), floored at 1 so a threshold of 0 never matches the whole
 * field (byte 127 = zero swing; sentinel 255 never matches in-shader).
 */
function wpaByteMin(hl: SubsetHighlight | null): number {
	if (!hl || hl.class !== 'wpa') return 0;
	return Math.max(1, Math.round((hl.wpaThreshold ?? 0) * 127));
}

/** Flatten per-ball [x,y] slot anchors to the uniform layout; missing slots
 *  default to an evenly-spaced row across the middle of the viewport. */
function railSlotArray(rail: OverRail): number[] {
	const m = rail.indices.length;
	const out: number[] = [];
	for (let i = 0; i < m; i++) {
		const s = rail.slots?.[i];
		out.push(s ? s[0] : (i + 0.5) / Math.max(1, m), s ? s[1] : 0.42);
	}
	return out;
}

/** The filter uniform fields resolved from a scene's declarative facets. */
interface ResolvedFilter {
	active: boolean;
	filterTeam: number;
	filterSeason: number;
	filterMatchIndex: number;
	filterRangeLo: number;
	filterRangeHi: number;
	filterDim: number;
	/**
	 * §28 arbitrary-facet mask (or null). Uploaded imperatively via
	 * `field.setFilterMask` — it does NOT ride the scalar FieldRenderState — but its
	 * PRESENCE makes the filter active so `filterDim` resolves to the mode's dim (below).
	 * That is what keeps a stray scroll re-applying the held state from un-dimming the
	 * mask: `filterDim` stays at the dim value even though no scalar facet is set.
	 */
	filterMask: Uint8Array | null;
}

function resolveSceneFilter(s: SceneFieldState): ResolvedFilter {
	const team = s.filterTeam ?? null;
	const season = s.filterSeason ?? null;
	const matchIndex = s.filterMatchIndex ?? null;
	const range = s.filterMatchRange ?? null;
	const mask = s.filterMask ?? null;
	// A mask makes the filter active too (§28): the mask decides membership, so the
	// mode's dim must apply even when no scalar facet is set. Without this, a scroll
	// re-applying bowlHeld would reset filterDim to 1 (no-op) and the mask would drop
	// points but leave them at full brightness.
	const active = team != null || season != null || matchIndex != null || range != null || mask != null;
	const mode = s.filterMode ?? 'dim';
	return {
		active,
		filterTeam: team ?? -1,
		filterSeason: season ?? -1,
		filterMatchIndex: matchIndex ?? -1,
		filterRangeLo: range ? range[0] : 0,
		filterRangeHi: range ? range[1] : 0,
		// filterDim is a no-op when no facet is active (nothing is filtered out)
		filterDim: active ? FILTER_DIM[mode] : 1,
		filterMask: mask
	};
}

/**
 * Imperative bridge for the §28 sandbox mask. The scalar facets (team / season /
 * match / range) and `filterDim` ride the FieldRenderState through
 * `resolveRenderState` → `field.applyState`, but the arbitrary-facet MASK is
 * imperative (`field.setFilterMask`, a persistent data texture — NOT in the render
 * state, exactly like `setDuelGraph` / `setMatchTable`). So whenever the sandbox
 * re-applies its held state (bowlHeld) — e.g. a stray scroll — call this to re-assert
 * the SAME mask (or clear it). Demand-mode: one render at most. The scalar side is
 * already handled by the render-state path, so this touches only the mask.
 */
export function applyFilterUniforms(
	field: Pick<FieldHandle, 'setFilterMask'>,
	s: SceneFieldState
): void {
	field.setFilterMask(s.filterMask ?? null);
}

/**
 * Pure scene-state math for the scroll orchestrator: resolves a (from, to, t)
 * triple into one FieldRenderState for FieldHandle.applyState(). Layouts ride
 * uLayoutA/uLayoutB + morph; every scalar lerps; highlight class is discrete
 * (whichever side declares one) while its lift/boost/othersDim lerp, so
 * subsets glide in and out.
 */

interface ResolvedSceneState {
	layout: SceneFieldState['layout'];
	reveal: number;
	dim: number;
	wplDim: number;
	labels: number;
	highlight: SubsetHighlight | null;
	resort: SubsetResort | null;
	cascade: RunoutCascade | null;
	rivers: SubsetRivers | null;
	waterline: Waterline | null;
	pricelens: PriceLens | null;
	overrail: OverRail | null;
	phase: ConstellationPhaseState | null;
	flowLift: number;
	sparks: SparkSubset | null;
	matchSplit: number;
	reviews: ReviewSubset | null;
	duelReveal: number;
	duelDominance: number;
	duelDustDim: number;
	strandRecede: number;
	ribbonReveal: number;
	teleportProgress: number;
	teleportLift: number;
	teleportOthersDim: number;
	teamIgnite: boolean;
	wallHeatMix: number;
}

export function withDefaults(s: SceneFieldState): ResolvedSceneState {
	return {
		layout: s.layout,
		reveal: s.reveal ?? 1,
		dim: s.dim ?? 1,
		wplDim: s.wplDim ?? 1,
		labels: s.labels ?? 0,
		highlight: s.highlight ?? null,
		resort: s.resort ?? null,
		cascade: s.cascade ?? null,
		rivers: s.rivers ?? null,
		waterline: s.waterline ?? null,
		pricelens: s.pricelens ?? null,
		overrail: s.overrail ?? null,
		phase: s.phase ?? null,
		flowLift: s.flowLift ?? 1,
		sparks: s.sparks ?? null,
		matchSplit: s.matchSplit ?? 0,
		reviews: s.reviews ?? null,
		duelReveal: s.duelReveal ?? 0,
		duelDominance: s.duelDominance ?? 0,
		duelDustDim: s.duelDustDim ?? 1,
		strandRecede: s.strandRecede ?? 0,
		ribbonReveal: s.ribbonReveal ?? 1,
		teleportProgress: s.teleportProgress ?? 0,
		teleportLift: s.teleportLift ?? 0,
		teleportOthersDim: s.teleportOthersDim ?? 1,
		teamIgnite: s.teamIgnite ?? true,
		wallHeatMix: s.wallHeatMix ?? 0
	};
}

/** Default column grouping for a re-sort: IPL-only when WPL is skipped. */
function resortColumns(r: SubsetResort): ResortColumns {
	return r.columns ?? (r.skipWpl ? 'ipl' : 'all');
}

const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

export function resolveRenderState(
	from: SceneFieldState,
	to: SceneFieldState,
	t: number,
	teamId: number
): FieldRenderState {
	const f = withDefaults(from);
	const g = withDefaults(to);
	const clampedT = Math.min(1, Math.max(0, t));

	const fromHl = f.highlight;
	const toHl = g.highlight;
	const hlClass = toHl
		? HL_CLASS[toHl.class]
		: fromHl
			? HL_CLASS[fromHl.class]
			: HL_CLASS.none;

	// Re-sort resolves like the highlight: whichever side declares it fixes the
	// discrete fields (class / skipWpl / column grouping) while engage / lift /
	// tint / othersDim lerp — so the subset glides into and out of its columns.
	const fromRs = f.resort;
	const toRs = g.resort;
	const rs = toRs ?? fromRs;
	const rsClass = rs ? HL_CLASS[rs.class] : HL_CLASS.none;

	// Run-out cascade resolves like the highlight/re-sort: the active descriptor
	// (preferring `to`) fixes the discrete class + the beat's config constants
	// (tint / fall / fade / mute), while only `sweep` LERPS — so the cascade
	// engages as the scene declaring it advances the sweep, and settles back
	// (sweep → 0) when the next scene declares none. An inactive side contributes
	// sweep 0, so the run-outs return cleanly on the reverse leg.
	const fromCas = f.cascade;
	const toCas = g.cascade;
	const cas = toCas ?? fromCas;
	const casClass = cas ? CASCADE_CLASS[cas.class] : CASCADE_CLASS.none;

	// Dismissal rivers resolve like the cascade: the active descriptor (preferring
	// `to`) fixes the discrete class + the beat's config (kinds / tint / othersDim
	// / mute), while only `engage` LERPS — so the rivers engage as the scene
	// declaring them advances engage, and settle back (engage → 0) when the next
	// scene declares none. An inactive side contributes engage 0, so the wickets
	// return cleanly to their clouds on the reverse leg.
	const fromRiv = f.rivers;
	const toRiv = g.rivers;
	const riv = toRiv ?? fromRiv;
	const rivClass = riv ? RIVERS_CLASS[riv.class] : RIVERS_CLASS.none;

	// Waterline resolves like the cascade/rivers: the active descriptor (preferring
	// `to`) fixes the discrete config (drownDim / teamKeepLit), while `level` LERPS
	// — so the water RISES as the scene scrubs, and DRAINS to the floor (an inactive
	// side contributes level 0) when the next scene declares none. With NO waterline
	// on either side `level` is -1, an inert sentinel, so the drown branch is a
	// shader no-op and R1/R2 render byte-identically.
	const fromWl = f.waterline;
	const toWl = g.waterline;
	const wl = toWl ?? fromWl;

	// Pricelens (§19) resolves like the cascade/waterline: the active descriptor
	// (preferring `to`) fixes the DISCRETE table pair (from / table), while `mix`
	// LERPS between the sides' declared mixes (a side with no lens contributes
	// the active lens's own mix, so a lens fades nothing when only one side
	// declares it — the recolor itself is already gated on the worth layout's
	// share of the morph, so it rides free→worth in and worth→free out for free).
	// Cross-TABLE transitions (e.g. the C5-6b lens release, rise → recent) are
	// the scene's job via dynamicState, exactly like the cascade sweep. With NO
	// lens on either side both rows resolve null → the neutral ramp (inert; every
	// prior scene byte-identical).
	const fromPl = f.pricelens;
	const toPl = g.pricelens;
	const pl = toPl ?? fromPl;
	const plMix = pl
		? lerp(fromPl?.mix ?? pl.mix ?? 1, toPl?.mix ?? pl.mix ?? 1, clampedT)
		: 0;

	// Over rail (§20) resolves like the cascade: the active descriptor
	// (preferring `to`) fixes the DISCRETE config (indices / slots / dimRest /
	// scale / lift), while only `progress` LERPS — so the balls fly out as the
	// scene declaring the rail advances progress, and settle back into their
	// exact field positions (progress → 0) when the next scene declares none.
	// With NO rail on either side the index set is empty → inert (uRailN 0),
	// every prior scene byte-identical.
	const fromRail = f.overrail;
	const toRail = g.overrail;
	const rail = toRail ?? fromRail;

	// Constellation phase (§22) resolves EXACTLY like the pricelens: the active
	// descriptor (preferring `to`) fixes the DISCRETE table pair (from / table),
	// while `mix` LERPS between the sides' declared mixes (a side with no phase
	// contributes the active phase's own mix, so nothing jumps when only one side
	// declares it — the star lerp is already gated on the constellation layout's
	// share of the morph in-shader, so it rides free→constellation for free). The
	// C6-5 phase glide (a cross-TABLE change, e.g. all → powerplay) is the scene's
	// job via dynamicState, exactly like the pricelens era flip. With NO phase on
	// either side both ids resolve null → the field defaults them to 'all' (inert;
	// every prior scene byte-identical since the shader only reads uStar on
	// the constellation layout). NEVER a live re-embed.
	const fromPh = f.phase;
	const toPh = g.phase;
	const ph = toPh ?? fromPh;
	const phMix = ph
		? lerp(fromPh?.mix ?? ph.mix ?? 1, toPh?.mix ?? ph.mix ?? 1, clampedT)
		: 0;

	// Impact-sub sparks (§23) resolve like the highlight: glow / lift / othersDim
	// all LERP from their inert defaults (glow 0, lift 0, othersDim 1), so the sparks
	// fade in when a scene declares them and fade back out (glow → 0) when the next
	// scene declares none. Membership is the baked aSpark flag; the effect is gated
	// on glow > 0, so a no-spark scene equals DEFAULT_RENDER_STATE.
	const fromSp = f.sparks;
	const toSp = g.sparks;

	// Review chips (§25) resolve like the rivers: the active descriptor (preferring
	// `to`) fixes the discrete class (0 active / -1 inert), while `engage` LERPS — so
	// the chips fly out as the scene declaring them advances engage, and settle back
	// (engage → 0) when the next scene declares none. When NO reviews are declared
	// (rev null) every review field takes its INERT default so a non-review scene is
	// byte-identical to DEFAULT_RENDER_STATE (reviewClass -1 → the shader branch is a
	// no-op, so the team-glow-mute guardrail keyed off it never fires).
	const fromRev = f.reviews;
	const toRev = g.reviews;
	const rev = toRev ?? fromRev;

	// Facet filter resolves like the highlight: the discrete facets come from
	// whichever side declares an active filter (preferring `to`), while filterDim
	// lerps — an inactive side contributes dim 1, so a filter fades in/out cleanly.
	const fFilter = resolveSceneFilter(from);
	const gFilter = resolveSceneFilter(to);
	const facets = gFilter.active ? gFilter : fFilter.active ? fFilter : gFilter;

	return {
		layoutA: f.layout,
		layoutB: g.layout,
		morph: clampedT,
		reveal: lerp(f.reveal, g.reveal, clampedT),
		dim: lerp(f.dim, g.dim, clampedT),
		wplDim: lerp(f.wplDim, g.wplDim, clampedT),
		labels: lerp(f.labels, g.labels, clampedT),
		highlightClass: hlClass,
		highlightLift: lerp(fromHl?.lift ?? 0, toHl?.lift ?? 0, clampedT),
		highlightBoost: lerp(fromHl?.boost ?? 0, toHl?.boost ?? 0, clampedT),
		othersDim: lerp(fromHl?.othersDim ?? 1, toHl?.othersDim ?? 1, clampedT),
		// discrete like the class: whichever side declares the highlight decides
		highlightSkipWpl: (toHl ?? fromHl)?.skipWpl ?? false,
		// the team stays lit through morphs; a scene may opt out explicitly
		teamId: (clampedT < 0.5 ? f.teamIgnite : g.teamIgnite) ? teamId : -1,
		// era-relative recolor blend lerps like any scalar (0 both sides = no-op),
		// so the C1-2 heat beat ramps in and settles back out with the scroll
		wallHeatMix: lerp(f.wallHeatMix, g.wallHeatMix, clampedT),
		resortClass: rsClass,
		resortSkipWpl: rs?.skipWpl ?? false,
		resortColumns: rs ? resortColumns(rs) : 'ipl',
		// engage/tint/othersDim/lift lerp — a side with no re-sort reads as
		// engage 0, tint 0, othersDim 1 (fully settled, no dimming)
		resortEngage: lerp(fromRs?.engage ?? 0, toRs?.engage ?? 0, clampedT),
		resortLift: lerp(fromRs?.lift ?? 0.5, toRs?.lift ?? 0.5, clampedT),
		resortTint: lerp(fromRs?.tint ?? 0, toRs?.tint ?? 0, clampedT),
		resortOthersDim: lerp(fromRs?.othersDim ?? 1, toRs?.othersDim ?? 1, clampedT),
		// facets discrete (from the active side); the dim fades so filters glide
		filterTeam: facets.filterTeam,
		filterSeason: facets.filterSeason,
		filterMatchIndex: facets.filterMatchIndex,
		filterRangeLo: facets.filterRangeLo,
		filterRangeHi: facets.filterRangeHi,
		filterDim: lerp(fFilter.active ? fFilter.filterDim : 1, gFilter.active ? gFilter.filterDim : 1, clampedT),
		// cascade: sweep lerps (engage/settle-back); the beat constants come from
		// the active descriptor (discrete, like the highlight class). When NO
		// cascade is declared (cas null) every field takes its INERT default so a
		// non-cascade scene is byte-identical to DEFAULT_RENDER_STATE — in
		// particular cascadeMute MUST be 0 or it would desaturate a picked team's
		// ignite glow in R1 (the team-ignite mute branch keys off uCascadeMute).
		cascadeClass: casClass,
		cascadeSweep: lerp(fromCas?.sweep ?? 0, toCas?.sweep ?? 0, clampedT),
		cascadeTint: cas ? cas.tint ?? 1 : 0,
		cascadeFall: cas ? cas.fall ?? 0.9 : 0,
		cascadeFade: cas ? cas.fade ?? 0 : 1,
		cascadeMute: cas ? cas.muteIdentity ?? 1 : 0,
		// rivers: engage lerps (engage/settle-back); the beat config comes from the
		// active descriptor (discrete, like the cascade). When NO rivers are
		// declared (riv null) every field takes its INERT default so a non-rivers
		// scene is byte-identical to DEFAULT_RENDER_STATE — in particular riversMute
		// MUST be 0 or it would desaturate a picked team's ignite glow (the
		// team-ignite mute branch keys off uRiversClass being active).
		riversClass: rivClass,
		riversEngage: lerp(fromRiv?.engage ?? 0, toRiv?.engage ?? 0, clampedT),
		riversTint: riv ? riv.tint ?? 1 : 0,
		riversOthersDim: riv ? riv.othersDim ?? 0.12 : 1,
		riversMute: riv ? riv.muteIdentity ?? 1 : 0,
		riversKinds: (toRiv ?? fromRiv)?.kinds ?? DEFAULT_RIVERS_KINDS,
		// waterline: level lerps (rises on the way in, drains to 0 on the reverse
		// leg); the drown config comes from the active descriptor. Inert at -1 when
		// no waterline is declared, so a non-tide scene equals DEFAULT_RENDER_STATE.
		waterLevel: wl ? lerp(fromWl?.level ?? 0, toWl?.level ?? 0, clampedT) : -1,
		waterDrownDim: wl ? wl.drownDim ?? WATERLINE_DEFAULT_DROWN : 1,
		waterTeamKeep: wl ? wl.teamKeepLit ?? true : false,
		// WPA highlight threshold (§21): discrete config from the active highlight
		// descriptor; 0 (inert) unless that descriptor's class is 'wpa'.
		highlightWpaMin: wpaByteMin(toHl ?? fromHl),
		// pricelens (§19): the table pair is discrete from the active descriptor;
		// mix lerps. No lens → both rows null (the neutral ramp — inert).
		worthTableA: pl ? (pl.from ?? pl.table) : null,
		worthTableB: pl ? pl.table : null,
		worthMix: plMix,
		// over rail (§20): indices/slots/config discrete from the active
		// descriptor; progress lerps (a side with no rail contributes 0, so the
		// balls return to the field on the reverse leg for free).
		railIndices: rail ? rail.indices : [],
		railSlots: rail ? railSlotArray(rail) : [],
		railProgress: rail
			? lerp(fromRail?.progress ?? 0, toRail?.progress ?? 0, clampedT)
			: 0,
		railDim: rail ? rail.dimRest ?? RAIL_DEFAULT_DIM : 1,
		railScale: rail ? rail.scale ?? RAIL_DEFAULT_SCALE : RAIL_DEFAULT_SCALE,
		railLift: rail ? rail.lift ?? RAIL_DEFAULT_LIFT : RAIL_DEFAULT_LIFT,
		// constellation phase (§22): the table pair is discrete from the active
		// descriptor (A = from ?? table, B = table); mix lerps. No phase → both null
		// (the field defaults them to 'all' — inert). Positions lerp, never re-fit.
		phaseTableA: ph ? (ph.from ?? ph.table) : null,
		phaseTableB: ph ? ph.table : null,
		phaseMix: phMix,
		// twin-rivers divergence reveal (§23): lerps like any scalar (default 1 both
		// sides = true heights, a no-op). Read in-shader only while the flow layout is
		// in the mix, so a non-flow scene equals DEFAULT_RENDER_STATE.
		flowLift: lerp(f.flowLift, g.flowLift, clampedT),
		// impact-sub sparks (§23): glow / lift / othersDim lerp from inert defaults so
		// the spark glow fades in and back out; inactive at glow 0 (byte-identical).
		sparkGlow: lerp(fromSp?.glow ?? 0, toSp?.glow ?? 0, clampedT),
		sparkLift: lerp(fromSp?.lift ?? 0, toSp?.lift ?? 0, clampedT),
		sparkOthersDim: lerp(fromSp?.othersDim ?? 1, toSp?.othersDim ?? 1, clampedT),
		// match-dots toss split (§24): the held lift lerps like any scalar (default 0 both
		// sides = neutral centroid, a no-op). Read in-shader only while the matchdots layout
		// is in the mix, so a non-matchdots scene equals DEFAULT_RENDER_STATE.
		matchSplit: lerp(f.matchSplit, g.matchSplit, clampedT),
		// review chips (§25): engage lerps (fly-out / settle-back); tint / othersDim come
		// from the active descriptor (discrete, like the rivers). Inert when NO reviews are
		// declared (reviewClass -1, engage 0, tint 0, othersDim 1) → byte-identical.
		reviewClass: rev ? 0 : -1,
		reviewEngage: lerp(fromRev?.engage ?? 0, toRev?.engage ?? 0, clampedT),
		reviewTint: rev ? rev.tint ?? 1 : 0,
		reviewOthersDim: rev ? rev.othersDim ?? 0.12 : 1,
		// duel web (§26): the four held scalars lerp like any scalar from their inert
		// defaults (reveal 0, dominance 0, dustDim 1, recede 0), so the web draws in and
		// settles back out; read in-shader only while the duelweb layout is in the mix, so
		// a non-duelweb scene equals DEFAULT_RENDER_STATE.
		duelReveal: lerp(f.duelReveal, g.duelReveal, clampedT),
		duelDominance: lerp(f.duelDominance, g.duelDominance, clampedT),
		duelDustDim: lerp(f.duelDustDim, g.duelDustDim, clampedT),
		strandRecede: lerp(f.strandRecede, g.strandRecede, clampedT),
		// ribbon + player teleporter (§27): the reveal + the three teleporter scalars lerp
		// like any scalar from their inert defaults (ribbonReveal 1, teleportProgress 0,
		// teleportLift 0, teleportOthersDim 1). Read in-shader only while the ribbon layout
		// is in the mix / the teleporter is engaged, so a non-ribbon scene equals
		// DEFAULT_RENDER_STATE (byte-identical).
		ribbonReveal: lerp(f.ribbonReveal, g.ribbonReveal, clampedT),
		teleportProgress: lerp(f.teleportProgress, g.teleportProgress, clampedT),
		teleportLift: lerp(f.teleportLift, g.teleportLift, clampedT),
		teleportOthersDim: lerp(f.teleportOthersDim, g.teleportOthersDim, clampedT)
	};
}

/**
 * A scene's fully-settled HELD state (post-morph): its fieldState resolved
 * through dynamicState at progress 1. This is the correct morph SOURCE for the
 * NEXT scene — a re-sort that engaged and tinted to completion must settle back
 * FROM that completed state, not from the un-modulated fieldState (no pop). The
 * orchestrator uses it for the `from` side; reduced motion ignores it (t = 1).
 */
export function heldState(scene: SceneDef): SceneFieldState {
	return scene.dynamicState ? scene.dynamicState(1, scene.fieldState) : scene.fieldState;
}

/**
 * A scene's live TARGET state at a given progress: its fieldState resolved
 * through dynamicState (so a caption step can drive a one-change field update
 * during the hold). The morph interpolates toward this on every tick.
 */
export function dynamicTarget(scene: SceneDef, progress: number): SceneFieldState {
	return scene.dynamicState ? scene.dynamicState(progress, scene.fieldState) : scene.fieldState;
}

/** The scene's end state for prefers-reduced-motion jump-cuts. */
export function sceneEndState(scene: SceneDef): SceneFieldState {
	return scene.reducedMotionEndState ?? scene.fieldState;
}

/** Fraction of the scene's scroll that drives the morph (rest holds). */
export function morphFraction(scene: SceneDef): number {
	const m = scene.morphLength ?? Math.min(140, scene.scrollLength);
	return Math.min(1, Math.max(0.0001, m / scene.scrollLength));
}

/**
 * How many points have appeared at a given assembly reveal value — the DOM
 * counter's source of truth. Mirrors the shader's frontier math exactly:
 * a point is visible once `chronoIndex/n < reveal * (1 + RAIN_W)`, so the
 * count is monotonic, 0 at reveal 0, and exactly n at reveal 1 — the counter
 * can only ever end at the number the pixels show.
 */
export function assemblyVisibleCount(reveal: number, nPoints: number): number {
	const r = Math.min(1, Math.max(0, reveal));
	return Math.min(nPoints, Math.floor(r * (1 + ASSEMBLY_RAIN_WINDOW) * nPoints));
}
