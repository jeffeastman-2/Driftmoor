# GEOMETRY.md — The Rusty Razor (Barbershop)

## Scene

- **name:** The Rusty Razor
- **place_path:** places/driftmoor/rusty_razor
- **z_level:** 16.25
- **width:** 26.0
- **height:** 26.0
- **origin:** 9265.75, 8567.0, 16.25

Notes: Small wooden-fronted barbershop. Origin at southwest corner.
Single room with two chairs, mirror, and a shelf of tonics.
Striped pole outside the door.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 13 | 0 |
| barber_chair_3.25  | 9 | 13 |
| barber_chair_6.5  | 19 | 13 |
| mirror          | 13 | 22 |
| tonic_shelf     | 3 | 19 |
| striped_pole    | 16 | -3|

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHOP       | 3.25        | (0,0) (26,0) (26,26) (0,26)     |
| EXTERIOR   | 0.0        | (-9,-9) (35,-9) (35,35) (-9,35) |

---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Back wall   | (0,22) (26,22) (26,26) (0,26)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 13 | 0 | places/driftmoor |
