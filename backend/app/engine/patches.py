from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.schemas.patch import PatchOperation


class PatchApplyError(ValueError):
    pass


def apply_patch_operations(
    state: dict[str, Any],
    operations: list[PatchOperation],
) -> dict[str, Any]:
    next_state = deepcopy(state)
    for operation in operations:
        _apply_operation(next_state, operation)
    return next_state


def _apply_operation(state: dict[str, Any], operation: PatchOperation) -> None:
    if operation.op == "set":
        parent, key = _resolve_parent(state, operation.path, create_missing=True)
        _set_child(parent, key, operation.value)
        return

    if operation.op in {"increase", "decrease"}:
        parent, key = _resolve_parent(state, operation.path, create_missing=True)
        current = _get_child(parent, key, default=0)
        if not _is_number(current):
            raise PatchApplyError(f"Cannot {operation.op} non-numeric value at {operation.path}.")
        delta = operation.value if operation.op == "increase" else -operation.value
        _set_child(parent, key, current + delta)
        return

    if operation.op == "append":
        parent, key = _resolve_parent(state, operation.path, create_missing=True)
        current = _get_child(parent, key, default=[])
        if not isinstance(current, list):
            raise PatchApplyError(f"Cannot append to non-list value at {operation.path}.")
        current.append(operation.value)
        _set_child(parent, key, current)
        return

    if operation.op == "remove":
        parent, key = _resolve_parent(state, operation.path, create_missing=False)
        _remove_child(parent, key)
        return

    if operation.op == "add_status":
        parent, key = _resolve_parent(state, operation.path, create_missing=True)
        statuses = _get_child(parent, key, default={})
        if not isinstance(statuses, dict):
            raise PatchApplyError(f"Status container must be an object at {operation.path}.")
        status_id = operation.value["id"]
        statuses[status_id] = operation.value
        _set_child(parent, key, statuses)
        return

    if operation.op == "remove_status":
        parent, key = _resolve_parent(state, operation.path, create_missing=False)
        statuses = _get_child(parent, key)
        if not isinstance(statuses, dict):
            raise PatchApplyError(f"Status container must be an object at {operation.path}.")
        statuses.pop(operation.value, None)
        _set_child(parent, key, statuses)
        return

    raise PatchApplyError(f"Unsupported patch operation: {operation.op}")


def _resolve_parent(
    document: dict[str, Any],
    pointer: str,
    *,
    create_missing: bool,
) -> tuple[Any, str | int]:
    tokens = _parse_pointer(pointer)
    if not tokens:
        raise PatchApplyError("Root path cannot be patched.")

    current: Any = document
    for token in tokens[:-1]:
        if isinstance(current, dict):
            if token not in current:
                if not create_missing:
                    raise PatchApplyError(f"Missing object path: {pointer}")
                current[token] = {}
            current = current[token]
            continue

        if isinstance(current, list):
            index = _parse_index(token)
            try:
                current = current[index]
            except IndexError:
                raise PatchApplyError(f"List index is out of range: {pointer}") from None
            continue

        raise PatchApplyError(f"Cannot traverse non-container value at {pointer}.")

    final_token = tokens[-1]
    if isinstance(current, list):
        return current, _parse_index(final_token)
    return current, final_token


def _parse_pointer(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise PatchApplyError(f"Invalid JSON Pointer: {pointer}")
    return [token.replace("~1", "/").replace("~0", "~") for token in pointer[1:].split("/")]


def _parse_index(token: str) -> int:
    try:
        index = int(token)
    except ValueError:
        raise PatchApplyError(f"Expected list index, got: {token}") from None
    if index < 0:
        raise PatchApplyError(f"List index cannot be negative: {token}")
    return index


def _get_child(parent: Any, key: str | int, *, default: Any = None) -> Any:
    if isinstance(parent, dict):
        return parent.get(key, default)
    if isinstance(parent, list):
        try:
            return parent[key]
        except IndexError:
            return default
    raise PatchApplyError("Parent is not a container.")


def _set_child(parent: Any, key: str | int, value: Any) -> None:
    if isinstance(parent, dict):
        parent[key] = value
        return

    if isinstance(parent, list):
        if key == len(parent):
            parent.append(value)
            return
        try:
            parent[key] = value
        except IndexError:
            raise PatchApplyError(f"List index is out of range: {key}") from None
        return

    raise PatchApplyError("Parent is not a container.")


def _remove_child(parent: Any, key: str | int) -> None:
    if isinstance(parent, dict):
        if key not in parent:
            raise PatchApplyError(f"Cannot remove missing key: {key}")
        del parent[key]
        return

    if isinstance(parent, list):
        try:
            del parent[key]
        except IndexError:
            raise PatchApplyError(f"List index is out of range: {key}") from None
        return

    raise PatchApplyError("Parent is not a container.")


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)
