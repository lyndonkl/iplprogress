<script lang="ts">
	import type { SceneAnnotationProps } from '$lib/story/types';

	/**
	 * CO-1 beat 1 — the stakes line, alone on black (storyboard §1 Scene CO-1).
	 * The field exists but is unborn (assembly reveal 0 — zero points visible);
	 * a faint CSS starfield keeps black from reading as broken. The line makes
	 * the reader stake a belief before anything is shown.
	 */
	let { reduced }: SceneAnnotationProps = $props();
</script>

<div class="pin">
	<div class="stars" aria-hidden="true"></div>
	<div class="stakes" class:reduced>
		<h1>Something happened to cricket scoring.</h1>
		<p>Draw what you think it was.</p>
		<div class="cue" aria-hidden="true">↓</div>
	</div>
</div>

<style>
	.pin {
		position: sticky;
		top: 0;
		height: 100vh;
		height: 100dvh;
		overflow: hidden;
	}

	.stars {
		position: absolute;
		inset: 0;
		background-image:
			radial-gradient(1.2px 1.2px at 18% 24%, rgba(232, 236, 245, 0.4), transparent 60%),
			radial-gradient(1px 1px at 66% 12%, rgba(232, 236, 245, 0.3), transparent 60%),
			radial-gradient(1.4px 1.4px at 84% 62%, rgba(232, 236, 245, 0.26), transparent 60%),
			radial-gradient(1px 1px at 38% 78%, rgba(232, 236, 245, 0.3), transparent 60%),
			radial-gradient(1px 1px at 8% 54%, rgba(232, 236, 245, 0.22), transparent 60%);
		background-size:
			280px 260px,
			340px 300px,
			420px 380px,
			360px 320px,
			300px 340px;
		background-repeat: repeat;
		opacity: 0.45;
	}

	.stakes {
		position: absolute;
		inset: 0;
		display: grid;
		place-content: center;
		text-align: center;
		padding: 2rem;
		gap: 0.5rem;
		animation: rise 900ms ease-out both;
	}

	.stakes.reduced {
		animation: none;
	}

	.stakes h1 {
		margin: 0;
		font-size: clamp(1.6rem, 5vw, 2.6rem);
		font-weight: 700;
		line-height: 1.2;
		max-width: 22ch;
	}

	.stakes p {
		margin: 0;
		font-size: clamp(1.1rem, 3vw, 1.4rem);
		color: var(--ink-dim);
	}

	.cue {
		margin-top: 2.2rem;
		font-size: 1.3rem;
		color: var(--ink-dim);
		animation: bounce 1.8s ease-in-out infinite;
	}

	@keyframes rise {
		from {
			opacity: 0;
			transform: translateY(14px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@keyframes bounce {
		0%,
		100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(7px);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.stakes,
		.cue {
			animation: none;
		}
	}
</style>
