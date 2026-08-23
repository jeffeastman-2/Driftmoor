# GEOMETRY.md — The Sleeping City of Nhal'Zirath

## Scene
- **name:** The Sleeping City of Nhal'Zirath
- **place_path:** places/obelisk_reach/echoing_caverns/sleeping_city
- **z_level:** -45
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
| Broken Lift | true | (51,136,-45) (69,136,-45) (69,157,-20) (51,157,-20) |
| Gate of Two Peoples | true | (39,118,-45) (81,118,-45) (81,136,-45) (39,136,-45) |
| Avenue of Sleeping Blades | true | (41,35,-45) (79,35,-45) (79,118,-45) (41,118,-45) |
| Chainworks | true | (27,51,-50) (41,51,-45) (41,106,-45) (27,106,-50) |
| Sleeping District | true | (79,91,-45) (103,91,-45) (103,108,-45) (79,108,-45) |
| Mirror Approach | true | (79,35,-45) (94,35,-45) (94,59,-45) (79,59,-45) |
| Hall of Unchosen Queens | true | (31,21,-50) (89,21,-50) (96,29,-50) (89,37,-45) (31,37,-45) (24,29,-50) |
| Crypt of Seven Chains | true | (43,3,-55) (77,3,-55) (84,21,-50) (36,21,-50) |

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
| snapped_hoist_chain | 55 | 147 | -30 | Snapped hoist chain |
| counterweight_brake | 65 | 139 | -42 | Counterweight brake |
| dwarven_gate_wheel | 47 | 126 | -42 | Dwarven gate wheel |
| elven_resonance_bells | 73 | 126 | -39 | Elven resonance bells |
| sleeping_blade_cocoons | 47 | 94 | -42 | Sleeping blade cocoons |
| suspended_drow_mage | 74 | 94 | -42 | Suspended drow mage |
| rotunda_mosaic | 60 | 77 | -45 | Shattered civic mosaic |
| chain_control_drum | 33 | 79 | -47 | Chain control drum |
| maintenance_tablet | 34 | 58 | -46 | Maintenance tablet |
| district_web_seal | 91 | 99 | -42 | District web-seal |
| future_mirrors | 86 | 47 | -42 | Future mirrors |
| eight_future_mirrors | 60 | 29 | -47 | Eight dark mirrors |
| seventh_chain_key | 60 | 25 | -48 | Seventh-chain key |
| living_lock_depression | 60 | 7 | -54 | Living-lock depression |
| stone_station | 48 | 13 | -52 | Stone station |
| chain_station | 72 | 13 | -52 | Chain station |
| witness_station | 51 | 6 | -53 | Witness station |
| choice_station | 69 | 6 | -53 | Choice station |
| vaelithras_bier | 60 | 10 | -53 | Vaelithra's black bier |
| broken_seventh_chain | 68 | 12 | -51 | Broken seventh chain |

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
