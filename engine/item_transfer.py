"""Item-transfer primitives and recipient resolution.

Extracted from engine.session (low-risk refactor): the leaf helpers for
naming/matching a transfer recipient and moving an item between holders. The
heavier orchestration (``_handle_item_transfer``) stays in session.py and
uses these. session.py re-exports these names, so existing
``from engine.session import _resolve_recipient_character`` etc. keep working.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # avoid a runtime import cycle (CharacterSession lives in session)
    from engine.session import CharacterSession
    from models.item import Item


# Words too generic to identify a specific party member.
_RECIPIENT_STOPWORDS = {
    "the", "a", "an", "to", "give", "given", "hand", "handed", "over", "off",
    "pass", "passes", "offer", "offers", "my", "his", "her", "their", "our",
    "this", "that", "it", "him", "them", "sir", "lady", "lord", "master",
    "mister", "miss", "and", "of", "with", "for", "i", "me", "you", "she",
    "he", "they", "we", "us", "drop", "take", "pick", "up", "down",
}


def _character_descriptor_tokens(cs: "CharacterSession") -> set[str]:
    """Build the set of tokens that may name/describe a character.

    Draws on id, name, race, class/role and scene handle so a recipient
    hint like "the cleric" or "Amara" or "the dwarf" resolves to the right
    party member. Generic stopwords are filtered out.
    """
    char = cs.character
    parts: list[str] = [
        char.id or "",
        char.name or "",
        char.race or "",
        getattr(char, "character_class", "") or "",
        getattr(char, "role", "") or "",
        cs.scene_handle or "",
    ]
    blob = " ".join(parts).lower()
    return {
        tok
        for tok in re.split(r"[^a-z0-9]+", blob)
        if tok and tok not in _RECIPIENT_STOPWORDS and len(tok) > 1
    }


def _resolve_recipient_character(
    intent_text: str,
    *,
    actor_id: str,
    characters: dict[str, "CharacterSession"],
    active_characters: set[str],
) -> Optional[str]:
    """Resolve a give/hand recipient from free-text intent to a character id.

    Scores each active character (other than the actor) by how many of its
    descriptor tokens — name, race, class/role, scene handle, id — appear in
    the intent text. Returns the id only when a single character is the
    strict best match; ambiguous or no match yields ``None`` so the caller
    narrates without transferring (no false hand-offs).
    """
    want = {
        tok
        for tok in re.split(r"[^a-z0-9]+", (intent_text or "").lower())
        if tok and tok not in _RECIPIENT_STOPWORDS and len(tok) > 1
    }
    if not want:
        return None
    best_id: Optional[str] = None
    best_score = 0
    tied = False
    for cid in sorted(active_characters):
        if cid == actor_id or cid not in characters:
            continue
        score = len(want & _character_descriptor_tokens(characters[cid]))
        if score > best_score:
            best_score, best_id, tied = score, cid, False
        elif score == best_score and score > 0:
            tied = True
    if best_score == 0 or tied:
        return None
    return best_id


def _apply_item_transfer(
    item: "Item",
    new_holder: Optional[str],
    *,
    characters: dict[str, "CharacterSession"],
    target_pos: Optional[tuple[float, float, str]] = None,
) -> None:
    """Move ``item`` to ``new_holder`` (or drop it when ``new_holder`` is None).

    Maintains both sides of ownership: the previous holder's inventory loses
    the id, the new holder's inventory gains it, and ``item.holder`` is set.
    When ``target_pos`` is given the item's position/zone are synced to it so
    a dropped or handed item sits where it should.
    """
    from models.space_time import Position

    old = item.holder
    if old and old in characters:
        inv = characters[old].character.inventory
        if item.id in inv:
            inv.remove(item.id)

    item.holder = new_holder

    if new_holder and new_holder in characters:
        inv = characters[new_holder].character.inventory
        if item.id not in inv:
            inv.append(item.id)

    if target_pos is not None:
        x, y, zone = target_pos
        item.position = Position(float(x), float(y))
        if zone:
            item.zone = zone


def _char_handle(cs: "CharacterSession", fallback: str) -> str:
    """Display name for a character: scene handle, then name, then id."""
    return cs.scene_handle or cs.character.name or fallback
