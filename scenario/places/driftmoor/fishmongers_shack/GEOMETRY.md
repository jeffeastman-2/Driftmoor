# GEOMETRY.md — The Fishmonger's Shack

## Scene

- **name:** The Fishmonger's Shack
- **place_path:** places/driftmoor/fishmongers_shack
- **z_level:** 5.0
- **width:** 10.0
- **height:** 8.0
- **origin:** 2733.0, 2604.0, 5.0

Notes: Small weathered shack near the harbor. Origin at southwest
corner. Single room with crates of fish, hanging nets, and hooks.
Slanted roof. Fish-shaped sign outside.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 5.0 | 0.0 |
| fish_crates     | 3.0 | 5.0 |
| salt_barrels    | 8.0 | 6.0 |
| hanging_nets    | 5.0 | 7.0 |
| counter         | 5.0 | 3.0 |
| fish_sign       | 5.0 | -1.0|

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHACK      | 1        | (0,0) (10,0) (10,8) (0,8)   |
| EXTERIOR   | 0        | (-3,-3) (13,-3) (13,11) (-3,11) |

---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Back wall   | (0,7) (10,7) (10,8) (0,8)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 5.0 | 0.0 | places/driftmoor |
