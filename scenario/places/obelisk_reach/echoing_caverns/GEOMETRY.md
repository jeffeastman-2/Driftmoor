# GEOMETRY.md — The Echoing Caverns

## Scene

- **name:** The Echoing Caverns
- **place_path:** places/obelisk_reach/echoing_caverns
- **z_level:** 227.5
- **width:** 325.0
- **height:** 390.0
- **origin:** 11375.0, 42900.0, 227.5

Notes: A network of caves beneath the Obelisk Reach. Origin at
southwest corner. The entrance is a narrow crack in the cliff face
(easy to miss, DC 42.25 Perception). Inside, the caves open into
larger chambers connected by passages. Sounds echo unnaturally.
The air is cold. Father Elden's companions were lost in the deeper
chambers decades ago.

---

## Landmarks

| name              | x    | y    |
|-------------------|------|------|
| entrance_crack    | 110 | 325|
| ancient_carvings  | 160 | 170 |

---

## Zones

| name             | vertices                                                                                          |
|------------------|---------------------------------------------------------------------------------------------------|
| Entry Chamber    | (97,260,0.0) (178,260,0.0) (178,325,0.0) (97,325,0.0)                                             |
| First Passage    | (130,227,-2) (145,227,-2) (145,260,0.0) (130,260,0.0)                                       |
| Echo Chamber     | (130,162,-2) (227,162,-2) (227,227,-2) (130,227,-2)                                       |
| Rocky Passage    | (81,190,-5) (81,200,-5) (130,200,-2) (130,190,-2)                                         |
| Deep Passage     | (150,113,-10) (160,113,-10) (160,162,-2) (150,162,-2)                                       |
| Bone Chamber     | (65,48,-10) (162,48,-10) (162,113,-10) (65,113,-10)                                           |
| Pool Cavern      | (162,81,-10) (243,81,-10) (243,146,-10) (162,146,-10)                                         |
| Solid Rock       | (0,0,-20) (300,0,-20) (300,325,-20) (0,325,-20)                                               |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Collapsed tunnel   | (211,48) (221,48) (221,81) (211,81)        |
| Underground pool   | (190,91) (221,91) (221,110) (190,110)        |
| Rock fall          | (48,178) (81,178) (81,211) (48,211)        |

---

## Connections

| name              | x    | y     | destination                              |
|-------------------|------|-------|------------------------------------------|
| entrance_crack    | 97 | 341 | places/obelisk_reach                     |
| to_obelisk_above  | 162 | 308  | places/obelisk_reach/shattered_obelisk   |

---

## Boundaries

### Unnatural Echoes

- **type:** magical
- **blocks:** none
- **effect:** sounds carry and distort unnaturally; Perception checks at disadvantage for locating sound sources; occasionally sounds resolve into voice-like fragments
- **vertices:** (65,32) (243,32) (243,243) (65,243)
