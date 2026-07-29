# GEOMETRY.md — The Fishmonger's Shack

## Scene

- **name:** The Fishmonger's Shack
- **place_path:** places/driftmoor/fishmongers_shack
- **z_level:** 16.25
- **width:** 16.25
- **height:** 13
- **origin:** 198.5, 313.5, 0

Notes: Small weathered shack near the harbor. Origin at southwest
corner. Single room with crates of fish, hanging nets, and hooks.
Slanted roof. Fish-shaped sign outside.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 8 | 0 |
| fish_crates     | 4.5 | 8 |
| salt_barrels    | 13 | 9.5 |
| hanging_nets    | 8 | 11 |
| counter         | 8 | 4.5 |
| fish_sign       | 8 | -1.5|

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHACK      | 3.25        | (0,0) (16,0) (16,13) (0,13)   |
| EXTERIOR   | 0.0        | (-4.5,-4.5) (21,-4.5) (21,17.5) (-4.5,17.5) |

---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Back wall   | (0,11) (16,11) (16,13) (0,13)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 8 | 0 | places/driftmoor |
