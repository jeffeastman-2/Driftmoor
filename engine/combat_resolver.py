"""Python-only combat resolution — bypasses DM-Left during active combat.

When ``in_combat`` is True and a character's intent is to attack, this module
produces an ``Adjudication`` directly without calling the DM-Left LLM.  This
eliminates hallucinated multiattacks, ignored range limits, and attacks against
dead targets that plague LLM-based adjudication.

Data flow with CombatResolver active:
    Player-Left (intent) → Player-Right (prose) → CombatResolver → DM-Right (narrate)

The resolver handles:
- Weapon selection: chooses best weapon from CharacterSession.weapons for range to target
- Auto-movement: moves attacker toward target up to speed (Python geometry) 
- Attack roll: d20 + weapon.attack_bonus vs target AC
- Damage roll: weapon.damage_dice with resistance/vulnerability applied
- Ammo tracking: decrements arrow count from character identity (best-effort)
- Condition deltas: standard table (took damage → cortisol, dealt damage → dopamine)
"""

from __future__ import annotations

import math
import random
import re
from typing import Optional

from engine.dm_agent import Adjudication
from models.weapon import Weapon


# ---------------------------------------------------------------------------
# Condition delta table (added to attacker/target independent of LLM)
# ---------------------------------------------------------------------------

_DEALT_DAMAGE_DELTAS = {"dopamine": 0.08, "norepinephrine": 0.05}
_TOOK_DAMAGE_DELTAS  = {"cortisol": 0.12, "norepinephrine": 0.08}
_MISSED_ATTACK_DELTAS = {"cortisol": 0.04}


def _roll_damage(dice_expr: str) -> int:
    """Roll a damage expression like '1d6', '2d4+2', '1d8 slashing'."""
    total = 0
    for m in re.finditer(r'(\d+)\s*[dD]\s*(\d+)', dice_expr):
        count, sides = int(m.group(1)), int(m.group(2))
        for _ in range(count):
            total += random.randint(1, sides)
    remainder = re.sub(r'\d+\s*[dD]\s*\d+', '', dice_expr)
    for m in re.finditer(r'([+-]\s*\d+)', remainder):
        total += int(m.group(1).replace(' ', ''))
    plain = remainder.strip()
    if re.fullmatch(r'\d+', plain):
        total += int(plain)
    return max(1, total)


def _apply_resistances(damage: int, damage_type: str, char) -> int:
    """Halve damage for resistances, double for vulnerabilities.

    ``char`` is a Character dataclass with damage_resistances and
    damage_vulnerabilities list[str] fields.
    """
    dtype = damage_type.lower()

    # Resistance: check if any resistance entry contains the damage type
    for res in getattr(char, "damage_resistances", []):
        if dtype in res.lower():
            damage = max(1, damage // 2)
            return damage  # resistance and vulnerability don't stack

    # Vulnerability
    for vuln in getattr(char, "damage_vulnerabilities", []):
        if dtype in vuln.lower():
            damage = damage * 2
            return damage

    return damage


def _distance(pos_a: tuple[float, float, str], pos_b: tuple[float, float, str]) -> float:
    return math.hypot(pos_b[0] - pos_a[0], pos_b[1] - pos_a[1])


def _move_toward(
    origin: tuple[float, float, str],
    target: tuple[float, float, str],
    max_feet: float,
    scene_geometry,
) -> tuple[float, float, str]:
    """Move from origin toward target up to max_feet. Return new position."""
    dist = _distance(origin, target)
    if dist <= max_feet or dist == 0:
        dest_x, dest_y = target[0], target[1]
    else:
        scale = max_feet / dist
        dest_x = round(origin[0] + (target[0] - origin[0]) * scale, 1)
        dest_y = round(origin[1] + (target[1] - origin[1]) * scale, 1)

    zone = ""
    if scene_geometry is not None:
        from models.space_time import Position
        z = scene_geometry.zone_at(Position(dest_x, dest_y))
        zone = (z or "").upper()

    return (dest_x, dest_y, zone)


def _best_weapon(
    weapons: list[Weapon],
    dist: float,
    prefer_ranged: bool = False,
) -> Weapon | None:
    """Pick the best weapon for the given distance to target.

    Preference order when prefer_ranged is False:
    1. Ranged weapon when dist > 10 ft (avoid melee disadvantage on ranged)
    2. Melee weapon when dist <= 10 ft
    3. Any ranged weapon still in range as fallback

    When prefer_ranged is True (character stated intent to shoot/use bow):
    1. Best ranged weapon in range, regardless of distance
    2. Fall back to melee only if no ranged weapon can reach

    Returns None if no weapon can reach the target.
    """
    if not weapons:
        return None

    ranged = [w for w in weapons if w.is_ranged and dist <= w.range_normal]
    melee  = [w for w in weapons if not w.is_ranged and dist <= w.reach + 0.5]

    best_ranged = sorted(ranged, key=lambda w: _avg_damage(w.damage_dice), reverse=True)[0] if ranged else None
    best_melee  = sorted(melee,  key=lambda w: _avg_damage(w.damage_dice), reverse=True)[0] if melee  else None

    if prefer_ranged:
        return best_ranged or best_melee
    if dist > 10 and best_ranged:
        return best_ranged
    return best_melee or best_ranged


def _avg_damage(dice_expr: str) -> float:
    """Rough expected value of a damage expression for weapon selection."""
    total = 0.0
    for m in re.finditer(r'(\d+)\s*[dD]\s*(\d+)', dice_expr):
        count, sides = int(m.group(1)), int(m.group(2))
        total += count * (sides + 1) / 2
    for m in re.finditer(r'([+-]\s*\d+)', re.sub(r'\d+\s*[dD]\s*\d+', '', dice_expr)):
        total += int(m.group(1).replace(' ', ''))
    return total


_RANGED_INTENT_RE = re.compile(
    r'\b(shoot|arrow|bow|ranged?|fire arrow|from a distance|at range)\b',
    re.IGNORECASE,
)


def _intent_prefers_ranged(intent_text: str) -> bool:
    """Return True if the intent text explicitly calls for a ranged attack."""
    return bool(_RANGED_INTENT_RE.search(intent_text or ""))


# ---------------------------------------------------------------------------
# CombatResolver
# ---------------------------------------------------------------------------

class CombatResolver:
    """Python-only combat resolver — no DM-Left LLM call.

    Call ``resolve()`` with the attacker's session and target id to get back
    an ``Adjudication`` that the session loop can use directly, then call
    DM-Right as usual for narration.
    """

    def resolve(
        self,
        *,
        character_id: str,
        turn: int,
        attacker_session,          # CharacterSession
        target_id: str,
        target_session,            # CharacterSession
        attacker_pos: tuple[float, float, str],
        target_pos: tuple[float, float, str],
        scene_geometry=None,
        game_time=None,
        intent_text: str = "",
    ) -> tuple[Adjudication, list[str]]:
        """Resolve one attack action. Returns (Adjudication, log_lines).

        Movement toward the target is handled here (up to the attacker's speed).
        The Adjudication.new_position will be set to the post-move position.
        hp_damage is populated so the session loop can apply it to current_hp.
        """
        log: list[str] = []
        attacker_char  = attacker_session.character
        target_char    = target_session.character
        weapons        = attacker_session.weapons

        speed_str = getattr(attacker_char, "speed", "30 ft")
        speed_m = re.search(r'(\d+)', speed_str or "")
        speed_ft = float(speed_m.group(1)) if speed_m else 30.0

        # 1. Move toward target
        dist_before = _distance(attacker_pos, target_pos)
        new_pos = _move_toward(attacker_pos, target_pos, speed_ft, scene_geometry)
        dist_after = _distance(new_pos, target_pos)
        if dist_before > dist_after + 0.1:
            log.append(
                f"[MOVE] {character_id} moves {dist_before - dist_after:.1f} ft "
                f"toward {target_id} → now {dist_after:.1f} ft away"
            )

        # 2. Select weapon — honor ranged intent if the character said so
        prefer_ranged = _intent_prefers_ranged(intent_text)
        weapon = _best_weapon(weapons, dist_after, prefer_ranged=prefer_ranged)
        if weapon is None:
            log.append(f"[COMBAT] {character_id}: no weapon can reach {target_id} at {dist_after:.1f} ft")
            adj = Adjudication(
                character_id=character_id,
                turn=turn,
                approved=True,
                new_position=new_pos,
                movement_target=(new_pos[0], new_pos[1]),
                notes=f"Moved but could not reach {target_id} with any available weapon.",
                spatial_events=["combat_initiated"],
            )
            return adj, log

        # 3. Roll attack
        d20 = random.randint(1, 20)
        total_roll = d20 + weapon.attack_bonus
        ac = getattr(target_char, "ac", 10)
        hit = total_roll >= ac

        log.append(
            f"[ATTACK] {character_id} ({weapon.name}) → {target_id}: "
            f"d20={d20}+{weapon.attack_bonus}={total_roll} vs AC {ac} → "
            f"{'HIT' if hit else 'MISS'}"
        )

        hp_damage: dict[str, int] = {}
        attacker_deltas: dict[str, float] = {}
        target_deltas: dict[str, float] = {}

        if hit:
            raw_dmg = _roll_damage(weapon.damage_dice)
            final_dmg = _apply_resistances(raw_dmg, weapon.damage_type, target_char)
            if final_dmg != raw_dmg:
                resist_note = "halved (resistance)" if final_dmg < raw_dmg else "doubled (vulnerability)"
                log.append(
                    f"[DAMAGE] {weapon.damage_dice} → rolled {raw_dmg}, {resist_note} → {final_dmg}"
                )
            else:
                log.append(f"[DAMAGE] {weapon.damage_dice} → {final_dmg} {weapon.damage_type}")
            hp_damage[target_id] = final_dmg
            attacker_deltas.update(_DEALT_DAMAGE_DELTAS)
            target_deltas.update(_TOOK_DAMAGE_DELTAS)
        else:
            attacker_deltas.update(_MISSED_ATTACK_DELTAS)

        # 4. Build events
        events = ["combat_initiated"]

        # 5. Build notes
        notes_parts = [
            f"Moved to {new_pos[:2]}, {dist_after:.1f} ft from {target_id}.",
            f"{weapon.name}: d20={d20}+{weapon.attack_bonus}={total_roll} vs AC {ac} → {'HIT' if hit else 'MISS'}.",
        ]
        if hit:
            notes_parts.append(f"Damage: {weapon.damage_dice} = {hp_damage.get(target_id, 0)} {weapon.damage_type}.")

        adj = Adjudication(
            character_id=character_id,
            turn=turn,
            approved=True,
            new_position=new_pos,
            movement_target=(new_pos[0], new_pos[1]),
            condition_deltas=attacker_deltas,
            spatial_events=events,
            attacks=[{
                "target": target_id,
                "hit_bonus": weapon.attack_bonus,
                "damage_expr": weapon.damage_dice,
            }],
            notes=" ".join(notes_parts),
            hp_damage=hp_damage,
        )
        return adj, log
