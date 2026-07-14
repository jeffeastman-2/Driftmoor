# GEOMETRY.md — Salt & Iron Mercantile

## Scene

- **name:** Salt & Iron Mercantile
- **place_path:** places/driftmoor/salt_and_iron
- **z_level:** 16.25
- **width:** 71.5
- **height:** 65.0
- **origin:** 9418.5, 8021.0, 16.25

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
| front_doors     | 35 | 0  |
| shelves_west    | 6  | 15 |
| shelves_east    | 65 | 15 |
| barrel_corner_w | 9  | 55 |
| barrel_corner_e | 61 | 55 |
| staircase       | 58 | 52 |
| clock           | 35 | 61 |
| cudgel_under_counter | 42 | 32 |
| ledger          | 32 | 32 |

---

## Zones

| name       | render_z | vertices                              |
|------------|----------|---------------------------------------|
| BACK_STORE | 6.5        | (0,45) (71,45) (71,65) (0,65)         |
| COUNTER    | 6.5        | (19,25) (58,25) (58,35) (19,35)         |
| SHOP_FLOOR | 3.25        | (0,0) (71,0) (71,45) (0,45)           |
| EXTERIOR   | 0.0        | (-16,-16) (87,-16) (87,81) (-16,81)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| COUNTER    |  (19,25) (58,25) (58,35) (19,35)         |

---

## Connections

| name             | x    | y    | destination                          |
|------------------|------|------|--------------------------------------|
| front_doors      | 35 | 0  | places/driftmoor                     |
| to_upper_floor   | 58 | 52 | places/driftmoor/salt_and_iron/upper_floor |

---

## Boundaries

---
