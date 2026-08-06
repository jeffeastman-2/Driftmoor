# GEOMETRY.md — Salt & Iron Mercantile

## Scene

- **name:** Salt & Iron Mercantile
- **place_path:** places/driftmoor/salt_and_iron
- **z_level:** 16.25
- **width:** 35.75
- **height:** 32.5
- **origin:** 487, 252, 0

Notes: One of the largest buildings in town — timber reinforced with
iron bands, both functional and defensible. The ground floor is the
shop: long central counter, shelves along all walls, barrels stacked
in corners. A small upstairs is Jorgen's private living quarters,
accessed by an interior staircase behind the counter — off limits to
customers. The double doors open onto the street to the south.
The shop is well-lit during trading hours; a clock ticks on the wall.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_doors     | 17.5 | 0  |
| shelves_west    | 3  | 7.5 |
| shelves_east    | 32.5 | 7.5 |
| barrel_corner_w | 4.5  | 27.5 |
| barrel_corner_e | 30.5 | 27.5 |
| staircase       | 29 | 26 |
| clock           | 17.5 | 30.5 |
| cudgel_under_counter | 21 | 16 |
| ledger          | 16 | 16 |
| counter_center  | 19.25 | 15 |
| central_display_w | 8 | 8 |
| central_display_e | 25 | 8 |
| rope_coils      | 6 | 19 |
| salt_sacks      | 32 | 19 |

---

## Zones

| name | render_z | auto_wall | vertices |
|------------|----------|---------|---------------------------------------|
| BACK_STORE | 6.5 |  | (0,22.5) (35.5,22.5) (35.5,32.5) (0,32.5) |
| SHOP_FLOOR | 3.25 |  | (0,0) (35.5,0) (35.5,22.5) (0,22.5) |
| EXTERIOR | 0.0 |  | (-8,-8) (43.5,-8) (43.5,40.5) (-8,40.5) |
---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| COUNTER    |  (9.5,12.5) (29,12.5) (29,17.5) (9.5,17.5)         |

---

## Connections

| name             | x    | y    | destination                          |
|------------------|------|------|--------------------------------------|
| front_doors      | 17.5 | 0  | places/driftmoor                     |
| to_upper_floor   | 29 | 26 | places/driftmoor/salt_and_iron/upper_floor |

---

## Boundaries

---
