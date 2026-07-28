"""Python spell resolution (MVP): slots, concentration, and core spell effects."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from models.character import PlayerCharacter
from models.game_state import GameState
from models.spellcasting import SpellcastingProfile


@dataclass
class SpellCastRequest:
    """One spell-cast attempt against optional targets."""

    caster_id: str
    spell_name: str
    target_ids: list[str] = field(default_factory=list)
    slot_level: int | None = None


@dataclass
class ActiveSpellEffect:
    """A running spell effect tracked by scene runtime state."""

    spell_name: str
    caster_id: str
    target_ids: list[str]
    remaining_rounds: int
    concentration: bool = False


@dataclass
class SpellRuntimeState:
    """Mutable runtime spell state for a scene/session."""

    active_effects: list[ActiveSpellEffect] = field(default_factory=list)
    concentration_by_caster: dict[str, ActiveSpellEffect] = field(default_factory=dict)


@dataclass
class SpellCastResult:
    """Outcome of one cast attempt."""

    approved: bool
    reason: str = ""
    slot_level_used: int | None = None
    hp_damage: dict[str, int] = field(default_factory=dict)
    hp_heal: dict[str, int] = field(default_factory=dict)
    started_effects: list[str] = field(default_factory=list)
    ended_effects: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _SpellDef:
    name: str
    level: int
    concentration: bool = False
    duration_rounds: int = 0
    effect: str = "utility"  # utility | damage | heal | stabilize
    dice: str = ""
    attack_roll: bool = False
    save_ability: str = ""  # DEX | CON | WIS | INT | CHA | STR
    save_on_success: str = "none"  # none | half


_SPELL_BOOK: dict[str, _SpellDef] = {
    "fire bolt": _SpellDef(name="Fire Bolt", level=0, effect="damage", dice="1d10"),
    "sacred flame": _SpellDef(
        name="Sacred Flame",
        level=0,
        effect="damage",
        dice="1d8",
        save_ability="DEX",
        save_on_success="none",
    ),
    "vicious mockery": _SpellDef(
        name="Vicious Mockery",
        level=0,
        effect="damage",
        dice="1d4",
        save_ability="WIS",
        save_on_success="none",
    ),
    "spare the dying": _SpellDef(name="Spare the Dying", level=0, effect="stabilize"),
    "guidance": _SpellDef(name="Guidance", level=0, concentration=True, duration_rounds=10),
    "light": _SpellDef(name="Light", level=0, duration_rounds=600),
    "healing word": _SpellDef(name="Healing Word", level=1, effect="heal", dice="1d4"),
    "cure wounds": _SpellDef(name="Cure Wounds", level=1, effect="heal", dice="1d8"),
    "guiding bolt": _SpellDef(name="Guiding Bolt", level=1, effect="damage", dice="4d6", attack_roll=True),
    "magic missile": _SpellDef(name="Magic Missile", level=1, effect="damage", dice="3d4+3"),
    "burning hands": _SpellDef(
        name="Burning Hands",
        level=1,
        effect="damage",
        dice="3d6",
        save_ability="DEX",
        save_on_success="half",
    ),
    "bless": _SpellDef(name="Bless", level=1, concentration=True, duration_rounds=10),
    "shield of faith": _SpellDef(name="Shield of Faith", level=1, concentration=True, duration_rounds=100),
    "faerie fire": _SpellDef(name="Faerie Fire", level=1, concentration=True, duration_rounds=10),
    "sanctuary": _SpellDef(name="Sanctuary", level=1, duration_rounds=10),
    "shield": _SpellDef(name="Shield", level=1, duration_rounds=1),
    "teleport": _SpellDef(name="Teleport", level=7, effect="teleport"),
}


def supported_spells_for(character: object) -> list[str]:
    """Engine-supported spells the character currently knows or has prepared."""
    profile = getattr(character, "spellcasting", None)
    if profile is None:
        return []
    authored = {
        _canonical_spell_name(s.name)
        for s in (
            list(profile.cantrips or [])
            + list(profile.prepared or [])
            + list(profile.known or [])
        )
        if getattr(s, "name", "")
    }
    return [
        definition.name
        for key, definition in _SPELL_BOOK.items()
        if key in authored
    ]


def _canonical_spell_name(name: str) -> str:
    """Normalize authored spell bullet text to a stable spell-name key."""
    if not name:
        return ""
    s = name.strip().lower()
    # Keep text before the first separator used for spell details.
    s = re.split(r"\s+[—\-:]\s+", s, maxsplit=1)[0]
    return re.sub(r"\s+", " ", s)


def _roll_dice(expr: str, rng: random.Random) -> int:
    total = 0
    for m in re.finditer(r"(\d+)\s*[dD]\s*(\d+)", expr):
        count, sides = int(m.group(1)), int(m.group(2))
        for _ in range(count):
            total += rng.randint(1, sides)
    remainder = re.sub(r"\d+\s*[dD]\s*\d+", "", expr)
    for m in re.finditer(r"([+-]\s*\d+)", remainder):
        total += int(m.group(1).replace(" ", ""))
    return max(0, total)


def _ability_mod(caster: PlayerCharacter, profile: SpellcastingProfile) -> int:
    key = (profile.ability or "").upper()
    if key == "CHA":
        return caster.modifier("charisma")
    if key == "WIS":
        return caster.modifier("wisdom")
    if key == "INT":
        return caster.modifier("intelligence")
    return 0


def _defense_mod(target: object, ability_key: str) -> int:
    key = (ability_key or "").upper()
    attr = {
        "STR": "strength",
        "DEX": "dexterity",
        "CON": "constitution",
        "INT": "intelligence",
        "WIS": "wisdom",
        "CHA": "charisma",
    }.get(key)
    if not attr:
        return 0
    if hasattr(target, "modifier") and hasattr(target, attr):
        try:
            return int(target.modifier(attr))
        except Exception:
            return 0
    return 0


def _known_or_prepared_names(profile: SpellcastingProfile, level: int) -> set[str]:
    names: set[str] = set()
    if level == 0:
        for spell in profile.cantrips:
            names.add(_canonical_spell_name(spell.name))
        return names
    for spell in profile.prepared:
        names.add(_canonical_spell_name(spell.name))
    for spell in profile.known:
        names.add(_canonical_spell_name(spell.name))
    return names


def _choose_slot_level(
    profile: SpellcastingProfile,
    *,
    required_level: int,
    requested_level: int | None,
) -> int | None:
    if required_level == 0:
        return 0
    if requested_level is not None:
        if requested_level < required_level:
            return None
        used = profile.spell_slots_used.get(requested_level, 0)
        max_slots = profile.spell_slots_max.get(requested_level, 0)
        return requested_level if used < max_slots else None

    for level in sorted(profile.spell_slots_max):
        if level < required_level:
            continue
        used = profile.spell_slots_used.get(level, 0)
        if used < profile.spell_slots_max[level]:
            return level
    return None


class SpellResolver:
    """MVP spell resolver for deterministic engine-side adjudication."""

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()

    def cast(
        self,
        game_state: GameState,
        request: SpellCastRequest,
        runtime: SpellRuntimeState,
    ) -> SpellCastResult:
        caster_obj = game_state.get_character(request.caster_id)
        if not isinstance(caster_obj, PlayerCharacter):
            return SpellCastResult(approved=False, reason="Caster must be a player character")

        profile = caster_obj.spellcasting
        if profile is None:
            return SpellCastResult(approved=False, reason="Caster has no spellcasting profile")

        key = _canonical_spell_name(request.spell_name)
        spell_def = _SPELL_BOOK.get(key)
        if spell_def is None:
            return SpellCastResult(approved=False, reason=f"Unsupported spell: {request.spell_name}")

        available = _known_or_prepared_names(profile, spell_def.level)
        if key not in available:
            return SpellCastResult(approved=False, reason="Spell is not known/prepared by caster")

        slot_level = _choose_slot_level(
            profile,
            required_level=spell_def.level,
            requested_level=request.slot_level,
        )
        if slot_level is None:
            return SpellCastResult(approved=False, reason="No spell slot available")

        result = SpellCastResult(approved=True, slot_level_used=(slot_level if slot_level > 0 else None))

        if spell_def.level > 0:
            profile.spell_slots_used[slot_level] = profile.spell_slots_used.get(slot_level, 0) + 1

        # One concentration effect per caster.
        if spell_def.concentration and request.caster_id in runtime.concentration_by_caster:
            old = runtime.concentration_by_caster[request.caster_id]
            runtime.active_effects = [e for e in runtime.active_effects if e is not old]
            result.ended_effects.append(old.spell_name)

        if spell_def.effect == "damage":
            if key == "magic missile":
                target_ids = [
                    tid for tid in request.target_ids
                    if game_state.get_character(tid) is not None
                    and hasattr(game_state.get_character(tid), "current_hp")
                ]
                if target_ids:
                    for i in range(3):
                        tid = target_ids[i % len(target_ids)]
                        target = game_state.get_character(tid)
                        if target is None or not hasattr(target, "current_hp"):
                            continue
                        dmg = self._rng.randint(1, 4) + 1
                        target.current_hp = max(0, target.current_hp - dmg)
                        result.hp_damage[tid] = result.hp_damage.get(tid, 0) + dmg
                return result
            for tid in request.target_ids:
                target = game_state.get_character(tid)
                if target is None or not hasattr(target, "current_hp"):
                    continue
                if spell_def.attack_roll:
                    attack_total = self._rng.randint(1, 20) + int(profile.attack_bonus or 0)
                    target_ac = int(getattr(target, "ac", 10) or 10)
                    if attack_total < target_ac:
                        continue
                if spell_def.save_ability:
                    save_total = self._rng.randint(1, 20) + _defense_mod(target, spell_def.save_ability)
                    save_dc = int(profile.save_dc or 10)
                    saved = save_total >= save_dc
                else:
                    saved = False
                if saved and spell_def.save_on_success == "none":
                    continue
                dmg = _roll_dice(spell_def.dice, self._rng)
                if saved:
                    if spell_def.save_on_success == "half":
                        dmg //= 2
                target.current_hp = max(0, target.current_hp - dmg)
                result.hp_damage[tid] = result.hp_damage.get(tid, 0) + dmg
                if key == "vicious mockery":
                    rider = ActiveSpellEffect(
                        spell_name="Vicious Mockery Disadvantage",
                        caster_id=request.caster_id,
                        target_ids=[tid],
                        remaining_rounds=10,
                        concentration=False,
                    )
                    runtime.active_effects.append(rider)
                    result.started_effects.append(rider.spell_name)
        elif spell_def.effect == "heal":
            amount = _roll_dice(spell_def.dice, self._rng) + _ability_mod(caster_obj, profile)
            amount = max(1, amount)
            for tid in request.target_ids:
                target = game_state.get_character(tid)
                if target is None or not hasattr(target, "current_hp") or not hasattr(target, "hp"):
                    continue
                target.current_hp = min(target.hp, target.current_hp + amount)
                result.hp_heal[tid] = result.hp_heal.get(tid, 0) + amount
        elif spell_def.effect == "stabilize":
            result.events.append("stabilize_attempt")
        elif spell_def.effect == "teleport":
            # Slot is consumed here; the actual relocation is applied by the
            # session, which owns scene geometry and position state.
            result.events.append("teleport")
        if spell_def.concentration or spell_def.duration_rounds > 0:
            effect = ActiveSpellEffect(
                spell_name=spell_def.name,
                caster_id=request.caster_id,
                target_ids=list(request.target_ids),
                remaining_rounds=spell_def.duration_rounds,
                concentration=spell_def.concentration,
            )
            runtime.active_effects.append(effect)
            result.started_effects.append(effect.spell_name)
            if spell_def.concentration:
                runtime.concentration_by_caster[request.caster_id] = effect

        return result

    def tick_effects(self, runtime: SpellRuntimeState, *, rounds: int = 1) -> list[str]:
        """Advance active spell durations and return names of expired effects."""
        expired_names: list[str] = []
        remaining: list[ActiveSpellEffect] = []

        for effect in runtime.active_effects:
            if effect.remaining_rounds > 0:
                effect.remaining_rounds = max(0, effect.remaining_rounds - rounds)

            if effect.remaining_rounds == 0:
                expired_names.append(effect.spell_name)
                if effect.concentration:
                    cur = runtime.concentration_by_caster.get(effect.caster_id)
                    if cur is effect:
                        runtime.concentration_by_caster.pop(effect.caster_id, None)
            else:
                remaining.append(effect)

        runtime.active_effects = remaining
        return expired_names
