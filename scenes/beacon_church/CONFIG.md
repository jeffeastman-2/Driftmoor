# Scene Config — Beacon Church

## Scene
- **scene_name:** beacon_church
- **title:** BEACON CHURCH
- **narrative_title:** The Beacon Church
- **transcript_title:** BEACON CHURCH — Amara, Elden, Mira
- **character_summary:** Amara (GPT-4o), Elden (DeepSeek), Mira (Grok)
- **default_turns:** 4

## Time
- **hour:** 19
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** anthropic
- **model:** claude-sonnet-4-20250514

## Scene Notes

This is an exploration/social scene in the village church. No combat expected.
The dark lantern is the visible sign of the obelisk's influence reaching into Driftmoor — it has no mundane explanation.
Two clerics of different orders meeting in a corrupted church. Amara serves Lathander (renewal), Elden serves Pelor (light). Compatible but distinct faiths.
Mira is guarded — she protects Elden and holds back information until she trusts the newcomer.
Elden's past in the Echoing Caverns is a deep wound — he will not volunteer it easily.

# Exit Motivations (DM only)

Characters may leave this scene. Recognise and permit these:
- Amara may want to examine the lantern more closely from outside, or visit Elyssa's cottage to research the corruption.
- Elden may mention the forge symbols or the mill — sending Amara to investigate.
- Mira may slip away to check the lantern herself at the top of the steeple.
- If they discuss the Echoing Caverns, any character may want to head north toward the obelisk.
- Practical needs: food from the bakery, supplies from Salt & Iron.

## Characters

### amara
- **type:** player
- **soul_file:** scenario/people/players/amara/SOUL.md
- **identity_file:** scenario/people/players/amara/IDENTITY.md
- **hp:** 10
- **ac:** 16
- **provider:** openai
- **model:** gpt-4o
- **dopamine:** 0.5
- **cortisol:** 0.35
- **norepinephrine:** 0.4
- **endorphins:** 0.5
- **serotonin:** 0.65
- **acetylcholine:** 0.55
- **oxytocin:** 0.55
- **dopamine_baseline:** 0.5
- **dopamine_volatility:** 0.5
- **cortisol_baseline:** 0.3
- **cortisol_volatility:** 0.5
- **serotonin_baseline:** 0.65
- **serotonin_volatility:** 0.3
- **oxytocin_baseline:** 0.5
- **oxytocin_volatility:** 0.5

### elden
- **type:** npc
- **soul_file:** scenario/people/npcs/elden/SOUL.md
- **identity_file:** scenario/people/npcs/elden/IDENTITY.md
- **hp:** 8
- **ac:** 10
- **provider:** deepseek
- **model:** deepseek-chat
- **dopamine:** 0.35
- **cortisol:** 0.45
- **norepinephrine:** 0.35
- **endorphins:** 0.3
- **serotonin:** 0.55
- **acetylcholine:** 0.5
- **oxytocin:** 0.5
- **dopamine_baseline:** 0.35
- **dopamine_volatility:** 0.3
- **cortisol_baseline:** 0.4
- **cortisol_volatility:** 0.4
- **serotonin_baseline:** 0.55
- **serotonin_volatility:** 0.3

### mira
- **type:** npc
- **soul_file:** scenario/people/npcs/mira/SOUL.md
- **identity_file:** scenario/people/npcs/mira/IDENTITY.md
- **hp:** 6
- **ac:** 10
- **provider:** xai
- **model:** grok-3
- **dopamine:** 0.45
- **cortisol:** 0.45
- **norepinephrine:** 0.55
- **endorphins:** 0.4
- **serotonin:** 0.5
- **acetylcholine:** 0.65
- **oxytocin:** 0.45
- **dopamine_baseline:** 0.45
- **dopamine_volatility:** 0.6
- **cortisol_baseline:** 0.35
- **cortisol_volatility:** 0.7
- **acetylcholine_baseline:** 0.6
- **acetylcholine_volatility:** 0.5

## Scene Introductions

### amara
You climbed the rise to the Beacon Church at dusk. Your order sent you to investigate disturbances in Driftmoor. The church is modest stone, wooden steeple. The lantern at the top is lit — but the light coming from it is wrong. Dark threads in what should be pure flame. Inside: simple, clean, beeswax and herbs. An old priest leans on an oak staff near the altar. A young woman with red braids is arranging candles and watched you come through the door before the priest did.

### elden
A cleric of Lathander has come to your church. Young, chain mail, silver sunrise symbol at her throat. She saw the lantern on her way up — you could tell by her face. She knows the light is wrong. Mira is watching from the candle rack, already assessing. You have been waiting for someone to come. You did not expect it to be someone from another order.

### mira
A stranger just walked in. Cleric. Lathander, not Pelor — you can tell from the symbol. Chain mail and a mace. She looked at the lantern on the way up. She knows. Father Elden is already leaning toward her with that look he gets when he wants to trust someone before he should. You have not told him what you saw at the lantern three nights ago. You are not sure you should tell this woman either. Not yet.

## Game State Sections
- header: Scene: The Beacon Church | file: scenario/places/driftmoor/beacon_church/PLACE.md
- file: scenario/places/driftmoor/beacon_church/CONTENTS.md
- header: Relevant Lore (DM only) | file: scenario/things/obelisk_shards.md
- header: Scene Notes | file: scenes/beacon_church/CONFIG.md#Scene Notes
