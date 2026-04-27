# GEOMETRY.md — The Tannery

## Scene

- **name:** The Tannery
- **place_path:** places/driftmoor/tannery
- **z_level:** 16.25
- **width:** 52.0
- **height:** 39.0
- **origin:** 9122.75, 8771.75, 16.25

Notes: Low stone building near the riverbank. Origin at southwest
corner. Tanning vats outside in a yard. Interior workshop with
hide racks and tools. Strong smell keeps visitors away.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_entrance  | 26  | 0  |
| hide_racks      | 13  | 19  |
| tool_bench      | 39 | 19  |
| drying_line     | 26  | 32 |
| tanning_vat_3.25   | 13  | -6 |
| tanning_vat_6.5   | 39 | -6 |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| WORKSHOP   | 3.25        | (0,0) (52,0) (52,39) (0,39)     |
| VAT_YARD   | 0.0        | (0,-13) (52,-13) (52,0) (0,0)     |
| EXTERIOR   | 0.0        | (-9,-19) (61,-19) (61,48) (-9,48)  |

---

## Impassable

| description | vertices                        |
|-------------|---------------------------------|
| Back wall   | (0,35) (52,35) (52,39) (0,39)   |

---

## Connections

| name            | x   | y   | destination      |
|-----------------|-----|-----|------------------|
| front_entrance  | 26 | 0 | places/driftmoor |
