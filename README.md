# GenWorld

GenWorld is a natural-language life sandbox with a structured, auditable world
state.

The first playable product is intentionally fixed in scope:

- One authored contemporary city and university district.
- One controllable university-student avatar.
- Natural-language actions inside a persistent life simulation.
- Diegetic Idea Mode for founding and reforming institutions.
- A separate structured Sandbox Editor for direct save editing.
- Bounded save-local mechanics built from a versioned `MechanicSpec`.

The repository currently contains a backend prototype for the ledger, patch
boundary, local action graph, time advancement, faction plans, queued events,
and daily settlement. It does not yet implement the approved player experience.
The deterministic world generator remains a test fixture and is not the target
new-game flow.

The immediate milestone is canonical state integrity. Frontend work, fixed-world
content, and model integration begin only after that gate passes.

## Current Stack

- Python 3.12 through `py`
- FastAPI
- LangGraph
- Pydantic
- SQLite through Python's standard library
- Standard-library `unittest`

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010
```

## Test

```powershell
.\.venv\Scripts\python -m unittest discover -s backend\tests -v
```

## Core APIs

These are the current prototype APIs, not the final product contract.

- `GET /health`
- `POST /worlds`
- `GET /worlds`
- `POST /worlds/generate`
- `GET /worlds/{world_id}`
- `POST /worlds/{world_id}/actions`
- `POST /worlds/{world_id}/advance`
- `POST /worlds/{world_id}/settle-day`
- `POST /worlds/{world_id}/events`
- `POST /worlds/{world_id}/patches`
- `GET /worlds/{world_id}/events`
- `GET /worlds/{world_id}/patches`

## Important Docs

- [Product Specification](docs/PRODUCT_SPEC.md)
- [Dynamic Mechanics](docs/DYNAMIC_MECHANICS.md)
- [Roadmap](docs/ROADMAP.md)
- [World State Schema](docs/WORLD_STATE_SCHEMA.md)
- [Patch DSL](docs/PATCH_DSL.md)
- [Prototype World Generation](docs/WORLD_GENERATION.md)
- [Prototype Action Loop](docs/ACTION_LOOP.md)
- [Prototype Simulation Engine](docs/SIMULATION_ENGINE.md)
- [Architecture](docs/ARCHITECTURE.md)
