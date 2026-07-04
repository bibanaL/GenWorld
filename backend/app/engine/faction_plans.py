from __future__ import annotations

import hashlib
from typing import Any

from app.schemas.patch import PatchOperation


def build_faction_plan_tick_operations(
    world_state: dict[str, Any],
    *,
    clock_progress: dict[str, int | float] | None = None,
    plan_limit: int = 20,
) -> list[PatchOperation]:
    operations: list[PatchOperation] = []
    factions = world_state.get("factions", {})
    clocks = world_state.get("clocks", {})
    current_day = int(number_or_default(world_state.get("time", {}).get("day"), 1))
    tracked_clock_progress = clock_progress if clock_progress is not None else _clock_progress(clocks)

    ticked = 0
    for faction_id, faction in factions.items():
        plans = faction.get("plans", {})
        for plan_id, plan in plans.items():
            if ticked >= plan_limit:
                return operations
            if plan.get("status", "active") != "active":
                continue

            progress = number_or_default(plan.get("progress"), 0)
            if progress >= 100:
                continue

            plan_delta = _plan_delta(plan)
            next_progress = min(progress + plan_delta, 100)
            operations.append(
                PatchOperation(
                    op="set",
                    path=f"/factions/{faction_id}/plans/{plan_id}/progress",
                    value=next_progress,
                    note="Faction plan tick.",
                )
            )

            if next_progress >= 100:
                operations.append(
                    PatchOperation(
                        op="set",
                        path=f"/factions/{faction_id}/plans/{plan_id}/status",
                        value="completed",
                        note="Faction plan completed.",
                    )
                )
                operations.append(
                    PatchOperation(
                        op="append",
                        path="/event_queue",
                        value=_plan_completed_queued_event(
                            faction_id=faction_id,
                            faction=faction,
                            plan_id=plan_id,
                            plan=plan,
                            current_day=current_day,
                        ),
                        note="Create follow-up queued event for completed faction plan.",
                    )
                )

            target_clock_id = plan.get("target_clock_id")
            if target_clock_id and target_clock_id in clocks:
                clock_operation = _target_clock_operation(
                    clock_id=target_clock_id,
                    clock=clocks[target_clock_id],
                    clock_progress=tracked_clock_progress,
                    delta=_target_clock_delta(plan_delta),
                )
                if clock_operation is not None:
                    operations.append(clock_operation)

            ticked += 1

    return operations


def _clock_progress(clocks: dict[str, dict[str, Any]]) -> dict[str, int | float]:
    return {
        clock_id: number_or_default(clock.get("progress"), 0)
        for clock_id, clock in clocks.items()
    }


def _plan_delta(plan: dict[str, Any]) -> int:
    priority = number_or_default(plan.get("priority"), 50)
    return max(1, min(5, int(priority) // 25))


def _target_clock_delta(plan_delta: int) -> int:
    return max(1, min(2, plan_delta // 2))


def _target_clock_operation(
    *,
    clock_id: str,
    clock: dict[str, Any],
    clock_progress: dict[str, int | float],
    delta: int,
) -> PatchOperation | None:
    progress = clock_progress.get(clock_id, number_or_default(clock.get("progress"), 0))
    max_progress = number_or_default(clock.get("max"), 100)
    if progress >= max_progress:
        return None

    next_progress = min(progress + delta, max_progress)
    clock_progress[clock_id] = next_progress
    return PatchOperation(
        op="set",
        path=f"/clocks/{clock_id}/progress",
        value=next_progress,
        note="Faction plan advances target clock.",
    )


def _plan_completed_queued_event(
    *,
    faction_id: str,
    faction: dict[str, Any],
    plan_id: str,
    plan: dict[str, Any],
    current_day: int,
) -> dict[str, Any]:
    event_id = _plan_completed_event_id(faction_id=faction_id, plan_id=plan_id)
    faction_name = faction.get("name", faction_id)
    plan_summary = plan.get("summary", plan_id)
    return {
        "id": event_id,
        "type": "faction_plan_followup",
        "summary": f"{faction_name} completed a plan: {plan_summary}",
        "trigger": {
            "type": "plan_completed",
            "faction_id": faction_id,
            "plan_id": plan_id,
        },
        "earliest_day": current_day + 1,
        "latest_day": current_day + 3,
        "priority": int(number_or_default(plan.get("priority"), 50)),
        "visibility": "hidden",
        "payload": {
            "faction_id": faction_id,
            "faction_name": faction_name,
            "plan_id": plan_id,
            "plan_summary": plan_summary,
            "target_clock_id": plan.get("target_clock_id"),
            "target_entity_ids": plan.get("target_entity_ids", []),
            "target_location_ids": plan.get("target_location_ids", []),
        },
    }


def _plan_completed_event_id(*, faction_id: str, plan_id: str) -> str:
    digest = hashlib.sha256(f"{faction_id}:{plan_id}:completed".encode("utf-8")).hexdigest()
    return f"queued_plan_completed_{digest[:12]}"


def number_or_default(value: Any, default: int | float) -> int | float:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return value
    return default
