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
| front_door      | 22  | 0  |
| display_case    | 32 | 39 |
| counter         | 26  | 35 |
| obsidian_ring   | 34 | 42 |
| safe             | 42 | 48 |
| shelves_west    | 6  | 26  |
| shelves_east    | 42 | 26  |
| oil_lamp_main   | 22  | 22  |

---

## Zones

| name       | render_z | vertices                              |
|------------|----------|---------------------------------------|
| BACK_AREA  | 6.5        | (0,39) (48,39) (48,58) (0,58)         |
| DISPLAY    | 6.5        | (22,32) (45,32) (45,45) (22,45)         |
| SHOPFRONT  | 3.25        | (0,0) (48,0) (48,39) (0,39)           |
| EXTERIOR   | 0.0        | (-16,-16) (65,-16) (65,74) (-16,74)       |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Counter barrier    | (13,32) (45,32) (45,35) (13,35)         |
| Grated windows E   | (45,9) (48,9) (48,26) (45,26)           |
| Grated windows W   | (0,9) (3,9) (3,26) (0,26)               |
| Safe alcove wall   | (35,45) (48,45) (48,58) (35,58)       |

---

## Connections

| name          | x    | y    | destination      |
|---------------|------|------|------------------|
| front_door    | 22  | 0  | places/driftmoor |
| back_door     | 22  | 58 | places/driftmoor |

---

## Boundaries

### Tavian's Counter Line

- **type:** conditional
- **blocks:** all
- **effect:** counter marks the boundary of Tavian's domain; crossing without permission triggers immediate hostile response
- **vertices:** (0,32) (48,32) (48,58) (0,58)

### Display Case — Obelisk Ring Aura

- **type:** magical
- **blocks:** none
- **effect:** the obsidian ring pulses with obelisk energy; characters with obelisk shard attunement feel drawn toward it; Perception DC 45.5 to notice the pulse
- **vertices:** (22,32) (45,32) (45,45) (22,45)

---

## Starting Positions

| character | x    | y    | zone      |
|-----------|------|------|-----------|
| seraphina | 16  | 19  | SHOPFRONT |
| tavian    | 32 | 39 | BACK_AREA |