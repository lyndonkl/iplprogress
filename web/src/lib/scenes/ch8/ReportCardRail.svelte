<script lang="ts">
	import type { ReportCard } from './data';

	/**
	 * The report-card rail (storyboard §0.1), the chapter's spine. A slim five-slot
	 * rail that rides one edge of the frame from C8-3 on. As each belief is graded,
	 * its slot stamps a verdict: a CROSS for fail, a TICK for pass, ICON FIRST and
	 * colour second so the grade never rests on colour alone (fallacies-guard). The
	 * fifth slot stays blank until C8-7 so the pass is a genuine reveal. The rail
	 * fail-red / pass-green are held distinct from the review chip red/green and from
	 * every team red. On mobile it collapses to a slim TOP strip so it never fights
	 * the bottom-anchored caption.
	 *
	 * `stamped` is the number of slots currently showing a verdict (0..5). Each scene
	 * passes its cumulative count: belief k shows k-1 prior stamps and adds its own
	 * once the scene reaches its grade step.
	 */
	interface Props {
		report: ReportCard | null;
		/** how many slots currently carry a verdict (0..5) */
		stamped: number;
	}
	let { report, stamped }: Props = $props();

	const beliefs = $derived(report?.beliefs ?? []);
</script>

{#if beliefs.length === 5}
	<div class="rail" aria-label="The belief report card">
		<span class="rail-title">the report card</span>
		<ol class="slots">
			{#each beliefs as b (b.slot)}
				{@const shown = stamped >= b.slot}
				{@const isPass = b.grade === 'pass'}
				<li class="slot" class:shown class:pass={isPass && shown} class:fail={!isPass && shown}>
					<span class="mark" aria-hidden="true">
						{#if shown}{isPass ? '✓' : '✕'}{:else}·{/if}
					</span>
					<span class="name">{b.name}</span>
					<span class="sr-only">
						{#if shown}
							{isPass ? 'pass' : 'not backed by the record'}
						{:else}
							not graded yet
						{/if}
					</span>
				</li>
			{/each}
		</ol>
	</div>
{/if}

<style>
	.rail {
		position: fixed;
		right: 1.4vw;
		top: 50%;
		transform: translateY(-50%);
		z-index: 6;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 0.6rem 0.55rem;
		border-radius: 12px;
		background: rgba(10, 14, 24, 0.72);
		border: 1px solid rgba(151, 161, 184, 0.22);
		pointer-events: none;
		max-width: 8.5rem;
	}

	.rail-title {
		font-size: 0.56rem;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--ink-dim);
	}

	.slots {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}

	.slot {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		opacity: 0.4;
		transition: opacity 0.3s ease;
	}

	.slot.shown {
		opacity: 1;
	}

	.mark {
		flex: none;
		width: 1.15rem;
		height: 1.15rem;
		display: grid;
		place-items: center;
		border-radius: 50%;
		font-size: 0.72rem;
		font-weight: 800;
		color: var(--ink-dim);
		background: rgba(151, 161, 184, 0.12);
		border: 1px solid rgba(151, 161, 184, 0.25);
	}

	.slot.fail .mark {
		color: #ffd9d2;
		background: rgba(224, 106, 90, 0.28);
		border-color: #e06a5a;
	}

	.slot.pass .mark {
		color: #daffe8;
		background: rgba(111, 207, 151, 0.28);
		border-color: #6fcf97;
	}

	.name {
		font-size: 0.62rem;
		line-height: 1.15;
		color: var(--ink-dim);
	}

	.slot.shown .name {
		color: var(--ink);
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	@media (max-width: 640px) {
		/* collapse to a slim top strip, clear of the top-right nav and the bottom caption */
		.rail {
			right: auto;
			left: 2vw;
			top: max(6vh, calc(env(safe-area-inset-top) + 8px));
			transform: none;
			flex-direction: row;
			align-items: center;
			gap: 0.4rem;
			max-width: 92vw;
			padding: 0.35rem 0.5rem;
		}

		.rail-title {
			display: none;
		}

		.slots {
			flex-direction: row;
			gap: 0.3rem;
		}

		.name {
			display: none;
		}
	}
</style>
