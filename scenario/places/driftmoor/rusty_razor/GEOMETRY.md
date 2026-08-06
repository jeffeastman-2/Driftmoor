# GEOMETRY.md — The Rusty Razor (Barbershop)

## Scene

- **name:** The Rusty Razor
- **place_path:** places/driftmoor/rusty_razor
- **z_level:** 16.25
- **width:** 13
- **height:** 13
- **origin:** 397.5, 364, 0

Notes: Small wooden-fronted barbershop. Origin at southwest corner.
Single room with two chairs, mirror, and a shelf of tonics.
Striped pole outside the door.

---

## Landmarks

| name            | x   | y   |
|-----------------|-----|-----|
| front_door      | 6.5 | 0 |
| central_rug | 6.536 | 5.611 |
| barber_chair_3.25 | 4.82 | 5.588 |
| barber_chair_6.5 | 8.34 | 5.574 |
| mirror | 6.5 | 11 |
| tonic_shelf | 1.678 | 9.962 |
| potbelly_stove | 10.826 | 10.293 |
| washstand | 6.615 | 9.75 |
| striped_pole | 8 | -1.5 |
---

## Zones

| name | render_z | auto_wall | vertices |
|------------|----------|---------|-----------------------------|
| SHOP | 3.25 |  | (0,0) (13,0) (13,13) (0,13) |
| EXTERIOR | 0.0 |  | (-4.5,-4.5) (17.5,-4.5) (17.5,17.5) (-4.5,17.5) |
---

## Impassable

| description | vertices                    |
|-------------|-----------------------------|
| Back wall   | (0,11) (13,11) (13,13) (0,13)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 6.5 | 0 | places/driftmoor |
