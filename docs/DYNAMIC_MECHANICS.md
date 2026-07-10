# Dynamic Mechanics And Save-Local Systems

Status: approved design direction. The exact `MechanicSpec` schema is delivered
by the roadmap after the fixed-world life loop is stable.

## Purpose

GenWorld should be able to model a persistent player idea that the base game
does not already understand.

The distinguishing promise is:

> When an action opens a genuinely new life direction, the current save can
> gain a bounded system that continues to run, can be reformed, and remains
> auditable.

This does not mean that every unusual sentence creates source code. It does not
allow a language model to modify the application, bypass NPC agency, create
resources without a source, or rewrite history.

## Resolution Ladder

Every proposed action or idea is handled at the lowest sufficient level:

```text
existing affordance
-> composition of existing rules
-> generic activity or project
-> instance of a generic domain framework
-> save-local MechanicSpec
```

Examples:

- Doing push-ups uses an existing exercise activity.
- Starting a study group uses a generic project and organization.
- Running a fourteen-day challenge uses an organization plus a scheduled
  challenge configuration.
- Creating a novel member-credit voting economy may require a save-local
  mechanic.

A new mechanic is justified only when the idea introduces one or more of:

- New persistent state.
- New repeated actions.
- A multi-stage lifecycle.
- Scheduled or daily settlement behavior.
- A new resource or progression model.
- Rules that existing frameworks cannot express without distortion.

This escalation policy prevents save files from accumulating a separate module
for every one-off action.

## Idea Mode Lifecycle

Idea Mode is a proposal workflow inside the fiction.

```text
natural-language idea
-> structured draft
-> assumptions and unresolved decisions
-> player revision or confirmation
-> in-world founding or reform project
-> resource, authority, consent, and feasibility checks
-> active institution or mechanic
```

Drafting and revising do not advance world time. Confirmation does not make the
proposal real by itself. It creates the next in-world work needed to realize
the idea.

An idea draft should expose:

- Intended purpose.
- Founding actor and authority.
- Required resources and prerequisites.
- Participants and affected actors.
- Proposed rules and benefits.
- Recurring activities and schedules.
- Governance and amendment procedure.
- Public claims and expected obligations.
- Known risks and unresolved assumptions.

## Generic Organization Framework

Organizations are a core domain framework, not generated code per organization.

The framework must support:

- Identity, purpose, doctrine, and public description.
- Founder, roles, members, applicants, and former members.
- Governance and decision authority.
- Policies and member expectations.
- Resources, income, costs, and property.
- Activities and schedules.
- Benefits, promises, contracts, and obligations.
- Reputation and relationships.
- Founding, active, suspended, split, merged, and dissolved states.
- Reform proposals and versioned rules.

### Doctrine, Policy, Promise, And Behavior

These concepts are intentionally separate:

- Doctrine states what the organization claims to value.
- Policy constrains official organization behavior.
- Promise creates an obligation to another actor.
- Member behavior remains an NPC decision.

A vegetarian doctrine does not make every member vegetarian. Members may agree,
comply reluctantly, violate the doctrine privately, protest, or leave. The
organization may influence behavior through relationships, incentives,
sanctions, and reputation, but it may not directly control minds.

### Governance

The right to reform an organization comes from its governance state, not from
the player's access to Idea Mode.

A founder-led organization may allow unilateral changes. A council-led
organization may require a vote. Existing contracts, public claims, legal
requirements, and member expectations still produce consequences after a
valid reform.

## Dialogue As Persistent Action

Dialogue inside an activity may create more than a roll modifier.

A player response can be parsed into:

- Content and factual claims.
- Tone and social approach.
- Promises or concessions.
- Threats, refusals, and conditions.
- Proposed exchanges.

Tone and relevance affect the immediate check. Claims are compared against
known facts and available evidence. Promises create persistent obligations with
beneficiaries, deadlines, expected value, and fulfillment state.

For example, promising free vegetables during recruitment may improve immediate
interest while creating a future supply obligation. Failure to fulfill it can
damage trust and create a public fact about the organization.

NPC membership must consider alignment, trust, perceived benefit, social proof,
cost, risk, relationships, and the resolution check. A successful roll cannot
override a hard refusal or force belief.

## Reform And Historical Continuity

A reform creates a new rule version. It does not edit the past.

When a player proposes a major reversal, the system identifies:

- Rules being added, removed, or changed.
- Scheduled activities that may be cancelled.
- Members and partners whose expectations are affected.
- Outstanding promises and contracts.
- Resources already spent.
- Public facts and reputation created by the old rules.
- Governance steps required for approval.

Future schedules may be cancelled. Completed events, NPC memories, public
claims, paid costs, and outstanding obligations remain canonical.

Members may accept the reform, leave, resist, or form a splinter organization.
Changing organizational doctrine does not rewrite individual beliefs.

## MechanicSpec As The Canonical Format

The permanent save format for a dynamic rule is a versioned, structured
`MechanicSpec`, not a general-purpose source file.

A specification is expected to contain:

- Mechanic ID, version, status, and provenance.
- Host API version and specification schema version.
- Requested capabilities.
- Private state schema and initial state.
- Registered affordances and activities.
- Triggers and conditions.
- Resolution-check requests.
- State-machine transitions.
- Scheduled and daily work.
- Proposed patch templates.
- Event templates.
- Limits and invariants.
- Tests and example scenarios.
- Migration and disable behavior.
- Content hash.

Conditions and formulas use a parsed safe expression representation. They must
never use Python `eval` or an equivalent unrestricted evaluator.

The specification remains editable and migratable across engine versions. The
save also retains the original player intent and human-readable rule summary so
that a future engine can explain or rebuild the mechanic.

## Runtime Contract

A mechanic receives bounded inputs and returns proposals:

```text
read-only context snapshot
+ mechanic-private state
+ host-provided random/check service
+ trigger or player command
-> check requests
+ patch proposals
+ events
+ scheduled follow-up work
```

A mechanic may not mutate canonical state directly. Patch proposals pass
through the same audit and ledger boundary as built-in systems.

Capabilities are explicit and minimal. A mechanic may read or propose changes
only within granted domains. Private state is namespaced by mechanic ID.

The host enforces:

- No filesystem, network, process, environment, or direct database access.
- No hidden source of wall-clock time or randomness.
- Execution, memory, output, and scheduling budgets.
- Patch count and effect-size limits.
- Protected core paths.
- Isolation between mechanics.
- Transactional execution and failure rollback.

Containment and state integrity can be enforced. Fun, balance, and semantic
correctness cannot be guaranteed and require tests, simulation, limits, and
player-visible rollback.

## Module Lifecycle

A save-local mechanic follows an explicit lifecycle:

```text
draft
-> validating
-> simulated
-> active
-> suspended or superseded
-> archived
```

Activation requires:

- Schema validation.
- Capability review.
- Static invariant checks.
- Generated and engine-owned tests.
- Execution against a cloned world snapshot.
- Successful rollback testing.
- A human-readable summary of effects.

A failure during validation quarantines the draft without changing the save.
A runtime failure suspends the mechanic, rolls back the transition, and records
an inspectable error event.

## Versioning And Save Compatibility

Each active mechanic is pinned to a specification version and host API version.
A reform creates a successor version and migrates private state through a
validated transition.

Old versions remain available to explain historical events. A save snapshot
contains active specifications, hashes, private state, and scheduled work.

Engine upgrades must either:

- Continue supporting the mechanic's host API version.
- Apply an explicit migration.
- Suspend the mechanic with a recoverable explanation.

The engine must never silently reinterpret old mechanic behavior.

## Future Script Runtimes

The first version executes `MechanicSpec` through a rule interpreter and safe
expressions. It does not execute generated Python, JavaScript, or Lua.

The runtime boundary is intentionally pluggable. If real mechanics demonstrate
that the structured representation is insufficient, a later research gate may
add a general script runtime.

Lua is the preferred first candidate for game-oriented embedded scripting.
QuickJS is a secondary candidate because model-generated JavaScript and JSON
interoperation are strong. WebAssembly is a possible later isolation target.
Python is not a candidate for executing untrusted save-local code in the
backend process.

A future script remains subordinate to the same capability, patch, budget,
version, test, and save boundaries. General scripting may expand expressiveness;
it may not expand authority.

## Sandbox Editor Relationship

The Sandbox Editor may inspect, create, revise, suspend, and archive save-local
mechanics through structured forms. It may also edit mechanic-private state when
the proposed state validates against the specification.

Editor changes:

- Do not require in-world authority.
- Do not advance time.
- Produce a diff and an editor event.
- Create a snapshot before commit.
- Remain undoable.
- Cannot modify the mechanic runtime's security boundary.

This is intentionally separate from Idea Mode, where organization founding and
reform remain subject to world causality.

## Illustrative Organization Flow

An avatar proposes a vegetarian environmental religion in Idea Mode.

1. The organization framework creates a draft doctrine, governance model,
   activities, and unresolved funding questions.
2. Confirmation creates an in-world founding project.
3. The avatar recruits in a supermarket.
4. An NPC asks whether membership includes free vegetables.
5. A sincere promise improves the immediate social check and creates a supply
   obligation.
6. Fulfillment or failure affects trust, reputation, and future membership.
7. A later proposal reverses the doctrine and cancels future activities.
8. Governance determines whether the reform passes.
9. Members react individually; some may leave or form a splinter group.
10. Old events, public claims, and unfulfilled obligations remain in history.

The organization uses the generic framework. A new save-local mechanic is only
needed if the player adds behavior the framework cannot express, such as a
novel member-credit economy with periodic allocation and voting rules.

## Acceptance Principles

A dynamic mechanic is acceptable only when:

- Its purpose and effects are understandable without reading source code.
- It survives save, load, engine restart, and rule-version migration.
- It cannot mutate state outside its declared capabilities.
- It cannot erase committed history.
- NPC reactions remain decisions, not mechanic-assigned beliefs.
- Promises and contracts remain enforceable across reforms.
- Failed execution leaves the prior canonical state intact.
- The player can inspect, suspend, roll back, and archive it.
- Another save is unaffected.
