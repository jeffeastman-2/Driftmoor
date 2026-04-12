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
| front_door      | 16.25 | 0.0 |
| weapon_rack     | 6.5 | 22.75 |
| cot             | 26.0 | 22.75 |
| ladder          | 16.25 | 29.25 |
| center          | 16.25 | 16.25 |

---

## Zones

| name            | render_z | vertices                    |
|-----------------|----------|-----------------------------|
| ROOF_PLATFORM   | 6.5        | (3.25,3.25) (29.25,3.25) (29.25,29.25) (3.25,29.25)     |
| GROUND_FLOOR    | 3.25        | (0.0,0.0) (32.5,0.0) (32.5,32.5) (0.0,32.5)  |
| EXTERIOR        | 0.0        | (-9.75,-9.75) (42.25,-9.75) (42.25,42.25) (-9.75,42.25) |

---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Tower walls | (0.0,0.0) (32.5,0.0) (32.5,32.5) (0.0,32.5) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 16.25 | 0.0 | places/driftmoor |
