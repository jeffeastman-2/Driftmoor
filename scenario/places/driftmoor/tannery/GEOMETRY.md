# GEOMETRY.md — The Tannery

## Scene

- **name:** The Tannery
- **place_path:** places/driftmoor/tannery
- **z_level:** 5.0
- **width:** 16.0
- **height:** 12.0
- **origin:** 2807.0, 2699.0, 5.0

Notes: Low stone building near the riverbank. Origin at southwest
corner. Tanning vats outside in a yard. Interior workshop with
hide racks and tools. Strong smell keeps visitors away.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_entrance  | 8.0  | 0.0  |
| hide_racks      | 4.0  | 6.0  |
| tool_bench      | 12.0 | 6.0  |
| drying_line     | 8.0  | 10.0 |
| tanning_vat_1   | 4.0  | -2.0 |
| tanning_vat_2   | 12.0 | -2.0 |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| WORKSHOP   | 1        | (0,0) (16,0) (16,12) (0,12)     |
| VAT_YARD   | 0        | (0,-4) (16,-4) (16,0) (0,0)     |
| EXTERIOR   | 0        | (-3,-6) (19,-6) (19,15) (-3,15)  |

---

## Impassable

| description | vertices                        |
|-------------|---------------------------------|
| Back wall   | (0,11) (16,11) (16,12) (0,12)   |

---

## Connections

| name            | x   | y   | destination      |
|-----------------|-----|-----|------------------|
| front_entrance  | 8.0 | 0.0 | places/driftmoor |
