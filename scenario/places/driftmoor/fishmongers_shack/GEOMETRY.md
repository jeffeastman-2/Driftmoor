# GEOMETRY.md — The Fishmonger's Shack

## Scene

- **name:** The Fishmonger's Shack
- **place_path:** places/driftmoor/fishmongers_shack
- **z_level:** 16.25
- **width:** 32.5
- **height:** 26.0
- **origin:** 8882.25, 8463.0, 16.25

Notes: Small weathered shack near the harbor. Origin at southwest
corner. Single room with crates of fish, hanging nets, and hooks.
Slanted roof. Fish-shaped sign outside.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 16 | 0 |
| fish_crates     | 9 | 16 |
| salt_barrels    | 26 | 19 |
| hanging_nets    | 16 | 22 |
| counter         | 16 | 9 |
| fish_sign       | 16 | -3|

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHACK      | 3.25        | (0,0) (32,0) (32,26) (0,26)   |
| EXTERIOR   | 0.0        | (-9,-9) (42,-9) (42,35) (-9,35) |

---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Back wall   | (0,22) (32,22) (32,26) (0,26)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 16 | 0 | places/driftmoor |
