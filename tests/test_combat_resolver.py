"""Unit tests for Python combat resolver attack-roll modifiers."""

from __future__ import annotations

from engine.combat_resolver import CombatResolver
from engine.session import CharacterSession
from models.character import Creature, PlayerCharacter
from models.condition import CharacterCondition, NeurochemicalState
from models.weapon import Weapon


def _attacker_session() -> CharacterSession:
    attacker = Creature(
        id="shadowbeast_1",
        name="Shadowbeast",
        race="Monstrosity",
        character_type="creature",
        hp=20,
        current_hp=20,
        ac=12,
        dexterity=14,
        faction="hostile",
    )
    return CharacterSession(
        character=attacker,
        condition=CharacterCondition(
            character_id="shadowbeast_1",
            character_name="Shadowbeast",
            state=NeurochemicalState(),
        ),
        soul="",
        identity="",
        initial_scene="",
        weapons=[
            Weapon(
                id="claw",
                name="Claw",
                damage_dice="1d4",
                damage_type="slashing",
                attack_bonus=5,
                reach=5,
            )
        ],
    )


def _target_session() -> CharacterSession:
    target = PlayerCharacter(
        id="tobin",
        name="Tobin",
        race="Half-Elf",
        character_type="player",
        character_class="Cleric",
        level=3,
        hp=24,
        current_hp=24,
        ac=14,
        dexterity=10,
        faction="party",
    )
    return CharacterSession(
        character=target,
        condition=CharacterCondition(
            character_id="tobin",
            character_name="Tobin",
            state=NeurochemicalState(),
        ),
        soul="",
        identity="",
        initial_scene="",
    )


def test_resolve_without_disadvantage_can_hit(monkeypatch):
    rolls = iter([15, 4])  # d20, damage die
    monkeypatch.setattr("engine.combat_resolver.random.randint", lambda a, b: next(rolls))

    resolver = CombatResolver()
    adjudication, _ = resolver.resolve(
        character_id="shadowbeast_1",
        turn=1,
        attacker_session=_attacker_session(),
        target_id="tobin",
        target_session=_target_session(),
        attacker_pos=(0.0, 0.0, "ROOM"),
        target_pos=(0.0, 0.0, "ROOM"),
        attack_disadvantage=False,
    )

    assert adjudication.hp_damage.get("tobin", 0) > 0


def test_resolve_with_disadvantage_uses_lower_roll(monkeypatch):
    # disadvantage d20s: 15 and 2 => uses 2, total 7 vs AC14 -> miss
    rolls = iter([15, 2])
    monkeypatch.setattr("engine.combat_resolver.random.randint", lambda a, b: next(rolls))

    resolver = CombatResolver()
    adjudication, log = resolver.resolve(
        character_id="shadowbeast_1",
        turn=1,
        attacker_session=_attacker_session(),
        target_id="tobin",
        target_session=_target_session(),
        attacker_pos=(0.0, 0.0, "ROOM"),
        target_pos=(0.0, 0.0, "ROOM"),
        attack_disadvantage=True,
    )

    assert adjudication.hp_damage == {}
    assert any("disadvantage applied" in line.lower() for line in log)
