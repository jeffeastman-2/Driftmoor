# GEOMETRY.md — Driftmoor Graveyard

## Scene

- **name:** Driftmoor Graveyard
- **place_path:** places/driftmoor/graveyard
- **z_level:** 16.25
- **width:** 51
- **height:** 29
- **origin:** 348, 630, 0

---

## Landmarks

| name              | x  | y  |
|-------------------|----|----|
| iron_gate         | 25.5 | 0  |
| central_path      | 25.5 | 14.5 |
| old_gravestones   | 10.364 | 15.67 |
| newer_graves      | 42.873 | 18.314 |
| old_gravestones_n | 17.5 | 23 |
| newer_graves_s    | 43.856 | 10 |
| old_gravestones_s | 10 | 8 |
| newer_graves_n    | 33.051 | 23.508 |
| offering_shelf    | 30.068 | 4.17 |
| church_wall_path  | 51 | 14.5 |

---

## Zones

| name      | render_z | vertices                          |
|-----------|----------|-----------------------------------|
| GRAVEYARD | 5.0      | (0,0) (51,0) (51,29) (0,29)   |
| EXTERIOR  | 0.0      | (-4,-4) (55,-4) (55,33) (-4,33) |

---

## Impassable

| description | vertices                         |
|-------------|----------------------------------|
| North wall  | (0,27) (51,27) (51,29) (0,29) |
| West wall   | (0,0) (2,0) (2,29) (0,29)       |
| East wall   | (49,0) (51,0) (51,29) (49,29) |
| South wall west | (0,0) (23.5,0) (23.5,2) (0,2) |
| South wall east | (27.5,0) (51,0) (51,2) (27.5,2) |

---

## Connections

| name                | x  | y | destination      |
|---------------------|----|---|------------------|
| graveyard_to_street | 25.5 | 0 | places/driftmoor |
| church_wall_path    | 51 | 14.5 | places/driftmoor/beacon_church |
