# Scene Config — The Fey Glade

## Scene
- **scene_name:** fey_glade
- **title:** FEY GLADE
- **narrative_title:** The Fey Glade
- **transcript_title:** FEY GLADE ENCOUNTER — Aeliana, Fennel, Shadowbeast
- **character_summary:** Aeliana, Fennel, Shadowbeast
- **default_turns:** 8
- **geometry_file:** scenario/places/mistwood_hills/fey_glade/GEOMETRY.md
- **place_file:** scenario/places/mistwood_hills/fey_glade/PLACE.md

## Time
- **hour:** 19
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** ollama
- **model:** gemma4:26b

## Characters

### aeliana
- **type:** player
- **soul_file:** scenario/people/players/aeliana/SOUL.md
- **identity_file:** scenario/people/players/aeliana/IDENTITY.md

### fennel
- **type:** player
- **soul_file:** scenario/people/npcs/fennel/SOUL.md
- **identity_file:** scenario/people/npcs/fennel/IDENTITY.md

### shadowbeast_1
- **type:** creature
- **creature_file:** scenario/creatures/shadowbeast.md
- **soul_file:** scenario/creatures/shadowbeast_soul.md
- **identity_file:** scenario/creatures/shadowbeast_identity.md
- **faction:** hostile
- **pronouns:** it/its
- **weapons:** shadowbeast_claw+4
- **armor:** natural_armor_shadowbeast
- **dopamine:** 0.8
- **cortisol:** 0.1
- **norepinephrine:** 0.85
- **endorphins:** 0.9
- **serotonin:** 0.2
- **acetylcholine:** 0.9
- **oxytocin:** 0.0
- **dopamine_baseline:** 0.7
- **dopamine_volatility:** 0.5
- **cortisol_baseline:** 0.1
- **cortisol_volatility:** 0.3
- **oxytocin_baseline:** 0.0
- **oxytocin_volatility:** 0.0

## Game State Sections
- header: Creatures in Scene | file: scenario/creatures/shadowbeast.md
- header: The Fey Glade Pool (DM Only) | file: scenario/places/mistwood_hills/fey_glade/LORE.md
- text: Exit Motivations (DM only) | file: scenario/places/mistwood_hills/fey_glade/PLACE.md#Exit Motivations
