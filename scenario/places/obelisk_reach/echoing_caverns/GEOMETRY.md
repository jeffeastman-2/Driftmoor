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

| name                       | x   | y   |
|----------------------------|-----|-----|
| entrance_crack             | 110 | 325 |
| ancient_carvings           | 160 | 170 |
| first_passage_mouth        | 137 | 260 |
| echo_chamber_arch          | 137 | 227 |
| rocky_passage_squeeze      | 130 | 195 |
| deep_passage_descent       | 155 | 162 |
| pool_passage_descent       | 205 | 162 |
| bone_chamber_threshold     | 155 | 113 |
| pool_cavern_threshold      | 205 | 146 |
| collapsed_tunnel_rubble    | 216 | 82  |
| hidden_cavern_opening      | 216 | 47  |

---

## Zones

| name             | vertices                                                                                          |
|------------------|---------------------------------------------------------------------------------------------------|
| Entry Chamber    | (97,260,0.0) (178,260,0.0) (178,325,0.0) (97,325,0.0)|
| First Passage    | (130,227,-2) (145,227,-2) (145,260,0.0) (130,260,0.0)|
| Echo Chamber     | (130,162,-2) (227,162,-2) (227,227,-2) (130,227,-2)|
| Rocky Passage    | (81,190,-5) (81,200,-5) (130,200,-2) (130,190,-2)|
| Deep Passage     | (150,113,-10) (160,113,-10) (160,162,-2) (150,162,-2)|
| Pool Passage     | (200,146,-10) (210,146,-10) (210,162,-2) (200,162,-2)|
| Bone Chamber     | (65,48,-10) (162,48,-10) (162,113,-10) (65,113,-10)|
| Pool Cavern      | (170,81,-10) (243,81,-10) (243,146,-10) (170,146,-10)|
| Collapsed Tunnel | (211,48,-20) (221,48,-10) (221,81,-10) (211,81,-20)|
| Hidden Cavern    | (210,48,-20) (243,48,-20) (243,31,-20) (210,31,-20)|

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Collapsed Tunnel   | (211,48) (221,48) (221,81) (211,81)        |
| Underground pool   | (190,91) (221,91) (221,110) (190,110)        |
| Rock fall          | (48,178) (81,178) (81,211) (48,211)        |
| Solid Rock         | (0,0) (300,0) (300,325) (0,325)            |

---

## Items

| id                  | x   | y   | label              |
|---------------------|-----|-----|--------------------|
| torch_bracket       | 100 | 270 | Torch bracket      |
| wall_scratches      | 115 | 320 | Tally scratches    |
| carved_symbols      | 222 | 200 | Carved symbols     |
| obelisk_fragment    | 178 | 195 | Obelisk fragment   |
| companion_remains   | 88  | 75  | Skeletal remains   |
| holy_symbol_pelor   | 92  | 78  | Holy symbol        |
| parchment_fragment  | 96  | 73  | Parchment fragment |

---

## Connections

| name              | x    | y     | destination                              |
|-------------------|------|-------|------------------------------------------|
| entrance_crack    | 97   | 341   | places/obelisk_reach                     |
| to_obelisk_above  | 162  | 308   | places/obelisk_reach/shattered_obelisk   |

---

## Boundaries

### Unnatural Echoes

- **type:** magical
- **blocks:** none
- **effect:** sounds carry and distort unnaturally; Perception checks at disadvantage for locating sound sources; occasionally sounds resolve into voice-like fragments
- **vertices:** (65,160) (243,160) (243,243) (65,243)

---

## Starting Positions

| character   | x   | y   | zone          |
|-------------|-----|-----|---------------|
| thorgrim    | 138 | 295 | Entry Chamber |
| amara       | 120 | 305 | Entry Chamber |
| seraphina   | 155 | 285 | Entry Chamber |
