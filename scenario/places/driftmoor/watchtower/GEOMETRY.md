# GEOMETRY.md — The Watchtower

## Scene

- **name:** The Watchtower
- **place_path:** places/driftmoor/watchtower
- **z_level:** 5.0
- **width:** 10.0
- **height:** 10.0
- **origin:** 2790.0, 2609.0, 5.0

Notes: Squat stone tower. Origin at southwest corner. Ground floor
is a single room with weapon rack and cot. Ladder leads to the roof
platform with views over the town and harbor. Oil lamps at top.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 5.0 | 0.0 |
| weapon_rack     | 2.0 | 7.0 |
| cot             | 8.0 | 7.0 |
| ladder          | 5.0 | 9.0 |
| center          | 5.0 | 5.0 |

---

## Zones

| name            | render_z | vertices                    |
|-----------------|----------|-----------------------------|
| ROOF_PLATFORM   | 2        | (1,1) (9,1) (9,9) (1,9)     |
| GROUND_FLOOR    | 1        | (0,0) (10,0) (10,10) (0,10)  |
| EXTERIOR        | 0        | (-3,-3) (13,-3) (13,13) (-3,13) |

---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Tower walls | (0,0) (10,0) (10,10) (0,10) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 5.0 | 0.0 | places/driftmoor |
