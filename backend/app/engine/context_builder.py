from __future__ import annotations

from typing import Any

from app.schemas.action import ActionIntent, ContextPack


def build_context_pack(
    *,
    world_state: dict[str, Any],
    intent: ActionIntent,
) -> ContextPack:
    player = world_state.get("player", {})
    time = world_state.get("time", {})
    locations = world_state.get("locations", {})
    entities = world_state.get("entities", {})
    clocks = world_state.get("clocks", {})
    facts = world_state.get("facts", {})

    player_location_id = player.get("current_location_id")
    relevant_location_ids = set(intent.matched_location_ids)
    if player_location_id:
        relevant_location_ids.add(player_location_id)
    if intent.target_id and intent.action_type == "move":
        relevant_location_ids.add(intent.target_id)

    relevant_entity_ids = set(intent.matched_entity_ids)
    if intent.target_id and intent.action_type in {"talk", "investigate"}:
        relevant_entity_ids.add(intent.target_id)

    visible_facts = []
    visible_facts.extend(facts.get("public", []))
    visible_facts.extend(facts.get("player_known", []))

    return ContextPack(
        current_day=time.get("day", 1),
        current_slot=time.get("slot", "morning"),
        player_location_id=player_location_id,
        player_location_name=locations.get(player_location_id, {}).get("name")
        if player_location_id
        else None,
        relevant_locations={
            location_id: locations[location_id]
            for location_id in relevant_location_ids
            if location_id in locations
        },
        relevant_entities={
            entity_id: entities[entity_id]
            for entity_id in relevant_entity_ids
            if entity_id in entities
        },
        relevant_clocks={clock_id: clock for clock_id, clock in list(clocks.items())[:3]},
        visible_facts=visible_facts[:8],
    )

