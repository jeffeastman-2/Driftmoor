# GEOMETRY.md — The Cobbler's Shop

## Scene

- **name:** The Cobbler's Shop
- **place_path:** places/driftmoor/cobblers_shop
- **z_level:** 5.0
- **width:** 10.0
- **height:** 8.0
- **origin:** 2825.0, 2636.0, 5.0

Notes: A snug brick-walled single-room shop. Origin at southwest
corner. Front window displays shoes. Workbench and tools in the back.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 5.0 | 0.0 |
| display_window  | 2.0 | 0.0 |
| workbench       | 5.0 | 6.0 |
| shoe_racks      | 9.0 | 4.0 |
| stool           | 3.0 | 5.0 |

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHOP       | 1        | (0,0) (10,0) (10,8) (0,8)   |
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
