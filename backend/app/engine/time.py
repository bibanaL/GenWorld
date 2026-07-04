from typing import Any


def next_time_slot(time_state: dict[str, Any]) -> dict[str, Any]:
    slots = time_state.get("slots_per_day") or ["morning", "afternoon", "evening", "night"]
    current_index = int(time_state.get("slot_index", 0))
    next_index = current_index + 1
    day = int(time_state.get("day", 1))

    if next_index >= len(slots):
        next_index = 0
        day += 1

    return {
        "day": day,
        "slot_index": next_index,
        "slot": slots[next_index],
    }


def time_advance_operations(time_state: dict[str, Any]) -> list[dict[str, Any]]:
    next_time = next_time_slot(time_state)
    return [
        {
            "op": "set",
            "path": "/time/day",
            "value": next_time["day"],
            "note": "Advance world time.",
        },
        {
            "op": "set",
            "path": "/time/slot",
            "value": next_time["slot"],
            "note": "Advance world time.",
        },
        {
            "op": "set",
            "path": "/time/slot_index",
            "value": next_time["slot_index"],
            "note": "Advance world time.",
        },
    ]

