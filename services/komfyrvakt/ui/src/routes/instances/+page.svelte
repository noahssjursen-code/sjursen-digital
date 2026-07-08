<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { base } from '$app/paths';
	import Card from '$shared/Card.svelte';
	import StateBadge from '$lib/StateBadge.svelte';
	import { api, timeAgo } from '$lib/api';

	type Instance = {
		id: number;
		namespace: string;
		name: string;
		entity_type: string;
		state: string;
		last_values: Record<string, unknown>;
		last_seen_at: string | null;
	};

	let instances: Instance[] = [];
	let error = '';
	let loading = true;
	let timer: ReturnType<typeof setInterval>;

	async function refresh() {
		try {
			instances = await api<Instance[]>('/api/instances');
			error = '';
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
		loading = false;
	}

	onMount(() => {
		refresh();
		timer = setInterval(refresh, 5000);
	});
	onDestroy(() => clearInterval(timer));
</script>

<h2>Instances</h2>

{#if error}
	<Card title="Error"><p class="error">{error}</p></Card>
{:else if loading}
	<p>Loading…</p>
{:else if instances.length === 0}
	<Card title="No instances yet">
		<p>
			Register one with
			<code>PUT /api/ns/&#123;namespace&#125;/instances/&#123;name&#125;</code> and start pushing logs.
		</p>
	</Card>
{:else}
	{#each instances as inst (inst.id)}
		<a class="row-link" href="{base}/instances/{inst.id}">
			<Card>
				<div class="row">
					<div>
						<div class="title-line">
							<span class="name">{inst.name}</span>
							<span class="ns">{inst.namespace}</span>
						</div>
						<div class="sub">
							{inst.entity_type} · last seen {timeAgo(inst.last_seen_at)}
						</div>
					</div>
					<StateBadge state={inst.state} />
				</div>
			</Card>
		</a>
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
	.row-link {
		text-decoration: none;
		color: inherit;
		display: block;
	}
	.row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
	}
	.title-line {
		display: flex;
		align-items: baseline;
		gap: 0.6rem;
	}
	.name {
		font-weight: 900;
		font-size: 1.1rem;
	}
	.ns {
		font-family: monospace;
		font-size: 0.8rem;
		opacity: 0.7;
	}
	.sub {
		font-size: 0.85rem;
		opacity: 0.7;
		margin-top: 0.2rem;
	}
</style>
