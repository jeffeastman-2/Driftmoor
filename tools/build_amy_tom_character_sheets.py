"""Build player sheets for Rowan Ashvale (Amy) and Garron Ironvow (Tom)."""

from pathlib import Path

from character_generation import CharacterDraft
from character_sheet_pdf import character_sheet_pdf


PLAYERS = Path("scenario/people/players")


def save(draft: CharacterDraft, slug: str) -> None:
    out_dir = PLAYERS / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{draft.name.split()[0]}_CharacterSheet.pdf"
    path.write_bytes(character_sheet_pdf(draft))
    print(path.resolve())


def main() -> None:
    sheets = [
        (
            "rowan",
            CharacterDraft(
                name="Rowan Ashvale", player="Amy", pronouns="she/her", gender="Woman",
                race="Human", character_class="Druid (Circle of the Land — Forest)", level=3,
                background="Hermit", alignment="Neutral Good", hp=24, ac=10,
                strength=10, dexterity=14, constitution=14, intelligence=12, wisdom=16, charisma=10,
                physical_description=("Weathered and quietly strong, with sun-browned skin, close-cropped brown "
                                      "hair threaded with early gray, and calm green eyes that catalogue a room's "
                                      "health at a glance. She wears a patched hide tunic dyed moss-green, a satchel "
                                      "of dried herbs at her hip, and carries a sickle worn smooth with use."),
                abilities=["AC: base 10; 15 while wearing leather armor and a wooden shield",
                           "Saving throws: Intelligence +3, Wisdom +5; initiative +2",
                           "Medicine +5, Religion +3, Nature +3, Survival +5",
                           "Wild Shape: CR 1/4 beast, no swim/fly speed; 2 uses per short or long rest",
                           "Natural Recovery (Forest): once per day on a short rest, recover spell slots totaling half her druid level (round up)",
                           "Circle Spells (Forest, always prepared): Barkskin, Spider Climb",
                           "Druidic: the secret language of druids; can leave hidden messages"],
                spells=["Spellcasting: Wisdom; save DC 13; spell attack +5; slots: 1st 4, 2nd 2",
                        "@SECTION Cantrips",
                        "Produce Flame (action, self, 10 min): flickering flame sheds light; can be hurled 60 ft for 1d8 fire",
                        "Guidance (action, touch, concentration 1 min): target adds 1d4 to one ability check of its choice",
                        "Shillelagh (bonus action, touch): a club or quarterstaff uses Wisdom to hit and deals 1d8",
                        "@SECTION 1st-Level Spells",
                        "Cure Wounds (action, touch): restore 1d8 + 3 HP",
                        "Entangle (action, 90 ft, concentration 1 min): Str save or restrained by grasping weeds in a 20-ft square",
                        "Faerie Fire (action, 60 ft, concentration 1 min): creatures in a 20-ft cube outlined; attacks against them have advantage; Dex save negates",
                        "Goodberry (action, touch): 10 berries, each restores 1 HP and a day's food",
                        "@SECTION 2nd-Level Spells",
                        "Barkskin (action, touch, concentration 1 hr): target's AC can't be less than 16",
                        "Spike Growth (action, 150 ft, concentration 10 min): hazardous ground in a 20-ft radius; 2d4 piercing per 5 ft moved through it",
                        "@SECTION Weapon Attacks",
                        "Quarterstaff (Shillelagh) +5: 1d8 + 3 bludgeoning",
                        "Sickle +2: 1d4 slashing"],
                equipment=["Leather armor and wooden shield", "Sickle and quarterstaff",
                           "Herbalism kit and healer's kit", "Sprig of dried yarrow (druidic focus)"], purse="90 gp",
                mood="Calm, watchful, quietly tired", disposition="Warm toward the wounded, patient with everyone else",
                values_and_drives=["Every living thing deserves care, not just the ones who can pay for it.",
                                   "Nature's patience teaches what urgency cannot.",
                                   "Treat symptoms, but never stop hunting the cause.",
                                   "Earn trust through steady presence, not promises."],
                fears_and_wounds=["A plague she couldn't stop in her home village, remembered by name.",
                                  "Becoming so practical about death that she forgets to grieve it.",
                                  "Wild Shape slipping into instinct she can't fully call back.",
                                  "Being needed by everyone and known by no one."],
                voice_and_manner=["Unhurried, exact speech, like she's already triaging the room.",
                                  "Asks about sleep and food before asking about danger.",
                                  "Silence is a diagnostic tool, not discomfort.",
                                  "Warmth arrives in actions before it arrives in words."],
                loyalties=["The dead of Ashvale, whose names she still recites.",
                           "Anyone too stubborn to admit they're hurt.",
                           "The old herbalist who trained her out of grief.", "Companions who let themselves be tended."],
                internal_contradiction=("Rowan preaches patience but drove herself past exhaustion trying to outrun a "
                                        "plague. She insists nature keeps better time than people do, while pushing "
                                        "her own body far past its limits whenever someone she loves is at risk."),
                signature_detail="A cracked ceramic vial, empty, that once held the cure that arrived one day too late.",
                open_threads=["Whether Driftmoor's healers know something about the old plague",
                              "Wild Shape instincts she hasn't fully mastered", "The herbalist mentor she hasn't written to in months"],
            ),
        ),
        (
            "garron",
            CharacterDraft(
                name="Garron Ironvow", player="Tom", pronouns="he/him", gender="Man",
                race="Mountain Dwarf", character_class="Paladin (Oath of Devotion)", level=3,
                background="Acolyte", alignment="Lawful Good", hp=31, ac=10,
                strength=16, dexterity=10, constitution=16, intelligence=10, wisdom=12, charisma=14,
                physical_description=("Broad and grey-bearded even by dwarven standards, Garron stands like a doorway "
                                      "nothing gets through without his say-so. His beard is bound in three iron rings, "
                                      "one etched with a psalm he recited over his brother's grave. He wears dented "
                                      "chain mail over a threadbare devotional tabard, and his shield bears a "
                                      "hand-hammered sunburst that has taken more blows than his face has."),
                abilities=["AC: base 10; 16 in chain mail; 18 with chain mail and shield",
                           "Saving throws: Wisdom +3, Charisma +4; initiative +0",
                           "Athletics +5, Insight +3, Persuasion +4, Religion +2",
                           "Fighting Style — Protection: reaction, impose disadvantage on an attack against an ally within 5 ft while wielding a shield",
                           "Divine Sense: detect celestials, fiends, and undead within 60 ft; 3 uses per long rest",
                           "Lay on Hands: 15-HP pool per long rest; touch to heal, or spend 5 to cure a disease or neutralize a poison",
                           "Divine Smite: expend a spell slot on a melee hit for +2d8 radiant (+3d8 vs. undead/fiends; +1d8 per slot level above 1st)",
                           "Channel Divinity (1/rest): Sacred Weapon or Turn the Unholy"],
                spells=["Spellcasting: Charisma; save DC 12; spell attack +4; slots: 1st 3",
                        "@SECTION Oath Spells (always prepared)",
                        "Protection from Evil and Good (action, touch, concentration 10 min): target resists damage from and has advantage on saves against aberrations, celestials, elementals, fey, fiends, undead",
                        "Sanctuary (bonus action, 30 ft): attackers must pass a Wis save or choose another target; ends if the warded creature attacks or harms another",
                        "@SECTION 1st-Level Spells",
                        "Bless (action, 30 ft, concentration 1 min): up to 3 creatures add 1d4 to attack rolls and saving throws",
                        "Cure Wounds (action, touch): restore 1d8 + 2 HP",
                        "Shield of Faith (bonus action, 60 ft, concentration 10 min): one creature gains +2 AC",
                        "@SECTION Weapon Attacks",
                        "Longsword +5: 1d8 + 3 slashing (1d10 + 3 two-handed)",
                        "Javelin +5: 1d6 + 3 piercing; range 30/120"],
                equipment=["Chain mail and shield (sunburst sigil)", "Longsword and three javelins",
                           "Iron sunburst holy symbol and prayer book", "Priest's pack"], purse="140 gp",
                mood="Steady, solemn, quietly attentive", disposition="Protective by default, slow to fully trust",
                values_and_drives=["A vow is only as good as the day it costs you something.",
                                   "Mercy is not weakness; it is discipline aimed at another person's good.",
                                   "Speak the hard true thing before the comfortable false one.",
                                   "Stand exactly where the frightened person needs someone standing."],
                fears_and_wounds=["The brother he swore to protect and buried instead.",
                                  "Doubt arriving disguised as reasonable caution.",
                                  "Failing the oath quietly, in small omissions no one would notice.",
                                  "Being granted mercy he doesn't believe he's earned."],
                voice_and_manner=["Speaks plainly and slowly, like every sentence might be sworn testimony.",
                                  "Prays aloud without embarrassment, mid-conversation if it matters.",
                                  "Rarely raises his voice; lowers it instead when truly angry.",
                                  "Kindness delivered bluntly, without cushioning."],
                loyalties=["The Hammerlight Vigil, the dwarven martial order that raised him in the faith.",
                           "His brother's memory and the oath sworn at his grave.",
                           "Anyone too weak or too stubborn to defend themselves.",
                           "Companions who keep their word even when it costs them."],
                internal_contradiction=("Garron preaches mercy but privately measures every failure against a vow "
                                        "he's not sure he can ever finish paying off. He forgives everyone faster "
                                        "than he forgives himself, and mistakes that asymmetry for humility."),
                signature_detail="Three iron rings bound in his beard, one etched with a half-remembered psalm.",
                open_threads=["The debt he believes he still owes his brother's memory",
                              "Whether the Hammerlight Vigil would recognize the vow he's kept",
                              "Driftmoor's gathering danger, and whether devotion is enough to meet it"],
            ),
        ),
    ]
    for slug, draft in sheets:
        save(draft, slug)


if __name__ == "__main__":
    main()
