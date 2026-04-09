# GEOMETRY.md — Salt & Iron Mercantile

## Scene

- **name:** Salt & Iron Mercantile
- **place_path:** places/driftmoor/salt_and_iron
- **z_level:** 5.0
- **width:** 22.0
- **height:** 20.0
- **origin:** 2898.0, 2468.0, 5.0

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
| front_doors     | 11.0 | 0.0  |
| main_counter    | 11.0 | 12.0 |
| shelves_west    | 2.0  | 10.0 |
| shelves_east    | 20.0 | 10.0 |
| barrel_corner_w | 3.0  | 17.0 |
| barrel_corner_e | 19.0 | 17.0 |
| staircase       | 18.0 | 16.0 |
| clock           | 11.0 | 19.0 |
| cudgel_under_counter | 13.0 | 13.0 |
| ledger          | 10.0 | 13.0 |

---

## Zones

| name       | render_z | vertices                              |
|------------|----------|---------------------------------------|
| BACK_STORE | 2        | (0,14) (22,14) (22,20) (0,20)         |
| COUNTER    | 2        | (6,11) (18,11) (18,14) (6,14)         |
| SHOP_FLOOR | 1        | (0,0) (22,0) (22,14) (0,14)           |
| EXTERIOR   | 0        | (-5,-5) (27,-5) (27,25) (-5,25)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| Main counter     | (6,11) (18,11) (18,13) (6,13)         |
| Back store wall  | (0,14) (22,14) (22,15) (0,15)         |

---

## Connections

| name             | x    | y    | destination                          |
|------------------|------|------|--------------------------------------|
| front_doors      | 11.0 | 0.0  | places/driftmoor                     |
| to_upper_floor   | 18.0 | 16.0 | places/driftmoor/salt_and_iron/upper_floor |

---

## Boundaries

### Counter Line — Jorgen's Domain

- **type:** conditional
- **blocks:** all
- **effect:** crossing behind the counter without permission is trespassing; Jorgen keeps a cudgel beneath the counter and will use it
- **vertices:** (0,11) (22,11) (22,20) (0,20)

### Back Store — Private

- **type:** physical
- **blocks:** all
- **effect:** locked door; Jorgen's private stock and staircase to quarters; DC 15 Thieves' Tools to pick
- **vertices:** (0,14) (22,14) (22,20) (0,20)

---

## Starting Positions

| character | x    | y    | zone       |
|-----------|------|------|------------|
| varrak    | 10.0 | 8.0  | SHOP_FLOOR |
| jorgen    | 11.0 | 13.0 | COUNTER    |