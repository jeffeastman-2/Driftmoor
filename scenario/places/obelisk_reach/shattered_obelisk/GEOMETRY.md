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
| obelisk_base      | 130.0 | 146.25 |
| fallen_section_n  | 113.75 | 227.5 |
| fallen_section_e  | 211.25 | 162.5 |
| fallen_section_s  | 146.25 | 48.75 |
| scorch_center     | 130.0 | 130.0 |
| dark_vein_crack   | 136.5 | 156.0 |
| cavern_path       | 32.5 | 97.5 |

---

## Zones

| name            | render_z | vertices                              |
|-----------------|----------|---------------------------------------|
| OBELISK_BASE    | 9.75        | (107.25,123.5) (152.75,123.5) (152.75,169.0) (107.25,169.0)        |
| SCORCH_ZONE     | 6.5        | (65.0,65.0) (195.0,65.0) (195.0,195.0) (65.0,195.0)        |
| DEBRIS_FIELD    | 3.25        | (16.25,16.25) (243.75,16.25) (243.75,243.75) (16.25,243.75)            |
| EXTERIOR        | 0.0        | (0.0,0.0) (260.0,0.0) (260.0,260.0) (0.0,260.0)            |

---

## Impassable

| description       | vertices                              |
|-------------------|---------------------------------------|
| Obelisk structure | (113.75,130.0) (146.25,130.0) (146.25,162.5) (113.75,162.5)        |
| Fallen section N  | (97.5,211.25) (130.0,211.25) (130.0,243.75) (97.5,243.75)        |
| Fallen section E  | (195.0,146.25) (227.5,146.25) (227.5,178.75) (195.0,178.75)        |
| Fallen section S  | (130.0,32.5) (162.5,32.5) (162.5,65.0) (130.0,65.0)        |

---

## Connections

| name            | x    | y    | destination                          |
|-----------------|------|------|--------------------------------------|
| approach_south  | 130.0 | 0.0  | places/obelisk_reach                 |
| to_caverns_west | 16.25  | 97.5 | places/obelisk_reach/echoing_caverns |

---

## Boundaries

### Obelisk Energy Aura

- **type:** magical
- **blocks:** none
- **effect:** low vibration felt in the chest; obelisk-attuned characters feel drawn to the base; dark veins visible at night; Perception DC 39.0 to sense the hum from the debris field
- **vertices:** (65.0,65.0) (195.0,65.0) (195.0,195.0) (65.0,195.0)
