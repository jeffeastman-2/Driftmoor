"""DriftmoorSceneAdapter — grounds LATN noun phrases against the live world.

Implements Engraf's ``SceneAdapter`` protocol (the parser's only window onto a
world): given a parsed ``NounPhrase``, return the world entities it could refer
to, ranked best-first. The parser owns grammar; this owns *what exists* and
*how matching works*.

Grounds two entity kinds, by the rule we settled on:

* **Items** — matched by STRING against id/label (identity lives in the label)
  AND against each item's ``appearance_bands`` text, since perception shows the
  player how a thing *looks* ("a low shadow at the foot of the west wall"), not
  its label ("Discarded pack"). Zone-filtered to the actor's current zone. Wraps
  the same normalization the shallow resolver uses (``_normalize_target`` /
  ``_tokens``). (Distance-correct band selection is the 2b perception-fed
  adapter; here any band can match.)
* **Characters** — matched by VECTOR SIMILARITY over the race/class/role/faction
  one-hot property dims, which this adapter POPULATES on each character's vector
  from its ``Character`` fields (mint-and-populate is one decision). Names and
  scene handles stay STRING-matched (identity, not a property). A character's
  score is the max of its name-string score and its descriptor-similarity score,
  so "Amara", "the cleric", and "the dwarf cleric" all resolve through one path.

Returns the **honest ranked list, ties included** — it never collapses to a
single winner or to None. The "refuse to guess on a tie" / disambiguation
policy lives one level up, in the resolver (per the integration plan), which is
also where 2a (NPC: fall back) and 2b (human: ask) legitimately diverge.

Constructed per actor per turn, closing over that actor's zone (and, in 2b,
perception). Registering the RPG dims is idempotent and done here so the
character property vectors can be built even if no lexicon was built first.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from engine.latn_dimensions import property_dim, register_driftmoor_dimensions

_PROPERTY_FIELDS = (("race", "race"), ("class", "character_class"),
                    ("role", "role"), ("faction", "faction"))


def _xyz(x, y, z=0.0) -> dict:
    return {"x": float(x), "y": float(y), "z": float(z)}


def _item_position(item) -> dict:
    pos = getattr(item, "position", None)
    if pos is not None:
        return _xyz(getattr(pos, "x", 0.0), getattr(pos, "y", 0.0))
    return _xyz(0.0, 0.0)


def _tuple_position(t) -> dict:
    if t and len(t) >= 2:
        return _xyz(t[0], t[1])
    return _xyz(0.0, 0.0)


def _np_text(np) -> str:
    """Surface content text of an NP for string matching: the words it consumed
    minus determiners/prepositions/punctuation, else the head noun."""
    words = []
    for tok in getattr(np, "consumed_tokens", None) or []:
        w = getattr(tok, "word", "") or ""
        if w and not (tok.isa("det") or tok.isa("prep") or tok.isa("punct")):
            words.append(w)
    if words:
        return " ".join(words)
    return getattr(np, "noun", "") or ""


class _ItemEntity:
    """GroundedEntity wrapper for a scene Item (string-matched; vector unused)."""

    def __init__(self, item, vector):
        self._item = item
        self.name = getattr(item, "label", "") or getattr(item, "id", "") or ""
        self.object_id = getattr(item, "id", "") or ""
        self.entity_id = self.object_id
        self.vector = vector
        self.position = _item_position(item)

    @property
    def item(self):
        return self._item

    @property
    def kind(self) -> str:
        return "item"


class _CharacterEntity:
    """GroundedEntity wrapper for a CharacterSession (vector = property dims)."""

    def __init__(self, character_id, session, vector, position):
        self._session = session
        self.character_id = character_id
        self.name = getattr(getattr(session, "character", None), "name", "") or character_id
        self.object_id = character_id
        self.entity_id = character_id
        self.vector = vector
        self.position = position

    @property
    def session(self):
        return self._session

    @property
    def kind(self) -> str:
        return "character"


class DriftmoorSceneAdapter:
    def __init__(
        self,
        *,
        items: Optional[dict] = None,
        characters: Optional[dict] = None,
        actor_zone: str = "",
        current_positions: Optional[dict] = None,
        recent: Optional[Iterable] = None,
    ):
        # Ensure the property dims exist before building character vectors.
        register_driftmoor_dimensions(
            cs.character for cs in (characters or {}).values() if getattr(cs, "character", None)
        )
        from engine.latn import VectorSpace

        self._items = items or {}
        self._characters = characters or {}
        self._actor_zone = (actor_zone or "").upper()
        self._positions = current_positions or {}
        self._recent = list(recent or [])
        self._empty_vector = VectorSpace()  # shared, for string-matched items

        # Property dims present in this scene — used to detect whether a query
        # NP carries descriptor constraints (vs being a pure name lookup).
        self._property_dims = self._collect_property_dims()
        # Pre-build character entities (and their property vectors) once.
        self._char_entities = {
            cid: self._make_character_entity(cid, cs)
            for cid, cs in self._characters.items()
        }

    # -- SceneAdapter protocol -------------------------------------------------

    def resolve_noun_phrase(self, np) -> List[Tuple[float, object]]:
        results: List[Tuple[float, object]] = []
        results.extend(self._match_items(np))
        results.extend(self._match_characters(np))
        results.sort(key=lambda pair: pair[0], reverse=True)
        return results

    def resolve_pronoun(self, pronoun: str) -> List[object]:
        p = (pronoun or "").lower()
        if p in ("they", "them"):
            return [e for _, e in self._all_entities()]
        if p in ("it", "its"):
            return [self._recent[-1]] if self._recent else []
        return []

    # -- internals -------------------------------------------------------------

    def _collect_property_dims(self) -> set:
        dims = set()
        for cs in self._characters.values():
            ch = getattr(cs, "character", None)
            if ch is None:
                continue
            for field, attr in _PROPERTY_FIELDS:
                dim = property_dim(field, getattr(ch, attr, "") or "")
                if dim:
                    dims.add(dim)
        return dims

    def _make_character_entity(self, character_id, cs):
        from engine.latn import VectorSpace

        vector = VectorSpace()
        ch = getattr(cs, "character", None)
        if ch is not None:
            for field, attr in _PROPERTY_FIELDS:
                dim = property_dim(field, getattr(ch, attr, "") or "")
                if dim:
                    vector[dim] = 1.0
        position = _tuple_position(self._positions.get(character_id))
        return _CharacterEntity(character_id, cs, vector, position)

    def _item_entity(self, item):
        return _ItemEntity(item, self._empty_vector)

    def _match_items(self, np) -> List[Tuple[float, object]]:
        from engine.verb_resolver import _normalize_target, _tokens

        target = _np_text(np)
        t = _normalize_target(target)
        if not t:
            return []
        want = _tokens(target)
        out: List[Tuple[float, object]] = []
        for item in self._items.values():
            if self._actor_zone:
                zone = (getattr(item, "zone", "") or "").upper()
                if zone != self._actor_zone:
                    continue
            iid = (getattr(item, "id", "") or "").lower()
            label = (getattr(item, "label", "") or "").lower()
            if t == iid or (label and t == label):
                score = 1.0
            elif label and (label in t or t in label):
                score = 0.85
            elif iid and iid in t:
                score = 0.7
            else:
                cand = _tokens(iid) | (_tokens(label) if label else set())
                shared = want & cand
                score = 0.6 * len(shared) / len(want) if want and shared else 0.0
            # A player can only refer to an item by how it currently LOOKS:
            # perception shows the appearance-band text ("a low shadow at the
            # foot of the west wall"), not the label ("Discarded pack"). So
            # ground the band descriptions too. (Distance-correct band selection
            # — only the band valid at the actor's range — is the 2b
            # perception-fed adapter's job; here any band can match.)
            score = max(score, self._band_score(item, t, want))
            if score > 0:
                out.append((score, self._item_entity(item)))
        return out

    def _band_score(self, item, t: str, want: set) -> float:
        """Match an NP against an item's appearance_bands. A whole-phrase
        substring hit ("low shadow" inside the band) scores high and is
        item-specific; otherwise fall back to token overlap (kept below the
        id/label scores so a real label match always wins)."""
        from engine.verb_resolver import _tokens

        bands = getattr(item, "appearance_bands", None) or {}
        if not isinstance(bands, dict):
            return 0.0
        best = 0.0
        for desc in bands.values():
            d = (desc or "").lower()
            if not d:
                continue
            if t and t in d:
                best = max(best, 0.8)
            elif want:
                shared = want & _tokens(d)
                if shared:
                    best = max(best, 0.55 * len(shared) / len(want))
        return best

    def _match_characters(self, np) -> List[Tuple[float, object]]:
        from engine.verb_resolver import _normalize_target

        target = _np_text(np)
        t = _normalize_target(target)
        vector = getattr(np, "vector", None)
        has_props = bool(self._property_dims) and vector is not None and any(
            vector[d] != 0.0 for d in self._property_dims
        )
        out: List[Tuple[float, object]] = []
        for ent in self._char_entities.values():
            name = (ent.name or "").lower()
            handle = (getattr(ent.session, "scene_handle", "") or "").lower()
            name_score = 0.0
            if t and (t == name or (handle and t == handle)):
                name_score = 1.0
            elif t and ((name and (name in t or t in name))
                        or (handle and (handle in t or t in handle))):
                name_score = 0.85
            desc_score = vector.semantic_similarity(ent.vector) if has_props else 0.0
            score = max(name_score, desc_score)
            if score > 0:
                out.append((score, ent))
        return out

    def _all_entities(self) -> List[Tuple[float, object]]:
        out = [(1.0, self._item_entity(it)) for it in self._items.values()]
        out.extend((1.0, ent) for ent in self._char_entities.values())
        return out
