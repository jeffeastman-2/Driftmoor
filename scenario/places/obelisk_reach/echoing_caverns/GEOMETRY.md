# GEOMETRY.md — The Echoing Caverns

## Scene

- **name:** The Echoing Caverns
- **place_path:** places/obelisk_reach/echoing_caverns
- **z_level:** 70.0
- **width:** 100.0
- **height:** 120.0
- **origin:** 3500.0, 13200.0, 70.0

Notes: A network of caves beneath the Obelisk Reach. Origin at
southwest corner. The entrance is a narrow crack in the cliff face
(easy to miss, DC 13 Perception). Inside, the caves open into
larger chambers connected by passages. Sounds echo unnaturally.
The air is cold. Father Elden's companions were lost in the deeper
chambers decades ago.

---

## Landmarks

| name              | x    | y    |
|-------------------|------|------|
| entrance_crack    | 30.0 | 100.0|
| entry_chamber     | 40.0 | 90.0 |
| first_passage     | 50.0 | 75.0 |
| echo_chamber      | 55.0 | 60.0 |
| deep_passage      | 40.0 | 45.0 |
| bone_chamber      | 35.0 | 25.0 |
| underground_pool  | 60.0 | 35.0 |
| ancient_carvings  | 25.0 | 50.0 |
| collapsed_tunnel  | 70.0 | 20.0 |

---

## Zones

| name             | render_z | vertices                              |
|------------------|----------|---------------------------------------|
| ENTRY_CHAMBER    | 2        | (30,80) (55,80) (55,100) (30,100)      |
| ECHO_CHAMBER     | 2        | (40,50) (70,50) (70,70) (40,70)        |
| BONE_CHAMBER     | 2        | (20,15) (50,15) (50,35) (20,35)        |
| DEEP_PASSAGE     | 1        | (30,35) (50,35) (50,50) (30,50)        |
| FIRST_PASSAGE    | 1        | (40,70) (60,70) (60,80) (40,80)        |
| POOL_CAVERN      | 1        | (50,25) (75,25) (75,45) (50,45)        |
| CAVES            | 0        | (0,0) (100,0) (100,120) (0,120)        |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Cave walls north   | (0,105) (100,105) (100,120) (0,120)    |
| Collapsed tunnel   | (65,15) (80,15) (80,25) (65,25)        |
| Underground pool   | (53,28) (68,28) (68,42) (53,42)        |
| Rock fall          | (15,55) (25,55) (25,65) (15,65)        |

---

## Connections

| name              | x    | y     | destination                              |
|-------------------|------|-------|------------------------------------------|
| entrance_crack    | 30.0 | 105.0 | places/obelisk_reach                     |
| to_obelisk_above  | 50.0 | 95.0  | places/obelisk_reach/shattered_obelisk   |

---

## Boundaries

### Unnatural Echoes

- **type:** magical
- **blocks:** none
- **effect:** sounds carry and distort unnaturally; Perception checks at disadvantage for locating sound sources; occasionally sounds resolve into voice-like fragments
- **vertices:** (20,10) (75,10) (75,75) (20,75)
