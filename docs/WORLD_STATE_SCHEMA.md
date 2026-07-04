# WorldState v1

WorldState v1 keeps the top-level structure small and stable while allowing each domain to grow internally.

The player should never interact with this structure directly. It is the backend ledger format used by the simulator, agents, auditor, and future world generator.

## Top-Level Shape

```json
{
  "schema_version": 1,
  "premise": "",
  "seed": null,
  "time": {},
  "player": {},
  "entities": {},
  "locations": {},
  "factions": {},
  "clocks": {},
  "facts": {},
  "event_queue": []
}
```

## Design Rule

Top-level domains should be rare and stable.

Do not add a new top-level field just because a new concept appears. Most new world objects should start inside `entities`, `locations`, `factions`, `clocks`, `facts`, or `event_queue`.

Good candidates for a future top-level field must be:

- Read frequently by the simulation loop.
- Broadly shared across many systems.
- Hard to model cleanly as a subdomain.
- Stable across multiple genres.

## `time`

Tracks in-world time.

Current defaults:

```json
{
  "day": 1,
  "slot": "morning",
  "slot_index": 0,
  "slots_per_day": ["morning", "afternoon", "evening", "night"]
}
```

The slot names are configurable because different worlds may later use different calendars.

## `player`

The player's avatar is separate from normal entities because it is accessed on almost every action.

Core fields:

- `id`
- `name`
- `identity`
- `current_location_id`
- `condition`
- `resources`
- `statuses`
- `relationships`
- `knowledge`
- `secrets`
- `goals`
- `traits`
- `metadata`

## `entities`

Generic world objects keyed by id.

Use this for:

- NPCs
- Items
- Artifacts
- Creatures
- Machines
- Spirits
- Contracts
- Other unusual world objects

Core fields:

- `id`
- `kind`
- `name`
- `summary`
- `current_location_id`
- `owner_id`
- `condition`
- `resources`
- `statuses`
- `relationships`
- `knowledge`
- `secrets`
- `goals`
- `traits`
- `properties`
- `metadata`

Supported `kind` values in v1:

- `npc`
- `item`
- `artifact`
- `creature`
- `object`
- `other`

## `locations`

Locations are top-level because movement, danger, faction control, and event triggers depend on them.

Core fields:

- `id`
- `name`
- `kind`
- `summary`
- `parent_id`
- `connected_to`
- `controlling_faction_id`
- `danger_level`
- `resources`
- `active_events`
- `hidden_features`
- `traits`
- `metadata`

## `factions`

Factions are top-level because they drive background simulation.

Core fields:

- `id`
- `name`
- `summary`
- `ideology`
- `resources`
- `goals`
- `plans`
- `relationships`
- `known_facts`
- `secrets`
- `controlled_location_ids`
- `traits`
- `metadata`

Faction plans are keyed by id and include:

- `id`
- `summary`
- `priority`
- `progress`
- `target_clock_id`
- `target_entity_ids`
- `target_location_ids`
- `status`

## `clocks`

Clocks represent world pressure and delayed consequences.

Examples:

- A sect investigation reaches 100/100.
- A corporate experiment becomes unstable.
- Public panic crosses a threshold.

Core fields:

- `id`
- `name`
- `progress`
- `max`
- `owner_id`
- `visibility`
- `trigger_event`
- `causes`
- `consequences`
- `metadata`

## `facts`

Facts protect continuity and visibility boundaries.

Fact groups:

- `public`
- `player_known`
- `hidden`
- `faction_known`

Each fact record includes:

- `id`
- `text`
- `visibility`
- `known_by`
- `source_event_id`
- `confidence`
- `tags`
- `metadata`

## `event_queue`

`event_queue` is for future or pending events.

It is different from the `events` database table:

- `events` table: happened already.
- `event_queue`: may happen later.

Queued event fields:

- `id`
- `type`
- `summary`
- `trigger`
- `earliest_day`
- `latest_day`
- `priority`
- `visibility`
- `payload`

## Extensibility

Most schema models allow additional fields.

Use `traits`, `properties`, or `metadata` for genre-specific details before introducing new top-level structure.

Examples:

- A cultivation world can store realm data under `traits`.
- A cyberpunk world can store implant data under `properties`.
- A supernatural world can store curse mechanics under `metadata` until they become formal mechanics.

## Current Boundary

WorldState v1 defines structure, not behavior.

The following are still separate systems:

- Patch validation and execution.
- World generation.
- World clocks and simulation.
- Mechanic DSL.
- Agent context-pack construction.
- Long-term memory and retrieval.

