"""Immediate dialogue-only responses outside combat initiative."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SocialExchangeSchedule:
    """Tracks NPC exploration slots consumed by immediate dialogue replies."""

    consumed: set[str] = field(default_factory=set)

    def mark_response(self, character_id: str) -> None:
        self.consumed.add(character_id)

    def suppress_slot(self, character_id: str, *, in_combat: bool) -> bool:
        if in_combat:
            self.consumed.clear()
            return False
        if character_id not in self.consumed:
            return False
        self.consumed.remove(character_id)
        return True


def directed_social_target(
    utterance: str,
    *,
    speaker_id: str,
    visible_ids: set[str],
    characters: dict,
) -> Optional[str]:
    """Resolve an addressed NPC, inferring the sole visible NPC when safe.

    ``utterance`` is already structured quoted speech from the transport, so a
    declarative introduction or answer is just as conversational as a question.
    With several visible NPCs we still require an explicit name and refuse to
    invent an addressee.
    """
    text = (utterance or "").strip()
    if not text:
        return None
    candidates = []
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower())
    for cid in sorted(visible_ids):
        if cid == speaker_id or cid not in characters:
            continue
        cs = characters[cid]
        # Transport-backed characters own their own words; never synthesize an
        # immediate answer on another human player's behalf.
        if (getattr(cs, "player_transport", "llm") or "llm").lower() != "llm":
            continue
        candidates.append(cid)
        names = {
            cid.replace("_", " ").lower(),
            (getattr(getattr(cs, "character", None), "name", "") or "").lower(),
            (getattr(cs, "scene_handle", "") or "").lower(),
        }
        if any(name and re.search(rf"\b{re.escape(name)}\b", normalized)
               for name in names):
            return cid
    return candidates[0] if len(candidates) == 1 else None


async def generate_social_reply(
    *, turn_cycle, target_id: str, target_cs, speaker_handle: str,
    utterance: str, scene_context: str,
) -> str:
    """Ask the target NPC's configured model for one dialogue-only response."""
    roles = turn_cycle._roles_for(target_id)
    call_llm = roles.player_right._call_llm or roles.player_left._call_llm
    handle = target_cs.scene_handle or target_cs.character.name or target_id
    if call_llm is None:
        return ""
    system = (
        f"{target_cs.soul}\n\n{target_cs.identity}\n\n"
        f"You are {handle}. Reply immediately and in character to a person who "
        "just addressed you. Output dialogue only: one or two concise sentences, "
        "with no narration, labels, markdown, quotation marks, movement, object "
        "use, or physical action. You may answer, evade, refuse, or remain terse."
    )
    user = (
        f"Scene context:\n{scene_context}\n\n"
        f'{speaker_handle} says: "{utterance}"\n\nRespond as {handle}.'
    )
    raw = (await call_llm(system, user) or "").strip()
    # Tolerate a model adding a SPOKEN label despite the output contract.
    match = re.search(r"(?:\*\*)?SPOKEN(?:\*\*)?\s*(?:—|:)?\s*(.+)", raw,
                      re.IGNORECASE | re.DOTALL)
    reply = match.group(1).strip() if match else raw
    return reply.strip().strip('"“”')
