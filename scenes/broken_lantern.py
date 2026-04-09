"""Scene configuration: Broken Lantern — Kaelin performs, Tess tends bar."""

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
        "kaelin": CharacterSession(
            character=PlayerCharacter(
                id="kaelin", name="Kaelin Brightspark", race="Lightfoot Halfling",
                character_type="player", character_class="Bard",
                level=1, hp=9, ac=11,
                strength=8, dexterity=14, constitution=12,
                intelligence=12, wisdom=10, charisma=16,
                location="broken_lantern",
            ),
            condition=CharacterCondition(
                character_id="kaelin",
                character_name="Kaelin",
                state=NeurochemicalState(
                    dopamine=0.70, cortisol=0.35, norepinephrine=0.45,
                    endorphins=0.65, serotonin=0.50, acetylcholine=0.60,
                    oxytocin=0.40,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.65, volatility=0.9),
                    "cortisol": DimensionProfile(baseline=0.30, volatility=0.7),
                    "endorphins": DimensionProfile(baseline=0.60, volatility=0.8),
                    "oxytocin": DimensionProfile(baseline=0.35, volatility=0.6),
                },
            ),
            soul=load_file(ROOT / "scenario/people/players/kaelin/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/players/kaelin/IDENTITY.md"),
            initial_scene=(
                "Evening at the Broken Lantern. You pushed through the door "
                "ten minutes ago — new town, no coin, empty stomach. The room "
                "is half full. Fisherfolk, a couple of farmers, a drunk at the "
                "end of the bar muttering about shadow giants. The woman behind "
                "the bar has already looked you over twice. You unslung your "
                "lute and found a stool near the fire. If you play well enough, "
                "dinner is free. It usually is."
            ),
        ),
        "tess": CharacterSession(
            character=NPC(
                id="tess", name="Tess Malwin", race="Human",
                character_type="npc",
                role="Owner, The Broken Lantern",
                home_location="broken_lantern",
                strength=13, dexterity=12, constitution=14,
                intelligence=13, wisdom=14, charisma=14,
                hp=14, ac=11,
                knowledge=[
                    "Suspicious travelers have been using the meeting room — nervous, secretive",
                    "Wilfred claims to have seen shadow giants near the obelisk cliffs",
                    "Strange noises from the unoccupied upstairs room — she has not investigated yet",
                    "Hidden compartment under the storage room floor — she guards it carefully",
                    "A previous owner supposedly hid something valuable in the storage room",
                ],
                active_concerns=[
                    "The meeting room guests — who are they working for",
                    "Wilfred's sightings — drunk rambling or real",
                    "The noises upstairs",
                    "A halfling bard just walked in with no coin and hungry eyes",
                ],
                location="broken_lantern",
            ),
            condition=CharacterCondition(
                character_id="tess",
                character_name="Tess",
                state=NeurochemicalState(
                    dopamine=0.45, cortisol=0.40, norepinephrine=0.50,
                    endorphins=0.40, serotonin=0.55, acetylcholine=0.70,
                    oxytocin=0.30,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.45, volatility=0.4),
                    "cortisol": DimensionProfile(baseline=0.35, volatility=0.5),
                    "acetylcholine": DimensionProfile(baseline=0.65, volatility=0.3),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/tess/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/npcs/tess/IDENTITY.md"),
            initial_scene=(
                "Evening crowd. The usual faces. Wilfred is three ales deep "
                "and talking about shadow giants again. Then the door opens "
                "and a halfling walks in — wild hair, patched clothes, lute "
                "across their back, and the particular confidence of someone "
                "who has talked their way into a meal before. They have already "
                "found the stool by the fire. No coin visible. You have seen "
                "this act. The question is whether this one is worth feeding."
            ),
        ),
    }

    kaelin_llm = make_call_llm("deepseek", "deepseek-chat")
    tess_llm = make_call_llm("xai", "grok-3")

    roles = {
        "kaelin": RoleSet(
            player_left=PlayerLeft(call_llm=kaelin_llm),
            player_right=PlayerRight(call_llm=kaelin_llm),
            dm_left=DMLeft(call_llm=kaelin_llm),
            dm_right=DMRight(call_llm=kaelin_llm),
        ),
        "tess": RoleSet(
            player_left=PlayerLeft(call_llm=tess_llm),
            player_right=PlayerRight(call_llm=tess_llm),
            dm_left=DMLeft(call_llm=tess_llm),
            dm_right=DMRight(call_llm=tess_llm),
        ),
    }

    place_md = load_file(
        ROOT / "scenario/places/driftmoor/broken_lantern/PLACE.md"
    )
    contents_md = load_file(
        ROOT / "scenario/places/driftmoor/broken_lantern/CONTENTS.md"
    )
    game_state_summary = (
        "# Scene: The Broken Lantern (Tavern)\n\n"
        f"{place_md}\n\n"
        f"{contents_md}\n\n"
        "# Scene Notes\n\n"
        "This is an exploration/social scene in the village tavern. "
        "No combat expected.\n"
        "Kaelin has no coin and is hungry. They need to earn a meal.\n"
        "Tess is sharp, fair, and always looking for useful people.\n"
        "Wilfred is at the bar muttering about shadow giants near the "
        "obelisk — this is a real plot thread, not just drunk talk.\n"
        "The meeting room behind the kitchen has suspicious guests.\n"
        "Strange noises have been reported from an unoccupied upstairs room.\n"
        "\n"
        "# Exit Motivations (DM only)\n\n"
        "Characters may leave this scene. Recognise and permit these:\n"
        "- Kaelin is a wanderer — they may want to explore the village, "
        "especially if they hear about the forge symbols or the pawnshop.\n"
        "- Tess may send someone to investigate the noises upstairs "
        "(this leads to a sub-location, not a scene exit).\n"
        "- If Wilfred's obelisk talk catches Kaelin's ear, they may "
        "head north toward the obelisk reach at dawn.\n"
        "- The suspicious meeting room guests may leave — Tess may ask "
        "someone to follow them.\n"
    )

    return SceneConfig(
        scene_name="broken_lantern",
        title="BROKEN LANTERN",
        narrative_title="The Broken Lantern",
        transcript_title="BROKEN LANTERN — Kaelin, Tess",
        character_summary="Kaelin (DeepSeek), Tess (Grok)",
        characters=characters,
        roles=roles,
        game_state_summary=game_state_summary,
        default_turns=4,
    )
