"""Load scene configuration from CONFIG.md + source .md files.

Replaces configure_from_json() for scenes that use the .md-based config format.
A scene is identified by the presence of scenes/<name>.md.

Stat parsing conventions
------------------------
Players / NPCs (IDENTITY.md):
    **HP:** 12
    **AC:** 14 (leather armor)     # number extracted automatically
    **Speed:** 35 ft
    **STR:** 10 | **DEX:** 16 (+3) | **CON:** 14 (+2) | **INT:** 12 | **WIS:** 15 | **CHA:** 10

Creatures (creature.md):
    Armor Class: 11
    Hit Points: 12 (2d8 + 3)      # integer extracted; dice formula ignored
    Speed: 40 ft
    Strength: 6 (-2)              # modifier in parentheses ignored
    etc.

Initial scene prose lives in PLACE.md under:
    ## Scene Introductions
    ### <char_id>
    <prose>
"""

from __future__ import annotations

import re
from pathlib import Path

from engine.llm_bridge import make_call_llm
from engine.dm_agent import DMLeft, DMRight
from engine.player_router import PlayerLeft, PlayerRight
from engine.scene_manager import RoleSet
from engine.session import CharacterSession
from engine.weapon_loader import load_weapons, load_armors, parse_character_weapons
from models.character import PlayerCharacter, NPC, Creature
from models.condition import CharacterCondition, NeurochemicalState, DimensionProfile
from models.geometry_loader import load_geometry
from models.space_time import GameTime, SceneGeometry
from models.weapon import Armor


ROOT = Path(__file__).resolve().parent.parent

_NEUROCHEMICALS = (
    "dopamine", "cortisol", "norepinephrine",
    "endorphins", "serotonin", "acetylcholine", "oxytocin",
)

_SOUL_APPEND = (
    "\n\n## Names and Strangers\n"
    "You do not know the name of someone you have not yet met. "
    "When encountering a new person, refer to them by appearance or role "
    "\u2014 \"the elf\", \"the ranger\", \"the hooded figure\" \u2014 "
    "until they tell you their name. "
    "Once a name has been spoken aloud in conversation, use it naturally."
)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _load(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def _extract_section(text: str, heading: str) -> str:
    """Text under ``## heading`` up to next ``##`` or EOF."""
    pat = rf"^##\s+{re.escape(heading)}[^\n]*\n(.*?)(?=^##\s|\Z)"
    m = re.search(pat, text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def _extract_subsection(text: str, heading: str) -> str:
    """Text under ``### heading`` up to next ``###``, ``##``, or EOF."""
    pat = rf"^###\s+{re.escape(heading)}[^\n]*\n(.*?)(?=^###\s|^##\s|\Z)"
    m = re.search(pat, text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def _parse_meta(section_text: str) -> dict[str, str]:
    """Parse ``- **key:** value`` bullet lines into {key: value}."""
    result: dict[str, str] = {}
    for line in section_text.splitlines():
        m = re.match(r"-\s*\*\*(.+?):\*\*\s*(.+)", line.strip())
        if m:
            result[m.group(1).strip()] = m.group(2).strip()
    return result


def _parse_all_char_sections(text: str) -> dict[str, dict[str, str]]:
    """Parse every ``### char_id`` subsection under ``## Characters``."""
    chars_block = _extract_section(text, "Characters")
    result: dict[str, dict[str, str]] = {}
    headings = re.findall(r"^###\s+(\S+)", chars_block, re.MULTILINE)
    for heading in headings:
        sub = _extract_subsection(chars_block, heading)
        result[heading] = _parse_meta(sub)
    return result


# ---------------------------------------------------------------------------
# IDENTITY.md stat parser (players / NPCs)
# ---------------------------------------------------------------------------

_ABILITY_SHORT = {
    "str": "strength", "dex": "dexterity", "con": "constitution",
    "int": "intelligence", "wis": "wisdom", "cha": "charisma",
}


def parse_identity_stats(text: str) -> dict:
    """Extract numeric combat stats from an IDENTITY.md file."""
    stats: dict = {
        "hp": 0, "ac": 0, "speed": "30 ft",
        "strength": 10, "dexterity": 10, "constitution": 10,
        "intelligence": 10, "wisdom": 10, "charisma": 10,
        "name": "", "race": "", "class_": "", "level": 1,
        "weapons": "", "armor": "",
        "provider": "", "model": "", "pronouns": "",
    }
    # Add neurochemical defaults
    for _dim in _NEUROCHEMICALS:
        stats[_dim] = 0.5
        stats[f"{_dim}_baseline"] = 0.0
        stats[f"{_dim}_volatility"] = 0.0

    # HP, AC, Speed
    for key, pat in [
        ("hp",    r"\*\*HP:\*\*\s*(\d+)"),
        ("ac",    r"\*\*AC:\*\*\s*(\d+)"),
        ("speed", r"\*\*Speed:\*\*\s*(\d+\s*ft)"),
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            stats[key] = int(val.split()[0]) if key in ("hp", "ac") else val

    # Ability scores: **STR:** 10 (possibly followed by modifier in parens)
    for short, full in _ABILITY_SHORT.items():
        m = re.search(rf"\*\*{short.upper()}:\*\*\s*(\d+)", text, re.IGNORECASE)
        if m:
            stats[full] = int(m.group(1))

    # Name from heading: "# IDENTITY.md — Character Name"
    m = re.search(r"^#\s+IDENTITY\.md\s+[—–-]+\s+(.+)$", text, re.MULTILINE)
    if m:
        stats["name"] = m.group(1).strip()

    # Race, Class/Level
    for key, pat in [
        ("race",   r"-\s*\*\*Race:\*\*\s*(.+)"),
        ("class_", r"-\s*\*\*Class:\*\*\s*(.+)"),
    ]:
        m2 = re.search(pat, text, re.IGNORECASE)
        if m2:
            stats[key] = m2.group(1).strip()

    if stats["class_"]:
        m3 = re.match(r"(.+?),\s*Level\s*(\d+)", stats["class_"], re.IGNORECASE)
        if m3:
            stats["class_"] = m3.group(1).strip()
            stats["level"] = int(m3.group(2))

    # Combat Equipment section: structured weapon/armor IDs
    equip_m = re.search(
        r"^##\s+Combat Equipment\s*\n(.*?)(?=^##|\Z)",
        text, re.MULTILINE | re.DOTALL,
    )
    if equip_m:
        block = equip_m.group(1)
        wm = re.search(r"-\s*\*\*weapons:\*\*\s*(.+)", block, re.IGNORECASE)
        if wm:
            stats["weapons"] = wm.group(1).strip()
        am = re.search(r"-\s*\*\*armor:\*\*\s*(\S+)", block, re.IGNORECASE)
        if am:
            stats["armor"] = am.group(1).strip()

    # Engine section: provider, model, pronouns
    engine_m = re.search(
        r"^##\s+Engine\s*\n(.*?)(?=^##|\Z)",
        text, re.MULTILINE | re.DOTALL,
    )
    if engine_m:
        block = engine_m.group(1)
        for key in ("provider", "model", "pronouns"):
            m = re.search(rf"-\s*\*\*{key}:\*\*\s*(\S+)", block, re.IGNORECASE)
            if m:
                stats[key] = m.group(1).strip()

    # Neurochemical Baseline section
    neuro_m = re.search(
        r"^##\s+Neurochemical Baseline\s*\n(.*?)(?=^##|\Z)",
        text, re.MULTILINE | re.DOTALL,
    )
    if neuro_m:
        block = neuro_m.group(1)
        for dim in _NEUROCHEMICALS:
            for suffix in ("", "_baseline", "_volatility"):
                key = f"{dim}{suffix}"
                m = re.search(
                    rf"-\s*\*\*{re.escape(key)}:\*\*\s*([\d.]+)",
                    block, re.IGNORECASE,
                )
                if m:
                    stats[key] = float(m.group(1))

    # Pronouns: also check Static Profile (- **Pronouns:** they/them)
    if not stats["pronouns"]:
        m = re.search(r"-\s*\*\*Pronouns:\*\*\s*(\S+)", text, re.IGNORECASE)
        if m:
            stats["pronouns"] = m.group(1).strip().lower()

    return stats


# ---------------------------------------------------------------------------
# Creature stat block parser
# ---------------------------------------------------------------------------

def parse_creature_stats(text: str) -> dict:
    """Extract stats from a creature .md file (e.g. shadowbeast.md)."""
    stats: dict = {
        "hp": 0, "ac": 0, "speed": "30 ft",
        "strength": 10, "dexterity": 10, "constitution": 10,
        "intelligence": 10, "wisdom": 10, "charisma": 10,
        "name": "", "race": "", "alignment": "", "challenge": "",
        "skills": [], "damage_resistances": [], "damage_vulnerabilities": [],
        "condition_immunities": [], "senses": [], "features": [], "actions": [],
        "tactics": "",
    }

    # Name: first non-blank line
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            stats["name"] = stripped
            break

    # Simple key: value pairs
    for key, pat in [
        ("race",      r"^Race:\s*(.+)$"),
        ("alignment", r"^Alignment:\s*(.+)$"),
        ("challenge", r"^Challenge:\s*(.+)$"),
    ]:
        m = re.search(pat, text, re.MULTILINE | re.IGNORECASE)
        if m:
            stats[key] = m.group(1).strip()

    m = re.search(r"^Speed:\s*(\d+\s*ft)", text, re.MULTILINE | re.IGNORECASE)
    if m:
        stats["speed"] = m.group(1).strip()

    m = re.search(r"Armor Class:\s*(\d+)", text, re.IGNORECASE)
    if m:
        stats["ac"] = int(m.group(1))

    m = re.search(r"Hit Points:\s*(\d+)", text, re.IGNORECASE)
    if m:
        stats["hp"] = int(m.group(1))

    for full in ("strength", "dexterity", "constitution",
                 "intelligence", "wisdom", "charisma"):
        m2 = re.search(rf"^{full.capitalize()}:\s*(\d+)", text,
                       re.MULTILINE | re.IGNORECASE)
        if m2:
            stats[full] = int(m2.group(1))

    def _collect_bullets(heading: str) -> list[str]:
        bm = re.search(
            rf"^{re.escape(heading)}[:\s]*\n(.*?)(?=^\w|\Z)",
            text, re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        if not bm:
            return []
        items = []
        for line in bm.group(1).splitlines():
            cleaned = re.sub(r"^[\s\u2022\-]+", "", line).strip()
            if cleaned:
                items.append(cleaned)
        return items

    stats["skills"] = _collect_bullets("Skills")
    stats["damage_resistances"] = _collect_bullets("Damage Resistances")
    stats["damage_vulnerabilities"] = _collect_bullets("Damage Vulnerabilities")
    stats["condition_immunities"] = _collect_bullets("Condition Immunities")
    stats["senses"] = _collect_bullets("Senses")
    stats["features"] = _collect_bullets("Features")

    # Actions: block between "Actions" heading and "Tactics" heading
    am = re.search(
        r"^Actions?\s*\n(.*?)(?=^Tactics?|\Z)",
        text, re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if am:
        for line in am.group(1).splitlines():
            cleaned = re.sub(r"^[\s\u2022\-]+", "", line).strip()
            if cleaned:
                stats["actions"].append(cleaned)

    tm = re.search(r"^Tactics?:?\s*\n(.*?)$", text,
                   re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if tm:
        stats["tactics"] = " ".join(
            re.sub(r"^[\s\u2022\-]+", "", ln).strip()
            for ln in tm.group(1).splitlines()
            if ln.strip()
        )

    return stats


# ---------------------------------------------------------------------------
# Scene introduction extraction from PLACE.md
# ---------------------------------------------------------------------------

def parse_scene_introductions(place_text: str) -> dict[str, str]:
    """Return {char_id: prose} from ``## Scene Introductions`` in PLACE.md."""
    block = _extract_section(place_text, "Scene Introductions")
    result: dict[str, str] = {}
    headings = re.findall(r"^###\s+(\S+)", block, re.MULTILINE)
    for heading in headings:
        result[heading] = _extract_subsection(block, heading)
    return result


# ---------------------------------------------------------------------------
# Game state sections parser
# ---------------------------------------------------------------------------

def _assemble_game_state(section_text: str) -> str:
    """Build game_state_summary from ``## Game State Sections`` bullets.

    Each bullet has the form::

        - header: My Title | file: path/to/file.md
        - header: DM Only  | file: path/to/file.md#Section Heading
        - file: path/to/standalone.md
    """
    parts: list[str] = []
    for line in section_text.splitlines():
        line = line.strip().lstrip("-").strip()
        if not line:
            continue

        # Split on first "|"
        if "|" in line:
            left, _, right = line.partition("|")
            left, right = left.strip(), right.strip()
        else:
            left, right = "", line.strip()

        # Extract optional header label (supports "header:" and "text:" prefixes)
        header = ""
        m_h = re.match(r"(?:header|text):\s*(.+)", left, re.IGNORECASE)
        if m_h:
            header = m_h.group(1).strip()

        # Extract file reference (optionally with #SectionName anchor)
        content = ""
        m_f = re.match(r"file:\s*(.+)", right, re.IGNORECASE)
        if m_f:
            file_ref = m_f.group(1).strip()
            if "#" in file_ref:
                file_path, _, section_name = file_ref.partition("#")
                file_text = _load(ROOT / file_path.strip())
                content = _extract_section(file_text, section_name.strip())
            else:
                content = _load(ROOT / file_ref)
        elif not left:
            # No "|" separator — entire line interpreted as bare "file: …"
            m_bare = re.match(r"file:\s*(.+)", line, re.IGNORECASE)
            if m_bare:
                content = _load(ROOT / m_bare.group(1).strip())

        if not content:
            continue

        block = f"# {header}\n\n{content}" if header else content
        parts.append(block)

    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Condition builder
# ---------------------------------------------------------------------------

def _build_condition(char_id: str, char_name: str, cfg: dict[str, str]) -> CharacterCondition:
    state_vals = {dim: float(cfg.get(dim, 0.5)) for dim in _NEUROCHEMICALS}
    state = NeurochemicalState(**state_vals)

    profiles: dict[str, DimensionProfile] = {}
    for dim in _NEUROCHEMICALS:
        b_key = f"{dim}_baseline"
        v_key = f"{dim}_volatility"
        if b_key in cfg or v_key in cfg:
            profiles[dim] = DimensionProfile(
                baseline=float(cfg.get(b_key, state_vals[dim])),
                volatility=float(cfg.get(v_key, 1.0)),
            )

    return CharacterCondition(
        character_id=char_id,
        character_name=char_name,
        state=state,
        profiles=profiles,
    )


# ---------------------------------------------------------------------------
# Character builders
# ---------------------------------------------------------------------------

def _build_player_or_npc(
    char_id: str,
    cfg: dict[str, str],
    introductions: dict[str, str],
) -> CharacterSession:
    identity_text = _load(ROOT / cfg["identity_file"])
    s = parse_identity_stats(identity_text)

    # CONFIG.md overrides take precedence over parsed stats
    hp    = int(cfg["hp"])    if "hp"    in cfg else s["hp"]
    ac    = int(cfg["ac"])    if "ac"    in cfg else s["ac"]
    speed = cfg["speed"]      if "speed" in cfg else s["speed"]

    char_type = cfg.get("type", "player")
    faction = cfg.get("faction", "party")
    name = cfg.get("name", s["name"]) or char_id

    if char_type == "player":
        character = PlayerCharacter(
            id=char_id,
            name=name,
            race=cfg.get("race", s["race"]),
            character_type="player",
            character_class=cfg.get("class", s["class_"]),
            level=int(cfg.get("level", s["level"])),
            hp=hp,
            current_hp=hp,
            ac=ac,
            speed=speed,
            faction=faction,
            strength=s["strength"],
            dexterity=s["dexterity"],
            constitution=s["constitution"],
            intelligence=s["intelligence"],
            wisdom=s["wisdom"],
            charisma=s["charisma"],
        )
    else:
        character = NPC(
            id=char_id,
            name=name,
            race=cfg.get("race", s["race"]),
            character_type="npc",
            role=cfg.get("role", ""),
            hp=hp,
            current_hp=hp,
            ac=ac,
            speed=speed,
            faction=faction,
            strength=s["strength"],
            dexterity=s["dexterity"],
            constitution=s["constitution"],
            intelligence=s["intelligence"],
            wisdom=s["wisdom"],
            charisma=s["charisma"],
        )

    soul = ""
    if cfg.get("soul_file"):
        soul = _load(ROOT / cfg["soul_file"])
    if soul:
        soul += _SOUL_APPEND

    initial_scene = introductions.get(char_id, "")
    if not initial_scene:
        raise ValueError(
            f"Missing '### {char_id}' under '## Scene Introductions' in PLACE.md"
        )

    return CharacterSession(
        character=character,
        condition=_build_condition(char_id, name.split()[0], cfg),
        soul=soul,
        identity=identity_text,
        initial_scene=initial_scene,
        scene_handle=cfg.get("scene_handle", ""),
    )


def _build_creature(
    char_id: str,
    cfg: dict[str, str],
    introductions: dict[str, str],
) -> CharacterSession:
    creature_text = _load(ROOT / cfg["creature_file"])
    s = parse_creature_stats(creature_text)
    name = cfg.get("name", s["name"]) or char_id

    character = Creature(
        id=char_id,
        name=name,
        race=cfg.get("race", s["race"]),
        character_type="creature",
        alignment=cfg.get("alignment", s["alignment"]),
        faction=cfg.get("faction", "hostile"),
        hp=s["hp"],
        current_hp=s["hp"],
        ac=s["ac"],
        speed=s["speed"],
        challenge=s["challenge"],
        strength=s["strength"],
        dexterity=s["dexterity"],
        constitution=s["constitution"],
        intelligence=s["intelligence"],
        wisdom=s["wisdom"],
        charisma=s["charisma"],
        skills=s["skills"],
        damage_resistances=s["damage_resistances"],
        damage_vulnerabilities=s["damage_vulnerabilities"],
        condition_immunities=s["condition_immunities"],
        senses=s["senses"],
        features=s["features"],
        actions=s["actions"],
        tactics=s["tactics"],
    )

    # Soul: soul_file > inline soul > creature_text
    soul = ""
    if cfg.get("soul_file"):
        soul = _load(ROOT / cfg["soul_file"])
    elif cfg.get("soul"):
        soul = cfg["soul"]
    else:
        soul = creature_text
    soul += _SOUL_APPEND

    # Identity: identity_file > inline identity > creature_text
    identity = ""
    if cfg.get("identity_file"):
        identity = _load(ROOT / cfg["identity_file"])
    elif cfg.get("identity"):
        identity = cfg["identity"]
    else:
        identity = creature_text

    initial_scene = introductions.get(char_id, "")
    if not initial_scene:
        raise ValueError(
            f"Missing '### {char_id}' under '## Scene Introductions' in PLACE.md"
        )

    return CharacterSession(
        character=character,
        condition=_build_condition(char_id, name, cfg),
        soul=soul,
        identity=identity,
        initial_scene=initial_scene,
        scene_handle=cfg.get("scene_handle", ""),
    )


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def configure_from_md(config_path: Path, game_time: GameTime | None = None, self_dm: bool = False):
    """Return a SceneConfig loaded from a CONFIG.md file.

    The SceneConfig class is imported lazily from engine.scene_runner to avoid
    module-level circular imports.
    """
    from engine.scene_runner import SceneConfig, _parse_starting_positions

    text = _load(config_path)

    # ── Scene metadata ──────────────────────────────────────────────────────
    scene_meta = _parse_meta(_extract_section(text, "Scene"))
    scene_name          = scene_meta["scene_name"]
    title               = scene_meta.get("title", scene_name.upper())
    narrative_title     = scene_meta.get("narrative_title", title)
    transcript_title    = scene_meta.get("transcript_title", title)
    character_summary   = scene_meta.get("character_summary", "")
    default_turns       = int(scene_meta.get("default_turns", 4))
    geometry_file       = scene_meta.get("geometry_file", "")
    place_file          = scene_meta.get("place_file", "")

    # ── Time ────────────────────────────────────────────────────────────────
    if game_time is None:
        time_meta = _parse_meta(_extract_section(text, "Time"))
        if time_meta:
            game_time = GameTime(
                hour=int(time_meta.get("hour", 12)),
                minute=int(time_meta.get("minute", 0)),
                day=int(time_meta.get("day", 1)),
                season=time_meta.get("season", "spring"),
                turn_duration=int(time_meta.get("turn_duration", 10)),
                absolute_turn=0,
            )

    # ── DM ──────────────────────────────────────────────────────────────────
    dm_meta     = _parse_meta(_extract_section(text, "DM"))
    dm_provider = dm_meta.get("provider", "anthropic")
    dm_model    = dm_meta.get("model", "claude-sonnet-4-20250514")
    dm_delay    = float(dm_meta.get("call_delay", 2.0))
    dm_llm      = make_call_llm(dm_provider, dm_model, call_delay=dm_delay)

    # ── Scene introductions — CONFIG.md first, PLACE.md as fallback ─────────
    introductions: dict[str, str] = parse_scene_introductions(text)
    if not introductions and place_file:
        place_text = _load(ROOT / place_file)
        introductions = parse_scene_introductions(place_text)

    # ── Geometry ─────────────────────────────────────────────────────────────
    geometry_summary = ""
    scene_geometry: SceneGeometry | None = None
    if geometry_file:
        geo_path = ROOT / geometry_file
        geometry_summary = _load(geo_path)
        if geo_path.exists():
            scene_geometry = load_geometry(geo_path)

    starting_positions = _parse_starting_positions(geometry_summary) if geometry_summary else {}

    # ── Weapon / Armor libraries ──────────────────────────────────────────────
    weapons_path = ROOT / "scenario" / "things" / "WEAPONS.md"
    armor_path   = ROOT / "scenario" / "things" / "ARMOR.md"
    weapon_library = load_weapons(weapons_path)
    armor_library  = load_armors(armor_path)

    # ── Characters ───────────────────────────────────────────────────────────
    char_cfgs = _parse_all_char_sections(text)
    characters: dict[str, CharacterSession] = {}
    roles: dict = {}
    character_pronouns: dict[str, str] = {}

    for char_id, cfg in char_cfgs.items():
        # For player/NPC characters, pre-fill missing cfg fields from IDENTITY.md
        if cfg.get("type") != "creature" and cfg.get("identity_file"):
            id_stats = parse_identity_stats(_load(ROOT / cfg["identity_file"]))
            for field in ("weapons", "armor", "provider", "model", "pronouns"):
                if not cfg.get(field) and id_stats.get(field):
                    cfg[field] = id_stats[field]
            for dim in _NEUROCHEMICALS:
                for suffix in ("", "_baseline", "_volatility"):
                    key = f"{dim}{suffix}"
                    if key not in cfg and id_stats.get(key):
                        cfg[key] = str(id_stats[key])

        if cfg.get("type") == "creature":
            session = _build_creature(char_id, cfg, introductions)
        else:
            session = _build_player_or_npc(char_id, cfg, introductions)

        # Attach weapons: CONFIG.md takes precedence, already merged above
        if cfg.get("weapons"):
            session.weapons = parse_character_weapons(cfg["weapons"], weapon_library)

        # Attach armor: CONFIG.md takes precedence, already merged above
        if cfg.get("armor"):
            session.armor = armor_library.get(cfg["armor"].strip())

        # Append starting position to initial_scene so the LLM knows where to begin
        pos = starting_positions.get(char_id) or starting_positions.get(
            re.sub(r"_\d+$", "", char_id)
        )
        if pos:
            x, y, zone = pos
            session.initial_scene += (
                f"\n\nYour starting position: x={x}, y={y}, zone={zone}."
            )

        characters[char_id] = session

        if cfg.get("pronouns"):
            character_pronouns[char_id] = cfg["pronouns"]

        provider   = cfg.get("provider", "anthropic")
        model      = cfg.get("model", "claude-sonnet-4-20250514")
        player_llm = make_call_llm(provider, model)
        char_dm_llm = player_llm if self_dm else dm_llm
        roles[char_id] = RoleSet(
            player_left=PlayerLeft(call_llm=player_llm),
            player_right=PlayerRight(call_llm=player_llm),
            dm_left=DMLeft(call_llm=char_dm_llm),
            dm_right=DMRight(call_llm=char_dm_llm),
        )

    # ── Game State Sections ───────────────────────────────────────────────────
    gs_text          = _extract_section(text, "Game State Sections")
    game_state_summary = _assemble_game_state(gs_text)

    # Fallback: geometry text alone
    if not game_state_summary and geometry_summary:
        game_state_summary = geometry_summary

    # When self_dm, use the first player character's LLM for narrative generation
    # to avoid hammering the DM provider (e.g. Claude 529s under load).
    narrative_provider = dm_provider
    narrative_model = dm_model
    if self_dm:
        for char_id, cfg in char_cfgs.items():
            if cfg.get("type") != "creature" and cfg.get("provider"):
                narrative_provider = cfg["provider"]
                narrative_model = cfg.get("model", dm_model)
                break

    return SceneConfig(
        scene_name=scene_name,
        title=title,
        narrative_title=narrative_title,
        transcript_title=transcript_title,
        character_summary=character_summary,
        characters=characters,
        roles=roles,
        game_state_summary=game_state_summary,
        geometry_summary=geometry_summary,
        scene_geometry=scene_geometry,
        default_turns=default_turns,
        game_time=game_time,
        dm_provider=dm_provider,
        dm_model=dm_model,
        narrative_provider=narrative_provider,
        narrative_model=narrative_model,
        character_pronouns=character_pronouns,
    )
