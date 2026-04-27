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
| entrance_crack    | 97 | 325|
| entry_chamber     | 130 | 292 |
| first_passage     | 162 | 243 |
| echo_chamber      | 178 | 195 |
| deep_passage      | 130 | 146 |
| bone_chamber      | 113 | 81 |
| underground_pool  | 195 | 113 |
| ancient_carvings  | 81 | 162 |
| collapsed_tunnel  | 227 | 65 |

---

## Zones

| name             | render_z | vertices                              |
|------------------|----------|---------------------------------------|
| ENTRY_CHAMBER    | 6.5      | (97,260) (178,260) (178,325) (97,325)      |
| FIRST_PASSAGE    | 6.5      | (130,227) (145,227) (145,260) (130,260)        |
| ECHO_CHAMBER     | 6.5      | (130,162) (227,162) (227,227) (130,227)        |
| DEEP_PASSAGE     | 3.25     | (150,113) (160,113) (160,162) (150,162)        |
| BONE_CHAMBER     | 6.5      | (65,48) (162,48) (162,113) (65,113)        |
| POOL_CAVERN      | 3.25     | (162,81) (243,81) (243,146) (162,146)        |
| CAVES            | 0.0      | (0,0) (325,0) (325,390) (0,390)        |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Cave walls north   | (0,341) (325,341) (325,390) (0,390)    |
| Collapsed tunnel   | (211,48) (260,48) (260,81) (211,81)        |
| Underground pool   | (172,91) (221,91) (221,136) (172,136)        |
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
