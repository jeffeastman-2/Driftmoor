# Scene Config — The Bitter Remedy

## Scene
- **scene_name:** bitter_remedy
- **title:** THE BITTER REMEDY
- **narrative_title:** The Bitter Remedy
- **transcript_title:** THE BITTER REMEDY — Gilthaness, Lytha
- **character_summary:** Gilthaness enters Lytha's apothecary
- **default_turns:** 4
- **geometry_file:** scenario/places/driftmoor/bitter_remedy/GEOMETRY.md
- **place_file:** scenario/places/driftmoor/bitter_remedy/PLACE.md

## Time
- **hour:** 20
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** ollama
- **model:** gemma4:26b

## Scene Notes

This is an exploration/social apothecary scene in Driftmoor.
No combat expected unless the player forces one.
Lytha is perceptive and practical; she is helpful but guarded around strangers.
The missing apprentice (Fennel) is a live concern and may become a hook.

# Exit Motivations (DM only)

Characters may leave this scene. Recognise and permit these:
- Return to Driftmoor town via the front door.
- Decline Lytha's requests and continue exploring town.
- Follow leads toward Mistwood Hills after gathering enough detail.

## Characters

### gilthaness
- **type:** player
- **soul_file:** scenario/people/players/gilthaness/SOUL.md
- **identity_file:** scenario/people/players/gilthaness/IDENTITY.md
- **position:** 22, 3

### lytha
- **type:** npc
- **soul_file:** scenario/people/npcs/lytha/SOUL.md
- **identity_file:** scenario/people/npcs/lytha/IDENTITY.md
- **position:** 22, 13

## Scene Introductions

### gilthaness
You step into The Bitter Remedy and the evening noise of Driftmoor drops away.
The room is warm and sharp with herb-scents: lavender, mint, and a bitter note
underneath. Shelves crowd the walls, and behind the counter Lytha Varrow pauses
mid-measure to study you with practiced caution.

### lytha
The front door opens and a traveler steps in off the street. You recognize the
look immediately: curious, tired, and potentially trouble. You keep one hand on
the counter near your scales and ask what they need before they can start poking
through your shelves.

## Game State Sections
- header: Scene: The Bitter Remedy (Apothecary) | file: scenario/places/driftmoor/bitter_remedy/PLACE.md
- file: scenario/places/driftmoor/bitter_remedy/CONTENTS.md
- header: Scene Notes | file: scenes/bitter_remedy.md#Scene Notes
