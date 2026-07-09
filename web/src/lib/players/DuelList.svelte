<script lang="ts">
	/**
	 * Panel C - Top Duels (storyboard 9.4). Each row is a diverging bar centred on par:
	 * it leans LEFT toward the batter when the batter dominates, RIGHT toward the bowler
	 * when the bowler dominates. DIRECTION rides side, LENGTH rides magnitude (position
	 * channel, CVD-immune); hue (warm=batter / cool=bowler) is REDUNDANT only and the two
	 * poles are luminance-matched (#e07a5f and #5a9ec4, both L* = 0.306). Three states:
	 * a real edge is filled and leaning; a genuine even is filled, centred, pale; a
	 * too-few-balls duel (EB-pulled to par) is a hollow outline, "too few to call." Ball
	 * count on every row; rows are pre-ranked by balls (no cherry-pick). Each row taps
	 * through to that exact duel in the Bowl.
	 */
	import type { Duel } from './data';

	let {
		duels,
		mu,
		onOpen,
		pending = false
	}: {
		duels: Duel[];
		mu: number;
		onOpen: (oppName: string) => void;
		pending?: boolean;
	} = $props();

	const EVEN = 0.04;
	const MAX_HALF = 46;

	type State = 'edge' | 'even' | 'toofew';
	interface Row {
		duel: Duel;
		state: State;
		side: 'bat' | 'bowl';
		left: number;
		width: number;
	}

	const rows = $derived.by((): Row[] => {
		let maxMag = 1e-6;
		for (const d of duels) if (!d.tooFew) maxMag = Math.max(maxMag, Math.abs(d.dom - mu));
		return duels.map((d): Row => {
			const diff = d.dom - mu;
			const mag = Math.abs(diff);
			const side: 'bat' | 'bowl' = diff >= 0 ? 'bat' : 'bowl';
			let state: State;
			if (d.tooFew) state = 'toofew';
			else if (mag < EVEN) state = 'even';
			else state = 'edge';

			let left: number;
			let width: number;
			if (state === 'edge') {
				const half = Math.max(3, Math.min(MAX_HALF, (mag / maxMag) * MAX_HALF));
				if (side === 'bat') {
					left = 50 - half;
					width = half;
				} else {
					left = 50;
					width = half;
				}
			} else if (state === 'even') {
				left = 47;
				width = 6;
			} else {
				left = 43;
				width = 14;
			}
			return { duel: d, state, side, left, width };
		});
	});
</script>

<div class="duels">
	<p class="orient">
		Each bar leans to whoever won the matchup: left is the batter, right is the bowler. Longer means
		a bigger edge; a hollow bar means too few balls to call.
	</p>
	<ul>
		{#each rows as r (r.duel.oppPid)}
			<li>
				<button class="duel" onclick={() => onOpen(r.duel.oppName)} disabled={pending}>
					<span class="opp">{r.duel.oppName}</span>
					<span class="track" aria-hidden="true">
						<span
							class="bar {r.state} {r.side}"
							style="left:{r.left}%;width:{r.width}%"
						></span>
					</span>
					<span class="figures">
						<span class="balls">{r.duel.balls} balls</span>
						<span class="sub"
							>{r.state === 'toofew'
								? 'too few to call'
								: `${r.duel.runs} runs, ${r.duel.dismissals} out`}</span
						>
					</span>
				</button>
			</li>
		{/each}
	</ul>
</div>

<style>
	.duels {
		margin: 0;
	}
	.orient {
		margin: 0 0 0.6rem;
		font-size: 0.9rem;
		line-height: 1.45;
		color: var(--ink-dim);
	}
	ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}
	.duel {
		display: grid;
		grid-template-columns: minmax(5.5rem, 8rem) 1fr auto;
		align-items: center;
		gap: 0.6rem;
		width: 100%;
		min-height: 44px;
		padding: 0.35rem 0.5rem;
		background: rgba(232, 236, 245, 0.03);
		border: 1px solid rgba(232, 236, 245, 0.06);
		border-radius: 8px;
		color: var(--ink);
		font: inherit;
		text-align: left;
		cursor: pointer;
	}
	.duel:hover:not(:disabled),
	.duel:focus-visible {
		background: rgba(232, 236, 245, 0.07);
		outline: none;
	}
	.duel:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 1px;
	}
	.duel:disabled {
		cursor: progress;
		opacity: 0.75;
	}
	.opp {
		font-size: 0.88rem;
		font-weight: 600;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.track {
		position: relative;
		display: block;
		height: 16px;
		border-radius: 4px;
		background: rgba(232, 236, 245, 0.04);
	}
	.track::before {
		content: '';
		position: absolute;
		left: 50%;
		top: -2px;
		bottom: -2px;
		width: 1px;
		background: var(--ink-dim);
		opacity: 0.5;
	}
	.bar {
		position: absolute;
		top: 3px;
		bottom: 3px;
		border-radius: 3px;
	}
	.bar.edge.bat {
		background: #e07a5f;
	}
	.bar.edge.bowl {
		background: #5a9ec4;
	}
	.bar.even {
		background: rgba(151, 161, 184, 0.55);
	}
	.bar.toofew {
		background: transparent;
		border: 1px dashed var(--ink-dim);
		opacity: 0.7;
	}
	.figures {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		font-variant-numeric: tabular-nums;
	}
	.balls {
		font-size: 0.82rem;
		font-weight: 600;
	}
	.sub {
		font-size: 0.72rem;
		color: var(--ink-dim);
	}
</style>
