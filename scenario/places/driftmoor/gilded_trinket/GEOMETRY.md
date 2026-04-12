# GEOMETRY.md — The Gilded Trinket (Pawn Shop)

## Scene

- **name:** The Gilded Trinket
- **place_path:** places/driftmoor/gilded_trinket
- **z_level:** 16.25
- **width:** 48.75
- **height:** 58.5
- **origin:** 9236.5, 8021.0, 16.25

Notes: A narrow, dimly lit building. The shopfront is the main room
with shelves, display cases, and a counter at the rear. Behind the
counter is a locked back area containing the large safe and Tavian's
private workspace. No upper floor — the building is single-storey.
Windows are small and covered with metal grates. Lighting is poor
throughout; oil lamps only. The display case with the obsidian ring
sits behind the counter near the back wall.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 22.75  | 0.0  |
| display_case    | 32.5 | 39.0 |
| counter         | 26.0  | 35.75 |
| obsidian_ring   | 34.12 | 42.25 |
| safe             | 42.25 | 48.75 |
| shelves_west    | 6.5  | 26.0  |
| shelves_east    | 42.25 | 26.0  |
| oil_lamp_main   | 22.75  | 22.75  |

---

## Zones

| name       | render_z | vertices                              |
|------------|----------|---------------------------------------|
| BACK_AREA  | 6.5        | (0.0,39.0) (48.75,39.0) (48.75,58.5) (0.0,58.5)         |
| DISPLAY    | 6.5        | (22.75,32.5) (45.5,32.5) (45.5,45.5) (22.75,45.5)         |
| SHOPFRONT  | 3.25        | (0.0,0.0) (48.75,0.0) (48.75,39.0) (0.0,39.0)           |
| EXTERIOR   | 0.0        | (-16.25,-16.25) (65.0,-16.25) (65.0,74.75) (-16.25,74.75)       |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Counter barrier    | (13.0,32.5) (45.5,32.5) (45.5,35.75) (13.0,35.75)         |
| Grated windows E   | (45.5,9.75) (48.75,9.75) (48.75,26.0) (45.5,26.0)           |
| Grated windows W   | (0.0,9.75) (3.25,9.75) (3.25,26.0) (0.0,26.0)               |
| Safe alcove wall   | (35.75,45.5) (48.75,45.5) (48.75,58.5) (35.75,58.5)       |

---

## Connections

| name          | x    | y    | destination      |
|---------------|------|------|------------------|
| front_door    | 22.75  | 0.0  | places/driftmoor |
| back_door     | 22.75  | 58.5 | places/driftmoor |

---

## Boundaries

### Tavian's Counter Line

- **type:** conditional
- **blocks:** all
- **effect:** counter marks the boundary of Tavian's domain; crossing without permission triggers immediate hostile response
- **vertices:** (0.0,32.5) (48.75,32.5) (48.75,58.5) (0.0,58.5)

### Display Case — Obelisk Ring Aura

- **type:** magical
- **blocks:** none
- **effect:** the obsidian ring pulses with obelisk energy; characters with obelisk shard attunement feel drawn toward it; Perception DC 45.5 to notice the pulse
- **vertices:** (22.75,32.5) (45.5,32.5) (45.5,45.5) (22.75,45.5)

---

## Starting Positions

| character | x    | y    | zone      |
|-----------|------|------|-----------|
| seraphina | 16.25  | 19.5  | SHOPFRONT |
| tavian    | 32.5 | 39.0 | BACK_AREA |