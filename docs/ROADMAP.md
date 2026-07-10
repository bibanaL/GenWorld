# GenWorld Development Roadmap

Status: active roadmap for the fixed-world life-sandbox product direction.

This roadmap supersedes the earlier world-generation-first plan. The approved
experience and dynamic-system boundaries are defined in:

- `PRODUCT_SPEC.md`
- `DYNAMIC_MECHANICS.md`

Current implementation documents describe the prototype as it exists today.
When they conflict with the two product documents above, the product documents
govern future work.

## Product Target

The first playable GenWorld release is a desktop-web, natural-language life
sandbox in one authored contemporary city and university district.

The player:

- Creates one university-student avatar from a structured draft.
- Acts through natural language inside a persistent structured world.
- Uses Idea Mode to found and reform institutions through in-world causality.
- Uses a separate structured Sandbox Editor to edit the save directly.
- May save, load, branch, and retry freely.
- Can eventually create bounded save-local mechanics when existing systems are
  not expressive enough.

Natural-language world generation is not part of the first playable release.

## Current Prototype Baseline

The repository already proves several useful foundations:

- FastAPI application and Pydantic request/response schemas.
- SQLite storage for worlds, events, and state patches.
- Patch DSL validation and append-only patch records.
- A structured `WorldState` with actors, locations, factions, clocks, facts,
  and queued events.
- A local deterministic world seed generator.
- A local LangGraph action pipeline.
- Four-slot time advancement.
- Faction plans, clocks, queued events, event effects, and daily settlement.
- Core regression tests for the prototype flow.

These are engineering prototypes, not completed player-facing milestones.

Known baseline gaps include:

- A patched state is not fully revalidated before persistence.
- Repeated investigation can create duplicate fact IDs.
- Multi-step patch and event transitions are not one atomic unit.
- Dependencies are not locked and the test client emits a deprecation warning.
- The local generator is still presented as a product API.
- The action loop is limited to six hard-coded intent types and fixed effects.
- Time is too coarse for schedules and life simulation.
- There is no frontend, save branching, character draft, activity model,
  personal NPC simulation, Idea Mode, Sandbox Editor, or mechanic runtime.

## Development Rules

1. Build vertical slices. A gameplay milestone is not complete until its API,
   persistence, player projection, UI, and regression path work together.
2. Preserve the ledger boundary. Engine, model, and mechanic code may propose
   changes; only validated transactions commit them.
3. Keep hidden canonical state separate from player-visible projections.
4. Reuse generic activities and domain frameworks before generating a new
   mechanic.
5. No generated general-purpose code runs in the first playable version.
6. No milestone expands the world, identity range, or platform scope without a
   written product decision.
7. Every irreversible migration includes backup, rollback, and compatibility
   tests.
8. A feature that cannot survive save, load, restart, and replay is not done.

## Definition Of Done

A milestone is complete only when:

- Contracts and relevant design decisions are documented.
- State and API migrations are explicit.
- Success, rejection, interruption, and recovery paths are tested.
- Player-visible information does not leak hidden state.
- Committed effects cite their patch and event records.
- The feature survives application restart and save reload.
- The vertical acceptance scenario is reproducible.
- The full regression suite passes without new warnings owned by the project.

## Milestone 0: Product Contract

Status: COMPLETE

### Goal

Replace the generic world-simulator direction with an explicit fixed-world life
sandbox contract before implementation expands further.

### Delivered

- Fixed contemporary university setting for the first version.
- University-student-only starting identity.
- Action, Idea, and Sandbox Editor mode boundaries.
- Natural-language action and ambiguity policy.
- Minute-level, turn-based time direction.
- Tiered NPC simulation and daily settlement direction.
- Free save, load, branch, and retry policy.
- First-version life-system scope.
- Desktop React client direction and information architecture.
- MechanicSpec-first dynamic-rule direction.
- General-purpose scripting deferred behind an evidence gate.

### Exit Gate

`PRODUCT_SPEC.md`, `DYNAMIC_MECHANICS.md`, and this roadmap agree on product
scope and terminology.

## Milestone 1: Canonical State Integrity

Status: NEXT

### Goal

Make the ledger a trustworthy base for saves, life simulation, editor changes,
and future generated mechanics.

### Backend Deliverables

- Revalidate and normalize the complete next `WorldState` before persistence.
- Add domain invariant validation for:
  - Stable and unique IDs.
  - Dictionary-key and record-ID agreement.
  - Valid actor and location references.
  - Valid schedule and time values.
  - Clock progress within bounds.
  - Unique facts, queued events, and active commitments.
- Reject invalid patches while recording the rejection and preserving state.
- Define an atomic transition service for a primary patch, derived effects, and
  associated events.
- Include explicit patch IDs in all consequence events.
- Add optimistic world revision checks to prevent lost concurrent updates.
- Add a schema migration mechanism for SQLite and canonical state.
- Introduce an application factory so tests can inject isolated settings and a
  ledger without import-time global coupling.
- Lock dependency versions and resolve the current TestClient warning.
- Add formatting, linting, type-checking, and automated test commands.

### Test Deliverables

- Invalid scalar types and constrained values are rejected.
- Broken references and duplicate IDs are rejected.
- Duplicate investigation facts are not appended.
- A derived event failure cannot leave a half-committed parent transition.
- Concurrent revision conflicts are rejected or retried explicitly.
- Existing prototype behavior remains covered.

### Acceptance Gate: State Integrity

- Twenty mixed prototype actions complete without invalid state or duplicate
  canonical IDs.
- A patch that sets `/time/day` to a string is rejected.
- Every committed consequence can be traced to a patch.
- Restarting the application preserves an identical validated state.

### Explicitly Not In Scope

- New player-facing gameplay.
- Frontend work.
- LLM integration.
- Save-local mechanics.

## Milestone 2: Fixed World And Character Creation

Status: PENDING

### Goal

Create the first real player entry flow without generating a world from a
natural-language premise.

### Content Deliverables

- One authored fictional contemporary city and university district.
- Eight to twelve important authored locations, including housing, campus,
  classrooms, food, exercise, shopping, and a public social space.
- Eight to twelve important authored NPCs with identities, schedules, traits,
  relationships, and starting knowledge.
- A lightweight background-NPC template that can become persistent after
  meaningful interaction.
- A versioned fixed-world content pack with stable IDs.

### Backend Deliverables

- `CharacterDraft` with `user_locked`, `generated`, and `derived` provenance.
- Identity-prompt parsing restricted to university-student identities.
- Draft generation, field edit, selective reroll, full reroll, validation, and
  confirmation APIs.
- Confirmation creates the canonical avatar and first save snapshot.
- Existing local world generation remains available only as a test fixture or
  explicit developer endpoint.
- Reject identities outside first-version scope with a clear product-level
  response rather than silently generating another world type.

### Frontend Deliverables

- React, TypeScript, and Vite application scaffold.
- Dedicated character-creation flow.
- Structured draft review with source labels.
- Selective edit and reroll controls.
- Confirmation and first-save transition.

### Acceptance Gate: New Game

- A player can enter a constrained identity such as an ordinary university
  student with modest finances.
- Player-locked facts survive every reroll.
- Generated fields can be independently edited or rerolled.
- Confirmation produces a valid avatar in the authored world.
- Loading the first snapshot reproduces the same avatar and starting state.

### Explicitly Not In Scope

- Other professions or age groups.
- Natural-language world generation.
- Generated major locations or institutions.
- Full visual polish.

## Milestone 3: Scene, Time, Travel, And Activities

Status: PENDING

### Goal

Make the fixed world explorable through structured scenes and time-consuming
activities before introducing model-backed free-form planning.

### Backend Deliverables

- Replace canonical four-slot time with day plus minute-of-day.
- Derive display periods such as morning and evening from canonical time.
- Add authored location connections, opening hours, and travel duration.
- Add an `Activity` model with stages, participants, location, duration,
  progress, interruption policy, and completion state.
- Implement built-in movement, rest, eat, study, exercise, and wait activities.
- Advance needs and schedules by elapsed duration rather than one fixed tick.
- Trigger daily settlement whenever time crosses the day boundary.
- Expose a player-visible `SceneView` projection without hidden facts.
- Expose separate debug and editor projections.

### Frontend Deliverables

- Main desktop game shell.
- Left avatar-status region.
- Center structured scene, narrative history, visible actors and objects, and
  suggested affordances.
- Right contextual tool region with initial schedule and event tabs.
- Clickable built-in interactions for testing the activity loop.

### Acceptance Gate: One Structured Day

- The avatar can travel from housing to class, eat, study, exercise, and rest.
- Opening hours and travel time affect feasibility.
- Activities advance time by different durations.
- The scene projection changes with time, location, and present actors.
- Hidden NPC and world state is absent from the player response.
- Crossing midnight performs one and only one daily settlement.

### Explicitly Not In Scope

- Free-form model-backed actions.
- Multi-turn dialogue.
- Idea Mode.
- Dynamic mechanics.

## Milestone 4: Natural-Language Planning And Checks

Status: PENDING

### Goal

Turn free-form player language into bounded action plans that reuse the fixed
world and activity systems.

### Backend Deliverables

- A model-provider abstraction with structured-output support and explicit
  timeout, retry, and failure behavior.
- `ActionPlan` with intent, goal, targets, approach, tone, inferred details,
  ordered steps, duration estimates, resources, and stop conditions.
- Context construction from the player-visible scene and authorized canonical
  facts.
- Low-impact default inference and material-ambiguity detection.
- Compound-action execution until a decision point or blocker.
- A pluggable `ResolutionCheck` engine with a first tuned `2d6` implementation,
  skills, difficulty, contextual modifiers, opposed factors, and outcome
  degrees.
- Check records linked to committed patches and events.
- REST command endpoints and SSE progress for model-backed planning and
  resolution.
- Basic quick-save and load before checks.
- A deterministic local planner retained for tests and model outages.

### Frontend Deliverables

- Natural-language Action composer.
- Visible planning and resolution progress.
- Focused clarification for material ambiguity.
- Structured outcome with expandable roll, difficulty, and modifier details.
- Quick-save and load controls.

### Acceptance Gate: Gym Action

Given an avatar at home, the player can enter:

```text
I go to the gym to work out and try to meet a trainer.
```

The system must:

- Select or clarify a valid authored gym.
- Infer immediate departure and reasonable duration.
- Plan travel, exercise, and social-contact steps.
- Avoid rolling for routine travel.
- Apply condition and skill context to uncertain steps.
- Preserve NPC agency.
- Commit time, location, condition, skill, and event changes atomically.

### Explicitly Not In Scope

- Creating new locations from the action.
- Generated rules.
- Long-running NPC dialogue.
- Organization founding.

## Milestone 5: Social Interaction And NPC Continuity

Status: PENDING

### Goal

Make scene interactions produce persistent relationships, memories, claims,
promises, and independently motivated NPC reactions.

### Backend Deliverables

- `pending_interaction` state for actions awaiting a player response.
- `DialogueMove` parsing for claims, tone, promises, concessions, threats,
  refusals, conditions, and exchanges.
- Resume, refuse, leave, interrupt, and timeout behavior.
- Important-NPC schedules, goals, current activities, relationships, and
  lightweight needs.
- Relationship evidence and per-person event history.
- Persistent promises with beneficiary, value, deadline, fulfillment, breach,
  and consequence state.
- Tiered NPC update policy for scene, important, persistent, and background
  actors.
- NPC reactions derived from traits, knowledge, interests, relationships, and
  context rather than model narration alone.

### Frontend Deliverables

- Pending-interaction presentation inside the center scene.
- Free-text response, refuse, leave, and interrupt controls.
- Relationship browser.
- Per-NPC event and promise history.
- Qualitative NPC attitude display without hidden-state leakage.

### Acceptance Gate: Conditional Recruitment

- An NPC asks a material question during a recruitment action.
- A sincere promise improves the immediate check for an explainable reason.
- The promise becomes a future obligation rather than a temporary modifier.
- Fulfillment improves trust; breach damages trust and creates a remembered
  event.
- Reloading the save preserves the interaction, obligation, and NPC memory.

### Explicitly Not In Scope

- One LLM call per NPC per turn.
- Omniscient relationship values in the normal UI.
- Generated organizations.

## Milestone 6: University Life And Seven-Day Simulation

Status: PENDING

### Goal

Complete the first coherent life-sandbox loop before adding system creation.

### Backend Deliverables

- Energy, hunger, stress, and mood rules driven by elapsed time and activities.
- Skills that influence checks and improve through relevant practice.
- Class schedules, attendance, coursework, study, and academic performance.
- Lightweight money, routine costs, and limited income opportunities.
- Important-NPC daily plans and background catch-up.
- Daily summaries linked to source events.
- Event scheduling that distinguishes direct immediate consequences from
  background settlement.
- Balance limits that prevent routine actions from producing runaway values.

### Frontend Deliverables

- Legible needs, mood, skills, schedule, money, and current activity.
- Daily summary and next-day schedule.
- Visible causes for major changes without exposing hidden simulation state.

### Acceptance Gate: Seven-Day Life

One avatar completes seven in-world days with at least:

- Five attended or missed scheduled commitments.
- Several exercise, study, rest, travel, and social activities.
- Three important NPCs following distinct schedules.
- One fulfilled and one breached or renegotiated promise.
- Skill progression that materially affects a later check.
- A financial tradeoff.
- A background event with traceable causes.

At the end, the state validates, the event history explains major changes, and
different player choices produce a materially different week.

### Explicitly Not In Scope

- Other careers.
- Full inventory or housing simulation.
- Idea Mode and generated mechanics.

## Milestone 7: Save Branches And Sandbox Editor

Status: PENDING

### Goal

Give the player explicit control over saves and a safe, visual way to edit the
current save without confusing editor authority with avatar agency.

### Backend Deliverables

- Named saves, quick saves, snapshots, parent-branch metadata, and load APIs.
- Transaction-safe snapshot points for activities and pending interactions.
- New roll attempts after loading a pre-check snapshot.
- Editor-only canonical projections and mutation endpoints.
- Structured editor operations that still pass schema and invariant validation.
- Diff preview, validation report, atomic commit, undo, and rollback.
- Editor events separated from diegetic world events while remaining auditable.

### Frontend Deliverables

- Save browser and branch history.
- Full-screen Sandbox Editor.
- Entity tree and structured forms for actors, locations, relationships,
  schedules, resources, activities, events, and mechanic records.
- Diff and validation preview.
- Undo and snapshot recovery.
- Clear visual separation from Action and Idea modes.

### Acceptance Gate: Edit And Recover

- A player saves before a check, loads, and receives a new attempt on a branch.
- An editor change updates a relationship and schedule without advancing time.
- An invalid editor change is rejected before commit.
- Undo restores the exact prior snapshot.
- Normal game views still hide canonical secrets after editor use.

### Explicitly Not In Scope

- Natural-language editor commands.
- Editing application or database schemas.
- Editing runtime security policy.

## Milestone 8: Idea Mode And Organizations

Status: PENDING

### Goal

Let the avatar propose, found, operate, and reform an organization while world
authority, resources, promises, and NPC agency remain meaningful.

### Backend Deliverables

- `IdeaDraft` and explicit Action/Idea mode routing.
- Generic project and organization frameworks.
- Organization identity, doctrine, policies, governance, roles, membership,
  resources, activities, schedules, benefits, promises, and lifecycle.
- Founding projects with prerequisites and progress.
- Recruitment actions integrated with social resolution.
- Reform proposals with authority checks, voting, affected-party analysis, and
  versioned rules.
- Member acceptance, resistance, exit, and splinter-organization behavior.
- Cancellation that affects future schedules without deleting history.

### Frontend Deliverables

- Action/Idea segmented composer control.
- Structured idea-draft review and revision.
- Founding-project and organization views.
- Governance, membership, obligations, activities, and reform views.

### Acceptance Gate: Found, Recruit, Reform

The player can:

1. Propose a vegetarian environmental religion.
2. Confirm a draft and create a founding project.
3. Recruit in a supermarket.
4. Make a promise of free vegetables during a pending interaction.
5. Build membership through repeated in-world actions.
6. Propose a reversal to a meat-centered doctrine.
7. Apply the governance process.
8. Observe members accept, leave, resist, or split.

Past events, public claims, paid costs, and unfulfilled promises must survive
the reform.

### Explicitly Not In Scope

- A separate generated code module for every organization.
- Instant institution creation on draft confirmation.
- Direct assignment of member beliefs.

## Milestone 9: MechanicSpec Runtime

Status: PENDING

### Goal

Provide a bounded, versioned save-local rule format before allowing a model to
generate mechanics.

### Backend Deliverables

- Versioned `MechanicSpec` schema and canonical storage.
- Safe parsed conditions and formulas.
- Private namespaced mechanic state.
- Registered affordances, activities, state machines, triggers, checks,
  schedules, patch templates, and event templates.
- Explicit read and patch capabilities.
- Runtime execution, memory, output, and scheduling budgets.
- Draft, validating, simulated, active, suspended, superseded, and archived
  lifecycle states.
- Validation against a cloned snapshot.
- Engine-owned tests and mechanic-provided tests.
- Transaction rollback, automatic suspension, and inspectable failures.
- Version migration and host API compatibility handling.
- Save, load, export, import, and editor support.

### Authored Reference Mechanics

At least two mechanics are written manually through the same public contract:

- A fourteen-day night-running challenge with deposits, attendance, penalties,
  and prize settlement.
- A member-credit and budget-voting extension for an organization.

These examples must prove repeated actions, private state, scheduled work,
multi-actor effects, reform, and archival.

### Acceptance Gate: Manual Dynamic Rules

- Both mechanics run without application-specific branching in the engine.
- Capability violations are rejected.
- Infinite or excessive work is terminated and rolled back.
- Save and reload preserve code-independent specifications and private state.
- A version upgrade migrates an active mechanic without losing history.
- Disabling one save-local mechanic does not affect another save.

### Explicitly Not In Scope

- Model-generated mechanics.
- Python, JavaScript, Lua, or WebAssembly execution.
- Runtime-defined database schemas.

## Milestone 10: Model-Generated Save Mechanics

Status: PENDING

### Goal

Deliver the core differentiator: a player idea that existing systems cannot
express can become a validated, save-local mechanic.

### Backend Deliverables

- Classification through the full resolution ladder before generation.
- Structured model generation of `MechanicSpec`, explanation, tests, and
  migration policy.
- Static validation and capability minimization.
- Clone-world simulation with success and adversarial cases.
- Activation only after all engine-owned gates pass.
- Runtime monitoring, automatic suspension, rollback, and repair proposal.
- Reform through successor specification versions.
- Provenance from player idea to generated spec, checks, patches, and events.

### Frontend Deliverables

- Clear progress while a mechanic is proposed, validated, simulated, and
  activated.
- Human-readable rule summary and requested capabilities.
- Mechanic history, versions, tests, failures, suspend, rollback, and archive.
- Sandbox Editor support for structured mechanic inspection and revision.

### Acceptance Gate: New Persistent System

A player proposes behavior that the base organization framework and authored
mechanics cannot express. The system must:

- Explain why a new mechanic is required.
- Generate a bounded specification rather than application source.
- Reject unsafe or invalid variants without changing the save.
- Activate a valid variant.
- Add persistent state, interactions, and scheduled settlement.
- Survive save, load, restart, and version reform.
- Affect only the current save.

### Explicitly Not In Scope

- General-purpose generated source code.
- Silent capability expansion.
- Automatic modification of base mechanics.

## Milestone 11: First Playable Alpha

Status: PENDING

### Goal

Stabilize all vertical slices into a coherent local alpha rather than adding
new domains.

### Deliverables

- End-to-end onboarding and recovery from model, validation, and runtime errors.
- Performance budgets for action planning, settlement, saves, and mechanics.
- UI loading, empty, interrupted, rejected, and recovery states.
- Accessibility and keyboard navigation for primary workflows.
- Save migration and backup tests across application versions.
- Thirty-day continuity and event-log pressure tests.
- Structured playtest instrumentation without hidden-state leakage.
- Documentation for setup, saves, editor recovery, and known scope limits.

### Acceptance Gates

- A new player can create an avatar and complete a week without developer tools.
- Thirty in-world days complete without state corruption or unbounded queues.
- At least three important NPC relationships remain causally understandable.
- One organization survives founding, operation, reform, and a member split.
- One generated mechanic survives a version migration.
- Save branches, quick reload, editor undo, and recovery all preserve integrity.
- Normal play never requires direct JSON editing.

## General Script Runtime Research Gate

Lua, QuickJS, or WebAssembly is not a scheduled product milestone.

Research begins only when all of the following are true:

- Milestone 10 is complete.
- At least three desirable mechanics cannot be expressed cleanly in
  `MechanicSpec`.
- Expanding the structured representation would make it materially less safe or
  understandable.
- Save migration and capability enforcement are already proven.
- A test corpus exists for containment, determinism, timeouts, memory limits,
  host API compatibility, and rollback.

Lua is the preferred first candidate. QuickJS is the secondary candidate.
Python is not eligible for in-process untrusted mechanic execution.

## Deferred Backlog

The following are intentionally not placed on the active roadmap:

- Natural-language world generation.
- Multiple world genres or cities.
- Non-student starting identities.
- Multiple controllable avatars or households.
- Full professions outside the university slice.
- Housing construction and detailed inventory simulation.
- Real-time background simulation.
- Mobile-first client.
- Multiplayer, accounts, and deployment architecture.
- PostgreSQL, vector retrieval, and distributed infrastructure.
- AI-written application source code.

Items enter the roadmap only after the fixed-world alpha provides evidence that
they solve a real player or scale problem.

## Immediate Next Work

Start Milestone 1 only.

The first implementation sequence is:

1. Add post-patch full-state validation and domain invariants.
2. Fix duplicate canonical IDs.
3. Define atomic transition and event-linking behavior.
4. Add optimistic revisions and migration scaffolding.
5. Refactor application construction for isolated tests.
6. Lock dependencies and clean the test baseline.
7. Re-run the twenty-action integrity gate.

Do not start the frontend, fixed-world content, or model integration until the
Milestone 1 state-integrity gate passes.
