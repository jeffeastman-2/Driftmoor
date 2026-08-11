"""Character interview, validation, and Markdown serialization for Driftmoor."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import re
from pathlib import Path
from typing import Any

from models.character_loader import load_player_character


ABILITIES = ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")


@dataclass
class CharacterDraft:
    name: str = "The Wanderer"
    player: str = "TBD"
    pronouns: str = "they/them"
    gender: str = "Unspecified"
    race: str = "Human"
    character_class: str = "Fighter"
    level: int = 1
    background: str = "Folk Hero"
    alignment: str = "Neutral Good"
    physical_description: str = "A road-worn traveler with an attentive gaze."
    hp: int = 10
    ac: int = 14
    speed: str = "30 ft"
    strength: int = 14
    dexterity: int = 12
    constitution: int = 14
    intelligence: int = 10
    wisdom: int = 12
    charisma: int = 10
    abilities: list[str] = field(default_factory=lambda: ["Athletics +2", "Perception +2"])
    spells: list[str] = field(default_factory=list)
    equipment: list[str] = field(default_factory=lambda: ["leather_armor", "longsword", "explorers_pack"])
    purse: str = "10 gp"
    mood: str = "Watchful, hopeful"
    disposition: str = "Ready to trust, but not carelessly"
    open_threads: list[str] = field(default_factory=list)
    values_and_drives: list[str] = field(default_factory=list)
    fears_and_wounds: list[str] = field(default_factory=list)
    voice_and_manner: list[str] = field(default_factory=list)
    loyalties: list[str] = field(default_factory=list)
    internal_contradiction: str = "They want a place to belong, yet leave before anyone can ask them to stay."
    signature_detail: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CharacterDraft":
        allowed = cls.__dataclass_fields__
        data = {key: value for key, value in raw.items() if key in allowed}
        for key in ABILITIES + ("level", "hp", "ac"):
            if key in data:
                try:
                    data[key] = int(data[key])
                except (TypeError, ValueError):
                    pass
        for key in ("abilities", "spells", "equipment", "open_threads", "values_and_drives",
                    "fears_and_wounds", "voice_and_manner", "loyalties"):
            if isinstance(data.get(key), str):
                data[key] = [part.strip() for part in data[key].split("\n") if part.strip()]
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "wanderer"


def fallback_draft(answers: dict[str, str]) -> CharacterDraft:
    """Make a playable draft without a model, useful for local/offline creation."""
    concept = answers.get("concept", "").strip()
    name = answers.get("name", "").strip() or "The Wanderer"
    tone = answers.get("temperament", "").strip()
    past = answers.get("past", "").strip()
    desire = answers.get("desire", "").strip()
    fear = answers.get("fear", "").strip()
    style = answers.get("play_style", "").lower()
    class_scores = {
        "Fighter": sum(word in style for word in ("fight", "close", "range", "protect")),
        "Rogue": sum(word in style for word in ("sneak", "deceive", "tool", "negotiate")),
        "Wizard": sum(word in style for word in ("magic", "mystery", "mysteries")),
        "Cleric": sum(word in style for word in ("heal", "support", "faith", "protect")),
    }
    cclass = max(class_scores, key=class_scores.get) if any(class_scores.values()) else "Fighter"
    past_low = past.lower()
    if any(word in past_low for word in ("soldier", "guard", "army", "war")):
        background = "Soldier"
    elif any(word in past_low for word in ("wild", "forest", "hunter", "ranger")):
        background = "Outlander"
    elif any(word in past_low for word in ("thief", "crime", "smuggl", "gang")):
        background = "Criminal"
    elif any(word in past_low for word in ("temple", "priest", "faith", "shrine")):
        background = "Acolyte"
    elif any(word in past_low for word in ("school", "book", "scholar", "study")):
        background = "Scholar"
    else:
        background = "Folk Hero"
    equipment = {
        "Wizard": ["dagger", "scholars_pack", "spellbook"],
        "Rogue": ["leather_armor", "rapier", "dagger", "thieves_tools", "burglars_pack"],
        "Cleric": ["scale_mail", "shield", "mace", "priests_pack", "holy_symbol"],
    }.get(cclass, ["chain_mail", "longsword", "shield", "explorers_pack"])
    return CharacterDraft(
        name=name,
        player=answers.get("player", "").strip() or "TBD",
        pronouns=answers.get("pronouns", "").strip() or "they/them",
        gender=answers.get("gender", "").strip() or "Unspecified",
        race=answers.get("race", "").strip() or "Human",
        character_class=cclass,
        level=int(answers.get("level", "1")) if answers.get("level", "1").isdigit() else 1,
        background=background,
        physical_description=concept or "A road-worn traveler whose history shows in their bearing.",
        abilities=["Perception +2", "Athletics +2"],
        equipment=equipment,
        open_threads=[desire] if desire else [],
        values_and_drives=[desire or "Find a purpose worth committing to."],
        fears_and_wounds=[fear or "Failing someone who depends on them."],
        voice_and_manner=[tone or "Measured, observant, and warmer than they first appear."],
        loyalties=[answers.get("loyalty", "").strip() or past
                   or "The companions who prove themselves on the road."],
        internal_contradiction=(
            answers.get("contradiction", "").strip()
            or (f"They are driven by {desire.lower()}, but fear {fear.lower()}."
                if desire and fear else CharacterDraft.internal_contradiction)
        ),
        signature_detail=answers.get("keepsake", "").strip(),
    )


SYSTEM_PROMPT = """You create grounded player characters for Driftmoor, a low-fantasy D&D-like RPG.
Turn the player's interview answers into exactly one JSON object matching the supplied schema.
Respect their authorship. Infer tasteful details, but do not add world-changing status, artifacts,
or powers. Deduce class and background from the desired play experiences and character history;
the player is not expected to know rules nomenclature. Mechanics must be conservative and playable.
Use catalog-like snake_case equipment ids.
Return JSON only, without markdown fences. Keep SOUL prose specific and actionable."""


def generation_prompt(answers: dict[str, str]) -> str:
    schema = CharacterDraft().to_dict()
    return (
        "INTERVIEW ANSWERS:\n" + json.dumps(answers, indent=2) +
        "\n\nOUTPUT SCHEMA (replace every value):\n" + json.dumps(schema, indent=2)
    )


def parse_model_draft(text: str) -> CharacterDraft:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("The model did not return a JSON character draft.")
    return CharacterDraft.from_dict(json.loads(cleaned[start:end + 1]))


def validate_draft(draft: CharacterDraft) -> list[str]:
    errors: list[str] = []
    for label, value in (("name", draft.name), ("race", draft.race),
                         ("class", draft.character_class), ("background", draft.background)):
        if not str(value).strip():
            errors.append(f"{label.title()} is required.")
    if not 1 <= draft.level <= 20:
        errors.append("Level must be between 1 and 20.")
    if draft.hp < 1:
        errors.append("HP must be at least 1.")
    if draft.ac < 1:
        errors.append("AC must be at least 1.")
    for ability in ABILITIES:
        score = getattr(draft, ability)
        if not 3 <= score <= 20:
            errors.append(f"{ability.title()} must be between 3 and 20.")
    if not draft.values_and_drives:
        errors.append("Add at least one value or drive.")
    if not draft.voice_and_manner:
        errors.append("Add at least one voice or manner note.")
    if not draft.internal_contradiction.strip():
        errors.append("Internal contradiction is required.")
    return errors


def _bullets(items: list[str], empty: str = "None") -> str:
    return "\n".join(f"- {item}" for item in items) if items else f"- {empty}"


def identity_markdown(d: CharacterDraft) -> str:
    stats = " | ".join(f"**{name[:3].upper()}:** {getattr(d, name)}" for name in ABILITIES)
    spells = "\n\n## Spells\n" + _bullets(d.spells) if d.spells else ""
    threads = "; ".join(d.open_threads) or "None yet"
    return f"""# IDENTITY.md — {d.name}

## Static Profile
- **Full Name:** {d.name}
- **Player:** {d.player}
- **Race:** {d.race}
- **Pronouns:** {d.pronouns}
- **Gender:** {d.gender}
- **Class:** {d.character_class}, Level {d.level}
- **Background:** {d.background}
- **Alignment:** {d.alignment}

## Physical Description
{d.physical_description}

## Combat Statistics
- **HP:** {d.hp}
- **AC:** {d.ac}
- **Speed:** {d.speed}
- {stats}

## Abilities and Proficiencies
{_bullets(d.abilities)}{spells}

## Equipment
{_bullets(d.equipment)}

## Runtime Defaults
- **scene_handle:** {d.name}, the {d.race.lower()} {d.character_class.lower()}

## Dynamic State
*(Updated by the game during play)*

- **Current HP:** {d.hp}
- **Mood:** {d.mood}
- **Disposition toward party:** {d.disposition}
- **Notable recent actions:** None yet
- **Active conditions:** None
- **Resources expended:** None
- **Spell slots used:** None
- **Open threads:** {threads}

## Wealth
- **Purse:** {d.purse}
"""


def soul_markdown(d: CharacterDraft) -> str:
    detail = f"\n\n## A Significant Detail\n{d.signature_detail}" if d.signature_detail else ""
    return f"""# SOUL.md — {d.name}

## Core Identity
- **Full Name:** {d.name}
- **Player:** {d.player}
- **Race/Class:** {d.race} {d.character_class}
- **Alignment:** {d.alignment}

## Values and Drives
{_bullets(d.values_and_drives)}

## Fears and Wounds
{_bullets(d.fears_and_wounds)}

## Voice and Manner
{_bullets(d.voice_and_manner)}

## Loyalties
{_bullets(d.loyalties)}

## Internal Contradiction
{d.internal_contradiction}{detail}
"""


def save_draft(draft: CharacterDraft, players_root: Path) -> Path:
    errors = validate_draft(draft)
    if errors:
        raise ValueError(" ".join(errors))
    directory = players_root / slugify(draft.name)
    if directory.exists():
        raise FileExistsError(f"A player named {draft.name!r} already exists.")
    directory.mkdir(parents=False)
    try:
        (directory / "IDENTITY.md").write_text(identity_markdown(draft), encoding="utf-8")
        (directory / "SOUL.md").write_text(soul_markdown(draft), encoding="utf-8")
        loaded = load_player_character(directory)
        if loaded.name != draft.name or loaded.hp != draft.hp:
            raise ValueError("Production loader did not reproduce the generated character.")
    except Exception:
        for child in directory.iterdir():
            child.unlink()
        directory.rmdir()
        raise
    return directory
