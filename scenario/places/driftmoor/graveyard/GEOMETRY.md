# GEOMETRY.md — Driftmoor Graveyard

## Scene

- **name:** Driftmoor Graveyard
- **place_path:** places/driftmoor/graveyard
- **z_level:** 16.25
- **width:** 102
- **height:** 58
- **origin:** 810, 1319, 16.25

---

## Landmarks

| name              | x  | y  |
|-------------------|----|----|
| iron_gate         | 51 | 0  |
| central_path      | 51 | 29 |
| old_gravestones   | 25 | 35 |
| newer_graves      | 77 | 35 |
| offering_shelf    | 88 | 12 |
| church_wall_path  | 102 | 29 |

---

## Zones

| name      | render_z | vertices                          |
|-----------|----------|-----------------------------------|
| GRAVEYARD | 5.0      | (0,0) (102,0) (102,58) (0,58)   |
| EXTERIOR  | 0.0      | (-8,-8) (110,-8) (110,66) (-8,66) |

---

## Impassable

| description | vertices                         |
|-------------|----------------------------------|
| North wall  | (0,54) (102,54) (102,58) (0,58) |
| West wall   | (0,0) (4,0) (4,58) (0,58)       |
| East wall   | (98,0) (102,0) (102,58) (98,58) |

---

## Connections

| name                | x  | y | destination      |
|---------------------|----|---|------------------|
| graveyard_to_street | 51 | 0 | places/driftmoor |
