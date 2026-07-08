"""End-to-end demo against a running Komfyrvakt instance.

Usage:
    python demo.py [base-url] [api-key]

With the default open dashboard no key is needed - the demo creates its own
ingest key via the API. Registers a fridge_sensor entity type and one fridge,
posts normal readings, then a sustained violation, and shows the resulting
alert + decision.
"""
import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
KEY = sys.argv[2] if len(sys.argv) > 2 else ""
NS = "demo-restaurant"

client = httpx.Client(base_url=BASE, headers={"X-API-Key": KEY} if KEY else {}, timeout=10)

if not KEY:
    resp = client.post("/api/keys", json={"name": "demo", "role": "ingest", "namespace": NS})
    resp.raise_for_status()
    client.headers["X-API-Key"] = resp.json()["key"]
    print("[ok] created demo ingest key via dashboard API")


def step(label, resp):
    resp.raise_for_status()
    print(f"[ok] {label}")
    return resp.json()


step("register entity type", client.put(f"/api/ns/{NS}/entity-types/fridge_sensor", json={
    "description": "Fridge temperature sensor. Reports every 10s.",
    "expected_every_seconds": 10,
    "fields": {
        "temp_c": {"type": "number"},
        "door_open": {"type": "boolean"},
    },
    "constraints": [
        {"name": "temp too high", "when": {"field": "temp_c", "above": 8}, "for_seconds": 3},
        {"name": "door left open while warm",
         "when": {"all": [{"field": "door_open", "equals": True}, {"field": "temp_c", "above": 6}]}},
    ],
    "actions": [
        {"id": "notify_manager", "description": "Send a push notification to the restaurant manager"},
        {"id": "call_manager", "description": "Trigger a phone call - for urgent food safety risk"},
        {"id": "false_alarm", "description": "Log and ignore - expected situation like defrost cycle"},
    ],
    "default_action": "notify_manager",
}))

step("register instance", client.put(f"/api/ns/{NS}/instances/fridge-1", json={"entity_type": "fridge_sensor"}))

print("posting normal readings...")
for temp in (4.0, 4.2, 3.9):
    step(f"  log temp={temp}", client.post("/api/logs", json={
        "namespace": NS, "instance": "fridge-1", "values": {"temp_c": temp, "door_open": False},
    }))
    time.sleep(0.3)

print("posting violation (temp 12.5, needs to hold for 3s)...")
step("  log temp=12.5", client.post("/api/logs", json={
    "namespace": NS, "instance": "fridge-1", "values": {"temp_c": 12.5},
}))
time.sleep(3.5)
result = step("  log temp=13.1 (duration elapsed)", client.post("/api/logs", json={
    "namespace": NS, "instance": "fridge-1", "values": {"temp_c": 13.1},
}))
print(f"  instance state: {result['results'][0]['instance_state']}")

alerts = step("fetch alerts", client.get("/api/alerts", params={"status": "active"}))
for a in alerts:
    print(f"  ALERT #{a['id']} [{a['kind']}] {a['summary']}")
    if a["decision"]:
        d = a["decision"]
        print(f"    -> decision: {d['action']} (source={d['source']}) {d['reason']}")

decisions = step("poll outbox", client.get("/api/decisions", params={"since": 0}))
print(f"  outbox cursor: {decisions['cursor']}, {len(decisions['decisions'])} decision(s)")

print("posting recovery (temp back to 4.0)...")
result = step("  log temp=4.0", client.post("/api/logs", json={
    "namespace": NS, "instance": "fridge-1", "values": {"temp_c": 4.0},
}))
print(f"  instance state: {result['results'][0]['instance_state']}")
print("done.")
