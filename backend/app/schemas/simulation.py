from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.event import EventRecord
from app.schemas.patch import StatePatchRecord


RiskLevel = Literal["low", "medium", "high"]


class WorldAdvanceRequest(BaseModel):
    reason: str = Field(default="Advance world simulation.", min_length=1, max_length=1000)
    risk_level: RiskLevel = "low"
    advance_time: bool = True
    clock_limit: int = Field(default=2, ge=0, le=20)
    tick_faction_plans: bool = True
    faction_plan_limit: int = Field(default=20, ge=0, le=100)


class WorldAdvanceResponse(BaseModel):
    world_id: str
    patch: StatePatchRecord
    event_queue_patch: StatePatchRecord | None = None
    triggered_events: list[EventRecord] = Field(default_factory=list)
    advanced_at: datetime


class DailySettlementRequest(BaseModel):
    reason: str = Field(default="Settle current world day.", min_length=1, max_length=1000)
    tick_faction_plans: bool = True
    faction_plan_limit: int = Field(default=100, ge=0, le=500)


class DailySettlementResponse(BaseModel):
    world_id: str
    settled_day: int
    new_day: int
    patch: StatePatchRecord
    event_queue_patch: StatePatchRecord | None = None
    triggered_events: list[EventRecord] = Field(default_factory=list)
    settled_at: datetime
