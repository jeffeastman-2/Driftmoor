from __future__ import annotations

from pathlib import Path
from datetime import date

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Driftmoor_Persistent_World_Architecture_Revised.docx"
ASSET_DIR = ROOT / "paper_assets"
ASSET_DIR.mkdir(exist_ok=True)

NAVY = "#17324D"
BLUE = "#2E74B5"
SLATE = "#52606D"
PALE = "#EEF3F7"
PALE_BLUE = "#E8F1F8"
WHITE = "#FFFFFF"
BLACK = "#111111"
RULE = "#B8C4CE"


def rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill.lstrip("#"))


def set_cell_margins(cell, top=90, start=120, bottom=90, end=120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_table_geometry(table, widths_dxa: list[int], indent_dxa: int = 120) -> None:
    total = sum(widths_dxa)
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(total))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), str(indent_dxa))
    tbl_ind.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths_dxa:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(widths_dxa[idx]))
            tc_w.set(qn("w:type"), "dxa")
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_field(paragraph, instruction: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    value = OxmlElement("w:t")
    value.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, value, end])


def add_hyperlink(paragraph, text: str, url: str):
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "2E74B5")
    r_pr.append(color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)
    run.append(r_pr)
    text_node = OxmlElement("w:t")
    text_node.text = text
    run.append(text_node)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def _font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _centered(draw, xy, text, font, fill, spacing=5):
    box = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, align="center")
    w, h = box[2] - box[0], box[3] - box[1]
    draw.multiline_text((xy[0] - w / 2, xy[1] - h / 2), text, font=font, fill=fill, spacing=spacing, align="center")


def _arrow(draw, start, end, fill=SLATE, width=5, both=False):
    draw.line([start, end], fill=fill, width=width)
    import math
    def head(tip, tail):
        angle = math.atan2(tip[1] - tail[1], tip[0] - tail[0])
        length = 18
        wing = 0.55
        pts = [
            tip,
            (tip[0] - length * math.cos(angle - wing), tip[1] - length * math.sin(angle - wing)),
            (tip[0] - length * math.cos(angle + wing), tip[1] - length * math.sin(angle + wing)),
        ]
        draw.polygon(pts, fill=fill)
    head(end, start)
    if both:
        head(start, end)


def make_pipeline_figure(path: Path) -> None:
    image = Image.new("RGB", (2160, 760), "white")
    draw = ImageDraw.Draw(image)
    _centered(draw, (1080, 70), "Authority shifts by stage; the current system is intentionally hybrid",
              _font(44, True), NAVY)
    boxes = [
        (45, 230, 290, 205, "Actor source", "human input or\nLLM Player-Left", "#F3F5F7"),
        (400, 230, 290, 205, "Action form", "ActionIntent +\nCharacterOutput", "#F3F5F7"),
        (755, 230, 290, 205, "Grounding", "LATN-first resolvers\n+ explicit fallback", "#E8F1F8"),
        (1110, 230, 290, 205, "Adjudication", "DM-Left and\nPython mechanics", "#FFF3D9"),
        (1465, 230, 290, 205, "Mutation", "positions, HP,\nitems, time, effects", "#E6F4EA"),
        (1820, 230, 290, 205, "Realization", "DM-Right\nnarration", "#F3E8FD"),
    ]
    for x, y, w, h, title, body, fill in boxes:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=20, fill=fill, outline=NAVY, width=4)
        _centered(draw, (x + w / 2, y + 62), title, _font(30, True), NAVY)
        _centered(draw, (x + w / 2, y + 137), body, _font(24), BLACK)
    for i in range(len(boxes) - 1):
        x1 = boxes[i][0] + boxes[i][2]
        x2 = boxes[i + 1][0]
        _arrow(draw, (x1 + 8, 332), (x2 - 8, 332), width=4)
    _arrow(draw, (1610, 485), (1610, 635), fill=BLUE, width=4, both=True)
    _centered(draw, (1610, 690), "Checkpoint / resume boundary", _font(27, True), BLUE)
    image.save(path)


def make_state_figure(path: Path) -> None:
    image = Image.new("RGB", (1890, 1025), "white")
    draw = ImageDraw.Draw(image)
    _centered(draw, (945, 65), "Persistent state is layered, not a single monolithic database",
              _font(42, True), NAVY)
    draw.rounded_rectangle((650, 365, 1240, 670), radius=25, fill=PALE_BLUE, outline=NAVY, width=5)
    _centered(draw, (945, 465), "Runtime world state", _font(39, True), NAVY)
    _centered(draw, (945, 570), "typed Python objects +\nengine-owned ledgers", _font(27), BLACK)
    nodes = [
        (45, 150, 490, 180, "Scenario specifications", "PLACE / CONTENTS / GEOMETRY\nIDENTITY / SOUL / item catalogs"),
        (1355, 150, 490, 180, "Spatial authority", "positions, zones, visibility,\nreachability and boundaries"),
        (45, 770, 490, 180, "Agent-local context", "perception, conditions,\nepisodic memory and history"),
        (1355, 770, 490, 180, "Checkpoint record", "turn results, HP, positions,\nitems, effects and memories"),
    ]
    for x, y, w, h, title, body in nodes:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=20, fill="#F7F9FA", outline=SLATE, width=4)
        _centered(draw, (x + w / 2, y + 55), title, _font(30, True), NAVY)
        _centered(draw, (x + w / 2, y + 125), body, _font(24), BLACK)
    for start, end in [((535, 300), (650, 410)), ((1355, 300), (1240, 410)),
                       ((535, 800), (650, 625)), ((1355, 800), (1240, 625))]:
        _arrow(draw, start, end, fill=BLUE, width=4, both=True)
    image.save(path)


def configure_doc(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.header_distance = Inches(0.35)
    section.footer_distance = Inches(0.35)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = rgb(BLACK)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.13

    for name, size, color, before, after in [
        ("Heading 1", 16, BLUE, 16, 7),
        ("Heading 2", 13, BLUE, 12, 5),
        ("Heading 3", 11.5, NAVY, 9, 3),
    ]:
        st = styles[name]
        st.font.name = "Calibri"
        st._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        st._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = rgb(color)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True

    caption = styles["Caption"]
    caption.font.name = "Calibri"
    caption.font.size = Pt(9)
    caption.font.italic = True
    caption.font.color.rgb = rgb(SLATE)
    caption.paragraph_format.space_before = Pt(3)
    caption.paragraph_format.space_after = Pt(9)
    caption.paragraph_format.keep_with_next = False

    if "Abstract" not in styles:
        abstract = styles.add_style("Abstract", WD_STYLE_TYPE.PARAGRAPH)
    else:
        abstract = styles["Abstract"]
    abstract.font.name = "Calibri"
    abstract.font.size = Pt(10)
    abstract.font.color.rgb = rgb(BLACK)
    abstract.paragraph_format.left_indent = Inches(0.35)
    abstract.paragraph_format.right_indent = Inches(0.35)
    abstract.paragraph_format.space_after = Pt(6)
    abstract.paragraph_format.line_spacing = 1.08

    if "Code Reference" not in styles:
        code = styles.add_style("Code Reference", WD_STYLE_TYPE.PARAGRAPH)
    else:
        code = styles["Code Reference"]
    code.font.name = "Consolas"
    code.font.size = Pt(8.5)
    code.font.color.rgb = rgb(NAVY)
    code.paragraph_format.left_indent = Inches(0.25)
    code.paragraph_format.space_after = Pt(4)

    header = section.header
    hp = header.paragraphs[0]
    hp.text = "DRIFTMOOR  /  TECHNICAL ARCHITECTURE DRAFT"
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for run in hp.runs:
        run.font.name = "Calibri"
        run.font.size = Pt(8)
        run.font.bold = True
        run.font.color.rgb = rgb(SLATE)

    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("Driftmoor architecture  |  ")
    r.font.name = "Calibri"
    r.font.size = Pt(8)
    r.font.color.rgb = rgb(SLATE)
    add_field(fp, "PAGE")


def add_title_page(doc: Document) -> None:
    doc.add_paragraph().paragraph_format.space_after = Pt(72)
    kicker = doc.add_paragraph()
    kicker.alignment = WD_ALIGN_PARAGRAPH.CENTER
    kicker.paragraph_format.space_after = Pt(18)
    r = kicker.add_run("TECHNICAL ARCHITECTURE PAPER  /  IMPLEMENTATION-GROUNDED REVISION")
    r.font.name = "Calibri"
    r.font.size = Pt(9)
    r.font.bold = True
    r.font.color.rgb = rgb(BLUE)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(12)
    r = title.add_run("Driftmoor")
    r.font.name = "Calibri"
    r.font.size = Pt(31)
    r.font.bold = True
    r.font.color.rgb = rgb(NAVY)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(22)
    r = subtitle.add_run("Authority Boundaries for Persistent-World\nLanguage Agents")
    r.font.name = "Calibri"
    r.font.size = Pt(19)
    r.font.bold = False
    r.font.color.rgb = rgb(BLUE)

    thesis = doc.add_paragraph()
    thesis.alignment = WD_ALIGN_PARAGRAPH.CENTER
    thesis.paragraph_format.left_indent = Inches(0.65)
    thesis.paragraph_format.right_indent = Inches(0.65)
    thesis.paragraph_format.space_after = Pt(42)
    r = thesis.add_run(
        "A hybrid architecture in which language models propose and express action, "
        "LATN grounds selected linguistic structures, and a Python simulation owns "
        "selected state transitions and invariants."
    )
    r.font.name = "Calibri"
    r.font.size = Pt(12)
    r.font.italic = True
    r.font.color.rgb = rgb(SLATE)

    meta = doc.add_table(rows=4, cols=2)
    meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_geometry(meta, [2100, 7260], indent_dxa=120)
    set_repeat_table_header(meta.rows[0])
    rows = [
        ("Status", "Working paper; implementation-grounded revision"),
        ("Artifact snapshot", "Driftmoor commit f9af2f6 (22 July 2026)"),
        ("Verification", "1,356 automated tests passed on 23 July 2026"),
        ("Scope", "Current implementation, architectural interpretation, and research roadmap"),
    ]
    for i, (label, value) in enumerate(rows):
        meta.cell(i, 0).text = label
        meta.cell(i, 1).text = value
        set_cell_shading(meta.cell(i, 0), PALE)
        for run in meta.cell(i, 0).paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = rgb(NAVY)
        for cell in meta.rows[i].cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                for run in p.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(9.5)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(55)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Prepared from direct inspection of the Driftmoor source repository")
    r.font.name = "Calibri"
    r.font.size = Pt(9)
    r.font.color.rgb = rgb(SLATE)

    doc.add_page_break()


def add_heading(doc, text: str, level: int = 1):
    return doc.add_heading(text, level=level)


def add_body(doc, text: str, *, style=None, bold_prefix: str | None = None):
    p = doc.add_paragraph(style=style)
    if bold_prefix and text.startswith(bold_prefix):
        a, b = text.split(bold_prefix, 1)
        if a:
            p.add_run(a)
        p.add_run(bold_prefix).bold = True
        p.add_run(b)
    else:
        p.add_run(text)
    return p


def add_bullet(doc, text: str):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.1
    return p.add_run(text)


def add_number(doc, text: str):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.1
    return p.add_run(text)


def add_figure(doc, image: Path, caption: str, width=6.35):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(image), width=Inches(width))
    for doc_pr in p._p.xpath(".//wp:docPr"):
        doc_pr.set("title", caption.split(".", 1)[0])
        doc_pr.set("descr", caption)
    c = doc.add_paragraph(caption, style="Caption")
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return c


def add_callout(doc, title: str, body: str):
    table = doc.add_table(rows=1, cols=1)
    set_table_geometry(table, [9360], indent_dxa=120)
    set_repeat_table_header(table.rows[0])
    cell = table.cell(0, 0)
    set_cell_shading(cell, PALE_BLUE)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(title)
    run.bold = True
    run.font.color.rgb = rgb(NAVY)
    p2 = cell.add_paragraph(body)
    p2.paragraph_format.space_after = Pt(0)
    for run in p2.runs:
        run.font.size = Pt(10)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(1)
    return table


def add_matrix(doc, headers: list[str], rows: list[list[str]], widths: list[int], font_size=8.8):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for j, header in enumerate(headers):
        hdr.cells[j].text = header
        set_cell_shading(hdr.cells[j], PALE)
        for run in hdr.cells[j].paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = rgb(NAVY)
    for row in rows:
        cells = table.add_row().cells
        for j, value in enumerate(row):
            cells[j].text = value
    set_table_geometry(table, widths, indent_dxa=120)
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0
                for run in p.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(font_size)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def build() -> None:
    pipeline = ASSET_DIR / "architecture_pipeline.png"
    state = ASSET_DIR / "persistent_state_layers.png"
    make_pipeline_figure(pipeline)
    make_state_figure(state)

    doc = Document()
    configure_doc(doc)
    add_title_page(doc)

    add_heading(doc, "Abstract", 1)
    add_body(doc, (
        "Driftmoor is a multi-agent tabletop role-playing engine used to investigate a broader systems question: "
        "where should authority reside when large language models act inside a persistent world? The implementation "
        "does not eliminate probabilistic models from interpretation or adjudication. Instead, it assigns authority "
        "by stage. Human or model-driven actors produce intentions; the Layered Augmented Transition Network (LATN) "
        "grounds a growing subset of linguistic actions against live scene entities; Python mechanics enforce selected "
        "spatial, inventory, combat, spell, economic, and temporal constraints; and an LLM realizes the resolved result "
        "as dialogue and prose. Runtime checkpoints preserve positions, health, conditions, memories, item possession, "
        "spell effects, and turn records. This paper documents that implemented hybrid architecture, distinguishes it "
        "from its proposed deterministic end state, and identifies testable research questions concerning grounding "
        "coverage, replayability, narrative fidelity, and state consistency."
    ), style="Abstract")
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.35)
    p.paragraph_format.right_indent = Inches(0.35)
    p.paragraph_format.space_before = Pt(4)
    r = p.add_run("Keywords: ")
    r.bold = True
    p.add_run("language agents; persistent worlds; grounded action; neuro-symbolic systems; simulation; LATN; narrative realization")

    add_callout(doc, "Central claim", (
        "Driftmoor's contribution is an explicit authority boundary, not full determinism: models may propose, interpret, "
        "and narrate, but selected state transitions are accepted only through engine-owned mechanics operating on "
        "persistent world state."
    ))

    add_heading(doc, "1. Introduction", 1)
    add_body(doc, (
        "Many language-agent systems represent the operational world primarily through prompt context: conversation "
        "history, retrieved memories, tool descriptions, and model-generated summaries. External tools can provide "
        "feedback, but the model often remains responsible for deciding what an instruction means, whether an action is "
        "valid, and how the resulting state should be described. That concentration of responsibility is productive for "
        "open-ended interaction, yet it complicates replay, invariant enforcement, causal attribution, and debugging."
    ))
    add_body(doc, (
        "Driftmoor explores a different allocation of responsibility. It is implemented as a Dungeons & Dragons 5e "
        "simulation in which human players and LLM-driven characters participate in shared scenes. Scenario files define "
        "places, entities, geometry, personas, affordances, and initial state. A central Python runtime maintains typed "
        "objects and turn-local ledgers. LLM roles generate character intentions, action prose, open-ended adjudication, "
        "and narration. Between those roles, deterministic components ground selected verbs and enforce selected physical "
        "and game-mechanical constraints."
    ))
    add_body(doc, (
        "The resulting system is neither a purely symbolic simulator nor an LLM wrapper around a text adventure. It is a "
        "hybrid architecture whose most important design decision is that authority can shift between components during a "
        "single turn. This paper describes the code as it exists at commit f9af2f6, rather than treating design aspirations "
        "as completed capabilities."
    ))

    add_heading(doc, "1.1 Contributions", 2)
    add_bullet(doc, "An implementation-grounded account of Driftmoor's current turn pipeline and state model.")
    add_bullet(doc, "A precise distinction among intention generation, linguistic grounding, adjudication, mutation, and narrative realization.")
    add_bullet(doc, "A layered account of persistence spanning authored specifications, runtime objects, agent-local memory, and JSON checkpoints.")
    add_bullet(doc, "A limitations and evaluation agenda that turns architectural claims into falsifiable questions.")

    add_heading(doc, "2. Related Architectural Patterns", 1)
    add_body(doc, (
        "Driftmoor shares the agent-environment loop found in ReAct, where language-model reasoning alternates with actions "
        "that obtain external feedback [1]. It also shares with Generative Agents an interest in memory, planning, and "
        "believable behavior inside a persistent social environment [2], and with Voyager an emphasis on executable action "
        "and environment feedback rather than unconstrained prose alone [3]. SayCan similarly separates linguistic "
        "affordance from environment-grounded feasibility when selecting robotic skills [4]."
    ))
    add_body(doc, (
        "The distinguishing emphasis here is narrower. Driftmoor does not claim a new general-purpose agent benchmark or a "
        "complete cognitive theory. It treats a richly authored game world as a laboratory for authority boundaries: which "
        "facts are prompt material, which are engine state, which actions can be grounded deterministically, and which "
        "outcomes may be narrated only after a state transition has been resolved."
    ))

    add_heading(doc, "3. System Boundary and Terminology", 1)
    add_body(doc, (
        "Five stages should be kept separate. An intention expresses what an actor wants to attempt. Grounding maps linguistic "
        "structure to entities and canonical actions in the current scene. Adjudication determines whether and how the attempt "
        "is allowed. Mutation changes authoritative runtime state. Realization renders the resolved result for humans and "
        "model-driven characters. The present implementation crosses probabilistic and deterministic boundaries more than once."
    ))
    add_figure(doc, pipeline, "Figure 1. Implemented turn pipeline. Colors distinguish model-heavy, grounding, hybrid adjudication, engine mutation, and narrative stages.")

    add_heading(doc, "3.1 Implemented data path", 2)
    add_matrix(doc,
        ["Stage", "Implemented representation", "Primary authority"],
        [
            ["Actor context", "RoleContext: condition, scene, persona, identity, perception", "Python assembly; authored files"],
            ["Intention", "ActionIntent", "Player-Left LLM, human transport, or test stub"],
            ["Action expression", "CharacterOutput: internal, body language, spoken, action", "Player-Right LLM or parser"],
            ["Grounding", "ResolvedAction and specialized LATN resolver results", "LATN plus scene adapter; shallow fallback in some paths"],
            ["Adjudication", "Adjudication plus Python resolution logs", "DM-Left for open judgment; Python for selected mechanics"],
            ["Mutation", "Direct updates to positions, HP, items, effects, time, ledgers", "Python engine"],
            ["Realization", "Narration", "DM-Right constrained by resolution and perception"],
            ["Persistence", "Per-turn JSON checkpoint", "Python serializer"],
        ],
        [1400, 4200, 3760], font_size=8.4)
    add_body(doc, (
        "This vocabulary matters because the earlier conceptual draft referred to ActorIntent, WorldOperation, WorldDelta, "
        "and EventRecord as if they were implemented types. They are useful names for a possible future event-sourced design, "
        "but the current repository uses ActionIntent, CharacterOutput, Adjudication, Narration, direct mutations, resolution "
        "logs, recent-event ledgers, and checkpoint records."
    ))

    add_heading(doc, "4. Persistent World Representation", 1)
    add_body(doc, (
        "Persistence in Driftmoor is layered rather than monolithic. Authored Markdown files define durable scenario content. "
        "Loaders transform that content into typed Python objects. A running scene adds mutable positions, conditions, item "
        "holders, active spell effects, memories, and turn history. Per-turn JSON snapshots preserve a substantial subset of "
        "that runtime state for resume. Calling the scenario files 'executable world content' is therefore reasonable only "
        "in the qualified sense that loaders parse their structured sections into runtime objects and affordances."
    ))
    add_figure(doc, state, "Figure 2. Four persistence layers connected to the runtime state used for grounding and adjudication.")

    add_heading(doc, "4.1 Authored specifications", 2)
    add_body(doc, (
        "Places and their contents are described through PLACE.md, CONTENTS.md, GEOMETRY.md, and zone files. Character identity "
        "and behavior priors come from IDENTITY.md and SOUL.md. Item libraries define weapons, armor, consumables, containers, "
        "and magical or mundane objects. These files mix structured fields with narrative material. The loader extracts the "
        "parts needed for mechanics while retaining raw prose for model context."
    ))

    add_heading(doc, "4.2 Runtime object model", 2)
    add_body(doc, (
        "GameState is a central registry of characters, places, things, scenes, and turn count. Entities reference one another "
        "by stable string identifiers, while indexes provide deterministic lookup. More specialized runtime structures hold "
        "spatial geometry, character conditions, spellcasting state, loadout, commerce catalogs, puzzles, scene topology, and "
        "per-character session data. This division is pragmatic rather than fully normalized: some scene mechanics live in "
        "the large session orchestrator rather than behind a single world-operation interface."
    ))

    add_heading(doc, "5. Agent Cognition and Subjective Context", 1)
    add_body(doc, (
        "Driftmoor distinguishes persistent world state from the subjective context supplied to an actor. RoleContext contains "
        "a character identifier, turn number, rendered condition state, scene context, SOUL content, IDENTITY content, a "
        "Python-computed perception block, and combat status. Player-Left uses that material to generate an ActionIntent. "
        "Player-Right turns the intent into internal monologue, body language, speech, and an action description."
    ))
    add_body(doc, (
        "The strongest implemented subjectivity guarantee is perceptual. Scene geometry computes visibility and reachability, "
        "and the resulting perception block is treated as exhaustive in prompts. DM-Right is separately instructed to narrate "
        "only creatures and events available to the acting character. Internal monologue does not enter shared scene history, "
        "whereas observable speech, body language, action, and narration can."
    ))
    add_heading(doc, "5.1 Memory, emotion, relationships, and goals", 2)
    add_body(doc, (
        "CharacterSession maintains bounded episodic memory and recent interaction records. Checkpoints restore those memories "
        "along with neurochemical condition state and recent scene history. NPC models also contain authored relationships, "
        "knowledge, hooks, and active concerns. These mechanisms support continuity, but they should not yet be described as a "
        "general cognitive-state engine. Relationship change and goal revision are not governed by a unified update model; "
        "some evolution remains implicit in prompts, narration, and authored content."
    ))
    add_callout(doc, "Implemented versus proposed", (
        "Implemented: bounded episodic notes, condition vectors, asymmetric perception, authored relationships, and context "
        "filtering. Proposed research direction: explicit, inspectable relationship and goal transitions linked to world events."
    ))

    add_heading(doc, "6. LATN as a Grounded Language Interface", 1)
    add_body(doc, (
        "The Layered Augmented Transition Network is integrated through a host-neutral parser interface and a Driftmoor scene "
        "adapter. LATN analyzes sentence and verb-phrase structure, applies a domain lexicon, and grounds noun phrases against "
        "ranked entities in the live scene. The resolver derives canonical verbs from semantic dimensions rather than relying "
        "only on surface keywords. Top-score ties are rejected rather than guessed."
    ))
    add_body(doc, (
        "Current coverage is deliberately incremental. LATN-backed resolvers handle object interactions such as examine, search, "
        "read, and press; transfers such as take, drop, and give; movement targets and distances; venue entry and exit; commerce "
        "actions; and short responses used in transactional flows. Conjoined verb phrases can yield multiple ResolvedAction "
        "objects. The scene adapter filters and ranks candidate items, characters, venues, and catalog entities."
    ))
    add_heading(doc, "6.1 The fallback boundary", 2)
    add_body(doc, (
        "LATN is not yet the universal parser for every player or agent utterance. The item-interaction path is LATN-first but "
        "retains a shallow resolver when parsing fails or grounds nothing. Other intent fields can be inferred through explicit "
        "Python heuristics. This fallback makes deployment robust but weakens claims of globally deterministic interpretation. "
        "A research evaluation should therefore report coverage, fallback frequency, ambiguity refusal, incorrect grounding, "
        "and downstream recovery separately."
    ))

    add_heading(doc, "7. Hybrid Adjudication and Engine Authority", 1)
    add_body(doc, (
        "The current adjudication boundary is hybrid. DM-Left is an LLM-backed role that evaluates proposed actions against "
        "rules, spatial summaries, and game state, returning an Adjudication object. Its output includes approval, a possible "
        "modified action, declared movement, condition deltas, spatial events, attack declarations, and notes. When no model "
        "is configured, the stub approves actions without changes."
    ))
    add_body(doc, (
        "Python then owns an expanding set of concrete mechanics. Movement is clamped to speed and checked against geometry. "
        "Combat resolves attack rolls, armor class, range, line of sight, and damage. Transfers modify possession and ownership "
        "through a shared primitive. Commerce moves item ownership and coin together. Spell logic tracks slots, concentration, "
        "durations, targeting, and implemented effects. Puzzles, item manipulation, loadout, scene transitions, initiative, "
        "visibility, and the game clock likewise contain engine-owned rules."
    ))
    add_body(doc, (
        "DM-Right receives the Adjudication, character output, scene history, authoritative perception, and any Python resolution "
        "log. Its prompt explicitly labels engine resolution as authoritative and instructs the model to narrate that result "
        "rather than the original intent. This ordering makes narrative downstream of selected mechanics, even though open-ended "
        "adjudication still includes a model."
    ))

    add_heading(doc, "8. Worked Execution Trace", 1)
    add_body(doc, (
        "Consider the utterance 'give the torch to Amara' when the acting character carries a grounded torch and Amara is a "
        "valid scene participant. The trace below is representative of implemented transfer logic; exact phrasing and narration "
        "remain model-dependent."
    ))
    add_matrix(doc,
        ["Step", "Operation", "Observable result"],
        [
            ["1", "Actor source produces an ActionIntent and CharacterOutput.", "The attempted transfer is explicit in the action text."],
            ["2", "LATN parses the transfer verb and grounds the direct object and recipient.", "A ResolvedAction identifies give, the torch, and Amara; ambiguity refuses to guess."],
            ["3", "The session validates actor, item, recipient, possession, and transfer preconditions.", "Invalid participants or possession produce a failure log without mutation."],
            ["4", "The shared transfer primitive moves possession and, for give, ownership.", "Holder, owner, character inventories, and carried position are synchronized."],
            ["5", "Recent-event and episodic-memory records are appended.", "Later prompts can include a bounded memory of the handoff."],
            ["6", "DM-Right receives the authoritative resolution log.", "Prose may vary, but it is instructed to describe the completed or rejected transfer."],
            ["7", "The turn checkpoint serializes the result.", "Resume can restore held items, ownership, position, memories, and turn history."],
        ],
        [700, 4420, 4240], font_size=8.4)
    add_body(doc, (
        "This trace shows why 'narrative is not the source of reality' is a useful but bounded statement. For implemented "
        "transfers, the mutation precedes narration and can be tested independently. For actions outside implemented mechanics, "
        "DM-Left or other model-mediated logic may still determine important parts of the outcome."
    ))

    add_heading(doc, "9. Persistence, Resume, and Causal Records", 1)
    add_body(doc, (
        "Each turn checkpoint records initiative order, ActionIntent, CharacterOutput, Adjudication, Narration, character "
        "conditions, health, positions, episodic memory, recent interactions, active characters, party examination state, "
        "spell runtime, held and wielded items, and possession information. Resume reconstructs narrative history from prior "
        "turn records and restores the last checkpoint's mutable state."
    ))
    add_body(doc, (
        "The checkpoint is not yet a complete event-sourced world database. It stores current snapshots plus turn results, and "
        "some loose scene content is reconstructed from authored specifications. Only currently held items are serialized by "
        "the item-ownership helper; loose objects are rebuilt from scene content. The architecture therefore offers resumable "
        "state and inspectable traces without guaranteeing that every possible world mutation can be replayed solely from an "
        "append-only event log."
    ))

    add_heading(doc, "10. Implementation Evidence", 1)
    add_body(doc, (
        "The claims in this paper were checked against the repository snapshot identified on the title page. The automated suite "
        "contains tests for LATN integration, scene and turn cycles, movement and geometry, visibility, combat, spells, inventory, "
        "commerce, item manipulation, persistence, transports, narration, multi-scene orchestration, and content loading. On "
        "23 July 2026, the repository's virtual environment executed 1,356 tests successfully, with one deprecation warning."
    ))
    add_body(doc, (
        "Passing tests establish regression coverage for encoded behavior, not scientific validation of the paper's broader "
        "claims. In particular, they do not measure how often free-form language falls outside LATN coverage, whether model "
        "narration contradicts engine state under varied prompts, or whether different model providers produce equivalent "
        "behavior."
    ))
    add_heading(doc, "10.1 Recommended evaluation protocol", 2)
    add_number(doc, "Construct a versioned corpus of human and agent utterances spanning supported, ambiguous, unsupported, negated, and conjoined actions.")
    add_number(doc, "Report LATN parse success, unique grounding, correct refusal, shallow-fallback use, and incorrect grounding as separate categories.")
    add_number(doc, "Replay identical checkpoints with fixed dice and controlled model outputs; compare engine deltas independently of prose.")
    add_number(doc, "Measure narration fidelity against resolution logs and perception constraints, including forbidden mentions and invented mutations.")
    add_number(doc, "Inject checkpoint/resume boundaries between every stage and verify state invariants after restoration.")
    add_number(doc, "Compare the hybrid pipeline with an LLM-only baseline and, where possible, a deterministic-only baseline.")

    add_heading(doc, "11. Limitations and Threats to Validity", 1)
    add_bullet(doc, "Domain specificity. The repository is designed around a particular D&D campaign; generalization beyond it is a research hypothesis.")
    add_bullet(doc, "Partial language coverage. LATN grounds a growing family of verbs but is not a complete natural-language interface.")
    add_bullet(doc, "Model-mediated adjudication. DM-Left still determines open-ended legality and interpretation in important paths.")
    add_bullet(doc, "Distributed authority. Mechanics are spread across specialized modules and a large session orchestrator, complicating formal reasoning.")
    add_bullet(doc, "Snapshot persistence. Checkpoints are resumable records, not a fully normalized database or append-only event store.")
    add_bullet(doc, "Cognitive claims. Memory, conditions, relationships, and goals are heterogeneous mechanisms rather than a validated model of cognition.")
    add_bullet(doc, "Evaluation maturity. The test suite is extensive, but no controlled comparison yet supports claims about grounding accuracy or agent quality.")

    add_heading(doc, "12. Research and Engineering Roadmap", 1)
    add_matrix(doc,
        ["Priority", "Change", "Research value"],
        [
            ["1", "Introduce canonical WorldOperation, WorldDelta, and EventRecord types without pretending they already exist.", "Creates a uniform audit and replay boundary across mechanics."],
            ["2", "Route all supported utterances through a single typed grounding result with explicit fallback reasons.", "Makes coverage and ambiguity measurable."],
            ["3", "Move remaining routine adjudication from DM-Left into deterministic validators.", "Narrows the probabilistic authority surface."],
            ["4", "Add a narrative-fidelity checker over resolution logs, perception, and state deltas.", "Measures whether realization stays faithful to computed reality."],
            ["5", "Define explicit relationship and goal transition rules.", "Turns cognitive evolution into inspectable state rather than prompt implication."],
            ["6", "Develop cross-domain scenarios with the same operation schema.", "Tests whether the architecture generalizes beyond the campaign."],
        ],
        [900, 4140, 4320], font_size=8.4)

    add_heading(doc, "13. Discussion", 1)
    add_body(doc, (
        "Driftmoor suggests that useful agent architectures need not choose between symbolic control and generative flexibility. "
        "The more practical question is which component is authorized to assert each kind of fact. An LLM can be an effective "
        "source of character motivation, language, and open-ended judgment without being the sole custodian of position, ownership, "
        "health, time, or visibility. A parser can ground common actions without needing to understand every utterance. A simulation "
        "can enforce important invariants while leaving room for narration and improvisation."
    ))
    add_body(doc, (
        "This allocation also improves inspectability. When a transfer is wrong, the investigator can distinguish parser grounding, "
        "precondition validation, mutation, memory recording, checkpointing, and narration. The same separation exposes gaps rather "
        "than concealing them: fallback parsing, LLM adjudication, and unmodeled mechanics are visible architectural boundaries."
    ))
    add_body(doc, (
        "Applications to robotics, digital twins, assistants, education, or collaborative virtual environments should therefore be "
        "presented as hypotheses. The transferable idea is not the D&D rule set. It is the staged ownership of authority, coupled "
        "with a persistent environment against which language can be grounded and outcomes can be checked."
    ))

    add_heading(doc, "14. Conclusion", 1)
    add_body(doc, (
        "Driftmoor is best understood as an evolving hybrid architecture for agents in a persistent world. Its present implementation "
        "combines LLM-driven intention and prose, LATN-backed grounding for selected actions, Python-owned mechanics and mutations, "
        "perception-constrained context, and resumable checkpoints. The system does not yet provide deterministic interpretation or "
        "adjudication for arbitrary language, nor a complete event-sourced world model. Those limitations are part of the research "
        "agenda rather than reasons to obscure the current result."
    ))
    add_body(doc, (
        "The architectural contribution is the boundary itself: reality is increasingly represented and changed outside the language "
        "model, while the model remains available where linguistic and imaginative flexibility are most valuable. Making that boundary "
        "explicit, testable, and progressively narrower offers a credible path toward grounded language agents whose behavior can be "
        "inspected without sacrificing expressive interaction."
    ))

    add_heading(doc, "Appendix A. Implementation Map", 1)
    add_matrix(doc,
        ["Concern", "Primary modules and artifacts"],
        [
            ["Turn roles and types", "engine/player_router.py; engine/dm_agent.py; engine/scene_manager.py"],
            ["LATN integration", "engine/latn.py; engine/latn_adapter.py; engine/latn_resolver.py; engine/latn_integration.py"],
            ["Session orchestration", "engine/session.py; engine/orchestrator.py; engine/scene_runner.py"],
            ["World and entity models", "models/game_state.py; models/character.py; models/thing.py; models/place.py; models/scene.py"],
            ["Space and time", "models/space_time.py; engine/geometry.py; engine/game_clock.py"],
            ["Mechanics", "engine/combat_resolver.py; engine/item_transfer.py; engine/commerce.py; engine/spell_resolver.py; engine/manipulation.py"],
            ["Persistence and records", "engine/persistence.py; engine/game_checkpoint.py; engine/transcript.py; engine/narrator.py"],
            ["Scenario content", "scenario/places; scenario/people; scenario/things; specs"],
            ["Verification", "tests/ (1,356 passing tests at the documented snapshot)"],
        ],
        [2350, 7010], font_size=8.7)

    add_heading(doc, "References", 1)
    refs = [
        ("[1] S. Yao et al., “ReAct: Synergizing Reasoning and Acting in Language Models,” ICLR, 2023. ",
         "https://arxiv.org/abs/2210.03629"),
        ("[2] J. S. Park et al., “Generative Agents: Interactive Simulacra of Human Behavior,” UIST, 2023. ",
         "https://arxiv.org/abs/2304.03442"),
        ("[3] G. Wang et al., “Voyager: An Open-Ended Embodied Agent with Large Language Models,” 2023. ",
         "https://arxiv.org/abs/2305.16291"),
        ("[4] M. Ahn et al., “Do As I Can, Not As I Say: Grounding Language in Robotic Affordances,” 2022. ",
         "https://arxiv.org/abs/2204.01691"),
        ("[5] Driftmoor source repository, commit f9af2f6153f924bac10676578990173dda27b528, 22 July 2026. "
         "Local implementation artifact reviewed for this paper.", None),
        ("[6] Driftmoor, “LATN Parser Integration (Phase 2),” docs/latn-integration.md, repository artifact.", None),
        ("[7] Driftmoor, architecture and scenario specifications in README.md and specs/, repository artifact.", None),
    ]
    for text, url in refs:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        p.paragraph_format.space_after = Pt(7)
        p.paragraph_format.line_spacing = 1.1
        p.add_run(text)
        if url:
            add_hyperlink(p, "arXiv record", url)

    # Keep tables and headings from splitting awkwardly.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.widow_control = True
    for p in doc.paragraphs:
        p.paragraph_format.widow_control = True

    doc.core_properties.title = "Driftmoor: Authority Boundaries for Persistent-World Language Agents"
    doc.core_properties.subject = "Implementation-grounded technical architecture paper"
    doc.core_properties.keywords = "Driftmoor, language agents, persistent worlds, LATN, simulation"
    doc.core_properties.comments = "Rewritten from direct inspection of the Driftmoor source repository."
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
