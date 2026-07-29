# GEOMETRY.md — Dustcloak's Curios

## Scene

- **name:** Dustcloak's Curios
- **place_path:** places/driftmoor/dustcloaks_curios
- **z_level:** 16.25
- **width:** 26
- **height:** 26
- **origin:** 212.5, 600.5, 0

Notes: Squat crooked structure on the outskirts near the Mistwood
Hills edge. Origin at southwest corner. Three levels: shopfront
(ground floor front), backroom (ground floor rear through curtained
doorway), and living loft above. Yard with organized chaos outside.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_gate      | 13  | 0  |
| shopfront_ctr   | 13  | 6.5  |
| curiosity_shelf | 4.5  | 8  |
| curtain_door    | 13  | 11  |
| backroom_desk   | 13  | 17.5 |
| loft_staircase  | 22.5 | 17.5 |
| obelisk_cache   | 6.5  | 19.5 |
| yard_junk       | 13  | -3 |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| LOFT       | 9.75        | (6.5,13) (26,13) (26,26) (6.5,26)     |
| BACKROOM   | 6.5        | (0,11) (26,11) (26,26) (0,26)     |
| SHOPFRONT  | 3.25        | (0,0) (26,0) (26,11) (0,11)       |
| YARD       | 0.0        | (3,-6.5) (22.5,-6.5) (22.5,0) (3,0)     |
| EXTERIOR   | 0.0        | (-4.5,-9.5) (30.5,-9.5) (30.5,30.5) (-4.5,30.5)  |

---

## Impassable

| description      | vertices                        |
|------------------|---------------------------------|
| Dividing wall    | (0,11) (26,11) (26,13) (0,13)       |
| Back wall        | (0,24) (26,24) (26,26) (0,26)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_gate | 13 | 0 | places/driftmoor |

---

## Boundaries

### Backroom — Private Research

- **type:** conditional
- **blocks:** all
- **effect:** curtained doorway; Kelem's private workspace with obelisk fragments; requires trust or deception to access
- **vertices:** (0,11) (26,11) (26,26) (0,26)
