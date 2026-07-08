<script lang="ts">
	import { onMount } from 'svelte';
	import Card from '$shared/Card.svelte';
	import Button from '$shared/Button.svelte';
	import Badge from '$shared/Badge.svelte';
	import { api } from '$lib/api';

	type SystemModule = {
		id: string;
		name: string;
		description: string;
		installed: boolean;
		licensed: boolean;
		launch_url: string;
	};

	let modules: SystemModule[] = [];
	let error = '';
	let loading = true;

	async function refresh() {
		try {
			modules = await api<SystemModule[]>('/api/system/modules');
			error = '';
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
		Sjursen Digital provides modular enterprise services for businesses.
		Select a module to launch. Admin and viewing dashboards are fully self-contained.
	</p>

	<div class="modules-grid">
		{#each modules as mod (mod.id)}
			<Card title={mod.name}>
				<div class="module-card">
					<p class="desc">{mod.description}</p>
					
					<div class="status-line">
						<div class="badges">
							{#if mod.licensed}
								<span class="licensed-badge">Licensed</span>
							{:else}
								<span class="paywall-badge">Paywalled</span>
							{/if}

							{#if mod.installed}
								<Badge>Installed</Badge>
							{:else}
								<span class="uninstalled-badge">Coming Soon</span>
							{/if}
						</div>

						<div class="action">
							{#if mod.installed && mod.licensed}
								<a href={mod.launch_url} class="launch-link">
									<Button>Launch</Button>
								</a>
							{:else if mod.installed && !mod.licensed}
								<a href="/keys" class="unlock-hint">
									<Button disabled={true}>License Required</Button>
								</a>
							{:else}
								<Button disabled={true}>Not Available</Button>
							{/if}
						</div>
					</div>

					{#if !mod.licensed && mod.installed}
						<p class="hint">
							Need access? Generate a cryptographically signed license in your terminal and 
							paste it in the <a class="inline-link" href="/keys">Licensing Portal</a>.
						</p>
					{/if}
				</div>
			</Card>
		{/each}
	</div>
{/if}

<style>
	h2 {
		margin: 0 0 1.5rem;
		font-size: 1.4rem;
		font-weight: 900;
		text-transform: uppercase;
		letter-spacing: -0.02em;
	}
	.intro {
		font-size: 1rem;
		margin-top: 0;
		margin-bottom: 2rem;
		line-height: 1.5;
		opacity: 0.85;
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
		font-size: 1rem;
		line-height: 1.4;
		opacity: 0.9;
	}

	.status-line {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: 1rem;
		border-top: 1px dashed #00000033;
		padding-top: 1rem;
	}

	.badges {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.launch-link {
		text-decoration: none;
	}

	.licensed-badge {
		display: inline-block;
		font-weight: 800;
		text-transform: uppercase;
		font-size: 0.7rem;
		letter-spacing: 0.05em;
		padding: 0.2rem 0.6rem;
		border: 2px solid #000;
		border-radius: 6px 12px 6px 12px/12px 6px 12px 6px;
		background: #000;
		color: #fff;
	}

	.paywall-badge {
		display: inline-block;
		font-weight: 800;
		text-transform: uppercase;
		font-size: 0.7rem;
		letter-spacing: 0.05em;
		padding: 0.2rem 0.6rem;
		border: 2px dashed #000;
		border-radius: 6px 12px 6px 12px/12px 6px 12px 6px;
		background: #fff;
		color: #000;
	}

	.uninstalled-badge {
		display: inline-block;
		font-weight: 800;
		text-transform: uppercase;
		font-size: 0.7rem;
		letter-spacing: 0.05em;
		padding: 0.2rem 0.6rem;
		border: 2px solid #000;
		border-radius: 6px 12px 6px 12px/12px 6px 12px 6px;
		background: repeating-linear-gradient(45deg, #000, #000 4px, #fff 4px, #fff 8px);
		color: #fff;
		text-shadow: 1px 1px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000;
	}

	.hint {
		margin-top: 1rem;
		font-size: 0.8rem;
		line-height: 1.4;
		opacity: 0.75;
		font-style: italic;
	}

	.inline-link {
		color: #000;
		font-weight: 700;
		text-decoration: underline;
	}
	.inline-link:hover {
		opacity: 0.8;
	}
</style>
