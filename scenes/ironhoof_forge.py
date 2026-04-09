"""Scene configuration: Ironhoof Forge — Thorgrim, Darrin, Kara."""

from engine.llm_bridge import make_call_llm
from engine.session import CharacterSession
from engine.player_router import PlayerLeft, PlayerRight
from engine.dm_agent import DMLeft, DMRight
from engine.scene_manager import RoleSet
from engine.scene_runner import SceneConfig, ROOT, load_file
from models.character import PlayerCharacter, NPC
from models.condition import (
    CharacterCondition,
    NeurochemicalState,
    DimensionProfile,
)


def configure() -> SceneConfig:
    characters = {
        "thorgrim": CharacterSession(
            character=PlayerCharacter(
                id="thorgrim", name="Thorgrim Stoneheart", race="Mountain Dwarf",
                character_type="player", character_class="Fighter",
                level=1, hp=13, ac=18,
                strength=16, dexterity=12, constitution=16,
                intelligence=10, wisdom=12, charisma=10,
                location="ironhoof_forge",
            ),
            condition=CharacterCondition(
                character_id="thorgrim",
                character_name="Thorgrim",
                state=NeurochemicalState(
                    dopamine=0.40, cortisol=0.45, norepinephrine=0.50,
                    endorphins=0.35, serotonin=0.40, acetylcholine=0.60,
                    oxytocin=0.20,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.40, volatility=0.4),
                    "cortisol": DimensionProfile(baseline=0.45, volatility=0.5),
                    "serotonin": DimensionProfile(baseline=0.45, volatility=0.3),
                    "oxytocin": DimensionProfile(baseline=0.15, volatility=0.3),
                },
            ),
            soul=load_file(ROOT / "scenario/people/players/thorgrim/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/players/thorgrim/IDENTITY.md"),
            initial_scene=(
                "Early morning at the forge. You slept poorly in the lean-to — "
                "bad dreams again, the ambush, the screaming. You are standing "
                "at the forge fire, examining the shadowy symbols carved into "
                "the stone wall. They were not here a week ago. The marks are "
                "unlike any mason's work you know. Darrin is at the anvil, "
                "hammering, pretending not to watch you. His daughter Kara "
                "is in the stables — you can hear her talking to the horses."
            ),
        ),
        "darrin": CharacterSession(
            character=NPC(
                id="darrin", name="Darrin Stonebrook", race="Human",
                character_type="npc",
                role="Blacksmith, Ironhoof Forge",
                home_location="ironhoof_forge",
                strength=15, dexterity=10, constitution=14,
                intelligence=10, wisdom=13, charisma=10,
                hp=16, ac=12,
                knowledge=[
                    "Shadowy symbols appeared on the forge walls — no one admits to carving them",
                    "One of the town's horses disappeared with clawed tracks heading toward Mistwood",
                    "The symbols feel wrong — cold to the touch even near the forge fire",
                    "He has heard rumors of similar marks near the old obelisk north of town",
                ],
                active_concerns=[
                    "The symbols on his forge — sabotage or something worse",
                    "The missing horse — Kara found the tracks",
                    "Kara's restlessness — she wants to leave with adventurers",
                ],
                location="ironhoof_forge",
            ),
            condition=CharacterCondition(
                character_id="darrin",
                character_name="Darrin",
                state=NeurochemicalState(
                    dopamine=0.35, cortisol=0.55, norepinephrine=0.50,
                    endorphins=0.30, serotonin=0.50, acetylcholine=0.55,
                    oxytocin=0.45,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.35, volatility=0.3),
                    "cortisol": DimensionProfile(baseline=0.40, volatility=0.6),
                    "oxytocin": DimensionProfile(baseline=0.40, volatility=0.4),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/darrin/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/npcs/darrin/IDENTITY.md"),
            initial_scene=(
                "Morning at the forge. You are hammering a set of horseshoes, "
                "but your mind is elsewhere. The dwarf — Thorgrim — is standing "
                "by the wall again, studying those marks. You have not asked "
                "him directly what he thinks. You are not sure you want to know. "
                "The marks appeared a week ago and they are cold to the touch "
                "even with the forge burning. From the stables you hear Kara "
                "talking to the remaining horses. One is still missing."
            ),
        ),
        "kara": CharacterSession(
            character=NPC(
                id="kara", name="Kara Stonebrook", race="Human",
                character_type="npc",
                role="Stable manager, Ironhoof Forge",
                home_location="ironhoof_forge",
                strength=10, dexterity=14, constitution=12,
                intelligence=12, wisdom=11, charisma=14,
                hp=10, ac=11,
                knowledge=[
                    "She found the clawed tracks where the horse disappeared — leading toward Mistwood",
                    "The remaining horses have been spooked for weeks, especially at night",
                    "She has seen Thorgrim sitting alone at the lean-to, staring at nothing",
                    "She wants to apprentice with adventurers — will offer a horse in exchange",
                ],
                active_concerns=[
                    "The missing horse — she feels responsible",
                    "Convincing her father to let her go",
                    "Whether Thorgrim might help her case",
                ],
                location="ironhoof_forge",
            ),
            condition=CharacterCondition(
                character_id="kara",
                character_name="Kara",
                state=NeurochemicalState(
                    dopamine=0.65, cortisol=0.30, norepinephrine=0.55,
                    endorphins=0.60, serotonin=0.55, acetylcholine=0.65,
                    oxytocin=0.50,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.60, volatility=0.9),
                    "cortisol": DimensionProfile(baseline=0.25, volatility=0.7),
                    "oxytocin": DimensionProfile(baseline=0.45, volatility=0.6),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/kara/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/npcs/kara/IDENTITY.md"),
            initial_scene=(
                "You are in the stables brushing down the bay mare. She is "
                "still jittery — all the horses have been since the night "
                "the gelding vanished. You found the tracks yourself. Claws, "
                "not hooves, heading into the Mistwood tree line. Your father "
                "told you to forget about it. You have not forgotten about it. "
                "Through the stable wall you can hear the forge hammer and "
                "the dwarf moving around. He has been studying those marks "
                "on the wall. You want to ask him what he thinks."
            ),
        ),
    }

    thorgrim_llm = make_call_llm("xai", "grok-3")
    darrin_llm = make_call_llm("openai", "gpt-4o")
    kara_llm = make_call_llm("deepseek", "deepseek-chat")

    roles = {
        "thorgrim": RoleSet(
            player_left=PlayerLeft(call_llm=thorgrim_llm),
            player_right=PlayerRight(call_llm=thorgrim_llm),
            dm_left=DMLeft(call_llm=thorgrim_llm),
            dm_right=DMRight(call_llm=thorgrim_llm),
        ),
        "darrin": RoleSet(
            player_left=PlayerLeft(call_llm=darrin_llm),
            player_right=PlayerRight(call_llm=darrin_llm),
            dm_left=DMLeft(call_llm=darrin_llm),
            dm_right=DMRight(call_llm=darrin_llm),
        ),
        "kara": RoleSet(
            player_left=PlayerLeft(call_llm=kara_llm),
            player_right=PlayerRight(call_llm=kara_llm),
            dm_left=DMLeft(call_llm=kara_llm),
            dm_right=DMRight(call_llm=kara_llm),
        ),
    }

    place_md = load_file(
        ROOT / "scenario/places/driftmoor/ironhoof_forge/PLACE.md"
    )
    contents_md = load_file(
        ROOT / "scenario/places/driftmoor/ironhoof_forge/CONTENTS.md"
    )
    obelisk_lore = load_file(ROOT / "scenario/things/obelisk_shards.md")
    game_state_summary = (
        "# Scene: Ironhoof Forge\n\n"
        f"{place_md}\n\n"
        f"{contents_md}\n\n"
        "# Relevant Lore (DM only)\n\n"
        f"{obelisk_lore}\n\n"
        "# Scene Notes\n\n"
        "This is an exploration/social scene at the forge. No combat expected.\n"
        "The shadowy symbols on the forge walls match obelisk-related markings "
        "found elsewhere — this is a plot thread, not a combat encounter.\n"
        "The missing horse and clawed tracks toward Mistwood are a separate hook.\n"
        "Kara wants to apprentice with adventurers. Darrin will resist this.\n"
        "Thorgrim has been staying at the lean-to. He is a guest, not an employee.\n"
        "\n"
        "# Exit Motivations (DM only)\n\n"
        "Characters may leave this scene. Recognise and permit these:\n"
        "- Thorgrim has not eaten since yesterday. The Weary Traveler tavern "
        "serves breakfast and is a short walk into town.\n"
        "- Kara wants to follow the clawed tracks toward Mistwood. "
        "She may try to slip away or recruit Thorgrim.\n"
        "- Darrin needs iron stock from the general store in town — "
        "he may send someone or go himself.\n"
        "- If anyone learns about the obelisk shard ring at the Gilded Trinket, "
        "the forge symbols become much more interesting.\n"
    )

    return SceneConfig(
        scene_name="ironhoof_forge",
        title="IRONHOOF FORGE",
        narrative_title="The Ironhoof Forge",
        transcript_title="IRONHOOF FORGE — Thorgrim, Darrin, Kara",
        character_summary="Thorgrim (Grok), Darrin (GPT-4o), Kara (DeepSeek)",
        characters=characters,
        roles=roles,
        game_state_summary=game_state_summary,
        default_turns=4,
    )
