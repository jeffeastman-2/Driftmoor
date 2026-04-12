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
| front_door      | 13.0 | 0.0 |
| barber_chair_3.25  | 9.75 | 13.0 |
| barber_chair_6.5  | 19.5 | 13.0 |
| mirror          | 13.0 | 22.75 |
| tonic_shelf     | 3.25 | 19.5 |
| striped_pole    | 16.25 | -3.25|

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHOP       | 3.25        | (0.0,0.0) (26.0,0.0) (26.0,26.0) (0.0,26.0)     |
| EXTERIOR   | 0.0        | (-9.75,-9.75) (35.75,-9.75) (35.75,35.75) (-9.75,35.75) |

---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Back wall   | (0.0,22.75) (26.0,22.75) (26.0,26.0) (0.0,26.0)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 13.0 | 0.0 | places/driftmoor |
