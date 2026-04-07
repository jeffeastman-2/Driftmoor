"""Player-Left and Player-Right role implementations.

Player-Left:  Generates structured action intent from character state and context.
              In production, calls an LLM to reason about what the character should do.

Player-Right: Generates in-character prose (INTERNAL/BODY_LANGUAGE/SPOKEN/ACTION)
              from the action intent and character context.
              In production, calls an LLM to write the four-section response.

Both roles are async.  When call_llm is None, stub behaviour returns
minimal valid data.  When call_llm is provided it is awaited as:
    await call_llm(system_prompt, user_message) -> str
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class RoleContext:
    """Assembled context for a player role LLM call."""
    character_id: str
    turn: int
    condition_text: str   # Rendered neurochemical state
    scene_context: str    # Zone, occupancy, visible history
    soul: str             # SOUL.md content
    identity: str         # IDENTITY.md content


@dataclass
class ActionIntent:
    """Output of Player-Left: what the character intends to do."""
    character_id: str
    turn: int
    intent: str
    movement_target: Optional[tuple[float, float, float]] = None
    interaction_target: Optional[str] = None


@dataclass
class CharacterOutput:
    """Output of Player-Right: in-character structured prose."""
    character_id: str
    turn: int
    internal: str = ""
    body_language: str = ""
    spoken: str = ""
    action: str = ""


# Type alias for the LLM callable: async (system_prompt, user_message) -> str
CallLLM = Callable[[str, str], Awaitable[str]]


# ---------------------------------------------------------------------------
# Player-Left
# ---------------------------------------------------------------------------

class PlayerLeft:
    """Generates structured action intent from character state and context.

    When call_llm is provided, sends context to an LLM and parses JSON.
    When call_llm is None, returns a default hold-position intent (stub).
    """

    def __init__(self, call_llm: Optional[CallLLM] = None):
        self._call_llm = call_llm

    def build_system_prompt(self, context: RoleContext) -> str:
        return (
            f"You are the strategic mind of {context.character_id}. "
            "Analyze the situation and your condition to determine "
            "the best action.\n\n"
            f"Your character:\n{context.soul}\n\n"
            "Respond ONLY with valid JSON "
            "(no markdown fencing, no commentary):\n"
            "{\n"
            '  "intent": "one sentence — what you will do this turn",\n'
            '  "movement_target": [x, y, z] or null,\n'
            '  "interaction_target": "character_id or item name" or null\n'
            "}"
        )

    def build_user_prompt(self, context: RoleContext) -> str:
        return (
            f"# Turn {context.turn}\n\n"
            f"## Condition\n{context.condition_text}\n\n"
            f"## Scene\n{context.scene_context}"
        )

    def parse_response(self, raw: str, context: RoleContext) -> ActionIntent:
        text = re.sub(r'```(?:json)?\s*', '', raw.strip())
        text = text.strip().rstrip('`')
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find('{'), text.rfind('}')
            if start != -1 and end > start:
                data = json.loads(text[start:end + 1])
            else:
                raise
        mt = data.get("movement_target")
        if mt is not None:
            mt = tuple(float(v) for v in mt)
        return ActionIntent(
            character_id=context.character_id,
            turn=context.turn,
            intent=data["intent"],
            movement_target=mt,
            interaction_target=data.get("interaction_target"),
        )

    async def generate_intent(self, context: RoleContext) -> ActionIntent:
        if self._call_llm is None:
            return ActionIntent(
                character_id=context.character_id,
                turn=context.turn,
                intent="observe surroundings and hold position",
            )
        system = self.build_system_prompt(context)
        user = self.build_user_prompt(context)
        raw = await self._call_llm(system, user)
        return self.parse_response(raw, context)


# ---------------------------------------------------------------------------
# Player-Right
# ---------------------------------------------------------------------------

class PlayerRight:
    """Generates in-character prose from action intent.

    When call_llm is provided, sends intent + context to an LLM and parses
    the four-section response (INTERNAL / BODY LANGUAGE / SPOKEN / ACTION).
    When call_llm is None, returns minimal prose echoing the intent (stub).
    """

    def __init__(self, call_llm: Optional[CallLLM] = None):
        self._call_llm = call_llm

    def build_system_prompt(self, context: RoleContext) -> str:
        return (
            f"{context.soul}\n\n"
            f"{context.identity}\n\n"
            f"You are {context.character_id}. "
            "Respond in character with exactly four sections:\n\n"
            "**INTERNAL** — Inner monologue (100-150 words). "
            "Reflect your condition state. "
            "Use phenomenologically rich language: "
            "perceptions, sensations, not analysis.\n\n"
            "**BODY LANGUAGE** — Physical state and demeanor "
            "(50-80 words).\n\n"
            "**SPOKEN** — Dialogue (optional; leave blank if silent).\n\n"
            "**ACTION** — What you do this turn (50-100 words). "
            "Be specific. Reference your zone and observable targets."
        )

    def build_user_prompt(
        self, intent: ActionIntent, context: RoleContext,
    ) -> str:
        return (
            f"# Turn {context.turn}\n\n"
            f"## Your intended action\n{intent.intent}\n\n"
            f"## Condition\n{context.condition_text}\n\n"
            f"## Scene\n{context.scene_context}"
        )

    def parse_response(self, raw: str, context: RoleContext) -> CharacterOutput:
        def _extract(text: str, section: str) -> str:
            pattern = rf"\*\*{section}\*\*\s*(?:—|:)?\s*(.*?)(?=\*\*|\Z)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else ""

        return CharacterOutput(
            character_id=context.character_id,
            turn=context.turn,
            internal=_extract(raw, "INTERNAL"),
            body_language=_extract(raw, "BODY LANGUAGE"),
            spoken=_extract(raw, "SPOKEN"),
            action=_extract(raw, "ACTION"),
        )

    async def generate_action(
        self, intent: ActionIntent, context: RoleContext,
    ) -> CharacterOutput:
        if self._call_llm is None:
            return CharacterOutput(
                character_id=context.character_id,
                turn=context.turn,
                internal=f"Considering: {intent.intent}",
                body_language="Alert, watchful.",
                spoken="",
                action=intent.intent,
            )
        system = self.build_system_prompt(context)
        user = self.build_user_prompt(intent, context)
        raw = await self._call_llm(system, user)
        return self.parse_response(raw, context)
