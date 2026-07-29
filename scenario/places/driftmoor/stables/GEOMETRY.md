# GEOMETRY.md — The Stables

## Scene

- **name:** The Stables
- **place_path:** places/driftmoor/stables
- **z_level:** 16.25
- **width:** 44
- **height:** 56.5
- **origin:** 602.5, 75.5, 0

---

## Landmarks

| name             | x  | y  |
|------------------|----|----|
| stable_entrance  | 3.5  | 0  |
| saddle_racks     | 6.5 | 13 |
| stall_row_center | 23 | 27.5 |
| feed_bins        | 32.5 | 13 |
| forge_door       | 0  | 32.5 |

---

## Zones

| name     | render_z | vertices                         |
|----------|----------|----------------------------------|
| STABLES  | 5.0      | (0,0) (44,0) (44,56.5) (0,56.5)  |
| EXTERIOR | 0.0      | (-4,-4) (48,-4) (48,60.5) (-4,60.5) |

---

## Impassable

| description      | vertices                         |
|------------------|----------------------------------|
| West stall wall  | (0,53.5) (19,53.5) (19,56.5) (0,56.5) |
| East stall wall  | (25,53.5) (44,53.5) (44,56.5) (25,56.5) |

---

## Connections

| name             | x | y | destination      |
|------------------|---|---|------------------|
| stable_to_street | 3.5 | 0 | places/driftmoor |
| stable_to_forge  | 0 | 32.5 | places/driftmoor/forge |
