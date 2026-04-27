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
| front_doors     | 48 | 0  |
| altar           | 48 | 58 |
| hearth          | 16  | 32 |
| bench_left      | 26  | 32 |
| bench_right     | 71 | 32 |
| lantern_pole    | 48 | 78 |
| garden_center   | 48 | 104 |
| steeple_base    | 42 | 65 |

---

## Zones

| name      | render_z | vertices                              |
|-----------|----------|---------------------------------------|
| ALTAR     | 6.5        | (32,48) (65,48) (65,71) (32,71)       |
| SACRISTY  | 6.5        | (71,45) (91,45) (91,71) (71,71)       |
| CHAPEL    | 3.25        | (6,6) (91,6) (91,71) (6,71)           |
| GARDEN    | 3.25        | (6,71) (91,71) (91,123) (6,123)         |
| EXTERIOR  | 0.0        | (-16,-16) (113,-16) (113,139) (-16,139)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| North wall       | (6,71) (91,71) (91,78) (6,78)         |
| Garden wall      | (0,117) (97,117) (97,123) (0,123)         |
| Steeple interior | (42,58) (55,58) (55,71) (42,71)       |

---

## Connections

| name            | x    | y    | destination              |
|-----------------|------|------|--------------------------|
| front_doors     | 48 | 0  | places/driftmoor         |
| garden_gate     | 48 | 120 | places/driftmoor         |
| sacristy_door   | 91 | 58 | places/driftmoor         |

---

## Boundaries

### Pelor's Sanctified Ground

- **type:** magical
- **blocks:** undead, shadow_creature, shadowbeast
- **effect:** sacred ground — undead cannot enter; shadowbeasts feel wrongness and recoil
- **vertices:** (6,6) (91,6) (91,123) (6,123)

### The Beacon Lantern Aura

- **type:** magical
- **blocks:** none
- **effect:** lantern atop steeple emits Pelor's light; currently flickering with dark energy — radius of comfort reduced, locals uneasy
- **vertices:** (32,58) (65,58) (65,81) (32,81)

---

## Starting Positions

| character | x    | y    | zone    |
|-----------|------|------|---------|
| amara     | 48 | 13  | CHAPEL  |
| father_elden | 48 | 52 | ALTAR  |
| mira      | 32 | 26  | CHAPEL  |