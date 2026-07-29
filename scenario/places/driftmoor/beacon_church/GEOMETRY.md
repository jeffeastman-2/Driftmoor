# GEOMETRY.md — The Beacon (Church of Pelor)

## Scene

- **name:** The Beacon
- **place_path:** places/driftmoor/beacon_church
- **z_level:** 26.0
- **width:** 48.75
- **height:** 40.625
- **origin:** 520.5, 630, 9.75

Notes: The Beacon sits on a small rise north of the Greywater, slightly
elevated above town (z=26.0 vs town z=16.25). Origin at southwest corner
of building footprint. The steeple is above z=26.0 and not a navigable
space. A small walled garden lies behind (north of) the main building.
Interior flows: entrance → main chapel → altar → sacristy (side door).

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_doors     | 24 | 0  |
| altar           | 24 | 29 |
| hearth          | 8  | 16 |
| bench_left      | 13  | 16 |
| bench_right     | 35.5 | 16 |
| lantern_pole    | 24 | 39 |
| garden_center   | 24 | 52 |
| steeple_base    | 21 | 32.5 |

---

## Zones

| name      | render_z | vertices                              |
|-----------|----------|---------------------------------------|
| ALTAR     | 6.5        | (16,24) (32.5,24) (32.5,35.5) (16,35.5)       |
| SACRISTY  | 6.5        | (35.5,22.5) (45.5,22.5) (45.5,35.5) (35.5,35.5)       |
| CHAPEL    | 3.25        | (3,3) (45.5,3) (45.5,35.5) (3,35.5)           |
| GARDEN    | 3.25        | (3,35.5) (45.5,35.5) (45.5,61.5) (3,61.5)         |
| EXTERIOR  | 0.0        | (-8,-8) (56.5,-8) (56.5,69.5) (-8,69.5)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| North wall       | (3,35.5) (45.5,35.5) (45.5,39) (3,39)         |
| Garden wall      | (0,58.5) (48.5,58.5) (48.5,61.5) (0,61.5)         |
| Steeple interior | (21,29) (27.5,29) (27.5,35.5) (21,35.5)       |

---

## Connections

| name            | x    | y    | destination              |
|-----------------|------|------|--------------------------|
| front_doors     | 24 | 0  | places/driftmoor         |
| garden_gate     | 24 | 60 | places/driftmoor         |
| sacristy_door   | 45.5 | 29 | places/driftmoor         |

---

## Boundaries

### Pelor's Sanctified Ground

- **type:** magical
- **blocks:** undead, shadow_creature, shadowbeast
- **effect:** sacred ground — undead cannot enter; shadowbeasts feel wrongness and recoil
- **vertices:** (3,3) (45.5,3) (45.5,61.5) (3,61.5)

### The Beacon Lantern Aura

- **type:** magical
- **blocks:** none
- **effect:** lantern atop steeple emits Pelor's light; currently flickering with dark energy — radius of comfort reduced, locals uneasy
- **vertices:** (16,29) (32.5,29) (32.5,40.5) (16,40.5)

---
