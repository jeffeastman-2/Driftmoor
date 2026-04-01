"""Top-level game state — central registry and lookup for all entities."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.character import Character, PlayerCharacter, NPC
from models.place import Place


@dataclass
class GameState:
    """Central registry holding all characters, places, and turn state.

    Entities reference each other by string ID.  This class provides
    the lookup methods that resolve those IDs to objects.
    """

    characters: list[Character] = field(default_factory=list)
    places: list[Place] = field(default_factory=list)
    turn: int = 0

    # ---- internal indexes, built lazily ----
    _characters_by_id: dict[str, Character] = field(
        default_factory=dict, init=False, repr=False,
    )
    _places_by_id: dict[str, Place] = field(
        default_factory=dict, init=False, repr=False,
    )

    def __post_init__(self) -> None:
        self._rebuild_indexes()

    def _rebuild_indexes(self) -> None:
        self._characters_by_id = {c.id: c for c in self.characters}
        self._places_by_id = {p.id: p for p in self.places}

    # ------------------------------------------------------------------
    # Character lookups
    # ------------------------------------------------------------------

    def get_character(self, character_id: str) -> Character | None:
        return self._characters_by_id.get(character_id)

    def get_players(self) -> list[PlayerCharacter]:
        return [c for c in self.characters if isinstance(c, PlayerCharacter)]

    def get_npcs(self) -> list[NPC]:
        return [c for c in self.characters if isinstance(c, NPC)]

    def get_characters_at(self, place_id: str) -> list[Character]:
        return [c for c in self.characters if c.location == place_id]

    # ------------------------------------------------------------------
    # Place lookups
    # ------------------------------------------------------------------

    def get_place(self, place_id: str) -> Place | None:
        return self._places_by_id.get(place_id)

    def get_parent(self, place_id: str) -> Place | None:
        place = self._places_by_id.get(place_id)
        if place is None or place.parent_id is None:
            return None
        return self._places_by_id.get(place.parent_id)

    def get_children(self, place_id: str) -> list[Place]:
        place = self._places_by_id.get(place_id)
        if place is None:
            return []
        return [
            self._places_by_id[cid]
            for cid in place.children
            if cid in self._places_by_id
        ]

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def move_character(self, character_id: str, place_id: str) -> None:
        character = self._characters_by_id.get(character_id)
        if character is None:
            raise KeyError(f"Unknown character: {character_id!r}")
        if place_id not in self._places_by_id:
            raise KeyError(f"Unknown place: {place_id!r}")
        character.location = place_id

    def advance_turn(self) -> None:
        self.turn += 1
