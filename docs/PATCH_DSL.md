# State Patch DSL

Status: current prototype mutation contract and retained architectural boundary.

Patch-based mutation remains part of the target product. Milestone 1 in
`ROADMAP.md` adds complete post-patch state validation, domain invariants,
atomic transitions, revision checks, and explicit consequence links before the
DSL is trusted by save editing or dynamic mechanics.

The State Patch DSL is the only supported way for agents and engine modules to request world-state changes.

AI agents may propose patches. The auditor validates them. The ledger applies and records them.

## Path Format

Patch paths use JSON Pointer syntax.

Examples:

```text
/player/name
/player/resources/coin
/player/statuses
/clocks/white_heron_investigation/progress
/facts/public
```

The following root paths are currently patchable:

- `/time`
- `/player`
- `/entities`
- `/locations`
- `/factions`
- `/clocks`
- `/facts`
- `/event_queue`

The following paths are protected:

- `/schema_version`
- `/premise`
- `/seed`

## Operations

### `set`

Sets a value at a path. Missing parent objects are created.

```json
{
  "op": "set",
  "path": "/player/name",
  "value": "Courier"
}
```

### `increase`

Increases a numeric value. Missing numeric targets start at `0`.

```json
{
  "op": "increase",
  "path": "/player/resources/coin",
  "value": 3
}
```

### `decrease`

Decreases a numeric value. Missing numeric targets start at `0`.

```json
{
  "op": "decrease",
  "path": "/player/condition/fatigue",
  "value": 1
}
```

### `append`

Appends a value to a list. Missing list targets are created.

```json
{
  "op": "append",
  "path": "/facts/public",
  "value": {
    "id": "fact_player_known_south_market",
    "text": "The player is known in the south market.",
    "visibility": "public",
    "tags": ["reputation"]
  }
}
```

### `remove`

Removes an object key or list item. This is high risk and currently requires `high` or `system` permission.

```json
{
  "op": "remove",
  "path": "/event_queue/0"
}
```

### `add_status`

Adds or replaces a status in a status object. The value must include an `id`.

```json
{
  "op": "add_status",
  "path": "/player/statuses",
  "value": {
    "id": "focused",
    "duration": 2,
    "source": "manual_test"
  }
}
```

### `remove_status`

Removes a status by status id.

```json
{
  "op": "remove_status",
  "path": "/player/statuses",
  "value": "focused"
}
```

## Patch Request

```json
{
  "reason": "Initialize player condition",
  "source_agent": "manual",
  "permission_level": "system",
  "operations": [
    {
      "op": "set",
      "path": "/player/name",
      "value": "Courier"
    }
  ]
}
```

## Audit Behavior

- Empty patch batches are rejected.
- Patch batches with more than 50 operations are rejected.
- Writes outside allowed roots are rejected.
- Writes to protected paths are rejected.
- `increase` and `decrease` require numeric values.
- `add_status` requires an object with a non-empty `id`.
- `remove_status` requires a non-empty status id string.
- Rejected patches are recorded with status `rejected` and do not mutate world state.
