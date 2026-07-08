"""Onboarding self-test: exercises the full pipeline with example data,
including edge cases, against the real HTTP API.

Two ways to run it:

1. Automatically on startup (default). The server tests itself in the
   background using an in-process HTTP client and a temporary admin key.
   Results land in the log and in GET /api/health under "selftest".
   Disable with KOMFYRVAKT_SELFTEST=0.

2. Manually against a running server:

       python -m app.selftest <admin-key> [base-url]

Everything runs in a reserved namespace (_selftest) which is purged before
and after, so it never pollutes real data. The silence-detection check
waits for the background scheduler, so the full suite takes ~20 seconds.
"""
import asyncio
import logging
import secrets
import time

import httpx

logger = logging.getLogger("komfyrvakt.selftest")

NS = "_selftest"

# Exposed via GET /api/health.
RESULTS: dict = {"status": "not_run"}


class Check:
    def __init__(self) -> None:
        self.items: list[tuple[str, bool, str]] = []

    def expect(self, name: str, ok: bool, detail: str = "") -> bool:
        self.items.append((name, bool(ok), detail))
        if ok:
            logger.info("[selftest] ok   - %s", name)
        else:
            logger.error("[selftest] FAIL - %s%s", name, f" ({detail})" if detail else "")
        return bool(ok)

    @property
    def failed(self) -> list[tuple[str, bool, str]]:
        return [i for i in self.items if not i[1]]


async def _wait_for(predicate, timeout: float, interval: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if await predicate():
            return True
        await asyncio.sleep(interval)
    return False


async def run_suite(client: httpx.AsyncClient, admin_key: str) -> Check:
    check = Check()
    started = time.monotonic()
    H = {"X-API-Key": admin_key}

    # Wipe leftovers from a previous crashed run.
    await client.delete(f"/api/ns/{NS}", headers=H)

    # ---------------------------------------------------------- health & auth
    r = await client.get("/api/health")
    check.expect("health endpoint responds", r.status_code == 200 and r.json().get("status") == "ok",
                 f"status {r.status_code}")

    r = await client.get("/api/alerts")
    check.expect("auth: missing key rejected (401)", r.status_code == 401, f"got {r.status_code}")
    r = await client.get("/api/alerts", headers={"X-API-Key": "kv_definitely_wrong"})
    check.expect("auth: invalid key rejected (401)", r.status_code == 401, f"got {r.status_code}")

    # ---------------------------------------------------------- registration
    basic_type = {
        "description": "selftest: open schema with all field types",
        "fields": {
            "temp_c": {"type": "number"},
            "door_open": {"type": "boolean"},
            "operator": {"type": "string", "sensitive": True},
        },
        "actions": [{"id": "noop", "description": "do nothing"}],
    }
    r = await client.put(f"/api/ns/{NS}/entity-types/basic", headers=H, json=basic_type)
    check.expect("entity type registration", r.status_code == 200 and r.json()["version"] == 1,
                 f"status {r.status_code}")

    r = await client.put(f"/api/ns/{NS}/entity-types/basic", headers=H, json=basic_type)
    check.expect("idempotent re-registration (no version bump)",
                 r.status_code == 200 and r.json()["changed"] is False and r.json()["version"] == 1,
                 f"changed={r.json().get('changed')} version={r.json().get('version')}")

    r = await client.put(f"/api/ns/{NS}/entity-types/basic", headers=H,
                         json={**basic_type, "description": "selftest: updated"})
    check.expect("changed registration bumps version", r.status_code == 200 and r.json()["version"] == 2,
                 f"version={r.json().get('version')}")

    r = await client.put(f"/api/ns/{NS}/entity-types/bad", headers=H,
                         json={"actions": [{"id": "a"}], "default_action": "nonexistent"})
    check.expect("invalid default_action rejected (422)", r.status_code == 422, f"got {r.status_code}")

    alarm_type = {
        "description": "selftest: immediate alarm",
        "fields": basic_type["fields"],
        "constraints": [{"name": "too warm", "when": {"field": "temp_c", "above": 8}}],
        "actions": [
            {"id": "notify", "description": "notify someone"},
            {"id": "false_alarm", "description": "ignore"},
        ],
        "default_action": "notify",
    }
    duration_type = {
        "description": "selftest: duration alarm",
        "fields": {"temp_c": {"type": "number"}},
        "constraints": [{"name": "warm for 2s", "when": {"field": "temp_c", "above": 8}, "for_seconds": 2}],
        "actions": [{"id": "notify"}],
    }
    composite_type = {
        "description": "selftest: composite constraint",
        "fields": {"temp_c": {"type": "number"}, "door_open": {"type": "boolean"}},
        "constraints": [{
            "name": "door open while warm",
            "when": {"all": [{"field": "door_open", "equals": True}, {"field": "temp_c", "above": 6}]},
        }],
        "actions": [{"id": "notify"}],
    }
    schedule_type = {
        "description": "selftest: schedule that is never active",
        "fields": {"temp_c": {"type": "number"}},
        "constraints": [{"name": "never scheduled", "when": {"field": "temp_c", "above": 0},
                         "schedule": {"days": []}}],
        "actions": [{"id": "notify"}],
    }
    silent_type = {
        "description": "selftest: silence detection",
        "expected_every_seconds": 1,
        "fields": {"temp_c": {"type": "number"}},
        "actions": [{"id": "notify"}],
    }
    for name, body in [("alarm", alarm_type), ("duration", duration_type),
                       ("composite", composite_type), ("schedule", schedule_type),
                       ("silent", silent_type)]:
        await client.put(f"/api/ns/{NS}/entity-types/{name}", headers=H, json=body)
        r = await client.put(f"/api/ns/{NS}/instances/{name}-1", headers=H, json={"entity_type": name})
        check.expect(f"instance registration ({name}-1)", r.status_code == 200, f"status {r.status_code}")

    r = await client.put(f"/api/ns/{NS}/instances/orphan", headers=H, json={"entity_type": "no_such_type"})
    check.expect("instance with unknown type rejected (422)", r.status_code == 422, f"got {r.status_code}")

    # ---------------------------------------------------------- ingest edges
    async def log(instance: str, values: dict, **extra):
        return await client.post("/api/logs", headers=H,
                                 json={"namespace": NS, "instance": instance, "values": values, **extra})

    r = await client.put(f"/api/ns/{NS}/instances/basic-1", headers=H, json={"entity_type": "basic"})
    r = await log("basic-1", {"temp_c": 4.0, "door_open": False, "operator": "Noah"})
    check.expect("valid ingest accepted", r.status_code == 200 and r.json()["accepted"] == 1,
                 f"status {r.status_code}")

    r = await log("basic-1", {"made_up_field": 1})
    check.expect("unknown field rejected (422)", r.status_code == 422, f"got {r.status_code}")

    r = await log("basic-1", {"temp_c": "not a number"})
    check.expect("wrong field type rejected (422)", r.status_code == 422, f"got {r.status_code}")

    r = await log("ghost-instance", {"temp_c": 1})
    check.expect("unknown instance rejected (404)", r.status_code == 404, f"got {r.status_code}")

    r = await log("basic-1", {"temp_c": 5.0}, ts="2026-07-08T12:00:00Z", event_id="evt-selftest-1")
    check.expect("explicit event time + event_id accepted", r.status_code == 200 and r.json()["accepted"] == 1)

    r = await log("basic-1", {"temp_c": 5.0}, ts="2026-07-08T12:00:00Z", event_id="evt-selftest-1")
    check.expect("duplicate event_id absorbed silently", r.status_code == 200 and r.json()["duplicates"] == 1,
                 f"body {r.text[:100]}")

    r = await log("basic-1", {"temp_c": 5.0}, ts="not-a-timestamp")
    check.expect("garbage timestamp rejected (422)", r.status_code == 422, f"got {r.status_code}")

    r = await client.post("/api/logs", headers=H, json=[
        {"namespace": NS, "instance": "basic-1", "values": {"temp_c": 4.1}, "event_id": "evt-batch-1"},
        {"namespace": NS, "instance": "basic-1", "values": {"temp_c": 4.2}, "event_id": "evt-batch-1"},
    ])
    check.expect("batch ingest with internal duplicate",
                 r.status_code == 200 and r.json()["accepted"] == 1 and r.json()["duplicates"] == 1,
                 f"body {r.text[:100]}")

    # ---------------------------------------------------------- alarm lifecycle
    r = await log("alarm-1", {"temp_c": 12.5, "operator": "Noah"})
    state = r.json()["results"][0]["instance_state"] if r.status_code == 200 else "?"
    check.expect("immediate constraint opens alarm", state == "alarm", f"state={state}")

    r = await client.get("/api/alerts", headers=H, params={"status": "active"})
    active = [a for a in r.json() if a["namespace"] == NS] if r.status_code == 200 else []
    alarm_alerts = [a for a in active if a["instance_name"] == "alarm-1"]
    check.expect("alert visible in feed", len(alarm_alerts) == 1, f"found {len(alarm_alerts)}")

    decision = alarm_alerts[0]["decision"] if alarm_alerts else None
    check.expect("decision attached with rule-default action",
                 decision is not None and decision["action"] == "notify" and decision["source"] == "rule",
                 f"decision={decision}")

    r = await client.get("/api/decisions", headers=H, params={"since": 0, "limit": 500})
    ns_decisions = [d for d in r.json()["decisions"] if d["namespace"] == NS]
    check.expect("outbox poll returns decision with cursor",
                 len(ns_decisions) >= 1 and r.json()["cursor"] >= ns_decisions[-1]["id"])

    redacted_ok = any(
        d["context_snapshot"].get("last_values", {}).get("operator") == "[redacted]"
        for d in ns_decisions
    )
    check.expect("sensitive field redacted in decision context", redacted_ok)

    cursor = r.json()["cursor"]
    r = await client.get("/api/decisions", headers=H, params={"since": cursor})
    check.expect("outbox cursor advances (no repeats)",
                 all(d["id"] > cursor for d in r.json()["decisions"]))

    if alarm_alerts:
        r = await client.post(f"/api/alerts/{alarm_alerts[0]['id']}/ack", headers=H)
        check.expect("alert acknowledgement", r.status_code == 200 and r.json()["status"] == "acknowledged",
                     f"body {r.text[:100]}")

    r = await log("alarm-1", {"temp_c": 4.0})
    state = r.json()["results"][0]["instance_state"]
    r = await client.get("/api/alerts", headers=H, params={"status": "resolved"})
    resolved = [a for a in r.json() if a["namespace"] == NS and a["instance_name"] == "alarm-1"]
    check.expect("recovery resolves alert and clears state", state == "ok" and len(resolved) >= 1,
                 f"state={state} resolved={len(resolved)}")

    # ---------------------------------------------------------- duration
    r = await log("duration-1", {"temp_c": 12.0})
    state = r.json()["results"][0]["instance_state"]
    check.expect("duration constraint: suspect first, no instant alarm", state == "suspect", f"state={state}")

    await asyncio.sleep(2.5)
    r = await log("duration-1", {"temp_c": 12.0})
    state = r.json()["results"][0]["instance_state"]
    check.expect("duration constraint: alarm after for_seconds", state == "alarm", f"state={state}")

    # ---------------------------------------------------------- composite
    r = await log("composite-1", {"door_open": True})
    state = r.json()["results"][0]["instance_state"]
    check.expect("composite: half-violated stays ok", state == "ok", f"state={state}")

    r = await log("composite-1", {"temp_c": 7.0})
    state = r.json()["results"][0]["instance_state"]
    check.expect("composite: fully violated (merged fields) alarms", state == "alarm", f"state={state}")

    # ---------------------------------------------------------- schedule
    r = await log("schedule-1", {"temp_c": 99.0})
    state = r.json()["results"][0]["instance_state"]
    check.expect("inactive schedule window suppresses constraint", state == "ok", f"state={state}")

    # ---------------------------------------------------------- scoped keys
    r = await client.post("/api/keys", headers=H,
                          json={"name": "selftest-ingest", "role": "ingest", "namespace": NS})
    ingest_key = r.json().get("key", "")
    ingest_key_id = r.json().get("id")
    check.expect("scoped ingest key creation", r.status_code == 200 and ingest_key.startswith("kv_"))

    r = await client.post("/api/logs", headers={"X-API-Key": ingest_key},
                          json={"namespace": NS, "instance": "basic-1", "values": {"temp_c": 4.3}})
    check.expect("ingest key can post logs in its namespace", r.status_code == 200, f"got {r.status_code}")

    r = await client.post("/api/logs", headers={"X-API-Key": ingest_key},
                          json={"namespace": "some-other-ns", "instance": "x", "values": {}})
    check.expect("ingest key blocked outside its namespace (403)", r.status_code == 403, f"got {r.status_code}")

    r = await client.get("/api/alerts", headers={"X-API-Key": ingest_key})
    check.expect("ingest key blocked from admin endpoints (403)", r.status_code == 403, f"got {r.status_code}")

    if ingest_key_id:
        await client.delete(f"/api/keys/{ingest_key_id}", headers=H)
        r = await client.post("/api/logs", headers={"X-API-Key": ingest_key},
                              json={"namespace": NS, "instance": "basic-1", "values": {"temp_c": 4.4}})
        check.expect("revoked key rejected (401)", r.status_code == 401, f"got {r.status_code}")

    # ---------------------------------------------------------- silence
    await log("silent-1", {"temp_c": 4.0})

    async def silent_alert_present():
        r = await client.get("/api/alerts", headers=H, params={"status": "active"})
        return any(a["namespace"] == NS and a["kind"] == "silent" for a in r.json())

    # expected_every_seconds=1 -> silent after ~3s; scheduler ticks every 10s.
    found = await _wait_for(silent_alert_present, timeout=15)
    check.expect("silence detection (scheduler flags dead stream)", found)

    if found:
        r = await log("silent-1", {"temp_c": 4.1})
        state = r.json()["results"][0]["instance_state"]
        check.expect("silence recovery on new data", state == "ok", f"state={state}")

    # ---------------------------------------------------------- cleanup
    r = await client.delete(f"/api/ns/{NS}", headers=H)
    check.expect("namespace purge cleans up all test data", r.status_code == 200,
                 f"status {r.status_code}")
    r = await client.get("/api/instances", headers=H)
    leftovers = [i for i in r.json() if i["namespace"] == NS]
    check.expect("no test data left behind", len(leftovers) == 0, f"{len(leftovers)} leftovers")

    # ---------------------------------------------------------- summary
    duration = time.monotonic() - started
    failed = check.failed
    RESULTS.clear()
    RESULTS.update({
        "status": "pass" if not failed else "fail",
        "passed": len(check.items) - len(failed),
        "failed": len(failed),
        "failures": [name for name, _, _ in failed],
        "duration_seconds": round(duration, 1),
    })
    if failed:
        logger.error("[selftest] %d/%d checks FAILED in %.1fs: %s",
                     len(failed), len(check.items), duration,
                     ", ".join(name for name, _, _ in failed))
    else:
        logger.info("[selftest] all %d checks passed in %.1fs - Komfyrvakt is live and working",
                    len(check.items), duration)
    return check


async def run_startup_selftest(app) -> None:
    """Startup onboarding: test the app through its own HTTP stack using a
    temporary admin key that is deleted afterwards."""
    from sqlmodel import Session

    from .auth import hash_key
    from .database import engine
    from .models import ApiKey

    await asyncio.sleep(2)  # let the scheduler and event loop settle
    raw = "kv_selftest_" + secrets.token_urlsafe(24)
    with Session(engine) as session:
        record = ApiKey(name="selftest-temporary", key_hash=hash_key(raw), role="admin", namespace="*")
        session.add(record)
        session.commit()
        key_id = record.id
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://selftest.local", timeout=30) as client:
            await run_suite(client, raw)
    except Exception:
        logger.exception("[selftest] crashed")
        RESULTS.clear()
        RESULTS.update({"status": "crashed"})
    finally:
        with Session(engine) as session:
            record = session.get(ApiKey, key_id)
            if record:
                session.delete(record)
                session.commit()


def main() -> None:
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(sys.argv) < 2:
        print("usage: python -m app.selftest <admin-api-key> [base-url]")
        sys.exit(2)
    key = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000"

    async def go() -> Check:
        async with httpx.AsyncClient(base_url=base, timeout=30) as client:
            return await run_suite(client, key)

    check = asyncio.run(go())
    sys.exit(0 if not check.failed else 1)


if __name__ == "__main__":
    main()
