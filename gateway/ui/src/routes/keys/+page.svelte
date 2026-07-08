<script lang="ts">
	import { onMount } from 'svelte';
	import Card from '$shared/Card.svelte';
	import Button from '$shared/Button.svelte';
	import Badge from '$shared/Badge.svelte';
	import { api } from '$lib/api';

	type LicenseInfo = {
		active: boolean;
		dev_mode: boolean;
		error?: string;
		customer_name?: string;
		customer_email?: string;
		modules?: Record<string, boolean>;
		expires_at?: string | null;
	};

	let info: LicenseInfo | null = null;
	let inputKey = '';
	let error = '';
	let success = '';
	let loading = true;
	let activating = false;

	async function refresh() {
		try {
			info = await api<LicenseInfo>('/api/system/license');
			error = '';
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
		loading = false;
	}

	async function activate() {
		if (!inputKey.trim()) return;
		activating = true;
		error = '';
		success = '';
		try {
			const res = await api<{ message: string }>('/api/system/license', {
				method: 'POST',
				body: JSON.stringify({ license_key: inputKey.trim() })
			});
			success = res.message;
			inputKey = '';
			await refresh();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
			try {
				const parsed = JSON.parse(error);
				if (parsed.detail) error = parsed.detail;
			} catch {}
		}
		activating = false;
	}

	async function deactivate() {
		if (!confirm('Are you sure you want to deactivate this license? This will lock all modular webapps.')) return;
		try {
			await api('/api/system/license', { method: 'DELETE' });
			await refresh();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	function fmtDate(iso: string | null | undefined): string {
		if (!iso) return 'Lifetime (Never Expires)';
		const d = new Date(iso);
		return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
	}

	onMount(refresh);
</script>

<div class="head">
	<h2>Modular Licensing</h2>
	{#if info?.dev_mode}
		<Badge>Developer Bypass Active</Badge>
	{/if}
</div>

{#if loading}
	<p>Loading licensing status…</p>
{:else if info}
	{#if error}
		<Card title="Error"><p class="error">{error}</p></Card>
	{/if}

	{#if info.active}
		<Card title="Active License Certificate">
			<div class="license-info">
				<div class="info-row">
					<span class="label">Customer</span>
					<span class="val">{info.customer_name}</span>
				</div>
				<div class="info-row">
					<span class="label">Email</span>
					<span class="val">{info.customer_email}</span>
				</div>
				<div class="info-row">
					<span class="label">Expiration</span>
					<span class="val">{fmtDate(info.expires_at)}</span>
				</div>
			</div>

			<div class="unlocked-section">
				<h3>Unlocked Entitlements</h3>
				<div class="module-chips">
					{#each Object.entries(info.modules ?? {}) as [mod, enabled]}
						{#if enabled}
							<div class="chip">
								<span class="check">✓</span>
								<span class="mod-name">{mod}</span>
							</div>
						{/if}
					{/each}
				</div>
			</div>

			<div class="deactivate-container">
				<Button on:click={deactivate}>Deactivate Key</Button>
			</div>
		</Card>
	{:else}
		<Card title="Activation Required">
			<p class="desc">
				Sjursen Digital products are distributed in modular, self-hostable packages.
				To boot individual services like <strong>Komfyrvakt</strong> or <strong>Obsero</strong>, 
				paste your cryptographically signed license token below.
			</p>

			{#if info.dev_mode}
				<div class="dev-banner">
					<strong>LOCAL DEVELOPER MODE</strong>
					<p>
						Because you have <code>SD_DEV_MODE=1</code> set in your environment variables, 
						all modules are fully unlocked locally for testing and playing. 
						You do not need to paste a license key.
					</p>
				</div>
			{/if}

			<div class="activate-form">
				{#if success}
					<p class="success">{success}</p>
				{/if}

				<div class="input-group">
					<label for="license-input">Paste Cryptographic License Token</label>
					<textarea
						id="license-input"
						rows="6"
						placeholder="eyJhbGciOiJSUzI1NiIs..."
						bind:value={inputKey}
						disabled={activating}
					></textarea>
				</div>

				<div class="btn-container">
					<Button on:click={activate} disabled={activating || !inputKey.trim()}>
						{activating ? 'Verifying Signature…' : 'Activate Suite'}
					</Button>
				</div>
			</div>
		</Card>

		<Card title="How to generate keys (Dev / Test)">
			<p class="hint">
				As the software developer at Sjursen Digital, you have the RSA signing keys 
				right in your repository! You can issue license keys for any modules instantly by 
				running this script in your terminal:
			</p>
			<code>python tools/generate_license.py "Customer Name" "email@domain.com" "komfyrvakt,obsero"</code>
		</Card>
	{/if}
{/if}

<style>
	.head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		flex-wrap: wrap;
		gap: 1rem;
	}
	h2 {
		margin: 0;
		font-size: 1.4rem;
		font-weight: 900;
		text-transform: uppercase;
		letter-spacing: -0.02em;
	}
	h3 {
		margin-top: 1.5rem;
		margin-bottom: 0.6rem;
		font-size: 0.8rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		opacity: 0.7;
	}
	.desc {
		font-size: 1rem;
		margin-top: 0;
		margin-bottom: 1.5rem;
		line-height: 1.5;
	}
	.error {
		font-family: monospace;
		white-space: pre-wrap;
	}
	code {
		background: #000;
		color: #fff;
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		font-size: 0.85rem;
	}

	.license-info {
		display: grid;
		gap: 1rem;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		margin-bottom: 1.5rem;
	}
	.info-row {
		display: flex;
		flex-direction: column;
		border: 2px solid #000;
		border-radius: 10px 6px 12px 6px/6px 12px 6px 10px;
		padding: 0.6rem 0.9rem;
		background: #fff;
	}
	.label {
		font-size: 0.7rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		opacity: 0.6;
	}
	.val {
		font-size: 1.1rem;
		font-weight: 900;
		margin-top: 0.2rem;
	}

	.module-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.6rem;
	}
	.chip {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		border: 2px solid #000;
		border-radius: 8px 12px 8px 12px/12px 8px 12px 8px;
		padding: 0.4rem 0.75rem;
		background: #fff;
		font-weight: 800;
		text-transform: uppercase;
		font-size: 0.85rem;
	}
	.check {
		font-size: 1.1rem;
		font-weight: 900;
	}

	.deactivate-container {
		margin-top: 2rem;
		display: flex;
		justify-content: flex-end;
	}

	.dev-banner {
		background: #000;
		color: #fff;
		border: 2px solid #000;
		border-radius: 12px 6px 10px 6px/6px 10px 6px 8px;
		padding: 1rem;
		margin-bottom: 1.5rem;
	}
	.dev-banner strong {
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-size: 0.85rem;
		border-bottom: 1px dashed #fff;
		padding-bottom: 0.2rem;
		display: inline-block;
	}
	.dev-banner p {
		margin: 0.5rem 0 0;
		font-size: 0.9rem;
		line-height: 1.4;
		opacity: 0.9;
	}

	.activate-form {
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
	}
	.input-group {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	textarea {
		border: 2px solid #000;
		border-radius: 12px 6px 10px 6px/6px 10px 6px 8px;
		padding: 0.6rem 0.9rem;
		font-family: monospace;
		font-size: 0.85rem;
		background: #fff;
		resize: vertical;
	}
	textarea:focus {
		outline: none;
		box-shadow: 2px 2px 0 #000;
	}
	.btn-container {
		display: flex;
		justify-content: flex-end;
	}
	.success {
		font-weight: 800;
		text-transform: uppercase;
		text-decoration: underline wavy;
		text-underline-offset: 4px;
		margin: 0 0 1rem;
	}
	.hint {
		margin-top: 0;
		font-size: 0.95rem;
	}
</style>
