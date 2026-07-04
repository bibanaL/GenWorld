# World Generation MVP

World generation currently means:

```text
natural-language premise
-> WorldSeed
-> WorldState
-> SQLite ledger
```

The generator does not write arbitrary world state directly.

## Current Generator

Phase 2 starts with a deterministic local generator.

This is intentional. The local generator verifies the complete data path before an LLM provider is connected:

- Request validation.
- Structured seed creation.
- WorldState construction.
- SQLite persistence.
- Event-log recording.
- API response shape.

The local generator is not the final creative layer.

## API

```http
POST /worlds/generate
```

Example request:

```json
{
  "name": "Spirit City",
  "premise": "A modern city where spiritual energy has returned and corporations, sects, and public institutions compete over supernatural resources.",
  "seed": 42,
  "faction_count": 3,
  "location_count": 7,
  "entity_count": 8,
  "clock_count": 4,
  "generator": "local"
}
```

Example response shape:

```json
{
  "world": {
    "id": "...",
    "name": "Spirit City",
    "premise": "...",
    "state": {}
  },
  "seed": {
    "premise": "...",
    "core_conflict": "...",
    "player_identity": "...",
    "factions": [],
    "locations": [],
    "entities": [],
    "clocks": [],
    "public_facts": [],
    "player_known_facts": [],
    "hidden_facts": [],
    "queued_events": []
  }
}
```

## WorldSeed Contents

The generated seed includes:

- `core_conflict`
- `player_identity`
- 2 to 5 factions
- 3 to 12 locations
- 3 to 15 entities
- 2 to 6 world clocks
- public facts
- player-known facts
- hidden facts
- queued events

## Builder Boundary

`WorldSeed` is converted into `WorldState` by backend code.

This is the key safety boundary:

- AI may generate seed data.
- Backend code constructs canonical world state.
- The ledger records the result.
- Future simulation must use patches, not raw state mutation.

## Future LLM Integration

When an LLM provider is connected, it should produce only `WorldSeed` using structured output.

It should not directly produce:

- Raw `WorldState`
- SQL statements
- State patches
- Executable mechanics
- Narrative prose as canonical facts

The intended future flow is:

```text
prompt
-> LLM structured output: WorldSeed
-> validation and repair
-> backend builder
-> ledger commit
```

## Current Limits

- No external model call yet.
- No style control.
- No complex genre-specific mechanics.
- No semantic memory.
- No map generation.
- No player-facing prose beyond structural summaries.
