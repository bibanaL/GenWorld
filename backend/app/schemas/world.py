from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.state import WorldState


class WorldCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    premise: str = Field(min_length=1, max_length=4000)
    seed: int | None = None
    initial_state: WorldState | None = None


class WorldSummary(BaseModel):
    id: str
    name: str
    premise: str
    created_at: datetime
    updated_at: datetime


class WorldRecord(WorldSummary):
    state: dict[str, Any]
