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
                properties=["natural"],  # always in hand; needs no draw
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
    monkeypatch.setattr("engine.game_rng._rng.randint", lambda a, b: next(rolls))

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
    monkeypatch.setattr("engine.game_rng._rng.randint", lambda a, b: next(rolls))

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


def _multi_weapon_attacker() -> CharacterSession:
    attacker = Creature(
        id="rogue_npc", name="Rogue", race="Human", character_type="creature",
        hp=20, current_hp=20, ac=14, dexterity=16, faction="hostile",
    )
    return CharacterSession(
        character=attacker,
        condition=CharacterCondition(
            character_id="rogue_npc", character_name="Rogue",
            state=NeurochemicalState(),
        ),
        soul="", identity="", initial_scene="",
        weapons=[
            Weapon(id="rapier", name="Rapier", damage_dice="1d8",
                   damage_type="piercing", attack_bonus=5, reach=5),
            Weapon(id="dagger", name="Dagger", damage_dice="1d4",
                   damage_type="piercing", attack_bonus=5, reach=5),
            Weapon(id="light_crossbow", name="Light Crossbow", damage_dice="1d8",
                   damage_type="piercing", attack_bonus=5, reach=5,
                   range_normal=80, range_max=320),
        ],
    )


def _resolve_with_intent(monkeypatch, intent_text):
    # Mirror the live flow: default-wield a primary, apply the turn's draw/
    # sheathe from the intent, then resolve against the wielded weapon(s).
    from engine.loadout import default_wield
    from engine.session import _apply_loadout_intent
    monkeypatch.setattr(
        "engine.game_rng._rng.randint", lambda a, b: 3)
    cs = _multi_weapon_attacker()
    default_wield(cs)
    _apply_loadout_intent(intent_text, cs, [])
    resolver = CombatResolver()
    _, log = resolver.resolve(
        character_id="rogue_npc", turn=1,
        attacker_session=cs,
        target_id="tobin", target_session=_target_session(),
        attacker_pos=(0.0, 0.0, "ROOM"), target_pos=(0.0, 0.0, "ROOM"),
        intent_text=intent_text,
    )
    return "\n".join(log)


def test_named_weapon_is_honored_over_best(monkeypatch):
    # "attack with my dagger" must use the dagger, not the higher-damage rapier.
    log = _resolve_with_intent(monkeypatch, "I attack the target with my dagger")
    assert "(Dagger)" in log and "(Rapier)" not in log


def test_unnamed_attack_falls_back_to_best_weapon(monkeypatch):
    # No weapon named -> damage-maximizing default (rapier 1d8 over dagger 1d4).
    log = _resolve_with_intent(monkeypatch, "I attack the target")
    assert "(Rapier)" in log


def test_named_ranged_weapon_honored(monkeypatch):
    # Naming the crossbow selects it even at melee range.
    log = _resolve_with_intent(monkeypatch, "I attack with my crossbow")
    assert "(Light Crossbow)" in log


def test_named_weapon_pure_helper():
    from engine.combat_resolver import _named_weapon
    ws = _multi_weapon_attacker().weapons
    assert _named_weapon("stab with my dagger", ws, 5.0).name == "Dagger"
    assert _named_weapon("fire the crossbow", ws, 5.0).name == "Light Crossbow"
    assert _named_weapon("swing the battle axe", ws, 5.0) is None  # not owned
    assert _named_weapon("attack the spider", ws, 5.0) is None     # nothing named


def test_preferred_weapon_overrides_best(monkeypatch):
    # A just-picked-up weapon (passed as preferred) is used even though the
    # rapier would otherwise win the damage-max default. It must be wielded.
    monkeypatch.setattr(
        "engine.game_rng._rng.randint", lambda a, b: 3)
    cs = _multi_weapon_attacker()
    cs.wielded = ["rapier", "dagger"]            # both in hand
    dagger = next(w for w in cs.weapons if w.id == "dagger")
    resolver = CombatResolver()
    _, log = resolver.resolve(
        character_id="rogue_npc", turn=1, attacker_session=cs,
        target_id="tobin", target_session=_target_session(),
        attacker_pos=(0.0, 0.0, "ROOM"), target_pos=(0.0, 0.0, "ROOM"),
        intent_text="I attack the target",   # no weapon named
        preferred_weapon=dagger,
    )
    assert "(Dagger)" in "\n".join(log)


def test_preferred_weapon_ignored_when_not_wielded(monkeypatch):
    monkeypatch.setattr(
        "engine.game_rng._rng.randint", lambda a, b: 3)
    cs = _multi_weapon_attacker()
    cs.wielded = ["rapier"]                       # dagger NOT in hand
    dagger = next(w for w in cs.weapons if w.id == "dagger")
    resolver = CombatResolver()
    _, log = resolver.resolve(
        character_id="rogue_npc", turn=1, attacker_session=cs,
        target_id="tobin", target_session=_target_session(),
        attacker_pos=(0.0, 0.0, "ROOM"), target_pos=(0.0, 0.0, "ROOM"),
        intent_text="I attack the target", preferred_weapon=dagger,
    )
    assert "(Rapier)" in "\n".join(log)         # falls back to wielded best
