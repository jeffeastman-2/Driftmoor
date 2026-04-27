# GEOMETRY.md — Dustcloak's Curios

## Scene

- **name:** Dustcloak's Curios
- **place_path:** places/driftmoor/dustcloaks_curios
- **z_level:** 16.25
- **width:** 52.0
- **height:** 52.0
- **origin:** 8927.75, 9064.25, 16.25

Notes: Squat crooked structure on the outskirts near the Mistwood
Hills edge. Origin at southwest corner. Three levels: shopfront
(ground floor front), backroom (ground floor rear through curtained
doorway), and living loft above. Yard with organized chaos outside.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_gate      | 26  | 0  |
| shopfront_ctr   | 26  | 13  |
| curiosity_shelf | 9  | 16  |
| curtain_door    | 26  | 22  |
| backroom_desk   | 26  | 35 |
| loft_staircase  | 45 | 35 |
| obelisk_cache   | 13  | 39 |
| yard_junk       | 26  | -6 |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| LOFT       | 9.75        | (13,26) (52,26) (52,52) (13,52)     |
| BACKROOM   | 6.5        | (0,22) (52,22) (52,52) (0,52)     |
| SHOPFRONT  | 3.25        | (0,0) (52,0) (52,22) (0,22)       |
| YARD       | 0.0        | (6,-13) (45,-13) (45,0) (6,0)     |
| EXTERIOR   | 0.0        | (-9,-19) (61,-19) (61,61) (-9,61)  |

---

## Impassable

| description      | vertices                        |
|------------------|---------------------------------|
| Dividing wall    | (0,22) (52,22) (52,26) (0,26)       |
| Back wall        | (0,48) (52,48) (52,52) (0,52)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_gate | 26 | 0 | places/driftmoor |

---

## Boundaries

### Backroom — Private Research

- **type:** conditional
- **blocks:** all
- **effect:** curtained doorway; Kelem's private workspace with obelisk fragments; requires trust or deception to access
- **vertices:** (0,22) (52,22) (52,52) (0,52)
