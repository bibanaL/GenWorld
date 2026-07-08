# Architecture

This document describes the current backend skeleton.

## Boundary Rule

AI and graph nodes may propose state changes.

Only the ledger commits state changes.

State changes must pass through Patch DSL validation and execution.

```text
agent or engine module
-> PatchOperation list
-> SQLiteLedger.apply_state_patch
-> auditor
-> patch executor
-> world state JSON
-> event log
```

## Current Layers

### API

```text
backend/app/main.py
```

FastAPI routes live here for now. Split into routers when route count or auth concerns grow.

### Graph

```text
backend/app/graph/player_action_graph.py
```

LangGraph orchestration only. It should not absorb parsing rules, simulation rules, storage code, or narrative logic.

### Agents

```text
backend/app/agents/
```

Current local agents:

- `intent_parser.py`
- `narrator.py`
- `world_generator.py`

These are local placeholders for future LLM-backed implementations.

### Engine

```text
backend/app/engine/
```

Engine modules produce rules, context, outcomes, and patch operations. They should not commit directly to storage.

Current modules:

- `action_resolver.py`
- `auditor.py`
- `context_builder.py`
- `daily_settlement.py`
- `event_effects.py`
- `event_queue.py`
- `faction_plans.py`
- `patches.py`
- `simulator.py`
- `time.py`
- `world_builder.py`

### Services

```text
backend/app/services/
```

Application services coordinate engine modules and storage commits.

Current services:

- `daily_settlement_service.py`
- `event_queue_service.py`

### Schemas

```text
backend/app/schemas/
```

Pydantic contracts for API requests, graph state fragments, world state, generation, actions, patches, and simulation.

### Storage

```text
backend/app/storage/sqlite_store.py
```

SQLite ledger. It owns world persistence, event logs, and patch records.

## Current Known Large Files

- `agents/world_generator.py`
- `storage/sqlite_store.py`

Do not split them just for aesthetics. Split when a real new responsibility appears:

- LLM world generation provider.
- Multiple storage backends.
- Migration system.
- More complex event-log queries.

## Test Contract

Core regression tests live in:

```text
backend/tests/test_core_flow.py
```

They must keep passing before adding feature work.
