<script lang="ts">
	import { footnotesOpen } from '$lib/state';
	import { FOOTNOTES, isFootnoteId } from './footnotes';

	/**
	 * The footnote slide-over: bottom sheet on mobile, side panel on desktop.
	 * Pure DOM, tap- and keyboard-operable (blueprint §2: no hover-only
	 * content). Opens when the footnotesOpen store holds a registry id.
	 */

	let panelEl = $state<HTMLElement | null>(null);
	let lastFocused: Element | null = null;

	const entry = $derived(isFootnoteId($footnotesOpen) ? FOOTNOTES[$footnotesOpen] : null);

	$effect(() => {
		if (entry && panelEl) {
			lastFocused = document.activeElement;
			panelEl.focus();
		} else if (!entry && lastFocused instanceof HTMLElement) {
			lastFocused.focus();
			lastFocused = null;
		}
	});

	function close(): void {
		footnotesOpen.set(null);
	}

	function onKeydown(e: KeyboardEvent): void {
		if (e.key === 'Escape') {
			e.stopPropagation();
			close();
			return;
		}
		if (e.key !== 'Tab' || !panelEl) return;
		// minimal focus trap: cycle within the panel
		const focusables = panelEl.querySelectorAll<HTMLElement>(
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

{#if entry}
	<div class="scrim" onclick={close} aria-hidden="true"></div>
	<div
		class="panel"
		role="dialog"
		aria-modal="true"
		aria-labelledby="footnote-title"
		tabindex="-1"
		bind:this={panelEl}
		onkeydown={onKeydown}
	>
		<header>
			<p class="overline">How we computed this</p>
			<h2 id="footnote-title">{entry.title}</h2>
			<button class="close" onclick={close} aria-label="Close footnote">✕</button>
		</header>
		<div class="body">
			{#each entry.paragraphs as para (para)}
				<p>{para}</p>
			{/each}
		</div>
	</div>
{/if}

<style>
	.scrim {
		position: fixed;
		inset: 0;
		z-index: 80;
		background: rgba(4, 6, 10, 0.55);
	}

	.panel {
		position: fixed;
		z-index: 81;
		background: #10141d;
		border: 1px solid rgba(232, 236, 245, 0.12);
		color: var(--ink);
		display: flex;
		flex-direction: column;
		outline: none;

		/* mobile: bottom sheet */
		left: 0;
		right: 0;
		bottom: 0;
		max-height: 72dvh;
		border-radius: 16px 16px 0 0;
	}

	@media (min-width: 720px) {
		/* desktop: right slide-over */
		.panel {
			left: auto;
			top: 0;
			bottom: 0;
			width: min(26rem, 90vw);
			max-height: none;
			border-radius: 0;
			border-right: none;
		}
	}

	header {
		position: relative;
		padding: 1.1rem 3rem 0.6rem 1.3rem;
		border-bottom: 1px solid rgba(232, 236, 245, 0.08);
	}

	.overline {
		margin: 0 0 0.3rem;
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.24em;
		text-transform: uppercase;
		color: var(--gold);
	}

	h2 {
		margin: 0 0 0.7rem;
		font-size: 1.15rem;
		line-height: 1.3;
	}

	.close {
		position: absolute;
		top: 0.9rem;
		right: 0.9rem;
		width: 44px;
		height: 44px;
		border: 1px solid rgba(232, 236, 245, 0.18);
		border-radius: 10px;
		background: transparent;
		color: var(--ink);
		font-size: 1rem;
		cursor: pointer;
	}

	.close:focus-visible {
		outline: 2px solid var(--teal);
		outline-offset: 2px;
	}

	.body {
		padding: 1rem 1.3rem 1.4rem;
		overflow-y: auto;
	}

	.body p {
		margin: 0 0 0.9rem;
		font-size: 0.95rem;
		line-height: 1.55;
		color: var(--ink);
	}

	.body p:last-child {
		margin-bottom: 0;
	}
</style>
