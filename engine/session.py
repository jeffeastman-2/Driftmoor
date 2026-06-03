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
import platform
import re
import random
import shlex
import subprocess
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import AsyncIterator, Optional

from engine.initiative import roll_initiative
from engine.player_router import RoleContext, ActionIntent, CharacterOutput
from engine.scene_manager import TurnCycle, TurnResult, RoleSet
from engine.dm_agent import Adjudication
from models.character import Character
from models.condition import CharacterCondition, render_condition
from models.geometry_loader import load_geometry
from models.space_time import GameTime, Position, SceneGeometry


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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMBAT_EVENT = "combat_initiated"
EXIT_EVENT = "exits_scene"
MELEE_DURATION = 1  # minutes per combat turn
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
    # Phase 3b: dormancy. "always" = active from turn 1 (default).
    # "zone_entry:<Zone Name>" = activate when an opposing-faction
    # character enters that zone. "door_open:<door_id>" = activate when
    # the named door fires its open side effect.
    activation: str = "always"
    # Python-owned episodic memory used to reinforce continuity in prompts.
    episodic_memory: list[str] = field(default_factory=list)
    recent_interactions: list[str] = field(default_factory=list)
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


def _is_search_like_intent(intent_text: str) -> bool:
    """Heuristic: intent text is a search/examine style action."""
    return bool(re.search(
        r"\b(search|examine|inspect|investigate|look|scan|check|sift)\b",
        (intent_text or "").lower(),
    ))


def _normalize_target_name(target: Optional[str]) -> str:
    """Normalize item target text for loop-key comparisons."""
    if not target:
        return ""
    s = target.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return s.strip()


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


def _point_to_segment_distance_2d(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> float:
    """Distance from point (px, py) to segment (ax, ay)-(bx, by)."""
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    qx, qy = ax + t * dx, ay + t * dy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def _polygons_are_adjacent(poly_a, poly_b, tol: float = 0.75) -> bool:
    """True when two zone polygons share/touch an edge (or near-edge)."""
    va = list(getattr(poly_a, "vertices", []) or [])
    vb = list(getattr(poly_b, "vertices", []) or [])
    if not va or not vb:
        return False

    for v in va:
        ax, ay = float(v[0]), float(v[1])
        for i in range(len(vb)):
            x1, y1 = float(vb[i][0]), float(vb[i][1])
            x2, y2 = float(vb[(i + 1) % len(vb)][0]), float(vb[(i + 1) % len(vb)][1])
            if _point_to_segment_distance_2d(ax, ay, x1, y1, x2, y2) <= tol:
                return True

    for v in vb:
        bx, by = float(v[0]), float(v[1])
        for i in range(len(va)):
            x1, y1 = float(va[i][0]), float(va[i][1])
            x2, y2 = float(va[(i + 1) % len(va)][0]), float(va[(i + 1) % len(va)][1])
            if _point_to_segment_distance_2d(bx, by, x1, y1, x2, y2) <= tol:
                return True

    return False


def _entry_point_inside_zone(
    *,
    actor_x: float,
    actor_y: float,
    target_poly,
    inset: float = 3.0,
) -> tuple[float, float]:
    """Pick a point just inside target_poly near the actor-facing boundary."""
    actor_pos = Position(actor_x, actor_y)
    boundary = target_poly.nearest_point(actor_pos)
    center = target_poly.centroid()

    vx = center.x - boundary.x
    vy = center.y - boundary.y
    mag = (vx * vx + vy * vy) ** 0.5
    if mag <= 1e-9:
        return float(center.x), float(center.y)

    step = min(inset, mag * 0.95)
    ux, uy = vx / mag, vy / mag
    tx = boundary.x + ux * step
    ty = boundary.y + uy * step
    if target_poly.contains(Position(tx, ty)):
        return float(tx), float(ty)

    # Fallback: walk from boundary toward center until we are inside.
    for frac in (0.65, 0.8, 1.0):
        cx = boundary.x + vx * frac
        cy = boundary.y + vy * frac
        if target_poly.contains(Position(cx, cy)):
            return float(cx), float(cy)
    return float(center.x), float(center.y)


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
) -> list:
    """Return glyph items in the given zone, if any."""
    if not current_zone or not items:
        return []
    from engine.state_resolver import GLYPH_IDS  # local import avoids cycle

    zone = current_zone.upper()
    return [
        item for item in items.values()
        if item.id in GLYPH_IDS and (item.zone or "").upper() == zone
    ]


def _zone_has_unresolved_puzzle(
    *,
    current_zone: str,
    items: Optional[dict],
    puzzle_state: Optional[dict],
) -> bool:
    """Return True when the actor is standing in an unsolved puzzle zone."""
    if not current_zone or not items or not puzzle_state:
        return False
    if puzzle_state.get("door_open", False):
        return False
    return bool(_puzzle_items_in_zone(current_zone, items))


def _build_puzzle_pressure_block(
    *,
    current_zone: str,
    items: Optional[dict],
    puzzle_state: Optional[dict],
) -> str:
    """Return a context block reminding the actor to keep working a live puzzle."""
    if not _zone_has_unresolved_puzzle(
        current_zone=current_zone,
        items=items,
        puzzle_state=puzzle_state,
    ):
        return ""

    seq = list((puzzle_state or {}).get("glyph_sequence", []))
    seq_text = " -> ".join(seq) if seq else "not yet started"
    glyphs = _puzzle_items_in_zone(current_zone, items)
    glyph_names = ", ".join((it.label or it.id).strip() for it in glyphs)
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
    current_target_norm: str,
) -> Optional[tuple[str, float, float, str]]:
    """Prefer a glyph item in the actor's current zone when a puzzle is live."""
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
    for item in _puzzle_items_in_zone(actor_zone, items):
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


def _max_attacks(identity_text: str) -> int:
    """Return the maximum number of attacks per turn from a character's identity/stat block.

    Looks for a Multiattack entry (e.g. 'makes 2 attacks'). Defaults to 1.
    """
    t = identity_text or ""
    m = re.search(
        r'multiattack[^.\n]*makes\s+(\d+)\s+(?:\w+\s+)?attacks',
        t, re.IGNORECASE,
    )
    if m:
        return int(m.group(1))
    return 1


def _max_attack_range(identity_text: str) -> float:
    """Return the maximum attack range in feet from a character's identity text.

    Checks (in order): ranged weapon range, AoE radius, melee reach.
    Defaults to 5 ft (standard melee) if none found.
    """
    t = identity_text or ""
    # Ranged weapon: "range 150/600 ft" or "range 80/320"
    m = re.search(r'\brange\s+(\d+)/\d+', t, re.IGNORECASE)
    if m:
        return float(m.group(1))
    # Ranged weapon: "range 60 ft"
    m = re.search(r'\brange\s+(\d+)\s*ft', t, re.IGNORECASE)
    if m:
        return float(m.group(1))
    # AoE radius: "10ft radius" or "10 ft radius"
    m = re.search(r'(\d+)\s*ft\s+radius', t, re.IGNORECASE)
    if m:
        return float(m.group(1))
    # Melee reach: "reach 10 ft"
    m = re.search(r'\breach\s+(\d+)\s*ft', t, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return 5.0  # default melee reach


def _enforce_attack_range(
    hp_damage: dict[str, int],
    attacker_pos: tuple[float, float, str] | None,
    current_positions: dict[str, tuple[float, float, str]],
    max_range: float,
) -> dict[str, int]:
    """Remove hp_damage entries where the target is beyond the attacker's max range.

    Used to catch LLM arithmetic errors where the DM resolves melee attacks
    from a position that is actually out of reach.
    """
    import math
    if attacker_pos is None or not hp_damage:
        return hp_damage
    ax, ay = attacker_pos[0], attacker_pos[1]
    filtered: dict[str, int] = {}
    for target_id, dmg in hp_damage.items():
        tpos = current_positions.get(target_id)
        if tpos is None:
            filtered[target_id] = dmg  # target position unknown, keep it
            continue
        dist = math.hypot(tpos[0] - ax, tpos[1] - ay)
        if dist <= max_range + 0.5:  # 0.5 ft tolerance for floating point
            filtered[target_id] = dmg
        # else: silently drop — attacker could not reach this target
    return filtered


def _clamp_position(
    proposed: tuple[float, float, str],
    origin: tuple[float, float, str],
    max_feet: float,
) -> tuple[float, float, str]:
    """Clamp *proposed* to within *max_feet* of *origin*.

    If the proposed displacement exceeds max_feet, scales it back along
    the same direction so the character moves at most max_feet.
    The zone from *proposed* is preserved — zone assignment belongs to the DM.
    """
    import math
    ox, oy = origin[0], origin[1]
    px, py = proposed[0], proposed[1]
    dx, dy = px - ox, py - oy
    dist = math.hypot(dx, dy)
    if dist <= max_feet or dist == 0:
        return proposed
    scale = max_feet / dist
    return (round(ox + dx * scale, 1), round(oy + dy * scale, 1), proposed[2])


def _roll_damage_expr(expr: str) -> int:
    """Roll a damage expression such as '1d6', '2d4+2', or '1d8 slashing'.

    Ignores non-numeric descriptors (damage type words).
    Returns at least 0.
    """
    total = 0
    # Roll all dice terms: NdM
    for m in re.finditer(r'(\d+)\s*[dD]\s*(\d+)', expr):
        count, sides = int(m.group(1)), int(m.group(2))
        for _ in range(count):
            total += random.randint(1, sides)
    # Apply flat modifier: the +/- numbers not part of a dice term
    remainder = re.sub(r'\d+\s*[dD]\s*\d+', '', expr)
    for m in re.finditer(r'([+-]\s*\d+)', remainder):
        total += int(m.group(1).replace(' ', ''))
    # Plain integer with no sign (rare, e.g. just "5")
    plain = remainder.strip()
    if re.fullmatch(r'\d+', plain):
        total += int(plain)
    return max(0, total)


def _segment_polygon_entry(
    ox: float, oy: float, tx: float, ty: float,
    vertices: list[tuple[float, ...]],
) -> Optional[tuple[float, float]]:
    """Return (x, y) where segment origin→target first enters the polygon.

    Returns None if the segment does not cross any edge.
    Caller should verify origin is outside and target inside.
    """
    dx, dy = tx - ox, ty - oy
    best_t = float("inf")
    best_pt: Optional[tuple[float, float]] = None
    n = len(vertices)
    for i in range(n):
        ax, ay = vertices[i][0], vertices[i][1]
        bx, by = vertices[(i + 1) % n][0], vertices[(i + 1) % n][1]
        ex, ey = bx - ax, by - ay
        denom = dx * ey - dy * ex
        if abs(denom) < 1e-9:
            continue  # parallel
        t = ((ax - ox) * ey - (ay - oy) * ex) / denom
        u = ((ax - ox) * dy - (ay - oy) * dx) / denom
        if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0 and t < best_t:
            best_t = t
            best_pt = (ox + t * dx, oy + t * dy)
    return best_pt


def _check_impassable(
    character_id: str,
    origin: tuple[float, float, str],
    new_pos: tuple[float, float, str],
    impassable: list,
    zones: Optional[dict] = None,
) -> tuple[bool, list[str], Optional[tuple[float, float]]]:
    """Check whether origin→new_pos enters impassable space.

    Two rules combine:

    1. **Outside all zones** — if ``zones`` is provided and the destination
       is not inside any walkable zone, the move is blocked. This naturally
       handles "background rock" (the negative space between chambers in a
       cavern) without requiring it to be enumerated as an impassable
       polygon.
    2. **Inside an impassable polygon** — for finer-grained obstacles (a
       pool inside a chamber, a pillar in a room) declared in the
       ``## Impassable`` table. Polygons that already contain the origin are
       skipped so a character standing in a pool can step out of it; this is
       also why rule 1 (not rule 2) handles whole-scene "Solid Rock" entries.

    Returns (move_allowed, log_lines, stop_at). ``stop_at`` is set to a
    point just outside the offending edge so the character visibly slides
    up to the wall instead of refusing to leave its origin.
    """
    log_lines: list[str] = []
    if not impassable and not zones:
        return True, log_lines, None

    ox, oy = origin[0], origin[1]
    tx, ty = new_pos[0], new_pos[1]

    # Skip if origin and target are the same point.
    if abs(tx - ox) < 1e-6 and abs(ty - oy) < 1e-6:
        return True, log_lines, None

    origin_pos = Position(ox, oy)
    target_pos = Position(tx, ty)

    best_t = float("inf")
    best_stop: Optional[tuple[float, float]] = None
    best_name = ""

    # Rule 1: destination outside all walkable zones.
    if zones:
        in_any_zone = any(z.contains(target_pos) for z in zones.values())
        if not in_any_zone:
            origin_in_any_zone = any(z.contains(origin_pos) for z in zones.values())
            if origin_in_any_zone:
                # Find first zone exit along origin→target.
                for zname, zpoly in zones.items():
                    if not zpoly.contains(origin_pos):
                        continue
                    exit_pt = _segment_polygon_entry(
                        ox, oy, tx, ty, zpoly.vertices,
                    )
                    if exit_pt is None:
                        continue
                    seg_dx, seg_dy = tx - ox, ty - oy
                    seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy
                    if seg_len_sq < 1e-9:
                        continue
                    t = ((exit_pt[0] - ox) * seg_dx + (exit_pt[1] - oy) * seg_dy) / seg_len_sq
                    if t < best_t:
                        best_t = t
                        best_stop = exit_pt
                        best_name = f"edge of {zname}"
            else:
                # Origin already outside zones — rare; let them try to move.
                pass

    # Rule 2: inside a foreground impassable polygon.
    for poly in (impassable or []):
        if poly.contains(origin_pos):
            continue  # already inside (e.g. pool) — let them try to leave
        crosses_in = poly.contains(target_pos)
        entry = _segment_polygon_entry(ox, oy, tx, ty, poly.vertices)
        if not crosses_in and entry is None:
            continue
        if entry is None:
            continue
        ex, ey = entry
        seg_dx, seg_dy = tx - ox, ty - oy
        seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy
        if seg_len_sq < 1e-9:
            continue
        t = ((ex - ox) * seg_dx + (ey - oy) * seg_dy) / seg_len_sq
        if t < best_t:
            best_t = t
            best_stop = (ex, ey)
            best_name = getattr(poly, "name", None) or "impassable"

    if best_stop is None:
        return True, log_lines, None

    # Back off ~0.5 ft from the edge so the character is clearly outside.
    ex, ey = best_stop
    seg_dx, seg_dy = tx - ox, ty - oy
    seg_len = (seg_dx * seg_dx + seg_dy * seg_dy) ** 0.5
    if seg_len > 1e-6:
        backoff = min(0.5, seg_len * 0.05)
        nx, ny = seg_dx / seg_len, seg_dy / seg_len
        stop_at = (ex - nx * backoff, ey - ny * backoff)
    else:
        stop_at = (ex, ey)

    log_lines.append(
        f"[IMPASSABLE] {character_id} blocked by {best_name}: "
        f"stops at x={stop_at[0]:.1f}, y={stop_at[1]:.1f}"
    )
    return False, log_lines, stop_at


def _check_boundary_crossing(
    character_id: str,
    origin: tuple[float, float, str],
    new_pos: tuple[float, float, str],
    character,
    boundaries: list,
    game_time,
) -> tuple[bool, int, list[str], Optional[tuple[float, float]]]:
    """Check if movement crosses a magical boundary inward.

    Returns (move_allowed, radiant_damage, log_lines, stop_at).
    ``stop_at`` is set when the save fails: a point just outside the barrier
    along the origin→target line, so the character visibly approaches the
    barrier and is repelled (rather than refusing to move at all).
    If the current period has no DC entry in the boundary table the barrier is
    quiescent and crossing is freely permitted (e.g. daylight — the beast avoids
    daylight by its own nature, not barrier force).
    """
    log_lines: list[str] = []

    ox, oy = origin[0], origin[1]
    tx, ty = new_pos[0], new_pos[1]
    origin_pos = Position(ox, oy)
    target_pos = Position(tx, ty)

    race = getattr(character, "race", "").lower().replace(" ", "_")
    char_type = getattr(character, "character_type", "").lower()
    # Strip trailing _N suffix so "shadowbeast_1" matches block entry "shadowbeast"
    base_id = re.sub(r"_\d+$", "", character_id).lower()

    for boundary in (boundaries or []):
        already_inside = boundary.perimeter.contains(origin_pos)
        would_enter = boundary.perimeter.contains(target_pos)

        if already_inside or not would_enter:
            continue  # not crossing inward

        if not (
            boundary.is_blocked(race)
            or boundary.is_blocked(char_type)
            or boundary.is_blocked(character_id)
            or boundary.is_blocked(base_id)
        ):
            continue  # this character is not affected by the boundary

        period = game_time.period if game_time else "night"
        dc = boundary.crossing_dc.get(period)

        if dc is None:
            # No DC for this period — barrier is quiescent, crossing allowed
            log_lines.append(
                f"[BOUNDARY] {character_id} crosses {boundary.name} freely "
                f"(period={period}, barrier quiescent)"
            )
            return True, 0, log_lines, None

        # Wisdom saving throw
        wisdom = getattr(character, "wisdom", 10)
        wis_mod = (wisdom - 10) // 2
        d20 = random.randint(1, 20)
        total = d20 + wis_mod

        if total >= dc:
            damage_expr = boundary.crossing_damage_success.get(period, "")
            dmg = _roll_damage_expr(damage_expr) if damage_expr else 0
            # Double for radiant vulnerability if the character has it
            vulnerabilities = getattr(character, "damage_vulnerabilities", [])
            if any("radiant" in v.lower() for v in vulnerabilities):
                dmg *= 2
                log_lines.append(
                    f"[BOUNDARY] {character_id} crosses {boundary.name}: "
                    f"WIS save d20={d20}+{wis_mod}={total} vs DC {dc} → SUCCESS, "
                    f"{dmg} radiant damage (doubled — radiant vulnerability)"
                )
            else:
                log_lines.append(
                    f"[BOUNDARY] {character_id} crosses {boundary.name}: "
                    f"WIS save d20={d20}+{wis_mod}={total} vs DC {dc} → SUCCESS, "
                    f"{dmg} radiant damage"
                )
            return True, dmg, log_lines, None
        else:
            # Compute the point where the path enters the barrier and back
            # off ~0.5 ft so the character visibly approaches and stops at
            # the shimmer instead of refusing to leave its origin.
            stop_at: Optional[tuple[float, float]] = None
            entry = _segment_polygon_entry(
                ox, oy, tx, ty, boundary.perimeter.vertices,
            )
            if entry is not None:
                ex, ey = entry
                seg_dx, seg_dy = tx - ox, ty - oy
                seg_len = (seg_dx * seg_dx + seg_dy * seg_dy) ** 0.5
                if seg_len > 1e-6:
                    backoff = min(0.5, seg_len * 0.05)
                    nx, ny = seg_dx / seg_len, seg_dy / seg_len
                    stop_at = (ex - nx * backoff, ey - ny * backoff)
                else:
                    stop_at = (ex, ey)
            log_lines.append(
                f"[BOUNDARY] {character_id} repelled by {boundary.name}: "
                f"WIS save d20={d20}+{wis_mod}={total} vs DC {dc} → FAILED"
                + (f" — stops at x={stop_at[0]:.1f}, y={stop_at[1]:.1f}"
                   if stop_at else "")
            )
            return False, 0, log_lines, stop_at

    return True, 0, log_lines, None  # no blocking boundary found


def _resolve_attacks(
    attacks: list[dict],
    character_id: str,
    attacker_pos: tuple[float, float, str] | None,
    current_positions: dict[str, tuple[float, float, str]],
    characters: dict,
    max_range: float,
    scene_geometry=None,
) -> tuple[dict[str, int], list[str]]:
    """Roll d20+bonus vs target AC, roll damage on hit. Returns (hp_damage, log_lines).

    hp_damage: target_id → total damage this turn
    log_lines: human-readable results injected into turn history for the DM ledger
    """
    import math
    hp_damage: dict[str, int] = {}
    log_lines: list[str] = []

    for atk in attacks:
        target_id = atk.get("target", "")
        hit_bonus = atk.get("hit_bonus", 0)
        damage_expr = atk.get("damage_expr", "1d4")

        # Fuzzy-match target ID: if DM omitted the numeric suffix (e.g. "shadowbeast"
        # instead of "shadowbeast_1"), find the first character whose id starts with it.
        if target_id not in characters:
            matched = next(
                (cid for cid in characters if cid.startswith(target_id) or target_id.startswith(cid)),
                None,
            )
            if matched:
                log_lines.append(
                    f"[ATTACK] fuzzy-matched target '{target_id}' → '{matched}'"
                )
                target_id = matched
            else:
                log_lines.append(f"[ATTACK] {character_id} → {target_id}: unknown target, skipped")
                continue

        # Range check and LOS check
        if attacker_pos is not None:
            tpos = current_positions.get(target_id)
            if tpos is not None:
                dist = math.hypot(tpos[0] - attacker_pos[0], tpos[1] - attacker_pos[1])
                if dist > max_range + 0.5:
                    log_lines.append(
                        f"[ATTACK] {character_id} → {target_id}: out of range "
                        f"({dist:.1f} ft > {max_range} ft), skipped"
                    )
                    continue
                # LOS check
                if scene_geometry is not None:
                    a_pos = Position(attacker_pos[0], attacker_pos[1])
                    t_pos = Position(tpos[0], tpos[1])
                    if not scene_geometry.can_see(a_pos, t_pos):
                        log_lines.append(
                            f"[ATTACK] {character_id} → {target_id}: no line of sight "
                            f"({scene_geometry.zone_at(a_pos) or '?'} → "
                            f"{scene_geometry.zone_at(t_pos) or '?'}), skipped"
                        )
                        continue

        target_char = characters[target_id].character
        ac = getattr(target_char, "ac", 10)
        d20 = random.randint(1, 20)
        total_roll = d20 + hit_bonus

        if total_roll >= ac:
            dmg = _roll_damage_expr(damage_expr)
            hp_damage[target_id] = hp_damage.get(target_id, 0) + dmg
            log_lines.append(
                f"[ATTACK] {character_id} → {target_id}: "
                f"d20={d20}+{hit_bonus}={total_roll} vs AC {ac} → HIT for {dmg} ({damage_expr})"
            )
        else:
            log_lines.append(
                f"[ATTACK] {character_id} → {target_id}: "
                f"d20={d20}+{hit_bonus}={total_roll} vs AC {ac} → MISS"
            )

    return hp_damage, log_lines


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

    Uses SceneGeometry.can_see() (which enforces LOS and zone visibility rules)
    to determine which other active characters are currently visible.
    Returns "" when no geometry is available (falls back to no constraint).

    Other creatures are referred to by their ``scene_handle`` (e.g. "the
    elf ranger") rather than their internal character_id, because the
    acting character has not necessarily been introduced to them by name.

    When ``items`` is provided, items in the same zone as the acting
    character are appended under an ``Items in this zone:`` sub-header.
    Same-zone items are presumed visible (Phase 5 will add LOS-aware item
    visibility for items separated from the character by sub-zone walls).
    """
    import math
    if scene_geometry is None:
        _dbg(f"[PERCEPTION] {character_id}: no scene_geometry — skipping LOS")
        return ""
    my_pos = current_positions.get(character_id)
    if my_pos is None:
        _dbg(f"[PERCEPTION] {character_id}: no position — skipping LOS")
        return ""

    _dbg(f"[PERCEPTION] {character_id} at {my_pos}")
    lines: list[str] = []
    for other_id, other_pos in current_positions.items():
        if other_id == character_id or other_id not in active_characters:
            continue
        a = Position(my_pos[0], my_pos[1])
        b = Position(other_pos[0], other_pos[1])
        visible = scene_geometry.can_see(a, b)
        zone_a = scene_geometry.zone_at(a) or "?"
        zone_b = scene_geometry.zone_at(b) or "?"
        dist = math.hypot(b.x - a.x, b.y - a.y)
        _dbg(f"[PERCEPTION]   {other_id} at {other_pos}: {zone_a}->{zone_b} dist={dist:.1f} visible={visible}")
        if visible:
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
            lines.append(
                f"- {label} ({faction_tag}{zone}, ~{dist_rounded:.0f} ft away)"
            )

    result = "\n".join(lines) if lines else ""

    # ------------------------------------------------------------------
    # Items in the character's current zone.
    # ------------------------------------------------------------------
    if items:
        my_zone = (my_pos[2] or scene_geometry.zone_at(Position(my_pos[0], my_pos[1])) or "").upper()
        item_lines: list[str] = []
        for item in items.values():
            iz = (item.zone or "").upper()
            if not iz or iz != my_zone:
                continue
            if item.position is None:
                continue
            dx = item.position.x - my_pos[0]
            dy = item.position.y - my_pos[1]
            dist = math.hypot(dx, dy)
            dist_rounded = round(dist / 5) * 5
            label = item.label or item.id.replace("_", " ")
            # Phase 3b.1: tag items already examined by anyone in the
            # party so the LLM stops looping on the same Search action.
            tag = " (already examined)" if item.discovered_by else ""
            item_lines.append(f"- {label} (~{dist_rounded:.0f} ft away){tag}")
        if item_lines:
            items_block = "Items in this zone:\n" + "\n".join(item_lines)
            result = f"{result}\n\n{items_block}" if result else items_block

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


def _build_points_of_interest(
    scene_geometry: Optional[SceneGeometry],
    my_pos: Optional[tuple[float, float, str]],
    visited_zones: Optional[set[str]] = None,
) -> str:
    """List named landmarks (and zone centers) with absolute coords and
    distance from the character's current position.

    Player-Left LLMs need explicit coords to write a meaningful MOVEMENT
    target; otherwise they emit small offsets from their current spot and
    appear stuck.

    Visibility filter: a landmark/zone center is shown only if it lies in
    the character's current zone OR a previously visited zone. Junction
    landmarks (on a zone seam) are shown if either adjacent zone is
    visible. Landmarks not associated with any zone (e.g. a scene-edge
    crack) are always shown — they're effectively "outside" the chamber
    map.
    """
    if scene_geometry is None or my_pos is None:
        return ""
    px, py = my_pos[0], my_pos[1]
    current_zone = (my_pos[2] or "").upper()
    visible_zones: set[str] = set(visited_zones or set())
    if current_zone:
        visible_zones.add(current_zone)
    lines: list[str] = []

    # Landmarks — filtered by zone visibility
    for name, pos in scene_geometry.landmarks.items():
        lm_zones = _zones_for_point(pos, scene_geometry.zones)
        # If a landmark sits in zones the character has not encountered,
        # hide it. If it's not in any zone (lm_zones empty), show it
        # (treat as scene-level / outside-the-map waypoint).
        if lm_zones and not (lm_zones & visible_zones):
            continue
        dist = ((pos.x - px) ** 2 + (pos.y - py) ** 2) ** 0.5
        lines.append(
            f"- {name}: x={pos.x:.0f}, y={pos.y:.0f} (~{dist:.0f} ft away)"
        )

    # Zone centers (helpful when the goal is "move into the GLADE") —
    # only for visible zones.
    for zname, polygon in scene_geometry.zones.items():
        if zname.upper() not in visible_zones:
            continue
        verts = polygon.vertices
        if not verts:
            continue
        cx = sum(v[0] for v in verts) / len(verts)
        cy = sum(v[1] for v in verts) / len(verts)
        dist = ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5
        lines.append(
            f"- {zname} zone center: x={cx:.0f}, y={cy:.0f} (~{dist:.0f} ft away)"
        )

    if not lines:
        return ""
    return "## Points of interest (use these coordinates in MOVEMENT)\n" + "\n".join(lines)


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
    puzzle_state: Optional[dict] = None,
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
        puzzle_state=puzzle_state,
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

_ATTACK_KEYWORDS = re.compile(
    r'\b(attack|shoot|fire|strike|shoot|stab|slash|lunge|charge|aim)\b',
    re.IGNORECASE,
)

_CAST_KEYWORDS = re.compile(r"\b(cast|casts|casting|use\s+spell|spell)\b", re.IGNORECASE)


def _intent_is_attack(intent_text: str) -> bool:
    """Return True if the Player-Left intent string describes an attack action."""
    return bool(_ATTACK_KEYWORDS.search(intent_text or ""))


def _intent_is_spell(intent_text: str) -> bool:
    """Return True when intent text appears to describe casting a spell."""
    return bool(_CAST_KEYWORDS.search(intent_text or ""))


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


def _find_combat_target(
    intent,
    attacker_id: str,
    characters: dict,
    current_positions: dict,
    active_characters: set[str],
) -> str | None:
    """Return the best target character_id for an attack.

    Priority:
    1. intent.interaction_target if it names an active hostile character
    2. Nearest active hostile character
    Returns None if no valid target exists.
    """
    import math

    attacker_faction = getattr(characters[attacker_id].character, "faction", "party")

    # Collect active hostiles (opposite faction)
    def is_hostile_to_attacker(cid: str) -> bool:
        if cid == attacker_id:
            return False
        f = getattr(characters[cid].character, "faction", "party")
        # hostile faction vs party faction, or party attacking hostile
        return (attacker_faction == "hostile") != (f == "hostile")

    hostiles = [
        cid for cid in active_characters
        if cid in characters and is_hostile_to_attacker(cid)
    ]
    if not hostiles:
        return None

    # 1. Check intent.interaction_target
    hint = (intent.interaction_target or "").strip().lower()
    if hint:
        # Fuzzy match: exact or prefix
        for cid in hostiles:
            if cid.lower() == hint or cid.lower().startswith(hint) or hint.startswith(cid.lower()):
                return cid

    # 2. Nearest hostile
    attacker_pos = current_positions.get(attacker_id)
    if attacker_pos is None:
        return hostiles[0]

    def dist_to(cid: str) -> float:
        pos = current_positions.get(cid)
        if pos is None:
            return 9999.0
        return math.hypot(pos[0] - attacker_pos[0], pos[1] - attacker_pos[1])

    return min(hostiles, key=dist_to)


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


def _shared_exam_key(zone: str | None, target: str | None) -> tuple[str, str] | None:
    """Build a normalized key for party-shared examination state."""
    z = (zone or "").upper().strip()
    t = _normalize_target_name(target)
    if not z or not t:
        return None
    return z, t


def _serialize_party_examination_state(
    state: dict[tuple[str, str], dict],
) -> dict[str, dict]:
    """Serialize tuple-keyed party examination state for JSON checkpoints."""
    out: dict[str, dict] = {}
    for (zone, target), meta in state.items():
        out[f"{zone}::{target}"] = {
            "label": str(meta.get("label", "")),
            "summary": str(meta.get("summary", "")),
            "by": str(meta.get("by", "")),
            "last_turn": int(meta.get("last_turn", 0) or 0),
            "needs_followup": bool(meta.get("needs_followup", False)),
        }
    return out


def _deserialize_party_examination_state(raw: dict | None) -> dict[tuple[str, str], dict]:
    """Deserialize checkpointed party examination state."""
    state: dict[tuple[str, str], dict] = {}
    if not isinstance(raw, dict):
        return state
    for key, meta in raw.items():
        if not isinstance(key, str) or "::" not in key:
            continue
        zone, target = key.split("::", 1)
        norm = _shared_exam_key(zone, target)
        if norm is None:
            continue
        meta_dict = meta if isinstance(meta, dict) else {}
        state[norm] = {
            "label": str(meta_dict.get("label", "")),
            "summary": str(meta_dict.get("summary", "")),
            "by": str(meta_dict.get("by", "")),
            "last_turn": int(meta_dict.get("last_turn", 0) or 0),
            "needs_followup": bool(meta_dict.get("needs_followup", False)),
        }
    return state


def _serialize_spell_runtime_state(runtime: SpellRuntimeState) -> dict:
    """Serialize mutable spell runtime state for checkpoints."""
    return {
        "active_effects": [
            {
                "spell_name": effect.spell_name,
                "caster_id": effect.caster_id,
                "target_ids": list(effect.target_ids),
                "remaining_rounds": int(effect.remaining_rounds),
                "concentration": bool(effect.concentration),
            }
            for effect in runtime.active_effects
        ],
        "concentration_by_caster": {
            caster_id: effect.spell_name
            for caster_id, effect in runtime.concentration_by_caster.items()
        },
    }


def _deserialize_spell_runtime_state(raw: dict | None) -> SpellRuntimeState:
    """Deserialize checkpointed spell runtime state."""
    runtime = SpellRuntimeState()
    if not isinstance(raw, dict):
        return runtime

    for item in raw.get("active_effects", []) or []:
        if not isinstance(item, dict):
            continue
        effect = ActiveSpellEffect(
            spell_name=str(item.get("spell_name", "")),
            caster_id=str(item.get("caster_id", "")),
            target_ids=[str(t) for t in (item.get("target_ids") or [])],
            remaining_rounds=int(item.get("remaining_rounds", 0) or 0),
            concentration=bool(item.get("concentration", False)),
        )
        runtime.active_effects.append(effect)

    for caster_id, spell_name in (raw.get("concentration_by_caster") or {}).items():
        if not isinstance(caster_id, str) or not isinstance(spell_name, str):
            continue
        match = next(
            (
                e for e in runtime.active_effects
                if e.caster_id == caster_id and e.spell_name == spell_name
            ),
            None,
        )
        if match is not None:
            runtime.concentration_by_caster[caster_id] = match

    return runtime


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


def _checkpoint_filename(turn: int, game_time: Optional[GameTime] = None) -> str:
    """Build checkpoint filename from game time or turn number."""
    if game_time is not None:
        return f"day{game_time.day}_{game_time.hour:02d}h{game_time.minute:02d}m.json"
    return f"turn_{turn:04d}.json"


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
) -> Path:
    """Save a turn checkpoint as JSON."""
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    path = checkpoint_dir / _checkpoint_filename(turn, game_time)

    active = active_characters if active_characters is not None else set(characters.keys())

    data = {
        "turn": turn,
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
            prose = (cr_data["narration"].get("prose") or "").strip()
            entry = ""
            if spoken and spoken.lower() not in ("(silent)", "(silence)"):
                entry += f'\n{char_id} says: "{spoken}"'
            if prose:
                entry += f"\n{prose}"
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


def _render_transport_prompt(
    *,
    context: RoleContext,
    cs: CharacterSession,
    raw_history: str = "",
) -> str:
    """Format the DM situation packet sent to human transport channels."""
    from engine.runtime_paths import current_session_id

    perception = context.perception.strip() if context.perception else "No other creatures are visible."
    scene = _render_transport_scene_delta(
        scene_context=context.scene_context,
        turn=context.turn,
        raw_history=raw_history,
        cs=cs,
    )
    return (
        f"PACKET: TURN PROMPT\n"
        f"TURN PROMPT: {context.turn}\n"
        f"SESSION: {current_session_id()}\n"
        f"CHARACTER: {context.character_id}\n"
        f"HANDLE: {cs.scene_handle or context.character_id}\n"
        f"\n"
        f"SCENE\n"
        f"{scene}\n"
        f"\n"
        f"PERCEPTION\n"
        f"{perception}\n"
        f"\n"
        f"Reply with your intent for this turn in plain text.\n"
    )


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


def _render_transport_scene_delta(
    *,
    scene_context: str,
    turn: int,
    raw_history: str,
    cs: CharacterSession,
) -> str:
    """Render scene block for transport prompts with per-player delta history."""
    # Turn 1 keeps compact scene intro. Seed cursor to avoid replaying old
    # context on turn 2 if raw history already exists (resume/new join).
    if turn <= 1:
        cs.transport_history_cursor = len(_history_lines_dedup(raw_history))
        return _compact_scene_for_transport(scene_context, turn=turn, raw_history=raw_history)

    history_lines = _history_lines_dedup(raw_history)
    start = max(0, min(cs.transport_history_cursor, len(history_lines)))
    delta = history_lines[start:]
    cs.transport_history_cursor = len(history_lines)

    if not delta:
        return "Recent context (since your last turn):\n(no new statements or actions)"
    return "Recent context (since your last turn):\n" + "\n".join(delta)


def _compact_scene_for_transport(
    scene_context: str,
    *,
    max_lines: int = 24,
    max_chars: int = 1800,
    turn: int = 1,
    raw_history: str = "",
) -> str:
    """Return a compact scene block for human transport prompts.

    On turn 1 the full (filtered) scene_context is shown so the player gets
    the scene intro.  On turn 2+ only the running dialogue/narration log is
    shown (raw_history), which avoids replaying the entire LLM system prompt
    and keeps the packet short.
    """
    # On turns after the first, use raw_history (the running log) directly.
    # This avoids replaying the full LLM system prompt (initial_scene text)
    # which can be 50-100 lines the human player does not need to re-read.
    if turn > 1 and raw_history.strip():
        history_lines = [ln.rstrip() for ln in raw_history.splitlines() if ln.strip()]
        deduped_history: list[str] = []
        last_norm = ""
        for ln in history_lines:
            norm = " ".join(ln.strip().lower().split())
            if norm == last_norm:
                continue
            deduped_history.append(ln)
            last_norm = norm

        tail = deduped_history[-max_lines:]
        while tail and len("\n".join(tail)) > max_chars:
            tail = tail[1:]
        if tail:
            return "Recent context:\n" + "\n".join(tail)

    raw = (scene_context or "").strip()
    if not raw:
        return "(no scene context available)"

    lines = [ln.rstrip() for ln in raw.splitlines() if ln.strip()]
    if not lines:
        return "(no scene context available)"

    # Human transport prompts should not replay engine memory/meta guidance.
    drop_headers = {
        "## what you remember",
        "## anti-repetition guidance",
        "## recent events",
        "## points of interest",
        "## puzzle pressure",
    }
    cleaned: list[str] = []
    skip_block = False
    for ln in lines:
        lowered = ln.strip().lower()
        if lowered.startswith("## "):
            skip_block = any(lowered.startswith(h) for h in drop_headers)
            if skip_block:
                continue
        if skip_block:
            continue
        cleaned.append(ln)

    if not cleaned:
        cleaned = lines

    # Past turn 1, prefer the dialogue/narration tail over static intro lines.
    # Separate "intro" lines (second-person scene setup) from "live" lines
    # (dialogue, narration) so the tail always leads with what changed.
    if turn > 1:
        intro_prefixes = (
            "you arrive",
            "you are here",
            "you hear",
            "you invite",
        )
        intro_lines = [
            ln for ln in cleaned
            if ln.strip().lower().startswith(intro_prefixes)
        ]
        live_lines = [
            ln for ln in cleaned
            if not ln.strip().lower().startswith(intro_prefixes)
        ]
        # Use live content; if there is none yet (turn 2 with no history),
        # fall back to intro lines so the prompt is not empty.
        cleaned = live_lines if live_lines else intro_lines

    tail = cleaned[-max_lines:]
    while tail and len("\n".join(tail)) > max_chars:
        tail = tail[1:]
    return "Recent context:\n" + "\n".join(tail)


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

    quoted_parts: list[str] = []
    for m in re.finditer(r'"([^"]+)"|“([^”]+)”', without_star):
        q = (m.group(1) or m.group(2) or "").strip()
        if q:
            quoted_parts.append(q)
    without_quotes = re.sub(r'"[^"]+"|“[^”]+”', " ", without_star)

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


async def _player_roles_via_transport(
    *,
    turn_cycle: TurnCycle,
    context: RoleContext,
    cs: CharacterSession,
    raw_history: str = "",
) -> tuple[ActionIntent, CharacterOutput]:
    """Run player roles using transport-backed human input when configured."""
    transport = (cs.player_transport or "llm").strip().lower()
    if transport != "telegram":
        return await turn_cycle.player_roles(context)

    inbox = (cs.player_inbox or "").strip()
    outbox = (cs.player_outbox or "").strip()
    if not inbox or not outbox:
        raise RuntimeError(
            f"Telegram transport for {context.character_id} requires both inbox and outbox paths."
        )

    host = (cs.player_host or "").strip()
    prompt_text = _render_transport_prompt(context=context, cs=cs, raw_history=raw_history)
    await _host_write_text(host, outbox, prompt_text)
    # Ignore stale inbox content from before this prompt was sent.
    accept_after_ns = time.time_ns()
    _dbg(f"[TRANSPORT] wrote turn {context.turn} prompt for {context.character_id} to {host or 'local'}:{outbox}")

    while True:
        inbound = (await _host_read_text(host, inbox, min_mtime_ns=accept_after_ns)).strip()
        if inbound:
            intent = _intent_from_transport_text(
                character_id=context.character_id,
                turn=context.turn,
                text=inbound,
            )
            output = await turn_cycle.player_right_from_intent(context, intent)
            spoken_text, action_text = _split_transport_utterance(inbound)
            if spoken_text:
                output.spoken = spoken_text
            elif output.spoken and output.spoken.strip().lower() not in {"", "(silent)", "(silence)"}:
                # Respect model-produced speech only when user did not provide any.
                output.spoken = output.spoken.strip()
            else:
                output.spoken = ""

            if action_text:
                output.action = action_text
            return intent, output
        await asyncio.sleep(1.0)


def _render_turn_result_packet(
    *,
    player_id: str,
    turn_result: TurnResult,
    characters: dict[str, CharacterSession],
) -> str:
    """Render a concise post-turn update for human transport channels."""
    from engine.runtime_paths import current_session_id

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
            if cr.narration.prose:
                lines.append(f"Outcome: {_truncate_for_transport(cr.narration.prose.strip(), 420)}")
            lines.append("")
            continue

        lines.append(f"[{handle}]")
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
) -> None:
    """Send post-turn updates to all configured Telegram players."""
    for char_id, cs in characters.items():
        if (cs.player_transport or "").strip().lower() != "telegram":
            continue
        if not (cs.player_outbox or "").strip():
            continue

        packet = _render_turn_result_packet(
            player_id=char_id,
            turn_result=turn_result,
            characters=characters,
        )
        await _host_write_text(
            (cs.player_host or "").strip(),
            (cs.player_outbox or "").strip(),
            packet,
        )
        _dbg(
            f"[TRANSPORT] wrote turn-result {turn_result.turn} for "
            f"{char_id} to {(cs.player_host or 'local').strip()}:{(cs.player_outbox or '').strip()}"
        )


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
        if not (cs.player_outbox or "").strip():
            continue
        await _host_write_text(
            (cs.player_host or "").strip(),
            (cs.player_outbox or "").strip(),
            packet,
        )
        _dbg(
            f"[TRANSPORT] wrote session-complete for "
            f"{char_id} to {(cs.player_host or 'local').strip()}:{(cs.player_outbox or '').strip()}"
        )


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
    character_pronouns: dict[str, str] | None = None,
    initial_active_characters: set[str] | None = None,
    initial_positions: Optional[dict[str, tuple[float, float, str]]] = None,
    initial_party_examination_state: Optional[dict[tuple[str, str], dict]] = None,
    initial_spell_runtime: Optional[SpellRuntimeState] = None,
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

    # Purge inbox and outbox dirs for all Telegram players so stale files from
    # aborted previous runs don't produce duplicate or out-of-order messages.
    for _cs in characters.values():
        if (_cs.player_transport or "").strip().lower() == "telegram":
            _inbox = (_cs.player_inbox or "").strip()
            _outbox = (_cs.player_outbox or "").strip()
            _host = (_cs.player_host or "").strip()
            if _inbox:
                try:
                    await _host_purge_dir(_host, _inbox)
                    _dbg(f"[TRANSPORT] purged inbox {_host or 'local'}:{_inbox} at session start")
                except Exception as _e:
                    _dbg(f"[TRANSPORT] inbox purge failed for {_host or 'local'}:{_inbox}: {_e}")
            if _outbox:
                try:
                    await _host_purge_dir(_host, _outbox)
                    _dbg(f"[TRANSPORT] purged outbox {_host or 'local'}:{_outbox} at session start")
                except Exception as _e:
                    _dbg(f"[TRANSPORT] outbox purge failed for {_host or 'local'}:{_outbox}: {_e}")

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

    # Live position tracking — seeded from geometry starting positions then
    # updated each turn from DM-approved MOVEMENT TARGET.
    current_positions: dict[str, tuple[float, float, str]] = _parse_positions_table(
        game_state_summary
    )
    # Fill any missing entries from the geometry's Starting Positions table
    # so speed-clamping works from Turn 1 even for characters not in the
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

    # Phase 3a: per-session puzzle bookkeeping (glyph press sequence,
    # secret-door state). Owned here, mutated by state_resolver.process_press.
    from engine.state_resolver import initial_puzzle_state
    puzzle_state: dict = initial_puzzle_state()

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

        for character_id in order:
            if character_id not in active_characters:
                continue

            # Expire stale focus at character step granularity.
            if party_focus_zone and turn_num > party_focus_until_turn:
                party_focus_zone = None
                party_focus_until_turn = 0

            cs = characters[character_id]
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
                puzzle_state=puzzle_state,
            )

            # Steps 1-3: Player-Left → Player-Right → DM-Left
            # When in combat and the character has structured weapons, bypass
            # DM-Left and use CombatResolver for attack resolution.
            intent, output = await _player_roles_via_transport(
                turn_cycle=turn_cycle,
                context=context,
                cs=cs,
                raw_history=combined_history,
            )
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
            ):
                focus_zone = party_focus_zone.upper()
                if actor_zone_before and actor_zone_before != focus_zone:
                    puzzle_live_here = _zone_has_unresolved_puzzle(
                        current_zone=actor_zone_before,
                        items=items,
                        puzzle_state=puzzle_state,
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
                        puzzle_state=puzzle_state,
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
                    puzzle_state=puzzle_state,
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
                    )
                    if attack_disadvantage and _consume_vicious_mockery_disadvantage(
                        spell_runtime, character_id
                    ):
                        attack_log.append(
                            f"[SPELL] {character_id} consumed Vicious Mockery disadvantage on this attack"
                        )
                    # Apply movement from resolver — enforce boundary crossing
                    if adjudication.new_position:
                        resolver_origin = current_positions.get(character_id)
                        resolver_new = adjudication.new_position
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
            player_target = intent.movement_target  # (x, y, z) or None

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
                from engine.verb_resolver import resolve_item_interaction
                _actor_zone = current_positions.get(
                    character_id, ("", "", "")
                )[2]
                _resolved = resolve_item_interaction(
                    intent_text=intent.intent or "",
                    interaction_target=intent.interaction_target,
                    items=items,
                    character_zone=_actor_zone,
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
                tx, ty = float(player_target[0]), float(player_target[1])
                raw_pos: tuple[float, float, str] = (tx, ty, "")
                char = characters[character_id].character
                speed_ft = _speed_to_feet(getattr(char, "speed", "30 ft"))
                origin = current_positions.get(character_id)
                if origin is not None:
                    raw_pos = _clamp_position(raw_pos, origin, speed_ft)
                tx, ty = raw_pos[0], raw_pos[1]
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

            # Phase 2b: resolve item interactions BEFORE narration so the
            # narrator sees DM-authoritative findings instead of inventing
            # them. Only when the action was approved and not consumed by
            # the combat resolver.
            if (
                adjudication.approved
                and not use_resolver
                and items
                and intent.interaction_target
            ):
                from engine.verb_resolver import resolve_item_interaction
                actor_zone = current_positions.get(character_id, ("", "", ""))[2]
                # Geometry-rendered zones come uppercase; items carry the
                # canonical-cased zone from CONTENTS.md. Match case-insensitive.
                resolved = resolve_item_interaction(
                    intent_text=intent.intent or "",
                    interaction_target=intent.interaction_target,
                    items=items,
                    character_zone=actor_zone,
                )
                if resolved is None and intent.interaction_target.strip():
                    # Phase 3b.1: actor named a target but the verb
                    # resolver could not match it in their current zone.
                    # Check whether the item exists in *some other* zone
                    # so the narrator gets an honest "out of reach" line
                    # instead of fabricating the interaction.
                    other_zone_match = resolve_item_interaction(
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

                    # Phase 3a: state-mutating verbs route through the
                    # state resolver, which OVERRIDES the response so the
                    # glyph sequence + door state machine drives the truth.
                    side_effects: list[dict] = []
                    if verb_canonical == "press":
                        from engine.state_resolver import process_press
                        response, side_effects = process_press(
                            item_obj, items, puzzle_state,
                        )
                        response = (response or "").strip()
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
                        # Verb past tense for the event line; "press" reads
                        # naturally as "pressed", others use "examined" by
                        # convention from Phase 2b.
                        verb_past = "pressed" if verb_canonical == "press" else "examined"
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

                    # Phase 3a: broadcast door state changes to all
                    # characters via recent_events. The spider in the
                    # Secret Chamber feels the vibration through its web
                    # and the LLM can react accordingly on its next turn.
                    for effect in side_effects:
                        ts = (
                            f"{game_time.hour}:{game_time.minute:02d}"
                            if game_time else f"t{turn_num}"
                        )
                        if effect.get("type") == "door_open":
                            recent_events.append((turn_num, (
                                f"{ts} | The hairline crack in the west "
                                f"wall of the Echo Chamber grinds open "
                                f"into a passable hewn opening. Stone "
                                f"vibrations carry through the surrounding "
                                f"rock — anything attuned to the rock or "
                                f"resting on a web in the Secret Chamber "
                                f"feels them clearly."
                            )))
                        elif effect.get("type") == "door_close":
                            recent_events.append((turn_num, (
                                f"{ts} | The hewn opening in the west "
                                f"wall of the Echo Chamber grinds shut "
                                f"to a hairline crack again."
                            )))

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

            cr = await turn_cycle.narrate_turn(
                intent, output, adjudication, "",
                resolution_log=attack_log if attack_log else None,
                character_pronouns=character_pronouns,
                perception=context.perception,
            )
            turn_result.character_results.append(cr)

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
            history_entry = ""
            spoken = cr.output.spoken or ""
            action = (cr.output.action or "").strip()
            if spoken.strip() and spoken.strip().lower() not in (
                "(silent)", "(silence)",
            ):
                cs = characters[cr.character_id]
                handle = cs.scene_handle or cr.character_id
                history_entry += (
                    f'\n{handle} says: "{spoken.strip()}"'
                )
            if action:
                cs = characters[cr.character_id]
                handle = cs.scene_handle or cr.character_id
                history_entry += f"\n{handle} acts: {action}"
            if cr.narration.prose:
                history_entry += f"\n{cr.narration.prose}"
            if history_entry:
                within_turn_history += history_entry

        await _broadcast_turn_results_to_transports(
            turn_result=turn_result,
            characters=characters,
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
            history_entry = ""
            if spoken.strip() and spoken.strip().lower() not in (
                "(silent)", "(silence)",
            ):
                cs = characters[cr.character_id]
                handle = cs.scene_handle or cr.character_id
                history_entry += (
                    f'\n{handle} says: "{spoken.strip()}"'
                )
            if action:
                cs = characters[cr.character_id]
                handle = cs.scene_handle or cr.character_id
                history_entry += f"\n{handle} acts: {action}"
            if cr.narration.prose:
                history_entry += f"\n{cr.narration.prose}"
            if history_entry:
                scene_history += history_entry

        # Move current-turn ledger entries into the sliding window
        ledger.flush_turn()

        # Advance scene-level spell effect durations once per completed turn.
        spell_resolver.tick_effects(spell_runtime, rounds=1)

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
    character_pronouns: dict[str, str] | None = None,
    start_turn: int = 1,
    initial_history: str = "",
    initial_active_characters: set[str] | None = None,
    initial_positions: Optional[dict[str, tuple[float, float, str]]] = None,
    initial_party_examination_state: Optional[dict[tuple[str, str], dict]] = None,
    initial_spell_runtime: Optional[SpellRuntimeState] = None,
) -> SessionResult:
    """Run a complete game session and return all results.

    Wraps ``iter_session`` for the common single-scene case.  Use
    ``iter_session`` directly when you need to interleave multiple scenes
    turn-by-turn (e.g. ``run_all.py``).
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
        character_pronouns=character_pronouns,
        initial_active_characters=initial_active_characters,
        initial_positions=initial_positions,
        initial_party_examination_state=initial_party_examination_state,
        initial_spell_runtime=initial_spell_runtime,
    ):
        turns.append(turn_result)

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

