from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.engine.daily_settlement import build_daily_settlement_operations
from app.services.event_queue_service import EventQueueProcessingResult, process_event_queue
from app.storage.sqlite_store import SQLiteLedger


class DailySettlementResult(BaseModel):
    settlement_patch: dict[str, Any]
    event_queue_patch: dict[str, Any] | None = None
    triggered_events: list[dict[str, Any]] = Field(default_factory=list)
    settled_day: int
    new_day: int


def settle_day(
    *,
    ledger: SQLiteLedger,
    world_id: str,
    reason: str,
    tick_faction_plans: bool,
    faction_plan_limit: int,
) -> DailySettlementResult:
    world = ledger.get_world(world_id)
    if world is None:
        raise KeyError(world_id)

    settled_day = int(world["state"].get("time", {}).get("day", 1))
    operations = build_daily_settlement_operations(
        world["state"],
        tick_faction_plans=tick_faction_plans,
        faction_plan_limit=faction_plan_limit,
    )

    settlement_patch = ledger.apply_state_patch(
        world_id=world_id,
        reason=reason,
        source_agent="daily_settlement.local",
        permission_level="system",
        operations=operations,
    )

    new_world = ledger.get_world(world_id)
    if new_world is None:
        raise KeyError(world_id)
    new_day = int(new_world["state"].get("time", {}).get("day", settled_day + 1))

    ledger.append_event(
        world_id=world_id,
        type_="daily_settlement",
        summary=reason,
        payload={
            "settled_day": settled_day,
            "new_day": new_day,
            "tick_faction_plans": tick_faction_plans,
            "faction_plan_limit": faction_plan_limit,
            "patch_id": settlement_patch["id"],
        },
    )

    event_queue_result: EventQueueProcessingResult = process_event_queue(
        ledger=ledger,
        world_id=world_id,
    )

    return DailySettlementResult(
        settlement_patch=settlement_patch,
        event_queue_patch=event_queue_result.patch,
        triggered_events=event_queue_result.triggered_events,
        settled_day=settled_day,
        new_day=new_day,
    )

