# GEOMETRY.md — The Old Watchtower

## Scene

- **name:** The Old Watchtower
- **place_path:** places/mistwood_hills/old_watchtower
- **z_level:** 120.0
- **width:** 30.0
- **height:** 30.0
- **origin:** 6085.0, 9585.0, 120.0

Notes: A crumbling stone tower on a hilltop in the Mistwood. Origin
at southwest corner of the hilltop clearing. The tower is roughly
circular, 8m diameter, with interior staircase. The upper level is
partially collapsed. A clearing surrounds the tower base. Dense
forest beyond.

---

## Landmarks

| name              | x    | y    |
|-------------------|------|------|
| tower_base        | 15.0 | 15.0 |
| tower_entrance    | 15.0 | 11.0 |
| staircase         | 13.0 | 15.0 |
| upper_level       | 15.0 | 15.0 |
| collapsed_section | 17.0 | 18.0 |
| clearing_south    | 15.0 | 5.0  |
| clearing_north    | 15.0 | 25.0 |
| viewpoint         | 15.0 | 16.0 |

---

## Zones

| name            | render_z | vertices                              |
|-----------------|----------|---------------------------------------|
| TOWER_INTERIOR  | 2        | (11,11) (19,11) (19,19) (11,19)        |
| CLEARING        | 1        | (3,3) (27,3) (27,27) (3,27)            |
| FOREST          | 0        | (0,0) (30,0) (30,30) (0,30)            |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Tower walls        | (10,10) (20,10) (20,11) (10,11)        |
| Collapsed section  | (16,17) (20,17) (20,20) (16,20)        |

---

## Connections

| name              | x    | y    | destination                  |
|-------------------|------|------|------------------------------|
| trail_south       | 15.0 | 0.0  | places/mistwood_hills        |
