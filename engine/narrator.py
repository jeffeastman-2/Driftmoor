"""Narrative story generator — turn checkpoints → LLM-written prose.

Extracts the raw narrative material (narration, dialogue, body language)
from turn checkpoint data, then sends it to an LLM with instructions
to weave it into a cohesive short story.

The prompt-building functions are pure and testable.
The LLM call is a thin async wrapper using make_call_llm().

Usage:
    from engine.narrator import generate_narrative_from_dir
    story = await generate_narrative_from_dir(
        Path("runtime/state/session_run"),
        provider="anthropic", model="claude-sonnet-4-20250514",
        title="The Fey Glade",
    )
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from engine.llm_bridge import make_call_llm


# ---------------------------------------------------------------------------
# Material extraction — checkpoint JSON → structured text for the LLM
# ---------------------------------------------------------------------------

def extract_scene_material(turns: list[dict]) -> str:
    """Extract narrative material from turn checkpoint dicts.

    Pulls narration prose, spoken dialogue, and body language in
    turn order. This gives the LLM the raw events to reshape into
    a story without game-mechanic noise (condition deltas, spatial
    events, adjudication notes).
    """
    sections: list[str] = []

    for turn_data in turns:
        turn_num = turn_data["turn"]
        parts: list[str] = [f"--- Turn {turn_num} ---"]

        for cr in turn_data["character_results"]:
            char_id = cr["character_id"]
            char_parts: list[str] = [f"{char_id.upper()}:"]

            # Body language
            body = cr["output"].get("body_language", "")
            if body.strip():
                char_parts.append(f"  Body language: {body.strip()}")

            # Spoken dialogue
            spoken = cr["output"].get("spoken", "")
            if spoken.strip() and spoken.strip().lower() not in (
                "(silent)", "(silence)", ""
            ):
                char_parts.append(f"  Says: {spoken.strip()}")

            # DM narration (the main prose)
            prose = cr["narration"].get("prose", "")
            if prose.strip():
                char_parts.append(f"  Narration: {prose.strip()}")

            parts.append("\n".join(char_parts))

        sections.append("\n\n".join(parts))

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Prompt building — pure functions, fully testable
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a fiction writer. You will receive raw scene material from a \
tabletop RPG session — narration, dialogue, and body language organized \
by turn. Weave this material into a single cohesive piece of prose fiction.

Guidelines:
- Third person, past tense.
- Preserve all dialogue exactly as given.
- Merge per-character, per-turn narration into one unified scene. \
The source material often describes the same moment from multiple \
character perspectives with redundant detail — collapse these into \
a single clean account. No "Turn 1" headers or game structure.
- Maintain chronological order.
- Do not invent new events, characters, or dialogue.
- No game mechanics (dice, HP, AC, condition deltas).
- Aggressively cut repetition. Characters often re-introduce \
themselves or re-state their purpose across multiple turns — render \
each introduction ONCE, the first time it happens. If a character \
asks "what brings you here?" and another character repeats the same \
question later, cut the duplicate entirely. If a character restates \
information already given, cut the restatement. Every sentence must \
add something new. A four-turn scene should read as one fluid \
conversation, not four rounds of the same exchange.

Style — this is critical:
- Write like Cormac McCarthy or Raymond Carver, not like a fantasy novel. \
Short sentences. Plain words. Let action and dialogue carry the scene.
- Cut adjectives ruthlessly. Never use two where zero will do. \
Delete "seemed to", "as if", "almost as though", and similar hedges.
- No similes involving weather, predators, or drawn bowstrings. \
No "electric tension", "crackling energy", "dancing shadows", or \
"ancient secrets". If you catch yourself reaching for an atmospheric \
cliché, stop and write what actually happened instead.
- Describe what characters DO, not what the air feels like.
- One paragraph of scene-setting at the top is fine. After that, \
earn every descriptive phrase with narrative purpose.
- Output only the story text. No commentary, no title unless requested.
"""


def build_narrative_prompt(
    material: str,
    *,
    title: str = "",
) -> tuple[str, str]:
    """Build the (system_prompt, user_message) pair for the LLM.

    Args:
        material: Output of extract_scene_material().
        title:    Optional title to include in the story.

    Returns:
        (system_prompt, user_message) ready for call_llm().
    """
    user_parts: list[str] = []

    if title:
        user_parts.append(f"Title: {title}\n")

    user_parts.append("Here is the raw scene material:\n")
    user_parts.append(material)

    return SYSTEM_PROMPT, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# LLM-powered narrative generation
# ---------------------------------------------------------------------------

async def generate_narrative(
    turns: list[dict],
    *,
    provider: str,
    model: str,
    title: str = "",
    api_key: Optional[str] = None,
) -> str:
    """Generate a narrative story from turn checkpoint data.

    Args:
        turns:    List of turn checkpoint dicts (as loaded from JSON).
        provider: LLM provider ("anthropic", "openai", "xai", etc.).
        model:    Model name.
        title:    Optional story title.
        api_key:  Optional API key override.

    Returns:
        The generated story as a string.
    """
    material = extract_scene_material(turns)
    system, user = build_narrative_prompt(material, title=title)
    call_llm = make_call_llm(provider, model, api_key=api_key)
    return await call_llm(system, user)


async def generate_narrative_from_dir(
    checkpoint_dir: Path,
    *,
    provider: str,
    model: str,
    title: str = "",
    output_path: Optional[Path] = None,
    api_key: Optional[str] = None,
) -> str:
    """Read checkpoints from a directory and generate a narrative.

    Args:
        checkpoint_dir: Directory containing turn_0001.json, etc.
        provider:       LLM provider.
        model:          Model name.
        title:          Optional story title.
        output_path:    If provided, write the story to this file.
        api_key:        Optional API key override.

    Returns:
        The generated story as a string.
    """
    files = set(checkpoint_dir.glob("turn_*.json")) | set(checkpoint_dir.glob("day*.json"))
    turns = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(files)]
    turns.sort(key=lambda d: d["turn"])

    story = await generate_narrative(
        turns, provider=provider, model=model,
        title=title, api_key=api_key,
    )

    if output_path:
        output_path.write_text(story, encoding="utf-8")

    return story
