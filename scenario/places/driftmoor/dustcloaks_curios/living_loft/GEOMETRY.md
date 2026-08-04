# GEOMETRY.md — Dustcloak's Curios Living Loft

## Scene

- **name:** Dustcloak's Living Loft
- **place_path:** places/driftmoor/dustcloaks_curios/living_loft
- **z_level:** 25.25
- **width:** 19.5
- **height:** 13
- **origin:** 6.5, 13, 9

Notes: Private upper story above the rear of the shop. The stair arrives at
the southeast corner.

---

## Landmarks

| name                | x    | y   | z |
|---------------------|------|-----|---|
| backroom_stair      | 17.21   | 4.455 | 0 |
| reinforced_cabinets | 6.3    | 11.554   | 4 |
| locked_chest        | 8.61   | 5.504   | 4 |
| narrow_bed          | 3.942    | 5.779   | 4 |
| wardrobe            | 11.674    | 10.483   | 4 |

---

## Zones

| name        | floor_z | ceiling_z | render_z | vertices                     |
|-------------|---------|-----------|----------|------------------------------|
| LIVING_LOFT | 0       | 8         | 3.25     | (0,0) (19.5,0) (19.5,13) (0,13) |

---

## Impassable

| description  | vertices                         |
|--------------|----------------------------------|
| North rafters | (0,12) (19.5,12) (19.5,13) (0,13) |

---

## Connections

| name             | x  | y   | destination                                  |
|------------------|----|-----|----------------------------------------------|
| to_backroom      | 16 | 4.5 | places/driftmoor/dustcloaks_curios          |
