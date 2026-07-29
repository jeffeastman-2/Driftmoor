# GEOMETRY.md — The Cobbler's Shop

## Scene

- **name:** The Cobbler's Shop
- **place_path:** places/driftmoor/cobblers_shop
- **z_level:** 16.25
- **width:** 16.25
- **height:** 13
- **origin:** 352, 364, 0

Notes: A snug brick-walled single-room shop. Origin at southwest
corner. Front window displays shoes. Workbench and tools in the back.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 8 | 0 |
| display_window  | 3 | 0 |
| workbench       | 8 | 9.5 |
| shoe_racks      | 14.5 | 6.5 |
| stool           | 4.5 | 8 |

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHOP       | 3.25        | (0,0) (16,0) (16,13) (0,13)   |
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
