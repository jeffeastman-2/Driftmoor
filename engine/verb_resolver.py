"""Phase 2b: match player intent to authored item interactions.

Given a player's ``ActionIntent`` (the natural-language ``intent`` plus the
``interaction_target`` field), look up the corresponding ``Item`` in the
character's current zone and return the DM-authored ``Interaction`` (if
any). The session loop injects the interaction's response into the
narrator's ``resolution_log`` and into ``recent_events`` so subsequent
turns build on Python-verified findings instead of LLM hallucinations.

Scope (Phase 2b): examine-class verbs only — ``examine``, ``search``,
``inspect``, ``study``, ``look (at)``, ``investigate``, plus aliases the
authors used in ``CONTENTS.md``. Verbs that mutate state (``press``,
``pickup``, ``read``) will land in later phases together with the state
machine they require.
"""

from __future__ import annotations

import re
from typing import Optional

from models.item import Interaction, Item


# Canonical verb -> phrases that should resolve to it. Order matters:
# the first canonical that matches wins. Each phrase is matched as a
# whole word (or whole multi-word run) against the intent text.
_VERB_LEXICON: list[tuple[str, list[str]]] = [
    ("examine", ["examine", "inspect", "study", "scrutinize", "observe", "look at", "look over", "look closer"]),
    ("search", ["search", "rummage", "rifle", "investigate", "comb"]),
    ("read", ["read", "decipher", "transcribe"]),
    ("press", ["press", "push", "depress", "tap", "trigger", "activate"]),
]


def _detect_verb(intent_text: str) -> Optional[str]:
    """Return the canonical verb present in ``intent_text``, or None.

    Multi-word phrases are matched first (longest-first within a canonical
    group) so that e.g. ``"look at"`` wins over ``"look"`` alone.
    """
    if not intent_text:
        return None
    text = intent_text.lower()
    for canonical, phrases in _VERB_LEXICON:
        for phrase in sorted(phrases, key=len, reverse=True):
            pattern = r"\b" + re.escape(phrase) + r"\b"
            if re.search(pattern, text):
                return canonical
    return None


def _normalize_target(s: str) -> str:
    """Lower-case, strip leading articles and trailing punctuation."""
    t = s.strip().lower().rstrip(".,;:!?")
    for art in ("the ", "a ", "an "):
        if t.startswith(art):
            t = t[len(art):]
            break
    return t


def _match_item(
    target: str, items: dict[str, Item], zone: Optional[str]
) -> Optional[Item]:
    """Resolve ``target`` (the ``Interact:`` field) to an Item.

    Restricts matches to the actor's current zone when ``zone`` is given.
    Tries id-exact, label-exact, then substring-on-label, then
    substring-on-id.
    """
    if not target or not items:
        return None
    t = _normalize_target(target)
    if not t:
        return None
    z = (zone or "").upper()
    candidates: list[Item] = [
        it for it in items.values()
        if not z or (it.zone and it.zone.upper() == z)
    ]
    # Exact id or label
    for it in candidates:
        if it.id.lower() == t:
            return it
        if it.label and it.label.lower() == t:
            return it
    # Substring on label, then id (longest label first to prefer specifics)
    by_label = sorted(
        (it for it in candidates if it.label),
        key=lambda it: len(it.label),
        reverse=True,
    )
    for it in by_label:
        if it.label.lower() in t or t in it.label.lower():
            return it
    for it in candidates:
        if it.id.lower() in t:
            return it
    return None


def _pick_by_condition(
    matches: list[Interaction], item_state: Optional[dict[str, str]]
) -> Interaction:
    """Choose among same-verb interactions using the item's runtime state.

    If ``item_state`` contains a key/value whose value appears in an
    interaction's ``condition`` text, prefer that match. Otherwise prefer
    the first unconditional match, falling back to the first listed.
    """
    if item_state:
        state_blob = " ".join(f"{k} {v}".lower() for k, v in item_state.items())
        for m in matches:
            if m.condition and all(
                tok in state_blob for tok in m.condition.lower().split()
                if tok.isalpha() and len(tok) > 2
            ):
                return m
    for m in matches:
        if not m.condition:
            return m
    return matches[0]


def resolve_item_interaction(
    *,
    intent_text: str,
    interaction_target: Optional[str],
    items: Optional[dict[str, Item]],
    character_zone: Optional[str],
) -> Optional[tuple[Item, Interaction]]:
    """Match a player's intent + interaction_target to an authored Interaction.

    Returns ``(item, interaction)`` when a match is found, else ``None``.
    Falls back to ``examine`` when no examine-class verb is detected but
    an item target was named (the common "Interact: Drag marks" case).
    """
    if not items or not interaction_target:
        return None
    item = _match_item(interaction_target, items, character_zone)
    if item is None:
        return None
    verb = _detect_verb(intent_text or "") or "examine"
    matches = _find_by_verb(item, verb)
    if not matches and verb != "examine":
        matches = _find_by_verb(item, "examine")
    if not matches:
        return None
    return item, _pick_by_condition(matches, item.state)


def _find_by_verb(item: Item, verb: str) -> list[Interaction]:
    """Like ``Item.find_interactions`` but tolerant of multi-word verbs.

    Authors sometimes write ``examine without disturbing`` or
    ``dig out``; this helper also matches when the interaction's verb
    *starts with* the canonical verb token.
    """
    direct = item.find_interactions(verb)
    if direct:
        return direct
    v = verb.lower()
    return [
        it for it in item.interactions
        if it.verb.lower().split() and it.verb.lower().split()[0] == v
    ]
