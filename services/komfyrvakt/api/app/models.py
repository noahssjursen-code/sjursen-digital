"""Database models. See DESIGN.md for the full data-model rationale.

Komfyrvakt is domain-agnostic: EntityType.fields_schema is an open dict of
typed fields declared by the customer. Nothing in here knows what the data
means.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import JSON, Column, Field, SQLModel, UniqueConstraint


def utcnow() -> datetime:
    return datetime.utcnow()


class Namespace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str = ""
    # AI policy is per-namespace: unset = AI disabled for this namespace.
    ai_endpoint: Optional[str] = None  # OpenAI-compatible base URL, e.g. http://ollama:11434/v1
    ai_model: Optional[str] = None
    ai_api_key: Optional[str] = None
    # Outbox push target: unset = poll-only delivery.
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class EntityType(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("namespace", "name"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    namespace: str = Field(index=True)
    name: str = Field(index=True)
    description: str = ""
    version: int = 1
    # Silence detection: expected reporting interval. None = never silence-checked.
    expected_every_seconds: Optional[int] = None
    # Open schema: {"temp_c": {"type": "number"}, "operator": {"type": "string", "sensitive": true}}
    fields_schema: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # List of constraint objects (see rules.py for the evaluated shape).
    constraints: list = Field(default_factory=list, sa_column=Column(JSON))
    # Closed action vocabulary: [{"id": "...", "description": "..."}]
    actions: list = Field(default_factory=list, sa_column=Column(JSON))
    default_action: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Instance(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("namespace", "name"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    namespace: str = Field(index=True)
    name: str = Field(index=True)
    entity_type: str
    # Optional per-instance constraint overrides: {"constraints": [...]} replaces the type's list.
    overrides: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # ok | suspect | alarm | silent
    state: str = Field(default="ok", index=True)
    # Last-known value per field (merged across log entries, for composite tests).
    last_values: dict = Field(default_factory=dict, sa_column=Column(JSON))
    last_seen_at: Optional[datetime] = None
    # Per-constraint violation tracking: {"0": {"violating_since": iso, "alert_id": 3}}
    constraint_state: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class LogEntry(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("instance_id", "dedupe_key"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    instance_id: int = Field(index=True, foreign_key="instance.id")
    ts: datetime = Field(index=True)          # event time (sensor-side)
    received_at: datetime = Field(default_factory=utcnow)
    values: dict = Field(default_factory=dict, sa_column=Column("field_values", JSON))
    meta: dict = Field(default_factory=dict, sa_column=Column(JSON))
    event_id: Optional[str] = None
    dedupe_key: str


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    namespace: str = Field(index=True)
    instance_id: int = Field(index=True, foreign_key="instance.id")
    kind: str = "constraint"                  # constraint | silent
    constraint_index: Optional[int] = None
    summary: str = ""
    status: str = Field(default="active", index=True)  # active | acknowledged | resolved
    opened_at: datetime = Field(default_factory=utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class Decision(SQLModel, table=True):
    """Outbox row. `id` is the monotonically increasing poll cursor."""

    id: Optional[int] = Field(default=None, primary_key=True)
    namespace: str = Field(index=True)
    instance_id: int = Field(foreign_key="instance.id")
    alert_id: Optional[int] = Field(default=None, foreign_key="alert.id")
    action: str
    source: str = "rule"                      # rule | ai | fallback
    confidence: Optional[float] = None
    reason: str = ""
    context_snapshot: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # none (no webhook configured) | pending | delivered | dead_letter
    delivery_status: str = Field(default="none", index=True)
    delivery_attempts: int = 0
    created_at: datetime = Field(default_factory=utcnow)


class ApiKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    key_hash: str = Field(unique=True, index=True)
    role: str = "ingest"                      # admin | ingest
    namespace: str = "*"                      # "*" or a specific namespace
    revoked: bool = False
    created_at: datetime = Field(default_factory=utcnow)
