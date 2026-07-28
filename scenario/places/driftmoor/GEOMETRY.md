# GEOMETRY.md — Driftmoor Town

## Scene

- **name:** Driftmoor Town
- **place_path:** places/driftmoor
- **z_level:** 16.25
- **width:** 1625.0
- **height:** 1462.5
- **origin:** 8450.0, 7800.0, 16.25

Notes: Local coordinates origin at southwest corner (Fisher Folk
quarter). X increases east, Y increases north. Scale: ~812.5m of
built town plus surrounding roads and harbor. The Greywater River
forms the northern boundary, curving from northwest to northeast.
The harbor and docks lie to the west. Streets are 16.25-32.5m wide.
Buildings are 48.75-81.25m footprints. The town sits 16.25m above sea level
on average; the church rise is slightly higher at ~26.0m.

Building centers are given as landmarks. Each named building with
spatial complexity has its own GEOMETRY.md. Simple single-room
buildings do not.

---

## Landmarks

| name                  | x     | y     |
|-----------------------|-------|-------|
| town_center           | 812 | 682 |
| well                  | 982.5 | 672.5 |
| greywater_bend        | 682 | 1105 |
| bridge_crossing       | 1267 | 1137 |
| harbor_pier_north     | 178  | 1007 |
| harbor_pier_south     | 146  | 812 |
| road_to_obelisk       | 568 | 1397 |
| road_to_old_mill      | 1592 | 747 |
| road_to_stonehearth   | 877 | 32  |
| graveyard_center      | 861 | 1348 |
| garden_center         | 877 | 243  |
| stable_center         | 1267 | 195  |
| corral_center         | 1446 | 227  |
| fisherfolk_center     | 292  | 130  |

---

## Zones

Zone order matters — first match wins in zone_at(). Zones are **per-building
footprints** (one zone per structure on the town map, centred on the building's
landmark), followed by the open ground and water they sit in, then EXTERIOR
last. So the more specific a zone, the earlier it is listed: a point inside the
tavern resolves to TAVERN, not MARKET_SQUARE or TOWN_COMMON. ``render_z`` only
affects draw stacking (higher = on top): buildings/docks (5) over the open
square/garden (4) over water (3) over the common ground (2) over EXTERIOR (0).

| name              | render_z | vertices                                                    |
|-------------------|----------|-------------------------------------------------------------|
| GRAVEYARD        | 5.0      | (696,1260) (1026,1260) (1026,1436) (696,1436) |
| CHURCH           | 5.0      | (1041,1260) (1265,1260) (1265,1436) (1041,1436) |
| DUSTCLOAKS_HOUSE | 5.0      | (425,1201) (581,1201) (581,1365) (425,1365) |
| MAYORS_HALL      | 5.0      | (1310,846) (1420,846) (1420,1038) (1310,1038) |
| MIDWIFE          | 5.0      | (1424,951) (1500,951) (1500,1063) (1424,1063) |
| TANNERY          | 5.0      | (646,933) (750,933) (750,1049) (646,1049) |
| CARPENTER        | 5.0      | (559,886) (643,886) (643,998) (559,998) |
| TAILOR           | 5.0      | (768,894) (888,894) (888,990) (768,990) |
| WEAVER           | 5.0      | (903,894) (1013,894) (1013,990) (903,990) |
| COOPER           | 5.0      | (530,776) (640,776) (640,880) (530,880) |
| COBBLER          | 5.0      | (704,728) (790,728) (790,832) (704,832) |
| BARBER           | 5.0      | (795,728) (861,728) (861,832) (795,832) |
| ROOMING_HOUSE    | 5.0      | (870,722) (982,722) (982,838) (870,838) |
| APOTHECARY       | 5.0      | (988,728) (1092,728) (1092,832) (988,832) |
| SCHOOLHOUSE      | 5.0      | (1285,687) (1445,687) (1445,807) (1285,807) |
| WATCHTOWER       | 5.0      | (600,665) (666,665) (666,731) (600,731) |
| WELL             | 5.0      | (980,680) (990,680) (990,670) (980,670) |
| FISHMONGER       | 5.0      | (397,627) (513,627) (513,737) (397,737) |
| BAKERY           | 5.0      | (626,504) (738,504) (738,632) (626,632) |
| PAWN_SHOP        | 5.0      | (743,504) (849,504) (849,632) (743,632) |
| TAVERN           | 5.0      | (855,504) (965,504) (965,632) (855,632) |
| MERCANTILE       | 5.0      | (974,504) (1106,504) (1106,632) (974,632) |
| ELYSSA_HOUSE     | 5.0      | (1376,454) (1516,454) (1516,618) (1376,618) |
| GENERAL_STORE    | 5.0      | (470,165) (634,165) (634,355) (470,355) |
| FORGE            | 5.0      | (1205,244) (1329,244) (1329,340) (1205,340) |
| STABLE           | 5.0      | (1205,151) (1329,151) (1329,239) (1205,239) |
| CORRAL           | 5.0      | (1356,139) (1536,139) (1536,315) (1356,315) |
| FISHERFOLK       | 5.0      | (300,750) (485,750) (485,850) (300,850) |
| BRIDGE           | 4.5      | (1235,1050) (1305,1050) (1305,1215) (1235,1215) |
| GARDEN           | 4.0      | (667,150) (1090,150) (1090,338) (667,338) |
| DOCKS            | 5.0      | (300,700) (50,700) (50,850) (300,850) |
| EXIT_OBELISK_REACH  | 2.5   | (455,1385) (650,1385) (650,1460) (455,1460) |
| EXIT_MISTWOOD_HILLS | 2.5   | (1505,1210) (1620,1210) (1620,1360) (1505,1360) |
| EXIT_OLD_MILL       | 2.5   | (1548,655) (1620,655) (1620,830) (1548,830) |
| EXIT_STONEHEARTH    | 2.5   | (762,5) (1000,5) (1000,110) (762,110) |
| AZURE_SEA        | 0.0      | (0,1462) (300,1462) (300,0) (0,0) |
| GREYWATER_RIVER  | 0.0      | (300,1072) (1625,1072) (1625,1200) (300,1200) |
| NORTH_BANK       | 2.0      | (300,1200) (1625,1200) (1625,1462) (300,1462) |
| TOWN_COMMON      | 2.0      | (300,0) (1625,0) (1625,1072) (300,1072) |
---

## Impassable

| description                      | vertices                                          |
|----------------------------------|---------------------------------------------------|
| Greywater River (west of bridge) | (260,1072) (1235,1072) (1235,1180) (260,1170)     |
| Greywater River (east of bridge) | (1305,1072) (1625,1072) (1625,1200) (1305,1200)   |
| Harbor water                     | (0,560) (250,560) (250,1072) (0,1072)             |
| Azure Sea                        | (0,1072) (300,1072) (300,1462) (0,1462)           |

---

## Connections

| name                   | x     | y     | destination                              |
|------------------------|-------|-------|------------------------------------------|
| to_region              | 812 | 731 | places/                                  |
| to_obelisk_road        | 568 | 1446 | places/obelisk_reach                     |
| to_old_mill_road       | 1608 | 747 | places/greywater_river/old_mill          |
| to_stonehearth_road    | 877 | 16   | places/plains_of_stonehearth             |
| to_mistwood_trail      | 1608 | 1235 | places/mistwood_hills                    |
| to_harbor_water        | 97  | 877 | places/azure_sea                         |
| to_dustcloaks_house    | 503 | 1283 | places/driftmoor/dustcloaks_curios       |
| to_church              | 1153 | 1300 | places/driftmoor/beacon_church           |
| to_mayors_hall         | 1365 | 942 | places/driftmoor/mayors_hall             |
| to_tavern              | 910 | 568 | places/driftmoor/broken_lantern          |
| to_salt_and_iron       | 1040 | 568 | places/driftmoor/salt_and_iron           |
| to_forge               | 1267 | 292  | places/driftmoor/forge                   |
| to_stable              | 1267 | 195  | places/driftmoor/stables                 |
| to_corral              | 1446 | 227  | places/driftmoor/corral                  |
| to_elyssa_house        | 1446 | 536 | places/driftmoor/elyssa_cottage           |
| to_apothecary          | 1040 | 780 | places/driftmoor/bitter_remedy           |
| to_gilded_trinket      | 796 | 568 | places/driftmoor/gilded_trinket          |
| to_rooming_house       | 926 | 780 | places/driftmoor/weary_traveler          |
| to_bakery              | 682 | 568 | places/driftmoor/bakery                  |
| to_cobbler             | 747 | 780 | places/driftmoor/cobblers_shop           |
| to_barber              | 828 | 780 | places/driftmoor/rusty_razor             |
| to_cooper              | 585 | 828 | places/driftmoor/coopers_shed            |
| to_carpenter           | 601 | 942 | places/driftmoor/carpenters_workshop     |
| to_weaver              | 958 | 942 | places/driftmoor/weavers_cottage         |
| to_tailor              | 828 | 942 | places/driftmoor/tailors_shop            |
| to_tannery             | 698 | 991 | places/driftmoor/tannery                 |
| to_fishmonger          | 455 | 682 | places/driftmoor/fishmongers_shack       |
| to_schoolhouse         | 1365 | 747 | places/driftmoor/schoolhouse            |
| to_midwife             | 1462 | 1007 | places/driftmoor/midwifes_home         |
| to_watchtower          | 633 | 698 | places/driftmoor/watchtower              |
| to_general_store       | 552 | 260 | places/driftmoor/general_store           |

---

## Boundaries

### Town Perimeter — Settled Ground

- **type:** conditional
- **blocks:** none
- **effect:** beyond this line is wilderness; shadowbeast sightings increase sharply
- **vertices:** (0,0) (1625,0) (1625,1462) (0,1462)

---
