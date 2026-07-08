<script lang="ts">
	import { onMount } from 'svelte';
	import Card from '$shared/Card.svelte';
	import Button from '$shared/Button.svelte';
	import Badge from '$shared/Badge.svelte';
	import { api, fmtTime } from '$lib/api';

	type ApiKeyRow = {
		id: number;
		name: string;
		key: string | null;
		role: string;
		namespace: string;
		revoked: boolean;
		created_at: string;
	};

	let keys: ApiKeyRow[] = [];
	let error = '';
	let loading = true;

	let revealed: Record<number, boolean> = {};
	let copied: number | null = null;

	let newName = '';
	let newRole = 'ingest';
	let newNamespace = '*';
	let creating = false;

	async function refresh() {
		try {
			keys = await api<ApiKeyRow[]>('/api/keys');
			error = '';
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
		loading = false;
	}

	async function create() {
		if (!newName.trim()) return;
		creating = true;
		try {
			const made = await api<ApiKeyRow>('/api/keys', {
				method: 'POST',
				body: JSON.stringify({
					name: newName.trim(),
					role: newRole,
					namespace: newNamespace.trim() || '*'
				})
			});
			newName = '';
			await refresh();
			revealed = { ...revealed, [made.id]: true };
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
		creating = false;
	}

	async function remove(id: number) {
		await api(`/api/keys/${id}`, { method: 'DELETE' });
		await refresh();
	}

	async function copy(k: ApiKeyRow) {
		if (!k.key) return;
		await navigator.clipboard.writeText(k.key);
		copied = k.id;
		setTimeout(() => (copied = null), 1500);
	}

	$: visible = keys.filter((k) => !k.revoked);

	onMount(refresh);
</script>

<h2>API keys</h2>

<Card title="New key">
	<p class="hint">
		Keys are for machines pushing data to <code>POST /api/logs</code>. Ingest keys can only
		write logs in their namespace; admin keys can do everything. The dashboard itself needs
		no key.
	</p>
	<div class="form">
		<input
			placeholder="name (e.g. fridge-sensors-prod)"
			bind:value={newName}
			on:keydown={(e) => e.key === 'Enter' && create()}
		/>
		<select bind:value={newRole}>
			<option value="ingest">ingest</option>
			<option value="admin">admin</option>
		</select>
		<input class="ns" placeholder="namespace (* = all)" bind:value={newNamespace} />
		<Button on:click={create} disabled={creating || !newName.trim()}>Generate</Button>
	</div>
</Card>

{#if error}
	<Card title="Error"><p class="error">{error}</p></Card>
{:else if loading}
	<p>Loading…</p>
{:else if visible.length === 0}
	<Card title="No keys yet"><p>Generate one above to start pushing logs.</p></Card>
{:else}
	{#each visible as k (k.id)}
		<Card>
			<div class="key-row">
				<div class="key-main">
					<div class="key-meta">
						<span class="key-name">{k.name}</span>
						<Badge>{k.role}</Badge>
						<span class="ns-label">{k.namespace}</span>
						<span class="when">{fmtTime(k.created_at)}</span>
					</div>
					<div class="key-value">
						{#if k.key === null}
							<span class="legacy">created before key storage — delete and regenerate to view</span>
						{:else if revealed[k.id]}
							<code class="raw">{k.key}</code>
						{:else}
							<code class="raw masked">kv_{'•'.repeat(24)}</code>
						{/if}
					</div>
				</div>
				<div class="key-actions">
					{#if k.key !== null}
						<Button on:click={() => (revealed = { ...revealed, [k.id]: !revealed[k.id] })}>
							{revealed[k.id] ? 'Hide' : 'View'}
						</Button>
						<Button on:click={() => copy(k)}>{copied === k.id ? 'Copied' : 'Copy'}</Button>
					{/if}
					<Button on:click={() => remove(k.id)}>Delete</Button>
				</div>
			</div>
		</Card>
	{/each}
{/if}

<style>
	h2 {
		margin: 0 0 1.5rem;
		font-size: 1.4rem;
		font-weight: 900;
		text-transform: uppercase;
		letter-spacing: -0.02em;
	}
	.hint {
		margin-top: 0;
		font-size: 0.95rem;
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

	.form {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}
	input,
	select {
		border: 2px solid #000;
		border-radius: 12px 6px 10px 6px/6px 10px 6px 8px;
		padding: 0.5rem 0.9rem;
		font-size: 0.95rem;
		background: #fff;
		font-family: inherit;
	}
	input:focus,
	select:focus {
		outline: none;
		box-shadow: 2px 2px 0 #000;
	}
	input {
		flex: 2;
		min-width: 200px;
	}
	input.ns {
		flex: 1;
		min-width: 140px;
		font-family: monospace;
	}

	.key-row {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		flex-wrap: wrap;
	}
	.key-main {
		flex: 1;
		min-width: 0;
	}
	.key-meta {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		flex-wrap: wrap;
	}
	.key-name {
		font-weight: 900;
		font-size: 1.05rem;
	}
	.ns-label {
		font-family: monospace;
		font-size: 0.8rem;
		font-weight: 700;
	}
	.when {
		font-size: 0.8rem;
		opacity: 0.6;
	}
	.key-value {
		margin-top: 0.6rem;
	}
	.raw {
		background: #fff;
		color: #000;
		border: 2px solid #000;
		border-radius: 8px 5px 9px 5px/5px 9px 5px 8px;
		padding: 0.35rem 0.6rem;
		font-family: monospace;
		font-size: 0.85rem;
		word-break: break-all;
		display: inline-block;
	}
	.raw.masked {
		letter-spacing: 0.1em;
		opacity: 0.55;
	}
	.legacy {
		font-size: 0.85rem;
		opacity: 0.6;
		font-style: italic;
	}
	.key-actions {
		display: flex;
		gap: 0.5rem;
		align-items: flex-start;
		flex-wrap: wrap;
	}
</style>
