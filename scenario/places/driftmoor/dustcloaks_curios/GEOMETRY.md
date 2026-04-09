# GEOMETRY.md — Dustcloak's Curios

## Scene

- **name:** Dustcloak's Curios
- **place_path:** places/driftmoor/dustcloaks_curios
- **z_level:** 5.0
- **width:** 16.0
- **height:** 16.0
- **origin:** 2747.0, 2789.0, 5.0

Notes: Squat crooked structure on the outskirts near the Mistwood
Hills edge. Origin at southwest corner. Three levels: shopfront
(ground floor front), backroom (ground floor rear through curtained
doorway), and living loft above. Yard with organized chaos outside.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_gate      | 8.0  | 0.0  |
| shopfront_ctr   | 8.0  | 4.0  |
| curiosity_shelf | 3.0  | 5.0  |
| curtain_door    | 8.0  | 7.0  |
| backroom_desk   | 8.0  | 11.0 |
| loft_staircase  | 14.0 | 11.0 |
| obelisk_cache   | 4.0  | 12.0 |
| yard_junk       | 8.0  | -2.0 |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| LOFT       | 3        | (4,8) (16,8) (16,16) (4,16)     |
| BACKROOM   | 2        | (0,7) (16,7) (16,16) (0,16)     |
| SHOPFRONT  | 1        | (0,0) (16,0) (16,7) (0,7)       |
| YARD       | 0        | (2,-4) (14,-4) (14,0) (2,0)     |
| EXTERIOR   | 0        | (-3,-6) (19,-6) (19,19) (-3,19)  |

---

## Impassable

| description      | vertices                        |
|------------------|---------------------------------|
| Dividing wall    | (0,7) (16,7) (16,8) (0,8)       |
| Back wall        | (0,15) (16,15) (16,16) (0,16)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_gate | 8.0 | 0.0 | places/driftmoor |

---

## Boundaries

### Backroom — Private Research

- **type:** conditional
- **blocks:** all
- **effect:** curtained doorway; Kelem's private workspace with obelisk fragments; requires trust or deception to access
- **vertices:** (0,7) (16,7) (16,16) (0,16)
