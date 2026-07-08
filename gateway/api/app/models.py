"""Database models for the Sjursen Digital gateway."""
from datetime import datetime
from typing import Optional

from sqlmodel import JSON, Column, Field, SQLModel


def utcnow() -> datetime:
    return datetime.utcnow()


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utcnow)


class License(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    license_key: str = Field(unique=True, index=True)
    customer_name: str
    customer_email: str
    # JSON containing enabled modules: {"komfyrvakt": true, "obsero": false}
    modules: dict = Field(default_factory=dict, sa_column=Column(JSON))
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
