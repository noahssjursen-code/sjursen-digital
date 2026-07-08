<script lang="ts">
  import Card from "../lib/components/Card.svelte";
  import Button from "../lib/components/Button.svelte";
  import Badge from "../lib/components/Badge.svelte";

  // Basic state for the dashboard
  let status = "online";
  let activeStreams = 0;
  let recentAlerts = [];

  async function fetchStatus() {
    try {
      const res = await fetch("/api/streams");
      if (res.ok) {
        const streams = await res.json();
        activeStreams = streams.length;
      }
    } catch (e) {
      console.error("Could not fetch streams", e);
    }
  }

  import { onMount } from "svelte";
  onMount(() => {
    fetchStatus();
  });
</script>

<main class="dashboard">
  <header class="header">
    <div class="brand">
      <!-- Embedded hand-drawn Normal-style brand logo -->
      <svg class="logo" viewBox="0 0 100 100" fill="none" role="img" aria-label="Sjursen Digital">
        <path
          d="M 46,25 C 33,25 25,32 25,41 C 25,51 45,49 45,59 C 45,68 37,75 24,75 L 60,75 C 73,75 75,64 75,50 C 75,36 73,25 60,25 Z"
          stroke="currentColor"
          stroke-width="6.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <div class="brand-text">
        <h1>Komfyrvakt</h1>
        <Badge>Self-Hosted</Badge>
      </div>
    </div>
    
    <div class="system-status {status}">
      <span class="status-indicator"></span> {status.toUpperCase()}
    </div>
  </header>

  <section class="stats">
    <Card title="Active Streams">
      <p class="value">{activeStreams}</p>
    </Card>
    <Card title="Active Alerts">
      <p class="value">{recentAlerts.length}</p>
    </Card>
  </section>

  <Card title="Circuit Breaker Status">
    <div class="action-panel">
      <h2>Welcome to your stream safety circuit</h2>
      <p>
        Komfyrvakt is armed and watching your infrastructure. To get started, configure an environment stream in the API, add limits, and push metrics to <code>/api/logs</code>.
      </p>
      
      <div class="actions">
        <Button on:click={fetchStatus}>Refresh Streams</Button>
        <Button>View Active Rules</Button>
      </div>
    </div>
  </Card>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: 'Stack Sans Headline', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    /* Hand-drawn Normal-style theme: pure black and paper white */
    background-color: #fcfbf7; 
    color: #000000;
    /* Subtle hand-drawn lined margin paper lines to sell the sketch feel */
    background-image: radial-gradient(#e5e7eb 1.5px, transparent 1.5px);
    background-size: 24px 24px;
    padding: 1rem;
  }

  .dashboard {
    max-width: 900px;
    margin: 0 auto;
    padding: 1rem;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 3.5px solid #000000;
    border-radius: 15px 255px 15px 255px/255px 15px 255px 15px;
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 1.2rem;
  }

  .logo {
    width: 50px;
    height: 50px;
    color: #000000;
    /* Apply organic hand-drawn wobble directly to the logo via CSS border radius mapping */
    transform: rotate(-3deg);
  }

  .brand-text {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.3rem;
  }

  .brand h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    text-transform: uppercase;
  }

  .system-status {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 800;
    font-size: 0.85rem;
    border: 3px solid #000000;
    padding: 0.4rem 0.8rem;
    background-color: #ffffff;
    border-radius: 255px 15px 225px 15px/15px 225px 15px 255px;
    box-shadow: 3px 3px 0px #000000;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .status-indicator {
    width: 10px;
    height: 10px;
    background-color: #000000;
    border-radius: 50%;
    border: 2px solid #000000;
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1rem;
  }

  .value {
    margin: 0;
    font-size: 3rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    font-family: monospace;
  }

  .action-panel h2 {
    margin-top: 0;
    font-size: 1.3rem;
    font-weight: 800;
    text-transform: uppercase;
  }

  .action-panel p {
    color: #374151;
    font-size: 1rem;
    margin-bottom: 1.5rem;
  }

  code {
    background-color: #000000;
    color: #ffffff;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.9rem;
    font-weight: 700;
  }

  .actions {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }
</style>
