from __future__ import annotations

from typing import Any

from app.engine.faction_plans import build_faction_plan_tick_operations
from app.schemas.patch import PatchOperation


def build_daily_settlement_operations(
    world_state: dict[str, Any],
    *,
    tick_faction_plans: bool = True,
    faction_plan_limit: int = 100,
) -> list[PatchOperation]:
    operations: list[PatchOperation] = []

    if tick_faction_plans:
        operations.extend(
            build_faction_plan_tick_operations(
                world_state,
                plan_limit=faction_plan_limit,
            )
        )

    next_day = int(world_state.get("time", {}).get("day", 1)) + 1
    slots = world_state.get("time", {}).get("slots_per_day") or [
        "morning",
        "afternoon",
        "evening",
        "night",
    ]
    first_slot = slots[0]

    operations.extend(
        [
            PatchOperation(
                op="set",
                path="/time/day",
                value=next_day,
                note="Daily settlement moves to next day.",
            ),
            PatchOperation(
                op="set",
                path="/time/slot",
                value=first_slot,
                note="Daily settlement resets to first time slot.",
            ),
            PatchOperation(
                op="set",
                path="/time/slot_index",
                value=0,
                note="Daily settlement resets slot index.",
            ),
        ]
    )

    return operations

