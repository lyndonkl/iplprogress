<script lang="ts">
	import { onMount } from 'svelte';
	import type { SceneAnnotationProps } from '$lib/story/types';
	import ReportCardRail from './ReportCardRail.svelte';
	import { loadCh8Data, type Ch8Data } from './data';

	/**
	 * C8-10, Chapter close: total the report card, then hand to Chapter 9. The match-
	 * dots exhale back into the free scatter (the controlling morph's reverse leg,
	 * declared in index.ts), so the end card's field is byte-identical to entry. The
	 * report-card rail holds its five stamps one last beat. No numbers (closes commit,
	 * they do not count). Ch 8 graded what captains BELIEVE (things that change fast);
	 * Ch 9 finds what STAYS (the rivalries and the roster churn underneath), so neither
	 * pre-judges the other.
	 */
	let { progress, active }: SceneAnnotationProps = $props();

	let ch8 = $state<Ch8Data | null>(null);
	onMount(() => {
		let alive = true;
		loadCh8Data().then((d) => {
			if (alive) ch8 = d;
		});
		return () => {
			alive = false;
		};
	});

	const step = $derived(progress < 0.4 ? 1 : progress < 0.72 ? 2 : 3);
</script>

<div class="pin" class:active>
	{#if step < 3}
		<ReportCardRail report={ch8?.report_card ?? null} stamped={5} />
	{/if}

	<div class="caption-slot">
		{#if step === 1}
			<div class="scene-card">
				<p>
					Four fails and one pass. Bowling first is not the edge, most reviews never overturn the
					call, spells are gone, and momentum is mostly a feeling. Only the pacing of a chase held up.
				</p>
			</div>
		{:else if step === 2}
			<div class="scene-card">
				<p>Here is the thing about beliefs. They churn. A whole doctrine can arrive and die inside a broadcast cycle.</p>
			</div>
		{:else}
			<div class="scene-card">
				<p>
					{ch8?.mystery_handoff_out ??
						'But underneath the churn, some things refuse to move. Rivalries. Who a team keeps. Next chapter, we find what stays.'}
				</p>
				<p class="note">Next: <strong>The Living League.</strong></p>
			</div>
		{/if}
	</div>
</div>

<style>
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
	}

	.pin.active {
		visibility: visible;
	}

	.caption-slot {
		position: absolute;
		left: 5vw;
		top: 14vh;
		max-width: min(28rem, 86vw);
	}

	@media (max-width: 640px) {
		.caption-slot {
			left: 50%;
			transform: translateX(-50%);
			width: 92vw;
			max-width: 92vw;
			top: auto;
			bottom: max(10vh, calc(env(safe-area-inset-bottom) + 64px));
		}
	}
</style>
