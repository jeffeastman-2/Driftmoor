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
| front_door      | 19.5  | 0.0  |
| main_loom       | 19.5  | 13.0  |
| yarn_baskets    | 6.5  | 9.75  |
| dye_pots        | 32.5 | 9.75  |
| living_nook     | 19.5  | 26.0  |
| finished_cloth  | 32.5 | 22.75  |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| LIVING     | 6.5        | (0.0,19.5) (39.0,19.5) (39.0,32.5) (0.0,32.5)   |
| WORKSHOP   | 3.25        | (0.0,0.0) (39.0,0.0) (39.0,19.5) (0.0,19.5)     |
| EXTERIOR   | 0.0        | (-9.75,-9.75) (48.75,-9.75) (48.75,42.25) (-9.75,42.25) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0.0,29.25) (39.0,29.25) (39.0,32.5) (0.0,32.5)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 19.5 | 0.0 | places/driftmoor |
