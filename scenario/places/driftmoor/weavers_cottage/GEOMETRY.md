# GEOMETRY.md — The Weaver's Cottage

## Scene

- **name:** The Weaver's Cottage
- **place_path:** places/driftmoor/weavers_cottage
- **z_level:** 16.25
- **width:** 39.0
- **height:** 32.5
- **origin:** 9389.25, 8723.0, 16.25

Notes: Stone-and-thatch cottage. Origin at southwest corner.
Main room with a large loom dominating the space. Baskets of
yarn and dyed thread. Small living area in the back.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 19  | 0  |
| main_loom       | 19  | 13  |
| yarn_baskets    | 6  | 9  |
| dye_pots        | 32 | 9  |
| living_nook     | 19  | 26  |
| finished_cloth  | 32 | 22  |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| LIVING     | 6.5        | (0,19) (39,19) (39,32) (0,32)   |
| WORKSHOP   | 3.25        | (0,0) (39,0) (39,19) (0,19)     |
| EXTERIOR   | 0.0        | (-9,-9) (48,-9) (48,42) (-9,42) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,29) (39,29) (39,32) (0,32)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 19 | 0 | places/driftmoor |
