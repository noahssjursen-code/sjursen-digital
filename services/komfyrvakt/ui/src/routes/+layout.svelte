<script lang="ts">
	import { page } from '$app/stores';
	import { base } from '$app/paths';

	const nav = [
		{ href: `${base}/`, label: 'Alerts' },
		{ href: `${base}/instances`, label: 'Instances' },
		{ href: `${base}/types`, label: 'Types' },
		{ href: `${base}/keys`, label: 'Keys' }
	];

	$: current = $page.url.pathname;
	const isActive = (href: string, path: string) =>
		href === `${base}/` ? path === `${base}/` || path === `${base}` : path.startsWith(href);
</script>

<div class="shell">
	<header class="header">
		<a class="brand" href="{base}/">
			<svg class="logo" viewBox="0 0 100 100" fill="none" role="img" aria-label="Komfyrvakt">
				<path
					d="M 46,25 C 33,25 25,32 25,41 C 25,51 45,49 45,59 C 45,68 37,75 24,75 L 60,75 C 73,75 75,64 75,50 C 75,36 73,25 60,25 Z"
					stroke="currentColor"
					stroke-width="6.5"
					stroke-linecap="round"
					stroke-linejoin="round"
				/>
			</svg>
			<span class="brand-name">Komfyrvakt</span>
		</a>
		<nav>
			{#each nav as item}
				<a href={item.href} class:active={isActive(item.href, current)}>{item.label}</a>
			{/each}
		</nav>
	</header>

	<main>
		<slot />
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family:
			'Inter',
			-apple-system,
			BlinkMacSystemFont,
			'Segoe UI',
			Roboto,
			sans-serif;
		background-color: #fdfdfb;
		color: #000;
		background-image: radial-gradient(#f1f3f5 1.5px, transparent 1.5px);
		background-size: 20px 24px;
	}
	:global(*) {
		box-sizing: border-box;
	}

	.shell {
		max-width: 960px;
		margin: 0 auto;
		padding: 1.5rem 1rem 4rem;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: 1rem;
		border-bottom: 2px solid #000;
		padding-bottom: 1rem;
		margin-bottom: 2rem;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		text-decoration: none;
		color: #000;
	}
	.logo {
		width: 40px;
		height: 40px;
		transform: rotate(-1.5deg);
	}
	.brand-name {
		font-size: 1.5rem;
		font-weight: 900;
		letter-spacing: -0.03em;
		text-transform: uppercase;
	}

	nav {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}
	nav a {
		color: #000;
		text-decoration: none;
		font-weight: 800;
		text-transform: uppercase;
		font-size: 0.85rem;
		letter-spacing: 0.03em;
		padding: 0.4rem 0.9rem;
		border: 2px solid transparent;
		border-radius: 12px 6px 10px 6px/6px 10px 6px 8px;
	}
	nav a:hover {
		border-color: #000;
	}
	nav a.active {
		background: #000;
		color: #fff;
		border-color: #000;
		box-shadow: 2px 2px 0 #000;
	}
</style>
