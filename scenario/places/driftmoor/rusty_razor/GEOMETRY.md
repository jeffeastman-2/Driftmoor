# GEOMETRY.md — The Rusty Razor (Barbershop)

## Scene

- **name:** The Rusty Razor
- **place_path:** places/driftmoor/rusty_razor
- **z_level:** 5.0
- **width:** 8.0
- **height:** 8.0
- **origin:** 2851.0, 2636.0, 5.0

Notes: Small wooden-fronted barbershop. Origin at southwest corner.
Single room with two chairs, mirror, and a shelf of tonics.
Striped pole outside the door.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 4.0 | 0.0 |
| barber_chair_1  | 3.0 | 4.0 |
| barber_chair_2  | 6.0 | 4.0 |
| mirror          | 4.0 | 7.0 |
| tonic_shelf     | 1.0 | 6.0 |
| striped_pole    | 5.0 | -1.0|

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| SHOP       | 1        | (0,0) (8,0) (8,8) (0,8)     |
| EXTERIOR   | 0        | (-3,-3) (11,-3) (11,11) (-3,11) |

---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Back wall   | (0,7) (8,7) (8,8) (0,8)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 4.0 | 0.0 | places/driftmoor |
