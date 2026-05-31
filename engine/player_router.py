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
    in_combat: bool = False


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

    @staticmethod
    def _items_from_perception(perception: str) -> list[str]:
        """Extract visible item labels from the perception block.

        Expected shape:
            Items in this zone:
            - Snapped torch (~10 ft away)
            - Drag marks (~15 ft away) (already examined)
        """
        if not perception:
            return []
        marker = "Items in this zone:"
        idx = perception.find(marker)
        if idx < 0:
            return []
        tail = perception[idx + len(marker):]
        labels: list[str] = []
        for raw in tail.splitlines():
            line = raw.strip()
            if not line.startswith("- "):
                continue
            body = line[2:].strip()
            label = body.split("(~", 1)[0].strip()
            if label:
                labels.append(label)
        return labels

    @staticmethod
    def _infer_interaction_target(intent_text: str, perception: str) -> Optional[str]:
        """Infer item target from intent text + visible items when TARGET is missing."""
        items = PlayerLeft._items_from_perception(perception)
        if not items:
            return None
        intent_l = (intent_text or "").lower()

        # Strong match: explicit mention of a visible item label.
        for label in items:
            if label.lower() in intent_l:
                return label

        # Soft match: token overlap for phrasing variants.
        tokens = set(re.findall(r"[a-z]+", intent_l))
        stop = {
            "the", "a", "an", "around", "near", "area", "for", "any",
            "small", "useful", "further", "other", "more", "items",
            "item", "clues", "clue", "search", "examine", "inspect",
            "investigate", "look", "scan", "check", "ground", "floor",
        }
        tokens = {t for t in tokens if t not in stop}
        if tokens:
            best_label: Optional[str] = None
            best_score = 0
            for label in items:
                ltoks = set(re.findall(r"[a-z]+", label.lower()))
                score = len(tokens & ltoks)
                if score > best_score:
                    best_score = score
                    best_label = label
            if best_label and best_score > 0:
                return best_label

        # Fallback: if exactly one item is visible and intent is examine/search-like.
        if len(items) == 1 and re.search(
            r"\b(search|examine|inspect|investigate|look|scan|check|sift)\b",
            intent_l,
        ):
            return items[0]
        return None

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
            "is AUTHORITATIVE and EXHAUSTIVE. It is the only list of "
            "creatures your character is currently aware of. This rule "
            "covers EVERY form of awareness — not just targeting: \n"
            "  • You may not see, hear, smell, sense, track, or think about "
            "creatures not on this list.\n"
            "  • You may not reference them in your INTENT, MOVEMENT, or "
            "TARGET, even indirectly (e.g. 'alert the ranger', 'approach "
            "the figure', 'flank the beast'). If they are not listed, they "
            "do not exist to you right now.\n"
            "  • Your SOUL or IDENTITY may mention other characters as "
            "background or past relationships. That is NOT current "
            "perception. Unless a character appears in the perception "
            "list, you do not know they are near you.\n"
            "  • '## Scene' may contain narration written for OTHER "
            "characters this turn, from THEIR points of view. It is "
            "provided for continuity only. If a creature is mentioned "
            "there but is NOT in your perception list, you cannot "
            "perceive them and must not reference them in INTENT, "
            "MOVEMENT, or TARGET.\n"
            "  • Scene titles, transcripts, cast lists, or the names of "
            "other participants are out-of-character metadata. Ignore them.\n"
            "Creatures not listed are UNKNOWN to you — do not acknowledge "
            "their existence or attempt to perceive, signal, or target "
            "them. Other characters, if visible, may be interacted with "
            "according to the rules.\n\n"
            "CRITICAL — HISTORY: Read the scene history carefully. Do NOT repeat "
            "actions already completed. If you have already introduced "
            "yourself, do not introduce yourself again. If a question "
            "has already been asked, do not ask it again. Advance the "
            "conversation — reveal new information, change tactics, "
            "react to what others said, or take a new action. "
            "Do NOT repeat any spoken line word-for-word from a prior turn. "
            "CRITICAL — GROUNDING: Keep reasoning tied to concrete, observable "
            "facts. Prefer counts, distances, times, locations, visible marks, "
            "and direct quotes. If you speculate, frame it as a hypothesis and "
            "say what observation would support or falsify it. Avoid abstract "
            "technobabble unless it is anchored to a specific thing you can "
            "actually point at in the scene. "
            "CRITICAL — STUCK LOOP: If your last two or more turns show the same "
            "action (e.g. 'search the shimmering patch' repeated), you MUST choose "
            "a different action this turn. The repeated action has already yielded "
            "what it can. Move on: explore elsewhere, speak with a companion, "
            "rest, prepare for what comes next, or leave the area. "
            "If a local puzzle is still unresolved, keep working the puzzle "
            "before leaving the zone. "
            "If you have searched your current chamber and found no new evidence, "
            "use MOVEMENT to enter a different zone or passage listed under "
            "Points of interest.\n\n"
            "Respond with exactly these labeled sections "
            "(no markdown fencing):\n\n"
            "**INTENT** — One sentence: what you will do this turn "
            "(name the action type, e.g. 'Dash east toward the trail exit').\n"
            "**MOVEMENT** — Target coordinates as x, y "
            "(or \"none\" if staying put). "
            "MUST be different from your current position — "
            "do not repeat your current coordinates here. "
            "Choose a destination you intend to reach this turn.\n"
            "**TARGET** — Character or item you interact with "
            "(or \"none\").\n"
            "Be specific. Reference your zone and observable targets. If you "
            "make a causal claim, state it as a hypothesis and attach one "
            "observable clue to it."
        )

    def build_user_prompt(self, context: RoleContext) -> str:
        if context.perception:
            perception_header = "## What you can currently perceive"
            if context.in_combat:
                perception_header = "## COMBAT ACTIVE — Visible targets"
            perception_block = f"\n\n{perception_header}\n{context.perception}"
            has_hostile = "HOSTILE" in (context.perception or "")
            if context.in_combat:
                perception_block += (
                    "\n\nYou are in active combat. "
                    "Attack visible hostile creatures — do not Search or wait."
                )
            elif has_hostile:
                perception_block += (
                    "\n\nA HOSTILE creature is visible. You do not need to "
                    "wait for it to attack first. If it is within your "
                    "weapon's range (longbow 150 ft, shortbow 80 ft, javelin "
                    "30 ft thrown, melee 5 ft), you may attack now. "
                    "'Wait and see' against a known hostile is rarely the "
                    "right call — opening from range before it closes the "
                    "distance is usually correct for a ranged attacker."
                )
        else:
            perception_block = (
                "\n\n## What you can currently perceive\n"
                "No other creatures are visible from your current position."
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
        target_norm = (target_raw or "").strip().lower().rstrip(".")
        if target_raw and target_norm not in ("none", "null", "n/a", ""):
            interaction = target_raw

        # If the model omitted TARGET, infer it from visible items in perception.
        if not interaction:
            interaction = self._infer_interaction_target(intent, context.perception)

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
            "**SPOKEN** — Dialogue (optional; leave blank if silent). "
            "CRITICAL: Check ## Scene for your previous SPOKEN lines. "
            "Do NOT repeat any line verbatim. Each turn, say something new "
            "— react to what just happened, reveal new information, or stay silent.\n\n"
            "**ACTION** — What you do this turn (50-100 words). "
            "Be specific. Reference your zone and observable targets.\n\n"
            "CRITICAL — PERCEPTION: '## What you can currently perceive' "
            "is AUTHORITATIVE and EXHAUSTIVE. It is the only list of "
            "creatures your character is currently aware of. This rule "
            "covers EVERY form of awareness — not just targeting:\n"
            "  • Do not see, hear, smell, sense, track, or think about "
            "creatures not on the list in ANY of the four sections "
            "(INTERNAL, BODY LANGUAGE, SPOKEN, ACTION).\n"
            "  • Do not narrate heat signatures, footsteps, voices, scents, "
            "vibrations, or silhouettes of creatures not on the list. "
            "If they are not listed, they do not exist to you right now.\n"
            "  • Do not invent a second figure, companion, or prey based "
            "on scene titles, cast summaries, or pattern-matching. Those "
            "are out-of-character metadata.\n"
            "  • Your SOUL or IDENTITY may reference other characters as "
            "background or past relationships. That is NOT current "
            "perception. Unless a character appears in the perception "
            "list, you do not know they are present.\n"
            "  • '## Scene' may contain narration written for OTHER "
            "characters this turn, from THEIR points of view. It is "
            "provided for continuity only. If a creature is mentioned "
            "there but is NOT in your perception list, you cannot perceive "
            "them; do not reference them in any of your four sections.\n"
            "  • Do not address anyone in SPOKEN who is not on the list."
        )

    def build_user_prompt(
        self, intent: ActionIntent, context: RoleContext,
    ) -> str:
        if context.perception:
            perception_block = (
                f"\n\n## What you can currently perceive\n{context.perception}"
            )
        else:
            perception_block = (
                "\n\n## What you can currently perceive\n"
                "No other creatures are visible, audible, or otherwise "
                "detectable from your current position."
            )
        return (
            f"# Turn {context.turn}\n\n"
            f"## Your intended action\n{intent.intent}\n\n"
            f"## Condition\n{context.condition_text}\n\n"
            f"## Scene\n{context.scene_context}"
            f"{perception_block}"
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
