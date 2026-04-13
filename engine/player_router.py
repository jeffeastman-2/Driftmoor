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

import re
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional

from engine.debug import _dbg


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
    perception: str = ""  # Python-computed LOS visibility block (authoritative)


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
            "## Each Turn You Have\n"
            "- **Movement** — Move up to your speed in feet. "
            "Difficult terrain costs double. Climbing costs double. "
            "You can split movement before and after your action.\n"
            "- **One Action** — Choose from the list below.\n"
            "- **One Bonus Action** — Only if a class feature, spell, or ability "
            "explicitly grants one (e.g. two-weapon fighting, Cunning Action).\n"
            "- **One Free Object Interaction** — Draw/stow a weapon, open a door, "
            "pick up an item. A second such interaction requires the Use an Object action.\n\n"
            "## Actions\n"
            "- **Attack** — Make one attack (melee or ranged). "
            "If you have Extra Attack, you make two or more attacks as one action. "
            "With two-weapon fighting, use your bonus action to attack with your off-hand "
            "light weapon (no ability modifier to damage). "
            "Ranged attacks against adjacent targets have disadvantage.\n"
            "- **Cast a Spell** — Cast a spell with a casting time of 1 action. "
            "Concentration spells end any existing concentration spell.\n"
            "- **Dash** — Gain extra movement equal to your full speed this turn. "
            "A speed-30 character can move 60 ft total; speed-35 can move 70 ft. "
            "Difficult terrain still costs double. "
            "This is the correct action to outrun a pursuer.\n"
            "- **Disengage** — Your movement does not provoke opportunity attacks "
            "for the rest of this turn. Use this to escape melee safely.\n"
            "- **Dodge** — Until the start of your next turn, all attack rolls against you "
            "have disadvantage (if you can see the attacker), and you have advantage on "
            "Dexterity saving throws. You lose this if incapacitated or your speed becomes 0.\n"
            "- **Help** — Choose an ally and a task. That ally has advantage on the next "
            "ability check for that task, OR advantage on the next attack roll against a "
            "creature within 5 ft of you. Advantage lasts until the start of your next turn.\n"
            "- **Hide** — Make a Dexterity (Stealth) check against observers' passive "
            "Perception. If successful, you are hidden: attackers have disadvantage against "
            "you and you have advantage on attacks. Moving out of cover or attacking "
            "breaks hiding.\n"

            "- **Search** — Make a Wisdom (Perception) or Intelligence (Investigation) "
            "check to find something hidden or examine the environment carefully.\n"
            "- **Use a Magic Item** — Activate a magic item that requires an action "
            "(e.g. drink a potion, activate a wand).\n"
            "- **Use an Object** — Interact with a second object this turn (beyond your "
            "free interaction), or use an object that requires focused attention "
            "(e.g. pick a lock, load a crossbow).\n"
            "- **Use a Special Ability** — Activate a class feature, racial trait, or "
            "other special ability that requires an action.\n\n"
            "CRITICAL — PERCEPTION: '## What you can currently perceive' "
            "is authoritative. You may only Attack or directly target "
            "creatures listed there. Creatures not listed are unknown "
            "to you — do not acknowledge their existence or attempt to "
            "target them. What to do instead is your own choice. Other "
            "characters, if visible, may be interacted with according to the rules.\n\n"
            "CRITICAL — HISTORY: Read the scene history carefully. Do NOT repeat "
            "actions already completed. If you have already introduced "
            "yourself, do not introduce yourself again. If a question "
            "has already been asked, do not ask it again. Advance the "
            "conversation — reveal new information, change tactics, "
            "react to what others said, or take a new action.\n\n"
            "Respond with exactly these labeled sections "
            "(no markdown fencing):\n\n"
            "**INTENT** — One sentence: what you will do this turn "
            "(name the action type, e.g. 'Dash east toward the trail exit').\n"
            "**MOVEMENT** — Target coordinates as x, y, z "
            "(or \"none\" if staying put).\n"
            "**TARGET** — Character or item you interact with "
            "(or \"none\")."
        )

    def build_user_prompt(self, context: RoleContext) -> str:
        perception_block = (
            f"\n\n## What you can currently perceive\n{context.perception}"
            if context.perception else
            "\n\n## What you can currently perceive\nNo other creatures are visible from your current position."
        )
        prompt = (
            f"# Turn {context.turn}\n\n"
            f"## Condition\n{context.condition_text}\n\n"
            f"## Scene\n{context.scene_context}"
            f"{perception_block}"
        )
        _dbg(f"[PLAYER-LEFT] {context.character_id} perception block: {repr(context.perception)}")
        return prompt

    def parse_response(self, raw: str, context: RoleContext) -> ActionIntent:
        def _extract(text: str, section: str) -> str:
            pattern = rf"\*\*{section}\*\*\s*(?:—|:|--)?\s*(.*?)(?=\*\*|\Z)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else ""

        text = raw.strip()
        intent = _extract(text, "INTENT")
        movement_raw = _extract(text, "MOVEMENT")
        target_raw = _extract(text, "TARGET")

        # Parse movement coordinates
        mt = None
        if movement_raw and movement_raw.lower() not in ("none", "null", "n/a", "stay", ""):
            nums = re.findall(r'-?\d+(?:\.\d+)?', movement_raw)
            if len(nums) >= 2:
                try:
                    coords = [float(n) for n in nums[:3]]
                    if len(coords) == 2:
                        coords.append(0.0)
                    mt = tuple(coords)
                except (TypeError, ValueError):
                    pass

        # Parse interaction target
        interaction = None
        if target_raw and target_raw.lower() not in ("none", "null", "n/a", ""):
            interaction = target_raw

        # Fallback: if no sections found, treat whole response as intent
        if not intent:
            intent = text.split('\n')[0].strip() or "observe surroundings"

        return ActionIntent(
            character_id=context.character_id,
            turn=context.turn,
            intent=intent,
            movement_target=mt,
            interaction_target=interaction,
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
        result = self.parse_response(raw, context)
        _dbg(f"[PLAYER-LEFT] {context.character_id} intent: {result.intent!r}")
        return result


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
            "Reflect your condition state through concrete "
            "perceptions and sensations, not analysis.\n\n"
            "**BODY LANGUAGE** — Physical state and demeanor "
            "(30-50 words). Just posture, hands, gaze — no metaphors.\n\n"
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
