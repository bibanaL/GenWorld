from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.patch import PatchOperation


Visibility = Literal["public", "player_known", "hidden", "faction_known"]


class ExtensibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class TimeState(ExtensibleModel):
    day: int = Field(default=1, ge=1)
    slot: str = Field(default="morning", min_length=1)
    slot_index: int = Field(default=0, ge=0)
    slots_per_day: list[str] = Field(
        default_factory=lambda: ["morning", "afternoon", "evening", "night"]
    )


class StatusRecord(ExtensibleModel):
    id: str = Field(min_length=1)
    name: str | None = None
    intensity: int | None = Field(default=None, ge=0)
    duration_slots: int | None = Field(default=None, ge=0)
    source: str | None = None
    effects: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class RelationshipRecord(ExtensibleModel):
    target_id: str = Field(min_length=1)
    stance: str = "neutral"
    trust: int = Field(default=50, ge=0, le=100)
    tension: int = Field(default=0, ge=0, le=100)
    known_facts: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class KnowledgeState(ExtensibleModel):
    known_facts: list[str] = Field(default_factory=list)
    secrets_known: list[str] = Field(default_factory=list)
    suspicions: list[str] = Field(default_factory=list)


class ActorState(ExtensibleModel):
    current_location_id: str | None = None
    condition: dict[str, Any] = Field(default_factory=dict)
    resources: dict[str, Any] = Field(default_factory=dict)
    statuses: dict[str, StatusRecord] = Field(default_factory=dict)
    relationships: dict[str, RelationshipRecord] = Field(default_factory=dict)
    knowledge: KnowledgeState = Field(default_factory=KnowledgeState)
    secrets: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    traits: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlayerState(ActorState):
    id: str = "player"
    name: str | None = None
    identity: str | None = None


EntityKind = Literal["npc", "item", "artifact", "creature", "object", "other"]


class EntityState(ActorState):
    id: str = Field(min_length=1)
    kind: EntityKind = "other"
    name: str = Field(min_length=1)
    summary: str = ""
    owner_id: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class LocationState(ExtensibleModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: str = "place"
    summary: str = ""
    parent_id: str | None = None
    connected_to: list[str] = Field(default_factory=list)
    controlling_faction_id: str | None = None
    danger_level: int = Field(default=0, ge=0, le=100)
    resources: dict[str, Any] = Field(default_factory=dict)
    active_events: list[str] = Field(default_factory=list)
    hidden_features: list[str] = Field(default_factory=list)
    traits: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlanRecord(ExtensibleModel):
    id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    priority: int = Field(default=50, ge=0, le=100)
    progress: int = Field(default=0, ge=0, le=100)
    target_clock_id: str | None = None
    target_entity_ids: list[str] = Field(default_factory=list)
    target_location_ids: list[str] = Field(default_factory=list)
    status: str = "active"


class FactionState(ExtensibleModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    summary: str = ""
    ideology: str | None = None
    resources: dict[str, Any] = Field(default_factory=dict)
    goals: list[str] = Field(default_factory=list)
    plans: dict[str, PlanRecord] = Field(default_factory=dict)
    relationships: dict[str, RelationshipRecord] = Field(default_factory=dict)
    known_facts: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    controlled_location_ids: list[str] = Field(default_factory=list)
    traits: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClockState(ExtensibleModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    progress: int = Field(default=0, ge=0)
    max: int = Field(default=100, gt=0)
    owner_id: str | None = None
    visibility: Visibility = "hidden"
    trigger_event: str | None = None
    causes: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FactRecord(ExtensibleModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    visibility: Visibility = "hidden"
    known_by: list[str] = Field(default_factory=list)
    source_event_id: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FactLedger(ExtensibleModel):
    public: list[FactRecord] = Field(default_factory=list)
    player_known: list[FactRecord] = Field(default_factory=list)
    hidden: list[FactRecord] = Field(default_factory=list)
    faction_known: dict[str, list[FactRecord]] = Field(default_factory=dict)


class QueuedEvent(ExtensibleModel):
    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    trigger: dict[str, Any] = Field(default_factory=dict)
    earliest_day: int | None = Field(default=None, ge=1)
    latest_day: int | None = Field(default=None, ge=1)
    priority: int = Field(default=50, ge=0, le=100)
    visibility: Visibility = "hidden"
    payload: dict[str, Any] = Field(default_factory=dict)
    effects: list[PatchOperation] = Field(default_factory=list, max_length=12)


class WorldState(ExtensibleModel):
    schema_version: int = 1
    premise: str = ""
    seed: int | None = None
    time: TimeState = Field(default_factory=TimeState)
    player: PlayerState = Field(default_factory=PlayerState)
    entities: dict[str, EntityState] = Field(default_factory=dict)
    locations: dict[str, LocationState] = Field(default_factory=dict)
    factions: dict[str, FactionState] = Field(default_factory=dict)
    clocks: dict[str, ClockState] = Field(default_factory=dict)
    facts: FactLedger = Field(default_factory=FactLedger)
    event_queue: list[QueuedEvent] = Field(default_factory=list)
