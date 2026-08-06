# GEOMETRY.md — The Gilded Trinket (Pawn Shop)

## Scene

- **name:** The Gilded Trinket
- **place_path:** places/driftmoor/gilded_trinket
- **z_level:** 16.25
- **width:** 24.375
- **height:** 29.25
- **origin:** 371.5, 252, 0

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
| front_door      | 11  | 0  |
| display_case    | 18.156 | 2.521 |
| counter         | 11.895  | 13.067 |
| obsidian_ring   | 12.059 | 25.492 |
| safe             | 21 | 24 |
| shelves_west    | 2  | 11  |
| shelves_east    | 22 | 11  |
| oil_lamp_main   | 10.012  | 13.156  |
| curio_table_w   | 7   | 8   |
| curio_table_e   | 17  | 8   |
| weapon_rack     | 2.742   | 24.336  |
| private_desk    | 10.73  | 26.168  |

---

## Zones

| name | render_z | auto_wall | vertices |
|------------|----------|---------|---------------------------------------|
| BACK_AREA | 6.5 |  | (0,19.5) (24,19.5) (24,29) (0,29) |
| SHOPFRONT | 3.25 |  | (0,0) (24,0) (24,19.5) (0,19.5) |
| EXTERIOR | 0.0 |  | (-8,-8) (32.5,-8) (32.5,37) (-8,37) |
---

## Impassable

| description        | vertices                              |
|--------------------|---------------------------------------|
| Counter barrier    | (6.5,16) (22.5,16) (22.5,17.5) (6.5,17.5)         |
| Grated windows E   | (22.5,4.5) (24,4.5) (24,13) (22.5,13)           |
| Grated windows W   | (0,4.5) (1.5,4.5) (1.5,13) (0,13)               |
| Safe alcove wall   | (17.5,22.5) (24,22.5) (24,29) (17.5,29)       |

---

## Connections

| name          | x    | y    | destination      |
|---------------|------|------|------------------|
| front_door    | 11  | 0  | places/driftmoor |
| back_door     | 11  | 29 | places/driftmoor |

---

## Boundaries

### Tavian's Counter Line

- **type:** conditional
- **blocks:** all
- **render:** hidden
- **effect:** counter marks the boundary of Tavian's domain; crossing without permission triggers immediate hostile response
- **vertices:** (0,16) (24,16) (24,29) (0,29)

### Display Case — Obelisk Ring Aura

- **type:** magical
- **blocks:** none
- **render:** hidden
- **effect:** the obsidian ring pulses with obelisk energy; characters with obelisk shard attunement feel drawn toward it; Perception DC 45.5 to notice the pulse
- **vertices:** (11,16) (22.5,16) (22.5,22.5) (11,22.5)

---
