# GEOMETRY.md — Dustcloak's Curios

## Scene

- **name:** Dustcloak's Curios
- **place_path:** places/driftmoor/dustcloaks_curios
- **z_level:** 16.25
- **width:** 26
- **height:** 26
- **origin:** 212.5, 600.5, 0

Notes: Squat crooked structure on the outskirts near the Mistwood
Hills edge. Origin at southwest corner. The shopfront and backroom occupy the
ground floor; the living loft is a separate enterable scene above. Yard with
organized chaos outside.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_gate      | 13  | 0  |
| shopfront_ctr   | 13  | 6.5  |
| curiosity_shelf | 3  | 7  |
| east_curiosity_shelf | 23 | 7 |
| shop_counter    | 13  | 6.378 |
| display_table_w | 6.615   | 2.527 |
| display_table_e | 19.209  | 2.597 |
| curtain_door    | 13  | 12  |
| backroom_desk   | 8.499  | 22.609 |
| loft_staircase  | 22.5 | 18 |
| obelisk_cache   | 3.035  | 15.696 |
| appraisal_bench | 8.752 | 15.703 |
| locked_box      | 13.481 | 24.104 |
| yard_junk       | 9.424  | -4.632 |
| yard_wheels     | 6.223   | -4.511 |
| yard_furniture  | 19.666 | -4.355 |

---

## Zones

| name | render_z | auto_wall | vertices |
|------------|----------|---------|---------------------------------|
| BACKROOM | 6.5 |  | (0,11) (26,11) (26,26) (0,26) |
| SHOPFRONT | 3.25 |  | (0,0) (26,0) (26,11) (0,11) |
| YARD | 0.0 |  | (3,-6.5) (22.5,-6.5) (22.5,0) (3,0) |
| EXTERIOR | 0.0 |  | (-4.5,-9.5) (30.5,-9.5) (30.5,30.5) (-4.5,30.5) |
---

## Walls

- **auto_wall:** false

Hand-authored: the SHOPFRONT/BACKROOM boundary already has a working 9 ft
curtained archway (curtain_door) flanked by real wall — wider than the
default door-gap convention gives, and there's no "wide door" option yet.
Not broken, just doesn't fit the simple convention; opt out rather than
force a mismatch.

---

## Impassable

| description      | vertices                        |
|------------------|---------------------------------|
| Dividing wall west | (0,11) (10.5,11) (10.5,13) (0,13) |
| Dividing wall east | (19.5,11) (26,11) (26,13) (19.5,13) |
| Back wall        | (0,24) (26,24) (26,26) (0,26)   |

---

## Connections

| name           | x    | y    | destination                                             |
|----------------|------|------|---------------------------------------------------------|
| front_gate     | 13   | 0    | places/driftmoor                                        |
| to_living_loft | 22.5 | 17.5 | places/driftmoor/dustcloaks_curios/living_loft         |

---

## Boundaries

### Backroom — Private Research

- **type:** conditional
- **blocks:** all
- **effect:** curtained doorway; Kelem's private workspace with obelisk fragments; requires trust or deception to access
- **render:** hidden
- **vertices:** (0,11) (26,11) (26,26) (0,26)
