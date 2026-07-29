# GEOMETRY.md — The Tannery

## Scene

- **name:** The Tannery
- **place_path:** places/driftmoor/tannery
- **z_level:** 16.25
- **width:** 26
- **height:** 19.5
- **origin:** 323, 466.5, 0

Notes: Low stone building near the riverbank. Origin at southwest
corner. Tanning vats outside in a yard. Interior workshop with
hide racks and tools. Strong smell keeps visitors away.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_entrance  | 13  | 0  |
| hide_racks      | 6.5  | 9.5  |
| tool_bench      | 19.5 | 9.5  |
| drying_line     | 13  | 16 |
| tanning_vat_3.25   | 6.5  | -3 |
| tanning_vat_6.5   | 19.5 | -3 |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| WORKSHOP   | 3.25        | (0,0) (26,0) (26,19.5) (0,19.5)     |
| VAT_YARD   | 0.0        | (0,-6.5) (26,-6.5) (26,0) (0,0)     |
| EXTERIOR   | 0.0        | (-4.5,-9.5) (30.5,-9.5) (30.5,24) (-4.5,24)  |

---

## Impassable

| description | vertices                        |
|-------------|---------------------------------|
| Back wall   | (0,17.5) (26,17.5) (26,19.5) (0,19.5)   |

---

## Connections

| name            | x   | y   | destination      |
|-----------------|-----|-----|------------------|
| front_entrance  | 13 | 0 | places/driftmoor |
