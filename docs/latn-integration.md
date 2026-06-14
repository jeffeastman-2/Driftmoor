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

1. **`DriftmoorSceneAdapter`** (implements the phase-1 `SceneAdapter`
   protocol, 2 methods) — the world the parser grounds noun phrases against.
   Grounds **items AND characters/creatures**, not items only (a recipient
   like "the cleric" in "give the mace to the cleric" is a grounded
   character NP — see transfer handling in 2a). `GroundedEntity` wraps an
   `Item` *or* a `CharacterSession`; the resolver dispatches on entity kind.
   - `resolve_noun_phrase(np) -> list[(score, GroundedEntity)]` ranked best
     first. Matching is entirely Driftmoor's. **Characters ground by vector
     similarity, not string scoring:** race / class / role / faction / state
     are closed, enumerable, schema-backed properties, so they get one-hot
     dims (one per *value* — `dwarf`, `cleric`, … — since nominal categories
     have no inter-value ordering; a single enum-valued dim would invent
     false similarity). The adapter populates them on each character from
     `Character.race/.class/.role/.faction` (+ state), and Engraf's
     asymmetric `semantic_similarity` ranks — so "the wounded dwarf cleric"
     composes `wounded`+`dwarf`+`cleric` and ranks the right character with
     no bespoke code. This replaces `_resolve_recipient_character`'s
     token-overlap scoring entirely. The only residue is the two *identity*
     channels — `name` (proper noun) and `scene_handle` (free text) — which
     stay exact/substring match (a clean lookup, not fuzzy scoring; never
     mint a dim per name). Roles are the boundary case: closed campaign
     roles get dims, genuinely free-form handles stay string. Item-matching
     still wraps `_match_item`/`_token_match` (item *labels* are identity =
     string); enumerable item properties (magical ← category, state) get
     dims by the same rule.
     - **Returns the honest ranked list, ties included — never collapses
       to `None` itself.** The "refuse to guess on a tie" policy
       (`_token_match`'s unique-winner rule today) moves UP into the
       Driftmoor resolver as a top-margin gate, because that is the seam
       where 2a and 2b legitimately differ: an exact top-score tie →
       `None`/fallback for an NPC (2a, today's behavior preserved exactly)
       vs a disambiguation prompt for a human (2b, "the top glyph or the
       cracked one?"). Existing giving-up tests assert at the resolver
       boundary and stay green. Keeping the adapter a pure ranker is also
       what lets LATN Layer-2 multiply hypotheses over alternatives.
     - **Scope differs by entity kind, and the adapter owns it:** items are
       zone-filtered to the actor's current zone; characters follow
       `_resolve_recipient_character`'s scope (`active_characters` — you can
       hand to anyone present, not just same-zone).
   - `resolve_pronoun(pronoun) -> list[GroundedEntity]` ("it" -> last
     referenced item/creature; "they/them" -> all perceived).
   - `GroundedEntity` = `name`, `vector` (a `VectorSpace`), `object_id`,
     `entity_id`, `position` dict with `'x'/'y'/'z'` keys (feet; z = 0.0).
     A thin wrapper over `Item` / `CharacterSession` does it.
   - **Construct one adapter per actor per turn**, closing over that actor's
     zone (and, in 2b, their perception list). Zone is NOT passed into
     `resolve_noun_phrase` — that signature is the frozen phase-1 protocol
     shared with Engraf. Rebuild the executor per turn, or reuse one and
     call `executor.update_scene_model(adapter)` (phase-1 ships this).
2. **`Lexicon`** — **layered and world-scoped, not per-scene** (decided).
   The lexicon answers "what can be *said*" (tokenization competence); the
   SceneAdapter answers "what can be *referred to* right now" (perception/
   zone rules stay there). Scoping the lexicon to the perceived scene would
   smuggle world rules into the tokenizer, produce wrong failure modes
   ("look for the shadowbeast" should parse cleanly and fail *grounding*,
   yielding "you don't see one here" — not fail to parse), and leak hidden
   scene contents through parse-quality differences. Include everything,
   hidden items too: the lexicon is internal, and uniform inclusion makes
   refusals uniform. Layers (a `ChainMap` satisfies the Lexicon facade's
   MutableMapping contract, so the phase-1 seam is unchanged):
   1. *Function-word base* — closed-class words (the/a/it, prepositions,
      conjunctions, negation, modals, to-be, question words), ideally
      factored out of Engraf's `vocabulary.py` into a shared module
      (small Engraf-side task: split function words from CAD content).
   2. *RPG layer* (static) — verb entries with intent dims (e.g.
      `'inspect': vector_from_features("verb action examine")`); the
      **character-property vocabulary carrying its one-hot dims** (race /
      class / faction / enumerable roles — `'cleric': vector_from_features(
      "noun", cleric=1.0)`), since these are D&D vocabulary, not per-world;
      and player-typed prose adjectives ("cracked", "glowing", "top") as
      POS-only.
   3. *World/campaign layer* (near-static) — character **names**
      (`proper_noun`; lowercased), place names, and item nouns. These are
      *identity*, so **POS-only** (`vector_from_features("noun")`) and
      matched by the adapter's string/exact logic — no hand-authored
      semantic vectors (property dims live in the RPG layer above; only the
      adapter's *population* of them from world data happens here). Generated
      mechanically from world data. Multi-word labels become compound
      entries (up to 3-word compounds supported); normalize parentheticals
      ("Trigger glyph (top)").
   4. *Scene layer* (thin) — only vocabulary spawned at runtime.
   Scale is a non-issue (dict lookup is O(1); compound search scales with
   input length, not lexicon size). Free text beyond world nouns ("I shout
   a warning") still contains unknowns — absorbed by the shallow-resolver
   fallback. Activate per parse with `use_lexicon(driftmoor_lexicon)`.
3. **`VPGroundingPolicy`** — start with `PermissiveVPPolicy`. The Engraf
   default is fail-closed against its CAD verb ontology and would reject
   every Driftmoor verb phrase. DM-Left already adjudicates action validity
   downstream; Layer 4 does not need to.
4. **`SpatialPolicy`** — `EngrafSpatialPolicy(proximity_threshold=<feet>)`
   if/when spatial PPs ("behind the obelisk") are wanted; not needed for
   the initial verb-resolver scope.

**Rules for determining when new vector dimensions are needed.**
Dimensions are the engine's semantics; everything else is opaque string
data the adapter compares literally. The whole vector is really a
three-tier contract:

1. **POS dims** — the parser decides structure with them (is this a noun?
   does the NP parse?).
2. **Non-POS dims (verb intents, properties)** — the engine decides
   behavior with them: branch on `isa('take')`, match `magical` against
   `Thing.category`. Anything the engine must reason about lives here.
3. **Raw words (the NP's consumed tokens)** — matched as literal text
   against world text (labels, descriptions). The engine never knows what
   "banded" means; it only knows it appears in the label.

**Verbs use the vector-dimension mechanism (decided).** Two artifacts, not
one: the **schema** (`VECTOR_DIMENSIONS` — the named axes every vector has;
shared across domains) and the **lexicon tables** (word → vector; one per
domain, swapped per parse via `use_lexicon`). The "RPG verb-intent block"
is a *schema* addition — ~7 new axes — not vocabulary. All vocabulary
differences live in the tables, where a common word with different senses
("place": Engraf `organize`, Driftmoor transfer) is simply a different
entry in each table. Verbs are the only word class needing new axes,
because they're the only class downstream code dispatches on
(`vp.vector.isa('examine')`): prepositions reuse the existing
spatial/directional dims (interpretation differences belong to
SpatialPolicy, not the lexicon), and adverbs are degree-shared or POS-only.
**Adjectives split by what they refer to:** descriptors that exist only as
label/description prose ("banded", "gnarled") are POS-only
(`vector_from_features("adj")`; the words reach the adapter via the NP's
consumed tokens and are string-matched). Descriptors that name a
**schema-backed world property** get a property dim in the RPG block —
e.g. `'magic': vector_from_features("adj", magical=1.0)` backed by
`Thing.category`; faction (hostile/friendly ← `Character.faction`);
enumerable states (open/closed/lit ← `Item.state` / `Place.dynamic_state`);
and character race/class/role (← `Character.race/.class/.role`), which is
how character NPs ("the dwarf cleric") ground by similarity instead of
string scoring. **Nominal categories are encoded one-hot — one dim per
*value* (`dwarf`, `elf`, `cleric`), never one enum-valued dim** — because
the values have no inter-value ordering and a numeric encoding would invent
false similarity. Identity (item labels, character names, `scene_handle`)
is the exception that stays string/exact, not a dim. The dim is an
interlingua between query NP and entity vector, so **minting a dim and
populating it in the adapter's entity vectorization are one decision** — an
unpopulated dim makes qualified queries match nothing, worse than string
matching.
Color/size dims already exist and may be reused if (and only if) entity
vectors populate them. Test for new dims: does the word answer a question
the engine can already answer from data? This keeps the block bounded —
closed, enumerable, schema-backed properties only.
Driftmoor's `_VERB_LEXICON` and Engraf's verb-intent dims are the same
design — the canonical verb is the dimension, the synonym list is the set
of words that activate it. Rather than run a parallel word→canonical mapping after the
parse, add an **RPG verb-intent block** to `VECTOR_DIMENSIONS` (and
`SEMANTIC_DIMENSIONS`): `examine, search, read, press, take, drop, give`
(no collisions with Engraf's block; keep the two blocks disjoint — don't
reuse Engraf dims for near-miss RPG meanings). Lexicon entries then carry
the canonical intent (`'inspect': vector_from_features("verb action
examine")`) and the resolver dispatches on `vp.vector.isa('examine')`.
Why dims beat word-recovery: (1) inflected verbs get the *root's vector*
but keep the surface word at Layer-1, so `isa('examine')` works on
"studying the glyph" with no extra stemming; (2) the dim composes into the
VP vector and survives conjunctions per-VP; (3) a future `DriftmoorVPPolicy`
can key off the dims in the same idiom as `EngrafVPPolicy`. This resolves
the shared-vs-per-domain schema fork in favor of **one shared schema with
labeled per-domain blocks**; the deferred #3a (per-domain `VectorSchema`)
remains unnecessary. Cost accepted: the schema is a coordinated namespace,
and any stale L6 model checkpoints are invalidated (already deprioritized).
First 2a task on the Engraf side: append the RPG dim block (additive;
`VECTOR_LENGTH` is computed dynamically, Engraf ignores the new dims).

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

1. Build the three Driftmoor pieces: `DriftmoorSceneAdapter` (grounds
   zone-filtered items + active characters; constructed per actor per turn),
   the layered `Lexicon` builder, and activate `PermissiveVPPolicy` around
   parses.
2. Reimplement the resolver pipeline behind the existing signatures:
   parse `intent_text` at Layer 4/5 → take the best hypothesis's
   `VerbPhrase`(s) → canonical verb from the VP's intent dimension
   (`vp.vector.isa('examine')` etc.) → Item from the grounded object NP
   (`vp.noun_phrase` grounding) → `Interaction` via the existing
   `_find_by_verb` / `_pick_by_condition` logic, which stays as-is.
   Apply the unique-winner gate here (top-score margin on the grounding
   candidates) so today's refuse-to-guess behavior is preserved.
   For transfer verbs (`give`/`hand`), resolve the recipient from the
   `to`-PP's NP (it carries the `directional_target` dim) through the same
   adapter — grounding a character, not an item. `_VERB_LEXICON` /
   `_TRANSFER_LEXICON` and `_resolve_recipient_character` don't disappear —
   their (canonical, synonyms) and descriptor-scoring data migrate from
   regex machinery to the source for generating lexicon entries and the
   adapter's character-matching.
3. Keep the shallow resolver as a **fallback** when the parse fails or
   grounds nothing — same philosophy as the current examine fallback. This
   makes the rollout safe: LATN can only improve resolution, never lose it.
   The fallback matters because the two approaches fail differently:
   keyword grep is immune to syntax (it finds "press" anywhere in rambling
   NPC prose), while LATN must parse — and its grammar grew up on
   command-style sentences, not narrative inner monologue. Expect
   human-typed commands (2b) to parse better than NPC LLM prose (2a).
4. **Acceptance test before cutover:** replay logged NPC intent texts
   through LATN headlessly and **categorize each outcome into a taxonomy**,
   not a raw agreement %. A percentage punishes the cases LATN is *designed*
   to win (where disagreement is the goal). Buckets:
   - **agree** — LATN == shallow. Baseline.
   - **LATN-win** — LATN correct, shallow wrong: negation ("don't touch"),
     modality ("I resist the urge to press"), inflection ("pressing", which
     `\bpress\b` misses today), syntactic roles ("take the mace from the
     altar"), pronouns, conjunctions, *and* shallow false-positives LATN
     correctly avoids. Good — do not penalize.
   - **grammar-gap** — LATN failed/misparsed where shallow was right. The
     triage backlog.
   - **grounding-miss** — parsed fine but grounded wrong/nothing where
     shallow matched. Adapter/lexicon tuning.
   Cutover gate: grammar-gap and grounding-miss are small and triaged,
   LATN-wins net positive — not "agreement ≥ X%". The fallback (step 3)
   means grammar-gaps don't regress live regardless.
5. `detect_transfer_verb` can be backed by the same parse (transfer verbs are
   just lexicon entries), or left keyword-based initially — scope choice.

This seam benefits **all** characters immediately — LLM NPC intents flow
through the same resolver — and is testable headlessly (the LATN core has no
heavy deps).

Note the role boundary: LATN never replaces Player-Left's *decision*
function (agency from SOUL/IDENTITY/condition/perception); it replaces
*output structuring*. Follow-on once 2a is solid: relax Player-Left's rigid
`**INTENT**/**MOVEMENT**/**TARGET**` output format — the LLM writes one
natural sentence and LATN extracts the target (later, movement via spatial
PPs) more reliably than regex over self-reported sections. In 2b the same
boundary means the human supplies the decision and LATN the structuring;
nothing "replaces" the LLM because the human took its job.

**Resolved design question — multiple actions per turn:** conjunctive
intents parse as a `ConjunctionPhrase` whose `.phrases` is a list of
`VerbPhrase`s, so "pick up the mace and hand it to Amara" yields two
resolvable actions. Implemented as `engine.latn_resolver.resolve_actions(...)
-> list[ResolvedAction]`, with `resolve_item_interaction` as the drop-in
first-result wrapper (shallow fallback) so the existing turn loop works
unchanged until `session.py` is ready to sequence and narrate multi-action
turns (a session-loop design task: ordering, partial failure, per-action
narration).

**Open TODO — cross-clause pronoun anaphora (LATN-core):** the "it" in "pick
up the mace and give **it** to Amara" can't resolve at parse time — it's
grounded eagerly at L2 against parse-time recency, which can't see an
antecedent created/referenced by an earlier clause of the *same* sentence.
**This is a LATN-core problem, not Driftmoor-specific** — native Engraf has
it too: `execute_layer4("create a box and move it to [1,2,3]")` on an empty
scene yields **0 VPs** ("it" doesn't ground, the `move` VP fails
`EngrafVPPolicy`, the parse is dropped), whereas "move it" with the box
pre-existing grounds fine. Agreed model: **a pronoun is *always* a deferred
grounding promise**, forced by the executor against the recency at force-time
(seeded with scene/turn referents, extended per clause) — uniform across
single-clause and conjunction. Root fix belongs in Engraf
(`resolve_pronoun` / L2 grounding); the executor (Engraf's interpreter,
Driftmoor's `resolve_actions`) supplies the running recency and forces the
promise. TODO marked in `engine/latn_resolver.py`; needs an Engraf-side
breadcrumb near `resolve_pronoun` too.

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
- **Lexicon curation**: nouns and names are now generated from world data
  (resolved above); the remaining curation question is the *adjective*
  vocabulary players will actually type ("cracked", "glowing", "top").
  Start small; unknown adjectives degrade gracefully to noun-only matching.
- ~~**Vector-space fork**~~ (resolved): one shared schema with labeled
  per-domain verb-intent blocks (see "Verbs use the vector-dimension
  mechanism" above). Per-domain schemas (#3a) stay unnecessary unless the
  shared namespace becomes a coordination problem later.
