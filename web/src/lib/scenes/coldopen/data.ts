import { base } from '$app/paths';

/**
 * Loader for `scenes/coldopen.json` (pipeline artifact — R1a data contract):
 * per-season 200+ totals for the You-Draw-It truth line, plus the corpus
 * facts the title card quotes (storyboard §1 CO-1..CO-3, §9 verified-number
 * index). Fetched once and cached; on fetch failure the storyboard §9
 * verified-number constants are the sanctioned fallback so the cold open
 * never renders an untraceable figure.
 */

export interface ColdOpenSeason {
	league: 'ipl' | 'wpl';
	season: number;
	totals200: number;
	matches: number;
	deliveries: number;
}

export interface ColdOpenCorpus {
	points_rendered: number;
	corpus_total: number;
	superover_balls: number;
	matches: number;
	players: number;
	ipl_seasons: number;
	wpl_seasons: number;
}

interface ColdOpenJson {
	corpus: ColdOpenCorpus;
	seasons: ColdOpenSeason[];
}

export interface ColdOpenData {
	corpus: ColdOpenCorpus;
	/** IPL 200+ totals in season order — index 0 is `firstSeason` (2008) */
	iplTotals200: number[];
	firstSeason: number;
	/** false = storyboard §9 fallback constants (artifact fetch failed) */
	fromArtifact: boolean;
}

/** Storyboard §9: pre-drawn 2008–2012 (11,1,9,5,5) + truth 2013–2026. */
const FALLBACK_TOTALS_200 = [11, 1, 9, 5, 5, 4, 9, 7, 6, 10, 15, 11, 13, 9, 18, 37, 41, 52, 65];

const FALLBACK_CORPUS: ColdOpenCorpus = {
	points_rendered: 316199,
	corpus_total: 316388,
	superover_balls: 189,
	matches: 1331,
	players: 938,
	ipl_seasons: 19,
	wpl_seasons: 4
};

let cache: Promise<ColdOpenData> | null = null;

export function loadColdOpenData(): Promise<ColdOpenData> {
	cache ??= fetchColdOpen();
	return cache;
}

async function fetchColdOpen(): Promise<ColdOpenData> {
	try {
		const res = await fetch(`${base}/data/scenes/coldopen.json`);
		if (!res.ok) throw new Error(`coldopen.json → HTTP ${res.status}`);
		const raw = (await res.json()) as ColdOpenJson;
		const ipl = raw.seasons
			.filter((s) => s.league === 'ipl')
			.sort((a, b) => a.season - b.season);
		if (ipl.length === 0) throw new Error('coldopen.json holds no IPL seasons');
		return {
			corpus: raw.corpus,
			iplTotals200: ipl.map((s) => s.totals200),
			firstSeason: ipl[0].season,
			fromArtifact: true
		};
	} catch {
		return {
			corpus: FALLBACK_CORPUS,
			iplTotals200: [...FALLBACK_TOTALS_200],
			firstSeason: 2008,
			fromArtifact: false
		};
	}
}
