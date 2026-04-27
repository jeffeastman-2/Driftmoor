# GEOMETRY.md — The Cobbler's Shop

## Scene

- **name:** The Cobbler's Shop
- **place_path:** places/driftmoor/cobblers_shop
- **z_level:** 16.25
- **width:** 32.5
- **height:** 26.0
- **origin:** 9181.25, 8567.0, 16.25

Notes: A snug brick-walled single-room shop. Origin at southwest
corner. Front window displays shoes. Workbench and tools in the back.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 16 | 0 |
| display_window  | 6 | 0 |
| workbench       | 16 | 19 |
| shoe_racks      | 29 | 13 |
| stool           | 9 | 16 |

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHOP       | 3.25        | (0,0) (32,0) (32,26) (0,26)   |
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
