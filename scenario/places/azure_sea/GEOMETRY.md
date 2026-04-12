# GEOMETRY.md — The Azure Sea

## Scene

- **name:** The Azure Sea
- **place_path:** places/azure_sea
- **z_level:** 0.0
- **width:** 8125.0
- **height:** 27625.0
- **origin:** 0.0, 0.0, 0.0

Notes: Coastal waters west of Driftmoor. Origin at southwest corner
of the sea zone. X increases east (toward shore), Y increases north.
Most of this area is open water (impassable without a vessel). The
harbor mouth is accessed from the east. The sea stacks and Drowned
Isle are the only navigable features beyond the harbor.

---

## Landmarks

| name               | x      | y      |
|--------------------|--------|--------|
| drowned_isle       | 2925.0  | 14300.0 |
| sea_stacks_cluster | 3900.0 | 18850.0 |
| harbor_mouth       | 7800.0 | 8450.0 |
| deep_water_center  | 2600.0  | 9750.0 |
| coastal_shallows   | 5850.0 | 6500.0 |
| tidal_flats        | 4875.0 | 15600.0 |

---

## Zones

| name           | render_z | vertices                                                    |
|----------------|----------|-------------------------------------------------------------|
| DROWNED_ISLE   | 9.75        | (2275.0,13650.0) (3575.0,13650.0) (3575.0,14950.0) (2275.0,14950.0)               |
| SEA_STACKS     | 9.75        | (3250.0,18200.0) (4550.0,18200.0) (4550.0,19500.0) (3250.0,19500.0)             |
| HARBOR_APPROACH| 6.5        | (6500.0,7475.0) (8125.0,7475.0) (8125.0,9425.0) (6500.0,9425.0)              |
| TIDAL_ZONE     | 6.5        | (3900.0,13000.0) (6500.0,13000.0) (6500.0,20150.0) (3900.0,20150.0)             |
| OPEN_WATER     | 3.25        | (0.0,0.0) (7150.0,0.0) (7800.0,10400.0) (6500.0,27625.0) (0.0,27625.0)             |
| EXTERIOR       | 0.0        | (0.0,0.0) (8125.0,0.0) (8125.0,27625.0) (0.0,27625.0)                         |

---

## Impassable

| description        | vertices                                                    |
|--------------------|-------------------------------------------------------------|
| Open deep water    | (0.0,0.0) (4875.0,0.0) (4875.0,10400.0) (3250.0,26000.0) (0.0,26000.0)             |

---

## Connections

| name              | x      | y      | destination                          |
|-------------------|--------|--------|--------------------------------------|
| to_harbor         | 7800.0 | 8450.0 | places/driftmoor                     |
| to_drowned_isle   | 2925.0  | 14300.0 | places/azure_sea/drowned_isle        |
| to_sea_stacks     | 3900.0 | 18850.0 | places/azure_sea/sea_stacks          |
| to_coastal_path   | 7150.0 | 3250.0 | places/plains_of_stonehearth         |

---

## Boundaries

### Open Water

- **type:** physical
- **blocks:** land_creature
- **effect:** impassable without vessel or swimming ability; cold water, strong tides
- **vertices:** (0.0,0.0) (7150.0,0.0) (7800.0,10400.0) (6500.0,27625.0) (0.0,27625.0)

### Tidal Access Zone

- **type:** conditional
- **blocks:** all
- **effect:** accessible only at low tide on foot; at high tide requires a boat
- **vertices:** (2275.0,13000.0) (6500.0,13000.0) (6500.0,20150.0) (2275.0,20150.0)
