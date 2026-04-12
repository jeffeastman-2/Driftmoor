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
| front_door      | 16.25 | 0.0 |
| display_window  | 6.5 | 0.0 |
| workbench       | 16.25 | 19.5 |
| shoe_racks      | 29.25 | 13.0 |
| stool           | 9.75 | 16.25 |

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHOP       | 3.25        | (0.0,0.0) (32.5,0.0) (32.5,26.0) (0.0,26.0)   |
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
