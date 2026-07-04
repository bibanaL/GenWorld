from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


PatchOp = Literal[
    "set",
    "increase",
    "decrease",
    "append",
    "remove",
    "add_status",
    "remove_status",
]

PermissionLevel = Literal["low", "medium", "high", "system"]


class PatchOperation(BaseModel):
    op: PatchOp
    path: str = Field(min_length=1, max_length=300)
    value: Any = None
    note: str | None = Field(default=None, max_length=500)

    @field_validator("path")
    @classmethod
    def validate_json_pointer(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("Patch path must be a JSON Pointer starting with '/'.")
        if "//" in value:
            raise ValueError("Patch path cannot contain empty segments.")
        return value


class StatePatchRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)
    source_agent: str = Field(default="manual", min_length=1, max_length=120)
    permission_level: PermissionLevel = "system"
    operations: list[PatchOperation] = Field(min_length=1, max_length=50)


class StatePatchRecord(BaseModel):
    id: str
    world_id: str
    reason: str
    source_agent: str
    permission_level: PermissionLevel
    operations: list[PatchOperation]
    status: str
    error: str | None = None
    created_at: datetime
    applied_at: datetime | None = None

