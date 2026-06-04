# Scene Config - Elyssa Cottage Conversation Test

## Scene
- **scene_name:** elyssa_cottage
- **title:** ELYSSA COTTAGE
- **narrative_title:** Elyssa Cottage Conversation Test
- **transcript_title:** ELYSSA COTTAGE - Hendricks, Elyssa
- **character_summary:** Hendricks and Elyssa in Elyssa's cottage
- **default_turns:** 4
- **geometry_file:** scenario/places/driftmoor/elyssa_cottage/GEOMETRY.md
- **place_file:** scenario/places/driftmoor/elyssa_cottage/PLACE.md

## Time
- **hour:** 18
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** ollama
- **model:** gemma4:26b

## Scene Notes

This is a social test scene with no intended combat. Hendricks has come to
Elyssa's cottage to talk about the obelisk disturbances and local reports.
The objective is to verify stable back-and-forth dialogue and coherent
continuity over several turns.
Keep the conversation grounded: prefer counts, distances, dates, visible
marks, and direct observations over abstract theory. If someone proposes a
cause, it should be phrased as a hypothesis tied to at least one concrete
observation.

## Characters

### hendricks
- **type:** player
- **soul_file:** scenario/people/players/hendricks/SOUL.md
- **identity_file:** scenario/people/players/hendricks/IDENTITY.md

### elyssa
- **type:** npc
- **soul_file:** scenario/people/npcs/elyssa/SOUL.md
- **identity_file:** scenario/people/npcs/elyssa/IDENTITY.md

## Scene Introductions

### hendricks
You arrive at Elyssa Moonglow's cottage just before dusk, coat still damp with
mist from the road in. Through the open door you see map tables, pinned notes,
and a scholar who has not slept enough but has not stopped working either.

You came to test claims against evidence. If Elyssa's reports are grounded,
you need the details. If they are not, you need to know that before anyone
starts making plans around bad assumptions.

### elyssa
You hear measured footsteps on the front path and look up from a spread of
annotated maps. A serious traveler stands at your door: poised,
alert, and clearly not here by accident. You have enough problems that you do
not turn away capable minds.

You invite Hendricks in and prepare to compare notes on the obelisk, the
shadows, and what Driftmoor is not yet admitting out loud.

## Game State Sections
- header: Scene: Elyssa Cottage | file: scenario/places/driftmoor/elyssa_cottage/PLACE.md
- file: scenario/places/driftmoor/elyssa_cottage/CONTENTS.md
- header: Scene Notes | file: scenes/elyssa_cottage.md#Scene Notes
