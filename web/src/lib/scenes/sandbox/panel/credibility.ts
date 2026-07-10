import { base } from '$app/paths';

/**
 * THE BOWL credibility layer (R7b, storyboard 9.1 + 9.3): the trust meter and the
 * raw-to-best-guess shrinkage slider for the sandbox leaderboards.
 *
 * Two tiny league-wide artifacts drive it (loaded once, base-path aware, cached):
 *  - engines/stabilization.json: per-stat M, the ball count at which a rate stat is
 *    half signal. The trust meter reads n (balls) vs M; the slider reads M as the
 *    shrinkage prior weight. Batting strike rate M is about 95, economy M about 104.
 *  - engines/truetalent.json: the block params for the batting shrinkage (z for the
 *    80% interval, and the per-league population centre the regression leans on).
 *
 * SUPPRESSIBLE: a fetch or parse failure resolves null, so a missing artifact can
 * never regress the R6b sandbox. When credibility is null the panel renders the
 * plain R6b leaderboards (no trust dots, no slider), byte-identical to before.
 *
 * The sandbox slider is BATTING-ONLY and works in plain strike-rate space (runs per
 * 100 balls), which is exact for a live selection. It regresses each batter's raw
 * selection strike rate toward that batter's own league average strike rate, using
 * the strike-rate stabilization point M as the prior weight. The pipeline SR+ (which
 * needs the per-delivery par mix) is NOT reconstructed client-side; truetalent's
 * per-pid SR+ rows stay on the R7a player card, and the bowler-charged economy stays
 * on the card artifact (the client economy would be byes and legbyes generous).
 */

/* ---- the raw artifact shapes (only the fields the sandbox reads) ---------- */

interface RawStabOverall {
	M: number | null;
	mean: number;
	sigma2: number;
}
interface RawStabEra {
	mean: number;
	n_groups: number;
}
interface RawStabStat {
	overall: RawStabOverall;
	by_era: Record<string, RawStabEra>;
}
interface RawStabFile {
	stats: Record<string, RawStabStat>;
}
interface RawTrueTalentFile {
	z: number;
	M: number;
	sigma2: number;
	pop_mean: Record<string, number>;
}

/* ---- the compact object the panel consumes -------------------------------- */

export interface Credibility {
	batting: {
		/** balls to half-signal for strike rate (about 94.5); trust + shrinkage weight */
		M: number;
		/** ball-level runs-per-ball variance; the 80% CI half-width uses it */
		sigma2: number;
		/** the 0.90 normal quantile (about 1.2816) for a two-sided 80% interval */
		z: number;
		/** per-league average strike rate (runs per 100 balls); the shrinkage centre */
		popMeanSR: { ipl: number; wpl: number };
	};
	bowling: {
		/** balls to half-signal for economy (about 104); the bowler trust dot uses it */
		M: number | null;
	};
}

export type TrustState = 'reliable' | 'firming' | 'noisy';

/**
 * Trust state from the SAMPLE SIZE only, never the numerator (so a big raw tally on
 * few balls still reads noisy). reliable = at or past M; firming = half of M to M;
 * noisy = under half of M. A null M (a stat that never settles at this grouping)
 * holds trust low.
 */
export function trustState(n: number, M: number | null): TrustState {
	if (M == null || !(M > 0)) return 'noisy';
	if (n >= M) return 'reliable';
	if (n >= M / 2) return 'firming';
	return 'noisy';
}

export interface RegressResult {
	/** the shrunken strike-rate point estimate at this lambda */
	point: number;
	/** low edge of the 80% interval */
	lo: number;
	/** high edge of the 80% interval */
	hi: number;
}

/**
 * The empirical-Bayes shrinkage in plain strike-rate units.
 *   point(lambda) = mu + (rawSR - mu) * n / (n + lambda*M)
 *   half(lambda)  = 100 * z * sqrt(sigma2 / (n + lambda*M))
 * lambda 0 returns the raw strike rate (as it happened); lambda 1 is the full
 * best-guess shrink toward the league centre mu. sigma2 is the ball-level runs
 * variance, so the standard error of the shrunken mean is scaled by 100 into
 * strike-rate points. The CI always brackets the point.
 */
export function regressSR(
	rawSR: number,
	n: number,
	mu: number,
	M: number,
	sigma2: number,
	z: number,
	lambda: number
): RegressResult {
	const denom = n + lambda * M;
	if (denom <= 0) return { point: mu, lo: mu, hi: mu };
	const point = mu + (rawSR - mu) * (n / denom);
	const half = 100 * z * Math.sqrt(sigma2 / denom);
	return { point, lo: point - half, hi: point + half };
}

/* ---- lazy, cached, suppressible loader ------------------------------------ */

let credPromise: Promise<Credibility | null> | null = null;

async function fetchJson<T>(url: string): Promise<T> {
	const res = await fetch(url);
	if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
	return (await res.json()) as T;
}

/**
 * Pool the by-era means of one league into a single average strike rate (runs per
 * 100 balls), weighting each era bucket by its group count. Falls back to the given
 * overall strike rate when a league has no era buckets.
 */
function leagueMeanSR(byEra: Record<string, RawStabEra>, prefix: string, fallbackSR: number): number {
	let wsum = 0;
	let w = 0;
	for (const [key, bucket] of Object.entries(byEra)) {
		if (!key.startsWith(prefix)) continue;
		wsum += bucket.mean * bucket.n_groups;
		w += bucket.n_groups;
	}
	return w > 0 ? (wsum / w) * 100 : fallbackSR;
}

/** Load (once) and cache the sandbox credibility params, or null on any failure. */
export function loadCredibility(): Promise<Credibility | null> {
	credPromise ??= (async () => {
		try {
			const [stab, tt] = await Promise.all([
				fetchJson<RawStabFile>(`${base}/data/engines/stabilization.json`),
				fetchJson<RawTrueTalentFile>(`${base}/data/engines/truetalent.json`)
			]);
			const bsr = stab.stats.batting_sr;
			const beco = stab.stats.bowling_economy;
			if (!bsr || !beco) return null;
			const overallSR = bsr.overall.mean * 100;
			return {
				batting: {
					M: bsr.overall.M ?? tt.M,
					sigma2: bsr.overall.sigma2,
					z: tt.z,
					popMeanSR: {
						ipl: leagueMeanSR(bsr.by_era, 'ipl', overallSR),
						wpl: leagueMeanSR(bsr.by_era, 'wpl', overallSR)
					}
				},
				bowling: { M: beco.overall.M }
			};
		} catch {
			return null;
		}
	})();
	return credPromise;
}
