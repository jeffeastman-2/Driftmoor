"""Common scene runner — shared logic for all scene configurations."""

import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from engine.llm_bridge import make_call_llm
from engine.session import CharacterSession, run_session
from engine.dm_agent import DMLeft, DMRight
from engine.player_router import PlayerLeft, PlayerRight
from engine.scene_manager import RoleSet
from engine.transcript import elaborate_session_from_dir
from engine.narrator import generate_narrative_from_dir
from engine.map_renderer import render_map, render_interactive_map_html
from engine.runtime_paths import get_scene_dir, get_session_dir
from models.character import PlayerCharacter, NPC, Creature
from models.condition import (
    CharacterCondition,
    NeurochemicalState,
    DimensionProfile,
)
from models.space_time import GameTime, SceneGeometry
from models.geometry_loader import load_geometry

ROOT = Path(__file__).resolve().parent.parent


def load_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def _parse_starting_positions(geometry_text: str) -> dict[str, tuple[float, float, str]]:
    """Parse the '## Starting Positions' table from a GEOMETRY.md string.

    Returns {character_id: (x, y, zone)}.
    """
    import re
    positions: dict[str, tuple[float, float, str]] = {}
    m = re.search(r"##\s+Starting Positions.*?(\|.+?)(?=\n##|\Z)", geometry_text, re.DOTALL)
    if not m:
        return positions
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) >= 3 and cells[0] not in ("character", "---", "-"):
            try:
                char_id, x, y = cells[0], float(cells[1]), float(cells[2])
                zone = cells[3] if len(cells) >= 4 else ""
                positions[char_id] = (x, y, zone)
            except ValueError:
                pass
    return positions


@dataclass
class SceneConfig:
    scene_name: str
    title: str
    narrative_title: str
    transcript_title: str
    character_summary: str
    characters: dict[str, CharacterSession]
    roles: dict[str, RoleSet]
    game_state_summary: str
    geometry_summary: str = ""
    scene_geometry: SceneGeometry | None = None
    geometry_path: Path | None = None
    items: dict = field(default_factory=dict)  # {item_id: models.item.Item}
    default_turns: int = 4
    game_time: GameTime | None = None
    dm_provider: str = "anthropic"
    dm_model: str = "claude-sonnet-4-20250514"
    narrative_provider: str = "anthropic"
    narrative_model: str = "claude-sonnet-4-20250514"
    character_pronouns: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# JSON → SceneConfig loader
# ---------------------------------------------------------------------------

def _build_character(char_id: str, cdata: dict) -> tuple[CharacterSession, str, str]:
    """Build a CharacterSession from a JSON character dict.

    Returns (session, provider, model).
    """
    ctype = cdata["type"]
    stats = {
        k: cdata.get(k, 0)
        for k in ("strength", "dexterity", "constitution",
                   "intelligence", "wisdom", "charisma")
    }

    # Faction defaults: players/npcs → "party", creatures → "hostile"
    default_faction = "hostile" if ctype == "creature" else "party"
    faction = cdata.get("faction", default_faction)

    if ctype == "player":
        character = PlayerCharacter(
            id=char_id,
            name=cdata["name"],
            race=cdata["race"],
            character_type="player",
            character_class=cdata.get("class", ""),
            level=cdata.get("level", 1),
            hp=cdata.get("hp", 0),
            current_hp=cdata.get("hp", 0),
            ac=cdata.get("ac", 0),
            speed=cdata.get("speed", "30 ft"),
            location=cdata.get("location", ""),
            faction=faction,
            **stats,
        )
    elif ctype == "npc":
        character = NPC(
            id=char_id,
            name=cdata["name"],
            race=cdata["race"],
            character_type="npc",
            role=cdata.get("role", ""),
            home_location=cdata.get("home_location", ""),
            hp=cdata.get("hp", 0),
            current_hp=cdata.get("hp", 0),
            ac=cdata.get("ac", 0),
            speed=cdata.get("speed", "30 ft"),
            knowledge=cdata.get("knowledge", []),
            active_concerns=cdata.get("active_concerns", []),
            location=cdata.get("location", ""),
            faction=faction,
            **stats,
        )
    elif ctype == "creature":
        character = Creature(
            id=char_id,
            name=cdata["name"],
            race=cdata["race"],
            character_type="creature",
            alignment=cdata.get("alignment", ""),
            faction=faction,
            hp=cdata.get("hp", 0),
            current_hp=cdata.get("hp", 0),
            ac=cdata.get("ac", 0),
            speed=cdata.get("speed", ""),
            challenge=cdata.get("challenge", ""),
            skills=cdata.get("skills", []),
            damage_resistances=cdata.get("damage_resistances", []),
            damage_vulnerabilities=cdata.get("damage_vulnerabilities", []),
            condition_immunities=cdata.get("condition_immunities", []),
            senses=cdata.get("senses", []),
            features=cdata.get("features", []),
            actions=cdata.get("actions", []),
            tactics=cdata.get("tactics", ""),
            location=cdata.get("location", ""),
            **stats,
        )
    else:
        raise ValueError(f"Unknown character type: {ctype}")

    # Condition
    cond_data = cdata["condition"]
    state = NeurochemicalState(**cond_data["state"])
    profiles = {
        k: DimensionProfile(**v) for k, v in cond_data.get("profiles", {}).items()
    }
    condition = CharacterCondition(
        character_id=char_id,
        character_name=cdata.get("condition_name", cdata["name"].split()[0]),
        state=state,
        profiles=profiles,
    )

    # Soul and identity — file path or inline string
    soul = cdata.get("soul", "")
    if cdata.get("soul_file"):
        soul = load_file(ROOT / cdata["soul_file"])
    if soul:
        soul += (
            "\n\n## Names and Strangers\n"
            "You do not know the name of someone you have not yet met. "
            "When encountering a new person, refer to them by appearance or role "
            "\u2014 \"the elf\", \"the ranger\", \"the hooded figure\" \u2014 "
            "until they tell you their name. "
            "Once a name has been spoken aloud in conversation, use it naturally."
        )
    identity = cdata.get("identity", "")
    if cdata.get("identity_file"):
        identity = load_file(ROOT / cdata["identity_file"])

    session = CharacterSession(
        character=character,
        condition=condition,
        soul=soul,
        identity=identity,
        initial_scene=cdata["initial_scene"],
        scene_handle=cdata.get("scene_handle", ""),
    )
    return session, cdata["provider"], cdata["model"]


def _build_game_state(sections: list[dict]) -> str:
    """Assemble game_state_summary from a list of sections.

    Each section dict has:
      - "header" (optional): prefixed as "# header"
      - "file" or "text": content source
    """
    parts: list[str] = []
    for section in sections:
        block = ""
        if "file" in section:
            block = load_file(ROOT / section["file"])
        elif "text" in section:
            block = section["text"]
        if section.get("header"):
            block = f"# {section['header']}\n\n{block}"
        if block:
            parts.append(block)
    return "\n\n".join(parts)


def configure_from_json(json_path: Path, game_time: GameTime | None = None) -> SceneConfig:
    """Load a scene configuration from a JSON file.

    Args:
        json_path: Path to the scene JSON file.
        game_time: Optional override for the scene's game_time. When provided
            (e.g. from run_all.py to synchronise all scenes to a single session
            start time) it takes precedence over the ``game_time`` block in the
            JSON file.
    """
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # Scene-level DM provider (all characters share the same DM)
    dm_provider = data.get("dm_provider", "anthropic")
    dm_model = data.get("dm_model", "claude-sonnet-4-20250514")
    dm_delay = data.get("dm_call_delay", 2.0)
    dm_llm = make_call_llm(dm_provider, dm_model, call_delay=dm_delay)

    characters: dict[str, CharacterSession] = {}
    roles: dict[str, RoleSet] = {}

    for char_id, cdata in data["characters"].items():
        session, provider, model = _build_character(char_id, cdata)
        characters[char_id] = session

        player_llm = make_call_llm(provider, model)
        roles[char_id] = RoleSet(
            player_left=PlayerLeft(call_llm=player_llm),
            player_right=PlayerRight(call_llm=player_llm),
            dm_left=DMLeft(call_llm=dm_llm),
            dm_right=DMRight(call_llm=dm_llm),
        )

    game_state_summary = _build_game_state(data.get("game_state_sections", []))

    geometry_summary = ""
    scene_geometry: SceneGeometry | None = None
    geo_path: Path | None = None
    if data.get("geometry_file"):
        geo_path = ROOT / data["geometry_file"]
        geometry_summary = load_file(geo_path)
        if geo_path.exists():
            scene_geometry = load_geometry(geo_path)

    # Inject starting positions into each character's initial_scene so the
    # character agent knows exactly where it is (not just the DM).
    if geometry_summary:
        starting_positions = _parse_starting_positions(geometry_summary)
        for char_id, cs in characters.items():
            # Try exact match first, then strip trailing _<digits> (e.g. shadowbeast_1 → shadowbeast)
            import re as _re
            pos = starting_positions.get(char_id) or starting_positions.get(
                _re.sub(r"_\d+$", "", char_id)
            )
            if pos:
                x, y, zone = pos
                cs.initial_scene = (
                    cs.initial_scene
                    + f"\n\nYour starting position: x={x}, y={y}, zone={zone}."
                )

    # Game time — caller override takes precedence over JSON
    if game_time is None and "game_time" in data:
        gt = data["game_time"]
        game_time = GameTime(
            hour=gt["hour"],
            minute=gt.get("minute", 0),
            day=gt.get("day", 1),
            season=gt.get("season", "spring"),
            turn_duration=gt.get("turn_duration", 10),
            absolute_turn=0,
        )

    return SceneConfig(
        scene_name=data["scene_name"],
        title=data["title"],
        narrative_title=data["narrative_title"],
        transcript_title=data["transcript_title"],
        character_summary=data["character_summary"],
        characters=characters,
        roles=roles,
        game_state_summary=game_state_summary,
        geometry_summary=geometry_summary,
        scene_geometry=scene_geometry,
        geometry_path=geo_path,
        default_turns=data.get("default_turns", 4),
        game_time=game_time,
        dm_provider=dm_provider,
        dm_model=dm_model,
        narrative_provider=data.get("narrative_provider", "anthropic"),
        narrative_model=data.get("narrative_model", "claude-sonnet-4-20250514"),
    )


def _write_runtime_map(
    *,
    geometry_path: Path,
    scene_name: str,
    checkpoint_dir: Path,
) -> None:
    """Write the runtime map (full character paths from snapshots) into the
    checkpoint directory.

    The static scenario map (starting positions only) lives alongside
    ``GEOMETRY.md`` in ``scenario/places/.../<scene>/`` and is treated as a
    committed artifact. Regenerate it explicitly with::

        python -m engine.map_renderer <scene_slug>

    when geometry changes — not on every run.
    """
    runtime_map = checkpoint_dir / f"{scene_name}_map.png"
    runtime_map_html = checkpoint_dir / f"{scene_name}_map.html"
    try:
        render_map(
            geometry_path, runtime_map, snapshot_dir=checkpoint_dir,
            title=f"{scene_name.replace('_', ' ').title()} — character paths",
        )
        print(f"  Written to {runtime_map}")

        render_interactive_map_html(
            geometry_path,
            runtime_map_html,
            snapshot_dir=checkpoint_dir,
            title=f"{scene_name.replace('_', ' ').title()} — interactive character paths",
        )
        print(f"  Written to {runtime_map_html}")
    except Exception as exc:  # noqa: BLE001 — visualization is best-effort
        print(f"  [map] failed: {exc}")


def print_turn_result(turn_result):
    print(f"\n{'=' * 70}")
    print(f"  TURN {turn_result.turn}  —  Initiative: {', '.join(turn_result.initiative_order)}")
    print(f"{'=' * 70}")

    for cr in turn_result.character_results:
        print(f"\n  --- {cr.character_id.upper()} ---")
        print(f"  Intent:     {cr.intent.intent}")
        if cr.intent.movement_target:
            print(f"  Move to:    {cr.intent.movement_target}")
        if cr.intent.interaction_target:
            print(f"  Interact:   {cr.intent.interaction_target}")
        if cr.output.spoken and cr.output.spoken.lower() not in ("(silent)", "(silence)", ""):
            print(f"  Spoken:     \"{cr.output.spoken}\"")
        else:
            print(f"  Spoken:     (silent)")
        print(f"  Approved:   {cr.adjudication.approved}")
        if cr.adjudication.condition_deltas:
            deltas = ", ".join(
                f"{k}: {v:+.2f}" for k, v in cr.adjudication.condition_deltas.items()
            )
            print(f"  Deltas:     {deltas}")
        if cr.adjudication.spatial_events:
            print(f"  Events:     {cr.adjudication.spatial_events}")
        print(f"\n  Narration:")
        print(f"  {cr.narration.prose}")


async def run_scene(config: SceneConfig, num_turns: int | None = None):
    """Run a scene: execute turns, print results, generate transcript + narrative."""
    if num_turns is None:
        num_turns = config.default_turns

    checkpoint_dir = get_scene_dir(config.scene_name)

    # Clear previous run
    if checkpoint_dir.exists():
        shutil.rmtree(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{config.title} — {num_turns} turns")
    print(f"Characters: {config.character_summary}")
    print(f"Checkpoints: {checkpoint_dir}\n")

    start = time.monotonic()
    result = await run_session(
        config.characters, config.roles,
        num_turns=num_turns,
        game_state_summary=config.game_state_summary,
        geometry_summary=config.geometry_summary,
        scene_geometry=config.scene_geometry,
        items=config.items or None,
        checkpoint_dir=checkpoint_dir,
        game_time=config.game_time,
    )
    elapsed = time.monotonic() - start

    for turn_result in result.turns:
        print_turn_result(turn_result)

    print(f"\n{'=' * 70}")
    print(f"  SESSION COMPLETE — {num_turns} turns in {elapsed:.1f}s")
    print(f"{'=' * 70}")

    print(f"\nFinal conditions:")
    for char_id, condition in result.final_conditions.items():
        d = condition.state.dopamine
        c = condition.state.cortisol
        n = condition.state.norepinephrine
        print(f"  {char_id:15s}  dop={d:.2f}  cor={c:.2f}  nor={n:.2f}")

    scene_name = config.scene_name
    print(f"\nGenerating transcript...")
    elaborate_session_from_dir(
        checkpoint_dir,
        output_path=checkpoint_dir / f"{scene_name}_transcript.txt",
        title=config.transcript_title,
    )
    print(f"  Written to {checkpoint_dir / f'{scene_name}_transcript.txt'}")

    print(f"Generating narrative...")
    await generate_narrative_from_dir(
        checkpoint_dir,
        provider=config.narrative_provider, model=config.narrative_model,
        title=config.narrative_title,
        character_pronouns=config.character_pronouns or None,
        output_path=checkpoint_dir / f"{scene_name}_story.txt",
    )
    print(f"  Written to {checkpoint_dir / f'{scene_name}_story.txt'}")

    if config.geometry_path is not None and config.geometry_path.exists():
        _write_runtime_map(
            geometry_path=config.geometry_path,
            scene_name=scene_name,
            checkpoint_dir=checkpoint_dir,
        )
