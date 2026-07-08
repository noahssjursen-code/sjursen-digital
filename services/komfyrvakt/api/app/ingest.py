"""Ingest pipeline: validate -> dedupe -> store -> update instance -> evaluate -> decide."""
import hashlib
import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from .decisions import make_decision
from .models import EntityType, Instance, LogEntry, utcnow
from .rules import clear_silence, process_instance
from .validation import validate_values


def _dedupe_key(event_id: str | None, ts: datetime, values: dict) -> str:
    if event_id:
        return f"eid:{event_id}"
    payload = ts.isoformat() + json.dumps(values, sort_keys=True, default=str)
    return "sha:" + hashlib.sha256(payload.encode()).hexdigest()


def ingest_one(session: Session, item: dict) -> dict:
    """Ingest a single log dict: {namespace, instance, values, ts?, meta?, event_id?}.

    Returns {"status": "ok" | "duplicate", "instance_state": ...}.
    Raises HTTPException on unknown instance or schema violation.
    """
    namespace = item.get("namespace", "default")
    instance_name = item.get("instance")
    if not instance_name:
        raise HTTPException(status_code=422, detail="Missing 'instance'")
    values = item.get("values") or {}
    if not isinstance(values, dict):
        raise HTTPException(status_code=422, detail="'values' must be an object")

    instance = session.exec(
        select(Instance).where(Instance.namespace == namespace, Instance.name == instance_name)
    ).first()
    if instance is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown instance '{namespace}/{instance_name}'. Register it first via PUT /api/ns/{namespace}/instances/{instance_name}",
        )
    etype = session.exec(
        select(EntityType).where(EntityType.namespace == namespace, EntityType.name == instance.entity_type)
    ).first()
    if etype is None:
        raise HTTPException(status_code=500, detail=f"Instance references missing entity type '{instance.entity_type}'")

    errors = validate_values(values, etype.fields_schema or {})
    if errors:
        raise HTTPException(status_code=422, detail={"instance": f"{namespace}/{instance_name}", "errors": errors})

    ts_raw = item.get("ts")
    try:
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).replace(tzinfo=None) if ts_raw else utcnow()
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail=f"Invalid 'ts': {ts_raw!r} (expected ISO 8601)")

    entry = LogEntry(
        instance_id=instance.id,
        ts=ts,
        values=values,
        meta=item.get("meta") or {},
        event_id=item.get("event_id"),
        dedupe_key=_dedupe_key(item.get("event_id"), ts, values),
    )
    session.add(entry)
    try:
        session.flush()
    except IntegrityError:
        # Duplicates are absorbed silently: retrying senders are correct senders.
        session.rollback()
        return {"status": "duplicate", "instance_state": instance.state}

    now = utcnow()
    instance.last_values = {**(instance.last_values or {}), **values}
    instance.last_seen_at = now
    clear_silence(session, instance, now)

    opened_alerts = process_instance(session, instance, etype, now)
    for alert in opened_alerts:
        make_decision(session, instance, etype, alert)

    session.commit()
    session.refresh(instance)
    return {"status": "ok", "instance_state": instance.state, "alerts_opened": len(opened_alerts)}
