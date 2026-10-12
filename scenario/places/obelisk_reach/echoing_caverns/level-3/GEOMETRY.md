# GEOMETRY.md — The Sleeping City of Nhal'Zirath

## Scene
- **name:** The Sleeping City of Nhal'Zirath
- **place_path:** places/obelisk_reach/echoing_caverns/sleeping_city
- **z_level:** -90
- **width:** 120
- **height:** 160
- **origin:** 11590, 42945, 180

Notes: Top-down schematic geometry. North is the collapsed cavern approach;
the visible processional axis runs south toward Vaelithra's crypt. Coordinates
are local feet and intentionally preserve the loop and alternate approach shown
in sleeping-city-layout.svg.

---

## Landmarks

| name | x | y |
|---|---|---|
| avenue_threshold | 60 | 151 |
| chainworks_upper_door | 54 | 92 |
| sleeping_district_seal | 68 | 121 |
| civic_rotunda | 60 | 77 |
| chainworks_lower_door | 54 | 59 |
| stairway_threshold | 62 | 37 |

---

## Walls
- **auto_wall:** true

---

## Zones

| name | auto_wall | vertices |
|---|---|---|
| Gate of Two Peoples | true | (53,151,-95) (67,151,-95) (67,160,-95) (53,160,-95) |
| Avenue of Sleeping Blades | true | (54,37,-95) (69,37,-95) (69,62,-95) (79,68,-95) (79,85,-95) (68,90,-95) (67,151,-95) (53,151,-95) (54,90,-95) (45,85,-95) (45,67,-95) (54,61,-95) |
| Chainworks | true | (28,57,-100) (54,57,-98.9011) (54,61,-96.4286) (42,61,-95) (42,90,-95) (54,90,-95) (54,94,-95.9615) (28,94,-100) |
| Sleeping District-1 | true | (67,113,-95) (118,113,-95) (118,130,-95) (67,130,-95) |
| Sleeping District-2 | true | (6,113,-95) (54,113,-95) (54,130,-95) (6,130,-95) |
| Stairway to Royal Precinct | true | (54,13,-95) (69,13,-95) (69,37,-95) (54,37,-95) |

---

## Impassable

| description | vertices |
|---|---|
| Collapsed civic rotunda | (47,67) (55,62) (66,62) (77,69) (76,83) (66,89) (57,89) (47,83) |
| Web-sealed deeper city | (91,44) (117,43) (118,113) (92,113) |

---

## Items

| id | x | y | z | label |
|---|---|---|---|---|
| elven_resonance_bells | 73 | 126 | -89 | Elven resonance bells |
| sleeping_blade_cocoons | 53 | 102 | -92 | Sleeping blade cocoons |
| sleeping_drow_mage | 68 | 98 | -92 | Sleeping drow mage |
| rotunda_mosaic | 60 | 77 | -95 | Shattered civic mosaic |
| chain_control_drum | 33 | 79 | -97 | Chain control drum |
| maintenance_tablet | 31 | 69 | -96 | Maintenance tablet |
| district_web_seal | 79 | 121 | -92 | District web-seal |

---

## Ambient Visibility
The city has no natural light. Temporal webbing sheds dim violet light near
sleepers and seals; beyond it, carried light or darkvision is required.

- **default:** 30

---

## Connections

| name | x | y | destination |
|---|---|---|---|
| gate_of_two_peoples | 60 | 157 | places/obelisk_reach/echoing_caverns/level-2 |

---

## Boundaries

### Temporal Web-Sleep
- **type:** magical
- **blocks:** movement, sound
- **effect:** translucent webbing suspends creatures and objects outside ordinary time; cutting or dispelling a strand may wake its occupant and propagate a harmonic disturbance to nearby cocoons
- **vertices:** (3,37) (120,37) (121,133) (3,133)

