from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.patch import PatchOperation
from app.schemas.state import EntityKind, Visibility
from app.schemas.world import WorldRecord


class WorldGenerationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    premise: str = Field(min_length=1, max_length=4000)
    seed: int | None = None
    faction_count: int = Field(default=3, ge=2, le=5)
    location_count: int = Field(default=7, ge=3, le=12)
    entity_count: int = Field(default=8, ge=3, le=15)
    clock_count: int = Field(default=4, ge=2, le=6)
    generator: Literal["local"] = "local"


class SeedFaction(BaseModel):
    id: str
    name: str
    summary: str
    ideology: str
    goals: list[str]
    resources: dict[str, int]
    secrets: list[str] = Field(default_factory=list)


class SeedLocation(BaseModel):
    id: str
    name: str
    kind: str
    summary: str
    danger_level: int = Field(ge=0, le=100)
    controlling_faction_id: str | None = None
    connected_to: list[str] = Field(default_factory=list)
    hidden_features: list[str] = Field(default_factory=list)


class SeedEntity(BaseModel):
    id: str
    kind: EntityKind
    name: str
    summary: str
    current_location_id: str | None = None
    owner_id: str | None = None
    goals: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)


class SeedClock(BaseModel):
    id: str
    name: str
    progress: int = Field(ge=0)
    max: int = Field(default=100, gt=0)
    owner_id: str | None = None
    visibility: Visibility = "hidden"
    trigger_event: str
    causes: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)


class SeedFact(BaseModel):
    id: str
    text: str
    visibility: Visibility
    known_by: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class SeedQueuedEvent(BaseModel):
    id: str
    type: str
    summary: str
    trigger: dict
    earliest_day: int | None = Field(default=None, ge=1)
    latest_day: int | None = Field(default=None, ge=1)
    priority: int = Field(default=50, ge=0, le=100)
    visibility: Visibility = "hidden"
    payload: dict = Field(default_factory=dict)
    effects: list[PatchOperation] = Field(default_factory=list, max_length=12)


class WorldSeed(BaseModel):
    premise: str
    core_conflict: str
    player_identity: str
    factions: list[SeedFaction]
    locations: list[SeedLocation]
    entities: list[SeedEntity]
    clocks: list[SeedClock]
    public_facts: list[SeedFact]
    player_known_facts: list[SeedFact]
    hidden_facts: list[SeedFact]
    queued_events: list[SeedQueuedEvent]


class WorldGenerationResponse(BaseModel):
    world: WorldRecord
    seed: WorldSeed
