# Scene Config — Salt & Iron Mercantile

## Scene
- **scene_name:** salt_and_iron
- **title:** SALT & IRON
- **narrative_title:** Salt and Iron
- **transcript_title:** SALT & IRON — Varrak, Jorgen
- **character_summary:** Varrak (Grok), Jorgen (DeepSeek)
- **default_turns:** 4

## Time
- **hour:** 14
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** anthropic
- **model:** claude-sonnet-4-20250514

## Scene Notes

This is an exploration/social scene in the general store. No combat expected.
Varrak is a sorcerer with Detect Magic — if he casts it, nothing in stock is magical, but the map of Driftmoor is worth buying.
Kelem Dustcloak sent Varrak here. Jorgen suspects Kelem of illicit dealings. This creates immediate tension if Varrak mentions Kelem's name.
Jorgen rewards good stories with discounts — Varrak's draconic heritage and obelisk research could earn one.
The missing supply caravan is a hook Jorgen will offer if he decides Varrak is reliable.

# Exit Motivations (DM only)

Characters may leave this scene. Recognise and permit these:
- Varrak may want to visit Kelem at Dustcloak's Curios to examine the obelisk fragments directly.
- Jorgen may mention the Echoing Caverns artifact and suggest Varrak head north.
- If Jorgen mentions the forge symbols or the dark light at the Beacon Church, Varrak may investigate those locations.
- Varrak is hungry and new in town — Jorgen may direct him to the Broken Lantern for food and lodging.
- Jorgen may hire Varrak to find the missing caravan.

## Characters

### varrak
- **type:** player
- **soul_file:** scenario/people/players/varrak/SOUL.md
- **identity_file:** scenario/people/players/varrak/IDENTITY.md
- **hp:** 8
- **ac:** 13
- **provider:** xai
- **model:** grok-3
- **dopamine:** 0.55
- **cortisol:** 0.4
- **norepinephrine:** 0.5
- **endorphins:** 0.35
- **serotonin:** 0.4
- **acetylcholine:** 0.7
- **oxytocin:** 0.15
- **dopamine_baseline:** 0.5
- **dopamine_volatility:** 0.6
- **cortisol_baseline:** 0.35
- **cortisol_volatility:** 0.5
- **acetylcholine_baseline:** 0.65
- **acetylcholine_volatility:** 0.4
- **oxytocin_baseline:** 0.1
- **oxytocin_volatility:** 0.2

### jorgen
- **type:** npc
- **soul_file:** scenario/people/npcs/jorgen/SOUL.md
- **identity_file:** scenario/people/npcs/jorgen/IDENTITY.md
- **hp:** 16
- **ac:** 11
- **provider:** deepseek
- **model:** deepseek-chat
- **dopamine:** 0.4
- **cortisol:** 0.45
- **norepinephrine:** 0.45
- **endorphins:** 0.35
- **serotonin:** 0.5
- **acetylcholine:** 0.55
- **oxytocin:** 0.25
- **dopamine_baseline:** 0.4
- **dopamine_volatility:** 0.3
- **cortisol_baseline:** 0.4
- **cortisol_volatility:** 0.5
- **serotonin_baseline:** 0.5
- **serotonin_volatility:** 0.3

## Scene Introductions

### varrak
You came to Salt & Iron because Kelem Dustcloak told you to start here. The mercantile is large, organized, iron-banded timber. Shelves of rope, tools, salt barrels, weapons. A long counter runs the center. Behind it stands a broad man with a salt-and-pepper beard and a scowl. He looked at you — a red dragonborn in robes with no armor — and has not spoken yet. Your satchel holds your obelisk notes. Something in this town is connected to the fragments. You can feel it in the base of your skull, the way you always feel it near shard-touched places.

### jorgen
A dragonborn just walked into your shop. Red scales, amber eyes, robes, no armor. Carrying a leather satchel and a quarterstaff. He is looking at the shelves the way someone looks when they are not shopping — he is scanning. A sorcerer, almost certainly. You have not decided yet if he is Kelem's man or something else. The supply caravan is three days late and you are in no mood for trouble.

## Game State Sections
- header: Scene: Salt & Iron Mercantile | file: scenario/places/driftmoor/salt_and_iron/PLACE.md
- file: scenario/places/driftmoor/salt_and_iron/CONTENTS.md
- header: Relevant Lore (DM only) | file: scenario/things/obelisk_shards.md
- header: Scene Notes | file: scenes/salt_and_iron/CONFIG.md#Scene Notes
