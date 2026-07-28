# GEOMETRY.md — The Stables

## Scene

- **name:** The Stables
- **place_path:** places/driftmoor/stables
- **z_level:** 16.25
- **width:** 88
- **height:** 113
- **origin:** 1263, 151, 16.25

---

## Landmarks

| name             | x  | y  |
|------------------|----|----|
| stable_entrance  | 7  | 0  |
| saddle_racks     | 13 | 26 |
| stall_row_center | 46 | 55 |
| feed_bins        | 65 | 26 |
| forge_door       | 0  | 65 |

---

## Zones

| name     | render_z | vertices                         |
|----------|----------|----------------------------------|
| STABLES  | 5.0      | (0,0) (88,0) (88,113) (0,113)  |
| EXTERIOR | 0.0      | (-8,-8) (96,-8) (96,121) (-8,121) |

---

## Impassable

| description      | vertices                         |
|------------------|----------------------------------|
| West stall wall  | (0,107) (38,107) (38,113) (0,113) |
| East stall wall  | (50,107) (88,107) (88,113) (50,113) |

---

## Connections

| name             | x | y | destination      |
|------------------|---|---|------------------|
| stable_to_street | 7 | 0 | places/driftmoor |
| stable_to_forge  | 0 | 65 | places/driftmoor/forge |
