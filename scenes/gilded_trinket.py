"""Scene configuration: Gilded Trinket — Seraphina browses, Tavian minds the shop."""

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
        "seraphina": CharacterSession(
            character=PlayerCharacter(
                id="seraphina", name="Seraphina Duskwhisper", race="Half-Elf",
                character_type="player", character_class="Rogue",
                level=1, hp=9, ac=11, strength=8, dexterity=16,
                constitution=12, intelligence=14, wisdom=10, charisma=15,
                location="gilded_trinket",
            ),
            condition=CharacterCondition(
                character_id="seraphina",
                character_name="Seraphina",
                state=NeurochemicalState(
                    dopamine=0.65, cortisol=0.40, norepinephrine=0.60,
                    endorphins=0.50, serotonin=0.45, acetylcholine=0.75,
                    oxytocin=0.25,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.55, volatility=0.9),
                    "cortisol": DimensionProfile(baseline=0.40, volatility=0.8),
                    "acetylcholine": DimensionProfile(baseline=0.65, volatility=0.7),
                    "oxytocin": DimensionProfile(baseline=0.20, volatility=0.4),
                },
            ),
            soul=load_file(ROOT / "scenario/people/players/seraphina/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/players/seraphina/IDENTITY.md"),
            initial_scene=(
                "You push open the door of The Gilded Trinket. A bell chimes. "
                "Narrow, cluttered, dim oil lamp light. Shelves of rusty tools, "
                "old weapons, curios. A locked glass display case at the counter "
                "holds the more interesting items — you notice a tarnished silver ring "
                "with a dark stone that seems to catch the lamplight oddly. "
                "Behind the counter stands a tall, lean figure with faintly "
                "shimmering bronze scales and piercing green eyes that are "
                "already weighing you. Smells of dust and polish."
            ),
        ),
        "tavian": CharacterSession(
            character=NPC(
                id="tavian", name="Tavian Drakescale", race="Half-Dragon (Bronze)",
                character_type="npc",
                role="Pawnbroker, The Gilded Trinket",
                home_location="gilded_trinket",
                dexterity=12, intelligence=14, wisdom=13, charisma=14,
                hp=18, ac=13,
                knowledge=[
                    "The obelisk shard ring in the display case is dangerous — a villager pawned it after nightmares and compulsions",
                    "The cracked compass and stone amulet are genuinely magical",
                    "The map fragment shows part of the Drowned Isle coastline",
                    "His smuggling contacts could source rare items but he avoids using them",
                ],
                active_concerns=[
                    "The obelisk shard ring — what to do with it",
                    "His medallion — will not discuss or sell",
                    "His smuggling past resurfacing",
                ],
                location="gilded_trinket",
            ),
            condition=CharacterCondition(
                character_id="tavian",
                character_name="Tavian",
                state=NeurochemicalState(
                    dopamine=0.50, cortisol=0.35, norepinephrine=0.50,
                    endorphins=0.55, serotonin=0.60, acetylcholine=0.70,
                    oxytocin=0.30,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.50, volatility=0.5),
                    "cortisol": DimensionProfile(baseline=0.30, volatility=0.6),
                    "serotonin": DimensionProfile(baseline=0.60, volatility=0.4),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/tavian/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/npcs/tavian/IDENTITY.md"),
            initial_scene=(
                "The bell above the door chimes. A half-elf woman steps in — "
                "raven-black hair, dark leather armor, green eyes that are already "
                "scanning every shelf. She moves with the quiet economy of someone "
                "who knows how to move without being heard. Rogue, almost certainly. "
                "A faint scar on her right cheek. Silver crescent moon pendant at her throat. "
                "Her gaze lingers on the display case — specifically on the ring. "
                "The ring with the dark stone you have been trying to decide what to do with."
            ),
        ),
    }

    seraphina_llm = make_call_llm("anthropic", "claude-sonnet-4-20250514")
    tavian_llm = make_call_llm("openai", "gpt-4o")

    roles = {
        "seraphina": RoleSet(
            player_left=PlayerLeft(call_llm=seraphina_llm),
            player_right=PlayerRight(call_llm=seraphina_llm),
            dm_left=DMLeft(call_llm=seraphina_llm),
            dm_right=DMRight(call_llm=seraphina_llm),
        ),
        "tavian": RoleSet(
            player_left=PlayerLeft(call_llm=tavian_llm),
            player_right=PlayerRight(call_llm=tavian_llm),
            dm_left=DMLeft(call_llm=tavian_llm),
            dm_right=DMRight(call_llm=tavian_llm),
        ),
    }

    place_md = load_file(
        ROOT / "scenario/places/driftmoor/gilded_trinket/PLACE.md"
    )
    contents_md = load_file(
        ROOT / "scenario/places/driftmoor/gilded_trinket/CONTENTS.md"
    )
    obelisk_lore = load_file(ROOT / "scenario/things/obelisk_shards.md")
    game_state_summary = (
        "# Scene: The Gilded Trinket (Pawnshop)\n\n"
        f"{place_md}\n\n"
        f"{contents_md}\n\n"
        "# Relevant Lore (DM only)\n\n"
        f"{obelisk_lore}\n\n"
        "# Scene Notes\n\n"
        "This is an exploration/social scene in a pawnshop. No combat expected.\n"
        "Seraphina has an unexplained latent arcane ability — she may sense the "
        "obelisk shard's resonance where others would not.\n"
        "Tavian knows the ring is dangerous but has not decided what to do with it.\n"
        "The cracked compass and stone amulet are genuinely magical — Tavian knows.\n"
        "\n"
        "# Exit Motivations (DM only)\n\n"
        "Characters may leave this scene. Recognise and permit these:\n"
        "- Seraphina has not eaten since arriving in Driftmoor. "
        "The Weary Traveler tavern is nearby and she can smell bread from the bakery.\n"
        "- If the ring's resonance unsettles her, she may seek out "
        "Elyssa Moonglow at her cottage — the local herbalist who studies shards.\n"
        "- Tavian may mention the strange symbols at the forge if the "
        "conversation turns to the obelisk or dark magic.\n"
        "- Seraphina is a rogue — she may want to case other shops or find lodging.\n"
    )

    return SceneConfig(
        scene_name="gilded_trinket",
        title="GILDED TRINKET",
        narrative_title="The Gilded Trinket",
        transcript_title="GILDED TRINKET — Seraphina, Tavian",
        character_summary="Seraphina (Claude), Tavian (GPT-4o)",
        characters=characters,
        roles=roles,
        game_state_summary=game_state_summary,
        default_turns=4,
    )
