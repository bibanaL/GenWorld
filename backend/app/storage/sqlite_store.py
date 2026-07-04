from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from app.engine.auditor import PatchAuditError, audit_patch_operations
from app.engine.patches import PatchApplyError, apply_patch_operations
from app.schemas.patch import PatchOperation, PermissionLevel
from app.schemas.state import WorldState


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class StatePatchRejected(ValueError):
    pass


class SQLiteLedger:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def init_schema(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS worlds (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    premise TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    world_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS state_patches (
                    id TEXT PRIMARY KEY,
                    world_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    patch_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    applied_at TEXT,
                    FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_events_world_created
                    ON events(world_id, created_at);

                CREATE INDEX IF NOT EXISTS idx_state_patches_world_created
                    ON state_patches(world_id, created_at);
                """
            )

    def create_world(
        self,
        *,
        name: str,
        premise: str,
        seed: int | None,
        initial_state: WorldState | dict[str, Any] | None,
    ) -> dict[str, Any]:
        world_id = str(uuid.uuid4())
        now = utc_now()
        state = self._prepare_world_state(
            premise=premise,
            seed=seed,
            initial_state=initial_state,
        )

        with self._connect() as con:
            con.execute(
                """
                INSERT INTO worlds (id, name, premise, state_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (world_id, name, premise, json.dumps(state, ensure_ascii=False), now, now),
            )
            self._insert_event(
                con,
                world_id=world_id,
                type_="world_created",
                summary=f"World created: {name}",
                payload={"premise": premise, "seed": seed},
                created_at=now,
            )

        world = self.get_world(world_id)
        if world is None:
            raise RuntimeError("World was created but could not be loaded.")
        return world

    def list_worlds(self) -> list[dict[str, Any]]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT id, name, premise, created_at, updated_at
                FROM worlds
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_world(self, world_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute(
                """
                SELECT id, name, premise, state_json, created_at, updated_at
                FROM worlds
                WHERE id = ?
                """,
                (world_id,),
            ).fetchone()

        if row is None:
            return None

        result = dict(row)
        result["state"] = json.loads(result.pop("state_json"))
        return result

    def append_event(
        self,
        *,
        world_id: str,
        type_: str,
        summary: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        now = utc_now()
        with self._connect() as con:
            if not self._world_exists(con, world_id):
                raise KeyError(world_id)
            event = self._insert_event(
                con,
                world_id=world_id,
                type_=type_,
                summary=summary,
                payload=payload,
                created_at=now,
            )
        return event

    def list_events(self, world_id: str) -> list[dict[str, Any]]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT id, world_id, type, summary, payload_json, created_at
                FROM events
                WHERE world_id = ?
                ORDER BY created_at ASC
                """,
                (world_id,),
            ).fetchall()
        events = []
        for row in rows:
            event = dict(row)
            event["payload"] = json.loads(event.pop("payload_json"))
            events.append(event)
        return events

    def apply_state_patch(
        self,
        *,
        world_id: str,
        reason: str,
        source_agent: str,
        permission_level: PermissionLevel,
        operations: list[PatchOperation],
    ) -> dict[str, Any]:
        patch_id = str(uuid.uuid4())
        created_at = utc_now()
        applied_at: str | None = None
        status = "applied"
        error: str | None = None

        patch_payload = {
            "source_agent": source_agent,
            "permission_level": permission_level,
            "operations": [operation.model_dump(mode="json") for operation in operations],
            "error": None,
        }

        with self._connect() as con:
            row = con.execute(
                """
                SELECT state_json
                FROM worlds
                WHERE id = ?
                """,
                (world_id,),
            ).fetchone()
            if row is None:
                raise KeyError(world_id)

            state = json.loads(row["state_json"])

            try:
                audit_patch_operations(operations, permission_level)
                next_state = apply_patch_operations(state, operations)
            except (PatchAuditError, PatchApplyError) as exc:
                status = "rejected"
                error = str(exc)
                patch_payload["error"] = error
            else:
                applied_at = utc_now()
                con.execute(
                    """
                    UPDATE worlds
                    SET state_json = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        json.dumps(next_state, ensure_ascii=False),
                        applied_at,
                        world_id,
                    ),
                )
                self._insert_event(
                    con,
                    world_id=world_id,
                    type_="state_patch_applied",
                    summary=reason,
                    payload={"patch_id": patch_id, "operations": patch_payload["operations"]},
                    created_at=applied_at,
                )

            self._insert_state_patch(
                con,
                patch_id=patch_id,
                world_id=world_id,
                reason=reason,
                patch_payload=patch_payload,
                status=status,
                created_at=created_at,
                applied_at=applied_at,
            )

        record = {
            "id": patch_id,
            "world_id": world_id,
            "reason": reason,
            "source_agent": source_agent,
            "permission_level": permission_level,
            "operations": operations,
            "status": status,
            "error": error,
            "created_at": created_at,
            "applied_at": applied_at,
        }
        if error is not None:
            raise StatePatchRejected(error)
        return record

    def list_state_patches(self, world_id: str) -> list[dict[str, Any]]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT id, world_id, reason, patch_json, status, created_at, applied_at
                FROM state_patches
                WHERE world_id = ?
                ORDER BY created_at ASC
                """,
                (world_id,),
            ).fetchall()

        patches = []
        for row in rows:
            patch = dict(row)
            payload = json.loads(patch.pop("patch_json"))
            patch["source_agent"] = payload["source_agent"]
            patch["permission_level"] = payload["permission_level"]
            patch["operations"] = payload["operations"]
            patch["error"] = payload.get("error")
            patches.append(patch)
        return patches

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.database_path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _insert_event(
        self,
        con: sqlite3.Connection,
        *,
        world_id: str,
        type_: str,
        summary: str,
        payload: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        event_id = str(uuid.uuid4())
        con.execute(
            """
            INSERT INTO events (id, world_id, type, summary, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                world_id,
                type_,
                summary,
                json.dumps(payload, ensure_ascii=False),
                created_at,
            ),
        )
        return {
            "id": event_id,
            "world_id": world_id,
            "type": type_,
            "summary": summary,
            "payload": payload,
            "created_at": created_at,
        }

    def _insert_state_patch(
        self,
        con: sqlite3.Connection,
        *,
        patch_id: str,
        world_id: str,
        reason: str,
        patch_payload: dict[str, Any],
        status: str,
        created_at: str,
        applied_at: str | None,
    ) -> None:
        con.execute(
            """
            INSERT INTO state_patches
                (id, world_id, reason, patch_json, status, created_at, applied_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patch_id,
                world_id,
                reason,
                json.dumps(patch_payload, ensure_ascii=False),
                status,
                created_at,
                applied_at,
            ),
        )

    def _world_exists(self, con: sqlite3.Connection, world_id: str) -> bool:
        row = con.execute("SELECT 1 FROM worlds WHERE id = ?", (world_id,)).fetchone()
        return row is not None

    def _prepare_world_state(
        self,
        *,
        premise: str,
        seed: int | None,
        initial_state: WorldState | dict[str, Any] | None,
    ) -> dict[str, Any]:
        if initial_state is None:
            state = WorldState(premise=premise, seed=seed)
            return state.model_dump(mode="json")

        state = WorldState.model_validate(initial_state)
        if not state.premise:
            state.premise = premise
        if state.seed is None:
            state.seed = seed
        return state.model_dump(mode="json")
