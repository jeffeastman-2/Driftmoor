# GEOMETRY.md — The Watchtower

## Scene

- **name:** The Watchtower
- **place_path:** places/driftmoor/watchtower
- **z_level:** 16.25
- **width:** 16.25
- **height:** 16.25
- **origin:** 300, 332.5, 0

Notes: Squat stone tower. Origin at southwest corner. Ground floor
is a single room with weapon rack and cot. Ladder leads to the roof
platform with views over the town and harbor. Oil lamps at top.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 8 | 0 |
| weapon_rack     | 1.944 | 9.218 |
| cot             | 13.264 | 12.386 |
| ladder          | 7.868 | 13.792 |
| center          | 8.198 | 6.68 |

---

## Zones

| name            | render_z | vertices                    |
|-----------------|----------|-----------------------------|
| ROOF_PLATFORM   | 32.5       | (1.5,1.5) (14.5,1.5) (14.5,14.5) (1.5,14.5)     |
| GROUND_FLOOR    | 3.25        | (0,0) (16,0) (16,16) (0,16)  |
| EXTERIOR        | 0.0        | (-4.5,-4.5) (21,-4.5) (21,21) (-4.5,21) |

---

## Impassable

| description      | vertices                         |
|------------------|----------------------------------|
| North tower wall | (0,14.5) (16,14.5) (16,16) (0,16)  |
| West tower wall  | (0,0) (1.5,0) (1.5,16) (0,16)      |
| East tower wall  | (14.5,0) (16,0) (16,16) (14.5,16)  |
| South wall west  | (0,0) (6.5,0) (6.5,1.5) (0,1.5)      |
| South wall east  | (9.5,0) (16,0) (16,1.5) (9.5,1.5)    |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 8 | 0 | places/driftmoor |
