# Scene Config - Elyssa Cottage Conversation Test

## Scene
- **scene_name:** elyssa_cottage
- **title:** ELYSSA COTTAGE
- **narrative_title:** Elyssa Cottage Conversation Test
- **transcript_title:** ELYSSA COTTAGE - Gilthaness, Elyssa
- **character_summary:** Gilthaness and Elyssa in Elyssa's cottage
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

This is a social test scene with no intended combat. Gilthaness has come to
Elyssa's cottage to talk about the obelisk disturbances and local reports.
The objective is to verify stable back-and-forth dialogue and coherent
continuity over several turns.
Keep the conversation grounded: prefer counts, distances, dates, visible
marks, and direct observations over abstract theory. If someone proposes a
cause, it should be phrased as a hypothesis tied to at least one concrete
observation.

## Characters

### gilthaness
- **type:** player
- **soul_file:** scenario/people/players/gilthaness/Gilthaness_SOUL.md
- **identity_file:** scenario/people/players/gilthaness/IDENTITY.md
- **player:** telegram
- **channel:** telegram
- **host:** ultra
- **inbox:** ~/messages/from-gilthaness
- **outbox:** ~/messages/to-gilthaness
- **provider:** ollama
- **model:** gemma4:26b

### elyssa
- **type:** npc
- **soul_file:** scenario/people/npcs/elyssa/SOUL.md
- **identity_file:** scenario/people/npcs/elyssa/IDENTITY.md
- **provider:** ollama
- **model:** gemma4:26b

## Scene Introductions

### gilthaness
You arrive at Elyssa Moonglow's cottage just before dusk. The air smells faintly
of rosemary and cold stone. You have heard enough about the obelisk and the
mounting disturbances to decide that this scholar is worth your time. The door
is open, a lamp lit, and stacks of notes are visible from the threshold.

You are here to talk, assess what Elyssa knows, and judge whether her warnings
are precise, exaggerated, or dangerously understated.

### elyssa
You hear measured footsteps on the front path and look up from a spread of
annotated maps. A seasoned wood-elf traveler stands at your door: poised,
alert, and clearly not here by accident. You have enough problems that you do
not turn away capable minds.

You invite Gilthaness in and prepare to compare notes on the obelisk, the
shadows, and what Driftmoor is not yet admitting out loud.

## Game State Sections
- header: Scene: Elyssa Cottage | file: scenario/places/driftmoor/elyssa_cottage/PLACE.md
- file: scenario/places/driftmoor/elyssa_cottage/CONTENTS.md
- header: Scene Notes | file: scenes/elyssa_cottage.md#Scene Notes
