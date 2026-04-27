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
| river_mouth         | 650  | 325  |
| willowford_bridge   | 6175 | 2925  |
| willowford_ford     | 5525 | 2275  |
| old_mill            | 8125 | 4550 |
| willow_bend         | 2600  | 1300  |
| fishing_bank        | 1625  | 650  |
| farmers_landing     | 4550 | 1950  |
| otter_den           | 3575 | 1787  |

---

## Zones

| name              | render_z | vertices                                              |
|-------------------|----------|-------------------------------------------------------|
| OLD_MILL_AREA     | 6.5        | (7475,3900) (8775,3900) (8775,5200) (7475,5200)        |
| WILLOWFORD        | 6.5        | (5200,2275) (6825,2275) (6825,3575) (5200,3575)          |
| RIVER_CHANNEL     | 3.25        | (325,162) (8775,4387) (8775,4875) (325,650)             |
| NORTH_BANK        | 3.25        | (325,650) (8775,4875) (8775,6500) (325,6500)           |
| SOUTH_BANK        | 3.25        | (325,0) (8775,0) (8775,4387) (325,162)                  |
| EXTERIOR          | 0.0        | (0,0) (9750,0) (9750,6500) (0,6500)                    |

---

## Impassable

| description         | vertices                                              |
|---------------------|-------------------------------------------------------|
| River deep channel  | (650,260) (8450,4485) (8450,4777) (650,552)            |

---

## Connections

| name               | x      | y      | destination                              |
|--------------------|--------|--------|------------------------------------------|
| to_driftmoor       | 325  | 325  | places/driftmoor                         |
| to_willowford      | 6175 | 2925  | places/greywater_river/willowford_bridge |
| to_old_mill        | 8125 | 4550 | places/greywater_river/old_mill          |
| to_mistwood        | 9100 | 5850 | places/mistwood_hills                    |
| to_farms           | 4875 | 325  | places/driftmoor                         |

---

## Boundaries

### River Crossing

- **type:** physical
- **blocks:** land_creature
- **effect:** river impassable except at Willowford Bridge or ford (DC 45.5 Athletics to ford, cold fast water)
- **vertices:** (325,162) (8775,4387) (8775,4875) (325,650)
