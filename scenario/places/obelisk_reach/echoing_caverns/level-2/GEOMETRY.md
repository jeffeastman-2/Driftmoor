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
| broken_lift_shaft          | 70  | 165 |
| factor_office_door         | 45  | 145 |
| receiving_floor_arch       | 70  | 115 |
| cold_larder_threshold      | 95  | 95  |
| beast_pens_gate            | 95  | 45  |
| cistern_door               | 35  | 55  |
| gate_of_two_peoples_entrance | 70  | 25  |

---

## Walls

- **auto_wall:** false

The Freight Quarter consists of rough-hewn chambers with occasional iron doors
and gates. The broken lift shaft and gate of two peoples have mechanical
barriers that function; the other chambers connect via open archways.

## Zones

| name | auto_wall | vertices |
|------------------|---------|---------------------------------------------------------------------------------------------------|
| Broken Lift | false | (51,157,-75) (89,157,-75) (89,178,-75) (51,178,-75) |
| Factor's Office | false | (26,126,-75) (64,126,-75) (64,162,-75) (26,162,-75) |
| Fungal Stores | false | (66,126,-75) (104,126,-75) (104,157,-75) (66,157,-75) |
| Receiving Floor | false | (51,92,-75) (89,92,-75) (89,136,-75) (51,136,-75) |
| Freight Guardroom | false | (6,102,-75) (44,102,-75) (44,162,-75) (6,162,-75) |
| Cold Larder | false | (89,73,-75) (109,73,-75) (109,115,-75) (89,115,-75) |
| Beast Pens | false | (76,30,-75) (109,30,-75) (109,78,-75) (76,78,-75) |
| Cistern | false | (15,30,-75) (56,30,-75) (56,80,-75) (15,80,-75) |
| Gate of Two Peoples | false | (31,10,-75) (109,10,-75) (109,45,-75) (31,45,-75) |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Collapsed storage vault | (31,30) (41,25) (46,35) (36,40)        |
| Underground reservoir   | (11,61) (31,61) (31,91) (11,91)        |
| Solid Rock         | (0,0) (140,0) (140,180) (0,180)        |

---

## Items

| id                  | x   | y   | z   | label              |
|---------------------|-----|-----|-----|--------------------|
| rusted_chain_hook   | 70  | 170 |  6  | Rusted chain hook  |
| broken_wagon_wheel  | 75  | 130 |     | Broken wagon wheel |
| crate_labels        | 85  | 140 |  3  | Crate labels       |
| rusted_scales       | 95  | 125 |     | Rusted scales      |
| damp_sacks          | 75  | 110 |     | Damp sacks         |
| cold_larder_door_knob | 99 | 95  |  4  | Cold larder door knob |
| iron_bollard        | 95  | 55  |  2  | Iron bollard       |
| beast_feed_trough   | 90  | 50  |  1  | Beast feed trough  |
| cistern_valve       | 35  | 65  |  3  | Cistern valve      |
| rusted_gate_lever   | 70  | 25  |  2  | Rusted gate lever  |
| graffiti_tag        | 45  | 25  |  3  | Graffiti tag       |
| broken_shackle      | 80  | 35  |  1  | Broken shackle     |

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
| broken_lift_shaft | 70   | 178   | places/obelisk_reach/echoing_caverns/level-1 |
| to_level_3        | 70   | 10    | places/obelisk_reach/echoing_caverns/level-3 |

---

## Boundaries

### Damp Cold
- **type:** environmental
- **blocks:** none
- **effect:** temperature drops 5°F per round in the cold larder and cistern areas; creatures without cold resistance take 1d4 cold damage per round
- **vertices:** (89,73) (109,73) (109,115) (89,115) (51,80) (51,60)

### Beast Pen Containment
- **type:** physical/magical
- **blocks:** movement
- **effect:** creatures inside the beast pens cannot leave without the gate lever being turned
- **vertices:** (76,30) (109,30) (109,78) (76,78)
