# Driftmoor v0.1 Release Checklist

## Release Goal

Driftmoor v0.1 is a polished, playable vertical slice centered on the town of
Driftmoor.

The release supports exploring the town, entering its first-class buildings,
meeting their resident NPCs, using shops and services, moving through authored
geometry, and receiving narration that agrees with engine state.

The Fey Glade and Echoing Caverns are included as experimental previews. They
are not part of the v0.1 completeness guarantee.

## Definition of Done

Driftmoor v0.1 is ready when:

- [ ] Every item under **Required Release Gates** is complete.
- [ ] The full automated test suite passes from a clean checkout.
- [ ] A manual browser walkthrough passes using the documented release setup.
- [ ] A fresh installation succeeds using only public documentation.
- [ ] No secrets, private transcripts, personal data, or machine-specific
      artifacts are present in the repository or its published history.
- [ ] Known limitations and deferred content are documented.
- [ ] The release commit is tagged `v0.1.0`.

## Supported Scope

### Included

- Driftmoor town map and its 26 first-class destinations
- Town building entry and exit
- Resident NPC loading and introductions
- Spatial movement, visibility, and map rendering
- Grounded narration
- Town commerce and services
- Checkpointing and resumption for supported town play
- Browser play as the primary user-facing path
- Local solo self-hosting
- Trusted remote solo play over a private network such as Tailscale
- One human player per game-server process

### Experimental Preview

- [ ] Label the Fey Glade as experimental in user-facing documentation.
- [ ] Label the Echoing Caverns as experimental in user-facing documentation.
- [ ] Confirm preview failures cannot block or corrupt Driftmoor town play.

### Deferred Beyond v0.1

- Old Mill completion
- Haverstad family promotion to fully authored first-class NPCs
- Public-internet game hosting
- Authenticated multi-human sessions
- Session lobbies, invitations, and player-to-character seat assignment
- Full regional campaign progression
- Production-completeness guarantees for Fey Glade
- Production-completeness guarantees for Echoing Caverns
- Generalizing the engine beyond the Driftmoor campaign

## v0.1 Deployment Contract

Driftmoor v0.1 is a self-hosted application, not a public multiplayer service.

Supported deployment modes:

1. **Local solo play:** The player runs Driftmoor on their own machine, using
   either a reachable local model backend or their own cloud-provider
   credentials.
2. **Trusted remote solo play:** A host runs Driftmoor and its model backend on
   a private machine. One trusted player connects through a private network
   such as Tailscale. The browser is only the client; model execution and game
   state remain on the host.

The v0.1 web server must not be presented as safe for direct public-internet
exposure. It currently binds beyond localhost, has no application-level
authentication or player identity, and accepts input for one configured human
player.

Explicitly unsupported in v0.1:

- Direct exposure of `web_play.py` to the public internet
- Anonymous or untrusted remote players
- Multiple human players sharing one game-server process
- One server process hosting multiple independent games
- Public account registration, matchmaking, or persistent hosted accounts

Documentation must state these boundaries anywhere remote access is described.
A reverse proxy, port forward, or public tunnel does not by itself make the
application safe for untrusted access.

Future authenticated multiplayer requires:

- Authenticated users or scoped invitation tokens
- Server-side game/session ownership
- Player-to-character seat assignment
- Authorization on input, map, event, inventory, and checkpoint access
- Per-player perception-filtered event streams
- Reconnection and session-lobby behavior
- HTTPS, CSRF protection, request-size limits, and rate limiting
- Isolation between simultaneous games and players

## Required Release Gates

### 1. Place and Building Integrity

The automated building audit is
[`tests/test_driftmoor_buildings.py`](tests/test_driftmoor_buildings.py).
It discovers buildings from Driftmoor's connection table rather than keeping a
second hard-coded list.

For every first-class destination, it verifies:

- A `PLACE.md` exists.
- A `GEOMETRY.md` exists.
- Its generic entry phrase resolves to the correct place.
- Its town doorway has coordinates.
- Its geometry loads with the correct `place_path`.
- Its interior has a reciprocal arrival/exit point to Driftmoor.
- Every initialized resident NPC is instantiated by the place.
- Every initialized resident NPC has an explicit scene introduction.
- Every bold named entry under `Who Is Normally Here` resolves to a structured
  resident.

Current automatically verified destinations:

- [x] `dustcloaks_curios` — Dustcloak's house/curios
- [x] `beacon_church` — church
- [x] `graveyard` — graveyard/cemetery
- [x] `mayors_hall` — mayor's hall
- [x] `broken_lantern` — tavern
- [x] `salt_and_iron` — mercantile
- [x] `forge` — Ironhoof Forge
- [x] `stables` — stable/stables
- [x] `corral` — corral
- [x] `elyssa_cottage` — Elyssa's house
- [x] `bitter_remedy` — apothecary
- [x] `gilded_trinket` — pawn shop
- [x] `weary_traveler` — rooming house
- [x] `bakery` — bakery
- [x] `cobblers_shop` — cobbler
- [x] `rusty_razor` — barber
- [x] `coopers_shed` — cooper
- [x] `carpenters_workshop` — carpenter
- [x] `weavers_cottage` — weaver
- [x] `tailors_shop` — tailor
- [x] `tannery` — tannery
- [x] `fishmongers_shack` — fishmonger
- [x] `schoolhouse` — schoolhouse
- [x] `midwifes_home` — midwife
- [x] `watchtower` — watchtower
- [x] `general_store` — general store

Remaining place work:

- [x] Add explicit place `type` and `aliases` metadata.
- [x] Make directory slugs stable internal IDs rather than player-facing names.
- [x] Preserve compatibility with title-, type-, connection-, and
      directory-derived aliases during migration.
- [x] Standardize map landmark type labels while retaining proper place names
      in tooltips.
- [x] Review every building's description, connections, dynamic state, and
      notable contents for contradictions.
- [x] Review internal subplaces and remove or repair stale, non-enterable
      directory/connection references.

### 2. NPC Completeness

- [x] Structured resident loading is audited for first-class town buildings.
- [x] Explicit resident scene introductions are audited.
- [x] Prose-only named residents are rejected by the building audit.
- [x] Elise Harper is a first-class NPC and resident clerk of Mayor's Hall.
- [ ] Review every Driftmoor NPC's `IDENTITY.md` for required runtime fields.
- [ ] Review every Driftmoor NPC's `SOUL.md` for stable voice, knowledge, and
      motivations.
- [x] Confirm residents appear at plausible positions in their building
      geometry.
- [ ] Confirm NPC knowledge does not reveal DM-only or unperceived information.
- [ ] Confirm NPC starting locations agree across initialization, place files,
      and scenes.

### 3. Movement, Entry, and Narration

- [x] Distant `enter` intents walk toward a doorway instead of teleporting.
- [x] Scene transition occurs after reaching the doorway.
- [x] Singular `stable` and plural `stables` resolve correctly.
- [x] Forge, stables, and corral are independent first-class places.
- [x] Compound sibling transition such as
      `exit the forge and enter the stables` is supported.
- [x] Narration receives authoritative approach-versus-entry results.
- [x] Building tooltips display title-cased types and proper names.
- [ ] Add an automated multi-turn test that begins far from a door, approaches,
      enters, and exits a representative building.
- [ ] Add a multi-building scripted traversal covering at least one named
      business, one generic business alias, and one compound transition.
- [ ] Manually verify map position and narration after each transition.
- [ ] Verify save/resume while inside a building and after returning to town.

### 4. Commerce and Services

- [ ] Inventory every Driftmoor merchant and service provider.
- [ ] Verify each advertised good or service has an authoritative price source.
- [ ] Verify `what can I buy?` returns the correct catalog in every shop.
- [ ] Verify purchases debit the buyer, credit or record the vendor side, and
      transfer the item.
- [ ] Verify failed purchases do not alter inventory or currency.
- [ ] Verify sale and haggling behavior where advertised.
- [x] Reconcile legacy global item lists with per-place
      `CONTENTS.md` files.
- [ ] Decide which services require immediate engine support and which may be
      honestly narrated as deferred work.

### 5. Content and Playability Review

- [x] Perform a building-by-building browser walkthrough.
- [x] Speak with every resident NPC at least once.
- [x] Ask every merchant what they sell.
- [?] Exercise the missing-horse hook without requiring unfinished Old Mill
      content.
- [?] Exercise the forge-symbol hook without requiring an experimental region.
- [x] Confirm empty places, including the corral, are intentionally empty.
- [x] Confirm every visible map landmark has an accurate label and tooltip.
- [x] Record known narrative or grounding limitations discovered during the
      walkthrough.

### 6. Automated Quality Gate

- [x] Driftmoor building integration audit exists.
- [x] Current full suite passes: 1,426 tests at checklist creation.
- [ ] Add a single documented release-test command.
- [ ] Run the suite with warnings surfaced and review every warning.
- [ ] Run formatting/linting/type checks selected for v0.1.
- [ ] Ensure tests do not require private API keys.
- [ ] Ensure deterministic tests use the shared seeded game RNG.
- [ ] Test on a clean virtual environment using supported Python versions.

Suggested release test:

```bash
MPLCONFIGDIR=/tmp/driftmoor-mpl .venv/bin/pytest -q
```

## Public Release Readiness

### Repository Hygiene

- [ ] Confirm `.env` and all local credential files are ignored.
- [ ] Scan the complete Git history for API keys and credentials.
- [ ] Scan the complete Git history for personal names, private messages, and
      unintended transcripts.
- [ ] Remove or ignore runtime checkpoints, model outputs, generated maps,
      caches, logs, and unknown-word telemetry unless intentionally shipped.
- [ ] Remove machine-specific absolute paths from tracked files and examples.
- [ ] Verify a clone contains no required untracked assets.
- [ ] Review large binary files and decide whether they belong in the release.

### Documentation

- [ ] Update `README.md` status from general active development to the precise
      v0.1 supported scope.
- [ ] Document browser-first quick start from a clean clone.
- [ ] Document the LATN dependency and supported installation layouts.
- [ ] Document Ollama and cloud-provider configuration without exposing keys.
- [ ] Add architecture and scenario-authoring links for contributors.
- [ ] Add a `KNOWN_LIMITATIONS.md` or equivalent release section.
- [ ] Add contribution and issue-reporting guidance.
- [ ] Add a code of conduct if outside contributions are invited.

### Legal and Attribution

- [ ] Choose and add a software license.
- [ ] Confirm authored campaign text and artwork may be published.
- [ ] Review D&D rules terminology and third-party material for licensing or
      attribution requirements.
- [ ] Add notices for bundled or referenced dependencies and assets.
- [ ] Document model-provider requirements and applicable user obligations.

### Security and Privacy

- [ ] Run a dependency vulnerability review.
- [ ] Review browser and web-server defaults before recommending public use.
- [x] Document local solo play as the default v0.1 deployment.
- [x] Document trusted remote solo play over a private network.
- [x] Warn explicitly against exposing `web_play.py` directly to the public
      internet.
- [x] Document the one-human-player-per-process limitation.
- [x] Confirm remote-access documentation does not imply that a reverse proxy
      or tunnel supplies application-level authorization.
- [ ] Confirm the server does not expose arbitrary local files.
- [ ] Confirm logs and checkpoints do not unintentionally store secrets.
- [ ] Document that users are responsible for securing externally exposed
      model endpoints and game servers.

## Manual Release Walkthrough

Perform from a fresh clone and a new game state:

- [ ] Install dependencies using only the README.
- [ ] Start Driftmoor in the browser.
- [ ] Complete a local solo browser connection.
- [ ] Complete a trusted remote browser connection over a private network.
- [ ] Confirm a second browser is not documented or represented as a second
      independently authenticated player.
- [ ] Locate and enter Ironhoof Forge from town.
- [ ] Exit the forge and enter the stables using a compound intent.
- [ ] Observe Kara, Bramble, and Thistle in the stable.
- [ ] Enter the empty corral and return to town.
- [ ] Enter a named business using its proper name.
- [ ] Enter the same or another business using only its generic type.
- [ ] Speak with an NPC newly loaded from a place file.
- [ ] Ask a merchant what is available and complete a purchase.
- [ ] Save or stop, resume the session, and verify location and inventory.
- [ ] Confirm narration never claims a blocked movement or premature entry.
- [ ] Confirm the live map, icons, labels, and tooltips remain correct.

## Release Procedure

- [ ] Freeze v0.1 scope; move new regional work to the deferred list.
- [ ] Complete all required gates.
- [ ] Run the release test suite from a clean checkout.
- [ ] Complete the manual release walkthrough.
- [ ] Update version and status documentation.
- [ ] Write release notes with supported scope, previews, and known limitations.
- [ ] Create a release candidate commit.
- [ ] Tag the accepted commit `v0.1.0`.
- [ ] Publish the repository.
- [ ] Verify installation once more from the public repository.

## Release Notes Draft

> Driftmoor v0.1 provides a playable town-focused vertical slice with
> first-class enterable buildings, resident NPCs, commerce, spatial movement,
> persistent state, live maps, and narration grounded in engine outcomes.
>
> The Fey Glade and Echoing Caverns are included as experimental previews and
> are not covered by the v0.1 completeness guarantee. The Old Mill, Haverstad
> family content, and broader regional campaign remain in development.

## Progress Log

Record release-focused decisions and milestone completions here.

- 2026-07-28: Scoped v0.1 to Driftmoor proper.
- 2026-07-28: Classified Fey Glade and Echoing Caverns as experimental
  previews.
- 2026-07-28: Deferred Old Mill and Haverstad first-class NPC work.
- 2026-07-28: Added automated coverage for all 26 first-class Driftmoor
  destinations and their initialized resident NPCs.
- 2026-08-02: Reviewed Driftmoor place prose, connections, dynamic state, and
  contents; consolidated eight stale prose-only room directories into their
  parent scenes and added an audit requiring geometry for every authored place.
