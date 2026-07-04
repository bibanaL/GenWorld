from __future__ import annotations

from typing import Any

from app.engine.faction_plans import build_faction_plan_tick_operations
from app.engine.time import time_advance_operations
from app.schemas.patch import PatchOperation


def build_world_advance_operations(
    world_state: dict[str, Any],
    *,
    risk_level: str = "low",
    advance_time: bool = True,
    clock_limit: int = 2,
    tick_faction_plans: bool = True,
    faction_plan_limit: int = 20,
) -> list[PatchOperation]:
    operations: list[PatchOperation] = []
    clock_progress = _clock_progress(world_state.get("clocks", {}))

    operations.extend(
        _clock_operations(
            world_state.get("clocks", {}),
            delta=clock_delta(risk_level),
            limit=clock_limit,
            clock_progress=clock_progress,
        )
    )

    if tick_faction_plans:
        operations.extend(
            build_faction_plan_tick_operations(
                world_state,
                clock_progress=clock_progress,
                plan_limit=faction_plan_limit,
            )
        )

    if advance_time:
        operations.extend(
            PatchOperation.model_validate(operation)
            for operation in time_advance_operations(world_state.get("time", {}))
        )

    return operations


def clock_delta(risk_level: str) -> int:
    if risk_level == "high":
        return 7
    if risk_level == "medium":
        return 4
    return 2


def _clock_operations(
    clocks: dict[str, dict[str, Any]],
    *,
    delta: int,
    limit: int,
    clock_progress: dict[str, int | float],
) -> list[PatchOperation]:
    operations: list[PatchOperation] = []
    for clock_id, clock in list(clocks.items())[:limit]:
        progress = clock_progress.get(clock_id, number_or_default(clock.get("progress"), 0))
        max_progress = number_or_default(clock.get("max"), 100)
        if progress >= max_progress:
            continue
        next_progress = min(progress + delta, max_progress)
        clock_progress[clock_id] = next_progress
        operations.append(
            PatchOperation(
                op="set",
                path=f"/clocks/{clock_id}/progress",
                value=next_progress,
                note="World pressure tick capped at max.",
            )
        )
    return operations


def _clock_progress(clocks: dict[str, dict[str, Any]]) -> dict[str, int | float]:
    return {
        clock_id: number_or_default(clock.get("progress"), 0)
        for clock_id, clock in clocks.items()
    }


def number_or_default(value: Any, default: int | float) -> int | float:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return value
    return default
