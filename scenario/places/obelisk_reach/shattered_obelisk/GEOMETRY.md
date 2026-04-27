# GEOMETRY.md — The Shattered Obelisk

## Scene

- **name:** The Shattered Obelisk
- **place_path:** places/obelisk_reach/shattered_obelisk
- **z_level:** 325.0
- **width:** 260.0
- **height:** 260.0
- **origin:** 10075.0, 43875.0, 325.0

Notes: A towering fractured stone spire. Origin at southwest corner
of the obelisk area. The base is roughly 32.5m across. Fallen sections
are scattered in a radiating pattern. The ground around the base is
scorched in old burn patterns. The surface hums with magical energy
and occasionally flickers with dark veins of light.

---

## Landmarks

| name              | x    | y    |
|-------------------|------|------|
| obelisk_base      | 130 | 146 |
| fallen_section_n  | 113 | 227 |
| fallen_section_e  | 211 | 162 |
| fallen_section_s  | 146 | 48 |
| scorch_center     | 130 | 130 |
| dark_vein_crack   | 136 | 156 |
| cavern_path       | 32 | 97 |

---

## Zones

| name            | render_z | vertices                              |
|-----------------|----------|---------------------------------------|
| OBELISK_BASE    | 9.75        | (107,123) (152,123) (152,169) (107,169)        |
| SCORCH_ZONE     | 6.5        | (65,65) (195,65) (195,195) (65,195)        |
| DEBRIS_FIELD    | 3.25        | (16,16) (243,16) (243,243) (16,243)            |
| EXTERIOR        | 0.0        | (0,0) (260,0) (260,260) (0,260)            |

---

## Impassable

| description       | vertices                              |
|-------------------|---------------------------------------|
| Obelisk structure | (113,130) (146,130) (146,162) (113,162)        |
| Fallen section N  | (97,211) (130,211) (130,243) (97,243)        |
| Fallen section E  | (195,146) (227,146) (227,178) (195,178)        |
| Fallen section S  | (130,32) (162,32) (162,65) (130,65)        |

---

## Connections

| name            | x    | y    | destination                          |
|-----------------|------|------|--------------------------------------|
| approach_south  | 130 | 0  | places/obelisk_reach                 |
| to_caverns_west | 16  | 97 | places/obelisk_reach/echoing_caverns |

---

## Boundaries

### Obelisk Energy Aura

- **type:** magical
- **blocks:** none
- **effect:** low vibration felt in the chest; obelisk-attuned characters feel drawn to the base; dark veins visible at night; Perception DC 39.0 to sense the hum from the debris field
- **vertices:** (65,65) (195,65) (195,195) (65,195)
