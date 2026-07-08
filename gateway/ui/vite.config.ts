import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
	plugins: [sveltekit()],
	resolve: {
		alias: {
			'$shared': path.resolve(__dirname, '../../shared/components')
		}
	},
	server: {
		port: 3000,
		proxy: {
			// Route central gateway APIs to the gateway backend
			'/api': 'http://localhost:8000'
		},
		fs: {
			allow: [
				'src',
				'.svelte-kit',
				'node_modules',
				path.resolve(__dirname, '../../shared/components')
			]
		}
	}
});
