"""Load consumables (food & drink) into Thing templates with authored effects.

Mirrors ``engine.weapon_loader``: a markdown catalog
(``scenario/things/CONSUMABLES.md``) of edible/drinkable Things, each with an
``effects`` column parsed into ``models.thing.Effect``s. A character's
``provisions`` list (from IDENTITY) instantiates copies of these into their kit
so ``eat``/``drink`` can act on them through the unified manipulation dispatch.

Effect spec grammar (comma-separated in the catalog's ``effects`` column):
  ``heal N``            -> restore N HP
  ``status <name>``     -> add a status condition
  ``<dim> <delta>``     -> a neurochemical nudge, when <dim> is one of the seven
                           canonical dimensions (dopamine, cortisol, ...)
  ``<name> <delta>``    -> a character stat in the condition's extensions bucket
                           (hunger / thirst / fatigue / intoxication / ...)
Deltas are signed floats (``-0.4``, ``+0.05``).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from models.condition import DIMENSIONS
from models.thing import Effect, Interaction, Thing, derive_affordances


def parse_effect(spec: str) -> Optional[Effect]:
    """Parse one authored effect spec into an :class:`~models.thing.Effect`."""
    parts = (spec or "").split()
    if not parts:
        return None
    head = parts[0].lower()
    if head == "heal":
        try:
            return Effect(kind="heal", payload={"amount": int(float(parts[1]))})
        except (IndexError, ValueError):
            return None
    if head == "status":
        name = " ".join(parts[1:]).strip()
        return Effect(kind="status", payload={"name": name}) if name else None
    if head == "ac":
        try:
            return Effect(kind="ac", payload={"bonus": int(float(parts[1]))})
        except (IndexError, ValueError):
            return None
    if len(parts) >= 2:
        try:
            delta = float(parts[1])
        except ValueError:
            return None
        if head in DIMENSIONS:
            return Effect(kind="neuro", payload={"dim": head, "delta": delta})
        return Effect(kind="stat", payload={"name": head, "delta": delta})
    return None


def parse_effects(cell: str) -> list[Effect]:
    """Parse a comma-separated ``effects`` cell into a list of Effects."""
    out: list[Effect] = []
    for spec in (cell or "").split(","):
        eff = parse_effect(spec.strip())
        if eff is not None:
            out.append(eff)
    return out


def parse_contents(cell: str) -> list[tuple[str, int]]:
    """Parse a container's ``contents`` cell — ``id`` or ``id xN`` / ``id×N``,
    comma-separated — into (catalog_id, quantity) pairs."""
    out: list[tuple[str, int]] = []
    for part in (cell or "").split(","):
        m = re.match(r"^([a-z0-9_]+)(?:\s*[x×]\s*(\d+))?$", part.strip(), re.IGNORECASE)
        if m:
            out.append((m.group(1).lower(), int(m.group(2)) if m.group(2) else 1))
    return out


def make_thing(cid: str, name: str, kind: str, effect_specs) -> Thing:
    """Build a catalog Thing of a given ``kind``: ``eat``/``drink`` (a consumable
    with the matching interaction → EDIBLE/DRINKABLE), ``tool`` (holdable, usable)
    or ``wearable`` (occupies a body slot), plus any parsed effects."""
    from models.thing import CONTAINER, HOLDABLE, TOOL, WEARABLE
    kinds = [k.strip().lower() for k in (kind or "").split(",") if k.strip()]
    interactions = []
    if any(k in ("eat", "edible") for k in kinds):
        interactions = [Interaction(verb="eat", response=f"You eat the {name.lower()}.")]
    elif any(k in ("drink", "drinkable") for k in kinds):
        interactions = [Interaction(verb="drink", response=f"You drink the {name.lower()}.")]
    thing = Thing(id=cid, label=name, pickable=True,
                  description=f"{name}.", interactions=interactions)
    for spec in effect_specs:
        eff = spec if isinstance(spec, Effect) else parse_effect(str(spec))
        if eff is not None:
            thing.effects.append(eff)
    derive_affordances(thing)
    # Each kind adds its affordance (a Thing may have several, e.g.
    # "wearable, container"). A shield is HAND-HELD (holdable), not worn — its AC
    # comes from an `ac +N` effect that stacks on worn armor.
    for k in kinds:
        if k == "tool":
            thing.affordances.update({TOOL, HOLDABLE})
        elif k in ("wearable", "worn", "armor"):
            thing.affordances.add(WEARABLE)
        elif k in ("shield", "held", "holdable"):
            thing.affordances.add(HOLDABLE)
        elif k == "container":
            thing.affordances.add(CONTAINER)
    return thing


def make_consumable(cid: str, name: str, kind: str, effect_specs) -> Thing:
    """Back-compat alias: build an edible/drinkable Thing (see make_thing)."""
    return make_thing(cid, name, "drink" if kind.strip().lower().startswith("drink")
                      else "eat", effect_specs)


def _parse_table(text: str) -> list[dict[str, str]]:
    """Parse the first markdown table in ``text`` into row dicts."""
    lines = [ln for ln in text.split("\n")]
    header: list[str] = []
    rows: list[dict[str, str]] = []
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            if header:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if re.match(r"^[\s\-:|]+$", s.strip("|")):  # separator row
            continue
        if not header:
            header = [c.lower() for c in cells]
            continue
        rows.append({header[i]: cells[i] for i in range(min(len(header), len(cells)))})
    return rows


def load_catalog(path: Path, default_kind: str = "eat") -> dict[str, Thing]:
    """Parse a markdown catalog (id | name | kind | effects) into id -> Thing
    templates. Works for CONSUMABLES.md (eat/drink) and GEAR.md (tool/wearable)
    — the ``kind`` column drives the affordance."""
    if not path.exists():
        return {}
    lib: dict[str, Thing] = {}
    for row in _parse_table(path.read_text()):
        cid = (row.get("id") or "").strip()
        if not cid:
            continue
        thing = make_thing(
            cid, (row.get("name") or cid).strip(),
            (row.get("kind") or default_kind).strip(), parse_effects(row.get("effects", "")))
        thing.contents = parse_contents(row.get("contents", ""))
        lib[cid] = thing
    return lib


def load_consumables(path: Path) -> dict[str, Thing]:
    """Parse CONSUMABLES.md into id -> Thing templates (edible/drinkable)."""
    return load_catalog(path, default_kind="eat")


def load_gear(path: Path) -> dict[str, Thing]:
    """Parse GEAR.md into id -> Thing templates (tools, wearables, trinkets)."""
    return load_catalog(path, default_kind="wearable")
