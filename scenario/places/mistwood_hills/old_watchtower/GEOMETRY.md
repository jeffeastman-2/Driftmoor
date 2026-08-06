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
| tower_base        | 48 | 48 |
| tower_entrance    | 48 | 35 |
| staircase         | 42 | 48 |
| upper_level       | 48 | 48 |
| collapsed_section | 55 | 58 |
| clearing_south    | 48 | 16  |
| clearing_north    | 48 | 81 |
| viewpoint         | 48 | 52 |

---

## Zones

| name | render_z | auto_wall | vertices |
|-----------------|----------|---------|---------------------------------------|
| TOWER_INTERIOR | 6.5 |  | (35,35) (61,35) (61,61) (35,61) |
| CLEARING | 3.25 |  | (9,9) (87,9) (87,87) (9,87) |
| FOREST | 0.0 |  | (0,0) (97,0) (97,97) (0,97) |
---

## Walls

- **auto_wall:** false

This is a ruined-watchtower exploration site — a clearing and its interior, not rooms with doors. None of these zones share a coincident edge with any other, so the per-zone perimeter pass would seal every one into an isolated box with no door to open it.

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Tower walls        | (32,32) (65,32) (65,35) (32,35)        |
| Collapsed section  | (52,55) (65,55) (65,65) (52,65)        |

---

## Connections

| name              | x    | y    | destination                  |
|-------------------|------|------|------------------------------|
| trail_south       | 48 | 0  | places/mistwood_hills        |
