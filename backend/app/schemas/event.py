from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventCreateRequest(BaseModel):
    type: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)


class EventRecord(BaseModel):
    id: str
    world_id: str
    type: str
    summary: str
    payload: dict[str, Any]
    created_at: datetime

