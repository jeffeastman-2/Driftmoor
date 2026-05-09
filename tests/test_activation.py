"""Phase 3b tests: dormancy + activation triggers."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from engine.activation import (
    check_activations,
    initial_dormant_set,
    _door_open_target,
    _zone_entry_target,
)


def _stub_session(faction: str, activation: str = "always", name: str = "stub"):
    return SimpleNamespace(
        character=SimpleNamespace(faction=faction, name=name),
        activation=activation,
        scene_handle=name,
    )


class TestParsing:
    def test_zone_entry(self):
        assert _zone_entry_target("zone_entry:Secret Chamber") == "Secret Chamber"
        assert _zone_entry_target("always") is None

    def test_door_open(self):
        assert _door_open_target("door_open:secret_door") == "secret_door"
        assert _door_open_target("zone_entry:X") is None


class TestInitialDormant:
    def test_always_excluded(self):
        chars = {
            "amara": _stub_session("party", "always"),
            "spider": _stub_session("hostile", "zone_entry:Secret Chamber"),
        }
        assert initial_dormant_set(chars) == {"spider"}

    def test_missing_field_treated_as_always(self):
        amara = _stub_session("party")
        del amara.activation  # type: ignore[attr-defined]
        chars = {"amara": amara}
        assert initial_dormant_set(chars) == set()

    def test_empty_string_is_always(self):
        chars = {"amara": _stub_session("party", "")}
        assert initial_dormant_set(chars) == set()


class TestZoneEntryActivation:
    def test_party_in_zone_activates(self):
        chars = {
            "amara": _stub_session("party"),
            "spider": _stub_session("hostile", "zone_entry:Secret Chamber"),
        }
        active = {"amara"}
        positions = {
            "amara": (60.0, 195.0, "SECRET CHAMBER"),
            "spider": (64.0, 195.0, "SECRET CHAMBER"),
        }
        fired = check_activations(
            characters=chars,
            active_characters=active,
            current_positions=positions,
        )
        assert "spider" in active
        assert any(r.startswith("zone_entry:") for _, r in fired)

    def test_party_not_in_zone_does_not_activate(self):
        chars = {
            "amara": _stub_session("party"),
            "spider": _stub_session("hostile", "zone_entry:Secret Chamber"),
        }
        active = {"amara"}
        positions = {
            "amara": (137.0, 265.0, "ENTRY CHAMBER"),
            "spider": (64.0, 195.0, "SECRET CHAMBER"),
        }
        fired = check_activations(
            characters=chars,
            active_characters=active,
            current_positions=positions,
        )
        assert "spider" not in active
        assert fired == []

    def test_same_faction_does_not_trigger(self):
        # Another hostile creature standing in the spider's lair shouldn't
        # wake it.
        chars = {
            "spider": _stub_session("hostile", "zone_entry:Secret Chamber"),
            "rat": _stub_session("hostile"),
        }
        active = {"rat"}
        positions = {
            "spider": (64.0, 195.0, "SECRET CHAMBER"),
            "rat": (60.0, 195.0, "SECRET CHAMBER"),
        }
        check_activations(
            characters=chars,
            active_characters=active,
            current_positions=positions,
        )
        assert "spider" not in active

    def test_already_active_unchanged(self):
        chars = {"spider": _stub_session("hostile", "zone_entry:Secret Chamber")}
        active = {"spider"}
        positions = {"spider": (64.0, 195.0, "SECRET CHAMBER")}
        fired = check_activations(
            characters=chars,
            active_characters=active,
            current_positions=positions,
        )
        # No double-firing.
        assert fired == []


class TestDoorOpenActivation:
    def test_door_open_event_activates(self):
        chars = {
            "guardian": _stub_session("hostile", "door_open:secret_door"),
        }
        active: set[str] = set()
        fired = check_activations(
            characters=chars,
            active_characters=active,
            current_positions={},
            door_events=[{"type": "door_open"}],
        )
        assert "guardian" in active
        assert any("door_open" in r for _, r in fired)

    def test_no_door_event_does_not_activate(self):
        chars = {
            "guardian": _stub_session("hostile", "door_open:secret_door"),
        }
        active: set[str] = set()
        check_activations(
            characters=chars,
            active_characters=active,
            current_positions={},
            door_events=[],
        )
        assert "guardian" not in active

    def test_door_close_does_not_activate(self):
        chars = {
            "guardian": _stub_session("hostile", "door_open:secret_door"),
        }
        active: set[str] = set()
        check_activations(
            characters=chars,
            active_characters=active,
            current_positions={},
            door_events=[{"type": "door_close"}],
        )
        assert "guardian" not in active
