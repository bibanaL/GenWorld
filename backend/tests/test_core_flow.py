import os
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
TEST_DB_PATH = Path(tempfile.gettempdir()) / f"genworld_test_{os.getpid()}.db"

sys.path.insert(0, str(BACKEND_ROOT))
os.environ["GENWORLD_DATABASE_PATH"] = str(TEST_DB_PATH)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


class CoreFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

    def test_generate_world_records_seed_event(self) -> None:
        world = self._generate_world(seed=501)

        self.assertEqual(len(world["state"]["factions"]), 3)
        self.assertEqual(len(world["state"]["locations"]), 7)
        self.assertEqual(len(world["state"]["entities"]), 8)
        self.assertEqual(len(world["state"]["clocks"]), 4)

        events = self.client.get(f"/worlds/{world['id']}/events").json()
        self.assertEqual(["world_created", "world_seed_generated"], [event["type"] for event in events])

    def test_player_action_commits_patch_and_event(self) -> None:
        world = self._generate_world(seed=502)

        response = self.client.post(
            f"/worlds/{world['id']}/actions",
            json={
                "text": "我调查 Old Station 附近的异常压力。",
                "actor_id": "player",
                "advance_time": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["intent"]["action_type"], "investigate")
        self.assertEqual(body["patch"]["status"], "applied")

        state = self.client.get(f"/worlds/{world['id']}").json()["state"]
        self.assertEqual(state["time"]["slot"], "afternoon")
        self.assertGreaterEqual(state["player"]["condition"]["fatigue"], 0)
        self.assertEqual(len(state["facts"]["player_known"]), 2)

        events = self.client.get(f"/worlds/{world['id']}/events").json()
        self.assertIn("player_action_resolved", [event["type"] for event in events])

    def test_player_action_can_trigger_queued_clock_event(self) -> None:
        world = self._generate_world(seed=507)
        queued_event = world["state"]["event_queue"][0]
        clock_id = queued_event["trigger"]["clock_id"]

        self._apply_patch(
            world_id=world["id"],
            operations=[{"op": "set", "path": f"/clocks/{clock_id}/progress", "value": 74}],
        )

        response = self.client.post(
            f"/worlds/{world['id']}/actions",
            json={"text": "I wait and observe.", "advance_time": True},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["intent"]["action_type"], "wait")
        self.assertEqual(len(body["triggered_events"]), 1)
        self.assertEqual(body["triggered_events"][0]["type"], "queued_event_triggered")

        state = self.client.get(f"/worlds/{world['id']}").json()["state"]
        self.assertNotIn(queued_event["id"], [event["id"] for event in state["event_queue"]])

    def test_world_advance_uses_patch_ledger(self) -> None:
        world = self._generate_world(seed=503)
        first_clock_before = next(iter(world["state"]["clocks"].values()))["progress"]

        response = self.client.post(
            f"/worlds/{world['id']}/advance",
            json={
                "reason": "Regression advance.",
                "risk_level": "medium",
                "clock_limit": 2,
                "tick_faction_plans": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["patch"]["status"], "applied")

        state = self.client.get(f"/worlds/{world['id']}").json()["state"]
        first_clock_after = next(iter(state["clocks"].values()))["progress"]
        self.assertEqual(state["time"]["slot"], "afternoon")
        self.assertEqual(first_clock_after - first_clock_before, 4)

    def test_faction_plan_tick_advances_plan_and_target_clock(self) -> None:
        world = self._generate_world(seed=508)
        faction_id, faction = next(iter(world["state"]["factions"].items()))
        plan_id, plan = next(iter(faction["plans"].items()))
        target_clock_id = plan["target_clock_id"]
        plan_progress_before = plan["progress"]
        clock_progress_before = world["state"]["clocks"][target_clock_id]["progress"]

        response = self.client.post(
            f"/worlds/{world['id']}/advance",
            json={
                "reason": "Tick faction plan only.",
                "risk_level": "low",
                "advance_time": False,
                "clock_limit": 0,
                "tick_faction_plans": True,
                "faction_plan_limit": 1,
            },
        )

        self.assertEqual(response.status_code, 200)

        state = self.client.get(f"/worlds/{world['id']}").json()["state"]
        plan_after = state["factions"][faction_id]["plans"][plan_id]
        clock_after = state["clocks"][target_clock_id]
        self.assertEqual(plan_after["progress"] - plan_progress_before, 2)
        self.assertEqual(clock_after["progress"] - clock_progress_before, 1)
        self.assertEqual(state["time"]["slot"], "morning")

    def test_completed_faction_plan_creates_delayed_followup_event(self) -> None:
        world = self._generate_world(seed=509)
        faction_id, faction = next(iter(world["state"]["factions"].items()))
        plan_id, _ = next(iter(faction["plans"].items()))
        original_queue_ids = {event["id"] for event in world["state"]["event_queue"]}

        self._apply_patch(
            world_id=world["id"],
            operations=[
                {
                    "op": "set",
                    "path": f"/factions/{faction_id}/plans/{plan_id}/progress",
                    "value": 99,
                },
                {
                    "op": "set",
                    "path": f"/factions/{faction_id}/plans/{plan_id}/priority",
                    "value": 100,
                },
            ],
        )

        response = self.client.post(
            f"/worlds/{world['id']}/advance",
            json={
                "reason": "Complete faction plan.",
                "advance_time": False,
                "clock_limit": 0,
                "tick_faction_plans": True,
                "faction_plan_limit": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["triggered_events"], [])

        state = self.client.get(f"/worlds/{world['id']}").json()["state"]
        plan = state["factions"][faction_id]["plans"][plan_id]
        new_queue_items = [
            event for event in state["event_queue"] if event["id"] not in original_queue_ids
        ]
        self.assertEqual(plan["status"], "completed")
        self.assertEqual(len(new_queue_items), 1)
        self.assertEqual(new_queue_items[0]["trigger"]["type"], "plan_completed")
        self.assertEqual(new_queue_items[0]["earliest_day"], state["time"]["day"] + 1)

        trigger_response = None
        for _ in range(4):
            trigger_response = self.client.post(
                f"/worlds/{world['id']}/advance",
                json={
                    "reason": "Move toward completed plan follow-up.",
                    "advance_time": True,
                    "clock_limit": 0,
                    "tick_faction_plans": False,
                },
            )

        assert trigger_response is not None
        self.assertEqual(trigger_response.status_code, 200)
        triggered_events = trigger_response.json()["triggered_events"]
        self.assertEqual(len(triggered_events), 1)
        self.assertEqual(triggered_events[0]["payload"]["trigger"]["type"], "plan_completed")
        self.assertFalse(triggered_events[0]["payload"]["overdue"])

    def test_daily_settlement_moves_to_next_morning(self) -> None:
        world = self._generate_world(seed=510)

        self._apply_patch(
            world_id=world["id"],
            operations=[
                {"op": "set", "path": "/time/day", "value": 3},
                {"op": "set", "path": "/time/slot", "value": "night"},
                {"op": "set", "path": "/time/slot_index", "value": 3},
            ],
        )

        response = self.client.post(
            f"/worlds/{world['id']}/settle-day",
            json={
                "reason": "Regression daily settlement.",
                "tick_faction_plans": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["settled_day"], 3)
        self.assertEqual(body["new_day"], 4)
        self.assertEqual(body["patch"]["status"], "applied")

        state = self.client.get(f"/worlds/{world['id']}").json()["state"]
        self.assertEqual(state["time"]["day"], 4)
        self.assertEqual(state["time"]["slot"], "morning")
        self.assertEqual(state["time"]["slot_index"], 0)

        events = self.client.get(f"/worlds/{world['id']}/events").json()
        self.assertIn("daily_settlement", [event["type"] for event in events])

    def test_daily_settlement_can_trigger_completed_plan_followup(self) -> None:
        world = self._generate_world(seed=511)
        faction_id, faction = next(iter(world["state"]["factions"].items()))
        plan_id, _ = next(iter(faction["plans"].items()))

        self._apply_patch(
            world_id=world["id"],
            operations=[
                {
                    "op": "set",
                    "path": f"/factions/{faction_id}/plans/{plan_id}/progress",
                    "value": 99,
                },
                {
                    "op": "set",
                    "path": f"/factions/{faction_id}/plans/{plan_id}/priority",
                    "value": 100,
                },
            ],
        )

        response = self.client.post(
            f"/worlds/{world['id']}/settle-day",
            json={
                "reason": "Complete plan during daily settlement.",
                "tick_faction_plans": True,
                "faction_plan_limit": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["new_day"], 2)
        self.assertEqual(len(body["triggered_events"]), 1)
        self.assertEqual(body["triggered_events"][0]["payload"]["trigger"]["type"], "plan_completed")

        state = self.client.get(f"/worlds/{world['id']}").json()["state"]
        self.assertEqual(state["factions"][faction_id]["plans"][plan_id]["status"], "completed")

    def test_world_advance_triggers_queued_clock_event(self) -> None:
        world = self._generate_world(seed=505)
        queued_event = world["state"]["event_queue"][0]
        clock_id = queued_event["trigger"]["clock_id"]

        self._apply_patch(
            world_id=world["id"],
            operations=[{"op": "set", "path": f"/clocks/{clock_id}/progress", "value": 74}],
        )

        response = self.client.post(
            f"/worlds/{world['id']}/advance",
            json={
                "reason": "Trigger queued event.",
                "risk_level": "low",
                "advance_time": False,
                "clock_limit": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["triggered_events"]), 1)
        self.assertEqual(body["triggered_events"][0]["type"], "queued_event_triggered")
        self.assertFalse(body["triggered_events"][0]["payload"]["overdue"])

        state = self.client.get(f"/worlds/{world['id']}").json()["state"]
        self.assertNotIn(queued_event["id"], [event["id"] for event in state["event_queue"]])

    def test_overdue_queued_clock_event_still_triggers(self) -> None:
        world = self._generate_world(seed=506)
        queued_event = world["state"]["event_queue"][0]
        clock_id = queued_event["trigger"]["clock_id"]

        self._apply_patch(
            world_id=world["id"],
            operations=[
                {"op": "set", "path": "/time/day", "value": queued_event["latest_day"] + 1},
                {"op": "set", "path": f"/clocks/{clock_id}/progress", "value": 74},
            ],
        )

        response = self.client.post(
            f"/worlds/{world['id']}/advance",
            json={
                "reason": "Trigger overdue queued event.",
                "risk_level": "low",
                "advance_time": False,
                "clock_limit": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        triggered_event = response.json()["triggered_events"][0]
        self.assertTrue(triggered_event["payload"]["overdue"])
        self.assertEqual(
            triggered_event["payload"]["scheduled_window"]["latest_day"],
            queued_event["latest_day"],
        )

    def test_rejected_patch_is_recorded_without_mutating_state(self) -> None:
        world = self._generate_world(seed=504)

        response = self.client.post(
            f"/worlds/{world['id']}/patches",
            json={
                "reason": "Attempt protected mutation.",
                "source_agent": "test",
                "permission_level": "system",
                "operations": [{"op": "set", "path": "/seed", "value": 999}],
            },
        )

        self.assertEqual(response.status_code, 422)

        state = self.client.get(f"/worlds/{world['id']}").json()["state"]
        self.assertEqual(state["seed"], 504)

        patches = self.client.get(f"/worlds/{world['id']}/patches").json()
        self.assertEqual(patches[-1]["status"], "rejected")

    def _generate_world(self, *, seed: int) -> dict:
        response = self.client.post(
            "/worlds/generate",
            json={
                "name": f"Regression World {seed}",
                "premise": "A city where hidden factions move under public pressure.",
                "seed": seed,
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["world"]

    def _apply_patch(self, *, world_id: str, operations: list[dict]) -> dict:
        response = self.client.post(
            f"/worlds/{world_id}/patches",
            json={
                "reason": "Test setup patch.",
                "source_agent": "test",
                "permission_level": "system",
                "operations": operations,
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()


if __name__ == "__main__":
    unittest.main()
