"""HTTP API. All admin routes are namespace-prefixed: /api/ns/{namespace}/...

Roles: admin keys manage everything; ingest keys can only POST logs.
Namespace-scoped keys only see their own namespace.
"""
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete
from sqlmodel import Session, func, select

from .auth import check_namespace, hash_key, new_raw_key, require_admin, require_ingest
from .database import get_session
from .ingest import ingest_one
from .models import Alert, ApiKey, Decision, EntityType, Instance, LogEntry, Namespace, utcnow

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------- health

@router.get("/health")
def health(session: Session = Depends(get_session)):
    from .selftest import RESULTS as selftest_results

    return {
        "status": "ok",
        "service": "komfyrvakt",
        "version": "0.1.0",
        "instances": session.exec(select(func.count()).select_from(Instance)).one(),
        "active_alerts": session.exec(
            select(func.count()).select_from(Alert).where(Alert.status == "active")
        ).one(),
        "selftest": selftest_results,
    }


# ---------------------------------------------------------------- namespaces

class NamespaceIn(BaseModel):
    description: str = ""
    ai_endpoint: Optional[str] = None
    ai_model: Optional[str] = None
    ai_api_key: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None


def _ns_out(ns: Namespace) -> dict:
    return {
        "name": ns.name,
        "description": ns.description,
        "ai_enabled": bool(ns.ai_endpoint),
        "ai_model": ns.ai_model,
        "webhook_configured": bool(ns.webhook_url),
        "created_at": ns.created_at,
    }


@router.get("/namespaces")
def list_namespaces(key: ApiKey = Depends(require_admin), session: Session = Depends(get_session)):
    q = select(Namespace)
    if key.namespace != "*":
        q = q.where(Namespace.name == key.namespace)
    return [_ns_out(ns) for ns in session.exec(q).all()]


@router.put("/namespaces/{name}")
def upsert_namespace(
    name: str,
    body: NamespaceIn,
    key: ApiKey = Depends(require_admin),
    session: Session = Depends(get_session),
):
    check_namespace(key, name)
    ns = session.exec(select(Namespace).where(Namespace.name == name)).first()
    created = ns is None
    if created:
        ns = Namespace(name=name)
    for field, value in body.model_dump().items():
        setattr(ns, field, value)
    session.add(ns)
    session.commit()
    session.refresh(ns)
    return {**_ns_out(ns), "created": created}


@router.delete("/ns/{namespace}")
def purge_namespace(
    namespace: str,
    key: ApiKey = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Remove a namespace and ALL its data (types, instances, logs, alerts,
    decisions, scoped keys). This is the GDPR/offboarding hammer -
    irreversible."""
    check_namespace(key, namespace)
    instances = session.exec(select(Instance).where(Instance.namespace == namespace)).all()
    instance_ids = [i.id for i in instances]
    counts = {
        "instances": len(instances),
        "logs": 0,
        "alerts": 0,
        "decisions": 0,
        "entity_types": 0,
        "keys_deleted": 0,
    }
    if instance_ids:
        counts["logs"] = session.execute(
            delete(LogEntry).where(LogEntry.instance_id.in_(instance_ids))  # type: ignore[union-attr]
        ).rowcount
    counts["alerts"] = session.execute(delete(Alert).where(Alert.namespace == namespace)).rowcount
    counts["decisions"] = session.execute(delete(Decision).where(Decision.namespace == namespace)).rowcount
    for i in instances:
        session.delete(i)
    counts["entity_types"] = session.execute(
        delete(EntityType).where(EntityType.namespace == namespace)
    ).rowcount
    for k in session.exec(select(ApiKey).where(ApiKey.namespace == namespace)).all():
        session.delete(k)
        counts["keys_deleted"] += 1
    ns = session.exec(select(Namespace).where(Namespace.name == namespace)).first()
    if ns:
        session.delete(ns)
    session.commit()
    return {"purged": namespace, **counts}


# ---------------------------------------------------------------- entity types

class EntityTypeIn(BaseModel):
    description: str = ""
    expected_every_seconds: Optional[int] = None
    fields: dict = {}
    constraints: list = []
    actions: list = []
    default_action: Optional[str] = None


def _etype_out(t: EntityType) -> dict:
    return {
        "namespace": t.namespace,
        "name": t.name,
        "description": t.description,
        "version": t.version,
        "expected_every_seconds": t.expected_every_seconds,
        "fields": t.fields_schema,
        "constraints": t.constraints,
        "actions": t.actions,
        "default_action": t.default_action,
        "updated_at": t.updated_at,
    }


def _validate_etype(body: EntityTypeIn) -> None:
    action_ids = set()
    for a in body.actions:
        if not isinstance(a, dict) or "id" not in a:
            raise HTTPException(status_code=422, detail="Each action needs at least an 'id'")
        action_ids.add(a["id"])
    if body.default_action and body.default_action not in action_ids:
        raise HTTPException(status_code=422, detail=f"default_action '{body.default_action}' not in actions")
    for i, c in enumerate(body.constraints):
        if not isinstance(c, dict) or "when" not in c:
            raise HTTPException(status_code=422, detail=f"Constraint #{i} needs a 'when' test")
        if c.get("action") and c["action"] not in action_ids:
            raise HTTPException(status_code=422, detail=f"Constraint #{i} action '{c['action']}' not in actions")


@router.get("/ns/{namespace}/entity-types")
def list_entity_types(namespace: str, key: ApiKey = Depends(require_admin), session: Session = Depends(get_session)):
    check_namespace(key, namespace)
    types = session.exec(select(EntityType).where(EntityType.namespace == namespace)).all()
    return [_etype_out(t) for t in types]


@router.put("/ns/{namespace}/entity-types/{name}")
def upsert_entity_type(
    namespace: str,
    name: str,
    body: EntityTypeIn,
    key: ApiKey = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Idempotent code-first registration: identical payloads are no-ops,
    changed payloads bump the version (DESIGN.md §8)."""
    check_namespace(key, namespace)
    _validate_etype(body)
    # Namespaces are auto-created on first use.
    if session.exec(select(Namespace).where(Namespace.name == namespace)).first() is None:
        session.add(Namespace(name=namespace))

    etype = session.exec(
        select(EntityType).where(EntityType.namespace == namespace, EntityType.name == name)
    ).first()
    incoming = body.model_dump()
    if etype is None:
        etype = EntityType(
            namespace=namespace,
            name=name,
            description=incoming["description"],
            expected_every_seconds=incoming["expected_every_seconds"],
            fields_schema=incoming["fields"],
            constraints=incoming["constraints"],
            actions=incoming["actions"],
            default_action=incoming["default_action"],
        )
        changed = True
    else:
        current = {
            "description": etype.description,
            "expected_every_seconds": etype.expected_every_seconds,
            "fields": etype.fields_schema,
            "constraints": etype.constraints,
            "actions": etype.actions,
            "default_action": etype.default_action,
        }
        changed = current != incoming
        if changed:
            etype.description = incoming["description"]
            etype.expected_every_seconds = incoming["expected_every_seconds"]
            etype.fields_schema = incoming["fields"]
            etype.constraints = incoming["constraints"]
            etype.actions = incoming["actions"]
            etype.default_action = incoming["default_action"]
            etype.version += 1
            etype.updated_at = utcnow()
    session.add(etype)
    session.commit()
    session.refresh(etype)
    return {**_etype_out(etype), "changed": changed}


# ---------------------------------------------------------------- instances

class InstanceIn(BaseModel):
    entity_type: str
    overrides: dict = {}


def _instance_out(i: Instance) -> dict:
    return {
        "id": i.id,
        "namespace": i.namespace,
        "name": i.name,
        "entity_type": i.entity_type,
        "state": i.state,
        "last_values": i.last_values,
        "last_seen_at": i.last_seen_at,
        "overrides": i.overrides,
        "created_at": i.created_at,
    }


@router.get("/instances")
def list_all_instances(key: ApiKey = Depends(require_admin), session: Session = Depends(get_session)):
    q = select(Instance)
    if key.namespace != "*":
        q = q.where(Instance.namespace == key.namespace)
    return [_instance_out(i) for i in session.exec(q).all()]


@router.get("/instances/{instance_id}")
def get_instance(instance_id: int, key: ApiKey = Depends(require_admin), session: Session = Depends(get_session)):
    instance = session.get(Instance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    check_namespace(key, instance.namespace)
    return _instance_out(instance)


@router.get("/instances/{instance_id}/logs")
def instance_logs(
    instance_id: int,
    limit: int = Query(default=100, le=1000),
    key: ApiKey = Depends(require_admin),
    session: Session = Depends(get_session),
):
    instance = session.get(Instance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    check_namespace(key, instance.namespace)
    entries = session.exec(
        select(LogEntry)
        .where(LogEntry.instance_id == instance_id)
        .order_by(LogEntry.ts.desc())  # type: ignore[union-attr]
        .limit(limit)
    ).all()
    return [
        {"id": e.id, "ts": e.ts, "received_at": e.received_at, "values": e.values, "meta": e.meta}
        for e in entries
    ]


@router.put("/ns/{namespace}/instances/{name}")
def upsert_instance(
    namespace: str,
    name: str,
    body: InstanceIn,
    key: ApiKey = Depends(require_admin),
    session: Session = Depends(get_session),
):
    check_namespace(key, namespace)
    etype = session.exec(
        select(EntityType).where(EntityType.namespace == namespace, EntityType.name == body.entity_type)
    ).first()
    if etype is None:
        raise HTTPException(status_code=422, detail=f"Unknown entity type '{body.entity_type}' in namespace '{namespace}'")
    instance = session.exec(
        select(Instance).where(Instance.namespace == namespace, Instance.name == name)
    ).first()
    created = instance is None
    if created:
        instance = Instance(namespace=namespace, name=name, entity_type=body.entity_type)
    instance.entity_type = body.entity_type
    instance.overrides = body.overrides
    session.add(instance)
    session.commit()
    session.refresh(instance)
    return {**_instance_out(instance), "created": created}


# ---------------------------------------------------------------- logs (ingest)

@router.post("/logs")
def ingest_logs(
    body: Any = Body(...),
    key: ApiKey = Depends(require_ingest),
    session: Session = Depends(get_session),
):
    """Accepts a single log object or a batch (list). Each item:
    {"namespace": "...", "instance": "...", "values": {...}, "ts"?: iso8601, "event_id"?: str, "meta"?: {}}
    """
    if not isinstance(body, (dict, list)):
        raise HTTPException(status_code=422, detail="Body must be a log object or a list of log objects")
    items = body if isinstance(body, list) else [body]
    if len(items) > 1000:
        raise HTTPException(status_code=422, detail="Batch too large (max 1000)")
    results = []
    for item in items:
        check_namespace(key, item.get("namespace", "default"))
        results.append(ingest_one(session, item))
    accepted = sum(1 for r in results if r["status"] == "ok")
    duplicates = sum(1 for r in results if r["status"] == "duplicate")
    return {"accepted": accepted, "duplicates": duplicates, "results": results}


# ---------------------------------------------------------------- alerts

def _alert_out(a: Alert, instance: Instance | None, decision: Decision | None) -> dict:
    return {
        "id": a.id,
        "namespace": a.namespace,
        "instance_id": a.instance_id,
        "instance_name": instance.name if instance else None,
        "entity_type": instance.entity_type if instance else None,
        "kind": a.kind,
        "constraint_index": a.constraint_index,
        "summary": a.summary,
        "status": a.status,
        "opened_at": a.opened_at,
        "acknowledged_at": a.acknowledged_at,
        "resolved_at": a.resolved_at,
        "decision": {
            "id": decision.id,
            "action": decision.action,
            "source": decision.source,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "delivery_status": decision.delivery_status,
        }
        if decision
        else None,
    }


@router.get("/alerts")
def list_alerts(
    status: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    key: ApiKey = Depends(require_admin),
    session: Session = Depends(get_session),
):
    q = select(Alert)
    if key.namespace != "*":
        q = q.where(Alert.namespace == key.namespace)
    if status:
        q = q.where(Alert.status == status)
    q = q.order_by(Alert.opened_at.desc()).limit(limit)  # type: ignore[union-attr]
    alerts = session.exec(q).all()
    instances = {i.id: i for i in session.exec(select(Instance)).all()}
    out = []
    for a in alerts:
        decision = session.exec(
            select(Decision).where(Decision.alert_id == a.id).order_by(Decision.id.desc())  # type: ignore[union-attr]
        ).first()
        out.append(_alert_out(a, instances.get(a.instance_id), decision))
    return out


@router.post("/alerts/{alert_id}/ack")
def acknowledge_alert(alert_id: int, key: ApiKey = Depends(require_admin), session: Session = Depends(get_session)):
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    check_namespace(key, alert.namespace)
    if alert.status == "active":
        alert.status = "acknowledged"
        alert.acknowledged_at = utcnow()
        session.add(alert)
        session.commit()
    return {"id": alert.id, "status": alert.status}


# ---------------------------------------------------------------- decisions (outbox poll)

@router.get("/decisions")
def poll_decisions(
    since: int = 0,
    limit: int = Query(default=100, le=500),
    key: ApiKey = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Poll the outbox with a cursor: pass the highest decision id you've seen."""
    q = select(Decision).where(Decision.id > since)
    if key.namespace != "*":
        q = q.where(Decision.namespace == key.namespace)
    decisions = session.exec(q.order_by(Decision.id).limit(limit)).all()  # type: ignore[arg-type]
    return {
        "cursor": decisions[-1].id if decisions else since,
        "decisions": [
            {
                "id": d.id,
                "namespace": d.namespace,
                "instance_id": d.instance_id,
                "alert_id": d.alert_id,
                "action": d.action,
                "source": d.source,
                "confidence": d.confidence,
                "reason": d.reason,
                "context_snapshot": d.context_snapshot,
                "delivery_status": d.delivery_status,
                "created_at": d.created_at,
            }
            for d in decisions
        ],
    }


# ---------------------------------------------------------------- api keys

class ApiKeyIn(BaseModel):
    name: str
    role: str = "ingest"
    namespace: str = "*"


def _key_out(k: ApiKey) -> dict:
    return {
        "id": k.id,
        "name": k.name,
        "key": k.key,  # None for keys created before raw storage; regenerate those
        "role": k.role,
        "namespace": k.namespace,
        "revoked": k.revoked,
        "created_at": k.created_at,
    }


@router.get("/keys")
def list_keys(key: ApiKey = Depends(require_admin), session: Session = Depends(get_session)):
    return [_key_out(k) for k in session.exec(select(ApiKey)).all()]


@router.post("/keys")
def create_key(body: ApiKeyIn, key: ApiKey = Depends(require_admin), session: Session = Depends(get_session)):
    if body.role not in ("admin", "ingest"):
        raise HTTPException(status_code=422, detail="role must be 'admin' or 'ingest'")
    if key.namespace != "*" and body.namespace != key.namespace:
        raise HTTPException(status_code=403, detail="Cannot create keys outside your namespace scope")
    raw = new_raw_key()
    record = ApiKey(name=body.name, key=raw, key_hash=hash_key(raw), role=body.role, namespace=body.namespace)
    session.add(record)
    session.commit()
    session.refresh(record)
    return _key_out(record)


@router.delete("/keys/{key_id}")
def delete_key(key_id: int, key: ApiKey = Depends(require_admin), session: Session = Depends(get_session)):
    record = session.get(ApiKey, key_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Key not found")
    session.delete(record)
    session.commit()
    return {"id": key_id, "deleted": True}
