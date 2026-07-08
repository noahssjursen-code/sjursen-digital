import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
	plugins: [sveltekit()],
	resolve: {
		alias: {
			// Elegant monorepo alias for shared UI components
			'$shared': path.resolve(__dirname, '../../../shared/components')
		}
	},
	server: {
		port: 3000,
		proxy: {
			'/api': 'http://localhost:8000'
		},
		fs: {
			// Allow Vite to serve files from the shared monorepo directory outside project root
			allow: [
				'src',
				'.svelte-kit',
				'node_modules',
				path.resolve(__dirname, '../../../shared/components')
			]
		}
	}
});
