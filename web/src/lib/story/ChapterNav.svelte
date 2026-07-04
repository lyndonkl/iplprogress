<script lang="ts">
	import { base } from '$app/paths';
	import { pickedTeam } from '$lib/state';
	import type { NavItem } from './navplan';

	/**
	 * Persistent chapter nav (blueprint §2, ships from R1): a fixed ☰ button
	 * (44×44, top-right) opening a sheet (mobile) / right rail (desktop) of
	 * chapter entries. Built scenes are real links (hash deep-links; the story
	 * shell calls ScrollTrigger.update() on hashchange); unbuilt chapters are
	 * titles with a `soon` tag. Chapters stand alone: jumping anywhere works
	 * with no sketch or team state.
	 */

	interface Props {
		items: NavItem[];
		/** appears after the cold open (or immediately on deep entry / return visits) */
		visible: boolean;
		/** anchor of the currently-active scene */
		currentAnchor: string;
		/** stored progress anchor from a previous visit, if any */
		resumeAnchor?: string | null;
	}

	let { items, visible, currentAnchor, resumeAnchor = null }: Props = $props();

	let open = $state(false);
	let sheetEl = $state<HTMLElement | null>(null);
	let buttonEl = $state<HTMLButtonElement | null>(null);

	const teamLine = $derived(
		$pickedTeam === null || $pickedTeam.team === 'neutral'
			? 'No team picked'
			: `Team: ${$pickedTeam.team}${$pickedTeam.league === 'wpl' ? ' (WPL)' : ''}`
	);

	const showResume = $derived(
		resumeAnchor !== null && resumeAnchor !== undefined && resumeAnchor !== currentAnchor
	);

	function toggle(): void {
		open = !open;
	}

	function close(): void {
		open = false;
		buttonEl?.focus();
	}

	$effect(() => {
		if (open && sheetEl) sheetEl.focus();
	});

	function onKeydown(e: KeyboardEvent): void {
		if (e.key === 'Escape') {
			e.stopPropagation();
			close();
			return;
		}
		if (e.key !== 'Tab' || !sheetEl) return;
		const focusables = sheetEl.querySelectorAll<HTMLElement>(
			'button, a[href], [tabindex]:not([tabindex="-1"])'
		);
		if (focusables.length === 0) return;
		const first = focusables[0];
		const last = focusables[focusables.length - 1];
		if (e.shiftKey && document.activeElement === first) {
			e.preventDefault();
			last.focus();
		} else if (!e.shiftKey && document.activeElement === last) {
			e.preventDefault();
			first.focus();
		}
	}
</script>

{#if visible || open}
	<button
		class="nav-button"
		bind:this={buttonEl}
		onclick={toggle}
		aria-label="Chapters"
		aria-expanded={open}
		aria-controls="chapter-nav-sheet"
	>
		<span class="glyph" aria-hidden="true">☰</span>
		{#if showResume && !open}<span class="dot" aria-hidden="true"></span>{/if}
	</button>
{/if}

{#if open}
	<div class="scrim" onclick={close} aria-hidden="true"></div>
	<div
		id="chapter-nav-sheet"
		class="sheet"
		role="dialog"
		aria-modal="true"
		aria-label="Chapters"
		tabindex="-1"
		bind:this={sheetEl}
		onkeydown={onKeydown}
	>
		<header>
			<p class="overline">Every Ball Ever</p>
			<button class="close" onclick={close} aria-label="Close chapter menu">✕</button>
		</header>

		{#if showResume}
			<a class="resume" href="#{resumeAnchor}" onclick={close}>
				Continue where you left off →
			</a>
		{/if}

		<p class="team-line">
			{teamLine} · <a href="#picker" onclick={close}>change</a>
		</p>

		<ul aria-label="Chapter list">
			{#each items as item (item.label)}
				<li>
					{#if item.status === 'live' && item.anchor}
						<a
							href="#{item.anchor}"
							onclick={close}
							aria-current={item.anchor === currentAnchor ? 'true' : undefined}
						>
							{item.label}
						</a>
					{:else}
						<span class="soon-item">
							{item.label}
							<span class="tag">soon</span>
						</span>
					{/if}
				</li>
			{/each}
		</ul>

		<footer>
			<a href="{base}/methods/" class="methods">How we computed all of this →</a>
		</footer>
	</div>
{/if}

<style>
	.nav-button {
		position: fixed;
		top: 12px;
		right: 12px;
		z-index: 70;
		width: 44px;
		height: 44px;
		border-radius: 12px;
		border: 1px solid rgba(232, 236, 245, 0.16);
		background: rgba(11, 14, 20, 0.62);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
		color: var(--ink);
		font-size: 1.05rem;
		cursor: pointer;
	}

	.nav-button:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.dot {
		position: absolute;
		top: 7px;
		right: 7px;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--gold);
	}

	.scrim {
		position: fixed;
		inset: 0;
		z-index: 71;
		background: rgba(4, 6, 10, 0.55);
	}

	.sheet {
		position: fixed;
		z-index: 72;
		inset: 0;
		background: #10141d;
		color: var(--ink);
		padding: 1.1rem 1.3rem 1.6rem;
		overflow-y: auto;
		outline: none;
	}

	@media (min-width: 720px) {
		.sheet {
			left: auto;
			width: min(24rem, 90vw);
			border-left: 1px solid rgba(232, 236, 245, 0.12);
		}
	}

	header {
		position: relative;
		margin-bottom: 0.9rem;
	}

	.overline {
		margin: 0.4rem 0 0;
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.28em;
		text-transform: uppercase;
		color: var(--gold);
	}

	.close {
		position: absolute;
		top: 0;
		right: 0;
		width: 44px;
		height: 44px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		border-radius: 10px;
		background: transparent;
		color: var(--ink);
		cursor: pointer;
	}

	.close:focus-visible,
	.sheet a:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.resume {
		display: block;
		margin: 0 0 0.9rem;
		padding: 0.7rem 0.9rem;
		border: 1px solid rgba(232, 163, 61, 0.4);
		border-radius: 10px;
		color: var(--gold);
		text-decoration: none;
		font-weight: 600;
	}

	.team-line {
		margin: 0 0 1rem;
		font-size: 0.85rem;
		color: var(--ink-dim);
	}

	.team-line a {
		color: var(--teal);
	}

	ul {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	li {
		border-bottom: 1px solid rgba(232, 236, 245, 0.06);
	}

	li a,
	.soon-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.8rem;
		padding: 0.75rem 0.2rem;
		font-size: 0.95rem;
		line-height: 1.35;
	}

	li a {
		color: var(--ink);
		text-decoration: none;
	}

	li a[aria-current='true'] {
		color: var(--teal);
		font-weight: 650;
	}

	.soon-item {
		color: var(--ink-dim);
	}

	.tag {
		flex: none;
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		padding: 0.15rem 0.45rem;
		border: 1px solid rgba(151, 161, 184, 0.35);
		border-radius: 999px;
		color: var(--ink-dim);
	}

	footer {
		margin-top: 1.2rem;
	}

	.methods {
		color: var(--teal);
		font-size: 0.9rem;
	}
</style>
