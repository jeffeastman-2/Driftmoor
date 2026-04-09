# GEOMETRY.md — The Azure Sea

## Scene

- **name:** The Azure Sea
- **place_path:** places/azure_sea
- **z_level:** 0.0
- **width:** 2500.0
- **height:** 8500.0
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
| drowned_isle       | 900.0  | 4400.0 |
| sea_stacks_cluster | 1200.0 | 5800.0 |
| harbor_mouth       | 2400.0 | 2600.0 |
| deep_water_center  | 800.0  | 3000.0 |
| coastal_shallows   | 1800.0 | 2000.0 |
| tidal_flats        | 1500.0 | 4800.0 |

---

## Zones

| name           | render_z | vertices                                                    |
|----------------|----------|-------------------------------------------------------------|
| DROWNED_ISLE   | 3        | (700,4200) (1100,4200) (1100,4600) (700,4600)               |
| SEA_STACKS     | 3        | (1000,5600) (1400,5600) (1400,6000) (1000,6000)             |
| HARBOR_APPROACH| 2        | (2000,2300) (2500,2300) (2500,2900) (2000,2900)              |
| TIDAL_ZONE     | 2        | (1200,4000) (2000,4000) (2000,6200) (1200,6200)             |
| OPEN_WATER     | 1        | (0,0) (2200,0) (2400,3200) (2000,8500) (0,8500)             |
| EXTERIOR       | 0        | (0,0) (2500,0) (2500,8500) (0,8500)                         |

---

## Impassable

| description        | vertices                                                    |
|--------------------|-------------------------------------------------------------|
| Open deep water    | (0,0) (1500,0) (1500,3200) (1000,8000) (0,8000)             |

---

## Connections

| name              | x      | y      | destination                          |
|-------------------|--------|--------|--------------------------------------|
| to_harbor         | 2400.0 | 2600.0 | places/driftmoor                     |
| to_drowned_isle   | 900.0  | 4400.0 | places/azure_sea/drowned_isle        |
| to_sea_stacks     | 1200.0 | 5800.0 | places/azure_sea/sea_stacks          |
| to_coastal_path   | 2200.0 | 1000.0 | places/plains_of_stonehearth         |

---

## Boundaries

### Open Water

- **type:** physical
- **blocks:** land_creature
- **effect:** impassable without vessel or swimming ability; cold water, strong tides
- **vertices:** (0,0) (2200,0) (2400,3200) (2000,8500) (0,8500)

### Tidal Access Zone

- **type:** conditional
- **blocks:** all
- **effect:** accessible only at low tide on foot; at high tide requires a boat
- **vertices:** (700,4000) (2000,4000) (2000,6200) (700,6200)
