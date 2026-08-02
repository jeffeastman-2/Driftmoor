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

from engine.game_rng import rng
import re
from dataclasses import dataclass, field
from typing import Optional
import re

from engine.player_router import CallLLM, CharacterOutput


def _roll_dice(n: int = 8, sides: int = 20) -> list[int]:
    """Roll n dice with the given number of sides using Python's CSPRNG."""
    return [rng().randint(1, sides) for _ in range(n)]


def _roll_damage_pools(n: int = 6) -> dict[str, list[int]]:
    """Pre-roll damage dice pools for all common die sizes."""
    return {
        "d4":  [rng().randint(1, 4)  for _ in range(n)],
        "d6":  [rng().randint(1, 6)  for _ in range(n)],
        "d8":  [rng().randint(1, 8)  for _ in range(n)],
        "d10": [rng().randint(1, 10) for _ in range(n)],
        "d12": [rng().randint(1, 12) for _ in range(n)],
    }


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
    new_position: Optional[tuple[float, float, str]] = None  # Python-computed from movement_target
    movement_target: Optional[tuple[float, float]] = None  # DM-declared destination (x, y)
    condition_deltas: dict[str, float] = field(default_factory=dict)
    spatial_events: list[str] = field(default_factory=list)
    attacks: list[dict] = field(default_factory=list)  # [{target, hit_bonus, damage_expr}]
    notes: str = ""
    # hp_damage is computed by Python from attacks; kept for checkpoint serialisation
    hp_damage: dict[str, int] = field(default_factory=dict)


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
            "A set of pre-rolled d20 results and damage dice will be provided "
            "in the user prompt under '## Dice Rolls'. You MUST use these rolls "
            "in order for any saving throws, attack rolls, contested checks, and "
            "damage rolls — do NOT invent or assume your own values. "
            "Consume from each pool left to right; unused rolls are discarded. "
            "For damage: use the matching die pool (e.g. '2d6' → take 2 values "
            "from the d6 pool and sum them). Never use maximum or average damage "
            "— always use the pre-rolled values.\n\n"
            "## Melee and Ranged Combat Rules\n"
            "1 melee round = 6 seconds (one D&D 5e round). "
            "Coordinates are in feet. All D&D 5e stat block distances "
            "(speed, reach, range) are in feet and apply directly to coordinates.\n\n"
            "MOVEMENT — CRITICAL:\n"
            "Python owns movement resolution. The character declares a "
            "MOVEMENT target in their action; Python automatically clamps "
            "the actual travel to the character's speed (or 2× speed when "
            "Dashing) along the line toward the target. You do NOT decide "
            "the final position and you do NOT need NEW POSITION at all.\n"
            "  - APPROVED is about whether the ACTION TYPE is legal "
            "(can the character do this kind of thing right now?), NOT "
            "about distance. Never set APPROVED: No just because the "
            "destination is farther than the character's speed — Python "
            "will simply move them as far as they can go.\n"
            "  - Legitimate reasons to set APPROVED: No: action targets a "
            "creature that does not exist; uses an ability the character "
            "doesn't have; attacks an ally without justification; the "
            "character is incapacitated; barrier-crossing save fails (use "
            "pre-rolled d20).\n"
            "  - 'Already in the right zone' is NOT a reason to deny — "
            "intra-zone movement is normal and Python handles it.\n"
            "  - You may briefly note the distance and that Python will "
            "clamp, but APPROVED stays Yes.\n\n"
            "ATTACKS:\n"
            "  - Melee (e.g. 'reach 5 ft.'): attacker's post-move position "
            "must be within reach of target. If not reachable this round, "
            "attack is impossible — APPROVED: No.\n"
            "  - Ranged (e.g. 'range 80/320 ft.'): attack from current position "
            "without moving; normal range is the first number.\n"
            "  - Move BEFORE attacking, not after. MOVEMENT TARGET must be set "
            "to a position within reach of the target — even when already in the "
            "same zone, intra-zone movement requires a MOVEMENT TARGET. Without it, "
            "the creature does not move and Python will reject the attack as out of range.\n"
            "  - Multiattack: all attacks from ONE chosen position. "
            "Cannot move between attacks.\n"
            "  - NOTES must show each attack roll separately: "
            "'Attack N vs [target]: d20=X+mod=Y vs AC Z → hit/miss for D damage'.\n\n"
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
            "**MOVEMENT TARGET** — Echo the character's stated movement "
            "target (or \"none\"). Python uses the character's own "
            "MOVEMENT field from their action — not this one — as the "
            "authoritative destination. This field is for your reasoning only.\n"
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
            "area entirely (fleeing, retreating, departing), "
            "or when a character or creature is reduced to 0 HP.\n"
            "  CRITICAL: If APPROVED is No (barrier crossing failed, "
            "action rejected), do NOT emit boundary_crossed or "
            "combat_initiated. Those events only apply when the action "
            "actually succeeds.\n"
            "**NOTES** — Full adjudication reasoning: movement distances, "
            "whether each attack can land (reach/range check), and any saving "
            "throw results (use pre-rolled d20 pool for saves). "
            "Do NOT roll or compute damage — Python handles dice.\n"
            "**ATTACKS** — Declare each attack being made this turn. "
            "One attack per line in the format:\n"
            "  target=<character_id>, bonus=<+N>, damage=<XdY+Z>\n"
            "Example:\n"
            "  target=fennel, bonus=+4, damage=1d6\n"
            "Use 'none' if no attacks are made. "
            "Only declare attacks your NOTES confirm are physically possible "
            "(within reach/range after movement, action approved). "
            "Declare ONLY as many attacks as the stat block allows — "
            "if there is no Multiattack entry, declare exactly ONE attack. "
            "Python will roll d20+bonus vs target AC and apply damage on hit — "
            "do not compute hit/miss or damage yourself."
        )

    def build_user_prompt(
        self,
        character_output: CharacterOutput,
        game_state_summary: str,
        geometry_summary: str,
        dice_rolls: list[int] | None = None,
        dm_ledger: str = "",
    ) -> str:
        dice_section = ""
        if dice_rolls:
            rolls_str = ", ".join(str(r) for r in dice_rolls)
            dice_section = (
                f"\n\n## Dice Rolls (d20 pool — use in order for saves/checks)\n"
                f"[{rolls_str}]\n"
                f"Note: attack hit/miss and damage are resolved by Python — "
                f"do not roll damage yourself."
            )
        ledger_section = f"{dm_ledger}\n\n" if dm_ledger else ""
        return (
            f"{ledger_section}"
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
        target_raw = _extract("MOVEMENT TARGET")
        condition_raw = _extract("CONDITION")
        events_raw = _extract("EVENTS")
        notes_raw = _extract("NOTES")
        attacks_raw = _extract("ATTACKS")

        # Parse approved
        approved = approved_raw.lower().startswith("yes") if approved_raw else True

        # Safety net: the DM reliably computes saving throws but has a
        # deep bias toward APPROVED: No whenever a barrier is mentioned,
        # even when the save succeeded.  Read the math directly from NOTES
        # and override when roll >= DC.  Only fires when approved is already
        # False and a DC is present (saves, not attack rolls vs AC).
        if not approved and notes_raw:
            # Primary: "N vs DC M" or "N >= DC M" — both values in one match
            both_m = re.search(
                r'(\d+)\s+(?:vs?\.?\s+)?dc\s*:?\s*(\d+)',
                notes_raw, re.IGNORECASE,
            )
            if both_m:
                roll_val, dc_val = int(both_m.group(1)), int(both_m.group(2))
                if roll_val >= dc_val:
                    approved = True
            else:
                # Fallback: find DC and roll separately.
                # Prioritise d20/rolling patterns over bare "rolled N" to
                # avoid accidentally capturing damage rolls like "rolled 4+2".
                dc_m = re.search(r'\bdc\s*:?\s*(\d+)', notes_raw, re.IGNORECASE)
                roll_m = (
                    re.search(r'd20[:\s]+(\d+)', notes_raw, re.IGNORECASE) or
                    re.search(r'rolling?[:\s]+(\d+)', notes_raw, re.IGNORECASE) or
                    re.search(r'rolled?[:\s]+(\d+)', notes_raw, re.IGNORECASE)
                )
                if dc_m and roll_m:
                    dc_val = int(dc_m.group(1))
                    roll_val = int(roll_m.group(1))
                    if roll_val >= dc_val:
                        approved = True

        # Parse modified action
        modified_action = None
        if modified_raw and modified_raw.lower() not in ("none", "null", "n/a", ""):
            modified_action = modified_raw

        # Parse movement target: x=<val>, y=<val> (no zone — Python resolves)
        movement_target: tuple[float, float] | None = None
        if target_raw and target_raw.lower() not in ("none", "null", "n/a", "no movement", ""):
            x_m = re.search(r'x\s*=\s*(-?\d+(?:\.\d+)?)', target_raw, re.IGNORECASE)
            y_m = re.search(r'y\s*=\s*(-?\d+(?:\.\d+)?)', target_raw, re.IGNORECASE)
            if x_m and y_m:
                movement_target = (float(x_m.group(1)), float(y_m.group(1)))

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
                e.strip().strip('-•').strip().rstrip('.')
                for e in parts if e.strip() and e.strip() not in ('-', '•')
            ]
        # Python owns these event flags — strip any LLM-emitted versions.
        # combat_initiated is set by CombatResolver / declared-attacks check.
        # boundary_crossed is set by _check_boundary_crossing in session.py.
        _PYTHON_OWNED_EVENTS = {"combat_initiated", "boundary_crossed"}
        spatial_events = [
            e for e in spatial_events if e.lower() not in _PYTHON_OWNED_EVENTS
        ]

        # Parse attacks: one per line, "target=X, bonus=+N, damage=YdZ+W"
        attacks: list[dict] = []
        if attacks_raw and attacks_raw.lower() not in ("none", "null", "n/a", ""):
            for line in attacks_raw.splitlines():
                line = line.strip().lstrip('-•').strip()
                if not line:
                    continue
                t_m = re.search(r'target\s*=\s*(\w+)', line, re.IGNORECASE)
                b_m = re.search(r'bonus\s*=\s*([+-]?\d+)', line, re.IGNORECASE)
                d_m = re.search(r'damage\s*=\s*([\ddDsS+\-\s]+)', line, re.IGNORECASE)
                if t_m and b_m and d_m:
                    attacks.append({
                        "target": t_m.group(1).lower(),
                        "hit_bonus": int(b_m.group(1)),
                        "damage_expr": d_m.group(1).strip(),
                    })

        return Adjudication(
            character_id=character_id,
            turn=turn,
            approved=approved,
            modified_action=modified_action,
            movement_target=movement_target,
            condition_deltas=condition_deltas,
            spatial_events=spatial_events,
            attacks=attacks,
            notes=notes_raw,
        )

    async def adjudicate(
        self,
        character_output: CharacterOutput,
        game_state_summary: str,
        geometry_summary: str,
        dm_ledger: str = "",
    ) -> Adjudication:
        if self._call_llm is None:
            return Adjudication(
                character_id=character_output.character_id,
                turn=character_output.turn,
                approved=True,
            )
        system = self.build_system_prompt()
        dice_rolls = _roll_dice(8)  # d20 pool for saves and skill checks
        user = self.build_user_prompt(
            character_output, game_state_summary, geometry_summary,
            dice_rolls=dice_rolls, dm_ledger=dm_ledger,
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

    @staticmethod
    def _enforce_acting_pronouns(
        prose: str,
        character_id: str,
        character_pronouns: dict[str, str] | None,
    ) -> str:
        """Best-effort guardrail against acting-character misgendering.

        LLM prompts request strict pronoun fidelity, but occasional drift still
        happens. This post-pass normalizes third-person pronouns to the acting
        character's configured pronouns.
        """
        if not prose or not character_pronouns:
            return prose

        p = (character_pronouns.get(character_id) or "").strip().lower()
        if p not in {"she/her", "he/him", "they/them"}:
            return prose

        if p == "she/her":
            replacements = {
                "he": "she",
                "him": "her",
                "his": "her",
                "himself": "herself",
            }
        elif p == "he/him":
            replacements = {
                "she": "he",
                "her": "him",
                "hers": "his",
                "herself": "himself",
            }
        else:  # they/them
            replacements = {
                "he": "they",
                "him": "them",
                "his": "their",
                "himself": "themself",
                "she": "they",
                "her": "them",
                "hers": "theirs",
                "herself": "themself",
            }

        fixed = prose
        for src, dst in replacements.items():
            fixed = re.sub(rf"\b{src}\b", dst, fixed)
            fixed = re.sub(rf"\b{src.capitalize()}\b", dst.capitalize(), fixed)
        return fixed

    @staticmethod
    def _enforce_character_style(
        prose: str,
        character_id: str,
    ) -> str:
        """Apply lightweight character-specific style corrections.

        This is intentionally narrow and only fixes recurrent, known drift that
        is jarring in playtest output.
        """
        if not prose:
            return prose

        if character_id.lower() == "gilthaness":
            fixed = prose
            fixed = re.sub(
                r"letting\s+each\s+heavy\s+footfall\s+strike\s+the\s+floor\s+with\s+a\s+heavy,\s*rhythmic\s+thud",
                "moving with quiet, measured steps",
                fixed,
                flags=re.IGNORECASE,
            )
            fixed = re.sub(
                r"\bheavy\s+footfalls?\b",
                "measured steps",
                fixed,
                flags=re.IGNORECASE,
            )
            fixed = re.sub(
                r"\bfootfalls?\s+strikes?\s+the\s+floor\b",
                "steps softly across the floor",
                fixed,
                flags=re.IGNORECASE,
            )
            fixed = re.sub(
                r"\bheavy,\s*rhythmic\s+thud(?:s)?\b",
                "soft, measured motion",
                fixed,
                flags=re.IGNORECASE,
            )
            fixed = re.sub(r"\bthud(?:s|ding)?\b", "soft tap", fixed, flags=re.IGNORECASE)
            return fixed

        return prose

    @staticmethod
    def _dedupe_repeated_opening_dialogue(prose: str) -> str:
        """Remove a decorative opening quote repeated in the narration body.

        Some narrators emit ``*“\"full speech\"”*`` and then narrate the same
        speech again, split across ordinary quoted sentences with attribution.
        The history-level speech guard cannot catch this because both copies are
        already inside one narration response.
        """
        if not prose:
            return prose
        match = re.match(
            r'^\s*\*[“"]+\"?(?P<quote>.*?)\"?[”"]+\*\s*(?P<rest>.+)$',
            prose,
            flags=re.DOTALL,
        )
        if match is None:
            return prose

        def norm(value: str) -> str:
            return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

        quote = match.group("quote").strip().strip('"“”')
        rest = match.group("rest").strip()
        # Attribution inserted between sentences prevents a whole-quote
        # substring comparison. Require every meaningful sentence from the
        # decorative quote to recur in the remaining prose before deleting it.
        chunks = [
            norm(chunk)
            for chunk in re.split(r"(?<=[.!?])\s+", quote)
            if len(norm(chunk).split()) >= 3
        ]
        rest_norm = norm(rest)
        if chunks and all(chunk in rest_norm for chunk in chunks):
            return rest
        return prose

    def build_system_prompt(
        self,
        character_pronouns: dict[str, str] | None = None,
    ) -> str:
        prompt = (
            "You are the narrative voice of the DM. Write 2-4 sentences "
            "of third-person, present-tense prose describing what happens. "
            "Be concrete and specific — what the character does, what "
            "others can see and hear. No game mechanics, dice, or "
            "meta-commentary. No purple prose — avoid 'seemed to', "
            "'as if', atmospheric clichés, and stacked adjectives. "
            "Plain language. Let the action speak.\n\n"
            "DIALOGUE: Include each spoken sentence exactly once. Do not place "
            "the full speech in a decorative opening quotation and then repeat "
            "it with attribution in the prose.\n\n"
            "GROUNDING: Keep descriptions tied to observable facts. Use "
            "counts, distances, times, positions, visible marks, direct speech, "
            "and physical cause/effect. If the scene suggests a theory, keep it "
            "as a hypothesis rather than a grand explanation.\n\n"
            "CRITICAL — POV: Narrate strictly from the acting character's "
            "point of view. If a '## Perception' section is present, it "
            "is the AUTHORITATIVE and EXHAUSTIVE list of creatures the "
            "acting character can currently perceive. Do NOT describe, "
            "name, reference, or imply the presence of any other creature "
            "— not by sight, sound, scent, heat signature, vibration, "
            "shadow, or any other sense. Do not write 'the two figures', "
            "'the companion', 'the watcher' or similar if only one (or "
            "zero) other creatures are listed. If the perception list is "
            "empty, narrate only what the acting character alone does and "
            "senses in their immediate surroundings.\n\n"
            "IMPORTANT: '## Scene so far' contains narration written for "
            "OTHER characters this turn, from THEIR points of view. It is "
            "provided for continuity and tone ONLY. It is NOT evidence of "
            "what the acting character can perceive. If '## Scene so far' "
            "mentions a creature that is NOT in the acting character's "
            "'## Perception' list, that creature is invisible/inaudible/"
            "undetectable to the acting character and MUST NOT appear, be "
            "named, or be alluded to in your output (not as 'Aeliana', "
            "'the ranger', 'the elf', 'the figure on the trail', "
            "'something in the distance', or any other reference). Write "
            "as if that creature does not exist.\n\n"
            "CRITICAL: If an '## Engine resolution' section is present, "
            "it is the authoritative record of what actually happened — "
            "attacks blocked by no line of sight did NOT land and must NOT "
            "be narrated as landing or even as attempted; attacks that missed "
            "did not hit; only hits cause damage. [MOVEMENT] entries record "
            "the character's actual movement: if they say the character moved "
            "from A to B, narrate that motion — do NOT narrate them being "
            "knocked back, repelled, or stopped short unless the entry says "
            "'repelled' or 'denied'. If NO [MOVEMENT] entry is present for "
            "the acting character, they did not move this turn — narrate them "
            "stationary (no charges, no strides forward, no closing distance, "
            "no skids to a halt against a barrier). Never contradict the "
            "engine resolution in your prose. [VENUE] entries are authoritative "
            "about doorway crossings: if one says the character approached but "
            "did not enter, do not describe them crossing the threshold or being "
            "inside; if it says they entered, describe the completed entry."
        )
        if character_pronouns:
            pronoun_str = ", ".join(
                f"{name} ({p})" for name, p in character_pronouns.items()
            )
            prompt += f"\n\nCharacter pronouns: {pronoun_str}. Use these consistently — never misgender a character."
        return prompt
    def build_user_prompt(
        self,
        adjudication: Adjudication,
        character_output: CharacterOutput,
        scene_history: str,
        resolution_log: list[str] | None = None,
        perception: str | None = None,
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
        resolution_block = ""
        if resolution_log:
            resolution_block = (
                "\n\n## ENGINE RESOLUTION (authoritative — narrate this, not the intent below)\n"
                + "\n".join(resolution_log)
            )
        # Perception block — constrains narrator to acting character's POV.
        if perception is not None:
            if perception.strip():
                perception_block = (
                    f"\n\n## Perception (authoritative — acting character's POV)\n"
                    f"{perception}\n"
                    "Narrate only these creatures. Do not reference any "
                    "other creature by any sense."
                )
            else:
                perception_block = (
                    "\n\n## Perception (authoritative — acting character's POV)\n"
                    "No other creatures are visible, audible, or otherwise "
                    "detectable. Narrate only the acting character alone in "
                    "their immediate surroundings. Do not mention, imply, "
                    "or reference any other character."
                )
        else:
            perception_block = ""
        return (
            f"# Character: {character_output.character_id} "
            f"(Turn {character_output.turn}){resolution_block}"
            f"{perception_block}\n\n"
            f"## What they intended\n{character_output.action}"
            f"{spoken_block}\n\n"
            f"## Adjudication: {status}{mod}{notes}{history_block}"
        )

    def parse_response(
        self,
        raw: str,
        character_id: str,
        turn: int,
        character_pronouns: dict[str, str] | None = None,
    ) -> Narration:
        prose = self._enforce_acting_pronouns(
            raw.strip(),
            character_id,
            character_pronouns,
        )
        prose = self._enforce_character_style(prose, character_id)
        prose = self._dedupe_repeated_opening_dialogue(prose)
        return Narration(
            character_id=character_id,
            turn=turn,
            prose=prose,
            visible_to=[],
        )

    async def narrate(
        self,
        adjudication: Adjudication,
        character_output: CharacterOutput,
        scene_history: str,
        resolution_log: list[str] | None = None,
        character_pronouns: dict[str, str] | None = None,
        perception: str | None = None,
    ) -> Narration:
        if self._call_llm is None:
            action_text = character_output.action or "(no action)"
            prose = f"{character_output.character_id} {action_text}."
            # Human-player roles intentionally have no narrator LLM. Surface
            # Python's authoritative item outcome instead of echoing the intent
            # as though opening, reading, eating, or drinking did nothing.
            for entry in reversed(resolution_log or []):
                if entry.startswith("[ITEM-INTERACTION]") and ": " in entry:
                    prose = entry.split(": ", 1)[1].strip()
                    break
                if entry.startswith("[ITEM]"):
                    match = re.match(r"^\[ITEM\]\s+(\S+)\s+(.+)$", entry)
                    actor = ""
                    clean = entry
                    if match:
                        actor = match.group(1).replace("_", " ").title()
                        clean = match.group(2)
                    clean = clean.split(": ", 1)[0].replace("_", " ").strip()
                    if clean:
                        prose = f"{actor} {clean}.".strip()
                        break
                if entry.startswith("[COMMERCE]") and " bought " in entry:
                    match = re.search(
                        r"\b(\S+) bought (.+?) from \S+ for exactly ([^;]+)",
                        entry,
                    )
                    if match:
                        actor = match.group(1).replace("_", " ").title()
                        prose = f"{actor} buys {match.group(2)} for {match.group(3)}."
                        break
            return Narration(
                character_id=adjudication.character_id,
                turn=adjudication.turn,
                prose=prose,
                visible_to=[],
            )
        system = self.build_system_prompt(character_pronouns=character_pronouns)
        user = self.build_user_prompt(
            adjudication, character_output, scene_history,
            resolution_log=resolution_log,
            perception=perception,
        )
        raw = await self._call_llm(system, user)
        return self.parse_response(
            raw,
            adjudication.character_id,
            adjudication.turn,
            character_pronouns=character_pronouns,
        )
