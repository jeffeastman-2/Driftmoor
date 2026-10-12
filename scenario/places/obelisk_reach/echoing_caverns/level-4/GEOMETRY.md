# GEOMETRY.md — The Royal Precinct of the Echoing Caverns

## Scene

- **name:** The Royal Precinct
- **place_path:** places/obelisk_reach/echoing_caverns/level-4
- **z_level:** -125
- **width:** 120
- **height:** 140
- **origin:** 11520.0, 42800.0, -125

Notes: A series of royal chambers carved with intricate detail, reflecting the
former glory of the buried kingdom. The air is colder here, carrying the
scent of ancient stone and the faint metallic tang of the deep earth. The
walls are lined with faded tapestries and cracked statuary. A narrow stairway
connects to level 3 above.

---

## Landmarks

| name                       | x   | y   |
|----------------------------|-----|-----|
| stairs_from_city_entrance  | 60 | 135 |
| royal_guard_checkpoint     | 59 | 112 |
| royal_guard_barracks_door  | 49 | 86 |
| court_kitchens_entrance    | 71 | 83 |
| hall_of_unchosen_queens    | 60 | 55 |
| treasury_antechamber_door  | 49 | 61 |
| throne_of_seven_chains     | 59 | 44 |

---

## Walls

- **auto_wall:** false

The Royal Precinct features both natural cave walls and architecturally
cut chambers. Some passages have iron doors, while others connect via open
archways.

## Zones

| name | auto_wall | vertices |
|------------------|---------|---------------------------------------------------------------------------------------------------|
| Stairs from City | false | (51,118,-125) (70,118,-125) (65,138,-125) (55,138,-125) |
| Royal Guard Checkpoint | false | (43,104,-125) (76,104,-125) (76,118,-125) (43,118,-125) |
| Royal Guard Barracks | false | (26,68,-125) (49,68,-125) (49,103,-125) (26,103,-125) |
| Court Kitchens | false | (71,68,-125) (94,68,-125) (94,103,-125) (71,103,-125) |
| Hall of Unchosen Queens | false | (49,56,-125) (71,56,-125) (71,104,-125) (49,104,-125) |
| Treasury Antechamber | false | (39,58,-125) (49,58,-125) (49,64,-125) (28,64,-125) (28,50,-125) (39,50,-125) |
| Royal Treasury | false | (11,30,-125) (39,30,-125) (39,50,-125) (11,50,-125) |
| Throne of Seven Chains | false | (46,33,-125) (74,33,-125) (74,56,-125) (46,56,-125) |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
|| (0,0) (120,0) (120,140) (0,140) | (0,0) (120,0) (120,140) (0,140) |

---

## Items

| id                  | x   | y   | z   | label              |
|---------------------|-----|-----|-----|--------------------|
| faded_tapestries    | 71 | 65 |  8  | Faded tapestries   |
| cracked_statuary    | 60 | 55 |  5  | Cracked statuary   |
| rusted_gate_lever   | 61 | 118 |  3  | Rusted gate lever  |
| guard_barracks_lock | 49 | 85 |  4  | Barracks lock      |
| kitchen_utensils    | 82 | 85 |  4  | Kitchen utensils   |
| treasury_door_knob  | 34 | 50 |  4  | Treasury door knob |
| seven_chains        | 59 | 45 |  2  | Seven chains       |
| royal_crest         | 60 | 90 | 10  | Royal crest        |
| broken_scepter      | 50 | 63 |  1  | Broken scepter     |

---

## Ambient Visibility

The Royal Precinct is poorly lit. Torches burn in wall brackets along the
main corridors, but side chambers dim quickly. The throne room is lit by a
single, perpetually burning candelabrum.

- **default:** 30

---

## Connections

| name              | x    | y     | destination                              |
|-------------------|------|-------|------------------------------------------|
| stairs_from_city  | 60 | 138 | places/obelisk_reach/echoing_caverns/level-3 |

---

## Boundaries

### Royal Sanctity
- **type:** magical
- **blocks:** none
- **effect:** creatures without royal blood feel a sense of unease and are disadvantaged on Perception checks
- **vertices:** (8,27) (80,27) (80,105) (9,106)

### Throne Binding
- **type:** magical
- **blocks:** planar travel
- **effect:** teleportation and planar travel spells fail within the throne room
- **vertices:** (47,34) (73,34) (73,55) (47,55)
