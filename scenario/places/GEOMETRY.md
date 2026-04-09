# GEOMETRY.md — The Region Around Driftmoor

## Scene

- **name:** The Region Around Driftmoor
- **place_path:** places/
- **z_level:** 0.0
- **width:** 20000.0
- **height:** 20000.0
- **origin:** 0.0, 0.0, 0.0

Notes: World coordinate origin at southwest corner of regional map.
X increases east, Y increases north. Sea level = 0.0. All child
place origins are expressed in these world coordinates. The regional
map is roughly 20km x 20km. Driftmoor town sits at approximately
(2800, 2600) — on the coast where the Greywater meets the Azure Sea.
The Obelisk Reach is ~10km north-northwest of town.

---

## Landmarks

| name                   | x       | y       |
|------------------------|---------|---------|
| driftmoor_town_center  | 2900.0  | 2700.0  |
| harbor_mouth           | 2400.0  | 2600.0  |
| greywater_river_mouth  | 3100.0  | 3000.0  |
| willowford_bridge      | 4800.0  | 3800.0  |
| old_mill               | 5400.0  | 4300.0  |
| watchtower_hill        | 6100.0  | 9600.0  |
| fey_glade              | 7222.0  | 11408.0 |
| mistwood_center        | 7000.0  | 10500.0 |
| obelisk_reach_edge     | 3500.0  | 12800.0 |
| shattered_obelisk      | 3400.0  | 13800.0 |
| echoing_caverns_mouth  | 3700.0  | 13500.0 |
| sea_stacks_cluster     | 1200.0  | 5800.0  |
| drowned_isle           | 900.0   | 4400.0  |
| plains_center          | 10000.0 | 2000.0  |
| willowford_ford        | 4600.0  | 3600.0  |

---

## Zones

Zone order matters — first match wins in zone_at(). EXTERIOR must be last.
Sub-zones appear before their parent zones.

| name                  | render_z | vertices                                                                    |
|-----------------------|----------|-----------------------------------------------------------------------------|
| DRIFTMOOR_TOWN        | 3        | (2600,2400) (3200,2400) (3200,3100) (2600,3100)                             |
| HARBOR                | 3        | (2100,2400) (2700,2400) (2700,3000) (2100,3000)                             |
| GREYWATER_RIVER       | 2        | (3000,2900) (3300,2900) (5700,4500) (5300,4500) (2900,3100)                 |
| OLD_MILL_SITE         | 3        | (5200,4100) (5700,4100) (5700,4600) (5200,4600)                             |
| OBELISK_REACH         | 2        | (2600,11500) (5000,11500) (5200,15000) (2400,15000)                         |
| SHATTERED_OBELISK     | 3        | (3100,13500) (3700,13500) (3700,14200) (3100,14200)                         |
| ECHOING_CAVERNS       | 3        | (3500,13200) (4000,13200) (4000,13800) (3500,13800)                         |
| FEY_GLADE             | 3        | (7172,11358) (7272,11358) (7272,11458) (7172,11458)                         |
| MISTWOOD_HILLS        | 1        | (4200,7000) (11000,7000) (11000,14500) (4200,14500)                         |
| FARMS_AND_FIELDS      | 1        | (3200,3000) (6500,3000) (6500,5500) (3200,5500)                             |
| PLAINS_OF_STONEHEARTH | 1        | (3200,0) (20000,0) (20000,7000) (3200,7000)                                 |
| AZURE_SEA             | 1        | (0,0) (2200,0) (2400,3200) (2000,8500) (0,8500)                             |
| EXTERIOR              | 0        | (0,0) (20000,0) (20000,20000) (0,20000)                                     |

---

## Impassable

| description             | vertices                                                         |
|-------------------------|------------------------------------------------------------------|
| Azure Sea open water    | (0,0) (2200,0) (2400,3200) (2000,8500) (0,8500)                 |
| Obelisk Reach cliffs    | (2400,13000) (2800,13000) (2800,15500) (2400,15500)              |
| Mistwood interior — no path | (5500,8500) (9500,8500) (9500,13000) (5500,13000)            |

---

## Connections

| name                  | x       | y       | destination                               |
|-----------------------|---------|---------|-------------------------------------------|
| to_driftmoor_town     | 2900.0  | 2700.0  | places/driftmoor                          |
| to_harbor             | 2300.0  | 2700.0  | places/driftmoor/harbor                   |
| to_old_mill           | 5400.0  | 4300.0  | places/greywater_river/old_mill           |
| to_willowford_bridge  | 4800.0  | 3800.0  | places/greywater_river/willowford_bridge  |
| to_obelisk_reach      | 3500.0  | 12800.0 | places/obelisk_reach                      |
| to_echoing_caverns    | 3700.0  | 13500.0 | places/obelisk_reach/echoing_caverns      |
| to_fey_glade_trail    | 6500.0  | 9200.0  | places/mistwood_hills/fey_glade           |
| to_watchtower         | 6100.0  | 9600.0  | places/mistwood_hills/old_watchtower      |
| to_drowned_isle       | 900.0   | 4400.0  | places/azure_sea/drowned_isle             |
| to_plains             | 10000.0 | 2000.0  | places/plains_of_stonehearth              |

---

## Boundaries

### Obelisk Reach Distortion Field

- **type:** magical
- **blocks:** none
- **effect:** perception checks degraded, compasses spin, light sources flicker
- **vertices:** (2600,11500) (5000,11500) (5200,15000) (2400,15000)

### Azure Sea — Open Water

- **type:** physical
- **blocks:** land_creature
- **effect:** impassable without vessel or swimming ability; cold, strong tides
- **vertices:** (0,0) (2200,0) (2400,3200) (2000,8500) (0,8500)

### Mistwood Disorientation Zone

- **type:** magical
- **blocks:** none
- **effect:** paths shift — navigation DC 15 or party becomes lost; whispers audible
- **vertices:** (5500,8500) (9500,8500) (9500,13000) (5500,13000)