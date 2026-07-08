<script lang="ts">
	import { onMount } from 'svelte';
	import Card from '$shared/Card.svelte';
	import Button from '$shared/Button.svelte';

	type SystemModule = {
		id: string;
		name: string;
		description: string;
		installed: boolean;
		launch_url: string;
	};

	let modules: SystemModule[] = [];
	let error = '';
	let loading = true;

	async function refresh() {
		try {
			const res = await fetch('/api/system/modules');
			if (!res.ok) throw new Error(await res.text());
			modules = await res.json();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
		loading = false;
	}

	onMount(refresh);
</script>

<h2>Application Launcher</h2>

{#if error}
	<Card title="Error"><p class="error">{error}</p></Card>
{:else if loading}
	<p>Loading application suite…</p>
{:else if modules.length === 0}
	<Card title="Suite is Empty">
		<p>No software modules detected. Connect with your development team.</p>
	</Card>
{:else}
	<p class="intro">
		Welcome to your Sjursen Digital software suite. Select an application module below to launch the dashboard.
	</p>

	<div class="modules-grid">
		{#each modules as mod (mod.id)}
			<Card title={mod.name}>
				<div class="module-card">
					<p class="desc">{mod.description}</p>
					
					<div class="status-line">
						<div class="action">
							{#if mod.installed}
								<a href={mod.launch_url} class="launch-link">
									<Button>Launch App</Button>
								</a>
							{:else}
								<Button disabled={true}>Coming Soon</Button>
							{/if}
						</div>
					</div>
				</div>
			</Card>
		{/each}
	</div>
{/if}

<style>
	h2 {
		margin: 0 0 0.5rem;
		font-size: 1.5rem;
		font-weight: 700;
		letter-spacing: -0.02em;
		color: var(--sd-text);
	}
	.intro {
		font-size: 0.95rem;
		margin-top: 0;
		margin-bottom: 2.5rem;
		line-height: 1.5;
		color: var(--sd-text-muted);
	}
	.error {
		font-family: monospace;
		white-space: pre-wrap;
	}

	.modules-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: 1.5rem;
	}

	.module-card {
		display: flex;
		flex-direction: column;
		height: 100%;
		justify-content: space-between;
	}

	.desc {
		margin: 0 0 1.5rem;
		font-size: 0.95rem;
		line-height: 1.5;
		color: var(--sd-text-muted);
	}

	.status-line {
		display: flex;
		justify-content: flex-end;
		align-items: center;
		border-top: 1px dashed var(--sd-border);
		padding-top: 1rem;
		margin-top: auto;
	}

	.launch-link {
		text-decoration: none;
	}
</style>
