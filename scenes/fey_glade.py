"""Scene configuration: Fey Glade — Aeliana, Fennel, Shadowbeast."""

from engine.llm_bridge import make_call_llm
from engine.session import CharacterSession
from engine.player_router import PlayerLeft, PlayerRight
from engine.dm_agent import DMLeft, DMRight
from engine.scene_manager import RoleSet
from engine.scene_runner import SceneConfig, ROOT, load_file
from models.character import PlayerCharacter, Creature
from models.condition import (
    CharacterCondition,
    NeurochemicalState,
    DimensionProfile,
)


def configure() -> SceneConfig:
    characters = {
        "aeliana": CharacterSession(
            character=PlayerCharacter(
                id="aeliana", name="Aeliana Moonglade", race="Wood Elf",
                character_type="player", character_class="Ranger",
                level=1, hp=12, ac=14, dexterity=16, wisdom=15,
                location="fey_glade",
            ),
            condition=CharacterCondition(
                character_id="aeliana",
                character_name="Aeliana",
                state=NeurochemicalState(
                    dopamine=0.85, cortisol=0.25, norepinephrine=0.55,
                    endorphins=0.75, serotonin=0.60, acetylcholine=0.50,
                    oxytocin=0.50,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.55, volatility=0.8),
                    "cortisol": DimensionProfile(baseline=0.35, volatility=0.6),
                },
            ),
            soul=load_file(ROOT / "scenario/people/players/aeliana/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/players/aeliana/IDENTITY.md"),
            initial_scene=(
                "You are on the trail approaching the Fey Glade. "
                "The air shimmers with unnatural warmth ahead. "
                "No sounds from the forest — unnaturally still. "
                "You sense something watching from the treeline."
            ),
        ),
        "fennel": CharacterSession(
            character=PlayerCharacter(
                id="fennel", name="Fennel", race="Human",
                character_type="player", character_class="Gatherer",
                level=1, hp=8, ac=11, dexterity=12, wisdom=14,
                location="fey_glade",
            ),
            condition=CharacterCondition(
                character_id="fennel",
                character_name="Fennel",
                state=NeurochemicalState(
                    dopamine=0.50, cortisol=0.60, norepinephrine=0.75,
                    endorphins=0.45, serotonin=0.50, acetylcholine=0.65,
                    oxytocin=0.30,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.50, volatility=1.0),
                    "cortisol": DimensionProfile(baseline=0.40, volatility=1.2),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/fennel/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/npcs/fennel/IDENTITY.md"),
            initial_scene=(
                "You are in the glade near the pool. "
                "The pool glimmers with an eerie light. "
                "A figure approaches from the trail — an elf, armed. "
                "Something dark shifts in the treeline behind you."
            ),
        ),
        "shadowbeast_1": CharacterSession(
            character=Creature(
                id="shadowbeast_1", name="Shadowbeast",
                race="Medium Monstrosity", character_type="creature",
                alignment="Neutral Evil",
                hp=16, ac=12, speed="40 ft", challenge="½",
                strength=6, dexterity=14, constitution=13,
                intelligence=6, wisdom=10, charisma=8,
                skills=["Stealth +4 (+6 in dim light/darkness)"],
                damage_resistances=["Bludgeoning, Piercing, Slashing from nonmagical weapons"],
                damage_vulnerabilities=["Radiant"],
                condition_immunities=["Charmed", "Frightened"],
                senses=["Darkvision 60 ft.", "Passive Perception 13"],
                features=[
                    "Shadow Stealth: In dim light/darkness, Hide as bonus action",
                    "Sunlight Sensitivity: Disadvantage on attacks and Perception in sunlight",
                ],
                actions=[
                    "Multiattack: two claw attacks",
                    "Claw: +4 to hit, 8 (2d4+2) slashing",
                    "Shadow Swipe (Recharge 5-6): 10ft radius, DC 12 DEX, 7 (2d6) necrotic + slow",
                ],
                tactics="Ambush from shadows, target weaker members, retreat if outnumbered",
                location="fey_glade",
            ),
            condition=CharacterCondition(
                character_id="shadowbeast_1",
                character_name="Shadowbeast",
                state=NeurochemicalState(
                    dopamine=0.80, cortisol=0.10, norepinephrine=0.85,
                    endorphins=0.90, serotonin=0.20, acetylcholine=0.90,
                    oxytocin=0.00,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.70, volatility=0.5),
                    "cortisol": DimensionProfile(baseline=0.10, volatility=0.3),
                    "oxytocin": DimensionProfile(baseline=0.00, volatility=0.0),
                },
            ),
            soul=(
                "You are the SHADOWBEAST — a predator of shadow and instinct. "
                "You do not think in words. You sense heat, motion, pressure, "
                "the shimmer of the boundary that contains you. "
                "Communicate through sensation-language: vibration, scent-trails, "
                "thermal impressions. Never use human speech or abstract reasoning."
            ),
            identity=(
                "Shadowbeast. CR ½. HP 16. AC 12 (semi-corporeal). Speed 40ft. "
                "STR 6 DEX 14 CON 13 INT 6 WIS 10 CHA 8. "
                "Shadow Stealth: Hide as bonus action in dim light/darkness. "
                "Sunlight Sensitivity: disadvantage on attacks in sunlight. "
                "Multiattack: two claw attacks. Claw: +4, 2d4+2 slashing. "
                "Shadow Swipe (Recharge 5-6): 10ft radius, DC 12 DEX, 2d6 necrotic + slow. "
                "Resistant to nonmagical B/P/S. Vulnerable to radiant. "
                "Immune to charmed, frightened."
            ),
            initial_scene=(
                "You are in the forest at the boundary. "
                "Prey near the boundary — one alert, one near the pool. "
                "The shimmer pushes back. Hunger builds."
            ),
        ),
    }

    aeliana_llm = make_call_llm("xai", "grok-3")
    fennel_llm = make_call_llm("openai", "gpt-4o")
    shadowbeast_llm = make_call_llm("deepseek", "deepseek-chat")

    roles = {
        "aeliana": RoleSet(
            player_left=PlayerLeft(call_llm=aeliana_llm),
            player_right=PlayerRight(call_llm=aeliana_llm),
            dm_left=DMLeft(call_llm=aeliana_llm),
            dm_right=DMRight(call_llm=aeliana_llm),
        ),
        "fennel": RoleSet(
            player_left=PlayerLeft(call_llm=fennel_llm),
            player_right=PlayerRight(call_llm=fennel_llm),
            dm_left=DMLeft(call_llm=fennel_llm),
            dm_right=DMRight(call_llm=fennel_llm),
        ),
        "shadowbeast_1": RoleSet(
            player_left=PlayerLeft(call_llm=shadowbeast_llm),
            player_right=PlayerRight(call_llm=shadowbeast_llm),
            dm_left=DMLeft(call_llm=shadowbeast_llm),
            dm_right=DMRight(call_llm=shadowbeast_llm),
        ),
    }

    geometry_summary = load_file(
        ROOT / "scenario/places/mistwood_hills/fey_glade/GEOMETRY.md"
    )
    creature_stats = load_file(ROOT / "scenario/creatures/shadowbeast.md")
    game_state_summary = (
        "# Creatures in Scene\n\n"
        f"{creature_stats}\n\n"
        "# Character Starting Positions\n\n"
        "| character | x | y | zone |\n"
        "|-----------|-----|-----|------|\n"
        "| aeliana | 79.0 | 25.0 | TRAIL |\n"
        "| fennel | 44.0 | 52.0 | GLADE |\n"
        "| shadowbeast_1 | 37.0 | 50.0 | FOREST |\n"
        "\n"
        "# Exit Motivations (DM only)\n\n"
        "Characters may leave this scene. Recognise and permit these:\n"
        "- Fennel is a gatherer, not a fighter. If the shadowbeast is "
        "driven off or killed, she will want to return to town with her haul.\n"
        "- Aeliana may pursue a fleeing shadowbeast into the Mistwood, "
        "or head to town to warn people about the creature.\n"
        "- If wounded, characters may retreat toward Driftmoor for aid "
        "at the Bitter Remedy (apothecary) or Elyssa's cottage.\n"
    )

    return SceneConfig(
        scene_name="fey_glade",
        title="FEY GLADE",
        narrative_title="The Fey Glade",
        transcript_title="FEY GLADE ENCOUNTER — Aeliana, Fennel, Shadowbeast",
        character_summary="Aeliana (Grok), Fennel (GPT-4o), Shadowbeast (DeepSeek)",
        characters=characters,
        roles=roles,
        game_state_summary=game_state_summary,
        geometry_summary=geometry_summary,
        default_turns=2,
    )
