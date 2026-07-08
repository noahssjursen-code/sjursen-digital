"""Background loop (every TICK_SECONDS):

1. Silence detection: instances that stopped reporting.
2. Duration elapse: violations that cross for_seconds without new logs arriving.
3. Outbox push: deliver pending decisions to namespace webhooks (HMAC-signed,
   retried up to MAX_ATTEMPTS, then dead-lettered; pollers are unaffected).
"""
import asyncio
import hashlib
import hmac
import json
import logging

import httpx
from sqlmodel import Session, select

from .database import engine
from .decisions import make_decision
from .models import Decision, EntityType, Instance, Namespace, utcnow
from .rules import check_silence, process_instance

logger = logging.getLogger("komfyrvakt.scheduler")

TICK_SECONDS = 10
MAX_ATTEMPTS = 5


def _evaluate_all(session: Session) -> None:
    now = utcnow()
    instances = session.exec(select(Instance)).all()
    etypes = {
        (t.namespace, t.name): t
        for t in session.exec(select(EntityType)).all()
    }
    for instance in instances:
        etype = etypes.get((instance.namespace, instance.entity_type))
        if etype is None:
            continue
        silent_alert = check_silence(session, instance, etype, now)
        if silent_alert is not None:
            make_decision(session, instance, etype, silent_alert)
        if instance.state != "silent":
            opened = process_instance(session, instance, etype, now)
            for alert in opened:
                make_decision(session, instance, etype, alert)
    session.commit()


def _deliver_webhooks(session: Session) -> None:
    pending = session.exec(
        select(Decision).where(Decision.delivery_status == "pending", Decision.delivery_attempts < MAX_ATTEMPTS)
    ).all()
    if not pending:
        return
    namespaces = {n.name: n for n in session.exec(select(Namespace)).all()}
    for decision in pending:
        ns = namespaces.get(decision.namespace)
        if ns is None or not ns.webhook_url:
            decision.delivery_status = "none"
            session.add(decision)
            continue
        body = json.dumps(
            {
                "id": decision.id,
                "namespace": decision.namespace,
                "instance_id": decision.instance_id,
                "alert_id": decision.alert_id,
                "action": decision.action,
                "source": decision.source,
                "confidence": decision.confidence,
                "reason": decision.reason,
                "created_at": decision.created_at.isoformat(),
            },
            default=str,
        )
        headers = {"Content-Type": "application/json"}
        if ns.webhook_secret:
            sig = hmac.new(ns.webhook_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
            headers["X-Komfyrvakt-Signature"] = f"sha256={sig}"
        decision.delivery_attempts += 1
        try:
            resp = httpx.post(ns.webhook_url, content=body, headers=headers, timeout=10)
            if 200 <= resp.status_code < 300:
                decision.delivery_status = "delivered"
            elif decision.delivery_attempts >= MAX_ATTEMPTS:
                decision.delivery_status = "dead_letter"
        except Exception:
            if decision.delivery_attempts >= MAX_ATTEMPTS:
                decision.delivery_status = "dead_letter"
        session.add(decision)
    session.commit()


def _tick() -> None:
    with Session(engine) as session:
        _evaluate_all(session)
        _deliver_webhooks(session)


async def run_scheduler() -> None:
    while True:
        try:
            await asyncio.to_thread(_tick)
        except Exception:
            logger.exception("Scheduler tick failed")
        await asyncio.sleep(TICK_SECONDS)
