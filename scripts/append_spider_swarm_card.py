from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph


SOURCE = Path("/Users/jeff/Desktop/D&D/Driftmoor Creature Cards - with Drow.docx")
OUTPUT = Path("/Users/jeff/Python/Driftmoor/output/docx/Driftmoor Creature Cards - with Drow and Spider Swarm.docx")


def append_clone(doc, paragraph):
    element = deepcopy(paragraph._p)
    doc._body._element.sectPr.addprevious(element)
    return Paragraph(element, doc._body)


def replace_runs(paragraph, parts):
    paragraph.clear()
    for text, bold, italic, size in parts:
        run = paragraph.add_run(text)
        run.bold = bold
        run.italic = italic
        if size is not None:
            from docx.shared import Pt
            run.font.size = Pt(size)
    return paragraph


def title(doc, template, name, side):
    p = append_clone(doc, template)
    return replace_runs(p, [(name, True, None, 15), (f"   {side}", True, None, 7)])


def labeled(doc, template, label, text):
    p = append_clone(doc, template)
    return replace_runs(p, [(label, True, None, 7.5), (text, None, None, 7.5)])


def plain(doc, template, text, italic=False):
    p = append_clone(doc, template)
    p.clear()
    run = p.add_run(text)
    run.italic = italic
    return p


def section(doc, template, text):
    p = append_clone(doc, template)
    p.clear()
    p.add_run(text)
    return p


def set_cell_text(cell, text):
    p = cell.paragraphs[0]
    if p.runs:
        p.runs[0].text = text
        for run in p.runs[1:]:
            run.text = ""
    else:
        p.add_run(text)


def main():
    doc = Document(SOURCE)
    paras = doc.paragraphs

    page_break = paras[400]
    title_template = paras[401]
    subtitle_template = paras[369]
    labeled_template = paras[370]
    section_template = paras[373]
    plain_template = paras[403]

    append_clone(doc, page_break)
    title(doc, title_template, "Spider Swarm", "FRONT")
    p = append_clone(doc, subtitle_template)
    replace_runs(p, [("Small Beast  •  Unaligned  •  CR 1/2 (100 XP)", None, True, 7.5)])

    table_element = deepcopy(doc.tables[-1]._tbl)
    doc._body._element.sectPr.addprevious(table_element)
    table = doc.tables[-1]
    top = ["AC 12 (natural armor)", "AC 12 (natural armor)", "HP 22 (5d8)", "HP 22 (5d8)", "SPEED 20 ft.; climb 20 ft.", "SPEED 20 ft.; climb 20 ft."]
    scores = ["3 (-4)", "13 (+1)", "10 (+0)", "1 (-5)", "2 (-4)", "1 (-5)"]
    for cell, value in zip(table.rows[0].cells, top):
        set_cell_text(cell, value)
    for cell, value in zip(table.rows[2].cells, scores):
        set_cell_text(cell, value)

    labeled(doc, labeled_template, "Skills: ", "Stealth +7")
    labeled(doc, labeled_template, "Senses: ", "Blindsight 10 ft.; Darkvision 20 ft.; Passive Perception 8")
    section(doc, section_template, "Features")
    labeled(doc, labeled_template, "Spider Climb: ", "The swarm can climb difficult surfaces, including upside down on ceilings, without needing an ability check.")
    labeled(doc, labeled_template, "Web Sense: ", "While in contact with a web, the swarm knows the exact location of any other creature in contact with the same web.")
    labeled(doc, labeled_template, "Web Walker: ", "The swarm ignores movement restrictions caused by webbing.")
    section(doc, section_template, "Actions")
    labeled(doc, labeled_template, "Bite: ", "Melee Weapon Attack: +3 to hit, reach 0 ft., one target. Hit: 10 (4d4) piercing damage, or 5 (2d4) piercing damage if the swarm has half its hit points or fewer. The target must make a DC 11 Constitution saving throw, taking 9 (2d8) poison damage on a failed save, or half as much on a success. If the poison reduces the target to 0 hit points, it is stable but poisoned for 1 hour and paralyzed while poisoned this way.")
    labeled(doc, labeled_template, "Web (Recharge 5–6): ", "Ranged Weapon Attack: +5 to hit, range 30/60 ft., one Large or smaller creature. Hit: The target is restrained by webbing. It can use an action to make a DC 12 Strength check, bursting the webbing on a success. The webbing can also be attacked and destroyed (AC 10; 5 hp; vulnerable to fire damage; immune to bludgeoning, poison, and psychic damage).")

    append_clone(doc, page_break)
    title(doc, title_template, "Spider Swarm", "BACK")
    section(doc, section_template, "At a glance")
    plain(doc, plain_template, "Hundreds of newly hatched spiders move as one hungry mass, reading vibrations through silk and pouring from ceiling cracks, freight containers, or ruptured egg sacs.")
    section(doc, section_template, "Tactics")
    plain(doc, plain_template, "The swarm clings to ceilings until prey passes beneath it, then drops onto the nearest exposed creature. It webs escape routes, surrounds one target, and bites through gaps in armor. It does not pursue prey through open flame or far beyond its nursery.")
    section(doc, section_template, "Run it quickly")
    plain(doc, plain_template, "Above half hit points, engulf and restrain isolated prey. At half hit points or fewer, use the reduced bite damage and scatter toward walls, drains, cracks, or upper webs—especially if fire reaches the webbing.", italic=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
