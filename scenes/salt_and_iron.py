"""Scene configuration: Salt & Iron — Varrak browses, Jorgen minds the shop."""

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
        "varrak": CharacterSession(
            character=PlayerCharacter(
                id="varrak", name="Varrak Ironflame", race="Dragonborn",
                character_type="player", character_class="Sorcerer",
                level=1, hp=8, ac=13,
                strength=10, dexterity=14, constitution=14,
                intelligence=12, wisdom=10, charisma=16,
                location="salt_and_iron",
            ),
            condition=CharacterCondition(
                character_id="varrak",
                character_name="Varrak",
                state=NeurochemicalState(
                    dopamine=0.55, cortisol=0.40, norepinephrine=0.50,
                    endorphins=0.35, serotonin=0.40, acetylcholine=0.70,
                    oxytocin=0.15,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.50, volatility=0.6),
                    "cortisol": DimensionProfile(baseline=0.35, volatility=0.5),
                    "acetylcholine": DimensionProfile(baseline=0.65, volatility=0.4),
                    "oxytocin": DimensionProfile(baseline=0.10, volatility=0.2),
                },
            ),
            soul=load_file(ROOT / "scenario/people/players/varrak/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/players/varrak/IDENTITY.md"),
            initial_scene=(
                "You came to Salt & Iron because Kelem Dustcloak told you "
                "to start here. The mercantile is large, organized, iron-banded "
                "timber. Shelves of rope, tools, salt barrels, weapons. A long "
                "counter runs the center. Behind it stands a broad man with a "
                "salt-and-pepper beard and a scowl. He looked at you — a red "
                "dragonborn in robes with no armor — and has not spoken yet. "
                "Your satchel holds your obelisk notes. Something in this town "
                "is connected to the fragments. You can feel it in the base of "
                "your skull, the way you always feel it near shard-touched places."
            ),
        ),
        "jorgen": CharacterSession(
            character=NPC(
                id="jorgen", name="Jorgen Hallowtide", race="Human",
                character_type="npc",
                role="Proprietor, Salt & Iron Mercantile",
                home_location="salt_and_iron",
                strength=14, dexterity=10, constitution=14,
                intelligence=12, wisdom=13, charisma=12,
                hp=16, ac=11,
                knowledge=[
                    "Supply caravan went missing — wants it found",
                    "Suspects Kelem Dustcloak of dealing in stolen or illicit goods",
                    "Rumors of an artifact in the Echoing Caverns",
                    "A dragonborn asking about the obelisk is either useful or dangerous",
                ],
                active_concerns=[
                    "The missing caravan — he needs those supplies",
                    "Kelem's dealings — something is off",
                    "Whether this dragonborn was sent by Kelem",
                ],
                location="salt_and_iron",
            ),
            condition=CharacterCondition(
                character_id="jorgen",
                character_name="Jorgen",
                state=NeurochemicalState(
                    dopamine=0.40, cortisol=0.45, norepinephrine=0.45,
                    endorphins=0.35, serotonin=0.50, acetylcholine=0.55,
                    oxytocin=0.25,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.40, volatility=0.3),
                    "cortisol": DimensionProfile(baseline=0.40, volatility=0.5),
                    "serotonin": DimensionProfile(baseline=0.50, volatility=0.3),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/jorgen/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/npcs/jorgen/IDENTITY.md"),
            initial_scene=(
                "A dragonborn just walked into your shop. Red scales, amber "
                "eyes, robes, no armor. Carrying a leather satchel and a "
                "quarterstaff. He is looking at the shelves the way someone "
                "looks when they are not shopping — he is scanning. A sorcerer, "
                "almost certainly. You have not decided yet if he is Kelem's "
                "man or something else. The supply caravan is three days late "
                "and you are in no mood for trouble."
            ),
        ),
    }

    varrak_llm = make_call_llm("anthropic", "claude-sonnet-4-20250514")
    jorgen_llm = make_call_llm("deepseek", "deepseek-chat")

    roles = {
        "varrak": RoleSet(
            player_left=PlayerLeft(call_llm=varrak_llm),
            player_right=PlayerRight(call_llm=varrak_llm),
            dm_left=DMLeft(call_llm=varrak_llm),
            dm_right=DMRight(call_llm=varrak_llm),
        ),
        "jorgen": RoleSet(
            player_left=PlayerLeft(call_llm=jorgen_llm),
            player_right=PlayerRight(call_llm=jorgen_llm),
            dm_left=DMLeft(call_llm=jorgen_llm),
            dm_right=DMRight(call_llm=jorgen_llm),
        ),
    }

    place_md = load_file(
        ROOT / "scenario/places/driftmoor/salt_and_iron/PLACE.md"
    )
    contents_md = load_file(
        ROOT / "scenario/places/driftmoor/salt_and_iron/CONTENTS.md"
    )
    obelisk_lore = load_file(ROOT / "scenario/things/obelisk_shards.md")
    game_state_summary = (
        "# Scene: Salt & Iron Mercantile\n\n"
        f"{place_md}\n\n"
        f"{contents_md}\n\n"
        "# Relevant Lore (DM only)\n\n"
        f"{obelisk_lore}\n\n"
        "# Scene Notes\n\n"
        "This is an exploration/social scene in the general store. "
        "No combat expected.\n"
        "Varrak is a sorcerer with Detect Magic — if he casts it, nothing "
        "in stock is magical, but the map of Driftmoor is worth buying.\n"
        "Kelem Dustcloak sent Varrak here. Jorgen suspects Kelem of "
        "illicit dealings. This creates immediate tension if Varrak "
        "mentions Kelem's name.\n"
        "Jorgen rewards good stories with discounts — Varrak's draconic "
        "heritage and obelisk research could earn one.\n"
        "The missing supply caravan is a hook Jorgen will offer if he "
        "decides Varrak is reliable.\n"
        "\n"
        "# Exit Motivations (DM only)\n\n"
        "Characters may leave this scene. Recognise and permit these:\n"
        "- Varrak may want to visit Kelem at Dustcloak's Curios to "
        "examine the obelisk fragments directly.\n"
        "- Jorgen may mention the Echoing Caverns artifact and suggest "
        "Varrak head north.\n"
        "- If Jorgen mentions the forge symbols or the dark light at the "
        "Beacon Church, Varrak may investigate those locations.\n"
        "- Varrak is hungry and new in town — Jorgen may direct him to "
        "the Broken Lantern for food and lodging.\n"
        "- Jorgen may hire Varrak to find the missing caravan.\n"
    )

    return SceneConfig(
        scene_name="salt_and_iron",
        title="SALT & IRON",
        narrative_title="Salt and Iron",
        transcript_title="SALT & IRON — Varrak, Jorgen",
        character_summary="Varrak (Claude), Jorgen (DeepSeek)",
        characters=characters,
        roles=roles,
        game_state_summary=game_state_summary,
        default_turns=4,
    )
