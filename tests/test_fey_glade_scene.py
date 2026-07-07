"""Fey Glade scene setup — Turn 0 transcript.

Instantiates the Fey Glade scene with Aeliana, Fennel, and the Shadowbeast,
including their neurochemical condition vectors and zone positions.

Run with:  python -m pytest tests/test_fey_glade_scene.py -s
"""

import pytest
from pathlib import Path

from engine.md_loader import configure_from_md
from models.game_init import initialize_game_state
from models.game_state import GameState
from models.character import Character, Creature, PlayerCharacter, NPC
from models.scene import Scene
from models.condition import (
    NeurochemicalState,
    DimensionProfile,
    CharacterCondition,
    render_condition,
    write_condition_md,
    DIMENSIONS,
)

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "scenario"


# ---------------------------------------------------------------------------
# Neurochemical conditions — Turn 0, from the scene PDF and MODEL.md
# ---------------------------------------------------------------------------

def _aeliana_condition() -> CharacterCondition:
    """Aeliana: tracking mode, alert, calm, no threat detected yet."""
    return CharacterCondition(
        character_id="aeliana",
        character_name="Aeliana Moonglade",
        turn=0,
        situation="Approaching the Fey Glade, following shadowbeast tracks",
        state=NeurochemicalState(
            dopamine=0.88,        # above baseline — tracking quarry, reward circuits active
            cortisol=0.28,        # low — no immediate threat detected
            norepinephrine=0.60,  # near baseline — alert but calm
            endorphins=0.75,      # well rested, physically good
            serotonin=0.70,       # stable — comfortable in wilderness
            acetylcholine=0.80,   # tracking mode — noticing everything
            oxytocin=0.55,        # baseline — alone, moderate openness
        ),
        profiles={
            "dopamine":        DimensionProfile(baseline=0.65, volatility=0.70),
            "cortisol":        DimensionProfile(baseline=0.40, volatility=0.60),
            "norepinephrine":  DimensionProfile(baseline=0.60, volatility=0.70),
            "endorphins":      DimensionProfile(baseline=0.70, volatility=0.40),
            "serotonin":       DimensionProfile(baseline=0.65, volatility=0.50),
            "acetylcholine":   DimensionProfile(baseline=0.75, volatility=0.80),
            "oxytocin":        DimensionProfile(baseline=0.55, volatility=0.60),
        },
        extensions={
            "obelisk_dopamine_response": 0.70,
            "obelisk_acetylcholine_response": 0.65,
        },
    )


def _fennel_condition() -> CharacterCondition:
    """Fennel: exhausted, hungry, hypervigilant, three days of isolation."""
    return CharacterCondition(
        character_id="fennel",
        character_name="Fennel Ashwick",
        turn=0,
        situation="Sheltering in glade for 3 days, shadowbeast at boundary",
        state=NeurochemicalState(
            dopamine=0.30,        # low — stuck, no progress, losing hope
            cortisol=0.72,        # elevated — constant threat, sleep-deprived
            norepinephrine=0.65,  # elevated — hypervigilant from days of watching
            endorphins=0.25,      # depleted — hungry, exhausted, no rest
            serotonin=0.30,       # low — isolated, frightened, impulse control fraying
            acetylcholine=0.70,   # still alert — survival demands attention
            oxytocin=0.20,        # very low — alone for three days, no social contact
        ),
        profiles={
            "dopamine":        DimensionProfile(baseline=0.55, volatility=0.60),
            "cortisol":        DimensionProfile(baseline=0.35, volatility=0.80),
            "norepinephrine":  DimensionProfile(baseline=0.45, volatility=0.70),
            "endorphins":      DimensionProfile(baseline=0.60, volatility=0.50),
            "serotonin":       DimensionProfile(baseline=0.60, volatility=0.65),
            "acetylcholine":   DimensionProfile(baseline=0.55, volatility=0.60),
            "oxytocin":        DimensionProfile(baseline=0.55, volatility=0.80),
        },
    )


def _shadowbeast_condition() -> CharacterCondition:
    """Shadowbeast: patient, alert, predatory focus, boundary frustration."""
    return CharacterCondition(
        character_id="shadowbeast_fey_glade",
        character_name="Shadowbeast",
        turn=0,
        situation="Patrolling TREELINE perimeter, prey in GLADE for 3 days",
        state=NeurochemicalState(
            dopamine=0.90,        # obelisk pull — constant high, drive never drops
            cortisol=0.35,        # low — apex predator, not threatened
            norepinephrine=0.80,  # high — hair-trigger reactivity
            endorphins=0.50,      # adequate — predator in its element
            serotonin=0.00,       # none — no impulse control, alignment marker
            acetylcholine=0.85,   # high — tracking mode, noticing everything
            oxytocin=0.00,        # none — no bonding capacity, alignment marker
        ),
        profiles={
            "dopamine":        DimensionProfile(baseline=0.90, volatility=0.30),
            "cortisol":        DimensionProfile(baseline=0.35, volatility=0.90),
            "norepinephrine":  DimensionProfile(baseline=0.70, volatility=0.85),
            "endorphins":      DimensionProfile(baseline=0.50, volatility=0.30),
            "serotonin":       DimensionProfile(baseline=0.00, volatility=0.00),
            "acetylcholine":   DimensionProfile(baseline=0.80, volatility=0.70),
            "oxytocin":        DimensionProfile(baseline=0.00, volatility=0.00),
        },
    )


# ---------------------------------------------------------------------------
# Zone tracking for the scene
# ---------------------------------------------------------------------------

ZONES = ["TRAIL", "TREELINE", "GLADE", "POOL"]
ADJACENCY = {
    "TRAIL": ["TREELINE"],
    "TREELINE": ["TRAIL", "GLADE"],
    "GLADE": ["TREELINE", "POOL"],
    "POOL": ["GLADE"],
}
STARTING_ZONES = {
    "aeliana": "TRAIL",
    "fennel": "GLADE",
    "shadowbeast_fey_glade": "TREELINE",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def gs():
    return initialize_game_state(SCENARIO_DIR)


@pytest.fixture(scope="module")
def fey_glade_characters(gs):
    aeliana = gs.get_character("aeliana")
    fennel = gs.get_character("fennel")
    shadowbeast = gs.get_character("shadowbeast_fey_glade")
    assert aeliana is not None, "aeliana not loaded"
    assert fennel is not None, "fennel not loaded"
    assert shadowbeast is not None, "shadowbeast_fey_glade not loaded"
    return {
        "aeliana": aeliana,
        "fennel": fennel,
        "shadowbeast_fey_glade": shadowbeast,
    }


@pytest.fixture(scope="module")
def conditions():
    return {
        "aeliana": _aeliana_condition(),
        "fennel": _fennel_condition(),
        "shadowbeast_fey_glade": _shadowbeast_condition(),
    }


CHARACTER_ORDER = ["aeliana", "shadowbeast_fey_glade", "fennel"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFeyGladeSetup:
    def test_scene_exists(self, gs):
        scene = gs.get_scene_at("fey_glade")
        assert scene is not None
        assert scene.status == "active"

    def test_aeliana_at_fey_glade(self, gs):
        aeliana = gs.get_character("aeliana")
        assert aeliana is not None
        assert aeliana.location == "fey_glade"

    def test_fennel_added(self, fey_glade_characters):
        fennel = fey_glade_characters["fennel"]
        assert fennel.name == "Fennel Ashwick"
        assert fennel.location == "fey_glade"
        assert isinstance(fennel, NPC)

    def test_shadowbeast_added(self, fey_glade_characters):
        sb = fey_glade_characters["shadowbeast_fey_glade"]
        assert sb.name == "Shadowbeasts"
        assert sb.character_type == "creature"
        assert isinstance(sb, Creature)

    def test_shadowbeast_stats(self, fey_glade_characters):
        sb = fey_glade_characters["shadowbeast_fey_glade"]
        assert sb.hp == 12
        assert sb.ac == 11
        assert sb.dexterity == 14
        assert sb.speed == "40 ft"

    def test_player_ac_is_dynamic_but_npc_ac_is_authored(self, gs, fey_glade_characters):
        cfg = configure_from_md(Path("scenes/fey_glade.md"))
        aeliana = cfg.characters["aeliana"].character
        fennel = fey_glade_characters["fennel"]

        assert aeliana is not None
        assert aeliana.natural_ac == 10
        assert aeliana.ac == 14  # leather armor 11 + DEX 3

        assert fennel.natural_ac == 10
        assert fennel.ac == 11   # game-state template preserves authored AC

    def test_fennel_has_soul(self, fey_glade_characters):
        fennel = fey_glade_characters["fennel"]
        assert fennel.soul_raw, "Fennel SOUL.md should be loaded"
        assert "Moonlace" in fennel.soul_raw

    def test_three_characters_in_scene(self, gs, fey_glade_characters):
        chars = gs.get_characters_at("fey_glade")
        ids = {c.id for c in chars}
        assert "aeliana" in ids
        assert "fennel" in ids
        assert "shadowbeast_fey_glade" in ids

    def test_zone_adjacency(self):
        assert "TREELINE" in ADJACENCY["TRAIL"]
        assert "TRAIL" in ADJACENCY["TREELINE"]
        assert "GLADE" in ADJACENCY["TREELINE"]
        assert "POOL" in ADJACENCY["GLADE"]

    def test_starting_zones(self):
        assert STARTING_ZONES["aeliana"] == "TRAIL"
        assert STARTING_ZONES["fennel"] == "GLADE"
        assert STARTING_ZONES["shadowbeast_fey_glade"] == "TREELINE"


class TestFeyGladeConditions:
    def test_aeliana_tracking_mode(self, conditions):
        cc = conditions["aeliana"]
        assert cc.state.acetylcholine >= 0.75  # tracking
        assert cc.state.cortisol < 0.40         # no threat detected
        assert cc.state.dopamine > 0.80         # reward circuits active

    def test_fennel_depleted(self, conditions):
        cc = conditions["fennel"]
        assert cc.state.endorphins < 0.30       # exhausted, hungry
        assert cc.state.oxytocin < 0.25         # isolated
        assert cc.state.cortisol > 0.65         # elevated threat

    def test_shadowbeast_predatory(self, conditions):
        cc = conditions["shadowbeast_fey_glade"]
        assert cc.state.dopamine >= 0.90        # obelisk pull — constant high
        assert cc.state.acetylcholine >= 0.80   # high alertness
        assert cc.state.norepinephrine >= 0.75  # hair-trigger reactivity
        assert cc.state.serotonin == 0.00       # no impulse control
        assert cc.state.oxytocin == 0.00        # no bonding capacity

    def test_all_conditions_render(self, conditions):
        for cid, cc in conditions.items():
            text = render_condition(cc)
            assert "CURRENT STATE:" in text
            assert len(text) > 100, f"{cid} render too short"

    def test_aeliana_extensions(self, conditions):
        cc = conditions["aeliana"]
        assert "obelisk_dopamine_response" in cc.extensions
        assert "obelisk_acetylcholine_response" in cc.extensions


# ---------------------------------------------------------------------------
# Transcript test — run with -s to see output
# ---------------------------------------------------------------------------

def test_fey_glade_transcript(gs, fey_glade_characters, conditions, capsys):
    scene = gs.get_scene_at("fey_glade")
    place = gs.get_place("fey_glade")

    print()
    print("=" * 70)
    print("  FEY GLADE — TURN 0 SCENE SETUP")
    print("=" * 70)
    print()
    print(f"  Scene: {scene.id}")
    print(f"  Location: {place.name}")
    print(f"  Status: {scene.status}")
    print(f"  Turn: 0")
    print(f"  Clock: Dusk in ~3 hours (mid-afternoon)")
    print(f"  Tension: Rising — Aeliana approaching shadowbeast position")
    print()

    # Zone layout
    print("  ZONES:")
    print("    TRAIL → TREELINE → GLADE → POOL")
    print()

    # Characters and positions
    print("  CHARACTERS:")
    for cid in CHARACTER_ORDER:
        char = fey_glade_characters[cid]
        zone = STARTING_ZONES[cid]
        tag = "PC" if isinstance(char, PlayerCharacter) else char.character_type.upper()
        print(f"    [{tag}] {char.name} — {zone}")
        if char.physical_description:
            desc = char.physical_description[:80]
            print(f"          {desc}...")
    print()

    # Scene flags
    print("  SCENE FLAGS:")
    print("    • fennel_memory_degradation_active")
    print("    • pool_cycle_approaching (dusk in 3 hours)")
    print("    • shadowbeast_unaware_of_aeliana (fragile)")
    print()

    # What each character knows
    print("  WHAT EACH CHARACTER KNOWS:")
    print()
    print("    Aeliana:")
    print("      • Tracking shadowbeasts northeast from Driftmoor")
    print("      • Tracks go cold ahead")
    print("      • Air smells different — warmer, sweeter")
    print("      • Does NOT know about Fennel, the glade, or the pool")
    print()
    print("    Fennel:")
    print("      • Shadowbeast at TREELINE as usual")
    print("      • Someone approaching on TRAIL")
    print("      • Cannot call out — sound draws the shadowbeast")
    print("      • Has bow + six arrows")
    print()
    print("    Shadowbeast:")
    print("      • Fennel in GLADE — same as always")
    print("      • Something new on TRAIL — not yet detected")
    print("      • Boundary holds")
    print()

    # Neurochemical conditions
    print("  NEUROCHEMICAL CONDITIONS:")
    print()
    for cid in CHARACTER_ORDER:
        cc = conditions[cid]
        print(f"    --- {cc.character_name} (Turn {cc.turn}) ---")
        print(f"    Situation: {cc.situation}")
        rendered = render_condition(cc)
        for line in rendered.splitlines():
            print(f"    {line}")
        if cc.extensions:
            print(f"    Extensions: {cc.extensions}")
        print()

    print("=" * 70)

    # Assertions
    assert len(fey_glade_characters) == 3
    assert len(conditions) == 3
    assert scene is not None
    for cid in ["aeliana", "fennel", "shadowbeast_fey_glade"]:
        assert cid in conditions
        assert cid in STARTING_ZONES
