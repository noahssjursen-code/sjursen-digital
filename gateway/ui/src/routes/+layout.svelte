<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getSessionToken, clearSessionToken } from '$lib/api';

	let authenticated = false;

	const nav = [
		{ href: '/', label: 'Apps' },
		{ href: '/keys', label: 'Licensing' }
	];

	$: current = $page.url.pathname;
	const isActive = (href: string, path: string) =>
		href === '/' ? path === '/' : path.startsWith(href);

	function logout() {
		clearSessionToken();
		authenticated = false;
		goto('/login');
	}

	onMount(() => {
		const token = getSessionToken();
		const isLoginPath = $page.url.pathname.startsWith('/login');
		
		if (!token && !isLoginPath) {
			goto('/login');
		} else if (token) {
			authenticated = true;
			if (isLoginPath) {
				goto('/');
			}
		}
	});

	// Keep authentication state reactive to page transitions
	$: {
		if (typeof window !== 'undefined') {
			const token = getSessionToken();
			authenticated = !!token;
		}
	}
</script>

<div class="shell">
	<header class="header">
		<a class="brand" href="/">
			<svg class="logo" viewBox="0 0 100 100" fill="none" role="img" aria-label="Sjursen Digital">
				<path
					d="M 46,25 C 33,25 25,32 25,41 C 25,51 45,49 45,59 C 45,68 37,75 24,75 L 60,75 C 73,75 75,64 75,50 C 75,36 73,25 60,25 Z"
					stroke="currentColor"
					stroke-width="6.5"
					stroke-linecap="round"
					stroke-linejoin="round"
				/>
			</svg>
			<div class="brand-text">
				<span class="brand-name">Sjursen Digital</span>
				<span class="sub-name">Gateway Portal</span>
			</div>
		</a>

		{#if authenticated}
			<nav>
				{#each nav as item}
					<a href={item.href} class:active={isActive(item.href, current)}>{item.label}</a>
				{/each}
				<button class="logout-btn" on:click={logout}>Logout</button>
			</nav>
		{/if}
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
		padding-bottom: 1.2rem;
		margin-bottom: 2.5rem;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.9rem;
		text-decoration: none;
		color: #000;
	}
	.logo {
		width: 44px;
		height: 44px;
		transform: rotate(-1.5deg);
	}
	.brand-text {
		display: flex;
		flex-direction: column;
	}
	.brand-name {
		font-size: 1.4rem;
		font-weight: 900;
		letter-spacing: -0.03em;
		text-transform: uppercase;
		line-height: 1.1;
	}
	.sub-name {
		font-size: 0.75rem;
		font-weight: 800;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		opacity: 0.6;
		margin-top: 0.1rem;
	}

	nav {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		flex-wrap: wrap;
	}
	nav a, .logout-btn {
		color: #000;
		text-decoration: none;
		font-weight: 800;
		text-transform: uppercase;
		font-size: 0.85rem;
		letter-spacing: 0.03em;
		padding: 0.4rem 0.9rem;
		border: 2px solid transparent;
		border-radius: 12px 6px 10px 6px/6px 10px 6px 8px;
		background: none;
		cursor: pointer;
		font-family: inherit;
	}
	nav a:hover, .logout-btn:hover {
		border-color: #000;
	}
	nav a.active {
		background: #000;
		color: #fff;
		border-color: #000;
		box-shadow: 2px 2px 0 #000;
	}
	.logout-btn {
		opacity: 0.75;
	}
	.logout-btn:hover {
		opacity: 1;
		background-color: #fff;
	}
</style>
