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

import random
import re
from dataclasses import dataclass, field
from typing import Optional

from engine.player_router import CallLLM, CharacterOutput


def _roll_dice(n: int = 8, sides: int = 20) -> list[int]:
    """Roll n dice with the given number of sides using Python's CSPRNG."""
    return [random.randint(1, sides) for _ in range(n)]


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
    new_position: Optional[tuple[float, float, str]] = None
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
            "## Dice Rolls\n"
            "A set of pre-rolled d20 results will be provided in the user "
            "prompt under '## Dice Rolls'. You MUST use these rolls in order "
            "for any saving throws, attack rolls, or contested checks — do NOT "
            "invent or assume your own values. Consume from left to right; "
            "unused rolls are discarded.\n\n"
            "## Spatial Boundaries\n"
            "The geometry includes named boundaries that physically block "
            "certain creature types. You must enforce these strictly:\n"
            "  - If an action would move a blocked creature across a boundary, "
            "reject it (APPROVED: No) and explain in NOTES.\n"
            "  - Effects projected FROM a blocked creature (shadow tendrils, "
            "magical auras, reach attacks) also cannot cross the boundary — "
            "treat them as blocked at the boundary line.\n"
            "  - When a partially-blocked creature ATTEMPTS to cross (saves "
            "allowed at dusk/darkness per geometry rules), use the next "
            "pre-rolled d20 to resolve the saving throw, state the DC, "
            "the roll, and the result in NOTES.\n"
            "    CRITICAL: APPROVED controls whether the position change "
            "actually takes effect in the engine. If the save SUCCEEDS, "
            "set APPROVED: Yes so the creature's position updates. "
            "If the save FAILS, set APPROVED: No. "
            "Emitting boundary_crossed in EVENTS without APPROVED: Yes "
            "does nothing — the creature stays where it was.\n\n"
            "Respond with exactly these labeled sections "
            "(no markdown fencing):\n\n"
            "**APPROVED** — Yes or No.\n"
            "**MODIFIED ACTION** — Rewritten action if rejected, "
            "otherwise \"none\".\n"
            "**NEW POSITION** — Character's absolute position after this "
            "action as x=<val>, y=<val>, zone=<ZONE> "
            "(or \"none\" if the character did not move). "
            "When a boundary crossing is approved you MUST emit "
            "the new coordinates inside the boundary here.\n"
            "**CONDITION** — Neurochemical deltas as "
            "dimension +/-value, comma separated "
            "(e.g. \"dopamine +0.1, cortisol -0.05\") "
            "or \"none\".\n"
            "**EVENTS** — Spatial events, comma separated "
            "(e.g. \"enters_fey_glade, crosses_boundary\") "
            "or \"none\".\n"
            "  Important events to emit:\n"
            "  - combat_initiated: when a character uses a weapon "
            "or offensive spell against an opponent.\n"
            "  - exits_scene: when a character leaves the scene "
            "area entirely (fleeing, retreating, departing).\n"
            "**NOTES** — Brief adjudication reasoning, including any "
            "dice rolls used and their outcomes."
        )

    def build_user_prompt(
        self,
        character_output: CharacterOutput,
        game_state_summary: str,
        geometry_summary: str,
        dice_rolls: list[int] | None = None,
    ) -> str:
        dice_section = ""
        if dice_rolls:
            rolls_str = ", ".join(str(r) for r in dice_rolls)
            dice_section = f"\n\n## Dice Rolls\nd20 pool (use in order): [{rolls_str}]"
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
            f"{dice_section}"
        )

    def parse_response(
        self, raw: str, character_id: str, turn: int,
    ) -> Adjudication:
        text = raw.strip()

        def _extract(section: str) -> str:
            pattern = rf"\*\*{section}\*\*\s*(?:—|:|--)?\s*(.*?)(?=\*\*|\Z)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else ""

        approved_raw = _extract("APPROVED")
        modified_raw = _extract("MODIFIED ACTION")
        pos_raw = _extract("NEW POSITION")
        condition_raw = _extract("CONDITION")
        events_raw = _extract("EVENTS")
        notes_raw = _extract("NOTES")

        # Parse approved
        approved = approved_raw.lower().startswith("yes") if approved_raw else True

        # Parse modified action
        modified_action = None
        if modified_raw and modified_raw.lower() not in ("none", "null", "n/a", ""):
            modified_action = modified_raw

        # Parse new absolute position: x=<val>, y=<val>, zone=<ZONE>
        pos = None
        if pos_raw and pos_raw.lower() not in ("none", "null", "n/a", "no movement", ""):
            x_m = re.search(r'x\s*=\s*(-?\d+(?:\.\d+)?)', pos_raw, re.IGNORECASE)
            y_m = re.search(r'y\s*=\s*(-?\d+(?:\.\d+)?)', pos_raw, re.IGNORECASE)
            zone_m = re.search(r'zone\s*=\s*(\w+)', pos_raw, re.IGNORECASE)
            if x_m and y_m:
                pos = (float(x_m.group(1)), float(y_m.group(1)),
                       zone_m.group(1).upper() if zone_m else "")

        # Parse condition deltas: handles multiple formats:
        #   "dopamine +0.1, cortisol -0.05"
        #   "dopamine 0.1"
        #   "increase dopamine by 0.08"
        condition_deltas: dict[str, float] = {}
        if condition_raw and condition_raw.lower() not in ("none", "null", "n/a", ""):
            known_dims = {
                "dopamine", "cortisol", "norepinephrine",
                "endorphins", "serotonin", "acetylcholine", "oxytocin",
            }
            for dim in known_dims:
                # Check "decrease" first — must negate
                neg_pattern = rf'decrease\s+{dim}[:\s]+(?:by\s+)?([+-]?\d+(?:\.\d+)?)'
                m_neg = re.search(neg_pattern, condition_raw, re.IGNORECASE)
                if m_neg:
                    try:
                        condition_deltas[dim] = -abs(float(m_neg.group(1)))
                    except ValueError:
                        pass
                    continue
                # General: "dopamine +0.1" or "dopamine: +0.1" or
                #          "increase dopamine by 0.1" or "dopamine 0.08"
                pattern = rf'(?:increase\s+)?{dim}[:\s]+(?:by\s+)?([+-]?\d+(?:\.\d+)?)'
                m = re.search(pattern, condition_raw, re.IGNORECASE)
                if m:
                    try:
                        condition_deltas[dim] = float(m.group(1))
                    except ValueError:
                        pass

        # Parse spatial events: comma-separated, newline-separated, or bullet lists
        spatial_events: list[str] = []
        if events_raw and events_raw.lower() not in ("none", "null", "n/a", ""):
            # Split on commas, newlines, or bullet markers
            parts = re.split(r'[,\n]|\s*[-•]\s+', events_raw)
            spatial_events = [
                e.strip().strip('-•').strip()
                for e in parts if e.strip() and e.strip() not in ('-', '•')
            ]

        return Adjudication(
            character_id=character_id,
            turn=turn,
            approved=approved,
            modified_action=modified_action,
            new_position=pos,
            condition_deltas=condition_deltas,
            spatial_events=spatial_events,
            notes=notes_raw,
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
        dice_rolls = _roll_dice(8)
        user = self.build_user_prompt(
            character_output, game_state_summary, geometry_summary,
            dice_rolls=dice_rolls,
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
            "of third-person, present-tense prose describing what happens. "
            "Be concrete and specific — what the character does, what "
            "others can see and hear. No game mechanics, dice, or "
            "meta-commentary. No purple prose — avoid 'seemed to', "
            "'as if', atmospheric clichés, and stacked adjectives. "
            "Plain language. Let the action speak."
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
        spoken_block = ""
        spoken = getattr(character_output, "spoken", "") or ""
        if spoken.strip() and spoken.strip().lower() not in (
            "(silent)", "(silence)",
        ):
            spoken_block = f"\n\n## What they said\n\"{spoken.strip()}\""
        return (
            f"# Character: {character_output.character_id} "
            f"(Turn {character_output.turn})\n\n"
            f"## What they did\n{character_output.action}"
            f"{spoken_block}\n\n"
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
