from __future__ import annotations

import hashlib
from typing import Any

from app.engine.simulator import number_or_default
from app.schemas.action import ActionIntent, ActionOutcome, ContextPack
from app.schemas.patch import PatchOperation


def resolve_player_action(
    *,
    world_id: str,
    action_text: str,
    world_state: dict[str, Any],
    intent: ActionIntent,
    context: ContextPack,
) -> ActionOutcome:
    operations: list[PatchOperation] = []
    consequences: list[str] = []

    if intent.action_type == "move" and intent.target_id:
        operations.append(
            PatchOperation(
                op="set",
                path="/player/current_location_id",
                value=intent.target_id,
                note="Player moved to a matched location.",
            )
        )
        summary = f"You move toward {intent.target_name}."
        consequences.append("Your position changes.")
    elif intent.action_type == "rest":
        player_condition = world_state.get("player", {}).get("condition", {})
        fatigue = number_or_default(player_condition.get("fatigue"), 0)
        exposure = number_or_default(player_condition.get("exposure"), 0)
        operations.extend(
            [
                PatchOperation(
                    op="set",
                    path="/player/condition/fatigue",
                    value=max(fatigue - 20, 0),
                    note="Rest reduces fatigue without going below zero.",
                ),
                PatchOperation(
                    op="set",
                    path="/player/condition/exposure",
                    value=max(exposure - 2, 0),
                    note="Keeping quiet reduces exposure without going below zero.",
                ),
            ]
        )
        summary = "You take time to recover and reduce immediate pressure."
        consequences.append("Fatigue drops if it was present.")
    elif intent.action_type == "wait":
        summary = "You hold position and let the situation breathe."
        consequences.append("Time passes with minimal direct action.")
    elif intent.action_type == "talk" and intent.target_id:
        operations.append(
            PatchOperation(
                op="set",
                path=f"/player/relationships/{intent.target_id}",
                value={
                    "target_id": intent.target_id,
                    "stance": "contacted",
                    "trust": 52,
                    "tension": 8,
                    "known_facts": [],
                    "notes": [f"Contacted during day {context.current_day}."],
                },
                note="Local parser resolved a social contact.",
            )
        )
        summary = f"You make contact with {intent.target_name}."
        consequences.append("A basic relationship record is created or refreshed.")
    elif intent.action_type == "investigate":
        operations.extend(
            [
                PatchOperation(
                    op="increase",
                    path="/player/condition/fatigue",
                    value=8,
                    note="Investigation costs attention and stamina.",
                ),
                PatchOperation(
                    op="append",
                    path="/facts/player_known",
                    value={
                        "id": _fact_id(world_id, action_text),
                        "text": f"The player investigated: {action_text}",
                        "visibility": "player_known",
                        "known_by": ["player"],
                        "confidence": 0.7,
                        "tags": ["investigation", "local_stub"],
                        "metadata": {"source": "action_resolver"},
                    },
                    note="Investigation creates a player-known lead.",
                ),
            ]
        )
        summary = "You push into the available clues and produce a tentative lead."
        consequences.append("You gain a player-known lead, but fatigue rises.")
    else:
        operations.append(
            PatchOperation(
                op="increase",
                path="/player/condition/fatigue",
                value=3,
                note="Unclear action still consumes attention.",
            )
        )
        summary = "You act, but the current local parser cannot resolve the intent cleanly."
        consequences.append("The action is recorded as uncertain.")

    return ActionOutcome(
        level=_outcome_level(intent.action_type),
        summary=summary,
        consequences=consequences,
        operations=operations,
    )


def _outcome_level(action_type: str) -> str:
    if action_type == "rest":
        return "rested"
    if action_type == "wait":
        return "quiet"
    if action_type == "unknown":
        return "uncertain"
    if action_type == "investigate":
        return "partial"
    return "success"


def _fact_id(world_id: str, action_text: str) -> str:
    digest = hashlib.sha256(f"{world_id}:{action_text}".encode("utf-8")).hexdigest()
    return f"fact_action_{digest[:12]}"

