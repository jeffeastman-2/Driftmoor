"""Build two-page, double-sided 'player card' handouts (crunch on the front,
prose on the back), matching the format the user used for game 1's physical
cards, at a print-friendly 12pt body size."""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from character_sheet_pdf import INK, MUTED, GOLD, LINE, M, W, H, _text, _wrapped_lines

PLAYERS = Path("scenario/people/players")

ABILITY_ORDER = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
BODY_SIZE = 12
BODY_LEADING = 15


def _rule(c: canvas.Canvas, y: float) -> None:
    c.setStrokeColor(LINE)
    c.setLineWidth(.7)
    c.line(M, y, W - M, y)


def _header(c: canvas.Canvas, d: dict, page: int) -> None:
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 8)
    c.drawString(M, H - M - 10, "DRIFTMOOR")
    c.setFillColor(MUTED); c.setFont("Helvetica", 7)
    c.drawRightString(W - M, H - M - 10, f"PLAYER CARD  |  PAGE {page} OF 2")
    _rule(c, H - M - 15)


def _section_label(c: canvas.Canvas, title: str, x: float, y: float) -> None:
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, title.upper())


def _bullets(c: canvas.Canvas, items: list, x: float, y: float, width: float,
             size: float = BODY_SIZE, leading: float = BODY_LEADING) -> float:
    for label, desc in items:
        prefix = f"{label} – " if desc else (f"{label}" if label else "")
        full = f"{prefix}{desc}" if desc else label
        lines = _wrapped_lines(full, width - 12, "Helvetica", size)
        c.setFillColor(GOLD)
        c.circle(x + 2, y + 3, 1.6, stroke=0, fill=1)
        for i, line in enumerate(lines):
            if i == 0 and prefix:
                c.setFillColor(INK); c.setFont("Helvetica-Bold", size)
                c.drawString(x + 9, y, prefix)
                bold_w = stringWidth(prefix, "Helvetica-Bold", size)
                c.setFont("Helvetica", size)
                c.drawString(x + 9 + bold_w, y, line[len(prefix):])
            else:
                c.setFillColor(INK); c.setFont("Helvetica", size)
                c.drawString(x + 9, y, line)
            y -= leading
    return y


def draw_front(c: canvas.Canvas, d: dict) -> None:
    _header(c, d, 1)
    y = H - M - 40

    c.setFillColor(INK); c.setFont("Helvetica-Bold", 19)
    for line in _wrapped_lines(f"{d['player']} is {d['name']}", W - 2 * M, "Helvetica-Bold", 19):
        c.drawString(M, y, line)
        y -= 22
    c.setFillColor(MUTED); c.setFont("Helvetica", BODY_SIZE)
    c.drawString(M, y, f"{d['race']} {d['char_class_short']}")
    y -= BODY_LEADING + 6

    c.setFillColor(INK); c.setFont("Helvetica-Bold", BODY_SIZE)
    c.drawString(M, y, "Race:"); c.setFont("Helvetica", BODY_SIZE); c.drawString(M + 45, y, d["race"])
    c.setFont("Helvetica-Bold", BODY_SIZE); c.drawString(300, y, "Alignment:")
    c.setFont("Helvetica", BODY_SIZE); c.drawString(365, y, d["alignment"])
    y -= BODY_LEADING
    c.setFillColor(INK); c.setFont("Helvetica-Bold", BODY_SIZE)
    c.drawString(M, y, "Class:"); c.setFont("Helvetica", BODY_SIZE); c.drawString(M + 45, y, d["char_class"])
    y -= BODY_LEADING
    c.setFillColor(INK); c.setFont("Helvetica-Bold", BODY_SIZE)
    c.drawString(M, y, "Background:"); c.setFont("Helvetica", BODY_SIZE); c.drawString(M + 80, y, d["background"])
    c.setFont("Helvetica-Bold", BODY_SIZE); c.drawString(300, y, "Hit Points:")
    c.setFont("Helvetica", BODY_SIZE); c.drawString(370, y, str(d["hp"]))
    c.setFont("Helvetica-Bold", BODY_SIZE); c.drawString(420, y, "AC:")
    c.setFont("Helvetica", BODY_SIZE); c.drawString(445, y, str(d["ac"]))
    y -= BODY_LEADING + 8
    _rule(c, y); y -= 22

    _section_label(c, "Stats", M, y); y -= 20
    col_w = (W - 2 * M) / 3
    for i, key in enumerate(ABILITY_ORDER):
        col, row = i % 3, i // 3
        x = M + col * col_w
        cy = y - row * 22
        score, mod = d["stats"][key]
        c.setFillColor(INK); c.setFont("Helvetica-Bold", BODY_SIZE)
        c.drawString(x, cy, f"{key}:")
        c.setFont("Helvetica", BODY_SIZE)
        c.drawString(x + 40, cy, f"{score} ({mod:+d})")
    y -= 22 * 2 + 10
    _rule(c, y); y -= 22

    _section_label(c, "Proficiencies", M, y); y -= 20
    y = _bullets(c, d["proficiencies"], M, y, W - 2 * M)
    y -= 8
    _rule(c, y); y -= 22

    _section_label(c, "Equipment", M, y); y -= 20
    _bullets(c, [(item, "") for item in d["equipment"]], M, y, W - 2 * M)


def draw_back(c: canvas.Canvas, d: dict) -> None:
    _header(c, d, 2)
    y = H - M - 40

    c.setFillColor(INK); c.setFont("Helvetica-Bold", 15)
    c.drawString(M, y, d["name"])
    y -= 24

    _section_label(c, "Personality Traits", M, y); y -= 20
    y = _text(c, d["personality"], M, y, W - 2 * M, size=BODY_SIZE, leading=BODY_LEADING)
    y -= 14
    _rule(c, y); y -= 22

    _section_label(c, "Race & Class Profile", M, y); y -= 20
    y = _text(c, d["profile"], M, y, W - 2 * M, size=BODY_SIZE, leading=BODY_LEADING)
    y -= 14
    _rule(c, y); y -= 22

    _section_label(c, "Backstory", M, y); y -= 20
    _text(c, d["backstory"], M, y, W - 2 * M, size=BODY_SIZE, leading=BODY_LEADING)


def save(d: dict, slug: str) -> None:
    out_dir = PLAYERS / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{d['name'].split()[0]}_Card.pdf"
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setTitle(f"{d['name']} - Driftmoor Player Card")
    draw_front(c, d)
    c.showPage()
    draw_back(c, d)
    c.save()
    print(path.resolve())


def main() -> None:
    rowan = dict(
        player="Amy", name="Rowan Ashvale", race="Human", char_class="Druid (Circle of the Land — Forest)",
        char_class_short="Druid", background="Hermit", alignment="Neutral Good", hp=24, ac=15,
        stats={"STR": (10, 0), "DEX": (14, 2), "CON": (14, 2), "INT": (12, 1), "WIS": (16, 3), "CHA": (10, 0)},
        proficiencies=[
            ("Wild Shape", "transform into a small animal (CR 1/4 or lower); 2 uses per rest — great for scouting or escape"),
            ("Natural Recovery", "once per day on a short rest, recover some spent spell slots"),
            ("Spellcasting (Wisdom)", "save DC 13, spell attack +5"),
            ("Druidic", "a secret language known only to druids"),
            ("Skilled", "proficient in Medicine, Nature, Survival, and Religion"),
        ],
        equipment=["Leather armor and wooden shield (AC 15)", "Sickle and quarterstaff",
                   "Herbalism kit and healer's kit", "Sprig of dried yarrow (spellcasting focus)"],
        personality=("Unhurried and exacting, Rowan treats every crisis like a diagnosis to be made rather than a "
                     "fight to be won — she asks about sleep and food before she asks about danger."),
        profile=("Weathered and quietly strong, with sun-browned skin, close-cropped brown hair threaded with "
                 "early gray, and calm green eyes that catalogue a room's health at a glance. She wears a patched "
                 "hide tunic dyed moss-green, a satchel of dried herbs at her hip, and carries a sickle worn smooth "
                 "with use."),
        backstory=("Rowan grew up the daughter of a village midwife in Ashvale, learning early that medicine is "
                   "equal parts skill and mercy. When a plague swept through the village, she exhausted every "
                   "remedy she knew and watched people die anyway — including some she'd promised to save. "
                   "Afterward, an old herbalist at the wood's edge took her in and taught her that the forest holds "
                   "cures no apothecary does, if you're patient enough to listen for them. Rowan left Ashvale with "
                   "a druid's calling and an empty ceramic vial she still carries — the last cure that arrived "
                   "a day too late. She wanders now wherever sickness or rumor of it leads her, still hunting the "
                   "causes doctors miss, still unsure whether the forest's patience will ever fully answer for the "
                   "village she couldn't save."),
    )

    garron = dict(
        player="Tom", name="Garron Ironvow", race="Mountain Dwarf", char_class="Paladin (Oath of Devotion)",
        char_class_short="Paladin", background="Acolyte", alignment="Lawful Good", hp=31, ac=18,
        stats={"STR": (16, 3), "DEX": (10, 0), "CON": (16, 3), "INT": (10, 0), "WIS": (12, 1), "CHA": (14, 2)},
        proficiencies=[
            ("Divine Sense", "sense celestials, fiends, and undead within 60 ft; 3 uses per long rest"),
            ("Lay on Hands", "a 15-point healing pool — touch to heal, or spend 5 to cure disease or poison"),
            ("Divine Smite", "spend a spell slot on a melee hit for a burst of extra radiant damage"),
            ("Channel Divinity", "once per rest — make a weapon supernaturally accurate and glowing, or try to force undead/fiends to flee"),
            ("Trained for War", "proficient with heavy armor, shields, and all weapons"),
        ],
        equipment=["Chain mail and shield with a sunburst sigil (AC 18)", "Longsword and three javelins",
                   "Iron sunburst holy symbol and prayer book", "Priest's pack"],
        personality=("Plainspoken and steady, Garron measures every kindness against a vow he's not sure he's "
                     "finished paying — he forgives everyone else faster than he forgives himself."),
        profile=("Broad and grey-bearded even by dwarven standards, Garron stands like a doorway nothing gets "
                 "through without his say-so. His beard is bound in three iron rings, one etched with a psalm he "
                 "recited over his brother's grave. He wears dented chain mail over a threadbare devotional "
                 "tabard, and his shield bears a hand-hammered sunburst that has taken more blows than his face "
                 "has."),
        backstory=("Garron was raised within the Hammerlight Vigil, a dwarven martial order that trains its "
                   "acolytes as much in scripture as in the shield wall. He and his younger brother swore their "
                   "oaths together, expecting to serve side by side for decades. His brother died on Garron's "
                   "watch during a raid gone wrong — a failure Garron has never fully forgiven himself for, "
                   "though the Vigil absolved him formally within a season. He bound his brother's memory into his "
                   "beard as a second iron ring, and has worn it, alongside a third etched with a half-remembered "
                   "psalm, ever since. Garron left the Vigil's halls following a conviction he can't fully "
                   "explain — a sense that something in Driftmoor will test whether the vow he renewed at his "
                   "brother's grave still holds. He hasn't decided whether that's providence, guilt, or both, but "
                   "he's stopped waiting to find out."),
    )

    kaelin = dict(
        player="Neala", name="Kaelin Brightspark", race="Human", char_class="Bard (College of Lore)",
        char_class_short="Bard", background="Entertainer", alignment="Chaotic Good", hp=27, ac=13,
        stats={"STR": (8, -1), "DEX": (14, 2), "CON": (12, 1), "INT": (12, 1), "WIS": (10, 0), "CHA": (18, 4)},
        proficiencies=[
            ("Bardic Inspiration", "bonus action, give an ally a d6 to add to an attack, check, or save; 4 uses per long rest"),
            ("Jack of All Trades", "add half proficiency bonus to any check you're not already trained in"),
            ("Cutting Words", "reaction — spend a Bardic Inspiration die to subtract from an enemy's roll after it's made"),
            ("Expertise", "double proficiency in Performance and Persuasion"),
            ("Spellcasting (Charisma)", "save DC 14, spell attack +6"),
        ],
        equipment=["Leather armor (AC 13)", "Rapier, dagger, and belt knife",
                   "Well-worn lute carved with vines and leaves", "Musician's pack"],
        personality=("Bright and quick-witted, Kaelin fills every room she enters and rarely lets anyone see what "
                     "the brightness is covering."),
        profile=("Slender and attractive with a presence that fills the room. Wild red curls, bright hazel eyes, "
                 "a mischievous grin rarely absent from her freckled face. Clothing a riot of emerald green and "
                 "deep gold patches. A well-worn lute carved with vines and leaves rests across her back."),
        backstory=("Kaelin grew up trading songs for coin in taverns across the region, learning early that a good "
                   "story could talk her out of almost any trouble. That confidence cracked the night a tyrannical "
                   "noble, stung by one of her sharper verses, burned down the inn where she was performing — and "
                   "several friends who'd sheltered her didn't get out. She carries the guilt quietly, wrapped in "
                   "the same charm she uses for everything else, and has never quite stopped performing even when "
                   "the audience is just herself. She travels now with a College of Lore's restless curiosity and "
                   "a private vow, never spoken aloud, to make her words count for something better than spite."),
    )

    brenna = dict(
        player="Ann", name="Brenna Carrowmere", race="Human", char_class="Fighter (Battle Master)",
        char_class_short="Fighter", background="Knight of the Order", alignment="Lawful Good", hp=28, ac=16,
        stats={"STR": (16, 3), "DEX": (12, 1), "CON": (14, 2), "INT": (10, 0), "WIS": (11, 0), "CHA": (13, 1)},
        proficiencies=[
            ("Combat Superiority", "4 superiority dice (d8) — attach to attacks for maneuvers like Precision Attack, Riposte, Trip Attack"),
            ("Second Wind", "bonus action, heal 1d10+3 HP once per short rest"),
            ("Action Surge", "take a whole extra action once per short rest"),
            ("Great Weapon Fighting", "reroll 1s and 2s on weapon damage dice"),
            ("Skilled", "proficient in Athletics, Insight, Intimidation, Survival, and smith's tools"),
        ],
        equipment=["Chain mail (AC 16)", "Greatsword, dagger, and light crossbow",
                   "Explorer's pack and smith's tools", "Bronze Whitecairn falcon badge"],
        personality=("Plain-spoken and steady, Brenna keeps people at arm's length with politeness and lets her "
                     "actions do the vouching instead."),
        profile=("Tall and broad-shouldered, built by decades of drill and road work. Pale skin is weathered "
                 "across the cheekbones; her hair, the color of wet straw, is cut short and practical. A long pale "
                 "scar runs from left temple to jaw. She wears chain mail beneath a faded russet-and-green "
                 "surcoat bearing the Carrowmere reed, and carries her greatsword with the ease of long habit."),
        backstory=("Brenna trained from childhood as a Knight of the Order, learning that a sworn word binds "
                   "harder than iron and costs more than blood. She served for years alongside Ser Halmond, a "
                   "mentor she still measures herself against, until she lost him on a campaign she doesn't "
                   "discuss. She came to Driftmoor to honor a contract whose sponsor died before she arrived, "
                   "meaning to stay only a week — she's stayed considerably longer, evaluating the people around "
                   "her with the same professional care and personal reluctance she brings to everything, unsure "
                   "yet whether this is another waystation or the start of an oath she's postponed for eleven "
                   "years."),
    )

    cinnabar = dict(
        player="MC", name="Cinnabar", race="Wood Elf", char_class="Rogue (Arcane Trickster)",
        char_class_short="Rogue", background="Criminal (Burglar)", alignment="Chaotic Good", hp=24, ac=15,
        stats={"STR": (8, -1), "DEX": (17, 3), "CON": (14, 2), "INT": (14, 2), "WIS": (12, 1), "CHA": (13, 1)},
        proficiencies=[
            ("Sneak Attack", "2d6 extra damage once per turn with advantage or an ally adjacent to the target"),
            ("Cunning Action", "Dash, Disengage, or Hide as a bonus action"),
            ("Mage Hand Legerdemain", "an invisible spectral hand that can pick locks or lift objects at range"),
            ("Expertise", "double proficiency in Stealth and Thieves' Tools"),
            ("Spellcasting (Intelligence)", "save DC 12, spell attack +4"),
        ],
        equipment=["Studded leather (AC 15)", "Rapier, shortbow, and dagger",
                   "Thieves' tools and burglar's pack", "Unexplained silver ring"],
        personality=("Quick and dry-humored, Cinnabar deflects praise and confession alike with perfect timing, "
                     "then quietly shows up when it matters."),
        profile=("Slight and quick, with copper-red hair cut unevenly short, freckled olive skin, and moss-green "
                 "eyes that miss very little. She dresses in charcoal leathers and a wine-red scarf, moving with "
                 "practiced economy. A silver ring she never explains stays on her hand even in sleep."),
        backstory=("Cinnabar cut her teeth as a burglar working the rooftops for a guild she's since put a great "
                   "deal of distance between herself and. An old bond, represented by an unexplained silver ring "
                   "she never removes even in sleep, still shapes more of her choices than she'd admit. She "
                   "arrived in Driftmoor chasing rumors of a moor-witch who trades secrets for memories, unsure "
                   "whether that's exactly what she needs or exactly what would ruin her — so for now she "
                   "watches, listens, and keeps one hand close to every metaphorical lock, including the one on "
                   "herself."),
    )

    hendricks = dict(
        player="Richard", name="Hendricks Aldemar Vey", race="Human", char_class="Wizard (School of Divination)",
        char_class_short="Wizard", background="Sage", alignment="Neutral Good", hp=17, ac=12,
        stats={"STR": (8, -1), "DEX": (14, 2), "CON": (12, 1), "INT": (17, 3), "WIS": (15, 2), "CHA": (11, 0)},
        proficiencies=[
            ("Portent", "record two d20 rolls after a long rest and substitute either for any roll made by you or another creature"),
            ("Arcane Recovery", "once per day on a short rest, recover some spent spell slots"),
            ("Ritual Casting", "cast ritual-tagged spells without using a spell slot"),
            ("Spellcasting (Intelligence)", "save DC 13, spell attack +5"),
            ("Skilled", "proficient in Arcana, History, Insight, Investigation, and Medicine"),
        ],
        equipment=["Quarterstaff and component pouch", "Spellbook and scholar's pack",
                   "Mended blue robes", "Leather notebook containing Ilse's last letters"],
        personality=("Gentle and careful with his words, Hendricks qualifies every claim he makes and treats "
                     "foreknowledge as an obligation rather than an advantage."),
        profile=("A thin, slightly stooped man with wispy white hair, a well-kept beard, and pale blue eyes. His "
                 "dark blue robes are visibly mended. He carries an ash staff and pockets full of small objects, "
                 "each with a story."),
        backstory=("Hendricks spent most of his life as a retired scholar chasing questions rather than answers, "
                   "until the death of Ilse — a colleague whose last letters he still carries — left him with a "
                   "question he couldn't research his way out of. He followed fourteen days of matching auguries "
                   "to reach Driftmoor, treating the pattern as either providence or a problem worth solving "
                   "properly. He behaves like a man still quietly in office: collecting observations, testing "
                   "whether wisdom is possible once regret has become part of the method, and wondering — more "
                   "than he lets on — why this particular town keeps appearing in his portents."),
    )

    pippa = dict(
        player="Terry", name="Pippa Thistlewren", race="Fairy", char_class="Sorcerer (Wild Magic)",
        char_class_short="Sorcerer", background="Entertainer", alignment="Chaotic Good", hp=17, ac=12,
        stats={"STR": (8, -1), "DEX": (15, 2), "CON": (13, 1), "INT": (12, 1), "WIS": (10, 0), "CHA": (17, 3)},
        proficiencies=[
            ("Wild Magic Surge", "casting a spell may trigger a random magical effect"),
            ("Tides of Chaos", "gain advantage on one roll; refreshes after a long rest or a surge"),
            ("Fey Flight", "30 ft flying speed"),
            ("Spellcasting (Charisma)", "save DC 13, spell attack +5"),
            ("Skilled", "proficient in Arcana, Persuasion, Performance, and Insight"),
        ],
        equipment=["Silver-chain wand (arcane focus)", "Dagger",
                   "Small explorer's pack and patchwork clothes", "Locket containing a charred splinter"],
        personality=("Bright and impulsive, Pippa talks fast, loves fast, and treats curiosity as something close "
                     "to sacred."),
        profile=("Small even for a fairy, all quick wings and kinetic posture, with wild dark curls full of "
                 "leaves and accidental trophies. Her brown skin catches a faint shimmer that brightens when she "
                 "is excited. Lavender eyes track three things at once, and her clothes look assembled from joy, "
                 "weather, and impulse."),
        backstory=("Pippa left the Whistlewren, her fey family, chasing old fey knowledge and a question she's "
                   "never quite said out loud. A locket holding a charred splinter from a childhood barn fire "
                   "travels everywhere with her — a private shame she hasn't resolved, tangled up with the wild "
                   "magic she's still learning to trust rather than fear. She arrived in Driftmoor mid-thunderstorm "
                   "asking everyone she met about the moor-witch, and has since found people before she found "
                   "answers. She's pretending those are separate outcomes and hasn't quite convinced herself."),
    )

    tobin = dict(
        player="Dave", name="Tobin Aldermere", race="Half-Elf", char_class="Cleric (Life Domain)",
        char_class_short="Cleric", background="Acolyte", alignment="Neutral Good", hp=24, ac=18,
        stats={"STR": (12, 1), "DEX": (10, 0), "CON": (14, 2), "INT": (11, 0), "WIS": (16, 3), "CHA": (14, 2)},
        proficiencies=[
            ("Disciple of Life", "healing spells restore extra HP automatically"),
            ("Channel Divinity", "once per rest — Turn Undead, or Preserve Life to distribute 15 HP among allies"),
            ("Spellcasting (Wisdom)", "save DC 13, spell attack +5"),
            ("Skilled", "proficient in Insight, Medicine, Persuasion, and Religion"),
        ],
        equipment=["Chain mail and shield with Bright Hearth sigil (AC 18)", "Mace",
                   "Wooden holy symbol and prayer book", "Healer's kit and travel journal of names"],
        personality=("Warm and unhurried, Tobin counsels through stories and asks more questions than he "
                     "answers."),
        profile=("Broad-shouldered and comfortably grounded, with brown hair gone silver at the temples and warm "
                 "eyes lined by easy laughter. His traveling clothes are practical and worn clean, and his wooden "
                 "holy symbol hangs at his chest with the familiarity of a second heartbeat. He carries a mace as "
                 "a reluctant necessity rather than an identity."),
        backstory=("Tobin trained as an acolyte of the Bright Hearth, a domestic, hospitality-centered faith that "
                   "taught him healing outranks argument in a crisis. He intended only to pass through Driftmoor "
                   "on his circuit, but kept finding one more person who needed him and one more reason to stay — "
                   "first taking on chapel calls to support an overworked local priest, then simply staying. He "
                   "suspects that's either providence or vanity, and has decided he's willing to be corrected by "
                   "events either way. His travel journal, filled with names of people he's helped, has gotten "
                   "considerably longer than he planned."),
    )

    save(kaelin, "kaelin")
    save(brenna, "brenna")
    save(cinnabar, "cinnabar")
    save(hendricks, "hendricks")
    save(pippa, "pippa")
    save(tobin, "tobin")
    save(rowan, "rowan")
    save(garron, "garron")


if __name__ == "__main__":
    main()
