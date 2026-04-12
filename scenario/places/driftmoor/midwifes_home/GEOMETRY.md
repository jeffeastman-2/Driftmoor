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
| front_door      | 19.5  | 0.0  |
| hearth          | 6.5  | 9.75  |
| rocking_chair   | 13.0  | 9.75  |
| remedy_shelf    | 32.5 | 9.75  |
| treatment_door  | 19.5  | 19.5  |
| treatment_cot   | 19.5  | 29.25  |
| herb_garden     | 45.5 | 22.75  |

---

## Zones

| name            | render_z | vertices                        |
|-----------------|----------|---------------------------------|
| TREATMENT_ROOM  | 6.5        | (0.0,19.5) (39.0,19.5) (39.0,39.0) (0.0,39.0)      |
| LIVING_ROOM     | 3.25        | (0.0,0.0) (39.0,0.0) (39.0,19.5) (0.0,19.5)        |
| HERB_GARDEN     | 3.25        | (39.0,9.75) (58.5,9.75) (58.5,35.75) (39.0,35.75)    |
| EXTERIOR        | 0.0        | (-9.75,-9.75) (68.25,-9.75) (68.25,48.75) (-9.75,48.75)  |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Dividing wall  | (0.0,19.5) (39.0,19.5) (39.0,22.75) (0.0,22.75)        |
| Back wall      | (0.0,35.75) (39.0,35.75) (39.0,39.0) (0.0,39.0)    |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 19.5 | 0.0 | places/driftmoor |
