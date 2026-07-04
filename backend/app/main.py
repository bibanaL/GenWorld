from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException

from app.agents.world_generator import LocalWorldSeedGenerator
from app.config import get_settings
from app.engine.simulator import build_world_advance_operations
from app.engine.world_builder import build_world_state_from_seed
from app.graph.player_action_graph import PlayerActionGraphRunner
from app.schemas.action import PlayerActionRequest, PlayerActionResponse
from app.schemas.event import EventCreateRequest, EventRecord
from app.schemas.generation import WorldGenerationRequest, WorldGenerationResponse
from app.schemas.patch import StatePatchRecord, StatePatchRequest
from app.schemas.simulation import (
    DailySettlementRequest,
    DailySettlementResponse,
    WorldAdvanceRequest,
    WorldAdvanceResponse,
)
from app.schemas.world import WorldCreateRequest, WorldRecord, WorldSummary
from app.services.daily_settlement_service import settle_day
from app.services.event_queue_service import process_event_queue
from app.storage.sqlite_store import SQLiteLedger, StatePatchRejected


settings = get_settings()
ledger = SQLiteLedger(settings.resolved_database_path)
world_seed_generator = LocalWorldSeedGenerator()
player_action_graph = PlayerActionGraphRunner(ledger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ledger.init_schema()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


def get_ledger() -> SQLiteLedger:
    return ledger


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "database": str(settings.resolved_database_path),
    }


@app.post("/worlds", response_model=WorldRecord)
def create_world(
    request: WorldCreateRequest,
    store: SQLiteLedger = Depends(get_ledger),
) -> dict:
    return store.create_world(
        name=request.name,
        premise=request.premise,
        seed=request.seed,
        initial_state=request.initial_state,
    )


@app.get("/worlds", response_model=list[WorldSummary])
def list_worlds(store: SQLiteLedger = Depends(get_ledger)) -> list[dict]:
    return store.list_worlds()


@app.post("/worlds/generate", response_model=WorldGenerationResponse)
def generate_world(
    request: WorldGenerationRequest,
    store: SQLiteLedger = Depends(get_ledger),
) -> dict:
    world_seed = world_seed_generator.generate(request)
    state = build_world_state_from_seed(seed=world_seed, numeric_seed=request.seed)
    world = store.create_world(
        name=request.name,
        premise=request.premise,
        seed=request.seed,
        initial_state=state,
    )
    store.append_event(
        world_id=world["id"],
        type_="world_seed_generated",
        summary="Structured world seed generated.",
        payload=world_seed.model_dump(mode="json"),
    )
    return {"world": world, "seed": world_seed}


@app.get("/worlds/{world_id}", response_model=WorldRecord)
def get_world(
    world_id: str,
    store: SQLiteLedger = Depends(get_ledger),
) -> dict:
    world = store.get_world(world_id)
    if world is None:
        raise HTTPException(status_code=404, detail="World not found")
    return world


@app.post("/worlds/{world_id}/actions", response_model=PlayerActionResponse)
def resolve_player_action(
    world_id: str,
    request: PlayerActionRequest,
) -> dict:
    try:
        result = player_action_graph.run(world_id, request)
    except KeyError:
        raise HTTPException(status_code=404, detail="World not found") from None
    except StatePatchRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    return {
        "world_id": world_id,
        "action_text": result["action_text"],
        "intent": result["intent"],
        "context_pack": result["context_pack"],
        "outcome": result["outcome"],
        "patch": result["patch"],
        "event_queue_patch": result.get("event_queue_patch"),
        "triggered_events": result.get("triggered_events", []),
        "narrative": result["narrative"],
        "resolved_at": result["resolved_at"],
    }


@app.post("/worlds/{world_id}/advance", response_model=WorldAdvanceResponse)
def advance_world(
    world_id: str,
    request: WorldAdvanceRequest,
    store: SQLiteLedger = Depends(get_ledger),
) -> dict:
    world = store.get_world(world_id)
    if world is None:
        raise HTTPException(status_code=404, detail="World not found")

    operations = build_world_advance_operations(
        world["state"],
        risk_level=request.risk_level,
        advance_time=request.advance_time,
        clock_limit=request.clock_limit,
        tick_faction_plans=request.tick_faction_plans,
        faction_plan_limit=request.faction_plan_limit,
    )
    if not operations:
        raise HTTPException(status_code=422, detail="No simulation operations were produced.")

    try:
        patch = store.apply_state_patch(
            world_id=world_id,
            reason=request.reason,
            source_agent="world_simulator.local",
            permission_level="system",
            operations=operations,
        )
    except StatePatchRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    store.append_event(
        world_id=world_id,
        type_="world_advanced",
        summary=request.reason,
        payload={
            "risk_level": request.risk_level,
            "advance_time": request.advance_time,
            "clock_limit": request.clock_limit,
            "tick_faction_plans": request.tick_faction_plans,
            "faction_plan_limit": request.faction_plan_limit,
            "patch_id": patch["id"],
        },
    )
    try:
        event_queue_result = process_event_queue(ledger=store, world_id=world_id)
    except StatePatchRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    return {
        "world_id": world_id,
        "patch": patch,
        "event_queue_patch": event_queue_result.patch,
        "triggered_events": event_queue_result.triggered_events,
        "advanced_at": patch["applied_at"],
    }


@app.post("/worlds/{world_id}/settle-day", response_model=DailySettlementResponse)
def settle_world_day(
    world_id: str,
    request: DailySettlementRequest,
    store: SQLiteLedger = Depends(get_ledger),
) -> dict:
    try:
        result = settle_day(
            ledger=store,
            world_id=world_id,
            reason=request.reason,
            tick_faction_plans=request.tick_faction_plans,
            faction_plan_limit=request.faction_plan_limit,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="World not found") from None
    except StatePatchRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    return {
        "world_id": world_id,
        "settled_day": result.settled_day,
        "new_day": result.new_day,
        "patch": result.settlement_patch,
        "event_queue_patch": result.event_queue_patch,
        "triggered_events": result.triggered_events,
        "settled_at": result.settlement_patch["applied_at"],
    }


@app.post("/worlds/{world_id}/events", response_model=EventRecord)
def append_event(
    world_id: str,
    request: EventCreateRequest,
    store: SQLiteLedger = Depends(get_ledger),
) -> dict:
    try:
        return store.append_event(
            world_id=world_id,
            type_=request.type,
            summary=request.summary,
            payload=request.payload,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="World not found") from None


@app.get("/worlds/{world_id}/events", response_model=list[EventRecord])
def list_events(
    world_id: str,
    store: SQLiteLedger = Depends(get_ledger),
) -> list[dict]:
    if store.get_world(world_id) is None:
        raise HTTPException(status_code=404, detail="World not found")
    return store.list_events(world_id)


@app.post("/worlds/{world_id}/patches", response_model=StatePatchRecord)
def apply_state_patch(
    world_id: str,
    request: StatePatchRequest,
    store: SQLiteLedger = Depends(get_ledger),
) -> dict:
    try:
        return store.apply_state_patch(
            world_id=world_id,
            reason=request.reason,
            source_agent=request.source_agent,
            permission_level=request.permission_level,
            operations=request.operations,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="World not found") from None
    except StatePatchRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@app.get("/worlds/{world_id}/patches", response_model=list[StatePatchRecord])
def list_state_patches(
    world_id: str,
    store: SQLiteLedger = Depends(get_ledger),
) -> list[dict]:
    if store.get_world(world_id) is None:
        raise HTTPException(status_code=404, detail="World not found")
    return store.list_state_patches(world_id)
