from __future__ import annotations

from typing import Any

from app.schemas.action import ActionIntent


def parse_player_intent(action_text: str, world_state: dict[str, Any]) -> ActionIntent:
    normalized = action_text.lower()
    matched_locations = match_named_records(normalized, world_state.get("locations", {}))
    matched_entities = match_named_records(normalized, world_state.get("entities", {}))

    action_type = "unknown"
    keywords: list[str] = []
    risk_level = "medium"

    if _contains_any(normalized, ["rest", "sleep", "recover", "休息", "睡", "恢复"]):
        action_type = "rest"
        keywords.append("rest")
        risk_level = "low"
    elif _contains_any(normalized, ["wait", "observe", "等待", "观察", "守候"]):
        action_type = "wait"
        keywords.append("wait")
        risk_level = "low"
    elif _contains_any(
        normalized,
        ["search", "investigate", "study", "track", "查", "调查", "搜索", "研究", "追踪"],
    ):
        action_type = "investigate"
        keywords.append("investigate")
        risk_level = "high"
    elif _contains_any(normalized, ["talk", "ask", "contact", "meet", "问", "谈", "联系", "拜访"]):
        action_type = "talk"
        keywords.append("talk")
        risk_level = "medium"
    elif _contains_any(normalized, ["go", "move", "travel", "enter", "去", "前往", "移动", "进入"]):
        action_type = "move"
        keywords.append("move")
        risk_level = "low" if matched_locations else "medium"
    elif matched_entities:
        action_type = "talk"
    elif matched_locations:
        action_type = "move"

    target_id = None
    target_name = None
    if action_type == "move" and matched_locations:
        target_id = matched_locations[0]
        target_name = world_state["locations"][target_id].get("name")
    elif action_type in {"talk", "investigate"} and matched_entities:
        target_id = matched_entities[0]
        target_name = world_state["entities"][target_id].get("name")
    elif matched_locations:
        target_id = matched_locations[0]
        target_name = world_state["locations"][target_id].get("name")

    return ActionIntent(
        action_type=action_type,
        target_id=target_id,
        target_name=target_name,
        risk_level=risk_level,
        time_cost_slots=1,
        matched_location_ids=matched_locations,
        matched_entity_ids=matched_entities,
        keywords=keywords,
        confidence=0.8 if target_id or keywords else 0.35,
    )


def match_named_records(text: str, records: dict[str, dict[str, Any]]) -> list[str]:
    matches = []
    for record_id, record in records.items():
        name = str(record.get("name", "")).lower()
        if record_id.lower() in text or (name and name in text):
            matches.append(record_id)
    return matches


def _contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)

