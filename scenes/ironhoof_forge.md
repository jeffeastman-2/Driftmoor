# Scene Config — Ironhoof Forge

## Scene
- **scene_name:** ironhoof_forge
- **title:** IRONHOOF FORGE
- **narrative_title:** The Ironhoof Forge
- **transcript_title:** IRONHOOF FORGE — Thorgrim, Darrin, Kara
- **character_summary:** Thorgrim (Grok), Darrin (GPT-4o), Kara (DeepSeek)
- **default_turns:** 4

## Time
- **hour:** 7
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** ollama
- **model:** gemma4:26b

## Scene Notes

This is an exploration/social scene at the forge. No combat expected.
The shadowy symbols on the forge walls match obelisk-related markings found elsewhere — this is a plot thread, not a combat encounter.
The missing horse and clawed tracks toward Mistwood are a separate hook.
Kara wants to apprentice with adventurers. Darrin will resist this.
Thorgrim has been staying at the lean-to. He is a guest, not an employee.

# Exit Motivations (DM only)

Characters may leave this scene. Recognise and permit these:
- Thorgrim has not eaten since yesterday. The Weary Traveler tavern serves breakfast and is a short walk into town.
- Kara wants to follow the clawed tracks toward Mistwood. She may try to slip away or recruit Thorgrim.
- Darrin needs iron stock from the general store in town — he may send someone or go himself.
- If anyone learns about the obelisk shard ring at the Gilded Trinket, the forge symbols become much more interesting.

## Characters

### thorgrim
- **type:** player
- **soul_file:** scenario/people/players/thorgrim/SOUL.md
- **identity_file:** scenario/people/players/thorgrim/IDENTITY.md
- **hp:** 13
- **ac:** 18
- **provider:** ollama
- **model:** gemma4:26b
- **dopamine:** 0.4
- **cortisol:** 0.45
- **norepinephrine:** 0.5
- **endorphins:** 0.35
- **serotonin:** 0.4
- **acetylcholine:** 0.6
- **oxytocin:** 0.2
- **dopamine_baseline:** 0.4
- **dopamine_volatility:** 0.4
- **cortisol_baseline:** 0.45
- **cortisol_volatility:** 0.5
- **serotonin_baseline:** 0.45
- **serotonin_volatility:** 0.3
- **oxytocin_baseline:** 0.15
- **oxytocin_volatility:** 0.3

### darrin
- **type:** npc
- **soul_file:** scenario/people/npcs/darrin/SOUL.md
- **identity_file:** scenario/people/npcs/darrin/IDENTITY.md
- **hp:** 16
- **ac:** 12
- **provider:** ollama
- **model:** gemma4:26b
- **dopamine:** 0.35
- **cortisol:** 0.55
- **norepinephrine:** 0.5
- **endorphins:** 0.3
- **serotonin:** 0.5
- **acetylcholine:** 0.55
- **oxytocin:** 0.45
- **dopamine_baseline:** 0.35
- **dopamine_volatility:** 0.3
- **cortisol_baseline:** 0.4
- **cortisol_volatility:** 0.6
- **oxytocin_baseline:** 0.4
- **oxytocin_volatility:** 0.4

### kara
- **type:** npc
- **soul_file:** scenario/people/npcs/kara/SOUL.md
- **identity_file:** scenario/people/npcs/kara/IDENTITY.md
- **hp:** 10
- **ac:** 11
- **provider:** ollama
- **model:** gemma4:26b
- **dopamine:** 0.65
- **cortisol:** 0.3
- **norepinephrine:** 0.55
- **endorphins:** 0.6
- **serotonin:** 0.55
- **acetylcholine:** 0.65
- **oxytocin:** 0.5
- **dopamine_baseline:** 0.6
- **dopamine_volatility:** 0.9
- **cortisol_baseline:** 0.25
- **cortisol_volatility:** 0.7
- **oxytocin_baseline:** 0.45
- **oxytocin_volatility:** 0.6

## Scene Introductions

### thorgrim
Early morning at the forge. You slept poorly in the lean-to — bad dreams again, the ambush, the screaming. You are standing at the forge fire, examining the shadowy symbols carved into the stone wall. They were not here a week ago. The marks are unlike any mason's work you know. Darrin is at the anvil, hammering, pretending not to watch you. His daughter Kara is in the stables — you can hear her talking to the horses.

### darrin
Morning at the forge. You are hammering a set of horseshoes, but your mind is elsewhere. The dwarf — Thorgrim — is standing by the wall again, studying those marks. You have not asked him directly what he thinks. You are not sure you want to know. The marks appeared a week ago and they are cold to the touch even with the forge burning. From the stables you hear Kara talking to the remaining horses. One is still missing.

### kara
You are in the stables brushing down the bay mare. She is still jittery — all the horses have been since the night the gelding vanished. You found the tracks yourself. Claws, not hooves, heading into the Mistwood tree line. Your father told you to forget about it. You have not forgotten about it. Through the stable wall you can hear the forge hammer and the dwarf moving around. He has been studying those marks on the wall. You want to ask him what he thinks.

## Game State Sections
- header: Scene: Ironhoof Forge | file: scenario/places/driftmoor/ironhoof_forge/PLACE.md
- file: scenario/places/driftmoor/ironhoof_forge/CONTENTS.md
- header: Relevant Lore (DM only) | file: scenario/things/obelisk_shards.md
- header: Scene Notes | file: scenes/ironhoof_forge.md#Scene Notes
