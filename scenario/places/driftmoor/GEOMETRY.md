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
| town_center           | 812.5 | 682.5 |
| well                  | 1007.5 | 698.75 |
| watchtower            | 633.75 | 698.75 |
| greywater_bend        | 682.5 | 1105.0 |
| bridge_crossing       | 1267.5 | 1137.5 |
| harbor_pier_north     | 178.75  | 1007.5 |
| harbor_pier_south     | 146.25  | 812.5 |
| road_to_obelisk       | 568.75 | 1397.5 |
| road_to_old_mill      | 1592.5 | 747.5 |
| road_to_stonehearth   | 877.5 | 32.5  |
| dustcloaks_house      | 503.75 | 1283.75 |
| graveyard_center      | 861.25 | 1348.75 |
| church_center         | 1153.75 | 1300.0 |
| mayors_hall_center    | 1365.0 | 942.5 |
| midwife_center        | 1462.5 | 1007.5 |
| schoolhouse_center    | 1365.0 | 747.5 |
| elyssa_house_center   | 1446.25 | 536.25 |
| tannery_center        | 698.75 | 991.25 |
| carpenter_center      | 601.25 | 942.5 |
| cooper_center         | 585.0 | 828.75 |
| tailor_center         | 828.75 | 942.5 |
| weaver_center         | 958.75 | 942.5 |
| cobbler_center        | 747.5 | 780.0 |
| barber_center         | 828.75 | 780.0 |
| rooming_house_center  | 926.25 | 780.0 |
| apothecary_center     | 1040.0 | 780.0 |
| fishmonger_center     | 455.0 | 682.5 |
| bakery_center         | 682.5 | 568.75 |
| pawn_shop_center      | 796.25 | 568.75 |
| tavern_center         | 910.0 | 568.75 |
| mercantile_center     | 1040.0 | 568.75 |
| general_store_center  | 552.5 | 260.0  |
| garden_center         | 877.5 | 243.75  |
| forge_center          | 1267.5 | 292.5  |
| stable_center         | 1267.5 | 195.0  |
| corral_center         | 1446.25 | 227.5  |
| fisherfolk_center     | 292.5  | 130.0  |

---

## Zones

Zone order matters — first match wins in zone_at(). EXTERIOR is last.
Sub-zones (individual buildings) appear before their district zone.

| name              | render_z | vertices                                                    |
|-------------------|----------|-------------------------------------------------------------|
| GREYWATER_RIVER   | 6.5        | (260.0,1072.5) (1625.0,1072.5) (1625.0,1202.5) (1267.5,1202.5) (260.0,1170.0)            |
| GRAVEYARD         | 6.5        | (698.75,1218.75) (1023.75,1218.75) (1023.75,1430.0) (698.75,1430.0)                     |
| HARBOR_WATER      | 6.5        | (0.0,650.0) (243.75,650.0) (243.75,1105.0) (0.0,1105.0)                           |
| DOCKS             | 6.5        | (97.5,715.0) (260.0,715.0) (260.0,1072.5) (97.5,1072.5)                         |
| NORTH_BANK        | 3.25        | (260.0,1105.0) (1625.0,1105.0) (1625.0,1462.5) (260.0,1462.5)                       |
| HARBOR_DISTRICT   | 3.25        | (0.0,325.0) (422.5,325.0) (422.5,1105.0) (0.0,1105.0)                         |
| CRAFTSMEN_QUARTER | 3.25        | (422.5,780.0) (715.0,780.0) (715.0,1072.5) (422.5,1072.5)                     |
| VILLAGE_CENTER    | 3.25        | (422.5,617.5) (1365.0,617.5) (1365.0,1072.5) (422.5,1072.5)                     |
| SOUTH_ROW         | 3.25        | (617.5,503.75) (1397.5,503.75) (1397.5,650.0) (617.5,650.0)                     |
| EAST_QUARTER      | 3.25        | (1267.5,325.0) (1625.0,325.0) (1625.0,1072.5) (1267.5,1072.5)                     |
| SOUTH_QUARTER     | 3.25        | (422.5,65.0) (1625.0,65.0) (1625.0,503.75) (422.5,503.75)                       |
| FISHERFOLK        | 3.25        | (0.0,0.0) (422.5,0.0) (422.5,325.0) (0.0,325.0)                             |
| EXTERIOR          | 0.0        | (0.0,0.0) (1625.0,0.0) (1625.0,1462.5) (0.0,1462.5)                             |

---

## Impassable

| description           | vertices                                                    |
|-----------------------|-------------------------------------------------------------|
| Greywater River       | (260.0,1072.5) (1625.0,1072.5) (1625.0,1202.5) (1267.5,1202.5) (260.0,1170.0)            |
| Harbor open water     | (0.0,650.0) (178.75,650.0) (178.75,1105.0) (0.0,1105.0)                           |
| Graveyard wall        | (698.75,1218.75) (1023.75,1218.75) (1023.75,1430.0) (698.75,1430.0)                     |

---

## Connections

| name                   | x     | y     | destination                              |
|------------------------|-------|-------|------------------------------------------|
| to_region              | 812.5 | 731.25 | places/                                  |
| to_obelisk_road        | 568.75 | 1446.25 | places/obelisk_reach                     |
| to_old_mill_road       | 1608.75 | 747.5 | places/greywater_river/old_mill          |
| to_stonehearth_road    | 877.5 | 16.25   | places/plains_of_stonehearth             |
| to_mistwood_trail      | 1608.75 | 1235.0 | places/mistwood_hills                    |
| to_harbor_water        | 97.5  | 877.5 | places/azure_sea                         |
| to_dustcloaks_house    | 503.75 | 1283.75 | places/driftmoor/dustcloaks_curios       |
| to_church              | 1153.75 | 1300.0 | places/driftmoor/beacon_church           |
| to_mayors_hall         | 1365.0 | 942.5 | places/driftmoor/mayors_hall             |
| to_broken_lantern      | 910.0 | 568.75 | places/driftmoor/broken_lantern          |
| to_salt_and_iron       | 1040.0 | 568.75 | places/driftmoor/salt_and_iron           |
| to_forge               | 1267.5 | 292.5  | places/driftmoor/ironhoof_forge          |
| to_elyssa_house        | 1446.25 | 536.25 | places/driftmoor/elyssa_residence        |
| to_apothecary          | 1040.0 | 780.0 | places/driftmoor/bitter_remedy           |
| to_gilded_trinket      | 796.25 | 568.75 | places/driftmoor/gilded_trinket          |
| to_rooming_house       | 926.25 | 780.0 | places/driftmoor/weary_traveler          |

---

## Boundaries

### Town Perimeter — Settled Ground

- **type:** conditional
- **blocks:** none
- **effect:** beyond this line is wilderness; shadowbeast sightings increase sharply
- **vertices:** (0.0,0.0) (1625.0,0.0) (1625.0,1462.5) (0.0,1462.5)

### Greywater River — North Bank Crossing

- **type:** physical
- **blocks:** land_creature
- **effect:** impassable except at bridge crossing (1267.5, 1137.5); swimming possible but cold and fast
- **vertices:** (260.0,1072.5) (1625.0,1072.5) (1625.0,1202.5) (1267.5,1202.5) (260.0,1170.0)

---

## Starting Positions

| character  | x     | y     | zone            |
|------------|-------|-------|-----------------|
| thorgrim   | 1267.5 | 292.5  | SOUTH_QUARTER   |
| kaelin     | 910.0 | 568.75 | SOUTH_ROW       |
| seraphina  | 796.25 | 568.75 | SOUTH_ROW       |
| lilar      | 1267.5 | 942.5 | EAST_QUARTER    |
| aeliana    | 812.5 | 682.5 | VILLAGE_CENTER  |