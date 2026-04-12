# GEOMETRY.md — The Plains of Stonehearth

## Scene

- **name:** The Plains of Stonehearth
- **place_path:** places/plains_of_stonehearth
- **z_level:** 16.25
- **width:** 54600.0
- **height:** 22750.0
- **origin:** 10400.0, 0.0, 16.25

Notes: Windswept grasslands southeast of Driftmoor. Origin at
southwest corner. Vast and mostly flat with rocky outcroppings
and small caves scattered throughout. Used for grazing sheep and
goats. Sparsely populated with a few farmsteads. Shadowbeasts
have been preying on livestock, especially at night.

---

## Landmarks

| name               | x       | y      |
|--------------------|---------|--------|
| plains_center      | 22100.0  | 6500.0 |
| northern_farmstead | 6500.0  | 17875.0 |
| southern_farmstead | 16250.0  | 3250.0 |
| rocky_outcrop_west | 9750.0  | 9750.0 |
| rocky_outcrop_east | 29250.0  | 8125.0 |
| sheep_pasture      | 13000.0  | 13000.0 |
| shadowbeast_den    | 26000.0  | 11375.0 |
| coastal_path_west  | 1625.0   | 9750.0 |
| road_to_driftmoor  | 3250.0  | 17875.0 |

---

## Zones

| name              | render_z | vertices                                                    |
|-------------------|----------|-------------------------------------------------------------|
| ROCKY_OUTCROP_W   | 6.5        | (8125.0,8125.0) (11375.0,8125.0) (11375.0,11375.0) (8125.0,11375.0)              |
| ROCKY_OUTCROP_E   | 6.5        | (27625.0,6500.0) (30875.0,6500.0) (30875.0,9750.0) (27625.0,9750.0)              |
| FARMLANDS         | 3.25        | (4875.0,14625.0) (16250.0,14625.0) (16250.0,21125.0) (4875.0,21125.0)              |
| PASTURES          | 3.25        | (9750.0,9750.0) (19500.0,9750.0) (19500.0,16250.0) (9750.0,16250.0)              |
| OPEN_GRASSLAND    | 0.0        | (0.0,0.0) (54600.0,0.0) (54600.0,22750.0) (0.0,22750.0)                        |

---

## Impassable

| description           | vertices                                                    |
|-----------------------|-------------------------------------------------------------|
| Rocky outcrop W cliffs | (9100.0,8775.0) (10400.0,8775.0) (10400.0,10725.0) (9100.0,10725.0)             |
| Rocky outcrop E cliffs | (28275.0,7150.0) (30225.0,7150.0) (30225.0,9100.0) (28275.0,9100.0)             |

---

## Connections

| name               | x       | y      | destination                    |
|--------------------|---------|--------|--------------------------------|
| road_to_driftmoor  | 3250.0  | 17875.0 | places/driftmoor               |
| coastal_path_west  | 0.0     | 9750.0 | places/azure_sea               |
| plains_east        | 53625.0 | 11375.0 | places/plains_of_stonehearth   |
