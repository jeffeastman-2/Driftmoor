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
| front_gate      | 26.0  | 0.0  |
| shopfront_ctr   | 26.0  | 13.0  |
| curiosity_shelf | 9.75  | 16.25  |
| curtain_door    | 26.0  | 22.75  |
| backroom_desk   | 26.0  | 35.75 |
| loft_staircase  | 45.5 | 35.75 |
| obelisk_cache   | 13.0  | 39.0 |
| yard_junk       | 26.0  | -6.5 |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| LOFT       | 9.75        | (13.0,26.0) (52.0,26.0) (52.0,52.0) (13.0,52.0)     |
| BACKROOM   | 6.5        | (0.0,22.75) (52.0,22.75) (52.0,52.0) (0.0,52.0)     |
| SHOPFRONT  | 3.25        | (0.0,0.0) (52.0,0.0) (52.0,22.75) (0.0,22.75)       |
| YARD       | 0.0        | (6.5,-13.0) (45.5,-13.0) (45.5,0.0) (6.5,0.0)     |
| EXTERIOR   | 0.0        | (-9.75,-19.5) (61.75,-19.5) (61.75,61.75) (-9.75,61.75)  |

---

## Impassable

| description      | vertices                        |
|------------------|---------------------------------|
| Dividing wall    | (0.0,22.75) (52.0,22.75) (52.0,26.0) (0.0,26.0)       |
| Back wall        | (0.0,48.75) (52.0,48.75) (52.0,52.0) (0.0,52.0)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_gate | 26.0 | 0.0 | places/driftmoor |

---

## Boundaries

### Backroom — Private Research

- **type:** conditional
- **blocks:** all
- **effect:** curtained doorway; Kelem's private workspace with obelisk fragments; requires trust or deception to access
- **vertices:** (0.0,22.75) (52.0,22.75) (52.0,52.0) (0.0,52.0)
