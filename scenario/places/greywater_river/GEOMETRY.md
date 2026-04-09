# GEOMETRY.md — The Greywater River

## Scene

- **name:** The Greywater River
- **place_path:** places/greywater_river
- **z_level:** 3.0
- **width:** 3000.0
- **height:** 2000.0
- **origin:** 2900.0, 2900.0, 3.0

Notes: The river corridor from Driftmoor to the Old Mill area.
Origin at southwest corner near the river mouth. X increases east
(upriver), Y increases north. The river flows roughly west-southwest
from the mill area. Banks are lined with willows downstream, open
fields upstream. Willowford Bridge crosses midway.

---

## Landmarks

| name                | x      | y      |
|---------------------|--------|--------|
| river_mouth         | 200.0  | 100.0  |
| willowford_bridge   | 1900.0 | 900.0  |
| willowford_ford     | 1700.0 | 700.0  |
| old_mill            | 2500.0 | 1400.0 |
| willow_bend         | 800.0  | 400.0  |
| fishing_bank        | 500.0  | 200.0  |
| farmers_landing     | 1400.0 | 600.0  |
| otter_den           | 1100.0 | 550.0  |

---

## Zones

| name              | render_z | vertices                                              |
|-------------------|----------|-------------------------------------------------------|
| OLD_MILL_AREA     | 2        | (2300,1200) (2700,1200) (2700,1600) (2300,1600)        |
| WILLOWFORD        | 2        | (1600,700) (2100,700) (2100,1100) (1600,1100)          |
| RIVER_CHANNEL     | 1        | (100,50) (2700,1350) (2700,1500) (100,200)             |
| NORTH_BANK        | 1        | (100,200) (2700,1500) (2700,2000) (100,2000)           |
| SOUTH_BANK        | 1        | (100,0) (2700,0) (2700,1350) (100,50)                  |
| EXTERIOR          | 0        | (0,0) (3000,0) (3000,2000) (0,2000)                    |

---

## Impassable

| description         | vertices                                              |
|---------------------|-------------------------------------------------------|
| River deep channel  | (200,80) (2600,1380) (2600,1470) (200,170)            |

---

## Connections

| name               | x      | y      | destination                              |
|--------------------|--------|--------|------------------------------------------|
| to_driftmoor       | 100.0  | 100.0  | places/driftmoor                         |
| to_willowford      | 1900.0 | 900.0  | places/greywater_river/willowford_bridge |
| to_old_mill        | 2500.0 | 1400.0 | places/greywater_river/old_mill          |
| to_mistwood        | 2800.0 | 1800.0 | places/mistwood_hills                    |
| to_farms           | 1500.0 | 100.0  | places/driftmoor                         |

---

## Boundaries

### River Crossing

- **type:** physical
- **blocks:** land_creature
- **effect:** river impassable except at Willowford Bridge or ford (DC 14 Athletics to ford, cold fast water)
- **vertices:** (100,50) (2700,1350) (2700,1500) (100,200)
