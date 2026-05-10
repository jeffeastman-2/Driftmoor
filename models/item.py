"""Item and Interaction dataclasses for scene contents.

See ``specs/CONTENTS.md`` for the file-format specification this module
parses against. ``models.contents_loader`` builds these objects from a
``CONTENTS.md`` file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Interaction:
    """A single ``<verb> [(condition)] → <response>`` adjudication entry.

    Attributes:
        verb: Canonical verb (the first phrasing listed in the source).
        aliases: Other verbs that resolve to this interaction.
        condition: Free-text precondition (parenthetical in the source);
            empty string when no condition was given.
        response: DM-authoritative result text.
    """

    verb: str
    aliases: list[str] = field(default_factory=list)
    condition: str = ""
    response: str = ""

    def matches(self, candidate: str) -> bool:
        """True if ``candidate`` (case-insensitive) matches verb or any alias."""
        c = candidate.strip().lower()
        if c == self.verb.lower():
            return True
        return any(c == a.lower() for a in self.aliases)


@dataclass
class Item:
    """A scene-level item parsed from a CONTENTS.md ``### <item_id>`` block.

    Position/zone are populated from the corresponding GEOMETRY.md entry
    when the loader is given access to a ``SceneGeometry``; otherwise they
    remain ``None``.
    """

    id: str
    description: str = ""

    # Properties (parsed from the italicized parenthetical line)
    pickable: bool = False
    flavor_only: bool = False
    pressable: bool = False
    quest_item_for: Optional[str] = None
    extra_facts: list[str] = field(default_factory=list)

    # Cross-reference: when set, interactions were inherited from this item id.
    interactions_ref: Optional[str] = None

    # List of interactions in source order. The same verb may appear more
    # than once with different conditions (e.g. ``press (when crack is
    # closed)`` vs ``press (when crack is open)``); look-up logic should
    # iterate and match on verb + (optionally) condition.
    interactions: list["Interaction"] = field(default_factory=list)

    # Spatial (populated from GEOMETRY.md by the loader if available)
    position: Optional[object] = None  # models.space_time.Position
    zone: Optional[str] = None
    label: str = ""

    # Mutable runtime state — not parsed; engine maintains these.
    holder: Optional[str] = None
    state: dict[str, str] = field(default_factory=dict)
    discovered_by: set[str] = field(default_factory=set)

    def find_interaction(self, verb: str) -> Optional["Interaction"]:
        """Return the first interaction matching ``verb`` (or alias)."""
        for interaction in self.interactions:
            if interaction.matches(verb):
                return interaction
        return None

    def find_interactions(self, verb: str) -> list["Interaction"]:
        """Return ALL interactions matching ``verb`` (or alias).

        Useful when the same verb is listed multiple times with distinct
        conditions; callers can then pick by condition match.
        """
        return [i for i in self.interactions if i.matches(verb)]
