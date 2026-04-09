# GEOMETRY.md — Driftmoor Town

## Scene

- **name:** Driftmoor Town
- **place_path:** places/driftmoor
- **z_level:** 5.0
- **width:** 500.0
- **height:** 450.0
- **origin:** 2600.0, 2400.0, 5.0

Notes: Local coordinates origin at southwest corner (Fisher Folk
quarter). X increases east, Y increases north. Scale: ~250m of
built town plus surrounding roads and harbor. The Greywater River
forms the northern boundary, curving from northwest to northeast.
The harbor and docks lie to the west. Streets are 5-10m wide.
Buildings are 15-25m footprints. The town sits 5m above sea level
on average; the church rise is slightly higher at ~8m.

Building centers are given as landmarks. Each named building with
spatial complexity has its own GEOMETRY.md. Simple single-room
buildings do not.

---

## Landmarks

| name                  | x     | y     |
|-----------------------|-------|-------|
| town_center           | 250.0 | 210.0 |
| well                  | 310.0 | 215.0 |
| watchtower            | 195.0 | 215.0 |
| greywater_bend        | 210.0 | 340.0 |
| bridge_crossing       | 390.0 | 350.0 |
| harbor_pier_north     | 55.0  | 310.0 |
| harbor_pier_south     | 45.0  | 250.0 |
| road_to_obelisk       | 175.0 | 430.0 |
| road_to_old_mill      | 490.0 | 230.0 |
| road_to_stonehearth   | 270.0 | 10.0  |
| dustcloaks_house      | 155.0 | 395.0 |
| graveyard_center      | 265.0 | 415.0 |
| church_center         | 355.0 | 400.0 |
| mayors_hall_center    | 420.0 | 290.0 |
| midwife_center        | 450.0 | 310.0 |
| schoolhouse_center    | 420.0 | 230.0 |
| elyssa_house_center   | 445.0 | 165.0 |
| tannery_center        | 215.0 | 305.0 |
| carpenter_center      | 185.0 | 290.0 |
| cooper_center         | 180.0 | 255.0 |
| tailor_center         | 255.0 | 290.0 |
| weaver_center         | 295.0 | 290.0 |
| cobbler_center        | 230.0 | 240.0 |
| barber_center         | 255.0 | 240.0 |
| rooming_house_center  | 285.0 | 240.0 |
| apothecary_center     | 320.0 | 240.0 |
| fishmonger_center     | 140.0 | 210.0 |
| bakery_center         | 210.0 | 175.0 |
| pawn_shop_center      | 245.0 | 175.0 |
| tavern_center         | 280.0 | 175.0 |
| mercantile_center     | 320.0 | 175.0 |
| general_store_center  | 170.0 | 80.0  |
| garden_center         | 270.0 | 75.0  |
| forge_center          | 390.0 | 90.0  |
| stable_center         | 390.0 | 60.0  |
| corral_center         | 445.0 | 70.0  |
| fisherfolk_center     | 90.0  | 40.0  |

---

## Zones

Zone order matters — first match wins in zone_at(). EXTERIOR is last.
Sub-zones (individual buildings) appear before their district zone.

| name              | render_z | vertices                                                    |
|-------------------|----------|-------------------------------------------------------------|
| GREYWATER_RIVER   | 2        | (80,330) (500,330) (500,370) (390,370) (80,360)            |
| GRAVEYARD         | 2        | (215,375) (315,375) (315,440) (215,440)                     |
| HARBOR_WATER      | 2        | (0,200) (75,200) (75,340) (0,340)                           |
| DOCKS             | 2        | (30,220) (80,220) (80,330) (30,330)                         |
| NORTH_BANK        | 1        | (80,340) (500,340) (500,450) (80,450)                       |
| HARBOR_DISTRICT   | 1        | (0,100) (130,100) (130,340) (0,340)                         |
| CRAFTSMEN_QUARTER | 1        | (130,240) (220,240) (220,330) (130,330)                     |
| VILLAGE_CENTER    | 1        | (130,190) (420,190) (420,330) (130,330)                     |
| SOUTH_ROW         | 1        | (190,155) (430,155) (430,200) (190,200)                     |
| EAST_QUARTER      | 1        | (390,100) (500,100) (500,330) (390,330)                     |
| SOUTH_QUARTER     | 1        | (130,20) (500,20) (500,155) (130,155)                       |
| FISHERFOLK        | 1        | (0,0) (130,0) (130,100) (0,100)                             |
| EXTERIOR          | 0        | (0,0) (500,0) (500,450) (0,450)                             |

---

## Impassable

| description           | vertices                                                    |
|-----------------------|-------------------------------------------------------------|
| Greywater River       | (80,330) (500,330) (500,370) (390,370) (80,360)            |
| Harbor open water     | (0,200) (55,200) (55,340) (0,340)                           |
| Graveyard wall        | (215,375) (315,375) (315,440) (215,440)                     |

---

## Connections

| name                   | x     | y     | destination                              |
|------------------------|-------|-------|------------------------------------------|
| to_region              | 250.0 | 225.0 | places/                                  |
| to_obelisk_road        | 175.0 | 445.0 | places/obelisk_reach                     |
| to_old_mill_road       | 495.0 | 230.0 | places/greywater_river/old_mill          |
| to_stonehearth_road    | 270.0 | 5.0   | places/plains_of_stonehearth             |
| to_mistwood_trail      | 495.0 | 380.0 | places/mistwood_hills                    |
| to_harbor_water        | 30.0  | 270.0 | places/azure_sea                         |
| to_dustcloaks_house    | 155.0 | 395.0 | places/driftmoor/dustcloaks_curios       |
| to_church              | 355.0 | 400.0 | places/driftmoor/beacon_church           |
| to_mayors_hall         | 420.0 | 290.0 | places/driftmoor/mayors_hall             |
| to_broken_lantern      | 280.0 | 175.0 | places/driftmoor/broken_lantern          |
| to_salt_and_iron       | 320.0 | 175.0 | places/driftmoor/salt_and_iron           |
| to_forge               | 390.0 | 90.0  | places/driftmoor/ironhoof_forge          |
| to_elyssa_house        | 445.0 | 165.0 | places/driftmoor/elyssa_residence        |
| to_apothecary          | 320.0 | 240.0 | places/driftmoor/bitter_remedy           |
| to_gilded_trinket      | 245.0 | 175.0 | places/driftmoor/gilded_trinket          |
| to_rooming_house       | 285.0 | 240.0 | places/driftmoor/weary_traveler          |

---

## Boundaries

### Town Perimeter — Settled Ground

- **type:** conditional
- **blocks:** none
- **effect:** beyond this line is wilderness; shadowbeast sightings increase sharply
- **vertices:** (0,0) (500,0) (500,450) (0,450)

### Greywater River — North Bank Crossing

- **type:** physical
- **blocks:** land_creature
- **effect:** impassable except at bridge crossing (390, 350); swimming possible but cold and fast
- **vertices:** (80,330) (500,330) (500,370) (390,370) (80,360)

---

## Starting Positions

| character  | x     | y     | zone            |
|------------|-------|-------|-----------------|
| thorgrim   | 390.0 | 90.0  | SOUTH_QUARTER   |
| kaelin     | 280.0 | 175.0 | SOUTH_ROW       |
| seraphina  | 245.0 | 175.0 | SOUTH_ROW       |
| lilar      | 390.0 | 290.0 | EAST_QUARTER    |
| aeliana    | 250.0 | 210.0 | VILLAGE_CENTER  |