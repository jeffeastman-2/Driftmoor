# Scene Config — The Broken Lantern

## Scene
- **scene_name:** broken_lantern
- **title:** BROKEN LANTERN
- **narrative_title:** The Broken Lantern
- **transcript_title:** BROKEN LANTERN — Kaelin, Tess
- **character_summary:** Kaelin (DeepSeek), Tess (Grok)
- **default_turns:** 4

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

This is an exploration/social scene in the village tavern. No combat expected.
Kaelin has no coin and is hungry. They need to earn a meal.
Tess is sharp, fair, and always looking for useful people.
Wilfred is at the bar muttering about shadow giants near the obelisk — this is a real plot thread, not just drunk talk.
The meeting room behind the kitchen has suspicious guests.
Strange noises have been reported from an unoccupied upstairs room.

# Exit Motivations (DM only)

Characters may leave this scene. Recognise and permit these:
- Kaelin is a wanderer — they may want to explore the village, especially if they hear about the forge symbols or the pawnshop.
- Tess may send someone to investigate the noises upstairs (this leads to a sub-location, not a scene exit).
- If Wilfred's obelisk talk catches Kaelin's ear, they may head north toward the obelisk reach at dawn.
- The suspicious meeting room guests may leave — Tess may ask someone to follow them.

## Characters

### kaelin
- **type:** player
- **soul_file:** scenario/people/players/kaelin/SOUL.md
- **identity_file:** scenario/people/players/kaelin/IDENTITY.md
- **pronouns:** they/them
- **hp:** 9
- **ac:** 11
- **provider:** ollama
- **model:** gemma4:26b
- **dopamine:** 0.7
- **cortisol:** 0.35
- **norepinephrine:** 0.45
- **endorphins:** 0.65
- **serotonin:** 0.5
- **acetylcholine:** 0.6
- **oxytocin:** 0.4
- **dopamine_baseline:** 0.65
- **dopamine_volatility:** 0.9
- **cortisol_baseline:** 0.3
- **cortisol_volatility:** 0.7
- **endorphins_baseline:** 0.6
- **endorphins_volatility:** 0.8
- **oxytocin_baseline:** 0.35
- **oxytocin_volatility:** 0.6

### tess
- **type:** npc
- **soul_file:** scenario/people/npcs/tess/SOUL.md
- **identity_file:** scenario/people/npcs/tess/IDENTITY.md
- **hp:** 14
- **ac:** 11
- **provider:** ollama
- **model:** gemma4:26b
- **dopamine:** 0.45
- **cortisol:** 0.4
- **norepinephrine:** 0.5
- **endorphins:** 0.4
- **serotonin:** 0.55
- **acetylcholine:** 0.7
- **oxytocin:** 0.3
- **dopamine_baseline:** 0.45
- **dopamine_volatility:** 0.4
- **cortisol_baseline:** 0.35
- **cortisol_volatility:** 0.5
- **acetylcholine_baseline:** 0.65
- **acetylcholine_volatility:** 0.3

## Scene Introductions

### kaelin
Evening at the Broken Lantern. You pushed through the door ten minutes ago — new town, no coin, empty stomach. The room is half full. Fisherfolk, a couple of farmers, a drunk at the end of the bar muttering about shadow giants. The woman behind the bar has already looked you over twice. You unslung your lute and found a stool near the fire. If you play well enough, dinner is free. It usually is.

### tess
Evening crowd. The usual faces. Wilfred is three ales deep and talking about shadow giants again. Then the door opens and a halfling walks in — wild hair, patched clothes, lute across their back, and the particular confidence of someone who has talked their way into a meal before. They have already found the stool by the fire. No coin visible. You have seen this act. The question is whether this one is worth feeding.

## Game State Sections
- header: Scene: The Broken Lantern (Tavern) | file: scenario/places/driftmoor/broken_lantern/PLACE.md
- file: scenario/places/driftmoor/broken_lantern/CONTENTS.md
- header: Scene Notes | file: scenes/broken_lantern.md#Scene Notes
