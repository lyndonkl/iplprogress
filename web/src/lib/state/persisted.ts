import { browser } from '$app/environment';
import { writable, type Writable } from 'svelte/store';

/**
 * SSR-safe localStorage-backed store factory.
 *
 * - On the server (prerender) the store simply holds `initial`; localStorage
 *   is never touched.
 * - On the client it hydrates once from localStorage (invalid JSON or a
 *   failing validator falls back to `initial` — corrupted storage can never
 *   break the page) and writes back on every set. `null` clears the key.
 * - Storage failures (quota, private mode, blocked) degrade to in-memory
 *   state silently: persistence is an enhancement, never a dependency.
 */
export function persisted<T>(
	key: string,
	initial: T,
	validate: (v: unknown) => v is T
): Writable<T> {
	let start = initial;
	if (browser) {
		try {
			const raw = localStorage.getItem(key);
			if (raw !== null) {
				const parsed: unknown = JSON.parse(raw);
				if (validate(parsed)) start = parsed;
			}
		} catch {
			/* unreadable storage → initial */
		}
	}

	const store = writable<T>(start);

	if (browser) {
		store.subscribe((v) => {
			try {
				if (v === null || v === undefined) localStorage.removeItem(key);
				else localStorage.setItem(key, JSON.stringify(v));
			} catch {
				/* quota / private mode: state stays in-memory */
			}
		});
	}

	return store;
}

/* ---- small validator helpers ---------------------------------------------- */

export function isRecord(v: unknown): v is Record<string, unknown> {
	return typeof v === 'object' && v !== null && !Array.isArray(v);
}

export function isFiniteNumber(v: unknown): v is number {
	return typeof v === 'number' && Number.isFinite(v);
}
