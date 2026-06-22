"""Phase 3b: dormancy + activation triggers for non-player characters.

Creatures (and NPCs) may declare an ``activation`` trigger in their
scene-config block. Until the trigger fires they are *dormant*:

- Excluded from initiative — they take no turns.
- Excluded from every other character's perception.
- Not narrated, not transcribed, not surfaced in the scene story.

When the engine detects the trigger condition it adds the character to
``active_characters`` and emits an event so opponents have Python-verified
context for the new presence.

Supported trigger grammars (Phase 3b):

- ``always`` — active from turn 1 (default; matches pre-3b behaviour).
- ``zone_entry:<Zone Name>`` — activate when any character whose
  ``faction`` differs from this character's faction is currently inside
  the named zone (case-insensitive).
- ``door_open:<door_id>`` — activate when a state_resolver door_open
  side effect fires (door id is currently informational; we have one
  door, but the grammar is forward-compatible).

Triggers are evaluated by ``check_activations``, which the session
loop invokes (a) after position updates and (b) after door state
changes.
"""

from __future__ import annotations

from typing import Iterable, Optional


def _zone_entry_target(activation: str) -> Optional[str]:
    if activation.startswith("zone_entry:"):
        return activation[len("zone_entry:"):].strip()
    return None


def _door_open_target(activation: str) -> Optional[str]:
    if activation.startswith("door_open:"):
        return activation[len("door_open:"):].strip()
    return None


def initial_dormant_set(characters: dict) -> set[str]:
    """Return ids of characters whose activation is not ``always``."""
    dormant: set[str] = set()
    for cid, cs in characters.items():
        activation = (getattr(cs, "activation", "always") or "always").strip()
        if activation and activation.lower() != "always":
            dormant.add(cid)
    return dormant


def check_activations(
    *,
    characters: dict,
    active_characters: set[str],
    current_positions: dict[str, tuple[float, float, str]],
    door_events: Iterable[dict] = (),
) -> list[tuple[str, str]]:
    """Promote any dormant character whose activation trigger now fires.

    Mutates ``active_characters`` in place. Returns a list of
    ``(character_id, reason)`` tuples for the triggers that fired so the
    caller can append events to ``recent_events``.
    """
    fired: list[tuple[str, str]] = []
    door_event_types = {ev.get("type") for ev in door_events if ev}
    for cid, cs in characters.items():
        if cid in active_characters:
            continue
        # A defeated character (0 HP) has left the fight for good. Without this
        # guard a creature with a zone_entry/door_open trigger is re-added every
        # turn while an enemy lingers in its trigger zone — so a dead spider
        # stays "in the scene" and combat never ends. ("always" creatures are
        # already protected by the branch below; this covers the triggered ones.)
        if getattr(getattr(cs, "character", None), "current_hp", 1) <= 0:
            continue
        activation = (getattr(cs, "activation", "always") or "always").strip()
        if not activation or activation.lower() == "always":
            # "always" creatures are never dormant in the first place,
            # and a character removed from active_characters (e.g. exited
            # the scene, died) must NOT be silently revived here.
            continue

        zone = _zone_entry_target(activation)
        if zone is not None:
            target = zone.upper()
            my_faction = getattr(cs.character, "faction", "")
            for other_id, pos in current_positions.items():
                if other_id == cid:
                    continue
                other_cs = characters.get(other_id)
                if other_cs is None:
                    continue
                other_faction = getattr(other_cs.character, "faction", "")
                if other_faction == my_faction:
                    continue
                if pos and len(pos) >= 3 and (pos[2] or "").upper() == target:
                    active_characters.add(cid)
                    fired.append((cid, f"zone_entry:{zone}"))
                    break
            continue

        door_id = _door_open_target(activation)
        if door_id is not None:
            if "door_open" in door_event_types:
                active_characters.add(cid)
                fired.append((cid, f"door_open:{door_id}"))
            continue

    return fired
