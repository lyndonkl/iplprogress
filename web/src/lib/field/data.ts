import type { FieldData, GroupMeta, MetaJson, TeamMeta } from './types';

/**
 * Loads the pipeline contract files (R0 set + the R1a per-point attributes —
 * all inside the ledger's pre-assembly budget; see static/data/ledger.json).
 * If any file is missing or inconsistent:
 *  - dev builds fall back to a synthetic 316,388-point field (flagged loudly in
 *    the console) so scenes can be developed while the pipeline runs in parallel;
 *  - production builds throw, and the page shows an integration error overlay.
 */
export async function loadFieldData(baseUrl: string): Promise<FieldData> {
	try {
		const [meta, groups, teams, gidBuf, attrBuf, bfBuf, teamBuf, heatBuf] = await Promise.all([
			fetchJson<MetaJson>(`${baseUrl}/data/meta.json`),
			fetchJson<GroupMeta[]>(`${baseUrl}/data/groups.json`),
			fetchJson<TeamMeta[]>(`${baseUrl}/data/teams.json`),
			fetchBuffer(`${baseUrl}/data/group_ids.u16`),
			fetchBuffer(`${baseUrl}/data/attrs.u8`),
			fetchBuffer(`${baseUrl}/data/ballsfaced.u8`),
			fetchBuffer(`${baseUrl}/data/team.u8`),
			fetchBuffer(`${baseUrl}/data/wallheat.u8`)
		]);

		const n = meta.n_points;
		if (!Number.isInteger(n) || n <= 0) throw new Error(`meta.json n_points invalid: ${n}`);
		if (gidBuf.byteLength !== n * 2)
			throw new Error(`group_ids.u16 byteLength ${gidBuf.byteLength} ≠ 2 × n_points (${n})`);
		if (attrBuf.byteLength !== n)
			throw new Error(`attrs.u8 byteLength ${attrBuf.byteLength} ≠ n_points (${n})`);
		if (bfBuf.byteLength !== n)
			throw new Error(`ballsfaced.u8 byteLength ${bfBuf.byteLength} ≠ n_points (${n})`);
		if (teamBuf.byteLength !== n)
			throw new Error(`team.u8 byteLength ${teamBuf.byteLength} ≠ n_points (${n})`);
		if (heatBuf.byteLength !== n)
			throw new Error(`wallheat.u8 byteLength ${heatBuf.byteLength} ≠ n_points (${n})`);
		if (!Array.isArray(groups) || groups.length === 0) throw new Error('groups.json empty');
		if (!Array.isArray(teams) || teams.length === 0) throw new Error('teams.json empty');
		const counted = groups.reduce((s, g) => s + g.count, 0);
		if (counted !== n) throw new Error(`groups.json counts sum ${counted} ≠ n_points (${n})`);

		// group_ids.u16 is little-endian on the wire; every platform we target is
		// little-endian, but decode defensively anyway.
		const groupIds = decodeU16LE(gidBuf);

		// OPTIONAL per-point match index (R1b §12): enables the uFilterMatch facet
		// and the exact-match tooltip. Absent until the pipeline ships it — fetch
		// non-fatally so R1a and the range-based match preset keep working.
		const matchIndex = await fetchOptionalU16(`${baseUrl}/data/match_index.u16`, n);

		return {
			nPoints: n,
			meta,
			groups,
			teams,
			groupIds,
			attrs: new Uint8Array(attrBuf),
			ballsFaced: new Uint8Array(bfBuf),
			team: new Uint8Array(teamBuf),
			wallHeat: new Uint8Array(heatBuf),
			matchIndex,
			synthetic: false
		};
	} catch (err) {
		if (import.meta.env.DEV) {
			console.warn(
				'%c[every-ball-ever] SYNTHETIC FALLBACK (dev only)',
				'color:#ff5d3a;font-weight:bold',
				'— real /data files missing or invalid; generating a fake 316,388-point field.',
				err
			);
			// Dev-only dynamic import: in production this branch is statically dead
			// (import.meta.env.DEV === false), so the synthetic module is never
			// bundled and the fallback path cannot ship.
			const { syntheticFieldData } = await import('./synthetic');
			return syntheticFieldData();
		}
		throw err;
	}
}

async function fetchJson<T>(url: string): Promise<T> {
	const res = await fetch(url);
	if (!res.ok) throw new Error(`${url} → HTTP ${res.status}`);
	return (await res.json()) as T;
}

async function fetchBuffer(url: string): Promise<ArrayBuffer> {
	const res = await fetch(url);
	if (!res.ok) throw new Error(`${url} → HTTP ${res.status}`);
	const type = res.headers.get('content-type') ?? '';
	if (type.includes('text/html')) throw new Error(`${url} → served HTML, not binary`);
	return res.arrayBuffer();
}

/**
 * Fetch an OPTIONAL little-endian Uint16 buffer of exactly `n` entries. Returns
 * undefined (never throws) when the file is missing or the wrong size — the
 * caller treats absence as "facet unavailable", so a not-yet-shipped pipeline
 * artifact degrades gracefully rather than breaking the whole field.
 */
async function fetchOptionalU16(url: string, n: number): Promise<Uint16Array | undefined> {
	try {
		const res = await fetch(url);
		if (!res.ok) return undefined;
		const type = res.headers.get('content-type') ?? '';
		if (type.includes('text/html')) return undefined; // dev server 404 → index.html
		const buf = await res.arrayBuffer();
		if (buf.byteLength !== n * 2) {
			if (import.meta.env.DEV)
				console.warn(`[every-ball-ever] ${url}: byteLength ${buf.byteLength} ≠ 2×${n} — ignoring`);
			return undefined;
		}
		return decodeU16LE(buf);
	} catch {
		return undefined;
	}
}

function decodeU16LE(buf: ArrayBuffer): Uint16Array {
	const probe = new Uint8Array(new Uint16Array([0x0102]).buffer);
	if (probe[0] === 0x02) return new Uint16Array(buf); // little-endian host: zero-copy
	const dv = new DataView(buf);
	const out = new Uint16Array(buf.byteLength / 2);
	for (let i = 0; i < out.length; i++) out[i] = dv.getUint16(i * 2, true);
	return out;
}
