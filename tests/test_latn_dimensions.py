"""Tests for Driftmoor's RPG dimension definitions (engine.latn_dimensions).

The pure functions (name derivation) need no Engraf; the registration
round-trip is skipped unless Engraf is importable.
"""

from dataclasses import dataclass

import pytest

from engine.latn_dimensions import (
    RESPONSE_DIMS,
    CURRENCY_DIMS,
    FACTION_VALUES,
    SPATIAL_DIMS,
    VERB_DIMS,
    _norm,
    derive_character_property_dims,
    driftmoor_rpg_dimensions,
)


@dataclass
class _FakeChar:
    race: str = ""
    character_class: str = ""
    role: str = ""


def test_norm_snake_cases_free_text():
    assert _norm("High Elf") == "high_elf"
    assert _norm("  War-Cleric ") == "war_cleric"
    assert _norm("Smith") == "smith"
    assert _norm("") == ""


def test_derive_namespaces_and_dedupes():
    chars = [
        _FakeChar(race="Dwarf", character_class="Cleric", role="Smith"),
        _FakeChar(race="Dwarf", character_class="Fighter"),     # dup race
        _FakeChar(race="High Elf", role="Captain of the Guard"),
    ]
    dims = derive_character_property_dims(chars)
    assert dims == sorted(dims)  # sorted, deterministic
    assert "race_dwarf" in dims
    assert "race_high_elf" in dims
    assert "class_cleric" in dims and "class_fighter" in dims
    assert "role_smith" in dims and "role_captain_of_the_guard" in dims
    assert dims.count("race_dwarf") == 1  # de-duped


def test_full_list_is_static_first_and_deduped():
    chars = [_FakeChar(race="Human", character_class="Wizard")]
    dims = driftmoor_rpg_dimensions(chars)
    # verbs lead, bare
    assert dims[: len(VERB_DIMS)] == list(VERB_DIMS)
    # faction present, namespaced
    for f in FACTION_VALUES:
        assert f"faction_{f}" in dims
    # derived present
    assert "race_human" in dims and "class_wizard" in dims
    # no duplicates overall
    assert len(dims) == len(set(dims))


def test_empty_characters_yields_only_static():
    dims = driftmoor_rpg_dimensions()
    assert set(dims) == (
        set(VERB_DIMS)
        | set(SPATIAL_DIMS)
        | set(RESPONSE_DIMS)
        | set(CURRENCY_DIMS)
        | {f"faction_{f}" for f in FACTION_VALUES}
    )


def test_registration_round_trip_if_engraf_available():
    pytest.importorskip("latn.An_N_Space_Model.vector_dimensions")
    from latn.An_N_Space_Model import vector_dimensions as vd
    from engine.latn_dimensions import register_driftmoor_dimensions

    snap = list(vd.VECTOR_DIMENSIONS)
    try:
        register_driftmoor_dimensions([_FakeChar(race="Dwarf", character_class="Cleric")])
        assert "examine" in vd.VECTOR_DIMENSIONS
        assert "class_cleric" in vd.VECTOR_DIMENSIONS
        assert "race_dwarf" in vd.VECTOR_DIMENSIONS
    finally:
        vd.VECTOR_DIMENSIONS[:] = snap
