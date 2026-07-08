from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.intent_parser import parse_player_intent
from app.agents.narrator import narrate_action_result
from app.engine.action_resolver import resolve_player_action
from app.engine.context_builder import build_context_pack
from app.engine.simulator import build_world_advance_operations
from app.schemas.action import (
    ActionIntent,
    ActionOutcome,
    ContextPack,
    PlayerActionRequest,
)
from app.services.event_queue_service import (
    preflight_event_queue_after_operations,
    process_event_queue,
)
from app.storage.sqlite_store import SQLiteLedger


class PlayerActionGraphState(TypedDict, total=False):
    world_id: str
    actor_id: str
    action_text: str
    advance_time: bool
    world: dict[str, Any]
    intent: ActionIntent
    context_pack: ContextPack
    outcome: ActionOutcome
    patch: dict[str, Any] | None
    event_queue_patch: dict[str, Any] | None
    triggered_events: list[dict[str, Any]]
    narrative: str
    resolved_at: str


class PlayerActionGraphRunner:
    def __init__(self, ledger: SQLiteLedger) -> None:
        self.ledger = ledger
        self.graph = self._build_graph()

    def run(self, world_id: str, request: PlayerActionRequest) -> PlayerActionGraphState:
        initial_state: PlayerActionGraphState = {
            "world_id": world_id,
            "actor_id": request.actor_id,
            "action_text": request.text,
            "advance_time": request.advance_time,
        }
        return self.graph.invoke(initial_state)

    def _build_graph(self):
        graph = StateGraph(PlayerActionGraphState)
        graph.add_node("load_world_state", self._load_world_state)
        graph.add_node("parse_player_intent", self._parse_player_intent)
        graph.add_node("build_context_pack", self._build_context_pack)
        graph.add_node("resolve_action", self._resolve_action)
        graph.add_node("advance_world", self._advance_world)
        graph.add_node("commit_state", self._commit_state)
        graph.add_node("narrate_result", self._narrate_result)

        graph.add_edge(START, "load_world_state")
        graph.add_edge("load_world_state", "parse_player_intent")
        graph.add_edge("parse_player_intent", "build_context_pack")
        graph.add_edge("build_context_pack", "resolve_action")
        graph.add_edge("resolve_action", "advance_world")
        graph.add_edge("advance_world", "commit_state")
        graph.add_edge("commit_state", "narrate_result")
        graph.add_edge("narrate_result", END)
        return graph.compile()

    def _load_world_state(self, state: PlayerActionGraphState) -> dict[str, Any]:
        world = self.ledger.get_world(state["world_id"])
        if world is None:
            raise KeyError(state["world_id"])
        return {"world": world}

    def _parse_player_intent(self, state: PlayerActionGraphState) -> dict[str, Any]:
        intent = parse_player_intent(
            action_text=state["action_text"],
            world_state=state["world"]["state"],
        )
        return {"intent": intent}

    def _build_context_pack(self, state: PlayerActionGraphState) -> dict[str, Any]:
        context_pack = build_context_pack(
            world_state=state["world"]["state"],
            intent=state["intent"],
        )
        return {"context_pack": context_pack}

    def _resolve_action(self, state: PlayerActionGraphState) -> dict[str, Any]:
        outcome = resolve_player_action(
            world_id=state["world_id"],
            action_text=state["action_text"],
            world_state=state["world"]["state"],
            intent=state["intent"],
            context=state["context_pack"],
        )
        return {"outcome": outcome}

    def _advance_world(self, state: PlayerActionGraphState) -> dict[str, Any]:
        if not state.get("advance_time", True):
            return {}

        outcome = state["outcome"]
        operations = list(outcome.operations)
        operations.extend(
            build_world_advance_operations(
                state["world"]["state"],
                risk_level=state["intent"].risk_level,
                advance_time=True,
                clock_limit=2,
            )
        )
        return {"outcome": outcome.model_copy(update={"operations": operations})}

    def _commit_state(self, state: PlayerActionGraphState) -> dict[str, Any]:
        outcome = state["outcome"]
        preflight_event_queue_after_operations(
            world_state=state["world"]["state"],
            operations=outcome.operations,
        )
        patch = self.ledger.apply_state_patch(
            world_id=state["world_id"],
            reason=f"Player action: {state['action_text']}",
            source_agent="player_action_graph.local",
            permission_level="system",
            operations=outcome.operations,
        )
        self.ledger.append_event(
            world_id=state["world_id"],
            type_="player_action_resolved",
            summary=outcome.summary,
            payload={
                "action_text": state["action_text"],
                "intent": state["intent"].model_dump(mode="json"),
                "outcome": outcome.model_dump(mode="json"),
                "patch_id": patch["id"],
            },
        )
        event_queue_result = process_event_queue(
            ledger=self.ledger,
            world_id=state["world_id"],
        )
        return {
            "patch": patch,
            "event_queue_patch": event_queue_result.patch,
            "triggered_events": event_queue_result.triggered_events,
            "resolved_at": datetime.now(UTC).isoformat(),
        }

    def _narrate_result(self, state: PlayerActionGraphState) -> dict[str, Any]:
        narrative = narrate_action_result(
            intent=state["intent"],
            context=state["context_pack"],
            outcome=state["outcome"],
        )
        return {"narrative": narrative}
