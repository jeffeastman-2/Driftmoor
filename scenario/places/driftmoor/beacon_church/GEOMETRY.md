# GEOMETRY.md — The Beacon (Church of Pelor)

## Scene

- **name:** The Beacon
- **place_path:** places/driftmoor/beacon_church
- **z_level:** 26.0
- **width:** 97.5
- **height:** 81.25
- **origin:** 9603.75, 9100.0, 26.0

Notes: The Beacon sits on a small rise north of the Greywater, slightly
elevated above town (z=26.0 vs town z=16.25). Origin at southwest corner
of building footprint. The steeple is above z=26.0 and not a navigable
space. A small walled garden lies behind (north of) the main building.
Interior flows: entrance → main chapel → altar → sacristy (side door).

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_doors     | 48.75 | 0.0  |
| altar           | 48.75 | 58.5 |
| hearth          | 16.25  | 32.5 |
| bench_left      | 26.0  | 32.5 |
| bench_right     | 71.5 | 32.5 |
| lantern_pole    | 48.75 | 78.0 |
| garden_center   | 48.75 | 104.0 |
| steeple_base    | 42.25 | 65.0 |

---

## Zones

| name      | render_z | vertices                              |
|-----------|----------|---------------------------------------|
| ALTAR     | 6.5        | (32.5,48.75) (65.0,48.75) (65.0,71.5) (32.5,71.5)       |
| SACRISTY  | 6.5        | (71.5,45.5) (91.0,45.5) (91.0,71.5) (71.5,71.5)       |
| CHAPEL    | 3.25        | (6.5,6.5) (91.0,6.5) (91.0,71.5) (6.5,71.5)           |
| GARDEN    | 3.25        | (6.5,71.5) (91.0,71.5) (91.0,123.5) (6.5,123.5)         |
| EXTERIOR  | 0.0        | (-16.25,-16.25) (113.75,-16.25) (113.75,139.75) (-16.25,139.75)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| North wall       | (6.5,71.5) (91.0,71.5) (91.0,78.0) (6.5,78.0)         |
| Garden wall      | (0.0,117.0) (97.5,117.0) (97.5,123.5) (0.0,123.5)         |
| Steeple interior | (42.25,58.5) (55.25,58.5) (55.25,71.5) (42.25,71.5)       |

---

## Connections

| name            | x    | y    | destination              |
|-----------------|------|------|--------------------------|
| front_doors     | 48.75 | 0.0  | places/driftmoor         |
| garden_gate     | 48.75 | 120.25 | places/driftmoor         |
| sacristy_door   | 91.0 | 58.5 | places/driftmoor         |

---

## Boundaries

### Pelor's Sanctified Ground

- **type:** magical
- **blocks:** undead, shadow_creature, shadowbeast
- **effect:** sacred ground — undead cannot enter; shadowbeasts feel wrongness and recoil
- **vertices:** (6.5,6.5) (91.0,6.5) (91.0,123.5) (6.5,123.5)

### The Beacon Lantern Aura

- **type:** magical
- **blocks:** none
- **effect:** lantern atop steeple emits Pelor's light; currently flickering with dark energy — radius of comfort reduced, locals uneasy
- **vertices:** (32.5,58.5) (65.0,58.5) (65.0,81.25) (32.5,81.25)

---

## Starting Positions

| character | x    | y    | zone    |
|-----------|------|------|---------|
| amara     | 48.75 | 13.0  | CHAPEL  |
| father_elden | 48.75 | 52.0 | ALTAR  |
| mira      | 32.5 | 26.0  | CHAPEL  |