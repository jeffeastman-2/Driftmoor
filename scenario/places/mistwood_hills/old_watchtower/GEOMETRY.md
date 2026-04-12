# GEOMETRY.md — The Old Watchtower

## Scene

- **name:** The Old Watchtower
- **place_path:** places/mistwood_hills/old_watchtower
- **z_level:** 390.0
- **width:** 97.5
- **height:** 97.5
- **origin:** 19776.25, 31151.25, 390.0

Notes: A crumbling stone tower on a hilltop in the Mistwood. Origin
at southwest corner of the hilltop clearing. The tower is roughly
circular, 26.0m diameter, with interior staircase. The upper level is
partially collapsed. A clearing surrounds the tower base. Dense
forest beyond.

---

## Landmarks

| name              | x    | y    |
|-------------------|------|------|
| tower_base        | 48.75 | 48.75 |
| tower_entrance    | 48.75 | 35.75 |
| staircase         | 42.25 | 48.75 |
| upper_level       | 48.75 | 48.75 |
| collapsed_section | 55.25 | 58.5 |
| clearing_south    | 48.75 | 16.25  |
| clearing_north    | 48.75 | 81.25 |
| viewpoint         | 48.75 | 52.0 |

---

## Zones

| name            | render_z | vertices                              |
|-----------------|----------|---------------------------------------|
| TOWER_INTERIOR  | 6.5        | (35.75,35.75) (61.75,35.75) (61.75,61.75) (35.75,61.75)        |
| CLEARING        | 3.25        | (9.75,9.75) (87.75,9.75) (87.75,87.75) (9.75,87.75)            |
| FOREST          | 0.0        | (0.0,0.0) (97.5,0.0) (97.5,97.5) (0.0,97.5)            |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Tower walls        | (32.5,32.5) (65.0,32.5) (65.0,35.75) (32.5,35.75)        |
| Collapsed section  | (52.0,55.25) (65.0,55.25) (65.0,65.0) (52.0,65.0)        |

---

## Connections

| name              | x    | y    | destination                  |
|-------------------|------|------|------------------------------|
| trail_south       | 48.75 | 0.0  | places/mistwood_hills        |
