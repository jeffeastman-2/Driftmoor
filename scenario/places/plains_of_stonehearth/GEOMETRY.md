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
| plains_center      | 22100  | 6500 |
| northern_farmstead | 6500  | 17875 |
| southern_farmstead | 16250  | 3250 |
| rocky_outcrop_west | 9750  | 9750 |
| rocky_outcrop_east | 29250  | 8125 |
| sheep_pasture      | 13000  | 13000 |
| shadowbeast_den    | 26000  | 11375 |
| coastal_path_west  | 1625   | 9750 |
| road_to_driftmoor  | 3250  | 17875 |

---

## Zones

| name | render_z | auto_wall | vertices |
|-------------------|----------|---------|-------------------------------------------------------------|
| ROCKY_OUTCROP_W | 6.5 |  | (8125,8125) (11375,8125) (11375,11375) (8125,11375) |
| ROCKY_OUTCROP_E | 6.5 |  | (27625,6500) (30875,6500) (30875,9750) (27625,9750) |
| FARMLANDS | 3.25 |  | (4875,14625) (16250,14625) (16250,21125) (4875,21125) |
| PASTURES | 3.25 |  | (9750,9750) (19500,9750) (19500,16250) (9750,16250) |
| OPEN_GRASSLAND | 0.0 |  | (0,0) (54600,0) (54600,22750) (0,22750) |
---

## Walls

- **auto_wall:** false

This is a grasslands region map — an exploration area, not rooms with
doors. None of these zones share a coincident edge with any other, so
the per-zone perimeter pass would seal every one into an isolated box
with no door to open it.

## Impassable

| description           | vertices                                                    |
|-----------------------|-------------------------------------------------------------|
| Rocky outcrop W cliffs | (9100,8775) (10400,8775) (10400,10725) (9100,10725)             |
| Rocky outcrop E cliffs | (28275,7150) (30225,7150) (30225,9100) (28275,9100)             |

---

## Connections

| name               | x       | y      | destination                    |
|--------------------|---------|--------|--------------------------------|
| road_to_driftmoor  | 3250  | 17875 | places/driftmoor               |
| coastal_path_west  | 0     | 9750 | places/azure_sea               |
| plains_east        | 53625 | 11375 | places/plains_of_stonehearth   |
