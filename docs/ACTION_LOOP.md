# Player Action Loop

Status: current prototype implementation.

The six local intent types and fixed one-step outcomes are scaffolding, not the
target action contract. The approved direction introduces minute-level time,
`ActionPlan`, multi-step `Activity`, pending interaction, and auditable
resolution checks. See `PRODUCT_SPEC.md` and `ROADMAP.md`.

The first player action loop is a local LangGraph workflow.

It is intentionally simple. Its job is to prove that a natural-language action can move through a controlled pipeline and produce audited world-state changes.

## API

```http
POST /worlds/{world_id}/actions
```

Example request:

```json
{
  "text": "I investigate the strange pressure around the old station.",
  "actor_id": "player",
  "advance_time": true
}
```

Example response shape:

```json
{
  "world_id": "...",
  "action_text": "...",
  "intent": {},
  "context_pack": {},
  "outcome": {},
  "patch": {},
  "event_queue_patch": {},
  "triggered_events": [],
  "narrative": "...",
  "resolved_at": "..."
}
```

## LangGraph Flow

```text
load_world_state
-> parse_player_intent
-> build_context_pack
-> resolve_action
-> advance_world
-> commit_state
-> narrate_result
```

## Module Boundaries

The graph file should stay thin:

```text
backend/app/graph/player_action_graph.py
```

Current implementation modules:

- `agents/intent_parser.py`: local keyword and name matching.
- `engine/context_builder.py`: selects relevant state for the action.
- `engine/action_resolver.py`: converts intent and context into Patch DSL operations.
- `engine/simulator.py`: adds background time, clock advancement, and faction plan ticks.
- `services/event_queue_service.py`: preflights triggered queued-event effects, then processes triggered events after state commit.
- `agents/narrator.py`: renders a simple result string from committed facts.

The graph should orchestrate these modules, not absorb their logic.

## Current Local Intent Types

- `move`
- `investigate`
- `talk`
- `rest`
- `wait`
- `unknown`

The current parser uses simple keyword and name matching. It is only a placeholder for a future LLM intent parser.

## State Mutation Boundary

The action graph does not mutate world state directly.

It produces Patch DSL operations, then commits them through the SQLite ledger:

```text
action graph
-> PatchOperation list
-> ledger.apply_state_patch
-> auditor
-> patch executor
-> event log
```

Before the action patch commits, the graph previews the resulting world state and checks whether triggered queued events have legal effects.

After the action patch commits, the graph processes `event_queue` against the latest world state. Triggered queued events are removed through a second patch, legal event effects are applied through the same patch, and `queued_event_triggered` records are written.

## Current Behavior

`move`

- Sets `/player/current_location_id` when a known location is matched.
- Advances time when `advance_time` is true.
- Ticks the first two world clocks.
- Ticks active faction plans through the simulation engine.

`investigate`

- Increases fatigue.
- Adds a player-known fact.
- Advances time.
- Ticks world clocks more aggressively than low-risk actions.
- Ticks active faction plans.

`talk`

- Creates or refreshes a basic relationship record.
- Advances time.

`rest`

- Reduces fatigue and exposure without going below zero.
- Advances time.

`wait`

- Advances time and world clocks without direct player changes.

`unknown`

- Records an uncertain action and increases fatigue slightly.

## Current Limits

- No LLM parsing yet.
- No real dice system yet.
- No detailed difficulty model yet.
- No world mechanics DSL execution yet.
- No rich narrator yet.
- No conflict resolution between multiple agents yet.

These are deliberate omissions. The current milestone is a stable action pipeline, not a finished game master.
