<script lang="ts">
	import { onMount } from 'svelte';
	import Card from '$shared/Card.svelte';
	import Button from '$shared/Button.svelte';
	import { api, getApiKey, setApiKey } from '$lib/api';

	let key = '';
	let status: 'unknown' | 'ok' | 'bad' = 'unknown';
	let checking = false;

	async function save() {
		setApiKey(key);
		await test();
	}

	async function test() {
		checking = true;
		try {
			await api('/api/instances');
			status = 'ok';
		} catch {
			status = 'bad';
		}
		checking = false;
	}

	onMount(() => {
		key = getApiKey();
		if (key) test();
	});
</script>

<h2>Settings</h2>

<Card title="API key">
	<p>
		The dashboard talks to the Komfyrvakt API with an admin key. On first startup the server
		prints a bootstrap admin key to its log — paste it here. It is stored only in this browser.
	</p>
	<div class="key-row">
		<input
			type="password"
			bind:value={key}
			placeholder="kv_..."
			on:keydown={(e) => e.key === 'Enter' && save()}
		/>
		<Button on:click={save} disabled={checking}>Save & test</Button>
	</div>
	{#if status === 'ok'}
		<p class="status ok">Key works. You're in.</p>
	{:else if status === 'bad'}
		<p class="status bad">Key rejected by the server.</p>
	{/if}
</Card>

<Card title="Getting data in">
	<p>Minimal flow (all admin endpoints, see <code>/docs</code> for schemas):</p>
	<ol>
		<li><code>PUT /api/ns/&#123;ns&#125;/entity-types/&#123;name&#125;</code> — declare fields, constraints, actions</li>
		<li><code>PUT /api/ns/&#123;ns&#125;/instances/&#123;name&#125;</code> — register the thing being watched</li>
		<li><code>POST /api/logs</code> — push data (use a scoped ingest key from <code>POST /api/keys</code>)</li>
		<li><code>GET /api/decisions?since=&#123;cursor&#125;</code> — poll decisions, or configure a namespace webhook</li>
	</ol>
</Card>

<style>
	h2 {
		margin: 0 0 1.5rem;
		font-size: 1.4rem;
		font-weight: 900;
		text-transform: uppercase;
		letter-spacing: -0.02em;
	}
	.key-row {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}
	input {
		flex: 1;
		min-width: 240px;
		border: 2px solid #000;
		border-radius: 12px 6px 10px 6px/6px 10px 6px 8px;
		padding: 0.5rem 0.9rem;
		font-family: monospace;
		font-size: 0.95rem;
		background: #fff;
	}
	input:focus {
		outline: none;
		box-shadow: 2px 2px 0 #000;
	}
	.status {
		font-weight: 800;
		text-transform: uppercase;
		font-size: 0.8rem;
		margin-bottom: 0;
	}
	.status.bad {
		text-decoration: underline wavy;
	}
	code {
		background: #000;
		color: #fff;
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		font-size: 0.85rem;
	}
	ol {
		margin: 0.5rem 0 0;
		padding-left: 1.4rem;
		line-height: 2;
	}
</style>
