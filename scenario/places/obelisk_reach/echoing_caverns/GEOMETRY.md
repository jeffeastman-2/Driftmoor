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
| entrance_crack    | 97.5 | 325.0|
| entry_chamber     | 130.0 | 292.5 |
| first_passage     | 162.5 | 243.75 |
| echo_chamber      | 178.75 | 195.0 |
| deep_passage      | 130.0 | 146.25 |
| bone_chamber      | 113.75 | 81.25 |
| underground_pool  | 195.0 | 113.75 |
| ancient_carvings  | 81.25 | 162.5 |
| collapsed_tunnel  | 227.5 | 65.0 |

---

## Zones

| name             | render_z | vertices                              |
|------------------|----------|---------------------------------------|
| ENTRY_CHAMBER    | 6.5        | (97.5,260.0) (178.75,260.0) (178.75,325.0) (97.5,325.0)      |
| ECHO_CHAMBER     | 6.5        | (130.0,162.5) (227.5,162.5) (227.5,227.5) (130.0,227.5)        |
| BONE_CHAMBER     | 6.5        | (65.0,48.75) (162.5,48.75) (162.5,113.75) (65.0,113.75)        |
| DEEP_PASSAGE     | 3.25        | (97.5,113.75) (162.5,113.75) (162.5,162.5) (97.5,162.5)        |
| FIRST_PASSAGE    | 3.25        | (130.0,227.5) (195.0,227.5) (195.0,260.0) (130.0,260.0)        |
| POOL_CAVERN      | 3.25        | (162.5,81.25) (243.75,81.25) (243.75,146.25) (162.5,146.25)        |
| CAVES            | 0.0        | (0.0,0.0) (325.0,0.0) (325.0,390.0) (0.0,390.0)        |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Cave walls north   | (0.0,341.25) (325.0,341.25) (325.0,390.0) (0.0,390.0)    |
| Collapsed tunnel   | (211.25,48.75) (260.0,48.75) (260.0,81.25) (211.25,81.25)        |
| Underground pool   | (172.25,91.0) (221.0,91.0) (221.0,136.5) (172.25,136.5)        |
| Rock fall          | (48.75,178.75) (81.25,178.75) (81.25,211.25) (48.75,211.25)        |

---

## Connections

| name              | x    | y     | destination                              |
|-------------------|------|-------|------------------------------------------|
| entrance_crack    | 97.5 | 341.25 | places/obelisk_reach                     |
| to_obelisk_above  | 162.5 | 308.75  | places/obelisk_reach/shattered_obelisk   |

---

## Boundaries

### Unnatural Echoes

- **type:** magical
- **blocks:** none
- **effect:** sounds carry and distort unnaturally; Perception checks at disadvantage for locating sound sources; occasionally sounds resolve into voice-like fragments
- **vertices:** (65.0,32.5) (243.75,32.5) (243.75,243.75) (65.0,243.75)
