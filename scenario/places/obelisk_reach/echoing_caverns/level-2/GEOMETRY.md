# GEOMETRY.md — The Freight Quarter of the Echoing Caverns

## Scene

- **name:** The Freight Quarter
- **place_path:** places/obelisk_reach/echoing_caverns/level-2
- **z_level:** -55
- **width:** 140
- **height:** 180
- **origin:** 11420.0, 42720.0, -55

Notes: A network of storage and labor chambers carved into the cavern wall.
The Freight Quarter serves as the upper staging area for goods moving deeper
into the caverns. The air smells of damp earth, old grain, and the faint
sulfurous tang of beast pens. Narrow lift shafts connect to levels above and
below.

---

## Landmarks

| name                       | x   | y   |
|----------------------------|-----|-----|
| broken_lift_shaft          | 70 | 165 |
| factor_office_door         | 45 | 145 |
| receiving_floor_arch       | 62 | 157 |
| cold_larder_threshold      | 83 | 99 |
| beast_pens_gate            | 82 | 61 |
| cistern_door               | 34 | 61 |
| gate_of_two_peoples_entrance | 64 | 25 |

---

## Walls

- **auto_wall:** false

The Freight Quarter consists of rough-hewn chambers with occasional iron doors
and gates. The broken lift shaft and gate of two peoples have mechanical
barriers that function; the other chambers connect via open archways.

## Zones

| name | auto_wall | vertices |
|------------------|---------|---------------------------------------------------------------------------------------------------|
| Broken Lift | false | (51,157,-55) (76,157,-55) (76,178,-55) (51,178,-55) |
| Factor's Office | false | (7,116,-55) (45,116,-55) (45,152,-55) (7,152,-55) |
| Fungal Stores | false | (83,121,-55) (121,121,-55) (121,152,-55) (83,152,-55) |
| Receiving Floor | false | (44,45,-55) (82,45,-55) (83,157,-55) (45,157,-55) |
| Freight Guardroom | false | (7,81,-55) (44,81,-55) (44,113,-55) (7,113,-55) |
| Cold Larder | false | (83,84,-55) (122,84,-55) (122,116,-55) (83,116,-55) |
| Beast Pens | false | (82,45,-55) (115,45,-55) (115,79,-55) (82,79,-55) |
| Cistern | false | (7,47,-55) (44,47,-55) (44,78,-55) (7,78,-55) |
| Gate of Two Peoples | false | (49,24,-55) (78,24,-55) (78,45,-55) (49,45,-55) |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Collapsed storage vault | (31,30) (41,25) (46,35) (36,40) |
| Underground reservoir   | (11,52) (32,52) (32,75) (11,75) |
| Solid Rock         | (0,0) (140,0) (140,180) (0,180) |

---

## Items

| id                  | x   | y   | z   | label              |
|---------------------|-----|-----|-----|--------------------|
| rusted_chain_hook   | 70 | 170 |  6  | Rusted chain hook  |
| broken_wagon_wheel  | 92 | 125 |     | Broken wagon wheel |
| crate_labels        | 98 | 144 |  3  | Crate labels       |
| rusted_scales       | 98 | 135 |     | Rusted scales      |
| damp_sacks          | 49 | 145 |     | Damp sacks         |
| cold_larder_door_knob | 84 | 99 |  4  | Cold larder door knob |
| iron_bollard        | 91 | 74 |  2  | Iron bollard       |
| beast_feed_trough   | 96 | 65 |  1  | Beast feed trough  |
| cistern_valve       | 35 | 65 |  3  | Cistern valve      |
| rusted_gate_lever   | 70 | 25 |  2  | Rusted gate lever  |
| graffiti_tag        | 52 | 25 |  3  | Graffiti tag       |
| broken_shackle      | 86 | 50 |  1  | Broken shackle     |

---

## Ambient Visibility

The Freight Quarter is poorly lit. Torches burn in wall brackets along the
main corridors, but side chambers dim quickly. The cistern area is perpetually
misty, reducing visibility to 15 feet.

- **default:** 30

---

## Connections

| name              | x    | y     | destination                              |
|-------------------|------|-------|------------------------------------------|
| broken_lift_shaft | 64 | 178 | places/obelisk_reach/echoing_caverns/level-1 |
| to_level_3        | 64 | 24 | places/obelisk_reach/echoing_caverns/level-3 |

---

## Boundaries

### Damp Cold
- **type:** environmental
- **blocks:** none
- **effect:** temperature drops 5°F per round in the cold larder and cistern areas; creatures without cold resistance take 1d4 cold damage per round
- **vertices:** (84,84) (122,84) (122,115) (84,115)

### Beast Pen Containment
- **type:** physical/magical
- **blocks:** movement
- **effect:** creatures inside the beast pens cannot leave without the gate lever being turned
- **vertices:** (83,46) (115,46) (115,78) (83,78)
