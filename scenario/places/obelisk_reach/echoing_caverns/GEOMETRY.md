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
(easy to miss, DC 13 Perception). Inside, the caves open into
larger chambers connected by passages. Sounds echo unnaturally.
The air is cold. Father Elden's companions were lost in the deeper 
chambers years ago.

---

## Landmarks

| name                       | x   | y   |
|----------------------------|-----|-----|
| entrance_crack             | 110 | 325 |
| ancient_carvings           | 160 | 170 |
| first_passage_mouth        | 154 | 262 |
| echo_chamber_arch          | 154 | 227 |
| rocky_passage_squeeze      | 130 | 195 |
| secret_chamber_threshold   | 81 | 195 |
| deep_passage_descent       | 149 | 161 |
| pool_passage_descent       | 205 | 162 |
| bone_chamber_threshold     | 135 | 113 |
| pool_cavern_threshold      | 205 | 146 |
| collapsed_tunnel_rubble    | 216 | 82 |
| hidden_cavern_opening      | 216 | 47 |

---

## Walls

- **auto_wall:** false

Natural cave passages (rocky_passage_squeeze, secret_chamber_threshold,
deep_passage_descent, etc.), not architected rooms with doors — none of
the passage landmarks follow the *_door/*_archway naming convention (the
closest, echo_chamber_arch, doesn't even match on the literal word), so
turning this on would seal every chamber shut with no route between them.

## Zones

| name | auto_wall | vertices |
|------------------|---------|---------------------------------------------------------------------------------------------------|
| Entry Chamber |  | (115,262,0) (167,262,0) (174,276,0) (176,294,0) (175,311,0) (158,325,0) (109,325,0) (97,311,0) (96,293,0) (98,276,0) |
| First Passage |  | (148,227,-2) (160,227,-2) (160,262,0) (148,262,0) |
| Echo Chamber |  | (140,161,-2) (216,162,-2) (226,174,-2) (226,213,-2) (212,223,-2) (196,227,-2) (146,227,-2) (130,213,-2) (130,176,-2) |
| Rocky Passage |  | (81,190,-5) (81,200,-5) (130,200,-2) (130,190,-2) |
| Secret Chamber |  | (56,178,-5) (74,178,-5) (82,183,-5) (81,206,-5) (74,211,-5) (54,210,-5) (48,205,-5) (48,187,-5) |
| Deep Passage |  | (129,113,-10) (141,113,-10) (154,161,-2) (143,161,-2) |
| Pool Passage |  | (200,146,-10) (210,146,-10) (210,162,-2) (200,162,-2) |
| Bone Chamber |  | (115,66,-10) (141,70,-10) (159,83,-10) (162,98,-10) (154,113,-10) (105,113,-10) (85,110,-10) (74,98,-10) (72,83,-10) (77,70,-10) |
| Pool Cavern |  | (184,81,-10) (231,81,-10) (241,92,-10) (244,114,-10) (242,128,-10) (228,146,-10) (185,146,-10) (170,130,-10) (167,114,-10) (170,93,-10) |
| Collapsed Tunnel |  | (211,48,-20) (221,48,-10) (221,81,-10) (211,81,-20) |
| Hidden Cavern |  | (199,48,-20) (227,48,-20) (239,45,-20) (238,37,-20) (229,31,-20) (202,31,-20) (194,38,-20) |
---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Collapsed Tunnel   | (211,48) (221,48) (221,81) (211,81) |
| Underground pool   | (190,91) (221,91) (221,110) (190,110) |
| Solid Rock         | (0,0) (300,0) (300,325) (0,325) |

---

## Items

| id                  | x   | y   | z   | label              |
|---------------------|-----|-----|-----|--------------------|
| torch_bracket       | 102 | 315 |  6  | Torch bracket      |
| wall_scratches      | 118 | 323 |  3  | Tally scratches    |
| snapped_torch       | 136 | 278 |     | Snapped torch      |
| old_bloodstain      | 153 | 266 |     | Dark stain         |
| discarded_pack      | 141 | 286 |     | Discarded pack     |
| drag_marks          | 146 | 277 |     | Drag marks         |
| carved_symbols      | 224 | 200 |  5  | Carved symbols     |
| obelisk_fragment    | 178 | 195 |     | Obelisk fragment   |
| trigger_glyph_top    | 130 | 196 |  5  | Trigger glyph (top)    |
| trigger_glyph_middle | 130 | 196 | 4.5 | Trigger glyph (middle) |
| trigger_glyph_bottom | 130 | 196 |  4  | Trigger glyph (bottom) |
| secret_burial_vault | 64 | 195 |     | Burial vault       |
| mace_plus_one       | 64 | 195 |  3  | Mace +1            |
| companion_remains   | 89 | 81 |     | Skeletal remains   |
| holy_symbol_pelor   | 92 | 87 |     | Holy symbol        |
| parchment_fragment  | 97 | 80 |     | Parchment fragment |

---

## Ambient Visibility

Unlit caverns. Without another light source a creature sees only as far as
its torch throws (or as far as its darkvision reaches). Mist plays no part
here — sight is purely light-limited, so darkvision extends it fully.

- **default:** 25

---

## Connections

| name              | x    | y     | destination                              |
|-------------------|------|-------|------------------------------------------|
| entrance_crack    | 110 | 325 | places/obelisk_reach                     |
| to_obelisk_above  | 162 | 308 | places/obelisk_reach/shattered_obelisk   |
| hidden_cavern_opening | 216 | 47 | places/obelisk_reach/echoing_caverns/sleeping_city |

---

## Boundaries

### Unnatural Echoes

- **type:** magical
- **blocks:** none
- **effect:** sounds carry and distort unnaturally; Perception checks at disadvantage for locating sound sources; occasionally sounds resolve into voice-like fragments
- **vertices:** (112,151) (244,151) (243,239) (113,240)

---
