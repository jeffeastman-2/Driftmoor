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
| upper_lift_mouth | 60 | 153 |
| lift_cage | 60 | 142 |
| gate_threshold | 60 | 126 |
| avenue_threshold | 60 | 116 |
| chainworks_upper_door | 41 | 103 |
| sleeping_district_seal | 79 | 103 |
| civic_rotunda | 60 | 77 |
| chainworks_lower_door | 41 | 55 |
| mirror_approach_door | 79 | 55 |
| hall_main_threshold | 60 | 35 |
| hall_mirror_threshold | 78 | 30 |
| crypt_threshold | 60 | 21 |
| black_bier | 60 | 10 |

---

## Walls
- **auto_wall:** true

---

## Zones

| name | auto_wall | vertices |
|---|---|---|
| Broken Lift | true | (51,136,-95) (69,136,-95) (69,157,-70) (51,157,-70) |
| Gate of Two Peoples | true | (39,118,-95) (81,118,-95) (81,136,-95) (39,136,-95) |
| Avenue of Sleeping Blades | true | (41,35,-95) (79,35,-95) (79,118,-95) (41,118,-95) |
| Chainworks | true | (27,51,-100) (41,51,-95) (41,106,-95) (27,106,-100) |
| Sleeping District | true | (79,91,-95) (103,91,-95) (103,108,-95) (79,108,-95) |
| Mirror Approach | true | (79,35,-95) (94,35,-95) (94,59,-95) (79,59,-95) |
| Hall of Unchosen Queens | true | (31,21,-100) (89,21,-100) (96,29,-100) (89,37,-95) (31,37,-95) (24,29,-100) |
| Crypt of Seven Chains | true | (43,3,-105) (77,3,-105) (84,21,-100) (36,21,-100) |

---

## Impassable

| description | vertices |
|---|---|
| Collapsed civic rotunda | (49,66) (55,61) (66,62) (72,69) (70,82) (64,89) (53,87) (47,78) |
| Web-sealed deeper city | (99,91) (106,91) (106,108) (99,108) |
| Broken upper lift machinery | (51,153) (69,153) (69,160) (51,160) |

---

## Items

| id | x | y | z | label |
|---|---|---|---|---|
| snapped_hoist_chain | 55 | 147 | -80 | Snapped hoist chain |
| counterweight_brake | 65 | 139 | -92 | Counterweight brake |
| dwarven_gate_wheel | 47 | 126 | -92 | Dwarven gate wheel |
| elven_resonance_bells | 73 | 126 | -89 | Elven resonance bells |
| sleeping_blade_cocoons | 47 | 94 | -92 | Sleeping blade cocoons |
| suspended_drow_mage | 74 | 94 | -92 | Suspended drow mage |
| rotunda_mosaic | 60 | 77 | -95 | Shattered civic mosaic |
| chain_control_drum | 33 | 79 | -97 | Chain control drum |
| maintenance_tablet | 34 | 58 | -96 | Maintenance tablet |
| district_web_seal | 91 | 99 | -92 | District web-seal |
| future_mirrors | 86 | 47 | -92 | Future mirrors |
| eight_future_mirrors | 60 | 29 | -97 | Eight dark mirrors |
| seventh_chain_key | 60 | 25 | -98 | Seventh-chain key |
| living_lock_depression | 60 | 7 | -104 | Living-lock depression |
| stone_station | 48 | 13 | -102 | Stone station |
| chain_station | 72 | 13 | -102 | Chain station |
| witness_station | 51 | 6 | -103 | Witness station |
| choice_station | 69 | 6 | -103 | Choice station |
| vaelithras_bier | 60 | 10 | -103 | Vaelithra's black bier |
| broken_seventh_chain | 68 | 12 | -101 | Broken seventh chain |

---

## Ambient Visibility
The city has no natural light. Temporal webbing sheds dim violet light near
sleepers and seals; beyond it, carried light or darkvision is required.

- **default:** 30

---

## Connections

| name | x | y | destination |
|---|---|---|---|
| upper_lift_mouth | 60 | 157 | places/obelisk_reach/echoing_caverns |

---

## Boundaries

### Temporal Web-Sleep
- **type:** magical
- **blocks:** movement, sound
- **effect:** translucent webbing suspends creatures and objects outside ordinary time; cutting or dispelling a strand may wake its occupant and propagate a harmonic disturbance to nearby cocoons
- **vertices:** (43,38) (77,38) (77,115) (43,115)

### Crypt Binding
- **type:** magical
- **blocks:** planar travel
- **effect:** while four or more chains remain anchored, Vaelithra cannot leave the bier and teleportation across the crypt boundary fails; two connected chains are presently frayed rather than sound
- **vertices:** (36,3) (84,3) (84,22) (36,22)
