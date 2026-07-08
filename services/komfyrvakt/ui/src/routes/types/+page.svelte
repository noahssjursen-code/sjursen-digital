<script lang="ts">
	import { onMount } from 'svelte';
	import Card from '$shared/Card.svelte';
	import Badge from '$shared/Badge.svelte';
	import { api } from '$lib/api';

	type NamespaceInfo = { name: string };
	type EntityType = {
		namespace: string;
		name: string;
		description: string;
		version: number;
		expected_every_seconds: number | null;
		fields: Record<string, { type?: string; sensitive?: boolean }>;
		constraints: Array<{ name?: string; for_seconds?: number }>;
		actions: Array<{ id: string; description?: string }>;
		default_action: string | null;
	};

	let types: EntityType[] = [];
	let error = '';
	let loading = true;

	async function refresh() {
		try {
			const namespaces = await api<NamespaceInfo[]>('/api/namespaces');
			const perNs = await Promise.all(
				namespaces.map((ns) => api<EntityType[]>(`/api/ns/${ns.name}/entity-types`))
			);
			types = perNs.flat();
			error = '';
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
		loading = false;
	}

	onMount(refresh);
</script>

<h2>Entity types</h2>

{#if error}
	<Card title="Error"><p class="error">{error}</p></Card>
{:else if loading}
	<p>Loading…</p>
{:else if types.length === 0}
	<Card title="No entity types yet">
		<p>
			Entity types are registered code-first:
			<code>PUT /api/ns/&#123;namespace&#125;/entity-types/&#123;name&#125;</code> with fields,
			constraints and actions. See the design doc or <code>/docs</code>.
		</p>
	</Card>
{:else}
	{#each types as t (t.namespace + '/' + t.name)}
		<Card title={t.name}>
			<div class="meta">
				<Badge>v{t.version}</Badge>
				<span class="ns">{t.namespace}</span>
				{#if t.expected_every_seconds}
					<span class="interval">expects data every {t.expected_every_seconds}s</span>
				{/if}
			</div>
			{#if t.description}
				<p class="desc">{t.description}</p>
			{/if}

			<div class="section">
				<span class="label">Fields</span>
				<div class="chips">
					{#each Object.entries(t.fields ?? {}) as [field, spec]}
						<span class="chip">
							{field}: {spec.type ?? 'number'}{spec.sensitive ? ' [sensitive]' : ''}
						</span>
					{/each}
				</div>
			</div>

			<div class="section">
				<span class="label">Constraints</span>
				<div class="chips">
					{#each t.constraints ?? [] as c, i}
						<span class="chip">
							{c.name ?? `#${i}`}{c.for_seconds ? ` (${c.for_seconds}s)` : ''}
						</span>
					{/each}
				</div>
			</div>

			<div class="section">
				<span class="label">Actions</span>
				<div class="chips">
					{#each t.actions ?? [] as a}
						<span class="chip" class:default={a.id === t.default_action} title={a.description}>
							{a.id}
						</span>
					{/each}
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
	.meta {
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
	.interval {
		font-size: 0.8rem;
		opacity: 0.6;
	}
	.desc {
		margin: 0.6rem 0 0;
		font-size: 0.95rem;
	}
	.section {
		margin-top: 0.9rem;
	}
	.label {
		display: block;
		font-size: 0.7rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		opacity: 0.7;
		margin-bottom: 0.35rem;
	}
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}
	.chip {
		font-family: monospace;
		font-size: 0.8rem;
		font-weight: 700;
		border: 2px solid #000;
		border-radius: 10px 6px 12px 6px/6px 12px 6px 10px;
		padding: 0.15rem 0.5rem;
		background: #fff;
	}
	.chip.default {
		background: #000;
		color: #fff;
	}
</style>
