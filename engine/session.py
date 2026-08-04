"""Direct Python game loop — no Lobster, no OpenClaw.

Thin orchestrator that wires together TurnCycle, initiative,
conditions, and checkpointing. Human WhatsApp routing can be
re-added later when OpenClaw is stable.

Usage:
    result = await run_session(characters, character_roles, num_turns=3)
"""

from __future__ import annotations

import asyncio
import base64
import json
import math
import platform
import re
import random
import shlex
import subprocess
import time
from functools import lru_cache
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import AsyncIterator, Optional, TYPE_CHECKING

from engine.initiative import roll_initiative
from engine.player_router import RoleContext, ActionIntent, CharacterOutput
from engine.scene_manager import TurnCycle, TurnResult, RoleSet, CharacterTurnResult
from engine.dm_agent import Adjudication, Narration
from models.character import Character
from models.condition import CharacterCondition, render_condition
from models.geometry_loader import load_geometry
from models.space_time import GameTime, Polygon, Position, SceneGeometry


from engine.debug import _dbg
from engine.combat_resolver import CombatResolver
from engine.spell_resolver import (
    ActiveSpellEffect,
    SpellCastRequest,
    SpellResolver,
    SpellRuntimeState,
)
from models.game_state import GameState
from models.weapon import Weapon, Armor

if TYPE_CHECKING:
    from engine.puzzles import PuzzleRegistry
    from models.item import Item


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMBAT_EVENT = "combat_initiated"
EXIT_EVENT = "exits_scene"
MELEE_DURATION = 1  # minutes per combat turn
EXPLORATION_ROUNDS_PER_TURN = 10  # one exploration turn spans ~10 melee rounds
MAX_MELEE_ROUNDS = 20  # safety cap — melee rounds never count against num_turns


# ---------------------------------------------------------------------------
# Session data types
# ---------------------------------------------------------------------------

@dataclass
class CharacterSession:
    """Per-character state for a session."""
    character: Character
    condition: CharacterCondition
    soul: str
    identity: str
    initial_scene: str
    scene_handle: str = ""  # How others see this character before names are exchanged
    weapons: list[Weapon] = field(default_factory=list)
    armor: Armor | None = None
    # Phase 2: weapon/item ids currently in hand (subset of the kit). Natural
    # weapons are always available and need not appear here. See engine.loadout.
    wielded: list[str] = field(default_factory=list)
    # Non-weapon items currently held in-hand (e.g. a picked-up torch). A subset
    # of inventory; each occupies one hand like a weapon. See engine.loadout.
    held_items: list[str] = field(default_factory=list)
    # A derived Thing-view of the character's kit (weapons + armor) with
    # affordances + carry-state, rebuilt from the loadout by
    # ``loadout.materialize_things``. The unified manipulation dispatch
    # (engine.manipulation) and affordance-aware grounding read this; the
    # loadout fields above remain the source of truth.
    things: list = field(default_factory=list)
    # The character's instantiated catalog possessions — food & drink
    # (CONSUMABLES) plus tools & wearables (GEAR) — each a models.thing.Thing
    # with affordances + effects, referenced by id in IDENTITY. Stateful
    # (consuming removes one); materialize_things folds these into ``things`` so
    # the unified eat/drink/wear/use dispatch and grounding reach them.
    pack: list = field(default_factory=list)
    # Phase 3b: dormancy. "always" = active from turn 1 (default).
    # "zone_entry:<Zone Name>" = activate when an opposing-faction
    # character enters that zone. "door_open:<door_id>" = activate when
    # the named door fires its open side effect.
    activation: str = "always"
    # Python-owned episodic memory used to reinforce continuity in prompts.
    episodic_memory: list[str] = field(default_factory=list)
    recent_interactions: list[str] = field(default_factory=list)
    # People this character has encountered, keyed by stable character id.
    # Unlike the scene cast, this survives transitions and checkpoint reloads.
    known_people: dict[str, str] = field(default_factory=dict)
    last_zone_seen: str = ""
    # Input routing metadata for player-controlled characters.
    # Current engine behavior remains LLM-driven; transport fields are used by
    # external bridges (e.g. Telegram) and future turn-router integration.
    player_transport: str = "llm"  # llm | telegram | whatsapp | file
    player_host: str = ""  # e.g. "ultra" when inbox/outbox are remote
    player_channel: str = ""
    player_inbox: str = ""
    player_outbox: str = ""
    # Cursor into raw_history lines for transport prompts; used to send only
    # new statements/actions since this player's last turn.
    transport_history_cursor: int = 0
    # Python-owned body posture, independent of planar map position.
    posture: str = "standing"


@dataclass
class SessionResult:
    """Results from a complete session."""
    turns: list[TurnResult]
    final_conditions: dict[str, CharacterCondition]
    scene_history: str


# ---------------------------------------------------------------------------
# Position tracking helpers
# ---------------------------------------------------------------------------

def _parse_positions_table(game_state_summary: str) -> dict[str, tuple[float, float, str]]:
    """Extract the character position table from game_state_summary.

    Expects a markdown table with columns: character | x | y | zone.
    Returns a dict of char_id → (x, y, zone).  Skips the header row.
    """
    positions: dict[str, tuple[float, float, str]] = {}
    pattern = r'\|\s*(\w+)\s*\|\s*(-?\d+\.?\d*)\s*\|\s*(-?\d+\.?\d*)\s*\|\s*(\w+)\s*\|'
    for m in re.finditer(pattern, game_state_summary):
        char_id, x, y, zone = m.group(1), m.group(2), m.group(3), m.group(4)
        if char_id.lower() == "character":
            continue  # header row
        positions[char_id] = (float(x), float(y), zone.upper())
    return positions


def _update_positions_in_summary(
    game_state_summary: str,
    positions: dict[str, tuple[float, float, str]],
) -> str:
    """Replace the position table in game_state_summary with current values.

    Rebuilds the ``| character | x | y | zone |`` table with live positions so
    the DM always sees where characters actually are rather than turn-0 values.
    """
    if not positions:
        return game_state_summary
    rows = ["| character | x | y | zone |", "|-----------|-----|-----|------|"]
    for char_id, (x, y, zone) in positions.items():
        rows.append(f"| {char_id} | {x} | {y} | {zone} |")
    new_table = "\n".join(rows)
    # Replace the existing table (header + any number of data rows)
    updated = re.sub(
        r'\| character \| x \| y \| zone \|.*?(?=\n#|\n\n|\Z)',
        new_table,
        game_state_summary,
        flags=re.DOTALL,
    )
    return updated


def _speed_to_feet(speed_str: str) -> float:
    """Parse a D&D speed string (e.g. '40 ft', '30 ft.') into feet.

    Coordinates are in feet so no conversion is needed — just extract the number.
    Returns feet per round. Defaults to 30.0 if unparseable.
    """
    m = re.search(r'(\d+)', speed_str or "")
    return float(m.group(1)) if m else 30.0


def _movement_budget_feet(speed_str: str, *, in_combat: bool) -> float:
    """Movement cap in feet for the current turn.

    Character speed is authored as feet per melee round. Outside combat, one
    Driftmoor turn spans multiple rounds (10), so movement budget scales by
    that factor. In combat, keep one-round movement.
    """
    per_round = _speed_to_feet(speed_str)
    if in_combat:
        return per_round
    return per_round * EXPLORATION_ROUNDS_PER_TURN


def _clamp_to_authored_home(
    character_id: str,
    candidate: tuple[float, float, str],
    character,
    scene_geometry,
) -> tuple[float, float, str]:
    """Keep an authored resident within its radius of its turn-0 position."""
    radius = getattr(character, "movement_radius", None)
    starts = getattr(scene_geometry, "starting_positions", None)
    if radius is None or not starts:
        return candidate
    home = starts.get(character_id)
    if home is None:
        return candidate
    radius = max(0.0, float(radius))
    dx = float(candidate[0]) - float(home.x)
    dy = float(candidate[1]) - float(home.y)
    distance = math.hypot(dx, dy)
    if distance <= radius or distance == 0:
        return candidate
    scale = radius / distance
    return (
        float(home.x) + dx * scale,
        float(home.y) + dy * scale,
        candidate[2],
    )


_NUMBER_WORDS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}


def _parse_number_words(text: str) -> Optional[float]:
    """Parse a small English number phrase (e.g. "ten", "twenty five")."""
    toks = [t for t in re.split(r"[^a-z]+", (text or "").lower()) if t]
    if not toks:
        return None

    total = 0
    current = 0
    saw_number = False
    for tok in toks:
        if tok == "and":
            continue
        val = _NUMBER_WORDS.get(tok)
        if val is None:
            return None
        saw_number = True
        if val == 100:
            current = max(1, current) * 100
        elif val >= 20 and val % 10 == 0:
            current += val
        else:
            current += val
    total += current
    return float(total) if saw_number else None


def _requested_movement_feet(intent_text: str) -> Optional[float]:
    """Return explicit requested movement distance in feet, if present.

    Supports both numeric and word-number forms such as ``10 ft`` and
    ``ten feet``. Returns None when no explicit distance is present.
    """
    text = (intent_text or "").lower()
    if not text:
        return None

    # Numeric form: "10 ft", "10 feet", "10 foot".
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:ft\.?|feet|foot)\b", text)
    if m is not None:
        try:
            return float(m.group(1))
        except ValueError:
            return None

    # Word form: "ten feet", "twenty five foot".
    toks = [t for t in re.split(r"[^a-z]+", text) if t]
    for i, tok in enumerate(toks):
        if tok not in {"ft", "feet", "foot"}:
            continue
        phrase: list[str] = []
        j = i - 1
        while j >= 0:
            t = toks[j]
            if t in _NUMBER_WORDS or t == "and":
                phrase.append(t)
                j -= 1
                continue
            break
        if not phrase:
            continue
        parsed = _parse_number_words(" ".join(reversed(phrase)))
        if parsed is not None:
            return parsed
    return None


def _movement_cap_for_intent(
    speed_str: str,
    intent_text: str,
    *,
    in_combat: bool,
    requested_distance_ft: Optional[float] = None,
) -> float:
    """Turn movement cap, honoring explicit intent distance when provided."""
    budget = _movement_budget_feet(speed_str, in_combat=in_combat)
    requested = (
        requested_distance_ft
        if requested_distance_ft is not None
        else _requested_movement_feet(intent_text)
    )
    if requested is None or requested <= 0:
        return budget
    return min(budget, requested)


def _is_search_like_intent(intent_text: str) -> bool:
    """Intent text is a search/examine style action.

    LATN-grounded on the ``search``/``examine`` dims (search/look/scan/check/
    sift/examine/inspect/investigate all live in the lexicon)."""
    from engine import latn_resolver
    return latn_resolver.intent_has_action(intent_text, "search", "examine")


# Generic text helpers live in engine.text_util (extracted); re-exported so
# the many turn-loop call sites use them unqualified.
from engine.text_util import _normalize_target_name  # noqa: E402


def _position_bucket(
    pos: Optional[tuple[float, float, str]],
) -> tuple[int, int, str]:
    """Bucket position into ~5 ft bins for repeat-search detection."""
    if pos is None:
        return (0, 0, "")
    x, y, z = pos
    return (int(round(x / 5.0)), int(round(y / 5.0)), (z or "").upper())


def _choose_novel_item_for_search(
    *,
    character_id: str,
    current_positions: dict[str, tuple[float, float, str]],
    items: Optional[dict],
    current_target_norm: str,
) -> Optional[tuple[str, float, float, str]]:
    """Pick a same-zone item that is likely to yield new information.

    Preference order: unexamined items first, then nearest by distance.
    Returns (label, x, y, zone) or None when no candidate is available.
    """
    if not items:
        return None
    actor_pos = current_positions.get(character_id)
    if actor_pos is None:
        return None
    ax, ay, az = actor_pos
    actor_zone = (az or "").upper()
    if not actor_zone:
        return None

    candidates: list[tuple[int, float, str, float, float, str]] = []
    for item in items.values():
        zone = (item.zone or "").upper()
        if zone != actor_zone or item.position is None:
            continue
        label = item.label or item.id.replace("_", " ")
        if _normalize_target_name(label) == current_target_norm:
            continue
        dist = ((item.position.x - ax) ** 2 + (item.position.y - ay) ** 2) ** 0.5
        unseen_rank = 0 if not item.discovered_by else 1
        candidates.append((
            unseen_rank,
            dist,
            label,
            float(item.position.x),
            float(item.position.y),
            zone,
        ))

    if not candidates:
        return None
    candidates.sort(key=lambda t: (t[0], t[1], t[2]))
    _, _, label, ix, iy, zone = candidates[0]
    return label, ix, iy, zone


def _all_zone_items_examined(
    *,
    character_id: str,
    current_positions: dict[str, tuple[float, float, str]],
    items: Optional[dict],
) -> bool:
    """Return True when all items in the actor's current zone were examined."""
    if not items:
        return False
    actor_pos = current_positions.get(character_id)
    if actor_pos is None:
        return False
    actor_zone = (actor_pos[2] or "").upper()
    if not actor_zone:
        return False

    in_zone = [
        it for it in items.values()
        if (it.zone or "").upper() == actor_zone and it.position is not None
    ]
    if not in_zone:
        return False
    return all(bool(it.discovered_by) for it in in_zone)


# Spatial geometry helpers live in engine.geometry (extracted). Re-exported
# so the turn loop and other callers use them unqualified.
from engine.geometry import (  # noqa: E402
    _check_boundary_crossing,
    _check_impassable,
    _clamp_position,
    _entry_point_inside_zone,
    _point_to_segment_distance_2d,
    _polygons_are_adjacent,
    _segment_polygon_entry,
)


def _choose_exploration_waypoint(
    *,
    character_id: str,
    current_positions: dict[str, tuple[float, float, str]],
    scene_geometry: Optional[SceneGeometry],
    visited: Optional[set[str]] = None,
) -> Optional[tuple[str, float, float]]:
    """Choose a nearby exploration waypoint that pushes movement forward.

    Prefers adjacent zones first (to avoid global jumps), then falls back to
    any zone if adjacency cannot be determined. Within each set, unvisited
    zones outrank visited zones. Returned coordinates are nudged just inside
    the destination zone to reduce seam-clamping on boundary lines.
    Returns (zone_name, x, y) or None.
    """
    if scene_geometry is None:
        return None
    actor_pos = current_positions.get(character_id)
    if actor_pos is None:
        return None
    ax, ay, az = actor_pos
    current_zone = (az or "").upper()
    seen = {z.upper() for z in (visited or set())}

    zones_by_upper = {
        name.upper(): polygon for name, polygon in scene_geometry.zones.items()
    }
    current_poly = zones_by_upper.get(current_zone)

    candidates: list[tuple[int, float, str, float, float]] = []

    def _add_candidate(zone_upper: str, poly) -> None:
        if zone_upper == current_zone or zone_upper == "FOREST":
            return
        verts = poly.vertices
        if not verts:
            return
        tx, ty = _entry_point_inside_zone(
            actor_x=ax,
            actor_y=ay,
            target_poly=poly,
            inset=3.0,
        )
        dist = ((tx - ax) ** 2 + (ty - ay) ** 2) ** 0.5
        unseen_rank = 0 if zone_upper not in seen else 1
        candidates.append((unseen_rank, dist, zone_upper, tx, ty))

    # Prefer adjacent zones first. This prevents jumps to far/hidden branches.
    if current_poly is not None:
        for zone_upper, poly in zones_by_upper.items():
            if _polygons_are_adjacent(current_poly, poly):
                _add_candidate(zone_upper, poly)

    # Fallback when no adjacent candidates were detected.
    if not candidates:
        for zone_upper, poly in zones_by_upper.items():
            _add_candidate(zone_upper, poly)

    if not candidates:
        return None
    candidates.sort(key=lambda t: (t[0], t[1], t[2]))
    _, _, zone, x, y = candidates[0]
    return zone, x, y


def _waypoint_for_zone(
    *,
    character_id: str,
    current_positions: dict[str, tuple[float, float, str]],
    scene_geometry: Optional[SceneGeometry],
    target_zone: str,
) -> Optional[tuple[float, float]]:
    """Return a seam-safe movement point inside the requested target zone."""
    if scene_geometry is None or not target_zone:
        return None
    actor_pos = current_positions.get(character_id)
    if actor_pos is None:
        return None
    ax, ay, _ = actor_pos

    zone_upper = target_zone.upper()
    target_poly = None
    for zname, poly in scene_geometry.zones.items():
        if zname.upper() == zone_upper:
            target_poly = poly
            break
    if target_poly is None:
        return None

    tx, ty = _entry_point_inside_zone(
        actor_x=ax,
        actor_y=ay,
        target_poly=target_poly,
        inset=3.0,
    )
    return tx, ty


def _next_zone_toward(
    scene_geometry: Optional[SceneGeometry],
    from_zone: str,
    to_zone: str,
) -> Optional[str]:
    """First zone to step into from ``from_zone`` on a shortest path to
    ``to_zone``, via the zone-adjacency graph (``_polygons_are_adjacent``).

    Lets a cross-zone move advance one hop per turn through the connecting
    passages instead of drawing a straight line that runs into walls. Returns
    the destination's stored zone name (so it feeds ``_waypoint_for_zone``), or
    None when the zones are the same, unknown, or not connected.
    """
    if scene_geometry is None:
        return None
    zones = scene_geometry.zones or {}
    fz, tz = (from_zone or "").upper(), (to_zone or "").upper()
    if not fz or not tz or fz == tz:
        return None
    by_upper = {name.upper(): name for name in zones}
    if fz not in by_upper or tz not in by_upper:
        return None

    def _neighbors(zu: str) -> list[str]:
        poly = zones[by_upper[zu]]
        return [
            name.upper()
            for name, p in zones.items()
            if name.upper() != zu and _polygons_are_adjacent(poly, p)
        ]

    from collections import deque
    visited = {fz}
    parent: dict[str, str] = {}
    queue = deque([fz])
    while queue:
        cur = queue.popleft()
        if cur == tz:
            step = cur
            while parent.get(step) != fz and step in parent:
                step = parent[step]
            return by_upper.get(step)
        for nb in _neighbors(cur):
            if nb not in visited:
                visited.add(nb)
                parent[nb] = cur
                queue.append(nb)
    return None


def _should_block_backtrack(
    *,
    current_zone: str,
    target_zone: str,
    visited: Optional[set[str]],
    party_focus_zone: Optional[str],
) -> bool:
    """Return True when movement would backtrack away from party focus.

    While a party focus is active, prevent leaving the focus zone for any
    previously visited zone. Moves to unvisited zones remain allowed.
    """
    if not current_zone or not target_zone or not party_focus_zone:
        return False
    cz = current_zone.upper()
    tz = target_zone.upper()
    focus = party_focus_zone.upper()
    if cz != focus:
        return False
    if tz == focus:
        return False
    seen = {z.upper() for z in (visited or set())}
    return tz in seen


def _follows_party_focus(cs: CharacterSession) -> bool:
    """Whether this AI character is an explicitly attached companion."""
    character = getattr(cs, "character", None)
    return bool(
        character is not None
        and getattr(character, "character_type", "") != "player"
        and getattr(character, "follows_party", False)
    )


def _exploration_redirect_intent(
    *,
    zone_name: str,
    known_zones: Optional[set[str]] = None,
) -> str:
    """Build exploration redirect text without leaking unknown zone names.

    If the destination zone has not been visited by the actor yet, keep the
    directive generic ("move deeper") so hidden geometry labels are not
    surfaced in-character.
    """
    known = {z.upper() for z in (known_zones or set())}
    if zone_name and zone_name.upper() in known:
        return f"Move toward {zone_name} and continue exploration there."
    return "Move deeper through the passage and continue exploration there."


def _puzzle_items_in_zone(
    current_zone: str,
    items: Optional[dict],
    puzzles: Optional["PuzzleRegistry"],
) -> list:
    """Return puzzle-input items located in the given zone, if any."""
    if not current_zone or not items or not puzzles:
        return []
    target_ids = puzzles.target_ids
    if not target_ids:
        return []
    zone = current_zone.upper()
    return [
        item for item in items.values()
        if item.id in target_ids and (item.zone or "").upper() == zone
    ]


def _zone_has_unresolved_puzzle(
    *,
    current_zone: str,
    items: Optional[dict],
    puzzles: Optional["PuzzleRegistry"],
) -> bool:
    """Return True when the actor stands in a zone with an unsolved puzzle."""
    if not current_zone or not items or not puzzles:
        return False
    for item in _puzzle_items_in_zone(current_zone, items, puzzles):
        puzzle = puzzles.puzzle_for_item(item.id)
        if puzzle is not None and not puzzle.solved:
            return True
    return False


def _build_puzzle_pressure_block(
    *,
    current_zone: str,
    items: Optional[dict],
    puzzles: Optional["PuzzleRegistry"],
) -> str:
    """Return a context block reminding the actor to keep working a live puzzle."""
    if not _zone_has_unresolved_puzzle(
        current_zone=current_zone,
        items=items,
        puzzles=puzzles,
    ):
        return ""

    zone_items = _puzzle_items_in_zone(current_zone, items, puzzles)
    glyph_names = ", ".join((it.label or it.id).strip() for it in zone_items)
    # Report progress from the (single) live puzzle covering this zone.
    seq_text = "not yet started"
    for it in zone_items:
        puzzle = puzzles.puzzle_for_item(it.id) if puzzles else None
        if puzzle is not None and not puzzle.solved:
            seq_text = puzzle.progress_summary()
            break
    return (
        "## Unresolved puzzle (keep working this zone before leaving)\n"
        f"The current zone still contains an unsolved puzzle: {glyph_names}. "
        f"Current puzzle progress: {seq_text}. "
        "Stay with the puzzle until it advances, resolves, or clearly proves "
        "to be a dead end."
    )


def _choose_puzzle_focus_item(
    *,
    character_id: str,
    current_positions: dict[str, tuple[float, float, str]],
    items: Optional[dict],
    puzzles: Optional["PuzzleRegistry"],
    current_target_norm: str,
) -> Optional[tuple[str, float, float, str]]:
    """Prefer a puzzle-input item in the actor's current zone when live."""
    if not items:
        return None
    actor_pos = current_positions.get(character_id)
    if actor_pos is None:
        return None
    ax, ay, az = actor_pos
    actor_zone = (az or "").upper()
    if not actor_zone:
        return None

    candidates: list[tuple[int, float, str, float, float, str]] = []
    for item in _puzzle_items_in_zone(actor_zone, items, puzzles):
        if item.position is None:
            continue
        label = item.label or item.id.replace("_", " ")
        if _normalize_target_name(label) == current_target_norm:
            continue
        dist = ((item.position.x - ax) ** 2 + (item.position.y - ay) ** 2) ** 0.5
        unseen_rank = 0 if not item.discovered_by else 1
        candidates.append((
            unseen_rank,
            dist,
            label,
            float(item.position.x),
            float(item.position.y),
            actor_zone,
        ))

    if not candidates:
        return None
    candidates.sort(key=lambda t: (t[0], t[1], t[2]))
    _, _, label, ix, iy, zone = candidates[0]
    return label, ix, iy, zone


def _broadcast_effects(
    side_effects: list[dict],
    recent_events,
    turn_num: int,
    game_time: Optional[GameTime],
) -> None:
    """Append any authored ``broadcast`` text from puzzle effects.

    The broadcast text lives with the puzzle definition (CONTENTS.md), not in
    the loop, so other characters perceive world consequences (e.g. a creature
    feeling a door grind open) without scene-specific code here.
    """
    for effect in side_effects or []:
        text = (effect.get("broadcast") or "").strip()
        if not text:
            continue
        ts = (
            f"{game_time.hour}:{game_time.minute:02d}"
            if game_time else f"t{turn_num}"
        )
        recent_events.append((turn_num, f"{ts} | {text}"))


def _first_sentence(text: str) -> str:
    """Return the first sentence of ``text``, ensuring trailing punctuation."""
    head = (text or "").split(". ", 1)[0].strip()
    if head and not head.endswith("."):
        head += "."
    return head


async def _run_puzzle_exchange(
    *,
    first_item,
    puzzle,
    puzzles: "PuzzleRegistry",
    interactive: bool,
    turn_cycle: TurnCycle,
    cs: CharacterSession,
    context: RoleContext,
    output: CharacterOutput,
    character_id: str,
    turn_num: int,
    game_time: Optional[GameTime],
    items: dict,
    actor_zone: str,
    characters: dict[str, CharacterSession],
    attack_log: list[str],
    recent_events,
    scene_geometry=None,
) -> list[dict]:
    """Drive a puzzle's state machine for one actor and return its effects.

    Outside combat (``interactive=True``) this runs the atomic *focused
    exchange*: the actor presses one input, the puzzle returns a terse
    response plus a "what do you do next?" prompt, and the same actor is
    re-prompted for the next press — all within this single turn, with the
    rest of the world frozen. The exchange ends the moment the puzzle solves,
    resets, or the actor does anything other than press the next input
    (any incorrect response exits). In combat (``interactive=False``) a
    single press resolves with no re-prompt.

    The actor's ``output.action`` is rewritten to describe the *whole*
    sequence actually performed (not just the opening press), so the turn's
    narration and the post-turn RESULT packet reflect what really happened —
    including the final solve — rather than only the first press.

    All press logging (attack_log, recent_events, episodic memory, discovery)
    is handled here so the caller's generic interaction bookkeeping does not
    double-count puzzle presses. Returns the accumulated side effects (door
    open/close) so the caller can broadcast them and feed activation checks.
    """
    import dataclasses

    from engine.verb_resolver import _detect_verb
    # LATN-first (flag-gated, shallow fallback) for the mid-puzzle re-prompt:
    # the actor presses inputs, which LATN parses well (incl. "the top glyph").
    from engine.latn_integration import (
        infer_interaction_target,
        resolve_item_interaction,
    )

    handle = (
        characters[character_id].scene_handle
        or characters[character_id].character.name
        or character_id
    )
    zone_label = actor_zone.upper() or "this zone"

    def _ts() -> str:
        return (
            f"{game_time.hour}:{game_time.minute:02d}"
            if game_time else f"t{turn_num}"
        )

    side_effects_all: list[dict] = []
    pressed_labels: list[str] = []
    press_detail_lines: list[str] = []
    solved = False
    current_item = first_item
    # Each correct press can advance the sequence by one; bound the loop a
    # little beyond the solution length as a safety net.
    max_steps = len(puzzle.target_ids) + 2

    for _ in range(max_steps):
        label = current_item.label or current_item.id
        result = puzzles.press(current_item.id)
        response = (result.response or "").strip()

        current_item.discovered_by.add(character_id)
        side_effects_all.extend(result.side_effects)
        pressed_labels.append(label)
        solved = result.solved

        if response:
            # Detail lines are buffered (not appended to attack_log yet) so the
            # ordered-sequence summary can lead the puzzle block in the
            # narrator's authoritative resolution log.
            press_detail_lines.append(
                f"[PUZZLE] {character_id} pressed {label}: {response}"
            )
            head = _first_sentence(response)
            recent_events.append((turn_num, (
                f"{_ts()} | {handle} pressed {label} — {head}"
            )))
            _append_memory_note(
                cs,
                f"Turn {turn_num}: you pressed {label} in {zone_label} "
                f"and learned: {head}",
            )

        # Real-time per-press feedback to human transport channels: each press
        # (step, solve, reset, or reverse) emits its own result message so the
        # player sees the mechanism respond as it happens. Crucially this is
        # the only place the terminal solve/reset/reverse response surfaces,
        # since those end the exchange with no follow-up prompt.
        if interactive:
            await _emit_puzzle_press_result(
                cs=cs,
                character_id=character_id,
                turn_num=turn_num,
                label=label,
                response=response,
                solved=result.solved,
            )

        # End conditions: solved, reset, reversed, or non-interactive mode.
        if not result.awaiting_input or not interactive:
            break

        # Focused re-prompt: ask the SAME actor what they do next. The press
        # response was just emitted as its own message, so the prompt carries
        # only the question — no need to restate the feedback here.
        feedback = (
            "## You are mid-sequence at a mechanism (act now)\n"
            f"{result.follow_up_prompt}"
        )
        focused = dataclasses.replace(
            context,
            scene_context=f"{context.scene_context}\n\n{feedback}",
        )
        next_intent, _ = await _player_roles_via_transport(
            turn_cycle=turn_cycle,
            context=focused,
            cs=cs,
            items=items,
        )

        next_target = next_intent.interaction_target or infer_interaction_target(
            next_intent.intent or "", items, characters, actor_zone,
            scene_geometry,
        )
        next_resolved = (
            resolve_item_interaction(
                intent_text=next_intent.intent or "",
                interaction_target=next_target,
                items=items,
                characters=characters,
                character_zone=actor_zone,
                scene_geometry=scene_geometry,
            )
            if next_target else None
        )
        next_item = next_resolved[0] if next_resolved else None

        # Anything other than pressing the next input to THIS puzzle ends the
        # exchange and abandons the in-progress sequence (no penalty).
        if (
            next_item is None
            or puzzles.puzzle_for_item(next_item.id) is not puzzle
            or _detect_verb(next_intent.intent or "") != "press"
        ):
            puzzle.abandon()
            press_detail_lines.append(
                f"[PUZZLE] {character_id} stepped away from the sequence "
                f"before completing it; the mechanism resets."
            )
            break

        current_item = next_item

    # Rewrite the actor's action so narration and the RESULT packet describe
    # the full sequence performed, not just the opening press.
    if pressed_labels:
        output.action = _describe_press_sequence(pressed_labels, solved=solved)
        # Lead the narrator's authoritative resolution log with one ordered
        # summary line so its prose describes the whole sequence rather than
        # anchoring on the opening press; the per-press detail lines follow for
        # color. (The narrator is told to narrate the resolution log over the
        # intent.)
        if len(pressed_labels) > 1:
            ordered = " → ".join(pressed_labels)
            tail = (
                "; the sequence completed."
                if solved
                else "; the sequence did not complete."
            )
            attack_log.append(
                f"[PUZZLE] {character_id} pressed, in order: {ordered}{tail}"
            )
    attack_log.extend(press_detail_lines)

    return side_effects_all


def _describe_press_sequence(labels: list[str], *, solved: bool) -> str:
    """Humanize the presses performed in a focused puzzle exchange.

    Produces an authoritative ``output.action`` line so the turn's narration
    and the post-turn RESULT packet reflect every press, ending with whether
    the sequence completed.
    """
    if not labels:
        return ""
    if len(labels) == 1:
        action = f"Presses {labels[0]}"
    else:
        action = "Presses " + ", ".join(labels[:-1]) + f", then {labels[-1]}, in sequence"
    if solved:
        action += ", completing the sequence"
    return action + "."


# Combat resolution helpers live in engine.combat (extracted). Re-exported so
# the turn loop and tests (test_combat_resolver) use them unqualified.
from engine.combat import (  # noqa: E402
    _enforce_attack_range,
    _find_combat_target,
    _max_attack_range,
    _max_attacks,
    _resolve_attacks,
)


# ---------------------------------------------------------------------------
# DM Ledger
# ---------------------------------------------------------------------------

_PERMANENT_TRIGGERS = {"boundary_crossed", "combat_initiated", "exits_scene"}


class DMLedger:
    """Engine-authoritative event log injected into every DM adjudication prompt.

    Solves the stateless-LLM state-tracking problem: the engine owns all
    authoritative facts (positions, combat status, crossing outcomes) and
    presents them to the DM as a verified ledger rather than leaving the DM
    to re-derive them from ambiguous prose.

    Structure:
      Permanent Events  — first-time significant events kept forever
      Recent Turns      — sliding window of last 4 turns
      Current State     — live snapshot rebuilt every turn
    """

    def __init__(self) -> None:
        self.permanent_events: list[str] = []
        self._recent_turns: deque[list[str]] = deque(maxlen=4)
        self._current_turn: list[str] = []

    def record(self, cr: "CharacterTurnResult", game_time=None) -> None:  # noqa: F821
        """Record one character result into the current-turn buffer."""
        from engine.scene_manager import CharacterTurnResult  # local to avoid circular  # noqa: F401

        timestamp = (
            f"{game_time.hour}:{game_time.minute:02d}"
            if game_time else f"t{cr.turn}"
        )
        adj = cr.adjudication

        # Action summary (first 70 chars)
        action = (cr.output.action or "")[:70].rstrip()

        # Dice result — "N vs DC M SUCCESS/FAILED"
        dice_str = ""
        roll_m = re.search(
            r'(\d+)\s+(?:vs?\.?\s+)?dc\s*:?\s*(\d+)', adj.notes, re.IGNORECASE
        )
        if roll_m:
            r, d = int(roll_m.group(1)), int(roll_m.group(2))
            dice_str = f" | d20={r} vs DC={d} {'SUCCESS' if r >= d else 'FAILED'}"

        # Position
        pos_str = ""
        if adj.new_position:
            x, y, zone = adj.new_position
            pos_str = f" | pos x={x},y={y},{zone}"

        # Events
        events = [
            e.strip().rstrip(".")
            for e in adj.spatial_events
            if e.strip().lower() not in ("none", "none.", "")
        ]
        events_str = f" | {', '.join(events)}" if events else ""

        status = "APPROVED" if adj.approved else "BLOCKED"
        line = (
            f"{timestamp} | {cr.character_id} | {action}"
            f"{dice_str} | {status}{pos_str}{events_str}"
        )
        self._current_turn.append(line)

        # Permanent events: boundary crossings, combat start, exits
        # Only record permanent events when the action was approved.
        for event in events:
            if not adj.approved:
                continue
            key = event.lower()
            if any(t in key for t in _PERMANENT_TRIGGERS):
                perm = f"{timestamp} | {cr.character_id} | {event.upper()}{pos_str}"
                if perm not in self.permanent_events:
                    self.permanent_events.append(perm)

    def flush_turn(self) -> None:
        """Move current-turn entries into the recent-turns sliding window."""
        if self._current_turn:
            self._recent_turns.append(list(self._current_turn))
            self._current_turn = []

    def render(
        self,
        current_positions: dict[str, tuple[float, float, str]],
        in_combat: bool,
        game_time=None,
        characters: dict | None = None,
    ) -> str:
        """Return the full ledger block for insertion at the top of a DM prompt."""
        lines: list[str] = ["## DM Ledger (engine-verified — do not contradict)\n"]

        if self.permanent_events:
            lines.append("### Permanent Events")
            lines.extend(self.permanent_events)
            lines.append("")

        all_recent = [ln for turn in self._recent_turns for ln in turn]
        all_recent.extend(self._current_turn)
        if all_recent:
            lines.append("### Recent Turns")
            lines.extend(all_recent)
            lines.append("")

        lines.append("### Current State")
        for char_id, (x, y, zone) in current_positions.items():
            side = "INSIDE barrier" if zone.upper() == "GLADE" else "outside barrier"
            hp_str = ""
            stat_str = ""
            if characters and char_id in characters:
                char = characters[char_id].character
                curr = getattr(char, "current_hp", char.hp)
                hp_str = f" | HP {curr}/{char.hp}"
                speed = getattr(char, "speed", "") or ""
                ac = getattr(char, "ac", 0) or 0
                bits = []
                if speed:
                    bits.append(f"speed {speed}")
                if ac:
                    bits.append(f"AC {ac}")
                if bits:
                    stat_str = " | " + ", ".join(bits)
            lines.append(f"- {char_id}: x={x}, y={y}, zone={zone} ({side}){hp_str}{stat_str}")
        lines.append(f"- Combat: {'ACTIVE' if in_combat else 'INACTIVE'}")
        if game_time:
            lines.append(
                f"- Game time: {game_time.hour}:{game_time.minute:02d}"
                f" | period: {game_time.period}"
            )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_perception(
    character_id: str,
    scene_geometry: Optional[SceneGeometry],
    current_positions: dict[str, tuple[float, float, str]],
    active_characters: set[str],
    characters: Optional[dict[str, "CharacterSession"]] = None,
    items: Optional[dict] = None,
) -> str:
    """Return a preformatted perception block for what character_id can see.

    Perception is gated by the acting character's effective sight range —
    the scene's ambient (light-limited) range for the zone they stand in
    (``SceneGeometry.ambient_sight_range``), extended by their darkvision.
    Mist and occlusion (``visibility_rules`` via ``can_see``) and line of
    sight still apply on top and are *not* pierced by darkvision. Creatures
    beyond visual range but within a non-visual sense (blindsight,
    tremorsense, keen hearing/smell) are surfaced as "sensed, not seen".

    If geometry/positions are unavailable, falls back to a coarse "co-present"
    list of other active characters so social scenes without full geometry do
    not collapse into artificial solitude.

    Other creatures are referred to by their ``scene_handle`` (e.g. "the
    elf ranger") rather than their internal character_id, because the
    acting character has not necessarily been introduced to them by name.

    When ``items`` is provided, items are reported in two sub-headers so
    "in view" means only what is currently seen:

    * ``Items in view:`` — items the actor can perceive RIGHT NOW (within sight
      range *and* line of sight, which lets a character at a zone seam perceive
      nearby items in an adjoining zone). Past half the sight range they read as
      a vague placeholder; an in-view item already examined is flagged
      ``(already examined)`` so it isn't re-examined.
    * ``Items remembered or examined:`` — items previously examined by anyone in
      the party (``discovered_by`` non-empty) whose identity/location is recalled
      but which are NOT currently in sight.
    """
    import math
    from models.senses import resolve_senses

    def _co_present_lines() -> str:
        lines: list[str] = []
        for other_id in sorted(active_characters):
            if other_id == character_id:
                continue
            label = other_id
            faction_tag = ""
            if characters is not None:
                cs_other = characters.get(other_id)
                if cs_other is not None:
                    if cs_other.scene_handle:
                        label = cs_other.scene_handle
                    fac = getattr(cs_other.character, "faction", "neutral")
                    if fac == "hostile":
                        faction_tag = "HOSTILE, "
                    elif fac == "party":
                        faction_tag = "ally, "
            lines.append(f"- {label} ({faction_tag}co-present)")
        return "\n".join(lines)

    if scene_geometry is None:
        _dbg(f"[PERCEPTION] {character_id}: no scene_geometry — using co-present fallback")
        return _co_present_lines()
    my_pos = current_positions.get(character_id)
    if my_pos is None:
        _dbg(f"[PERCEPTION] {character_id}: no position — using co-present fallback")
        return _co_present_lines()

    _dbg(f"[PERCEPTION] {character_id} at {my_pos}")

    # Resolve the acting character's effective sight range for the zone they
    # stand in: ambient (light) range extended by darkvision. None ambient =
    # unlimited (open-air / lit scene). Non-visual senses give a separate
    # detection range used for "sensed, not seen" creatures.
    my_pos_pt = Position(my_pos[0], my_pos[1])
    my_zone_name = my_pos[2] or scene_geometry.zone_at(my_pos_pt)
    obs_senses = resolve_senses()
    if characters is not None:
        cs_me = characters.get(character_id)
        if cs_me is not None:
            ch_me = cs_me.character
            obs_senses = resolve_senses(
                race=getattr(ch_me, "race", "") or "",
                senses=getattr(ch_me, "senses", None),
                features=getattr(ch_me, "features", None),
            )
    ambient = scene_geometry.ambient_sight_range(my_zone_name)
    if ambient is None:
        visual_ft = math.inf
    else:
        visual_ft = max(ambient, obs_senses.darkvision_ft)
    nonvisual_ft = obs_senses.nonvisual_range_ft
    _dbg(
        f"[PERCEPTION]   sight: ambient={ambient} darkvision="
        f"{obs_senses.darkvision_ft} visual={visual_ft} nonvisual={nonvisual_ft}"
    )

    lines: list[str] = []
    for other_id, other_pos in current_positions.items():
        if other_id == character_id or other_id not in active_characters:
            continue
        a = Position(my_pos[0], my_pos[1])
        b = Position(other_pos[0], other_pos[1])
        in_los = scene_geometry.can_see(a, b)
        zone_a = scene_geometry.zone_at(a) or "?"
        zone_b = scene_geometry.zone_at(b) or "?"
        dist = math.hypot(b.x - a.x, b.y - a.y)
        sees = in_los and dist <= visual_ft
        sensed = (not sees) and nonvisual_ft > 0 and dist <= nonvisual_ft
        _dbg(
            f"[PERCEPTION]   {other_id} at {other_pos}: {zone_a}->{zone_b} "
            f"dist={dist:.1f} los={in_los} sees={sees} sensed={sensed}"
        )
        if not (sees or sensed):
            continue
        dist_rounded = round(dist / 5) * 5
        zone = other_pos[2] or zone_b
        label = other_id
        faction_tag = ""
        if characters is not None:
            cs_other = characters.get(other_id)
            if cs_other is not None:
                if cs_other.scene_handle:
                    label = cs_other.scene_handle
                fac = getattr(cs_other.character, "faction", "neutral")
                if fac == "hostile":
                    faction_tag = "HOSTILE, "
                elif fac == "party":
                    faction_tag = "ally, "
        if sees:
            lines.append(
                f"- {label} ({faction_tag}{zone}, ~{dist_rounded:.0f} ft away)"
            )
        else:
            manner = "by vibration" if obs_senses.tremorsense_ft >= dist else "by sound/scent"
            lines.append(
                f"- {label} ({faction_tag}{zone}, ~{dist_rounded:.0f} ft away "
                f"— sensed {manner}, not seen)"
            )

    result = "\n".join(lines) if lines else ""

    # ------------------------------------------------------------------
    # Items the character can perceive.
    #
    # An item is currently visible when it is within the observer's sight
    # range AND in line of sight (can_see ray-traces across zone seams, so a
    # character standing at a boundary perceives nearby items in the
    # adjoining zone). Items previously examined by anyone in the party have
    # a known location and are recalled regardless of distance or sight.
    # ------------------------------------------------------------------
    if items:
        from models.item import apparent_size_band

        my_zone = (my_zone_name or "").upper()
        # Identifiability falls off with distance like perspective: an item's
        # apparent size (≈ size / distance) selects a perception band. Within
        # near/intermediate it is identified (or shown its authored band text);
        # at far/distant it reads as a vague shape (authored or generic); below
        # the smallest band it is too small to make out and is omitted. Items
        # examined or remembered by the party keep their identity regardless.
        view_lines: list[str] = []      # currently visible
        recalled_lines: list[str] = []  # examined/remembered but not in sight now
        for item in items.values():
            if item.position is None:
                continue
            # Carried items are in someone's pack, not lying loose in the
            # scene — they must not surface as perceivable scene items.
            if item.holder is not None:
                continue
            item_pt = item.position
            # 3D distance: the actor stands on the floor at her location; the
            # item sits at its zone floor + its own height (position.z is height
            # above the floor). This separates items stacked in z (the trigger
            # glyphs) and reflects chambers at different elevations.
            _actor_z = scene_geometry.floor_z_at(my_pos_pt)
            _item_z = scene_geometry.floor_z_at(item_pt) + (getattr(item_pt, "z", 0.0) or 0.0)
            dist = (
                (item_pt.x - my_pos[0]) ** 2
                + (item_pt.y - my_pos[1]) ** 2
                + (_item_z - _actor_z) ** 2
            ) ** 0.5
            currently_visible = (
                dist <= visual_ft
                and scene_geometry.can_see(my_pos_pt, item_pt)
            )
            examined = bool(item.discovered_by)
            if not (currently_visible or examined):
                continue
            dist_rounded = round(dist / 5) * 5
            label = item.label or item.id.replace("_", " ")
            item_zone = item.zone or ""
            zone_prefix = (
                f"{item_zone}, " if item_zone.upper() != my_zone else ""
            )
            if not currently_visible:
                # Examined/remembered but out of sight now — its own section so
                # "Items in view" means only what the actor can currently see.
                recalled_lines.append(
                    f"- {label} ({zone_prefix}~{dist_rounded:.0f} ft away)"
                )
                continue
            if examined:
                # Visible AND already known — identity established; flag it so
                # the actor doesn't re-examine it.
                view_lines.append(
                    f"- {label} ({zone_prefix}~{dist_rounded:.0f} ft away) (already examined)"
                )
                continue
            band = apparent_size_band(item.size_ft, dist)
            if band is None:
                # Too small/far to make out at all — omit it.
                continue
            authored = item.appearance_bands.get(band)
            if authored:
                shown = authored
            elif band in ("near", "intermediate"):
                # Close enough (for its size) to identify by sight.
                shown = label
            else:
                # An unauthored small prop at long range is visual clutter, not
                # a useful "mystery shape".  Omit it until close enough to
                # identify; authored far/distant silhouettes still appear.
                continue
            view_lines.append(
                f"- {shown} ({zone_prefix}~{dist_rounded:.0f} ft away)"
            )
        if view_lines:
            block = "Items in view:\n" + "\n".join(view_lines)
            result = f"{result}\n\n{block}" if result else block
        if recalled_lines:
            block = "Items remembered or examined:\n" + "\n".join(recalled_lines)
            result = f"{result}\n\n{block}" if result else block

    _dbg(f"[PERCEPTION]   result: {repr(result)}")
    return result


def _zones_for_point(
    pos: Position,
    zones: dict[str, "Polygon"],
    edge_tol: float = 3.0,
) -> set[str]:
    """Return zones containing pos, or whose polygon edges are within
    edge_tol feet of pos. Lets landmarks on a zone seam (e.g. a doorway
    polygon vertex shared by two chambers) be associated with both.
    """
    out: set[str] = set()
    for zname, poly in zones.items():
        if poly.contains(pos):
            out.add(zname.upper())
            continue
        verts = poly.vertices
        n = len(verts)
        for i in range(n):
            x1, y1 = verts[i][0], verts[i][1]
            x2, y2 = verts[(i + 1) % n][0], verts[(i + 1) % n][1]
            dx, dy = x2 - x1, y2 - y1
            length_sq = dx * dx + dy * dy
            if length_sq == 0:
                d = ((pos.x - x1) ** 2 + (pos.y - y1) ** 2) ** 0.5
            else:
                t = max(0.0, min(1.0,
                    ((pos.x - x1) * dx + (pos.y - y1) * dy) / length_sq))
                qx, qy = x1 + t * dx, y1 + t * dy
                d = ((pos.x - qx) ** 2 + (pos.y - qy) ** 2) ** 0.5
            if d <= edge_tol:
                out.add(zname.upper())
                break
    return out


def _town_visible_zone_names(
    scene_geometry: Optional[SceneGeometry],
    observer: Position,
    current_zone: str = "",
) -> set[str]:
    """Town zones whose nearest exterior edge is in line of sight now.

    Visited zones are memory; they must not gate present perception.  Using a
    zone's nearest point lets an opaque building expose its visible facade
    without pretending the observer can see landmarks through its walls.
    """
    if (
        scene_geometry is None
        or (getattr(scene_geometry, "place_path", "") or "").strip("/").lower()
        != "places/driftmoor"
    ):
        return set()
    visible: set[str] = set()
    for name, polygon in scene_geometry.zones.items():
        upper = str(name).upper()
        if upper == "EXTERIOR":
            continue
        target = observer if upper == current_zone else polygon.nearest_point(observer)
        if scene_geometry.can_see(observer, target):
            visible.add(upper)
    return visible


def _build_points_of_interest(
    scene_geometry: Optional[SceneGeometry],
    my_pos: Optional[tuple[float, float, str]],
    visited_zones: Optional[set[str]] = None,
) -> str:
    """List named landmarks with absolute coords and
    distance from the character's current position.

    Player-Left LLMs need explicit coords to write a meaningful MOVEMENT
    target; otherwise they emit small offsets from their current spot and
    appear stuck.

    Visibility filter: a landmark is shown only if it lies in the character's
    current zone OR a previously visited zone. Junction landmarks (on a zone
    seam) are shown if either adjacent zone is visible. Landmarks not
    associated with any zone (e.g. a scene-edge crack) are always shown —
    they're effectively "outside" the chamber map.
    """
    if scene_geometry is None or my_pos is None:
        return ""
    px, py = my_pos[0], my_pos[1]
    current_zone = (my_pos[2] or "").upper()
    visible_zones: set[str] = set(visited_zones or set())
    if current_zone:
        visible_zones.add(current_zone)
    lines: list[str] = []
    _town_los = (
        (getattr(scene_geometry, "place_path", "") or "").strip("/").lower()
        == "places/driftmoor"
    )
    _observer = Position(float(px), float(py))
    visible_zones.update(
        _town_visible_zone_names(scene_geometry, _observer, current_zone)
    )

    def _town_point_visible(pos: Position) -> bool:
        if not _town_los:
            return True
        target = pos
        zone_name = scene_geometry.zone_at(pos)
        if zone_name and zone_name.upper() != current_zone:
            poly = scene_geometry.zones.get(zone_name)
            if poly is not None:
                target = poly.nearest_point(_observer)
        return scene_geometry.can_see(_observer, target)

    # Landmarks — filtered by zone visibility
    for name, pos in scene_geometry.landmarks.items():
        if not _town_point_visible(pos):
            continue
        lm_zones = _zones_for_point(pos, scene_geometry.zones)
        # If a landmark sits in zones the character has not encountered,
        # hide it. If it's not in any zone (lm_zones empty), show it
        # (treat as scene-level / outside-the-map waypoint).
        if lm_zones and not (lm_zones & visible_zones):
            continue
        dist = ((pos.x - px) ** 2 + (pos.y - py) ** 2) ** 0.5
        # Only an authored connection leads onward. Merely sitting on/near a
        # zone seam is not an affordance: chairs, shelves, mirrors, and other
        # ordinary landmarks must never be advertised as exits.
        onward = ""
        is_connection = any(
            abs(pos.x - conn.x) < 0.5 and abs(pos.y - conn.y) < 0.5
            for conn in (getattr(scene_geometry, "connections", {}) or {}).values()
        )
        onward_zones = {
            zone for zone in lm_zones
            if zone not in {current_zone, "EXTERIOR"}
        } if is_connection else set()
        if is_connection and onward_zones:
            onward = " — leads onward to " + ", ".join(
                z.title() for z in sorted(onward_zones)
            )
        lines.append(
            f"- {name}: x={pos.x:.0f}, y={pos.y:.0f} (~{dist:.0f} ft away){onward}"
        )

    # Enterable venues appear as POIs via their authored doorway (the connection
    # point), which is why the redundant per-building *_center landmarks were
    # retired. Only sub-place doorways are folded in — region exits stay
    # represented by their road landmarks. Skipped for non-Driftmoor scenes.
    _lm_pts = [(p.x, p.y) for p in scene_geometry.landmarks.values()]
    for _child, _conn, dx, dy in _driftmoor_source_doorways(
        getattr(scene_geometry, "place_path", "") or ""
    ):
        door = Position(dx, dy)
        if not _town_point_visible(door):
            continue
        door_zones = _zones_for_point(door, scene_geometry.zones)
        if door_zones and not (door_zones & visible_zones):
            continue
        # A landmark already marking this spot wins (no double-listing).
        if any(abs(dx - lx) < 2.0 and abs(dy - ly) < 2.0 for lx, ly in _lm_pts):
            continue
        label = re.sub(r"^to[ _]+", "", _conn).replace("_", " ").strip() or _child
        dist = ((dx - px) ** 2 + (dy - py) ** 2) ** 0.5
        onward = ""
        destination_zones = {
            zone for zone in door_zones
            if zone not in {current_zone, "EXTERIOR"}
        }
        if destination_zones:
            onward = " — enter to go inside"
        lines.append(
            f"- {label}: x={dx:.0f}, y={dy:.0f} (~{dist:.0f} ft away){onward}"
        )

    if not lines:
        return ""
    here = current_zone.title() if current_zone else "an unmarked area"
    header = (
        f"## Where you are and where you can go\n"
        f"You are in the {here}. The landmarks below are the only places you "
        f"can currently see or reach; use their coordinates in MOVEMENT to "
        f"travel. Entries marked \"leads onward\" open into a new area.\n"
    )
    return header + "\n".join(lines)


# Words that signal the actor intends to relocate this turn.
_MOVE_CUE_WORDS = {
    "move", "moves", "moving", "go", "goes", "going", "head", "heads",
    "heading", "walk", "walks", "walking", "advance", "advances",
    "advancing", "approach", "approaches", "approaching", "enter",
    "enters", "entering", "cross", "crosses", "crossing", "proceed",
    "proceeds", "proceeding", "step", "steps", "stepping", "travel",
    "travels", "traveling", "travelling", "toward", "towards", "into",
    "descend", "descends", "descending", "climb", "climbs", "climbing",
    "make", "follow", "follows", "following",
}

# Generic location nouns that, on their own, do not identify a destination.
_DESTINATION_GENERIC = {
    "chamber", "passage", "zone", "center", "centre", "mouth", "descent",
    "squeeze", "threshold", "opening", "rubble", "arch", "crack", "tunnel",
    "cavern", "area", "room", "rooms", "the", "a", "an",
}

_CONNECTOR_NAME_TOKENS = {
    "stair", "stairs", "staircase", "door", "gate", "arch", "hall",
    "corridor", "entry", "entrance", "exit", "threshold", "landing",
}


# The enter/leave verb split now lives in the LATN lexicon (threshold-crossing
# verbs carry an "enter"/"leave" dim on top of "move"); venue-transition
# detection parses through LATN rather than these regexes — see
# _infer_driftmoor_venue_transition.


def _normalize_venue_intent_text(text: str) -> str:
    """Normalize common typo seams in venue-enter/exit phrases.

    Examples: ``enterthe bitter remedy`` -> ``enter the bitter remedy`` and
    vertical stair travel -> the same enter/leave semantics used by doorways.
    """
    t = (text or "").strip().lower()
    if not t:
        return ""
    t = re.sub(
        r"\b(enter|enters|entering|leave|leaves|leaving|exit|exits|exiting)(the|a|an)\b",
        r"\1 \2",
        t,
    )
    if re.fullmatch(
        r"(?:i\s+)?(?:go|walk|head|climb|move)\s+"
        r"(?:upstairs|up\s+(?:the\s+)?stairs|(?:the\s+)?stairs)",
        t,
    ):
        return "enter upstairs"
    if re.fullmatch(
        r"(?:i\s+)?(?:go|walk|head|move)\s+"
        r"(?:downstairs|down\s+(?:the\s+)?stairs)",
        t,
    ) or re.fullmatch(
        r"(?:i\s+)?descend\s+(?:downstairs|(?:the\s+)?stairs)",
        t,
    ):
        return "leave"
    return t


@dataclass(frozen=True)
class _SceneNode:
    scene_name: str
    place_path: str
    parent_place_path: str
    aliases: tuple[str, ...]
    place_type: str = ""


def _scene_aliases(*texts: str) -> tuple[str, ...]:
    stop_words = {"the", "and", "of", "a", "an", "to", "in", "at", "on", "for", "with", "scene"}
    out: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if not text:
            continue
        norm = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
        for word in norm.split():
            if len(word) > 2 and word not in stop_words and word not in seen:
                seen.add(word)
                out.append(word)
    return tuple(out)


_DRIFTMOOR_PLACES_ROOT = Path(__file__).resolve().parent.parent / "scenario" / "places" / "driftmoor"


def _scene_header_aliases(place_file: Path) -> tuple[str, ...]:
    aliases: list[str] = []
    try:
        text = place_file.read_text(encoding="utf-8")
    except OSError:
        return ()
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        aliases.extend(_scene_aliases(m.group(1)))
    return tuple(aliases)


def _place_identity_metadata(place_file: Path) -> tuple[str, tuple[str, ...]]:
    """Return explicit ``(type, aliases)`` from a PLACE.md identity section.

    Directory slugs remain stable technical ids. These fields own the
    player-facing category and vocabulary, so a place can be renamed or gain
    colloquial names without moving files. Legacy-derived aliases are still
    appended by ``_scene_node_from_place_file`` during migration.
    """
    try:
        text = place_file.read_text(encoding="utf-8")
    except OSError:
        return "", ()
    match = re.search(
        r"^## Place Identity\s*$\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return "", ()
    fields: dict[str, str] = {}
    for key, value in re.findall(
        r"^\s*-\s*\*\*(.+?):\*\*\s*(.*?)\s*$",
        match.group(1),
        re.MULTILINE,
    ):
        fields[key.strip().lower()] = value.strip()
    place_type = fields.get("type", "").lower()
    aliases = tuple(
        alias.strip().lower()
        for alias in fields.get("aliases", "").split(",")
        if alias.strip()
    )
    return place_type, tuple(dict.fromkeys(aliases))


def _place_path_from_place_file(place_file: Path) -> str:
    try:
        rel_parent = place_file.parent.relative_to(_DRIFTMOOR_PLACES_ROOT)
    except ValueError:
        return ""
    suffix = "" if rel_parent == Path(".") else f"/{rel_parent.as_posix()}"
    return f"places/driftmoor{suffix}"


def _scene_node_from_place_file(place_file: Path) -> _SceneNode:
    place_path = _place_path_from_place_file(place_file)
    parent_place_path = place_path.rsplit("/", 1)[0] if "/" in place_path else ""
    scene_name = Path(place_path).name or "driftmoor"
    place_type, explicit_aliases = _place_identity_metadata(place_file)
    legacy_aliases = _scene_aliases(
        scene_name.replace("_", " "),
        place_path.split("/")[-1].replace("_", " "),
    )
    legacy_aliases += _scene_header_aliases(place_file)
    # Keep the stable place-name alias first because a few presentation paths
    # use aliases[0] as the human-readable label. Explicit aliases extend the
    # grounding vocabulary without changing that display name.
    scene_aliases = tuple(dict.fromkeys(legacy_aliases + explicit_aliases))
    return _SceneNode(
        scene_name, place_path, parent_place_path, scene_aliases, place_type
    )


@lru_cache(maxsize=1)
def _driftmoor_connection_aliases() -> dict[str, tuple[str, ...]]:
    """Destination-place aliases derived from authored connection names.

    Example: ``to_rooming_house -> places/driftmoor/weary_traveler`` adds
    ``rooming house`` aliases so natural enter-phrasing resolves correctly.
    """
    out: dict[str, set[str]] = {}
    if not _DRIFTMOOR_PLACES_ROOT.exists():
        return {}

    for geom_file in sorted(_DRIFTMOOR_PLACES_ROOT.glob("**/GEOMETRY.md")):
        try:
            text = geom_file.read_text(encoding="utf-8")
        except OSError:
            continue

        m = re.search(r"##\s+Connections\b(.*?)(?=\n##\s+\w|\Z)", text, re.DOTALL)
        if not m:
            continue

        for raw in m.group(1).splitlines():
            line = raw.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 4:
                continue
            name, dest = cells[0], cells[3]
            if not name or not dest:
                continue
            if name.lower() == "name" or dest.lower() == "destination":
                continue
            if re.fullmatch(r"-+", name.replace(" ", "")):
                continue

            dest_norm = dest.lower().strip().strip("/")
            if not dest_norm.startswith("places/driftmoor/"):
                continue

            hint = re.sub(r"^to_", "", name.lower().strip()).replace("_", " ")
            if not hint:
                continue

            # Connection hints are best kept phrase-level (e.g. "rooming house").
            # Token-level expansion can introduce ambiguous one-word aliases like
            # "house" that incorrectly match unrelated child venues.
            out.setdefault(dest_norm, set()).add(hint)

    return {k: tuple(sorted(v)) for k, v in out.items()}


@lru_cache(maxsize=1)
def _driftmoor_place_registry() -> tuple[_SceneNode, ...]:
    nodes: list[_SceneNode] = []
    if not _DRIFTMOOR_PLACES_ROOT.exists():
        return tuple(nodes)
    conn_aliases = _driftmoor_connection_aliases()
    for place_file in sorted(_DRIFTMOOR_PLACES_ROOT.glob("**/PLACE.md")):
        node = _scene_node_from_place_file(place_file)
        if node.place_path:
            extra = conn_aliases.get(node.place_path.lower().strip("/"), ())
            if extra:
                aliases = tuple(dict.fromkeys(node.aliases + extra))
                node = _SceneNode(
                    node.scene_name,
                    node.place_path,
                    node.parent_place_path,
                    aliases,
                    node.place_type,
                )
            nodes.append(node)
    return tuple(nodes)


def _transition_target_place_path(
    target_scene_name: str,
    source_place_path: str,
) -> str:
    """Resolve a transition's scene basename within its place hierarchy.

    Scene basenames are intentionally reusable (many buildings can have an
    ``upstairs``). Prefer a direct child, parent, or sibling of the source
    before considering a globally unique legacy basename.
    """
    target = (target_scene_name or "").strip().lower()
    source = (source_place_path or "").strip().lower().strip("/")
    if not target:
        return ""
    if target == "driftmoor":
        return "places/driftmoor"

    registry = _driftmoor_place_registry()
    source_node = next((node for node in registry if node.place_path == source), None)
    candidates = [node for node in registry if node.scene_name == target]

    direct_child = next(
        (node for node in candidates if node.parent_place_path == source),
        None,
    )
    if direct_child is not None:
        return direct_child.place_path

    if source_node is not None:
        parent = next(
            (
                node for node in candidates
                if node.place_path == source_node.parent_place_path
            ),
            None,
        )
        if parent is not None:
            return parent.place_path

        sibling = next(
            (
                node for node in candidates
                if node.parent_place_path == source_node.parent_place_path
            ),
            None,
        )
        if sibling is not None:
            return sibling.place_path

    # Preserve legacy behavior only when the basename is globally unambiguous.
    return candidates[0].place_path if len(candidates) == 1 else ""


def _resolve_debug_travel_place(intent_text: str) -> str:
    """Resolve an explicit ``/goto PLACE`` developer travel command.

    The leading slash keeps this outside LATN and the in-world Teleport spell.
    Only authored Driftmoor places resolve, and ambiguous aliases fail closed.
    """
    match = re.match(r"^\s*/goto\s+(.+?)\s*$", intent_text or "", re.IGNORECASE)
    if match is None:
        return ""
    wanted = re.sub(r"[^a-z0-9]+", " ", match.group(1).lower()).strip()
    if not wanted:
        return ""

    matches: list[str] = []
    for node in _driftmoor_place_registry():
        path_tail = node.place_path.removeprefix("places/driftmoor/")
        labels = {
            node.scene_name.replace("_", " "),
            path_tail.replace("/", " ").replace("_", " "),
            *(alias.replace("_", " ") for alias in node.aliases),
        }
        normalized = {
            re.sub(r"[^a-z0-9]+", " ", label.lower()).strip()
            for label in labels if label
        }
        if wanted in normalized:
            matches.append(node.place_path)
    unique = list(dict.fromkeys(matches))
    return unique[0] if len(unique) == 1 else ""


def _entry_point_from_target_geometry(
    target_place_path: str,
    source_place_path: str,
    scene_geometry: SceneGeometry | None,
) -> tuple[float, float, str] | None:
    """Best doorway spawn in ``target_place_path`` for an arrival from source.

    Reads the destination place's ``GEOMETRY.md`` Connections table and returns
    the ``(x, y, zone)`` of the first row whose destination equals
    ``source_place_path``. ``None`` when no authored match exists.
    """
    if scene_geometry is None:
        return None
    target = (target_place_path or "").strip().lower().strip("/")
    source = (source_place_path or "").strip().lower().strip("/")
    if not target or not source:
        return None
    if not target.startswith("places/driftmoor"):
        return None

    rel = target.removeprefix("places/driftmoor").strip("/")
    geom_path = _DRIFTMOOR_PLACES_ROOT / rel / "GEOMETRY.md" if rel else _DRIFTMOOR_PLACES_ROOT / "GEOMETRY.md"
    if not geom_path.exists():
        return None

    try:
        text = geom_path.read_text(encoding="utf-8")
    except OSError:
        return None

    m = re.search(r"##\s+Connections\b(.*?)(?=\n##\s+\w|\Z)", text, re.DOTALL)
    if not m:
        return None

    for raw in m.group(1).splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        name, x_s, y_s, dest = cells[0], cells[1], cells[2], cells[3]
        if not name or name.lower() == "name":
            continue
        if dest.lower().strip().strip("/") != source:
            continue
        try:
            x = float(x_s)
            y = float(y_s)
        except ValueError:
            continue
        z = (scene_geometry.zone_at(Position(x, y, 0.0)) or "").upper()
        return (x, y, z)

    return None


def _seed_transition_actor_start(
    scene_geometry: SceneGeometry | None,
    actor_id: str,
    current_positions: dict,
) -> None:
    """Give a newly entered map a fog-of-war seed for its preserved actor."""
    if scene_geometry is None or actor_id not in current_positions:
        return
    x, y, _zone = current_positions[actor_id]
    scene_geometry.starting_positions[actor_id] = Position(float(x), float(y))


# An actor must be within this many feet of a venue's authored doorway (its
# Connections-table point) for an "enter" to cross into the sub-scene. Farther
# away, "enter X" just walks the actor toward that door — clamped to the turn's
# movement budget, exactly like "go to X" — and the crossing happens on the turn
# a clamped move finally lands them at the door.
_DOORWAY_ARRIVAL_FT = 8.0


@lru_cache(maxsize=8)
def _driftmoor_source_doorways(source_place_path: str) -> tuple[tuple[str, str, float, float], ...]:
    """``(child_scene_name, connection_name, x, y)`` for each authored connection
    in the *source* place's GEOMETRY Connections table — i.e. where each child
    venue's front door sits in this scene's coordinates. Empty when the source
    isn't a Driftmoor place. Only connections whose destination is a sub-place of
    the source count (region/exit connections lead out of the scene, no doorway
    here)."""
    source = (source_place_path or "").strip().lower().strip("/")
    if not source.startswith("places/driftmoor"):
        return ()
    rel = source.removeprefix("places/driftmoor").strip("/")
    geom_path = (_DRIFTMOOR_PLACES_ROOT / rel / "GEOMETRY.md") if rel \
        else (_DRIFTMOOR_PLACES_ROOT / "GEOMETRY.md")
    if not geom_path.exists():
        return ()
    try:
        text = geom_path.read_text(encoding="utf-8")
    except OSError:
        return ()
    m = re.search(r"##\s+Connections\b(.*?)(?=\n##\s+\w|\Z)", text, re.DOTALL)
    if not m:
        return ()
    out: list[tuple[str, str, float, float]] = []
    for raw in m.group(1).splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        name, x_s, y_s, dest = cells[0], cells[1], cells[2], cells[3]
        if not name or name.lower() == "name":
            continue
        dest_norm = dest.lower().strip().strip("/")
        if not dest_norm.startswith(source + "/"):
            continue
        child = dest_norm.rsplit("/", 1)[-1]
        try:
            out.append((child, name, float(x_s), float(y_s)))
        except ValueError:
            continue
    return tuple(out)


def _driftmoor_enter_doorway(
    intent_text: str,
    current_place_path: str,
    actor_zone: str,
    scene_geometry: "SceneGeometry | None",
    actor_position: Optional[tuple] = None,
) -> Optional[tuple[str, tuple[float, float, str]]]:
    """For an "enter <child>" intent, return ``(target_scene, (x, y, zone))`` of
    the child venue's authored doorway in the current scene, so the turn loop can
    both walk the actor there (clamped) and gate the sub-scene crossing on
    arrival. Returns None when the intent isn't a doorway-gated entry — an exit,
    a non-Driftmoor scene, or a child with no authored doorway (those keep the
    legacy immediate transition)."""
    target_scene = _infer_driftmoor_venue_transition(
        intent_text, current_place_path, actor_zone, actor_position)
    if target_scene is None:
        return None
    # Only descents (entering a child of the current place) are doorway-gated;
    # exits back to a parent pass straight through.
    place = (current_place_path or "").strip().lower().strip("/")
    is_child = any(
        n.scene_name == target_scene and n.parent_place_path == place
        for n in _driftmoor_place_registry()
    )
    if not is_child:
        return None
    for child, _conn, x, y in _driftmoor_source_doorways(place):
        if child == target_scene:
            zone = ""
            if scene_geometry is not None:
                zone = (scene_geometry.zone_at(Position(x, y, 0.0)) or "").upper()
            return (target_scene, (x, y, zone))
    return None


_VENUE_ALIAS_GENERIC = {
    "place", "building", "the", "a", "an", "shop", "house", "hall", "store",
    "room", "rooms", "md", "of", "and",
}


def _clean_venue_aliases(aliases: tuple[str, ...]) -> tuple[str, ...]:
    """A venue's identifying aliases for LATN grounding: drop the PLACE.md-title
    boilerplate and bare generic nouns (``shop``/``house``/…) so a generic word
    of one venue can't be a groundable name of another. Multi-word phrases
    (``rooming house``, ``pawn shop``) survive whole — only the standalone
    generic token is dropped."""
    out: list[str] = []
    for a in aliases:
        al = (a or "").strip().lower()
        if not al or al in _VENUE_ALIAS_GENERIC or "place md" in al:
            continue
        out.append(al)
    return tuple(dict.fromkeys(out))


def _driftmoor_child_venues(current_place_path: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """``(scene_name, cleaned_aliases)`` for each enterable child of the current
    place — the venue candidates LATN grounds an "enter <name>" against.

    A PLACE.md alone does not make a venue enterable from its parent: the
    parent's geometry must also author a doorway connection to it.  This keeps
    umbrella/location records (such as the former combined Ironhoof site) from
    competing with first-class buildings that have their own doors.
    """
    place = (current_place_path or "").strip().lower().strip("/")
    if not place:
        return ()
    doorway_children = {
        child for child, _conn, _x, _y in _driftmoor_source_doorways(place)
    }
    return tuple(
        (node.scene_name, _clean_venue_aliases(node.aliases))
        for node in _driftmoor_place_registry()
        if node.parent_place_path == place and node.scene_name in doorway_children
    )


def _venue_candidates_at_door(
    current_place_path: str,
    actor_zone: str,
    candidates: tuple[tuple[str, tuple[str, ...]], ...],
    actor_position: Optional[tuple] = None,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Narrow venue candidates to a clearly nearest authored doorway.

    Generic aliases such as ``cottage`` may legitimately name more than one
    town destination. A building footprint is decisive. On nearby open ground,
    choose the nearest doorway only when it is materially closer than second
    place; otherwise preserve the ambiguity and ask.
    """
    zone = (actor_zone or "").upper()
    place = (current_place_path or "").strip().lower().strip("/")
    if not zone or not place:
        return ()
    rel = place.removeprefix("places/driftmoor").strip("/")
    geom_path = (
        _DRIFTMOOR_PLACES_ROOT / rel / "GEOMETRY.md"
        if rel else _DRIFTMOOR_PLACES_ROOT / "GEOMETRY.md"
    )
    try:
        geometry = load_geometry(geom_path)
    except (OSError, ValueError):
        return ()
    names = {
        child
        for child, _connection, x, y in _driftmoor_source_doorways(place)
        if (geometry.zone_at(Position(x, y, 0.0)) or "").upper() == zone
    }
    narrowed = tuple(candidate for candidate in candidates if candidate[0] in names)
    if len(narrowed) == 1:
        return narrowed
    if actor_position is None or len(actor_position) < 2:
        return ()
    px, py = float(actor_position[0]), float(actor_position[1])
    candidate_names = {candidate[0] for candidate in candidates}
    ranked = sorted(
        (
            ((x - px) ** 2 + (y - py) ** 2) ** 0.5,
            child,
        )
        for child, _connection, x, y in _driftmoor_source_doorways(place)
        if child in candidate_names
    )
    if len(ranked) < 2:
        return ()
    nearest, second = ranked[0], ranked[1]
    # Both an absolute and relative margin: 40 ft vs 55 ft remains ambiguous;
    # 40 ft vs 100 ft is a reasonable location-based inference.
    if second[0] - nearest[0] < 20.0 or nearest[0] > second[0] * 0.7:
        return ()
    return tuple(candidate for candidate in candidates if candidate[0] == nearest[1])


def _driftmoor_approach_doorway(
    intent_text: str,
    current_place_path: str,
) -> Optional[tuple[str, tuple[float, float, str]]]:
    """Resolve a uniquely named venue in a movement phrase to its front door."""
    words = _dest_tokens(intent_text)
    if not words or not (words & (_MOVE_CUE_WORDS | {"teleport"})):
        return None
    generic = _VENUE_ALIAS_GENERIC | {"cottage"}
    scored: list[tuple[int, str]] = []
    for scene_name, aliases in _driftmoor_child_venues(current_place_path):
        best = 0
        for alias in aliases:
            alias_words = _dest_tokens(alias)
            identifying = alias_words - generic
            if identifying and identifying <= words:
                best = max(best, len(identifying))
        if best:
            scored.append((best, scene_name))
    if not scored:
        return None
    top = max(score for score, _scene in scored)
    winners = {scene for score, scene in scored if score == top}
    if len(winners) != 1:
        return None
    winner = next(iter(winners))
    for child, _connection, x, y in _driftmoor_source_doorways(current_place_path):
        if child == winner:
            return (child, (x, y, ""))
    return None


def _ambiguous_driftmoor_venues(
    intent_text: str,
    current_place_path: str,
) -> tuple[tuple[str, str], ...]:
    """Return matching child venues for an ambiguous ``enter`` target.

    This is only explanatory: actual transition authority remains with LATN.
    Exact aliases and standalone alias words are considered so a bare generic
    noun such as ``cottage`` can produce a useful choice list.
    """
    text = _normalize_venue_intent_text(intent_text)
    if not re.search(r"\b(?:enter|visit|go inside|go in|go into|step inside|walk inside)\b", text):
        return ()
    match = re.search(
        r"\b(?:enter|visit|go inside|go in|go into|step inside|walk inside)\s+"
        r"(?:the\s+|a\s+|an\s+)?(.+?)\s*$",
        text,
    )
    if not match:
        return ()
    target = re.sub(r"[^a-z0-9]+", " ", match.group(1).lower()).strip()
    if not target:
        return ()
    out: list[tuple[str, str]] = []
    by_path = {node.scene_name: node for node in _driftmoor_place_registry()}
    for scene_name, aliases in _driftmoor_child_venues(current_place_path):
        if any(target == alias or target in alias.split() for alias in aliases):
            node = by_path.get(scene_name)
            label = scene_name.replace("_", " ").title()
            if node is not None:
                explicit = next((a for a in node.aliases if " " in a), "")
                if explicit:
                    label = explicit.title()
            out.append((scene_name, label))
    return tuple(out) if len(out) > 1 else ()


def _infer_driftmoor_venue_transition(
    intent_text: str,
    current_place_path: str,
    actor_zone: str,
    actor_position: Optional[tuple] = None,
) -> Optional[str]:
    """Detect hierarchy-based Driftmoor scene transitions via LATN.

    The authored ``scenario/places/driftmoor`` directory defines the tree:
    you can enter any child place from its parent, and exit a child place back
    to the nearest parent place. The intent is parsed by LATN — a verb ``isa
    "enter"`` grounds its object NP to a child venue (compound-aware, unique
    winner), and a verb ``isa "leave"`` returns to the parent — rather than
    regex alias matching, so multi-word venue names resolve consistently and a
    generic sub-token ("shop") can't hijack another venue.
    """
    text = _normalize_venue_intent_text(intent_text)
    place = (current_place_path or "").strip().lower().strip("/")
    if not text or not place:
        return None

    by_place = {node.place_path: node for node in _driftmoor_place_registry()}
    current = by_place.get(place)
    if current is None:
        return None

    from engine import latn_integration

    # Candidates = the enterable children, plus the CURRENT place itself so that
    # "leave the rooming house" (naming the place you're in) grounds its object
    # and the leave VP survives policy. A self-referential "enter" is guarded
    # below (you can't enter where you already are).
    children = _driftmoor_child_venues(place)
    child_names = {sn for sn, _ in children}
    candidates = children + ((current.scene_name, _clean_venue_aliases(current.aliases)),)

    # Parse the complete conjunction once. Candidate grounding includes the
    # current place's siblings so a later clause is not discarded merely
    # because it becomes reachable only after an earlier `leave`. Each clause
    # is then authorized against the simulated hierarchy state in sequence.
    grounding_candidates = list(candidates)
    if current.parent_place_path:
        known = {scene_name for scene_name, _aliases in grounding_candidates}
        grounding_candidates.extend(
            candidate
            for candidate in _driftmoor_child_venues(current.parent_place_path)
            if candidate[0] not in known
        )
    plan = latn_integration.resolve_venue_plan(
        text, {}, actor_zone or "", grounding_candidates
    )
    simulated = current
    planned_target = None
    for kind, target in plan:
        if kind == "leave":
            parent = by_place.get(simulated.parent_place_path) if simulated.parent_place_path else None
            if parent is not None:
                simulated = parent
                planned_target = parent.scene_name
            continue
        enterable = {sn for sn, _aliases in _driftmoor_child_venues(simulated.place_path)}
        if kind == "enter" and target in enterable:
            next_place = next((node for node in by_place.values() if node.scene_name == target), None)
            if next_place is not None:
                simulated = next_place
                planned_target = target
    if len(plan) > 1:
        return planned_target

    res = latn_integration.resolve_venue_transition(text, {}, actor_zone or "", candidates)
    if res == ("enter", None):
        ambiguous_names = {
            scene_name
            for scene_name, _label in _ambiguous_driftmoor_venues(text, place)
        }
        proximity_candidates = tuple(
            candidate for candidate in children
            if not ambiguous_names or candidate[0] in ambiguous_names
        )
        at_door = _venue_candidates_at_door(
            place, actor_zone, proximity_candidates, actor_position
        )
        if at_door:
            res = latn_integration.resolve_venue_transition(
                text, {}, actor_zone or "", at_door
            )
    if res is None:
        return None
    kind, target = res
    if kind == "leave":
        parent = by_place.get(current.parent_place_path) if current.parent_place_path else None
        return parent.scene_name if parent is not None else None
    if kind == "enter" and target in child_names:
        return target
    return None


def _infer_rooming_house_transition(
    intent_text: str,
    current_place_path: str,
    actor_zone: str,
) -> Optional[str]:
    """Backward-compatible alias for the generalized Driftmoor venue hook."""
    return _infer_driftmoor_venue_transition(intent_text, current_place_path, actor_zone)


def _dest_tokens(s: str) -> set[str]:
    """Word tokens for destination matching (keeps ordinals like 'first')."""
    out: set[str] = set()
    for tok in re.split(r"[^a-z0-9]+", s.lower()):
        if not tok:
            continue
        out.add(tok)
        # Small plural normalization so "guest room" can match "GUEST_ROOMS".
        if len(tok) > 3 and tok.endswith("s"):
            out.add(tok[:-1])
    return out


# Compass directions as world-space unit vectors. Map orientation (see
# map_renderer: screen y = -world y) puts +y at the top, so +y is NORTH and +x
# is EAST. Diagonals are normalized.
_DIAG = 0.7071
_CARDINAL_VECTORS: dict[str, tuple[float, float]] = {
    "north": (0.0, 1.0), "n": (0.0, 1.0),
    "south": (0.0, -1.0), "s": (0.0, -1.0),
    "east": (1.0, 0.0), "e": (1.0, 0.0),
    "west": (-1.0, 0.0), "w": (-1.0, 0.0),
    "northeast": (_DIAG, _DIAG), "ne": (_DIAG, _DIAG),
    "northwest": (-_DIAG, _DIAG), "nw": (-_DIAG, _DIAG),
    "southeast": (_DIAG, -_DIAG), "se": (_DIAG, -_DIAG),
    "southwest": (-_DIAG, -_DIAG), "sw": (-_DIAG, -_DIAG),
}

_COMPASS_LABELS = ("east", "northeast", "north", "northwest",
                   "west", "southwest", "south", "southeast")


def _compass_label(dx: float, dy: float) -> str:
    """8-point compass word for a world-space delta (+y north, +x east)."""
    import math
    return _COMPASS_LABELS[round(math.degrees(math.atan2(dy, dx)) / 45) % 8]


def _answer_where_question(
    intent_text: str,
    *,
    characters: dict,
    actor_zone: str,
    scene_geometry,
    venues,
    player_xy,
) -> Optional[str]:
    """Answer "where is <venue>?" from geometry, or None.

    LATN's SQ pass grounds the queried focus to an enterable venue; this reports
    that venue's authored doorway as a bearing + distance from the player. Only a
    ``where`` question that grounds a venue with a known door and a known player
    position is answered -- otherwise None, and the caller falls back to the
    annotated DM. (Landmark/zone focuses aren't grounded yet -- a later slice.)
    """
    if player_xy is None or scene_geometry is None:
        return None
    from engine.latn_integration import build_context
    from engine import latn_resolver
    lexicon, adapter = build_context(
        {}, characters or {}, actor_zone or "", scene_geometry, venues=venues)
    rq = latn_resolver.resolve_world_query(
        intent_text or "", lexicon=lexicon, adapter=adapter)
    if rq is None or rq.kind != "geography" or rq.focus_entity is None:
        return None
    ent = rq.focus_entity
    doorways = {
        child: (x, y)
        for child, _conn, x, y in _driftmoor_source_doorways(
            getattr(scene_geometry, "place_path", "") or "")
    }
    if getattr(ent, "kind", "") == "venue":
        pos = doorways.get(ent.scene_name)
        label = (ent.aliases[0] if getattr(ent, "aliases", None)
                 else ent.scene_name.replace("_", " ")).title()
    else:
        raw = getattr(ent, "position", {}) or {}
        pos = (raw.get("x"), raw.get("y"))
        label = (getattr(ent, "name", "") or "landmark").replace("_", " ").title()
    if pos is None:
        return None
    dx, dy = pos[0] - player_xy[0], pos[1] - player_xy[1]
    dist = (dx * dx + dy * dy) ** 0.5
    if dist < 10.0:
        return f"The {label} is right here."
    return (f"The {label} is to the {_compass_label(dx, dy)}, "
            f"about {dist:.0f} ft away.")


def _answer_venue_existence_question(
    intent_text: str, *, characters: dict, actor_zone: str, scene_geometry, venues,
) -> Optional[str]:
    """Answer an authored-place existence question such as bakery-in-town."""
    if scene_geometry is None:
        return None
    from engine.latn_integration import build_context
    from engine import latn_resolver
    lexicon, adapter = build_context(
        {}, characters or {}, actor_zone or "", scene_geometry, venues=venues)
    rq = latn_resolver.resolve_world_query(
        intent_text or "", lexicon=lexicon, adapter=adapter)
    if (rq is None or rq.kind != "existence" or rq.focus_entity is None
            or getattr(rq.focus_entity, "kind", "") != "venue"):
        return None
    ent = rq.focus_entity
    label = (ent.aliases[0] if getattr(ent, "aliases", None)
             else ent.scene_name.replace("_", " ")).title()
    return f"Yes. There is a {label} in town."


def _character_possessions(cs, items) -> list[str]:
    """De-duplicated human-readable list of what a character is carrying --
    weapons, pack goods (food/tools/wearables), and picked-up scene items."""
    char = getattr(cs, "character", None)
    labels: list[str] = []
    seen: set[str] = set()

    def _add(text) -> None:
        label = (text or "").strip()
        key = label.lower()
        if label and key not in seen:
            seen.add(key)
            labels.append(label)

    for weapon in (getattr(cs, "weapons", None) or []):
        _add(getattr(weapon, "name", ""))
    for prov in (getattr(cs, "pack", None) or []):
        _add(getattr(prov, "label", None) or getattr(prov, "id", ""))
    for iid in (getattr(char, "inventory", None) or []):
        it = (items or {}).get(iid)
        _add((getattr(it, "label", "") or getattr(it, "name", "")
              or str(iid).replace("_", " ")))
    return labels


def _answer_self_question(
    intent_text: str,
    *,
    cs,
    characters: dict,
    actor_zone: str,
    scene_geometry,
    items,
    catalog=(),
) -> Optional[str]:
    """Answer a first-person question about the speaker -- wealth or possessions
    -- from their own character, or None. LATN classifies the question (currency
    vs possession, deferring purchase questions to the catalog); the answer is
    read straight off the CharacterSession, no DM/LLM."""
    if cs is None:
        return None
    from engine.latn_integration import build_context
    from engine import latn_resolver
    from models.currency import format_coins
    lexicon, adapter = build_context(
        items or {}, characters or {}, actor_zone or "", scene_geometry,
        catalog=catalog)
    kind = latn_resolver.resolve_self_query(
        intent_text or "", lexicon=lexicon, adapter=adapter)
    if kind is None:
        return None
    char = getattr(cs, "character", None)
    purse = format_coins(getattr(char, "purse_cp", 0) or 0)
    if kind == "wealth":
        return f"You have {purse} in your purse."
    goods = _character_possessions(cs, items)
    if goods:
        return f"You are carrying: {', '.join(goods)}. Your purse holds {purse}."
    return f"You aren't carrying anything. Your purse holds {purse}."


def _visible_character_query_records(
    character_id: str,
    current_positions: dict,
    active_characters: set[str],
    characters: dict,
    scene_geometry,
) -> list[tuple[str, str, float]]:
    """Structured visible-character records used by engine query answers."""
    import math
    from models.senses import resolve_senses

    my_pos = current_positions.get(character_id)
    if my_pos is None:
        return []
    if scene_geometry is None:
        return [
            (cid, getattr(characters.get(cid), "scene_handle", "") or cid, 0.0)
            for cid in sorted(active_characters)
            if cid != character_id
        ]
    observer = Position(my_pos[0], my_pos[1])
    my_zone = my_pos[2] or scene_geometry.zone_at(observer)
    me = characters.get(character_id)
    senses = resolve_senses()
    if me is not None:
        senses = resolve_senses(
            race=getattr(me.character, "race", "") or "",
            senses=getattr(me.character, "senses", None),
            features=getattr(me.character, "features", None),
        )
    ambient = scene_geometry.ambient_sight_range(my_zone)
    visual_ft = math.inf if ambient is None else max(ambient, senses.darkvision_ft)
    records: list[tuple[str, str, float]] = []
    for cid in sorted(active_characters):
        if cid == character_id or cid not in current_positions:
            continue
        other = current_positions[cid]
        point = Position(other[0], other[1])
        distance = math.hypot(point.x - observer.x, point.y - observer.y)
        if distance > visual_ft or not scene_geometry.can_see(observer, point):
            continue
        cs = characters.get(cid)
        label = (getattr(cs, "scene_handle", "") or cid) if cs is not None else cid
        if cs is not None and label.strip().lower() == cid.strip().lower():
            label = getattr(cs.character, "name", "") or label
        records.append((cid, label, round(distance / 5) * 5))
    return records


def _answer_basic_state_question(
    intent_text: str,
    *,
    cs,
    actor_zone: str,
    scene_geometry,
    game_time,
    characters: dict,
    character_id: str = "",
    current_positions: Optional[dict] = None,
    active_characters: Optional[set[str]] = None,
) -> Optional[str]:
    """Answer identity, current-location, and game-clock questions."""
    from engine.latn_integration import build_context
    from engine import latn_resolver
    venues = _driftmoor_child_venues(getattr(scene_geometry, "place_path", "") or "") \
        if scene_geometry is not None else ()
    grounding_characters = _characters_with_acquaintances(characters, cs)
    lexicon, adapter = build_context(
        {}, grounding_characters, actor_zone or "", scene_geometry, venues=venues)
    query = latn_resolver.resolve_state_query(
        intent_text or "", lexicon=lexicon, adapter=adapter)
    if query is None or query.kind not in {
        "identity", "location", "time", "person_identity", "unknown_person",
        "person_definition",
        "visible_people", "person_property_true", "person_property_false",
        "acquaintance_true", "acquaintance_false",
        "known_people",
    }:
        return None
    char = getattr(cs, "character", None)

    if query.kind == "identity" and char is not None:
        name = getattr(char, "name", "") or getattr(char, "id", "") or "your character"
        race = (getattr(char, "race", "") or "").strip()
        char_class = (getattr(char, "character_class", "") or "").strip()
        description = " ".join(part for part in (race, char_class) if part)
        return f"You are {name}" + (f", a {description}." if description else ".")

    if query.kind == "unknown_person":
        focus = query.query.focus_np
        label = (getattr(focus, "noun", None) or "that person")
        label = str(label).replace("_", " ").strip().title()
        return f"Your character does not yet know who {label} is."

    if query.kind == "person_identity" and query.focus_entity is not None:
        known = getattr(query.focus_entity, "session", None)
        known_char = getattr(known, "character", None)
        name = getattr(known_char, "name", "") or getattr(query.focus_entity, "name", "")
        role = (getattr(known_char, "role", "") or "").strip()
        return f"{name} is {role}." if role else f"That is {name}."

    if query.kind == "person_definition" and query.focus_entity is not None:
        known = getattr(query.focus_entity, "session", None)
        known_char = getattr(known, "character", None)
        name = getattr(known_char, "name", "") or getattr(query.focus_entity, "name", "")
        role = (getattr(known_char, "role", "") or "person").strip()
        return f"{name} is a {role}."

    if query.kind == "visible_people":
        visible = _visible_character_query_records(
            character_id, current_positions or {}, active_characters or set(),
            characters, scene_geometry)
        if not visible:
            return "You cannot currently see anyone else here."
        return "You can see:\n" + "\n".join(
            f"- {label} (~{distance:.0f} ft away)" for _cid, label, distance in visible)

    if query.kind == "known_people":
        known = dict(getattr(cs, "known_people", None) or {})
        visible = _visible_character_query_records(
            character_id, current_positions or {}, active_characters or set(),
            characters, scene_geometry)
        for cid, _label, _distance in visible:
            other = characters.get(cid)
            known_char = getattr(other, "character", None)
            name = getattr(known_char, "name", "") or getattr(other, "scene_handle", "") or cid
            known[cid] = name
        cs.known_people = known
        if not known:
            return "Your character does not yet know anyone else."
        return "Your character knows:\n" + "\n".join(
            f"- {name}" for _cid, name in sorted(known.items()))

    if query.kind in {"person_property_true", "person_property_false"}:
        ent = query.focus_entity
        known = getattr(ent, "session", None)
        known_char = getattr(known, "character", None)
        name = getattr(known_char, "name", "") or getattr(ent, "name", "") or "That person"
        complements = list(getattr(query.query.predicate, "complement_phrases", None) or [])
        prop = getattr(complements[0], "noun", "") if complements else "that"
        if query.kind == "person_property_true":
            return f"Yes. {name} is a {prop}."
        return f"No. {name} is not a {prop}."

    if query.kind in {"acquaintance_true", "acquaintance_false"}:
        if query.kind == "acquaintance_false" or query.focus_entity is None:
            return "No. Your character does not know that person."
        ent = query.focus_entity
        known = getattr(ent, "session", None)
        known_char = getattr(known, "character", None)
        name = getattr(known_char, "name", "") or getattr(ent, "name", "")
        known_id = getattr(ent, "entity_id", "") or getattr(known_char, "id", "")
        if known_id:
            cs.known_people[known_id] = name or known_id
        return f"Yes. Your character knows {name}."

    if query.kind == "location":
        zone = (actor_zone or "").replace("_", " ").strip().title()
        place = (getattr(scene_geometry, "name", "") or "").replace("_", " ").strip().title()
        if zone and place and zone.lower() != place.lower():
            return f"You are in {zone}, in {place}."
        if zone or place:
            return f"You are in {zone or place}."
        return "Your current location is not mapped."

    if query.kind == "time":
        if game_time is None:
            return "The game clock is not configured for this scene."
        return (
            f"It is {game_time.hour:02d}:{game_time.minute:02d} on day "
            f"{game_time.day} ({game_time.period}, {game_time.season})."
        )
    return None


def _characters_with_acquaintances(characters: dict, cs) -> dict:
    """Add remembered people to LATN grounding without making them present."""
    grounded = dict(characters or {})
    for cid, name in (getattr(cs, "known_people", None) or {}).items():
        if cid in grounded:
            continue
        remembered = SimpleNamespace(
            id=cid, name=name, race="", character_class="", role="", faction="")
        grounded[cid] = SimpleNamespace(character=remembered, scene_handle=name)
    return grounded


def _answer_place_definition_question(
    intent_text: str, *, characters: dict, actor_zone: str, scene_geometry,
    player_xy=None, visited_zones: Optional[set[str]] = None,
) -> Optional[str]:
    """Answer ``what is <place>?`` from the authoritative PLACE.md record."""
    from engine.latn_integration import build_context
    from engine import latn_resolver
    venues = _driftmoor_child_venues(getattr(scene_geometry, "place_path", "") or "") \
        if scene_geometry is not None else ()
    visible_keys = {
        key
        for keys, _label, _distance in _visible_query_points(
            scene_geometry, player_xy, actor_zone, visited_zones or set())
        for key in keys
    }
    # A generic definite NP ("the cottage") must ground in the actor's current
    # perceptual discourse domain, not against every authored venue in town.
    # Explicitly remembered places can later be supplied as a separate known-
    # place scope; today visibility is the authoritative available scope.
    venues = tuple(
        venue for venue in venues if f"venue:{venue[0]}" in visible_keys
    )
    lexicon, adapter = build_context(
        {}, characters or {}, actor_zone or "", scene_geometry, venues=venues)
    query = latn_resolver.resolve_state_query(
        intent_text or "", lexicon=lexicon, adapter=adapter)
    if query is None or query.kind != "place_definition" or query.focus_entity is None:
        return None
    scene_name = getattr(query.focus_entity, "scene_name", "")
    node = next((n for n in _driftmoor_place_registry() if n.scene_name == scene_name), None)
    if node is None:
        return None

    place_file = _DRIFTMOOR_PLACES_ROOT / Path(node.place_path).relative_to("places/driftmoor") / "PLACE.md"
    try:
        authored = place_file.read_text(encoding="utf-8")
    except OSError:
        return None
    header = re.search(r"^#\s+(?:PLACE\.md\s+[—-]\s*)?(.+?)\s*$", authored, re.MULTILINE)
    label = (header.group(1).strip() if header else node.scene_name.replace("_", " ").title())
    section = re.search(
        r"^## Description and Atmosphere\s*$\n(.*?)(?=^## |\Z)",
        authored, re.MULTILINE | re.DOTALL,
    )
    prose = ""
    if section:
        prose = re.split(r"\n\s*\n", section.group(1).strip(), maxsplit=1)[0].strip()
        prose = re.sub(r"\s+", " ", prose)
    kind = node.place_type.replace("_", " ").strip()
    lead = f"{label} is a {kind}." if kind else f"{label} is a place in Driftmoor."
    return f"{lead} {prose}".strip()


def _visible_query_points(
    scene_geometry, player_xy, actor_zone: str, visited_zones: set[str],
) -> list[tuple[frozenset[str], str, float]]:
    """Return visible ``(entity keys, label, distance)`` records from geometry."""
    if scene_geometry is None or player_xy is None:
        return []
    observer = Position(float(player_xy[0]), float(player_xy[1]))
    current_zone = (actor_zone or "").upper()
    visible_zones = {str(zone).upper() for zone in (visited_zones or set())}
    if current_zone:
        visible_zones.add(current_zone)
    town_los = (
        (getattr(scene_geometry, "place_path", "") or "").strip("/").lower()
        == "places/driftmoor"
    )
    if town_los:
        visible_zones.update(
            _town_visible_zone_names(scene_geometry, observer, current_zone)
        )

    def visible(point: Position) -> bool:
        target = point
        zone_name = scene_geometry.zone_at(point)
        if town_los and zone_name and zone_name.upper() != current_zone:
            poly = scene_geometry.zones.get(zone_name)
            if poly is not None:
                target = poly.nearest_point(observer)
        if town_los and not scene_geometry.can_see(observer, target):
            return False
        zones = _zones_for_point(point, scene_geometry.zones)
        return not zones or bool(zones & visible_zones)

    records: list[tuple[frozenset[str], str, float]] = []
    landmark_points: list[tuple[float, float, int]] = []
    for name, point in (getattr(scene_geometry, "landmarks", {}) or {}).items():
        if visible(point):
            landmark_points.append((point.x, point.y, len(records)))
            records.append((
                frozenset({f"landmark:{name}"}), name.replace("_", " ").title(),
                ((point.x - observer.x) ** 2 + (point.y - observer.y) ** 2) ** 0.5,
            ))
    for child, connection, x, y in _driftmoor_source_doorways(
        getattr(scene_geometry, "place_path", "") or ""
    ):
        point = Position(x, y)
        # Match the map/POI policy: an authored landmark at the same doorway
        # owns its presentation, avoiding duplicate entries for one location.
        overlap = next((
            index for lx, ly, index in landmark_points
            if abs(x - lx) < 2.0 and abs(y - ly) < 2.0
        ), None)
        if visible(point) and overlap is not None:
            keys, label, distance = records[overlap]
            records[overlap] = (keys | {f"venue:{child}"}, label, distance)
        elif visible(point):
            label = connection
            if label.lower().startswith("to_"):
                label = label[3:]
            records.append((
                frozenset({f"venue:{child}"}), label.replace("_", " ").strip().title(),
                ((x - observer.x) ** 2 + (y - observer.y) ** 2) ** 0.5,
            ))
    return records


def _answer_perception_question(
    intent_text: str,
    *,
    context: RoleContext,
    characters: dict,
    actor_zone: str,
    scene_geometry,
    items,
    player_xy=None,
    visited_zones: Optional[set[str]] = None,
) -> Optional[str]:
    """Answer an external-view question from Python-filtered perception state."""
    from engine.latn_integration import build_context
    from engine import latn_resolver

    venues = _driftmoor_child_venues(getattr(scene_geometry, "place_path", "") or "") \
        if scene_geometry is not None else ()
    lexicon, adapter = build_context(
        items or {}, characters or {}, actor_zone or "", scene_geometry,
        venues=venues,
    )
    query = latn_resolver.resolve_world_query(
        intent_text or "", lexicon=lexicon, adapter=adapter)
    if query is None or query.kind not in {"perception_list", "perception_target"}:
        return None
    records = _visible_query_points(
        scene_geometry, player_xy, actor_zone, visited_zones or set())
    if query.kind == "perception_target" and query.focus_entity is not None:
        ent = query.focus_entity
        key = f"{getattr(ent, 'kind', '')}:{getattr(ent, 'entity_id', '')}"
        record = next((record for record in records if key in record[0]), None)
        label = (getattr(ent, "name", "") or getattr(ent, "entity_id", "") or "that").replace("_", " ").title()
        if record is not None:
            return f"Yes. You can see {record[1]} (~{record[2]:.0f} ft away)."
        return f"No. You cannot currently see {label}."

    parts: list[str] = []
    if records:
        visible = [f"- {label} (~{distance:.0f} ft away)" for _key, label, distance in records]
        parts.append("You can see these nearby places and landmarks:\n" + "\n".join(visible))
    perception = (context.perception or "").strip()
    if perception:
        parts.append(perception)
    return "\n\n".join(parts) if parts else "You do not see anything distinct nearby."


_COORD_DEST_RE = re.compile(
    r"[\[(]\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*[\])]"
)


def _infer_coordinate_destination(
    intent_text: str,
    scene_geometry: Optional["SceneGeometry"],
) -> Optional[tuple[float, float, str]]:
    """Resolve explicit coordinate destinations in movement intent text.

    Supports forms like ``move to [1267, 292]`` or ``move towards (1267,292)``.
    Returns ``(x, y, zone)`` when found (zone from ``zone_at`` when geometry is
    available), else ``None``.
    """
    if not intent_text:
        return None
    words = _dest_tokens(intent_text)
    if not words or not (words & _MOVE_CUE_WORDS):
        return None
    m = _COORD_DEST_RE.search(intent_text)
    if m is None:
        return None
    x = float(m.group(1))
    y = float(m.group(2))
    zone = ""
    if scene_geometry is not None:
        zone = (scene_geometry.zone_at(Position(x, y)) or "").upper()
    return (x, y, zone)


def _coordinate_authoritative_target(
    intent_text: str,
    structured_target: Optional[tuple[float, float, float]],
    scene_geometry: Optional["SceneGeometry"],
) -> Optional[tuple[float, float, str] | tuple[float, float, float]]:
    """Prefer a coordinate written in the intent over model-generated fields."""
    return (
        _infer_coordinate_destination(intent_text, scene_geometry)
        or structured_target
    )


def _should_apply_cross_zone_routing(explicit_coordinate) -> bool:
    """Semantic waypoint routing must never replace a player coordinate."""
    return explicit_coordinate is None


def _infer_cardinal_destination(
    intent_text: str,
    my_pos: Optional[tuple[float, float, str]],
    scene_geometry: Optional["SceneGeometry"],
) -> Optional[tuple[float, float, str]]:
    """Resolve a bare compass heading to a pure directional travel step.

    The other movement backfills ground named zones, landmarks, items, and party
    members, but a bare compass heading ("I move south") matched nothing, so the
    actor never moved. Map orientation: +y is north, +x is east. Returns a far
    projected point along the requested heading (zone left blank), then the
    normal downstream clamp applies the actual movement budget for the turn
    (exploration vs combat) and all wall/boundary checks. Returns None when the
    intent names no single compass direction.
    """
    if scene_geometry is None or my_pos is None:
        return None
    words = _dest_tokens(intent_text)
    if not words or not (words & _MOVE_CUE_WORDS):
        return None
    dirs = {_CARDINAL_VECTORS[w] for w in words if w in _CARDINAL_VECTORS}
    if len(dirs) != 1:  # zero, or conflicting headings -> don't guess
        return None
    ux, uy = next(iter(dirs))
    px, py = float(my_pos[0]), float(my_pos[1])
    # Keep cardinals axis-true: "east" means +x with no implied north/south bias.
    # Project far so downstream clamp decides actual per-turn travel distance.
    return (px + ux * 10000.0, py + uy * 10000.0, "")


def _point_inside_zone_near_gateway(
    scene_geometry: "SceneGeometry",
    *,
    gateway: tuple[float, float],
    approach_from: tuple[float, float],
    dest_zone: str,
    center_of,
) -> Optional[tuple[float, float]]:
    """Return a point just inside ``dest_zone`` past a seam ``gateway``.

    A gateway landmark sits on the seam between two zones, so ``zone_at``
    resolves it to whichever side wins the point-in-polygon test (usually
    the zone the actor is leaving). To actually cross, we step a short
    distance past the gateway *continuing the actor's approach direction*
    (gateway minus approach point). That direction reliably points through
    the threshold regardless of where the destination zone's centroid lies,
    avoiding the sideways drift the centroid heuristic caused. We probe a
    few small step sizes and return the first that lands inside the target
    zone. Falls back to a step toward the centroid, then None.
    """
    gx, gy = gateway
    polygon = scene_geometry.zones.get(dest_zone)
    if polygon is None:
        for k, p in scene_geometry.zones.items():
            if k.upper() == dest_zone.upper():
                polygon = p
                break
    if polygon is None:
        return None

    def _inside(x: float, y: float) -> bool:
        z = scene_geometry.zone_at(Position(x, y))
        return bool(z) and z.upper() == dest_zone.upper()

    # Primary direction: keep walking the way the actor was already heading.
    dirs: list[tuple[float, float]] = []
    ax, ay = approach_from
    fx, fy = gx - ax, gy - ay
    flen = (fx * fx + fy * fy) ** 0.5
    if flen > 1e-6:
        dirs.append((fx / flen, fy / flen))
    # Fallback direction: toward the destination centroid.
    center = center_of(dest_zone)
    if center is not None:
        cx, cy = center[0] - gx, center[1] - gy
        clen = (cx * cx + cy * cy) ** 0.5
        if clen > 1e-6:
            dirs.append((cx / clen, cy / clen))

    for ux, uy in dirs:
        for step in (1.0, 2.0, 3.0, 5.0):
            nx, ny = gx + ux * step, gy + uy * step
            if _inside(nx, ny):
                return (nx, ny)
    return None


# Honorifics/articles that precede a name but must not be used to match it.
_NAME_TITLES = {
    "sister", "father", "brother", "mother", "sir", "lord", "lady",
    "master", "captain", "elder", "the",
}


def _infer_character_destination(
    intent_text: str,
    self_id: str,
    characters: dict,
    current_positions: dict[str, tuple[float, float, str]],
    active_characters: set[str],
) -> Optional[tuple[float, float, str]]:
    """Resolve "move toward <character>" to that character's live position.

    The movement backfill otherwise grounds only items (LATN) and
    zones/landmarks (shallow), so naming a party member ("move to Gilthaness",
    "move toward Amara") yields no destination and the actor never moves.
    Requires a movement cue word, then matches the intent text against each
    *other* active character's id and the proper-name/handle tokens of their
    name (titles and short words excluded). Returns that character's current
    (x, y, z) — clamped to walking speed downstream — or None when nothing, or
    more than one character, matches.
    """
    words = _dest_tokens(intent_text)
    if not words or not (words & _MOVE_CUE_WORDS):
        return None
    matches: list[tuple[float, float, str]] = []
    other_positions: list[tuple[float, float, str]] = []
    for cid in active_characters:
        if cid == self_id or cid not in characters:
            continue
        pos = current_positions.get(cid)
        if pos is None:
            continue
        other_positions.append(pos)
        cs = characters[cid]
        name = getattr(getattr(cs, "character", None), "name", "") or ""
        handle = getattr(cs, "scene_handle", "") or ""
        cands = {cid.lower()}
        for tok in _dest_tokens(name) | _dest_tokens(handle):
            if len(tok) >= 4 and tok not in _NAME_TITLES:
                cands.add(tok)
        if words & cands:
            matches.append(pos)
    # Exactly one named character -> its position.
    if len(matches) == 1:
        return matches[0]
    # In a one-on-one scene, "move closer" has a single reasonable referent.
    # Preserve ambiguity whenever two or more other characters are present.
    if not matches and words & {"closer", "nearer"} and len(other_positions) == 1:
        return other_positions[0]
    return None


def _infer_movement_destination(
    intent_text: str,
    scene_geometry: Optional[SceneGeometry],
    my_pos: Optional[tuple[float, float, str]],
    visited_zones: Optional[set[str]] = None,
) -> Optional[tuple[float, float, str]]:
    """Resolve a named destination in ``intent_text`` to coordinates.

    Player-Left sometimes names where it is going in the free-text INTENT
    (e.g. "Move to the first passage") but leaves MOVEMENT empty, so the
    structured ``movement_target`` is None and the actor never moves. This
    backfills the coordinate by matching the intent text against landmarks and
    zone names.

    Matching requires a movement cue word AND a shared *discriminating*
    token (an ordinal/name word like "first" or "echo", not a generic noun
    like "chamber"), so an ambiguous phrase resolves to nothing rather than
    an arbitrary pick. Landmarks win over zones; ties break by nearest
    distance from the actor (remaining exact ties yield None).
    Distance is clamped to walking speed downstream, so this only sets a
    direction of travel — it never teleports.
    """
    if scene_geometry is None or my_pos is None:
        return None
    words = _dest_tokens(intent_text)
    if not words or not (words & _MOVE_CUE_WORDS):
        return None

    px, py = my_pos[0], my_pos[1]
    current_zone = (my_pos[2] or "").upper()
    visible_zones: set[str] = set(visited_zones or set())
    if current_zone:
        visible_zones.add(current_zone)

    def _best(candidates: list[tuple[str, float, float, str]]):
        best = None
        best_dist = float("inf")
        best_score = 0
        tied = False
        for name, cx, cy, zone in candidates:
            cand = _dest_tokens(name)
            discriminating = cand - _DESTINATION_GENERIC
            shared = words & discriminating
            if not shared:
                continue
            score = len(shared)
            dist = ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5
            if score > best_score:
                best_score, best_dist = score, dist
                best, tied = (name, cx, cy, zone), False
            elif score == best_score:
                if dist < best_dist - 1e-6:
                    best_dist = dist
                    best = (name, cx, cy, zone)
                    tied = False
                elif abs(dist - best_dist) <= 1e-6:
                    tied = True
        return None if (best is None or tied) else best

    def _zone_center(zname: str) -> Optional[tuple[float, float]]:
        polygon = scene_geometry.zones.get(zname)
        if polygon is None:
            # zones dict may be keyed case-sensitively; match upper().
            for k, p in scene_geometry.zones.items():
                if k.upper() == zname.upper():
                    polygon = p
                    break
        if polygon is None or not polygon.vertices:
            return None
        verts = polygon.vertices
        return (
            sum(v[0] for v in verts) / len(verts),
            sum(v[1] for v in verts) / len(verts),
        )

    # Landmarks first (filtered to the same visibility as Points of interest).
    lm_candidates: list[tuple[str, float, float, str]] = []
    lm_zone_map: dict[str, set[str]] = {}
    for name, pos in scene_geometry.landmarks.items():
        lm_zones = _zones_for_point(pos, scene_geometry.zones)
        if lm_zones and not (lm_zones & visible_zones):
            continue
        display = name.replace("_", " ")
        lm_candidates.append((display, pos.x, pos.y, ""))
        lm_zone_map[display] = lm_zones
    hit = _best(lm_candidates)
    if hit is not None:
        name, hx, hy, _ = hit
        # If this landmark is a gateway onto a zone the actor has not yet
        # entered, the landmark itself usually sits on the seam, which
        # ``zone_at`` resolves to the *current* zone. Push the target just
        # across the threshold into the onward zone so arriving actually
        # changes zones instead of stalling at the mouth.
        onward_zones = sorted((lm_zone_map.get(name, set()) - visible_zones))
        if onward_zones:
            crossed = _point_inside_zone_near_gateway(
                scene_geometry,
                gateway=(hx, hy),
                approach_from=(px, py),
                dest_zone=onward_zones[0],
                center_of=_zone_center,
            )
            if crossed is not None:
                hx, hy = crossed
        return (hx, hy, "")

    # Fall back to named zones. Zone names may be known before a zone is
    # visited (e.g., upstairs guest rooms), so evaluate all authored zones.
    # When crossing from one zone to another, route through a connector
    # waypoint (stairs/doors) first to avoid ambiguous "jump to center"
    # behavior; once close to that waypoint, continue to a target-zone anchor.
    # If no connector exists, prefer a nearest authored landmark in the target
    # zone; use centroid only if no landmark exists there.
    zone_candidates: list[tuple[str, float, float, str]] = []
    for zname, polygon in scene_geometry.zones.items():
        verts = polygon.vertices
        if not verts:
            continue
        cx = sum(v[0] for v in verts) / len(verts)
        cy = sum(v[1] for v in verts) / len(verts)
        zone_candidates.append((zname, cx, cy, zname))
    zhit = _best(zone_candidates)
    if zhit is None:
        return None
    _, zx, zy, zzone = zhit

    current_zone = (my_pos[2] or "").upper()
    if current_zone and zzone.upper() != current_zone:
        connector_candidates: list[tuple[float, float, float, float]] = []

        def _add_connector_candidate(cx: float, cy: float) -> None:
            to_target = ((cx - zx) ** 2 + (cy - zy) ** 2) ** 0.5
            from_actor = ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5
            connector_candidates.append((to_target, from_actor, cx, cy))

        # Authored scene connections are explicit traversal waypoints.
        for _name, pos in (getattr(scene_geometry, "connections", {}) or {}).items():
            conn_zones = _zones_for_point(pos, scene_geometry.zones)
            if conn_zones and current_zone not in conn_zones:
                continue
            _add_connector_candidate(float(pos.x), float(pos.y))

        # Connector-like landmark names in the current zone are also good
        # waypoints (e.g., staircase, archway) for moving between zones.
        for name, pos in scene_geometry.landmarks.items():
            name_toks = _dest_tokens(name.replace("_", " "))
            if not (name_toks & _CONNECTOR_NAME_TOKENS):
                continue
            lm_zones = _zones_for_point(pos, scene_geometry.zones)
            if lm_zones and current_zone not in lm_zones:
                continue
            _add_connector_candidate(float(pos.x), float(pos.y))

        if connector_candidates:
            connector_candidates.sort(key=lambda t: (t[0], t[1]))
            _to_target, _from_actor, cx, cy = connector_candidates[0]
            # Only use connector-first while we are still approaching it;
            # once near it, continue onward into the destination zone.
            if _from_actor > 8.0:
                return (cx, cy, current_zone)

    nearest_zone_landmark: Optional[tuple[float, float]] = None
    nearest_dist = float("inf")
    for _name, pos in scene_geometry.landmarks.items():
        lm_zones = _zones_for_point(pos, scene_geometry.zones)
        if zzone.upper() not in lm_zones:
            continue
        dist = ((pos.x - px) ** 2 + (pos.y - py) ** 2) ** 0.5
        if dist < nearest_dist:
            nearest_dist = dist
            nearest_zone_landmark = (pos.x, pos.y)

    if nearest_zone_landmark is not None:
        return (nearest_zone_landmark[0], nearest_zone_landmark[1], zzone)
    return (zx, zy, zzone)



def _events_from_cr(
    cr,
    pre_active: set[str],
    post_active: set[str],
    handles: dict[str, str],
    game_time,
) -> list[str]:
    """Derive Python-verified event sentences from one character result.

    These are short factual statements (death, damage, boundary crossing,
    combat start/exit) that get surfaced to all subsequent characters via
    a "Recent events" block in their context. Lets every character see the
    consequences of prior actions even if the prose narration is ambiguous.
    """
    out: list[str] = []
    ts = (
        f"{game_time.hour:02d}:{game_time.minute:02d}"
        if game_time else f"t{cr.turn}"
    )
    actor = handles.get(cr.character_id, cr.character_id)
    adj = cr.adjudication
    just_died = pre_active - post_active

    if "combat_initiated" in adj.spatial_events and adj.approved:
        out.append(f"{ts} — combat begins")
    if "boundary_crossed" in adj.spatial_events and adj.approved:
        out.append(f"{ts} — {actor} crossed the magical boundary")
    if "exits_scene" in adj.spatial_events and adj.approved:
        out.append(f"{ts} — {actor} left the scene")

    for tid, dmg in (adj.hp_damage or {}).items():
        if not dmg or dmg <= 0:
            continue
        target = handles.get(tid, tid)
        if tid == cr.character_id:
            out.append(f"{ts} — {actor} took {dmg} damage from the boundary")
        else:
            out.append(f"{ts} — {actor} hit {target} for {dmg} damage")
        if tid in just_died and tid != cr.character_id:
            out.append(f"{ts} — {target} was killed")

    if cr.character_id in just_died:
        out.append(f"{ts} — {actor} was killed")

    return out


def _history_entry(handle: str, spoken: str, action: str, prose: str) -> str:
    """Render one speaker's contribution to running scene history.

    Entries are separated by a blank line so RECENT CONTEXT remains scannable
    when multiple characters speak and act in sequence.
    """
    parts: list[str] = []
    spoken_norm = re.sub(r"[^a-z0-9]+", " ", spoken.lower()).strip()
    prose_norm = re.sub(r"[^a-z0-9]+", " ", prose.lower()).strip()
    # Narration frequently embeds the exact spoken line. Do not add a second
    # explicit `says:` copy to history/prompt context when it already does.
    spoken_is_in_prose = bool(spoken_norm and spoken_norm in prose_norm)
    if (spoken.strip()
            and spoken.strip().lower() not in ("(silent)", "(silence)")
            and not spoken_is_in_prose):
        parts.append(f'{handle} says: "{spoken.strip()}"')
    if action.strip():
        parts.append(f"{handle} acts: {action.strip()}")
    if prose.strip():
        parts.append(prose.strip())
    if not parts:
        return ""
    return "\n\n" + "\n".join(parts)


def _reseed_discovered_from_examination_state(
    items: Optional[dict],
    party_examination_state: Optional[dict[tuple[str, str], dict]],
) -> None:
    """Re-populate each item's ``discovered_by`` from restored examination state.

    ``item.discovered_by`` is not checkpointed: loose scene items are rebuilt
    with an empty set on resume. The persisted ``party_examination_state`` does
    record examinations (keyed by ``(ZONE, normalized target)`` with the
    examiner id), so map it back onto the items. Without this, perception's
    "Items remembered or examined" section silently empties on every resume.
    """
    if not items or not party_examination_state:
        return
    for (state_zone, state_target), meta in party_examination_state.items():
        by = (meta or {}).get("by")
        if not by:
            continue
        for it in items.values():
            if _normalize_target_name(it.label or it.id) != state_target:
                continue
            it_zone = (getattr(it, "zone", None) or "").upper()
            if it_zone and state_zone and it_zone != state_zone:
                continue  # same name in a different zone — not this item
            it.discovered_by.add(by)


def _build_context(
    cs: CharacterSession,
    turn: int,
    scene_history: str,
    scene_geometry: Optional[SceneGeometry] = None,
    current_positions: Optional[dict[str, tuple[float, float, str]]] = None,
    active_characters: Optional[set[str]] = None,
    in_combat: bool = False,
    characters: Optional[dict[str, CharacterSession]] = None,
    recent_events: Optional[list[str]] = None,
    visited_zones: Optional[dict[str, set[str]]] = None,
    items: Optional[dict] = None,
    puzzles: Optional["PuzzleRegistry"] = None,
) -> RoleContext:
    """Build a RoleContext from session state."""
    # Replace baked-in "Your starting position: x=…" with the live value so
    # the character never uses stale starting coordinates when choosing movement.
    initial_scene = cs.initial_scene
    my_pos = (current_positions or {}).get(cs.character.id)
    if my_pos is not None:
        px, py, pzone = my_pos
        initial_scene = re.sub(
            r'Your starting position: x=[^\n]+',
            f'Your current position: x={px}, y={py}, zone={pzone}.',
            initial_scene,
        )
    scene = initial_scene
    scene = (
        f"{scene}\n\n## Current posture (Python-verified)\n"
        f"- You are {getattr(cs, 'posture', 'standing')}."
    )
    if scene_history:
        scene = f"{initial_scene}\n\n{scene_history}"
    if recent_events:
        events_block = (
            "## Recent events (Python-verified facts; trust over prose)\n"
            + "\n".join(f"- {ev}" for ev in recent_events)
        )
        scene = f"{scene}\n\n{events_block}"
    if cs.episodic_memory:
        memory_block = (
            "## What you remember (Python-verified)\n"
            + "\n".join(f"- {ev}" for ev in cs.episodic_memory[-6:])
        )
        scene = f"{scene}\n\n{memory_block}"
    if cs.recent_interactions:
        repeat_guard = (
            "## Anti-repetition guidance\n"
            "- You recently examined: "
            + ", ".join(cs.recent_interactions[-5:])
            + "\n"
            "- Do not repeat the same target unless genuinely new evidence appears."
            " If local clues are exhausted, move deeper."
        )
        scene = f"{scene}\n\n{repeat_guard}"
    # Maintain visited_zones for this character. The zone the character is
    # currently standing in counts as visited for future turns.
    char_visited: set[str] = set()
    if visited_zones is not None:
        char_visited = visited_zones.setdefault(cs.character.id, set())
        if my_pos is not None and my_pos[2]:
            char_visited.add(my_pos[2].upper())
    poi = _build_points_of_interest(scene_geometry, my_pos, char_visited)
    if poi:
        scene = f"{scene}\n\n{poi}"

    current_zone = (my_pos[2] if my_pos is not None else "") or ""
    puzzle_block = _build_puzzle_pressure_block(
        current_zone=current_zone,
        items=items,
        puzzles=puzzles,
    )
    if puzzle_block:
        scene = f"{scene}\n\n{puzzle_block}"

    perception = _build_perception(
        cs.character.id,
        scene_geometry,
        current_positions or {},
        active_characters or set(),
        characters=characters,
        items=items,
    )
    # Compute the set of character IDs the acting character can actually see,
    # for membership tests below (the perception string above uses scene
    # handles, not IDs, so substring tests against it are unreliable).
    visible_ids: set[str] = set()
    if scene_geometry is not None and my_pos is not None:
        import math as _math  # local alias; outer import inside _build_perception
        for other_id, other_pos in (current_positions or {}).items():
            if other_id == cs.character.id or other_id not in (active_characters or set()):
                continue
            a = Position(my_pos[0], my_pos[1])
            b = Position(other_pos[0], other_pos[1])
            if scene_geometry.can_see(a, b):
                visible_ids.add(other_id)
    # If combat is active and there are combatants not visible (different zone),
    # add a sound cue — growling and impact sounds carry regardless of LOS.
    if in_combat and perception is not None:
        my_zone = my_pos[2].upper() if my_pos else ""
        unseen_combatants = [
            cid for cid in (active_characters or set())
            if cid != cs.character.id
            and cid not in visible_ids
            and (current_positions or {}).get(cid, (None, None, my_zone))[2].upper() != my_zone
        ]
        if unseen_combatants:
            sound_note = (
                "- You hear sounds of combat nearby — growling, impact, "
                "and movement in the surrounding area. Something is fighting close by."
            )
            perception = (perception + "\n" + sound_note) if perception else sound_note
    return RoleContext(
        character_id=cs.character.id,
        turn=turn,
        condition_text=render_condition(cs.condition),
        scene_context=scene,
        soul=cs.soul,
        identity=cs.identity,
        perception=perception,
        in_combat=in_combat,
    )


# ---------------------------------------------------------------------------
# Combat resolver helpers
# ---------------------------------------------------------------------------

def _intent_is_attack(intent_text: str) -> bool:
    """Return True if the Player-Left intent string describes an attack action.

    LATN-grounded: the attack-verb vocabulary lives in the lexicon (isa the
    ``attack`` dim), so this is one check instead of a keyword regex to keep in
    sync -- "swing at" / "loose an arrow" are caught for free."""
    from engine import latn_resolver
    return latn_resolver.intent_has_action(intent_text, "attack")


def _resolve_teleport_destination(
    intent_text: str,
    scene_geometry: Optional[SceneGeometry],
    items: Optional[dict] = None,
) -> Optional[tuple[float, float, str]]:
    """Resolve a named zone, landmark, or item anywhere in the scene for Teleport.

    Unlike :func:`_infer_movement_destination`, Teleport can reach any place
    the caster can name (not just adjacent/visible ones) and lands exactly on
    the destination with no speed clamp. Resolution order is zones (the caster
    teleports into a region, landing at its centroid, which is reliably inside
    the polygon), then named landmarks, then named scene items/features (e.g.
    "the trigger glyphs") which land on the feature's own position.
    Matching needs a shared *discriminating* token (an ordinal/name word like
    "echo" or "glyph", not a generic noun like "chamber"); ambiguous ties
    resolve to None rather than an arbitrary pick — except that several items
    sharing the same discriminating name *and* the same zone (the three
    trigger glyphs) are treated as one destination.
    """
    if scene_geometry is None:
        return None
    words = _dest_tokens(intent_text)
    if not words:
        return None

    # Map-assisted casting may name an exact coordinate. Teleport is itself the
    # relocation cue, so this path is not subject to ordinary movement cues or
    # speed clamping.
    coordinate_match = _COORD_DEST_RE.search(intent_text or "")
    if coordinate_match is not None:
        cx = float(coordinate_match.group(1))
        cy = float(coordinate_match.group(2))
        zone = (scene_geometry.zone_at(Position(cx, cy)) or "").upper()
        if zone:
            return (cx, cy, zone)

    # Town venues are authored as child scenes whose doors live in the current
    # scene's Connections table. Resolve their aliases before generic zones so
    # "Teleport to Dustcloak's Curios" lands at that specific front door.
    place_path = getattr(scene_geometry, "place_path", "") or ""
    venue = _driftmoor_approach_doorway(intent_text, place_path)
    if venue is not None:
        _scene_name, (vx, vy, _zone) = venue
        zone = (scene_geometry.zone_at(Position(vx, vy)) or "").upper()
        return (vx, vy, zone)

    def _best(candidates: list[tuple[str, float, float, str]]):
        best = None
        best_score = 0
        tied = False
        for name, cx, cy, zone in candidates:
            discriminating = _dest_tokens(name) - _DESTINATION_GENERIC
            shared = words & discriminating
            if not shared:
                continue
            score = len(shared)
            if score > best_score:
                best_score, best, tied = score, (cx, cy, zone), False
            elif score == best_score:
                tied = True
        return None if (best is None or tied) else best

    # Zones first — teleport targets a region; centroid lands inside it.
    zone_candidates: list[tuple[str, float, float, str]] = []
    for zname, polygon in scene_geometry.zones.items():
        verts = polygon.vertices
        if not verts:
            continue
        cx = sum(v[0] for v in verts) / len(verts)
        cy = sum(v[1] for v in verts) / len(verts)
        zone_candidates.append((zname, cx, cy, zname.upper()))
    zhit = _best(zone_candidates)
    if zhit is not None:
        return zhit

    # Next, a named landmark, snapping to its containing zone label.
    lm_candidates: list[tuple[str, float, float, str]] = []
    for name, pos in scene_geometry.landmarks.items():
        zone = scene_geometry.zone_at(pos) or ""
        lm_candidates.append((name.replace("_", " "), pos.x, pos.y, zone.upper()))
    lmhit = _best(lm_candidates)
    if lmhit is not None:
        return lmhit

    # Finally, a named scene item/feature (e.g. "the trigger glyphs"). Several
    # items sharing both the discriminating name and a single zone count as one
    # destination; we land on the first such item's position.
    if not items:
        return None
    best_score = 0
    best_matches: list[tuple[float, float, str]] = []
    for item in items.values():
        pos = getattr(item, "position", None)
        if pos is None:
            continue
        label = item.label or item.id.replace("_", " ")
        discriminating = _dest_tokens(label) - _DESTINATION_GENERIC
        shared = words & discriminating
        if not shared:
            continue
        score = len(shared)
        zone = (item.zone or scene_geometry.zone_at(pos) or "").upper()
        if score > best_score:
            best_score = score
            best_matches = [(float(pos.x), float(pos.y), zone)]
        elif score == best_score:
            best_matches.append((float(pos.x), float(pos.y), zone))
    if not best_matches:
        return None
    zones = {z for _, _, z in best_matches}
    if len(zones) != 1:
        return None  # ambiguous: matching items span multiple zones
    return best_matches[0]


def _intent_is_spell(intent_text: str) -> bool:
    """Return True when intent text describes casting a spell.

    LATN-grounded on the ``cast`` dim (cast/invoke/channel). A bare "use a
    spell" with no named spell no longer trips the gate -- it never cast
    anything anyway (``_extract_spell_name_from_intent`` finds no name)."""
    from engine import latn_resolver
    return latn_resolver.intent_has_action(intent_text, "cast")


def _extract_spell_name_from_intent(intent_text: str, cs: CharacterSession) -> str | None:
    """Infer the intended spell name by matching known/prepared/cantrip names."""
    profile = getattr(cs.character, "spellcasting", None)
    if profile is None:
        return None

    candidates = [s.name for s in profile.cantrips] + [s.name for s in profile.prepared] + [s.name for s in profile.known]
    if not candidates:
        return None

    text = (intent_text or "").lower()
    for name in candidates:
        if name and name.lower() in text:
            return name

    # Fallback: handle patterns like "Cast Healing Word on X".
    m = re.search(r"\bcast\s+([A-Za-z'\s]+?)(?:\s+on\b|\s+at\b|$)", text)
    if m:
        hinted = m.group(1).strip()
        for name in candidates:
            if hinted == name.lower():
                return name
    return None


def _teleport_venue_arrival_fact(
    character_id: str,
    intent_text: str,
    scene_geometry: Optional[SceneGeometry],
) -> Optional[str]:
    """Authoritative narration fact for a teleport aimed at a town venue.

    Venue teleportation deliberately targets the exterior connection point.  A
    narrator otherwise tends to interpret the venue name as permission to put
    the caster inside the building, contradicting the position map and bypassing
    the separate ``enter`` action.
    """
    if scene_geometry is None:
        return None
    place_path = getattr(scene_geometry, "place_path", "") or ""
    venue = _driftmoor_approach_doorway(intent_text, place_path)
    if venue is None:
        return None
    scene_name, _door = venue
    venue_label = scene_name.replace("_", " ")
    return (
        f"[TELEPORT ARRIVAL] {character_id} materialized outside "
        f"{venue_label}, at its exterior doorway. They did not enter the "
        "building; do not narrate them inside, among its shelves, or in its "
        "rooms."
    )


def _resolve_spell_targets(
    intent: ActionIntent,
    *,
    caster_id: str,
    characters: dict[str, CharacterSession],
    active_characters: set[str],
) -> list[str]:
    """Resolve interaction target text to active character IDs for spell casting."""
    target_hint = (intent.interaction_target or "").strip().lower()
    if not target_hint:
        return []

    results: list[str] = []
    for cid in sorted(active_characters):
        if cid == caster_id or cid not in characters:
            continue
        if cid.lower() == target_hint or cid.lower().startswith(target_hint) or target_hint.startswith(cid.lower()):
            results.append(cid)
            continue
        cname = (characters[cid].character.name or "").strip().lower()
        if cname and (cname == target_hint or cname.startswith(target_hint) or target_hint in cname):
            results.append(cid)
    return results


# Item-transfer primitives + recipient resolution live in engine.item_transfer
# (extracted refactor). Re-exported here so existing
# `from engine.session import _resolve_recipient_character` etc. keep working,
# and so _handle_item_transfer below can use them unqualified.
from engine.item_transfer import (  # noqa: E402
    _RECIPIENT_STOPWORDS,
    _apply_item_transfer,
    _char_handle,
    _character_descriptor_tokens,
    _resolve_recipient_character,
    transfer_coins,
    transfer_thing,
)


def _handle_coin_transfer(
    *, intent_text: str, character_id: str,
    characters: dict[str, "CharacterSession"], active_characters: set[str],
    turn_num: int, game_time: Optional[GameTime], attack_log: list,
    recent_events: list, cs: "CharacterSession",
) -> bool:
    """Settle an explicit ``give/pay <person> <coins>`` purse transfer."""
    from models.currency import format_coins, parse_coins

    text = (intent_text or "").strip()
    if not re.match(r"^(?:i\s+)?(?:give|pay|hand)\b", text, re.IGNORECASE):
        return False
    amount_cp = parse_coins(text)
    if amount_cp is None:
        return False
    recipient = _resolve_recipient_character(
        text, actor_id=character_id, characters=characters,
        active_characters=active_characters,
    )
    if recipient is None:
        return False

    result = transfer_coins(
        amount_cp, from_id=character_id, to_id=recipient, characters=characters,
    )
    actor = _char_handle(characters[character_id], character_id)
    receiver = _char_handle(characters[recipient], recipient)
    amount = format_coins(amount_cp)
    ts = f"{game_time.hour}:{game_time.minute:02d}" if game_time else f"t{turn_num}"
    if result.ok:
        attack_log.append(
            f"[COIN-TRANSFER] SETTLED by the engine — do not alter: "
            f"{character_id} gives exactly {amount} to {recipient}; their purses "
            f"have been updated. Narrate only this outcome."
        )
        recent_events.append((turn_num, f"{ts} | {actor} gives {amount} to {receiver}."))
        _append_memory_note(cs, f"Turn {turn_num}: you gave {amount} to {receiver}.")
    else:
        attack_log.append(
            f"[COIN-TRANSFER] {character_id} cannot give {amount} to {recipient}: "
            f"{result.reason}; no coin moved. Narrate only this refusal."
        )
        recent_events.append((turn_num, f"{ts} | {actor} cannot pay {receiver} {amount}."))
    return True


def _handle_item_transfer(
    *,
    transfer_verb: str,
    item_obj: "Item",
    label: str,
    character_id: str,
    characters: dict[str, "CharacterSession"],
    active_characters: set[str],
    current_positions: dict,
    intent_text: str,
    actor_zone: str,
    turn_num: int,
    game_time: Optional[GameTime],
    attack_log: list,
    recent_events: list,
    cs: "CharacterSession",
    authored_response: Optional[str],
    recipient_override: Optional[str] = None,
) -> None:
    """Apply a take/drop/give possession change and log the outcome.

    Mutates ``item_obj.holder`` and the relevant character inventories via
    :func:`_apply_item_transfer`, appends a ``[ITEM-TRANSFER]`` line to the
    resolution log (so the narrator reflects what actually happened), and
    records a recent-events bullet and the actor's memory note. ``give``
    only transfers on a single unambiguous recipient match; otherwise it
    narrates without moving the item.
    """
    ts = (
        f"{game_time.hour}:{game_time.minute:02d}"
        if game_time else f"t{turn_num}"
    )
    actor_handle = _char_handle(characters[character_id], character_id)
    actor_pos = current_positions.get(character_id, (0.0, 0.0, actor_zone))

    def _emit(log_line: str, event_text: str, memory_text: Optional[str]) -> None:
        attack_log.append(log_line)
        recent_events.append((turn_num, f"{ts} | {event_text}"))
        if memory_text:
            _append_memory_note(cs, f"Turn {turn_num}: {memory_text}")

    if transfer_verb == "take":
        if item_obj.holder == character_id:
            _emit(
                f"[ITEM-TRANSFER] {character_id} already carries {label}; "
                f"no change. Do not narrate a fresh pickup.",
                f"{actor_handle} is already carrying the {label}.",
                None,
            )
            return
        if item_obj.holder and item_obj.holder != character_id:
            holder_handle = _char_handle(
                characters.get(item_obj.holder, characters[character_id]),
                item_obj.holder,
            ) if item_obj.holder in characters else item_obj.holder
            _emit(
                f"[ITEM-TRANSFER] {character_id} cannot take {label}: it is "
                f"held by {item_obj.holder}. Narrate that {holder_handle} has "
                f"it, not a successful pickup.",
                f"{actor_handle} reaches for the {label}, but {holder_handle} "
                f"is holding it.",
                None,
            )
            return
        # Taking unclaimed loot makes you its owner; a thing someone else owns
        # keeps its owner (possession without ownership — theft is Phase 6).
        transfer_thing(
            item_obj, from_id=item_obj.holder, to_id=character_id,
            characters=characters,
            move_ownership=(getattr(item_obj, "owner", None) is None),
            coin_cp=0, target_pos=actor_pos,
        )
        item_obj.discovered_by.add(character_id)
        flavor = authored_response or f"{actor_handle} picks up the {label}."
        from engine import loadout
        if getattr(item_obj, "weapon", None) is not None:
            # A picked-up weapon becomes usable: register it on the character and
            # ready it (auto-sheathing to free a hand if needed).
            _emit(
                f"[ITEM-TRANSFER] {character_id} takes {label} (now carried by "
                f"{character_id}): {flavor}",
                f"{actor_handle} picks up the {label}.",
                f"you picked up {label} and are now carrying it.",
            )
            _w = loadout.register_held_weapon(cs, item_obj)
            if _w is not None:
                _ld: list[str] = []
                loadout.draw(cs, _w, _ld)
                if _ld:
                    attack_log.append(f"[LOADOUT] {character_id}: " + ", ".join(_ld))
        else:
            # A non-weapon (a torch, a relic) is taken up into a hand. Surface
            # the item's authored description so the narrator gives the player a
            # close look at what they now hold.
            in_hand = loadout.hold_item(cs, item_obj.id)
            desc = (getattr(item_obj, "description", "") or "").strip()
            hand_note = (
                "It is now in hand." if in_hand
                else "Their hands are full, so they tuck it away."
            )
            detail = f" Up close: {desc}" if desc else ""
            _emit(
                f"[ITEM-TRANSFER] {character_id} takes {label} (now carried by "
                f"{character_id}): {flavor} {hand_note} Describe the item in "
                f"vivid detail for the player.{detail}",
                f"{actor_handle} picks up the {label}.",
                f"you picked up {label} and are now holding it.",
            )
            if not in_hand:
                loadout.stow_item(cs, item_obj.id)  # no-op safety; keep in pack
        return

    if transfer_verb == "drop":
        if item_obj.holder != character_id:
            _emit(
                f"[ITEM-TRANSFER] {character_id} is not carrying {label}; "
                f"nothing to drop. Do not narrate a drop.",
                f"{actor_handle} is not carrying the {label}.",
                None,
            )
            return
        from engine import loadout
        loadout.stow_item(cs, item_obj.id)  # free the hand if it was held
        # Dropping releases possession to the floor but not ownership — your pack
        # left in the rooming house is still yours.
        transfer_thing(
            item_obj, from_id=character_id, to_id=None, characters=characters,
            move_ownership=False, coin_cp=0, target_pos=actor_pos,
        )
        flavor = authored_response or f"{actor_handle} sets down the {label}."
        _emit(
            f"[ITEM-TRANSFER] {character_id} drops {label} in "
            f"{actor_zone.upper() or 'this zone'}: {flavor}",
            f"{actor_handle} sets the {label} down.",
            f"you set down {label} in {actor_zone.upper() or 'this zone'}.",
        )
        return

    if transfer_verb == "stow":
        if item_obj.holder != character_id:
            _emit(
                f"[ITEM-TRANSFER] {character_id} is not carrying {label}; "
                f"nothing to stow. Do not narrate stowing it.",
                f"{actor_handle} is not carrying the {label}.",
                None,
            )
            return
        # Stow = into the pack: stays in inventory, but the hand is freed. Item
        # ownership and position are unchanged (still carried by the actor).
        from engine import loadout
        loadout.stow_item(cs, item_obj.id)
        flavor = authored_response or f"{actor_handle} stows the {label} in their pack."
        _emit(
            f"[ITEM-TRANSFER] {character_id} stows {label} in their pack "
            f"(still carried; hand freed): {flavor}",
            f"{actor_handle} stows the {label} away.",
            f"you stowed {label} in your pack.",
        )
        return

    # give / hand over
    if item_obj.holder and item_obj.holder != character_id:
        _emit(
            f"[ITEM-TRANSFER] {character_id} cannot give {label}: it is held "
            f"by {item_obj.holder}, not by them. Do not narrate a hand-off.",
            f"{actor_handle} does not have the {label} to give.",
            None,
        )
        return
    # LATN grounds the recipient by vector similarity (recipient_override, set
    # by the caller when the flag is on); fall back to the shallow token-overlap
    # match when it is absent.
    recipient = recipient_override or _resolve_recipient_character(
        intent_text,
        actor_id=character_id,
        characters=characters,
        active_characters=active_characters,
    )
    if recipient is None:
        _emit(
            f"[ITEM-TRANSFER] {character_id} tried to give {label} but the "
            f"recipient is unclear or absent; no transfer. Narrate the offer "
            f"without anyone receiving it.",
            f"{actor_handle} offers the {label}, but it is unclear who is "
            f"meant to take it.",
            None,
        )
        return
    recipient_handle = _char_handle(characters[recipient], recipient)
    recipient_pos = current_positions.get(recipient, actor_pos)
    # Giving hands over ownership as well as possession.
    transfer_thing(
        item_obj, from_id=character_id, to_id=recipient, characters=characters,
        move_ownership=True, coin_cp=0, target_pos=recipient_pos,
    )
    item_obj.discovered_by.add(recipient)
    flavor = authored_response or (
        f"{actor_handle} hands the {label} to {recipient_handle}."
    )
    _emit(
        f"[ITEM-TRANSFER] {character_id} gives {label} to {recipient} (now "
        f"carried by {recipient}): {flavor}",
        f"{actor_handle} hands the {label} to {recipient_handle}.",
        f"you handed {label} to {recipient_handle}.",
    )


@lru_cache(maxsize=1)
def _driftmoor_shop_catalog():
    """The town's shop catalog (priced goods as templates), built once."""
    from models.shop_catalog import ShopCatalog
    return ShopCatalog.from_places_root(_DRIFTMOOR_PLACES_ROOT)


def _current_shopkeeper(characters, active_characters, catalog):
    """The id of a present character who is a vendor (has for-sale stock), or
    None — commerce only happens where there's a shopkeeper to trade with."""
    for cid in sorted(active_characters):
        if cid in characters and catalog.entries_for(cid):
            return cid
    return None


def _commerce_negotiator(cs, character_id):
    """An ``async (prompt) -> reply`` bound to a human player's transport, or
    None for non-transport actors.

    It lets a buy run as a quote->confirm *sub-dialog inside the buyer's single
    turn*: the shopkeeper names a price and the very next line the human sends is
    read as their answer — no turn is consumed and no initiative advances between
    the quote and the reply (the same in-turn dialog shape the DM-question
    handler already uses). Web ``receive`` blocks until input; Telegram long-polls
    and returns empty on timeout, so we loop until a line actually arrives."""
    transport = (getattr(cs, "player_transport", None) or "llm").strip().lower()
    if transport == "web":
        from engine import web_transport
        wt = web_transport.for_character(character_id)

        async def ask(prompt: str) -> str:
            web_transport.flush_inbound(character_id)
            web_transport.set_awaiting(character_id, True)
            await wt.send(prompt)
            reply = (await wt.receive() or "").strip()
            web_transport.set_awaiting(character_id, False)
            return reply

        return ask
    if transport == "telegram":
        from engine import telegram_transport
        tt = telegram_transport.for_character(character_id)
        if tt is None:
            return None

        async def ask(prompt: str) -> str:
            await asyncio.to_thread(tt.flush)
            await asyncio.to_thread(tt.send, prompt)
            while True:
                reply = (await asyncio.to_thread(tt.poll_once) or "").strip()
                if reply:
                    return reply

        return ask
    return None


def _format_unknown_word_prompt(unknowns: list) -> str:
    """A DM line naming the words the parser did not recognise, with the nearest
    known spelling where there is one. ``unknowns`` is diagnose()'s output:
    a list of (word, [suggestions])."""
    parts = []
    for word, hints in unknowns:
        if hints:
            parts.append(f'"{word}" (did you mean {" or ".join(hints)}?)')
        else:
            parts.append(f'"{word}"')
    listing = "; ".join(parts)
    head = ("I don't know the word" if len(unknowns) == 1
            else "I don't know some of those words:")
    return (f'The Dungeon Master pauses: "{head} {listing}. '
            f'Could you put it another way?"')


def _filter_presented_unknowns(unknowns, presented_text: str):
    """Do not reject vocabulary the game itself recently showed the player."""
    presented = set(re.findall(r"[a-z0-9]+", (presented_text or "").lower()))
    return [entry for entry in unknowns if entry[0].lower() not in presented]


def _format_ambiguous_venue_prompt(candidates) -> str:
    labels = [label for _scene_name, label in candidates]
    choices = ", ".join(labels[:-1]) + f" or {labels[-1]}"
    return (
        'The Dungeon Master pauses: "That place name is ambiguous. '
        f'Did you mean {choices}?"'
    )


async def _clarify_ambiguous_venue(intent_text, *, ask, candidates):
    """Ask once which venue was meant, preserving the original enter verb."""
    if not candidates:
        return intent_text
    reply = (await ask(_format_ambiguous_venue_prompt(candidates)) or "").strip()
    if not reply:
        return intent_text
    if re.search(r"\b(?:enter|visit|go|step|walk)\b", reply.lower()):
        return reply
    return f"enter {reply}"


async def _clarify_unknown_words(intent_text, *, ask, diagnose_fn, max_rounds: int = 3):
    """In-turn sub-dialog for a human whose line uses words the lexicon doesn't
    know: the DM names them (and near spellings) and asks for a rephrase, reading
    the reply and re-checking, up to ``max_rounds``. Returns the refined line
    (or the player's last line if they don't clear it, so the caller proceeds
    with best effort). No LLM, no turn consumed.

    ``diagnose_fn(text)`` must be self-contained w.r.t. the active lexicon (set
    it internally) so no lexicon global is held across the ``await`` -- other
    scenes may run concurrently."""
    text = intent_text or ""
    for _ in range(max_rounds):
        unknowns = diagnose_fn(text)
        if not unknowns:
            return text
        reply = (await ask(_format_unknown_word_prompt(unknowns)) or "").strip()
        if not reply:
            return text
        text = reply
    return text


def _player_intent_grounds(intent_text, *, lexicon, adapter, items, characters,
                           actor_zone, entries) -> bool:
    """True when the engine can ground the line to *some* action -- a buy/sell of
    a real good, or any recognized action verb (examine / take / give / attack /
    cast / move, incl. "go to X" / "enter X").

    Gates the unknown-word clarification: a line that grounds is acted on and its
    surrounding prose narrated, never interrogated about vocabulary ("I look
    around and ask for bolts" buys the bolts; it doesn't quibble over "look").
    Only when nothing grounds does the clarification help. Deliberately generous
    -- when unsure, treat as grounded so we don't nag."""
    from engine import latn_resolver
    from engine.latn_integration import resolve_commerce
    try:
        if entries and resolve_commerce(intent_text, items, characters, actor_zone, entries):
            return True
    except Exception:  # noqa: BLE001 - a gate must never crash the turn
        pass
    try:
        if latn_resolver.resolve_actions(intent_text, lexicon=lexicon, adapter=adapter):
            return True
    except Exception:  # noqa: BLE001
        pass
    return False


async def _handle_commerce(
    *,
    intent_text: str,
    character_id: str,
    characters: dict,
    items: dict,
    cs: "CharacterSession",
    turn_num: int,
    game_time: Optional[GameTime],
    attack_log: list,
    recent_events: list,
    shopkeeper: str,
    catalog,
    negotiate=None,
) -> bool:
    """Resolve a buy/sell against the ``shopkeeper`` present in the scene. Returns
    True when the intent was a commerce action (so the caller skips the scene-item
    interaction path), False otherwise.

    A buy is an engine-owned exchange settled inside the buyer's single turn — a
    *sub-dialog*, not a cross-turn handoff. When ``negotiate`` is supplied (an
    ``async (prompt) -> reply`` bound to the buyer's transport), the shopkeeper
    quotes a price and the same nested exchange reads the buyer's yes/no reply
    right away — no initiative advances between the quote and the answer. An
    affirm completes the sale. A monetary counteroffer is evaluated against the
    merchant's authored flexibility; the merchant may accept it or make one
    final counter, still without advancing initiative. Other replies let the
    offer lapse. With no ``negotiate`` (a non-interactive actor) a priced buy
    settles at the listed price directly. Sells settle in one step (cross-turn
    item refs are a later refinement)."""
    from engine import commerce, loadout
    from engine.latn_integration import resolve_commerce, resolve_response
    from models.currency import format_coins, parse_coins

    loadout.materialize_things(cs)
    possessions = {t.id: t for t in (getattr(cs, "things", None) or [])}

    ts = f"{game_time.hour}:{game_time.minute:02d}" if game_time else f"t{turn_num}"
    actor = _char_handle(characters[character_id], character_id)
    keep = _char_handle(characters[shopkeeper], shopkeeper)

    def _emit(log_line: str, event_text: str, memory_text: Optional[str] = None) -> None:
        attack_log.append(log_line)
        recent_events.append((turn_num, f"{ts} | {event_text}"))
        if memory_text:
            _append_memory_note(cs, f"Turn {turn_num}: {memory_text}")

    def _commit_buy(entry, agreed_price_cp: Optional[int] = None) -> None:
        r = commerce.settle_buy(entry, buyer_id=character_id, shopkeeper_id=shopkeeper,
                                catalog=catalog, characters=characters,
                                agreed_price_cp=agreed_price_cp)
        price = format_coins(r.price_cp)
        if not r.ok:
            why = {"cannot_afford": f"can't afford the {entry.name} ({price})",
                   "not_for_sale": f"the {entry.name} isn't for sale"}.get(
                       r.reason, f"can't buy the {entry.name}")
            _emit(f"[COMMERCE] SETTLED by the engine — do not alter: {character_id} "
                  f"{why}; NO purchase happened and no coin moved. Narrate only "
                  f"this refusal.",
                  f"{actor} tries to buy the {entry.name}, but {why}.")
            return
        thing = r.thing
        items[thing.id] = thing
        if getattr(thing, "weapon", None) is not None:
            weapon = loadout.register_held_weapon(cs, thing)
            if weapon is not None:
                loadout.draw(cs, weapon)
        else:
            if getattr(cs, "pack", None) is None:
                cs.pack = []
            if thing not in cs.pack:
                cs.pack.append(thing)
            loadout.hold_item(cs, thing.id)
        loadout.materialize_things(cs)
        name = thing.name or thing.id
        _emit(f"[COMMERCE] SETTLED by the engine — do not alter: {character_id} "
              f"bought {name} from {shopkeeper} for exactly {price}; it is now in "
              f"their possession and the coin has changed hands. Narrate only this "
              f"outcome — do not change the price, the good, or whether it happened.",
              f"{actor} buys the {name} from {keep} for {price}.",
              f"you bought {name} for {price}.")
        # In a food-service venue, "drink the ale" / "eat the pie" naturally
        # means order and consume it.  Commerce owns the purchase first; once
        # settled, run the same affordance-gated manipulation used for any
        # possessed consumable.
        from engine import manipulation
        consume_verb = manipulation.classify_verb(intent_text, thing)
        if consume_verb in {"eat", "drink"}:
            mr = manipulation.apply_manipulation(
                cs, consume_verb, thing, items=items,
                actor_pos=(0.0, 0.0, ""), actor_zone="",
                character_id=character_id, game_time=game_time,
                turn_num=turn_num,
            )
            if mr.applied:
                attack_log.extend(mr.log)
                recent_events.extend(mr.events)
                for note in mr.memory:
                    _append_memory_note(cs, note)
                from models.thing import CONSUMED
                if getattr(getattr(thing, "carry", None), "location", "") == CONSUMED:
                    items.pop(thing.id, None)

    res = resolve_commerce(
        intent_text, possessions, characters, "", catalog.entries_for(shopkeeper))
    if res is None:
        return False
    verb, obj = res

    # --- A buy: quote a price, then settle only on the buyer's confirmation —
    #     all inside this one turn (a sub-dialog on the buyer's transport, so no
    #     initiative advances between the quote and the answer). ---
    if verb == "buy":
        if obj is None:
            _emit(f"[COMMERCE] {character_id} wants to buy from {shopkeeper} but "
                  f"which good is unclear; no offer made.",
                  f"{actor} asks {keep} about buying, but it's unclear what.")
            return True
        if obj.listed_price_cp is None:
            _emit(f"[COMMERCE] the {obj.name} is not for sale; {shopkeeper} makes "
                  f"no offer.",
                  f"{keep} says the {obj.name} isn't for sale.")
            return True
        price = format_coins(obj.listed_price_cp)
        if negotiate is None:
            # Non-interactive actor: no one to confirm with, settle directly.
            _commit_buy(obj)
            return True
        reply = await negotiate(
            f'{keep}: "That\'ll be {price} for the {obj.name}. Have we a deal?"'
        )
        if resolve_response(reply, characters, "") == "affirm":
            _commit_buy(obj)
            return True
        offered_cp = parse_coins(reply)
        if offered_cp is not None:
            from engine.negotiation import (
                evaluate_counteroffer, merchant_haggle_policy,
            )
            decision = evaluate_counteroffer(
                ask_cp=obj.listed_price_cp,
                offered_cp=offered_cp,
                policy=merchant_haggle_policy(
                    shopkeeper, category=getattr(obj, "category", "") or ""
                ),
            )
            if decision.accepted and decision.agreed_cp is not None:
                _commit_buy(obj, decision.agreed_cp)
                return True
            if decision.counter_cp is not None:
                offered = format_coins(offered_cp)
                counter = format_coins(decision.counter_cp)
                counter_reply = await negotiate(
                    f'{keep}: "I can\'t do {offered}. I can make it {counter}. '
                    'Have we a deal?"'
                )
                if resolve_response(counter_reply, characters, "") == "affirm":
                    _commit_buy(obj, decision.counter_cp)
                    return True
        _emit(f"[COMMERCE] {character_id} does not take {shopkeeper}'s offer of "
              f"{obj.name} at {price}; the offer lapses and nothing changes hands. "
              f"Narrate only that the deal did not happen.",
              f"{actor} leaves the {obj.name} on the counter.")
        return True

    # sell (single-step settle)
    label = getattr(obj, "name", None) or getattr(obj, "label", None) or getattr(obj, "id", "item")
    if obj is None:
        _emit(f"[COMMERCE] {character_id} wants to sell to {shopkeeper} but which "
              f"item is unclear; no sale.",
              f"{actor} offers to sell {keep} something, but it's unclear what.")
        return True
    r = commerce.settle_sell(obj, seller_id=character_id, shopkeeper_id=shopkeeper,
                             characters=characters)
    price = format_coins(r.price_cp)
    if not r.ok:
        why = {"not_sellable": f"the {label} has no resale value",
               "not_owned": f"the {label} isn't theirs to sell",
               "shop_broke": f"{keep} can't cover {price} for the {label}"}.get(
                   r.reason, f"can't sell the {label}")
        _emit(f"[COMMERCE] SETTLED by the engine — do not alter: {character_id} "
              f"{why}; NO sale happened and no coin moved. Narrate only this refusal.",
              f"{actor} tries to sell the {label}, but {why}.")
        return True
    sold_id = getattr(obj, "id", "")
    items.pop(sold_id, None)
    cs.pack = [p for p in (getattr(cs, "pack", None) or []) if getattr(p, "id", "") != sold_id]
    cs.weapons = [w for w in (getattr(cs, "weapons", None) or []) if getattr(w, "id", "") != sold_id]
    loadout.materialize_things(cs)
    _emit(f"[COMMERCE] SETTLED by the engine — do not alter: {character_id} sold "
          f"{label} to {shopkeeper} for exactly {price}; ownership and coin have "
          f"changed hands. Narrate only this outcome.",
          f"{actor} sells the {label} to {keep} for {price}.",
          f"you sold {label} for {price}.")
    return True


def _append_memory_note(
    cs: CharacterSession,
    note: str,
    *,
    max_items: int = 18,
) -> None:
    """Append an episodic memory line, avoiding immediate duplicates."""
    text = (note or "").strip()
    if not text:
        return
    if cs.episodic_memory and cs.episodic_memory[-1] == text:
        return
    cs.episodic_memory.append(text)
    if len(cs.episodic_memory) > max_items:
        del cs.episodic_memory[:-max_items]


def _record_recent_interaction(
    cs: CharacterSession,
    target: str | None,
    *,
    max_items: int = 8,
) -> None:
    """Track recent interaction targets to discourage repeated searching."""
    norm = _normalize_target_name(target)
    if not norm:
        return
    cs.recent_interactions = [t for t in cs.recent_interactions if t != norm]
    cs.recent_interactions.append(norm)
    if len(cs.recent_interactions) > max_items:
        del cs.recent_interactions[:-max_items]


# Checkpoint serialization helpers live in engine.persistence (extracted).
# Re-exported so the save/resume orchestrators below and the tests use them
# unqualified.
from engine.persistence import (  # noqa: E402
    _checkpoint_filename,
    _deserialize_party_examination_state,
    _deserialize_spell_runtime_state,
    _serialize_item_ownership,
    _serialize_party_examination_state,
    _serialize_spell_runtime_state,
    _shared_exam_key,
)


def _has_vicious_mockery_disadvantage(
    runtime: SpellRuntimeState,
    attacker_id: str,
) -> bool:
    for effect in runtime.active_effects:
        if (
            effect.spell_name == "Vicious Mockery Disadvantage"
            and attacker_id in effect.target_ids
            and effect.remaining_rounds > 0
        ):
            return True
    return False


def _consume_vicious_mockery_disadvantage(
    runtime: SpellRuntimeState,
    attacker_id: str,
) -> bool:
    for i, effect in enumerate(runtime.active_effects):
        if (
            effect.spell_name == "Vicious Mockery Disadvantage"
            and attacker_id in effect.target_ids
        ):
            runtime.active_effects.pop(i)
            return True
    return False


def _classify_examination_result(
    *,
    verb: str,
    response: str,
) -> tuple[bool, bool, bool]:
    """Classify whether a shared examination likely needs follow-up.

    Returns (mark_examined, needs_followup, complete).
    """
    text = (response or "").strip().lower()
    if not text:
        return False, False, False

    followup_terms = (
        "glyph", "mechanism", "sequence", "locked", "rune", "sigil",
        "hairline crack", "door", "switch", "lever", "puzzle",
    )
    completion_terms = (
        "no scraps", "no signs", "no clue", "no traces", "nothing",
        "none", "undisturbed", "empty", "no obvious", "no fragments",
    )

    verb_norm = (verb or "").strip().lower()
    needs_followup = any(t in text for t in followup_terms) or verb_norm.startswith("press")
    complete = any(t in text for t in completion_terms)

    if needs_followup:
        return True, True, False
    if complete:
        return True, False, True
    return True, False, False


def _sync_carried_item_positions(
    characters: dict[str, "CharacterSession"],
    current_positions: dict,
    items: Optional[dict],
) -> None:
    """Make carried items follow their holder.

    A held item's position/zone are only set at the moment of pickup, so it
    otherwise "stays" in the zone where it was grabbed even as the holder walks
    away — which made "drop"/"save" fail once you moved (the verb resolver keys
    on the item's zone). Run once per turn after movement so each held item sits
    at its holder's current position, and possession verbs resolve in the
    holder's current zone. Loose items (no holder) are untouched. Perception
    already excludes held items (see ``_build_perception``), so this never makes
    a carried item surface as a loose scene item.
    """
    if not items:
        return
    from models.space_time import Position
    for it in (items.values() if hasattr(items, "values") else items):
        holder = getattr(it, "holder", None)
        if not holder or holder not in characters:
            continue
        pos = current_positions.get(holder)
        if pos is None:
            continue
        it.position = Position(float(pos[0]), float(pos[1]))
        zone = pos[2] if len(pos) > 2 else ""
        if zone:
            it.zone = zone


def _save_turn(
    checkpoint_dir: Path,
    turn: int,
    turn_result: TurnResult,
    characters: dict[str, CharacterSession],
    game_time: Optional[GameTime] = None,
    in_combat: bool = False,
    active_characters: Optional[set[str]] = None,
    current_positions: Optional[dict] = None,
    party_examination_state: Optional[dict[tuple[str, str], dict]] = None,
    spell_runtime: Optional[SpellRuntimeState] = None,
    items: Optional[dict] = None,
    scene_place_path: str = "",
) -> Path:
    """Save a turn checkpoint as JSON."""
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    path = checkpoint_dir / _checkpoint_filename(turn, game_time)

    active = active_characters if active_characters is not None else set(characters.keys())

    data = {
        "turn": turn,
        "scene_place_path": scene_place_path or "",
        "in_combat": in_combat,
        "active_characters": sorted(active),
        "game_time": {
            "hour": game_time.hour,
            "minute": game_time.minute,
            "day": game_time.day,
            "season": game_time.season,
            "period": game_time.period,
        } if game_time else None,
        "initiative_order": turn_result.initiative_order,
        "character_results": [
            {
                "character_id": cr.character_id,
                "turn": cr.turn,
                "intent": asdict(cr.intent),
                "output": asdict(cr.output),
                "adjudication": asdict(cr.adjudication),
                "narration": asdict(cr.narration),
            }
            for cr in turn_result.character_results
        ],
        "conditions": {
            char_id: cs.condition.state.to_dict()
            for char_id, cs in characters.items()
            if char_id in active
        },
        "hp": {
            char_id: {
                "current": getattr(cs.character, "current_hp", cs.character.hp),
                "max": cs.character.hp,
            }
            for char_id, cs in characters.items()
            if char_id in active
        },
        "current_positions": {
            char_id: {"x": pos[0], "y": pos[1], "zone": pos[2]}
            for char_id, pos in (current_positions or {}).items()
        },
        "memory": {
            char_id: {
                "episodic": cs.episodic_memory,
                "recent_interactions": cs.recent_interactions,
                "known_people": cs.known_people,
                "last_zone_seen": cs.last_zone_seen,
            }
            for char_id, cs in characters.items()
            if char_id in active
        },
        "party_examination_state": _serialize_party_examination_state(
            party_examination_state or {}
        ),
        "spell_runtime": _serialize_spell_runtime_state(
            spell_runtime or SpellRuntimeState()
        ),
        "item_ownership": _serialize_item_ownership(items or {}),
        "wielded": {
            char_id: list(getattr(cs, "wielded", None) or [])
            for char_id, cs in characters.items()
            if char_id in active and (getattr(cs, "wielded", None) or [])
        },
        "held_items": {
            char_id: list(getattr(cs, "held_items", None) or [])
            for char_id, cs in characters.items()
            if char_id in active and (getattr(cs, "held_items", None) or [])
        },
        "postures": {
            char_id: getattr(cs, "posture", "standing")
            for char_id, cs in characters.items()
            if char_id in active
        },
    }
    path.write_text(json.dumps(data, indent=2, default=str))
    return path


# ---------------------------------------------------------------------------
# Resume helpers
# ---------------------------------------------------------------------------

def load_resume_state(
    checkpoint_dir: Path,
    characters: dict[str, CharacterSession],
) -> tuple[
    int,
    int | None,
    str,
    set[str] | None,
    dict[str, tuple[float, float, str]],
    dict[tuple[str, str], dict],
    SpellRuntimeState,
]:
    """Read a checkpoint directory and prepare state for resuming a session.

    Patches ``characters`` conditions in-place from the last checkpoint so
    characters start the next session with their ending emotional state.

    Returns:
        (last_turn, last_game_minutes, scene_history, last_active_characters, checkpoint_positions)
        - last_turn: the highest turn number found (0 if none)
        - last_game_minutes: absolute game minutes from the last checkpoint's
          game_time (None if no game_time was recorded)
        - scene_history: full reconstructed narrative/dialogue history so
          characters remember what happened in prior turns
        - last_active_characters: set of character IDs still active at session end
        - checkpoint_positions: dict of character_id → (x, y, zone) from the last
          checkpoint, used to seed current_positions when resuming
    """
    from models.condition import NeurochemicalState

    files = sorted(
        (p for p in checkpoint_dir.glob("*.json") if not p.stem.endswith("transcript")),
        key=lambda p: p.name,
    )
    if not files:
        return 0, None, "", None, {}, {}, SpellRuntimeState()

    scene_history = ""
    last_turn = 0
    last_game_minutes: int | None = None
    last_active_characters: set[str] | None = None

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        last_turn = data["turn"]

        gt = data.get("game_time")
        if gt:
            last_game_minutes = gt["day"] * 24 * 60 + gt["hour"] * 60 + gt["minute"]

        # Reconstruct history using the same logic as iter_session
        for cr_data in data.get("character_results", []):
            char_id = cr_data["character_id"]
            spoken = (cr_data["output"].get("spoken") or "").strip()
            action = (cr_data["output"].get("action") or "").strip()
            prose = (cr_data["narration"].get("prose") or "").strip()
            entry = _history_entry(char_id, spoken, action, prose)
            scene_history += entry

    # Restore conditions from the last checkpoint
    last_data = json.loads(files[-1].read_text(encoding="utf-8"))
    for char_id, state_dict in last_data.get("conditions", {}).items():
        if char_id in characters:
            characters[char_id].condition.state = NeurochemicalState.from_dict(state_dict)

    # Restore HP from last checkpoint so characters resume with correct health
    for char_id, hp_dict in last_data.get("hp", {}).items():
        if char_id in characters:
            characters[char_id].character.current_hp = hp_dict["current"]

    # Restore the wielded set so a resumed fight remembers what's drawn
    # (default_wield at scene start only fills empty hands, so this wins).
    for char_id, wielded in last_data.get("wielded", {}).items():
        if char_id in characters and isinstance(wielded, list):
            characters[char_id].wielded = list(wielded)

    # Restore held non-weapon items (e.g. a torch) so a resumed scene remembers
    # what's in hand vs stowed in the pack.
    for char_id, held in last_data.get("held_items", {}).items():
        if char_id in characters and isinstance(held, list):
            characters[char_id].held_items = list(held)

    for char_id, posture in last_data.get("postures", {}).items():
        if char_id in characters and posture in {
            "standing", "seated", "kneeling", "prone"
        }:
            from engine.posture import apply_posture
            apply_posture(characters[char_id], posture)

    # Restore active_characters set if the checkpoint recorded it
    if "active_characters" in last_data:
        last_active_characters = set(last_data["active_characters"])

    # Restore per-character episodic memory when present.
    for char_id, mem in last_data.get("memory", {}).items():
        if char_id not in characters:
            continue
        cs = characters[char_id]
        cs.episodic_memory = list(mem.get("episodic", []))
        cs.recent_interactions = list(mem.get("recent_interactions", []))
        cs.known_people = dict(mem.get("known_people", {}))
        cs.last_zone_seen = (mem.get("last_zone_seen") or "").upper()

    # Restore positions from last checkpoint (may be absent in older checkpoints)
    checkpoint_positions: dict[str, tuple[float, float, str]] = {}
    for char_id, pos_dict in last_data.get("current_positions", {}).items():
        checkpoint_positions[char_id] = (pos_dict["x"], pos_dict["y"], pos_dict["zone"])

    party_examination_state = _deserialize_party_examination_state(
        last_data.get("party_examination_state")
    )
    spell_runtime = _deserialize_spell_runtime_state(last_data.get("spell_runtime"))

    return (
        last_turn,
        last_game_minutes,
        scene_history,
        last_active_characters,
        checkpoint_positions,
        party_examination_state,
        spell_runtime,
    )


def restore_item_ownership(
    checkpoint_dir: Path,
    items: dict | None,
    characters: dict[str, CharacterSession],
) -> None:
    """Re-apply held-item ownership from the last checkpoint, in place.

    Reads ``item_ownership`` from the most recent checkpoint and sets each
    item's ``holder``, restores its carried position/zone, and rebuilds the
    holding character's ``inventory``. Loose items are untouched. Safe to
    call when there are no checkpoints or no items (no-op).
    """
    if not items:
        return
    files = sorted(
        (p for p in checkpoint_dir.glob("*.json") if not p.stem.endswith("transcript")),
        key=lambda p: p.name,
    )
    if not files:
        return
    from models.space_time import Position

    last_data = json.loads(files[-1].read_text(encoding="utf-8"))
    ownership = last_data.get("item_ownership") or {}
    if not isinstance(ownership, dict):
        return
    for iid, meta in ownership.items():
        it = items.get(iid)
        if it is None or not isinstance(meta, dict):
            continue
        holder = meta.get("holder")
        if not holder:
            continue
        it.holder = str(holder)
        x, y = meta.get("x"), meta.get("y")
        if x is not None and y is not None:
            it.position = Position(float(x), float(y))
        if meta.get("zone"):
            it.zone = meta["zone"]
        if holder in characters:
            inv = characters[holder].character.inventory
            if iid not in inv:
                inv.append(iid)


# ---------------------------------------------------------------------------
# Human transport helpers (Telegram/file inbox-outbox)
# ---------------------------------------------------------------------------

_PURGE_DIR_SCRIPT = (
    "from pathlib import Path\n"
    "import sys\n"
    "p = Path(sys.argv[1]).expanduser()\n"
    "if p.exists() and p.is_dir():\n"
    "    for f in list(p.iterdir()):\n"
    "        if f.is_file():\n"
    "            f.unlink(missing_ok=True)\n"
)

_WRITE_TEXT_SCRIPT = (
    "from pathlib import Path\n"
    "from datetime import datetime\n"
    "import sys\n"
    "p = Path(sys.argv[1]).expanduser()\n"
    "data = sys.stdin.read()\n"
    "if p.exists() and p.is_dir():\n"
    "    p.mkdir(parents=True, exist_ok=True)\n"
    "    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')\n"
    "    (p / f'msg_{stamp}.txt').write_text(data, encoding='utf-8')\n"
    "else:\n"
    "    p.parent.mkdir(parents=True, exist_ok=True)\n"
    "    p.write_text(data, encoding='utf-8')\n"
)

_POP_TEXT_SCRIPT = (
    "from pathlib import Path\n"
    "import sys\n"
    "cutoff = int(sys.argv[2]) if len(sys.argv) > 2 else 0\n"
    "p = Path(sys.argv[1]).expanduser()\n"
    "if p.exists() and p.is_dir():\n"
    "    files = sorted([f for f in p.iterdir() if f.is_file()], key=lambda f: (f.stat().st_mtime_ns, f.name))\n"
    "    fresh = []\n"
    "    for f in files:\n"
    "        try:\n"
    "            mtime = f.stat().st_mtime_ns\n"
    "        except FileNotFoundError:\n"
    "            continue\n"
    "        if cutoff and mtime < cutoff:\n"
    "            f.unlink(missing_ok=True)\n"
    "        else:\n"
    "            fresh.append((mtime, f))\n"
    "    target = None\n"
    "    if fresh:\n"
    "        target = fresh[-1][1]\n"
    "    if target is not None:\n"
    "        txt = target.read_text(encoding='utf-8')\n"
    "        target.unlink(missing_ok=True)\n"
    "        for _, other in fresh[:-1]:\n"
    "            other.unlink(missing_ok=True)\n"
    "        print(txt, end='')\n"
    "elif p.exists() and p.is_file():\n"
    "    if p.stat().st_mtime_ns >= cutoff:\n"
    "        txt = p.read_text(encoding='utf-8')\n"
    "        p.write_text('', encoding='utf-8')\n"
    "        print(txt, end='')\n"
    "    elif cutoff:\n"
    "        p.write_text('', encoding='utf-8')\n"
)


def _run_host_python(
    *,
    host: str,
    script: str,
    args: list[str],
    stdin_text: str = "",
) -> str:
    """Run a tiny Python snippet locally or over SSH and return stdout."""
    host_norm = (host or "").strip().lower()
    node_full = (platform.node() or "").strip().lower()
    node_short = node_full.split(".")[0] if node_full else ""
    local_aliases = {"", "localhost", "127.0.0.1", "::1", "local", "self", node_full, node_short}

    is_local = host_norm in local_aliases
    cmd = ["python3", "-c", script, *args] if is_local else ["ssh", host, "python3", "-c", script, *args]
    proc = subprocess.run(
        cmd,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        scope = f"host '{host}'" if host else "local host"
        raise RuntimeError(f"Transport command failed on {scope}: {stderr}")
    return proc.stdout


def _is_local_host(host: str) -> bool:
    host_norm = (host or "").strip().lower()
    node_full = (platform.node() or "").strip().lower()
    node_short = node_full.split(".")[0] if node_full else ""
    local_aliases = {"", "localhost", "127.0.0.1", "::1", "local", "self", node_full, node_short}
    return host_norm in local_aliases


def _run_remote_shell(host: str, shell_script: str, stdin_text: str = "") -> str:
    """Execute a bash snippet on a remote host over SSH."""
    proc = subprocess.run(
        ["ssh", host, "bash", "-lc", shell_script],
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"Transport command failed on host '{host}': {stderr}")
    return proc.stdout


def _run_remote_python_stdin(host: str, script: str, args: list[str]) -> str:
    """Execute Python script on remote host with script passed via stdin."""
    proc = subprocess.run(
        ["ssh", host, "python3", "-", *args],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"Transport command failed on host '{host}': {stderr}")
    return proc.stdout


async def _host_purge_dir(host: str, path: str) -> None:
    """Remove all files in a remote/local directory (for pre-session outbox cleanup)."""
    expanded_path = str(Path(path).expanduser())
    if not _is_local_host(host):
        script = (
            "from pathlib import Path\n"
            "import sys\n"
            "p = Path(sys.argv[1]).expanduser()\n"
            "if p.exists() and p.is_dir():\n"
            "    for f in list(p.iterdir()):\n"
            "        if f.is_file():\n"
            "            f.unlink(missing_ok=True)\n"
        )
        await asyncio.to_thread(
            _run_remote_python_stdin,
            host,
            script,
            [expanded_path],
        )
        return
    await asyncio.to_thread(
        _run_host_python,
        host=host,
        script=_PURGE_DIR_SCRIPT,
        args=[expanded_path],
        stdin_text="",
    )


async def _host_write_text(host: str, path: str, text: str) -> None:
    expanded_path = str(Path(path).expanduser())
    if not _is_local_host(host):
        payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
        script = (
            "from pathlib import Path\n"
            "from datetime import datetime\n"
            "import base64\n"
            "import sys\n"
            "p = Path(sys.argv[1]).expanduser()\n"
            "data = base64.b64decode(sys.argv[2]).decode('utf-8')\n"
            "if p.exists() and p.is_dir():\n"
            "    p.mkdir(parents=True, exist_ok=True)\n"
            "    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')\n"
            "    (p / f'msg_{stamp}.txt').write_text(data, encoding='utf-8')\n"
            "else:\n"
            "    p.parent.mkdir(parents=True, exist_ok=True)\n"
            "    p.write_text(data, encoding='utf-8')\n"
        )
        await asyncio.to_thread(
            _run_remote_python_stdin,
            host,
            script,
            [expanded_path, payload],
        )
        return
    await asyncio.to_thread(
        _run_host_python,
        host=host,
        script=_WRITE_TEXT_SCRIPT,
        args=[expanded_path],
        stdin_text=text,
    )


async def _host_read_text(host: str, path: str, *, min_mtime_ns: int = 0) -> str:
    expanded_path = str(Path(path).expanduser())
    if not _is_local_host(host):
        script = (
            "from pathlib import Path\n"
            "import sys\n"
            "cutoff = int(sys.argv[2]) if len(sys.argv) > 2 else 0\n"
            "p = Path(sys.argv[1]).expanduser()\n"
            "if p.exists() and p.is_dir():\n"
            "    files = sorted([f for f in p.iterdir() if f.is_file()], key=lambda f: (f.stat().st_mtime_ns, f.name))\n"
            "    fresh = []\n"
            "    for f in files:\n"
            "        try:\n"
            "            mtime = f.stat().st_mtime_ns\n"
            "        except FileNotFoundError:\n"
            "            continue\n"
            "        if cutoff and mtime < cutoff:\n"
            "            f.unlink(missing_ok=True)\n"
            "        else:\n"
            "            fresh.append((mtime, f))\n"
            "    target = None\n"
            "    if fresh:\n"
            "        target = fresh[-1][1]\n"
            "    if target is not None:\n"
            "        txt = target.read_text(encoding='utf-8')\n"
            "        target.unlink(missing_ok=True)\n"
            "        for _, other in fresh[:-1]:\n"
            "            other.unlink(missing_ok=True)\n"
            "        print(txt, end='')\n"
            "elif p.exists() and p.is_file():\n"
            "    if p.stat().st_mtime_ns >= cutoff:\n"
            "        txt = p.read_text(encoding='utf-8')\n"
            "        p.write_text('', encoding='utf-8')\n"
            "        print(txt, end='')\n"
            "    elif cutoff:\n"
            "        p.write_text('', encoding='utf-8')\n"
        )
        return await asyncio.to_thread(
            _run_remote_python_stdin,
            host,
            script,
            [expanded_path, str(min_mtime_ns)],
        )
    return await asyncio.to_thread(
        _run_host_python,
        host=host,
        script=_POP_TEXT_SCRIPT,
        args=[expanded_path, str(min_mtime_ns)],
        stdin_text="",
    )


def _apply_loadout_intent(intent_text: str, cs: "CharacterSession",
                          log: list[str]) -> None:
    """Apply draw/sheathe manipulations named in the intent and auto-draw the
    weapon the actor says they're attacking with, mutating ``cs.wielded``.

    Focused clause parser (split on commas / and / then) so "I sheathe my
    dagger, draw my crossbow and attack the spider" works in one turn; the verb
    of each clause is read via LATN dims (draw/hold/sheathe/stow/attack), not a
    regex. Phase 2c replaces this with LATN multi-action parsing plus a reword.
    """
    from engine import loadout, latn_resolver
    from engine.combat_resolver import _weapon_name_tokens
    weapons = getattr(cs, "weapons", None) or []
    _GENERIC_TAGS = {
        "simple", "martial", "melee", "ranged", "weapon",
        "finesse", "light", "heavy", "reach", "thrown",
        "ammunition", "loading", "two_handed", "versatile", "natural",
    }

    def _name_tokens(w) -> set[str]:
        toks = set(_weapon_name_tokens(w))
        for tag in (getattr(w, "tags", None) or []):
            t = (tag or "").strip().lower().replace("_", " ")
            if t and t not in _GENERIC_TAGS:
                toks.add(t)
        return {t for t in toks if t}

    def _named(s: str, *, prefer_wielded: bool = False):
        s_l = s.lower()
        search_weapons = list(weapons)
        if prefer_wielded:
            wielded = set(getattr(cs, "wielded", None) or [])
            search_weapons.sort(key=lambda w: (w.id not in wielded, w.id))
        for w in search_weapons:
            if any(re.search(rf'\b{re.escape(t)}\b', s_l)
                   for t in _name_tokens(w)):
                return w
        return None

    clauses = re.split(r'\s*(?:,|\band\b|\bthen\b)\s*', intent_text or "",
                       flags=re.IGNORECASE)
    # Read each clause's verb signal once (draw/hold=draw a weapon; sheathe/stow=
    # sheathe it; attack=auto-draw the attacked-with weapon).
    clause_verbs = [
        (c, latn_resolver.intent_action_dims(
            c, ("draw", "hold", "sheathe", "stow", "attack")))
        for c in clauses
    ]
    for clause, verbs in clause_verbs:
        if verbs & {"sheathe", "stow"}:
            w = _named(clause, prefer_wielded=True)
            if w is not None:
                loadout.sheathe(cs, w, log)
        elif verbs & {"draw", "hold"}:
            w = _named(clause)
            if w is not None:
                loadout.draw(cs, w, log)
    # Auto-draw a weapon named in the attack clause ("attack with my dagger").
    for clause, verbs in clause_verbs:
        if "attack" in verbs:
            w = _named(clause)
            if w is not None and not loadout.is_wielding(cs, w):
                loadout.draw(cs, w, log)
            break


def _find_takeable_weapon_item(intent_text: str, items, actor_zone: str):
    """A loose weapon item named in the intent and within reach (same zone,
    unheld), or None. Lets "pick up the mace and attack" ground the mace even
    while the attack drives the turn through the combat resolver."""
    from engine.combat_resolver import _weapon_name_tokens
    text = (intent_text or "").lower()
    az = (actor_zone or "").upper()
    for item in (items.values() if hasattr(items, "values") else (items or [])):
        w = getattr(item, "weapon", None)
        if w is None or getattr(item, "holder", None):
            continue
        iz = (getattr(item, "zone", None) or "").upper()
        if az and iz and iz != az:
            continue
        toks = set(_weapon_name_tokens(w))
        lbl = (getattr(item, "label", "") or "").lower()
        if lbl:
            toks.add(lbl)
            toks.update(lbl.split())
        if any(re.search(rf'\b{re.escape(t)}\b', text) for t in toks if t):
            return item
    return None


def _loadout_summary(cs: "CharacterSession") -> str:
    """One-line summary of the character's weapons (and worn armor) for the
    turn prompt, so the player/LLM knows what they can attack with. Built from
    the character's structured kit; "" when there's nothing to show."""
    weapons = [w.name for w in (getattr(cs, "weapons", None) or [])
               if getattr(w, "name", "")]
    armor = getattr(cs, "armor", None)
    armor_name = getattr(armor, "name", "") if armor is not None else ""
    if not weapons and not armor_name:
        return ""
    line = ", ".join(weapons) if weapons else "(no weapons)"
    if armor_name:
        line += f" (worn: {armor_name})"
    return line


def _carried_items_summary(cs: "CharacterSession", items: Optional[dict]) -> str:
    """Non-weapon gear the character is carrying (e.g. a picked-up torch), for
    the turn prompt. Weapons are already shown by ``_loadout_summary``/WIELDING,
    so they're excluded here to avoid double-listing. Built from the character's
    inventory (item ids) resolved against the scene ``items`` registry for
    labels; falls back to the prettified id when an item isn't in the registry.
    Returns "" when there's nothing to show."""
    inv = getattr(getattr(cs, "character", None), "inventory", None) or []
    if not inv:
        return ""
    labels: list[str] = []
    for iid in inv:
        it = items.get(iid) if items else None
        if it is not None and getattr(it, "weapon", None) is not None:
            continue  # weapons are shown under CARRYING (weapons)/WIELDING
        label = (getattr(it, "label", "") or "").strip() if it is not None else ""
        labels.append(label or str(iid).replace("_", " "))
    return ", ".join(labels)


def _render_transport_prompt(
    *,
    context: RoleContext,
    cs: CharacterSession,
    raw_history: str = "",
    actor_pos: Optional[tuple] = None,
    actor_z: float = 0.0,
    items: Optional[dict] = None,
    dialogue_partner: str = "",
) -> str:
    """Format the DM situation packet sent to human transport channels.

    ``actor_pos`` is the actor's current ``(x, y, zone)`` (from
    current_positions) and ``actor_z`` her floor elevation there; when given,
    the exact coordinates [x, y, z] are surfaced in the CURRENT POSITION section
    — handy for debugging movement against item/landmark coords. (Likely
    droppable once movement is solid.)
    """
    from engine.runtime_paths import current_session_id

    header = (
        f"PACKET: TURN PROMPT\n"
        f"TURN PROMPT: {context.turn}\n"
        f"SESSION: {current_session_id()}\n"
        f"CHARACTER: {context.character_id}\n"
        f"HANDLE: {cs.scene_handle or context.character_id}\n"
    )

    # A focused puzzle exchange appends a "## You are mid-sequence at a
    # mechanism" block to scene_context between presses. While the actor is
    # mid-sequence the only thing that matters is the mechanism's response to
    # their last press plus the "what do you do next?" prompt — the standing
    # scene, position, and perception were already shown on the turn's first
    # prompt and would only bury the live feedback. So when that block is
    # present we render a minimal, focused packet and nothing else.
    mechanism_block = _extract_scene_section(
        context.scene_context, "## You are mid-sequence at a mechanism"
    )
    if mechanism_block:
        mech_lines = [
            ln for ln in mechanism_block.splitlines()
            if not ln.strip().lower().startswith("## ")
        ]
        mechanism_section = "\n".join(mech_lines).strip()
        # Minimal, conversational exchange during a focused mechanism sequence:
        # no packet/turn header, no labels — just the DM's prompt, so it reads
        # like a back-and-forth rather than a turn packet.
        return mechanism_section + "\n"

    if dialogue_partner:
        # The NPC's immediate reply was just delivered as the preceding live
        # message. Do not bury it beneath a repeated turn packet while this is
        # still a private adjacency-pair conversation.
        return (
            f"Reply to {dialogue_partner} in quotes, or enter an unquoted "
            "action to leave the conversation.\n"
        )

    perception = context.perception.strip() if context.perception else "No other creatures are visible."
    delta = _render_transport_scene_delta(
        scene_context=context.scene_context,
        turn=context.turn,
        raw_history=raw_history,
        cs=cs,
    )
    recent_section = _strip_recent_prefix(delta)
    recent_section = _humanize_recent_context(recent_section)
    zone_brief, current_position = _orientation_for_transport(context.scene_context)
    scene_intro = _scene_intro_for_transport(context.scene_context, raw_history)

    # Section order for human channels:
    #   SCENE            — description of the current zone
    #   RECENT CONTEXT   — what changed since last turn (omitted if empty)
    #   CURRENT POSITION — where you are and where you can travel
    #   PERCEPTION       — who/what you can see
    # On turn 1 SCENE is the full scene intro; later turns use the brief
    # zone line. Actions by earlier-initiative characters this turn appear
    # under RECENT CONTEXT, never folded into SCENE.
    if context.turn <= 1:
        scene_section = scene_intro or zone_brief or "(no scene description available)"
    else:
        scene_section = zone_brief or scene_intro or "(your surroundings are unchanged)"

    parts = [header]
    parts.append(f"SCENE\n{scene_section}")
    if recent_section.strip():
        parts.append(f"RECENT CONTEXT\n{recent_section}")
    # Exact coordinates [x, y, z] + zone, so movement can be checked against
    # item/landmark coords. z is the actor's floor elevation (sloped passages
    # and lower chambers read negative).
    coord_line = ""
    if actor_pos is not None and len(actor_pos) >= 2:
        zone = actor_pos[2] if len(actor_pos) > 2 and isinstance(actor_pos[2], str) else ""
        # Current HP appended so the player can track damage each turn.
        hp_suffix = ""
        if getattr(cs.character, "hp", None) is not None:
            _maxhp = cs.character.hp
            _curhp = getattr(cs.character, "current_hp", _maxhp)
            hp_suffix = f" with {_curhp}/{_maxhp} HP"
        ac_suffix = ""
        if getattr(cs.character, "ac", None) is not None:
            ac_suffix = f", AC {int(cs.character.ac)}"
        coord_line = (
            f"You are at [{float(actor_pos[0]):.1f}, {float(actor_pos[1]):.1f}, {actor_z:.1f}]"
            + (f" in {zone}" if zone else "")
            + hp_suffix
            + ac_suffix
        )
    if current_position.strip() or coord_line:
        body = "\n".join(p for p in (coord_line, current_position.strip()) if p)
        parts.append(f"CURRENT POSITION\n{body}")
    loadout = _loadout_summary(cs)
    gear = _carried_items_summary(cs, items)
    carry_body = "\n".join(p for p in (loadout, gear) if p)
    if carry_body:
        parts.append(f"CARRYING\n{carry_body}")
    from engine.loadout import (
        wielded_weapons as _wielded_weapons,
        hands_free as _hands_free,
        held_items as _held_items,
    )
    in_hand = [w.name for w in _wielded_weapons(cs)]
    # Non-weapon items held in-hand (e.g. a torch) share the WIELDING line so the
    # player sees everything currently occupying their hands.
    for _hid in _held_items(cs):
        _hit = items.get(_hid) if items else None
        _hlabel = (getattr(_hit, "label", "") or "").strip() if _hit else ""
        in_hand.append(_hlabel or str(_hid).replace("_", " "))
    if in_hand:
        free = _hands_free(cs)
        parts.append(
            f"WIELDING\n{', '.join(in_hand)} "
            f"({free} hand{'s' if free != 1 else ''} free)"
        )
    parts.append(f"PERCEPTION\n{perception}")
    parts.append("Reply with your intent for this turn in plain text, and put what you say in quotes.")
    return "\n\n".join(parts) + "\n"


def _history_lines_dedup(raw_history: str) -> list[str]:
    """Normalize raw history to a de-duplicated line list."""
    history_lines = [ln.rstrip() for ln in (raw_history or "").splitlines() if ln.strip()]
    deduped_history: list[str] = []
    last_norm = ""
    for ln in history_lines:
        norm = " ".join(ln.strip().lower().split())
        if norm == last_norm:
            continue
        deduped_history.append(ln)
        last_norm = norm
    return deduped_history


def _extract_scene_section(scene_context: str, heading: str) -> str:
    """Return the block of ``scene_context`` under a markdown ``## heading``.

    Matches case-insensitively. The block runs from the heading line up to
    (but not including) the next ``## `` heading or end of text. Returns ""
    if the heading is not present.
    """
    raw = (scene_context or "")
    lines = raw.splitlines()
    target = heading.strip().lower()
    out: list[str] = []
    capturing = False
    for ln in lines:
        lowered = ln.strip().lower()
        if lowered.startswith("## "):
            if capturing:
                break
            capturing = lowered.startswith(target)
            if capturing:
                out.append(ln.rstrip())
            continue
        if capturing and ln.strip():
            out.append(ln.rstrip())
    return "\n".join(out).strip()


def _strip_recent_prefix(text: str) -> str:
    """Drop a leading ``Recent context...`` label line from a delta block."""
    lines = (text or "").splitlines()
    if lines and lines[0].strip().lower().startswith("recent context"):
        return "\n".join(lines[1:]).strip()
    return (text or "").strip()


_TRANSPORT_SAYS_RE = re.compile(r"^(?P<who>.+?) says: (?P<rest>.+)$")
_TRANSPORT_ACTS_RE = re.compile(r"^(?P<who>.+?) acts: (?P<rest>.+)$")
# A bare fallback utterance, e.g. ``gilthaness "do you have any bolts?".`` —
# a single id token followed only by a quoted line (optional trailing period).
_BARE_UTTERANCE_RE = re.compile(r'^(?P<who>\S+)\s+"(?P<quote>.+)"\.?\s*$')


def _tidy_bare_utterance(line: str) -> str:
    """Reformat a bare ``<id> "quote".`` fallback line to ``Name: "quote"``.

    The narrator's no-LLM fallback renders a spoken action as
    ``{character_id} "{spoken}".`` — an un-capitalized id with a trailing
    period and no attribution colon. For the human RECENT CONTEXT we title-case
    the id and give it a colon so it reads like the other dialogue lines.
    Non-matching prose (a full narration sentence) is returned unchanged.
    """
    m = _BARE_UTTERANCE_RE.match(line)
    if not m:
        return line
    who = " ".join(
        w[:1].upper() + w[1:] for w in m.group("who").replace("_", " ").split()
    )
    return f'{who}: "{m.group("quote")}"'



def _humanize_recent_context(text: str) -> str:
    """Collapse the raw says/acts/prose history triple into one readable line
    per beat for the human RECENT CONTEXT.

    ``raw_history`` records each contribution as up to three lines — a raw
    ``{handle} says: "…"`` quote, a first-person ``{handle} acts: …`` intent,
    and a polished third-person prose narration that already restates both.
    Showing all three to a human reader is noisy and repetitive, so here we keep
    only the polished prose when present, falling back to the spoken quote (then
    the action) when there is no prose. Bare ``[MOVEMENT] …`` debug lines are
    dropped — position is shown separately under CURRENT POSITION and on the
    map. This touches only the human-facing packet; NPC prompts read the raw
    history unchanged.
    """
    speaker: Optional[str] = None
    says_line: Optional[str] = None
    acts_line: Optional[str] = None
    prose_line: Optional[str] = None
    out: list[str] = []

    def flush() -> None:
        nonlocal speaker, says_line, acts_line, prose_line
        if prose_line is not None:
            out.append(prose_line)
        elif says_line is not None:
            out.append(says_line)
        elif acts_line is not None:
            out.append(acts_line)
        speaker = says_line = acts_line = prose_line = None

    for raw in (text or "").splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("[MOVEMENT]"):
            continue
        ms = _TRANSPORT_SAYS_RE.match(line)
        ma = _TRANSPORT_ACTS_RE.match(line)
        if ms:
            if speaker is not None or says_line or acts_line or prose_line:
                flush()
            speaker = ms.group("who")
            says_line = line
        elif ma:
            who = ma.group("who")
            if speaker is None:
                speaker = who
                acts_line = line
            elif who == speaker and acts_line is None and prose_line is None:
                acts_line = line
            else:
                flush()
                speaker = who
                acts_line = line
        else:
            # Prose narration (or a plain history line): it ends the beat and,
            # when present, is the single line we keep for that beat. A bare
            # ``<id> "quote".`` fallback is tidied to ``Name: "quote"``.
            prose_line = _tidy_bare_utterance(line)
            flush()

    flush()
    return "\n".join(out)


def _scene_intro_for_transport(scene_context: str, raw_history: str) -> str:
    """Extract the static scene-intro prose from ``scene_context``.

    ``scene_context`` is assembled as ``initial_scene`` + running history +
    a series of ``## ...`` engine sections (memory, events, orientation,
    puzzle pressure). For the human SCENE block we want only the intro
    narrative, so we drop any line that also appears in ``raw_history`` and
    everything from the first ``## `` heading onward.
    """
    hist: set[str] = set()
    for ln in (raw_history or "").splitlines():
        s = ln.strip()
        if s:
            hist.add(" ".join(s.lower().split()))
    out: list[str] = []
    for ln in (scene_context or "").splitlines():
        s = ln.strip()
        if s.startswith("## "):
            break  # sections live at the tail; intro is everything before
        if not s:
            continue
        if " ".join(s.lower().split()) in hist:
            continue
        out.append(ln.rstrip())
    # Cap the intro so a long opening narration does not flood the packet.
    out = out[:24]
    while out and len("\n".join(out)) > 1800:
        out = out[:-1]
    return "\n".join(out).strip()


def _orientation_for_transport(scene_context: str) -> tuple[str, str]:
    """Split the orientation block into (zone_brief, current_position).

    ``zone_brief`` is the lead sentence naming the current zone (rendered
    under SCENE). ``current_position`` is the movement guidance plus the
    landmark list (rendered under CURRENT POSITION). For human channels the
    landmark coordinates are dropped and names are humanized, since the
    player travels by naming a destination rather than typing coordinates.
    """
    block = _extract_scene_section(scene_context, "## Where you are and where you can go")
    if not block:
        return "", ""
    lines = [ln for ln in block.splitlines() if not ln.strip().lower().startswith("## ")]
    zone_brief = ""
    intro_rest = ""
    list_lines: list[str] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("- "):
            # Strip "x=.., y=.." coordinates and humanize the landmark name.
            t = re.sub(
                r"^(\s*-\s+)(.+?):\s*x=-?\d+(?:\.\d+)?,\s*y=-?\d+(?:\.\d+)?\s*",
                lambda m: m.group(1) + m.group(2).replace("_", " ") + " ",
                ln,
            )
            list_lines.append(t.rstrip())
        elif not zone_brief:
            head, sep, rest = s.partition(". ")
            if sep:
                zone_brief = head.strip() + "."
                intro_rest = rest.strip()
            else:
                zone_brief = s
    intro_rest = intro_rest.replace(
        "use their coordinates in MOVEMENT to travel",
        "use their names to travel",
    )
    cp_parts: list[str] = []
    # Repeat the zone line so CURRENT POSITION is self-contained — the
    # player should not have to scroll back to SCENE to recall where they are.
    if zone_brief:
        cp_parts.append(zone_brief)
    if intro_rest:
        cp_parts.append(intro_rest)
    cp_parts.extend(list_lines)
    return zone_brief, "\n".join(cp_parts).strip()


def _render_transport_scene_delta(
    *,
    scene_context: str,
    turn: int,
    raw_history: str,
    cs: CharacterSession,
) -> str:
    """Render the running-history delta for transport prompts.

    Returns only the dialogue/narration lines this player has not yet seen
    (everything past their per-player cursor). On turn 1 the cursor starts
    at 0, so actions taken by earlier-initiative characters this turn are
    surfaced as recent context rather than swallowed. Returns "" when there
    is nothing new.
    """
    history_lines = _history_lines_dedup(raw_history)
    start = max(0, min(cs.transport_history_cursor, len(history_lines)))
    delta = history_lines[start:]
    cs.transport_history_cursor = len(history_lines)

    if not delta:
        return ""
    return "Recent context (since your last turn):\n" + "\n".join(delta)


def _intent_from_transport_text(
    *,
    character_id: str,
    turn: int,
    text: str,
) -> ActionIntent:
    """Convert a human utterance into a minimal ActionIntent."""
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        cleaned = "Hold position and observe surroundings."
    return ActionIntent(
        character_id=character_id,
        turn=turn,
        intent=cleaned,
        movement_target=None,
        interaction_target=None,
    )


def _split_transport_utterance(text: str) -> tuple[str, str]:
    """Split human transport text into (spoken, action) components.

    Conventions supported:
    - ``*...*`` marks nonverbal/action text.
    - Quoted text (straight or curly quotes) marks spoken dialogue.
    - Unquoted text is treated as action by default (asterisks optional).
    """
    raw = (text or "").strip()
    if not raw:
        return "", ""

    action_parts = [m.group(1).strip() for m in re.finditer(r"\*([^*]+)\*", raw) if m.group(1).strip()]
    without_star = re.sub(r"\*[^*]+\*", " ", raw)

    # Accept straight/curly quote pairs interchangeably. Human chat input often
    # autocorrects only one side of a pair.
    quoted_parts: list[str] = []
    for m in re.finditer(r'["“]([^"”]+)["”]', without_star):
        q = (m.group(1) or "").strip()
        if q:
            quoted_parts.append(q)
    without_quotes = re.sub(r'["“][^"”]+["”]', " ", without_star)

    # An unmatched opening quote still expresses a clear mode switch: the rest
    # of the submitted line is dialogue. Treating it as an action is both less
    # useful and contrary to what the opening delimiter tells us.
    unmatched_open = re.search(r'["“]', without_quotes)
    if unmatched_open is not None:
        q = without_quotes[unmatched_open.end():].strip()
        if q:
            quoted_parts.append(q)
        without_quotes = without_quotes[:unmatched_open.start()]

    remainder = " ".join(without_quotes.split()).strip()
    action = " ".join(action_parts).strip()

    if quoted_parts:
        spoken = " ".join(quoted_parts).strip()
        if remainder:
            action = f"{action} {remainder}".strip() if action else remainder
        return spoken, action

    # No explicit quotes: treat unstarred remainder as action by default.
    if remainder:
        action = f"{action} {remainder}".strip() if action else remainder
    return "", action


def _clean_spoken_output(text: str) -> str:
    """Remove model sentinel text that explicitly means no dialogue."""
    spoken = (text or "").strip()
    low = spoken.lower().strip("*_ ")
    if low in {"", "(none)", "(silent)", "(silence)"}:
        return ""
    if "no spoken dialogue" in low:
        return ""
    return spoken


async def _transport_send(character_id: str, cs: "CharacterSession", text: str) -> None:
    """Send out-of-turn text to a human player over Telegram, if configured.

    No-op for non-telegram actors or when the player's bot isn't configured.
    Bot API call runs in a worker thread so it never blocks the event loop.
    """
    if (cs.player_transport or "").strip().lower() != "telegram":
        return
    from engine import telegram_transport
    tt = telegram_transport.for_character(character_id)
    if tt is None:
        return
    if not await asyncio.to_thread(tt.send, text):
        _dbg(f"[TRANSPORT] failed to send broadcast to {character_id}")


_WH_WORDS = (
    "what", "where", "who", "whom", "whose", "why", "when", "which", "how",
)


def _looks_like_question(text: str) -> bool:
    """Heuristic: a player line is a question for the DM (not an action intent)
    when it ends with '?' or opens with a wh-word. A deliberate string seam so
    LATN's wh-question parse can replace it later."""
    t = (text or "").strip()
    if not t:
        return False
    if len(t) >= 2 and t[0] in {'"', '“'} and t[-1] in {'"', '”'}:
        t = t[1:-1].strip()
    if t.endswith("?"):
        return True
    first = t.lower().split()[0].strip(",.!:;\"'“”")
    return first in _WH_WORDS


def _is_explicit_spoken_utterance(text: str) -> bool:
    """True when transport input contains player-authored quoted dialogue."""
    spoken, _action = _split_transport_utterance(text)
    return bool(spoken.strip())


def _visible_social_ids(
    speaker_id: str,
    *,
    scene_geometry: Optional[SceneGeometry],
    current_positions: dict[str, tuple[float, float, str]],
    active_characters: set[str],
) -> set[str]:
    """Character ids the speaker can address in an immediate exchange."""
    speaker = current_positions.get(speaker_id)
    if speaker is None:
        return set()
    out: set[str] = set()
    for cid, pos in current_positions.items():
        if cid == speaker_id or cid not in active_characters:
            continue
        if scene_geometry is None:
            if (pos[2] or "").upper() == (speaker[2] or "").upper():
                out.add(cid)
            continue
        if scene_geometry.can_see(
            Position(speaker[0], speaker[1]), Position(pos[0], pos[1])
        ):
            out.add(cid)
    return out


def _spell_help(text: str, cs: CharacterSession) -> Optional[str]:
    """Answer generic spell prompts without consuming a turn.

    A bare ``spell`` / ``cast a spell`` cannot identify one spell to cast.
    Return the truthful engine-supported subset for this character, including
    remaining slots, instead of sending the ambiguity to the LLM.
    """
    normalized = re.sub(r"[^a-z ]+", " ", (text or "").lower())
    normalized = " ".join(normalized.split())
    help_forms = {
        "spell", "spells", "cast spell", "cast a spell",
        "what spell can i cast", "what spells can i cast",
        "which spell can i cast", "which spells can i cast",
    }
    if normalized not in help_forms:
        return None
    from engine.spell_resolver import supported_spells_for
    spells = supported_spells_for(cs.character)
    if not spells:
        return "You have no spells that the Python spell resolver currently supports."
    profile = getattr(cs.character, "spellcasting", None)
    slot_bits = []
    if profile is not None:
        for level in sorted(profile.spell_slots_max):
            maximum = profile.spell_slots_max[level]
            remaining = maximum - profile.spell_slots_used.get(level, 0)
            slot_bits.append(f"level {level}: {remaining}/{maximum}")
    slots = "; ".join(slot_bits)
    tail = f" Remaining slots: {slots}." if slots else ""
    return "Engine-supported spells you can cast: " + ", ".join(spells) + "." + tail


async def _dm_answer(turn_cycle: TurnCycle, context: RoleContext, question: str) -> str:
    """Answer a human player's question to the DM, bounded to what their
    character can currently perceive. Reuses the character's own LLM provider;
    returns a short fallback when no model is configured (stub mode)."""
    call_llm = turn_cycle._roles_for(context.character_id).player_left._call_llm
    if call_llm is None:
        return "(The DM is silent — no model is configured to answer.)"
    system = (
        "You are the Dungeon Master answering a player's question. Answer "
        "briefly, using ONLY what the player's character can currently perceive "
        "(their perception and the scene below). Do not reveal hidden "
        "information, do not invent facts, and do not take actions or advance "
        "the story for them. If the character could not know, say so."
    )
    user = (
        f"Scene:\n{context.scene_context}\n\n"
        f"What {context.character_id} can perceive:\n{context.perception}\n\n"
        f"Player asks: {question}"
    )
    try:
        raw = await call_llm(system, user)
    except Exception as e:  # noqa: BLE001 - keep the dialog alive on LLM error
        _dbg(f"[TRANSPORT] DM answer failed for {context.character_id}: {e}")
        return "(The DM doesn't respond just now.)"
    return (raw or "").strip() or "(The DM has no answer.)"


async def _player_roles_via_transport(
    *,
    turn_cycle: TurnCycle,
    context: RoleContext,
    cs: CharacterSession,
    raw_history: str = "",
    actor_pos: Optional[tuple] = None,
    actor_z: float = 0.0,
    items: Optional[dict] = None,
    current_positions: Optional[dict] = None,
    answer_query=None,
    dialogue_partner: str = "",
) -> tuple[ActionIntent, CharacterOutput]:
    """Run player roles using transport-backed human input when configured.

    Supports two human transports — Telegram (long-poll over the Bot API) and
    the in-process web transport (asyncio queues). They differ only in how a
    line is sent/received; the prompt, the wh-question -> DM dialog, and the
    intent conversion are shared. Non-transport actors fall back to the LLM.
    """
    transport = (cs.player_transport or "llm").strip().lower()

    if transport == "telegram":
        from engine import telegram_transport
        tt = telegram_transport.for_character(context.character_id)
        if tt is None:
            raise RuntimeError(
                f"Telegram transport for {context.character_id} requires "
                f"BOT_TOKEN_{context.character_id.upper()} and "
                f"CHAT_ID_{context.character_id.upper()} (or bare BOT_TOKEN/CHAT_ID) "
                f"in the environment."
            )
        # Discard anything received before this prompt (accept-after cutoff).
        # Bot API calls run in a worker thread so the long-poll never blocks.
        await asyncio.to_thread(tt.flush)

        async def _send(text: str) -> None:
            await asyncio.to_thread(tt.send, text)

        async def _recv() -> str:
            return (await asyncio.to_thread(tt.poll_once) or "").strip()
    elif transport == "web":
        from engine import web_transport
        wt = web_transport.for_character(context.character_id)
        # Discard anything received before this prompt (accept-after cutoff): the
        # web UI only enables its input on our turn, but drop stray/duplicate
        # out-of-turn POSTs so receive() reads this turn's reply, not a stale one.
        web_transport.flush_inbound(context.character_id)
        # It's this player's turn now — the browser enables its input line off
        # this flag (steady state, so a page reload re-derives it correctly).
        web_transport.set_awaiting(context.character_id, True)
        # Publish live positions (incl. NPCs who already acted THIS turn) so the
        # web map shows where everyone is now while the human decides, instead of
        # lagging a turn behind the end-of-turn checkpoints.
        if current_positions is not None:
            web_transport.publish_positions(current_positions)

        async def _send(text: str) -> None:
            await wt.send(text)

        async def _recv() -> str:
            return (await wt.receive() or "").strip()
    else:
        return await turn_cycle.player_roles(context)

    prompt_text = _render_transport_prompt(
        context=context, cs=cs, raw_history=raw_history,
        actor_pos=actor_pos, actor_z=actor_z, items=items,
        dialogue_partner=dialogue_partner)
    await _send(prompt_text)
    _dbg(f"[TRANSPORT] sent turn {context.turn} prompt to "
         f"{context.character_id} via {transport}")

    while True:
        inbound = await _recv()
        if not inbound:
            # Telegram's poll_once long-polls (~30s) then returns empty; web's
            # receive blocks until input. Either way, loop for the next line.
            continue
        if re.match(r"^\s*/goto\b", inbound, re.IGNORECASE):
            debug_target = _resolve_debug_travel_place(inbound)
            if not debug_target:
                await _send(
                    "Debug travel destination is unknown or ambiguous. Use a "
                    "unique authored place name, such as /goto graveyard, "
                    "/goto living loft, or /goto storage room."
                )
                continue
            intent = _intent_from_transport_text(
                character_id=context.character_id,
                turn=context.turn,
                text=inbound,
            )
            output = CharacterOutput(
                character_id=context.character_id,
                turn=context.turn,
                spoken="",
                action=(
                    "Uses the developer travel back door to jump to "
                    f"{Path(debug_target).name.replace('_', ' ')}."
                ),
            )
            if transport == "web":
                web_transport.set_awaiting(context.character_id, False)
            return intent, output
        spell_help = _spell_help(inbound, cs)
        if spell_help is not None:
            await _send(spell_help)
            continue
        # Let LATN answer the question first (cheap; returns None for a
        # non-question). The parallel SQ pass grounds shop-catalog questions --
        # "are your bolts for sale?", "what do you have for sale?" -- and the
        # engine answers them directly, no '?' or wh-word required and no LLM.
        # Only a question LATN can't answer falls to the DM (annotated); a
        # non-question returns None here and drops to the action resolver below.
        grounded_answer = answer_query(inbound) if answer_query is not None else None
        if grounded_answer is not None:
            await _send(grounded_answer)
            continue
        # A question goes to the DM, not the action resolver: answer it and keep
        # the dialog open (no cap) until the player states an actual intent.
        if (_looks_like_question(inbound)
                and not _is_explicit_spoken_utterance(inbound)):
            answer = await _dm_answer(turn_cycle, context, inbound)
            # Flag DM/LLM involvement: these questions are answered by the model,
            # not LATN+the engine, so the player can see where the parser hasn't
            # taken over yet (and where the answer may be improvised).
            await _send(f"🎲 DM (LLM — not yet parsed by LATN): {answer}")
            continue
        intent = _intent_from_transport_text(
            character_id=context.character_id,
            turn=context.turn,
            text=inbound,
        )
        output = await turn_cycle.player_right_from_intent(context, intent)
        spoken_text, action_text = _split_transport_utterance(inbound)
        # The human player's words are authoritative: only speak what they
        # actually quoted. Never let the model invent dialogue for a human.
        output.spoken = spoken_text or ""
        # The transport parser, not Player-Right, owns a human's action text.
        # In particular, speech-only input must clear any action the model
        # inferred from the same words.
        output.action = action_text or ""
        if transport == "web":
            # Turn consumed — the browser will disable its input until the next
            # prompt (and this clears the reload-safe flag on the server too).
            web_transport.set_awaiting(context.character_id, False)
        return intent, output


def _render_turn_result_packet(
    *,
    player_id: str,
    turn_result: TurnResult,
    characters: dict[str, CharacterSession],
    current_positions: Optional[dict[str, tuple[float, float, str]]] = None,
) -> str:
    """Render a concise post-turn update for human transport channels."""
    from engine.runtime_paths import current_session_id

    positions = current_positions or {}

    def _location_line(char_id: str) -> Optional[str]:
        pos = positions.get(char_id)
        if not pos:
            return None
        _x, _y, zone = pos
        zone_label = (zone or "").strip() or "unknown area"
        return f"Location: {zone_label}"

    lines: list[str] = [
        "PACKET: TURN RESULT",
        f"TURN RESULT: {turn_result.turn}",
        f"SESSION: {current_session_id()}",
        f"FOR: {player_id}",
        "",
    ]

    for cr in turn_result.character_results:
        cs = characters.get(cr.character_id)
        handle = cs.scene_handle if cs and cs.scene_handle else cr.character_id

        if cr.character_id == player_id:
            lines.append("[you]")
            loc = _location_line(cr.character_id)
            if loc:
                lines.append(loc)
            spoken = (cr.output.spoken or "").strip()
            action = (cr.output.action or "").strip()
            if spoken and spoken.lower() not in {"(silent)", "(silence)"}:
                lines.append(f"Spoken: {spoken}")
            if action:
                lines.append(f"Action: {action}")
            if cr.narration.prose:
                lines.append(f"Outcome: {_truncate_for_transport(cr.narration.prose.strip(), 420)}")
            lines.append("")
            continue

        lines.append(f"[{handle}]")
        loc = _location_line(cr.character_id)
        if loc:
            lines.append(loc)
        if cr.output.spoken and cr.output.spoken.strip().lower() not in {"", "(silent)", "(silence)"}:
            lines.append(f"Spoken: {cr.output.spoken.strip()}")
        elif cr.narration.prose:
            lines.append(f"Outcome: {_truncate_for_transport(cr.narration.prose.strip(), 420)}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _truncate_for_transport(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


async def _broadcast_turn_results_to_transports(
    *,
    turn_result: TurnResult,
    characters: dict[str, CharacterSession],
    current_positions: Optional[dict[str, tuple[float, float, str]]] = None,
) -> None:
    """Send post-turn updates to all configured Telegram players."""
    for char_id, cs in characters.items():
        if (cs.player_transport or "").strip().lower() != "telegram":
            continue
        packet = _render_turn_result_packet(
            player_id=char_id,
            turn_result=turn_result,
            characters=characters,
            current_positions=current_positions,
        )
        await _transport_send(char_id, cs, packet)


def _render_puzzle_press_packet(
    *,
    character_id: str,
    turn_num: int,
    label: str,
    response: str,
    solved: bool,
) -> str:
    """Render a single puzzle press's outcome for human transport channels.

    Minimal/conversational: no packet header — just what happened, so a focused
    mechanism exchange reads like a dialog with the DM."""
    lines = [
        f"You pressed {label}.",
        response.strip(),
    ]
    if solved:
        lines.append("")
        lines.append("The sequence is complete.")
    return "\n".join(lines).strip() + "\n"


async def _emit_puzzle_press_result(
    *,
    cs: CharacterSession,
    character_id: str,
    turn_num: int,
    label: str,
    response: str,
    solved: bool,
) -> None:
    """Emit one puzzle press's outcome to a human transport channel.

    Gives real-time, per-press feedback during a focused puzzle exchange so a
    transport player sees the mechanism respond to each press as it happens —
    including the terminal solve/reset/reverse press, which ends the exchange
    with no follow-up prompt and would otherwise never be surfaced. No-op for
    non-transport (LLM) actors and when there is nothing to report.
    """
    if (cs.player_transport or "").strip().lower() != "telegram":
        return
    if not (response or "").strip():
        return
    packet = _render_puzzle_press_packet(
        character_id=character_id,
        turn_num=turn_num,
        label=label,
        response=response,
        solved=solved,
    )
    await _transport_send(character_id, cs, packet)


def _render_session_complete_packet(
    *,
    completed_turns: int,
) -> str:
    """Render a compact closeout message for human transport channels."""
    from engine.runtime_paths import current_session_id

    return (
        f"PACKET: SESSION COMPLETE\n"
        f"SESSION COMPLETE\n"
        f"SESSION: {current_session_id()}\n"
        f"TURNS: {completed_turns}\n"
        f"Status: run finished. Dialogue channel is now closed for this session.\n"
    )


async def _broadcast_session_complete_to_transports(
    *,
    completed_turns: int,
    characters: dict[str, CharacterSession],
) -> None:
    """Send a final closeout packet to all configured Telegram players."""
    packet = _render_session_complete_packet(completed_turns=completed_turns)
    for char_id, cs in characters.items():
        if (cs.player_transport or "").strip().lower() != "telegram":
            continue
        await _transport_send(char_id, cs, packet)


def _has_telegram_transport(characters: dict[str, CharacterSession]) -> bool:
    return any(
        (cs.player_transport or "").strip().lower() == "telegram"
        for cs in characters.values()
    )


TRANSPORT_SETTLE_SECONDS = 3.0


# ---------------------------------------------------------------------------
# Session runner
# ---------------------------------------------------------------------------

async def iter_session(
    characters: dict[str, CharacterSession],
    character_roles: dict[str, RoleSet],
    num_turns: int,
    *,
    game_state_summary: str = "",
    geometry_summary: str = "",
    checkpoint_dir: Optional[Path] = None,
    game_time: Optional[GameTime] = None,
    rng: Optional[random.Random] = None,
    start_turn: int = 1,
    initial_history: str = "",
    scene_geometry: Optional[SceneGeometry] = None,
    items: Optional[dict] = None,
    puzzles: Optional["PuzzleRegistry"] = None,
    character_pronouns: dict[str, str] | None = None,
    initial_active_characters: set[str] | None = None,
    initial_positions: Optional[dict[str, tuple[float, float, str]]] = None,
    initial_party_examination_state: Optional[dict[tuple[str, str], dict]] = None,
    initial_spell_runtime: Optional[SpellRuntimeState] = None,
    on_character_acted: "Callable[[str, int, dict, CharacterTurnResult], None] | None" = None,
    on_scene_transition: "Callable[[str, object], None] | None" = None,
) -> AsyncIterator[TurnResult]:
    """Async generator — yields one TurnResult per turn.

    Handles all per-turn state internally (scene history, combat tracking,
    condition mutations, checkpointing, clock advancement).  After each turn
    is fully processed the result is yielded so callers can interleave
    multiple independent sessions turn-by-turn.

    Use ``run_session`` for the common single-scene case.

    ``start_turn`` and ``initial_history`` support resuming a previous session:
    turn numbering begins at ``start_turn`` and characters are seeded with the
    reconstructed history from prior turns so they remember what happened.
    """
    turn_cycle = TurnCycle(character_roles=character_roles)
    scene_history = initial_history

    # Install the session RNG so every gameplay roll (dice, attacks, boundary
    # checks) draws from ONE seeded stream -- a given seed reproduces the game,
    # instead of dice reaching for the global `random` module (whose seed
    # pytest-randomly owns, which made combat-outcome tests flaky by run order).
    from engine.game_rng import use_rng
    rng = use_rng(rng)

    # (Pre-session inbox/outbox purge removed: the direct Telegram transport has
    # no files; stale messages are handled by TelegramTransport.flush() at each
    # prompt.)

    # Combat state
    in_combat = False
    pre_combat_duration: int | None = None
    spell_resolver = SpellResolver(rng=rng)
    spell_runtime = initial_spell_runtime or SpellRuntimeState()

    # Phase 3b: dormancy. Creatures with activation triggers (e.g.
    # zone_entry:Secret Chamber) are excluded from initiative and
    # perception until the trigger fires.
    from engine.activation import initial_dormant_set, check_activations
    dormant: set[str] = initial_dormant_set(characters)

    active_characters: set[str] = (
        initial_active_characters & set(characters.keys())
        if initial_active_characters is not None
        else set(characters.keys()) - dormant
    )

    story_turns_remaining = num_turns
    melee_rounds_remaining = MAX_MELEE_ROUNDS
    turn_num = start_turn

    # Live position tracking — seeded from the scene's starting positions then
    # updated each turn from DM-approved MOVEMENT TARGET.
    current_positions: dict[str, tuple[float, float, str]] = _parse_positions_table(
        game_state_summary
    )
    # Fill any missing entries from the scene-resolved starting positions
    # (carried on scene_geometry.starting_positions by the loader) so
    # speed-clamping works from Turn 1 even for characters not in the
    # game_state_summary position table.
    if scene_geometry is not None:
        for char_id in characters:
            if char_id in current_positions:
                continue
            # Exact match first, then prefix match (e.g. "shadowbeast" matches "shadowbeast_1")
            start_pos = scene_geometry.starting_positions.get(char_id)
            if start_pos is None:
                start_pos = next(
                    (p for k, p in scene_geometry.starting_positions.items()
                     if char_id.startswith(k) or k.startswith(char_id)),
                    None,
                )
            if start_pos is not None:
                zone = scene_geometry.zone_at(start_pos) or ""
                current_positions[char_id] = (start_pos.x, start_pos.y, zone.upper())

    # When resuming from a checkpoint, override positions with the last known
    # live positions so characters are placed where they actually ended up, not
    # at their starting positions in game_state_summary.
    if initial_positions:
        current_positions.update(initial_positions)

    # Drop positions for characters who are no longer active (e.g. died or
    # exited the scene in a prior run). Without this, geometry-seeded starting
    # positions would resurrect dead characters in the position table — they
    # wouldn't get initiative, but they'd appear in the DM Ledger and LLMs
    # would reference them.
    for char_id in list(current_positions.keys()):
        if char_id not in active_characters:
            current_positions.pop(char_id, None)

    # DM ledger — authoritative event log injected into every DM prompt
    ledger = DMLedger()

    # Player-facing recent events — Python-verified facts (deaths, damage,
    # boundary crossings, combat start) shown in every player's context so
    # they don't need to mine prose for state changes. Sliding window keyed
    # by turn_num.
    recent_events: deque[tuple[int, str]] = deque(maxlen=40)

    # Engine-side anti-loop memory keyed per character. Stores recent
    # search signatures as (kind, target_norm, position_bucket).
    search_history: dict[str, deque[tuple[str, str, tuple[int, int, str]]]] = {}

    # Party-shared memory of what has already been examined in each zone.
    # Key: (ZONE, normalized target label)
    # Value: {label, summary, by, last_turn, needs_followup}
    party_examination_state: dict[tuple[str, str], dict] = dict(
        initial_party_examination_state or {}
    )

    # Re-seed each item's discovered_by from the restored examination state.
    # Loose scene items are rebuilt with an empty discovered_by on resume, but
    # the checkpoint records who examined what in party_examination_state (keyed
    # by ZONE + normalized target, with the examiner id). Perception's "Items
    # remembered or examined" section reads item.discovered_by, so without this
    # re-seed that section silently empties out whenever a session is resumed.
    _reseed_discovered_from_examination_state(items, party_examination_state)

    # Phase 2: preserve explicit/restored wielded state only (no auto-draw at
    # scene start). Re-register picked-up weapons on resume and rebuild the
    # derived Thing-view used by manipulation/grounding.
    from engine.loadout import sync_held_weapons, materialize_things
    for _cs in characters.values():
        sync_held_weapons(_cs, items)  # re-register picked-up weapons on resume
        materialize_things(_cs)        # derived Thing-view of the kit for dispatch

    # Per-session puzzles. Each puzzle owns its own state machine; the loop
    # only delegates presses to the registry and applies the results. An
    # empty registry (no authored puzzles) is a harmless no-op.
    from engine.puzzles import PuzzleRegistry
    puzzle_registry: PuzzleRegistry = puzzles if puzzles is not None else PuzzleRegistry()

    # Per-character visited-zone tracking. A character is aware of named
    # landmarks/zone-centers only in zones they have entered. Seed with each
    # character's current zone so the starting chamber's contents are
    # immediately visible.
    visited_zones: dict[str, set[str]] = {}
    for _cid, _pos in current_positions.items():
        if _pos and _pos[2]:
            visited_zones.setdefault(_cid, set()).add(_pos[2].upper())
            if _cid in characters:
                characters[_cid].last_zone_seen = _pos[2].upper()

    # Party-level forward focus: when one actor successfully advances into a
    # new zone, lightly pull others there for a short window and suppress
    # immediate backtracking into already-visited zones.
    party_focus_zone: Optional[str] = None
    party_focus_until_turn: int = 0
    pending_scene_transition: tuple[str, str, tuple[float, float, str], str, str] | None = None
    from engine.social_exchange import SocialExchangeSchedule
    # Human speaker -> sole NPC partner for a compact follow-up prompt. This is
    # runtime conversation focus, not persistent world state.
    active_dialogues: dict[str, str] = {}

    while True:
        combat_at_start = in_combat
        if combat_at_start:
            if melee_rounds_remaining <= 0:
                break
        else:
            if story_turns_remaining <= 0:
                break

        # Roll initiative — only for characters still in the scene
        char_list = [
            cs.character for cid, cs in characters.items()
            if cid in active_characters
        ]
        if not char_list:
            break

        entries = roll_initiative(char_list, rng=rng)
        order = [e.character_id for e in entries]

        # Rebuild the position table with live positions for this turn
        turn_game_state = _update_positions_in_summary(game_state_summary, current_positions)

        # Execute each character in initiative order, rebuilding context
        # just-in-time so each character sees within-turn narration from
        # characters who acted earlier in the same turn.
        turn_result = TurnResult(turn=turn_num, initiative_order=order)
        within_turn_history = ""
        pending_scene_transition = None
        # Immediate dialogue consumes only a still-pending initiative slot in
        # this exploration turn. Never carry suppression into the next turn.
        social_schedule = SocialExchangeSchedule()
        acted_this_turn: set[str] = set()

        for character_id in order:
            if character_id not in active_characters:
                continue
            if social_schedule.suppress_slot(character_id, in_combat=in_combat):
                continue
            acted_this_turn.add(character_id)

            # Expire stale focus at character step granularity.
            if party_focus_zone and turn_num > party_focus_until_turn:
                party_focus_zone = None
                party_focus_until_turn = 0

            cs = characters[character_id]
            actor_pos_before_action = current_positions.get(character_id, (0.0, 0.0, ""))
            memory_count_before = len(cs.episodic_memory)
            # Snapshot the active set so we can detect deaths that happen
            # during damage application this turn.
            pre_active = set(active_characters)
            combined_history = scene_history
            if within_turn_history:
                combined_history = (
                    f"{scene_history}\n{within_turn_history}"
                    if scene_history else within_turn_history
                )

            # Filter to events from the current and the previous 2 turns —
            # enough to reflect "the beast was killed last turn" without
            # bloating context with stale combat from earlier in the scene.
            visible_events = [
                ev for (et, ev) in recent_events if et >= turn_num - 2
            ]

            context = _build_context(
                cs, turn_num, combined_history,
                scene_geometry=scene_geometry,
                current_positions=current_positions,
                active_characters=active_characters,
                in_combat=in_combat,
                characters=characters,
                recent_events=visible_events,
                visited_zones=visited_zones,
                items=items,
                puzzles=puzzle_registry,
            )

            # Steps 1-3: Player-Left → Player-Right → DM-Left
            # When in combat and the character has structured weapons, bypass
            # DM-Left and use CombatResolver for attack resolution.
            _ap = current_positions.get(character_id)
            _az = (
                scene_geometry.floor_z_at(Position(_ap[0], _ap[1]))
                if scene_geometry is not None and _ap else 0.0
            )
            # LATN-grounded answers to a player's questions (shop catalog for
            # now), so shop questions bypass the DM/LLM. Assembles the present
            # shopkeeper's goods the same way the clarify block below does;
            # returns None for non-questions and unrouted questions (which then
            # fall to the annotated DM).
            def _answer_query(text, _char_id=character_id, _cs=cs):
                try:
                    from engine.latn_integration import resolve_query as _resolve_query
                    _q_zone = (current_positions.get(_char_id, (0.0, 0.0, ""))[2] or "")
                    # 1) Identity, location, and game-clock state.
                    ans = _answer_basic_state_question(
                        text, cs=_cs, actor_zone=_q_zone,
                        scene_geometry=scene_geometry, game_time=game_time,
                        characters=characters or {}, character_id=_char_id,
                        current_positions=current_positions,
                        active_characters=active_characters)
                    if ans is not None:
                        return ans
                    # 2) Authored place knowledge.
                    ans = _answer_place_definition_question(
                        text, characters=characters or {}, actor_zone=_q_zone,
                        scene_geometry=scene_geometry,
                        player_xy=((current_positions[_char_id][0], current_positions[_char_id][1])
                                   if _char_id in current_positions else None),
                        visited_zones=visited_zones.get(_char_id, set()))
                    if ans is not None:
                        return ans
                    # 3) External perception -- engine/fog-of-war authoritative.
                    ans = _answer_perception_question(
                        text, context=context, characters=characters or {},
                        actor_zone=_q_zone, scene_geometry=scene_geometry,
                        items=items,
                        player_xy=((current_positions[_char_id][0], current_positions[_char_id][1])
                                   if _char_id in current_positions else None),
                        visited_zones=visited_zones.get(_char_id, set()),
                    )
                    if ans is not None:
                        return ans
                    _q_cat = _driftmoor_shop_catalog()
                    _q_keeper = _current_shopkeeper(characters, active_characters, _q_cat)
                    _q_entries = _q_cat.entries_for(_q_keeper) if _q_keeper else []
                    # 4) A first-person question about yourself -- "how much gold
                    # do I have", "what am I carrying", "what can I sell".
                    ans = _answer_self_question(
                        text, cs=_cs, characters=characters or {},
                        actor_zone=_q_zone, scene_geometry=scene_geometry,
                        items=items, catalog=_q_entries)
                    if ans is not None:
                        return ans
                    # 5) A shop-catalog question -- "what can I buy", "are your
                    # bolts for sale". (Purchase questions were deferred here.)
                    ans = _resolve_query(
                        text, items or {}, characters or {}, _q_zone,
                        catalog=_q_entries, scene_geometry=scene_geometry)
                    if ans is not None:
                        return ans
                    # 6) Geography: "where is <venue>?" -> bearing + distance to
                    # its door, answered by the engine instead of the DM.
                    _pos = current_positions.get(_char_id)
                    _venues = (
                        _driftmoor_child_venues(getattr(scene_geometry, "place_path", "") or "")
                        if scene_geometry is not None else ())
                    ans = _answer_venue_existence_question(
                        text, characters=characters or {}, actor_zone=_q_zone,
                        scene_geometry=scene_geometry, venues=_venues)
                    if ans is not None:
                        return ans
                    return _answer_where_question(
                        text, characters=characters or {}, actor_zone=_q_zone,
                        scene_geometry=scene_geometry, venues=_venues,
                        player_xy=((_pos[0], _pos[1]) if _pos else None))
                except Exception as e:  # noqa: BLE001 - keep the dialog alive
                    _dbg(f"[QUERY] resolve_query failed for {_char_id}: {e}")
                    return None

            _dialogue_partner_id = active_dialogues.get(character_id)
            _dialogue_partner_label = ""
            if _dialogue_partner_id:
                _dialogue_visible = _visible_social_ids(
                    character_id,
                    scene_geometry=scene_geometry,
                    current_positions=current_positions,
                    active_characters=active_characters,
                )
                if _dialogue_visible == {_dialogue_partner_id}:
                    _partner_cs = characters.get(_dialogue_partner_id)
                    if _partner_cs is not None:
                        _dialogue_partner_label = (
                            _partner_cs.scene_handle
                            or _partner_cs.character.name
                            or _dialogue_partner_id
                        )
                else:
                    active_dialogues.pop(character_id, None)

            intent, output = await _player_roles_via_transport(
                turn_cycle=turn_cycle,
                context=context,
                cs=cs,
                raw_history=combined_history,
                actor_pos=_ap,
                actor_z=_az,
                items=items,
                current_positions=current_positions,
                answer_query=_answer_query,
                dialogue_partner=_dialogue_partner_label,
            )
            # Developer commands are claimed before LATN diagnostics.  Their
            # slash-prefixed command word is intentionally not game lexicon;
            # only the authored destination is resolved by the debug grounder.
            _debug_travel_target = _resolve_debug_travel_place(
                intent.intent or ""
            )
            output.spoken = _clean_spoken_output(output.spoken)
            if not output.spoken or output.action:
                active_dialogues.pop(character_id, None)
            _social_target = None
            _social_visible_ids: set[str] = set()
            if (
                not in_combat
                and output.spoken
                and (cs.player_transport or "llm").strip().lower()
                in {"web", "telegram"}
            ):
                from engine.social_exchange import directed_social_target
                _social_visible_ids = _visible_social_ids(
                    character_id,
                    scene_geometry=scene_geometry,
                    current_positions=current_positions,
                    active_characters=active_characters,
                )
                _social_target = directed_social_target(
                    output.spoken,
                    speaker_id=character_id,
                    visible_ids=_social_visible_ids,
                    characters=characters,
                )

            # Parser honesty: when a human's line grounds to NO action, and it
            # uses words the lexicon doesn't know, the DM names them (+ near
            # spellings) and asks for a rephrase -- an in-turn sub-dialog, no LLM.
            # Gated on grounding: a line the engine can act on (even buried in
            # prose -- "I look around and ask for bolts") is acted on and
            # narrated, never interrogated. The diagnostic lexicon mirrors the
            # hooks' (scene items, characters, zones, venues, present shop goods)
            # so real words aren't flagged. Transport-backed human players only.
            _asker = _commerce_negotiator(cs, character_id)
            # Quoted human input is free-form character speech, not an engine
            # command. NPC/DM dialogue owns its interpretation, so the action
            # lexicon must never demand that spoken prose be rephrased.
            if (
                _asker is not None
                and intent.intent
                and not output.spoken
                and not _debug_travel_target
            ):
                try:
                    from engine.latn_integration import build_context as _dm_build_ctx
                    from engine.latn import use_lexicon as _dm_use_lex
                    from latn.lexer.diagnostics import diagnose as _dm_diagnose
                    _dm_zone = (current_positions.get(character_id, (0.0, 0.0, ""))[2] or "")
                    _dm_venues = (
                        list(_driftmoor_child_venues(
                            getattr(scene_geometry, "place_path", "") or ""))
                        if scene_geometry is not None else [])
                    # Preserve nouns in later clauses of a venue plan. A
                    # sibling is not enterable yet, but can become so after an
                    # earlier `leave`; lexical recognition must not discard the
                    # sentence before sequential execution gets that chance.
                    _dm_place = next((
                        node for node in _driftmoor_place_registry()
                        if node.place_path == (
                            getattr(scene_geometry, "place_path", "") or ""
                        )
                    ), None) if scene_geometry is not None else None
                    if _dm_place is not None and _dm_place.parent_place_path:
                        _dm_seen = {name for name, _aliases in _dm_venues}
                        _dm_venues.extend(
                            candidate
                            for candidate in _driftmoor_child_venues(
                                _dm_place.parent_place_path)
                            if candidate[0] not in _dm_seen
                        )
                    _dm_cat = _driftmoor_shop_catalog()
                    _dm_keeper = _current_shopkeeper(characters, active_characters, _dm_cat)
                    _dm_entries = _dm_cat.entries_for(_dm_keeper) if _dm_keeper else []
                    # items is None for an item-less scene (web_play passes
                    # `cfg.items or None`); build_context needs a dict like every
                    # other caller's `items or {}`.
                    _dm_characters = _characters_with_acquaintances(characters, cs)
                    _dm_lex, _dm_adp = _dm_build_ctx(
                        items or {}, _dm_characters, _dm_zone, scene_geometry,
                        venues=_dm_venues, catalog=_dm_entries)

                    _place_path = (
                        getattr(scene_geometry, "place_path", "") or ""
                        if scene_geometry is not None else ""
                    )
                    _venue_choices = _ambiguous_driftmoor_venues(
                        intent.intent, _place_path
                    )
                    if _venue_choices and _infer_driftmoor_venue_transition(
                        intent.intent, _place_path, _dm_zone,
                        current_positions.get(character_id),
                    ) is None:
                        _refined = await _clarify_ambiguous_venue(
                            intent.intent, ask=_asker,
                            candidates=_venue_choices,
                        )
                        if _refined and _refined != intent.intent:
                            intent.intent = _refined
                            output.action = _refined

                    if not _player_intent_grounds(
                        intent.intent, lexicon=_dm_lex, adapter=_dm_adp,
                        items=items or {}, characters=_dm_characters,
                        actor_zone=_dm_zone, entries=_dm_entries,
                    ):
                        def _dm_diag(_t, _lex=_dm_lex):
                            with _dm_use_lex(_lex):
                                diagnosed = _dm_diagnose(_t)
                            return _filter_presented_unknowns(
                                diagnosed, combined_history
                            )

                        # Record the out-of-vocabulary words so real gaps (e.g.
                        # "eat") accumulate for review and can be added to the
                        # lexicon later -- no one has to remember them mid-game.
                        _diag = _dm_diag(intent.intent)
                        if _diag:
                            from engine.unknown_word_log import log_unknown_words
                            log_unknown_words(
                                [w for w, _s in _diag],
                                intent_text=intent.intent,
                                scene=getattr(scene_geometry, "place_path", "") or "",
                                suggestions={w: s for w, s in _diag if s},
                            )

                        _refined = await _clarify_unknown_words(
                            intent.intent, ask=_asker, diagnose_fn=_dm_diag)
                        if _refined and _refined != intent.intent:
                            intent.intent = _refined
                            output.action = _refined
                except Exception as _dm_err:  # noqa: BLE001 - a nicety must never crash the turn
                    _dbg(f"[CLARIFY] skipped for {character_id}: "
                         f"{type(_dm_err).__name__}: {_dm_err}")

            loop_guard_notes: list[str] = []

            actor_zone_before = (
                current_positions.get(character_id, (None, None, ""))[2] or ""
            ).upper()

            # Shared-state guard: if the party already examined this target in
            # this zone and no follow-up is needed, redirect toward novel info.
            if (
                not in_combat
                and intent.interaction_target
                and actor_zone_before
                and _is_search_like_intent(intent.intent or "")
            ):
                shared_key = _shared_exam_key(actor_zone_before, intent.interaction_target)
                shared_exam = party_examination_state.get(shared_key) if shared_key else None
                if shared_exam and not bool(shared_exam.get("needs_followup", False)):
                    alt = _choose_novel_item_for_search(
                        character_id=character_id,
                        current_positions=current_positions,
                        items=items,
                        current_target_norm=_normalize_target_name(intent.interaction_target),
                    )
                    if alt is not None:
                        label, ix, iy, izone = alt
                        intent.interaction_target = label
                        intent.movement_target = (ix, iy, 0.0)
                        intent.intent = f"Examine {label} for new information and then advance."
                        loop_guard_notes.append(
                            f"[SHARED-EXAM] {character_id}: '{shared_exam.get('label') or intent.interaction_target}' "
                            f"already examined in {actor_zone_before}; redirected to '{label}' in {izone}."
                        )
                    else:
                        waypoint = _choose_exploration_waypoint(
                            character_id=character_id,
                            current_positions=current_positions,
                            scene_geometry=scene_geometry,
                            visited=visited_zones.get(character_id, set()),
                        )
                        if waypoint is not None:
                            w_zone, wx, wy = waypoint
                            intent.interaction_target = None
                            intent.movement_target = (wx, wy, 0.0)
                            intent.intent = _exploration_redirect_intent(
                                zone_name=w_zone,
                                known_zones=visited_zones.get(character_id, set()),
                            )
                            loop_guard_notes.append(
                                f"[SHARED-EXAM] {character_id}: prior target in {actor_zone_before} "
                                f"already settled; redirected toward {w_zone}."
                            )

            # Party-focus pull: if another character has committed to a forward
            # zone recently, bias this actor to follow unless a local unresolved
            # puzzle should keep them in place.
            if (
                not in_combat
                and party_focus_zone
                and turn_num <= party_focus_until_turn
                and _follows_party_focus(cs)
            ):
                focus_zone = party_focus_zone.upper()
                if actor_zone_before and actor_zone_before != focus_zone:
                    puzzle_live_here = _zone_has_unresolved_puzzle(
                        current_zone=actor_zone_before,
                        items=items,
                        puzzles=puzzle_registry,
                    )
                    if not puzzle_live_here:
                        focus_wp = _waypoint_for_zone(
                            character_id=character_id,
                            current_positions=current_positions,
                            scene_geometry=scene_geometry,
                            target_zone=focus_zone,
                        )
                        if focus_wp is not None:
                            fx, fy = focus_wp
                            intent.interaction_target = None
                            intent.movement_target = (fx, fy, 0.0)
                            intent.intent = _exploration_redirect_intent(
                                zone_name=focus_zone,
                                known_zones=visited_zones.get(character_id, set()),
                            )
                            loop_guard_notes.append(
                                f"[PARTY-FOCUS] {character_id}: following active "
                                f"party focus toward {focus_zone} at "
                                f"({fx:.1f},{fy:.1f})."
                            )

                # Anti-backtrack in focus zone: don't leave focus for an
                # already-visited zone while focus is active.
                elif actor_zone_before == focus_zone and intent.movement_target is not None and scene_geometry is not None:
                    tx, ty = float(intent.movement_target[0]), float(intent.movement_target[1])
                    target_zone = scene_geometry.zone_at(Position(tx, ty)) or ""
                    puzzle_live_here = _zone_has_unresolved_puzzle(
                        current_zone=actor_zone_before,
                        items=items,
                        puzzles=puzzle_registry,
                    )
                    if (
                        not puzzle_live_here
                        and _should_block_backtrack(
                            current_zone=actor_zone_before,
                            target_zone=target_zone,
                            visited=visited_zones.get(character_id, set()),
                            party_focus_zone=focus_zone,
                        )
                    ):
                        intent.movement_target = None
                        intent.interaction_target = None
                        intent.intent = "Continue investigating this area before backtracking."
                        loop_guard_notes.append(
                            f"[PARTY-FOCUS] {character_id}: blocked backtrack "
                            f"from {focus_zone} to visited zone {target_zone.upper()}."
                        )

            # Engine-side anti-loop guard: if the actor repeats the same
            # search in the same ~5 ft bucket for 3 consecutive turns,
            # retarget to a different visible item in-zone.
            if not in_combat and _is_search_like_intent(intent.intent):
                bucket = _position_bucket(current_positions.get(character_id))
                target_norm = _normalize_target_name(intent.interaction_target)
                hist = search_history.setdefault(character_id, deque(maxlen=3))
                recent_two = list(hist)[-2:]
                current_zone = (current_positions.get(character_id, (None, None, ""))[2] or "").upper()
                puzzle_live = _zone_has_unresolved_puzzle(
                    current_zone=current_zone,
                    items=items,
                    puzzles=puzzle_registry,
                )
                repeated_zone_search = (
                    len(recent_two) == 2
                    and all(kind == "search" and pb[2] == bucket[2] for kind, _, pb in recent_two)
                )
                repeated = (
                    len(recent_two) == 2
                    and all(
                        kind == "search" and tnorm == target_norm and pb == bucket
                        for kind, tnorm, pb in recent_two
                    )
                )
                if repeated:
                    alt = _choose_novel_item_for_search(
                        character_id=character_id,
                        current_positions=current_positions,
                        items=items,
                        current_target_norm=target_norm,
                    )
                    if alt is not None:
                        label, ix, iy, izone = alt
                        intent.interaction_target = label
                        intent.movement_target = (ix, iy, 0.0)
                        intent.intent = (
                            f"Examine {label} for new information and then advance."
                        )
                        loop_guard_notes.append(
                            f"[LOOP-GUARD] {character_id}: repeated search loop "
                            f"detected at {bucket}; retargeted to '{label}' "
                            f"in {izone}."
                        )
                elif repeated_zone_search and puzzle_live:
                    puzzle_focus = _choose_puzzle_focus_item(
                        character_id=character_id,
                        current_positions=current_positions,
                        items=items,
                        puzzles=puzzle_registry,
                        current_target_norm=target_norm,
                    )
                    if puzzle_focus is not None:
                        label, ix, iy, izone = puzzle_focus
                        intent.interaction_target = label
                        intent.movement_target = (ix, iy, 0.0)
                        intent.intent = (
                            f"Continue the unresolved puzzle by working on {label}."
                        )
                        loop_guard_notes.append(
                            f"[LOOP-GUARD] {character_id}: unresolved puzzle in "
                            f"{current_zone}; redirected to puzzle focus '{label}' "
                            f"in {izone}."
                        )
                elif repeated_zone_search:
                    waypoint = _choose_exploration_waypoint(
                        character_id=character_id,
                        current_positions=current_positions,
                        scene_geometry=scene_geometry,
                        visited=visited_zones.get(character_id, set()),
                    )
                    if waypoint is not None:
                        w_zone, wx, wy = waypoint
                        char_known_zones = visited_zones.get(character_id, set())
                        intent.interaction_target = None
                        intent.movement_target = (wx, wy, 0.0)
                        intent.intent = _exploration_redirect_intent(
                            zone_name=w_zone,
                            known_zones=char_known_zones,
                        )
                        examined_state = _all_zone_items_examined(
                            character_id=character_id,
                            current_positions=current_positions,
                            items=items,
                        )
                        loop_guard_notes.append(
                            f"[LOOP-GUARD] {character_id}: same-zone search churn "
                            f"detected (all_items_examined={examined_state}); "
                            f"redirected toward {w_zone} at ({wx:.1f},{wy:.1f})."
                        )
                hist.append((
                    "search",
                    _normalize_target_name(intent.interaction_target),
                    bucket,
                ))
            else:
                search_history.pop(character_id, None)

            use_resolver = (
                in_combat
                and bool(cs.weapons)
                and _intent_is_attack(intent.intent)
            )
            used_spell_resolver = False
            spell_cast_log: list[str] = []
            if (
                not use_resolver
                and _intent_is_spell(intent.intent)
                and isinstance(cs.character, Character)
            ):
                spell_name = _extract_spell_name_from_intent(intent.intent, cs)
                if spell_name:
                    targets = _resolve_spell_targets(
                        intent,
                        caster_id=character_id,
                        characters=characters,
                        active_characters=active_characters,
                    )
                    gs_ref = GameState(characters=[x.character for x in characters.values()])
                    spell_result = spell_resolver.cast(
                        gs_ref,
                        SpellCastRequest(
                            caster_id=character_id,
                            spell_name=spell_name,
                            target_ids=targets,
                        ),
                        spell_runtime,
                    )
                    if not spell_result.approved:
                        notes = spell_result.reason
                    else:
                        note_parts = [f"Spell resolved in Python: {spell_name}."]
                        if spell_result.started_effects:
                            note_parts.append(
                                "Started effect(s): " + ", ".join(spell_result.started_effects) + "."
                            )
                        if spell_result.ended_effects:
                            note_parts.append(
                                "Ended effect(s): " + ", ".join(spell_result.ended_effects) + "."
                            )
                        notes = " ".join(note_parts)
                    adjudication = Adjudication(
                        character_id=character_id,
                        turn=turn_num,
                        approved=spell_result.approved,
                        notes=notes,
                        hp_damage=dict(spell_result.hp_damage),
                    )
                    attack_log = []
                    if spell_result.approved:
                        used_spell_resolver = True
                        # Teleport: relocate the caster to a named zone/landmark/feature.
                        # The resolver consumed the slot and emitted "teleport";
                        # the session owns geometry/positions so it applies the move.
                        if "teleport" in spell_result.events:
                            dest = _resolve_teleport_destination(
                                intent.intent, scene_geometry, items
                            )
                            if dest is not None:
                                origin = current_positions.get(character_id)
                                tx, ty = float(dest[0]), float(dest[1])
                                tzone = (
                                    scene_geometry.zone_at(Position(tx, ty))
                                    if scene_geometry else dest[2]
                                ) or dest[2]
                                new_pos = (tx, ty, tzone.upper())
                                current_positions[character_id] = new_pos
                                adjudication.new_position = new_pos
                                if visited_zones is not None and tzone:
                                    visited_zones.setdefault(
                                        character_id, set()
                                    ).add(tzone.upper())
                                if origin is not None:
                                    ox, oy, oz = origin
                                    attack_log.append(
                                        f"[TELEPORT] {character_id}: "
                                        f"({ox:.1f},{oy:.1f},{oz}) → "
                                        f"({tx:.1f},{ty:.1f},{new_pos[2]})"
                                    )
                                else:
                                    attack_log.append(
                                        f"[TELEPORT] {character_id}: → "
                                        f"({tx:.1f},{ty:.1f},{new_pos[2]})"
                                    )
                                venue_arrival = _teleport_venue_arrival_fact(
                                    character_id, intent.intent, scene_geometry
                                )
                                if venue_arrival is not None:
                                    attack_log.append(venue_arrival)
                            else:
                                attack_log.append(
                                    f"[TELEPORT] {character_id}: no recognizable "
                                    f"destination in intent '{intent.intent}'; "
                                    f"spell fizzles."
                                )
                        for tid, dmg in spell_result.hp_damage.items():
                            if tid in characters:
                                tchar = characters[tid].character
                                if hasattr(tchar, "current_hp") and tchar.current_hp <= 0:
                                    active_characters.discard(tid)
                                    current_positions.pop(tid, None)
                                    attack_log.append(f"[{tid} is dead — reduced to 0 HP]")
                        for tid, heal in spell_result.hp_heal.items():
                            attack_log.append(f"[SPELL] {character_id} heals {tid} for {heal} HP")
                        if spell_result.hp_damage:
                            attack_log.append(
                                f"[SPELL] {character_id} casts {spell_name}: "
                                + ", ".join(f"{tid} takes {dmg}" for tid, dmg in spell_result.hp_damage.items())
                            )
                            if "combat_initiated" not in adjudication.spatial_events:
                                adjudication.spatial_events.append("combat_initiated")
                    else:
                        used_spell_resolver = True
                        spell_cast_log.append(f"[SPELL] {character_id} cast rejected: {spell_result.reason}")
                        attack_log.extend(spell_cast_log)
                else:
                    used_spell_resolver = True
                    adjudication = Adjudication(
                        character_id=character_id,
                        turn=turn_num,
                        approved=False,
                        notes="Spell cast rejected: unknown or unavailable spell name.",
                    )
                    attack_log = [
                        f"[SPELL] {character_id} cast rejected: unknown or unavailable spell name"
                    ]
            if use_resolver:
                # Find best target: interaction_target hint first, then nearest hostile
                target_id = _find_combat_target(
                    intent, character_id, characters, current_positions,
                    active_characters,
                )
                if target_id and target_id in characters:
                    # Conjoined "pick up <weapon> and attack": do the pickup now
                    # (the take path is otherwise gated to non-attack turns), so
                    # the just-grabbed weapon is wielded and used this swing.
                    _pickup_log: list[str] = []
                    _preferred_weapon = None
                    from engine.verb_resolver import (
                        detect_transfer_verb, authored_transfer_response,
                    )
                    if detect_transfer_verb(intent.intent or "") == "take":
                        _wi = _find_takeable_weapon_item(
                            intent.intent or "", items, actor_zone)
                        if _wi is not None:
                            _handle_item_transfer(
                                transfer_verb="take", item_obj=_wi,
                                label=_wi.label or _wi.id,
                                character_id=character_id, characters=characters,
                                active_characters=active_characters,
                                current_positions=current_positions,
                                intent_text=intent.intent or "",
                                actor_zone=actor_zone, turn_num=turn_num,
                                game_time=game_time, attack_log=_pickup_log,
                                recent_events=recent_events, cs=cs,
                                authored_response=authored_transfer_response(
                                    _wi, "take"),
                                recipient_override=None,
                            )
                            _preferred_weapon = next(
                                (w for w in cs.weapons if w.id == _wi.id), None)
                    # Apply any draw/sheathe the actor declared this turn and
                    # auto-draw the weapon they're attacking with, so the
                    # resolver swings the right thing.
                    _loadout_log: list[str] = []
                    _apply_loadout_intent(intent.intent, cs, _loadout_log)
                    resolver = CombatResolver()
                    attack_disadvantage = _has_vicious_mockery_disadvantage(
                        spell_runtime, character_id
                    )
                    adjudication, attack_log = resolver.resolve(
                        character_id=character_id,
                        turn=turn_num,
                        attacker_session=cs,
                        target_id=target_id,
                        target_session=characters[target_id],
                        attacker_pos=current_positions.get(character_id, (0.0, 0.0, "")),
                        target_pos=current_positions.get(target_id, (0.0, 0.0, "")),
                        scene_geometry=scene_geometry,
                        game_time=game_time,
                        intent_text=intent.intent,
                        attack_disadvantage=attack_disadvantage,
                        preferred_weapon=_preferred_weapon,
                    )
                    # Narrate the pickup, then the draw/sheathe, before the swing.
                    if _loadout_log:
                        attack_log[:0] = [f"[LOADOUT] {character_id}: "
                                          + ", ".join(_loadout_log)]
                    if _pickup_log:
                        attack_log[:0] = _pickup_log
                    if attack_disadvantage and _consume_vicious_mockery_disadvantage(
                        spell_runtime, character_id
                    ):
                        attack_log.append(
                            f"[SPELL] {character_id} consumed Vicious Mockery disadvantage on this attack"
                        )
                    # Apply movement from resolver — enforce boundary crossing
                    if adjudication.new_position:
                        resolver_origin = current_positions.get(character_id)
                        resolver_new = _clamp_to_authored_home(
                            character_id,
                            adjudication.new_position,
                            characters[character_id].character,
                            scene_geometry,
                        )
                        adjudication.new_position = resolver_new
                        boundary_ok = True
                        if (
                            scene_geometry is not None
                            and scene_geometry.boundaries
                            and resolver_origin is not None
                        ):
                            boundary_ok, crossing_dmg, b_log, stop_at = _check_boundary_crossing(
                                character_id,
                                resolver_origin,
                                resolver_new,
                                characters[character_id].character,
                                scene_geometry.boundaries,
                                game_time,
                            )
                            attack_log.extend(b_log)
                            if crossing_dmg > 0:
                                char_obj = characters[character_id].character
                                current_hp = getattr(char_obj, "current_hp", getattr(char_obj, "hp", 0))
                                char_obj.current_hp = max(0, current_hp - crossing_dmg)
                                adjudication.hp_damage[character_id] = (
                                    adjudication.hp_damage.get(character_id, 0) + crossing_dmg
                                )
                            # Python owns boundary_crossed — emit only when
                            # the resolver's auto-move actually crossed an
                            # applicable boundary (b_log non-empty) and the
                            # crossing was permitted.
                            if boundary_ok and b_log and "boundary_crossed" not in adjudication.spatial_events:
                                adjudication.spatial_events.append("boundary_crossed")
                        if boundary_ok:
                            # Check impassable polygons after boundaries pass.
                            impassable_ok = True
                            imp_stop: Optional[tuple[float, float]] = None
                            if (
                                scene_geometry is not None
                                and resolver_origin is not None
                                and (scene_geometry.impassable or scene_geometry.zones)
                            ):
                                impassable_ok, i_log, imp_stop = _check_impassable(
                                    character_id,
                                    resolver_origin,
                                    resolver_new,
                                    scene_geometry.impassable,
                                    scene_geometry.zones,
                                )
                                attack_log.extend(i_log)
                            if impassable_ok:
                                current_positions[character_id] = resolver_new
                            elif imp_stop is not None:
                                sx, sy = imp_stop
                                sz = (scene_geometry.zone_at(Position(sx, sy))
                                      if scene_geometry else "") or resolver_new[2]
                                stopped = (sx, sy, sz.upper())
                                adjudication.new_position = stopped
                                current_positions[character_id] = stopped
                            else:
                                adjudication.new_position = None
                        elif stop_at is not None:
                            # Repelled — slide to barrier edge so the path
                            # visibly approaches the shimmer.
                            sx, sy = stop_at
                            sz = (scene_geometry.zone_at(Position(sx, sy))
                                  if scene_geometry else "") or resolver_new[2]
                            stopped = (sx, sy, sz.upper())
                            adjudication.new_position = stopped
                            current_positions[character_id] = stopped
                        else:
                            adjudication.new_position = None
                    # Apply hp damage immediately
                    for tid, dmg in adjudication.hp_damage.items():
                        if tid in characters:
                            tchar = characters[tid].character
                            if hasattr(tchar, "current_hp"):
                                tchar.current_hp = max(0, tchar.current_hp - dmg)
                                if tchar.current_hp <= 0:
                                    active_characters.discard(tid)
                                    current_positions.pop(tid, None)
                                    attack_log.append(f"[{tid} is dead — reduced to 0 HP]")
                                    ts = (
                                        f"{game_time.hour}:{game_time.minute:02d}"
                                        if game_time else f"t{turn_num}"
                                    )
                                    dead_entry = f"{ts} | {tid} | DEAD — 0 HP, removed from scene"
                                    if dead_entry not in ledger.permanent_events:
                                        ledger.permanent_events.append(dead_entry)
                    # Apply condition deltas to target from being hit
                    if adjudication.hp_damage.get(target_id, 0) > 0:
                        characters[target_id].condition.apply_delta(
                            {"cortisol": 0.12, "norepinephrine": 0.08}
                        )
                else:
                    # No valid target — fall through to DM-Left
                    use_resolver = False

            if not use_resolver and not used_spell_resolver:
                _adjudication = await turn_cycle.dm_adjudicate(
                    output=output,
                    game_state_summary=turn_game_state,
                    geometry_summary=geometry_summary,
                    scene_history=within_turn_history,
                    dm_ledger=ledger.render(current_positions, in_combat, game_time, characters=characters),
                )
                adjudication = _adjudication
                attack_log: list[str] = []

            if loop_guard_notes:
                attack_log.extend(loop_guard_notes)

            # Python movement resolution — clamp to speed, snap to zone.
            # Player-Left declares intent.movement_target; Python owns the result.
            # DM-Left can reject the action (approved=False) but cannot rewrite
            # the destination — its MOVEMENT TARGET is ignored here.
            # Skipped when CombatResolver already applied movement.
            player_target = _coordinate_authoritative_target(
                intent.intent,
                intent.movement_target,
                scene_geometry,
            )

            from engine.posture import resolve_posture, posture_landmark_target
            _posture_requested = resolve_posture(intent.intent or "")
            _posture_target = posture_landmark_target(
                intent.intent or "", _posture_requested, scene_geometry,
                current_positions.get(character_id),
            )
            if _posture_target is not None and adjudication.approved:
                player_target = _posture_target
                intent.movement_target = _posture_target
                attack_log.append(
                    f"[POSTURE] {character_id}: approaches the named seating "
                    f"at ({_posture_target[0]:.1f},{_posture_target[1]:.1f})."
                )

            # A named venue approach is grounded to its authored front door,
            # overriding an LLM-generated movement coordinate. This prevents
            # phrases such as "move toward Elyssa's cottage" from wandering in
            # an invented direction.
            _approach_info = None
            if scene_geometry is not None and intent.intent:
                _approach_info = _driftmoor_approach_doorway(
                    intent.intent,
                    getattr(scene_geometry, "place_path", "") or "",
                )
            if _approach_info is not None and adjudication.approved:
                player_target = _approach_info[1]
                intent.movement_target = player_target

            # An explicit coordinate in the intent is authoritative over a
            # model-generated MOVEMENT field. This is especially important for
            # map double-click commands: the language model may otherwise emit
            # a nearby or even opposite-direction coordinate despite repeating
            # the requested destination in its prose.
            _explicit_coordinate = _infer_coordinate_destination(
                intent.intent, scene_geometry
            )
            if _explicit_coordinate is not None and adjudication.approved:
                player_target = _explicit_coordinate
                intent.movement_target = _explicit_coordinate
                attack_log.append(
                    f"[COORDINATE] {character_id}: explicit intent coordinate "
                    f"({_explicit_coordinate[0]:.1f},"
                    f"{_explicit_coordinate[1]:.1f}) overrides structured "
                    f"movement."
                )

            # "enter <venue>" is a distance-clamped walk to that venue's front
            # door (its authored connection point), not a teleport. Resolve the
            # doorway once; force it as this turn's movement target so the actor
            # heads there (clamped), and reuse it below to gate the crossing on
            # arrival. None for exits / non-venue intents, which are unchanged.
            _enter_info = None
            if scene_geometry is not None and intent.intent:
                _enter_info = _driftmoor_enter_doorway(
                    intent.intent,
                    getattr(scene_geometry, "place_path", "") or "",
                    current_positions.get(character_id, ("", "", ""))[2],
                    scene_geometry,
                    current_positions.get(character_id),
                )
            if _enter_info is not None and adjudication.approved:
                _door = _enter_info[1]
                player_target = (_door[0], _door[1], _door[2] or "")
                intent.movement_target = player_target

            # The model sometimes names its destination only in the free-text
            # INTENT ("Move to the first passage") and leaves MOVEMENT empty,
            # so movement_target is None and the actor never relocates.
            # Backfill the coordinate from a named landmark/zone in the intent
            # text. Distance is clamped to speed downstream, so this only sets
            # a direction of travel.
            if (
                not use_resolver
                and adjudication.approved
                and player_target is None
                and intent.intent
            ):
                _move_zone = current_positions.get(
                    character_id, ("", "", "")
                )[2]
                # Explicit coordinates FIRST: "move to [x,y]" is an exact
                # destination and should override looser heading/item inference.
                _dest = _infer_coordinate_destination(
                    intent.intent,
                    scene_geometry,
                )
                # Compass next: a bare heading ("move south") is an unambiguous
                # direction. _infer_cardinal_destination returns None unless the
                # text names a single compass word, so trying it before LATN item
                # grounding prevents "south" from attaching to an unrelated item.
                if _dest is None:
                    _dest = _infer_cardinal_destination(
                        intent.intent,
                        current_positions.get(character_id),
                        scene_geometry,
                    )
                # LATN: ground "move to the <item>" to a scene item's position,
                # so a feature/landmark named in free text becomes a destination.
                if _dest is None:
                    from engine.latn_integration import infer_movement_target
                    _dest = infer_movement_target(
                        intent.intent, items, characters, _move_zone,
                        scene_geometry,
                    )
                # Shallow fallback: zone/landmark named in the text.
                if _dest is None and scene_geometry is not None:
                    _dest = _infer_movement_destination(
                        intent.intent,
                        scene_geometry,
                        current_positions.get(character_id),
                        visited_zones.get(character_id, set()) if visited_zones else set(),
                    )
                # Character fallback: "move toward <party member>" grounds to
                # that character's current position (clamped to speed below).
                if _dest is None:
                    _dest = _infer_character_destination(
                        intent.intent,
                        character_id,
                        characters,
                        current_positions,
                        active_characters,
                    )
                if _dest is not None:
                    player_target = _dest
                    intent.movement_target = _dest
                    attack_log.append(
                        f"[INFER-MOVE] {character_id}: derived movement "
                        f"target ({_dest[0]:.1f},{_dest[1]:.1f}) from intent "
                        f"text '{intent.intent}'."
                    )

            # The model sometimes describes an interaction in the free-text
            # intent (e.g. "I press the top glyph") but leaves the structured
            # interaction_target empty. Backfill it from the intent text when
            # a verb + in-zone item can be identified, so both the auto-move
            # and interaction-resolution gates below fire correctly.
            if (
                not use_resolver
                and adjudication.approved
                and items
                and not intent.interaction_target
                and intent.intent
            ):
                # LATN-first (flag-gated, shallow fallback): parse the free-text
                # intent to backfill the object when the model left
                # interaction_target empty.
                from engine.latn_integration import infer_interaction_target
                _infer_zone = current_positions.get(
                    character_id, ("", "", "")
                )[2]
                _inferred_target = infer_interaction_target(
                    intent.intent, items, characters, _infer_zone,
                    scene_geometry,
                )
                if _inferred_target:
                    intent.interaction_target = _inferred_target
                    attack_log.append(
                        f"[INFER-TARGET] {character_id}: derived interaction "
                        f"target '{_inferred_target}' from intent text."
                    )

            # Phase 3b.1: if the actor declared an interaction_target whose
            # item lives in their current zone, auto-route movement to that
            # item's position. Distance is still clamped to walking speed
            # downstream, so a far item just gets closer this turn — but
            # the actor stops standing 30 ft from a thing they say they
            # are examining. Only fires when the actor didn't already pick
            # a movement target near the item.
            if (
                not use_resolver
                and adjudication.approved
                and items
                and intent.interaction_target
            ):
                # LATN-first with shallow verb_resolver fallback baked in.
                from engine.latn_integration import resolve_item_interaction
                _actor_zone = current_positions.get(
                    character_id, ("", "", "")
                )[2]
                _resolved = resolve_item_interaction(
                    intent_text=intent.intent or "",
                    interaction_target=intent.interaction_target,
                    items=items,
                    characters=characters,
                    character_zone=_actor_zone,
                    scene_geometry=scene_geometry,
                )
                if _resolved is not None:
                    _it_obj, _ = _resolved
                    if _it_obj.position is not None:
                        import math as _math_local
                        ix, iy = _it_obj.position.x, _it_obj.position.y
                        existing = player_target
                        # Replace movement_target unless it is already
                        # within ~5 ft of the item.
                        replace = True
                        if existing is not None:
                            ex, ey = float(existing[0]), float(existing[1])
                            if _math_local.hypot(ex - ix, ey - iy) <= 5.0:
                                replace = False
                        if replace:
                            player_target = (ix, iy, _it_obj.zone or "")
                            intent.movement_target = player_target
                            attack_log.append(
                                f"[AUTO-MOVE] {character_id}: routing to "
                                f"interaction target "
                                f"'{_it_obj.label or _it_obj.id}' at "
                                f"({ix:.1f},{iy:.1f})"
                            )

            if (
                not use_resolver
                and adjudication.approved
                and player_target is not None
            ):
                # Cross-zone routing: a straight line to a target in another
                # zone runs into walls. When the destination zone differs from
                # the actor's, redirect this turn's move to the entry point of
                # the next zone along the adjacency graph — one hop per turn,
                # arriving over several turns. Same-zone targets are unaffected.
                if (scene_geometry is not None
                        and _should_apply_cross_zone_routing(_explicit_coordinate)):
                    _az = (current_positions.get(
                        character_id, ("", "", ""))[2] or "").upper()
                    _dz = ""
                    _pt2 = player_target[2] if len(player_target) > 2 else None
                    if isinstance(_pt2, str) and _pt2:
                        _dz = _pt2.upper()
                    if not _dz or _dz not in {
                        z.upper() for z in scene_geometry.zones
                    }:
                        _zp = scene_geometry.zone_at(Position(
                            float(player_target[0]), float(player_target[1])))
                        _dz = (_zp or "").upper()
                    if _az and _dz and _az != _dz:
                        _nz = _next_zone_toward(scene_geometry, _az, _dz)
                        if _nz:
                            _wp = _waypoint_for_zone(
                                character_id=character_id,
                                current_positions=current_positions,
                                scene_geometry=scene_geometry,
                                target_zone=_nz,
                            )
                            if _wp is not None:
                                player_target = (_wp[0], _wp[1], _nz)
                                attack_log.append(
                                    f"[ROUTE] {character_id}: {_az} → {_dz} via "
                                    f"{_nz.upper()} — heading to its entry at "
                                    f"({_wp[0]:.1f},{_wp[1]:.1f})"
                                )
                tx, ty = float(player_target[0]), float(player_target[1])
                raw_pos: tuple[float, float, str] = (tx, ty, "")
                char = characters[character_id].character
                requested_dist = None
                if intent.intent:
                    from engine.latn_integration import infer_movement_distance
                    requested_dist = infer_movement_distance(
                        intent.intent,
                        items,
                        characters,
                        current_positions.get(character_id, ("", "", ""))[2],
                        scene_geometry,
                    )
                speed_ft = _movement_cap_for_intent(
                    getattr(char, "speed", "30 ft"),
                    intent.intent or "",
                    in_combat=in_combat,
                    requested_distance_ft=requested_dist,
                )
                origin = current_positions.get(character_id)
                if origin is not None:
                    raw_pos = _clamp_position(raw_pos, origin, speed_ft)
                tx, ty = raw_pos[0], raw_pos[1]
                confined = _clamp_to_authored_home(
                    character_id,
                    (tx, ty, raw_pos[2]),
                    char,
                    scene_geometry,
                )
                tx, ty = confined[0], confined[1]
                if scene_geometry is not None:
                    zone = scene_geometry.zone_at(Position(tx, ty)) or ""
                else:
                    zone = current_positions.get(character_id, ("", "", ""))[2]

                # Boundary crossing check — Python owns enforcement; DM cannot override.
                boundary_ok = True
                stop_at: Optional[tuple[float, float]] = None
                if scene_geometry is not None and scene_geometry.boundaries and origin is not None:
                    boundary_ok, crossing_dmg, b_log, stop_at = _check_boundary_crossing(
                        character_id,
                        origin,
                        (tx, ty, ""),
                        characters[character_id].character,
                        scene_geometry.boundaries,
                        game_time,
                    )
                    attack_log.extend(b_log)
                    if crossing_dmg > 0:
                        char_obj = characters[character_id].character
                        current_hp = getattr(char_obj, "current_hp", getattr(char_obj, "hp", 0))
                        char_obj.current_hp = max(0, current_hp - crossing_dmg)
                        adjudication.hp_damage[character_id] = (
                            adjudication.hp_damage.get(character_id, 0) + crossing_dmg
                        )
                    # Python owns boundary_crossed event — emit only when an
                    # applicable boundary was actually traversed (b_log non-empty)
                    # and crossing succeeded.
                    if boundary_ok and b_log and "boundary_crossed" not in adjudication.spatial_events:
                        adjudication.spatial_events.append("boundary_crossed")

                if boundary_ok:
                    new_pos = (tx, ty, zone.upper())
                    # Impassable polygons + outside-zones blocking.
                    impassable_ok = True
                    imp_stop: Optional[tuple[float, float]] = None
                    if scene_geometry is not None and origin is not None and (
                        scene_geometry.impassable or scene_geometry.zones
                    ):
                        impassable_ok, i_log, imp_stop = _check_impassable(
                            character_id, origin, new_pos,
                            scene_geometry.impassable, scene_geometry.zones,
                        )
                        attack_log.extend(i_log)
                    if impassable_ok:
                        adjudication.new_position = new_pos
                        current_positions[character_id] = new_pos
                        if origin is not None:
                            ox, oy, oz = origin
                            moved = (abs(ox - tx) > 0.5 or abs(oy - ty) > 0.5)
                            if moved:
                                attack_log.append(
                                    f"[MOVEMENT] {character_id}: "
                                    f"({ox:.1f},{oy:.1f},{oz}) → "
                                    f"({tx:.1f},{ty:.1f},{new_pos[2]})"
                                )
                            else:
                                attack_log.append(
                                    f"[MOVEMENT] {character_id}: held position "
                                    f"({ox:.1f},{oy:.1f},{oz})"
                                )
                    elif imp_stop is not None:
                        sx, sy = imp_stop
                        sz = (scene_geometry.zone_at(Position(sx, sy))
                              if scene_geometry else "") or ""
                        stopped = (sx, sy, sz.upper())
                        adjudication.new_position = stopped
                        current_positions[character_id] = stopped
                elif stop_at is not None:
                    # Repelled by barrier — slide to its outer edge so the
                    # path visibly approaches the shimmer.
                    sx, sy = stop_at
                    sz = (scene_geometry.zone_at(Position(sx, sy))
                          if scene_geometry else "") or ""
                    stopped = (sx, sy, sz.upper())
                    adjudication.new_position = stopped
                    current_positions[character_id] = stopped
                    attack_log.append(
                        f"[MOVEMENT] {character_id}: repelled by barrier — "
                        f"stopped at ({sx:.1f},{sy:.1f},{sz.upper()})"
                    )
                else:
                    # Movement denied — keep character at origin
                    adjudication.movement_target = None
                    attack_log.append(
                        f"[MOVEMENT] {character_id}: denied — held at origin"
                    )

            if _posture_requested is not None and adjudication.approved:
                from engine.posture import settle_posture
                _posture_applied = settle_posture(
                    cs, _posture_requested,
                    current_positions.get(character_id),
                    _posture_target,
                )
                if _posture_applied:
                    attack_log.append(
                        f"[POSTURE] SETTLED by the engine — {character_id} is "
                        f"now {_posture_requested}. Narrate the physical posture "
                        f"without adding dialogue."
                    )
                    ts = f"{game_time.hour}:{game_time.minute:02d}" if game_time else f"t{turn_num}"
                    recent_events.append((
                        turn_num,
                        f"{ts} | {_char_handle(cs, character_id)} is now "
                        f"{_posture_requested}.",
                    ))
                else:
                    attack_log.append(
                        f"[POSTURE] {character_id} has not reached the seating; "
                        f"posture remains {cs.posture}."
                    )

            # Python attack resolution — roll d20+bonus vs AC, check range and
            # LOS; DM declared targets via **ATTACKS** but Python owns the dice.
            # Skipped when CombatResolver already resolved the attack.
            if not use_resolver and adjudication.approved:
                attacker_char = characters[character_id].character
                attacker_identity = characters[character_id].identity
                max_range = _max_attack_range(attacker_identity)
                max_attacks = _max_attacks(attacker_identity)
                declared = adjudication.attacks[:max_attacks]
                if len(adjudication.attacks) > max_attacks:
                    attack_log.append(
                        f"[ATTACK] capped from {len(adjudication.attacks)} "
                        f"to {max_attacks} (stat block limit)"
                    )
                hp_damage, atk_log = _resolve_attacks(
                    declared,
                    character_id,
                    current_positions.get(character_id),
                    current_positions,
                    characters,
                    max_range,
                    scene_geometry=scene_geometry,
                )
                # Append (don't overwrite) so prior MOVEMENT/BOUNDARY entries
                # in attack_log survive into the narrator's resolution_log.
                attack_log.extend(atk_log)
                # Merge resolved attack damage into adjudication.hp_damage
                # (do not overwrite — boundary-crossing damage may already be
                # recorded for the moving character).
                for tid, dmg in hp_damage.items():
                    adjudication.hp_damage[tid] = (
                        adjudication.hp_damage.get(tid, 0) + dmg
                    )
                # Python owns combat_initiated — emit only when DM-Left actually
                # declared and approved at least one attack this turn.
                if declared and "combat_initiated" not in adjudication.spatial_events:
                    adjudication.spatial_events.append("combat_initiated")

                for target_id, dmg in hp_damage.items():
                    if target_id not in characters:
                        continue
                    char = characters[target_id].character
                    if hasattr(char, "current_hp"):
                        char.current_hp = max(0, char.current_hp - dmg)
                        if char.current_hp <= 0:
                            active_characters.discard(target_id)
                            current_positions.pop(target_id, None)
                            attack_log.append(
                                f"[{target_id} is dead — reduced to 0 HP]"
                            )
                            ts = (
                                f"{game_time.hour}:{game_time.minute:02d}"
                                if game_time else f"t{turn_num}"
                            )
                            dead_entry = f"{ts} | {target_id} | DEAD — 0 HP, removed from scene"
                            if dead_entry not in ledger.permanent_events:
                                ledger.permanent_events.append(dead_entry)

            # Update per-character visited zones from resolved post-turn
            # position and promote party focus when a genuinely new zone is
            # entered. Focus lives for the next two turns.
            post_pos = current_positions.get(character_id)
            if post_pos and post_pos[2]:
                post_zone = post_pos[2].upper()
                char_seen = visited_zones.setdefault(character_id, set())
                zone_is_new = post_zone not in char_seen
                char_seen.add(post_zone)
                prev_zone = (cs.last_zone_seen or actor_zone_before or "").upper()
                if prev_zone and prev_zone != post_zone:
                    _append_memory_note(
                        cs,
                        f"Turn {turn_num}: you moved from {prev_zone} to {post_zone}.",
                    )
                elif not prev_zone:
                    _append_memory_note(
                        cs,
                        f"Turn {turn_num}: you are in {post_zone}.",
                    )
                cs.last_zone_seen = post_zone
                if (
                    not in_combat
                    and actor_zone_before
                    and post_zone
                    and post_zone != actor_zone_before
                    and zone_is_new
                ):
                    party_focus_zone = post_zone
                    party_focus_until_turn = turn_num + 2
                    loop_guard_notes.append(
                        f"[PARTY-FOCUS] {character_id}: established party focus "
                        f"on {post_zone} through turn {party_focus_until_turn}."
                    )

            # Step 4: DM-Right narrates what Python actually resolved.
            # resolution_log tells it which attacks hit, missed, or were blocked.
            # perception constrains narration to the acting character's POV.
            # NOTE: within_turn_history is intentionally NOT passed — other-POV
            # narration from earlier actors this turn leaks unperceived creatures
            # into the acting character's narration. The character's own action
            # already reflects what they perceived; perception + action are
            # sufficient for the narrator.
            _kit_manip_applied = False

            # Kit possession verbs (draw / sheathe / drop / wear) on a weapon or
            # armor. The scene take/drop machinery only knows scene Things, so a
            # kit possession used to no-op silently. The unified affordance-gated
            # dispatch resolves the named kit Thing and applies the verb; only
            # when no scene item was targeted, so picked-up scene things keep the
            # normal path.
            if (
                adjudication.approved
                and not use_resolver
                and intent.intent
            ):
                from engine import loadout, manipulation
                _loadout_log: list[str] = []
                _apply_loadout_intent(intent.intent, cs, _loadout_log)
                if _loadout_log:
                    attack_log.append(
                        f"[LOADOUT] {character_id}: " + ", ".join(_loadout_log)
                    )
                loadout.materialize_things(cs)
                _thing = manipulation.find_possessed_thing(cs, intent.intent)
                if _thing is None:
                    _thing = manipulation.find_possessed_scene_thing(
                        cs,
                        intent.intent,
                        items,
                        intent.interaction_target,
                    )
                if _thing is not None:
                    _verb = manipulation.classify_verb(intent.intent, _thing)
                    # Draw/sheathe can be compound ("sheathe sword and draw
                    # dagger") and are already handled clause-by-clause above.
                    if _verb is not None and not (
                        _loadout_log and _verb in {"draw", "sheathe"}
                    ):
                        _wpos = current_positions.get(character_id, (0.0, 0.0, ""))
                        _mr = manipulation.apply_manipulation(
                            cs, _verb, _thing, items=items, actor_pos=_wpos,
                            actor_zone=_wpos[2] if len(_wpos) > 2 else "",
                            character_id=character_id, game_time=game_time,
                            turn_num=turn_num)
                        if _mr.applied:
                            _kit_manip_applied = True
                            attack_log.extend(_mr.log)
                            recent_events.extend(_mr.events)
                            for _note in _mr.memory:
                                _append_memory_note(cs, _note)
                else:
                    _used_up = manipulation.find_consumed_scene_thing(
                        cs, intent.intent, items)
                    if _used_up is not None:
                        _used_name = (
                            getattr(_used_up, "label", None)
                            or getattr(_used_up, "name", None)
                            or getattr(_used_up, "id", "item")
                        )
                        attack_log.append(
                            f"[ITEM] {character_id} has no {_used_name} left"
                        )
                        _kit_manip_applied = True

            # Commerce: buy a shop good / sell a possession to the shopkeeper
            # present in this scene. Runs only where there IS a shopkeeper (so it
            # costs nothing elsewhere), and only if nothing already handled the
            # intent; marks it handled so it isn't re-processed as an interaction.
            if (
                adjudication.approved
                and not use_resolver
                and not _kit_manip_applied
                and intent.intent
                and _handle_coin_transfer(
                    intent_text=intent.intent,
                    character_id=character_id,
                    characters=characters,
                    active_characters=active_characters,
                    turn_num=turn_num,
                    game_time=game_time,
                    attack_log=attack_log,
                    recent_events=recent_events,
                    cs=cs,
                )
            ):
                _kit_manip_applied = True

            _negotiate = _commerce_negotiator(cs, character_id)
            if (
                adjudication.approved
                and not use_resolver
                and not _kit_manip_applied
                and intent.intent
                and _negotiate is not None
            ):
                _shop_catalog = _driftmoor_shop_catalog()
                _shopkeeper = _current_shopkeeper(
                    characters, active_characters, _shop_catalog)
                if _shopkeeper is not None and await _handle_commerce(
                    intent_text=intent.intent,
                    character_id=character_id,
                    characters=characters,
                    items=items,
                    cs=cs,
                    turn_num=turn_num,
                    game_time=game_time,
                    attack_log=attack_log,
                    recent_events=recent_events,
                    shopkeeper=_shopkeeper,
                    catalog=_shop_catalog,
                    negotiate=_negotiate,
                ):
                    _kit_manip_applied = True

            # Phase 2b: resolve item interactions BEFORE narration so the
            # narrator sees DM-authoritative findings instead of inventing
            # them. Only when the action was approved and not consumed by
            # the combat resolver.
            if (
                adjudication.approved
                and not use_resolver
                and not _kit_manip_applied
                and items
                and intent.interaction_target
            ):
                from engine.verb_resolver import (
                    detect_transfer_verb,
                    authored_transfer_response,
                    resolve_item_interaction as _shallow_resolve_item,
                )
                # LATN-first, drop-in compatible with a shallow fallback.
                from engine.latn_integration import resolve_item_interaction
                transfer_verb = detect_transfer_verb(intent.intent or "")
                actor_zone = current_positions.get(character_id, ("", "", ""))[2]
                # Geometry-rendered zones come uppercase; items carry the
                # canonical-cased zone from CONTENTS.md. Match case-insensitive.
                resolved = resolve_item_interaction(
                    intent_text=intent.intent or "",
                    interaction_target=intent.interaction_target,
                    items=items,
                    characters=characters,
                    character_zone=actor_zone,
                    scene_geometry=scene_geometry,
                )
                if (
                    transfer_verb is None
                    and resolved is None
                    and intent.interaction_target.strip()
                ):
                    # Phase 3b.1: actor named a target but the verb
                    # resolver could not match it in their current zone.
                    # Check whether the item exists in *some other* zone
                    # so the narrator gets an honest "out of reach" line
                    # instead of fabricating the interaction.
                    # Other-zone honesty check stays on the shallow resolver: it
                    # is a "does this item exist anywhere" lookup, and the LATN
                    # adapter's no-zone semantics are not yet validated.
                    other_zone_match = _shallow_resolve_item(
                        intent_text=intent.intent or "",
                        interaction_target=intent.interaction_target,
                        items=items,
                        character_zone=None,
                    )
                    if other_zone_match is not None:
                        oz_item, _ = other_zone_match
                        oz_label = oz_item.label or oz_item.id
                        oz_zone = oz_item.zone or "elsewhere"
                        attack_log.append(
                            f"[ITEM-INTERACTION] {character_id} cannot "
                            f"interact with '{oz_label}': it is in "
                            f"{oz_zone}, not in {actor_zone or 'this zone'}. "
                            f"The character is not within reach and the "
                            f"narration must reflect this — do not describe "
                            f"examining or touching it."
                        )
                        ts = (
                            f"{game_time.hour}:{game_time.minute:02d}"
                            if game_time else f"t{turn_num}"
                        )
                        handle = (
                            characters[character_id].scene_handle
                            or characters[character_id].character.name
                            or character_id
                        )
                        recent_events.append((turn_num, (
                            f"{ts} | {handle} reaches toward {oz_label} "
                            f"but it is in {oz_zone}, beyond reach from here."
                        )))
                if resolved is not None:
                    item_obj, interaction_obj = resolved
                    label = item_obj.label or item_obj.id
                    verb_canonical = interaction_obj.verb.lower().split()[0] if interaction_obj.verb else ""

                    # Possession changes (take / drop / give) are detected
                    # straight from the intent text so they fire even when the
                    # item authored no matching interaction. They mutate
                    # ownership directly and bypass the examine/puzzle paths.
                    transfer_verb = detect_transfer_verb(intent.intent or "")
                    side_effects: list[dict] = []

                    if transfer_verb is not None:
                        # LATN-grounded recipient for "give" (flag-gated; None
                        # otherwise, so the handler uses its shallow match).
                        from engine.latn_integration import resolve_recipient
                        _recipient_override = (
                            resolve_recipient(
                                intent.intent or "", items, characters,
                                actor_zone, scene_geometry,
                            ) if transfer_verb == "give" else None
                        )
                        _handle_item_transfer(
                            transfer_verb=transfer_verb,
                            item_obj=item_obj,
                            label=label,
                            character_id=character_id,
                            characters=characters,
                            active_characters=active_characters,
                            current_positions=current_positions,
                            intent_text=intent.intent or "",
                            actor_zone=actor_zone,
                            turn_num=turn_num,
                            game_time=game_time,
                            attack_log=attack_log,
                            recent_events=recent_events,
                            cs=cs,
                            authored_response=authored_transfer_response(
                                item_obj, transfer_verb
                            ),
                            recipient_override=_recipient_override,
                        )
                    else:
                        # State-mutating presses on a puzzle input route through
                        # the puzzle's own state machine (see engine.puzzles).
                        # The puzzle owns its responses, progress, and effects;
                        # the loop only delegates and broadcasts the result.
                        puzzle = (
                            puzzle_registry.puzzle_for_item(item_obj.id)
                            if verb_canonical == "press" else None
                        )

                        if puzzle is not None:
                            # Atomic focused exchange outside combat; a single
                            # press (no re-prompt) while in combat.
                            side_effects = await _run_puzzle_exchange(
                                first_item=item_obj,
                                puzzle=puzzle,
                                puzzles=puzzle_registry,
                                interactive=not in_combat,
                                turn_cycle=turn_cycle,
                                cs=cs,
                                context=context,
                                output=output,
                                character_id=character_id,
                                turn_num=turn_num,
                                game_time=game_time,
                                items=items,
                                actor_zone=actor_zone,
                                characters=characters,
                                attack_log=attack_log,
                                recent_events=recent_events,
                                scene_geometry=scene_geometry,
                            )
                        else:
                            response = (interaction_obj.response or "").strip()

                            if response:
                                attack_log.append(
                                    f"[ITEM-INTERACTION] {character_id} {interaction_obj.verb} "
                                    f"{label}: {response}"
                                )
                                ts = (
                                    f"{game_time.hour}:{game_time.minute:02d}"
                                    if game_time else f"t{turn_num}"
                                )
                                # First sentence keeps the recent-events bullet tight.
                                first_sentence = response.split(". ", 1)[0].strip()
                                if first_sentence and not first_sentence.endswith("."):
                                    first_sentence += "."
                                handle = (
                                    characters[character_id].scene_handle
                                    or characters[character_id].character.name
                                    or character_id
                                )
                                verb_past = "examined"
                                ev = (
                                    f"{ts} | {handle} {verb_past} {label} — "
                                    f"{first_sentence}"
                                )
                                recent_events.append((turn_num, ev))
                                item_obj.discovered_by.add(character_id)
                                _append_memory_note(
                                    cs,
                                    f"Turn {turn_num}: you {verb_past} {label} in {actor_zone.upper() or 'this zone'} and learned: {first_sentence}",
                                )

                                zone_for_state = (actor_zone or item_obj.zone or "").upper()
                                shared_key = _shared_exam_key(zone_for_state, label)
                                if shared_key is not None:
                                    mark_examined, needs_followup, complete = _classify_examination_result(
                                        verb=interaction_obj.verb or "",
                                        response=response,
                                    )
                                    if mark_examined:
                                        prev = party_examination_state.get(shared_key, {})
                                        was_followup = bool(prev.get("needs_followup", False))
                                        party_examination_state[shared_key] = {
                                            "label": label,
                                            "summary": first_sentence,
                                            "by": character_id,
                                            "last_turn": turn_num,
                                            "needs_followup": needs_followup or (was_followup and not complete),
                                        }

                    # Broadcast any world-affecting effects (e.g. a door
                    # grinding open) to other characters. The broadcast text
                    # is authored with the puzzle, not hard-coded here.
                    _broadcast_effects(
                        side_effects, recent_events, turn_num, game_time,
                    )

            # Phase 3b: re-evaluate activation triggers now that movement
            # and door state may have changed. Promotes dormant creatures
            # whose triggers fire (e.g. giant spider when a non-spider
            # enters the Secret Chamber).
            _door_events_this_turn = []
            try:
                _door_events_this_turn = side_effects  # type: ignore[name-defined]
            except NameError:
                _door_events_this_turn = []
            fired_activations = check_activations(
                characters=characters,
                active_characters=active_characters,
                current_positions=current_positions,
                door_events=_door_events_this_turn,
            )
            for activated_id, reason in fired_activations:
                handle = (
                    characters[activated_id].scene_handle
                    or characters[activated_id].character.name
                    or activated_id
                )
                ts = (
                    f"{game_time.hour}:{game_time.minute:02d}"
                    if game_time else f"t{turn_num}"
                )
                recent_events.append((turn_num, (
                    f"{ts} | {handle} stirs — its presence becomes apparent "
                    f"({reason})."
                )))

            # Tell the narrator whether a doorway-gated "enter" actually
            # crossed the threshold. Movement coordinates alone cannot express
            # this distinction, and otherwise prose may claim entry while the
            # engine merely moved the actor closer to the door.
            if _enter_info is not None:
                _venue_now = current_positions.get(
                    character_id, (0.0, 0.0, "")
                )
                _venue_door = _enter_info[1]
                _venue_dist = (
                    (float(_venue_now[0]) - _venue_door[0]) ** 2
                    + (float(_venue_now[1]) - _venue_door[1]) ** 2
                ) ** 0.5
                _venue_label = _enter_info[0].replace("_", " ")
                if _venue_dist > _DOORWAY_ARRIVAL_FT:
                    attack_log.append(
                        f"[VENUE] {character_id}: approached the "
                        f"{_venue_label} but did not enter it this turn "
                        f"({_venue_dist:.1f} ft from the doorway)."
                    )
                else:
                    attack_log.append(
                        f"[VENUE] {character_id}: reached the doorway and "
                        f"entered the {_venue_label} this turn."
                    )
            elif intent.intent:
                _immediate_venue = _infer_driftmoor_venue_transition(
                    intent.intent,
                    getattr(scene_geometry, "place_path", "")
                    if scene_geometry else "",
                    current_positions.get(character_id, (0.0, 0.0, ""))[2],
                )
                if _immediate_venue is not None:
                    attack_log.append(
                        f"[VENUE] {character_id}: completed the transition to "
                        f"{_immediate_venue.replace('_', ' ')} this turn."
                    )

            cr = await turn_cycle.narrate_turn(
                intent, output, adjudication, "",
                resolution_log=attack_log if attack_log else None,
                character_pronouns=character_pronouns,
                perception=context.perception,
            )
            turn_result.character_results.append(cr)

            # Scene transition hook: Driftmoor town <-> authored interior venues.
            # Keep it conservative: one transition request per turn (first wins).
            if pending_scene_transition is None:
                _cur_place = getattr(scene_geometry, "place_path", "") if scene_geometry else ""
                _cur_zone = current_positions.get(character_id, (0.0, 0.0, ""))[2]
                _source_scene = Path(_cur_place).name if _cur_place else ""
                _debug_target = _debug_travel_target
                _target_scene = _debug_target or _infer_driftmoor_venue_transition(
                    intent.intent or "", _cur_place, _cur_zone,
                )
                # Entering a child venue is doorway-gated: cross in only once
                # this turn's clamped move has brought the actor to the venue's
                # front door. Farther off, the move just closed the distance and
                # the actor re-issues "enter" next turn. Exits and venues without
                # an authored doorway (_enter_info is None) transition as before.
                if (
                    _target_scene is not None
                    and not _debug_target
                    and _enter_info is not None
                    and _enter_info[0] == _target_scene
                ):
                    _now = current_positions.get(character_id, (0.0, 0.0, ""))
                    _door = _enter_info[1]
                    _dist = (
                        (float(_now[0]) - _door[0]) ** 2
                        + (float(_now[1]) - _door[1]) ** 2
                    ) ** 0.5
                    if _dist > _DOORWAY_ARRIVAL_FT:
                        _target_scene = None
                if _target_scene is not None:
                    pending_scene_transition = (
                        character_id,
                        _target_scene,
                        actor_pos_before_action,
                        _source_scene,
                        _cur_place,
                    )

            if adjudication.approved:
                _record_recent_interaction(cs, intent.interaction_target)

            # Guarantee at least one episodic memory trace per acting turn.
            # Richer notes (zone transition, item discovery, etc.) win; this
            # fallback records current zone context when no other note landed.
            if len(cs.episodic_memory) == memory_count_before:
                zone_now = (
                    current_positions.get(character_id, (None, None, ""))[2]
                    or cs.last_zone_seen
                    or ""
                ).upper()
                if zone_now:
                    _append_memory_note(
                        cs,
                        f"Turn {turn_num}: you are in {zone_now}.",
                    )
                else:
                    _append_memory_note(
                        cs,
                        f"Turn {turn_num}: you held position.",
                    )

            # Record result in DM ledger (later chars in this turn see it)
            ledger.record(cr, game_time)

            # Derive Python-verified events for the player-facing recent-events
            # block. Compare pre_active vs. current active_characters to detect
            # deaths that just happened from this cr's damage application.
            handles = {
                cid: (c.scene_handle or c.character.name or cid)
                for cid, c in characters.items()
            }
            for ev in _events_from_cr(
                cr, pre_active, set(active_characters), handles, game_time,
            ):
                recent_events.append((turn_num, ev))

            # Append attack log to within_turn_history so subsequent characters
            # in this turn can see what happened
            for log_line in attack_log:
                within_turn_history += f"\n{log_line}"

            # Check for exits_scene — remove from active set mid-turn
            if EXIT_EVENT in cr.adjudication.spatial_events:
                active_characters.discard(character_id)
                current_positions.pop(character_id, None)

            # Check for combat_initiated — switch to melee time.
            # NOTE: the swap to MELEE_DURATION is deferred until AFTER this
            # turn's advance() so that the turn during which combat begins
            # ticks at its original (exploration) cadence. Otherwise a turn
            # in which combat both starts and ends — e.g. one round of
            # ranged volley — would advance the clock by only 1 minute,
            # leaving an awkward 19:21 timestamp between two 10-minute
            # exploration ticks.
            if (COMBAT_EVENT in cr.adjudication.spatial_events
                    and cr.adjudication.approved
                    and not in_combat and game_time is not None):
                in_combat = True
                pre_combat_duration = game_time.turn_duration
                # Apply swap after the post-turn advance, below.

            # Build history entry: dialogue + narration
            spoken = cr.output.spoken or ""
            action = (cr.output.action or "").strip()
            cs = characters[cr.character_id]
            handle = cs.scene_handle or cr.character_id
            history_entry = _history_entry(
                handle,
                spoken,
                action,
                cr.narration.prose or "",
            )
            if history_entry:
                within_turn_history += history_entry

            # Publish the initiating action before any immediate social reply,
            # preserving question -> answer ordering in live clients.
            _speaker_hook_sent = False
            if on_character_acted is not None:
                try:
                    on_character_acted(
                        character_id, turn_num, dict(current_positions), cr)
                    _speaker_hook_sent = True
                except Exception:  # noqa: BLE001
                    pass

            # Social exchange override: outside combat, a transport-backed
            # player's directed question receives one immediate dialogue-only
            # NPC response. This is an adjacency pair, not another physical
            # action, and consumes the NPC's next exploration initiative slot.
            if (not in_combat and _social_target is not None
                    and _social_target in active_characters):
                from engine.social_exchange import generate_social_reply
                target_cs = characters[_social_target]
                speaker_handle = handle
                target_history = (
                    f"{scene_history}\n{within_turn_history}"
                    if scene_history else within_turn_history
                )
                target_context = _build_context(
                    target_cs, turn_num, target_history,
                    scene_geometry=scene_geometry,
                    current_positions=current_positions,
                    active_characters=active_characters,
                    in_combat=False,
                    characters=characters,
                    items=items,
                    puzzles=puzzle_registry,
                )
                reply = await generate_social_reply(
                    turn_cycle=turn_cycle,
                    target_id=_social_target,
                    target_cs=target_cs,
                    speaker_handle=speaker_handle,
                    utterance=output.spoken,
                    scene_context=target_context.scene_context,
                )
                if reply:
                    social_intent = ActionIntent(
                        character_id=_social_target,
                        turn=turn_num,
                        intent=f"answer {character_id}",
                        interaction_target=character_id,
                    )
                    social_output = CharacterOutput(
                        character_id=_social_target,
                        turn=turn_num,
                        spoken=reply,
                        action="",
                    )
                    social_adj = Adjudication(
                        character_id=_social_target,
                        turn=turn_num,
                        approved=True,
                        notes="Immediate dialogue-only social response; no physical action.",
                    )
                    social_cr = CharacterTurnResult(
                        character_id=_social_target,
                        turn=turn_num,
                        intent=social_intent,
                        output=social_output,
                        adjudication=social_adj,
                        narration=Narration(
                            character_id=_social_target,
                            turn=turn_num,
                            prose="",
                            visible_to=[],
                        ),
                    )
                    turn_result.character_results.append(social_cr)
                    if _social_target not in acted_this_turn:
                        social_schedule.mark_response(_social_target)
                    if not output.action and _social_visible_ids == {_social_target}:
                        active_dialogues[character_id] = _social_target
                    target_handle = target_cs.scene_handle or _social_target
                    within_turn_history += _history_entry(
                        target_handle, reply, "", ""
                    )
                    ledger.record(social_cr, game_time)
                    if on_character_acted is not None:
                        try:
                            on_character_acted(
                                _social_target, turn_num,
                                dict(current_positions), social_cr,
                            )
                        except Exception:  # noqa: BLE001
                            pass

            # Per-initiative hook: this character has acted and moved, so callers
            # can refresh live views (e.g. the web map + log) without waiting for
            # the whole turn to finish. ``cr`` carries this character's narration
            # so a live UI can stream it. Best-effort; a failure never aborts play.
            if on_character_acted is not None and not _speaker_hook_sent:
                try:
                    on_character_acted(
                        character_id, turn_num, dict(current_positions), cr)
                except Exception:  # noqa: BLE001 — live views are best-effort
                    pass

        await _broadcast_turn_results_to_transports(
            turn_result=turn_result,
            characters=characters,
            current_positions=current_positions,
        )

        # Small pause so transport result packet is safely delivered before
        # the next turn's prompt is written.  Only matters when there is at
        # least one Telegram player; cost is negligible otherwise.
        if _has_telegram_transport(characters):
            await asyncio.sleep(TRANSPORT_SETTLE_SECONDS)

        # Apply condition deltas from DMLeft adjudication
        for cr in turn_result.character_results:
            if cr.adjudication.condition_deltas:
                characters[cr.character_id].condition.apply_delta(
                    cr.adjudication.condition_deltas
                )
            # Accumulate dialogue + narration for next turn's context
            spoken = cr.output.spoken or ""
            action = (cr.output.action or "").strip()
            cs = characters[cr.character_id]
            handle = cs.scene_handle or cr.character_id
            history_entry = _history_entry(
                handle,
                spoken,
                action,
                cr.narration.prose or "",
            )
            if history_entry:
                scene_history += history_entry

        # Move current-turn ledger entries into the sliding window
        ledger.flush_turn()

        # Apply deferred scene transition after the turn's narration is emitted.
        # The next turn runs in the destination scene with its own geometry,
        # items, and active cast while preserving the acting player's state.
        if pending_scene_transition is not None:
            actor_id, target_scene_name, actor_from_pos, source_scene_name, source_place_path = pending_scene_transition
            actor_cs = characters.get(actor_id)
            if actor_cs is not None:
                from engine.md_loader import configure_from_place_path
                from engine.activation import initial_dormant_set
                from engine.puzzles import PuzzleRegistry

                # Place-driven transition loading: scene transitions derive from
                # authored place paths (scenario/places/...), not scenes/*.md.
                target_place_path = (
                    target_scene_name
                    if target_scene_name.startswith("places/")
                    else _transition_target_place_path(
                        target_scene_name, source_place_path,
                    )
                )

                if target_place_path:
                    # Debug travel carries a full authored place path; use the
                    # ordinary scene slug for callbacks and narration below.
                    target_scene_name = Path(target_place_path).name
                    cfg = configure_from_place_path(
                        target_place_path,
                        game_time=game_time,
                    )

                    # Preserve return anchor when entering any authored child
                    # scene so exiting returns to where the actor came from.
                    if source_scene_name and target_scene_name != source_scene_name:
                        setattr(actor_cs, "_mvp_return_scene", source_scene_name)
                        setattr(actor_cs, "_mvp_return_pos", actor_from_pos)

                    # Update the actor's scene intro from destination config while
                    # preserving runtime state (condition/inventory/loadout/memory).
                    tmpl_actor = cfg.characters.get(actor_id)
                    if tmpl_actor is not None:
                        actor_cs.initial_scene = tmpl_actor.initial_scene

                    # Replace cast with destination scene cast + preserved actor.
                    new_characters: dict[str, CharacterSession] = {actor_id: actor_cs}
                    for cid, cs2 in cfg.characters.items():
                        if cid == actor_id:
                            continue
                        new_characters[cid] = cs2
                    characters.clear()
                    characters.update(new_characters)

                    character_roles.clear()
                    character_roles.update(cfg.roles)
                    turn_cycle.character_roles = character_roles

                    game_state_summary = cfg.game_state_summary
                    geometry_summary = cfg.geometry_summary
                    scene_geometry = cfg.scene_geometry
                    carried_items = {
                        iid: thing for iid, thing in (items or {}).items()
                        if getattr(thing, "holder", None) == actor_id
                    }
                    items = cfg.items or {}
                    items.update(carried_items)
                    puzzle_registry = cfg.puzzles if cfg.puzzles is not None else PuzzleRegistry()
                    cfg.characters = characters
                    cfg.roles = character_roles
                    cfg.items = items
                    cfg.game_time = game_time

                    # Rebuild active set for the destination scene.
                    dormant = initial_dormant_set(characters)
                    active_characters = set(characters.keys()) - dormant

                    # Position everyone at destination starts; actor uses their
                    # saved return anchor when stepping back out to Driftmoor.
                    current_positions = {}
                    for cid, cs2 in characters.items():
                        if scene_geometry is None:
                            current_positions[cid] = (0.0, 0.0, "")
                            continue

                        if (
                            cid == actor_id
                            and target_scene_name == getattr(actor_cs, "_mvp_return_scene", "")
                            and isinstance(getattr(actor_cs, "_mvp_return_pos", None), tuple)
                        ):
                            rx, ry, rz = getattr(actor_cs, "_mvp_return_pos")
                            current_positions[cid] = (float(rx), float(ry), str(rz).upper())
                            continue

                        start = scene_geometry.starting_positions.get(cid)
                        if start is None:
                            # Prefix match for creature ids with suffixes.
                            start = next(
                                (p for k, p in scene_geometry.starting_positions.items()
                                 if cid.startswith(k) or k.startswith(cid)),
                                None,
                            )
                        if start is not None:
                            z = (scene_geometry.zone_at(start) or "").upper()
                            current_positions[cid] = (float(start.x), float(start.y), z)
                        else:
                            if cid == actor_id:
                                doorway = _entry_point_from_target_geometry(
                                    target_place_path,
                                    source_place_path,
                                    scene_geometry,
                                )
                                if doorway is not None:
                                    current_positions[cid] = doorway
                                    continue
                            current_positions[cid] = (0.0, 0.0, "")

                    # Reset scene-local visibility progression for the new map.
                    visited_zones = {}
                    for _cid, _pos in current_positions.items():
                        if _pos and _pos[2]:
                            visited_zones.setdefault(_cid, set()).add(_pos[2].upper())
                            if _cid in characters:
                                characters[_cid].last_zone_seen = _pos[2].upper()

                    # The player is normally not authored in a place-local
                    # upstairs cast.  Seed their resolved arrival point into the
                    # destination map so the transition callback can render fog
                    # of war immediately instead of producing an apparently
                    # blank screen until another movement event arrives.
                    _seed_transition_actor_start(
                        scene_geometry, actor_id, current_positions
                    )

                    party_focus_zone = None
                    party_focus_until_turn = 0
                    scene_history = ""

                    _actor_handle = (
                        characters[actor_id].scene_handle
                        or characters[actor_id].character.name
                        or actor_id
                    )
                    _ts = (
                        f"{game_time.hour}:{game_time.minute:02d}"
                        if game_time else f"t{turn_num}"
                    )
                    _dest_title = target_scene_name.replace("_", " ").title()
                    recent_events.append((turn_num, f"{_ts} | {_actor_handle} transitions to {_dest_title}."))
                    _append_memory_note(
                        characters[actor_id],
                        f"Turn {turn_num}: you transitioned to {_dest_title}.",
                    )
                    if on_scene_transition is not None:
                        try:
                            on_scene_transition(target_scene_name, cfg)
                        except Exception:
                            pass

        # Advance scene-level spell effect durations once per completed turn.
        spell_resolver.tick_effects(spell_runtime, rounds=1)

        # Carried items follow their holder, so a torch picked up in one zone and
        # carried into another can still be dropped/stowed there (the possession
        # verbs resolve on the item's current zone).
        _sync_carried_item_positions(characters, current_positions, items)

        # Persist checkpoint
        if checkpoint_dir:
            _save_turn(
                checkpoint_dir,
                turn_num,
                turn_result,
                characters,
                game_time,
                in_combat=in_combat,
                active_characters=active_characters,
                current_positions=current_positions,
                party_examination_state=party_examination_state,
                spell_runtime=spell_runtime,
                items=items,
                scene_place_path=(
                    getattr(scene_geometry, "place_path", "")
                    if scene_geometry is not None else ""
                ),
            )
        # Advance game clock
        if game_time:
            game_time.advance(1)

        # Count this turn against the appropriate budget
        if combat_at_start:
            melee_rounds_remaining -= 1
        else:
            story_turns_remaining -= 1
        turn_num += 1

        # Check for combat end: no hostile still facing a non-hostile
        if in_combat and game_time is not None:
            hostiles_active = any(
                cs.character.faction == "hostile"
                for cid, cs in characters.items()
                if cid in active_characters
            )
            non_hostiles_active = any(
                cs.character.faction != "hostile"
                for cid, cs in characters.items()
                if cid in active_characters
            )
            if not non_hostiles_active and hostiles_active:
                # Allies all dead/fled and hostiles remain — hostiles win, end session
                break
            if not hostiles_active:
                # Hostiles eliminated or fled — return to story pacing
                in_combat = False
                game_time.turn_duration = pre_combat_duration or 10
                pre_combat_duration = None
            elif game_time.turn_duration != MELEE_DURATION:
                # Combat is ongoing into the next turn — switch to melee
                # cadence now (deferred from when combat_initiated fired
                # so the starting turn ticks at exploration speed).
                game_time.turn_duration = MELEE_DURATION

        yield turn_result


async def run_session(
    characters: dict[str, CharacterSession],
    character_roles: dict[str, RoleSet],
    num_turns: int,
    *,
    game_state_summary: str = "",
    geometry_summary: str = "",
    checkpoint_dir: Optional[Path] = None,
    game_time: Optional[GameTime] = None,
    rng: Optional[random.Random] = None,
    scene_geometry: Optional[SceneGeometry] = None,
    items: Optional[dict] = None,
    puzzles: Optional["PuzzleRegistry"] = None,
    character_pronouns: dict[str, str] | None = None,
    start_turn: int = 1,
    initial_history: str = "",
    initial_active_characters: set[str] | None = None,
    initial_positions: Optional[dict[str, tuple[float, float, str]]] = None,
    initial_party_examination_state: Optional[dict[tuple[str, str], dict]] = None,
    initial_spell_runtime: Optional[SpellRuntimeState] = None,
    on_turn: "Callable[[TurnResult], None] | None" = None,
    on_character_acted: "Callable[[str, int, dict, CharacterTurnResult], None] | None" = None,
    on_scene_transition: "Callable[[str, object], None] | None" = None,
) -> SessionResult:
    """Run a complete game session and return all results.

    Wraps ``iter_session`` for the common single-scene case.  Use
    ``iter_session`` directly when you need to interleave multiple scenes
    turn-by-turn (e.g. ``run_all.py``).

    ``on_turn`` (if given) is invoked after each turn's checkpoint is written —
    the checkpoint is already on disk — so callers can regenerate per-turn
    artifacts (e.g. the live map). It is best-effort: an exception in it is
    swallowed so a visualization failure never aborts the session.
    """
    turns: list[TurnResult] = []
    async for turn_result in iter_session(
        characters, character_roles, num_turns,
        game_state_summary=game_state_summary,
        geometry_summary=geometry_summary,
        checkpoint_dir=checkpoint_dir,
        game_time=game_time,
        rng=rng,
        start_turn=start_turn,
        initial_history=initial_history,
        scene_geometry=scene_geometry,
        items=items,
        puzzles=puzzles,
        character_pronouns=character_pronouns,
        initial_active_characters=initial_active_characters,
        initial_positions=initial_positions,
        initial_party_examination_state=initial_party_examination_state,
        initial_spell_runtime=initial_spell_runtime,
        on_character_acted=on_character_acted,
        on_scene_transition=on_scene_transition,
    ):
        turns.append(turn_result)
        if on_turn is not None:
            try:
                on_turn(turn_result)
            except Exception:  # noqa: BLE001 — live artifacts are best-effort
                pass

    # Give the final TURN RESULT packet time to be consumed before
    # SESSION COMPLETE is emitted on transport channels.
    if turns and _has_telegram_transport(characters):
        await asyncio.sleep(TRANSPORT_SETTLE_SECONDS)

    await _broadcast_session_complete_to_transports(
        completed_turns=len(turns),
        characters=characters,
    )

    return SessionResult(
        turns=turns,
        final_conditions={
            char_id: cs.condition for char_id, cs in characters.items()
        },
        scene_history="",
    )
