# GEOMETRY.md — The Greywater River

## Scene

- **name:** The Greywater River
- **place_path:** places/greywater_river
- **z_level:** 9.75
- **width:** 9750.0
- **height:** 6500.0
- **origin:** 9425.0, 9425.0, 9.75

Notes: The river corridor from Driftmoor to the Old Mill area.
Origin at southwest corner near the river mouth. X increases east
(upriver), Y increases north. The river flows roughly west-southwest
from the mill area. Banks are lined with willows downstream, open
fields upstream. Willowford Bridge crosses midway.

---

## Landmarks

| name                | x      | y      |
|---------------------|--------|--------|
| river_mouth         | 650.0  | 325.0  |
| willowford_bridge   | 6175.0 | 2925.0  |
| willowford_ford     | 5525.0 | 2275.0  |
| old_mill            | 8125.0 | 4550.0 |
| willow_bend         | 2600.0  | 1300.0  |
| fishing_bank        | 1625.0  | 650.0  |
| farmers_landing     | 4550.0 | 1950.0  |
| otter_den           | 3575.0 | 1787.5  |

---

## Zones

| name              | render_z | vertices                                              |
|-------------------|----------|-------------------------------------------------------|
| OLD_MILL_AREA     | 6.5        | (7475.0,3900.0) (8775.0,3900.0) (8775.0,5200.0) (7475.0,5200.0)        |
| WILLOWFORD        | 6.5        | (5200.0,2275.0) (6825.0,2275.0) (6825.0,3575.0) (5200.0,3575.0)          |
| RIVER_CHANNEL     | 3.25        | (325.0,162.5) (8775.0,4387.5) (8775.0,4875.0) (325.0,650.0)             |
| NORTH_BANK        | 3.25        | (325.0,650.0) (8775.0,4875.0) (8775.0,6500.0) (325.0,6500.0)           |
| SOUTH_BANK        | 3.25        | (325.0,0.0) (8775.0,0.0) (8775.0,4387.5) (325.0,162.5)                  |
| EXTERIOR          | 0.0        | (0.0,0.0) (9750.0,0.0) (9750.0,6500.0) (0.0,6500.0)                    |

---

## Impassable

| description         | vertices                                              |
|---------------------|-------------------------------------------------------|
| River deep channel  | (650.0,260.0) (8450.0,4485.0) (8450.0,4777.5) (650.0,552.5)            |

---

## Connections

| name               | x      | y      | destination                              |
|--------------------|--------|--------|------------------------------------------|
| to_driftmoor       | 325.0  | 325.0  | places/driftmoor                         |
| to_willowford      | 6175.0 | 2925.0  | places/greywater_river/willowford_bridge |
| to_old_mill        | 8125.0 | 4550.0 | places/greywater_river/old_mill          |
| to_mistwood        | 9100.0 | 5850.0 | places/mistwood_hills                    |
| to_farms           | 4875.0 | 325.0  | places/driftmoor                         |

---

## Boundaries

### River Crossing

- **type:** physical
- **blocks:** land_creature
- **effect:** river impassable except at Willowford Bridge or ford (DC 45.5 Athletics to ford, cold fast water)
- **vertices:** (325.0,162.5) (8775.0,4387.5) (8775.0,4875.0) (325.0,650.0)
