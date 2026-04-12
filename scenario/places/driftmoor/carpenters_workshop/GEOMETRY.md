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
| open_front      | 26.0  | 0.0  |
| main_workbench  | 26.0  | 19.5  |
| lumber_pile     | 45.5 | 29.25  |
| tool_wall       | 0.0  | 19.5  |
| display_area    | 13.0  | 6.5  |
| sawdust_pile    | 39.0 | 13.0  |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| STORAGE    | 6.5        | (32.5,19.5) (52.0,19.5) (52.0,39.0) (32.5,39.0)  |
| WORKSHOP   | 3.25        | (0.0,0.0) (52.0,0.0) (52.0,39.0) (0.0,39.0)    |
| EXTERIOR   | 0.0        | (-9.75,-9.75) (61.75,-9.75) (61.75,48.75) (-9.75,48.75) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0.0,35.75) (52.0,35.75) (52.0,39.0) (0.0,39.0) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| open_front | 26.0 | 0.0 | places/driftmoor |
