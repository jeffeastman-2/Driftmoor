"""Printable, filled character sheet generated from a CharacterDraft."""

from __future__ import annotations

from io import BytesIO
import math

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from character_generation import ABILITIES, CharacterDraft


W, H = letter
M = 30
INK = colors.HexColor("#1D211E")
MUTED = colors.HexColor("#64675F")
GOLD = colors.HexColor("#936C2D")
PALE = colors.HexColor("#F0EBDD")
LINE = colors.HexColor("#9C998F")


def modifier(score: int) -> int:
    return math.floor((score - 10) / 2)


def proficiency_bonus(level: int) -> int:
    return 2 + max(0, level - 1) // 4


def _fit(c: canvas.Canvas, text: str, width: float, font: str, size: float,
         minimum: float = 5.5) -> float:
    text = str(text)
    while size > minimum and stringWidth(text, font, size) > width:
        size -= .25
    return size


def _wrapped_lines(text: str, width: float, font: str, size: float,
                   max_lines: int | None = None) -> list[str]:
    paragraphs = str(text or "").splitlines() or [""]
    out: list[str] = []
    for paragraph in paragraphs:
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if not current or stringWidth(candidate, font, size) <= width:
                current = candidate
            else:
                out.append(current)
                current = word
        if current:
            out.append(current)
        elif not words:
            out.append("")
    if max_lines and len(out) > max_lines:
        out = out[:max_lines]
        while out[-1] and stringWidth(out[-1] + "...", font, size) > width:
            out[-1] = out[-1][:-1]
        out[-1] += "..."
    return out


def _text(c: canvas.Canvas, text: str, x: float, y: float, width: float,
          size: float = 8, leading: float = 10.5, max_lines: int | None = None,
          color=INK, font: str = "Helvetica") -> float:
    c.setFillColor(color)
    c.setFont(font, size)
    for line in _wrapped_lines(text, width, font, size, max_lines):
        c.drawString(x, y, line)
        y -= leading
    return y


def _box(c: canvas.Canvas, x: float, y: float, w: float, h: float,
         title: str, fill=None, radius: float = 6) -> tuple[float, float, float, float]:
    c.setStrokeColor(LINE)
    c.setLineWidth(.8)
    if fill:
        c.setFillColor(fill)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=bool(fill))
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawString(x + 7, y + h - 11, title.upper())
    return x + 7, y + 7, w - 14, h - 22


def _header(c: canvas.Canvas, draft: CharacterDraft, page: int) -> None:
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(M, H - 23, "DRIFTMOOR")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7)
    c.drawRightString(W - M, H - 23, f"PLAYER CHARACTER  |  PAGE {page} OF 2")
    c.setStrokeColor(LINE)
    c.line(M, H - 28, W - M, H - 28)
    if page == 1:
        c.setFillColor(INK)
        size = _fit(c, draft.name, 300, "Helvetica-Bold", 24, 15)
        c.setFont("Helvetica-Bold", size)
        c.drawString(M, H - 59, draft.name)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(M, H - 74, "CHARACTER NAME")
        info_x = 335
        entries = [
            ("CLASS & LEVEL", f"{draft.character_class} {draft.level}"),
            ("ANCESTRY", draft.race), ("BACKGROUND", draft.background),
            ("PLAYER", draft.player), ("PRONOUNS", draft.pronouns),
            ("ALIGNMENT", draft.alignment),
        ]
        col_w = 116
        for i, (lab, value) in enumerate(entries):
            col, row = i % 2, i // 2
            x, y = info_x + col * col_w, H - 48 - row * 22
            c.setFillColor(INK); c.setFont("Helvetica-Bold", _fit(c, value, col_w - 5, "Helvetica-Bold", 8.5))
            c.drawString(x, y, value)
            c.setFillColor(MUTED); c.setFont("Helvetica", 5.5); c.drawString(x, y - 8, lab)
            c.setStrokeColor(LINE); c.line(x, y - 10, x + col_w - 8, y - 10)
    else:
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(M, H - 57, draft.name)
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
        c.drawString(M, H - 70, "THE PERSON BEHIND THE NUMBERS")


def _ability_box(c: canvas.Canvas, draft: CharacterDraft, name: str, x: float, y: float) -> None:
    score = getattr(draft, name)
    c.setStrokeColor(LINE); c.setFillColor(colors.white)
    c.roundRect(x, y, 61, 77, 8, stroke=1, fill=1)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(x + 30.5, y + 63, name[:3].upper())
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 23)
    mod = modifier(score)
    c.drawCentredString(x + 30.5, y + 34, f"{mod:+d}")
    c.setFillColor(PALE); c.circle(x + 30.5, y + 10, 13, stroke=1, fill=1)
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x + 30.5, y + 7, str(score))


def _list(c: canvas.Canvas, items: list[str], x: float, y: float, width: float,
          max_lines: int, size: float = 7.5) -> None:
    remaining = max_lines
    for item in items or ["None"]:
        lines = _wrapped_lines(str(item).replace("_", " "), width - 10, "Helvetica", size, remaining)
        if not lines or remaining <= 0:
            break
        c.setFillColor(GOLD); c.circle(x + 2, y + 2, 1.3, stroke=0, fill=1)
        for i, line in enumerate(lines):
            c.setFillColor(INK); c.setFont("Helvetica", size)
            c.drawString(x + 7, y, line)
            y -= 10
            remaining -= 1
            if remaining <= 0:
                return


def _page_one(c: canvas.Canvas, d: CharacterDraft) -> None:
    _header(c, d, 1)
    top = H - 112
    for i, name in enumerate(ABILITIES):
        _ability_box(c, d, name, M, top - i * 85 - 77)

    mid_x = 103
    stat_w = 98
    stats = [
        ("ARMOR CLASS", str(d.ac)), ("HIT POINTS", f"{d.hp} / {d.hp}"),
        ("SPEED", d.speed), ("PROF. BONUS", f"+{proficiency_bonus(d.level)}"),
    ]
    for i, (title, value) in enumerate(stats):
        x = mid_x + (i % 2) * (stat_w + 8)
        y = top - 70 - (i // 2) * 78
        _box(c, x, y, stat_w, 68, title, fill=PALE)
        c.setFillColor(INK); c.setFont("Helvetica-Bold", _fit(c, value, stat_w - 15, "Helvetica-Bold", 20))
        c.drawCentredString(x + stat_w / 2, y + 22, value)

    bx, by, bw, bh = _box(c, mid_x, top - 331, 204, 165, "Abilities & Proficiencies")
    _list(c, d.abilities, bx, by + bh - 3, bw, 13)

    bx, by, bw, bh = _box(c, mid_x, top - 500, 204, 155, "Equipment & Wealth")
    _list(c, d.equipment, bx, by + bh - 3, bw, 10)
    c.setStrokeColor(LINE); c.line(bx, by + 14, bx + bw, by + 14)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 6.5); c.drawString(bx, by + 3, "PURSE")
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 8); c.drawRightString(bx + bw, by + 3, d.purse)

    right_x, right_w = 317, W - M - 317
    bx, by, bw, bh = _box(c, right_x, top - 244, right_w, 242, "Attacks, Spells & Features")
    feature_items = list(d.spells) + list(d.abilities)
    _list(c, feature_items, bx, by + bh - 3, bw, 20, 7.5)

    bx, by, bw, bh = _box(c, right_x, top - 383, right_w, 127, "Physical Description")
    _text(c, d.physical_description, bx, by + bh - 3, bw, size=7.5, leading=10, max_lines=10)

    bx, by, bw, bh = _box(c, right_x, top - 500, right_w, 105, "Current State")
    state = f"Mood: {d.mood}\n\nDisposition: {d.disposition}"
    _text(c, state, bx, by + bh - 3, bw, size=7.5, leading=10, max_lines=8)


def _narrative_box(c: canvas.Canvas, title: str, items: list[str] | str,
                   x: float, y: float, w: float, h: float, lines: int) -> None:
    bx, by, bw, bh = _box(c, x, y, w, h, title, fill=colors.white)
    text = items if isinstance(items, str) else "\n".join(f"- {item}" for item in items)
    _text(c, text or "None recorded.", bx, by + bh - 2, bw, size=8, leading=10.5, max_lines=lines)


def _page_two(c: canvas.Canvas, d: CharacterDraft) -> None:
    c.showPage()
    _header(c, d, 2)
    y_top = H - 94
    left, right, gap = M, 309, 12
    col_w = (W - 2 * M - gap) / 2
    _narrative_box(c, "Values & Drives", d.values_and_drives, left, y_top - 145, col_w, 145, 11)
    _narrative_box(c, "Fears & Wounds", d.fears_and_wounds, right, y_top - 145, col_w, 145, 11)
    _narrative_box(c, "Voice & Manner", d.voice_and_manner, left, y_top - 292, col_w, 135, 10)
    _narrative_box(c, "Loyalties", d.loyalties, right, y_top - 292, col_w, 135, 10)
    _narrative_box(c, "Internal Contradiction", d.internal_contradiction, left, y_top - 434,
                   W - 2 * M, 130, 10)
    _narrative_box(c, "Significant Detail", d.signature_detail or "None recorded.", left,
                   y_top - 548, col_w, 102, 7)
    _narrative_box(c, "Open Threads", d.open_threads, right, y_top - 548, col_w, 102, 7)
    c.setFillColor(PALE); c.roundRect(M, 39, W - 2 * M, 40, 5, stroke=0, fill=1)
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 8)
    c.drawString(M + 10, 63, "NOTES FROM THE ROAD")
    c.setStrokeColor(LINE); c.line(M + 123, 58, W - M - 10, 58)
    c.line(M + 10, 48, W - M - 10, 48)


def character_sheet_pdf(draft: CharacterDraft) -> bytes:
    """Return a two-page, print-ready PDF for the supplied character draft."""
    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=letter)
    c.setTitle(f"{draft.name} - Driftmoor Character Sheet")
    c.setAuthor("Driftmoor")
    _page_one(c, draft)
    _page_two(c, draft)
    c.save()
    return stream.getvalue()
