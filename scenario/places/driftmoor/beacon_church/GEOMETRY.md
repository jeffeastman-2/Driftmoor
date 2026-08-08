# GEOMETRY.md — The Beacon (Church of Pelor)

## Scene

- **name:** The Beacon
- **place_path:** places/driftmoor/beacon_church
- **z_level:** 26.0
- **width:** 48.75
- **height:** 78.0
- **origin:** 520.5, 630, 9.75

Notes: The Beacon sits on a small rise north of the Greywater, slightly
elevated above town (z=26.0 vs town z=16.25). Origin at southwest corner
of building footprint. The steeple is above z=26.0 and not a navigable
space. A half-width garden lies behind (north of) the main chapel; its
east flank is a residential wing (sanctuary, sacristy, kitchen, and
Elden's and Mira's rooms), each opening onto the garden.
Interior flows: entrance → main chapel → altar; garden entrance (left of
the altar) → garden → residential wing doors along the garden's east edge.

---

## Landmarks

| name             | x    | y    |
|------------------|------|------|
| front_doors      | 24 | 3  |
| garden_door   | 13.492  | 27.79 |
| garden_gate      | 13.5 | 78 |
| altar            | 24.112 | 20.273 |
| hearth           | 6.378  | 6.729 |
| bench_left       | 31.183  | 11.277 |
| bench_right      | 31.131 | 14.878 |
| pew_sw           | 18.299 | 7.906 |
| pew_se           | 31.176 | 7.917 |
| pew_nw           | 18.302 | 11.325 |
| pew_ne           | 18.286 | 14.899 |
| candle_stand     | 17.874 | 20.144 |
| steeple_base     | 21 | 26 |
| graveyard_gate   | 3 | 53.015 |
| lantern_pole     | 10.563 | 30.563 |
| herb_bed_w       | 7.79 | 59.083 |
| herb_bed_e       | 8.083 | 69.244 |
| garden_center    | 13.5 | 65 |
| sanctuary_door   | 24 | 33 |
| sanctuary_bed    | 41.342 | 33.629 |
| sacristy_door    | 24 | 43 |
| sacristy_table   | 41.454 | 43 |
| kitchen_door     | 24 | 53 |
| kitchen_stove    | 41.859 | 50.161 |
| kitchen_worktable| 34.854 | 53.532 |
| eldens_room_door | 24 | 63 |
| eldens_bed       | 41.552 | 63.63 |
| eldens_desk      | 31.351 | 65.581 |
| miras_room_door  | 24 | 73 |
| miras_bed        | 41.762 | 73.629 |
| miras_chest      | 36.804 | 73.482 |

---

## Zones

| name          | render_z | auto_wall | vertices                                |
|---------------|----------|---------|--------------------------------------------|
| ALTAR         | 6.5 |  | (16,18) (32.5,18) (32.5,28) (16,28) |
| CHAPEL        | 3.25 |  | (3,3) (45.5,3) (45.5,28) (3,28) |
| GARDEN        | 3.25 |  | (3,28) (24,28) (24,78) (3,78) |
| SANCTUARY     | 6.5 |  | (24,28) (45.5,28) (45.5,38) (24,38) |
| SACRISTY      | 6.5 |  | (24,38) (45.5,38) (45.5,48) (24,48) |
| KITCHEN       | 6.5 |  | (24,48) (45.5,48) (45.5,58) (24,58) |
| ELDENS_ROOM   | 6.5 |  | (24,58) (45.5,58) (45.5,68) (24,68) |
| MIRAS_ROOM    | 6.5 |  | (24,68) (45.5,68) (45.5,78) (24,78) |
| EXTERIOR      | 0.0 |  | (-8,-8) (56.5,-8) (56.5,86) (-8,86) |
---

## Fog of War

- **reveal_on_entry:** SANCTUARY, SACRISTY, KITCHEN, ELDENS_ROOM, MIRAS_ROOM

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|

---

## Connections

| name             | x    | y    | destination              |
|------------------|------|------|--------------------------|
| front_doors      | 24 | 3  | places/driftmoor         |
| garden_gate      | 13.5 | 78 | places/driftmoor         |
| graveyard_gate   | 3 | 48.5 | places/driftmoor/graveyard |

---

## Boundaries

### Pelor's Sanctified Ground

- **type:** magical
- **blocks:** undead, shadow_creature, shadowbeast
- **effect:** sacred ground — undead cannot enter; shadowbeasts feel wrongness and recoil
- **render:** hidden
- **vertices:** (3,3) (45.5,3) (45.5,78) (3,78)

### The Beacon Lantern Aura

- **type:** magical
- **blocks:** none
- **effect:** lantern atop steeple emits Pelor's light; currently flickering with dark energy — radius of comfort reduced, locals uneasy
- **render:** hidden
- **vertices:** (16,22) (32.5,22) (32.5,33) (16,33)

---
