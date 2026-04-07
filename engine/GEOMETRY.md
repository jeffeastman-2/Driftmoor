# GEOMETRY.md FORMAT SPECIFICATION — Patch for Opus
# 
# This document specifies the canonical GEOMETRY.md format for all
# scene geometry files in the Driftmoor engine. It replaces section
# 2.3 of SPACE_TIME.md (hardcoded Python worked example) and updates
# section 12 (file locations).
#
# Key changes from current SPACE_TIME.md:
# 1. Geometry lives in GEOMETRY.md files, not Python files
# 2. Zones table adds render_z column (match order != render order)
# 3. FOREST/VOID catch-all zone is always last in match order
# 4. Sub-zones listed before parent zones (first match wins)
# 5. Scene bounding box is the outermost polygon (always FOREST/VOID)

======================================================================
SECTION 2.3 REPLACEMENT — GEOMETRY.md as canonical format
======================================================================

Every place with spatial significance has a GEOMETRY.md file located
at:

    scenarios/driftmoor/<place_path>/GEOMETRY.md

The SceneGeometry object is loaded from this file at runtime. The
Python dataclass instances in geometry/ are generated from these
files, not written by hand.

----------------------------------------------------------------------
GEOMETRY.md FILE FORMAT
----------------------------------------------------------------------

# GEOMETRY.md — <Scene Name>

## Scene

- **name:** <display name>
- **place_path:** <path to PLACE.md, without PLACE.md>
- **z_level:** <primary z level, float, sea level = 0.0>
- **width:** <bounding box east-west, metres>
- **height:** <bounding box north-south, metres>
- **origin:** <world x>, <world y>, <world z>

## Landmarks

| name | x | y |
|------|---|---|
| <name> | <local x> | <local y> |

Landmarks are named fixed points within the scene. Positions are
in local scene coordinates (origin at southwest corner).

## Zones

Zone order matters — first match wins in zone_at(). Catch-all
zone (FOREST, VOID, EXTERIOR) must always be LAST.

Sub-zones must appear BEFORE their parent zone.

| name | render_z | vertices |
|------|----------|----------|
| <name> | <int> | (x,y) (x,y) ... |

render_z is the visual stacking order for map rendering.
Higher render_z renders on top.
Match order (table row order) and render order (render_z) are
independent.

Recommended render_z values:
  0 — background catch-all (FOREST, VOID, EXTERIOR)
  1 — primary zones (TRAIL, GLADE, main rooms)
  2 — sub-zones within primary zones (POOL within GLADE)
  3 — features and landmarks
  4 — characters (assigned at render time, not in file)
  5 — overlays (magical boundaries, effects)

## Impassable

| description | vertices |
|-------------|----------|
| <description> | (x,y) (x,y) ... |

Impassable polygons block movement. Characters cannot enter these
areas without special abilities or conditions.

## Connections

| name | x | y | destination |
|------|---|---|-------------|
| <name> | <local x> | <local y> | <scene name or place_path> |

Connections are named exit points linking this scene to others.

## Boundaries

Named sections for magical or special boundaries.

### <Boundary Name>

- **type:** magical | physical | conditional
- **blocks:** <comma-separated entity types>
- **effect:** <description>
- **vertices:** (x,y) (x,y) ...

## Starting Positions

Default starting positions for characters assigned to this scene.
Override at runtime for specific scenarios.

| character | x | y | zone |
|-----------|---|---|------|
| <character_id> | <local x> | <local y> | <zone name> |

----------------------------------------------------------------------
WORKED EXAMPLE — Fey Glade (current canonical version)
----------------------------------------------------------------------

# GEOMETRY.md — The Fey Glade

## Scene

- **name:** The Fey Glade
- **place_path:** places/mistwood_hills/fey_glade
- **z_level:** 0.2
- **width:** 100.0
- **height:** 100.0
- **origin:** 1222.0, 2608.0, 0.2

## Landmarks

| name           | x    | y    |
|----------------|------|------|
| glade_center   | 50.0 | 50.0 |
| pool_surface   | 42.5 | 52.5 |
| carved_stone   | 42.0 | 52.0 |
| trail_entrance | 59.0 | 45.0 |
| oak_west       | 43.0 | 50.0 |
| oak_east       | 57.0 | 50.0 |

## Zones

Zone order matters — first match wins in zone_at(). FOREST must be last.

| name   | render_z | vertices                                    |
|--------|----------|---------------------------------------------|
| POOL   | 2        | (42,52) (43,52) (43,53) (42,53)             |
| GLADE  | 1        | (40,45) (60,45) (60,55) (40,55)             |
| TRAIL  | 1        | (59,45) (60,45) (100,4) (99,3)              |
| FOREST | 0        | (0,0) (100,0) (100,100) (0,100)             |

Notes:
- POOL (render_z=2) renders above GLADE (render_z=1) visually
- POOL listed before GLADE so positions inside pool match POOL first
- TRAIL is an organic polygon pointing southeast — not a rectangle
- FOREST is the catch-all background zone

## Impassable

| description  | vertices                        |
|--------------|---------------------------------|
| Pool surface | (42,52) (43,52) (43,53) (42,53) |

## Connections

| name       | x    | y   | destination         |
|------------|------|-----|---------------------|
| trail_exit | 99.0 | 4.0 | mistwood_hills path |

## Boundaries

### Fey Glade Repulsion Boundary

- **type:** magical
- **blocks:** shadowbeast, shadow_creature, undead
- **effect:** wrongness — body stops, cannot cross
- **vertices:** (39,44) (61,44) (61,56) (39,56)

## Starting Positions

| character   | x    | y    | zone   |
|-------------|------|------|--------|
| aeliana     | 79.0 | 25.0 | TRAIL  |
| fennel      | 44.0 | 52.0 | GLADE  |
| shadowbeast | 37.0 | 50.0 | FOREST |

----------------------------------------------------------------------
MULTI-LEVEL EXAMPLE — Echoing Caverns (three z-levels)
----------------------------------------------------------------------

Each level is a separate GEOMETRY.md file:

  places/obelisk_reach/echoing_caverns/entrance/GEOMETRY.md
  places/obelisk_reach/echoing_caverns/level_1/GEOMETRY.md
  places/obelisk_reach/echoing_caverns/level_2/GEOMETRY.md
  places/obelisk_reach/echoing_caverns/level_3/GEOMETRY.md

Each has its own z_level:
  entrance:  z_level = -15.0
  level_1:   z_level = -24.0
  level_2:   z_level = -37.0
  level_3:   z_level = -49.0  (deepest — embedded fragment)

Connections link levels:
  entrance → level_1 via "shaft_down" connection
  level_1  → entrance via "shaft_up" connection
  level_1  → level_2 via "passage_deeper"
  etc.

----------------------------------------------------------------------
SUB-ZONE EXAMPLE — Old Mill (rooms within ground floor)
----------------------------------------------------------------------

# GEOMETRY.md — Old Mill: Ground Floor

## Scene
- **name:** Old Mill Ground Floor
- **z_level:** -3.0
- **width:** 20.0
- **height:** 15.0

## Zones

| name         | render_z | vertices                              |
|--------------|----------|---------------------------------------|
| MILLSTONES   | 2        | (2,2) (10,2) (10,8) (2,8)            |
| COUNTER      | 2        | (12,2) (18,2) (18,6) (12,6)          |
| GRAIN_STORE  | 2        | (2,9) (8,9) (8,13) (2,13)            |
| GROUND_FLOOR | 1        | (0,0) (20,0) (20,15) (0,15)          |
| EXTERIOR     | 0        | (-5,-5) (25,-5) (25,20) (-5,20)      |

Notes:
- MILLSTONES, COUNTER, GRAIN_STORE all render above GROUND_FLOOR
- All listed before GROUND_FLOOR so they match first
- EXTERIOR is catch-all

======================================================================
SECTION 12 REPLACEMENT — File Locations
======================================================================

```
models/space_time.py       # Position, Polygon, SceneGeometry,
                           # GameTime, Portal, MagicalBoundary
models/world_map.py        # World coordinate origins
engine/spatial.py          # Visibility, movement, acoustic detection
engine/time_manager.py     # GameTime management, trigger evaluation
engine/geometry_loader.py  # Loads GEOMETRY.md → SceneGeometry objects
engine/map_renderer.py     # 2D map plotting (matplotlib)

scenarios/driftmoor/
  places/
    mistwood_hills/
      fey_glade/
        PLACE.md
        CONTENTS.md
        GEOMETRY.md        # ← geometry lives here, alongside PLACE.md
    driftmoor/
      GEOMETRY.md          # town bounding box and district zones
      mayors_hall/
        GEOMETRY.md
        mayors_office/
          GEOMETRY.md
        records_room/
          GEOMETRY.md
      broken_lantern/
        GEOMETRY.md
        main_room/
          GEOMETRY.md
      ...
    obelisk_reach/
      echoing_caverns/
        entrance/
          GEOMETRY.md
        level_1/
          GEOMETRY.md
        level_2/
          GEOMETRY.md
        level_3/
          GEOMETRY.md
    greywater_river/
      old_mill/
        ground_floor/
          GEOMETRY.md
        upper_floor/
          GEOMETRY.md
```

Key change: GEOMETRY.md lives alongside PLACE.md and CONTENTS.md
in the place directory. Not in a separate geometry/ folder.
Each place directory now has up to three files:
  PLACE.md       — description, atmosphere, connections, dynamic state
  CONTENTS.md    — items, creatures, DM notes
  GEOMETRY.md    — spatial geometry (optional for simple places)

Simple places (single room, no spatial complexity) do not need
GEOMETRY.md. The engine falls back to zone-less position tracking
for these.

======================================================================
GEOMETRY LOADER — geometry_loader.py
======================================================================

The geometry loader reads GEOMETRY.md files and produces
SceneGeometry objects. It does not require manual Python geometry
files.

```python
class GeometryLoader:
    def load(self, place_path: str) -> SceneGeometry | None:
        geometry_path = Path(place_path) / "GEOMETRY.md"
        if not geometry_path.exists():
            return None  # simple place, no geometry
        return self._parse(geometry_path.read_text())

    def _parse(self, content: str) -> SceneGeometry:
        # Parse markdown tables into dataclass fields
        # Sections: Scene, Landmarks, Zones, Impassable,
        #           Connections, Boundaries, Starting Positions
        ...
```

The loader replaces all hardcoded Python SceneGeometry instances
in SPACE_TIME.md section 2.3. The Fey Glade GEOMETRY.md above
is the canonical source — the Python worked example in section 2.3
is now deprecated.

======================================================================
SVG RENDERING — y-axis convention
======================================================================

World coordinates: y increases northward (standard math convention)
SVG coordinates:   y increases downward (SVG convention)

The map renderer must apply a y-flip when converting world
coordinates to SVG coordinates:

```python
def world_to_svg(
    pos: Position,
    scene: SceneGeometry,
    svg_height: float,
    scale: float
) -> tuple[float, float]:
    svg_x = (pos.x - scene.origin.x) * scale
    svg_y = svg_height - (pos.y - scene.origin.y) * scale
    return svg_x, svg_y
```

Without this flip, north appears at the bottom of the map.
This was the error in the initial plan view diagram.