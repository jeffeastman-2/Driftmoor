"""Build Kaelin Brightspark's current two-page player sheet."""

from pathlib import Path

from character_generation import CharacterDraft
from character_sheet_pdf import character_sheet_pdf


def main() -> None:
    draft = CharacterDraft(
        name="Kaelin Brightspark",
        player="Neala",
        pronouns="she/her",
        gender="Woman",
        race="Human",
        character_class="Bard (College of Lore)",
        level=4,
        background="Entertainer",
        alignment="Chaotic Good",
        physical_description=(
            "Slender and striking, with wild red curls, bright hazel eyes, freckles, "
            "and a mischievous grin. Her clothes are a riot of emerald and deep gold "
            "patches. A well-worn lute carved with vines and leaves rests across her back."
        ),
        hp=27,
        ac=10,
        speed="30 ft",
        strength=8,
        dexterity=14,
        constitution=12,
        intelligence=12,
        wisdom=10,
        charisma=18,
        abilities=[
            "AC: base 10; 13 while wearing leather armor",
            "Initiative +3; saving throws: Dexterity +4, Charisma +6",
            "Expertise: Performance +8, Persuasion +8",
            "Lore proficiencies: Arcana +3, History +3, Insight +2",
            "Jack of All Trades: +1 to non-proficient ability checks",
            "Bardic Inspiration d6: 4 uses per long rest; bonus action, 60 ft",
            "Song of Rest d6: allies spending Hit Dice regain +1d6 HP",
            "Cutting Words: reaction, spend Inspiration to reduce a foe's roll",
        ],
        spells=[
            "Spellcasting: Charisma; save DC 14; spell attack +6",
            "Slots: 1st 4, 2nd 3; spells known 7; cantrips known 3",
            "@SECTION Cantrips",
            "Vicious Mockery (action, 60 ft): Wis save; 1d4 psychic damage and disadvantage on its next attack before your next turn",
            "Minor Illusion (action, 30 ft, 1 min): create a sound or a still image no larger than a 5-ft cube; physical contact reveals it",
            "Message (action, 120 ft, 1 round): whisper to one creature you point at; it may whisper a reply only you hear",
            "@SECTION 1st-Level Spells",
            "Detect Magic (action/ritual, self, concentration 10 min): sense magic within 30 ft; an action reveals a visible aura's school",
            "Faerie Fire (action, 60 ft, concentration 1 min): creatures in a 20-ft cube make Dex saves; failures glow, cannot hide by invisibility, and attacks against them have advantage",
            "Healing Word (bonus action, 60 ft): one creature regains 1d4 + 4 HP; cannot cast another leveled spell that turn",
            "Dissonant Whispers (action, 60 ft): Wis save; 3d6 psychic and target uses its reaction to flee; half damage and no movement on success",
            "@SECTION 2nd-Level Spells",
            "Calm Emotions (action, 60 ft, concentration 1 min): Cha saves in a 20-ft-radius sphere; suppress charm/fear or make targets temporarily indifferent",
            "Detect Thoughts (action, self, concentration 1 min): read nearby surface thoughts; probing deeper allows a Wis save and reveals your intrusion",
            "Invisibility (action, touch, concentration 1 hr): target and carried gear become unseen until it attacks or casts a spell",
            "@SECTION Weapon Attacks",
            "Attacks: rapier +4 (1d8+2 piercing); dagger +4 (1d4+2 piercing)",
        ],
        equipment=[
            "Leather armor",
            "Rapier, dagger, and belt knife",
            "Well-worn lute carved with vines and leaves",
            "Musician's pack",
        ],
        purse="875 gp",
        mood="Bright, watchful beneath the brightness",
        disposition="Fiercely attached to the party, though she frames it as casual",
        open_threads=[
            "The tyrannical noble who burned the inn",
            "The friends killed in that fire",
            "The strange verse that entered The Fey Glade without her choosing",
        ],
        values_and_drives=[
            "Joy as resistance: laughter and music are deliberate acts of defiance.",
            "Carry hope for people who cannot carry it themselves.",
            "Treat every person as a story whose course can still be changed.",
            "Protect the people she loves, whatever the performance may suggest.",
        ],
        fears_and_wounds=[
            "The burning inn and the friends who died after her careless insult.",
            "That her own words may cause harm again.",
            "The silence in which old loss becomes audible.",
        ],
        voice_and_manner=[
            "Vibrant, quick, and infectious; she naturally fills a room.",
            "Frames danger and combat as stories with endings that can be changed.",
            "A sharp observer beneath the performance.",
            "Moves from bawdy tune to heartbreaking ballad without warning.",
        ],
        loyalties=[
            "The party, whom she privately regards as her second chance.",
            "The memory of the friends who died; her music carries their names.",
            "Her irreplaceable lute and the life of wandering it represents.",
        ],
        internal_contradiction=(
            "Kaelin presents herself as someone who has never been hurt. Her wrist "
            "tattoos, guarded care around powerful people, and fierce protectiveness "
            "tell a different story to anyone paying attention."
        ),
        signature_detail=(
            "Her vine-carved lute has survived everything with her. It is not merely "
            "an instrument and cannot be replaced."
        ),
    )

    output = Path("output/pdf/Kaelin_CharacterSheet.pdf")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(character_sheet_pdf(draft))
    print(output.resolve())


if __name__ == "__main__":
    main()
