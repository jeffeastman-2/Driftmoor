"""DM-Left and DM-Right role implementations.

DM-Left:  Adjudicates character actions against game rules and spatial state.
          Validates movement, checks boundaries, computes condition deltas
          and spatial events. In production, calls an LLM with DM context.

DM-Right: Narrates adjudicated actions into scene prose visible to
          other characters. In production, calls an LLM to write narrative.

Both roles are async.  When call_llm is None, stub behaviour returns
minimal valid data.  When call_llm is provided it is awaited as:
    await call_llm(system_prompt, user_message) -> str
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional

from engine.player_router import CallLLM, CharacterOutput


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class Adjudication:
    """Output of DM-Left: rules enforcement and state changes."""
    character_id: str
    turn: int
    approved: bool = True
    modified_action: Optional[str] = None
    position_delta: Optional[tuple[float, float, float]] = None
    condition_deltas: dict[str, float] = field(default_factory=dict)
    spatial_events: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Narration:
    """Output of DM-Right: narrative prose."""
    character_id: str
    turn: int
    prose: str = ""
    visible_to: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# DM-Left
# ---------------------------------------------------------------------------

class DMLeft:
    """Adjudicates character actions against game rules and spatial state.

    When call_llm is provided, sends action + game state to an LLM.
    When call_llm is None, approves all actions with no changes (stub).
    """

    def __init__(self, call_llm: Optional[CallLLM] = None):
        self._call_llm = call_llm

    def build_system_prompt(self) -> str:
        return (
            "You are the rules-adjudication DM for a D&D 5e session. "
            "Evaluate the character's proposed action against game rules, "
            "spatial constraints, and the current game state.\n\n"
            "Respond ONLY with valid JSON "
            "(no markdown fencing, no commentary):\n"
            "{\n"
            '  "approved": true or false,\n'
            '  "modified_action": "rewritten action if rejected, else null",\n'
            '  "position_delta": [dx, dy, dz] or null,\n'
            '  "condition_deltas": {"dopamine": 0.1, "cortisol": -0.05},\n'
            '  "spatial_events": ["enters_fey_glade"],\n'
            '  "notes": "brief adjudication notes"\n'
            "}"
        )

    def build_user_prompt(
        self,
        character_output: CharacterOutput,
        game_state_summary: str,
        geometry_summary: str,
    ) -> str:
        return (
            f"# Character: {character_output.character_id} "
            f"(Turn {character_output.turn})\n\n"
            f"## Proposed Output\n"
            f"INTERNAL: {character_output.internal}\n"
            f"BODY LANGUAGE: {character_output.body_language}\n"
            f"SPOKEN: {character_output.spoken}\n"
            f"ACTION: {character_output.action}\n\n"
            f"## Game State\n{game_state_summary}\n\n"
            f"## Spatial Geometry\n{geometry_summary}"
        )

    def parse_response(
        self, raw: str, character_id: str, turn: int,
    ) -> Adjudication:
        text = re.sub(r'```(?:json)?\s*', '', raw.strip())
        text = text.strip().rstrip('`')

        def _try_parse(s: str) -> dict:
            s = re.sub(r',\s*([}\]])', r'\1', s)
            return json.loads(s)

        try:
            data = _try_parse(text)
        except json.JSONDecodeError:
            start, end = text.find('{'), text.rfind('}')
            if start != -1 and end > start:
                data = _try_parse(text[start:end + 1])
            else:
                raise
        pd = data.get("position_delta")
        if pd is not None:
            if any(v is None for v in pd):
                pd = None
            else:
                pd = tuple(float(v) for v in pd)
        return Adjudication(
            character_id=character_id,
            turn=turn,
            approved=data.get("approved", True),
            modified_action=data.get("modified_action"),
            position_delta=pd,
            condition_deltas=data.get("condition_deltas", {}),
            spatial_events=data.get("spatial_events", []),
            notes=data.get("notes", ""),
        )

    async def adjudicate(
        self,
        character_output: CharacterOutput,
        game_state_summary: str,
        geometry_summary: str,
    ) -> Adjudication:
        if self._call_llm is None:
            return Adjudication(
                character_id=character_output.character_id,
                turn=character_output.turn,
                approved=True,
            )
        system = self.build_system_prompt()
        user = self.build_user_prompt(
            character_output, game_state_summary, geometry_summary,
        )
        raw = await self._call_llm(system, user)
        return self.parse_response(
            raw, character_output.character_id, character_output.turn,
        )


# ---------------------------------------------------------------------------
# DM-Right
# ---------------------------------------------------------------------------

class DMRight:
    """Narrates adjudicated actions into scene prose.

    When call_llm is provided, sends adjudication + output to an LLM.
    When call_llm is None, returns a minimal one-line narration (stub).
    """

    def __init__(self, call_llm: Optional[CallLLM] = None):
        self._call_llm = call_llm

    def build_system_prompt(self) -> str:
        return (
            "You are the narrative voice of the DM. Write 2-4 sentences "
            "of vivid third-person, present-tense prose describing what "
            "happens. Do not include game mechanics, dice results, or "
            "meta-commentary. Focus on sensory detail and atmosphere."
        )

    def build_user_prompt(
        self,
        adjudication: Adjudication,
        character_output: CharacterOutput,
        scene_history: str,
    ) -> str:
        status = "APPROVED" if adjudication.approved else "MODIFIED"
        mod = ""
        if adjudication.modified_action:
            mod = f"\nModified to: {adjudication.modified_action}"
        notes = (
            f"\nNotes: {adjudication.notes}" if adjudication.notes else ""
        )
        history_block = (
            f"\n\n## Scene so far\n{scene_history}" if scene_history else ""
        )
        return (
            f"# Character: {character_output.character_id} "
            f"(Turn {character_output.turn})\n\n"
            f"## What they did\n{character_output.action}\n\n"
            f"## Adjudication: {status}{mod}{notes}{history_block}"
        )

    def parse_response(
        self, raw: str, character_id: str, turn: int,
    ) -> Narration:
        return Narration(
            character_id=character_id,
            turn=turn,
            prose=raw.strip(),
            visible_to=[],
        )

    async def narrate(
        self,
        adjudication: Adjudication,
        character_output: CharacterOutput,
        scene_history: str,
    ) -> Narration:
        if self._call_llm is None:
            action_text = character_output.action or "(no action)"
            return Narration(
                character_id=adjudication.character_id,
                turn=adjudication.turn,
                prose=f"{character_output.character_id} {action_text}.",
                visible_to=[],
            )
        system = self.build_system_prompt()
        user = self.build_user_prompt(
            adjudication, character_output, scene_history,
        )
        raw = await self._call_llm(system, user)
        return self.parse_response(
            raw, adjudication.character_id, adjudication.turn,
        )
