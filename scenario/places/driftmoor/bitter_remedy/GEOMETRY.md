# GEOMETRY.md — The Bitter Remedy (Apothecary)

## Scene

- **name:** The Bitter Remedy
- **place_path:** places/driftmoor/bitter_remedy
- **z_level:** 16.25
- **width:** 22.75
- **height:** 19.5
- **origin:** 494, 364, 0

Notes: Small weathered stone building near the Greywater River.
Origin at southwest corner. Shopfront with counter and shelves
in front, restricted back room behind a closed door. Green vines
on exterior walls. Crooked chimney.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 11  | 0  |
| counter         | 11  | 6.5  |
| herb_shelves_w  | 3  | 4.5  |
| herb_shelves_e  | 19.5 | 4.5  |
| mortar_pestle   | 9.5  | 8  |
| back_room_door  | 11  | 11  |
| experiment_table| 11  | 16 |
| volatile_shelf  | 19.5 | 16 |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| BACK_ROOM  | 6.5        | (0,11) (22.5,11) (22.5,19.5) (0,19.5)   |
| SHOPFRONT  | 3.25        | (0,0) (22.5,0) (22.5,11) (0,11)     |
| EXTERIOR   | 0.0        | (-4.5,-4.5) (27.5,-4.5) (27.5,24) (-4.5,24) |

---

## Impassable

| description    | vertices                      |
|----------------|-------------------------------|
| Counter        | (4.5,6.5) (17.5,6.5) (17.5,8) (4.5,8)     |
| Dividing wall  | (0,11) (22.5,11) (22.5,13) (0,13)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 11 | 0 | places/driftmoor |

---

## Boundaries

### Back Room — Restricted

- **type:** conditional
- **blocks:** all
- **effect:** back room off-limits to customers; contains volatile ingredients and personal experiments
- **vertices:** (0,11) (22.5,11) (22.5,19.5) (0,19.5)
