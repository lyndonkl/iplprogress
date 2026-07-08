/**
 * The field data contract (R0, extended for R1a). Files live under
 * static/data/, emitted by the Python pipeline. The web app never writes there.
 */

export interface GroupMeta {
	/** group index — array position in groups.json */
	gi: number;
	league: 'ipl' | 'wpl';
	season: number;
	count: number;
}

export interface TeamMeta {
	/** team id — matches the per-point byte in team.u8 */
	id: number;
	league: 'ipl' | 'wpl';
	/** canonical current franchise name (pipeline canonicalization tables) */
	name: string;
	short: string;
	/** hex color, e.g. "#FDB913" */
	color: string;
	active: boolean;
}

export interface MetaJson {
	n_points: number;
	built_at: string;
	point_order: string;
	/** meta v2 (storyboard CO-3 traceability) — optional until the pipeline emits them */
	n_players?: number;
	n_matches?: Record<string, number>;
	files?: Record<string, { bytes_raw: number; bytes_gz: number }>;
}

export interface FieldData {
	nPoints: number;
	meta: MetaJson;
	groups: GroupMeta[];
	teams: TeamMeta[];
	/** per-delivery group index (gi), length nPoints */
	groupIds: Uint16Array;
	/**
	 * per-delivery packed byte, length nPoints:
	 * bits 0-2 outcome class (0 dot · 1 single · 2 two-or-three · 3 four · 4 six ·
	 * 5 other-extras-scoring-ball), bit 3 wicket fell, bit 4 WPL.
	 */
	attrs: Uint8Array;
	/** per-delivery batter balls-faced-so-far index, capped at 255 (wides excluded) */
	ballsFaced: Uint8Array;
	/** per-delivery batting-team id (matches teams.json ids) */
	team: Uint8Array;
	/**
	 * per-delivery era-relative intent byte (wallheat.u8): how hot this ball's
	 * (season × clamped balls-faced) cell strike rate runs versus the pooled IPL
	 * 2008-2010 batter at the SAME ball-index. Neutral byte 73 = the 2008-2010
	 * batter; below = cooler, above = hotter. Drives the C1-2 thesis-beat recolor
	 * (uploaded NORMALIZED to 0..1). Same point order as ballsFaced.
	 */
	wallHeat: Uint8Array;
	/**
	 * per-delivery match index (same point order), length nPoints — OPTIONAL:
	 * present only when the pipeline ships `match_index.u16` (see CONTRACT §12.4).
	 * Enables the `uFilterMatch` facet and the exact-match tooltip on any tap.
	 * When absent, match filtering falls back to a contiguous point-index RANGE
	 * (deliveries of a match ARE contiguous in point order), which needs no buffer.
	 */
	matchIndex?: Uint16Array;
	/**
	 * per-delivery batter cumulative-innings-runs byte (cap 255), same point
	 * order as ballsFaced — OPTIONAL, drives the Ch 2 `worms` layout's y axis
	 * (CONTRACT §13). Present only when the pipeline ships `cumruns.u8`; absent
	 * until then, so worm-space y collapses to the floor (graceful — R1 scenes
	 * never use `worms`). Uploaded NORMALIZED (u8 → 0..1) like wallHeat.
	 */
	cumRuns?: Uint8Array;
	/**
	 * per-delivery INTERLEAVED bowler-season plane coordinate (bowlerplane.u8),
	 * length 2×nPoints — OPTIONAL, drives the Ch 3 `frontier` layout (CONTRACT
	 * §15). Two bytes per point in field point order: byte 0 = bowler-season
	 * economy (linear over [4,16] RPO → 0..254), byte 1 = bowler-season bowling
	 * strike rate (linear over [8,60] balls/wicket → 0..254, with 255 = sentinel
	 * "no bowler-credited wicket" → clamps to the top 60+ bucket). Present only
	 * when the pipeline ships bowlerplane.u8; absent until then, so the frontier
	 * plane collapses to the bottom-left corner (graceful — R1/R2a never use it).
	 * Bound as two non-normalized attributes (aBowlEcon, aBowlSr) off one
	 * interleaved buffer — no copy, no positions on the wire.
	 */
	bowlerPlane?: Uint8Array;
	/**
	 * per-delivery full-innings-total byte (innings_total.u8), length nPoints —
	 * OPTIONAL, drives the Ch 4 `tide` layout's y axis (CONTRACT §18). One raw
	 * byte per point in field point order: decoded innings total (runs) = byte ×
	 * 2 (2-run resolution; every ball of an innings carries the same byte, so it
	 * gzips tiny). Present only when the pipeline ships innings_total.u8; absent
	 * until then, so the tide skyline collapses to the floor (graceful — R1/R2
	 * never use `tide`). Packed (with the within-season slot + first-innings flag)
	 * into the single `aTide` GL attribute on-device, to stay within the vertex-
	 * attribute budget (MAX_VERTEX_ATTRIBS).
	 */
	inningsTotal?: Uint8Array;
	/**
	 * per-delivery match-state cell byte (restate.u8), length nPoints — OPTIONAL,
	 * drives the Ch 5 `worth` layout (CONTRACT §19). One raw byte per point in
	 * field point order: byte = over × 10 + wicketsDown (0..199), where over is
	 * the delivery's over index 0..19 and wicketsDown counts dismissals before
	 * the delivery. Both innings are packed. Present only when the pipeline
	 * ships restate.u8; absent until then, so the worth grid collapses to the
	 * top-left cell (graceful — R1..R3b-1 never use `worth`). Packed with the
	 * WPA byte into the single `aPrice` GL attribute on-device (vertex-attribute
	 * budget).
	 */
	stateCell?: Uint8Array;
	/**
	 * per-delivery signed WPA byte (wpa.u8), length nPoints — OPTIONAL, drives
	 * the Ch 5 WPA subset-highlight (CONTRACT §21). Batting-team perspective:
	 * byte = 127 + round(wpa × 127) clamped 0..254 (127 = zero swing); byte 255
	 * = sentinel "no WPA for this ball" (D/L, undecided, or short-target
	 * matches — exactly what the win grids exclude). Sentinel balls never match
	 * the highlight. Packed with the state cell into `aPrice`.
	 */
	wpa?: Uint8Array;
	/** true when this is the dev-only synthetic fallback, not pipeline output */
	synthetic: boolean;
}

/** Outcome-class bit meanings, for readability at call sites. */
export const OUTCOME_DOT = 0;
export const OUTCOME_SINGLE = 1;
export const OUTCOME_TWO_THREE = 2;
export const OUTCOME_FOUR = 3;
export const OUTCOME_SIX = 4;
export const OUTCOME_OTHER = 5;

/* ---------------------------------------------------------------------------
 * Field layouts + render state — the uniform-level contract the story shell
 * drives. All layouts are computed IN-SHADER from per-point attributes; no
 * position buffers ever cross the wire (blueprint §2).
 * ------------------------------------------------------------------------- */

export type LayoutId =
	| 'free'
	| 'columns'
	| 'wall'
	| 'assembly'
	| 'worms'
	| 'frontier'
	| 'tide'
	| 'worth'
	| 'constellation'
	| 'flow'
	| 'matchdots';

/**
 * Which per-innings-phase star map is active in the Ch 6 constellation
 * (CONTRACT §22). The `phase` state selects one of the four precomputed,
 * Procrustes-aligned tables fed via `field.setStarTables`, and lerps the 23
 * star centres between two of them (the phase toggle — a coherent star-table
 * swap over the HELD constellation, not a re-sort and not a second morph).
 */
export type ConstellationPhase = 'all' | 'powerplay' | 'middle' | 'death';

/** Shader-side layout codes (uLayoutA / uLayoutB). */
export const LAYOUT_CODE: Record<LayoutId, number> = {
	free: 0,
	columns: 1,
	wall: 2,
	assembly: 3,
	// Ch 2 controlling morph (free→worms): x = balls-faced (aBallsFaced, display
	// extent 60+), y = cumulative innings runs (aCumRuns), settled as a low-alpha
	// density haze. In-shader from existing attributes + cumruns.u8 (CONTRACT §13).
	worms: 4,
	// Ch 3 controlling morph (free→frontier): x = bowler-season economy, y =
	// bowler-season bowling strike rate, settled as a low-alpha density haze of
	// dense bowler-season clouds. In-shader from the interleaved bowlerplane.u8
	// (byte 0 economy, byte 1 strike rate). Fixed data aspect, letterboxed
	// (never stretched), like `worms`. See CONTRACT §15.
	frontier: 5,
	// Ch 4 controlling morph (free→tide): x = season block + within-season packing
	// (innings ranked short→tall), y = a column filled to the innings TOTAL (from
	// innings_total.u8). A dense first-innings skyline; non-first-innings balls
	// settle into a low-alpha reservoir haze. The innings total, the packing slot
	// and the first-innings flag are packed into ONE attribute (aTide). Fixed data
	// aspect, letterboxed like `worms`/`frontier`. See CONTRACT §18.
	tide: 6,
	// Ch 5 controlling morph (free→worth): every ball condenses to the cell of
	// the match situation it was bowled in — x = over of the innings (1 left →
	// 20 right), y = wickets fallen when the ball was bowled (0 at the TOP → 9
	// at the bottom) — from restate.u8 (cell = over×10 + wicketsDown, packed
	// into the aPrice attribute with the WPA byte). Cell color = the pricelens
	// (a 200-entry table the scene feeds — CONTRACT §19), density-normalized so
	// integrated cell brightness tracks the price, never the crowd. Fixed data
	// aspect, letterboxed like `worms`/`frontier`/`tide`. See CONTRACT §19.
	worth: 7,
	// Ch 6 controlling morph (free→constellation): every ball condenses to its
	// SEASON-GROUP STAR centre — position = the per-phase star table (23 × (x,y),
	// fed via setStarTables) indexed in-shader by the ball's group id (position.y
	// = group_ids.u16) + a small radial jitter so a star reads as a glowing disc.
	// The phase toggle lerps the 23 star centres between two precomputed tables
	// (uStarMix), never a re-embed. Fixed data aspect (square), letterboxed like
	// `worms`/`frontier`/`tide`/`worth`. No new per-point buffer. See CONTRACT §22.
	constellation: 8,
	// Ch 7 controlling morph (free→flow): the twin rivers. Every ball condenses to
	// its LEAGUE-SEASON RIVER CELL — x = the ball's season along a shared time axis
	// (IPL 2008→2026 spans the width; WPL 2023→2026 shares the same season x's, a
	// short ribbon), y = that league-season's RUN RATE on a fixed "runs an over"
	// axis (a per-gi river table fed via setRiverTable, indexed in-shader by the
	// ball's group id — the league bit comes free with the season group). A fixed
	// DECORATIVE band thickness (a constant jitter, NOT a ball-count encoding) makes
	// the ribbon read as a flowing band of its own balls; the two rivers run
	// parallel then DIVERGE at 2023. `flowLift` reveals the post-fork climb (the
	// divergence emphasis). Fixed data aspect, letterboxed like the others. No new
	// per-point buffer (reuses group_ids.u16 + the attrs WPL bit). See CONTRACT §23.
	flow: 9,
	// Ch 8 controlling morph (free→matchdots): every ball condenses to the centroid
	// of the MATCH it belongs to + a small radial jitter disc, so one glowing dot =
	// one whole match (1,331 of them). x = season/time axis (2008 left → 2026 right),
	// y = the match centroid; the `matchSplit` scalar (the flowLift analog) lerps each
	// dot into its toss lane (winner batted first → upper lane, winner chose to field
	// → lower lane). NO new per-point buffer + NO new vertex attribute (the field
	// stays at 14): the ball's match id is recovered in-shader by a BINARY SEARCH of
	// position.x against a `match_bounds` DATA TEXTURE (1,331 monotone block-start
	// point indices), then its centroid + toss + density gain is texelFetched from a
	// second `uMatchTex` data texture — both fed once via field.setMatchTable (the
	// setRiverTable / setWorthTables / uWorthTex precedent). Dots render at a CONSTANT
	// radius and CONSTANT (density-normalized) brightness, so a run-heavy or longer
	// match is never bigger or brighter (design gate). Hue stays identity (the toss
	// rivers read POSITIONALLY by lane, never by hue). Fixed data aspect, letterboxed
	// like the others. See CONTRACT §24.
	matchdots: 10
};

/**
 * Subset-highlight class codes (uHlClass). 0-5 match the outcome classes in
 * attrs.u8; 6 selects the wicket bit; 7 selects by WPA swing size (|byte−127|
 * ≥ the threshold uniform, sentinel 255 never matches — CONTRACT §21); -1 = no
 * highlight active. The subset re-sort (uResortClass, §7 capability) reuses the
 * SAME class codes EXCEPT 'wpa' (highlight-only; the re-sort's CPU ordinal pass
 * decodes attrs.u8, which does not carry WPA).
 */
export const HL_CLASS = {
	none: -1,
	dot: OUTCOME_DOT,
	single: OUTCOME_SINGLE,
	twoThree: OUTCOME_TWO_THREE,
	four: OUTCOME_FOUR,
	six: OUTCOME_SIX,
	other: OUTCOME_OTHER,
	wicket: 6,
	wpa: 7
} as const;

export type HighlightClass = Exclude<keyof typeof HL_CLASS, 'none'>;

/** Classes the subset RE-SORT supports ('wpa' is highlight-only — §21). */
export type ResortableClass = Exclude<HighlightClass, 'wpa'>;

/** wpa.u8 encoding constants (mirror the pipeline's wpa_buffer decode spec). */
export const WPA_ZERO_BYTE = 127;
export const WPA_SENTINEL_BYTE = 255;

/**
 * attrs.u8 bit 5 — the "hit by that season's top-10 six-hitter" flag, packed by
 * the pipeline into the spare bit above outcome (0-2) / wicket (3) / WPL (4).
 * Drives the C1-5 two-tone re-sort recolor (top-10 specialists vs everyone
 * else) as a per-point LUMINANCE split within the six-ember hue — never a hue
 * change. Until the pipeline re-encodes the bit it reads 0 everywhere, so the
 * re-sort degrades to a single-tone column (graceful).
 */
export const ATTR_TOP10_BIT = 32;

/**
 * attrs.u8 bit 6 (mask 0x40) — the run-out dismissal flag, packed by the
 * pipeline into the spare bit above outcome (0-2) / wicket (3) / WPL (4) /
 * top-10 (5). Seeds the `aRunOut` GL membership flag for the C2-4 cascade
 * (CONTRACT §14). Until the pipeline re-encodes it the bit reads 0 everywhere,
 * so the field seeds an empty flag — the scene supplies membership at runtime
 * via `field.setRunouts(indices)` (a CPU index set derived from the columnar
 * `wicket_kind == 'run out'`), which works with zero pipeline dependency.
 */
export const ATTR_RUNOUT_BIT = 64;

/**
 * Run-out cascade subset class codes (uCascadeClass). Only 'runOut' today; the
 * shader tests the per-point `aRunOut` flag rather than decoding a class, so
 * the code just gates the capability on/off. -1 = no cascade active.
 */
export const CASCADE_CLASS = { none: -1, runOut: 0 } as const;

export type CascadeClass = Exclude<keyof typeof CASCADE_CLASS, 'none'>;

/**
 * Dismissal-kind codes for the Ch 3 rivers subset (CONTRACT §16), baked into the
 * per-point `aDismissal` GL flag via `field.setDismissals`. -1 = not a
 * bowler-credited wicket (run-outs / retired are excluded — a fielding event).
 * The codes are FIXED; the band STACK order (bottom→top) is chosen per-scene via
 * the rivers descriptor's `kinds` array, defaulting to bowled, lbw, stumped,
 * caught so the two woodwork dismissals (bowled + lbw) sit adjacent + baseline-
 * anchored as one "stumps" group.
 */
export const DISMISSAL_CODE = { bowled: 0, lbw: 1, caught: 2, stumped: 3 } as const;

export type DismissalKind = keyof typeof DISMISSAL_CODE;

/** Default band stack order, bottom→top (the "stumps" group anchored to baseline). */
export const DEFAULT_RIVERS_KINDS: readonly DismissalKind[] = ['bowled', 'lbw', 'stumped', 'caught'];

/**
 * Rivers subset class codes (uRiversClass). Only 'wicket' today; the shader
 * tests the per-point `aDismissal` flag (>= 0) for membership rather than
 * decoding a class, so the code just gates the capability on/off. -1 = inactive.
 */
export const RIVERS_CLASS = { none: -1, wicket: 0 } as const;

export type RiversClass = Exclude<keyof typeof RIVERS_CLASS, 'none'>;

/**
 * Which season groups form re-sort columns. 'ipl' = IPL seasons only (the C1-5
 * fireworks: 19 columns, WPL sixes stay on the shelf); 'all' = every group.
 */
export type ResortColumns = 'ipl' | 'all';

/* ---------------------------------------------------------------------------
 * Facet filter (R1b §12 — the Bowl instrument). A point is VISIBLE iff it
 * passes EVERY active facet (team AND season AND match); failing points are
 * hidden or ghosted per `mode`, and are removed from the GPU pick pass so
 * only visible balls are tappable. Every facet is independent — `null` means
 * that facet imposes no constraint.
 * ------------------------------------------------------------------------- */

/** How filtered-OUT points render: fully hidden (α→0) or ghosted (dim). */
export type FilterMode = 'hide' | 'dim';

/** The luminance×alpha multiplier applied to filtered-OUT points, per mode. */
export const FILTER_DIM: Record<FilterMode, number> = { hide: 0, dim: 0.09 };

/**
 * The imperative filter the sandbox scene drives (via `field.setFilter`). Maps
 * onto the `FieldRenderState.filter*` uniforms. R1b ships TEAM + SEASON only,
 * plus the ONE famous-match preset expressed as `matchRange` (or `matchIndex`
 * once the pipeline ships `match_index.u16`). Everything else is deferred (R6).
 */
export interface FieldFilter {
	/** teams.json id to keep, or null = all teams */
	team: number | null;
	/** season YEAR to keep (matches any league's group for that year), or null = all */
	season: number | null;
	/**
	 * match index to keep, or null = all. Requires the OPTIONAL `match_index.u16`
	 * buffer (FieldData.matchIndex); a no-op when that buffer isn't loaded — use
	 * `matchRange` instead for the R1b preset. See CONTRACT §12.4.
	 */
	matchIndex: number | null;
	/**
	 * contiguous point-index range [lo, hi) to keep, or null = no range. Matches
	 * a single game with zero new buffers because a match's deliveries ARE
	 * contiguous in point order — the working path for R1b's famous-match preset.
	 */
	matchRange: readonly [number, number] | null;
	/** how filtered-out points render (default 'dim') */
	mode: FilterMode;
}

/** The neutral filter — every facet inactive (the whole field visible). */
export const NO_FILTER: FieldFilter = {
	team: null,
	season: null,
	matchIndex: null,
	matchRange: null,
	mode: 'dim'
};

/**
 * One fully-resolved GPU state for the persistent field. The story
 * orchestrator interpolates between scene fieldStates and calls
 * FieldHandle.applyState() with one of these — exactly one render per change
 * (demand-mode rendering, blueprint §2).
 */
export interface FieldRenderState {
	/** morph source layout */
	layoutA: LayoutId;
	/** morph target layout */
	layoutB: LayoutId;
	/** 0 = pure layoutA · 1 = pure layoutB */
	morph: number;
	/**
	 * assembly stream-in 0..1 (chronological by point index). Only meaningful
	 * while layoutA or layoutB is 'assembly'; keep at 1 otherwise.
	 */
	reveal: number;
	/** global luminance multiplier — 1 = full brightness (dim = the loop stops, too) */
	dim: number;
	/** extra luminance multiplier on WPL points — 1 = full (C1-2 shelf staging) */
	wplDim: number;
	/** season-column DOM label plane opacity 0..1 */
	labels: number;
	/** subset-highlight class code (HL_CLASS values; -1 = none) */
	highlightClass: number;
	/** world-units vertical lift for highlighted points */
	highlightLift: number;
	/** brightness boost for highlighted points (0..1) */
	highlightBoost: number;
	/** luminance multiplier for non-matching points while a highlight is active */
	othersDim: number;
	/** WPL points never match the highlight (they take the others path — C1-5) */
	highlightSkipWpl: boolean;
	/** picked-team id (teams.json) whose balls ignite in team color; -1 = none */
	teamId: number;
	/**
	 * era-relative recolor blend for the C1-2 thesis beat: 0 = outcome colour
	 * (establishing shot / fireworks), 1 = every ball recoloured by its wallHeat
	 * cell (how far it beats the 2008-2010 batter at the same ball-index). The
	 * blend is a no-op at 0, so the establishing shot and the six two-tone are
	 * unchanged. Team-ignite still wins on top. Never > 0 while a re-sort is
	 * engaged (the beat is staged alone).
	 */
	wallHeatMix: number;

	/* ---- subset re-sort (§7 capability — the C1-5 fireworks) ----------------
	 * A cross-cutting modifier (composes with any base layout, like the
	 * highlight): points matching `resortClass` fly from their current layout
	 * position into per-season firework columns as `resortEngage` scrubs 0→1,
	 * arcing up out of the wall on the way (staggered per point → object
	 * constancy), and settle back as it scrubs 1→0. Everything else dims by
	 * `resortOthersDim`. A per-point two-tone recolor (attrs.u8 bit 5) fades in
	 * with `resortTint`. Fully reversible; no new position buffers cross the
	 * wire — the per-group stacking ordinal is derived on-device. */
	/** re-sort subset class code (HL_CLASS values; -1 = no re-sort active) */
	resortClass: number;
	/** WPL points never re-sort (they stay on the wall — C1-5 skipWpl) */
	resortSkipWpl: boolean;
	/** which season groups form columns (group selection + column count) */
	resortColumns: ResortColumns;
	/** 0 = points on their base layout · 1 = matching points fully in columns */
	resortEngage: number;
	/** world-units peak of the lift arc while flying to/from the columns */
	resortLift: number;
	/** two-tone recolor strength 0..1 (top-10 specialists vs everyone else) */
	resortTint: number;
	/** luminance × for non-matching points while the re-sort is engaged */
	resortOthersDim: number;

	/* ---- facet filter (§12 capability — the Bowl instrument) ----------------
	 * Resolved uniform values. A point passes iff it clears EVERY active facet;
	 * failing points are dimmed by `filterDim` and dropped from the pick pass.
	 * All facets default to inactive, so R1a scenes are unaffected. */
	/** team id to keep, or -1 = team facet inactive */
	filterTeam: number;
	/** season YEAR to keep, or -1 = season facet inactive */
	filterSeason: number;
	/** match index to keep, or -1 = inactive (needs the match_index buffer) */
	filterMatchIndex: number;
	/** point-index range lo (inclusive); the range facet is active iff hi > lo */
	filterRangeLo: number;
	/** point-index range hi (exclusive) */
	filterRangeHi: number;
	/** luminance×alpha for FILTERED-OUT points (0 hide … 1 no-op) */
	filterDim: number;

	/* ---- run-out cascade (§14 capability — the C2-4 hero subset) -------------
	 * A cross-cutting SEASON-SWEPT flash+fall of the run-out subset (per-point
	 * `aRunOut`, seeded from attrs.u8 bit 6 or a CPU index set). Composes with
	 * the `worms` layout; it does NOT spend a second controlling morph (like the
	 * highlight and the re-sort). As `cascadeSweep` advances 0→1 each season's
	 * run-out cohort flashes red and ejects downward TOGETHER (Gestalt common
	 * fate — one discrete pulse per season), then fades. Fully reversible: the
	 * next scene declaring no cascade lerps `cascadeSweep` back to 0. All fields
	 * default inactive (uCascadeClass -1), so R1a/R1b scenes render identically. */
	/** cascade subset class code (-1 = inactive, 0 = runOut) */
	cascadeClass: number;
	/** 0→1 season pointer — cohorts up to this season have flashed + fallen */
	cascadeSweep: number;
	/** red flash strength 0..1 as a season's wave crosses (beat-gated hue exception) */
	cascadeTint: number;
	/** world-units downward eject depth for a fully fallen point */
	cascadeFall: number;
	/** residual alpha × for a fully fallen point (0 = gone, 1 = stays lit) */
	cascadeFade: number;
	/** team-identity glow desaturation 0..1 through the cascade (red-team guard) */
	cascadeMute: number;

	/* ---- dismissal rivers (§16 capability — the Ch 3 hero subset) ------------
	 * A cross-cutting subset that streams the bowler-credited wicket points
	 * (per-point `aDismissal` >= 0, fed via field.setDismissals) OUT of the
	 * frontier clouds into a FLAT-BASELINE 100%-stacked band as `riversEngage`
	 * scrubs 0→1 (staggered per point → object constancy), and settles back as it
	 * scrubs 1→0. Composes with the `frontier` layout; it does NOT spend a second
	 * controlling morph (like the highlight / re-sort / cascade). Wicket points
	 * recolour categorically by dismissal kind (the gated hue exception, weighted
	 * by `riversTint`); everything else dims by `riversOthersDim`; the reader's
	 * team glow desaturates by `riversMute` through the beat (red-team guard). All
	 * fields default inactive (uRiversClass -1), so R1/R2a scenes are unaffected. */
	/** rivers subset class code (-1 = inactive, 0 = wicket) */
	riversClass: number;
	/** 0 = points in their clouds · 1 = fully stacked into the flat-baseline bands */
	riversEngage: number;
	/** categorical dismissal-kind recolor strength 0..1 (beat-gated hue exception) */
	riversTint: number;
	/** luminance × for non-wicket points while the rivers are engaged */
	riversOthersDim: number;
	/** team-identity glow desaturation 0..1 through the rivers beat (red-team guard) */
	riversMute: number;
	/** band stack order bottom→top (drives the per-point stacked y — discrete config) */
	riversKinds: readonly DismissalKind[];

	/* ---- waterline (§18 capability — the Ch 4 rising going rate) --------------
	 * A cross-cutting LEVEL over the held `tide` layout (like the highlight /
	 * re-sort / cascade / rivers, it spends NO second controlling morph): the
	 * going rate for the scrubbed season, a horizontal line the SCENE draws on the
	 * annotation plane. A first-innings column whose innings TOTAL sits below the
	 * level is DROWNED (dimmed toward the reservoir — LUMINANCE only, never a hue
	 * change, so hue stays identity). `waterLevel` lerps as the season pointer
	 * scrubs (the water rises); an inactive side contributes -1, so the drown is
	 * a shader no-op and R1/R2 render byte-identically. The waterline / 165 ghost
	 * / 200 / 230 lines are pure annotation-plane rules the scene anchors via
	 * `tidePoint` / `tideTotalToY` — this capability only drives the column dim. */
	/** going-rate level in RUNS; a first-innings column below it drowns. -1 = inactive */
	waterLevel: number;
	/** luminance × for a drowned column (default 1 = no dimming when inactive) */
	waterDrownDim: number;
	/** the picked team's columns keep their identity glow even when drowned */
	waterTeamKeep: boolean;

	/* ---- WPA subset-highlight threshold (§21 — Ch 5) --------------------------
	 * Only meaningful while highlightClass === HL_CLASS.wpa: a point matches iff
	 * |wpaByte − 127| ≥ this BYTE distance (and the byte isn't the 255 sentinel).
	 * Resolved from SubsetHighlight.wpaThreshold (absolute |ΔWP| 0..1 →
	 * round(t × 127), floored at 1 so threshold 0 never matches the whole field). */
	highlightWpaMin: number;

	/* ---- pricelens (§19 capability — the Ch 5 worth-grid color state) ---------
	 * A cross-cutting COLOR state over the held `worth` layout (like the
	 * waterline over `tide` — it composes with the layout and spends NO second
	 * controlling morph). Each table id names a 200-entry per-cell luminance
	 * table the scene fed via `field.setWorthTables()`; the shader mixes table A
	 * → table B by `worthMix` (the C5-6a era flip is exactly this lerp), then
	 * applies the §0.1 density-normalization gain so a cell's INTEGRATED
	 * brightness tracks its price, never its point count. Null table = the
	 * neutral ramp. Luminance only — hue stays identity. Inert for every prior
	 * layout (the shader branch is gated on the worth layout being in the mix). */
	/** pricelens table id A (null = neutral ramp) */
	worthTableA: string | null;
	/** pricelens table id B (null = neutral ramp) — the mix target */
	worthTableB: string | null;
	/** 0 = pure table A · 1 = pure table B */
	worthMix: number;

	/* ---- over rail (§20 capability — the Ch 5 set-piece six-ball lift) --------
	 * A cross-cutting subset modifier (like resort/cascade/rivers — it composes
	 * with any base layout and spends NO controlling morph): the named points
	 * (a tiny index set, ≤ RAIL_MAX_SLOTS) lift out of the field and fly to
	 * viewport-anchored rail slots as `railProgress` scrubs 0→1, enlarging to
	 * hero size; everything else dims by `railDim`. The flying balls render in a
	 * dedicated 8-point OVERLAY draw on top of the 316k field (so the heroes are
	 * never fogged by later-indexed points — see CONTRACT §20); the main field
	 * culls the members while the rail is active. Empty `railIndices` = inactive
	 * (byte-identical for every prior scene). */
	/** field point indices of the rail balls, bowling order (empty = inactive) */
	railIndices: readonly number[];
	/** viewport-fraction slot anchors, flat [x0,y0, x1,y1, …] (x 0 left→1 right, y 0 top→1 bottom) */
	railSlots: readonly number[];
	/** 0 = balls in the field · 1 = balls at their rail slots (lerps) */
	railProgress: number;
	/** luminance×alpha for the REST of the field at railProgress 1 (1 = no dimming) */
	railDim: number;
	/** hero point-size multiplier at the slots */
	railScale: number;
	/** world-units peak of the flight arc */
	railLift: number;

	/* ---- constellation phase (§22 capability — the Ch 6 phase toggle) ---------
	 * A cross-cutting POSITION state over the held `constellation` layout (the
	 * exact analog of the pricelens color state over `worth`, except the table is
	 * star POSITIONS, not colours): the 23 star centres lerp from phase table A
	 * (source/`from`) to phase table B (target/`table`) by `phaseMix`. The
	 * point-to-star assignment never changes — only the centres move, minimally
	 * and Procrustes-locked, so the WPL never crosses the men's worm. Tables are
	 * fed once via `field.setStarTables`; a null id resolves to 'all'. Read only
	 * while the `constellation` layout is in the mix, so every prior scene renders
	 * byte-identically regardless of these values. NEVER a live re-embed. */
	/** phase table A (the lerp SOURCE / `from`), or null → 'all' */
	phaseTableA: ConstellationPhase | null;
	/** phase table B (the lerp TARGET / `table`), or null → 'all' */
	phaseTableB: ConstellationPhase | null;
	/** 0 = pure table A · 1 = pure table B (the star-centre lerp) */
	phaseMix: number;

	/* ---- twin rivers (§23 capability — the Ch 7 flow layout) ------------------
	 * The `flow` layout places every ball at its league-season river cell from the
	 * per-gi river table fed via `field.setRiverTable`. `flowLift` is the ONE scalar
	 * a scene drives over the held rivers: it lerps each river's centreline from the
	 * table's flat BASELINE height (0) to its TRUE run-rate height (1) — the
	 * divergence reveal (C7-3's "flat, then the post-2023 stretch lifts"). Only the
	 * post-fork seasons move (the pipeline sets baseHeight == trueHeight for the
	 * pre-rule seasons, so they never lift); with no baseHeights fed the lift is a
	 * no-op (base == true). At flowLift 1 (the settled + reduced-motion end state)
	 * the rivers sit at their TRUE heights — the honest picture. Read only while the
	 * flow layout is in the A/B mix, so every prior scene renders byte-identically. */
	/** 0 = rivers at the flat baseline · 1 = rivers at true run-rate heights (default 1) */
	flowLift: number;

	/* ---- impact-sub sparks (§23 capability — the Ch 7 subset lift) ------------
	 * A cross-cutting LUMINANCE + small-lift glow over the per-point `aSpark` flag
	 * (baked once via `field.setSparks`, the setRunouts precedent — the 517 impact-
	 * sub deliveries). It composes with any layout (the sparks glow as they enter
	 * the IPL river) and spends NO controlling morph. LUMINANCE/position only — hue
	 * stays identity. Inactive at `sparkGlow` 0 (every prior scene byte-identical);
	 * reversible (glow lerps back to 0). Drive `sparkGlow` across the hold from a
	 * caption step via `SceneDef.dynamicState`, like the cascade sweep / rivers
	 * engage. `sparkOthersDim` optionally damps non-spark points so the sparks pop. */
	/** spark brightness/glow strength 0..1 (0 = inactive — no spark effect) */
	sparkGlow: number;
	/** world-units vertical lift for spark points while glowing */
	sparkLift: number;
	/** luminance × for non-spark points while sparks glow (1 = no dimming) */
	sparkOthersDim: number;

	/* ---- match-dots toss split (§24 capability — the Ch 8 controlling morph) ---
	 * `matchSplit` is the ONE held scalar a scene drives over the held match-dots
	 * (the flowLift analog): it lerps every dot from its neutral match centroid
	 * (0) into its toss lane (1) — winner batted first rises to the upper lane,
	 * winner chose to field falls to the lower lane, by the match table's toss
	 * class. Time still runs left→right inside each lane, so the field-first river
	 * SWELLS after 2016 straight from the data's own toss shift (no authored
	 * animation). Read in-shader only while the `matchdots` layout is in the A/B
	 * mix, so every prior scene renders byte-identically regardless of this value. */
	/** 0 = dots on their neutral match centroid · 1 = dots lifted into their toss lanes */
	matchSplit: number;

	/* ---- review chips (§25 capability — the Ch 8 subset) ----------------------
	 * A cross-cutting subset over the held match-dots (the setDismissals/setSparks
	 * precedent — it spends NO controlling morph): the 988 review deliveries fly OUT
	 * of the held dots into per-team green/red chip stacks as `reviewEngage` scrubs
	 * 0→1 (staggered per point → object constancy), and settle back as it scrubs 1→0.
	 * Membership + the per-(team×outcome) stack slot are baked once via
	 * field.setReviews (the review code into aDismissal, the packed lane+slot into
	 * aRiverPos — NO new attribute, and aTeam is left untouched so team-ignite stays
	 * correct everywhere). Review balls recolor by outcome — a LIGHTER green (the
	 * review paid off / upheld) vs a DARKER red (the call stood / struck down),
	 * separated by LUMINANCE not hue alone so "mostly dark = mostly the call stood"
	 * survives red-green colorblindness (CVD-safe gate); the review-red is held
	 * luminance-distinct from every team red, and while the chips are engaged the
	 * team-glow-mute guardrail extends so identity never bleeds into the chip read.
	 * All fields default inactive (reviewClass -1), so R0..R7 render byte-identically. */
	/** review subset class code (-1 = inactive, 0 = review chips engaged) */
	reviewClass: number;
	/** 0 = review balls on their match-dots · 1 = fully flown into the chip stacks */
	reviewEngage: number;
	/** green/red outcome recolor strength 0..1 (the luminance-separated CVD-safe recolor) */
	reviewTint: number;
	/** luminance × for non-review points while the chips are engaged (1 = no dimming) */
	reviewOthersDim: number;
}

export const DEFAULT_RENDER_STATE: FieldRenderState = {
	layoutA: 'free',
	layoutB: 'free',
	morph: 0,
	reveal: 1,
	dim: 1,
	wplDim: 1,
	labels: 0,
	highlightClass: HL_CLASS.none,
	highlightLift: 0,
	highlightBoost: 0,
	othersDim: 1,
	highlightSkipWpl: false,
	teamId: -1,
	wallHeatMix: 0,
	resortClass: HL_CLASS.none,
	resortSkipWpl: false,
	resortColumns: 'ipl',
	resortEngage: 0,
	resortLift: 0,
	resortTint: 0,
	resortOthersDim: 1,
	filterTeam: -1,
	filterSeason: -1,
	filterMatchIndex: -1,
	filterRangeLo: 0,
	filterRangeHi: 0,
	filterDim: 1,
	cascadeClass: CASCADE_CLASS.none,
	cascadeSweep: 0,
	cascadeTint: 0,
	cascadeFall: 0,
	cascadeFade: 1,
	cascadeMute: 0,
	riversClass: RIVERS_CLASS.none,
	riversEngage: 0,
	riversTint: 0,
	riversOthersDim: 1,
	riversMute: 0,
	riversKinds: DEFAULT_RIVERS_KINDS,
	waterLevel: -1,
	waterDrownDim: 1,
	waterTeamKeep: false,
	highlightWpaMin: 0,
	worthTableA: null,
	worthTableB: null,
	worthMix: 0,
	railIndices: [],
	railSlots: [],
	railProgress: 0,
	railDim: 1,
	railScale: 7,
	railLift: 0.35,
	phaseTableA: null,
	phaseTableB: null,
	phaseMix: 0,
	flowLift: 1,
	sparkGlow: 0,
	sparkLift: 0,
	sparkOthersDim: 1,
	matchSplit: 0,
	reviewClass: -1,
	reviewEngage: 0,
	reviewTint: 0,
	reviewOthersDim: 1
};
