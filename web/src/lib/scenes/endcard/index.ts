import type { SceneDef } from '$lib/story/types';
import EndCard from './EndCard.svelte';

/**
 * END CARD — owned by the end-card scene builders (storyboard §4).
 * The field exhales back into the free field behind the card (the return leg
 * of Ch 1's controlling morph, not a second morph); the card itself is
 * static DOM, so the loop stays stopped while it holds. The card reads
 * `ebe.team.v1` for the personalized sandbox tease but never gates on it
 * (deep links into #end always work).
 */
export const scenes: SceneDef[] = [
	{
		id: 'end',
		chapter: 'endcard',
		anchor: 'end',
		navLabel: 'What’s next',
		scrollLength: 180,
		morphLength: 80,
		fieldState: { layout: 'free', dim: 0.55 },
		annotations: EndCard
	}
];
