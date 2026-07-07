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
| well                  | 1007 | 698 |
| watchtower            | 633 | 698 |
| greywater_bend        | 682 | 1105 |
| bridge_crossing       | 1267 | 1137 |
| harbor_pier_north     | 178  | 1007 |
| harbor_pier_south     | 146  | 812 |
| road_to_obelisk       | 568 | 1397 |
| road_to_old_mill      | 1592 | 747 |
| road_to_stonehearth   | 877 | 32  |
| dustcloaks_house      | 503 | 1283 |
| graveyard_center      | 861 | 1348 |
| church_center         | 1153 | 1300 |
| mayors_hall_center    | 1365 | 942 |
| midwife_center        | 1462 | 1007 |
| schoolhouse_center    | 1365 | 747 |
| elyssa_house_center   | 1446 | 536 |
| tannery_center        | 698 | 991 |
| carpenter_center      | 601 | 942 |
| cooper_center         | 585 | 828 |
| tailor_center         | 828 | 942 |
| weaver_center         | 958 | 942 |
| cobbler_center        | 747 | 780 |
| barber_center         | 828 | 780 |
| rooming_house_center  | 926 | 780 |
| apothecary_center     | 1040 | 780 |
| fishmonger_center     | 455 | 682 |
| bakery_center         | 682 | 568 |
| pawn_shop_center      | 796 | 568 |
| tavern_center         | 910 | 568 |
| mercantile_center     | 1040 | 568 |
| general_store_center  | 552 | 260  |
| garden_center         | 877 | 243  |
| forge_center          | 1267 | 292  |
| stable_center         | 1267 | 195  |
| corral_center         | 1446 | 227  |
| fisherfolk_center     | 292  | 130  |

---

## Zones

Zone order matters — first match wins in zone_at(). EXTERIOR is last.
Sub-zones (individual buildings) appear before their district zone.

| name              | render_z | vertices                                                    |
|-------------------|----------|-------------------------------------------------------------|
| GREYWATER_RIVER   | 6.5        | (260,1072) (1625,1072) (1625,1202) (1267,1202) (260,1170)            |
| GRAVEYARD         | 6.5        | (698,1218) (1023,1218) (1023,1430) (698,1430)                     |
| HARBOR_WATER      | 6.5        | (0,650) (243,650) (243,1105) (0,1105)                           |
| DOCKS             | 6.5        | (97,715) (260,715) (260,1072) (97,1072)                         |
| NORTH_BANK        | 3.25        | (260,1105) (1625,1105) (1625,1462) (260,1462)                       |
| HARBOR_DISTRICT   | 3.25        | (0,325) (422,325) (422,1105) (0,1105)                         |
| CRAFTSMEN_QUARTER | 3.25        | (422,780) (715,780) (715,1072) (422,1072)                     |
| VILLAGE_CENTER    | 3.25        | (422,617) (1365,617) (1365,1072) (422,1072)                     |
| SOUTH_ROW         | 3.25        | (617,503) (1397,503) (1397,650) (617,650)                     |
| EAST_QUARTER      | 3.25        | (1267,325) (1625,325) (1625,1072) (1267,1072)                     |
| SOUTH_QUARTER     | 3.25        | (422,65) (1625,65) (1625,503) (422,503)                       |
| FISHERFOLK        | 3.25        | (0,0) (422,0) (422,325) (0,325)                             |
| EXTERIOR          | 0.0        | (0,0) (1625,0) (1625,1462) (0,1462)                             |

---

## Impassable

| description           | vertices                                                    |
|-----------------------|-------------------------------------------------------------|
| Greywater River       | (260,1072) (1625,1072) (1625,1202) (1267,1202) (260,1170)            |
| Harbor open water     | (0,650) (178,650) (178,1105) (0,1105)                           |
| Graveyard wall        | (698,1218) (1023,1218) (1023,1430) (698,1430)                     |

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
| to_broken_lantern      | 910 | 568 | places/driftmoor/broken_lantern          |
| to_salt_and_iron       | 1040 | 568 | places/driftmoor/salt_and_iron           |
| to_forge               | 1267 | 292  | places/driftmoor/ironhoof_forge          |
| to_elyssa_house        | 1446 | 536 | places/driftmoor/elyssa_residence        |
| to_apothecary          | 1040 | 780 | places/driftmoor/bitter_remedy           |
| to_gilded_trinket      | 796 | 568 | places/driftmoor/gilded_trinket          |
| to_rooming_house       | 926 | 780 | places/driftmoor/weary_traveler          |

---

## Boundaries

### Town Perimeter — Settled Ground

- **type:** conditional
- **blocks:** none
- **effect:** beyond this line is wilderness; shadowbeast sightings increase sharply
- **vertices:** (0,0) (1625,0) (1625,1462) (0,1462)

### Greywater River — North Bank Crossing

- **type:** physical
- **blocks:** land_creature
- **effect:** impassable except at bridge crossing (1267,1137); swimming possible but cold and fast
- **vertices:** (260,1072) (1625,1072) (1625,1202) (1267,1202) (260,1170)

---
