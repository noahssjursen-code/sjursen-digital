import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		// adapter-static is ideal for single-container architectures
		// since it builds a zero-dependency SPA that FastAPI can serve directly
		adapter: adapter({
			pages: '../api/static',
			assets: '../api/static',
			fallback: 'index.html',
			precompress: false,
			strict: true
		})
	}
};

export default config;
