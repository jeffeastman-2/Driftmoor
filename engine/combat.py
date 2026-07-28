"""Combat resolution helpers.

Extracted from engine.session (low-risk refactor): parsing attack capability
from stat-block text, range enforcement, the d20-vs-AC attack resolver, and
hostile-target selection. Depends only on stdlib, models.space_time.Position,
and the shared dice roller. session.py re-exports these so the turn loop and
tests (test_combat_resolver) are unchanged.
"""

from __future__ import annotations

from engine.game_rng import rng
import re

from models.space_time import Position

from engine.dice import _roll_damage_expr


def _max_attacks(identity_text: str) -> int:
    """Return the maximum number of attacks per turn from a character's identity/stat block.

    Looks for a Multiattack entry (e.g. 'makes 2 attacks'). Defaults to 1.
    """
    t = identity_text or ""
    m = re.search(
        r'multiattack[^.\n]*makes\s+(\d+)\s+(?:\w+\s+)?attacks',
        t, re.IGNORECASE,
    )
    if m:
        return int(m.group(1))
    return 1


def _max_attack_range(identity_text: str) -> float:
    """Return the maximum attack range in feet from a character's identity text.

    Checks (in order): ranged weapon range, AoE radius, melee reach.
    Defaults to 5 ft (standard melee) if none found.
    """
    t = identity_text or ""
    # Ranged weapon: "range 150/600 ft" or "range 80/320"
    m = re.search(r'\brange\s+(\d+)/\d+', t, re.IGNORECASE)
    if m:
        return float(m.group(1))
    # Ranged weapon: "range 60 ft"
    m = re.search(r'\brange\s+(\d+)\s*ft', t, re.IGNORECASE)
    if m:
        return float(m.group(1))
    # AoE radius: "10ft radius" or "10 ft radius"
    m = re.search(r'(\d+)\s*ft\s+radius', t, re.IGNORECASE)
    if m:
        return float(m.group(1))
    # Melee reach: "reach 10 ft"
    m = re.search(r'\breach\s+(\d+)\s*ft', t, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return 5.0  # default melee reach


def _enforce_attack_range(
    hp_damage: dict[str, int],
    attacker_pos: tuple[float, float, str] | None,
    current_positions: dict[str, tuple[float, float, str]],
    max_range: float,
) -> dict[str, int]:
    """Remove hp_damage entries where the target is beyond the attacker's max range.

    Used to catch LLM arithmetic errors where the DM resolves melee attacks
    from a position that is actually out of reach.
    """
    import math
    if attacker_pos is None or not hp_damage:
        return hp_damage
    ax, ay = attacker_pos[0], attacker_pos[1]
    filtered: dict[str, int] = {}
    for target_id, dmg in hp_damage.items():
        tpos = current_positions.get(target_id)
        if tpos is None:
            filtered[target_id] = dmg  # target position unknown, keep it
            continue
        dist = math.hypot(tpos[0] - ax, tpos[1] - ay)
        if dist <= max_range + 0.5:  # 0.5 ft tolerance for floating point
            filtered[target_id] = dmg
        # else: silently drop — attacker could not reach this target
    return filtered


def _resolve_attacks(
    attacks: list[dict],
    character_id: str,
    attacker_pos: tuple[float, float, str] | None,
    current_positions: dict[str, tuple[float, float, str]],
    characters: dict,
    max_range: float,
    scene_geometry=None,
) -> tuple[dict[str, int], list[str]]:
    """Roll d20+bonus vs target AC, roll damage on hit. Returns (hp_damage, log_lines).

    hp_damage: target_id → total damage this turn
    log_lines: human-readable results injected into turn history for the DM ledger
    """
    import math
    hp_damage: dict[str, int] = {}
    log_lines: list[str] = []

    for atk in attacks:
        target_id = atk.get("target", "")
        hit_bonus = atk.get("hit_bonus", 0)
        damage_expr = atk.get("damage_expr", "1d4")

        # Fuzzy-match target ID: if DM omitted the numeric suffix (e.g. "shadowbeast"
        # instead of "shadowbeast_1"), find the first character whose id starts with it.
        if target_id not in characters:
            matched = next(
                (cid for cid in characters if cid.startswith(target_id) or target_id.startswith(cid)),
                None,
            )
            if matched:
                log_lines.append(
                    f"[ATTACK] fuzzy-matched target '{target_id}' → '{matched}'"
                )
                target_id = matched
            else:
                log_lines.append(f"[ATTACK] {character_id} → {target_id}: unknown target, skipped")
                continue

        # Range check and LOS check
        if attacker_pos is not None:
            tpos = current_positions.get(target_id)
            if tpos is not None:
                dist = math.hypot(tpos[0] - attacker_pos[0], tpos[1] - attacker_pos[1])
                if dist > max_range + 0.5:
                    log_lines.append(
                        f"[ATTACK] {character_id} → {target_id}: out of range "
                        f"({dist:.1f} ft > {max_range} ft), skipped"
                    )
                    continue
                # LOS check
                if scene_geometry is not None:
                    a_pos = Position(attacker_pos[0], attacker_pos[1])
                    t_pos = Position(tpos[0], tpos[1])
                    if not scene_geometry.can_see(a_pos, t_pos):
                        log_lines.append(
                            f"[ATTACK] {character_id} → {target_id}: no line of sight "
                            f"({scene_geometry.zone_at(a_pos) or '?'} → "
                            f"{scene_geometry.zone_at(t_pos) or '?'}), skipped"
                        )
                        continue

        target_char = characters[target_id].character
        ac = getattr(target_char, "ac", 10)
        d20 = rng().randint(1, 20)
        total_roll = d20 + hit_bonus

        if total_roll >= ac:
            dmg = _roll_damage_expr(damage_expr)
            hp_damage[target_id] = hp_damage.get(target_id, 0) + dmg
            log_lines.append(
                f"[ATTACK] {character_id} → {target_id}: "
                f"d20={d20}+{hit_bonus}={total_roll} vs AC {ac} → HIT for {dmg} ({damage_expr})"
            )
        else:
            log_lines.append(
                f"[ATTACK] {character_id} → {target_id}: "
                f"d20={d20}+{hit_bonus}={total_roll} vs AC {ac} → MISS"
            )

    return hp_damage, log_lines


def _find_combat_target(
    intent,
    attacker_id: str,
    characters: dict,
    current_positions: dict,
    active_characters: set[str],
) -> str | None:
    """Return the best target character_id for an attack.

    Priority:
    1. intent.interaction_target if it names an active hostile character
    2. Nearest active hostile character
    Returns None if no valid target exists.
    """
    import math

    attacker_faction = getattr(characters[attacker_id].character, "faction", "party")

    # Collect active hostiles (opposite faction)
    def is_hostile_to_attacker(cid: str) -> bool:
        if cid == attacker_id:
            return False
        f = getattr(characters[cid].character, "faction", "party")
        # hostile faction vs party faction, or party attacking hostile
        return (attacker_faction == "hostile") != (f == "hostile")

    hostiles = [
        cid for cid in active_characters
        if cid in characters and is_hostile_to_attacker(cid)
    ]
    if not hostiles:
        return None

    # 1. Check intent.interaction_target
    hint = (intent.interaction_target or "").strip().lower()
    if hint:
        # Fuzzy match: exact or prefix
        for cid in hostiles:
            if cid.lower() == hint or cid.lower().startswith(hint) or hint.startswith(cid.lower()):
                return cid

    # 2. Nearest hostile
    attacker_pos = current_positions.get(attacker_id)
    if attacker_pos is None:
        return hostiles[0]

    def dist_to(cid: str) -> float:
        pos = current_positions.get(cid)
        if pos is None:
            return 9999.0
        return math.hypot(pos[0] - attacker_pos[0], pos[1] - attacker_pos[1])

    return min(hostiles, key=dist_to)
