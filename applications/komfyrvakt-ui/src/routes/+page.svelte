<script lang="ts">
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
      <h1>Komfyrvakt</h1>
      <span class="badge">Self-Hosted</span>
    </div>
    <div class="system-status {status}">
      <span class="dot"></span> {status.toUpperCase()}
    </div>
  </header>

  <section class="stats">
    <div class="card">
      <h3>Active Streams</h3>
      <p class="value">{activeStreams}</p>
    </div>
    <div class="card">
      <h3>Active Alerts</h3>
      <p class="value">{recentAlerts.length}</p>
    </div>
  </section>

  <section class="action-panel">
    <h2>Welcome to your stream safety circuit</h2>
    <p>
      Komfyrvakt is running. To get started, configure a stream in the API and post logs to <code>/api/logs</code>.
    </p>
  </section>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background-color: #0f172a;
    color: #f8fafc;
  }

  .dashboard {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .brand h1 {
    margin: 0;
    font-size: 1.8rem;
    letter-spacing: -0.02em;
  }

  .badge {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 500;
  }

  .system-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    font-weight: 600;
    color: #10b981;
  }

  .dot {
    width: 8px;
    height: 8px;
    background-color: #10b981;
    border-radius: 50%;
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .card {
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 1.5rem;
    border-radius: 8px;
  }

  .card h3 {
    margin: 0 0 0.5rem 0;
    color: #94a3b8;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .card .value {
    margin: 0;
    font-size: 2.2rem;
    font-weight: 700;
  }

  .action-panel {
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 2rem;
    border-radius: 8px;
  }

  .action-panel h2 {
    margin-top: 0;
    font-size: 1.4rem;
  }

  code {
    background-color: #0f172a;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    color: #38bdf8;
    font-family: monospace;
  }
</style>
