# GEOMETRY.md — The Midwife's Home

## Scene

- **name:** The Midwife's Home
- **place_path:** places/driftmoor/midwifes_home
- **z_level:** 16.25
- **width:** 39.0
- **height:** 45.5
- **origin:** 9893.0, 8788.0, 16.25

Notes: Cozy cottage with an herb garden. Origin at southwest corner.
Living room in front, treatment room behind, herb garden on the east
side. Smells of herbs and dried flowers.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 19  | 0  |
| hearth          | 6  | 9  |
| rocking_chair   | 13  | 9  |
| remedy_shelf    | 32 | 9  |
| treatment_door  | 19  | 19  |
| treatment_cot   | 19  | 29  |
| herb_garden     | 45 | 22  |

---

## Zones

| name            | render_z | vertices                        |
|-----------------|----------|---------------------------------|
| TREATMENT_ROOM  | 6.5        | (0,19) (39,19) (39,39) (0,39)      |
| LIVING_ROOM     | 3.25        | (0,0) (39,0) (39,19) (0,19)        |
| HERB_GARDEN     | 3.25        | (39,9) (58,9) (58,35) (39,35)    |
| EXTERIOR        | 0.0        | (-9,-9) (68,-9) (68,48) (-9,48)  |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Dividing wall  | (0,19) (39,19) (39,22) (0,22)        |
| Back wall      | (0,35) (39,35) (39,39) (0,39)    |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 19 | 0 | places/driftmoor |
