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
| drowned_isle       | 2925  | 14300 |
| sea_stacks_cluster | 3900 | 18850 |
| harbor_mouth       | 7800 | 8450 |
| deep_water_center  | 2600  | 9750 |
| coastal_shallows   | 5850 | 6500 |
| tidal_flats        | 4875 | 15600 |

---

## Zones

| name           | render_z | vertices                                                    |
|----------------|----------|-------------------------------------------------------------|
| DROWNED_ISLE   | 9.75        | (2275,13650) (3575,13650) (3575,14950) (2275,14950)               |
| SEA_STACKS     | 9.75        | (3250,18200) (4550,18200) (4550,19500) (3250,19500)             |
| HARBOR_APPROACH| 6.5        | (6500,7475) (8125,7475) (8125,9425) (6500,9425)              |
| TIDAL_ZONE     | 6.5        | (3900,13000) (6500,13000) (6500,20150) (3900,20150)             |
| OPEN_WATER     | 3.25        | (0,0) (7150,0) (7800,10400) (6500,27625) (0,27625)             |
| EXTERIOR       | 0.0        | (0,0) (8125,0) (8125,27625) (0,27625)                         |

---

## Impassable

| description        | vertices                                                    |
|--------------------|-------------------------------------------------------------|
| Open deep water    | (0,0) (4875,0) (4875,10400) (3250,26000) (0,26000)             |

---

## Connections

| name              | x      | y      | destination                          |
|-------------------|--------|--------|--------------------------------------|
| to_harbor         | 7800 | 8450 | places/driftmoor                     |
| to_drowned_isle   | 2925  | 14300 | places/azure_sea/drowned_isle        |
| to_sea_stacks     | 3900 | 18850 | places/azure_sea/sea_stacks          |
| to_coastal_path   | 7150 | 3250 | places/plains_of_stonehearth         |

---

## Boundaries

### Open Water

- **type:** physical
- **blocks:** land_creature
- **effect:** impassable without vessel or swimming ability; cold water, strong tides
- **vertices:** (0,0) (7150,0) (7800,10400) (6500,27625) (0,27625)

### Tidal Access Zone

- **type:** conditional
- **blocks:** all
- **effect:** accessible only at low tide on foot; at high tide requires a boat
- **vertices:** (2275,13000) (6500,13000) (6500,20150) (2275,20150)
