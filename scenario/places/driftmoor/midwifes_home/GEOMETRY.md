# GEOMETRY.md — The Midwife's Home

## Scene

- **name:** The Midwife's Home
- **place_path:** places/driftmoor/midwifes_home
- **z_level:** 16.25
- **width:** 19.5
- **height:** 22.75
- **origin:** 712, 475.5, 0

Notes: Cozy cottage with an herb garden. Origin at southwest corner.
Living room in front, treatment room behind, herb garden on the east
side. Smells of herbs and dried flowers.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 9.5  | 0  |
| hearth          | 2.402  | 4.4  |
| rocking_chair   | 10.486  | 7.988  |
| remedy_shelf    | 17.694 | 5.397  |
| treatment_door  | 9.5  | 9.5  |
| treatment_cot   | 4.816  | 15.895  |
| herb_garden     | 24 | 11  |
| garden_archway  | 19.5 | 7 |

---

## Zones

| name | render_z | auto_wall | vertices |
|-----------------|----------|---------|---------------------------------|
| TREATMENT_ROOM | 6.5 |  | (0,9.5) (19.5,9.5) (19.5,19.5) (0,19.5) |
| LIVING_ROOM | 3.25 |  | (0,0) (19.5,0) (19.5,9.5) (0,9.5) |
| HERB_GARDEN | 3.25 |  | (19.5,4.5) (29,4.5) (29,17.5) (19.5,17.5) |
| EXTERIOR | 0.0 |  | (-4.5,-4.5) (34,-4.5) (34,24) (-4.5,24) |
---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Dividing wall west | (0,9.5) (8,9.5) (8,11) (0,11)          |
| Dividing wall east | (11,9.5) (19.5,9.5) (19.5,11) (11,11) |
| Back wall      | (0,17.5) (19.5,17.5) (19.5,19.5) (0,19.5)    |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 9.5 | 0 | places/driftmoor |
