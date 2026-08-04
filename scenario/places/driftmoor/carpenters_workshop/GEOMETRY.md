# GEOMETRY.md — Carpenter's Workshop

## Scene

- **name:** Carpenter's Workshop
- **place_path:** places/driftmoor/carpenters_workshop
- **z_level:** 16.25
- **width:** 26
- **height:** 19.5
- **origin:** 279.5, 443, 0

Notes: Timber-framed with an open front facing south. Origin at
southwest corner. Workshop area with workbenches and lumber storage.
Open front allows view from the street. Finished furniture displayed
near the entrance.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| open_front      | 13  | 0  |
| main_workbench  | 10.903  | 10.443  |
| lumber_pile     | 20.927 | 14.5  |
| tool_wall       | 1.919  | 14.217  |
| display_area    | 2.83  | 4.467  |
| sawdust_pile    | 10.904 | 17.821  |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| STORAGE    | 6.5        | (16,9.5) (26,9.5) (26,19.5) (16,19.5)  |
| WORKSHOP   | 3.25        | (0,0) (26,0) (26,19.5) (0,19.5)    |
| EXTERIOR   | 0.0        | (-4.5,-4.5) (30.5,-4.5) (30.5,24) (-4.5,24) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,17.5) (26,17.5) (26,19.5) (0,19.5) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| open_front | 13 | 0 | places/driftmoor |
