<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';
	import { PayoffCard, requestTeamChange } from '$lib/scenes/picker';

	/**
	 * C1-7 — Team payoff card scene (storyboard §3): the chapter's finding
	 * re-told in the reader's colors. A thin scene wrapper around the REUSABLE
	 * payoff card the picker directory owns (CONTRACT §7: chapter builders
	 * import { PayoffCard } and drop it in — never fork it). Strictly template
	 * + payoff/ch1.json (16 variants, snapshot-tested); re-renders live on a
	 * team change, and "Not your team? Change it" round-trips through the
	 * picker and returns HERE (storyboard: "→ picker (state preserved,
	 * returns here)").
	 *
	 * The card renders inside a FIXED pin, so the card element itself can't be
	 * the scroll-return target (its rect is viewport-relative). The in-flow
	 * return anchor below sits mid-section — past the card-slot's shown
	 * threshold — and is what the picker's advance scrolls back to.
	 */
	let { progress, active, field }: SceneAnnotationProps = $props();

	/* morphLength / scrollLength from index.ts: 50 / 140 */
	const shown = $derived(progress >= 0.4);

	let returnAnchor = $state<HTMLElement | null>(null);
</script>

<!-- in-flow (section-relative) scroll target for the change-team round trip;
     45% of the section ≈ progress 0.45 — the card is shown on arrival -->
<div class="return-anchor" bind:this={returnAnchor} aria-hidden="true"></div>

<div class="pin" class:active>
	<div class="card-slot" class:shown>
		<PayoffCard
			teams={field?.data.teams ?? null}
			onChangeTeam={() => requestTeamChange(returnAnchor)}
		/>
	</div>
</div>

<style>
	.return-anchor {
		position: absolute;
		top: 45%;
		left: 0;
		width: 1px;
		height: 1px;
	}

	/* viewport-fixed while active — one scene's captions on screen at a time */
	.pin {
		position: fixed;
		inset: 0;
		visibility: hidden;
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	.pin.active {
		visibility: visible;
	}

	/* instant show/hide — appear-states never ride a transition (a stalled
	   fade after a nav jump would hide the card; the beat must not need it) */
	.card-slot {
		opacity: 0;
		max-height: 100%;
	}

	.card-slot.shown {
		opacity: 1;
	}
</style>
