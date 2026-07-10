# GenWorld Product Specification

Status: approved product direction for the first playable version.

This document defines the target experience. Documents such as
`ACTION_LOOP.md` and `SIMULATION_ENGINE.md` describe the current prototype and
must not be treated as the final product contract.

## Product Statement

GenWorld is a natural-language life sandbox set in one fixed contemporary
world.

The player controls a single avatar. The player may attempt any action that is
plausible in the setting, while the rule engine decides feasibility, time,
costs, checks, NPC reactions, and committed consequences.

The canonical world is structured and persistent. Language models interpret,
plan, propose content, and narrate. They do not directly mutate canonical
state.

The first playable version is deliberately narrow:

- One authored fictional contemporary city.
- One authored university and its surrounding neighborhood.
- One controllable university-student avatar.
- A fixed set of core institutions and important locations.
- Eight to twelve important authored NPCs.
- Lightweight background NPCs that may become persistent after interaction.

Natural-language world generation, arbitrary starting professions, multiple
controllable avatars, and generated cities are deferred.

## Experience Principles

1. Freedom means freedom to attempt, not guaranteed success.
2. Player phrasing controls precision, not permission to act.
3. Mundane missing details should be inferred when the consequence is small.
4. Material ambiguity, irreversible actions, and large commitments require a
   player decision.
5. NPCs retain agency. A player action may persuade or pressure an NPC but may
   not dictate the NPC's internal state or response.
6. Direct consequences happen immediately. Background simulation is primarily
   settled at day boundaries.
7. Past events, promises, and memories cannot be erased by rewriting current
   rules.
8. The player owns the save experience and may save, load, and retry freely.
9. Every committed change remains inspectable through state patches and event
   records.
10. New systems should reuse stable domain frameworks before a save-specific
    mechanic is created.

## Three Modes

GenWorld has three explicit interaction modes. The system must never infer the
mode from ambiguous prose.

### Action Mode

Action Mode is diegetic. The player controls the avatar inside the world.

- Input is natural language.
- Actions consume inferred world time.
- Preconditions, checks, resources, and NPC agency apply.
- Immediate scene reactions are resolved before the action completes.
- Relevant NPCs and local events receive a small simulation tick.
- Crossing a day boundary invokes daily settlement.

### Idea Mode

Idea Mode is also diegetic. The avatar designs an institution, project,
challenge, policy, or other persistent system.

- Input is natural language.
- Drafting does not advance world time.
- The output is a structured proposal, not an instantly real institution.
- The player may revise or confirm the proposal.
- A confirmed proposal becomes an in-world founding or reform project.
- Resources, authority, recruitment, consent, law, and NPC reactions determine
  whether the idea becomes operational.

Idea Mode must not be used as a shortcut around world causality.

### Sandbox Editor

The Sandbox Editor is non-diegetic. It is a structured save editor, not a
natural-language game mode.

- It does not advance world time.
- It can edit save-local actors, locations, relationships, resources, events,
  schedules, activities, and mechanics.
- It shows a structured diff before commit.
- Edits are atomic, validated, undoable, and associated with a save snapshot.
- It may not modify application source, database schema, audit policy, runtime
  capabilities, or the base save format.

Natural language may later assist form filling, but it is not the primary
editor interaction.

## New Game Flow

The player starts inside the fixed contemporary world by describing a
university-student identity.

```text
identity prompt
-> structured character draft
-> review and selective reroll/edit
-> confirmation
-> canonical save creation
```

Character draft fields have provenance:

- `user_locked`: explicitly supplied by the player and preserved across rolls.
- `generated`: proposed by the system and independently editable or rerollable.
- `derived`: calculated from confirmed fields and world rules.

The system may fill in family background, major, academic year, housing,
schedule, initial relationships, resources, traits, and starting skills. It may
not silently contradict player-locked facts.

No canonical world or avatar is committed until the player confirms the draft.

## Player Action Loop

The target action loop is:

```text
player-visible scene projection
-> natural-language input
-> structured ActionPlan
-> infer low-impact missing details
-> check feasibility and material ambiguity
-> execute Activity steps
-> pause for meaningful interaction when needed
-> resolve uncertain steps
-> audit and commit patches
-> record events and promises
-> tick relevant NPCs and local systems
-> return narrative plus structured results
```

### Action Planning

An `ActionPlan` may contain:

- The player's immediate action.
- The intended outcome.
- Target actors, objects, and locations.
- Approach and tone.
- Required travel.
- Expected duration.
- Resource use.
- Ordered substeps.
- Stop conditions and decision points.

Missing details follow this policy:

- Infer a reversible, low-cost default when context is sufficient.
- Begin the reversible portion of a multi-stage action when later detail can be
  chosen after observation.
- Ask one focused question when plausible interpretations have materially
  different outcomes.
- Confirm irreversible, high-cost, or long-duration commitments.
- Explain an in-world blocker and expose nearby alternatives when an action is
  impossible.

### Activities

Actions that take time or contain multiple steps become `Activity` records.
Activities may be ongoing, interruptible, paused for a decision, completed, or
cancelled.

Examples include travel, exercise, studying, a work shift, organizing an
event, founding an organization, and moving home.

A compound request should execute until it reaches new material information,
a failed precondition, an irreversible branch, or a required player response.

### Pending Interaction

An action may enter `pending_interaction` when an NPC asks a meaningful
question or a scene creates a consequential decision.

The player's response may contain:

- A claim.
- A promise or concession.
- A threat or refusal.
- A proposed exchange.
- A tone or social approach.

The response affects resolution modifiers and may create persistent facts,
commitments, and future events. The player must be able to answer, refuse,
leave, or interrupt the activity.

## Resolution Checks

Routine actions do not require a roll. A check is created only when:

- The result is uncertain.
- Success and failure both produce meaningful states.
- Relevant actor ability or context can affect the result.

The initial resolution engine should support a tunable dice formula, actor
attributes and skills, contextual modifiers, opposed NPC factors, difficulty,
and degrees of outcome.

The default design direction is a curved distribution such as `2d6` rather
than applying a flat `d20` roll to routine life. The exact balance remains a
playtest concern, not a storage contract.

Every committed check records:

- Dice result.
- Difficulty.
- Modifiers and their reasons.
- Random source metadata.
- Outcome degree.
- Resulting patch and event IDs.

The normal UI shows the outcome and important positive or negative factors.
Exact arithmetic is available in an expanded view.

## Time And Simulation

The world is turn-based and pauses between player inputs.

Canonical time uses day plus minute-of-day. Labels such as morning, afternoon,
evening, and night are derived presentation values.

Actions infer duration from travel, activity type, approach, and interruptions.
An action may cross hours or days. Crossing midnight runs daily settlement.

Simulation is tiered:

- Scene NPCs react immediately.
- Important connected NPCs maintain schedules, goals, memories, and current
  activities.
- Other persistent NPCs receive lightweight catch-up during settlement.
- Unnamed background populations are aggregated until promoted by interaction.

Directly caused emergencies happen immediately. Daily settlement handles
background schedules, needs, school performance, lightweight finances,
relationship maintenance, NPC plans, summaries, and queued world events.

## First-Version Life Systems

The first playable version includes:

- Minute-level time, travel, schedules, and multi-step activities.
- Energy, hunger, stress, and mood.
- Skills and resolution modifiers.
- Relationships, dialogue consequences, promises, and event memory.
- University classes, attendance, coursework, and academic performance.
- Lightweight money, costs, and income.
- One generic organization framework usable from Idea Mode.

Housing customization, a full inventory simulation, disease, broad reputation
networks, family control, many professions, and macroeconomics are deferred.

## Knowledge And View Boundaries

The normal game UI uses the avatar's knowledge, not raw canonical state.

- Time, money, owned items, and schedules may be exact.
- The avatar's condition, mood, and skills must be legible enough for planning.
- NPC attitudes and emotions are normally qualitative.
- Hidden motives, facts, and world pressures require observation or discovery.
- Debug views and the Sandbox Editor may inspect canonical state.

The backend must expose separate player, debug, and editor projections. The
frontend must not filter secrets from an unrestricted `WorldState` response.

## Save And Retry Model

Free manual save, quick save, load, and retry are part of the default
experience. Ironman behavior may exist later as an optional mode.

A save snapshot includes:

- Canonical world state.
- Event and patch cursors.
- Current time and active activities.
- Pending interactions.
- Active mechanic specifications and versions.
- Save-local mechanic state.
- Scheduled work.

Loading a pre-check save may produce a new result and creates a new save branch.
Auditability means committed history is explainable; it does not force a loaded
branch to repeat an abandoned roll.

Snapshots may only be created at safe transaction boundaries, not during
partial mechanic execution.

## Frontend Information Architecture

The first client targets desktop web browsers and uses React, TypeScript, and
Vite. FastAPI remains the backend. REST handles commands and queries; SSE may
stream model-backed planning, generation, and resolution progress. WebSockets
and Next.js are not required for the first version.

Character creation is a dedicated flow. The main game uses three information
regions:

- Left: avatar and global status such as time, energy, mood, money, and current
  activity.
- Center: current scene, structured observations, narrative, visible actors and
  objects, suggested interactions, and natural-language input.
- Right: relationships, per-person event history, schedule, organizations,
  projects, and contextual tools.

Suggested interactions are discoverability aids, not an action whitelist.

Action Mode and Idea Mode share the main composer through an explicit segmented
mode control. The Sandbox Editor is a separate full-screen workspace with an
entity tree, structured forms, validation, diff preview, and history.

## Deferred Work

The following are explicitly outside the first playable scope:

- Natural-language world generation.
- Multiple world genres.
- Arbitrary starting professions.
- Multiple controllable household members.
- Real-time simulation while the player is absent.
- Mobile-first layout.
- Multiplayer and authentication.
- PostgreSQL and vector retrieval.
- General-purpose generated scripting.
- AI-written application source code.
- Large-scale autonomous NPC populations.

These items require evidence from the fixed-world life loop before they enter a
development milestone.
