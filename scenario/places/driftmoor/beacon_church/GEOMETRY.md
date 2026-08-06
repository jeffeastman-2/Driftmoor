# GEOMETRY.md — The Beacon (Church of Pelor)

## Scene

- **name:** The Beacon
- **place_path:** places/driftmoor/beacon_church
- **z_level:** 26.0
- **width:** 48.75
- **height:** 61.5
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
| front_doors     | 24 | 3  |
| garden_archway  | 24 | 35.5 |
| garden_gate     | 24 | 61.5 |
| altar           | 24.112 | 24.407 |
| hearth          | 6.992  | 7.711 |
| bench_left      | 31.147  | 14.992 |
| bench_right     | 31.131 | 18.577 |
| pew_sw          | 18.15 | 11.15 |
| pew_se          | 31.14 | 11.15 |
| pew_nw          | 18.153 | 14.839 |
| pew_ne          | 18.137 | 18.536 |
| candle_stand    | 17.664 | 25.7 |
| sacristy_table  | 40.388 | 24.087 |
| herb_bed_w      | 12 | 48 |
| herb_bed_e      | 36 | 48 |
| lantern_pole    | 24 | 39 |
| garden_center   | 24 | 52 |
| steeple_base    | 21 | 32.5 |

---

## Zones

| name | render_z | auto_wall | vertices |
|-----------|----------|---------|---------------------------------------|
| ALTAR | 6.5 |  | (16,24) (32.5,24) (32.5,35.5) (16,35.5) |
| SACRISTY | 6.5 |  | (35.5,22.5) (45.5,22.5) (45.5,35.5) (35.5,35.5) |
| CHAPEL | 3.25 |  | (3,3) (45.5,3) (45.5,35.5) (3,35.5) |
| GARDEN | 3.25 |  | (3,35.5) (45.5,35.5) (45.5,61.5) (3,61.5) |
| EXTERIOR | 0.0 |  | (-8,-8) (56.5,-8) (56.5,69.5) (-8,69.5) |
---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| North wall west  | (3,35.5) (22.5,35.5) (22.5,39) (3,39)         |
| North wall east  | (25.5,35.5) (45.5,35.5) (45.5,39) (25.5,39)  |
| Garden wall west | (0,58.5) (22.5,58.5) (22.5,61.5) (0,61.5)    |
| Garden wall east | (25.5,58.5) (48.5,58.5) (48.5,61.5) (25.5,61.5) |
| Steeple interior | (21,29) (27.5,29) (27.5,35.5) (21,35.5)       |

---

## Connections

| name            | x    | y    | destination              |
|-----------------|------|------|--------------------------|
| front_doors     | 24 | 3  | places/driftmoor         |
| garden_gate     | 24 | 61.5 | places/driftmoor         |
| sacristy_door   | 45.5 | 29 | places/driftmoor         |
| graveyard_path  | 3 | 48.5 | places/driftmoor/graveyard |

---

## Boundaries

### Pelor's Sanctified Ground

- **type:** magical
- **blocks:** undead, shadow_creature, shadowbeast
- **effect:** sacred ground — undead cannot enter; shadowbeasts feel wrongness and recoil
- **render:** hidden
- **vertices:** (3,3) (45.5,3) (45.5,61.5) (3,61.5)

### The Beacon Lantern Aura

- **type:** magical
- **blocks:** none
- **effect:** lantern atop steeple emits Pelor's light; currently flickering with dark energy — radius of comfort reduced, locals uneasy
- **render:** hidden
- **vertices:** (16,29) (32.5,29) (32.5,40.5) (16,40.5)

---
