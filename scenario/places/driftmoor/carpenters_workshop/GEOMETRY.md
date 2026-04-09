# GEOMETRY.md — Carpenter's Workshop

## Scene

- **name:** Carpenter's Workshop
- **place_path:** places/driftmoor/carpenters_workshop
- **z_level:** 5.0
- **width:** 16.0
- **height:** 12.0
- **origin:** 2778.0, 2684.0, 5.0

Notes: Timber-framed with an open front facing south. Origin at
southwest corner. Workshop area with workbenches and lumber storage.
Open front allows view from the street. Finished furniture displayed
near the entrance.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| open_front      | 8.0  | 0.0  |
| main_workbench  | 8.0  | 6.0  |
| lumber_pile     | 14.0 | 9.0  |
| tool_wall       | 0.0  | 6.0  |
| display_area    | 4.0  | 2.0  |
| sawdust_pile    | 12.0 | 4.0  |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| STORAGE    | 2        | (10,6) (16,6) (16,12) (10,12)  |
| WORKSHOP   | 1        | (0,0) (16,0) (16,12) (0,12)    |
| EXTERIOR   | 0        | (-3,-3) (19,-3) (19,15) (-3,15) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,11) (16,11) (16,12) (0,12) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| open_front | 8.0 | 0.0 | places/driftmoor |
