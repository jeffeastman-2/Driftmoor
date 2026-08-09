"""Build the printable Driftmoor character-creation playtest packet."""

from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "Driftmoor_Eight_Question_Character_Interview.pdf"
W, H = letter
M = 44
INK = colors.HexColor("#20221f")
MUTED = colors.HexColor("#66685f")
GOLD = colors.HexColor("#9B7436")
PALE = colors.HexColor("#F2EEE3")
LINE = colors.HexColor("#B9B4A8")


def wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float,
            font: str = "Helvetica", size: float = 9.5, leading: float = 13,
            color=INK) -> float:
    c.setFont(font, size)
    c.setFillColor(color)
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def checkbox(c: canvas.Canvas, x: float, y: float, label: str, size: float = 8.5) -> float:
    c.setStrokeColor(MUTED)
    c.rect(x, y - 7, 8, 8, stroke=1, fill=0)
    c.setFillColor(INK)
    c.setFont("Helvetica", size)
    c.drawString(x + 12, y - 6, label)
    return x + 14 + stringWidth(label, "Helvetica", size)


def lines(c: canvas.Canvas, x: float, y: float, width: float, count: int,
          gap: float = 18) -> float:
    c.setStrokeColor(LINE)
    c.setLineWidth(.55)
    for _ in range(count):
        c.line(x, y, x + width, y)
        y -= gap
    return y


def label(c: canvas.Canvas, text: str, x: float, y: float) -> None:
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x, y, text.upper())


def field(c: canvas.Canvas, title: str, prompt: str, x: float, y: float,
          width: float, line_count: int = 2) -> float:
    label(c, title, x, y)
    y -= 13
    y = wrapped(c, prompt, x, y, width, size=8.5, leading=11, color=MUTED)
    y -= 7
    return lines(c, x, y, width, line_count) - 5


def section(c: canvas.Canvas, number: str, title: str, subtitle: str, y: float) -> float:
    c.setFillColor(PALE)
    c.roundRect(M, y - 31, W - 2 * M, 34, 5, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(M + 11, y - 11, number)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(M + 34, y - 12, title)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(M + 34, y - 25, subtitle)
    return y - 46


def header(c: canvas.Canvas, page: int, title: str) -> None:
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(M, H - 28, "DRIFTMOOR")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawRightString(W - M, H - 28, title)
    c.setStrokeColor(LINE)
    c.line(M, H - 34, W - M, H - 34)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W / 2, 23, f"Eight-Question Character Interview  |  Page {page} of 2")


def new_page(c: canvas.Canvas, page: int, title: str) -> float:
    if page > 1:
        c.showPage()
    header(c, page, title)
    return H - 56


def page_one(c: canvas.Canvas) -> None:
    y = new_page(c, 1, "Begin with a person, not a stat block")
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 27)
    c.drawString(M, y, "Who comes to Driftmoor?")
    y -= 22
    y = wrapped(c, "Eight questions are enough to discover a playable character. Answer in your own words. "
                "There are no ideal responses. "
                "You may choose from a list, write something custom, ask Driftmoor to suggest, "
                "or leave an optional detail unstated.", M, y, W - 2 * M,
                size=10.5, leading=15, color=MUTED) - 14
    c.setFillColor(PALE)
    c.roundRect(M, y - 46, W - 2 * M, 48, 5, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(M + 12, y - 15, "PLAYTESTER")
    c.setFont("Helvetica", 9)
    c.drawString(M + 12, y - 34, "Your name: __________________________________")
    c.drawString(M + 285, y - 34, "Date: __________________")
    y -= 66
    y = section(c, "01", "Identity", "These choices belong to you. Driftmoor should not silently infer them.", y)
    label(c, "Character name", M, y)
    c.setStrokeColor(LINE); c.line(M + 112, y - 1, W - M, y - 1)
    y -= 24
    label(c, "Pronouns", M, y)
    x = M + 88
    for item in ("she/her", "he/him", "they/them", "custom", "unspecified"):
        x = checkbox(c, x, y + 5, item) + 10
    y -= 25
    label(c, "Gender (optional)", M, y)
    c.setStrokeColor(LINE); c.line(M + 112, y - 1, W - M, y - 1)
    y -= 25
    label(c, "Ancestry / people", M, y)
    x = M + 112
    for item in ("Human", "Elf", "Dwarf", "Halfling", "Other", "Suggest"):
        x = checkbox(c, x, y + 5, item) + 8
    y -= 23
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawString(M + 112, y, "If Other: _________________________________________________")
    y -= 22
    y = field(c, "1 - First impression", "What do we notice when they first walk into a room?", M, y, W - 2 * M, 3)
    y = field(c, "2 - A life before the road", "What part of their past still has a hold on them?", M, y, W - 2 * M, 3)
    y = field(c, "3 - The reason to leave", "What do they want badly enough to take a dangerous road?", M, y, W - 2 * M, 3)
    y = field(c, "4 - Fear or wound", "What would they hate for their companions to discover? What experience still shapes them?", M, y, W - 2 * M, 3)


def page_two(c: canvas.Canvas) -> None:
    y = new_page(c, 2, "The inner character")
    y = section(c, "02", "A soul with edges", "Specific tensions give Driftmoor something meaningful to portray.", y)
    y = field(c, "5 - Voice and manner", "How do they speak, move, joke, or behave under pressure?", M, y, W - 2 * M, 2)
    y = field(c, "6 - Loyalty", "Who, what, or which principle could call them back even when leaving would be safer?", M, y, W - 2 * M, 2)
    y = field(c, "7 - Contradiction", "Name two true things about them that do not sit comfortably together.", M, y, W - 2 * M, 2)
    y = field(c, "8 - Significant object", "Do they carry something mundane that matters to them? Why can they not let it go?", M, y, W - 2 * M, 2)

    y = section(c, "03", "How do you want to play?", "Choose experiences; Driftmoor can translate them into rules later.", y)
    label(c, "Choose any that sound fun", M, y)
    options = ["Protect allies", "Fight up close", "Attack at range", "Sneak and deceive",
               "Solve mysteries", "Use broad magic", "Heal and support", "Negotiate",
               "Explore wilderness", "Improvise with tools"]
    for row in range(5):
        checkbox(c, M, y - 16 - row * 15, options[row * 2], 7.5)
        checkbox(c, M + 255, y - 16 - row * 15, options[row * 2 + 1], 7.5)
    y -= 91
    label(c, "How many rules and options sound fun?", M, y)
    x = M + 220
    for item in ("Keep it simple", "A few choices", "Lots", "Surprise me"):
        x = checkbox(c, x, y + 5, item, 7) + 8
    y -= 22
    label(c, "How experienced are they?", M, y)
    x = M + 170
    for item in ("Just beginning", "Some hard lessons", "Proven", "Match group"):
        x = checkbox(c, x, y + 5, item, 7) + 8
    y -= 23
    y = field(c, "Anything mechanics must express", "A signature tactic, training, spell, disability, tool, or limitation that matters to the concept.", M, y, W - 2 * M, 1)


def build() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=letter)
    c.setTitle("Driftmoor Eight-Question Character Interview")
    c.setAuthor("Driftmoor")
    page_one(c)
    page_two(c)
    c.save()
    return OUT


if __name__ == "__main__":
    print(build())
