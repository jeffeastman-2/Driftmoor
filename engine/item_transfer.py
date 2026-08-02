"""Item-transfer primitives and recipient resolution.

Extracted from engine.session (low-risk refactor): the leaf helpers for
naming/matching a transfer recipient and moving an item between holders. The
heavier orchestration (``_handle_item_transfer``) stays in session.py and
uses these. session.py re-exports these names, so existing
``from engine.session import _resolve_recipient_character`` etc. keep working.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
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

    This is the *possession* leg only: the previous holder's inventory loses the
    id, the new holder's inventory gains it, and ``item.holder`` is set. When
    ``target_pos`` is given the item's position/zone are synced to it so a
    dropped or handed item sits where it should. Ownership (``item.owner``) and
    coin are handled by :func:`transfer_thing`, not here.
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


@dataclass
class TransferResult:
    """Outcome of :func:`transfer_thing`. ``reason`` is empty on success, else a
    machine code the caller can branch on ("cannot_afford", "invalid_amount")."""
    ok: bool
    reason: str = ""


def transfer_coins(
    amount_cp: int,
    *,
    from_id: str,
    to_id: str,
    characters: dict[str, "CharacterSession"],
) -> TransferResult:
    """Atomically move purse currency between two characters."""
    payer_cs = characters.get(from_id)
    payee_cs = characters.get(to_id)
    payer = getattr(payer_cs, "character", None)
    payee = getattr(payee_cs, "character", None)
    if amount_cp <= 0:
        return TransferResult(False, "invalid_amount")
    if payer is None or payee is None:
        return TransferResult(False, "invalid_party")
    if not payer.can_afford(amount_cp):
        return TransferResult(False, "cannot_afford")
    payer.debit(amount_cp)
    payee.credit(amount_cp)
    return TransferResult(True)


def transfer_thing(
    thing: "Item",
    *,
    from_id: Optional[str],
    to_id: Optional[str],
    characters: dict[str, "CharacterSession"],
    move_ownership: bool,
    move_possession: bool = True,
    coin_cp: int = 0,
    target_pos: Optional[tuple[float, float, str]] = None,
) -> TransferResult:
    """The one transfer primitive: move any subset of {ownership, possession,
    coin} between two parties, **atomically**.

    The item goes from ``from_id`` to ``to_id``. When ``coin_cp`` is positive the
    item *recipient* (``to_id``) pays that many copper to the item *giver*
    (``from_id``) — the buy/sell shape (whoever receives the item pays for it).
    Nothing mutates unless the whole transfer can complete: if the payer can't
    afford the coin, the call fails and leaves everything untouched.

    All five verbs are configurations of this:

    * give   — ``move_ownership=True``, ``coin_cp=0``
    * drop   — ``move_ownership=False``, ``to_id=None``, ``coin_cp=0``
    * take   — ``move_ownership=(thing.owner is None)`` (own unclaimed loot; an
      owned thing keeps its owner — possession without ownership is theft)
    * buy    — item seller→buyer, ``move_ownership=True``, ``coin_cp=price``
    * sell   — item seller→buyer(shop), ``move_ownership=True``, ``coin_cp=bid``
    * steal  — ``move_possession`` only, ``move_ownership=False``, ``coin_cp=0``
    """
    def _char(cid: Optional[str]):
        cs = characters.get(cid) if cid else None
        return getattr(cs, "character", None) if cs else None

    # Gate on affordability BEFORE mutating anything (atomicity).
    if coin_cp:
        if coin_cp < 0:
            return TransferResult(False, "invalid_amount")
        payer = _char(to_id)  # the item recipient pays the item giver
        if payer is None or not payer.can_afford(coin_cp):
            return TransferResult(False, "cannot_afford")

    # Commit — reached only when the whole transfer can complete.
    if move_possession:
        _apply_item_transfer(thing, to_id, characters=characters, target_pos=target_pos)
    if move_ownership:
        thing.owner = to_id
    if coin_cp:
        _char(to_id).debit(coin_cp)
        payee = _char(from_id)
        if payee is not None:
            payee.credit(coin_cp)
    return TransferResult(True)


def _char_handle(cs: "CharacterSession", fallback: str) -> str:
    """Display name for a character: scene handle, then name, then id."""
    return cs.scene_handle or cs.character.name or fallback
