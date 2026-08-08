# GEOMETRY.md — The Weaver's Cottage

## Scene

- **name:** The Weaver's Cottage
- **place_path:** places/driftmoor/weavers_cottage
- **z_level:** 16.25
- **width:** 19.5
- **height:** 16.25
- **origin:** 451.5, 447, 0

Notes: Stone-and-thatch cottage. Origin at southwest corner.
Main room with a large loom dominating the space. Baskets of
yarn and dyed thread. Small living area in the back.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 9.5  | 0  |
| main_loom       | 9.5  | 6.5  |
| yarn_baskets    | 3.121  | 13.671  |
| dye_pots        | 16.664 | 2.569  |
| living_nook     | 9.5  | 13  |
| finished_cloth  | 15.819 | 12.81  |
| living_door     | 9.5  | 9.5  |

---

## Zones

| name | render_z | auto_wall | vertices |
|------------|----------|---------|-------------------------------|
| LIVING | 6.5 |  | (0,9.5) (19.5,9.5) (19.5,16) (0,16) |
| WORKSHOP | 3.25 |  | (0,0) (19.5,0) (19.5,9.5) (0,9.5) |
| EXTERIOR | 0.0 |  | (-4.5,-4.5) (24,-4.5) (24,21) (-4.5,21) |
---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,14.5) (19.5,14.5) (19.5,16) (0,16)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 9.5 | 0 | places/driftmoor |
