"""Effect application — landing a Thing's Effects on a character.

Effects have two lifetimes (see the item-unification design):

* **thing-borne** — active only while the thing is wielded/worn (a weapon's
  ``damage``, armor's ``ac``). These already apply through the combat resolver
  and the AC calc off carry-state; they are NOT applied here.
* **character-borne** — transferred onto the eater when a consumable is used up.
  Eating destroys the vehicle; the payload (a heal, a neurochemical nudge, a
  satiety bump, a status) lands on the *character*, with its own lifetime. This
  module applies those.

Source-agnostic by design: a healing potion (arcane) and a loaf of bread
(mundane) run through the same pipe and differ only by ``Effect.source``.
"Magical" is a flavor tag on the effect, not a separate mechanism — so this is
also where enchantment payloads will land.
"""

from __future__ import annotations

from typing import Optional

from models.condition import DIMENSIONS


def apply_effect(cs, effect) -> Optional[str]:
    """Apply one character-borne :class:`~models.thing.Effect` to the character
    behind ``cs``. Returns a short past-tense note for narration, or ``None`` for
    effect kinds that are not character-borne (a weapon's ``damage``/``ac`` apply
    through combat, not here) or that could not land."""
    kind = getattr(effect, "kind", "")
    payload = getattr(effect, "payload", None) or {}
    char = getattr(cs, "character", None)

    if kind == "heal" and char is not None:
        amount = int(payload.get("amount", 0) or 0)
        before = int(getattr(char, "current_hp", 0) or 0)
        cap = int(getattr(char, "hp", 0) or 0) or (before + amount)
        char.current_hp = min(cap, before + amount)
        healed = char.current_hp - before
        return f"heals {healed} HP" if healed else None

    if kind == "neuro":
        cond = getattr(cs, "condition", None)
        dim = payload.get("dim")
        delta = float(payload.get("delta", 0) or 0)
        if cond is not None and dim in DIMENSIONS and hasattr(cond, "apply_delta"):
            cond.apply_delta({dim: delta})
            return f"{dim} {delta:+.2f}"
        return None

    if kind == "stat":
        # A non-neurochemical character stat (hunger/satiety/intoxication...) in
        # the condition's free-form `extensions` bucket. Clamped to [0, 1].
        cond = getattr(cs, "condition", None)
        name = str(payload.get("name", "")).strip()
        delta = float(payload.get("delta", 0) or 0)
        ext = getattr(cond, "extensions", None)
        if ext is not None and name:
            ext[name] = round(max(0.0, min(1.0, ext.get(name, 0.0) + delta)), 4)
            return f"{name} {delta:+.2f}"
        return None

    if kind == "status" and char is not None:
        name = str(payload.get("name", "")).strip()
        conds = getattr(char, "conditions", None)
        if name and conds is not None:
            if name not in conds:
                conds.append(name)
            return f"now {name}"
        return None

    # Unknown or thing-borne kinds (damage, ac, …) are not applied here.
    return None


def apply_thing_effects(cs, thing) -> list[str]:
    """Apply every character-borne Effect a ``thing`` carries onto the character
    (used when a consumable is eaten/drunk). Source-agnostic — a mundane and an
    arcane effect of the same kind land identically. Returns the narration notes
    for the effects that took hold."""
    notes: list[str] = []
    for effect in (getattr(thing, "effects", None) or []):
        note = apply_effect(cs, effect)
        if note:
            notes.append(note)
    return notes
