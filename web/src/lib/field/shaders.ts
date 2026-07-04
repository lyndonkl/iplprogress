/**
 * The morph shader (GLSL ES 3.0 — three r163+ is WebGL2-only). Both layouts
 * are computed IN-SHADER from per-point attributes — no position buffers ever
 * cross the wire (blueprint §2).
 *
 * Attribute packing (ShaderMaterial's built-in `position` vec3 is reused as
 * the per-point record — three floats, all exact integers < 2^24):
 *   position.x = point index (chronological)
 *   position.y = group index gi
 *   position.z = ordinal within group (client-computed in one pass)
 *   aAttrs     = packed outcome byte (bits 0-2 class, bit 3 wicket, bit 4 WPL)
 */

export function makeVertexShader(groupCount: number): string {
	return /* glsl */ `
#define GROUP_COUNT ${groupCount}

uniform float uProgress;      // 0 = free field · 1 = season columns
uniform float uHalfW;         // ortho frustum half-width (world)
uniform float uHalfH;         // ortho frustum half-height (world)
uniform float uPointScale;    // base point size, device px
uniform float uColHalfWidth;  // column body half-width (world)
uniform float uColBottom;     // column base y (world)
uniform float uColUsableH;    // tallest column height (world)
uniform float uInvMaxCount;   // 1 / max group count
uniform vec2 uCols[GROUP_COUNT]; // per-group: (column centre x, unused)

in float aAttrs;

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

void main() {
	float grp = position.y;
	float ord = position.z;

	// four decorrelated hash draws chained from the point index
	uint r1 = pcg(uint(position.x));
	uint r2 = pcg(r1);
	uint r3 = pcg(r2);
	uint r4 = pcg(r3);
	float h1 = float(r1) * INV32;
	float h2 = float(r2) * INV32;
	float h3 = float(r3) * INV32;
	float h4 = float(r4) * INV32;

	// ---- Layout A: the free field — procedural scatter from the index hash,
	//      slight z-jitter for depth on the 2.5D ortho camera.
	vec3 posA = vec3(
		(h1 * 2.0 - 1.0) * uHalfW * 0.95,
		(h2 * 2.0 - 1.0) * uHalfH * 0.92,
		(h3 - 0.5) * 0.8
	);

	// ---- Layout B: season columns — column x from the group centroid table,
	//      stack height from the within-group ordinal, deterministic jitter.
	vec2 col = uCols[int(grp + 0.5)];
	vec3 posB = vec3(
		col.x + (h4 * 2.0 - 1.0) * uColHalfWidth,
		uColBottom + (ord + h2 * 1.5) * uInvMaxCount * uColUsableH,
		(h3 - 0.5) * 0.25
	);

	// ---- Morph with per-point stagger so the field streams, not teleports.
	float delay = h3 * 0.55;
	float t = clamp(uProgress * 1.55 - delay, 0.0, 1.0);
	t = t * t * (3.0 - 2.0 * t);
	vec3 pos = mix(posA, posB, t);

	// ---- Decode the packed attr byte.
	int a = int(aAttrs + 0.5);
	int outcome = a & 7;
	bool wicket = (a & 8) != 0;
	bool wpl = (a & 16) != 0;

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

	vColor = c;
	vGlow = glow;
	vAlpha = 0.85;

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
	// subtle additive-feel glow for sixes: hot centre + soft halo
	if (vGlow > 0.5) {
		float halo = 1.0 - smoothstep(0.0, 0.5, d);
		halo *= halo;
		col += vec3(1.0, 0.42, 0.20) * halo * 0.6;
		alpha = max(alpha, halo * 0.55);
	}
	if (alpha < 0.02) discard;
	fragColor = vec4(col, alpha);
}
`;
