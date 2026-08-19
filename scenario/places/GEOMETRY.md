# GEOMETRY.md — The Region Around Driftmoor

## Scene

- **name:** The Region Around Driftmoor
- **place_path:** places/
- **z_level:** 0.0
- **width:** 126750.0
- **height:** 169000.0
- **origin:** 0.0, 0.0, 0.0

Notes: World coordinate origin at southwest corner of regional map.
X increases east, Y increases north. Sea level = 0.0. All child
place origins are expressed in these world coordinates. The regional
mapped land is roughly 126.75km west-to-east by 169km south-to-north.
Its outline follows the hand-drawn regional map rather than a square survey
grid. Driftmoor town sits at approximately
(29575,27462) — on the coast where the Greywater meets the Azure Sea.
The Obelisk Reach is ~105.62km north-northwest of town.

---

## Landmarks

| name | x | y | z | label | destination |
|---|---|---|---|---|---|
| old_mill | 57037 | 45418 | 0 | Old Mill | places/greywater_river/old_mill |

## Zones

| name | render_z | auto_wall | vertices |
|---|---|---|---|
| MISTWOOD_FOREST | 20 | false | (23420,37697) (25940,60167) (23820,86079) (20160,107000) (44104,127083) (46627,146999) (37562,166823) (126562,168637) (124338,89376) (100081,84100) (79706,80622) (62701,75180) (40219,46471) |
| FARMS_AND_FIELDS | 20 | false | (59449,41521) (66864,57662) (98208,58024) (98912,39053) (73264,23510) (48118,20208) (42420,35170) |
| WESTERN_CLIFFS | 20 | false | (17642,69089) (19452,93163) (15560,111908) (8964,128085) (-844,130605) (9373,109973) (12675,92950) |
| HARBOR | 20 | false | (19429,26277) (25150,24776) (24082,34555) (20132,32272) |
| DRIFTMOOR_TOWN | 10 | false | (25202,25044) (38527,29057) (35134,39584) (24174,35012) |
| AZURE_SEA | 10 | false | (0,0) (20434,379) (25202,25044) (38527,29057) (24174,35012) (16900,73937) (9399,110064) (-359,130155) (0,169000) |
| GREYWATER_VALLEY | 10 | false | (35134,39584) (44362,47531) (62318,67599) (78911,77311) (103176,78008) (124391,87529) (124587,68070) (90530,59646) (64741,48899) (48587,33743) (38527,29057) |
| MISTWOOD_HILLS | 10 | false | (16900,73937) (9399,110064) (29575,116187) (42250,128862) (44826,146410) (32021,167358) (126750,169000) (124391,87529) (103176,78008) (78911,77311) (62318,67599) (44362,47531) (35134,39584) (24174,35012) |
| OBELISK_REACH | 10 | false | (9399,110064) (-359,130155) (0,169000) (32021,167358) (44826,146410) (42250,128862) (29575,116187) |
| PLAINS_OF_STONEHEARTH | 10 | false | (20434,379) (126750,0) (124587,68070) (90530,59646) (64741,48899) (48587,33743) (38527,29057) (25202,25044) |
| EXTERIOR | 0 | false | (0,0) (126750,0) (126750,169000) (0,169000) |

## Walls

- **auto_wall:** false

Regional face edges are map boundaries, not movement-blocking walls.

## Impassable

| description | vertices |
|---|---|

## Connections

| name | x | y | destination |
|---|---|---|---|
| to_driftmoor | 30631 | 28518 | places/driftmoor |
| to_azure_sea | 9506 | 46475 | places/azure_sea |
| to_greywater_valley | 57037 | 45418 | places/greywater_river |
| to_mistwood_hills | 68656 | 97175 | places/mistwood_hills |
| to_obelisk_reach | 36968 | 135200 | places/obelisk_reach |
| to_plains | 105625 | 21125 | places/plains_of_stonehearth |

## Routes

| name | kind | color | width | vertices |
|---|---|---|---|---|
| Greywater River | river | #587f91 | 1800 | (124528,72271) (117293,72184) (110853,75254) (102969,74512) (97758,71469) (94728,64791) (88539,62038) (81210,63433) (74968,65735) (65562,64588) (58991,59981) (57875,51565) (56844,44256) (51168,41800) (46764,43369) (41309,40982) (38314,36926) (32475,35067) (28146,32572) (24485,30489) |
| Gold Run | river | #6f98aa | 900 | (118658,109472) (112820,101676) (112816,94057) (110248,87095) (103644,84896) (99277,80153) (98255,71310) |
| Blackwater River | river | #486b79 | 1100 | (107306,132269) (97522,120333) (94276,108345) (93513,96062) (88653,84552) (81120,74288) (73789,66972) |
| Fanghorn | river | #668d9c | 750 | (26859,128425) (37250,114826) (49934,109031) (61940,110653) (68482,101743) (77889,95922) (83266,77477) |
| Misty | river | #82a9b5 | 700 | (84546,157231) (86393,137784) (76279,122750) (79261,109638) (77772,95684) |
| Obelisk Trail | trail | #6d5639 | 650 | (31669,37652) (32743,50700) (30631,76050) (27462,101400) (23887,122234) (8310,145343) |
| Greywater Road | road | #765f42 | 900 | (36243,33645) (42605,37167) (45865,38357) (58445,41698) (62318,59150) (72310,62835) (87024,58968) (95059,61434) (99590,69087) (108595,71484) (124606,69191) |
| Stonehearth Road | road | #765f42 | 900 | (34741,27741) (43750,26922) (47189,18446) (71696,21696) (91178,379) |
| Mistwood Trail | trail | #6d5639 | 650 | (50499,39333) (50071,45303) (48592,60156) (57662,75329) (55023,87013) (59345,101080) |
| Coast Path | trail | #6d5639 | 550 | (23302,1400) (26336,15888) (27215,24159) (24155,46026) (18895,74028) |

## Boundaries

No regional boundaries are authored outside the editable region and sub-zone layers.

## Map Styles

| target | fill |
|---|---|
| AZURE_SEA | #7897a3 |
| DRIFTMOOR_TOWN | #9b7658 |
| GREYWATER_VALLEY | #87976b |
| MISTWOOD_HILLS | #657958 |
| OBELISK_REACH | #8c8175 |
| PLAINS_OF_STONEHEARTH | #b5a86e |
| MISTWOOD_FOREST | #4f6b48 |
| FARMS_AND_FIELDS | #bca96a |
| WESTERN_CLIFFS | #746f68 |
| HARBOR | #7897a3 |
