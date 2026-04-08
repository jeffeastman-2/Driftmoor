"""Tests for the GameClock and SceneClock — global time synchronisation.

The clock system ensures multi-scene games stay time-consistent:
- Each scene has a time_cursor (seconds elapsed) and a heartbeat
- Exploration heartbeat: configurable (default 60s)
- Combat heartbeat: 6s (one D&D round)
- The orchestrator always advances the scene furthest behind in time
- Combat scenes naturally "pause" exploration scenes by advancing slowly
"""

import pytest

from engine.game_clock import GameClock, SceneClock, TimeScale


# =========================================================================
# TimeScale
# =========================================================================

class TestTimeScale:
    def test_exploration_heartbeat(self):
        assert TimeScale.EXPLORATION == 60.0

    def test_combat_heartbeat(self):
        assert TimeScale.COMBAT == 6.0


# =========================================================================
# SceneClock
# =========================================================================

class TestSceneClock:
    def test_create_default(self):
        sc = SceneClock(scene_id="fey_glade")
        assert sc.scene_id == "fey_glade"
        assert sc.time_cursor == 0.0
        assert sc.heartbeat == TimeScale.EXPLORATION

    def test_create_at_specific_time(self):
        sc = SceneClock(scene_id="market", time_cursor=300.0)
        assert sc.time_cursor == 300.0

    def test_tick_advances_cursor(self):
        sc = SceneClock(scene_id="fey_glade")
        sc.tick()
        assert sc.time_cursor == 60.0

    def test_tick_twice(self):
        sc = SceneClock(scene_id="fey_glade")
        sc.tick()
        sc.tick()
        assert sc.time_cursor == 120.0

    def test_enter_combat(self):
        sc = SceneClock(scene_id="fey_glade")
        sc.enter_combat()
        assert sc.heartbeat == TimeScale.COMBAT

    def test_exit_combat(self):
        sc = SceneClock(scene_id="fey_glade")
        sc.enter_combat()
        sc.exit_combat()
        assert sc.heartbeat == TimeScale.EXPLORATION

    def test_combat_tick(self):
        sc = SceneClock(scene_id="fey_glade")
        sc.enter_combat()
        sc.tick()
        assert sc.time_cursor == 6.0

    def test_custom_exploration_heartbeat(self):
        sc = SceneClock(scene_id="market", heartbeat=30.0)
        sc.tick()
        assert sc.time_cursor == 30.0

    def test_exit_combat_restores_previous_heartbeat(self):
        sc = SceneClock(scene_id="market", heartbeat=30.0)
        sc.enter_combat()
        assert sc.heartbeat == 6.0
        sc.exit_combat()
        assert sc.heartbeat == 30.0

    def test_in_combat_property(self):
        sc = SceneClock(scene_id="fey_glade")
        assert sc.in_combat is False
        sc.enter_combat()
        assert sc.in_combat is True
        sc.exit_combat()
        assert sc.in_combat is False


# =========================================================================
# GameClock
# =========================================================================

class TestGameClock:
    def test_create_empty(self):
        gc = GameClock()
        assert gc.scenes == {}

    def test_add_scene(self):
        gc = GameClock()
        gc.add_scene("fey_glade")
        assert "fey_glade" in gc.scenes
        assert gc.scenes["fey_glade"].time_cursor == 0.0

    def test_add_scene_at_time(self):
        gc = GameClock()
        gc.add_scene("market", time_cursor=300.0)
        assert gc.scenes["market"].time_cursor == 300.0

    def test_add_scene_custom_heartbeat(self):
        gc = GameClock()
        gc.add_scene("tavern", heartbeat=120.0)
        assert gc.scenes["tavern"].heartbeat == 120.0

    def test_next_scene_single(self):
        gc = GameClock()
        gc.add_scene("fey_glade")
        assert gc.next_scene() == "fey_glade"

    def test_next_scene_picks_furthest_behind(self):
        gc = GameClock()
        gc.add_scene("fey_glade")
        gc.add_scene("market")
        gc.scenes["market"].time_cursor = 60.0
        assert gc.next_scene() == "fey_glade"

    def test_next_scene_tie_is_deterministic(self):
        gc = GameClock()
        gc.add_scene("alpha")
        gc.add_scene("beta")
        # Both at 0.0 — should pick consistently
        result = gc.next_scene()
        assert result in ("alpha", "beta")

    def test_tick_scene(self):
        gc = GameClock()
        gc.add_scene("fey_glade")
        gc.tick("fey_glade")
        assert gc.scenes["fey_glade"].time_cursor == 60.0

    def test_combat_scene_many_ticks_before_exploration(self):
        """Combat scene needs 10 ticks to catch up to one exploration tick."""
        gc = GameClock()
        gc.add_scene("fey_glade")
        gc.add_scene("market")

        # Market does one exploration turn
        gc.tick("market")
        assert gc.scenes["market"].time_cursor == 60.0

        # Fey glade enters combat
        gc.scenes["fey_glade"].enter_combat()

        # Fey glade should be next for 10 rounds
        for i in range(10):
            assert gc.next_scene() == "fey_glade"
            gc.tick("fey_glade")

        # After 10 combat ticks, fey_glade is at 60.0
        assert gc.scenes["fey_glade"].time_cursor == 60.0

        # Now they're tied — either could be next
        next_id = gc.next_scene()
        assert next_id in ("fey_glade", "market")

    def test_global_time(self):
        gc = GameClock()
        gc.add_scene("fey_glade")
        gc.add_scene("market")
        assert gc.global_time == 0.0
        gc.tick("market")
        # Global time is the minimum — fey_glade is still at 0
        assert gc.global_time == 0.0
        gc.tick("fey_glade")
        assert gc.global_time == 60.0

    def test_remove_scene(self):
        gc = GameClock()
        gc.add_scene("fey_glade")
        gc.add_scene("market")
        gc.remove_scene("market")
        assert "market" not in gc.scenes
        assert gc.next_scene() == "fey_glade"

    def test_next_scene_empty_raises(self):
        gc = GameClock()
        with pytest.raises(ValueError):
            gc.next_scene()

    def test_enter_combat_via_gameclock(self):
        gc = GameClock()
        gc.add_scene("fey_glade")
        gc.enter_combat("fey_glade")
        assert gc.scenes["fey_glade"].in_combat is True
        assert gc.scenes["fey_glade"].heartbeat == TimeScale.COMBAT

    def test_exit_combat_via_gameclock(self):
        gc = GameClock()
        gc.add_scene("fey_glade")
        gc.enter_combat("fey_glade")
        gc.exit_combat("fey_glade")
        assert gc.scenes["fey_glade"].in_combat is False
