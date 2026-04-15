# Scene Config — The Old Mill

## Scene
- **scene_name:** old_mill
- **title:** OLD MILL
- **narrative_title:** The Old Mill
- **transcript_title:** OLD MILL — Lilar, Gregan, Tessa
- **character_summary:** Lilar (DeepSeek), Gregan (GPT-4o), Tessa (Grok)
- **default_turns:** 4

## Time
- **hour:** 11
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** anthropic
- **model:** claude-sonnet-4-20250514

## Scene Notes

This is an exploration/social scene at the mill. No combat expected.
The symbols on the beams match obelisk-related markings found elsewhere.
Tessa has secret rubbings of the symbols and has been near the obelisk.
Baby Isla's distress near the outer walls is a barometer of the corruption.
Gregan is suspicious of strangers and will not open up easily.
Tessa will share information privately if she trusts the cleric.

# Exit Motivations (DM only)

Characters may leave this scene. Recognise and permit these:
- Lilar may want to bring the symbol rubbings to Father Elden at the Beacon Church for comparison.
- Tessa may try to lead Lilar to the riverbank stones where she found matching symbols.
- Gregan needs supplies from Salt & Iron in town — he may send someone or mention needing to go himself.
- If Lilar learns about the shadowbeast attack, he may head toward the Fey Glade or Mistwood to investigate.

## Characters

### lilar
- **type:** player
- **soul_file:** scenario/people/players/lilar/SOUL.md
- **identity_file:** scenario/people/players/lilar/IDENTITY.md
- **hp:** 10
- **ac:** 14
- **provider:** deepseek
- **model:** deepseek-chat
- **dopamine:** 0.45
- **cortisol:** 0.4
- **norepinephrine:** 0.45
- **endorphins:** 0.4
- **serotonin:** 0.6
- **acetylcholine:** 0.55
- **oxytocin:** 0.55
- **dopamine_baseline:** 0.45
- **dopamine_volatility:** 0.4
- **cortisol_baseline:** 0.35
- **cortisol_volatility:** 0.5
- **serotonin_baseline:** 0.6
- **serotonin_volatility:** 0.3
- **oxytocin_baseline:** 0.5
- **oxytocin_volatility:** 0.5

### gregan
- **type:** npc
- **soul_file:** scenario/people/npcs/haversteads/gregan.md
- **identity_file:** scenario/people/npcs/haversteads/gregan.md
- **hp:** 14
- **ac:** 10
- **provider:** openai
- **model:** gpt-4o
- **dopamine:** 0.3
- **cortisol:** 0.6
- **norepinephrine:** 0.55
- **endorphins:** 0.25
- **serotonin:** 0.4
- **acetylcholine:** 0.5
- **oxytocin:** 0.45
- **dopamine_baseline:** 0.35
- **dopamine_volatility:** 0.3
- **cortisol_baseline:** 0.5
- **cortisol_volatility:** 0.6
- **oxytocin_baseline:** 0.4
- **oxytocin_volatility:** 0.4

### tessa
- **type:** npc
- **soul_file:** scenario/people/npcs/haversteads/tessa.md
- **identity_file:** scenario/people/npcs/haversteads/tessa.md
- **hp:** 6
- **ac:** 10
- **provider:** xai
- **model:** grok-3
- **dopamine:** 0.6
- **cortisol:** 0.5
- **norepinephrine:** 0.65
- **endorphins:** 0.55
- **serotonin:** 0.45
- **acetylcholine:** 0.7
- **oxytocin:** 0.4
- **dopamine_baseline:** 0.55
- **dopamine_volatility:** 0.9
- **cortisol_baseline:** 0.35
- **cortisol_volatility:** 0.8
- **acetylcholine_baseline:** 0.65
- **acetylcholine_volatility:** 0.7

## Scene Introductions

### lilar
You followed the river road to the Old Mill after hearing reports of strange symbols and a shadowbeast attack on a farmer. The mill is large, stone, two stories. The waterwheel groans. Inside, flour dust hangs in the air. Gregan Haverstead is at the grinding stones — broad, graying, flour-dusted. He looked up when you entered and has not smiled. His daughter Tessa, about fourteen, is near the far wall doing something with the support beams she stopped as soon as she saw you. You can see marks carved into the wood — dark, deliberate, unlike any mason's or carpenter's work you know. A baby cries from upstairs.

### gregan
A cleric just walked into your mill. Faded white robes, holy symbol of Pelor, shield on his back. He is looking at the beams. Tessa was near those beams again — you saw her pull her hand back when the door opened. You do not know this man. You do not know if he is here to help or to make things worse. The mill wheel is grinding unevenly and you have not slept well in a week.

### tessa
You were tracing the symbols on the beam when the door opened. A man in white robes. A cleric. You stepped back and shoved the charcoal rubbing into your apron pocket. Your father is watching from the grinding stones. He saw you near the beams again. The cleric is looking at the marks now. He might actually know what they are. You want to ask but not in front of your father.

## Game State Sections
- header: Scene: The Old Mill | file: scenario/places/greywater_river/old_mill/PLACE.md
- file: scenario/places/greywater_river/old_mill/CONTENTS.md
- header: Relevant Lore (DM only) | file: scenario/things/obelisk_shards.md
- header: Scene Notes | file: scenes/old_mill.md#Scene Notes
