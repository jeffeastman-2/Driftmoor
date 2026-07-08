# SCENE.md

Specification for scene configuration files under scenes/. These files are
loaded by engine/md_loader.py via configure_from_md.

Status: implemented

---

## Purpose

A scene file defines:

- scene metadata (name, titles, geometry/place links)
- time defaults
- DM model defaults
- cast and per-character scene overrides
- optional introduction prose and game-state include pointers

Identity and soul files still own character sheet and persona content. Scene
config owns placement and runtime routing/carry-state defaults.

---

## Top-level sections

Expected headings:

- ## Scene
- ## Time
- ## DM
- ## Characters

Optional headings:

- ## Scene Notes
- ## Mission Objective
- ## Spelunking Notes (or any authored notes)
- ## Scene Introductions
- ## Game State Sections

All parsed metadata lines use this shape:

- **key:** value

---

## Scene section

Required keys:

- scene_name
- geometry_file
- place_file

Common keys:

- title
- narrative_title
- transcript_title
- character_summary
- default_turns

---

## Time section

Supported keys:

- hour
- minute
- day
- season
- turn_duration

---

## DM section

Supported keys:

- provider
- model

These become the scene default model routing. Character blocks may override.

---

## Characters section

Each character is a subsection:

### <character_id>

Supported keys:

- type: player | npc | creature
- soul_file
- identity_file
- creature_file
- scene_handle
- activation
- position
- provider
- model

Transport/routing keys (player-facing bridges):

- player_transport
- channel
- host
- inbox
- outbox

Starting carry-state keys (scene-authored):

- in_hand
- held_items (alias of in_hand)
- worn
- worn_items (alias of worn)

Carry-state semantics:

- in_hand/held_items accepts a comma, semicolon, pipe, or newline separated
  list of item references.
- References are matched by id and, when available, by label text.
- Weapon references in in_hand are drawn into wielded.
- Non-weapon references in in_hand are put into held_items (hand occupancy).
- worn/worn_items marks matching pack Things as worn.
- If an item is listed both in hand and worn, worn wins (it is removed from
  held_items).

Notes:

- position is authored as x, y[, z]; zone is always derived from geometry.
- Scene placement is authoritative for turn-0 seeding.

---

## Scene Introductions section

Optional per-character prose blocks:

### <character_id>

<free text>

When present, this text is appended to the character's opening context.

---

## Example character block

### gilthaness
- **type:** player
- **soul_file:** scenario/people/players/gilthaness/SOUL.md
- **identity_file:** scenario/people/players/gilthaness/IDENTITY.md
- **player_transport:** telegram
- **channel:** telegram
- **host:** ultra
- **inbox:** ~/messages/from-gilthaness
- **outbox:** ~/messages/to-gilthaness
- **position:** 110, 320
- **in_hand:** snapped_torch, mug of ale
- **worn:** wooden_vine_carved_bracelet
