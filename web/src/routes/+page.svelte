<script lang="ts">
	import { browser } from '$app/environment';
	import { get } from 'svelte/store';
	import Story from '$lib/story/Story.svelte';
	import ChapterNav from '$lib/story/ChapterNav.svelte';
	import { buildNavItems } from '$lib/story/navplan';
	import type { SceneDef } from '$lib/story/types';
	import { chapterProgress } from '$lib/state';
	import { scenes as coldOpenScenes } from '$lib/scenes/coldopen';
	import { scenes as pickerScenes } from '$lib/scenes/picker';
	import { scenes as ch1Scenes } from '$lib/scenes/ch1';
	import { scenes as ch2Scenes } from '$lib/scenes/ch2';
	import { scenes as ch3Scenes } from '$lib/scenes/ch3';
	import { scenes as ch4Scenes } from '$lib/scenes/ch4';
	import { scenes as interludeScenes } from '$lib/scenes/interlude';
	import { scenes as ch5Scenes } from '$lib/scenes/ch5';
	import { scenes as endCardScenes } from '$lib/scenes/endcard';
	import { scenes as sandboxScenes } from '$lib/scenes/sandbox';

	/**
	 * The piece: an ordered list of scenes from the chapter directories,
	 * composed into one scroll timeline over the persistent field
	 * (see lib/story/CONTRACT.md for the contract + ownership map).
	 */
	const scenes: SceneDef[] = [
		...coldOpenScenes,
		...pickerScenes,
		...ch1Scenes,
		...ch2Scenes,
		...ch3Scenes,
		...ch4Scenes,
		// The Net Session interlude teaches both currencies; Chapter 5 (What a
		// Ball Is Worth) spends them immediately. The end card follows.
		...interludeScenes,
		...ch5Scenes,
		...endCardScenes,
		...sandboxScenes
	];

	const navItems = buildNavItems(scenes);

	// Snapshot BEFORE the story starts writing progress: this is the previous
	// visit's "last anchor reached", powering the nav's Continue affordance.
	const resumeAnchor = browser ? (get(chapterProgress)?.scene ?? null) : null;

	let currentAnchor = $state(scenes[0].anchor ?? scenes[0].id);
	// the ☰ dims to 40% while a set-piece morph is in flight (storyboard §6)
	let navDimmed = $state(false);

	function onSceneChange(_index: number, scene: SceneDef): void {
		currentAnchor = scene.anchor ?? scene.id;
	}
</script>

<svelte:head>
	<title>Every Ball Ever</title>
	<meta
		name="description"
		content="Every ball ever bowled in the IPL and WPL, as one living field of light — and it never leaves the screen."
	/>
</svelte:head>

<Story {scenes} {onSceneChange} onSetPieceChange={(inFlight) => (navDimmed = inFlight)} />

<ChapterNav items={navItems} dimmed={navDimmed} {currentAnchor} {resumeAnchor} />
