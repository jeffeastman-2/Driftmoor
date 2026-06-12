# LATN Parser Integration (Phase 2)

> Status: **ready to start.** The LATN API is now firm: Engraf phase 1
> (decoupling the LATN core behind injectable seams) is complete as of
> 2026-05-20. This document is the phase-2 integration plan on the
> Driftmoor side.

## Background

The project owner has a **Layered Augmented Transition Network (LATN)** parser,
modularized in Python under the **ENGRAF** package. It was originally built for
a 3D graphics world. Notable properties:

- Strong at parsing **verb phrases**, including **conjunctive phrases** such as
  "pick up the mace **and** hand it to Amara".
- Uses **by-design (not learned) vector embeddings** for the vocabulary.

Engraf phase 1 factored the LATN core (Layers 1–5) away from everything
CAD/Engraf-specific. The core no longer depends on Engraf's scene model,
vocabulary, verb rules, spatial thresholds, or the Layer-6 LLM experiment —
each is an injectable seam with an Engraf default. Driftmoor supplies its own
implementations without forking the parser. The five seams landed as commits
on Engraf `main`: `24358a8` (SceneAdapter), `545c0b4` (Lexicon), `0621272`
(VPGroundingPolicy), `cc53691` (SpatialPolicy), `6dc3a0d` (L6 extraction).

**Dependency:** until phase 3 (physical repackaging) the LATN core lives
inside the Engraf repo (`engraf.lexer.*`, `engraf.atn.*`, `engraf.pos.*`,
`engraf.utils.*`, `engraf.An_N_Space_Model.*`). The core needs only `numpy`.
Install Engraf as an editable path dependency for now; the import surface
below is what phase 3 will lift into a standalone `latn` package, so code
written against it now survives the move.

## The LATN API Driftmoor codes against

One entry point and four injectable seams:

```python
from engraf.lexer.latn_layer_executor import LATNLayerExecutor
from engraf.lexer.scene_adapter import SceneAdapter, GroundedEntity   # protocol
from engraf.lexer.lexicon import Lexicon, use_lexicon
from engraf.lexer.vp_policy import PermissiveVPPolicy, use_vp_policy
from engraf.lexer.spatial_policy import EngrafSpatialPolicy, use_spatial_policy

executor = LATNLayerExecutor(my_scene_adapter)      # or None = parse-only
result = executor.execute_layer5(intent_text)       # Layer5Result
# result.hypotheses[0] -> best parse; VPs/NPs with grounding attached
```

What Driftmoor implements:

1. **`SceneAdapter`** (protocol, 2 methods) — the world the parser grounds
   noun phrases against:
   - `resolve_noun_phrase(np) -> list[(score, GroundedEntity)]` ranked best
     first. Matching algorithm is entirely Driftmoor's (wrap the existing
     `_match_item`/`_token_match` logic, zone-restricted).
   - `resolve_pronoun(pronoun) -> list[GroundedEntity]` ("it" -> last
     referenced item/creature; "they/them" -> all perceived).
   - `GroundedEntity` = `name`, `vector` (a `VectorSpace`), `object_id`,
     `entity_id`, `position` dict with `'x'/'y'/'z'` keys (feet; z = 0.0).
     A thin wrapper over `Item` / perceived creature does it.
2. **`Lexicon`** — built **per scene/turn**, since item labels and character
   names vary. Layer-1 tokenization only types words that are in the active
   lexicon (unknown words degrade the parse), so register: the RPG verb
   vocabulary (`_VERB_LEXICON` + `_TRANSFER_LEXICON` phrases, as
   `vector_from_features("verb action")`), item labels and character names
   as nouns (multi-word labels like "shimmering patch" are supported — the
   tokenizer tries up to 3-word compounds), and zone/feature nouns. Activate
   per parse with `use_lexicon(scene_lexicon)`.
3. **`VPGroundingPolicy`** — start with `PermissiveVPPolicy`. The Engraf
   default is fail-closed against its CAD verb ontology and would reject
   every Driftmoor verb phrase. DM-Left already adjudicates action validity
   downstream; Layer 4 does not need to.
4. **`SpatialPolicy`** — `EngrafSpatialPolicy(proximity_threshold=<feet>)`
   if/when spatial PPs ("behind the obelisk") are wanted; not needed for
   the initial verb-resolver scope.

**Verbs need no new vector dimensions.** The canonical verb is recovered
from the parsed `VerbPhrase.verb` word (e.g. "examine", "take"), not from
verb-intent dimensions. The open Engraf-side question of one-shared-vs-
per-domain vector schemas therefore does **not** block phase 2; it only
arises if Driftmoor later wants semantic (dimension-level) verb validation.

## What it replaces

Today, intent → action resolution lives in
[`engine/verb_resolver.py`](../engine/verb_resolver.py). It is deliberately
shallow: keyword/phrase detection (`_VERB_LEXICON`, `_TRANSFER_LEXICON` +
`detect_transfer_verb`) and string-based item matching (`_match_item`:
id/label exact, substring, token-overlap), **not** sentence parsing. Current
limitations the LATN parser addresses:

- **Single verb + single target per intent** — no compound/conjunctive actions.
- **Heuristic item matching** — no pronoun resolution, no adjective/descriptor
  discrimination ("the *cracked* glyph"), ambiguity handled by giving up.

## Integration plan

### Phase 2a — LATN-backed verb resolver (do this first)

`engine/verb_resolver.py` is the single choke point the turn loop calls:

- `resolve_item_interaction(...) -> (Item, Interaction) | None`
- `infer_interaction_target(...) -> target str | None`

The turn-loop branching in `engine/session.py` (transfer / puzzle / examine)
keys off the **returned canonical verb + item**, so preserving that contract
minimizes churn. Plan:

1. Build the three Driftmoor pieces: `ItemSceneAdapter` (wraps the
   zone-filtered `items` dict), per-scene `Lexicon` builder, and activate
   `PermissiveVPPolicy` around parses.
2. Reimplement the resolver pipeline behind the existing signatures:
   parse `intent_text` at Layer 4/5 → take the best hypothesis's
   `VerbPhrase`(s) → canonical verb from `vp.verb` (mapped through the
   existing canonical groups) → Item from the grounded NP (`vp.noun_phrase`
   grounding) → `Interaction` via the existing `_find_by_verb` /
   `_pick_by_condition` logic, which stays as-is.
3. Keep the shallow resolver as a **fallback** when the parse fails or
   grounds nothing — same philosophy as the current examine fallback. This
   makes the rollout safe: LATN can only improve resolution, never lose it.
4. `detect_transfer_verb` can be backed by the same parse (transfer verbs are
   just lexicon entries), or left keyword-based initially — scope choice.

This seam benefits **all** characters immediately — LLM NPC intents flow
through the same resolver — and is testable headlessly (the LATN core has no
heavy deps).

**Resolved design question — multiple actions per turn:** conjunctive
intents parse as a `ConjunctionPhrase` whose `.phrases` is a list of
`VerbPhrase`s, so "pick up the mace and hand it to Amara" yields two
resolvable actions (with "it" resolving via the adapter's pronoun method).
Add a new list-returning API:

- `resolve_item_interactions(...) -> list[(canonical_verb, Item, Interaction)]`

and keep `resolve_item_interaction` as a thin first-element wrapper so the
existing turn loop works unchanged until `session.py` is ready to sequence
and narrate multi-action turns (a session-loop design task, not a parser
one: ordering, partial failure, and per-action narration).

### Phase 2b — Human player front end (`HumanPlayerLeft`)

The second seam, from the original integration goal: let a human play a
character by typing English. `PlayerLeft.generate_intent(RoleContext) ->
ActionIntent` (`engine/player_router.py`) is the substitution point — for a
human-controlled character the decision LLM is *deleted*, not reimplemented;
the human is the agent and LATN is the parser.

- Reuses everything from 2a (adapter, lexicon, policies), with the adapter
  fed from `RoleContext.perception` (the authoritative visible-entity list)
  instead of the items dict alone.
- Output mapping: grounded NP → `interaction_target`; spatial PP (via
  `SpatialPolicy` + entity positions) → `movement_target` (x, y, z in feet,
  later speed-clamped by the engine as today); the verb and remaining text
  pass through as the free-form `intent` string for DM-Left to adjudicate.
- Parse-failure UX: unlike 2a there is a user to talk to — on a failed or
  ungrounded parse, echo what couldn't be understood and let them rephrase,
  rather than silently falling back.

### Phase 3 — repackaging (unchanged)

Once 2a/2b are working, lift the LATN core out of the Engraf repo into a
standalone package; Engraf and Driftmoor both depend on it. Mechanical —
the import boundary is already test-enforced on the Engraf side.

## Open questions

- **Multi-action turn semantics** (session-loop side): ordering, what happens
  when action 2 depends on action 1's success, how DM-Right narrates a
  sequence. The parser hands over a list; the loop owns the rest.
- **Lexicon curation**: how much RPG vocabulary beyond the per-scene nouns
  (adjectives players will actually type: "cracked", "glowing", "top")
  is needed before NP grounding feels robust. Start small; unknown
  adjectives degrade gracefully to noun-only matching.
- **Vector-space fork** (Engraf-side, deferred): shared extended schema vs
  per-domain schemas. Only matters if Driftmoor later wants dimension-level
  verb semantics; phase 2 proceeds without it.
