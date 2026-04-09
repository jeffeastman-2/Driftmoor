# GEOMETRY.md — The Weaver's Cottage

## Scene

- **name:** The Weaver's Cottage
- **place_path:** places/driftmoor/weavers_cottage
- **z_level:** 5.0
- **width:** 12.0
- **height:** 10.0
- **origin:** 2889.0, 2684.0, 5.0

Notes: Stone-and-thatch cottage. Origin at southwest corner.
Main room with a large loom dominating the space. Baskets of
yarn and dyed thread. Small living area in the back.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 6.0  | 0.0  |
| main_loom       | 6.0  | 4.0  |
| yarn_baskets    | 2.0  | 3.0  |
| dye_pots        | 10.0 | 3.0  |
| living_nook     | 6.0  | 8.0  |
| finished_cloth  | 10.0 | 7.0  |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| LIVING     | 2        | (0,6) (12,6) (12,10) (0,10)   |
| WORKSHOP   | 1        | (0,0) (12,0) (12,6) (0,6)     |
| EXTERIOR   | 0        | (-3,-3) (15,-3) (15,13) (-3,13) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,9) (12,9) (12,10) (0,10)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 6.0 | 0.0 | places/driftmoor |
