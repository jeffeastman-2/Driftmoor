# Economy & Transactions — Implementation Plan

Status: **planned** · Owner: Jeff · Drafted with Claude, 2026-07-14

This plan turns Driftmoor's shops from stage-set into a working economy:
**give / take / buy / sell / steal**, backed by real ownership, a coin purse,
item weight, and a two-party negotiation. It is written so each phase is an
**atomic git commit** — self-contained, leaves the full test suite green, and
can be handed to a fresh agent (e.g. VS Copilot) with no prior context.

---

## 0. Orientation (read first)

**The one idea.** give / take / buy / sell / steal are configurations of a
single primitive: a **transfer of `{ownership, possession, coin}` between two
parties, gated by consent.**

| verb  | ownership moves | possession moves | coin moves | consent |
|-------|:---:|:---:|:---:|---|
| give  | yes | yes | — | giver only |
| drop  | no  | yes (→ world) | — | holder only |
| take (unowned) | yes | yes | — | taker only |
| buy   | yes | yes | payer→seller | both |
| sell  | yes | yes | buyer→seller | both |
| steal | **no** | yes | — | **absent** (owner unaware) |

Note the two orthogonal axes we kept splitting on:

- **possession** = who's holding it / where it sits. Already modelled:
  `Thing.holder`, `Thing.position`, `Thing.zone`, `Thing.carry` (CarryState).
- **ownership** = who it *belongs to*. **New.** A pack left in the rooming
  house is `holder=None, zone=rooming_house, owner=<player>`. Theft is exactly
  "possession moved, ownership didn't."

**Design decisions already settled (do not relitigate):**

1. `owner` is a **new field**, distinct from `holder`.
2. Money is an **integer count of copper pieces** (`_cp`), never a float and
   never separate coin piles. 1 gp = 100 cp. Denominations are a *display
   formatter*, not a data model — one integer means change is always exact.
3. A Thing carries three money-ish numbers, all distinct:
   `value_cp` (base/market worth), `listed_price_cp` (the ask; `None` = **not
   for sale**), and an owner's private sentiment is deferred.
4. `weight_lb` (scalar) is the encumbrance lever. Coins weigh (5e: 50 coins =
   1 lb). Full 3-D volume / bin-packing is **out of scope**.
5. Theft detection = opposed check (Sleight of Hand vs Passive Perception).
   On detection, **emit an event to the owner-agent** and let the NPC
   adjudicate the consequence — do **not** hardcode a penalty table.
6. A negotiation is **multi-round but intra-turn**: world-time is frozen while a
   modal two-party sub-dialogue runs; it commits **one atomic transfer** (or
   none). Only the two participants are involved (no auctions).
7. Stay in **LATN**: buy/sell/steal are verbs the parser grounds, exactly like
   enter/take/give. **No regex intent matching** — extend the verb + entity
   model. (See `docs/latn-integration.md` and the venue-entry precedent.)

**Deferred (explicitly NOT in this plan — do not build):** physical coin
denominations & making change; 3-D volume / packing; magical-item appraisal &
identification; reputation/faction memory of caught theft; re-provisioning /
supply chain; NPC-to-NPC trade.

---

## Codebase map (where things live today)

| System | File(s) |
|---|---|
| Thing model (holder, position, zone, carry, size_ft, quantity, **market facet** `price`/`vendor_id`/`category`, **container facet** `contents`/`capacity`) | `models/thing.py` |
| Thing loading (scene things, shop goods, "materialize kit") | `models/thing_loader.py`, `engine/md_loader.py` |
| Character model (`inventory: list[str]`, hp/ac, ability scores) — **no currency yet** | `models/character.py`, `models/character_loader.py` |
| Transfer primitive (`_apply_item_transfer`, recipient resolution) | `engine/item_transfer.py` |
| Transfer orchestration (`_handle_item_transfer`: holder checks, `[ITEM-TRANSFER]` log) | `engine/session.py` (~2646+) |
| Affordance-gated verb dispatch | `engine/manipulation.py` |
| LATN verb dims | `engine/latn_dimensions.py` (`VERB_DIMS`) |
| LATN verb lexicon (`_TRANSFER_LEXICON`, `_EXTRA_VERB_SYNONYMS`) | `engine/latn_lexicon.py`, `engine/verb_resolver.py` |
| LATN grounding (adapter entities, `resolve_actions`, `_TRANSFER_VERBS`) | `engine/latn_adapter.py`, `engine/latn_resolver.py`, `engine/latn_integration.py` |
| Turn loop (action application) | `engine/session.py` |
| NPC agents (disposition, neurochemical baseline) | `scenario/people/npcs/<id>/{SOUL,IDENTITY}.md`, condition model |
| Shop inventory (authored prose) | each shop's `IDENTITY.md` `## Rates and Services`; `scenario/things/mundane_items.md` |

**Conventions for every phase:**
- Run `.venv/bin/python -m pytest -q` — it must stay green (currently 1247).
- Branch off `main`, commit, fast-forward merge (repo's pattern).
- Add tests in `tests/` alongside the code; each phase ships its own tests.
- Money is always `int` copper. Name money variables/fields with a `_cp` suffix.

---

## Phase 1 — Data model: ownership, value, weight (fields only, no behavior) — ✅ DONE (commit below)

**Goal.** Add the property/value/weight fields to `Thing` and a currency helper.
Pure additive; no verb changes.

> **As built:** the price→`value_cp`/`listed_price_cp`/`owner` derivation lives in
> `Thing.__post_init__` (single source of truth for every construction path,
> including Phase 4's materialize-kit), so `thing_loader.py` needed no edits.
> Explicitly-passed values win; a good with a vendor is for-sale at its value and
> owned by the vendor; a priced scene prop (no vendor) has a value but stays
> not-for-sale and unowned.

**Files.** `models/thing.py`, new `models/currency.py`, `models/thing_loader.py`,
`tests/test_currency.py`, `tests/test_thing.py`.

**Changes.**
- `models/currency.py`:
  - `parse_coins(s: str) -> Optional[int]` — "5 gp" → 500, "2 sp" → 20,
    "7 cp" → 7, "1 gp 4 sp" → 140. Ranges ("2-5 gp") and "Varies" → `None`.
    Denominations: cp=1, sp=10, ep=50, gp=100, pp=1000.
  - `format_coins(cp: int) -> str` — 140 → "1 gp 4 sp"; 0 → "0 cp".
- `models/thing.py` — add to the `Thing` dataclass:
  - `owner: Optional[str] = None` — character id that owns it (`None` = unowned).
  - `value_cp: Optional[int] = None` — base/market worth in copper.
  - `listed_price_cp: Optional[int] = None` — the ask; `None` = **not for sale**.
  - `weight_lb: float = 0.0` — 0 = unspecified.
- `models/thing_loader.py` — at load, populate `value_cp = parse_coins(price)`
  for shop goods; set `listed_price_cp = value_cp` and `owner = vendor_id` for
  goods that come from a shop; leave all three `None`/unset for scene props.

**Acceptance.**
- `parse_coins`/`format_coins` round-trip on a table of cases (incl. `None`).
- A shop good loads with `value_cp` set and `owner == vendor_id`; a scene prop
  loads with `owner=None, listed_price_cp=None`.
- Suite green.

**Commit:** `Economy pt1: Thing gains owner/value_cp/listed_price_cp/weight_lb + currency helpers`
**Depends on:** nothing.

---

## Phase 2 — Purse on characters (integer copper) — ✅ DONE (commit below)

**Goal.** Every character can hold money.

> **As built:** `purse_cp` + `can_afford`/`debit`/`credit` live on the base
> `Character` (so players, NPCs, and creatures all inherit them). The loader
> parses an optional `- **Purse:** …` line (via `_parse_purse` → `currency.parse_coins`)
> at each construction site; absent/unparseable → 0. No character authors a purse
> yet — that's author-side data — but the field is present and integer on every
> loaded character.

**Files.** `models/character.py`, `models/character_loader.py`,
`tests/test_character_loader.py`.

**Changes.**
- `models/character.py` — add `purse_cp: int = 0` to the character base; helpers
  `can_afford(cp) -> bool`, `debit(cp) -> bool` (False + no-op if broke),
  `credit(cp)`.
- `models/character_loader.py` — parse an optional `## Wealth` section /
  `- **Purse:** 15 gp` field via `currency.parse_coins`; default 0 when absent.
- (Data, author-side, not this commit) players get a starting purse; shopkeepers
  get a finite till so selling *to* them is bounded.

**Acceptance.** Characters load with `purse_cp`; `debit` refuses when broke;
`credit`/`debit` are exact-integer; suite green.

**Commit:** `Economy pt2: integer-copper purse on characters`
**Depends on:** Phase 1 (currency.py).

---

## Phase 3 — Generalize the transfer primitive (ownership + coin aware) — ✅ DONE (commit below)

**Goal.** One primitive that moves any subset of {ownership, possession, coin}
atomically. Refactor give/take/drop onto it, behavior-preserving.

> **As built:** `transfer_thing(...) -> TransferResult` in `engine/item_transfer.py`
> wraps the possession leg (`_apply_item_transfer`) with ownership + atomic coin.
> **Coin convention:** the item *recipient* (`to_id`) pays the item *giver*
> (`from_id`) — the buy/sell shape (whoever receives the item pays). Affordability
> is gated before any mutation. give (`move_ownership=True`), drop
> (`move_ownership=False`, `to_id=None`), and take (`move_ownership=` unowned) in
> `session._handle_item_transfer` now route through it. The take site reads
> ownership via `getattr(item_obj, "owner", None)` so duck-typed item stubs still
> work.

**Files.** `engine/item_transfer.py`, `engine/session.py` (`_handle_item_transfer`),
`tests/test_item_transfer.py`.

**Changes.**
- Add `transfer_thing(thing, *, from_id, to_id, move_ownership: bool,
  move_possession: bool, coin_cp: int, characters) -> TransferResult`.
  - Atomic: if `coin_cp > 0` and the payer can't afford it, the whole transfer
    fails and nothing mutates.
  - `move_possession` updates `holder`/`carry`/`position`/`zone` (reuse existing
    `_apply_item_transfer` internals). `move_ownership` sets `thing.owner`.
    `coin_cp` debits payer / credits payee.
- Re-express existing verbs through it: **give** = ownership+possession move;
  **drop** = possession→world, ownership unchanged; **take (unowned)** =
  ownership+possession to taker. Keep the `[ITEM-TRANSFER]` logging.

**Acceptance.** Unit tests: coin+ownership+possession move together or not at all;
payer-broke aborts the whole transfer; give/take/drop unchanged externally
(existing transfer tests still pass). Suite green.

**Commit:** `Economy pt3: ownership+coin-aware transfer primitive; give/take/drop refactored onto it`
**Depends on:** Phases 1–2.

---

## Phase 4 — Structured shop catalog + lazy materialization — ✅ DONE (commit below)

**Goal.** A shop's sellable stock is structured data the engine can transact
against, and each good materializes into a full Thing only when needed.

> **As built:** `models/shop_catalog.py`. The Phase-1 priced goods from
> `load_all_things` (those with a vendor + `listed_price_cp`) are the catalog
> *templates* — no separate parse of the "Rates and Services" prose was needed,
> since the market facet already carries the structured price/owner. `ShopCatalog`
> indexes templates by id and by shop; `CatalogEntry.from_thing` is the light
> display view; `ShopCatalog.materialize(catalog_id, owner=…, zone=…, position=…)`
> deep-copies a template into a fresh shop-owned, unheld Thing with a unique id
> (`<catalog_id>_iN`), so repeated calls yield independent Things and the template
> is never mutated. Session wiring is deferred to Phase 7 (buy/sell).

**Files.** new `models/shop_catalog.py`, `models/thing_loader.py`,
`tests/test_shop_catalog.py`.

**Changes.**
- Define a `CatalogEntry` (catalog_id, name, `value_cp`, `listed_price_cp`,
  `category`, `weight_lb`, source shop id). Parse it from the shop's authored
  inventory — start from `## Rates and Services` in the shopkeeper's IDENTITY.md
  (and/or `scenario/things/mundane_items.md`). Keep the prose; derive structure.
- `materialize_catalog_item(catalog_id, *, owner, zone, position) -> Thing`
  — builds a full Thing on demand (owner=shopkeeper, `holder=None`, placed in the
  shop), reusing the existing "materialize kit" pattern in `thing_loader`.

**Acceptance.** A shop's catalog parses to entries with `listed_price_cp` set;
`materialize_catalog_item` returns a Thing owned by the shopkeeper with the right
price; materializing twice yields two independent Things. Suite green.

**Commit:** `Economy pt4: structured shop catalog + lazy item materialization`
**Depends on:** Phase 1.

---

## Phase 5 — Containers & ownership inheritance (shelves/counters)

**Goal.** Shop furniture (shelves, counters, displays) are container Things owned
by the shopkeeper; their contents inherit that owner.

**Files.** `models/thing.py` (helper), `engine/md_loader.py`, `tests/test_thing.py`.

**Changes.**
- Rule: a Thing whose container has an `owner` inherits that owner unless it sets
  its own. Add `resolve_owner(thing, container)` and apply during load/expansion.
- (Data, author-side) shops declare shelf/counter container Things; their
  `contents` are the catalog goods. **Furniture placement & geometry are Jeff's
  data work** — this commit ships only the inheritance *rule* + a test scene.

**Acceptance.** A good inside a shopkeeper-owned shelf reports
`owner == shopkeeper`; a good that sets its own owner keeps it. Suite green.

**Commit:** `Economy pt5: container ownership inheritance for shop shelves`
**Depends on:** Phases 1, 4.

---

## Phase 6 — `steal` verb + detection check

**Goal.** Taking what you don't own is theft, with a real chance of being caught.

**Files.** `engine/latn_dimensions.py`, `engine/latn_lexicon.py`,
`engine/latn_resolver.py`, `engine/session.py`, new `engine/theft.py`,
`tests/test_theft.py`.

**Changes.**
- Add `steal` to `VERB_DIMS`; add synonyms (steal, pocket, pilfer, filch, swipe,
  lift, palm) to the lexicon; recognize it in the resolver as a transfer verb.
- **`take` of an *owned* Thing routes to the theft path too** (implicit theft);
  bare `steal` makes intent explicit.
- `engine/theft.py`: `attempt_theft(actor, owner, *, rng) -> bool` — opposed
  check, actor Sleight of Hand (Dex mod + prof if proficient) vs owner Passive
  Perception (10 + Wis mod + prof). Pass an injectable `rng` for deterministic
  tests.
  - On the transfer: theft = **possession moves, ownership does NOT** (goods stay
    "stolen" — `thing.owner` unchanged).
  - On **detected**: emit a structured event to the owner-agent (e.g. an injected
    intent / `[THEFT-DETECTED]` ledger entry naming actor + item). The NPC agent
    decides the consequence next turn — **no hardcoded penalty**.

**Acceptance.** `steal the loaf` parses; opposed check runs (seeded); undetected
→ actor holds it, `owner` unchanged; detected → owner-agent event emitted;
`take` of an owned item triggers the same path; `take` of unowned does not.
Suite green (deterministic seed).

**Commit:** `Economy pt6: steal verb + Sleight-vs-Perception detection, consequence via owner-agent`
**Depends on:** Phase 3.

---

## Phase 7 — `buy` / `sell` verbs (the coin leg), auto-accept

**Goal.** Purchase and sale as LATN verbs grounding the catalog, transacting real
coin. Straight accept at listed price — haggling is Phase 8.

**Files.** `engine/latn_dimensions.py`, `engine/latn_lexicon.py`,
`engine/latn_adapter.py` (ground catalog entries as a grounded entity kind, like
venues), `engine/latn_resolver.py`, `engine/session.py`, `tests/test_buy_sell.py`.

**Changes.**
- Add `buy`, `sell` to `VERB_DIMS` + synonyms (buy/purchase; sell/vend/offload).
- Grounding: `buy <X>` grounds `X` to a **catalog entry** for the current shop
  (new grounded entity kind — mirror the venue/`_VenueEntity` pattern from
  `latn_adapter`). `sell <X>` grounds `X` to a Thing the actor owns.
- Apply via the Phase-3 primitive:
  - **buy**: `transfer_thing(materialize(entry), from=shopkeeper, to=player,
    ownership+possession, coin_cp=listed_price_cp)`. Gate: for-sale, affordable.
  - **sell**: shop bid = `round(value_cp * BUY_RATE)` (e.g. 0.5); gate on the
    shopkeeper's purse (Phase 2) and willingness (category the shop deals in).
- Refusals are first-class results: not-for-sale, can't-afford, shop-won't-buy,
  shopkeeper-broke — each a clear message, no mutation.

**Acceptance.** `buy the meat pie` debits the player, credits the shopkeeper,
leaves the pie owned+held by the player; `sell my dagger` reverses at the bid
price; each refusal path fires and mutates nothing. Suite green.

**Commit:** `Economy pt7: buy/sell verbs grounding the shop catalog, at listed price`
**Depends on:** Phases 3, 4 (and 2).

---

## Phase 8 — Two-party negotiation (modal sub-dialogue within a turn)

**Goal.** The transaction becomes a *scene*: the shopkeeper quotes, counters,
refuses; the player haggles; disposition tilts the price. World-time frozen; one
atomic transfer (or none) commits.

Split into two commits.

### 8a — Engine: suspend/resume two-party dialogue primitive
**Files.** `engine/session.py`, new `engine/negotiation.py`, `tests/test_negotiation.py`.
- The turn loop can **suspend**, run a bounded interactive exchange between the
  acting player and one NPC agent (offer → counter → accept/refuse, capped
  rounds), then **resume** with a committed outcome. World state and turn counter
  do not advance during it; only the two participants act. Reusable beyond
  shopping (bribe, persuade, interrogate).
- Tests script the dialogue turns (no live LLM) and assert: agreed → one transfer
  at the agreed price; refused → nothing; round cap respected; no world-time
  advance.

### 8b — Haggle policy + UI
**Files.** shopkeeper policy (uses disposition / neurochemical baseline to set
reservation price & flexibility), `web_play.py` (the two-party dialog screen).
- A warmer / higher-oxytocin shopkeeper concedes more; a wary one holds firm or
  refuses. Reservation price bounded by `value_cp` (won't sell below cost / buy
  above resale).

**Acceptance.** A scripted haggle round-trips to a committed transfer at the
agreed price; refusal commits nothing; disposition visibly shifts the outcome;
UI renders the exchange. Suite green.

**Commit(s):** `Economy pt8a: suspend/resume two-party negotiation primitive` ·
`Economy pt8b: disposition-driven haggling + two-party dialog UI`
**Depends on:** Phase 7.

---

## Later / optional (own plans; not blocking a demo)

- **Encumbrance enforcement** — carry weight budget = 15 × Str lb; coins count
  (50/lb); over-budget → penalties. Field exists after Phase 1; enforcement is a
  small follow-up.
- Coin denominations as physical objects & making change.
- Magical-item **appraisal / identification** (the Gilded Trinket's whole
  personality — value hidden until identified).
- **Reputation** memory of caught theft (the town gossips; Maribel already
  "hears everything").
- Re-provisioning / supply chain.

---

## Suggested handoff order

1 → 2 → 3 form the spine (data + purse + primitive) and are the safest to hand
off first. 4 and 5 (catalog, containers) are independent of 6 (steal). 7 needs
3+4. 8 needs 7 and is the largest — do it last, split as 8a/8b. Any single phase
above is a complete, testable, atomically-committable unit.
