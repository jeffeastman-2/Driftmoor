"""Scene configuration: Old Mill — Father Lilar, Gregan, Tessa."""

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
        "lilar": CharacterSession(
            character=PlayerCharacter(
                id="lilar", name="Father Lilar Hearthsong", race="Human",
                character_type="player", character_class="Cleric",
                level=1, hp=10, ac=14,
                strength=12, dexterity=10, constitution=14,
                intelligence=10, wisdom=16, charisma=14,
                location="old_mill",
            ),
            condition=CharacterCondition(
                character_id="lilar",
                character_name="Lilar",
                state=NeurochemicalState(
                    dopamine=0.45, cortisol=0.40, norepinephrine=0.45,
                    endorphins=0.40, serotonin=0.60, acetylcholine=0.55,
                    oxytocin=0.55,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.45, volatility=0.4),
                    "cortisol": DimensionProfile(baseline=0.35, volatility=0.5),
                    "serotonin": DimensionProfile(baseline=0.60, volatility=0.3),
                    "oxytocin": DimensionProfile(baseline=0.50, volatility=0.5),
                },
            ),
            soul=load_file(ROOT / "scenario/people/players/lilar/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/players/lilar/IDENTITY.md"),
            initial_scene=(
                "You followed the river road to the Old Mill after hearing "
                "reports of strange symbols and a shadowbeast attack on a farmer. "
                "The mill is large, stone, two stories. The waterwheel groans. "
                "Inside, flour dust hangs in the air. Gregan Haverstead is at "
                "the grinding stones — broad, graying, flour-dusted. He looked "
                "up when you entered and has not smiled. His daughter Tessa, "
                "about fourteen, is near the far wall doing something with "
                "the support beams she stopped as soon as she saw you. "
                "You can see marks carved into the wood — dark, deliberate, "
                "unlike any mason's or carpenter's work you know. A baby "
                "cries from upstairs."
            ),
        ),
        "gregan": CharacterSession(
            character=NPC(
                id="gregan", name="Gregan Haverstead", race="Human",
                character_type="npc",
                role="Mill operator, Old Mill",
                home_location="old_mill",
                strength=15, dexterity=10, constitution=14,
                intelligence=10, wisdom=12, charisma=10,
                hp=14, ac=10,
                knowledge=[
                    "Strange symbols carved into the mill beams — suspects sabotage",
                    "Shadowbeast sightings near the mill have increased",
                    "Tessa has been slipping off to explore near the obelisk",
                    "A grain-delivery farmer was attacked by something with claws on the river road",
                    "The riverbank is eroding on the north side — structural risk",
                ],
                active_concerns=[
                    "The symbols on the beams — who carved them and why",
                    "Tessa's unauthorized explorations",
                    "The mill is failing and he cannot fix it alone",
                ],
                location="old_mill",
            ),
            condition=CharacterCondition(
                character_id="gregan",
                character_name="Gregan",
                state=NeurochemicalState(
                    dopamine=0.30, cortisol=0.60, norepinephrine=0.55,
                    endorphins=0.25, serotonin=0.40, acetylcholine=0.50,
                    oxytocin=0.45,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.35, volatility=0.3),
                    "cortisol": DimensionProfile(baseline=0.50, volatility=0.6),
                    "oxytocin": DimensionProfile(baseline=0.40, volatility=0.4),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/haversteads/gregan.md"),
            identity=load_file(ROOT / "scenario/people/npcs/haversteads/gregan.md"),
            initial_scene=(
                "A cleric just walked into your mill. Faded white robes, "
                "holy symbol of Pelor, shield on his back. He is looking "
                "at the beams. Tessa was near those beams again — you saw "
                "her pull her hand back when the door opened. You do not "
                "know this man. You do not know if he is here to help or "
                "to make things worse. The mill wheel is grinding unevenly "
                "and you have not slept well in a week."
            ),
        ),
        "tessa": CharacterSession(
            character=NPC(
                id="tessa", name="Tessa Haverstead", race="Human",
                character_type="npc",
                role="Mill assistant and unauthorized explorer",
                home_location="old_mill",
                strength=8, dexterity=14, constitution=12,
                intelligence=13, wisdom=11, charisma=12,
                hp=6, ac=10,
                knowledge=[
                    "The symbols on the mill beams match carvings she found on riverbank stones",
                    "She has been near the obelisk area and seen things she has not told anyone",
                    "She has been secretly copying the symbols — she thinks they mean something",
                    "Baby Isla gets fussy near the outer walls where the symbols are strongest",
                ],
                active_concerns=[
                    "The symbols — what do they mean",
                    "Getting caught by her father for exploring near the obelisk",
                    "Whether this stranger can be trusted with what she knows",
                ],
                location="old_mill",
            ),
            condition=CharacterCondition(
                character_id="tessa",
                character_name="Tessa",
                state=NeurochemicalState(
                    dopamine=0.60, cortisol=0.50, norepinephrine=0.65,
                    endorphins=0.55, serotonin=0.45, acetylcholine=0.70,
                    oxytocin=0.40,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.55, volatility=0.9),
                    "cortisol": DimensionProfile(baseline=0.35, volatility=0.8),
                    "acetylcholine": DimensionProfile(baseline=0.65, volatility=0.7),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/haversteads/tessa.md"),
            identity=load_file(ROOT / "scenario/people/npcs/haversteads/tessa.md"),
            initial_scene=(
                "You were tracing the symbols on the beam when the door "
                "opened. A man in white robes. A cleric. You stepped back "
                "and shoved the charcoal rubbing into your apron pocket. "
                "Your father is watching from the grinding stones. He saw "
                "you near the beams again. The cleric is looking at the "
                "marks now. He might actually know what they are. You want "
                "to ask but not in front of your father."
            ),
        ),
    }

    lilar_llm = make_call_llm("anthropic", "claude-sonnet-4-20250514")
    gregan_llm = make_call_llm("openai", "gpt-4o")
    tessa_llm = make_call_llm("xai", "grok-3")

    roles = {
        "lilar": RoleSet(
            player_left=PlayerLeft(call_llm=lilar_llm),
            player_right=PlayerRight(call_llm=lilar_llm),
            dm_left=DMLeft(call_llm=lilar_llm),
            dm_right=DMRight(call_llm=lilar_llm),
        ),
        "gregan": RoleSet(
            player_left=PlayerLeft(call_llm=gregan_llm),
            player_right=PlayerRight(call_llm=gregan_llm),
            dm_left=DMLeft(call_llm=gregan_llm),
            dm_right=DMRight(call_llm=gregan_llm),
        ),
        "tessa": RoleSet(
            player_left=PlayerLeft(call_llm=tessa_llm),
            player_right=PlayerRight(call_llm=tessa_llm),
            dm_left=DMLeft(call_llm=tessa_llm),
            dm_right=DMRight(call_llm=tessa_llm),
        ),
    }

    place_md = load_file(
        ROOT / "scenario/places/greywater_river/old_mill/PLACE.md"
    )
    contents_md = load_file(
        ROOT / "scenario/places/greywater_river/old_mill/CONTENTS.md"
    )
    obelisk_lore = load_file(ROOT / "scenario/things/obelisk_shards.md")
    game_state_summary = (
        "# Scene: The Old Mill\n\n"
        f"{place_md}\n\n"
        f"{contents_md}\n\n"
        "# Relevant Lore (DM only)\n\n"
        f"{obelisk_lore}\n\n"
        "# Scene Notes\n\n"
        "This is an exploration/social scene at the mill. No combat expected.\n"
        "The symbols on the beams match obelisk-related markings found elsewhere.\n"
        "Tessa has secret rubbings of the symbols and has been near the obelisk.\n"
        "Baby Isla's distress near the outer walls is a barometer of the corruption.\n"
        "Gregan is suspicious of strangers and will not open up easily.\n"
        "Tessa will share information privately if she trusts the cleric.\n"
        "\n"
        "# Exit Motivations (DM only)\n\n"
        "Characters may leave this scene. Recognise and permit these:\n"
        "- Lilar may want to bring the symbol rubbings to Father Elden at "
        "the Beacon Church for comparison.\n"
        "- Tessa may try to lead Lilar to the riverbank stones where she "
        "found matching symbols.\n"
        "- Gregan needs supplies from Salt & Iron in town — he may send "
        "someone or mention needing to go himself.\n"
        "- If Lilar learns about the shadowbeast attack, he may head "
        "toward the Fey Glade or Mistwood to investigate.\n"
    )

    return SceneConfig(
        scene_name="old_mill",
        title="OLD MILL",
        narrative_title="The Old Mill",
        transcript_title="OLD MILL — Lilar, Gregan, Tessa",
        character_summary="Lilar (Claude), Gregan (GPT-4o), Tessa (Grok)",
        characters=characters,
        roles=roles,
        game_state_summary=game_state_summary,
        default_turns=4,
    )
