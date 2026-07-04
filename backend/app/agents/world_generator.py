from __future__ import annotations

import hashlib
import random
import re

from app.schemas.generation import (
    SeedClock,
    SeedEntity,
    SeedFaction,
    SeedFact,
    SeedLocation,
    SeedQueuedEvent,
    WorldGenerationRequest,
    WorldSeed,
)


class LocalWorldSeedGenerator:
    """Deterministic structural generator used before LLM providers are wired."""

    def generate(self, request: WorldGenerationRequest) -> WorldSeed:
        rng = random.Random(_effective_seed(request.premise, request.seed))
        theme = _theme_label(request.premise)

        factions = _generate_factions(theme, request.faction_count, rng)
        locations = _generate_locations(theme, request.location_count, factions, rng)
        entities = _generate_entities(theme, request.entity_count, factions, locations, rng)
        clocks = _generate_clocks(theme, request.clock_count, factions, rng)
        public_facts, player_known_facts, hidden_facts = _generate_facts(
            theme,
            factions,
            locations,
            clocks,
        )
        queued_events = _generate_queued_events(theme, clocks)

        return WorldSeed(
            premise=request.premise,
            core_conflict=(
                f"{theme} is being pulled between public order, hidden power, "
                "and groups willing to reshape the world for advantage."
            ),
            player_identity=f"Newly entangled outsider in {theme}",
            factions=factions,
            locations=locations,
            entities=entities,
            clocks=clocks,
            public_facts=public_facts,
            player_known_facts=player_known_facts,
            hidden_facts=hidden_facts,
            queued_events=queued_events,
        )


def _effective_seed(premise: str, seed: int | None) -> int:
    if seed is not None:
        return seed
    digest = hashlib.sha256(premise.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _theme_label(premise: str) -> str:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]+", premise)
    if words:
        return " ".join(words[:4]).title()
    compact = premise.strip().replace("\n", " ")
    return compact[:24] or "The City"


def _generate_factions(
    theme: str,
    count: int,
    rng: random.Random,
) -> list[SeedFaction]:
    templates = [
        ("civic_directorate", "Civic Directorate", "preserve order through surveillance"),
        ("veil_syndicate", "Veil Syndicate", "profit from hidden routes and secrets"),
        ("aurelian_institute", "Aurelian Institute", "control dangerous knowledge"),
        ("ashen_chorus", "Ashen Chorus", "force a revelation that cannot be contained"),
        ("iron_compact", "Iron Compact", "turn crisis into hard political power"),
    ]
    rng.shuffle(templates)

    factions = []
    for index, (suffix, name, ideology) in enumerate(templates[:count], start=1):
        faction_id = f"faction_{suffix}"
        factions.append(
            SeedFaction(
                id=faction_id,
                name=name,
                summary=f"A major power in {theme} that tries to {ideology}.",
                ideology=ideology,
                goals=[
                    f"Secure leverage over {theme}",
                    "Identify useful assets before rivals do",
                ],
                resources={
                    "influence": rng.randint(35, 80),
                    "money": rng.randint(25, 75),
                    "intelligence": rng.randint(25, 85),
                    "force": rng.randint(15, 70),
                },
                secrets=[f"{name} is hiding the true cost of its current plan."],
            )
        )
    return factions


def _generate_locations(
    theme: str,
    count: int,
    factions: list[SeedFaction],
    rng: random.Random,
) -> list[SeedLocation]:
    templates = [
        ("old_station", "Old Station", "transit_hub"),
        ("south_market", "South Market", "market"),
        ("sealed_archive", "Sealed Archive", "archive"),
        ("river_gate", "River Gate", "checkpoint"),
        ("glass_tower", "Glass Tower", "corporate_site"),
        ("lowtown_clinic", "Lowtown Clinic", "clinic"),
        ("underpass_shrine", "Underpass Shrine", "shrine"),
        ("north_powerworks", "North Powerworks", "infrastructure"),
        ("rain_square", "Rain Square", "public_square"),
        ("red_line_tunnel", "Red Line Tunnel", "restricted_zone"),
        ("harbor_stack", "Harbor Stack", "industrial_zone"),
        ("observatory_ward", "Observatory Ward", "research_site"),
    ]
    locations = []
    selected = templates[:count]
    for index, (suffix, name, kind) in enumerate(selected):
        faction = factions[index % len(factions)] if factions and index % 2 == 0 else None
        connected_to = []
        if index > 0:
            connected_to.append(f"loc_{selected[index - 1][0]}")
        if index + 1 < len(selected):
            connected_to.append(f"loc_{selected[index + 1][0]}")
        locations.append(
            SeedLocation(
                id=f"loc_{suffix}",
                name=name,
                kind=kind,
                summary=f"A {kind.replace('_', ' ')} in {theme} where pressure gathers.",
                danger_level=rng.randint(5, 75),
                controlling_faction_id=faction.id if faction else None,
                connected_to=connected_to,
                hidden_features=[
                    f"A hidden route links {name} to a larger conflict."
                ],
            )
        )
    return locations


def _generate_entities(
    theme: str,
    count: int,
    factions: list[SeedFaction],
    locations: list[SeedLocation],
    rng: random.Random,
) -> list[SeedEntity]:
    templates = [
        ("mira_vale", "Mira Vale", "npc", "A courier with more contacts than loyalty."),
        ("doctor_sen", "Doctor Sen", "npc", "A backstreet doctor who treats impossible wounds."),
        ("arden_kai", "Arden Kai", "npc", "A calm negotiator with a dangerous patron."),
        ("lena_cross", "Lena Cross", "npc", "A watcher who records patterns others miss."),
        ("black_key", "Black Key", "artifact", "An object that opens routes that should not exist."),
        ("ledger_chip", "Ledger Chip", "item", "A damaged record of hidden transactions."),
        ("hollow_courier", "Hollow Courier", "creature", "A messenger altered by the world's secret rules."),
        ("broken_relay", "Broken Relay", "object", "A machine that still receives forbidden signals."),
        ("glass_token", "Glass Token", "artifact", "A proof of access to a faction vault."),
        ("nameless_broker", "Nameless Broker", "npc", "An information seller who never repeats a price."),
        ("red_masque", "Red Masque", "npc", "A performer tied to several impossible disappearances."),
        ("weathered_case", "Weathered Case", "item", "A locked case that many people recognize but deny."),
        ("echo_child", "Echo Child", "creature", "A quiet presence that repeats tomorrow's words."),
        ("silver_map", "Silver Map", "artifact", "A map that marks danger before it arrives."),
        ("station_keeper", "Station Keeper", "npc", "A tired caretaker who knows where bodies vanish."),
    ]
    entities = []
    for index, (suffix, name, kind, summary) in enumerate(templates[:count]):
        faction = factions[index % len(factions)] if factions and kind == "npc" else None
        location = locations[index % len(locations)] if locations else None
        entities.append(
            SeedEntity(
                id=f"entity_{suffix}",
                kind=kind,
                name=name,
                summary=f"{summary} Connected to {theme}.",
                current_location_id=location.id if location else None,
                owner_id=faction.id if faction else None,
                goals=["Survive the next shift of power"] if kind == "npc" else [],
                secrets=[f"{name} knows one fact that could redirect a faction plan."],
            )
        )
    rng.shuffle(entities)
    return entities


def _generate_clocks(
    theme: str,
    count: int,
    factions: list[SeedFaction],
    rng: random.Random,
) -> list[SeedClock]:
    templates = [
        ("public_panic", "Public Panic", "A public incident forces authorities to act."),
        ("faction_crackdown", "Faction Crackdown", "A faction launches a visible operation."),
        ("hidden_experiment", "Hidden Experiment", "A contained experiment breaks containment."),
        ("rival_investigation", "Rival Investigation", "A rival identifies a key hidden actor."),
        ("market_collapse", "Market Collapse", "A vital black-market channel shuts down."),
        ("forbidden_signal", "Forbidden Signal", "A signal reaches everyone carrying a secret mark."),
    ]
    clocks = []
    for index, (suffix, name, trigger) in enumerate(templates[:count]):
        owner = factions[index % len(factions)] if factions and index != 0 else None
        clocks.append(
            SeedClock(
                id=f"clock_{suffix}",
                name=name,
                progress=rng.randint(5, 45),
                max=100,
                owner_id=owner.id if owner else None,
                visibility="hidden" if index else "player_known",
                trigger_event=trigger,
                causes=[f"Pressure in {theme} is accumulating."],
                consequences=[trigger],
            )
        )
    return clocks


def _generate_facts(
    theme: str,
    factions: list[SeedFaction],
    locations: list[SeedLocation],
    clocks: list[SeedClock],
) -> tuple[list[SeedFact], list[SeedFact], list[SeedFact]]:
    public_facts = [
        SeedFact(
            id="fact_public_tension",
            text=f"People in {theme} know that several powers are moving more aggressively than usual.",
            visibility="public",
            tags=["tension"],
        ),
    ]

    player_known_facts = [
        SeedFact(
            id="fact_player_arrival",
            text="The player has recently become entangled in the city's hidden conflict.",
            visibility="player_known",
            known_by=["player"],
            tags=["player"],
        ),
    ]

    hidden_facts = []
    if factions:
        hidden_facts.append(
            SeedFact(
                id="fact_hidden_faction_cost",
                text=f"{factions[0].name} will sacrifice a public asset if its plan stalls.",
                visibility="hidden",
                known_by=[factions[0].id],
                tags=["faction_secret"],
            )
        )
    if locations and clocks:
        hidden_facts.append(
            SeedFact(
                id="fact_hidden_trigger_site",
                text=f"{locations[0].name} is tied to the trigger behind {clocks[0].name}.",
                visibility="hidden",
                tags=["location_secret", "clock"],
            )
        )
    return public_facts, player_known_facts, hidden_facts


def _generate_queued_events(
    theme: str,
    clocks: list[SeedClock],
) -> list[SeedQueuedEvent]:
    events = []
    for index, clock in enumerate(clocks[:2], start=1):
        events.append(
            SeedQueuedEvent(
                id=f"queued_{clock.id}",
                type="clock_threshold",
                summary=f"{clock.name} may change the situation in {theme}.",
                trigger={"clock_id": clock.id, "progress_at_least": 75},
                earliest_day=index,
                latest_day=index + 3,
                priority=60 + index * 5,
                visibility=clock.visibility,
                payload={"trigger_event": clock.trigger_event},
            )
        )
    return events
