<script lang="ts">
	import { goto } from '$app/navigation';
	import Card from '$shared/Card.svelte';
	import Button from '$shared/Button.svelte';
	import { api, setSessionToken } from '$lib/api';

	let username = '';
	let password = '';
	let error = '';
	let loading = false;

	async function login() {
		if (!username.trim() || !password.trim()) {
			error = 'Please enter both username and password';
			return;
		}
		error = '';
		loading = true;
		try {
			const res = await api<{ token: string; username: string }>('/api/auth/login', {
				method: 'POST',
				body: JSON.stringify({
					username: username.trim(),
					password: password.trim()
				})
			});
			setSessionToken(res.token);
			// Force reload layout by navigating to root
			window.location.href = '/';
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
			try {
				const parsed = JSON.parse(error);
				if (parsed.detail) error = parsed.detail;
			} catch {}
		}
		loading = false;
	}
</script>

<div class="login-container">
	<Card title="Gateway Login">
		<p class="intro">
			Unlock your self-hosted Sjursen Digital suite. If this is your first startup,
			your randomized administrator password was printed to the server terminal.
		</p>

		<form on:submit|preventDefault={login}>
			{#if error}
				<div class="error-box">
					<span>{error}</span>
				</div>
			{/if}

			<div class="input-group">
				<label for="username">Username</label>
				<input
					id="username"
					placeholder="admin"
					bind:value={username}
					disabled={loading}
					autocomplete="username"
				/>
			</div>

			<div class="input-group">
				<label for="password">Password</label>
				<input
					id="password"
					type="password"
					placeholder="••••••••"
					bind:value={password}
					disabled={loading}
					autocomplete="current-password"
				/>
			</div>

			<div class="btn-container">
				<Button type="submit" disabled={loading}>
					{loading ? 'Logging in…' : 'Enter Suite'}
				</Button>
			</div>
		</form>
	</Card>
</div>

<style>
	.login-container {
		max-width: 440px;
		margin: 4rem auto 0;
	}
	.intro {
		font-size: 0.9rem;
		margin-top: 0;
		margin-bottom: 1.5rem;
		line-height: 1.4;
		opacity: 0.85;
	}
	form {
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
	}
	.input-group {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	label {
		font-size: 0.75rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		opacity: 0.75;
	}
	input {
		border: 2px solid #000;
		border-radius: 12px 6px 10px 6px/6px 10px 6px 8px;
		padding: 0.6rem 0.9rem;
		font-size: 0.95rem;
		background: #fff;
		font-family: inherit;
	}
	input:focus {
		outline: none;
		box-shadow: 2px 2px 0 #000;
	}
	.error-box {
		border: 2px dashed #000;
		background: #fff;
		color: #000;
		padding: 0.6rem 0.9rem;
		border-radius: 8px;
		font-size: 0.85rem;
		font-weight: 700;
		text-transform: uppercase;
		text-decoration: underline wavy;
		text-underline-offset: 4px;
	}
	.btn-container {
		margin-top: 0.5rem;
		display: flex;
		justify-content: flex-end;
	}
</style>
