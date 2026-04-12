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
| front_door      | 16.25 | 0.0 |
| fish_crates     | 9.75 | 16.25 |
| salt_barrels    | 26.0 | 19.5 |
| hanging_nets    | 16.25 | 22.75 |
| counter         | 16.25 | 9.75 |
| fish_sign       | 16.25 | -3.25|

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHACK      | 3.25        | (0.0,0.0) (32.5,0.0) (32.5,26.0) (0.0,26.0)   |
| EXTERIOR   | 0.0        | (-9.75,-9.75) (42.25,-9.75) (42.25,35.75) (-9.75,35.75) |

---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Back wall   | (0.0,22.75) (32.5,22.75) (32.5,26.0) (0.0,26.0)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 16.25 | 0.0 | places/driftmoor |
