"""Constraint evaluation and the per-instance state machine.

Constraint shape (stored as JSON on the EntityType, overridable per instance):

    {
      "name": "temp too high",
      "when": {"field": "temp_c", "above": 8},
      "for_seconds": 300,                       # optional; 0/absent = alarm immediately
      "schedule": {"start": "22:00", "end": "06:00", "days": [0,1,2,3,4]},  # optional
      "action": "notify_manager"                # optional default action for this constraint
    }

`when` expresses the VIOLATION condition. Tests compose with all/any:

    {"all": [{"field": "door_open", "equals": true}, {"field": "temp_c", "above": 6}]}

Supported field operators: above, below, equals, not_equals, one_of, not_one_of.
A test on a field with no known value yet is not violating (we can't judge
what we haven't seen).
"""
from datetime import datetime, time

from sqlmodel import Session, select

from .models import Alert, EntityType, Instance, utcnow


def check_test(test: dict, values: dict) -> bool:
    """True = violating."""
    if "all" in test:
        subs = test["all"]
        return bool(subs) and all(check_test(t, values) for t in subs)
    if "any" in test:
        return any(check_test(t, values) for t in test["any"])

    field = test.get("field")
    if field is None or field not in values or values[field] is None:
        return False
    v = values[field]

    if "above" in test:
        return v > test["above"]
    if "below" in test:
        return v < test["below"]
    if "equals" in test:
        return v == test["equals"]
    if "not_equals" in test:
        return v != test["not_equals"]
    if "one_of" in test:
        return v in test["one_of"]
    if "not_one_of" in test:
        return v not in test["not_one_of"]
    return False


def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def in_schedule(schedule: dict | None, now: datetime) -> bool:
    """No schedule = constraint always active. Overnight windows (22:00-06:00) supported."""
    if not schedule:
        return True
    days = schedule.get("days")
    if days is not None and now.weekday() not in days:
        return False
    start = schedule.get("start")
    end = schedule.get("end")
    if not start or not end:
        return True
    t, t0, t1 = now.time(), _parse_hhmm(start), _parse_hhmm(end)
    if t0 <= t1:
        return t0 <= t <= t1
    return t >= t0 or t <= t1  # crosses midnight


def effective_constraints(instance: Instance, etype: EntityType) -> list:
    override = (instance.overrides or {}).get("constraints")
    return override if override is not None else (etype.constraints or [])


def constraint_summary(c: dict, idx: int, instance: Instance) -> str:
    name = c.get("name") or f"constraint #{idx}"
    return f"{instance.namespace}/{instance.name}: '{name}' violated"


def process_instance(session: Session, instance: Instance, etype: EntityType, now: datetime | None = None) -> list[Alert]:
    """Run the state machine for one instance against its last-known values.

    Called on every ingest and periodically by the scheduler (so durations
    can elapse without new logs arriving). Returns newly OPENED alerts so
    the caller can attach decisions.
    """
    now = now or utcnow()
    constraints = effective_constraints(instance, etype)
    cstate = dict(instance.constraint_state or {})
    opened: list[Alert] = []
    any_suspect = False
    any_alarm = False

    for idx, c in enumerate(constraints):
        key = str(idx)
        entry = dict(cstate.get(key) or {})
        violating = in_schedule(c.get("schedule"), now) and check_test(c.get("when", {}), instance.last_values or {})

        if violating:
            since_raw = entry.get("violating_since")
            if not since_raw:
                entry["violating_since"] = now.isoformat()
                since = now
            else:
                since = datetime.fromisoformat(since_raw)
            elapsed = (now - since).total_seconds()
            need = c.get("for_seconds") or 0

            if elapsed >= need and not entry.get("alert_id"):
                alert = Alert(
                    namespace=instance.namespace,
                    instance_id=instance.id,
                    kind="constraint",
                    constraint_index=idx,
                    summary=constraint_summary(c, idx, instance),
                    opened_at=now,
                )
                session.add(alert)
                session.flush()  # get alert.id
                entry["alert_id"] = alert.id
                opened.append(alert)

            if entry.get("alert_id"):
                any_alarm = True
            else:
                any_suspect = True
        else:
            alert_id = entry.get("alert_id")
            if alert_id:
                alert = session.get(Alert, alert_id)
                if alert and alert.status != "resolved":
                    alert.status = "resolved"
                    alert.resolved_at = now
                    session.add(alert)
            entry = {}

        cstate[key] = entry

    instance.constraint_state = cstate

    # Silence overrides everything until data flows again (cleared at ingest).
    if instance.state != "silent":
        instance.state = "alarm" if any_alarm else ("suspect" if any_suspect else "ok")
    session.add(instance)
    return opened


def check_silence(session: Session, instance: Instance, etype: EntityType, now: datetime | None = None) -> Alert | None:
    """Scheduler-only: no data for 3x the expected interval means the pipe
    itself is broken, which is its own alarm (DESIGN.md §4)."""
    now = now or utcnow()
    if not etype.expected_every_seconds or instance.last_seen_at is None:
        return None
    if instance.state == "silent":
        return None
    gap = (now - instance.last_seen_at).total_seconds()
    if gap < 3 * etype.expected_every_seconds:
        return None

    instance.state = "silent"
    session.add(instance)
    alert = Alert(
        namespace=instance.namespace,
        instance_id=instance.id,
        kind="silent",
        summary=(
            f"{instance.namespace}/{instance.name}: silent for {int(gap)}s "
            f"(expected data every {etype.expected_every_seconds}s)"
        ),
        opened_at=now,
    )
    session.add(alert)
    session.flush()
    return alert


def clear_silence(session: Session, instance: Instance, now: datetime | None = None) -> None:
    """Called at ingest when a silent instance starts reporting again."""
    if instance.state != "silent":
        return
    now = now or utcnow()
    silent_alerts = session.exec(
        select(Alert).where(
            Alert.instance_id == instance.id,
            Alert.kind == "silent",
            Alert.status != "resolved",
        )
    ).all()
    for a in silent_alerts:
        a.status = "resolved"
        a.resolved_at = now
        session.add(a)
    instance.state = "ok"
    session.add(instance)
