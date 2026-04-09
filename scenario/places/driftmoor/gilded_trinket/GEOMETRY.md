# GEOMETRY.md — The Gilded Trinket (Pawn Shop)

## Scene

- **name:** The Gilded Trinket
- **place_path:** places/driftmoor/gilded_trinket
- **z_level:** 5.0
- **width:** 15.0
- **height:** 18.0
- **origin:** 2842.0, 2468.0, 5.0

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
| front_door      | 7.0  | 0.0  |
| display_case    | 10.0 | 12.0 |
| counter         | 8.0  | 11.0 |
| obsidian_ring   | 10.5 | 13.0 |
| safe             | 13.0 | 15.0 |
| shelves_west    | 2.0  | 8.0  |
| shelves_east    | 13.0 | 8.0  |
| oil_lamp_main   | 7.0  | 7.0  |

---

## Zones

| name       | render_z | vertices                              |
|------------|----------|---------------------------------------|
| BACK_AREA  | 2        | (0,12) (15,12) (15,18) (0,18)         |
| DISPLAY    | 2        | (7,10) (14,10) (14,14) (7,14)         |
| SHOPFRONT  | 1        | (0,0) (15,0) (15,12) (0,12)           |
| EXTERIOR   | 0        | (-5,-5) (20,-5) (20,23) (-5,23)       |

---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Counter barrier    | (4,10) (14,10) (14,11) (4,11)         |
| Grated windows E   | (14,3) (15,3) (15,8) (14,8)           |
| Grated windows W   | (0,3) (1,3) (1,8) (0,8)               |
| Safe alcove wall   | (11,14) (15,14) (15,18) (11,18)       |

---

## Connections

| name          | x    | y    | destination      |
|---------------|------|------|------------------|
| front_door    | 7.0  | 0.0  | places/driftmoor |
| back_door     | 7.0  | 18.0 | places/driftmoor |

---

## Boundaries

### Tavian's Counter Line

- **type:** conditional
- **blocks:** all
- **effect:** counter marks the boundary of Tavian's domain; crossing without permission triggers immediate hostile response
- **vertices:** (0,10) (15,10) (15,18) (0,18)

### Display Case — Obelisk Ring Aura

- **type:** magical
- **blocks:** none
- **effect:** the obsidian ring pulses with obelisk energy; characters with obelisk shard attunement feel drawn toward it; Perception DC 14 to notice the pulse
- **vertices:** (7,10) (14,10) (14,14) (7,14)

---

## Starting Positions

| character | x    | y    | zone      |
|-----------|------|------|-----------|
| seraphina | 5.0  | 6.0  | SHOPFRONT |
| tavian    | 10.0 | 12.0 | BACK_AREA |