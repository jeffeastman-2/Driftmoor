"""Build per-player initial context briefings from GameState."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from models.character import Character, PlayerCharacter, NPC
from models.game_state import GameState
from models.place import Place
from models.thing import Thing


# ---------------------------------------------------------------------------
# Game overview — concise setting description given to every player
# ---------------------------------------------------------------------------

GAME_OVERVIEW = (
    "Driftmoor is a small town perched on a rocky coast where the Greywater "
    "River flows into the Azure Sea. Driftmoor is nestled between jagged "
    "cliffs and windswept plains, giving it an isolated but picturesque "
    "setting. It has a population of around 500: mostly humans, halflings "
    "and a few dwarves and elves. A small harbor is sheltered by rocky "
    "outcroppings. Wooden piers and fishing boats dominate the scene, with "
    "ramshackle homes belonging to the fisherfolk. The waters are teeming "
    "with fish, but the occasional shadowy form beneath the surface unnerves "
    "the locals. The heart of Driftmoor has modest stone and timber buildings "
    "that house several shops: an apothecary, a pawn shop, a rooming house, "
    "a tavern, a small church, a barber shop, a stable, a mercantile and the "
    "mayor's hall. A mile upriver are scattered farms growing hardy grains, "
    "root vegetables, and some grazing livestock. Farmers often transport "
    "their goods downstream to the harbor by raft. It is late fall; the days "
    "grow shorter and the harvest is in.\n\n"
    "You've arrived in your location by various means and at different times "
    "and have not yet met other adventurers. You may now explore the area on "
    "your own, interact with people and creatures whom you may meet and, if "
    "circumstances align, meet some of your fellow adventurers."
)


# ---------------------------------------------------------------------------
# README loader — used only for per-character backstory extraction
# ---------------------------------------------------------------------------

_README_CACHE: str | None = None


def _load_readme(scenario_dir: Path) -> str:
    global _README_CACHE
    if _README_CACHE is None:
        readme = scenario_dir / "README.md"
        _README_CACHE = readme.read_text(encoding="utf-8").strip()
    return _README_CACHE


# ---------------------------------------------------------------------------
# PlayerContext — structured container returned by build_player_context()
# ---------------------------------------------------------------------------

@dataclass
class PlayerContext:
    character_name: str = ""
    game_overview: str = ""
    character_brief: str = ""
    character_soul: str = ""
    backstory: str = ""
    location_name: str = ""
    location_description: str = ""
    scene_characters: list[dict[str, str]] = field(default_factory=list)
    available_items: list[dict[str, str]] = field(default_factory=list)

    def render(self) -> str:
        parts: list[str] = []

        parts.append("# Game Overview\n")
        parts.append(self.game_overview)

        parts.append("\n\n# Your Character\n")
        parts.append(self.character_brief)

        parts.append("\n\n# Personality & Soul\n")
        parts.append(self.character_soul)

        parts.append("\n\n# Your Backstory\n")
        parts.append(self.backstory)

        parts.append(f"\n\n# Current Location: {self.location_name}\n")
        parts.append(self.location_description)

        if self.scene_characters:
            parts.append("\n\n# Characters Present\n")
            for sc in self.scene_characters:
                parts.append(f"\n## {sc['name']}\n")
                if sc.get("role"):
                    parts.append(f"*{sc['role']}*\n")
                if sc.get("physical_description"):
                    parts.append(sc["physical_description"] + "\n")

        if self.available_items:
            parts.append("\n\n# Available Items\n")
            for item in self.available_items:
                line = f"- **{item['name']}**"
                if item.get("price"):
                    line += f" ({item['price']})"
                if item.get("description"):
                    line += f" — {item['description']}"
                parts.append(line + "\n")

        return "".join(parts)


# ---------------------------------------------------------------------------
# Extract backstory paragraph for a specific character from the README
# ---------------------------------------------------------------------------

def _extract_backstory(overview: str, character_name: str) -> str:
    """Pull the backstory paragraph for *character_name* from the README."""
    first_name = character_name.split()[0]
    lines = overview.splitlines()
    start = None
    for i, line in enumerate(lines):
        if first_name in line and line.strip().startswith(first_name):
            start = i
            break
    if start is None:
        return ""
    # Collect lines until the next character heading or end
    result_lines: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped == "":
            if result_lines:
                # Allow one blank line within paragraph, stop at second
                result_lines.append("")
                continue
            continue
        # Stop at next character heading: "Name Surname (Race Class)"
        # Headings are short lines (<80 chars) ending with ")"
        if (
            len(stripped) < 80
            and stripped.endswith(")")
            and any(
                stripped.startswith(name)
                for name in [
                    "Kaelin", "Thorgrim", "Seraphina", "Varrak",
                    "Aeliana", "Sister Amara", "Father Lilar",
                ]
            )
        ):
            break
        result_lines.append(stripped)
    return "\n".join(result_lines).strip()


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_player_context(
    gs: GameState,
    character_id: str,
    scenario_dir: Path | None = None,
) -> PlayerContext:
    """Build initial context briefing for a player character."""
    char = gs.get_character(character_id)
    if char is None:
        raise KeyError(f"Unknown character: {character_id!r}")
    if not isinstance(char, PlayerCharacter):
        raise ValueError(f"{character_id!r} is not a player character")

    # Resolve scenario_dir default
    if scenario_dir is None:
        scenario_dir = Path(__file__).resolve().parent.parent / "scenario"

    readme = _load_readme(scenario_dir)

    # Location
    place = gs.get_place(char.location) if char.location else None
    location_name = place.name if place else ""
    location_description = place.description if place else ""
    if place and place.place_raw:
        location_description = place.place_raw

    # Scene characters (excluding self)
    scene_chars: list[dict[str, str]] = []
    if char.location:
        for c in gs.get_characters_at(char.location):
            if c.id == char.id:
                continue
            entry: dict[str, str] = {"name": c.name}
            if isinstance(c, NPC):
                entry["role"] = c.role
            if c.physical_description:
                entry["physical_description"] = c.physical_description
            scene_chars.append(entry)

    # Available items at this location
    items: list[dict[str, str]] = []
    if char.location:
        for t in gs.get_things_at(char.location):
            entry = {"name": t.name}
            if t.price:
                entry["price"] = t.price
            if t.description:
                entry["description"] = t.description
            items.append(entry)

    backstory = _extract_backstory(readme, char.name)

    return PlayerContext(
        character_name=char.name,
        game_overview=GAME_OVERVIEW,
        character_brief=char.identity_raw,
        character_soul=char.soul_raw,
        backstory=backstory,
        location_name=location_name,
        location_description=location_description,
        scene_characters=scene_chars,
        available_items=items,
    )
