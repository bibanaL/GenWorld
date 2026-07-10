# Simulation Engine

Status: current prototype implementation.

Four-slot time, faction-wide ticking, and the current event queue prove the
storage and orchestration path. The target product replaces canonical slots
with minute-level time and adds tiered personal NPC simulation while retaining
audited patches and daily settlement. See `PRODUCT_SPEC.md` and `ROADMAP.md`.

The simulation engine owns time and background world pressure.

It is separate from the player action graph so that world movement does not become coupled to player input.

## Current Modules

```text
backend/app/engine/time.py
backend/app/engine/simulator.py
backend/app/engine/event_queue.py
backend/app/engine/event_effects.py
backend/app/engine/faction_plans.py
backend/app/engine/daily_settlement.py
backend/app/services/event_queue_service.py
backend/app/services/daily_settlement_service.py
```

`time.py`

- Computes the next time slot.
- Produces time-advance patch operations.

`simulator.py`

- Produces world-clock patch operations.
- Combines clock advancement and optional time advancement.
- Does not commit state directly.

`event_queue.py`

- Detects queued events whose trigger conditions are satisfied.
- Produces removal patch operations for triggered queue items.
- Adds validated queued-event effect operations to the same patch batch.
- Does not commit state directly.

`event_effects.py`

- Validates the narrower effect surface available to queued events.
- Converts queued event `effects` into Patch DSL operations.
- Rejects effects that try to directly rewrite the player, time, premise, seed, schema version, or arbitrary roots.
- Does not commit state directly.

`faction_plans.py`

- Advances active faction plans.
- Advances a plan's `target_clock_id` by a small capped amount.
- Marks a plan `completed` when progress reaches 100.
- Does not create new plans, relationships, facts, or story events.

`daily_settlement.py`

- Ends the current world day.
- Moves time to the next day morning.
- Optionally ticks faction plans.
- Does not directly apply player damage or relationship changes.

`daily_settlement_service.py`

- Commits daily settlement patches.
- Writes a `daily_settlement` event.
- Processes event queue after the new day begins.

`event_queue_service.py`

- Coordinates event queue processing with the ledger.
- Preflights event queue effects before the parent action or simulation patch commits.
- Applies queue-removal and event-effect patches.
- Appends `queued_event_triggered` records to the event log.

## API

```http
POST /worlds/{world_id}/advance
POST /worlds/{world_id}/settle-day
```

Example request:

```json
{
  "reason": "Advance world by one slot.",
  "risk_level": "low",
  "advance_time": true,
  "clock_limit": 2,
  "tick_faction_plans": true,
  "faction_plan_limit": 20
}
```

Daily settlement request:

```json
{
  "reason": "Settle current world day.",
  "tick_faction_plans": true,
  "faction_plan_limit": 100
}
```

## State Boundary

The simulator does not mutate world state directly.

It returns Patch DSL operations:

```text
simulator
-> PatchOperation list
-> ledger.apply_state_patch
-> auditor
-> patch executor
-> event log
```

This keeps background simulation auditable and consistent with player actions.

## Current Behavior

- Advances the first N clocks by a risk-based delta.
- Caps clock progress at each clock's `max`.
- Optionally advances the world time slot.
- Advances active faction plans by deterministic local rules.
- Records a `world_advanced` event after a successful patch.
- Processes queued clock-triggered events after world advancement.

Daily settlement behavior:

- Treats the current day as finished.
- Moves the world to the next day morning.
- Optionally advances faction plans once.
- Records a `daily_settlement` event.
- Processes queued events after the new day begins.

In gameplay terms:

```text
Day 3 night
-> settle day
-> faction plans advance in the background
-> world moves to Day 4 morning
-> queued events that can happen on Day 4 may trigger
```

Risk deltas:

- `low`: 2
- `medium`: 4
- `high`: 7

Faction plan rules:

- Only plans with `status: "active"` are ticked.
- Plan progress delta is based on priority: `priority // 25`, clamped to `1..5`.
- A plan with `target_clock_id` advances that clock by `1..2`, capped at the clock's `max`.
- When plan progress reaches 100, the plan status becomes `completed`.
- Completed plans create a follow-up queued event.
- Follow-up events are delayed: earliest trigger day is the next world day.
- Follow-up events can apply narrow world consequences through queued event effects.
- Follow-up events do not directly harm the player or rewrite relationships yet.

In gameplay terms:

```text
Faction plan reaches 100
-> plan becomes completed
-> a follow-up event is placed in event_queue
-> the next world day can trigger that event
-> the player gets room to react before consequences escalate
```

## Event Queue Triggering

The first supported trigger type is a clock threshold:

```json
{
  "trigger": {
    "clock_id": "clock_public_panic",
    "progress_at_least": 75
  },
  "earliest_day": 1,
  "latest_day": 3
}
```

The second supported trigger type is a completed faction plan:

```json
{
  "trigger": {
    "type": "plan_completed",
    "faction_id": "faction_veil_syndicate",
    "plan_id": "plan_advance_clock_public_panic"
  },
  "earliest_day": 2,
  "latest_day": 4
}
```

Trigger rules:

- If `current_day < earliest_day`, the event does not trigger yet.
- For clock events, if the referenced clock does not exist, the event does not trigger.
- For clock events, if clock progress is lower than `progress_at_least`, the event does not trigger.
- For clock events, if clock progress reaches the threshold, the event triggers.
- For completed-plan events, if the faction plan is not completed, the event does not trigger.
- If `current_day > latest_day`, the event still triggers and is marked `overdue: true`.

Triggered queued events are removed from `/event_queue` through Patch DSL.

If a queued event has `effects`, those effects are validated and applied in the same patch batch that removes the queue item.

In gameplay terms:

```text
clock or faction trigger becomes true
-> queued event is selected
-> event effects are validated
-> event is removed from event_queue
-> allowed effects change the world
-> queued_event_triggered is written to the event log
```

Allowed first-version effects are deliberately narrow:

- Clock progress changes.
- Location danger, control, active events, traits, and metadata.
- Faction resources, goals, known facts, controlled locations, plan progress/status, traits, and metadata.
- Entity statuses, condition, resources, current location, traits, properties, and metadata.
- Fact appends.
- New delayed event appends.

Not allowed:

- Direct player mutation.
- Direct time mutation.
- Premise, seed, or schema-version mutation.
- Removing world objects from event effects.
- Arbitrary paths outside the allowed effect surface.

Before a player action, world advance, or daily settlement commits, the service previews the resulting world state and checks triggered queued-event effects. If this preflight fails, the parent patch is not committed. This prevents a half-success state where time advances but the triggered event fails.

The event log receives:

```text
queued_event_triggered
```

The payload includes:

- `queued_event_id`
- `queued_event_type`
- `trigger`
- `clock`
- `overdue`
- `scheduled_window`
- `effects_count`

## File Size And Coupling Rule

LangGraph workflows should orchestrate.

Engine modules should decide mechanics.

Storage modules should commit and read state.

Schemas should define contracts.

If a workflow file grows because it contains parsing rules, simulation rules, narrative rules, and storage behavior, split it before adding features.

## Future Splits

Likely next modules:

- `engine/dice.py`
- `engine/mechanics.py`
