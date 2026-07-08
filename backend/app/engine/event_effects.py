from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.schemas.patch import PatchOperation


class EventEffectError(ValueError):
    pass


ALLOWED_EFFECT_OPS = {
    "set",
    "increase",
    "decrease",
    "append",
    "add_status",
    "remove_status",
}


def build_event_effect_operations(queued_event: dict[str, Any]) -> list[PatchOperation]:
    operations = []
    for raw_effect in queued_event.get("effects") or []:
        try:
            operation = PatchOperation.model_validate(raw_effect)
        except ValidationError as exc:
            raise EventEffectError(
                f"Queued event has an invalid effect: {queued_event.get('id')}"
            ) from exc

        _validate_effect_operation(operation, queued_event_id=queued_event.get("id", "unknown"))
        operations.append(operation)

    return operations


def _validate_effect_operation(operation: PatchOperation, *, queued_event_id: str) -> None:
    if operation.op not in ALLOWED_EFFECT_OPS:
        raise EventEffectError(
            f"Queued event {queued_event_id} uses unsupported effect op: {operation.op}"
        )

    if operation.op == "remove":
        raise EventEffectError(f"Queued event {queued_event_id} cannot remove world objects.")

    tokens = _path_tokens(operation.path)
    if not tokens:
        raise EventEffectError(f"Queued event {queued_event_id} cannot patch the root state.")

    if _is_allowed_clock_effect(tokens, operation):
        return
    if _is_allowed_location_effect(tokens, operation):
        return
    if _is_allowed_faction_effect(tokens, operation):
        return
    if _is_allowed_entity_effect(tokens, operation):
        return
    if _is_allowed_fact_effect(tokens, operation):
        return
    if _is_allowed_event_queue_effect(tokens, operation):
        return

    raise EventEffectError(
        f"Queued event {queued_event_id} has an effect outside allowed paths: {operation.path}"
    )


def _is_allowed_clock_effect(tokens: list[str], operation: PatchOperation) -> bool:
    if len(tokens) != 3 or tokens[0] != "clocks":
        return False
    return tokens[2] == "progress" and operation.op in {"set", "increase", "decrease"}


def _is_allowed_location_effect(tokens: list[str], operation: PatchOperation) -> bool:
    if len(tokens) < 3 or tokens[0] != "locations":
        return False

    field = tokens[2]
    if len(tokens) == 3 and field == "danger_level":
        return operation.op in {"set", "increase", "decrease"}
    if len(tokens) == 3 and field == "active_events":
        return operation.op == "append" and isinstance(operation.value, str)
    if len(tokens) == 3 and field == "controlling_faction_id":
        return operation.op == "set" and (
            isinstance(operation.value, str) or operation.value is None
        )
    if len(tokens) >= 4 and field in {"traits", "metadata"}:
        return operation.op in {"set", "increase", "decrease", "append"}

    return False


def _is_allowed_faction_effect(tokens: list[str], operation: PatchOperation) -> bool:
    if len(tokens) < 3 or tokens[0] != "factions":
        return False

    field = tokens[2]
    if len(tokens) == 4 and field == "resources":
        return operation.op in {"set", "increase", "decrease"}
    if len(tokens) == 3 and field in {"goals", "known_facts", "controlled_location_ids"}:
        return operation.op == "append" and isinstance(operation.value, str)
    if len(tokens) == 5 and field == "plans" and tokens[4] == "status":
        return operation.op == "set" and isinstance(operation.value, str)
    if len(tokens) == 5 and field == "plans" and tokens[4] == "progress":
        return operation.op in {"set", "increase", "decrease"}
    if len(tokens) >= 4 and field in {"traits", "metadata"}:
        return operation.op in {"set", "increase", "decrease", "append"}

    return False


def _is_allowed_entity_effect(tokens: list[str], operation: PatchOperation) -> bool:
    if len(tokens) < 3 or tokens[0] != "entities":
        return False

    field = tokens[2]
    if len(tokens) == 3 and field == "statuses":
        return operation.op in {"add_status", "remove_status"}
    if len(tokens) == 4 and field in {"condition", "resources"}:
        return operation.op in {"set", "increase", "decrease"}
    if len(tokens) == 3 and field == "current_location_id":
        return operation.op == "set" and (
            isinstance(operation.value, str) or operation.value is None
        )
    if len(tokens) >= 4 and field in {"traits", "properties", "metadata"}:
        return operation.op in {"set", "increase", "decrease", "append"}

    return False


def _is_allowed_fact_effect(tokens: list[str], operation: PatchOperation) -> bool:
    if tokens[0] != "facts" or operation.op != "append":
        return False
    if len(tokens) == 2 and tokens[1] in {"public", "player_known", "hidden"}:
        return _is_fact_value(operation.value, visibility=tokens[1])
    if len(tokens) == 3 and tokens[1] == "faction_known":
        return _is_fact_value(operation.value, visibility="faction_known")
    return False


def _is_allowed_event_queue_effect(tokens: list[str], operation: PatchOperation) -> bool:
    if tokens != ["event_queue"] or operation.op != "append":
        return False
    return _is_queued_event_value(operation.value)


def _is_fact_value(value: Any, *, visibility: str) -> bool:
    if not isinstance(value, dict):
        return False
    if not isinstance(value.get("id"), str) or not value["id"]:
        return False
    if not isinstance(value.get("text"), str) or not value["text"]:
        return False
    return value.get("visibility") == visibility


def _is_queued_event_value(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required_string_fields = ("id", "type", "summary")
    if any(not isinstance(value.get(field), str) or not value[field] for field in required_string_fields):
        return False
    if not isinstance(value.get("trigger"), dict):
        return False
    return True


def _path_tokens(path: str) -> list[str]:
    return [token.replace("~1", "/").replace("~0", "~") for token in path[1:].split("/")]
