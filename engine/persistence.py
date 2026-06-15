"""Checkpoint serialization helpers.

Extracted from engine.session (low-risk refactor): the pure (de)serialization
of party-examination state, spell runtime state, item ownership, and the
checkpoint filename. These convert engine state to/from JSON-ready dicts;
the IO orchestrators that drive them (_save_turn / load_resume_state /
restore_item_ownership) stay in session for now (tightly coupled to turn
state). session.py re-exports these so the orchestrators and tests
(test_session, test_inventory) are unchanged.
"""

from __future__ import annotations

from typing import Optional

from models.space_time import GameTime

from engine.spell_resolver import ActiveSpellEffect, SpellRuntimeState
from engine.text_util import _normalize_target_name


def _shared_exam_key(zone: str | None, target: str | None) -> tuple[str, str] | None:
    """Build a normalized key for party-shared examination state."""
    z = (zone or "").upper().strip()
    t = _normalize_target_name(target)
    if not z or not t:
        return None
    return z, t


def _serialize_party_examination_state(
    state: dict[tuple[str, str], dict],
) -> dict[str, dict]:
    """Serialize tuple-keyed party examination state for JSON checkpoints."""
    out: dict[str, dict] = {}
    for (zone, target), meta in state.items():
        out[f"{zone}::{target}"] = {
            "label": str(meta.get("label", "")),
            "summary": str(meta.get("summary", "")),
            "by": str(meta.get("by", "")),
            "last_turn": int(meta.get("last_turn", 0) or 0),
            "needs_followup": bool(meta.get("needs_followup", False)),
        }
    return out


def _deserialize_party_examination_state(raw: dict | None) -> dict[tuple[str, str], dict]:
    """Deserialize checkpointed party examination state."""
    state: dict[tuple[str, str], dict] = {}
    if not isinstance(raw, dict):
        return state
    for key, meta in raw.items():
        if not isinstance(key, str) or "::" not in key:
            continue
        zone, target = key.split("::", 1)
        norm = _shared_exam_key(zone, target)
        if norm is None:
            continue
        meta_dict = meta if isinstance(meta, dict) else {}
        state[norm] = {
            "label": str(meta_dict.get("label", "")),
            "summary": str(meta_dict.get("summary", "")),
            "by": str(meta_dict.get("by", "")),
            "last_turn": int(meta_dict.get("last_turn", 0) or 0),
            "needs_followup": bool(meta_dict.get("needs_followup", False)),
        }
    return state


def _serialize_spell_runtime_state(runtime: SpellRuntimeState) -> dict:
    """Serialize mutable spell runtime state for checkpoints."""
    return {
        "active_effects": [
            {
                "spell_name": effect.spell_name,
                "caster_id": effect.caster_id,
                "target_ids": list(effect.target_ids),
                "remaining_rounds": int(effect.remaining_rounds),
                "concentration": bool(effect.concentration),
            }
            for effect in runtime.active_effects
        ],
        "concentration_by_caster": {
            caster_id: effect.spell_name
            for caster_id, effect in runtime.concentration_by_caster.items()
        },
    }


def _deserialize_spell_runtime_state(raw: dict | None) -> SpellRuntimeState:
    """Deserialize checkpointed spell runtime state."""
    runtime = SpellRuntimeState()
    if not isinstance(raw, dict):
        return runtime

    for item in raw.get("active_effects", []) or []:
        if not isinstance(item, dict):
            continue
        effect = ActiveSpellEffect(
            spell_name=str(item.get("spell_name", "")),
            caster_id=str(item.get("caster_id", "")),
            target_ids=[str(t) for t in (item.get("target_ids") or [])],
            remaining_rounds=int(item.get("remaining_rounds", 0) or 0),
            concentration=bool(item.get("concentration", False)),
        )
        runtime.active_effects.append(effect)

    for caster_id, spell_name in (raw.get("concentration_by_caster") or {}).items():
        if not isinstance(caster_id, str) or not isinstance(spell_name, str):
            continue
        match = next(
            (
                e for e in runtime.active_effects
                if e.caster_id == caster_id and e.spell_name == spell_name
            ),
            None,
        )
        if match is not None:
            runtime.concentration_by_caster[caster_id] = match

    return runtime


def _checkpoint_filename(turn: int, game_time: Optional[GameTime] = None) -> str:
    """Build checkpoint filename from game time or turn number."""
    if game_time is not None:
        return f"day{game_time.day}_{game_time.hour:02d}h{game_time.minute:02d}m.json"
    return f"turn_{turn:04d}.json"


def _serialize_item_ownership(items: dict) -> dict:
    """Serialize ownership of every currently-held item for checkpoints.

    Only items with a ``holder`` are recorded (loose scene items are
    reconstructed from scene contents on load). Each entry keeps the
    holder plus the item's position/zone so a resumed session places the
    item exactly where it was carried/handed.
    """
    out: dict = {}
    for iid, it in (items or {}).items():
        holder = getattr(it, "holder", None)
        if not holder:
            continue
        pos = getattr(it, "position", None)
        out[iid] = {
            "holder": str(holder),
            "x": float(pos.x) if pos is not None else None,
            "y": float(pos.y) if pos is not None else None,
            "zone": getattr(it, "zone", None),
        }
    return out
