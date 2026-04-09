# GEOMETRY.md — The Beacon (Church of Pelor)

## Scene

- **name:** The Beacon
- **place_path:** places/driftmoor/beacon_church
- **z_level:** 8.0
- **width:** 30.0
- **height:** 25.0
- **origin:** 2955.0, 2800.0, 8.0

Notes: The Beacon sits on a small rise north of the Greywater, slightly
elevated above town (z=8.0 vs town z=5.0). Origin at southwest corner
of building footprint. The steeple is above z=8.0 and not a navigable
space. A small walled garden lies behind (north of) the main building.
Interior flows: entrance → main chapel → altar → sacristy (side door).

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_doors     | 15.0 | 0.0  |
| altar           | 15.0 | 18.0 |
| hearth          | 5.0  | 10.0 |
| bench_left      | 8.0  | 10.0 |
| bench_right     | 22.0 | 10.0 |
| lantern_pole    | 15.0 | 24.0 |
| garden_center   | 15.0 | 32.0 |
| steeple_base    | 13.0 | 20.0 |

---

## Zones

| name      | render_z | vertices                              |
|-----------|----------|---------------------------------------|
| ALTAR     | 2        | (10,15) (20,15) (20,22) (10,22)       |
| SACRISTY  | 2        | (22,14) (28,14) (28,22) (22,22)       |
| CHAPEL    | 1        | (2,2) (28,2) (28,22) (2,22)           |
| GARDEN    | 1        | (2,22) (28,22) (28,38) (2,38)         |
| EXTERIOR  | 0        | (-5,-5) (35,-5) (35,43) (-5,43)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| North wall       | (2,22) (28,22) (28,24) (2,24)         |
| Garden wall      | (0,36) (30,36) (30,38) (0,38)         |
| Steeple interior | (13,18) (17,18) (17,22) (13,22)       |

---

## Connections

| name            | x    | y    | destination              |
|-----------------|------|------|--------------------------|
| front_doors     | 15.0 | 0.0  | places/driftmoor         |
| garden_gate     | 15.0 | 37.0 | places/driftmoor         |
| sacristy_door   | 28.0 | 18.0 | places/driftmoor         |

---

## Boundaries

### Pelor's Sanctified Ground

- **type:** magical
- **blocks:** undead, shadow_creature, shadowbeast
- **effect:** sacred ground — undead cannot enter; shadowbeasts feel wrongness and recoil
- **vertices:** (2,2) (28,2) (28,38) (2,38)

### The Beacon Lantern Aura

- **type:** magical
- **blocks:** none
- **effect:** lantern atop steeple emits Pelor's light; currently flickering with dark energy — radius of comfort reduced, locals uneasy
- **vertices:** (10,18) (20,18) (20,25) (10,25)

---

## Starting Positions

| character | x    | y    | zone    |
|-----------|------|------|---------|
| amara     | 15.0 | 4.0  | CHAPEL  |
| father_elden | 15.0 | 16.0 | ALTAR  |
| mira      | 10.0 | 8.0  | CHAPEL  |