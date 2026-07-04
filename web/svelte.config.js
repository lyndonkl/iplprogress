import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		// Full static prerender, no server routes anywhere (blueprint §8).
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: undefined,
			precompress: false,
			strict: true
		}),
		paths: {
			// GitHub Pages subpath from day one (blueprint §8): the site must work
			// at https://<user>.github.io/<repo>/. CI builds with BASE_PATH set.
			base: process.env.BASE_PATH || '',
			// absolute base-prefixed asset URLs, so CI can assert the subpath build
			relative: false
		}
	}
};

export default config;
