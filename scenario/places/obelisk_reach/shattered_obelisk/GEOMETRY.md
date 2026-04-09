# GEOMETRY.md — The Shattered Obelisk

## Scene

- **name:** The Shattered Obelisk
- **place_path:** places/obelisk_reach/shattered_obelisk
- **z_level:** 100.0
- **width:** 80.0
- **height:** 80.0
- **origin:** 3100.0, 13500.0, 100.0

Notes: A towering fractured stone spire. Origin at southwest corner
of the obelisk area. The base is roughly 10m across. Fallen sections
are scattered in a radiating pattern. The ground around the base is
scorched in old burn patterns. The surface hums with magical energy
and occasionally flickers with dark veins of light.

---

## Landmarks

| name              | x    | y    |
|-------------------|------|------|
| obelisk_base      | 40.0 | 45.0 |
| fallen_section_n  | 35.0 | 70.0 |
| fallen_section_e  | 65.0 | 50.0 |
| fallen_section_s  | 45.0 | 15.0 |
| scorch_center     | 40.0 | 40.0 |
| dark_vein_crack   | 42.0 | 48.0 |
| cavern_path       | 10.0 | 30.0 |

---

## Zones

| name            | render_z | vertices                              |
|-----------------|----------|---------------------------------------|
| OBELISK_BASE    | 3        | (33,38) (47,38) (47,52) (33,52)        |
| SCORCH_ZONE     | 2        | (20,20) (60,20) (60,60) (20,60)        |
| DEBRIS_FIELD    | 1        | (5,5) (75,5) (75,75) (5,75)            |
| EXTERIOR        | 0        | (0,0) (80,0) (80,80) (0,80)            |

---

## Impassable

| description       | vertices                              |
|-------------------|---------------------------------------|
| Obelisk structure | (35,40) (45,40) (45,50) (35,50)        |
| Fallen section N  | (30,65) (40,65) (40,75) (30,75)        |
| Fallen section E  | (60,45) (70,45) (70,55) (60,55)        |
| Fallen section S  | (40,10) (50,10) (50,20) (40,20)        |

---

## Connections

| name            | x    | y    | destination                          |
|-----------------|------|------|--------------------------------------|
| approach_south  | 40.0 | 0.0  | places/obelisk_reach                 |
| to_caverns_west | 5.0  | 30.0 | places/obelisk_reach/echoing_caverns |

---

## Boundaries

### Obelisk Energy Aura

- **type:** magical
- **blocks:** none
- **effect:** low vibration felt in the chest; obelisk-attuned characters feel drawn to the base; dark veins visible at night; Perception DC 12 to sense the hum from the debris field
- **vertices:** (20,20) (60,20) (60,60) (20,60)
