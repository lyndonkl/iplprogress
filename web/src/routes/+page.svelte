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
	import { scenes as endCardScenes } from '$lib/scenes/endcard';

	/**
	 * The piece: an ordered list of scenes from the chapter directories,
	 * composed into one scroll timeline over the persistent field
	 * (see lib/story/CONTRACT.md for the contract + ownership map).
	 */
	const scenes: SceneDef[] = [
		...coldOpenScenes,
		...pickerScenes,
		...ch1Scenes,
		...endCardScenes
	];

	const navItems = buildNavItems(scenes);

	// Snapshot BEFORE the story starts writing progress: this is the previous
	// visit's "last anchor reached", powering the nav's Continue affordance.
	const resumeAnchor = browser ? (get(chapterProgress)?.scene ?? null) : null;
	// Deep entries (shared links, nav jumps) get the nav immediately.
	const deepEntry = browser && window.location.hash.length > 1;

	let currentAnchor = $state(scenes[0].anchor ?? scenes[0].id);
	let currentChapter = $state(scenes[0].chapter);

	function onSceneChange(_index: number, scene: SceneDef): void {
		currentAnchor = scene.anchor ?? scene.id;
		currentChapter = scene.chapter;
	}

	// Chapter nav appears after the cold open (blueprint §2) — or immediately
	// for deep entries and returning readers.
	const navVisible = $derived(currentChapter !== 'coldopen' || deepEntry || resumeAnchor !== null);
</script>

<svelte:head>
	<title>Every Ball Ever</title>
	<meta
		name="description"
		content="Every ball ever bowled in the IPL and WPL, as one living field of light — and it never leaves the screen."
	/>
</svelte:head>

<Story {scenes} {onSceneChange} />

<ChapterNav items={navItems} visible={navVisible} {currentAnchor} {resumeAnchor} />
