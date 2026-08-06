# GEOMETRY.md — Salt & Iron Upper Floor

## Scene

- **name:** Salt & Iron Upper Floor
- **place_path:** places/driftmoor/salt_and_iron/upper_floor
- **z_level:** 25.25
- **width:** 35.5
- **height:** 32.5
- **origin:** 0, 0, 9

Notes: Private living quarters above the mercantile. The staircase arrives
near the northeast corner.

---

## Landmarks

| name | x | y | z |
|---|---|---|---|
| stair_landing | 29 | 26 | 0 |
| bed | 8.931 | 25.726 | 4 |
| writing_table | 17.517 | 28.933 | 4 |
| iron_chest | 3.93 | 3.551 | 4 |
| small_stove | 18.928 | 3.619 | 4 |
| account_shelves | 2.276 | 13.378 | 4 |

---

## Zones

| name | floor_z | ceiling_z | render_z | auto_wall | vertices |
|---|---|---|---|---------|---|
| LIVING_QUARTERS | 0 | 8 | 3.25 |  | (0,0) (35.5,0) (35.5,32.5) (0,32.5) |
| STAIR_LANDING | 0 | 8 | 7.0 |  | (26,22) (32,22) (32,32.5) (26,32.5) |
---

## Connections

| name | x | y | destination |
|---|---|---|---|
| to_shop | 29 | 26 | places/driftmoor/salt_and_iron |
