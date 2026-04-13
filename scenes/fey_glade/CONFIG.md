# Scene Config — The Fey Glade

## Scene
- **scene_name:** fey_glade
- **title:** FEY GLADE
- **narrative_title:** The Fey Glade
- **transcript_title:** FEY GLADE ENCOUNTER — Aeliana, Fennel, Shadowbeast
- **character_summary:** Aeliana (Grok), Fennel (GPT-4o), Shadowbeast (DeepSeek)
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
- **provider:** anthropic
- **model:** claude-sonnet-4-20250514

## Characters

### aeliana
- **type:** player
- **soul_file:** scenario/people/players/aeliana/SOUL.md
- **identity_file:** scenario/people/players/aeliana/IDENTITY.md
- **provider:** xai
- **model:** grok-3
- **scene_handle:** the elf ranger
- **pronouns:** she/her
- **dopamine:** 0.85
- **cortisol:** 0.25
- **norepinephrine:** 0.55
- **endorphins:** 0.75
- **serotonin:** 0.6
- **acetylcholine:** 0.5
- **oxytocin:** 0.5
- **dopamine_baseline:** 0.55
- **dopamine_volatility:** 0.8
- **cortisol_baseline:** 0.35
- **cortisol_volatility:** 0.6

### fennel
- **type:** player
- **soul_file:** scenario/people/npcs/fennel/SOUL.md
- **identity_file:** scenario/people/npcs/fennel/IDENTITY.md
- **provider:** openai
- **model:** gpt-4o
- **scene_handle:** the young gatherer
- **pronouns:** he/him
- **dopamine:** 0.5
- **cortisol:** 0.6
- **norepinephrine:** 0.75
- **endorphins:** 0.45
- **serotonin:** 0.5
- **acetylcholine:** 0.65
- **oxytocin:** 0.3
- **dopamine_baseline:** 0.5
- **dopamine_volatility:** 1.0
- **cortisol_baseline:** 0.4
- **cortisol_volatility:** 1.2

### shadowbeast_1
- **type:** creature
- **creature_file:** scenario/creatures/shadowbeast.md
- **soul_file:** scenario/creatures/shadowbeast_soul.md
- **identity_file:** scenario/creatures/shadowbeast_identity.md
- **faction:** hostile
- **provider:** deepseek
- **model:** deepseek-chat
- **pronouns:** it/its
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
