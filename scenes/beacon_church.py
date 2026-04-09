"""Scene configuration: Beacon Church — Sister Amara, Father Elden, Mira."""

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
        "amara": CharacterSession(
            character=PlayerCharacter(
                id="amara", name="Sister Amara Solbright", race="Human",
                character_type="player", character_class="Cleric",
                level=1, hp=10, ac=16,
                strength=14, dexterity=10, constitution=12,
                intelligence=10, wisdom=16, charisma=14,
                location="beacon_church",
            ),
            condition=CharacterCondition(
                character_id="amara",
                character_name="Amara",
                state=NeurochemicalState(
                    dopamine=0.50, cortisol=0.35, norepinephrine=0.40,
                    endorphins=0.50, serotonin=0.65, acetylcholine=0.55,
                    oxytocin=0.55,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.50, volatility=0.5),
                    "cortisol": DimensionProfile(baseline=0.30, volatility=0.5),
                    "serotonin": DimensionProfile(baseline=0.65, volatility=0.3),
                    "oxytocin": DimensionProfile(baseline=0.50, volatility=0.5),
                },
            ),
            soul=load_file(ROOT / "scenario/people/players/amara/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/players/amara/IDENTITY.md"),
            initial_scene=(
                "You climbed the rise to the Beacon Church at dusk. Your "
                "order sent you to investigate disturbances in Driftmoor. "
                "The church is modest stone, wooden steeple. The lantern "
                "at the top is lit — but the light coming from it is wrong. "
                "Dark threads in what should be pure flame. Inside: simple, "
                "clean, beeswax and herbs. An old priest leans on an oak "
                "staff near the altar. A young woman with red braids is "
                "arranging candles and watched you come through the door "
                "before the priest did."
            ),
        ),
        "elden": CharacterSession(
            character=NPC(
                id="elden", name="Father Elden Greybeard", race="Human",
                character_type="npc",
                role="Priest of Pelor, The Beacon",
                home_location="beacon_church",
                strength=8, dexterity=8, constitution=10,
                intelligence=12, wisdom=16, charisma=14,
                hp=8, ac=10,
                knowledge=[
                    "The church lantern flickers with dark light — connected to the obelisk",
                    "He entered the Echoing Caverns decades ago and lost his companions",
                    "Mira has an emerging divine magic talent she has not fully tested",
                    "He has heard about the symbols at the forge and the mill",
                ],
                active_concerns=[
                    "The lantern — its corruption is worsening",
                    "His companions' remains in the Echoing Caverns",
                    "Mira's future — she is outgrowing this place",
                ],
                location="beacon_church",
            ),
            condition=CharacterCondition(
                character_id="elden",
                character_name="Elden",
                state=NeurochemicalState(
                    dopamine=0.35, cortisol=0.45, norepinephrine=0.35,
                    endorphins=0.30, serotonin=0.55, acetylcholine=0.50,
                    oxytocin=0.50,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.35, volatility=0.3),
                    "cortisol": DimensionProfile(baseline=0.40, volatility=0.4),
                    "serotonin": DimensionProfile(baseline=0.55, volatility=0.3),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/elden/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/npcs/elden/IDENTITY.md"),
            initial_scene=(
                "A cleric of Lathander has come to your church. Young, chain "
                "mail, silver sunrise symbol at her throat. She saw the lantern "
                "on her way up — you could tell by her face. She knows the light "
                "is wrong. Mira is watching from the candle rack, already "
                "assessing. You have been waiting for someone to come. You did "
                "not expect it to be someone from another order."
            ),
        ),
        "mira": CharacterSession(
            character=NPC(
                id="mira", name="Mira", race="Human",
                character_type="npc",
                role="Acolyte, The Beacon",
                home_location="beacon_church",
                strength=8, dexterity=12, constitution=10,
                intelligence=12, wisdom=14, charisma=12,
                hp=6, ac=10,
                knowledge=[
                    "She has seen something near the lantern at night she has not told Elden",
                    "She believes a holy relic in the Mistwood Hills could protect Driftmoor",
                    "Father Elden went into the Echoing Caverns once — something happened there",
                    "The dark light in the lantern has no physical source",
                ],
                active_concerns=[
                    "The lantern — what she saw and has not reported",
                    "Whether this stranger can be trusted with Elden's safety",
                    "Her own emerging abilities",
                ],
                location="beacon_church",
            ),
            condition=CharacterCondition(
                character_id="mira",
                character_name="Mira",
                state=NeurochemicalState(
                    dopamine=0.45, cortisol=0.45, norepinephrine=0.55,
                    endorphins=0.40, serotonin=0.50, acetylcholine=0.65,
                    oxytocin=0.45,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.45, volatility=0.6),
                    "cortisol": DimensionProfile(baseline=0.35, volatility=0.7),
                    "acetylcholine": DimensionProfile(baseline=0.60, volatility=0.5),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/mira/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/npcs/mira/IDENTITY.md"),
            initial_scene=(
                "A stranger just walked in. Cleric. Lathander, not Pelor — "
                "you can tell from the symbol. Chain mail and a mace. She "
                "looked at the lantern on the way up. She knows. Father "
                "Elden is already leaning toward her with that look he gets "
                "when he wants to trust someone before he should. You have "
                "not told him what you saw at the lantern three nights ago. "
                "You are not sure you should tell this woman either. Not yet."
            ),
        ),
    }

    amara_llm = make_call_llm("openai", "gpt-4o")
    elden_llm = make_call_llm("deepseek", "deepseek-chat")
    mira_llm = make_call_llm("xai", "grok-3")

    roles = {
        "amara": RoleSet(
            player_left=PlayerLeft(call_llm=amara_llm),
            player_right=PlayerRight(call_llm=amara_llm),
            dm_left=DMLeft(call_llm=amara_llm),
            dm_right=DMRight(call_llm=amara_llm),
        ),
        "elden": RoleSet(
            player_left=PlayerLeft(call_llm=elden_llm),
            player_right=PlayerRight(call_llm=elden_llm),
            dm_left=DMLeft(call_llm=elden_llm),
            dm_right=DMRight(call_llm=elden_llm),
        ),
        "mira": RoleSet(
            player_left=PlayerLeft(call_llm=mira_llm),
            player_right=PlayerRight(call_llm=mira_llm),
            dm_left=DMLeft(call_llm=mira_llm),
            dm_right=DMRight(call_llm=mira_llm),
        ),
    }

    place_md = load_file(
        ROOT / "scenario/places/driftmoor/beacon_church/PLACE.md"
    )
    contents_md = load_file(
        ROOT / "scenario/places/driftmoor/beacon_church/CONTENTS.md"
    )
    obelisk_lore = load_file(ROOT / "scenario/things/obelisk_shards.md")
    game_state_summary = (
        "# Scene: The Beacon Church\n\n"
        f"{place_md}\n\n"
        f"{contents_md}\n\n"
        "# Relevant Lore (DM only)\n\n"
        f"{obelisk_lore}\n\n"
        "# Scene Notes\n\n"
        "This is an exploration/social scene in the village church. "
        "No combat expected.\n"
        "The dark lantern is the visible sign of the obelisk's influence "
        "reaching into Driftmoor — it has no mundane explanation.\n"
        "Two clerics of different orders meeting in a corrupted church. "
        "Amara serves Lathander (renewal), Elden serves Pelor (light). "
        "Compatible but distinct faiths.\n"
        "Mira is guarded — she protects Elden and holds back information "
        "until trust is earned.\n"
        "Elden wants to trust but carries deep guilt about the Echoing "
        "Caverns.\n"
        "\n"
        "# Exit Motivations (DM only)\n\n"
        "Characters may leave this scene. Recognise and permit these:\n"
        "- Amara may want to examine the lantern directly — this leads "
        "outside and up the steeple.\n"
        "- Mira may mention the Mistwood relic quest if she trusts Amara.\n"
        "- Elden may mention hearing about symbols at the forge or mill, "
        "suggesting Amara visit those locations.\n"
        "- If the conversation turns to the obelisk, Amara may want to "
        "head north toward Obelisk Reach.\n"
        "- Amara has not eaten — Elden may offer the herb garden's "
        "modest hospitality, or suggest the Broken Lantern tavern.\n"
    )

    return SceneConfig(
        scene_name="beacon_church",
        title="BEACON CHURCH",
        narrative_title="The Beacon Church",
        transcript_title="BEACON CHURCH — Amara, Elden, Mira",
        character_summary="Amara (GPT-4o), Elden (DeepSeek), Mira (Grok)",
        characters=characters,
        roles=roles,
        game_state_summary=game_state_summary,
        default_turns=4,
    )
