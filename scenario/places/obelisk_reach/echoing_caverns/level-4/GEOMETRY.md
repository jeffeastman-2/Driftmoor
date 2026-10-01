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
| stairs_from_city_entrance  | 60  | 130 |
| royal_guard_checkpoint     | 60  | 110 |
| royal_guard_barracks_door  | 45  | 85  |
| court_kitchens_entrance    | 75  | 85  |
| hall_of_unchosen_queens    | 60  | 55  |
| treasury_antechamber_door  | 60  | 35  |
| throne_of_seven_chains     | 60  | 15  |

---

## Walls

- **auto_wall:** false

The Royal Precinct features both natural cave walls and architecturally
cut chambers. Some passages have iron doors, while others connect via open
archways.

## Zones

| name | auto_wall | vertices |
|------------------|---------|---------------------------------------------------------------------------------------------------|
| Stairs from City | false | (31,118,-125) (89,118,-125) (89,138,-125) (31,138,-125) |
| Royal Guard Checkpoint | false | (31,98,-125) (89,98,-125) (89,118,-125) (31,118,-125) |
| Royal Guard Barracks | false | (26,68,-125) (49,68,-125) (49,103,-125) (26,103,-125) |
| Court Kitchens | false | (71,68,-125) (94,68,-125) (94,103,-125) (71,103,-125) |
| Hall of Unchosen Queens | false | (31,38,-125) (89,38,-125) (89,83,-125) (31,83,-125) |
| Treasury Antechamber | false | (46,28,-125) (74,28,-125) (74,48,-125) (46,48,-125) |
| Royal Treasury | false | (46,8,-125) (74,8,-125) (74,28,-125) (46,28,-125) |
| Throne of Seven Chains | false | (46,0,-125) (74,0,-125) (74,18,-125) (46,18,-125) |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Collapsed Treasury | (46,8) (74,8) (74,28) (46,28)        |
| Solid Rock         | (0,0) (120,0) (120,140) (0,140)        |

---

## Items

| id                  | x   | y   | z   | label              |
|---------------------|-----|-----|-----|--------------------|
| faded_tapestries    | 60  | 65  |  8  | Faded tapestries   |
| cracked_statuary    | 60  | 55  |  5  | Cracked statuary   |
| rusted_gate_lever   | 60  | 110 |  3  | Rusted gate lever  |
| guard_barracks_lock | 37  | 85  |  4  | Barracks lock      |
| kitchen_utensils    | 82  | 85  |  4  | Kitchen utensils   |
| treasury_door_knob  | 60  | 38  |  4  | Treasury door knob |
| seven_chains        | 60  | 9   |  2  | Seven chains       |
| royal_crest         | 60  | 90  | 10  | Royal crest        |
| broken_scepter      | 60  | 9   |  1  | Broken scepter     |

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
| stairs_from_city  | 60   | 138   | places/obelisk_reach/echoing_caverns/level-3 |

---

## Boundaries

### Royal Sanctity
- **type:** magical
- **blocks:** none
- **effect:** creatures without royal blood feel a sense of unease and are disadvantaged on Perception checks
- **vertices:** (31,0) (89,0) (89,140) (31,140)

### Throne Binding
- **type:** magical
- **blocks:** planar travel
- **effect:** teleportation and planar travel spells fail within the throne room
- **vertices:** (46,0) (74,0) (74,18) (46,18)
