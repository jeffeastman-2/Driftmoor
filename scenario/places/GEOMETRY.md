# GEOMETRY.md — The Region Around Driftmoor

## Scene

- **name:** The Region Around Driftmoor
- **place_path:** places/
- **z_level:** 0.0
- **width:** 211250.0
- **height:** 211250.0
- **origin:** 0.0, 0.0, 0.0

Notes: World coordinate origin at southwest corner of regional map.
X increases east, Y increases north. Sea level = 0.0. All child
place origins are expressed in these world coordinates. The regional
map is roughly 211.25km x 211.25km. Driftmoor town sits at approximately
(29575.0, 27462.5) — on the coast where the Greywater meets the Azure Sea.
The Obelisk Reach is ~105.62km north-northwest of town.

---

## Landmarks

| name                   | x       | y       |
|------------------------|---------|---------|
| driftmoor_town_center  | 30631.25  | 28518.75  |
| harbor_mouth           | 25350.0  | 27462.5  |
| greywater_river_mouth  | 32743.75  | 31687.5  |
| willowford_bridge      | 50700.0  | 40137.5  |
| old_mill               | 57037.5  | 45418.75  |
| watchtower_hill        | 64431.25  | 101400.0  |
| fey_glade              | 76282.38  | 120497.0 |
| mistwood_center        | 73937.5  | 110906.25 |
| obelisk_reach_edge     | 36968.75  | 135200.0 |
| shattered_obelisk      | 35912.5  | 145762.5 |
| echoing_caverns_mouth  | 39081.25  | 142593.75 |
| sea_stacks_cluster     | 12675.0  | 61262.5  |
| drowned_isle           | 9506.25   | 46475.0  |
| plains_center          | 105625.0 | 21125.0  |
| willowford_ford        | 48587.5  | 38025.0  |

---

## Zones

Zone order matters — first match wins in zone_at(). EXTERIOR must be last.
Sub-zones appear before their parent zones.

| name                  | render_z | vertices                                                                    |
|-----------------------|----------|-----------------------------------------------------------------------------|
| DRIFTMOOR_TOWN        | 31.69        | (27462.5,25350.0) (33800.0,25350.0) (33800.0,32743.75) (27462.5,32743.75)                             |
| HARBOR                | 31.69        | (22181.25,25350.0) (28518.75,25350.0) (28518.75,31687.5) (22181.25,31687.5)                             |
| GREYWATER_RIVER       | 21.12        | (31687.5,30631.25) (34856.25,30631.25) (60206.25,47531.25) (55981.25,47531.25) (30631.25,32743.75)                 |
| OLD_MILL_SITE         | 31.69        | (54925.0,43306.25) (60206.25,43306.25) (60206.25,48587.5) (54925.0,48587.5)                             |
| OBELISK_REACH         | 21.12        | (27462.5,121468.75) (52812.5,121468.75) (54925.0,158437.5) (25350.0,158437.5)                         |
| SHATTERED_OBELISK     | 31.69        | (32743.75,142593.75) (39081.25,142593.75) (39081.25,149987.5) (32743.75,149987.5)                         |
| ECHOING_CAVERNS       | 31.69        | (36968.75,139425.0) (42250.0,139425.0) (42250.0,145762.5) (36968.75,145762.5)                         |
| FEY_GLADE             | 31.69        | (75754.25,119968.88) (76810.5,119968.88) (76810.5,121025.12) (75754.25,121025.12)                         |
| MISTWOOD_HILLS        | 10.56        | (44362.5,73937.5) (116187.5,73937.5) (116187.5,153156.25) (44362.5,153156.25)                         |
| FARMS_AND_FIELDS      | 10.56        | (33800.0,31687.5) (68656.25,31687.5) (68656.25,58093.75) (33800.0,58093.75)                             |
| PLAINS_OF_STONEHEARTH | 10.56        | (33800.0,0.0) (211250.0,0.0) (211250.0,73937.5) (33800.0,73937.5)                                 |
| AZURE_SEA             | 10.56        | (0.0,0.0) (23237.5,0.0) (25350.0,33800.0) (21125.0,89781.25) (0.0,89781.25)                             |
| EXTERIOR              | 0.0        | (0.0,0.0) (211250.0,0.0) (211250.0,211250.0) (0.0,211250.0)                                     |

---

## Impassable

| description             | vertices                                                         |
|-------------------------|------------------------------------------------------------------|
| Azure Sea open water    | (0.0,0.0) (23237.5,0.0) (25350.0,33800.0) (21125.0,89781.25) (0.0,89781.25)                 |
| Obelisk Reach cliffs    | (25350.0,137312.5) (29575.0,137312.5) (29575.0,163718.75) (25350.0,163718.75)              |
| Mistwood interior — no path | (58093.75,89781.25) (100343.75,89781.25) (100343.75,137312.5) (58093.75,137312.5)            |

---

## Connections

| name                  | x       | y       | destination                               |
|-----------------------|---------|---------|-------------------------------------------|
| to_driftmoor_town     | 30631.25  | 28518.75  | places/driftmoor                          |
| to_harbor             | 24293.75  | 28518.75  | places/driftmoor/harbor                   |
| to_old_mill           | 57037.5  | 45418.75  | places/greywater_river/old_mill           |
| to_willowford_bridge  | 50700.0  | 40137.5  | places/greywater_river/willowford_bridge  |
| to_obelisk_reach      | 36968.75  | 135200.0 | places/obelisk_reach                      |
| to_echoing_caverns    | 39081.25  | 142593.75 | places/obelisk_reach/echoing_caverns      |
| to_fey_glade_trail    | 68656.25  | 97175.0  | places/mistwood_hills/fey_glade           |
| to_watchtower         | 64431.25  | 101400.0  | places/mistwood_hills/old_watchtower      |
| to_drowned_isle       | 9506.25   | 46475.0  | places/azure_sea/drowned_isle             |
| to_plains             | 105625.0 | 21125.0  | places/plains_of_stonehearth              |

---

## Boundaries

### Obelisk Reach Distortion Field

- **type:** magical
- **blocks:** none
- **effect:** perception checks degraded, compasses spin, light sources flicker
- **vertices:** (27462.5,121468.75) (52812.5,121468.75) (54925.0,158437.5) (25350.0,158437.5)

### Azure Sea — Open Water

- **type:** physical
- **blocks:** land_creature
- **effect:** impassable without vessel or swimming ability; cold, strong tides
- **vertices:** (0.0,0.0) (23237.5,0.0) (25350.0,33800.0) (21125.0,89781.25) (0.0,89781.25)

### Mistwood Disorientation Zone

- **type:** magical
- **blocks:** none
- **effect:** paths shift — navigation DC 158.44 or party becomes lost; whispers audible
- **vertices:** (58093.75,89781.25) (100343.75,89781.25) (100343.75,137312.5) (58093.75,137312.5)