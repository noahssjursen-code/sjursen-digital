<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { page } from '$app/stores';
	import Card from '$shared/Card.svelte';
	import Badge from '$shared/Badge.svelte';
	import StateBadge from '$lib/StateBadge.svelte';
	import Sparkline from '$lib/Sparkline.svelte';
	import { api, fmtTime, timeAgo } from '$lib/api';

	type Instance = {
		id: number;
		namespace: string;
		name: string;
		entity_type: string;
		state: string;
		last_values: Record<string, unknown>;
		last_seen_at: string | null;
	};
	type LogRow = {
		id: number;
		ts: string;
		received_at: string;
		values: Record<string, unknown>;
	};

	let instance: Instance | null = null;
	let logs: LogRow[] = [];
	let error = '';
	let timer: ReturnType<typeof setInterval>;

	$: id = $page.params.id;

	async function refresh() {
		try {
			[instance, logs] = await Promise.all([
				api<Instance>(`/api/instances/${id}`),
				api<LogRow[]>(`/api/instances/${id}/logs?limit=200`)
			]);
			error = '';
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	// One sparkline per numeric field, oldest -> newest.
	$: numericSeries = (() => {
		const series: Record<string, number[]> = {};
		for (const row of [...logs].reverse()) {
			for (const [k, v] of Object.entries(row.values ?? {})) {
				if (typeof v === 'number') (series[k] ??= []).push(v);
			}
		}
		return series;
	})();

	onMount(() => {
		refresh();
		timer = setInterval(refresh, 5000);
	});
	onDestroy(() => clearInterval(timer));
</script>

{#if error}
	<Card title="Error"><p class="error">{error}</p></Card>
{:else if !instance}
	<p>Loading…</p>
{:else}
	<div class="head">
		<div>
			<h2>{instance.name}</h2>
			<div class="meta">
				<Badge>{instance.entity_type}</Badge>
				<span class="ns">{instance.namespace}</span>
				<span class="seen">last seen {timeAgo(instance.last_seen_at)}</span>
			</div>
		</div>
		<StateBadge state={instance.state} />
	</div>

	<Card title="Last known values">
		{#if Object.keys(instance.last_values ?? {}).length === 0}
			<p>No data yet.</p>
		{:else}
			<div class="values">
				{#each Object.entries(instance.last_values) as [field, value]}
					<div class="value-cell">
						<span class="field">{field}</span>
						<span class="val">{JSON.stringify(value)}</span>
					</div>
				{/each}
			</div>
		{/if}
	</Card>

	{#each Object.entries(numericSeries) as [field, series]}
		<Card title={field}>
			<Sparkline points={series} />
		</Card>
	{/each}

	<Card title="Recent logs">
		{#if logs.length === 0}
			<p>No logs yet.</p>
		{:else}
			<div class="log-table">
				{#each logs as row (row.id)}
					<div class="log-row">
						<span class="log-ts" title={fmtTime(row.ts)}>{fmtTime(row.ts)}</span>
						<code class="log-values">{JSON.stringify(row.values)}</code>
					</div>
				{/each}
			</div>
		{/if}
	</Card>
{/if}

<style>
	h2 {
		margin: 0;
		font-size: 1.4rem;
		font-weight: 900;
		text-transform: uppercase;
		letter-spacing: -0.02em;
	}
	.head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}
	.meta {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		margin-top: 0.5rem;
		flex-wrap: wrap;
	}
	.ns {
		font-family: monospace;
		font-size: 0.8rem;
		font-weight: 700;
	}
	.seen {
		font-size: 0.8rem;
		opacity: 0.6;
	}
	.error {
		font-family: monospace;
		white-space: pre-wrap;
	}

	.values {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
		gap: 0.75rem;
	}
	.value-cell {
		border: 2px solid #000;
		border-radius: 10px 6px 12px 6px/6px 12px 6px 10px;
		padding: 0.5rem 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		background: #fff;
	}
	.field {
		font-size: 0.7rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		opacity: 0.7;
	}
	.val {
		font-family: monospace;
		font-weight: 900;
		font-size: 1.2rem;
		word-break: break-all;
	}

	.log-table {
		max-height: 420px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
	}
	.log-row {
		display: flex;
		gap: 1rem;
		padding: 0.35rem 0;
		border-bottom: 1px dashed #00000033;
		font-size: 0.85rem;
		align-items: baseline;
	}
	.log-ts {
		white-space: nowrap;
		opacity: 0.7;
		font-family: monospace;
	}
	.log-values {
		font-family: monospace;
		word-break: break-all;
	}
</style>
