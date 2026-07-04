from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.patch import PatchOperation


class TriggeredQueuedEvent(BaseModel):
    queued_event_id: str
    queued_event_type: str
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)
    overdue: bool = False


class EventQueueProcessingPlan(BaseModel):
    operations: list[PatchOperation] = Field(default_factory=list)
    triggered_events: list[TriggeredQueuedEvent] = Field(default_factory=list)


def build_event_queue_processing_plan(world_state: dict[str, Any]) -> EventQueueProcessingPlan:
    current_day = int(world_state.get("time", {}).get("day", 1))
    clocks = world_state.get("clocks", {})
    factions = world_state.get("factions", {})
    event_queue = world_state.get("event_queue", [])

    triggered: list[tuple[int, TriggeredQueuedEvent]] = []
    for index, queued_event in enumerate(event_queue):
        triggered_event = _maybe_trigger_event(
            queued_event=queued_event,
            clocks=clocks,
            factions=factions,
            current_day=current_day,
        )
        if triggered_event is not None:
            triggered.append((index, triggered_event))

    operations = [
        PatchOperation(
            op="remove",
            path=f"/event_queue/{index}",
            note="Remove triggered queued event.",
        )
        for index, _ in sorted(triggered, key=lambda item: item[0], reverse=True)
    ]

    return EventQueueProcessingPlan(
        operations=operations,
        triggered_events=[event for _, event in triggered],
    )


def _maybe_trigger_event(
    *,
    queued_event: dict[str, Any],
    clocks: dict[str, dict[str, Any]],
    factions: dict[str, dict[str, Any]],
    current_day: int,
) -> TriggeredQueuedEvent | None:
    earliest_day = queued_event.get("earliest_day")
    if earliest_day is not None and current_day < int(earliest_day):
        return None

    trigger = queued_event.get("trigger") or {}
    if trigger.get("type") == "plan_completed":
        return _maybe_trigger_plan_completed_event(
            queued_event=queued_event,
            trigger=trigger,
            factions=factions,
            current_day=current_day,
        )

    clock_id = trigger.get("clock_id")
    if not clock_id:
        return None

    clock = clocks.get(clock_id)
    if clock is None:
        return None

    progress = _number_or_default(clock.get("progress"), 0)
    threshold = _number_or_default(trigger.get("progress_at_least"), clock.get("max", 100))
    if progress < threshold:
        return None

    latest_day = queued_event.get("latest_day")
    overdue = latest_day is not None and current_day > int(latest_day)
    scheduled_window = {
        "earliest_day": earliest_day,
        "latest_day": latest_day,
    }

    payload = dict(queued_event.get("payload") or {})
    payload.update(
        {
            "queued_event_id": queued_event.get("id"),
            "queued_event_type": queued_event.get("type"),
            "trigger": trigger,
            "clock": {
                "id": clock_id,
                "name": clock.get("name"),
                "progress": progress,
                "max": clock.get("max"),
            },
            "overdue": overdue,
            "scheduled_window": scheduled_window,
        }
    )

    return TriggeredQueuedEvent(
        queued_event_id=queued_event.get("id", "unknown_queued_event"),
        queued_event_type=queued_event.get("type", "unknown"),
        summary=queued_event.get("summary", "Queued event triggered."),
        payload=payload,
        overdue=overdue,
    )


def _maybe_trigger_plan_completed_event(
    *,
    queued_event: dict[str, Any],
    trigger: dict[str, Any],
    factions: dict[str, dict[str, Any]],
    current_day: int,
) -> TriggeredQueuedEvent | None:
    faction_id = trigger.get("faction_id")
    plan_id = trigger.get("plan_id")
    if not faction_id or not plan_id:
        return None

    faction = factions.get(faction_id)
    if faction is None:
        return None

    plan = faction.get("plans", {}).get(plan_id)
    if plan is None or plan.get("status") != "completed":
        return None

    latest_day = queued_event.get("latest_day")
    overdue = latest_day is not None and current_day > int(latest_day)
    scheduled_window = {
        "earliest_day": queued_event.get("earliest_day"),
        "latest_day": latest_day,
    }

    payload = dict(queued_event.get("payload") or {})
    payload.update(
        {
            "queued_event_id": queued_event.get("id"),
            "queued_event_type": queued_event.get("type"),
            "trigger": trigger,
            "plan": {
                "faction_id": faction_id,
                "faction_name": faction.get("name"),
                "plan_id": plan_id,
                "summary": plan.get("summary"),
                "status": plan.get("status"),
                "progress": plan.get("progress"),
            },
            "overdue": overdue,
            "scheduled_window": scheduled_window,
        }
    )

    return TriggeredQueuedEvent(
        queued_event_id=queued_event.get("id", "unknown_queued_event"),
        queued_event_type=queued_event.get("type", "unknown"),
        summary=queued_event.get("summary", "Faction plan follow-up triggered."),
        payload=payload,
        overdue=overdue,
    )


def _number_or_default(value: Any, default: int | float) -> int | float:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return value
    return default
