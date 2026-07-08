from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, JSON

class StreamBase(SQLModel):
    name: str = Field(index=True)
    description: Optional[str] = None
    tags: Optional[Dict[str, str]] = Field(default_factory=dict, sa_type=JSON)

class Stream(StreamBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StreamCreate(StreamBase):
    pass

class LogEntryBase(SQLModel):
    stream_id: int = Field(foreign_key="stream.id", index=True)
    value: float  # Quantitative reading (e.g. 17.5 degrees)
    message: Optional[str] = None  # Qualitative text (e.g. "Door open")
    metadata_json: Optional[Dict[str, str]] = Field(default_factory=dict, sa_type=JSON)

class LogEntry(LogEntryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

class LogEntryCreate(LogEntryBase):
    pass

class RuleBase(SQLModel):
    stream_id: int = Field(foreign_key="stream.id")
    name: str
    parameter_name: str  # e.g., "value"
    operator: str  # "gt", "lt", "eq"
    threshold: float
    duration_seconds: int  # Trigger alert only if condition persists for X seconds
    actions: Optional[Dict[str, str]] = Field(default_factory=dict, sa_type=JSON) # e.g. {"on_trigger": "call_manager"}

class Rule(RuleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True)

class AlertBase(SQLModel):
    stream_id: int = Field(foreign_key="stream.id")
    rule_id: int = Field(foreign_key="rule.id")
    status: str = Field(default="active")  # "active", "resolved", "acknowledged"

class Alert(AlertBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    ai_decision: Optional[str] = None  # e.g. "call_manager - verified door open after hours"
