# GEOMETRY.md — The Watchtower

## Scene

- **name:** The Watchtower
- **place_path:** places/driftmoor/watchtower
- **z_level:** 16.25
- **width:** 32.5
- **height:** 32.5
- **origin:** 9067.5, 8479.25, 16.25

Notes: Squat stone tower. Origin at southwest corner. Ground floor
is a single room with weapon rack and cot. Ladder leads to the roof
platform with views over the town and harbor. Oil lamps at top.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 16 | 0 |
| weapon_rack     | 6 | 22 |
| cot             | 26 | 22 |
| ladder          | 16 | 29 |
| center          | 16 | 16 |

---

## Zones

| name            | render_z | vertices                    |
|-----------------|----------|-----------------------------|
| ROOF_PLATFORM   | 6.5        | (3,3) (29,3) (29,29) (3,29)     |
| GROUND_FLOOR    | 3.25        | (0,0) (32,0) (32,32) (0,32)  |
| EXTERIOR        | 0.0        | (-9,-9) (42,-9) (42,42) (-9,42) |

---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Tower walls | (0,0) (32,0) (32,32) (0,32) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 16 | 0 | places/driftmoor |
