from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.event import EventRecord
from app.schemas.patch import PatchOperation, StatePatchRecord


ActionType = Literal["move", "investigate", "talk", "rest", "wait", "unknown"]
RiskLevel = Literal["low", "medium", "high"]
OutcomeLevel = Literal["success", "partial", "quiet", "rested", "uncertain"]


class PlayerActionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    actor_id: str = Field(default="player", min_length=1, max_length=120)
    advance_time: bool = True


class ActionIntent(BaseModel):
    action_type: ActionType
    target_id: str | None = None
    target_name: str | None = None
    risk_level: RiskLevel = "medium"
    time_cost_slots: int = Field(default=1, ge=0, le=4)
    matched_location_ids: list[str] = Field(default_factory=list)
    matched_entity_ids: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ContextPack(BaseModel):
    current_day: int
    current_slot: str
    player_location_id: str | None = None
    player_location_name: str | None = None
    relevant_locations: dict[str, Any] = Field(default_factory=dict)
    relevant_entities: dict[str, Any] = Field(default_factory=dict)
    relevant_clocks: dict[str, Any] = Field(default_factory=dict)
    visible_facts: list[dict[str, Any]] = Field(default_factory=list)


class ActionOutcome(BaseModel):
    level: OutcomeLevel
    summary: str
    consequences: list[str] = Field(default_factory=list)
    operations: list[PatchOperation] = Field(default_factory=list)


class PlayerActionResponse(BaseModel):
    world_id: str
    action_text: str
    intent: ActionIntent
    context_pack: ContextPack
    outcome: ActionOutcome
    patch: StatePatchRecord | None = None
    event_queue_patch: StatePatchRecord | None = None
    triggered_events: list[EventRecord] = Field(default_factory=list)
    narrative: str
    resolved_at: datetime
