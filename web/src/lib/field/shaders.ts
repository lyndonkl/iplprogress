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
 *   aMatchIndex = per-delivery match index (u16, OPTIONAL — only present when
 *                 the pipeline ships match_index.u16; gates the uFilterMatch
 *                 facet + the exact-match tooltip. See CONTRACT §12.4.)
 */

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
uniform vec2 uCols[GROUP_COUNT]; // per-group: (column centre x, wall row centre y)
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
uniform float uResortX[GROUP_COUNT]; // per-group re-sort column centre x (world)
uniform float uPickedTeam;    // ignite: picked-team id (-1 = none)
uniform vec3 uTeamColor;      // picked team's color
uniform float uWallHeatMix;   // 0 = outcome colour · 1 = era-relative heat (C1-2 thesis beat)

// ---- Facet filter (R1b §12). A point is VISIBLE iff it passes every active
//      facet; failing points are hidden/ghosted (uFilterDim) and never pickable.
uniform float uFilterTeam;    // team id to keep, or -1 = team facet inactive
uniform int uFilterSeason;    // season YEAR to keep, or -1 = season facet inactive
uniform int uGroupSeason[GROUP_COUNT]; // gi → season year (season-facet lookup)
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
`;

/** Core per-point attributes (both shaders read these). */
function coreAttrsGlsl(hasMatch: boolean): string {
	return /* glsl */ `
in float aAttrs;
in float aBallsFaced;
in float aTeam;
in float aSubOrd;
in float aCumRuns;  // batter cumulative innings runs, NORMALIZED 0..1 (worm-space y)
in float aRunOut;   // run-out membership flag 0/1 (worm-space cascade)
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

vec3 pickLayout(int id, vec3 pFree, vec3 pCols, vec3 pWall, vec3 pWorms) {
	if (id == 1) return pCols;
	if (id == 2) return pWall;
	if (id == 4) return pWorms;
	return pFree; // 0 free · 3 assembly share the free-field scatter
}

// Facet filter (R1b §12): true iff the point passes every ACTIVE facet.
bool passesFilter(int gi) {
	if (uFilterTeam >= 0.0 && abs(aTeam - uFilterTeam) >= 0.5) return false;
	if (uFilterSeason >= 0 && uGroupSeason[gi] != uFilterSeason) return false;
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
	float wormWeight;    // 0..1 amount of worm-space in the current A/B mix (haze alpha)
	bool runOut;         // run-out membership flag (aRunOut) — cascade subset
	float cascadeFall;   // 0..1 fall progress for this point's season cohort
	float cascadeFlash;  // 0..1 red-flash intensity as the season wave crosses
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
	o.runOut = aRunOut > 0.5;

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
	vec2 col = uCols[gi];
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

	// morph with per-point stagger so the field streams, not teleports
	float delay = h3 * 0.55;
	float t = clamp(uProgress * 1.55 - delay, 0.0, 1.0);
	t = t * t * (3.0 - 2.0 * t);
	vec3 pos = mix(
		pickLayout(uLayoutA, posFree, posCols, posWall, posWorms),
		pickLayout(uLayoutB, posFree, posCols, posWall, posWorms),
		t
	);

	// how much worm-space is in the current mix — drives the density-haze alpha
	// (no-op for R1 layouts, which are never code 4)
	o.wormWeight = (uLayoutA == 4 ? (1.0 - t) : 0.0) + (uLayoutB == 4 ? t : 0.0);

	// subset re-sort flight — matching points arc into their season's column
	if (o.matchResort) {
		float re = clamp(uResortEngage * 1.55 - delay, 0.0, 1.0);
		re = re * re * (3.0 - 2.0 * re);
		vec3 posCol = vec3(
			uResortX[gi] + (h4 * 2.0 - 1.0) * uColHalfWidth,
			uColBottom + (aSubOrd + 0.5 + h2 * 0.6) * uResortInvMax * uColUsableH,
			(h3 - 0.5) * 0.25
		);
		pos = mix(pos, posCol, re);
		pos.y += 4.0 * re * (1.0 - re) * uResortLift;
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

	// subset highlight — the LIFT is position (shared); the color is per-shader
	o.hlMatch = false;
	if (uHlClass >= 0.0) {
		int hc = int(uHlClass + 0.5);
		bool m = (hc == 6) ? o.wicket : (o.outcome == hc);
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
		float seasonPos = clamp((float(uGroupSeason[gi]) - uCascadeMinSeason) * uCascadeInvSpan, 0.0, 1.0);
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

	o.reAmt = resortOn ? clamp(uResortEngage, 0.0, 1.0) : 0.0;
	o.filterPass = passesFilter(gi);
	o.pos = pos;
	return o;
}
`;
}

export function makeVertexShader(groupCount: number, hasMatch = false): string {
	return /* glsl */ `
#define GROUP_COUNT ${groupCount}
#define RAIN_W ${ASSEMBLY_RAIN_WINDOW}
#define WALLHEAT_NEUTRAL ${(WALLHEAT_NEUTRAL_BYTE / 255).toFixed(6)}
#define CASCADE_FLASH_W ${CASCADE_FLASH_WINDOW.toFixed(6)}
#define WORM_HAZE_ALPHA ${WORM_HAZE_ALPHA.toFixed(6)}
${hasMatch ? '#define HAS_MATCH' : ''}

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

	// ---- Dims are luminance-only (hue is identity, never quantity).
	c *= uDim;
	if (wpl) c *= uWplDim;

	// ---- Worm-space density haze (§13): the field settles to low alpha so
	//      overlapping balls read as texture/density, not a solid fill. No-op
	//      outside worm-space (wormWeight is 0 for every R1 layout).
	alphaMul *= mix(1.0, WORM_HAZE_ALPHA, core.wormWeight);

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

	// ---- Facet filter: points failing an active facet are hidden/ghosted.
	//      (uFilterDim is 0 to hide, small to ghost, 1 no-op — and is a no-op
	//      whenever no facet is active because filterPass is then always true.)
	if (!core.filterPass) {
		alphaMul *= uFilterDim;
		c *= mix(0.5, 1.0, uFilterDim);
	}

	// ---- Team ignite: the reader's franchise renders in team color and resists
	//      the dims AND the worm-space haze — personalization survives (C2-8).
	if (uPickedTeam >= 0.0 && abs(aTeam - uPickedTeam) < 0.5) {
		vec3 tcol = uTeamColor;
		float igniteK = 0.82;
		float glowK = 0.35;
		// through the run-out cascade the team glow desaturates one stop so a
		// red-team reader (RCB/PBKS/SRH) never confuses identity with a run-out.
		// Gated on the cascade being ACTIVE so a picked team in R1 is untouched.
		if (uCascadeClass >= 0.0 && uCascadeMute > 0.0) {
			float m = clamp(uCascadeMute, 0.0, 1.0);
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

export function makePickVertexShader(groupCount: number, hasMatch = false): string {
	return /* glsl */ `
#define GROUP_COUNT ${groupCount}
#define RAIN_W ${ASSEMBLY_RAIN_WINDOW}
#define CASCADE_FLASH_W ${CASCADE_FLASH_WINDOW.toFixed(6)}
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
