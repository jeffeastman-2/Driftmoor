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

## Characters

### gilthaness
- **type:** player
- **soul_file:** scenario/people/players/gilthaness/Gilthaness_SOUL.md
- **identity_file:** scenario/people/players/gilthaness/Gilthaness_IDENTITY.md
- **scene_handle:** the elven magic-user
- **pronouns:** she/her
- **hp:** 87
- **ac:** 17
- **provider:** ollama
- **model:** gemma4:26b
- **dopamine:** 0.58
- **cortisol:** 0.30
- **norepinephrine:** 0.45
- **endorphins:** 0.55
- **serotonin:** 0.71
- **acetylcholine:** 0.86
- **oxytocin:** 0.62
- **dopamine_baseline:** 0.58
- **dopamine_volatility:** 0.35
- **cortisol_baseline:** 0.30
- **cortisol_volatility:** 0.30
- **serotonin_baseline:** 0.70
- **serotonin_volatility:** 0.20

### elyssa
- **type:** npc
- **soul_file:** scenario/people/npcs/elyssa/SOUL.md
- **identity_file:** scenario/people/npcs/elyssa/IDENTITY.md
- **scene_handle:** the scholar of Driftmoor
- **pronouns:** she/her
- **hp:** 24
- **ac:** 12
- **provider:** ollama
- **model:** gemma4:26b
- **dopamine:** 0.42
- **cortisol:** 0.44
- **norepinephrine:** 0.54
- **endorphins:** 0.40
- **serotonin:** 0.52
- **acetylcholine:** 0.72
- **oxytocin:** 0.36
- **dopamine_baseline:** 0.40
- **dopamine_volatility:** 0.25
- **cortisol_baseline:** 0.42
- **cortisol_volatility:** 0.35
- **acetylcholine_baseline:** 0.70
- **acetylcholine_volatility:** 0.25

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
