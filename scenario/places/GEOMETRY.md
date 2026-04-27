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
(29575,27462) — on the coast where the Greywater meets the Azure Sea.
The Obelisk Reach is ~105.62km north-northwest of town.

---

## Landmarks

| name                   | x       | y       |
|------------------------|---------|---------|
| driftmoor_town_center  | 30631  | 28518  |
| harbor_mouth           | 25350  | 27462  |
| greywater_river_mouth  | 32743  | 31687  |
| willowford_bridge      | 50700  | 40137  |
| old_mill               | 57037  | 45418  |
| watchtower_hill        | 64431  | 101400  |
| fey_glade              | 76282  | 120497 |
| mistwood_center        | 73937  | 110906 |
| obelisk_reach_edge     | 36968  | 135200 |
| shattered_obelisk      | 35912  | 145762 |
| echoing_caverns_mouth  | 39081  | 142593 |
| sea_stacks_cluster     | 12675  | 61262  |
| drowned_isle           | 9506   | 46475  |
| plains_center          | 105625 | 21125  |
| willowford_ford        | 48587  | 38025  |

---

## Zones

Zone order matters — first match wins in zone_at(). EXTERIOR must be last.
Sub-zones appear before their parent zones.

| name                  | render_z | vertices                                                                    |
|-----------------------|----------|-----------------------------------------------------------------------------|
| DRIFTMOOR_TOWN        | 31.69        | (27462,25350) (33800,25350) (33800,32743) (27462,32743)                             |
| HARBOR                | 31.69        | (22181,25350) (28518,25350) (28518,31687) (22181,31687)                             |
| GREYWATER_RIVER       | 21.12        | (31687,30631) (34856,30631) (60206,47531) (55981,47531) (30631,32743)                 |
| OLD_MILL_SITE         | 31.69        | (54925,43306) (60206,43306) (60206,48587) (54925,48587)                             |
| OBELISK_REACH         | 21.12        | (27462,121468) (52812,121468) (54925,158437) (25350,158437)                         |
| SHATTERED_OBELISK     | 31.69        | (32743,142593) (39081,142593) (39081,149987) (32743,149987)                         |
| ECHOING_CAVERNS       | 31.69        | (36968,139425) (42250,139425) (42250,145762) (36968,145762)                         |
| FEY_GLADE             | 31.69        | (75754,119968) (76810,119968) (76810,121025) (75754,121025)                         |
| MISTWOOD_HILLS        | 10.56        | (44362,73937) (116187,73937) (116187,153156) (44362,153156)                         |
| FARMS_AND_FIELDS      | 10.56        | (33800,31687) (68656,31687) (68656,58093) (33800,58093)                             |
| PLAINS_OF_STONEHEARTH | 10.56        | (33800,0) (211250,0) (211250,73937) (33800,73937)                                 |
| AZURE_SEA             | 10.56        | (0,0) (23237,0) (25350,33800) (21125,89781) (0,89781)                             |
| EXTERIOR              | 0.0        | (0,0) (211250,0) (211250,211250) (0,211250)                                     |

---

## Impassable

| description             | vertices                                                         |
|-------------------------|------------------------------------------------------------------|
| Azure Sea open water    | (0,0) (23237,0) (25350,33800) (21125,89781) (0,89781)                 |
| Obelisk Reach cliffs    | (25350,137312) (29575,137312) (29575,163718) (25350,163718)              |
| Mistwood interior — no path | (58093,89781) (100343,89781) (100343,137312) (58093,137312)            |

---

## Connections

| name                  | x       | y       | destination                               |
|-----------------------|---------|---------|-------------------------------------------|
| to_driftmoor_town     | 30631  | 28518  | places/driftmoor                          |
| to_harbor             | 24293  | 28518  | places/driftmoor/harbor                   |
| to_old_mill           | 57037  | 45418  | places/greywater_river/old_mill           |
| to_willowford_bridge  | 50700  | 40137  | places/greywater_river/willowford_bridge  |
| to_obelisk_reach      | 36968  | 135200 | places/obelisk_reach                      |
| to_echoing_caverns    | 39081  | 142593 | places/obelisk_reach/echoing_caverns      |
| to_fey_glade_trail    | 68656  | 97175  | places/mistwood_hills/fey_glade           |
| to_watchtower         | 64431  | 101400  | places/mistwood_hills/old_watchtower      |
| to_drowned_isle       | 9506   | 46475  | places/azure_sea/drowned_isle             |
| to_plains             | 105625 | 21125  | places/plains_of_stonehearth              |

---

## Boundaries

### Obelisk Reach Distortion Field

- **type:** magical
- **blocks:** none
- **effect:** perception checks degraded, compasses spin, light sources flicker
- **vertices:** (27462,121468) (52812,121468) (54925,158437) (25350,158437)

### Azure Sea — Open Water

- **type:** physical
- **blocks:** land_creature
- **effect:** impassable without vessel or swimming ability; cold, strong tides
- **vertices:** (0,0) (23237,0) (25350,33800) (21125,89781) (0,89781)

### Mistwood Disorientation Zone

- **type:** magical
- **blocks:** none
- **effect:** paths shift — navigation DC 158.44 or party becomes lost; whispers audible
- **vertices:** (58093,89781) (100343,89781) (100343,137312) (58093,137312)