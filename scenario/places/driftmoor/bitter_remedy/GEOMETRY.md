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
| front_door      | 22  | 0  |
| counter         | 22  | 13  |
| herb_shelves_w  | 6  | 9  |
| herb_shelves_e  | 39 | 9  |
| mortar_pestle   | 19  | 16  |
| back_room_door  | 22  | 22  |
| experiment_table| 22  | 32 |
| volatile_shelf  | 39 | 32 |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| BACK_ROOM  | 6.5        | (0,22) (45,22) (45,39) (0,39)   |
| SHOPFRONT  | 3.25        | (0,0) (45,0) (45,22) (0,22)     |
| EXTERIOR   | 0.0        | (-9,-9) (55,-9) (55,48) (-9,48) |

---

## Impassable

| description    | vertices                      |
|----------------|-------------------------------|
| Counter        | (9,13) (35,13) (35,16) (9,16)     |
| Dividing wall  | (0,22) (45,22) (45,26) (0,26)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 22 | 0 | places/driftmoor |

---

## Boundaries

### Back Room — Restricted

- **type:** conditional
- **blocks:** all
- **effect:** back room off-limits to customers; contains volatile ingredients and personal experiments
- **vertices:** (0,22) (45,22) (45,39) (0,39)
