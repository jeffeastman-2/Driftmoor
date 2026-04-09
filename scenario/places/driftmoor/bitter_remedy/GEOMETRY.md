# GEOMETRY.md — The Bitter Remedy (Apothecary)

## Scene

- **name:** The Bitter Remedy
- **place_path:** places/driftmoor/bitter_remedy
- **z_level:** 5.0
- **width:** 14.0
- **height:** 12.0
- **origin:** 2913.0, 2634.0, 5.0

Notes: Small weathered stone building near the Greywater River.
Origin at southwest corner. Shopfront with counter and shelves
in front, restricted back room behind a closed door. Green vines
on exterior walls. Crooked chimney.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 7.0  | 0.0  |
| counter         | 7.0  | 4.0  |
| herb_shelves_w  | 2.0  | 3.0  |
| herb_shelves_e  | 12.0 | 3.0  |
| mortar_pestle   | 6.0  | 5.0  |
| back_room_door  | 7.0  | 7.0  |
| experiment_table| 7.0  | 10.0 |
| volatile_shelf  | 12.0 | 10.0 |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| BACK_ROOM  | 2        | (0,7) (14,7) (14,12) (0,12)   |
| SHOPFRONT  | 1        | (0,0) (14,0) (14,7) (0,7)     |
| EXTERIOR   | 0        | (-3,-3) (17,-3) (17,15) (-3,15) |

---

## Impassable

| description    | vertices                      |
|----------------|-------------------------------|
| Counter        | (3,4) (11,4) (11,5) (3,5)     |
| Dividing wall  | (0,7) (14,7) (14,8) (0,8)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 7.0 | 0.0 | places/driftmoor |

---

## Boundaries

### Back Room — Restricted

- **type:** conditional
- **blocks:** all
- **effect:** back room off-limits to customers; contains volatile ingredients and personal experiments
- **vertices:** (0,7) (14,7) (14,12) (0,12)
