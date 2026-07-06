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
        "gender": "",
        "weapons": "", "armor": "",
        "provider": "", "model": "", "pronouns": "",
        "player_transport": "", "channel": "", "host": "",
        "inbox": "", "outbox": "", "scene_handle": "",
        "activation": "",
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

    # Race, Class/Level, Gender
    for key, pat in [
        ("race",   r"-\s*\*\*Race:\*\*\s*(.+)"),
        ("class_", r"-\s*\*\*Class:\*\*\s*(.+)"),
        ("gender", r"-\s*\*\*Gender:\*\*\s*(.+)"),
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
        pm = re.search(r"-\s*\*\*provisions:\*\*\s*(.+)", block, re.IGNORECASE)
        if pm:
            stats["provisions"] = pm.group(1).strip()

    # Equipment section: a FLAT list of catalog id references (any order), each
    # ``id[+N][: Display Name]``, resolved against the catalogs at load time.
    # Anything that isn't a catalog id stays free-text. (A legacy
    # ``## Combat Equipment`` block above still supplies structured weapons/armor
    # for un-migrated characters; their prose ``## Equipment`` list simply
    # resolves to all-free-text.)
    eq_m = re.search(
        r"^##\s+Equipment\s*\n(.*?)(?=^##|\Z)",
        text, re.MULTILINE | re.DOTALL,
    )
    if eq_m:
        entries = [
            ln.strip()[1:].strip()
            for ln in eq_m.group(1).splitlines()
            if ln.strip().startswith("-") and ln.strip()[1:].strip()
        ]
        if entries:
            stats["equipment_entries"] = entries

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

    # Runtime / Transport defaults for human-channel routing.
    runtime_m = re.search(
        r"^##\s+(?:Runtime(?:\s+Defaults)?|Transport(?:\s+Defaults)?)\s*\n(.*?)(?=^##|\Z)",
        text, re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if runtime_m:
        block = runtime_m.group(1)
        for key in (
            "player_transport",
            "channel",
            "host",
            "inbox",
            "outbox",
            "scene_handle",
            "activation",
        ):
            m = re.search(rf"-\s*\*\*{key}:\*\*\s*(.+)", block, re.IGNORECASE)
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

    # Fallback: infer pronouns from explicit Gender when Pronouns is absent.
    # We only infer from a dedicated Gender field to avoid overreaching.
    if not stats["pronouns"] and stats["gender"]:
        g = stats["gender"].strip().lower()
        if g in {"female", "woman", "girl"}:
            stats["pronouns"] = "she/her"
        elif g in {"male", "man", "boy"}:
            stats["pronouns"] = "he/him"
        elif g in {"nonbinary", "non-binary", "enby"}:
            stats["pronouns"] = "they/them"

    return stats


def _char_llm_config(
    cfg: dict, dm_provider: str, dm_model: str
) -> tuple[str, str]:
    """Per-character (provider, model) for a scene.

    The scene's DM provider/model are the default for every character; a
    character's scene block may override either. LLM routing is a scene/runtime
    concern, so identities never contribute here.
    """
    return cfg.get("provider") or dm_provider, cfg.get("model") or dm_model


# A flat Equipment entry: a lower-case snake_case catalog id, an optional weapon
# attack-bonus override (+N / -N), and an optional ": Display Name" instance
# label. Anything not matching (prose like "Holy symbol") is a free-text item.
_EQUIP_ENTRY_RE = re.compile(r"^([a-z0-9_]+)([+-]\d+)?\s*(?::\s*(.+))?$")


def _parse_equip_entry(entry: str):
    """Parse ``id[+N][: Name]`` -> (id, bonus_str, name) or None for free-text."""
    m = _EQUIP_ENTRY_RE.match((entry or "").strip())
    if not m:
        return None
    return m.group(1), (m.group(2) or ""), (m.group(3) or "").strip()


def _instantiate(lib, cid: str, name: str):
    """Deep-copy a catalog template (independent per-character instance) and
    apply the optional display-name override."""
    import copy
    inst = copy.deepcopy(lib[cid])
    if name:
        inst.label = name
    return inst


def _apply_equipment(session, id_stats, cfg, weapon_library, armor_library,
                     consumable_library, gear_library) -> None:
    """Resolve a character's equipment onto the session. Structured weapons/armor
    may come from a legacy ``## Combat Equipment`` (via ``cfg``); a flat
    ``## Equipment`` id list contributes weapons, armor, and pack Things. Each
    flat entry ``id[+N][: Name]`` is routed by which catalog holds the id;
    anything unrecognized stays a free-text possession. (``+N`` is a legacy
    manual attack-bonus override — it will be computed at runtime once the
    proficiency model lands.)"""
    from models.thing import DRINKABLE, EDIBLE
    weapons = (parse_character_weapons(cfg["weapons"], weapon_library)
               if cfg.get("weapons") else [])
    armor_id = cfg.get("armor")
    pack: list = []
    free_text: list = []
    for entry in (id_stats.get("equipment_entries") or []):
        parsed = _parse_equip_entry(entry)
        if parsed is None:
            free_text.append(entry)
            continue
        eid, bonus, name = parsed
        if eid in weapon_library:
            w = parse_character_weapons(eid + bonus, weapon_library)
            if w and name:               # honor the ": Display Name" override
                w[0].name = name
            weapons.extend(w)
        elif eid in armor_library:
            armor_id = eid
        elif eid in consumable_library:
            pack.append(_instantiate(consumable_library, eid, name))
        elif eid in gear_library:
            pack.append(_instantiate(gear_library, eid, name))
        else:
            free_text.append(name or entry)
    if weapons:
        session.weapons = weapons
    if armor_id:
        session.armor = armor_library.get(str(armor_id).strip())
    session.pack = pack
    if free_text:
        session.character.equipment = free_text
    # Seed hunger/thirst when the character carries food/drink, so consuming
    # visibly reduces them (until a needs tick drives them over time).
    if getattr(session, "condition", None) is not None and any(
            (EDIBLE in t.affordances or DRINKABLE in t.affordances) for t in pack):
        ext = session.condition.extensions
        ext.setdefault("hunger", 0.5)
        ext.setdefault("thirst", 0.5)


def _merge_identity_defaults(cfg: dict[str, str], id_stats: dict) -> None:
    """Fill missing scene config keys from identity-derived defaults.

    Scene config remains authoritative; this only fills absent values.
    """
    # NOTE: provider/model are intentionally NOT merged from the identity.
    # LLM routing is a scene/runtime concern (see _char_llm_config): a
    # character inherits the scene's DM model unless its scene block overrides.
    for field in (
        "weapons",
        "armor",
        "pronouns",
        "player_transport",
        "channel",
        "host",
        "inbox",
        "outbox",
        "scene_handle",
        "activation",
    ):
        if not cfg.get(field) and id_stats.get(field):
            cfg[field] = str(id_stats[field])

    # Backward-compat: scene config currently stores transport mode in
    # the "player" key. If missing, map identity player_transport onto it.
    if not cfg.get("player") and id_stats.get("player_transport"):
        cfg["player"] = str(id_stats["player_transport"])


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


def _normalize_player_transport(player_value: str, channel_value: str) -> str:
    """Map scene metadata to normalized player transport mode.

    Legacy configs used ``player`` for a human's name (e.g. "Wayne").
    Unknown values are treated as ``llm`` for backward compatibility.
    """
    raw = (player_value or "").strip().lower()
    channel = (channel_value or "").strip().lower()

    # Prefer explicit channel when present.
    if channel in {"telegram", "whatsapp", "file", "llm"}:
        return channel

    if raw in {"telegram", "tg", "bot:telegram", "human:telegram"}:
        return "telegram"
    if raw in {"whatsapp", "wa", "bot:whatsapp", "human:whatsapp"}:
        return "whatsapp"
    if raw in {"file", "filesystem", "human:file"}:
        return "file"
    if raw in {"llm", "agent", "ai", "npc", ""}:
        return "llm"

    # Legacy: player name (not transport)
    return "llm"


def _warn_unarmed_combatants(characters: dict, scene_name: str) -> list[str]:
    """Flag (to stderr) characters with no structured weapons in a scene that
    can see combat. Returns the flagged character ids (for tests).

    The deterministic CombatResolver only engages for a character with at least
    one structured weapon (parsed from a ``- **weapons:** ...`` line). Without
    one, an attack silently degrades to LLM-narrated resolution that may apply
    no HP — so surface the data gap at load instead of mid-fight. Only fires
    when a hostile-faction combatant is present; otherwise the scene is social
    and weaponlessness is expected.
    """
    has_hostile = any(
        getattr(getattr(s, "character", None), "faction", "party") == "hostile"
        for s in characters.values()
    )
    if not has_hostile:
        return []
    unarmed = sorted(
        cid for cid, s in characters.items() if not getattr(s, "weapons", None)
    )
    if unarmed:
        import sys
        print(
            f"[md_loader] WARNING: combat-capable scene '{scene_name}' has "
            f"character(s) with no structured weapons; their attacks fall back "
            f"to unreliable LLM narration: {', '.join(unarmed)}. Add a "
            f"'- **weapons:** <id>+<bonus>, ...' line to each.",
            file=sys.stderr,
        )
    return unarmed


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
    dm_provider = dm_meta.get("provider", "ollama")
    dm_model    = dm_meta.get("model", "gemma4:26b")
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
    geo_path: Path | None = None
    if geometry_file:
        geo_path = ROOT / geometry_file
        geometry_summary = _load(geo_path)
        if geo_path.exists():
            scene_geometry = load_geometry(geo_path)
        else:
            geo_path = None

    starting_positions = _parse_starting_positions(geometry_summary) if geometry_summary else {}
    # ── Contents (items) ──────────────────────────────────────────
    # CONTENTS.md is expected as a sibling of GEOMETRY.md. Loading is
    # best-effort: a missing or malformed file leaves ``items`` empty so
    # legacy scenes without CONTENTS.md continue to run.
    items: dict = {}
    if geo_path is not None:
        scene_dir = geo_path.parent
        zones_dir = scene_dir / "zones"
        contents_path = scene_dir / "CONTENTS.md"
        from models.contents_loader import (
            load_contents_with_geometry,
            load_zone_contents_with_geometry,
        )
        try:
            # Prefer per-zone source files when present; fall back to legacy
            # scene-level CONTENTS.md for older scenes.
            if zones_dir.exists() and any(zones_dir.glob("*.md")):
                items = load_zone_contents_with_geometry(
                    zones_dir, geo_path, scene_geometry=scene_geometry,
                )
            elif contents_path.exists():
                items = load_contents_with_geometry(
                    contents_path, geo_path, scene_geometry=scene_geometry,
                )
        except Exception as e:  # pragma: no cover - logged for diagnostics
            import sys
            src = str(zones_dir if zones_dir.exists() else contents_path)
            print(
                f"[md_loader] WARNING: failed to load scene items from {src}: {e}",
                file=sys.stderr,
            )
    # ── Puzzles ───────────────────────────────────────────────────────────────
    # The optional ``## Puzzles`` block of the same CONTENTS.md. Each puzzle
    # owns its own state machine (see engine.puzzles); the loader only turns
    # authored specs into live puzzle objects. Best-effort, like items.
    from engine.puzzles import PuzzleRegistry
    puzzle_registry: PuzzleRegistry = PuzzleRegistry()
    if geo_path is not None:
        contents_path = geo_path.parent / "CONTENTS.md"
        if contents_path.exists():
            from models.contents_loader import load_puzzles
            from engine.puzzles import build_registry
            try:
                puzzle_registry = build_registry(load_puzzles(contents_path))
            except Exception as e:  # pragma: no cover - logged for diagnostics
                import sys
                print(
                    f"[md_loader] WARNING: failed to load puzzles from "
                    f"{contents_path}: {e}",
                    file=sys.stderr,
                )
    # ── Weapon / Armor libraries ──────────────────────────────────────────────
    weapons_path = ROOT / "scenario" / "things" / "WEAPONS.md"
    armor_path   = ROOT / "scenario" / "things" / "ARMOR.md"
    weapon_library = load_weapons(weapons_path)
    armor_library  = load_armors(armor_path)
    from engine.consumable_loader import load_consumables, load_gear
    consumable_library = load_consumables(ROOT / "scenario" / "things" / "CONSUMABLES.md")
    gear_library = load_gear(ROOT / "scenario" / "things" / "GEAR.md")

    # Resolve pickable weapon items (``*Weapon:* mace+1``) into base Weapons now
    # that the library is loaded, so a picked-up item can be wielded in combat.
    from engine.weapon_loader import build_item_weapon
    from models.thing import derive_affordances
    for _it in (items or {}).values():
        _spec = getattr(_it, "weapon_spec", None)
        if _spec:
            _it.weapon = build_item_weapon(
                _spec, weapon_library,
                item_id=_it.id, label=_it.label or _it.id.replace("_", " "),
            )
        # Tag each scene Thing with the affordances/effects derived from its
        # parsed fields (pickable/weapon/interactions) so the manipulation
        # dispatch and affordance-aware grounding can reason over them.
        derive_affordances(_it)

    # ── Characters ───────────────────────────────────────────────────────────
    char_cfgs = _parse_all_char_sections(text)
    characters: dict[str, CharacterSession] = {}
    roles: dict = {}
    character_pronouns: dict[str, str] = {}

    for char_id, cfg in char_cfgs.items():
        # For player/NPC characters, pre-fill missing cfg fields from IDENTITY.md
        id_stats: dict = {}
        if cfg.get("type") != "creature" and cfg.get("identity_file"):
            id_stats = parse_identity_stats(_load(ROOT / cfg["identity_file"]))
            _merge_identity_defaults(cfg, id_stats)
            for dim in _NEUROCHEMICALS:
                for suffix in ("", "_baseline", "_volatility"):
                    key = f"{dim}{suffix}"
                    if key not in cfg and id_stats.get(key):
                        cfg[key] = str(id_stats[key])

        if cfg.get("type") == "creature":
            session = _build_creature(char_id, cfg, introductions)
        else:
            session = _build_player_or_npc(char_id, cfg, introductions)

        # Resolve equipment (structured legacy weapons/armor + the flat
        # ## Equipment id list) onto weapons / armor / pack / free-text.
        _apply_equipment(session, id_stats, cfg, weapon_library, armor_library,
                         consumable_library, gear_library)

        # Append starting position to initial_scene so the LLM knows where to begin
        pos = starting_positions.get(char_id) or starting_positions.get(
            re.sub(r"_\d+$", "", char_id)
        )
        if pos:
            x, y, zone = pos
            session.initial_scene += (
                f"\n\nYour starting position: x={x}, y={y}, zone={zone}."
            )

        # Phase 3b: per-character activation trigger (default "always").
        session.activation = cfg.get("activation", "always").strip() or "always"

        # Player transport metadata: this is routing intent only. Existing
        # LLM role wiring is unchanged until a transport router is enabled.
        session.player_transport = _normalize_player_transport(
            cfg.get("player", ""),
            cfg.get("channel", ""),
        )
        session.player_host = cfg.get("host", "").strip()
        session.player_channel = cfg.get("channel", "").strip()
        session.player_inbox = cfg.get("inbox", "").strip()
        session.player_outbox = cfg.get("outbox", "").strip()

        characters[char_id] = session

        if cfg.get("pronouns"):
            character_pronouns[char_id] = cfg["pronouns"]

        # LLM routing is a scene/runtime concern: a character inherits the
        # scene's DM provider/model unless its own scene block overrides them.
        # Identities never carry provider/model (see _merge_identity_defaults).
        provider, model = _char_llm_config(cfg, dm_provider, dm_model)
        player_llm = make_call_llm(provider, model)
        char_dm_llm = player_llm if self_dm else dm_llm
        roles[char_id] = RoleSet(
            player_left=PlayerLeft(call_llm=player_llm),
            player_right=PlayerRight(call_llm=player_llm),
            dm_left=DMLeft(call_llm=char_dm_llm),
            dm_right=DMRight(call_llm=char_dm_llm),
        )

    # Surface combatants who will silently fall back to LLM-narrated attacks
    # (no structured weapon → CombatResolver is bypassed).
    _warn_unarmed_combatants(characters, scene_name)

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
        geometry_path=geo_path,
        items=items,
        puzzles=puzzle_registry,
        default_turns=default_turns,
        game_time=game_time,
        dm_provider=dm_provider,
        dm_model=dm_model,
        narrative_provider=narrative_provider,
        narrative_model=narrative_model,
        character_pronouns=character_pronouns,
    )
