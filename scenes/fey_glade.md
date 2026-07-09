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
- **position:** 256, 81

## Game State Sections
- header: Creatures in Scene | file: scenario/creatures/shadowbeast/CREATURE.md
- header: The Fey Glade Pool (DM Only) | file: scenario/places/mistwood_hills/fey_glade/LORE.md
- text: Exit Motivations (DM only) | file: scenario/places/mistwood_hills/fey_glade/PLACE.md#Exit Motivations
