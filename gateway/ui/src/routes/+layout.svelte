<div class="shell">
	<header class="header">
		<a class="brand" href="/">
			<img class="logo" src="/logo.png" alt="Sjursen Digital logo" />
			<div class="brand-text">
				<span class="brand-name">Sjursen Digital</span>
				<span class="sub-name">Gateway Control</span>
			</div>
		</a>
	</header>

	<main class="main-content">
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
		background-color: #fafafa;
		color: #18181b;
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;

		/* Sjursen Digital design tokens (light app theme) */
		--sd-surface: #ffffff;
		--sd-text: #18181b;
		--sd-text-muted: #52525b;
		--sd-border: #e4e4e7;
		--sd-border-subtle: #f4f4f5;
		--sd-action: #18181b;
		--sd-action-hover: #27272a;
		--sd-action-text: #ffffff;
		--sd-disabled: #f4f4f5;
		--sd-disabled-text: #a1a1aa;
		--sd-badge-bg: #f4f4f5;
		--sd-badge-text: #3f3f46;
	}
	:global(*) {
		box-sizing: border-box;
	}

	.shell {
		max-width: 1040px;
		margin: 0 auto;
		padding: 2.5rem 1.5rem 6rem;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: 1rem;
		border-bottom: 1px solid var(--sd-border);
		padding-bottom: 1.5rem;
		margin-bottom: 3.5rem;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.9rem;
		text-decoration: none;
		color: var(--sd-text);
	}

	.logo {
		height: 30px;
		width: auto;
		transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
	}
	.brand:hover .logo {
		transform: scale(1.04);
	}

	.brand-text {
		display: flex;
		flex-direction: column;
	}
	.brand-name {
		font-size: 1.25rem;
		font-weight: 700;
		letter-spacing: -0.025em;
		line-height: 1.1;
	}
	.sub-name {
		font-size: 0.75rem;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--sd-text-muted);
		margin-top: 0.15rem;
	}

	.main-content {
		animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(4px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
