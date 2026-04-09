# GEOMETRY.md — The Midwife's Home

## Scene

- **name:** The Midwife's Home
- **place_path:** places/driftmoor/midwifes_home
- **z_level:** 5.0
- **width:** 12.0
- **height:** 14.0
- **origin:** 3044.0, 2704.0, 5.0

Notes: Cozy cottage with an herb garden. Origin at southwest corner.
Living room in front, treatment room behind, herb garden on the east
side. Smells of herbs and dried flowers.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 6.0  | 0.0  |
| hearth          | 2.0  | 3.0  |
| rocking_chair   | 4.0  | 3.0  |
| remedy_shelf    | 10.0 | 3.0  |
| treatment_door  | 6.0  | 6.0  |
| treatment_cot   | 6.0  | 9.0  |
| herb_garden     | 14.0 | 7.0  |

---

## Zones

| name            | render_z | vertices                        |
|-----------------|----------|---------------------------------|
| TREATMENT_ROOM  | 2        | (0,6) (12,6) (12,12) (0,12)      |
| LIVING_ROOM     | 1        | (0,0) (12,0) (12,6) (0,6)        |
| HERB_GARDEN     | 1        | (12,3) (18,3) (18,11) (12,11)    |
| EXTERIOR        | 0        | (-3,-3) (21,-3) (21,15) (-3,15)  |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Dividing wall  | (0,6) (12,6) (12,7) (0,7)        |
| Back wall      | (0,11) (12,11) (12,12) (0,12)    |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 6.0 | 0.0 | places/driftmoor |
