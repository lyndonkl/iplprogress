/**
 * The story-shell morph shader (GLSL ES 3.0 — three r163+ is WebGL2-only).
 * ALL layouts are computed IN-SHADER from per-point attributes — no position
 * buffers ever cross the wire (blueprint §2).
 *
 * Layouts (uLayoutA → uLayoutB, mixed by uProgress with per-point stagger):
 *   0 free      — procedural scatter from the index hash (the resting field).
 *                 WPL points scatter into their own constellation, upper-right
 *                 sky, deliberately apart from the IPL cloud (storyboard CO-3
 *                 / blueprint §3: "a second league assembles — its own body of
 *                 light"; the constellation→shelf continuity in C1-2 depends
 *                 on this staying upper).
 *   1 columns   — season columns (centroid table + within-group ordinal)
 *   2 wall      — ignition wall: x = balls-faced 1..30+ (aBallsFaced clamped),
 *                 y = season row centre (uCols[gi].y), storyboard C1-2
 *   3 assembly  — the free-field scatter, revealed chronologically by point
 *                 index as uReveal scrubs 0→1 (cold-open counter set piece)
 *   4 worms     — Ch 2 worm-space (CONTRACT §13): x = balls-faced (aBallsFaced,
 *                 clamped 1..60+), y = cumulative innings runs (aCumRuns),
 *                 settled as a low-alpha density haze (WORM_HAZE_ALPHA); fixed
 *                 data aspect ratio, letterboxed (never stretched).
 *
 * Cross-cutting uniform-driven states (compose with any layout):
 *   subset highlight — points matching uHlClass lift (uHlLift) and brighten
 *                      (uHlBoost); everything else dims (uOthersDim).
 *   subset re-sort   — points matching uResortClass fly into per-season columns
 *                      as uResortEngage scrubs 0→1 (§9); reversible.
 *   run-out cascade  — points with aRunOut flash red + fall as uCascadeSweep
 *                      sweeps seasons 0→1 (§14, Ch 2 C2-4); reversible.
 *   team ignite      — points whose aTeam == uPickedTeam render in uTeamColor
 *                      and resist the global dim (personalization survives)
 *   facet filter     — points that FAIL the active team/season/match facets are
 *                      hidden (uFilterDim 0) or ghosted (uFilterDim > 0); they
 *                      are ALSO removed from the GPU pick pass (R1b §11/§12).
 *   dims             — uDim (whole field) and uWplDim (WPL points only) are
 *                      luminance multipliers: hue never encodes quantity
 *
 * The vertex logic that decides WHERE a point sits and WHETHER it is visible
 * (`computeCore()` below) is SHARED verbatim by the visual vertex shader and
 * the GPU-picking vertex shader (`makePickVertexShader`), so the pick pass is
 * pixel-registered to the field the reader sees and honours the same filter —
 * filtered-out points are never pickable. Only the colour/encoding differs.
 *
 * Attribute packing (ShaderMaterial's built-in `position` vec3 is reused as
 * the per-point record — three floats, all exact integers < 2^24):
 *   position.x = point index (chronological)
 *   position.y = group index gi
 *   position.z = ordinal within group (client-computed in one pass)
 *   aAttrs      = packed outcome byte (bits 0-2 class, bit 3 wicket, bit 4 WPL,
 *                 bit 5 = hit by that season's top-10 six-hitter — C1-5 two-tone)
 *   aBallsFaced = batter balls-faced index (u8, capped 255)
 *   aTeam       = batting-team id (u8, matches teams.json)
 *   aSubOrd     = point's ordinal among its group's re-sort subset (client-
 *                 computed on demand; 0 for non-subset points — no wire cost)
 *   aWallHeat   = era-relative "intent" byte, NORMALIZED to 0..1 (drives the
 *                 C1-2 thesis-beat recolor, gated by uWallHeatMix)
 *   aCumRuns    = batter cumulative innings runs, NORMALIZED to 0..1 (worm-space
 *                 y, §13; binds zeros until the pipeline ships cumruns.u8)
 *   aRunOut     = run-out membership flag 0/1 (worm-space cascade, §14; seeded
 *                 from attrs bit 6, overridable via field.setRunouts — no wire cost)
 *   aPrice      = packed Ch 5 record (CONTRACT §19/§21): restate.u8 state-cell
 *                 byte (bits 0-7 — the worth-grid position) + wpa.u8 byte × 256
 *                 (bits 8-15 — the WPA subset-highlight; 255 = sentinel). Baked
 *                 on-device from the two optional buffers (attribute budget).
 *   aMatchIndex = per-delivery match index (u16, OPTIONAL — only present when
 *                 the pipeline ships match_index.u16; gates the uFilterMatch
 *                 facet + the exact-match tooltip. See CONTRACT §12.4.)
 */

import { FLOW_RIBBON_ALPHA, RAIL_MAX_SLOTS, WORTH_CELL_FILL } from './layout';

/** Fraction of the reveal range a point spends "raining in" (assembly layout). */
export const ASSEMBLY_RAIN_WINDOW = 0.045;

/**
 * Base alpha multiplier the field settles to in worm-space (Ch 2 `worms`, §13):
 * every ball on screen exactly once, at low alpha, so coincident balls stack
 * into a density HAZE (dense wedge bottom-left) rather than a solid fill. The
 * par / anchor exemplar worms live on the annotation plane, so the GL field is
 * pure ground. Team-ignited points resist this (personalization survives, C2-8).
 */
export const WORM_HAZE_ALPHA = 0.3;

/**
 * Base alpha multiplier for the Ch 4 tide reservoir (§18): non-first-innings
 * balls (second innings, super-over, rain-hit) that settle into the low haze
 * behind and below the skyline, so "every ball ever is here" stays literally
 * true while the lit first-innings columns carry the argument. First-innings
 * columns keep full alpha; only the reservoir is damped. Baked as TIDE_RESERVOIR_A.
 */
export const TIDE_RESERVOIR_ALPHA = 0.16;

/**
 * Sweep-distance (in `cascadeSweep` units) a single season's run-out cohort
 * spends flashing + falling — sized near the season pitch (~1/18 over 2008-26)
 * so each season reads as ONE discrete synchronized pulse (Gestalt common fate,
 * C2-4), never asynchronous rain. Baked into the shader as CASCADE_FLASH_W.
 */
export const CASCADE_FLASH_WINDOW = 0.05;

/**
 * The wallheat encoding's neutral byte (ch1.json `ignition.wallheat.neutral_byte`
 * = 73): the byte at which a cell equals the pooled IPL 2008-2010 batter at its
 * ball-index and sits at the diverging scale's neutral pivot. Baked into the
 * shader as `WALLHEAT_NEUTRAL` (73/255) so 2008-era rows read neutral. Mirror of
 * the pipeline constant — if the pipeline re-encodes with a different pivot,
 * this must move with it.
 */
export const WALLHEAT_NEUTRAL_BYTE = 73;

/**
 * Per-ball flight stagger (in `railProgress` units) between adjacent rail slots
 * (Ch 5 §20): ball 1 leads, ball 6 trails, so the over lifts out as a readable
 * left-to-right wave rather than a teleport. The progress ramp is over-driven
 * (×1.25) so the LAST ball still completes at progress 1.
 */
export const RAIL_STAGGER = 0.05;

/**
 * Base alpha multiplier the field settles to in the Ch 8 match-dots (§24): the 316k
 * balls collapse into 1,331 discs (~230 balls a disc), so a moderate base alpha lets
 * each dot read as a soft glowing disc rather than a blown-out blob. Combined in the
 * shader with the per-match DENSITY GAIN (uMatchTex.w) so a longer / run-heavier match
 * is no brighter than a short one (the design gate). Team-ignited dots resist it
 * (personalization survives). No-op outside the matchdots layout. Owner-tunable; baked
 * into the shader as MATCHDOTS_ALPHA.
 */
export const MATCHDOTS_ALPHA = 0.5;

/**
 * Base alpha multiplier the STRAND (non-dust) points settle to in the Ch 9 duel web
 * (§26): the ~316k balls collapse into ~1,691 strand clusters, so a moderate base
 * alpha lets each cluster read as a soft glowing band rather than a blown-out blob.
 * Team-ignited points resist it (personalization survives). No-op outside the duelweb
 * layout. Owner-tunable; baked into the shader as DUELWEB_ALPHA.
 */
export const DUELWEB_ALPHA = 0.5;

/* ---------------------------------------------------------------------------
 * Shared GLSL — the position + visibility core. Used verbatim by BOTH the
 * visual and the pick vertex shaders so their geometry can never drift.
 * ------------------------------------------------------------------------- */

/** Full uniform superset (both shaders declare it; unused uniforms compile out). */
const UNIFORMS_GLSL = /* glsl */ `
uniform float uProgress;      // 0 = layout A · 1 = layout B
uniform int uLayoutA;         // layout codes: 0 free · 1 columns · 2 wall · 3 assembly
uniform int uLayoutB;
uniform float uReveal;        // assembly stream-in 0..1 (chronological)
uniform float uInvN;          // 1 / nPoints
uniform float uHalfW;         // ortho frustum half-width (world)
uniform float uHalfH;         // ortho frustum half-height (world)
uniform float uPointScale;    // base point size, device px
uniform float uColHalfWidth;  // column body half-width (world)
uniform float uColBottom;     // column base y (world)
uniform float uColUsableH;    // tallest column height (world)
uniform float uInvMaxCount;   // 1 / max group count
// Per-group data texture (GROUP_COUNT × 4 RGBA float; texelFetch'd via grpRow()).
// Collapses SEVEN per-group uniform ARRAYS (uCols/uStar/uFlow/uResortX/uRiverX/
// uTideX/uGroupSeason — 189 hard vertex-uniform rows, since array elements never
// pack) into ONE sampler so the shared program links under the WebGL2 256-vertex-
// uniform-vector floor on mobile GPUs (desktop reports 1024, so it linked there;
// a phone at the floor failed to LINK and blacked out every scene). Rows:
//   row 0 = uCols        RGBA = (colX, wallRowY, 0, 0)
//   row 1 = uStar        RGBA = (phaseA.x, phaseA.y, phaseB.x, phaseB.y)
//   row 2 = uFlow        RGBA = (seasonX, baselineY, trueY, slope)
//   row 3 = packed       RGBA = (resortX, riverX, tideX, groupSeason-as-float)
// The uWorthTex / uMatchTex vertex-texture precedent — proven on the target GPUs.
uniform highp sampler2D uGroupTex;
uniform float uWallLeft;      // wall left edge (world)
uniform float uWallWidth;     // wall width (world)
uniform float uWallCellHalfW; // balls-faced cell jitter half-width (world)
uniform float uWallRowHalfH;  // season row jitter half-height (world)
uniform float uDim;           // global luminance multiplier (1 = full)
uniform float uWplDim;        // WPL-only luminance multiplier (1 = full)
uniform float uHlClass;       // subset-highlight class code (-1 none · 0-5 outcome · 6 wicket)
uniform float uHlLift;        // world-units vertical lift for highlighted points
uniform float uHlBoost;       // brightness boost for highlighted points
uniform float uOthersDim;     // luminance multiplier for non-highlighted points
uniform float uHlSkipWpl;     // 1 = WPL points never match the highlight (C1-5)
uniform float uResortClass;   // subset re-sort class code (-1 none · 0-5 outcome · 6 wicket)
uniform float uResortSkipWpl; // 1 = WPL points never re-sort (stay on the wall)
uniform float uResortEngage;  // 0 = base layout · 1 = matching points in columns
uniform float uResortLift;    // world-units peak of the flight arc
uniform float uResortTint;    // two-tone recolor strength 0..1 (top-10 vs rest)
uniform float uResortOthersDim; // luminance × for non-matching points while engaged
uniform float uResortInvMax;  // 1 / max per-group subset count (column height norm)
// per-group re-sort column centre x → uGroupTex row 3.x (grpRow(gi,3).x)
uniform float uPickedTeam;    // ignite: picked-team id (-1 = none)
uniform vec3 uTeamColor;      // picked team's color
uniform float uWallHeatMix;   // 0 = outcome colour · 1 = era-relative heat (C1-2 thesis beat)

// ---- Facet filter (R1b §12). A point is VISIBLE iff it passes every active
//      facet; failing points are hidden/ghosted (uFilterDim) and never pickable.
uniform float uFilterTeam;    // team id to keep, or -1 = team facet inactive
uniform int uFilterSeason;    // season YEAR to keep, or -1 = season facet inactive
// gi → season year (season-facet lookup) → uGroupTex row 3.w (int(grpRow(gi,3).w))
uniform float uFilterRangeLo; // point-index range lo (inclusive); range facet
uniform float uFilterRangeHi; //   active iff uFilterRangeHi > uFilterRangeLo
uniform float uFilterMatch;   // match index to keep, or -1 (needs aMatchIndex)
uniform float uFilterDim;     // luminance×alpha for FILTERED-OUT points (0 hide … 1 no-op)

// ---- Worm-space layout (Ch 2, §13). Fixed-aspect, letterboxed box; x = balls
//      faced (1..60+), y = cumulative innings runs (0..cap). Positions in-shader.
uniform float uWormLeft;      // world x at balls-faced 1
uniform float uWormWidth;     // world width across the balls-faced extent
uniform float uWormBottom;    // world y at cumulative runs 0
uniform float uWormHeight;    // world height across the cumulative-runs extent
uniform float uWormXCap;      // balls-faced display clamp (60 — the 60+ bucket)
uniform float uWormRunsCapNorm; // runs display cap as a NORMALIZED value (cap/255)
uniform float uWormCellHalfW; // in-cell x jitter half-width (haze texture)
uniform float uWormCellHalfH; // in-cell y jitter half-height (haze texture)

// ---- Run-out cascade (Ch 2, §14). Season-swept flash+fall of the aRunOut
//      subset; composes with worm-space, spends NO extra controlling morph.
uniform float uCascadeClass;    // -1 = inactive · >= 0 = cascade engaged (runOut)
uniform float uCascadeSweep;    // 0→1 season pointer (cohorts up to here have fallen)
uniform float uCascadeTint;     // red flash strength 0..1 (beat-gated hue exception)
uniform float uCascadeFall;     // world-units downward eject depth for fallen points
uniform float uCascadeFade;     // residual alpha × for a fully fallen point
uniform float uCascadeMute;     // team-glow desaturation 0..1 through the cascade
uniform float uCascadeMinSeason;// earliest season year (sweep origin)
uniform float uCascadeInvSpan;  // 1 / (latest - earliest season) — sweep normalizer

// ---- Frontier plane (Ch 3, §15). Fixed-aspect, letterboxed box; x = bowler-
//      season economy (aBowlEcon byte 0), y = bowling strike rate (aBowlSr byte
//      1, 255 = no-wicket sentinel → top 60+ bucket). Positions in-shader.
uniform float uFrontierLeft;    // world x at economy lo (left = cheap)
uniform float uFrontierWidth;   // world width across the economy extent
uniform float uFrontierBottom;  // world y at strike-rate lo (bottom = strikes fast)
uniform float uFrontierHeight;  // world height across the strike-rate extent
uniform float uFrontierCellHalfW; // per-bowler-season cloud x jitter (density haze)
uniform float uFrontierCellHalfH; // per-bowler-season cloud y jitter (density haze)

// ---- Dismissal rivers (Ch 3, §16). The bowler-credited wicket subset (aDismissal
//      >= 0) streams out of the frontier clouds into a flat-baseline 100%-stacked
//      band; composes with the frontier layout, spends NO extra controlling morph.
uniform float uRiversClass;     // -1 = inactive · >= 0 = rivers engaged (wicket)
uniform float uRiversEngage;    // 0 = points in clouds · 1 = fully stacked in bands
uniform float uRiversTint;      // categorical dismissal recolor strength (hue exception)
uniform float uRiversOthersDim; // luminance × for non-wicket points while engaged
uniform float uRiversMute;      // team-glow desaturation 0..1 through the rivers beat
uniform float uRiverBottom;     // world y at 0% share (the flat baseline)
uniform float uRiverHeight;     // world height spanning 0 → 100% share
uniform float uRiverHalfW;      // in-strip x jitter half-width (fills the strip)
// per-group season strip centre x → uGroupTex row 3.y (grpRow(gi,3).y)

// ---- Tide skyline (Ch 4, §18). Fixed-aspect, letterboxed box; x = season block
//      (uTideX[gi]) + within-season packing, y = a column filled to the innings
//      TOTAL. All three are packed into ONE attribute (aTide). First-innings balls
//      build columns; the rest settle into a low-alpha reservoir haze. In-shader.
uniform float uTideBottom;      // world y at innings total 0 (the coastline floor)
uniform float uTideHeight;      // world height spanning total 0 → TIDE_TOTAL_CAP
uniform float uTideInvCap;      // 1 / TIDE_TOTAL_CAP (decoded-total → 0..1)
uniform float uTideBlockHalfW;  // half-width of a season block (columns pack within ±)
uniform float uTideCellHalfW;   // per-column x jitter half-width (< the column pitch)
uniform float uTideReservoirH;  // world height of the reservoir haze band (non-first-inn)
// per-group season block centre x → uGroupTex row 3.z (grpRow(gi,3).z)

// ---- Waterline (Ch 4, §18). A LEVEL over the held tide layout: a first-innings
//      column whose innings total (runs) is below uWaterLevel drowns (LUMINANCE
//      only). Composes with the tide layout, spends NO extra controlling morph.
//      Inactive at uWaterLevel < 0, so R1/R2 render byte-identically.
uniform float uWaterLevel;      // going-rate level in RUNS; column total < this drowns. -1 = inactive
uniform float uWaterDrownDim;   // luminance × for a drowned column (1 = no dimming)
uniform float uWaterTeamKeep;   // 1 = the picked team's columns stay lit even when drowned

// ---- Worth grid (Ch 5, §19). Fixed-aspect, letterboxed 20-over × 10-wicket
//      state grid; positions in-shader from the packed aPrice attribute (cell =
//      over×10 + wicketsDown from restate.u8). The pricelens tables live in a
//      200×N RG float data texture: R = the cell's price LUMINANCE (0..1, the
//      scene's table) · G = the cell's DENSITY GAIN (client-derived from the
//      cell's point count, §0.1) — one row per table id fed via setWorthTables.
uniform float uWorthLeft;     // world x at over 0 (the grid's left edge)
uniform float uWorthWidth;    // world width across the 20 overs
uniform float uWorthBottom;   // world y at 9 wickets down (the grid's bottom edge)
uniform float uWorthHeight;   // world height (0 wickets down at the TOP)
uniform highp sampler2D uWorthTex; // 200×N RG float pricelens rows (lum, gain) —
                              // highp: the default lowp sampler would quantize the
                              // small density gains (min 0.02) into visible banding
uniform int uWorthRowA;       // pricelens table row A (-1 = neutral ramp)
uniform int uWorthRowB;       // pricelens table row B (-1 = neutral ramp)
uniform float uWorthMix;      // 0 = pure row A · 1 = pure row B (the era-flip lerp)

// ---- WPA subset-highlight (Ch 5, §21). Only read while uHlClass == 7: a point
//      matches iff |wpaByte − 127| ≥ uHlWpaMin and the byte isn't the 255
//      sentinel ("no WPA": D/L, undecided, short-target matches).
uniform float uHlWpaMin;      // min |wpaByte − 127| to match (byte units, ≥ 1)

// ---- Over rail (Ch 5, §20). The set-piece six-ball lift: the named points fly
//      to viewport-anchored slots as uRailProgress scrubs 0→1; everything else
//      dims by uRailDim. Members are CULLED from the main pass and drawn by a
//      dedicated RAIL_OVERLAY pass on top of the field (draw-order honesty: a
//      hero ball must never be fogged by later-indexed points). Inactive at
//      uRailN == 0, so every prior scene renders byte-identically.
uniform int uRailN;                // active rail slots (0 = inactive)
uniform float uRailIdx[RAIL_MAX];  // field point index per slot (bowling order)
uniform vec2 uRailSlot[RAIL_MAX];  // viewport-fraction anchors (x 0 left→1 right, y 0 top→1 bottom)
uniform float uRailProgress;       // 0 = balls in the field · 1 = balls at their slots
uniform float uRailDim;            // rest-of-field luminance×alpha at progress 1
uniform float uRailScale;          // hero point-size multiplier at the slots
uniform float uRailLift;           // world-units peak of the flight arc

// ---- Constellation (Ch 6, §22). Every ball condenses to its SEASON-GROUP STAR
//      centre. uStar[gi] holds the ball's star position for BOTH phase tables
//      (xy = table A / the "from" map, zw = table B / the "table" map), each a
//      normalized coord in the common [-1,1] frame; uStarMix lerps them (the phase
//      toggle — a coherent star-table swap, never a re-embed). The frame maps
//      1:1 in both axes into the fixed-aspect (square) letterboxed box (centred
//      at the origin, half-size uConstHalfExtent). A small radial jitter of
//      radius uConstStarR makes each star a glowing disc of its own balls.
//      Inactive for every prior layout (never code 8), so they render identically.
// per-gi star (xy = phase A · zw = phase B, normalized [-1,1]) → uGroupTex row 1 (grpRow(gi,1))
uniform float uStarMix;            // 0 = phase A · 1 = phase B (the phase-toggle lerp)
uniform float uConstHalfExtent;    // world half-size of the [-1,1] star frame (letterboxed)
uniform float uConstStarR;         // world radius of a star's jitter disc

// ---- Twin rivers (Ch 7, §23). Every ball condenses to its LEAGUE-SEASON RIVER
//      cell. uFlow[gi] packs the season's world geometry: x = season centre x
//      (shared time axis), y = the flat BASELINE run-rate height (world), z = the
//      TRUE run-rate height (world), w = the world slope toward the next same-league
//      season (the tilt that makes the band read as a continuous flowing ribbon).
//      The centreline lerps baseline→true by uFlowLift (the divergence reveal). A
//      fixed decorative band jitter (±uFlowBandHalf) makes the ribbon a band of its
//      own balls (NOT a ball-count encoding). x jitters ±uFlowHalfPitch so adjacent
//      seasons meet and the ribbon reads continuous. Inactive for every prior layout
//      (never code 9), so R1..R6 render byte-identically.
// per-gi (seasonX, baselineY, trueY, slope) in world units → uGroupTex row 2 (grpRow(gi,2))
uniform float uFlowHalfPitch;      // in-season x jitter half-width (half the year pitch, world)
uniform float uFlowBandHalf;       // decorative band half-thickness (world; constant, not ball count)
uniform float uFlowLift;           // 0 = baseline heights · 1 = true run-rate heights (the reveal)

// ---- Impact-sub sparks (Ch 7, §23). A luminance + small-lift glow over the
//      per-point aSpark flag (the 517 impact-sub deliveries, baked via setSparks).
//      Composes with any layout (the sparks glow as they enter the IPL river);
//      inactive at uSparkGlow == 0, so every prior scene renders byte-identically.
uniform float uSparkGlow;          // spark brightness/glow strength 0..1 (0 = inactive)
uniform float uSparkLift;          // world-units vertical lift for spark points
uniform float uSparkOthersDim;     // luminance × for non-spark points while sparks glow

// ---- Match-dots (Ch 8, §24). Every ball condenses to the CENTROID of its MATCH.
//      NO new per-point attribute + NO new buffer: the ball's match id is recovered
//      by a BINARY SEARCH of position.x against uMatchBoundsTex (1,331 monotone
//      block-start point indices), then its centroid + toss + density gain is read
//      from uMatchTex (per match: R = nx, G = ny normalized [-1,1]; B = toss class
//      0 bat-first / 1 field-first; A = per-match density gain). The centroid maps
//      1:1 into the letterboxed box via uMatchHalfExtent (per-axis); uMatchSplit lifts
//      each dot into its toss lane. A constant radial jitter (uMatchDotR) makes each
//      match a glowing disc. The whole block is gated on the matchdots layout (code
//      10) being in the mix, so the ~11-texelFetch binary search runs ONLY on
//      matchdots frames and every prior scene renders byte-identically.
uniform highp sampler2D uMatchTex;       // per-match: (nx, ny, toss, densityGain)
uniform highp sampler2D uMatchBoundsTex; // per-match: R = block-start point index (monotone)
uniform int uMatchN;                     // number of matches (binary-search bound)
uniform int uMatchTexW;                  // match-texture width (id → texel wrapping)
uniform vec2 uMatchHalfExtent;           // world half-extents: world = normalized × this
uniform float uMatchDotR;                // world radius of a match dot's constant jitter disc
uniform float uMatchLaneY;               // world lane-centre offset (bat-first up / field-first down)
uniform float uMatchLaneHalf;            // world lane band half-height (dots spread within a lane)
uniform float uMatchSplit;               // 0 = neutral centroid · 1 = lifted into the toss lanes

// ---- Review chips (Ch 8, §25). A subset over the held match-dots (the rivers/sparks
//      precedent). Membership + the packed lane+slot ride the REUSED aDismissal (review
//      code -1 none / 0 struck / 1 upheld) + aRiverPos (lane index in the integer part,
//      cumulative stack slot 0..1 in the fraction), so aTeam is NEVER touched (team-
//      ignite stays correct in every chapter) and no new attribute is added. The 988
//      review balls fly out into per-lane columns (struck-down red at the bottom, upheld
//      green on top). Inactive at uReviewClass < 0, so every prior scene is byte-identical.
uniform float uReviewClass;         // -1 = inactive · >= 0 = review chips engaged
uniform float uReviewEngage;        // 0 = balls on their match-dots · 1 = fully stacked in the chips
uniform float uReviewTint;          // green/red outcome recolor strength (luminance-separated, CVD-safe)
uniform float uReviewOthersDim;     // luminance × for non-review points while the chips are engaged
uniform float uReviewLaneX[TEAM_COUNT]; // world x per franchise lane index
uniform float uReviewBottom;        // world y at the stack baseline (0%)
uniform float uReviewHeight;        // world height spanning 0 → the busiest lane
uniform float uReviewLaneHalfW;     // in-lane x jitter half-width (fills the column)
uniform float uReviewChipJitter;    // small in-slot y jitter (chips read as a soft stack)

// ---- Duel web (Ch 9, §26). Every ball condenses to its DUEL's strand-midpoint
//      cluster centre (px, py normalized [-1,1]) + a small radial jitter disc, so a
//      strand reads as a glowing band of its own balls; balls in no tracked pairing
//      scatter as low-alpha DUST. NO new per-point attribute + NO new buffer: the
//      ball's duel id rides uPairingTex (indexed by point index; 0xFFFF = dust), and
//      the duel's cluster centre + dominance color + ball weight is read from uDuelTex.
//      Per-duel focus (0..1, for the strand recede) rides uDuelFocusTex (fed via
//      setDuelFocus). The whole block is gated on the duelweb layout (code 11) being in
//      the mix, so the fetches run ONLY on duelweb frames and every prior scene renders
//      byte-identically.
uniform highp sampler2D uPairingTex;   // per-point: R = duel id (0xFFFF = dust), indexed by point index
uniform int uPairingTexW;              // pairing-texture width (point index → texel wrapping)
uniform highp sampler2D uDuelTex;      // per-duel: (px, py normalized [-1,1], dominance color -1..1, ballWeight)
uniform int uDuelTexW;                 // duel-texture width (id → texel wrapping)
uniform highp sampler2D uDuelFocusTex; // per-duel: R = focus 0..1 (1 = lit · 0 = recede candidate)
uniform int uDuelFocusTexW;            // duel-focus-texture width (id → texel wrapping)
uniform float uDuelHalfExtent;         // world half-extent: world = normalized × this (square box)
uniform float uDuelDotR;               // world radius of a strand cluster's constant jitter disc
uniform float uDuelReveal;             // 0 = strand points hidden · 1 = fully drawn (the web draw)
uniform float uDuelDominance;          // 0 = outcome colour · 1 = full red/white/blue dominance recolor
uniform float uDuelDustDim;            // luminance × for the dust balls (1 = no dimming)
uniform float uStrandRecede;           // 0 = every knot lit · 1 = non-focus knots receded to neutral
`;

/** Core per-point attributes (both shaders read these). */
function coreAttrsGlsl(hasMatch: boolean): string {
	return /* glsl */ `
in float aAttrs;
in float aBallsFaced;
in float aTeam;
in float aSubOrd;
in float aCumRuns;  // batter cumulative innings runs, NORMALIZED 0..1 (worm-space y)
in float aRunOut;   // packed runtime FLAG bits (no wire cost): bit0 = run-out (Ch 2
                    // cascade), bit1 = impact-sub spark (Ch 7). One attribute holds
                    // both — they are baked via setRunouts / setSparks and Ch 2 and
                    // Ch 7 never render together, so packing keeps the field inside
                    // the vertex-attribute budget (adding a 15th attribute overflows
                    // the ANGLE/Metal ceiling — CONTRACT §18.6 / §23).
in float aBowlEcon; // bowler-season economy byte 0..254 (frontier x); raw, non-normalized
in float aBowlSr;   // bowler-season strike-rate byte 0..254, 255 = no-wicket sentinel (frontier y)
in float aDismissal;// dismissal-kind flag -1 none / 0 bowled / 1 lbw / 2 caught / 3 stumped (rivers)
in float aRiverPos; // stacked 0..1 share-position within the season strip (rivers y); baked on-device
in float aTide;     // packed tide record (§18), baked on-device to stay within the
                    // vertex-attribute budget: innings-total byte (bits 0-7; runs =
                    // byte×2, tide y), within-season packing slot quantized 0..1023
                    // (bits 8-17; tide x, innings ranked short→tall), first-innings
                    // flag (bit 18; 0 routes the ball to the reservoir haze)
in float aPrice;    // packed Ch 5 record (§19/§21), baked on-device (attribute
                    // budget): state-cell byte from restate.u8 (bits 0-7; cell =
                    // over×10 + wicketsDown, worth-grid position) + WPA byte from
                    // wpa.u8 × 256 (bits 8-15; 127 = zero swing, 255 = sentinel)
${hasMatch ? 'in float aMatchIndex; // per-delivery match index (u16)' : ''}
`;
}

/** pcg hash + layout picker + facet-filter test + the shared position core. */
function coreBodyGlsl(): string {
	return /* glsl */ `
// PCG hash — exact integer path, no float-precision striping at 316k indices.
uint pcg(uint v) {
	uint state = v * 747796405u + 2891336453u;
	uint word = ((state >> ((state >> 28u) + 4u)) ^ state) * 277803737u;
	return (word >> 22u) ^ word;
}
const float INV32 = 1.0 / 4294967296.0;

// match-dots (§24): id → texel in the match textures (wraps if the match count ever
// exceeds one texture row; uMatchTexW is the width fed by field.ts, so 1,331 sits in
// row 0). Shared by the centroid (uMatchTex) and bounds (uMatchBoundsTex) fetches.
ivec2 mtexel(int id) { return ivec2(id % uMatchTexW, id / uMatchTexW); }

// per-group data-texture fetch: row 0 = uCols (colX, wallRowY) · row 1 = uStar
// (phaseA.xy, phaseB.zw) · row 2 = uFlow (seasonX, baselineY, trueY, slope) ·
// row 3 = packed scalars (resortX, riverX, tideX, groupSeason). Replaces the 7
// per-group uniform ARRAYS (189 vertex-uniform rows) with ONE texelFetch so the
// program links under the WebGL2 256-vertex-uniform-vector floor on mobile GPUs.
vec4 grpRow(int gi, int row) { return texelFetch(uGroupTex, ivec2(gi, row), 0); }

vec3 pickLayout(int id, vec3 pFree, vec3 pCols, vec3 pWall, vec3 pWorms, vec3 pFrontier, vec3 pTide, vec3 pWorth, vec3 pConst, vec3 pFlow, vec3 pMatch, vec3 pDuel) {
	if (id == 1) return pCols;
	if (id == 2) return pWall;
	if (id == 4) return pWorms;
	if (id == 5) return pFrontier;
	if (id == 6) return pTide;
	if (id == 7) return pWorth;
	if (id == 8) return pConst;
	if (id == 9) return pFlow;
	if (id == 10) return pMatch;
	if (id == 11) return pDuel;
	return pFree; // 0 free · 3 assembly share the free-field scatter
}

// Density-haze layouts (worm-space code 4, frontier code 5): the field settles
// to low alpha so overlapping balls read as texture, and the reader's team
// resists the haze. Shared test so both use the same wormWeight path.
bool isHazeLayout(int id) { return id == 4 || id == 5; }

// Facet filter (R1b §12): true iff the point passes every ACTIVE facet.
bool passesFilter(int gi) {
	if (uFilterTeam >= 0.0 && abs(aTeam - uFilterTeam) >= 0.5) return false;
	if (uFilterSeason >= 0 && int(grpRow(gi, 3).w) != uFilterSeason) return false;
	if (uFilterRangeHi > uFilterRangeLo &&
		(position.x < uFilterRangeLo || position.x >= uFilterRangeHi)) return false;
#ifdef HAS_MATCH
	if (uFilterMatch >= 0.0 && abs(aMatchIndex - uFilterMatch) >= 0.5) return false;
#endif
	return true;
}

// Everything that decides WHERE a point is and WHETHER it renders. Shared so
// the pick pass is registered to the visual field and honours the same filter.
struct Core {
	vec3 pos;
	bool culled;         // assembly frontier hasn't reached this point → offscreen
	float assemblyAlpha; // rain-in alpha (1 outside the assembly window)
	bool filterPass;     // passes every active facet (pickable + full brightness)
	int outcome;
	bool wicket;
	bool wpl;
	bool top10;
	bool hlMatch;        // matches uHlClass (color brighten / others-dim)
	bool matchResort;    // matches uResortClass (color recolor)
	float reAmt;         // resort engage weight for the recolor
	float baseSizeMul;   // outcome-driven base point-size multiplier
	float wormWeight;    // 0..1 amount of density-haze layout in the A/B mix (haze alpha)
	bool runOut;         // run-out membership flag (aRunOut) — cascade subset
	float cascadeFall;   // 0..1 fall progress for this point's season cohort
	float cascadeFlash;  // 0..1 red-flash intensity as the season wave crosses
	bool riverMember;    // bowler-credited wicket (aDismissal >= 0) — rivers subset
	float riverEngage;   // 0..1 rivers engage weight (recolor / others-dim strength)
	float tideWeight;    // 0..1 amount of the tide layout in the A/B mix (drown / reservoir gate)
	bool tideFirst;      // builds a tide column (aTide bit 18) — vs the reservoir haze
	float tideTotal;     // decoded innings total in RUNS (byte × 2) — the waterline drown test
	float worthWeight;   // 0..1 amount of the worth layout in the A/B mix (pricelens gate)
	float worthCell;     // decoded state cell 0..199 (aPrice bits 0-7) — pricelens texel x
	float wpaByte;       // decoded WPA byte 0..255 (aPrice bits 8-15; 255 = sentinel)
	bool railMember;     // one of the over rail's named points (§20)
	float railT;         // 0..1 flight progress toward the rail slot (overlay pass only)
	bool spark;          // impact-sub spark membership (aSpark) — Ch 7 luminance lift (§23)
	float flowWeight;    // 0..1 amount of the twin-rivers layout in the A/B mix (ribbon alpha)
	float matchWeight;   // 0..1 amount of the matchdots layout in the A/B mix (§24 settle alpha)
	float matchGain;     // per-match density gain (§24 constant-brightness discs; 1 outside matchdots)
	bool reviewMember;   // review-chip subset member (aDismissal >= 0 while reviews engaged, §25)
	float duelWeight;    // 0..1 amount of the duel-web layout in the A/B mix (§26 settle / hue / recede gate)
	float duelColor;     // per-duel dominance color -1..1 (+1 batter-red / -1 bowler-blue; 0 outside duelweb)
	float duelFocus;     // per-duel focus 0..1 (1 = lit · 0 = recede candidate; 1 outside duelweb)
	bool duelDust;       // true when this ball is in no tracked pairing (dust scatter) — §26
};

Core computeCore() {
	Core o;
	float ord = position.z;
	int gi = int(position.y + 0.5);

	// four decorrelated hash draws chained from the point index
	uint r1 = pcg(uint(position.x));
	uint r2 = pcg(r1);
	uint r3 = pcg(r2);
	uint r4 = pcg(r3);
	float h1 = float(r1) * INV32;
	float h2 = float(r2) * INV32;
	float h3 = float(r3) * INV32;
	float h4 = float(r4) * INV32;

	// decode the packed attr byte
	int a = int(aAttrs + 0.5);
	o.outcome = a & 7;
	o.wicket = (a & 8) != 0;
	o.wpl = (a & 16) != 0;
	o.top10 = (a & 32) != 0;
	// run-out membership is a dedicated flag (seeded from attrs bit 6 or a CPU
	// index set) so it is decoupled from the immutable attr byte — see §14.
	// aRunOut is a packed flag byte: bit0 = run-out (Ch 2 cascade), bit1 = impact-sub
	// spark (Ch 7). Decoding bit0 with mod is byte-identical to the old gt-0.5 test for
	// every value the run-out path ever sets (0/1), so R1..R4a render identically.
	o.runOut = mod(aRunOut, 2.0) >= 0.5;
	o.spark = aRunOut >= 1.5; // bit1 set (value 2 or 3) — the Ch 7 spark subset (§23)

	// subset re-sort membership (drives position + color)
	bool resortOn = uResortClass >= 0.0;
	o.matchResort = false;
	if (resortOn) {
		int rc = int(uResortClass + 0.5);
		o.matchResort = (rc == 6) ? o.wicket : (o.outcome == rc);
		if (o.matchResort && uResortSkipWpl > 0.5 && o.wpl) o.matchResort = false;
	}

	// free field — WPL its own upper-right constellation, IPL cloud below a gap
	vec3 posFree;
	if (o.wpl) {
		posFree = vec3(
			(0.50 + (h1 * 2.0 - 1.0) * 0.42) * uHalfW,
			(0.76 + (h2 * 2.0 - 1.0) * 0.14) * uHalfH,
			(h3 - 0.5) * 0.8
		);
	} else {
		posFree = vec3(
			(h1 * 2.0 - 1.0) * uHalfW * 0.95,
			((h2 * 2.0 - 1.0) * 0.72 - 0.20) * uHalfH,
			(h3 - 0.5) * 0.8
		);
	}

	// season columns
	vec2 col = grpRow(gi, 0).xy; // uCols[gi] → uGroupTex row 0 (colX, wallRowY)
	vec3 posCols = vec3(
		col.x + (h4 * 2.0 - 1.0) * uColHalfWidth,
		uColBottom + (ord + h2 * 1.5) * uInvMaxCount * uColUsableH,
		(h3 - 0.5) * 0.25
	);

	// ignition wall
	float bf = clamp(aBallsFaced, 1.0, 30.0);
	float cellT = (bf - 1.0) / 29.0;
	vec3 posWall = vec3(
		uWallLeft + cellT * uWallWidth + (h4 * 2.0 - 1.0) * uWallCellHalfW,
		col.y + (h2 * 2.0 - 1.0) * uWallRowHalfH,
		(h3 - 0.5) * 0.25
	);

	// worm-space (Ch 2): x = balls faced (1..60+), y = cumulative innings runs.
	// The par / anchor exemplar worms are the SCENE's job on the annotation plane
	// (registered via projectToCss); the GL field here is the density haze only.
	float wbf = clamp(aBallsFaced, 1.0, uWormXCap);
	float wx = (wbf - 1.0) / (uWormXCap - 1.0);
	float wy = clamp(aCumRuns / uWormRunsCapNorm, 0.0, 1.0);
	vec3 posWorms = vec3(
		uWormLeft + wx * uWormWidth + (h4 * 2.0 - 1.0) * uWormCellHalfW,
		uWormBottom + wy * uWormHeight + (h2 * 2.0 - 1.0) * uWormCellHalfH,
		(h3 - 0.5) * 0.25
	);

	// frontier plane (Ch 3, §15): x = bowler-season economy (byte 0, [4,16]),
	// y = bowler-season strike rate (byte 1, [8,60]; 255 = no-wicket sentinel →
	// top 60+ bucket). byte/254 IS the normalized axis position (the buffer is
	// encoded over the same lo/hi the box spans), so this matches frontierPoint()
	// exactly and the SVG edge/ghost/anchors can never drift from the GL haze.
	float fex = clamp(aBowlEcon, 0.0, 254.0) / 254.0;
	float fsy = (aBowlSr >= 254.5) ? 1.0 : clamp(aBowlSr / 254.0, 0.0, 1.0);
	vec3 posFrontier = vec3(
		uFrontierLeft + fex * uFrontierWidth + (h4 * 2.0 - 1.0) * uFrontierCellHalfW,
		uFrontierBottom + fsy * uFrontierHeight + (h2 * 2.0 - 1.0) * uFrontierCellHalfH,
		(h3 - 0.5) * 0.25
	);

	// tide skyline (Ch 4, §18): x = season block (uTideX[gi]) + within-season
	// packing slot, y = a column filled from the floor up to the innings TOTAL. The
	// per-point record is packed into ONE attribute (aTide) to stay within the GPU
	// vertex-attribute budget; decode it the same way the pick shader decodes its
	// index (exact integers < 2^23 in highp): byte (runs = byte×2, the
	// innings_total.u8 scale) + 256·colQuant(0..1023) + 262144·firstFlag.
	float tideByte = mod(aTide, 256.0);
	float tideRest = floor(aTide / 256.0);
	float tideColQ = mod(tideRest, 1024.0);
	o.tideFirst = floor(tideRest / 1024.0) > 0.5;
	o.tideTotal = tideByte * 2.0;
	float tideColPos = (tideColQ / 1023.0) * 2.0 - 1.0; // within-season slot -1..1
	float tideNorm = clamp(o.tideTotal * uTideInvCap, 0.0, 1.0);
	vec3 posTide;
	if (o.tideFirst) {
		// h1 fills the column uniformly from the floor to the total (the top ≈ total)
		posTide = vec3(
			grpRow(gi, 3).z + tideColPos * uTideBlockHalfW + (h4 * 2.0 - 1.0) * uTideCellHalfW,
			uTideBottom + h1 * tideNorm * uTideHeight,
			(h3 - 0.5) * 0.25
		);
	} else {
		// reservoir haze: spread across the season block, low near the floor
		posTide = vec3(
			grpRow(gi, 3).z + (h4 * 2.0 - 1.0) * uTideBlockHalfW,
			uTideBottom + h1 * uTideReservoirH,
			(h3 - 0.5) * 0.25
		);
	}

	// worth grid (Ch 5, §19): cell = over×10 + wicketsDown (restate.u8 byte in
	// aPrice bits 0-7). x = the over (0 left → 19 right), y = wickets fallen
	// (0 at the TOP → 9 at the bottom), deterministic jitter packing the cell
	// body (WORTH_CELL_FILL of the pitch — the gutter keeps cells readable).
	// This matches worthCell() in layout.ts exactly, so annotation-plane rings
	// and hatches can never drift from the GL cells.
	o.worthCell = min(mod(aPrice, 256.0), 199.0);
	o.wpaByte = floor(aPrice / 256.0);
	float wOver = floor(o.worthCell / 10.0);
	float wDown = o.worthCell - wOver * 10.0;
	vec3 posWorth = vec3(
		uWorthLeft + ((wOver + 0.5 + (h4 - 0.5) * WORTH_CELL_FILL) / 20.0) * uWorthWidth,
		uWorthBottom + (1.0 - (wDown + 0.5 + (h2 - 0.5) * WORTH_CELL_FILL) / 10.0) * uWorthHeight,
		(h3 - 0.5) * 0.25
	);

	// constellation (Ch 6, §22): the ball's season-group STAR centre. uStar[gi]
	// carries the star's normalized [-1,1] position for both phase tables (xy =
	// A, zw = B); uStarMix lerps them (the phase toggle — the WHOLE season-cohort
	// glides together, no per-point stagger, since every ball of a season shares
	// gi and so shares starN + a fixed jitter offset → the disc translates
	// rigidly, Gestalt common fate). The frame maps 1:1 into the square box
	// (centred at the origin), matching constellationPoint() exactly so the SVG
	// worm / threads / labels can never drift. A radial jitter (h4 angle, h1
	// radius; linear radius → a centre-dense glow) makes the star a disc of balls.
	vec4 starV = grpRow(gi, 1); // uStar[gi] → uGroupTex row 1 (phaseA.xy, phaseB.zw)
	vec2 starN = mix(starV.xy, starV.zw, uStarMix);
	float starAng = h4 * 6.28318530718;
	float starRad = uConstStarR * h1;
	vec3 posConstellation = vec3(
		starN.x * uConstHalfExtent + cos(starAng) * starRad,
		starN.y * uConstHalfExtent + sin(starAng) * starRad,
		(h3 - 0.5) * 0.25
	);

	// twin rivers (Ch 7, §23): x = the ball's season centre (uFlow[gi].x) + an
	// in-season jitter of ±uFlowHalfPitch so adjacent seasons meet and the ribbon
	// reads continuous; y = the season's centreline run-rate height, lerped from the
	// flat BASELINE (uFlow[gi].y) to the TRUE height (uFlow[gi].z) by uFlowLift (the
	// divergence reveal), tilted toward the next season by the world slope
	// (uFlow[gi].w) so the band flows, plus a FIXED decorative band jitter of
	// ±uFlowBandHalf (a constant thickness, NOT a ball-count encoding — height means
	// run rate). WPL seasons carry their own gi with the same season x as the IPL
	// year, so the two rivers coexist on one time axis and diverge at 2023. This
	// matches flowSeasonToX / flowRateToY in layout.ts exactly, so the SVG
	// centrelines / axis / fork marker can never drift from the GL ribbons.
	vec4 fv = grpRow(gi, 2); // uFlow[gi] → uGroupTex row 2 (seasonX, baselineY, trueY, slope)
	float flowXOff = (h4 * 2.0 - 1.0) * uFlowHalfPitch;
	float flowCy = mix(fv.y, fv.z, clamp(uFlowLift, 0.0, 1.0)) + fv.w * flowXOff;
	vec3 posFlow = vec3(
		fv.x + flowXOff,
		flowCy + (h2 * 2.0 - 1.0) * uFlowBandHalf,
		(h3 - 0.5) * 0.25
	);

	// match-dots (Ch 8, §24): every ball condenses to the CENTROID of its MATCH.
	// GATED on the matchdots layout (code 10) being in the mix, so the ~11-texelFetch
	// binary search runs ONLY on matchdots frames — every prior scene skips it, and
	// posMatch stays the cheap free scatter (pickLayout returns it only for id == 10,
	// which never happens off the matchdots layout, so it is never USED). This keeps
	// R0..R7 byte-identical AND spends the search cost only where the layout is live.
	vec3 posMatch = posFree;
	o.matchGain = 1.0;
	if (uLayoutA == 10 || uLayoutB == 10) {
		// binary search: the largest match m with bounds[m] <= this ball's point index.
		// A match's deliveries are contiguous in point order, so bounds is monotone and
		// bounds[0] == 0, so lo always converges to this ball's own match block.
		int mlo = 0;
		int mhi = uMatchN - 1;
		for (int it = 0; it < 12; it++) {   // ceil(log2(1331)) = 11, +1 safety
			if (mlo >= mhi) break;
			int mid = (mlo + mhi + 1) / 2;
			float b = texelFetch(uMatchBoundsTex, mtexel(mid), 0).r;
			if (b <= position.x) mlo = mid; else mhi = mid - 1;
		}
		vec4 mc = texelFetch(uMatchTex, mtexel(mlo), 0); // (nx, ny, toss, densityGain)
		o.matchGain = mc.w;
		float mnx = mc.x;
		float mny = mc.y;
		// neutral centroid y vs the toss lane (bat-first up, field-first down); the dots
		// spread within a lane by their own centroid ny so the lane reads as a band that
		// swells where the data has more matches — the field-first river after 2016.
		float baseCy = mny * uMatchHalfExtent.y;
		float laneSign = (mc.z < 0.5) ? 1.0 : -1.0;
		float laneCy = laneSign * uMatchLaneY + mny * uMatchLaneHalf;
		float cy = mix(baseCy, laneCy, clamp(uMatchSplit, 0.0, 1.0));
		// constant radial jitter disc (linear radius → a centre-dense glow, the
		// constellation precedent) — a run-heavy / longer match is no fatter than a
		// low-scoring one, since nothing about the disc encodes a stat (design gate).
		float mAng = h4 * 6.28318530718;
		float mRad = uMatchDotR * h1;
		posMatch = vec3(
			mnx * uMatchHalfExtent.x + cos(mAng) * mRad,
			cy + sin(mAng) * mRad,
			(h3 - 0.5) * 0.25
		);
	}

	// duel web (Ch 9, §26): every ball condenses to its DUEL's strand-midpoint cluster.
	// GATED on the duelweb layout (code 11) being in the mix, so the pairing / duel
	// texelFetches run ONLY on duelweb frames — every prior scene skips them, and posDuel
	// stays the cheap free scatter (pickLayout returns it only for id == 11, which never
	// happens off the duelweb layout, so it is never USED). This keeps R0..R8 byte-
	// identical AND spends the fetch cost only where the layout is live. NO new attribute:
	// the ball's duel id rides uPairingTex, indexed by its own point index (position.x).
	vec3 posDuel = posFree;
	o.duelColor = 0.0;
	o.duelFocus = 1.0;
	o.duelDust = true;
	if (uLayoutA == 11 || uLayoutB == 11) {
		int pidx = int(position.x + 0.5);
		int did = int(texelFetch(uPairingTex, ivec2(pidx % uPairingTexW, pidx / uPairingTexW), 0).r + 0.5);
		if (did >= 65534) {
			// dust: a ball in no tracked pairing → a diffuse low-alpha scatter (reuse posFree)
			posDuel = posFree;
			o.duelDust = true;
		} else {
			vec4 dv = texelFetch(uDuelTex, ivec2(did % uDuelTexW, did / uDuelTexW), 0); // (px, py, color, ballWeight)
			o.duelColor = dv.z;
			o.duelDust = false;
			o.duelFocus = texelFetch(uDuelFocusTex, ivec2(did % uDuelFocusTexW, did / uDuelFocusTexW), 0).r;
			// constant radial jitter disc (linear radius → a centre-dense glow, the
			// constellation / match-dots precedent) so a strand reads as a disc of balls;
			// nothing about the disc encodes a stat (design gate).
			float dAng = h4 * 6.28318530718;
			float dRad = uDuelDotR * h1;
			posDuel = vec3(
				dv.x * uDuelHalfExtent + cos(dAng) * dRad,
				dv.y * uDuelHalfExtent + sin(dAng) * dRad,
				(h3 - 0.5) * 0.25
			);
		}
	}

	// morph with per-point stagger so the field streams, not teleports
	float delay = h3 * 0.55;
	float t = clamp(uProgress * 1.55 - delay, 0.0, 1.0);
	t = t * t * (3.0 - 2.0 * t);
	vec3 pos = mix(
		pickLayout(uLayoutA, posFree, posCols, posWall, posWorms, posFrontier, posTide, posWorth, posConstellation, posFlow, posMatch, posDuel),
		pickLayout(uLayoutB, posFree, posCols, posWall, posWorms, posFrontier, posTide, posWorth, posConstellation, posFlow, posMatch, posDuel),
		t
	);

	// how much of a density-haze layout (worm-space 4 or frontier 5) is in the
	// current mix — drives the low-alpha haze (no-op for R1 layouts, never 4/5).
	o.wormWeight = (isHazeLayout(uLayoutA) ? (1.0 - t) : 0.0) + (isHazeLayout(uLayoutB) ? t : 0.0);

	// how much of the tide layout (code 6) is in the mix — gates the waterline
	// drown + the reservoir alpha (no-op for every R1/R2 layout, never 6).
	o.tideWeight = (uLayoutA == 6 ? (1.0 - t) : 0.0) + (uLayoutB == 6 ? t : 0.0);

	// how much of the worth layout (code 7) is in the mix — gates the pricelens
	// recolor + density gain (no-op for every prior layout, never 7).
	o.worthWeight = (uLayoutA == 7 ? (1.0 - t) : 0.0) + (uLayoutB == 7 ? t : 0.0);

	// how much of the twin-rivers layout (code 9) is in the mix — gates the ribbon
	// alpha (no-op for every prior layout, never 9).
	o.flowWeight = (uLayoutA == 9 ? (1.0 - t) : 0.0) + (uLayoutB == 9 ? t : 0.0);

	// how much of the match-dots layout (code 10) is in the mix — gates the settle
	// alpha + the per-match density gain + the size/glow flatten (§24). No-op for
	// every prior layout (matchWeight is 0, never code 10), so R0..R7 are byte-identical.
	o.matchWeight = (uLayoutA == 10 ? (1.0 - t) : 0.0) + (uLayoutB == 10 ? t : 0.0);

	// how much of the duel-web layout (code 11) is in the mix — gates the settle alpha
	// + the dominance hue + the strand recede + the dust dim (§26). No-op for every prior
	// layout (duelWeight is 0, never code 11), so R0..R8 are byte-identical.
	o.duelWeight = (uLayoutA == 11 ? (1.0 - t) : 0.0) + (uLayoutB == 11 ? t : 0.0);

	// impact-sub spark lift (§23) — the POSITION change lives here so the pick pass
	// tracks the lifted spark; the brighten/glow is per-shader (visual). Gated on
	// uSparkGlow so it is a no-op for every prior scene (byte-identical).
	if (uSparkGlow > 0.0 && o.spark) pos.y += uSparkLift * uSparkGlow;

	// subset re-sort flight — matching points arc into their season's column
	if (o.matchResort) {
		float re = clamp(uResortEngage * 1.55 - delay, 0.0, 1.0);
		re = re * re * (3.0 - 2.0 * re);
		vec3 posCol = vec3(
			grpRow(gi, 3).x + (h4 * 2.0 - 1.0) * uColHalfWidth,
			uColBottom + (aSubOrd + 0.5 + h2 * 0.6) * uResortInvMax * uColUsableH,
			(h3 - 0.5) * 0.25
		);
		pos = mix(pos, posCol, re);
		pos.y += 4.0 * re * (1.0 - re) * uResortLift;
	}

	// dismissal rivers flight (§16): bowler-credited wickets (aDismissal >= 0)
	// stream out of their frontier cloud into the flat-baseline 100%-stacked band.
	// aRiverPos is the baked stacked share-position (0 baseline → 1 top); the
	// season strip x is a per-group uniform. Reversible: uRiversEngage 1→0 returns
	// each wicket to its cloud. A cross-cutting POSITION modifier like the re-sort.
	o.riverMember = false;
	o.riverEngage = 0.0;
	if (uRiversClass >= 0.0 && aDismissal >= -0.5) {
		o.riverMember = true;
		o.riverEngage = clamp(uRiversEngage, 0.0, 1.0);
		float rv = clamp(uRiversEngage * 1.55 - delay, 0.0, 1.0);
		rv = rv * rv * (3.0 - 2.0 * rv);
		vec3 posBand = vec3(
			grpRow(gi, 3).y + (h4 * 2.0 - 1.0) * uRiverHalfW,
			uRiverBottom + aRiverPos * uRiverHeight,
			(h3 - 0.5) * 0.25
		);
		pos = mix(pos, posBand, rv);
	}

	// review chips flight (§25): the 988 review deliveries (aDismissal >= 0 while the
	// reviews are engaged) fly OUT of the held match-dots into per-team chip columns.
	// The REUSED aRiverPos packs the franchise LANE index (integer part) + the cumulative
	// stack slot 0..1 (fraction), so aTeam stays untouched and no attribute is added.
	// Struck-down (aDismissal 0) chips sit low, upheld (aDismissal 1) high — the slot is
	// baked cumulative struck-then-upheld in field.ts. Reversible: uReviewEngage 1→0
	// returns each chip to its match-dot. A cross-cutting POSITION modifier like the rivers.
	o.reviewMember = false;
	if (uReviewClass >= 0.0 && aDismissal >= -0.5) {
		o.reviewMember = true;
		float lane = floor(aRiverPos);
		float slot = aRiverPos - lane;
		int li = int(lane + 0.5);
		float laneX = uReviewLaneX[li];
		vec3 posChip = vec3(
			laneX + (h4 * 2.0 - 1.0) * uReviewLaneHalfW,
			uReviewBottom + slot * uReviewHeight + (h2 * 2.0 - 1.0) * uReviewChipJitter,
			(h3 - 0.5) * 0.25
		);
		float cv = clamp(uReviewEngage * 1.55 - delay, 0.0, 1.0);
		cv = cv * cv * (3.0 - 2.0 * cv);
		pos = mix(pos, posChip, cv);
	}

	// assembly stream-in: chronological reveal by point index
	o.assemblyAlpha = 1.0;
	o.culled = false;
	if (uLayoutA == 3 || uLayoutB == 3) {
		float ci = position.x * uInvN;
		float d = (uReveal * (1.0 + RAIN_W) - ci) / RAIN_W;
		if (d <= 0.0) {
			o.culled = true;
		} else if (d < 1.0) {
			float fall = 1.0 - d;
			pos.y += fall * fall * uHalfH * 1.35; // rains in from above
			o.assemblyAlpha *= d;
		}
	}

	// base point size from the outcome class (wicket takes priority)
	float sizeMul = 1.0;
	if (o.wicket) sizeMul = 1.45;
	else if (o.outcome == 3) sizeMul = 1.5;
	else if (o.outcome == 4) sizeMul = 1.9;
	o.baseSizeMul = sizeMul;

	// subset highlight — the LIFT is position (shared); the color is per-shader.
	// Class 7 (§21) selects by WPA swing size: |wpaByte − 127| ≥ uHlWpaMin, with
	// the 255 sentinel ("no WPA") never matching.
	o.hlMatch = false;
	if (uHlClass >= 0.0) {
		int hc = int(uHlClass + 0.5);
		bool m;
		if (hc == 7) m = o.wpaByte < 254.5 && abs(o.wpaByte - 127.0) >= uHlWpaMin;
		else m = (hc == 6) ? o.wicket : (o.outcome == hc);
		if (m && uHlSkipWpl > 0.5 && o.wpl) m = false;
		o.hlMatch = m;
		if (m) pos.y += uHlLift;
	}

	// run-out cascade fall (§14) — the POSITION change lives here so the pick
	// pass tracks the fallen point; the red flash / fade is per-shader (visual).
	// Each season's cohort shares one phase (per-gi season pointer) → the whole
	// cohort falls TOGETHER as one synchronized wave (Gestalt common fate).
	o.cascadeFall = 0.0;
	o.cascadeFlash = 0.0;
	if (uCascadeClass >= 0.0 && o.runOut) {
		float seasonPos = clamp((grpRow(gi, 3).w - uCascadeMinSeason) * uCascadeInvSpan, 0.0, 1.0);
		// carry the sweep just past 1 so the final season fully falls at sweep 1
		float effSweep = uCascadeSweep * (1.0 + CASCADE_FLASH_W);
		float local = (effSweep - seasonPos) / CASCADE_FLASH_W;
		if (local > 0.0) {
			float f = clamp(local, 0.0, 1.0);
			float fallT = f * f * (3.0 - 2.0 * f);
			o.cascadeFall = fallT;
			pos.y -= fallT * uCascadeFall;
			// flash brightest right as the wave hits (local ~0), fading as it falls
			o.cascadeFlash = 1.0 - smoothstep(0.0, 0.6, local);
		}
	}

	// over rail (§20) — the set-piece six-ball lift. Membership is a tiny
	// uniform index set (≤ RAIL_MAX, no attribute cost): rail members are CULLED
	// from the main pass (both visual and pick) while the rail is engaged, and a
	// dedicated RAIL_OVERLAY draw — compiled from this same core — flies them to
	// their viewport-anchored slots ON TOP of the whole field, so a hero ball is
	// never fogged by later-indexed points (draw order = point order). Fully
	// reversible: uRailProgress back to 0 returns each ball to its exact field
	// position. A no-op at uRailN == 0 (every prior scene, byte-identical).
	o.railMember = false;
	o.railT = 0.0;
	int railSlot = -1;
	if (uRailN > 0) {
		for (int i = 0; i < RAIL_MAX; i++) {
			if (i >= uRailN) break;
			if (abs(position.x - uRailIdx[i]) < 0.5) { railSlot = i; break; }
		}
	}
#ifdef RAIL_OVERLAY
	if (railSlot < 0) {
		o.culled = true; // the overlay draws rail members only
	} else {
		o.railMember = true;
		// staggered per slot (ball 1 leads) so the over lifts as a wave; the ramp
		// is over-driven so the last ball still completes at progress 1
		float rt = clamp(uRailProgress * 1.25 - float(railSlot) * RAIL_STAGGER_W, 0.0, 1.0);
		rt = rt * rt * (3.0 - 2.0 * rt);
		vec2 sfrac = uRailSlot[railSlot];
		vec3 posSlot = vec3((sfrac.x * 2.0 - 1.0) * uHalfW, (1.0 - sfrac.y * 2.0) * uHalfH, 0.45);
		pos = mix(pos, posSlot, rt);
		pos.y += 4.0 * rt * (1.0 - rt) * uRailLift;
		o.railT = rt;
	}
#else
	if (railSlot >= 0) {
		o.railMember = true;
		o.culled = true; // the overlay draw owns this ball while the rail is engaged
	}
#endif

	o.reAmt = resortOn ? clamp(uResortEngage, 0.0, 1.0) : 0.0;
	o.filterPass = passesFilter(gi);
	o.pos = pos;
	return o;
}
`;
}

export function makeVertexShader(
	groupCount: number,
	teamCount: number,
	hasMatch = false,
	railOverlay = false
): string {
	return /* glsl */ `
#define GROUP_COUNT ${groupCount}
#define TEAM_COUNT ${Math.max(1, teamCount)}
#define RAIN_W ${ASSEMBLY_RAIN_WINDOW}
#define WALLHEAT_NEUTRAL ${(WALLHEAT_NEUTRAL_BYTE / 255).toFixed(6)}
#define CASCADE_FLASH_W ${CASCADE_FLASH_WINDOW.toFixed(6)}
#define WORM_HAZE_ALPHA ${WORM_HAZE_ALPHA.toFixed(6)}
#define TIDE_RESERVOIR_A ${TIDE_RESERVOIR_ALPHA.toFixed(6)}
#define WORTH_CELL_FILL ${WORTH_CELL_FILL.toFixed(6)}
#define RAIL_MAX ${RAIL_MAX_SLOTS}
#define RAIL_STAGGER_W ${RAIL_STAGGER.toFixed(6)}
#define FLOW_RIBBON_A ${FLOW_RIBBON_ALPHA.toFixed(6)}
#define MATCHDOTS_ALPHA ${MATCHDOTS_ALPHA.toFixed(6)}
#define DUELWEB_ALPHA ${DUELWEB_ALPHA.toFixed(6)}
${hasMatch ? '#define HAS_MATCH' : ''}
${railOverlay ? '#define RAIL_OVERLAY' : ''}

${UNIFORMS_GLSL}
${coreAttrsGlsl(hasMatch)}
in float aWallHeat;           // era-relative intent 0..1 (normalized u8; neutral = 73/255)

out vec3 vColor;
out float vGlow;
out float vAlpha;

const vec3 C_DOT   = vec3(0.227, 0.263, 0.345); // #3a4358
const vec3 C_ONE   = vec3(0.420, 0.478, 0.600); // #6b7a99
const vec3 C_TWO   = vec3(0.490, 0.561, 0.690); // #7d8fb0
const vec3 C_FOUR  = vec3(0.910, 0.639, 0.239); // #e8a33d
const vec3 C_SIX   = vec3(1.000, 0.365, 0.227); // #ff5d3a
const vec3 C_WKT   = vec3(0.851, 0.310, 0.420); // #d94f6b
const vec3 C_XTRA  = vec3(0.333, 0.392, 0.498); // #55647f
const vec3 C_TEAL  = vec3(0.180, 0.769, 0.714); // #2ec4b6
// run-out cascade flash (C2-4): brighter + more saturated than ANY team red so
// a red-team reader never mistakes "my team" for "a run-out"; luminance-distinct
// from the dark haze so the signal reads on luminance, not hue alone (§0.1).
const vec3 C_CASCADE_RED = vec3(1.0, 0.145, 0.115); // #ff251d

// dismissal-rivers categorical palette (C3-4, the ONE gated hue exception in Ch
// 3): luminance-distinct, brighter than any team red, and none is the WPL teal.
// bowled + lbw SHARE the "stumps" amber (the woodwork group); caught (the big
// band) a calm blue; stumped (the thin sliver) a vivid magenta so it still reads.
// Owner-tunable (storyboard §7c) — the exact hues are the remaining sign-off.
const vec3 C_RIVER_STUMPS  = vec3(1.000, 0.690, 0.180); // #ffb02e — bowled + lbw
const vec3 C_RIVER_CAUGHT  = vec3(0.357, 0.549, 1.000); // #5b8cff — caught
const vec3 C_RIVER_STUMPED = vec3(0.878, 0.373, 0.847); // #e05fd8 — stumped

// review-chip outcome palette (C8-4, the ONE gated hue exception in Ch 8, §25). The
// CVD-safe gate: the two bands MUST separate by LUMINANCE, not hue alone, so "mostly
// dark = mostly the call stood" survives red-green colorblindness. C_REVIEW_GREEN is
// the LIGHTER band (the review paid off / upheld, lum ≈ 0.83) and C_REVIEW_RED the
// DARKER band (the call stood / struck down, lum ≈ 0.52). The review-red is held
// luminance-distinct from and brighter than every team identity red (so a red-franchise
// reader never confuses "my team" with "struck down"), and the green is held off the
// WPL teal. Owner-tunable (storyboard §7) — the exact hues are the remaining sign-off.
const vec3 C_REVIEW_GREEN = vec3(0.659, 0.925, 0.753); // #a8ecc0 — upheld / paid off (LIGHTER)
const vec3 C_REVIEW_RED   = vec3(0.937, 0.353, 0.267); // #ef5a44 — struck down / call stood (DARKER)

// duel-web dominance palette (C9, §26): a DIVERGING bowler-blue (-1) · neutral (0) ·
// batter-red (+1) ramp for "who came out on top". Deliberately red-vs-blue (not
// red-vs-green) so the read survives red-green colorblindness; a near-even (EB-shrunk)
// duel stays pale near the neutral gray. Mirrors dominanceColor() in the ch9 scene so
// the GL clusters and the SVG strands share one palette. C_DUEL_RECEDE is the neutral
// low luminance non-focus knots sink toward under strandRecede.
const vec3 C_DUEL_RED     = vec3(1.000, 0.416, 0.302); // #ff6a4d — batter came out on top
const vec3 C_DUEL_BLUE    = vec3(0.290, 0.639, 1.000); // #4aa3ff — bowler came out on top
const vec3 C_DUEL_NEUTRAL = vec3(0.592, 0.631, 0.722); // #97a1b8 — an even fight (pale)
const vec3 C_DUEL_RECEDE  = vec3(0.235, 0.259, 0.325); // #3c4253 — receded non-focus knot

${coreBodyGlsl()}

// Era-relative "intent" ramp for the C1-2 thesis beat (blended by uWallHeatMix).
// DIVERGING about WALLHEAT_NEUTRAL (= the 2008-2010 batter): cool deep-blue
// below, neutral grey-blue at it, amber → six-red well above. Reuses the
// outcome palette; the ONE authored place hue encodes a quantity, gated to the beat.
vec3 heatColor(float h) {
	if (h <= WALLHEAT_NEUTRAL) {
		float t = clamp(h / WALLHEAT_NEUTRAL, 0.0, 1.0);
		return mix(C_DOT, C_TWO, t);
	}
	float t = (h - WALLHEAT_NEUTRAL) / (1.0 - WALLHEAT_NEUTRAL);
	if (t < 0.5) return mix(C_TWO, C_FOUR, t / 0.5);
	return mix(C_FOUR, C_SIX, clamp((t - 0.5) / 0.5, 0.0, 1.0));
}

// Pricelens texel for a worth-grid cell (§19): R = the cell's price LUMINANCE
// (0..1, from the scene's table), G = the cell's DENSITY GAIN (client-derived
// from the cell's point count so INTEGRATED brightness tracks the price). Rows
// A and B mix by uWorthMix — the C5-6a era flip is exactly this lerp. A row of
// -1 reads as the neutral ramp (lum 1, gain 1).
vec2 worthLumGain(float cell) {
	int cx = int(cell + 0.5);
	vec2 a = uWorthRowA >= 0 ? texelFetch(uWorthTex, ivec2(cx, uWorthRowA), 0).rg : vec2(1.0);
	vec2 b = uWorthRowB >= 0 ? texelFetch(uWorthTex, ivec2(cx, uWorthRowB), 0).rg : vec2(1.0);
	return mix(a, b, clamp(uWorthMix, 0.0, 1.0));
}

void main() {
	Core core = computeCore();

	// assembly: not yet bowled into the field — cull before rasterization
	if (core.culled) {
		vColor = vec3(0.0);
		vGlow = 0.0;
		vAlpha = 0.0;
		gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
		gl_PointSize = 0.0;
		return;
	}

	vec3 pos = core.pos;
	float alphaMul = core.assemblyAlpha;
	int outcome = core.outcome;
	bool wicket = core.wicket;
	bool wpl = core.wpl;
	float sizeMul = core.baseSizeMul;

	// ---- Color from the outcome class.
	vec3 c;
	float glow = 0.0;
	if (wicket)            { c = C_WKT; }
	else if (outcome == 0) { c = C_DOT; }
	else if (outcome == 1) { c = C_ONE; }
	else if (outcome == 2) { c = C_TWO; }
	else if (outcome == 3) { c = C_FOUR; }
	else if (outcome == 4) { c = C_SIX; glow = 1.0; }
	else                   { c = C_XTRA; }

	// WPL points shift toward the cool teal family — two populations.
	if (wpl) {
		float k = (outcome == 3 || outcome == 4) && !wicket ? 0.32 : 0.5;
		c = mix(c, C_TEAL, k);
	}

	// ---- Match-dots flatten (§24): a match dot must read at a CONSTANT radius and
	//      brightness, so a boundary-heavy match is no bigger or brighter than a
	//      low-scoring one (design gate). Fade the outcome size boost + the six/four
	//      glow toward neutral by matchWeight; HUE stays identity. Team-ignite runs
	//      LATER, so the reader's own team still pops. No-op off the matchdots layout
	//      (matchWeight 0 → mix is identity), so every prior scene is byte-identical.
	sizeMul = mix(sizeMul, 1.0, core.matchWeight);
	glow *= mix(1.0, 0.0, core.matchWeight);

	// ---- Era-relative intent recolor (C1-2 thesis beat), gated by uWallHeatMix.
	if (uWallHeatMix > 0.0) {
		c = mix(c, heatColor(aWallHeat), uWallHeatMix);
	}

	// ---- Subset highlight color (the pos.y lift already happened in core).
	if (uHlClass >= 0.0) {
		if (core.hlMatch) {
			c *= 1.0 + uHlBoost;
			sizeMul *= 1.0 + 0.35 * uHlBoost;
			glow = max(glow, uHlBoost * 0.5);
		} else {
			alphaMul *= uOthersDim;
			c *= mix(0.8, 1.0, uOthersDim);
		}
	}

	// ---- Subset re-sort recolor (two-tone LUMINANCE split, weighted by engage).
	if (uResortClass >= 0.0) {
		float reAmt = core.reAmt;
		if (core.matchResort) {
			float tone = mix(1.0, core.top10 ? 1.4 : 0.5, uResortTint);
			c *= mix(1.0, tone, reAmt);
			glow = max(glow, 0.4 * reAmt);
			sizeMul *= 1.0 + 0.15 * reAmt;
		} else {
			float od = mix(1.0, uResortOthersDim, reAmt);
			alphaMul *= od;
			c *= mix(0.75, 1.0, od);
		}
	}

	// ---- Rail-overlay resistance (§20): a LIFTED hero ball reads as THE
	//      OBJECT, not as its cell's price or the scene's mood — as railT → 1
	//      it resists the scene dim and the pricelens luminance/density gain
	//      (mirrors the team ignite's worth resistance). Compiled ONLY into
	//      the overlay pass; railKeep is constant 0.0 in the main pass, so
	//      every prior scene renders byte-identically.
#ifdef RAIL_OVERLAY
	float railKeep = core.railT;
#else
	float railKeep = 0.0;
#endif

	// ---- Dims are luminance-only (hue is identity, never quantity).
	c *= mix(uDim, 1.0, railKeep);
	if (wpl) c *= uWplDim;

	// ---- Worm-space density haze (§13): the field settles to low alpha so
	//      overlapping balls read as texture/density, not a solid fill. No-op
	//      outside worm-space (wormWeight is 0 for every R1 layout).
	alphaMul *= mix(1.0, WORM_HAZE_ALPHA, core.wormWeight);

	// ---- Twin-rivers ribbon alpha (§23): the two rivers settle to a moderate
	//      alpha so each dense band reads as a bright ribbon of texture, not a
	//      saturated blob. No-op outside the flow layout (flowWeight is 0 for every
	//      prior layout, never code 9), so R1..R6 render byte-identically.
	alphaMul *= mix(1.0, FLOW_RIBBON_A, core.flowWeight);

	// ---- Match-dots settle (§24): the 316k balls collapse into 1,331 discs, so a
	//      moderate base alpha (MATCHDOTS_ALPHA) lets each read as a soft disc, and the
	//      per-match DENSITY GAIN (uMatchTex.w, in core.matchGain) makes a dot's
	//      INTEGRATED brightness independent of the match's ball count — a longer / rain-
	//      shortened match is no dimmer or brighter than a full one (the design gate).
	//      No-op outside the matchdots layout (matchWeight 0), so R0..R7 are byte-identical.
	alphaMul *= mix(1.0, MATCHDOTS_ALPHA * core.matchGain, core.matchWeight);

	// ---- Duel web (§26): the rivalry web. Gated on the duelweb layout being in the
	//      mix (duelWeight 0 for every prior layout → every branch below is a no-op and
	//      R0..R8 render byte-identically). HUE stays identity until uDuelDominance > 0.
	if (core.duelWeight > 0.0) {
		float dw = core.duelWeight;
		if (core.duelDust) {
			// dust: the ~236k balls in no tracked pairing sink so the strands pop.
			alphaMul *= mix(1.0, uDuelDustDim, dw);
		} else {
			// dominance hue: a diverging bowler-blue (-1) · neutral (0) · batter-red (+1)
			// ramp, mixed in by uDuelDominance so a strand reads WHO came out on top. A
			// near-even (EB-shrunk) duel stays pale near the neutral gray.
			float dc = clamp(core.duelColor, -1.0, 1.0);
			vec3 pole = dc >= 0.0 ? C_DUEL_RED : C_DUEL_BLUE;
			vec3 domC = mix(C_DUEL_NEUTRAL, pole, abs(dc));
			c = mix(c, domC, uDuelDominance * dw);
			// strand recede: non-focus knots (uDuelFocusTex < 1, written by setDuelFocus)
			// sink toward a neutral low luminance so only the focused strand(s) stay lit.
			c = mix(c, C_DUEL_RECEDE, uStrandRecede * (1.0 - core.duelFocus) * dw);
			// web draw: strand points fade in as uDuelReveal rises (0 → 1).
			alphaMul *= mix(1.0, uDuelReveal, dw);
		}
		// settle alpha: the 316k balls collapse into ~1,691 clusters, so a moderate base
		// alpha lets each strand read as a soft band rather than a blown-out blob.
		alphaMul *= mix(1.0, DUELWEB_ALPHA, dw);
	}

	// ---- Worth-grid pricelens (§19): the cell's price LUMINANCE rides the
	//      color (hue stays identity — a scalar multiply is luminance only) and
	//      the DENSITY GAIN rides the alpha, so a cell's INTEGRATED brightness
	//      tracks the active price table, never its point count (§0.1 binding).
	//      Gated on the worth layout being in the mix — a no-op for every prior
	//      layout (worthWeight is 0, never code 7).
	if (core.worthWeight > 0.0) {
		vec2 pw = worthLumGain(core.worthCell);
		float ww = core.worthWeight * (1.0 - railKeep);
		c *= mix(1.0, pw.x, ww);
		alphaMul *= mix(1.0, pw.y, ww);
	}

	// ---- Tide reservoir + waterline drown (§18). No-op unless the tide layout is
	//      in the mix (tideWeight > 0), so R1/R2 render byte-identically. First-
	//      innings columns carry full alpha; non-first-innings balls damp to the
	//      reservoir haze; a first-innings column whose innings total sits below
	//      the going rate (uWaterLevel, runs) DROWNS on LUMINANCE only (never hue).
	if (core.tideWeight > 0.0) {
		bool tideTeam = uPickedTeam >= 0.0 && abs(aTeam - uPickedTeam) < 0.5;
		if (!core.tideFirst) {
			alphaMul *= mix(1.0, TIDE_RESERVOIR_A, core.tideWeight);
			c *= mix(1.0, 0.7, core.tideWeight);
		} else if (uWaterLevel >= 0.0 && core.tideTotal < uWaterLevel &&
		           !(tideTeam && uWaterTeamKeep > 0.5)) {
			float drown = mix(1.0, uWaterDrownDim, core.tideWeight);
			alphaMul *= drown;
			c *= mix(0.55, 1.0, drown);
		}
	}

	// ---- Run-out cascade (§14): fade the fallen cohort, then the beat-gated red
	//      flash overrides the haze so the danger/loss signal reads on luminance.
	if (uCascadeClass >= 0.0 && core.runOut) {
		alphaMul *= mix(1.0, uCascadeFade, core.cascadeFall);
		float flash = core.cascadeFlash * uCascadeTint;
		if (flash > 0.0) {
			c = mix(c, C_CASCADE_RED, flash);
			glow = max(glow, flash * 0.85);
			alphaMul = max(alphaMul, flash * 0.9);
			sizeMul *= 1.0 + 0.35 * flash;
		}
	}

	// ---- Dismissal rivers recolor (§16): the bowler-credited wicket subset
	//      recolours categorically by dismissal kind (the ONE gated hue exception
	//      in Ch 3), everything else dims. The pos fly-out already happened in
	//      core; this is the colour half (visual only). No-op when uRiversClass < 0.
	if (uRiversClass >= 0.0) {
		if (core.riverMember) {
			int dk = int(aDismissal + 0.5);
			vec3 rc = C_RIVER_STUMPS;               // bowled (0) + lbw (1) share the stumps hue
			if (dk == 2) rc = C_RIVER_CAUGHT;       // caught
			else if (dk == 3) rc = C_RIVER_STUMPED; // stumped
			c = mix(c, rc, uRiversTint * core.riverEngage);
			glow = max(glow, 0.4 * core.riverEngage);
			sizeMul *= 1.0 + 0.1 * core.riverEngage;
		} else {
			float od = mix(1.0, uRiversOthersDim, core.riverEngage);
			alphaMul *= od;
			c *= mix(0.75, 1.0, od);
		}
	}

	// ---- Review chips recolor (§25): the review subset recolours by OUTCOME — a
	//      LIGHTER green (the review paid off / upheld, aDismissal 1) vs a DARKER red
	//      (the call stood / struck down, aDismissal 0), separated by LUMINANCE not hue
	//      alone so "mostly dark = mostly the call stood" survives red-green colorblindness
	//      (the CVD-safe gate). Everything else dims. The fly-out already happened in core;
	//      the tick/cross micro-glyphs are the scene's SVG. No-op when uReviewClass < 0.
	if (uReviewClass >= 0.0) {
		float re = clamp(uReviewEngage, 0.0, 1.0);
		if (core.reviewMember) {
			vec3 rc = (aDismissal > 0.5) ? C_REVIEW_GREEN : C_REVIEW_RED;
			c = mix(c, rc, uReviewTint * re);
			glow = max(glow, 0.25 * re);
		} else {
			float od = mix(1.0, uReviewOthersDim, re);
			alphaMul *= od;
			c *= mix(0.75, 1.0, od);
		}
	}

	// ---- Impact-sub sparks (§23): the 517 impact-sub deliveries glow as bright
	//      sparks entering the IPL river — a LUMINANCE boost + glow + size (hue
	//      stays identity), with non-spark points optionally damped (uSparkOthersDim)
	//      so the sparks pop. The pos lift already happened in core. No-op at
	//      uSparkGlow == 0, so every prior scene renders byte-identically.
	if (uSparkGlow > 0.0) {
		if (core.spark) {
			c *= 1.0 + 0.9 * uSparkGlow;
			glow = max(glow, 0.7 * uSparkGlow);
			sizeMul *= 1.0 + 0.5 * uSparkGlow;
			alphaMul = max(alphaMul, 0.9 * uSparkGlow);
		} else {
			float od = mix(1.0, uSparkOthersDim, uSparkGlow);
			alphaMul *= od;
			c *= mix(0.8, 1.0, od);
		}
	}

	// ---- Facet filter: points failing an active facet are hidden/ghosted.
	//      (uFilterDim is 0 to hide, small to ghost, 1 no-op — and is a no-op
	//      whenever no facet is active because filterPass is then always true.)
	if (!core.filterPass) {
		alphaMul *= uFilterDim;
		c *= mix(0.5, 1.0, uFilterDim);
	}

	// ---- Over rail (§20): while the rail is engaged the REST of the field dims
	//      hard behind the lifted balls (set-piece dimming, luminance + alpha,
	//      following uRailProgress so the dim rides the lift). Rail members are
	//      culled from this pass and drawn by the overlay. No-op at uRailN == 0.
	if (uRailN > 0 && !core.railMember) {
		float rr = mix(1.0, uRailDim, clamp(uRailProgress, 0.0, 1.0));
		alphaMul *= rr;
		c *= mix(0.8, 1.0, rr);
	}
#ifdef RAIL_OVERLAY
	// the overlay's hero balls enlarge toward uRailScale and pick up a glow as
	// they arrive at their slots (the DOM chip takes over the names/numbers)
	sizeMul *= mix(1.0, uRailScale, core.railT);
	glow = max(glow, 0.45 * core.railT);
#endif

	// ---- Team ignite: the reader's franchise renders in team color and resists
	//      the dims AND the worm-space haze — personalization survives (C2-8).
	if (uPickedTeam >= 0.0 && abs(aTeam - uPickedTeam) < 0.5) {
		vec3 tcol = uTeamColor;
		float igniteK = 0.82;
		float glowK = 0.35;
		// through the run-out cascade (C2-4) OR the dismissal rivers (C3-4) the team
		// glow desaturates one stop so a red-team reader (RCB/PBKS/SRH) never
		// confuses identity with a run-out or a caught/stumped tint. Gated on the
		// beat being ACTIVE so a picked team in R1/R2a-hold is untouched.
		float muteAmt = 0.0;
		if (uCascadeClass >= 0.0) muteAmt = max(muteAmt, uCascadeMute);
		if (uRiversClass >= 0.0) muteAmt = max(muteAmt, uRiversMute);
		// through the review chips (C8-4) the team glow desaturates so a red-franchise
		// reader (RCB / PBKS / SRH) never confuses their own lit lane with a struck-down
		// (red) chip; the mute rises with the chip engage. Gated on the beat being active.
		if (uReviewClass >= 0.0) muteAmt = max(muteAmt, uReviewEngage);
		if (muteAmt > 0.0) {
			float m = clamp(muteAmt, 0.0, 1.0);
			float lum = dot(tcol, vec3(0.299, 0.587, 0.114));
			tcol = mix(tcol, vec3(lum), 0.5 * m);
			igniteK = mix(0.82, 0.55, m);
			glowK = mix(0.35, 0.18, m);
		}
		c = mix(c, tcol, igniteK);
		sizeMul *= 1.25;
		glow = max(glow, glowK);
		// resist the haze so the reader's team reads at full brightness in worm-space
		alphaMul = max(alphaMul, mix(alphaMul, 0.82, core.wormWeight));
		// resist the twin-rivers ribbon alpha a stop so the reader's team glows inside
		// its own river (an IPL team in the men's river, a WPL team in the women's) —
		// personalization survives the most abstract Ch 7 layout (standing rule)
		alphaMul = max(alphaMul, mix(alphaMul, 0.82, core.flowWeight));
		// resist the worth density gain a stop so the reader's team stays readable
		// on the price map (personalization survives — standing rule)
		alphaMul = max(alphaMul, mix(alphaMul, 0.55, core.worthWeight));
	}

	vColor = c;
	vGlow = glow;
	vAlpha = 0.85 * alphaMul;

	gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
	gl_PointSize = uPointScale * sizeMul;
}
`;
}

export const fragmentShader = /* glsl */ `
precision mediump float;

in vec3 vColor;
in float vGlow;
in float vAlpha;

out vec4 fragColor;

void main() {
	vec2 uv = gl_PointCoord - 0.5;
	float d = length(uv);
	// round sprite, soft edge
	float core = 1.0 - smoothstep(0.30, 0.5, d);
	float alpha = core * vAlpha;
	vec3 col = vColor;
	// subtle additive-feel glow: hot centre + soft halo
	if (vGlow > 0.05) {
		float halo = 1.0 - smoothstep(0.0, 0.5, d);
		halo *= halo;
		col += col * halo * (0.9 * vGlow);
		alpha = max(alpha, halo * 0.55 * vGlow * (vAlpha > 0.0 ? 1.0 : 0.0));
	}
	if (alpha < 0.02) discard;
	fragColor = vec4(col, alpha);
}
`;

/* ---------------------------------------------------------------------------
 * GPU picking (R1b §11). The pick vertex shader shares `computeCore()` so a
 * point sits at the exact same place it does visually and is culled when it is
 * filtered out (never pickable) or not yet assembled. The fragment writes the
 * point index encoded as 24-bit RGB (index+1, so 0 reads back as "no point").
 * Points render as SOLID squares (no round mask) so even 1-2px points paint a
 * pixel; the readback scans outward from the tap for the nearest painted pixel
 * (the pick radius). Rendered on demand to a tiny offscreen target — one render
 * + one readback per tap, never a loop (idle GPU stays ~0).
 * ------------------------------------------------------------------------- */

export function makePickVertexShader(groupCount: number, teamCount: number, hasMatch = false): string {
	return /* glsl */ `
#define GROUP_COUNT ${groupCount}
#define TEAM_COUNT ${Math.max(1, teamCount)}
#define RAIN_W ${ASSEMBLY_RAIN_WINDOW}
#define CASCADE_FLASH_W ${CASCADE_FLASH_WINDOW.toFixed(6)}
#define WORTH_CELL_FILL ${WORTH_CELL_FILL.toFixed(6)}
#define RAIL_MAX ${RAIL_MAX_SLOTS}
#define RAIL_STAGGER_W ${RAIL_STAGGER.toFixed(6)}
#define MATCHDOTS_ALPHA ${MATCHDOTS_ALPHA.toFixed(6)}
#define DUELWEB_ALPHA ${DUELWEB_ALPHA.toFixed(6)}
${hasMatch ? '#define HAS_MATCH' : ''}

${UNIFORMS_GLSL}
${coreAttrsGlsl(hasMatch)}

out highp vec3 vPickColor;

${coreBodyGlsl()}

void main() {
	Core core = computeCore();

	// Filtered-out or not-yet-assembled points are NOT pickable → cull offscreen.
	if (core.culled || !core.filterPass) {
		gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
		gl_PointSize = 0.0;
		vPickColor = vec3(0.0);
		return;
	}

	// Encode (index + 1) into 24-bit RGB; 0 is reserved for the background.
	float id1 = position.x + 1.0;
	float r = mod(id1, 256.0);
	float g = mod(floor(id1 / 256.0), 256.0);
	float b = mod(floor(id1 / 65536.0), 256.0);
	vPickColor = vec3(r, g, b) / 255.0;

	gl_Position = projectionMatrix * modelViewMatrix * vec4(core.pos, 1.0);
	// inflate small points a touch so each reliably paints ≥1px in the pick patch
	gl_PointSize = uPointScale * max(core.baseSizeMul, 1.6);
}
`;
}

export const pickFragmentShader = /* glsl */ `
precision highp float;

in highp vec3 vPickColor;

out vec4 fragColor;

void main() {
	// solid square (no round mask) → maximal hit area; exact index bytes out
	fragColor = vec4(vPickColor, 1.0);
}
`;
