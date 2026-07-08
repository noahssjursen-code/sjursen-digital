# Komfyrvakt — Design & Inner Workings

> **Komfyrvakt** (Norwegian: *stove guard*) is a self-hostable event monitoring and
> decision engine. Services, sensors, and apps post logs to it. It watches the
> streams, detects abnormal patterns with deterministic rules, consults an AI layer
> only when judgment is needed, and delivers structured decisions back to the
> customer's own code for execution.
>
> This document describes how the service works internally — partly as-built,
> partly as-intended. It is the source of truth for implementation decisions.

## 1. Principles

1. **Deterministic first, AI second.** Rules (threshold + duration + schedule)
   decide *whether* something is abnormal. The AI only decides *what to do about
   it*, and only when configured. With AI disabled, Komfyrvakt is still a fully
   functional watchdog.
2. **Closed action vocabulary.** The AI never free-forms. It picks from actions the
   developer declared, with a reason string. Garbage or timeout → fall back to the
   rule's default action.
3. **Self-contained.** One container: FastAPI + SQLite + compiled SvelteKit UI.
   No data leaves the host unless the customer configures an external AI endpoint
   or webhook target.
4. **Code-first integration.** Registering entity types is declarative and
   idempotent, done from the customer's own service at startup. The UI is a
   viewer, not a required configuration tool.
5. **Boring operations.** Backup = copy one SQLite file. Upgrade = pull new image.
   Schema migrations run automatically on startup.

## 2. Core objects

The entire public surface is four objects plus the outbox.

### 2.1 EntityType

A declarative contract: schema + constraints + allowed actions.

```json
{
  "name": "temperature_sensor",
  "description": "Temperature sensor for fridge environments",
  "expected_every_seconds": 10,
  "fields": {
    "temp_c":    { "type": "number" },
    "door_open": { "type": "boolean" },
    "location":  { "type": "string" }
  },
  "constraints": [
    { "field": "temp_c",    "ok":    { "min": 0, "max": 6 } },
    { "field": "temp_c",    "alarm": { "above": 10, "for_seconds": 300 } },
    { "field": "door_open", "alarm": { "equals": true, "for_seconds": 240, "schedule": "after_closing" } }
  ],
  "actions": [
    { "id": "notify_manager",  "description": "Send SMS to site manager" },
    { "id": "escalate_oncall", "description": "Page on-call technician" },
    { "id": "false_alarm",     "description": "Dismiss and log" }
  ],
  "default_action": "notify_manager"
}
```

- **Registration is idempotent.** Registering an identical type is a no-op.
  Changing a type bumps its version; old log rows keep their version reference.
- **`expected_every_seconds`** powers silence detection (see §4.3). Optional —
  streams without it are never silence-checked.
- **Action `description`s are load-bearing:** they are injected into the AI
  context so the model can choose sensibly. They are written by the developer
  who knows what the actions mean.
- **`default_action`** is executed when the AI is disabled, unreachable, or
  returns an invalid decision.

### 2.2 Instance

A concrete stream of a given type: `fridge-1-bergen` is an instance of
`temperature_sensor`. Instances inherit the type's constraints and may override
per-field bounds (a freezer's acceptable range differs from a fridge's, same
schema).

### 2.3 LogEntry

One event posted by the customer's code:

```json
{
  "instance": "fridge-1-bergen",
  "ts": "2026-07-08T20:11:04Z",
  "values": { "temp_c": 17.2, "door_open": true },
  "meta": { "device_fw": "1.4.2" }
}
```

- Validated against the EntityType schema at ingest; unknown fields are rejected,
  missing optional fields are allowed.
- **Idempotency:** clients may send an `event_id`; duplicates (same instance +
  event_id) are absorbed silently. Without an event_id, exact duplicates on
  (instance, ts, values-hash) are deduped.
- `ts` is the sensor-side timestamp; the server also records `received_at`.

### 2.4 Decision

The output object. Produced by the rule engine (rules-only mode) or the AI layer:

```json
{
  "id": "dec_01H...",
  "instance": "fridge-1-bergen",
  "alert_id": "alr_01H...",
  "action": "notify_manager",
  "source": "ai",
  "confidence": 0.86,
  "reason": "Temp rising 40 min after closing; door_open persisted 7 min; matches after-hours-door pattern, not defrost cycle.",
  "context_snapshot": { "...": "the exact window of logs and rule state the AI saw" },
  "created_at": "2026-07-08T20:18:04Z"
}
```

`source` is `"rule"` (default action, AI not consulted), `"ai"`, or
`"fallback"` (AI consulted but failed/invalid → default action used).
`context_snapshot` makes every decision auditable: what did the system see when
it decided?

## 3. Pipeline

```
POST /api/logs
  → validate against EntityType schema (reject unknown shape)
  → dedupe (event_id / content hash)
  → append to hot store (SQLite, WAL mode)
  → rule engine evaluates the instance's active constraints
      → constraint tracks its own duration window ("above 10 for 300s")
      → schedule windows checked (e.g. "after_closing")
  → state machine per instance:  ok → suspect → alarm → resolved
      → transitions create/close Alerts
  → on alarm:
      → if AI configured for this type: build context, call decision layer
      → else: emit Decision with default_action, source="rule"
  → Decision lands in the outbox
  → delivery: webhook push (signed, retried) and/or poll cursor
```

### 3.1 State machine

Per instance, not per constraint. States:

| State      | Meaning                                              |
|------------|------------------------------------------------------|
| `ok`       | All constraints satisfied                            |
| `suspect`  | A constraint is violated but its duration window has not elapsed |
| `alarm`    | Violation persisted past `for_seconds` → Alert opened |
| `resolved` | Values returned to acceptable range → Alert closed    |

`suspect` exists so that a 5-second temperature blip never wakes anyone up, and
so the UI can show "watching this" before it becomes "act on this".

### 3.2 Alerts

An Alert is the lifecycle wrapper around a rule violation: opened on
`suspect → alarm`, closed on `alarm → resolved`, acknowledgeable from the UI.
Alerts, Decisions, and executed-action results are **never deleted** — they are
the audit trail.

## 4. Detection

### 4.1 Constraints

Three parts, all deterministic:

- **Value test** — `min/max`, `above/below`, `equals`, `one_of`
- **Duration** — `for_seconds`: violation must persist continuously
- **Schedule** — optional named window (`after_closing`, `weekends`, cron-like
  ranges) during which the constraint applies or is suppressed

### 4.2 Why duration + schedule matter

A bare min/max check is what every dumb tool does. `17°C` is not the alarm —
`17°C for five minutes, after closing` is. This is where Komfyrvakt is smart
*before* any AI is involved.

### 4.3 Silence detection (dead-man switch)

If an EntityType declares `expected_every_seconds`, a scheduler checks each
instance's last-seen timestamp. Silence beyond a multiple (default 3×) opens an
Alert of kind `silent`. A dead sensor is not a healthy fridge — absence of data
is itself a signal.

## 5. AI decision layer

### 5.1 Interface, not implementation

Komfyrvakt does **not** bundle a model. It speaks the **OpenAI-compatible chat
API** to a configurable endpoint:

| Config                     | Effect                                            |
|----------------------------|---------------------------------------------------|
| unset (default)            | AI disabled; rules-only mode; default actions fire |
| `http://ollama:11434/v1`   | Airgapped sidecar (e.g. Ollama + small model) in the same compose file |
| Azure OpenAI / any provider| Customer's own tenant, their key, their data path  |

This keeps the "runs on a $6 VPS" story intact, keeps the networkless story
intact (sidecar), and never makes model quality Komfyrvakt's problem.

### 5.2 Context construction

When an alarm escalates to the AI, the context contains:

1. The EntityType description and the instance identity
2. The recent log window (hot store) for that instance
3. The constraint that tripped, including its duration/schedule config
4. Current state machine state and open Alert
5. The action list **with their developer-written descriptions**
6. Recent prior Decisions for this instance (so it can spot repeats/flapping)

### 5.3 Output contract

The model must return structured JSON choosing one `action` from the closed
list, plus `confidence` and `reason`. Anything else — invalid action id,
malformed JSON, timeout — triggers the fallback: `default_action`,
`source="fallback"`. The raw model response is stored for debugging.

## 6. Storage (SQLite)

Single file, WAL mode. Three data tiers:

| Tier     | Contents                                   | Retention                          |
|----------|--------------------------------------------|-------------------------------------|
| Hot      | Raw LogEntries per instance                | Sliding window (default 7 days)     |
| Rollups  | min/max/avg/count per minute → hour → day  | Long (default 2 years)              |
| Audit    | Alerts, Decisions, action results, type versions | Never deleted                  |

A background task downsamples hot → rollups, then deletes raw rows past
retention. This keeps the DB file small enough that backup remains "copy one
file". Retention is configurable per EntityType.

Ingest rate: 10s-interval streams × hundreds of instances is well within
SQLite/WAL comfort. If a deployment outgrows this, that is a "you have
succeeded" problem; a Postgres backend can be a paid-tier feature later.

## 7. Delivery — the outbox

Every Decision lands in a persistent outbox table. Two consumption modes, same
data:

- **Push:** Komfyrvakt POSTs to the customer's webhook.
  - HMAC-signed body (`X-Komfyrvakt-Signature`)
  - Exponential backoff retries; after N failures → dead-letter status, visible
    in the UI
- **Poll:** `GET /api/decisions?since=<cursor>` — for airgapped hosts and
  clients that cannot expose an endpoint. The cursor is a monotonically
  increasing id, so consumers can resume exactly where they left off.

Execution stays in the customer's code: they map `action` ids to real methods
(send SMS, kill an API key, open a ticket). Komfyrvakt records what it decided;
the customer's handler reports back an optional execution result for the audit
trail.

## 8. API surface (v1)

```
# Contracts
PUT  /api/entity-types/{name}       idempotent register/update (bumps version)
GET  /api/entity-types

# Instances
PUT  /api/instances/{name}          create/update, binds to a type, overrides
GET  /api/instances

# Ingest
POST /api/logs                      single or batch
GET  /api/logs/{instance}?window=   hot-store window (UI + AI context)

# Alerts & decisions
GET  /api/alerts?status=active
POST /api/alerts/{id}/ack
GET  /api/decisions?since=<cursor>  poll consumption
POST /api/decisions/{id}/result     customer reports execution outcome

# Ops
GET  /api/health                    liveness + self-metrics
```

Auth: scoped API keys. An ingest key can only post logs; an admin key manages
types and reads decisions. Keys are revocable individually, so one leaked
sensor key never exposes data.

## 9. Self-monitoring

Who watches the watchman:

- `/api/health` exposes queue depths, last scheduler run, DB size, outbox
  dead-letter count
- The scheduler alarms *itself* (a built-in `komfyrvakt.internal` instance) if
  rule evaluation falls behind ingest — degradation is visible in the same
  alert feed as everything else

## 10. UI

Viewer, not configurator. Three views in priority order:

1. **Alert feed** (home) — active alarms first. Each alert expands into the
   decision card: what the system saw (`context_snapshot`), what it decided,
   why, and what happened (webhook result / ack).
2. **Instance detail** — rollup chart with threshold lines and alert markers on
   the timeline; current state machine state.
3. **Audit log** — flat, filterable, exportable (CSV; PDF later). This is the
   compliance artifact.

Styling: shared Sjursen Digital component library (`shared/components/`) —
black-and-white, subtle hand-drawn line character.

## 11. Packaging & tiers

- **One image:** FastAPI serves the compiled SvelteKit SPA from `api/static/`.
  One exposed port. `/data` volume for SQLite.
- **Compose variants:** standalone; or with an Ollama sidecar for airgapped AI.
- **Tier sketch** (subject to change):
  - *Community* — self-host, rules engine, alerts, poll delivery
  - *Pro* — AI decision layer, webhook signing/retries, audit export, retention config
  - *Business* — SSO, multi-site, priority support, commercial license
- **Licensing (future):** offline license keys via asymmetric signatures
  (Ed25519) — payload + signature verified locally against an embedded public
  key; no phone-home. Not implemented until there is something worth protecting.

## 12. Build order

1. Ingest hardening: EntityType registration, schema validation, dedupe, API keys
2. Rule engine: constraints (value/duration/schedule), state machine, silence detection
3. Alert feed UI + instance detail
4. Outbox + webhook push (signed, retried) + poll cursor
5. AI decision layer behind the OpenAI-compatible interface (off by default)
6. Audit export, rule dry-run mode, retention/rollup scheduler

The product is genuinely useful and demoable after step 3. The AI layer is the
differentiator on top — never a load-bearing dependency.
