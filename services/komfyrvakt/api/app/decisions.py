"""Decision layer: when an alert opens, pick ONE action from the entity
type's closed action vocabulary.

Order of preference (DESIGN.md §5):
  1. AI, if the namespace has an ai_endpoint configured (OpenAI-compatible).
  2. Rule default (constraint-level action, then type default, then first action).
  3. Fallback = rule default, used when the AI call fails or answers garbage.

The AI never invents actions. It only picks from the list.
"""
import json

import httpx
from sqlmodel import Session, select

from .models import Alert, Decision, EntityType, Instance, LogEntry, Namespace
from .validation import redact

AI_TIMEOUT_SECONDS = 15

SYSTEM_PROMPT = (
    "You are Komfyrvakt, a safety decision engine. An alert has fired for a "
    "monitored entity. Based on the context, choose exactly one action from "
    "the allowed list. Respond with ONLY a JSON object, no prose: "
    '{"action": "<one allowed action id>", "confidence": <0.0-1.0>, "reason": "<one sentence>"}'
)


def build_context(session: Session, instance: Instance, etype: EntityType, alert: Alert) -> dict:
    recent = session.exec(
        select(LogEntry)
        .where(LogEntry.instance_id == instance.id)
        .order_by(LogEntry.ts.desc())  # type: ignore[union-attr]
        .limit(20)
    ).all()
    constraints = etype.constraints or []
    constraint = None
    if alert.constraint_index is not None and alert.constraint_index < len(constraints):
        constraint = constraints[alert.constraint_index]
    return {
        "alert": {"kind": alert.kind, "summary": alert.summary, "opened_at": alert.opened_at.isoformat()},
        "entity_type": {"name": etype.name, "description": etype.description},
        "instance": {"namespace": instance.namespace, "name": instance.name, "state": instance.state},
        "violated_constraint": constraint,
        "last_values": redact(instance.last_values or {}, etype.fields_schema or {}),
        "recent_logs": [
            {"ts": e.ts.isoformat(), "values": redact(e.values or {}, etype.fields_schema or {})}
            for e in reversed(recent)
        ],
        "allowed_actions": etype.actions or [],
    }


def rule_default_action(etype: EntityType, alert: Alert) -> str:
    constraints = etype.constraints or []
    if alert.constraint_index is not None and alert.constraint_index < len(constraints):
        per_constraint = constraints[alert.constraint_index].get("action")
        if per_constraint:
            return per_constraint
    if etype.default_action:
        return etype.default_action
    actions = etype.actions or []
    return actions[0]["id"] if actions else "noop"


def call_ai(ns: Namespace, context: dict) -> dict:
    url = ns.ai_endpoint.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if ns.ai_api_key:
        headers["Authorization"] = f"Bearer {ns.ai_api_key}"
    body = {
        "model": ns.ai_model or "",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context, default=str)},
        ],
    }
    resp = httpx.post(url, json=body, headers=headers, timeout=AI_TIMEOUT_SECONDS)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("AI response contained no JSON object")
    return json.loads(content[start : end + 1])


def make_decision(session: Session, instance: Instance, etype: EntityType, alert: Alert) -> Decision:
    ns = session.exec(select(Namespace).where(Namespace.name == instance.namespace)).first()
    context = build_context(session, instance, etype, alert)
    allowed_ids = {a["id"] for a in (etype.actions or [])}
    default = rule_default_action(etype, alert)

    action, source, confidence, reason = default, "rule", None, "Rule default (AI not configured for this namespace)"

    if ns and ns.ai_endpoint:
        try:
            ai = call_ai(ns, context)
            if ai.get("action") in allowed_ids:
                action = ai["action"]
                source = "ai"
                confidence = ai.get("confidence")
                reason = str(ai.get("reason", ""))
            else:
                source = "fallback"
                reason = f"AI proposed unknown action '{ai.get('action')}', fell back to rule default"
        except Exception as exc:  # AI is an enhancement; failures must never block a decision.
            source = "fallback"
            reason = f"AI call failed ({type(exc).__name__}), fell back to rule default"

    decision = Decision(
        namespace=instance.namespace,
        instance_id=instance.id,
        alert_id=alert.id,
        action=action,
        source=source,
        confidence=confidence,
        reason=reason,
        context_snapshot=context,
        delivery_status="pending" if (ns and ns.webhook_url) else "none",
    )
    session.add(decision)
    session.flush()
    return decision
