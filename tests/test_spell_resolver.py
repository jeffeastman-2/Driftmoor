"""TDD tests for Python spell resolution (resource + effect semantics)."""

from __future__ import annotations

import random

from engine.spell_resolver import (
    SpellCastRequest,
    SpellResolver,
    SpellRuntimeState,
)
from models.character import Creature, PlayerCharacter
from models.game_state import GameState
from models.spellcasting import Spell, SpellcastingProfile


def _caster(
    *,
    cid: str,
    name: str,
    character_class: str,
    level: int,
    ability_mod: int,
    cantrips: list[str],
    known: list[str],
    prepared: list[str],
    slots: dict[int, int],
) -> PlayerCharacter:
    profile = SpellcastingProfile(
        ability="CHA",
        save_dc=13,
        attack_bonus=5,
        cantrips=[Spell(name=s, level=0) for s in cantrips],
        known=[Spell(name=s, level=1) for s in known],
        prepared=[Spell(name=s, level=1) for s in prepared],
        spell_slots_max=dict(slots),
        spell_slots_used={k: 0 for k in slots},
    )
    return PlayerCharacter(
        id=cid,
        name=name,
        race="Human",
        character_type="player",
        character_class=character_class,
        level=level,
        charisma=10 + ability_mod * 2,
        wisdom=10 + ability_mod * 2,
        intelligence=10 + ability_mod * 2,
        hp=20,
        current_hp=20,
        ac=12,
        spellcasting=profile,
    )


def _target(cid: str = "shadowbeast", hp: int = 18) -> Creature:
    return Creature(
        id=cid,
        name="Shadowbeast",
        race="Monstrosity",
        character_type="creature",
        hp=hp,
        current_hp=hp,
        ac=12,
    )


class TestSpellResolverCore:
    def test_cantrip_does_not_consume_slots(self):
        caster = _caster(
            cid="varrak",
            name="Varrak",
            character_class="Sorcerer",
            level=1,
            ability_mod=3,
            cantrips=["Fire Bolt"],
            known=["Shield"],
            prepared=[],
            slots={1: 2},
        )
        target = _target(hp=10)
        gs = GameState(characters=[caster, target])

        runtime = SpellRuntimeState()
        result = SpellResolver(rng=random.Random(1)).cast(
            gs,
            SpellCastRequest(caster_id="varrak", spell_name="Fire Bolt", target_ids=["shadowbeast"]),
            runtime,
        )

        assert result.approved
        assert target.current_hp < 10
        assert caster.spellcasting.spell_slots_used[1] == 0

    def test_leveled_spell_consumes_slot(self):
        caster = _caster(
            cid="tobin",
            name="Tobin",
            character_class="Cleric",
            level=3,
            ability_mod=3,
            cantrips=["Guidance"],
            known=[],
            prepared=["Healing Word"],
            slots={1: 4, 2: 2},
        )
        ally = _target("brenna", hp=20)
        ally.current_hp = 10
        gs = GameState(characters=[caster, ally])

        runtime = SpellRuntimeState()
        result = SpellResolver(rng=random.Random(2)).cast(
            gs,
            SpellCastRequest(caster_id="tobin", spell_name="Healing Word", target_ids=["brenna"]),
            runtime,
        )

        assert result.approved
        assert ally.current_hp > 10
        assert caster.spellcasting.spell_slots_used[1] == 1

    def test_rejects_when_no_spell_slots_remain(self):
        caster = _caster(
            cid="tobin",
            name="Tobin",
            character_class="Cleric",
            level=3,
            ability_mod=3,
            cantrips=["Guidance"],
            known=[],
            prepared=["Guiding Bolt"],
            slots={1: 1},
        )
        caster.spellcasting.spell_slots_used[1] = 1
        target = _target(hp=10)
        gs = GameState(characters=[caster, target])

        runtime = SpellRuntimeState()
        result = SpellResolver(rng=random.Random(3)).cast(
            gs,
            SpellCastRequest(caster_id="tobin", spell_name="Guiding Bolt", target_ids=["shadowbeast"]),
            runtime,
        )

        assert not result.approved
        assert "slot" in result.reason.lower()
        assert target.current_hp == 10

    def test_replaces_existing_concentration(self):
        caster = _caster(
            cid="tobin",
            name="Tobin",
            character_class="Cleric",
            level=3,
            ability_mod=3,
            cantrips=["Guidance"],
            known=[],
            prepared=["Bless", "Shield of Faith"],
            slots={1: 4},
        )
        ally = _target("brenna", hp=20)
        gs = GameState(characters=[caster, ally])

        runtime = SpellRuntimeState()
        resolver = SpellResolver(rng=random.Random(4))

        first = resolver.cast(
            gs,
            SpellCastRequest(caster_id="tobin", spell_name="Bless", target_ids=["brenna"]),
            runtime,
        )
        second = resolver.cast(
            gs,
            SpellCastRequest(caster_id="tobin", spell_name="Shield of Faith", target_ids=["brenna"]),
            runtime,
        )

        assert first.approved
        assert second.approved
        assert runtime.concentration_by_caster["tobin"].spell_name == "Shield of Faith"
        assert "Bless" in second.ended_effects

    def test_rejects_unknown_or_unavailable_spell(self):
        caster = _caster(
            cid="varrak",
            name="Varrak",
            character_class="Sorcerer",
            level=1,
            ability_mod=3,
            cantrips=["Fire Bolt"],
            known=["Shield"],
            prepared=[],
            slots={1: 2},
        )
        target = _target(hp=10)
        gs = GameState(characters=[caster, target])

        runtime = SpellRuntimeState()
        result = SpellResolver(rng=random.Random(5)).cast(
            gs,
            SpellCastRequest(caster_id="varrak", spell_name="Guiding Bolt", target_ids=["shadowbeast"]),
            runtime,
        )

        assert not result.approved
        assert "known" in result.reason.lower() or "prepared" in result.reason.lower()

    def test_guidance_cantrip_sets_concentration_without_slot(self):
        caster = _caster(
            cid="tobin",
            name="Tobin",
            character_class="Cleric",
            level=3,
            ability_mod=3,
            cantrips=["Guidance"],
            known=[],
            prepared=[],
            slots={1: 4},
        )
        ally = _target("brenna", hp=20)
        gs = GameState(characters=[caster, ally])

        runtime = SpellRuntimeState()
        result = SpellResolver(rng=random.Random(6)).cast(
            gs,
            SpellCastRequest(caster_id="tobin", spell_name="Guidance", target_ids=["brenna"]),
            runtime,
        )

        assert result.approved
        assert caster.spellcasting.spell_slots_used[1] == 0
        assert runtime.concentration_by_caster["tobin"].spell_name == "Guidance"

    def test_shield_starts_non_concentration_effect(self):
        caster = _caster(
            cid="varrak",
            name="Varrak",
            character_class="Sorcerer",
            level=1,
            ability_mod=3,
            cantrips=["Fire Bolt"],
            known=["Shield"],
            prepared=[],
            slots={1: 2},
        )
        gs = GameState(characters=[caster])

        runtime = SpellRuntimeState()
        result = SpellResolver(rng=random.Random(7)).cast(
            gs,
            SpellCastRequest(caster_id="varrak", spell_name="Shield", target_ids=["varrak"]),
            runtime,
        )

        assert result.approved
        assert caster.spellcasting.spell_slots_used[1] == 1
        assert runtime.concentration_by_caster == {}
        assert any(e.spell_name == "Shield" for e in runtime.active_effects)

    def test_burning_hands_hits_multiple_targets(self):
        caster = _caster(
            cid="varrak",
            name="Varrak",
            character_class="Sorcerer",
            level=1,
            ability_mod=3,
            cantrips=["Fire Bolt"],
            known=["Burning Hands"],
            prepared=[],
            slots={1: 2},
        )
        t1 = _target("beast1", hp=20)
        t2 = _target("beast2", hp=20)
        gs = GameState(characters=[caster, t1, t2])

        runtime = SpellRuntimeState()
        result = SpellResolver(rng=random.Random(8)).cast(
            gs,
            SpellCastRequest(caster_id="varrak", spell_name="Burning Hands", target_ids=["beast1", "beast2"]),
            runtime,
        )

        assert result.approved
        assert "beast1" in result.hp_damage
        assert "beast2" in result.hp_damage
        assert t1.current_hp < 20 and t2.current_hp < 20

    def test_spare_the_dying_emits_stabilize_event(self):
        caster = _caster(
            cid="amara",
            name="Amara",
            character_class="Cleric",
            level=1,
            ability_mod=3,
            cantrips=["Spare the Dying"],
            known=[],
            prepared=[],
            slots={1: 2},
        )
        ally = _target("brenna", hp=20)
        ally.current_hp = 0
        gs = GameState(characters=[caster, ally])

        runtime = SpellRuntimeState()
        result = SpellResolver(rng=random.Random(9)).cast(
            gs,
            SpellCastRequest(caster_id="amara", spell_name="Spare the Dying", target_ids=["brenna"]),
            runtime,
        )

        assert result.approved
        assert "stabilize_attempt" in result.events

    def test_tick_effects_expires_concentration(self):
        caster = _caster(
            cid="tobin",
            name="Tobin",
            character_class="Cleric",
            level=3,
            ability_mod=3,
            cantrips=["Guidance"],
            known=[],
            prepared=[],
            slots={1: 4},
        )
        ally = _target("brenna", hp=20)
        gs = GameState(characters=[caster, ally])

        runtime = SpellRuntimeState()
        resolver = SpellResolver(rng=random.Random(10))
        cast = resolver.cast(
            gs,
            SpellCastRequest(caster_id="tobin", spell_name="Guidance", target_ids=["brenna"]),
            runtime,
        )
        assert cast.approved

        expired = resolver.tick_effects(runtime, rounds=10)
        assert "Guidance" in expired
        assert "tobin" not in runtime.concentration_by_caster
