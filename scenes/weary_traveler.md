# Scene Config — The Weary Traveler

## Scene
- **scene_name:** weary_traveler
- **title:** The Weary Traveler
- **narrative_title:** The Weary Traveler
- **transcript_title:** The Weary Traveler — Gilthaness
- **character_summary:** Gilthaness and Martha Greaves
- **default_turns:** 8
- **geometry_file:** scenario/places/driftmoor/weary_traveler/GEOMETRY.md
- **place_file:** scenario/places/driftmoor/weary_traveler/PLACE.md

## Time
- **hour:** 19
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** ollama
- **model:** gemma4:26b

## Scene Notes

Interior social scene. No combat expected unless provoked.
Martha Greaves is the innkeeper and should be active whenever this scene is loaded.

# Exit Motivations (DM only)

Characters may leave this scene.
- Leaving via the front door returns to Driftmoor town outside the rooming house.

## Characters

### gilthaness
- **type:** player
- **soul_file:** scenario/people/players/gilthaness/SOUL.md
- **identity_file:** scenario/people/players/gilthaness/IDENTITY.md
- **player_transport:** telegram
- **channel:** telegram
- **host:** ultra
- **position:** 32, 6

## Scene Introductions

### gilthaness
You step inside the Weary Traveler. Warm stew-scented air rolls over you from the hearth. Martha Greaves is already watching the room and your entrance at the same time.

## Game State Sections
- header: Scene: The Weary Traveler | file: scenario/places/driftmoor/weary_traveler/PLACE.md
- file: scenario/places/driftmoor/weary_traveler/CONTENTS.md
- header: Scene Notes | file: scenes/weary_traveler.md#Scene Notes
