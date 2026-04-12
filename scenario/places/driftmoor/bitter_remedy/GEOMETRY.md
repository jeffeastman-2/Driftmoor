# GEOMETRY.md — The Bitter Remedy (Apothecary)

## Scene

- **name:** The Bitter Remedy
- **place_path:** places/driftmoor/bitter_remedy
- **z_level:** 16.25
- **width:** 45.5
- **height:** 39.0
- **origin:** 9467.25, 8560.5, 16.25

Notes: Small weathered stone building near the Greywater River.
Origin at southwest corner. Shopfront with counter and shelves
in front, restricted back room behind a closed door. Green vines
on exterior walls. Crooked chimney.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 22.75  | 0.0  |
| counter         | 22.75  | 13.0  |
| herb_shelves_w  | 6.5  | 9.75  |
| herb_shelves_e  | 39.0 | 9.75  |
| mortar_pestle   | 19.5  | 16.25  |
| back_room_door  | 22.75  | 22.75  |
| experiment_table| 22.75  | 32.5 |
| volatile_shelf  | 39.0 | 32.5 |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| BACK_ROOM  | 6.5        | (0.0,22.75) (45.5,22.75) (45.5,39.0) (0.0,39.0)   |
| SHOPFRONT  | 3.25        | (0.0,0.0) (45.5,0.0) (45.5,22.75) (0.0,22.75)     |
| EXTERIOR   | 0.0        | (-9.75,-9.75) (55.25,-9.75) (55.25,48.75) (-9.75,48.75) |

---

## Impassable

| description    | vertices                      |
|----------------|-------------------------------|
| Counter        | (9.75,13.0) (35.75,13.0) (35.75,16.25) (9.75,16.25)     |
| Dividing wall  | (0.0,22.75) (45.5,22.75) (45.5,26.0) (0.0,26.0)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 22.75 | 0.0 | places/driftmoor |

---

## Boundaries

### Back Room — Restricted

- **type:** conditional
- **blocks:** all
- **effect:** back room off-limits to customers; contains volatile ingredients and personal experiments
- **vertices:** (0.0,22.75) (45.5,22.75) (45.5,39.0) (0.0,39.0)
