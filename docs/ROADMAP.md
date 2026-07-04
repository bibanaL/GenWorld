# GenWorld Milestone Roadmap

## 0. Project Definition

GenWorld is a natural-language, multi-agent world simulator.

The player interacts with the world through free-form language. The backend maintains structured state, runs world simulation rules, coordinates agents through LangGraph, and records auditable state changes.

The project is not an AI novel generator. It is a world engine where AI proposes, the rule layer validates, and the engine commits state.

## Guiding Principles

1. Natural-language interaction, structured backend.
2. AI can create and propose, but cannot directly mutate core state.
3. Every important world change must be recorded as an event and a state patch.
4. World simulation must continue even when the player is not directly touching an entity.
5. Start with a small playable world before scaling the architecture.
6. Prefer inspectable local storage first, then introduce infrastructure only when there is a concrete need.
7. Style distillation is postponed until the simulation loop is stable.

## Phase 0: Repository And Environment Baseline

### Goal

Create a clean local project foundation that can run on the current machine without Docker, PostgreSQL, Redis, or a game engine.

### Current Machine Assumptions

- Python is available through `py`, currently Python 3.12.1.
- `python` should not be used because it points to the Windows Store placeholder.
- Node.js 22 is available.
- npm and pnpm are available.
- Git is available.
- SQLite is available through Python's standard library.
- Docker, PostgreSQL, Redis, Poetry, and uv are not assumed.

### Recommended Stack

- Python 3.12
- FastAPI
- LangGraph
- Pydantic
- SQLite through Python `sqlite3`
- OpenAI SDK or another LLM SDK behind a provider abstraction
- Simple HTML/JS frontend served by FastAPI

### Deliverables

- Git repository initialized.
- Python virtual environment created.
- Minimal dependency file.
- FastAPI service starts locally.
- Health-check endpoint works.
- SQLite database can be created and migrated manually.

### Acceptance Criteria

- Running one command starts the backend.
- A local browser can open a basic page.
- A test SQLite database can store and read one world record.

### Explicitly Not In Scope

- PostgreSQL
- Redis
- Docker
- Next.js
- Vector database
- Full authentication
- Multi-user support

## Phase 1: Core World Ledger

### Goal

Build the structured state foundation before adding complex AI behavior.

### Core Concepts

- World
- Entity
- Event
- State patch
- Mechanic
- Agent run
- World snapshot

### Suggested SQLite Tables

- `worlds`
- `world_snapshots`
- `entities`
- `events`
- `state_patches`
- `mechanics`
- `agent_runs`
- `memories`

### Deliverables

- Pydantic schemas for world state.
- SQLite storage layer.
- Append-only event log.
- State patch format.
- Snapshot save/load.
- Simple debug endpoint for reading current world state.

### Acceptance Criteria

- A world can be created and loaded.
- A state patch can be applied and recorded.
- The system can show what changed, when, and why.
- No AI call is required to test the ledger.

### Explicitly Not In Scope

- Semantic memory
- Vector retrieval
- Large-scale NPC autonomy
- AI-generated executable code

## Phase 2: World Generation MVP

### Goal

Turn a natural-language world prompt into a runnable initial world state.

### Inputs

Example:

```text
Create a modern city where spiritual energy has returned, corporations and sects fight over supernatural resources, and the player is a newly awakened courier.
```

### Generated Outputs

- World premise
- Core conflict
- Basic world rules
- 3 factions
- 5 to 10 NPCs
- 8 to 15 locations
- 3 to 5 world clocks
- Initial event queue
- Player starting state

### Deliverables

- `create_world` API.
- World-generation agent.
- Structured output schema.
- Validation and repair pass.
- Initial world snapshot committed to SQLite.

### Acceptance Criteria

- User can create a world from one natural-language prompt.
- Generated world contains enough structure to simulate at least 7 in-world days.
- Invalid AI output is rejected or repaired before commit.
- Hidden facts are separated from player-visible facts.

### Explicitly Not In Scope

- Complex prose style controls
- Long-term memory retrieval
- Procedural maps
- Images or game-engine rendering

## Phase 3: LangGraph Player Action Loop

### Goal

Make one complete player action run through a controlled multi-agent pipeline.

### LangGraph Flow

```text
load_world_state
-> parse_player_intent
-> build_context_pack
-> resolve_action
-> run_mechanics
-> advance_world
-> audit_state_patches
-> commit_state
-> narrate_result
```

### Agents

- Intent Parser
- Simulation Director
- State Auditor
- Narrator

### Deliverables

- LangGraph graph definition.
- Pydantic graph state.
- Natural-language action API.
- Deterministic dice/random helper with seed support.
- State patch validation.
- Basic narrative output.

### Acceptance Criteria

- Player can submit an action in natural language.
- The system parses intent into structured form.
- The action produces events and state patches.
- State Auditor can reject illegal patches.
- Narrator only describes committed facts.
- The system can run at least 20 consecutive player actions without losing world state.

### Explicitly Not In Scope

- One agent per NPC.
- One agent per faction running constantly.
- Advanced memory retrieval.
- Style distillation.

## Phase 4: World Simulation Loop

### Goal

Make the world move independently from the player.

### Simulation Features

- Time slots within a day.
- Daily settlement.
- Faction plans.
- NPC lightweight plans.
- World clocks.
- Triggered events.
- Delayed consequences.

### Suggested Time Model

- Morning
- Afternoon
- Evening
- Night

### Deliverables

- Time advancement engine.
- World clock engine.
- Faction plan schema.
- Background event generator.
- Daily settlement endpoint.
- Debug view showing active clocks and pending events.

### Acceptance Criteria

- A world can advance one time slot without player action.
- A world can advance one full day.
- Faction clocks can trigger events.
- Player actions can speed up, slow down, or redirect world clocks.
- Generated background events have visible causes in the event log.

### Explicitly Not In Scope

- Full economic simulation
- Large-scale battle simulation
- Global map simulation
- Persistent autonomous agent processes

## Phase 5: Mechanic DSL And AI-Created Local Rules

### Goal

Allow AI to create world-specific mechanics within a controlled rule format.

### Rule

AI may create mechanics, but the engine executes them.

AI should not directly execute arbitrary Python code in this phase.

### Example Mechanic

```yaml
mechanic_id: spirit_pollution
trigger:
  when: player_uses_spirit_power
  condition: location.pollution_level > 40
effect:
  - op: increase
    path: player.status.contamination
    value: 5
limits:
  max_increase_per_turn: 12
  cannot_directly_kill: true
```

### Deliverables

- Mechanic schema.
- Mechanic validator.
- Mechanic interpreter.
- Rules Engineer agent.
- Mechanic registry.
- Test cases for each generated mechanic.

### Acceptance Criteria

- AI can propose a new mechanic.
- The mechanic is validated before registration.
- The mechanic can produce legal state patches.
- Invalid mechanics are rejected with clear reasons.
- Mechanics are versioned and can be disabled.

### Explicitly Not In Scope

- Arbitrary AI-written Python execution.
- File, network, or database access from generated mechanics.
- Permanent world-rule rewrites without explicit approval.

## Phase 6: Local Memory And Retrieval

### Goal

Improve continuity without introducing a vector database yet.

### Storage Choice

Use SQLite `FTS5` for local full-text search over events, memories, NPC notes, and world facts.

### Deliverables

- Memory record schema.
- Event summarization after each day.
- FTS5 index.
- Context-pack retrieval by keyword/entity/time.
- Memory compaction rules.

### Acceptance Criteria

- The system can retrieve relevant past events by entity and keyword.
- Context packs include old facts without loading the entire world history.
- Daily summaries reduce prompt size.
- Retrieval results cite event IDs or memory IDs.

### Explicitly Not In Scope

- Vector database
- Embedding model dependency
- Cross-world semantic search

## Phase 7: Introduce Vector Retrieval

### When To Start This Phase

Do not introduce a vector database just because it is fashionable.

Start this phase when at least two of the following are true:

- A single world has more than 1,000 meaningful events or memory records.
- Keyword search misses important semantically related memories.
- NPC continuity depends on fuzzy memory retrieval.
- The context pack routinely omits relevant old facts.
- Multiple worlds need semantic search across similar concepts.

### Preferred First Choice

Use PostgreSQL with `pgvector` after the project has already moved to PostgreSQL.

### Alternative Local Choice

Use a lightweight local vector store only if PostgreSQL migration is intentionally postponed.

### Deliverables

- Embedding provider abstraction.
- Memory embedding job.
- Vector search endpoint.
- Hybrid retrieval: entity filters + time filters + vector similarity.
- Retrieval evaluation set.

### Acceptance Criteria

- Vector retrieval improves context relevance over FTS5 on a small evaluation set.
- Retrieved memories are traceable back to stored event IDs.
- The system can explain why a memory was included in a context pack.
- Vector search is used for memory retrieval, not as the source of truth.

### Explicitly Not In Scope

- Replacing the event log.
- Replacing structured world state.
- Letting vector memory override current canonical state.

## Phase 8: PostgreSQL Migration

### When To Start This Phase

Start after the simulation loop is fun and stable, not before.

Good triggers:

- SQLite write concurrency becomes painful.
- Multiple users or multiple worlds run concurrently.
- Debugging JSON queries in SQLite becomes limiting.
- Vector retrieval is ready and `pgvector` is preferred.
- Deployment needs a real database server.

### Deliverables

- PostgreSQL schema.
- Migration script from SQLite.
- JSONB-based world state storage.
- Optional `pgvector` extension.
- Database backup and restore workflow.

### Acceptance Criteria

- Existing worlds migrate without data loss.
- Event logs and state patches remain auditable.
- Performance is at least equal to SQLite for normal local usage.
- The app can run against either SQLite or PostgreSQL during migration.

### Explicitly Not In Scope

- Premature distributed systems design.
- Sharding.
- Event streaming infrastructure.

## Phase 9: Better Web Client

### Goal

Replace the simple HTML/JS interface only after the backend loop is useful.

### Candidate Stack

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query

### Deliverables

- World creation screen.
- Player action console.
- Story timeline.
- Debug state inspector.
- Event log view.
- Mechanic registry view.
- Clock and faction status view.

### Acceptance Criteria

- The UI makes the world easier to inspect and play.
- The user can continue a world without touching backend tools.
- Debug views expose state changes clearly.

### Explicitly Not In Scope

- Heavy animation
- Game-engine rendering
- Marketplace/social features

## Phase 10: Multi-Agent Expansion

### Goal

Introduce more specialized agents without losing central state control.

### Add Only As Needed

- Faction Agent
- NPC Agent
- Location Agent
- Questline Agent
- Mechanic Review Agent

### Rule

Agents do not own truth. The ledger owns truth.

Agents receive context packs and return proposals.

### Deliverables

- Agent role registry.
- Context-pack builder per agent type.
- Agent output schemas.
- Agent run tracing.
- Conflict resolution strategy.

### Acceptance Criteria

- Adding an agent improves a measurable workflow.
- Agent outputs remain structured.
- Conflicting proposals are resolved by the Simulation Director or core engine.
- No agent directly commits state.

### Explicitly Not In Scope

- Always-on NPC agents for every character.
- Agent group chat as the primary architecture.
- Unbounded agent recursion.

## Phase 11: Safe AI-Written Functions

### Goal

Optionally allow AI to generate executable functions for local world mechanics.

### Entry Criteria

Only begin this phase after the DSL mechanic system has proven insufficient.

Good reasons:

- Some mechanics are too awkward to express in DSL.
- Mechanics need reusable calculations.
- The system needs richer condition logic.

### Required Safety Constraints

- Pure functions only.
- No file access.
- No network access.
- No direct database access.
- Strict timeouts.
- Strict input and output schemas.
- Deterministic seeded randomness.
- Static analysis before registration.
- Unit tests before activation.
- Only state patches as output.

### Deliverables

- Function sandbox.
- Function permission model.
- Generated function test harness.
- Versioned function registry.
- Rollback and disable controls.

### Acceptance Criteria

- A generated function can be tested before use.
- A generated function cannot mutate state directly.
- A generated function cannot access external resources.
- Bad functions fail safely.

### Explicitly Not In Scope

- General-purpose plugin execution.
- User-uploaded arbitrary code.
- Agent self-modifying core engine code.

## Phase 12: Style Distillation Layer

### Goal

Add controlled prose style after the simulation is already stable.

### Why This Is Late

Style is valuable, but it must not decide facts. If added too early, it can hide simulation bugs behind pretty prose.

### Deliverables

- Style profile schema.
- Style extraction from user-provided samples.
- Narrator style controls.
- Safety boundary between committed facts and prose rendering.

### Acceptance Criteria

- Same committed event can be rendered in different styles.
- Style layer cannot change world state.
- Style output does not invent uncommitted facts.

## Phase 13: Multi-User And Deployment

### Goal

Prepare the system for real users after the single-user world loop is proven.

### Deliverables

- User accounts.
- World ownership.
- Save slots.
- Deployment configuration.
- Background job system.
- Database backups.
- Rate limits and model-cost tracking.

### Likely Added Infrastructure

- PostgreSQL
- Redis
- Background worker
- Containerized deployment

### Acceptance Criteria

- Multiple users can run worlds independently.
- Long-running jobs do not block normal requests.
- Costs and token usage are visible.
- Worlds can be backed up and restored.

## Progress Gates

Use these gates to avoid premature complexity.

### Gate A: First Playable Loop

Required before adding advanced UI or vector memory.

- Create world.
- Submit player action.
- Resolve result.
- Commit state.
- Narrate result.
- Continue for 20 actions.

### Gate B: Seven-Day Simulation

Required before adding PostgreSQL or vector retrieval.

- One world runs for 7 in-world days.
- At least 3 factions act.
- World clocks trigger at least 2 events.
- Event log explains major changes.

### Gate C: Ten-Day Continuity Test

Required before style distillation or AI-written functions.

- One world runs for 10 in-world days.
- NPCs remember relevant prior events.
- Contradictions are detected or avoided.
- Player actions have delayed consequences.

### Gate D: Memory Pressure Test

Required before vector database.

- More than 1,000 meaningful event or memory records.
- FTS5 retrieval misses relevant semantic matches.
- Context pack quality can be measured.

## Current Recommended Next Step

Build Phase 0 and Phase 1 first:

1. Initialize the repository.
2. Create the Python backend skeleton.
3. Add FastAPI, LangGraph, Pydantic, and a local SQLite ledger.
4. Implement world creation without complex simulation.
5. Verify that state patches and event logs are auditable.

The first real milestone is not beautiful storytelling. The first real milestone is a world state that can survive repeated actions without becoming inconsistent.
