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
| front_doors     | 35.75 | 0.0  |
| main_counter    | 35.75 | 39.0 |
| shelves_west    | 6.5  | 32.5 |
| shelves_east    | 65.0 | 32.5 |
| barrel_corner_w | 9.75  | 55.25 |
| barrel_corner_e | 61.75 | 55.25 |
| staircase       | 58.5 | 52.0 |
| clock           | 35.75 | 61.75 |
| cudgel_under_counter | 42.25 | 42.25 |
| ledger          | 32.5 | 42.25 |

---

## Zones

| name       | render_z | vertices                              |
|------------|----------|---------------------------------------|
| BACK_STORE | 6.5        | (0.0,45.5) (71.5,45.5) (71.5,65.0) (0.0,65.0)         |
| COUNTER    | 6.5        | (19.5,35.75) (58.5,35.75) (58.5,45.5) (19.5,45.5)         |
| SHOP_FLOOR | 3.25        | (0.0,0.0) (71.5,0.0) (71.5,45.5) (0.0,45.5)           |
| EXTERIOR   | 0.0        | (-16.25,-16.25) (87.75,-16.25) (87.75,81.25) (-16.25,81.25)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| Main counter     | (19.5,35.75) (58.5,35.75) (58.5,42.25) (19.5,42.25)         |
| Back store wall  | (0.0,45.5) (71.5,45.5) (71.5,48.75) (0.0,48.75)         |

---

## Connections

| name             | x    | y    | destination                          |
|------------------|------|------|--------------------------------------|
| front_doors      | 35.75 | 0.0  | places/driftmoor                     |
| to_upper_floor   | 58.5 | 52.0 | places/driftmoor/salt_and_iron/upper_floor |

---

## Boundaries

### Counter Line — Jorgen's Domain

- **type:** conditional
- **blocks:** all
- **effect:** crossing behind the counter without permission is trespassing; Jorgen keeps a cudgel beneath the counter and will use it
- **vertices:** (0.0,35.75) (71.5,35.75) (71.5,65.0) (0.0,65.0)

### Back Store — Private

- **type:** physical
- **blocks:** all
- **effect:** locked door; Jorgen's private stock and staircase to quarters; DC 48.75 Thieves' Tools to pick
- **vertices:** (0.0,45.5) (71.5,45.5) (71.5,65.0) (0.0,65.0)

---

## Starting Positions

| character | x    | y    | zone       |
|-----------|------|------|------------|
| varrak    | 32.5 | 26.0  | SHOP_FLOOR |
| jorgen    | 35.75 | 42.25 | COUNTER    |