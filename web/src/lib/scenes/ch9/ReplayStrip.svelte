<script lang="ts">
	import { isWicket, type Replay } from './data';

	/**
	 * The tap-a-duel replay strip (CONTRACT §26.4 / storyboard §10). Scene-authored
	 * SVG/DOM, rendered ONCE per tapped duel from the emitted per-duel ball list
	 * (replays[id]), no rAF loop, no set-piece budget. Every meeting the pair ever
	 * had, in bowling order, grouped into season bands. Each cell is colored by
	 * outcome, and every WICKET carries a redundant SHAPE (a skittle glyph), never
	 * color alone, so the drama survives small cells and colorblindness. On desktop
	 * it flows wide; on a phone it WRAPS (season bands as row separators) so the
	 * whole rivalry is one screen-gestalt read, never a 160-row column.
	 */
	interface Summary {
		bat: string;
		bowl: string;
		balls: number;
		runs: number;
		dis: number;
		span: [number, number];
	}
	interface Props {
		replay: Replay | null;
		summary: Summary;
		onClose?: () => void;
	}
	let { replay, summary, onClose }: Props = $props();

	interface Cell {
		code: number;
		wicket: boolean;
		runs: number;
	}
	interface Band {
		season: number;
		cells: Cell[];
	}

	/* re-block the flat code stream into season bands from the run-length sb list */
	const bands = $derived.by<Band[]>(() => {
		if (!replay) return [];
		const out: Band[] = [];
		let i = 0;
		for (const [season, count] of replay.sb) {
			const cells: Cell[] = [];
			for (let k = 0; k < count && i < replay.c.length; k++, i++) {
				const code = replay.c[i];
				cells.push({ code, wicket: isWicket(code), runs: code <= 6 ? code : 0 });
			}
			out.push({ season, cells });
		}
		return out;
	});

	/** an outcome class per cell (background tone; boundaries brighter, dots faint) */
	function toneClass(c: Cell): string {
		if (c.wicket) return 'wk';
		if (c.runs === 6) return 'six';
		if (c.runs === 4) return 'four';
		if (c.runs >= 2) return 'two';
		if (c.runs === 1) return 'one';
		return 'dot';
	}
</script>

{#if replay}
	<div class="replay" role="dialog" aria-label={`${summary.bat} versus ${summary.bowl}, ball by ball`}>
		<div class="head">
			<div class="who">
				<strong>{summary.bat}</strong> versus <strong>{summary.bowl}</strong>
			</div>
			<div class="sum">
				{summary.balls} balls, {summary.runs} runs, {summary.dis}
				{summary.dis === 1 ? 'dismissal' : 'dismissals'}, {summary.span[0]} to {summary.span[1]}
			</div>
			{#if onClose}
				<button class="close" onclick={() => onClose?.()} aria-label="Close the replay">×</button>
			{/if}
		</div>

		<div class="bands">
			{#each bands as b (b.season)}
				<div class="band">
					<span class="season">{b.season}</span>
					<div class="cells">
						{#each b.cells as c, k (k)}
							<span class="cell {toneClass(c)}" title={c.wicket ? 'wicket' : `${c.runs}`}>
								{#if c.wicket}
									<!-- the redundant skittle SHAPE (not color alone) -->
									<svg viewBox="0 0 10 10" class="skittle" aria-hidden="true">
										<path d="M5 1 L5 6 M2.5 9 L7.5 9" />
										<circle cx="5" cy="7.5" r="1.1" />
									</svg>
								{:else if c.runs >= 4}
									<span class="num">{c.runs}</span>
								{/if}
							</span>
						{/each}
					</div>
				</div>
			{/each}
		</div>

		<div class="key" aria-hidden="true">
			<span class="k"><span class="cell four"><span class="num">4</span></span> boundary</span>
			<span class="k"
				><span class="cell wk"
					><svg viewBox="0 0 10 10" class="skittle"
						><path d="M5 1 L5 6 M2.5 9 L7.5 9" /><circle cx="5" cy="7.5" r="1.1" /></svg
					></span
				> wicket</span
			>
		</div>
	</div>
{/if}

<style>
	.replay {
		pointer-events: auto;
		background: rgba(10, 14, 24, 0.95);
		border: 1px solid rgba(151, 161, 184, 0.28);
		border-radius: 14px;
		padding: 0.9rem 1.05rem;
		max-width: min(46rem, 94vw);
		max-height: 70vh;
		overflow-y: auto;
		box-shadow: 0 12px 40px rgba(0, 0, 0, 0.55);
	}

	.head {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0.3rem 0.8rem;
		margin-bottom: 0.7rem;
	}

	.who {
		font-size: 1rem;
		color: var(--ink);
	}

	.who strong {
		font-weight: 800;
	}

	.sum {
		font-size: 0.78rem;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
	}

	.close {
		margin-left: auto;
		min-width: 44px;
		min-height: 44px;
		border: none;
		background: none;
		color: var(--ink-dim);
		font-size: 1.4rem;
		line-height: 1;
		cursor: pointer;
	}

	.close:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.bands {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.band {
		display: flex;
		align-items: flex-start;
		gap: 0.55rem;
		border-top: 1px solid rgba(151, 161, 184, 0.14);
		padding-top: 0.4rem;
	}

	.season {
		flex: none;
		width: 2.6rem;
		font-size: 0.7rem;
		font-weight: 700;
		color: var(--ink-dim);
		font-variant-numeric: tabular-nums;
		padding-top: 0.1rem;
	}

	.cells {
		display: flex;
		flex-wrap: wrap;
		gap: 3px;
	}

	.cell {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 15px;
		height: 15px;
		border-radius: 3px;
		font-size: 0.56rem;
		font-weight: 800;
		line-height: 1;
	}

	.cell.dot {
		background: rgba(151, 161, 184, 0.16);
	}

	.cell.one {
		background: rgba(151, 161, 184, 0.34);
	}

	.cell.two {
		background: rgba(151, 161, 184, 0.55);
	}

	.cell.four {
		background: var(--gold);
		color: #1a1204;
	}

	.cell.six {
		background: var(--ember);
		color: #1a0803;
		box-shadow: inset 0 0 0 1.5px rgba(255, 255, 255, 0.55);
	}

	.cell.wk {
		background: rgba(20, 26, 40, 0.95);
		box-shadow: inset 0 0 0 1px rgba(232, 236, 245, 0.7);
	}

	.num {
		color: inherit;
	}

	.skittle {
		width: 10px;
		height: 10px;
		fill: none;
		stroke: #fff;
		stroke-width: 1.3;
		stroke-linecap: round;
	}

	.skittle circle {
		fill: #fff;
		stroke: none;
	}

	.key {
		display: flex;
		gap: 1rem;
		margin-top: 0.7rem;
		font-size: 0.68rem;
		color: var(--ink-dim);
	}

	.key .k {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
	}

	@media (max-width: 640px) {
		.cell {
			width: 17px;
			height: 17px;
		}
	}
</style>
