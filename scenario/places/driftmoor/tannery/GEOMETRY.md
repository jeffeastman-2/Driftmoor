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
| front_entrance  | 26.0  | 0.0  |
| hide_racks      | 13.0  | 19.5  |
| tool_bench      | 39.0 | 19.5  |
| drying_line     | 26.0  | 32.5 |
| tanning_vat_3.25   | 13.0  | -6.5 |
| tanning_vat_6.5   | 39.0 | -6.5 |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| WORKSHOP   | 3.25        | (0.0,0.0) (52.0,0.0) (52.0,39.0) (0.0,39.0)     |
| VAT_YARD   | 0.0        | (0.0,-13.0) (52.0,-13.0) (52.0,0.0) (0.0,0.0)     |
| EXTERIOR   | 0.0        | (-9.75,-19.5) (61.75,-19.5) (61.75,48.75) (-9.75,48.75)  |

---

## Impassable

| description | vertices                        |
|-------------|---------------------------------|
| Back wall   | (0.0,35.75) (52.0,35.75) (52.0,39.0) (0.0,39.0)   |

---

## Connections

| name            | x   | y   | destination      |
|-----------------|-----|-----|------------------|
| front_entrance  | 26.0 | 0.0 | places/driftmoor |
