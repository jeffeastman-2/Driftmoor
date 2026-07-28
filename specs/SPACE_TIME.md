# SPACE_TIME.md — Spatial and Temporal Architecture
## Driftmoor Engine Design Specification

---

## Overview

This document specifies the spatial coordinate system and time
tracking model for the Driftmoor engine. It is a separate concern
from the neurochemical model (MODEL.md) and prompt assembly
(TURN_PROMPT_DESIGN.md).

The coordinate system is inspired by ENGRAF (Eastman, 1975) —
a system that parsed natural language scene descriptions into
geometric representations. Driftmoor inverts this: geometric
representations generate natural language descriptions for
LLM agents. The grounding relationship is the same; the
direction of traversal is reversed.

---

## 1. The Coordinate System

### 1.1 Three-Dimensional Position

Every entity — character, item, landmark, zone boundary —
has a position in 3D space.

```python
@dataclass
class Position:
    x: float    # east-west (east is positive)
    y: float    # north-south (north is positive)
    z: float    # elevation and dungeon level
                # 0.0    = ground level, sea level reference
                # > 0.0  = above ground (floors, cliffs, towers)
                # < 0.0  = below ground (cellars, dungeons, caverns)

    def distance_to(self, other: Position) -> float:
        return sqrt((self.x - other.x)**2 +
                    (self.y - other.y)**2 +
                    (self.z - other.z)**2)

    def horizontal_distance_to(self, other: Position) -> float:
        # Ignores z — for movement cost on same level
        return sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
```

### 1.2 Units

All distances in **meters**.

```
1 unit = 1 meter
Standard grid square = 1.5 meters (optional display layer)
Character speed = meters per turn (see section 4)
```

### 1.3 Z Conventions

```
z =  0.0   Ground level / sea level
z =  1.0   One floor up (approximately 3 meters)
z =  2.0   Two floors up
z = -1.0   One level underground
z = -2.0   Two levels underground
z = -0.5   Partial below ground (cellar, sunken floor)

Fractional z for elevation within a level:
z =  0.3   Low hill (church rise above Driftmoor)
z =  0.6   Moderate elevation (Obelisk Reach cliffs)
z =  1.5   Watchtower observation platform
z = -0.2   Slightly sunken (mill ground floor, river grade)
```

---

## 2. Scene Geometry

### 2.1 SceneGeometry Object

Every place with spatial significance has a SceneGeometry
object. Simple places (single room, no sub-spaces) have
minimal geometry. Complex places (town, dungeon, multi-floor
building) have full geometry.

```python
@dataclass
class SceneGeometry:
    name: str
    place_path: str              # reference to PLACE.md
    z_level: float               # primary z level of this scene
    width: float                 # bounding box east-west (meters)
    height: float                # bounding box north-south (meters)
    origin: Position             # southwest corner, absolute coords

    landmarks: dict[str, Position]   # named fixed points
    zones: dict[str, Polygon]        # named zone boundaries
    impassable: list[Polygon]        # walls, water, dense brush
    connections: dict[str, Position] # named exits to other scenes

    def absolute_position(self, local: Position) -> Position:
        # Convert local scene coordinates to world coordinates
        return Position(
            x=self.origin.x + local.x,
            y=self.origin.y + local.y,
            z=self.origin.z + local.z,
        )
```

### 2.2 Polygon Zones

Zone boundaries are defined as polygons in local scene
coordinates (origin at southwest corner of scene).

```python
@dataclass
class Polygon:
    vertices: list[tuple[float, float]]  # (x, y) pairs

    def contains(self, point: Position) -> bool:
        # Point-in-polygon test (ray casting)
        ...

    def boundary_distance(self, point: Position) -> float:
        # Distance from point to nearest boundary edge
        ...
```

### 2.3 Fey Glade Geometry (worked example)

```python
fey_glade = SceneGeometry(
    name="The Fey Glade",
    place_path="places/mistwood_hills/fey_glade",
    z_level=0.2,      # slight elevation in the hills
    width=24.0,
    height=36.0,
    origin=Position(x=1260.0, y=2640.0, z=0.2),  # world coords

    landmarks={
        "trail_entrance":   Position(12, 0),
        "treeline_south":   Position(12, 9),
        "glade_center":     Position(12, 18),
        "oak_west":         Position(6, 15),   # Fennel's cover
        "oak_east":         Position(18, 15),
        "pool_surface":     Position(12, 28.5),
        "carved_stone":     Position(11, 27.5), # pool edge, slightly west
        "pool_north_bank":  Position(12, 30),
    },

    zones={
        "TRAIL": Polygon([
            (0, 0), (24, 0), (24, 9), (0, 9)
        ]),
        "TREELINE": Polygon([
            (0, 9), (24, 9), (24, 15), (0, 15)
        ]),
        "GLADE": Polygon([
            (0, 15), (24, 15), (24, 25.5), (0, 25.5)
        ]),
        "POOL": Polygon([
            (4.5, 25.5), (19.5, 25.5), (19.5, 36), (4.5, 36)
        ]),
    },

    impassable=[
        # Dense brush on east and west sides of trail
        Polygon([(0, 0), (4.5, 0), (4.5, 15), (0, 15)]),
        Polygon([(19.5, 0), (24, 0), (24, 15), (19.5, 15)]),
        # Pool surface (impassable without swimming/magic)
        Polygon([(6, 27), (18, 27), (18, 36), (6, 36)]),
    ],

    connections={
        "trail_south":  Position(12, 0),   # → Mistwood Hills path
        "treeline_gap": Position(12, 9),   # → forest perimeter
    }
)

# Character starting positions (Turn 0)
TURN_0_POSITIONS = {
    "aeliana":    Position(12, 3.5),   # TRAIL, approaching center
    "fennel":     Position(10.5, 15.5), # GLADE edge, near west oak
    "shadowbeast": Position(12, 10.5),  # TREELINE, boundary side
}
```

### 2.4 The Shadowbeast Boundary

The glade boundary that stops the shadowbeast is not a zone
boundary — it is a separate geometric object with magical
properties:

```python
@dataclass
class MagicalBoundary:
    name: str
    perimeter: Polygon    # the boundary line
    blocks: list[str]     # entity types blocked
    effect: str           # what happens at boundary

fey_glade_boundary = MagicalBoundary(
    name="Fey Glade Repulsion Boundary",
    perimeter=Polygon([  # runs along inner TREELINE edge
        (0, 14.5), (24, 14.5), (24, 15.5), (0, 15.5)
        # Simplified — real boundary follows glade perimeter
    ]),
    blocks=["shadowbeast", "shadow_creature", "undead"],
    effect="wrongness — body stops, cannot cross"
)
```

---

## 3. World Map and Multi-Scene Coordinates

### 3.1 World Coordinate System

All scenes exist within a single world coordinate space.
Scene origins are set once and never change.

```python
# Approximate world coordinates for Driftmoor region
# Origin (0,0,0) = center of Driftmoor town square
# 1 unit = 1 meter

WORLD_ORIGINS = {
    # Driftmoor Town (z=0, sea level)
    "driftmoor":              Position(0, 0, 0),
    "mayors_hall":            Position(-60, 30, 0),
    "broken_lantern":         Position(15, 24, 0),
    "salt_and_iron":          Position(-30, 0, 0),
    "bitter_remedy":          Position(90, -60, 0),
    "beacon_church":          Position(-15, 120, 9),    # z=9: on the rise
    "forge":                  Position(-240, -90, 0),
    "stables":                Position(-225, -110, 0),
    "corral":                 Position(-195, -105, 0),
    "dustcloaks_curios":      Position(-360, 180, 0),   # near Mistwood edge
    "elyssa_cottage":         Position(150, 240, 4.5),  # z=4.5: low hill

    # Surrounding Region
    "old_mill":               Position(600, 1200, -3),   # upriver, lower grade
    "willowford_bridge":      Position(540, 600, 0),
    "obelisk_reach":          Position(-150, 2400, 60),  # z=60: cliffs
    "shattered_obelisk":      Position(-150, 2700, 66),
    "echoing_caverns":        Position(-180, 2730, -15), # z=-15: underground

    # Mistwood Hills
    "mistwood_hills":         Position(900, 1800, 15),
    "fey_glade":              Position(1260, 2640, 6),
    "old_watchtower":         Position(840, 2160, 24),   # z=24: hilltop

    # Azure Sea
    "driftmoor_harbor":       Position(0, -300, 0),
    "sea_stacks":             Position(-150, -600, 0),
    "drowned_isle":           Position(240, -900, -1.5), # z=-1.5: partially submerged

    # Plains of Stonehearth
    "plains_of_stonehearth":  Position(600, -600, 3),
}
```

### 3.2 Multi-Level Dungeons

Dungeons and multi-floor buildings use z levels:

```python
# Echoing Caverns — three underground levels
echoing_caverns_levels = {
    "entrance":  SceneGeometry(z_level=-15,  ...),  # cliff face entry
    "level_1":   SceneGeometry(z_level=-24,  ...),  # first chamber
    "level_2":   SceneGeometry(z_level=-36,  ...),  # ancient chamber
    "level_3":   SceneGeometry(z_level=-48,  ...),  # deepest — embedded fragment
}

# Old Mill — two floors
old_mill_levels = {
    "ground_floor": SceneGeometry(z_level=-3,  ...),  # river grade
    "upper_floor":  SceneGeometry(z_level=0,   ...),  # living quarters
}

# Mayor's Hall — two floors
mayors_hall_levels = {
    "ground_floor": SceneGeometry(z_level=0,  ...),
    "upper_floor":  SceneGeometry(z_level=3,  ...),  # living quarters
}
```

### 3.3 Scene Connections as Portals

Transitions between scenes are defined as portal pairs:

```python
@dataclass
class Portal:
    from_scene: str
    from_position: Position
    to_scene: str
    to_position: Position
    traversal_cost: float  # meters of movement to use portal
    conditions: list[str]  # "requires_key", "locked", "magical" etc.
    direction_label: str   # "north", "upstairs", "down the cliff path"

# Example portals
PORTALS = [
    Portal(
        from_scene="fey_glade",
        from_position=Position(12, 0),
        to_scene="mistwood_hills",
        to_position=Position(1260, 2625, 6),
        traversal_cost=1.5,
        conditions=[],
        direction_label="south along the trail",
    ),
    Portal(
        from_scene="echoing_caverns/entrance",
        from_position=Position(3, 1.5, -15),
        to_scene="echoing_caverns/level_1",
        to_position=Position(3, 1.5, -24),
        traversal_cost=9.0,
        conditions=[],
        direction_label="down the shaft",
    ),
]
```

---

## 4. Movement

### 4.1 Character Speed

Speed in meters per turn, from D&D 5e:

```python
BASE_SPEEDS = {
    "human":      9,
    "wood_elf":   10.5,
    "half_elf":   9,
    "dwarf":      7.5,
    "halfling":   7.5,
    "dragonborn": 9,
    "shadowbeast": 12,  # predator — faster than humanoids
}
```

### 4.2 Movement Cost

```python
def movement_cost(
    from_pos: Position,
    to_pos: Position,
    terrain: str = "normal"
) -> float:
    base = from_pos.horizontal_distance_to(to_pos)
    multipliers = {
        "normal":       1.0,
        "difficult":    2.0,   # dense brush, rubble, shallow water
        "climbing":     2.0,   # vertical movement (z change)
        "swimming":     2.0,
        "crawling":     2.0,
        "sneaking":     1.0,   # no cost penalty, but norepinephrine check
    }
    return base * multipliers.get(terrain, 1.0)

def can_reach(
    character,
    target_pos: Position,
    scene: SceneGeometry
) -> bool:
    cost = movement_cost(character.position, target_pos)
    return cost <= character.speed
```

### 4.3 D&D Diagonal Movement

D&D 5e uses a simplification: diagonal movement costs the
same as cardinal movement (1.5 meters per square). This avoids
Pythagorean calculation at the table.

The engine uses true Euclidean distance internally but can
apply the D&D diagonal simplification for display and
action cost calculations:

```python
def dnd_distance(from_pos: Position, to_pos: Position) -> float:
    # Chebyshev distance — same as D&D diagonal rule
    dx = abs(from_pos.x - to_pos.x)
    dy = abs(from_pos.y - to_pos.y)
    return max(dx, dy)  # simplified
```

### 4.4 Elevation and Vertical Movement

Vertical movement (z changes) costs double:

```python
def vertical_cost(from_z: float, to_z: float) -> float:
    return abs(from_z - to_z) * 2.0
```

Falling is free but has consequences handled by DM-Left.

---

## 5. Visibility and Line of Sight

### 5.1 Observation Range

```python
@dataclass
class ObservationProfile:
    base_range: float        # meters, normal conditions
    darkvision_range: float  # meters, in darkness (0 if none)
    perception_modifier: int # from acetylcholine/Perception skill

BASE_OBSERVATION = {
    "human":      ObservationProfile(18, 0,  0),
    "wood_elf":   ObservationProfile(18, 18, 2),  # darkvision
    "shadowbeast":ObservationProfile(36, 36, 4), # predator senses
}
```

### 5.2 Line of Sight

```python
def has_line_of_sight(
    observer: Position,
    target: Position,
    scene: SceneGeometry
) -> bool:
    # Ray casting against impassable polygons
    ray = LineSegment(observer, target)
    for obstacle in scene.impassable:
        if ray.intersects(obstacle):
            return False
    return True

def can_observe(
    observer_character,
    target_position: Position,
    scene: SceneGeometry
) -> bool:
    distance = observer_character.position.horizontal_distance_to(
        target_position
    )
    profile = observer_character.observation_profile
    in_range = distance <= profile.base_range
    los = has_line_of_sight(
        observer_character.position,
        target_position,
        scene
    )
    return in_range and los
```

### 5.3 Visibility Conditions

```python
VISIBILITY_MODIFIERS = {
    "bright_light":  1.0,   # full range
    "dim_light":     0.5,   # half range (or darkvision)
    "darkness":      0.0,   # zero unless darkvision
    "fog":           0.3,   # heavy fog — 30% range
    "light_fog":     0.6,
    "rain":          0.7,
    "pool_shimmer":  0.8,   # the pool's light helps but distracts
}
```

### 5.4 Sound Detection

The shadowbeast uses sound rather than sight. A separate
acoustic detection model:

```python
def can_hear(
    listener_position: Position,
    sound_position: Position,
    sound_volume: str,  # "whisper", "normal", "loud", "shout"
    scene: SceneGeometry
) -> bool:
    distance = listener_position.distance_to(sound_position)
    hearing_ranges = {
        "whisper": 3,
        "normal":  18,
        "loud":    36,
        "shout":   90,
    }
    max_range = hearing_ranges[sound_volume]
    # Sound partially blocked by dense vegetation
    obstruction = acoustic_obstruction(
        listener_position, sound_position, scene
    )
    effective_range = max_range * (1 - obstruction)
    return distance <= effective_range
```

---

## 6. Time Tracking

### 6.1 GameTime Object

```python
@dataclass
class GameTime:
    hour: int            # 0-23
    minute: int          # 0-59
    day: int             # campaign day (1-indexed)
    season: str          # spring/summer/autumn/winter
    turn_duration: int   # minutes per turn (mode-dependent)
    absolute_turn: int   # total turns elapsed since session start

    @property
    def period(self) -> str:
        if   4 <= self.hour < 6:   return "dawn"
        elif 6 <= self.hour < 12:  return "morning"
        elif 12 <= self.hour < 14: return "midday"
        elif 14 <= self.hour < 18: return "afternoon"
        elif 18 <= self.hour < 20: return "dusk"
        elif 20 <= self.hour < 23: return "evening"
        else:                       return "night"

    @property
    def is_dark(self) -> bool:
        return self.period in ["evening", "night", "dawn"]

    def advance(self, turns: int = 1) -> None:
        minutes = self.turn_duration * turns
        self.minute += minutes
        while self.minute >= 60:
            self.minute -= 60
            self.hour += 1
        while self.hour >= 24:
            self.hour -= 24
            self.day += 1

    def minutes_until(self, target_hour: int) -> int:
        current_minutes = self.hour * 60 + self.minute
        target_minutes = target_hour * 60
        if target_minutes <= current_minutes:
            target_minutes += 24 * 60
        return target_minutes - current_minutes

    def turns_until(self, target_hour: int) -> int:
        return self.minutes_until(target_hour) // self.turn_duration
```

### 6.2 Turn Duration Modes

```python
TURN_DURATIONS = {
    "combat":      1,    # 6 seconds (D&D standard: 1/10 minute)
                         # Using 1 minute for engine simplicity
    "exploration": 10,   # 10 minutes (D&D standard)
    "travel":      60,   # 1 hour
    "rest":        480,  # 8 hours (long rest)
    "downtime":    1440, # 1 day
}
```

DM-Left sets the turn duration based on scene type. The Fey
Glade scene is exploration mode (10 minutes per turn) unless
combat initiates (switches to combat mode, 1 minute per turn).

### 6.3 Time-Triggered Events

DM-Left checks time triggers after each turn advance:

```python
TIME_TRIGGERS = {
    "fey_glade": [
        {
            "condition": lambda t: t.period == "dusk",
            "event": "pool_cycle_brightening",
            "description": "Pool light intensifies. Shadowbeast dopamine +0.15.",
            "flags": ["pool_dusk_active"],
        },
        {
            "condition": lambda t: t.hour == 0,  # midnight
            "event": "pool_cycle_peak",
            "description": "Pool at maximum brightness. All neurochemical effects amplified.",
            "flags": ["pool_midnight_peak"],
        },
        {
            "condition": lambda t: t.period == "dawn",
            "event": "pool_cycle_dimming",
            "description": "Pool light fading. Shadowbeast dopamine returns toward baseline.",
            "flags": [],
        },
    ],
    "driftmoor": [
        {
            "condition": lambda t: t.period == "dusk",
            "event": "church_lantern_lit",
            "description": "The Beacon lantern lights on the hill. Currently flickering with dark light.",
            "flags": ["lantern_active"],
        },
    ],
}
```

### 6.4 Fey Glade Starting Time

```python
fey_glade_start_time = GameTime(
    hour=14,         # 2:00 PM
    minute=30,
    day=1,
    season="autumn",
    turn_duration=10,  # exploration mode
    absolute_turn=0,
)

# Dusk at hour 18 (6:00 PM)
# Minutes until dusk: 210 minutes
# Turns until dusk: 21 turns at 10 min/turn
# This is why "approximately 3 hours until dusk" is correct
```

---

## 7. Spatial Rendering for Prompts

The context builder converts geometric data to natural
language for character prompts. Characters never receive
raw coordinates.

### 7.1 Position Rendering

```python
def render_position(
    character,
    scene: SceneGeometry,
    observer: Character = None
) -> str:
    pos = character.position
    zone = scene.zone_at(pos)
    nearest = scene.nearest_landmark(pos)
    dist_to_nearest = pos.horizontal_distance_to(nearest.position)

    if observer:
        # Relative description from observer's perspective
        bearing = bearing_label(observer.position, pos)
        distance = observer.position.horizontal_distance_to(pos)
        range_cat = range_category(distance)
        return (f"approximately {int(distance)} meters {bearing} of you, "
                f"near the {nearest.name}")
    else:
        # Absolute description
        return (f"in the {zone}, approximately {int(dist_to_nearest)} "
                f"meters from the {nearest.name}")

def range_category(distance: float) -> str:
    if distance <= 1.5: return "melee range"
    if distance <= 9:   return "close range"
    if distance <= 18:  return "medium range"
    if distance <= 36:  return "long range"
    return "extreme range"

def bearing_label(from_pos: Position, to_pos: Position) -> str:
    dx = to_pos.x - from_pos.x
    dy = to_pos.y - from_pos.y
    angle = degrees(atan2(dy, dx))
    # Convert to compass bearing
    if   -22.5 <= angle < 22.5:   return "east"
    elif  22.5 <= angle < 67.5:   return "northeast"
    elif  67.5 <= angle < 112.5:  return "north"
    elif 112.5 <= angle < 157.5:  return "northwest"
    elif angle >= 157.5 or angle < -157.5: return "west"
    elif -157.5 <= angle < -112.5: return "southwest"
    elif -112.5 <= angle < -67.5:  return "south"
    else:                           return "southeast"
```

### 7.2 Time Rendering

```python
def render_time(game_time: GameTime) -> str:
    period = game_time.period
    turns_to_dusk = game_time.turns_until(18)
    minutes_to_dusk = turns_to_dusk * game_time.turn_duration

    if minutes_to_dusk > 120:
        dusk_warning = f"Dusk in approximately {minutes_to_dusk // 60} hours"
    elif minutes_to_dusk > 0:
        dusk_warning = f"Dusk in approximately {minutes_to_dusk} minutes — {turns_to_dusk} turns"
    else:
        dusk_warning = "It is dark"

    return f"{period.capitalize()}. {dusk_warning}."

# Example output:
# "Afternoon. Dusk in approximately 3 hours."
# "Afternoon. Dusk in approximately 40 minutes — 4 turns."
# "Dusk. The pool is brightening."
```

### 7.3 Available Actions from Geometry

The context builder derives MOVE options from the character's
position, speed, and scene geometry:

```python
def generate_move_actions(
    character,
    scene: SceneGeometry
) -> list[str]:
    actions = []
    speed = character.speed

    # Check reachable zones
    for zone_name, zone_polygon in scene.zones.items():
        nearest_point = zone_polygon.nearest_point(character.position)
        cost = movement_cost(character.position, nearest_point)
        if cost <= speed and zone_name != character.current_zone:
            actions.append(
                f"Move to {zone_name} "
                f"({int(cost)} meters, {int(cost/1.5)} squares)"
            )

    # Check reachable landmarks
    for landmark_name, landmark_pos in scene.landmarks.items():
        cost = movement_cost(character.position, landmark_pos)
        if cost <= speed:
            actions.append(
                f"Move to {landmark_name} "
                f"({int(cost)} meters)"
            )

    # Check portals
    for portal in scene.connections.values():
        cost = portal.traversal_cost
        if cost <= speed:
            actions.append(
                f"Exit via {portal.direction_label}"
            )

    return actions
```

---

## 8. The Town of Driftmoor as a Designed Map

Driftmoor town is a 2D scene at z=0 (sea level) with all
buildings as polygon footprints and named positions.

The town map is both:
- A geometric object used by the engine for spatial computation
- A visual artifact renderable as a 2D plot

```python
driftmoor_town = SceneGeometry(
    name="Driftmoor Town",
    place_path="places/driftmoor",
    z_level=0.0,
    width=600.0,    # meters east-west
    height=600.0,   # meters north-south
    origin=Position(-300, -300, 0),

    landmarks={
        "town_square":      Position(0, 0),
        "harbor_pier":      Position(0, -240),
        "north_road":       Position(0, 300),
        "river_road":       Position(240, 0),
    },

    # Building footprints as polygons
    # Each building is also a sub-scene with its own SceneGeometry
    zones={
        "harbor_district":  Polygon([(-180,-300),(180,-300),(180,-120),(-180,-120)]),
        "village_center":   Polygon([(-120,-120),(120,-120),(120,120),(-120,120)]),
        "outskirts_north":  Polygon([(-180,120),(180,120),(180,300),(-180,300)]),
        "outskirts_east":   Polygon([(120,-120),(300,-120),(300,120),(120,120)]),
        "outskirts_west":   Polygon([(-300,-120),(-120,-120),(-120,120),(-300,120)]),
    },
)

# Individual buildings (sub-scenes of driftmoor_town)
BUILDING_FOOTPRINTS = {
    "mayors_hall":      Polygon([(-75,15),(-45,15),(-45,45),(-75,45)]),
    "broken_lantern":   Polygon([(0,15),(36,15),(36,45),(0,45)]),
    "salt_and_iron":    Polygon([(-45,-15),(0,-15),(0,15),(-45,15)]),
    "beacon_church":    Polygon([(-30,105),(0,105),(0,135),(-30,135)]),
    # ... all buildings from places/driftmoor/
}
```

### 8.1 Map Rendering

The town map is renderable as a 2D plot using matplotlib
or similar:

```python
def render_town_map(
    scene: SceneGeometry,
    character_positions: dict[str, Position] = None,
    show_zones: bool = True,
    show_buildings: bool = True,
    output_path: str = None
) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    ax.set_aspect('equal')
    ax.set_facecolor('#1a1a2e')  # dark background

    # Draw zones
    if show_zones:
        zone_colors = {
            "harbor_district": "#1e3a5f",
            "village_center":  "#2d4a2d",
            "outskirts_north": "#3a2d1e",
            "outskirts_east":  "#3a2d1e",
            "outskirts_west":  "#3a2d1e",
        }
        for zone_name, polygon in scene.zones.items():
            color = zone_colors.get(zone_name, "#2a2a2a")
            patch = patches.Polygon(
                polygon.vertices,
                closed=True,
                facecolor=color,
                edgecolor="#444444",
                linewidth=0.5
            )
            ax.add_patch(patch)

    # Draw buildings
    if show_buildings:
        for building_name, polygon in BUILDING_FOOTPRINTS.items():
            patch = patches.Polygon(
                polygon.vertices,
                closed=True,
                facecolor="#4a3728",
                edgecolor="#8b6914",
                linewidth=1
            )
            ax.add_patch(patch)
            centroid = polygon.centroid()
            ax.text(centroid.x, centroid.y, building_name,
                   fontsize=5, color="#ccaa77",
                   ha='center', va='center')

    # Draw character positions
    if character_positions:
        type_colors = {
            "player":   "#3b82f6",
            "npc":      "#10b981",
            "monster":  "#ef4444",
        }
        for char_name, pos in character_positions.items():
            color = type_colors.get(char_name, "#ffffff")
            ax.plot(pos.x, pos.y, 'o',
                   color=color, markersize=8)
            ax.text(pos.x + 3, pos.y + 3, char_name,
                   fontsize=7, color=color)

    ax.set_xlim(-330, 330)
    ax.set_ylim(-330, 330)
    ax.set_title("Driftmoor", color="#e2e8f0", fontsize=14)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight',
                   facecolor='#0f172a')
    else:
        plt.show()
```

---

## 9. Integration with Engine

### 9.1 DM-Left Spatial Responsibilities

DM-Left owns all spatial state updates:

- Update character positions after movement actions
- Check portal transitions (scene changes)
- Compute visibility for information filtering
- Compute acoustic detection for the shadowbeast
- Evaluate time triggers after each turn
- Update GameTime
- Check magical boundary interactions

### 9.2 Context Builder Spatial Input

The context builder receives spatial state from DM-Left
and uses it to:

- Generate MOVE options (from `generate_move_actions`)
- Render positions for scene descriptions
- Determine what each character can observe
- Compute range categories for combat/interaction options
- Render current time and time-sensitive warnings

### 9.3 Relationship to MODEL.md

Spatial state and neurochemical state are independent but
interact through events:

```python
# Spatial events that trigger neurochemical deltas
SPATIAL_TRIGGERS = {
    "enters_darkness": {
        "cortisol":       +0.10,
        "norepinephrine": +0.10,
    },
    "obelisk_shard_within_10m": {
        # Aeliana's extension dimensions fire here
        "aeliana.obelisk_dopamine_response":     +0.20,
        "aeliana.obelisk_acetylcholine_response": +0.15,
        "cortisol": +0.05,  # all characters
    },
    "shadowbeast_within_3m": {
        "cortisol":       +0.25,
        "norepinephrine": +0.20,
    },
    "enters_fey_glade": {
        "dopamine":      +0.10,  # warmth, beauty
        "serotonin":     +0.05,  # the glade is calming
        "acetylcholine": +0.10,  # heightened attention
    },
    "pool_proximity_within_3m": {
        "dopamine":  +0.15,  # lure effect
        "cortisol":  +0.10,  # wrongness signal
        # Fennel's memory effect fires separately
    },
}
```

---

## 10. ENGRAF Connection

This spatial model is the computational inverse of ENGRAF
(Eastman, 1975).

ENGRAF: natural language scene description
         → geometric representation

Driftmoor: geometric representation
            → natural language scene description (for LLM agents)

The vector-semantic grounding that ENGRAF pioneered —
representing scene understanding as vectors in a semantic
space — anticipates the neurochemical condition vectors
in MODEL.md. Both are grounding mechanisms: ENGRAF grounds
language in geometry, the condition vector grounds behavior
in physiology.

The coordinate system, polygon zones, line-of-sight
computation, and landmark-relative position description
are all present in the 1975 dissertation. The LLM agents
that consume the rendered output are new. The geometry
beneath them is fifty years old.

---

## 11. Implementation Priority

Suggested build order:

1. `Position` dataclass with distance methods
2. `Polygon` with contains() and nearest_point()
3. `SceneGeometry` with zone_at() and nearest_landmark()
4. `GameTime` with advance() and period property
5. Fey Glade geometry (worked example, validation target)
6. Position renderer (coordinates → natural language)
7. Time renderer (GameTime → prompt text)
8. Move action generator
9. Visibility / line-of-sight computation
10. Acoustic detection (for shadowbeast)
11. Spatial triggers → neurochemical deltas (integrates with MODEL.md)
12. Town map renderer (matplotlib)
13. World coordinate system (all scene origins)
14. Portal system (scene transitions)

The Fey Glade geometry in section 2.3 provides a complete
worked example for steps 1-10. Validate against ground truth
outputs in `docs/fey_glade_experiment/ground_truth.md`.

---

## 12. File Locations

```
models/space_time.py     # Position, Polygon, SceneGeometry,
                         # GameTime, Portal, MagicalBoundary
models/world_map.py      # World coordinate origins, all scene geometries
engine/spatial.py        # Visibility, movement, acoustic detection
engine/time_manager.py   # GameTime management, trigger evaluation
engine/map_renderer.py   # 2D map plotting (matplotlib)
scenarios/driftmoor/
  geometry/
    fey_glade.py         # Fey Glade SceneGeometry instance
    driftmoor_town.py    # Town map with all building footprints
    echoing_caverns.py   # Multi-level dungeon geometry
    old_mill.py          # Two-floor mill geometry
    # ... one file per complex scene
```
