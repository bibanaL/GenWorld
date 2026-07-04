# GenWorld

GenWorld is a natural-language, multi-agent world simulator.

Current focus:

- Structured world ledger.
- Patch-based state mutation.
- Local world generation.
- Local LangGraph player action loop.
- Local world time and clock advancement.

LLM providers are intentionally not connected yet. The current milestone is to prove that the world can run, mutate, and audit itself without depending on model output.

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

- `GET /health`
- `POST /worlds`
- `POST /worlds/generate`
- `GET /worlds/{world_id}`
- `POST /worlds/{world_id}/actions`
- `POST /worlds/{world_id}/advance`
- `POST /worlds/{world_id}/settle-day`
- `POST /worlds/{world_id}/patches`
- `GET /worlds/{world_id}/events`
- `GET /worlds/{world_id}/patches`

## Important Docs

- [Roadmap](docs/ROADMAP.md)
- [World State Schema](docs/WORLD_STATE_SCHEMA.md)
- [Patch DSL](docs/PATCH_DSL.md)
- [World Generation](docs/WORLD_GENERATION.md)
- [Action Loop](docs/ACTION_LOOP.md)
- [Simulation Engine](docs/SIMULATION_ENGINE.md)
- [Architecture](docs/ARCHITECTURE.md)
