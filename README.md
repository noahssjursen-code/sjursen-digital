# Sjursen Digital

Sjursen Digital builds **self-hostable backend services** that solve real operational problems.

You run the software on your own infrastructure. We build the system, ship updates, and offer a subscription for the software, support, and commercial features. Your data stays on your server.

## What we build

Focused tools — not platforms. Backend-heavy services with minimal UI:

- APIs and workers that take input, do the work, and return output
- Docker-based deployments that are simple to install and operate
- Clear free and paid tiers: core features self-hosted, business features on subscription

Examples of the kind of problems we target: authorization, integrations, automation pipelines, audit/logging, and other workflows that teams currently solve with spreadsheets, manual glue, or fragile in-house scripts.

## Products

### SEDE

**SEDE** (Norwegian: *stove guard* — a safety device that monitors stove activity and cuts the power if a burner gets dangerously hot) is a self-hostable event monitoring and decision engine. It acts as an automated digital circuit breaker and escalation guard for any stream of data.

You post logs (from IoT sensors, SaaS apps, background workers, or integrations). SEDE monitors the stream, detects when a pattern crosses your safety thresholds, and invokes an AI layer only when human-like judgment is needed. The AI analyzes the context—what the stream is, what the data says, and what actions are allowed—and returns a structured decision. Your integration code parses that decision to run the safety handler: page a technician, shut off an API key, trigger a webhook, or alert managers.

It is built to be **implemented anywhere** you need a reliable monitoring brain. Completely self-hosted so you keep absolute control over your logs, credentials, and compute.

**Example:** A restaurant chain monitors six fridge/freezer environments. Sensors post temperature readings every 10 seconds. A door stays open after closing, temperatures climb, and the stream crosses thresholds. SEDE analyzes the pattern and decides whether to alert a manager, escalate, or dismiss — your integration code executes the result.

## Repository

```text
sjursen-digital/
├── assets/logo/        # Brand assets
├── shared/             # Shared assets across all apps
│   └── components/     # Reusable Svelte UI components (e.g. Card, Button)
├── website/            # Company homepage (static SvelteKit site, host anywhere)
├── gateway/            # The self-hosted Gateway customers download
│   ├── api/            # FastAPI reverse proxy & launcher backend
│   └── ui/             # SvelteKit launcher UI (compiled into api/static/)
└── services/           # Product modules mounted under the Gateway (in development)
```

## Brand

Primary logo: `assets/logo/sjursen-digital.svg`

---

Noah Sebastian Sjursen · Bergen, Norway
