# GEOMETRY.md — Driftmoor Town

## Scene

- **name:** Driftmoor Town
- **place_path:** places/driftmoor
- **z_level:** 16.25
- **width:** 812.5
- **height:** 731.25
- **origin:** 8450.0, 7800.0, 16.25

Notes: Local coordinates origin at southwest corner (Fisher Folk
quarter). X increases east, Y increases north. Coordinates are in
feet. The scene spans about 812.5 by 731.25 feet, including the
built town, surrounding roads, and harbor. The Greywater River
forms the northern boundary, curving from northwest to northeast.
The harbor and docks lie to the west. The town sits 16.25 feet above
sea level on average; the church rise is slightly higher at about
26 feet.

Building centers are given as landmarks. Each named building with
spatial complexity has its own GEOMETRY.md. Simple single-room
buildings do not.

---

## Landmarks

| name                  | x     | y     |
|-----------------------|-------|-------|
| town_center           | 406 | 341 |
| well                  | 491.25 | 336.25 |
| greywater_bend        | 341 | 552.5 |
| bridge_crossing       | 633.5 | 568.5 |
| bridge_south_archway  | 635   | 536   |
| bridge_north_archway  | 635   | 600   |
| harbor_pier_north     | 89  | 503.5 |
| harbor_pier_south     | 73  | 406 |
| road_to_obelisk       | 284 | 698.5 |
| road_to_old_mill      | 796 | 373.5 |
| road_to_stonehearth   | 438.5 | 16  |
| graveyard_center      | 430.5 | 674 |
| garden_center         | 438.5 | 121.5  |
| stable_center         | 633.5 | 97.5  |
| corral_center         | 723 | 113.5  |
| fisherfolk_center     | 146  | 65  |

---

## Zones

Zone order matters — first match wins in zone_at(). Zones are **per-building
footprints** (one zone per structure on the town map, centred on the building's
landmark), followed by the open ground and water they sit in, then EXTERIOR
last. So the more specific a zone, the earlier it is listed: a point inside the
tavern resolves to TAVERN, not MARKET_SQUARE or TOWN_COMMON. ``render_z`` only
affects draw stacking (higher = on top): buildings/docks (5) over the open
square/garden (4) over water (3) over the common ground (2) over EXTERIOR (0).

| name              | render_z | auto_wall | vertices                                                    |
|-------------------|----------|-----------|-------------------------------------------------------------|
| GRAVEYARD        | 5.0      |           | (348,630) (513,630) (513,718) (348,718) |
| CHURCH           | 5.0      |           | (520.5,630) (632.5,630) (632.5,718) (520.5,718) |
| DUSTCLOAKS_CURIOS | 5.0     |           | (212.5,600.5) (290.5,600.5) (290.5,682.5) (212.5,682.5) |
| MAYORS_HALL      | 5.0      |           | (655,423) (710,423) (710,519) (655,519) |
| MIDWIFE          | 5.0      |           | (712,475.5) (750,475.5) (750,531.5) (712,531.5) |
| TANNERY          | 5.0      |           | (323,466.5) (375,466.5) (375,524.5) (323,524.5) |
| CARPENTER        | 5.0      |           | (279.5,443) (321.5,443) (321.5,499) (279.5,499) |
| TAILOR           | 5.0      |           | (384,447) (444,447) (444,495) (384,495) |
| WEAVER           | 5.0      |           | (451.5,447) (506.5,447) (506.5,495) (451.5,495) |
| COOPER           | 5.0      |           | (265,388) (320,388) (320,440) (265,440) |
| COBBLER          | 5.0      |           | (352,364) (395,364) (395,416) (352,416) |
| BARBER           | 5.0      |           | (397.5,364) (430.5,364) (430.5,416) (397.5,416) |
| ROOMING_HOUSE    | 5.0      |           | (435,361) (491,361) (491,419) (435,419) |
| APOTHECARY       | 5.0      |           | (494,364) (546,364) (546,416) (494,416) |
| SCHOOLHOUSE      | 5.0      |           | (642.5,343.5) (722.5,343.5) (722.5,403.5) (642.5,403.5) |
| WATCHTOWER       | 5.0      |           | (300,332.5) (333,332.5) (333,365.5) (300,365.5) |
| WELL             | 5.0      |           | (490,340) (495,340) (495,335) (490,335) |
| FISHMONGER       | 5.0      |           | (198.5,313.5) (256.5,313.5) (256.5,368.5) (198.5,368.5) |
| BAKERY           | 5.0      |           | (313,252) (369,252) (369,316) (313,316) |
| PAWN_SHOP        | 5.0      |           | (371.5,252) (424.5,252) (424.5,316) (371.5,316) |
| TAVERN           | 5.0      |           | (427.5,252) (482.5,252) (482.5,316) (427.5,316) |
| MERCANTILE       | 5.0      |           | (487,252) (553,252) (553,316) (487,316) |
| ELYSSA_COTTAGE   | 5.0      |           | (688,227) (758,227) (758,309) (688,309) |
| GENERAL_STORE    | 5.0      |           | (235,82.5) (317,82.5) (317,177.5) (235,177.5) |
| FORGE            | 5.0      |           | (602.5,122) (664.5,122) (664.5,170) (602.5,170) |
| STABLE           | 5.0      |           | (602.5,75.5) (664.5,75.5) (664.5,119.5) (602.5,119.5) |
| CORRAL           | 5.0      |   false    | (678,69.5) (768,69.5) (768,157.5) (678,157.5) |
| FISHERFOLK       | 5.0      |           | (150,375) (242.5,375) (242.5,425) (150,425) |
| BRIDGE           | 4.5      |   false   | (617.5,525) (652.5,525) (652.5,607.5) (617.5,607.5) |
| GARDEN           | 4.0      |   false   | (333.5,75) (545,75) (545,169) (333.5,169) |
| DOCKS            | 5.0      |           | (150,350) (25,350) (25,425) (150,425) |
| AZURE_SEA        | 0.0      |           | (0,731) (150,731) (150,0) (0,0) |
| GREYWATER_RIVER  | 0.0      |           | (150,536) (812.5,536) (812.5,600) (150,600) |
| NORTH_BANK       | 2.0      |           | (150,600) (812.5,600) (812.5,731) (150,731) |
| TOWN_COMMON      | 2.0      | false     | (150,0) (812.5,0) (812.5,536) (150,536) |
---

## Impassable

| description                      | vertices                                          |
|----------------------------------|---------------------------------------------------|
| Greywater River (west of bridge) | (130,536) (617.5,536) (617.5,590) (130,585)     |
| Greywater River (east of bridge) | (652.5,536) (812.5,536) (812.5,600) (652.5,600)   |
| Harbor water                     | (0,280) (125,280) (125,536) (0,536)             |
| Azure Sea                        | (0,536) (150,536) (150,731) (0,731)           |

---

## Connections

| name                   | x     | y     | destination                              |
|------------------------|-------|-------|------------------------------------------|
| to_region              | 406 | 365.5 | places/                                  |
| to_harbor_water        | 48.5  | 438.5 | places/azure_sea                         |
| to_dustcloaks_curios   | 251.5 | 641.5 | places/driftmoor/dustcloaks_curios       |
| to_church              | 576.5 | 650 | places/driftmoor/beacon_church           |
| to_graveyard           | 430.5 | 674 | places/driftmoor/graveyard               |
| to_mayors_hall         | 682.5 | 471 | places/driftmoor/mayors_hall             |
| to_tavern              | 455 | 284 | places/driftmoor/broken_lantern          |
| to_salt_and_iron       | 520 | 284 | places/driftmoor/salt_and_iron           |
| to_forge               | 633.5 | 146  | places/driftmoor/forge                   |
| to_stable              | 633.5 | 97.5  | places/driftmoor/stables                 |
| to_corral              | 723 | 113.5  | places/driftmoor/corral                  |
| to_elyssa_cottage      | 723 | 268 | places/driftmoor/elyssa_cottage           |
| to_apothecary          | 520 | 390 | places/driftmoor/bitter_remedy           |
| to_gilded_trinket      | 398 | 284 | places/driftmoor/gilded_trinket          |
| to_rooming_house       | 463 | 390 | places/driftmoor/weary_traveler          |
| to_bakery              | 341 | 284 | places/driftmoor/bakery                  |
| to_cobbler             | 373.5 | 390 | places/driftmoor/cobblers_shop           |
| to_barber              | 414 | 390 | places/driftmoor/rusty_razor             |
| to_cooper              | 292.5 | 414 | places/driftmoor/coopers_shed            |
| to_carpenter           | 300.5 | 471 | places/driftmoor/carpenters_workshop     |
| to_weaver              | 479 | 471 | places/driftmoor/weavers_cottage         |
| to_tailor              | 414 | 471 | places/driftmoor/tailors_shop            |
| to_tannery             | 349 | 495.5 | places/driftmoor/tannery                 |
| to_fishmonger          | 227.5 | 341 | places/driftmoor/fishmongers_shack       |
| to_fisherfolk          | 196 | 400 | places/driftmoor/fisherfolk              |
| to_schoolhouse         | 682.5 | 373.5 | places/driftmoor/schoolhouse            |
| to_midwife             | 731 | 503.5 | places/driftmoor/midwifes_home         |
| to_watchtower          | 316.5 | 349 | places/driftmoor/watchtower              |
| to_general_store       | 276 | 130 | places/driftmoor/general_store           |

---

## Boundaries

### Town Perimeter — Settled Ground

- **type:** conditional
- **blocks:** none
- **effect:** beyond this line is wilderness; shadowbeast sightings increase sharply
- **vertices:** (0,0) (812.5,0) (812.5,731) (0,731)

---
