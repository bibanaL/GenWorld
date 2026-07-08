from app.schemas.generation import WorldSeed
from app.schemas.state import (
    ClockState,
    EntityState,
    FactLedger,
    FactRecord,
    FactionState,
    LocationState,
    PlanRecord,
    PlayerState,
    QueuedEvent,
    WorldState,
)


def build_world_state_from_seed(
    *,
    seed: WorldSeed,
    numeric_seed: int | None,
) -> WorldState:
    factions = {
        faction.id: FactionState(
            id=faction.id,
            name=faction.name,
            summary=faction.summary,
            ideology=faction.ideology,
            resources=faction.resources,
            goals=faction.goals,
            secrets=faction.secrets,
        )
        for faction in seed.factions
    }

    locations = {
        location.id: LocationState(
            id=location.id,
            name=location.name,
            kind=location.kind,
            summary=location.summary,
            danger_level=location.danger_level,
            controlling_faction_id=location.controlling_faction_id,
            connected_to=location.connected_to,
            hidden_features=location.hidden_features,
        )
        for location in seed.locations
    }

    entities = {
        entity.id: EntityState(
            id=entity.id,
            kind=entity.kind,
            name=entity.name,
            summary=entity.summary,
            current_location_id=entity.current_location_id,
            owner_id=entity.owner_id,
            goals=entity.goals,
            secrets=entity.secrets,
        )
        for entity in seed.entities
    }

    clocks = {
        clock.id: ClockState(
            id=clock.id,
            name=clock.name,
            progress=clock.progress,
            max=clock.max,
            owner_id=clock.owner_id,
            visibility=clock.visibility,
            trigger_event=clock.trigger_event,
            causes=clock.causes,
            consequences=clock.consequences,
        )
        for clock in seed.clocks
    }

    facts = FactLedger(
        public=[
            FactRecord(
                id=fact.id,
                text=fact.text,
                visibility="public",
                known_by=fact.known_by,
                tags=fact.tags,
            )
            for fact in seed.public_facts
            if fact.visibility == "public"
        ],
        player_known=[
            FactRecord(
                id=fact.id,
                text=fact.text,
                visibility="player_known",
                known_by=fact.known_by or ["player"],
                tags=fact.tags,
            )
            for fact in seed.player_known_facts
        ],
        hidden=[
            FactRecord(
                id=fact.id,
                text=fact.text,
                visibility="hidden",
                known_by=fact.known_by,
                tags=fact.tags,
            )
            for fact in seed.hidden_facts
        ],
    )

    queued_events = [
        QueuedEvent(
            id=event.id,
            type=event.type,
            summary=event.summary,
            trigger=event.trigger,
            earliest_day=event.earliest_day,
            latest_day=event.latest_day,
            priority=event.priority,
            visibility=event.visibility,
            payload=event.payload,
            effects=event.effects,
        )
        for event in seed.queued_events
    ]

    _attach_initial_plans(factions, clocks)
    _attach_controlled_locations(factions, locations)

    starting_location_id = seed.locations[0].id if seed.locations else None

    return WorldState(
        premise=seed.premise,
        seed=numeric_seed,
        player=PlayerState(
            identity=seed.player_identity,
            current_location_id=starting_location_id,
            goals=["Understand the hidden conflict", "Survive the first week"],
            resources={"coin": 2, "leverage": 0},
            condition={"health": 100, "fatigue": 0, "exposure": 0},
        ),
        entities=entities,
        locations=locations,
        factions=factions,
        clocks=clocks,
        facts=facts,
        event_queue=queued_events,
        metadata={"core_conflict": seed.core_conflict},
    )


def _attach_initial_plans(
    factions: dict[str, FactionState],
    clocks: dict[str, ClockState],
) -> None:
    clock_values = list(clocks.values())
    if not clock_values:
        return

    for index, faction in enumerate(factions.values()):
        clock = clock_values[index % len(clock_values)]
        plan_id = f"plan_advance_{clock.id}"
        faction.plans[plan_id] = PlanRecord(
            id=plan_id,
            summary=f"Advance or exploit {clock.name}.",
            priority=60,
            progress=10,
            target_clock_id=clock.id,
            status="active",
        )


def _attach_controlled_locations(
    factions: dict[str, FactionState],
    locations: dict[str, LocationState],
) -> None:
    for location in locations.values():
        if location.controlling_faction_id and location.controlling_faction_id in factions:
            factions[location.controlling_faction_id].controlled_location_ids.append(location.id)
