<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { base } from '$app/paths';
	import Card from '$shared/Card.svelte';
	import Button from '$shared/Button.svelte';
	import Badge from '$shared/Badge.svelte';
	import StateBadge from '$lib/StateBadge.svelte';
	import { api, fmtTime, timeAgo } from '$lib/api';

	type Decision = {
		id: number;
		action: string;
		source: string;
		confidence: number | null;
		reason: string;
		delivery_status: string;
	};
	type Alert = {
		id: number;
		namespace: string;
		instance_id: number;
		instance_name: string | null;
		entity_type: string | null;
		kind: string;
		summary: string;
		status: string;
		opened_at: string;
		resolved_at: string | null;
		decision: Decision | null;
	};

	let alerts: Alert[] = [];
	let error = '';
	let loading = true;
	let showResolved = false;
	let timer: ReturnType<typeof setInterval>;

	async function refresh() {
		try {
			alerts = await api<Alert[]>('/api/alerts');
			error = '';
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
		loading = false;
	}

	async function ack(id: number) {
		await api(`/api/alerts/${id}/ack`, { method: 'POST' });
		await refresh();
	}

	$: visible = showResolved ? alerts : alerts.filter((a) => a.status !== 'resolved');
	$: activeCount = alerts.filter((a) => a.status === 'active').length;

	onMount(() => {
		refresh();
		timer = setInterval(refresh, 5000);
	});
	onDestroy(() => clearInterval(timer));
</script>

<div class="page-head">
	<h2>Alert feed</h2>
	<div class="head-actions">
		<label class="toggle">
			<input type="checkbox" bind:checked={showResolved} />
			show resolved
		</label>
		<Button on:click={refresh}>Refresh</Button>
	</div>
</div>

{#if error}
	<Card title="Error"><p class="error">{error}</p></Card>
{:else if loading}
	<p>Loading…</p>
{:else if visible.length === 0}
	<Card title={activeCount === 0 ? 'All quiet' : 'Nothing to show'}>
		<p>
			No {showResolved ? '' : 'unresolved '}alerts. Komfyrvakt is watching. Register entity types
			and instances via the API, then push logs to <code>/api/logs</code>.
		</p>
	</Card>
{:else}
	{#each visible as alert (alert.id)}
		<Card>
			<div class="alert-row">
				<div class="alert-main">
					<div class="alert-meta">
						<StateBadge state={alert.status} />
						<Badge>{alert.kind}</Badge>
						<span class="ns">{alert.namespace}</span>
						<span class="when" title={fmtTime(alert.opened_at)}>{timeAgo(alert.opened_at)}</span>
					</div>
					<p class="summary">{alert.summary}</p>
					{#if alert.instance_name}
						<a class="instance-link" href="{base}/instances/{alert.instance_id}">
							{alert.instance_name} ({alert.entity_type})
						</a>
					{/if}
					{#if alert.decision}
						<div class="decision">
							<span class="decision-action">{alert.decision.action}</span>
							<span class="decision-source">
								via {alert.decision.source}{alert.decision.confidence != null
									? ` (${Math.round(alert.decision.confidence * 100)}%)`
									: ''}
							</span>
							{#if alert.decision.reason}
								<p class="decision-reason">{alert.decision.reason}</p>
							{/if}
						</div>
					{/if}
				</div>
				<div class="alert-actions">
					{#if alert.status === 'active'}
						<Button on:click={() => ack(alert.id)}>Ack</Button>
					{/if}
				</div>
			</div>
		</Card>
	{/each}
{/if}

<style>
	.page-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}
	h2 {
		margin: 0;
		font-size: 1.4rem;
		font-weight: 900;
		text-transform: uppercase;
		letter-spacing: -0.02em;
	}
	.head-actions {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	.toggle {
		font-size: 0.8rem;
		font-weight: 700;
		text-transform: uppercase;
		display: flex;
		align-items: center;
		gap: 0.4rem;
		cursor: pointer;
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

	.alert-row {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
	}
	.alert-main {
		flex: 1;
		min-width: 0;
	}
	.alert-meta {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		flex-wrap: wrap;
	}
	.ns {
		font-family: monospace;
		font-size: 0.8rem;
		font-weight: 700;
	}
	.when {
		font-size: 0.8rem;
		opacity: 0.6;
	}
	.summary {
		margin: 0.6rem 0 0.2rem;
		font-weight: 700;
		font-size: 1.05rem;
	}
	.instance-link {
		color: #000;
		font-size: 0.85rem;
		font-weight: 700;
	}
	.decision {
		margin-top: 0.8rem;
		border: 2px dashed #000;
		border-radius: 10px 6px 12px 6px/6px 12px 6px 10px;
		padding: 0.6rem 0.9rem;
	}
	.decision-action {
		font-family: monospace;
		font-weight: 900;
		background: #000;
		color: #fff;
		padding: 0.15rem 0.5rem;
		border-radius: 4px;
	}
	.decision-source {
		font-size: 0.8rem;
		text-transform: uppercase;
		font-weight: 700;
		margin-left: 0.5rem;
	}
	.decision-reason {
		margin: 0.5rem 0 0;
		font-size: 0.9rem;
		opacity: 0.85;
	}
</style>
