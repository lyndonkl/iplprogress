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
 *
 * Cross-cutting uniform-driven states (compose with any layout):
 *   subset highlight — points matching uHlClass lift (uHlLift) and brighten
 *                      (uHlBoost); everything else dims (uOthersDim).
 *                      uHlSkipWpl excludes WPL points from the match (C1-5:
 *                      the WPL's sixes stay on its shelf while the IPL's lift)
 *   subset re-sort   — points matching uResortClass fly from their base layout
 *                      into per-season firework columns as uResortEngage scrubs
 *                      0→1 (x = uResortX[gi] column centre, y stacked by the
 *                      per-point subset ordinal aSubOrd / uResortInvMax),
 *                      arcing up out of the wall (uResortLift) with the SAME
 *                      per-point stagger so object constancy holds; everything
 *                      else dims (uResortOthersDim). A per-point two-tone
 *                      recolor fades in with uResortTint (attrs.u8 bit 5 =
 *                      top-10 specialist → bright, else dim — LUMINANCE only).
 *                      uResortSkipWpl keeps WPL points on the wall. Reversible:
 *                      the settle-back is just uResortEngage lerping 1→0. §7.
 *   team ignite      — points whose aTeam == uPickedTeam render in uTeamColor
 *                      and resist the global dim (personalization survives)
 *   dims             — uDim (whole field) and uWplDim (WPL points only) are
 *                      luminance multipliers: hue never encodes quantity
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
 */

/** Fraction of the reveal range a point spends "raining in" (assembly layout). */
export const ASSEMBLY_RAIN_WINDOW = 0.045;

export function makeVertexShader(groupCount: number): string {
	return /* glsl */ `
#define GROUP_COUNT ${groupCount}
#define RAIN_W ${ASSEMBLY_RAIN_WINDOW}

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
uniform float uPickedTeam;    // picked-team id (-1 = none)
uniform vec3 uTeamColor;      // picked team's color

in float aAttrs;
in float aBallsFaced;
in float aTeam;
in float aSubOrd;

out vec3 vColor;
out float vGlow;
out float vAlpha;

// PCG hash — exact integer path, no float-precision striping at 316k indices.
uint pcg(uint v) {
	uint state = v * 747796405u + 2891336453u;
	uint word = ((state >> ((state >> 28u) + 4u)) ^ state) * 277803737u;
	return (word >> 22u) ^ word;
}

const float INV32 = 1.0 / 4294967296.0;

const vec3 C_DOT   = vec3(0.227, 0.263, 0.345); // #3a4358
const vec3 C_ONE   = vec3(0.420, 0.478, 0.600); // #6b7a99
const vec3 C_TWO   = vec3(0.490, 0.561, 0.690); // #7d8fb0
const vec3 C_FOUR  = vec3(0.910, 0.639, 0.239); // #e8a33d
const vec3 C_SIX   = vec3(1.000, 0.365, 0.227); // #ff5d3a
const vec3 C_WKT   = vec3(0.851, 0.310, 0.420); // #d94f6b
const vec3 C_XTRA  = vec3(0.333, 0.392, 0.498); // #55647f
const vec3 C_TEAL  = vec3(0.180, 0.769, 0.714); // #2ec4b6

vec3 pickLayout(int id, vec3 pFree, vec3 pCols, vec3 pWall) {
	if (id == 1) return pCols;
	if (id == 2) return pWall;
	return pFree; // 0 free · 3 assembly share the free-field scatter
}

void main() {
	float grp = position.y;
	float ord = position.z;
	int gi = int(grp + 0.5);

	// four decorrelated hash draws chained from the point index
	uint r1 = pcg(uint(position.x));
	uint r2 = pcg(r1);
	uint r3 = pcg(r2);
	uint r4 = pcg(r3);
	float h1 = float(r1) * INV32;
	float h2 = float(r2) * INV32;
	float h3 = float(r3) * INV32;
	float h4 = float(r4) * INV32;

	// ---- Decode the packed attr byte (needed by the free layout's WPL
	//      constellation and by the highlight below).
	int a = int(aAttrs + 0.5);
	int outcome = a & 7;
	bool wicket = (a & 8) != 0;
	bool wpl = (a & 16) != 0;
	bool top10 = (a & 32) != 0; // hit by that season's top-10 six-hitter (C1-5 two-tone)

	// ---- Subset re-sort membership (drives both position and color below).
	bool resortOn = uResortClass >= 0.0;
	bool matchResort = false;
	if (resortOn) {
		int rc = int(uResortClass + 0.5);
		matchResort = (rc == 6) ? wicket : (outcome == rc);
		if (matchResort && uResortSkipWpl > 0.5 && wpl) matchResort = false;
	}

	// ---- Layout: the free field — procedural scatter from the index hash,
	//      slight z-jitter for depth on the 2.5D ortho camera. The WPL is its
	//      own constellation in the upper-right sky, deliberately apart — the
	//      IPL cloud fills the sky below a clear gap (storyboard CO-3; the
	//      upper→upper continuity into the C1-2 shelf is authored).
	vec3 posFree;
	if (wpl) {
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

	// ---- Layout: season columns — column x from the group centroid table,
	//      stack height from the within-group ordinal, deterministic jitter.
	vec2 col = uCols[gi];
	vec3 posCols = vec3(
		col.x + (h4 * 2.0 - 1.0) * uColHalfWidth,
		uColBottom + (ord + h2 * 1.5) * uInvMaxCount * uColUsableH,
		(h3 - 0.5) * 0.25
	);

	// ---- Layout: the ignition wall — x from the balls-faced index (capped
	//      30+ bucket at the right edge), y from the season row centre.
	float bf = clamp(aBallsFaced, 1.0, 30.0);
	float cellT = (bf - 1.0) / 29.0;
	vec3 posWall = vec3(
		uWallLeft + cellT * uWallWidth + (h4 * 2.0 - 1.0) * uWallCellHalfW,
		col.y + (h2 * 2.0 - 1.0) * uWallRowHalfH,
		(h3 - 0.5) * 0.25
	);

	// ---- Morph with per-point stagger so the field streams, not teleports.
	float delay = h3 * 0.55;
	float t = clamp(uProgress * 1.55 - delay, 0.0, 1.0);
	t = t * t * (3.0 - 2.0 * t);
	vec3 pos = mix(
		pickLayout(uLayoutA, posFree, posCols, posWall),
		pickLayout(uLayoutB, posFree, posCols, posWall),
		t
	);

	// ---- Subset re-sort: matching points fly from the base layout into their
	//      season's firework column, arcing up on the way. Staggered by the
	//      SAME per-point delay as the layout morph, so every point traces one
	//      continuous path (object constancy); reversible via uResortEngage 1→0.
	if (matchResort) {
		float re = clamp(uResortEngage * 1.55 - delay, 0.0, 1.0);
		re = re * re * (3.0 - 2.0 * re);
		vec3 posCol = vec3(
			uResortX[gi] + (h4 * 2.0 - 1.0) * uColHalfWidth,
			uColBottom + (aSubOrd + 0.5 + h2 * 0.6) * uResortInvMax * uColUsableH,
			(h3 - 0.5) * 0.25
		);
		pos = mix(pos, posCol, re);
		pos.y += 4.0 * re * (1.0 - re) * uResortLift; // lift arc, symmetric both legs
	}

	float alphaMul = 1.0;

	// ---- Assembly stream-in: chronological reveal by point index. A point
	//      is hidden until the reveal frontier reaches it, rains in across
	//      the RAIN_W window, then sits. At uReveal == 1 every point has
	//      landed (frontier maps to 1 + RAIN_W), so morphing assembly→free
	//      afterwards is a no-op on positions.
	if (uLayoutA == 3 || uLayoutB == 3) {
		float ci = position.x * uInvN;
		float d = (uReveal * (1.0 + RAIN_W) - ci) / RAIN_W;
		if (d <= 0.0) {
			// not yet bowled into the field — cull before rasterization
			vColor = vec3(0.0);
			vGlow = 0.0;
			vAlpha = 0.0;
			gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
			gl_PointSize = 0.0;
			return;
		} else if (d < 1.0) {
			float fall = 1.0 - d;
			pos.y += fall * fall * uHalfH * 1.35; // rains in from above
			alphaMul *= d;
		}
	}

	// ---- Color from the outcome class (decoded above).
	vec3 c;
	float glow = 0.0;
	float sizeMul = 1.0;
	if (wicket)             { c = C_WKT;  sizeMul = 1.45; }
	else if (outcome == 0)  { c = C_DOT; }
	else if (outcome == 1)  { c = C_ONE; }
	else if (outcome == 2)  { c = C_TWO; }
	else if (outcome == 3)  { c = C_FOUR; sizeMul = 1.5; }
	else if (outcome == 4)  { c = C_SIX;  sizeMul = 1.9; glow = 1.0; }
	else                    { c = C_XTRA; }

	// WPL points shift toward the cool teal family — two populations.
	if (wpl) {
		float k = (outcome == 3 || outcome == 4) && !wicket ? 0.32 : 0.5;
		c = mix(c, C_TEAL, k);
	}

	// ---- Subset highlight: matching points lift and brighten; others dim.
	//      uHlSkipWpl keeps WPL points out of the subset (they take the
	//      others path instead — C1-5: the WPL's sixes stay on its shelf).
	if (uHlClass >= 0.0) {
		int hc = int(uHlClass + 0.5);
		bool m = (hc == 6) ? wicket : (outcome == hc);
		if (m && uHlSkipWpl > 0.5 && wpl) m = false;
		if (m) {
			pos.y += uHlLift;
			c *= 1.0 + uHlBoost;
			sizeMul *= 1.0 + 0.35 * uHlBoost;
			glow = max(glow, uHlBoost * 0.5);
		} else {
			alphaMul *= uOthersDim;
			c *= mix(0.8, 1.0, uOthersDim);
		}
	}

	// ---- Subset re-sort recolor: matching points brighten as they lift and
	//      carry the two-tone LUMINANCE split (top-10 specialist bright vs rest
	//      dim, within the six-ember hue — never a second hue); everything else
	//      dims hard so the columns read on a cleared stage. Weighted by engage
	//      so it fades in with the flight and back out on the settle.
	if (resortOn) {
		float reAmt = clamp(uResortEngage, 0.0, 1.0);
		if (matchResort) {
			float tone = mix(1.0, top10 ? 1.4 : 0.5, uResortTint);
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

	// ---- Team ignite: the reader's franchise renders in team color and
	//      resists the dims — personalization survives every scene state.
	if (uPickedTeam >= 0.0 && abs(aTeam - uPickedTeam) < 0.5) {
		c = mix(c, uTeamColor, 0.82);
		sizeMul *= 1.25;
		glow = max(glow, 0.35);
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
