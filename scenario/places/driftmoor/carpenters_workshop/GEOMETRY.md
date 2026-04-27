# GEOMETRY.md — Carpenter's Workshop

## Scene

- **name:** Carpenter's Workshop
- **place_path:** places/driftmoor/carpenters_workshop
- **z_level:** 16.25
- **width:** 52.0
- **height:** 39.0
- **origin:** 9028.5, 8723.0, 16.25

Notes: Timber-framed with an open front facing south. Origin at
southwest corner. Workshop area with workbenches and lumber storage.
Open front allows view from the street. Finished furniture displayed
near the entrance.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| open_front      | 26  | 0  |
| main_workbench  | 26  | 19  |
| lumber_pile     | 45 | 29  |
| tool_wall       | 0  | 19  |
| display_area    | 13  | 6  |
| sawdust_pile    | 39 | 13  |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| STORAGE    | 6.5        | (32,19) (52,19) (52,39) (32,39)  |
| WORKSHOP   | 3.25        | (0,0) (52,0) (52,39) (0,39)    |
| EXTERIOR   | 0.0        | (-9,-9) (61,-9) (61,48) (-9,48) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,35) (52,35) (52,39) (0,39) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| open_front | 26 | 0 | places/driftmoor |
