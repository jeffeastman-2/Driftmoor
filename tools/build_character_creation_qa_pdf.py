"""Build the printable Driftmoor character-creation playtest packet."""

from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "Driftmoor_Quick_Character_Interview.pdf"
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
    c.drawCentredString(W / 2, 23, "Quick Character Interview  |  Driftmoor")


def new_page(c: canvas.Canvas, page: int, title: str) -> float:
    if page > 1:
        c.showPage()
    header(c, page, title)
    return H - 56


def page_one(c: canvas.Canvas) -> None:
    y = new_page(c, 1, "No game knowledge needed")
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 27)
    c.drawString(M, y, "Who are you in Driftmoor?")
    y -= 22
    y = wrapped(c, "Driftmoor is a small town on a cold, rocky coast. People have gone missing, strange creatures "
                "have been seen on the roads, and you have arrived just as the town needs help. Pick whatever sounds "
                "fun. We will turn your choices into a ready-to-play character.", M, y, W - 2 * M,
                size=10.5, leading=15, color=MUTED) - 14
    y = section(c, "01", "The basics", "Three details. Make them up or ask for a suggestion.", y)
    label(c, "Your character's name", M, y)
    c.setStrokeColor(LINE); c.line(M + 145, y - 1, W - M, y - 1)
    y -= 29
    label(c, "Gender", M, y)
    x = M + 74
    for item in ("Male", "Female", "Unstated"):
        x = checkbox(c, x, y + 5, item) + 13
    y -= 28
    label(c, "Race", M, y)
    x = M + 74
    for item in ("Human", "Elf", "Dwarf", "Halfling", "Suggest"):
        x = checkbox(c, x, y + 5, item) + 12
    y -= 44

    y = section(c, "02", "What sounds fun?", "Check as many as you like.", y)
    fun = ("Protect friends", "Fight up close", "Use a bow", "Sneak around",
           "Use magic", "Heal people", "Talk your way through", "Solve mysteries")
    for row in range(4):
        checkbox(c, M + 12, y - row * 22, fun[row * 2], 9)
        checkbox(c, M + 275, y - row * 22, fun[row * 2 + 1], 9)
    y -= 108

    y = section(c, "03", "What are you like?", "Pick two or three, or add your own.", y)
    traits = ("Brave", "Kind", "Clever", "Curious", "Funny", "Careful", "Stubborn", "Mysterious")
    for row in range(2):
        x = M + 12
        for item in traits[row * 4:(row + 1) * 4]:
            x = checkbox(c, x, y - row * 22, item, 9) + 30
    y -= 65
    label(c, "Something else", M + 12, y)
    c.setStrokeColor(LINE); c.line(M + 110, y - 1, W - M, y - 1)
    y -= 42

    y = section(c, "04", "Why did your player come to Driftmoor?", "Choose one. We can invent the details together.", y)
    reasons = ("To help", "For money", "To solve a mystery", "Looking for someone", "Sent here", "Just passing through")
    for row in range(2):
        x = M + 12
        for item in reasons[row * 3:(row + 1) * 3]:
            x = checkbox(c, x, y - row * 22, item, 9) + 36
    y -= 62
    c.setFillColor(PALE)
    c.roundRect(M, y - 34, W - 2 * M, 38, 5, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(M + 12, y - 12, "THAT IS ENOUGH TO BEGIN.")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8.5)
    c.drawString(M + 12, y - 26, "After you have played, you can add a past, fears, loyalties, and other details that feel true.")


def page_two(c: canvas.Canvas) -> None:
    y = new_page(c, 2, "A little more about you")
    y = section(c, "02", "What makes you interesting?", "Short, ordinary answers are perfect.", y)
    y = field(c, "5 - How you act", "How do you usually talk and act, especially when things go wrong?", M, y, W - 2 * M, 2)
    y = field(c, "6 - What matters", "Who or what matters most to you?", M, y, W - 2 * M, 2)
    y = field(c, "7 - Strength and flaw", "What is one good quality and one flaw you have?", M, y, W - 2 * M, 2)
    y = field(c, "8 - Something you carry", "Do you carry an object that matters to you? What is it, and why?", M, y, W - 2 * M, 2)

    y = section(c, "03", "How do you want to play?", "Choose whatever sounds fun. We will handle the rules.", y)
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
    label(c, "How experienced should you be?", M, y)
    x = M + 170
    for item in ("Just beginning", "Some hard lessons", "Proven", "Match group"):
        x = checkbox(c, x, y + 5, item, 7) + 8
    y -= 23
    y = field(c, "Anything special?", "Is there anything you definitely want to be able to do?", M, y, W - 2 * M, 1)


def build() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=letter)
    c.setTitle("Driftmoor Quick Character Interview")
    c.setAuthor("Driftmoor")
    page_one(c)
    c.save()
    return OUT


if __name__ == "__main__":
    print(build())
