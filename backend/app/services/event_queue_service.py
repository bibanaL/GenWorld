from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.engine.event_effects import EventEffectError
from app.engine.event_queue import build_event_queue_processing_plan
from app.engine.patches import PatchApplyError, apply_patch_operations
from app.schemas.patch import PatchOperation
from app.storage.sqlite_store import SQLiteLedger, StatePatchRejected


class EventQueueProcessingResult(BaseModel):
    patch: dict[str, Any] | None = None
    triggered_events: list[dict[str, Any]] = Field(default_factory=list)


def process_event_queue(
    *,
    ledger: SQLiteLedger,
    world_id: str,
) -> EventQueueProcessingResult:
    world = ledger.get_world(world_id)
    if world is None:
        raise KeyError(world_id)

    try:
        plan = build_event_queue_processing_plan(world["state"])
    except EventEffectError as exc:
        raise StatePatchRejected(str(exc)) from exc
    if not plan.operations:
        return EventQueueProcessingResult()

    patch = ledger.apply_state_patch(
        world_id=world_id,
        reason="Process triggered queued events.",
        source_agent="event_queue.local",
        permission_level="system",
        operations=plan.operations,
    )

    triggered_events = [
        ledger.append_event(
            world_id=world_id,
            type_="queued_event_triggered",
            summary=triggered_event.summary,
            payload=triggered_event.payload,
        )
        for triggered_event in plan.triggered_events
    ]

    return EventQueueProcessingResult(
        patch=patch,
        triggered_events=triggered_events,
    )


def preflight_event_queue_after_operations(
    *,
    world_state: dict[str, Any],
    operations: list[PatchOperation],
) -> None:
    try:
        preview_state = apply_patch_operations(world_state, operations)
        build_event_queue_processing_plan(preview_state)
    except (EventEffectError, PatchApplyError) as exc:
        raise StatePatchRejected(str(exc)) from exc
