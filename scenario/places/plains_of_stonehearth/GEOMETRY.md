# GEOMETRY.md — The Plains of Stonehearth

## Scene

- **name:** The Plains of Stonehearth
- **place_path:** places/plains_of_stonehearth
- **z_level:** 5.0
- **width:** 16800.0
- **height:** 7000.0
- **origin:** 3200.0, 0.0, 5.0

Notes: Windswept grasslands southeast of Driftmoor. Origin at
southwest corner. Vast and mostly flat with rocky outcroppings
and small caves scattered throughout. Used for grazing sheep and
goats. Sparsely populated with a few farmsteads. Shadowbeasts
have been preying on livestock, especially at night.

---

## Landmarks

| name               | x       | y      |
|--------------------|---------|--------|
| plains_center      | 6800.0  | 2000.0 |
| northern_farmstead | 2000.0  | 5500.0 |
| southern_farmstead | 5000.0  | 1000.0 |
| rocky_outcrop_west | 3000.0  | 3000.0 |
| rocky_outcrop_east | 9000.0  | 2500.0 |
| sheep_pasture      | 4000.0  | 4000.0 |
| shadowbeast_den    | 8000.0  | 3500.0 |
| coastal_path_west  | 500.0   | 3000.0 |
| road_to_driftmoor  | 1000.0  | 5500.0 |

---

## Zones

| name              | render_z | vertices                                                    |
|-------------------|----------|-------------------------------------------------------------|
| ROCKY_OUTCROP_W   | 2        | (2500,2500) (3500,2500) (3500,3500) (2500,3500)              |
| ROCKY_OUTCROP_E   | 2        | (8500,2000) (9500,2000) (9500,3000) (8500,3000)              |
| FARMLANDS         | 1        | (1500,4500) (5000,4500) (5000,6500) (1500,6500)              |
| PASTURES          | 1        | (3000,3000) (6000,3000) (6000,5000) (3000,5000)              |
| OPEN_GRASSLAND    | 0        | (0,0) (16800,0) (16800,7000) (0,7000)                        |

---

## Impassable

| description           | vertices                                                    |
|-----------------------|-------------------------------------------------------------|
| Rocky outcrop W cliffs | (2800,2700) (3200,2700) (3200,3300) (2800,3300)             |
| Rocky outcrop E cliffs | (8700,2200) (9300,2200) (9300,2800) (8700,2800)             |

---

## Connections

| name               | x       | y      | destination                    |
|--------------------|---------|--------|--------------------------------|
| road_to_driftmoor  | 1000.0  | 5500.0 | places/driftmoor               |
| coastal_path_west  | 0.0     | 3000.0 | places/azure_sea               |
| plains_east        | 16500.0 | 3500.0 | places/plains_of_stonehearth   |
